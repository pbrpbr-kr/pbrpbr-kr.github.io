#!/usr/bin/env python3
"""PubMed(NCBI E-utilities, 공식 무료 API)에서 키워드별 연도별 논문 수와 최근 논문을 가져온다.

사용: python3 collect_pubmed.py "polynucleotide skin" "exosome skin" ... > pubmed.json
NCBI_API_KEY가 .env에 있으면 사용(없어도 동작, 초당 3회 제한).
"""
import datetime
import json
import sys
import time

from common import http_json, load_env

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


def esearch(term, extra=None):
    env = load_env()
    p = {"db": "pubmed", "term": term, "retmode": "json", "retmax": 5, "sort": "pub_date"}
    if env.get("NCBI_API_KEY"):
        p["api_key"] = env["NCBI_API_KEY"]
    p.update(extra or {})
    time.sleep(0.4)
    return http_json(BASE + "esearch.fcgi", p)["esearchresult"]


def summaries(ids):
    if not ids:
        return []
    time.sleep(0.4)
    r = http_json(BASE + "esummary.fcgi", {"db": "pubmed", "id": ",".join(ids), "retmode": "json"})["result"]
    out = []
    for i in ids:
        d = r.get(i, {})
        out.append({
            "pmid": i,
            "title": d.get("title"),
            "journal": d.get("fulljournalname"),
            "pubdate": d.get("pubdate"),
            "pubtype": d.get("pubtype"),
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{i}/",
        })
    return out


def main(keywords):
    year = datetime.date.today().year
    result = {"source": "PubMed E-utilities", "retrieved": datetime.date.today().isoformat(), "keywords": {}}
    for kw in keywords:
        counts = {}
        for y in range(year - 4, year + 1):
            r = esearch(kw, {"datetype": "pdat", "mindate": str(y), "maxdate": str(y), "retmax": 0})
            counts[str(y)] = int(r["count"])
        recent = esearch(kw)
        rct = esearch(kw + " AND (randomized controlled trial[pt] OR systematic review[pt] OR meta-analysis[pt])", {"retmax": 3})
        result["keywords"][kw] = {
            "counts_by_year": counts,
            "note": f"{year}년 수치는 연중 누적",
            "recent": summaries(recent["idlist"]),
            "high_level_evidence_count": int(rct["count"]),
            "high_level_recent": summaries(rct["idlist"]),
        }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: collect_pubmed.py <english keyword> [...]")
    main(sys.argv[1:])
