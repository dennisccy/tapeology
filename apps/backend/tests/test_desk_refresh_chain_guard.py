"""Source-introspection guards for the ``/desk`` chained refresh control -- the
``test_desk_ui_guards.py`` pattern (read the frontend .tsx as TEXT, assert on structure; no
browser, no runtime).

The control runs four refresh acts in order -- the universe membership fetch, the bar top-up, the
bar index reconciliation, then the screen for today -- by driving the SAME four endpoints the
page's existing controls already drive. These guards pin the four properties that make that safe:

  (a) **No mount path.** No ``useEffect`` argument list anywhere in the page references the chain
      driver or any compute trigger. This is the era's own critical anti-goal ("Every run is an
      explicit operator act ... page-load GETs never trigger fetches or computes") and it now
      covers the three already-shipped buttons too, not only the new one.
  (b) **The entry point is click-only.** ``handleRefreshAll`` appears in exactly two syntactic
      shapes -- its own declaration, and the single props binding -- and the button carries a
      plain ``onClick`` with no focus/ref auto-invocation.
  (c) **No second trigger path.** The driver calls the three EXISTING ``handleTrigger*`` handlers,
      never the raw ``lib/api`` clients and never a bare ``fetch(`` -- the
      ``test_structure_prefill_reuses_the_existing_load_function`` precedent applied to this
      block. It also owns no poll of its own: the page has exactly one ``setInterval(`` per
      compute manager (four, forward-test era), because the chain WAITS on the state the existing
      poll effects already maintain.
  (d) **Honest step semantics.** The four steps appear once each, in order; the chain advances on
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
durable run ledger keeps its length. That is an operator-run verification, reported run-or-not-run,
never a CI gate.

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
# own wait tick.
_EXPECTED_EFFECT_COUNT = 11
_EXPECTED_INTERVAL_COUNT = 4
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
    # Forward-test era: the chain must NOT start the forward compute — measuring a recorded
    # screen is its own operator act, never an implicit fifth step. BOTH the raw client and the
    # handler are banned here (unlike the three entries above, whose handlers the chain
    # legitimately calls).
    "triggerDeskForwardCompute(",
    "handleTriggerForward(",
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
    (the ``test_desk_hover_tooltip_guard.py`` precedent)."""
    match = re.search(rf"\bfunction\s+{re.escape(name)}\s*\(", source)
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
    """The driver reuses the three shipped trigger handlers -- it never calls the raw lib/api
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


def test_the_chain_runs_the_four_steps_in_order():
    """Membership, then top-up, then index, then screen -- once each, in that order, because a
    screen's bar-store pin is resolved before its walk and would otherwise pin stale bars."""
    body = _extract_function(_strip_comments(_DESK_PAGE.read_text()), _DRIVER)
    expected = (
        "triggerDeskUniverseFetch(",
        "handleTriggerTopup",
        "handleTriggerReconcile",
        "handleTriggerScreen",
    )
    positions = []
    for needle in expected:
        assert body.count(needle) == 1, (
            f"{_DRIVER} references {needle!r} {body.count(needle)} times, expected exactly once"
        )
        positions.append(body.index(needle))
    assert positions == sorted(positions), (
        f"{_DRIVER} runs its steps out of order -- found at offsets {positions}; the screen must "
        "run last, after the bars and the index it pins"
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
