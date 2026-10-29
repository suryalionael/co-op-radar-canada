"""Canadian place names, and the loose Canada filter used at fetch time (ADR 0002)."""

from __future__ import annotations

import re

from pipeline.models import Province

PROVINCE_NAMES: dict[str, Province] = {
    "ontario": Province.ON,
    "quebec": Province.QC,
    "québec": Province.QC,
    "british columbia": Province.BC,
    "colombie-britannique": Province.BC,
    "alberta": Province.AB,
    "manitoba": Province.MB,
    "saskatchewan": Province.SK,
    "nova scotia": Province.NS,
    "nouvelle-écosse": Province.NS,
    "new brunswick": Province.NB,
    "nouveau-brunswick": Province.NB,
    "newfoundland": Province.NL,
    "labrador": Province.NL,
    "prince edward island": Province.PE,
    "yukon": Province.YT,
    "northwest territories": Province.NT,
    "nunavut": Province.NU,
}

# Cities that name one province on their own. Places that share a name with a
# bigger city elsewhere (London, Victoria, Hamilton, Kingston, Windsor, Richmond,
# Cambridge, Surrey) are matched only when the
# province is also named, so they are left out of this list on purpose.
CITIES: dict[str, Province] = {
    **dict.fromkeys(
        [
            "toronto",
            "ottawa",
            "mississauga",
            "brampton",
            "markham",
            "vaughan",
            "oakville",
            "burlington",
            "richmond hill",
            "north york",
            "scarborough",
            "etobicoke",
            "kitchener",
            "waterloo",
            "kitchener-waterloo",
            "guelph",
            "barrie",
            "oshawa",
            "sudbury",
            "thunder bay",
            "st. catharines",
            "niagara falls",
            "peterborough",
            "pickering",
            "ajax",
            "whitby",
            "milton",
            "thornhill",
        ],
        Province.ON,
    ),
    **dict.fromkeys(
        [
            "montreal",
            "montréal",
            "quebec city",
            "québec city",
            "ville de québec",
            "laval",
            "gatineau",
            "longueuil",
            "sherbrooke",
            "trois-rivières",
            "lévis",
            "saguenay",
            "boucherville",
            "brossard",
        ],
        Province.QC,
    ),
    **dict.fromkeys(
        ["vancouver", "burnaby", "kelowna", "nanaimo", "coquitlam", "abbotsford", "north vancouver", "kamloops"],
        Province.BC,
    ),
    **dict.fromkeys(["calgary", "edmonton", "lethbridge", "red deer"], Province.AB),
    **dict.fromkeys(["winnipeg", "brandon"], Province.MB),
    **dict.fromkeys(["regina", "saskatoon"], Province.SK),
    **dict.fromkeys(["halifax", "dartmouth"], Province.NS),
    **dict.fromkeys(["moncton", "fredericton", "saint john"], Province.NB),
    **dict.fromkeys(["st. john's", "st john's"], Province.NL),
    **dict.fromkeys(["charlottetown"], Province.PE),
    **dict.fromkeys(["whitehorse"], Province.YT),
    **dict.fromkeys(["yellowknife"], Province.NT),
    **dict.fromkeys(["iqaluit"], Province.NU),
}

_NAMES = {**PROVINCE_NAMES, **CITIES}
# Longest first, so "north vancouver" wins over "vancouver" and "quebec city" over "quebec".
NAME_PATTERN = re.compile(
    r"(?<![\w-])(" + "|".join(re.escape(n) for n in sorted(_NAMES, key=len, reverse=True)) + r")(?![\w-])",
    re.IGNORECASE,
)

PROVINCE_CODES = [p.value for p in Province if len(p.value) == 2]
# Two-letter codes count only in a location context: capitals, after a separator
# or the start, and before a separator or the end. "Toronto, ON" and "Remote - BC"
# match; "Turn ON the lights" does not.
CODE_PATTERN = re.compile(r"(?:^|[,\-–/(|]\s*)(" + "|".join(PROVINCE_CODES) + r")(?=\s*(?:$|[,\-–/)|;]))")
CANADA_PATTERN = re.compile(r"\bcanada\b", re.IGNORECASE)
REMOTE_PATTERN = re.compile(r"\bremote\b", re.IGNORECASE)


def find_provinces(location: str) -> list[tuple[Province, str]]:
    """Every province named in a location string, in order, with the text that named it."""
    found: list[tuple[int, Province, str]] = []
    for m in NAME_PATTERN.finditer(location):
        found.append((m.start(), _NAMES[m.group(1).lower()], m.group(1)))
    for m in CODE_PATTERN.finditer(location):
        found.append((m.start(1), Province(m.group(1)), m.group(1)))
    found.sort(key=lambda f: f[0])
    seen: set[Province] = set()
    out = []
    for _, province, text in found:
        if province not in seen:
            seen.add(province)
            out.append((province, text))
    return out


def mentions_canada(text: str) -> bool:
    return bool(CANADA_PATTERN.search(text) or find_provinces(text))


def passes_loose_filter(location: str, title: str, description_text: str) -> bool:
    """Keep a posting if any of its text mentions a Canadian place or "remote".

    Deliberately a superset of what the site shows, so a better province
    extractor later never lacks data (ADR 0002).
    """
    text = f"{location}\n{title}\n{description_text}"
    return mentions_canada(text) or bool(REMOTE_PATTERN.search(text))
