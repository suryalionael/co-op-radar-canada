"""Turn the processed Parquet files into the small JSON files the site loads.

Reads data/processed/*.parquet with DuckDB and writes site/public/data/:

    postings.json   open student postings in Canada, newest first
    programs.json   program-watch status and the change history
    meta.json       data date per source, counts, and the site's coverage numbers
    companies.json  every tracked company with its open count and hiring window

Output depends only on the data (no "generated at" clock time), so a day with
no new data produces identical files and no deploy. (Company badges use today's date,
so they can change when a hiring window comes near.)

If there is no processed data yet, the files are written empty and the site
says so. The site never ships sample postings.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

import duckdb
import yaml

from pipeline.hiring_window import badge, hiring_window

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
SITE_DATA = ROOT / "site" / "public" / "data"
EMPLOYERS = ROOT / "config" / "employers.yaml"
RUN_LOG = ROOT / "data" / "run_log.jsonl"

POSTING_FIELDS = [
    "id",
    "source",
    "employer_id",
    "title",
    "url",
    "location_raw",
    "province",
    "provinces",
    "remote",
    "term",
    "terms",
    "term_status",
    "flag_term_in_past",
    "term_start",
    "term_end",
    "duration_options_months",
    "duration_is_range",
    "duration_status",
    "track",
    "first_seen",
    "last_seen",
    "evidence",
]

DEFAULTS = {  # columns added after the first processed files
    "duration_is_range": "FALSE",
    "term_status": "NULL",
    "flag_term_in_past": "FALSE",
}


def _rows(con: duckdb.DuckDBPyConnection, sql: str) -> list[dict[str, Any]]:
    result = con.execute(sql)
    columns = [d[0] for d in result.description]
    return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]


def _jsonable(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


def load_employers(path: Path) -> dict[str, dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return {e["id"]: e for e in yaml.safe_load(f)["employers"]}


def last_fetch_days(run_log: Path) -> dict[str, str | None]:
    """The latest day each fetch command ran, from data/run_log.jsonl."""
    days: dict[str, str | None] = {"postings": None, "programs": None}
    if not run_log.exists():
        return days
    for line in run_log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        key = {"fetch-postings": "postings", "fetch-programs": "programs"}.get(entry.get("command", ""))
        if key and entry.get("day"):
            days[key] = max(days[key] or "", entry["day"])
    return days


def build_postings(con: duckdb.DuckDBPyConnection, processed: Path, employers: dict[str, dict[str, Any]]) -> list[Any]:
    path = processed / "postings.parquet"
    if not path.exists():
        return []
    columns = {row["column_name"] for row in _rows(con, f"DESCRIBE SELECT * FROM read_parquet('{path.as_posix()}')")}
    # A Parquet file written before a column existed still builds; the column reads as its default.
    fields = [f if f in columns else f"{DEFAULTS[f]} AS {f}" for f in POSTING_FIELDS]
    rows = _rows(
        con,
        f"""
        SELECT {", ".join(fields)}
        FROM read_parquet('{path.as_posix()}')
        WHERE in_canada AND is_student_role AND status = 'open'
        ORDER BY first_seen DESC, id
        """,
    )
    out = []
    for row in rows:
        evidence = json.loads(row.pop("evidence") or "{}")
        employer = employers.get(row["employer_id"], {})
        out.append(
            {k: _jsonable(v) for k, v in row.items()}
            | {
                "employer": employer.get("name", row["employer_id"]),
                "sector": employer.get("sector"),
                "evidence": {
                    k: evidence[k]
                    for k in ("term", "term_context", "term_dates", "term_ambiguous", "duration", "duration_context")
                    if k in evidence
                },
            }
        )
    return out


def build_programs(con: duckdb.DuckDBPyConnection, processed: Path) -> dict[str, list[Any]]:
    watch_path, changes_path = processed / "program_watch.parquet", processed / "program_changes.parquet"
    programs = []
    if watch_path.exists():
        programs = _rows(
            con,
            f"""
            SELECT program_id, employer_id, name, url, last_checked, last_fetch_ok,
                   last_hash IS NOT NULL AS ever_read, last_changed,
                   change_excerpt, expected_open, expected_open_src
            FROM read_parquet('{watch_path.as_posix()}')
            ORDER BY last_changed DESC NULLS LAST, name
            """,
        )
    changes = []
    if changes_path.exists():
        changes = _rows(
            con,
            f"""
            SELECT program_id, changed_on, change_excerpt, kind
            FROM read_parquet('{changes_path.as_posix()}')
            ORDER BY changed_on DESC, program_id
            LIMIT 200
            """,
        )
    return {
        "programs": [{k: _jsonable(v) for k, v in p.items()} for p in programs],
        "changes": [{k: _jsonable(v) for k, v in c.items()} for c in changes],
    }


BOARD_URLS = {
    "greenhouse": "https://job-boards.greenhouse.io/{}",
    "lever": "https://jobs.lever.co/{}",
    "ashby": "https://jobs.ashbyhq.com/{}",
}
BADGE_ORDER = {"open": 0, "soon": 1, "quiet": 2}


def student_first_seen(con: duckdb.DuckDBPyConnection, processed: Path) -> dict[str, list[dt.date]]:
    """First-seen dates of every Canadian student posting, open or closed, by employer."""
    path = processed / "postings.parquet"
    if not path.exists():
        return {}
    dates: dict[str, list[dt.date]] = {}
    sql = f"SELECT employer_id, first_seen FROM read_parquet('{path.as_posix()}') WHERE in_canada AND is_student_role"
    for row in _rows(con, sql):
        dates.setdefault(row["employer_id"], []).append(row["first_seen"])
    return dates


def build_companies(
    employers: dict[str, dict[str, Any]],
    postings: list[Any],
    programs: list[Any],
    dates: dict[str, list[dt.date]],
    today: dt.date,
) -> list[Any]:
    open_ids: dict[str, list[str]] = {}
    for p in postings:
        open_ids.setdefault(p["employer_id"], []).append(p["id"])
    by_employer = {p["employer_id"]: p for p in programs}
    names = {eid: e.get("name", eid) for eid, e in employers.items()}
    names |= {eid: p["name"] for eid, p in by_employer.items() if eid not in names}
    out = []
    for eid, name in names.items():
        e, program = employers.get(eid, {}), by_employer.get(eid)
        company_dates = list(dates.get(eid, []))
        if program and program.get("expected_open"):
            company_dates.append(dt.date.fromisoformat(str(program["expected_open"])))
        window = hiring_window(company_dates)
        ids = open_ids.get(eid, [])
        years = sorted({d.year for d in company_dates})
        span = f"{years[0]}" if years and years[0] == years[-1] else f"{years[0]}–{years[-1]}" if years else ""
        out.append(
            {
                "slug": eid,
                "name": name,
                "sector": e.get("sector"),
                "board_url": BOARD_URLS[e["board_type"]].format(e["board_token"])
                if e.get("board_type") in BOARD_URLS
                else None,
                "open_count": len(ids),
                "posting_ids": ids,
                "program_id": program["program_id"] if program else None,
                "window": window,
                "basis": f"from {len(company_dates)} postings, {span}" if company_dates else "",
                "badge": badge(window, len(ids), today),
            }
        )
    return sorted(out, key=lambda c: (BADGE_ORDER[c["badge"]], -c["open_count"], c["name"].casefold()))


def build(
    processed: Path = PROCESSED,
    out_dir: Path = SITE_DATA,
    employers_path: Path = EMPLOYERS,
    run_log: Path = RUN_LOG,
    today: dt.date | None = None,
) -> dict[str, Any]:
    employers = load_employers(employers_path)
    con = duckdb.connect()
    postings = build_postings(con, processed, employers)
    programs = build_programs(con, processed)
    days = last_fetch_days(run_log)
    companies = build_companies(
        employers, postings, programs["programs"], student_first_seen(con, processed), today or dt.date.today()
    )
    meta = {
        "data_as_of": days,
        "counts": {
            "open_student_postings": len(postings),
            "duration_stated": sum(p["duration_status"] == "stated" for p in postings),
            "duration_from_dates": sum(p["duration_status"] == "inferred_from_dates" for p in postings),
            "employers_with_postings": len({p["employer_id"] for p in postings}),
            "employer_boards_tracked": len(employers),
            "programs_watched": len(programs["programs"]),
            "companies": len(companies),
        },
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, data in (("postings", postings), ("programs", programs), ("meta", meta), ("companies", companies)):
        text = json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
        (out_dir / f"{name}.json").write_text(text, encoding="utf-8")
    return meta


if __name__ == "__main__":
    print(json.dumps(build(), indent=1))
