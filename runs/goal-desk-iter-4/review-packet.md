# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 17. Shown in full: 17.

```diff
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
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-desk-index.html             | 12 +++--
 runs/goal-session-desk/.engine.lock/epoch        |  2 +-
 runs/goal-session-desk/.engine.lock/pid          |  2 +-
 runs/goal-session-desk/dispatch/.pump-alive      |  4 +-
 runs/goal-session-desk/engine.pid                |  2 +-
 runs/goal-session-desk/journey-scripts/J-07.json |  5 +-
 runs/goal-session-desk/session.json              |  6 +--
 runs/goal-session-desk/state/assumptions.md      | 41 ++++++++++++++
 runs/goal-session-desk/state/blueprint.md        | 17 ++++--
 runs/goal-session-desk/summary.md                | 69 ++++++++++++++++++++++--
 runs/goal-session-desk/telemetry.jsonl           | 32 +++++++++++
 runs/goal-session-desk/trace/trace.jsonl         | 10 ++++
 12 files changed, 180 insertions(+), 22 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
