"""era-desk-iter-6 (J-05) source-introspection guard tests -- the ``test_copy_discipline.py``
pattern (read a frontend .tsx file as TEXT, assert on substrings; no browser, no runtime).

Guards, each proving something about the frontend a backend-only test suite otherwise could
not see:

  (a) TC-5 -- ``apps/frontend/app/desk/page.tsx`` never references any of the structure-side
      compute endpoints/functions (``/research/tradability``, ``/research/levels``,
      ``compute_tradability``, ``compute_levels``) -- every number the desk briefing renders comes
      from the already-fetched screen snapshot (``GET /research/desk/screen``), never a second,
      divergent computation (single-source-of-truth -- the era's own hard anti-goal).
  (b) TC-6 -- the NEW ``/structure`` query-param prefill block (delimited by the
      ``J-05-PREFILL-START``/``J-05-PREFILL-END`` markers in ``structure/page.tsx``) calls the
      SAME ``handleLoad`` the manual Load button already calls, and introduces no second
      fetch/compute path.
  (c) goal-desk-iter-17 (J-13) TC-8 -- ``apps/frontend/app/desk/page.tsx`` never derives a price
      value via arithmetic on ``row.distance_bps``/``row.price_low``/``row.price_high`` -- the new
      ``band`` column/tooltip line renders ``row.reference_close`` beside the row's own
      ``price_low``/``price_high``, never a value recomputed from them client-side.
  (d) goal-desk-iter-18 (J-14) TC-11 -- the SAME arithmetic guard, extended to also cover
      ``row.opposite_band``'s ``distance_bps``/``price_low``/``price_high``/``band_score`` and
      ``row.bands_by_class``'s ``A``/``B``/``C``/``unclassified`` counts -- the new ``opposite``
      column/tooltip line renders these fields verbatim, never a derived distance, price, or count.
  (e) goal-desk-iter-24 (J-16) TC-7 -- the ranked table's own layout REFLOW must not become a
      layout that silently changes what's rendered: `rows` renders in served order only (no
      `.sort(`/`.reverse(`/re-slice/comparator anywhere over `rows` -- the new `rank` cell is the
      `.map` index, never a client-recomputed position), and every `data-testid` a shipped
      journey's golden script or guard test depends on is still present in source after the
      reflow.

A guard that can never fail proves nothing -- each carries a seeded counter-test proving the
detection logic itself actually catches a violation (the ``test_copy_discipline.py``
seeded-violation precedent)."""

from __future__ import annotations

import pathlib
import re

_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
_DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"
_STRUCTURE_PAGE = _FRONTEND_ROOT / "app" / "structure" / "page.tsx"

_FORBIDDEN_DESK_REFERENCES = (
    "/research/tradability",
    "/research/levels",
    "compute_tradability",
    "compute_levels",
)

# Every fetch/compute-trigger function this page already imports from lib/api, PLUS a bare
# `fetch(` -- if the prefill block ever grows a second network call of its own rather than
# reusing `handleLoad`, one of these substrings will be present.
_FORBIDDEN_PREFILL_CALLS = (
    "fetchLevels(",
    "fetchTradability(",
    "recordBarSeries(",
    "createBacktest(",
    "triggerEdgeReportCompute(",
    "fetch(",
)


def test_desk_page_never_references_structure_compute_endpoints():
    """TC-5: every rendered desk value comes from the already-fetched screen snapshot -- the desk
    page source contains zero references to the structure-side compute endpoints/functions."""
    source = _DESK_PAGE.read_text()
    hits = [needle for needle in _FORBIDDEN_DESK_REFERENCES if needle in source]
    assert not hits, (
        f"apps/frontend/app/desk/page.tsx references {hits} -- the desk briefing must read every "
        "value from GET /research/desk/screen verbatim, never recompute a structure number "
        "client-side"
    )


def test_desk_page_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing."""
    seeded_source = "const x = fetch('/research/tradability?symbol=AAPL');"
    hits = [needle for needle in _FORBIDDEN_DESK_REFERENCES if needle in seeded_source]
    assert hits == ["/research/tradability"]


def _extract_prefill_block(source: str) -> str:
    start = source.index("// J-05-PREFILL-START")
    end = source.index("// J-05-PREFILL-END")
    assert start < end, "J-05-PREFILL-START must precede J-05-PREFILL-END"
    return source[start:end]


def test_structure_page_has_the_j05_prefill_markers():
    """The extraction below is only meaningful if the markers actually exist -- an absent block
    would otherwise make ``test_structure_prefill_reuses_the_existing_load_function`` vacuous
    (``str.index`` raises ``ValueError`` rather than silently matching nothing, so a missing
    marker already fails loudly; this test names that failure mode explicitly)."""
    source = _STRUCTURE_PAGE.read_text()
    assert "// J-05-PREFILL-START" in source
    assert "// J-05-PREFILL-END" in source
    assert "useSearchParams" in source


def test_structure_prefill_reuses_the_existing_load_function():
    """TC-6: the new query-param prefill block calls the SAME ``handleLoad`` the manual Load
    button already calls -- no second fetch/compute function is introduced."""
    source = _STRUCTURE_PAGE.read_text()
    block = _extract_prefill_block(source)
    assert "handleLoad(" in block, (
        "the J-05 prefill block never calls handleLoad() -- it must reuse the manual Load "
        "button's own load path, not a second one"
    )
    hits = [needle for needle in _FORBIDDEN_PREFILL_CALLS if needle in block]
    assert not hits, (
        f"the J-05 prefill block calls {hits} -- it must call ONLY the existing handleLoad(), "
        "never a second fetch/compute function"
    )


def test_structure_prefill_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail (counter-test): a seeded second fetch call inside the prefill block is
    caught, and a block missing the handleLoad() call is caught too."""
    seeded_block_with_second_fetch = (
        "// J-05-PREFILL-START\n"
        "useEffect(() => { fetchLevels(symbol, asOf); handleLoad(symbol, asOf); }, []);\n"
        "// J-05-PREFILL-END\n"
    )
    hits = [
        needle for needle in _FORBIDDEN_PREFILL_CALLS if needle in seeded_block_with_second_fetch
    ]
    assert hits == ["fetchLevels("]

    seeded_block_missing_handle_load = (
        "// J-05-PREFILL-START\nuseEffect(() => { setSymbolInput(symbol); }, []);\n"
        "// J-05-PREFILL-END\n"
    )
    assert "handleLoad(" not in seeded_block_missing_handle_load


# goal-desk-iter-17 (J-13) TC-8: no expression in the desk page may derive a NEW price value via
# arithmetic on `distance_bps`/`price_low`/`price_high` -- the honest disclosure this journey ships
# (`row.reference_close`, `row.price_low`-`row.price_high`) is a verbatim render of already-served
# values, never a client-side recomputation of the very number `reference_close` exists to disclose
# instead of forcing an operator (or agent) to invert `distance_bps` against a band edge.
# goal-desk-iter-18 (J-14): extended (never duplicated -- the iter-17 direct precedent) to also
# cover `row.opposite_band.*`'s distance/price/score fields and `row.bands_by_class.*`'s per-class
# counts -- the new `opposite` column/tooltip line renders these verbatim too, never a derived
# distance, price, or count (e.g. a client-side "total bands" sum or an implied spread).
_PRICE_ARITHMETIC_FIELDS = (
    r"row\.(?:distance_bps|price_low|price_high"
    r"|opposite_band\.(?:distance_bps|price_low|price_high|band_score)"
    r"|bands_by_class\.(?:A|B|C|unclassified))"
)
_PRICE_ARITHMETIC_PATTERN = re.compile(
    rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
)


def test_desk_page_never_derives_a_price_via_arithmetic_on_distance_or_band_edges():
    """TC-8/TC-11: scans `apps/frontend/app/desk/page.tsx`'s source for any expression combining
    `row.distance_bps`/`row.price_low`/`row.price_high` (goal-desk-iter-17, J-13) or
    `row.opposite_band.*`/`row.bands_by_class.*` (goal-desk-iter-18, J-14) with an arithmetic
    operator. The `band` column/tooltip line renders `row.reference_close` beside
    `row.price_low`/`row.price_high`, and the new `opposite` column/tooltip line renders
    `row.opposite_band`/`row.bands_by_class` verbatim -- never a derived value."""
    source = _DESK_PAGE.read_text()
    hits = _PRICE_ARITHMETIC_PATTERN.findall(source)
    assert not hits, (
        f"apps/frontend/app/desk/page.tsx derives a value via arithmetic on distance_bps/price_low/"
        f"price_high/opposite_band/bands_by_class ({hits}) -- the page must render only what "
        "GET /research/desk/screen already served, never recompute a value client-side"
    )


def test_desk_page_price_arithmetic_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing."""
    seeded_source = "const implied = row.price_high - row.reference_close;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_source) is not None


def test_desk_page_price_arithmetic_guard_catches_opposite_band_and_bands_by_class_arithmetic():
    """TC-11 (goal-desk-iter-18, J-14) counter-test: the extended guard also catches arithmetic on
    the new `opposite_band`/`bands_by_class` fields, not just the pre-existing distance_bps/
    price_low/price_high ones."""
    seeded_opposite = "const gap = row.opposite_band.price_high - row.price_high;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_opposite) is not None

    seeded_score = "const combined = row.opposite_band.band_score + row.band_score;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_score) is not None

    seeded_bands_by_class = "const total = row.bands_by_class.A + row.bands_by_class.B;"
    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_bands_by_class) is not None


# goal-desk-iter-24 (J-16) TC-7 (a): the ranked table's own reflow adds a `rank` cell rendering
# each row's own 1-based position in the served `rows` array (the `.map` index) -- this guard
# proves the page never sorts, reverses, or re-slices `rows` to produce that position (or any
# other display order) client-side. Matches a direct chain (`rows.sort(`), a spread-then-chain
# (`[...rows].sort(`), and an intervening simple call (e.g. `rows.filter(...).sort(`) -- `.filter(`
# alone (used elsewhere on this page only to COUNT rows, never to reorder or re-render them) is not
# itself forbidden.
_ROWS_REORDER_PATTERN = re.compile(
    r"(?:\[\s*\.\.\.\s*rows\s*\]|\brows\b)\s*(?:\.\s*\w+\([^()]*\)\s*)*\.\s*(?:sort|reverse|slice)\s*\("
)


def test_desk_page_never_reorders_rows_client_side():
    """TC-7: `rows` renders in the exact order `GET /research/desk/screen` served it in -- the
    page never sorts, reverses, or re-slices it. The new `rank` cell renders each row's own
    position in that SAME served order (the `.map` index), never a client-recomputed one."""
    source = _DESK_PAGE.read_text()
    match = _ROWS_REORDER_PATTERN.search(source)
    assert match is None, (
        f"apps/frontend/app/desk/page.tsx reorders `rows` client-side ({match.group(0)!r}) -- the "
        "page must render the served order verbatim; the rank cell renders each row's own array "
        "index, never a value derived from a client-side sort/reverse/slice"
    )


def test_desk_page_rows_reorder_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing."""
    seeded_sort = "const ranked = [...rows].sort((a, b) => a.distance_bps - b.distance_bps);"
    assert _ROWS_REORDER_PATTERN.search(seeded_sort) is not None

    seeded_reverse = "const reversed = rows.reverse();"
    assert _ROWS_REORDER_PATTERN.search(seeded_reverse) is not None

    seeded_slice = "const page1 = rows.slice(0, 10);"
    assert _ROWS_REORDER_PATTERN.search(seeded_slice) is not None

    seeded_chained = "const top = rows.filter(hasTickEvidence).sort((a, b) => a.rank - b.rank);"
    assert _ROWS_REORDER_PATTERN.search(seeded_chained) is not None


# goal-desk-iter-24 (J-16) TC-7 (b): every `data-testid` a shipped journey's golden replay script,
# guard test, or hover-tooltip contract depends on is still present in the source after the
# reflow -- the reflow may move a disclosure's markup (a new element, a new line inside the SAME
# row), but it must never drop, hide, or rename the testid itself. "the compute controls" (goal.md
# J-16 step 4) are the three primary trigger buttons this page ships (Run Screen / Top-up /
# Reconcile Index) -- untouched by this iteration's ranked-row-only reflow, checked here anyway as
# the cheapest possible proof nothing regressed. `desk-refresh-all-button` is the FOURTH compute
# control by that same definition (it drives all three of the above in sequence, plus the
# membership fetch). No golden script targets it and none ever should -- it is a write path, and
# every shipped desk golden is deliberately read-only -- so this static presence pin is the ONLY
# automated proof it still ships at all. Its behavioural guards live in
# test_desk_refresh_chain_guard.py.
_REQUIRED_DESK_TESTIDS = (
    "desk-screen-rows-table",
    "desk-row-drill-in",
    "desk-row-side",
    "desk-row-band-class",
    "desk-row-distance",
    "desk-row-score",
    "desk-coverage-badges",
    "desk-coverage-badge",
    "desk-row-tick-evidence",
    "desk-row-basis",
    "desk-row-history",
    "desk-row-band",
    "desk-row-opposite",
    "desk-row-levels",
    "desk-skip-row",
    "desk-history-row",
    "desk-provenance",
    "desk-title",
    "desk-run-screen-button",
    "desk-topup-button",
    "desk-reconcile-button",
    "desk-refresh-all-button",
)


def test_desk_page_keeps_every_shipped_testid_after_the_reflow():
    """TC-7: every testid a shipped journey's golden script/guard test/tooltip contract depends
    on is still present in the reflowed source -- the layout changed, nothing else did."""
    source = _DESK_PAGE.read_text()
    missing = [testid for testid in _REQUIRED_DESK_TESTIDS if testid not in source]
    assert not missing, (
        f"apps/frontend/app/desk/page.tsx is missing testid(s) {missing} after the reflow -- a "
        "shipped journey's golden script/guard test/tooltip contract depends on each of these "
        "remaining present with the same text"
    )


def test_desk_page_testid_presence_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing."""
    seeded_source = "const x = 1;"
    missing = [testid for testid in _REQUIRED_DESK_TESTIDS if testid not in seeded_source]
    assert missing == list(_REQUIRED_DESK_TESTIDS)


# goal-desk-iter-24 (J-16) TC-6/TC-7 (c): the reflow's own regression guard for the defect the
# iter-24 review caught -- dropping a ranked cell's in-cell label prefix ALSO deletes the literal
# page text a stored golden replay script asserts through `page.get_by_text`, which matches
# VISIBLE DOM TEXT only (the composite drill-in `title` carrying the same word is invisible to it).
# TC-6 allows zero golden-script edits, so the two cells a golden pins by literal text
# (`desk-row-band` <- J-13.json, `desk-row-opposite` <- J-14.json) must keep the prefix WORD the
# script's expected text starts with. This guard reads BOTH artifacts and ties them together, so a
# future prefix drop fails here (a fast, keyless, browser-free test) instead of only in a browser
# replay lane. The other three disclosure cells (basis/history/levels) are deliberately absent from
# this list: no stored golden asserts their prefixed text (J-08 pins "d before as-of", J-11 pins
# "sessions", J-15 has no script), which is exactly why dropping THOSE prefixes was safe.
_JOURNEY_SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[3] / "runs" / "goal-session-desk" / "journey-scripts"
)

_GOLDEN_TEXT_PINNED_CELLS = (
    ("J-13.json", "desk-row-band", "band "),
    ("J-14.json", "desk-row-opposite", "opposite "),
)


def _desk_cell_source(source: str, testid: str) -> str:
    """The source of the single `<td ... data-testid="<testid>"> ... </td>` block."""
    start = source.index(f'data-testid="{testid}"')
    end = source.index("</td>", start)
    return source[start:end]


def _golden_expected_texts(script_name: str) -> list[str]:
    """Every literal `text` a golden script asserts (step `expect` action or `expect` clause)."""
    import json

    data = json.loads((_JOURNEY_SCRIPTS_DIR / script_name).read_text())
    texts: list[str] = []
    for step in data.get("steps", []):
        for holder in (step.get("action") or {}, step.get("expect") or {}):
            text = holder.get("text")
            if isinstance(text, str):
                texts.append(text)
    return texts


def test_desk_row_cells_keep_the_label_prefix_their_golden_script_asserts():
    """TC-6: the `band`/`opposite` cells still render the prefix WORD their stored golden replay
    script's expected page text starts with -- dropping it fails J-13/J-14 on replay."""
    source = _DESK_PAGE.read_text()
    for script_name, testid, prefix in _GOLDEN_TEXT_PINNED_CELLS:
        pinned = [t for t in _golden_expected_texts(script_name) if t.startswith(prefix)]
        assert pinned, (
            f"{script_name} no longer asserts any page text starting with {prefix!r} -- this pin "
            f"has gone vacuous; re-derive it from the script's own expected texts"
        )
        cell = _desk_cell_source(source, testid)
        assert f"`{prefix}" in cell, (
            f"apps/frontend/app/desk/page.tsx's {testid} cell no longer renders the {prefix!r} "
            f"label prefix, but {script_name} asserts the literal page text {pinned[0]!r} via "
            f"page.get_by_text (visible DOM text only -- a `title` attribute does not satisfy it). "
            f"TC-6 permits zero golden-script edits, so this cell must keep the prefix word."
        )


def test_desk_row_label_prefix_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing."""
    seeded_cell = (
        'data-testid="desk-row-band">\n'
        "  {row.reference_close == null\n"
        "    ? `${fmt(row.price_low)}–${fmt(row.price_high)} · close not recorded in this snapshot`\n"
        "    : `${fmt(row.price_low)}–${fmt(row.price_high)} · close ${fmt(row.reference_close)}`}\n"
        "</td>"
    )
    cell = _desk_cell_source(seeded_cell, "desk-row-band")
    assert "`band " not in cell

    # and the pin itself is non-vacuous: J-13/J-14 really do assert those literal texts today
    assert any(t.startswith("band ") for t in _golden_expected_texts("J-13.json"))
    assert any(t.startswith("opposite ") for t in _golden_expected_texts("J-14.json"))
