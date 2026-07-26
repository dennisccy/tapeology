# Iteration diff (bounded)

Files changed: 126. Shown in full: 92.

**Excluded paths** (data/lock/binary — content not shown; the secret scanner
still scanned them; Read a file directly if it matters):
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/tree/reports/qa/goal-afx01-iter-3-evidence/UT-01-summary-mixed.png` (3 diff lines)
- `incredible_auto_dev/tests/judgment/auditor/case-01-clean-pass/tree/reports/qa/goal-afx01-iter-3-evidence/UT-02-summary-empty.png` (3 diff lines)

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `incredible_auto_dev/docs/improvement-roadmap.md` (617 lines not shown)
- `incredible_auto_dev/feedback/README.md` (13 lines not shown)
- `incredible_auto_dev/hooks/post-edit-lint.sh` (29 lines not shown)
- `incredible_auto_dev/hooks/post-write-artifact-quality.sh` (25 lines not shown)
- `incredible_auto_dev/scripts/automation/browser-qa-phase.sh` (13 lines not shown)
- `incredible_auto_dev/scripts/automation/dev-phase.sh` (13 lines not shown)
- `incredible_auto_dev/scripts/automation/finalize-phase.sh` (13 lines not shown)
- `incredible_auto_dev/scripts/automation/generate-test-plan.sh` (12 lines not shown)
- `incredible_auto_dev/scripts/automation/goal-iter-lean.sh` (13 lines not shown)
- `incredible_auto_dev/scripts/automation/harvest-lessons.sh` (13 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/chain-tmp.sh` (13 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/common.sh` (27 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/condense.sh` (20 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/goal-gates.sh` (13 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/interactive-dispatch.sh` (21 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/plain-language.sh` (158 lines not shown)
- `incredible_auto_dev/scripts/automation/lib/render_iteration_summary.py` (121 lines not shown)
- `incredible_auto_dev/scripts/automation/phase-audit.sh` (12 lines not shown)
- `incredible_auto_dev/scripts/automation/qa-phase.sh` (13 lines not shown)
- `incredible_auto_dev/scripts/automation/render-summary.sh` (13 lines not shown)
- `incredible_auto_dev/scripts/automation/review-phase.sh` (13 lines not shown)
- `incredible_auto_dev/scripts/automation/run-evals.sh` (51 lines not shown)
- `incredible_auto_dev/scripts/automation/run-goal.sh` (273 lines not shown)
- `incredible_auto_dev/scripts/automation/run-judgment-evals.sh` (30 lines not shown)
- `incredible_auto_dev/scripts/automation/run-phase.sh` (71 lines not shown)
- `incredible_auto_dev/scripts/automation/ui-test-design-phase.sh` (13 lines not shown)
- `incredible_auto_dev/skills/goal-authoring.md` (13 lines not shown)
- `incredible_auto_dev/skills/plain-language.md` (78 lines not shown)
- `incredible_auto_dev/tests/automation/test-doc-drift.sh` (120 lines not shown)
- `incredible_auto_dev/tests/automation/test-escalation-warn.sh` (90 lines not shown)
- `incredible_auto_dev/tests/automation/test-plain-language.sh` (172 lines not shown)
- `apps/frontend/app/desk/page.tsx` (848 lines not shown)

```diff
diff --git a/README.md b/README.md
index 880fac2..d27b38b 100644
--- a/README.md
+++ b/README.md
@@ -62,7 +62,8 @@ Current capabilities:
 - **Cockpit price-chart tradable bands and a descriptive confluence chip** — the tradable support/resistance bands from the Structure page's map now also draw directly on the live cockpit price chart while watching a symbol in Simulated or Historical mode: one or two solid price lines per band (rose for resistance, emerald for support), each labeled with side, class, quality score, and whether it sits on a round number — alongside the existing tape-state markers, without changing how those render. A small descriptive banner appears beneath the chart only when the last traded price sits inside one of those bands AND the live tape reading matches that band's configured rejection-or-breakthrough state — for example "Inside R-band 300.05–300.17 (class A) · tape: Ask Absorption (rejection) · measured history: edge report." The banner states the current condition and points to the edge report as measured history; it never tells you to buy or sell and never predicts an outcome. A simulated ticker with no real recorded price history shows an honest "No tradable map for TICKER" note instead of a fabricated band. Live mode is unchanged — the price chart, and therefore the bands and banner, stay hidden there exactly as before.
 - **S&P 100 universe snapshot fetch and registry (research API)** — on explicit request, fetch the current S&P 100 constituent list from a public source (Wikipedia) and validate it (a real company-symbol table, roughly 90–110 names, no garbled entries), refusing with a specific explanation on any anomaly rather than guessing or saving a partial list. A valid fetch is saved as a permanent, checksummed, dated snapshot; fetching identical membership again is recognized and refused rather than silently duplicated or overwritten. Dual-class tickers are normalized for use elsewhere in the app (for example `BRK.B` → `BRK-B`) while the original source form is kept in the snapshot's own record. A second call lists every saved snapshot and returns the most recent membership, honestly reporting that nothing has been fetched yet before the first run. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
 - **Bar coverage check and resumable top-up over the universe (research API + command-line tool)** — for every member of the most recently registered S&P 100 universe snapshot, see instantly — read from a lookup index, never by re-scanning the underlying bar files — whether hourly, 4-hour, daily, and weekly price bars are already on file and how fresh each one is. A single operator-triggered job then walks every member of that universe and fills in whichever of those four windows are missing, reusing the exact same fetch-and-record path a single manual bar request already uses, so behavior is identical; it reports live progress per symbol/timeframe (newly fetched, already on file, or failed), can be cancelled mid-run, and safely resumes without re-downloading anything already recorded. A command-line version runs the same job unattended for a real, full pass over the whole universe. There is no browser page for this yet; the coverage check and the top-up job are both reachable through the research API, and the top-up job also from the command line.
-- **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `GET /research/taxonomy`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/bars/{id}/candles`, `GET /research/candles`, `GET /research/levels`, `GET /research/tradability`, `GET /research/setups`, `GET /research/setups/{id}`, `GET /research/edge-report`, `POST /research/edge-report/compute`, `GET /research/edge-report/compute`, `POST /research/edge-report/compute/cancel`, `POST /research/desk/universe/fetch`, `GET /research/desk/universe`, `GET /research/desk/coverage`, `POST /research/desk/topup/compute`, `GET /research/desk/topup/compute`, `POST /research/desk/topup/compute/cancel`, `GET /meta/ui-routes`.
+- **A daily screening desk over the fetched universe (research API + command-line tool)** — for the latest registered S&P 100 universe snapshot, run a "screen" as of a chosen date: for every member, read its own already-computed tradable level map and summarize the closest support/resistance band into one ranked list — that band's inherited A/B/C conviction class, how far the screen date's closing price sits from it in basis points, and the band's quality score, ranked strongest and closest first. A member with no recorded price bars for that date is reported as an honest "skipped" entry rather than guessed at. Every run is pinned to its exact inputs — the screen date, which universe snapshot was used, the exact configuration in effect, and the bar data on file at the time — so repeating an identical request returns the same saved result instead of writing a duplicate, and a corrupted or tampered saved run is refused rather than silently overwritten. A run reports live progress as it works through the list and can be cancelled mid-flight; only one run proceeds at a time. Past runs can be browsed as lightweight summaries, or fetched in full by date or as the latest recorded result. Triggered explicitly from the command line or the research API — never automatically. There is no browser page for this yet.
+- **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `GET /research/taxonomy`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/bars/{id}/candles`, `GET /research/candles`, `GET /research/levels`, `GET /research/tradability`, `GET /research/setups`, `GET /research/setups/{id}`, `GET /research/edge-report`, `POST /research/edge-report/compute`, `GET /research/edge-report/compute`, `POST /research/edge-report/compute/cancel`, `POST /research/desk/universe/fetch`, `GET /research/desk/universe`, `GET /research/desk/coverage`, `POST /research/desk/topup/compute`, `GET /research/desk/topup/compute`, `POST /research/desk/topup/compute/cancel`, `GET /research/desk/screen`, `POST /research/desk/screen/compute`, `GET /research/desk/screen/compute`, `POST /research/desk/screen/compute/cancel`, `GET /meta/ui-routes`.
 - **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, datasets, backtests, strategy registry, PnL ledger, bar series, support/resistance levels, tradable level maps, touch-event case studies, profit edge reports, and navigation data the REST API serves. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
 <!-- /AUTO:capabilities -->
 
diff --git a/apps/backend/app/meta.py b/apps/backend/app/meta.py
index 5199ea0..6667e1e 100644
--- a/apps/backend/app/meta.py
+++ b/apps/backend/app/meta.py
@@ -13,6 +13,10 @@ era-5D J-02 ("The Clean Slate" demolition interlude): the four journal-era rows
 ``/journal/[id]``, ``/studies``, ``/performance``) are removed here in the SAME iteration their
 pages are deleted (the no-dead-link rule, applied in reverse) — the map now lists exactly the
 two KEPT routes.
+
+Era B "The Desk" J-04 (this iteration): the third row, ``/desk``, is added here in the SAME
+iteration its page ships (the no-dead-link rule, forward direction this time) — the nav and MCP
+``ui_route_map`` pick it up with no further edit.
 """
 
 from __future__ import annotations
@@ -27,6 +31,7 @@ router = APIRouter(prefix="/meta", tags=["meta"])
 UI_ROUTES: tuple[dict[str, object], ...] = (
     {"path": "/", "label": "Cockpit", "nav": True},
     {"path": "/structure", "label": "Structure", "nav": True},
+    {"path": "/desk", "label": "Desk", "nav": True},
 )
 
 
diff --git a/apps/backend/app/providers/adapters/yahoo.py b/apps/backend/app/providers/adapters/yahoo.py
index 8e8b90b..92629d1 100644
--- a/apps/backend/app/providers/adapters/yahoo.py
+++ b/apps/backend/app/providers/adapters/yahoo.py
@@ -50,6 +50,7 @@ though in practice ``yfinance`` reuses this project's already-installed ``pandas
 
 from __future__ import annotations
 
+import math
 from datetime import datetime, timedelta
 from typing import AsyncIterator
 
@@ -155,6 +156,32 @@ def _chunks(start: datetime, end: datetime, limits: tuple[int, int] | None) -> l
     return windows or [(start, end)]
 
 
+def _is_priced_row(row) -> bool:
+    """Does ONE vendor row carry a real, finite price for all four OHLC fields (and a finite
+    volume)?
+
+    Yahoo emits a row for a session that has NOT traded yet — the current calendar day before the
+    open, and some post-holiday days — with pandas ``NaN`` in every price column and only a volume
+    number. ``float(NaN)`` succeeds silently, so without this check that row becomes a ``RawBar``
+    whose open/high/low/close are all ``nan``, and a ``NaN`` token is persisted into the
+    append-only, checksummed ``BarStore`` (era-desk-iter-4 audit B1 — 60 series over 58 symbols
+    were poisoned exactly this way, and ``/structure``'s candlestick chart then threw on the
+    ``null`` the JSON encoder serves for it).
+
+    A row with no prices is an ABSENT bar, not a bar whose prices are unknown, so it is dropped
+    HERE — at the vendor seam that knows what the vendor meant — exactly as an empty chunk is. A
+    window in which EVERY row is priceless still raises the honest ``NoDataForWindow`` below,
+    because ``rows_by_epoch`` stays empty."""
+    try:
+        return all(
+            math.isfinite(float(row[column]))
+            for column in ("Open", "High", "Low", "Close", "Volume")
+        )
+    except (TypeError, ValueError, KeyError):
+        # A non-numeric / missing column is likewise not a usable candle — dropped, never guessed.
+        return False
+
+
 def _resample_4h(hourly: tuple[RawBar, ...]) -> tuple[RawBar, ...]:
     """Deterministically resample REAL ``1h`` bars into aligned 4-hour buckets (era-5 J-02 — the
     era's single named new backend computation, confined entirely to this module; never duplicated
@@ -277,6 +304,9 @@ class YahooAdapter:
                 # other chunks returned. An all-empty result still raises below.
                 continue
             for ts, row in history.iterrows():
+                if not _is_priced_row(row):
+                    # No prices at all -> an absent bar, dropped at the seam (see _is_priced_row).
+                    continue
                 bar = RawBar(
                     sym,
                     timeframe,
diff --git a/apps/backend/app/research/bars.py b/apps/backend/app/research/bars.py
index e246fea..9ced136 100644
--- a/apps/backend/app/research/bars.py
+++ b/apps/backend/app/research/bars.py
@@ -38,13 +38,18 @@ Disciplines (each an anti-goal or a J-01 acceptance clause):
     recorded series for one symbol+timeframe, folded by timestamp). All go through the SAME verified
     load — projections of verified content, never a second, unverified read path.
   * **Honest failure states.** Unknown id -> ``BarSeriesNotFound``; an empty fetched window ->
-    ``EmptyBarWindowError`` (nothing written, nothing fabricated).
+    ``EmptyBarWindowError`` (nothing written, nothing fabricated); a candle with no finite price ->
+    ``NonFiniteBarPriceError`` (era-desk-iter-4 audit B1 — the write-path rail that makes "a
+    priceless bar can never reach disk" structural rather than a per-caller convention; the read
+    side excludes any already-recorded priceless ROW from the merged view and reports it in
+    ``integrity_errors``, never touching the append-only file).
 """
 
 from __future__ import annotations
 
 import hashlib
 import json
+import math
 import time
 import uuid
 from dataclasses import dataclass
@@ -83,6 +88,21 @@ class EmptyBarWindowError(Exception):
     is fabricated."""
 
 
+class NonFiniteBarPriceError(Exception):
+    """A bar offered for recording carries a non-finite price (``NaN``/``inf``) in one of its OHLC
+    fields — an explicit refusal at the ONE write path; nothing is written.
+
+    A candle with no price is not a candle. Vendors emit such a row for a session that has not
+    traded yet (pandas ``NaN`` in every price column), and ``float(nan)`` succeeds silently — so
+    without this guard the append-only, checksummed store accepts a permanently priceless bar, and
+    JSON round-trips it through the non-standard ``NaN`` token into every reader as ``null``
+    (era-desk-iter-4 audit B1: that is how 60 series over 58 symbols were poisoned and how
+    ``/structure``'s candlestick chart was taken down). The adapter that knows what the vendor meant
+    drops the row first (``providers/adapters/yahoo.py::_is_priced_row``); THIS is the structural
+    backstop that makes "a priceless bar can never reach disk" true for every write path, present
+    and future."""
+
+
 def _canonical(obj: object) -> bytes:
     """The one canonical JSON encoding every checksum in this module hashes (stable across
     processes: sorted keys, no whitespace) — the SAME encoding ``research/datasets.py`` uses."""
@@ -114,6 +134,23 @@ def _bar_to_row(bar: RawBar) -> dict:
     }
 
 
+_PRICE_FIELDS = ("open", "high", "low", "close")
+
+
+def _has_finite_prices(row: dict) -> bool:
+    """Does ONE stored candle row carry a real, finite number in all four price fields?
+
+    The single predicate behind both halves of the priceless-bar rail: ``record`` REFUSES a row that
+    fails it (``NonFiniteBarPriceError`` — nothing reaches disk), and ``_merged_rows`` EXCLUDES a
+    row that fails it from the merged view while reporting it in ``integrity_errors`` (the 60 series
+    already on disk when the guard shipped — files never touched, since bar series are append-only
+    and are never deleted, re-tagged, or content-perturbed)."""
+    try:
+        return all(math.isfinite(float(row[field])) for field in _PRICE_FIELDS)
+    except (KeyError, TypeError, ValueError):
+        return False
+
+
 def _row_to_bar(symbol: str, timeframe: str, row: dict) -> RawBar:
     return RawBar(
         symbol, timeframe, row["ts"], row["open"], row["high"], row["low"], row["close"], row["volume"]
@@ -161,11 +198,14 @@ _RACY_WRITE_GUARD_SECONDS = 2.0
 
 
 # The merged-view memo behind ``BarStore.merged_candles``: key = (symbol, timeframe, the exact set of
-# contributing (series_id, content-checksum) pairs); value = (ascending merged rows, meta). Same
-# atomic single-key-assignment publish discipline as ``_VERIFIED_CACHE`` above. Because the key
-# names every contributing series AND its content checksum, ANY change to the recorded set (a new
-# fetch, a deleted file, a changed file) yields a different key -- a stale merge cannot be served.
-_MERGED_CACHE: dict[tuple, tuple[list[dict], dict]] = {}
+# contributing (series_id, content-checksum) pairs); value = (ascending merged rows, meta, the
+# per-series priceless-row reports excluded from that fold). Same atomic single-key-assignment
+# publish discipline as ``_VERIFIED_CACHE`` above. Because the key names every contributing series
+# AND its content checksum, ANY change to the recorded set (a new fetch, a deleted file, a changed
+# file) yields a different key -- a stale merge cannot be served. The priceless-row reports ride
+# ALONG in the cached value (rather than being recomputed, or routed through the uncacheable
+# ``errors`` set) so a pair holding one is memoized exactly like any other.
+_MERGED_CACHE: dict[tuple, tuple[list[dict], dict, list[dict]]] = {}
 
 
 def _slice_rows(
@@ -418,7 +458,8 @@ class BarStore:
         ``series_ids`` (every contributing series, oldest-created first), ``bar_count`` (the merged
         total available, not the slice length), ``revised_timestamps``, and ``integrity_errors``
         (a corrupt file is surfaced exactly as ``list`` surfaces it — never served as data, never
-        silently dropped from the merge)."""
+        silently dropped from the merge; a recorded row carrying no finite price is surfaced the
+        same way and excluded from the fold — see ``_merged_rows``)."""
         normalized_symbol = symbol.strip().upper()
         normalized_timeframe = timeframe.strip()
         merged, meta = self._merged_rows(normalized_symbol, normalized_timeframe)
@@ -436,7 +477,20 @@ class BarStore:
         new series, deleting one, or any content change produces a different key — a stale merge is
         not representable. Published with the SAME single-assignment discipline as
         ``_VERIFIED_CACHE`` above (see that block comment for the torn-read rationale). Nothing is
-        cached when a file fails verification, since the error set is part of the answer."""
+        cached when a file fails verification, since the error set is part of the answer.
+
+        PRICELESS ROWS (era-desk-iter-4 audit B1). A recorded row whose OHLC are not all finite
+        numbers carries no price at all, so it is excluded from the fold and reported in
+        ``integrity_errors`` — the same treatment, through the same registered channel, that a
+        corrupt FILE already gets ("never served as data, never silently dropped"). Excluding the
+        ROW rather than the whole file is deliberate: the 60 series that were recorded before
+        ``record``'s finite guard existed each hold ONE priceless row beside hundreds of real ones,
+        and quarantining whole files would silently change every band and level those real bars
+        support (measured: AAPL's support side moves). The files themselves are never touched — bar
+        series are append-only and are never deleted, re-tagged, or content-perturbed — so the
+        exclusion lives here, on the read that every chart and every analytic consumer shares. The
+        per-series report is part of the MEMOIZED value (not of ``errors``), so the fold stays
+        memoized for the affected pairs exactly as before."""
         if not self._root.exists():
             return [], {"series_ids": [], "bar_count": 0, "revised_timestamps": 0, "integrity_errors": []}
 
@@ -457,17 +511,31 @@ class BarStore:
         key = (symbol, timeframe, tuple((s.meta.get("id"), s.meta.get("checksum")) for s in contributing))
         cached = _MERGED_CACHE.get(key)  # read-local-reference-before-inspect
         if cached is not None and not errors:
-            return cached[0], {**cached[1], "integrity_errors": []}
+            return cached[0], {**cached[1], "integrity_errors": [dict(e) for e in cached[2]]}
 
         by_ts: dict[float, dict] = {}
         revised: set[float] = set()
+        priceless: list[dict] = []
         for loaded in contributing:
+            dropped = 0
             for row in loaded.rows:
+                if not _has_finite_prices(row):
+                    dropped += 1  # a row with no price is not a candle -- see the docstring
+                    continue
                 ts = row["ts"]
                 previous = by_ts.get(ts)
                 if previous is not None and previous != row:
                     revised.add(ts)
                 by_ts[ts] = row
+            if dropped:
+                priceless.append({
+                    "file": f"{loaded.meta.get('id')}.json",
+                    "error": (
+                        f"{dropped} recorded row(s) carry a non-finite price (no OHLC value at "
+                        f"all) — excluded from the merged {symbol} {timeframe} series; the file "
+                        f"itself is unchanged (bar series are append-only)"
+                    ),
+                })
         merged = [by_ts[ts] for ts in sorted(by_ts)]
         meta = {
             "series_ids": [s.meta.get("id") for s in contributing],
@@ -475,8 +543,8 @@ class BarStore:
             "revised_timestamps": len(revised),
         }
         if not errors:
-            _MERGED_CACHE[key] = (merged, meta)  # single atomic rebind
-        return merged, {**meta, "integrity_errors": errors}
+            _MERGED_CACHE[key] = (merged, meta, priceless)  # single atomic rebind
+        return merged, {**meta, "integrity_errors": errors + [dict(e) for e in priceless]}
 
     def load_bars(self, bar_series_id: str) -> list[RawBar]:
         """The stored candle series as typed ``RawBar`` records (verified load, exact stored
@@ -546,6 +614,20 @@ class BarStore:
         if not bars:
             raise EmptyBarWindowError("no bars in the requested window — nothing was recorded")
         rows = [_bar_to_row(bar) for bar in bars]
+        # The priceless-bar rail (era-desk-iter-4 audit B1): a candle with no finite price is not a
+        # candle, and this store is append-only — so the refusal has to happen BEFORE the write,
+        # never as a later repair. Checked here rather than in each caller so it holds for every
+        # write path (the /research/bars route, the desk top-up job, the CLI warmers, and anything
+        # added later); the offending timestamp is named so the operator can see which row the
+        # vendor served empty.
+        for row in rows:
+            if not _has_finite_prices(row):
+                raise NonFiniteBarPriceError(
+                    f"{symbol} {timeframe}: the bar at ts {row['ts']} carries a non-finite price "
+                    f"(open={row['open']!r} high={row['high']!r} low={row['low']!r} "
+                    f"close={row['close']!r}) — a bar with no price is not a bar, so nothing was "
+                    f"recorded"
+                )
         checksum = _content_checksum(symbol, timeframe, feed, rows)
         # Registration-time duplicate scan over the HEALTHY registry — the exact same series
         # content is never recorded twice.
diff --git a/apps/backend/app/research/desk_routes.py b/apps/backend/app/research/desk_routes.py
index 411be36..5027fdd 100644
--- a/apps/backend/app/research/desk_routes.py
+++ b/apps/backend/app/research/desk_routes.py
@@ -295,7 +295,34 @@ def trigger_desk_screen_compute(
     """Start the single-flight desk screen compute job for ``body.screen_date``, or — if one is
     already running — return it UNCHANGED (``started: False``, never a second concurrent job).
     Returns ``{"started": bool, "compute": <snapshot>}``; the actual walk runs on a background
-    worker thread, off this request, so this route returns immediately."""
+    worker thread, off this request, so this route returns immediately.
+
+    Refuses — 422, naming the missing universe, never starting a job or persisting anything — when
+    no universe snapshot is registered yet (mirrors the top-up CLI's own no-universe message,
+    ``desk_topup_compute.py:352-356``; closes audit B4: a screen run with no universe would
+    otherwise persist a permanent, useless honest-empty snapshot every time it's re-triggered).
+
+    ``UniverseStore.list()`` also reports ``records == []`` when snapshot FILES exist but every one
+    of them failed its integrity check, so the refusal names that cause separately rather than
+    telling the operator nothing is registered when something is (era-desk-iter-4 audit B2): the
+    action a damaged snapshot needs (look at the named file) is not the action an absent one needs
+    (fetch a universe)."""
+    records, errors = universe_store.list()
+    if not records:
+        if errors:
+            raise HTTPException(
+                status_code=422,
+                detail=(
+                    f"no READABLE universe snapshot is registered -- nothing to screen: "
+                    f"{len(errors)} snapshot file(s) failed their integrity check and are excluded "
+                    "(" + "; ".join(f"{e['file']}: {e['error']}" for e in errors) + ")"
+                ),
+            )
+        raise HTTPException(
+            status_code=422,
+            detail="no universe snapshot is registered -- nothing to screen (run "
+            "POST /research/desk/universe/fetch first)",
+        )
     return manager.trigger(
         body.screen_date, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store,
     )
diff --git a/apps/backend/app/research/desk_screen_compute.py b/apps/backend/app/research/desk_screen_compute.py
index 87bfa1e..c55e0ec 100644
--- a/apps/backend/app/research/desk_screen_compute.py
+++ b/apps/backend/app/research/desk_screen_compute.py
@@ -81,19 +81,25 @@ def run_screen_and_record(
     *,
     progress: Callable[[dict], None] | None = None,
     should_abort: Callable[[], bool] | None = None,
-) -> dict:
-    """Compute ONE screen (``compute_screen`` -- the sole walker) and persist it, append-only. If
-    an identical-pin screen is already recorded, the EXISTING snapshot's meta is returned (never a
-    second file, never a rewrite) rather than raising -- ``ScreenAlreadyRecorded`` is caught here,
-    not propagated, since reusing an already-recorded snapshot is a normal, expected outcome, not a
-    failure. A cancelled (partial) walk is NEVER recorded -- returns ``None`` instead (the caller
-    distinguishes "cancelled, nothing recorded" from "recorded/reused" by this ``None`` check)."""
+) -> tuple[dict | None, bool]:
+    """Compute ONE screen (``compute_screen`` -- the sole walker) and persist it, append-only.
+    Returns ``(record, reused)``:
+
+      * a cancelled (partial) walk is NEVER recorded -- returns ``(None, False)`` (the caller
+        distinguishes "cancelled, nothing recorded" from "recorded/reused" by the ``None`` check);
+      * a freshly-persisted snapshot returns ``(record, False)``;
+      * an identical-pin screen already recorded returns the EXISTING snapshot's meta with
+        ``(record, True)`` (never a second file, never a rewrite) -- ``ScreenAlreadyRecorded`` is
+        caught here, not propagated, since reusing an already-recorded snapshot is a normal,
+        expected outcome, not a failure (era-desk-iter-4 J-04, audit B2: this ``reused`` flag is
+        what lets a caller distinguish "this job's walk is what created the snapshot" from "this
+        job's walk found an already-recorded one and changed nothing")."""
     result = compute_screen(
         universe_store, bar_store, bar_index, dataset_store, config, screen_date,
         progress=progress, should_abort=should_abort,
     )
     if should_abort is not None and should_abort():
-        return None
+        return None, False
     try:
         return screen_store.record(
             screen_date=result["screen_date"],
@@ -103,14 +109,14 @@ def run_screen_and_record(
             bar_store_signature=result["bar_store_signature"],
             rows=result["rows"],
             skipped=result["skipped"],
-        )
+        ), False
     except ScreenAlreadyRecorded as exc:
         existing = screen_store.find_by_key(
             result["screen_date"], result["as_of"], result["universe_snapshot_id"],
             result["config_fingerprint"], result["bar_store_signature"],
         )
         assert existing is not None and existing["id"] == exc.existing_id
-        return existing
+        return existing, True
 
 
 class DeskScreenComputeManager:
@@ -166,6 +172,10 @@ class DeskScreenComputeManager:
                 "started_utc": _iso_utc_now(),
                 "finished_utc": None,
                 "error": None,
+                # era-desk-iter-4 J-04 (audit B2): honest until a terminal state resolves --
+                # "initial/running: reused false, screen_id null" (nothing recorded yet).
+                "reused": False,
+                "screen_id": None,
                 "progress": {"members_total": members_total, "members_done": 0, "current": None},
             }
             self._snapshot = snapshot
@@ -186,14 +196,26 @@ class DeskScreenComputeManager:
 
         def _work() -> None:
             try:
-                run_screen_and_record(
+                record, reused = run_screen_and_record(
                     universe_store, bar_store, bar_index, dataset_store, config, screen_store,
                     screen_date, progress=_publish, should_abort=cancel_event.is_set,
                 )
             except Exception as exc:  # noqa: BLE001 -- surfaced verbatim, never swallowed
                 self._resolve(job_id, "failed", error=str(exc))
                 return
-            self._resolve(job_id, "cancelled" if cancel_event.is_set() else "done", error=None)
+            # ``record is None`` means the walk observed the cancel BEFORE persisting anything, so
+            # `screen_id`/`reused` fall out to null/False -- nothing was recorded.
+            #
+            # The converse does NOT hold, and the snapshot deliberately reports the truth rather
+            # than the tidier rule (era-desk-iter-4 audit B3): a cancel that lands in the window
+            # between `run_screen_and_record`'s own should_abort() check and this line resolves
+            # `state: "cancelled"` WITH a non-null `screen_id` (and `reused: true` if that pin was
+            # already on file). Something really was recorded in that race, and saying so is more
+            # honest than reporting null for a snapshot the operator can go and read.
+            self._resolve(
+                job_id, "cancelled" if cancel_event.is_set() else "done", error=None,
+                reused=reused, screen_id=record["id"] if record is not None else None,
+            )
 
         thread = threading.Thread(target=_work, name=f"desk-screen-compute:{job_id}", daemon=True)
         with self._lock:
@@ -201,12 +223,18 @@ class DeskScreenComputeManager:
         thread.start()
         return {"started": True, "compute": _copy_snapshot(snapshot)}
 
-    def _resolve(self, job_id: str, state: str, *, error: str | None) -> None:
+    def _resolve(
+        self, job_id: str, state: str, *, error: str | None,
+        reused: bool = False, screen_id: str | None = None,
+    ) -> None:
         with self._lock:
             current = self._snapshot
             if current is None or current["id"] != job_id:
                 return  # superseded -- never resolve a job that is no longer the current one
-            self._snapshot = {**current, "state": state, "finished_utc": _iso_utc_now(), "error": error}
+            self._snapshot = {
+                **current, "state": state, "finished_utc": _iso_utc_now(), "error": error,
+                "reused": reused, "screen_id": screen_id,
+            }
 
     def cancel(self) -> None:
         """Signal cooperative cancellation for the in-flight job -- a harmless no-op if idle (the
@@ -263,13 +291,14 @@ def main() -> int:
     dataset_store = get_dataset_store()
     screen_store = ScreenStore(resolve_desk_screen_dir(config.desk_universe_dir_resolved()))
 
-    recorded = run_screen_and_record(
+    recorded, reused = run_screen_and_record(
         universe_store, bar_store, bar_index, dataset_store, config, screen_store,
         args.date, progress=_cli_progress_printer(),
     )
     print(
         f"desk screen complete for {args.date}: {len(recorded['rows'])} ranked, "
-        f"{len(recorded['skipped'])} skipped -- snapshot {recorded['id']}."
+        f"{len(recorded['skipped'])} skipped -- snapshot {recorded['id']} "
+        f"({'reused existing' if reused else 'newly recorded'})."
     )
     return 0
 
diff --git a/apps/backend/app/research/desk_universe.py b/apps/backend/app/research/desk_universe.py
index a2efbd0..b196c49 100644
--- a/apps/backend/app/research/desk_universe.py
+++ b/apps/backend/app/research/desk_universe.py
@@ -400,6 +400,22 @@ class UniverseStore:
 
         date = datetime.now(timezone.utc).date().isoformat()
         snapshot_id = f"universe-{date}-{checksum}"
+        # A file already at this snapshot id's own path, with the duplicate-checksum scan above
+        # finding no match, means exactly one thing: that file failed its integrity check (`list`
+        # surfaces it in `integrity_errors` and withholds it from `existing`), because the path is
+        # a deterministic function of (today's date, content checksum) and the scan above already
+        # covers every OTHER already-registered snapshot's checksum. Writing here would SILENTLY
+        # overwrite a corrupted/tampered snapshot and erase the very integrity error the store had
+        # been honestly surfacing -- both a rewrite ("snapshots are append-only ... never
+        # rewritten") and a silence. Refuse loudly instead; a human decides what happens to the
+        # damaged file (mirrors ``desk_screen.ScreenStore.record``'s identical guard).
+        if self._path(snapshot_id).exists():
+            raise UniverseIntegrityError(
+                f"universe snapshot file '{self._path(snapshot_id).name}' already exists on disk "
+                f"but failed its integrity check -- refusing to overwrite it (universe snapshots "
+                f"are append-only and are never rewritten). Move or remove the damaged file "
+                f"explicitly before re-recording this key."
+            )
         meta = {
             "id": snapshot_id,
             "date": date,
diff --git a/apps/backend/app/research/routes.py b/apps/backend/app/research/routes.py
index f9d140e..8251e4a 100644
--- a/apps/backend/app/research/routes.py
+++ b/apps/backend/app/research/routes.py
@@ -43,6 +43,7 @@ from .bars import (
     BarSeriesNotFound,
     BarStore,
     EmptyBarWindowError,
+    NonFiniteBarPriceError,
 )
 from .edge_report import EdgeReportError, peek_strategy_comparison_report
 from .edge_report_backtest_cache import EdgeReportBacktestCache, resolve_backtest_cache_db_path
@@ -691,6 +692,12 @@ def record_bar_series(
         raise HTTPException(status_code=409, detail=str(exc))
     except EmptyBarWindowError as exc:
         raise HTTPException(status_code=422, detail=str(exc))
+    except NonFiniteBarPriceError as exc:
+        # The store's priceless-bar rail refused the write (era-desk-iter-4 audit B1). Unreachable
+        # through a Yahoo fetch now that the adapter drops such rows at the vendor seam, so this maps
+        # the OTHER adapters' (and any future caller's) case to the same honest 422 the empty-window
+        # refusal uses — a caller-visible refusal naming the row, never an opaque 500.
+        raise HTTPException(status_code=422, detail=str(exc))
     # Era-5 J-03: additively index the freshly-recorded series ONLY after store.record succeeds —
     # using the returned meta dict's fields (the values that actually got written), never
     # re-derived from the request body.
diff --git a/apps/backend/tests/test_bars.py b/apps/backend/tests/test_bars.py
index 7bdfef5..cf7c91f 100644
--- a/apps/backend/tests/test_bars.py
+++ b/apps/backend/tests/test_bars.py
@@ -26,6 +26,10 @@ from app.research.bars import (
     BarSeriesNotFound,
     BarStore,
     EmptyBarWindowError,
+    NonFiniteBarPriceError,
+    _canonical,
+    _content_checksum,
+    _sha256,
 )
 
 FIXTURE_BAR_DIR = Path(__file__).parent / "fixtures" / "bars"
@@ -195,6 +199,143 @@ def test_empty_bar_list_is_an_explicit_refusal(tmp_path):
     assert records == [] and errors == []
 
 
+# --- the priceless-bar rail (era-desk-iter-4 audit B1) -------------------------------------------
+# A candle with no finite price is not a candle. `record` REFUSES one (nothing reaches disk); the
+# merged read EXCLUDES any already-recorded priceless ROW and reports it in `integrity_errors`,
+# never touching the append-only file. Both halves matter: the write guard stops the bleeding, the
+# read guard is what makes the 60 series poisoned before it existed harmless (58 symbols, incl. the
+# era's pinned AAPL, each holding ONE priceless row beside hundreds of real bars -- quarantining
+# whole FILES would silently move every band those real bars support).
+
+
+@pytest.mark.parametrize("field", ["open", "high", "low", "close"])
+@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
+def test_record_refuses_a_bar_carrying_a_non_finite_price(tmp_path, field, bad):
+    store = BarStore(tmp_path / "bars")
+    prices = {"o": 148.0, "h": 149.5, "l": 147.5, "c": 149.0}
+    prices[{"open": "o", "high": "h", "low": "l", "close": "c"}[field]] = bad
+    poisoned = _bar(
+        "PG", "1d", datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp(),
+        prices["o"], prices["h"], prices["l"], prices["c"], 1_000_000,
+    )
+    with pytest.raises(NonFiniteBarPriceError) as exc_info:
+        store.record(
+            symbol="PG", timeframe="1d", window_start_utc=WINDOW_START, window_end_utc=WINDOW_END,
+            feed="yahoo", bars=[poisoned],
+        )
+    assert "PG 1d" in str(exc_info.value)
+    # Nothing reached disk: not a file, not a registry row, not an integrity error.
+    assert store.list() == ([], [])
+    assert not (tmp_path / "bars").exists() or list((tmp_path / "bars").glob("*.json")) == []
+
+
+def test_record_refuses_the_whole_series_when_only_one_bar_is_priceless(tmp_path):
+    # The real vendor shape: hundreds of good bars plus ONE not-yet-traded row. The refusal is
+    # per-SERIES (nothing partially recorded) so the caller drops the bad row and re-records.
+    store = BarStore(tmp_path / "bars")
+    bars = _small_daily_series("PG") + [
+        _bar("PG", "1d", datetime(2026, 6, 4, tzinfo=timezone.utc).timestamp(),
+             float("nan"), float("nan"), float("nan"), float("nan"), 47402209)
+    ]
+    with pytest.raises(NonFiniteBarPriceError):
+        store.record(
+            symbol="PG", timeframe="1d", window_start_utc=WINDOW_START, window_end_utc=WINDOW_END,
+            feed="yahoo", bars=bars,
+        )
+    assert store.list() == ([], [])
+
+
+def _plant_priceless_row(store: BarStore, meta: dict) -> float:
+    """Rewrite an ALREADY-recorded series' file with one APPENDED priceless row and BOTH checksums
+    recomputed — reproducing the exact on-disk state of the 60 series written before ``record``'s
+    finite guard existed (a fully VALID file, both checksums correct, holding a row whose OHLC are
+    the JSON ``NaN`` token). It cannot go through ``record`` any more, which is the point.
+    Returns the planted row's timestamp."""
+    path = store.root / f"{meta['id']}.json"
+    payload = json.loads(path.read_text())
+    record = payload["record"]
+    rows = record["bars"]
+    priceless_ts = rows[-1]["ts"] + 86400.0
+    rows.append({
+        "ts": priceless_ts, "open": float("nan"), "high": float("nan"),
+        "low": float("nan"), "close": float("nan"), "volume": 47402209,
+    })
+    record["meta"]["bar_count"] = len(rows)
+    record["meta"]["checksum"] = _content_checksum(
+        record["meta"]["symbol"], record["meta"]["timeframe"], record["meta"]["feed"], rows
+    )
+    payload["file_checksum"] = _sha256(_canonical(record))
+    path.write_text(json.dumps(payload))
+    return priceless_ts
+
+
+def test_a_planted_priceless_series_still_passes_both_checksums(tmp_path):
+    # Guard on the guard: the planted file is NOT a corrupt file (that path is already covered).
+    # It verifies cleanly and is served by every per-series read verbatim — the stored truth.
+    store = BarStore(tmp_path / "bars")
+    meta = _record_small_series(store)
+    priceless_ts = _plant_priceless_row(store, meta)
+    records, errors = store.list()
+    assert errors == [] and len(records) == 1
+    assert [row["ts"] for row in records[0]["bars"]][-1] == priceless_ts
+    assert len(store.get(meta["id"])["bars"]) == 4
+
+
+def test_merged_read_excludes_a_recorded_priceless_row_and_reports_it(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    meta = _record_small_series(store)
+    clean_rows, _hb, _ha, clean_meta = store.merged_candles("PG", "1d", limit=500)
+    assert len(clean_rows) == 3 and clean_meta["integrity_errors"] == []
+
+    priceless_ts = _plant_priceless_row(store, meta)
+
+    rows, _hb, _ha, merged_meta = store.merged_candles("PG", "1d", limit=500)
+    # The priceless row contributes NOTHING, and every real bar is byte-identical to before.
+    assert rows == clean_rows
+    assert priceless_ts not in [row["ts"] for row in rows]
+    assert merged_meta["bar_count"] == 3
+    assert merged_meta["series_ids"] == [meta["id"]]
+    # ...and it is REPORTED, through the same registered channel a corrupt file uses.
+    assert len(merged_meta["integrity_errors"]) == 1
+    reported = merged_meta["integrity_errors"][0]
+    assert reported["file"] == f"{meta['id']}.json"
+    assert "1 recorded row(s) carry a non-finite price" in reported["error"]
+    assert "the file itself is unchanged" in reported["error"]
+    # The typed analytic view (levels/tradability/desk screen read THIS) agrees exactly.
+    assert [bar.epoch for bar in store.merged_bars("PG", "1d")] == [row["ts"] for row in clean_rows]
+
+
+def test_excluding_a_priceless_row_never_touches_the_append_only_file(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    meta = _record_small_series(store)
+    _plant_priceless_row(store, meta)
+    path = tmp_path / "bars" / f"{meta['id']}.json"
+    before = path.read_bytes()
+
+    store.merged_candles("PG", "1d", limit=500)
+    store.merged_bars("PG", "1d")
+    store.get(meta["id"])
+    store.list()
+
+    assert path.read_bytes() == before  # append-only: never deleted, re-tagged, or perturbed
+
+
+def test_the_merged_fold_stays_memoized_for_a_pair_holding_a_priceless_row(tmp_path):
+    # The priceless report rides ALONG in the memoized value rather than through the uncacheable
+    # `errors` set, so an affected pair is not re-folded on every read — and, critically, the
+    # cache-HIT path reports the exclusion exactly as the cache-miss path did.
+    store = BarStore(tmp_path / "bars")
+    meta = _record_small_series(store)
+    _plant_priceless_row(store, meta)
+
+    first_rows, first_meta = store._merged_rows("PG", "1d")
+    second_rows, second_meta = store._merged_rows("PG", "1d")
+
+    assert second_rows is first_rows  # the memo served the identical folded list
+    assert second_meta["integrity_errors"] == first_meta["integrity_errors"]
+    assert len(second_meta["integrity_errors"]) == 1
+
+
 # --- the committed miniature multi-timeframe fixture (keyless CI proof) --------------------------
 
 
diff --git a/apps/backend/tests/test_bars_api.py b/apps/backend/tests/test_bars_api.py
index 47e62c8..2e83bf0 100644
--- a/apps/backend/tests/test_bars_api.py
+++ b/apps/backend/tests/test_bars_api.py
@@ -570,6 +570,45 @@ def test_merged_read_surfaces_a_corrupted_file_instead_of_merging_it(ctx):
     assert f"{corrupt['id']}.json" == body["integrity_errors"][0]["file"]
 
 
+def test_merged_read_never_serves_a_null_priced_candle(ctx):
+    """era-desk-iter-4 audit B1, at the exact chokepoint that took ``/structure`` down: this is the
+    endpoint the Tradable-Map candlestick chart pages, and JSON serves a stored ``NaN`` price as
+    ``null``. A priceless row already on disk must be excluded from the served window and reported
+    — never handed to the chart as a candle whose open is ``null``."""
+    client, bar_dir = ctx
+    series = _record_window(client, first_index=0, count=5)
+    path = bar_dir / f"{series['id']}.json"
+    payload = json.loads(path.read_text())
+    record = payload["record"]
+    record["bars"].append({
+        "ts": _BASE_EPOCH + 5 * _DAY, "open": float("nan"), "high": float("nan"),
+        "low": float("nan"), "close": float("nan"), "volume": 47402209,
+    })
+    record["meta"]["bar_count"] = len(record["bars"])
+    # Both checksums recomputed: this is a VALID file holding a priceless row (exactly the state of
+    # the 60 real series), not a corrupt file — that case is covered separately above.
+    from app.research.bars import _canonical, _content_checksum, _sha256
+
+    record["meta"]["checksum"] = _content_checksum(
+        record["meta"]["symbol"], record["meta"]["timeframe"], record["meta"]["feed"], record["bars"]
+    )
+    payload["file_checksum"] = _sha256(_canonical(record))
+    path.write_text(json.dumps(payload))
+
+    body = client.get(
+        "/research/candles", params={"symbol": SYMBOL, "timeframe": TIMEFRAME, "limit": 500}
+    ).json()
+
+    assert body["bar_count"] == 5
+    assert [row["ts"] for row in body["bars"]] == [_BASE_EPOCH + i * _DAY for i in range(5)]
+    for row in body["bars"]:
+        for field in ("open", "high", "low", "close"):
+            assert row[field] is not None
+    assert len(body["integrity_errors"]) == 1
+    assert body["integrity_errors"][0]["file"] == f"{series['id']}.json"
+    assert "non-finite price" in body["integrity_errors"][0]["error"]
+
+
 def test_merged_read_reflects_a_newly_recorded_series_immediately(ctx):
     """The fold is memoized; the memo key names every contributing series AND its checksum, so a
     fresh recording can never be served a stale merge."""
diff --git a/apps/backend/tests/test_desk_screen_compute.py b/apps/backend/tests/test_desk_screen_compute.py
index 5dbaa4c..889e8f9 100644
--- a/apps/backend/tests/test_desk_screen_compute.py
+++ b/apps/backend/tests/test_desk_screen_compute.py
@@ -360,10 +360,11 @@ def real_ctx(tmp_path):
 
 def test_first_run_screen_and_record_persists_a_new_snapshot(real_ctx):
     universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
-    recorded = run_screen_and_record(
+    recorded, reused = run_screen_and_record(
         universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
     )
     assert recorded is not None
+    assert reused is False
     assert any(r["symbol"] == "AAPL" for r in recorded["rows"])
     records, errors = screen_store.list()
     assert errors == [] and len(records) == 1 and records[0]["id"] == recorded["id"]
@@ -371,15 +372,17 @@ def test_first_run_screen_and_record_persists_a_new_snapshot(real_ctx):
 
 def test_second_run_with_identical_pins_reuses_the_existing_snapshot_no_second_file(real_ctx, tmp_path):
     """TC-4: the manager/store returns the EXISTING snapshot (same id) rather than writing a
-    second file."""
+    second file -- and (era-desk-iter-4) the second call's own ``reused`` flag says so."""
     universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
-    first = run_screen_and_record(
+    first, first_reused = run_screen_and_record(
         universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
     )
-    second = run_screen_and_record(
+    second, second_reused = run_screen_and_record(
         UniverseStore(universe_store.root), BarStore(bar_store.root), BarIndex(bar_index.db_path),
         DatasetStore(tmp_path / "datasets"), CONFIG, screen_store, SCREEN_DATE,
     )
+    assert first_reused is False
+    assert second_reused is True
     assert second["id"] == first["id"]
     records, errors = screen_store.list()
     assert errors == [] and len(records) == 1  # no second file
@@ -387,18 +390,94 @@ def test_second_run_with_identical_pins_reuses_the_existing_snapshot_no_second_f
 
 def test_cancel_before_the_walk_starts_returns_none_and_records_nothing(real_ctx):
     universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
-    result = run_screen_and_record(
+    result, reused = run_screen_and_record(
         universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
         should_abort=lambda: True,
     )
     assert result is None
+    assert reused is False
     records, _errors = screen_store.list()
     assert records == []
 
 
 # ==================================================================================================
-# Routes -- honest-empty (TC-5), ?date= (TC-6), 422 on missing screen_date (TC-9), GET-never-
-# computes, single-flight/cancel through HTTP, idle-cancel 409.
+# era-desk-iter-4 (J-04, audit B2): the manager's own `reused`/`screen_id` fields, resolved through
+# a full `trigger()` -> terminal-snapshot round trip against the REAL `compute_screen` (real
+# fixture universe, real AAPL bars) -- distinct from the manager-mechanics section above, which
+# fakes `compute_screen` for timing control and never asserted these two fields.
+# ==================================================================================================
+
+
+def test_trigger_resolves_reused_false_and_its_own_screen_id_on_a_fresh_compute(real_ctx):
+    """TC-8."""
+    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
+    mgr = DeskScreenComputeManager()
+    mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
+    snap = _wait_for_terminal(mgr)
+    mgr.join_all(timeout=5)
+
+    assert snap["state"] == "done"
+    assert snap["reused"] is False
+    assert snap["screen_id"] is not None
+    records, _errors = screen_store.list()
+    assert records[0]["id"] == snap["screen_id"]
+
+
+def test_trigger_resolves_reused_true_and_the_existing_screen_id_on_a_repeat_compute(real_ctx):
+    """TC-7."""
+    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
+    first_mgr = DeskScreenComputeManager()
+    first_mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
+    first_snap = _wait_for_terminal(first_mgr)
+    first_mgr.join_all(timeout=5)
+    assert first_snap["reused"] is False
+
+    second_mgr = DeskScreenComputeManager()
+    second_mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
+    second_snap = _wait_for_terminal(second_mgr)
+    second_mgr.join_all(timeout=5)
+
+    assert second_snap["state"] == "done"
+    assert second_snap["reused"] is True
+    assert second_snap["screen_id"] == first_snap["screen_id"]
+    records, errors = screen_store.list()
+    assert errors == [] and len(records) == 1  # no second file
+
+
+def test_initial_and_running_snapshot_carry_the_honest_reused_false_screen_id_null_defaults(
+    manager_env, monkeypatch,
+):
+    """Initial/running state: ``reused: false``, ``screen_id: null`` -- nothing recorded yet."""
+    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
+    started = threading.Event()
+    release = threading.Event()
+
+    def fake_compute_screen(*_args, **_kwargs):
+        started.set()
+        release.wait(timeout=5)
+        return {
+            "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z",
+            "universe_snapshot_id": "x", "config_fingerprint": "y", "bar_store_signature": "z",
+            "rows": [], "skipped": [],
+        }
+
+    monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)
+
+    mgr = DeskScreenComputeManager()
+    result = mgr.trigger(
+        SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store,
+    )
+    assert result["compute"]["reused"] is False
+    assert result["compute"]["screen_id"] is None
+    assert started.wait(timeout=5)
+    release.set()
+    _wait_for_terminal(mgr)
+    mgr.join_all(timeout=5)
+
+
+# ==================================================================================================
+# Routes -- honest-empty (TC-5), ?date= (TC-6), 422 on missing screen_date, GET-never-computes,
+# single-flight/cancel through HTTP, idle-cancel 409, no-universe refusal (era-desk-iter-4 TC-9).
 # ==================================================================================================
 
 
@@ -407,6 +486,11 @@ def route_ctx(tmp_path, monkeypatch):
     monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
     monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
     monkeypatch.setenv("TAPEOLOGY_DESK_SCREEN_DIR", str(tmp_path / "screen"))
+    # era-desk-iter-4 (closes audit T3): the ONE `route_ctx` among this file's siblings that read
+    # the ambient `.data/datasets` tree instead of a temp dir -- `trigger_desk_screen_compute`
+    # reads `dataset_store` for the tick-evidence badge via `get_dataset_store()`, which resolves
+    # `TAPEOLOGY_DATASET_DIR` (unscoped here, previously) or else the real on-disk default.
+    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
     store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
     registry = ResearchRegistry(store, CONFIG)
     set_registry(registry)
@@ -447,12 +531,66 @@ def test_get_screen_compute_before_any_trigger_is_an_honest_null_and_starts_noth
 
 
 def test_post_trigger_missing_screen_date_is_422(route_ctx):
-    """TC-9: the endpoint never defaults to the current wall-clock date."""
+    """The endpoint never defaults to the current wall-clock date."""
     client, _mgr, _tmp_path = route_ctx
     r = client.post("/research/desk/screen/compute", json={})
     assert r.status_code == 422
 
 
+def test_post_trigger_with_no_universe_registered_refuses_and_persists_nothing(route_ctx):
+    """era-desk-iter-4 TC-9 (closes audit B4): a screen compute must refuse -- never persist a
+    permanent, useless honest-empty snapshot -- when no universe snapshot is registered."""
+    client, fresh_manager, _tmp_path = route_ctx
+    before = client.get("/research/desk/screen").json()
+    assert before == {"screens": [], "latest": None, "integrity_errors": []}
+
+    r = client.post("/research/desk/screen/compute", json={"screen_date": SCREEN_DATE})
+    assert r.status_code == 422
+    assert "universe" in r.json()["detail"]
+
+    after = client.get("/research/desk/screen").json()
+    assert after == {"screens": [], "latest": None, "integrity_errors": []}
+    # No background job was even started.
+    assert fresh_manager.snapshot() is None
+    # The absent-universe wording names the action that fixes it, and does NOT claim a file problem.
+    assert "no universe snapshot is registered" in r.json()["detail"]
+    assert "POST /research/desk/universe/fetch" in r.json()["detail"]
+
+
+def test_post_trigger_refusal_names_a_damaged_universe_snapshot_rather_than_claiming_none_exists(
+    route_ctx,
+):
+    """era-desk-iter-4 audit B2: ``UniverseStore.list()`` also reports ``records == []`` when
+    snapshot FILES exist but every one failed its integrity check. The refusal is right either way,
+    but the two causes need different operator actions, so the message must distinguish them
+    instead of saying "nothing is registered" about a universe that IS registered (and damaged)."""
+    client, fresh_manager, tmp_path = route_ctx
+    universe_dir = tmp_path / "universe"
+    snapshot = UniverseStore(universe_dir).record(
+        members=["AAA"], raw_members={"AAA": "AAA"},
+        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
+    )
+    path = universe_dir / f"{snapshot['id']}.json"
+    payload = json.loads(path.read_text())
+    payload["record"]["meta"]["member_count"] = 999  # tamper -- the file checksum now disagrees
+    path.write_text(json.dumps(payload))
+    records, errors = UniverseStore(universe_dir).list()
+    assert records == [] and len(errors) == 1  # the precondition this finding is about
+
+    r = client.post("/research/desk/screen/compute", json={"screen_date": SCREEN_DATE})
+
+    assert r.status_code == 422
+    detail = r.json()["detail"]
+    assert "no READABLE universe snapshot is registered" in detail
+    assert "integrity check" in detail
+    assert f"{snapshot['id']}.json" in detail  # the operator is told WHICH file to look at
+    assert "POST /research/desk/universe/fetch" not in detail  # not the action this cause needs
+    assert fresh_manager.snapshot() is None
+    assert client.get("/research/desk/screen").json() == {
+        "screens": [], "latest": None, "integrity_errors": [],
+    }
+
+
 def test_post_trigger_runs_to_completion_and_get_polls_the_same_snapshot(route_ctx):
     client, _mgr, tmp_path = route_ctx
     UniverseStore(tmp_path / "universe").record(
diff --git a/apps/backend/tests/test_desk_universe.py b/apps/backend/tests/test_desk_universe.py
index a8ec0fc..1c2d2b3 100644
--- a/apps/backend/tests/test_desk_universe.py
+++ b/apps/backend/tests/test_desk_universe.py
@@ -286,6 +286,32 @@ def test_load_raises_universe_integrity_error_for_unparseable_json(tmp_path):
     assert len(errors) == 1
 
 
+def test_recording_over_a_corrupted_file_at_the_same_key_is_refused_never_a_silent_overwrite(tmp_path):
+    """iter-4 (closes audit B3 / iter-3's lesson): mirrors
+    ``test_desk_screen.py``'s ``test_recording_over_a_corrupted_file_at_the_same_key_is_refused_never_a_silent_overwrite``
+    for ``UniverseStore``. A tampered snapshot is withheld from ``records`` (surfaced in
+    ``integrity_errors``), so the duplicate-checksum scan in ``record`` cannot see it -- but the
+    file's PATH is a deterministic function of (today's date, content checksum), so a re-record of
+    the SAME membership on the SAME day lands on the SAME file. ``record`` must refuse explicitly:
+    never silently overwrite a damaged snapshot (a rewrite -- "snapshots are append-only ... never
+    rewritten"), and never erase the integrity error the store was honestly surfacing."""
+    universe_dir = tmp_path / "universe"
+    store = UniverseStore(universe_dir)
+    _record_fixture(store)
+    path = next(universe_dir.glob("*.json"))
+    data = json.loads(path.read_text())
+    data["record"]["meta"]["member_count"] = 999  # tamper -- file_checksum now disagrees
+    path.write_text(json.dumps(data))
+    tampered_bytes = path.read_bytes()
+
+    with pytest.raises(UniverseIntegrityError) as excinfo:
+        _record_fixture(store)
+    assert path.name in str(excinfo.value)
+    assert path.read_bytes() == tampered_bytes
+    records, errors = store.list()
+    assert records == [] and len(errors) == 1  # still surfaced, not silently healed
+
+
 # --- T-3 guard: the universe store never routes through the dataset store -----------------------
 
 
diff --git a/apps/backend/tests/test_meta_routes.py b/apps/backend/tests/test_meta_routes.py
index 319c45a..dbe7eb3 100644
--- a/apps/backend/tests/test_meta_routes.py
+++ b/apps/backend/tests/test_meta_routes.py
@@ -11,6 +11,10 @@ now lists exactly the two KEPT routes, Cockpit and Structure. The dropped
 ``test_ui_routes_includes_performance_now_its_page_ships`` and
 ``test_ui_routes_represents_journal_detail_honestly`` asserted routes that no longer exist.
 
+Era B "The Desk" J-04 (this iteration): the third row, ``/desk``, ships in the SAME iteration as
+its page (this file's own documented "route ships WITH its test update" precedent) — the
+route-count assertions below widen from two to three, in nav order.
+
 Uses a lifespan-less ``TestClient`` (the existing ``test_api.py`` precedent): the meta router
 has no registry/engine dependencies, so no store injection is needed.
 """
@@ -23,13 +27,14 @@ client = TestClient(app)
 
 
 def test_ui_routes_lists_exactly_the_live_routes():
-    """The payload is byte-stable and lists exactly the two live routes, in nav order."""
+    """The payload is byte-stable and lists exactly the three live routes, in nav order."""
     response = client.get("/meta/ui-routes")
     assert response.status_code == 200
     assert response.json() == {
         "routes": [
             {"path": "/", "label": "Cockpit", "nav": True},
             {"path": "/structure", "label": "Structure", "nav": True},
+            {"path": "/desk", "label": "Desk", "nav": True},
         ]
     }
 
@@ -55,12 +60,23 @@ def test_ui_routes_includes_structure_now_its_page_ships():
 
 
 def test_ui_routes_top_bar_entries_match_the_rendered_nav_set():
-    """The nav filters ``nav: true`` — exactly Cockpit / Structure (two entries in the map, both
-    top-bar destinations, per era-5D J-02's demolition of the journal/studies/performance rows)."""
+    """The nav filters ``nav: true`` — exactly Cockpit / Structure / Desk (three entries in the
+    map, all top-bar destinations, per era-B J-04 appending the ``/desk`` row)."""
     routes = client.get("/meta/ui-routes").json()["routes"]
     top_bar = [(r["path"], r["label"]) for r in routes if r["nav"]]
-    assert len(routes) == 2
+    assert len(routes) == 3
     assert top_bar == [
         ("/", "Cockpit"),
         ("/structure", "Structure"),
+        ("/desk", "Desk"),
     ]
+
+
+def test_ui_routes_includes_desk_now_its_page_ships():
+    """Era B J-04 (this iteration) ships /desk WITH its nav entry (page and entry land in the SAME
+    iteration — the no-dead-link rule): exactly one ``/desk`` entry, labeled Desk, nav-true —
+    mirrors ``test_ui_routes_includes_structure_now_its_page_ships`` above."""
+    routes = client.get("/meta/ui-routes").json()["routes"]
+    desk = [r for r in routes if r["path"] == "/desk"]
+    assert len(desk) == 1
+    assert desk[0] == {"path": "/desk", "label": "Desk", "nav": True}
diff --git a/apps/backend/tests/test_structure_chart_viewport.py b/apps/backend/tests/test_structure_chart_viewport.py
index cb5e4ae..93bf3ac 100644
--- a/apps/backend/tests/test_structure_chart_viewport.py
+++ b/apps/backend/tests/test_structure_chart_viewport.py
@@ -191,7 +191,11 @@ def test_window_changes_preserve_the_visible_range():
     code = _code(STRUCTURE_CHART)
     assert "getVisibleLogicalRange()" in code
     assert re.search(r"anchor\s*=", code), "expected a remembered anchor bar"
-    assert "bars.findIndex((b) => b.ts === anchor.ts)" in code, (
+    # The array named here is whatever the component actually FED the library (era-desk-iter-4 audit
+    # B1 renamed it `drawableBars` — the finite-price-filtered view — so the anchor index and the
+    # library's own logical index stay the same number). The invariant under test is unchanged: the
+    # anchor is re-located by TIMESTAMP, never by a row count.
+    assert re.search(r"\w*[Bb]ars\.findIndex\(\(b\) => b\.ts === anchor\.ts\)", code), (
         "the anchor must be re-located by timestamp, not by a row count"
     )
     assert "anchor.offset" in code, "the anchor's offset from the range's left edge must be kept"
diff --git a/apps/backend/tests/test_yahoo_adapter.py b/apps/backend/tests/test_yahoo_adapter.py
index 5433812..d629445 100644
--- a/apps/backend/tests/test_yahoo_adapter.py
+++ b/apps/backend/tests/test_yahoo_adapter.py
@@ -11,6 +11,7 @@ fetched live and frozen) so the mocked response is genuinely Yahoo-shaped, not a
 from __future__ import annotations
 
 import json
+import math
 from datetime import datetime, timedelta, timezone
 from pathlib import Path
 
@@ -182,6 +183,96 @@ def test_fetch_bars_raises_no_data_for_window_for_an_empty_vendor_response(monke
     assert "window" in str(exc_info.value)
 
 
+# --- the priceless-row rail (era-desk-iter-4 audit B1) -----------------------------------------
+# Yahoo serves a row for a session that has NOT traded yet with NaN in every price column and only
+# a volume number. `float(nan)` succeeds silently, so before this guard existed that row became a
+# RawBar with nan OHLC and was persisted into the append-only BarStore (60 series / 58 symbols),
+# which then served `"open": null` to /structure's candlestick chart and took the page down.
+
+
+def _priceless_row_dataframe(fixture: dict) -> pd.DataFrame:
+    """The committed real fixture PLUS one appended vendor row shaped exactly as Yahoo's
+    not-yet-traded row is: NaN in all four price columns, a real volume."""
+    df = _fixture_dataframe(fixture)
+    later = pd.to_datetime([fixture["bars"][-1]["epoch"] + 86400], unit="s", utc=True)
+    priceless = pd.DataFrame(
+        {
+            "Open": [float("nan")],
+            "High": [float("nan")],
+            "Low": [float("nan")],
+            "Close": [float("nan")],
+            "Volume": [47402209],
+        },
+        index=later,
+    )
+    return pd.concat([df, priceless])
+
+
+def test_fetch_bars_drops_a_vendor_row_whose_prices_are_all_nan(monkeypatch):
+    fixture = _load_fixture()
+    priceless_epoch = fixture["bars"][-1]["epoch"] + 86400
+    _install_fake_ticker(monkeypatch, _priceless_row_dataframe(fixture))
+
+    bars = YahooAdapter().fetch_bars(fixture["symbol"], START, END, "1d")
+
+    # Exactly the three REAL fixture bars survive; the priceless row is an absent bar, not a bar.
+    assert len(bars) == 3
+    assert [b.epoch for b in bars] == [b["epoch"] for b in fixture["bars"]]
+    assert priceless_epoch not in [b.epoch for b in bars]
+    # And every surviving bar carries four finite prices -- no nan reaches the caller at all.
+    for bar in bars:
+        for value in (bar.open, bar.high, bar.low, bar.close):
+            assert math.isfinite(value)
+
+
+def test_fetch_bars_drops_a_priceless_row_without_disturbing_the_real_rows(monkeypatch):
+    # The dropped row must not perturb the rows around it: same epochs, same OHLC, same volumes,
+    # byte-for-byte identical to the run where the vendor never served the priceless row at all.
+    fixture = _load_fixture()
+    _install_fake_ticker(monkeypatch, _fixture_dataframe(fixture))
+    clean = YahooAdapter().fetch_bars(fixture["symbol"], START, END, "1d")
+    _install_fake_ticker(monkeypatch, _priceless_row_dataframe(fixture))
+    with_priceless = YahooAdapter().fetch_bars(fixture["symbol"], START, END, "1d")
+    assert with_priceless == clean
+
+
+def test_fetch_bars_raises_no_data_for_window_when_every_vendor_row_is_priceless(monkeypatch):
+    # An ALL-priceless window is honestly indistinguishable from an empty one: nothing tradable
+    # happened. It must raise NoDataForWindow -- never return an empty tuple, never a nan bar.
+    fixture = _load_fixture()
+    epochs = [b["epoch"] for b in fixture["bars"]]
+    all_nan = pd.DataFrame(
+        {
+            "Open": [float("nan")] * len(epochs),
+            "High": [float("nan")] * len(epochs),
+            "Low": [float("nan")] * len(epochs),
+            "Close": [float("nan")] * len(epochs),
+            "Volume": [0] * len(epochs),
+        },
+        index=pd.to_datetime(epochs, unit="s", utc=True),
+    )
+    _install_fake_ticker(monkeypatch, all_nan)
+    with pytest.raises(NoDataForWindow):
+        YahooAdapter().fetch_bars(fixture["symbol"], START, END, "1d")
+
+
+def test_fetch_bars_drops_a_row_whose_volume_is_nan(monkeypatch):
+    # A NaN volume would make `int(row["Volume"])` raise and fail the WHOLE fetch, discarding every
+    # real bar the same response carried -- so it is covered by the same drop.
+    fixture = _load_fixture()
+    df = _fixture_dataframe(fixture)
+    later = pd.to_datetime([fixture["bars"][-1]["epoch"] + 86400], unit="s", utc=True)
+    nan_volume = pd.DataFrame(
+        {"Open": [201.0], "High": [202.0], "Low": [200.0], "Close": [201.5], "Volume": [float("nan")]},
+        index=later,
+    )
+    _install_fake_ticker(monkeypatch, pd.concat([df, nan_volume]))
+
+    bars = YahooAdapter().fetch_bars(fixture["symbol"], START, END, "1d")
+
+    assert [b.epoch for b in bars] == [b["epoch"] for b in fixture["bars"]]
+
+
 def test_interval_map_covers_the_five_directly_fetched_era5_timeframes():
     # Explicit scope proof: exactly the FIVE directly-fetched era-5 timeframes ("4h" is
     # deliberately absent -- it is never requested from the vendor as its own interval; see
diff --git a/apps/frontend/components/StructureChart.tsx b/apps/frontend/components/StructureChart.tsx
index d6bcf98..5cf13f1 100644
--- a/apps/frontend/components/StructureChart.tsx
+++ b/apps/frontend/components/StructureChart.tsx
@@ -1,6 +1,6 @@
 "use client";
 
-import { useEffect, useRef, useState } from "react";
+import { useEffect, useMemo, useRef, useState } from "react";
 import type { BarRow, SrLevel, TradabilityBand } from "@/lib/types";
 import { formatDateTimeDMY } from "@/lib/datetime";
 import { EmptyHint } from "./Panel";
@@ -89,6 +89,24 @@ export interface ChartPriceLineSpec {
   title: string;
 }
 
+// Is ONE served row drawable as a candle? The charting library asserts (and THROWS, unmounting the
+// whole page) on a candle whose open/high/low/close is not a number — and JSON serves a stored
+// non-finite price as `null`. The backend now excludes such rows from the merged read and reports
+// them in `integrity_errors` (research/bars.py), so this is defence in depth, not the fix: one
+// unusable row must degrade the CHART (dropped, and said so beneath it), never delete the page.
+// era-desk-iter-4 audit B1 — the reproduced failure was exactly "Assertion failed: Candlestick
+// series item data value of open must be a number, got=object, value=null", 0.1s after the wall
+// rendered, on 58 symbols including the era's pinned AAPL.
+function isDrawableCandle(bar: BarRow): boolean {
+  return (
+    Number.isFinite(bar.ts) &&
+    Number.isFinite(bar.open) &&
+    Number.isFinite(bar.high) &&
+    Number.isFinite(bar.low) &&
+    Number.isFinite(bar.close)
+  );
+}
+
 export function StructureChart({
   bars,
   levels,
@@ -120,6 +138,12 @@ export function StructureChart({
   clockFormatter?: boolean;
 }) {
   const containerRef = useRef<HTMLDivElement | null>(null);
+  // Only drawable rows reach the library (see isDrawableCandle). Everything downstream — the
+  // viewport anchoring, the as-of index, the "any candles at all" hint — indexes into THIS array,
+  // so a dropped row can never shift the operator's scroll position onto the wrong candle.
+  const drawableBars = useMemo(() => bars.filter(isDrawableCandle), [bars]);
+  const drawableLiveBars = useMemo(() => liveBars.filter(isDrawableCandle), [liveBars]);
+  const undrawableCount = bars.length - drawableBars.length + (liveBars.length - drawableLiveBars.length);
   // `chartReady` flips once the dynamically imported chart library has built the chart+series. It
   // is STATE (not just a ref) on purpose: the candle window resolves in a few milliseconds and can
   // easily land BEFORE the dynamic import does, and a ref would leave the draw effects with nothing
@@ -308,7 +332,7 @@ export function StructureChart({
     // Candles VERBATIM from the loaded window. `ts` is already a real UTC-epoch-seconds value
     // (the bar store's own field — see research/bars.py's `_bar_to_row`), so — unlike
     // PriceChart.tsx's logical-time-to-epoch mapping — no anchor offset is needed here.
-    const candles = bars.map((b) => ({
+    const candles = drawableBars.map((b) => ({
       time: b.ts as any,
       open: b.open,
       high: b.high,
@@ -335,7 +359,7 @@ export function StructureChart({
         : null;
 
     series.setData(candles);
-    drawnBarsRef.current = bars;
+    drawnBarsRef.current = drawableBars;
 
     if (candles.length === 0) {
       drawnRef.current = false;
@@ -348,14 +372,14 @@ export function StructureChart({
       // crush the whole window into the canvas width, which is exactly what made a long series
       // unreadable and expensive to draw.)
       const viewport = initialViewportBars();
-      const asOfIndex = asOfTs === undefined ? -1 : bars.findIndex((b) => b.ts === asOfTs);
+      const asOfIndex = asOfTs === undefined ? -1 : drawableBars.findIndex((b) => b.ts === asOfTs);
       const to =
         asOfIndex >= 0
           ? Math.min(candles.length, asOfIndex + Math.round(viewport * (1 - AS_OF_VIEWPORT_SHARE)))
           : candles.length;
       chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, to - viewport), to });
     } else if (anchor && visibleRange) {
-      const newIndex = bars.findIndex((b) => b.ts === anchor.ts);
+      const newIndex = drawableBars.findIndex((b) => b.ts === anchor.ts);
       if (newIndex >= 0) {
         const from = newIndex - anchor.offset;
         chart.timeScale().setVisibleLogicalRange({
@@ -371,7 +395,7 @@ export function StructureChart({
     // re-issued here. Marked `fill` so the hook can refuse it at its cap. This is what makes the
     // chart converge on a full viewport instead of loading exactly one page per operator gesture.
     requestMissingBars(chart.timeScale().getVisibleLogicalRange(), { fill: true });
-  }, [bars, asOfTs, chartReady]);
+  }, [drawableBars, asOfTs, chartReady]);
 
   // --- Feed the live tape bars into the second series (cockpit only) ----------------------------
   // Updated in place so the last bar animates as trades arrive: when the new array is an append-only
@@ -385,7 +409,7 @@ export function StructureChart({
     const liveSeries = liveSeriesRef.current;
     if (!chart || !liveSeries) return;
 
-    const candles = liveBars.map((b) => ({
+    const candles = drawableLiveBars.map((b) => ({
       time: b.ts as any,
       open: b.open,
       high: b.high,
@@ -397,7 +421,7 @@ export function StructureChart({
     const canIncrement =
       prev.length > 0 &&
       candles.length >= prev.length &&
-      liveBars[prev.length - 1]?.ts === prev[prev.length - 1]?.ts;
+      drawableLiveBars[prev.length - 1]?.ts === prev[prev.length - 1]?.ts;
 
     if (canIncrement) {
       for (let i = prev.length - 1; i < candles.length; i++) {
@@ -415,8 +439,8 @@ export function StructureChart({
         chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, to - viewport), to });
       }
     }
-    drawnLiveRef.current = liveBars;
-  }, [liveBars, chartReady]);
+    drawnLiveRef.current = drawableLiveBars;
+  }, [drawableLiveBars, chartReady]);
 
   // --- Draw the level + band reference lines (clear-then-redraw, PriceChart.tsx's pattern) ------
   // Kept in its OWN effect so appending a lazily-loaded candle page never re-creates every line.
@@ -579,7 +603,7 @@ export function StructureChart({
     }
   }, [asOfTs, asOfLabel, bars, chartReady]);
 
-  const hasBars = bars.length > 0 || liveBars.length > 0;
+  const hasBars = drawableBars.length > 0 || drawableLiveBars.length > 0;
 
   return (
     <div className="relative">
@@ -589,6 +613,14 @@ export function StructureChart({
           <EmptyHint>No candles to draw for this timeframe.</EmptyHint>
         </div>
       )}
+      {undrawableCount > 0 && (
+        <p
+          data-testid="structure-chart-undrawable-rows"
+          className="mt-1 text-[11px] text-amber-300/80"
+        >
+          {undrawableCount} row(s) in this window carry no price and are not drawn.
+        </p>
+      )}
       {loadingMore && (
         <div
           data-testid="structure-chart-loading-more"
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index dfc24d3..fa0d389 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -6,6 +6,9 @@ import type {
   BarSeriesRecord,
   CreateBacktestParams,
   DatasetsListResult,
+  DeskScreenComputeSnapshot,
+  DeskScreenListResult,
+  DeskTopupComputeSnapshot,
   EdgeReportComputeSnapshot,
   EdgeReportPayload,
   LevelsResponse,
@@ -907,3 +910,171 @@ export async function cancelEdgeReportCompute(): Promise<{ ok: boolean; error?:
     return { ok: false, error: "Backend unreachable — is the API running?" };
   }
 }
+
+// --- era-desk-iter-4 (J-04): the /desk page's seven fetch/trigger/cancel functions. Mirror
+// `triggerEdgeReportCompute`/`fetchEdgeReportCompute`/`cancelEdgeReportCompute` immediately above
+// exact `{ok, data, error}` shape and 422/unreachable-fold behavior byte-for-byte.
+
+// GET /research/desk/screen — the screen-history list + latest full snapshot, served VERBATIM.
+// Mirrors `fetchEdgeReport`/`fetchDatasets` (a LIST-shaped endpoint, no query params — the
+// `?date=` variant is J-05 scope, deferred). An honest-empty (`{screens: [], latest: null,
+// integrity_errors: []}`) result is a valid `ok:true` outcome — the caller renders it as the
+// "Desk screen not computed yet." state, never a failure; `data: null` is reserved for a genuine
+// non-200 / unreachable backend.
+export async function fetchDeskScreen(): Promise<{
+  ok: boolean;
+  data: DeskScreenListResult | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/screen`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskScreenListResult };
+    }
+    let error = "The desk screen could not be loaded.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, data: null, error };
+  } catch {
+    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
+  }
+}
+
+// POST /research/desk/screen/compute — start (or, while one is already running, observe) the
+// single-flight screen compute job. `screenDate` is the CALLER's own today (the `todayUtcDate()`
+// helper, /structure's own "Today" shortcut precedent) — this function takes it as a parameter
+// rather than resolving it itself, so the page owns the ONE date source. Mirrors
+// `triggerEdgeReportCompute`'s exact shape; the backend's own 422 (e.g. no universe registered)
+// `detail` is surfaced VERBATIM, never a client-fabricated message.
+export async function triggerDeskScreenCompute(screenDate: string): Promise<{
+  ok: boolean;
+  data?: { started: boolean; compute: DeskScreenComputeSnapshot };
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/screen/compute`, {
+      method: "POST",
+      headers: { "Content-Type": "application/json" },
+      body: JSON.stringify({ screen_date: screenDate }),
+    });
+    if (res.ok) {
+      const data = await res.json();
+      return { ok: true, data };
+    }
+    let error = "The screen compute could not be started.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, error };
+  } catch {
+    return { ok: false, error: "Backend unreachable — is the API running?" };
+  }
+}
+
+// GET /research/desk/screen/compute — the screen compute job's current/last snapshot, served
+// VERBATIM, or `null` if none has ever run. Mirrors `fetchEdgeReportCompute`: `ok:false, data:null`
+// on any failure so a poll tick's caller keeps the last known view — never fabricates a snapshot.
+export async function fetchDeskScreenCompute(): Promise<{
+  ok: boolean;
+  data: DeskScreenComputeSnapshot | null;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/screen/compute`);
+    if (!res.ok) return { ok: false, data: null };
+    const data = await res.json();
+    return { ok: true, data: (data as DeskScreenComputeSnapshot | null) ?? null };
+  } catch {
+    return { ok: false, data: null };
+  }
+}
+
+// POST /research/desk/screen/compute/cancel — cancel the in-flight screen compute job. Mirrors
+// `cancelEdgeReportCompute`'s `{ok, error?}` shape; the backend's 409 (idle) `detail` is surfaced
+// VERBATIM.
+export async function cancelDeskScreenCompute(): Promise<{ ok: boolean; error?: string }> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/screen/compute/cancel`, { method: "POST" });
+    if (res.ok) return { ok: true };
+    let error = "The screen compute could not be cancelled.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, error };
+  } catch {
+    return { ok: false, error: "Backend unreachable — is the API running?" };
+  }
+}
+
+// POST /research/desk/topup/compute — start (or, while one is already running, observe) the
+// single-flight desk bar top-up job over the latest universe snapshot's members. No request body
+// (the backend resolves the latest universe snapshot itself). Mirrors
+// `triggerDeskScreenCompute`'s shape; this is the FIRST-EVER UI caller of this endpoint (shipped
+// J-02, iter-2 — CLI/POST-only until now).
+export async function triggerDeskTopupCompute(): Promise<{
+  ok: boolean;
+  data?: { started: boolean; compute: DeskTopupComputeSnapshot };
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/topup/compute`, { method: "POST" });
+    if (res.ok) {
+      const data = await res.json();
+      return { ok: true, data };
+    }
+    let error = "The bar top-up could not be started.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, error };
+  } catch {
+    return { ok: false, error: "Backend unreachable — is the API running?" };
+  }
+}
+
+// GET /research/desk/topup/compute — the top-up job's current/last snapshot, served VERBATIM, or
+// `null` if none has ever run this process. Mirrors `fetchDeskScreenCompute`.
+export async function fetchDeskTopupCompute(): Promise<{
+  ok: boolean;
+  data: DeskTopupComputeSnapshot | null;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/topup/compute`);
+    if (!res.ok) return { ok: false, data: null };
+    const data = await res.json();
+    return { ok: true, data: (data as DeskTopupComputeSnapshot | null) ?? null };
+  } catch {
+    return { ok: false, data: null };
+  }
+}
+
+// POST /research/desk/topup/compute/cancel — cancel the in-flight top-up job. Mirrors
+// `cancelDeskScreenCompute`.
+export async function cancelDeskTopupCompute(): Promise<{ ok: boolean; error?: string }> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/topup/compute/cancel`, { method: "POST" });
+    if (res.ok) return { ok: true };
+    let error = "The bar top-up could not be cancelled.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, error };
+  } catch {
+    return { ok: false, error: "Backend unreachable — is the API running?" };
+  }
+}
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 9c5cb95..79bf11a 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -778,3 +778,128 @@ export interface EdgeReportNotComputed {
 // not-computed payload. `payload.status === "not_computed"` is the render branch's discriminator
 // (see `structure/page.tsx`'s Edge Report section).
 export type EdgeReportPayload = EdgeReportResponse | EdgeReportNotComputed;
+
+// --- Era B "The Desk" iter-4 (J-04) -- the /desk briefing page's types. Mirrors the backend's
+// registered shapes verbatim (runs/goal-session-desk/state/blueprint.md's Data Contract "New rows
+// this era" table) -- every value here is rendered read-only; nothing is recomputed client-side.
+
+// One ranked screen row (`desk_screen.py`'s `compute_screen`), owned by `app/research/desk_screen.py`,
+// served verbatim by `GET /research/desk/screen`. `band_class`/`distance_bps`/`band_score`/
+// `price_low`/`price_high` all come from ONE `compute_tradability` band per symbol -- never
+// recomputed here. `coverage` is keyed by timeframe (e.g. "1h"/"4h"/"1d"/"1w"), each entry read
+// verbatim from `desk_coverage.get_desk_coverage` -- rendered honestly per-timeframe (a symbol may
+// hold bars for some pinned timeframes and not others; never assumed uniform).
+export interface DeskScreenRow {
+  symbol: string;
+  side: "support" | "resistance";
+  band_class: "A" | "B" | "C" | null;
+  distance_bps: number;
+  band_score: number;
+  price_low: number;
+  price_high: number;
+  coverage: Record<string, { has_bars: boolean; latest_window_end_utc: string | null }>;
+  tick_evidence: boolean;
+}
+
+// A member the screen walked but could not rank -- two honest, distinct reasons, never conflated:
+// "no_bars" (no bar series recorded at all) vs "no_basis" (a daily series exists but no prior
+// session resolves as a basis).
+export interface DeskScreenSkip {
+  symbol: string;
+  skipped: true;
+  reason: "no_bars" | "no_basis";
+  coverage: Record<string, { has_bars: boolean; latest_window_end_utc: string | null }>;
+  tick_evidence: boolean;
+}
+
+// One full, persisted screen snapshot -- frozen JSON, append-only, keyed on five pins
+// (`screen_date`, `as_of`, `universe_snapshot_id`, `config_fingerprint`, `bar_store_signature`).
+// `rows` is already in the snapshot's OWN served rank order (class desc, distance asc, score
+// desc, symbol asc) -- never re-sorted client-side.
+export interface DeskScreenSnapshot {
+  id: string;
+  screen_date: string;
+  as_of: string;
+  universe_snapshot_id: string | null;
+  config_fingerprint: string;
+  bar_store_signature: string;
+  created_utc: string;
+  rows: DeskScreenRow[];
+  skipped: DeskScreenSkip[];
+}
+
+// The lightweight, meta-only projection `GET /research/desk/screen`'s bulk `screens` list serves
+// for EVERY historical snapshot -- id/pins/counts only, NEVER the full `rows`/`skipped` arrays (a
+// screen snapshot is materially larger than a universe snapshot -- desk_screen.py module
+// docstring). The read-only screen-history list on `/desk` renders this verbatim, no click-through
+// (J-05 scope, deferred).
+export interface DeskScreenMeta {
+  id: string;
+  screen_date: string;
+  as_of: string;
+  universe_snapshot_id: string | null;
+  config_fingerprint: string;
+  bar_store_signature: string;
+  created_utc: string;
+  counts: { rows: number; skipped: number };
+}
+
+// `GET /research/desk/screen` (no `date` param) -- honest-empty-or-populated, HTTP 200 always,
+// never 404. `latest === null` iff no screen has EVER been computed -- the page's ONE discriminator
+// for the "Desk screen not computed yet." empty state (never conflated with a computed screen that
+// simply skipped every member, which renders `rows: []` with a non-empty `latest`).
+export interface DeskScreenListResult {
+  screens: DeskScreenMeta[];
+  latest: DeskScreenSnapshot | null;
+  integrity_errors: { file: string; error: string }[];
+}
+
+// era-desk-iter-4 (J-04) -- the screen compute manager's job snapshot (`DeskScreenComputeManager`,
+// `app/research/desk_screen_compute.py`), served VERBATIM by GET/POST `/research/desk/screen/compute`.
+// `reused`/`screen_id` are THIS iteration's additive amendment to the row (audit B2): `screen_id`
+// is the resulting persisted snapshot's own id once a terminal state resolves (`null` while
+// running or before any trigger); `reused` is `true` iff that snapshot already existed under the
+// SAME 5-pin key before this job ran (a pure re-read, zero new file written), `false` when this
+// job's own walk is what created it.
+export interface DeskScreenComputeProgress {
+  members_total: number;
+  members_done: number;
+  current: string | null;
+}
+
+export interface DeskScreenComputeSnapshot {
+  id: string;
+  state: "running" | "done" | "cancelled" | "failed";
+  screen_date: string;
+  started_utc: string | null;
+  finished_utc: string | null;
+  error: string | null;
+  reused: boolean;
+  screen_id: string | null;
+  progress: DeskScreenComputeProgress;
+}
+
+// The desk bar top-up compute manager's job snapshot (`DeskTopupComputeManager`, shipped J-02,
+// iter-2), served VERBATIM by GET/POST `/research/desk/topup/compute`. THIS iteration (J-04) is
+// its first-ever UI consumer (a Top-up button on `/desk`) -- read-only wiring, zero shape change.
+export interface DeskTopupOutcome {
+  symbol: string;
+  timeframe: string;
+  outcome: "reused" | "fetched" | "failed";
+  detail: string | null;
+}
+
+export interface DeskTopupComputeProgress {
+  pairs_total: number;
+  pairs_done: number;
+  outcomes: DeskTopupOutcome[];
+}
+
+export interface DeskTopupComputeSnapshot {
+  id: string;
+  state: "running" | "done" | "cancelled" | "failed";
+  started_utc: string | null;
+  finished_utc: string | null;
+  error: string | null;
+  progress: DeskTopupComputeProgress;
+}
diff --git a/incredible_auto_dev/.claude/agents/demo-narrator.md b/incredible_auto_dev/.claude/agents/demo-narrator.md
index 3cc275c..c7c82d6 100644
--- a/incredible_auto_dev/.claude/agents/demo-narrator.md
+++ b/incredible_auto_dev/.claude/agents/demo-narrator.md
@@ -4,8 +4,8 @@ description: Per-iteration product demonstrator. Authors a machine-executable de
 model: claude-sonnet-5
 tools: [Read, Glob, Grep, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 2.0.0
-last_updated: 2026-05-22
+version: 2.1.0
+last_updated: 2026-07-26
 ---
 
 # Demo Narrator — demo-script author
@@ -26,6 +26,9 @@ testing. Favor the flows that were already verified working this iteration.
 
 CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
+1. `.claude/skills/plain-language.md` — the shared plain-writing standard. It
+   governs every `title` and `narration` field you write.
+
 The dispatch wrapper passes you: a `mode` (`record`, `live`, or `session`), a
 `phase-id` (or a session `sid` in session mode), the `FRONTEND_URL`, and the
 **Demo JSON output path** to write.
diff --git a/incredible_auto_dev/.claude/agents/developer.md b/incredible_auto_dev/.claude/agents/developer.md
index b6615cb..6908d46 100644
--- a/incredible_auto_dev/.claude/agents/developer.md
+++ b/incredible_auto_dev/.claude/agents/developer.md
@@ -3,8 +3,8 @@ name: developer
 description: Implementation agent. Reads the execution plan from runs/<phase>/plan.md, implements changes following TDD. Handles both backend and frontend work. On retry, reads existing review/QA reports and fixes only the listed issues. Writes dev handoff when complete.
 model: claude-sonnet-5
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.1.1
-last_updated: 2026-07-03
+version: 1.1.2
+last_updated: 2026-07-25
 ---
 
 # Developer Agent
@@ -17,7 +17,7 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
 1. `docs/goal.md` — understand the project's overall goal before implementing
 2. `.claude/project-template.md` — stack configuration, test commands, architecture principles
-3. `docs/architecture/*.md` — understand existing project architecture
+3. `docs/architecture/*.md` — existing project architecture (if present; created by update-docs.sh after the first finalized phase — absence is normal early on, skip silently)
 4. `runs/<phase>/plan.md` — execution plan (what to build)
 5. Phase spec at `docs/phases/<phase>.md` — requirements and definition of done
 6. Relevant existing code in the project
diff --git a/incredible_auto_dev/.claude/agents/goal-evaluator.md b/incredible_auto_dev/.claude/agents/goal-evaluator.md
index ed57bbe..27b15ac 100644
--- a/incredible_auto_dev/.claude/agents/goal-evaluator.md
+++ b/incredible_auto_dev/.claude/agents/goal-evaluator.md
@@ -4,8 +4,8 @@ description: Goal-mode iteration evaluator. Reads iteration outputs (handoffs, b
 model: claude-opus-5
 tools: [Read, Glob, Grep, Bash, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.7.0
-last_updated: 2026-07-18
+version: 1.8.0
+last_updated: 2026-07-26
 ---
 
 # Goal Evaluator Agent
@@ -207,6 +207,17 @@ Write to `runs/goal-session-<sid>/iter-<N>/eval.md`:
 <only present when verdict is GOAL_ACHIEVED, REGRESSION, or STALLED — explain why halting>
 ```
 
+### 6b. Plain-language rule for prose fields
+
+The session owner is not a native English reader. In the PROSE fields only — `Reasoning` and `Next-step recommendation` in evaluator-log.md (step 4), and the `## Summary`, `## Next-Step Recommendation`, and `## Halt Justification` sections of eval.md (step 6) — write plain English:
+
+- Short sentences. Everyday words. No idioms.
+- Whenever you name a journey ID, put its short name next to it: J-04 "Sign in with email" — never a bare ID list.
+- Describe what the user would see, not internal code: "the login page rejects a correct password", not a function, class, or variable name. (Evidence references keep their file paths — that rule is unchanged.)
+- End the recommendation with one sentence saying what should happen next, phrased so a non-programmer could act on it or approve it.
+
+This rule changes WORDING ONLY. It does not change any machine-parsed format: the verdict lines and their allowed values defined elsewhere in this document, the depth-recommendation line, all headings, table shapes, JSON schemas, and file paths stay exactly as specified.
+
 ### 7. Overwrite iteration-state.md (the next planner's digest)
 
 After eval.md is written (so your fresh verdict is its newest entry), write
diff --git a/incredible_auto_dev/.claude/agents/iteration-summarizer.md b/incredible_auto_dev/.claude/agents/iteration-summarizer.md
index a449407..756b531 100644
--- a/incredible_auto_dev/.claude/agents/iteration-summarizer.md
+++ b/incredible_auto_dev/.claude/agents/iteration-summarizer.md
@@ -4,8 +4,8 @@ description: Post-iteration summarizer. Reads the iteration's artifacts (dev han
 model: claude-sonnet-5
 tools: [Read, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.1.0
-last_updated: 2026-07-07
+version: 1.2.0
+last_updated: 2026-07-26
 ---
 
 # Iteration Summarizer
@@ -30,6 +30,7 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
 1. `templates/iteration-summary.md` — the exact section structure your output must follow
 2. `.claude/skills/visible-change-summarizer.md` — tone and brevity guidance for user-facing summaries
+3. `.claude/skills/plain-language.md` — the shared plain-writing standard (short sentences, IDs always with friendly names, the status word table). It governs the `## In plain words` block, the project story, and the delivered wrap.
 
 ## Input files (read only what exists)
 
diff --git a/incredible_auto_dev/.claude/agents/orchestrator.md b/incredible_auto_dev/.claude/agents/orchestrator.md
index 5fe2a2e..cf2fada 100644
--- a/incredible_auto_dev/.claude/agents/orchestrator.md
+++ b/incredible_auto_dev/.claude/agents/orchestrator.md
@@ -3,8 +3,8 @@ name: orchestrator
 description: Phase execution planner. When invoked by run-phase.sh, reads CLAUDE.md and the phase spec, then writes a concise execution plan to runs/<phase>/plan.md. The shell script (run-phase.sh) drives the dev/review/QA loop; the orchestrator's job is planning only.
 model: claude-sonnet-5
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.0.0
-last_updated: 2026-05-04
+version: 1.0.1
+last_updated: 2026-07-25
 ---
 
 # Orchestrator Agent
@@ -17,7 +17,7 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
 1. `docs/goal.md` — project goal, vision, success criteria (ensure phase aligns with this)
 2. `.claude/project-template.md` — project-specific stack, architecture principles
-3. `docs/architecture/` — project architecture docs (understand what already exists)
+3. `docs/architecture/` — project architecture docs (if present; created by update-docs.sh after the first finalized phase — absence is normal early on, skip silently)
 4. `docs/handoffs/*-dev.md` — prior phase handoffs (what was already built)
 5. The phase spec at `docs/phases/<phase>.md`
 
diff --git a/incredible_auto_dev/.claude/agents/readme-maintainer.md b/incredible_auto_dev/.claude/agents/readme-maintainer.md
index 6f849bb..c533bcf 100644
--- a/incredible_auto_dev/.claude/agents/readme-maintainer.md
+++ b/incredible_auto_dev/.claude/agents/readme-maintainer.md
@@ -4,8 +4,8 @@ description: Project README maintainer (goal mode). After each iteration, refres
 model: claude-sonnet-5
 tools: [Read, Write, Edit, Glob, Grep]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.0.0
-last_updated: 2026-06-04
+version: 1.1.0
+last_updated: 2026-07-26
 ---
 
 # README Maintainer
@@ -31,6 +31,8 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 3. The existing `README.md` at the repo root, if present.
 4. `templates/project-readme.md` — the skeleton to start from **only if `README.md`
    is absent**.
+5. `.claude/skills/plain-language.md` — the shared plain-writing standard for
+   everything you write into the AUTO blocks.
 
 ## Capability inputs (read what exists, skip what doesn't)
 
diff --git a/incredible_auto_dev/.claude/agents/retro-analyst.md b/incredible_auto_dev/.claude/agents/retro-analyst.md
index 5661985..4125bdf 100644
--- a/incredible_auto_dev/.claude/agents/retro-analyst.md
+++ b/incredible_auto_dev/.claude/agents/retro-analyst.md
@@ -4,8 +4,8 @@ description: Post-session retrospective analyst. Reads ONLY the frozen retro-inp
 model: claude-haiku-4-5
 tools: [Read, Write]
 disallowed_tools: ["Bash(rm -rf /)", "Bash(rm -rf ~)", "Bash(rm -rf ~/*)", "Bash(rm -rf /home*)", "Bash(rm -rf /root*)", "Bash(rm -rf /etc*)", "Bash(rm -rf /usr*)", "Bash(rm -rf /var*)", "Bash(rm -rf /boot*)", "Bash(rm -rf /lib*)", "Bash(rm -rf /opt*)", "Bash(rm -rf /srv*)", "Bash(rm -rf /sys*)", "Bash(rm -rf /proc*)", "Bash(git push --force origin main)", "Bash(git push --force origin master)", "Bash(git push -f origin main)", "Bash(git push -f origin master)", "Bash(git push *)", "Bash(git push)", "Bash(git push --force *)", "Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh release *)", "Bash(git tag *)"]
-version: 1.0.0
-last_updated: 2026-07-10
+version: 1.1.0
+last_updated: 2026-07-26
 ---
 
 # Retro Analyst
@@ -47,6 +47,14 @@ Number items RETRO-1 … RETRO-5, at most 5, each ≤20 lines, in this exact sha
 
 Hard rule: no Evidence line → no item. Every Evidence entry names the digest section and quotes the line(s) verbatim, e.g. `Evidence: Friction counters — "Quota pauses: 3"`. Zero items is a valid output: when nothing recurred, the Candidate items body is exactly `nothing recurred worth proposing` plus one sentence saying why (e.g. all counters zero, lessons product-only).
 
+Plain-writing rules (the report is read by a non-developer owner first):
+- The FIRST sentence of every **Problem:** must be plain English: short, everyday
+  words, says who hits the pain and when. Technical detail goes in the second
+  sentence.
+- Never use a bare internal codename (EVO-1, §16, REL-n, a lane or tripwire name)
+  without saying in words what it is.
+- Keep the header's code legend line exactly as the skeleton shows it.
+
 ## Output
 
 Write exactly ONE file — the output path from your dispatch prompt (`reports/goal-session-<sid>-retro.md`), overwriting any existing file:
@@ -54,8 +62,11 @@ Write exactly ONE file — the output path from your dispatch prompt (`reports/g
 ```
 # Session retro — <sid>
 
-> **PROPOSALS ONLY** — a human promotes candidates into docs/improvement-roadmap.md §16
-> per EVO-1; nothing here is scheduled work.
+> **Ideas only — nothing here is scheduled work.** These are suggestions for
+> improving the build system itself, not your product. A human reviews them and
+> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
+> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
+> = chance a change breaks something else.
 
 **Session:** <sid> · **Terminal status:** <from Outcome> · **Iterations:** <from Outcome>
 
diff --git a/incredible_auto_dev/.claude/anti-patterns.md b/incredible_auto_dev/.claude/anti-patterns.md
deleted file mode 100644
index 67b0bd2..0000000
--- a/incredible_auto_dev/.claude/anti-patterns.md
+++ /dev/null
@@ -1,340 +0,0 @@
-# Anti-Patterns
-
-Failure modes observed in production multi-agent development pipelines.
-Each entry includes: the pattern, why it fails, and how to prevent it.
-
----
-
-## 1. Vague acceptance criteria cause infinite review loops
-
-**Pattern:** Phase specs contain requirements like "works correctly", "handles all cases", or "the UI should look nice."
-
-**Why it fails:** The reviewer and the developer use different interpretations of "correct". Each review cycle produces a FAIL for a different reason. After 3 loops the pipeline halts with no clear fix.
-
-**Prevention:** Every item in DEFINITION OF DONE must be:
-- Specific: "POST /api/items returns 201 with the created item's ID"
-- Testable: a concrete pass/fail condition, not a judgment
-- Scoped: tied to this phase only, not aspirational future state
-
-**Example (bad):** "The form submission should work."
-**Example (good):** "Submitting a valid form creates a record in the database and redirects to the detail page. Submitting an invalid form shows field-level error messages and does not create a record."
-
----
-
-## 2. Hardcoded stack paths in agent prompts break portability
-
-**Pattern:** Agent definitions or scripts contain paths like `apps/backend/.venv/bin/python -m pytest` or `cd apps/backend && alembic upgrade head` embedded directly.
-
-**Why it fails:** When the framework is adopted by a new project, every agent file needs manual editing. Agents in the pipeline inherit the wrong paths and fail silently.
-
-**Prevention:** All stack-specific commands live in `.claude/project-template.md`. Agent definitions reference the template: "Run the test command from project-template.md." Scripts use env vars (`CHAIN_START_BACKEND_CMD`) or conventionally-named scripts (`scripts/start-backend.sh`).
-
----
-
-## 3. Merged backend+frontend into one developer agent reduces flexibility
-
-**Pattern (anti):** Splitting implementation into separate backend-only and frontend-only agents with separate model invocations.
-
-**Why it's a false economy:** The backend agent writes the handoff, then the frontend agent reads it and adds another handoff. Two sequential long-context invocations for work that shares context. Each agent re-reads the spec, plan, and existing code from scratch.
-
-**Prevention:** A single developer agent handles both. The plan marks `Frontend Present: yes/no`. On yes, the agent implements backend first, then frontend in the same session. Alternatively, run two passes of the same developer agent (backend pass, then frontend pass) using the same agent definition with different context flags.
-
----
-
-## 4. UI evolution is an afterthought, not a pipeline gate
-
-**Pattern:** QA runs unit tests, they pass, phase is declared done. Three phases later the product manager notices the user can't access the new feature because no navigation link was added.
-
-**Why it fails:** Unit tests don't check whether the UI exposes the capability. A backend feature is invisible until the UI surfaces it.
-
-**Prevention:** The UI Evolution Audit is part of every phase with `Frontend Present: yes`. `UI-FAIL` blocks overall QA PASS. Review checklist explicitly checks for navigation updates and detail/list pages.
-
----
-
-## 5. Quota exhaustion mid-pipeline without retry causes data loss
-
-**Pattern:** A 6-stage pipeline runs unattended. At stage 4 (QA), Claude hits the usage quota and exits. The partial run state is lost. The pipeline must restart from scratch.
-
-**Why it fails:** Wasted compute. Worse, if stage 3 (dev) made changes that weren't committed, the developer re-implements the same code differently on retry, causing drift.
-
-**Prevention:**
-- Checkpoint/resume via `runs/<phase>/status.json` — completed stages are skipped on re-run
-- `quota-retry.sh` wraps every Claude invocation — detects quota messages, parses the reset time, sleeps and retries automatically
-- Never start a long pipeline before verifying quota headroom
-
----
-
-## 6. Review reports without file:line references are useless
-
-**Pattern:** Review report says "the validation logic has issues" or "error handling could be improved."
-
-**Why it fails:** The developer reads the report, doesn't know which file or line to fix, makes a guess, and the reviewer flags the same "issue" again in the next loop.
-
-**Prevention:** Every finding in a review report MUST include:
-- Exact file path
-- Line number or function name
-- Specific problem description
-- Specific fix description
-
-**Example (bad):** "Error handling is insufficient."
-**Example (good):** "`apps/backend/routers/items.py:47` — `create_item` does not catch `IntegrityError` from SQLAlchemy. Add a try/except that returns 409 Conflict when a duplicate key is detected."
-
----
-
-## 7. Reviewer and QA validator that fix code bypass the feedback loop
-
-**Pattern:** The reviewer notices a bug and edits the file to fix it "since it's obvious." The QA validator notices a test failure and patches the test to pass.
-
-**Why it fails:** The developer agent doesn't learn from the correction. On the next phase, the same mistake recurs because the developer never saw it as a fix — only the reviewer did. More critically: reviewer fixes can silently introduce new bugs that QA was supposed to catch, but QA didn't see the reviewer's changes.
-
-**Prevention:**
-- Reviewer NEVER edits source files — writes the report only
-- QA NEVER fixes test failures — writes them as blockers
-- Only the developer (and auditor, for critical post-QA issues) modifies source code
-
----
-
-## 8. Free-form agent conversation leads to hallucinated agreements
-
-**Pattern:** Two agents "discuss" a design decision in chat. Agent B says "OK I'll implement it your way." Agent B then implements something different because its actual context window didn't include the full conversation.
-
-**Why it fails:** Chat messages between agents are not in each agent's context window. Agents only have access to what was in their initial prompt and what they've read from files in the current session.
-
-**Prevention:** Agents communicate ONLY through filesystem artifacts. No "pass a message to the next agent." The orchestrator writes a plan to a file; the developer reads that file. The developer writes a handoff; the reviewer reads that file. This is the only reliable inter-agent communication.
-
----
-
-## 9. Missing functional test plans make QA rubber-stamp
-
-**Pattern:** QA runs `pytest` and reports PASS. The test suite covers internal functions but doesn't verify the user-facing feature works end-to-end. A critical API endpoint is broken but no test covers it.
-
-**Why it fails:** "Tests pass" and "the feature works for a user" are different claims. Without a functional test plan derived from the spec, QA only validates what the developer chose to test, not what the spec required.
-
-**Prevention:** The test plan generator runs BEFORE QA, deriving explicit test cases from the spec's DEFINITION OF DONE and REQUIRED USER FLOWS. QA must execute each TC-01, TC-02, ... test case and record actual vs expected outcomes. A test case failure is a blocker.
-
----
-
-## 10. Supply-chain attacks target autonomous agents
-
-**Pattern:** A compromised PyPI or npm package gets installed by an agent during a phase run. The agent has no reason to be suspicious — it's just running the install command from the spec.
-
-**Why it fails:** Autonomous agents install packages without human review. A single compromised dependency can exfiltrate secrets, modify the codebase, or establish persistence — all while the pipeline continues normally.
-
-**Prevention:** The install security gate intercepts every `pip install`, `npm install`, `git clone`, and `curl|bash` command. On Claude Code it reads the PreToolUse JSON from stdin (`.tool_input.command` — `$CLAUDE_TOOL_INPUT_COMMAND` never existed; SEC-7 fixed the plumbing) and enforces via an agent-visible `permissionDecision:"deny"` with the remediation in the reason (pin the version / edit the `config/install-security-policy.json` allowlist / `CHAIN_INSTALL_GATE_BYPASS=true`) — never a user prompt. Registry packages are warn-mode (SEC-6: proceed + logged banner); direct URLs, tarballs, custom indexes, denylist hits, unknown requirements files, unpinned git clones, and real (unquoted — quoted mentions pass) `curl|bash` deny. All decisions are logged to `reports/security/install-decisions.jsonl`. The gate is a non-negotiable pipeline component — it is not "paranoia."
-
----
-
-## 11. One large phase spec with no DEFINITION OF DONE
-
-**Pattern:** A phase spec describes 8 features in general terms, with no numbered acceptance checklist.
-
-**Why it fails:** The orchestrator doesn't know what "done" looks like. The developer implements 5 of the 8 things. The reviewer gives PASS_WITH_NOTES on the missing 3. QA gives PASS because tests pass. The audit gives FAIL because the spec goal wasn't reached. The pipeline re-runs from dev — wasting 3 cycles that could have been avoided.
-
-**Prevention:** Every phase spec MUST have a numbered DEFINITION OF DONE checklist. Each item is specific and testable. The auditor's primary job is to verify this checklist against actual code, not summaries.
-
----
-
-## 12. Agents that "summarize" instead of reading source code
-
-**Pattern:** The auditor reads the dev handoff and QA report, concludes "tests pass and the handoff describes the implementation," and gives PASS.
-
-**Why it fails:** The handoff is a summary written by the agent that implemented the code. It naturally omits mistakes. The QA report validates what the developer chose to test. Neither is a substitute for reading the actual source files.
-
-**Prevention:** Auditor instructions explicitly state: "Read actual source files, not summaries. If you cannot verify a claim from code, trace through the implementation. Never trust a handoff summary alone."
-
----
-
-## 13. Backend capabilities without UI verification leads to invisible features
-
-**Pattern:** A phase adds 3 new API endpoints. Unit tests pass. QA validates the APIs. Audit gives PASS. But no one verified that the user can actually reach these features from the UI. Three phases later, someone clicks through the app and discovers half the features have no navigation path.
-
-**Why it fails:** "Tests pass" and "the feature works for a user" are completely different claims. A feature that exists in the backend but has no UI entry point is invisible product capability — it was built but cannot be used.
-
-**Prevention:** The UI visibility system produces 6 artifacts per phase:
-- `implementation-summary` — what was built
-- `user-visible-changes` — what users can now do
-- `ui-surface-map` — which routes/components changed and what to test
-- `ui-test-plan` — exact click paths and expected outcomes
-- `ui-test-results` — browser automation evidence
-- `what-to-click` — 5-minute operator verification guide
-
-The phase closure auditor blocks completion when these artifacts are missing or vague. Browser QA must test actual user workflows, not just that pages render.
-
----
-
-## 14. Vague test steps make test plans useless
-
-**Pattern:** A test plan says "test the form submission" or "verify results are correct." The browser QA agent cannot execute this. A human tester cannot follow this. The plan exists but adds no value.
-
-**Why it fails:** Vague test steps produce vague results. "Tested and it works" is not evidence. A test plan that cannot produce reproducible pass/fail evidence is not a test plan.
-
-**Prevention:** Every test step must specify: exact URL, exact element to interact with (by name or visible label), exact value to input, and exact expected outcome. The `post-write-artifact-quality.sh` hook warns when phase report files contain vague placeholder lines. The `what-to-click-writer` skill enforces concrete step writing.
-
----
-
-## 15. Mocked-only tests for external integrations pass while live adapter is broken
-
-**Pattern:** Adapter tests mock all HTTP/browser calls. Tests pass. But the real site changed its HTML structure, blocks headless browsers, or requires auth. No one discovers this until manual testing.
-
-**Why it fails:** Mocked tests validate the parsing logic against a frozen snapshot of the external system. They never detect selector drift, bot detection, geo-blocking, or TLS fingerprint rejection. 100% mocked test coverage gives false confidence that the integration works.
-
-**Prevention:** For phases that add external integrations (scrapers, APIs, webhooks), the developer must include at least one test marked `@pytest.mark.integration` (or equivalent) that hits the real external system. QA functional test plan must include a live integration test case. These tests may be slow/flaky and skipped in CI, but must exist and be run at least once during the phase. The dev handoff must explicitly state whether live testing was successful or document the blocker if it wasn't.
-
-**Example (bad):** All Tesco adapter tests use `_build_tile_html()` fixtures. Tests pass. Tesco changes its CSS classes → live adapter returns 0 results. Bot detection blocks headless Playwright → adapter gets HTTP 403. Neither is caught until a human clicks through the UI.
-
-**Example (good):** One test marked `@pytest.mark.integration` calls `TescoAdapter().search("milk")` against the real Tesco site and asserts `len(results) > 0`. This test is slow but catches selector drift, bot detection, and infrastructure issues immediately.
-
----
-
-## 16. Hardcoded localhost in service configuration breaks non-local access
-
-**Pattern:** API URLs, CORS origins, and service bindings all use `localhost` or `127.0.0.1`. Works on the dev machine's browser. Breaks when accessed from another machine via private IP, from a VM host, through Docker, or behind a reverse proxy.
-
-**Why it fails:** The frontend sends API requests to the hardcoded `localhost:8000`. A user on another machine resolves `localhost` to their own loopback — the backend isn't there. Even if the backend is reachable by IP, restrictive CORS blocks the request. Even if CORS allows it, the backend only listens on `127.0.0.1` and rejects non-loopback connections.
-
-**Prevention:** Reviewer checklist flags any hardcoded `localhost`/`127.0.0.1` in:
-- API client URLs → must be configurable via env var or derived dynamically (e.g., `window.location.hostname`)
-- CORS origins → must use `*`, a port-range regex (e.g. `http://(localhost|127\.0\.0\.1):\d+`), or be configurable in dev mode
-- Service bindings → dev scripts must bind to `0.0.0.0`, not `127.0.0.1`
-- Dev scripts (`dev.sh`, `start-frontend.sh`) → must pass host/port via env var, not hardcoded URL strings
-
-**Sub-pattern — auto-dev-chain port drift:** `ensure_phase_ports` in `lib/common.sh` assigns a hashed preferred port and falls back to the next free port if taken (e.g., 3101 → 3102 when a stale server holds 3101). A CORS whitelist of specific ports (e.g. `[..., "http://localhost:3101"]`) will reject the fallback port and the QA/browser-QA frontend will fail to fetch data, while `curl` still works. Use a regex or env-driven allowlist so any dev port works.
-
-**Example (bad):** `const API_BASE = "http://localhost:8000"` — works only from the same machine.
-**Example (good):** `const API_BASE = \`http://${window.location.hostname}:${API_PORT}\`` — works from any hostname the user accesses the frontend with.
-**Example (CORS bad):** `allow_origins=["http://localhost:3101"]` — breaks when chain falls back to 3102.
-**Example (CORS good, FastAPI):** `allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+"`.
-
----
-
-## 17. Long `sleep` blocks the chain across system suspend/resume
-
-**Pattern:** Quota-retry logic calls `sleep 11137` (e.g. 3 hours) to wait for the Anthropic reset. The user closes the laptop lid, system suspends. On wake the next day, the sleep continues ticking monotonically instead of noticing that wall-clock time already passed the reset — the chain blocks for many hours past the intended wake-up.
-
-**Why it fails:** On Linux, `sleep N` in coreutils may sleep against the monotonic clock (pauses during suspend) or depend on the kernel honoring RTC wake-up. Across suspend/hibernate, neither guarantee is reliable: a 3-hour sleep that straddles an overnight suspend can block for 12+ hours. The pipeline is not crashed — it is silently wedged in a sleep that the user can only detect by inspecting `/proc/<pid>/wchan`.
-
-**Prevention:** Long waits must target an absolute wall-clock epoch, not a duration. `lib/quota-retry.sh::_sleep_until_epoch` polls `date +%s` against the target epoch in ≤60-second chunks — on resume, the very next poll sees the epoch has passed and the sleep exits. Any new pipeline script that needs to wait more than ~60 seconds MUST use `_sleep_until_epoch` rather than `sleep $secs`.
-
-**Example (bad):** `sleep "$sleep_secs"` where `sleep_secs` may be hours — stuck indefinitely if the laptop suspends.
-**Example (good):** `_sleep_until_epoch "$reset_epoch"` — guaranteed to return within 60s of wall clock reaching the target.
-
----
-
-## 18. Goal mode without Must-have journeys or Anti-goals
-
-**Pattern:** A user authors `docs/goal.md` from the template but skips or leaves placeholder content in the **Must-have user journeys** and **Anti-goals** sections, then runs `./scripts/automation/run-goal.sh`. The goal-decomposer produces vague iter specs and the goal-evaluator has no concrete evidence to anchor its `GOAL_ACHIEVED` decision.
-
-**Why it fails:** Goal mode uses an AI evaluator to decide when the loop terminates. Without specific journeys, the evaluator falls back on subjective judgment — best case it loops forever (related to anti-pattern #1), worst case it declares done prematurely on something that doesn't actually work for users. Anti-goals serve as veto criteria; without them the evaluator may rubber-stamp a violation (committed credentials, paid-SaaS dependency, accessibility regression) just because the journeys click through.
-
-**Prevention:**
-- `run-goal.sh` validates `docs/goal.md` on first run: it MUST contain a non-empty Must-have user journeys section with at least one journey, and a non-empty Anti-goals section. The script aborts with a clear error message if either is empty or contains only the template placeholders.
-- Each journey in goal.md MUST have an ID (`J-NN`), numbered click/type/assert steps the browser-qa-agent can execute, and an "Acceptance" line describing the observable end state. The goal-evaluator references these by ID, so missing IDs break the journey-history tracking.
-- Anti-goals MUST be concrete, checkable rules (e.g., "no hard-coded credentials in source files"), not aspirations ("be secure"). Concrete rules let the evaluator classify violations as critical (halts loop) vs minor (continues with fix recommendation).
-
-**Example (bad):**
-```
-## Must-have user journeys
-- TODO: fill in later
-
-## Anti-goals
-- Be secure.
-- Be fast.
-```
-
-**Example (good):**
-```
-## Must-have user journeys
-- **J-01: Sign up and log in**
-  - Steps: 1. visit /signup  2. enter email+password  3. submit  4. expect /dashboard  5. log out  6. log in again  7. expect /dashboard
-  - Acceptance: dashboard greeting shows the user's email
-
-## Anti-goals
-- No hard-coded credentials, API keys, or tokens in source.
-- Auth tokens MUST NOT be stored in localStorage (httpOnly cookies only).
-- No dependency on a paid SaaS service unless explicitly listed in Constraints.
-```
-
----
-
-## 19. `timeout`-wrapped child swallows terminal Ctrl-C
-
-**Pattern:** A long-running command is wrapped with GNU `timeout` for a runtime cap (e.g. `timeout 7200 claude --print "$prompt"`). The user presses Ctrl-C in the terminal and… nothing happens. The shell prints no abort message, no trap fires, and the prompt does not return for many seconds — sometimes minutes — until the wrapped command happens to finish on its own.
-
-**Why it fails:** GNU `timeout` defaults to placing its child in a **new process group** via `setpgid(2)`. Terminal Ctrl-C delivers SIGINT to the foreground process group only, which now contains just the parent shell — *not* the wrapped command. The shell receives the signal and queues the trap, but then has to wait for the pipeline to complete before running the trap; the wrapped command never received SIGINT, so it keeps running. From the user's perspective the script is unresponsive. Eventually the command exits naturally and only then does the queued trap fire — by which point the user has assumed Ctrl-C was lost and probably reached for `kill -9` or closed the terminal.
-
-This is especially bad for AI-agent scripts: the wrapped `claude` keeps consuming API credits long after the user thought they aborted.
-
-**Prevention:** pass `--foreground` to `timeout` (or otherwise keep the child in the parent's process group). With `--foreground`, the wrapped command stays in the parent's pgrp and terminal Ctrl-C reaches it directly. The documented downside — grandchildren of the wrapped command are not timed out — is acceptable for harness use cases where the wrapped command (e.g., `claude`) manages its own subprocesses.
-
-**Example (bad):** `timeout --kill-after=60 7200 claude -p "$prompt" 2>&1 | tee log` — terminal Ctrl-C does NOT reach claude. Trap is queued but blocked.
-**Example (good):** `timeout --foreground --kill-after=60 7200 claude -p "$prompt" 2>&1 | tee log` — terminal Ctrl-C reaches claude immediately; trap fires within milliseconds.
-
-**Detection:** if `kill -INT $shell_pid` exits the shell quickly but terminal Ctrl-C feels "stuck", that's the smoking gun. Confirm with `ps -o pid,pgid,cmd <child_pid>` — if the child's PGID differs from the parent shell's, you've got the bug.
-
----
-
-## 20. `next build` against a live `next dev` corrupts `.next` and SKIPs the demo
-
-**Pattern:** A production `next build` (or a typecheck/lint step that triggers a build) runs while the demo/QA `next dev` server is up. Both write the **same** `apps/frontend/.next` directory, so the build deletes/renames the webpack chunks the dev server is serving. The dev server then answers **every** request with HTTP 500 (`MODULE_NOT_FOUND`, a require stack through `.next/server/...`/`webpack-runtime.js`) and never recovers on its own. The per-iteration demo / browser-QA then report "Frontend did not respond after 90s of retries" and record **SKIPPED**, even though the server is up — it is just 500ing.
-
-**Why it fails:** `next dev` lazily reads compiled chunks from `.next`; a concurrent `next build` clobbers them. The corruption is sticky — only removing `.next` and letting `next dev` rebuild fixes it. In the post-dev fanout this cascades: the shared-services boot tries to start the frontend, fails on the corrupt build, kills it, and every parallel branch (demo, browser-qa) then waits out its readiness budget against a dead port.
-
-**Prevention (harness side, already done):** the harness now self-heals. `_start_service_with_retries` (in `scripts/automation/lib/common.sh`) detects the corrupt-`.next` signature, clears `.next`, and grants one guaranteed-cold rebuild attempt with a longer budget (`CHAIN_FRONTEND_HEAL_TIMEOUT`, default 180s) instead of killing a still-compiling server; `_kill_pid_tree` now escalates TERM→KILL so a surviving worker can't re-corrupt `.next` or squat the port; and the readiness gate `_wait_for_frontend_ready` heals once on the standalone path. Recovery costs a full cold compile per occurrence, so it is a cost, not a free pass.
-
-**Prevention (project side, optional but better):** give build/QA/typecheck commands their own dist dir so they never touch the dev build. Next.js reads `distDir` from `next.config.{js,ts}` (NOT an env var by default), so wire it through config — e.g. `distDir: process.env.NEXT_DIST_DIR || '.next'` — and run builds with `NEXT_DIST_DIR=.next-qa next build`. Agents MUST NOT run a production `next build` while the demo/QA `next dev` is up unless the build is isolated this way.
-
-**Detection:** the frontend start log (`$QA_FRONTEND_LOG` — under the run's `CHAIN_TMPDIR`, e.g. `.../fanout-frontend-<port>.log`) showing `MODULE_NOT_FOUND` / `Cannot find module` with a `GET / 500` and a `.next/server/...` require stack is the signature. `_next_build_is_corrupt` in `common.sh` greps for exactly this.
-
----
-
-## 21. Shared /tmp accumulation and cross-job pytest tmp races
-
-**Pattern:** Nothing sets `TMPDIR`, so every tool the agents run (pytest, playwright/chromium, `mktemp`) writes into shared `/tmp`. pytest's default basetemp `/tmp/pytest-of-<user>/` is keyed on the USER, not the run — concurrent pipeline jobs (different projects, same machine, same user) share it and race pytest's own "keep last 3, rmtree older" pruning (`Directory not empty`, lock races, stale undeletable dirs). Meanwhile the harness's own temp files pile up forever: kept-on-failure `claude-quota-*.log`s, telemetry usage sidecars leaked on every non-success path, and per-role service logs (`fanout-*`, `demo-*`, `goal-iter-*`) that no cleanup path ever targeted. Cleanup ran only on run-phase.sh's success path — never on `fail()`, quota/transport/signal exits, or lean goal iterations.
-
-**Why it fails:** `/tmp` is a shared namespace with no run identifier, so no cleanup step can safely delete anything (it might belong to a concurrent job) — and agents could not delete anyway (see the rm-ban fix: deny-rule over-match + Claude Code's built-in rm working-directory containment). The only "cleanup" was pytest pruning itself, which is exactly the thing that races.
-
-**Prevention:** per-run tmp isolation via `lib/chain-tmp.sh` (REL-13 moved the root OFF /tmp entirely — on this class of machine `/tmp` is a quota'd tmpfs that EDQUOTs long before it looks full):
-- Every entry script (run-phase.sh, run-goal.sh, goal-iter-lean.sh) calls `chain_tmp_init <run-id>`, which creates `$CHAIN_TMP_ROOT/iad.<id>.<pid>` (root default `~/.cache/iad`: big un-quota'd ext4, NOT /tmp) and exports it as `TMPDIR`/`TMP`/`TEMP`; a nested script ADOPTS the inherited dir (owner-guarded, and only while the recorded owner pid is still alive). The WHOLE TMPDIR is kept ≤62 chars (Chromium's 108-char unix-socket limit); long run-ids are shortened to `<prefix>-<sha256-first8>` with the raw id in `.chain-run-id`. NEW pipeline entry scripts MUST do the same.
-- Cleanup is an EXIT trap (fires on success, fail(), quota 75, transport 70, signal exits) plus `chain_tmp_rotate` at the goal-mode iteration boundary — after `_join_showcase_tail`, never right after the evaluator (the async showcase tail still writes there).
-- New `mktemp` calls MUST use a `"${TMPDIR:-/tmp}/…"` template, never a hardcoded `/tmp/...` template. Standalone scratch roots (benchmarks, judgment sandboxes) use `"${CHAIN_TMP_ROOT:-${TMPDIR:-$HOME/.cache/iad}}"` and write an `.owner-pid` file so the janitor can tell live from leaked.
-- Files deliberately kept for debugging MUST be moved to `$CHAIN_TRACE_DIR` (`_quota_preserve_failure_log`), never left in tmp.
-- The ONLY sanctioned fixed-name /tmp files are the two quota sentinels (`/tmp/{claude,codex}-quota-exhausted`) — quota is account-global, every concurrent job must see the same sentinel, and `chain_tmp_janitor` never matches their names.
-- `chain_tmp_janitor` (entry-script start) reaps strays across `$CHAIN_TMP_ROOT` AND the legacy roots (`CHAIN_TMP_LEGACY_ROOTS`, default `/tmp`): `iad.*` dirs whose owner pid is dead (age-gated normally; ANY age under `--aggressive`), `bench-*` scratch beyond the newest `CHAIN_BENCH_KEEP=2`, `judgment-*` sandboxes, legacy loose temp files, `pytest-of-$USER` entries, and `$CHAIN_TMP_ROOT/shared` entries older than `CHAIN_TMP_SHARED_MAX_AGE_HOURS=72`. Tests that call the janitor MUST pass `CHAIN_TMP_LEGACY_ROOTS=""` or they will sweep the real /tmp.
-- `chain_tmp_disk_guard` (engine preflight + top of every goal iteration) checks free space (statvfs on the root; a WRITE PROBE on /tmp because statvfs cannot see tmpfs user quotas) and runs the aggressive janitor under pressure. Only a still-critical `CHAIN_TMP_ROOT` filesystem pauses the session (resumable `AWAITING_DISK`); /tmp pressure alone is warn-only.
-- Interactive/subagent runs get TMPDIR from the user-global `~/.claude/settings.json` `env` block (`TMPDIR=~/.cache/iad/shared`). Verified empirically 2026-07-14: settings-env **overrides** even a parent-exported TMPDIR for `claude -p` children, so engine-dispatched agents also write to `shared/` — per-iteration rotation does not apply to agent-side writes; the 72h `shared/` sweep (24h for pytest basetemps inside) is their reaper. Both lanes land on the big disk, which is the point.
-
-**AGENT RULE — disk-full errors are self-service, never a user interrupt:** on `No space left on device` or `Disk quota exceeded`, run `bash scripts/automation/tmp-doctor.sh --aggressive`, retry the failed command ONCE, and continue. NEVER `rm` arbitrary /tmp files (concurrent sessions own some of them), and NEVER halt the chain to ask the user about disk space.
-
-**Example (bad):** `tmp_log=$(mktemp /tmp/claude-quota-XXXXXX.log)` + keep-on-failure with no reaper — one leaked file per failed/quota invocation, forever.
-**Example (good):** `tmp_log=$(mktemp "${TMPDIR:-/tmp}/claude-quota-XXXXXX.log")`; on failure `_quota_preserve_failure_log "$tmp_log" claude-failure` moves it under `runs/<phase>/trace/`.
-
-**Detection:** `bash scripts/automation/tmp-doctor.sh --status` prints per-root usage with live/dead ownership. Suspicious signs: many numbered dirs under `pytest-of-$(id -un)`, `bench-*`/`judgment-*` dirs with a dead `.owner-pid`, or more than one `iad.*` dir per live pipeline job. A healthy run owns exactly ONE `iad.*` dir, and it disappears when the run exits.
-
----
-
-## 22. A scanner that reads the pipeline's own output flags itself forever
-
-**Pattern:** The goal-mode secret scan built its input as `git diff <snapshot>` plus EVERY untracked file — no path exclusion. Goal mode commits only after evaluation, so the harness's own generated artifacts (`runs/<sid>/iter-N/scan-report.md` — the scanner's previous output, which lists the matched token excerpts — plus `iter-diff.md`, `runs/<sid>/trace/`, `reports/**`, handoffs) were untracked at scan time and got scanned. Each build re-detected the tokens quoted in the previous build's report; agents then *explained* the false positive in prose, planting more copies in evaluator logs, summaries, and specs.
-
-**Why it fails:** Self-referential and monotonically growing — the finding count compounds every iteration (observed 1 → 3 → rising in tapeology session `yahoo_fetch`) and permanently blocks the GOAL_ACHIEVED gate on a product whose real diff is clean. Two iterations spent "fixing" it made it worse: every explanation or allowlist edit that quotes the token is new scan input. A second-order effect: the two per-iteration artifact builds (lean-path early build vs. the pre-evaluator rebuild) scanned different snapshots of the accumulating bookkeeping, so consumers reported CLEAN while the canonical report said CRITICAL. A third: bookkeeping could exhaust the untracked-file cap (200), silently hiding product files from the scan entirely.
-
-**Prevention:** Verifiers scan the PRODUCT, never the pipeline's bookkeeping. `goal_gate_build_diff_artifacts` applies `CHAIN_SCAN_BOOKKEEPING_EXCLUDES` (default `runs reports docs/handoffs docs/phases`, mirroring `CHAIN_STEP_HASH_EXCLUDES`) as a `:(exclude)` pathspec on BOTH the tracked diff and the untracked enumeration; the scan-report footer records the active scope. Do NOT fix this class of bug with value-based allowlists ("this token is a known fake") — that blinds the detector to the same token in real source and breaks the case-05 judgment fixture, which plants a fake credential in product code precisely to prove detection. The distinction is path-based (generated output vs. source), never value-based. Any file a pipeline stage GENERATES that can quote findings (reports, traces, logs, specs, handoffs) must be excluded from every scanner/verifier input, and fixture secrets inside scanner code itself must be assembled at runtime (keyword and value split) so the scanner's own diff can never trip it — both enforced by self-tests (`scan_diff.py self-test` self-scan guard; `goal-gates.sh --self-test` cases 11/12).
-
----
-
-## 23. Prompt-sized content crossing execve as a single argv/env string
-
-**Pattern:** The interactive dispatch builder passed the full agent prompt to `jq` as one `--arg` value (argv), with a python3 fallback that env-prefixed it (`_ID_P="$prompt"`, envp); the headless backends passed it as `claude -p "<prompt>"` / `codex exec "<prompt>"` argv. Linux caps every SINGLE argv/envp string at MAX_ARG_STRLEN (32 pages = 128 KiB), independent of total ARG_MAX — past it execve fails with E2BIG (`Argument list too long`) and the child never runs. Goal-mode prompt templates inlined line-capped-but-not-byte-capped evaluator-log/assumption tails, which crossed 128 KiB around iteration 40 of a 43-iteration production session: EVERY decomposer/evaluator/summarizer dispatch from there failed until a human pump operator hand-reconstructed prompts from on-disk artifacts. The bug survived at least one refactor because nothing regression-tested oversized prompts.
-
-**Why it fails:** Three compounding mistakes. (1) The per-string cap is invisible in testing — normal prompts are tens of KB, and the failure appears only when ONE string crosses it. (2) The shell performs the `> "$req"` redirect in the forked child BEFORE the exec attempt, so the failed builder still creates a 0-byte file. (3) The builder's exit status was never checked, so the empty request was atomically PUBLISHED — the pump claimed a payload with no agent/prompt/res_path and the engine sat in the inflight wait (24 h in production config). The requeue path rebuilt the same oversized prompt and failed deterministically; the python3 fallback could never rescue the jq branch because envp shares the same per-string cap as argv.
-
-**Prevention:** Applies to any code handing agent prompts (or other unbounded content) to a child process, and to any code publishing channel artifacts.
-- Unbounded content NEVER crosses execve as one argv/env string. Route it via a file written by the shell builtin `printf` (no exec, no cap) + `jq --rawfile`, via stdin (`< file`, or `< <(printf '%s' "$var")` from a NON-exported shell variable), or a heredoc. Exporting the variable — including an `X="$big" cmd` env-prefix — re-introduces the same E2BIG via envp.
-- Validate channel artifacts BEFORE publishing: non-empty (`[[ -s f ]]`) FIRST — a broken builder that exits 0 writing nothing also defeats tool-based validation — then a JSON parse; on failure log loudly (agent + prompt size) and return WITHOUT publishing. (`lib/interactive-dispatch.sh` publish guard; self-tests 13–15.)
-- Producer side: byte-cap inlined log tails, not just line-cap (`_tail_or_placeholder`, `CHAIN_INLINE_TAIL_MAX_BYTES` default 48 KiB, marker names the on-disk file). The dispatch layer must still handle arbitrary sizes — the cap is bloat/token control, not the fix.
-- Headless: prompts past `CHAIN_PROMPT_ARGV_MAX` (default 100000 bytes) are fed on stdin (`claude -p` reads the prompt from stdin; `codex exec -` is the stdin sentinel); below the threshold argv is used exactly as before (`_invoke_with_prompt_stdin`; oversized-routing tests in test-quota-retry.sh).
-
-**Example (bad):** `jq -cn --arg p "$prompt" '{prompt:$p}' > req.json; mv req.json req.json.ready` — a 200 KB prompt means jq never execs, yet the 0-byte redirect target is still created and published.
-**Example (good):** `printf '%s' "$prompt" > "$pf"; jq -cn --rawfile p "$pf" '{prompt:$p}' > req.json 2>/dev/null; [[ -s req.json ]] && jq -e . req.json >/dev/null 2>&1 || { echo "build failed" >&2; return 2; }`
-
-**Detection:** `bash: …: Argument list too long` in engine stderr; a 0-byte `req.*.ready` in the channel dir; the pump claiming a request whose JSON has no fields. 30-second repro: `p="$(head -c 200000 /dev/zero | tr '\0' x)"; jq -cn --arg p "$p" . > /tmp/r.json` fails and leaves `/tmp/r.json` at 0 bytes.
diff --git a/incredible_auto_dev/.claude/anti-patterns/01-vague-acceptance-criteria.md b/incredible_auto_dev/.claude/anti-patterns/01-vague-acceptance-criteria.md
new file mode 100644
index 0000000..79126bf
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/01-vague-acceptance-criteria.md
@@ -0,0 +1,16 @@
+## 1. Vague acceptance criteria cause infinite review loops
+
+**Pattern:** Phase specs contain requirements like "works correctly", "handles all cases", or "the UI should look nice."
+
+**Why it fails:** The reviewer and the developer use different interpretations of "correct". Each review cycle produces a FAIL for a different reason. After 3 loops the pipeline halts with no clear fix.
+
+**Prevention:** Every item in DEFINITION OF DONE must be:
+- Specific: "POST /api/items returns 201 with the created item's ID"
+- Testable: a concrete pass/fail condition, not a judgment
+- Scoped: tied to this phase only, not aspirational future state
+
+**Example (bad):** "The form submission should work."
+**Example (good):** "Submitting a valid form creates a record in the database and redirects to the detail page. Submitting an invalid form shows field-level error messages and does not create a record."
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/02-hardcoded-stack-paths.md b/incredible_auto_dev/.claude/anti-patterns/02-hardcoded-stack-paths.md
new file mode 100644
index 0000000..a49dd16
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/02-hardcoded-stack-paths.md
@@ -0,0 +1,10 @@
+## 2. Hardcoded stack paths in agent prompts break portability
+
+**Pattern:** Agent definitions or scripts contain paths like `apps/backend/.venv/bin/python -m pytest` or `cd apps/backend && alembic upgrade head` embedded directly.
+
+**Why it fails:** When the framework is adopted by a new project, every agent file needs manual editing. Agents in the pipeline inherit the wrong paths and fail silently.
+
+**Prevention:** All stack-specific commands live in `.claude/project-template.md`. Agent definitions reference the template: "Run the test command from project-template.md." Scripts use env vars (`CHAIN_START_BACKEND_CMD`) or conventionally-named scripts (`scripts/start-backend.sh`).
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/03-merged-developer-agent.md b/incredible_auto_dev/.claude/anti-patterns/03-merged-developer-agent.md
new file mode 100644
index 0000000..8f6b947
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/03-merged-developer-agent.md
@@ -0,0 +1,10 @@
+## 3. Merged backend+frontend into one developer agent reduces flexibility
+
+**Pattern (anti):** Splitting implementation into separate backend-only and frontend-only agents with separate model invocations.
+
+**Why it's a false economy:** The backend agent writes the handoff, then the frontend agent reads it and adds another handoff. Two sequential long-context invocations for work that shares context. Each agent re-reads the spec, plan, and existing code from scratch.
+
+**Prevention:** A single developer agent handles both. The plan marks `Frontend Present: yes/no`. On yes, the agent implements backend first, then frontend in the same session. Alternatively, run two passes of the same developer agent (backend pass, then frontend pass) using the same agent definition with different context flags.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/04-ui-evolution-afterthought.md b/incredible_auto_dev/.claude/anti-patterns/04-ui-evolution-afterthought.md
new file mode 100644
index 0000000..b4902b0
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/04-ui-evolution-afterthought.md
@@ -0,0 +1,10 @@
+## 4. UI evolution is an afterthought, not a pipeline gate
+
+**Pattern:** QA runs unit tests, they pass, phase is declared done. Three phases later the product manager notices the user can't access the new feature because no navigation link was added.
+
+**Why it fails:** Unit tests don't check whether the UI exposes the capability. A backend feature is invisible until the UI surfaces it.
+
+**Prevention:** The UI Evolution Audit is part of every phase with `Frontend Present: yes`. `UI-FAIL` blocks overall QA PASS. Review checklist explicitly checks for navigation updates and detail/list pages.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/05-quota-exhaustion-no-retry.md b/incredible_auto_dev/.claude/anti-patterns/05-quota-exhaustion-no-retry.md
new file mode 100644
index 0000000..60d4d51
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/05-quota-exhaustion-no-retry.md
@@ -0,0 +1,13 @@
+## 5. Quota exhaustion mid-pipeline without retry causes data loss
+
+**Pattern:** A 6-stage pipeline runs unattended. At stage 4 (QA), Claude hits the usage quota and exits. The partial run state is lost. The pipeline must restart from scratch.
+
+**Why it fails:** Wasted compute. Worse, if stage 3 (dev) made changes that weren't committed, the developer re-implements the same code differently on retry, causing drift.
+
+**Prevention:**
+- Checkpoint/resume via `runs/<phase>/status.json` — completed stages are skipped on re-run
+- `quota-retry.sh` wraps every Claude invocation — detects quota messages, parses the reset time, sleeps and retries automatically
+- Never start a long pipeline before verifying quota headroom
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/06-review-without-file-line.md b/incredible_auto_dev/.claude/anti-patterns/06-review-without-file-line.md
new file mode 100644
index 0000000..2c15668
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/06-review-without-file-line.md
@@ -0,0 +1,17 @@
+## 6. Review reports without file:line references are useless
+
+**Pattern:** Review report says "the validation logic has issues" or "error handling could be improved."
+
+**Why it fails:** The developer reads the report, doesn't know which file or line to fix, makes a guess, and the reviewer flags the same "issue" again in the next loop.
+
+**Prevention:** Every finding in a review report MUST include:
+- Exact file path
+- Line number or function name
+- Specific problem description
+- Specific fix description
+
+**Example (bad):** "Error handling is insufficient."
+**Example (good):** "`apps/backend/routers/items.py:47` — `create_item` does not catch `IntegrityError` from SQLAlchemy. Add a try/except that returns 409 Conflict when a duplicate key is detected."
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/07-reviewer-qa-fixing-code.md b/incredible_auto_dev/.claude/anti-patterns/07-reviewer-qa-fixing-code.md
new file mode 100644
index 0000000..ca3e741
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/07-reviewer-qa-fixing-code.md
@@ -0,0 +1,13 @@
+## 7. Reviewer and QA validator that fix code bypass the feedback loop
+
+**Pattern:** The reviewer notices a bug and edits the file to fix it "since it's obvious." The QA validator notices a test failure and patches the test to pass.
+
+**Why it fails:** The developer agent doesn't learn from the correction. On the next phase, the same mistake recurs because the developer never saw it as a fix — only the reviewer did. More critically: reviewer fixes can silently introduce new bugs that QA was supposed to catch, but QA didn't see the reviewer's changes.
+
+**Prevention:**
+- Reviewer NEVER edits source files — writes the report only
+- QA NEVER fixes test failures — writes them as blockers
+- Only the developer (and auditor, for critical post-QA issues) modifies source code
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/08-freeform-agent-conversation.md b/incredible_auto_dev/.claude/anti-patterns/08-freeform-agent-conversation.md
new file mode 100644
index 0000000..fd08a08
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/08-freeform-agent-conversation.md
@@ -0,0 +1,10 @@
+## 8. Free-form agent conversation leads to hallucinated agreements
+
+**Pattern:** Two agents "discuss" a design decision in chat. Agent B says "OK I'll implement it your way." Agent B then implements something different because its actual context window didn't include the full conversation.
+
+**Why it fails:** Chat messages between agents are not in each agent's context window. Agents only have access to what was in their initial prompt and what they've read from files in the current session.
+
+**Prevention:** Agents communicate ONLY through filesystem artifacts. No "pass a message to the next agent." The orchestrator writes a plan to a file; the developer reads that file. The developer writes a handoff; the reviewer reads that file. This is the only reliable inter-agent communication.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/09-missing-functional-test-plans.md b/incredible_auto_dev/.claude/anti-patterns/09-missing-functional-test-plans.md
new file mode 100644
index 0000000..801af05
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/09-missing-functional-test-plans.md
@@ -0,0 +1,10 @@
+## 9. Missing functional test plans make QA rubber-stamp
+
+**Pattern:** QA runs `pytest` and reports PASS. The test suite covers internal functions but doesn't verify the user-facing feature works end-to-end. A critical API endpoint is broken but no test covers it.
+
+**Why it fails:** "Tests pass" and "the feature works for a user" are different claims. Without a functional test plan derived from the spec, QA only validates what the developer chose to test, not what the spec required.
+
+**Prevention:** The test plan generator runs BEFORE QA, deriving explicit test cases from the spec's DEFINITION OF DONE and REQUIRED USER FLOWS. QA must execute each TC-01, TC-02, ... test case and record actual vs expected outcomes. A test case failure is a blocker.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/10-supply-chain-attacks.md b/incredible_auto_dev/.claude/anti-patterns/10-supply-chain-attacks.md
new file mode 100644
index 0000000..f29535e
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/10-supply-chain-attacks.md
@@ -0,0 +1,10 @@
+## 10. Supply-chain attacks target autonomous agents
+
+**Pattern:** A compromised PyPI or npm package gets installed by an agent during a phase run. The agent has no reason to be suspicious — it's just running the install command from the spec.
+
+**Why it fails:** Autonomous agents install packages without human review. A single compromised dependency can exfiltrate secrets, modify the codebase, or establish persistence — all while the pipeline continues normally.
+
+**Prevention:** The install security gate intercepts every `pip install`, `npm install`, `git clone`, and `curl|bash` command. On Claude Code it reads the PreToolUse JSON from stdin (`.tool_input.command` — `$CLAUDE_TOOL_INPUT_COMMAND` never existed; SEC-7 fixed the plumbing) and enforces via an agent-visible `permissionDecision:"deny"` with the remediation in the reason (pin the version / edit the `config/install-security-policy.json` allowlist / `CHAIN_INSTALL_GATE_BYPASS=true`) — never a user prompt. Registry packages are warn-mode (SEC-6: proceed + logged banner); direct URLs, tarballs, custom indexes, denylist hits, unknown requirements files, unpinned git clones, and real (unquoted — quoted mentions pass) `curl|bash` deny. All decisions are logged to `reports/security/install-decisions.jsonl`. The gate is a non-negotiable pipeline component — it is not "paranoia."
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/11-spec-without-definition-of-done.md b/incredible_auto_dev/.claude/anti-patterns/11-spec-without-definition-of-done.md
new file mode 100644
index 0000000..33875fa
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/11-spec-without-definition-of-done.md
@@ -0,0 +1,10 @@
+## 11. One large phase spec with no DEFINITION OF DONE
+
+**Pattern:** A phase spec describes 8 features in general terms, with no numbered acceptance checklist.
+
+**Why it fails:** The orchestrator doesn't know what "done" looks like. The developer implements 5 of the 8 things. The reviewer gives PASS_WITH_NOTES on the missing 3. QA gives PASS because tests pass. The audit gives FAIL because the spec goal wasn't reached. The pipeline re-runs from dev — wasting 3 cycles that could have been avoided.
+
+**Prevention:** Every phase spec MUST have a numbered DEFINITION OF DONE checklist. Each item is specific and testable. The auditor's primary job is to verify this checklist against actual code, not summaries.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/12-agents-summarize-not-read.md b/incredible_auto_dev/.claude/anti-patterns/12-agents-summarize-not-read.md
new file mode 100644
index 0000000..7285a9a
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/12-agents-summarize-not-read.md
@@ -0,0 +1,10 @@
+## 12. Agents that "summarize" instead of reading source code
+
+**Pattern:** The auditor reads the dev handoff and QA report, concludes "tests pass and the handoff describes the implementation," and gives PASS.
+
+**Why it fails:** The handoff is a summary written by the agent that implemented the code. It naturally omits mistakes. The QA report validates what the developer chose to test. Neither is a substitute for reading the actual source files.
+
+**Prevention:** Auditor instructions explicitly state: "Read actual source files, not summaries. If you cannot verify a claim from code, trace through the implementation. Never trust a handoff summary alone."
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/13-backend-without-ui-verification.md b/incredible_auto_dev/.claude/anti-patterns/13-backend-without-ui-verification.md
new file mode 100644
index 0000000..824696a
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/13-backend-without-ui-verification.md
@@ -0,0 +1,18 @@
+## 13. Backend capabilities without UI verification leads to invisible features
+
+**Pattern:** A phase adds 3 new API endpoints. Unit tests pass. QA validates the APIs. Audit gives PASS. But no one verified that the user can actually reach these features from the UI. Three phases later, someone clicks through the app and discovers half the features have no navigation path.
+
+**Why it fails:** "Tests pass" and "the feature works for a user" are completely different claims. A feature that exists in the backend but has no UI entry point is invisible product capability — it was built but cannot be used.
+
+**Prevention:** The UI visibility system produces 6 artifacts per phase:
+- `implementation-summary` — what was built
+- `user-visible-changes` — what users can now do
+- `ui-surface-map` — which routes/components changed and what to test
+- `ui-test-plan` — exact click paths and expected outcomes
+- `ui-test-results` — browser automation evidence
+- `what-to-click` — 5-minute operator verification guide
+
+The phase closure auditor blocks completion when these artifacts are missing or vague. Browser QA must test actual user workflows, not just that pages render.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/14-vague-test-steps.md b/incredible_auto_dev/.claude/anti-patterns/14-vague-test-steps.md
new file mode 100644
index 0000000..bc16500
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/14-vague-test-steps.md
@@ -0,0 +1,10 @@
+## 14. Vague test steps make test plans useless
+
+**Pattern:** A test plan says "test the form submission" or "verify results are correct." The browser QA agent cannot execute this. A human tester cannot follow this. The plan exists but adds no value.
+
+**Why it fails:** Vague test steps produce vague results. "Tested and it works" is not evidence. A test plan that cannot produce reproducible pass/fail evidence is not a test plan.
+
+**Prevention:** Every test step must specify: exact URL, exact element to interact with (by name or visible label), exact value to input, and exact expected outcome. The `post-write-artifact-quality.sh` hook warns when phase report files contain vague placeholder lines. The `what-to-click-writer` skill enforces concrete step writing.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/15-mocked-only-external-tests.md b/incredible_auto_dev/.claude/anti-patterns/15-mocked-only-external-tests.md
new file mode 100644
index 0000000..b09a99b
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/15-mocked-only-external-tests.md
@@ -0,0 +1,14 @@
+## 15. Mocked-only tests for external integrations pass while live adapter is broken
+
+**Pattern:** Adapter tests mock all HTTP/browser calls. Tests pass. But the real site changed its HTML structure, blocks headless browsers, or requires auth. No one discovers this until manual testing.
+
+**Why it fails:** Mocked tests validate the parsing logic against a frozen snapshot of the external system. They never detect selector drift, bot detection, geo-blocking, or TLS fingerprint rejection. 100% mocked test coverage gives false confidence that the integration works.
+
+**Prevention:** For phases that add external integrations (scrapers, APIs, webhooks), the developer must include at least one test marked `@pytest.mark.integration` (or equivalent) that hits the real external system. QA functional test plan must include a live integration test case. These tests may be slow/flaky and skipped in CI, but must exist and be run at least once during the phase. The dev handoff must explicitly state whether live testing was successful or document the blocker if it wasn't.
+
+**Example (bad):** All Tesco adapter tests use `_build_tile_html()` fixtures. Tests pass. Tesco changes its CSS classes → live adapter returns 0 results. Bot detection blocks headless Playwright → adapter gets HTTP 403. Neither is caught until a human clicks through the UI.
+
+**Example (good):** One test marked `@pytest.mark.integration` calls `TescoAdapter().search("milk")` against the real Tesco site and asserts `len(results) > 0`. This test is slow but catches selector drift, bot detection, and infrastructure issues immediately.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/16-hardcoded-localhost.md b/incredible_auto_dev/.claude/anti-patterns/16-hardcoded-localhost.md
new file mode 100644
index 0000000..db0cbfd
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/16-hardcoded-localhost.md
@@ -0,0 +1,21 @@
+## 16. Hardcoded localhost in service configuration breaks non-local access
+
+**Pattern:** API URLs, CORS origins, and service bindings all use `localhost` or `127.0.0.1`. Works on the dev machine's browser. Breaks when accessed from another machine via private IP, from a VM host, through Docker, or behind a reverse proxy.
+
+**Why it fails:** The frontend sends API requests to the hardcoded `localhost:8000`. A user on another machine resolves `localhost` to their own loopback — the backend isn't there. Even if the backend is reachable by IP, restrictive CORS blocks the request. Even if CORS allows it, the backend only listens on `127.0.0.1` and rejects non-loopback connections.
+
+**Prevention:** Reviewer checklist flags any hardcoded `localhost`/`127.0.0.1` in:
+- API client URLs → must be configurable via env var or derived dynamically (e.g., `window.location.hostname`)
+- CORS origins → must use `*`, a port-range regex (e.g. `http://(localhost|127\.0\.0\.1):\d+`), or be configurable in dev mode
+- Service bindings → dev scripts must bind to `0.0.0.0`, not `127.0.0.1`
+- Dev scripts (`dev.sh`, `start-frontend.sh`) → must pass host/port via env var, not hardcoded URL strings
+
+**Sub-pattern — auto-dev-chain port drift:** `ensure_phase_ports` in `lib/common.sh` assigns a hashed preferred port and falls back to the next free port if taken (e.g., 3101 → 3102 when a stale server holds 3101). A CORS whitelist of specific ports (e.g. `[..., "http://localhost:3101"]`) will reject the fallback port and the QA/browser-QA frontend will fail to fetch data, while `curl` still works. Use a regex or env-driven allowlist so any dev port works.
+
+**Example (bad):** `const API_BASE = "http://localhost:8000"` — works only from the same machine.
+**Example (good):** `const API_BASE = \`http://${window.location.hostname}:${API_PORT}\`` — works from any hostname the user accesses the frontend with.
+**Example (CORS bad):** `allow_origins=["http://localhost:3101"]` — breaks when chain falls back to 3102.
+**Example (CORS good, FastAPI):** `allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+"`.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/17-long-sleep-suspend.md b/incredible_auto_dev/.claude/anti-patterns/17-long-sleep-suspend.md
new file mode 100644
index 0000000..92e8bf0
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/17-long-sleep-suspend.md
@@ -0,0 +1,13 @@
+## 17. Long `sleep` blocks the chain across system suspend/resume
+
+**Pattern:** Quota-retry logic calls `sleep 11137` (e.g. 3 hours) to wait for the Anthropic reset. The user closes the laptop lid, system suspends. On wake the next day, the sleep continues ticking monotonically instead of noticing that wall-clock time already passed the reset — the chain blocks for many hours past the intended wake-up.
+
+**Why it fails:** On Linux, `sleep N` in coreutils may sleep against the monotonic clock (pauses during suspend) or depend on the kernel honoring RTC wake-up. Across suspend/hibernate, neither guarantee is reliable: a 3-hour sleep that straddles an overnight suspend can block for 12+ hours. The pipeline is not crashed — it is silently wedged in a sleep that the user can only detect by inspecting `/proc/<pid>/wchan`.
+
+**Prevention:** Long waits must target an absolute wall-clock epoch, not a duration. `lib/quota-retry.sh::_sleep_until_epoch` polls `date +%s` against the target epoch in ≤60-second chunks — on resume, the very next poll sees the epoch has passed and the sleep exits. Any new pipeline script that needs to wait more than ~60 seconds MUST use `_sleep_until_epoch` rather than `sleep $secs`.
+
+**Example (bad):** `sleep "$sleep_secs"` where `sleep_secs` may be hours — stuck indefinitely if the laptop suspends.
+**Example (good):** `_sleep_until_epoch "$reset_epoch"` — guaranteed to return within 60s of wall clock reaching the target.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/18-goal-journeys-anti-goals.md b/incredible_auto_dev/.claude/anti-patterns/18-goal-journeys-anti-goals.md
new file mode 100644
index 0000000..5469fc4
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/18-goal-journeys-anti-goals.md
@@ -0,0 +1,36 @@
+## 18. Goal mode without Must-have journeys or Anti-goals
+
+**Pattern:** A user authors `docs/goal.md` from the template but skips or leaves placeholder content in the **Must-have user journeys** and **Anti-goals** sections, then runs `./scripts/automation/run-goal.sh`. The goal-decomposer produces vague iter specs and the goal-evaluator has no concrete evidence to anchor its `GOAL_ACHIEVED` decision.
+
+**Why it fails:** Goal mode uses an AI evaluator to decide when the loop terminates. Without specific journeys, the evaluator falls back on subjective judgment — best case it loops forever (related to anti-pattern #1), worst case it declares done prematurely on something that doesn't actually work for users. Anti-goals serve as veto criteria; without them the evaluator may rubber-stamp a violation (committed credentials, paid-SaaS dependency, accessibility regression) just because the journeys click through.
+
+**Prevention:**
+- `run-goal.sh` validates `docs/goal.md` on first run: it MUST contain a non-empty Must-have user journeys section with at least one journey, and a non-empty Anti-goals section. The script aborts with a clear error message if either is empty or contains only the template placeholders.
+- Each journey in goal.md MUST have an ID (`J-NN`), numbered click/type/assert steps the browser-qa-agent can execute, and an "Acceptance" line describing the observable end state. The goal-evaluator references these by ID, so missing IDs break the journey-history tracking.
+- Anti-goals MUST be concrete, checkable rules (e.g., "no hard-coded credentials in source files"), not aspirations ("be secure"). Concrete rules let the evaluator classify violations as critical (halts loop) vs minor (continues with fix recommendation).
+
+**Example (bad):**
+```
+## Must-have user journeys
+- TODO: fill in later
+
+## Anti-goals
+- Be secure.
+- Be fast.
+```
+
+**Example (good):**
+```
+## Must-have user journeys
+- **J-01: Sign up and log in**
+  - Steps: 1. visit /signup  2. enter email+password  3. submit  4. expect /dashboard  5. log out  6. log in again  7. expect /dashboard
+  - Acceptance: dashboard greeting shows the user's email
+
+## Anti-goals
+- No hard-coded credentials, API keys, or tokens in source.
+- Auth tokens MUST NOT be stored in localStorage (httpOnly cookies only).
+- No dependency on a paid SaaS service unless explicitly listed in Constraints.
+```
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/19-timeout-swallows-ctrl-c.md b/incredible_auto_dev/.claude/anti-patterns/19-timeout-swallows-ctrl-c.md
new file mode 100644
index 0000000..0e5060b
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/19-timeout-swallows-ctrl-c.md
@@ -0,0 +1,17 @@
+## 19. `timeout`-wrapped child swallows terminal Ctrl-C
+
+**Pattern:** A long-running command is wrapped with GNU `timeout` for a runtime cap (e.g. `timeout 7200 claude --print "$prompt"`). The user presses Ctrl-C in the terminal and… nothing happens. The shell prints no abort message, no trap fires, and the prompt does not return for many seconds — sometimes minutes — until the wrapped command happens to finish on its own.
+
+**Why it fails:** GNU `timeout` defaults to placing its child in a **new process group** via `setpgid(2)`. Terminal Ctrl-C delivers SIGINT to the foreground process group only, which now contains just the parent shell — *not* the wrapped command. The shell receives the signal and queues the trap, but then has to wait for the pipeline to complete before running the trap; the wrapped command never received SIGINT, so it keeps running. From the user's perspective the script is unresponsive. Eventually the command exits naturally and only then does the queued trap fire — by which point the user has assumed Ctrl-C was lost and probably reached for `kill -9` or closed the terminal.
+
+This is especially bad for AI-agent scripts: the wrapped `claude` keeps consuming API credits long after the user thought they aborted.
+
+**Prevention:** pass `--foreground` to `timeout` (or otherwise keep the child in the parent's process group). With `--foreground`, the wrapped command stays in the parent's pgrp and terminal Ctrl-C reaches it directly. The documented downside — grandchildren of the wrapped command are not timed out — is acceptable for harness use cases where the wrapped command (e.g., `claude`) manages its own subprocesses.
+
+**Example (bad):** `timeout --kill-after=60 7200 claude -p "$prompt" 2>&1 | tee log` — terminal Ctrl-C does NOT reach claude. Trap is queued but blocked.
+**Example (good):** `timeout --foreground --kill-after=60 7200 claude -p "$prompt" 2>&1 | tee log` — terminal Ctrl-C reaches claude immediately; trap fires within milliseconds.
+
+**Detection:** if `kill -INT $shell_pid` exits the shell quickly but terminal Ctrl-C feels "stuck", that's the smoking gun. Confirm with `ps -o pid,pgid,cmd <child_pid>` — if the child's PGID differs from the parent shell's, you've got the bug.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/20-next-build-against-dev.md b/incredible_auto_dev/.claude/anti-patterns/20-next-build-against-dev.md
new file mode 100644
index 0000000..5186dc9
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/20-next-build-against-dev.md
@@ -0,0 +1,14 @@
+## 20. `next build` against a live `next dev` corrupts `.next` and SKIPs the demo
+
+**Pattern:** A production `next build` (or a typecheck/lint step that triggers a build) runs while the demo/QA `next dev` server is up. Both write the **same** `apps/frontend/.next` directory, so the build deletes/renames the webpack chunks the dev server is serving. The dev server then answers **every** request with HTTP 500 (`MODULE_NOT_FOUND`, a require stack through `.next/server/...`/`webpack-runtime.js`) and never recovers on its own. The per-iteration demo / browser-QA then report "Frontend did not respond after 90s of retries" and record **SKIPPED**, even though the server is up — it is just 500ing.
+
+**Why it fails:** `next dev` lazily reads compiled chunks from `.next`; a concurrent `next build` clobbers them. The corruption is sticky — only removing `.next` and letting `next dev` rebuild fixes it. In the post-dev fanout this cascades: the shared-services boot tries to start the frontend, fails on the corrupt build, kills it, and every parallel branch (demo, browser-qa) then waits out its readiness budget against a dead port.
+
+**Prevention (harness side, already done):** the harness now self-heals. `_start_service_with_retries` (in `scripts/automation/lib/common.sh`) detects the corrupt-`.next` signature, clears `.next`, and grants one guaranteed-cold rebuild attempt with a longer budget (`CHAIN_FRONTEND_HEAL_TIMEOUT`, default 180s) instead of killing a still-compiling server; `_kill_pid_tree` now escalates TERM→KILL so a surviving worker can't re-corrupt `.next` or squat the port; and the readiness gate `_wait_for_frontend_ready` heals once on the standalone path. Recovery costs a full cold compile per occurrence, so it is a cost, not a free pass.
+
+**Prevention (project side, optional but better):** give build/QA/typecheck commands their own dist dir so they never touch the dev build. Next.js reads `distDir` from `next.config.{js,ts}` (NOT an env var by default), so wire it through config — e.g. `distDir: process.env.NEXT_DIST_DIR || '.next'` — and run builds with `NEXT_DIST_DIR=.next-qa next build`. Agents MUST NOT run a production `next build` while the demo/QA `next dev` is up unless the build is isolated this way.
+
+**Detection:** the frontend start log (`$QA_FRONTEND_LOG` — under the run's `CHAIN_TMPDIR`, e.g. `.../fanout-frontend-<port>.log`) showing `MODULE_NOT_FOUND` / `Cannot find module` with a `GET / 500` and a `.next/server/...` require stack is the signature. `_next_build_is_corrupt` in `common.sh` greps for exactly this.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/21-shared-tmp-accumulation.md b/incredible_auto_dev/.claude/anti-patterns/21-shared-tmp-accumulation.md
new file mode 100644
index 0000000..bd97a01
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/21-shared-tmp-accumulation.md
@@ -0,0 +1,25 @@
+## 21. Shared /tmp accumulation and cross-job pytest tmp races
+
+**Pattern:** Nothing sets `TMPDIR`, so every tool the agents run (pytest, playwright/chromium, `mktemp`) writes into shared `/tmp`. pytest's default basetemp `/tmp/pytest-of-<user>/` is keyed on the USER, not the run — concurrent pipeline jobs (different projects, same machine, same user) share it and race pytest's own "keep last 3, rmtree older" pruning (`Directory not empty`, lock races, stale undeletable dirs). Meanwhile the harness's own temp files pile up forever: kept-on-failure `claude-quota-*.log`s, telemetry usage sidecars leaked on every non-success path, and per-role service logs (`fanout-*`, `demo-*`, `goal-iter-*`) that no cleanup path ever targeted. Cleanup ran only on run-phase.sh's success path — never on `fail()`, quota/transport/signal exits, or lean goal iterations.
+
+**Why it fails:** `/tmp` is a shared namespace with no run identifier, so no cleanup step can safely delete anything (it might belong to a concurrent job) — and agents could not delete anyway (see the rm-ban fix: deny-rule over-match + Claude Code's built-in rm working-directory containment). The only "cleanup" was pytest pruning itself, which is exactly the thing that races.
+
+**Prevention:** per-run tmp isolation via `lib/chain-tmp.sh` (REL-13 moved the root OFF /tmp entirely — on this class of machine `/tmp` is a quota'd tmpfs that EDQUOTs long before it looks full):
+- Every entry script (run-phase.sh, run-goal.sh, goal-iter-lean.sh) calls `chain_tmp_init <run-id>`, which creates `$CHAIN_TMP_ROOT/iad.<id>.<pid>` (root default `~/.cache/iad`: big un-quota'd ext4, NOT /tmp) and exports it as `TMPDIR`/`TMP`/`TEMP`; a nested script ADOPTS the inherited dir (owner-guarded, and only while the recorded owner pid is still alive). The WHOLE TMPDIR is kept ≤62 chars (Chromium's 108-char unix-socket limit); long run-ids are shortened to `<prefix>-<sha256-first8>` with the raw id in `.chain-run-id`. NEW pipeline entry scripts MUST do the same.
+- Cleanup is an EXIT trap (fires on success, fail(), quota 75, transport 70, signal exits) plus `chain_tmp_rotate` at the goal-mode iteration boundary — after `_join_showcase_tail`, never right after the evaluator (the async showcase tail still writes there).
+- New `mktemp` calls MUST use a `"${TMPDIR:-/tmp}/…"` template, never a hardcoded `/tmp/...` template. Standalone scratch roots (benchmarks, judgment sandboxes) use `"${CHAIN_TMP_ROOT:-${TMPDIR:-$HOME/.cache/iad}}"` and write an `.owner-pid` file so the janitor can tell live from leaked.
+- Files deliberately kept for debugging MUST be moved to `$CHAIN_TRACE_DIR` (`_quota_preserve_failure_log`), never left in tmp.
+- The ONLY sanctioned fixed-name /tmp files are the two quota sentinels (`/tmp/{claude,codex}-quota-exhausted`) — quota is account-global, every concurrent job must see the same sentinel, and `chain_tmp_janitor` never matches their names.
+- `chain_tmp_janitor` (entry-script start) reaps strays across `$CHAIN_TMP_ROOT` AND the legacy roots (`CHAIN_TMP_LEGACY_ROOTS`, default `/tmp`): `iad.*` dirs whose owner pid is dead (age-gated normally; ANY age under `--aggressive`), `bench-*` scratch beyond the newest `CHAIN_BENCH_KEEP=2`, `judgment-*` sandboxes, legacy loose temp files, `pytest-of-$USER` entries, and `$CHAIN_TMP_ROOT/shared` entries older than `CHAIN_TMP_SHARED_MAX_AGE_HOURS=72`. Tests that call the janitor MUST pass `CHAIN_TMP_LEGACY_ROOTS=""` or they will sweep the real /tmp.
+- `chain_tmp_disk_guard` (engine preflight + top of every goal iteration) checks free space (statvfs on the root; a WRITE PROBE on /tmp because statvfs cannot see tmpfs user quotas) and runs the aggressive janitor under pressure. Only a still-critical `CHAIN_TMP_ROOT` filesystem pauses the session (resumable `AWAITING_DISK`); /tmp pressure alone is warn-only.
+- Interactive/subagent runs get TMPDIR from the user-global `~/.claude/settings.json` `env` block (`TMPDIR=~/.cache/iad/shared`). Verified empirically 2026-07-14: settings-env **overrides** even a parent-exported TMPDIR for `claude -p` children, so engine-dispatched agents also write to `shared/` — per-iteration rotation does not apply to agent-side writes; the 72h `shared/` sweep (24h for pytest basetemps inside) is their reaper. Both lanes land on the big disk, which is the point.
+
+**AGENT RULE — disk-full errors are self-service, never a user interrupt:** on `No space left on device` or `Disk quota exceeded`, run `bash scripts/automation/tmp-doctor.sh --aggressive`, retry the failed command ONCE, and continue. NEVER `rm` arbitrary /tmp files (concurrent sessions own some of them), and NEVER halt the chain to ask the user about disk space.
+
+**Example (bad):** `tmp_log=$(mktemp /tmp/claude-quota-XXXXXX.log)` + keep-on-failure with no reaper — one leaked file per failed/quota invocation, forever.
+**Example (good):** `tmp_log=$(mktemp "${TMPDIR:-/tmp}/claude-quota-XXXXXX.log")`; on failure `_quota_preserve_failure_log "$tmp_log" claude-failure` moves it under `runs/<phase>/trace/`.
+
+**Detection:** `bash scripts/automation/tmp-doctor.sh --status` prints per-root usage with live/dead ownership. Suspicious signs: many numbered dirs under `pytest-of-$(id -un)`, `bench-*`/`judgment-*` dirs with a dead `.owner-pid`, or more than one `iad.*` dir per live pipeline job. A healthy run owns exactly ONE `iad.*` dir, and it disappears when the run exits.
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/22-scanner-flags-own-output.md b/incredible_auto_dev/.claude/anti-patterns/22-scanner-flags-own-output.md
new file mode 100644
index 0000000..7cd69cb
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/22-scanner-flags-own-output.md
@@ -0,0 +1,10 @@
+## 22. A scanner that reads the pipeline's own output flags itself forever
+
+**Pattern:** The goal-mode secret scan built its input as `git diff <snapshot>` plus EVERY untracked file — no path exclusion. Goal mode commits only after evaluation, so the harness's own generated artifacts (`runs/<sid>/iter-N/scan-report.md` — the scanner's previous output, which lists the matched token excerpts — plus `iter-diff.md`, `runs/<sid>/trace/`, `reports/**`, handoffs) were untracked at scan time and got scanned. Each build re-detected the tokens quoted in the previous build's report; agents then *explained* the false positive in prose, planting more copies in evaluator logs, summaries, and specs.
+
+**Why it fails:** Self-referential and monotonically growing — the finding count compounds every iteration (observed 1 → 3 → rising in tapeology session `yahoo_fetch`) and permanently blocks the GOAL_ACHIEVED gate on a product whose real diff is clean. Two iterations spent "fixing" it made it worse: every explanation or allowlist edit that quotes the token is new scan input. A second-order effect: the two per-iteration artifact builds (lean-path early build vs. the pre-evaluator rebuild) scanned different snapshots of the accumulating bookkeeping, so consumers reported CLEAN while the canonical report said CRITICAL. A third: bookkeeping could exhaust the untracked-file cap (200), silently hiding product files from the scan entirely.
+
+**Prevention:** Verifiers scan the PRODUCT, never the pipeline's bookkeeping. `goal_gate_build_diff_artifacts` applies `CHAIN_SCAN_BOOKKEEPING_EXCLUDES` (default `runs reports docs/handoffs docs/phases`, mirroring `CHAIN_STEP_HASH_EXCLUDES`) as a `:(exclude)` pathspec on BOTH the tracked diff and the untracked enumeration; the scan-report footer records the active scope. Do NOT fix this class of bug with value-based allowlists ("this token is a known fake") — that blinds the detector to the same token in real source and breaks the case-05 judgment fixture, which plants a fake credential in product code precisely to prove detection. The distinction is path-based (generated output vs. source), never value-based. Any file a pipeline stage GENERATES that can quote findings (reports, traces, logs, specs, handoffs) must be excluded from every scanner/verifier input, and fixture secrets inside scanner code itself must be assembled at runtime (keyword and value split) so the scanner's own diff can never trip it — both enforced by self-tests (`scan_diff.py self-test` self-scan guard; `goal-gates.sh --self-test` cases 11/12).
+
+---
+
diff --git a/incredible_auto_dev/.claude/anti-patterns/23-prompt-argv-execve.md b/incredible_auto_dev/.claude/anti-patterns/23-prompt-argv-execve.md
new file mode 100644
index 0000000..c723698
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/23-prompt-argv-execve.md
@@ -0,0 +1,16 @@
+## 23. Prompt-sized content crossing execve as a single argv/env string
+
+**Pattern:** The interactive dispatch builder passed the full agent prompt to `jq` as one `--arg` value (argv), with a python3 fallback that env-prefixed it (`_ID_P="$prompt"`, envp); the headless backends passed it as `claude -p "<prompt>"` / `codex exec "<prompt>"` argv. Linux caps every SINGLE argv/envp string at MAX_ARG_STRLEN (32 pages = 128 KiB), independent of total ARG_MAX — past it execve fails with E2BIG (`Argument list too long`) and the child never runs. Goal-mode prompt templates inlined line-capped-but-not-byte-capped evaluator-log/assumption tails, which crossed 128 KiB around iteration 40 of a 43-iteration production session: EVERY decomposer/evaluator/summarizer dispatch from there failed until a human pump operator hand-reconstructed prompts from on-disk artifacts. The bug survived at least one refactor because nothing regression-tested oversized prompts.
+
+**Why it fails:** Three compounding mistakes. (1) The per-string cap is invisible in testing — normal prompts are tens of KB, and the failure appears only when ONE string crosses it. (2) The shell performs the `> "$req"` redirect in the forked child BEFORE the exec attempt, so the failed builder still creates a 0-byte file. (3) The builder's exit status was never checked, so the empty request was atomically PUBLISHED — the pump claimed a payload with no agent/prompt/res_path and the engine sat in the inflight wait (24 h in production config). The requeue path rebuilt the same oversized prompt and failed deterministically; the python3 fallback could never rescue the jq branch because envp shares the same per-string cap as argv.
+
+**Prevention:** Applies to any code handing agent prompts (or other unbounded content) to a child process, and to any code publishing channel artifacts.
+- Unbounded content NEVER crosses execve as one argv/env string. Route it via a file written by the shell builtin `printf` (no exec, no cap) + `jq --rawfile`, via stdin (`< file`, or `< <(printf '%s' "$var")` from a NON-exported shell variable), or a heredoc. Exporting the variable — including an `X="$big" cmd` env-prefix — re-introduces the same E2BIG via envp.
+- Validate channel artifacts BEFORE publishing: non-empty (`[[ -s f ]]`) FIRST — a broken builder that exits 0 writing nothing also defeats tool-based validation — then a JSON parse; on failure log loudly (agent + prompt size) and return WITHOUT publishing. (`lib/interactive-dispatch.sh` publish guard; self-tests 13–15.)
+- Producer side: byte-cap inlined log tails, not just line-cap (`_tail_or_placeholder`, `CHAIN_INLINE_TAIL_MAX_BYTES` default 48 KiB, marker names the on-disk file). The dispatch layer must still handle arbitrary sizes — the cap is bloat/token control, not the fix.
+- Headless: prompts past `CHAIN_PROMPT_ARGV_MAX` (default 100000 bytes) are fed on stdin (`claude -p` reads the prompt from stdin; `codex exec -` is the stdin sentinel); below the threshold argv is used exactly as before (`_invoke_with_prompt_stdin`; oversized-routing tests in test-quota-retry.sh).
+
+**Example (bad):** `jq -cn --arg p "$prompt" '{prompt:$p}' > req.json; mv req.json req.json.ready` — a 200 KB prompt means jq never execs, yet the 0-byte redirect target is still created and published.
+**Example (good):** `printf '%s' "$prompt" > "$pf"; jq -cn --rawfile p "$pf" '{prompt:$p}' > req.json 2>/dev/null; [[ -s req.json ]] && jq -e . req.json >/dev/null 2>&1 || { echo "build failed" >&2; return 2; }`
+
+**Detection:** `bash: …: Argument list too long` in engine stderr; a 0-byte `req.*.ready` in the channel dir; the pump claiming a request whose JSON has no fields. 30-second repro: `p="$(head -c 200000 /dev/zero | tr '\0' x)"; jq -cn --arg p "$p" . > /tmp/r.json` fails and leaves `/tmp/r.json` at 0 bytes.
diff --git a/incredible_auto_dev/.claude/anti-patterns/README.md b/incredible_auto_dev/.claude/anti-patterns/README.md
new file mode 100644
index 0000000..1de890c
--- /dev/null
+++ b/incredible_auto_dev/.claude/anti-patterns/README.md
@@ -0,0 +1,33 @@
+# Anti-Patterns — documented failure modes (index)
+
+One file per numbered entry, split from the former monolith (CTX-12) so a reader loads
+only what matches the situation: scan this index, open the matching `<NN>-<slug>.md`,
+nothing else. Numbering is FROZEN forever — files keep their original `## <N>. <title>`
+headings; the next new entry takes the next free number (24) as `<NN>-<slug>.md` plus a
+row here (maintenance protocol §2).
+
+| # | Entry | Applies when | Rule (one line) |
+|---|-------|--------------|-----------------|
+| 1 | [01-vague-acceptance-criteria.md](01-vague-acceptance-criteria.md) | authoring phase specs | Every DEFINITION OF DONE item must be specific and testable |
+| 2 | [02-hardcoded-stack-paths.md](02-hardcoded-stack-paths.md) | editing agent bodies/prompts | Stack commands live in project-template.md; agents reference, never inline |
+| 3 | [03-merged-developer-agent.md](03-merged-developer-agent.md) | restructuring agents | One developer handles backend+frontend, driven by `Frontend Present:` |
+| 4 | [04-ui-evolution-afterthought.md](04-ui-evolution-afterthought.md) | frontend-affecting phases | UI Evolution Audit gates QA; UI-FAIL blocks overall PASS |
+| 5 | [05-quota-exhaustion-no-retry.md](05-quota-exhaustion-no-retry.md) | dispatch/retry plumbing | Checkpoint and resume on quota exits; never restart from scratch |
+| 6 | [06-review-without-file-line.md](06-review-without-file-line.md) | writing review reports | Every finding carries file:line and a concrete fix task |
+| 7 | [07-reviewer-qa-fixing-code.md](07-reviewer-qa-fixing-code.md) | reviewer/qa behavior | Judges report; only the developer fixes |
+| 8 | [08-freeform-agent-conversation.md](08-freeform-agent-conversation.md) | inter-agent communication | Filesystem artifacts only; no agent-to-agent chat |
+| 9 | [09-missing-functional-test-plans.md](09-missing-functional-test-plans.md) | QA pipeline | Derive an explicit test plan from the spec before QA runs |
+| 10 | [10-supply-chain-attacks.md](10-supply-chain-attacks.md) | package installs | Every install goes through the security gate |
+| 11 | [11-spec-without-definition-of-done.md](11-spec-without-definition-of-done.md) | phase spec authoring | Numbered, testable DEFINITION OF DONE in every spec |
+| 12 | [12-agents-summarize-not-read.md](12-agents-summarize-not-read.md) | audit/review evidence | Verify claims from actual source code, not summaries |
+| 13 | [13-backend-without-ui-verification.md](13-backend-without-ui-verification.md) | user-facing phases | 6 UI artifacts required; invisible features fail closure |
+| 14 | [14-vague-test-steps.md](14-vague-test-steps.md) | test plan authoring | Exact URL, element, input, and expected outcome per step |
+| 15 | [15-mocked-only-external-tests.md](15-mocked-only-external-tests.md) | external integrations | At least one live integration test; mocks alone prove nothing |
+| 16 | [16-hardcoded-localhost.md](16-hardcoded-localhost.md) | service configuration | Bind addresses and URLs configurable; no localhost literals |
+| 17 | [17-long-sleep-suspend.md](17-long-sleep-suspend.md) | wait/retry code | Sleep toward an absolute epoch with polling, never one long duration |
+| 18 | [18-goal-journeys-anti-goals.md](18-goal-journeys-anti-goals.md) | goal.md authoring | Goal mode refuses to start without Must-have journeys + Anti-goals |
+| 19 | [19-timeout-swallows-ctrl-c.md](19-timeout-swallows-ctrl-c.md) | timeout-wrapped dispatch | Use `timeout --foreground` so Ctrl-C reaches the child |
+| 20 | [20-next-build-against-dev.md](20-next-build-against-dev.md) | Next.js projects | Never `next build` against a live `next dev`; separate distDir |
+| 21 | [21-shared-tmp-accumulation.md](21-shared-tmp-accumulation.md) | temp files | Per-run TMPDIR isolation via chain-tmp.sh; never raw shared /tmp |
+| 22 | [22-scanner-flags-own-output.md](22-scanner-flags-own-output.md) | scan scoping | Scan the product; exclude the pipeline's own bookkeeping paths |
+| 23 | [23-prompt-argv-execve.md](23-prompt-argv-execve.md) | passing prompts to child processes | Prompt-sized content goes via stdin or file, never argv/env |
diff --git a/incredible_auto_dev/.claude/architecture/README.md b/incredible_auto_dev/.claude/architecture/README.md
index aaac9f4..e96b821 100644
--- a/incredible_auto_dev/.claude/architecture/README.md
+++ b/incredible_auto_dev/.claude/architecture/README.md
@@ -9,9 +9,9 @@ This directory contains the framework's architecture documentation. These docs d
 | [system-overview.md](system-overview.md) | Design philosophy, component taxonomy, how components relate, mode comparison |
 | [pipeline.md](pipeline.md) | 11-step phase pipeline with data flow, retry loops, checkpoint/resume |
 | [goal-mode.md](goal-mode.md) | Goal-mode architecture: outer loop, halt logic, decomposer + evaluator, state |
-| [agents.md](agents.md) | All 19 agents: role, model tier, inputs, outputs |
+| [agents.md](agents.md) | All 20 agents: role, model tier, inputs, outputs |
 | [artifacts.md](artifacts.md) | Complete artifact map with paths, producers, and consumers (phase + goal modes) |
-| [skills-and-hooks.md](skills-and-hooks.md) | 13 skills and 5 hooks: purpose, consuming agent, trigger |
+| [skills-and-hooks.md](skills-and-hooks.md) | 16 skills and 5 hooks: purpose, consuming agent, trigger |
 | [configuration.md](configuration.md) | All config surfaces: project-template, agent-models, security policy |
 | [adoption-guide.md](adoption-guide.md) | Step-by-step guide to adopting this framework in a project (phase and goal modes) |
 
@@ -21,7 +21,7 @@ This directory contains the framework's architecture documentation. These docs d
 - **.claude/core.md** -- universal quality rules, testing requirements, security baseline.
 - **.claude/workflow.md** -- pipeline stages, retry policy, verdict formats.
 - **.claude/project-template.md** -- project-specific config (filled in per project).
-- **.claude/anti-patterns.md** -- 18 documented failure modes.
+- **.claude/anti-patterns/** -- failure-mode tree: README index + one file per numbered entry.
 - **docs/goal.md** -- project vision and success criteria (filled in per project).
 - **docs/architecture/** -- project-specific architecture docs (auto-updated per phase).
 
diff --git a/incredible_auto_dev/.claude/architecture/adoption-guide.md b/incredible_auto_dev/.claude/architecture/adoption-guide.md
index 949606e..88525fe 100644
--- a/incredible_auto_dev/.claude/architecture/adoption-guide.md
+++ b/incredible_auto_dev/.claude/architecture/adoption-guide.md
@@ -62,7 +62,7 @@ Every phase spec must have:
 - A numbered DEFINITION OF DONE checklist
 - Specific, testable acceptance criteria
 
-See `.claude/anti-patterns.md` (pattern 1) for why vague acceptance criteria cause problems.
+See `.claude/anti-patterns/01-vague-acceptance-criteria.md` for why vague acceptance criteria cause problems.
 
 ## Step 5: Run the Pipeline
 
@@ -182,12 +182,12 @@ your-project/
     core.md                          # Universal rules
     workflow.md                      # Pipeline definition
     project-template.md              # Project config (you fill this in)
-    anti-patterns.md                 # Failure modes
-    agents/                          # 14 agent definitions (12 phase + 2 goal)
-    skills/                          # 13 skills
+    anti-patterns/                   # Failure modes (README index + per-entry files)
+    agents/                          # agent definitions (rendered from agents/<name>/)
+    skills/                          # 16 skills
     hooks/                           # 5 hooks
     architecture/                    # Framework architecture docs (incl. goal-mode.md)
-  scripts/automation/                # 18 automation scripts (incl. run-goal.sh, goal-iter-lean.sh)
+  scripts/automation/                # automation scripts (incl. run-goal.sh, goal-iter-lean.sh)
     lib/                             # quota-retry.sh, common.sh, telemetry.sh
   config/                            # model-tiers.yaml, security policy
   templates/                         # 15 artifact templates
diff --git a/incredible_auto_dev/.claude/architecture/agents.md b/incredible_auto_dev/.claude/architecture/agents.md
index e16d447..1b17c4b 100644
--- a/incredible_auto_dev/.claude/architecture/agents.md
+++ b/incredible_auto_dev/.claude/architecture/agents.md
@@ -4,11 +4,10 @@ The framework defines 20 agents in `.claude/agents/` (rendered from `agents/<nam
 
 ## Model Tiers
 
-| Tier | Model | Used for |
-|------|-------|----------|
-| strong | claude-opus-5 | Judgment: goal evaluation/decomposition, skeptical audit, confirms |
-| standard | claude-sonnet-5 | Solid tasks: code review, UI analysis, test design |
-| light | claude-haiku-4-5 | Routine workflow: QA execution, git operations |
+Tier→model resolution lives in `config/model-tiers.yaml` (via `model_tier` in each
+`agents/<name>/agent.yaml`); the prose rationale table — which model, which class of
+work, why — is maintained once, in `.claude/model-orchestration.md` §1. The per-agent
+tier notes below restate the agent.yaml facts only.
 
 ## Core Pipeline Agents (7)
 
diff --git a/incredible_auto_dev/.claude/architecture/artifacts.md b/incredible_auto_dev/.claude/architecture/artifacts.md
index 4a20e85..eb2eab5 100644
--- a/incredible_auto_dev/.claude/architecture/artifacts.md
+++ b/incredible_auto_dev/.claude/architecture/artifacts.md
@@ -1,41 +1,17 @@
 # Artifacts
 
-All inter-agent communication happens through filesystem artifacts. This document maps every artifact type, its path, producer, consumers, and format.
+All inter-agent communication happens through filesystem artifacts. The runtime-routed
+artifact tables — core pipeline, UI visibility (6 per phase), and goal-mode artifacts,
+each with producers and consumers — are maintained ONCE in `.claude/workflow.md`
+(§Communication Model and §Goal Mode Pipeline): that is the copy agents read, and it
+wins on any disagreement. This document adds only what workflow.md does not carry —
+the showcase/security artifact inventory, backend-only stubs, and the goal-mode
+schemas.
 
-## Core Pipeline Artifacts
+## Showcase, Security, and Standalone Artifacts
 
 | Artifact | Path | Producer | Consumers |
 |----------|------|----------|-----------|
-| Phase spec | `docs/phases/<phase>.md` | Human | All agents |
-| Execution plan | `runs/<phase>/plan.md` | orchestrator | developer, reviewer, qa, auditor, all UI agents |
-| Test plan | `reports/qa/<phase>-test-plan.md` | qa (generate mode) | qa (validate mode), ui-test-designer |
-| Dev handoff | `docs/handoffs/<phase>-dev.md` | developer | reviewer, qa, auditor, ui-impact-analyst |
-| Frontend handoff | `docs/handoffs/<phase>-frontend.md` | developer | reviewer, qa, auditor, ui-impact-analyst |
-| Review report | `reports/reviews/<phase>-review.md` | reviewer | qa, developer (fix mode) |
-| QA report | `reports/qa/<phase>-qa.md` | qa (validate mode) | auditor, release-manager |
-| Audit report | `docs/handoffs/<phase>-audit.md` | auditor | release-manager, phase-closure-auditor |
-| Phase status | `runs/<phase>/status.json` | scripts + agents | scripts (checkpoint/resume) |
-| Phase summary | `runs/<phase>/summary.json` | finalize-phase.sh | release-manager |
-| Project goal | `docs/goal.md` | Human | orchestrator, developer, reviewer, qa |
-| Project architecture | `docs/architecture/*.md` | update-docs.sh | orchestrator, developer |
-
-## UI Visibility Artifacts (6 per phase)
-
-| Artifact | Path | Producer | Consumers |
-|----------|------|----------|-----------|
-| Implementation summary | `reports/phase-{N}-implementation-summary.md` | developer | ui-impact-analyst, phase-closure-auditor |
-| User-visible changes | `reports/phase-{N}-user-visible-changes.md` | ui-impact-analyst | ui-test-designer, ux-regression-reviewer, phase-closure-auditor |
-| UI surface map | `reports/phase-{N}-ui-surface-map.md` | ui-impact-analyst | ui-test-designer, browser-qa-agent, ux-regression-reviewer |
-| UI test plan | `reports/phase-{N}-ui-test-plan.md` | ui-test-designer | browser-qa-agent, phase-closure-auditor |
-| UI test results | `reports/phase-{N}-ui-test-results.md` | browser-qa-agent | ux-regression-reviewer, phase-closure-auditor |
-| What to click | `reports/phase-{N}-what-to-click.md` | ui-test-designer | operator (human), phase-closure-auditor |
-
-## Additional Artifacts
-
-| Artifact | Path | Producer | Consumers |
-|----------|------|----------|-----------|
-| UX regression report | `reports/phase-{N}-ux-regression.md` | ux-regression-reviewer | phase-closure-auditor |
-| Closure verdict | `reports/phase-{N}-closure-verdict.md` | phase-closure-auditor | finalize-phase.sh |
 | UI audit report | `reports/qa/<phase>-ui-audit.md` | ui-audit-phase.sh | qa (standalone) |
 | Browser evidence | `reports/qa/<phase>-evidence/*.png` | browser-qa-agent | phase-closure-auditor |
 | Iteration summary (MD) | `reports/phase-<phase>-iteration-summary.md` | iteration-summarizer | render_iteration_summary.py, human |
@@ -49,23 +25,15 @@ All inter-agent communication happens through filesystem artifacts. This documen
 | Delivered wrap (MD) | `reports/goal-session-<sid>-delivered.md` | iteration-summarizer (delivered mode, GOAL_ACHIEVED only) | render_iteration_summary.py, human |
 | Delivered wrap (HTML) | `reports/goal-session-<sid>-delivered.html` | render_iteration_summary.py (`delivered` command) | human |
 | Install decisions | `reports/security/install-decisions.jsonl` | install-security-gate.sh | human review |
-| Framework architecture | `.claude/architecture/*.md` | update-docs.sh | all agents (reference) |
 
 ## Verdict Formats
 
-All verdicts use the prefix `**Verdict:**` followed by the exact value. Scripts parse this line by machine via `verdicts.py`.
-
-| Report | Valid Verdicts |
-|--------|---------------|
-| Review | `PASS`, `PASS_WITH_NOTES`, `FAIL` |
-| QA | `PASS`, `PASS_WITH_NOTES`, `FAIL` |
-| Audit | `PASS`, `PASS_WITH_GAPS`, `FAIL` |
-| UI Evolution (in QA) | `UI-PASS`, `UI-PASS-WITH-GAPS`, `UI-FAIL` |
-| Browser QA | `PASS`, `FAIL`, `SKIPPED` |
-| Phase Closure | `CLOSURE-PASS`, `CLOSURE-FAIL` |
-| UX Regression | `UX-REGRESSION-PASS`, `UX-REGRESSION-WARN`, `UX-REGRESSION-FAIL` |
-| Iteration summary | `GOAL_ACHIEVED`, `CONTINUE`, `ESCALATE`, `REGRESSION`, `STALLED`, `PASS`, `FAIL`, `IN-PROGRESS` |
-| Demo results | `RECORDED`, `RECORDED_WITH_NOTES`, `SKIPPED`, `NOT_YET` (showcase, never blocks the pipeline) |
+Machine-parsed: every verdict is a `**Verdict:**` line with an exact value. The
+complete vocabulary lives in code — `scripts/automation/lib/verdicts.py` (one enum per
+report class) — validated at write time by `lib/artifact_schemas.py`. The runtime-routed
+prose copy of the core report classes is `.claude/workflow.md` §Verdict Formats; each
+emitting agent's body names its own enum values (enforced by `lib/lint_contracts.py`).
+Emit verdict lines EXACTLY as those sources specify.
 
 ## Backend-Only N/A Stubs
 
@@ -77,19 +45,12 @@ When `Frontend Present: no`, the pipeline writes N/A stub files for the 6 UI vis
 
 ## Goal-Mode Artifacts
 
-Goal mode adds a parallel artifact tree under `runs/goal-session-<sid>/`. Per-iteration code/test artifacts still use the existing `runs/<iter-name>/` and `reports/...<iter-name>...` paths, where the iteration name `goal-<sid>-iter-<N>` is treated as a "phase name" — so all phase-mode artifacts above are produced for goal-mode iterations too.
+Goal mode adds a parallel artifact tree under `runs/goal-session-<sid>/`. Per-iteration code/test artifacts still use the existing `runs/<iter-name>/` and `reports/...<iter-name>...` paths, where the iteration name `goal-<sid>-iter-<N>` is treated as a "phase name" — so all phase-mode artifacts are produced for goal-mode iterations too. The goal-mode artifact table and both verdict tables (evaluator + loop-level halts) live in `.claude/workflow.md` §Goal Mode Pipeline. Not listed there:
 
 | Artifact | Path | Producer | Consumers |
 |----------|------|----------|-----------|
 | Goal spec (extended) | `docs/goal.md` (with Must-have user journeys + Anti-goals sections) | Human | goal-decomposer, goal-evaluator, all phase agents |
-| Iteration spec | `docs/phases/goal-<sid>-iter-<N>.md` | goal-decomposer | run-phase.sh (full) or goal-iter-lean.sh (lean), then all downstream agents |
-| Session state | `runs/goal-session-<sid>/session.json` | run-goal.sh | run-goal.sh (resume, halt arithmetic) |
-| Journey history | `runs/goal-session-<sid>/state/journey-history.json` | goal-evaluator | goal-decomposer (next-step planning), goal-evaluator (regression detection), run-goal.sh (stall detection via hash) |
-| Evaluator log | `runs/goal-session-<sid>/state/evaluator-log.md` | goal-evaluator (append-only) | goal-decomposer (read last 3 entries) |
-| Iter eval | `runs/goal-session-<sid>/iter-<N>/eval.md` | goal-evaluator | run-goal.sh (verdict parsing) |
-| Telemetry | `runs/goal-session-<sid>/telemetry.jsonl` | run-goal.sh + goal-iter-lean.sh + lib/telemetry.sh | analysis tools (jq), future self-evolution loop (deferred) |
 | History hashes | `runs/goal-session-<sid>/.history-hashes` | run-goal.sh | run-goal.sh (stall detection) |
-| Session summary | `runs/goal-session-<sid>/summary.md` | run-goal.sh (on halt) | Human |
 
 ### journey-history.json schema
 
@@ -125,13 +86,6 @@ See [`docs/goal-mode-telemetry.md`](../../docs/goal-mode-telemetry.md). Each lin
 
 ### Goal-mode verdicts
 
-The goal-evaluator emits one of:
-| Verdict | Meaning |
-|---|---|
-| `GOAL_ACHIEVED` | All Must-have journeys pass, no critical anti-goal violations. Loop halts with success. |
-| `CONTINUE` | Progress made or actionable next work identified. Loop continues. |
-| `ESCALATE` | Lean iteration uncovered ambiguity; next iteration MUST run as full. |
-| `REGRESSION` | A previously-passing journey now fails OR a critical anti-goal was violated. Halts for human review. |
-| `STALLED` | Evaluator-side judgment that no productive next work is identifiable. Halts. |
-
-The outer loop also emits halt verdicts of its own (`BUDGET_EXHAUSTED`, `STALLED` via hash detection, `REGRESSION_HALT`, `ABORTED`) into `session.json.status`.
+Evaluator verdicts (`GOAL_ACHIEVED` / `CONTINUE` / `ESCALATE` / `REGRESSION` /
+`STALLED`) and the loop-level halt verdicts are specified in `.claude/workflow.md`
+§Goal Mode Pipeline (vocabulary: `lib/verdicts.py` `GoalEvalVerdict`).
diff --git a/incredible_auto_dev/.claude/architecture/configuration.md b/incredible_auto_dev/.claude/architecture/configuration.md
index 8a3e188..5a278e6 100644
--- a/incredible_auto_dev/.claude/architecture/configuration.md
+++ b/incredible_auto_dev/.claude/architecture/configuration.md
@@ -25,7 +25,7 @@ Agents reference this file for stack-specific commands (test runner, package man
 
 ## config/model-tiers.yaml (+ agents/*/agent.yaml `model_tier`)
 
-Maps each of the 19 agents to a model tier (12 phase-mode + 2 goal-mode).
+Maps each of the 20 agents to a model tier (12 phase-pipeline + 4 goal-mode + 4 showcase/maintenance).
 
 ```yaml
 tiers:
diff --git a/incredible_auto_dev/.claude/architecture/goal-mode.md b/incredible_auto_dev/.claude/architecture/goal-mode.md
index aa269a2..1279697 100644
--- a/incredible_auto_dev/.claude/architecture/goal-mode.md
+++ b/incredible_auto_dev/.claude/architecture/goal-mode.md
@@ -85,7 +85,7 @@ After the evaluator runs, the verdict directly drives the loop:
 
 **Quota exhaustion is NOT a halt.** The wrapped `claude_with_quota_retry` library transparently sleeps until the quota resets, then resumes the same agent invocation. Telemetry records the quota pause for observability.
 
-**Per-iteration tmp hygiene.** The engine owns a per-run tmp dir (`lib/chain-tmp.sh`, exported as `TMPDIR`): session-scoped at startup, then rotated to `$CHAIN_TMP_ROOT/iad.goal-<sid>-iter-<N>.<pid>` (root default `~/.cache/iad`, not the quota'd tmpfs `/tmp`; ≤62-char TMPDIR, long ids hash-shortened) at each iteration boundary — immediately after `_join_showcase_tail`, because the previous iteration's async showcase tail keeps writing demo logs until that join (never clean right after the evaluator). The `[run-goal] Tmp cleanup: cleared …` log line marks the step. Both dispatch depths adopt the engine's dir (owner-guarded), and the engine's EXIT trap removes the final dir on any halt. A startup janitor reaps strays from crashed sessions across the root and legacy `/tmp`. See `.claude/anti-patterns.md` #21.
+**Per-iteration tmp hygiene.** The engine owns a per-run tmp dir (`lib/chain-tmp.sh`, exported as `TMPDIR`): session-scoped at startup, then rotated to `$CHAIN_TMP_ROOT/iad.goal-<sid>-iter-<N>.<pid>` (root default `~/.cache/iad`, not the quota'd tmpfs `/tmp`; ≤62-char TMPDIR, long ids hash-shortened) at each iteration boundary — immediately after `_join_showcase_tail`, because the previous iteration's async showcase tail keeps writing demo logs until that join (never clean right after the evaluator). The `[run-goal] Tmp cleanup: cleared …` log line marks the step. Both dispatch depths adopt the engine's dir (owner-guarded), and the engine's EXIT trap removes the final dir on any halt. A startup janitor reaps strays from crashed sessions across the root and legacy `/tmp`. See `.claude/anti-patterns/21-shared-tmp-accumulation.md`.
 
 **Disk-space guard (`AWAITING_DISK`).** `chain_tmp_disk_guard` runs once at preflight (next to the GitHub preflight) and again at the top of every iteration, with the other halt checks — never mid-iteration. Under pressure (root fs below `CHAIN_TMP_MIN_FREE_MB`, or a `/tmp` write-probe hitting ENOSPC/EDQUOT — statvfs cannot see tmpfs user quotas) it runs the aggressive janitor: dead-pid run dirs at any age, stale `bench-*`/`judgment-*`/`shared/` entries. Only when the ROOT filesystem is still below `CHAIN_TMP_HARD_MIN_FREE_MB` after sweeping does the engine pause: `session.json.status = AWAITING_DISK`, exit 0, resumable exactly like the auth pause (fix: `scripts/automation/tmp-doctor.sh --aggressive`, then `--resume`). /tmp pressure alone is warn-only — agent-side writes land in `~/.cache/iad/shared` via the user-global settings `env` TMPDIR (verified: settings-env overrides even a parent-exported TMPDIR for dispatched agents, so their reaper is the 72h `shared/` sweep, not per-iteration rotation).
 
@@ -196,4 +196,4 @@ Telemetry capture is a foundation for a future "self-evolution" loop where this
 - [`docs/goal-mode-telemetry.md`](../../docs/goal-mode-telemetry.md) — telemetry schema
 - [`agents.md`](agents.md) — full agent inventory
 - [`pipeline.md`](pipeline.md) — phase-mode pipeline (the "full" inner pipeline of goal mode)
-- [`.claude/anti-patterns.md`](../anti-patterns.md) — anti-pattern #18 covers goal-mode authoring
+- [`.claude/anti-patterns/18-goal-journeys-anti-goals.md`](../anti-patterns/18-goal-journeys-anti-goals.md) — the goal-mode authoring failure mode
diff --git a/incredible_auto_dev/.claude/architecture/pipeline.md b/incredible_auto_dev/.claude/architecture/pipeline.md
index 77e7666..ea4d7b3 100644
--- a/incredible_auto_dev/.claude/architecture/pipeline.md
+++ b/incredible_auto_dev/.claude/architecture/pipeline.md
@@ -54,7 +54,7 @@ Phase spec (docs/phases/<phase>.md)
     |
     v
 [Step 9] auditor --> audit-report
-         (loop: max 2 attempts on FAIL)
+         (loop: max 3 attempts on FAIL; retry caps authoritative in workflow.md §Retry Policy)
     |
     v
 [Step 10] phase-closure-auditor --> closure-verdict
@@ -141,4 +141,4 @@ Key contracts:
 
 Goal mode: full iterations dispatch through `run-phase.sh --no-finalize`, so the fanout runs there too. Lean iterations (`goal-iter-lean.sh`) have no parallelisable surface — dev → review → browser-qa → demo is strictly sequential — and run as today.
 
-**Per-run tmp isolation** (`lib/chain-tmp.sh`): `run-phase.sh` initializes `$CHAIN_TMP_ROOT/iad.<phase>.<pid>` (root default `~/.cache/iad` — big un-quota'd disk, NOT the quota'd tmpfs `/tmp`; the whole TMPDIR stays ≤62 chars for Chromium's unix-socket limit, long ids hash-shortened with the raw id in `.chain-run-id`) and exports it as `TMPDIR`, so pytest basetemps, chromium profiles, dispatch temp logs, and `_qa_log_path` service logs all land in one per-run dir (adopted, not re-created, when nested under run-goal.sh — and only while the recorded owner pid is alive). The un-numbered cleanup block after Step 10.5 announces the dir; the actual removal happens in an EXIT trap that fires on EVERY exit path (success, `fail()`, quota 75, transport 70, signal aborts) and, on non-success, first archives bounded service-log tails to `runs/<phase>/service-logs/`. A janitor at startup reaps strays from crashed runs across the root AND legacy `/tmp` (age- and pid-liveness-gated; also `bench-*`/`judgment-*` scratch and the `shared/` interactive-TMPDIR dir), and `chain_tmp_disk_guard` sweeps aggressively under disk pressure (warn-only here; the goal engine owns the pause). See `.claude/anti-patterns.md` #21 and `scripts/automation/tmp-doctor.sh`.
+**Per-run tmp isolation** (`lib/chain-tmp.sh`): `run-phase.sh` initializes `$CHAIN_TMP_ROOT/iad.<phase>.<pid>` (root default `~/.cache/iad` — big un-quota'd disk, NOT the quota'd tmpfs `/tmp`; the whole TMPDIR stays ≤62 chars for Chromium's unix-socket limit, long ids hash-shortened with the raw id in `.chain-run-id`) and exports it as `TMPDIR`, so pytest basetemps, chromium profiles, dispatch temp logs, and `_qa_log_path` service logs all land in one per-run dir (adopted, not re-created, when nested under run-goal.sh — and only while the recorded owner pid is alive). The un-numbered cleanup block after Step 10.5 announces the dir; the actual removal happens in an EXIT trap that fires on EVERY exit path (success, `fail()`, quota 75, transport 70, signal aborts) and, on non-success, first archives bounded service-log tails to `runs/<phase>/service-logs/`. A janitor at startup reaps strays from crashed runs across the root AND legacy `/tmp` (age- and pid-liveness-gated; also `bench-*`/`judgment-*` scratch and the `shared/` interactive-TMPDIR dir), and `chain_tmp_disk_guard` sweeps aggressively under disk pressure (warn-only here; the goal engine owns the pause). See `.claude/anti-patterns/21-shared-tmp-accumulation.md` and `scripts/automation/tmp-doctor.sh`.
diff --git a/incredible_auto_dev/.claude/architecture/skills-and-hooks.md b/incredible_auto_dev/.claude/architecture/skills-and-hooks.md
index 4fc2040..ad3060a 100644
--- a/incredible_auto_dev/.claude/architecture/skills-and-hooks.md
+++ b/incredible_auto_dev/.claude/architecture/skills-and-hooks.md
@@ -1,6 +1,6 @@
 # Skills and Hooks
 
-## Skills (9 total, in `.claude/skills/`)
+## Skills (in `.claude/skills/`)
 
 Skills are reusable instruction files that agents read during their workflow. They are not agents -- they are methodologies.
 
@@ -9,6 +9,7 @@ Skills are reusable instruction files that agents read during their workflow. Th
 | Diff-to-UI Impact | `diff-to-ui-impact.md` | ui-impact-analyst | Classify file changes by UI impact type (frontend-direct, backend-api, backend-internal, config, full-stack) |
 | UI Workflow Inference | `ui-workflow-inference.md` | ui-impact-analyst | Infer user journeys from changed routes, components, and entry points |
 | Visible Change Summarizer | `visible-change-summarizer.md` | ui-impact-analyst | Write plain-language user-facing change summaries for operators |
+| Plain Language | `plain-language.md` | iteration-summarizer, demo-narrator, readme-maintainer | Shared plain-English writing standard for owner-facing prose: short sentences, IDs with friendly names, the canonical status/verdict word table (single source: `lib/plain-language.sh`) |
 | Manual UI Test Plan Generator | `manual-ui-test-plan-generator.md` | ui-test-designer | Create human-executable test plans with exact steps and expected outcomes |
 | What-to-Click Writer | `what-to-click-writer.md` | ui-test-designer | Write fast operator verification guides (5-minute check) |
 | Browser Workflow Executor | `browser-workflow-executor.md` | browser-qa-agent | Execute browser flows via Chrome MCP (navigate, click, type, screenshot) |
diff --git a/incredible_auto_dev/.claude/architecture/system-overview.md b/incredible_auto_dev/.claude/architecture/system-overview.md
index f899187..f116821 100644
--- a/incredible_auto_dev/.claude/architecture/system-overview.md
+++ b/incredible_auto_dev/.claude/architecture/system-overview.md
@@ -28,9 +28,9 @@ The framework consists of 6 component types:
 
 Markdown files that define each agent's role, inputs, outputs, and rules. Agents are invoked by automation scripts. Each agent has a model tier assignment (strong/standard/light) — `model_tier` in `agents/<name>/agent.yaml`, resolved via `config/model-tiers.yaml`.
 
-Twelve agents serve the phase pipeline (orchestrator, developer, reviewer, qa, auditor, release-manager, product-manager, ui-impact-analyst, ui-test-designer, browser-qa-agent, ux-regression-reviewer, phase-closure-auditor). Two agents are specific to goal mode (goal-decomposer, goal-evaluator). Goal mode reuses all twelve phase agents unchanged.
+Twelve agents serve the phase pipeline (orchestrator, developer, reviewer, qa, auditor, release-manager, product-manager, ui-impact-analyst, ui-test-designer, browser-qa-agent, ux-regression-reviewer, phase-closure-auditor). Four are specific to goal mode (goal-decomposer, goal-evaluator, coherence-auditor, goal-proposer) and four are showcase/maintenance agents (iteration-summarizer, demo-narrator, readme-maintainer, retro-analyst). Goal mode reuses the twelve phase agents unchanged.
 
-### 2. Skills (9 total, in `.claude/skills/`)
+### 2. Skills (in `.claude/skills/`)
 
 Reusable instruction files that agents read during their workflow. Skills are not agents -- they are methodologies that agents consume. For example, the `diff-to-ui-impact` skill teaches the ui-impact-analyst how to classify file changes.
 
@@ -65,11 +65,11 @@ CLAUDE.md (constitution)
     +-- .claude/core.md (universal rules)
     +-- .claude/workflow.md (pipeline definition)
     +-- .claude/project-template.md (project config)
-    +-- .claude/anti-patterns.md (failure modes)
+    +-- .claude/anti-patterns/ (failure modes: index + per-entry files)
     |
     +-- .claude/agents/*.md (12 agent definitions)
     |       |
-    |       +-- read .claude/skills/*.md (13 skills)
+    |       +-- read .claude/skills/*.md (16 skills)
     |
     +-- .claude/hooks/*.sh (5 hooks, triggered by Claude Code)
     |
diff --git a/incredible_auto_dev/.claude/commands/goal-status.md b/incredible_auto_dev/.claude/commands/goal-status.md
index f318de0..ebcfada 100644
--- a/incredible_auto_dev/.claude/commands/goal-status.md
+++ b/incredible_auto_dev/.claude/commands/goal-status.md
@@ -27,3 +27,7 @@ the engine, dispatch agents, or write anything.
    the opt-in `--intent-checkpoint` "is this the product you wanted?" pause —
    resuming acknowledges it), **orphaned** (dead engine PID — `/goal-resume`),
    or **finished** (and the final verdict).
+7. **Plain words first:** lead the summary with the status translated into a
+   plain sentence (the wording table lives in `docs/READING-REPORTS.md`), with
+   the raw code in parentheses — e.g. "The chain is paused and waiting for your
+   blueprint review (`AWAITING_BLUEPRINT_APPROVAL`)." Same for the last verdict.
diff --git a/incredible_auto_dev/.claude/core.md b/incredible_auto_dev/.claude/core.md
index 83c7381..7e4eed2 100644
--- a/incredible_auto_dev/.claude/core.md
+++ b/incredible_auto_dev/.claude/core.md
@@ -69,7 +69,7 @@ On `No space left on device` / `Disk quota exceeded`: run
 `bash scripts/automation/tmp-doctor.sh --aggressive`, retry the failed command
 ONCE, and continue. Never `rm` arbitrary `/tmp` files (concurrent sessions own
 some of them) and never halt to ask the user about disk space — the doctor
-only removes temp dirs proven dead or stale (`.claude/anti-patterns.md` #21).
+only removes temp dirs proven dead or stale (`.claude/anti-patterns/21-shared-tmp-accumulation.md`).
 
 ---
 
@@ -117,7 +117,7 @@ When a phase introduces or modifies code that calls external systems (scrapers,
 - [ ] Known failures (bot detection, geo-blocking, auth requirements) are documented in the dev handoff as "Known Issues" — not silently passed over
 - [ ] The dev handoff explicitly states whether live testing was successful or not
 
-See anti-patterns #15 and #16 for detailed failure modes and prevention strategies.
+See `.claude/anti-patterns/15-mocked-only-external-tests.md` and `16-hardcoded-localhost.md` for detailed failure modes and prevention strategies.
 
 ---
 
diff --git a/incredible_auto_dev/.claude/hooks/post-edit-lint.sh b/incredible_auto_dev/.claude/hooks/post-edit-lint.sh
index 2081eb8..90f3b6d 100644
--- a/incredible_auto_dev/.claude/hooks/post-edit-lint.sh
+++ b/incredible_auto_dev/.claude/hooks/post-edit-lint.sh
@@ -1,6 +1,23 @@
 #!/usr/bin/env bash
 # Post-edit hook: run lightweight syntax validation on edited source files
-FILE="$1"
+#
+# Two input modes (SEC-7 pattern, mirrors guard-dangerous-commands.sh):
+#   argv mode  — file path as $1 (run-evals, test harness, Codex).
+#   stdin mode — the Claude Code PostToolUse protocol: JSON on stdin
+#     (.tool_input.file_path; $CLAUDE_TOOL_INPUT_FILE_PATH never existed).
+# Advisory only: warnings to stderr, always exit 0.
+FILE="${1:-}"
+if [[ -z "$FILE" && ! -t 0 ]]; then
+  _payload=$(cat 2>/dev/null || true)
+  if [[ -n "$_payload" ]]; then
+    if command -v jq >/dev/null 2>&1; then
+      FILE=$(printf '%s' "$_payload" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null) || FILE=""
+    else
+      FILE=$(printf '%s' "$_payload" | python3 -c 'import json,sys; ti=json.load(sys.stdin).get("tool_input",{}); print(ti.get("file_path") or ti.get("path") or "")' 2>/dev/null) || FILE=""
+    fi
+  fi
+fi
+[[ -z "$FILE" ]] && exit 0
 
 if [[ "$FILE" == *.py ]]; then
   if command -v python3 &>/dev/null; then
diff --git a/incredible_auto_dev/.claude/hooks/post-write-artifact-quality.sh b/incredible_auto_dev/.claude/hooks/post-write-artifact-quality.sh
index 57aaf7a..c292634 100755
--- a/incredible_auto_dev/.claude/hooks/post-write-artifact-quality.sh
+++ b/incredible_auto_dev/.claude/hooks/post-write-artifact-quality.sh
@@ -10,6 +10,20 @@ set -e
 
 FILE_PATH="${1:-}"
 
+# Claude Code PostToolUse passes JSON on stdin (.tool_input.file_path);
+# $CLAUDE_TOOL_INPUT_FILE_PATH never existed. argv ($1) remains the
+# test-harness / Codex path (SEC-7 pattern, mirrors guard-dangerous-commands.sh).
+if [[ -z "$FILE_PATH" && ! -t 0 ]]; then
+  _payload=$(cat 2>/dev/null || true)
+  if [[ -n "$_payload" ]]; then
+    if command -v jq >/dev/null 2>&1; then
+      FILE_PATH=$(printf '%s' "$_payload" | jq -r '.tool_input.file_path // .tool_input.path // empty' 2>/dev/null) || FILE_PATH=""
+    else
+      FILE_PATH=$(printf '%s' "$_payload" | python3 -c 'import json,sys; ti=json.load(sys.stdin).get("tool_input",{}); print(ti.get("file_path") or ti.get("path") or "")' 2>/dev/null) || FILE_PATH=""
+    fi
+  fi
+fi
+
 if [[ -z "$FILE_PATH" ]]; then exit 0; fi
 if [[ ! -f "$FILE_PATH" ]]; then exit 0; fi
 
diff --git a/incredible_auto_dev/.claude/letter-to-future-sessions.md b/incredible_auto_dev/.claude/letter-to-future-sessions.md
index de29b24..f7d3bb8 100644
--- a/incredible_auto_dev/.claude/letter-to-future-sessions.md
+++ b/incredible_auto_dev/.claude/letter-to-future-sessions.md
@@ -51,9 +51,11 @@ pain into its §16 staging section.
   (`claude -p --model <id> 'reply OK'`), flip the tier, resync, update
   `.claude/model-orchestration.md`'s table in the same commit. Never re-pin a per-agent
   `model_override` except as a commented temporary exception — the evals fail on it.
-- **Append-only files grow until they poison prompts.** `lessons.md`, `anti-patterns.md`,
-  goal.md journeys. The dispatch wrappers pre-trim/slice the big ones, but condensation
-  (maintenance protocol §4) still has to happen — a 500-line lessons file is a smell.
+- **Append-only files grow until they poison prompts.** `lessons.md`, the
+  anti-patterns index, goal.md journeys. The dispatch wrappers pre-trim/slice the big
+  ones, but condensation (maintenance protocol §4) still has to happen — a 500-line
+  lessons file is a smell. (The anti-patterns monolith itself was split into
+  `.claude/anti-patterns/` per-entry files for this reason.)
 - **Skills edited without version bumps.** The rendered agent frontmatter carries
   `version:`; bump it with every body/skill change so drift between what an agent file says
   and what a long-running session loaded is diagnosable.
diff --git a/incredible_auto_dev/.claude/maintenance-protocol.md b/incredible_auto_dev/.claude/maintenance-protocol.md
index a215573..fbf9491 100644
--- a/incredible_auto_dev/.claude/maintenance-protocol.md
+++ b/incredible_auto_dev/.claude/maintenance-protocol.md
@@ -28,9 +28,11 @@ state files. When this protocol and momentum conflict, the protocol wins.
 
 - **Goal-session lessons** (product/project-specific): the evaluator appends to
   `runs/goal-session-<sid>/state/lessons.md` per its format. Signal only — no routine entries.
-- **Framework lessons** (pipeline/tooling pitfalls that transcend one project): append a
-  numbered entry to `.claude/anti-patterns.md` following its existing format (symptom → root
-  cause → rule). One entry per distinct failure mode; cite the session/iteration where it bit.
+- **Framework lessons** (pipeline/tooling pitfalls that transcend one project): create the
+  next-numbered file under `.claude/anti-patterns/` (`<NN>-<slug>.md` — numbering is frozen,
+  take one past the highest) following the existing format (symptom → root cause → rule),
+  AND add its row to the `README.md` index there (the index↔entries eval enforces the pair).
+  One entry per distinct failure mode; cite the session/iteration where it bit.
 - Format discipline: every lesson states (a) the trigger condition ("Applies to:"), (b) the
   concrete mistake, (c) the checkable rule that prevents it. A lesson without a checkable
   rule is a war story — rewrite it until it's a rule.
@@ -57,7 +59,7 @@ sync is a no-op when the mirrors already exist, so:
 ## 4. Condensation rule (growth control)
 
 When any append-only knowledge file exceeds **~200 lines** (`lessons.md`,
-`.claude/anti-patterns.md`, `letter-to-future-sessions.md` handoff section):
+`letter-to-future-sessions.md` handoff section):
 1. Condense duplicate/superseded entries into their general rule (keep the rule, drop the
    retelling); move historical examples to `<file>.archive.md` beside the original.
 2. Do it in a dedicated commit touching nothing else, message `chore(<file>): condense`.
@@ -69,10 +71,10 @@ When any append-only knowledge file exceeds **~200 lines** (`lessons.md`,
    `**AGENT RULE …:**`) stay in place, no LLM involved. The goal engine runs it warn-only
    at session start for session state files (`lessons.md`, `assumptions.md`) over 200
    lines (knob `CHAIN_AUTO_CONDENSE`, default true). It structurally REFUSES paths under
-   `.claude/` unless `--human` is passed — so `.claude/anti-patterns.md` is condensed
-   ONLY by a human running
-   `bash scripts/automation/lib/condense.sh --human .claude/anti-patterns.md`
-   in its own dedicated commit per rule 2; it also refuses rule 3's files outright.
+   `.claude/` unless `--human` is passed; it also refuses rule 3's files outright.
+   (The anti-patterns monolith this clause used to govern was split into the per-entry
+   tree `.claude/anti-patterns/` — entries stay small, so condensation no longer
+   applies there.)
 
 ## 5. Cache stability
 
@@ -96,4 +98,4 @@ The full ordered checklist — spend gates, per-step evidence, rollback — is `
 2. `./scripts/automation/run-evals.sh` must be green before commit.
 3. If the change alters an artifact format (verdict line, report path, JSON schema): grep for
    every reader of that artifact and update them in the SAME commit (see
-   `.claude/anti-patterns.md` — writer/reader drift is a documented failure class).
+   `.claude/anti-patterns/` — writer/reader drift is a documented failure class).
diff --git a/incredible_auto_dev/.claude/settings.json b/incredible_auto_dev/.claude/settings.json
index d09eb58..6b80649 100644
--- a/incredible_auto_dev/.claude/settings.json
+++ b/incredible_auto_dev/.claude/settings.json
@@ -370,7 +370,7 @@
         "hooks": [
           {
             "type": "command",
-            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/post-edit-lint.sh\" \"$CLAUDE_TOOL_INPUT_FILE_PATH\" 2>/dev/null || true"
+            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/post-edit-lint.sh\" 2>/dev/null || true"
           }
         ]
       },
@@ -379,7 +379,7 @@
         "hooks": [
           {
             "type": "command",
-            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/post-write-artifact-quality.sh\" \"$CLAUDE_TOOL_INPUT_FILE_PATH\" 2>/dev/null || true"
+            "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/post-write-artifact-quality.sh\" 2>/dev/null || true"
           }
         ]
       }
diff --git a/incredible_auto_dev/.claude/skills/goal-authoring.md b/incredible_auto_dev/.claude/skills/goal-authoring.md
index 29af29e..6c93c13 100644
--- a/incredible_auto_dev/.claude/skills/goal-authoring.md
+++ b/incredible_auto_dev/.claude/skills/goal-authoring.md
@@ -4,7 +4,7 @@ Used by `/goal-init` (interview → author) and, once it ships, by `/goal-lint`
 reuse). `docs/goal.md` is the product constitution: the goal-evaluator treats its
 Must-have journeys as objective ground truth and its Anti-goals as veto rules, so its
 quality decides every downstream iteration. Vague journeys are the documented #1
-failure mode (`.claude/anti-patterns.md` #1, #18).
+failure mode (`.claude/anti-patterns/01-vague-acceptance-criteria.md`, `18-goal-journeys-anti-goals.md`).
 
 ## Interview ground rules
 
diff --git a/incredible_auto_dev/.claude/skills/plain-language.md b/incredible_auto_dev/.claude/skills/plain-language.md
new file mode 100644
index 0000000..44f749c
--- /dev/null
+++ b/incredible_auto_dev/.claude/skills/plain-language.md
@@ -0,0 +1,72 @@
+# Skill: Plain Language
+
+How to write the prose a product owner reads. This is the shared writing standard
+for owner-facing sections (plain-words blocks, stories, narrations, README text,
+recommendations). It does not change any machine-parsed format.
+
+## Who you are writing for
+
+- The product owner. Not a developer.
+- Not a native English reader. Dense English costs them real effort.
+- They have two questions: "is my product OK?" and "what should I do next?"
+- They do not know the pipeline's internal names, and they should not need to.
+
+## Hard rules
+
+1. **Short sentences.** One idea per sentence. Prefer under ~20 words. Split long
+   sentences instead of chaining clauses with dashes and parentheses.
+2. **Everyday words.** "stopped" not "halted"; "broken" not "regressed" (say
+   "worked before, broken now"); "check" not "audit" — unless the code word itself
+   is the subject, then explain it once.
+3. **No bare internal names in plain sections.** No agent names, no file paths, no
+   environment variables, no ticket codes (REL-14, EVO-1, §16). If one must
+   appear, say in words what it is: "the roadmap's staging list (§16), which a
+   human reviews".
+4. **Every ID carries its friendly name.** Write `J-04 "Sign in with email"`,
+   never a bare ID list. Same for UT-nn tests: say what the test checks.
+5. **Describe what the user sees, not the code.** "The login page rejects a
+   correct password", not a function, class, endpoint, or stack trace.
+6. **End with an action.** Say what happens next, or what the owner should do,
+   in one sentence a non-programmer could act on.
+
+## Status words (single source)
+
+The canonical plain sentences for every session status and evaluator verdict live
+in `scripts/automation/lib/plain-language.sh`, and the owner-facing glossary is
+`docs/READING-REPORTS.md`. Reuse those words; do not invent new translations.
+Quick table for the most common codes:
+
+| Code | Plain words |
+|---|---|
+| CONTINUE | normal progress — the chain builds the next piece by itself |
+| ESCALATE | something tricky came up; the next round is slower and more careful |
+| REGRESSION | something that worked before is broken now |
+| STALLED | the chain cannot make progress alone and is asking for help |
+| GOAL_ACHIEVED | every must-have journey works; the session finishes |
+| passing / failing / regressed | working / broken / worked before, broken now |
+
+## Three examples
+
+- Bad: "Added POST /api/v1/items endpoint with SQLAlchemy persistence."
+  Good: "You can now create new items, and they are saved."
+- Bad: "J-02, J-05 remain failing; BQA lane SKIPPED-INFRA."
+  Good: "Two journeys are not working yet: J-02 \"Mark an item done\" and J-05
+  \"Filter the list\". The browser test could not run this round, so J-05 was
+  not re-checked."
+- Bad: "Iter-4 verdict demoted per gate; see eval.md."
+  Good: "A safety rule overrode the evaluator's claim this round — the stricter
+  answer wins. The evaluation file explains which rule fired."
+
+## Never simplify these
+
+Machine-parsed surfaces must stay byte-identical. Plain language is added NEXT TO
+them, never instead of them:
+
+- Verdict lines (the bold `Verdict:` marker lines scripts grep) and their
+  ALL-CAPS values.
+- Required section headings (H2 names like `In plain words`), the three
+  `What you can do now / What changed this time / What's next` labels, and any
+  field label a template marks as required.
+- JSON files, keys, and schemas; artifact file names and paths; exit codes.
+- Evidence references: keep exact file paths and screenshot names in evidence
+  fields — precision there is the point.
diff --git a/incredible_auto_dev/.claude/workflow.md b/incredible_auto_dev/.claude/workflow.md
index f223303..429e5ed 100644
--- a/incredible_auto_dev/.claude/workflow.md
+++ b/incredible_auto_dev/.claude/workflow.md
@@ -14,7 +14,7 @@ Plan → Test Plan → Dev+Review loop → QA loop → Audit loop → Finalize
 
 | Stage | Script | Agent | Output |
 |-------|--------|-------|--------|
-| 1. Plan | `run-phase.sh` (internal) | orchestrator | `runs/<phase>/plan.md` (reads `docs/goal.md` + `docs/architecture/` + `.claude/architecture/` + prior handoffs first) |
+| 1. Plan | `run-phase.sh` (internal) | orchestrator | `runs/<phase>/plan.md` (reads `docs/goal.md` + prior handoffs + `docs/architecture/` if present — created by update-docs.sh after the first finalized phase) |
 | 2. Test Plan | `generate-test-plan.sh` | qa (mode: generate) | `reports/qa/<phase>-test-plan.md` — dispatch skipped (loudly logged) when the spec already lists its own tests (`## Test`-titled section or ≥3 `TC-` lines) and `CHAIN_SKIP_TESTPLAN_IF_PRESENT=true` (default `false`; TOKEN-3) |
 | 3. Dev + Review | `dev-phase.sh` + `review-phase.sh` | developer, reviewer | `docs/handoffs/<phase>-dev.md`, `reports/phase-{N}-implementation-summary.md` |
 | 4. UI Impact Analysis | `ui-impact-phase.sh` | ui-impact-analyst | `reports/phase-{N}-user-visible-changes.md`, `reports/phase-{N}-ui-surface-map.md` |
@@ -66,8 +66,8 @@ Agents ONLY communicate through filesystem artifacts. No free-form messages betw
 | UX regression report | `reports/phase-{N}-ux-regression.md` | ux-regression-reviewer | phase-closure-auditor |
 | Closure verdict | `reports/phase-{N}-closure-verdict.md` | phase-closure-auditor | finalize-phase.sh |
 | Project goal | `docs/goal.md` | Human | orchestrator, developer, reviewer, qa |
-| Project architecture | `docs/architecture/*.md` | update-docs.sh | orchestrator, developer |
-| Framework architecture | `.claude/architecture/*.md` | update-docs.sh | All agents (reference) |
+| Project architecture | `docs/architecture/*.md` (if present; created after the first finalized phase — absence is normal early on) | update-docs.sh | orchestrator, developer |
+| Framework architecture | `.claude/architecture/*.md` | update-docs.sh | Framework maintainers (reference) |
 
 ---
 
@@ -237,13 +237,12 @@ The `Frontend Present:` line is machine-read by `qa-phase.sh` to decide whether
 
 ## Model Tier Rationale
 
-| Tier | Model | Used for |
-|------|-------|----------|
-| strong | claude-opus-5 | Judgment: goal evaluation/decomposition, skeptical audit, confirms |
-| standard | claude-sonnet-5 | Solid tasks: code review, test plan generation |
-| light | claude-haiku-4-5 | Routine workflow: QA execution, git/GitHub operations |
-
-Model assignments: each agent picks a tier (`model_tier`) in `agents/<name>/agent.yaml`; the tier resolves to a concrete model in `config/model-tiers.yaml`. Edit those, then re-render with `python3 scripts/automation/sync-cli-assets.py --cli claude` and commit the regenerated `.claude/agents/*.md`.
+Each agent picks a tier (`model_tier`) in `agents/<name>/agent.yaml`; the tier resolves
+to a concrete model in `config/model-tiers.yaml` — the ONLY place model ids live. The
+prose tier table (which model, which class of work, why) is maintained once, in
+`.claude/model-orchestration.md` §1, kept current per maintenance-protocol §6. After
+editing tiers: re-render with `python3 scripts/automation/sync-cli-assets.py --cli claude`
+and commit the regenerated `.claude/agents/*.md`.
 
 ---
 
diff --git a/incredible_auto_dev/CLAUDE.md b/incredible_auto_dev/CLAUDE.md
index 80a83f2..0153396 100644
--- a/incredible_auto_dev/CLAUDE.md
+++ b/incredible_auto_dev/CLAUDE.md
@@ -24,15 +24,15 @@ Both modes run on **Claude Code** (default) or **OpenAI Codex CLI** (`--cli code
 | File | Contents | Who reads it |
 |------|----------|--------------|
 | `.claude/core.md` | Universal quality rules, testing checklist, security baseline, token policy | **All agents** |
-| `.claude/workflow.md` | Pipeline stages, retry policy, artifact locations, verdict formats, UI evolution policy | **All agents** |
+| `.claude/workflow.md` | Pipeline stages, retry policy, artifact locations, verdict formats, UI evolution policy | goal-decomposer, reviewer; on-demand pipeline reference for any other agent |
 | `.claude/project-template.md` | Project stack, test/run commands, architecture principles | **All agents** |
 | `.claude/model-orchestration.md` | Model×effort table, delegation package, reporting contract, escalation ladder, non-self-verification rules | Orchestrator, pump, anyone dispatching agents |
-| `.claude/judgment-rubrics.md` | Executable judgment criteria (escalation, definition-of-done, stop-and-ask, wrong-direction signals, evidence floors, honesty) with ✚/✖ examples | Judges (evaluator, auditor, decomposer, reviewer) and anyone making verdict-class calls |
-| `.claude/delegation-templates.md` | Fill-in dispatch templates (search/implement/refactor/research/review) | Anyone dispatching agents |
+| `.claude/judgment-rubrics.md` | Executable judgment criteria (escalation, definition-of-done, stop-and-ask, wrong-direction signals, evidence floors, honesty) with ✚/✖ examples | auditor (direct); goal-evaluator (via its methodology skill); anyone making verdict-class calls |
+| `.claude/delegation-templates.md` | Fill-in dispatch templates (search/implement/refactor/research/review) | Interactive maintainer sessions dispatching ad-hoc subagents |
 | `.claude/maintenance-protocol.md` | Which files may be edited autonomously vs. need the user; the resync invariant; lessons format; condensation rule | Anyone editing framework/instruction files |
-| `.claude/anti-patterns.md` | Documented failure modes from production use | Orchestrator, reviewer, auditor; add new ones per maintenance protocol §2 |
+| `.claude/anti-patterns/` | Failure-mode tree: README index + one file per numbered entry — scan the index, open only matching entries | Orchestrator, reviewer, auditor; add new ones per maintenance protocol §2 |
 | `.claude/letter-to-future-sessions.md` | How this system degrades and what to check first | New sessions doing framework work |
-| `.claude/architecture/` | System architecture, agent catalog, pipeline flow, artifact map | Reference (all agents) |
+| `.claude/architecture/` | System architecture, agent catalog, pipeline flow, artifact map | Framework maintainers only — pipeline agents must NOT read these (orchestrator rule) |
 
 ## AGENTS AND SKILLS
 
diff --git a/incredible_auto_dev/README.md b/incredible_auto_dev/README.md
index 0538b13..418800e 100644
--- a/incredible_auto_dev/README.md
+++ b/incredible_auto_dev/README.md
@@ -38,7 +38,7 @@ The multi-CLI infrastructure is in place and the Claude path is verified non-reg
 - [ ] **Real Codex end-to-end run + hardening.** `_codex_invoke` quota/error regexes in `lib/quota-retry.sh` are best-guess. First real `--cli codex` run will reveal the actual OpenAI rate-limit/error wording to match. Expect 1–2 tightening passes.
 - [ ] **Codex stream parsing.** `lib/codex_stream_renderer.py` handles several plausible event shapes; confirm against real `codex exec --json` NDJSON and trim to the actual schema.
 - [ ] **Retire legacy `.claude/` files from git.** `.claude/agents/*.md`, `.claude/settings.json`, `.claude/hooks/*`, `.claude/skills/*` are still tracked and regenerated on sync (producing small, functionally-identical cosmetic diffs). Move them to `.gitignore` and `git rm --cached` once the Claude no-regression run passes.
-- [ ] **`hooks/lib/normalize-input.sh` / `normalize-output.sh`.** Planned shims so one hook script reads a uniform input schema and writes a uniform allow/block decision across both CLIs. SEC-7 inlined the normalization in the two Bash guards (argv → stdin `.tool_input.command` fallback + Claude `permissionDecision` deny-JSON); the shim remains TODO for deduplication and for the PostToolUse hooks (`$CLAUDE_TOOL_INPUT_FILE_PATH` is equally nonexistent — they need the stdin `.tool_input.file_path` treatment; advisory-only, so inert ≠ security hole).
+- [ ] **`hooks/lib/normalize-input.sh` / `normalize-output.sh`.** Planned shims so one hook script reads a uniform input schema and writes a uniform allow/block decision across both CLIs. SEC-7 inlined the normalization in the two Bash guards (argv → stdin `.tool_input.command` fallback + Claude `permissionDecision` deny-JSON) and CTX-1 did the same for the PostToolUse pair (stdin `.tool_input.file_path`, advisory); the shim remains TODO purely for deduplication.
 - [ ] **Architecture docs.** `.claude/architecture/*.md` still describe the pre-migration Claude-only layout; update for the neutral source + adapter model.
 - [ ] **MCP servers in neutral source.** `policy/mcp-servers.yaml` is a stub; Claude MCP/plugins currently live in `adapters/claude/passthrough/`. Promote to neutral source when a shared MCP definition is actually needed.
 - [ ] **Mixed-CLI runs (per-agent override).** Architecture supports a per-agent `cli:` field in `agent.yaml`; not wired up. Deferred until there's a real use case.
@@ -230,6 +230,10 @@ means it's an early or backend-only iteration with no features to walk through.
 
 ### Outputs produced
 
+**New to these files and the status codes inside them?** Read
+[`docs/READING-REPORTS.md`](docs/READING-REPORTS.md) — a plain-language guide to
+which report to open and what every code means.
+
 | Artifact | Where | Audience |
 |----------|-------|----------|
 | Plain-language section + Watch-it-work gallery + technical accordions | `reports/phase-<phase>-summary.html` | Everyone |
@@ -445,7 +449,7 @@ bash scripts/automation/render-summary.sh --session-index <sid>        # re-rend
 | `runs/goal-session-<sid>/state/journey-history.json` | Per-journey pass/fail/regressed status across iterations |
 | `runs/goal-session-<sid>/telemetry.jsonl` | Structured event log for the session — see [`docs/goal-mode-telemetry.md`](docs/goal-mode-telemetry.md) |
 
-**Temp-file hygiene:** every run gets its own `$CHAIN_TMP_ROOT/iad.<run-id>.<pid>` dir (root default `~/.cache/iad` — a big un-quota'd disk, NOT the quota'd tmpfs `/tmp`), exported as `TMPDIR`, so pytest/playwright/service-log temp files are isolated per run and removed on exit (goal mode clears the previous iteration's dir at each iteration boundary). A startup janitor sweeps strays from crashed runs across the root and legacy `/tmp` — stale `iad.*` dirs, `bench-*`/`judgment-*` scratch, `pytest-of-$USER` entries, and the `shared/` interactive-TMPDIR dir — and `chain_tmp_disk_guard` sweeps aggressively under disk pressure (goal mode pauses as resumable `AWAITING_DISK` only when the root filesystem stays critically low). Self-service cleanup any agent can run: `./scripts/automation/tmp-doctor.sh [--status|--clean|--aggressive]`. Knobs: `CHAIN_TMPDIR_DISABLE=true` (leave the environment alone), `CHAIN_TMP_JANITOR=false` (skip the sweep), `CHAIN_TMP_ROOT` (base dir), `CHAIN_TMP_LEGACY_ROOTS` (extra janitor roots, default `/tmp`), `CHAIN_TMP_MAX_AGE_HOURS=24` / `CHAIN_TMP_SHARED_MAX_AGE_HOURS=72` (age gates), `CHAIN_BENCH_KEEP=2` (bench scratch retention), `CHAIN_TMP_MIN_FREE_MB=2048` / `CHAIN_TMP_HARD_MIN_FREE_MB=512` / `CHAIN_TMP_PROBE_MB=32` (disk guard), `CHAIN_TMP_DISK_GUARD=false` (disable the guard). See `.claude/anti-patterns.md` #21.
+**Temp-file hygiene:** every run gets its own `$CHAIN_TMP_ROOT/iad.<run-id>.<pid>` dir (root default `~/.cache/iad` — a big un-quota'd disk, NOT the quota'd tmpfs `/tmp`), exported as `TMPDIR`, so pytest/playwright/service-log temp files are isolated per run and removed on exit (goal mode clears the previous iteration's dir at each iteration boundary). A startup janitor sweeps strays from crashed runs across the root and legacy `/tmp` — stale `iad.*` dirs, `bench-*`/`judgment-*` scratch, `pytest-of-$USER` entries, and the `shared/` interactive-TMPDIR dir — and `chain_tmp_disk_guard` sweeps aggressively under disk pressure (goal mode pauses as resumable `AWAITING_DISK` only when the root filesystem stays critically low). Self-service cleanup any agent can run: `./scripts/automation/tmp-doctor.sh [--status|--clean|--aggressive]`. Knobs: `CHAIN_TMPDIR_DISABLE=true` (leave the environment alone), `CHAIN_TMP_JANITOR=false` (skip the sweep), `CHAIN_TMP_ROOT` (base dir), `CHAIN_TMP_LEGACY_ROOTS` (extra janitor roots, default `/tmp`), `CHAIN_TMP_MAX_AGE_HOURS=24` / `CHAIN_TMP_SHARED_MAX_AGE_HOURS=72` (age gates), `CHAIN_BENCH_KEEP=2` (bench scratch retention), `CHAIN_TMP_MIN_FREE_MB=2048` / `CHAIN_TMP_HARD_MIN_FREE_MB=512` / `CHAIN_TMP_PROBE_MB=32` (disk guard), `CHAIN_TMP_DISK_GUARD=false` (disable the guard). See `.claude/anti-patterns/21-shared-tmp-accumulation.md`.
 
 ## Subrepo Usage
 
diff --git a/incredible_auto_dev/adapters/claude/sync.py b/incredible_auto_dev/adapters/claude/sync.py
index 8167f71..c9be2ab 100644
--- a/incredible_auto_dev/adapters/claude/sync.py
+++ b/incredible_auto_dev/adapters/claude/sync.py
@@ -9,7 +9,7 @@ Generates:
   .claude/commands/<name>.md   (slash commands, mirrored from commands/)
 
 Leaves alone:
-  .claude/core.md, workflow.md, anti-patterns.md, project-template.md
+  .claude/core.md, workflow.md, the anti-patterns/ tree, project-template.md
   .claude/architecture/
   .claude/settings.local.json, .example
 """
@@ -191,31 +191,27 @@ def _hooks_block_for_claude() -> dict:
         entries = []
         for matcher, basename in by_event[event]:
             # Claude Code passes hook input as JSON on stdin (.tool_input.*);
-            # $CLAUDE_TOOL_INPUT_COMMAND was never a real env var, so the Bash
-            # guards read stdin themselves (argv remains the test-harness /
-            # Codex path) and return decisions as hookSpecificOutput JSON on
-            # stdout with exit 0 (SEC-7). Every hook is wrapped `|| true`: on
-            # Claude the exit code carries no signal (exit 1 is a NON-blocking
-            # error; the stdout JSON is the decision channel) and a hook crash
-            # must never surface into the transcript. install-security-gate
-            # keeps stderr un-redirected so its warn banners reach debug logs.
+            # $CLAUDE_TOOL_INPUT_COMMAND / $CLAUDE_TOOL_INPUT_FILE_PATH were
+            # never real env vars, so every hook reads stdin itself (argv
+            # remains the test-harness / Codex path): the PreToolUse guards
+            # extract .tool_input.command and return decisions as
+            # hookSpecificOutput JSON on stdout with exit 0 (SEC-7); the
+            # PostToolUse hooks extract .tool_input.file_path and stay
+            # advisory (stderr warnings only, CTX-1). Every hook is wrapped
+            # `|| true`: on Claude the exit code carries no signal (exit 1 is
+            # a NON-blocking error; stdout JSON is the decision channel) and a
+            # hook crash must never surface into the transcript.
+            # install-security-gate keeps stderr un-redirected so its warn
+            # banners reach debug logs.
             tail = " || true" if basename == "install-security-gate.sh" else " 2>/dev/null || true"
             cmd_path = f"$CLAUDE_PROJECT_DIR/.claude/hooks/{basename}"
-            if event == "PostToolUse":
-                # FIXME(follow-up): $CLAUDE_TOOL_INPUT_FILE_PATH is likewise not
-                # a real env var — the PostToolUse hooks need the stdin
-                # (.tool_input.file_path) treatment; they are advisory-only, so
-                # their inertness is not a security hole (roadmap SEC-7 note).
-                arg = ' "$CLAUDE_TOOL_INPUT_FILE_PATH"'
-            else:
-                arg = ""
             entries.append(
                 {
                     "matcher": matcher,
                     "hooks": [
                         {
                             "type": "command",
-                            "command": f'bash "{cmd_path}"{arg}{tail}',
+                            "command": f'bash "{cmd_path}"{tail}',
                         }
                     ],
                 }
diff --git a/incredible_auto_dev/agents/demo-narrator/agent.yaml b/incredible_auto_dev/agents/demo-narrator/agent.yaml
index 899e091..72280d6 100644
--- a/incredible_auto_dev/agents/demo-narrator/agent.yaml
+++ b/incredible_auto_dev/agents/demo-narrator/agent.yaml
@@ -12,6 +12,6 @@ tools_allowed:
 - Glob
 - Grep
 - Write
-version: 2.0.0
-last_updated: '2026-05-22'
+version: 2.1.0
+last_updated: '2026-07-26'
 body: body.md
diff --git a/incredible_auto_dev/agents/demo-narrator/body.md b/incredible_auto_dev/agents/demo-narrator/body.md
index e112c77..f8d8929 100644
--- a/incredible_auto_dev/agents/demo-narrator/body.md
+++ b/incredible_auto_dev/agents/demo-narrator/body.md
@@ -17,6 +17,9 @@ testing. Favor the flows that were already verified working this iteration.
 
 CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
+1. `.claude/skills/plain-language.md` — the shared plain-writing standard. It
+   governs every `title` and `narration` field you write.
+
 The dispatch wrapper passes you: a `mode` (`record`, `live`, or `session`), a
 `phase-id` (or a session `sid` in session mode), the `FRONTEND_URL`, and the
 **Demo JSON output path** to write.
diff --git a/incredible_auto_dev/agents/developer/agent.yaml b/incredible_auto_dev/agents/developer/agent.yaml
index 87b3136..02ec569 100644
--- a/incredible_auto_dev/agents/developer/agent.yaml
+++ b/incredible_auto_dev/agents/developer/agent.yaml
@@ -3,6 +3,6 @@ description: Implementation agent. Reads the execution plan from runs/<phase>/pl
   following TDD. Handles both backend and frontend work. On retry, reads existing review/QA reports and
   fixes only the listed issues. Writes dev handoff when complete.
 model_tier: standard
-version: 1.1.1
-last_updated: '2026-07-03'
+version: 1.1.2
+last_updated: '2026-07-25'
 body: body.md
diff --git a/incredible_auto_dev/agents/developer/body.md b/incredible_auto_dev/agents/developer/body.md
index ec66822..9ac5e84 100644
--- a/incredible_auto_dev/agents/developer/body.md
+++ b/incredible_auto_dev/agents/developer/body.md
@@ -9,7 +9,7 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
 1. `docs/goal.md` — understand the project's overall goal before implementing
 2. `.claude/project-template.md` — stack configuration, test commands, architecture principles
-3. `docs/architecture/*.md` — understand existing project architecture
+3. `docs/architecture/*.md` — existing project architecture (if present; created by update-docs.sh after the first finalized phase — absence is normal early on, skip silently)
 4. `runs/<phase>/plan.md` — execution plan (what to build)
 5. Phase spec at `docs/phases/<phase>.md` — requirements and definition of done
 6. Relevant existing code in the project
diff --git a/incredible_auto_dev/agents/goal-evaluator/agent.yaml b/incredible_auto_dev/agents/goal-evaluator/agent.yaml
index e6f8c5b..7b81606 100644
--- a/incredible_auto_dev/agents/goal-evaluator/agent.yaml
+++ b/incredible_auto_dev/agents/goal-evaluator/agent.yaml
@@ -10,6 +10,6 @@ tools_allowed:
 - Grep
 - Bash
 - Write
-version: 1.7.0
-last_updated: '2026-07-18'
+version: 1.8.0
+last_updated: '2026-07-26'
 body: body.md
diff --git a/incredible_auto_dev/agents/goal-evaluator/body.md b/incredible_auto_dev/agents/goal-evaluator/body.md
index 128bf3c..ae726d5 100644
--- a/incredible_auto_dev/agents/goal-evaluator/body.md
+++ b/incredible_auto_dev/agents/goal-evaluator/body.md
@@ -198,6 +198,17 @@ Write to `runs/goal-session-<sid>/iter-<N>/eval.md`:
 <only present when verdict is GOAL_ACHIEVED, REGRESSION, or STALLED — explain why halting>
 ```
 
+### 6b. Plain-language rule for prose fields
+
+The session owner is not a native English reader. In the PROSE fields only — `Reasoning` and `Next-step recommendation` in evaluator-log.md (step 4), and the `## Summary`, `## Next-Step Recommendation`, and `## Halt Justification` sections of eval.md (step 6) — write plain English:
+
+- Short sentences. Everyday words. No idioms.
+- Whenever you name a journey ID, put its short name next to it: J-04 "Sign in with email" — never a bare ID list.
+- Describe what the user would see, not internal code: "the login page rejects a correct password", not a function, class, or variable name. (Evidence references keep their file paths — that rule is unchanged.)
+- End the recommendation with one sentence saying what should happen next, phrased so a non-programmer could act on it or approve it.
+
+This rule changes WORDING ONLY. It does not change any machine-parsed format: the verdict lines and their allowed values defined elsewhere in this document, the depth-recommendation line, all headings, table shapes, JSON schemas, and file paths stay exactly as specified.
+
 ### 7. Overwrite iteration-state.md (the next planner's digest)
 
 After eval.md is written (so your fresh verdict is its newest entry), write
diff --git a/incredible_auto_dev/agents/iteration-summarizer/agent.yaml b/incredible_auto_dev/agents/iteration-summarizer/agent.yaml
index 883df49..f75428e 100644
--- a/incredible_auto_dev/agents/iteration-summarizer/agent.yaml
+++ b/incredible_auto_dev/agents/iteration-summarizer/agent.yaml
@@ -8,6 +8,6 @@ model_tier: standard
 tools_allowed:
 - Read
 - Write
-version: 1.1.0
-last_updated: '2026-07-07'
+version: 1.2.0
+last_updated: '2026-07-26'
 body: body.md
diff --git a/incredible_auto_dev/agents/iteration-summarizer/body.md b/incredible_auto_dev/agents/iteration-summarizer/body.md
index b687953..b242f26 100644
--- a/incredible_auto_dev/agents/iteration-summarizer/body.md
+++ b/incredible_auto_dev/agents/iteration-summarizer/body.md
@@ -21,6 +21,7 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
 1. `templates/iteration-summary.md` — the exact section structure your output must follow
 2. `.claude/skills/visible-change-summarizer.md` — tone and brevity guidance for user-facing summaries
+3. `.claude/skills/plain-language.md` — the shared plain-writing standard (short sentences, IDs always with friendly names, the status word table). It governs the `## In plain words` block, the project story, and the delivered wrap.
 
 ## Input files (read only what exists)
 
diff --git a/incredible_auto_dev/agents/orchestrator/agent.yaml b/incredible_auto_dev/agents/orchestrator/agent.yaml
index b861b3d..8d5c092 100644
--- a/incredible_auto_dev/agents/orchestrator/agent.yaml
+++ b/incredible_auto_dev/agents/orchestrator/agent.yaml
@@ -3,6 +3,6 @@ description: Phase execution planner. When invoked by run-phase.sh, reads CLAUDE
   then writes a concise execution plan to runs/<phase>/plan.md. The shell script (run-phase.sh) drives
   the dev/review/QA loop; the orchestrator's job is planning only.
 model_tier: standard
-version: 1.0.0
-last_updated: '2026-05-04'
+version: 1.0.1
+last_updated: '2026-07-25'
 body: body.md
diff --git a/incredible_auto_dev/agents/orchestrator/body.md b/incredible_auto_dev/agents/orchestrator/body.md
index 139cb8f..42e14ff 100644
--- a/incredible_auto_dev/agents/orchestrator/body.md
+++ b/incredible_auto_dev/agents/orchestrator/body.md
@@ -9,7 +9,7 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 
 1. `docs/goal.md` — project goal, vision, success criteria (ensure phase aligns with this)
 2. `.claude/project-template.md` — project-specific stack, architecture principles
-3. `docs/architecture/` — project architecture docs (understand what already exists)
+3. `docs/architecture/` — project architecture docs (if present; created by update-docs.sh after the first finalized phase — absence is normal early on, skip silently)
 4. `docs/handoffs/*-dev.md` — prior phase handoffs (what was already built)
 5. The phase spec at `docs/phases/<phase>.md`
 
diff --git a/incredible_auto_dev/agents/readme-maintainer/agent.yaml b/incredible_auto_dev/agents/readme-maintainer/agent.yaml
index 57ec9fc..57d070f 100644
--- a/incredible_auto_dev/agents/readme-maintainer/agent.yaml
+++ b/incredible_auto_dev/agents/readme-maintainer/agent.yaml
@@ -10,6 +10,6 @@ tools_allowed:
 - Edit
 - Glob
 - Grep
-version: 1.0.0
-last_updated: '2026-06-04'
+version: 1.1.0
+last_updated: '2026-07-26'
 body: body.md
diff --git a/incredible_auto_dev/agents/readme-maintainer/body.md b/incredible_auto_dev/agents/readme-maintainer/body.md
index 25ab215..51d06b5 100644
--- a/incredible_auto_dev/agents/readme-maintainer/body.md
+++ b/incredible_auto_dev/agents/readme-maintainer/body.md
@@ -22,6 +22,8 @@ CLAUDE.md is auto-loaded into your system prompt — do not Read it again.
 3. The existing `README.md` at the repo root, if present.
 4. `templates/project-readme.md` — the skeleton to start from **only if `README.md`
    is absent**.
+5. `.claude/skills/plain-language.md` — the shared plain-writing standard for
+   everything you write into the AUTO blocks.
 
 ## Capability inputs (read what exists, skip what doesn't)
 
diff --git a/incredible_auto_dev/agents/retro-analyst/agent.yaml b/incredible_auto_dev/agents/retro-analyst/agent.yaml
index 3aa43e0..580d600 100644
--- a/incredible_auto_dev/agents/retro-analyst/agent.yaml
+++ b/incredible_auto_dev/agents/retro-analyst/agent.yaml
@@ -6,6 +6,6 @@ model_tier: light
 tools_allowed:
 - Read
 - Write
-version: 1.0.0
-last_updated: '2026-07-10'
+version: 1.1.0
+last_updated: '2026-07-26'
 body: body.md
diff --git a/incredible_auto_dev/agents/retro-analyst/body.md b/incredible_auto_dev/agents/retro-analyst/body.md
index deb5a3d..7c9d511 100644
--- a/incredible_auto_dev/agents/retro-analyst/body.md
+++ b/incredible_auto_dev/agents/retro-analyst/body.md
@@ -38,6 +38,14 @@ Number items RETRO-1 … RETRO-5, at most 5, each ≤20 lines, in this exact sha
 
 Hard rule: no Evidence line → no item. Every Evidence entry names the digest section and quotes the line(s) verbatim, e.g. `Evidence: Friction counters — "Quota pauses: 3"`. Zero items is a valid output: when nothing recurred, the Candidate items body is exactly `nothing recurred worth proposing` plus one sentence saying why (e.g. all counters zero, lessons product-only).
 
+Plain-writing rules (the report is read by a non-developer owner first):
+- The FIRST sentence of every **Problem:** must be plain English: short, everyday
+  words, says who hits the pain and when. Technical detail goes in the second
+  sentence.
+- Never use a bare internal codename (EVO-1, §16, REL-n, a lane or tripwire name)
+  without saying in words what it is.
+- Keep the header's code legend line exactly as the skeleton shows it.
+
 ## Output
 
 Write exactly ONE file — the output path from your dispatch prompt (`reports/goal-session-<sid>-retro.md`), overwriting any existing file:
@@ -45,8 +53,11 @@ Write exactly ONE file — the output path from your dispatch prompt (`reports/g
 ```
 # Session retro — <sid>
 
-> **PROPOSALS ONLY** — a human promotes candidates into docs/improvement-roadmap.md §16
-> per EVO-1; nothing here is scheduled work.
+> **Ideas only — nothing here is scheduled work.** These are suggestions for
+> improving the build system itself, not your product. A human reviews them and
+> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
+> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
+> = chance a change breaks something else.
 
 **Session:** <sid> · **Terminal status:** <from Outcome> · **Iterations:** <from Outcome>
 
diff --git a/incredible_auto_dev/commands/goal-status.md b/incredible_auto_dev/commands/goal-status.md
index f318de0..ebcfada 100644
--- a/incredible_auto_dev/commands/goal-status.md
+++ b/incredible_auto_dev/commands/goal-status.md
@@ -27,3 +27,7 @@ the engine, dispatch agents, or write anything.
    the opt-in `--intent-checkpoint` "is this the product you wanted?" pause —
    resuming acknowledges it), **orphaned** (dead engine PID — `/goal-resume`),
    or **finished** (and the final verdict).
+7. **Plain words first:** lead the summary with the status translated into a
+   plain sentence (the wording table lives in `docs/READING-REPORTS.md`), with
+   the raw code in parentheses — e.g. "The chain is paused and waiting for your
+   blueprint review (`AWAITING_BLUEPRINT_APPROVAL`)." Same for the last verdict.
diff --git a/incredible_auto_dev/docs/READING-REPORTS.md b/incredible_auto_dev/docs/READING-REPORTS.md
new file mode 100644
index 0000000..aa165de
--- /dev/null
+++ b/incredible_auto_dev/docs/READING-REPORTS.md
@@ -0,0 +1,186 @@
+# Reading the chain's output — a plain guide
+
+This page explains, in plain words, everything the chain prints and writes for you:
+which file to open, what each status code means, and what the short codes stand for.
+Keep it open the first few times you run the chain.
+
+(For how to *start* a run, see [`goal-mode-quickstart.md`](goal-mode-quickstart.md).
+This page is only about reading what comes out.)
+
+---
+
+## 1. Which file do I open?
+
+Start at the top of this list. The first two cover 90% of what you need.
+
+### `reports/goal-session-<sid>-index.html` — the session page (open this first)
+The one-page overview of a goal session. It leads with "The story so far" (a plain
+narrative of how your product has grown), then the latest demo gallery with
+screenshots, a journey progress matrix, and one card per iteration.
+**Check three things:** does the story match what you wanted? are the journey rows
+turning green over time? does the newest card's badge look healthy?
+
+### `reports/phase-<iter>-summary.html` — one iteration, one page
+The per-iteration view. It leads with **"In plain words"** (what you can do now, what
+changed this time, what's next) and a "Watch it work" screenshot gallery. Technical
+sections sit below, collapsed — you can ignore them.
+**Check three things:** the "In plain words" block, the verdict badge, the gallery.
+
+### `reports/phase-<iter>-what-to-click.md` — try it yourself in 5 minutes
+A short numbered guide: exact pages to open, buttons to press, and what you should
+see. No developer knowledge needed. Written for full iterations and phases.
+
+### `runs/goal-session-<sid>/iter-<N>/eval.md` — why the loop stopped
+The evaluator's explanation for an iteration: a summary, evidence per journey, and a
+recommendation. The terminal points you here when the chain halts. Read the
+`## Summary` and `## Next-Step Recommendation` sections; skip the tables unless
+you're curious.
+
+### `runs/goal-session-<sid>/state/blueprint.md` — the app's floor plan (pause: review it)
+When the chain pauses with "blueprint approval needed", it wants you to check two
+things it drafted: the navigation plan (does every feature have an obvious home?)
+and the data contract (each shared number has exactly one source). Edit the file
+directly — your edits ARE the approval — then resume.
+
+### `runs/goal-session-<sid>/state/intent-review.md` — mid-session checkpoint (pause: answer it)
+Appears only if you enabled the intent checkpoint. It shows progress and asks: is
+this still the product you wanted? Edit `docs/goal.md` if the direction drifted,
+then resume.
+
+### `reports/goal-session-<sid>-delivered.html` — the finish-line page
+Written once, when the goal is achieved. A friendly wrap-up of everything the
+product can do, with the final walkthrough embedded. The `.md` next to it is the
+text version.
+
+### `reports/phase-<iter>-demo-script.md` and `-demo-results.md` — the guided tour
+The narrated walkthrough behind the gallery: each step has a plain sentence, the
+exact action taken, and a screenshot (`reports/demo/<iter>/step-NN.png`). Steps
+marked `[NEW]` were added this iteration. A failed demo step is a soft note, never
+a failure of your product's tests.
+
+### `reports/phase-<iter>-user-visible-changes.md` — what users can now do
+A plain list of new abilities, visible UI changes, changed behavior, and things
+built in the backend that have no UI yet ("not visible yet").
+
+### `reports/goal-session-<sid>-retro.md` — ideas for improving the chain itself
+Written after a session ends. Suggestions for the framework (not your product),
+for a human to accept or ignore. Nothing in it is scheduled work.
+
+### Deeper, technical reports (fine to skip)
+Written for the pipeline and for developers; the summary pages above already
+digest them:
+- `reports/reviews/<iter>-review.md` — code review, verdict PASS / FAIL.
+- `reports/qa/<iter>-qa.md` and `-test-plan.md` — test runs (test cases are `TC-nn`).
+- `reports/phase-<iter>-ui-test-plan.md` / `-ui-test-results.md` — browser tests (`UT-nn`)
+  with screenshots as evidence.
+- `reports/phase-<iter>-ui-surface-map.md`, `-ux-regression.md`, `-closure-verdict.md`,
+  `reports/qa/<iter>-ui-audit.md` — UI coverage and closure gates.
+- `docs/handoffs/<iter>-dev.md` / `-audit.md`, `reports/phase-<iter>-implementation-summary.md`
+  — developer handoffs and the auditor's report.
+- `runs/goal-session-<sid>/iter-<N>/coherence.md` — checks new code didn't duplicate
+  data sources or hide features outside the navigation.
+- `runs/goal-session-<sid>/iter-<N>/journeys-changed.md` — appears only if you edited
+  `docs/goal.md` mid-session; lists journeys that must be re-verified.
+- `runs/<...>/status.json`, `session.json`, `summary.json`, `plan.md`,
+  `journey-history.json`, `state/project-story.md` — machine state and sources the
+  HTML pages are built from. You never need to open them.
+
+---
+
+## 2. What the status codes mean
+
+These appear in the terminal, in `session.json`, and on the HTML badges. The
+terminal prints the same plain sentences next to them; this is the full list.
+
+### Session end / pause statuses (goal mode)
+
+| Code | In plain words |
+|---|---|
+| `GOAL_ACHIEVED` | The goal is complete: every must-have journey works and no rule was broken. |
+| `BUDGET_EXHAUSTED` | The session stopped because it reached the iteration limit you set (`--max-iter`). Nothing is broken. Resume with a higher limit to build more. |
+| `STALLED` | The chain stopped because it could not make progress on its own. What was built so far still works. Read the last evaluation, unblock the problem (or edit `docs/goal.md`), then resume. |
+| `REGRESSION_HALT` | Something that worked before is broken now, so the chain stopped to protect your product. After you fix or accept the break, resume with `--acknowledge-regression`. |
+| `ABORTED` | The run was interrupted before it finished the iteration. Nothing is lost — resume when ready. |
+| `ABORT_MALFORMED` | The evaluator wrote an unreadable verdict twice in a row, so the chain stopped instead of guessing. Your product is unchanged. |
+| `GATE_BLOCKED` | A project rule (gate) rejected this iteration's plan, so the chain paused before building anything. |
+| `AWAITING_BLUEPRINT_APPROVAL` | Paused, not broken — waiting for you to review `state/blueprint.md` and resume. |
+| `AWAITING_INTENT_REVIEW` | Paused, not broken — waiting for you to finish the intent checkpoint and resume. |
+| `AWAITING_PUMP` | The Claude Code session that runs the agents went away, so the engine paused safely. Re-open Claude Code in this repo and run `/goal-resume`. |
+| `AWAITING_GITHUB_AUTH` | Paused because the chain cannot push to GitHub (login missing or expired). Run `gh auth login`, then resume. |
+| `AWAITING_DISK` | Paused because this computer is low on disk space — the chain never builds in that state. Free space, then resume. |
+| `in_progress` | The session is running normally. |
+
+### The evaluator's per-iteration verdict
+
+Printed after every iteration as `Verdict: <code>`.
+
+| Code | In plain words |
+|---|---|
+| `CONTINUE` | Normal progress — the chain plans and builds the next piece by itself. |
+| `ESCALATE` | The last round found something tricky, so the next round uses the slower, more careful pipeline. |
+| `REGRESSION` | Something that worked before is broken — the chain is stopping so you can look. |
+| `STALLED` | The evaluator sees no useful next step it can do alone — it is stopping to ask for your help. |
+| `GOAL_ACHIEVED` | Every must-have journey now works, so the session will finish. |
+
+"Next depth" after the verdict: `lean` = a quick build-and-check round; `full` = a
+full round with extra review, audit and UX checks.
+
+### Other verdict words you'll see inside reports
+
+| Code | In plain words |
+|---|---|
+| `PASS` / `FAIL` | The check passed / found problems (the pipeline fixes and retries by itself). |
+| `PASS_WITH_NOTES` | Passed; small non-blocking remarks attached. |
+| `PASS_WITH_GAPS` | Passed overall, but the auditor found real gaps worth reading. |
+| `SKIPPED` | The check didn't run (usually: no browser or no frontend this round). |
+| `COHERENCE-PASS / WARN / FAIL` | New code kept / strained / broke the app's structure rules (one source per value, every feature reachable in the navigation). |
+| `CLOSURE-PASS / CLOSURE-FAIL` | The final completeness gate for an iteration passed / blocked it. |
+| `UI-PASS / UI-PASS-WITH-GAPS / UI-FAIL` | The UI evolved properly with the new capability / partially / not at all. |
+| `RECORDED / RECORDED_WITH_NOTES / NOT_YET` | The demo tour was captured / captured with soft notes / there is nothing to demo yet. |
+| `IN-PROGRESS` | The session hasn't ended; this iteration is a normal middle step. |
+
+### Journey status words (the pills and the matrix)
+
+`passing` / `already_passing` = ✓ working · `failing` = ✗ broken (not built or not
+working yet) · `regressed` = ⚠ worked before, broken now · `partial` = ~ partly
+working · `unknown` = ? not verified yet · `pending_infra` = the test could not run
+(browser/infrastructure problem), the feature itself may be fine.
+
+---
+
+## 3. Short codes and chain words
+
+**ID families**
+- `J-01, J-02…` — your **user journeys** from `docs/goal.md` (things a user can do,
+  e.g. J-04 "Sign in with email"). The product is done when all of them pass.
+- `UT-01…` — **browser tests**, each checking one journey through a real browser.
+- `TC-01…` — **QA test cases** from the test plan.
+- `P0 / P1 / P2` — how urgent (P0 = most urgent).
+- `Effort S / M / L` — how much work (small / one session / multiple sessions).
+- `Risk LOW / MED / HIGH` — chance the change breaks something else.
+- `CRITICAL / IMPORTANT / GAP / OBSERVATION` — audit findings, most to least serious.
+- `RETRO-1…` — numbered suggestions in a retro report.
+- `CTX-8, REL-14, SPEED-2, EVO-1, §16…` — internal improvement tickets and section
+  numbers for the framework itself (`docs/improvement-roadmap.md`). Maintainer
+  bookkeeping — safe to ignore while running your product.
+
+**Chain words**
+- **journey** — one thing a user can do, written as steps with an observable result.
+- **iteration** — one loop of plan → build → check. **baseline** — iteration 0, which
+  only verifies the starting state and builds nothing.
+- **lean / full depth** — quick round vs. full-rigor round (see above).
+- **evaluator** — the agent that judges each iteration and writes `eval.md`.
+- **gate** — a mechanical safety check that can override an agent's claim. If a gate
+  demotes a verdict, the stricter answer wins.
+- **blueprint** — the app's floor plan you approve once (navigation + data contract).
+- **pump** — the Claude Code session that actually runs the agents when you use the
+  interactive `/goal` commands. If it disappears, the engine pauses (`AWAITING_PUMP`).
+- **showcase** — the non-blocking tail of each iteration that produces the demo,
+  summary, README refresh, and HTML pages. It can fail without failing your build.
+- **anti-goal** — a thing you told the chain never to do (`docs/goal.md`).
+
+---
+
+*Single source note (for maintainers): the plain sentences for statuses and verdicts
+are defined in `scripts/automation/lib/plain-language.sh` and mirrored here and in
+`skills/plain-language.md`. If wording changes, change it in all three together.*
diff --git a/incredible_auto_dev/docs/goal-mode-interactive.md b/incredible_auto_dev/docs/goal-mode-interactive.md
index 56dee7c..4d5d0c4 100644
--- a/incredible_auto_dev/docs/goal-mode-interactive.md
+++ b/incredible_auto_dev/docs/goal-mode-interactive.md
@@ -105,10 +105,11 @@ programmatic path with an API key** (`run-goal.sh` without `--interactive`).
   the run pauses; continue after it resets. (The headless path's
   sleep-until-reset does **not** apply in interactive mode.)
 - **Model tiering becomes live.** Each agent runs on its `.claude/agents/<name>.md`
-  model tier (Opus for strong agents, Sonnet for standard, Haiku for light), so
-  cost follows the tier. The **strong tier is Opus 4.8** — Anthropic's most capable
-  Opus-tier model. It runs on Max; Pro may not grant it. If a
-  tier's model is unavailable, set an interactive tier override (see Troubleshooting).
+  model tier, so cost follows the tier. The **strong tier** resolves via
+  `config/model-tiers.yaml` (`python3 scripts/automation/lib/agent_permissions.py
+  tier-model strong` prints the current id). Strong-tier models run on Max; Pro may
+  not grant them. If a tier's model is unavailable, set an interactive tier override
+  (see Troubleshooting).
   Do **not** set
   `CLAUDE_CODE_SUBAGENT_MODEL` — it overrides every subagent and flattens the tiers.
 - **Fidelity gaps vs headless.** The per-agent `--effort` downgrade is **not**
diff --git a/incredible_auto_dev/docs/goal-mode-quickstart.md b/incredible_auto_dev/docs/goal-mode-quickstart.md
index a32b5dc..d4e3029 100644
--- a/incredible_auto_dev/docs/goal-mode-quickstart.md
+++ b/incredible_auto_dev/docs/goal-mode-quickstart.md
@@ -4,6 +4,10 @@ Goal mode is an autonomous, continuous mode of the AI Multi-Agent Dev Chain. You
 
 For phase-by-phase mode (still fully supported), see the main [README](../README.md). For the architecture details, see [`.claude/architecture/goal-mode.md`](../.claude/architecture/goal-mode.md).
 
+New to the terms and status codes (STALLED, `J-01`, lean/full…)? Keep
+[`READING-REPORTS.md`](READING-REPORTS.md) open next to your first run — it explains
+every report file and every code in plain words.
+
 ## When to use goal mode vs phase mode
 
 | Use **phase mode** when … | Use **goal mode** when … |
@@ -347,4 +351,4 @@ Then:
 - [`templates/project-goal.md`](../templates/project-goal.md) — full goal template with all required sections
 - [`.claude/architecture/goal-mode.md`](../.claude/architecture/goal-mode.md) — internal architecture
 - [`docs/goal-mode-telemetry.md`](goal-mode-telemetry.md) — telemetry event schema
-- [`.claude/anti-patterns.md`](../.claude/anti-patterns.md) — common authoring pitfalls (especially #18)
+- [`.claude/anti-patterns/`](../.claude/anti-patterns/) — common authoring pitfalls (especially `18-goal-journeys-anti-goals.md`)
diff --git a/incredible_auto_dev/docs/goal.md b/incredible_auto_dev/docs/goal.md
index 5475c1e..784fb31 100644
--- a/incredible_auto_dev/docs/goal.md
+++ b/incredible_auto_dev/docs/goal.md
@@ -20,11 +20,41 @@ Developers and teams who want to automate their development lifecycle with AI ag
 6. Artifact-based inter-agent communication (no free-form conversation)
 7. Configurable model tiers (strong/standard/light) per agent
 
-## Non-Goals
-
-- Being a general-purpose coding assistant — this is a structured, phase-gated pipeline, not a freeform agent
-- Replacing human judgment on architecture, product direction, or critical design decisions
-- Supporting non-Claude AI providers (Gemini, GPT, etc.) — Claude-only by design
+## Must-have user journeys
+
+The framework's own acceptance journeys — operator-observable and evidence-backed. They
+also make this file pass the same validation (`run-goal.sh validate_goal_file`) the
+framework enforces on every adopter's goal.md.
+
+- **J-01: Adopter ships phase 1**
+  1. Fill `.claude/project-template.md` and author `docs/phases/phase-1.md` from `templates/phase-spec.md`.
+  2. Run `./scripts/automation/run-phase.sh phase-1`.
+  Acceptance: the run ends with CLOSURE-PASS; `runs/phase-1/status.json` reaches the
+  final step; all 6 `reports/phase-1-*` UI-visibility artifacts exist.
+- **J-02: Goal session achieves a demo goal**
+  1. Author a small adopter-style `docs/goal.md` (journeys + anti-goals).
+  2. Run `./scripts/automation/run-goal.sh --session-id demo`.
+  Acceptance: the session halts GOAL_ACHIEVED only through the deterministic gates plus
+  the two-key confirm — `telemetry.jsonl` halt event, `iter-<N>/gate-report.md`, and the
+  CONFIRM_ACHIEVED verdict line all present.
+- **J-03: Interrupted session resumes**
+  1. Ctrl-C a running goal session mid-iteration.
+  2. Relaunch `./scripts/automation/run-goal.sh --session-id <same-sid>`.
+  Acceptance: the engine resumes from checkpoint without repeating completed steps —
+  checkpoint markers present in the session dir; `engine.log` shows completed steps
+  skipped on re-entry.
+- **J-04: Offline evals protect edits**
+  1. Run `./scripts/automation/run-evals.sh` with no API access.
+  2. Seed a mirror edit (hand-edit one `.claude/agents/*.md`), run it again, then resync
+     with `python3 scripts/automation/sync-cli-assets.py --cli claude` and run it a third time.
+  Acceptance: exit 0 on the clean tree, exit 1 on the seeded drift, exit 0 again after
+  the resync.
+
+## Anti-goals
+
+- No freeform-assistant mode: every change enters through a phase spec or a goal-mode iteration spec — work with no spec behind it is rejected in review
+- No autonomous decisions on what the product IS: changes to `CLAUDE.md`, `docs/goal.md` journeys/anti-goals, model spend, or gate defaults require explicit human approval (maintenance-protocol §1) — an agent-made change there without a matching approved task is a violation
+- No third AI provider: the backends are exactly Claude Code and OpenAI Codex CLI (`docs/cli-providers.md`) — a change adding another provider integration is out of scope
 
 ## Note for Projects Using This Framework
 
diff --git a/incredible_auto_dev/docs/improvement-roadmap.archive.md b/incredible_auto_dev/docs/improvement-roadmap.archive.md
index 4365dc5..c855db9 100644
--- a/incredible_auto_dev/docs/improvement-roadmap.archive.md
+++ b/incredible_auto_dev/docs/improvement-roadmap.archive.md
@@ -713,3 +713,133 @@ legend: active file §4.
   `run-evals.sh` §2c: suite went 83 → 84 pass / 0 fail, verbose line
   `PASS: unit: tests/automation/test-doc-drift.sh`. Effort S → self-verified per
   §2.7/G8 (fresh-session rule is M/L only).
+
+### DOC-5 · "Reading the reports" guide
+- **Priority:** P1 · **Effort:** S · **Risk:** LOW · **Status:** absorbed into PLAIN-1 (§19) 2026-07-26
+- **Problem:** the chain produces MD summaries, HTML reports, demo galleries, a session
+  index, gate reports — nothing tells the owner which one to open and what to look for.
+- **Current state:** partial coverage spread across README sections + `runs/SCHEMA.md`
+  (machine-oriented).
+- **Change spec:** `docs/READING-REPORTS.md`: per artifact — what it is, who it's for
+  (owner vs maintainer), when it appears, the 3 things to check (e.g. session index:
+  journey matrix trend, latest verdict, assumptions section once NEED-6 lands).
+  One screenshot-free page; link from README "Outputs" table and the session-index
+  footer if the renderer has one.
+- **DoD:** every report artifact in `runs/SCHEMA.md`'s human-facing set has an entry.
+- **Verify:** cross-check list vs `runs/SCHEMA.md`; link greps.
+- **Files:** `docs/READING-REPORTS.md` (new), README.
+- **Rollback:** docs-only.
+- **Absorption note (2026-07-26):** delivered as PLAIN-1 slice 1 — the guide gained a
+  status/verdict glossary and a code legend, and the renderer footer link became part
+  of PLAIN-1 slice 4 (renderer commit).
+
+### PLAIN-1 · Plain-English explanation layer (absorbs DOC-5)
+- **Priority:** P1 · **Effort:** M · **Risk:** MED · **Status:** DONE (2026-07-26)
+- **Verified (2026-07-26, fresh non-implementer session per G8, at 138982c):** DoD
+  checked line by line. Verify block re-run green: evals 136 pass / 0 fail
+  (`test-plain-language.sh` in the §2c list; 59 pass / 0 fail standalone),
+  `sync-cli-assets.py --check` 0 drift, renderer self-test passed (updated pins + the
+  MD-contract assertions), lib smoke prints the three-part plain block ending in the
+  `docs/READING-REPORTS.md` pointer. Call-sites: 22 `explain_goal_status`/`_verdict`
+  sites in run-goal.sh (every anchored halt — BUDGET_EXHAUSTED, STALLED ×2,
+  REGRESSION_HALT, ABORT_MALFORMED — all pauses, GOAL_ACHIEVED, the verdict line
+  `:2246`) + 5 `explain_phase` sites in run-phase.sh (Review/QA pass+fail, final
+  banner). Glossary: all 12 statuses + 5 verdicts appear in READING-REPORTS.md, which
+  is linked from README and the quickstart top. Writer wiring: iteration-summarizer /
+  demo-narrator / readme-maintainer name the skill (agent.yaml bumps 2.0.0→2.1.0,
+  1.1.0→1.2.0, 1.0.0→1.1.0), retro-analyst carries the rules inline by design (no
+  skill line), goal-status translates with the raw code in parentheses. Evaluator:
+  §6b at body.md:201, agent.yaml 1.8.0; spot-run evidenced by the kept
+  `judgment-goal-evaluator-*` sandboxes (shared temp root): both bracketing cases ran
+  WITH the §6b body (v1.8.0 confirmed inside each sandbox), GOT == EXPECTED
+  (GOAL_ACHIEVED / REGRESSION), prose follows the new rule, `**Verdict:**` markers
+  byte-exact — in fact the full 6-case goal-evaluator suite was green (the a87a59f
+  14/14 re-baseline run carried the §6b working tree). Architecture skill-count
+  claims read 16 in all three docs plus the skills-and-hooks row.
+- **Problem:** every surface the owner actually reads is written for the machine or for
+  maintainer AIs: ~20 SHOUTING status/verdict codes with no gloss at point of use
+  (STALLED vs AWAITING_PUMP vs REGRESSION_HALT vs ABORT_MALFORMED all mean "stopped"
+  with different remedies), roadmap codenames leaking into terminal output and retros
+  (REL-14, EVO-1, §16), 35–50-word sentences with env-vars inline, five unlegended
+  severity scales (P0-2 / S-M-L / LOW-MED-HIGH / CRITICAL-IMPORTANT-GAP-OBSERVATION /
+  anti-goal critical-minor). The friendly layer that exists (`## In plain words`, HTML
+  story pages, pause banners) reaches only 2 of 20 agents, and nothing tells the owner
+  which file to open.
+- **Current state:** (anchors @ 4181629) run-goal.sh: 253 ad-hoc echo sites, no style
+  policy, halt lines are bare codes (`:1458` BUDGET_EXHAUSTED, `:1465`/`:2448` STALLED,
+  `:2442` REGRESSION_HALT, `:2458` ABORT_MALFORMED); only the pause banners
+  (`:1511-1532`, `:1581-1596`) are owner-readable. The ONLY enum→sentence translation
+  in the repo is `skills/goal-interactive-dispatch.md:242-254` (pump-only).
+  goal-evaluator body: zero style guidance; `## Next-Step Recommendation` mandates
+  ID-speak. Renderer prints raw enums in hero/cover/pills
+  (`render_iteration_summary.py:1355`, `:1875`, `:1326-1334`) though a plain-word pill
+  map already exists (`:1586-1592`). Style guidance overall: 2 UI-scoped skills + one
+  core.md line — no shared standard, no glossary doc.
+- **Change spec:** six commits, each independently eval-green:
+  1. this roadmap entry (+ DOC-5 absorbed → archive).
+  2. `docs/READING-REPORTS.md` (new; DOC-5's guide + status/verdict glossary + code
+     legend), linked from README outputs area + `docs/goal-mode-quickstart.md` top.
+  3. NEW `scripts/automation/lib/plain-language.sh` (`explain_goal_status STATUS [SID]
+     [ROOT]`, `explain_goal_verdict VERDICT DEPTH`, `explain_phase KEY`, `plain_*_keys`
+     list fns; case-based; every fn `return 0`) + additive call-sites at every
+     run-goal.sh halt/pause/verdict echo and run-phase.sh Review/QA/final-banner lines
+     (existing echoes byte-untouched; `run-goal.sh:1793` is test-pinned) + NEW
+     `tests/automation/test-plain-language.sh` (map completeness; coverage of every
+     `write_session_summary "X"` / `d["status"] = "X"` status; output purity — no
+     `**Verdict:**`/`## `/parse-marker strings; pinned-literal re-asserts) wired into
+     the `run-evals.sh` §2c list.
+  4. renderer: `_PLAIN_BADGE` map + `badge-enum` suffix at hero/cover, plain pill text
+     with raw status in `title=`, session-index footer link to READING-REPORTS.md;
+     update the 4 affected self-test expect-list pins in the same commit
+     (`"J-04 · passing"` → `"J-04 · ✓ working"` etc.); the `:2402-2438` MD-contract
+     assertions must pass UNCHANGED.
+  5. NEW `skills/plain-language.md` (audience profile, hard rules, plain-word table
+     copied from the lib, 3 bad→good pairs, never-simplify list) wired via one
+     "always read" line into iteration-summarizer, demo-narrator, readme-maintainer.
+     retro-analyst gets NO skill line (light tier + its one-file evidence boundary):
+     instead its body inlines the literal rules — a code-legend line in the report
+     skeleton, "first Problem sentence is plain English", no bare codenames.
+     `commands/goal-status.md` gains "translate the
+     status, raw code in parentheses"; bump each touched agent.yaml version; fix the
+     eval-enforced "15 skills" claims → 16 (architecture README/adoption-guide/
+     system-overview) + skills-and-hooks row; resync mirrors.
+  6. goal-evaluator: ONE additive block `### 6b. Plain-language rule for prose fields`
+     (scope: Reasoning / Next-step recommendation / `## Summary` /
+     `## Next-Step Recommendation` / `## Halt Justification` ONLY; short sentences;
+     journey IDs always carry their short name; describe what the user would see; the
+     block must NOT contain a literal verdict-marker string, lint_contracts
+     `:169-199`); agent.yaml 1.7.0 → 1.8.0; resync; then the judgment spot-run below
+     BEFORE push.
+- **Spot-run gate (commit 6):** `run-judgment-evals.sh --list --judge goal-evaluator`
+  first (free); STOP if 2 × per-case estimate > ~US$5. Then exactly two bracketing
+  cases with `--keep-sandbox`: `case-01-clean-goal-achieved` and
+  `case-03-regression-broken-journey` (≈ $4.76 projected). Both must exit 0 with
+  GOT == EXPECTED; eyeball sandbox eval.md for the new style. Any class flip →
+  `git revert` commit 6 + resync, stop.
+- **DoD:** every terminal halt/pause and the per-iteration verdict line print a plain
+  what-happened / is-the-product-OK / what-to-do block + a `docs/READING-REPORTS.md`
+  pointer; every status in READING-REPORTS.md glossary; renderer hero/cover/pills show
+  plain words (enum still visible); the 4 writer agents name the skill; evaluator
+  prose rule landed with spot-run green; evals green; machine contracts byte-identical
+  (self-test (c) proves it).
+- **Verify:** `./scripts/automation/run-evals.sh` after every commit;
+  `python3 scripts/automation/sync-cli-assets.py --cli claude --check`;
+  `bash -c 'source scripts/automation/lib/plain-language.sh; explain_goal_status
+  STALLED demo /tmp'`; renderer self-test; the spot-run.
+- **Files:** `docs/improvement-roadmap.md`, `docs/READING-REPORTS.md` (new), README,
+  `docs/goal-mode-quickstart.md`, `scripts/automation/lib/plain-language.sh` (new),
+  `scripts/automation/{run-goal.sh,run-phase.sh,run-evals.sh}`,
+  `tests/automation/test-plain-language.sh` (new),
+  `scripts/automation/lib/render_iteration_summary.py`, `skills/plain-language.md`
+  (new), `agents/{iteration-summarizer,retro-analyst,demo-narrator,readme-maintainer,
+  goal-evaluator}/{body.md,agent.yaml}`, `commands/goal-status.md`,
+  `.claude/architecture/{README,adoption-guide,system-overview,skills-and-hooks}.md`,
+  regenerated mirrors.
+- **Rollback:** per-commit `git revert` (each slice is independent); commit 6 revert
+  must be followed by a resync.
+- **Stop-and-ask:** spot-run projected cost > ~US$5; any golden verdict class flip;
+  any place where a plain line cannot be ADDED without editing a test-pinned or
+  machine-parsed line.
+- **Non-goals:** diagnostic/tripwire console lines; enum/schema/path renames; length
+  budgets on specs (D6); reviewer/auditor bodies; roadmap/commit-message prose; a
+  中文 layer (possible later on top of the same single-source table).
```
