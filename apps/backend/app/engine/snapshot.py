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
    stream_status: str          # "connecting" | "live" | "stale" | "paused" | "closed"

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

    @property
    def primary_features(self) -> dict[str, float]:
        return self.features[self.primary_window]
