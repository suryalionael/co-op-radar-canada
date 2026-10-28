"""Role-track extractor: keyword rules on the title first, then the description.

Rules are checked in order and the first match wins, so the more specific
tracks come first ("Machine Learning Engineer" is ml_ai, not software;
"Data Engineer" is data_eng, not software).

The description is used only when the title says nothing about the track
(for example "Co-op Student, Summer 2027"). There, a track needs at least two
keyword hits, and the track with the most hits wins.
"""

from __future__ import annotations

import re

from pipeline.models import Track

RULES: list[tuple[Track, re.Pattern[str]]] = [
    # Non-software engineering disciplines, so "Mechanical Engineering Intern" is not software.
    (
        Track.other,
        re.compile(
            r"\b(?:mechanical|electrical|civil|chemical|industrial|manufacturing|hardware|structural|"
            r"geotechnical|mining|aerospace)\s+(?:engineer(?:ing)?|design)\b",
            re.IGNORECASE,
        ),
    ),
    (
        Track.ml_ai,
        re.compile(
            r"\b(?:machine learning|ML|AI|artificial intelligence|deep learning|NLP|natural language|"
            r"computer vision|LLMs?|MLOps|applied scientist|research scientist|reinforcement learning)\b",
            re.IGNORECASE,
        ),
    ),
    (
        Track.data_eng,
        re.compile(
            r"\b(?:data engineer(?:ing)?|analytics engineer(?:ing)?|data platform|data infrastructure|ETL|"
            r"data pipelines?|big data)\b",
            re.IGNORECASE,
        ),
    ),
    (Track.data_science, re.compile(r"\b(?:data scien(?:ce|tist)s?|quantitative|quant|statistic(?:s|ian))\b", re.I)),
    (
        Track.data_analytics,
        re.compile(
            r"\b(?:data analy(?:st|tics|sis)|business intelligence|BI|analytics|insights|reporting analyst|"
            r"business analyst|data)\b",
            re.IGNORECASE,
        ),
    ),
    (
        Track.software,
        re.compile(
            r"\b(?:software|developer|développeur|développement|programmer|back-?end|front-?end|full[- ]?stack|"
            r"mobile|ios|android|web|devops|SRE|site reliability|QA|quality assurance|test automation|"
            r"firmware|embedded|cloud|infrastructure|security engineer|platform engineer|engineering)\b",
            re.IGNORECASE,
        ),
    ),
    (
        Track.business_ops,
        re.compile(
            r"\b(?:business|operations|finance|financial|accounting|marketing|sales|product manag(?:er|ement)|"
            r"product|strategy|human resources|HR|people|talent|recruit(?:ing|er|ment)|customer success|"
            r"supply chain|legal|communications|partnerships|analyst)\b",
            re.IGNORECASE,
        ),
    ),
]


def track_from_title(title: str) -> tuple[Track, str | None]:
    for track, pattern in RULES:
        m = pattern.search(title)
        if m:
            return track, m.group(0)
    return Track.other, None


def _title_is_specific(title: str) -> bool:
    return any(pattern.search(title) for _, pattern in RULES)


def track_from_description(description: str) -> tuple[Track, str | None]:
    best: tuple[int, Track, str | None] = (0, Track.other, None)
    for track, pattern in RULES[1:-1]:  # business words are too common in descriptions to count
        hits = pattern.findall(description)
        if len(hits) >= 2 and len(hits) > best[0]:
            best = (len(hits), track, hits[0])
    return best[1], best[2]


def extract_track(title: str, description: str) -> tuple[Track, str | None]:
    if _title_is_specific(title):
        return track_from_title(title)
    return track_from_description(description)
