#!/usr/bin/env bash
# install-pre-commit.sh — re-establish the local .git/hooks/pre-commit (v7.5-1).
#
# The sandbox rotation wipes .git/hooks (recurrence recorded in STATE v6.7-0
# and v6.8-0). This installer is idempotent and rebuilds the combined hook
# from three tracked stages:
#   1. CJK gate ........ scripts/check_cjk.py on staged gated .md
#   2. key-guard ....... inline (token full forms + work/.config paths)
#   3. report-lint ..... scripts/report_lint.py --fix on staged outbox/*.md
# Run after every fresh box: bash scripts/hooks/install-pre-commit.sh
set -euo pipefail
cd "$(dirname "$0")/../.."

HOOK=.git/hooks/pre-commit
mkdir -p .git/hooks

cat > "$HOOK" <<'HOOK'
#!/usr/bin/env bash
# Combined pre-commit hook — stages installed by scripts/hooks/install-pre-commit.sh
# (v7.5-1). Each stage can be skipped for meta-commits with SKIP_LINT_REASON=<reason>.
set -u
rc=0

# ---------- stage 1: CJK gate (gated dirs only: outbox reports docs directives) ----------
staged_cjk=$(git diff --cached --name-only --diff-filter=ACM -- outbox reports docs directives || true)
staged_cjk=$(printf '%s\n' "$staged_cjk" | grep -E '^(outbox|reports|docs|directives)/.*\.md$' || true)
if [ -n "$staged_cjk" ]; then
  if ! python3 scripts/check_cjk.py $staged_cjk; then
    echo "pre-commit: CJK gate failed" >&2; rc=1
  fi
fi

# ---------- stage 2: key-guard ----------
staged_all=$(git diff --cached --name-only --diff-filter=ACM || true)
for f in $staged_all; do
  case "$f" in
    work/.config/*)
      echo "pre-commit: key-guard: $f under work/.config/ is not trackable" >&2; rc=1; continue ;;
  esac
  if git show ":$f" 2>/dev/null | grep -Eqn -e \
      '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|ghp_[A-Za-z0-9]{36}|gho_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,}|nvapi-[A-Za-z0-9_\-]{20,}|sk-[A-Za-z0-9_\-]{20,}|AKIA[0-9A-Z]{16}|xox[abp]-[A-Za-z0-9\-]{16,}|AIza[0-9A-Za-z_\-]{35}'; then
    echo "pre-commit: key-guard: $f contains a private-key block or full-form token (never print it)" >&2
    rc=1
  fi
done

# ---------- stage 3: report-lint on staged outbox reports ----------
staged_reports=$(git diff --cached --name-only --diff-filter=ACM -- 'outbox/*.md' \
                | grep -v -E 'outbox/(INDEX|LATEST|_TEMPLATE)\.md' || true)
if [ -n "$staged_reports" ] && [ -x scripts/report_lint.py ]; then
  if ! python3 scripts/report_lint.py --fix $staged_reports; then
    echo "pre-commit: report-lint FAIL — fix the report or tag the defect honestly" >&2
    rc=1
  fi
  # --fix may have rewritten the lint line inside the staged files: re-add
  for f in $staged_reports; do git add -- "$f"; done
fi

exit $rc
HOOK
chmod +x "$HOOK"

# verify the three stage sources exist
for s in scripts/check_cjk.py scripts/report_lint.py; do
  [ -f "$s" ] || { echo "missing $s" >&2; exit 1; }
done
echo "pre-commit hook installed: $HOOK (CJK + key-guard + report-lint)"
