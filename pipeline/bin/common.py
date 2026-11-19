"""공통 유틸: .env 로드, HTTP GET/POST(JSON). 표준 라이브러리만 사용."""
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # skin-blog/
UA = "skin-trend-blog-pipeline/1.0"


def load_env():
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            if v and k.strip() not in os.environ:
                os.environ[k.strip()] = v
    return os.environ


def http_json(url, params=None, headers=None, data=None, timeout=30):
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    h = {"User-Agent": UA}
    h.update(headers or {})
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))
