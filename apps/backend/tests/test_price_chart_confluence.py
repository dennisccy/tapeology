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
  2. the band overlay's fetch is keyed on `[ticker, history?.epoch_anchor]` (not `ticker` alone) and
     is DEFERRED — no request is issued — until `history?.epoch_anchor` resolves, with NO
     wall-clock-"now" fallback anywhere in the `as_of` computation (no client-side "which is the
     prior session" date arithmetic either — the no-lookahead resolution is entirely server-side, in
     `tradability.py`'s own `_resolve_basis`).

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
STRUCTURE_CHART = FRONTEND_DIR / "components" / "StructureChart.tsx"
PAGE_TSX = FRONTEND_DIR / "app" / "page.tsx"
# The ONE shared tradable-map read both surfaces (this cockpit container and /structure's Tradable
# Map) fetch through — the fetch-shape invariants below are asserted where the fetch now lives.
TRADABILITY_HOOK = FRONTEND_DIR / "lib" / "useTradability.ts"

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
    """The bands read must be keyed on the LATCHED per-watch anchor — NOT on the view, and NOT
    folded into the existing 1s `setInterval` history poll. `epoch_anchor` is a STABLE per-watch
    value (the engine sets it once at watch-start and it never changes while the same ticker stays
    watched), but the raw `history` object transiently nulls on every VIEW SWITCH (the poll effect
    resets it) — so the container LATCHES the anchor once per watch (reset only on a ticker
    change; a transient null never clears it) and hands the SHARED `useTradability` hook a stable
    (ticker, asOfIso) pair: at most one fetch per watch, and the band overlay never flashes off on
    a Tape/History toggle. The hook itself — the ONE tradable-map read both this container and
    /structure use — is VALUE-KEYED: its single fetch effect re-runs only when
    (symbol, asOfIso, reloadSeq) actually changes, never on a poll tick."""
    source = _source()
    # The container reads the map through the shared hook, fed by the latched anchor — never a
    # direct fetch of its own.
    assert "useTradability(ticker, tradabilityAsOfIso)" in source, (
        "expected the container to read the map via the shared useTradability hook, keyed on the "
        "latched anchor"
    )
    assert "fetchTradability(" not in source, (
        "the container must not fetch the tradable map directly — the shared hook owns that read"
    )
    # The latch assigns only a RESOLVED anchor (a view-switch transient null never clears it)...
    assert "epoch_anchor != null" in source, (
        "expected the latch to be guarded on a non-null history?.epoch_anchor"
    )
    # ...and resets only when the ticker (the watched session) changes.
    reset_idx = source.index("setLatchedAnchor(null)")
    assert "[ticker]" in source[reset_idx : reset_idx + 250], (
        "expected the latch reset effect to be keyed on [ticker] alone"
    )
    # The shared hook's ONE fetch effect is value-keyed — never polled.
    hook = TRADABILITY_HOOK.read_text()
    idx = hook.index("fetchTradability(")
    m = re.search(r"\},\s*\[([^\]]*)\]\s*\)\s*;", hook[idx : idx + 900])
    assert m, "could not find the hook effect's dependency array after the fetchTradability( call"
    deps = m.group(1).strip()
    assert deps == "symbol, asOfIso, reloadSeq", (
        f"expected the hook's fetch effect to be keyed on [symbol, asOfIso, reloadSeq], found deps={deps!r}"
    )


def test_tradability_as_of_uses_the_watched_sessions_own_anchor_with_no_client_side_session_math():
    """`as_of` must be the WATCHED SESSION's own current moment: `history.epoch_anchor` (Data
    Contract row 13, already fetched by the existing history poll — no new fetch) converted to an
    ISO string. There is NO wall-clock-"now" fallback anywhere in the computation: an early-return
    guard defers the fetch entirely (issues no request, stays in `phase: "loading"`) until
    `history?.epoch_anchor` resolves. This is what makes a HISTORICAL replay of a PAST session
    (e.g. 2026-06-22) resolve THAT session's own prior-close basis (2026-06-18) at every moment,
    including the sub-second window before the first `history` response lands — the request is
    simply not issued yet, rather than issued against today's date (the prior iteration's wall-clock
    fallback was observed to transiently draw today's-basis bands during that window; this iteration
    removes the fallback entirely instead of narrowing it). No-lookahead guard: the frontend must
    contain no local "prior session" date arithmetic — `_resolve_basis` (tradability.py) alone
    decides the prior session server-side; this only supplies WHICH moment to resolve from, and only
    once that moment is known."""
    source = _source()
    hook = TRADABILITY_HOOK.read_text()
    # The latch reads the SERVED anchor field verbatim, and the ISO conversion multiplies the
    # latched seconds by 1000 — the SAME pure unit conversion this file already does for candle
    # timestamps (toClock), not a fresh unit convention and never a date computation.
    assert "setLatchedAnchor(history.epoch_anchor)" in source, (
        "expected the latch to read history's own epoch_anchor field verbatim"
    )
    assert "latchedAnchor * 1000" in source, (
        "expected the latched epoch (seconds) to be converted to ms for the ISO as_of"
    )
    # No wall-clock-'now' fallback anywhere in the container OR the shared hook: while the anchor
    # is unresolved the hook DEFERS (issues no request), never asks about today's date. This is
    # what makes a HISTORICAL replay of a PAST session (e.g. 2026-06-22) resolve THAT session's
    # own prior-close basis (2026-06-18) at every moment, including the sub-second window before
    # the first `history` response lands.
    for text, name in ((source, "PriceChart.tsx"), (hook, "useTradability.ts")):
        assert "new Date().toISOString()" not in text, (
            f"found a wall-clock-'now' fallback in {name} — the read must defer until the caller's "
            "moment resolves, never fall back to today's date"
        )
    # The hook's deferred branch: `asOfIso == null` issues NO request and reports phase "loading"
    # (never "idle", so ready-only empty-state logic downstream stays quiet). Anchored on the CODE
    # form (`if (...)`) so the docstring's own mention of the guard never matches first.
    idx = hook.index("if (asOfIso == null)")
    deferred = hook[idx : idx + 400]
    deferred_body = deferred[: deferred.index("return;")]
    assert 'phase: "loading"' in deferred_body, (
        'expected the deferred (asOfIso == null) branch to report phase: "loading"'
    )
    assert "fetchTradability(" not in deferred_body, (
        "the deferred branch must issue NO request"
    )
    assert hook.count('phase: "loading"') >= 2, (
        "expected BOTH the deferred branch and the actual pre-fetch state update to set "
        'phase: "loading" while the moment is unresolved or a fetch is in flight'
    )
    banned_session_math = [
        "getPreviousTradingDay",
        "priorSession",
        "previousSession",
        "subtractDays",
        "setDate(",
        "getDay()",
    ]
    for text, name in ((source, "PriceChart.tsx"), (hook, "useTradability.ts")):
        offenders = [b for b in banned_session_math if b in text]
        assert not offenders, (
            f"found apparent client-side prior-session date arithmetic in {name}: {offenders}"
        )


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
    """The band overlay must draw ONLY served `TradabilityBand` fields (verbatim) — no local
    scoring/clustering. The cockpit now delegates the DRAWING to StructureChart.tsx (the shared
    renderer) via the `bands` prop, so the band-field reads live there; PriceChart.tsx only passes
    the served `bands` through. Checks the exact property-access substrings on the renderer."""
    source = STRUCTURE_CHART.read_text()
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
    # And the cockpit container hands the served bands straight to the renderer (no local reshaping).
    assert "bands={tradabilityState.data?.bands ?? []}" in _source()


def test_no_tradable_map_empty_state_present():
    """A SIM-*/no-bar-series symbol must show an explicit, honest 'no tradable map' state — never a
    fabricated band. Reuses the pre-existing `EmptyHint` component (already imported)."""
    source = _source()
    assert "no_bar_series_for_symbol" in source
    assert re.search(r"no tradable map", source, re.IGNORECASE)
    assert source.count("<EmptyHint") >= 2, (
        "expected a SECOND EmptyHint usage beyond the pre-existing 'no price history' one"
    )


def test_page_threads_tape_state_prop_and_renders_chart_in_live_mode_too():
    """`page.tsx` must pass the WS-snapshot's own `tape_state` field into `PriceChart` as the
    `tapeState` prop. The cockpit-chart upgrade REMOVES the old sim/historical-only render gate: the
    chart now renders in every data mode (live included), where it draws live moving bars built from
    the tape (the engine learns its true-clock anchor at the first live event). The `waiting`/
    `connecting`/`failed` gates still keep it hidden until there is something real to chart."""
    source = PAGE_TSX.read_text()
    assert "tapeState={snapshot?.tape_state ?? null}" in source, (
        "expected page.tsx to pass tapeState={snapshot?.tape_state ?? null} into PriceChart"
    )
    assert '(mode === "sim" || mode === "historical")' not in source, (
        "the sim/historical-only chart gate must be GONE — the chart renders in live mode too"
    )
