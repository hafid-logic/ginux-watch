#!/usr/bin/env bash
# style-notes.sh — generate STYLE-NOTES.md: a measured profile of upstream
# (gmkurtzer/ginux) commit / PR / review style (directive v3.3 §2, worker W1).
#
# CLI:
#   style-notes.sh --repo DIR --pulls FILE --reviews FILE --comments FILE \
#                  --since-days 30 --out FILE
#
# Inputs:
#   --repo      a git clone of gmkurtzer/ginux (full git log; NOT fetched here)
#   --pulls     JSON array of PR metadata (number,state,draft,user,created_at,
#               closed_at,merged_at,head,additions,deletions,changed_files,title)
#               — accepts both the flattened dump schema (user/head as strings)
#               and raw API schema (user.login / head.ref objects)
#   --reviews   JSON array (pr,id,user,state,submitted_at,body)
#   --comments  JSON array (pr,id,user,created_at,body)
#
# Output: markdown report with Arabic headers + English technical terms.
# Every measured number is tagged [MEASURED] with its source and as-of date.
# Robustness: any section with no data emits "n/a" instead of failing.
#
# Constraints honored: no network access, no cargo/rust, no secrets.
set -euo pipefail

USAGE="usage: $0 --repo DIR --pulls FILE --reviews FILE --comments FILE --since-days N --out FILE"

REPO=""
PULLS=""
REVIEWS=""
COMMENTS=""
SINCE_DAYS="30"
OUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)        REPO="$2"; shift 2 ;;
    --pulls)       PULLS="$2"; shift 2 ;;
    --reviews)     REVIEWS="$2"; shift 2 ;;
    --comments)    COMMENTS="$2"; shift 2 ;;
    --since-days)  SINCE_DAYS="$2"; shift 2 ;;
    --out)         OUT="$2"; shift 2 ;;
    -h|--help)     echo "$USAGE"; exit 0 ;;
    *)             echo "unknown arg: $1" >&2; echo "$USAGE" >&2; exit 2 ;;
  esac
done

[[ -n "$REPO" && -n "$OUT" ]] || { echo "$USAGE" >&2; exit 2; }
[[ "$SINCE_DAYS" =~ ^[0-9]+$ ]] || { echo "--since-days must be a non-negative integer" >&2; exit 2; }
[[ -d "$REPO" ]] || { echo "--repo is not a directory: $REPO" >&2; exit 2; }
for f in "$PULLS" "$REVIEWS" "$COMMENTS"; do
  if [[ -n "$f" && ! -f "$f" ]]; then
    echo "warn: input file missing (section will be n/a): $f" >&2
  fi
done
command -v python3 >/dev/null || { echo "python3 required" >&2; exit 3; }
command -v git     >/dev/null || { echo "git required" >&2; exit 3; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# ---------------------------------------------------------------- git capture
GIT_OK=1
if ! git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "warn: $REPO is not a git repository (git sections will be n/a)" >&2
  GIT_OK=0
fi

if [[ "$GIT_OK" -eq 1 ]]; then
  # Non-merge commits with per-file numstat (\x01 starts each commit record;
  # binary files appear as "-<TAB>-<TAB>path" and are skipped downstream).
  git -C "$REPO" log --no-merges --pretty=format:$'\x01%H %cI' --numstat \
    > "$TMP/numstat.txt"
  # Non-merge commit messages: sha \x02 subject \x02 body
  git -C "$REPO" log --no-merges --pretty=format:$'\x01%H\x02%s\x02%b' \
    > "$TMP/messages.txt"
  git -C "$REPO" rev-parse HEAD > "$TMP/head.txt"
else
  : > "$TMP/numstat.txt"
  : > "$TMP/messages.txt"
  : > "$TMP/head.txt"
fi

# --------------------------------------------------------------- json preflight
preflight() { # $1 = path ; prints record count; 0 if unreadable
  local f="$1"
  [[ -n "$f" && -f "$f" ]] || { echo 0; return; }
  if command -v jq >/dev/null && jq -e 'type == "array"' "$f" >/dev/null 2>&1; then
    jq 'length' "$f"
  else
    echo "warn: not a valid JSON array (section will be n/a): $f" >&2
    echo 0
  fi
}
echo "input records: pulls=$(preflight "$PULLS") reviews=$(preflight "$REVIEWS") comments=$(preflight "$COMMENTS")" >&2

OUT_DIR="$(dirname "$OUT")"
mkdir -p "$OUT_DIR"

# ------------------------------------------------------------------- analysis
python3 - "$REPO" "$PULLS" "$REVIEWS" "$COMMENTS" "$SINCE_DAYS" "$OUT" \
  "$TMP/numstat.txt" "$TMP/messages.txt" "$TMP/head.txt" <<'PYEOF'
#!/usr/bin/env python3
"""Embedded analyzer for style-notes.sh (python stdlib only)."""
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

REPO, PULLS, REVIEWS, COMMENTS, SINCE_DAYS, OUT = sys.argv[1:7]
NUMSTAT_F, MESSAGES_F, HEAD_F = sys.argv[7:10]
SINCE_DAYS = int(SINCE_DAYS)
NOW = datetime.now(timezone.utc)
GEN = NOW.strftime("%Y-%m-%dT%H:%M:%SZ")
MAINTAINER = "gmkurtzer"

warnings = []


def warn(msg):
    warnings.append(msg)


def read_json_array(path):
    """Read a JSON array file; any failure -> [] + warning (never raises)."""
    if not path:
        return []
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except OSError as exc:
        warn(f"unreadable input {path}: {exc}")
        return []
    except json.JSONDecodeError as exc:
        warn(f"invalid JSON in {path}: {exc}")
        return []
    if not isinstance(data, list):
        warn(f"not a JSON array: {path}")
        return []
    return data


def login(entry):
    """user field: flattened dump has a string; raw API has {login: ...}."""
    u = entry.get("user")
    if isinstance(u, dict):
        return u.get("login") or ""
    return u if isinstance(u, str) else ""


def head_ref(entry):
    h = entry.get("head")
    if isinstance(h, dict):
        return h.get("ref") or ""
    return h if isinstance(h, str) else ""


def parse_iso(ts):
    if not ts or not isinstance(ts, str):
        return None
    t = ts.strip()
    try:
        return datetime.fromisoformat(t.replace("Z", "+00:00"))
    except ValueError:
        return None


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def median(xs):
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    m = n // 2
    if n % 2:
        return float(s[m])
    return (s[m - 1] + s[m]) / 2.0


def fmt(x, nd=1):
    if x is None:
        return "n/a"
    r = round(x, nd)
    if nd == 0:
        return str(int(r))
    return f"{r:.{nd}f}".rstrip("0").rstrip(".") if r == r else "n/a"


def md_cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")[:200]


# ------------------------------------------------------------------ git parse
def parse_numstat(text):
    """Return list of commits: {sha, date, adds, dels, files:[(name,a,d)]}."""
    commits = []
    cur = None
    for line in text.splitlines():
        if line.startswith("\x01"):
            parts = line[1:].split(" ", 1)
            cur = {"sha": parts[0], "date": parse_iso(parts[1]) if len(parts) > 1 else None,
                   "adds": 0, "dels": 0, "files": []}
            commits.append(cur)
            continue
        if cur is None or not line.strip():
            continue
        f = line.split("\t")
        if len(f) != 3:
            continue
        if f[0] == "-" or f[1] == "-":   # binary file -> skipped [MEASURED note]
            continue
        try:
            a, d = int(f[0]), int(f[1])
        except ValueError:
            continue
        cur["adds"] += a
        cur["dels"] += d
        cur["files"].append((f[2], a, d))
    return commits


def parse_messages(text):
    """Return {sha: {subject, body}}."""
    out = {}
    for rec in text.split("\x01"):
        if not rec.strip():
            continue
        parts = rec.split("\x02", 2)
        if len(parts) < 3:
            continue
        sha, subj, body = parts[0].strip(), parts[1], parts[2]
        out[sha] = {"subject": subj.strip(), "body": body}
    return out


def read_small(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


numstat_txt = read_small(NUMSTAT_F)
messages_txt = read_small(MESSAGES_F)
head_sha = read_small(HEAD_F)

commits = parse_numstat(numstat_txt)
msgs = parse_messages(messages_txt)
for c in commits:
    c.update(msgs.get(c["sha"], {"subject": "", "body": ""}))

# git as-of = newest commit date among analyzed non-merge commits
git_dates = [c["date"] for c in commits if c["date"]]
GIT_ASOF = max(git_dates).astimezone(timezone.utc).strftime("%Y-%m-%d") if git_dates else None
cutoff = NOW - timedelta(days=SINCE_DAYS)
recent = [c for c in commits if c["date"] and c["date"] >= cutoff]
SRC_GIT_ALL = f"`git log --numstat` (all history) — [MEASURED], as-of {GIT_ASOF or 'n/a'}"
SRC_GIT_30 = f"`git log --numstat` (آخر {SINCE_DAYS} يومًا) — [MEASURED], as-of {GIT_ASOF or 'n/a'}"

# pulls / reviews / comments
pulls = read_json_array(PULLS)
reviews = read_json_array(REVIEWS)
comments = read_json_array(COMMENTS)
SRC_PULLS = f"`{PULLS.split('/')[-1] if PULLS else '—'}` — [MEASURED], as-of {GEN}"
SRC_REVIEWS = f"`{REVIEWS.split('/')[-1] if REVIEWS else '—'}` — [MEASURED], as-of {GEN}"
SRC_COMMENTS = f"`{COMMENTS.split('/')[-1] if COMMENTS else '—'}` — [MEASURED], as-of {GEN}"

lines = []
add = lines.append

add("# STYLE-NOTES — بروفايل أسلوب المستودع الأصلي (upstream) `gmkurtzer/ginux`")
add("")
add(f"*توليد آلي: {GEN} UTC — كل الأرقام مقيسة من البيانات الخام وموسومة `[MEASURED]` مع المصدر وتاريخ as-of. "
    "البنية: عناوين عربية + مصطلحات تقنية إنجليزية.*")
add("")
add(f"*نافذة \"آخر {SINCE_DAYS} يومًا\" للبيانات من git: من "
    f"{cutoff.strftime('%Y-%m-%d')} حتى {GIT_ASOF or 'n/a'} (commit date، UTC).*")
add("")

# ----------------------------------------------------------- 1. commit sizes
add("## 1. حجم الـ commits (commit size)")
add("")
if commits:
    a_all = [c["adds"] for c in commits]
    d_all = [c["dels"] for c in commits]
    t_all = [c["adds"] + c["dels"] for c in commits]
    first_date = min(git_dates).astimezone(timezone.utc).strftime("%Y-%m-%d") if git_dates else None
    add(f"عدد الـ non-merge commits (كل التاريخ): **{len(commits)}** "
        f"— {SRC_GIT_ALL}. الملفات الثنائية (binary) مستثناة من الأرقام."
        + (f" أول commit: {first_date}." if first_date else ""))
    add("")
    add("| المقياس | المتوسط mean | الوسيط median | المصدر |")
    add("|---|---|---|---|")
    add(f"| additions (سطور مضافة) | {fmt(mean(a_all))} | {fmt(median(a_all))} | {SRC_GIT_ALL} |")
    add(f"| deletions (سطور محذوفة) | {fmt(mean(d_all))} | {fmt(median(d_all))} | {SRC_GIT_ALL} |")
    add(f"| additions+deletions (الحجم الكلي) | {fmt(mean(t_all))} | {fmt(median(t_all))} | {SRC_GIT_ALL} |")
    add("")
    add(f"ملاحظة توزيع: المتوسط mean أعلى بكثير من الوسيط median (ذيل ثقيل heavy tail بسبب commits ضخمة)؛ "
        "الوسيط أصدق وصفًا للـ commit النموذجي."
        if (mean(t_all) or 0) > 3 * (median(t_all) or 0) else
        "ملاحظة توزيع: المتوسط والوسيط متقاربان نسبيًا.")
    add("")
    if len(recent) == len(commits):
        add(f"ملاحظة: النافذة (آخر {SINCE_DAYS} يومًا) تغطي كل تاريخ المستودع — لذا تتطابق أرقام النافذتين. [MEASURED]")
        add("")
    if recent:
        a_r = [c["adds"] for c in recent]
        d_r = [c["dels"] for c in recent]
        t_r = [c["adds"] + c["dels"] for c in recent]
        add(f"عدد الـ non-merge commits (آخر {SINCE_DAYS} يومًا): **{len(recent)}** — {SRC_GIT_30}")
        add("")
        add("| المقياس | المتوسط mean | الوسيط median | المصدر |")
        add("|---|---|---|---|")
        add(f"| additions | {fmt(mean(a_r))} | {fmt(median(a_r))} | {SRC_GIT_30} |")
        add(f"| deletions | {fmt(mean(d_r))} | {fmt(median(d_r))} | {SRC_GIT_30} |")
        add(f"| additions+deletions | {fmt(mean(t_r))} | {fmt(median(t_r))} | {SRC_GIT_30} |")
    else:
        add(f"آخر {SINCE_DAYS} يومًا: **n/a** (لا توجد commits في النافذة) — {SRC_GIT_30}")
else:
    add("n/a (لا توجد بيانات git صالحة)")
add("")

# -------------------------------------------------------- 2. subject format
add("## 2. صيغة الموضوع (subject)")
add("")
if commits:
    subj_all = [c["subject"] for c in commits if c["subject"]]
    subj_rec = [c["subject"] for c in recent if c["subject"]]
    chars = [len(s) for s in subj_all]
    words = [len(s.split()) for s in subj_all]
    upper = sum(1 for s in subj_all if s[:1].isupper())
    n = len(subj_all)
    conv_re = re.compile(r"^[A-Za-z][\w./-]*(\([^)]*\))?:")
    VERBS = {"add", "fix", "use", "remove", "update", "make", "allow", "prevent",
             "handle", "move", "rename", "drop", "split", "set", "treat", "clamp",
             "release", "require", "guard", "avoid", "normalize", "document",
             "enable", "disable", "support", "introduce", "switch", "reject",
             "skip", "ignore", "limit", "expose", "mark", "validate", "harden",
             "migrate", "unify", "simplify", "record", "define", "charge", "cover"}
    conv = sum(1 for s in subj_all
               if conv_re.match(s) or (s.split() and s.split()[0].strip(":").lower() in VERBS))
    first_words = {}
    for s in subj_all:
        w = s.split()[0] if s.split() else "(empty)"
        first_words[w] = first_words.get(w, 0) + 1
    top8 = sorted(first_words.items(), key=lambda kv: (-kv[1], kv[0]))[:8]

    add(f"عينة القياس: **{n}** subject — {SRC_GIT_ALL}")
    add("")
    add("| المقياس | all-history | آخر " + str(SINCE_DAYS) + " يومًا | المصدر |")
    add("|---|---|---|---|")
    c_r = [len(s) for s in subj_rec]
    w_r = [len(s.split()) for s in subj_rec]
    add(f"| طول بالأحرف mean / median | {fmt(mean(chars))} / {fmt(median(chars))} | "
        f"{fmt(mean(c_r)) if subj_rec else 'n/a'} / {fmt(median(c_r)) if subj_rec else 'n/a'} | {SRC_GIT_ALL} |")
    add(f"| عدد الكلمات mean / median | {fmt(mean(words))} / {fmt(median(words))} | "
        f"{fmt(mean(w_r)) if subj_rec else 'n/a'} / {fmt(median(w_r)) if subj_rec else 'n/a'} | {SRC_GIT_ALL} |")
    add(f"| يبدأ بحرف كبير (uppercase) | {fmt(100.0 * upper / n)}% | "
        + (f"{fmt(100.0 * sum(1 for s in subj_rec if s[:1].isupper()) / len(subj_rec))}%" if subj_rec else "n/a")
        + f" | {SRC_GIT_ALL} |")
    add(f"| بادئة تقليدية (conventional prefix: `fix:`/`Add`/`kernel:`…) | {fmt(100.0 * conv / n)}% | "
        + (f"{fmt(100.0 * sum(1 for s in subj_rec if conv_re.match(s) or (s.split() and s.split()[0].strip(':').lower() in VERBS)) / len(subj_rec))}%" if subj_rec else "n/a")
        + f" | {SRC_GIT_ALL} |")
    add("")
    add("أكثر 8 كلمات أولى (first-words، كما هي حرفيًا): "
        + ", ".join(f"`{md_cell(w)}` ×{c}" for w, c in top8) + f" — {SRC_GIT_ALL}")
    add("")
    # 3 typical subjects: the three straddling the median char length
    by_len = sorted(subj_all, key=len)
    if by_len:
        m = len(by_len) // 2
        picks = []
        for idx in (max(0, m - 1), m, min(len(by_len) - 1, m + (1 if len(by_len) > 2 else 0))):
            s = by_len[idx]
            if s not in picks:
                picks.append(s)
        add("ثلاثة subjects نموذجية (حول الوسيط حسب الطول):")
        add("")
        for s in picks[:3]:
            add(f"- «{md_cell(s)}» — {SRC_GIT_ALL}")
else:
    add("n/a (لا توجد بيانات git صالحة)")
add("")

# --------------------------------------------------------------- 3. body
add("## 3. الجسم (body)")
add("")
if commits:
    bodies = [c["body"] for c in commits]
    nonempty = [b for b in bodies if b.strip()]
    nb = len(nonempty)
    bl = [len(b.strip().splitlines()) for b in nonempty]
    bullets = sum(1 for b in nonempty
                  if any(ln.strip().startswith(("-", "*", "•")) for ln in b.splitlines()))
    sob = sum(1 for b in nonempty if "signed-off-by:" in b.lower())
    pct = lambda k: fmt(100.0 * k / len(bodies)) + "%" if bodies else "n/a"
    add(f"عينة القياس: **{len(bodies)}** non-merge commit — {SRC_GIT_ALL}")
    add("")
    add("| المقياس | القيمة | المصدر |")
    add("|---|---|---|")
    add(f"| نسبة commits بجسم غير فارغ (non-empty body) | {pct(nb)} | {SRC_GIT_ALL} |")
    add(f"| متوسط أسطر الجسم (لمن لديه جسم؛ mean) | {fmt(mean(bl)) if bl else 'n/a'} | {SRC_GIT_ALL} |")
    add(f"| جسم يحوي bullets (`-`/`*`) | {pct(bullets)} | {SRC_GIT_ALL} |")
    add(f"| جسم يحوي `Signed-off-by:` | {pct(sob)} | {SRC_GIT_ALL} |")
else:
    add("n/a (لا توجد بيانات git صالحة)")
add("")

# ------------------------------------------------------- 4. branch prefixes
add("## 4. نمط الفروع (branch style)")
add("")
if pulls:
    prefixes = {}
    for p in pulls:
        ref = head_ref(p)
        if not ref:
            pref = "(بدون ref)"
        elif ref.startswith("refs/heads/"):
            ref2 = ref[len("refs/heads/"):]
            pref = ref2.split("/", 1)[0] + "/" if "/" in ref2 else "(مقطع واحد)"
        elif "/" in ref:
            pref = ref.split("/", 1)[0] + "/"
        else:
            pref = "(مقطع واحد)"
        prefixes[pref] = prefixes.get(pref, 0) + 1
    top = sorted(prefixes.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    add(f"عينة القياس: **{len(pulls)}** PR — {SRC_PULLS}")
    add("")
    add("| بادئة الفرع (branch prefix) | العدد | المصدر |")
    add("|---|---|---|")
    for k, v in top:
        add(f"| `{md_cell(k)}` | {v} | {SRC_PULLS} |")
else:
    add("n/a (لا توجد بيانات PR صالحة)")
add("")

# --------------------------------------------------- 5. hot files last N days
add(f"## 5. الملفات الأكثر لمسًا آخر {SINCE_DAYS} يومًا (hot files)")
add("")
if commits and recent:
    touch, churn = {}, {}
    for c in recent:
        for name, a, d in c["files"]:
            touch[name] = touch.get(name, 0) + 1
            churn[name] = churn.get(name, 0) + a + d
    ranked = sorted(touch.items(), key=lambda kv: (-kv[1], kv[0]))[:15]
    add(f"عينة القياس: **{len(recent)}** non-merge commit خلال آخر {SINCE_DAYS} يومًا — {SRC_GIT_30}. "
        "touch = عدد الـ commits التي لمست الملف؛ churn = مجموع additions+deletions. الملفات الثنائية مستثناة.")
    add("")
    add("| # | الملف | touch | churn | المصدر |")
    add("|---|---|---|---|---|")
    for i, (name, t) in enumerate(ranked, 1):
        add(f"| {i} | `{md_cell(name)}` | {t} | {churn.get(name, 0)} | {SRC_GIT_30} |")
else:
    add("n/a (لا توجد commits في نافذة آخر " + str(SINCE_DAYS) + " يومًا أو لا توجد بيانات git)")
add("")

# ------------------------------------------------------- 6. PR external merge
add("## 6. زمن PR خارجي → دمج (external PR → merge time)")
add("")
if pulls:
    def days_of(entries):
        out = []
        for p in entries:
            created = parse_iso(p.get("created_at"))
            merged = parse_iso(p.get("merged_at"))
            if not created or not merged:
                continue
            d = (merged - created).total_seconds() / 86400.0
            if d < 0:
                warn(f"PR #{p.get('number')}: merged_at قبل created_at (تم استثناؤه)")
                continue
            out.append(d)
        return out

    merged = [p for p in pulls if p.get("merged_at")]
    external = [p for p in merged if login(p) != MAINTAINER]
    own = [p for p in merged if login(p) == MAINTAINER]

    def row(entries, label):
        ds = days_of(entries)
        if not ds:
            return f"| {label} | 0 | n/a | n/a | n/a | n/a | {SRC_PULLS} |"
        return (f"| {label} | {len(ds)} | {fmt(mean(ds))} | {fmt(median(ds))} | "
                f"{fmt(min(ds))} | {fmt(max(ds))} | {SRC_PULLS} |")

    add("external = `user.login != \"gmkurtzer\"`. الوحدة: أيام (days = merged_at − created_at).")
    add("")
    add("| الشريحة | عدد PR مدموجة | mean (يوم) | median (يوم) | min | max | المصدر |")
    add("|---|---|---|---|---|---|---|")
    add(row(merged, "الكل (overall)"))
    add(row(external, "خارجية فقط (external-only)"))
    add("")
    add(f"عدد الـ PR المدموجة بواسطة/من {MAINTAINER} بنفسه (merged PRs authored by {MAINTAINER}): "
        f"**{len(own)}** من أصل {len(merged)} مدموجة — {SRC_PULLS}")
else:
    add("n/a (لا توجد بيانات PR صالحة)")
add("")

# --------------------------------------------------- 7. review phrases
add("## 7. عبارات المراجعة المتكررة (recurring review phrases)")
add("")
if reviews:
    by_state = {}
    for r in reviews:
        by_state.setdefault(r.get("state") or "(بدون حالة)", []).append(r)
    add(f"عينة القياس: **{len(reviews)}** review — {SRC_REVIEWS}")
    add("")
    add("| حالة الـ review (state) | العدد | المصدر |")
    add("|---|---|---|")
    for st in ("APPROVED", "CHANGES_REQUESTED", "COMMENTED", "DISMISSED"):
        if st in by_state:
            add(f"| `{st}` | {len(by_state[st])} | {SRC_REVIEWS} |")
    for st, rs in sorted(by_state.items()):
        if st not in ("APPROVED", "CHANGES_REQUESTED", "COMMENTED", "DISMISSED"):
            add(f"| `{md_cell(st)}` | {len(rs)} | {SRC_REVIEWS} |")
    add("")
    blocking = by_state.get("CHANGES_REQUESTED", [])
    if blocking:
        add(f"### نصوص CHANGES_REQUESTED حرفيًا ({len(blocking)})")
        add("")
        for r in sorted(blocking, key=lambda x: (x.get("submitted_at") or "", x.get("pr") or 0)):
            body = (r.get("body") or "").strip() or "(نص فارغ)"
            add(f"**PR #{r.get('pr')}** — {r.get('submitted_at') or 'n/a'} — @{login(r) or 'n/a'}:")
            add("")
            add("```")
            add(body)
            add("```")
            add("")
    KEYWORDS = {
        "tests/test": r"\btests?\b",
        "unsafe": r"\bunsafe\b",
        "overflow": r"\boverflow\b",
        "naming/name": r"\bnaming\b|\bname(?:d|s)?\b",
        "CI": r"\bCI\b",
        "docs": r"\bdocs?\b|\bdocumentation\b",
        "merge": r"\bmerge(?:d|s|able)?\b",
        "blocking": r"\bblocking\b|\bcannot merge\b",
        "exact head": r"exact head",
        "make test": r"make test",
        "make check": r"make check",
        "ABI": r"\bABI\b",
        "race": r"\brace\b",
        "panic": r"\bpanic\b",
    }
    add("تكرار الكلمات المفتاحية (عدد الـ reviews التي تذكر الكلمة، نصوص كل الحالات):")
    add("")
    add("| الكلمة المفتاحية | عدد reviews | المصدر |")
    add("|---|---|---|")
    for label, pat in KEYWORDS.items():
        cnt = sum(1 for r in reviews
                  if re.search(pat, (r.get("body") or ""), re.IGNORECASE))
        add(f"| `{label}` | {cnt} | {SRC_REVIEWS} |")
else:
    add("n/a (لا توجد بيانات reviews صالحة)")
add("")

# ------------------------------------------------- 8. maintainer comments
add(f"## 8. طلبات المراجعة المتكررة ({MAINTAINER} comments — recurring requests)")
add("")
gk = [c for c in comments if login(c) == MAINTAINER]
if gk:
    THEMES = {
        "CI/checks خضراء قبل الدمج": r"\bCI\b|GitHub Actions|checks are green|fresh GitHub",
        "تشغيل make test / make check": r"make test|make check",
        "الالتزام بـ \"exact head\" / قابلية إعادة الإنتاج (reproducibility)": r"exact head|reproducib",
        "طلب اختبارات (tests) جديدة/مصفوفة": r"\btests?\b|matrix|test suite",
        "دليل تحقق (validation evidence)": r"validated|verified|evidence",
        "توثيق (docs/README)": r"\bdocs?\b|documentation|README",
        "سلامة الذاكرة (unsafe/safety)": r"\bunsafe\b|safety|soundness",
        "شكر/تقدير (thanks)": r"thank",
    }
    add(f"عينة القياس: **{len(gk)}** تعليق من @{MAINTAINER} (من أصل {len(comments)} تعليقًا) — {SRC_COMMENTS}")
    add("")
    add("| النمط المطلوب (theme) | عدد التعليقات | المصدر |")
    add("|---|---|---|")
    for label, pat in THEMES.items():
        cnt = sum(1 for c in gk if re.search(pat, c.get("body") or "", re.IGNORECASE))
        add(f"| {label} | {cnt} | {SRC_COMMENTS} |")
    add("")
    # representative quotes: most theme-matching comments first, then earliest
    def score(c):
        return sum(1 for pat in THEMES.values()
                   if re.search(pat, c.get("body") or "", re.IGNORECASE))
    ranked = sorted(gk, key=lambda c: (-score(c), c.get("created_at") or "", c.get("pr") or 0))
    seen_pr, quotes = set(), []
    for c in ranked:
        pr = c.get("pr")
        if pr in seen_pr:
            continue
        seen_pr.add(pr)
        text = " ".join((c.get("body") or "").split())
        text = text.replace("\\n", " / ")  # dump quirk: some bodies hold literal backslash-n
        if len(text) > 140:
            text = text[:140].rsplit(" ", 1)[0] + "…"
        quotes.append((pr, c.get("created_at") or "n/a", text))
        if len(quotes) == 5:
            break
    if quotes:
        add("اقتباسات تمثيلية (≤140 حرفًا):")
        add("")
        for pr, at, text in quotes:
            add(f"- PR #{pr} ({at}): «{md_cell(text)}» — {SRC_COMMENTS}")
else:
    add("n/a (لا توجد تعليقات من @" + MAINTAINER + " في البيانات)")
add("")

# --------------------------------------------- 9. comparison with old PLAN
add("## 9. المقارنة بإحصاءات PLAN القديمة (توجيه v3.3 §2b)")
add("")
if commits:
    a_all = [c["adds"] for c in commits]
    d_all = [c["dels"] for c in commits]
    words = [len(c["subject"].split()) for c in commits if c["subject"]]
    CLAIM_ADD, CLAIM_DEL, CLAIM_WORDS = 567, 368, 5
    m_add, m_del, m_w = mean(a_all), mean(d_all), mean(words)

    def delta(m, c):
        if m is None:
            return "n/a", "n/a"
        d = m - c
        p = fmt(100.0 * d / c) + "%" if c else "n/a"
        return f"{d:+.1f}", p

    add("القيم القديمة مأخوذة من وثائق PLAN الداخلية القديمة (توجيه v3.3 §2b) وتعتبر "
        "`[CLAIMED]` وليست مقيسة هنا؛ عمود \"المقيس\" من نفس عينة القسم 1 و2.")
    add("")
    add("| المقياس | CLAIMED (PLAN قديمة) | MEASURED (مقيس) | الفرق Δ | Δ% | مصدر المقيس |")
    add("|---|---|---|---|---|---|")
    d1, p1 = delta(m_add, CLAIM_ADD)
    add(f"| mean additions/commit | {CLAIM_ADD} | {fmt(m_add)} | {d1} | {p1} | {SRC_GIT_ALL} |")
    d2, p2 = delta(m_del, CLAIM_DEL)
    add(f"| mean deletions/commit | {CLAIM_DEL} | {fmt(m_del)} | {d2} | {p2} | {SRC_GIT_ALL} |")
    d3, p3 = delta(m_w, CLAIM_WORDS)
    add(f"| mean عدد كلمات الـ subject | {CLAIM_WORDS} | {fmt(m_w)} | {d3} | {p3} | {SRC_GIT_ALL} |")
    add("")
    add(f"**الخلاصة:** الإحصاءات القديمة (‎+{CLAIM_ADD}/−{CLAIM_DEL}‎ وكلمات ≈{CLAIM_WORDS}) "
        + ("أكبر بكثير من المقيس فعليًا — يبدو أنها قِيست على شريحة مختلفة (مثل PRs كبيرة أو بيانات أولية) ولا تعبر عن أسلوب الـ commits الفعلي"
           if (m_add or 0) < CLAIM_ADD * 0.5 and (m_del or 0) < CLAIM_DEL * 0.5
           else "قريبة/مقاربة للمقيس فعليًا — راجع الفروق في الجدول أعلاه")
        + ".")
else:
    add("n/a (لا توجد بيانات git صالحة للمقارنة)")
add("")

# ------------------------------------------------------------------- footer
add("---")
add("")
add("## المصادر (data sources)")
add("")
add(f"- repo: `{REPO}` — HEAD SHA: `{head_sha or 'n/a'}`" + (f" (as-of {GIT_ASOF})" if GIT_ASOF else ""))
add(f"- pulls: `{PULLS.split('/')[-1] if PULLS else '—'}` ({len(pulls)} سجلًا) — {SRC_PULLS}")
add(f"- reviews: `{REVIEWS.split('/')[-1] if REVIEWS else '—'}` ({len(reviews)} سجلًا) — {SRC_REVIEWS}")
add(f"- comments: `{COMMENTS.split('/')[-1] if COMMENTS else '—'}` ({len(comments)} سجلًا) — {SRC_COMMENTS}")
add(f"- تاريخ التوليد: {GEN} UTC")
add("- ملاحظات منهجية: merge commits مستثناة من أقسام git؛ الملفات الثنائية (binary numstat `-`) "
    "مستثناة من الأحجام والـ churn؛ حقول `additions/deletions/changed_files` في dump الـ PRs تأتي "
    "`null` من API القائمة (GitHub quirk) ولا يستخدمها هذا التقرير؛ كيان `user`/`head` يُقرأ بصيغة "
    "الـ dump المسطّحة أو صيغة API الخام على السواء؛ بعض أجسام التعليقات تحوي `\\n` حرفيًا (quirk في "
    "سكربت الـ dump) وتُطبّع إلى ` / ` في الاقتباسات.")
if warnings:
    add("- تحذيرات:")
    for w in sorted(set(warnings)):
        add(f"  - {w}")

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
print(f"wrote {OUT} ({len(lines)} lines)", file=sys.stderr)
PYEOF
