# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

```diff
diff --git a/apps/backend/app/research/desk_screen.py b/apps/backend/app/research/desk_screen.py
index 911c0ef..f59fc8b 100644
--- a/apps/backend/app/research/desk_screen.py
+++ b/apps/backend/app/research/desk_screen.py
@@ -54,8 +54,9 @@ screen's final ``rows`` list (TC-14) -- one rule serves both jobs.
 still reflects whichever pinned timeframes genuinely have bars (never a fabricated all-false).
 
 **Basis disclosure (goal-desk-iter-9, J-08).** Every RANKED row also carries ``basis_as_of``
-(copied VERBATIM from ``result["basis_as_of"]`` -- the SAME value ``_resolve_reference_close``
-already consumes to find the reference close, so this costs zero additional
+(copied VERBATIM from ``result["basis_as_of"]`` -- the SAME value
+``_resolve_reference_close_and_history`` already consumes to find the reference close, so this
+costs zero additional
 ``BarStore``/``compute_tradability`` work) and ``basis_age_days`` (a plain calendar-date
 difference between that value and the row's own ``as_of``, mirroring ``_distance_bps``'s "plain
 arithmetic derivation" style -- see ``_basis_age_days`` below). Skip rows never carry these fields
@@ -65,6 +66,16 @@ row-shape validation or enrichment (a plain checksum-verified passthrough), so
 ``GET /research/desk/screen`` serves that absence VERBATIM -- never defaulted, never backfilled
 (the append-only rail applies to row CONTENT, not just to the snapshot as a whole).
 
+**History disclosure (goal-desk-iter-15, J-11).** Every RANKED row also carries
+``history_sessions`` (the count of daily bars at or before ``basis_as_of``, derived in the SAME
+``store.merged_bars(symbol, "1d")`` ascending walk ``_resolve_reference_close_and_history`` already
+performs to resolve the reference close -- zero additional ``BarStore`` read) and ``history_start``
+(the earliest of those bars' own timestamp, formatted through the identical ``_iso`` function
+``basis_as_of`` itself uses). Skip rows never carry these fields, matching the basis-disclosure
+precedent exactly. A snapshot recorded BEFORE this addition simply has ranked rows that OMIT these
+two keys entirely -- the SAME append-only-row-content discipline the basis fields established:
+never defaulted, never backfilled, never present as ``null``.
+
 **No new ``Config`` field.** The screen store's directory resolves via ``resolve_desk_screen_dir``
 below -- a bare ``TAPEOLOGY_DESK_SCREEN_DIR``-env-var-or-sibling-of-``desk_universe_dir_resolved()``
 default (the ``edge_report_cache.resolve_cache_db_path`` pattern) -- never a ``desk_screen_dir``
@@ -233,23 +244,38 @@ def _row_rank_key(row: dict) -> tuple[int, float, float, str]:
     return (-_CLASS_RANK[row["band_class"]], row["distance_bps"], -row["band_score"], row["symbol"])
 
 
-# --- reference close price (TC-19) ----------------------------------------------------------------
+# --- reference close price + history disclosure (TC-19; goal-desk-iter-15, J-11) ------------------
 
 
-def _resolve_reference_close(store: BarStore, symbol: str, basis_as_of: str) -> float:
+def _resolve_reference_close_and_history(
+    store: BarStore, symbol: str, basis_as_of: str
+) -> tuple[float, int, str]:
     """The ONE daily bar in ``store.merged_bars(symbol, "1d")`` whose own timestamp -- formatted
-    through the SAME ``_iso`` function ``tradability.py`` uses -- matches ``basis_as_of`` verbatim.
-    Never re-derives WHICH bar is the basis (that stays ``compute_tradability``'s exclusive
-    decision); never touches ``tradability.py``'s or ``levels.py``'s return shape.
+    through the SAME ``_iso`` function ``tradability.py`` uses -- matches ``basis_as_of`` verbatim,
+    PLUS (goal-desk-iter-15, J-11 -- see the module docstring's "History disclosure" section) the
+    two history-depth fields derived from that SAME ascending walk: ``history_sessions`` (how many
+    bars were walked up to and including the match -- ``merged_bars`` is already ascending, so this
+    is simply a running count, never a second pass or a separate counting read) and
+    ``history_start`` (the FIRST bar's own timestamp seen in this same walk, formatted through the
+    identical ``_iso``). Never re-derives WHICH bar is the basis (that stays
+    ``compute_tradability``'s exclusive decision); never touches ``tradability.py``'s or
+    ``levels.py``'s return shape; issues exactly the ONE ``store.merged_bars`` call this function
+    already issued before J-11 (TC-6 -- zero extra store read).
 
     Structurally this bar always exists: ``basis_as_of`` is itself derived from a bar
     ``compute_tradability`` read via this EXACT accessor (``tradability.py``'s own
     ``_select_daily_series`` calls ``BarStore.merged_bars(symbol, "1d")``), and the store is
     immutable between the two reads within one screen computation -- a missing match is an
-    unreachable internal-invariant failure, surfaced loudly (never a fabricated close)."""
+    unreachable internal-invariant failure, surfaced loudly (never a fabricated close or history)."""
+    history_sessions = 0
+    history_start: str | None = None
     for bar in store.merged_bars(symbol, "1d"):
-        if _iso(bar.epoch) == basis_as_of:
-            return bar.close
+        history_sessions += 1
+        bar_iso = _iso(bar.epoch)
+        if history_start is None:
+            history_start = bar_iso
+        if bar_iso == basis_as_of:
+            return bar.close, history_sessions, history_start
     raise RuntimeError(
         f"internal invariant violated: no daily bar for {symbol!r} matches basis_as_of "
         f"{basis_as_of!r} -- compute_tradability's own basis bar must always be present in "
@@ -295,8 +321,9 @@ def compute_screen(
     the full snapshot content MINUS the store-assigned ``id``/``created_utc`` (``ScreenStore.record``
     assigns those): ``{screen_date, as_of, universe_snapshot_id, config_fingerprint,
     bar_store_signature, rows, skipped}``. Each RANKED row additionally carries ``basis_as_of``/
-    ``basis_age_days`` (goal-desk-iter-9, J-08 -- see the module docstring's "Basis disclosure"
-    section); skip rows never carry them.
+    ``basis_age_days`` (goal-desk-iter-9, J-08) and ``history_sessions``/``history_start``
+    (goal-desk-iter-15, J-11) -- see the module docstring's "Basis disclosure" and "History
+    disclosure" sections; skip rows never carry any of the four.
 
     ``progress``, if given, is called after EACH member with ``{"symbol": symbol}`` (the caller
     tracks its own done/total counters -- the ``desk_topup_compute.run_topup`` precedent).
@@ -340,7 +367,9 @@ def compute_screen(
                  "coverage": coverage, "tick_evidence": tick_evidence}
             )
         else:
-            close = _resolve_reference_close(bar_store, symbol, result["basis_as_of"])
+            close, history_sessions, history_start = _resolve_reference_close_and_history(
+                bar_store, symbol, result["basis_as_of"]
+            )
             best = _select_best_band(result["bands"], close)
             rows.append(
                 {
@@ -355,6 +384,8 @@ def compute_screen(
                     "tick_evidence": tick_evidence,
                     "basis_as_of": result["basis_as_of"],
                     "basis_age_days": _basis_age_days(result["basis_as_of"], as_of),
+                    "history_sessions": history_sessions,
+                    "history_start": history_start,
                 }
             )
 
diff --git a/apps/backend/tests/test_desk_hover_tooltip_guard.py b/apps/backend/tests/test_desk_hover_tooltip_guard.py
index 2947ab0..e539942 100644
--- a/apps/backend/tests/test_desk_hover_tooltip_guard.py
+++ b/apps/backend/tests/test_desk_hover_tooltip_guard.py
@@ -91,13 +91,14 @@ def test_ranked_row_drill_in_tooltip_is_built_from_distance_score_and_coverage_f
     ``basis_as_of``/``basis_age_days`` -- the new basis column is a plain descriptive `<td>` with
     NO per-cell ``title`` of its own (the same F2 lesson applied proactively), so its full-precision
     detail must join this SAME consolidated tooltip or it is unreachable by pointer, exactly like
-    the three fields above."""
+    the three fields above. goal-desk-iter-15 (J-11) adds one more: ``row.history_start`` -- the
+    new history column applies the identical F2-proactive discipline."""
     source = _DESK_PAGE.read_text()
     fn_name = _anchor_title_function_name(source, "desk-row-drill-in")
     fn_source = _extract_function(source, fn_name)
     for needle in (
         "row.distance_bps", "row.band_score", "latest_window_end_utc",
-        "row.basis_as_of", "row.basis_age_days",
+        "row.basis_as_of", "row.basis_age_days", "row.history_start",
     ):
         assert needle in fn_source, (
             f"{fn_name}() never references {needle!r} -- the ranked row's composite hover "
diff --git a/apps/backend/tests/test_desk_screen.py b/apps/backend/tests/test_desk_screen.py
index a592a4d..546ec97 100644
--- a/apps/backend/tests/test_desk_screen.py
+++ b/apps/backend/tests/test_desk_screen.py
@@ -10,6 +10,7 @@ from __future__ import annotations
 
 import json
 import shutil
+from datetime import date, datetime, timedelta, timezone
 from pathlib import Path
 
 import pytest
@@ -30,7 +31,13 @@ from app.research.desk_screen import (
     resolve_desk_screen_dir,
     screen_as_of,
 )
-from app.research.desk_screen import _basis_age_days, _distance_bps, _row_rank_key, _select_best_band
+from app.research.desk_screen import (
+    _basis_age_days,
+    _distance_bps,
+    _epoch,
+    _row_rank_key,
+    _select_best_band,
+)
 from app.research.desk_universe import UniverseStore
 
 FIXTURE_UNIVERSE_DIR = Path(__file__).parent / "fixtures" / "universe"
@@ -466,6 +473,8 @@ def test_fixture_universe_with_zero_bars_skips_every_member_as_no_bars(ctx):
     assert {s["symbol"] for s in screen["skipped"]} == set(members)
     assert all(s["reason"] == "no_bars" for s in screen["skipped"])
     assert all(s["tick_evidence"] is False for s in screen["skipped"])
+    # TC-5 (goal-desk-iter-15, J-11): a skip row never carries either history-disclosure field.
+    assert all("history_sessions" not in s and "history_start" not in s for s in screen["skipped"])
 
 
 def test_aapl_row_cross_checks_byte_identical_to_the_real_tradability_route(ctx, monkeypatch):
@@ -588,6 +597,8 @@ def test_a_daily_series_with_no_resolvable_prior_session_is_skipped_no_basis(ctx
     assert entry["reason"] == "no_basis"
     assert entry["coverage"]["1d"]["has_bars"] is True
     assert entry["coverage"]["1h"]["has_bars"] is False
+    # TC-5 (goal-desk-iter-15, J-11): a "no_basis" skip row never carries either history field.
+    assert "history_sessions" not in entry and "history_start" not in entry
 
 
 def test_repeat_computation_in_two_fresh_instances_is_byte_identical(ctx, tmp_path):
@@ -762,3 +773,229 @@ def test_a_legacy_row_recorded_without_basis_fields_serves_them_absent_never_bac
     row = records[0]["rows"][0]
     assert "basis_as_of" not in row
     assert "basis_age_days" not in row
+
+
+# ==================================================================================================
+# history disclosure (goal-desk-iter-15, J-11) -- history_sessions / history_start
+# ==================================================================================================
+
+
+def _daily_bar_epoch(day: date) -> float:
+    """04:00 UTC -- the SAME daily-bar hour every Yahoo fixture in this file already uses."""
+    return datetime(day.year, day.month, day.day, 4, 0, 0, tzinfo=timezone.utc).timestamp()
+
+
+def _iso_of(epoch: float) -> str:
+    """The SAME epoch -> ISO formatting ``desk_screen.py``'s own ``_iso`` uses -- a local copy per
+    this project's own convention (each module/test owns its tiny formatting helper)."""
+    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(timespec="microseconds").replace(
+        "+00:00", "Z"
+    )
+
+
+def _daily_bars(symbol: str, start: date, count: int) -> list[RawBar]:
+    """``count`` synthetic daily bars for a REAL fixture-universe member (lessons.md iter-2: never a
+    synthetic ``AAA``-style symbol for a clause naming real symbols -- only the price/volume values
+    here are synthetic), one per calendar day starting at ``start``. Only the TIMESTAMPS matter to a
+    history-depth count, so price/volume are arbitrary constants."""
+    return [
+        RawBar(symbol, "1d", _daily_bar_epoch(start + timedelta(days=i)), 100.0, 101.0, 99.0, 100.5, 1000)
+        for i in range(count)
+    ]
+
+
+def _seed_daily_bars(bar_store: BarStore, bar_index: BarIndex, bars: list[RawBar]) -> None:
+    meta = bar_store.record(
+        symbol=bars[0].symbol, timeframe="1d",
+        window_start_utc=_iso_of(bars[0].epoch), window_end_utc=_iso_of(bars[-1].epoch + 86400.0),
+        feed="yahoo", bars=bars,
+    )
+    bar_index.insert(meta)
+
+
+def test_history_sessions_and_start_match_the_seeded_daily_series_up_to_basis(ctx):
+    """TC-1: a real fixture-universe member (ABBV) seeded with 5 synthetic daily bars, all dated
+    strictly before ``SCREEN_DATE`` (so every seeded bar counts and the basis resolves to the LAST
+    one) -- the ranked row's ``history_sessions`` equals the seeded count and ``history_start``
+    equals the earliest seeded bar's own timestamp."""
+    universe_store, bar_store, bar_index, dataset_store = ctx
+    bars = _daily_bars("ABBV", start=date(2026, 6, 12), count=5)  # 06-12 .. 06-16, all < 06-22
+    _seed_daily_bars(bar_store, bar_index, bars)
+
+    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
+    row = next(r for r in screen["rows"] if r["symbol"] == "ABBV")
+
+    assert row["basis_as_of"] == _iso_of(bars[-1].epoch)
+    assert row["history_sessions"] == 5
+    assert row["history_start"] == _iso_of(bars[0].epoch)
+
+
+def test_history_sessions_is_not_off_by_one_when_the_basis_bar_is_the_series_first_bar(ctx):
+    """Error case (goal.md's own TESTING REQUIREMENTS): a member whose basis resolves to the VERY
+    FIRST bar in its own series -- ``history_sessions`` must read ``1``, never ``0`` (an off-by-one
+    undercount) nor any value implying a second, unseen bar."""
+    universe_store, bar_store, bar_index, dataset_store = ctx
+    bars = _daily_bars("ABBV", start=date(2026, 6, 18), count=1)
+    _seed_daily_bars(bar_store, bar_index, bars)
+
+    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
+    row = next(r for r in screen["rows"] if r["symbol"] == "ABBV")
+
+    assert row["history_sessions"] == 1
+    assert row["history_start"] == row["basis_as_of"] == _iso_of(bars[0].epoch)
+
+
+def test_short_and_long_history_members_carry_visibly_different_session_counts_in_the_same_run(ctx):
+    """TC-2: two real fixture-universe members, each seeded with its OWN synthetic daily series --
+    ABBV short (5 sessions), ACN long (450 sessions), both entirely BEFORE ``SCREEN_DATE`` so every
+    seeded bar counts -- resolve visibly different ``history_sessions`` in the SAME screen run,
+    independently confirming the DoD's <=60 / >=400 split is reachable in THIS rig (iter-9 lesson:
+    never trust goal.md's own cited live numbers as a byte-for-byte target)."""
+    universe_store, bar_store, bar_index, dataset_store = ctx
+    short_bars = _daily_bars("ABBV", start=date(2026, 6, 12), count=5)
+    long_bars = _daily_bars("ACN", start=date(2025, 1, 1), count=450)
+    _seed_daily_bars(bar_store, bar_index, short_bars)
+    _seed_daily_bars(bar_store, bar_index, long_bars)
+
+    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
+    by_symbol = {r["symbol"]: r for r in screen["rows"]}
+    assert "ABBV" in by_symbol and "ACN" in by_symbol
+
+    short_row, long_row = by_symbol["ABBV"], by_symbol["ACN"]
+    assert short_row["history_sessions"] == 5
+    assert short_row["history_start"] == _iso_of(short_bars[0].epoch)
+    assert long_row["history_sessions"] == 450
+    assert long_row["history_start"] == _iso_of(long_bars[0].epoch)
+
+    # The DoD's own split (<=60 short, >=400 long), confirmed reachable in THIS run.
+    assert short_row["history_sessions"] <= 60
+    assert long_row["history_sessions"] >= 400
+
+
+def test_history_fields_stay_byte_identical_on_a_recompute_under_identical_pins(ctx, tmp_path):
+    """TC-3: mirrors ``test_recording_a_freshly_computed_screen_twice_is_refused_and_basis_fields_
+    stay_byte_identical`` for the two NEW fields -- a screen recorded once, then a FRESH computation
+    under the identical pins, is refused a second write, and the content already on disk (read back
+    via ``list()``) is byte-identical to the second (unrecorded) computation's ``history_sessions``/
+    ``history_start`` on every ranked row."""
+    universe_store, bar_store, bar_index, dataset_store = ctx
+    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
+    screen_store = ScreenStore(tmp_path / "screen")
+
+    first_screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
+    recorded = screen_store.record(**first_screen)
+
+    second_screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
+    with pytest.raises(ScreenAlreadyRecorded) as excinfo:
+        screen_store.record(**second_screen)
+    assert excinfo.value.existing_id == recorded["id"]
+
+    stored_records, errors = screen_store.list()
+    assert errors == []
+    assert json.dumps(stored_records[0]["rows"], sort_keys=True) == json.dumps(
+        second_screen["rows"], sort_keys=True
+    )
+    aapl_row = next(r for r in stored_records[0]["rows"] if r["symbol"] == "AAPL")
+    assert aapl_row["history_sessions"] == next(
+        r for r in second_screen["rows"] if r["symbol"] == "AAPL"
+    )["history_sessions"]
+    assert aapl_row["history_start"] is not None
+
+
+def test_a_legacy_row_recorded_without_history_fields_serves_them_absent_never_backfilled(tmp_path):
+    """TC-4: the exact shape every screen snapshot recorded BEFORE this iteration has: ranked rows
+    that OMIT ``history_sessions``/``history_start`` entirely (never merely present-as-``null``) --
+    mirrors ``test_a_legacy_row_recorded_without_basis_fields_serves_them_absent_never_backfilled``
+    for the two new fields. ``_record``'s own default row carries no such keys at all, so this is
+    true by construction; this test pins that contract so a future change cannot silently start
+    defaulting or backfilling legacy rows on read."""
+    store = ScreenStore(tmp_path / "screen")
+    _record(store)
+
+    records, errors = store.list()
+    assert errors == []
+    row = records[0]["rows"][0]
+    assert "history_sessions" not in row
+    assert "history_start" not in row
+
+
+def test_history_fields_add_zero_extra_merged_bars_calls(ctx, monkeypatch):
+    """TC-6: proves the row builder's reference-close-plus-history derivation
+    (``_resolve_reference_close_and_history``) issues exactly the ONE ``BarStore.merged_bars(symbol,
+    "1d")`` call it already issued before J-11 (goal-desk-iter-9's own reference-close walk) -- never
+    a second, separate walk for the history fields. Compares the per-symbol total ``merged_bars(...,
+    "1d")`` call count of a FULL screen walk against ``compute_tradability`` run ALONE on the
+    identical inputs (the only OTHER source of ``merged_bars(symbol, "1d")`` calls in this walk, via
+    ``tradability.py``'s own ``_select_daily_series`` and ``compute_levels``'s per-timeframe reads):
+    the full walk must add exactly ONE more such call -- the SAME single call the row builder always
+    made -- never two."""
+    universe_store, bar_store, bar_index, dataset_store = ctx
+    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
+
+    as_of_epoch = _epoch(screen_as_of(SCREEN_DATE))
+    calls: list[tuple[str, str]] = []
+    original = BarStore.merged_bars
+
+    def _tracked(self, symbol, timeframe):
+        calls.append((symbol, timeframe))
+        return original(self, symbol, timeframe)
+
+    monkeypatch.setattr(BarStore, "merged_bars", _tracked)
+
+    from app.research.tradability import compute_tradability as _compute_tradability
+
+    _compute_tradability(bar_store, "AAPL", as_of_epoch, CONFIG)
+    baseline_1d_calls = sum(1 for symbol, timeframe in calls if symbol == "AAPL" and timeframe == "1d")
+    calls.clear()
+
+    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
+    assert any(r["symbol"] == "AAPL" for r in screen["rows"]), "AAPL must resolve a ranked row"
+    full_1d_calls = sum(1 for symbol, timeframe in calls if symbol == "AAPL" and timeframe == "1d")
+
+    assert full_1d_calls == baseline_1d_calls + 1, (
+        "the row builder's reference-close+history derivation must add exactly ONE merged_bars "
+        "call beyond compute_tradability's own basis resolution -- never a second walk for history"
+    )
+
+
+def test_aapl_row_history_cross_checks_against_get_candles(ctx, monkeypatch):
+    """TC-7: single-source-of-truth cross-check -- the AAPL ranked row's ``history_sessions``/
+    ``history_start`` match ``GET /research/candles``'s own merged, price-less-row-excluded response
+    (the SAME route the chart itself reads) filtered to bars at or before the row's own
+    ``basis_as_of``, proving the desk never derives a divergent count from a second, independent
+    read."""
+    from fastapi.testclient import TestClient
+
+    from app.main import app, get_market_adapter, manager
+    from app.research.routes import ResearchRegistry, set_registry
+    from app.research.store import JournalStore
+
+    universe_store, bar_store, bar_index, dataset_store = ctx
+    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
+
+    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
+    row = next(r for r in screen["rows"] if r["symbol"] == "AAPL")
+
+    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(bar_store.root))
+    journal = JournalStore(str(bar_store.root.parent / "journal.db"), CONFIG)
+    set_registry(ResearchRegistry(journal, CONFIG))
+    try:
+        with TestClient(app) as client:
+            resp = client.get(
+                "/research/candles", params={"symbol": "AAPL", "timeframe": "1d", "limit": 500}
+            )
+    finally:
+        for ticker in list(manager._engines.keys()):
+            manager.stop(ticker)
+        set_registry(None)
+        app.dependency_overrides.pop(get_market_adapter, None)
+        journal.close()
+
+    assert resp.status_code == 200
+    body = resp.json()
+
+    basis_epoch = datetime.fromisoformat(row["basis_as_of"].replace("Z", "+00:00")).timestamp()
+    filtered = [bar for bar in body["bars"] if bar["ts"] <= basis_epoch]
+    assert len(filtered) == row["history_sessions"]
+    earliest_ts = min(bar["ts"] for bar in filtered)
+    assert _iso_of(earliest_ts) == row["history_start"]
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 270edba..0181955 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -228,6 +228,10 @@ function hasNoCoverageAtAll(coverage: Record<string, { has_bars: boolean }>): bo
 // established for distance/score) plus `row.basis_age_days`. A legacy row (recorded before this
 // iteration) has BOTH keys absent, not merely `null` -- `== null` (loose equality) catches both
 // `undefined` and `null` in one check, per this project's own `fmt()` convention (lib/format.ts).
+// era-desk-iter-15 (J-11): the SAME tooltip also carries the row's history-depth detail --
+// `row.history_sessions` plus `row.history_start` untruncated (the visible "history" cell below
+// shows only the date portion, the SAME rounded-display/full-precision-on-hover split as basis) --
+// a legacy row (recorded before this iteration) has both keys absent, `== null` catches both.
 function deskRowDrillInTitle(row: DeskScreenRow): string {
   const coverageLines = Object.entries(row.coverage)
     .map(([timeframe, tf]) => `${timeframe} window last requested: ${tf.latest_window_end_utc ?? "never"}`)
@@ -236,7 +240,11 @@ function deskRowDrillInTitle(row: DeskScreenRow): string {
     row.basis_as_of == null || row.basis_age_days == null
       ? "basis not recorded in this snapshot"
       : `basis ${row.basis_as_of} (${row.basis_age_days} d before as-of)`;
-  return `distance ${row.distance_bps} bps · score ${row.band_score} · ${basisLine}${
+  const historyLine =
+    row.history_sessions == null || row.history_start == null
+      ? "history not recorded in this snapshot"
+      : `history ${row.history_sessions} sessions from ${row.history_start}`;
+  return `distance ${row.distance_bps} bps · score ${row.band_score} · ${basisLine} · ${historyLine}${
     coverageLines ? ` · ${coverageLines}` : ""
   }`;
 }
@@ -250,14 +258,15 @@ function deskSkipDrillInTitle(skip: DeskScreenSkip): string {
 }
 
 // One ranked row: symbol, side, band-class chip, distance-bps chip, band score, per-timeframe
-// coverage badges, tick-evidence badge, basis column (era-desk-iter-9/J-08) — every value read
-// verbatim from the snapshot. Distance and score are DISPLAYED to two decimals (a
-// `0.33523150389608725 bps` cell defeated the scanability the briefing exists for — audit F3); the
-// full-precision value is not lost — it is reachable via the row's own drill-in anchor's composite
-// `title` (`deskRowDrillInTitle` above, audit F2 fix), never a per-cell `title` (iter-7 audit F1:
-// this comment used to claim the opposite). The basis column follows the SAME split: a rounded,
-// date-only display with the full-precision `basis_as_of` reachable only via that same composite
-// tooltip. The band-class chip carries the "nearest same-class band" caption
+// coverage badges, tick-evidence badge, basis column (era-desk-iter-9/J-08), history column
+// (era-desk-iter-15/J-11) — every value read verbatim from the snapshot. Distance and score are
+// DISPLAYED to two decimals (a `0.33523150389608725 bps` cell defeated the scanability the
+// briefing exists for — audit F3); the full-precision value is not lost — it is reachable via the
+// row's own drill-in anchor's composite `title` (`deskRowDrillInTitle` above, audit F2 fix), never
+// a per-cell `title` (iter-7 audit F1: this comment used to claim the opposite). The basis and
+// history columns follow the SAME split: a rounded, date-only display with the full-precision
+// value reachable only via that same composite tooltip. The band-class chip carries the "nearest
+// same-class band" caption
 // (assumptions.md iter-4 entry 1 — `_select_best_band` itself stays byte-unchanged; this copy
 // keeps the chip honest about what the ranking actually selects rather than implying it is the
 // symbol's single strongest band).
@@ -319,6 +328,15 @@ function DeskRow({ row, asOf }: { row: DeskScreenRow; asOf: string }) {
           ? "basis not recorded in this snapshot"
           : `basis ${row.basis_as_of.slice(0, 10)} · ${row.basis_age_days} d before as-of`}
       </td>
+      {/* era-desk-iter-15 (J-11): descriptive only, session count + start date (full precision --
+          the untruncated `history_start` -- lives in the row anchor's own composite `title` above,
+          NEVER a per-cell `title` here, the same F2 lesson the basis column above already applies).
+          `== null` catches a legacy row's ENTIRELY ABSENT keys (`undefined`), not just `null`. */}
+      <td className={LABEL_CELL} data-testid="desk-row-history">
+        {row.history_sessions == null || row.history_start == null
+          ? "history not recorded in this snapshot"
+          : `history ${row.history_sessions} sessions · from ${row.history_start.slice(0, 10)}`}
+      </td>
     </tr>
   );
 }
@@ -347,6 +365,7 @@ function DeskRowsTable({ rows, asOf }: { rows: DeskScreenRow[]; asOf: string })
             <th className={HEADER_CELL_LEFT}>coverage</th>
             <th className={HEADER_CELL_LEFT}>tick evidence</th>
             <th className={HEADER_CELL_LEFT}>basis</th>
+            <th className={HEADER_CELL_LEFT}>history</th>
           </tr>
         </thead>
         <tbody>
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index f5b3763..7ce9eba 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -798,6 +798,12 @@ export type EdgeReportPayload = EdgeReportResponse | EdgeReportNotComputed;
 // OMIT these two keys ENTIRELY (the append-only rail: legacy snapshots are never backfilled) --
 // the runtime value there is `undefined`, not `null`, so callers must check
 // `row.basis_as_of == null` (loose equality) to catch both, never `=== null` alone.
+// era-desk-iter-15 (J-11) -- history disclosure: how many completed daily sessions (and from what
+// start date) `basis_as_of` was measured over -- derived in the SAME `desk_screen.py` walk that
+// resolves `basis_as_of`/`basis_age_days`, so it carries the identical presence contract: always
+// non-null on a NEWLY computed ranked row, entirely ABSENT (not `null`) on a row recorded before
+// this iteration -- callers must check `row.history_sessions == null` (loose equality), same as
+// the basis fields above.
 export interface DeskScreenRow {
   symbol: string;
   side: "support" | "resistance";
@@ -810,6 +816,8 @@ export interface DeskScreenRow {
   tick_evidence: boolean;
   basis_as_of: string | null;
   basis_age_days: number | null;
+  history_sessions: number | null;
+  history_start: string | null;
 }
 
 // A member the screen walked but could not rank -- two honest, distinct reasons, never conflated:
```
