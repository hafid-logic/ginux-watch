#!/usr/bin/env python3
"""GIT_SSH_COMMAND wrapper: paramiko-based ssh for github.com over port 443.
Usage: GIT_SSH_COMMAND='python3 scripts/git_ssh_paramiko.py' GIT_SSH_VARIANT=ssh git push/fetch
Handles git's invocation: [options] [-p port] [user@]host [command...]
Key path fixed to the gitignored deploy key; no secrets inside this file.

s50 transport fixes [MEASURED 2026-11-07, sandbox rebuild era]:
1. Normalize `git-upload-pack '/owner/repo.git'` -> no leading slash:
   GitHub SSH answers the no-slash form instantly and stalls on the slash form.
2. Forward git's stdin to the channel concurrently and read stdout/stderr
   without waiting for channel EOF: the previous `stdout.read()`-only loop
   deadlocked (git waits for the server, server waits for git's request)."""
import sys, os, re, threading, time

KEY = "/home/z/my-project/ginux-watch/work/.config/ssh/ginux_watch_deploy-20261107"
KNOWN_HOSTS = "/home/z/my-project/ginux-watch/work/.config/ssh/known_hosts_github"


def parse_args(argv):
    port = 22
    host = None
    cmd = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "-p" and i + 1 < len(argv):
            port = int(argv[i + 1]); i += 2; continue
        if a in ("-4", "-6", "-v", "-A", "-a"):
            i += 1; continue
        if a == "-o" and i + 1 < len(argv):
            i += 2; continue
        if host is None:
            host = a.split("@")[-1]; i += 1; continue
        cmd = argv[i:]; break
    return port, host, cmd


def normalize_cmd(cmd):
    """Strip the leading slash git's ssh:// form adds to the repo path."""
    for i, a in enumerate(cmd):
        m = re.match(r"^(git-(?:upload|receive)-pack|git-upload-archive)\s+'?/([^']+?)'?$", a)
        if m:
            cmd[i] = f"{m.group(1)} '{m.group(2)}'"
    return cmd


def main(argv):
    port, host, cmd = parse_args(argv)
    if host is None:
        print("git_ssh_paramiko: no host in args:", argv, file=sys.stderr)
        return 2
    cmd = normalize_cmd(cmd)
    import paramiko
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        cli.load_host_keys(KNOWN_HOSTS)
    except Exception:
        pass
    cli.connect(hostname=host, port=port, username="git",
                key_filename=KEY, look_for_keys=False, allow_agent=False,
                timeout=30, banner_timeout=30, auth_timeout=30)
    stdin_f, stdout_f, stderr_f = cli.exec_command(" ".join(cmd))
    chan = stdout_f.channel

    def pump_stdin():
        try:
            while True:
                data = sys.stdin.buffer.read(8192)
                if not data:
                    break
                chan.sendall(data)
        except Exception:
            pass
        try:
            chan.shutdown_write()
        except Exception:
            pass

    t = threading.Thread(target=pump_stdin, daemon=True)
    t.start()

    while True:
        got = False
        if chan.recv_ready():
            sys.stdout.buffer.write(chan.recv(65536)); sys.stdout.buffer.flush(); got = True
        if chan.recv_stderr_ready():
            sys.stderr.buffer.write(chan.recv_stderr(65536)); sys.stderr.buffer.flush(); got = True
        if chan.exit_status_ready() and not chan.recv_ready() and not chan.recv_stderr_ready():
            break
        if not got:
            time.sleep(0.02)
    rc = chan.recv_exit_status()
    sys.stdout.buffer.flush(); sys.stderr.buffer.flush()
    cli.close()
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
