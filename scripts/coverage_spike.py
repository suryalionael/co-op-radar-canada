"""Phase 0 coverage spike: how many Canadian student postings do the seed boards carry?

Fetches every board in config/employers.yaml once, politely, and applies the
counting rules written down in docs/decisions/0001-coverage-thresholds.md
before any results existed. Those rules, in short:

- A board counts only if its fetch returned HTTP 200 with a parseable job list.
- A posting is "in Canada" if its *location fields* (never the description)
  mention Canada, a province or territory, or a Canadian city. "Remote" alone
  does not count.
- A posting is a "student role" if its title contains one of the ADR's words
  as a whole word: intern, internship, co-op/coop/co op, student, summer,
  stagiaire, stage (plural "s" allowed, so "Interns" matches but "Internal"
  does not).
- Each posting is counted once, keyed on (source, board_token, job_id).

Also reported, outside the headline number: student postings whose location is
only "Remote", how many counted postings mention a term or a duration, and the
bytes each board would take after the loose Canada filter (for ADR 0002).

This is a throwaway measuring stick, not the v1 extractors. Re-run it monthly;
each run is saved under data/coverage/ for the v3 coverage chart.

Usage:
    python scripts/coverage_spike.py                     # all boards, save results
    python scripts/coverage_spike.py --only cohere,d2l   # quick check, nothing saved
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

USER_AGENT = (
    "co-op-radar-canada/0.1 (student project; coverage check; +https://github.com/suryalionael/co-op-radar-canada)"
)
SLEEP_SECONDS = 1.0  # pause between requests to the same host
TIMEOUT_SECONDS = 30
MIN_RESPONDING_BOARDS = 100  # ADR 0001 validity rule

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EMPLOYERS = ROOT / "config" / "employers.yaml"
DEFAULT_OUT_DIR = ROOT / "data" / "coverage"

# --- Location rules (ADR 0001, rule 2) ------------------------------------------

PROVINCE_NAMES = (
    "ontario",
    "quebec",
    "québec",
    "british columbia",
    "alberta",
    "manitoba",
    "saskatchewan",
    "nova scotia",
    "new brunswick",
    "newfoundland",
    "labrador",
    "prince edward island",
    "yukon",
    "northwest territories",
    "nunavut",
)
# Cities that are unambiguous enough to stand alone. Left out on purpose:
# London (UK), Victoria (Australia), Hamilton (NZ, Bermuda), Kingston (Jamaica),
# Windsor (UK), Richmond (US). Those still match when the province is named.
CANADIAN_CITIES = (
    "toronto",
    "montreal",
    "montréal",
    "vancouver",
    "calgary",
    "edmonton",
    "ottawa",
    "waterloo",
    "kitchener",
    "cambridge, on",
    "guelph",
    "mississauga",
    "brampton",
    "markham",
    "vaughan",
    "oakville",
    "burlington",
    "richmond hill",
    "north york",
    "scarborough",
    "etobicoke",
    "gatineau",
    "laval",
    "longueuil",
    "quebec city",
    "québec city",
    "sherbrooke",
    "trois-rivières",
    "burnaby",
    "surrey, bc",
    "kelowna",
    "nanaimo",
    "halifax",
    "dartmouth",
    "moncton",
    "fredericton",
    "saint john",
    "st. john's",
    "charlottetown",
    "winnipeg",
    "regina",
    "saskatoon",
    "lethbridge",
    "red deer",
    "whitehorse",
    "yellowknife",
    "iqaluit",
)
CANADA_NAMES = re.compile(
    r"\b(?:canada|" + "|".join(re.escape(n) for n in PROVINCE_NAMES + CANADIAN_CITIES) + r")\b",
    re.IGNORECASE,
)
# Two-letter codes count only in a location context: capitals, after a comma, dash,
# slash, parenthesis or the start, and before the end or one of those. So
# "Toronto, ON", "Remote - BC" and "ON, Canada" match; "Turn ON" and "on site" do not.
PROVINCE_CODES = ("ON", "QC", "BC", "AB", "MB", "SK", "NS", "NB", "NL", "PE", "YT", "NT", "NU")
CANADA_CODES = re.compile(r"(?:^|[,\-–/(|]\s*)(?:" + "|".join(PROVINCE_CODES) + r")(?=\s*(?:$|[,\-–/)|;]))")
REMOTE = re.compile(r"\bremote\b", re.IGNORECASE)
# What a "remote with no country" location may contain besides the word remote.
REMOTE_FILLER = re.compile(r"\b(?:remote|anywhere|worldwide|global|first|only|fully)\b|[^a-z]+", re.IGNORECASE)


def is_canadian_location(location: str) -> bool:
    return bool(CANADA_NAMES.search(location) or CANADA_CODES.search(location))


def is_remote_no_country(location: str) -> bool:
    """True for "Remote", "Remote - Anywhere" and the like: remote, and nothing else named."""
    return bool(REMOTE.search(location)) and not REMOTE_FILLER.sub("", location).strip()


# --- Student title rule (ADR 0001, rule 3) --------------------------------------

STUDENT_TITLE = re.compile(
    r"\b(?:interns?|internships?|co[-‐‑ ]?ops?|students?|summer|stagiaires?|stages?)\b",
    re.IGNORECASE,
)


def is_student_title(title: str) -> bool:
    return bool(STUDENT_TITLE.search(title))


# --- Term and duration mentions (reported separately, quick regex) -------------

SEASON = r"(?:summer|fall|autumn|winter|spring|été|automne|hiver|printemps)"
YEAR = r"20\d\d"
TERM_MENTION = re.compile(
    rf"\b{SEASON}\s*(?:term\s*|of\s+)?[,'’-]?\s*(?:{YEAR}|'\d\d)\b|\b{YEAR}\s+{SEASON}\b",
    re.IGNORECASE,
)
NUMBER_WORDS = (
    "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    "thirteen|fourteen|fifteen|sixteen|eighteen|twenty|twenty-four"
)
DURATION_MENTION = re.compile(
    rf"\b(?:\d{{1,2}}|{NUMBER_WORDS})(?:\s*(?:,|or|to|-|–)\s*(?:\d{{1,2}}|{NUMBER_WORDS}))*"
    r"[\s-]*(?:months?|weeks?|mois|semaines)\b",
    re.IGNORECASE,
)


def first_match(pattern: re.Pattern[str], *texts: str) -> str | None:
    for text in texts:
        m = pattern.search(text)
        if m:
            return m.group(0)
    return None


# --- Normalizing each platform's job list ---------------------------------------

TAG = re.compile(r"<[^>]+>")
SPACE = re.compile(r"\s+")


def html_to_text(raw: str) -> str:
    # Greenhouse escapes its HTML once (&lt;p&gt;), so unescape, strip tags, unescape again.
    text = TAG.sub(" ", html.unescape(raw or ""))
    return SPACE.sub(" ", html.unescape(text)).strip()


@dataclass
class Job:
    job_id: str
    title: str
    location: str  # every location field joined with " / "
    description: str  # plain text
    url: str
    raw: dict[str, Any] = field(repr=False)


def _join(parts: list[str | None]) -> str:
    seen: list[str] = []
    for p in parts:
        p = (p or "").strip()
        if p and p not in seen:
            seen.append(p)
    return " / ".join(seen)


def normalize_greenhouse(payload: Any) -> list[Job]:
    jobs = []
    for j in payload["jobs"]:
        offices = j.get("offices") or []
        location = _join(
            [(j.get("location") or {}).get("name")]
            + [o.get("location") for o in offices]
            + [o.get("name") for o in offices]
        )
        jobs.append(
            Job(
                job_id=str(j["id"]),
                title=j.get("title") or "",
                location=location,
                description=html_to_text(j.get("content") or ""),
                url=j.get("absolute_url") or "",
                raw=j,
            )
        )
    return jobs


def normalize_lever(payload: Any) -> list[Job]:
    jobs = []
    for j in payload:
        cats = j.get("categories") or {}
        # Lever's structured country code is part of the location, not the description.
        country = "Canada" if (j.get("country") or "").upper() == "CA" else j.get("country")
        location = _join([cats.get("location"), *(cats.get("allLocations") or []), country])
        lists = " ".join(f"{x.get('text', '')} {html_to_text(x.get('content', ''))}" for x in j.get("lists") or [])
        description = " ".join(
            [
                j.get("descriptionPlain") or html_to_text(j.get("description") or ""),
                lists,
                j.get("additionalPlain") or "",
            ]
        )
        jobs.append(
            Job(
                job_id=str(j["id"]),
                title=j.get("text") or "",
                location=location,
                description=SPACE.sub(" ", description).strip(),
                url=j.get("hostedUrl") or "",
                raw=j,
            )
        )
    return jobs


def normalize_ashby(payload: Any) -> list[Job]:
    jobs = []
    for j in payload["jobs"]:
        address = (j.get("address") or {}).get("postalAddress") or {}
        secondary = [s.get("location") for s in j.get("secondaryLocations") or []]
        location = _join([j.get("location"), *secondary, address.get("addressRegion"), address.get("addressCountry")])
        jobs.append(
            Job(
                job_id=str(j.get("id") or j.get("jobUrl")),
                title=j.get("title") or "",
                location=location,
                description=j.get("descriptionPlain") or html_to_text(j.get("descriptionHtml") or ""),
                url=j.get("jobUrl") or "",
                raw=j,
            )
        )
    return jobs


def board_url(board_type: str, token: str) -> str:
    return {
        "greenhouse": f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true",
        "lever": f"https://api.lever.co/v0/postings/{token}?mode=json",
        "ashby": f"https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true",
    }[board_type]


NORMALIZERS = {"greenhouse": normalize_greenhouse, "lever": normalize_lever, "ashby": normalize_ashby}


# --- Per-board measurement ------------------------------------------------------


@dataclass
class BoardResult:
    employer_id: str
    board_type: str
    board_token: str
    ok: bool
    error: str | None = None
    total: int = 0
    canada: int = 0
    canada_student: int = 0
    remote_student_no_country: int = 0
    canada_student_with_term: int = 0
    canada_student_with_duration: int = 0
    loose_filter_kept: int = 0
    loose_filter_bytes: int = 0  # JSON bytes of the kept postings, descriptions included
    loose_filter_gzip_bytes: int = 0
    student_postings: list[dict[str, Any]] = field(default_factory=list)


def passes_loose_filter(job: Job) -> bool:
    """Brief section 4.1: the deliberately broad filter used at fetch time in v1."""
    text = f"{job.location} {job.title} {job.description}"
    return is_canadian_location(text) or bool(REMOTE.search(text))


def measure_board(employer: dict[str, Any], payload: Any) -> BoardResult:
    """Apply the ADR 0001 counting rules to one board's parsed response."""
    board_type, token = employer["board_type"], employer["board_token"]
    result = BoardResult(employer["id"], board_type, token, ok=True)
    jobs = NORMALIZERS[board_type](payload)

    seen: set[str] = set()
    kept_raw: list[dict[str, Any]] = []
    for job in jobs:
        if job.job_id in seen:  # key is (source, board_token, job_id); source and token are fixed here
            continue
        seen.add(job.job_id)
        result.total += 1

        if passes_loose_filter(job):
            kept_raw.append(job.raw)

        student = is_student_title(job.title)
        if not is_canadian_location(job.location):
            if student and is_remote_no_country(job.location):
                result.remote_student_no_country += 1
            continue
        result.canada += 1
        if not student:
            continue
        result.canada_student += 1
        term = first_match(TERM_MENTION, job.title, job.description)
        duration = first_match(DURATION_MENTION, job.title, job.description)
        result.canada_student_with_term += term is not None
        result.canada_student_with_duration += duration is not None
        result.student_postings.append(
            {
                "job_id": job.job_id,
                "title": job.title,
                "location": job.location,
                "url": job.url,
                "term_match": term,
                "duration_match": duration,
            }
        )

    encoded = "\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in kept_raw).encode()
    result.loose_filter_kept = len(kept_raw)
    result.loose_filter_bytes = len(encoded)
    result.loose_filter_gzip_bytes = len(gzip.compress(encoded, mtime=0)) if encoded else 0
    return result


# --- Fetching -------------------------------------------------------------------


def fetch_json(url: str) -> tuple[Any, str | None]:
    """Return (parsed JSON, None) on success or (None, reason) on any failure."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        return None, type(e).__name__ + (f": {e.reason}" if isinstance(e, urllib.error.URLError) else "")


def looks_like_job_list(board_type: str, payload: Any) -> bool:
    if board_type == "lever":
        return isinstance(payload, list)
    return isinstance(payload, dict) and isinstance(payload.get("jobs"), list)


def fetch_and_measure(employer: dict[str, Any]) -> BoardResult:
    payload, error = fetch_json(board_url(employer["board_type"], employer["board_token"]))
    if error is None and not looks_like_job_list(employer["board_type"], payload):
        error = "unexpected response shape"
    if error is not None:
        return BoardResult(employer["id"], employer["board_type"], employer["board_token"], ok=False, error=error)
    return measure_board(employer, payload)


def run_all(employers: list[dict[str, Any]]) -> list[BoardResult]:
    """One thread per platform, so requests to the same host stay sequential and spaced."""
    by_platform: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for e in employers:
        by_platform[e["board_type"]].append(e)

    def run_platform(group: list[dict[str, Any]]) -> list[BoardResult]:
        out = []
        for i, employer in enumerate(group):
            if i:
                time.sleep(SLEEP_SECONDS)
            out.append(fetch_and_measure(employer))
            print(
                f"  {employer['board_type']:<10} {employer['board_token']:<28} {'ok' if out[-1].ok else out[-1].error}",
                file=sys.stderr,
            )
        return out

    with ThreadPoolExecutor(max_workers=max(1, len(by_platform))) as pool:
        groups = list(pool.map(run_platform, by_platform.values()))
    return sorted((r for g in groups for r in g), key=lambda r: r.employer_id)


# --- Reporting ------------------------------------------------------------------

SUM_FIELDS = (
    "total",
    "canada",
    "canada_student",
    "remote_student_no_country",
    "canada_student_with_term",
    "canada_student_with_duration",
    "loose_filter_kept",
    "loose_filter_bytes",
    "loose_filter_gzip_bytes",
)


def summarize(results: list[BoardResult], run_date: str) -> dict[str, Any]:
    ok = [r for r in results if r.ok]
    totals = {f: sum(getattr(r, f) for r in ok) for f in SUM_FIELDS}
    return {
        "run_date": run_date,
        "boards_in_seed_list": len(results),
        "boards_ok": len(ok),
        "boards_failed": len(results) - len(ok),
        "valid_for_decision": len(ok) >= MIN_RESPONDING_BOARDS,
        **totals,
    }


def decision_for(count: int) -> str:
    if count >= 100:
        return "100 or more: build v1 as planned."
    if count >= 40:
        return "40 to 99: build v1, and run employer discovery during v1 to reach about 300 employers."
    return "Fewer than 40: run employer discovery and the ATS terms check before the site; lead with program watch."


def markdown_report(summary: dict[str, Any], results: list[BoardResult]) -> str:
    s = summary
    lines = [
        "| Measure | Value |",
        "|---|---|",
        f"| Run date | {s['run_date']} |",
        f"| Boards in seed list | {s['boards_in_seed_list']} |",
        f"| Boards responding successfully | {s['boards_ok']} |",
        f"| Boards failed or 404 | {s['boards_failed']} |",
        f"| Total postings | {s['total']} |",
        f"| Postings in Canada | {s['canada']} |",
        f"| **Canadian student postings (headline)** | **{s['canada_student']}** |",
        f"| Student postings, remote with no country | {s['remote_student_no_country']} |",
        f"| Canadian student postings mentioning a term | {s['canada_student_with_term']} |",
        f"| Canadian student postings mentioning a duration | {s['canada_student_with_duration']} |",
        "",
        f"Loose Canada filter: {s['loose_filter_kept']} postings, "
        f"{s['loose_filter_bytes'] / 1e6:.2f} MB as JSON lines, {s['loose_filter_gzip_bytes'] / 1e6:.2f} MB gzipped.",
        "",
    ]
    if s["valid_for_decision"]:
        lines.append(f"Decision table row: {decision_for(s['canada_student'])}")
    else:
        lines.append(
            f"Not valid for the decision: {s['boards_ok']} boards responded, ADR 0001 needs at least "
            f"{MIN_RESPONDING_BOARDS}. Fix or add boards and re-run."
        )
    failed = [r for r in results if not r.ok]
    if failed:
        lines += ["", "Failed boards:", ""]
        lines += [f"- `{r.employer_id}` ({r.board_type}/{r.board_token}): {r.error}" for r in failed]
    lines += [
        "",
        "Per employer (boards with Canadian postings):",
        "",
        "| Employer | Board | Total | Canada | Canadian student | Term | Duration |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in sorted(results, key=lambda r: (-r.canada_student, -r.canada, r.employer_id)):
        if r.ok and r.canada:
            lines.append(
                f"| {r.employer_id} | {r.board_type} | {r.total} | {r.canada} | {r.canada_student} | "
                f"{r.canada_student_with_term} | {r.canada_student_with_duration} |"
            )
    return "\n".join(lines) + "\n"


def load_employers(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        employers: list[dict[str, Any]] = yaml.safe_load(f)["employers"]
    return employers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--employers", type=Path, default=DEFAULT_EMPLOYERS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--only", help="comma-separated employer ids; results are printed but not saved")
    args = parser.parse_args(argv)

    employers = load_employers(args.employers)
    if args.only:
        wanted = set(args.only.split(","))
        employers = [e for e in employers if e["id"] in wanted]
    run_date = dt.date.today().isoformat()
    print(f"Fetching {len(employers)} boards...", file=sys.stderr)
    results = run_all(employers)
    summary = summarize(results, run_date)
    report = markdown_report(summary, results)
    print(report)

    if not args.only:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        out = {"summary": summary, "boards": [asdict(r) for r in results]}
        (args.out_dir / f"{run_date}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
        (args.out_dir / f"{run_date}.md").write_text(report)
        print(f"Saved {args.out_dir / run_date}.json and .md", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
