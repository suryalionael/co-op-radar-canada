# 0008: Use each board's structured job-type fields

- **Status:** Accepted
- **Date:** 2026-10-30
- **Deciders:** Lionael Surya

## Context

Whether a posting is a co-op, an internship or a full-time job has so far been read from the title alone. The job-board APIs often say it directly, in a field the employer filled in. [HamzaPM58/coop-watcher](https://github.com/HamzaPM58/coop-watcher) showed that Lever's `categories.commitment` (values like "Coop Student" or "Intern") is a useful co-op signal. We reimplement the idea, not its code.

These fields were already in the raw snapshots, since `RawPosting.raw` keeps every API field except the description (ADR 0002). They were not in the processed postings.

## What each API provides

Checked against live responses on 2026-10-30. Greenhouse: `geotab`, `internshiplist2000`, `momentenergy`. Ashby: `1password`, `cohere`, `bree`. Lever: `waabi`, `eqbank`.

| Field | Lever | Ashby | Greenhouse |
|---|---|---|---|
| `employment_type_raw` | `categories.commitment`, free text ("Full-time", "Intern", "Student", "Coop Student") | `employmentType`, a fixed set (`FullTime`, `PartTime`, `Intern`, `Contract`, `Temporary`) | No standard field. Some employers add a custom field in `metadata`; we use it only when its name is an employment-type label ("Employment Type", "Job Type", "Employment Status", "Commitment"). Geotab's says "Intern/Student" |
| `department` | `categories.department` | `department` | `departments[].name`, joined with " / " |
| `team` | `categories.team` | `team` | none |
| `workplace_type_raw` | `workplaceType` (`hybrid`, `onsite`, `remote`) | `workplaceType` (`Remote`, `Hybrid`, `OnSite`) | custom `metadata` field named "Working Conditions" or "Workplace Type", when present |
| `posted_on` | `createdAt` (ms since epoch, UTC date) | `publishedAt` | `first_published` |

Greenhouse custom fields whose names are questions ("Under which category should this job be listed…") are not used, even when the answer looks like a job type.

## Decision

- Add `employment_type_raw`, `department`, `team`, `workplace_type_raw` and `posted_on` to `Posting` and `data/processed/postings.parquet`. Values are the board's text verbatim, with whitespace collapsed. `None` means the board did not say.
- Each source module has a `job_fields()` function that reads them from the stored API record, so every existing snapshot gets them on the next processing run, with no re-fetch.
- These fields are evidence in their own right: the board's structured answer, not text we parsed. When the role-type extractor uses one, the evidence names the field (for example `employment_type: Coop Student`).
- Order of signals for role type: structured employment type, then title, then description. The role-type section below gives the details.
- `posted_on` is used to flag terms that ended before the posting was published. When a board gives no date, `first_seen` is used instead.

## Role type

`pipeline/extract/role_type.py` sets a new `role_type` field (`coop`, `intern`, `student`, `none`). `is_student_role` becomes `role_type != none`.

1. **Signals in order:** structured employment type, then title, then description. Between the first two, the more specific type wins (co-op over intern over student), and ties go to the structured field. Ashby's fixed list has `Intern` but no co-op value, so a title saying "Co-op" refines it to co-op.
2. **A structured value that names no student type** ("Full-time", "FullTime") is no signal. Many boards leave it at its default for intern roles.
3. **The description only refines.** It can turn a generic `student` ("Summer Student") into `coop` or `intern`. It never makes a role a student role on its own, so a senior posting that mentions "our co-op students" stays `none`.
4. **Whole-word rules only:**
   - co-op: `\bco[-‐‑ ]?ops?\b`, so "Cooperative" does not match.
   - intern: `\binterns?\b`, `\binternships?\b`, "stagiaire", and French "stage" before en/de/du/d'/à. "Internal", "International" and "Early Stage" do not match.
   - student: "student(s)" except where it names a service for students ("Student Success", "Student Services") or follows for/to/with.
5. **Evidence:** `evidence["is_student_role"]` is the exact matched span, and `evidence["role_type_field"]` names where it matched (`employment_type`, `title` or `description`).

[coop-watcher](https://github.com/HamzaPM58/coop-watcher) once matched "intern" as a substring, so "Internal Audit" counted as a student role. It fixed that by dropping "intern" from title matching altogether, which loses real intern titles. Whole-word matching keeps both right. The regression tests in `tests/test_extract.py` cover these cases.

## Term status, duration ranges and past terms

Changes to the term and duration extractors that make them more honest about what a posting says:

- **`term_status`** (`stated`, `ambiguous`, `not_stated`). "Spring 2027" means different months at different schools, so it is never mapped to a term. When it is all a posting says, `term` stays empty, `term_status` is `ambiguous`, and the span is kept in `evidence["term_ambiguous"]`.
- **Plain month and year** ("May 2027 GIS Co-op", "(Winter/January 2027)", "Jan 2027") now give a term on the school calendar: January–April is Winter, May–August Summer, September–December Fall. In a title this always counts. In a description it counts only when the same sentence names the work term and no deadline word comes right before it, so "apply by May 2027" and "graduating in May 2027" give no term.
- **`duration_is_range`.** "8–12 months" keeps 8 and 12 as `duration_options_months` and sets the flag. Site filters keep working, and "8 or 12" stays distinguishable from "8 to 12".
- **`flag_term_in_past`.** True when every stated term ended before the posting date (`posted_on`, or `first_seen` when the board gives no date). The term is kept exactly as stated and never corrected. The curated list has real cases, such as a role posted in October 2026 whose title says "Winter 2026".

## Consequences

- Greenhouse boards without a custom employment-type field still rely on the title. Most Greenhouse boards we checked have none.
- `employment_type_raw` is free text on Lever and Greenhouse. It is never shown as-is on the site; it feeds the role-type extractor, which maps it to a small set of values.
- The site JSON is unchanged by this ADR.
