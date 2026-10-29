"""Job-board sources. Each module turns one platform's public API response into RawPostings."""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from typing import Any

from pipeline.geo import passes_loose_filter
from pipeline.models import BoardFetch, RawPosting, Source
from pipeline.sources import ashby, greenhouse, lever
from pipeline.sources.http import FetchError, PoliteClient
from pipeline.text import content_hash, html_to_text

Parser = Callable[[Any, str, str], list[RawPosting]]

PLATFORMS: dict[Source, tuple[Callable[[str], str], Parser]] = {
    Source.greenhouse: (greenhouse.board_url, greenhouse.parse),
    Source.lever: (lever.board_url, lever.parse),
    Source.ashby: (ashby.board_url, ashby.parse),
}


def keep_canadian(postings: list[RawPosting]) -> list[RawPosting]:
    """Apply the loose Canada filter and fill in each description hash."""
    kept = []
    for p in postings:
        if passes_loose_filter(p.location_raw, p.title, html_to_text(p.description_html)):
            kept.append(p.model_copy(update={"description_hash": content_hash(p.description_html)}))
    return kept


def fetch_board(
    client: PoliteClient, employer: dict[str, Any], now: dt.datetime | None = None
) -> tuple[BoardFetch, list[RawPosting]]:
    """Fetch one board. Never raises for source problems: failures come back as ok=False."""
    source = Source(employer["board_type"])
    token, employer_id = employer["board_token"], employer["id"]
    board_url, parse = PLATFORMS[source]
    fetched_at = now or dt.datetime.now(dt.UTC)
    try:
        postings = parse(client.get_json(board_url(token)), employer_id, token)
    except (FetchError, ValueError, KeyError, TypeError) as e:
        status = BoardFetch(
            source=source, board_token=token, employer_id=employer_id, fetched_at=fetched_at, ok=False, error=str(e)
        )
        return status, []
    kept = keep_canadian(postings)
    status = BoardFetch(
        source=source,
        board_token=token,
        employer_id=employer_id,
        fetched_at=fetched_at,
        ok=True,
        job_count=len(postings),
        kept_count=len(kept),
    )
    return status, kept
