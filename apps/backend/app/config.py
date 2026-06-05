"""Single source of every tunable number in the engine (anti-goal: no magic numbers).

Window lengths, the large-print threshold, every classifier threshold, and every
confidence boundary live here and ONLY here. Engine and classifier code reads from a
``Config`` instance — no such literal may appear inline in those modules. Tests and the
API import the same instance so there is one source of truth for the numbers too.
"""

from __future__ import annotations

from dataclasses import dataclass


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

    # --- seller_control gate thresholds -----------------------------------------------
    # The negative mirror of the buyer gate (max_stable_spread / min_trade_speed are
    # side-neutral and shared). seller_control requires real DOWNWARD price progress, so
    # its impact cutoff is NEGATIVE — price impact, not raw aggression.
    min_aggressive_sell_ratio: float = 0.60  # share of directional volume that is sells
    max_sell_price_impact: float = -0.02     # MUST be negative: price actually fell

    # --- absorption gate thresholds (bid_absorption / ask_absorption) -----------------
    # The keystone case: high one-sided aggression but the quote HOLDS, so the matching
    # price impact is flat (NOT past the control cutoff) and the quote refreshes. The flat-
    # impact condition reuses the control cutoffs directly (bid_absorption needs
    # sell_price_impact ABOVE max_sell_price_impact; ask_absorption needs buy_price_impact
    # BELOW min_buy_price_impact) — so the absorption and control gates are mutually
    # exclusive on the impact condition and cannot both fire.
    #
    # Positive evidence the quote actually refreshed (held its level under aggression).
    # Mere absence of impact is NOT enough — absorption requires real refresh evidence, so a
    # silent/cold provider stays honest `unclear` (no fabricated absorption).
    min_bid_refresh_score: float = 0.55
    min_ask_refresh_score: float = 0.55
    # Half-width of the "price is flat" band (impact magnitude). absorption_score and the
    # absorption-confidence flatness component ramp from 1.0 at zero impact to 0.0 here.
    # Wider than the control cutoff magnitude (|0.02|) so there is a graded near-zero region.
    absorption_flat_band: float = 0.05

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
    # How far refresh above its floor earns a full absorption-confidence component (the
    # absorption confidence rewards a refreshing quote + flat impact, where the directional
    # confidence rewards impact magnitude + speed).
    refresh_scale: float = 0.45
    # The spread component is scored against ``max_stable_spread`` directly.

    # Component weights for the buyer_control confidence (must sum to 1.0).
    confidence_weights: tuple[float, float, float, float] = (0.25, 0.25, 0.25, 0.25)

    # --- Engine bookkeeping -----------------------------------------------------------
    recent_trades_limit: int = 30            # rows kept for the Recent-trades panel
    event_log_limit: int = 50                # messages kept in the Event-log panel

    # --- Price-history buffer & prediction chart (J-17 / J-18) ------------------------
    # The OHLC candle bin sizes (logical seconds) the engine accumulates concurrently and
    # the chart offers via its bar-size selector. The set of valid `?bar=` values for
    # `GET /tape/{ticker}/history` comes from HERE — an out-of-set bar is a 422 (never
    # silently coerced). No bar-size literal may appear inline in engine/serializer code.
    history_bar_sizes: tuple[int, ...] = (10, 30, 60)
    # The tape states that earn a transition MARKER on the chart. A transition INTO any of
    # these "meaningful" states is marked (with the engine's own state + confidence — never
    # recomputed); a transition into `unclear` is NOT marked. Listed here (not inline) so the
    # marker-significance rule is config-owned (no-magic anti-goal).
    history_marker_states: tuple[str, ...] = (
        "buyer_control",
        "seller_control",
        "bid_absorption",
        "ask_absorption",
    )
    # Cap on candles/markers retained PER bar size (in-memory, Phase-1). A long replay is
    # bounded so memory stays flat; the chart pans/zooms over what is retained.
    history_max_bars: int = 1000
    history_max_markers: int = 500

    # --- Real historical replay (J-11) ------------------------------------------------
    # Selectable replay speeds for a historical watch. A superset of the UI's {1,2,5,10}
    # (TopBar REPLAY_SPEEDS) so every UI choice validates; an out-of-set speed is a 422.
    allowed_replay_speeds: tuple[float, ...] = (1.0, 2.0, 5.0, 10.0)
    default_replay_speed: float = 1.0
    # Max wall-clock seconds the feeder waits between two replayed events. A large logical
    # gap in the real data (e.g. a quiet minute) is clamped to this so the cockpit never
    # stalls. Pacing is delivery-only — engine math stays purely logical/deterministic.
    replay_pacing_cap_seconds: float = 1.0

    # --- Symbol search (J-13) ---------------------------------------------------------
    symbol_search_limit: int = 20            # max suggestions returned to the search box
    symbol_search_min_query: int = 1         # below this query length => empty list (no error)

    # --- Live market-closed pre-flight gate (J-14) ------------------------------------
    # HTTP status for a live watch refused because the market is closed: the request is valid
    # but conflicts with the current market session, so 409 Conflict. The frontend keys off the
    # `reason` ("market_closed"), not this code, so 503 would be an acceptable alternative.
    market_closed_status_code: int = 409

    # --- Live streaming stale watchdog (J-12 / J-15) ----------------------------------
    # The live feeder flips the row-6 `stream_status` to `stale` when NO live event arrives
    # within this many wall-clock seconds (and back to `live` on the next event), fabricating
    # no trades during the lull. This is a *delivery-gap* timeout (a real feed lull), not an
    # engine threshold — the engine math stays purely logical/deterministic.
    stale_gap_seconds: float = 10.0

    def window_label(self, window: int) -> str:
        return f"{window}s"

    @property
    def primary_window_label(self) -> str:
        return self.window_label(self.primary_window)


# The one shared instance read by engine, classifier, API, and tests.
CONFIG = Config()
