# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Canadian university and college co-op and internship students, mostly in CS
and engineering. They use it on a laptop or a phone during recruiting season
(roughly September to January). Their job is to find roles that match the
exact term and duration their school approves (for example "Summer 2027, 4
months, Ontario") and apply before the window closes.

## Product Purpose

It is a free, public tracker for Canadian tech co-op and internship postings.
It answers three questions:

- What is open right now?
- When does each company usually hire?
- When do the big student programs open?

Success means students actually use it during the Summer 2027 cycle, from a
launch before winter break.

## Positioning

- Every term and duration shown links back to the exact words in the
  posting that state it. If a posting doesn't say, the site says "not stated"
  instead of guessing.
- Hiring windows per company are built from when postings actually appeared.
- Program watch covers the big employers (banks, insurers, governments) that
  have no public posting API, by recording the day their student-program
  pages change.
- US-heavy internship trackers rarely record term or duration. That is the
  gap this product fills.

## Operating Context

- Students scan, filter and click through to the employer's own application
  page. The site never hosts applications.
- The data refreshes once a day from a pipeline that reads public
  Greenhouse, Lever and Ashby job boards (171 employers) and 30
  student-program pages.
- Built and run by two students (Lio and Ei Htoo).

## Capabilities and Constraints

- The site is statically exported (Next.js) and hosted on the Vercel free
  tier. It has no accounts or backend.
- Public, permitted sources only. It never fetches anything from LinkedIn,
  Indeed, Glassdoor, Reddit or Workday career sites. Those may appear only
  as outbound links.
- Coverage is partial by design, and the About page says so. Never claim to
  list every co-op in Canada.
- The negarprh/Canadian-Tech-Internships list may be used, with credit, only
  once written permission exists (ADR 0007, to be superseded).
- No salary data: Canadian internship postings rarely state pay.

## Brand Commitments

- The name is Co-op Radar Canada.
- The voice is student-to-student: plain and direct, with a bit of
  personality, like a friend who did the research. "Built by students for
  students."
- Speedrun (speedrun-talent-network.com) is the reference for the structure
  (jobs-first board, collections, dense rows). It is not a reference for the
  look.

## Evidence on Hand

- Real data lives in `site/public/data/` (postings, companies, programs, meta).
- `docs/evaluation.md` has the extractor accuracy results. They are
  provisional until human labels give an agreement figure.
- There are no testimonials, user counts or press yet, and none may be
  invented.

## Product Principles

1. Show the evidence, never guess. "Not stated" beats a confident wrong
   answer.
2. Jobs first. The first screen is the board, not a pitch.
3. Honest coverage. Say what is missing and where to look instead.
4. Fast and free. Static pages, no sign-up needed to get value.

## Accessibility & Inclusion

WCAG AA contrast in light and dark mode. Filters must be usable from the
keyboard. Layouts must work at 375px wide.
