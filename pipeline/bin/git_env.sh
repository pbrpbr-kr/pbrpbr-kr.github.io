# source 해서 쓴다. .env에서 GITHUB_REPO, GITHUB_TOKEN을 읽고,
# 토큰을 명령줄·원격 URL에 남기지 않도록 GIT_ASKPASS로 넘긴다.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)"
set -a; [ -f "$ROOT/.env" ] && . "$ROOT/.env"; set +a
if [ -z "${GITHUB_REPO:-}" ] || [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "ERROR: .env에 GITHUB_REPO(예: myname/skin-blog)와 GITHUB_TOKEN을 넣어 주세요." >&2
  return 1 2>/dev/null || exit 1
fi
ASKPASS="$ROOT/pipeline/bin/.askpass.sh"
printf '#!/bin/sh\ncase "$1" in Username*) echo x-access-token;; *) echo "$GITHUB_TOKEN";; esac\n' > "$ASKPASS"
chmod 700 "$ASKPASS"
export GIT_ASKPASS="$ASKPASS" GIT_TERMINAL_PROMPT=0 GITHUB_TOKEN
REMOTE_URL="https://github.com/${GITHUB_REPO}.git"
