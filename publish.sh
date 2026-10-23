#!/usr/bin/env bash
# Build and publish site/ to the gh-pages branch (GitHub Pages source = gh-pages / root).
# Used because the box's gh token lacks the `workflow` scope needed to push an Actions workflow.
set -euo pipefail
cd "$(dirname "$0")"
python3 build.py
touch site/.nojekyll
SRC_SHA=$(git rev-parse --short HEAD)
TMP=$(mktemp -d)
cp -r site/. "$TMP"/
cd "$TMP"
git init -q -b gh-pages
git config user.name "$(git -C "$OLDPWD" config user.name)"
git config user.email "$(git -C "$OLDPWD" config user.email)"
git add -A
git commit -qm "Deploy site from main@$SRC_SHA"
git push -q -f "$(git -C "$OLDPWD" remote get-url origin)" gh-pages
cd - >/dev/null; rm -rf "$TMP"
echo "Pushed gh-pages from main@$SRC_SHA"
