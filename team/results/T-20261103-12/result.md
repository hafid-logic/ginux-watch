# T-20261103-12 — Critic review of PR draft 2026-11-03-v28-fuzz-pr.md [DONE]

Reviewed draft: `drafts/2026-11-03-v28-fuzz-pr.md` (independent critic; not the author).
Verification transcript (commands + outputs): `evidence/verify-draft-facts.txt`.

## 1. Number trace

- 124 files / +849 lines [MEASURED]: `git diff --stat c86945b1..HEAD | tail -2` → "124 files
  changed, 849 insertions(+)"; head = `eccb0de7` (evidence/verify-draft-facts.txt).
- Seeds 53/34/26, total 113 [MEASURED]: per-dir `git ls-tree -r` counts (evidence/);
  matches T-11 §3b seed loads.
- 83,823 bytes [MEASURED]: `git ls-tree -rl … | awk '{s+=$4}'`. Draft "84 KB total":
  83.8 kB decimal → 84 KB. Not misleading (0.2% off; 81.9 under binary KiB reading).
  MINOR: prefer "83.8 KB".
- libfuzzer-sys `"=0.4.13"` [MEASURED]: fork2 `fuzz/Cargo.toml:22` exact.
- **Cargo.lock "33 packages" — DOES NOT TRACE [MEASURED]**: fork2 `fuzz/Cargo.lock` has
  **34** `[[package]]` sections / 34 `name = ` lines (34 unique names, incl. `ginux-fuzz`
  itself). A reviewer running `rg -c 'name ='` gets 34, contradicting the draft. FIX.
- Execs 24.9M/101.6M/46.3M = 172.8M [MEASURED]: T-11 result.md §3b (24,918,248 /
  101,564,909 / 46,269,525 / 172,752,682); raw `DONE 24918248`, `#101564909 DONE`,
  `#46269525 DONE` in T-11 evidence/round-*.tail.log.
- Coverage regions 92.95/97.50/99.43%, functions 97.94/100/100% [MEASURED]: raw TOTAL rows
  in team/results/T-20261103-11/evidence/coverage-*_surfaces.log; draft correctly uses real
  functions% (T-11 warns the summary "functions" column is branches).
- 0/0/0/0 checks, zero crashes/sanitizer reports, QEMU 10.1.2, run 41614443506, sha
  eccb0de7 [MEASURED]: T-11 result.md (run URL matches, 7/7 SUCCESS).
- "no root file modified" [MEASURED]: `git diff --name-only c86945b1..HEAD | grep -v '^fuzz/'`
  → empty. "root 1.99.0/UEFI toolchain untouched" [MEASURED]: only `fuzz/rust-toolchain.toml`
  changed; root rust-toolchain.toml at HEAD still 1.99.0 / x86_64-unknown-uefi.
- nightly-2026-11-02 + rust-src + llvm-tools-preview [MEASURED]: fork2
  fuzz/rust-toolchain.toml. Path deps + `default-features = false, features = ["sha256"]`
  on ginux-oci [MEASURED]: fork2 fuzz/Cargo.toml:16-18.
- c86945b1 [MEASURED]: ancestor of HEAD ("Merge pull request #56…", 2026-11-03).

All numbers trace EXCEPT "33 packages" (measured 34).

## 2. Rules compliance

- **Word count 278 (wc -w) — OVER the 250 limit. FIX REQUIRED** (evidence/).
- English; "Refs #58" (L1); main @ c86945b1 (L1); run summary + URL (L10); exclusions with
  reason (L12); new-dependency statement, 0.4.13 pinned, "No other manifest is touched"
  (L14); "Draft; happy to split per target" (L16); AI disclosure (L16); non-security
  disclaimer (L16) — all present [OBSERVED].
- No promises (both "happy to…" conditional) [OBSERVED]. No unsourced numbers beyond the
  33-packages defect [OBSERVED].

## 3. Tone vs maintainer #58 conditions

- 3 targets with committed seeds AND dictionaries [MEASURED]: fuzz/{oci,protocol,volume}.dict
  + corpus-seed* in fork2; workflow maps dict+seeds per target.
- README exact commands + bounded smoke [MEASURED]: fork2 fuzz/README.md "Smoke run
  (bounded, about 60 s per target)" matches draft "~60 s per target".
- No crash artifacts / oversized corpus [MEASURED]: fuzz/ has only corpus-seed* (83,823 B);
  no corpus/ or artifact dirs.
- Pinned commit + run summary [MEASURED]: present.
- Run URL on hafid-logic/ginux-watch — the team's public infra repo (the only writable
  target per protocol); acceptable, not upstream. OK [INFERRED].

## 4. Secrets / placeholders

- `ghp_|gho_|github_pat_|TODO|FIXME|XXX|TBD|placeholder|<your|<token` case-insensitive scan
  → no matches [MEASURED] (evidence/). No emails; only `@hafid-logic`, `#58` [MEASURED].
- "coverage (seeds + evolved corpus)" [MEASURED]: matches workflow step "Coverage (lcov
  over committed seeds + evolved corpus)" (ginux-watch .github/workflows/
  fuzz-branch-verify.yml:210; corpus = seeds dir + evolved corpus).

## 5. Minimal fixes

1. L5 "(33 packages)" → "(34 locked packages)" — measured 34 `[[package]]` sections (33
   only if the `ginux-fuzz` crate itself is excluded); the text must survive
   `rg -c 'name ='` = 34.
2. Cut ≥28 words to reach ≤250. Safe trims: L5 surface list → "tar/PAX, rootfs traversal,
   registry surfaces" (−8); L7 protocol parenthetical → "ARP, IPv4/ICMP parse, neighbor
   state machine" (−4); L12 → "No CI workflow added — upstream keeps its own minimal
   check.yml; README smoke reproduces anywhere" (−7); L5 deps → "in-repo path deps:
   ginux-oci (default features off + sha256), ginux-protocol-state, ginux-volume-format"
   (−4); L10 drop "(QEMU 10.1.2)" (−2); "84 KB" → "83.8 KB" (precision).
3. Keep everything else verbatim — required elements all present and correct.

FINAL VERDICT: **REVISE** — apply fixes 1–2 (word count 278→≤250; "33 packages"→34).
After those mechanical edits the draft is approvable; no other defects found.
