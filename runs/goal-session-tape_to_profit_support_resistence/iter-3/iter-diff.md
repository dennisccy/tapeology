# Iteration diff (bounded)

Files changed: 37. Shown in full: 28.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `reports/goal-session-tape_to_profit_support_resistence-index.html` (45 diff lines)
- `reports/phase-goal-tape_to_profit_support_resistence-iter-2-iteration-summary.md` (97 diff lines)
- `reports/phase-goal-tape_to_profit_support_resistence-iter-2-summary.html` (42 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/iter-3/.steps/decomposer.done` (7 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/iter-3/goal-slice.md` (311 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/iter-3/snapshot-sha` (8 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/state/project-story.md` (26 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/telemetry.jsonl` (22 diff lines)
- `runs/goal-session-tape_to_profit_support_resistence/trace/trace.jsonl` (20 diff lines)

```diff
diff --git a/README.md b/README.md
index 749a9a5..542bcaa 100644
--- a/README.md
+++ b/README.md
@@ -70,8 +70,9 @@ Current capabilities:
 - **Baseline-edge report (command-line research tool)** — measures the current champion strategy across every dataset ever recorded, then ranks the results best-to-worst separately within the training data and within the held-out data (the two are never mixed together). Each dataset's result is shown in R-multiples and dollars, with its trade count, beside a random-entry comparison line. A dataset only earns a "positive edge" mark on its held-out side, and only when the result is genuinely profitable, has enough trades to trust, and beats the random comparison — not merely because the sign looks favorable. When nothing clears that bar — including when no datasets have been recorded yet — the report says so plainly ("no positive-edge dataset") instead of manufacturing a favorable result; it changes nothing else in the product (no promotion, no ledger write, no champion change) and produces a byte-identical report on repeated runs.
 - **Performance page** — a fourth top-level page (reachable from the top navigation bar on every page) renders the profit-and-loss ledger and the current champion strategy and indicator profile verbatim from their canonical endpoints — nothing is recalculated or rounded for display. Each ledger row shows net return in both R-multiples and dollars for the train and hold-out splits, kept strictly separate with their own trade counts; a split with too few trades to draw a conclusion from is labeled "insufficient sample" rather than shown as a real result, and a missing prior baseline (the founding row) is shown as explicitly absent rather than a fabricated zero. Every figure carries the same "simulated — assumed fees/slippage — not indicative of live results" register used elsewhere in the product.
 - **Multi-timeframe historical bar store (research API)** — record a real historical OHLC (open/high/low/close) price-bar series for a symbol at daily, weekly, monthly, hourly, and other calendar timeframes, and keep the saved copy — its symbol, timeframe, exact time window, source feed, and bar count — forever, unchanged. Every recorded series carries two layers of built-in checksums, re-verified on every read; a corrupted file surfaces an explicit error rather than silently serving bad data, and recording the exact same series twice is refused with a message pointing at the original rather than silently duplicating it. Reading a saved series back returns byte-identical results run after run. Missing market-data credentials produce a clear, explicit message rather than invented price data. Watching a ticker in the live cockpit never records a bar series — recording is a separate, explicit research action. A committed fixture proves the full record-then-read round trip with no credentials. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
-- **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `POST /research/thesis`, `GET /research/thesis/active`, `GET /research/taxonomy`, `GET /research/analytics`, `GET /research/journal`, `GET /research/journal/{id}`, `POST /research/thesis/{id}/action`, `GET /research/studies`, `POST /research/studies`, `POST /research/studies/{id}/cancel`, `GET /research/hints/active`, `GET /research/hints`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /meta/ui-routes`.
-- **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, journal, studies, datasets, backtests, PnL ledger, bar series, and navigation data a person sees. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
+- **Support/resistance level detection (research API)** — from any recorded bar series, compute the horizontal price levels where a symbol has structurally turned: swing pivots (a bar's high or low that is the extreme among its surrounding neighbours) and prior-period extremes (the prior day/week/month's high, low, or close), each stamped with its timeframe, how it was derived, its touch count, and an overall strength score that weights longer timeframes and more touches higher. Every one of those parameters comes from one central config — nothing is hard-coded or invented on the fly. Levels computed "as of" a given time use only bars recorded at or before that moment; a bar recorded later can never change an earlier answer — proven directly by comparing the same query against a store with and without the later bars physically removed. Identical requests always return byte-identical results. A symbol with no bar history at all gets an explicitly different message than a symbol that has history but no notable levels yet — the two "nothing to show" cases are never conflated. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
+- **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `POST /research/thesis`, `GET /research/thesis/active`, `GET /research/taxonomy`, `GET /research/analytics`, `GET /research/journal`, `GET /research/journal/{id}`, `POST /research/thesis/{id}/action`, `GET /research/studies`, `POST /research/studies`, `POST /research/studies/{id}/cancel`, `GET /research/hints/active`, `GET /research/hints`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/levels`, `GET /meta/ui-routes`.
+- **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, journal, studies, datasets, backtests, PnL ledger, bar series, support/resistance levels, and navigation data a person sees. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
 <!-- /AUTO:capabilities -->
 
 This project embeds the [`incredible_auto_dev`](https://github.com/dennisccy/incredible_auto_dev)
diff --git a/apps/backend/app/config.py b/apps/backend/app/config.py
index 2b89caa..330ad3a 100644
--- a/apps/backend/app/config.py
+++ b/apps/backend/app/config.py
@@ -1109,6 +1109,42 @@ class Config:
         }
     )
 
+    # --- Structure-and-tape era: confluence zones + A/B/C conviction classes (era-4 capability 3,
+    # J-03) -- RESEARCH DEFAULTS, the SAME ``sr_pivot_lookback`` discipline directly above: a
+    # starting point, never a validated edge; every research value lives in config with its
+    # rationale documented HERE, no literal in ``research/levels.py``. Namespaced ``sr_confluence_*``
+    # -- the same ``sr_`` family as the J-02 level-detection parameters above (one research
+    # computation), never colliding with the unrelated intraday tape setups.
+    #
+    # CONFLUENCE BAND (basis points of a zone's ANCHOR price -- its first, lowest-priced member):
+    # levels pooled across EVERY timeframe join the same confluence zone iff their price falls
+    # within ``price * sr_confluence_band_bps / 10_000`` of the zone's anchor (an anchor-fixed scan,
+    # never a pairwise/chained comparison, so a zone's price span is bounded by ONE tolerance window
+    # rather than an unbounded chain of near-neighbours -- see ``_cluster_levels``). Wider than
+    # ``sr_touch_tolerance_bps`` (5.0) because INDEPENDENT timeframes' own detected extremes rarely
+    # land on the exact same price the way a single series' own touches do, yet bounded so it does
+    # not smear together clearly distinct levels -- calibrated against the committed PG fixture: at
+    # 20 bps its real 1h/1d level set forms several distinct, informative zones (never one
+    # degenerate blob spanning the whole price range), verified by direct computation in
+    # ``tests/test_levels.py``.
+    sr_confluence_band_bps: float = 20.0
+    # CLASS A: a zone earns the highest conviction grade iff it has AT LEAST this many DISTINCT
+    # timeframes among its members AND at least one of those timeframes is in the long-term bucket
+    # (``PRIOR_PERIOD_TIMEFRAMES`` -- reused verbatim, no second "long-term" list) -- goal.md's own
+    # hypothesis ("levels that align across timeframes matter more"), with a long-term anchor
+    # specifically named ("a required long-term member"). The committed PG fixture stores only TWO
+    # timeframes (1h, 1d), so it can never itself produce a class A zone -- an honest, documented
+    # consequence of the committed data's own breadth, not a defect (proven instead on a dedicated
+    # synthetic 3-timeframe fixture; see ``tests/test_levels.py``).
+    sr_confluence_class_a_min_timeframes: int = 3
+    # CLASS B: the lesser bar -- at least this many DISTINCT timeframes (but not enough, or not
+    # long-term enough, to qualify for A). A qualifying cluster (>= 2 members, structurally
+    # guaranteed by ``_cluster_levels``) whose members are ALL from a SINGLE timeframe (e.g. two
+    # nearby swing pivots on the same 1h series) does not clear this floor and grades C instead --
+    # genuine cross-timeframe confluence is a strictly higher bar than mere same-timeframe price
+    # proximity (which each level's own ``touch_count`` already captures).
+    sr_confluence_class_b_min_timeframes: int = 2
+
     def profile_definition(self, profile_id: str) -> dict | None:
         """The config-owned descriptor for ``profile_id`` (Data Contract row 33) — the
         ``strategy_definition`` pattern applied to profiles: THIS method is the ONE place that
@@ -1320,6 +1356,16 @@ class Config:
             "sr_pivot_lookback",
             "sr_touch_tolerance_bps",
             "sr_timeframe_weights",
+            # The confluence-zone clustering band + A/B/C class-threshold parameters (era-4
+            # capability 3, J-03): the IDENTICAL ``sr_pivot_lookback`` rationale directly above --
+            # confluence zones/classes are the SAME separate research computation (never stamped
+            # with, or compared across, a ``config_fingerprint`` anywhere), so two journals
+            # identical in every FINGERPRINTED threshold but configured with a different confluence
+            # band or class-threshold MUST share a fingerprint. Pinned by a fingerprint-stability
+            # test + the real-threshold counter-test in ``tests/test_levels.py``.
+            "sr_confluence_band_bps",
+            "sr_confluence_class_a_min_timeframes",
+            "sr_confluence_class_b_min_timeframes",
             "journal_list_default_limit",
             "journal_list_max_limit",
             "analytics_min_sample_size",
diff --git a/apps/backend/app/mcp/__init__.py b/apps/backend/app/mcp/__init__.py
index 5371550..c20a50a 100644
--- a/apps/backend/app/mcp/__init__.py
+++ b/apps/backend/app/mcp/__init__.py
@@ -190,8 +190,10 @@ TOOLS: tuple[types.Tool, ...] = (
         name="levels",
         description=(
             "Read-only proxy of GET /research/levels — deterministic, lookahead-free "
-            "support/resistance levels (price, timeframe, type, touch_count, strength) for one "
-            "symbol as of one UTC instant, computed from the recorded bar store, JSON verbatim."
+            "support/resistance levels (price, timeframe, type, touch_count, strength) PLUS their "
+            "confluence zones (member levels, timeframe-weighted score, honest A/B/C conviction "
+            "class) for one symbol as of one UTC instant, computed from the recorded bar store, "
+            "JSON verbatim."
         ),
         inputSchema=_object_schema(
             {
diff --git a/apps/backend/app/research/levels.py b/apps/backend/app/research/levels.py
index b7fc365..fe612a1 100644
--- a/apps/backend/app/research/levels.py
+++ b/apps/backend/app/research/levels.py
@@ -1,12 +1,13 @@
-"""Deterministic, lookahead-free support/resistance level detection (era-4 capability 2, J-02) --
-Data Contract row 39's LEVELS half (confluence classes are J-03; out of scope here).
+"""Deterministic, lookahead-free support/resistance level detection AND confluence-zone
+classification (era-4 capabilities 2 + 3, J-02 + J-03) -- Data Contract row 39's COMPLETE owner
+(levels AND their A/B/C confluence classes).
 
-THIS MODULE is the sole computer of support/resistance levels. It reads bars ONLY through the
-EXISTING ``BarStore`` (era-4 J-01, ``research/bars.py``) -- it owns no persistence and makes no
-network/vendor call (vendor-neutral by construction: it touches only stored ``RawBar`` rows, never
-a vendor SDK or vendor-specific field). ``GET /research/levels`` and the read-only MCP ``levels``
-tool both serve this module's output VERBATIM (single source of truth -- no second computation
-path).
+THIS MODULE is the sole computer of support/resistance levels and their confluence zones. It reads
+bars ONLY through the EXISTING ``BarStore`` (era-4 J-01, ``research/bars.py``) -- it owns no
+persistence and makes no network/vendor call (vendor-neutral by construction: it touches only
+stored ``RawBar`` rows, never a vendor SDK or vendor-specific field). ``GET /research/levels`` and
+the read-only MCP ``levels`` tool both serve this module's output VERBATIM (single source of truth
+-- no second computation path).
 
 Two DETERMINISTIC, config-owned detection methods, applied per stored bar series:
 
@@ -41,6 +42,24 @@ additive boolean flag -- the ``insufficient_sample`` / ``integrity_errors`` prec
 fabricated placeholder); a symbol WITH series but no derivable levels at the requested ``as_of``
 surfaces an empty ``levels`` list with that flag ``false`` -- an explicit "no levels found",
 never a bare, ambiguous empty array.
+
+**Confluence zones + A/B/C conviction classes (J-03).** ``compute_confluence_zones`` is a PURE
+function of the ``levels`` list above -- it touches no store/bar of its own, so it inherits the
+as-of lookahead-free truncation for free (no second truncation surface to get wrong). Levels
+pooled across EVERY timeframe are clustered by price proximity (``Config.sr_confluence_band_bps``,
+an anchor-fixed scan -- ``_cluster_levels``); only clusters with >= 2 members are "qualifying" and
+become a zone (a lone level has no confluence partner -- never a fabricated one-member "zone").
+Each zone carries its member levels (each already stamped with its own ``timeframe``), a
+timeframe-weighted ``score`` (the sum of member ``strength`` values -- each already folds in its
+OWN timeframe's weight, so the score is never double-weighted), and an honest ``class`` (A/B/C)
+graded purely by DISTINCT-TIMEFRAME breadth (``_grade_zone`` -- goal.md's "levels that align
+across timeframes matter more"), never by score: class A needs a config-owned minimum of distinct
+timeframes AND at least one long-term member (``PRIOR_PERIOD_TIMEFRAMES``, reused verbatim); class
+B needs only the (lower) distinct-timeframe floor; a qualifying cluster whose members share ONE
+timeframe grades C -- a real, honestly-reported zone of the lowest conviction, never suppressed.
+A symbol with levels but no qualifying cluster returns an explicit empty ``confluence_zones`` list
+(``no_bar_series_for_symbol`` is unaffected either way -- a SEPARATE, pre-existing honest flag).
+Zones are sorted by an explicit total order (``_zone_sort_key``) for byte-identical served JSON.
 """
 
 from __future__ import annotations
@@ -163,25 +182,130 @@ def _select_one_series_per_timeframe(records: list[dict]) -> dict[str, dict]:
     return by_timeframe
 
 
+# --- Confluence zones + A/B/C conviction classes (era-4 capability 3, J-03) ------------------------
+# The three honest grades a qualifying cluster (>= 2 price-clustered levels) can carry -- never a
+# fourth/fabricated grade, never assigned to a non-qualifying (< 2 member) cluster (which is simply
+# absent from the served list, per the module docstring).
+CLASS_A = "A"
+CLASS_B = "B"
+CLASS_C = "C"
+
+
+def _cluster_levels(levels: list[dict], band_bps: float) -> list[list[dict]]:
+    """Group ``levels`` (POOLED across every timeframe -- confluence is cross-timeframe by
+    definition) into confluence clusters.
+
+    An ANCHOR-FIXED scan over levels sorted ascending by price: the FIRST (lowest-priced) member of
+    a cluster fixes its tolerance window (``anchor * band_bps / 10_000``); every subsequent level
+    within that window of the ANCHOR (never the previous member) joins the SAME cluster -- so a
+    cluster's price span is bounded by ONE fixed tolerance rather than an unbounded chain of
+    near-neighbours (the classic chaining defect a naive pairwise-consecutive-gap scan would admit).
+
+    Only clusters with >= 2 members are returned -- a lone level has no confluence partner and is
+    silently dropped from the result (never a fabricated one-member "zone"; the module docstring's
+    "no qualifying cluster" honest-empty state)."""
+    ordered = sorted(levels, key=lambda lvl: (lvl["price"], lvl["timeframe"], lvl["type"]))
+    clusters: list[list[dict]] = []
+    current: list[dict] = []
+    anchor = 0.0
+    tolerance = 0.0
+    for level in ordered:
+        if current and abs(level["price"] - anchor) <= tolerance:
+            current.append(level)
+            continue
+        if len(current) >= 2:
+            clusters.append(current)
+        anchor = level["price"]
+        tolerance = anchor * (band_bps / 10_000.0)
+        current = [level]
+    if len(current) >= 2:
+        clusters.append(current)
+    return clusters
+
+
+def _grade_zone(members: list[dict], config: Config) -> str:
+    """A/B/C by DISTINCT-TIMEFRAME breadth alone (goal.md: "levels that align across timeframes
+    matter more") -- NEVER by score, so the class always answers "how many independent timeframes
+    agree here", while the score (``_confluence_zone``) stays a separate, additive number.
+
+    Class A needs BOTH a config-owned minimum distinct-timeframe count AND at least one long-term
+    member (the existing ``PRIOR_PERIOD_TIMEFRAMES`` bucket, reused verbatim -- no second "long-term"
+    list). Class B needs only the (lower) distinct-timeframe floor. Anything else -- structurally,
+    every member sharing exactly ONE timeframe -- grades C: a real, honestly-reported zone of the
+    lowest conviction (same-timeframe price proximity, which each level's own ``touch_count``
+    already captures), never suppressed and never upgraded."""
+    distinct_timeframes = {member["timeframe"] for member in members}
+    has_long_term = any(tf in PRIOR_PERIOD_TIMEFRAMES for tf in distinct_timeframes)
+    if len(distinct_timeframes) >= config.sr_confluence_class_a_min_timeframes and has_long_term:
+        return CLASS_A
+    if len(distinct_timeframes) >= config.sr_confluence_class_b_min_timeframes:
+        return CLASS_B
+    return CLASS_C
+
+
+def _confluence_zone(members: list[dict], config: Config) -> dict:
+    """One served zone: its members (sorted by the SAME total order ``_cluster_levels`` scans in),
+    its timeframe-weighted ``score`` (the sum of member ``strength`` values -- each already folds in
+    its own timeframe's weight via ``_level``, so this is never double-weighted), and its honest
+    ``class``."""
+    ordered_members = sorted(members, key=lambda lvl: (lvl["price"], lvl["timeframe"], lvl["type"]))
+    return {
+        "levels": ordered_members,
+        "score": sum(member["strength"] for member in ordered_members),
+        "class": _grade_zone(ordered_members, config),
+    }
+
+
+def _zone_sort_key(zone: dict) -> tuple:
+    """A total order over zones (lowest member price, then member count) so served JSON is never
+    perturbed by scan-order happenstance -- pairs with ``_sort_key``'s total order over levels."""
+    return (zone["levels"][0]["price"], len(zone["levels"]))
+
+
+def compute_confluence_zones(levels: list[dict], config: Config) -> list[dict]:
+    """The canonical confluence-zone computation (era-4 capability 3, J-03): a PURE function of the
+    ALREADY lookahead-free ``levels`` list ``compute_levels`` produces below -- no bar/store access
+    of its own, so it inherits the as-of truncation for free (no second truncation surface to get
+    wrong; the identical inputs always yield identical zones). Clusters ``levels`` (pooled across
+    every timeframe) within ``config.sr_confluence_band_bps``; each qualifying cluster becomes a
+    zone (member levels, timeframe-weighted score, honest A/B/C class). Sorted by an explicit total
+    order (``_zone_sort_key``) for byte-identical served JSON."""
+    clusters = _cluster_levels(levels, band_bps=config.sr_confluence_band_bps)
+    zones = [_confluence_zone(members, config) for members in clusters]
+    zones.sort(key=_zone_sort_key)
+    return zones
+
+
 def compute_levels(store: BarStore, symbol: str, as_of_epoch: float, config: Config) -> dict:
     """The canonical ``GET /research/levels`` + MCP ``levels`` computation (single source of
     truth) -- every level for ``symbol`` derived from its stored bar series, as of
     ``as_of_epoch`` (a UTC epoch-seconds instant; the ROUTE parses the ISO string once, never
     here, so this function itself carries no lookahead-leaking default).
 
-    Returns ``{"levels": [...], "no_bar_series_for_symbol": bool}`` -- an explicit, ADDITIVE
-    honesty flag (the ``insufficient_sample`` precedent) rather than an ambiguous bare empty
-    ``levels`` list: the flag is ``True`` only when NO stored, healthy series exists for
-    ``symbol`` at all; a symbol WITH series but nothing derivable at this ``as_of`` reports
-    ``False`` with an empty ``levels`` list -- an honest "no levels found", never fabricated.
+    Returns ``{"levels": [...], "no_bar_series_for_symbol": bool, "confluence_zones": [...]}`` --
+    ``no_bar_series_for_symbol`` is an explicit, ADDITIVE honesty flag (the ``insufficient_sample``
+    precedent) rather than an ambiguous bare empty ``levels`` list: the flag is ``True`` only when
+    NO stored, healthy series exists for ``symbol`` at all; a symbol WITH series but nothing
+    derivable at this ``as_of`` reports ``False`` with an empty ``levels`` list -- an honest "no
+    levels found", never fabricated. ``confluence_zones`` (J-03, additive beside the two J-02 keys)
+    is ``compute_confluence_zones``' output over the SAME ``levels`` list -- always ``[]`` when
+    ``levels`` is empty (whichever honest reason), never fabricated.
 
     A stored series whose timeframe is outside ``config.sr_timeframe_weights`` (impossible today
     -- that set covers every ``bar_timeframes`` entry, pinned by a dedicated config test) would
-    raise ``KeyError`` rather than silently skip or fabricate a weight."""
+    raise ``KeyError`` rather than silently skip or fabricate a weight.
+
+    Note on the corrupt-sole-series seam (iter-2 finding B1, revisited for J-03): this function
+    reads only ``store.list()``'s HEALTHY ``records`` half (the same as J-02) -- a symbol whose
+    ONLY bar series is corrupted therefore still aliases to ``no_bar_series_for_symbol: true`` with
+    an empty ``confluence_zones`` list, exactly as it aliased before confluence existed. J-03
+    introduces no new fabricated or aliased state here: the distinct corrupt-series honest state
+    remains owned by ``GET /research/bars`` (a deliberate, unchanged decision -- see the dev
+    handoff)."""
     records, _integrity_errors = store.list()
     matching = [r for r in records if r["symbol"] == symbol]
     if not matching:
-        return {"levels": [], "no_bar_series_for_symbol": True}
+        return {"levels": [], "no_bar_series_for_symbol": True, "confluence_zones": []}
 
     levels: list[dict] = []
     for timeframe, record in _select_one_series_per_timeframe(matching).items():
@@ -193,4 +317,8 @@ def compute_levels(store: BarStore, symbol: str, as_of_epoch: float, config: Con
                 _prior_period_extremes(bars, timeframe, config.sr_touch_tolerance_bps, weight, as_of_epoch)
             )
     levels.sort(key=_sort_key)
-    return {"levels": levels, "no_bar_series_for_symbol": False}
+    return {
+        "levels": levels,
+        "no_bar_series_for_symbol": False,
+        "confluence_zones": compute_confluence_zones(levels, config),
+    }
diff --git a/apps/backend/app/research/routes.py b/apps/backend/app/research/routes.py
index 5b7b297..e152364 100644
--- a/apps/backend/app/research/routes.py
+++ b/apps/backend/app/research/routes.py
@@ -1624,24 +1624,26 @@ def get_bar_series(bar_series_id: str, store: BarStore = Depends(get_bar_store))
     return {"bar_series": meta}
 
 
-# --- Deterministic support/resistance levels (era-4 capability 2, J-02) -----------------------------
+# --- Deterministic support/resistance levels + confluence zones (era-4 capabilities 2 + 3, J-02 +
+# J-03) -------------------------------------------------------------------------------------------
 # ONE route: GET /research/levels?symbol=<S>&as_of=<ISO-T>. The S/R module (research/levels.py) is
-# the sole computer of levels; this route only parses/validates the query params and serves the
-# module's output VERBATIM (single source of truth -- the MCP `levels` tool proxies this
-# byte-identically; no second computation path). ``classes`` (J-03 confluence) is deliberately
-# ABSENT this iteration -- an additive-only field a later iteration can add without a breaking
-# change (the plan's explicit reserved-shape note).
+# the sole computer of levels AND their confluence zones/A-B-C classes; this route only
+# parses/validates the query params and serves the module's output VERBATIM (single source of
+# truth -- the MCP `levels` tool proxies this byte-identically; no second computation path).
+# `confluence_zones` (J-03) is now an additive field beside `levels` / `no_bar_series_for_symbol` --
+# no route-body change was needed since the route already spreads `compute_levels`'s dict verbatim.
 
 
 @router.get("/levels")
 def get_levels(symbol: str, as_of: str, store: BarStore = Depends(get_bar_store)) -> dict:
-    """Deterministic, lookahead-free support/resistance levels for ``symbol`` as of ``as_of``
-    (J-02). ``symbol``/``as_of`` are both REQUIRED query params (FastAPI 422s a missing one
-    before this body runs); an empty ``symbol`` or a malformed ``as_of`` are explicit 422s here
-    (never a silent "now" default, which would leak lookahead). A symbol with no recorded bar
-    series at all, and a symbol with series but nothing derivable at this instant, are TWO
-    distinct honest states -- see ``compute_levels``' ``no_bar_series_for_symbol`` flag -- never
-    one ambiguous bare empty ``levels`` array."""
+    """Deterministic, lookahead-free support/resistance levels, PLUS their confluence zones and
+    A/B/C conviction classes (J-02 + J-03), for ``symbol`` as of ``as_of``. ``symbol``/``as_of``
+    are both REQUIRED query params (FastAPI 422s a missing one before this body runs); an empty
+    ``symbol`` or a malformed ``as_of`` are explicit 422s here (never a silent "now" default,
+    which would leak lookahead). A symbol with no recorded bar series at all, and a symbol with
+    series but nothing derivable at this instant, are TWO distinct honest states -- see
+    ``compute_levels``' ``no_bar_series_for_symbol`` flag -- never one ambiguous bare empty
+    ``levels`` array; ``confluence_zones`` is ``[]`` in both cases (never fabricated)."""
     if not symbol:
         raise HTTPException(status_code=422, detail="a levels query requires a symbol")
     try:
diff --git a/apps/backend/tests/test_levels.py b/apps/backend/tests/test_levels.py
index 9023b92..91120d3 100644
--- a/apps/backend/tests/test_levels.py
+++ b/apps/backend/tests/test_levels.py
@@ -27,9 +27,13 @@ from app.config import CONFIG, Config
 from app.providers.adapters.base import RawBar
 from app.research.bars import BarStore
 from app.research.levels import (
+    CLASS_A,
+    CLASS_B,
+    CLASS_C,
     PRIOR_PERIOD_EXTREME,
     PRIOR_PERIOD_TIMEFRAMES,
     SWING_PIVOT,
+    compute_confluence_zones,
     compute_levels,
 )
 
@@ -47,6 +51,15 @@ def _bar(symbol: str, timeframe: str, day_index: int, high: float, low: float, c
     return RawBar(symbol, timeframe, _BASE + day_index * _DAY, close, high, low, close, 1_000)
 
 
+def _lvl(price: float, timeframe: str, strength: float, level_type: str = SWING_PIVOT, touch_count: int = 1) -> dict:
+    """A hand-built level dict -- the exact shape ``research/levels.py``'s own ``_level()``
+    produces -- for testing ``compute_confluence_zones`` DIRECTLY as a pure function, independent
+    of any bar/store machinery (clustering/scoring/grading depend only on ``price``, ``timeframe``,
+    and ``strength``; ``type``/``touch_count`` are carried through unchanged and rarely matter
+    here)."""
+    return {"price": price, "timeframe": timeframe, "type": level_type, "touch_count": touch_count, "strength": strength}
+
+
 # --- Synthetic swing-pivot fixture: 6 "4h" bars (NOT a prior-period timeframe, so ONLY swing
 # pivots are computed -- isolates the pivot/touch/strength mechanism from prior-period extremes).
 _SWING_SYMBOL = "SYN-SWING"
@@ -192,6 +205,93 @@ def test_prior_period_extreme_does_not_apply_to_a_non_prior_period_timeframe(tmp
     assert all(lvl["type"] == SWING_PIVOT for lvl in result["levels"])
 
 
+# --- Confluence zones + A/B/C classes: the pure `compute_confluence_zones` function ----------------
+# Direct unit tests -- hand-built level dicts, no bar/store machinery -- isolate the
+# clustering/scoring/grading algorithm itself from the bar-derived integration proofs further below.
+
+
+def test_confluence_clustering_joins_within_band_across_timeframes_and_grades_class_a():
+    levels = [
+        _lvl(100.00, "1h", strength=2.0),
+        _lvl(100.05, "1d", strength=4.0),
+        _lvl(100.10, "1w", strength=5.0),
+        _lvl(500.00, "1h", strength=2.0),  # isolated -- no partner within band, joins no zone
+    ]
+    zones = compute_confluence_zones(levels, CONFIG)
+    assert len(zones) == 1
+    zone = zones[0]
+    assert [m["price"] for m in zone["levels"]] == [100.00, 100.05, 100.10]
+    assert {m["timeframe"] for m in zone["levels"]} == {"1h", "1d", "1w"}
+    assert zone["score"] == 11.0  # 2.0 + 4.0 + 5.0, timeframe-weighted sum of member strengths
+    assert zone["class"] == CLASS_A
+
+
+def test_confluence_class_a_requires_a_long_term_member_not_just_timeframe_count():
+    """Three DISTINCT timeframes clustering -- but NONE in the long-term bucket -- must grade B,
+    not A: the long-term-member condition is enforced INDEPENDENTLY of the distinct-timeframe
+    count (goal.md's "a required long-term member", not merely "several timeframes")."""
+    assert not (set(("1h", "4h", "8h")) & set(PRIOR_PERIOD_TIMEFRAMES)), "the setup's own premise"
+    levels = [
+        _lvl(50.00, "1h", strength=2.0),
+        _lvl(50.02, "4h", strength=3.0),
+        _lvl(50.04, "8h", strength=3.0),
+    ]
+    zones = compute_confluence_zones(levels, CONFIG)
+    assert len(zones) == 1
+    assert len({m["timeframe"] for m in zones[0]["levels"]}) == 3  # meets the COUNT floor...
+    assert zones[0]["class"] == CLASS_B  # ...but never A without a long-term member
+
+
+def test_confluence_class_b_two_distinct_timeframes_below_the_class_a_floor():
+    levels = [_lvl(75.00, "1h", strength=2.0), _lvl(75.03, "1d", strength=4.0)]
+    zones = compute_confluence_zones(levels, CONFIG)
+    assert len(zones) == 1
+    assert zones[0]["score"] == 6.0
+    assert zones[0]["class"] == CLASS_B
+
+
+def test_confluence_class_c_same_timeframe_cluster_below_the_class_b_floor():
+    levels = [_lvl(60.00, "1h", strength=2.0), _lvl(60.02, "1h", strength=2.0)]
+    zones = compute_confluence_zones(levels, CONFIG)
+    assert len(zones) == 1
+    assert zones[0]["score"] == 4.0
+    assert zones[0]["class"] == CLASS_C
+
+
+def test_confluence_clustering_is_anchor_fixed_not_chained_to_the_previous_member():
+    """A -> B is within band of the cluster's ANCHOR (A, the first/lowest member); B -> C is
+    within band of B but C is NOT within band of the anchor -- proves the scan re-checks every
+    candidate against the cluster's FIXED anchor, never against the most-recently-added member (a
+    naive chained scan would incorrectly admit C too, letting the cluster's price span drift
+    unbounded)."""
+    band_bps = CONFIG.sr_confluence_band_bps
+    a, b, c = 100.00, 100.15, 100.30
+    tol = a * band_bps / 10_000.0
+    assert abs(b - a) <= tol and abs(c - b) <= tol and abs(c - a) > tol, "the setup's own premise"
+    levels = [_lvl(a, "1h", strength=2.0), _lvl(b, "1d", strength=4.0), _lvl(c, "1w", strength=5.0)]
+    zones = compute_confluence_zones(levels, CONFIG)
+    assert len(zones) == 1  # {a, b} cluster; c is dropped as an isolated singleton
+    assert [m["price"] for m in zones[0]["levels"]] == [a, b]
+
+
+def test_confluence_singleton_level_produces_no_zone():
+    levels = [_lvl(10.0, "1h", strength=2.0), _lvl(900.0, "1d", strength=4.0)]
+    assert compute_confluence_zones(levels, CONFIG) == []
+
+
+def test_confluence_zones_sorted_by_explicit_total_order_ascending_by_lowest_member_price():
+    levels = [
+        _lvl(500.00, "1h", strength=2.0), _lvl(500.02, "1d", strength=4.0),
+        _lvl(100.00, "1h", strength=2.0), _lvl(100.01, "1d", strength=4.0),
+    ]
+    zones = compute_confluence_zones(levels, CONFIG)
+    assert [z["levels"][0]["price"] for z in zones] == [100.00, 500.00]
+
+
+def test_confluence_zones_empty_for_empty_levels():
+    assert compute_confluence_zones([], CONFIG) == []
+
+
 # --- Lookahead-free: the headline correctness property ---------------------------------------------
 
 
@@ -199,7 +299,11 @@ def test_lookahead_free_a_level_at_t_is_unchanged_by_any_bar_after_t():
     """The definitive proof: a store holding ONLY bars timestamped <= T produces the IDENTICAL
     result to a store holding the FULL committed fixture (including bars after T), both queried at
     the SAME as-of T. Uses the real committed PG 1h fixture, truncated at bar index 6 (2026-06-09
-    19:00Z) -- squarely inside the window, well before the last bar."""
+    19:00Z) -- squarely inside the window, well before the last bar. The full-dict
+    ``json.dumps(...) == json.dumps(...)`` comparison below covers ``confluence_zones``/``class``
+    too (J-03) -- extended below with an EXPLICIT non-vacuous zone assertion, since
+    ``compute_confluence_zones`` is a pure function of this SAME (already lookahead-free) `levels`
+    list and introduces no second truncation surface of its own."""
     full_store = BarStore(FIXTURE_BAR_DIR)
     as_of = _epoch("2026-06-09T19:00:00Z")  # bar index 6's own ts
     full_result = compute_levels(full_store, "PG", as_of, CONFIG)
@@ -230,6 +334,16 @@ def test_lookahead_free_a_level_at_t_is_unchanged_by_any_bar_after_t():
     assert json.dumps(truncated_result, sort_keys=True) == json.dumps(full_result, sort_keys=True)
     assert len(full_result["levels"]) >= 1, "the proof must exercise at least one real level"
 
+    # J-03 extension: at this EARLIER as_of the cross-timeframe zone has only TWO members --
+    # 148.095 (the 1h swing confirmed only once bar index 7 becomes visible) is NOT yet part of it
+    # -- proving idx6's not-yet-visible neighbour never leaked into the zone or its class either.
+    zones = full_result["confluence_zones"]
+    assert len(zones) == 6, "the proof must exercise a real, non-trivial set of zones"
+    cross_tf_zone = zones[-1]
+    assert [m["price"] for m in cross_tf_zone["levels"]] == [148.06, 148.23]
+    assert cross_tf_zone["score"] == 8.0
+    assert cross_tf_zone["class"] == CLASS_B
+
 
 # --- Byte-identical determinism ---------------------------------------------------------------------
 
@@ -240,6 +354,7 @@ def test_byte_identical_determinism_across_independent_runs():
     first = compute_levels(store, "PG", as_of, CONFIG)
     second = compute_levels(BarStore(FIXTURE_BAR_DIR), "PG", as_of, CONFIG)  # a FRESH store object
     assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
+    assert len(first["confluence_zones"]) >= 1, "the proof must exercise at least one real zone"
 
 
 # --- The committed PG fixture: exact real-data acceptance values -----------------------------------
@@ -304,6 +419,134 @@ def test_committed_fixture_prior_period_extremes_exact_values_keyless():
     assert len(result["levels"]) == 20  # 15 prior-period + 1 daily swing + 4 hourly swing
 
 
+def test_committed_fixture_confluence_zones_exact_values_keyless():
+    """The real PG fixture (era-4 J-01) stores only TWO timeframes (1h, 1d) -- confirmed by direct
+    computation, not hand-derived: it produces SIX confluence zones, FIVE same-timeframe (1d-only)
+    C-grade zones and exactly ONE genuine cross-timeframe (1h+1d) B-grade zone -- and, honestly,
+    NEVER a class A zone (which needs a THIRD distinct timeframe the committed fixture does not
+    have; class A is instead proven reachable on the synthetic 3-timeframe fixture below)."""
+    store = BarStore(FIXTURE_BAR_DIR)
+    as_of = _epoch("2026-06-09T21:00:00Z")
+    result = compute_levels(store, "PG", as_of, CONFIG)
+    zones = result["confluence_zones"]
+
+    assert [z["class"] for z in zones] == [CLASS_C, CLASS_C, CLASS_C, CLASS_C, CLASS_C, CLASS_B]
+    assert CLASS_A not in {z["class"] for z in zones}, "unreachable on this 2-timeframe fixture"
+
+    def _prices(zone: dict) -> list[float]:
+        return [m["price"] for m in zone["levels"]]
+
+    assert _prices(zones[0]) == [138.86, 139.03] and zones[0]["score"] == 8.0
+    assert _prices(zones[1]) == [139.89, 139.89, 140.0] and zones[1]["score"] == 12.0
+    assert _prices(zones[2]) == [140.19, 140.28] and zones[2]["score"] == 8.0
+    assert _prices(zones[3]) == [140.78, 140.82] and zones[3]["score"] == 8.0
+    assert _prices(zones[4]) == [141.8, 141.82] and zones[4]["score"] == 16.0
+
+    cross_tf_zone = zones[5]
+    assert _prices(cross_tf_zone) == [148.06, 148.095, 148.23]
+    assert {m["timeframe"] for m in cross_tf_zone["levels"]} == {"1h", "1d"}
+    assert cross_tf_zone["score"] == 12.0
+
+
+# --- Confluence zones through `compute_levels`: a real bar-derived class A (the plan's own "Known
+# Consideration" -- the committed PG fixture stores only TWO timeframes and can never itself
+# produce a class A zone, so a synthetic THREE-timeframe fixture proves class A IS reachable
+# through the real, bar-driven `compute_levels` path, not merely the pure-function unit tests above)
+# ------------------------------------------------------------------------------------------------
+
+_CONFLUENCE_SYMBOL = "SYN-CONFLUENCE"
+
+
+def _confluence_fixture(store: BarStore) -> None:
+    """A three-timeframe (1h/1d/1w) synthetic fixture engineered for an exact A/B/C case. Every
+    "noise" extreme (each bar's OTHER high/low, engineered far outside any band) sits isolated --
+    verified by direct computation, not hand-derived:
+
+      * ~100.00 (1h swing-high) + ~100.05 (1d prior-period close) + ~100.10 (1w prior-period close)
+        -- THREE distinct timeframes including two long-term ones -- class A.
+      * ~200.00 (1h swing-high) + ~200.08 (1d prior-period close) -- TWO distinct timeframes --
+        class B.
+      * ~300.00 + ~300.05 (both 1h swing-highs) -- ONE distinct timeframe -- class C.
+      * ~500.00 (1h swing-high), isolated -- no confluence partner -- appears in NO zone.
+    """
+    hourly_specs = [
+        (50, 40, 45), (100.00, 41, 98), (55, 42, 50), (200.00, 43, 198), (57, 44, 52),
+        (300.00, 45, 298), (58, 46, 53), (300.05, 47, 297), (59, 48, 54), (500.00, 49, 498),
+        (60, 50, 55),
+    ]
+    hourly_bars = [
+        RawBar(_CONFLUENCE_SYMBOL, "1h", _BASE + i * 3600.0, close, high, low, close, 1_000)
+        for i, (high, low, close) in enumerate(hourly_specs)
+    ]
+    daily_bars = [
+        RawBar(_CONFLUENCE_SYMBOL, "1d", _BASE + 0 * _DAY, 100.05, 900, 10, 100.05, 1_000),
+        RawBar(_CONFLUENCE_SYMBOL, "1d", _BASE + 1 * _DAY, 200.08, 910, 20, 200.08, 1_000),
+    ]
+    weekly_bars = [
+        RawBar(_CONFLUENCE_SYMBOL, "1w", _BASE + 0 * _DAY, 100.10, 920, 30, 100.10, 1_000),
+    ]
+    store.record(
+        symbol=_CONFLUENCE_SYMBOL, timeframe="1h",
+        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-01-01T11:00:00Z",
+        feed="sip", bars=hourly_bars,
+    )
+    store.record(
+        symbol=_CONFLUENCE_SYMBOL, timeframe="1d",
+        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-01-03T00:00:00Z",
+        feed="sip", bars=daily_bars,
+    )
+    store.record(
+        symbol=_CONFLUENCE_SYMBOL, timeframe="1w",
+        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-01-08T00:00:00Z",
+        feed="sip", bars=weekly_bars,
+    )
+
+
+def test_synthetic_three_timeframe_fixture_produces_exact_a_b_c_zones_through_compute_levels(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    _confluence_fixture(store)
+    as_of = _BASE + 8 * _DAY  # comfortably past every period's closure (1w's 604800s is longest)
+    result = compute_levels(store, _CONFLUENCE_SYMBOL, as_of, CONFIG)
+    assert result["no_bar_series_for_symbol"] is False
+    zones = result["confluence_zones"]
+    assert len(zones) == 3
+
+    zone_a, zone_b, zone_c = zones
+    assert [m["price"] for m in zone_a["levels"]] == [100.00, 100.05, 100.10]
+    assert {m["timeframe"] for m in zone_a["levels"]} == {"1h", "1d", "1w"}
+    assert zone_a["score"] == 11.0  # 2.0 (1h) + 4.0 (1d) + 5.0 (1w)
+    assert zone_a["class"] == CLASS_A
+
+    assert [m["price"] for m in zone_b["levels"]] == [200.00, 200.08]
+    assert {m["timeframe"] for m in zone_b["levels"]} == {"1h", "1d"}
+    assert zone_b["score"] == 6.0  # 2.0 (1h) + 4.0 (1d)
+    assert zone_b["class"] == CLASS_B
+
+    assert [m["price"] for m in zone_c["levels"]] == [300.00, 300.05]
+    assert {m["timeframe"] for m in zone_c["levels"]} == {"1h"}
+    assert zone_c["score"] == 8.0  # 4.0 + 4.0 (both touch_count 2 -- see the 130.0/130.03 precedent)
+    assert zone_c["class"] == CLASS_C
+
+    # The isolated 500.00 swing-high and every engineered noise extreme appear in NO zone.
+    all_zone_prices = {m["price"] for z in zones for m in z["levels"]}
+    assert 500.00 not in all_zone_prices
+    assert all(price not in all_zone_prices for price in (900, 10, 910, 20, 920, 30))
+
+
+def test_no_qualifying_cluster_on_bar_derived_levels_is_an_honest_empty_zones_list(tmp_path):
+    """The EXISTING J-02 swing fixture, unmodified: its four pivots (100.0/102.0/115.0/130.0) are
+    all far apart in price (the closest gap is 200+ bps, well outside the confluence band) -- an
+    honest empty ``confluence_zones`` list, never fabricated, and distinct from
+    ``no_bar_series_for_symbol`` (which stays False: the symbol DOES have levels, just no
+    qualifying cluster among them)."""
+    store = BarStore(tmp_path / "bars")
+    _swing_fixture(store)
+    result = compute_levels(store, _SWING_SYMBOL, _BASE + 5 * _DAY, CONFIG)
+    assert result["no_bar_series_for_symbol"] is False
+    assert len(result["levels"]) == 4
+    assert result["confluence_zones"] == []
+
+
 # --- Honest, distinct failure states (never one bare ambiguous empty array) ------------------------
 
 
@@ -311,20 +554,20 @@ def test_symbol_with_no_recorded_bar_series_is_a_distinct_honest_state(tmp_path)
     store = BarStore(tmp_path / "bars")
     _swing_fixture(store)  # records ONLY `_SWING_SYMBOL` -- never the queried symbol below
     result = compute_levels(store, "NEVER-RECORDED", _BASE + 100 * _DAY, CONFIG)
-    assert result == {"levels": [], "no_bar_series_for_symbol": True}
+    assert result == {"levels": [], "no_bar_series_for_symbol": True, "confluence_zones": []}
 
 
 def test_symbol_with_bar_series_but_nothing_derivable_yet_is_a_distinct_honest_state(tmp_path):
     store = BarStore(tmp_path / "bars")
     _swing_fixture(store)
     result = compute_levels(store, _SWING_SYMBOL, _BASE - 1, CONFIG)  # before the series even starts
-    assert result == {"levels": [], "no_bar_series_for_symbol": False}
+    assert result == {"levels": [], "no_bar_series_for_symbol": False, "confluence_zones": []}
 
 
 def test_empty_bar_store_is_no_bar_series_for_symbol(tmp_path):
     store = BarStore(tmp_path / "bars")  # never recorded anything at all
     result = compute_levels(store, "PG", _BASE, CONFIG)
-    assert result == {"levels": [], "no_bar_series_for_symbol": True}
+    assert result == {"levels": [], "no_bar_series_for_symbol": True, "confluence_zones": []}
 
 
 # --- Multiple series for the same (symbol, timeframe): most-recently-created wins ------------------
@@ -375,6 +618,12 @@ def test_sr_parameters_are_config_sourced_no_magic_numbers():
     assert isinstance(CONFIG.sr_touch_tolerance_bps, float) and CONFIG.sr_touch_tolerance_bps > 0
     assert isinstance(CONFIG.sr_timeframe_weights, dict) and CONFIG.sr_timeframe_weights
     assert set(CONFIG.sr_timeframe_weights) == set(CONFIG.bar_timeframes)
+    assert isinstance(CONFIG.sr_confluence_band_bps, float) and CONFIG.sr_confluence_band_bps > 0
+    assert isinstance(CONFIG.sr_confluence_class_a_min_timeframes, int)
+    assert isinstance(CONFIG.sr_confluence_class_b_min_timeframes, int)
+    assert CONFIG.sr_confluence_class_b_min_timeframes >= 2  # "distinct timeframes" needs >= 2
+    # A is the strictly higher bar -- its floor can never be laxer than B's.
+    assert CONFIG.sr_confluence_class_a_min_timeframes >= CONFIG.sr_confluence_class_b_min_timeframes
 
     import inspect
 
@@ -384,6 +633,9 @@ def test_sr_parameters_are_config_sourced_no_magic_numbers():
     assert "config.sr_pivot_lookback" in src
     assert "config.sr_touch_tolerance_bps" in src
     assert "config.sr_timeframe_weights" in src
+    assert "config.sr_confluence_band_bps" in src
+    assert "config.sr_confluence_class_a_min_timeframes" in src
+    assert "config.sr_confluence_class_b_min_timeframes" in src
 
 
 # --- config_fingerprint: sr_* fields excluded, default pinned unmoved -------------------------------
@@ -396,5 +648,14 @@ def test_sr_config_fields_are_excluded_from_config_fingerprint():
     assert (
         Config(sr_timeframe_weights={"1d": 99.0}).config_fingerprint() == CONFIG.config_fingerprint()
     )
+    assert Config(sr_confluence_band_bps=999.0).config_fingerprint() == CONFIG.config_fingerprint()
+    assert (
+        Config(sr_confluence_class_a_min_timeframes=9).config_fingerprint()
+        == CONFIG.config_fingerprint()
+    )
+    assert (
+        Config(sr_confluence_class_b_min_timeframes=9).config_fingerprint()
+        == CONFIG.config_fingerprint()
+    )
     # ...while a real classifier threshold still moves it (the counter-test).
     assert Config(min_trade_speed=0.51).config_fingerprint() != CONFIG.config_fingerprint()
diff --git a/apps/backend/tests/test_levels_api.py b/apps/backend/tests/test_levels_api.py
index 5f72225..9d035bb 100644
--- a/apps/backend/tests/test_levels_api.py
+++ b/apps/backend/tests/test_levels_api.py
@@ -1,14 +1,19 @@
-"""The ``GET /research/levels`` endpoint (era-4 capability 2, J-02) -- route-level integration.
+"""The ``GET /research/levels`` endpoint (era-4 capabilities 2 + 3, J-02 + J-03) -- route-level
+integration.
 
 Mirrors ``test_bars_api.py``'s ``ctx`` fixture (TestClient + temp bar dir + injected
 ``FakeAdapter``): a bar series is recorded through the REAL ``POST /research/bars`` route, then
 ``GET /research/levels`` is read back and asserted against exact values -- the full request path,
-not a direct module call (``test_levels.py`` covers the pure computation in isolation).
+not a direct module call (``test_levels.py`` covers the pure level/confluence computation in
+isolation). The committed real PG bar-fixture pair is also seeded directly into the temp bar dir
+(the ``test_mcp_server.py`` technique) to prove the confluence-zones field end to end on real data.
 """
 
 from __future__ import annotations
 
+import shutil
 from datetime import datetime, timezone
+from pathlib import Path
 
 import pytest
 from fastapi.testclient import TestClient
@@ -20,6 +25,8 @@ from app.research.routes import ResearchRegistry, set_registry
 from app.research.store import JournalStore
 from fakes import FakeAdapter
 
+FIXTURE_BAR_DIR = Path(__file__).parent / "fixtures" / "bars"
+
 SYMBOL = "LVL"
 TIMEFRAME = "4h"
 _BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)
@@ -109,6 +116,40 @@ def test_get_levels_happy_path_exact_values(ctx):
     assert by_price[130.0]["touch_count"] == 2
     assert by_price[130.0]["strength"] == weight * 2
 
+    # J-03: this single-timeframe fixture's four pivots are all far apart in price (the closest
+    # gap is 200+ bps, well outside the confluence band) -- an honest empty zones list, never
+    # fabricated (the pure-computation matrix lives in test_levels.py; this proves the SAME
+    # honesty holds through the real route).
+    assert body["confluence_zones"] == []
+
+
+def test_get_levels_confluence_zones_exact_values_on_the_committed_pg_fixture(ctx):
+    """The committed real PG bar-fixture pair (era-4 J-01, 2 timeframes: 1h + 1d), seeded directly
+    into the temp bar dir, read back through the REAL route -- proving `confluence_zones` is served
+    end to end on real data, not just via a direct module call (`test_levels.py`'s
+    ``test_committed_fixture_confluence_zones_exact_values_keyless`` owns the exhaustive exact-value
+    proof; this asserts the SAME shape survives the route's serialization unchanged)."""
+    client, bar_dir = ctx
+    bar_dir.mkdir(parents=True, exist_ok=True)  # BarStore only creates it lazily inside `record()`
+    fixtures = list(FIXTURE_BAR_DIR.glob("*.json"))
+    assert fixtures, "the committed bar fixture directory must not be empty"
+    for fixture in fixtures:
+        shutil.copy(fixture, bar_dir / fixture.name)
+
+    as_of = "2026-06-09T21:00:00Z"  # at/after both fixtures' window_end_utc
+    r = client.get("/research/levels", params={"symbol": "PG", "as_of": as_of})
+    assert r.status_code == 200
+    body = r.json()
+    assert body["no_bar_series_for_symbol"] is False
+    zones = body["confluence_zones"]
+    assert len(zones) == 6
+    assert [z["class"] for z in zones] == ["C", "C", "C", "C", "C", "B"]
+
+    cross_tf_zone = zones[-1]
+    assert [m["price"] for m in cross_tf_zone["levels"]] == [148.06, 148.095, 148.23]
+    assert {m["timeframe"] for m in cross_tf_zone["levels"]} == {"1h", "1d"}
+    assert cross_tf_zone["score"] == 12.0
+
 
 def test_get_levels_lowercases_are_normalized_to_the_stored_uppercase_symbol(ctx):
     client, _bar_dir = ctx
@@ -131,6 +172,7 @@ def test_unrecorded_symbol_is_a_distinct_honest_state_not_an_ambiguous_empty_lis
     body = r.json()
     assert body["levels"] == []
     assert body["no_bar_series_for_symbol"] is True
+    assert body["confluence_zones"] == []
 
 
 def test_no_bar_series_recorded_at_all_is_the_same_distinct_state(ctx):
@@ -140,6 +182,7 @@ def test_no_bar_series_recorded_at_all_is_the_same_distinct_state(ctx):
     body = r.json()
     assert body["levels"] == []
     assert body["no_bar_series_for_symbol"] is True
+    assert body["confluence_zones"] == []
 
 
 def test_as_of_before_any_recorded_bar_is_honest_no_levels_found_not_the_prior_state(ctx):
@@ -150,6 +193,7 @@ def test_as_of_before_any_recorded_bar_is_honest_no_levels_found_not_the_prior_s
     body = r.json()
     assert body["levels"] == []
     assert body["no_bar_series_for_symbol"] is False  # distinct from the unrecorded-symbol state
+    assert body["confluence_zones"] == []
 
 
 # --- 422s: never a silent coercion, never a lookahead-leaking "now" default -------------------------
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index 9c3cfc8..e2417d9 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -288,10 +288,12 @@ async def test_bars_tool_byte_identical_on_a_non_empty_live_list(mcp_env, backen
 
 @pytest.mark.anyio
 async def test_levels_tool_byte_identical_on_a_non_empty_live_result(mcp_env, backend_paths):
-    """``levels`` (era-4 J-02) ships in the SAME iteration as its endpoint — the ``bars`` J-01
-    precedent: seed the live backend's bar directory with the committed KEYLESS fixture pair
-    directly (no vendor call, no credentials touched), then prove the two-argument tool's JSON is
-    byte-identical to its curl equivalent on a NON-EMPTY result."""
+    """``levels`` (era-4 J-02, confluence zones added at J-03) ships in the SAME iteration as its
+    endpoint — the ``bars`` J-01 precedent: seed the live backend's bar directory with the
+    committed KEYLESS fixture pair directly (no vendor call, no credentials touched), then prove
+    the two-argument tool's JSON is byte-identical to its curl equivalent on a NON-EMPTY result --
+    including the ``confluence_zones`` field (J-03), so this proxy proof meaningfully covers it too
+    (not merely a vacuous byte-match on an empty list)."""
     bar_dir = Path(backend_paths["TAPEOLOGY_BAR_DIR"])
     fixtures = list(FIXTURE_BAR_DIR.glob("*.json"))
     assert fixtures, "the committed bar fixture directory must not be empty"
@@ -302,6 +304,7 @@ async def test_levels_tool_byte_identical_on_a_non_empty_live_result(mcp_env, ba
     rest = httpx.get(f"{mcp_env}/research/levels", params={"symbol": "PG", "as_of": as_of}, timeout=5.0)
     assert rest.status_code == 200
     assert len(rest.json()["levels"]) >= 1, "the live result must be non-empty for this proof"
+    assert len(rest.json()["confluence_zones"]) >= 1, "the live zones must be non-empty for this proof"
     assert result.isError is False
     assert len(result.content) == 1
     assert result.content[0].text.encode("utf-8") == rest.content, "levels not byte-identical"
diff --git adocs/handoffs/goal-tape_to_profit_support_resistence-iter-3-audit.md bdocs/handoffs/goal-tape_to_profit_support_resistence-iter-3-audit.md
new file mode 100644
index 0000000..8f2c065
--- /dev/null
+++ bdocs/handoffs/goal-tape_to_profit_support_resistence-iter-3-audit.md
@@ -0,0 +1,155 @@
+# goal-tape_to_profit_support_resistence-iter-3 Audit Report
+
+**Date:** 2026-07-06
+**Auditor:** Hard audit pass — skeptical, evidence-based
+
+---
+
+## 1. Executive Verdict
+
+**Verdict:** PASS
+
+J-03 ships the confluence-zone + A/B/C classification half of Data-Contract Row 39 as a purely
+additive `confluence_zones` field on the existing `compute_levels` return dict — no new module,
+route, or MCP tool — and every acceptance property (deterministic anchor-fixed clustering,
+timeframe-weighted scoring, honest A/B/C grading, no-lookahead, byte-identical REST≡MCP, honest
+empty states, frozen `default`/`v1`) is genuinely implemented and independently verified against the
+running code, not just the handoff. I traced the algorithm's unhappy paths (singletons, same-price
+duplicates, corrupt-sole-series aliasing, later-bar leakage) and re-ran the full suite myself; no
+CRITICAL or IMPORTANT issue exists, so no fix was applied.
+
+---
+
+## 2. Findings
+
+### Backend Findings
+
+**B1 — OBSERVATION (observation): committed real PG fixture can never produce a class A zone**
+`apps/backend/app/config.py:1139` sets `sr_confluence_class_a_min_timeframes = 3`, but the committed
+PG fixture stores only two timeframes (1h, 1d), so class A is structurally unreachable on real
+committed data. This is honestly documented (config comment `config.py:1135-1138`, handoff "Known
+Issues") and class A reachability is instead proven end-to-end through the real bar-driven
+`compute_levels` path on a dedicated synthetic 3-timeframe fixture
+(`test_levels.py:505` `test_synthetic_three_timeframe_fixture_produces_exact_a_b_c_zones_through_compute_levels`).
+An honest data-breadth consequence, not a defect — no fix warranted.
+
+**B2 — OBSERVATION (observation): same-price levels of different `type` both count toward a zone**
+When a swing-pivot and a prior-period-extreme land on the identical price (e.g. PG zone[1] members
+`[139.89, 139.89, 140.0]`, `research/levels.py:246` `_confluence_zone`), both appear as distinct
+members and both contribute to `score` (12.0 here). This is by design — two independent detection
+methods corroborating one price — and is honestly labelled (each member carries its own distinct
+`type`), never a fabricated duplicate. Verified directly: `score == sum(member strengths)` holds for
+every zone. No fix warranted.
+
+**B3 — OBSERVATION (observation): the "2 members = cluster" minimum is a code literal, not config**
+`research/levels.py:216,221` gate a qualifying cluster on `len(current) >= 2`. Unlike the confluence
+band and the A/B/C timeframe floors (all config-owned and fingerprint-excluded), this `2` is a
+literal. It is the structural definition of "confluence" (you cannot have levels *aligning* with
+fewer than two), analogous to the deliberately-non-config `_PERIOD_SECONDS` calendar facts, not a
+tunable research threshold — so it is out of the no-magic-numbers requirement's intent. Noted only
+for completeness; no fix warranted.
+
+### Frontend Findings
+
+N/A — J-03 is a machine surface (REST + MCP). `git diff -- apps/frontend/` is empty (verified by me,
+not just claimed); browser-qa correctly SKIPPED.
+
+### Test Findings
+
+**T1 — OBSERVATION (observation): no-magic-numbers introspection is a presence-check, not an absence-check**
+`test_levels.py:616` `test_sr_parameters_are_config_sourced_no_magic_numbers` asserts each of the six
+`config.sr_*` field names appears in `levels.py`'s source, but does not grep for the *absence* of
+literal thresholds (as the test plan's TC-09 pass-criteria phrased it). I closed this gap by reading
+`levels.py` directly: the grading/clustering logic contains no hardcoded threshold — the only numeric
+literals are the structural bps denominator `10_000.0` (identical to the pre-existing `_touch_count`
+usage) and the structural cluster-minimum `2` (B3). The guard is therefore adequate in practice. No
+fix warranted.
+
+---
+
+## 3. Domain Assessment
+
+The core domain logic is correct and honest. I verified each property against the running code:
+
+- **Clustering (`_cluster_levels`, `research/levels.py:194`)** — an anchor-fixed scan over
+  price-sorted levels: the lowest member fixes the tolerance window (`anchor * band_bps / 10_000`)
+  and every candidate is re-checked against that FIXED anchor, so a cluster's span is bounded by one
+  tolerance rather than an unbounded chain. Directly tested
+  (`test_confluence_clustering_is_anchor_fixed_not_chained_to_the_previous_member`, with a premise
+  assertion), and I confirmed independently that every served zone's members sit within the band of
+  their anchor. Singletons are dropped (never a fabricated one-member zone). Because anchor prices
+  are strictly increasing across clusters, `_zone_sort_key`'s lowest-member-price element is already
+  a strict total order — byte-identical determinism holds (re-verified via a fresh-store `json.dumps`
+  equality test).
+
+- **Grading (`_grade_zone`, `research/levels.py:226`)** — by distinct-timeframe breadth alone, never
+  by score. Class A requires BOTH a config-owned distinct-timeframe floor AND a long-term member
+  (`PRIOR_PERIOD_TIMEFRAMES`, reused verbatim — no second "long-term" list); the two conditions are
+  independently enforced, proven by
+  `test_confluence_class_a_requires_a_long_term_member_not_just_timeframe_count` (a 1h+4h+8h cluster
+  meets the count but grades B). Class B needs only the distinct-timeframe floor; a same-timeframe
+  cluster grades C. Exact expected classes are asserted on the committed PG fixture
+  (`[C,C,C,C,C,B]`) and the synthetic fixture (`A,B,C`) — I reproduced both directly.
+
+- **Scoring** — `score = sum(member strength)`, and since each level's `strength` already folds in
+  its own timeframe weight, the sum is timeframe-weighted without double-weighting. Verified:
+  `score == sum(strength)` for every served zone.
+
+- **No-lookahead (the headline critical property, extended to classes)** —
+  `compute_confluence_zones` is a pure function of the already-`ts <= as_of`-truncated `levels` list
+  (`compute_levels` filters via `_bars_as_of` before any windowing), so it introduces no second
+  truncation surface. The physical-truncation test asserts the full response dict (including
+  `confluence_zones` and each `class`) is byte-identical between a store holding only bars ≤ T and
+  the full store queried at the same T, plus an explicit non-vacuous assertion that a
+  not-yet-confirmed 1h swing (148.095) is absent from the zone at the earlier as-of.
+
+- **Single source of truth / MCP read-only** — the route spreads `**result` verbatim
+  (`routes.py:1655`); the MCP `levels` tool proxies `response.text` byte-for-byte. The byte-identity
+  test compares encoded MCP text to the REST body on a NON-EMPTY result (asserting `confluence_zones`
+  is non-empty first, so the proof is not vacuous). Grep confirmed no second computation path and no
+  premature J-04/J-05 code (`structure_tape` / `research/strategies` / `class_scaled` → no matches).
+
+- **Honest failure states** — three distinct states each return `confluence_zones: []` and are
+  asserted with exact full-dict equality: no series (`no_bar_series_for_symbol: true`), series but
+  nothing derivable (`false`, empty levels), and levels but no qualifying cluster (`false`, non-empty
+  levels). The corrupt-sole-series seam is correctly decide-and-documented (not fixed, per scope):
+  `compute_confluence_zones` reads only the healthy `levels` list, so a corrupt sole series still
+  aliases to `no_bar_series_for_symbol: true` exactly as in iter-2 — no new fabricated/aliased state,
+  ownership retained by `GET /research/bars`.
+
+- **Frozen `default`/`v1` + fingerprint** — all three new `sr_confluence_*` fields are in
+  `config_fingerprint()`'s `excluded` set (`config.py:1366-1368`); I confirmed
+  `config_fingerprint() == '4d665603569b9dbf'` and that changing the band does NOT move the hash,
+  while a real classifier threshold (`min_trade_speed`) still does. The J-07 freeze gate
+  (observer + profile + real-data equivalence, 57 tests) passes.
+
+---
+
+## 4. Fixes Applied During This Audit
+
+None. No CRITICAL or IMPORTANT finding surfaced; all findings are OBSERVATION-level and documenting
+them (not fixing them) is the correct action. No source file, test, or handoff was modified by this
+audit.
+
+### Independent verification performed (evidence)
+
+| Check | Command / method | Result |
+|-------|------------------|--------|
+| Full backend suite (regressions) | `pytest tests/ -q` | 1107 passed, 1 skipped, 0 failed, 0 errors (exit 0) — status-char count 1108 |
+| Confluence + levels + MCP + J-07 gate | `pytest tests/test_levels.py tests/test_levels_api.py tests/test_mcp_server.py tests/test_observer_equivalence.py tests/test_profile_equivalence.py tests/test_real_data_gate.py -q` | 114 passed (exit 0) |
+| Pinned fingerprint + active exclusion | `Config().config_fingerprint()` + counter | `4d665603569b9dbf`; band change does not move hash |
+| Served shape + invariants | direct `compute_levels` call on committed PG fixture | additive `confluence_zones`; classes `[C,C,C,C,C,B]`; A unreachable; `score==Σstrength`; all members within band of anchor |
+| Frontend untouched | `git diff --stat -- apps/frontend/` | empty |
+| No scope creep | grep `structure_tape` / `research/strategies` / `class_scaled` | no matches |
+
+---
+
+## 5. Recommended Next Step
+
+**Proceed.** J-03 fully achieves its goal — `GET /research/levels` (and the byte-identical MCP
+`levels` tool) now serves confluence zones with member levels (+ timeframes), a timeframe-weighted
+score, and an honest A/B/C conviction class, computed once in the Row-39 owner, lookahead-free, with
+`default`/`v1` frozen and the pinned fingerprint unmoved. Required-still-passing J-01/J-02/J-07 remain
+green. The three OBSERVATIONs are honest, documented limitations that do not compromise the phase
+goal and require no action here. The A/B/C zones are ready to be consumed by J-04's `structure_tape`
+entries (arm-at) and J-05's class-scaled risk in later iterations.
diff --git adocs/handoffs/goal-tape_to_profit_support_resistence-iter-3-dev.md bdocs/handoffs/goal-tape_to_profit_support_resistence-iter-3-dev.md
new file mode 100644
index 0000000..0218714
--- /dev/null
+++ bdocs/handoffs/goal-tape_to_profit_support_resistence-iter-3-dev.md
@@ -0,0 +1,201 @@
+# goal-tape_to_profit_support_resistence-iter-3 Dev Handoff
+
+**Phase:** goal-tape_to_profit_support_resistence-iter-3
+**Date:** 2026-07-06
+**Agent:** developer
+**Status:** complete
+
+## What Was Built
+
+J-03 — confluence zones + A/B/C conviction classes, the classification half of Data Contract row 39
+that iter-2 (J-02) deliberately left out of scope. Built entirely INSIDE the existing
+`research/levels.py` (the registered row-39 owner) as an additive field on `compute_levels`'s
+return dict — no new module, endpoint, or MCP tool, per the plan:
+
+- **`research/levels.py`** — two new functions plus three new constants:
+  - **`_cluster_levels(levels, band_bps)`** — pools levels across EVERY timeframe and clusters them
+    by price proximity with an ANCHOR-FIXED scan (sorted ascending by price; the first/lowest
+    member of a cluster fixes its tolerance window — `anchor * band_bps / 10_000` — and every
+    subsequent candidate is compared to that FIXED anchor, never the previous member, so a
+    cluster's price span is bounded by one tolerance rather than an unbounded chain of
+    near-neighbours). Only clusters with >= 2 members are "qualifying" and returned; a lone level
+    has no confluence partner and is silently dropped (never a fabricated one-member "zone").
+  - **`_grade_zone(members, config)`** — the A/B/C decision, by DISTINCT-TIMEFRAME breadth alone
+    (goal.md's "levels that align across timeframes matter more"), never by score: class A needs
+    both a config-owned minimum distinct-timeframe count AND at least one member timeframe in the
+    existing `PRIOR_PERIOD_TIMEFRAMES` long-term bucket (reused verbatim — no second "long-term"
+    list); class B needs only the (lower) distinct-timeframe floor; a qualifying cluster whose
+    members share exactly ONE timeframe grades C — a real, honestly-reported zone of the lowest
+    conviction, never suppressed.
+  - **`compute_confluence_zones(levels, config)`** — the canonical, exported entry point: clusters
+    `levels`, builds each zone (`levels` members, a timeframe-weighted `score` = sum of member
+    `strength` values — already timeframe-weighted per level, so never double-weighted — and the
+    `class`), sorts zones by an explicit total order (`_zone_sort_key`: lowest member price, then
+    member count) for byte-identical served JSON. **A PURE function of the already lookahead-free
+    `levels` list** — it touches no store/bar of its own, so it inherits the as-of truncation for
+    free (no second truncation surface to get wrong).
+  - `CLASS_A = "A"`, `CLASS_B = "B"`, `CLASS_C = "C"` — the three honest grades.
+  - `compute_levels` now returns `{"levels": [...], "no_bar_series_for_symbol": bool,
+    "confluence_zones": [...]}` — the new field is additive, always `[]` when `levels` is empty
+    (whichever honest reason).
+- **Config** (`config.py`): `sr_confluence_band_bps` (float, default 20.0 — wider than the existing
+  `sr_touch_tolerance_bps` of 5.0 because independent timeframes' own detected extremes rarely land
+  on the exact same price the way a single series' own touches do, calibrated against the committed
+  PG fixture to produce several distinct, informative zones rather than one degenerate blob),
+  `sr_confluence_class_a_min_timeframes` (int, default 3), `sr_confluence_class_b_min_timeframes`
+  (int, default 2). All three added to `config_fingerprint()`'s `excluded` set (the identical
+  `sr_pivot_lookback` rationale — confluence is a separate research computation never stamped with a
+  `config_fingerprint`) — the pinned `default` fingerprint stays `4d665603569b9dbf` (verified).
+- **Route** (`research/routes.py`): no route-BODY change — the route already spreads
+  `compute_levels`'s dict verbatim (`**result`), so `confluence_zones` flows through automatically.
+  Updated the comment block above the route (previously marked `classes` "deliberately ABSENT
+  this iteration") and the route's own docstring to describe the new field.
+- **MCP** (`mcp/__init__.py`): no dispatch-logic change — the `levels` tool is a byte-for-byte HTTP
+  proxy of the REST response body, so any new field flows through automatically. Updated the tool's
+  `description` text to mention confluence zones/classes for doc parity.
+
+## Design decisions (beyond the plan's explicit direction)
+
+- **Field name**: `confluence_zones` (not the placeholder `classes` name used in the iter-2
+  "deliberately ABSENT" comments) — clearer, since each zone itself carries a `class`; the plan
+  explicitly left the exact name as the developer's call.
+- **Zone shape**: exactly three keys per zone — `levels` (member level dicts, unchanged shape, each
+  already carrying its own `timeframe`), `score`, `class`. No redundant `timeframes` convenience
+  field was added (a consumer can derive distinct timeframes from `levels[].timeframe` trivially) —
+  keeping the additive contract minimal, per the simplicity bar.
+- **A qualifying cluster needs >= 2 members, of ANY timeframe(s)** — not >= 2 DISTINCT timeframes.
+  A same-timeframe cluster (e.g. two nearby swing pivots on one 1h series) IS a real, reportable
+  zone — just graded C (the lowest conviction), never suppressed. This reads "a symbol with levels
+  but no qualifying cluster returns an explicit empty zones list" as "no qualifying cluster" meaning
+  "no 2+ levels close in price at all," with the A/B/C grade separately answering "how many
+  independent timeframes agree" — cleanly separating the CLUSTERING concern (price-based) from the
+  GRADING concern (timeframe-diversity-based). Verified on the real committed PG fixture: 5 of its 6
+  real zones are same-timeframe (1d-only) C-grade zones.
+- **Class A requires BOTH a distinct-timeframe-count floor AND a long-term member** — not count
+  alone. A direct unit test
+  (`test_confluence_class_a_requires_a_long_term_member_not_just_timeframe_count`) proves a
+  3-distinct-timeframe cluster with NO long-term member (1h+4h+8h) grades B, not A — the two
+  conditions are independently enforced.
+- **Anchor-fixed clustering, not chained-to-previous-member** — documented and directly tested
+  (`test_confluence_clustering_is_anchor_fixed_not_chained_to_the_previous_member`) to prevent the
+  classic clustering defect where a chain of pairwise-close levels lets a cluster's price span drift
+  unbounded.
+- **Corrupt-sole-series seam (plan's explicit ask to decide + document, not fix)**: confirmed by
+  inspection that `compute_confluence_zones` takes ONLY the already-derived `levels` list as input —
+  it never touches `store` or `BarStore.list()`'s `integrity_errors` half. A symbol whose sole bar
+  series is corrupted therefore still aliases to `no_bar_series_for_symbol: true` with an empty
+  `confluence_zones` list, exactly as it aliased before confluence existed (iter-2's B1 finding,
+  unchanged). The distinct corrupt-series honest state remains owned by `GET /research/bars`. J-03
+  introduces no new fabricated or aliased state at the levels endpoint.
+
+## Files Changed
+
+- `apps/backend/app/config.py` -- `sr_confluence_band_bps`, `sr_confluence_class_a_min_timeframes`,
+  `sr_confluence_class_b_min_timeframes`; all three excluded from `config_fingerprint`
+- `apps/backend/app/research/levels.py` -- `_cluster_levels`, `_grade_zone`, `_confluence_zone`,
+  `_zone_sort_key`, `compute_confluence_zones`, `CLASS_A`/`CLASS_B`/`CLASS_C`; `compute_levels`
+  wires `confluence_zones` into its return dict; module + function docstrings updated (confluence
+  classes are now in scope, no longer "J-03, out of scope here")
+- `apps/backend/app/research/routes.py` -- updated the comment block above `GET /research/levels`
+  (previously "classes deliberately ABSENT") and the route's own docstring; no route-body change
+- `apps/backend/app/mcp/__init__.py` -- updated the `levels` tool's `description` text; no
+  dispatch-logic change (already a byte-identical proxy that forwards any new field)
+- `apps/backend/tests/test_levels.py` -- extended: 11 new test functions (8 direct
+  `compute_confluence_zones` unit tests covering clustering/scoring/A/B/C grading/anchor-fixed
+  behaviour/sorting/empty cases; a new 3-timeframe synthetic bar fixture (`_confluence_fixture`,
+  symbol `SYN-CONFLUENCE`) proving a real bar-derived class A zone through `compute_levels` end to
+  end; an exact-value test on the committed PG fixture; an honest-empty-zones test reusing the
+  existing J-02 swing fixture) plus in-place extensions to 6 existing tests (the lookahead-free
+  test now asserts zones/class are unaffected by a later bar too; the determinism test asserts a
+  non-vacuous zone; the three honest-state tests assert `confluence_zones: []`; the no-magic-numbers
+  and fingerprint-exclusion tests cover the three new config fields)
+- `apps/backend/tests/test_levels_api.py` -- extended the happy-path test to assert
+  `confluence_zones == []` on its single-timeframe fixture; extended the three honest-state tests
+  the same way; added one new route-level test that seeds the real committed PG fixture pair
+  directly into the temp bar dir (mirroring `test_mcp_server.py`'s technique) and asserts the exact
+  zones shape through the REAL route
+- `apps/backend/tests/test_mcp_server.py` -- extended the existing `levels` byte-identity test with
+  a `confluence_zones` non-empty assertion (the byte-for-byte proxy check already covered the field
+  structurally; this makes the coverage intent explicit and non-vacuous)
+
+`git diff -- apps/frontend/` is **empty** — confirmed no frontend file was touched.
+
+## Tests Run
+
+Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q --junit-xml=/tmp/junit.xml`
+Result (JUnit XML totals): **1107 passed, 1 skipped, 1108 collected, 0 failed, 0 errors**, 362.28s.
+The single skip is the same pre-existing gated live-socket test noted in every prior iteration's
+handoff. Up from iter-2's baseline of 1095 passed / 1096 collected — **+12 new tests** (11 in
+`test_levels.py`, 1 in `test_levels_api.py`), **zero regressions**.
+
+Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py tests/test_profile_equivalence.py tests/test_real_data_gate.py -v`
+Result: **57 passed** (7 + 15 + 35 — identical counts to iter-1/iter-2's handoffs; the J-07
+byte-identical-`default` guard, the pinned-fingerprint test, and the vendor-confinement gate are all
+unaffected).
+
+Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_levels.py tests/test_levels_api.py tests/test_mcp_server.py -v`
+Result: **57 passed** (26 + 10 + 21).
+
+Command: `cd apps/backend && .venv/bin/python -c "from app.config import CONFIG; assert CONFIG.config_fingerprint() == '4d665603569b9dbf'"`
+Result: passes — the pinned `default` fingerprint is confirmed unchanged despite three new
+`Config` fields.
+
+Command: `git diff --stat -- apps/frontend/`
+Result: empty (no output) — confirmed.
+
+Command: `grep -rn "structure_tape\|research/strategies\|research\.strategies" apps/backend/app/`
+Result: no matches — confirmed J-04–J-06 remain unbuilt, no scope creep.
+
+## Pre-Handoff Verification
+
+- **Service startup**: ran `bash scripts/dev.sh`, confirmed backend (uvicorn on :8301) and frontend
+  (Next.js on :3301) started cleanly with no errors. Force-stopped every backend/frontend PID
+  (including the `next-server`/`next dev` grandchild worker processes noted in iter-2's handoff —
+  `pkill -f "next dev"` alone did not catch them this run either; killed by explicit PID), confirmed
+  both ports free via `lsof`, then ran `dev.sh` a second time — both services bound cleanly with no
+  port conflicts.
+- **Live smoke test** (against the real `dev.sh`-started backend, not just the test suite): seeded
+  the committed PG fixture pair into `apps/backend/.data/bars/`, then hit
+  `GET /research/levels?symbol=PG&as_of=2026-06-09T21:00:00Z` over real HTTP and called the MCP
+  `levels` tool against that same live backend via `TAPEOLOGY_API_BASE` — both returned
+  `confluence_zones` with the identical 6-zone (5×C, 1×B) result verified in the test suite. Also
+  checked live: a missing `as_of` (422), a malformed `as_of` (422), and an unrecorded symbol
+  (`no_bar_series_for_symbol: true`, `confluence_zones: []`). Seeded fixture files were removed from
+  the dev data directory after the check; no test data was left behind.
+- **No new external integration or native dependency** this iteration (a pure derived-computation
+  layer over the existing bar store) — the corresponding pre-handoff checklist items are N/A.
+
+## Known Issues
+
+- **`sr_confluence_band_bps` (20.0 bps default) is a documented research starting point, not a
+  validated edge** — same "RESEARCH DEFAULT, calibrated against the sims/fixtures, never a
+  validated edge" discipline the existing `sr_pivot_lookback` etc. already use. Calibrated so the
+  committed PG fixture (2 timeframes) forms several distinct, informative zones rather than one
+  degenerate blob spanning the whole price range — verified by direct computation, not
+  hand-derived, and asserted exactly in `test_levels.py`.
+- **`sr_confluence_class_a_min_timeframes` / `sr_confluence_class_b_min_timeframes` are single
+  global values**, matching the plan's own precedent (`sr_pivot_lookback` /
+  `sr_touch_tolerance_bps` are likewise single global values, not per-timeframe or per-symbol).
+- **The committed real PG fixture can never produce a class A zone** (it stores only 1h + 1d — two
+  timeframes; class A needs three) — an honest, documented consequence of the committed data's own
+  breadth (flagged in the plan's own "Known Consideration"), not a defect. Class A is proven
+  reachable through the real bar-driven `compute_levels` path on a dedicated synthetic 3-timeframe
+  fixture (`SYN-CONFLUENCE`, `test_synthetic_three_timeframe_fixture_produces_exact_a_b_c_zones_through_compute_levels`)
+  and directly on the pure `compute_confluence_zones` function
+  (`test_confluence_clustering_joins_within_band_across_timeframes_and_grades_class_a`).
+- **No support-vs-resistance "kind" labelling of a zone** — correctly out of scope per the phase
+  spec (a J-04 tape-confirmation concern); a zone is a horizontal price cluster only.
+- **J-04–J-06 remain unbuilt, as scoped** — no `structure_tape` strategy, strategy registry, or
+  named-strategy comparison exists yet; `GET /research/strategies` still 404s (grep-confirmed no
+  such route/module exists).
+- **No frontend/UI surface** — machine-only (REST + MCP), as scoped; no page, panel, or nav change.
+  Confirmed via `git diff -- apps/frontend/` (empty).
+- **The corrupt-sole-series seam decision (iter-2 B1, revisited)**: unchanged from iter-2 — a
+  corrupted sole bar series still aliases to `no_bar_series_for_symbol: true` rather than a distinct
+  integrity-error state at the levels endpoint. See "Design decisions" above; this is a deliberate,
+  documented scope reading (the phase spec explicitly asks to decide-and-document, not fix), not a
+  gap discovered mid-implementation.
+- **`.claude/project-template.md` is still the generic unfilled template** (carried over from every
+  prior iteration, not this iteration's scope) — this developer again used `docs/goal.md`'s
+  Constraints section, `scripts/dev.sh`, and the venv at `apps/backend/.venv/` as the actual stack
+  source of truth. The backend venv runs Python 3.14.4.
diff --git adocs/phases/goal-tape_to_profit_support_resistence-iter-3.md bdocs/phases/goal-tape_to_profit_support_resistence-iter-3.md
new file mode 100644
index 0000000..3435410
--- /dev/null
+++ bdocs/phases/goal-tape_to_profit_support_resistence-iter-3.md
@@ -0,0 +1,103 @@
+# Goal Iteration 3 — J-03: confluence zones + A/B/C conviction classes
+
+<!-- machine-readable goal-mode metadata -->
+## Goal Mode Metadata
+
+- **Session ID:** tape_to_profit_support_resistence
+- **Iteration:** 3
+- **Mode:** next
+- **Depth:** full
+- **Frontend Present:** no
+- **Target journeys:** J-03
+- **Required-still-passing journeys:** J-01, J-02, J-07
+- **Anti-goal reminders (verbatim from `docs/goal.md`; most load-bearing for J-03: No lookahead · No ML/no online tuning · No fabricated data · Single source of truth · frozen `default`/`v1` · MCP read-only):**
+  - **No live execution path.** Tapeology MUST NOT place, route, or transmit orders anywhere — no brokerage integration, no trading API, **no paper-trading API**, no order tickets. The ONLY permitted "fill" is the offline backtester's simulated fill against recorded historical tape, clearly labelled simulated and sent nowhere; "position size" is a simulated notional, never a real order. *(critical)*
+  - **No profit claims and no advice.** Simulated PnL is a caveated measurement: it MUST always appear with its R counterpart, its n, its fee/slippage assumptions, its train-or-hold-out basis, and its null baseline — never presented as expected live results, an edge claim, or a reason to trade. No imperative cues, no prediction language. *(critical)*
+  - **The tape engine, `default` profile, and `v1` strategy are frozen.** Structure work is additive and versioned only: new bars/levels/classes and the `structure_tape` strategy may be added, but the `default` profile's outputs stay byte-identical (equivalence-tested), the live cockpit uses `default` only, `v1` stays byte-identical, and no enhancement may mutate an archived-era behaviour to pass. *(critical)*
+  - **No train-only promotion.** Nothing becomes the champion on train data alone: hold-out survival (net R AND net $, at the configured minimum n) is the only promotion gate; overfit results are labelled overfit. *(critical)*
+  - **No lookahead.** Levels and classes computed "as of" time T use only bars at or before T; a backtest may never see a level derived from data after the moment it is used. *(critical)*
+  - **No ML, no online tuning.** S/R detection, confluence scoring, class thresholds, and class-based risk are bounded, config-enumerated, offline, and deterministic; no fitted models, no optimizer loops in the engine, no thresholds that move at runtime.
+  - **No fabricated data — honest failure states.** No synthesized bars, levels, trades, fills, or PnL to force a green journey; every failure mode (backend down, corrupt file, empty window, missing credentials, rate-limited, no levels found, insufficient n) surfaces an explicit, distinct state. *(critical)*
+  - **Single source of truth.** Every canonical value — bar series, levels, confluence classes, backtest aggregates, PnL rows — is computed once and read verbatim by every surface (REST, WebSocket, UI, MCP, reports). A second computation path or a diverging number across surfaces is a defect. *(critical)*
+  - **No capital or portfolio management.** Class "position size" is a per-trade simulated notional only — no account, no equity curve, no compounding projection, no real position tracking. *(critical)*
+  - **MCP is read-only.** The MCP server exposes no mutating tools, proxies only the canonical GET surface (plus the allowlisted `get_endpoint`), and MUST NOT become a second implementation of any computation. *(critical)*
+  - **Persistence stays scoped.** SQLite holds research records; the bar and dataset stores hold explicitly recorded historical bars and tape for research replay. The live cockpit's tape remains unpersisted; no ambient recording. *(critical)*
+  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the AUTO:journeys marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a PnL-ledger acceptance criterion, keep the `default` profile and `v1` byte-identical, and include a [NEW]-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*
+
+## GOAL
+
+A researcher calling `GET /research/levels` (and the read-only MCP `levels` tool) receives, beside the raw support/resistance levels, the **confluence zones** that cluster those levels across timeframes — each zone carrying its member levels (with timeframes), a timeframe-weighted score, and an honest **A / B / C** conviction class.
+
+## BACKGROUND
+
+J-01 (bar store) and J-02 (deterministic, lookahead-free S/R levels) are passing; iter-2's evaluator returned CONTINUE with a `full` recommendation and named J-03 as the natural next step, iter-2's coherence was COHERENCE-PASS (no consolidation owed). Following the priority rubric: no journey is regressed (rule 1 n/a), no coherence FAIL to consolidate (rule 2 n/a), and **J-03 is the unblocker** — it produces the A/B/C classified zones that J-04's `structure_tape` entries arm at and that J-05's class-scaled risk consumes, and it shares blueprint Data-Contract Row 39 with J-02 (rule 3). It is also the smallest change set — a single additive field on the *existing* `GET /research/levels` response, computed in the *existing* `research/levels.py` owner (rule 4) — and it is the only risky journey carried this iteration (rule 5). Depth is **full** by the "Picking depth" triggers (cited, not because of ESCALATE — prior verdict was CONTINUE): it (a) introduces a new canonical computation (confluence clustering + timeframe-weighted scoring + A/B/C grading), (b) requires new correctness tests beyond browser smoke (deterministic clustering, byte-identical re-runs, config-owned thresholds, honest labelling), and (c) extends the **critical no-lookahead** property to classes — and, being a machine surface with no browser smoke to catch a wiring slip, the test suite IS the acceptance, which warrants the fuller audit/QA/coherence pass.
+
+## IN SCOPE
+
+### Backend
+- [ ] Add config-owned confluence parameters to `apps/backend/app/config.py`, `sr_`-namespaced and each documented with rationale (no magic numbers): a **clustering tolerance / confluence band** (e.g. `sr_confluence_band_bps`) and the **A/B/C class thresholds** (e.g. score cutoffs and/or the confluence criteria such as minimum distinct timeframes / required long-term member). **Add every new field to the `config_fingerprint()` `excluded` set** (the same rationale as the three existing `sr_*` level fields at `config.py:1320-1322`) — they are a separate research computation input, never a tape/backtest/PnL value; the pinned `default` fingerprint MUST stay `4d665603569b9dbf` (iter-1 lesson: any non-excluded new field silently breaks J-07).
+- [ ] Add deterministic, lookahead-free confluence clustering + A/B/C classification **inside the existing `apps/backend/app/research/levels.py`** (the registered Row-39 owner — NO new module, endpoint, or owner): cluster the levels already computed by `compute_levels` across timeframes whose prices fall within the config band into confluence zones; score each zone = timeframe-weighted sum of its member levels' strengths; grade it A/B/C by the config thresholds/criteria. Each zone records its **member levels (with timeframes)**, its **score**, and its **class**. Sort zones by an explicit total order so the served JSON is byte-identical.
+- [ ] Return the zones as an **additive** field on `compute_levels`' existing return dict (e.g. `confluence_zones` / `classes`, beside `levels` and `no_bar_series_for_symbol`) — served verbatim by the existing `GET /research/levels` route and the existing read-only MCP `levels` proxy. No second computation path; MCP JSON stays byte-identical to REST.
+- [ ] Honest labelling: a zone is class **A only when the config confluence criteria are met** (e.g. several timeframes including a long-term level within tolerance), honestly graded B/C otherwise; a symbol with no series keeps `no_bar_series_for_symbol: true` with an empty zones list; a symbol with levels but no qualifying cluster returns an explicit empty zones list — never a fabricated zone or class.
+- [ ] Decide + document the corrupt-sole-series seam (iter-2 B1 lesson): confirm the confluence layer introduces **no new fabricated or aliased state** — it reads only the healthy levels `compute_levels` already produces; the *distinct* corrupt-series honest state remains owned by `GET /research/bars`. Record this decision in the dev handoff.
+
+### Frontend
+- N/A — J-03 is a machine surface (REST + MCP) only. The nav skeleton (Cockpit · Journal · Studies · Performance) is unchanged this era; `apps/frontend/` MUST NOT change.
+
+### New user-facing capability
+Through `GET /research/levels` (+ MCP `levels`), a researcher can now read the confluence structure of a symbol's S/R levels — which levels cluster across timeframes and how much conviction (A/B/C) each cluster carries — the structural conviction layer J-04's tape-confirmed entries will later arm at.
+
+### New information displayed
+Confluence zones on the `GET /research/levels` response: per zone, its member levels (each with timeframe), its timeframe-weighted score, and its A/B/C class.
+
+### New user actions
+None — read-only GET; machine surface, no new controls.
+
+### UI surface changes
+None — no page, panel, or nav change.
+
+### Product surface delta
+The levels endpoint graduates from a flat list of levels to "levels + their confluence conviction structure (A/B/C)". No visual/UI change.
+
+### Blueprint conformance
+J-03's output lives on the **already-registered Row-39 canonical home** — `GET /research/levels` + MCP `levels` (machine surface, no nav home) — exactly as the baseline blueprint's Information Architecture places it (feature-home table, "J-03 confluence zones + A/B/C classes | API `GET /research/levels` (same endpoint) + MCP `levels`"). No nav-skeleton change; no `blueprint.reapproval-requested` written.
+
+### Data-contract additions
+**None.** Blueprint Data-Contract **Row 39** ("Support/resistance levels + A/B/C confluence classes") already registers the confluence zones + A/B/C classes with a single owner (the S/R + confluence module in `research/levels.py`) and a single serving endpoint (`GET /research/levels` + MCP `levels`); its notes already name "confluence band, class thresholds" as config-sourced. J-03 ships the previously-out-of-scope **classes half** of that already-registered row — it adds no new canonical value and no new endpoint/owner, so the blueprint needs no edit. The new confluence config params (band, class thresholds) are computation **inputs**, not displayed values, so they take no Data-Contract row (config-owned + fingerprint-excluded, per Row 39's "every parameter config-sourced" note).
+
+## OUT OF SCOPE
+
+- **J-04** (`structure_tape` strategy / strategy registry / `GET /research/strategies`), **J-05** (class-scaled stop/reward/simulated size), **J-06** (named-strategy comparison vs `v1`) — later iterations.
+- Any **new endpoint, MCP tool, or module** — the zones ride the existing `GET /research/levels` route, the existing MCP `levels` proxy, and the existing `research/levels.py` owner.
+- Any **support-vs-resistance "kind" labelling** of a zone — a zone is a horizontal price cluster; whether it acts as support or resistance depends on the tape at approach time and is **J-04's** tape-confirmation concern (goal.md's J-03 acceptance requires only clustering, scoring, and A/B/C grading — not direction).
+- Any **new distinct honest state for a corrupt SOLE bar series** at the levels endpoint — that honesty is owned by `GET /research/bars` (decide-and-document only; do not add a new state here).
+- Any change to the **raw levels computation**, the bar store, the `default` profile, `v1`, or any archived-era surface.
+- Any **frontend/UI/nav change**, any levels view, and any cross-timeframe bar aggregation.
+
+## DEFINITION OF DONE
+
+- [ ] **J-03 passes** — `GET /research/levels` (and MCP `levels`) returns confluence zones, each with its member levels (+ timeframes), a timeframe-weighted score, and an A/B/C class; verified by the backend acceptance suite (machine surface — the test suite IS the acceptance; browser-qa correctly N/A, documented).
+- [ ] Clustering tolerance (confluence band) and A/B/C class thresholds/criteria are **config-owned** — a no-magic-numbers introspection test (extending `tests/test_levels.py`'s existing pattern) asserts no literal thresholds in `levels.py`.
+- [ ] A zone is graded **class A only when the config confluence criteria are met**; a non-qualifying cluster is honestly graded B/C or absent — asserted with exact expected classes on the committed bar fixture.
+- [ ] **Byte-identical** deterministic re-runs of the zones/classes (explicit total order) — asserted.
+- [ ] **No-lookahead extended to classes** — zones/classes at as-of T derive only from bars ≤ T; a bar after T cannot change any zone or class — asserted in the same physical-truncation style as J-02.
+- [ ] **MCP `levels` remains byte-identical** to the REST response including the new zones field (single source of truth) — asserted.
+- [ ] **Required-still-passing J-01, J-02, J-07 remain green:** full backend suite passes; `Config().config_fingerprint() == '4d665603569b9dbf'` unchanged (new confluence fields in the `excluded` set); engine observer + profile equivalence byte-identical (`default`/`v1` frozen); `git diff <iter-3 base snapshot>..HEAD -- apps/frontend/` is empty.
+- [ ] No anti-goal violation introduced (no ML/fitting, no lookahead, no fabricated zone, single source of truth, no second computation path, MCP read-only) — grep/scan CLEAN.
+- [ ] Unit tests pass; no regressions.
+- [ ] Dev handoff written at `docs/handoffs/goal-tape_to_profit_support_resistence-iter-3-dev.md` (including the corrupt-sole-series seam decision).
+
+## TESTING REQUIREMENTS
+
+- **Browser:** none — J-03 is a backend/machine surface (REST + MCP); browser-qa is correctly N/A. Documented reason: no frontend/UI/nav change (`apps/frontend/` untouched — the executor must confirm the empty frontend diff, per the iter-0/iter-2 lesson that zero-frontend-diff iterations need no screenshot evidence).
+- **Unit/integration:** extend `apps/backend/tests/test_levels.py` + `tests/test_levels_api.py` — deterministic clustering into zones; timeframe-weighted score exactness; A/B/C grading on the committed fixture with **exact expected classes**; config-owned thresholds (no-magic-numbers introspection); byte-identical re-runs; no-lookahead-for-classes (physical truncation); honest empty-zones state and `no_bar_series_for_symbol` state. Extend the MCP byte-identity test to cover the new zones field. Extend/confirm the fingerprint-stability test so the new confluence config fields are excluded and the `default` fingerprint is unmoved.
+- **Error cases:** symbol with no series → `no_bar_series_for_symbol: true`, empty zones (not fabricated); symbol with levels but no qualifying cluster → explicit empty zones list; invalid / out-of-set `as_of` handled by the existing route validation (unchanged — assert no regression); an unknown timeframe weight still raises rather than fabricating.
+
+## NOTES
+
+- **Lessons applied** (session `lessons.md`):
+  - *iter-1 (config fingerprint + vendor names):* any new `Config` field silently moves the pinned `default` fingerprint (`4d665603569b9dbf`) and breaks J-07 unless added to the `config_fingerprint()` `excluded` set — the new confluence band + class-threshold fields (a separate research computation, never a tape/backtest value) MUST be excluded, exactly as the three `sr_*` level fields were. (Vendor-name-in-config is not a risk here — the confluence code touches no vendor SDK.)
+  - *iter-2 (corrupt sole series):* `compute_levels` reads only the healthy half of `BarStore.list()`, so a corrupt SOLE series currently aliases to `no_bar_series_for_symbol: true`; the distinct corrupt-series state is owned by `GET /research/bars`. J-03 makes this a conscious decision — keep that ownership (confluence adds no new fabricated/aliased state) and document it; do not add a new corrupt state at the levels endpoint.
+- **Single-source-of-truth discipline** (the coherence-auditor's central check): confluence zones are computed ONCE in `research/levels.py` (the Row-39 owner) and served verbatim by the one route + the one MCP proxy — no second computation path, no divergent serialization.
+- The codebase already anticipates this additive field: `apps/backend/app/research/levels.py:2` and `apps/backend/app/research/routes.py:1631` both mark `classes` (J-03 confluence) as deliberately absent pending this iteration.
+- References: iter-2 `eval.md` next-step recommendation (advance to J-03, full, additive `classes` field on the existing endpoint); iter-2 `coherence.md` COHERENCE-PASS (Row 39 canonical home confirmed).
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-3-closure-verdict.md breports/phase-goal-tape_to_profit_support_resistence-iter-3-closure-verdict.md
new file mode 100644
index 0000000..fb868d6
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-3-closure-verdict.md
@@ -0,0 +1,130 @@
+# Phase goal-tape_to_profit_support_resistence-iter-3 — Closure Verdict
+
+**Phase:** goal-tape_to_profit_support_resistence-iter-3
+**Date:** 2026-07-06
+**Written by:** phase-closure-auditor
+
+---
+
+**Verdict:** CLOSURE-PASS
+
+---
+
+## Standard Pipeline Gate Checks
+
+| Artifact | Status | Verdict |
+|----------|--------|---------|
+| Review report (`reports/reviews/goal-tape_to_profit_support_resistence-iter-3-review.md`) | exists | PASS |
+| QA report (`reports/qa/goal-tape_to_profit_support_resistence-iter-3-qa.md`) | exists | PASS |
+| Audit report (`docs/handoffs/goal-tape_to_profit_support_resistence-iter-3-audit.md`) | exists | PASS |
+
+All three gates carry unambiguous PASS verdicts. Audit performed independent re-verification, not
+a rubber-stamp of the dev handoff: re-ran the full backend suite (1107 passed / 1 skipped / 0
+failed, exit 0), re-derived `Config().config_fingerprint()` and confirmed it equals the pinned
+`4d665603569b9dbf` with the three new confluence fields excluded (and confirmed a real-threshold
+change WOULD move the hash, proving the exclusion is live, not vacuous), re-read the clustering
+(`_cluster_levels`) and grading (`_grade_zone`) source directly rather than trusting the handoff's
+description, and re-confirmed `git diff --stat -- apps/frontend/` is empty. Three OBSERVATION-level
+findings (B1/B2/B3) were logged, none CRITICAL/IMPORTANT, none requiring a fix.
+
+---
+
+## UI Visibility Artifact Checks
+
+`Frontend Present: no` (declared in `runs/goal-tape_to_profit_support_resistence-iter-3/plan.md`
+line 50, and matches the phase spec's "Frontend: N/A — J-03 is a machine surface... `apps/frontend/`
+MUST NOT change"). Per the phase-closure-gate skill, N/A stubs are acceptable for all 6 artifacts in
+this case, provided they exist and are honestly N/A rather than hiding vagueness.
+
+| Artifact | Exists | Non-Empty | Non-Vague | Status |
+|----------|--------|-----------|-----------|--------|
+| implementation-summary.md | yes | yes (105 lines, substantive) | yes — real content | OK |
+| user-visible-changes.md | yes | yes (5 lines) | yes — honest N/A, reasoned | OK |
+| ui-surface-map.md | yes | yes (5 lines) | yes — honest N/A, reasoned | OK |
+| ui-test-plan.md | yes | yes (3 lines) | yes — honest N/A, reasoned | OK |
+| ui-test-results.md | yes | yes (5 lines) | yes — SKIPPED with documented reason | OK |
+| what-to-click.md | yes | yes (3 lines) | yes — honest N/A, reasoned | OK |
+
+Note: `implementation-summary.md` is a full, plain-language write-up of the confluence-zone feature
+(not an N/A stub) — this is correct: the *implementation* is real and substantial even though there
+is no *UI* for it. The other 5 artifacts are properly short N/A stubs, since there is genuinely no
+frontend surface this iteration.
+
+No `reports/phase-goal-tape_to_profit_support_resistence-iter-3-ux-regression.md` exists. This is
+consistent with a backend-only iteration where browser QA was correctly not run (nothing for a UX
+regression reviewer to check); its absence is not a blocking gap here.
+
+---
+
+## Cross-Reference Checks
+
+- [x] user-visible-changes lists ≥1 specific capability, **or** is honestly N/A for backend-only —
+  N/A, consistent with Frontend Present: no.
+- [x] ui-surface-map has specific route/component entries, **or** is honestly N/A — N/A ("No UI
+  surfaces affected"), consistent.
+- [x] ui-test-plan has specific steps, **or** is honestly N/A — N/A, consistent.
+- [x] ui-test-results shows execution evidence, **or** SKIPPED with documented reason — SKIPPED,
+  reason given: "Backend-only phase (Frontend Present: no). No browser tests executed." This
+  matches the phase spec's own TESTING REQUIREMENTS section, which pre-declares browser tests as
+  correctly N/A and requires only a confirmed-empty `apps/frontend/` diff as evidence.
+- [x] what-to-click has ≥3 numbered steps, **or** is honestly N/A — N/A, consistent.
+- [x] implementation-summary claims are consistent with ui-test-results evidence — yes. The
+  implementation-summary's own "Backend-Only Items" section states explicitly: "there is still no
+  page or panel in the website that displays it" and "No screen to view zones/grades yet: an
+  operator can see zone and grade information only through the API/MCP tools right now, not through
+  a page in the website." This directly matches (does not contradict) the N/A claims in
+  user-visible-changes.md and ui-surface-map.md. There is no case here of a feature described as
+  "user-facing" or "complete UI capability" while the UI artifacts claim nothing changed — the
+  implementation-summary itself is careful to frame every capability as machine-surface-only.
+
+**Independent verification performed by this gate** (not just re-reading claims):
+- `git diff --stat -- apps/frontend/` → empty (confirmed directly, exit code 0, no output).
+- `git status --short -- apps/frontend/` → empty; no untracked frontend files either.
+- `runs/goal-tape_to_profit_support_resistence-iter-3/status.json` `changed_files` list contains
+  only: `config.py`, `research/levels.py`, `research/routes.py`, `mcp/__init__.py`, three backend
+  test files, the dev handoff, and the implementation-summary — zero frontend paths.
+- Cross-checked review, QA, and audit reports' test-count claims against each other: dev handoff
+  claims 1107 passed/1 skipped/0 failed (+12 new tests, 0 regressions); QA reproduces the identical
+  JUnit output verbatim; audit independently re-ran the suite and reports the identical 1107/1/0/0.
+  No discrepancy across the three independent reports.
+
+---
+
+## Backend-Only Claim Guard (Step 4)
+
+Both trigger conditions were checked and neither fires:
+
+1. `user-visible-changes.md` says "no visible changes" **AND** `ui-surface-map.md` shows affected
+   frontend files → **Does not apply.** `ui-surface-map.md` shows **zero** affected frontend files
+   (explicitly "No UI surfaces affected"), consistent with the confirmed-empty `apps/frontend/`
+   diff. No inconsistency.
+2. implementation-summary lists capabilities **AND** browser-qa shows all SKIPPED **AND** no
+   documented reason → **Does not apply.** A documented reason exists in `ui-test-results.md`
+   ("Backend-only phase (Frontend Present: no)"), and the phase spec itself pre-declares browser
+   testing as N/A for this iteration ("Browser: none — J-03 is a backend/machine surface (REST +
+   MCP); browser-qa is correctly N/A... zero-frontend-diff iterations need no screenshot
+   evidence"). This is exactly the rule's stated non-blocking exception: backend-scoped phase
+   language + SKIPPED + documented reason = acceptable.
+
+---
+
+## Blocking Issues
+
+None.
+
+---
+
+## Non-Blocking Notes
+
+- Three OBSERVATION-level findings from the audit report (B1: real PG fixture structurally cannot
+  reach class A — 2 committed timeframes vs. a 3-timeframe requirement, honestly documented and
+  proven reachable via a dedicated synthetic fixture; B2: same-price levels of different `type` both
+  count toward a zone's score — by design, not a defect; B3: the ">= 2 members" cluster-minimum is a
+  code literal rather than a config field — judged structural, not a tunable research threshold) are
+  carried forward as documented, non-blocking limitations. None required a fix and the audit
+  explicitly declined to treat them as gaps.
+- No UX-regression report was produced for this iteration; reasonable given there is no UI surface
+  to regress-check (Frontend Present: no, zero frontend diff, browser QA correctly N/A).
+- This iteration's changes are currently uncommitted working-tree modifications (confirmed via `git
+  status`) — closure of this phase-audit gate does not include the commit/release step, which is a
+  separate pipeline stage.
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-3-implementation-summary.md breports/phase-goal-tape_to_profit_support_resistence-iter-3-implementation-summary.md
new file mode 100644
index 0000000..7f98f19
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-3-implementation-summary.md
@@ -0,0 +1,105 @@
+# goal-tape_to_profit_support_resistence-iter-3 — Implementation Summary
+
+**Phase:** goal-tape_to_profit_support_resistence-iter-3
+**Date:** 2026-07-06
+**Written by:** developer
+
+---
+
+## Features Implemented
+
+- **Grouping price levels that line up across timeframes into "confluence zones"**: Building on the
+  previous iteration's individual support/resistance price levels, the system now looks at all of a
+  symbol's levels together — across every timeframe (hourly, daily, weekly, and so on) — and groups
+  together any that sit close to the same price into a single "zone." A zone that only ever shows up
+  on one timeframe stays its own separate thing; a zone where several different timeframes agree on
+  roughly the same price is grouped as one.
+- **Each zone gets a conviction grade (A / B / C)**: Every zone is graded honestly based on how many
+  *different* timeframes agree on it, and whether at least one of those timeframes is a longer-term
+  one (daily, weekly, or monthly). A zone confirmed by several timeframes including a longer-term
+  one earns the top grade, "A." A zone confirmed by two different timeframes earns "B." A zone that
+  only shows up within a single timeframe (for example, two nearby turning points both found on the
+  hourly chart) still gets reported — honestly, as the lowest grade, "C" — rather than being hidden.
+  Nothing is ever upgraded or invented to make a zone look stronger than it is.
+- **Each zone also carries a combined strength score**: The individual strength numbers of every
+  level inside a zone are added together into one combined score for the zone, so a zone's overall
+  weight-of-evidence is visible alongside its letter grade.
+- **No hindsight allowed, extended to zones and grades**: The same "no looking into the future"
+  guarantee proven for individual levels last iteration now also covers zones and their grades — a
+  price bar recorded after the moment you're asking about can never change a zone or its grade,
+  proven directly by comparing the answer with and without that later bar physically present in
+  storage.
+- **Always the same answer for the same question**: Asking the same "zones as of this time"
+  question twice in a row, or from two separate copies of the tool, always returns the identical
+  result, down to the byte — the same guarantee individual levels already had.
+- **Honest "nothing to show" messages, extended**: A symbol with levels but none of them close
+  enough together to form a zone now honestly reports an empty zone list — never a fabricated zone,
+  and never confused with "this symbol has no price history at all" (which remains its own,
+  separate honest answer from last iteration).
+- **Available everywhere levels already were**: The zone and grade information rides on the exact
+  same web address and the exact same AI-assistant (MCP) tool that already served individual levels
+  — there is no new web address or new tool to learn, and the machine-tool answer stays
+  word-for-word identical to the website's own answer, as with every other feature in this project.
+
+## Changed Behavior
+
+- None beyond the addition itself. Every existing feature — the live trading-tape cockpit, the
+  research journal, the studies page, the performance page, and last iteration's individual
+  support/resistance levels — behaves exactly as before (confirmed: zero files under the website's
+  frontend code were touched, and the full backend test suite, including the dedicated
+  "nothing changed" checks, stayed green).
+
+## Backend-Only Items
+
+- The new zone/grade information rides on `GET /research/levels` (the same machine endpoint from
+  last iteration) plus the matching MCP tool — there is still no page or panel in the website that
+  displays it. That remains intentionally out of scope for this step; a future "levels" screen
+  showing zones and grades visually is possible later, but this iteration is purely the underlying
+  calculation.
+
+## Incomplete Items
+
+- **A real trading strategy that reacts to graded zones, and honestly measuring whether it would
+  have made money**: This iteration only produces the zones and their letter grades. The next
+  planned steps — building a strategy that enters a trade when price reaches a graded zone and the
+  live tape confirms a direction, sizing that trade and its risk based on the zone's grade, and then
+  honestly measuring (on saved historical data, never live money) whether that strategy would have
+  beaten doing nothing — are **not** part of this iteration and remain to be built.
+- **No screen to view zones/grades yet**: an operator can see zone and grade information only
+  through the API/MCP tools right now, not through a page in the website.
+
+## Config and Environment Changes
+
+- No new environment variables were added. Three new *internal* settings now exist in the system's
+  one central settings file (all with sensible starting defaults, clearly labelled as starting
+  points rather than proven-optimal values): how close in price two levels from different
+  timeframes must be to count as the "same" zone, how many different timeframes a zone needs to earn
+  the top "A" grade, and the (lower) bar for the middle "B" grade.
+- No database migration was needed and no new external account/service is introduced — this feature
+  only re-groups price levels the system already computes from bar data it already has saved.
+
+## Known Limitations
+
+- **The "how close counts as the same zone" and "how many timeframes for each grade" numbers are
+  reasonable starting points, not scientifically validated values.** They were chosen to be sensible
+  and are documented as such (the same honesty standard already applied to similar starting-point
+  settings elsewhere in the project) — they have not been tested against real trading outcomes yet.
+- **The one real, committed sample of saved price history only covers two timeframes (hourly and
+  daily), so it can never by itself produce a top-grade "A" zone** (an A-grade zone needs a third
+  timeframe to agree). This is an honest, expected consequence of how much sample data exists today,
+  not a bug — a top-grade zone IS proven to work correctly using a purpose-built practice example
+  with three timeframes, and separately, the real two-timeframe sample data honestly produces
+  several middle- and lowest-grade zones exactly as it should.
+- **Zones don't yet say whether a price level is acting as "support" or "resistance"** — that
+  depends on which direction price is approaching from and what the live tape says at the moment,
+  which is explicitly the NEXT planned step, not this one.
+- **If a saved price-bar file for a symbol's only timeframe ever becomes corrupted, the system still
+  reports "no price history for this symbol" rather than a more specific "this symbol's data is
+  damaged" message** — unchanged from last iteration; this was a conscious decision to leave alone
+  for now (not something newly discovered), and the existing corruption-detection safeguard still
+  catches and reports the damage separately elsewhere.
+- **The trading strategy, its risk sizing, and honest profit measurement against graded zones remain
+  unbuilt, as planned** — this iteration is purely the "group levels into graded zones" building
+  block those later steps will consume.
+- **No screen in the website to look at zones/grades directly** — machine-only (web API + MCP
+  tool), as planned for this step.
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-3-iteration-summary.md breports/phase-goal-tape_to_profit_support_resistence-iter-3-iteration-summary.md
new file mode 100644
index 0000000..1bbfb5d
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-3-iteration-summary.md
@@ -0,0 +1,73 @@
+# Iteration Summary — goal-tape_to_profit_support_resistence-iter-3
+
+**Verdict:** PASS
+**Iteration type:** goal-full
+**Date:** 2026-07-06
+**Iteration:** 3
+
+## In plain words
+
+**What you can do now:** You can type in a stock ticker and watch Tapeology read live trade-by-trade order flow to see whether buyers or sellers are in control, write trading ideas into a journal, run replay studies, and view honest backtest and profit-and-loss results on a Performance page — all delivered in earlier rounds. The new support-and-resistance work is still being built behind the scenes and isn't ready to try yet.
+
+**What changed this time:** Behind-the-scenes work — nothing visibly new this round. Tapeology now groups its price levels together whenever several different timeframes point to nearly the same price, and grades how convincing each group is on an A, B, or C scale — still only readable by other computer programs right now, not yet shown anywhere on the website.
+
+**What's next:** Next, Tapeology will start turning these graded price zones into an actual trading rule that waits for the live tape to confirm a real entry before acting on them.
+
+## Headline
+
+Support/resistance levels now cluster into confluence zones graded A/B/C by conviction.
+
+## Direction
+
+**Signal:** improving
+**Why:** J-03 (confluence zones + A/B/C conviction classes) was built end-to-end this iteration as an additive `confluence_zones` field inside the existing `research/levels.py` owner — no new endpoint, module, or MCP tool. Review, QA (14/14 test cases), and audit each independently returned PASS with zero regressions (1107 passed / 1 skipped, up from 1095) and the J-07 sentinel intact (fingerprint `4d665603569b9dbf` unmoved). The formal goal-evaluator pass and journey-history update are still pending at write time, but every gate that has run this iteration agrees J-03 is genuinely done, extending three straight iterations (J-01 → J-02 → J-03) of forward journey progress.
+
+**Trend (last 4 iters):**
+- Newly passing this iter: J-03
+- Newly passing in last 4 iters total: J-01, J-02, J-03
+- Regressions in last 4 iters: none
+- Anti-goal violations in last 4 iters: none
+- Iters with no journey state change: 1 of last 4
+
+**Latest evaluator reasoning:** J-03 built end to end. Additive to existing research/levels.py (no new endpoint/module/tool). Full backend suite 1107 passed / 1 skipped / 0 failed (up from 1096). J-07 sentinel intact (fingerprint 4d665603569b9dbf unmoved; 3 new sr_confluence_* fields excluded); empty frontend diff.
+
+## What was done
+
+- Built deterministic confluence clustering (`_cluster_levels`, anchor-fixed scan) and A/B/C grading (`_grade_zone`, by distinct-timeframe breadth plus a required long-term member) inside `research/levels.py` — no new module, endpoint, or MCP tool
+- Wired the new `compute_confluence_zones` entry point into `compute_levels`'s return dict as an additive `confluence_zones` field, served verbatim by the existing `GET /research/levels` route and MCP `levels` proxy
+- Added 3 new config-owned fields (`sr_confluence_band_bps`, `sr_confluence_class_a_min_timeframes`, `sr_confluence_class_b_min_timeframes`), all excluded from `config_fingerprint()` — pinned `default` fingerprint `4d665603569b9dbf` unchanged
+- Added 12 new tests (11 in `test_levels.py`, 1 in `test_levels_api.py`) covering clustering, timeframe-weighted scoring, A/B/C grading, anchor-fixed behavior, byte-identical determinism, no-lookahead, and honest empty-zone states
+- Full backend suite: 1107 passed / 1 skipped / 0 failed (up from 1095), zero regressions; J-07 sentinel intact (equivalence suites green); confirmed empty `apps/frontend/` diff
+- Browser QA correctly SKIPPED (backend-only, no frontend surface); review PASS, QA PASS (14/14 test cases), audit PASS (3 OBSERVATION-only findings, no fixes needed), closure CLOSURE-PASS
+
+## What's left
+
+- Journey J-04 (Tape-confirmed structure entries as a registered strategy) failing — no `structure_tape` strategy or strategy registry exists yet; `GET /research/strategies` still 404s (grep-confirmed)
+- Journey J-05 (Class-scaled stop, reward, and simulated size) failing — depends on J-04's unbuilt strategy registry
+- Journey J-06 (`structure_tape` measured honestly against the v1 champion) failing — no named-strategy edge-report/sweep path yet
+- No screen in the website to view confluence zones yet — machine-only surface (REST + MCP) by design
+- Confluence band tolerance and A/B/C timeframe thresholds are documented starting-point defaults, not yet validated against real trading outcomes
+- The committed real PG fixture can never produce a class A zone on its own (only 2 of the required 3 timeframes) — an honest, documented data-breadth limitation, not a defect
+- Corrupt-sole-series seam at `GET /research/levels` still aliases to `no_bar_series_for_symbol` rather than a distinct integrity state — a deliberate, documented scope decision carried from iter-2
+
+## Next step
+
+Iter-4 builds J-04 — tape-confirmed structure entries as a registered `structure_tape` strategy, arming where price enters a J-03 confluence zone's proximity band and the tape confirms direction (rejection or breakthrough), reusing the engine's existing level-cross + state-native arming machinery. This is the natural dependency successor now that J-03's graded zones exist for it to consume.
+
+## Artifacts
+
+| Report | Verdict | Path |
+|--------|---------|------|
+| Iter spec | — | docs/phases/goal-tape_to_profit_support_resistence-iter-3.md |
+| Dev handoff | — | docs/handoffs/goal-tape_to_profit_support_resistence-iter-3-dev.md |
+| Review | PASS | reports/reviews/goal-tape_to_profit_support_resistence-iter-3-review.md |
+| Browser QA | SKIPPED | reports/phase-goal-tape_to_profit_support_resistence-iter-3-ui-test-results.md |
+| Implementation summary | — | reports/phase-goal-tape_to_profit_support_resistence-iter-3-implementation-summary.md |
+| User-visible changes | — | reports/phase-goal-tape_to_profit_support_resistence-iter-3-user-visible-changes.md |
+| What to click | — | reports/phase-goal-tape_to_profit_support_resistence-iter-3-what-to-click.md |
+| UI surface map | — | reports/phase-goal-tape_to_profit_support_resistence-iter-3-ui-surface-map.md |
+| UI test plan | — | reports/phase-goal-tape_to_profit_support_resistence-iter-3-ui-test-plan.md |
+| QA | PASS | reports/qa/goal-tape_to_profit_support_resistence-iter-3-qa.md |
+| Audit | PASS | docs/handoffs/goal-tape_to_profit_support_resistence-iter-3-audit.md |
+| Closure | CLOSURE-PASS | reports/phase-goal-tape_to_profit_support_resistence-iter-3-closure-verdict.md |
+| Journey history | — | runs/goal-session-tape_to_profit_support_resistence/state/journey-history.json |
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-3-summary.html breports/phase-goal-tape_to_profit_support_resistence-iter-3-summary.html
new file mode 100644
index 0000000..de9a199
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-3-summary.html
@@ -0,0 +1,358 @@
+<!doctype html>
+<html lang="en"><head>
+<meta charset="utf-8">
+<title>goal-tape_to_profit_support_resistence-iter-3 — Iteration Summary</title>
+<style>
+*, *::before, *::after { box-sizing: border-box; }
+body {
+  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
+  margin: 0; padding: 0; color: #1f2328; background: #f6f8fa; line-height: 1.5;
+}
+.container { max-width: 880px; margin: 0 auto; padding: 24px 16px 80px; }
+.hero {
+  background: white; border: 1px solid #d0d7de; border-radius: 8px;
+  padding: 28px; margin-bottom: 16px; text-align: center;
+}
+.hero.pass { border-top: 6px solid #1a7f37; }
+.hero.fail { border-top: 6px solid #cf222e; }
+.hero.inprogress { border-top: 6px solid #d4a72c; }
+.hero h1 { margin: 0 0 6px 0; font-size: 1.6rem; }
+.hero h2 { margin: 0 0 14px 0; font-size: 1rem; color: #57606a; font-weight: 500; }
+.badge-row { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin-bottom: 10px; }
+.badge {
+  display: inline-flex; align-items: center; gap: 8px;
+  padding: 6px 14px; border-radius: 999px; font-weight: 600; font-size: 0.95rem;
+}
+.badge.pass { background: #dafbe1; color: #1a7f37; }
+.badge.fail { background: #ffebe9; color: #cf222e; }
+.badge.inprogress { background: #fff8c5; color: #9a6700; }
+.signal-badge { padding: 6px 14px; border-radius: 999px; font-weight: 600; font-size: 0.9rem; }
+.signal-badge.improving { background: #dafbe1; color: #1a7f37; }
+.signal-badge.holding { background: #ddf4ff; color: #0969da; }
+.signal-badge.stalling { background: #fff8c5; color: #9a6700; }
+.signal-badge.regressing { background: #ffebe9; color: #cf222e; }
+.signal-badge.na { background: #f6f8fa; color: #57606a; }
+.meta { color: #57606a; font-size: 0.875rem; margin: 10px 0 16px; }
+.journey-row {
+  display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin: 12px 0 4px;
+}
+.journey-pill {
+  display: inline-flex; align-items: center; gap: 6px;
+  padding: 4px 10px; border-radius: 999px; font-size: 0.85rem;
+  background: #f6f8fa; border: 1px solid #d0d7de;
+}
+.journey-pill.passing, .journey-pill.already_passing { background: #dafbe1; color: #1a7f37; border-color: #b4e2c0; }
+.journey-pill.failing, .journey-pill.regressed { background: #ffebe9; color: #cf222e; border-color: #f1aeb0; }
+.journey-pill.partial { background: #fff8c5; color: #9a6700; border-color: #eed888; }
+.journey-pill.unknown { background: #f6f8fa; color: #57606a; }
+.hero-image { margin-top: 18px; }
+.hero-image img { max-width: 100%; height: auto; border-radius: 6px; border: 1px solid #d0d7de; }
+details {
+  background: white; border: 1px solid #d0d7de; border-radius: 8px;
+  margin-bottom: 12px;
+}
+details > summary {
+  cursor: pointer; padding: 14px 18px; font-weight: 600; font-size: 1.05rem;
+  list-style: none; user-select: none; display: flex; align-items: center; gap: 8px;
+}
+details > summary::-webkit-details-marker { display: none; }
+details > summary::before {
+  content: '▶'; transition: transform 0.15s; font-size: 0.75rem; color: #57606a;
+}
+details[open] > summary::before { transform: rotate(90deg); }
+.accordion-body { padding: 0 18px 18px; }
+.accordion-body h3 { font-size: 0.95rem; color: #57606a; margin: 16px 0 6px; }
+.why-text { background: #f6f8fa; padding: 10px 12px; border-radius: 6px; margin: 4px 0 12px; }
+ul.bullets { margin: 6px 0 14px; padding-left: 22px; }
+ul.bullets li { margin-bottom: 4px; }
+ol.steps { padding-left: 0; list-style: none; counter-reset: step; }
+ol.steps > li {
+  counter-increment: step; padding: 12px 0 12px 44px;
+  border-top: 1px solid #eaeef2; position: relative;
+}
+ol.steps > li:first-child { border-top: none; }
+ol.steps > li::before {
+  content: counter(step); position: absolute; left: 0; top: 14px;
+  width: 30px; height: 30px; border-radius: 50%;
+  background: #0969da; color: white; display: flex;
+  align-items: center; justify-content: center; font-size: 0.85rem; font-weight: 600;
+}
+.step-shot { margin-top: 10px; }
+.step-shot img { max-width: 100%; height: auto; border-radius: 6px; border: 1px solid #d0d7de; }
+.next-step-box {
+  background: #ddf4ff; padding: 12px 16px; border-radius: 6px;
+  border-left: 4px solid #0969da; margin: 12px 0;
+}
+.drill-table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
+.drill-table th, .drill-table td {
+  text-align: left; padding: 8px 6px; border-bottom: 1px solid #eaeef2;
+}
+.drill-table th { background: #f6f8fa; }
+.verdict-cell.PASS, .verdict-cell.CLOSURE-PASS, .verdict-cell.GOAL_ACHIEVED { color: #1a7f37; font-weight: 600; }
+.verdict-cell.FAIL, .verdict-cell.CLOSURE-FAIL, .verdict-cell.REGRESSION { color: #cf222e; font-weight: 600; }
+.verdict-cell.CONTINUE, .verdict-cell.ESCALATE, .verdict-cell.STALLED { color: #9a6700; font-weight: 600; }
+.verdict-cell.SKIPPED, .verdict-cell.UNKNOWN, .verdict-cell.IN-PROGRESS { color: #57606a; }
+.footer-note { text-align: center; color: #6e7781; font-size: 0.8rem; margin-top: 24px; }
+.iter-card {
+  background: white; border: 1px solid #d0d7de; border-radius: 8px;
+  padding: 16px 18px; margin-bottom: 12px; display: flex; align-items: center; gap: 14px;
+}
+.iter-card .left { flex-shrink: 0; }
+.iter-card .body { flex: 1 1 auto; }
+.iter-card .body .title { font-weight: 600; }
+.iter-card .body .sub { color: #57606a; font-size: 0.88rem; margin-top: 2px; }
+.iter-card a.open { color: #0969da; text-decoration: none; font-weight: 500; }
+.iter-card a.open:hover { text-decoration: underline; }
+.matrix { width: 100%; border-collapse: collapse; margin: 12px 0 22px; font-size: 0.88rem; }
+.matrix th, .matrix td { padding: 6px 8px; border: 1px solid #d0d7de; text-align: center; }
+.matrix th:first-child, .matrix td:first-child { text-align: left; }
+.matrix .cell-passing, .matrix .cell-already_passing { background: #dafbe1; color: #1a7f37; }
+.matrix .cell-failing, .matrix .cell-regressed { background: #ffebe9; color: #cf222e; }
+.matrix .cell-partial { background: #fff8c5; color: #9a6700; }
+.matrix .cell-unknown { background: #f6f8fa; color: #57606a; }
+.no-summary {
+  background: #fff8c5; border: 1px solid #eed888; padding: 14px 18px;
+  border-radius: 8px; color: #9a6700; margin-bottom: 14px;
+}
+/* Plain-language layer — the primary, non-technical view. */
+.plain-words {
+  background: linear-gradient(180deg, #ffffff 0%, #f6fbff 100%);
+  border: 1px solid #d6e4f0; border-radius: 10px;
+  padding: 22px 24px; margin: 18px 0 6px;
+  box-shadow: 0 1px 2px rgba(20, 40, 80, 0.04);
+}
+.plain-words .pw-heading {
+  margin: 0 0 14px; font-size: 1.15rem; color: #0969da;
+  text-transform: uppercase; letter-spacing: 0.05em;
+}
+.pw-grid {
+  display: grid; gap: 14px;
+  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
+}
+.pw-card {
+  background: white; border-radius: 8px; padding: 14px 16px;
+  border: 1px solid #e3eaf3;
+}
+.pw-card .pw-label {
+  font-size: 0.78rem; font-weight: 600; color: #57606a;
+  text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 6px;
+}
+.pw-card .pw-text {
+  margin: 0; font-size: 1rem; color: #1f2328; line-height: 1.45;
+}
+.pw-empty { color: #8c959f; font-style: italic; font-size: 0.95rem; }
+.tech-divider {
+  margin: 18px 0 8px; text-align: center;
+  color: #6e7781; font-size: 0.82rem; font-style: italic;
+  border-top: 1px dashed #d0d7de; padding-top: 12px;
+}
+/* Watch-it-work — narrated screenshot gallery from demo-narrator. */
+.watch-it-work {
+  background: white; border: 1px solid #d6e4f0; border-radius: 10px;
+  padding: 18px 22px; margin: 10px 0 6px;
+}
+.wiw-head {
+  display: flex; align-items: center; justify-content: space-between;
+  gap: 12px; margin-bottom: 14px; flex-wrap: wrap;
+}
+.wiw-heading {
+  margin: 0; font-size: 1.05rem; color: #0969da;
+  text-transform: uppercase; letter-spacing: 0.05em;
+}
+.demo-badge {
+  font-size: 0.75rem; font-weight: 600; padding: 4px 10px; border-radius: 12px;
+  border: 1px solid transparent; letter-spacing: 0.04em;
+}
+.demo-badge.demo-recorded { background: #dafbe1; color: #1a7f37; border-color: #aceebb; }
+.demo-badge.demo-notes    { background: #fff8c5; color: #9a6700; border-color: #e8d97e; }
+.demo-badge.demo-skipped  { background: #f6f8fa; color: #57606a; border-color: #d0d7de; }
+.demo-badge.demo-pending  { background: #ddf4ff; color: #0969da; border-color: #b6e3ff; }
+.demo-grid {
+  display: grid; gap: 14px;
+  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
+}
+.demo-step {
+  margin: 0; padding: 12px; background: #f6f8fa;
+  border: 1px solid #d0d7de; border-radius: 8px;
+}
+.demo-step-head {
+  display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
+  font-size: 0.9rem;
+}
+.demo-step-num {
+  font-weight: 600; color: #57606a; font-variant-numeric: tabular-nums;
+}
+.demo-step-title { color: #1f2328; font-weight: 500; }
+.demo-new {
+  background: #ddf4ff; color: #0969da; font-size: 0.7rem; font-weight: 700;
+  padding: 2px 6px; border-radius: 4px; letter-spacing: 0.06em;
+}
+.demo-shot { margin-bottom: 8px; }
+.demo-shot img {
+  width: 100%; height: auto; border-radius: 4px; border: 1px solid #d0d7de;
+  display: block;
+}
+.demo-narration {
+  margin: 0; color: #1f2328; font-size: 0.92rem; line-height: 1.4;
+}
+.demo-empty {
+  margin: 8px 0 0; color: #57606a; font-style: italic;
+  white-space: pre-wrap; overflow-wrap: anywhere;
+}
+.demo-notes-wrap { margin-top: 14px; }
+.demo-notes-wrap summary {
+  cursor: pointer; color: #9a6700; font-weight: 500; font-size: 0.9rem;
+}
+.demo-notes-wrap[open] summary { margin-bottom: 6px; }
+/* Story so far + latest demo (session index plain-language top). */
+.story-so-far {
+  background: linear-gradient(180deg, #ffffff 0%, #f6fbff 100%);
+  border: 1px solid #d6e4f0; border-radius: 10px;
+  padding: 22px 26px; margin: 14px 0 6px;
+  box-shadow: 0 1px 2px rgba(20, 40, 80, 0.04);
+}
+.story-heading {
+  margin: 0 0 12px; font-size: 1.1rem; color: #0969da;
+  text-transform: uppercase; letter-spacing: 0.05em;
+}
+.story-body { font-size: 1rem; color: #1f2328; line-height: 1.55; }
+.story-body .story-h { margin: 14px 0 6px; color: #1f2328; }
+.story-body p { margin: 0 0 10px; }
+.session-demo {
+  background: white; border: 1px solid #d6e4f0; border-radius: 10px;
+  padding: 0; margin: 8px 0 6px; overflow: hidden;
+}
+.session-demo-head {
+  display: flex; align-items: center; justify-content: space-between;
+  gap: 10px; padding: 12px 22px;
+  background: #f6f8fa; border-bottom: 1px solid #d6e4f0;
+  font-weight: 600; color: #1f2328; font-size: 0.95rem;
+}
+.session-demo-head a.open { color: #0969da; text-decoration: none; font-weight: 500; font-size: 0.9rem; }
+.session-demo-head a.open:hover { text-decoration: underline; }
+.session-demo .watch-it-work {
+  border: none; border-radius: 0; box-shadow: none; margin: 0;
+}
+/* Delivered link banner — sits on the session index when GOAL_ACHIEVED. */
+.delivered-link {
+  margin: 14px 0; padding: 14px 22px;
+  background: #dafbe1; border: 1px solid #aceebb; border-radius: 10px;
+  color: #1a7f37; font-size: 1rem;
+}
+.delivered-link a {
+  color: #1a7f37; font-weight: 600; text-decoration: none; margin-left: 8px;
+}
+.delivered-link a:hover { text-decoration: underline; }
+.delivered-back {
+  margin: 8px 0 14px; padding: 0; font-size: 0.9rem;
+}
+.delivered-back a { color: #0969da; text-decoration: none; }
+.delivered-back a:hover { text-decoration: underline; }
+.delivered-body {
+  background: white; border: 1px solid #d6e4f0; border-radius: 10px;
+  padding: 22px 28px; margin: 12px 0;
+}
+.delivered-body h2.story-h { margin-top: 0; }
+/* Feature manual (session index, top of page). */
+.cover-vision {
+  margin: 8px 0 14px; color: #57606a; font-size: 1.02rem;
+  font-style: italic; max-width: 60ch;
+}
+.feature-toc {
+  background: white; border: 1px solid #d6e4f0; border-radius: 10px;
+  padding: 20px 26px; margin: 14px 0;
+  box-shadow: 0 1px 2px rgba(20, 40, 80, 0.04);
+}
+.feature-toc-heading {
+  margin: 0 0 14px; font-size: 1.05rem; color: #0969da;
+  text-transform: uppercase; letter-spacing: 0.05em;
+}
+.feature-toc-list {
+  margin: 0; padding-left: 22px; font-size: 1rem; line-height: 1.7;
+}
+.feature-toc-list li { padding: 2px 0; }
+.feature-toc-list a {
+  color: #1f2328; text-decoration: none; font-weight: 500;
+}
+.feature-toc-list a:hover { color: #0969da; text-decoration: underline; }
+.toc-extra-header {
+  list-style: none; margin: 10px 0 4px -22px;
+  font-size: 0.82rem; color: #57606a; font-weight: 600;
+  text-transform: uppercase; letter-spacing: 0.04em;
+}
+.feature-manual { margin: 14px 0; }
+.feature-section {
+  background: white; border: 1px solid #d6e4f0; border-radius: 10px;
+  padding: 22px 26px; margin: 16px 0;
+  box-shadow: 0 1px 2px rgba(20, 40, 80, 0.04);
+  scroll-margin-top: 12px;
+}
+.feature-heading {
+  margin: 0 0 10px; font-size: 1.2rem; color: #1f2328;
+  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
+}
+.feature-description {
+  margin: 0 0 16px; color: #1f2328; font-size: 1rem; line-height: 1.55;
+}
+.feature-description-label {
+  font-weight: 600; color: #57606a; margin-right: 4px;
+}
+.feature-note {
+  margin: 8px 0 12px; padding: 8px 12px;
+  background: #fff8c5; border: 1px solid #eed888; border-radius: 6px;
+  color: #9a6700; font-size: 0.88rem;
+}
+.feature-source {
+  margin: 12px 0 0; font-size: 0.88rem; color: #57606a;
+}
+.feature-source a { color: #0969da; text-decoration: none; }
+.feature-source a:hover { text-decoration: underline; }
+.feature-empty {
+  margin: 10px 0; padding: 12px 16px;
+  background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px;
+  color: #57606a; font-style: italic;
+}
+.status-pill {
+  font-size: 0.78rem; font-weight: 600; padding: 3px 10px; border-radius: 12px;
+  letter-spacing: 0.04em; white-space: nowrap; display: inline-block;
+}
+.status-pill-passing { background: #dafbe1; color: #1a7f37; border: 1px solid #aceebb; }
+.status-pill-failing { background: #ffebe9; color: #cf222e; border: 1px solid #f2b8b5; }
+.status-pill-regressed { background: #ffebe9; color: #cf222e; border: 1px solid #f2b8b5; }
+.status-pill-partial { background: #fff8c5; color: #9a6700; border: 1px solid #e8d97e; }
+.status-pill-unknown { background: #f6f8fa; color: #57606a; border: 1px solid #d0d7de; }
+.status-pill-coming-soon { background: #f6f8fa; color: #57606a; border: 1px solid #d0d7de; }
+.developer-view {
+  margin: 28px 0 6px;
+  border: 1px dashed #d0d7de; border-radius: 8px;
+}
+.developer-view > summary {
+  cursor: pointer; padding: 12px 16px;
+  color: #57606a; font-size: 0.92rem; font-weight: 500;
+  background: #f6f8fa; border-radius: 8px;
+}
+.developer-view[open] > summary {
+  border-bottom: 1px dashed #d0d7de;
+  border-radius: 8px 8px 0 0;
+}
+.developer-view-body { padding: 12px 18px; }
+</style>
+</head><body><div class='container'>
+<section class='hero pass'><div class='badge-row'><div class='badge pass'><svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
+<circle cx="12" cy="12" r="11" fill="#1a7f37"/>
+<path d="M7 12.5l3 3 7-7" stroke="white" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
+</svg><span>PASS</span></div><span class='signal-badge improving'>Direction: improving</span></div><h1>Iteration 3  ·  session tape_to_profit_support_resistence</h1><h2>Support/resistance levels now cluster into confluence zones graded A/B/C by conviction.</h2><div class='meta'>2026-07-06 · goal-full</div><div class='meta'>Journeys: 3/7 passing</div><div class='journey-row'><span class='journey-pill passing' title='Multi-timeframe historical bars are ingested and persisted (data foundation + free-plan probe)'>J-01 · passing</span><span class='journey-pill passing' title='Deterministic support/resistance levels per timeframe'>J-02 · passing</span><span class='journey-pill failing' title='Confluence zones and A/B/C conviction classes'>J-03 · failing</span><span class='journey-pill failing' title='Tape-confirmed structure entries as a registered strategy'>J-04 · failing</span><span class='journey-pill failing' title='Class-scaled stop, reward, and simulated size'>J-05 · failing</span><span class='journey-pill failing' title='structure_tape is measured honestly against the v1 champion'>J-06 · failing</span><span class='journey-pill already_passing' title='The archived eras are unchanged (regression sentinel)'>J-07 · already_passing</span></div></section>
+<section class='plain-words'><h2 class='pw-heading'>In plain words</h2><div class='pw-grid'><div class='pw-card'><div class='pw-label'>What you can do now</div><p class='pw-text'>You can type in a stock ticker and watch Tapeology read live trade-by-trade order flow to see whether buyers or sellers are in control, write trading ideas into a journal, run replay studies, and view honest backtest and profit-and-loss results on a Performance page — all delivered in earlier rounds. The new support-and-resistance work is still being built behind the scenes and isn&#x27;t ready to try yet.</p></div><div class='pw-card'><div class='pw-label'>What changed this time</div><p class='pw-text'>Behind-the-scenes work — nothing visibly new this round. Tapeology now groups its price levels together whenever several different timeframes point to nearly the same price, and grades how convincing each group is on an A, B, or C scale — still only readable by other computer programs right now, not yet shown anywhere on the website.</p></div><div class='pw-card'><div class='pw-label'>What&#x27;s next</div><p class='pw-text'>Next, Tapeology will start turning these graded price zones into an actual trading rule that waits for the live tape to confirm a real entry before acting on them.</p></div></div></section>
+<div class='tech-divider'><span>Technical detail below — open if you want the developer view.</span></div>
+<details><summary>What was done</summary><div class='accordion-body'><ul class='bullets'><li>Built deterministic confluence clustering (`_cluster_levels`, anchor-fixed scan) and A/B/C grading (`_grade_zone`, by distinct-timeframe breadth plus a required long-term member) inside `research/levels.py` — no new module, endpoint, or MCP tool</li><li>Wired the new `compute_confluence_zones` entry point into `compute_levels`&#x27;s return dict as an additive `confluence_zones` field, served verbatim by the existing `GET /research/levels` route and MCP `levels` proxy</li><li>Added 3 new config-owned fields (`sr_confluence_band_bps`, `sr_confluence_class_a_min_timeframes`, `sr_confluence_class_b_min_timeframes`), all excluded from `config_fingerprint()` — pinned `default` fingerprint `4d665603569b9dbf` unchanged</li><li>Added 12 new tests (11 in `test_levels.py`, 1 in `test_levels_api.py`) covering clustering, timeframe-weighted scoring, A/B/C grading, anchor-fixed behavior, byte-identical determinism, no-lookahead, and honest empty-zone states</li><li>Full backend suite: 1107 passed / 1 skipped / 0 failed (up from 1095), zero regressions; J-07 sentinel intact (equivalence suites green); confirmed empty `apps/frontend/` diff</li><li>Browser QA correctly SKIPPED (backend-only, no frontend surface); review PASS, QA PASS (14/14 test cases), audit PASS (3 OBSERVATION-only findings, no fixes needed), closure CLOSURE-PASS</li></ul></div></details>
+<details><summary>What's left + Next step</summary><div class='accordion-body'><h3>Still open</h3><ul class='bullets'><li>Journey J-04 (Tape-confirmed structure entries as a registered strategy) failing — no `structure_tape` strategy or strategy registry exists yet; `GET /research/strategies` still 404s (grep-confirmed)</li><li>Journey J-05 (Class-scaled stop, reward, and simulated size) failing — depends on J-04&#x27;s unbuilt strategy registry</li><li>Journey J-06 (`structure_tape` measured honestly against the v1 champion) failing — no named-strategy edge-report/sweep path yet</li><li>No screen in the website to view confluence zones yet — machine-only surface (REST + MCP) by design</li><li>Confluence band tolerance and A/B/C timeframe thresholds are documented starting-point defaults, not yet validated against real trading outcomes</li><li>The committed real PG fixture can never produce a class A zone on its own (only 2 of the required 3 timeframes) — an honest, documented data-breadth limitation, not a defect</li><li>Corrupt-sole-series seam at `GET /research/levels` still aliases to `no_bar_series_for_symbol` rather than a distinct integrity state — a deliberate, documented scope decision carried from iter-2</li></ul><h3>Next step</h3><div class='next-step-box'>Iter-4 builds J-04 — tape-confirmed structure entries as a registered `structure_tape` strategy, arming where price enters a J-03 confluence zone&#x27;s proximity band and the tape confirms direction (rejection or breakthrough), reusing the engine&#x27;s existing level-cross + state-native arming machinery. This is the natural dependency successor now that J-03&#x27;s graded zones exist for it to consume.</div></div></details>
+<details><summary>Direction signal</summary><div class='accordion-body'><div class='why-text'><strong>Why:</strong> J-03 (confluence zones + A/B/C conviction classes) was built end-to-end this iteration as an additive `confluence_zones` field inside the existing `research/levels.py` owner — no new endpoint, module, or MCP tool. Review, QA (14/14 test cases), and audit each independently returned PASS with zero regressions (1107 passed / 1 skipped, up from 1095) and the J-07 sentinel intact (fingerprint `4d665603569b9dbf` unmoved). The formal goal-evaluator pass and journey-history update are still pending at write time, but every gate that has run this iteration agrees J-03 is genuinely done, extending three straight iterations (J-01 → J-02 → J-03) of forward journey progress.</div><h3>Trend</h3><ul class='bullets'><li>Newly passing this iter: J-03</li><li>Newly passing in last 4 iters total: J-01, J-02, J-03</li><li>Regressions in last 4 iters: none</li><li>Anti-goal violations in last 4 iters: none</li><li>Iters with no journey state change: 1 of last 4</li></ul><h3>Latest evaluator reasoning</h3><div class='why-text'>J-03 built end to end. Additive to existing research/levels.py (no new endpoint/module/tool). Full backend suite 1107 passed / 1 skipped / 0 failed (up from 1096). J-07 sentinel intact (fingerprint 4d665603569b9dbf unmoved; 3 new sr_confluence_* fields excluded); empty frontend diff.</div></div></details>
+<details><summary>Artifacts</summary><div class='accordion-body'><table class='drill-table'><thead><tr><th>Report</th><th>Verdict</th><th>Path</th></tr></thead><tbody><tr><td>Iter spec</td><td><span class='verdict-cell —'>—</span></td><td><a href='../docs/phases/goal-tape_to_profit_support_resistence-iter-3.md'>docs/phases/goal-tape_to_profit_support_resistence-iter-3.md</a></td></tr><tr><td>Dev handoff</td><td><span class='verdict-cell —'>—</span></td><td><a href='../docs/handoffs/goal-tape_to_profit_support_resistence-iter-3-dev.md'>docs/handoffs/goal-tape_to_profit_support_resistence-iter-3-dev.md</a></td></tr><tr><td>Review</td><td><span class='verdict-cell PASS'>PASS</span></td><td><a href='reviews/goal-tape_to_profit_support_resistence-iter-3-review.md'>reports/reviews/goal-tape_to_profit_support_resistence-iter-3-review.md</a></td></tr><tr><td>Browser QA</td><td><span class='verdict-cell SKIPPED'>SKIPPED</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-3-ui-test-results.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-3-ui-test-results.md</a></td></tr><tr><td>Implementation summary</td><td><span class='verdict-cell —'>—</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-3-implementation-summary.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-3-implementation-summary.md</a></td></tr><tr><td>User-visible changes</td><td><span class='verdict-cell —'>—</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-3-user-visible-changes.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-3-user-visible-changes.md</a></td></tr><tr><td>What to click</td><td><span class='verdict-cell —'>—</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-3-what-to-click.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-3-what-to-click.md</a></td></tr><tr><td>UI surface map</td><td><span class='verdict-cell —'>—</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-3-ui-surface-map.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-3-ui-surface-map.md</a></td></tr><tr><td>UI test plan</td><td><span class='verdict-cell —'>—</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-3-ui-test-plan.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-3-ui-test-plan.md</a></td></tr><tr><td>QA</td><td><span class='verdict-cell PASS'>PASS</span></td><td><a href='qa/goal-tape_to_profit_support_resistence-iter-3-qa.md'>reports/qa/goal-tape_to_profit_support_resistence-iter-3-qa.md</a></td></tr><tr><td>Audit</td><td><span class='verdict-cell PASS'>PASS</span></td><td><a href='../docs/handoffs/goal-tape_to_profit_support_resistence-iter-3-audit.md'>docs/handoffs/goal-tape_to_profit_support_resistence-iter-3-audit.md</a></td></tr><tr><td>Closure</td><td><span class='verdict-cell CLOSURE-PASS'>CLOSURE-PASS</span></td><td><a href='phase-goal-tape_to_profit_support_resistence-iter-3-closure-verdict.md'>reports/phase-goal-tape_to_profit_support_resistence-iter-3-closure-verdict.md</a></td></tr><tr><td>Journey history</td><td><span class='verdict-cell —'>—</span></td><td><a href='../runs/goal-session-tape_to_profit_support_resistence/state/journey-history.json'>runs/goal-session-tape_to_profit_support_resistence/state/journey-history.json</a></td></tr></tbody></table></div></details>
+<details><summary>Timing — where this iteration's wall time went</summary><div class='accordion-body'><pre>== Wall-time report: session tape_to_profit_support_resistence
+  goal-tape_to_profit_support_resistence-iter-3  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
+      iteration-summarizer         8.9m  calls=1
+      goal-decomposer              8.9m  calls=1
+      readme-maintainer            5.5m  calls=1
+      pump-wait                  3.8m</pre></div></details>
+<div class='footer-note'>Generated 2026-07-06 10:29 by <code>render_iteration_summary.py</code> · source: <a href='phase-goal-tape_to_profit_support_resistence-iter-3-iteration-summary.md'>phase-goal-tape_to_profit_support_resistence-iter-3-iteration-summary.md</a></div>
+</div></body></html>
\ No newline at end of file
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-3-ui-surface-map.md breports/phase-goal-tape_to_profit_support_resistence-iter-3-ui-surface-map.md
new file mode 100644
index 0000000..5a829a7
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-3-ui-surface-map.md
@@ -0,0 +1,5 @@
+# Phase goal-tape_to_profit_support_resistence-iter-3 — UI Surface Map
+
+**Status:** N/A — Backend-only phase (Frontend Present: no)
+
+No UI surfaces affected.
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-3-ui-test-plan.md breports/phase-goal-tape_to_profit_support_resistence-iter-3-ui-test-plan.md
new file mode 100644
index 0000000..aef8790
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-3-ui-test-plan.md
@@ -0,0 +1,3 @@
+# Phase goal-tape_to_profit_support_resistence-iter-3 — UI Test Plan
+
+**Status:** N/A — Backend-only phase. No UI tests required.
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-3-ui-test-results.md breports/phase-goal-tape_to_profit_support_resistence-iter-3-ui-test-results.md
new file mode 100644
index 0000000..7e0471c
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-3-ui-test-results.md
@@ -0,0 +1,5 @@
+# Phase goal-tape_to_profit_support_resistence-iter-3 — UI Test Results
+
+**Browser QA Verdict:** SKIPPED
+
+**Reason:** Backend-only phase (Frontend Present: no). No browser tests executed.
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-3-user-visible-changes.md breports/phase-goal-tape_to_profit_support_resistence-iter-3-user-visible-changes.md
new file mode 100644
index 0000000..8e60a10
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-3-user-visible-changes.md
@@ -0,0 +1,5 @@
+# Phase goal-tape_to_profit_support_resistence-iter-3 — User-Visible Changes
+
+**Status:** N/A — Backend-only phase (Frontend Present: no)
+
+No user-visible changes. All changes are internal backend implementation.
diff --git areports/phase-goal-tape_to_profit_support_resistence-iter-3-what-to-click.md breports/phase-goal-tape_to_profit_support_resistence-iter-3-what-to-click.md
new file mode 100644
index 0000000..53fde8d
--- /dev/null
+++ breports/phase-goal-tape_to_profit_support_resistence-iter-3-what-to-click.md
@@ -0,0 +1,3 @@
+# Phase goal-tape_to_profit_support_resistence-iter-3 — What to Click
+
+**Status:** N/A — Backend-only phase. No UI verification steps.
diff --git areports/qa/goal-tape_to_profit_support_resistence-iter-3-qa.md breports/qa/goal-tape_to_profit_support_resistence-iter-3-qa.md
new file mode 100644
index 0000000..0fe3520
--- /dev/null
+++ breports/qa/goal-tape_to_profit_support_resistence-iter-3-qa.md
@@ -0,0 +1,174 @@
+**Verdict:** PASS
+
+---
+
+## Phase Summary
+
+**Phase:** goal-tape_to_profit_support_resistence-iter-3  
+**Date:** 2026-07-06  
+**Frontend Present:** no
+
+**Capability:** Confluence zones + A/B/C conviction classes. A researcher calling `GET /research/levels` receives, beside the raw support/resistance levels, the confluence zones that cluster those levels across timeframes — each zone carrying its member levels (with timeframes), a timeframe-weighted score, and an honest A/B/C conviction class, computed once, served from one canonical owner, and read verbatim by REST and MCP.
+
+---
+
+## Step 1: Artifact Verification
+
+All required artifacts are present and correct:
+
+- ✓ `docs/handoffs/goal-tape_to_profit_support_resistence-iter-3-dev.md` — EXISTS (complete handoff with design decisions)
+- ✓ `reports/reviews/goal-tape_to_profit_support_resistence-iter-3-review.md` — EXISTS (PASS verdict)
+- ✓ `runs/goal-tape_to_profit_support_resistence-iter-3/status.json` — EXISTS (current_step: browser_qa_complete)
+
+**Verdict:** All required artifacts present.
+
+---
+
+## Step 2: Backend Test Results
+
+Command run: `cd apps/backend && .venv/bin/python -m pytest tests/ -q --junit-xml=/tmp/junit.xml`
+
+**Test Output (exact):**
+
+```
+........................................................................ [  6%]
+........................................................................ [ 12%]
+........................................................................ [ 19%]
+........................................................................ [ 25%]
+........................................................................ [ 32%]
+........................................................................ [ 38%]
+.................................s...................................... [ 45%]
+........................................................................ [ 51%]
+........................................................................ [ 58%]
+........................................................................ [ 64%]
+........................................................................ [ 71%]
+........................................................................ [ 77%]
+........................................................................ [ 84%]
+........................................................................ [ 90%]
+........................................................................ [ 97%]
+............................                                             [100%]
+
+=============================== warnings summary ===============================
+.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
+  apps/backend/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with`starlette.testclient` is deprecated; install `httpx2` instead.
+    from starlette.testclient import TestClient as TestClient  # noqa
+
+tests/test_analytics_api.py::test_endpoint_serves_module_projection_verbatim
+  apps/backend/.venv/lib/python3.14/site-packages/websockets/legacy/__init__.py:6: DeprecationWarning: websockets.legacy is deprecated; see https://websockets.readthedocs.
+readthedocs.org/en/stable/howto/upgrade.html for upgrade instructions
+    warnings.warn(  # deprecated in 14.0 - 2024-11-09
+
+-- Docs: https://docs.pytest.org/en/how-pytest.org/how-pytest.org
+```
+
+**Test Counts:** 1107 passed, 0 failed, 0 errors, 1 skipped, 1108 collected
+
+**Result:** ✓ ALL TESTS PASS — 1107 passed, 1 skipped (pre-existing gated socket test), 0 failures, 0 errors.
+
+Breakdown per the dev handoff:
+- Total backend suite: **1107 passed, 1 skipped** (from 1108 collected)
+- J-07 gate tests (`test_observer_equivalence.py`, `test_profile_equivalence.py`, `test_real_data_gate.py`): **57 passed** (unchanged from prior iterations)
+- Confluence-focused tests (`test_levels.py`, `test_levels_api.py`, `test_mcp_server.py`): **57 passed** (26 + 10 + 21)
+- New tests this iteration: **+12** (11 in `test_levels.py`, 1 in `test_levels_api.py`)
+- Regressions: **0**
+
+---
+
+## Step 3: Functional Test Plan Execution
+
+Test plan: `reports/qa/goal-tape_to_profit_support_resistence-iter-3-test-plan.md` (14 test cases total)
+
+### Functional Test Results Table
+
+| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
+|---------|------|------|----------|--------|---------|-------|
+| TC-01 | Levels within confluence band cluster | api | Single zone with 2+ members | Clustering test PASSED | PASS | Anchor-fixed clustering verified in test suite |
+| TC-02 | Levels outside confluence band do not join | api | Separate zones for out-of-band levels | Out-of-band exclusion verified | PASS | Band tolerance enforced; levels >20 bps apart remain separate |
+| TC-03 | Zone score is timeframe-weighted sum | api | Exact numeric match | Timeframe-weighted scoring verified | PASS | Zone score = Σ(member.strength) where member.strength already weighted by timeframe |
+| TC-04 | A/B/C grading: class A when criteria met | api | Exact class label "A" | 3+ distinct timeframes + long-term member → class A | PASS | Direct unit test `test_confluence_class_a_requires_a_long_term_member_not_just_timeframe_count` |
+| TC-05 | Honest B/C grading when criteria not met | api | Honest B or C labels, no fabrication | Real PG fixture (2 timeframes) produces honest B/C | PASS | 5 of 6 real zones are C-grade (same-timeframe), 1 is B-grade; never fabricated A |
+| TC-06 | Byte-identical deterministic re-runs | api | Identical JSON hashes; stable order | Zones sorted by `_zone_sort_key` (price, then member count) | PASS | Explicit total order for byte-identical served JSON |
+| TC-07 | No-lookahead for zones/classes | api | Zones at T unchanged when later bars added | Physical truncation test verifies no-lookahead | PASS | `compute_confluence_zones` is a pure function of already-truncated `levels` list |
+| TC-08 | MCP levels tool byte-identical to REST | api | JSON hashes match; single source of truth | MCP is byte-for-byte proxy of REST response | PASS | No dispatch-logic change; routes.py spreads `compute_levels` dict verbatim with `**result` |
+| TC-09 | No-magic-numbers: all thresholds in Config | artifact | Zero hardcoded numeric thresholds in levels.py | grep-confirmed zero hardcoded threshold literals | PASS | All 3 new config fields (`sr_confluence_band_bps`, `sr_confluence_class_a_min_timeframes`, `sr_confluence_class_b_min_timeframes`) owned by Config |
+| TC-10 | Config fingerprint unchanged; new fields excluded | api | Fingerprint == 4d665603569b9dbf; new fields in excluded set | Fingerprint pinned: 4d665603569b9dbf; fields excluded | PASS | All 3 new confluence fields in `excluded` set per `config_fingerprint()`; same pattern as existing `sr_*` fields |
+| TC-11 | Honest empty zones: no_bar_series_for_symbol | api | `no_bar_series_for_symbol: true`, `confluence_zones: []` | Honest empty state returned for missing symbol | PASS | Three separate honest-state tests assert empty `confluence_zones` list (never null, never fabricated) |
+| TC-12 | Honest empty zones: levels but no cluster | api | Non-empty `levels`, empty `confluence_zones` | Distinction maintained: levels present but no 2+ member cluster | PASS | Only 2+ member clusters returned; lone levels silently dropped (never fabricated 1-member zones) |
+| TC-13 | Frontend files unchanged (zero diff) | artifact | `git diff apps/frontend/` empty; exit code 0 | No changes to any frontend file | PASS | Confirmed via `git diff HEAD -- apps/frontend/` (no output); backend-only iteration |
+| TC-14 | Grep-guard: no J-04 code (`structure_tape`) | artifact | Zero matches in active code for `structure_tape` | grep-confirmed zero active-code matches | PASS | J-04–J-06 remain unbuilt; no second computation path introduced |
+
+**Summary:** 14/14 test cases PASSED
+
+---
+
+## Step 4: Browser Checks
+
+**Status:** SKIPPED — backend-only phase
+
+Frontend Present: no. No browser checks required per phase spec (Machine-only REST + MCP, as scoped).
+
+---
+
+## Step 5: UI Evolution Audit
+
+**Status:** SKIPPED — backend-only phase
+
+No UI/frontend surface in this iteration. Per spec: "No frontend/UI surface — machine-only (REST + MCP), as scoped; no page, panel, or nav change." Confirmed via `git diff -- apps/frontend/` (empty).
+
+---
+
+## Step 6: Code Quality Verification
+
+### Spec Alignment
+- ✓ Definition of Done: **COMPLETE** (all acceptance criteria met)
+- ✓ Scope: **NO CREEP** (J-04–J-06 remain unbuilt, grep-confirmed)
+- ✓ Architecture: **ADHERES** (single-owner pattern; confluence is additive field on existing `compute_levels`, no new module/route/MCP tool)
+
+### Implementation Quality (per review PASS verdict)
+- ✓ **Deterministic, lookahead-free clustering + A/B/C classification** — implemented inside existing `research/levels.py` (the registered Data-Contract-Row-39 owner)
+- ✓ **Additive field on `compute_levels`'s return dict** — served verbatim by existing `GET /research/levels` route and MCP `levels` proxy
+- ✓ **Honest labelling** — class A only when config criteria are met; B/C otherwise; never fabricated
+- ✓ **Config-owned confluence parameters** — `sr_confluence_band_bps`, `sr_confluence_class_a_min_timeframes`, `sr_confluence_class_b_min_timeframes`, all excluded from `config_fingerprint()` fingerprint (pinned at `4d665603569b9dbf`)
+- ✓ **No second computation path** — grep-confirmed no `structure_tape`, `research/strategies`, or J-04 scaffold
+- ✓ **Frontend unchanged** — `git diff -- apps/frontend/` empty
+- ✓ **Corrupt-sole-series seam decision** — documented in dev handoff: unchanged from iter-2 (J-02), still aliased to `no_bar_series_for_symbol: true` with empty `confluence_zones` list
+
+### Test Coverage
+- ✓ **New tests:** 12 added (11 in `test_levels.py`, 1 in `test_levels_api.py`)
+- ✓ **Regressions:** 0
+- ✓ **Full suite:** 1107 passed, 1 skipped, 0 failed
+- ✓ **J-07 gate tests:** 57 passed (unchanged; `default`/`v1` byte-identical)
+
+### Configuration Integrity
+- ✓ **Fingerprint verification:** `Config().config_fingerprint() == '4d665603569b9dbf'` (pinned, unchanged despite 3 new fields)
+- ✓ **Excluded fields active:** New confluence fields in `excluded` set; would move hash if NOT excluded (proven by counter-test in suite)
+- ✓ **No magic numbers:** All thresholds reference Config; zero hardcoded literals in clustering/grading logic
+
+---
+
+## Blockers
+
+**NONE.** All verification checks pass. All test cases pass. All required artifacts present and correct.
+
+---
+
+## Conclusion
+
+Phase goal achieved: **Confluence zones + A/B/C conviction classes shipped as an additive field on the existing `GET /research/levels` endpoint.** The implementation:
+
+1. Clusters support/resistance levels across timeframes within a configured price tolerance band
+2. Scores each zone as a timeframe-weighted sum of member level strengths
+3. Grades zones A/B/C based on distinct timeframe count and long-term member presence
+4. Returns zones as an explicit, always-present field (empty list for honest non-qualifying cases)
+5. Reads verbatim through both REST and MCP, single source of truth
+6. Includes no new route, no new MCP tool, no scope creep
+
+**Test suite:** 1107 passed, 0 failed, 0 errors. **Functional test plan:** 14/14 passed.
+
+---
+
+## QA Sign-Off
+
+**Verdict:** PASS
+
+The implementation is complete, correct, and ready to ship.
diff --git areports/qa/goal-tape_to_profit_support_resistence-iter-3-test-plan.md breports/qa/goal-tape_to_profit_support_resistence-iter-3-test-plan.md
new file mode 100644
index 0000000..ce23bde
--- /dev/null
+++ breports/qa/goal-tape_to_profit_support_resistence-iter-3-test-plan.md
@@ -0,0 +1,327 @@
+# Goal Iteration 3 — Confluence Zones & A/B/C Classes Functional Test Plan
+
+**Phase:** goal-tape_to_profit_support_resistence-iter-3
+**Date:** 2026-07-06
+**Frontend Present:** no
+
+## Phase Goal
+
+A researcher calling `GET /research/levels` receives, beside the raw support/resistance levels, the confluence zones that cluster those levels across timeframes — each zone carrying its member levels (with timeframes), a timeframe-weighted score, and an honest A/B/C conviction class, computed once, served from one canonical owner, and read verbatim by REST and MCP.
+
+---
+
+## Test Cases
+
+### TC-01 — Levels within confluence band cluster into a single zone
+
+**Type:** api
+**Preconditions:**
+- Backend is running with test fixtures loaded (PG 1h + 1d bars)
+- Confluence band is set in `Config` (e.g., `sr_confluence_band_bps`)
+- Levels have already been computed from the fixture bars
+
+**Steps:**
+1. Call `GET /research/levels?symbol=PG&as_of=<fixture_timestamp>`
+2. Parse the response JSON for `confluence_zones` field
+3. Identify all levels within the response
+4. Group levels by price proximity (within the configured band)
+5. Verify a single zone exists for levels that fall within the band
+
+**Expected outcome:** 
+A single confluence zone is returned with multiple member levels from different timeframes (e.g., 1h and 1d) whose prices fall within the configured tolerance band.
+
+**Pass criteria:** 
+The zone contains at least 2 member levels with distinct timeframes; all members' prices are within `sr_confluence_band_bps` of each other; no duplicate members in the zone.
+
+---
+
+### TC-02 — Levels outside the confluence band do not join the zone
+
+**Type:** api
+**Preconditions:**
+- Backend is running with test fixtures loaded
+- Multiple levels exist at different price points
+- At least one level is outside the tolerance band
+
+**Steps:**
+1. Call `GET /research/levels?symbol=PG&as_of=<fixture_timestamp>`
+2. Parse `confluence_zones` in the response
+3. Calculate price differences between levels at different timeframes
+4. Verify that levels outside the band are not members of the same zone
+
+**Expected outcome:** 
+Levels whose prices are beyond the configured tolerance band remain in separate zones (or as isolated levels).
+
+**Pass criteria:** 
+Each zone contains only members whose prices are within the tolerance band; levels outside the band do not appear as members of the same zone.
+
+---
+
+### TC-03 — Zone score is a timeframe-weighted sum of member levels' strengths
+
+**Type:** api
+**Preconditions:**
+- A synthetic multi-timeframe fixture with known level strengths and timeframe weights is loaded
+- Timeframe weights are configured (e.g., `sr_timeframe_weights`)
+- Each level has a known strength value
+
+**Steps:**
+1. Call `GET /research/levels?symbol=<fixture_symbol>&as_of=<fixture_timestamp>`
+2. Extract the confluence zone(s) and their member levels
+3. For each member level, retrieve its strength value and corresponding timeframe weight
+4. Manually compute the expected zone score: sum of (level_strength × timeframe_weight)
+5. Compare the computed value to the returned zone `score` field
+
+**Expected outcome:** 
+The returned zone score matches the manually computed timeframe-weighted sum.
+
+**Pass criteria:** 
+Exact numeric match (or ±0.01 tolerance for floating-point rounding); formula correctness asserted on the synthetic fixture with exact known inputs.
+
+---
+
+### TC-04 — A/B/C grading: class A when config criteria are met
+
+**Type:** api
+**Preconditions:**
+- A synthetic fixture with 3+ distinct timeframes (meeting the A-class criterion) is loaded
+- All member levels fall within the confluence band
+- At least one member is a long-term level (e.g., 1d or 1w)
+- Config class thresholds are set to grade this zone as A
+
+**Steps:**
+1. Call `GET /research/levels?symbol=<fixture_symbol>&as_of=<fixture_timestamp>`
+2. Extract the confluence zone(s)
+3. Verify each zone's `class` field value
+
+**Expected outcome:** 
+A zone meeting the config A-class criteria (multiple timeframes including a long-term level within tolerance) is graded as class **A**.
+
+**Pass criteria:** 
+Exact class label "A" returned; criteria (distinct timeframes, long-term member presence, band fit) verified to be met in the fixture.
+
+---
+
+### TC-05 — A/B/C grading: honest B/C when criteria not met
+
+**Type:** api
+**Preconditions:**
+- The PG fixture (1h + 1d only, 2 timeframes) is loaded
+- If the A-class criterion requires 3+ timeframes, the real PG fixture cannot produce a class A zone
+- Config class thresholds are properly set
+
+**Steps:**
+1. Call `GET /research/levels?symbol=PG&as_of=<fixture_timestamp>`
+2. Extract the confluence zone(s) returned
+3. Verify the class of any zone(s) returned
+
+**Expected outcome:** 
+Zones that do not meet the A-class criteria are honestly graded as **B or C**, never as fabricated A.
+
+**Pass criteria:** 
+Class label is B or C (exact label per config); the honest non-A grading reflects the actual timeframe count / long-term presence in the real fixture; no fabricated zones.
+
+---
+
+### TC-06 — Byte-identical deterministic re-runs with explicit total order
+
+**Type:** api
+**Preconditions:**
+- Backend is running
+- Fixture data and config are unchanged
+- Zones are sorted by an explicit total order (e.g., price, then timeframe)
+
+**Steps:**
+1. Call `GET /research/levels?symbol=PG&as_of=<fixture_timestamp>` — capture response JSON as run 1
+2. Call the same endpoint again with identical parameters — capture response JSON as run 2
+3. Compute SHA-256 hash of the entire `confluence_zones` array (or full response) for each run
+4. Compare the hashes and the JSON structure (member order, field values)
+
+**Expected outcome:** 
+Both calls return byte-identical JSON; the order of zones and member levels within each zone is consistent across runs.
+
+**Pass criteria:** 
+JSON hashes match exactly; `confluence_zones` array order is stable (e.g., zones sorted by lowest member price, ties broken by timeframe); all numeric values identical.
+
+---
+
+### TC-07 — No-lookahead: zones/classes at as-of T use only bars ≤ T
+
+**Type:** api
+**Preconditions:**
+- A fixture with bar data spanning a known range (e.g., bars for timestamps t0, t1, t2, ..., tN)
+- Zones are computed with as-of time = t_k (a point in the middle of the range)
+
+**Steps:**
+1. Call `GET /research/levels?symbol=<fixture_symbol>&as_of=t_k` (truncation point in the middle)
+2. Record the zones and their member levels returned
+3. Call the same endpoint with as_of = t_N (all bars available)
+4. Compare the two zone results
+
+**Expected outcome:** 
+The zones at as-of t_k are identical to what was computed when all bars at or before t_k were known; adding bars after t_k does not change any zone or class computed at t_k.
+
+**Pass criteria:** 
+Zones returned for as_of=t_k are unchanged when later bars are added; lookahead property verified via physical truncation test (same style as J-02 test_lookahead_free_...).
+
+---
+
+### TC-08 — MCP `levels` tool remains byte-identical to REST response
+
+**Type:** api
+**Preconditions:**
+- Backend MCP server is running
+- `GET /research/levels` is reachable
+- MCP `levels` tool is available
+
+**Steps:**
+1. Call `GET /research/levels?symbol=PG&as_of=<fixture_timestamp>` via REST
+2. Call the MCP `levels` tool with the same parameters (symbol, as_of)
+3. Compare the returned JSON payloads
+
+**Expected outcome:** 
+The MCP response is byte-identical to the REST response, including the new `confluence_zones` field.
+
+**Pass criteria:** 
+JSON hashes match; no field reordering or value divergence; single source of truth confirmed (REST ≡ MCP).
+
+---
+
+### TC-09 — No-magic-numbers introspection: confluence config fields in code
+
+**Type:** artifact
+**Preconditions:**
+- Source files exist: `apps/backend/app/config.py`, `apps/backend/app/research/levels.py`
+
+**Steps:**
+1. Read `apps/backend/app/config.py`
+2. Identify the confluence band field(s) (e.g., `sr_confluence_band_bps`)
+3. Identify the A/B/C class threshold field(s) (e.g., score cutoffs, criteria names)
+4. Read `apps/backend/app/research/levels.py`
+5. Grep for literal numeric thresholds (e.g., `if score > 0.75:`, `if num_timeframes >= 3:`)
+6. Verify all thresholds reference config fields, not hardcoded numbers
+
+**Expected outcome:** 
+All confluence parameters are defined in `Config` and referenced by name in `levels.py`; no literal threshold numbers appear in the clustering/grading logic.
+
+**Pass criteria:** 
+Grep returns zero matches for patterns like `if.*score\s*[><=].*\d` or `if.*timeframes.*\d` in `levels.py`; every threshold is a `Config` or `self.config` attribute access.
+
+---
+
+### TC-10 — Config fingerprint unchanged; new fields in excluded set
+
+**Type:** api
+**Preconditions:**
+- Backend is running
+- `Config().config_fingerprint()` is callable
+- Source file `apps/backend/app/config.py` is accessible
+
+**Steps:**
+1. Call the backend route or directly invoke `Config().config_fingerprint()`
+2. Record the returned fingerprint hash
+3. Read `apps/backend/app/config.py` and locate the `config_fingerprint()` method
+4. Verify that new confluence config fields (e.g., `sr_confluence_band_bps`, class thresholds) are listed in the `excluded` set
+5. Compare the returned hash to the expected value: `4d665603569b9dbf`
+
+**Expected outcome:** 
+The `config_fingerprint()` returns exactly `4d665603569b9dbf` (iter-1 pinned value); new confluence fields are present in the `excluded` set, same pattern as existing `sr_*` fields.
+
+**Pass criteria:** 
+Fingerprint hash matches `4d665603569b9dbf`; all new confluence fields are in the `excluded` set; a counter-test (removing a field from `excluded`) would change the hash, proving the exclusion is active.
+
+---
+
+### TC-11 — Honest empty zones: no_bar_series_for_symbol behavior unchanged
+
+**Type:** api
+**Preconditions:**
+- A symbol with no bar series in the store is queried
+- Backend is running
+
+**Steps:**
+1. Call `GET /research/levels?symbol=NOSUCHSYMBOL&as_of=<any_timestamp>`
+2. Parse the response for `no_bar_series_for_symbol` and `confluence_zones` fields
+
+**Expected outcome:** 
+Response includes `no_bar_series_for_symbol: true` and `confluence_zones: []` (empty list, not null or absent).
+
+**Pass criteria:** 
+Both fields present; `no_bar_series_for_symbol` is true; `confluence_zones` is an empty array; no fabricated zone or class.
+
+---
+
+### TC-12 — Honest empty zones: levels but no qualifying cluster
+
+**Type:** api
+**Preconditions:**
+- A symbol has levels at multiple price points with no cluster (prices far apart, outside the band)
+- At most one level exists per timeframe, or no combination qualifies for clustering
+
+**Steps:**
+1. Call `GET /research/levels?symbol=<isolated_fixture_symbol>&as_of=<fixture_timestamp>`
+2. Parse the response for `levels` and `confluence_zones` fields
+
+**Expected outcome:** 
+Response includes a non-empty `levels` array and an empty `confluence_zones` array (not null, not fabricated zones).
+
+**Pass criteria:** 
+`levels` is non-empty; `confluence_zones` is present and an empty array; explicit distinction between "no levels at all" and "levels but no cluster" maintained.
+
+---
+
+### TC-13 — Frontend files unchanged (zero diff)
+
+**Type:** artifact
+**Preconditions:**
+- Git repository is available
+- Iteration baseline snapshot exists (or main branch is used as baseline)
+
+**Steps:**
+1. Run: `git diff <baseline>..HEAD -- apps/frontend/`
+2. Capture the output
+
+**Expected outcome:** 
+The diff is empty — no changes to any file in `apps/frontend/`.
+
+**Pass criteria:** 
+`git diff` returns no output; exit code is 0; confirms backend-only iteration (no UI change, as per spec).
+
+---
+
+### TC-14 — No second computation path: grep-guard for `structure_tape` and J-04 code
+
+**Type:** artifact
+**Preconditions:**
+- Source files exist across the backend codebase
+
+**Steps:**
+1. Run: `grep -r "structure_tape" apps/backend/app/research/ --include="*.py"` (excluding tests and comments)
+2. Run: `grep -r "GET /research/strategies" apps/backend/app/ --include="*.py"` (excluding tests)
+3. Run: `grep -r "class_scaled\|scaled_by_class" apps/backend/app/research/ --include="*.py"`
+4. Record any matches
+
+**Expected outcome:** 
+No matches (or only in comments/docstrings explicitly marking as "J-04, out of scope").
+
+**Pass criteria:** 
+Zero matches in active code; confirms single-source-of-truth discipline and no premature J-04 implementation.
+
+---
+
+## Summary
+
+**Total test cases:** 14
+- **API tests:** 8 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-10)
+- **Artifact tests:** 6 (TC-09, TC-11, TC-12, TC-13, TC-14)
+
+All tests verify the core requirements:
+- Deterministic clustering and byte-identical re-runs
+- Correct timeframe-weighted scoring
+- Honest A/B/C grading per config criteria
+- No lookahead
+- Single source of truth (REST ≡ MCP)
+- Config ownership (no magic numbers)
+- Honest empty states
+- Zero frontend change
+- Grep-guarded separation from J-04
diff --git areports/reviews/goal-tape_to_profit_support_resistence-iter-3-review.md breports/reviews/goal-tape_to_profit_support_resistence-iter-3-review.md
new file mode 100644
index 0000000..c1aa688
--- /dev/null
+++ breports/reviews/goal-tape_to_profit_support_resistence-iter-3-review.md
@@ -0,0 +1,25 @@
+**Verdict:** PASS
+
+```yaml
+phase: goal-tape_to_profit_support_resistence-iter-3
+date: 2026-07-06
+reviewer: reviewer
+summary: |
+  J-03 confluence zones + A/B/C classes added as an additive field on compute_levels inside the
+  existing research/levels.py owner, no new route/module/MCP tool. Clustering, grading, config
+  fields, fingerprint exclusion, and lookahead-safety all independently re-verified by running the
+  test suite (57/57 targeted + 57/57 J-07 gate pass, fingerprint pinned at 4d665603569b9dbf,
+  frontend diff empty).
+spec_alignment:
+  definition_of_done: complete
+  scope_creep: none
+issues: []
+standards:
+  state_transitions_server_side: n/a
+  test_quality: pass
+  no_dead_code: pass
+  no_hardcoded_localhost: n/a
+  ui_evolved_with_capability: n/a
+  navigation_updated: n/a
+  architecture_principles: pass
+```
diff --git aruns/goal-session-tape_to_profit_support_resistence/iter-3/.steps/coherence.done bruns/goal-session-tape_to_profit_support_resistence/iter-3/.steps/coherence.done
new file mode 100644
index 0000000..49cab4d
--- /dev/null
+++ bruns/goal-session-tape_to_profit_support_resistence/iter-3/.steps/coherence.done
@@ -0,0 +1 @@
+{"v":1,"step":"coherence","iter":"3","iter_name":"goal-tape_to_profit_support_resistence-iter-3","ts":"2026-07-06T09:35:53Z","tree_hash":"355762bb082bc34b8566f0facd883d4283433642","artifacts":["runs/goal-session-tape_to_profit_support_resistence/iter-3/coherence.md"],"verdict":"COHERENCE-WARN","journeys":""}
diff --git aruns/goal-session-tape_to_profit_support_resistence/iter-3/coherence.md bruns/goal-session-tape_to_profit_support_resistence/iter-3/coherence.md
new file mode 100644
index 0000000..5b1ec14
--- /dev/null
+++ bruns/goal-session-tape_to_profit_support_resistence/iter-3/coherence.md
@@ -0,0 +1,33 @@
+# Iteration 3 — Coherence Audit
+
+**Iteration:** goal-tape_to_profit_support_resistence-iter-3
+**Date:** 2026-07-06
+**Written by:** coherence-auditor
+
+---
+
+**Verdict:** COHERENCE-WARN
+
+---
+
+## Data Contract check
+
+| Value / entity | Result | Evidence (file:line) |
+|---|---|---|
+| Support/resistance levels + A/B/C confluence classes (Data Contract row 39, both halves) | OK | Computed ONCE in the already-registered owner `apps/backend/app/research/levels.py` — new `compute_confluence_zones`/`_cluster_levels`/`_grade_zone`/`_confluence_zone`/`_zone_sort_key` (levels.py:162-244) are added inside this SAME module, not a new one; `compute_levels` (levels.py:247-296) folds the zones in as an additive `confluence_zones` key. Served verbatim by the existing single route `apps/backend/app/research/routes.py:1637-1655` (`return {"symbol": normalized_symbol, "as_of": as_of, **result}` — confirmed by direct read, no field is dropped/repicked) and the existing MCP `levels` tool (`apps/backend/app/mcp/__init__.py:190-199`, description text updated only, no handler change). Byte-identity between REST and MCP is asserted end-to-end by `apps/backend/tests/test_mcp_server.py:290-832` (`test_levels_tool_byte_identical_on_a_non_empty_live_result`, extended this iteration to require a non-empty `confluence_zones` in the compared body). Grepped the rest of the backend (`analytics.py`, `pnl_scan.py`, `edge_report.py`) and `apps/frontend/` for `confluence`/`cluster`/`CLASS_A` — zero hits outside `research/levels.py` and its own tests: no second computation path anywhere. |
+| Confluence config inputs (`sr_confluence_band_bps`, `sr_confluence_class_a_min_timeframes`, `sr_confluence_class_b_min_timeframes`) | OK | Computation inputs, not displayed values, per row 39's own "every parameter config-sourced" note — correctly take no Data-Contract row. Declared with rationale at `apps/backend/app/config.py:1130,1139,1146`; added to the `config_fingerprint()` `excluded` list at `config.py:1366-1368`, same pattern/placement as the three pre-existing `sr_*` fields immediately above them (`config.py:1356-1358`) — preserves the pinned `default` fingerprint (`test_sr_config_fields_are_excluded_from_config_fingerprint` in `test_levels.py:688-703` asserts this directly). |
+| New value not yet in the Data Contract | N/A | `confluence_zones` is not a new concept — Row 39 already named "A/B/C confluence classes" explicitly; this iteration ships the previously-deferred classes half of an already-registered row (the iter spec's own "Data-contract additions: None" is correct, matches the blueprint text verbatim). No A5 "unregistered value" note warranted. |
+
+## Information Architecture check
+
+| Feature / route | Result | Evidence (nav file inspected) |
+|---|---|---|
+| `GET /research/levels` `confluence_zones` field (J-03) | OK | Blueprint IA lists J-03's canonical home as "API `GET /research/levels` (same endpoint) + MCP `levels`" with Nav section "machine" (no nav home required). No new route, file, or MCP tool was added — `git diff <snapshot>..HEAD --diff-filter=A` shows zero new source files. `git diff <snapshot>..HEAD -- apps/frontend/` is empty, confirming the spec's "Frontend Present: no" / "apps/frontend/ MUST NOT change" constraint held. No nav/sidebar/router file exists to check reachability against because none was meant to change — consistent with the blueprint. |
+
+## Blocking violations (FAIL only)
+
+None.
+
+## Advisory notes (non-blocking)
+
+- **README capability bullet undersells this iteration's actual shipped capability.** `README.md`'s `<!-- AUTO:capabilities -->` block gained its first-ever bullet for the levels endpoint this iteration — `"**Support/resistance level detection (research API)**..."` (README.md, `AUTO:capabilities` block, new bullet before the REST-API-routes bullet) — but its prose describes only the J-02 half (swing pivots, prior-period extremes, no-lookahead, byte-identical determinism, the two honest "nothing to show" states) and never mentions confluence zones, timeframe-weighted scoring, or the A/B/C conviction classes that are this exact iteration's (J-03's) entire deliverable on the same endpoint. (Confirmed via `git show <snapshot>:README.md` that no prior S/R-levels bullet existed before this iteration, so this is a fresh miss, not stale carry-over text.) Not a Data Contract or IA violation — there is one computation, one endpoint, and no nav change — so this does not block. Recommend the next README pass extend this bullet (or the adjacent "Machine-readable access for AI tools" bullet, which does now list "support/resistance levels" but likewise omits confluence/classes) to describe the confluence-zone/A-B-C-class shape so the doc matches the response the code and tests actually assert.
diff --git aruns/goal-session-tape_to_profit_support_resistence/iter-3/journey-history.pre.json bruns/goal-session-tape_to_profit_support_resistence/iter-3/journey-history.pre.json
new file mode 100644
index 0000000..3f6e3f4
--- /dev/null
+++ bruns/goal-session-tape_to_profit_support_resistence/iter-3/journey-history.pre.json
@@ -0,0 +1,69 @@
+{
+  "journeys": {
+    "J-01": {
+      "id": "J-01",
+      "name": "Multi-timeframe historical bars are ingested and persisted (data foundation + free-plan probe)",
+      "status": "passing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-2",
+      "last_passing_iter": "goal-tape_to_profit_support_resistence-iter-2",
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "Required-still-passing; full backend suite green this iter (reports/qa/goal-tape_to_profit_support_resistence-iter-2-qa.md: 1095 passed incl. test_bars.py/test_bars_api.py) + evaluator-reran fingerprint 4d665603569b9dbf + observer/profile equivalence (exit 0)"
+    },
+    "J-02": {
+      "id": "J-02",
+      "name": "Deterministic support/resistance levels per timeframe",
+      "status": "passing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-2",
+      "last_passing_iter": "goal-tape_to_profit_support_resistence-iter-2",
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "Backend/machine-surface journey (no browser step; browser QA correctly SKIPPED). reports/qa/goal-tape_to_profit_support_resistence-iter-2-qa.md TC-01..TC-18 all PASS + evaluator independently reran tests/test_levels.py+test_levels_api.py+2 MCP byte-identity/arg tests+observer/profile equivalence => exit 0 (48 passed) + audit PASS_WITH_GAPS (physical-truncation lookahead proof non-vacuous; single-source-of-truth confirmed)"
+    },
+    "J-03": {
+      "id": "J-03",
+      "name": "Confluence zones and A/B/C conviction classes",
+      "status": "failing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-2",
+      "last_passing_iter": null,
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "Out of scope this iter. GET /research/levels ships levels only; classes field deliberately absent (dev handoff + audit Domain section); no confluence clustering/scoring/grading code exists"
+    },
+    "J-04": {
+      "id": "J-04",
+      "name": "Tape-confirmed structure entries as a registered strategy",
+      "status": "failing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-2",
+      "last_passing_iter": null,
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "Out of scope this iter. evaluator grep -rn 'structure_tape|/research/strategies' apps/backend/app/ => no matches; /research/strategies still 404s (no strategy registry)"
+    },
+    "J-05": {
+      "id": "J-05",
+      "name": "Class-scaled stop, reward, and simulated size",
+      "status": "failing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-2",
+      "last_passing_iter": null,
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "Out of scope this iter. No per-class stop/reward/sizing machinery; transitively absent (depends on the unbuilt structure_tape registry — grep-confirmed no structure_tape)"
+    },
+    "J-06": {
+      "id": "J-06",
+      "name": "structure_tape is measured honestly against the v1 champion",
+      "status": "failing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-2",
+      "last_passing_iter": null,
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "Out of scope this iter. pnl_scan/edge_report remain champion-only; no named-strategy evaluation path added (grep-confirmed no structure_tape)"
+    },
+    "J-07": {
+      "id": "J-07",
+      "name": "The archived eras are unchanged (regression sentinel)",
+      "status": "already_passing",
+      "last_verified_iter": "goal-tape_to_profit_support_resistence-iter-2",
+      "last_passing_iter": "goal-tape_to_profit_support_resistence-iter-2",
+      "first_seen_iter": "goal-tape_to_profit_support_resistence-iter-0",
+      "last_evidence_path": "evaluator-reran tests/test_observer_equivalence.py + tests/test_profile_equivalence.py (green, exit 0, byte-identical default) + live-computed Config().config_fingerprint()=='4d665603569b9dbf' (pinned, unmoved; 3 new sr_* fields correctly excluded) + git diff 37d3ad2..HEAD -- apps/frontend/ empty"
+    }
+  },
+  "anti_goal_violations": [],
+  "updated_at": "2026-07-06T05:15:00Z"
+}
diff --git aruns/goal-tape_to_profit_support_resistence-iter-3/plan.md bruns/goal-tape_to_profit_support_resistence-iter-3/plan.md
new file mode 100644
index 0000000..cdd4c91
--- /dev/null
+++ bruns/goal-tape_to_profit_support_resistence-iter-3/plan.md
@@ -0,0 +1,119 @@
+# goal-tape_to_profit_support_resistence-iter-3 Execution Plan
+
+## Alignment check
+
+J-03 (confluence zones + A/B/C conviction classes) is docs/goal.md Key Capability #3
+("Confluence classification") and Must-have journey J-03 verbatim. It builds directly on J-01
+(bar store, iter-1) and J-02 (deterministic, lookahead-free S/R levels, iter-2), both shipped and
+PASS/PASS_WITH_GAPS-audited. No drift from the project goal, no scope creep detected — the spec's
+IN SCOPE section maps 1:1 onto goal.md's J-03 acceptance text (clustering, timeframe-weighted
+score, A/B/C grading, additive field on the existing endpoint). Everything the spec defers
+(direction/kind labelling, a distinct corrupt-sole-series state, J-04-J-06) is correctly named as
+OUT OF SCOPE and matches the archived plan's own reserved shape (`levels.py:2` and
+`routes.py:1631` already mark `classes` as deliberately absent pending this iteration).
+
+## What to Build
+
+- **Config-owned confluence parameters** in `apps/backend/app/config.py`, `sr_`-namespaced, each
+  documented with rationale (no magic numbers): a clustering tolerance / confluence band (spec
+  suggests `sr_confluence_band_bps`) and the A/B/C class thresholds/criteria (score cutoffs and/or
+  confluence criteria such as minimum distinct timeframes / required long-term member — exact
+  field name(s) and shape are the developer's call, mirroring the `sr_timeframe_weights` style).
+  **Add every new field to `config_fingerprint()`'s `excluded` set** — same rationale as the three
+  existing `sr_*` fields at `config.py:1320-1322`. The pinned `default` fingerprint MUST stay
+  `4d665603569b9dbf`.
+- **Deterministic, lookahead-free confluence clustering + A/B/C classification**, added INSIDE the
+  existing `apps/backend/app/research/levels.py` (the registered Data-Contract-Row-39 owner — NO
+  new module, endpoint, or MCP tool): cluster the levels `compute_levels` already produces, across
+  timeframes, into confluence zones wherever prices fall within the config band; score each zone as
+  a timeframe-weighted sum of its member levels' strengths; grade A/B/C by the config
+  thresholds/criteria. Each zone records its member levels (with timeframes), its score, its class.
+  Sort zones by an explicit total order for byte-identical served JSON.
+- **Return zones as an additive field** on `compute_levels`'s existing return dict (beside `levels`
+  and `no_bar_series_for_symbol`) — served verbatim by the existing `GET /research/levels` route
+  and the existing MCP `levels` proxy. No second computation path; MCP JSON stays byte-identical to
+  REST.
+- **Honest labelling**: class A only when the config confluence criteria are met; B/C otherwise —
+  never a fabricated class. `no_bar_series_for_symbol` behavior is unchanged. A symbol with levels
+  but no qualifying cluster returns an explicit empty zones list (never a bare/ambiguous result).
+- **Decide + document (do not fix) the corrupt-sole-series seam**: confirm the confluence layer
+  reads only the healthy levels `compute_levels` already produces and introduces no new fabricated
+  or aliased state; the distinct corrupt-series state stays owned by `GET /research/bars` (iter-2
+  finding B1). Record this decision explicitly in the dev handoff.
+
+## Agents Required
+
+- **developer: yes** — backend-only implementation (confluence clustering/scoring/grading in
+  `research/levels.py`, config fields, tests). Equivalent answer in the dispatcher's own
+  vocabulary: **backend-data: yes, frontend-ux: no** — there is no frontend work in this iteration.
+
+Frontend Present: no
+
+## Files to Create/Modify
+
+- `apps/backend/app/config.py` -- add the confluence-band + A/B/C class-threshold field(s),
+  `sr_`-namespaced, with rationale; add all new fields to `config_fingerprint()`'s `excluded` set
+  (same pattern as `sr_pivot_lookback` / `sr_touch_tolerance_bps` / `sr_timeframe_weights`)
+- `apps/backend/app/research/levels.py` -- add clustering + timeframe-weighted scoring + A/B/C
+  grading; wire the new zones field into `compute_levels`'s return dict; update the module
+  docstring's "confluence classes are J-03, out of scope here" line (now in scope)
+- `apps/backend/app/research/routes.py` -- update the "classes deliberately ABSENT" comment block
+  above `GET /research/levels` (`routes.py:1627-1633`); no route body change should be needed since
+  the route already spreads `compute_levels`'s dict verbatim (`**result`)
+- `apps/backend/app/mcp/__init__.py` -- update the `levels` tool's description text to mention
+  confluence zones/classes for doc parity; no dispatch-logic change needed (already a byte-identical
+  proxy that forwards any new field)
+- `apps/backend/tests/test_levels.py` -- extend: one or more synthetic multi-timeframe fixtures for
+  exact-value control over A/B/C assertions (mirroring the existing `_swing_fixture` /
+  `_prior_period_fixture` pattern — see Known Consideration below), deterministic clustering tests,
+  score-exactness tests, A/B/C grading tests with exact expected classes, byte-identical re-run
+  test, no-lookahead-for-classes test (physical truncation, same style as J-02's), no-magic-numbers
+  introspection extended to the new config field(s), honest empty-zones-list test, fingerprint-
+  exclusion test extended to the new fields
+- `apps/backend/tests/test_levels_api.py` -- extend the happy-path test(s) to assert the new zones
+  field's exact shape/values on the committed PG fixture; assert honest states unchanged
+- `apps/backend/tests/test_mcp_server.py` -- extend the `levels` byte-identity test to cover the new
+  zones field
+- `docs/handoffs/goal-tape_to_profit_support_resistence-iter-3-dev.md` -- NEW dev handoff (must
+  include the corrupt-sole-series seam decision, per DoD)
+
+`apps/frontend/` MUST NOT change this iteration (confirm via `git diff -- apps/frontend/` empty in
+the handoff, same as iter-1/iter-2).
+
+## Known Consideration (flagging, not deciding, for the developer)
+
+The only **committed real** bar fixture is PG `1h` (9 bars) + PG `1d` (5 bars) — **two**
+timeframes. If the config's A-class criterion requires 3+ distinct timeframes (or specifically a
+long-term member plus multiple others), the real committed fixture alone may never produce a class
+A zone. This is exactly the situation J-02 solved by pairing synthetic fixtures (full numeric
+control) with the real PG fixture (keyless real-data proof) — the same pattern should carry
+forward here: use a synthetic multi-series fixture to exercise and exactly assert a genuine A case
+(and a genuine B/C case), and separately assert whatever honest classes the 2-timeframe real PG
+fixture actually produces (which may legitimately be B/C-only). This is a design decision for the
+developer to make and document, not something this plan prescribes.
+
+## Key Test Scenarios
+
+- Levels within the config confluence band, across timeframes, cluster into one zone; levels
+  outside the band do not join.
+- Zone score = timeframe-weighted sum of member levels' strengths — exact value asserted on a
+  synthetic fixture with known inputs.
+- A/B/C grading: a zone meeting the config criteria grades A; a non-qualifying cluster grades B/C
+  — exact expected classes asserted (both a synthetic A case and whatever the real PG fixture
+  honestly produces).
+- Byte-identical deterministic re-runs of zones/classes (explicit total order).
+- No-lookahead extended to classes: a bar after as-of `T` cannot change any zone or class (physical
+  store-truncation test, mirroring J-02's `test_lookahead_free_...`).
+- MCP `levels` tool remains byte-identical to the REST response including the new zones field.
+- No-magic-numbers introspection extended to the new confluence config field(s).
+- `Config().config_fingerprint() == '4d665603569b9dbf'` unchanged; new confluence fields present in
+  the `excluded` set; a real-threshold counter-test proves they'd move the hash if NOT excluded.
+- Honest empty states: `no_bar_series_for_symbol` behavior unchanged; a symbol with levels but no
+  qualifying cluster returns an explicit empty zones list (not fabricated, not conflated with the
+  no-series state).
+- Full backend suite green (no regressions); `test_observer_equivalence.py` +
+  `test_profile_equivalence.py` + `test_real_data_gate.py` all green (`default`/`v1` byte-identical,
+  frozen).
+- `git diff -- apps/frontend/` empty.
+- Grep-guard: no `research/strategies`, `structure_tape`, or second computation path introduced
+  (J-04–J-06 correctly remain unbuilt).
diff --git aruns/goal-tape_to_profit_support_resistence-iter-3/status.json bruns/goal-tape_to_profit_support_resistence-iter-3/status.json
new file mode 100644
index 0000000..f1a6539
--- /dev/null
+++ bruns/goal-tape_to_profit_support_resistence-iter-3/status.json
@@ -0,0 +1,23 @@
+{
+  "phase": "goal-tape_to_profit_support_resistence-iter-3",
+  "status": "complete",
+  "current_step": "closure_passed",
+  "updated_at": "2026-07-06T09:22:11.111322Z",
+  "started_at": "2026-07-06T07:27:47.864532Z",
+  "cli": "claude",
+  "blockers": [],
+  "changed_files": [
+    "apps/backend/app/config.py",
+    "apps/backend/app/research/levels.py",
+    "apps/backend/app/research/routes.py",
+    "apps/backend/app/mcp/__init__.py",
+    "apps/backend/tests/test_levels.py",
+    "apps/backend/tests/test_levels_api.py",
+    "apps/backend/tests/test_mcp_server.py",
+    "docs/handoffs/goal-tape_to_profit_support_resistence-iter-3-dev.md",
+    "reports/phase-goal-tape_to_profit_support_resistence-iter-3-implementation-summary.md"
+  ],
+  "tests_run": true,
+  "browser_checks_run": false,
+  "next_action": "review"
+}
```
