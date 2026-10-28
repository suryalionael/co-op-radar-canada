"""Check which job-board platforms a candidate board token exists on.

Used to build and re-verify config/employers.yaml. For each token it tries
Greenhouse, Lever and Ashby once, politely, and prints one JSON line per hit:
platform, token, board name (Greenhouse only), total jobs, and how many jobs
have a Canadian-looking location (a sanity check that the token belongs to the
company we think it does, not a same-named company elsewhere).

Usage:
    python scripts/check_board_tokens.py tokens.txt > hits.jsonl

tokens.txt has one token per line; blank lines and lines starting with # are skipped.
Standard library only, so it runs before the project has any dependencies.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Any

USER_AGENT = "co-op-radar-canada/0.1 (student project; board token check)"
SLEEP_SECONDS = 0.3  # pause between requests to the same host

# Place names match in any case; province codes only in capitals, so "on" or "ab"
# inside ordinary words never match.
CANADA_NAMES = re.compile(
    r"\b(canada|ontario|quebec|québec|british columbia|alberta|manitoba|saskatchewan|"
    r"nova scotia|new brunswick|newfoundland|prince edward island|"
    r"toronto|montreal|montréal|vancouver|calgary|edmonton|ottawa|waterloo|kitchener|"
    r"halifax|winnipeg|victoria|mississauga|markham|burnaby|quebec city)\b",
    re.IGNORECASE,
)
CANADA_CODES = re.compile(r"\b(ON|BC|AB|QC|MB|SK|NS|NB)\b")


def is_canadian(location: str) -> bool:
    return bool(CANADA_NAMES.search(location) or CANADA_CODES.search(location))


def get_json(url: str) -> Any:
    """Return parsed JSON, or None on 404 or any error."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None


def check_greenhouse(token: str) -> dict[str, Any] | None:
    board = get_json(f"https://boards-api.greenhouse.io/v1/boards/{token}")
    if not isinstance(board, dict) or "name" not in board:
        return None
    jobs = get_json(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs")
    jobs = jobs.get("jobs", []) if isinstance(jobs, dict) else []
    locations = [(j.get("location") or {}).get("name", "") for j in jobs]
    return {"board_name": board["name"], "jobs": len(jobs), "locations": locations}


def check_lever(token: str) -> dict[str, Any] | None:
    jobs = get_json(f"https://api.lever.co/v0/postings/{token}?mode=json")
    if not isinstance(jobs, list):
        return None
    locations = [
        " / ".join(
            [(j.get("categories") or {}).get("location") or ""]
            + ((j.get("categories") or {}).get("allLocations") or [])
        )
        for j in jobs
    ]
    return {"board_name": None, "jobs": len(jobs), "locations": locations}


def check_ashby(token: str) -> dict[str, Any] | None:
    data = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{token}")
    if not isinstance(data, dict) or "jobs" not in data:
        return None
    jobs = data["jobs"]
    locations = [
        " / ".join([j.get("location") or ""] + [s.get("location") or "" for s in j.get("secondaryLocations") or []])
        for j in jobs
    ]
    return {"board_name": None, "jobs": len(jobs), "locations": locations}


CHECKERS = {"greenhouse": check_greenhouse, "lever": check_lever, "ashby": check_ashby}


def run_platform(platform: str, tokens: list[str]) -> list[dict[str, Any]]:
    """Check every token on one platform, sequentially, sleeping between requests."""
    hits = []
    for token in tokens:
        result = CHECKERS[platform](token)
        if result is not None:
            canadian = sum(1 for loc in result.pop("locations") if is_canadian(loc))
            hits.append({"platform": platform, "token": token, **result, "canada_jobs": canadian})
        time.sleep(SLEEP_SECONDS)
    return hits


def main() -> None:
    with open(sys.argv[1], encoding="utf-8") as f:
        tokens = [t.strip() for t in f if t.strip() and not t.startswith("#")]
    # One thread per platform: requests to the same host stay sequential.
    with ThreadPoolExecutor(max_workers=len(CHECKERS)) as pool:
        results = pool.map(lambda p: run_platform(p, tokens), CHECKERS)
    for platform_hits in results:
        for hit in platform_hits:
            print(json.dumps(hit))


if __name__ == "__main__":
    main()
