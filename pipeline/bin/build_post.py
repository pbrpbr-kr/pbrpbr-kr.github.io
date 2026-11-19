#!/usr/bin/env python3
"""작업 폴더(post.json + body.md)를 검증하고 Jekyll 글로 만든다.

사용: python3 build_post.py <work_dir> [--dry-run]

1) 스키마 점검   2) 교차검증 규칙 점검(이 스크립트가 직접 판정)   3) 의료광고 표현 점검
결과:
  - 모두 통과  → _posts/YYYY-MM-DD-slug.md 생성, exit 0
  - 하나라도 걸림 → pipeline/review_queue/YYYY-MM-DD-slug/ 로 옮기고 사유 기록, exit 2
  - 입력 오류   → exit 1
마지막 줄에 JSON 결과를 출력한다.
"""
import datetime
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KST = datetime.timezone(datetime.timedelta(hours=9))

EVIDENCE_LEVELS = {"objective", "mixed", "cross_verified_sns"}
OBJECTIVE_TYPES = {"paper", "search_trend", "sales", "procedure_stats", "regulatory", "market_report"}
SOURCE_TYPES = OBJECTIVE_TYPES | {"news", "sns", "influencer", "industry", "other"}
VERDICTS = {"supported": "지지", "partial": "부분 지지", "contradicted": "반박", "unverifiable": "확인 불가"}
MIN_VERIFIERS = 2          # SNS 주장마다 '지지' 최소 수
REQUIRED_VERIFIERS = 3     # SNS 주장이 있으면 이만큼의 독립 검증자 결과가 있어야 함

# --- 의료광고 표현 점검 (의료법 제56조 취지) ---------------------------------
# (패턴, 사유). 본문·제목·요약·주장 텍스트에 적용.
BLOCK = [
    (r"100\s*%", "효과 보장 표현(100%)"),
    (r"(효과|결과)(를|가|를\s*)?\s*보장", "효과 보장 표현"),
    (r"보장(합니다|된다|됩니다|해\s*드)", "효과 보장 표현"),
    (r"확실(한|히)\s*(효과|개선|결과)", "효과 단정 표현"),
    (r"부작용(이|은|도)?\s*(전혀\s*)?없(는|다|습니다|어요|음)", "부작용 부정 표현"),
    (r"(통증|붓기|멍)(이|은|도)?\s*(전혀\s*)?없(는|다|습니다|어요|음)", "부작용 부정 표현"),
    (r"(무통|무 통증)", "부작용 부정 표현"),
    (r"(영구적|평생)\s*(효과|유지)", "효과 단정 표현"),
    (r"(완벽(한|하게|히)|기적|마법\s*같은)", "과장 표현"),
    (r"(최고의|최초의|유일한|국내\s*1위|No\.?\s*1|넘버원)", "최상급·비교 우위 표현"),
    (r"(전\s*[·/&]?\s*후\s*(사진|비교)|비포\s*[&/]?\s*애프터|before\s*[&/]?\s*after)", "전후 비교"),
    (r"(시술|치료)\s*(전후|전과\s*후)\s*(비교|사진|변화)", "전후 비교"),
    (r"[가-힣A-Za-z0-9]{2,}(의원|클리닉|성형외과의원|피부과의원)(?![가-힣])", "특정 의료기관 언급"),
    (r"(원장님?|대표원장)", "특정 의료인 언급"),
    (r"(할인|이벤트\s*가|특가|\d[\d,]*\s*만?\s*원(부터|대|에))", "가격·할인 정보"),
    (r"(예약|상담)\s*(문의|하세요|바로가기)", "유인·알선 표현"),
    (r"(010|02|031)-?\d{3,4}-?\d{4}", "연락처"),
    (r"!\[|<img", "본문에 직접 넣은 이미지(이미지는 [[img:id]] 자리표시자와 images.json으로만)"),
]
# 이미지 생성 프롬프트·대체텍스트·캡션 전용 금지 요소 (프롬프트에는 화면에 '있는 것'만 쓴다)
IMAGE_BLOCK = [
    (r"\b(before|after|split[- ]screen|comparison|side[- ]by[- ]side)\b|전후|비교", "전후·비교 이미지"),
    (r"\b(face|faces|portrait|person|people|woman|women|man|men|girl|boy|model|patient|selfie)\b|얼굴|인물|환자|모델", "사람·얼굴"),
    (r"\b(clinic|hospital|doctor|dermatologist|nurse|treatment room)\b|병원|클리닉|의사|시술실", "의료기관·의료진"),
    (r"\b(logo|brand|label text|packaging|typography|text)\b|로고|브랜드|문구", "글자·로고·브랜드"),
    (r"\b(injecting|being injected|needle in skin)\b", "시술 장면"),
]

WARN = [
    (r"후기", "체험 후기 성격 표현 — 인용이면 SNS 동향 맥락인지 확인"),
    (r"(효과\s*(가|는)?\s*(뛰어|탁월|확실))", "효과 강조"),
    (r"(즉시|즉각|바로)\s*(효과|개선)", "즉각 효과 표현"),
]


def kst_now():
    return datetime.datetime.now(KST)


def yaml_scalar(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if v is None:
        return '""'
    return json.dumps(str(v), ensure_ascii=False)


def to_yaml(obj, indent=0):
    pad = "  " * indent
    lines = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)) and v:
                lines.append(f"{pad}{k}:")
                lines.append(to_yaml(v, indent + 1))
            elif isinstance(v, (dict, list)):
                lines.append(f"{pad}{k}: {'{}' if isinstance(v, dict) else '[]'}")
            else:
                lines.append(f"{pad}{k}: {yaml_scalar(v)}")
    else:
        for item in obj:
            if isinstance(item, dict):
                sub = to_yaml(item, indent + 1).splitlines()
                lines.append(f"{pad}- {sub[0].strip()}")
                lines.extend(sub[1:])
            else:
                lines.append(f"{pad}- {yaml_scalar(item)}")
    return "\n".join(lines)


def check_schema(meta, body):
    errs = []
    for k in ("title", "slug", "dek", "categories", "evidence_level", "evidence_summary", "trust_note", "claims", "sources", "verification"):
        if k not in meta:
            errs.append(f"필드 누락: {k}")
    if errs:
        return errs
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+){0,2}", meta["slug"]) or len(meta["slug"]) > 24:
        errs.append("slug는 영문 소문자 1~3단어, 24자 이내(예: pdrn, exosome, skin-booster) — 글 주소가 됨")
    elif list((ROOT / "_posts").glob(f"*-{meta['slug']}.md")):
        errs.append(f"slug '{meta['slug']}'가 이미 쓰임 → 주제를 구분하는 단어를 붙이세요(예: {meta['slug']}-vegan)")
    if meta["evidence_level"] not in EVIDENCE_LEVELS:
        errs.append(f"evidence_level은 {sorted(EVIDENCE_LEVELS)} 중 하나")
    if len(meta["sources"]) < 3:
        errs.append("출처는 3개 이상")
    for i, s in enumerate(meta["sources"], 1):
        if not str(s.get("url", "")).startswith("http"):
            errs.append(f"출처 {i}: url 누락")
        if s.get("type") not in SOURCE_TYPES:
            errs.append(f"출처 {i}: type은 {sorted(SOURCE_TYPES)} 중 하나")
    if not meta["claims"]:
        errs.append("핵심 주장(claims)이 비어 있음")
    if len(body.strip()) < 1500:
        errs.append("본문이 너무 짧음(1,500자 미만)")
    if re.search(r"\[\d+\]", body):
        errs.append("본문에 [n] 출처 번호를 쓰지 않음(매거진 문체, 출처는 문장 속에 자연스럽게)")
    tn = meta.get("trust_note", "")
    if not (60 <= len(tn) <= 320):
        errs.append("trust_note는 60~320자의 짧은 단락")
    if re.search(r"검증자|교차\s*검증|교차\s*확인|Codex|codex|서브에이전트|지지\s*\d|부분 지지|evidence|verdict", tn):
        errs.append("trust_note에 검증 절차·판정 용어를 쓰지 않음(독자 눈높이로 신뢰도만 서술)")
    if not (10 <= len(meta.get("dek", "")) <= 90):
        errs.append("dek(부제)은 10~90자 한 문장")
    return errs


def check_verification(meta):
    """주장별 근거 규칙. 이 함수의 판정이 최종이다(입력의 status는 신뢰하지 않음)."""
    errs = []
    srcs = meta["sources"]
    verifiers = {v.get("name") for v in meta["verification"].get("verifiers", [])}
    perspectives = {v.get("perspective") for v in meta["verification"].get("verifiers", [])}
    kinds = set()
    for i, c in enumerate(meta["claims"], 1):
        ids = c.get("source_ids", [])
        if not ids or any(not (1 <= n <= len(srcs)) for n in ids):
            errs.append(f"주장 {i}: source_ids가 출처 번호를 가리키지 않음")
            continue
        cited_types = {srcs[n - 1].get("type") for n in ids}
        ev = c.get("evidence")
        kinds.add(ev)
        if ev == "objective":
            if not cited_types & OBJECTIVE_TYPES:
                errs.append(f"주장 {i}: 'objective'인데 객관 데이터 출처가 없음")
            c["verdict"] = "객관 데이터로 확인"
        elif ev == "sns":
            vv = c.get("verdicts", {})
            bad = [n for n, v in vv.items() if v not in VERDICTS]
            if bad:
                errs.append(f"주장 {i}: 판정값 오류 {bad}")
                continue
            sup = sum(1 for v in vv.values() if v == "supported")
            con = sum(1 for v in vv.values() if v == "contradicted")
            if len(vv) < REQUIRED_VERIFIERS:
                errs.append(f"주장 {i}: 독립 검증 결과가 {len(vv)}개(필요 {REQUIRED_VERIFIERS})")
            elif con > 0:
                errs.append(f"주장 {i}: 반박한 검증자가 있음 → 글에서 빼야 함")
            elif sup < MIN_VERIFIERS:
                errs.append(f"주장 {i}: '지지' {sup}개(필요 {MIN_VERIFIERS})")
            c["verdict"] = " · ".join(f"{n} {VERDICTS[v]}" for n, v in vv.items())
        else:
            errs.append(f"주장 {i}: evidence는 objective 또는 sns")
    if "sns" in kinds and (len(verifiers) < REQUIRED_VERIFIERS or len(perspectives) < REQUIRED_VERIFIERS):
        errs.append("SNS 주장이 있는데 서로 다른 관점의 검증자가 3명 미만")
    expected = "objective" if kinds == {"objective"} else ("cross_verified_sns" if kinds == {"sns"} else "mixed")
    if meta["evidence_level"] != expected:
        errs.append(f"evidence_level이 주장 구성과 다름(기대값 {expected})")
    return errs


def load_images(work):
    f = work / "images.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


def check_images(meta, body, images):
    errs = []
    ids = [im.get("id") for im in images]
    if "hero" not in ids:
        errs.append("대표 이미지(id: hero)가 없음")
    if not (2 <= len(images) <= 4):
        errs.append("이미지는 대표 이미지 포함 2~4장")
    used = set(re.findall(r"\[\[img:([a-z0-9-]+)\]\]", body))
    for im in images:
        i = im.get("id", "")
        if not re.fullmatch(r"[a-z0-9-]+", i):
            errs.append(f"이미지 id 형식 오류: {i}")
            continue
        if len(im.get("alt", "")) < 8 or not im.get("caption"):
            errs.append(f"이미지 {i}: alt(8자 이상)와 caption 필요")
        if not (ROOT / "assets" / "img" / "posts" / meta["slug"] / f"{i}.jpg").exists():
            errs.append(f"이미지 파일 없음: assets/img/posts/{meta['slug']}/{i}.jpg (gen_images.sh 먼저)")
        if i != "hero" and i not in used:
            errs.append(f"이미지 {i}가 본문에서 쓰이지 않음([[img:{i}]] 필요)")
    for u in used - set(ids):
        errs.append(f"본문의 [[img:{u}]]에 해당하는 이미지가 없음")
    if "hero" in used:
        errs.append("hero는 제목 아래에 자동으로 들어가므로 본문에 넣지 않음")
    return errs


def check_image_compliance(images):
    out = []
    for im in images:
        text = " ".join([im.get("prompt", ""), im.get("alt", ""), im.get("caption", "")])
        for pat, why in IMAGE_BLOCK:
            for m in re.finditer(pat, text, flags=re.I):
                out.append(f"이미지 {im.get('id')} — {why}: “{m.group(0)}”")
    return out


def render_images(body, images, slug):
    by = {im["id"]: im for im in images}
    def rep(m):
        im = by.get(m.group(1))
        if not im:
            return m.group(0)
        return f"![{im['alt']}](/assets/img/posts/{slug}/{im['id']}.jpg)\n*{im['caption']} · AI 생성 이미지*"
    return re.sub(r"\[\[img:([a-z0-9-]+)\]\]", rep, body)


def check_compliance(meta, body):
    text = "\n".join([meta["title"], meta["dek"], meta["trust_note"], meta["evidence_summary"], body] + [c.get("text", "") for c in meta["claims"]])
    blocks, warns = [], []
    for pat, why in BLOCK:
        for m in re.finditer(pat, text, flags=re.I):
            blocks.append(f"{why}: “{m.group(0)}”")
    for pat, why in WARN:
        for m in re.finditer(pat, text, flags=re.I):
            warns.append(f"{why}: “{m.group(0)}”")
    return sorted(set(blocks)), sorted(set(warns))


def main(work, dry=False):
    work = Path(work)
    meta = json.loads((work / "post.json").read_text(encoding="utf-8"))
    body = (work / "body.md").read_text(encoding="utf-8")
    now = kst_now()
    result = {"work_dir": str(work)}

    schema = check_schema(meta, body)
    if schema:
        result.update(outcome="invalid", errors=schema)
        print(json.dumps(result, ensure_ascii=False))
        return 1
    images = load_images(work)
    ierr = check_images(meta, body, images)
    if ierr:
        result.update(outcome="invalid", errors=ierr)
        print(json.dumps(result, ensure_ascii=False))
        return 1
    verr = check_verification(meta)
    blocks, warns = check_compliance(meta, body)
    blocks += check_image_compliance(images)
    blocks += [b for b in check_compliance(meta, " ".join(im.get("alt", "") + " " + im.get("caption", "") for im in images))[0] if b not in blocks]

    meta["verification"]["status"] = "passed" if not verr else "failed"
    meta["verification"]["checked_at"] = now.strftime("%Y-%m-%d %H:%M KST")
    for v in meta["verification"].get("verifiers", []):
        v["verdict"] = VERDICTS.get(v.get("verdict"), v.get("verdict"))
    meta["compliance"] = {"status": "통과" if not blocks else "검토 필요",
                          "checked_at": now.strftime("%Y-%m-%d %H:%M KST")}

    fm = {
        "layout": "post",
        "title": meta["title"],
        "dek": meta["dek"],
        "image": f"/assets/img/posts/{meta['slug']}/hero.jpg",
        "image_alt": next(im["alt"] for im in images if im["id"] == "hero"),
        "image_caption": next(im["caption"] for im in images if im["id"] == "hero") + " · AI 생성 이미지",
        "date": now.strftime("%Y-%m-%d %H:%M:%S +0900"),
        "categories": meta["categories"],
        "evidence_level": meta["evidence_level"],
        "evidence_summary": meta["evidence_summary"],
        "trust_note": meta["trust_note"],
        "claims": [{"text": c["text"], "evidence": c["evidence"], "verdict": c.get("verdict", "")} for c in meta["claims"]],
        "verification": meta["verification"],
        "compliance": meta["compliance"],
        "sources": meta["sources"],
    }
    doc = "---\n" + to_yaml(fm) + "\n---\n\n" + render_images(body.strip(), images, meta["slug"]) + "\n"
    name = f"{now:%Y-%m-%d}-{meta['slug']}"
    result.update(verification_errors=verr, compliance_blocks=blocks, compliance_warnings=warns)

    if verr or blocks:
        dest = ROOT / "pipeline" / "review_queue" / name
        result["outcome"] = "review"
        if not dry:
            dest.mkdir(parents=True, exist_ok=True)
            (dest / f"{name}.md").write_text(doc, encoding="utf-8")
            shutil.copy(work / "post.json", dest / "post.json")
            shutil.copy(work / "body.md", dest / "body.md")
            if (work / "images.json").exists():
                shutil.copy(work / "images.json", dest / "images.json")
            (dest / "REVIEW.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        result["path"] = str(dest)
        print(json.dumps(result, ensure_ascii=False))
        return 2

    out = ROOT / "_posts" / f"{name}.md"
    result.update(outcome="ready", path=str(out))
    if not dry:
        out.write_text(doc, encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: build_post.py <work_dir> [--dry-run]")
    sys.exit(main(sys.argv[1], "--dry-run" in sys.argv))
