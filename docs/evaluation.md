# Evaluation

How the extractors are measured, and the results. **No results yet:** the labelled set is built in v1 week 5 (see [timeline](timeline.md)). Nothing on this page will be filled in until it has been measured.

## Method

1. `python -m pipeline.cli label-sheet --data-root data-branch` adds postings to `data/labels/postings.csv`: every open Canadian student posting, up to 200; if there are fewer, other Canadian postings fill the rest (they still test province and track). The sheet does **not** include the extractor's answers, so labels are not anchored on them.
2. Each row is labelled by hand from the original posting (open the URL). Column rules are in the docstring of `pipeline/evaluate.py`. A duration the posting gives only as dates ("May to August") is labelled as stated.
3. `python -m pipeline.cli evaluate --data-root data-branch` prints the table below.

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

## Known limits

- Rules only read the title, location fields and description text. Durations stated only in an image or a linked PDF are missed.
- The duration extractor rejects phrases near words like "experience", "probation", "within" or "at least". This trades recall for precision on purpose.
- News classification (v2) uses headlines only, since article text is never stored.
