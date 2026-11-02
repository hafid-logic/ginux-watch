# Environment lessons (from earlier manual runs; the CI workflow encodes them)

- QEMU: fetch the official release tarball (download.qemu.org). `git clone` of the tag fails on
  submodules from gitlab.com (HTTP 403 in the sandbox). Tarball hashes were stable between runs.
- QEMU 10.1.x needs libfdt (libfdt-dev); 10.0.13 does not for x86_64-softmmu.
- `./configure --target-list=x86_64-softmmu --disable-docs --disable-user --disable-gtk --disable-sdl --disable-werror --enable-slirp`
- Without root: libslirp's pkg-config module is named `slirp` (slirp.pc); a sysroot needs PKG_CONFIG
  paths fixed; `ninja` must be on PATH for QEMU's configure; meson can come from `pip install --target`.
- Ginux: `make doctor` looks for `qemu-system-x86_64` on PATH, so put a shim directory with a symlink
  first on PATH; `QEMU_SYSTEM_X86_64` also selects the binary.
- Ginux build needs Rust 1.99.0 (rust-toolchain.toml; add target x86_64-unknown-none) and clang with
  the x86_64-none-elf target (kernel/build.rs).
- OVMF: Debian paths /usr/share/OVMF/OVMF_CODE_4M.fd and OVMF_VARS_4M.fd; `QEMU_ACCEL=tcg` without KVM.
- `make reset-storage` before each `make test`. TCG `make test` takes ~76-99 s.
- QEMU can outlive a timed-out `make`: kill the whole process group.
- Normal-boot `serial_write` output may be dropped before the console is ready; failure markers come
  from `kernel_fail` (raw writes). Queue sizes are printed in the verification boot (`make test`).
- Sandbox disks were ~10 GiB: delete QEMU build trees after install. Platform sessions were recycled
  between messages; only the persistent work directory survived. That is why CI is primary.
- Sandbox recycle (2026-11-01 -> 2026-11-02) wiped work/bin/gh, the local ginux-watch git clone and session evidence; upload/ + download/ survived. Conclusion: durable state lives in the pushed GitHub repo; do auth->push->dispatch in one session whenever possible.
