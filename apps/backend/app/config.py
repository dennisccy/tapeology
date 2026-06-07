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

    # --- Per-call vendor timeout (J-22 / no-unbounded-waits anti-goal) ----------------
    # The hard wall-clock bound for a SINGLE outbound vendor request that gates a Watch
    # (the historical-window fetch in `_watch_historical` and the market-clock pre-flight in
    # `_watch_live`). Each such `asyncio.to_thread(...)` call runs under
    # `asyncio.wait_for(..., timeout=vendor_call_timeout_seconds)`; on expiry the Watch is
    # refused with an explicit `provider_timeout` error and NO engine is created (no tape is
    # fabricated). This is the OUTER `wait_for` BACKSTOP — it abandons the worker thread but does
    # not stop the underlying call; the real call-level deadline below is what actually cuts the
    # vendor request off. It is a PRE-connection per-request bound and is DISTINCT from
    # `stale_gap_seconds` (a mid-stream delivery-gap watchdog) — the two MUST NOT be conflated.
    vendor_call_timeout_seconds: float = 8.0

    # --- Real call-level vendor HTTP deadline (J-28 / bounded-honest-vendor-calls anti-goal) --
    # The TRUE call-level deadline applied at the vendor-call boundary — a real HTTP timeout on
    # the SDK client's underlying `requests.Session` (set inside the one vendor adapter; that SDK
    # exposes no per-request `timeout` kwarg). A slow/large/CPU-bound vendor response is cut off
    # by the client ITSELF (surfacing as a distinct timeout the adapter maps to the neutral
    # `provider_timeout`), not merely abandoned by the outer `wait_for` wrapper (which leaves the
    # worker thread running). It is the (requests connect, read) timeout in seconds.
    #
    # ORDERING INVARIANT (J-28, asserted by a unit test from config, never hardcoded):
    #   vendor_http_timeout_seconds  <=  vendor_call_timeout_seconds   (HTTP deadline <= wrapper)
    #   vendor_call_timeout_seconds  <   WATCH_REQUEST_TIMEOUT_MS / 1000  (backend < frontend)
    # i.e. the backend-effective bound (the HTTP deadline, bounded above by the wrapper) is
    # strictly shorter than the frontend client timeout (12000ms in apps/frontend/lib/config.ts),
    # so the user ALWAYS sees the backend's honest, distinct error rather than a client-side
    # give-up. Do NOT raise these to "fix" a slow window — J-29 is fast BY DESIGN, not by a longer
    # deadline. The frontend constant is mirrored here ONLY to make the ordering invariant testable
    # in-process; the live value lives in `apps/frontend/lib/config.ts`.
    vendor_http_timeout_seconds: float = 6.0
    frontend_watch_request_timeout_ms: int = 12000

    # --- Historical-window fetch cache (J-29 / fast-by-design) -------------------------
    # A bounded in-process cache of fetched REAL historical windows keyed by (symbol, start, end,
    # feed) so re-watching the same symbol+window is near-instant (a cache hit skips the vendor
    # round-trip entirely and replays the SAME real `HistoricalWindow` — never a fabricated one).
    # Bounded so memory stays flat: at most this many windows, each evicted after this many
    # wall-clock seconds (LRU + TTL). A miss behaves exactly as before (one real fetch). These are
    # operational cache bounds, not engine thresholds — the engine math stays untouched.
    historical_cache_max_entries: int = 32
    historical_cache_ttl_seconds: float = 300.0

    # --- Historical warm-up fast-forward (J-29 / prompt warm-up) -----------------------
    # On a historical replay the feeder delivers the first up-to-`warmup_min_events` warm-up events
    # with this (tiny) wall-clock pace instead of their logical inter-event gaps, then resumes
    # normal `_feed_paced` pacing — so the cockpit shows a WARM read quickly rather than waiting out
    # the real timeline of the warm-up window. This is DELIVERY PACING ONLY: the fast-forwarded
    # events still enter the engine in the same order with their same logical timestamps, so the
    # resulting features/state/confidence are IDENTICAL to an un-fast-forwarded replay (determinism
    # preserved — asserted by a unit test). It is NOT an engine threshold.
    warmup_fast_forward_pace_seconds: float = 0.0

    # --- Symbol-universe background warm/refresh (J-30 / warmed search) ----------------
    # The tradable-symbol universe is warmed once at FastAPI startup (in the background, via the
    # neutral adapter seam — no-creds => a no-op, search stays []) so the FIRST search after a
    # (re)start is not a multi-second stall. Optionally refreshed in the background this often;
    # `0` (the default) disables the periodic refresh (the one-time startup warm alone satisfies
    # "not a multi-second stall"). This is an operational cache-refresh cadence, not an engine
    # threshold.
    symbol_universe_refresh_seconds: float = 0.0

    # --- Live streaming stale watchdog (J-12 / J-15) ----------------------------------
    # The live feeder flips the row-6 `stream_status` to `stale` when NO live event arrives
    # within this many wall-clock seconds (and back to `live` on the next event), fabricating
    # no trades during the lull. This is a *delivery-gap* timeout (a real feed lull), not an
    # engine threshold — the engine math stays purely logical/deterministic.
    stale_gap_seconds: float = 10.0

    # --- Pause/resume feeder freeze (J-19) --------------------------------------------
    # While a watch is paused the feeder stops *applying* events without cancelling its task or
    # closing a live socket. The paced (sim/historical) feeders poll this many wall-clock seconds
    # between checks of the engine's paused flag so they freeze in place (consuming nothing) and
    # resume exactly where they left off — no fabricated catch-up. This is a *delivery* poll
    # cadence (wall-clock), never an engine threshold; the engine math stays logical/deterministic.
    pause_poll_seconds: float = 0.02

    def window_label(self, window: int) -> str:
        return f"{window}s"

    @property
    def primary_window_label(self) -> str:
        return self.window_label(self.primary_window)


# The one shared instance read by engine, classifier, API, and tests.
CONFIG = Config()
