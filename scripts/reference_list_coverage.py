"""Which job-board platforms does the curated Canadian internship list point to?

Fetches both READMEs of negarprh/Canadian-Tech-Internships-2027 (ADR 0007),
saves the raw copies to the gitignored data/reference/raw/, parses every row
and classifies each Apply link by platform. Writes two committed files of
aggregate counts and our own token lists, never the listings themselves:

- data/coverage/reference_platform_breakdown.csv: per season and platform, the
  number of listings, open listings and distinct companies. Links on other
  hosts are broken out by host.
- data/coverage/reference_candidate_tokens.csv: every Greenhouse, Lever and
  Ashby board token the list links to, plus the companies whose links show
  Greenhouse (gh_jid) without a token, and whether each is already in
  config/employers.yaml.

Usage:
    python scripts/reference_list_coverage.py            # fetch, save raw, write CSVs
    python scripts/reference_list_coverage.py --offline  # reuse data/reference/raw/
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

import yaml

from pipeline.reference_list import FILES, TOKEN_PLATFORMS, ReferenceRow, classify_url, fetch_raw, load_rows

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "reference" / "raw"
OUT_DIR = ROOT / "data" / "coverage"
EMPLOYERS = ROOT / "config" / "employers.yaml"


def platform_breakdown(rows: list[ReferenceRow]) -> list[dict[str, object]]:
    """Listings, open listings and distinct companies per (season, platform[, host]).

    Closed rows have no link, so they are counted under platform "none"; the
    platform shares that matter are over open rows with a link.
    """
    groups: dict[tuple[int, str, str], list[ReferenceRow]] = defaultdict(list)
    for r in rows:
        p = classify_url(r.apply_url)
        groups[(r.season, p.platform, p.host if p.platform == "other" else "")].append(r)
        groups[(r.season, "all", "")].append(r)
    out: list[dict[str, object]] = []
    for (season, platform, host), group in sorted(groups.items(), key=lambda kv: (kv[0][0], -len(kv[1]), kv[0][1:])):
        out.append(
            {
                "season": season,
                "platform": platform,
                "host": host,
                "listings": len(group),
                "open_listings": sum(not r.closed for r in group),
                "companies": len({r.company.casefold() for r in group}),
            }
        )
    return out


def configured_boards(path: Path = EMPLOYERS) -> set[tuple[str, str]]:
    """(platform, token) for every configured board, plus (platform, "name:<employer name>") so that
    a link with an unknown token can still be matched to a configured employer by name."""
    with path.open(encoding="utf-8") as f:
        employers = yaml.safe_load(f)["employers"]
    boards = {(e["board_type"], str(e["board_token"]).lower()) for e in employers}
    return boards | {(e["board_type"], f"name:{e['name'].casefold()}") for e in employers}


def candidate_tokens(rows: list[ReferenceRow], configured: set[tuple[str, str]]) -> list[dict[str, object]]:
    """One row per (platform, token, company) on Greenhouse, Lever or Ashby. Token is blank when unknown."""
    groups: dict[tuple[str, str, str], list[ReferenceRow]] = defaultdict(list)
    names: dict[str, str] = {}
    for r in rows:
        p = classify_url(r.apply_url)
        if p.platform not in TOKEN_PLATFORMS:
            continue
        key = r.company.casefold()
        names.setdefault(key, r.company)
        groups[(p.platform, (p.token or "").lower(), key)].append(r)
    out: list[dict[str, object]] = []
    for (platform, token, key), group in sorted(groups.items()):
        out.append(
            {
                "platform": platform,
                "token": token,
                "company": names[key],
                "seasons": ";".join(str(s) for s in sorted({r.season for r in group})),
                "listings": len(group),
                "in_employers_yaml": "yes" if (platform, token or f"name:{key}") in configured else "no",
            }
        )
    return out


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--offline", action="store_true", help="reuse the raw copies in data/reference/raw/")
    args = parser.parse_args(argv)
    if not args.offline:
        fetch_raw(RAW_DIR)
    rows = load_rows(RAW_DIR)
    if not rows:
        print("No listing rows parsed: has the table format changed?", file=sys.stderr)
        return 1
    breakdown = platform_breakdown(rows)
    tokens = candidate_tokens(rows, configured_boards())
    write_csv(OUT_DIR / "reference_platform_breakdown.csv", breakdown)
    write_csv(OUT_DIR / "reference_candidate_tokens.csv", tokens)
    for season in FILES:
        print(f"{season}: {sum(r.season == season for r in rows)} rows")
    print(f"{len(tokens)} candidate token rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
