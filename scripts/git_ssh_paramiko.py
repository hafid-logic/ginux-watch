#!/usr/bin/env python3
"""GIT_SSH_COMMAND wrapper: paramiko-based ssh for github.com over port 443.
Usage: GIT_SSH_COMMAND='python3 scripts/git_ssh_paramiko.py' GIT_SSH_VARIANT=ssh git push/fetch
Handles git's invocation: [options] [-p port] [user@]host [command...]
Key path fixed to the gitignored deploy key; no secrets inside this file."""
import sys, os

KEY = os.path.expanduser(
    "~/.config-fallback")  # placeholder, resolved below
KEY = "/home/z/my-project/ginux-watch/work/.config/ssh/ginux_watch_deploy-20261107"
KNOWN_HOSTS = "/home/z/my-project/ginux-watch/work/.config/ssh/known_hosts_github"

def main(argv):
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
    if host is None:
        print("git_ssh_paramiko: no host in args:", argv, file=sys.stderr)
        return 2
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
    stdin, stdout, stderr = cli.exec_command(" ".join(cmd), timeout=120)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    rc = stdout.channel.recv_exit_status()
    sys.stdout.write(out)
    sys.stderr.write(err)
    cli.close()
    return rc

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
