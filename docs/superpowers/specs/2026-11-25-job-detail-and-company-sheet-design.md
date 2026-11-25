# Job detail pages and a company spreadsheet

Status: draft for Lio's approval · 2026-11-25

Two parts, built in this order. Part A has no outside dependency; Part B adds Google Sheets.

## Why

- **A.** Today a posting is only a row. A student can't judge a role without leaving, and
  Speedrun-style boards open a detail page with the full posting and an Apply button. Lio wants
  clicking a job to open that page, with a button that sends the student to the employer's
  application link.
- **B.** The company list lives in two YAML files that only Lio's coding session edits. Lio wants
  to add and delete companies himself, and to research each company's details and hiring months,
  in a spreadsheet.

## Goals

1. Clicking a job opens `/jobs/<id>/` with: back link, company tile, title, chips (location, term,
   length, work mode), an **Apply** button at the top and again at the bottom, our verified term
   and length with the highlighted quotes, and the employer's full description.
2. Apply opens the employer's own application link in a new tab. The site never hosts applications.
3. One Google Sheet is the source of truth for the company list. Lio and Ei add, edit and delete
   rows. The daily run reads it and the site updates the next morning.
4. Hiring months that Lio researches show on the company page and in the strips, labelled
   *researched*. Where a company has none, the calendar built from postings is used, labelled
   *from postings*.

## Non-goals

- Applying on our site, accounts, saved jobs.
- Editing postings in the sheet. Postings still come only from the pipeline.
- Moving the 30 program-watch pages (`config/programs.yaml`) into the sheet. They stay in the repo
  because each was checked by hand for fetchability.
- Real-time updates. The daily run is the refresh.

## Anti-goals (a failure even if it works)

- Employer HTML running unsanitised on our domain.
- A bad spreadsheet edit (cleared sheet, wrong column, a typo'd board token) taking the site or
  the daily run down.
- Showing a researched hiring window as if it were measured. It is always labelled with where it
  came from.
- Committing full daily API responses to `main` (ADR 0002 rejects this).

## Constraints

- Public, permitted sources only; the sheet holds only public information. No secrets: the
  pipeline reads the sheet through a view-only link, so there are no credentials in the repo or
  in Actions.
- Next.js static export on the Vercel free tier. One page per open posting (about 130) is fine.
- Never invent numbers. A researched window is Lio's data and says so.
- Existing evidence quotes, plates and the timetable design (DESIGN.md) are reused.

## Approaches considered

**Where the description text comes from (Part A)**

- **A1. Commit sanitised descriptions of *open* postings to `main` (chosen).** About 130 files,
  rewritten only when the text changes and deleted when a posting closes. Git stores only the
  changes, so growth is the new and edited postings, not the whole set each day. Vercel builds
  from `main`, so it just works.
- A2. Read them from the `data` branch at build time. Vercel builds only the production branch,
  so it can't see the orphan branch. Dropped.
- A3. Fetch from the employer APIs in the visitor's browser. Leaks visitors' IPs to third
  parties, hits CORS limits, breaks when an employer changes the feed. Dropped.

**How the sheet reaches the site (Part B)**

- **B1. Live Google Sheet read by the daily run, with a committed copy (chosen by Lio).** The run
  downloads the sheet as CSV through a "anyone with the link can view" URL, validates it, and
  writes `config/companies.csv` to `main`. Everything else reads the committed CSV. A failed
  fetch or failed validation keeps the last good copy.
- B2. Sheet as a working copy that Claude loads into the repo on request. Safer, but manual.
- B3. CSV edited in the repo. No Google dependency, less comfortable. Both were offered; Lio
  picked B1.

## Design

### Part A: job detail pages

- **Data.** `build_site_data.py` also writes `site/content/descriptions/<id>.html` for each open
  posting, from the stored description. The files are **sanitised in the pipeline** with an
  allowlist (paragraphs, line breaks, lists, bold/italic, headings mapped down to `h3`/`h4`,
  links with `rel="noopener noreferrer nofollow"` and `https:` only). Scripts, styles, event
  handlers, `javascript:` URLs, images and iframes are dropped. Output is deterministic, so an
  unchanged posting produces no diff. Files for closed postings are deleted.
- **Route.** `/jobs/[id]/`, one static page per open posting via `generateStaticParams`. The id is
  the existing 16-hex posting id. A posting that has closed returns the site's 404, which links
  to its company page.
- **Page.** Layout follows Lio's screenshot, in the timetable design: narrow reading column
  (about 70ch), company tile and "Company · Hiring" label, title, chips, Apply, facts block
  (term and length with plates and quotes, "length not stated" where true), description,
  Apply again, then a footer line: "Posting text from <Company>'s <Greenhouse|Lever|Ashby> job
  board, first seen <date>. Always confirm on the employer's site."
- **Rows.** The title in each row links to the detail page, and the whole row is the click
  target (the Apply link inside stays separate and goes straight to the employer). The "source"
  toggle in rows is removed, since the quotes now live on the detail page.
- **Company page** rows link to detail pages the same way.

### Part B: the company sheet

- **Sheet.** A new Google Sheet in Lio's Drive, seeded by Claude from the current 198 companies,
  shared view-by-link, edit access for Lio and Ei only. One tab, `companies`, one row per company.

  | Column | Meaning |
  |---|---|
  | `id` | Stable key. Don't change it for an existing company. New rows get a lowercase slug. |
  | `name`, `sector` | Shown on the site. |
  | `show` | `yes` or `no`. `no` hides the company and its postings but keeps the row. |
  | `website`, `careers_url` | Optional links shown on the company page. |
  | `board_type`, `board_token` | `greenhouse`, `lever` or `ashby` and its token. Blank means no postings feed. |
  | `hq_province` | Optional. |
  | `hiring_months` | Researched months, e.g. `Sep-Oct` or `9,10`. |
  | `hiring_note` | Free text, e.g. "Summer roles post in September." |
  | `hiring_source` | URL or short note on where Lio found it. |
  | `notes` | Internal; never published. |

- **Sync.** New `pipeline/company_sheet.py` and a step at the start of `daily.yml`: download the
  CSV, validate, and if it passes write `config/companies.csv` (committed with the daily data).
  `fetch-postings` and `build_site_data.py` read `config/companies.csv` instead of
  `employers.yaml`. The sheet URL is a public config value, not a secret.
- **Validation** (all must pass or the run keeps the last good copy, logs the reason in
  `data/run_log.jsonl`, and the workflow run is marked failed so it is visible):
  required columns present, `id` unique and URL-safe, `show` is yes/no, `board_type` known,
  months parse, links are `https:`, and the new row count is at least 50% of the previous one
  (guards against a cleared or sorted-over sheet).
- **Add.** A row with a board token is checked by the existing board check on the next run. If the
  board doesn't answer or has no Canadian jobs, the company is still listed, without postings,
  and the run log says why. A row with no token is a research-only company.
- **Delete.** Removing a row removes the company and its postings from the site on the next run.
  Raw history on the `data` branch is untouched. Use `show = no` to hide without losing the row.
- **Migration.** `config/employers.yaml` becomes `config/companies.csv`; its `verified` dates
  and sources move into `notes`. `scripts/check_board_tokens.py` reads the CSV. ADR 0010 records
  the change.
- **Hiring calendar.** `companies.json` `window` gains `source` (`"researched"` or `"postings"`),
  plus `note` and `source_url` when researched. Researched months have no counts, so the strip
  shades them evenly. The strip caption reads "Researched: Sep–Oct" or "From 6 postings, 2026".
  The company page shows the note and a link to the source. `badge()` (open / soon / quiet) uses
  whichever window applies.

## My calls (change any of them)

- Descriptions of closed postings are deleted, and old detail links 404 to the company page.
- A row's whole area is clickable, and the in-row "source" toggle goes away.
- Programs stay in `config/programs.yaml` for now.
- The 50% row-count guard, and `show = no` as the safe way to hide a company.
- `notes` is never published; every other column may be.
- New ADR 0010 supersedes the parts of ADR 0002 and the employers file convention that change.

## Left to the builder

- The sanitiser (small allowlist on the standard library parser, or a vetted library) and its
  tests with hostile input: `<script>`, `onerror=`, `javascript:` links, nested tags,
  unclosed tags, huge posts.
- Month parsing rules for `hiring_months` ("Sep-Oct", "Sep to Oct", "9,10", "Nov-Jan" wrapping).
- The exact Google Sheets export URL and how to test the fetch (this cloud session cannot reach
  Google; the allowed hosts need `docs.google.com`).
- Page copy and the 404 page.

## Open items for Lio

- Confirm the columns above, or add any you want.
- Share the sheet "anyone with the link can view" (Claude can do this when it creates the sheet).
- Decide whether Ei gets edit access.
