# Reserves ready for owner to open (one click, pre-filled title+body)

Opening upstream is ALWAYS human. Each link opens GitHub's PR form pre-filled (English, GFM, AI footer). No manual copying.

## Zero-Conflict Matrix (phase 4)

**Rule:** at most ONE open PR per target file and per crate at a time. Open the recommended batch together; hold same-file/same-crate reserves until the prior PR merges.

### Recommended Conflict-Free Batch (open these together)

- `tests/devices-random-xorshift` (ginux-devices → `crates/ginux-devices/src/lib.rs`) — [Open](https://github.com/gmkurtzer/ginux/compare/main...hafid-logic:tests/devices-random-xorshift?quick_pull=1&title=tests%28devices%29%3A+pin+Random+read+xorshift64+sequence+and+state+advancement&body=%23%23%23+What%0APins+%60DeviceRegistry%3A%3Aread%60+Random+xorshift64+sequence%3A+first+four+bytes+match+the+reference+algorithm+from+default+seed%2C+and+successive+reads+advance+state.%0A%0A%23%23%23+Why+it+matters%0AThe+PRNG+drives+%2Fdev%2Frandom+output%3B+replacing+XOR+with+OR+or+flipping+shift+direction+produces+a+degenerate+or+predictable+stream.+Existing+tests+verify+read+succeeds+but+never+pin+output+values.%0A%0A%23%23%23+Mutation+evidence+%28fail-then-pass%29%0A%7C+Mutant+%7C+Existing+suite+%7C+New+test+%7C%0A%7C---%7C---%7C---%7C%0A%7C+%60%5E%3D+...+%3C%3C+13%60+-%3E+%60%5C%7C%3D+...+%3C%3C+13%60+%7C+PASS+%28survives%29+%7C+FAIL+%28killed%29+%7C%0A%7C+%60%3C%3C+13%60+-%3E+%60%3E%3E+13%60+%7C+PASS+%28survives%29+%7C+FAIL+%28killed%29+%7C%0A%0ABaseline%3A+PASS.+Reproduce%3A+%60cargo+test+-p+ginux-devices+--lib+random_read_pins%60.%0A%0ASpec-Ref%3A+xorshift64+PRNG+%28Marsaglia+2003%29%2C+%2Fdev%2Frandom+semantics%0A%0APrepared+with+AI+assistance%3B+reviewed+by+me.%0A)

### All reserves grouped by target file

#### `crates/ginux-devices/src/lib.rs`
- `tests/devices-random-xorshift` ✅ batch — [Open](https://github.com/gmkurtzer/ginux/compare/main...hafid-logic:tests/devices-random-xorshift?quick_pull=1&title=tests%28devices%29%3A+pin+Random+read+xorshift64+sequence+and+state+advancement&body=%23%23%23+What%0APins+%60DeviceRegistry%3A%3Aread%60+Random+xorshift64+sequence%3A+first+four+bytes+match+the+reference+algorithm+from+default+seed%2C+and+successive+reads+advance+state.%0A%0A%23%23%23+Why+it+matters%0AThe+PRNG+drives+%2Fdev%2Frandom+output%3B+replacing+XOR+with+OR+or+flipping+shift+direction+produces+a+degenerate+or+predictable+stream.+Existing+tests+verify+read+succeeds+but+never+pin+output+values.%0A%0A%23%23%23+Mutation+evidence+%28fail-then-pass%29%0A%7C+Mutant+%7C+Existing+suite+%7C+New+test+%7C%0A%7C---%7C---%7C---%7C%0A%7C+%60%5E%3D+...+%3C%3C+13%60+-%3E+%60%5C%7C%3D+...+%3C%3C+13%60+%7C+PASS+%28survives%29+%7C+FAIL+%28killed%29+%7C%0A%7C+%60%3C%3C+13%60+-%3E+%60%3E%3E+13%60+%7C+PASS+%28survives%29+%7C+FAIL+%28killed%29+%7C%0A%0ABaseline%3A+PASS.+Reproduce%3A+%60cargo+test+-p+ginux-devices+--lib+random_read_pins%60.%0A%0ASpec-Ref%3A+xorshift64+PRNG+%28Marsaglia+2003%29%2C+%2Fdev%2Frandom+semantics%0A%0APrepared+with+AI+assistance%3B+reviewed+by+me.%0A)
