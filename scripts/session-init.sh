#!/usr/bin/env bash
# session-init.sh — هوية git الصحيحة لكل جلسة عمل
# (توجيه المستخدم 2026-11-03 بعد اكتشاف commit 701edf5 بهوية افتراضية "Z User <z@container>" في PR 61)
# تُنفَّذ في بداية كل جلسة، وتُتحقق الهوية بـ git config --get قبل أي commit أو merge.
set -euo pipefail

GIT_NAME="Abdelhafid DJIDEL"
GIT_EMAIL="266947999+hafid-logic@users.noreply.github.com"

git config --global user.name  "$GIT_NAME"
git config --global user.email "$GIT_EMAIL"

# تحقق إلزامي — توقف بخطأ إذا لم تستقر الهوية
NAME="$(git config --get user.name)"
EMAIL="$(git config --get user.email)"
if [ "$NAME" != "$GIT_NAME" ] || [ "$EMAIL" != "$GIT_EMAIL" ]; then
  echo "IDENTITY MISMATCH: '$NAME' <$EMAIL>" >&2
  exit 1
fi
echo "git identity OK: $NAME <$EMAIL>"
