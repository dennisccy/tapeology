"""era-desk-iter-6 (J-05) source-introspection guard tests -- the ``test_copy_discipline.py``
pattern (read a frontend .tsx file as TEXT, assert on substrings; no browser, no runtime).

Two guards, each proving something about the frontend a backend-only test suite otherwise could
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

A guard that can never fail proves nothing -- each carries a seeded counter-test proving the
detection logic itself actually catches a violation (the ``test_copy_discipline.py``
seeded-violation precedent)."""

from __future__ import annotations

import pathlib

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
