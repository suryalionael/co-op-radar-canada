# 0003: Workday out of scope

- **Status:** Accepted
- **Date:** 2026-10-28
- **Deciders:** Lionael Surya

## Context

Most large Canadian banks, insurers, pension funds and many utilities post jobs on Workday. These employers run some of the largest student programs in the country. Workday career sites are served from undocumented endpoints; there is no published public posting API like Greenhouse's, Lever's or Ashby's.

## Options

1. Call Workday career-site endpoints directly. Would add many large employers, but relies on undocumented interfaces with no stated permission, can break without notice, and conflicts with the project's rule of public, permitted sources only.
2. Leave Workday out of the posting pipeline and cover those employers another way.

## Decision

Option 2. No code fetches from Workday career sites. Those employers are covered by:

- **Program watch:** their public student-program pages are fingerprinted daily, so the site can say when a program page changed.
- **Submissions (v2):** anyone can submit a posting through the GitHub issue form.
- **Link-outs:** employer pages link to the employer's own career site.

The About page states plainly that postings from Workday employers do not appear automatically.

## Consequences

- Posting coverage skews toward tech employers. The site's positioning reflects that: verified postings from Canada's tech employers, plus program watch for everyone else.
- Revisiting this requires a new ADR, employer by employer, with the employer's terms checked first.
