"""Clean an employer's job-description HTML before it is shown on our own pages.

The text comes from a third party and is rendered on our domain, so it is reduced
to a small allowlist here, in the pipeline, not in the browser:

- kept: paragraphs, line breaks, lists, bold, italic, links, and headings
  (h1-h3 become h3, h4-h6 become h4);
- links keep only an absolute https URL and get rel="noopener noreferrer nofollow";
  any other link is replaced by its text;
- every other tag is removed and its text kept, except scripts, styles, frames,
  objects, svg, templates and noscript, whose contents are dropped too;
- attributes other than a link's href are dropped, so no style or event handler survives.

Greenhouse sends its description with the markup escaped ("&lt;p&gt;"); that is
unescaped once. The output is deterministic and cleaning it again changes nothing.
"""

from __future__ import annotations

import html
from html.parser import HTMLParser
from urllib.parse import urlsplit

KEEP = {"p", "br", "ul", "ol", "li", "strong", "b", "em", "i", "a", "h3", "h4"}
HEADINGS = {"h1": "h3", "h2": "h3", "h3": "h3", "h4": "h4", "h5": "h4", "h6": "h4"}
DROP_WITH_CONTENT = {"script", "style", "iframe", "object", "embed", "svg", "noscript", "template", "head", "title"}
VOID = {"br"}
LINK_REL = "noopener noreferrer nofollow"


def _safe_href(value: str | None) -> str | None:
    """The URL if it is an absolute https link, else None."""
    if not value:
        return None
    url = "".join(ch for ch in value if ch >= " " and ch != "\x7f").strip()
    parts = urlsplit(url)
    return url if parts.scheme.lower() == "https" and parts.netloc else None


class _Cleaner(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.stack: list[str] = []
        self.skip: str | None = None  # a dropped tag whose contents are being skipped
        self.skip_depth = 0

    def _open(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = HEADINGS.get(tag, tag)
        if tag not in KEEP:
            return
        if tag == "li" and self.stack and self.stack[-1] == "li":
            self._close("li")
        if tag in {"p", "h3", "h4", "ul", "ol"} and self.stack and self.stack[-1] == "p":
            self._close("p")
        if tag == "a":
            href = _safe_href(dict(attrs).get("href"))
            if href is None:
                return
            self.out.append(f'<a href="{html.escape(href, quote=True)}" rel="{LINK_REL}">')
            self.stack.append("a")
            return
        if tag in VOID:
            self.out.append(f"<{tag}>")
            return
        self.out.append(f"<{tag}>")
        self.stack.append(tag)

    def _close(self, tag: str) -> None:
        if tag not in self.stack:
            return
        while self.stack:
            top = self.stack.pop()
            self.out.append(f"</{top}>")
            if top == tag:
                return

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if self.skip:
            if tag == self.skip:
                self.skip_depth += 1
            return
        if tag in DROP_WITH_CONTENT:
            self.skip, self.skip_depth = tag, 1
            return
        self._open(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if self.skip or tag in DROP_WITH_CONTENT:
            return  # "<script/>" opens nothing we could close
        self._open(tag, attrs)
        if tag not in VOID:
            self._close(HEADINGS.get(tag, tag))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.skip:
            if tag == self.skip:
                self.skip_depth -= 1
                if self.skip_depth == 0:
                    self.skip = None
            return
        tag = HEADINGS.get(tag, tag)
        if tag in KEEP and tag not in VOID:
            self._close(tag)

    def handle_data(self, data: str) -> None:
        if not self.skip:
            self.out.append(html.escape(data, quote=False))


def sanitize_description(raw: str) -> str:
    if not raw:
        return ""
    if "<" not in raw and "&lt;" in raw:
        raw = html.unescape(raw)
    cleaner = _Cleaner()
    cleaner.feed(raw)
    cleaner.close()
    while cleaner.stack:
        cleaner.out.append(f"</{cleaner.stack.pop()}>")
    return "".join(cleaner.out)
