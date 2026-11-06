# Evidence memo 1/3 — `scan_layer` :253/:263/:264 (request from #222 owner reply)

**Status: prepared locally, NOT published.** Owner request (issue #222, reply
2026-11-06T05:29:33Z): "the unreviewed `scan_layer` paths ... remain open".

## Question

Are the `scan_layer` sites flagged in #222 as "similar patterns and I did not
review it" (crates/ginux-vfs-index/src/main.rs :253, :263, :264) reproducible
defects on current main?

## Answer

**No defect found within the tested matrix** [MEASURED on upstream main head
`3f2fe7df`; the `ginux-vfs-index` tree is byte-identical to `64a3e3f7` where the
matrix originally ran — verified by `diff -rq` of both extractions]. This is a
bounded negative result, not a proof of absence: the claim is exactly "nothing
found inside the matrix below", with its limits stated in the last section.

## The three sites and what actually bounds them

| Site | Expression | Binding bound | Tag |
|---|---|---|---|
| :253 | `offset + 512 <= source_len` | `source_len = source.metadata()?.len()` (:114) is a real file length; an overflow here needs a single file of ≥ 2^64−511 bytes | MEASURED (bound) / INFERRED (reachability) |
| :263 | `data_offset = offset + 512` | loop invariant `offset ≤ source_len−512` at entry (gate :253 passed) | MEASURED (invariant) |
| :264 | `size.checked_add(511).ok_or(…)? / 512 * 512` | `checked_add` is explicit; `parse_octal` (:639) reads the [124..136] field = 11 octal digits max ⇒ `size ≤ 0o77777777777 = 8,589,934,591` (~8.59 GB); `u64::MAX` is not expressible; GNU base-256 (`0x80` tag) fails `from_utf8` with a clean error | MEASURED |

Side result [MEASURED]: `record_len = end − record_offset` (:326) never
underflows (`record_offset ≤ offset < end`).

## Adversarial matrix actually executed

Built at `64a3e3f7` (vfs-index unchanged since), release binary sha256
`07b7f0ef…`, plus a debug binary (overflow-checks on by construction):

| Case | Input | Result | Tag |
|---|---|---|---|
| B2 | max expressible size `0o77777777777` (~8.59 GB) on a 1.5 KB file | clean error `truncated OCI layer entry` (:269), no panic, no silent wrap | MEASURED |
| C2 | GNU base-256 size field = u64::MAX | clean `Utf8Error` from `parse_octal` (:649) | MEASURED |
| E2 | declared size 4096, file truncated after header | clean `truncated OCI layer entry` (:269) | MEASURED |
| sanity | standard tar via python tarfile | scan passes; later fails at Rocky-verify as designed | MEASURED |
| :253 bound | `truncate -s 18446744073709551104` | filesystem refuses: `EFBIG: Value too large for defined data type` | MEASURED (environment bound) |

## Limits of this memo (stated explicitly)

- The octal field physically caps expressible sizes at ~8.59 GB; sizes beyond
  that are outside the format's grammar, and the base-256 escape is rejected at
  parse. This is a format-level bound, not a formal proof over all inputs.
- The `:253` case was bounded by the test filesystem (EFBIG), not by the code.
- The matrix covers crafted single-record headers plus a standard tar; it is
  not a fuzzing campaign over the full header space.
- "No defect found within the matrix" is the entire claim; if the owner wants
  a different or wider matrix, the harness can be extended.

**Conclusion for #222:** the "unreviewed `scan_layer` paths" clause can be
closed as *reviewed, bounded, and clean within the stated matrix* — zero
reproducible defects, therefore zero PR candidates from these sites. Posted
nowhere; publication stays Abdelhafid's manual call.
