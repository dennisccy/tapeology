"""Source-introspection guards for the forward touch table's time column -- the
``test_desk_ui_guards.py`` pattern (read the frontend .tsx as TEXT, assert on substrings; no
browser, no runtime).

A touch time is read against a trading session, so it renders on the session's OWN clock: US
Eastern. Rendered as raw UTC it is four or five hours off what the exchange schedule says; rendered
on the READER's clock (which this column briefly did) it is off by whatever their offset happens to
be, which makes two operators describing the same touch disagree. The exchange clock is the one
reading that is the same everywhere, and it is what every other stamp on this page now uses too.

Guards:

  (a) the cell renders through ``formatTouchEtTime`` and keeps the served ``at_utc`` in its
      tooltip -- a converted display that discarded the raw record would put the operator a step
      away from what was actually recorded.
  (b) the conversion goes through the ONE shared ET formatter (``formatTimeET``): no hand-rolled
      offset table (wrong twice a year), no reader-local rendering (the regression this replaced),
      and no slicing of a formatted string inside a block guarded against slices.
  (c) the column says which clock it is on. An unlabelled converted time is worse than a UTC one:
      it looks like the value it replaced.
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

_HEADER = "time (ET)"
# The two renderings this replaced, in order. Either one's return is a silent regression: the
# column would read plausibly and be wrong -- by a fixed 4-5h for the UTC slice, and by the
# reader's own offset for the locale conversion.
_OLD_UTC_SLICE = "touchRow.at_utc.substring(11, 19)"
_OLD_LOCAL_CONVERSION = "toLocaleTimeString"


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


def test_the_touch_time_renders_on_the_exchange_clock_and_keeps_the_served_stamp():
    """(a) The cell converts for display and preserves the record in its tooltip."""
    row = _extract_function(_DESK_PAGE.read_text(), "ForwardTouchRow")
    assert "formatTouchEtTime(touchRow.at_utc)" in row, (
        "the touch time no longer renders through formatTouchEtTime"
    )
    assert "touchRow.at_utc} (raw UTC record)" in row, (
        "the touch time cell no longer carries the served UTC stamp in its tooltip -- a converted "
        "value with no way back to the record is a value the operator cannot check"
    )
    assert _OLD_UTC_SLICE not in row, (
        "the touch time is being sliced out of the UTC string again -- it would read as a session "
        "time while being four or five hours off the session"
    )


def test_the_conversion_goes_through_the_one_shared_et_formatter():
    """(b) The page must not carry its own timezone table, and must not fall back to the reader's
    own clock -- the two ways this column has been wrong before.

    The time-alone shape comes from the shared module's own `formatTimeET` rather than from slicing
    a full stamp here. That is not cosmetic: this cell sits inside the Forward Returns block, which
    `test_desk_forward_ui_guard` scans for `.sort(`/`.reverse(`/`.slice(` so no row set can be
    quietly reordered or capped -- and a string slice is indistinguishable from a row slice to that
    scan. Formatting belongs in the formatter module either way."""
    source = _DESK_PAGE.read_text()
    helper = _extract_function(source, "formatTouchEtTime")
    assert "formatTimeET(atUtc" in helper, (
        "formatTouchEtTime no longer defers to the one shared ET formatter"
    )
    assert ".slice(" not in helper, (
        "formatTouchEtTime is slicing a formatted string again -- the shared module owns the "
        "time-alone shape, and this block's no-reorder/no-cap guard cannot tell a string slice "
        "from a row slice"
    )
    assert _OLD_LOCAL_CONVERSION not in helper, (
        "formatTouchEtTime renders on the reader's own clock again -- two operators in different "
        "zones would read different times for the same touch"
    )
    for forbidden in ("getTimezoneOffset", "+01:00", "-04:00", "-05:00", "Europe/", "3600"):
        assert forbidden not in helper, (
            f"formatTouchEtTime contains {forbidden!r} -- the shared formatter owns the zone and "
            "its daylight-time rules; a hand-rolled offset would be wrong twice a year"
        )
    # The zone belongs to the shared module, named once, never restated per call site -- and so
    # does the formatter the helper defers to.
    datetime_lib = (_FRONTEND_ROOT / "lib" / "datetime.ts").read_text()
    assert 'US_MARKET_TZ = "America/New_York"' in datetime_lib, (
        "the market zone is no longer named once in lib/datetime.ts"
    )
    assert "export function formatTimeET(" in datetime_lib, (
        "formatTimeET is no longer exported from lib/datetime.ts -- the touch column would have "
        "nowhere to get a market-clock time except by rolling its own"
    )


def test_the_column_names_the_clock_it_is_on():
    """(c) An unlabelled converted time is indistinguishable from the UTC value it replaced.

    A deliberate, PAID-FOR re-expression, recorded rather than hidden. This used to pin the literal
    markup ``<th className={FORWARD_TOUCH_HEAD}>time (ET)</th>``. The touch table's leaf headers are
    now rendered by the shared `SortableHeader`, so that exact element no longer exists -- but the
    PROPERTY it protected is unchanged and is asserted directly instead: the touch table has a
    column whose header text names the clock, and it is the column that reads the touch instant.

    The header text itself is byte-identical; only the element wrapping it moved. What bounds the
    move is `SortableHeader` rendering `column.label` VERBATIM, pinned by
    apps/backend/tests/test_table_sort_guards.py::test_the_header_renders_the_columns_own_label --
    without that, a shared component could quietly re-word every header on the page."""
    source = _DESK_PAGE.read_text()
    start = source.index("function forwardTouchColumns(")
    body = source[start : source.index("function ForwardTouchTable(")]
    assert f'label: "{_HEADER}"' in body, (
        "the touch table's time column no longer names the clock it renders on"
    )
    # ...and it is the column reading the touch's own instant, not some other column that happens
    # to carry the label.
    time_column = body[body.index(f'label: "{_HEADER}"') :]
    time_column = time_column[: time_column.index("},")]
    assert "touch.at_utc" in time_column, (
        f"the {_HEADER!r} column no longer reads the touch instant -- the label would be naming a "
        "clock some other value is on"
    )
    assert find_violations(_HEADER) == []


def test_the_clock_column_guard_can_fail_on_a_seeded_violation():
    """A lint that cannot fail proves nothing: an unlabelled or mis-bound time column is caught."""
    seeded = 'function forwardTouchColumns() { { id: "at", label: "time", value: (touch) => touch.at_utc }, }function ForwardTouchTable('
    body = seeded[: seeded.index("function ForwardTouchTable(")]
    assert f'label: "{_HEADER}"' not in body


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
    assert "formatTouchEtTime(touchRow.at_utc)" not in row
    assert _OLD_UTC_SLICE in row

    seeded_offset_helper = (
        "function formatTouchEtTime(atUtc: string): string {\n"
        "  return new Date(new Date(atUtc).getTime() - 4 * 3600 * 1000).toISOString();\n"
        "}\n"
    )
    helper = _extract_function(seeded_offset_helper, "formatTouchEtTime")
    assert "formatTimeET(atUtc" not in helper
    assert "3600" in helper

    # The slice this replaced: correct output, but invisible to the block's no-reorder/no-cap guard
    # as anything other than a slice.
    seeded_sliced_helper = (
        "function formatTouchEtTime(atUtc: string): string {\n"
        "  return formatDateTimeET(atUtc, { zone: false }).slice(11);\n"
        "}\n"
    )
    sliced = _extract_function(seeded_sliced_helper, "formatTouchEtTime")
    assert ".slice(" in sliced

    seeded_local_helper = (
        "function formatTouchEtTime(atUtc: string): string {\n"
        "  return new Date(atUtc).toLocaleTimeString(undefined, { hourCycle: 'h23' });\n"
        "}\n"
    )
    local_helper = _extract_function(seeded_local_helper, "formatTouchEtTime")
    assert _OLD_LOCAL_CONVERSION in local_helper
