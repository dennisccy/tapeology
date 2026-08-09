"""Source-introspection guards for the ``/desk`` chained refresh control -- the
``test_desk_ui_guards.py`` pattern (read the frontend .tsx as TEXT, assert on structure; no
browser, no runtime).

The control runs five refresh acts in order -- the universe membership fetch, the bar top-up, the
bar index reconciliation, the screen for each day of the as-of range, then the forward returns for
every snapshot that run recorded -- by driving the SAME five endpoints the page's existing controls
already drive. These guards pin the four properties that make that safe:

  (a) **No mount path.** No ``useEffect`` argument list anywhere in the page references the chain
      driver or any compute trigger. This is the era's own critical anti-goal ("Every run is an
      explicit operator act ... page-load GETs never trigger fetches or computes") and it now
      covers the three already-shipped buttons too, not only the new one.
  (b) **The entry point is click-only.** ``handleRefreshAll`` appears in exactly two syntactic
      shapes -- its own declaration, and the single props binding -- and the button carries a
      plain ``onClick`` with no focus/ref auto-invocation.
  (c) **No second trigger path.** The driver calls the four EXISTING ``handleTrigger*`` handlers,
      never the raw ``lib/api`` clients and never a bare ``fetch(`` -- the
      ``test_structure_prefill_reuses_the_existing_load_function`` precedent applied to this
      block. It also owns no poll of its own: the page has exactly one ``setInterval(`` per
      compute manager (four, forward-test era), because the chain WAITS on the state the existing
      poll effects already maintain.
  (d) **Honest step semantics.** The five steps appear once each, in order; the chain advances on
      ``"done"`` and halts on ``"failed"``/``"cancelled"``; and ``started`` is never used as a
      halt condition, because ``started: false`` means a job was already running and was adopted.

The backend contracts these depend on are already pinned hermetically elsewhere and are NOT
duplicated here: single-flight re-POST returning ``started is False``
(``test_desk_topup_compute.py``, ``test_desk_screen_compute.py``, ``test_desk_index_reconcile.py``)
and the 409 duplicate-membership refusal (``test_desk_universe_api.py``).

WHAT THESE GUARDS CANNOT PROVE -- stated plainly, because a guard whose limits are unstated gets
trusted past them:

  * They prove no *lexical* trigger call sits inside a ``useEffect(`` argument list. They do NOT
    prove no POST happens on mount at runtime. An INDIRECT path defeats them -- effect A sets a
    flag that effect B reads and acts on, a lazy ``useState(() => ...)`` initializer, a ref
    callback, a child component's own effect. The specific machinery that could do this is banned
    by name below, but an enumeration is not a proof.
  * The paren/brace walks are naive: a ``)`` or ``}`` inside a string, template or regex literal
    within an effect body truncates the extracted block, and the scan would then under-report.
    Comment-stripping plus the non-vacuity assertions turn most mis-walks into loud failures
    rather than silent passes -- but not all of them.
  * They prove source structure, never behaviour. Nothing here executes a line of TSX.

The only real proof of "fires only on click" is the runtime one: load the page repeatedly with no
click and observe that all four compute snapshots keep their ``id`` and ``started_utc``, and every
durable run ledger keeps its length -- a fifth STEP must not add a mount POST. That check and every
other runtime claim here is an operator-run verification, reported run-or-not-run, never a CI
gate.

Every guard carries a seeded counter-test proving the detection logic actually catches a
violation (the ``test_copy_discipline.py`` seeded-violation precedent)."""

from __future__ import annotations

import json
import pathlib
import re

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
_DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"
_API_CLIENT = _FRONTEND_ROOT / "lib" / "api.ts"
_JOURNEY_SCRIPTS = _REPO_ROOT / "runs" / "goal-session-desk" / "journey-scripts"

_MARKER_START = "// REFRESH-CHAIN-START"
_MARKER_END = "// REFRESH-CHAIN-END"

_DRIVER = "handleRefreshAll"
_BUTTON_TESTID = "desk-refresh-all-button"
_UNIVERSE_FETCH_PATH = "/research/desk/universe/fetch"

# The page's own effect/timer census. Each is asserted as an EXACT count rather than a bound,
# so a future edit that adds one has to come here and say why. Re-derived for the forward-test
# era: +1 as-of-keyed screen-pins GET (the J-21 pins read moved out of the mount effect so it
# follows the operator's resolved To day — still a GET, never a trigger), +1 forward-record GET
# keyed on the displayed snapshot (the screenCompareResult precedent), +1 forward-compute poll
# (the FOURTH compute manager, mirroring the existing trio's poll shape exactly) — 8 -> 11
# effects, 3 -> 4 intervals ("one per compute manager"), the single setTimeout stays the chain's
# own wait tick. The fifth chain step added NONE of the three: its `forwardComputeRef` mirror went
# into the EXISTING mirror effect, it starts no poll (the forward poll already existed) and it
# reuses the one wait tick. 11/4/1 standing unchanged across that change is part of the design.
#
# 11 -> 13 for the two reads that make an ABSENT forward record legible instead of ambiguous, both
# keyed on the displayed snapshot exactly as the forward-record read beside them is, and both plain
# GETs: +1 forward-coverage read (how many of this snapshot's ranked members hold a fine series
# covering its session — an upper bound on what a measurement could reach, disclosed before the
# click rather than discovered hours into a run) and +1 forward-run-ledger read (whether a
# measurement of this snapshot has ever finished, which is what distinguishes "never ran" from "ran
# and found nothing"). They are separate effects rather than branches of the record read because
# they answer different questions and matter MOST when that read returns null. Intervals and the
# timeout are untouched: the ledger's refresh piggybacks the EXISTING forward-compute poll's own
# terminal tick, and the chain still owns exactly one sleep.
#
# 13 -> 15 and 4 -> 5 for the deep fine-bar backfill, the FIFTH compute manager: +1 poll (mirroring
# the existing four polls' shape exactly -- registered only while a job the operator STARTED is
# running, and it calls no trigger) and +1 plan read keyed on the backfill's own From/To (a plain
# GET that issues no vendor call, reads no BarStore and starts nothing; it exists so the operator
# sees how many windows, and where each timeframe stops against the keyless vendor's own history,
# BEFORE committing to a sweep measured in hours). The timeout is untouched -- the chain still owns
# exactly one sleep. Neither new effect can reach a trigger, which is the property the scan below
# actually polices; the counts are here so that scan stays provably complete.
_EXPECTED_EFFECT_COUNT = 15
_EXPECTED_INTERVAL_COUNT = 5
_EXPECTED_TIMEOUT_COUNT = 1

# Everything that could start real work. The chain's own driver is included: an effect that calls
# it is exactly as forbidden as an effect that calls a trigger directly.
_TRIGGER_CALLS = (
    f"{_DRIVER}(",
    "handleTriggerUniverseFetch(",
    "handleTriggerTopup(",
    "handleTriggerReconcile(",
    "handleTriggerScreen(",
    "handleTriggerForward(",
    "triggerDeskUniverseFetch(",
    "triggerDeskTopupCompute(",
    "triggerDeskReconcileCompute(",
    "triggerDeskScreenCompute(",
    "triggerDeskForwardCompute(",
)

# Machinery that can invoke a handler without a user click. None of it is used by this page today;
# the guard freezes that.
_FORBIDDEN_AUTO_INVOCATION = (
    "requestIdleCallback",
    "requestAnimationFrame",
    "IntersectionObserver",
    ".click()",
    "autoFocus",
    "onFocus",
)

# The raw lib/api clients the driver must NOT call directly -- it goes through the three existing
# handlers so each control's own state bookkeeping stays the single owner of that state. The
# membership fetch is the one exception (it has no existing handler) and is asserted separately.
_FORBIDDEN_DRIVER_CALLS = (
    "triggerDeskTopupCompute(",
    "triggerDeskReconcileCompute(",
    "triggerDeskScreenCompute(",
    # Forward-test era, REVERSED by operator decision. This tuple previously banned BOTH the raw
    # client and `handleTriggerForward(` here, on the reasoning that "measuring a recorded screen
    # is its own operator act, never an implicit fifth step".
    #
    # What changed, and why: a forward result is only meaningful against a screen snapshot that
    # already exists, and the chain is the thing that creates them -- over a whole as-of range, at
    # that. Leaving the measurement out meant a 31-day refresh finished with 31 unmeasured
    # snapshots and 31 manual clicks still to do, each one requiring the operator to first select
    # that snapshot in the history list. The chain now measures every snapshot IT recorded, as a
    # serialized fifth step.
    #
    # What was given up, stated plainly: a Refresh Data click now starts N forward computes rather
    # than zero, and the click is roughly twice the wall-clock it was. That cost is serialized so
    # two walks never overlap, stoppable at any row boundary, and cheap on a re-click because the
    # backend's own 2-pin reuse short-circuits an already-measured input with zero bar reads. It
    # used to be bounded by a 31-day SCREEN_DAY_RANGE_MAX_DAYS cap on the range as well; that cap
    # is gone (one snapshot per date makes an already-covered day a tens-of-milliseconds reuse
    # rather than a full walk, so the ceiling was pricing work the chain no longer does), leaving
    # Stop as the operator's bound on a wide range.
    #
    # What did NOT change, and is still guarded here: the raw client stays banned, so the chain
    # drives the panel's own handler and that panel's state stays the single owner of the trigger
    # state -- exactly the invariant the three entries above encode. `handleTriggerForward(` also
    # stays in _TRIGGER_CALLS, so no useEffect may reach it: the era anti-goal holds unbroken, a
    # page load still computes nothing, and the fifth step runs only because someone clicked.
    "triggerDeskForwardCompute(",
)

_LINE_COMMENT = re.compile(r"//[^\n]*")
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_BARE_FETCH = re.compile(r"(?<![A-Za-z0-9_$])fetch\(")
_ELEMENT_REF = re.compile(r"(?<![A-Za-z])ref=\{")


def _strip_comments(source: str) -> str:
    """Comments out first -- a ``)`` inside prose would close a paren walk early, and a needle
    mentioned in a comment is not a call. Mirrors ``test_copy_discipline.py``'s own stripper."""
    return _LINE_COMMENT.sub("", _BLOCK_COMMENT.sub("", source))


def _effect_blocks(source: str) -> list[str]:
    """Every ``useEffect(``'s own argument text -- a paren-depth walk from the ``(`` that follows
    the identifier to its matching ``)``. Comments are stripped by the caller."""
    blocks: list[str] = []
    for match in re.finditer(r"\buseEffect\s*\(", source):
        depth = 0
        start = match.end() - 1
        for index in range(start, len(source)):
            char = source[index]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    blocks.append(source[start : index + 1])
                    break
    return blocks


def _extract_function(source: str, name: str) -> str:
    """The named function's own body -- a brace-depth walk from its declaration's first ``{``
    (the ``test_desk_hover_tooltip_guard.py`` precedent). The optional ``<...>`` accepts a GENERIC
    declaration (``function awaitRefreshChainJob<T extends ChainJobSnapshot>(``) -- without it the
    waiter's own guards would silently fail to find the function they guard."""
    match = re.search(rf"\bfunction\s+{re.escape(name)}\s*(?:<[^(]*?>)?\s*\(", source)
    assert match is not None, f"{name} is not declared in the source"
    opening = source.index("{", match.end())
    depth = 0
    for index in range(opening, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[opening : index + 1]
    raise AssertionError(f"{name}'s body never closes -- the brace walk ran off the end")


def _refresh_chain_block(source: str) -> str:
    start = source.index(_MARKER_START)
    end = source.index(_MARKER_END)
    assert start < end, f"{_MARKER_START} must precede {_MARKER_END}"
    return source[start:end]


def _effects_referencing_a_trigger(source: str) -> list[tuple[int, str]]:
    stripped = _strip_comments(source)
    return [
        (index, needle)
        for index, block in enumerate(_effect_blocks(stripped))
        for needle in _TRIGGER_CALLS
        if needle in block
    ]


# --- (a) no mount path ---------------------------------------------------------------------------


def test_no_effect_can_reach_the_refresh_chain_or_any_compute_trigger():
    """The era's critical anti-goal, mechanically: nothing that starts real work is reachable from
    a ``useEffect``. Covers the three already-shipped buttons as well as the chain."""
    hits = _effects_referencing_a_trigger(_DESK_PAGE.read_text())
    assert not hits, (
        f"a useEffect in apps/frontend/app/desk/page.tsx references {hits} -- every run on this "
        "page is an explicit operator act; a page load must never trigger a fetch or a compute"
    )


def test_the_effect_scan_is_not_vacuous():
    """A walk that silently returns nothing would make the guard above pass on any file. Assert it
    actually found the page's effects and that each extracted block looks like an argument list."""
    stripped = _strip_comments(_DESK_PAGE.read_text())
    blocks = _effect_blocks(stripped)
    assert len(blocks) == _EXPECTED_EFFECT_COUNT, (
        f"apps/frontend/app/desk/page.tsx has {len(blocks)} useEffect blocks, expected "
        f"{_EXPECTED_EFFECT_COUNT} -- if an effect was deliberately added or removed, re-derive "
        "this number here rather than loosening it, so the no-mount-trigger scan above stays "
        "provably complete"
    )
    for block in blocks:
        assert block.startswith("(") and block.endswith(")")
        assert "=>" in block


def test_the_no_mount_trigger_guard_can_fail_on_seeded_violations():
    """The lint CAN fail -- for all three shapes an auto-trigger would realistically take."""
    seeded = (
        "useEffect(() => { handleRefreshAll(); }, []);",
        "useEffect(() => { void handleTriggerTopup(); }, [topupCompute]);",
        "useEffect(() => { if (auto) { triggerDeskScreenCompute(todayUtcDate()); } }, []);",
    )
    for source in seeded:
        assert _effects_referencing_a_trigger(source), f"seeded violation not caught: {source}"


def test_the_page_ships_no_auto_invocation_machinery():
    """Nothing that can call a handler without a click. All zero today; frozen here."""
    stripped = _strip_comments(_DESK_PAGE.read_text())
    hits = [needle for needle in _FORBIDDEN_AUTO_INVOCATION if needle in stripped]
    assert not hits, (
        f"apps/frontend/app/desk/page.tsx contains {hits} -- each of these can invoke a handler "
        "without an operator click, which would defeat the explicit-operator-act rule"
    )


# --- (b) the entry point is click-only -----------------------------------------------------------


def test_the_refresh_entry_point_is_reachable_only_from_the_button():
    """``handleRefreshAll`` appears exactly twice: its declaration, and the one props binding."""
    stripped = _strip_comments(_DESK_PAGE.read_text())
    occurrences = list(re.finditer(rf"\b{_DRIVER}\b", stripped))
    assert len(occurrences) == 2, (
        f"{_DRIVER} appears {len(occurrences)} times in apps/frontend/app/desk/page.tsx, expected "
        "exactly 2 (its declaration and the single props binding) -- any third reference is a "
        "second way to start the chain and must be justified here"
    )
    contexts = [stripped[max(0, m.start() - 60) : m.end() + 20] for m in occurrences]
    assert any(re.search(rf"async function {_DRIVER}\s*\(", c) for c in contexts), (
        f"{_DRIVER} is never declared as an async function -- the extraction below would be vacuous"
    )
    assert any(re.search(rf"onRefreshAll:\s*{_DRIVER}\b", c) for c in contexts), (
        f"{_DRIVER} is not bound to the control's onRefreshAll prop -- the button would be inert"
    )


def test_the_refresh_button_is_a_plain_click_target():
    """The button element itself carries onClick and nothing that could self-invoke."""
    source = _DESK_PAGE.read_text()
    anchor = source.index(f'data-testid="{_BUTTON_TESTID}"')
    opening = source.rindex("<button", 0, anchor)
    element = source[opening : source.index(">", anchor) + 1]
    assert "onClick={onRefreshAll}" in element, (
        f"the {_BUTTON_TESTID} element does not bind onClick={{onRefreshAll}}"
    )
    assert 'type="button"' in element, (
        f"the {_BUTTON_TESTID} element is not type=\"button\" -- a default submit could fire it "
        "without a deliberate click"
    )
    assert "autoFocus" not in element
    assert _ELEMENT_REF.search(element) is None, (
        f"the {_BUTTON_TESTID} element takes a ref -- a ref callback can invoke a handler without "
        "a click"
    )


def test_the_click_target_guard_can_fail_on_seeded_violations():
    """The lint CAN fail: a non-click binding and a ref-carrying button are both caught."""
    seeded_onload = f'<button data-testid="{_BUTTON_TESTID}" onLoad={{handleRefreshAll}}>'
    assert "onClick={onRefreshAll}" not in seeded_onload
    seeded_ref = f'<button data-testid="{_BUTTON_TESTID}" ref={{node}} type="button">'
    assert _ELEMENT_REF.search(seeded_ref) is not None
    # `href={` must NOT trip the ref pattern -- this page uses it on its drill-in links.
    assert _ELEMENT_REF.search('<Link href={`/structure?symbol=X`}>') is None


# --- (c) no second trigger path, no fourth poll ---------------------------------------------------


def test_the_refresh_chain_block_markers_exist():
    """Without the markers, every block-scoped assertion below would be vacuous."""
    source = _DESK_PAGE.read_text()
    assert _MARKER_START in source
    assert _MARKER_END in source
    assert f'data-testid="{_BUTTON_TESTID}"' in source


def test_the_chain_drives_the_existing_handlers_not_a_second_path():
    """The driver reuses the four shipped trigger handlers -- it never calls the raw lib/api
    clients and never opens a bare fetch of its own."""
    body = _extract_function(_strip_comments(_DESK_PAGE.read_text()), _DRIVER)
    hits = [needle for needle in _FORBIDDEN_DRIVER_CALLS if needle in body]
    assert not hits, (
        f"{_DRIVER} calls {hits} directly -- it must go through the existing handleTrigger* "
        "handlers so each control's own state stays the single owner of that state"
    )
    assert _BARE_FETCH.search(body) is None, (
        f"{_DRIVER} opens a bare fetch() -- every network call on this page goes through lib/api"
    )


def test_the_chain_adds_no_extra_poll_and_one_sleep():
    """The chain waits on the state the per-manager poll effects already maintain, so the page
    has exactly one interval per compute manager (four, forward-test era) and the chain itself
    owns none; its only timer is the single wait-tick sleep."""
    stripped = _strip_comments(_DESK_PAGE.read_text())
    intervals = stripped.count("setInterval(")
    timeouts = stripped.count("setTimeout(")
    assert intervals == _EXPECTED_INTERVAL_COUNT, (
        f"apps/frontend/app/desk/page.tsx has {intervals} setInterval calls, expected "
        f"{_EXPECTED_INTERVAL_COUNT} (one per compute manager: screen, top-up, reconcile, "
        "forward) -- the refresh chain must not poll the backend itself; it observes the state "
        "those effects already keep current"
    )
    assert timeouts == _EXPECTED_TIMEOUT_COUNT, (
        f"apps/frontend/app/desk/page.tsx has {timeouts} setTimeout calls, expected "
        f"{_EXPECTED_TIMEOUT_COUNT} (the chain's wait tick, which issues no requests)"
    )
    assert "setTimeout(" in _extract_function(stripped, "refreshChainSleep")


def test_the_universe_fetch_path_literal_lives_only_in_the_api_client():
    """Path literals live in lib/api.ts. The page names the function, never the URL."""
    assert _UNIVERSE_FETCH_PATH not in _DESK_PAGE.read_text(), (
        "apps/frontend/app/desk/page.tsx hardcodes the universe-fetch path -- every endpoint "
        "literal belongs in lib/api.ts"
    )
    # Comments stripped first: the client's own header comment names the endpoint as prose, which
    # is documentation, not a second owner of the literal.
    assert _strip_comments(_API_CLIENT.read_text()).count(_UNIVERSE_FETCH_PATH) == 1, (
        "the universe-fetch path literal must appear exactly once in lib/api.ts -- one owner"
    )


# --- (d) honest step semantics --------------------------------------------------------------------


def test_the_chain_runs_the_five_steps_in_order():
    """Membership, then top-up, then index, then screen, then the forward returns -- each named
    exactly once, in that order. The screen runs after the bars and the index because its bar-store
    pin is resolved before its walk and would otherwise pin stale bars; the forward measurement
    follows the screen because it measures a snapshot that has to exist first.

    The last two are INTERLEAVED per day rather than run as two passes (see
    ``test_the_forward_measurement_runs_inside_the_day_loop`` below), which this ordering assertion
    is deliberately compatible with: the forward trigger still appears exactly once, and still
    after the screen trigger, because it sits directly beneath it inside the one loop."""
    body = _extract_function(_strip_comments(_DESK_PAGE.read_text()), _DRIVER)
    expected = (
        "triggerDeskUniverseFetch(",
        "handleTriggerTopup",
        "handleTriggerReconcile",
        "handleTriggerScreen",
        "handleTriggerForward",
    )
    positions = []
    for needle in expected:
        assert body.count(needle) == 1, (
            f"{_DRIVER} references {needle!r} {body.count(needle)} times, expected exactly once"
        )
        positions.append(body.index(needle))
    assert positions == sorted(positions), (
        f"{_DRIVER} runs its steps out of order -- found at offsets {positions}; the screen must "
        "run after the bars and the index it pins, and the forward step after the screens it "
        "measures"
    )


def test_the_forward_step_measures_the_ids_this_run_recorded():
    """Step 5 measures the snapshots THIS run recorded -- never whichever snapshot the history
    panel happens to be displaying, which has nothing to do with the range that was just clicked.
    The no-argument form of the handler is the panel button's, and reaching for it here would
    silently measure the wrong thing."""
    body = _extract_function(_strip_comments(_DESK_PAGE.read_text()), _DRIVER)
    assert re.search(r"handleTriggerForward\(\s*\w+\s*\)", body) is not None, (
        f"{_DRIVER} calls handleTriggerForward with no explicit snapshot id -- the no-argument "
        "form measures the DISPLAYED snapshot, which is not what this run recorded"
    )
    assert "displayedSnapshot" not in body, (
        f"{_DRIVER} reads displayedSnapshot -- the fifth step must measure the ids the screen step "
        "itself collected, never the panel's current selection"
    )
    assert "await handleTriggerForward(" in body, (
        f"{_DRIVER} does not await the forward trigger -- the manager is single-flight, so an "
        "un-awaited second trigger would adopt the first job instead of measuring its own snapshot"
    )


def test_the_forward_step_guard_can_fail_on_seeded_violations():
    seeded_no_arg = "const started = await handleTriggerForward();"
    assert re.search(r"handleTriggerForward\(\s*\w+\s*\)", seeded_no_arg) is None
    seeded_displayed = "const started = await handleTriggerForward(displayedSnapshot.id);"
    assert "displayedSnapshot" in seeded_displayed


def _day_loop_body(driver_body: str) -> str:
    """The per-day loop's own body -- a brace walk from ``for (let dayIndex`` (the
    ``_extract_function`` technique, applied to a loop)."""
    match = re.search(r"for\s*\(\s*let\s+dayIndex\b", driver_body)
    assert match is not None, "the driver has no per-day loop"
    opening = driver_body.index("{", match.end())
    depth = 0
    for index in range(opening, len(driver_body)):
        char = driver_body[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return driver_body[opening : index + 1]
    raise AssertionError("the day loop's body never closes -- the brace walk ran off the end")


def test_the_forward_measurement_runs_inside_the_day_loop():
    """A DURABILITY property, not a style choice. These ran as two passes -- every screen, then
    every measurement -- so the second pass began only once the first had finished. On 2026-08-06 a
    51-day range spent 2h42m recording screens and produced ZERO forward records: the chain lives
    entirely in the tab, is never resumed after a reload, and whatever ended it in that window took
    all 51 measurements with it, leaving nothing on disk and no trace they had been due.

    Measuring each day beside its own screen is what makes an interrupted range keep every day it
    actually finished. If the forward trigger ever moves back out of this loop, that guarantee is
    silently gone while every other assertion in this file still passes."""
    body = _extract_function(_strip_comments(_DESK_PAGE.read_text()), _DRIVER)
    loop = _day_loop_body(body)
    assert "handleTriggerScreen" in loop, (
        "the per-day loop no longer runs the screen -- this guard is anchored to the wrong loop"
    )
    assert "handleTriggerForward" in loop, (
        f"{_DRIVER} triggers the forward measurement OUTSIDE its per-day loop -- an interrupted "
        "range then loses every measurement it had not reached, which is exactly the 2026-08-06 "
        "loss this interleaving exists to prevent"
    )


def test_the_session_filter_runs_once_before_the_loop_and_never_per_day():
    """The chain enumerated raw CALENDAR days, so a range screened weekends, US market holidays and
    dates that had not happened yet exactly like real sessions -- ~280 of the 939 snapshots on disk
    on 2026-08-08, every one of them carrying an all-absent forward record. The filter that fixes
    that must resolve ONCE, before the loop: a per-day call would put a network round-trip in front
    of every day of a 51-day range."""
    body = _extract_function(_strip_comments(_DESK_PAGE.read_text()), _DRIVER)
    assert body.count("handleLoadSessionDays(") == 1, (
        f"{_DRIVER} resolves the recorded sessions {body.count('handleLoadSessionDays(')} times -- "
        "it must be exactly one awaited read before the per-day loop"
    )
    assert "handleLoadSessionDays" not in _day_loop_body(body), (
        f"{_DRIVER} resolves the recorded sessions INSIDE its per-day loop -- one round-trip per "
        "day of the range, for an answer that does not change while the chain runs"
    )
    assert "runDays[dayIndex]" in _day_loop_body(body), (
        "the per-day loop still reads the unfiltered calendar days -- the filter's output is not "
        "what gets screened"
    )


def test_the_session_filter_fails_open_on_every_unproven_answer():
    """The rail that keeps this from screening LESS than it used to on evidence it does not have: a
    failed call, an unreachable backend and a store with no daily bars must each return the
    caller's own day list unchanged."""
    body = _extract_function(_strip_comments(_DESK_PAGE.read_text()), "handleLoadSessionDays")
    assert "if (!result.ok || result.data === null) return { days, skipped: 0 };" in body, (
        "handleLoadSessionDays no longer returns the caller's own days when the read fails"
    )
    assert "result.data.evidence.anchor_symbols.length === 0" in body, (
        "handleLoadSessionDays no longer fails open when no member holds a daily series -- an "
        "empty session set would then read as 'nothing traded' and screen nothing at all"
    )
    # Intersecting with `sessions` is load-bearing: subtracting `non_sessions` would keep every
    # future date, which is exactly what put two future-dated snapshots on disk.
    assert "sessions.has(day)" in body, (
        "handleLoadSessionDays no longer intersects with the recorded sessions -- subtracting the "
        "proven non-sessions alone keeps every date past the last recorded daily bar"
    )
    assert "non_sessions" not in body


def test_the_day_loop_guard_can_fail_on_a_seeded_violation():
    seeded = (
        "for (let dayIndex = 0; dayIndex < n; dayIndex += 1) { await handleTriggerScreen(day); }\n"
        "for (const id of ids) { await handleTriggerForward(id); }"
    )
    assert "handleTriggerForward" not in _day_loop_body(seeded)


def test_the_job_waiter_is_bounded_and_the_driver_names_a_lost_job():
    """The waiter looped unbounded while ``read()`` returned null -- and null is exactly what a
    backend restart produces (the manager's snapshot is process-scoped, so the poll sets state to
    null and then stops polling). The step sat on one frozen line forever, with no error and no
    timeout. A job that can no longer be observed is a failed step, and the chain must say so."""
    stripped = _strip_comments(_DESK_PAGE.read_text())
    waiter = _extract_function(stripped, "awaitRefreshChainJob")
    assert "REFRESH_CHAIN_LOST_JOB_TICKS" in waiter, (
        "awaitRefreshChainJob has no tick budget -- a job the backend forgot would hang the step "
        "forever with no error"
    )
    assert '"lost"' in waiter, "awaitRefreshChainJob never reports a lost job as its own outcome"

    body = _extract_function(stripped, _DRIVER)
    assert '"lost"' in body, (
        f"{_DRIVER} never handles a lost job -- the waiter's third outcome must halt the step "
        "explicitly, never fall through as if it had settled"
    )


def test_the_lost_job_budget_is_counted_in_ticks_not_wall_clock():
    """A backgrounded tab has its timers throttled to >=1s, so a wall-clock deadline would fail a
    perfectly healthy run whose operator switched away. The budget counts ticks for that reason."""
    stripped = _strip_comments(_DESK_PAGE.read_text())
    waiter = _extract_function(stripped, "awaitRefreshChainJob")
    assert "Date.now()" not in waiter and "performance.now()" not in waiter, (
        "awaitRefreshChainJob reads a wall clock -- a throttled background tab would then be "
        "reported as a lost job"
    )


def test_the_chain_never_renders_a_slash_progress_readout():
    """A hazard the needle scan below provably cannot catch: `_rendered_literals` strips `${...}`
    before comparing, so a template like `${done} / ${total} rows` reduces to " /  rows" and
    passes -- while RENDERING `101 / 101`, a string J-18 pins against the screen-runs table. This
    control renders above that table, so the replay engine's first-in-DOM match would resolve
    here. The chain writes progress as "N of M"."""
    hits = [literal for literal in _rendered_literals(_DESK_PAGE.read_text()) if " / " in literal]
    assert not hits, (
        f"refresh-chain copy renders a slash progress readout {hits} -- write it as 'N of M'; a "
        "rendered '101 / 101' would intercept J-18's golden match page-wide"
    )


def test_the_chain_advances_on_done_and_halts_on_failed_or_cancelled():
    """The three terminal states the compute managers actually publish, all handled by name."""
    body = _extract_function(_strip_comments(_DESK_PAGE.read_text()), _DRIVER)
    for literal in ('"done"', '"failed"', '"cancelled"'):
        assert literal in body, (
            f"{_DRIVER} never mentions {literal} -- each terminal state a compute manager can "
            "publish must be handled explicitly, not folded into a catch-all"
        )


def test_an_already_running_job_is_adopted_never_treated_as_an_error():
    """``started: false`` means the manager handed back the job already running. Halting on it
    would turn single-flight -- the property that makes this chain safe -- into a failure."""
    body = _extract_function(_strip_comments(_DESK_PAGE.read_text()), _DRIVER)
    assert re.search(r"!\s*\w+(\.\w+)*\.started\b", body) is None, (
        f"{_DRIVER} halts on a falsy `started` -- a job already running must be ADOPTED and "
        "waited on, never reported as a failure"
    )
    assert "adopted" in body, (
        f"{_DRIVER} never names the adopted case -- an operator must be told when the chain "
        "joined a job that was already running rather than starting one"
    )


def test_the_adoption_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing."""
    seeded = 'if (!result.data.started) { halt(index, "failed", "already running"); return false; }'
    assert re.search(r"!\s*\w+(\.\w+)*\.started\b", seeded) is not None


def test_the_membership_409_is_a_normal_outcome_not_a_failure():
    """A 409 means the content is identical to a snapshot already registered -- nothing to write.
    The chain must continue to the remaining three steps."""
    body = _extract_function(_strip_comments(_DESK_PAGE.read_text()), _DRIVER)
    assert "409" in body, (
        f"{_DRIVER} never distinguishes a 409 -- an unchanged membership would be reported as a "
        "failed step and would stop the bars, the index and the screen from refreshing at all"
    )
    assert '"noop"' in body, (
        f"{_DRIVER} has no distinct no-op outcome -- calling an unchanged membership 'done' would "
        "imply a registration that never happened"
    )


# --- golden-replay text interception --------------------------------------------------------------


def _golden_pinned_texts() -> set[str]:
    """Every literal a shipped desk journey's replay script matches on. The replay engine resolves
    these page-globally with a first-in-DOM-order substring match, so a new visible string that
    contains one of them can silently become the match -- the golden then goes green while proving
    nothing about the section it was written for."""
    texts: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("text", "name") and isinstance(value, str):
                    texts.add(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    for path in sorted(_JOURNEY_SCRIPTS.glob("*.json")):
        walk(json.loads(path.read_text()).get("steps", []))
    return texts


_INTERPOLATION = re.compile(r"\$\{[^}]*\}")
_STRING_LITERAL = re.compile(r'"([^"\n]*)"')
_TEMPLATE_LITERAL = re.compile(r"`([^`]*)`")
# Structural literals -- Tailwind class lists and testids. Every token carries a `-`/`:`/`[`, which
# no rendered English copy on this page does.
_STRUCTURAL_LITERAL = re.compile(r"^[\w\-\[\]/:.%\s]+$")


def _rendered_literals(source: str) -> list[str]:
    block = _refresh_chain_block(source)
    body = _extract_function(_strip_comments(source), _DRIVER)
    literals: list[str] = []
    for chunk in (_strip_comments(block), body):
        for match in _STRING_LITERAL.finditer(chunk):
            literals.append(match.group(1))
        for match in _TEMPLATE_LITERAL.finditer(chunk):
            literals.append(_INTERPOLATION.sub("", match.group(1)))
    return [
        literal
        for literal in literals
        if literal.strip()
        and not (
            _STRUCTURAL_LITERAL.match(literal)
            and all("-" in token or ":" in token or "[" in token for token in literal.split())
        )
    ]


def test_the_refresh_chain_copy_cannot_intercept_a_golden_replay_match():
    """No string the chain renders contains a literal a shipped golden matches on. Parsed from the
    scripts at test time, so a new pinned string is picked up without editing this file."""
    pinned = _golden_pinned_texts()
    collisions = [
        (literal, needle)
        for literal in _rendered_literals(_DESK_PAGE.read_text())
        for needle in pinned
        if needle.lower() in literal.lower()
    ]
    assert not collisions, (
        f"refresh-chain copy collides with a golden's pinned text: {collisions} -- the replay "
        "engine takes the FIRST in-DOM-order substring match page-wide, and this control renders "
        "above the ledger sections, so the golden would resolve here and stop proving anything"
    )


def test_the_interception_guard_is_not_vacuous_and_can_fail():
    """It found real pinned texts and real rendered literals, and it catches a seeded collision."""
    pinned = _golden_pinned_texts()
    assert len(pinned) > 20, f"only {len(pinned)} pinned golden texts parsed -- the scan is broken"
    assert "Top-up Runs" in pinned and "coverage" in pinned
    literals = _rendered_literals(_DESK_PAGE.read_text())
    assert len(literals) > 10, f"only {len(literals)} rendered literals found -- the scan is broken"
    seeded = "Index Reconciliation finished"
    assert any(needle.lower() in seeded.lower() for needle in pinned)
