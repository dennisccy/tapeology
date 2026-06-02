"""Pure projections of one ``EngineSnapshot`` into the JSON each view returns.

These functions ONLY read fields off the snapshot — they never recompute a value (anti-goal:
single source of truth). ``/summary`` and the WS stream re-expose the same snapshot fields
that ``/state`` and ``/features`` serve, so every view shows one identical engine value per
metric. The headline feature subset is read straight from the snapshot's primary window.
"""

from __future__ import annotations

from .engine.snapshot import EngineSnapshot, TradeRow

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
        "timestamp": snap.timestamp,
        "market": _market(snap),
        "tape_state": snap.tape_state,
        "confidence": snap.confidence,
        "primary_window": snap.primary_window,
        "headline_features": _headline_features(snap),
        "observations": list(snap.observations),
    }


def serialize_stream(snap: EngineSnapshot) -> dict:
    """Full live payload pushed over the WS stream — re-exposes the whole snapshot."""
    return {
        "ticker": snap.ticker,
        "scenario": snap.scenario,
        "stream_status": snap.stream_status,
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
