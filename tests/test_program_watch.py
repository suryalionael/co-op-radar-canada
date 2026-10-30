"""Program watch must flag real changes and ignore noise (v1 acceptance criterion)."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import httpx

from pipeline.models import ChangeKind
from pipeline.program_watch import build_program_watch, change_excerpt, fetch_program, main_text
from pipeline.sources.http import PoliteClient
from pipeline.storage import iter_programs_days, write_programs_day
from pipeline.text import content_hash

PAGE = """<!doctype html><html><head><title>Student jobs</title>
<script>var build = "{build}";</script><style>.x{{}}</style></head>
<body>
<nav><a href="/">Home</a><a href="/jobs">Jobs</a></nav>
<div id="onetrust-banner-sdk">We use cookies. Accept all? {cookie}</div>
<header>Big Bank Careers</header>
<main>
  <h1>Summer student program</h1>
  <p>Applications for summer 2027 {status}.</p>
  <div class="carousel"><p>Featured story: {story}</p></div>
  <p>Visited {views} times. Generated at {time}.</p>
  <p>Date modified: {modified}</p>
</main>
<footer>© {year} Big Bank. All rights reserved.</footer>
</body></html>"""

BASE = {
    "build": "a1",
    "cookie": "v1",
    "status": "will open in December",
    "story": "Meet Priya",
    "views": "1234567",
    "time": "10:42 AM",
    "modified": "2026-10-28",
    "year": "2026",
}


def page(**changes: str) -> str:
    return PAGE.format(**(BASE | changes))


def test_main_text_keeps_content_and_drops_chrome() -> None:
    text = main_text(page())
    assert "Summer student program" in text
    assert "Applications for summer 2027 will open in December." in text
    for noise in ("cookies", "Home", "Big Bank Careers", "All rights reserved", "Meet Priya", "var build"):
        assert noise not in text


def test_noise_does_not_change_the_hash() -> None:
    noisy = page(
        build="b2", cookie="v2", story="Meet Sam", views="1239999", time="3:15 PM", modified="2026-11-03", year="2027"
    )
    assert content_hash(main_text(noisy)) == content_hash(main_text(page()))


def test_session_tokens_do_not_change_the_hash() -> None:
    # Some careers sites (jobs.rbc.com, jobs.bmo.com) print a fresh 32-character hex token on every request.
    def tokened(token: str) -> str:
        return f"<main><h1>Campus</h1><p>Students apply here.</p><p>{token}</p></main>"

    a = main_text(tokened("66b7a57ae4fa47b2a60de83fdefeeb78"))
    b = main_text(tokened("62a26cb4403b4207ad92e533eedcf184"))
    assert a == b
    assert main_text(tokened("123e4567-e89b-12d3-a456-426614174000")) == a
    assert "Students apply here." in a
    # ordinary words made only of hex letters are kept
    assert "facade" in main_text("<main><p>The facade is decaf.</p></main>")


def test_real_change_changes_the_hash() -> None:
    assert main_text(page(status="are now open")) != main_text(page())


def test_change_excerpt_shows_added_lines() -> None:
    old = main_text(page())
    new = main_text(page(status="are now open"))
    assert change_excerpt(old, new) == "Applications for summer 2027 are now open."


PROGRAMS = [{"id": "bigbank_summer", "employer_id": "bigbank", "name": "Big Bank summer", "url": "https://x/students"}]


def record(html: str | None, ok: bool = True) -> dict[str, object]:
    text = main_text(html) if html else None
    return {
        "program_id": "bigbank_summer",
        "url": "https://x/students",
        "ok": ok,
        "error": None if ok else "HTTP 503",
        "text": text,
        "hash": content_hash(text) if text else None,
    }


def day(n: int) -> dt.date:
    return dt.date(2026, 11, 1) + dt.timedelta(days=n)


def test_seven_noisy_days_raise_no_alert() -> None:
    days = [
        (day(i), [record(page(time=f"{i}:00 AM", views=str(1000000 + i), story=f"Story {i}", cookie=str(i)))])
        for i in range(7)
    ]
    watch, changes = build_program_watch(PROGRAMS, days)
    assert changes == []
    assert watch[0].last_changed is None and watch[0].last_checked == day(6)


def test_failed_fetch_is_not_a_change() -> None:
    days = [(day(0), [record(page())]), (day(1), [record(None, ok=False)]), (day(2), [record(page())])]
    watch, changes = build_program_watch(PROGRAMS, days)
    assert changes == []
    assert watch[0].last_fetch_ok is True


def test_change_is_recorded_once_on_the_day_it_happens() -> None:
    days = [
        (day(0), [record(page())]),
        (day(1), [record(page())]),
        (day(2), [record(page(status="are now open"))]),
        (day(3), [record(page(status="are now open"))]),
    ]
    watch, changes = build_program_watch(PROGRAMS, days)
    assert [(c.changed_on, c.kind) for c in changes] == [(day(2), ChangeKind.content_change)]
    assert watch[0].last_changed == day(2)
    assert watch[0].change_excerpt == "Applications for summer 2027 are now open."


def test_manual_note_and_expected_open() -> None:
    programs = [
        PROGRAMS[0]
        | {
            "expected_open": dt.date(2026, 12, 1),
            "expected_open_src": "https://x/students",
            "note": "Page says applications open December 1",
            "note_date": dt.date(2026, 10, 28),
        }
    ]
    watch, changes = build_program_watch(programs, [])
    assert watch[0].expected_open == dt.date(2026, 12, 1)
    assert [c.kind for c in changes] == [ChangeKind.manual_note]


def test_fetch_program_and_storage_round_trip(tmp_path: Path) -> None:
    client = PoliteClient(min_interval=0, client=httpx.Client(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, text=page())
    )))  # fmt: skip
    now = dt.datetime(2026, 11, 1, tzinfo=dt.UTC)
    r = fetch_program(client, PROGRAMS[0], now)
    assert r["ok"] and r["hash"]
    write_programs_day(tmp_path, day(0), [r])
    [(d, records)] = list(iter_programs_days(tmp_path))
    assert d == day(0) and records[0]["hash"] == r["hash"]


def test_fetch_program_failure() -> None:
    client = PoliteClient(
        min_interval=0, client=httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(503)))
    )
    r = fetch_program(client, PROGRAMS[0], dt.datetime(2026, 11, 1, tzinfo=dt.UTC))
    assert not r["ok"] and r["error"] == "HTTP 503"


def test_config_loads_and_skips_unverified(tmp_path: Path) -> None:
    from pipeline.program_watch import load_programs

    root = Path(__file__).resolve().parent.parent
    load_programs(root / "config" / "programs.yaml")  # parses without error
    config = tmp_path / "programs.yaml"
    config.write_text(
        "programs:\n"
        "  - {id: a, employer_id: x, name: A, url: 'https://a', verified: 2026-11-01}\n"
        "  - {id: b, employer_id: x, name: B, url: 'https://b', verified: null}\n"
    )
    assert [p["id"] for p in load_programs(config)] == ["a"]


def test_robots_txt_is_respected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /students\n")
        return httpx.Response(200, text=page())

    client = PoliteClient(min_interval=0, client=httpx.Client(transport=httpx.MockTransport(handler)))
    r = fetch_program(client, PROGRAMS[0], dt.datetime(2026, 11, 1, tzinfo=dt.UTC))
    assert not r["ok"] and r["error"] == "disallowed by robots.txt"
