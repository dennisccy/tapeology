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
    'aria-label="Run Screen, Top-up and Reconcile Index controls"',
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
