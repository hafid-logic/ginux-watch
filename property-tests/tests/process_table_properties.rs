//! Property and model-based tests for the pure `ProcessTable<8>` core of the
//! upstream `ginux-process` crate (C-1 hot region #1: waitid / process
//! reaping + signal delivery). Upstream is consumed READ-ONLY via a path
//! dependency; semantics recorded at upstream SHA
//! 285d025b7f8bcad0784585dcfbd23cada4643408.
//!
//! Two layers:
//!   1. A differential model test: a slot-accurate reference model
//!      (`Model`, transcribed line-by-line from upstream `lib.rs`) is driven
//!      by the same random op sequence as a real `ProcessTable<8>`; after
//!      every op the observable table state must equal the model state.
//!   2. Focused invariant properties: one-shot reaping, waitable-child
//!      selection, orphan adoption, capacity, error cleanliness, and the
//!      sigprocmask/queue/handler-frame signal rules.
//!
//! Style follows the crate's own inline tests: behavior-sentence names,
//! `assert_eq!(..., Ok(..)/Err(..))` conventions, tables sized to the
//! scenario. No unsafe. Deterministic: fixed case counts, default proptest
//! RNG (stable across runs unless PROPTEST_* env overrides it).

use ginux_process::{
    ChildStatus, Credentials, ProcessError, ProcessTable, SignalAction, SignalDelivery, TaskId,
    TaskState, TaskView, WaitResult, WaitTarget, MAX_SIGNAL, WNOHANG, WUNTRACED,
};
use proptest::prelude::*;

const TASKS: usize = 8;
/// Mirrors upstream `UNBLOCKABLE_SIGNALS`: SIGKILL (9) and SIGSTOP (19).
const UNBLOCKABLE: u64 = (1 << (9 - 1)) | (1 << (19 - 1));

// ---------------------------------------------------------------------------
// Reference model (transcribed from upstream lib.rs at the recorded SHA)
// ---------------------------------------------------------------------------

#[derive(Clone, Debug)]
struct ModelTask {
    id: TaskId,
    tgid: u32,
    parent: u32,
    process_group: u32,
    session: u32,
    state: TaskState,
    uid: u32,
    gid: u32,
    capabilities: u64,
    signal_mask: u64,
    pending_signals: u64,
    exec_epoch: u32,
    signal_actions: [SignalAction; MAX_SIGNAL as usize],
    signal_frame_active: bool,
    saved_signal_mask: u64,
}

#[derive(Clone, Debug)]
struct Model {
    /// Positional slots: upstream allocates the first free slot and reaping
    /// empties the slot in place, so slot order is part of the contract
    /// (it decides which child `wait` reports first).
    slots: Vec<Option<ModelTask>>,
    next_pid: u32,
    next_generation: u32,
}

impl Model {
    fn new() -> Self {
        Self {
            slots: vec![None; TASKS],
            next_pid: 1,
            next_generation: 1,
        }
    }

    fn occupied(&self) -> usize {
        self.slots.iter().filter(|s| s.is_some()).count()
    }

    fn first_free(&self) -> Option<usize> {
        self.slots.iter().position(|s| s.is_none())
    }

    /// Mirrors the private `ProcessTable::index`.
    fn index_of(&self, id: TaskId) -> Result<usize, ProcessError> {
        match self
            .slots
            .iter()
            .position(|s| s.as_ref().is_some_and(|t| t.id.pid == id.pid))
        {
            Some(i) if self.slots[i].as_ref().unwrap().id == id => Ok(i),
            Some(_) => Err(ProcessError::StaleTask),
            None => Err(ProcessError::InvalidTask),
        }
    }

    fn task(&self, id: TaskId) -> Result<&ModelTask, ProcessError> {
        Ok(self.slots[self.index_of(id)?].as_ref().unwrap())
    }

    fn task_mut(&mut self, id: TaskId) -> Result<&mut ModelTask, ProcessError> {
        let i = self.index_of(id)?;
        Ok(self.slots[i].as_mut().unwrap())
    }

    /// Mirrors the private `ProcessTable::allocate` field derivation; the
    /// identity itself is taken from the real table (TaskId generations are
    /// not publicly constructible), and the driver asserts the counters.
    fn fresh_task(
        &self,
        id: TaskId,
        parent: u32,
        tgid_arg: u32,
        pg_arg: u32,
        session_arg: u32,
        creds: (u32, u32, u64),
    ) -> ModelTask {
        let pid = id.pid;
        ModelTask {
            id,
            tgid: if tgid_arg == 0 { pid } else { tgid_arg },
            parent,
            process_group: if pg_arg == 0 { pid } else { pg_arg },
            session: if session_arg == 0 { pid } else { session_arg },
            state: TaskState::Running,
            uid: creds.0,
            gid: creds.1,
            capabilities: creds.2,
            signal_mask: 0,
            pending_signals: 0,
            exec_epoch: 0,
            signal_actions: [SignalAction::Default; MAX_SIGNAL as usize],
            signal_frame_active: false,
            saved_signal_mask: 0,
        }
    }

    /// Mirrors the private `adopt_orphans`.
    fn adopt_orphans(&mut self, tgid: u32) {
        let group_running = self.slots.iter().any(|s| {
            s.as_ref()
                .is_some_and(|t| t.tgid == tgid && t.state == TaskState::Running)
        });
        if group_running {
            return;
        }
        for slot in self.slots.iter_mut() {
            if let Some(t) = slot {
                if t.parent == tgid {
                    t.parent = 1;
                }
            }
        }
    }

    fn expect_create_init(&self) -> Result<(), ProcessError> {
        if self.slots.iter().any(|s| s.is_some()) {
            return Err(ProcessError::InvalidState);
        }
        Ok(())
    }

    fn commit_create_init(&mut self, id: TaskId, creds: (u32, u32, u64)) {
        assert_eq!(id.pid, self.next_pid, "pid counter drift on create_init");
        assert_eq!(
            id.generation(),
            self.next_generation,
            "generation counter drift on create_init"
        );
        assert_eq!(self.first_free(), Some(0), "init must take the first slot");
        self.slots[0] = Some(self.fresh_task(id, 0, 1, 1, 1, creds));
        self.next_pid += 1;
        self.next_generation += 1;
    }

    fn expect_fork(&self, parent: TaskId) -> Result<(), ProcessError> {
        let p = self.task(parent)?;
        if p.state != TaskState::Running {
            return Err(ProcessError::InvalidParent);
        }
        if self.first_free().is_none() {
            return Err(ProcessError::TableFull);
        }
        Ok(())
    }

    fn commit_fork(&mut self, parent: TaskId, child: TaskId) {
        assert_eq!(child.pid, self.next_pid, "pid counter drift on fork");
        assert_eq!(
            child.generation(),
            self.next_generation,
            "generation counter drift on fork"
        );
        let (tgid, pg, session, creds, mask, actions, frame, saved) = {
            let p = self.task(parent).unwrap();
            (
                p.tgid,
                p.process_group,
                p.session,
                (p.uid, p.gid, p.capabilities),
                p.signal_mask,
                p.signal_actions,
                p.signal_frame_active,
                p.saved_signal_mask,
            )
        };
        let mut task = self.fresh_task(child, tgid, 0, pg, session, creds);
        // fork copies mask + dispositions + handler frame; pending starts empty.
        task.signal_mask = mask;
        task.signal_actions = actions;
        task.signal_frame_active = frame;
        task.saved_signal_mask = saved;
        let slot = self.first_free().unwrap();
        self.slots[slot] = Some(task);
        self.next_pid += 1;
        self.next_generation += 1;
    }

    fn expect_clone_thread(&self, leader: TaskId) -> Result<(), ProcessError> {
        let p = self.task(leader)?;
        if p.state != TaskState::Running {
            return Err(ProcessError::InvalidParent);
        }
        if self.first_free().is_none() {
            return Err(ProcessError::TableFull);
        }
        Ok(())
    }

    fn commit_clone_thread(&mut self, leader: TaskId, tid: TaskId) {
        assert_eq!(tid.pid, self.next_pid, "pid counter drift on clone_thread");
        assert_eq!(
            tid.generation(),
            self.next_generation,
            "generation counter drift on clone_thread"
        );
        let (parent, tgid, pg, session, creds) = {
            let p = self.task(leader).unwrap();
            (
                p.parent,
                p.tgid,
                p.process_group,
                p.session,
                (p.uid, p.gid, p.capabilities),
            )
        };
        let task = self.fresh_task(tid, parent, tgid, pg, session, creds);
        let slot = self.first_free().unwrap();
        self.slots[slot] = Some(task);
        self.next_pid += 1;
        self.next_generation += 1;
    }

    fn expect_exit(&self, id: TaskId) -> Result<(), ProcessError> {
        if self.task(id)?.state != TaskState::Running {
            return Err(ProcessError::InvalidState);
        }
        Ok(())
    }

    fn commit_exit(&mut self, id: TaskId, status: i32) {
        let tgid = {
            let t = self.task_mut(id).unwrap();
            t.state = TaskState::Exited(status);
            t.tgid
        };
        self.adopt_orphans(tgid);
    }

    fn expect_signaled(&self, id: TaskId, sig: u8) -> Result<(), ProcessError> {
        if sig == 0 || sig > MAX_SIGNAL {
            return Err(ProcessError::InvalidSignal);
        }
        if self.task(id)?.state != TaskState::Running {
            return Err(ProcessError::InvalidState);
        }
        Ok(())
    }

    fn commit_signaled(&mut self, id: TaskId, sig: u8) {
        let tgid = {
            let t = self.task_mut(id).unwrap();
            t.state = TaskState::Signaled(sig);
            t.tgid
        };
        self.adopt_orphans(tgid);
    }

    /// Mirrors `wait`: slot-order scan, leader-only, parent-tgid ownership,
    /// status extraction, NotChild vs NoExitedChild classification.
    fn expect_wait(
        &self,
        parent: TaskId,
        target: WaitTarget,
    ) -> Result<WaitResult, ProcessError> {
        let p = self.task(parent)?;
        if p.state != TaskState::Running {
            return Err(ProcessError::InvalidState);
        }
        let parent_pid = p.tgid;
        let child = self.slots.iter().position(|s| {
            s.as_ref().is_some_and(|t| {
                t.parent == parent_pid
                    && t.id.pid == t.tgid
                    && matches!(t.state, TaskState::Exited(_) | TaskState::Signaled(_))
                    && match target {
                        WaitTarget::Any => true,
                        WaitTarget::Group(group) => t.process_group == group,
                        WaitTarget::Specific(pid) => t.id.pid == pid,
                    }
            })
        });
        if let Some(i) = child {
            let t = self.slots[i].as_ref().unwrap();
            let status = match t.state {
                TaskState::Exited(code) => ChildStatus::Exited(code),
                TaskState::Signaled(sig) => ChildStatus::Signaled(sig),
                _ => return Err(ProcessError::InvalidState),
            };
            return Ok(WaitResult {
                child: t.id,
                status,
            });
        }
        if let WaitTarget::Specific(pid) = target {
            if !self.slots.iter().any(|s| {
                s.as_ref().is_some_and(|t| {
                    t.parent == parent_pid && t.id.pid == pid && t.id.pid == t.tgid
                })
            }) {
                return Err(ProcessError::NotChild);
            }
        }
        Err(ProcessError::NoExitedChild)
    }

    fn commit_reap(&mut self, child: TaskId) {
        let i = self.index_of(child).unwrap();
        self.slots[i] = None;
    }

    fn expect_has_waitable(
        &self,
        parent: TaskId,
        target: WaitTarget,
    ) -> Result<bool, ProcessError> {
        let p = self.task(parent)?;
        if p.state != TaskState::Running {
            return Err(ProcessError::InvalidState);
        }
        let parent_pid = p.tgid;
        Ok(self.slots.iter().any(|s| {
            s.as_ref().is_some_and(|t| {
                t.parent == parent_pid
                    && t.id.pid == t.tgid
                    && match target {
                        WaitTarget::Any => true,
                        WaitTarget::Group(group) => t.process_group == group,
                        WaitTarget::Specific(pid) => t.id.pid == pid,
                    }
            })
        }))
    }

    fn expect_set_signal_mask(&self, id: TaskId) -> Result<(), ProcessError> {
        self.task(id).map(|_| ())
    }

    fn commit_set_signal_mask(&mut self, id: TaskId, mask: u64) {
        self.task_mut(id).unwrap().signal_mask = mask & !UNBLOCKABLE;
    }

    fn expect_signal(&self, id: TaskId, sig: u8) -> Result<(), ProcessError> {
        if sig == 0 || sig > MAX_SIGNAL {
            return Err(ProcessError::InvalidSignal);
        }
        if self.task(id)?.state != TaskState::Running {
            return Err(ProcessError::InvalidState);
        }
        Ok(())
    }

    fn commit_signal(&mut self, id: TaskId, sig: u8) {
        self.task_mut(id).unwrap().pending_signals |= 1u64 << (sig - 1);
    }

    fn expect_set_signal_action(&self, id: TaskId, sig: u8) -> Result<(), ProcessError> {
        if sig == 0 || sig > MAX_SIGNAL || UNBLOCKABLE & (1u64 << (sig - 1)) != 0 {
            return Err(ProcessError::InvalidSignal);
        }
        self.task(id).map(|_| ())
    }

    fn commit_set_signal_action(&mut self, id: TaskId, sig: u8, action: SignalAction) {
        self.task_mut(id).unwrap().signal_actions[sig as usize - 1] = action;
    }

    fn expect_signal_action(&self, id: TaskId, sig: u8) -> Result<SignalAction, ProcessError> {
        if sig == 0 || sig > MAX_SIGNAL {
            return Err(ProcessError::InvalidSignal);
        }
        Ok(self.task(id)?.signal_actions[sig as usize - 1])
    }

    fn expect_next_signal(&self, id: TaskId) -> Result<Option<u8>, ProcessError> {
        let t = self.task(id)?;
        let deliverable = t.pending_signals & !t.signal_mask;
        if deliverable == 0 {
            return Ok(None);
        }
        Ok(Some(deliverable.trailing_zeros() as u8 + 1))
    }

    fn commit_next_signal(&mut self, id: TaskId, sig: u8) {
        self.task_mut(id).unwrap().pending_signals &= !(1u64 << (sig - 1));
    }

    /// Mirrors `begin_signal` (pop-then-dispatch). Returns the expected
    /// result plus the updated task when the call succeeds; an Err leaves
    /// state untouched upstream (the popped bit is re-marked), so no commit.
    fn expect_begin_signal(
        &self,
        id: TaskId,
    ) -> (
        Result<Option<SignalDelivery>, ProcessError>,
        Option<ModelTask>,
    ) {
        let sig = match self.expect_next_signal(id) {
            Ok(Some(s)) => s,
            Ok(None) => return (Ok(None), None),
            Err(e) => return (Err(e), None),
        };
        let t = self.task(id).unwrap();
        let mut updated = t.clone();
        updated.pending_signals &= !(1u64 << (sig - 1));
        let delivery = match t.signal_actions[sig as usize - 1] {
            SignalAction::Default => SignalDelivery::Default(sig),
            SignalAction::Ignore => SignalDelivery::Ignored(sig),
            SignalAction::Handler(address) => {
                if t.signal_frame_active {
                    // Nested handler refused; pending bit was re-marked, so
                    // the net state change is zero.
                    return (Err(ProcessError::InvalidState), None);
                }
                updated.signal_frame_active = true;
                updated.saved_signal_mask = t.signal_mask;
                updated.signal_mask = t.signal_mask | (1u64 << (sig - 1));
                SignalDelivery::Handler { signal: sig, address }
            }
        };
        (Ok(Some(delivery)), Some(updated))
    }

    fn commit_task(&mut self, id: TaskId, updated: ModelTask) {
        let i = self.index_of(id).unwrap();
        self.slots[i] = Some(updated);
    }

    fn expect_signal_return(&self, id: TaskId) -> Result<(), ProcessError> {
        if !self.task(id)?.signal_frame_active {
            return Err(ProcessError::InvalidState);
        }
        Ok(())
    }

    fn commit_signal_return(&mut self, id: TaskId) {
        let t = self.task_mut(id).unwrap();
        t.signal_mask = t.saved_signal_mask;
        t.saved_signal_mask = 0;
        t.signal_frame_active = false;
    }

    fn expect_blocking_interrupted(&self, id: TaskId) -> Result<bool, ProcessError> {
        let t = self.task(id)?;
        Ok(t.pending_signals & !t.signal_mask != 0)
    }

    fn expect_exec(&self, id: TaskId) -> Result<u32, ProcessError> {
        let t = self.task(id)?;
        if t.state != TaskState::Running {
            return Err(ProcessError::InvalidState);
        }
        Ok(t.exec_epoch + 1) // upstream checked_add; overflow unreachable here
    }

    fn commit_exec(&mut self, id: TaskId) {
        let t = self.task_mut(id).unwrap();
        t.signal_frame_active = false;
        t.saved_signal_mask = 0;
        for action in t.signal_actions.iter_mut() {
            if *action != SignalAction::Ignore {
                *action = SignalAction::Default;
            }
        }
        t.exec_epoch += 1;
    }

    fn expect_reap_thread(&self, id: TaskId) -> Result<(), ProcessError> {
        let t = self.task(id)?;
        if t.id.pid == t.tgid || t.state == TaskState::Running {
            return Err(ProcessError::InvalidState);
        }
        Ok(())
    }

    fn commit_reap_thread(&mut self, id: TaskId) {
        let i = self.index_of(id).unwrap();
        self.slots[i] = None;
    }

    fn apply_shutdown(&mut self, status: i32) -> usize {
        let mut stopped = 0;
        for slot in self.slots.iter_mut() {
            if let Some(t) = slot {
                if t.state == TaskState::Running {
                    t.state = TaskState::Exited(status);
                    stopped += 1;
                }
            }
        }
        stopped
    }

    fn apply_reap_all(&mut self) -> usize {
        let mut reaped = 0;
        for slot in self.slots.iter_mut() {
            let dead = slot
                .as_ref()
                .is_some_and(|t| matches!(t.state, TaskState::Exited(_) | TaskState::Signaled(_)));
            if dead {
                *slot = None;
                reaped += 1;
            }
        }
        reaped
    }

    fn expect_set_process_group(&self, id: TaskId, group: u32) -> Result<(), ProcessError> {
        self.task(id)?;
        if group == 0 {
            return Err(ProcessError::InvalidTask);
        }
        Ok(())
    }

    fn commit_set_process_group(&mut self, id: TaskId, group: u32) {
        self.task_mut(id).unwrap().process_group = group;
    }

    fn has_pid(&self, pid: u32) -> bool {
        self.slots
            .iter()
            .any(|s| s.as_ref().is_some_and(|t| t.id.pid == pid))
    }
}

// ---------------------------------------------------------------------------
// Observable-state agreement checks
// ---------------------------------------------------------------------------

fn assert_view_matches(view: &TaskView, mt: &ModelTask) {
    assert_eq!(view.id, mt.id, "id of {:?}", mt.id);
    assert_eq!(view.tgid, mt.tgid, "tgid of {:?}", mt.id);
    assert_eq!(view.parent, mt.parent, "parent of {:?}", mt.id);
    assert_eq!(
        view.process_group, mt.process_group,
        "process_group of {:?}",
        mt.id
    );
    assert_eq!(view.session, mt.session, "session of {:?}", mt.id);
    assert_eq!(view.state, mt.state, "state of {:?}", mt.id);
    assert_eq!(view.exec_epoch, mt.exec_epoch, "exec_epoch of {:?}", mt.id);
    assert_eq!(view.credentials.uid, mt.uid, "uid of {:?}", mt.id);
    assert_eq!(view.credentials.gid, mt.gid, "gid of {:?}", mt.id);
    assert_eq!(
        view.credentials.capabilities, mt.capabilities,
        "capabilities of {:?}",
        mt.id
    );
    assert!(
        view.credentials.groups().is_empty(),
        "groups of {:?} must stay empty (never set in this harness)",
        mt.id
    );
}

/// Full observable agreement: occupancy count, per-task view fields, pid
/// lookup, and absence of every reaped/never-allocated pid.
fn assert_table_matches_model(table: &ProcessTable<TASKS>, model: &Model) {
    assert_eq!(
        table.active(),
        model.occupied(),
        "active() must equal model occupancy"
    );
    for mt in model.slots.iter().flatten() {
        let view = table
            .view(mt.id)
            .unwrap_or_else(|e| panic!("table lost model task {:?}: {:?}", mt.id, e));
        assert_view_matches(&view, mt);
        let by_pid = table
            .lookup(mt.id.pid)
            .unwrap_or_else(|| panic!("lookup({}) lost {:?}", mt.id.pid, mt.id));
        assert_view_matches(&by_pid, mt);
    }
    for pid in 1..model.next_pid {
        if !model.has_pid(pid) {
            assert!(
                table.lookup(pid).is_none(),
                "pid {pid} must be absent (reaped or never allocated)"
            );
        }
    }
}

// ---------------------------------------------------------------------------
// Op vocabulary and strategies
// ---------------------------------------------------------------------------

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum TargetSpec {
    Any,
    /// Group of the registry task at this index (current group if alive).
    Group(u8),
    /// Wild group id: usually nonexistent, exercises empty-match paths.
    GroupWild(u32),
    /// Pid of the registry task at this index (dead pids exercise NotChild).
    Specific(u8),
    /// Wild pid: reaped, not-yet-allocated, or zero.
    SpecificWild(u32),
}

#[derive(Clone, Debug, PartialEq, Eq)]
enum Op {
    CreateInit { creds: u8 },
    Fork { parent: u8 },
    CloneThread { leader: u8 },
    Exec { who: u8 },
    Exit { who: u8, status: i16 },
    Signaled { who: u8, sig: u8 },
    ReapThread { who: u8 },
    Wait { parent: u8, target: TargetSpec, options: u32 },
    HasWaitable { parent: u8, target: TargetSpec },
    SetSignalMask { who: u8, mask: u64 },
    Signal { who: u8, sig: u8 },
    SetSignalAction { who: u8, sig: u8, kind: u8, addr: u64 },
    NextSignal { who: u8 },
    BeginSignal { who: u8 },
    SignalReturn { who: u8 },
    BlockingInterrupted { who: u8 },
    ReadAction { who: u8, sig: u8 },
    SetProcessGroup { who: u8, group: u16 },
    Shutdown { status: i16 },
    ReapAll,
}

fn mk_creds(c: (u32, u32, u64)) -> Credentials {
    if c.2 == u64::MAX {
        Credentials::root()
    } else {
        Credentials::unprivileged(c.0, c.1)
    }
}

fn pick(registry: &[TaskId], sel: u8) -> TaskId {
    registry[sel as usize % registry.len()]
}

/// Table and model must resolve the same selector, so resolution goes
/// through the shared registry + model (dead tasks fall back to a stale but
/// deterministic value).
fn resolve_target(spec: &TargetSpec, registry: &[TaskId], model: &Model) -> WaitTarget {
    match spec {
        TargetSpec::Any => WaitTarget::Any,
        TargetSpec::Group(sel) => {
            let id = pick(registry, *sel);
            match model.task(id) {
                Ok(t) => WaitTarget::Group(t.process_group),
                Err(_) => WaitTarget::Group(id.pid),
            }
        }
        TargetSpec::GroupWild(g) => WaitTarget::Group(*g),
        TargetSpec::Specific(sel) => WaitTarget::Specific(pick(registry, *sel).pid),
        TargetSpec::SpecificWild(p) => WaitTarget::Specific(*p),
    }
}

fn arb_wait_options() -> impl Strategy<Value = u32> {
    prop_oneof![
        3 => Just(0u32),
        2 => Just(WNOHANG),
        1 => Just(WNOHANG | WUNTRACED),
        1 => Just(WNOHANG | ginux_process::WCONTINUED),
        1 => Just(ginux_process::WAIT_ALLOWED_OPTIONS),
        1 => (0u32..16).prop_map(|v| v),
    ]
}

fn arb_target_spec() -> impl Strategy<Value = TargetSpec> {
    prop_oneof![
        4 => Just(TargetSpec::Any),
        2 => (0u8..8).prop_map(TargetSpec::Group),
        1 => (0u32..24).prop_map(TargetSpec::GroupWild),
        3 => (0u8..8).prop_map(TargetSpec::Specific),
        2 => (0u32..24).prop_map(TargetSpec::SpecificWild),
    ]
}

fn arb_op() -> impl Strategy<Value = Op> {
    prop_oneof![
        2 => (0u8..2).prop_map(|c| Op::CreateInit { creds: c }),
        14 => (0u8..16).prop_map(|p| Op::Fork { parent: p }),
        5 => (0u8..16).prop_map(|l| Op::CloneThread { leader: l }),
        4 => (0u8..16).prop_map(|w| Op::Exec { who: w }),
        10 => (0u8..16, -128i16..256).prop_map(|(w, s)| Op::Exit { who: w, status: s }),
        5 => (0u8..16, 0u8..70).prop_map(|(w, s)| Op::Signaled { who: w, sig: s }),
        3 => (0u8..16).prop_map(|w| Op::ReapThread { who: w }),
        12 => (0u8..16, arb_target_spec(), arb_wait_options())
            .prop_map(|(p, t, o)| Op::Wait { parent: p, target: t, options: o }),
        4 => (0u8..16, arb_target_spec())
            .prop_map(|(p, t)| Op::HasWaitable { parent: p, target: t }),
        4 => (0u8..16, any::<u64>()).prop_map(|(w, m)| Op::SetSignalMask { who: w, mask: m }),
        8 => (0u8..16, 0u8..70).prop_map(|(w, s)| Op::Signal { who: w, sig: s }),
        5 => (0u8..16, 0u8..70, 0u8..3, any::<u64>())
            .prop_map(|(w, s, k, a)| Op::SetSignalAction { who: w, sig: s, kind: k, addr: a }),
        6 => (0u8..16).prop_map(|w| Op::NextSignal { who: w }),
        6 => (0u8..16).prop_map(|w| Op::BeginSignal { who: w }),
        4 => (0u8..16).prop_map(|w| Op::SignalReturn { who: w }),
        3 => (0u8..16).prop_map(|w| Op::BlockingInterrupted { who: w }),
        3 => (0u8..16, 0u8..70).prop_map(|(w, s)| Op::ReadAction { who: w, sig: s }),
        2 => (0u8..16, 0u16..512).prop_map(|(w, g)| Op::SetProcessGroup { who: w, group: g }),
        1 => (-128i16..256).prop_map(|s| Op::Shutdown { status: s }),
        1 => Just(Op::ReapAll),
    ]
}

// ---------------------------------------------------------------------------
// Driver: apply one op to table + model, compare outcomes, assert agreement
// ---------------------------------------------------------------------------

fn drive(op: &Op, table: &mut ProcessTable<TASKS>, model: &mut Model, registry: &mut Vec<TaskId>) {
    let needs_task = !matches!(op, Op::CreateInit { .. } | Op::ReapAll | Op::Shutdown { .. });
    if needs_task && registry.is_empty() {
        return; // nothing to act on yet; a previous op already asserted agreement
    }
    match *op {
        Op::CreateInit { creds } => {
            let triple = if creds == 0 {
                (0, 0, u64::MAX)
            } else {
                (1000 + creds as u32, 1000, 0)
            };
            let want = model.expect_create_init();
            let got = table.create_init(mk_creds(triple));
            match (want, got) {
                (Ok(()), Ok(id)) => {
                    model.commit_create_init(id, triple);
                    registry.push(id);
                }
                (Err(we), Err(ge)) => assert_eq!(we, ge, "create_init error mismatch"),
                (want, got) => panic!("create_init: table={got:?} model={want:?}"),
            }
        }
        Op::Fork { parent } => {
            let p = pick(registry, parent);
            let want = model.expect_fork(p);
            let got = table.fork(p);
            match (want, got) {
                (Ok(()), Ok(child)) => {
                    model.commit_fork(p, child);
                    registry.push(child);
                }
                (Err(we), Err(ge)) => assert_eq!(we, ge, "fork({p:?}) error mismatch"),
                (want, got) => panic!("fork({p:?}): table={got:?} model={want:?}"),
            }
        }
        Op::CloneThread { leader } => {
            let l = pick(registry, leader);
            let want = model.expect_clone_thread(l);
            let got = table.clone_thread(l);
            match (want, got) {
                (Ok(()), Ok(tid)) => {
                    model.commit_clone_thread(l, tid);
                    registry.push(tid);
                }
                (Err(we), Err(ge)) => assert_eq!(we, ge, "clone_thread({l:?}) error mismatch"),
                (want, got) => panic!("clone_thread({l:?}): table={got:?} model={want:?}"),
            }
        }
        Op::Exec { who } => {
            let w = pick(registry, who);
            let want = model.expect_exec(w);
            let got = table.exec(w);
            match (want, got) {
                (Ok(epoch), got) => {
                    assert_eq!(got, Ok(epoch), "exec({w:?}) epoch mismatch");
                    model.commit_exec(w);
                }
                (Err(we), Err(ge)) => assert_eq!(we, ge, "exec({w:?}) error mismatch"),
                (want, got) => panic!("exec({w:?}): table={got:?} model={want:?}"),
            }
        }
        Op::Exit { who, status } => {
            let w = pick(registry, who);
            let want = model.expect_exit(w);
            let got = table.exit(w, status as i32);
            match (want, got) {
                (Ok(()), Ok(())) => model.commit_exit(w, status as i32),
                (Err(we), Err(ge)) => assert_eq!(we, ge, "exit({w:?}) error mismatch"),
                (want, got) => panic!("exit({w:?}, {status}): table={got:?} model={want:?}"),
            }
        }
        Op::Signaled { who, sig } => {
            let w = pick(registry, who);
            let want = model.expect_signaled(w, sig);
            let got = table.signaled(w, sig);
            match (want, got) {
                (Ok(()), Ok(())) => model.commit_signaled(w, sig),
                (Err(we), Err(ge)) => assert_eq!(we, ge, "signaled({w:?}, {sig}) error mismatch"),
                (want, got) => panic!("signaled({w:?}, {sig}): table={got:?} model={want:?}"),
            }
        }
        Op::ReapThread { who } => {
            let w = pick(registry, who);
            let want = model.expect_reap_thread(w);
            let got = table.reap_thread(w);
            match (want, got) {
                (Ok(()), Ok(())) => model.commit_reap_thread(w),
                (Err(we), Err(ge)) => assert_eq!(we, ge, "reap_thread({w:?}) error mismatch"),
                (want, got) => panic!("reap_thread({w:?}): table={got:?} model={want:?}"),
            }
        }
        Op::Wait { parent, target, options } => {
            let p = pick(registry, parent);
            let t = resolve_target(&target, registry, model);
            let want = model.expect_wait(p, t);
            let got = table.wait(p, t, options);
            match (want, got) {
                (Ok(want_r), Ok(got_r)) => {
                    assert_eq!(got_r, want_r, "wait({p:?}, {t:?}) payload mismatch");
                    model.commit_reap(got_r.child);
                }
                (Err(we), Err(ge)) => {
                    assert_eq!(we, ge, "wait({p:?}, {t:?}) error mismatch")
                }
                (want, got) => panic!(
                    "wait({p:?}, {t:?}, options={options:#x}): table={got:?} model={want:?}"
                ),
            }
        }
        Op::HasWaitable { parent, target } => {
            let p = pick(registry, parent);
            let t = resolve_target(&target, registry, model);
            let want = model.expect_has_waitable(p, t);
            let got = table.has_waitable_child(p, t);
            assert_eq!(got, want, "has_waitable_child({p:?}, {t:?})");
        }
        Op::SetSignalMask { who, mask } => {
            let w = pick(registry, who);
            let want = model.expect_set_signal_mask(w);
            let got = table.set_signal_mask(w, mask);
            match (want, got) {
                (Ok(()), Ok(())) => model.commit_set_signal_mask(w, mask),
                (Err(we), Err(ge)) => {
                    assert_eq!(we, ge, "set_signal_mask({w:?}) error mismatch")
                }
                (want, got) => panic!("set_signal_mask({w:?}): table={got:?} model={want:?}"),
            }
        }
        Op::Signal { who, sig } => {
            let w = pick(registry, who);
            let want = model.expect_signal(w, sig);
            let got = table.signal(w, sig);
            match (want, got) {
                (Ok(()), Ok(())) => model.commit_signal(w, sig),
                (Err(we), Err(ge)) => assert_eq!(we, ge, "signal({w:?}, {sig}) error mismatch"),
                (want, got) => panic!("signal({w:?}, {sig}): table={got:?} model={want:?}"),
            }
        }
        Op::SetSignalAction { who, sig, kind, addr } => {
            let w = pick(registry, who);
            let action = match kind {
                0 => SignalAction::Default,
                1 => SignalAction::Ignore,
                _ => SignalAction::Handler(addr),
            };
            let want = model.expect_set_signal_action(w, sig);
            let got = table.set_signal_action(w, sig, action);
            match (want, got) {
                (Ok(()), Ok(())) => model.commit_set_signal_action(w, sig, action),
                (Err(we), Err(ge)) => assert_eq!(
                    we, ge,
                    "set_signal_action({w:?}, {sig}) error mismatch"
                ),
                (want, got) => panic!(
                    "set_signal_action({w:?}, {sig}, {action:?}): table={got:?} model={want:?}"
                ),
            }
        }
        Op::NextSignal { who } => {
            let w = pick(registry, who);
            let want = model.expect_next_signal(w);
            let got = table.next_signal(w);
            assert_eq!(got, want, "next_signal({w:?})");
            if let Ok(Some(sig)) = got {
                model.commit_next_signal(w, sig);
            }
        }
        Op::BeginSignal { who } => {
            let w = pick(registry, who);
            let (want, updated) = model.expect_begin_signal(w);
            let got = table.begin_signal(w);
            assert_eq!(&got, &want, "begin_signal({w:?})");
            if let Some(updated) = updated {
                model.commit_task(w, updated);
            }
        }
        Op::SignalReturn { who } => {
            let w = pick(registry, who);
            let want = model.expect_signal_return(w);
            let got = table.signal_return(w);
            assert_eq!(&got, &want, "signal_return({w:?})");
            if want.is_ok() {
                model.commit_signal_return(w);
            }
        }
        Op::BlockingInterrupted { who } => {
            let w = pick(registry, who);
            let want = model.expect_blocking_interrupted(w);
            let got = table.blocking_interrupted(w);
            assert_eq!(got, want, "blocking_interrupted({w:?})");
        }
        Op::ReadAction { who, sig } => {
            let w = pick(registry, who);
            let want = model.expect_signal_action(w, sig);
            let got = table.signal_action(w, sig);
            assert_eq!(got, want, "signal_action({w:?}, {sig})");
        }
        Op::SetProcessGroup { who, group } => {
            let w = pick(registry, who);
            let want = model.expect_set_process_group(w, group as u32);
            let got = table.set_process_group(w, group as u32);
            match (want, got) {
                (Ok(()), Ok(())) => model.commit_set_process_group(w, group as u32),
                (Err(we), Err(ge)) => {
                    assert_eq!(we, ge, "set_process_group({w:?}) error mismatch")
                }
                (want, got) => panic!(
                    "set_process_group({w:?}, {group}): table={got:?} model={want:?}"
                ),
            }
        }
        Op::Shutdown { status } => {
            let want = model.apply_shutdown(status as i32);
            let got = table.shutdown(status as i32);
            assert_eq!(got, want, "shutdown({status}) stopped-count mismatch");
        }
        Op::ReapAll => {
            let want = model.apply_reap_all();
            let got = table.reap_all();
            assert_eq!(got, want, "reap_all() count mismatch");
        }
    }
    assert_table_matches_model(table, model);
}

// ---------------------------------------------------------------------------
// Property tests
// ---------------------------------------------------------------------------

proptest! {
    #![proptest_config(ProptestConfig::with_cases(256))]

    /// (a) Model-based state machine: random op sequences driven against a
    /// real ProcessTable<8> and the slot-accurate reference model, with full
    /// observable-state agreement asserted after every op.
    #[test]
    fn model_matches_process_table_over_random_op_sequences(
        seq in proptest::collection::vec(arb_op(), 0..=48),
    ) {
        let mut table: ProcessTable<TASKS> = ProcessTable::new();
        let mut model = Model::new();
        let mut registry: Vec<TaskId> = Vec::new();
        for op in &seq {
            drive(op, &mut table, &mut model, &mut registry);
        }
    }

    /// (b) One-shot reaping: every dead child is reported exactly once with
    /// the exact exit/signal status, then is gone forever.
    #[test]
    fn reaping_is_one_shot_with_exact_statuses(
        count in 1usize..=7,
        statuses in proptest::collection::vec(-128i32..=255, 7),
        kill in proptest::collection::vec(any::<bool>(), 7),
        sigs in proptest::collection::vec(1u8..=64, 7),
    ) {
        let mut table: ProcessTable<TASKS> = ProcessTable::new();
        let init = table.create_init(Credentials::root()).unwrap();
        let mut children = Vec::new();
        for _ in 0..count {
            children.push(table.fork(init).unwrap());
        }
        let mut expected: Vec<(u32, ChildStatus)> = Vec::new();
        for i in 0..count {
            if kill[i] {
                table.signaled(children[i], sigs[i]).unwrap();
                expected.push((children[i].pid, ChildStatus::Signaled(sigs[i])));
            } else {
                table.exit(children[i], statuses[i]).unwrap();
                expected.push((children[i].pid, ChildStatus::Exited(statuses[i])));
            }
        }
        // WNOHANG/WUNTRACED bits are accepted and must not change semantics.
        let mut reaped: Vec<(u32, ChildStatus)> = Vec::new();
        loop {
            match table.wait(init, WaitTarget::Any, WNOHANG | WUNTRACED) {
                Ok(r) => reaped.push((r.child.pid, r.status)),
                Err(ProcessError::NoExitedChild) => break,
                Err(e) => panic!("unexpected wait error {e:?}"),
            }
        }
        reaped.sort_by_key(|e| e.0);
        expected.sort_by_key(|e| e.0);
        assert_eq!(reaped, expected, "reaped set must equal the dead set, once each");
        assert_eq!(
            table.wait(init, WaitTarget::Any, 0),
            Err(ProcessError::NoExitedChild),
            "nothing left to reap"
        );
        for (pid, _) in &expected {
            assert_eq!(
                table.wait(init, WaitTarget::Specific(*pid), 0),
                Err(ProcessError::NotChild),
                "pid {pid} must not be reapable twice"
            );
            assert_eq!(table.lookup(*pid), None, "pid {pid} must be gone");
        }
        assert_eq!(table.active(), 1, "only init remains");
    }

    /// (b) wait only ever reports dead DIRECT children of the caller
    /// (leader-only, parent-tgid ownership); running children give
    /// NoExitedChild, grandchildren give NotChild, and a running parent
    /// shields its whole subtree from its own parent.
    #[test]
    fn wait_returns_only_dead_direct_children_of_the_caller(
        n_children in 1usize..=3,
        n_grandchildren in 0usize..=3,
        kill in proptest::collection::vec(any::<bool>(), 3),
        statuses in proptest::collection::vec(-128i32..=255, 3),
        gstatus in -128i32..=255,
    ) {
        let mut table: ProcessTable<TASKS> = ProcessTable::new();
        let init = table.create_init(Credentials::root()).unwrap();
        let shell = table.fork(init).unwrap();
        let mut children = Vec::new();
        for _ in 0..n_children {
            children.push(table.fork(shell).unwrap());
        }
        let mut grandchildren = Vec::new();
        for c in children.iter().take(n_grandchildren) {
            grandchildren.push(table.fork(*c).unwrap());
        }
        // Grandchild zombie while every child still runs: invisible to the
        // grandparent and to init (the running shell shields its subtree).
        if let Some(g) = grandchildren.first().copied() {
            table.exit(g, gstatus).unwrap();
            assert_eq!(
                table.wait(shell, WaitTarget::Any, 0),
                Err(ProcessError::NoExitedChild),
                "grandchild zombie must be invisible to the grandparent"
            );
            assert_eq!(
                table.wait(init, WaitTarget::Any, 0),
                Err(ProcessError::NoExitedChild),
                "the running shell shields its subtree from init"
            );
            assert_eq!(
                table.wait(shell, WaitTarget::Specific(g.pid), 0),
                Err(ProcessError::NotChild)
            );
            assert_eq!(
                table.has_waitable_child(shell, WaitTarget::Specific(g.pid)),
                Ok(false)
            );
        }
        let mut dead: Vec<(u32, i32)> = Vec::new();
        for (i, c) in children.iter().enumerate() {
            if kill[i] {
                table.exit(*c, statuses[i]).unwrap();
                dead.push((c.pid, statuses[i]));
            }
        }
        for c in &children {
            if !dead.iter().any(|(pid, _)| *pid == c.pid) {
                assert_eq!(
                    table.wait(shell, WaitTarget::Specific(c.pid), 0),
                    Err(ProcessError::NoExitedChild),
                    "running child is not reportable"
                );
                assert_eq!(
                    table.has_waitable_child(shell, WaitTarget::Specific(c.pid)),
                    Ok(true),
                    "a running child still counts as waitable"
                );
            }
        }
        // A dead child is reportable by pid exactly once...
        if let Some((pid, code)) = dead.first().copied() {
            let c = children.iter().find(|c| c.pid == pid).unwrap();
            let r = table.wait(shell, WaitTarget::Specific(c.pid), 0).unwrap();
            assert_eq!(r.child, *c);
            assert_eq!(r.status, ChildStatus::Exited(code));
            assert_eq!(
                table.wait(shell, WaitTarget::Specific(c.pid), 0),
                Err(ProcessError::NotChild),
                "reaped child must not be reapable twice"
            );
        }
        // ...and an Any-drain returns the remaining dead children exactly.
        let mut drained: Vec<u32> = Vec::new();
        loop {
            match table.wait(shell, WaitTarget::Any, 0) {
                Ok(r) => drained.push(r.child.pid),
                Err(ProcessError::NoExitedChild) => break,
                Err(e) => panic!("unexpected wait error {e:?}"),
            }
        }
        drained.sort_unstable();
        let mut want_dead: Vec<u32> = dead
            .iter()
            .skip(usize::from(!dead.is_empty()))
            .map(|(pid, _)| *pid)
            .collect();
        want_dead.sort_unstable();
        assert_eq!(drained, want_dead, "Any-drain must report exactly the dead children");
        for (pid, _) in &dead {
            assert_eq!(table.lookup(*pid), None, "pid {pid} must be gone");
        }
        let running_left = n_children - dead.len();
        assert_eq!(
            table.has_waitable_child(shell, WaitTarget::Any),
            Ok(running_left > 0)
        );
        assert_eq!(table.has_waitable_child(init, WaitTarget::Any), Ok(true));
    }

    /// (b) adopt_orphans: children are handed to init only once the LAST
    /// thread of their parent group dies, and both zombie and running
    /// orphans stay waitable by init afterwards.
    #[test]
    fn adoption_reparents_children_to_init_and_preserves_waitability(
        with_thread in any::<bool>(),
        child_exits_first in any::<bool>(),
        mid_status in -128i32..=255,
        child_status in -128i32..=255,
    ) {
        let mut table: ProcessTable<TASKS> = ProcessTable::new();
        let init = table.create_init(Credentials::root()).unwrap();
        let mid = table.fork(init).unwrap();
        let child = table.fork(mid).unwrap();
        let thread = if with_thread {
            Some(table.clone_thread(mid).unwrap())
        } else {
            None
        };
        if child_exits_first {
            table.exit(child, child_status).unwrap();
        }
        // Before the whole mid group is dead the child stays with mid.
        assert_eq!(table.view(child).unwrap().parent, mid.pid);
        assert_eq!(
            table.wait(init, WaitTarget::Specific(child.pid), 0),
            Err(ProcessError::NotChild),
            "init must not reap a child it does not own yet"
        );
        if let Some(t) = thread {
            table.exit(mid, mid_status).unwrap();
            // Leader zombie but its thread still runs: children keep mid.
            assert_eq!(
                table.view(child).unwrap().parent,
                mid.pid,
                "children stay with the process while a thread runs"
            );
            table.exit(t, 0).unwrap();
            table.reap_thread(t).unwrap();
        } else {
            table.exit(mid, mid_status).unwrap();
        }
        // Last thread of mid gone: orphan handed to init (parent pid 1).
        assert_eq!(table.view(child).unwrap().parent, 1, "orphan adopted by init");
        if child_exits_first {
            let r = table.wait(init, WaitTarget::Specific(child.pid), 0).unwrap();
            assert_eq!(r.child, child);
            assert_eq!(r.status, ChildStatus::Exited(child_status));
        } else {
            assert_eq!(
                table.wait(init, WaitTarget::Specific(child.pid), 0),
                Err(ProcessError::NoExitedChild),
                "running orphan waitable-but-not-reportable"
            );
            table.exit(child, child_status).unwrap();
            let r = table.wait(init, WaitTarget::Specific(child.pid), 0).unwrap();
            assert_eq!(r.status, ChildStatus::Exited(child_status));
        }
        // mid itself is reaped by init exactly once.
        assert_eq!(
            table.wait(init, WaitTarget::Specific(mid.pid), 0).unwrap().status,
            ChildStatus::Exited(mid_status)
        );
        assert_eq!(
            table.wait(init, WaitTarget::Specific(mid.pid), 0),
            Err(ProcessError::NotChild)
        );
    }

    /// (b) Capacity is hard: zombies still occupy slots, fork fails closed
    /// with TableFull at 8, reaping frees exactly one slot, pids are never
    /// reused, and active() never exceeds 8.
    #[test]
    fn table_capacity_is_hard_enforced_at_eight(cycles in 0usize..=4) {
        let mut table: ProcessTable<TASKS> = ProcessTable::new();
        let init = table.create_init(Credentials::root()).unwrap();
        let mut cohort: Vec<TaskId> = Vec::new();
        for _ in 0..TASKS - 1 {
            cohort.push(table.fork(init).unwrap());
            assert!(table.active() <= TASKS);
        }
        assert_eq!(table.active(), TASKS);
        assert_eq!(table.fork(init), Err(ProcessError::TableFull));
        // A zombie still occupies its slot: exit without reaping stays full.
        table.exit(cohort[0], 7).unwrap();
        assert_eq!(table.active(), TASKS, "zombie must still occupy a slot");
        assert_eq!(table.fork(init), Err(ProcessError::TableFull));
        // Reaping frees exactly one slot; the new pid is fresh.
        table.wait(init, WaitTarget::Any, 0).unwrap();
        assert_eq!(table.active(), TASKS - 1);
        let mut current = table.fork(init).unwrap();
        assert_eq!(table.active(), TASKS);
        assert_ne!(current.pid, cohort[0].pid, "pids are never reused");
        for i in 0..cycles {
            table.exit(current, i as i32).unwrap();
            assert_eq!(table.active(), TASKS, "zombie holds the slot");
            table.wait(init, WaitTarget::Any, 0).unwrap();
            assert_eq!(table.active(), TASKS - 1);
            current = table.fork(init).unwrap();
            assert_eq!(table.active(), TASKS);
            assert!(table.active() <= TASKS);
        }
        // Bulk teardown: shutdown marks every running task, reap_all clears.
        let running = table.active();
        assert_eq!(table.shutdown(137), running);
        assert_eq!(table.reap_all(), running);
        assert_eq!(table.active(), 0, "shutdown+reap_all must empty the table");
    }

    /// (b)+(e) Error cleanliness: bogus wait selectors, zombie waiters,
    /// reaped identities, and invalid signal numbers all return typed
    /// errors and never panic. Signal-number validity is checked before
    /// task identity in `signal`/`signaled`.
    #[test]
    fn bad_wait_and_signal_targets_error_cleanly_without_panicking(
        wild in any::<u32>(),
        sig in 0u8..=100,
        status in -128i32..=255,
    ) {
        let mut table: ProcessTable<TASKS> = ProcessTable::new();
        let init = table.create_init(Credentials::root()).unwrap();
        let child = table.fork(init).unwrap();
        assert_eq!(
            table.wait(init, WaitTarget::Specific(0), 0),
            Err(ProcessError::NotChild)
        );
        assert_eq!(
            table.wait(init, WaitTarget::Specific(u32::MAX), 0),
            Err(ProcessError::NotChild)
        );
        assert_eq!(
            table.wait(child, WaitTarget::Specific(init.pid), 0),
            Err(ProcessError::NotChild)
        );
        let wild_pid = if wild == init.pid || wild == child.pid || wild == u32::MAX {
            child.pid + 3
        } else {
            wild
        };
        assert_eq!(
            table.wait(init, WaitTarget::Specific(wild_pid), 0),
            Err(ProcessError::NotChild)
        );
        assert_eq!(
            table.wait(init, WaitTarget::Specific(child.pid), 0),
            Err(ProcessError::NoExitedChild)
        );
        assert_eq!(
            table.wait(init, WaitTarget::Group(wild_pid), 0),
            Err(ProcessError::NoExitedChild)
        );
        assert_eq!(
            table.has_waitable_child(init, WaitTarget::Group(wild_pid)),
            Ok(false)
        );
        // Options bits (even out-of-range garbage) are accepted and inert.
        assert_eq!(
            table.wait(init, WaitTarget::Specific(child.pid), ginux_process::WAIT_ALLOWED_OPTIONS | wild),
            Err(ProcessError::NoExitedChild)
        );
        // A zombie parent is not a valid waiter.
        table.exit(child, status).unwrap();
        assert_eq!(table.wait(child, WaitTarget::Any, 0), Err(ProcessError::InvalidState));
        assert_eq!(
            table.has_waitable_child(child, WaitTarget::Any),
            Err(ProcessError::InvalidState)
        );
        // After reaping, every id-keyed op fails cleanly.
        table.wait(init, WaitTarget::Specific(child.pid), 0).unwrap();
        assert_eq!(table.view(child), Err(ProcessError::InvalidTask));
        assert_eq!(table.lookup(child.pid), None);
        assert_eq!(table.next_signal(child), Err(ProcessError::InvalidTask));
        assert_eq!(table.blocking_interrupted(child), Err(ProcessError::InvalidTask));
        assert_eq!(
            table.set_signal_mask(child, wild as u64),
            Err(ProcessError::InvalidTask)
        );
        let want_signal_err = if sig == 0 || sig > MAX_SIGNAL {
            ProcessError::InvalidSignal
        } else {
            ProcessError::InvalidTask
        };
        assert_eq!(table.signal(child, sig), Err(want_signal_err));
        // Validity-first ordering in `signaled` too.
        assert_eq!(table.signaled(child, 0), Err(ProcessError::InvalidSignal));
        assert_eq!(table.signaled(child, MAX_SIGNAL + 1), Err(ProcessError::InvalidSignal));
        assert_eq!(
            table.signaled(child, sig.clamp(1, MAX_SIGNAL)),
            Err(ProcessError::InvalidTask)
        );
    }

    /// (c) Mask set/clear semantics: delivery is exactly pending minus the
    /// stored mask (request minus SIGKILL/SIGSTOP), ascending by signal
    /// number, consuming each notification once; masked signals survive
    /// until the mask clears; duplicates collapse; SIGKILL/SIGSTOP can
    /// never be masked. (No public mask getter exists, so the contract is
    /// observed through next_signal/blocking_interrupted behavior.)
    #[test]
    fn signal_mask_gates_delivery_and_never_blocks_kill_stop(
        mask in any::<u64>(),
        arrivals in proptest::collection::vec(1u8..=64, 12),
    ) {
        let mut table: ProcessTable<TASKS> = ProcessTable::new();
        let init = table.create_init(Credentials::root()).unwrap();
        let mut pending: u64 = 0;
        for s in &arrivals {
            table.signal(init, *s).unwrap();
            pending |= 1u64 << (*s - 1);
        }
        table.set_signal_mask(init, mask).unwrap();
        let stored = mask & !UNBLOCKABLE;
        assert_eq!(
            table.blocking_interrupted(init),
            Ok(pending & !stored != 0),
            "blocking_interrupted must mirror pending & !mask"
        );
        let drained = drain_all(&mut table, init);
        let want: Vec<u8> = (1u32..=64)
            .filter(|s| {
                pending & (1u64 << (s - 1)) != 0 && stored & (1u64 << (s - 1)) == 0
            })
            .map(|s| s as u8)
            .collect();
        assert_eq!(drained, want, "delivery must be ascending and mask-respecting");
        assert_eq!(table.blocking_interrupted(init), Ok(false));
        // Masked signals are still pending: clearing the mask releases exactly
        // the leftovers (pending minus what was already delivered).
        table.set_signal_mask(init, 0).unwrap();
        let drained2 = drain_all(&mut table, init);
        let want2: Vec<u8> = (1u32..=64)
            .filter(|s| {
                pending & (1u64 << (s - 1)) != 0 && stored & (1u64 << (s - 1)) != 0
            })
            .map(|s| s as u8)
            .collect();
        assert_eq!(drained2, want2, "masked signals survive until the mask clears");
        // SIGKILL/SIGSTOP can never be masked, even with an all-ones request;
        // an ordinary signal (15) sent alongside stays masked behind them.
        table.set_signal_mask(init, u64::MAX).unwrap();
        table.signal(init, 9).unwrap();
        table.signal(init, 19).unwrap();
        table.signal(init, 15).unwrap();
        assert_eq!(table.next_signal(init), Ok(Some(9)));
        assert_eq!(table.next_signal(init), Ok(Some(19)));
        assert_eq!(table.next_signal(init), Ok(None), "15 stays masked");
    }

    /// (c) Handler frames: a handler delivery auto-masks its own signal and
    /// saves the pre-handler mask; nested deliveries with Default/Ignore
    /// actions still proceed, a nested Handler is refused with the pending
    /// bit preserved; sigreturn restores the saved mask exactly and a
    /// double sigreturn fails.
    #[test]
    fn handler_frames_block_only_handler_delivery_and_restore_mask(
        sig in (1u8..=64).prop_filter("must be blockable", |s| *s != 9 && *s != 19),
        other in (1u8..=64).prop_filter("must be blockable", |s| *s != 9 && *s != 19),
        nested_kind in 0u8..3,
        addr in any::<u64>(),
        pre_mask in any::<u64>(),
    ) {
        prop_assume!(sig != other);
        let mut table: ProcessTable<TASKS> = ProcessTable::new();
        let init = table.create_init(Credentials::root()).unwrap();
        // Pre-handler mask with both test signals left deliverable.
        let request = pre_mask & !(1u64 << (sig - 1)) & !(1u64 << (other - 1));
        table.set_signal_mask(init, request).unwrap();
        table
            .set_signal_action(init, sig, SignalAction::Handler(addr))
            .unwrap();
        let nested_action = match nested_kind {
            0 => SignalAction::Default,
            1 => SignalAction::Ignore,
            _ => SignalAction::Handler(addr.wrapping_add(0x1000)),
        };
        table.set_signal_action(init, other, nested_action).unwrap();
        table.signal(init, sig).unwrap();
        assert_eq!(
            table.begin_signal(init),
            Ok(Some(SignalDelivery::Handler { signal: sig, address: addr }))
        );
        // Frame active: the handler signal is auto-masked, resends stay pending.
        table.signal(init, sig).unwrap();
        assert_eq!(
            table.next_signal(init),
            Ok(None),
            "handler signal must be masked during its own frame"
        );
        // Non-Handler actions deliver even during a frame.
        table.signal(init, other).unwrap();
        let want_nested = match nested_kind {
            0 => Ok(Some(SignalDelivery::Default(other))),
            1 => Ok(Some(SignalDelivery::Ignored(other))),
            _ => Err(ProcessError::InvalidState),
        };
        assert_eq!(
            table.begin_signal(init),
            want_nested,
            "nested delivery of signal {other}"
        );
        if nested_kind == 2 {
            assert_eq!(
                table.blocking_interrupted(init),
                Ok(true),
                "refused nested handler signal stays pending"
            );
        }
        // sigreturn restores the pre-handler mask exactly; double return fails.
        table.signal_return(init).unwrap();
        assert_eq!(
            table.signal_return(init),
            Err(ProcessError::InvalidState),
            "double sigreturn must fail"
        );
        // After the return the re-sent handler signal (plus a refused nested
        // handler signal) is deliverable again, in ascending order.
        let mut want_after: Vec<u8> = if nested_kind == 2 {
            vec![sig, other]
        } else {
            vec![sig]
        };
        want_after.sort_unstable();
        for want in want_after {
            assert_eq!(table.next_signal(init), Ok(Some(want)));
        }
        assert_eq!(
            table.next_signal(init),
            Ok(None),
            "queue must be empty at the end"
        );
    }

    /// (c) fork/exec signal-state rules (PR #191 family): fork copies mask
    /// and dispositions but NOT the pending set; exec resets caught
    /// dispositions to Default, keeps Ignore, keeps pending and mask, and
    /// bumps the exec epoch monotonically.
    #[test]
    fn fork_copies_mask_and_dispositions_not_pending_and_exec_resets_dispositions(
        mask in any::<u64>(),
        handler_sig in (1u8..=64).prop_filter("must be blockable", |s| *s != 9 && *s != 19),
        ignored_sig in (1u8..=64).prop_filter("must be blockable", |s| *s != 9 && *s != 19),
        plain_sig in 1u8..=64,
        pending_sig in 1u8..=64,
        addr in any::<u64>(),
    ) {
        prop_assume!(handler_sig != ignored_sig);
        prop_assume!(plain_sig != handler_sig && plain_sig != ignored_sig);
        let mut table: ProcessTable<TASKS> = ProcessTable::new();
        let init = table.create_init(Credentials::root()).unwrap();
        table
            .set_signal_mask(init, mask | (1u64 << (handler_sig - 1)))
            .unwrap();
        table
            .set_signal_action(init, handler_sig, SignalAction::Handler(addr))
            .unwrap();
        table
            .set_signal_action(init, ignored_sig, SignalAction::Ignore)
            .unwrap();
        // Pending on the parent must NOT leak into the child.
        table.signal(init, pending_sig).unwrap();
        let child = table.fork(init).unwrap();
        // Dispositions copied verbatim.
        assert_eq!(
            table.signal_action(child, handler_sig),
            Ok(SignalAction::Handler(addr))
        );
        assert_eq!(
            table.signal_action(child, ignored_sig),
            Ok(SignalAction::Ignore)
        );
        assert_eq!(
            table.signal_action(child, plain_sig),
            Ok(SignalAction::Default)
        );
        // Pending set starts empty on the child.
        assert_eq!(table.next_signal(child), Ok(None));
        assert_eq!(table.blocking_interrupted(child), Ok(false));
        // The copied mask behaves identically in the child.
        table.signal(child, handler_sig).unwrap();
        assert_eq!(
            table.next_signal(child),
            Ok(None),
            "copied mask must still block the handler signal"
        );
        // exec: reset caught dispositions, keep Ignore, pending, and mask.
        assert_eq!(table.exec(child), Ok(1));
        assert_eq!(
            table.signal_action(child, handler_sig),
            Ok(SignalAction::Default)
        );
        assert_eq!(
            table.signal_action(child, ignored_sig),
            Ok(SignalAction::Ignore)
        );
        assert_eq!(
            table.signal_action(child, plain_sig),
            Ok(SignalAction::Default)
        );
        assert_eq!(
            table.next_signal(child),
            Ok(None),
            "pending survives exec under the kept mask"
        );
        table.set_signal_mask(child, 0).unwrap();
        assert_eq!(table.next_signal(child), Ok(Some(handler_sig)));
        assert_eq!(table.next_signal(child), Ok(None));
        // exec epochs count monotonically per task.
        assert_eq!(table.exec(child), Ok(2));
    }
}

/// Drain `next_signal` until empty (used by the mask property).
fn drain_all(table: &mut ProcessTable<TASKS>, who: TaskId) -> Vec<u8> {
    let mut out = Vec::new();
    loop {
        match table.next_signal(who).unwrap() {
            Some(sig) => out.push(sig),
            None => break,
        }
    }
    out
}
