"""Rule-based extractors. Every extracted field keeps the text it came from in `evidence`."""

from __future__ import annotations

from typing import Any

from pipeline.extract.duration import extract_duration
from pipeline.extract.province import extract_location
from pipeline.extract.student import is_student_role
from pipeline.extract.term import extract_term
from pipeline.extract.track import extract_track
from pipeline.models import RawPosting
from pipeline.text import html_to_text

CONTEXT_CHARS = 70


def quote_context(span: str, *texts: str, width: int = CONTEXT_CHARS) -> str | None:
    """A short quote around the first place `span` appears, cut at word boundaries.

    Used to show the posting's own words next to an extracted fact. Ellipses mark
    where the quote was cut.
    """
    for text in texts:
        at = text.find(span)
        if at < 0:
            continue
        start, end = max(0, at - width), min(len(text), at + len(span) + width)
        if start > 0:
            space = text.find(" ", start, at)
            start = space + 1 if space >= 0 else start
        if end < len(text):
            space = text.rfind(" ", at + len(span), end)
            end = space if space >= 0 else end
        quote = " ".join(text[start:end].split())
        return ("…" if start > 0 else "") + quote + ("…" if end < len(text) else "")
    return None


def extract_posting(raw: RawPosting, description_html: str) -> dict[str, Any]:
    """Every extracted Posting field for one raw posting."""
    description = html_to_text(description_html)
    evidence: dict[str, str] = {}

    term = extract_term(raw.title, description)
    if term.evidence:
        evidence["term"] = term.evidence
    if term.dates_evidence:
        evidence["term_dates"] = term.dates_evidence

    duration = extract_duration(raw.title, description, term.start, term.end, term.dates_evidence)
    if duration.evidence:
        evidence["duration"] = duration.evidence

    location = extract_location(raw.location_raw, raw.workplace_hint)
    if location.province_evidence:
        evidence["province"] = location.province_evidence
    if location.remote_evidence:
        evidence["remote"] = location.remote_evidence

    # The posting's own words around the term and duration, for the site's evidence quotes.
    for field in ("term", "duration"):
        span = evidence.get(field, "").split(" | ")[0]
        context = quote_context(span, raw.title, description) if span else None
        if context:
            evidence[f"{field}_context"] = context

    track, track_evidence = extract_track(raw.title, description)
    if track_evidence:
        evidence["track"] = track_evidence

    student, student_evidence = is_student_role(raw.title)
    if student_evidence:
        evidence["is_student_role"] = student_evidence

    return {
        "in_canada": location.in_canada,
        "province": location.province,
        "provinces": location.provinces,
        "remote": location.remote,
        "term": term.term,
        "terms": term.terms,
        "term_start": term.start,
        "term_end": term.end,
        "duration_options_months": duration.options_months,
        "duration_status": duration.status,
        "track": track,
        "is_student_role": student,
        "evidence": evidence,
    }
