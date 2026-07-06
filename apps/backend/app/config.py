"""Single source of every tunable number in the engine (anti-goal: no magic numbers).

Window lengths, the large-print threshold, every classifier threshold, and every
confidence boundary live here and ONLY here. Engine and classifier code reads from a
``Config`` instance — no such literal may appear inline in those modules. Tests and the
API import the same instance so there is one source of truth for the numbers too.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

# The ONE registered strategy id (era-3 capability 3, J-03). Data Contract row 34: the complete
# v1 strategy definition is config-owned — ``Config.strategy_definition(STRATEGY_V1_ID)`` below is
# its single owner, read by the backtest runner and echoed verbatim into every report's
# provenance. Any other strategy id is honestly refused (422 at the route) until a later journey
# registers more; strategy VARIANT enumeration is J-07 sweep territory, deliberately not here.
STRATEGY_V1_ID = "v1"

# The frozen legacy profile (era-3 capability 2, J-06; Data Contract row 33) — the SAME
# "id constant + Config-owned definition method" pattern as STRATEGY_V1_ID above governs both the
# strategy grammar (row 34, ``strategy_definition``) and the profile registry (row 33,
# ``profile_definition`` / ``profile_registry`` below). Moved here from
# ``app/research/backtests.py`` (its historical home, which never actually read it — only
# re-exported it); ``app.research.backtests`` re-exports it still, so existing importers are
# unaffected. Every archived-era surface and the live cockpit run on THIS profile only, forever
# (the byte-equivalence anti-goal).
PROFILE_DEFAULT = "default"

# THE FIRST additive candidate profile (J-06) — proves the versioned-profile mechanism. Registered
# beside ``PROFILE_DEFAULT``, selectable ONLY by an explicit backtest run's ``profile`` param
# (never by the live cockpit or any archived-era surface — enforced by
# ``tests/test_profile_equivalence.py``'s source-scan guard). See ``Config.profile_definition``
# for its ONE declared additive override.
PROFILE_CANDIDATE_FASTER_WARMUP = "candidate-faster-warmup"

# Registration order for the registry projection (``Config.profile_registry``) — private: external
# callers go through ``profile_definition`` (single lookup) or ``profile_registry`` (the full
# list), never this tuple directly.
_PROFILE_IDS_IN_ORDER: tuple[str, ...] = (PROFILE_DEFAULT, PROFILE_CANDIDATE_FASTER_WARMUP)


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

    # --- RELATIVE spread / price-impact gates (J-33 / price-impact-relative-to-price) ----------
    # The directional/absorption gates judge the "wide spread" and "clean price impact" tests
    # RELATIVE to the instrument's price level (spread in basis points of price; impact as a
    # RETURN), NOT via the absolute dollar constants above — which were calibrated for the ~$100
    # simulator and forced a real ~$30–50 name with a proportionate spread to `unclear`. The
    # classifier reads the canonical ``reference_price`` feature (computed once in the feature
    # engine) and applies these when a basis is present; with NO basis (legacy unit-test fixtures
    # that pass no reference_price) it falls back to the absolute constants above, so the existing
    # classifier tests are byte-identical (the absolute path is unchanged).
    #
    # EQUIVALENCE / SIM SANITY (the relative path must keep all five sim scenarios green):
    #   * sim control/absorption: price ~$100, spread $0.02 = 2 bps  (well under max_stable_spread_bps)
    #   * sim chop:               price ~$100, spread $0.10–$0.20 = 10–20 bps — but chop is blocked
    #                             by the RATIO floor regardless, so the bps cutoff is generous enough
    #                             to admit a real fast-mover's proportionate spread without ever
    #                             admitting chop (whose one-sided ratios never reach 0.60).
    # max_stable_spread_bps is deliberately generous so a genuine ~$30–50 fast-mover with a
    # proportionate (even absolute-$-wide) spread is NOT forced to `unclear`; a genuinely wide
    # RELATIVE spread (e.g. > this many bps) still blocks control/absorption (honest-uncertainty
    # holds). The impact-return cutoffs are the relative mirrors of min_buy/max_sell_price_impact:
    # at $100 the old $0.02 cutoff is 2 bps of return (0.0002), so these keep the sim equivalence
    # while expressing the cutoff as a return that scales to any price level.
    max_stable_spread_bps: float = 30.0          # average spread (bps of mid/last) at/below = stable
    min_buy_price_impact_return: float = 0.0002  # MUST be positive: real upward progress (a return)
    max_sell_price_impact_return: float = -0.0002  # MUST be negative: real downward progress
    # Half-width of the relative "price is flat" band (impact magnitude as a return). The absorption
    # gates use the EXACT complement of the control impact-return condition, so control and
    # absorption stay mutually exclusive on impact (the keystone) in the relative domain too. Wider
    # than the control return cutoff (|0.0002|) so there is a graded near-zero region (mirrors the
    # absolute absorption_flat_band's relation to max_sell_price_impact).
    absorption_flat_band_return: float = 0.0005
    # How far past the relative impact-return cutoff a metric must read to earn a full (1.0)
    # confidence component (the relative mirror of impact_scale). At $100 a $0.40 impact is a 0.004
    # return, comfortably past this — so sim confidence stays well above reasonable_confidence.
    impact_return_scale: float = 0.003

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

    # --- Directional override: spread is a GRADED factor, not an absolute veto (J-36) -----------
    # On REAL data a momentarily wide or absent/crossed QUOTED spread (a single-venue IEX quote, or
    # the suppressed/crossed quotes around an LULD trading halt) must NOT by itself veto a move that
    # is otherwise CLEARLY directional. The directional gates above apply ``spread_metric <= max_spread``
    # as a hard AND-term, so on the GME 14-05-2024 open drop a ~2,700-bps single-venue quote killed a
    # move whose sell-ratio (0.77), negative impact (−4.79), and speed (1.5) all clearly passed —
    # forcing a perpetual ``unclear`` through an obvious >10% drop. The fix:
    #   * historical fetch uses the SIP consolidated feed (config ``historical_feed`` below) so the
    #     quoted spread is realistic the vast majority of the time; AND
    #   * when a move is CLEARLY DIRECTIONAL — ratio >= floor AND |relative price impact| past its
    #     cutoff AND speed >= floor (the EXISTING control predicate MINUS the spread term) — it
    #     resolves to control even when the quoted spread is wide/absent, with the spread entering
    #     ONLY through a GRADED confidence factor (never as a veto).
    # The override engages ONLY for that clearly-directional case and is ADDITIVE: a genuinely wide
    # RELATIVE spread on weak/mixed tape (J-06 / J-33) and high aggression with no proportionate
    # price progress (absorption, J-04/J-05) are unchanged — they never satisfy the override predicate
    # (weak ratio / flat impact / low speed), so honest-uncertainty and price-impact-over-aggression
    # hold. The absorption gates remain the EXACT complement of the control impact condition.
    #
    # ``directional_override_enabled`` gates the whole behaviour (a single switch for the keystone
    # test to prove the pre-override fixtures stay byte-identical when False). The override's
    # ratio/impact/speed floors REUSE the existing control floors (min_aggressive_*_ratio,
    # min_buy/max_sell_price_impact[_return], min_trade_speed) — it adds NO second set of magic
    # numbers; only the bounded graded-spread band below is new.
    directional_override_enabled: bool = True
    # THE OVERRIDE BAND (the artifact-vs-illiquid boundary). The override engages only while the
    # spread is at most ``override_max_spread_multiple`` × the stable-spread cap — i.e. a spread that
    # is moderately-to-very wide (a single-venue / fast-mover / momentarily-halted QUOTE around a
    # real directional move), but NOT a spread so wide it signals genuinely illiquid / mixed tape.
    # Beyond this multiple the spread STILL VETOES control (honest-uncertainty holds: a genuinely
    # wide *relative* spread on mixed tape reads ``unclear``). Calibrated from real SIP data:
    #   * the GME 14-05-2024 open-drop window quotes ~28–44 bps avg on SIP (≈1–1.5× the 30-bps cap)
    #     — well inside the band, so the clear >10% drop resolves to seller_control; while
    #   * the honest-uncertainty guards (250 bps ≈ 8× the cap; $0.50 ≈ 8× the $0.06 absolute cap)
    #     are OUTSIDE the band, so genuinely-wide-relative tape still reads unclear.
    # A 4× multiple cleanly separates the two (real ~1.5× admitted, guard ~8× still vetoed). Scales to
    # either metric domain (bps when a price basis exists, dollars otherwise) since it multiplies the
    # active cap.
    override_max_spread_multiple: float = 4.0
    # Inside the band the spread is a GRADED confidence factor, never a veto: at/under the cap it
    # scores 1.0 (no change to the in-gate confidence); at the band edge (``override_max_spread_multiple``
    # × cap) it scores this floor; in between it decays LINEARLY. The floor is high enough that a
    # clearly-directional move with a wide-but-in-band spread still earns confidence >=
    # ``reasonable_confidence`` (so the move is called), while a wider in-band spread still LOWERS
    # confidence (graded, honest) — never asserting false certainty.
    override_spread_floor_score: float = 0.50

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

    # --- Canonical display/epoch anchor for SIMULATED data (J-31, Data Contract row 13) ------
    # The chart's time axis shows TRUE clock time via an ADDITIVE epoch anchor: the real UTC epoch
    # that logical-time 0 maps to (true_clock = anchor + logical_ts). For historical/live the
    # anchor is the first real record's UTC epoch (computed in the provider). For SIMULATED data
    # there is no real epoch, so the synthetic session-clock is anchored to this config-owned
    # synthetic session-start instant — a fixed UTC epoch (seconds) corresponding to
    # 2024-01-02 09:30:00 America/New_York (US RTH open, EST -05:00 = 14:30:00Z), a real clock
    # face rather than an elapsed 0…600 s counter. It is DISPLAY metadata only — it never enters
    # classification, so the engine stays deterministic (no wall-clock in the engine math). A fixed
    # constant (not wall-clock now()) keeps the simulated axis reproducible. No inline literal may
    # appear in engine/provider code — it lives ONLY here.
    sim_session_anchor_epoch: float = 1704205800.0  # 2024-01-02T14:30:00Z (09:30 ET, EST)

    # --- Real historical replay (J-11) ------------------------------------------------
    # Selectable replay speeds for a historical watch. A superset of the UI's {1,2,5,10}
    # (TopBar REPLAY_SPEEDS) so every UI choice validates; an out-of-set speed is a 422.
    allowed_replay_speeds: tuple[float, ...] = (1.0, 2.0, 5.0, 10.0)
    default_replay_speed: float = 1.0

    # --- Per-mode vendor market-data feed (J-36) --------------------------------------
    # The feed each REAL mode reads, config-owned and read ONLY inside the one vendor adapter (no
    # vendor enum leaks outward). HISTORICAL replay uses the SIP consolidated feed — realistic
    # spreads, free for data >15 min old — so a real directional move is judged against a real
    # quoted spread rather than a wide single-venue IEX quote (the J-36 root cause). LIVE streaming
    # stays on the free IEX feed by design (out of scope to change). The vendor's feed-override env
    # var still takes precedence inside the adapter (it forces BOTH modes to the named feed) so an
    # operator can pin a feed for testing; with no override these per-mode defaults apply. These are
    # vendor-neutral feed NAMES (strings), not the vendor's feed enum — the adapter maps the name
    # to its enum internally, so no vendor type appears here.
    historical_feed: str = "sip"
    live_feed: str = "iex"

    # --- Progressive long-window load: displayed-series caps (J-37) -------------------
    # A long/dense Full-RTH window can carry tens of thousands of real prints. The engine still bins
    # EVERY real print on its deterministic logical timeline (tape state + features stay single-source
    # and exact — nothing is dropped from the computation), but the DISPLAYED recent-trades and chart
    # series are already bounded (``recent_trades_limit`` / ``history_max_bars`` / ``history_max_markers``)
    # so memory stays flat regardless of window size. The progressive-fetch first-chunk budget (the
    # wall-clock the backend may spend fetching the FIRST sub-window before replay begins) is bounded
    # by the existing vendor-call deadlines (``vendor_http_timeout_seconds`` / ``vendor_call_timeout_seconds``),
    # which stay shorter than the frontend timeout — so time-to-first-data is decoupled from total
    # window load without a new magic number. The maximum number of background sub-window chunks
    # fetched concurrently while replay is already running reuses ``historical_chunk_max_concurrency``.
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

    # --- Chunked long-window historical fetch (J-34 / fast-by-design, not a longer timeout) ----
    # A long requested window (up to a full trading day) is split into BOUNDED sub-windows fetched
    # with BOUNDED concurrency and stitched back in epoch order into ONE real window — parallelizing
    # the vendor SDK's otherwise-sequential pagination so the advertised Full-RTH quick-pick loads
    # for a liquid symbol instead of returning the "very high-volume" error. Both bounds are
    # config-owned (no magic number): a window longer than the sub-window size is split into
    # ceil(span / chunk) sub-windows, at most ``historical_chunk_max_concurrency`` fetched at once.
    # A window at/under the sub-window size is fetched as a SINGLE call (the prior fast path,
    # unchanged). Stitching merges the sub-windows' real trades/quotes and sorts by epoch —
    # it MUST NOT fabricate, drop, reorder (beyond the canonical epoch sort), or de-duplicate real
    # prints; a re-watch of the same symbol+window stays near-instant from the window cache. This is
    # fast BY DESIGN (concurrency), never a relaxed deadline — the backend bound stays shorter than
    # the frontend client timeout; a window genuinely too large to load within budget still resolves
    # to the actionable "shorter range" backstop (J-28).
    historical_chunk_seconds: float = 900.0       # sub-window span (15 min) — split above this
    historical_chunk_max_concurrency: int = 4     # max sub-window fetches in flight at once

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

    # --- Research evolution: journal store + fingerprint (capabilities 23 / 28) ---------------
    # The journal-scoped SQLite store's DB path. It is ONLY a default here — the operator overrides
    # it with the ``TAPEOLOGY_JOURNAL_DB`` env var (read in ``journal_db_path`` below) and tests
    # inject a per-test temp path via the existing dependency-override pattern (``get_journal_store``
    # in main.py). ``":memory:"`` is a valid value for a hermetic in-process store. Persistence is
    # SCOPED to research records (theses, verdict events, hints, actions, studies) — NO tape data is
    # ever written here (committed test fixtures excepted).
    journal_db_path: str = "tapeology_journal.db"
    # SQLite busy timeout (milliseconds) applied on every connection (capability 28 discipline):
    # under WAL with a single writer queue, a reader that briefly contends waits up to this long
    # rather than failing immediately. Operational store tuning, never an engine threshold.
    journal_busy_timeout_ms: int = 5000
    # The CURRENT journal schema version the store migrates UP to on open (capability 28). Stamped in
    # the ``schema_version`` table at creation, and the target of the versioned on-open migration: a
    # store opened against an older DB runs each pending step inside one ``BEGIN IMMEDIATE`` writer
    # transaction until the stored version equals this. Bump (and add the matching migration step in
    # ``store._migrate``) whenever the schema changes.
    #   v1 → v2: ``verdict_events`` gains ``rule_first_true_ts`` / ``rule_first_true_price`` (the
    #            capability-24 dwell timing record), added by ``ALTER TABLE`` and never backfilled
    #            (the append-only timeline keeps old rows' values ``NULL``).
    #   v2 → v3: ``actions`` gains ``spread_at_mark`` (the J-52 action-mark spread, a moment value
    #            taken once from the snapshot at recording), added by ``ALTER TABLE`` and never
    #            backfilled (any pre-existing action row keeps ``NULL`` — never recomputed).
    #   v3 → v4: ``theses`` gains ``risk_flags`` (the J-49 capability-26 entry risk flags, computed
    #            once at declaration and frozen on the thesis), added by ``ALTER TABLE`` and never
    #            backfilled (a pre-migration thesis keeps ``NULL`` — it was never risk-assessed, so its
    #            projection OMITS the ``risk_flags`` key entirely rather than read a dishonest empty
    #            list).
    #   v4 → v5: ``theses`` gains ``execution_checks`` (the J-54 capability-27 machine-derived
    #            execution checks + their suggested mistake tags, computed ONCE at terminal resolution
    #            from the recorded marks + the append-only timeline + the frozen thesis fields), added
    #            by ``ALTER TABLE`` and never backfilled (a pre-migration RESOLVED thesis keeps
    #            ``NULL`` — its checks were never computed, so the journal detail OMITS the
    #            ``execution_checks`` key rather than fabricate a pass/fail at read).
    #   v5 → v6: ``theses`` gains the J-55/J-56/J-57 review-pillar columns IN ONE BUMP —
    #            ``statement_final_statuses`` (per-statement FINAL statuses persisted ONCE at terminal
    #            resolution, J-55), ``grades`` (the outcome × process grade computed ONCE at resolution,
    #            J-56), and ``review_tags`` / ``review_note`` / ``reviewed`` (the user-confirmed review
    #            saved by ``POST …/review``, J-57). All added by ``ALTER TABLE`` and never backfilled (a
    #            pre-migration RESOLVED thesis keeps ``NULL`` for each — its statuses/grades were never
    #            computed and it was never reviewed, so the journal detail OMITS each key rather than
    #            fabricate a value at read).
    #   v6 → v7: ``theses`` gains ONE additive ``excursions`` column — the per-horizon excursion record
    #            (capability 30, J-58) computed ONCE at the terminal resolution / stream-end and stored
    #            verbatim. Added by ``ALTER TABLE`` and never backfilled (a pre-v7 RESOLVED thesis keeps
    #            ``NULL`` — its excursions were never measured, so the journal detail OMITS the key
    #            rather than fabricate numbers at read).
    #   v7 → v8: NEW ``backtests`` table (era-3 capability 4, J-03) in the payload-blob shape the
    #            ``studies`` table proved (id, payload, created_wall_ts). Created by the migration
    #            (``CREATE TABLE IF NOT EXISTS`` — idempotent by construction) and arriving EMPTY:
    #            a migration never fabricates a backtest report, and no existing table or row is
    #            touched by this step.
    #   v8 → v9: NEW ``pnl_ledger`` table (era-3 capability 5, J-04; Data Contract row 32) in the
    #            payload-blob shape with the ENHANCEMENT id as the primary key (one honest row per
    #            enhancement — uniqueness is structural). Created by the migration
    #            (``CREATE TABLE IF NOT EXISTS`` — idempotent by construction) and arriving EMPTY:
    #            a migration never fabricates a ledger row, and no existing table or row is touched
    #            by this step.
    #   v9 → v10: NEW ``champion_pointer`` table (era-3 capability 7, J-07; Data Contract row 33) —
    #             a SINGLETON row (id=1) holding the ONE persisted, movable champion pointer that
    #             replaces the retired hardcoded ``{STRATEGY_V1_ID, PROFILE_DEFAULT}`` constant.
    #             Created by the migration (``CREATE TABLE IF NOT EXISTS`` — idempotent by
    #             construction) and arriving EMPTY; seeded to the founding ``v1``/``default`` pair
    #             by ``JournalStore._ensure_champion_pointer_seeded`` UNCONDITIONALLY on every open
    #             (fresh-create included — a fresh DB is already at the target version, so this
    #             version-gated step never runs for it) — never inside this gated step, so a DB
    #             migrated straight from an old snapshot seeds too, exactly once.
    # Excluded from ``config_fingerprint`` (see the exclusion set below): a migration must NOT change
    # the fingerprint — verdicts depend on classifier thresholds, never on where/how the DB is stored.
    journal_schema_version: int = 10

    # --- Profit-research era: HISTORICAL TAPE DATASET STORE directory (capability 1, J-02) ------
    # Where the dataset store persists explicitly recorded historical tape (one JSON file per
    # dataset). It is ONLY a default here — the operator overrides it with the
    # ``TAPEOLOGY_DATASET_DIR`` env var (read in ``dataset_dir_resolved`` below, the
    # ``TAPEOLOGY_JOURNAL_DB`` pattern) and tests point it at a temp dir the same way. The default
    # is package-anchored (``apps/backend/.data/datasets/``, covered by the repo's ``.data/``
    # gitignore entry) so it resolves identically whatever the process cwd is. Persistence is
    # SCOPED: this dir holds explicitly recorded research datasets ONLY — the live cockpit's tape
    # is NEVER written here (recording is an explicit research action, never ambient).
    #
    # EXCLUDED FROM ``config_fingerprint`` (see the exclusion set in ``config_fingerprint``) with
    # the ``journal_db_path`` discipline: WHERE datasets are stored cannot affect any persisted
    # research value, so two journals identical in every threshold but storing datasets in
    # different directories (or on different machines — the default embeds an absolute path) MUST
    # share a fingerprint. Pinned by a fingerprint-stability test + the real-threshold counter-test
    # (``tests/test_datasets.py``).
    dataset_dir: str = str(Path(__file__).resolve().parents[1] / ".data" / "datasets")

    # --- Research evolution: verdict-transition engine (capability 24) -------------------------
    # RESEARCH DEFAULTS — a starting point calibrated against the deterministic sims, NEVER a
    # validated edge (the goal doc's Research-config-defaults constraint: every research value lives
    # in config with its sim calibration documented; no literal in research code). These enter the
    # ``config_fingerprint`` automatically (it hashes the entire frozen config), so a verdict timeline
    # is never silently compared across different verdict timings.
    #
    # PER-SETUP VERDICT DWELL (LOGICAL seconds): how long the raw verdict rule must hold CONTINUOUSLY
    # (in logical time, restarting at thesis creation) before the verdict is PUBLISHED — so a single
    # flickering tick never publishes a transition and confirmation is always backed by sustained
    # post-declaration evidence. Calibrated against the sim phase lengths: SIM-BUYER/SIM-REVERSAL's
    # control phase and SIM-REVERSAL's absorption phase each run well past 30s logical once settled
    # (the classifier's 30s primary window), so a 3.0s dwell publishes comfortably INSIDE the phase
    # while still demanding several consecutive confirming ticks (at the 0.5s sim tick that is ~6
    # ticks). Keyed per setup so a slower-to-trust setup can carry a longer dwell without a magic
    # number anywhere else; all four share the same default here (one documented starting point).
    verdict_dwell_seconds: dict = field(
        default_factory=lambda: {
            "absorption_reversal": 3.0,
            "trend_continuation": 3.0,
            "level_break": 3.0,
            "failed_move_fade": 3.0,
        }
    )
    # INVALIDATION ε (a spread multiple): a single print beyond the declared invalidation by AT LEAST
    # this many TIMES the current spread is a hard, dwell-exempt invalidation — far enough past the
    # level that one genuinely-bad print (a fat-finger inside the guard) does NOT trip it. The guard
    # band is ``epsilon × spread`` on the wrong side of the invalidation. Calibrated so the sim's
    # $0.02 spread yields a ~$0.03 band: a print $0.04+ through the level invalidates immediately,
    # while a lone print $0.02 through it (inside the band) does not. A spread multiple (not a dollar
    # figure) so it scales to any instrument's price/liquidity (the no-magic-numbers discipline).
    invalidation_epsilon_spread_multiple: float = 1.5
    # k CONSECUTIVE prints beyond the invalidation (INSIDE the ε guard band) that together invalidate:
    # a sustained leak through the level — not a single ≥ε breach, not a lone bad print — is itself
    # decisive. ``k`` consecutive prints on the wrong side (each by any margin > 0) auto-resolve the
    # thesis. Keeps a slow drift through the level honest without waiting for one big ≥ε print.
    invalidation_k_consecutive: int = 3
    # The append-only verdict timeline is capped at this many PUBLISHED rows per thesis (the oldest
    # are pruned on append once the cap is exceeded). A safety bound on an unbounded live watch — a
    # generous default since transitions are rare (dwell-gated). Capacity bound only; the surviving
    # rows are never edited (append-only at the repository level holds — pruning is the store's own
    # capacity management, distinct from any update/delete of a retained row, which does not exist).
    verdict_timeline_cap: int = 500

    # --- Research evolution: MANAGEMENT-STANCE DWELL (capability 27, J-53; data-contract row 25) ----
    # RESEARCH DEFAULT — a starting point calibrated against the deterministic sims, NEVER a validated
    # edge (the goal doc's Research-config-defaults constraint: every research value lives in config
    # with its sim calibration documented; no literal in research code). The holding-period MANAGEMENT
    # STANCE (``thesis_intact | thesis_weakening | thesis_invalidated``) is a pure derivation from the
    # latest PUBLISHED verdict; it publishes through THIS config-owned, LOGICAL-time dwell so a single
    # flickering verdict tick never flaps the stance — EXCEPT ``thesis_invalidated``, which is
    # dwell-exempt (it mirrors the hard, dwell-exempt invalidation trigger and is terminal). Calibrated
    # to the SAME 3.0 s the per-setup verdict dwell uses (the verdict it reads is already dwell-gated,
    # so a SHORT additional stance dwell suffices to absorb a one-tick verdict flicker without lagging
    # the user's read; at the 0.5 s sim tick that is a few consecutive ticks). One documented starting
    # point; tighten/loosen only with a re-measured justification, never to fit a result.
    #
    # EXCLUDED FROM ``config_fingerprint`` (see the exclusion set in ``config_fingerprint``) with the
    # codified iter-12 / iter-16 discipline: the stance is NEVER PERSISTED (it is a live cue, derived
    # at read from the published verdict + the recorded marks — schema stays v7, no stance row exists).
    # A serving-only timing value that touches NO persisted research value (no verdict, feature, grade,
    # excursion, or stamp) MUST NOT move the fingerprint — else two journals identical in every
    # threshold but served at different stance dwells would mint different fingerprints and could never
    # be pooled. Pinned by a fingerprint-stability test (changing it does NOT move the fingerprint) and
    # its counter-test (a real classifier threshold STILL does).
    management_stance_dwell_seconds: float = 3.0

    # --- Research evolution: ENTRY-CHECKLIST STANCE DWELL (capability 33, J-63; data-contract row 25) -
    # RESEARCH DEFAULT — a starting point calibrated against the deterministic sims, NEVER a validated
    # edge (the goal doc's Research-config-defaults constraint: every research value lives in config
    # with its sim calibration documented; no literal in research code). The entry-checklist AGGREGATE
    # STANCE (``conditions_met | conditions_not_met | tape_against | no_fresh_tape``) is composed at the
    # moment of decision from EXISTING engine values; it publishes through THIS config-owned,
    # LOGICAL-time dwell so a single flickering check (a lone tick where one margin dips under its
    # boundary) never flaps the stance. Calibrated to the SAME 3.0 s the management-stance + per-setup
    # verdict dwells use — the checks it aggregates read already-dwelled canonical values (the published
    # verdict is itself dwell-gated), so a SHORT additional stance dwell suffices to absorb a one-tick
    # flicker without lagging the user's read; at the 0.5 s sim tick that is a few consecutive ticks.
    # One documented starting point; tighten/loosen only with a re-measured justification, never to fit.
    #
    # EXCLUDED FROM ``config_fingerprint`` (see the exclusion set in ``config_fingerprint``) with the
    # codified iter-12 / iter-16 / iter-20 discipline: the checklist + its stance are NEVER PERSISTED
    # (a live cue computed at read from the published verdict + canonical features — schema stays v7,
    # no checklist row exists). A serving-only timing value that touches NO persisted research value
    # (no verdict, feature, grade, excursion, or stamp) MUST NOT move the fingerprint — else two
    # journals identical in every threshold but served at different checklist dwells would mint
    # different fingerprints and could never be pooled. Pinned by a fingerprint-stability test (changing
    # it does NOT move the fingerprint) and its counter-test (a real classifier threshold STILL does).
    checklist_stance_dwell_seconds: float = 3.0

    # --- Research evolution: DELIVERY-LAG BOUND (capability 22 row 14, J-63; data-contract row 14) -----
    # RESEARCH DEFAULT — a documented starting point, NEVER a validated edge. The ``tape_lag_ok``
    # entry-checklist check (J-63) passes when the feeder-owned ``delivery_lag_seconds`` (the latest
    # record's epoch vs wall clock in LIVE mode; the feeder's processing backlog vs its own pacing
    # schedule in paced replay) is at/under THIS bound. A healthy live or sim feed reads a lag well
    # under it; a stalled/backlogged feeder reads above it and ``tape_lag_ok`` honestly fails (feeding
    # ``no_fresh_tape``). Calibrated to the SAME family as ``stale_gap_seconds`` (10.0 s) but tighter:
    # the stale gap is the hard "no event at all" watchdog, whereas this lag bound is the gentler
    # "events are arriving but the processed tape trails real time" honesty gate — 5.0 s so a momentary
    # dense-tape catch-up does not trip it while a sustained processing lag does. Seconds (a wall-clock
    # delivery metric, NEVER read by classification — determinism unchanged), so no relative scaling.
    #
    # EXCLUDED FROM ``config_fingerprint`` (see the exclusion set in ``config_fingerprint``) with the
    # SAME iter-12/16/20 discipline: the lag check is part of the never-persisted checklist (schema
    # stays v7), and ``delivery_lag_seconds`` is feeder-owned DELIVERY metadata that never enters any
    # persisted research value (no verdict, feature, grade, excursion, or stamp). A serving-only bound
    # MUST NOT move the fingerprint — else two journals identical in every threshold but served under
    # different lag bounds could never be pooled. Pinned by a fingerprint-stability test + counter-test.
    delivery_lag_ok_bound_seconds: float = 5.0

    # --- Research evolution: JOURNAL LIST serving (capability 31 / J-51) ------------------------
    # The journal LIST endpoint (``GET /research/journal``) page-size policy. These are SERVING-ONLY
    # values: the number of persisted thesis rows returned per page. They are EXCLUDED from
    # ``config_fingerprint`` (see the exclusion set below) for the same reason ``journal_db_path`` is —
    # a page-size choice cannot affect ANY persisted research value (it never touches a verdict, a
    # feature, a grade, or a stamp). Including it would dishonestly fragment the analytics pools (two
    # journals identical in every threshold but served at different page sizes would mint different
    # fingerprints and could never be pooled), so it is deliberately excluded — never forgotten.
    #   * ``journal_list_default_limit`` — the page size used when the request omits ``limit``.
    #   * ``journal_list_max_limit``     — the hard cap; a request ``limit`` above this is CLAMPED down
    #                                      to it (a serving safety bound, never a 422 — an over-large
    #                                      page is honestly satisfied with the most rows we will serve).
    journal_list_default_limit: int = 50
    journal_list_max_limit: int = 200

    # --- Research evolution: SEGREGATED JOURNAL ANALYTICS (capability 31 / J-59) -----------------
    # The minimum group sample size for the analytics view (``GET /research/analytics``). A per
    # ``setup_type`` × ``direction`` group whose ``n`` is BELOW this serves an explicit
    # ``insufficient_sample`` marker (with ``n`` still present) instead of bare distributions — never
    # a naked percentage on a thin pool. This is a SERVING / PRESENTATION-ONLY threshold: it changes
    # only what the analytics surface CHOOSES to show, never any persisted research value (it never
    # touches a verdict, a feature, a grade, an excursion, or a stamp). It is therefore EXCLUDED from
    # ``config_fingerprint`` (see the exclusion set below) by the SAME iter-12 page-size precedent
    # (``journal_list_*`` above): fingerprinting a display threshold would dishonestly FRAGMENT the
    # analytics pools — two journals identical in every threshold but viewed at different min-sample
    # sizes would mint different fingerprints and could never be pooled. A documented RESEARCH DEFAULT
    # — a starting point, never a validated edge. Defaults to 5 (a small but non-trivial floor so a
    # one-off thesis never reads as a "distribution"). Pinned by a fingerprint-stability unit test
    # (changing this value must NOT change ``config_fingerprint``).
    analytics_min_sample_size: int = 5

    # --- Research evolution: ENTRY RISK FLAGS (capability 26, J-49) -----------------------------
    # RESEARCH DEFAULTS — a starting point calibrated against the deterministic sims, NEVER a
    # validated edge (same discipline as the verdict-dwell defaults above). The flag set is computed
    # ONCE from the declaration-time engine snapshot and FROZEN on the thesis (advisory, never
    # blocking). FOUR of the six flags reuse EXISTING gates with NO new constant:
    #   * ``before_warmup``        reuses ``warmup_min_events`` (the classifier's own warm-up floor);
    #   * ``wide_spread_illiquid`` reuses the classifier's relative-spread gate
    #                              (``max_stable_spread_bps`` when a price basis exists, else the
    #                              absolute ``max_stable_spread``) — VERBATIM, no second threshold;
    #   * ``low_trade_speed``      reuses ``min_trade_speed`` — VERBATIM;
    #   * ``against_expected_tape`` is setup-aware (snapshot tape state vs the setup's expected tape)
    #                              and needs no numeric threshold at all.
    # Only the TWO below are genuinely new (capability 26 names exactly these two as new):
    #
    # CHASE RETURN THRESHOLD (a directional impact-as-return): a declaration is ``chasing_entry`` when
    # the recent FAVORABLE-side price-impact return (the SAME ``buy_price_impact``/``sell_price_impact``
    # divided by the canonical ``reference_price`` the classifier already uses as its relative impact
    # metric — direction-aware: buy for a long, |sell| for a short) ALREADY exceeds this. Calibrated
    # against SIM-BUYER's buyer-control phase: the favorable buy-impact return sits at ~0.0033 right at
    # warm-up and climbs past ~0.0040 a few seconds later (an EXTENDED move), so a 0.0040 threshold
    # fires ``chasing_entry`` on a well-past-warm-up declare (the move has already run) while a clean
    # at-warm-up declare does not — the honest "you are chasing an extended move" boundary. Expressed
    # as a RETURN (not a dollar move) so it scales to any instrument's price level (no-magic-numbers).
    chase_return_threshold: float = 0.0040
    # INVALIDATION-TOO-TIGHT SPREAD MULTIPLE: a declaration is ``invalidation_too_tight`` when the
    # distance from the current last to the declared invalidation is BELOW this many times the current
    # spread — i.e. the stop sits so close to price that ordinary spread noise would trip it. A spread
    # MULTIPLE (not a dollar band) so it scales to any instrument's price/liquidity, mirroring the
    # invalidation-ε robustness multiple. Calibrated against the sim's ~$0.02 spread: at a 2.0×
    # multiple an invalidation within ~$0.04 of the last is flagged too tight, while a normal
    # invalidation ~$1 away (50× the spread) is comfortably clear.
    invalidation_too_tight_spread_multiple: float = 2.0

    # --- Research evolution: OUTCOME × PROCESS GRADES (capability 29, J-56) ----------------------
    # The config-owned rules for the two review grades, computed ONCE at terminal resolution
    # (alongside execution checks) and persisted (schema v6). NO numeric score anywhere — both axes
    # are ENUM labels with plain-language evidence naming which named checks drove them.
    #
    # OUTCOME (``thesis_held | thesis_failed | no_read``) is 1:1 from the resolution (goal.md
    # capability 29) — a fixed, config-owned map, never a judgement:
    #   * ``played_out``  -> ``thesis_held``   (the idea ran its course on your side);
    #   * ``invalidated`` -> ``thesis_failed`` (the tape resolved it against the thesis);
    #   * ``expired``     -> ``no_read``       (the watch ended before the thesis resolved either way);
    #   * ``abandoned``   -> ``no_read``       (closed without running its course — no outcome read).
    # Kept in config (not hardcoded in research code) so the single 1:1 mapping has ONE owner.
    process_outcome_grade_map: dict = field(
        default_factory=lambda: {
            "played_out": "thesis_held",
            "invalidated": "thesis_failed",
            "expired": "no_read",
            "abandoned": "no_read",
        }
    )
    # PROCESS (``clean | flagged | violated``) is a config-owned RULE over the named, evidence-backed
    # checks (the FROZEN entry risk flags + the persisted execution checks) — NEVER a numeric score,
    # and CRITICALLY: being invalidated is never by itself a process failure (the system enforces
    # invalidation; an invalidated thesis with no failed execution check and no fired risk flag grades
    # ``clean``). The rule, in priority order (the worst named finding wins):
    #   * ``violated`` — at least ``process_violated_min_failed_checks`` execution check(s) read
    #     ``failed`` (the user demonstrably did something the checks flag: held through the stop,
    #     chased, cut a confirming thesis early, entered before confirmation). A failed EXECUTION
    #     check is grounded in the user's OWN recorded marks, so it is a process matter.
    #   * ``flagged`` — no failed execution check, but at least
    #     ``process_flagged_min_risk_flags`` entry risk flag(s) fired at declaration (an advisory the
    #     user declared into). Risk flags are advisory, so they ``flag`` rather than ``violate``.
    #   * ``clean``   — neither (no failed execution check, no fired risk flag).
    # The two thresholds are config-owned (no literal in research code) and default to 1 (any single
    # failed check violates; any single fired flag flags). They are documented research defaults — a
    # starting point, never a validated edge.
    process_violated_min_failed_checks: int = 1
    process_flagged_min_risk_flags: int = 1

    # --- Research evolution: EXCURSION OUTCOMES (capability 30, J-58) ----------------------------
    # The config-owned excursion horizons, computed ONCE at terminal resolution / stream-end (a
    # research record, schema v7) and served VERBATIM on the journal detail. NO numeric "score"
    # anywhere — each horizon reports MFE/MAE in R units + a TERNARY outcome
    # (``+1R_first | -1R_first | neither_within_horizon``) resolved by FIRST TOUCH in logical time.
    # These are documented RESEARCH DEFAULTS — a starting point, never a validated edge — and they
    # enter ``config_fingerprint`` (it hashes the entire config), so a record created after this
    # iteration carries a new fingerprint (the intended honesty mechanism: analytics never pool
    # across fingerprints). This is NOT a defect — it is the same fingerprint-shift discipline every
    # prior research-config addition introduced.
    #
    # HORIZONS (logical seconds past the anchor): the canonical 10 / 30 / 60 / 120 s family
    # (goal.md's predictive-value horizons). Calibrated against the seeded J-58 substrate — J-42's
    # ``SIM-BUYER`` confirmed long with the EXACT J-42 invalidation of 98.00 (R ≈ 2.21 at the
    # confirmation, which lands ~22.5s logical in). SIM-BUYER grinds price strictly UP but only at
    # ~$0.012/s, so a full +1R favorable move ($2.21 past the anchor) is NOT reached within any short
    # horizon: the 10 / 30 / 60s horizons fully ELAPSE at ``neither_within_horizon`` (a partial
    # favorable excursion honestly recorded as MFE, well under +1R) — at least one COMPLETED horizon.
    # The J-58 script ends the watch ~77s of logical time past the confirmation (the entry-marked
    # thesis then survives active-but-not-evaluated at the stream end), which is BEFORE the 120s
    # horizon elapses, so the 120s horizon is still open and is TRUNCATED at the stream end — at least
    # one STREAM-END-TRUNCATED horizon. Both requirements the spec calls for are thus deterministically
    # exercised by the seeded run (proven in test_excursions.py's J-58 calibration test).
    excursion_horizons_seconds: tuple = (10.0, 30.0, 60.0, 120.0)
    # The R MULTIPLE at which the ternary outcome resolves by first touch (favorable reaches
    # ``+excursion_target_r`` before adverse reaches ``-excursion_target_r``, or neither within the
    # horizon). Kept in config (no literal in research code) so the "+1R / -1R" definition has ONE
    # owner; defaults to 1.0 R (the goal-doc ternary ``+1R_first | -1R_first | neither``). A research
    # default — a starting point, never a validated edge.
    excursion_target_r: float = 1.0

    # --- Engine-performance gate: dense-replay CI time budget (capability 34, J-62) -------------
    # The wall-clock BUDGET (seconds) the CI timing gate allows for an UNPACED replay of the
    # committed ≈10-minute real SIP dense fixture through a fresh full ``TapeEngine`` (the same
    # fixture-replay path the J-60 study runner will use). The gate proves rolling-feature
    # maintenance is TRULY INCREMENTAL across window evictions — no per-event full-window rescan —
    # so the studies layer can be built on an engine that demonstrably keeps up with dense real tape.
    #
    # CALIBRATION (documented research/CI default, never a validated edge): on the dev machine the
    # committed PG 10-minute SIP fixture (3,229 trades + 11,012 quotes; all five windows evict)
    # replays unpaced in ≈10 s with the incremental refresh maintenance, versus ≈184 s with the old
    # permanently-degraded post-eviction merge (the quadratic defect this gate guards against). The
    # budget is set with generous headroom (≈6× the measured incremental time, and far below the
    # minutes the O(n²) path costs) so the gate does NOT flake on a slow CI box yet STILL fails hard
    # if the quadratic regression returns. Raise it only with a re-measured justification — never to
    # paper over a real regression.
    #
    # EXCLUDED FROM ``config_fingerprint`` (see the exclusion set in ``config_fingerprint``), with
    # the iter-12 / iter-16 discipline: this is a CI GATE value that never enters ANY persisted
    # research computation (it touches no verdict, feature, grade, excursion, or stamp). Fingerprinting
    # it would dishonestly FRAGMENT the analytics pools — two journals identical in every threshold
    # but run under different CI budgets would mint different fingerprints and could never be pooled.
    # Pinned by a fingerprint-stability test (changing it does NOT move the fingerprint) and its
    # counter-test (a real classifier threshold still DOES).
    dense_replay_time_budget_seconds: float = 60.0

    # --- Research evolution: REPLAY STUDIES (capability 32, J-60/J-61/J-62) ----------------------
    # RESEARCH DEFAULTS — a starting point calibrated against the seeded sims + the committed PG SIP
    # reference fixture, NEVER a validated edge (the goal doc's Research-config-defaults constraint:
    # every research value lives in config with its sim/fixture calibration documented; no literal in
    # research code). A replay study runs the EXISTING setup grammar over a chosen window through a
    # FRESH engine (observer-only), auto-arms occurrences per the rules below, measures each
    # occurrence's excursions through the EXISTING excursion machinery, and reports them side-by-side
    # with a seeded random-arm-time NULL baseline. These five values SHAPE the persisted study results
    # (which occurrences arm, the R basis they measure against, how many null arms), so they ENTER
    # ``config_fingerprint`` — a study created after this iteration carries a new fingerprint (the
    # intended honesty mechanism: studies never pool across fingerprints). This is NOT a defect — it is
    # the same fingerprint-shift discipline every prior research-config addition introduced.
    #
    # STUDY NULL-ARM COUNT: how many random-arm-time NULL-baseline occurrences are drawn (from the
    # recorded seed) over the SAME window, SAME direction, SAME R definition, and SAME horizons as the
    # setup arms. The seed is persisted on the study record so the baseline reproduces exactly. A
    # control population large enough to be a meaningful comparison yet bounded so one in-memory replay
    # pass serves both populations within the CI budget. Defaults to 100 (the goal.md register's
    # "random-time baseline: 41/100" illustration).
    study_null_arm_count: int = 100
    # STUDY ARMING SUSTAIN (logical seconds): the auto-arming rule for the two state-native setups
    # (absorption_reversal / trend_continuation) requires the setup's PREMISE tape state to hold
    # CONTINUOUSLY for at least this long before an occurrence is armed — so a single flickering tick
    # never arms an occurrence (the same sustained-evidence discipline the verdict dwell enforces).
    # Composed ONLY of EXISTING engine states (no new indicator): absorption_reversal arms on sustained
    # matching ABSORPTION (the premise), trend_continuation on sustained matching CONTROL. Calibrated
    # against the sims' 30s primary window + their phase lengths so SIM-REVERSAL's absorption phase and
    # SIM-BUYER's control phase each arm exactly one occurrence at the point the premise is settled.
    study_arm_sustain_seconds: float = 5.0
    # STUDY ARMING COOLDOWN (logical seconds): after an occurrence arms, no further occurrence of the
    # same study arms until this much logical time has elapsed past the arm — so one sustained premise
    # phase produces ONE occurrence, not an occurrence every tick. A generous default (longer than the
    # longest excursion horizon) so occurrences are well-separated and never overlap their excursion
    # windows. Calibrated so each single-regime sim phase yields exactly one armed occurrence.
    study_arm_cooldown_seconds: float = 180.0
    # STUDY OCCURRENCE-R SPREAD MULTIPLE (the named occurrence-R design decision — documented in the
    # dev handoff). An auto-armed occurrence has NO user-typed invalidation, so its R basis is derived
    # DETERMINISTICALLY from existing engine values at the arm instant: a synthetic invalidation placed
    # this many TIMES the arm-instant spread on the ADVERSE side of the arm price (below for a long,
    # above for a short). R = |arm_price − synthetic_invalidation| then flows through the EXISTING
    # ``marks.r_basis`` helper + the ``excursions.py`` ternary/horizon machinery — the study is a
    # REGISTERED CONSUMER of the one R formula, never a second one. IDENTICAL for setup and null arms
    # (each arm derives its own basis from its own arm-instant price + spread the same way). A spread
    # MULTIPLE (not a dollar band) so it scales to any instrument, mirroring the invalidation-ε /
    # too-tight multiples. NEVER fitted to make results look good — that would be auto-tuning. Defaults
    # to 10.0 (a stop comfortably outside spread noise yet reachable within the configured horizons on
    # a real move — calibrated against the GME drop slice + the sim phases so +1R/−1R are exercised).
    study_occurrence_r_spread_multiple: float = 10.0
    # STUDY OCCURRENCE-R FLOOR (a price distance): a no-spread-basis fallback for the occurrence R so a
    # window whose arm-instant quote is missing/zero still measures a meaningful, deterministic R rather
    # than a degenerate R == 0 that resolves every horizon to ``neither`` (an honest but useless null
    # study). The synthetic invalidation is placed MAX(spread-multiple band, this floor) from the arm
    # price on the adverse side. A price-distance floor (not a multiple) since by definition there is no
    # spread to scale; documented research default calibrated against the sims' ~$0.01 tick so it is a
    # few ticks. Enters the fingerprint (it shapes the persisted R basis).
    study_occurrence_r_floor: float = 0.05
    # STUDY NULL-BASELINE SEED: the default seed used to draw the random null-arm times when a study
    # does not carry its own. Persisted on each study record at creation so the baseline reproduces
    # exactly (same seed ⇒ identical arms). A documented research default; it shapes the persisted null
    # baseline, so it ENTERS the fingerprint. Per-study override is possible (recorded on the record),
    # but the default keeps the committed reference study reproducible in CI.
    study_null_baseline_seed: int = 1729
    # STUDY LIST PAGE SIZE (``GET /research/studies``): a SERVING-ONLY value — the max number of study
    # rows the list returns. EXCLUDED from ``config_fingerprint`` (see the exclusion set in
    # ``config_fingerprint``) by the SAME iter-12 page-size precedent (``journal_list_*``): a list page
    # size touches NO persisted study value (it never changes an occurrence, an R basis, a baseline, or
    # a stamp), so two journals identical in every threshold but served at different study-list page
    # sizes MUST share a fingerprint (else fragmenting the very pools studies exist to compare). Pinned
    # by a fingerprint-stability test (changing it does NOT move the fingerprint) and its counter-test.
    study_list_max: int = 100
    # HINT SUSTAIN DWELL (logical seconds, capability 33 / J-65): a state-native setup-forming hint
    # fires only after its PREMISE tape state (one of the four sustained states — bid_absorption /
    # ask_absorption / buyer_control / seller_control) has held CONTINUOUSLY for at least this long —
    # so a single flickering tick, or SIM-CHOP's flapping unclear/mixed stream, NEVER sustains past
    # it and NEVER fires a hint (the same sustained-evidence discipline the verdict dwell and the
    # study-arm sustain enforce). Composed ONLY of EXISTING engine states (no new indicator). A
    # RESEARCH DEFAULT — a starting point, never a validated edge. Logical-time (the verdict-dwell
    # precedent), so sim journeys are deterministic and no wall-clock enters a hint decision (the wall
    # ts on the record is a stamp only). Calibrated against the sims' phase lengths so SIM-BIDABS's
    # sustained bid_absorption phase fires exactly one hint within a browser-verifiable wait, while
    # SIM-CHOP's flapping never holds one premise state long enough to reach it. ENTERS the fingerprint
    # (it shapes the persisted hint records — the study-arm-sustain precedent).
    hint_sustain_dwell_seconds: float = 5.0
    # HINT COOLDOWN (logical seconds, capability 33 / J-65): after a hint fires for a pattern on the
    # watched ticker, no further hint of the SAME pattern on the SAME ticker fires until this much
    # logical time has elapsed past the fire — so one sustained premise phase produces ONE logged hint,
    # not a hint every tick (the study-arm-cooldown precedent). A generous default so re-fires are
    # well-separated; the active-hint lifecycle (clear-on-state-leave / clear-on-non-live-status) is
    # independent of this re-fire gate. A RESEARCH DEFAULT, logical-time, deterministic. ENTERS the
    # fingerprint (it shapes which hint records are persisted — the study-arm-cooldown precedent).
    hint_cooldown_seconds: float = 180.0
    # HINT LOG PAGE SIZE (``GET /research/hints``): a SERVING-ONLY value — the default/max number of
    # persisted hint-log rows the list returns. EXCLUDED from ``config_fingerprint`` (see the exclusion
    # set in ``config_fingerprint``) by the SAME iter-12 page-size precedent (``journal_list_*`` /
    # ``study_list_max``): a list page size touches NO persisted hint value (it never changes a hint
    # record, its evidence, its citation, or its stamps), so two journals identical in every threshold
    # but served at different hint-log page sizes MUST share a fingerprint. Pinned by a
    # fingerprint-stability test (changing it does NOT move the fingerprint) and its counter-test
    # (``test_hint_log_max_is_serving_only_excluded_from_fingerprint`` +
    # ``test_a_real_threshold_still_changes_fingerprint`` in ``tests/test_research_hints.py``, iter-24).
    hint_log_max: int = 200
    # SOUND-CUE COOLDOWN (wall-clock seconds, capability 33 / J-66): the OPTIONAL, off-by-default
    # client sound cue (the last capability-33 item) fires ONLY on a stance/verdict TRANSITION and then
    # stays silent for at least this many seconds before it may fire again — a debounce so a brief
    # verdict flicker (or two transitions in quick succession) never machine-guns the speaker. The cue
    # itself is a CLIENT-LOCAL UI preference: the toggle state is never sent to the backend and the cue
    # is NEVER PERSISTED. This key is SERVING-ONLY — it is served additively to the frontend via the
    # row-24 taxonomy payload (alongside the sound-cue display copy) so the cooldown is config-owned
    # (no magic number in the UI), and the browser reads it verbatim. A RESEARCH DEFAULT — a documented
    # starting point, never a validated edge. Calibrated to the SAME 3.0 s family as the verdict /
    # stance dwells (the values it debounces are themselves already dwell-gated), so a single extra
    # debounce of that order suffices to avoid a double-fire without lagging a genuine second
    # transition. Seconds (a wall-clock UI debounce, NEVER read by classification — determinism
    # unchanged), so no relative scaling.
    #
    # EXCLUDED FROM ``config_fingerprint`` (see the exclusion set in ``config_fingerprint``) with the
    # codified iter-12/16/20/23 discipline: the cue is NEVER PERSISTED (schema stays v7 — no cue row
    # exists), so this serving-only timing value touches NO persisted research value (no verdict,
    # feature, grade, excursion, stamp, hint, or study). It MUST NOT move the fingerprint — else two
    # journals identical in every threshold but served at different cue cooldowns would mint different
    # fingerprints and could never be pooled. Pinned by a fingerprint-stability test (changing it does
    # NOT move the fingerprint) + the real-threshold counter-test, in the SAME commit as this key (the
    # ``study_list_max`` / ``hint_log_max`` serving-only pattern; iter-23 lesson — never promised only
    # in prose).
    sound_cue_cooldown_seconds: float = 3.0

    # --- Profit-research era: STRATEGY GRAMMAR V1 + BACKTEST models (capabilities 3/4, J-03) -------
    # RESEARCH DEFAULTS — documented starting points calibrated against the deterministic sims and
    # the committed PG SIP fixture pair, NEVER a validated edge and NEVER fitted to make results
    # look good (the no-ML / no-online-tuning anti-goal: these values are fixed config, enumerated
    # here and nowhere else; nothing moves at runtime). The complete v1 strategy definition (Data
    # Contract row 34) is ``strategy_definition`` below — a pure read of these fields plus the
    # REUSED studies constants (``study_arm_sustain_seconds`` / ``study_arm_cooldown_seconds`` for
    # entry arming; ``study_occurrence_r_spread_multiple`` / ``study_occurrence_r_floor`` for the
    # R-stop's arm-instant synthetic invalidation) — no new indicator, no second copy of any
    # existing threshold. All five values below SHAPE persisted backtest reports (which fills, at
    # what adjusted prices, at what cost, in whose dollars), so they ENTER ``config_fingerprint``
    # (the intended never-pool-across-fingerprints honesty shift, exactly like every prior
    # research-config addition).
    #
    # TIME-HORIZON EXIT (logical seconds after entry): an open simulated trade that has hit neither
    # its R-stop nor a state-flip exits at the first recorded event at/after this horizon.
    # Calibrated to the LONGEST excursion horizon (excursion_horizons_seconds' 120s) so a backtest
    # trade's lifetime matches the outermost window the excursion machinery already studies, and so
    # the bounded sims deterministically exercise a completed horizon exit (SIM-BUYER's 24.5s arm
    # exits at 144.5s inside the bounded stream — pinned in tests/test_backtests.py).
    strategy_exit_horizon_seconds: float = 120.0
    # FEE MODEL (explicit, disclosed in every report): a per-share fee with a minimum per fill —
    # both legs of a round trip pay ``max(per_share x shares, min_per_trade)``. The $0.005/share +
    # $1 minimum shape is the widely published US-equity per-share commission scale — a disclosed
    # ASSUMPTION for simulated fills, never a claim about any live venue's pricing.
    strategy_fee_per_share: float = 0.005
    strategy_fee_min_per_trade: float = 1.0
    # SLIPPAGE MODEL (explicit, disclosed): each fill pays this FRACTION of the recorded
    # at-that-event spread ADVERSELY (entry worse by it, exit worse by it). 0.5 models crossing
    # the spread from mid — the honest cost of taking liquidity at the recorded quote; a recorded
    # moment with no usable quote (spread None/<=0) honestly contributes zero slippage rather than
    # a fabricated cost.
    strategy_slippage_spread_fraction: float = 0.5
    # FIXED $-PER-R NOTIONAL (dollar conversion): every simulated trade risks exactly this many
    # dollars per 1R (shares = dollars_per_r / R basis), so R and $ are two disclosed unit systems
    # over the SAME measurement and a dollar figure can never appear without its R counterpart.
    # $100/R keeps the illustrative scale small and obviously simulated.
    strategy_dollars_per_r: float = 100.0
    # SEEDED RANDOM-ENTRY NULL BASELINE (the report's mandatory comparison population): this many
    # random entry instants (and per-entry random directions) drawn from the recorded seed over the
    # SAME dataset, exiting under the SAME rules, fees, and slippage. Count mirrors
    # ``study_null_arm_count`` (100); the seed mirrors the ``study_null_baseline_seed`` precedent —
    # recorded verbatim in every report so the baseline reproduces exactly. Both SHAPE the persisted
    # report, so both ENTER the fingerprint.
    backtest_null_entry_count: int = 100
    backtest_null_baseline_seed: int = 1729
    # BACKTEST LIST PAGE SIZE (``GET /research/backtests``): a SERVING-ONLY value — the max number
    # of backtest rows the list returns. EXCLUDED from ``config_fingerprint`` (see the exclusion
    # set in ``config_fingerprint``) by the SAME iter-12 page-size precedent (``journal_list_*`` /
    # ``study_list_max`` / ``hint_log_max``): a list page size touches NO persisted backtest value
    # (it never changes a trade, a fill, an aggregate, a baseline, or a stamp), so two journals
    # identical in every threshold but served at different backtest-list page sizes MUST share a
    # fingerprint. Pinned by a fingerprint-stability test + the real-threshold counter-test
    # (tests/test_backtests.py).
    backtest_list_max: int = 100

    # --- Profit-research era: THE PnL LEDGER (capability 5, J-04; Data Contract row 32) ----------
    # "INSUFFICIENT SAMPLE" LABEL MINIMUM: a ledger split (train or hold-out) whose ``n`` is BELOW
    # this serves an explicit ``insufficient_sample`` marker (with ``n`` still present) on every
    # surface — REST, the markdown render, and the MCP proxy of the same route — never a naked
    # simulated PnL figure on a thin pool. This is a SERVING / PRESENTATION-ONLY threshold (the
    # documented ``analytics_min_sample_size`` EXCLUSION rationale, J-59): it changes only what the
    # ledger surfaces CHOOSE to label, never any persisted research value (the stored row keeps its
    # verbatim copied aggregates whatever the minimum reads). It is therefore EXCLUDED from
    # ``config_fingerprint`` (see the exclusion set below) — two journals identical in every
    # threshold but viewed at different label minimums MUST share a fingerprint. Defaults to 5 (the
    # ``analytics_min_sample_size`` floor — a small but non-trivial n under which a distribution
    # claim would be dishonest). NOTE: J-07's PROMOTION minimum is a separate, future decision —
    # a gate that decides what gets promoted shapes persisted rows and will be fingerprinted there.
    # Pinned by a fingerprint-stability test + the founding-value counter-test
    # (tests/test_pnl_ledger.py).
    pnl_min_sample_size: int = 5
    # THE FOUNDING BASELINE ROW's identity (config-owned — no literal in research code): the
    # enhancement id and title of the era's FIRST ledger row, measuring strategy v1 on profile
    # ``default`` over the frozen fixture train + hold-out pair. The id is the uniqueness key (one
    # honest row per enhancement), so re-running the seeding CLI finds it and no-ops honestly.
    # Both values are persisted VERBATIM into the row, so they are row-shaping and DELIBERATELY
    # NOT excluded from ``config_fingerprint`` (the never-pool honesty mechanism — pinned by the
    # counter-test in tests/test_pnl_ledger.py).
    pnl_founding_enhancement_id: str = "founding-baseline-strategy-v1-default"
    pnl_founding_enhancement_title: str = "founding baseline — strategy v1 on default"
    # THE FOUNDING WINDOWS (UTC ISO start/end pairs): the exact slices of the committed keyless
    # ``PG_SIP_REFERENCE`` window the founding row measures — chosen to reproduce the committed
    # fixture dataset pair CONTENT-IDENTICALLY (the seeding CLI records through the real store
    # path; content checksums equal the committed pair's, proven in tests/test_pnl_ledger.py).
    # Frozen coordinates of frozen data: they select WHAT the founding row measures, so they are
    # row-shaping and DELIBERATELY NOT excluded from ``config_fingerprint``.
    pnl_founding_train_window: tuple = ("2026-06-09T17:00:00Z", "2026-06-09T17:01:00Z")
    pnl_founding_holdout_window: tuple = ("2026-06-09T17:05:00Z", "2026-06-09T17:05:45Z")
    # WHERE the pure-rendered PnL history markdown lives: the COMMITTED repo file
    # ``reports/pnl/pnl-history.md`` (goal.md capability 5 / Product Shape names exactly this
    # path). Package-anchored absolute default (the ``dataset_dir`` pattern) so the render CLI
    # resolves it whatever the process cwd is; tests pass an explicit temp path to the write
    # function instead. EXCLUDED FROM ``config_fingerprint`` (see the exclusion set below) with
    # the ``journal_db_path`` / ``dataset_dir`` discipline: WHERE the render is written cannot
    # affect any persisted research value, and the default embeds an absolute per-machine path.
    pnl_history_md_path: str = str(
        Path(__file__).resolve().parents[3] / "reports" / "pnl" / "pnl-history.md"
    )

    # --- Profit-research era: THE FIRST CANDIDATE INDICATOR PROFILE (capability 2, J-06; Data
    # Contract row 33) -----------------------------------------------------------------------------
    # RESEARCH DEFAULT — a starting point, NEVER a validated edge (no-ML / no-online-tuning
    # anti-goal: candidate search is bounded, config-enumerated, offline). The candidate's ONE
    # additive change: an ALTERNATE THRESHOLD VALUE for the EXISTING ``warmup_min_events`` gate
    # (never a new code path, never a second gate) — fewer processed trades are required before
    # the classifier evaluates the real control/absorption gates instead of forcing a cold-start
    # ``unclear``. Read ONLY by ``Config.resolved_for_profile`` to build a per-run OVERLAY
    # ``Config`` (via ``dataclasses.replace`` — never a mutation) for a backtest that explicitly
    # requests ``PROFILE_CANDIDATE_FASTER_WARMUP``; ``warmup_min_events`` itself and the shared
    # ``CONFIG`` singleton are NEVER touched, so the live cockpit and every ``default``-profile
    # backtest stay byte-identical (equivalence-tested in tests/test_profile_equivalence.py).
    #
    # CALIBRATED to legitimately move behavior on the committed PG SIP reference fixture (the
    # iter-4 "make it fire" lesson — never a no-op candidate): lowering the floor from 40 to 30
    # processed trades moves the first directional call genuinely EARLIER on BOTH the founding
    # train and hold-out windows (a real ``tape_state`` difference, not merely a confidence
    # nudge — pinned in tests/test_profile_equivalence.py), while the control/absorption gates
    # themselves (ratio / impact / spread / speed) are completely untouched — a call this
    # candidate makes is exactly as evidenced as ``default``'s, just permitted to fire on fewer
    # processed trades.
    #
    # EXCLUDED FROM ``config_fingerprint`` (see the exclusion set in ``config_fingerprint``): this
    # field is REGISTRY METADATA ONLY — the value ``resolved_for_profile`` overlays onto the REAL
    # ``warmup_min_events`` field — and is never itself read by engine/classifier code, so its mere
    # presence on ``Config`` must NOT move ANY existing fingerprint (``default``'s included, pinned
    # against the committed founding PnL-ledger row). The candidate's distinct fingerprint comes
    # from the OVERLAID ``warmup_min_events`` value on the resolved per-run Config — the ONE
    # existing hasher, no second mechanism.
    profile_candidate_warmup_min_events: int = 30

    # --- Profit-research era: THE CANDIDATE-SWEEP PROMOTION GATE (capability 7, J-07) -------------
    # The minimum PER-SPLIT trade count (n) a candidate's HOLD-OUT measurement must reach before it
    # is even ELIGIBLE for promotion — the config.py:920 note's "separate, future decision" for J-07,
    # now made: a DEDICATED field rather than reusing ``pnl_min_sample_size``, because the two
    # thresholds gate DIFFERENT things (that one labels a served split "insufficient sample" for
    # display; this one decides whether a candidate may EVER become champion) even though they
    # currently share the same floor value — the ``analytics_min_sample_size`` vs
    # ``pnl_min_sample_size`` precedent (two distinct min-n fields for two distinct honesty
    # purposes). Enforced BOTH ways by ``app/research/pnl_scan.py`` (the sweep's ONE reader): a
    # below-minimum candidate is refused promotion even with a positive hold-out net R/$ delta; an
    # at-or-above-minimum candidate with a positive hold-out net R AND net $ delta is promoted.
    #
    # EXCLUDED FROM ``config_fingerprint`` (see the exclusion set below), matching the
    # ``pnl_min_sample_size`` discipline exactly: this gate decides WHICH candidate gets promoted
    # and thus WHETHER a ledger row / champion move happens, but it never shapes the CONTENT of any
    # persisted trade, fill, or aggregate — a promoted candidate's ledger row stores the SAME
    # verbatim backtest aggregates whatever this threshold reads, exactly like the label minimum's
    # "insufficient_sample" marker never touches a stored row's numbers. Two journals identical in
    # every threshold but configured with a different promotion floor MUST share a fingerprint (else
    # the very backtests this floor gates would be dishonestly fragmented across fingerprints for a
    # presentation/decision-only reason). This is a FLAGGED JUDGMENT CALL (see the design notes in
    # ``runs/goal-tape_to_profit-iter-7/plan.md``): the config.py:920 note could also be read as
    # "the promotion gate should move the fingerprint" — but that note describes the ledger ROW's
    # OWN existing provenance stamp (every backtest report already carries its own
    # ``config_fingerprint``), not a mandate to fingerprint this threshold specifically. Verified
    # against the pinned default fingerprint test in ``tests/test_profile_equivalence.py``.
    promotion_min_sample_size: int = 5

    # --- Structure-and-tape era: MULTI-TIMEFRAME BAR STORE (era-4 capability 1, J-01) -------------
    # Where the bar store persists explicitly recorded multi-timeframe OHLC bar series (one JSON
    # file per series) — mirrors ``dataset_dir`` exactly (the era-3 capability-1 precedent). It is
    # ONLY a default here — the operator overrides it with the ``TAPEOLOGY_BAR_DIR`` env var (read
    # in ``bar_dir_resolved`` below, the ``dataset_dir_resolved`` pattern) and tests point it at a
    # temp dir the same way. The default is package-anchored (``apps/backend/.data/bars/``, covered
    # by the repo's ``.data/`` gitignore entry) so it resolves identically whatever the process cwd
    # is. Persistence is SCOPED: this dir holds explicitly recorded bar series ONLY — the live
    # cockpit's tape is NEVER written here (recording is an explicit research action).
    #
    # EXCLUDED FROM ``config_fingerprint`` (see the exclusion set in ``config_fingerprint``) with
    # the ``dataset_dir`` discipline: WHERE bar series are stored cannot affect any persisted
    # research value, so two journals identical in every threshold but storing bars in different
    # directories (or on different machines — the default embeds an absolute path) MUST share a
    # fingerprint. Pinned by a fingerprint-stability test + the real-threshold counter-test
    # (tests/test_bars.py).
    bar_dir: str = str(Path(__file__).resolve().parents[1] / ".data" / "bars")

    # The valid ``?timeframe=`` set for a bar recording — distinct from the EXISTING intra-second
    # ``history_bar_sizes`` above (the tape engine's OHLC candle bin sizes in LOGICAL SECONDS for
    # the live prediction chart; an unrelated concept that must not be conflated or collide). These
    # are CALENDAR OHLC candle timeframes (goal.md's long-term/mid-term/shorter-timeframe
    # hierarchy): minute-level (shorter), hour-level including 4h/8h (mid-term), and day/week/month
    # (long-term). An out-of-set value is a 422 (never silently coerced) — mirrors the ``?bar=``
    # validation precedent. A pure validation ALLOWLIST (it shapes no persisted tape/backtest/study
    # value), so it is EXCLUDED FROM ``config_fingerprint`` alongside ``bar_dir`` (same rationale).
    bar_timeframes: tuple[str, ...] = ("1m", "5m", "15m", "1h", "4h", "8h", "1d", "1w", "1mo")

    # FREE-TIER RECENCY-DELAY GUARD (seconds): the configured market-data vendor's free plan serves
    # historical bars with roughly a 15-minute delay — the vendor entitlement excludes the most
    # recent 15 minutes of data. A bar-record request's effective vendor-fetch window end is
    # clamped to ``min(requested_end, now - bar_recency_delay_seconds)`` (the one concrete adapter's
    # ``fetch_bars``, via its ``_bar_fetch_end_clamp`` helper) so the adapter never asks for — and
    # so never receives — the still-embargoed most-recent bar. A documented, disclosed OPERATIONAL
    # assumption (the free-plan historical delay), never a validated edge. EXCLUDED FROM
    # ``config_fingerprint``: it governs WHICH real bars a fetch can reach, not any
    # tape/backtest/study computation. (Vendor specifics stay confined to the one adapter module —
    # the provider-agnostic-engine anti-goal — so this value is deliberately described generically.)
    bar_recency_delay_seconds: float = 900.0

    # RATE-THROTTLE (a documented, disclosed operational assumption — the configured market-data
    # vendor's published free-tier rate limit is 200 requests/minute): the minimum wall-clock
    # spacing enforced between consecutive REAL bar-fetch vendor calls (the one concrete adapter's
    # own throttle helper), so a bulk multi-timeframe backfill never bursts past the entitlement. A
    # single interactive record request is unaffected beyond waiting behind its OWN
    # immediately-prior call. This paces CALL FREQUENCY only — the EXISTING
    # ``vendor_http_timeout_seconds`` still bounds each call's own duration; the two are independent
    # and MUST NOT be conflated. EXCLUDED FROM ``config_fingerprint``: an operational vendor-call
    # cadence, never a tape/backtest/study value.
    bar_rate_limit_per_minute: int = 200

    # --- Structure-and-tape era: deterministic S/R LEVEL detection (era-4 capability 2, J-02) -----
    # RESEARCH DEFAULTS -- a starting point, never a validated edge (the same
    # ``verdict_dwell_seconds`` discipline: every research value lives in config with its
    # rationale documented here; no literal in ``research/levels.py``). Namespaced ``sr_*``
    # (support/resistance) so it never collides with the EXISTING, UNRELATED intraday tape setups
    # ``level_break`` / ``failed_move_fade`` (above) -- a different "level" concept entirely (a
    # structural price derived from bars, not a live tape-arming setup).
    #
    # PIVOT LOOKBACK N: a bar's high (or low) is a swing-high (swing-low) pivot iff it is STRICTLY
    # greater (less) than BOTH its N neighbours on either side -- a ``2N+1``-bar fractal window.
    # N=1 (a 3-bar window) is the smallest window that defines a local extreme at all; it already
    # yields real pivots on the committed PG 1h/1d fixtures (verified in ``tests/test_levels.py``)
    # without any fixture extension.
    sr_pivot_lookback: int = 1
    # TOUCH TOLERANCE (basis points of the level's OWN price -- the "RELATIVE ... judged relative
    # to the instrument's price level" discipline above, not an absolute dollar constant that
    # would not scale across instruments): a bar (other than the level's own originating bar,
    # which always counts) registers an extra "touch" of a level iff its high OR low comes within
    # ``price * sr_touch_tolerance_bps / 10_000`` of the level's price. Feeds ``touch_count`` and,
    # through it, ``strength``.
    sr_touch_tolerance_bps: float = 5.0
    # PER-TIMEFRAME WEIGHT: ``strength = timeframe_weight * touch_count``. Ordinally increasing
    # with timeframe length (goal.md's stated hypothesis -- "levels that align across timeframes
    # matter more" -- long-term levels carry more conviction than short-term ones), covering every
    # timeframe ``bar_timeframes`` registers (``tests/test_levels.py`` pins the set equality) so a
    # weight lookup never silently falls back to a fabricated default.
    sr_timeframe_weights: dict = field(
        default_factory=lambda: {
            "1m": 1.0,
            "5m": 1.0,
            "15m": 1.0,
            "1h": 2.0,
            "4h": 3.0,
            "8h": 3.0,
            "1d": 4.0,
            "1w": 5.0,
            "1mo": 6.0,
        }
    )

    def profile_definition(self, profile_id: str) -> dict | None:
        """The config-owned descriptor for ``profile_id`` (Data Contract row 33) — the
        ``strategy_definition`` pattern applied to profiles: THIS method is the ONE place that
        decides registration. ``profiles_projection`` (``GET /research/profiles``) and the
        backtest route's validation both consult it — never a second allowlist. Returns ``None``
        for an unregistered id (the route maps that to an honest 422).

        ``default`` is the frozen legacy profile (no overrides — every archived-era surface and
        the live cockpit run on it, byte-equivalence-tested). The ONE registered candidate is
        additive-only and self-documenting: its id, the profile it is ``based_on``, and its exact
        declared ``overrides`` (field name -> value, read from config — no magic number)."""
        if profile_id == PROFILE_DEFAULT:
            return {"id": PROFILE_DEFAULT, "frozen": True, "is_default": True}
        if profile_id == PROFILE_CANDIDATE_FASTER_WARMUP:
            return {
                "id": PROFILE_CANDIDATE_FASTER_WARMUP,
                "frozen": False,
                "is_default": False,
                "based_on": PROFILE_DEFAULT,
                "overrides": {"warmup_min_events": self.profile_candidate_warmup_min_events},
            }
        return None

    def profile_registry(self) -> list[dict]:
        """Every REGISTERED profile's descriptor, in registration order (``default`` first, then
        each candidate) — the full ``GET /research/profiles`` list. Built ENTIRELY from
        ``profile_definition`` (never a second copy of any id or override value)."""
        return [self.profile_definition(pid) for pid in _PROFILE_IDS_IN_ORDER]

    def resolved_for_profile(self, profile_id: str) -> "Config | None":
        """The per-run ``Config`` for ``profile_id`` — applied ONLY inside a fresh backtest engine
        for that one run (never the shared ``CONFIG`` singleton, never a cockpit/engine path
        outside a backtest's own ``profile`` request param — enforced by a source-scan test).

        ``default`` returns ``self`` UNCHANGED — the identical object, not merely an equal copy
        (the strongest possible byte-identical guarantee: the frozen-default anti-goal). A
        registered candidate returns a FRESH ``dataclasses.replace(self, **overrides)`` — self is
        never mutated. An unregistered id returns ``None`` (the route already 422s before this is
        ever called for an unknown profile — defensive here, never silently substitutes
        ``default``)."""
        definition = self.profile_definition(profile_id)
        if definition is None:
            return None
        if profile_id == PROFILE_DEFAULT:
            return self
        return replace(self, **definition["overrides"])

    def strategy_definition(self, strategy_id: str) -> dict | None:
        """The COMPLETE config-owned strategy definition for ``strategy_id`` (Data Contract row 34).

        The SINGLE owner of the v1 strategy grammar: the backtest runner READS this (never a
        restated copy) and echoes it VERBATIM into every report's provenance. Only
        ``STRATEGY_V1_ID`` is registered; any other id returns ``None`` (the route maps that to an
        explicit 422 — never a silently-coerced default strategy).

        v1 declares, entirely from named config values (no inline threshold anywhere):
          * ENTRIES — the EXISTING state-native setup arming (the studies' sustained-premise rule):
            setup type x direction over ``trend_continuation`` / ``absorption_reversal``, long and
            short, gated by the REUSED ``study_arm_sustain_seconds`` / ``study_arm_cooldown_seconds``
            constants. One open trade at a time (``one_open_trade``): while a simulated position is
            open no new entry arms, and concurrent eligibility resolves in the declared setup order.
            The two level setups (``level_break`` / ``failed_move_fade``) are NOT in v1 — they
            require an operator-supplied hindsight level and have no state-native arming.
          * EXITS — invalidation R-stop (the studies' arm-instant synthetic invalidation:
            ``study_occurrence_r_spread_multiple`` x arm spread, floored at
            ``study_occurrence_r_floor``, on the adverse side; R via the shared ``marks.r_basis``);
            the ``strategy_exit_horizon_seconds`` time horizon; state-flip (the OPPOSING control
            state reads — the existing state vocabulary, resolved by the runner through the studies'
            one state-mapping helper); and the explicit deterministic ``dataset_end`` forced exit at
            the last recorded price for a trade still open at stream end.
          * FEE MODEL — ``strategy_fee_per_share`` with ``strategy_fee_min_per_trade`` per fill.
          * SLIPPAGE MODEL — ``strategy_slippage_spread_fraction`` of the recorded spread, adverse
            at each fill.
          * DOLLAR CONVERSION — the fixed ``strategy_dollars_per_r`` notional.
        """
        if strategy_id != STRATEGY_V1_ID:
            return None
        return {
            "strategy_id": STRATEGY_V1_ID,
            "entries": {
                "rule": "state_native_sustained_premise",
                "setups": [
                    {"setup_type": "trend_continuation", "direction": "long"},
                    {"setup_type": "trend_continuation", "direction": "short"},
                    {"setup_type": "absorption_reversal", "direction": "long"},
                    {"setup_type": "absorption_reversal", "direction": "short"},
                ],
                "arm_sustain_seconds": self.study_arm_sustain_seconds,
                "arm_cooldown_seconds": self.study_arm_cooldown_seconds,
                "concurrency": "one_open_trade",
            },
            "exits": {
                "r_stop": {
                    "rule": "synthetic_invalidation_at_arm",
                    "spread_multiple": self.study_occurrence_r_spread_multiple,
                    "floor": self.study_occurrence_r_floor,
                },
                "horizon_seconds": self.strategy_exit_horizon_seconds,
                "state_flip": {"rule": "opposing_control_state"},
                "dataset_end": {"rule": "forced_exit_at_last_recorded_price"},
            },
            "fees": {
                "per_share": self.strategy_fee_per_share,
                "min_per_trade": self.strategy_fee_min_per_trade,
            },
            "slippage": {"spread_fraction": self.strategy_slippage_spread_fraction},
            "dollars_per_r": self.strategy_dollars_per_r,
        }

    def window_label(self, window: int) -> str:
        return f"{window}s"

    @property
    def primary_window_label(self) -> str:
        return self.window_label(self.primary_window)

    def journal_db_path_resolved(self) -> str:
        """The effective journal DB path: the ``TAPEOLOGY_JOURNAL_DB`` env var if set, else the
        config default. Read at store-construction time so an operator can point persistence at a
        real file without code change, while tests inject a temp path via dependency-override."""
        return os.environ.get("TAPEOLOGY_JOURNAL_DB", self.journal_db_path)

    def dataset_dir_resolved(self) -> str:
        """The effective dataset-store directory: the ``TAPEOLOGY_DATASET_DIR`` env var if set,
        else the package-anchored config default (the ``journal_db_path_resolved`` pattern). Read
        at store-construction time so an operator can point the dataset store at a real location
        without code change, while tests point it at a temp dir via the env var."""
        return os.environ.get("TAPEOLOGY_DATASET_DIR", self.dataset_dir)

    def bar_dir_resolved(self) -> str:
        """The effective bar-store directory: the ``TAPEOLOGY_BAR_DIR`` env var if set, else the
        package-anchored config default (the ``dataset_dir_resolved`` pattern, era-4 J-01). Read at
        store-construction time so an operator can point the bar store at a real location without
        code change, while tests point it at a temp dir via the env var."""
        return os.environ.get("TAPEOLOGY_BAR_DIR", self.bar_dir)

    def config_fingerprint(self) -> str:
        """A stable hash over the ENTIRE frozen config (capability 28 / honesty stamps).

        Every research record carries this so results are NEVER silently compared across different
        thresholds: a verdict depends transitively on every classifier threshold, so the fingerprint
        spans the whole config dataclass (classifier + research values), not a hand-picked subset.

        Properties (asserted by the unit matrix):
          * **Stable across runs / processes** — derived only from the config field values (sorted,
            JSON-serialized), never from object identity, ordering noise, or wall-clock.
          * **Changes when ANY config value changes** — a different threshold yields a different
            hash, so two records under different configs can never be silently pooled.
        Operational store-tuning fields (the journal DB path / busy timeout) are EXCLUDED: they do
        not affect any engine/verdict computation, so two journals that differ only in where they
        live must share a fingerprint (else every temp-path test would mint a unique one). The
        journal LIST page-size fields (``journal_list_default_limit`` / ``journal_list_max_limit``)
        are EXCLUDED for the same reason: a serving page size touches no persisted research value, so
        two journals identical in every threshold but served at different page sizes MUST share a
        fingerprint (else their analytics pools would be dishonestly fragmented). The analytics
        min-sample threshold (``analytics_min_sample_size``) is EXCLUDED for the identical reason
        (capability 31 / J-59): it is a serving/presentation-only display gate that touches no
        persisted research value, so two journals identical in every threshold but viewed at
        different min-sample sizes MUST share a fingerprint (else fragmenting the very pools the
        analytics surface exists to compare). The dense-replay CI timing budget
        (``dense_replay_time_budget_seconds``) is EXCLUDED for the identical reason (capability 34 /
        J-62): a CI gate value touches no persisted research value, so two journals identical in every
        threshold but run under different CI budgets MUST share a fingerprint. The management-stance
        dwell (``management_stance_dwell_seconds``) is EXCLUDED for the identical reason (capability
        27 / J-53): the stance is a live cue that is NEVER PERSISTED (schema stays v7), so a stance
        timing value touches no persisted research value and two journals identical in every threshold
        but served at different stance dwells MUST share a fingerprint.
        """
        excluded = {
            "journal_db_path",
            "journal_busy_timeout_ms",
            "journal_schema_version",
            # The dataset-store directory (era-3 capability 1, J-02): an operational storage
            # location with the ``journal_db_path`` discipline — it cannot affect any persisted
            # research value (a dataset's CONTENT is checksummed; where the file lives is not),
            # and the package-anchored default embeds an absolute path that would otherwise mint
            # a different fingerprint per machine. Pinned by a fingerprint-stability test + the
            # real-threshold counter-test in tests/test_datasets.py.
            "dataset_dir",
            # The bar-store directory (era-4 capability 1, J-01): the identical ``dataset_dir``
            # storage-location discipline — it cannot affect any persisted research value, and the
            # package-anchored default embeds an absolute path that would otherwise mint a
            # different fingerprint per machine. Pinned by a fingerprint-stability test + the
            # real-threshold counter-test in tests/test_bars.py.
            "bar_dir",
            # The bar-timeframe validation allowlist + the free-tier recency-delay/rate-throttle
            # parameters (era-4 capability 1, J-01): none of these shape any persisted
            # tape/backtest/study value — they only govern an unrelated, brand-new bar-storage
            # capability's ``?timeframe=`` validation and vendor-fetch mechanics (which real bars a
            # fetch can reach, and how fast consecutive vendor calls may run). Two journals
            # identical in every threshold but configured with different bar-fetch mechanics MUST
            # share a fingerprint. Pinned by a fingerprint-stability test + the real-threshold
            # counter-test in tests/test_bars.py.
            "bar_timeframes",
            "bar_recency_delay_seconds",
            "bar_rate_limit_per_minute",
            # The S/R level-detection parameters (era-4 capability 2, J-02): ``levels`` is a
            # SEPARATE research computation from the tape engine / backtest / PnL-ledger /
            # thesis-verdict pipeline this fingerprint stamps onto every persisted record for
            # never-pool-across-fingerprints honesty -- a level is never itself stamped with (or
            # compared across) a ``config_fingerprint`` anywhere. Two journals identical in every
            # FINGERPRINTED threshold but configured with different pivot lookback / touch
            # tolerance / timeframe weights MUST share a fingerprint (else every temp-config test
            # of these brand-new, unrelated parameters would mint a different fingerprint and
            # falsely fragment the tape/backtest/PnL pools those OTHER thresholds exist to
            # protect) -- the identical ``bar_timeframes`` rationale directly above, applied to a
            # different brand-new capability. Pinned by a fingerprint-stability test + the
            # real-threshold counter-test in ``tests/test_levels.py``.
            "sr_pivot_lookback",
            "sr_touch_tolerance_bps",
            "sr_timeframe_weights",
            "journal_list_default_limit",
            "journal_list_max_limit",
            "analytics_min_sample_size",
            # The dense-replay CI timing budget (capability 34 / J-62): a CI GATE value that never
            # enters any persisted research computation, so two journals identical in every threshold
            # but run under different CI budgets MUST share a fingerprint (else fragmenting the
            # analytics pools). Same iter-12/iter-16 precedent as the serving/display fields above.
            "dense_replay_time_budget_seconds",
            # The study-list page size (capability 32 / J-60): a SERVING-ONLY value that never enters
            # any persisted study computation (it touches no occurrence, R basis, baseline, or stamp),
            # so two journals identical in every threshold but served at different study-list page sizes
            # MUST share a fingerprint. Same iter-12 page-size precedent (``journal_list_*`` above). The
            # FIVE other new study keys (``study_null_arm_count``, ``study_arm_sustain_seconds``,
            # ``study_arm_cooldown_seconds``, ``study_occurrence_r_spread_multiple``,
            # ``study_occurrence_r_floor``, ``study_null_baseline_seed``) are DELIBERATELY NOT excluded
            # — they shape the persisted study results, so they MOVE the fingerprint (the intended
            # never-pool-across-fingerprints honesty mechanism).
            "study_list_max",
            # The management-stance dwell (capability 27 / J-53): the stance is a live cue that is
            # NEVER PERSISTED (schema stays v7 — no stance row exists), so this timing value touches no
            # persisted research value (no verdict, feature, grade, excursion, or stamp). It is
            # therefore serving-only and EXCLUDED by the same iter-12/iter-16 precedent — two journals
            # identical in every threshold but served at different stance dwells MUST share a
            # fingerprint. Pinned by a fingerprint-stability test + the real-threshold counter-test.
            "management_stance_dwell_seconds",
            # The entry-checklist stance dwell (capability 33 / J-63): the checklist + its aggregate
            # stance are a live cue NEVER PERSISTED (schema stays v7 — no checklist row exists), so this
            # timing value touches no persisted research value. Serving-only, EXCLUDED by the identical
            # iter-12/16/20 precedent (the ``management_stance_dwell_seconds`` sibling above). Pinned by
            # a fingerprint-stability test + the real-threshold counter-test.
            "checklist_stance_dwell_seconds",
            # The delivery-lag bound (capability 22 row 14 / J-63): the ``tape_lag_ok`` check it gates is
            # part of the never-persisted checklist, and ``delivery_lag_seconds`` is feeder-owned
            # DELIVERY metadata that never enters any persisted research value. Serving-only, EXCLUDED by
            # the identical precedent. Pinned by a fingerprint-stability test + the real-threshold
            # counter-test.
            "delivery_lag_ok_bound_seconds",
            # The hint-log page size (capability 33 / J-65): a SERVING-ONLY value that never enters any
            # persisted hint computation (it touches no hint record, evidence, citation, or stamp), so
            # two journals identical in every threshold but served at different hint-log page sizes MUST
            # share a fingerprint. Same iter-12 page-size precedent (``journal_list_*`` / ``study_list_max``
            # above). The TWO hint timing keys (``hint_sustain_dwell_seconds`` / ``hint_cooldown_seconds``)
            # are DELIBERATELY NOT excluded — they shape WHICH hint records get persisted, so they MOVE
            # the fingerprint (the intended never-pool-across-fingerprints honesty mechanism; the
            # study-arm-sustain / study-arm-cooldown precedent).
            "hint_log_max",
            # The sound-cue cooldown (capability 33 / J-66): the OPTIONAL sound cue is a CLIENT-LOCAL UI
            # preference that is NEVER PERSISTED (schema stays v7 — no cue row exists), so this
            # serving-only debounce value touches NO persisted research value (no verdict, feature,
            # grade, excursion, stamp, hint, or study). Serving-only, EXCLUDED by the identical
            # iter-12/16/20/23 precedent (the ``hint_log_max`` / serving dwell siblings above) — two
            # journals identical in every threshold but served at different cue cooldowns MUST share a
            # fingerprint. Pinned by a fingerprint-stability test + the real-threshold counter-test.
            "sound_cue_cooldown_seconds",
            # The backtest-list page size (era-3 capability 4 / J-03): a SERVING-ONLY value that never
            # enters any persisted backtest computation (it touches no trade, fill, aggregate, null
            # baseline, or stamp), so two journals identical in every threshold but served at
            # different backtest-list page sizes MUST share a fingerprint. Same iter-12 page-size
            # precedent (``journal_list_*`` / ``study_list_max`` / ``hint_log_max`` above). The SEVEN
            # other new J-03 keys (``strategy_exit_horizon_seconds``, ``strategy_fee_per_share``,
            # ``strategy_fee_min_per_trade``, ``strategy_slippage_spread_fraction``,
            # ``strategy_dollars_per_r``, ``backtest_null_entry_count``,
            # ``backtest_null_baseline_seed``) are DELIBERATELY NOT excluded — they shape the
            # persisted backtest reports, so they MOVE the fingerprint (the intended
            # never-pool-across-fingerprints honesty mechanism; the study-keys precedent).
            "backtest_list_max",
            # The PnL-ledger "insufficient sample" LABEL minimum (era-3 capability 5 / J-04): a
            # SERVING / PRESENTATION-ONLY threshold by the documented ``analytics_min_sample_size``
            # precedent above — it changes only which ledger splits get LABELED at read, never any
            # persisted ledger value (rows store verbatim copies of the row-31 aggregates whatever
            # this reads). Two journals identical in every threshold but viewed at different label
            # minimums MUST share a fingerprint. The founding-row identity values
            # (``pnl_founding_enhancement_id`` / ``pnl_founding_enhancement_title``) and the
            # founding windows (``pnl_founding_train_window`` / ``pnl_founding_holdout_window``)
            # are DELIBERATELY NOT excluded — they are persisted verbatim into (or select the data
            # measured by) the founding ledger row, so they MOVE the fingerprint (the intended
            # never-pool honesty mechanism). Pinned both ways in tests/test_pnl_ledger.py.
            "pnl_min_sample_size",
            # The candidate-sweep PROMOTION minimum-n gate (era-3 capability 7 / J-07): a
            # presentation/decision-only threshold by the identical ``pnl_min_sample_size``
            # discipline directly above — it decides WHICH candidate may be promoted, never the
            # CONTENT of any persisted trade, fill, or aggregate (a promoted row stores the same
            # verbatim backtest aggregates whatever this floor reads). Two journals identical in
            # every threshold but configured with a different promotion floor MUST share a
            # fingerprint. See the field's own docstring for the full judgment-call rationale.
            "promotion_min_sample_size",
            # The PnL-history markdown target path (era-3 capability 5 / J-04): an operational
            # storage location with the ``journal_db_path`` / ``dataset_dir`` discipline — WHERE
            # the pure render is written cannot affect any persisted research value, and the
            # package-anchored default embeds an absolute path that would otherwise mint a
            # different fingerprint per machine. Pinned in tests/test_pnl_ledger.py.
            "pnl_history_md_path",
            # The candidate profile's registry-metadata override value (era-3 capability 2 /
            # J-06): NEVER itself read by engine/classifier code — ``resolved_for_profile``
            # overlays it onto the REAL ``warmup_min_events`` field, and it is THAT (never
            # excluded) field which moves the fingerprint for a candidate-resolved Config. Unlike
            # the founding-row identity values above (persisted VERBATIM into a ledger row, so
            # NOT excluded), this value is only ever READ to build a per-run overlay — it is
            # itself never persisted anywhere, so two journals identical in every threshold but
            # carrying a different (unapplied) candidate override value MUST share a fingerprint.
            # Pinned both ways in tests/test_profile_equivalence.py.
            "profile_candidate_warmup_min_events",
        }
        payload = {k: v for k, v in asdict(self).items() if k not in excluded}
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


# The one shared instance read by engine, classifier, API, and tests.
CONFIG = Config()
