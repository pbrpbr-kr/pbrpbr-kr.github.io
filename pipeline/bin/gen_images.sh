#!/bin/bash
# 글 이미지 생성: OpenAI Codex(ChatGPT 이미지 생성 기능)로 images.json의 이미지를 만들고
# assets/img/posts/<slug>/<id>.jpg 로 저장한다.
# 사용: gen_images.sh <work_dir> <slug>
#   images.json: [{"id":"hero","prompt":"영문 장면 묘사","alt":"대체 텍스트","caption":"캡션"}, ...]
#   - id "hero"는 제목 아래 대표 이미지, 나머지는 본문의 [[img:<id>]] 자리에 들어간다.
set -uo pipefail
WORK="$(cd "$1" && pwd)"; SLUG="$2"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CODEX="$(command -v codex || echo "$HOME/.local/bin/codex")"
OUTDIR="$ROOT/assets/img/posts/$SLUG"
RAW="$WORK/img_raw"
mkdir -p "$OUTDIR" "$RAW"

LIST=$(/usr/bin/python3 - "$WORK/images.json" <<'PY'
import json, sys
for im in json.load(open(sys.argv[1], encoding="utf-8")):
    print(f'- {im["id"]}.png : {im["prompt"]}')
PY
)

PROMPT="이미지 생성 도구로 아래 이미지들을 하나씩 만들고, 각 파일을 이 디렉터리($RAW)에 지정한 파일명으로 저장하세요(도구가 다른 곳에 저장하면 여기로 복사).

공통 스타일: 고급 라이프스타일 매거진의 에디토리얼 일러스트/스틸라이프. 부드러운 자연광, 크림·피치·세이지 계열의 차분한 색감, 여백이 넉넉한 구도, 16:9 가로.
반드시 지킬 것(의료광고 규제):
- 글자, 숫자, 로고, 브랜드명, 실제 제품 패키지 없음
- 실제 인물이나 알아볼 수 있는 얼굴 없음. 피부 상태가 좋아지거나 나빠진 모습, 전후 비교, 화면 분할 비교 없음
- 사람에게 주사·시술하는 장면, 병원·클리닉 내부, 의료진 없음
- 과장된 '빛나는 피부' 효과 연출 없음

만들 이미지:
$LIST

끝나면 저장한 파일 경로와 픽셀 크기만 한 줄씩 답하세요."

"$CODEX" exec -s workspace-write --skip-git-repo-check --color never -C "$RAW" \
  -o "$WORK/images_codex.md" "$PROMPT" < /dev/null > "$WORK/images_codex.log" 2>&1
echo "codex_exit=$?"

/usr/bin/python3 - "$WORK/images.json" "$RAW" "$OUTDIR" <<'PY'
import json, subprocess, sys
from pathlib import Path
ims = json.load(open(sys.argv[1], encoding="utf-8")); raw = Path(sys.argv[2]); out = Path(sys.argv[3])
ok = True
for im in ims:
    src = raw / f'{im["id"]}.png'
    dst = out / f'{im["id"]}.jpg'
    if not src.exists():
        print(f'MISSING {im["id"]}'); ok = False; continue
    subprocess.run(["/usr/bin/sips", "-s", "format", "jpeg", "-s", "formatOptions", "82",
                    "--resampleWidth", "1600", str(src), "--out", str(dst)], capture_output=True)
    print(f'OK {im["id"]} -> {dst} ({dst.stat().st_size//1024} KB)')
print("IMAGES_OK" if ok else "IMAGES_INCOMPLETE")
PY
