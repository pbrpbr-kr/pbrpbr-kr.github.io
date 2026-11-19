#!/usr/bin/env python3
"""키가 있을 때만 동작하는 공식 API 수집기. 키가 없는 소스는 'skipped'로 표시하고 넘어간다.

사용: python3 collect_optional.py "울쎄라" "리쥬란" ... > optional.json

소스(모두 공식 API, 자격증명은 사용자가 .env에 직접 입력):
- 네이버 데이터랩 검색어 트렌드: NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
- YouTube Data API v3 (인플루언서 영상 언급량): YOUTUBE_API_KEY
- X API v2 최근 게시물 수: X_BEARER_TOKEN (유료 요금제 필요)
- Threads API 키워드 검색: THREADS_ACCESS_TOKEN
- Instagram Graph API 해시태그 검색: IG_USER_ID, IG_ACCESS_TOKEN (비즈니스/크리에이터 계정)
"""
import datetime
import json
import sys
import urllib.parse

from common import http_json, load_env

TODAY = datetime.date.today()


def naver_datalab(env, kws):
    end = TODAY
    start = end - datetime.timedelta(days=365)
    groups = [{"groupName": k, "keywords": [k]} for k in kws[:5]]
    r = http_json(
        "https://openapi.naver.com/v1/datalab/search",
        headers={"X-Naver-Client-Id": env["NAVER_CLIENT_ID"], "X-Naver-Client-Secret": env["NAVER_CLIENT_SECRET"]},
        data={"startDate": start.isoformat(), "endDate": end.isoformat(), "timeUnit": "month", "keywordGroups": groups},
    )
    return {"note": "상대 검색량(기간 내 최대=100)", "results": r.get("results")}


def youtube(env, kws):
    after = (TODAY - datetime.timedelta(days=30)).isoformat() + "T00:00:00Z"
    out = {}
    for k in kws:
        r = http_json("https://www.googleapis.com/youtube/v3/search", {
            "part": "snippet", "q": k, "type": "video", "publishedAfter": after,
            "regionCode": "KR", "relevanceLanguage": "ko", "maxResults": 10, "order": "viewCount",
            "key": env["YOUTUBE_API_KEY"],
        })
        out[k] = {
            "total_results_estimate_30d": r.get("pageInfo", {}).get("totalResults"),
            "top_videos": [{"title": i["snippet"]["title"], "channel": i["snippet"]["channelTitle"],
                            "url": "https://www.youtube.com/watch?v=" + i["id"]["videoId"],
                            "published": i["snippet"]["publishedAt"]} for i in r.get("items", [])],
        }
    return out


def x_counts(env, kws):
    out = {}
    for k in kws:
        r = http_json("https://api.x.com/2/tweets/counts/recent",
                      {"query": f"{k} -is:retweet", "granularity": "day"},
                      headers={"Authorization": "Bearer " + env["X_BEARER_TOKEN"]})
        out[k] = {"total_7d": r.get("meta", {}).get("total_tweet_count")}
    return out


def threads(env, kws):
    out = {}
    for k in kws:
        r = http_json("https://graph.threads.net/v1.0/keyword_search",
                      {"q": k, "search_type": "TOP", "fields": "id,text,timestamp,permalink",
                       "access_token": env["THREADS_ACCESS_TOKEN"]})
        out[k] = {"top_posts": [{"text": (p.get("text") or "")[:200], "url": p.get("permalink"),
                                 "timestamp": p.get("timestamp")} for p in r.get("data", [])[:10]]}
    return out


def instagram(env, kws):
    out = {}
    for k in kws:
        tag = k.replace(" ", "")
        h = http_json("https://graph.facebook.com/v21.0/ig_hashtag_search",
                      {"user_id": env["IG_USER_ID"], "q": tag, "access_token": env["IG_ACCESS_TOKEN"]})
        if not h.get("data"):
            out[k] = {"hashtag": tag, "found": False}
            continue
        hid = h["data"][0]["id"]
        m = http_json(f"https://graph.facebook.com/v21.0/{hid}/recent_media",
                      {"user_id": env["IG_USER_ID"], "fields": "permalink,timestamp,like_count,comments_count",
                       "access_token": env["IG_ACCESS_TOKEN"]})
        out[k] = {"hashtag": tag, "recent_media_24h_sample": len(m.get("data", [])),
                  "samples": m.get("data", [])[:5]}
    return out


SOURCES = [
    ("naver_datalab", ["NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET"], naver_datalab),
    ("youtube", ["YOUTUBE_API_KEY"], youtube),
    ("x", ["X_BEARER_TOKEN"], x_counts),
    ("threads", ["THREADS_ACCESS_TOKEN"], threads),
    ("instagram", ["IG_USER_ID", "IG_ACCESS_TOKEN"], instagram),
]


def main(kws):
    env = load_env()
    result = {"retrieved": TODAY.isoformat(), "sources": {}}
    for name, keys, fn in SOURCES:
        if not all(env.get(k) for k in keys):
            result["sources"][name] = {"status": "skipped", "reason": "자격증명 없음: " + ", ".join(keys)}
            continue
        try:
            result["sources"][name] = {"status": "ok", "data": fn(env, kws)}
        except Exception as e:  # 한 소스 실패가 전체를 막지 않게
            result["sources"][name] = {"status": "error", "error": f"{type(e).__name__}: {e}"}
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: collect_optional.py <keyword> [...]")
    main(sys.argv[1:])
