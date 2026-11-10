#!/usr/bin/env bash
# test-push-retry-offline.sh — v7.3-2c offline simulation of the team-watcher
# "Commit and push" failure class (run 29, 2026-11-09T21:41:49Z, exit 128).
#
# Reproduces failure modes WITHOUT any network using local bare "origin" repos:
#   Scenario A (faithful to production): competing workflow (monitor-style)
#     commits a DIFFERENT matrix file; worker's plain push is rejected —
#     retry loop (pull --rebase -X theirs + push, 3 attempts) recovers.
#   Scenario B (stress): competing writer touches the SAME state file —
#     plain push rejected, plain rebase would CONFLICT [MEASURED locally
#     2026-11-10], the fixed loop (-X theirs: fresh sweep hunks win +
#     rebase --abort between attempts) recovers.
# Pure local filesystem repos — zero GitHub calls.
set -u
PASS=0; FAIL=0

check() { # name expected (0 = must succeed, 1 = must fail) actual
  if [ "$2" = 0 ] && [ "$3" = 0 ]; then
    echo "PASS - $1"; PASS=$((PASS+1))
  elif [ "$2" != 0 ] && [ "$3" != 0 ]; then
    echo "PASS - $1"; PASS=$((PASS+1))
  else
    echo "FAIL - $1"; FAIL=$((FAIL+1))
  fi
}

retry_loop() { # inside worker dir: exact workflow pattern
  local ok=0 i
  for i in 1 2 3; do
    if git pull --rebase -X theirs origin main && git push -q origin HEAD:main; then ok=1; break; fi
    git rebase --abort >/dev/null 2>&1 || true
    sleep 0.2
  done
  [ "$ok" = 1 ]
}

mk_stage() { # $1 = dir: origin + worker + competing "other"
  rm -rf "$1"; mkdir -p "$1"
  git init -q --bare "$1/origin.git"
  git -C "$1/origin.git" symbolic-ref HEAD refs/heads/main
  git clone -q "$1/origin.git" "$1/worker"
  git -C "$1/worker" config user.email t@t; git -C "$1/worker" config user.name t
  git clone -q "$1/origin.git" "$1/other"
  git -C "$1/other" config user.email o@o; git -C "$1/other" config user.name o
}

# ---------- Scenario A: different-file race (production-faithful) ----------
A="$(mktemp -d)"; mk_stage "$A"
mkdir -p "$A/worker/matrix" "$A/other/matrix"
echo '{"hb":"base"}' > "$A/worker/matrix/upstream-watch.json"
git -C "$A/worker" add -A && git -C "$A/worker" commit -qm "base [skip ci]" && git -C "$A/worker" push -q origin HEAD:main
# competing workflow (monitor-style): sync onto the pushed base first, then commit a DIFFERENT file
git -C "$A/other" fetch -q origin main && git -C "$A/other" reset -q --hard FETCH_HEAD
echo '{"notify":"v1"}' > "$A/other/matrix/notify-state.json"
git -C "$A/other" add -A && git -C "$A/other" commit -qm "monitor state [skip ci]" && git -C "$A/other" push -q origin HEAD:main
# worker (stale) commits sweep state, plain push — must FAIL
echo '{"hb":"sweep1"}' > "$A/worker/matrix/upstream-watch.json"
git -C "$A/worker" add -A && git -C "$A/worker" commit -qm "lease sweep [skip ci]"
git -C "$A/worker" push origin HEAD:main >/dev/null 2>&1
check "A: plain push against moved remote fails (run 29 class)" 1 $?
cd "$A/worker" && retry_loop
check "A: retry loop (pull --rebase -X theirs + push x3) recovers" 0 $?
n=$(git -C "$A/origin.git" log --oneline main | wc -l)
if [ "$n" -ge 3 ]; then echo "PASS - A: origin/main holds monitor + sweep commits ($n)"; PASS=$((PASS+1)); else echo "FAIL - A: history incomplete ($n)"; FAIL=$((FAIL+1)); fi

# ---------- Scenario B: same-file race (stress; fresh sweep wins) ----------
B="$(mktemp -d)"; mk_stage "$B"
mkdir -p "$B/worker/matrix" "$B/other/matrix"
echo '{"hb":"base"}' > "$B/worker/matrix/upstream-watch.json"
git -C "$B/worker" add -A && git -C "$B/worker" commit -qm "base [skip ci]" && git -C "$B/worker" push -q origin HEAD:main
# competing writer: sync onto the base, then touches the SAME file
git -C "$B/other" fetch -q origin main && git -C "$B/other" reset -q --hard FETCH_HEAD
echo '{"hb":"competing"}' > "$B/other/matrix/upstream-watch.json"
git -C "$B/other" add -A && git -C "$B/other" commit -qm "other sweep [skip ci]" && git -C "$B/other" push -q origin HEAD:main
echo '{"hb":"fresh-sweep"}' > "$B/worker/matrix/upstream-watch.json"
git -C "$B/worker" add -A && git -C "$B/worker" commit -qm "lease sweep [skip ci]"
git -C "$B/worker" push origin HEAD:main >/dev/null 2>&1
check "B: plain push against same-file race fails" 1 $?
cd "$B/worker" && retry_loop
check "B: retry loop with -X theirs resolves same-file race" 0 $?
landed=$(git -C "$B/origin.git" show main:matrix/upstream-watch.json 2>/dev/null | tr -d ' \n')
if echo "$landed" | grep -q "fresh-sweep"; then echo "PASS - B: fresh sweep state landed on origin"; PASS=$((PASS+1)); else echo "FAIL - B: landed=$landed"; FAIL=$((FAIL+1)); fi

rm -rf "$A" "$B"
echo "test-push-retry-offline: $PASS PASS / $FAIL FAIL (local only, no network)"
[ "$FAIL" = 0 ]
