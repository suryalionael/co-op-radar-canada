# Evaluation

How the extractors are measured, and the results. **No results yet:** the labelled set is built in v1 week 5 (see [timeline](timeline.md)). Nothing on this page will be filled in until it has been measured.

## Method

1. `python -m pipeline.cli label-sheet --data-root data-branch` adds postings to `data/labels/postings.csv`: every open Canadian student posting, up to 200; if there are fewer, other Canadian postings fill the rest (they still test province and track). The sheet does **not** include the extractor's answers, so labels are not anchored on them.
2. Each row is labelled by hand from the original posting (open the URL). Column rules are in the docstring of `pipeline/evaluate.py`. A duration the posting gives only as dates ("May to August") is labelled as stated. A duration given as a range ("4–16 months") is labelled by its two ends (`4;16`), matching how the extractor stores it with `duration_is_range` set (ADR 0008). Dates about the student's graduation ("graduating in spring 2028") are not a term.
3. `python -m pipeline.cli evaluate --data-root data-branch` prints the table below.
4. **Second labeller.** Ei Htoo independently labels 40 of the same postings in `data/labels/postings_second.csv`, without seeing the first labels or the extractor output. `python -m pipeline.cli agreement` reports per-field agreement (with a Wilson interval) and Cohen's kappa. Disagreements are counted first, then resolved by discussion; the resolved labels are what the extractors are scored against.

Per field:

- **Precision** = correct / postings where the extractor gave a value. A "not stated" output is not counted against precision, which is why a wrong duration is treated as worse than "not stated".
- **Recall** = correct / postings where the label has a value.

Every figure is shown with its counts and a 95% Wilson interval, for example "57/59 = 0.97 (95% CI 0.88–0.99)".

A value is correct only if it matches the label exactly: for duration, the whole set of options; for province, the whole list in order.

**Target:** duration precision ≥ 0.95. If the interval's lower bound is below 0.90, the README says so. Recall is reported as measured.

## Results

| Field | Labelled examples | Precision | Recall |
|---|---|---|---|
| Term | not yet measured | — | — |
| Duration | not yet measured | — | — |
| Province | not yet measured | — | — |
| Track | not yet measured | — | — |
| Student role | not yet measured | — | — |

### Against a naive baseline

`python -m pipeline.cli evaluate` also scores a deliberately naive classifier on the same labelled rows, to show what the stricter rules add. A posting is a student role if its employment type or title contains "co-op", "coop", "intern" or "student" as a plain substring, and is Summer 2027 if its title contains "summer 2027" or "may 2027". These are our own few lines, modelled on the approach of [HamzaPM58/coop-watcher](https://github.com/HamzaPM58/coop-watcher), not its code. Both questions are scored on the "yes" class.

| Question | Labelled | Ours: precision | Ours: recall | Naive baseline: precision | Naive baseline: recall |
|---|---|---|---|---|---|
| Student role | not yet measured | — | — | — | — |
| Summer 2027 | not yet measured | — | — | — | — |

**Disagreements before labelling (not a score).** On the 2,018 open postings in Canada in the 2026-10-30 snapshot:

- The baseline calls 58 of them student roles; our extractor calls 48.
- All 14 that only the baseline counts are titles with "Internal" or "International": internal auditors, internal-tools engineers, "Engineering Manager, International", and similar.
- The 4 that only we count are French titles with "Stagiaire".
- 21 of our 48 were decided by the board's structured employment-type field, and 27 by the title.

These counts show where the two methods differ. They are not precision or recall, which need the labelled set.

### Labeller agreement

| Field | Postings labelled by both | Agreement | Cohen's kappa |
|---|---|---|---|
| all fields | not yet measured | — | — |

## Pipeline recall against a curated reference list

A second, independent check: of the internships a human curator found, how many does our pipeline hold? The curated list is [negarprh/Canadian-Tech-Internships-2027](https://github.com/negarprh/Canadian-Tech-Internships-2027), used for evaluation only (ADR 0007).

```bash
python -m pipeline.cli reference-recall --data-root data-branch   # add --offline to skip live board checks
```

**Reference set:** open rows of the 2027 list whose Apply link is on Greenhouse, Lever or Ashby and whose employer is in `config/employers.yaml`. A listing is **found** if our processed postings hold it (matched by the job id in the link, else by normalized URL) as an open, Canadian student posting. Each miss gets a likely reason from one live check of its board: gone from the board, filtered out as non-Canadian at fetch, employer added after our latest snapshot, or held but not counted (closed, location not read as Canadian, missed by role detection).

**Result (2026-10-30, latest snapshot 2026-10-30):**

| Reference set | Found |
|---|---|
| Listings on boards our latest snapshot fetched | 23/26 = 0.88 (95% CI 0.71–0.96) |
| Listings at every employer now in the config | 23/67 = 0.34 (95% CI 0.24–0.46) |

- All 3 misses on fetched boards are listings that are **no longer on the employer's board**: their job ids return 404, but the list still shows them as open. None was lost to our Canada filter or role detection.
- The lower second figure is not a pipeline miss. 39 of its 44 misses are at the 40 employers added on 2026-10-30 from this same list (`data/coverage/token_check_log.csv`), which no snapshot has fetched yet. The other 5 are gone from their boards. Re-run after the next Daily run.

**Caveats:**

- The list is not exhaustive and leans toward software roles, so this measures recall on what one curator found, not on every Canadian student posting.
- The reference set covers only employers we already track. It says nothing about employers we have not found, which is the coverage question in ADR 0001 and ADR 0009.
- The curator's term labels (the parenthetical "(Winter 2027)") are annotations, not text from the posting. They are **not gold labels** and never go into `data/labels/`.

**Term cross-check (not a score).** On matched postings where the curator gave a term, the curator's term is compared with ours: agree 10, disagree 0, we said "not stated" 0, we said "ambiguous" 0, out of 10. This is a sanity check on the term extractor, not an evaluation of it. The hand-labelled set above is the evaluation.

## Known limits

- Rules only read the title, location fields and description text. Durations stated only in an image or a linked PDF are missed.
- The duration extractor rejects phrases near words like "experience", "probation", "within" or "at least". This trades recall for precision on purpose.
- The term extractor skips any date with a graduation word ("graduation date", "graduating in", "diplôme") up to about 60 characters before it in the same sentence. A work term written in that same stretch of a sentence would be missed.
- News classification (v2) uses headlines only, since article text is never stored.
