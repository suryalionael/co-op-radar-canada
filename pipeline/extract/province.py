"""Province and remote/hybrid extractor, from the location fields only.

- Every province named in the location (city, full name, or a two-letter code
  in a location context) goes into `provinces`, in order; `province` is the first.
- A remote posting that names Canada but no province is REMOTE_CA.
- A posting that names Canada but no province and is not remote is in Canada
  with province UNKNOWN.
- Anything else is outside Canada as far as the location says.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from pipeline.geo import CANADA_PATTERN, find_provinces
from pipeline.models import Province, Remote

REMOTE = re.compile(r"\b(?:remote|work from home|wfh|télétravail|à distance)\b", re.IGNORECASE)
HYBRID = re.compile(r"\b(?:hybrid|hybride)\b", re.IGNORECASE)
ONSITE = re.compile(r"\b(?:on-?site|in[- ]office|in[- ]person|sur place)\b", re.IGNORECASE)


@dataclass
class LocationResult:
    in_canada: bool = False
    provinces: list[Province] = field(default_factory=list)
    remote: Remote = Remote.unknown
    province_evidence: str | None = None
    remote_evidence: str | None = None

    @property
    def province(self) -> Province:
        return self.provinces[0] if self.provinces else Province.UNKNOWN


def extract_remote(location: str, workplace_hint: str = "") -> tuple[Remote, str | None]:
    for text in (location, workplace_hint):
        for pattern, value in ((HYBRID, Remote.hybrid), (REMOTE, Remote.remote), (ONSITE, Remote.onsite)):
            m = pattern.search(text)
            if m:
                return value, m.group(0)
    return Remote.unknown, None


def extract_location(location: str, workplace_hint: str = "") -> LocationResult:
    result = LocationResult()
    result.remote, result.remote_evidence = extract_remote(location, workplace_hint)
    found = find_provinces(location)
    if found:
        result.in_canada = True
        result.provinces = [p for p, _ in found]
        result.province_evidence = " / ".join(text for _, text in found)
        return result
    canada = CANADA_PATTERN.search(location)
    if canada:
        result.in_canada = True
        result.province_evidence = canada.group(0)
        if result.remote == Remote.remote:
            result.provinces = [Province.REMOTE_CA]
    return result
