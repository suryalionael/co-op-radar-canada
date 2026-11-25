"""Employer HTML is cleaned to a small allowlist before it is shown on our domain."""

from __future__ import annotations

import time

import pytest

from pipeline.sanitize import sanitize_description


@pytest.mark.parametrize(
    ("raw", "clean"),
    [
        ("<p>Hello <strong>you</strong></p>", "<p>Hello <strong>you</strong></p>"),
        ("<script>alert(1)</script><p>x</p>", "<p>x</p>"),
        ("<style>p{}</style><p>x</p>", "<p>x</p>"),
        ('<iframe src="https://e.com"></iframe><p>x</p>', "<p>x</p>"),
        ("<svg><script>1</script></svg><p>x</p>", "<p>x</p>"),
        ('<p onclick="x()" style="color:red">a</p>', "<p>a</p>"),
        ('<a href="javascript:alert(1)">x</a>', "x"),
        ('<a href="JaVaScRiPt:alert(1)">x</a>', "x"),
        ('<a href="http://e.com">x</a>', "x"),
        ('<a href="//e.com">x</a>', "x"),
        (
            '<a href="https://e.com/a?b=1&c=2" target="_self">x</a>',
            '<a href="https://e.com/a?b=1&amp;c=2" rel="noopener noreferrer nofollow">x</a>',
        ),
        ("<img src=x onerror=alert(1)>", ""),
        ("<h1>T</h1><h2>U</h2><h5>S</h5>", "<h3>T</h3><h3>U</h3><h4>S</h4>"),
        ("<div><span>t</span></div>", "t"),
        ("<ul><li>a<li>b", "<ul><li>a</li><li>b</li></ul>"),
        ("&lt;p&gt;Hi&lt;/p&gt;", "<p>Hi</p>"),
        ("&lt;p&gt;a &amp;amp; b&lt;/p&gt;", "<p>a &amp; b</p>"),
        ("Plain text & more", "Plain text &amp; more"),
        ("<p>5 &lt; 6</p>", "<p>5 &lt; 6</p>"),
        ("<p>a<br>b</p>", "<p>a<br>b</p>"),
        ("", ""),
    ],
)
def test_sanitize(raw: str, clean: str) -> None:
    assert sanitize_description(raw) == clean


def test_idempotent_and_deterministic() -> None:
    raw = '<h1>A</h1><p onclick="x">b <a href="https://e.com">c</a></p><ul><li>d<li>e</ul><script>x</script>'
    once = sanitize_description(raw)
    assert sanitize_description(once) == once
    assert sanitize_description(raw) == once


def test_large_input_is_fast() -> None:
    raw = "<p>" + ("word <b>bold</b> " * 40) + "</p>"
    big = raw * 2500  # about 2 MB
    start = time.perf_counter()
    assert sanitize_description(big).startswith("<p>")
    assert time.perf_counter() - start < 2


def test_no_event_handler_or_script_survives_in_hostile_soup() -> None:
    raw = '<p><b onmouseover="x()">a</b><SCRIPT>bad()</SCRIPT><a href=" javascript:x()">y</a><img src=//e/x.png></p>'
    out = sanitize_description(raw).lower()
    for needle in ("script", "onmouseover", "javascript", "<img", "bad()"):
        assert needle not in out
