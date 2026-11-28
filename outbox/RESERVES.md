# Reserves ready for owner to open (one click, pre-filled title+body)

Opening upstream is ALWAYS human. Each link opens GitHub's PR form pre-filled (English, GFM, AI footer). No manual copying.

## Zero-Conflict Matrix (phase 4)

**Rule:** at most ONE open PR per target file and per crate at a time. Open the recommended batch together; hold same-file/same-crate reserves until the prior PR merges.

### Recommended Conflict-Free Batch (open these together)

- `tests/vfs-copy-overlay-size-boundary` (ginux-vfs → `crates/ginux-vfs/src/lib.rs`) — [Open](https://github.com/gmkurtzer/ginux/compare/main...hafid-logic:tests/vfs-copy-overlay-size-boundary?quick_pull=1&title=tests%28vfs%29%3A+pin+copy_to_overlay+exact+FILE_SIZE+acceptance&body=%23%23%23+What%0APins+%60copy_to_overlay%60+size+gate%3A+exact+FILE_SIZE+fit+copies+successfully%2C+and+smaller+base+files+also+copy+without+rejection.%0A%0A%23%23%23+Why+it+matters%0ARelaxing+%60%3E%60+to+%60%3E%3D%60+rejects+valid+exact-fit+images%3B+relaxing+to+%60%3D%3D%60+admits+only+exact+sizes+and+rejects+all+smaller+files.+Existing+tests+never+exercise+the+overlay+copy+size+boundary.%0A%0A%23%23%23+Mutation+evidence+%28fail-then-pass%29%0A%7C+Mutant+%7C+Existing+suite+%7C+New+test+%7C%0A%7C---%7C---%7C---%7C%0A%7C+%60size+%3E+FILE_SIZE%60+-%3E+%60size+%3E%3D+FILE_SIZE%60+%7C+PASS+%28survives%29+%7C+FAIL+%28killed%29+%7C%0A%7C+%60size+%3E+FILE_SIZE%60+-%3E+%60size+%3D%3D+FILE_SIZE%60+%7C+PASS+%28survives%29+%7C+FAIL+%28killed%29+%7C%0A%0ABaseline%3A+PASS.+Reproduce%3A+%60cargo+test+-p+ginux-vfs+--lib+copy_to_overlay_accepts%60.%0A%0ASpec-Ref%3A+overlay+copy-on-write+size+invariant+%28VFS+internal+contract%29%0A%0APrepared+with+AI+assistance%3B+reviewed+by+me.%0A)

### All reserves grouped by target file

#### `crates/ginux-vfs/src/lib.rs`
- `tests/vfs-copy-overlay-size-boundary` ✅ batch — [Open](https://github.com/gmkurtzer/ginux/compare/main...hafid-logic:tests/vfs-copy-overlay-size-boundary?quick_pull=1&title=tests%28vfs%29%3A+pin+copy_to_overlay+exact+FILE_SIZE+acceptance&body=%23%23%23+What%0APins+%60copy_to_overlay%60+size+gate%3A+exact+FILE_SIZE+fit+copies+successfully%2C+and+smaller+base+files+also+copy+without+rejection.%0A%0A%23%23%23+Why+it+matters%0ARelaxing+%60%3E%60+to+%60%3E%3D%60+rejects+valid+exact-fit+images%3B+relaxing+to+%60%3D%3D%60+admits+only+exact+sizes+and+rejects+all+smaller+files.+Existing+tests+never+exercise+the+overlay+copy+size+boundary.%0A%0A%23%23%23+Mutation+evidence+%28fail-then-pass%29%0A%7C+Mutant+%7C+Existing+suite+%7C+New+test+%7C%0A%7C---%7C---%7C---%7C%0A%7C+%60size+%3E+FILE_SIZE%60+-%3E+%60size+%3E%3D+FILE_SIZE%60+%7C+PASS+%28survives%29+%7C+FAIL+%28killed%29+%7C%0A%7C+%60size+%3E+FILE_SIZE%60+-%3E+%60size+%3D%3D+FILE_SIZE%60+%7C+PASS+%28survives%29+%7C+FAIL+%28killed%29+%7C%0A%0ABaseline%3A+PASS.+Reproduce%3A+%60cargo+test+-p+ginux-vfs+--lib+copy_to_overlay_accepts%60.%0A%0ASpec-Ref%3A+overlay+copy-on-write+size+invariant+%28VFS+internal+contract%29%0A%0APrepared+with+AI+assistance%3B+reviewed+by+me.%0A)
