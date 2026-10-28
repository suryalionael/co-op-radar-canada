"""Turn the processed Parquet files into the small JSON files the site loads.

Reads data/processed/*.parquet with DuckDB and writes site/public/data/:

    postings.json   open student postings in Canada, newest first
    programs.json   program-watch status and the change history
    meta.json       data date per source, counts, and the site's coverage numbers

Output depends only on the data (no "generated at" clock time), so a day with
no new data produces identical files and no deploy.

If there is no processed data yet, the files are written empty and the site
says so. The site never ships sample postings.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb
import yaml

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
SITE_DATA = ROOT / "site" / "public" / "data"
EMPLOYERS = ROOT / "config" / "employers.yaml"
RUN_LOG = ROOT / "data" / "run_log.jsonl"

POSTING_FIELDS = [
    "id",
    "employer_id",
    "title",
    "url",
    "location_raw",
    "province",
    "provinces",
    "remote",
    "term",
    "terms",
    "term_start",
    "term_end",
    "duration_options_months",
    "duration_status",
    "track",
    "first_seen",
    "last_seen",
    "evidence",
]


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
    rows = _rows(
        con,
        f"""
        SELECT {", ".join(POSTING_FIELDS)}
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
                    for k in ("term", "term_context", "term_dates", "duration", "duration_context")
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
            SELECT program_id, employer_id, name, url, last_checked, last_fetch_ok, last_changed,
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


def build(
    processed: Path = PROCESSED, out_dir: Path = SITE_DATA, employers_path: Path = EMPLOYERS, run_log: Path = RUN_LOG
) -> dict[str, Any]:
    employers = load_employers(employers_path)
    con = duckdb.connect()
    postings = build_postings(con, processed, employers)
    programs = build_programs(con, processed)
    days = last_fetch_days(run_log)
    meta = {
        "data_as_of": days,
        "counts": {
            "open_student_postings": len(postings),
            "duration_stated": sum(p["duration_status"] == "stated" for p in postings),
            "duration_from_dates": sum(p["duration_status"] == "inferred_from_dates" for p in postings),
            "employers_with_postings": len({p["employer_id"] for p in postings}),
            "employer_boards_tracked": len(employers),
            "programs_watched": len(programs["programs"]),
        },
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, data in (("postings", postings), ("programs", programs), ("meta", meta)):
        text = json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
        (out_dir / f"{name}.json").write_text(text, encoding="utf-8")
    return meta


if __name__ == "__main__":
    print(json.dumps(build(), indent=1))
