# Co-op Radar Canada — Project Brief

A handoff document for building Co-op Radar Canada from scratch. It covers the goal, scope, stack, architecture, data model, every data source, the phased build plan with acceptance criteria, and the rules the project must follow.

Owner: Lionael Surya (Lio), Honours Bachelor of Data Science & Analytics, Seneca Polytechnic, Toronto.
Written: October 28, 2026. Revised: October 28, 2026 (see section 0).

---

## 0. What changed in this revision

- **Added Phase 0, a coverage spike.** How many Canadian student postings Greenhouse, Lever and Ashby actually provide is the project's biggest unknown. It is now measured first, against thresholds written down before the numbers come in.
- **Moved program watch into v1 and hiring news into v2.** Program watch is cheap and most valuable during the Summer 2027 recruiting window (roughly September to January). News classification is the most work and the least actionable for a student.
- **Trimmed v1 to fit the time budget.** At 3 hours a week, Oct 28 to Dec 13 is about 20 hours. The issue form and weekly digest move to v2. The weekly market page moves to v3, since it needs weeks of data to mean anything.
- **Replaced "commit every raw snapshot to the repo."** Git keeps every version forever, so compressing old files never shrinks the repo. Section 4.1 has the new storage design.
- **Added a guard so a failed fetch never closes postings.**
- **Duration is now a list of allowed options**, because postings often say "4, 8 or 12-month terms."
- **Evaluation reports counts and confidence intervals**, not just a precision number.
- **Sources clarified.** LinkedIn is an outbound link only, never a source. Google News RSS is pending a terms check. Canadian press-release wires are added as candidates.
- **Added a coverage playbook (section 5.5)** and reframed the product so it stays useful even if posting coverage is thin.
- **News is now focused on student opportunities:** co-op, internships, summer jobs, student programs and the funding behind them. Sections 5.3, 6 and 7 have the new query list, pre-filter and signal classes.

---

## 1. What this is

A free, public website for Canadian students looking for co-ops and internships. It answers three questions:

1. **What is open right now?** Verified postings with the term, duration and province pulled out, so a student can filter to "Summer 2027, 4 months, Ontario" in one click.
2. **When do the big student programs open?** Program watch flags the day a student-program page changes, and a recruiting calendar records when each program opened.
3. **What student opportunities are in the news?** News about co-op, internship, summer-job and other student programs (new programs, intake dates, wage subsidies, cuts), matched to employers and programs where possible, and clearly labelled as a hint, not an opening.

**Positioning:** verified postings from Canada's tech employers, plus the one place that tracks when the big student programs open. The site does not claim to list every co-op in Canada, and the About page says so.

### Why it should exist

- Existing GitHub internship trackers are US-heavy and rarely state the work-term duration. Canadian co-op students need duration and term above all, because their schools only approve specific term lengths.
- Many Canadian student programs announce *dates* long before postings (for example, "summer roles open December 1"). Nobody collects those dates in one place.
- The largest Canadian employers (banks, insurers, utilities, governments) post on systems with no public API, but they announce their student programs on public pages. Program watch covers exactly the employers the posting pipeline cannot.
- Lio has run a daily manual co-op search since September 2026 and already knows the hard part: verifying term and duration from the posting itself.

### Why it matters for the owner

This is the flagship portfolio project for Lio's Summer 2027 co-op search. It shows data engineering (scheduled ingestion, snapshots, idempotent pipelines), data science (an extractor and a classifier with published precision and recall), and software engineering (a public site real people use). "Real students used it" is the resume line no tutorial project can give, which means the site must launch before winter break, while students are still applying.

---

## 2. Hard constraints

These are non-negotiable. Do not trade them away for features.

1. **$0 to run.** GitHub Actions and GitHub Pages (or Vercel's free tier) only. No paid APIs, no database server, no paid hosting. Any LLM use is limited to a one-time evaluation run, never the production pipeline.
2. **Public, permitted sources only.** Use official public job-board APIs, RSS feeds and open-data APIs. **No scraping of LinkedIn, Glassdoor, Indeed or Reddit.** Their terms forbid it. These sites may appear only as outbound links a student clicks (for example, a LinkedIn job search for an employer); nothing is ever fetched from them. Respect `robots.txt` and rate-limit every source.
3. **News is stored as metadata only:** headline, outlet, published date, URL. Never store or republish article text.
4. **Every fact is traceable.** Each posting and news item keeps its source URL and the date it was fetched. Each extracted field (term, duration, province) keeps the text span it came from.
5. **Explainable over clever.** Rules and simple models first. A more complex method replaces a simpler one only if it wins on a published evaluation.
6. **Honest labelling in the UI.** If duration could not be verified, the site says "duration not stated", not a guess. News is labelled as a hint, not an opening.

---

## 3. Stack

| Layer | Choice | Why |
|---|---|---|
| Ingestion and processing | Python 3.12, `httpx`, `feedparser`, `pydantic` | Owner's strongest language; pydantic validates every record at the boundary |
| Storage | Compact daily snapshots on an orphan `data` branch (section 4.1); small processed Parquet files on `main`; DuckDB for queries and builds | No server, full history, repo stays small |
| Scheduling | GitHub Actions cron | Free for public repos |
| Text classification | scikit-learn (TF-IDF + logistic regression) vs keyword rules | Matches the owner's coursework (BDM550 Text Mining); explainable |
| Tests and quality | pytest, Ruff, mypy | Owner already uses all three |
| Frontend | Next.js (static export) + TypeScript + Tailwind CSS | Owner's main web stack; static export means no server |
| Search on the site | Client-side over a prebuilt JSON index (e.g. MiniSearch or Fuse.js) | No backend needed |
| Hosting | GitHub Pages or Vercel free tier | Free |
| Analytics | Vercel Web Analytics (free) or GoatCounter | Needed for the "people used it" resume line |
| Submissions | GitHub issue form, validated by an Action | Lets anyone add postings without a backend |

If a choice here turns out not to work in practice, change it and record why in `docs/decisions/` (see section 9).

---

## 4. Architecture

```
               ┌──────────────── GitHub Actions (daily cron) ────────────────┐
               │                                                              │
Job boards ──► fetch_postings ──► raw snapshots ──► extract (term, duration, ─┤
(Greenhouse,                     `data` branch       province, track)         │
 Lever, Ashby,                   (section 4.1)                                │
 issue form)                                                                  ▼
                                                                    data/processed/postings.parquet
Program pages ──► fetch_programs ──► fingerprint + diff ──► data/processed/program_watch.parquet
                                                            data/processed/program_changes.parquet
                                                                                 │
News feeds ──► fetch_news ──► raw snapshots ──► dedupe ──► employer match ──► classify   (v2)
(GDELT, BetaKit,                                                                 │
 approved wires)                                                                 ▼
                                                                    data/processed/news.parquet
                                                                                 │
                                         build_site_data (DuckDB) ◄──────────────┘
                                                   │
                                                   ▼
                                    site/public/data/*.json  ──► Next.js static export ──► Pages/Vercel
```

Principles:

- **Raw is immutable.** Every fetch writes a dated raw snapshot. Processing reads raw and rewrites processed outputs from scratch, so re-running a day never double-counts.
- **Idempotent by key.** Postings key on `(source, board_token, source_job_id)`. News keys on normalized URL.
- **One job per concern** in the workflow (postings, programs, news, build), so one failing source doesn't block the site.
- **Fail loudly, publish safely.** If a source fails, the Action logs it to `data/run_log.jsonl` and the site keeps the last good data with a "last updated" date per source.
- **Never close on a failed fetch.** A board fetch counts as failed if it errors, times out, or returns zero jobs when it had jobs on the last successful fetch. A posting becomes `closed` only after it is missing from **two consecutive successful** fetches of its board. A failed fetch leaves every posting from that board unchanged.

### 4.1 Raw storage design

Daily full API responses with description HTML, committed to `main`, would grow the repo by megabytes a day, and git history keeps every version forever. Instead:

1. **Keep a loose Canada filter at fetch time.** Store a posting if its location, title or description mentions Canada, a Canadian province or territory, a Canadian city from the province map, or "remote". This is a deliberate superset so a better province extractor later never lacks data. Record the filter in ADR 0002.
2. **Store metadata daily, descriptions once.** Each day writes `raw/postings/YYYY-MM-DD.jsonl.gz` with one line per posting (all fields from the API except the description, plus `description_hash`). Each unique description is written once to `raw/descriptions/{hash}.html.gz`. An unchanged description is never stored twice.
3. **Raw lives on an orphan `data` branch**, not `main`. The daily Action checks out both. `main` holds code, config, labels, small processed outputs (overwritten each run) and the site.
4. **Size budget.** Phase 0 measures bytes per day after filtering. If the projected size passes 1 GB a year, roll each month into one Parquet file and squash that month's daily commits on the `data` branch, recording the change in an ADR.

---

## 5. Data sources

Verify each endpoint's current format and terms before building against it. The endpoints below are the known public patterns as of this writing.

### 5.1 Postings (v1)

| Source | Endpoint pattern | Notes |
|---|---|---|
| Greenhouse | `https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true` | Public JSON, includes full description HTML |
| Lever | `https://api.lever.co/v0/postings/{company}?mode=json` | Public JSON |
| Ashby | `https://api.ashbyhq.com/posting-api/job-board/{board_name}?includeCompensation=true` | Public JSON |
| GitHub issue form (v2) | Issues labelled `submission` | Validated by an Action, then reviewed |

**Seed list:** `config/employers.yaml`, starting with about 150 Canadian employers that use these three boards. Each entry has a canonical name, aliases, board type, board token, headquarters province and sector. Phase 0 decides whether to grow it (section 5.5).

**Known coverage gap:** most large Canadian banks, insurers and pension funds use Workday, which has no public posting API. Do not scrape Workday. Cover those employers through program watch and issue-form submissions, and state the gap plainly on the site's About page. Revisit only with a documented decision.

**LinkedIn:** not a source. Employer pages may include a plain LinkedIn job-search link for that employer. Nothing is fetched from LinkedIn.

### 5.2 Program watch (v1)

`config/programs.yaml`: about 30 student-program pages to fingerprint daily. Prioritize employers the posting pipeline cannot reach. Examples of the kind of page to include (verify current URLs before adding): FSWEP, Ontario Public Service student jobs, Big 5 bank student and campus pages, Manitoba Hydro summer students, BDC student jobs, Big 4 Canada student pages, BCI, BC Hydro, Hydro-Québec.

For each page: fetch, strip boilerplate (nav, footer, scripts, cookie banners), hash the main text, compare with the last hash. On change, append a `ProgramChange` record with the date and a short text diff, and flag it on the site as "this page changed on <date>". Also allow a manually entered `expected_open` date with a source URL (for example, a page that states its opening date). The change history feeds the recruiting calendar in v3.

### 5.3 Student-opportunity news (v2)

The news feed covers anything about student opportunities in Canada: co-op, internships, summer jobs, student programs, and the funding that pays for student hires. General business news (funding rounds, office openings) is out of scope unless the headline is about students.

| Source | Access | Status |
|---|---|---|
| GDELT DOC 2.0 API | `https://api.gdeltproject.org/api/v2/doc/doc?query=...&mode=artlist&format=json` with a Canadian-source filter | Approved |
| BetaKit RSS | Site RSS feed | Approved; startup internship and student-program news |
| Government of Canada news | Canada.ca news feeds (Open Government Licence) | Approved; Canada Summer Jobs, Student Work Placement Program, FSWEP and other federal programs |
| Canadian press-release wires | Newswire.ca (Cision), GlobeNewswire | Candidate: confirm feed availability and terms, then write an ADR |
| University newsrooms | RSS feeds from university news and co-op office pages | Candidate: confirm feeds and terms, then write an ADR |
| Google News RSS | `https://news.google.com/rss/search?q=...&hl=en-CA&gl=CA&ceid=CA:en` | Candidate: automated use is not clearly permitted. Check terms first; if still unclear, drop it and rely on GDELT and wires |

Store only: headline, outlet, published date, URL, query that found it, fetch date, and the terms it matched.

**Queries.** `config/news_queries.yaml` holds the search terms in four groups. This is a starting list; refine it after the first week of data and record big changes in an ADR.

```yaml
student_terms:      # who the opportunity is for
  - co-op student
  - co-op students
  - co-op placement
  - co-op program
  - work-integrated learning
  - summer student
  - summer students
  - summer jobs for students
  - student internship
  - internship program
  - paid internship
  - student jobs
  - student employment
program_names:      # named programs; verify each current name before adding
  - Canada Summer Jobs
  - Student Work Placement Program
  - FSWEP
  - Mitacs
opportunity_terms:  # signs the headline is about an opening, not just about students
  - hire
  - hiring
  - jobs
  - positions
  - placements
  - apply
  - applications
  - opens
  - launches
  - expands
  - funding
  - wage subsidy
french_terms:       # Québec coverage; French-language sources only
  - stage
  - stagiaire
  - emploi étudiant
  - emplois d'été
  - alternance travail-études
```

**Pre-filter (rules, before classification).** Keep a headline if it contains a program name, or a student term together with an opportunity term. Apply French terms only to French-language sources, since "stage" means something else in English. The pre-filter is deliberately broad and the classifier sorts out the noise. Expect plenty: headlines about international-student caps, tuition, student housing and student loans contain "student" but are not opportunities. They become `not_relevant` training examples.

**Headline only.** Because article text is never stored, every classification uses the headline alone. State this limit in `docs/evaluation.md`.

**Signal classes** (the example headlines are illustrative, not real):

| Class | Meaning | Example headline |
|---|---|---|
| `program_open` | An application window opens, or its dates are announced | "Applications open for 2027 summer student program" |
| `program_new` | A new or expanded co-op, internship or student program | "Firm launches paid internship program for students" |
| `funding` | Government money that pays for student hires | "Ottawa announces funding for student work placements" |
| `program_cut` | A student program paused, shrunk or frozen | "Province pauses summer student hiring" |
| `career_event` | Career fairs and recruiting events aimed at students | "Tech firms recruit at university co-op fair" |
| `not_relevant` | Mentions students but is not an opportunity | "Cap on international students tightened" |

**Expected volume.** Modest: likely a handful of relevant items a day at peak and fewer in summer, with most raw matches being noise. That is fine, because the digest only needs the few that matter. Program watch stays the more reliable signal that a specific program has opened; news complements it.

### 5.4 Market context (v3)

Statistics Canada Web Data Service (open API): monthly or quarterly job vacancies by province and industry. Confirm the exact table ID before building.

### 5.5 Coverage playbook

Use these levers only if Phase 0 calls for them, in this order. Each new source needs a terms check and an ADR before any code is written (see section 10).

| # | Lever | What it is | Status |
|---|---|---|---|
| 1 | Employer discovery | Build candidate lists from BetaKit, Communitech, MaRS, DMZ and Creative Destruction Lab portfolios; a script checks whether each company has a Greenhouse, Lever or Ashby board by trying likely board tokens | Approved: no new source |
| 2 | More ATS platforms | SmartRecruiters, Workable, Recruitee and Personio publish job feeds for their customers' career pages. Find and verify each documented public endpoint | Candidate: terms check + ADR per platform |
| 3 | Job Bank open data | Government of Canada job-posting data on the Open Government Portal (Open Government Licence) | Candidate for v3 market context; batch data, not live postings |
| 4 | Workday | Career sites run on undocumented endpoints, not a published API | Out of scope; revisit only with a documented decision, employer by employer |

Never sources: LinkedIn, Glassdoor, Indeed, Reddit.

---

## 6. Data model

All records validated with pydantic. Field names are the contract between pipeline and site.

### `Posting`
```
id                     str        # hash of (source, board_token, source_job_id)
source                 enum       # greenhouse | lever | ashby | submission
employer_id            str        # from employers.yaml
title                  str
url                    str
location_raw           str
province               enum?      # ON, BC, AB, QC, ... | REMOTE_CA | UNKNOWN
remote                 enum       # onsite | hybrid | remote | unknown
term                   str?       # e.g. "Summer 2027"
term_start             date?
term_end               date?
duration_options_months list[float]  # e.g. [4.0] or [4.0, 8.0, 12.0]; empty when not stated
duration_status        enum       # stated | inferred_from_dates | not_stated
track                  enum       # data_science | data_analytics | data_eng | ml_ai | software | business_ops | other
is_student_role        bool       # co-op / intern / student
evidence               dict       # field -> exact text span it was extracted from
description_hash       str        # key into raw/descriptions/
first_seen             date
last_seen              date
missed_fetches         int        # consecutive successful board fetches without this posting
status                 enum       # open | closed (closed only when missed_fetches >= 2)
deadline               date?
```

### `ProgramWatch`
```
program_id         str
employer_id        str
url                str
last_hash          str
last_checked       date
last_fetch_ok      bool
last_changed       date?
change_excerpt     str?
expected_open      date?
expected_open_src  str?
```

### `ProgramChange`
```
program_id         str
changed_on         date
change_excerpt     str
kind               enum       # content_change | manual_note
```

### `NewsItem` (v2)
```
id                 str   # hash of normalized URL
headline           str
outlet             str
url                str
published          datetime
fetched            datetime
query              str
language           enum  # en | fr
matched_terms      list[str]  # terms from news_queries.yaml found in the headline (evidence)
employer_ids       list[str]  # may be empty (government programs, employers not in the seed list)
program_ids        list[str]  # named programs matched, e.g. canada_summer_jobs; may be empty
signal             enum  # program_open | program_new | funding | program_cut | career_event | not_relevant
signal_method      enum  # rules | model
signal_score       float?
```

---

## 7. Build plan

Time budget: about 3 hours a week of project time. Oct 28 to Dec 13 is about 6.5 weeks (~20 h). Dec 14 to Jan 31 is about 7 weeks (~21 h). The holidays may add time, but the plan does not assume it. Ship each phase before starting the next, and when behind, cut from the phase's cut list rather than slipping the date.

### Phase 0 · Coverage spike (target: Nov 3, 2026, ~3 h)

1. Draft `config/employers.yaml` with the first ~150 employers. Rough is fine: name, board type, board token.
2. **Before running anything,** write `docs/decisions/0001-coverage-thresholds.md` with the decision table below. Adjust the numbers if you like, but only before seeing results.

   | Canadian student postings across seed boards | Decision |
   |---|---|
   | 100 or more | Build v1 as planned |
   | 40 to 99 | Build v1, and run employer discovery (5.5 lever 1) during v1 to reach ~300 employers |
   | Fewer than 40 | Before building the site: run employer discovery and the terms check for more ATS platforms (5.5 lever 2). Lead the site with program watch |

3. Write a throwaway script, `scripts/coverage_spike.py`, that fetches each board once (politely) and reports per employer and in total: boards that failed or returned 404 (wrong token), total postings, postings in Canada (loose location match), student postings in Canada (title matches intern, co-op, student or summer), how many of those mention a term or duration (quick regex), and bytes per board after the Canada filter (for the storage budget in 4.1).
4. Run it, add the results table to ADR 0001, and record the decision.

Late October is close to the peak for Summer 2027 postings, so this is near a best-case snapshot. A low count is a real signal; a high count may shrink by spring. Re-run the script monthly; the results feed the v3 coverage chart.

**Phase 0 acceptance criteria**
- ADR 0001 exists, with the thresholds committed before the results.
- Results table and decision recorded in the same ADR.
- Storage estimate recorded in ADR 0002.

### v1 · Verified postings and program watch (target: Dec 13, 2026, ~17 h)

1. Postings pipeline: daily Action, storage design from section 4.1, closed-status guard from section 4. (~4 h)
2. Rule-based extractor for term, duration, province and role track, with pytest cases. Rules, not an LLM, so it stays free and explainable. (~5 h)
3. Program watch for ~30 pages. **Start this by week 2** so the 7-day dry run finishes well before launch. (~2 h)
4. Hand-label postings in `data/labels/postings.csv` and publish extractor precision and recall per field in the README. Label every Canadian student posting up to 200. If fewer exist, label all of them and add non-student postings for the province and track fields. (~3 h)
5. Static site with search, filters (term, duration, province, track, remote), a "new this week" view, a program-watch panel ("changed on <date>", expected opening dates), and an About page that states the coverage gap. (~3 h)
6. Launch to Seneca students and with a LinkedIn post about the project; track visitors and GitHub stars.

**Extractor details**
- Term: regex over title and description for season + year ("Summer 2027", "May 2027 start", "Winter 2027"), and month ranges ("May–August 2027").
- Duration: explicit phrases ("4-month", "16 weeks", "four months", "8 months"). When a posting offers several lengths ("4, 8 or 12-month terms"), store all of them in `duration_options_months`. Convert weeks to months and round to the nearest whole month (16 weeks becomes 4), keeping the original phrase in `evidence`. Otherwise compute from stated start and end dates and mark `inferred_from_dates`; otherwise `not_stated`. Never guess from company norms.
- Province: map city names and province codes from the location field; handle "Remote, Canada" and multi-location postings.
- Track: keyword rules on title first, then description.
- Store the matching text span for every extracted field in `evidence`.

**v1 acceptance criteria**
- Daily Action runs green for 7 consecutive days.
- Duration extractor precision ≥ 0.95 on the labelled set (a wrong duration is worse than "not stated"), measured on postings where the extractor output a duration. Report it as counts with a 95% Wilson interval, for example "57/59 correct = 0.97 (95% CI 0.88–0.99)". If the lower bound is below 0.90, say so in the README. Report recall honestly whatever it is.
- Re-running the pipeline on the same day produces identical processed output.
- A test that simulates a failed or empty board fetch shows no postings closed.
- Program watch produces no false "changed" alerts from cookie banners, timestamps or rotating content over a 7-day dry run.
- Site loads and filters in under 2 seconds on a phone.
- Every posting card links to the original posting and shows "verified from posting text" or "duration not stated".
- The About page states what the site does not cover.

**Cut list if behind (in this order):** the "new this week" view, then the track filter, then program watch reduced to the 15 most important pages. Never cut the evaluation, provenance or honest labelling.

### v2 · Submissions, employer pages and student-opportunity news (target: Jan 31, 2027, ~21 h)

1. GitHub issue form for submissions, validated by an Action, then reviewed by hand. (~2 h)
2. Employer pages: open postings, program-watch status and news timeline side by side, plus a LinkedIn job-search link-out. (~2 h)
3. Weekly digest page and RSS: new Summer 2027 postings, programs that changed or opened, notable student-opportunity news. (~2 h)
4. Daily news pull using the queries in `config/news_queries.yaml` from GDELT, BetaKit, Canada.ca and any approved candidates, into dated snapshots, deduplicated by normalized URL and near-identical headline, then passed through the pre-filter in section 5.3. Google News RSS only if its terms check passes. (~3 h)
5. Match each headline to employers in the seed list using aliases (e.g. "RBC" / "Royal Bank") and to named programs (e.g. "Canada Summer Jobs"), with a test set of known false matches (e.g. "Apple" in a recipe headline). Headlines with no match still appear in the feed. (~3 h)
6. Hand-label 300 headlines that passed the pre-filter into the six signal classes, plus a random 100 that the pre-filter dropped, to estimate what it misses. If a class ends up with fewer than 20 examples, merge it into the nearest class and record the merge in an ADR. (~5 h)
7. Compare keyword rules with TF-IDF + logistic regression. Publish precision, recall and a confusion matrix. Keep whichever wins and document the decision. (~4 h)

**v2 acceptance criteria**
- Employer and program matching precision ≥ 0.9 on the labelled set, reported with counts.
- Pre-filter miss rate reported from the 100 dropped headlines.
- Classifier evaluation table published in `docs/evaluation.md`, with the chosen method justified.
- News feed has filters by signal type and province, and a visible note that news is a hint, not an opening.
- No article text anywhere in the repo or on the site.

**Cut list if behind:** ship items 1–5 by Jan 31 with rule-based signals (marked `signal_method = rules`), and move items 6–7 to Feb 28. The classifier comparison is the strongest data-science line on the resume, so it can slip but must not be dropped.

### v3 · Market view and season write-up (stretch, Feb–May 2027)

1. Weekly market page (postings by week, city and track), now that there are weeks of data.
2. Monthly job-vacancy chart by province from Statistics Canada, next to Co-op Radar's own posting counts.
3. Recruiting calendar: when each employer posted summer roles and when each program page changed, learned from the snapshots and `ProgramChange` history.
4. Coverage over the season, from the monthly Phase 0 re-runs.
5. Analysis: do program and funding announcements come before new student postings at the same employer or in the same province? Needs several months of data.
6. Public write-up of the season: what opened when, by sector and province.

---

## 8. Repository layout

```
co-op-radar-canada/              # branch: main
├─ README.md                  # problem, screenshot, evaluation table, how to run
├─ config/
│  ├─ employers.yaml
│  ├─ programs.yaml
│  └─ news_queries.yaml
├─ scripts/
│  └─ coverage_spike.py       # Phase 0; re-run monthly
├─ pipeline/
│  ├─ sources/                # greenhouse.py, lever.py, ashby.py, programs.py, gdelt.py, rss.py
│  ├─ extract/                # term.py, duration.py, province.py, track.py
│  ├─ news/                   # dedupe.py, match.py, classify.py
│  ├─ storage.py              # raw snapshot writer for the data branch (section 4.1)
│  ├─ models.py               # pydantic records
│  ├─ build_site_data.py
│  └─ cli.py                  # `python -m pipeline.cli fetch-postings` etc.
├─ data/
│  ├─ processed/              # small, rewritten each run
│  ├─ labels/                 # hand-labelled CSVs
│  └─ run_log.jsonl
├─ tests/
├─ site/                      # Next.js static export
├─ docs/
│  ├─ evaluation.md
│  ├─ sources.md              # every source, its terms, its status, and what is stored
│  └─ decisions/              # short ADRs, one per decision
└─ .github/
   ├─ workflows/              # ci.yml, daily.yml, deploy.yml
   └─ ISSUE_TEMPLATE/submit-posting.yml

data branch (orphan):
raw/
├─ postings/YYYY-MM-DD.jsonl.gz
├─ descriptions/{hash}.html.gz
├─ programs/YYYY-MM-DD.jsonl.gz
└─ news/YYYY-MM-DD.jsonl.gz
```

---

## 9. Engineering practices

- **Tests:** unit tests for every extractor rule and the employer matcher, with real (anonymized if needed) text fixtures. A test that fails if any record lacks a source URL or fetch date. A test that simulates a failed and an empty board fetch and checks that no posting closes.
- **CI:** Ruff, mypy and pytest on every push.
- **Decisions:** one short ADR per meaningful choice in `docs/decisions/` (context, options, choice, consequences). Write these early:
  - 0001: coverage thresholds and Phase 0 results
  - 0002: raw storage design, Canada filter and size budget
  - 0003: Workday out of scope
  - 0004: LinkedIn and other forbidden sites as link-outs only
  - 0005: hosting (GitHub Pages or Vercel)
  - Later: rules vs model for classification, each new source from section 5.5.
- **Evaluation reporting:** every precision or recall figure comes with its counts and a 95% Wilson interval.
- **Commits:** small and descriptive, so the history shows real progress.
- **Politeness:** set a descriptive User-Agent with a contact URL, cache responses, and sleep between requests to the same host.

---

## 10. How to work with the owner

- Lio is the developer and must understand every part of the code well enough to explain it in an interview. Explain design choices as you go and prefer code he can read over clever code.
- Lio's existing stack: Python, TypeScript, SQL, Next.js, React, Tailwind, FastAPI, PostgreSQL, Supabase, DuckDB, Kafka, Spark, Airflow, scikit-learn, XGBoost, pytest, Playwright, GitHub Actions, Docker.
- Related projects whose patterns carry over: the Nutrition Priority Index (provenance on every source, a simpler method that beat a complex one, published as a decision matrix) and FraudLens (checking data before trusting a model score).
- Never fabricate metrics, users or results for the README or resume. Report what the evaluation actually shows.
- Ask before adding any source not marked "Approved" in section 5, any paid service, or anything that touches a site's terms of use.

---

## 11. Open questions to settle early

1. **Exact list of the first 150 employers** (needed for Phase 0 this week). Start from Canadian tech, fintech, retail, energy and public-sector employers on Greenhouse, Lever and Ashby.
2. GitHub Pages or Vercel for hosting (Vercel gives free analytics; Pages keeps everything in GitHub).
3. Project name and domain. "Co-op Radar Canada" is the working name; check that it isn't already taken.
4. Google News RSS: does its terms check pass? Settle before v2 news work starts.
5. Raw storage: orphan `data` branch (default) or GitHub Release assets. Revisit only if the Phase 0 size estimate exceeds the budget.
6. Whether to include Indonesian internships later (out of scope for now).
