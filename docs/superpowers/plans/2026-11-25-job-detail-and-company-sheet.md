# Job Detail Pages and Company Sheet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clicking a job opens a detail page with the full cleaned description and an Apply button; the company list moves to a Google Sheet Lio and Ei edit, including researched hiring months.

**Architecture:** The pipeline sanitises each open posting's description into `site/content/descriptions/<id>.html`, and the site builds one static page per posting from it. A new `pipeline/companies.py` loads and validates `config/companies.csv`, which a daily `sync-companies` step refreshes from the Google Sheet's view-only CSV link (keeping the last good copy on any failure); every consumer of `config/employers.yaml` switches to it.

**Tech Stack:** Python 3.12 (stdlib `html.parser`, `csv`, httpx, pytest), DuckDB, Next.js 16 static export, Tailwind v4, Google Drive/Sheets connectors.

**Spec:** `docs/superpowers/specs/2026-11-25-job-detail-and-company-sheet-design.md`

## Global Constraints

- Public, permitted sources only; no secrets anywhere: the sheet is read through a view-only link.
- Next.js static export on the Vercel free tier. One page per open posting.
- Employer HTML is sanitised in the pipeline: allowlist only (`p`, `br`, `ul`, `ol`, `li`, `strong`, `b`, `em`, `i`, `a`, headings mapped to `h3`/`h4`); links `https:` only with `rel="noopener noreferrer nofollow"`; no scripts, styles, handlers, `javascript:` URLs, images or iframes.
- Never commit full daily API responses to `main` (ADR 0002): only sanitised descriptions of open postings, rewritten only when changed, deleted when a posting closes.
- A bad sheet must never break the site or the daily run: validate, and keep the last good `config/companies.csv`. Refuse a sheet with fewer than 50% of the previous row count.
- A researched hiring window is always labelled `researched`; the `notes` column is never published.
- Commits are authored by Lio; no Claude co-author lines. Checks before pushing: `ruff check .`, `ruff format --check .`, `mypy pipeline`, `pytest -q`, and in `site/`: `npm run typecheck`, `npm run build`, `npm run build:sample`.
- UI uses the timetable design (`DESIGN.md`); verify with `impeccable detect` at 1440x900 and 390x844.

## Review Focus

- A description containing `<script>`, `onerror=`, `javascript:` links, unclosed or nested tags → sanitised output has none of them (Task 1).
- A posting whose description file is missing → its detail page still renders facts and Apply; the build does not fail (Tasks 2, 3).
- A sheet that was cleared, mostly deleted, or fails to download → the last good CSV stays, the reason is logged, the run is marked failed (Task 5).
- Duplicate `id`, unknown `board_type`, non-`https` URL, `show` not yes/no, unparseable `hiring_months` → whole sheet rejected with a message naming the row; never silently blank (Task 4).
- Hiring months that wrap the year ("Nov-Jan") → a window with start 11, end 1 (Task 4).
- A company with researched months but no board and no postings → still listed with its researched strip (Tasks 6, 7).

---

## Part A: job detail pages

### Task 1: Description sanitiser

**Files:**
- Create: `pipeline/sanitize.py`
- Test: `tests/test_sanitize.py`

**Interfaces:**
- Produces: `sanitize_description(html: str) -> str`: cleaned HTML fragment, deterministic, `""` for empty input.

- [ ] **Step 1: Write failing tests** in `tests/test_sanitize.py`:
  - `<p>Hello <strong>you</strong></p>` is returned unchanged.
  - `<script>alert(1)</script><p>x</p>` → `<p>x</p>` (contents of script, style, iframe, object, svg, noscript, template are dropped, not just the tags).
  - `<p onclick="x()" style="color:red">a</p>` → `<p>a</p>`.
  - `<a href="javascript:alert(1)">x</a>` → `x`; `<a href="http://e.com">x</a>` → text only (https only); `<a href="https://e.com/a?b=1&c=2">x</a>` → `<a href="https://e.com/a?b=1&amp;c=2" rel="noopener noreferrer nofollow">x</a>`.
  - `<img src=x onerror=alert(1)>` → `""`; `<h1>T</h1><h5>S</h5>` → `<h3>T</h3><h4>S</h4>`; unknown `<div><span>t</span></div>` → `t` (unwrapped).
  - Unclosed `<ul><li>a<li>b` → `<ul><li>a</li><li>b</li></ul>` (every opened allowed tag is closed).
  - Greenhouse-style escaped input `&lt;p&gt;Hi&lt;/p&gt;` → `<p>Hi</p>` (unescape once when the input has no `<` but has `&lt;`).
  - Output of the sanitiser, sanitised again, is unchanged (idempotent); a 2 MB input finishes in under 2 s.
- [ ] **Step 2: Run** `pytest tests/test_sanitize.py -q`. Expected: FAIL (module missing).
- [ ] **Step 3: Implement `sanitize_description`** with a stdlib `html.parser.HTMLParser` subclass that emits only allowlisted tags with their allowed attributes, tracks a stack to close unclosed tags, and skips the content of the drop-list tags. Escape text and attribute values with `html.escape`.
- [ ] **Step 4: Run tests** and `ruff check`, `ruff format`, `mypy pipeline`. Expected: PASS.
- [ ] **Step 5: Commit** `git add pipeline/sanitize.py tests/test_sanitize.py && git commit -m "Add description sanitiser"`.

### Task 2: Write sanitised descriptions for open postings

**Files:**
- Modify: `pipeline/build_site_data.py`, `pipeline/cli.py` (`build-site-data` accepts `--data-root`), `.github/workflows/daily.yml`
- Test: `tests/test_build_site_data.py`

**Interfaces:**
- Consumes: `sanitize_description`; `pipeline.storage.read_description(root: Path, description_hash: str) -> str`; posting rows already carry `id` and `description_hash`.
- Produces: `write_descriptions(rows: list[dict[str, Any]], data_root: Path, out_dir: Path) -> int` (files written or kept; rows need `id` and `description_hash`), constant `DESCRIPTIONS = ROOT / "site" / "content" / "descriptions"`, and `build(..., data_root: Path | None = None, descriptions_dir: Path = DESCRIPTIONS)`. With `data_root=None` nothing is written or deleted.

- [ ] **Step 1: Write failing tests** with a `data_root` fixture built by `write_postings_day`: an open posting gets `<id>.html` with sanitised text; a closed one gets none; a file for an id no longer open is deleted; a second `build` with unchanged data leaves file contents and mtimes untouched; a posting whose description file is missing is skipped without raising and the others are still written; the descriptions never appear in `postings.json`.
- [ ] **Step 2: Run** the new tests. Expected: FAIL.
- [ ] **Step 3: Implement.** Add `description_hash` to the query for open student postings (kept out of the JSON), call `write_descriptions` from `build` when `data_root` is given, write a file only when its content differs, delete stale `*.html`. Pass `--data-root` through `cli.py`.
- [ ] **Step 4: Update `daily.yml`:** run `build-site-data --data-root data-branch` and add `site/content/descriptions` to the paths committed to `main`.
- [ ] **Step 5: Run** `pytest -q`, `ruff`, `mypy pipeline`. Expected: PASS.
- [ ] **Step 6: Generate once locally** against the `data` branch checkout and check the sizes: `du -sh site/content/descriptions` should be a few MB at most; report the number. Commit code and the generated files: `git add pipeline tests .github site/content && git commit -m "Write sanitised descriptions for open postings"`.

### Task 3: Detail page, linked rows, 404

**Files:**
- Create: `site/app/jobs/[id]/page.tsx`, `site/app/not-found.tsx`, `site/sample-data/descriptions/<id>.html` (for two of the sample postings; leave one sample posting without a file)
- Modify: `site/lib/data.ts`, `site/components/JobRow.tsx`, `site/app/globals.css` (a `.prose-posting` block for the description), `site/app/companies/[slug]/page.tsx` only if it needs the new row API
- Test: build output and screenshots (the site has no unit runner)

**Interfaces:**
- Produces: `getDescription(id: string): string | null` in `site/lib/data.ts` (reads `site/content/descriptions/<id>.html`, or `site/sample-data/descriptions/<id>.html` when `isSampleData`; `null` if absent). Route `/jobs/<id>/`, one page per open posting, `dynamicParams = false`.

- [ ] **Step 1: Implement the page** in the timetable design, following Lio's screenshot: back link to `/`, company tile (letter) with "Company · Hiring", title, chips (location, term, length plate, work mode), primary **Apply** button (`<a href={p.url} target="_blank" rel="noopener noreferrer">`, with the visually-hidden "opens the employer's site" text), a facts block (term and length with plates, `EvidenceQuote` for term, length and dates, the "worked out from dates" and "not stated" wording as today), the description in a `max-w-[70ch]` column via `dangerouslySetInnerHTML` (safe: sanitised in the pipeline; say so in a code comment), a second Apply button, and the footer line "Posting text from <Company>'s <Greenhouse|Lever|Ashby> job board, first seen <date>. Always confirm on the employer's site." When `getDescription` is `null`, show a one-line "The full text isn't available here; read it on the employer's site." and still show everything else.
- [ ] **Step 2: Link the rows.** In `JobRow`, the title becomes a `next/link` to `/jobs/<id>/` with a stretched-link pseudo-element so the whole row is clickable; the Apply link keeps `position: relative` above it. Remove the "source" toggle and the expanded panel (moved to the detail page).
- [ ] **Step 3: `not-found.tsx`** in the same design: "That posting is closed or doesn't exist.", links to Jobs and Companies.
- [ ] **Step 4: Build** `npm run typecheck`, `npm run build`, `npm run build:sample`. Expected: all pass; `out/jobs/<id>/index.html` exists for every open posting; the sample posting without a file renders.
- [ ] **Step 5: Look at it:** `impeccable shot` the detail page at 1440x900 and 390x844 (use the Chromium wrapper from earlier sessions), `impeccable detect --json` on the page and on `/` and `/companies/` (expect 0), and a contrast check. Fix what they show.
- [ ] **Step 6: Commit** `git add site && git commit -m "Job detail pages with full description and Apply; rows link to them"`.

---

## Part B: the company sheet

### Task 4: Company loader and validator

**Files:**
- Create: `pipeline/companies.py`
- Test: `tests/test_companies.py`

**Interfaces:**
- Produces:
  - `COLUMNS: list[str]` = `["id","name","sector","show","website","careers_url","board_type","board_token","hq_province","hiring_months","hiring_note","hiring_source","notes"]`
  - `class SheetError(ValueError)` with `.problems: list[str]`
  - `parse_hiring_months(text: str) -> list[int]`: month numbers 1–12 in order (wrapping allowed); `""` → `[]`; raises `ValueError` on anything unparseable. Accepts `Sep-Oct`, `Sep to Oct`, `September–October`, `9,10`, `Nov-Jan` (→ `[11,12,1]`), `Sep, Nov`.
  - `parse_companies(csv_text: str) -> list[dict[str, str]]`: validates and returns rows, raising `SheetError` listing every problem with its row number. Rules: all `COLUMNS` present (extra columns ignored); `id` non-empty, unique, `^[a-z0-9][a-z0-9_-]*$`; `name` non-empty; `show` is `yes` or `no` (default `yes` when blank); `board_type` blank or one of `greenhouse|lever|ashby`, and a token required when a type is given; `website` and `careers_url` blank or `https://…`; `hiring_months` parses; a header-only sheet is an error.
  - `load_companies(path: Path) -> list[dict[str, str]]`
  - `load_employers(path: Path, include_hidden: bool = False) -> list[dict[str, Any]]`: rows with a board, shaped like the old YAML entries (`id`, `name`, `sector`, `board_type`, `board_token`, `hq_province`), skipping `show = no` unless `include_hidden`.

- [ ] **Step 1: Write failing tests** for each rule above, each asserting the message names the row (`"row 4"`); `parse_hiring_months("Nov-Jan") == [11, 12, 1]`, `("9,10") == [9, 10]`, `("Sept") == [9]`, `("") == []`, `("banana")` raises; CRLF and a UTF-8 BOM are accepted; a cell starting with `=` is kept as plain text.
- [ ] **Step 2: Run** `pytest tests/test_companies.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement** with the stdlib `csv` module (`utf-8-sig`). Collect all problems before raising.
- [ ] **Step 4: Run tests, ruff, mypy.** Expected: PASS.
- [ ] **Step 5: Commit** `git add pipeline/companies.py tests/test_companies.py && git commit -m "Add company sheet loader and validator"`.

### Task 5: Sync from the sheet

**Files:**
- Modify: `pipeline/companies.py` (add sync), `pipeline/cli.py` (new `sync-companies` command), `.github/workflows/daily.yml`
- Test: `tests/test_companies.py`

**Interfaces:**
- Consumes: `parse_companies`, `SheetError`, `log_run` from `cli.py`.
- Produces: `sync_sheet(fetch: Callable[[], str], committed: Path) -> SyncResult` where `SyncResult` is a dataclass `(ok: bool, rows: int, changed: bool, reason: str | None)`. It calls `fetch()`, validates, applies the 50% guard against the committed file's row count, and writes `committed` only on success and only when content changed. Any exception from `fetch`, any `SheetError`, or a guard failure returns `ok=False` with a reason and leaves the file untouched. CLI `python -m pipeline.cli sync-companies --url <csv url>` logs a `sync-companies` line (`rows`, `changed`, `ok`, `reason`) and exits 1 when not ok.

- [ ] **Step 1: Write failing tests:** a good sheet replaces the file; identical content reports `changed=False`; a fetch that raises keeps the file and returns the reason; a sheet with a duplicate id is rejected; a sheet with 9 rows against a committed 20 is rejected (guard), while 10 is accepted; an empty body is rejected; no committed file yet accepts any valid sheet.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement `sync_sheet`** and the CLI command (default fetcher: `httpx.get(url, follow_redirects=True, timeout=30)` with `raise_for_status`).
- [ ] **Step 4: Daily workflow:** add a step before "Fetch postings": `python -m pipeline.cli sync-companies --url "${{ vars.COMPANY_SHEET_CSV_URL }}"` with `continue-on-error: true` and id `companies`, add `steps.companies.outcome == 'failure'` to the final failure check, and add `config/companies.csv` to the paths committed to `main`. (The URL is a repository variable, set in Task 8; it is not a secret.)
- [ ] **Step 5: Run tests, ruff, mypy.** Expected: PASS.
- [ ] **Step 6: Commit** `git add pipeline tests .github && git commit -m "Sync the company list from the Google Sheet, keeping the last good copy"`.

### Task 6: Migrate to `config/companies.csv` and switch every reader

**Files:**
- Create: `scripts/migrate_employers_to_csv.py` (one-off), `config/companies.csv`
- Modify: `pipeline/cli.py` (both `EMPLOYERS` uses), `pipeline/build_site_data.py`, `scripts/reference_list_coverage.py`, `scripts/coverage_spike.py`, `scripts/check_board_tokens.py` docstring, `pipeline/reference_recall.py` docstring, `README.md`, `TODO.md`; delete `config/employers.yaml`
- Test: `tests/test_build_site_data.py`, `tests/test_companies.py`

**Interfaces:**
- Consumes: `load_employers`, `load_companies`.
- Produces: `config/companies.csv` with one row per current company: every `employers.yaml` entry (`show = yes`, `notes` = its old `verified` date and `source`), plus one row per program-only employer from `config/programs.yaml` (name from `PROGRAM_EMPLOYER_NAMES`, no board). `build_site_data.build(..., companies_path: Path = COMPANIES)` replaces `employers_path`; `build_companies` takes the loaded rows, uses their `name`/`sector`, drops rows with `show = no` together with their postings, and `PROGRAM_EMPLOYER_NAMES` is deleted.

- [ ] **Step 1: Write failing tests:** `test_companies_csv_matches_old_lists` (after migration: 198 rows, 171 with boards, every `programs.yaml` employer id present, ids unique); `test_hidden_company_and_its_postings_are_dropped` in `test_build_site_data.py`; update the existing `build_site_data` tests to write a CSV fixture instead of YAML.
- [ ] **Step 2: Write and run the migration script,** commit `config/companies.csv`, then run the tests. Expected: new tests FAIL until readers switch.
- [ ] **Step 3: Switch the readers** (`cli.fetch_postings`, `cli` reference-recall at the second use, `build_site_data`, the three scripts) to `load_employers`/`load_companies`; delete `config/employers.yaml` and `PROGRAM_EMPLOYER_NAMES`; update the README and TODO mentions.
- [ ] **Step 4: Run** the full suite, `ruff`, `mypy`, regenerate `site/public/data`, and confirm `companies.json` still has 198 companies with the same names and open counts as before (compare against `git show HEAD:site/public/data/companies.json`).
- [ ] **Step 5: Commit** `git add -A config scripts pipeline tests README.md TODO.md site/public/data && git commit -m "Move the company list to config/companies.csv"`.

### Task 7: Researched hiring windows

**Files:**
- Modify: `pipeline/hiring_window.py`, `pipeline/build_site_data.py`, `site/lib/types.ts`, `site/components/WindowStrip.tsx`, `site/components/CompanyTable.tsx`, `site/app/companies/[slug]/page.tsx`, `site/sample-data/companies.json`
- Test: `tests/test_hiring_window.py`, `tests/test_build_site_data.py`

**Interfaces:**
- Produces: `researched_window(months: list[int]) -> dict[str, Any]` returning `{"months": [0|1 × 12], "start": int, "end": int, "n_dates": 0, "years": [0, 0], "source": "researched"}` (start/end are the first and last month of the run, wrapping allowed). `hiring_window` results gain `"source": "postings"`. Each company in `companies.json` gains `website`, `careers_url`, `hiring_note`, `hiring_source` (strings, `""` when blank); `notes` is never included. A company with `hiring_months` uses `researched_window`; otherwise the postings-based window. `badge()` is unchanged and works on either.
- TypeScript: `HiringWindow` gains `source: "researched" | "postings"`; `Company` gains the four strings.

- [ ] **Step 1: Write failing tests:** `researched_window([9, 10])` → months flags and `(9, 10)`; `researched_window([11, 12, 1])` → `(11, 1)`; a company row with `hiring_months = "Sep-Oct"` and 5 postings in March gets the researched window (source `researched`) and its basis says "researched"; a researched company with no board and no postings is still in `companies.json`; `companies.json` never contains the `notes` text.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** in the pipeline; update `basis` so a researched window reads "Researched" and a postings window keeps "from N postings, YYYY".
- [ ] **Step 4: Site.** `WindowStrip` shades researched months evenly with a caption "Researched: Sep–Oct"; postings windows keep "Usually hires …"; `CompanyTable` and the home sidebar show the strip when `window` is non-null (researched windows included); the company page shows the note, "Source: <hiring_source>" (a link when it starts with `https://`), and the website and careers links. Update the sample data (one researched company, one with links).
- [ ] **Step 5: Run** all Python checks, `npm run typecheck`, `build`, `build:sample`, `impeccable detect` on `/companies/` and a company page at both widths (expect 0), and screenshots.
- [ ] **Step 6: Commit** `git add -A pipeline tests site && git commit -m "Show researched hiring months, labelled, ahead of the postings-based calendar"`.

### Task 8: Create the sheet, wire it up, document

**Files:**
- Create: `docs/decisions/0010-company-sheet-and-published-descriptions.md`
- Modify: `docs/deploy.md` (how to edit the sheet, what the columns mean, what happens on a bad edit), `README.md` ideas list, `docs/kanban.md`
- External: a new Google Sheet in Lio's Drive; repository variable `COMPANY_SHEET_CSV_URL`

- [ ] **Step 1: Create the sheet** with the Drive connector from `config/companies.csv` (converted to a Google Sheet named "Co-op Radar companies", one tab named `companies`), then read it back with the Sheets connector and check the row count (198) and header.
- [ ] **Step 2: Share it:** "anyone with the link can view", and edit access for Lio and Ei Htoo (look up Ei's address in `docs/team.md`; if it isn't there, ask Lio rather than guessing). Freeze the header row and set data validation on `show` (yes/no) and `board_type` if the connector allows.
- [ ] **Step 3: The CSV URL** is `https://docs.google.com/spreadsheets/d/<id>/export?format=csv&gid=<gid>`. Set it as the repository variable `COMPANY_SHEET_CSV_URL` if the GitHub tools allow it; otherwise give Lio the exact value and the one place to paste it (Settings → Secrets and variables → Actions → Variables). Do not put it in a secret.
- [ ] **Step 4: Try the fetch** with `docs.google.com` allowed for this session (propose the host change if needed) or, failing that, trigger the daily workflow with `workflow_dispatch` once the branch is merged and read its `sync-companies` log line. State plainly which of the two was done.
- [ ] **Step 5: Write ADR 0010** (descriptions published sanitised, only for open postings; sheet as source of truth with a committed copy; what it supersedes in ADR 0002 and the employers-file convention) and the `docs/deploy.md` section.
- [ ] **Step 6: Final checks** (`pytest -q`, `ruff`, `mypy pipeline`, `npm run typecheck`, `build`, `build:sample`), then commit `git add -A docs README.md && git commit -m "Document the company sheet; ADR 0010"` and push.
