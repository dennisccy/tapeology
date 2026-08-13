"""Forward-test era: source-introspection guards for the ``/desk`` Forward Returns panel -- the
``test_desk_screen_compare_ui_guard.py`` pattern (read the .tsx as TEXT, assert on structure).

Four properties, each the cheapest static proof available:
  (a) the panel's own block exists and ships its primary testids;
  (b) the whole page renders its sections in the registered order -- the panel now renders THIRD,
      directly above the ranked briefing, NOT dead last as it originally did; the bottom-placement
      interception safety that move gave up is paid for by the bare-symbol golden guard below;
  (c) the block never sorts/reverses/slices what it renders (all rows, served order, uncapped);
  (d) the block never reuses a golden click-target attribute (the compare-guard's own tuple).

Like every guard in this family, these prove source structure, never runtime behaviour; each
carries a seeded counter-test."""

from __future__ import annotations

import json
import pathlib
import re

_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
_DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"

_BLOCK_START = "// --- Forward returns (forward-test era"
_BLOCK_END = "// --- Screen comparison (goal-desk-iter-35, J-20)"

# Matched as `testid="<id>"`, which covers BOTH the literal `data-testid="<id>"` attribute and the
# `testid=` prop a shared renderer takes (the per-touch table is one component serving both the
# touches and the baseline anchors, so its own testid necessarily arrives as a prop).
_REQUIRED_FORWARD_TESTIDS = (
    "desk-forward-section",
    "desk-forward-table",
    "desk-forward-compute-button",
    "desk-forward-register",
    "desk-forward-not-computed",
    # v2 touch-anchored surfaces: the per-row drill-in panel, its per-touch table and rows, and the
    # collapsed baseline-anchors disclosure -- static presence is their only automated proof
    # (no golden ever clicks a forward row; the panel is a read of an already-loaded record).
    "desk-forward-detail",
    "desk-forward-detail-touch",
    "desk-forward-detail-table",
    "desk-forward-detail-baseline",
    "desk-forward-detail-baseline-table",
    "desk-forward-summary-baseline",
    # The side-relative sign convention's own line: how to READ every directional number in the
    # panel. Its presence is the static proof that the reading rule ships beside the numbers.
    "desk-forward-sign-convention",
    # The two surfaces that make an ABSENT forward record legible rather than ambiguous, and which
    # therefore have to ship BESIDE `desk-forward-not-computed` rather than instead of it: how much
    # of this snapshot a measurement could reach at all (an upper bound, disclosed before the click
    # -- learning it by running the measurement cost 2h42m on 2026-08-06), and whether one has ever
    # finished. `desk-forward-runs-empty` is the load-bearing half of the second: a snapshot with no
    # record AND no attempt was never measured, where one with a `done` attempt and no record was
    # measured and found nothing.
    "desk-forward-coverage",
    "desk-forward-runs",
    "desk-forward-runs-empty",
    "desk-forward-runs-table",
    # The third such surface, and the one an all-absent record needs most: a record where NOT ONE
    # row carries a measurement renders the full section (real id, real members, every numeric cell
    # an em-dash), never the amber `desk-forward-not-computed` panel -- so without this line the
    # only account of why was a per-row `title` tooltip. Static presence is its automated proof.
    "desk-forward-all-absent",
)

# The golden click-target attributes the compare guard already forbids its own block from reusing
# -- the same tuple, applied to the forward block.
_FORBIDDEN_TESTID_ATTRS = (
    'data-testid="desk-history-row"',
    'data-testid="desk-screen-row"',
)
_FORBIDDEN_DATA_SCREEN_ID_ATTR = "data-screen-id="
_FORBIDDEN_ROW_TESTID_ATTR_RE = re.compile(r'data-testid="desk-row-[a-z-]+"')

_REORDER_RE = re.compile(r"\.\s*(?:sort|reverse|slice)\s*\(")

# Any arithmetic operator at all, for scanning a function whose ONLY job is to re-key already-served
# values. Deliberately blunter than the desk-wide field-bound guard: inside `forwardCloseMeasure`
# there is no legitimate arithmetic of any kind, so a name-bound pattern would be needlessly narrow.
_ARITHMETIC_RE = re.compile(r"[a-zA-Z_.\]]\s*[-+*/]\s*[a-zA-Z_.(\d]")

# The page's registered section order, keyed on each `<section>`'s own `aria-label`. These beat
# component-name needles on three counts: every one of the ten is unique in the file (a component
# name is not -- `<DeskRefreshChainControl` occurs twice, since DeskNotComputedPanel renders the
# same four controls, and `<DeskProvenance` also prefix-matches `<DeskProvenancePins`), they name
# the actual DOM landmarks rather than the components that happen to fill them, and they are what
# a screen reader announces -- so the order pinned here is the order a page reader experiences.
_SECTION_ORDER = (
    'aria-label="Screen history"',
    # Forward Returns moved ABOVE the controls: the measurement describes whichever snapshot the
    # calendar above just selected, so it reads directly beneath it -- what happened next, then the
    # controls that act.
    'aria-label="Forward Returns"',
    # Renamed, not reordered: the controls section gained a fourth control (the deep fine-bar
    # backfill), and a landmark a screen reader announces must name what it actually contains.
    'aria-label="Run Screen, Top-up, Reconcile Index and Deep Backfill controls"',
    'aria-label="Briefing"',
    'aria-label="Skipped members"',
    'aria-label="Top-up runs"',
    'aria-label="Index Reconciliation"',
    'aria-label="Screen Runs"',
    'aria-label="Screen Comparison"',
    'aria-label="Provenance"',
)

# A bare ticker: what a golden must NOT pin as page-wide text now that an uncapped symbol table
# renders above the briefing and the briefing itself renders one page at a time.
_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,5}$")

_JOURNEY_SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[3] / "runs" / "goal-session-desk" / "journey-scripts"
)


def _golden_assertion_texts() -> list[tuple[str, object, str]]:
    """Every literal text a shipped golden ASSERTS -- an `expect` clause's text, or an `expect`
    ACTION's own text. A `fill` action's text is input, never an assertion, so it is excluded."""
    found: list[tuple[str, object, str]] = []
    for path in sorted(_JOURNEY_SCRIPTS_DIR.glob("J-*.json")):
        for step in json.loads(path.read_text()).get("steps", []):
            action = step.get("action") or {}
            expect = step.get("expect") or {}
            if isinstance(expect.get("text"), str):
                found.append((path.name, step.get("n"), expect["text"]))
            if action.get("type") == "expect" and isinstance(action.get("text"), str):
                found.append((path.name, step.get("n"), action["text"]))
    return found


def _forward_block(source: str) -> str:
    start = source.index(_BLOCK_START)
    end = source.index(_BLOCK_END)
    assert start < end, "the forward block must precede the screen-comparison block in source"
    return source[start:end]


def _extract_function(source: str, name: str) -> str:
    """The named function's full body by brace-walk (this suite's convention -- each guard module
    owns its own copy rather than sharing one; see `test_desk_ui_guards.py`'s twin).

    The parameter list is walked FIRST and skipped: a component destructures its props, so the
    first `{` after the name opens the DESTRUCTURING PATTERN, not the body -- walking from there
    would return a props pattern and every assertion over it would pass on an empty haystack."""
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
    """A counter-test for the helper: if the walk stops at the destructuring pattern, every `in`
    assertion over the result silently passes on an empty haystack."""
    seeded = "function Widget({ touch }: Props) {\n  return touch.entry_price + 1;\n}\n"
    body = _extract_function(seeded, "Widget")
    assert "touch.entry_price + 1" in body, "the extractor stopped at the props pattern"
    assert body.endswith("}")


def test_the_forward_block_exists_and_ships_its_testids():
    source = _DESK_PAGE.read_text()
    block = _forward_block(source)
    missing = [t for t in _REQUIRED_FORWARD_TESTIDS if f'testid="{t}"' not in block]
    assert not missing, (
        f"the Forward Returns block is missing testid(s) {missing} -- its primary surfaces must "
        "stay statically present (no golden ever clicks a write path, so presence is the proof)"
    )


def test_the_page_renders_its_sections_in_the_registered_order():
    """The Forward Returns section no longer renders dead last -- it renders THIRD, directly above
    the ranked briefing table, and the provenance line moved to the bottom.

    DOM order is source order on this page, and that is a MAINTAINED invariant rather than a
    coincidence: every `<section>` below is a JSX child of exactly one of two function bodies
    (`DeskPopulatedScreen` for sections 1-5, `DeskPage` for 6-10), JSX children render in source
    order within one return, and `DeskPopulatedScreen`'s own call site precedes `DeskPage`'s
    remaining sections. The assertion below the loop pins that second half."""
    source = _DESK_PAGE.read_text()
    for needle in _SECTION_ORDER:
        assert source.count(needle) == 1, (
            f"{needle!r} occurs {source.count(needle)} times -- a source-index order check over a "
            "non-unique needle is a lie; every section landmark must be named exactly once"
        )
    # The invariant the whole comparison rests on: everything DeskPopulatedScreen renders comes
    # before everything DeskPage renders after it.
    assert source.index("<DeskPopulatedScreen") < source.index('aria-label="Top-up runs"'), (
        "DeskPopulatedScreen no longer renders before the always-on ledger sections -- the "
        "source-order == DOM-order invariant this guard depends on is gone"
    )
    positions = [source.index(needle) for needle in _SECTION_ORDER]
    assert positions == sorted(positions), (
        "the /desk sections are not in the registered order; source order is "
        f"{[name for _, name in sorted(zip(positions, _SECTION_ORDER))]}"
    )


def test_no_shipped_golden_pins_a_bare_symbol_as_page_wide_text():
    """The guard that PAYS for the bottom placement given up above.

    Forward Returns used to render dead last precisely so no golden's first-visible-match could
    resolve into it. It now renders above the briefing, and it renders a `member` column over
    every ranked symbol, uncapped. At the same time the briefing renders one 10-row page at a
    time. So a golden step that pins a bare ticker as PAGE-WIDE text has two independent ways to
    become a false green: it can match the forward table instead of the briefing, and the row it
    meant to prove may not be in the DOM at all. Such a pin must be scoped to a target."""
    texts = _golden_assertion_texts()
    assert texts, "the golden scan is vacuous -- no journey scripts were read"
    offenders = [(name, step, text) for name, step, text in texts if _TICKER_RE.match(text)]
    assert not offenders, (
        f"golden step(s) {offenders} pin a bare symbol as page-wide text -- scope the assertion to "
        'the briefing, e.g. a css target of [data-testid="desk-screen-rows-table"] '
        'td[data-testid="desk-row-symbol"]'
    )


def test_the_order_and_bare_symbol_guards_can_fail_on_seeded_violations():
    seeded_order = '<section aria-label="Briefing" />\n<section aria-label="Forward Returns" />'
    positions = [
        seeded_order.index('aria-label="Forward Returns"'),
        seeded_order.index('aria-label="Briefing"'),
    ]
    assert positions != sorted(positions)
    assert _TICKER_RE.match("BRK-B") is not None
    assert _TICKER_RE.match("AAPL") is not None
    for clean in (
        "Desk",
        "Class A",
        "d before as-of",
        "101 / 101",
        "08e471b10130e1e2",
        "Universe snapshot",
        "298.02–300.1001",
    ):
        assert _TICKER_RE.match(clean) is None


def test_the_forward_block_never_reorders_or_caps_what_it_renders():
    source = _DESK_PAGE.read_text()
    block = _forward_block(source)
    hits = _REORDER_RE.findall(block)
    assert not hits, (
        f"the Forward Returns block sorts/reverses/slices its rendered data ({hits}) -- every row "
        "renders in served order, uncapped; the scroll container is the size rail, never a slice"
    )


# The Forward Returns block's four tables, each of which must reach any non-served display order
# through the ONE shared hook rather than a comparator of its own.
_FORWARD_BLOCK_TABLES = (
    "ForwardRunsNote",
    "ForwardTouchTable",
    "DeskForwardSummaryView",
    "DeskForwardTable",
)


def test_the_forward_block_deliberately_permits_an_operator_chosen_sort():
    """A deliberate, PAID-FOR narrowing, recorded rather than hidden.

    The guard above bans the call syntax; its PROPERTY was that the block never chooses an order or
    a cap on the operator's behalf. All four of the block's tables are now sortable by clicking a
    column header, which leaves that property intact -- a header the operator clicks is the operator
    choosing.

    The dishonest way to permit this was available and is refused: `useTableSort(...)` contains no
    `.sort(`, so `_REORDER_RE` would have gone on finding nothing while ordering shipped underneath
    it. The permission is written down here instead.

    What is given up: these four tables can display rows in an order the record did not serve. What
    pays for it:

      (a) Every one of them reorders ONLY through the shared hook -- no comparator lives in this
          block, which is what the ban above still enforces.
      (b) Every one of them ships the disclosure note, so a non-served order always says so.
      (c) UNCAPPED SURVIVES UNCHANGED: the block still contains no `.slice(`, and each table maps
          `sort.entries`, whose length the hook's own guard pins equal to its input
          (test_table_sort_guards.py::test_the_hook_is_a_total_mapping_of_its_input). The scroll
          container is still the size rail, never a slice.

    NOTE for future edits to this block: `_forward_block` does NOT strip comments, so a comment
    between the block markers that quotes `.sort(`, `.slice(` or `.reverse(` call syntax will trip
    the guard above. Write "sorted" or "a slice", never the call form."""
    source = _DESK_PAGE.read_text()
    block = _forward_block(source)

    for name in _FORWARD_BLOCK_TABLES:
        body = _extract_function(source, name)
        assert "useTableSort(" in body, (
            f"{name} does not reach its display order through the shared sort hook -- a table in "
            "this block that orders rows any other way is an unguarded second comparator"
        )
        assert "sort.entries" in body, (
            f"{name} maps something other than the hook's own total projection -- `sort.entries` "
            "is one entry per served row, which is what keeps this block uncapped"
        )

    assert "<TableSortNote" in block, (
        "the Forward Returns block no longer discloses a non-served order"
    )
    assert ".slice(" not in block, (
        "the Forward Returns block slices what it renders -- it must stay uncapped"
    )


def test_the_forward_block_sort_narrowing_can_fail_on_a_seeded_violation():
    """A lint that cannot fail proves nothing."""
    seeded_hand_rolled = "function DeskForwardTable() { const r = [...record.rows].sort(cmp); }"
    body = _extract_function(seeded_hand_rolled, "DeskForwardTable")
    assert "useTableSort(" not in body
    assert _REORDER_RE.findall(body), "a hand-rolled comparator must still trip the ban above"


# Six sections render COLLAPSED, with their own read deferred until the first expand. Each entry
# pairs a section with the fetch that fills it.
#
# Four own a single, un-keyed read ("every run ever logged"), so "already fetched" is a one-shot
# fact and the read is issued from the expand handler.
_EXPAND_READ_SECTIONS = (
    ("screenRuns", "fetchDeskScreenRuns("),
    ("topupRuns", "fetchDeskTopupRuns("),
    ("indexReconciliation", "fetchDeskReconcileRuns("),
    ("playbookEvidence", "fetchDeskPlaybookEvidence("),
)

# The other two are keyed on the DISPLAYED snapshot, so their answer changes as the operator moves
# through history and "already fetched" is not a one-shot fact. Those keep their own effect, gated
# on the section being open -- expanding re-runs it, and a history selection while open refetches.
_KEYED_READ_SECTIONS = (
    ("screenComparison", "setScreenCompareResult(null);"),
    ("provenance", "setDisplayedPinsResult(null);"),
)

_ALL_COLLAPSED_SECTIONS = tuple(s for s, _ in _EXPAND_READ_SECTIONS) + tuple(
    s for s, _ in _KEYED_READ_SECTIONS
)

# Reads that must NEVER be deferred: they feed the compute controls, which are not collapsed.
# Deferring one would silently blank a shipped disclosure while its section went on rendering.
_UNDEFERRED_READS = (
    "fetchDeskScreenCompute(",
    "fetchDeskTopupCompute(",
    "fetchDeskReconcileCompute(",
    "fetchDeskForwardCompute(",
)


def _mount_effect(source: str) -> str:
    """The one mount effect's body -- the `useEffect(() => {...}, [])` that issues the page's
    un-keyed GETs. Bounded by its own empty dependency array."""
    start = source.index("let alive = true;\n    fetchDeskScreen()")
    return source[start : source.index("}, []);", start)]


def test_the_mount_effect_extractor_finds_a_real_effect():
    """A counter-test for the helper: every assertion over it is only as honest as this slice."""
    body = _mount_effect(_DESK_PAGE.read_text())
    assert "fetchDeskScreen()" in body and "fetchDeskSessions()" in body
    assert len(body) > 400, "the mount-effect slice is implausibly short"


def test_every_collapsed_section_starts_collapsed():
    """Collapsed is the DEFAULT, not a state the page can be left in. An initial value seeded with
    any section open would quietly undo the decluttering the collapse exists for."""
    source = _DESK_PAGE.read_text()
    assert "useState<ReadonlySet<DeskCollapsibleSection>>(\n    () => new Set(),\n  )" in source, (
        "the expanded-sections state no longer starts as an empty set -- some section would open "
        "on load"
    )


def test_a_collapsed_sections_heading_stays_outside_its_collapsed_body():
    """The heading must render whether or not the section is open.

    Not cosmetic: a shipped golden resolves every assertion with `state="visible"`, so a section
    whose own title disappeared when collapsed would read as GONE rather than closed -- and the
    operator would have nothing to click."""
    header = (_FRONTEND_ROOT / "components" / "CollapsibleSection.tsx").read_text()
    title_at = header.index("{title}")
    body_at = header.index("{open && (")
    assert title_at < body_at, (
        "the section title is rendered inside the conditional body -- a collapsed section would "
        "lose its own name and its expand control with it"
    )
    assert "aria-expanded={open}" in header and "aria-controls=" in header
    assert 'type="button"' in header, (
        "the expand control is not a real button -- a click handler on a non-interactive element "
        "is unreachable by keyboard and announces nothing"
    )


def test_a_collapsed_section_defers_its_own_read_until_expanded():
    """The property: a section and the GET that fills it are deferred TOGETHER.

    Render it lazily but fetch eagerly and the page keeps paying for answers nothing displays;
    fetch lazily but render eagerly and an expanded section stares at a loading skeleton nothing
    ever fills. So each section's read must be reachable only from its own expand path."""
    source = _DESK_PAGE.read_text()
    mount = _mount_effect(source)

    for section in _ALL_COLLAPSED_SECTIONS:
        assert f'id="{section}"' in source, f"{section} has no CollapsibleSection of its own"
        assert f'expandedSections.has("{section}")' in source, (
            f"{section}'s open state is not read from the expanded-sections set"
        )

    # (a) the four one-shot reads: issued from the expand handler, and ABSENT from the mount effect
    handler_at = source.index("function toggleSection(")
    handler = source[handler_at : source.index("\n  }", handler_at)]
    for section, fetch in _EXPAND_READ_SECTIONS:
        assert fetch in handler, (
            f"{fetch} is not issued from the expand handler -- a collapsed section's read must "
            "happen when it opens, not on load"
        )
        assert fetch not in mount, (
            f"{fetch} still fires from the mount effect -- the section is collapsed, so nothing "
            "renders what it fetches"
        )
    assert "sectionReadIssuedRef.current.has(section)" in handler, (
        "the expand handler does not remember which sections it has already read -- collapsing "
        "and re-expanding would refetch every time"
    )

    # (b) the two keyed reads: still their own effect, gated on the section, cleared BEFORE the
    # return so a stale answer never survives under a new heading
    for section, clear in _KEYED_READ_SECTIONS:
        pair = f'{clear}\n'
        assert pair in source
        gate = f'if (!expandedSections.has("{section}")) return;'
        assert gate in source, f"{section}'s keyed read is not gated on its own open state"
        assert source.index(clear) < source.index(gate), (
            f"{section} returns BEFORE clearing its own state -- the previous snapshot's answer "
            "would stay on screen under the new one's heading"
        )

    # (c) reads that feed the still-open controls are deferred by nothing
    for undeferred in _UNDEFERRED_READS:
        assert undeferred in mount, (
            f"{undeferred} no longer fires on mount -- it feeds a control that is not collapsed, "
            "so deferring it blanks a shipped disclosure"
        )


def test_the_deferred_read_guard_can_fail_on_a_seeded_violation():
    """A lint that cannot fail proves nothing. Three seeds, one per way the pairing can break."""
    # Rendered lazily but fetched eagerly: the read is still in the mount effect.
    eager = "let alive = true;\n    fetchDeskScreen()\n    fetchDeskScreenRuns();\n  }, []);"
    assert "fetchDeskScreenRuns(" in _mount_effect(eager)

    # Fetched lazily but never remembered: every expand refetches.
    forgetful = 'function toggleSection(s) {\n    fetchDeskScreenRuns().then(set);\n  }'
    assert "sectionReadIssuedRef.current.has(section)" not in forgetful

    # Returning BEFORE the clear leaves the previous snapshot's answer on screen.
    clear_after_return = (
        'if (!expandedSections.has("screenComparison")) return;\n'
        "    setScreenCompareResult(null);"
    )
    gate_at = clear_after_return.index('if (!expandedSections.has("screenComparison")) return;')
    assert clear_after_return.index("setScreenCompareResult(null);") > gate_at


def test_the_sign_convention_line_reads_the_record_and_never_assumes_one():
    """The panel must branch on the record's OWN served `return_sign_convention`, with an explicit
    fallback for records written before the convention existed -- a hardcoded 'signed to side'
    caption would mislabel every stored raw-signed record the append-only ledger still serves."""
    source = _DESK_PAGE.read_text()
    block = _forward_block(source)
    assert "return_sign_convention" in block, (
        "the Forward Returns block never reads the record's own return_sign_convention -- the "
        "reading rule it prints would then be an assumption, not the record's own declaration"
    )
    assert "?? \"raw\"" in block, (
        "the sign-convention read has no fallback for a record predating the convention -- those "
        "carry raw price moves and must be labelled as such, never relabelled as side-signed"
    )


def test_every_touch_cell_reaches_its_value_through_the_guarded_binding():
    """The desk arithmetic guard (`test_desk_ui_guards.py::_PRICE_ARITHMETIC_FIELDS`) can only see
    what is written as `touchValue.<served field>` / `touchRow.<served field>`. Renaming those into
    local props on the way into a cell would route the whole per-touch table around the one lint
    proving the page derives no number of its own -- so the cells must be written against the
    bindings, and this asserts they still are.

    Not a style rule: the exit price is served precisely so a reader can CHECK the return, which
    is exactly the arithmetic the page must never do itself."""
    block = _forward_block(_DESK_PAGE.read_text())
    for binding in (
        "touchValue.exit_price",
        "touchValue.return_pct",
        "touchValue.mdd_long_pct",
        "touchValue.mdd_short_pct",
        "touchRow.close_price",
        "touchRow.entry_price",
    ):
        assert binding in block, (
            f"the Forward Returns block no longer renders {binding} through its guarded binding "
            "-- the arithmetic lint cannot see a value passed under a different local name"
        )


def test_the_session_end_group_copies_served_values_and_derives_none():
    """The close group is rendered by the same component as a horizon, so its four numbers are
    re-keyed into a horizon-shaped object. Every one must be a VERBATIM copy of a served field --
    a `truncated`/`reason` literal is fine (they describe the shape, not a measurement), an
    arithmetic expression is not."""
    body = _extract_function(_DESK_PAGE.read_text(), "forwardCloseMeasure")
    for assignment in (
        "return_pct: touchRow.to_close_pct",
        "exit_price: touchRow.close_price",
        "mdd_long_pct: touchRow.mdd_long_pct",
        "mdd_short_pct: touchRow.mdd_short_pct",
        "effective_minutes: touchRow.minutes_to_close",
    ):
        assert assignment in body, f"forwardCloseMeasure no longer copies {assignment} verbatim"
    assert _ARITHMETIC_RE.search(body) is None, (
        f"forwardCloseMeasure derives a value ({_ARITHMETIC_RE.findall(body)}) -- it may only "
        "re-key already-served numbers under the horizon-leaf field names"
    )


def test_the_all_absent_note_reads_the_served_reason_field_not_a_recomputed_count():
    """The banner must fire on the condition a reader actually sees -- a record with rows, not one
    of which carries a measurement -- and must reach that by testing the served `reason` field
    rather than re-deriving any served number client-side."""
    body = _extract_function(_DESK_PAGE.read_text(), "ForwardAbsenceNote")
    assert "record.rows.every((row) => row.reason !== null)" in body, (
        "ForwardAbsenceNote no longer derives its condition from the served per-row `reason` "
        "field -- a recomputed count would be a second, drift-prone owner of that fact"
    )
    assert "record.rows.length > 0" in body, (
        "a record with NO rows already has its own honest empty state (desk-forward-rows-empty); "
        "the absence banner must not claim that case too"
    )


def test_the_all_absent_note_has_a_distinct_sentence_for_every_session_state():
    """Three situations produce an identical table of em-dashes -- a non-session, a real session
    past the vendor's fine-bar retention floor, and a date that has not happened yet. The whole
    point of the banner is that they no longer read the same, so each branch must ship its own
    sentence, plus a bare fallback for when the daily bars cannot say."""
    body = _extract_function(_DESK_PAGE.read_text(), "forwardAbsenceText")
    for state in ("not_a_recorded_session", "after_recorded_evidence", "recorded_session"):
        assert f'state === "{state}"' in body, f"no distinct sentence for session state {state}"
    assert "no daily bar is recorded for that date either" in body
    assert "the session has not been recorded" in body
    assert "reach back about 30 days (1m) and 60 days (5m)" in body
    # No branch may assert a cause the served state does not carry: the `unknown` fallback states
    # the absence and stops.
    assert body.count("return `${head}") >= 1, "the unknown state has no bare fallback sentence"


def test_the_forward_block_reuses_no_golden_click_target():
    source = _DESK_PAGE.read_text()
    block = _forward_block(source)
    for needle in _FORBIDDEN_TESTID_ATTRS:
        assert needle not in block, f"the Forward Returns block reuses {needle}"
    assert _FORBIDDEN_DATA_SCREEN_ID_ATTR not in block, (
        "the Forward Returns block reuses data-screen-id= (a golden CSS click target)"
    )
    assert _FORBIDDEN_ROW_TESTID_ATTR_RE.search(block) is None, (
        "the Forward Returns block reuses a desk-row-* testid (the ranked table's own family)"
    )


def test_the_guards_can_fail_on_seeded_violations():
    """Counter-tests: each detection actually catches its violation."""
    assert _REORDER_RE.search("record.rows.slice(0, 20).map(") is not None
    assert _REORDER_RE.search("forwardRows.sort((a, b) => a.symbol.localeCompare(b.symbol))") is not None
    assert _ARITHMETIC_RE.search("return_pct: touchRow.to_close_pct - touchRow.entry_price,") is not None
    assert _ARITHMETIC_RE.search("exit_price: touchRow.close_price * 1.0,") is not None
    assert _ARITHMETIC_RE.search("exit_price: touchRow.close_price ?? null,") is None
    assert _FORBIDDEN_ROW_TESTID_ATTR_RE.search('<td data-testid="desk-row-distance">') is not None
    seeded_missing = "const x = 1;"
    assert [
        t for t in _REQUIRED_FORWARD_TESTIDS if f'testid="{t}"' not in seeded_missing
    ] == list(_REQUIRED_FORWARD_TESTIDS)
    # A testid named only in prose does not count as shipped.
    mentioned_only = "// never reuse desk-forward-detail-table as a click target\n"
    assert "desk-forward-detail-table" in [
        t for t in _REQUIRED_FORWARD_TESTIDS if f'testid="{t}"' not in mentioned_only
    ]
