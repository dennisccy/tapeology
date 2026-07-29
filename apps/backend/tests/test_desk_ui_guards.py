"""era-desk-iter-6 (J-05) source-introspection guard tests -- the ``test_copy_discipline.py``
pattern (read a frontend .tsx file as TEXT, assert on substrings; no browser, no runtime).

Three guards, each proving something about the frontend a backend-only test suite otherwise could
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
