# 스킨 트렌드 리포트 — 자동 조사·발행 블로그

- **사이트**: Jekyll 정적 사이트, GitHub Pages가 빌드·호스팅 (`_layouts`, `_includes`, `assets`, `index.html`, `policy.md`)
- **파이프라인**: `pipeline/RUNBOOK.md` — Claude 데스크톱 앱의 예약 작업이 월·목 09:00에 이 절차를 실행
- **교차검증**: SNS 신호만 있는 주장은 독립 검증자 3명이 확인합니다.
  - `skin-verifier-sources`: 독립 출처 확인
  - `skin-verifier-skeptic`: 의학 근거·안전성 확인
  - `codex_verify.sh`: OpenAI Codex 확인
  - 에이전트 정의는 `.claude/agents/`에 있습니다.
- **발행 정책**: `build_post.py`의 검증 규칙과 의료광고 표현 점검을 통과하면 자동 발행합니다. 통과하지 못하면 `pipeline/review_queue/`로 갑니다.

## 처음 설정 (사용자가 직접)
1. GitHub에서 **Public** 저장소를 비어 있는 상태로 만듭니다. README를 추가하지 마세요. 예: `skin-blog`
2. Fine-grained 토큰을 만듭니다.
   - 위치: GitHub → Settings → Developer settings → Fine-grained tokens
   - 저장소: 이 저장소만 선택
   - 권한: Contents (Read and write), Pages (Read and write)
3. `.env.example`을 `.env`로 복사하고 `GITHUB_REPO`, `GITHUB_TOKEN`을 넣습니다. 선택 API 키는 나중에 넣어도 됩니다.
4. `bash pipeline/bin/setup_github.sh`를 실행합니다. 첫 push와 Pages 활성화를 하고 사이트 URL을 출력합니다.

## 검토 대기 글 발행
`pipeline/review_queue/<이름>/`의 `REVIEW.json`에서 걸린 이유를 확인합니다. `body.md`와 `post.json`을 고친 뒤 아래를 차례로 실행합니다.

```bash
python3 pipeline/bin/build_post.py pipeline/review_queue/<이름>
bash pipeline/bin/publish.sh "새 글: <제목>"
```
