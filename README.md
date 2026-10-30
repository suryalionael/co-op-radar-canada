# Co-op Radar Canada

Free tracker for Canadian co-op and internship postings, with verified term, duration and province, plus alerts when student programs open. Public sources only, $0 to run.

> **Status: early development (Phase 0).** There is no public site yet. The project is currently measuring how many Canadian student postings its sources actually provide before building anything on top of them. Everything below describes the plan unless it says otherwise. No metrics are reported until they have been measured.

---

## Why this exists

Canadian co-op students search differently from most internship seekers. Schools approve only specific work terms, so a student needs to know two things about every posting: **which term** it is (for example, Summer 2027) and **how long** it lasts (4, 8, 12 or 16 months). Most postings bury this in the description, and most internship trackers are US-focused and don't record it at all.

Many large Canadian employers and public-sector programs also announce *when* their student hiring opens weeks before the postings appear. Nobody collects those dates in one place.

Co-op Radar Canada aims to answer three questions:

1. **What is open right now?** Student postings with the term, duration and province extracted and checked, so you can filter to "Summer 2027, 4 months, Ontario" in one click.
2. **When do the big student programs open?** Daily monitoring of student-program pages, flagging the day each one changes.
3. **What student opportunities are in the news?** Headlines about co-op, internship and summer-job programs, new programs, and government funding for student hires. News is a hint, not an opening, and the site labels it that way.

## Principles

- **$0 to run.** GitHub Actions for scheduling, a static site for hosting. No paid APIs, no database server.
- **Public, permitted sources only.** Official job-board APIs, RSS feeds and open-data APIs. No scraping of LinkedIn, Indeed, Glassdoor or Reddit, and no unofficial access to Workday career sites.
- **Every fact is traceable.** Each posting keeps its source URL, fetch date, and the exact text each extracted field came from.
- **Honest labels.** If a posting doesn't state its duration, the site says "duration not stated" instead of guessing.
- **Explainable over clever.** Rules and simple models first. A more complex method replaces a simpler one only if it wins on a published evaluation. No LLM runs in the production pipeline.

## How it will work

A scheduled job runs once a day:

1. **Postings.** For each employer in `config/employers.yaml`, fetch open jobs from that employer's public Greenhouse, Lever or Ashby job-board API. Keep Canadian and remote postings and save a dated snapshot.
2. **Extraction.** Rule-based extractors find the term, duration, province and role track in each posting, storing the matching text span as evidence.
3. **Program watch.** Fetch about 30 student-program pages, fingerprint their main text, and record the date whenever it changes.
4. **News (v2).** Search public news APIs and RSS feeds for student-opportunity headlines. Store only the headline, outlet, date and link, never article text.
5. **Build.** DuckDB combines everything into small JSON files, and a static Next.js site lets visitors search and filter in their own browser.

## What it does not cover

Most large Canadian banks, insurers and pension funds post jobs on Workday, which has no public posting API. Their postings will not appear automatically. The site covers these employers through program watch and links to their own career pages instead, and says so on its About page.

## Evaluation

The extractors and the news classifier will be evaluated against hand-labelled data, and the results published here with counts and confidence intervals. A wrong duration is treated as worse than "not stated", so the target is precision of at least 0.95 on duration, with recall reported as measured.

| Field | Labelled examples | Precision | Recall |
|---|---|---|---|
| Term | not yet measured | — | — |
| Duration | not yet measured | — | — |
| Province | not yet measured | — | — |
| Track | not yet measured | — | — |

Full method and results will live in [`docs/evaluation.md`](docs/evaluation.md).

## Roadmap

| Phase | Target | Scope |
|---|---|---|
| Phase 0 | Nov 2026 | Coverage check: how many Canadian student postings do the sources provide? Decision recorded in an ADR |
| v1 | Dec 2026 | Daily postings pipeline, evaluated extractors, program watch, public static site |
| v2 | Jan 2027 | Posting submissions, employer pages, student-opportunity news, weekly digest and RSS |
| v3 | Spring 2027 | Market view, recruiting calendar, season write-up |

The week-by-week schedule, with what is done and what is next, is in [`docs/timeline.md`](docs/timeline.md).

## Repository layout

```
config/            employer list, program pages, news queries
scripts/           one-off scripts, such as the Phase 0 coverage check
pipeline/          fetching, extraction, news processing, site data build
data/              processed outputs and hand-labelled sets
tests/             pytest suite
site/              Next.js static site
docs/brief.md      full project brief
docs/decisions/    architecture decision records (one per decision)
docs/timeline.md   phase-by-phase schedule
docs/kanban.md     task board
```

## Running locally

Requires Python 3.12.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Phase 0:

```bash
python scripts/coverage_spike.py         # fetch every seed board once, save to data/coverage/
```

`scripts/check_board_tokens.py` checks which platform a candidate board token lives on, for adding employers to `config/employers.yaml`.

Pipeline (the daily Action runs the same commands; `data-branch/` is a checkout of the `data` branch):

```bash
git worktree add data-branch data        # or: git worktree add --orphan -b data data-branch
python -m pipeline.cli fetch-postings   --data-root data-branch
python -m pipeline.cli fetch-programs   --data-root data-branch
python -m pipeline.cli process-postings --data-root data-branch   # writes data/processed/postings.parquet
python -m pipeline.cli process-programs --data-root data-branch
python -m pipeline.cli label-sheet      --data-root data-branch   # rows to hand-label in data/labels/
python -m pipeline.cli evaluate         --data-root data-branch   # precision and recall with 95% intervals
python -m pipeline.cli reference-recall --data-root data-branch   # recall against a curated list (ADR 0007)
```

Program watch only fetches pages in `config/programs.yaml` whose URL has been checked by hand (`verified` set).

Site (Next.js static export, deployed on Vercel; see [`docs/deploy.md`](docs/deploy.md)):

```bash
python -m pipeline.cli build-site-data   # data/processed -> site/public/data
cd site && npm install
npm run dev:sample                        # fictional sample data, clearly bannered
npm run dev                               # real data
```

The design system is in [`DESIGN.md`](DESIGN.md).

## Design decisions

Every meaningful choice (which sources to use, how raw data is stored, why Workday is out of scope) is written up as a short decision record in [`docs/decisions/`](docs/decisions/). The full project brief is in [`docs/brief.md`](docs/brief.md).

## Team

Built by Lionael Surya (lead) and Ei Htoo. Who does what is in [`docs/team.md`](docs/team.md); open work is on the [kanban board](docs/kanban.md) and in [`TODO.md`](TODO.md).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). A submission form for postings the pipeline can't reach is planned for v2. Until then, feel free to open an issue with suggestions for employers or student-program pages to track.

## Disclaimer

Co-op Radar Canada is an independent student project. It is not affiliated with, endorsed by, or sponsored by any employer, job board, school, or government listed on the site. Always confirm details on the original posting before applying.

## Author

Built by Lionael Surya (Lio), Honours Bachelor of Data Science & Analytics, Seneca Polytechnic, Toronto, 
with Ei Htoo Khaing (E2), Honours Bachelor of Data Science & Analytics, Seneca Polytechnic, Toronto.

## License

To be decided.
