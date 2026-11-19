# 피부미용 트렌드 블로그 — 1회 실행 절차

예약 작업이 실행될 때마다 이 절차를 처음부터 끝까지 따릅니다. 사람의 입력 없이 끝까지 진행합니다. 주제 선택은 '총괄' 서브에이전트가 사용자 대신 합니다. 막히면 그 단계를 실패로 기록하고 멈춥니다.

- 프로젝트 루트: `/Users/sungminjang/클로드/skin-blog` (아래 경로는 모두 여기 기준)
- 실행 ID: `RUN=$(date +%Y%m%d-%H%M)`, 작업 폴더: `pipeline/work/$RUN/`
- 실행 로그: `pipeline/runs/$RUN.md`에 단계별 결과를 계속 덧붙입니다.

## 지켜야 할 원칙 (모든 단계에 적용)
1. **수집 방법**: 인스타그램·X·쓰레드·유튜브 화제성은 ① `.env`에 키가 있는 공식 API(`collect_optional.py`) ② 공개된 기사·리포트·트렌드 정리 글(WebSearch/WebFetch)로만 확인합니다. 플랫폼 페이지를 직접 긁지 않습니다. 로그인이 필요한 페이지는 열지 않습니다.
2. **의료광고 규제(의료법 제56조)**: 효과 보장·단정, 부작용 부정, 전후 비교, 체험 후기, 특정 병원·의사·가격·할인·예약 유도를 쓰지 않습니다. 제품·장비명은 업계 동향을 설명하는 데에만 쓰고, 권유하지 않습니다.
3. **자격증명**: `.env`를 읽기만 하고 수정하거나 출력하지 않습니다. 없는 키는 건너뜁니다.
4. **독립성**: 검증자 세 명에게는 주장 목록만 넘깁니다. 초안 본문, 수집 출처, 다른 검증자의 결과는 넘기지 않습니다.

## 1. 주제 후보 수집
0. 먼저 관리자 화면에서 바뀐 글을 받아 옵니다: `bash -c '. pipeline/bin/git_env.sh && git pull -q --rebase --autostash origin main'`
1. 최근 60일 동안 다룬 주제를 확인합니다: `ls _posts pipeline/review_queue` 그리고 `pipeline/topics_history.txt`가 있으면 읽습니다. 같은 주제는 다시 고르지 않습니다.
2. WebSearch로 최근 2~4주의 화제 신호를 찾습니다. 한국어 검색과 영어 검색을 섞고, 최소 6번 검색합니다. 예:
   - "리프팅 시술 트렌드 {이번 달}", "피부과 시술 인기 2026", "올리브영 랭킹 성분", "인스타그램 화제 스킨케어 성분", "쓰레드 피부 시술 화제", "K-beauty trending ingredient", "aesthetic procedure trend 2026", "skin booster trend"
   - 범주: 리프팅(장비·실), 주사·시술(스킨부스터, 필러, 보톡스 계열), 재료·성분(PDRN, 엑소좀, 펩타이드, 레티날 등), 홈케어·뷰티 디바이스, 트렌드.
3. 후보 4개 이상을 고르고, 각 후보마다 화제 신호의 근거 URL을 기록합니다.

## 2. 객관 데이터 수집
후보마다 영어 PubMed 검색어를 정하고, 수집기에는 한국어 키워드를 넘깁니다.
```bash
cd /Users/sungminjang/클로드/skin-blog/pipeline/bin
python3 collect_pubmed.py "<영어 검색어1>" "<영어 검색어2>" > ../work/$RUN/pubmed.json
python3 collect_optional.py "<한국어 키워드1>" "<한국어 키워드2>" > ../work/$RUN/optional.json
```
그 밖에 WebSearch로 판매량(올리브영·쿠팡 랭킹 기사, 기업 실적·IR), 시술 건수와 시장 규모(공공 통계, 업계 리포트), 허가 현황(식약처·FDA)을 찾습니다.

## 3. 주제 선정 — '총괄' 서브에이전트가 고름
사용자에게 묻지 않습니다. 사용자 역할은 '총괄'(`skin-chief-editor`) 서브에이전트가 맡습니다.

1. 후보를 **정확히 4개** 정리해 `work/$RUN/candidates.md`에 씁니다. 후보가 4개보다 적으면 1단계 검색을 더 해서 채웁니다.
   - 후보마다 적을 것: 한 줄 요약, 화제 신호(무엇이, 어디서), 확보한 객관 데이터, 예상 근거 수준(objective / mixed / cross_verified_sns), 규제 위험(낮음/중간/높음)과 이유
   - 특정 병원의 이벤트나 단일 제품 광고에 가까운 후보는 처음부터 뺍니다.
   - 4개 중 **2개 이상**은 단순 화장품·단순 성분이 아닌 주제로 채웁니다. 예: 리프팅에 대한 새로운 관점, 새 시술·장비 흐름, 사회적 현상이 된 트렌드
2. Agent 도구로 `subagent_type: "skin-chief-editor"`를 실행합니다.
   - 프롬프트에 줄 것: 후보 파일 경로, 지난 글 위치(`_posts/`, `pipeline/topics_history.txt`), 결과 파일 경로 `work/$RUN/chief_decision.json`
   - 그 subagent_type을 찾을 수 없으면 `/Users/sungminjang/클로드/skin-blog/.claude/agents/skin-chief-editor.md`를 읽어, 그 내용을 프롬프트로 general-purpose 에이전트를 실행합니다.
3. 총괄의 결정을 그대로 따릅니다. 메인 세션은 결정을 바꾸지 않습니다.
   - `selected`가 null이면 1단계로 돌아가 새 후보 4개를 모으고 총괄에게 다시 맡깁니다(최대 1회). 두 번째도 null이면 "발행할 주제 없음"으로 끝냅니다.
   - 총괄이 제안한 `angle`은 6단계 글 작성의 기사 방향으로 씁니다.
4. 실행 로그에 남길 것: 후보 4개의 한 줄 요약, 총괄의 점수표, 고른 주제, 이유

## 4. 주장 정리
글의 핵심 주장을 4~8개로 정리해 `work/$RUN/claims_all.json`에 저장합니다.
```json
[{"id":1,"text":"...","evidence":"objective","source_ids":[1,3]},
 {"id":2,"text":"...","evidence":"sns","source_ids":[4]}]
```
- `objective`: 논문 수, 검색량, 판매 순위·실적, 시술·시장 통계, 허가 정보 같은 객관 출처로 직접 뒷받침되는 주장
- `sns`: 객관 지표가 없고 SNS·인플루언서 화제성이나 보도에만 기대는 주장
- 출처 목록 `sources`도 이때 만듭니다. `type`은 paper / search_trend / sales / procedure_stats / regulatory / market_report / news / sns / influencer / industry / other 중 하나입니다.

## 5. 독립 교차검증 (sns 주장이 하나라도 있으면 반드시 실행)
`work/$RUN/claims_sns.json`에 sns 주장만 `[{"id":..,"text":..}]` 형식으로 저장합니다. 그다음 **세 검증자를 동시에** 실행합니다.

| 검증자 | 실행 방법 | 관점 |
|---|---|---|
| sources | Agent 도구, `subagent_type: "skin-verifier-sources"` | 독립 출처(언론·업계·공공기관) |
| skeptic | Agent 도구, `subagent_type: "skin-verifier-skeptic"` | 의학 근거·안전성·과장 |
| codex | Bash: `pipeline/bin/codex_verify.sh work/$RUN/claims_sns.json work/$RUN/verify_codex.json` (timeout 600000) | 다른 회사의 모델(OpenAI)이 처음부터 따로 확인 |

- 에이전트 프롬프트에는 claims 파일 경로, 결과 파일 경로(`work/$RUN/verify_sources.json`, `verify_skeptic.json`), 그리고 sources 검증자에게는 제외 도메인(수집 때 쓴 출처 도메인)만 줍니다.
- 그 subagent_type을 찾을 수 없으면 `/Users/sungminjang/클로드/skin-blog/.claude/agents/<이름>.md`를 읽어 그 내용을 프롬프트로 general-purpose 에이전트를 실행합니다.
- codex가 실패하면(`CODEX_PARSE_FAILED`, 로그인 오류 등) 한 번만 다시 시도합니다. 그래도 실패하면 codex 판정을 `unverifiable`로 기록합니다. 이 경우 나머지 두 검증자가 모두 `supported`여야 통과합니다.

결과 정리:
- 주장마다 `verdicts: {"sources": .., "skeptic": .., "codex": ..}`를 붙입니다.
- `contradicted`가 하나라도 있는 주장, 또는 `supported`가 2개 미만인 주장은 **글에서 뺍니다**. 빼고 나서 남은 주장으로 글이 성립하지 않으면 다른 후보로 돌아가 3단계부터 다시 합니다(최대 1회). 그래도 안 되면 "발행할 주제 없음"으로 끝냅니다.
- 검증자가 찾은 새 출처 가운데 글에 쓰는 것은 `sources`에 추가합니다.

## 6. 글 작성
`work/$RUN/body.md`(Markdown 본문)와 `work/$RUN/post.json`(메타데이터)을 씁니다.

### 문체: 리포트가 아니라 매거진 기사
독자는 세 부류입니다: 피부미용에 관심 많은 사람, 피부과 의사, 이 분야에 관심이 없던 사람. 셋 모두 끝까지 재미있게 읽을 수 있어야 합니다.
- **도입**: 첫 문단은 장면·질문·의외의 사실로 시작해 독자를 끌어들입니다. "~에 대해 알아보겠습니다" 같은 보고서식 문장은 쓰지 않습니다.
  - 예: "요즘 화장품 매대에서 '연어'라는 단어를 보고 고개를 갸웃한 적이 있다면…"
- **어조**: 친근한 해요체 또는 담백한 평서체 하나로 통일합니다. 짧은 문장과 긴 문장을 섞어 리듬을 만듭니다.
- **용어**: 전문 용어는 처음 나올 때 한 줄로 쉽게 풀어 줍니다. 비유를 쓰되, 의사가 읽어도 틀린 데가 없을 만큼 정확해야 합니다.
- **숫자**: 정말 중요한 숫자 2~4개만 골라 의미를 풀어 씁니다. 숫자를 나열하지 않습니다.
- **출처**: "미국 국립의학도서관 논문 데이터베이스를 보면", "올리브영 발표에 따르면"처럼 문장 속에서 자연스럽게 밝힙니다. `[1]` 같은 번호는 쓰지 않습니다. 전체 목록은 레이아웃이 글 끝에 접어서 붙입니다.
- **구성**: 소제목 3~5개, 본문 2,000~3,500자.
  - 소제목은 "데이터로 본 실제 모습" 같은 보고서식이 아니라 궁금증을 부르는 문장형으로 씁니다. 예: "연어에서 식물로, 원료가 바뀐다", "바르는 것과 맞는 것은 다르다"
  - 흐름: 왜 다들 이 얘기를 하나 → 실제로 얼마나 뜨거운가 → 과학은 어디까지 말해 주나 → 그래서 독자는 무엇을 기억하면 되나
  - 강조하고 싶은 한 문장은 `>` 인용 블록으로 한 번 정도 씁니다.
- **근거 수준 서술은 본문에 넣지 않습니다.** post.json의 `trust_note`에 따로 씁니다(아래 참고).
- 검증 과정(몇 명이 교차확인했는지, 판정 결과)은 본문과 trust_note 어디에도 쓰지 않습니다. 그 기록은 post.json에만 남습니다.

### 지켜야 할 것 (문체와 무관하게 항상)
- SNS에만 근거한 내용은 "SNS에서 ~라는 이야기가 많다"처럼 화제성으로만 쓰고, 효능 사실처럼 쓰지 않습니다.
- 이미지, 전후 비교, 후기 인용, 병원·의사 이름, 가격, 예약 유도는 넣지 않습니다.
- 재미를 위해 효과를 부풀리지 않습니다. 의료광고 금지 표현은 기사 문체에서도 똑같이 금지입니다.
- 면책 문구는 레이아웃이 자동으로 붙입니다.

### post.json의 독자용 필드
- `title`: 매거진 기사 제목처럼 궁금증을 부르는 문장. "~ 분석", "~ 데이터와 근거로 다시 보기" 같은 보고서식 제목은 쓰지 않습니다(예: "연어 DNA는 어떻게 화장대에 올랐나").
- `dek`: 제목 아래에 붙는 부제 한 문장(10~90자). 호기심을 부르되 과장하지 않습니다.
- `trust_note`: 글 끝 "이 이야기, 얼마나 믿을 만할까" 상자에 들어갈 2~3문장(60~320자). 아래 내용을 일상어로 씁니다.
  - 어디까지가 탄탄한 사실인지(예: 관심이 커진 것은 검색·판매 숫자로 분명함)
  - 어디부터 아직 지켜봐야 하는지(예: 바르는 제품의 효과는 연구가 부족함)
  - 검증자, 교차확인, 판정 같은 절차 용어는 쓰지 않습니다.

post.json:
```json
{
  "title": "...", "slug": "짧은-영문(1~3단어, 글 주소가 됨: 예 pdrn, exosome, skin-booster)",
  "dek": "부제 한 문장",
  "categories": ["리프팅|시술|성분|트렌드 중 1~2개"],
  "evidence_level": "objective | mixed | cross_verified_sns",
  "evidence_summary": "근거 수준을 한두 문장으로 (내부 기록용, 화면에 나오지 않음)",
  "trust_note": "독자용 신뢰도 단락 2~3문장",
  "claims": [{"text":"...","evidence":"objective","source_ids":[1]},
             {"text":"...","evidence":"sns","source_ids":[4],"verdicts":{"sources":"supported","skeptic":"supported","codex":"partial"}}],
  "sources": [{"title":"...","url":"https://...","type":"paper","publisher":"...","accessed":"YYYY-MM-DD"}],
  "verification": {
    "method": "객관 지표가 없는 주장 N개를 독립 검증자 3명이 서로의 결과를 보지 않고 따로 확인함 (2명 이상 지지, 반박 0건이면 통과)",
    "verifiers": [
      {"name":"sources","perspective":"독립 출처(언론·업계·공공기관) 교차확인","verdict":"supported","notes":"요지 한 문장"},
      {"name":"skeptic","perspective":"의학 근거·안전성·과장 여부(논문·규제기관)","verdict":"partial","notes":"..."},
      {"name":"codex","perspective":"외부 모델(OpenAI Codex) 독립 웹 검색 확인","verdict":"supported","notes":"..."}
    ]
  }
}
```
(모든 주장이 objective라면 verifiers는 비워 두고, method에 "객관 데이터로 직접 확인"이라고 씁니다.) 검증자별 `verdict`는 그 검증자의 전체 판정입니다(대부분이 supported면 supported).

### 이미지 (OpenAI Codex의 ChatGPT 이미지 생성)
이미지는 반드시 ChatGPT(Codex의 이미지 생성)에 맡겨 만들고, 결과 파일을 받아 글에 넣습니다. 다른 방법으로 이미지를 그리거나 웹에서 가져오지 않습니다. 글마다 2~4장을 넣습니다. 대표 이미지(`hero`) 1장과 본문 이미지 1~3장입니다.
1. 본문에서 이미지가 이해를 돕거나 분위기를 바꿔 줄 자리(보통 소제목 바로 아래)에 `[[img:<id>]]`를 한 줄로 넣습니다. id는 영문 소문자이고, `hero`는 본문에 넣지 않습니다(제목 아래에 자동으로 붙음).
2. `work/$RUN/images.json`을 씁니다.
   ```json
   [{"id":"hero","prompt":"영문 장면 묘사","alt":"이미지를 설명하는 한국어 대체 텍스트","caption":"짧은 한국어 캡션"},
    {"id":"lab","prompt":"...","alt":"...","caption":"..."}]
   ```
   - prompt에는 화면에 **있는 것만** 영어로 구체적으로 묘사합니다. 소재·구도·질감을 씁니다. 예: "a glass serum dropper releasing a single drop onto a smooth stone, dried salmon-pink rose petals"
   - 금지 사항은 스크립트가 공통으로 붙이므로 prompt에 "no people" 같은 부정문을 쓰지 않습니다. 금지어 검사에 걸립니다.
   - 사람, 얼굴, 피부 변화, 전후 비교, 시술 장면, 병원, 로고와 글자는 넣지 않습니다. 성분, 원료, 도구, 과학적 개념을 비유적인 정물이나 일러스트로 표현합니다.
   - 캡션은 사실을 단정하지 않는 설명형으로 씁니다. 예: "연어 DNA에서 시작된 성분이 화장대로 옮겨 왔다". "AI 생성 이미지" 표시는 자동으로 붙습니다.
3. 이미지를 만듭니다. 몇 분 걸리므로 timeout은 600000으로 둡니다.
   ```bash
   bash pipeline/bin/gen_images.sh pipeline/work/$RUN <slug>
   ```
   - `IMAGES_OK`가 나오면 생성된 jpg를 Read로 열어 봅니다.
   - 금지 요소(글자·로고, 사람·얼굴, 전후 비교 느낌)가 보이면 그 이미지의 prompt를 고쳐 한 번만 다시 만듭니다. 다시 만들 때는 images.json에 그 이미지만 남겨 실행합니다.
   - `IMAGES_INCOMPLETE`면 한 번 더 실행합니다. 그래도 실패하면 빠진 이미지는 빼고 진행합니다. hero가 없으면 빌드가 막히니, 이 경우 review로 남깁니다.

## 7. 빌드·점검·발행
```bash
cd /Users/sungminjang/클로드/skin-blog
python3 pipeline/bin/build_post.py pipeline/work/$RUN
```
- `"outcome":"ready"` (exit 0): 발행 정책이 **검증 통과 시 자동 발행**이므로 바로 `bash pipeline/bin/publish.sh "새 글: <제목>"`을 실행합니다.
- `"outcome":"review"` (exit 2): 발행이 보류된 것입니다. **그대로 두지 말고 아래 '7-1. 보류 글 검수·재발행'을 반드시 진행합니다.**
- `"outcome":"invalid"` (exit 1): 입력을 고쳐 다시 실행합니다.
- `compliance_warnings`는 발행을 막지 않지만 실행 로그에 적습니다.

### 7-1. 보류 글 검수·재발행 (발행인의 상시 지시: 보류되면 검수하고 다시 발행)
1. `pipeline/review_queue/<이름>/REVIEW.json`을 읽고, 걸린 항목마다 원인을 찾습니다.
   - `compliance_blocks`: `pipeline/bin/build_post.py`의 BLOCK 규칙(정규식)으로 work 디렉터리의 `body.md`와 `post.json`을 grep해 **어느 문장의 어느 글자에 걸렸는지** 찾습니다.
     - 무해한 단어 속에 걸린 오탐이면(예: '장기적으로' 속 '기적') 그 문장을 같은 뜻의 다른 표현으로 바꿉니다. 오탐 내용은 보고에 적습니다. 규칙 파일은 자동 실행 중에 고치지 않습니다.
     - 진짜 금지 표현이면 효과 보장·과장·홍보가 없는 표현으로 다시 씁니다. 해당 문장을 지워도 됩니다.
   - `verification_errors`: 검증 규칙을 통과하지 못한 주장은 **본문과 claims에서 빼거나**, 지지된 범위까지만 말하도록 낮춥니다. 검증자 판정이나 verification 기록은 절대 바꾸지 않습니다. 주장을 바꿨다면 evidence_level·trust_note도 그에 맞게 고칩니다.
   - 이미지 문제면 `gen_images.sh`를 다시 실행하거나 문제 이미지를 뺍니다(hero는 필수).
2. 고친 문장들을 다시 읽어 6단계 '지켜야 할 것'과 매거진 문체에 맞는지 스스로 검수합니다.
3. `python3 pipeline/bin/build_post.py pipeline/work/$RUN`을 다시 실행합니다(work 디렉터리 기준으로 다시 빌드하면 됩니다). 이 과정을 **최대 3번**까지 반복합니다.
4. ready가 나오면 `rm -rf pipeline/review_queue/<이름>`으로 보류본을 지우고 평소처럼 publish.sh로 발행합니다.
5. 3번 해도 통과하지 못하면 review_queue에 둔 채 발행하지 않고, 남은 문제를 보고에 적습니다. 검사 규칙을 끄거나 우회해서 발행하지 않습니다.

발행했다면 `pipeline/topics_history.txt`에 `날짜<TAB>주제<TAB>slug` 한 줄을 추가합니다. 1~3분 뒤 `curl -s -o /dev/null -w '%{http_code}'`로 글 URL(`https://pbrpbr-kr.github.io/<slug>/`)이 200인지 확인합니다. 아직 404면 2분 뒤 한 번 더 확인합니다.

## 8. 마무리 보고
(보고에 후보 4개와 총괄이 고른 이유를 한두 줄로 포함합니다.)
실행 로그를 완성하고, 마지막 메시지에 다음을 적습니다: 고른 주제, 근거 수준, 검증자별 판정, 결과(발행 URL / 검토 대기 경로 / 발행할 주제 없음), 건너뛴 수집 소스와 그 이유.
