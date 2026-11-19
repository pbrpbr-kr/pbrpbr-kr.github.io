#!/bin/bash
# _posts 에 새로 생긴 글을 커밋하고 GitHub에 push → GitHub Pages가 자동 재배포.
# 사용: publish.sh "<커밋 메시지>"
set -euo pipefail
. "$(dirname "$0")/git_env.sh"
cd "$ROOT"
# 관리자 화면(Pages CMS)에서 고친 내용을 먼저 받아 온 뒤 올린다
git pull -q --rebase --autostash origin main
git add _posts
[ -d assets/img/posts ] && git add assets/img/posts
if git diff --cached --quiet; then echo "NOTHING_TO_PUBLISH"; exit 0; fi
git commit -q -m "${1:-새 글 발행}"
git push -q origin main
echo "PUBLISHED $(git rev-parse --short HEAD)"
