"""Structural guards for the cockpit chart upgrade (Tradable-Map chart + live tape bars).

Same keyless source-inspection precedent as test_price_chart_confluence.py / test_structure_chart_
viewport.py (no frontend test runner in this repo). These pin the invariants a later refactor could
silently undo while everything still renders:

  1. the cockpit chart renders in EVERY data mode (live included) — the old sim/historical-only gate
     is gone;
  2. PriceChart.tsx is a CONTAINER — it delegates all drawing to the shared StructureChart and holds
     no chart library of its own;
  3. the live "history"-mode bars are the BACKEND's wall-clock timeframe bars, read verbatim (no
     client-side OHLC re-binning);
  4. the no-lookahead clamp is real — the recorded-store window is fetched strictly BEFORE the
     replay start and never pages forward;
  5. StructureChart's new cockpit props are all optional/defaulted (so /structure is byte-identical);
  6. the two-group (Tape / History) selector is present with an honest empty History group;
  7. the timeframe helpers are shared from one module (no duplicated TIMEFRAME_ORDER literal).
"""

from __future__ import annotations

import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BACKEND_DIR.parent / "frontend"
PRICE_CHART = FRONTEND_DIR / "components" / "PriceChart.tsx"
STRUCTURE_CHART = FRONTEND_DIR / "components" / "StructureChart.tsx"
PAGE_TSX = FRONTEND_DIR / "app" / "page.tsx"
STRUCTURE_PAGE = FRONTEND_DIR / "app" / "structure" / "page.tsx"
BAR_WINDOW = FRONTEND_DIR / "lib" / "useBarWindow.ts"
TIMEFRAMES = FRONTEND_DIR / "lib" / "timeframes.ts"
TYPES_TS = FRONTEND_DIR / "lib" / "types.ts"


def _read(path: Path) -> str:
    assert path.exists(), f"expected {path} to exist"
    return path.read_text()


def _code(path: Path) -> str:
    """Source with `//` line comments stripped — for the "this must not reappear" guards, where the
    prose explaining WHY it is gone would otherwise match itself."""
    return "\n".join(re.sub(r"//.*$", "", line) for line in _read(path).splitlines())


# --- 1. the chart renders in live mode too ------------------------------------------------------


def test_cockpit_page_mounts_chart_in_all_modes():
    source = _read(PAGE_TSX)
    assert '(mode === "sim" || mode === "historical")' not in source, (
        "the sim/historical-only chart gate must be gone — the chart renders in live mode too"
    )
    assert "tapeState={snapshot?.tape_state ?? null}" in source


# --- 2. PriceChart is a container; StructureChart does the drawing ------------------------------


def test_price_chart_delegates_drawing_to_structure_chart():
    code = _code(PRICE_CHART)
    assert "<StructureChart" in code, "the cockpit must render the shared StructureChart"
    # No chart library of its own — the drawing lives in StructureChart now.
    for banned in ('import("lightweight-charts")', "lc.createChart(", ".addSeries("):
        assert banned not in code, f"PriceChart.tsx must not draw directly ({banned!r} found)"


def test_price_chart_passes_live_and_overlay_props_to_the_renderer():
    source = _read(PRICE_CHART)
    for prop in (
        "liveBars={liveBars}",
        "bands={tradabilityState.data?.bands ?? []}",
        "extraMarkers={extraMarkers}",
        "extraPriceLines={extraPriceLines}",
        'asOfLabel="start"',
    ):
        assert prop in source, f"expected the cockpit to pass {prop} to StructureChart"
    # The axis formatter is no longer a cockpit-only prop: StructureChart renders every axis on the
    # market clock unconditionally, so the cockpit must NOT be re-granted an opt-in for it (that
    # opt-in is exactly what let the two pages disagree about what a given tick meant).
    assert "clockFormatter" not in source, (
        "the ET axis is unconditional in StructureChart — the cockpit must not pass an opt-in prop"
    )


# --- 3. live "history" bars are the backend's timeframe bars (no client re-binning) -------------


def test_history_mode_uses_backend_timeframe_bars_verbatim():
    source = _read(PRICE_CHART)
    assert "fetchTimeframeHistory" in source, "history mode must read GET …/history?timeframe="
    assert "history.timeframe_bars" in source, (
        "the live history bars must be the served timeframe_bars, read verbatim"
    )
    # Tape-state markers at a coarse timeframe are placed on the SERVED containing bucket, and the
    # no-lookahead boundary is the SERVED anchor_bucket_start — the client re-buckets nothing.
    assert "bucket_ts" in source
    assert "anchor_bucket_start" in source


# --- 4. the no-lookahead clamp ------------------------------------------------------------------


def test_no_lookahead_clamp_in_container_and_hook():
    price = _read(PRICE_CHART)
    assert "beforeOnly: true" in price, "the cockpit store window must be beforeOnly (no lookahead)"
    assert "anchorBucketStart - 1" in price, (
        "the store cursor must be anchor_bucket_start - 1 so every fetched bar's ts is strictly "
        "before the replay start"
    )

    hook = _read(BAR_WINDOW)
    assert "beforeOnly" in hook, "useBarWindow must support the beforeOnly clamp"
    # Under beforeOnly the initial window issues NO forward request and never pages newer.
    assert "anchorTs === undefined || beforeOnly" in hook, (
        "beforeOnly must skip the forward (after-anchor) initial request"
    )
    assert 'direction === "newer" && beforeOnlyRef.current' in hook, (
        "beforeOnly must refuse to page forward (loadNewer no-ops)"
    )


# --- 5. StructureChart's cockpit props are optional/defaulted -----------------------------------


def test_structure_chart_cockpit_props_are_optional_with_defaults():
    source = _read(STRUCTURE_CHART)
    for decl in (
        "liveBars?: BarRow[]",
        "extraMarkers?: ChartMarkerSpec[]",
        "extraPriceLines?: ChartPriceLineSpec[]",
        "secondsVisible?: boolean",
        "asOfLabel?: string",
    ):
        assert decl in source, f"expected optional prop {decl}"
    # Defaults present so every /structure call site (which passes none of these) is byte-identical.
    for default in (
        "liveBars = []",
        "extraMarkers = []",
        "extraPriceLines = []",
        "secondsVisible = false",
        'asOfLabel = "as-of"',
    ):
        assert default in source, f"expected default {default}"
    # One clock for both pages: the axis + crosshair formatter is applied at chart creation for
    # EVERY caller, never behind a per-call-site flag. That opt-in is exactly what let the cockpit
    # render local time while /structure fell through to the library's UTC default, so the two
    # charts disagreed about what "09:30" meant.
    assert "clockFormatter" not in source, (
        "StructureChart must not carry an opt-in axis-formatter prop"
    )
    assert "tickMarkFormatter: (time: number, tickMarkType: number) =>" in source, (
        "the axis tick formatter no longer reads the library's own tick GRANULARITY -- printing "
        "the full 23-character stamp on every tick leaves a wide chart showing four labels and "
        "repeats a meaningless 00:00:00 across every daily bar"
    )
    assert "timeFormatter: (time: number) => formatDateTimeET(time * 1000)" in source, (
        "the crosshair readout no longer prints the COMPLETE market-clock stamp -- that readout is "
        "where a precise reading is asked for rather than scanned"
    )
    # Both label shapes come from the shared module. A tick that marks a day/month/year prints a
    # date; a tick inside a session prints the clock time alone. Both are ET.
    for granularity in (
        "lc.TickMarkType.TimeWithSeconds",
        "lc.TickMarkType.Time",
        "formatTimeET(time * 1000)",
        "formatDateET(time * 1000)",
    ):
        assert granularity in source, f"expected the granularity-aware axis label: {granularity}"
    # The drawing additions must not have re-introduced fitContent (the squeeze paging exists to end).
    assert "fitContent(" not in _code(STRUCTURE_CHART)


# --- 6. the two-group (Tape / History) selector ------------------------------------------------


def test_two_group_timeframe_selector_present():
    source = _read(PRICE_CHART)
    assert 'aria-label="Tape bar size"' in source, "expected the Tape (logical-second) group"
    assert 'aria-label="History timeframe"' in source, "expected the History (timeframe) group"
    assert "HISTORY_BAR_SIZES.map" in source, "the Tape group offers the logical-second sizes"
    assert "historyTimeframes.map" in source, "the History group offers the recorded timeframes"
    assert "TIMEFRAMES_WITH_LIVE_BARS" in source, (
        "the History group must intersect recorded timeframes with the backend's supported set"
    )
    # A SIM-*/unrecorded symbol shows an honest empty History group, not a fabricated timeframe.
    assert "No recorded bars for" in source


def test_history_group_is_the_fixed_duration_supported_set():
    # The frontend's supported list mirrors the backend's TIMEFRAME_SECONDS keys; 1w/1mo are absent
    # (they cannot be honestly floored into live bars). The backend 422 remains the authority.
    types = _read(TYPES_TS)
    m = re.search(r"TIMEFRAMES_WITH_LIVE_BARS\s*=\s*\[([^\]]*)\]", types)
    assert m, "expected the TIMEFRAMES_WITH_LIVE_BARS constant"
    body = m.group(1)
    for tf in ("1m", "5m", "15m", "1h", "4h", "8h", "1d"):
        assert f'"{tf}"' in body, f"expected {tf} in the live-bar timeframe set"
    for absent in ("1w", "1mo"):
        assert f'"{absent}"' not in body, f"{absent} must NOT offer live bars"


# --- 7. shared timeframe helpers (no duplicated literal) ----------------------------------------


def test_shared_timeframe_helpers_are_imported_not_duplicated():
    assert 'export const TIMEFRAME_ORDER' in _read(TIMEFRAMES), (
        "the canonical timeframe order must live in lib/timeframes.ts"
    )
    for consumer in (STRUCTURE_PAGE, PRICE_CHART):
        source = _read(consumer)
        assert '@/lib/timeframes' in source, f"{consumer.name} must import the shared helpers"
        assert "const TIMEFRAME_ORDER" not in source, (
            f"{consumer.name} must not redeclare TIMEFRAME_ORDER — it lives in lib/timeframes.ts"
        )
