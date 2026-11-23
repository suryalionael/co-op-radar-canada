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

**Run on 2026-11-23** over the 200-row sheet (`data/labels/postings.csv`, Nov 1 snapshot), against the latest stored text of each posting.

> **Who labelled this set: Claude (an AI model), not a person.** Claude labelled all 200 rows from each posting's stored description on the `data` branch, the same text the extractors read. The live pages could not be opened from Claude's environment, and many had closed. Labels were written before any extractor output was viewed. Seven postings changed after the Nov 1 snapshot (a title or location edit); those are labelled from the later version, which is what the extractors are scored on, and the `notes` column says so. But Claude also wrote the extraction rules, so these labels are **not independent** of the rules and may share their blind spots. The brief allows an LLM for a one-time evaluation run; it does not make these figures human-verified. Ei Htoo's 40 independent human labels (`postings_second.csv`, V1-8) measure how far Claude's labels agree with a person's. Until that agreement is published, read these figures as provisional.

| Field | Labelled examples | Precision | Recall |
|---|---|---|---|
| Term | 102 | 102/102 = 1.00 (95% CI 0.96–1.00) | 102/102 = 1.00 (95% CI 0.96–1.00) |
| Duration | 79 | 72/72 = 1.00 (95% CI 0.95–1.00) | 72/79 = 0.91 (95% CI 0.83–0.96) |
| Province | 196 | 195/198 = 0.98 (95% CI 0.96–0.99) | 195/196 = 0.99 (95% CI 0.97–1.00) |
| Track | 200 | 142/200 = 0.71 (95% CI 0.64–0.77) | 142/200 = 0.71 (95% CI 0.64–0.77) |
| Student role | 200 | 200/200 = 1.00 (95% CI 0.98–1.00) | 200/200 = 1.00 (95% CI 0.98–1.00) |

Duration precision meets the 0.95 target. The interval's lower bound, 0.92, is above 0.90.

**Every error, by field:**

- **Duration fixes (2026-11-23).** After this list was written, the duration rules were changed to fix the misses below (all but the Tenstorrent month ranges) and the Moment Energy preference. Duration went from 65/66 precision and 65/79 recall to 72/72 and 72/79. The fixes were made while looking at these same 200 postings, so the new figures overstate how the rules will do on postings they haven't seen. Ei Htoo's independent labels (#13) are the check on that.
- **Duration, wrong (1):** Moment Energy's "Strong preference for students available for an 8-month co-op term" was read as an 8-month duration. It states a preference, so the label is blank.
- **Duration, missed (14):**
  - Behaviour Interactive's "work 37,5 hours/week for 4 months" (5 postings): no co-op or internship word in the same sentence.
  - Month ranges with no year ("Winter Term: Jan–Apr work term") at Tenstorrent (2): dates only become a duration when they have a year.
  - Cohere's "full-time4 month internship": no space before the number.
  - TELUS Digital's "approx. 16 weeks": the abbreviation's period ends the sentence before the role word.
  - "at least a 4 month term" (Fullscript): rejected by the "at least" rule.
  - "12–16 week internship" (Yotta Labs).
  - Brave's "$6000.00 per month for 3 months".
- **Province (4):** all four are remote postings in Canada with no province. The extractor uses the board's structured remote field, which the labeller did not see; the labeller read only the location and description text. Three of these the extractor called `REMOTE_CA` and the labels left blank; one is the other way round.
- **Track (58):** mostly about category boundaries rather than extraction errors:
  - hardware, electrical and IT roles the labeller put in `other` and the rules put in `software` (13);
  - marketing and sales roles with analytics in the title or description, `business_ops` vs `data_analytics` (8);
  - AI-related titles the rules map to `ml_ai` (10).

  The track definitions need a written boundary before this number means much.
- **Term:** no errors. The postings in this set state their terms plainly ("Winter 2027", "Hiver 2027", "January – August 2027").

### Against a naive baseline

`python -m pipeline.cli evaluate` also scores a deliberately naive classifier on the same labelled rows, to show what the stricter rules add. A posting is a student role if its employment type or title contains "co-op", "coop", "intern" or "student" as a plain substring, and is Summer 2027 if its title contains "summer 2027" or "may 2027". These are our own few lines, modelled on the approach of [HamzaPM58/coop-watcher](https://github.com/HamzaPM58/coop-watcher), not its code. Both questions are scored on the "yes" class.

| Question | Labelled | Ours: precision | Ours: recall | Naive baseline: precision | Naive baseline: recall |
|---|---|---|---|---|---|
| Student role | 200 | 175/175 = 1.00 (95% CI 0.98–1.00) | 175/175 = 1.00 (95% CI 0.98–1.00) | 171/171 = 1.00 (95% CI 0.98–1.00) | 171/175 = 0.98 (95% CI 0.94–0.99) |
| Summer 2027 | 200 | 24/24 = 1.00 (95% CI 0.86–1.00) | 24/24 = 1.00 (95% CI 0.86–1.00) | 15/15 = 1.00 (95% CI 0.80–1.00) | 15/24 = 0.62 (95% CI 0.43–0.79) |

On this sheet the baseline makes no false "yes" calls: the "Internal"/"International" titles it gets wrong (below) are not among the 200 rows. Its cost shows in recall: it misses four French "Stagiaire" titles as student roles, and misses Summer 2027 postings whose title says "été 2027" or gives the term only in the description.

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

**Result (2026-11-01, latest snapshot 2026-11-01, all 171 boards fetched):**

| Reference set | Found |
|---|---|
| Listings at every employer in the config | 64/70 = 0.91 (95% CI 0.83–0.96) |

The two figures in the first run (boards in the snapshot, and every employer in the config) are now the same, because every configured board is in the snapshot. The reference set grew from 67 to 70 as the curator added rows.

- 5 of the 6 misses are listings **no longer on the employer's board** (3 at D2L, 1 each at Equitable Bank and Zip): the list still shows them as open, but the board no longer has them.
- 1 miss is a location disagreement, not a bug. The curator lists it as "Remote, Canada"; the employer's board lists it as "North America" with the United States as its country, and the description does not mention Canada. Under the honest-labels rule we do not call it Canadian.
- None was lost to role detection.

First run, 2026-10-30, for comparison: 23/26 = 0.88 (95% CI 0.71–0.96) on boards in that snapshot; 23/67 = 0.34 overall, because the 40 employers added that day had not been fetched yet.

**Caveats:**

- The list is not exhaustive and leans toward software roles, so this measures recall on what one curator found, not on every Canadian student posting.
- The reference set covers only employers we already track. It says nothing about employers we have not found, which is the coverage question in ADR 0001 and ADR 0009.
- The curator's term labels (the parenthetical "(Winter 2027)") are annotations, not text from the posting. They are **not gold labels** and never go into `data/labels/`.

**Term cross-check (not a score).** On matched postings where the curator gave a term, the curator's term is compared with ours: agree 22, disagree 0, we said "not stated" 3, we said "ambiguous" 0, out of 25 (2026-11-01). This is a sanity check on the term extractor, not an evaluation of it. The hand-labelled set above is the evaluation.

## Known limits

- Rules only read the title, location fields and description text. Durations stated only in an image or a linked PDF are missed.
- The duration extractor rejects phrases near words like "experience", "probation", "within" or "at least". This trades recall for precision on purpose.
- The term extractor skips any date with a graduation word ("graduation date", "graduating in", "diplôme") up to about 60 characters before it in the same sentence. A work term written in that same stretch of a sentence would be missed.
- News classification (v2) uses headlines only, since article text is never stored.
