"""Single source of every tunable number in the engine (anti-goal: no magic numbers).

Window lengths, the large-print threshold, every classifier threshold, and every
confidence boundary live here and ONLY here. Engine and classifier code reads from a
``Config`` instance — no such literal may appear inline in those modules. Tests and the
API import the same instance so there is one source of truth for the numbers too.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Config:
    # --- Rolling feature windows (logical seconds) -------------------------------------
    windows: tuple[int, ...] = (10, 30, 60, 180, 300)
    # The window the classifier reads and the UI shows as the headline readout.
    primary_window: int = 30

    # --- Large print ------------------------------------------------------------------
    # A trade whose size is >= this counts toward ``large_print_count``.
    large_print_size: int = 500

    # --- buyer_control gate thresholds ------------------------------------------------
    # All four must hold (over the primary window) before buyer_control is considered.
    min_aggressive_buy_ratio: float = 0.60   # share of directional volume that is buys
    min_buy_price_impact: float = 0.02       # MUST be positive: price impact, not aggression
    max_stable_spread: float = 0.06          # average spread at/below this counts as stable
    min_trade_speed: float = 0.50            # trades per second

    # --- Warm-up ----------------------------------------------------------------------
    # Below this many processed trades the read is an honest cold-start ``unclear``. Set so
    # the first directional call lands with comfortable margin above ``reasonable_confidence``
    # (no boundary chatter between unclear/buyer_control as the primary window fills).
    warmup_min_events: int = 40

    # --- Confidence boundaries --------------------------------------------------------
    cold_start_confidence: float = 0.10      # before warm-up
    unclear_confidence: float = 0.20         # warmed up but no clean control
    # A directional state is emitted ONLY at/above this confidence; a tentative read stays
    # `unclear` (honest-uncertainty anti-goal). It is also the J-02 "reasonable" bar, so
    # by construction `buyer_control` always implies confidence >= reasonable_confidence.
    reasonable_confidence: float = 0.60
    max_confidence: float = 0.95             # never claim certainty

    # --- Confidence margin scales -----------------------------------------------------
    # How far past a threshold a metric must read to earn a full (1.0) component score.
    ratio_scale: float = 0.40
    impact_scale: float = 0.30
    speed_scale: float = 1.50
    # The spread component is scored against ``max_stable_spread`` directly.

    # Component weights for the buyer_control confidence (must sum to 1.0).
    confidence_weights: tuple[float, float, float, float] = (0.25, 0.25, 0.25, 0.25)

    # --- Engine bookkeeping -----------------------------------------------------------
    recent_trades_limit: int = 30            # rows kept for the Recent-trades panel
    event_log_limit: int = 50                # messages kept in the Event-log panel

    def window_label(self, window: int) -> str:
        return f"{window}s"

    @property
    def primary_window_label(self) -> str:
        return self.window_label(self.primary_window)


# The one shared instance read by engine, classifier, API, and tests.
CONFIG = Config()
