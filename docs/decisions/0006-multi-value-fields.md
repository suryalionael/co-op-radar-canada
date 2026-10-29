# 0006: Multi-value term and province, and an explicit in-Canada flag

- **Status:** Accepted
- **Date:** 2026-10-28
- **Deciders:** Lionael Surya

## Context

The brief's `Posting` model (section 6) has one `term` and one `province`. Real postings often have several of each: "Summer 2027 or Fall 2027", "Toronto / Vancouver". With a single value, a student filtering for British Columbia would miss a posting listed as "Toronto / Vancouver".

The model also had no way to say "in Canada, province unknown" (location just says "Canada") apart from "outside Canada". Both would be `province = UNKNOWN`.

## Options

1. Keep single values and pick one. Simple, but filters silently miss postings.
2. Replace `term` and `province` with lists. Correct, but every display needs to handle lists.
3. Keep `term` and `province` as the first value found (for display) and add `terms` and `provinces` with every value (for filtering).

## Decision

Option 3, plus a boolean `in_canada`.

- `terms`: every distinct term, title first, then description, in order of appearance. `term` is `terms[0]`.
- `provinces`: every province in the location fields, in order. `province` is `provinces[0]`, `REMOTE_CA` for remote-in-Canada with no province, or `UNKNOWN`.
- `in_canada`: the location fields name Canada or a Canadian place.

The site filters on `terms`, `provinces` and `in_canada`; cards display `term` and `province`.

## Consequences

- Filters do not miss multi-location or multi-term postings.
- Evaluation compares the full `provinces` list against the label (in order), which is stricter than checking one value.
- `term_start` and `term_end` still describe only the first dated range found.
