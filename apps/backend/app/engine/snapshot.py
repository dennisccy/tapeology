"""The single immutable per-tick engine snapshot — the one object every view reads.

There is exactly one ``EngineSnapshot`` per tick. ``/state``, ``/features``, ``/events``,
``/summary``, ``WS /stream``, and the UI all read FROM this object; none of them recompute
a value (anti-goal: single source of truth). The serializers in ``app.serializers`` are
pure projections of these fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TradeRow:
    timestamp: float
    price: float
    size: int
    side: str  # aggressor side: "buy" | "sell" | "unknown"


@dataclass(frozen=True)
class EngineSnapshot:
    ticker: str
    scenario: str
    timestamp: float            # logical timestamp of the last processed event
    event_count: int            # trades processed so far
    warm: bool                  # have we passed the warm-up floor?
    # Canonical row-6 lifecycle status, owned ONCE by the engine/feeder (never recomputed by the
    # API/UI). "connecting" (pre-open) -> "waiting" (stream open, no first event yet) -> "live"
    # (first event arrived); "stale" (delivery-gap lull, incl. a `waiting` that never got a first
    # event), "paused" (frozen, no teardown), "closed" (stopped/exhausted), "failed" (the feeder
    # raised — logged + surfaced, never swallowed). NOT part of classification (determinism holds).
    stream_status: str

    # Market (derived once in MarketState; spread = ask - bid).
    bid: float | None
    ask: float | None
    spread: float | None
    last: float | None

    # Features for every window, keyed by window label (e.g. "30s").
    features: dict[str, dict[str, float]]
    primary_window: str

    # Classification.
    tape_state: str
    confidence: float
    observations: tuple[str, ...]

    # Panels.
    recent_trades: tuple[TradeRow, ...] = field(default_factory=tuple)
    event_log: tuple[str, ...] = field(default_factory=tuple)

    # Canonical paused flag (Data Contract row 11). Owned ONCE by the engine/feeder: pause() sets
    # it (and flips stream_status to "paused"), resume() clears it (restoring the prior status).
    # REST, the WS stream, and the UI READ this — none of them guess paused. Defaulted (and placed
    # with the other defaulted fields) so every existing snapshot/test is unchanged (additive).
    paused: bool = False

    # Canonical display/epoch anchor (Data Contract row 13, J-31): the real UTC epoch (seconds)
    # that logical-time 0 maps to, so the chart renders TRUE clock time as ``anchor + logical_ts``
    # (real market time for historical/live; a synthetic session-clock for simulated). Preserved
    # ONCE by the engine/feeder (from the provider), NEVER fed into classification — it is additive
    # display metadata, so the engine stays deterministic and the same ordered stream yields
    # identical features/state/confidence. ``None`` when there is no anchor (an empty historical
    # window, or any pre-J-31 construction) — the chart then stays empty and fabricates no time.
    # Defaulted so every existing snapshot/test is unchanged (additive).
    epoch_anchor: float | None = None

    # Canonical feeder-owned DELIVERY LAG (Data Contract row 14, J-63): how far the processed tape
    # trails real time, in seconds — owned ONCE by the feeder (WatchManager), surfaced here as
    # ADDITIVE lifecycle/display metadata (the iter-9 ``end_reason`` precedent: an engine file may
    # carry feeder-owned lifecycle metadata as long as it NEVER enters classification). Per-mode
    # honest semantics: LIVE = the latest record's epoch vs wall clock (goal.md's canonical
    # definition); PACED replay (sim/historical) = the feeder's processing backlog against its OWN
    # pacing schedule (a replay deliberately hours behind wall clock is NOT "lagging"; a healthy sim
    # reads ≈0). NEVER read by features/state/confidence — the same ordered event stream yields
    # byte-identical engine outputs with or without it (determinism + observer-equivalence hold).
    # The ``tape_lag_ok`` checklist check + the future UI lag readout read THIS one value. ``None``
    # when the feeder has not stamped a lag yet (cold construction / a feeder that never sets one) —
    # an honest "no lag measured", distinct from a measured 0.0. Defaulted so every existing
    # snapshot/test is unchanged (additive).
    delivery_lag_seconds: float | None = None

    @property
    def primary_features(self) -> dict[str, float]:
        return self.features[self.primary_window]
