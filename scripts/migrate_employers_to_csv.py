"""One-off: build config/companies.csv from config/employers.yaml and config/programs.yaml.

Every employer with a job board becomes a row. Every employer that appears only in
config/programs.yaml (banks, governments) also becomes a row, with no board. Old fields
that have no column (verified date, headquarters country, source list) go into `notes`.
Kept as the record of how the CSV was first made. config/employers.yaml was deleted in the
same commit (it is in git history), so this no longer runs as-is. The Google Sheet is the
source of truth from then on.

    python scripts/migrate_employers_to_csv.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import yaml

from pipeline.companies import COLUMNS

ROOT = Path(__file__).resolve().parent.parent

# Names for employers known only through program watch (programs.yaml has ids, not names).
PROGRAM_EMPLOYER_NAMES = {
    "alberta_public_service": "Alberta Public Service",
    "bank_of_canada": "Bank of Canada",
    "bc_hydro": "BC Hydro",
    "bc_public_service": "BC Public Service",
    "bmo": "BMO",
    "canada_life": "Canada Life",
    "cibc": "CIBC",
    "cra": "Canada Revenue Agency",
    "deloitte_canada": "Deloitte Canada",
    "edc": "Export Development Canada",
    "evr": "Elk Valley Resources",
    "ey_canada": "EY Canada",
    "government_of_canada": "Government of Canada",
    "health_canada": "Health Canada",
    "hydro_one": "Hydro One",
    "interac": "Interac",
    "justice_canada": "Justice Canada",
    "kpmg_canada": "KPMG Canada",
    "manitoba_hydro": "Manitoba Hydro",
    "nrcan": "Natural Resources Canada",
    "omers": "OMERS",
    "ontario_public_service": "Ontario Public Service",
    "pwc_canada": "PwC Canada",
    "quebec_public_service": "Québec Public Service",
    "rbc": "RBC",
    "scotiabank": "Scotiabank",
    "ttc": "TTC",
}


def main() -> None:
    employers = yaml.safe_load((ROOT / "config" / "employers.yaml").read_text(encoding="utf-8"))["employers"]
    programs = yaml.safe_load((ROOT / "config" / "programs.yaml").read_text(encoding="utf-8"))["programs"]
    rows: list[dict[str, str]] = []
    for e in employers:
        notes = [f"verified {e['verified']}"] if e.get("verified") else []
        if e.get("hq_country"):
            notes.append(f"HQ {e['hq_country']}")
        if e.get("source"):
            notes.append("source: " + ", ".join(e["source"]))
        rows.append(
            {
                "id": e["id"],
                "name": e["name"],
                "sector": e.get("sector") or "",
                "show": "yes",
                "board_type": e["board_type"],
                "board_token": str(e["board_token"]),
                "hq_province": e.get("hq_province") or "",
                "notes": "; ".join(notes),
            }
        )
    have = {r["id"] for r in rows}
    first_page: dict[str, str] = {}
    for p in programs:
        first_page.setdefault(p["employer_id"], p["url"])
    for eid in sorted(first_page):
        if eid not in have:
            rows.append({"id": eid, "name": PROGRAM_EMPLOYER_NAMES[eid], "show": "yes", "careers_url": first_page[eid]})
    with (ROOT / "config" / "companies.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n", restval="")
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} companies ({len(employers)} with boards)")


if __name__ == "__main__":
    main()
