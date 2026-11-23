# Board redesign: jobs first, companies, hiring windows

Status: draft for Lio's approval · 2026-11-23

## Why

Lio dislikes the current site. It is "too plain and too AI slop". He wants it
to feel like speedrun-talent-network.com, but for Canadian tech co-ops and
internships. A student who lands on the site should start **browsing jobs at
once**: the welcome *is* the job board, and there is no separate landing page.
He also wants a **Companies** section, and a **hiring window** for every company
so students know when to watch for applications.

## Goals

1. `/` is the job board. It has a bold headline and a one-line pitch, then
   search, filter chips with counts, shortcut cards ("collections"), and a
   dense list of job rows. The first job row is visible above the fold on a
   1440×900 desktop.
2. `/companies` is a grid of every company we know of. Each company shows a
   12-month hiring-window strip and a status badge: *open now* (it has open
   postings), *opens ~Mon* (an expected window is coming), or *quiet*.
3. `/companies/[slug]` is one company's page. It shows the company's current
   postings, its hiring-window timeline with the dates the window was built
   from, and its program-watch history where one exists.
4. The visual design is done with the impeccable skill. Its outputs are
   PRODUCT.md, a new DESIGN.md, and a reviewed comp, which Lio approves before
   pages are built. Distinctive and confident; not a copy of Speedrun's look.
5. The evidence that sets us apart stays. Each term and duration still links
   to the words it came from, inside an expandable row.

## Non-goals

- Accounts, sign-in, saved jobs and alerts. A "Get notified" box may appear,
  but it links to the existing RSS/digest plans and collects no emails yet.
- Salary data. Canadian internship postings rarely state pay, so the row has
  no pay column.
- Logos fetched at runtime from a third-party service, which would leak
  visitors' IPs. A row's logo is a coloured letter tile for now.
- Adding new posting sources. That is a separate decision (ADR + Lio's OK).

## Anti-goals (a failure even if it works)

- Looking like a template: a purple gradient hero, uniform cards, generic
  icons, centred everything. Impeccable's slop checks must pass.
- Hiding the evidence, or showing a hiring-window guess as if it were a fact.
  Every window shows what it is based on ("from 6 postings, 2025–26").
- A slow board. The page is a static export, with no client fetch before the
  first rows render.

## Constraints

- Next.js 16 static export on the Vercel free tier. Tailwind v4 and Fontsource
  are already installed. No new UI component library.
- The site reads JSON written by `pipeline/build_site_data.py`
  (`site/public/data/*.json`). New data is added there; `site/lib/types.ts`
  is kept in sync.
- **The negarprh list (ADR 0007).** The friend said Lio may use and extend
  it, but the repo has no license. Before any company or date derived from
  it is *published*, there must be written permission: a LICENSE file in the
  repo or a public comment from the owner. A new ADR (0010) then supersedes
  0007. Until then, the build uses only our own data (171 employer boards,
  30 program pages, our first-seen dates), and the code reads the list behind
  one switch.
- Public, permitted sources only. Never LinkedIn, Indeed, Glassdoor, Reddit,
  or Workday career sites.
- Must work at phone width (375px) and in light and dark mode, with WCAG AA
  contrast and keyboard-usable filters.

## Approaches considered

- **A. Rebuild the structure, Speedrun-style (chosen by Lio).** New jobs
  board, companies index and company pages. A pipeline step derives the
  hiring windows. Most of `site/` is rewritten. This fixes the layout, not
  just the paint.
- **B. Reskin the current pages** with impeccable's critique/bolder/polish,
  then add Companies. Cheaper, but it keeps the layout Lio dislikes.
- **C. Rebuild on a component kit (shadcn etc.).** Fast, but it pushes
  toward the generic look Lio wants to escape. Dropped.

## Design decisions

### Data: `companies.json` (new, from `build_site_data.py`)

One record per company:

- `slug`, `name`, `sector`, `board_url`
- `open_count`, `postings` (ids)
- `program_id` (if it is program-watched)
- `window` (below)

Companies come from `config/employers.yaml` and `config/programs.yaml`. Once
permission exists, companies that appear only in the negarprh list are
added too.

### Hiring window

For each company, collect the dates its student postings first appeared:

- our `first_seen` from the data branch history;
- the negarprh "Date Posted" for 2026 and 2027 rows (only behind the
  permission switch);
- program pages' `expected_open` (already in `programs.yaml`).

Group the dates by month-of-year. The **window** is the shortest run of
months holding at least 60% of the dates, wrapping across December. It is
shown as a 12-cell strip with the cells shaded by how many dates fall in each
month. The record stores `months: int[12]`, `window_start`, `window_end`,
`n_dates`, `years`, and `basis` (which sources).

- With fewer than 3 dates, no window is drawn. The page says "Not enough
  history yet."
- The badge is *open now* if `open_count > 0`. It is *opens ~Mon* if today
  falls within the 2 months before `window_start`. Otherwise it is *quiet*.

### Pages

- **`/` (Jobs):**
  - a header and a one-line pitch;
  - a search box (title/company/city, client-side);
  - filter chips with live counts (term, province, track, duration,
    remote);
  - collections cards ("New this week", "Summer 2027", "8-month co-ops",
    "Ontario", "Remote"), which are presets of the same filters, kept in
    the URL query;
  - a sort (newest, company A–Z);
  - the rows. Each row: letter tile · title · "Company · City · Term" ·
    duration chip · "3d" age · "Apply →". Clicking the row expands its
    evidence quotes.
  - Pagination is "show more" in batches of 50.
- **`/companies`:** search, a filter by status, and a grid of company cards:
  name, sector, open count, window strip and badge. Sorted by open now,
  then soonest opening.
- **`/companies/[slug]`:** a header with the badge, a large window strip
  with its basis line, open postings (the same row component), and program
  watch changes.
- **`/programs` and `/about`** stay. They are restyled with the new system,
  with no content changes.
- **Nav:** Jobs · Companies · Programs · About, plus a count line ("412 open
  roles · 171 companies"), as on Speedrun.

### Visual design process (impeccable)

1. Run `impeccable init` to write PRODUCT.md (audience: Canadian
   co-op/intern students; job: find and apply before windows close).
2. Run `impeccable shape`/craft to set a direction and comp for `/` and
   `/companies`, then show it to Lio. **Lio approves the comp before page
   builds start.**
3. Build, then run `impeccable critique` and `audit` and fix what they find.
   The finish reviewer runs on the result.
4. Run the `impeccable-documenter` to rewrite DESIGN.md from the shipped
   site. The old evidence-ledger DESIGN.md is replaced.

## Left to the builder

- Component split, state handling for filters (URL query), and the font
  pairing within the approved comp.
- The exact collection presets, based on what the data actually has.
- Letter-tile colours (a deterministic hash of the name, contrast-checked).

## Open items for Lio (not blocking the build)

- Get the friend's written permission (a LICENSE or a comment) so the
  negarprh companies and dates can go live.
- Look at the comp when it's ready.
