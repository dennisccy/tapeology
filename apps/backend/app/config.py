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
from dataclasses import asdict, dataclass, field


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
    # Excluded from ``config_fingerprint`` (see the exclusion set below): a migration must NOT change
    # the fingerprint — verdicts depend on classifier thresholds, never on where/how the DB is stored.
    journal_schema_version: int = 3

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
        live must share a fingerprint (else every temp-path test would mint a unique one).
        """
        excluded = {"journal_db_path", "journal_busy_timeout_ms", "journal_schema_version"}
        payload = {k: v for k, v in asdict(self).items() if k not in excluded}
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


# The one shared instance read by engine, classifier, API, and tests.
CONFIG = Config()
