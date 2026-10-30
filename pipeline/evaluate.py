"""Evaluate the extractors against hand labels in data/labels/postings.csv.

Labelling sheet columns (one row per posting, filled in by hand from the posting itself):

    id, employer_id, title, url, location_raw,          <- exported, do not edit
    term, duration_options_months, province, track, is_student_role, notes

- term: e.g. "Summer 2027"; blank if the posting states none, or only an
  ambiguous one like "Spring 2027". Label the term as stated, even if it is
  already over.
- duration_options_months: options separated by ";" (e.g. "4;8"); blank if not stated.
  Count a duration the posting gives only as dates (May to August) as stated here.
  A range ("4-16 months") is labelled by its two ends ("4;16"), the same way the
  extractor stores it with duration_is_range set (ADR 0008).
- province: ON, BC, ..., REMOTE_CA, or UNKNOWN; several separated by ";" in posting order.
- track: data_science | data_analytics | data_eng | ml_ai | software | business_ops | other
- is_student_role: yes or no

The sheet is exported without the extractor's answers, so labels are not
anchored on them.

Per field:

- precision = correct / postings where the extractor gave a value
- recall    = correct / postings where the label has a value

Every figure is reported with its counts and a 95% Wilson interval (brief
section 9), e.g. "57/59 = 0.97 (95% CI 0.88–0.99)".

Naive baseline. To show what the stricter rules add, `compare_with_baseline`
scores two yes/no questions for our extractors and for a deliberately naive
classifier on the same labelled rows:

- student role: does the employment type or title contain "co-op", "coop",
  "intern" or "student" as a plain substring? ("Internal Audit" says yes.)
- Summer 2027: does the title contain "summer 2027" or "may 2027"?

It is our own few lines, modelled on the approach of HamzaPM58/coop-watcher, not
its code. Both questions are scored on the positive class: precision is right
"yes" answers over all "yes" answers, recall is right "yes" answers over all
rows labelled "yes".
"""

from __future__ import annotations

import csv
import math
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from pipeline.models import Posting

LABEL_COLUMNS = [
    "id",
    "employer_id",
    "title",
    "url",
    "location_raw",
    "term",
    "duration_options_months",
    "province",
    "track",
    "is_student_role",
    "notes",
]


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - margin), min(1.0, centre + margin))


@dataclass
class Ratio:
    k: int
    n: int

    def __str__(self) -> str:
        if self.n == 0:
            return "0/0 (no cases)"
        low, high = wilson_interval(self.k, self.n)
        return f"{self.k}/{self.n} = {self.k / self.n:.2f} (95% CI {low:.2f}–{high:.2f})"

    @property
    def lower_bound(self) -> float:
        return wilson_interval(self.k, self.n)[0]


@dataclass
class FieldScore:
    field: str
    labelled: int
    precision: Ratio
    recall: Ratio


# How each field is read from a label row and from a prediction. None means "no value".
Getter = Callable[[dict[str, str]], object | None]
Predictor = Callable[[Posting], object | None]


def _blank_to_none(value: str) -> str | None:
    value = (value or "").strip()
    return value or None


def _durations(value: str) -> tuple[float, ...] | None:
    value = (value or "").strip()
    return tuple(sorted(float(v) for v in value.split(";") if v.strip())) or None


def _provinces(value: str) -> tuple[str, ...] | None:
    value = (value or "").strip()
    return tuple(v.strip() for v in value.split(";") if v.strip()) or None


FIELDS: dict[str, tuple[Getter, Predictor]] = {
    "term": (lambda r: _blank_to_none(r["term"]), lambda p: p.term),
    "duration": (
        lambda r: _durations(r["duration_options_months"]),
        lambda p: tuple(p.duration_options_months) or None,
    ),
    "province": (
        lambda r: _provinces(r["province"]),
        lambda p: tuple(str(v) for v in p.provinces) if p.provinces else None,
    ),
    "track": (lambda r: _blank_to_none(r["track"]), lambda p: str(p.track)),
    "is_student_role": (
        lambda r: {"yes": True, "no": False}.get((r["is_student_role"] or "").strip().lower()),
        lambda p: p.is_student_role,
    ),
}


STUDENT_SUBSTRINGS = ("co-op", "coop", "intern", "student")


def baseline_is_student(p: Posting) -> bool:
    text = f"{p.employment_type_raw or ''} {p.title}".lower()
    return any(s in text for s in STUDENT_SUBSTRINGS)


def baseline_is_summer_2027(p: Posting) -> bool:
    title = p.title.lower()
    return "summer 2027" in title or "may 2027" in title


# Each yes/no question: how to read it from a label row (None = not labelled), from our
# extractors, and from the naive baseline.
YesNo = Callable[[Posting], bool]
BASELINE_QUESTIONS: dict[str, tuple[Callable[[dict[str, str]], bool | None], YesNo, YesNo]] = {
    "student role": (
        lambda r: {"yes": True, "no": False}.get((r["is_student_role"] or "").strip().lower()),
        lambda p: p.is_student_role,
        baseline_is_student,
    ),
    "Summer 2027": (
        lambda r: (r["term"] or "").strip() == "Summer 2027",
        lambda p: "Summer 2027" in p.terms,
        baseline_is_summer_2027,
    ),
}


@dataclass
class BaselineComparison:
    question: str
    labelled: int
    ours_precision: Ratio
    ours_recall: Ratio
    baseline_precision: Ratio
    baseline_recall: Ratio


def _positive_class(pairs: list[tuple[bool, bool]]) -> tuple[Ratio, Ratio]:
    """Precision and recall of the "yes" answers, from (truth, guess) pairs."""
    true_positive = sum(t and g for t, g in pairs)
    return Ratio(true_positive, sum(g for _, g in pairs)), Ratio(true_positive, sum(t for t, _ in pairs))


def compare_with_baseline(labels: list[dict[str, str]], postings: dict[str, Posting]) -> list[BaselineComparison]:
    out = []
    for question, (get_label, ours, baseline) in BASELINE_QUESTIONS.items():
        rows: list[tuple[bool, Posting]] = []
        for r in labels:
            truth = get_label(r)
            if truth is not None and r["id"] in postings:
                rows.append((truth, postings[r["id"]]))
        our_p, our_r = _positive_class([(truth, ours(p)) for truth, p in rows])
        base_p, base_r = _positive_class([(truth, baseline(p)) for truth, p in rows])
        out.append(BaselineComparison(question, len(rows), our_p, our_r, base_p, base_r))
    return out


def baseline_table(rows: Iterable[BaselineComparison]) -> str:
    lines = [
        "| Question | Labelled | Ours: precision | Ours: recall | Naive baseline: precision | Naive baseline: recall |",
        "|---|---|---|---|---|---|",
    ]
    for c in rows:
        lines.append(
            f"| {c.question} | {c.labelled} | {c.ours_precision} | {c.ours_recall} | "
            f"{c.baseline_precision} | {c.baseline_recall} |"
        )
    return "\n".join(lines) + "\n"


def score(labels: list[dict[str, str]], postings: dict[str, Posting]) -> list[FieldScore]:
    scores = []
    for name, (get_label, predict) in FIELDS.items():
        predicted = correct_predicted = labelled = correct_labelled = 0
        for row in labels:
            posting = postings.get(row["id"])
            if posting is None:
                continue
            truth, guess = get_label(row), predict(posting)
            if guess is not None:
                predicted += 1
                correct_predicted += guess == truth
            if truth is not None:
                labelled += 1
                correct_labelled += guess == truth
        scores.append(
            FieldScore(name, labelled, Ratio(correct_predicted, predicted), Ratio(correct_labelled, labelled))
        )
    return scores


@dataclass
class Agreement:
    field: str
    both_labelled: int
    agree: Ratio
    kappa: float | None  # Cohen's kappa; None when chance agreement is 1 (every label the same)


def cohens_kappa(pairs: Sequence[tuple[object, object]]) -> float | None:
    """Agreement beyond chance between two labellers. "No value" counts as its own category."""
    n = len(pairs)
    if n == 0:
        return None
    observed = sum(a == b for a, b in pairs) / n
    first = Counter(a for a, _ in pairs)
    second = Counter(b for _, b in pairs)
    expected = sum(first[k] * second.get(k, 0) for k in first) / (n * n)
    return None if expected == 1 else (observed - expected) / (1 - expected)


def agreement(first: list[dict[str, str]], second: list[dict[str, str]]) -> list[Agreement]:
    """Compare two people's labels on the postings both of them labelled (V1-8)."""
    by_id = {r["id"]: r for r in second}
    shared = [(r, by_id[r["id"]]) for r in first if r["id"] in by_id]
    out = []
    for name, (get_label, _) in FIELDS.items():
        pairs = [(get_label(a), get_label(b)) for a, b in shared]
        out.append(Agreement(name, len(pairs), Ratio(sum(a == b for a, b in pairs), len(pairs)), cohens_kappa(pairs)))
    return out


def agreement_table(rows: Iterable[Agreement]) -> str:
    lines = ["| Field | Postings labelled by both | Agreement | Cohen's kappa |", "|---|---|---|---|"]
    for a in rows:
        kappa = "—" if a.kappa is None else f"{a.kappa:.2f}"
        lines.append(f"| {a.field} | {a.both_labelled} | {a.agree} | {kappa} |")
    return "\n".join(lines) + "\n"


def markdown_table(scores: Iterable[FieldScore]) -> str:
    lines = ["| Field | Labelled examples | Precision | Recall |", "|---|---|---|---|"]
    for s in scores:
        lines.append(f"| {s.field} | {s.labelled} | {s.precision} | {s.recall} |")
    return "\n".join(lines) + "\n"


def read_labels(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return [row for row in csv.DictReader(f) if (row.get("id") or "").strip()]


def write_label_sheet(postings: list[Posting], path: Path, already_labelled: set[str]) -> int:
    """Append unlabelled postings to the sheet with label columns blank. Returns rows added."""
    new = [p for p in postings if p.id not in already_labelled]
    exists = path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LABEL_COLUMNS)
        if not exists:
            writer.writeheader()
        for p in new:
            writer.writerow(
                {
                    "id": p.id,
                    "employer_id": p.employer_id,
                    "title": p.title,
                    "url": p.url,
                    "location_raw": p.location_raw,
                }
            )
    return len(new)
