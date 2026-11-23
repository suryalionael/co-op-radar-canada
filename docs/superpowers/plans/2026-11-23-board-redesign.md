# Board Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the site into a jobs-first board (Speedrun-style) with a
Companies section and a hiring window for every company, designed with
impeccable.

**Architecture:** The pipeline gains a pure `hiring_window()` function, and
`build_site_data.py` writes `companies.json` beside the existing JSON. The
Next.js static site is rebuilt around three pages (`/`, `/companies`,
`/companies/[slug]`) that share a row component and a window-strip component.
The visual system comes from impeccable (PRODUCT.md → comp → build → critique
and audit → DESIGN.md).

**Tech Stack:** Python 3.12, DuckDB, pytest; Next.js 16 static export,
Tailwind v4, Fontsource; impeccable skill.

**Spec:** `docs/superpowers/specs/2026-11-23-board-redesign-design.md`

## Global Constraints

- Static export only. No client fetch before the first rows render. No new UI component library.
- Light and dark mode. WCAG AA contrast. Works at 375px wide. Keyboard-usable filters.
- No runtime third-party requests: no logos or fonts from a CDN at view time.
- The negarprh-derived companies and dates stay off until written permission exists (`REFERENCE_PUBLISHABLE = False`).
- A hiring window needs at least 3 dates. The window is the shortest run of months holding ≥60% of them, wrapping across December.
- Badges: `open` if open_count > 0. `soon` if today is within the 2 months before window_start. Else `quiet`.
- Commits are authored by Lio, with no Claude co-author trailers (Lio's instruction, 2026-11-23).

## Review Focus

- A company with zero postings and no program → still listed, badge quiet, "Not enough history yet". Test in Task 1/2.
- Dates that cluster across New Year (Nov, Dec, Jan) → the window wraps (start 11, end 1), not 1–12. Test in Task 1.
- A filter combination with no results → a clear empty state with a reset link, not a blank list. Checked in Task 4.
- A very long title or company name at 375px → wraps, no horizontal scroll. Checked in Task 6 audit.
- `postings.json` empty (first deploy) → the board shows its existing "No postings yet" message. Checked in Task 4.

---

### Task 1: `hiring_window()`

**Files:** Create `pipeline/hiring_window.py`; test `tests/test_hiring_window.py`

**Interfaces:**
- Produces: `hiring_window(dates: list[date]) -> dict | None`. It returns
  `None` when there are fewer than 3 dates. Otherwise it returns
  `{"months": list[int] (12 counts, Jan first), "start": int (1–12), "end": int (1–12), "n_dates": int, "years": [min_year, max_year]}`.
- Produces: `badge(window: dict | None, open_count: int, today: date) -> Literal["open", "soon", "quiet"]`

- [ ] Tests:
  - 2 dates → None
  - dates in Sep×4, Oct×2, Mar×1 → start 9, end 10
  - Nov, Dec, Jan, Jan → start 11, end 1
  - `badge(None, 3, …) == "open"`
  - `badge(win(start=9), 0, date(2027,7,15)) == "soon"`
  - `badge(win(start=9), 0, date(2027,3,1)) == "quiet"`
- [ ] Implement: try every start month and length 1..12 in order of length, and take the first run (ties broken by the largest count) with sum ≥ 0.6·n.
- [ ] Check `pytest tests/test_hiring_window.py` passes; commit.

### Task 2: `companies.json`

**Files:** Modify `pipeline/build_site_data.py`, `tests/test_build_site_data.py`, `site/lib/types.ts`, `site/lib/data.ts`

**Interfaces:**
- Consumes: `hiring_window`, `badge`.
- Produces: `companies.json` as a list of `Company`:
  `{slug, name, sector, board_url, open_count, posting_ids, program_id|null, window|null, basis: string, badge}`,
  sorted by badge (open, soon, quiet), then open_count desc, then name.
  `meta.counts.companies` is added.
- Produces (TS): a `Company` type, `getCompanies()`, and `getCompany(slug)`.

- [ ] Test: a building fixture with two employers (one with 3 historic postings, one with none) and one program. Assert both are present, the program is linked by `employer_id`, `basis` reads "from 3 postings, 2026", and the empty one has `window is None`.
- [ ] Implement:
  - Dates come from `first_seen` of *all* student postings in Canada (any status), plus the program's `expected_open` when set.
  - Companies come from employers.yaml plus program employer_ids not in it, using the program name as the company name.
  - `slug = id`.
  - `board_url` is derived from board_type/token. Use the same URL formats as the sources modules.
- [ ] Run the full `pytest`, `ruff` and `mypy`; regenerate `site/public/data`; commit.

### Task 3: Design direction (impeccable)

**Files:** Create `PRODUCT.md`; the comp goes in the scratchpad and is shown to Lio.

- [ ] Run impeccable `init` to write PRODUCT.md (audience, job, tone, anti-references: generic AI SaaS, purple gradients).
- [ ] Run impeccable `shape` to set the direction (type, colour, density, signature element = the window strip). Build a throwaway HTML comp of `/` and `/companies` with real data and screenshot it at 1440 and 375.
- [ ] **Stop:** send the comp to Lio for approval. Do not build pages until he approves.

### Task 4: Jobs board `/`

**Files:** Rewrite `site/app/page.tsx` and `site/app/globals.css`. Replace `PostingsExplorer.tsx` and `PostingEntry.tsx` with `JobBoard.tsx` and `JobRow.tsx`. Keep `EvidenceQuote.tsx`. Update `Nav.tsx` and `layout.tsx`.

- Filters (term, province, track, duration, remote), search, sort and collection presets are kept in the URL query.
- "Show more" adds 50 rows at a time. The empty-filter state offers "Clear filters".
- [ ] Run `npm run typecheck` and `npm run build`; take screenshots at 1440 and 375, light and dark; commit.

### Task 5: Companies `/companies` and `/companies/[slug]`

**Files:** Create `site/app/companies/page.tsx`, `site/app/companies/[slug]/page.tsx` (with `generateStaticParams`), `site/components/WindowStrip.tsx` and `site/components/CompanyCard.tsx`.

- [ ] Build; screenshots; commit.

### Task 6: Critique, audit, apply

- [ ] Run impeccable `critique` and `audit` on `/`, `/companies`, a company page, `/programs` and `/about`, at both widths and in both themes.
- [ ] Fix every material finding; restyle `/programs` and `/about` with the new tokens; commit per batch.
- [ ] Run the impeccable finish reviewer, then the documenter to rewrite DESIGN.md; commit.
- [ ] CI checks (`ruff`, `mypy`, `pytest`, site typecheck and build) all pass; push; open a PR to main.
