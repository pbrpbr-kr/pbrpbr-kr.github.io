#!/bin/bash
# 최초 1회: 로컬 저장소 초기화 → GitHub에 push → GitHub Pages 켜기 → 사이트 URL 출력.
# 사전 준비(사용자): GitHub에서 Public 저장소를 비어 있는 상태로 만들고, .env에 GITHUB_REPO/GITHUB_TOKEN 입력.
set -euo pipefail
. "$(dirname "$0")/git_env.sh"
cd "$ROOT"
OWNER="${GITHUB_REPO%%/*}"; NAME="${GITHUB_REPO##*/}"
OWNER_LC="$(echo "$OWNER" | tr '[:upper:]' '[:lower:]')"
if [ "$(echo "$NAME" | tr '[:upper:]' '[:lower:]')" = "${OWNER_LC}.github.io" ]; then BASEURL=""; else BASEURL="/$NAME"; fi
SITE_URL="https://${OWNER_LC}.github.io"
/usr/bin/sed -i '' -e "s|^url: .*|url: \"$SITE_URL\"|" -e "s|^baseurl: .*|baseurl: \"$BASEURL\"|" _config.yml

[ -d .git ] || git init -q -b main
git config user.name >/dev/null || git config user.name "skin-blog-bot"
git config user.email >/dev/null || git config user.email "skin-blog-bot@users.noreply.github.com"
git remote remove origin 2>/dev/null || true
git remote add origin "$REMOTE_URL"
git add -A
git commit -q -m "블로그 초기 설정" || true
git push -q -u origin main

API="https://api.github.com/repos/$GITHUB_REPO/pages"
AUTH=(-H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28")
code=$(curl -s -o /dev/null -w '%{http_code}' "${AUTH[@]}" "$API")
if [ "$code" != "200" ]; then
  curl -sS -X POST "${AUTH[@]}" "$API" -d '{"source":{"branch":"main","path":"/"}}' >/dev/null
fi
echo "PAGES_URL=${SITE_URL}${BASEURL}/"
