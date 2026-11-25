# T: harvest mutation-scan artifacts from GitHub runners (IN FLIGHT)

Status: **HARVESTED 2026-11-25** — 176 survivors across 4 crates in state/discoveries.json; 3 new cards promoted (devices-views-read, process-pipespace, vfs-overlay-open).
Runs #1-#5 of `mutation-scan` on hafid-logic/ginux-watch: all `success`.
Crates dispatched: ginux-devices, ginux-fs-policy, ginux-vfs, ginux-process (+1).

Blocker solved: artifact download 302-redirects to blob storage; forwarding the
Authorization header breaks it. Capture `Location` from the 302, then GET it with
NO auth header (see playbook D10).

Next action: download each run's `missed.txt`, write per-crate gap counts into
`state/discoveries.json`, then promote the top security-relevant clusters into
task cards like the four kernel-views ones.
