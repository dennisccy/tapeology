"""Structural guards for the cockpit tradable-band overlay + confluence chip (era-5B J-06).

PriceChart.tsx has no frontend test runner behind it (no `test` npm script, no `.test.ts(x)` file
anywhere in this repo — see every prior era-5B iteration's dev handoff); this repo's established
precedent for testing frontend LOGIC keylessly is a Python source-inspection test that reads the
`.tsx` source directly (test_profile_equivalence.py's `test_performance_page_offers_no_profile_
selection_control`, test_strategies_api.py's `test_strategies_module_carries_no_second_copy_of_
the_id_strings`, and this module's own sibling test_copy_discipline.py's frontend-literal scan).
This module extends that precedent to J-06's two hardest-to-verify-by-inspection invariants:

  1. the confluence chip's "which tape state confirms this band's side" decision reads the SERVED
     `/research/strategies` `structure_tape_map` mapping — never a client-hardcoded literal of one
     of the four tape-state names (single-source-of-truth / no-client-recomputation);
  2. the band overlay's fetch is keyed on `ticker` alone and passes the CURRENT wall-clock time as
     `as_of` (no client-side "which is the prior session" date arithmetic — the no-lookahead
     resolution is entirely server-side, in `tradability.py`'s own `_resolve_basis`).

Copy-discipline coverage (imperative/prediction/claim language in the new chip text) is NOT
duplicated here: `test_copy_discipline.py::test_lint_frontend_source_literals_are_clean` already
walks every `.tsx` string literal under `apps/frontend/components/**` and `apps/frontend/app/**`,
so it automatically covers PriceChart.tsx's new chip copy.
"""

from __future__ import annotations

import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"
PRICE_CHART = FRONTEND_DIR / "components" / "PriceChart.tsx"
PAGE_TSX = FRONTEND_DIR / "app" / "page.tsx"

# The four tape-state names the confirmation MAPPING may name. Legitimate ONLY inside the
# pre-existing MARKER_COLORS / STATE_LABELS cosmetic marker color/label dicts (unrelated to the
# confluence-matching decision) — every other occurrence would be a hardcoded restatement of the
# server-owned `rejection_states` / `breakthrough_states` mapping.
_TAPE_STATE_NAMES = ("bid_absorption", "ask_absorption", "buyer_control", "seller_control")
_STATE_LITERAL = re.compile(r'["\'](' + "|".join(_TAPE_STATE_NAMES) + r')["\']')


def _source() -> str:
    assert PRICE_CHART.exists(), f"expected {PRICE_CHART} to exist"
    return PRICE_CHART.read_text()


def _excluded_literal_lines(lines: list[str]) -> set[int]:
    """Line indices (0-based) inside the pre-existing MARKER_COLORS / STATE_LABELS object-literal
    blocks — the ONE allowed place a bare tape-state-name string literal may appear (cosmetic
    marker color/label lookups, unrelated to the chip's confirmation decision)."""
    excluded: set[int] = set()
    in_block = False
    for i, line in enumerate(lines):
        if re.search(r"const (MARKER_COLORS|STATE_LABELS)\s*:", line):
            in_block = True
        if in_block:
            excluded.add(i)
        if in_block and line.strip().startswith("};"):
            in_block = False
    return excluded


def test_confluence_matching_has_no_hardcoded_tape_state_literal():
    """The chip's "does the tape confirm this band's side" decision must compare the served
    `tapeState` prop against the FETCHED `structure_tape_map` entry's `rejection_states` /
    `breakthrough_states` fields — never a client-hardcoded copy of one of the four state names.
    Scoped to exclude the pre-existing MARKER_COLORS/STATE_LABELS dicts (cosmetic marker
    color/label lookups that already hardcode all four names for an unrelated purpose)."""
    lines = _source().splitlines()
    excluded = _excluded_literal_lines(lines)
    offenders = [
        (i + 1, line.strip())
        for i, line in enumerate(lines)
        if i not in excluded and _STATE_LITERAL.search(line)
    ]
    assert not offenders, (
        "hardcoded tape-state-name literal found outside the allowed MARKER_COLORS/STATE_LABELS "
        f"dicts (must instead read off the served /research/strategies mapping): {offenders}"
    )


def test_confluence_matching_reads_rejection_and_breakthrough_off_the_served_entry():
    """`rejection_states` / `breakthrough_states` must appear as PROPERTY READS (`.rejection_states`
    / `.breakthrough_states` — reading a field off the fetched strategies payload) — never as
    object-literal KEYS (`rejection_states:` / `breakthrough_states:`), which would mean the
    component declared its OWN restated copy of the mapping shape instead of reading the served
    one."""
    source = _source()
    assert ".rejection_states" in source, "expected a read of the served entry's rejection_states field"
    assert ".breakthrough_states" in source, "expected a read of the served entry's breakthrough_states field"
    assert "rejection_states:" not in source, (
        "found an object-literal `rejection_states:` KEY — the mapping must be READ off the served "
        "payload, never restated as a local object literal"
    )
    assert "breakthrough_states:" not in source, (
        "found an object-literal `breakthrough_states:` KEY — the mapping must be READ off the "
        "served payload, never restated as a local object literal"
    )


def test_confluence_selects_structure_tape_map_strategy_entry():
    """The chip must look up the `structure_tape_map` entry specifically (the registered strategy
    this era's rejection/breakthrough mapping lives on) — mirrors app/structure/page.tsx's OWN
    `STRATEGY_TAPE_ID = "structure_tape"` constant precedent (a registry-lookup key literal is
    legitimate; it is not tape-state confirmation vocabulary)."""
    source = _source()
    assert "structure_tape_map" in source
    assert "fetchStrategies" in source


def test_tradability_bands_fetch_is_keyed_on_ticker_and_stable_session_anchor_not_polled():
    """The bands fetch must be keyed on `[ticker, history?.epoch_anchor]` — NOT on `barSize`, and
    NOT folded into the existing 1s `setInterval` history poll. `epoch_anchor` is a STABLE per-watch
    value (the engine sets it once at watch-start and it never changes while the same ticker stays
    watched), so keying on it still fetches at most once or twice per watch (not every poll tick) —
    the tradable map is date-bounded and does not move intraday, unlike the tape-history poll."""
    source = _source()
    idx = source.index("fetchTradability(")
    tail = source[idx : idx + 900]
    m = re.search(r"\},\s*\[([^\]]*)\]\s*\)\s*;", tail)
    assert m, "could not find the enclosing effect's dependency array after the fetchTradability( call"
    deps = m.group(1).strip()
    assert deps == "ticker, history?.epoch_anchor", (
        f"expected the bands effect to be keyed on [ticker, history?.epoch_anchor], found deps={deps!r}"
    )


def test_tradability_as_of_uses_the_watched_sessions_own_anchor_with_no_client_side_session_math():
    """`as_of` must be the WATCHED SESSION's own current moment: `history.epoch_anchor` (Data
    Contract row 13, already fetched by the existing history poll — no new fetch) converted to an
    ISO string, falling back to the current wall-clock time only before the first `history`
    response lands. This is what makes a HISTORICAL replay of a PAST session (e.g. 2026-06-22)
    resolve THAT session's own prior-close basis (2026-06-18) — using the browser's wall-clock
    "now" instead would resolve TODAY's basis, which is unrelated to whatever price action is being
    replayed (verified empirically: a live AAPL 2026-06-22 replay showed no band anywhere near the
    replayed price when as_of was wall-clock "now"). No-lookahead guard: the frontend must contain
    no local "prior session" date arithmetic — `_resolve_basis` (tradability.py) alone decides the
    prior session server-side; this only supplies WHICH moment to resolve from."""
    source = _source()
    idx = source.index("fetchTradability(")
    call_site = source[idx : idx + 60]
    assert "asOf" in call_site, "expected fetchTradability to be called with a computed `asOf` variable"
    # The `asOf` computation itself, just above the call site.
    as_of_computation = source[max(0, idx - 400) : idx]
    assert "history?.epoch_anchor" in as_of_computation or "history.epoch_anchor" in as_of_computation, (
        "expected the as_of computation to read history's epoch_anchor field"
    )
    assert "epoch_anchor * 1000" in as_of_computation, (
        "expected epoch_anchor (seconds) to be converted to ms the SAME way this file already does "
        "for candle timestamps (toClock), not a fresh unit convention"
    )
    assert "new Date().toISOString()" in as_of_computation, (
        "expected a current-wall-clock-time fallback for before the first history response lands"
    )
    banned_session_math = [
        "getPreviousTradingDay",
        "priorSession",
        "previousSession",
        "subtractDays",
        "setDate(",
        "getDay()",
    ]
    offenders = [b for b in banned_session_math if b in source]
    assert not offenders, f"found apparent client-side prior-session date arithmetic: {offenders}"


def test_strategies_fetched_once_on_mount_not_per_ticker():
    """`fetchStrategies()` is ticker-independent config/registry data — it must be fetched in an
    effect with an EMPTY dependency array (mount-only), not re-fetched per ticker/tick."""
    source = _source()
    idx = source.index("fetchStrategies(")
    tail = source[idx : idx + 500]
    m = re.search(r"\},\s*\[([^\]]*)\]\s*\)\s*;", tail)
    assert m, "could not find the enclosing effect's dependency array after the fetchStrategies() call"
    deps = m.group(1).strip()
    assert deps == "", f"expected the strategies effect to be mount-only ([]), found deps={deps!r}"


def test_band_overlay_reads_only_served_band_fields():
    """The band overlay must draw ONLY served `TradabilityBand` fields (verbatim, reusing
    StructureChart.tsx's L97-120 pattern) — no local scoring/clustering. Checks for the exact
    property-access substrings the served shape provides."""
    source = _source()
    for field in (
        "band.side",
        "band.price_low",
        "band.price_high",
        "band.class",
        "band.quality_score",
        "band.round_number",
    ):
        assert field in source, f"expected the band overlay to read {field} verbatim"
    assert "createPriceLine" in source


def test_no_tradable_map_empty_state_present():
    """A SIM-*/no-bar-series symbol must show an explicit, honest 'no tradable map' state — never a
    fabricated band. Reuses the pre-existing `EmptyHint` component (already imported)."""
    source = _source()
    assert "no_bar_series_for_symbol" in source
    assert re.search(r"no tradable map", source, re.IGNORECASE)
    assert source.count("<EmptyHint") >= 2, (
        "expected a SECOND EmptyHint usage beyond the pre-existing 'no price history' one"
    )


def test_page_threads_tape_state_prop_and_preserves_live_mode_gate():
    """`page.tsx` must pass the WS-snapshot's own `tape_state` field into `PriceChart` as the new
    `tapeState` prop, WITHOUT touching the pre-existing sim/historical-only render gate (the gate
    alone is what keeps live mode byte-identical — the iter-7 plan's explicit "do not touch"
    instruction)."""
    source = PAGE_TSX.read_text()
    assert "tapeState={snapshot?.tape_state ?? null}" in source, (
        "expected page.tsx to pass tapeState={snapshot?.tape_state ?? null} into PriceChart"
    )
    assert '(mode === "sim" || mode === "historical")' in source, (
        "the live-mode gate must be present and unchanged"
    )
