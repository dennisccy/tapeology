"""Source-introspection guards for the forward touch table's time column -- the
``test_desk_ui_guards.py`` pattern (read the frontend .tsx as TEXT, assert on substrings; no
browser, no runtime).

A touch time is the one stamp on this page an operator reads against a trading session they either
sat through or are about to. Rendered as raw UTC it is silently an hour off the reader's clock for
most of the year -- the difference between "at the open" and "an hour into it". Every OTHER stamp
on the page is provenance (a record id's timestamp, a window end) and correctly stays UTC.

Guards:

  (a) the cell renders through ``formatTouchLocalTime`` and keeps the served ``at_utc`` in its
      tooltip -- a localised display that discarded the raw record would put the operator a step
      away from what was actually recorded.
  (b) the conversion is the BROWSER's, and the shipped HH:MM:SS shape is pinned rather than left to
      the locale.
  (c) the column says which clock it is on. A localised time under a bare "time" header is worse
      than a UTC one: it looks like the value it replaced.
  (d) the header cannot intercept a page-wide golden assertion.

Each carries a seeded counter-test."""

from __future__ import annotations

import json
import pathlib

from test_copy_discipline import find_violations

_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
_DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"
_JOURNEY_SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[3] / "runs" / "goal-session-desk" / "journey-scripts"
)

_HEADER = "time (local)"
# The exact UTC-slice rendering this replaced. Its return would be a silent regression: the column
# would read plausibly and be wrong by the reader's offset.
_OLD_RENDERING = "touchRow.at_utc.substring(11, 19)"


def _extract_function(source: str, name: str) -> str:
    """The named function's full body by brace-walk (this suite's convention -- each guard module
    owns its own copy rather than sharing one; see ``test_desk_ui_guards.py``'s twin).

    The parameter list is walked FIRST and skipped: a component destructures its props, so the
    first ``{`` after the name opens the DESTRUCTURING PATTERN, not the body."""
    marker = f"function {name}("
    start = source.index(marker)
    paren_depth = 0
    body_start = -1
    for index in range(start + len(marker) - 1, len(source)):
        char = source[index]
        if char == "(":
            paren_depth += 1
        elif char == ")":
            paren_depth -= 1
            if paren_depth == 0:
                body_start = source.index("{", index)
                break
    assert body_start != -1, f"{name}'s parameter list never closes"
    depth = 0
    for index in range(body_start, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"{name}'s body never closes")


def test_the_function_extractor_returns_a_body_not_a_props_pattern():
    """A counter-test for the helper: if the walk stops at the destructuring pattern, every ``in``
    assertion over the result silently passes on an empty haystack."""
    seeded = "function Widget({ touch }: Props) {\n  return touch.at_utc + 1;\n}\n"
    body = _extract_function(seeded, "Widget")
    assert "touch.at_utc + 1" in body, "the extractor stopped at the props pattern"
    assert body.endswith("}")


def _unscoped_golden_assertion_texts() -> list[tuple[str, object, str]]:
    """Every literal text a shipped golden asserts PAGE-WIDE -- with no ``target`` scoping it to
    one element. Only these can be intercepted by copy rendered earlier in the DOM."""
    found: list[tuple[str, object, str]] = []
    for path in sorted(_JOURNEY_SCRIPTS_DIR.glob("J-*.json")):
        for step in json.loads(path.read_text()).get("steps", []):
            action = step.get("action") or {}
            expect = step.get("expect") or {}
            if action.get("target"):
                continue
            for text in (
                expect.get("text"),
                action.get("text") if action.get("type") == "expect" else None,
            ):
                if isinstance(text, str) and text.strip():
                    found.append((path.name, step.get("n"), text))
    return found


def test_the_touch_time_renders_local_and_keeps_the_served_stamp():
    """(a) The cell converts for display and preserves the record in its tooltip."""
    row = _extract_function(_DESK_PAGE.read_text(), "ForwardTouchRow")
    assert "formatTouchLocalTime(touchRow.at_utc)" in row, (
        "the touch time no longer renders through formatTouchLocalTime"
    )
    assert "title={touchRow.at_utc}" in row, (
        "the touch time cell no longer carries the served UTC stamp in its tooltip -- a localised "
        "value with no way back to the record is a value the operator cannot check"
    )
    assert _OLD_RENDERING not in row, (
        "the touch time is being sliced out of the UTC string again -- it would read as the "
        "reader's clock while being the reader's clock offset by their own timezone"
    )


def test_the_conversion_is_the_browsers_and_the_shape_is_pinned():
    """(b) The page must not carry its own timezone table, and must not let the locale change a
    column of trading times into 12-hour or 24:00 form."""
    helper = _extract_function(_DESK_PAGE.read_text(), "formatTouchLocalTime")
    assert "toLocaleTimeString(undefined" in helper, (
        "formatTouchLocalTime no longer defers to the browser's own zone"
    )
    assert '"h23"' in helper, "the 24-hour cycle is no longer pinned"
    for unit in ("hour", "minute", "second"):
        assert f'{unit}: "2-digit"' in helper, f"the {unit} field is no longer 2-digit"
    for forbidden in ("getTimezoneOffset", "+01:00", "Europe/", "America/", "3600"):
        assert forbidden not in helper, (
            f"formatTouchLocalTime contains {forbidden!r} -- the browser owns the zone and its "
            "daylight-time rules; a hand-rolled offset would be wrong twice a year"
        )


def test_the_column_names_the_clock_it_is_on():
    """(c) An unlabelled localised time is indistinguishable from the UTC value it replaced."""
    source = _DESK_PAGE.read_text()
    assert f"<th className={{FORWARD_TOUCH_HEAD}}>{_HEADER}</th>" in source, (
        "the touch table's time column no longer names the clock it renders on"
    )
    assert find_violations(_HEADER) == []


def test_the_touch_time_header_cannot_intercept_a_shipped_golden():
    """(d) The replay engine takes the first page-wide substring match in DOM order."""
    texts = _unscoped_golden_assertion_texts()
    assert texts, "no unscoped golden assertions found -- this guard would be vacuous"
    collisions = [
        f"{name} step {n}: {text!r}"
        for name, n, text in texts
        if text.lower() in _HEADER.lower()
    ]
    assert not collisions, (
        "the touch time header would intercept page-wide golden assertions:\n"
        + "\n".join(collisions)
    )


def test_the_touch_time_guards_can_fail_on_seeded_violations():
    """Each detection above, seeded."""
    seeded_row = (
        "function ForwardTouchRow({ touch }: Props) {\n"
        "  return <td>{touchRow.at_utc.substring(11, 19)}Z</td>;\n"
        "}\n"
    )
    row = _extract_function(seeded_row, "ForwardTouchRow")
    assert "formatTouchLocalTime(touchRow.at_utc)" not in row
    assert _OLD_RENDERING in row

    seeded_helper = (
        "function formatTouchLocalTime(atUtc: string): string {\n"
        "  return new Date(new Date(atUtc).getTime() + 3600 * 1000).toISOString();\n"
        "}\n"
    )
    helper = _extract_function(seeded_helper, "formatTouchLocalTime")
    assert "toLocaleTimeString(undefined" not in helper
    assert "3600" in helper
