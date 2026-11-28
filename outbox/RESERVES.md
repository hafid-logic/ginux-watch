# Reserves ready for owner to open (one click, pre-filled title+body)

Opening upstream is ALWAYS human. Each link opens GitHub's PR form pre-filled (English, GFM, AI footer). No manual copying.

## Zero-Conflict Matrix (phase 4)

**Rule:** at most ONE open PR per target file and per crate at a time. Open the recommended batch together; hold same-file/same-crate reserves until the prior PR merges.

### Recommended Conflict-Free Batch (open these together)

- `tests/vfs-decode-boundary-exact` (ginux-vfs → `crates/ginux-vfs/src/lib.rs`) — [Open](https://github.com/gmkurtzer/ginux/compare/main...hafid-logic:tests/vfs-decode-boundary-exact?quick_pull=1&title=tests%28vfs%29%3A+pin+decode_record+exact+path%2Flink+bounds+and+overflow+rejection&body=%23%23%23+What%0APins+%60decode_record%60+length+gates%3A+exact+MAX_PATH%2FMAX_LINK+fit+decodes%2C+one-past-MAX_LINK+and+zero-length+path+are+rejected+at+index+load.%0A%0A%23%23%23+Why+it+matters%0ADecode+gates+guard+every+record+read%3B+relaxing+%60%3E%60+to+%60%3E%3D%60+rejects+valid+exact-fit+images%2C+while+%60%3D%3D%60+admits+oversized+links+that+later+slice+out+of+bounds.+Existing+tests+pin+encode-side+and+path-overflow+only%2C+not+decode-side+exact+fit+or+link+overflow.%0A%0A%23%23%23+Mutation+evidence+%28fail-then-pass%29%0A%7C+Mutant+%7C+Existing+suite+%7C+New+test+%7C%0A%7C---%7C---%7C---%7C%0A%7C+%60link_len+%3E+MAX_LINK%60+-%3E+%60%3E%3D%60+%7C+PASS+%28survives%29+%7C+FAIL+%28killed%29+%7C%0A%7C+%60path_len+%3E+MAX_PATH%60+-%3E+%60%3D%3D%60+%7C+PASS+%28survives%29+%7C+FAIL+%28killed%29+%7C%0A%0ABaseline%3A+PASS.+Reproduce%3A+%60cargo+test+-p+ginux-vfs+--lib+decode_record_accepts_exact%60.%0A%0APrepared+with+AI+assistance%3B+reviewed+by+me.%0A)

### All reserves grouped by target file

#### `crates/ginux-vfs/src/lib.rs`
- `tests/vfs-decode-boundary-exact` ✅ batch — [Open](https://github.com/gmkurtzer/ginux/compare/main...hafid-logic:tests/vfs-decode-boundary-exact?quick_pull=1&title=tests%28vfs%29%3A+pin+decode_record+exact+path%2Flink+bounds+and+overflow+rejection&body=%23%23%23+What%0APins+%60decode_record%60+length+gates%3A+exact+MAX_PATH%2FMAX_LINK+fit+decodes%2C+one-past-MAX_LINK+and+zero-length+path+are+rejected+at+index+load.%0A%0A%23%23%23+Why+it+matters%0ADecode+gates+guard+every+record+read%3B+relaxing+%60%3E%60+to+%60%3E%3D%60+rejects+valid+exact-fit+images%2C+while+%60%3D%3D%60+admits+oversized+links+that+later+slice+out+of+bounds.+Existing+tests+pin+encode-side+and+path-overflow+only%2C+not+decode-side+exact+fit+or+link+overflow.%0A%0A%23%23%23+Mutation+evidence+%28fail-then-pass%29%0A%7C+Mutant+%7C+Existing+suite+%7C+New+test+%7C%0A%7C---%7C---%7C---%7C%0A%7C+%60link_len+%3E+MAX_LINK%60+-%3E+%60%3E%3D%60+%7C+PASS+%28survives%29+%7C+FAIL+%28killed%29+%7C%0A%7C+%60path_len+%3E+MAX_PATH%60+-%3E+%60%3D%3D%60+%7C+PASS+%28survives%29+%7C+FAIL+%28killed%29+%7C%0A%0ABaseline%3A+PASS.+Reproduce%3A+%60cargo+test+-p+ginux-vfs+--lib+decode_record_accepts_exact%60.%0A%0APrepared+with+AI+assistance%3B+reviewed+by+me.%0A)
