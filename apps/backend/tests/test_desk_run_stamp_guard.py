"""Source-introspection guards for the Run Screen day stamp -- the ``test_desk_ui_guards.py``
pattern (read the frontend .tsx as TEXT, assert on substrings; no browser, no runtime).

Run Screen used to submit today's UTC calendar date. A screen dated D is marked up from the last
completed session BEFORE D and measured on D's own session, so the useful stamp is the next session
an operator can still act on -- and today's UTC date stops being that the moment the US close
passes. For anyone east of New York the gap is the ordinary evening case, not an edge case: at
22:00 in London the US session closed an hour ago, the UTC date has not rolled, and the old stamp
recorded a screen for a session already over. Saturdays and Sundays stamped a date with no session
at all.

``nextTradingStamp`` keys on the absolute close instant -- 16:00 US eastern -- so the operator's
own timezone never enters the result.

It used to reach that instant by hand: two UTC close hours (20 and 21) picked apart by a
``isUsEasternDaylightDate`` predicate that re-derived the second-Sunday-of-March and
first-Sunday-of-November boundaries itself. That is a rule the US Congress has moved before and can
move again, restated in this page rather than looked up. It now reads the ET wall-clock hour
straight off ``formatDateTimeET``, whose zone comes from the IANA database via ``Intl``, so the
daylight-time rule is data rather than arithmetic and there is exactly one close hour to name.
These guards pin THAT structure; the counter-tests below still name the two deleted constants so
the hand-rolled table cannot quietly return.

Guards:

  (a) the resolver is WIRED -- the blank-To default and the ceiling in ``validateScreenDayRange``
      both come from ``nextTradingStamp``, and neither is still ``todayUtcDate()``. A stamp the
      submit path does not use is decoration.
  (b) the resolver keys on the close instant -- it takes an injectable ``now``, resolves both the
      day and the hour through the ONE shared ET formatter, and names its close hour once. It reads
      no clock of its own beyond ``now``, carries no offset table, and fetches nothing.
  (c) the target is STATED before the click, and its copy clears the lint.
  (d) that copy cannot intercept a page-wide golden assertion.

Each carries a seeded counter-test proving the detection actually catches a violation.

The stamp's boundary BEHAVIOUR (the close minute, the weekend roll, both daylight-time edges) is
not assertable here -- this repo runs no frontend test runner, which is why ``now`` is a parameter:
the boundaries are exercised deterministically by compiling the shipped functions and driving them
with fixed instants. These guards pin the STRUCTURE that behaviour depends on."""

from __future__ import annotations

import json
import pathlib
import re

from test_copy_discipline import find_violations

_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
_DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"
_JOURNEY_SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[3] / "runs" / "goal-session-desk" / "journey-scripts"
)

_STAMP_TESTID = 'data-testid="desk-run-screen-stamp"'

# The stamp copy as an operator READS it (the JSX carries an interpolation, so the shipped literal
# is never a complete sentence in source).
_RENDERED_STAMP = "Run Screen will record 2026-08-06."

# Copy whose meaning changed with the resolver: both now name the upcoming session rather than
# today, and neither says "UTC" -- the resolved day is a US session date, not a timezone the
# operator has to translate.
_RENDERED_COPY = (
    _RENDERED_STAMP,
    "To day (US market day) — blank = upcoming US session",
    "From day (US market day) — blank = the To day",
    "Enter the To day as a real yyyy-MM-dd, or leave it blank for the upcoming US session date.",
    "The To day is after the upcoming US session date — a run can cover that day or any earlier day.",
)


def _skip_return_type(source: str, index: int) -> int:
    """Advance past an OBJECT return-type annotation, so the brace-walk below finds the body.

    ``validateScreenDayRange`` is declared ``): { error: …; range: … } {`` -- the annotation's own
    braces balance, so the sibling copies of this helper (which walk to the first ``{`` after the
    parameter list) hand back the TYPE and every assertion runs against a haystack that is not the
    function. Their targets have no object return type, so they are correct as written; this copy
    needs the extra step. A non-object annotation (``: string | null``) contains no brace and falls
    through untouched."""
    cursor = index
    while cursor < len(source) and source[cursor].isspace():
        cursor += 1
    if cursor >= len(source) or source[cursor] != ":":
        return index
    cursor += 1
    while cursor < len(source) and source[cursor].isspace():
        cursor += 1
    if cursor < len(source) and source[cursor] == "{":
        depth = 0
        while cursor < len(source):
            if source[cursor] == "{":
                depth += 1
            elif source[cursor] == "}":
                depth -= 1
                if depth == 0:
                    return cursor + 1
            cursor += 1
    return cursor


def _extract_function(source: str, name: str) -> str:
    """The named function's full body by brace-walk (this suite's convention -- each guard module
    owns its own copy rather than sharing one; see ``test_desk_ui_guards.py``'s twin).

    The parameter list is walked FIRST and skipped: a component destructures its props, so the
    first ``{`` after the name opens the DESTRUCTURING PATTERN, not the body -- walking from there
    would return a props pattern and every assertion over it would pass on an empty haystack. An
    object return-type annotation is skipped for the same reason (``_skip_return_type``)."""
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
                body_start = source.index("{", _skip_return_type(source, index + 1))
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
    seeded = "function Widget({ runDay }: Props) {\n  return runDay + 1;\n}\n"
    body = _extract_function(seeded, "Widget")
    assert "runDay + 1" in body, "the extractor stopped at the props pattern"
    assert body.endswith("}")


def test_the_function_extractor_skips_an_object_return_type():
    """The failure this copy exists to avoid: an annotated `): { … } {` signature whose type braces
    balance, handing back the TYPE as if it were the body."""
    seeded = (
        "function Validate(raw: string): { error: string | null; ok: boolean } {\n"
        "  return { error: null, ok: true };\n"
        "}\n"
    )
    body = _extract_function(seeded, "Validate")
    assert "return { error: null, ok: true };" in body, (
        "the extractor stopped at the return-type annotation"
    )


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


def test_the_submitted_day_resolves_through_the_session_stamp():
    """(a) Both the blank-To default and the ceiling come from ``nextTradingStamp``. The ceiling
    matters as much as the default: a stamp of tomorrow that the ceiling still measured against
    today would refuse the very day the control just offered."""
    validator = _extract_function(_DESK_PAGE.read_text(), "validateScreenDayRange")
    assert "const stamp = nextTradingStamp();" in validator, (
        "validateScreenDayRange no longer resolves the run day through nextTradingStamp"
    )
    assert 'toRaw.trim() === "" ? stamp : toRaw.trim()' in validator, (
        "a blank To day no longer resolves to the upcoming session"
    )
    assert "if (toValue > stamp)" in validator, (
        "the To-day ceiling is not the upcoming session date"
    )
    assert "todayUtcDate()" not in validator, (
        "validateScreenDayRange still reads today's UTC date -- after the US close that is a "
        "session already over, which is the whole defect the stamp exists to fix"
    )


def test_the_stamp_keys_on_the_close_instant_not_the_operators_clock():
    """(b) The resolver's structure: an injectable ``now``, both the day and the close-hour
    comparison read through the ONE shared ET formatter, one named close hour, and a weekday branch
    taken on the MARKET date. Nothing here may read a clock of its own or fetch."""
    source = _DESK_PAGE.read_text()
    stamp = _extract_function(source, "nextTradingStamp")
    assert "now: Date = new Date()" in stamp, (
        "nextTradingStamp no longer takes an injectable `now` -- its boundaries would become "
        "unexercisable, and this repo has no frontend test runner to catch that"
    )
    assert "getUTCDay()" in stamp, "nextTradingStamp no longer branches on the UTC weekday"
    # The day and the hour BOTH come from the shared formatter. Deriving either from `now`'s own
    # local or UTC fields is the regression class this whole guard exists for: two operators in
    # different zones would stamp different sessions from the same instant.
    assert "formatDateET(now)" in stamp, (
        "nextTradingStamp no longer resolves the market DATE through the shared ET formatter"
    )
    assert "formatDateTimeET(now" in stamp, (
        "nextTradingStamp no longer reads the market HOUR through the shared ET formatter -- a "
        "close comparison against the operator's own hour is wrong everywhere but New York"
    )
    assert "US_CLOSE_HOUR_ET" in stamp, "nextTradingStamp no longer reads US_CLOSE_HOUR_ET"
    assert "const US_CLOSE_HOUR_ET = 16;" in source, (
        "the close hour is no longer named once as an ET wall-clock hour"
    )
    for forbidden in ("fetch(", "Math.random", "toLocaleDateString", "getTimezoneOffset"):
        assert forbidden not in stamp, (
            f"nextTradingStamp contains {forbidden!r} -- the stamp must be a pure function of the "
            "absolute instant, never of where the operator happens to be"
        )
    # The hand-rolled daylight-time table this replaced must not come back. Its two UTC close hours
    # and its own second-Sunday/first-Sunday arithmetic restated a rule that has been legislated
    # more than once; the IANA zone behind `formatDateTimeET` is the maintained copy of it.
    for retired in (
        "US_CLOSE_HOUR_UTC_DAYLIGHT",
        "US_CLOSE_HOUR_UTC_STANDARD",
        "isUsEasternDaylightDate",
        "nthSundayUtc",
    ):
        assert retired not in source, (
            f"{retired!r} is back on the page -- the daylight-time rule belongs to the IANA zone "
            "the shared formatter reads, never to hand-written boundary arithmetic here"
        )
    # The zone itself is named exactly once, in the shared module.
    datetime_lib = (_FRONTEND_ROOT / "lib" / "datetime.ts").read_text()
    assert 'US_MARKET_TZ = "America/New_York"' in datetime_lib, (
        "the market zone is no longer named once in lib/datetime.ts"
    )


def test_the_target_day_is_stated_before_the_click():
    """(c) The control names the day it will submit. Without it the operator's only way to learn
    that an evening click stamps tomorrow is to click and read the result."""
    control = _extract_function(_DESK_PAGE.read_text(), "ScreenComputeControl")
    assert _STAMP_TESTID in control, "the Run Screen control no longer states the day it submits"
    assert "Run Screen will record {runDay}." in control, (
        "the stamp line no longer names the resolved run day"
    )
    for rendered in _RENDERED_COPY:
        assert find_violations(rendered) == [], (
            f"the run-stamp copy carries imperative/predictive/claim language: {rendered!r}"
        )


def test_the_shipped_labels_no_longer_promise_today():
    """(c, cont.) The two field labels and both To-day errors ship the reworded copy -- a label
    still reading "blank = today" would contradict what the control now does."""
    source = _DESK_PAGE.read_text()
    for rendered in _RENDERED_COPY[1:]:
        assert rendered in source, f"the reworded copy no longer ships: {rendered!r}"
    assert "To day (UTC) — blank = today" not in source, (
        "the To-day label still promises today"
    )
    assert re.search(r"blank it? blank to run today", source) is None
    # The fields name the SESSION they submit, not a timezone. `(UTC)` on a day field asked the
    # operator to translate a value that has no clock to translate.
    assert "(UTC)" not in source, (
        "a day field is labelled with a timezone again -- these submit a bare US market date, and "
        "naming a zone on a value with no clock is an instruction to convert nothing"
    )


def test_the_run_stamp_copy_cannot_intercept_a_shipped_golden():
    """(d) The replay engine takes the first page-wide substring match in DOM order, so copy that
    contains a golden's pinned text silently resolves the assertion here."""
    texts = _unscoped_golden_assertion_texts()
    assert texts, "no unscoped golden assertions found -- this guard would be vacuous"
    collisions = [
        f"{name} step {n}: {text!r} collides with {rendered!r}"
        for name, n, text in texts
        for rendered in _RENDERED_COPY
        if text.lower() in rendered.lower()
    ]
    assert not collisions, (
        "the run-stamp copy would intercept page-wide golden assertions:\n" + "\n".join(collisions)
    )


def test_the_run_stamp_guards_can_fail_on_seeded_violations():
    """Each detection above, seeded."""
    seeded_validator = (
        "function validateScreenDayRange(fromRaw: string, toRaw: string): Result {\n"
        '  const today = todayUtcDate();\n'
        '  const toValue = toRaw.trim() === "" ? today : toRaw.trim();\n'
        "  return { error: null, range: null };\n"
        "}\n"
    )
    validator = _extract_function(seeded_validator, "validateScreenDayRange")
    assert "const stamp = nextTradingStamp();" not in validator
    assert "todayUtcDate()" in validator

    seeded_stamp = (
        "function nextTradingStamp(): string {\n"
        "  return new Date().toISOString().slice(0, 10);\n"
        "}\n"
    )
    stamp = _extract_function(seeded_stamp, "nextTradingStamp")
    assert "now: Date = new Date()" not in stamp
    assert "getUTCDay()" not in stamp
    assert "formatDateET(now)" not in stamp
    assert "US_CLOSE_HOUR_ET" not in stamp

    # The two ways the clock can go wrong that a bare "does it compile" check would not see: the
    # operator's own hour standing in for the exchange's, and a re-hand-rolled daylight-time table.
    seeded_local_stamp = (
        "function nextTradingStamp(now: Date = new Date()): string {\n"
        "  const etHour = now.getHours();\n"
        "  return now.toISOString().slice(0, 10);\n"
        "}\n"
    )
    local_stamp = _extract_function(seeded_local_stamp, "nextTradingStamp")
    assert "formatDateTimeET(now" not in local_stamp

    seeded_dst_table = (
        "const US_CLOSE_HOUR_UTC_DAYLIGHT = 20;\n"
        "function isUsEasternDaylightDate(iso: string): boolean { return true; }\n"
    )
    assert any(
        retired in seeded_dst_table
        for retired in ("US_CLOSE_HOUR_UTC_DAYLIGHT", "isUsEasternDaylightDate")
    )

    seeded_control = "function ScreenComputeControl({ runDay }: Props) {\n  return null;\n}\n"
    assert _STAMP_TESTID not in _extract_function(seeded_control, "ScreenComputeControl")

    assert "upcoming us session" in _RENDERED_COPY[1].lower()
    assert find_violations("Run Screen will record it — price will break the wall.") != []
