"""Pure projections of one ``EngineSnapshot`` into the JSON each view returns.

These functions ONLY read fields off the snapshot — they never recompute a value (anti-goal:
single source of truth). ``/summary`` and the WS stream re-expose the same snapshot fields
that ``/state`` and ``/features`` serve, so every view shows one identical engine value per
metric. The headline feature subset is read straight from the snapshot's primary window.

``stream_status`` is passed through VERBATIM wherever it appears below (``serialize_state`` /
``serialize_summary`` / ``serialize_stream``) — one of
``connecting`` | ``waiting`` | ``live`` | ``stale`` | ``paused`` | ``closed`` | ``failed``,
owned once by the engine/feeder. The UI reads it as-is (it never adds a second status field or
guesses a status), so a connected-but-empty tape reads ``waiting`` and a feeder failure reads
``failed`` everywhere identically.
"""

from __future__ import annotations

from .config import CONFIG
from .engine.history import (
    TIMEFRAME_SECONDS,
    HistoryBuffer,
    OhlcBar,
    TapeMarker,
    TimeframeBar,
)
from .engine.snapshot import EngineSnapshot, TradeRow
from .research.feed_basis import data_feed_for_scenario

# The features the cockpit shows as headline readouts (and J-01 requires); a subset of the
# primary window's feature set — read from it, never recomputed.
HEADLINE_FEATURES = (
    "trade_speed",
    "aggressive_buy_ratio",
    "aggressive_sell_ratio",
    "net_aggressive_volume",
    "buy_price_impact",
    "sell_price_impact",
)


def _trade_row(row: TradeRow) -> dict:
    return {
        "timestamp": row.timestamp,
        "price": row.price,
        "size": row.size,
        "side": row.side,
    }


def _market(snap: EngineSnapshot) -> dict:
    return {"bid": snap.bid, "ask": snap.ask, "spread": snap.spread, "last": snap.last}


def _headline_features(snap: EngineSnapshot) -> dict:
    primary = snap.primary_features
    return {name: primary[name] for name in HEADLINE_FEATURES}


def serialize_state(snap: EngineSnapshot) -> dict:
    """Canonical tape state + confidence (`GET /tape/{ticker}/state`)."""
    return {
        "ticker": snap.ticker,
        "scenario": snap.scenario,
        "tape_state": snap.tape_state,
        "confidence": snap.confidence,
        "warm": snap.warm,
        "stream_status": snap.stream_status,
        "timestamp": snap.timestamp,
    }


def serialize_features(snap: EngineSnapshot) -> dict:
    """Canonical per-window features (`GET /tape/{ticker}/features`)."""
    return {
        "ticker": snap.ticker,
        "primary_window": snap.primary_window,
        "windows": snap.features,
    }


def serialize_events(snap: EngineSnapshot) -> dict:
    """Recent trades (with aggressor side), observations, and event log."""
    return {
        "ticker": snap.ticker,
        "recent_trades": [_trade_row(r) for r in snap.recent_trades],
        "observations": list(snap.observations),
        "event_log": list(snap.event_log),
    }


def serialize_summary(snap: EngineSnapshot) -> dict:
    """Compact headline snapshot — re-exposes /state + the headline feature subset."""
    return {
        "ticker": snap.ticker,
        "scenario": snap.scenario,
        "stream_status": snap.stream_status,
        "paused": snap.paused,
        # The current-watch FEED BASIS (Data Contract row 29, J-67) — sim | iex | sip — computed
        # ONCE server-side by the ONE consolidated scenario->data_feed mapping (config-aligned to
        # live_feed/historical_feed). Additive projection/display metadata only (the end_reason /
        # delivery_lag_seconds precedent): NEVER read by classification, never client-derived. The WS
        # frame re-exposes this SAME value verbatim (serialize_stream below), so the badge reads one
        # canonical basis identically across REST and WS — single source of truth.
        "data_feed": data_feed_for_scenario(snap.scenario, CONFIG),
        # The feeder-owned delivery lag (Data Contract row 14, J-63) — carried VERBATIM off the
        # snapshot (the engine never recomputes it; it is feeder-owned display metadata). The
        # ``tape_lag_ok`` checklist check + the future UI lag readout read this SAME value. ``None``
        # when the feeder has not stamped one yet (cold/sim construction) — honest absence, not 0.0.
        "delivery_lag_seconds": snap.delivery_lag_seconds,
        "timestamp": snap.timestamp,
        "market": _market(snap),
        "tape_state": snap.tape_state,
        "confidence": snap.confidence,
        "primary_window": snap.primary_window,
        "headline_features": _headline_features(snap),
        "observations": list(snap.observations),
    }


def _ohlc_bar(bar: OhlcBar) -> dict:
    return {
        "time": bar.start,
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
    }


def _tape_marker(marker: TapeMarker) -> dict:
    return {
        "time": marker.timestamp,
        "state": marker.state,
        "confidence": marker.confidence,
    }


def serialize_history(
    history: HistoryBuffer, bar: int, epoch_anchor: float | None = None
) -> dict:
    """Price history for the chart (`GET /tape/{ticker}/history?bar=`): OHLC bars + markers.

    A pure projection of the engine's history buffer for the requested (already-validated) bar
    size — it reads candles/markers the engine computed once and recomputes nothing (one focused
    chart, computed once). An empty buffer yields empty lists (HTTP 200) — never invented candles.

    ``epoch_anchor`` (Data Contract row 13, J-31) is the engine's canonical display anchor — the
    real UTC epoch that logical-time 0 maps to — carried through VERBATIM so the chart can render
    TRUE clock time as ``epoch_anchor + bar.time`` (a pure additive offset). Bar/marker ``time``
    stay LOGICAL (the engine's single-source timeline); the chart applies the anchor. ``None`` when
    there is no anchor (an empty/anchorless window) — the chart then fabricates no timestamps.
    """
    return {
        "bar": bar,
        "epoch_anchor": epoch_anchor,
        "bars": [_ohlc_bar(b) for b in history.bars(bar)],
        "markers": [_tape_marker(m) for m in history.markers()],
    }


def _timeframe_bar(bar: TimeframeBar) -> dict:
    return {
        "ts": bar.ts,
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
        "volume": bar.volume,
    }


def serialize_timeframe_history(
    history: HistoryBuffer, timeframe: str, epoch_anchor: float | None = None
) -> dict:
    """Wall-clock timeframe history for the cockpit chart's "history" mode
    (`GET /tape/{ticker}/history?timeframe=`): real-epoch OHLC+volume candles + tape-state markers.

    A pure projection of the engine's history buffer for the requested (already-validated)
    timeframe — it reads candles/markers the engine computed once and recomputes nothing (single
    source of truth). Additive alongside ``serialize_history`` (the logical-second ``?bar=`` mode),
    which is unchanged. An anchorless engine yields empty ``timeframe_bars`` and a null
    ``anchor_bucket_start`` (HTTP 200) — never invented candles.

    Fields:
      * ``timeframe`` / ``timeframe_seconds`` — the requested timeframe and its bucket width.
      * ``epoch_anchor`` (row 13) — carried through verbatim; the ``ts`` are already real epochs.
      * ``anchor_bucket_start`` — the real-epoch left edge of the anchor's bucket (``None`` when
        anchorless). The NO-LOOKAHEAD boundary: the chart draws recorded store bars strictly before
        it and the live tape's own moving bars from it onward.
      * ``timeframe_bars`` — the real-epoch OHLC+volume candles built live from the tape.
      * ``markers`` — the SAME meaningful tape-state-transition markers as the ``?bar=`` mode, each
        additionally carrying ``bucket_ts`` (the real-epoch left edge of the timeframe bucket that
        contains the marker, ``None`` when anchorless) so the chart places a marker on its
        containing candle at a coarse timeframe without recomputing the bucketing itself.
    """
    secs = TIMEFRAME_SECONDS[timeframe]
    anchor_bucket = history.anchor_bucket_start(timeframe)

    def _bucket_ts(logical: float) -> float | None:
        if epoch_anchor is None:
            return None
        return ((epoch_anchor + logical) // secs) * secs

    return {
        "timeframe": timeframe,
        "timeframe_seconds": secs,
        "epoch_anchor": epoch_anchor,
        "anchor_bucket_start": anchor_bucket,
        "timeframe_bars": [_timeframe_bar(b) for b in history.timeframe_bars(timeframe)],
        "markers": [
            {**_tape_marker(m), "bucket_ts": _bucket_ts(m.timestamp)}
            for m in history.markers()
        ],
    }


def serialize_stream(snap: EngineSnapshot) -> dict:
    """Full live payload pushed over the WS stream — re-exposes the whole snapshot."""
    return {
        "ticker": snap.ticker,
        "scenario": snap.scenario,
        "stream_status": snap.stream_status,
        "paused": snap.paused,
        # The current-watch FEED BASIS (Data Contract row 29, J-67) — re-exposed VERBATIM off the
        # SAME single mapping the ``/summary`` projection uses, so the WS frame and ``/summary`` serve
        # one identical basis (single source of truth; the badge never client-derives it).
        "data_feed": data_feed_for_scenario(snap.scenario, CONFIG),
        # The feeder-owned delivery lag (Data Contract row 14, J-63) — carried VERBATIM off the
        # snapshot so the WS frame and ``/summary`` serve the SAME single value (single source of
        # truth). ``None`` until the feeder stamps one. The ``tape_lag_ok`` check reads this value.
        "delivery_lag_seconds": snap.delivery_lag_seconds,
        "warm": snap.warm,
        "timestamp": snap.timestamp,
        "market": _market(snap),
        "tape_state": snap.tape_state,
        "confidence": snap.confidence,
        "primary_window": snap.primary_window,
        "features": snap.features,
        "headline_features": _headline_features(snap),
        "observations": list(snap.observations),
        "event_log": list(snap.event_log),
        "recent_trades": [_trade_row(r) for r in snap.recent_trades],
    }
