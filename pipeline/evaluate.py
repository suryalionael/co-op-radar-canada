"""Evaluate the extractors against hand labels in data/labels/postings.csv.

Labelling sheet columns (one row per posting, filled in by hand from the posting itself):

    id, employer_id, title, url, location_raw,          <- exported, do not edit
    term, duration_options_months, province, track, is_student_role, notes

- term: e.g. "Summer 2027"; blank if the posting states none.
- duration_options_months: options separated by ";" (e.g. "4;8"); blank if not stated.
  Count a duration the posting gives only as dates (May to August) as stated here.
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
"""

from __future__ import annotations

import csv
import math
from collections.abc import Callable, Iterable
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
