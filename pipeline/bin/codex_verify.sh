#!/bin/bash
# 외부 모델 검증자: OpenAI Codex가 웹 검색으로 주장을 처음부터 따로 확인한다.
# (~/.claude/agents/codex.md 의 codex 에이전트와 같은 `codex exec` 방식, 읽기 전용 샌드박스)
# 사용: codex_verify.sh <claims.json> <out.json>
#   claims.json: [{"id":1,"text":"..."}, ...]  — 주장만 넘기고, 수집 단계의 출처는 넘기지 않는다(독립성).
set -uo pipefail
CLAIMS="$1"; OUT="$2"
CODEX="$(command -v codex || echo "$HOME/.local/bin/codex")"
DIR="$(cd "$(dirname "$CLAIMS")" && pwd)"
PROMPT="당신은 피부미용 분야 팩트체커입니다. 아래 파일 $(basename "$CLAIMS") 의 각 주장을 웹 검색으로 직접 확인하세요.
규칙:
- 다른 검증자의 결과는 없습니다. 스스로 출처를 찾으세요. 가능하면 1차 출처(논문, 공공기관, 기업 공시·보도자료, 주요 언론)를 쓰세요.
- 인스타그램·X·쓰레드 페이지를 직접 긁지 말고, 공개된 기사·보고서·공식 페이지만 쓰세요.
- 판정: supported(독립 출처 2곳 이상이 뒷받침) / partial(일부만 맞거나 과장) / contradicted(출처가 반대) / unverifiable(확인할 출처 없음).
- 출력은 JSON 배열 하나만, 다른 텍스트 없이:
[{\"id\":1,\"verdict\":\"supported\",\"reason\":\"한국어 한두 문장\",\"sources\":[{\"title\":\"...\",\"url\":\"https://...\"}]}]"
"$CODEX" exec -s read-only --skip-git-repo-check --color never -c web_search='"live"' \
  -C "$DIR" -o "$OUT.raw" "$PROMPT" < /dev/null > "$OUT.log" 2>&1
code=$?
# 응답에서 JSON 배열만 추출
/usr/bin/python3 - "$OUT.raw" "$OUT" <<'PY'
import json, re, sys
raw = open(sys.argv[1], encoding="utf-8").read() if __import__("os").path.exists(sys.argv[1]) else ""
m = re.search(r"\[.*\]", raw, re.S)
try:
    data = json.loads(m.group(0)) if m else None
except Exception:
    data = None
json.dump({"verifier": "codex", "ok": data is not None, "results": data, "raw": None if data else raw[:2000]},
          open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("CODEX_OK" if data is not None else "CODEX_PARSE_FAILED")
PY
echo "codex_exit=$code"
