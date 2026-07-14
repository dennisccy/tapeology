# Iteration diff (bounded)

Files changed: 11. Shown in full: 10.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_edge_report.py` (11 lines not shown)

```diff
diff --git a/README.md b/README.md
index 4238547..1a5781f 100644
--- a/README.md
+++ b/README.md
@@ -80,6 +80,7 @@ Current capabilities:
 - **structure_tape-vs-v1 comparison on the Structure page** — beneath the Registry section, a Comparison section lets you choose a registered dataset and run both `structure_tape` and the champion strategy `v1` over it as an offline research job (it places nothing and never touches an order path); each side's progress is shown independently as it moves from Queued to Running (with a live count of events processed) to Done, and the two result cards populate automatically once both finish, with no manual refresh. It then shows both strategies' results side by side: trade count, net return in R and dollars, win rate, and maximum drawdown — a strategy that took zero trades shows an honest "no trades (n=0)" instead of a misleading zero — plus a per-class A/B/C breakdown of the same figures with an explicit "insufficient sample" label wherever a class has too few trades to trust. The always-visible "simulated — assumed fees/slippage — not indicative of live results" register is shown exactly as the backend serves it, never a rephrased copy. A read-only Champion panel beside the results confirms the champion is unaffected — this comparison never promotes a strategy or writes to the PnL ledger, no matter what it finds — and a Founding baseline panel shows the ledger's first recorded row for reference. Every number is read verbatim from the same backtest report the research API and command-line tool already serve. On the committed keyless sample data this honestly shows `structure_tape` arming too few (or zero) trades to trust a result, exactly the "not enough evidence yet" finding the underlying research tool already reports — the champion stays `v1` on `default`. No datasets registered, a comparison still running, a failed or cancelled run, and the backend being unreachable each show their own distinct, explicit message rather than a blank or guessed result.
 - **Tradable level map (research API)** — distills a symbol's raw support/resistance levels (which can number in the thousands for a heavily traded stock) down to at most 10 price "bands" total — the handful of price zones actually worth marking on a chart. Each band carries its price range, whether it is support or resistance, a quality score, how many underlying levels back it up, whether it sits on a psychologically "round" price, and an inherited A/B/C conviction class where one applies. The map for any given day is built using only data fully available before that trading day started — mirroring how a trader marks up charts before the open — with weekends and market holidays handled automatically by falling back to whichever trading day actually closed last. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
 - **Touch-event scanner and case-study registry (research API)** — walks every stored trading session in a 12-symbol panel's recorded price history and checks each session's actual price action against that session's own tradable level map, built strictly from data available before the session opened, so a later session's data can never change an earlier one's already-recorded result. Every genuine touch of a band is logged with its outcome — rejected and turned away, broken straight through, or chopped near the wall with no clear outcome — together with how far price moved by two later checkpoints. Run against real, freshly fetched price history for the full panel, the registry already holds several hundred touch events across all 12 symbols, a healthy mix of breakouts, rejections, and chops, with identical requests always returning byte-identical results. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
+- **Real tape recorded and joined at wall-touch events (command-line research tool + research API)** — with market-data vendor credentials configured, a dedicated recording tool captures a real trade-by-trade market-data window (an hour before through 90 minutes after) around the best-scoring touch events from the case-study registry, spreading its picks across as many different stocks as possible and always including the project's pinned reference example. Once a touch event has a matching real recording, opening that event's detail view replays the frozen tape-reading engine over the recording and attaches a timeline of what buyers and sellers were actually doing around the touch — for example, sellers absorbing at the ask right before a rejection, or buyers in control through a break. Events with no matching recording show an honestly empty timeline rather than an invented one. A committed real-data sample keeps this timeline check running with no credentials required. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
 - **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `POST /research/thesis`, `GET /research/thesis/active`, `GET /research/taxonomy`, `GET /research/analytics`, `GET /research/journal`, `GET /research/journal/{id}`, `POST /research/thesis/{id}/action`, `GET /research/studies`, `POST /research/studies`, `POST /research/studies/{id}/cancel`, `GET /research/hints/active`, `GET /research/hints`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/levels`, `GET /research/tradability`, `GET /research/setups`, `GET /research/setups/{id}`, `GET /meta/ui-routes`.
 - **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, journal, studies, datasets, backtests, strategy registry, PnL ledger, bar series, support/resistance levels, tradable level maps, touch-event case studies, and navigation data a person sees. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
 <!-- /AUTO:capabilities -->
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index b10d90d..6dd9d1c 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -28,6 +28,18 @@ STRATEGY_V1_ID = "v1"
 # out of scope this iteration) — registering structure_tape here never mutates v1's own branch.
 STRATEGY_TAPE_ID = "structure_tape"
 
+# THE SECOND additive strategy candidate (era-5B capability 5, J-04; Data Contract row "edge-report
+# cells") — the IDENTICAL "id constant + Config-owned definition method" pattern, registered BESIDE
+# v1/structure_tape in the strategy registry. ``strategy_definition`` below returns the EXACT SAME
+# grammar dict for this id as it does for ``STRATEGY_TAPE_ID`` (same entry/exit/fee/slippage/
+# size-scaling fields, verbatim, no new magic number) — the two ids share one branch. What differs
+# is NEVER the grammar; it is which candidates the backtest runner (``research/backtests.py``) arms
+# against: ``structure_tape`` reads raw classified levels/zones (``research/levels.py``),
+# ``structure_tape_map`` reads the derived tradable-map BANDS (``research/tradability.py``) instead
+# — a lens over the identical archetype, never a re-tuning of it. v1 and structure_tape stay
+# byte-identical (equivalence-tested); registering this id never mutates either of their branches.
+STRATEGY_TAPE_MAP_ID = "structure_tape_map"
+
 # The frozen legacy profile (era-3 capability 2, J-06; Data Contract row 33) — the SAME
 # "id constant + Config-owned definition method" pattern as STRATEGY_V1_ID above governs both the
 # strategy grammar (row 34, ``strategy_definition``) and the profile registry (row 33,
@@ -51,10 +63,10 @@ PROFILE_CANDIDATE_FASTER_WARMUP = "candidate-faster-warmup"
 _PROFILE_IDS_IN_ORDER: tuple[str, ...] = (PROFILE_DEFAULT, PROFILE_CANDIDATE_FASTER_WARMUP)
 
 # Registration order for the strategy registry projection (``Config.strategy_registry`` — era-4
-# J-04) — the IDENTICAL ``_PROFILE_IDS_IN_ORDER`` pattern applied to strategies: private, external
-# callers go through ``strategy_definition`` (single lookup) or ``strategy_registry`` (the full
-# list), never this tuple directly.
-_STRATEGY_IDS_IN_ORDER: tuple[str, ...] = (STRATEGY_V1_ID, STRATEGY_TAPE_ID)
+# J-04, era-5B J-04 adds ``structure_tape_map``) — the IDENTICAL ``_PROFILE_IDS_IN_ORDER`` pattern
+# applied to strategies: private, external callers go through ``strategy_definition`` (single
+# lookup) or ``strategy_registry`` (the full list), never this tuple directly.
+_STRATEGY_IDS_IN_ORDER: tuple[str, ...] = (STRATEGY_V1_ID, STRATEGY_TAPE_ID, STRATEGY_TAPE_MAP_ID)
 
 
 @dataclass(frozen=True)
@@ -1440,12 +1452,13 @@ class Config:
 
     def strategy_definition(self, strategy_id: str) -> dict | None:
         """The COMPLETE config-owned strategy definition for ``strategy_id`` (Data Contract row 34;
-        ``structure_tape`` is row 41, era-4 J-04).
+        ``structure_tape`` is row 41, era-4 J-04; ``structure_tape_map`` is era-5B J-04).
 
         The SINGLE owner of every registered strategy's grammar: the backtest runner READS this
         (never a restated copy) and echoes it VERBATIM into every report's provenance. Only
-        ``STRATEGY_V1_ID`` and ``STRATEGY_TAPE_ID`` are registered; any other id returns ``None``
-        (the route maps that to an explicit 422 — never a silently-coerced default strategy).
+        ``STRATEGY_V1_ID``, ``STRATEGY_TAPE_ID``, and ``STRATEGY_TAPE_MAP_ID`` are registered; any
+        other id returns ``None`` (the route maps that to an explicit 422 — never a
+        silently-coerced default strategy).
 
         v1 declares, entirely from named config values (no inline threshold anywhere):
           * ENTRIES — the EXISTING state-native setup arming (the studies' sustained-premise rule):
@@ -1486,10 +1499,20 @@ class Config:
             model, and fixed ``strategy_dollars_per_r`` notional.
           * SIZE — ``size_multiple_by_class`` (``structure_tape_size_multiple_by_class``, era-4
             J-05) scales the v1-identical ``dollars_per_r`` notional by the arming level's class.
+
+        ``structure_tape_map`` (era-5B capability 5, J-04; Data Contract row "edge-report cells")
+        returns the EXACT SAME dict as ``structure_tape`` above — same branch, same six
+        ``structure_tape_*`` config fields read verbatim, no new magic number, the only difference
+        the ``strategy_id`` key itself. The grammar (entry/exit/fee/slippage/size rules) is
+        identical; what genuinely differs lives OUTSIDE this method, in the backtest runner's
+        arming dispatch (``research/backtests.py``): ``structure_tape`` arms against raw classified
+        levels/zones (``research/levels.py``), ``structure_tape_map`` arms against the DERIVED
+        tradable-map bands (``research/tradability.py``) instead — a new lens over the identical
+        archetype, never a second grammar to keep in sync.
         """
-        if strategy_id == STRATEGY_TAPE_ID:
+        if strategy_id in (STRATEGY_TAPE_ID, STRATEGY_TAPE_MAP_ID):
             return {
-                "strategy_id": STRATEGY_TAPE_ID,
+                "strategy_id": strategy_id,
                 "entries": {
                     "rule": "structure_level_tape_confirmation",
                     "proximity_band_bps": self.structure_tape_proximity_band_bps,
@@ -1555,9 +1578,10 @@ class Config:
 
     def strategy_registry(self) -> list[dict]:
         """Every REGISTERED strategy's descriptor, in registration order (``v1`` first, then
-        ``structure_tape``) — the full ``GET /research/strategies`` list (era-4 J-04; Data
-        Contract row 40). Built ENTIRELY from ``strategy_definition`` (never a second copy of any
-        id or grammar value) — the identical ``profile_registry`` pattern applied to strategies."""
+        ``structure_tape``, then ``structure_tape_map``) — the full ``GET /research/strategies``
+        list (era-4 J-04; era-5B J-04 adds ``structure_tape_map``; Data Contract row 40). Built
+        ENTIRELY from ``strategy_definition`` (never a second copy of any id or grammar value) —
+        the identical ``profile_registry`` pattern applied to strategies."""
         return [self.strategy_definition(sid) for sid in _STRATEGY_IDS_IN_ORDER]
 
     def window_label(self, window: int) -> str:
@@ -1823,20 +1847,23 @@ class Config:
             # Pinned both ways in tests/test_profile_equivalence.py.
             "profile_candidate_warmup_min_events",
             # The structure_tape strategy's own config fields (era-4 capability 4, J-04; era-4
-            # capability 5, J-05 adds the class-scaled stop/reward/size fields on the SAME basis): a
-            # SEPARATE, additive strategy registered beside the frozen v1 — read ONLY when
-            # structure_tape itself is selected (never by a v1 backtest, the tape engine, or any
-            # study/PnL-ledger computation this fingerprint stamps onto every persisted record for
+            # capability 5, J-05 adds the class-scaled stop/reward/size fields on the SAME basis) —
+            # ALSO read verbatim by the era-5B ``structure_tape_map`` strategy (J-04), which shares
+            # this EXACT SAME six-field grammar (see ``strategy_definition`` above: one branch,
+            # keyed by either id) and introduces NO field of its own: a SEPARATE, additive strategy
+            # registered beside the frozen v1 — read ONLY when structure_tape or structure_tape_map
+            # itself is selected (never by a v1 backtest, the tape engine, or any study/PnL-ledger
+            # computation this fingerprint stamps onto every persisted record for
             # never-pool-across-fingerprints honesty), so their mere presence on ``Config`` must
             # NOT move the frozen ``default``-profile/``v1``-strategy fingerprint this hash is
             # pinned to (the identical ``sr_*`` rationale above, applied to a different brand-new,
             # unrelated strategy). Two journals identical in every FINGERPRINTED threshold but
             # configured with a different proximity band, tape-confirmation mapping, class-scaled
-            # stop, reward target, or size multiple MUST share a fingerprint. A structure_tape
-            # report's OWN class-scaled config is instead provenanced by the full ``strategy`` dict
-            # each report already embeds verbatim (never by ``config_fingerprint``, which stays
-            # scoped to the frozen default/v1 threshold set). Pinned by a fingerprint-stability test
-            # + the real-threshold counter-test in tests/test_backtests.py.
+            # stop, reward target, or size multiple MUST share a fingerprint. A structure_tape /
+            # structure_tape_map report's OWN class-scaled config is instead provenanced by the full
+            # ``strategy`` dict each report already embeds verbatim (never by ``config_fingerprint``,
+            # which stays scoped to the frozen default/v1 threshold set). Pinned by a
+            # fingerprint-stability test + the real-threshold counter-test in tests/test_backtests.py.
             "structure_tape_proximity_band_bps",
             "structure_tape_rejection_state_by_direction",
             "structure_tape_breakthrough_state_by_direction",
diff --git a/apps/backend/app/mcp/__init__.py b/apps/backend/app/mcp/__init__.py
index b649cae..ab472fe 100644
--- a/apps/backend/app/mcp/__init__.py
+++ b/apps/backend/app/mcp/__init__.py
@@ -17,8 +17,8 @@ Result contract (locked by ``tests/test_mcp_server.py``):
     <path>"``, ``isError`` true. Every registered tool's endpoint has shipped (``datasets`` at
     (era-3) J-02, ``backtests`` at J-03, ``pnl_ledger`` at J-04; ``/research/profiles`` — reached
     via ``get_endpoint`` — at J-05; ``bars`` at era-4 J-01; ``levels`` at era-4 J-02; ``strategies``
-    at era-4 J-04; ``tradability`` at era-5B J-01; ``setups`` at era-5B J-02); an
-    allowlisted-but-UNKNOWN path (any unshipped
+    at era-4 J-04; ``tradability`` at era-5B J-01; ``setups`` at era-5B J-02; ``edge_report`` at
+    era-5B J-04); an allowlisted-but-UNKNOWN path (any unshipped
     ``/research/*``) still surfaces the backend's honest 404 this way — never placeholder data.
   * backend unreachable — an explicit tool error naming the base URL and the failure
     (``BackendUnreachableError``); NEVER cached or fabricated data (no cache, no retry loop,
@@ -100,6 +100,10 @@ _STATIC_PATHS: dict[str, str] = {
     # `symbol`/`reaction`/`band_class` filters are NOT exposed here -- this tool always proxies the
     # UNFILTERED list, byte-identical to `GET /research/setups` with no query string.
     "setups": "/research/setups",
+    # `edge_report` (era-5B J-04) is the IDENTICAL no-required-param shape: the 3-way
+    # strategy-comparison report takes no query params at all -- it aggregates over the WHOLE
+    # registered dataset registry on its own.
+    "edge_report": "/research/edge-report",
 }
 
 _TAPE_PATHS: dict[str, str] = {
@@ -272,6 +276,20 @@ TOOLS: tuple[types.Tool, ...] = (
         ),
         inputSchema=_object_schema({}),
     ),
+    types.Tool(
+        name="edge_report",
+        description=(
+            "Read-only proxy of GET /research/edge-report -- the 3-way strategy-comparison report "
+            "(v1 vs the frozen structure_tape vs the additive structure_tape_map) aggregated into "
+            "per strategy x class x side x reaction x feed cells over every registered "
+            "event-window dataset that resolves an owning, classified touch event (n, gross/net R "
+            "and $, win rate, max drawdown, a seeded null baseline, and an insufficient_sample "
+            "label below the configured minimum n), plus a ranked list of train cells clearing the "
+            "positivity gate with their own hold-out status -- JSON verbatim. Never pools across "
+            "feeds, and never pools train with hold-out."
+        ),
+        inputSchema=_object_schema({}),
+    ),
     types.Tool(
         name="pnl_ledger",
         description=(
diff --git a/apps/backend/app/research/backtests.py b/apps/backend/app/research/backtests.py
index d7e57b6..fd898af 100644
--- a/apps/backend/app/research/backtests.py
+++ b/apps/backend/app/research/backtests.py
@@ -36,12 +36,13 @@ The disciplines, clause by clause:
     studies' arm-instant synthetic invalidation (the REUSED ``_synthetic_invalidation`` helper —
     ``study_occurrence_r_spread_multiple`` x arm spread, floored at ``study_occurrence_r_floor``,
     adverse side), with R via the shared ``marks.r_basis`` (row 27 — never a second formula); it
-    triggers on a recorded print at/through the invalidation. ``structure_tape`` trades ONLY
-    (era-4 J-05, gated on the arming ``level``/class being present) instead use a class-scaled,
-    LEVEL-relative invalidation (``_class_scaled_invalidation``) and additionally carry a
-    reward-target exit (``_class_scaled_target`` — a class R-multiple bounded by the next opposing
-    level resolved at arm time); v1/null trades never carry a ``target_price`` and so can never
-    reach that exit. The state-flip exit fires when the tape reads the OPPOSING control state (the
+    triggers on a recorded print at/through the invalidation. ``structure_tape`` AND
+    ``structure_tape_map`` trades (era-4 J-05 / era-5B J-04, gated on the arming ``level``/class
+    being present, never on the strategy id) instead use a class-scaled, LEVEL-relative
+    invalidation (``_class_scaled_invalidation``) and additionally carry a reward-target exit
+    (``_class_scaled_target`` — a class R-multiple bounded by the next opposing level/band resolved
+    at arm time); v1/null trades never carry a ``target_price`` and so can never reach that exit.
+    The state-flip exit fires when the tape reads the OPPOSING control state (the
     studies' ``_control_state`` vocabulary). The time horizon exits at the first recorded event
     at/after ``strategy_exit_horizon_seconds`` past entry. A trade still open when the stream ends
     is handled EXPLICITLY and deterministically: forced exit at the LAST recorded price, labeled
@@ -55,13 +56,13 @@ The disciplines, clause by clause:
     contributes zero slippage — honest absence, never a fabricated cost). Each fill pays
     ``max(strategy_fee_per_share x shares, strategy_fee_min_per_trade)``. Position size is the
     fixed notional: ``shares = strategy_dollars_per_r / R basis`` (v1/null); ``structure_tape``
-    trades (era-4 J-05) scale that SAME fixed notional by the arming level's class size multiple
-    (``structure_tape_size_multiple_by_class``) — still a per-trade SIMULATED notional only. R and
-    $ are two disclosed unit systems over the SAME measurement — GROSS from recorded prices, NET
-    from fills minus fees, and a dollar figure never exists without its R counterpart. The
-    per-class (A/B/C) PnL breakdown (era-4 J-05, Data Contract row 42) partitions the SAME trade
-    population by ``trade["level"]["class"]`` — computed once, alongside the strategy-level
-    aggregate, and served verbatim.
+    AND ``structure_tape_map`` trades (era-4 J-05 / era-5B J-04) scale that SAME fixed notional by
+    the arming level's class size multiple (``structure_tape_size_multiple_by_class``) — still a
+    per-trade SIMULATED notional only. R and $ are two disclosed unit systems over the SAME
+    measurement — GROSS from recorded prices, NET from fills minus fees, and a dollar figure never
+    exists without its R counterpart. The per-class (A/B/C) PnL breakdown (era-4 J-05, Data
+    Contract row 42) partitions the SAME trade population by ``trade["level"]["class"]`` —
+    computed once, alongside the strategy-level aggregate, and served verbatim.
 
   * **The seeded random-entry null baseline.** ``backtest_null_entry_count`` entry instants (and
     per-entry random directions) drawn from the recorded seed over the SAME dataset, exiting
@@ -93,12 +94,13 @@ import threading
 import time
 import uuid
 
-from ..config import Config, PROFILE_DEFAULT, STRATEGY_TAPE_ID
+from ..config import Config, PROFILE_DEFAULT, STRATEGY_TAPE_ID, STRATEGY_TAPE_MAP_ID
 from .bars import BarStore
 from .datasets import DatasetIntegrityError, DatasetNotFound, DatasetStore
 from .levels import compute_levels, CLASS_A, CLASS_B, CLASS_C
 from .marks import r_basis
 from .store import BacktestRecord, JournalStore
+from .tradability import RESISTANCE, SUPPORT, compute_tradability
 
 # The status vocabulary and the state-native helpers are REUSED from the studies module (one
 # owner per literal / per mapping — never a second copy): the premise-state arming map, the
@@ -147,8 +149,8 @@ NULL_SETUP_TYPE = "random_null"
 
 # Exit reasons (one explicit copy each — the iter-15 own-copy lesson).
 EXIT_R_STOP = "r_stop"
-# era-4 J-05: the class-scaled take-profit exit (structure_tape only — v1/null trades carry no
-# ``target_price`` and so can never reach this reason).
+# era-4 J-05: the class-scaled take-profit exit (structure_tape / structure_tape_map trades only —
+# v1/null trades carry no ``target_price`` and so can never reach this reason).
 EXIT_REWARD_TARGET = "reward_target"
 EXIT_HORIZON = "horizon"
 EXIT_STATE_FLIP = "state_flip"
@@ -245,6 +247,66 @@ def _next_opposing_zone_price(
     return min(side, key=lambda p: abs(p - entry_price))
 
 
+# --- structure_tape_map candidate sourcing (era-5B capability 5, J-04): the IDENTICAL zone/level
+# helpers directly above, twinned for TRADABLE-MAP BANDS (``research/tradability.py``) instead of
+# raw confluence zones (``research/levels.py``) — never imported from ``tradability.py`` itself
+# (that module owns band COMPUTATION; arming candidate SELECTION over an already-computed band
+# list is this module's own, existing "reused technique, twinned container" idiom — the identical
+# relationship ``_next_opposing_zone_price``/``_zone_nearest_price`` already have to their zone
+# input). A band's ``members`` list is the EXACT SAME level-dict shape (price/timeframe/type/
+# touch_count) a zone's ``levels`` list carries, and a band's ``class`` key is read the identical
+# way a zone's is — so ``_level_provenance`` above is REUSED UNCHANGED for a band, no twin needed. --
+
+
+def _band_nearest_price(band: dict, entry_price: float) -> float:
+    """The band's own member level NEAREST ``entry_price`` — the ``_zone_nearest_price`` technique,
+    applied to a band's ``members`` list."""
+    return min(band["members"], key=lambda lvl: abs(lvl["price"] - entry_price))["price"]
+
+
+def _next_opposing_band_price(
+    bands: list[dict], arming_band: dict, entry_price: float, direction: str
+) -> float | None:
+    """era-5B J-04: the nearest OTHER band's representative price on the side ``direction`` implies
+    — the ``_next_opposing_zone_price`` technique, applied to the tradable map's bands. Considers
+    EVERY other band regardless of its own inherited class (including an unclassified ``class:
+    null`` band — the reward-target's "next opposing level" is a PRICE-STRUCTURE question, not a
+    conviction one; only the ARMING band's own class scales the stop/reward/size, exactly as an
+    unclassified zone never existed for ``_next_opposing_zone_price`` to consider in the first
+    place). Excludes the arming band itself BY IDENTITY. ``None`` when nothing qualifies on that
+    side — the identical honest fallback."""
+    candidates = [_band_nearest_price(b, entry_price) for b in bands if b is not arming_band]
+    if direction == "long":
+        side = [p for p in candidates if p > entry_price]
+    else:
+        side = [p for p in candidates if p < entry_price]
+    if not side:
+        return None
+    return min(side, key=lambda p: abs(p - entry_price))
+
+
+def _structure_tape_map_side_for_reading(direction: str, setup_type: str) -> str:
+    """Which tradable-map SIDE (``tradability.SUPPORT`` / ``RESISTANCE``) a (direction, setup_type)
+    reading tests — goal.md's own floor/ceiling language for the tape-confirmation mapping
+    (``structure_tape_rejection_state_by_direction`` / ``..._breakthrough_state_by_direction``'s
+    own docstring in ``config.py``), made MECHANICAL now that a BAND — unlike a raw classified
+    level/zone, which carries no side at all — has an explicit ``side`` field to test it against: a
+    REJECTION defends the level it sits at (long defends a FLOOR — a support band; short defends a
+    CEILING — a resistance band); a BREAKTHROUGH moves BEYOND the level in its own direction (long
+    breaks a CEILING — resistance; short breaks a FLOOR — support).
+
+    A deliberate, flagged judgment call (see the dev handoff): ``_structure_tape_arm`` above has no
+    equivalent side filter because raw confluence zones carry no side at all, so it tests every
+    zone regardless of which side of price it sits on. Bands make the correct, side-aware test
+    possible for the first time — without it, a short "breakthrough" could arm against a distant
+    RESISTANCE band merely because price sits numerically below it, which is not a breakthrough of
+    anything. This never changes ``structure_tape``'s own byte-identical behaviour (a separate
+    branch, untouched)."""
+    if setup_type == _STRUCTURE_TAPE_REJECTION:
+        return SUPPORT if direction == "long" else RESISTANCE
+    return RESISTANCE if direction == "long" else SUPPORT
+
+
 def _class_scaled_target(
     entry_price: float,
     direction: str,
@@ -482,8 +544,9 @@ class BacktestRunner:
         epoch_anchor: float | None = None,
     ) -> list[dict]:
         """Arm and simulate ONE registered strategy's trades over the recorded path (era-4 J-04:
-        dispatches to the additive ``structure_tape`` branch; v1's own branch — and the code
-        below it — is UNCHANGED, so v1 stays byte-identical).
+        dispatches to the additive ``structure_tape`` branch; era-5B J-04 adds the additive
+        ``structure_tape_map`` branch beside it; v1's own branch — and the code below it — is
+        UNCHANGED, so v1 stays byte-identical).
 
         v1: ONE deterministic interleaved pass: at each recorded event the open trade's exit is
         evaluated FIRST, then (if flat) each declared setup x direction combo may arm per the
@@ -493,6 +556,8 @@ class BacktestRunner:
         exits ``dataset_end``."""
         if strategy["strategy_id"] == STRATEGY_TAPE_ID:
             return self._structure_tape_trades(path, strategy, bar_store, symbol, epoch_anchor)
+        if strategy["strategy_id"] == STRATEGY_TAPE_MAP_ID:
+            return self._structure_tape_map_trades(path, strategy, bar_store, symbol, epoch_anchor)
         config = self._config
         sustain = strategy["entries"]["arm_sustain_seconds"]
         cooldown = strategy["entries"]["arm_cooldown_seconds"]
@@ -643,6 +708,121 @@ class BacktestRunner:
                     return direction, setup_type, _level_provenance(level, zone), opposing_price
         return None
 
+    # --- structure_tape_map simulation (era-5B J-04): the IDENTICAL one-open-trade-at-a-time
+    # interleaved pass as structure_tape directly above (exits evaluated FIRST, then, while flat,
+    # one arming check per event), a NEW arming source only -------------------------------------
+    def _structure_tape_map_trades(
+        self,
+        path: list[_PathPoint],
+        strategy: dict,
+        bar_store: BarStore | None,
+        symbol: str | None,
+        epoch_anchor: float | None,
+    ) -> list[dict]:
+        """Arm and simulate ``structure_tape_map``'s trades over the recorded path — BYTE-IDENTICAL
+        control flow to ``_structure_tape_trades`` above (same one-open-trade loop, same
+        ``_exit_reason``/``_close_trade``/``_arm_trade`` calls — reused, never duplicated); the
+        ONLY difference is the arming SOURCE: ``_structure_tape_map_arm`` (tradable-map bands)
+        instead of ``_structure_tape_arm`` (raw classified levels/zones). See
+        ``_structure_tape_map_arm``'s own docstring for the arming rule and its honest-emptiness
+        floors (missing bar_store/symbol/epoch_anchor, no bar series, no classified band)."""
+        if bar_store is None or not symbol or epoch_anchor is None:
+            return []
+        entries = strategy["entries"]
+        horizon = strategy["exits"]["horizon_seconds"]
+        cooldown = entries["arm_cooldown_seconds"]
+        config = self._config
+        position: dict | None = None
+        cooldown_until = float("-inf")
+        trades: list[dict] = []
+        for i, point in enumerate(path):
+            if position is not None and i > position["index"] and point.last is not None:
+                reason = self._exit_reason(position, point, horizon)
+                if reason is not None:
+                    trades.append(self._close_trade(position, point, reason))
+                    position = None
+            if (
+                position is None
+                and point.last is not None
+                and point.timestamp >= cooldown_until
+            ):
+                arm = self._structure_tape_map_arm(
+                    point, bar_store, symbol, epoch_anchor + point.timestamp, entries, config
+                )
+                if arm is not None:
+                    direction, setup_type, level, opposing_price = arm
+                    position = self._arm_trade(
+                        i, point, setup_type, direction, level=level, opposing_price=opposing_price
+                    )
+                    cooldown_until = point.timestamp + cooldown
+        if position is not None:
+            trades.append(self._close_trade(position, path[-1], EXIT_DATASET_END))
+        return trades
+
+    @staticmethod
+    def _structure_tape_map_arm(
+        point: _PathPoint,
+        bar_store: BarStore,
+        symbol: str,
+        as_of_epoch: float,
+        entries: dict,
+        config: Config,
+    ) -> tuple[str, str, dict, float | None] | None:
+        """One flat-event arming check — the IDENTICAL shape ``_structure_tape_arm`` performs
+        (resolve which reading the CURRENT tape state confirms FIRST, so a non-confirming tick
+        never pays for a map computation at all; then test candidates AS OF this event's own
+        absolute timestamp; return the FIRST qualifying candidate's ``(direction, setup_type,
+        level_provenance, next_opposing_price)``, or ``None``), sourcing candidates from the
+        row-"Tradable level map" canonical ``compute_tradability`` BANDS (era-5B J-01) instead of
+        ``compute_levels`` confluence-zone levels — never levels.py's raw output directly (the
+        tradable map is the ONLY lens this strategy reads; never a second, independent levels
+        computation).
+
+        A band's ``members`` list is the SAME level-dict shape a zone's ``levels`` list carries, so
+        the per-member proximity/breakthrough test below and the class-scaled exit math it feeds
+        (via ``_level_provenance``, reused UNCHANGED) are IDENTICAL to ``_structure_tape_arm`` —
+        only the outer container, and which side of that container is searched, differ:
+
+          * An UNCLASSIFIED band (``class: null`` — no overlapping confluence zone, an honest
+            absence ``tradability.py`` itself documents) is skipped BEFORE any member test: there
+            is no A/B/C to scale a stop/reward/size against, so a band with no inherited class arms
+            nothing (the identical "an unclassified lone level never joins a zone and never arms"
+            discipline ``structure_tape`` already relies on — ``compute_tradability`` merely makes
+            the null case reachable here, since EVERY level joins some band, unlike zone
+            membership, which requires >= 2 members).
+          * Only bands on the SIDE ``_structure_tape_map_side_for_reading`` names for this
+            (direction, setup_type) reading are tested (a genuine, flagged judgment call — see that
+            function's own docstring and the dev handoff): a band, unlike a raw zone, carries an
+            explicit support/resistance side, so this arming can finally test the semantically
+            correct side rather than every band regardless of position.
+
+        ``next_opposing_price`` is resolved from this SAME ``compute_tradability`` result (never a
+        second/future map read) via ``_next_opposing_band_price``, feeding the identical
+        class-scaled reward-target exit ``structure_tape`` uses; ``None`` when no band qualifies on
+        the side ``direction`` implies."""
+        reading = _structure_tape_reading(point.tape_state, entries)
+        if reading is None:
+            return None
+        direction, setup_type = reading
+        result = compute_tradability(bar_store, symbol, as_of_epoch, config)
+        band_bps = entries["proximity_band_bps"]
+        bands = result["bands"]
+        wanted_side = _structure_tape_map_side_for_reading(direction, setup_type)
+        for band in bands:
+            if band["class"] is None or band["side"] != wanted_side:
+                continue
+            for level in band["members"]:
+                price = level["price"]
+                if setup_type == _STRUCTURE_TAPE_REJECTION:
+                    tolerance = price * (band_bps / 10_000.0)
+                    qualifies = abs(point.last - price) <= tolerance
+                else:  # breakthrough — the studies' level-cross technique (price beyond the level)
+                    qualifies = point.last > price if direction == "long" else point.last < price
+                if qualifies:
+                    opposing_price = _next_opposing_band_price(bands, band, point.last, direction)
+                    return direction, setup_type, _level_provenance(level, band), opposing_price
+        return None
+
     # --- the seeded random-entry null baseline (same exits, fees, slippage) --------------------
     def _null_trades(self, path: list[_PathPoint], seed: int) -> list[dict]:
         """The seeded random-entry null baseline over the SAME recorded path: entry instants
@@ -697,12 +877,15 @@ class BacktestRunner:
         opposing_price: float | None = None,
     ) -> dict:
         """Open one simulated trade at a recorded event. ``level`` (era-4 J-04) is the arming
-        level's provenance for a ``structure_tape`` trade; v1 and the null baseline never pass it,
-        so their trade dicts carry no ``level`` key at all (byte-identical to before).
+        level's provenance for a ``structure_tape`` OR ``structure_tape_map`` trade (era-5B J-04
+        reuses this same gate — the CALLER, never this method, decides which strategy passes
+        ``level``); v1 and the null baseline never pass it, so their trade dicts carry no ``level``
+        key at all (byte-identical to before).
 
         v1/null (``level is None``): the invalidation is the studies' REUSED, spread-based helper
-        — UNCHANGED. ``structure_tape`` (``level is not None``, era-4 J-05): the invalidation is
-        the NEW class-scaled, level-relative ``_class_scaled_invalidation``, and the position also
+        — UNCHANGED. structure_tape / structure_tape_map (``level is not None``, era-4 J-05): the
+        invalidation is the NEW class-scaled, level-relative ``_class_scaled_invalidation``, and
+        the position also
         carries a ``target_price`` (the class-scaled reward target, bounded by ``opposing_price`` —
         the next opposing level resolved at arm time, or ``None``). Either way R flows through the
         ONE shared ``marks.r_basis`` — never a second formula."""
@@ -774,10 +957,10 @@ class BacktestRunner:
         recorded spread contributes zero slippage — honest absence). GROSS is measured from the
         recorded prices; NET from the adjusted fills minus both fills' fees. The fixed
         ``strategy_dollars_per_r`` notional makes R and $ two views of one measurement:
-        ``shares = dollars_per_r / R basis`` — v1/null, UNCHANGED. ``structure_tape`` (era-4 J-05,
-        ``"level" in trade``): ``shares`` is scaled by the arming level's class size multiple
-        (``structure_tape_size_multiple_by_class``) over the SAME fixed notional — still a
-        PER-TRADE SIMULATED notional only, never a real order."""
+        ``shares = dollars_per_r / R basis`` — v1/null, UNCHANGED. structure_tape /
+        structure_tape_map (era-4 J-05 / era-5B J-04, ``"level" in trade``): ``shares`` is scaled
+        by the arming level's class size multiple (``structure_tape_size_multiple_by_class``) over
+        the SAME fixed notional — still a PER-TRADE SIMULATED notional only, never a real order."""
         config = self._config
         direction = trade["direction"]
         sign = 1.0 if direction == "long" else -1.0
diff --git a/apps/backend/app/research/edge_report.py b/apps/backend/app/research/edge_report.py
index 1248876..d944f44 100644
--- a/apps/backend/app/research/edge_report.py
+++ b/apps/backend/app/research/edge_report.py
@@ -1,5 +1,8 @@
 """The baseline-edge report (era-3 capability 9 groundwork, J-09) —
-``python -m app.research.edge_report --out <path>``.
+``python -m app.research.edge_report --out <path>`` — PLUS the era-5B J-04 additive 3-way
+strategy-comparison report served by ``GET /research/edge-report`` (see
+``run_strategy_comparison_report`` near the bottom of this module for that section's own detailed
+docstring; every helper/CLI above it is UNTOUCHED, byte-identical to before).
 
 Answers the era's founding question for the FROZEN champion ALONE — no candidate, no comparison,
 no promotion: does the currently persisted champion (read verbatim via
@@ -53,12 +56,31 @@ import json
 import sys
 from pathlib import Path
 
-from ..config import CONFIG, Config
-from .backtests import BacktestJobManager, REGISTER, STATUS_DONE
-from .datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN
+from ..config import (
+    CONFIG,
+    Config,
+    PROFILE_DEFAULT,
+    STRATEGY_TAPE_ID,
+    STRATEGY_TAPE_MAP_ID,
+    STRATEGY_V1_ID,
+)
+from .bars import BarStore
+# ``_aggregate`` is imported PRIVATE (the ``datasets.py`` -> ``from .studies import
+# _load_reference_window as _load_reference`` precedent): the ONE trade-population aggregator
+# every other report in this codebase already computes with (n/gross/net R and $/win_rate/
+# max_drawdown_r) -- reused VERBATIM for a strategy-comparison cell's pooled trade list, never a
+# second R/$/edge formula.
+from .backtests import BacktestJobManager, REGISTER, STATUS_DONE, _aggregate
+from .datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN, parse_utc_epoch
+from .setups import compute_setups
 from .store import JournalStore
 
-__all__ = ["EdgeReportError", "run_edge_report", "main"]
+__all__ = ["EdgeReportError", "run_edge_report", "run_strategy_comparison_report", "main"]
+
+# era-5B J-04: the three registered strategies a comparison cell may ever carry, in the SAME
+# registration order ``Config.strategy_registry()`` serves -- read here so a cell's own
+# ``strategy_id`` is never a restated literal.
+_ALL_STRATEGY_IDS: tuple[str, ...] = (STRATEGY_V1_ID, STRATEGY_TAPE_ID, STRATEGY_TAPE_MAP_ID)
 
 # The exact, honest empty finding (DoD-mandated literal string) — emitted whenever zero hold-out
 # datasets clear the positive-edge gate, including the true-empty-registry case.
@@ -94,13 +116,19 @@ def _run_backtest(
     *,
     strategy_id: str,
     profile: str,
+    bar_store: BarStore | None = None,
 ) -> dict:
     """Run ONE backtest synchronously through the EXISTING public job API (the
     ``pnl_scan._run_backtest`` pattern) and return its persisted ``result`` block — refusing
     explicitly unless it completed ``done`` (a failed/cancelled report carries no served
-    aggregates, so nothing could be honestly measured from it)."""
+    aggregates, so nothing could be honestly measured from it).
+
+    ``bar_store`` (era-5B J-04, optional, defaults ``None`` — every EXISTING champion-only caller
+    below is unaffected byte-for-byte) is threaded through to ``run_sync`` exactly like the
+    backtest route's own seam: ``structure_tape``/``structure_tape_map`` read it to arm; v1
+    ignores it."""
     payload = jobs.create({"dataset_id": dataset_id, "strategy_id": strategy_id, "profile": profile})
-    jobs.run_sync(payload["id"], dataset_store=dataset_store)
+    jobs.run_sync(payload["id"], dataset_store=dataset_store, bar_store=bar_store)
     final = store.get_backtest(payload["id"]).payload
     if final.get("status") != STATUS_DONE:
         raise EdgeReportError(
@@ -219,6 +247,217 @@ def run_edge_report(store: JournalStore, dataset_store: DatasetStore, config: Co
     }
 
 
+# --- The 3-way strategy-comparison report (era-5B capability 6, J-04; Data Contract row
+# "edge-report cells") -- an ADDITIVE extension of THIS module, never a fork: reuses the ONE
+# ``BacktestJobManager.create`` + ``run_sync`` path above (``_run_backtest``, now threading
+# ``bar_store`` through, see its own docstring), the verbatim ``_aggregate`` trade-population
+# arithmetic (imported from ``backtests.py`` — never re-derived), and ``_split_datasets``' ONE
+# checksum-verified ``DatasetStore.list()`` read per split (a dataset failing integrity
+# verification anywhere aborts the WHOLE report explicitly, same as ``run_edge_report`` above).
+# ``run_edge_report``/``main``/``_render_report`` and every helper above this comment stay
+# UNTOUCHED — the era-3 champion-only CLI's behaviour is byte-identical to before.
+#
+# Answers a DIFFERENT question than the champion-only report above: not "does the CURRENT
+# champion show a hold-out edge", but "which of the three REGISTERED strategies (v1 /
+# structure_tape / structure_tape_map) actually profits, broken down by the tradable-map class,
+# side, and touch reaction the recorded window was scanned FROM" — v1/structure_tape/
+# structure_tape_map are all measured, never just the champion; the champion pointer itself is
+# never read, moved, or promoted by this section (there is nothing here to promote — the identical
+# "no train-only promotion, by construction" property ``run_edge_report`` already has).
+#
+# A "cell" is EXACTLY one (strategy_id, band_class, band_side, reaction, feed) combination —
+# strategy x class x side x reaction is the DoD's named shape; ``feed`` is carried as a FIFTH,
+# additive dimension so two different feeds' recordings NEVER pool into one measurement (the
+# never-pool-across-feeds anti-goal, actively load-bearing here for the first time: unlike every
+# EARLIER era-3/4/5 surface, which only ever sees one feed's data per call, this report can
+# genuinely receive a mixed-feed dataset registry). Cells are materialized LAZILY -- only for
+# (dataset, event) pairs that genuinely attribute -- rather than pre-registering every
+# combinatorial slot: unlike the class-only ``_aggregate_by_class`` breakdown (a FIXED, three-value
+# enum with no further sub-dimension), a cell's own ``feed`` value is data-driven and unbounded, so
+# there is no fixed "every combination" skeleton to pre-populate honestly. An all-empty ``cells``
+# list (every registered dataset's window contains no scan event at all, e.g. a symbol outside the
+# config-owned panel) is therefore a valid degenerate case of "all cells insufficient_sample" — a
+# report with a smaller-than-expected cell count is never an error.
+
+
+def _dataset_event(dataset_meta: dict, events: list[dict]) -> dict | None:
+    """The ``compute_setups`` event this dataset was recorded around, or ``None`` when no scan
+    event's own touch falls inside the dataset's registered window — datasets do not carry
+    class/side/reaction themselves; only events do (module docstring). The
+    ``setups._matching_dataset`` window-containment TEST, mirrored (numeric epoch comparison,
+    inclusive both ends — the identical ``parse_utc_epoch`` discipline, never a lexicographic
+    string compare) but in the OPPOSITE direction: given ONE already-verified dataset (from THIS
+    module's own ``_split_datasets`` read), scan the already-computed ``events`` list for a match,
+    rather than re-opening a second ``DatasetStore.list()`` read the way ``_matching_dataset``
+    itself does internally (which silently drops a corrupt file's error — inconsistent with this
+    module's OWN all-or-nothing integrity discipline, so it is never called from here). Ties (more
+    than one event's touch falling inside the SAME window) break on the earliest ``touch_ts``, then
+    event ``id`` — deterministic, never insertion-order happenstance."""
+    window_start = parse_utc_epoch(dataset_meta["window_start_utc"])
+    window_end = parse_utc_epoch(dataset_meta["window_end_utc"])
+    candidates = [
+        e for e in events
+        if e["symbol"] == dataset_meta["symbol"]
+        and window_start <= parse_utc_epoch(e["touch_ts"]) <= window_end
+    ]
+    if not candidates:
+        return None
+    return min(candidates, key=lambda e: (e["touch_ts"], e["id"]))
+
+
+def _cell_key(cell: dict) -> tuple:
+    """The full identity tuple a cell is pooled/matched by — strategy x class x side x reaction x
+    feed, the never-pool-across-feeds dimension included."""
+    return (cell["strategy_id"], cell["band_class"], cell["band_side"], cell["reaction"], cell["feed"])
+
+
+def _split_cells(
+    jobs: BacktestJobManager,
+    store: JournalStore,
+    dataset_store: DatasetStore,
+    bar_store: BarStore,
+    datasets: list[dict],
+    events: list[dict],
+    config: Config,
+) -> list[dict]:
+    """One split's (train or hold-out) cells: for every dataset that resolves an owning event with
+    a genuinely inherited class (an unclassified ``class: null`` band is honestly excluded — there
+    is no A/B/C to report a cell under), run ALL THREE registered strategies over it and pool their
+    trades (and null-baseline trades) into the matching (strategy, class, side, reaction, feed)
+    cell. Trades from MULTIPLE datasets sharing a cell are ordered by their reconstructed REAL UTC
+    entry instant (``dataset["epoch_anchor"] + trade["entry"]["logical_ts"]`` — the identical
+    reconstruction ``setups.py``'s own tape-timeline join and ``serializers.serialize_history``
+    already use) before the ONE shared ``_aggregate`` call, so a pooled cell's ``win_rate``/
+    ``max_drawdown_r`` reflect a genuine chronological trade sequence — never scan-order/dataset-id
+    happenstance (max_drawdown_r is peak-to-trough IN TRADE ORDER; summing already-aggregated
+    numbers cannot recover that without the raw, correctly-ordered trade list)."""
+    pools: dict[tuple, dict] = {}
+    for dataset_meta in datasets:
+        event = _dataset_event(dataset_meta, events)
+        if event is None or event["band"]["class"] is None:
+            continue
+        feed = dataset_meta["data_feed"]
+        for strategy_id in _ALL_STRATEGY_IDS:
+            result = _run_backtest(
+                jobs, store, dataset_store, dataset_meta["id"],
+                strategy_id=strategy_id, profile=PROFILE_DEFAULT, bar_store=bar_store,
+            )
+            key = (strategy_id, event["band"]["class"], event["band"]["side"], event["reaction"], feed)
+            pool = pools.setdefault(key, {"trades": [], "null_trades": [], "dataset_ids": []})
+            anchor = dataset_meta.get("epoch_anchor") or 0.0
+            pool["trades"].extend(
+                (anchor + t["entry"]["logical_ts"], t) for t in result["trades"]
+            )
+            pool["null_trades"].extend(
+                (anchor + t["entry"]["logical_ts"], t) for t in result["null_baseline"]["trades"]
+            )
+            pool["dataset_ids"].append(dataset_meta["id"])
+
+    cells: list[dict] = []
+    for (strategy_id, band_class, band_side, reaction, feed), pool in pools.items():
+        ordered_trades = [t for _, t in sorted(pool["trades"], key=lambda pair: pair[0])]
+        ordered_null = [t for _, t in sorted(pool["null_trades"], key=lambda pair: pair[0])]
+        measurement = _aggregate(ordered_trades)
+        cells.append({
+            "strategy_id": strategy_id,
+            "band_class": band_class,
+            "band_side": band_side,
+            "reaction": reaction,
+            "feed": feed,
+            "dataset_ids": sorted(pool["dataset_ids"]),
+            "measurement": measurement,
+            "null_baseline": _aggregate(ordered_null),
+            "insufficient_sample": measurement["n"] < config.pnl_min_sample_size,
+        })
+    cells.sort(key=_cell_key)
+    return cells
+
+
+def _cell_beats_null(cell: dict) -> bool:
+    """"Beats its own null baseline" — the ``_beats_null`` gate, applied to a strategy-comparison
+    CELL instead of a per-dataset champion row (a genuine twin, not a re-derived formula: BOTH net
+    R AND net $ must exceed the cell's own seeded null baseline)."""
+    return (
+        cell["measurement"]["net_r"] > cell["null_baseline"]["net_r"]
+        and cell["measurement"]["net_usd"] > cell["null_baseline"]["net_usd"]
+    )
+
+
+def _cell_clears_gate(cell: dict, config: Config) -> bool:
+    """The identical ``_is_positive_edge`` four-part gate (positive net R AND net $, at least
+    ``Config.pnl_min_sample_size``, and beating the cell's own null baseline), applied to a
+    strategy-comparison cell. Used ONLY to rank/annotate a cell in the informational
+    ``surviving_train_cells`` list below — this module promotes nothing (see the module docstring);
+    the champion moves ONLY through the existing sweep gate on hold-out data."""
+    m = cell["measurement"]
+    return (
+        m["net_r"] > 0
+        and m["net_usd"] > 0
+        and m["n"] >= config.pnl_min_sample_size
+        and _cell_beats_null(cell)
+    )
+
+
+def _surviving_train_cells(
+    train_cells: list[dict], holdout_cells: list[dict], config: Config
+) -> list[dict]:
+    """A ranked, informational list of TRAIN cells that clear the positivity gate, each carrying
+    its OWN matching hold-out cell's status (an honest ``holdout_cell: None`` /
+    ``holdout_positive_edge: False`` when no hold-out data exists yet for that exact key — never a
+    fabricated verdict). Ranked by the train cell's OWN net R (descending), tie-broken by its full
+    identity key — the ``_rank`` pattern, applied to cells."""
+    holdout_by_key = {_cell_key(c): c for c in holdout_cells}
+    survivors: list[dict] = []
+    for cell in train_cells:
+        if not _cell_clears_gate(cell, config):
+            continue
+        holdout_cell = holdout_by_key.get(_cell_key(cell))
+        survivors.append({
+            "train_cell": cell,
+            "holdout_cell": holdout_cell,
+            "holdout_positive_edge": holdout_cell is not None and _cell_clears_gate(holdout_cell, config),
+        })
+    survivors.sort(
+        key=lambda s: (-s["train_cell"]["measurement"]["net_r"], _cell_key(s["train_cell"]))
+    )
+    return survivors
+
+
+def run_strategy_comparison_report(
+    store: JournalStore, dataset_store: DatasetStore, bar_store: BarStore, config: Config
+) -> dict:
+    """The ONE computer of the 3-way strategy-comparison report (era-5B J-04; ``GET
+    /research/edge-report`` + the MCP ``edge_report`` proxy serve this VERBATIM). Measures ``v1``,
+    ``structure_tape``, and ``structure_tape_map`` over EVERY registered event-window dataset that
+    resolves an owning, classified scan event, aggregated into per strategy x class x side x
+    reaction x feed cells. Raises ``EdgeReportError`` for a dishonest state (the identical
+    ``_split_datasets`` integrity discipline ``run_edge_report`` uses) — nothing is written by the
+    CALLER in that case. Strictly read-only: promotes nothing, appends no ledger row, moves no
+    champion pointer (see the module docstring)."""
+    jobs = BacktestJobManager(store, config)
+    train_datasets = _split_datasets(dataset_store, SPLIT_TRAIN)
+    holdout_datasets = _split_datasets(dataset_store, SPLIT_HOLDOUT)
+
+    # ONE ``compute_setups`` call for the WHOLE report (audit B2 hot-path guard) — never per
+    # dataset, never per split; reused for both the train and hold-out join below. Skipped
+    # entirely when the registry is empty (nothing to join against), so the empty-registry case
+    # never pays for a full panel scan at all.
+    events: list[dict] = []
+    if train_datasets or holdout_datasets:
+        events = compute_setups(bar_store, config)["events"]
+
+    train_cells = _split_cells(jobs, store, dataset_store, bar_store, train_datasets, events, config)
+    holdout_cells = _split_cells(jobs, store, dataset_store, bar_store, holdout_datasets, events, config)
+
+    return {
+        "register": REGISTER,
+        "pnl_min_sample_size": config.pnl_min_sample_size,
+        "train": {"cells": train_cells},
+        "holdout": {"cells": holdout_cells},
+        "surviving_train_cells": _surviving_train_cells(train_cells, holdout_cells, config),
+    }
+
+
 def _render_report(report: dict) -> str:
     """Pure, deterministic JSON render (sorted keys — the ``pnl_scan._render_report`` /
     ``datasets.py`` ``_canonical`` precedent): identical ``report`` dicts always render identical
diff --git a/apps/backend/app/research/routes.py b/apps/backend/app/research/routes.py
index f063d13..5cfb8f5 100644
--- a/apps/backend/app/research/routes.py
+++ b/apps/backend/app/research/routes.py
@@ -49,6 +49,7 @@ from .bars import (
     BarStore,
     EmptyBarWindowError,
 )
+from .edge_report import EdgeReportError, run_strategy_comparison_report
 from .levels import compute_levels
 from .setups import BROKE, CHOPPED, REJECTED, compute_setups, enrich_with_tape_timeline
 from .tradability import compute_tradability
@@ -2059,3 +2060,34 @@ def get_strategies(registry: ResearchRegistry = Depends(get_registry)) -> dict:
     genuine hold-out survivor moves it (J-06) — served verbatim from the ONE projection, reading
     the SAME single ``store.get_champion_pointer()`` source ``GET /research/profiles`` reads."""
     return strategies_projection(registry.store, registry.config)
+
+
+# --- The 3-way strategy-comparison edge report (era-5B capability 6, J-04; Data Contract row
+# "edge-report cells") ---------------------------------------------------------------------------
+# Exactly ONE route, GET only, mirroring ``GET /research/strategies`` immediately above in shape:
+# ``research/edge_report.py``'s ``run_strategy_comparison_report`` is the SOLE computer of this
+# value; this route only wires the three existing dependency seams (journal store, dataset store,
+# bar store — the identical ``create_backtest`` seam trio) and serves the module's output VERBATIM
+# (the MCP ``edge_report`` tool proxies this byte-identically; no second computation path). No
+# write surface exists on this route — any non-GET verb is FastAPI's default 405. This route never
+# reads or moves the champion pointer — see the module's own "no champion, no promotion" docstring.
+
+
+@router.get("/edge-report")
+def get_edge_report(
+    registry: ResearchRegistry = Depends(get_registry),
+    dataset_store: DatasetStore = Depends(get_dataset_store),
+    bar_store: BarStore = Depends(get_bar_store),
+) -> dict:
+    """The 3-way strategy-comparison report (``v1`` / ``structure_tape`` / ``structure_tape_map``)
+    aggregated into per strategy x class x side x reaction x feed cells over every registered
+    event-window dataset that resolves an owning, classified scan event — served VERBATIM from
+    ``run_strategy_comparison_report`` (era-5B J-04). A dataset failing integrity verification
+    aborts the whole report with an explicit 500 (the ``create_backtest``/``EdgeReportError``
+    precedent) — partial results are never served. An all-empty or all-``insufficient_sample``
+    report (the expected shape on a keyless, single-fixture registry) is a valid 200, never an
+    error."""
+    try:
+        return run_strategy_comparison_report(registry.store, dataset_store, bar_store, registry.config)
+    except EdgeReportError as exc:
+        raise HTTPException(status_code=500, detail=f"edge report could not complete: {exc}")
diff --git a/apps/backend/tests/test_backtests.py b/apps/backend/tests/test_backtests.py
index 5f18d83..76ebdf2 100644
--- a/apps/backend/tests/test_backtests.py
+++ b/apps/backend/tests/test_backtests.py
@@ -36,12 +36,13 @@ from pathlib import Path
 
 import pytest
 
-from app.config import CONFIG, STRATEGY_TAPE_ID, STRATEGY_V1_ID
+from app.config import CONFIG, STRATEGY_TAPE_ID, STRATEGY_TAPE_MAP_ID, STRATEGY_V1_ID
 from app.providers.adapters.base import RawBar
 from app.providers.base import QuoteEvent, Side, TradeEvent
 from app.providers.simulated import SIM_SCENARIOS, SimulatedProvider
 from app.research.backtests import (
     BacktestJobManager,
+    BacktestRunner,
     EXIT_DATASET_END,
     EXIT_HORIZON,
     EXIT_REWARD_TARGET,
@@ -59,6 +60,7 @@ from app.research.bars import BarStore
 from app.research.datasets import DatasetStore
 from app.research.marks import r_basis
 from app.research.store import JournalStore
+from app.research.studies import _PathPoint
 
 # The synthetic three-timeframe confluence fixture (class A/B/C zones at exact, known prices) --
 # REUSED verbatim from test_levels.py (the plan's own directive: the committed real PG bar fixture
@@ -381,11 +383,35 @@ def test_structure_tape_definition_is_config_owned_and_additive_beside_v1():
     assert "size_multiple_by_class" not in v1
 
 
-def test_strategy_registry_lists_v1_then_structure_tape_in_registration_order():
+def test_strategy_registry_lists_v1_structure_tape_then_structure_tape_map_in_registration_order():
     registry = CONFIG.strategy_registry()
-    assert [s["strategy_id"] for s in registry] == [STRATEGY_V1_ID, STRATEGY_TAPE_ID]
+    assert [s["strategy_id"] for s in registry] == [
+        STRATEGY_V1_ID,
+        STRATEGY_TAPE_ID,
+        STRATEGY_TAPE_MAP_ID,
+    ]
     assert registry[0] == CONFIG.strategy_definition(STRATEGY_V1_ID)
     assert registry[1] == CONFIG.strategy_definition(STRATEGY_TAPE_ID)
+    assert registry[2] == CONFIG.strategy_definition(STRATEGY_TAPE_MAP_ID)
+
+
+def test_structure_tape_map_definition_is_config_owned_and_identical_to_structure_tape_except_id():
+    """era-5B J-04: ``structure_tape_map`` reuses the EXACT SAME grammar as ``structure_tape`` —
+    same entries/exits/fees/slippage/size fields, verbatim, no new magic number — differing ONLY
+    in its own ``strategy_id``. What genuinely differs (arming candidate source: tradable-map
+    bands instead of raw levels/zones) lives in the backtest runner, not in this definition."""
+    tape = CONFIG.strategy_definition(STRATEGY_TAPE_ID)
+    tape_map = CONFIG.strategy_definition(STRATEGY_TAPE_MAP_ID)
+    assert tape_map is not None
+    assert tape_map["strategy_id"] == STRATEGY_TAPE_MAP_ID
+    assert {**tape_map, "strategy_id": "x"} == {**tape, "strategy_id": "x"}
+
+
+def test_default_fingerprint_still_pinned_after_registering_structure_tape_map():
+    # structure_tape_map introduces NO new Config field (it reuses the six structure_tape_* fields
+    # verbatim — see strategy_definition), so no new exclusion-set entry is needed at all; the
+    # fingerprint stays pinned trivially. Verified by direct computation, not assumed.
+    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
 
 
 def test_structure_tape_breakthrough_long_arms_at_the_class_a_resistance_level(
@@ -741,6 +767,210 @@ def test_v1_backtest_carries_an_honest_all_empty_per_class_breakdown(tmp_path, s
         assert by_class[cls]["insufficient_sample"] is True
 
 
+# --- Strategy grammar structure_tape_map: additive over compute_tradability BANDS (era-5B
+# capability 5, J-04) -- REUSES the confluence_bar_store fixture directly above (genuinely
+# multi-timeframe: 1h + 1d + 1w -- the iter-1 lesson: a daily-only fixture previously hid a real
+# ranking bug, so every arming test below runs against a fixture that mixes timeframes). Every
+# value below is VERIFIED BY DIRECT COMPUTATION against this exact fixture (never hand-derived --
+# the test_tradability.py/test_setups.py precedent). Through ``compute_tradability`` (as of
+# ``_STRUCTURE_TAPE_ANCHOR``, whose basis is the "1d" bar at BASE+1*DAY, close=200.08), the ~100.00
+# confluence zone becomes a SUPPORT band [100.00, 100.05] class B (the weekly member has not yet
+# closed at this basis, so B -- not the class-A zone test_synthetic_three_timeframe_fixture...
+# proves through the DIRECT, far-future compute_levels call above); ~300.00/300.05 becomes a
+# RESISTANCE band class C; 500/900/910/20/10 are each unclassified (``class: null``) singleton
+# bands with no overlapping confluence zone. --------------------------------------------------------
+
+
+def test_structure_tape_map_breakthrough_short_arms_at_the_class_b_support_band(
+    tmp_path, store, jobs, confluence_bar_store
+):
+    # SIM-SELLER: seller_control reads from 19.5s at 99.84 -- beyond (below) the support band's
+    # 1h member at 100.00. seller_control -> breakthrough short -> a FLOOR break (goal.md's own
+    # floor/ceiling language) -> the SUPPORT side, which is exactly this band's own side.
+    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-SELLER")
+    payload = _run(
+        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_MAP_ID, bar_store=confluence_bar_store
+    )
+    assert payload["status"] == STATUS_DONE
+    result = payload["result"]
+    assert result["strategy_id"] == STRATEGY_TAPE_MAP_ID
+    assert result["strategy"] == CONFIG.strategy_definition(STRATEGY_TAPE_MAP_ID)
+    trades = result["trades"]
+    assert len(trades) == 1
+    t = trades[0]
+    assert (t["setup_type"], t["direction"]) == ("breakthrough", "short")
+    assert t["entry"]["logical_ts"] == 19.5
+    assert t["entry"]["price"] == 99.84
+    # The inherited class is B here (a genuinely DIFFERENT class from structure_tape's own class-A
+    # test above) -- the tradable map's own morning-markup basis, not compute_levels' far-future
+    # as-of, so the arming level's class is READ from the band, never assumed identical.
+    assert t["level"] == {"price": 100.00, "timeframe": "1h", "class": "B"}
+    assert t["exit"]["reason"] == EXIT_DATASET_END
+    assert t["exit"]["logical_ts"] == 25.0
+    assert t["exit"]["price"] == 99.76
+    # Next opposing band price on the short side: the support band at [200.00, 200.08]'s nearest
+    # member (200.00) -- EVERY level joins some band (unlike zone membership), so this search finds
+    # more candidates than structure_tape's own zone-based one did on the identical trade shape.
+    _assert_structure_tape_trade_arithmetic(t, opposing_price=20.0)
+    _assert_per_class_breakdown_isolates_one_trade(result, cls="B")
+
+
+def test_structure_tape_map_rejection_long_arms_at_the_class_b_support_band(
+    tmp_path, store, jobs, confluence_bar_store
+):
+    # SIM-BIDABS: bid_absorption reads from 19.5s, price HELD FLAT at 100.00 -- inside the support
+    # band's own [100.00, 100.05] range. bid_absorption -> rejection long -> defends a FLOOR -> the
+    # SUPPORT side, matching this band's own side.
+    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-BIDABS")
+    payload = _run(
+        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_MAP_ID, bar_store=confluence_bar_store
+    )
+    result = payload["result"]
+    trades = result["trades"]
+    assert len(trades) == 1
+    t = trades[0]
+    assert (t["setup_type"], t["direction"]) == ("rejection", "long")
+    assert t["entry"]["logical_ts"] == 19.5
+    assert t["entry"]["price"] == 100.00
+    assert t["level"] == {"price": 100.00, "timeframe": "1h", "class": "B"}
+    assert t["exit"]["reason"] == EXIT_DATASET_END
+    assert t["exit"]["logical_ts"] == 25.0
+    assert t["exit"]["price"] == 100.00
+    _assert_structure_tape_trade_arithmetic(t, opposing_price=200.00)
+    _assert_per_class_breakdown_isolates_one_trade(result, cls="B")
+
+
+def test_structure_tape_map_side_aware_reading_never_arms_on_the_wrong_side_band(
+    tmp_path, store, jobs, confluence_bar_store
+):
+    """A deliberate, flagged design decision (see the dev handoff and
+    ``_structure_tape_map_side_for_reading``'s own docstring): unlike ``structure_tape`` (which has
+    no side concept and tests every zone regardless of position), ``structure_tape_map`` only tests
+    bands on the semantically correct side of a reading. SIM-BUYER's breakthrough-long premise
+    (buyer_control -> break a CEILING -> RESISTANCE) and SIM-ASKABS's rejection-short premise
+    (ask_absorption -> defend a CEILING -> RESISTANCE) both confirm at price ~100 -- but the ONLY
+    classified band there is the SUPPORT band [100.00, 100.05] (class B), so BOTH arm nothing, even
+    though structure_tape's OWN zone-based arm (no side filter) DOES arm on the identical zone at
+    the identical price (proven directly below as the contrasting positive control)."""
+    buyer_dstore, buyer_meta = None, None
+    for ticker in ("SIM-BUYER", "SIM-ASKABS"):
+        dstore, meta = _record_structure_tape_dataset(tmp_path, ticker)
+        if ticker == "SIM-BUYER":
+            buyer_dstore, buyer_meta = dstore, meta
+        payload = _run(
+            jobs, store, dstore, meta["id"],
+            strategy_id=STRATEGY_TAPE_MAP_ID, bar_store=confluence_bar_store,
+        )
+        assert payload["status"] == STATUS_DONE
+        assert payload["result"]["trades"] == [], f"{ticker} must not arm on the wrong-side band"
+
+    # Positive control: the IDENTICAL recorded SIM-BUYER dataset, but run under structure_tape's
+    # OWN raw-levels arm (no side filter at all) -- DOES arm at this exact zone, proving the empty
+    # result above is this iteration's deliberate side-awareness, not an accidental "nothing there".
+    tape_payload = _run(
+        jobs, store, buyer_dstore, buyer_meta["id"],
+        strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store,
+    )
+    assert len(tape_payload["result"]["trades"]) == 1
+
+
+def test_structure_tape_map_skips_an_unclassified_band_even_when_price_and_state_qualify(
+    confluence_bar_store,
+):
+    """An UNCLASSIFIED band (``class: null`` -- no overlapping confluence zone, an honest absence
+    ``tradability.py`` documents) never arms, even when price sits within its own proximity band
+    and the tape state confirms the matching reading -- there is no A/B/C to scale a stop/reward/
+    size against. Exercised directly against ``_structure_tape_map_arm`` (never through a full
+    backtest run) so the SAME reading/price/side can be tested against BOTH an unclassified band
+    (900.0, resistance, singleton, no zone) and a classified one (300.0/300.05, resistance, class
+    C) as a clean positive/negative contrast."""
+    entries = CONFIG.strategy_definition(STRATEGY_TAPE_MAP_ID)["entries"]
+    # ask_absorption -> rejection short -> defends a CEILING -> RESISTANCE side (matches both
+    # bands' own side, isolating the class check alone).
+    null_point = _PathPoint(timestamp=0.0, last=900.2, spread=0.02, tape_state="ask_absorption")
+    arm = BacktestRunner._structure_tape_map_arm(
+        null_point, confluence_bar_store, _CONFLUENCE_SYMBOL, _STRUCTURE_TAPE_ANCHOR, entries, CONFIG
+    )
+    assert arm is None, "an unclassified band must never arm"
+
+    classified_point = _PathPoint(timestamp=0.0, last=300.02, spread=0.02, tape_state="ask_absorption")
+    arm2 = BacktestRunner._structure_tape_map_arm(
+        classified_point, confluence_bar_store, _CONFLUENCE_SYMBOL, _STRUCTURE_TAPE_ANCHOR, entries, CONFIG
+    )
+    assert arm2 is not None, "the SAME reading against a classified band at a nearby price must arm"
+    direction, setup_type, level, _opposing = arm2
+    assert (direction, setup_type) == ("short", "rejection")
+    assert level == {"price": 300.0, "timeframe": "1h", "class": "C"}
+
+
+def test_structure_tape_map_no_arm_when_symbol_has_no_recorded_bands(tmp_path, store, jobs):
+    # An empty bar store -> compute_tradability's own honest no_bar_series_for_symbol state ->
+    # zero fabricated arms (the identical structure_tape precedent, era-5B J-04 twinned).
+    empty_bar_store = BarStore(tmp_path / "empty-bars")
+    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-SELLER")
+    payload = _run(
+        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_MAP_ID, bar_store=empty_bar_store
+    )
+    assert payload["status"] == STATUS_DONE
+    assert payload["result"]["trades"] == []
+
+
+def test_structure_tape_map_identical_request_rerun_is_byte_identical(
+    tmp_path, store, jobs, confluence_bar_store
+):
+    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-SELLER")
+    first = _run(
+        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_MAP_ID, bar_store=confluence_bar_store
+    )
+    second = _run(
+        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_MAP_ID, bar_store=confluence_bar_store
+    )
+    assert first["id"] != second["id"]
+    assert json.dumps(first["result"], sort_keys=True) == json.dumps(second["result"], sort_keys=True)
+
+
+def test_structure_tape_map_reads_tradability_never_recomputes_levels_or_zones():
+    """Coherence-critical guard (the ``test_structure_tape_reads_levels_from_the_one_canonical_
+    compute_levels_owner`` precedent, applied to the NEW arming path): ``_structure_tape_map_arm``
+    itself must read the row-"Tradable level map" canonical ``compute_tradability`` owner and must
+    NEVER call ``compute_levels`` or re-derive pivots/zones directly -- the tradable map is the
+    ONLY lens this strategy reads."""
+    import inspect
+
+    src = inspect.getsource(BacktestRunner._structure_tape_map_arm)
+    assert "compute_tradability(" in src
+    for forbidden in ("compute_levels(", "_swing_pivots", "_prior_period_extremes", "_cluster_levels", "_grade_zone"):
+        assert forbidden not in src, f"_structure_tape_map_arm must not recompute levels itself: {forbidden}"
+
+
+def test_v1_and_structure_tape_byte_identical_after_structure_tape_map_added(
+    tmp_path, store, jobs, confluence_bar_store
+):
+    """Frozen-foundation regression guard (era-5B J-04 DoD): v1's and structure_tape's OWN pinned
+    outputs, re-asserted on the EXACT SAME fixtures/inputs their own tests above already prove,
+    now that structure_tape_map's additive dispatch branch exists beside them -- the ONE explicit,
+    named before/after checkpoint the DoD requires (not a second source of truth; every value here
+    is already independently pinned by a dedicated test earlier in this file)."""
+    dstore, meta = _record_structure_tape_dataset(tmp_path, "SIM-BUYER")
+    tape_payload = _run(
+        jobs, store, dstore, meta["id"], strategy_id=STRATEGY_TAPE_ID, bar_store=confluence_bar_store
+    )
+    t = tape_payload["result"]["trades"][0]
+    assert (t["setup_type"], t["direction"]) == ("breakthrough", "long")
+    assert t["entry"]["logical_ts"] == 19.5 and t["entry"]["price"] == 100.18
+    assert t["level"] == {"price": 100.00, "timeframe": "1h", "class": "A"}
+    assert t["exit"]["reason"] == EXIT_DATASET_END
+    _assert_structure_tape_trade_arithmetic(t, opposing_price=200.00)
+
+    dstore2, meta2 = _record_sim(tmp_path, "SIM-BUYER")
+    v1_payload = _run(jobs, store, dstore2, meta2["id"])
+    v1t = v1_payload["result"]["trades"][0]
+    assert (v1t["setup_type"], v1t["direction"]) == ("trend_continuation", "long")
+    assert v1t["entry"]["logical_ts"] == 24.5 and v1t["entry"]["price"] == 100.24
+    assert v1t["exit"]["reason"] == EXIT_HORIZON
+    assert "level" not in v1t
+
+
 # --- Exit coverage: every exit reason exercised deterministically ----------------------------------
 
 
diff --git a/apps/backend/tests/test_edge_report.py b/apps/backend/tests/test_edge_report.py
index 732733b..75738ee 100644
--- a/apps/backend/tests/test_edge_report.py
+++ b/apps/backend/tests/test_edge_report.py
@@ -34,18 +34,35 @@ from pathlib import Path
 
 import pytest
 
-from app.config import CONFIG, PROFILE_CANDIDATE_FASTER_WARMUP, PROFILE_DEFAULT, STRATEGY_V1_ID
+from app.config import (
+    CONFIG,
+    PROFILE_CANDIDATE_FASTER_WARMUP,
+    PROFILE_DEFAULT,
+    STRATEGY_TAPE_ID,
+    STRATEGY_TAPE_MAP_ID,
+    STRATEGY_V1_ID,
+)
 from app.providers.base import QuoteEvent, Side, TradeEvent
 from app.research import edge_report
 from app.research.backtests import BacktestJobManager, REGISTER, STATUS_DONE
+from app.research.bars import BarStore
 from app.research.datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN
-from app.research.edge_report import EdgeReportError, NO_POSITIVE_EDGE_FINDING, run_edge_report
+from app.research.edge_report import (
+    EdgeReportError,
+    NO_POSITIVE_EDGE_FINDING,
+    run_edge_report,
+    run_strategy_comparison_report,
+)
 from app.research.store import JournalStore
 
 BACKEND_DIR = Path(__file__).resolve().parents[1]
 # The committed miniature train + hold-out dataset pair (the SAME fixture test_backtests.py's /
 # test_pnl_scan.py's own fixture-pair tests use) — the keyless CI substrate.
 FIXTURE_DATASET_DIR = Path(__file__).parent / "fixtures" / "datasets"
+# The committed J-03 event-window fixture (symbol PG -- NOT a config-owned panel symbol, so it
+# never resolves an owning compute_setups event under the REAL registered panel; see
+# test_keyless_committed_j03_fixture_with_the_real_panel_is_an_honest_empty_report below).
+FIXTURE_J03_DATASET_DIR = Path(__file__).parent / "fixtures" / "datasets_j03"
 
 
 # --- deterministic synthetic substrates (recorded through the REAL store path) -------------------
@@ -404,9 +421,9 @@ def test_run_backtest_raises_explicit_error_when_status_is_not_done(tmp_path):
         jobs = BacktestJobManager(store, CONFIG)
         real_run_sync = jobs.run_sync
 
-        def _cancel_before_running(backtest_id, *, dataset_store):
+        def _cancel_before_running(backtest_id, *, dataset_store, bar_store=None):
             jobs.cancel(backtest_id)  # sets the cooperative-cancellation flag BEFORE the real run
-            real_run_sync(backtest_id, dataset_store=dataset_store)
+            real_run_sync(backtest_id, dataset_store=dataset_store, bar_store=bar_store)
 
         jobs.run_sync = _cancel_before_running
 
@@ -453,3 +470,356 @@ def test_cli_main_writes_a_report_and_exits_zero_on_the_fixture_pair(tmp_path, m
     assert payload["champion"] == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
     assert len(payload["train"]["datasets"]) == 1
     assert len(payload["holdout"]["datasets"]) == 1
+
+
+# ==================================================================================================
+# The 3-way strategy-comparison report (era-5B capability 6, J-04) — ``run_strategy_comparison_
+# report``. ``run_edge_report``/``main``/every fixture and test above this marker are UNTOUCHED —
+# the era-3 champion-only CLI stays byte-identical (proven by the whole suite above still passing).
+# ==================================================================================================
+
+from test_backtests import _sim_events  # noqa: E402
+from test_setups import SYM_A, _seed_full, _syn_config  # noqa: E402
+
+
+def _record_windowed(
+    dstore: DatasetStore, events: list, *, symbol: str, scenario: str, anchor: float,
+    split: str, feed: str, window_start: str, window_end: str,
+) -> dict:
+    """The IDENTICAL ``DatasetStore.record`` public path ``test_backtests._record`` /
+    ``test_edge_report._record`` already use, with EVERY provenance field (split/feed/window)
+    caller-controlled — the ONLY thing those two existing helpers hard-code that this section's
+    tests genuinely need to vary (a recorded window must CONTAIN a specific known scan event's
+    ``touch_ts``; a feed must genuinely differ to prove the no-pooling guard)."""
+    return dstore.record(
+        symbol=symbol, source=scenario, source_kind="reference", source_id=symbol,
+        split=split, window_start_utc=window_start, window_end_utc=window_end,
+        data_feed=feed, epoch_anchor=anchor, events=events,
+    )
+
+
+# The SAME synthetic multi-timeframe/multi-session scan fixture ``test_setups.py`` already proves
+# exhaustively (touch detection, reaction classification, forward returns) — reused VERBATIM here
+# (never a second copy) purely as the KNOWN, pinned SOURCE of classified touch events this report
+# joins recorded datasets against. Verified by direct computation (not hand-derived): scanning
+# ``_seed_full`` under ``_syn_config()`` emits exactly one clean, SINGLE-event session with a
+# classified band -- 2026-01-05 (SYM_A, resistance, class C, band [250.10, 250.20], reaction
+# "broke", touch_ts "2026-01-05T00:00:00.000000Z") -- so every dataset window below is sized to
+# contain THAT one touch_ts, keeping every scenario a clean, single, known cell.
+_SCAN_WINDOW = {"window_start": "2026-01-04T23:00:00Z", "window_end": "2026-01-05T01:00:00Z"}
+
+
+@pytest.fixture
+def scan_bar_store(tmp_path):
+    store = BarStore(tmp_path / "scan-bars")
+    _seed_full(store)
+    return store
+
+
+@pytest.fixture
+def scan_config():
+    return _syn_config()
+
+
+def _record_v1_arming_dataset(
+    dstore: DatasetStore, *, max_logical: float, split: str, feed: str, label: str
+) -> dict:
+    """One dataset recorded from a truncated SIM-BUYER stream (the EXISTING ``_sim_events`` fixture
+    reused verbatim): arms exactly one deterministic v1 trend_continuation-long trade (entry
+    24.5s@100.24, horizon exit 144.5s@101.28 -- the SAME pinned shape ``test_backtests.py``'s own
+    ``test_sim_buyer_arms_one_trend_continuation_long_with_horizon_exit`` proves), so its net_r/
+    net_usd are IDENTICAL across every recording (only the truncation length -- hence the file
+    checksum -- differs, avoiding ``DatasetAlreadyRegistered`` while keeping pooled sums exact and
+    predictable: n datasets pool to net_r == n * 5.050000000001056)."""
+    events, provider = _sim_events("SIM-BUYER", max_logical)
+    return _record_windowed(
+        dstore, events, symbol=SYM_A, scenario=f"edge-report-{label}", anchor=provider.epoch_anchor,
+        split=split, feed=feed, **_SCAN_WINDOW,
+    )
+
+
+# --- The keyless committed-fixture run (Key Test Scenario: exact cell shape) ---------------------
+
+
+def test_keyless_committed_j03_fixture_with_the_real_panel_is_an_honest_empty_report(tmp_path, store):
+    """The literal DoD scenario: ``run_strategy_comparison_report`` over the COMMITTED
+    ``datasets_j03/`` fixture (symbol PG) under the REAL, shipped ``CONFIG`` (the config-owned
+    12-symbol panel, which does NOT include PG). PG can never resolve an owning scan event under
+    the real panel, so every cell is honestly absent — the degenerate, valid case of "all cells
+    insufficient_sample" (vacuously: there are none to violate the gate). An empty ``BarStore`` is
+    sufficient (and proves ``compute_setups`` never needs PG's own bars to reach this honest
+    empty state — the panel-symbol filter excludes it before any bar read)."""
+    dataset_store = DatasetStore(FIXTURE_J03_DATASET_DIR)
+    bar_store = BarStore(tmp_path / "empty-bars")
+
+    report = run_strategy_comparison_report(store, dataset_store, bar_store, CONFIG)
+
+    assert report["register"] == REGISTER
+    assert report["pnl_min_sample_size"] == CONFIG.pnl_min_sample_size
+    assert report["train"]["cells"] == []
+    assert report["holdout"]["cells"] == []
+    assert report["surviving_train_cells"] == []
+    assert "champion" not in report  # this report is never about a single champion pointer
+
+
+def test_empty_registry_3way_report_is_honest_and_empty(tmp_path, store):
+    dataset_store = DatasetStore(tmp_path / "datasets")  # never populated
+    bar_store = BarStore(tmp_path / "empty-bars")
+
+    report = run_strategy_comparison_report(store, dataset_store, bar_store, CONFIG)
+
+    assert report["train"]["cells"] == []
+    assert report["holdout"]["cells"] == []
+    assert report["surviving_train_cells"] == []
+
+
+# --- Real join + real cells over a synthetic scan (Key Test Scenario: exact cell structure) -------
+
+
+def test_synthetic_scan_join_produces_real_cells_all_insufficient_sample(
+    tmp_path, store, scan_bar_store, scan_config
+):
+    """ONE recorded dataset, windowed around the KNOWN 2026-01-05 class-C/broke/resistance scan
+    event, produces exactly THREE cells (v1 / structure_tape / structure_tape_map) — the exact
+    strategy x class x side x reaction shape the DoD names. v1 arms its one deterministic
+    trend_continuation trade (this fixture's bars are unrelated to structure_tape/
+    structure_tape_map's OWN arming source, so both honestly arm zero — never fabricated). Every
+    cell is ``insufficient_sample`` at n=1/n=0, below the shipped default minimum of 5 — the
+    literal "keyless run is expected all-insufficient_sample" DoD phrasing, realized here with a
+    genuinely non-empty, real cell set (not the vacuous empty case above)."""
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    meta = _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+
+    report = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)
+
+    cells = report["train"]["cells"]
+    assert {c["strategy_id"] for c in cells} == {STRATEGY_V1_ID, STRATEGY_TAPE_ID, STRATEGY_TAPE_MAP_ID}
+    for cell in cells:
+        assert cell["band_class"] == "C"
+        assert cell["band_side"] == "resistance"
+        assert cell["reaction"] == "broke"
+        assert cell["feed"] == "sim"
+        assert cell["dataset_ids"] == [meta["id"]]
+        assert cell["insufficient_sample"] is True  # every n below the shipped minimum of 5
+
+    v1_cell = next(c for c in cells if c["strategy_id"] == STRATEGY_V1_ID)
+    assert v1_cell["measurement"]["n"] == 1
+    assert v1_cell["measurement"]["net_r"] == pytest.approx(5.050000000001056)
+    assert v1_cell["measurement"]["win_rate"] == 1.0
+    for other_id in (STRATEGY_TAPE_ID, STRATEGY_TAPE_MAP_ID):
+        other_cell = next(c for c in cells if c["strategy_id"] == other_id)
+        assert other_cell["measurement"] == {
+            "n": 0, "gross_r": 0.0, "net_r": 0.0, "gross_usd": 0.0, "net_usd": 0.0,
+            "win_rate": None, "max_drawdown_r": None,
+        }
+    assert report["holdout"]["cells"] == []
+    assert report["surviving_train_cells"] == []  # n=1 fails the n>=5 gate on every cell
+    assert "champion" not in report
+
+
+def test_every_cell_carries_the_full_register_and_a_null_baseline(tmp_path, store, scan_bar_store, scan_config):
+    _record_v1_arming_dataset(
+        DatasetStore(tmp_path / "datasets"), max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a"
+    )
+    dataset_store = DatasetStore(tmp_path / "datasets")
+
+    report = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)
+
+    assert report["register"] == REGISTER == "simulated — assumed fees/slippage — not indicative of live results"
+    for cell in report["train"]["cells"]:
+        for key in ("n", "gross_r", "net_r", "gross_usd", "net_usd", "win_rate", "max_drawdown_r"):
+            assert key in cell["measurement"]
+            assert key in cell["null_baseline"]
+        assert cell["null_baseline"]["n"] == CONFIG.backtest_null_entry_count
+
+
+# --- No feed pooling (a two-feed input never merges into one cell) -------------------------------
+
+
+def test_two_same_feed_datasets_pool_and_a_different_feed_never_pools(
+    tmp_path, store, scan_bar_store, scan_config
+):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    meta_a = _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    meta_b = _record_v1_arming_dataset(dataset_store, max_logical=200.0, split=SPLIT_TRAIN, feed="sim", label="b")
+    meta_c = _record_v1_arming_dataset(dataset_store, max_logical=175.0, split=SPLIT_TRAIN, feed="iex", label="c")
+
+    report = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)
+
+    v1_cells = [c for c in report["train"]["cells"] if c["strategy_id"] == STRATEGY_V1_ID]
+    assert len(v1_cells) == 2  # sim and iex NEVER merge into one cell
+    by_feed = {c["feed"]: c for c in v1_cells}
+    assert set(by_feed) == {"sim", "iex"}
+
+    sim_cell = by_feed["sim"]
+    assert sim_cell["dataset_ids"] == sorted([meta_a["id"], meta_b["id"]])
+    assert sim_cell["measurement"]["n"] == 2
+    assert sim_cell["measurement"]["net_r"] == pytest.approx(2 * 5.050000000001056)
+    assert sim_cell["measurement"]["win_rate"] == 1.0  # both pooled trades are winners
+
+    iex_cell = by_feed["iex"]
+    assert iex_cell["dataset_ids"] == [meta_c["id"]]
+    assert iex_cell["measurement"]["n"] == 1
+    assert iex_cell["measurement"]["net_r"] == pytest.approx(5.050000000001056)
+
+    # No pooled/merged/combined key exists anywhere in the report (the run_edge_report precedent).
+    text = json.dumps(report)
+    for forbidden_key in ('"combined"', '"pooled"', '"all_feeds"'):
+        assert forbidden_key not in text
+
+
+# --- Train and hold-out stay in separate sections, never pooled (Key Test Scenario) ---------------
+
+
+def test_train_and_holdout_cells_stay_separate_never_pooled(tmp_path, store, scan_bar_store, scan_config):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    train_meta = _record_v1_arming_dataset(
+        dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="train"
+    )
+    holdout_meta = _record_v1_arming_dataset(
+        dataset_store, max_logical=225.0, split=SPLIT_HOLDOUT, feed="sim", label="holdout"
+    )
+
+    report = run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)
+
+    train_v1 = next(c for c in report["train"]["cells"] if c["strategy_id"] == STRATEGY_V1_ID)
+    holdout_v1 = next(c for c in report["holdout"]["cells"] if c["strategy_id"] == STRATEGY_V1_ID)
+    assert train_v1["dataset_ids"] == [train_meta["id"]]
+    assert holdout_v1["dataset_ids"] == [holdout_meta["id"]]
+    assert train_v1["measurement"]["n"] == 1
+    assert holdout_v1["measurement"]["n"] == 1  # NEVER 2 -- the two splits never pool together
+    assert set(report.keys()) >= {"train", "holdout"}
+    assert "cells" not in report  # no top-level pooled cell list outside the two sections
+
+
+# --- The champion pointer is never read, moved, or promoted (no-hand-promotion guard) -------------
+
+
+def test_champion_pointer_unchanged_after_a_3way_report_run(tmp_path, store, scan_bar_store, scan_config):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    before = store.get_champion_pointer()
+
+    run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)
+
+    assert store.get_champion_pointer() == before == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
+
+
+# --- Hot-path guard: compute_setups runs at most ONCE per report call (audit B2 carry-item) --------
+
+
+def test_compute_setups_runs_at_most_once_per_report_call(tmp_path, store, scan_bar_store, scan_config, monkeypatch):
+    calls = []
+    real_compute_setups = edge_report.compute_setups
+
+    def _counting_compute_setups(*args, **kwargs):
+        calls.append(1)
+        return real_compute_setups(*args, **kwargs)
+
+    monkeypatch.setattr(edge_report, "compute_setups", _counting_compute_setups)
+
+    # Empty registry: never even worth a full panel scan.
+    run_strategy_comparison_report(store, DatasetStore(tmp_path / "empty-datasets"), scan_bar_store, scan_config)
+    assert len(calls) == 0
+
+    # Non-empty registry: exactly ONE call for the WHOLE report (never once per dataset, never
+    # once per split — train + holdout share the SAME scan).
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+    _record_v1_arming_dataset(dataset_store, max_logical=225.0, split=SPLIT_HOLDOUT, feed="sim", label="b")
+    run_strategy_comparison_report(store, dataset_store, scan_bar_store, scan_config)
+    assert len(calls) == 1
+
+
+# --- Determinism: two independent runs of the identical scenario are byte-identical ---------------
+
+
+def test_3way_report_determinism_two_independent_runs_are_byte_identical(
+    tmp_path, scan_bar_store, scan_config
+):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    _record_v1_arming_dataset(dataset_store, max_logical=150.0, split=SPLIT_TRAIN, feed="sim", label="a")
+
+    store_a = JournalStore(str(tmp_path / "journal-a.db"), scan_config)
+    store_b = JournalStore(str(tmp_path / "journal-b.db"), scan_config)
+    try:
+        first = run_strategy_comparison_report(store_a, dataset_store, scan_bar_store, scan_config)
+        second = run_strategy_comparison_report(store_b, dataset_store, scan_bar_store, scan_config)
+        assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
+    finally:
+        store_a.close()
+        store_b.close()
+
+
+# --- Gate-integrity: the ranking/surviving-cell logic itself (a pure-function proof, the
+# ``test_rank_orders_by_net_r_descending_with_dataset_id_tiebreak`` precedent -- representative
+# already-computed measurement rows, never a fabricated backtest) --------------------------------
+
+
+def _cell(strategy_id, band_class, reaction, *, n, net_r, net_usd, null_net_r, null_net_usd, feed="sim"):
+    return {
+        "strategy_id": strategy_id,
+        "band_class": band_class,
+        "band_side": "resistance",
+        "reaction": reaction,
+        "feed": feed,
+        "dataset_ids": ["x"],
+        "measurement": {
+            "n": n, "gross_r": net_r, "net_r": net_r, "gross_usd": net_usd, "net_usd": net_usd,
+            "win_rate": 1.0 if n else None, "max_drawdown_r": 0.0 if n else None,
+        },
+        "null_baseline": {
+            "n": 100, "gross_r": null_net_r, "net_r": null_net_r, "gross_usd": null_net_usd,
+            "net_usd": null_net_usd, "win_rate": 0.4, "max_drawdown_r": 1.0,
+        },
+        "insufficient_sample": n < CONFIG.pnl_min_sample_size,
+    }
+
+
+def test_surviving_train_cells_clears_every_gate_and_carries_holdout_status():
+    clearing = _cell("v1", "A", "broke", n=5, net_r=4.0, net_usd=400.0, null_net_r=1.0, null_net_usd=100.0)
+    below_minimum_n = _cell("v1", "B", "broke", n=2, net_r=4.0, net_usd=400.0, null_net_r=1.0, null_net_usd=100.0)
+    fails_beat_null = _cell("v1", "C", "broke", n=5, net_r=0.5, net_usd=50.0, null_net_r=1.0, null_net_usd=100.0)
+    negative_net_r = _cell("v1", "A", "chopped", n=5, net_r=-1.0, net_usd=-100.0, null_net_r=-2.0, null_net_usd=-200.0)
+    train_cells = [clearing, below_minimum_n, fails_beat_null, negative_net_r]
+
+    matching_holdout = _cell("v1", "A", "broke", n=5, net_r=3.0, net_usd=300.0, null_net_r=0.5, null_net_usd=50.0)
+    holdout_cells = [matching_holdout]
+
+    survivors = edge_report._surviving_train_cells(train_cells, holdout_cells, CONFIG)
+
+    assert len(survivors) == 1
+    assert survivors[0]["train_cell"] == clearing
+    assert survivors[0]["holdout_cell"] == matching_holdout
+    assert survivors[0]["holdout_positive_edge"] is True
+
+
+def test_surviving_train_cells_honest_absence_when_no_holdout_data_exists_yet():
+    clearing = _cell("v1", "A", "broke", n=5, net_r=4.0, net_usd=400.0, null_net_r=1.0, null_net_usd=100.0)
+
+    survivors = edge_report._surviving_train_cells([clearing], [], CONFIG)
+
+    assert len(survivors) == 1
+    assert survivors[0]["holdout_cell"] is None
+    assert survivors[0]["holdout_positive_edge"] is False  # never fabricated True on absent data
+
+
+def test_surviving_train_cells_ranks_by_net_r_descending_with_deterministic_tiebreak():
+    lower = _cell("v1", "A", "broke", n=5, net_r=2.0, net_usd=200.0, null_net_r=0.1, null_net_usd=10.0)
+    higher = _cell("structure_tape", "A", "broke", n=5, net_r=3.0, net_usd=300.0, null_net_r=0.1, null_net_usd=10.0)
+
+    survivors = edge_report._surviving_train_cells([lower, higher], [], CONFIG)
+
+    assert [s["train_cell"]["strategy_id"] for s in survivors] == ["structure_tape", "v1"]
+
... [diff_bound] apps/backend/tests/test_edge_report.py: 11 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index 9bba8b2..e362c92 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -60,6 +60,7 @@ EXPECTED_TOOLS = (
     "setups",
     "backtests",
     "strategies",
+    "edge_report",
     "pnl_ledger",
     "taxonomy",
     "ui_route_map",
@@ -535,6 +536,47 @@ async def test_strategies_tool_byte_identical_on_a_non_empty_live_result(mcp_env
     assert result.content[0].text.encode("utf-8") == rest.content, "strategies not byte-identical"
 
 
+@pytest.mark.anyio
+async def test_edge_report_tool_byte_identical_to_rest(mcp_env):
+    """``edge_report`` (era-5B J-04) ships in the SAME iteration as its endpoint — the report
+    dict (``register``/``pnl_min_sample_size``/``train``/``holdout``/``surviving_train_cells``)
+    is ALWAYS present (an empty dataset registry is an honest, well-formed 200 — never an error),
+    so this proves byte-identity with no seeding at all, the ``strategies`` tool's own precedent."""
+    result = await call_tool("edge_report", {})
+    rest = httpx.get(f"{mcp_env}/research/edge-report", timeout=5.0)
+    assert rest.status_code == 200
+    payload = rest.json()
+    assert set(payload) >= {"register", "pnl_min_sample_size", "train", "holdout", "surviving_train_cells"}
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "edge_report not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_edge_report_tool_byte_identical_after_recording_a_real_dataset(mcp_env):
+    """The IDENTICAL ``datasets``/``backtests`` "flips from empty to a real state with ZERO MCP
+    code changes" precedent: after recording a real dataset through the live backend, the tool's
+    JSON is still byte-identical to its curl equivalent (still an honest empty ``cells`` list here
+    — PG, the reference fixture's symbol, is not a config-owned panel symbol — but the byte-proxy
+    discipline itself is what this test exists to prove, on a request that now does real work)."""
+    recorded = httpx.post(
+        f"{mcp_env}/research/datasets",
+        json={
+            "source_kind": "reference",
+            "split": "train",
+            "start": "2026-06-09T17:01:00Z",
+            "end": "2026-06-09T17:01:30Z",
+        },
+        timeout=15.0,
+    )
+    assert recorded.status_code in (200, 409)  # 409 = already recorded by an earlier test
+    result = await call_tool("edge_report", {})
+    rest = httpx.get(f"{mcp_env}/research/edge-report", timeout=15.0)
+    assert rest.status_code == 200
+    assert result.isError is False
+    assert result.content[0].text.encode("utf-8") == rest.content, "edge_report not byte-identical"
+
+
 @pytest.mark.anyio
 async def test_pnl_ledger_tool_byte_identical_on_a_non_empty_200(mcp_env, backend_paths):
     """J-04 flips ``pnl_ledger`` — the LAST honest 404 — to live data with ZERO MCP code changes
diff --git a/apps/backend/tests/test_strategies_api.py b/apps/backend/tests/test_strategies_api.py
index ad39329..9c0f878 100644
--- a/apps/backend/tests/test_strategies_api.py
+++ b/apps/backend/tests/test_strategies_api.py
@@ -12,7 +12,14 @@ from __future__ import annotations
 import pytest
 from fastapi.testclient import TestClient
 
-from app.config import CONFIG, PROFILE_CANDIDATE_FASTER_WARMUP, PROFILE_DEFAULT, STRATEGY_TAPE_ID, STRATEGY_V1_ID
+from app.config import (
+    CONFIG,
+    PROFILE_CANDIDATE_FASTER_WARMUP,
+    PROFILE_DEFAULT,
+    STRATEGY_TAPE_ID,
+    STRATEGY_TAPE_MAP_ID,
+    STRATEGY_V1_ID,
+)
 from app.main import app, manager
 from app.research.routes import ResearchRegistry, set_registry
 from app.research.store import JournalStore
@@ -34,16 +41,22 @@ def ctx(tmp_path, monkeypatch):
     store.close()
 
 
-def test_strategies_lists_v1_and_structure_tape_in_registration_order(ctx):
+def test_strategies_lists_v1_structure_tape_then_structure_tape_map_in_registration_order(ctx):
     """The exact config-owned registry state, pinned: ``v1`` (frozen) plus the additive
-    ``structure_tape`` — a registry, never a single hard-coded strategy."""
+    ``structure_tape`` and ``structure_tape_map`` — a registry, never a single hard-coded
+    strategy."""
     client, _store = ctx
     response = client.get("/research/strategies")
     assert response.status_code == 200
     payload = response.json()
-    assert [s["strategy_id"] for s in payload["strategies"]] == [STRATEGY_V1_ID, STRATEGY_TAPE_ID]
+    assert [s["strategy_id"] for s in payload["strategies"]] == [
+        STRATEGY_V1_ID,
+        STRATEGY_TAPE_ID,
+        STRATEGY_TAPE_MAP_ID,
+    ]
     assert payload["strategies"][0] == CONFIG.strategy_definition(STRATEGY_V1_ID)
     assert payload["strategies"][1] == CONFIG.strategy_definition(STRATEGY_TAPE_ID)
+    assert payload["strategies"][2] == CONFIG.strategy_definition(STRATEGY_TAPE_MAP_ID)
 
 
 def test_strategies_serves_the_founding_champion(ctx):
@@ -72,6 +85,7 @@ def test_strategies_champion_reflects_a_moved_pointer_the_same_pointer_profiles_
     assert [s["strategy_id"] for s in strategies_payload["strategies"]] == [
         STRATEGY_V1_ID,
         STRATEGY_TAPE_ID,
+        STRATEGY_TAPE_MAP_ID,
     ]
 
 
@@ -90,7 +104,11 @@ def test_strategies_module_carries_no_second_copy_of_the_id_strings():
     source = (
         Path(__file__).resolve().parents[1] / "app" / "research" / "strategies.py"
     ).read_text()
-    for literal in ('"v1"', "'v1'", f'"{STRATEGY_TAPE_ID}"', f"'{STRATEGY_TAPE_ID}'"):
+    for literal in (
+        '"v1"', "'v1'",
+        f'"{STRATEGY_TAPE_ID}"', f"'{STRATEGY_TAPE_ID}'",
+        f'"{STRATEGY_TAPE_MAP_ID}"', f"'{STRATEGY_TAPE_MAP_ID}'",
+    ):
         assert literal not in source, f"duplicated id literal {literal} in app/research/strategies.py"
 
 
@@ -139,6 +157,50 @@ def test_backtest_accepts_structure_tape_strategy_id(ctx):
         assert by_class[cls]["insufficient_sample"] is True
 
 
+def test_backtest_accepts_structure_tape_map_strategy_id(ctx):
+    """era-5B J-04: ``POST /research/backtests`` accepts ``structure_tape_map`` with NO
+    route-validation change (the identical ``structure_tape`` precedent directly above —
+    ``Config.strategy_definition`` is the one registry both this route and ``GET
+    /research/strategies`` consult)."""
+    client, _store = ctx
+    dataset = client.post(
+        "/research/datasets",
+        json={
+            "source_kind": "reference",
+            "split": "train",
+            "start": "2026-06-09T17:00:00Z",
+            "end": "2026-06-09T17:00:30Z",
+        },
+    ).json()["dataset"]
+    r = client.post(
+        "/research/backtests",
+        json={"dataset_id": dataset["id"], "strategy_id": STRATEGY_TAPE_MAP_ID, "profile": PROFILE_DEFAULT},
+    )
+    assert r.status_code == 200, r.text
+    created = r.json()["backtest"]
+    assert created["strategy_id"] == STRATEGY_TAPE_MAP_ID
+
+    import time
+
+    deadline = time.time() + 30
+    payload = None
+    while time.time() < deadline:
+        payload = client.get(f"/research/backtests/{created['id']}").json()["backtest"]
+        if payload["status"] in ("done", "failed", "cancelled"):
+            break
+        time.sleep(0.05)
+    assert payload["status"] == "done", payload.get("error")
+    assert payload["result"]["strategy_id"] == STRATEGY_TAPE_MAP_ID
+    # No tradable-map bands were ever recorded for this symbol in this test -- an honest empty
+    # trade list (zero fabricated arms), never a fallback to v1-like behaviour.
+    assert payload["result"]["trades"] == []
+    by_class = payload["result"]["aggregates_by_class"]
+    assert set(by_class) == {"A", "B", "C"}
+    for cls in ("A", "B", "C"):
+        assert by_class[cls]["n"] == 0
+        assert by_class[cls]["insufficient_sample"] is True
+
+
 def test_unregistered_strategy_id_is_still_422_never_coerced(ctx):
     client, _store = ctx
     dataset = client.post(
diff --git a/apps/backend/tests/test_edge_report_api.py b/apps/backend/tests/test_edge_report_api.py
new file mode 100644
index 0000000..34a226d
--- /dev/null
+++ b/apps/backend/tests/test_edge_report_api.py
@@ -0,0 +1,124 @@
+"""``GET /research/edge-report`` (era-5B capability 6, J-04) -- route-level integration. Mirrors
+``test_strategies_api.py``'s ``ctx`` fixture (TestClient + temp journal/dataset/bar dirs): the
+route wiring, non-GET 405, byte-identity to the module's own ``run_strategy_comparison_report``,
+and one real recorded-dataset smoke test through the ACTUAL ``POST /research/datasets`` route --
+the full request path, never a direct module call (``test_edge_report.py`` covers the pure
+computation's exact cell values and gate logic in isolation).
+"""
+
+from __future__ import annotations
+
+import json
+
+import pytest
+from fastapi.testclient import TestClient
+
+from app.config import CONFIG
+from app.main import app, manager
+from app.research.bars import BarStore
+from app.research.datasets import DatasetStore
+from app.research.edge_report import REGISTER, run_strategy_comparison_report
+from app.research.routes import ResearchRegistry, get_bar_store, set_registry
+from app.research.store import JournalStore
+
+
+@pytest.fixture
+def ctx(tmp_path, monkeypatch):
+    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
+    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
+    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
+    registry = ResearchRegistry(store, CONFIG)
+    set_registry(registry)
+    with TestClient(app) as c:
+        yield c, store, tmp_path
+    registry.backtest_jobs.join_all(timeout=10.0)
+    for ticker in list(manager._engines.keys()):
+        manager.stop(ticker)
+    set_registry(None)
+    store.close()
+
+
+def test_edge_report_empty_registry_is_an_honest_200(ctx):
+    client, _store, _tmp_path = ctx
+    response = client.get("/research/edge-report")
+    assert response.status_code == 200
+    payload = response.json()
+    assert payload["register"] == REGISTER
+    assert payload["pnl_min_sample_size"] == CONFIG.pnl_min_sample_size
+    assert payload["train"]["cells"] == []
+    assert payload["holdout"]["cells"] == []
+    assert payload["surviving_train_cells"] == []
+    assert "champion" not in payload  # this report is never about a single champion pointer
+
+
+def test_edge_report_matches_the_module_function_byte_for_byte(ctx):
+    """Single source of truth: the route's JSON is a VERBATIM serving of
+    ``run_strategy_comparison_report`` — never a second computation. Recording one dataset
+    through the real API first proves this on a genuinely non-trivial (if still
+    ``insufficient_sample``-shaped) payload, not merely the vacuous empty case."""
+    client, store, tmp_path = ctx
+    recorded = client.post(
+        "/research/datasets",
+        json={
+            "source_kind": "reference",
+            "split": "train",
+            "start": "2026-06-09T17:00:00Z",
+            "end": "2026-06-09T17:00:30Z",
+        },
+    )
+    assert recorded.status_code == 200, recorded.text
+
+    route_payload = client.get("/research/edge-report").json()
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    bar_store = BarStore(tmp_path / "bars")
+    direct = run_strategy_comparison_report(store, dataset_store, bar_store, CONFIG)
+    assert json.dumps(route_payload, sort_keys=True) == json.dumps(direct, sort_keys=True)
+    # PG (the reference fixture's own symbol) is not a config-owned panel symbol, so this
+    # recording honestly resolves no owning scan event -- still an empty, valid cell list.
+    assert route_payload["train"]["cells"] == []
+
+
+def test_edge_report_integrity_failure_is_an_explicit_500_never_a_partial_report(ctx, monkeypatch):
+    """A dataset failing checksum verification aborts the WHOLE report — the
+    ``create_backtest``/``DatasetIntegrityError`` precedent, mapped explicitly rather than
+    surfacing a raw 500 traceback or a silently-partial 200."""
+    client, _store, tmp_path = ctx
+    recorded = client.post(
+        "/research/datasets",
+        json={
+            "source_kind": "reference",
+            "split": "train",
+            "start": "2026-06-09T17:00:00Z",
+            "end": "2026-06-09T17:00:30Z",
+        },
+    )
+    assert recorded.status_code == 200, recorded.text
+    dataset_id = recorded.json()["dataset"]["id"]
+    path = tmp_path / "datasets" / f"{dataset_id}.json"
+    data = json.loads(path.read_text())
+    data["record"]["meta"]["checksum"] = "0" * 64  # tamper
+    path.write_text(json.dumps(data))
+
+    response = client.get("/research/edge-report")
+    assert response.status_code == 500
+    assert "integrity" in response.json()["detail"].lower()
+
+
+def test_non_get_verbs_are_405_no_write_surface_exists(ctx):
+    client, _store, _tmp_path = ctx
+    for method in ("post", "put", "patch", "delete"):
+        response = getattr(client, method)("/research/edge-report")
+        assert response.status_code == 405, f"{method.upper()} must be Method Not Allowed"
+
+
+def test_edge_report_route_wired_through_the_existing_get_bar_store_seam():
+    """A coherence guard (never a second bar-store construction): the route depends on the SAME
+    ``get_bar_store`` seam every other bar-reading route already uses."""
+    import inspect
+
+    from app.research import routes
+
+    src = inspect.getsource(routes.get_edge_report)
+    assert "Depends(get_bar_store)" in src
+    assert "Depends(get_dataset_store)" in src
+    assert get_bar_store is routes.get_bar_store
```
