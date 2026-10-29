"""A polite HTTP client: descriptive User-Agent, timeouts, and a pause between
requests to the same host."""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

USER_AGENT = "co-op-radar-canada/0.1 (student project; +https://github.com/suryalionael/co-op-radar-canada)"


class FetchError(Exception):
    """A fetch that should count as failed: network error, timeout, non-200 or bad body."""


class PoliteClient:
    def __init__(self, min_interval: float = 1.0, timeout: float = 30.0, client: httpx.Client | None = None) -> None:
        self.min_interval = min_interval
        self._client = client or httpx.Client(
            headers={"User-Agent": USER_AGENT}, timeout=timeout, follow_redirects=True
        )
        self._last_request: dict[str, float] = {}
        self._robots: dict[str, RobotFileParser | None] = {}

    def _wait_for(self, host: str) -> None:
        last = self._last_request.get(host)
        if last is not None:
            delay = self.min_interval - (time.monotonic() - last)
            if delay > 0:
                time.sleep(delay)
        self._last_request[host] = time.monotonic()

    def get(self, url: str) -> httpx.Response:
        self._wait_for(urlsplit(url).netloc)
        try:
            response = self._client.get(url)
        except httpx.HTTPError as e:
            raise FetchError(f"{type(e).__name__}: {e}") from e
        if response.status_code != 200:
            raise FetchError(f"HTTP {response.status_code}")
        return response

    def get_json(self, url: str) -> Any:
        response = self.get(url)
        try:
            return response.json()
        except ValueError as e:
            raise FetchError("response is not JSON") from e

    def allowed_by_robots(self, url: str) -> bool:
        """Check the host's robots.txt (cached per host). A missing robots.txt allows everything."""
        parts = urlsplit(url)
        host = f"{parts.scheme}://{parts.netloc}"
        if host not in self._robots:
            self._wait_for(parts.netloc)
            try:
                response = self._client.get(f"{host}/robots.txt")
            except httpx.HTTPError:
                response = None
            if response is not None and response.status_code == 200:
                parser = RobotFileParser()
                parser.parse(response.text.splitlines())
                self._robots[host] = parser
            else:
                self._robots[host] = None  # no robots.txt, or unreachable: the page fetch will report errors
        rules = self._robots[host]
        return rules is None or rules.can_fetch(USER_AGENT, url)

    def close(self) -> None:
        self._client.close()
