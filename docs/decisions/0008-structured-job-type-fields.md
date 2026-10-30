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
- Order of signals for role type: structured employment type, then title, then description. The role-type extractor that applies this order is described in a section added below.
- `posted_on` is used to flag terms that ended before the posting was published. When a board gives no date, `first_seen` is used instead.

## Consequences

- Greenhouse boards without a custom employment-type field still rely on the title. Most Greenhouse boards we checked have none.
- `employment_type_raw` is free text on Lever and Greenhouse. It is never shown as-is on the site; it feeds the role-type extractor, which maps it to a small set of values.
- The site JSON is unchanged by this ADR.
