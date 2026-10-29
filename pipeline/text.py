"""Small text helpers shared across the pipeline."""

from __future__ import annotations

import hashlib
import html
import re

_BLOCK_TAGS = re.compile(r"</?(?:p|div|br|li|ul|ol|h[1-6]|tr|section)\b[^>]*>", re.IGNORECASE)
_TAG = re.compile(r"<[^>]+>")
_SPACES = re.compile(r"[ \t ]+")
_BLANK_LINES = re.compile(r"\n\s*\n+")


def html_to_text(raw: str) -> str:
    """Plain text from description HTML, keeping paragraph breaks.

    Greenhouse escapes its HTML once (&lt;p&gt;), so unescape before stripping tags.
    """
    text = html.unescape(raw or "")
    text = _BLOCK_TAGS.sub("\n", text)
    text = html.unescape(_TAG.sub(" ", text))
    text = _SPACES.sub(" ", text)
    return _BLANK_LINES.sub("\n", text).strip()


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
