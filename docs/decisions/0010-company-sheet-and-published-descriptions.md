# 0010: The company list lives in a Google Sheet, and job descriptions are published

- **Status:** Accepted
- **Date:** 2026-11-25
- **Deciders:** Lionael Surya
- **Changes:** ADR 0002 (descriptions were never to reach `main`) in one respect, and the `config/employers.yaml` convention.

## Context

Two things Lio asked for:

1. Clicking a job should open a page with the employer's full description and an Apply button, like the reference board.
2. Lio and Ei Htoo should add, edit and delete companies themselves, and record each company's researched hiring months, without going through a coding session.

ADR 0002 keeps full API responses off `main` because committing them daily would grow the repo by megabytes a day, forever. The site is a static export built by Vercel from `main`, and Vercel cannot see the orphan `data` branch.

## Decision

**Descriptions.** The daily run writes a cleaned copy of each *open* posting's description to `site/content/descriptions/<id>.html`, and the site builds one page per posting from it.

- The HTML is reduced to an allowlist in the pipeline (`pipeline/sanitize.py`): paragraphs, line breaks, lists, bold, italic, `https` links with `rel="noopener noreferrer nofollow"`, headings mapped to `h3`/`h4`. Scripts, styles, frames, images, event handlers and every other attribute are dropped.
- A file is rewritten only when its text changes and deleted when the posting closes, so git history grows by new and edited postings, not by the whole set each day. About 120 files, 1 MB today.
- Each page says where the text came from and links to the employer's own application page. The site never hosts applications.

**Company list.** One Google Sheet is the source of truth.

- The sheet is shared view-only to anyone with the link and editable by Lio and Ei. It holds only public information; `notes` is the one column that is never published.
- The daily run downloads it as CSV, validates it (`pipeline/companies.py`), and writes `config/companies.csv`. Every other step reads that committed copy. `config/employers.yaml` is gone.
- A sheet that cannot be downloaded, fails validation, or has fewer than half the committed rows is rejected whole: the last good copy stays, the reason goes in `data/run_log.jsonl`, and the workflow run is marked failed.
- Removing a row (or setting `show = no`) removes the company and its postings from the site on the next run. Raw history on the `data` branch is untouched.
- A company's `hiring_months`, when filled in, replaces the calendar built from postings and is labelled "Researched" on the site, with its note and source.
- The 30 program-watch pages stay in `config/programs.yaml`, because each was checked by hand for fetchability.

## Consequences

- Posting text from employers is republished, sanitised, with credit and a link. If an employer objects, deleting its row removes it on the next run.
- Anyone with edit access to the sheet can change what the site shows the next morning. Validation limits the damage of mistakes, not of bad intent; keep edit access to the team.
- The daily workflow now depends on a repository variable, `COMPANY_SHEET_CSV_URL`. If it is missing the step fails visibly and the committed list keeps being used.
- `scripts/migrate_employers_to_csv.py` records how the CSV was first made from the YAML files; it no longer runs.
