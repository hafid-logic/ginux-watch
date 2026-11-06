/* poc207_t123.c — v5.6: T1–T3 multi-thread PoC for PR #207 bootstrap_poll_allowed,
 * with calibrated detection criteria and built-in controls.
 *
 * Standalone harness (OUR repo only; zero writes inside the PR #207 tree).
 * Replicates ginux-init's PEEKDATA gate (channel_hooks.rs:13-37, MAX=16,
 * reject fd>2, fail-closed) in a ptrace PTRACE_SYSCALL supervisor, then races
 * it against a two-thread tracee whose sibling flips fds[1].fd without pause.
 *
 * v5.6 CHANGE (calibration; supersedes v5.3-5 criteria, which are INVALIDATED —
 * see inbox/evidence/2026-11-06-222-evidence/04-poc207-recalibration.md):
 *   The old criterion counted `revents != 0 && fd_post > 2` on slot 1. If the
 *   tracee's fd 0 was /dev/null (POLLIN) or closed (POLLNVAL) — the runner
 *   default — a poll that legitimately executed on fd 0 still produced
 *   revents != 0, and a sibling flip before the exit-stop read completed the
 *   false positive. MEASURED on one sandbox machine, old criterion, 1M polls
 *   each: fd0=/dev/null -> 283,621 hits; fd0=closed -> 295,156/286,149;
 *   fd0=pipe+open writer -> 1,145/1,046. The ~18% "divergence" reported from
 *   runners was mostly detector artifact.
 *   FIX: the tracee now creates its OWN fd 0 = read end of an empty pipe whose
 *   write end stays open (poll -> revents==0 deterministically), and:
 *     T1 counts: gate snapshot said 0 AND kernel wrote POLLNVAL  (fd 0 is open,
 *                so POLLNVAL on slot 1 can only mean the kernel copied a value
 *                that is not open -- the sentinel);
 *     T3 counts: gate snapshot said 0 AND kernel wrote POLLHUP  (fd 3 is a
 *                fifo read end with closed writer; fd 0 cannot produce HUP);
 *     the fd_post exit-read requirement is REMOVED (it both inflated and
 *     missed: hit required the sibling to still hold the flipped value at the
 *     exit stop, a second race layered on the first).
 *   CONTROLS (no result without its control):
 *     ctl_a: fds[1].fd fixed 0, gate active   -> expect zero nonzero revents;
 *     ctl_b: fds[1].fd fixed sentinel, gate in observe-only -> expect POLLNVAL
 *            on 100% of executed polls (signature calibration);
 *     ctl_c: fds[1].fd fixed 3 (fifo HUP), gate observe-only -> expect POLLHUP
 *            on 100% of executed polls.
 *   ALSO FIXED: the tracee now parses the iteration count/mode passed by the
 *   supervisor (v5.3-5 silently ignored argv and always ran 1,000,000).
 *
 *   T2 (window width): CLOCK_MONOTONIC around the PEEKDATA gate loop = check
 *      window; min/med/max ns (unchanged from v5.3).
 *
 * MEASURED/INFERRED discipline: all counts printed are MEASURED on the runner;
 * generalization to ginux's fd-table invariant stays INFERRED (harness-only).
 * Build: cc -O2 -Wall -o poc207_t123 poc207_t123.c
 * Usage: ./poc207_t123 <iterations> <t1|t3|ctl_a|ctl_b|ctl_c>
 */
#define _GNU_SOURCE
#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <fcntl.h>
#include <sched.h>
#include <sys/mman.h>
#include <sys/ptrace.h>
#include <sys/syscall.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/user.h>
#include <poll.h>
#include <sys/wait.h>
#include <linux/ptrace.h>

#define MAX_BOOTSTRAP_POLL_FDS 16      /* ginux-core/src/lib.rs:5 */
#define SENTINEL 0x7ffffffe            /* >2, positive, poll() => POLLNVAL */
#define WRITER_FD 9                    /* tracee parks the pipe writer here */
#define SYS_POLL_X86_64 7

enum mode { M_T1, M_T3, M_CTL_A, M_CTL_B, M_CTL_C, M_BAD };
static const char *mode_name[] = { "t1", "t3", "ctl_a", "ctl_b", "ctl_c", "bad" };

static enum mode g_mode = M_T1;        /* supervisor side, from argv */
static int g_obs = 0;                  /* observe-only gate (ctl_b/ctl_c) */
static long g_iters     = 1000000;
static long g_wall_cap_s = 600;

static void die(const char *m){ perror(m); _exit(111); }

static double now_s(void){
  struct timespec ts; clock_gettime(CLOCK_MONOTONIC,&ts);
  return (double)ts.tv_sec + (double)ts.tv_nsec/1e9;
}

static enum mode parse_mode(const char *s){
  if (!strcmp(s,"t1")) return M_T1;
  if (!strcmp(s,"t3")) return M_T3;
  if (!strcmp(s,"ctl_a")) return M_CTL_A;
  if (!strcmp(s,"ctl_b")) return M_CTL_B;
  if (!strcmp(s,"ctl_c")) return M_CTL_C;
  return M_BAD;
}

/* ---------------- tracee ---------------- */
struct pollfd g_fds[2];
static volatile int g_run = 1;
static volatile int g_flip = 0;        /* 1=0<->sentinel 2=0<->fd3 3=const0 4=const sentinel 5=const fd3 */
static volatile int g_real_fd = 3;

static int sibling_fn(void *arg){
  (void)arg;
  unsigned s = SENTINEL;
  while (__atomic_load_n(&g_run, __ATOMIC_RELAXED)) {
    switch (__atomic_load_n(&g_flip, __ATOMIC_RELAXED)) {
    case 1:
      __atomic_store_n(&g_fds[1].fd, 0, __ATOMIC_RELAXED);
      syscall(SYS_sched_yield);
      __atomic_store_n(&g_fds[1].fd, (int)s, __ATOMIC_RELAXED);
      syscall(SYS_sched_yield);
      break;
    case 2:
      __atomic_store_n(&g_fds[1].fd, 0, __ATOMIC_RELAXED);
      syscall(SYS_sched_yield);
      __atomic_store_n(&g_fds[1].fd, g_real_fd, __ATOMIC_RELAXED);
      syscall(SYS_sched_yield);
      break;
    case 3:
      __atomic_store_n(&g_fds[1].fd, 0, __ATOMIC_RELAXED);
      break;
    case 4:
      __atomic_store_n(&g_fds[1].fd, (int)s, __ATOMIC_RELAXED);
      break;
    case 5:
      __atomic_store_n(&g_fds[1].fd, g_real_fd, __ATOMIC_RELAXED);
      break;
    default:
      syscall(SYS_sched_yield);
      break;
    }
  }
  syscall(SYS_exit, 0);
  return 0;
}

static int tracee_main(void){
  const char *it = getenv("POC207_ITERS");
  const char *fl = getenv("POC207_FLIP");
  if (it) g_iters = strtol(it, NULL, 0);
  if (fl) g_flip = atoi(fl);

  setvbuf(stdout,NULL,_IONBF,0);
  raise(SIGSTOP);   /* park until the supervisor SEIZEs us */

  /* v5.6: fd 0 = read end of an empty pipe, write end kept open at fd 9.
     poll(fd0) therefore returns revents==0 deterministically, independent of
     how the harness was launched (runners give /dev/null or a closed fd 0,
     which poisoned the v5.3 detector). Works whether inherited fd 0 was open
     or closed: pipe() fills the lowest free slot either way. */
  int p[2];
  if (pipe(p)) die("pipe");
  if (p[0] != 0) { if (dup2(p[0], 0) < 0) die("dup2 rd"); close(p[0]); }
  if (p[1] != WRITER_FD) { if (dup2(p[1], WRITER_FD) < 0) die("dup2 wr"); close(p[1]); }

  if (g_flip == 2 || g_flip == 5) {   /* t3 / ctl_c need the real HUP fd */
    int fd = open("/tmp/poc207-fifo", O_RDONLY | O_NONBLOCK);
    if (fd != 3) { dprintf(2,"T3 setup: expected fd 3, got %d (errno %d)\n", fd, errno); _exit(112); }
    /* Writer must open AFTER this read end exists and close while it is held:
       [MEASURED sandbox] a FIFO read end opened after the writer's open+close
       episode reports NO revents at all (virgin-read-end state); a read end
       that predates the writer episode reports POLLHUP deterministically. */
    int w = open("/tmp/poc207-fifo", O_WRONLY | O_NONBLOCK);
    if (w < 0) die("open fifo writer");
    close(w);
    g_real_fd = fd;
  }

  g_fds[0].fd = 0; g_fds[0].events = POLLIN; g_fds[0].revents = 0;
  g_fds[1].fd = 0; g_fds[1].events = POLLIN; g_fds[1].revents = 0;

  size_t ssz = 256*1024;
  char *stk = mmap(NULL, ssz, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
  if (stk == MAP_FAILED) die("mmap");
  int tid = clone(sibling_fn, stk+ssz,
      CLONE_VM|CLONE_FS|CLONE_FILES|CLONE_SIGHAND|CLONE_THREAD|CLONE_SYSVSEM, NULL);
  if (tid < 0) die("clone");

  for (long i=0;i<g_iters;i++) {
    g_fds[1].revents = 0;
    syscall(SYS_poll, g_fds, 2, 0);
  }
  __atomic_store_n(&g_run, 0, __ATOMIC_RELAXED);
  struct timespec ts = {0, 200*1000*1000}; nanosleep(&ts, NULL);
  _exit(0);
}

/* ---------------- supervisor ---------------- */
static pid_t g_leader, g_sibling_tid;
struct wins { double *v; size_t n, cap; };
static struct wins g_win;
static void win_push(double ns){
  if (g_win.n == g_win.cap) {
    g_win.cap = g_win.cap ? g_win.cap*2 : 4096;
    g_win.v = realloc(g_win.v, g_win.cap*sizeof(double));
    if (!g_win.v) die("realloc");
  }
  g_win.v[g_win.n++] = ns;
}
static int cmpd(const void *a, const void *b){
  double x = *(const double*)a, y = *(const double*)b;
  return x<y?-1:(x>y?1:0);
}
/* Supervision model (unchanged from v5.3-5): PTRACE_SYSCALL, not SYSEMU.
 * Rationale [MEASURED 2026-11-06, sandbox and ubuntu-24.04 runner]: resuming a
 * SYSEMU-armed entry stop with PTRACE_SYSCALL does not reliably execute the
 * syscall (mmap returned -ENOSYS, exit_group skipped). PTRACE_SYSCALL keeps
 * the structural question intact: the gate decides from a PEEKDATA snapshot
 * at entry; the kernel copies the LIVE pollfd array at execution after resume.
 * A PTRACE_SYSCALL supervisor has a LARGER decision latency than ginux's
 * SYSEMU supervisor — detection-favorable, and stated as such.
 * Denial emulation = orig_rax = -1 at entry, rax = -EBUSY at exit. In
 * observe-only mode (ctl_b/ctl_c) the gate decision is RECORDED but never
 * enforced, so the kernel always executes the poll. */

struct pend {
  pid_t tid;
  int used, allow, have1;
  unsigned long addr;
  int32_t snap1;
};
static struct pend g_pend[64];

static struct pend *pend_get(pid_t t, int create){
  struct pend *free_slot = NULL;
  for (int i=0;i<64;i++) {
    if (g_pend[i].used && g_pend[i].tid == t) return &g_pend[i];
    if (!g_pend[i].used && !free_slot) free_slot = &g_pend[i];
  }
  if (create && free_slot) { memset(free_slot,0,sizeof *free_slot); free_slot->used=1; free_slot->tid=t; return free_slot; }
  return NULL;
}

static long peek_word(pid_t t, unsigned long addr, unsigned long *out){
  errno = 0;
  long w = ptrace(PTRACE_PEEKDATA, t, (void*)addr, NULL);
  if (errno) return -1;                    /* fail-closed like channel_hooks */
  *out = (unsigned long)w;
  return 0;
}

int main(int argc, char **argv){
  if (getenv("POC207_TRACEE")) return tracee_main();
  if (argc > 1) g_iters = strtol(argv[1], NULL, 0);
  if (argc > 2) { g_mode = parse_mode(argv[2]); if (g_mode == M_BAD) { fprintf(stderr,"mode must be t1|t3|ctl_a|ctl_b|ctl_c\n"); _exit(109); } }
  g_obs = (g_mode == M_CTL_B || g_mode == M_CTL_C);
  int flip = (g_mode==M_T1)?1:(g_mode==M_T3)?2:(g_mode==M_CTL_A)?3:(g_mode==M_CTL_B)?4:5;

  if (g_mode == M_T3 || g_mode == M_CTL_C) {
    unlink("/tmp/poc207-fifo");
    if (mkfifo("/tmp/poc207-fifo", 0600)) die("mkfifo");
    /* The tracee itself opens its read end first, then opens+closes the
       writer — that ordering is what makes POLLHUP deterministic
       [MEASURED: see tracee_main]. The supervisor opens nothing, so no
       fd bookkeeping can leak into the tracee via exec. */
  }

  g_leader = fork();
  if (g_leader < 0) die("fork");
  if (g_leader == 0) {
    char iters[32]; snprintf(iters,sizeof iters,"%ld",g_iters);
    char fl[8];     snprintf(fl,sizeof fl,"%d",flip);
    setenv("POC207_TRACEE","1",1);
    setenv("POC207_ITERS",iters,1);   /* v5.6: tracee parses env (argv bug fix) */
    setenv("POC207_FLIP",fl,1);
    execl("/proc/self/exe","poc207-tracee",(char*)NULL);
    _exit(110);
  }

  int st;
  /* child parks itself with SIGSTOP right after exec; WUNTRACED is required
     to see that job-control stop from a non-traced child */
  if (waitpid(g_leader,&st,WUNTRACED)<0) die("wait pre-stop");
  if (getenv("POC207_DEBUG")) fprintf(stderr,"PREWAIT st=0x%x stopped=%d sig=%d\n", st, WIFSTOPPED(st), WIFSTOPPED(st)?WSTOPSIG(st):0);
  if (!WIFSTOPPED(st)) { fprintf(stderr,"child did not stop\n"); kill(g_leader,SIGKILL); _exit(110); }
  if (ptrace(PTRACE_SEIZE, g_leader, NULL,
        (void*)(unsigned long)(PTRACE_O_TRACESYSGOOD|PTRACE_O_TRACECLONE))) die("SEIZE");
  /* seizing a group-stopped tracee re-reports it as PTRACE_EVENT_STOP */
  if (waitpid(g_leader,&st,__WALL)<0) die("wait seize-stop");
  fprintf(stderr,"FIRST_EVENT st=0x%x\n", st);
  if (ptrace(PTRACE_SYSCALL, g_leader, NULL, NULL)) die("SYSCALL resume");

  long polls=0, denied=0, executed=0, snap_invalid=0, peek_fail=0;
  long nval_total=0, hup_total=0, in_total=0, err_total=0, other_total=0, zero_total=0;
  long nval_on_snap0=0, hup_on_snap0=0;
  double t0 = now_s();
  int leader_live = 1;
  int first_ev = 1;

  while (leader_live) {
    if (now_s() - t0 > (double)g_wall_cap_s) break;
    pid_t t = waitpid(-1, &st, __WALL);
    if (t < 0) { if (errno==EINTR) continue; die("waitpid"); }

    if (WIFEXITED(st) || WIFSIGNALED(st)) {
      if (getenv("POC207_DEBUG")) fprintf(stderr,"DEAD t=%d exited=%d sig=%d leader=%d\n", t, WIFEXITED(st)?WEXITSTATUS(st):-1, WIFSIGNALED(st)?WTERMSIG(st):-1, t==g_leader);
      if (t == g_leader) leader_live = 0;
      continue;
    }
    int sig = WSTOPSIG(st);
    unsigned event = (unsigned)st >> 16;
    if (first_ev) { fprintf(stderr,"FIRST_EVENT st=0x%x\n", st); first_ev = 0; }

    if (sig == SIGTRAP && event == PTRACE_EVENT_CLONE) {
      unsigned long ntid = 0;
      ptrace(PTRACE_GETEVENTMSG, t, NULL, &ntid);
      g_sibling_tid = (pid_t)ntid;
      ptrace(PTRACE_SYSCALL, (pid_t)ntid, NULL, NULL);
      ptrace(PTRACE_SYSCALL, t, NULL, NULL);
      continue;
    }
    if (sig == SIGTRAP && event == PTRACE_EVENT_EXIT) {
      ptrace(PTRACE_CONT, t, NULL, NULL);
      continue;
    }
    if (sig != (SIGTRAP|0x80)) {
      if (sig == SIGSEGV || sig == SIGILL || sig == SIGBUS || sig == SIGFPE) {
        fprintf(stderr,"FATAL tracee fault sig=%d tid=%d (aborting harness run)\n", sig, t);
        kill(g_leader, SIGKILL);
        leader_live = 0;
        break;
      }
      ptrace(PTRACE_SYSCALL, t, NULL, NULL);
      continue;
    }

    struct ptrace_syscall_info si; memset(&si,0,sizeof si);
    if (ptrace(PTRACE_GET_SYSCALL_INFO, t, (void*)sizeof si, &si) < 0) {
      ptrace(PTRACE_SYSCALL, t, NULL, NULL); continue;
    }

    if (si.op == PTRACE_SYSCALL_INFO_ENTRY) {
      int is_leader_poll = (t == g_leader && si.entry.nr == SYS_POLL_X86_64);
      if (getenv("POC207_DEBUG")) fprintf(stderr,"SC t=%d op=%d nr=%lld%s\n", t, si.op, (long long)si.entry.nr, is_leader_poll?" POLL":"");
      if (is_leader_poll) {
        struct pend *p = pend_get(t, 1);
        p->addr = si.entry.args[0];
        unsigned long count = si.entry.args[1];
        polls++;
        int allow = 1;
        if (count > MAX_BOOTSTRAP_POLL_FDS) allow = 0;
        unsigned long w1=0; int have1 = 0;
        double gw0 = now_s();
        for (unsigned long i=0; allow && i<count; i++) {
          unsigned long word;
          if (peek_word(t, p->addr + i*8, &word)) { allow = 0; peek_fail++; break; }
          int32_t fd = (int32_t)(word & 0xffffffffUL);
          if (i==1) { w1 = word; have1 = 1; }       /* record BEFORE deny-break (v5.6 counter fix) */
          if (fd > 2) { allow = 0; break; }
        }
        double gw1 = now_s();
        win_push((gw1-gw0)*1e9);
        p->allow = allow; p->have1 = have1; p->snap1 = have1 ? (int32_t)(w1 & 0xffffffffUL) : 0;
        if (have1 && p->snap1 > 2) snap_invalid++;
        if (!allow && !g_obs) {
          denied++;
          struct user_regs_struct r;
          if (ptrace(PTRACE_GETREGS, t, NULL, &r)==0) {
            r.orig_rax = -1;               /* classic emulate: kernel skips it */
            ptrace(PTRACE_SETREGS, t, NULL, &r);
          }
        }
        if (allow || g_obs) executed++;
      }
      ptrace(PTRACE_SYSCALL, t, NULL, NULL);
      continue;
    }

    if (si.op == PTRACE_SYSCALL_INFO_EXIT) {
      struct pend *p = pend_get(t, 0);
      if (p) {
        if (!p->allow && !g_obs) {
          struct user_regs_struct r;
          if (ptrace(PTRACE_GETREGS, t, NULL, &r)==0) {
            r.rax = (long long)-EBUSY;     /* emulated failure, tracee ignores */
            ptrace(PTRACE_SETREGS, t, NULL, &r);
          }
        } else if (p->have1) {
          /* v5.6 detector: classify the kernel-written revents of slot 1.
             fd 0 is an open, empty pipe with writer held open, so:
             POLLNVAL on slot 1 => kernel copied a value that is not open
             (the sentinel / a real fd only in T3's HUP case). */
          unsigned long wpost;
          if (peek_word(t, p->addr + 8, &wpost)==0) {
            int32_t fd_post = (int32_t)(wpost & 0xffffffffUL);  /* recorded, not used as evidence */
            (void)fd_post;
            uint16_t rev = (uint16_t)((wpost >> 48) & 0xffffUL);
            if (rev == 0) zero_total++;
            if (rev & POLLNVAL) { nval_total++; if (p->snap1 == 0) nval_on_snap0++; }
            if (rev & POLLHUP)  { hup_total++;  if (p->snap1 == 0) hup_on_snap0++; }
            if (rev & POLLIN)   in_total++;
            if (rev & POLLERR)  err_total++;
            if (rev != 0 && !(rev & (POLLNVAL|POLLHUP|POLLIN|POLLERR))) other_total++;
          }
        }
        p->used = 0;
      }
      ptrace(PTRACE_SYSCALL, t, NULL, NULL);
      continue;
    }

    ptrace(PTRACE_SYSCALL, t, NULL, NULL);  /* PTRACE_SYSCALL_INFO_NONE etc. */
  }

  kill(g_leader, SIGKILL);
  if (g_sibling_tid) { ptrace(PTRACE_KILL, g_sibling_tid, NULL, NULL); }

  /* fd 0 provenance of the tracee, read before it dies */
  char fd0link[128];
  ssize_t n0 = 0;
  n0 = readlink("/proc/self/fd/0", fd0link, sizeof fd0link - 1); /* supervisor's own fd 0 (launcher provenance) */
  if (n0 < 0) strcpy(fd0link, "CLOSED-OR-NONE"); else fd0link[n0] = 0;

  qsort(g_win.v, g_win.n, sizeof(double), cmpd);
  double med = g_win.n ? g_win.v[g_win.n/2] : 0;
  double mn  = g_win.n ? g_win.v[0] : 0;
  double mx  = g_win.n ? g_win.v[g_win.n-1] : 0;
  printf("RESULT mode=%s iterations=%ld observe_only=%d wall_s=%.1f\n",
         mode_name[g_mode], g_iters, g_obs, now_s()-t0);
  printf("RESULT polls=%ld gate_denied=%ld executed=%ld gate_snapshot_invalid=%ld peek_failures=%ld\n",
         polls, denied, executed, snap_invalid, peek_fail);
  printf("RESULT slot1_revents zero=%ld POLLIN=%ld POLLERR=%ld POLLHUP=%ld POLLNVAL=%ld other=%ld\n",
         zero_total, in_total, err_total, hup_total, nval_total, other_total);
  printf("RESULT hits snap0_nval=%ld snap0_hup=%ld (v5.6 criteria; fd_post no longer used as evidence)\n",
         nval_on_snap0, hup_on_snap0);
  printf("RESULT rates nval_of_executed=%.6f hup_of_executed=%.6f\n",
         executed? (double)nval_total/(double)executed : -1.0,
         executed? (double)hup_total/(double)executed : -1.0);
  printf("RESULT T2_window_ns gate_peek_n=%zu med=%.0f min=%.0f max=%.0f\n",
         g_win.n, med, mn, mx);
  printf("RESULT FD0_supervisor=%s\n", fd0link);

  int pass;
  switch (g_mode) {
  case M_CTL_A: pass = (nval_total==0 && hup_total==0 && in_total==0 && err_total==0 && other_total==0);
    printf("VERDICT CONTROL-A %s (fixed fd1=0: nonzero-revents events=%ld, expected 0)\n", pass?"PASS":"FAIL", in_total+err_total+other_total); break;
  case M_CTL_B: pass = (executed>0 && nval_total==executed);
    printf("VERDICT CONTROL-B %s (fixed sentinel: POLLNVAL/executed=%ld/%ld, expected 100%%)\n", pass?"PASS":"FAIL", nval_total, executed); break;
  case M_CTL_C: pass = (executed>0 && hup_total==executed);
    printf("VERDICT CONTROL-C %s (fixed fd3 fifo: POLLHUP/executed=%ld/%ld, expected 100%%)\n", pass?"PASS":"FAIL", hup_total, executed); break;
  case M_T3: pass = (hup_on_snap0>0);
    printf("VERDICT %s (harness)\n", pass ? "RACE-WON-ON-REAL-FD: snapshot validated 0, kernel polled real fd 3 (POLLHUP)" : "no divergence observed (harness)"); break;
  default: pass = (nval_on_snap0>0);
    printf("VERDICT %s (harness)\n", pass ? "RACE-WON: snapshot validated fd=0, kernel copied a not-open descriptor (POLLNVAL)" : "no divergence observed (harness)"); break;
  }
  return pass ? 0 : 1;
}
