# Iteration diff (bounded)

Files changed: 6. Shown in full: 6.

```diff
diff --git a/apps/backend/app/research/desk_screen.py b/apps/backend/app/research/desk_screen.py
index f59fc8b..87bf412 100644
--- a/apps/backend/app/research/desk_screen.py
+++ b/apps/backend/app/research/desk_screen.py
@@ -76,6 +76,17 @@ precedent exactly. A snapshot recorded BEFORE this addition simply has ranked ro
 two keys entirely -- the SAME append-only-row-content discipline the basis fields established:
 never defaulted, never backfilled, never present as ``null``.
 
+**Reference-close disclosure (goal-desk-iter-17, J-13).** Every RANKED row also carries
+``reference_close`` -- copied VERBATIM from the SAME ``close`` local
+``_resolve_reference_close_and_history`` already returns and this module already uses to call
+``_select_best_band``/``_distance_bps`` (zero new ``BarStore`` read, zero new accessor, zero
+re-derivation of which bar is the basis -- that stays ``compute_tradability``'s and
+``_resolve_reference_close_and_history``'s exclusive decision, unchanged). Skip rows never carry
+this field, matching the basis/history-disclosure precedent exactly. A snapshot recorded BEFORE
+this addition simply has ranked rows that OMIT this key entirely -- the SAME append-only-row-content
+discipline the basis/history fields established: never defaulted, never backfilled, never present
+as ``null``.
+
 **No new ``Config`` field.** The screen store's directory resolves via ``resolve_desk_screen_dir``
 below -- a bare ``TAPEOLOGY_DESK_SCREEN_DIR``-env-var-or-sibling-of-``desk_universe_dir_resolved()``
 default (the ``edge_report_cache.resolve_cache_db_path`` pattern) -- never a ``desk_screen_dir``
@@ -321,9 +332,10 @@ def compute_screen(
     the full snapshot content MINUS the store-assigned ``id``/``created_utc`` (``ScreenStore.record``
     assigns those): ``{screen_date, as_of, universe_snapshot_id, config_fingerprint,
     bar_store_signature, rows, skipped}``. Each RANKED row additionally carries ``basis_as_of``/
-    ``basis_age_days`` (goal-desk-iter-9, J-08) and ``history_sessions``/``history_start``
-    (goal-desk-iter-15, J-11) -- see the module docstring's "Basis disclosure" and "History
-    disclosure" sections; skip rows never carry any of the four.
+    ``basis_age_days`` (goal-desk-iter-9, J-08), ``history_sessions``/``history_start``
+    (goal-desk-iter-15, J-11), and ``reference_close`` (goal-desk-iter-17, J-13) -- see the module
+    docstring's "Basis disclosure", "History disclosure", and "Reference-close disclosure" sections;
+    skip rows never carry any of the five.
 
     ``progress``, if given, is called after EACH member with ``{"symbol": symbol}`` (the caller
     tracks its own done/total counters -- the ``desk_topup_compute.run_topup`` precedent).
@@ -386,6 +398,7 @@ def compute_screen(
                     "basis_age_days": _basis_age_days(result["basis_as_of"], as_of),
                     "history_sessions": history_sessions,
                     "history_start": history_start,
+                    "reference_close": close,
                 }
             )
 
diff --git a/apps/backend/tests/test_desk_screen.py b/apps/backend/tests/test_desk_screen.py
index 7e80866..05a9256 100644
--- a/apps/backend/tests/test_desk_screen.py
+++ b/apps/backend/tests/test_desk_screen.py
@@ -928,7 +928,10 @@ def test_history_fields_add_zero_extra_merged_bars_calls(ctx, monkeypatch):
     identical inputs (the only OTHER source of ``merged_bars(symbol, "1d")`` calls in this walk, via
     ``tradability.py``'s own ``_select_daily_series`` and ``compute_levels``'s per-timeframe reads):
     the full walk must add exactly ONE more such call -- the SAME single call the row builder always
-    made -- never two."""
+    made -- never two. goal-desk-iter-17 (J-13) TC-7: `reference_close` is read from this SAME
+    `_resolve_reference_close_and_history` tuple (no separate accessor of its own), so this guard
+    already covers it -- no additional test is needed to prove `reference_close` adds zero further
+    `merged_bars` calls."""
     universe_store, bar_store, bar_index, dataset_store = ctx
     _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
 
@@ -1001,6 +1004,190 @@ def test_aapl_row_history_cross_checks_against_get_candles(ctx, monkeypatch):
     assert _iso_of(earliest_ts) == row["history_start"]
 
 
+# ==================================================================================================
+# reference-close disclosure (goal-desk-iter-17, J-13) -- reference_close: the exact price the row's
+# band was measured against, so "the price is inside the wall" is a fact visible on screen instead
+# of arithmetic recovered by inverting distance_bps against a band edge.
+# ==================================================================================================
+
+
+def test_aapl_row_reference_close_equals_the_fixture_bars_own_recorded_close(ctx):
+    """TC-1/TC-19: `reference_close` is byte-identical to the AAPL fixture bar's own recorded close
+    at `basis_as_of` -- the SAME `expected_close` derivation
+    `test_aapl_row_cross_checks_byte_identical_to_the_real_tradability_route` already uses for its
+    own `distance_bps` assertion, confirming the new field is copied from the identical `close`
+    local that assertion is itself built from."""
+    universe_store, bar_store, bar_index, dataset_store = ctx
+    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
+
+    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
+    row = next(r for r in screen["rows"] if r["symbol"] == "AAPL")
+
+    basis_date = datetime.fromisoformat(row["basis_as_of"].replace("Z", "+00:00")).date()
+    fixture = _load_yahoo_fixture(AAPL_DAILY_FIXTURE)
+    basis_bar = next(
+        b for b in fixture["bars"]
+        if datetime.fromtimestamp(b["epoch"], tz=timezone.utc).date() == basis_date
+    )
+    assert row["reference_close"] == basis_bar["close"]
+
+
+def test_reference_close_golden_in_band_and_out_of_band_rows(ctx, monkeypatch):
+    """TC-1: two controlled ranked rows -- one whose `reference_close` sits exactly on its selected
+    band's near edge (`distance_bps == 0.0`, the boundary case of "the price is inside the wall":
+    `price_low <= reference_close <= price_high`), and one whose close sits strictly outside its
+    band. `compute_tradability` is monkeypatched to return exact, controlled bands (the
+    `test_basis_fields_add_zero_extra_compute_tradability_calls` precedent) so both scenarios are
+    deterministic rather than hoped-for from real fixture data; the CLOSE itself is real -- resolved
+    by the real `_resolve_reference_close_and_history` walk over a synthetic daily bar seeded
+    through the real `BarStore`, never hand-set on the row."""
+    import app.research.desk_screen as desk_screen_module
+
+    universe_store, bar_store, bar_index, dataset_store = ctx
+    inband_bar = _daily_bars("ABBV", start=date(2026, 6, 18), count=1)[0]
+    outband_bar = _daily_bars("ACN", start=date(2026, 6, 18), count=1)[0]
+    _seed_daily_bars(bar_store, bar_index, [inband_bar])
+    _seed_daily_bars(bar_store, bar_index, [outband_bar])
+
+    inband_basis = _iso_of(inband_bar.epoch)
+    outband_basis = _iso_of(outband_bar.epoch)
+
+    # price_low == the seeded close exactly -> distance_bps 0.0, and reference_close sits AT the
+    # near edge, i.e. inside [price_low, price_high].
+    inband_band = _band("resistance", inband_bar.close, inband_bar.close + 5.0, "A", 10.0)
+    # price_low strictly above the seeded close -> distance_bps > 0, reference_close outside
+    # [price_low, price_high].
+    outband_band = _band("resistance", outband_bar.close + 5.0, outband_bar.close + 10.0, "B", 5.0)
+
+    original = desk_screen_module.compute_tradability
+
+    def _tracked(store, symbol, as_of_epoch, config):
+        if symbol == "ABBV":
+            return {"no_bar_series_for_symbol": False, "basis_as_of": inband_basis, "bands": [inband_band]}
+        if symbol == "ACN":
+            return {"no_bar_series_for_symbol": False, "basis_as_of": outband_basis, "bands": [outband_band]}
+        return original(store, symbol, as_of_epoch, config)
+
+    monkeypatch.setattr(desk_screen_module, "compute_tradability", _tracked)
+
+    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
+    by_symbol = {r["symbol"]: r for r in screen["rows"]}
+
+    inband_row = by_symbol["ABBV"]
+    assert inband_row["reference_close"] == inband_bar.close
+    assert inband_row["distance_bps"] == 0.0
+    assert inband_row["price_low"] <= inband_row["reference_close"] <= inband_row["price_high"]
+
+    outband_row = by_symbol["ACN"]
+    assert outband_row["reference_close"] == outband_bar.close
+    assert outband_row["distance_bps"] > 0.0
+    assert not (outband_row["price_low"] <= outband_row["reference_close"] <= outband_row["price_high"])
+
+
+def test_row_order_is_unchanged_by_the_reference_close_addition(ctx):
+    """TC-3: `_row_rank_key` is computed entirely from `band_class`/`distance_bps`/`band_score`/
+    `symbol` -- unchanged this iteration (verify via `git diff`, appearing only as unchanged
+    CONTEXT) -- none of which the new `reference_close` field touches. The ranked-row symbol
+    SEQUENCE for this same fixture spread (the `test_rows_are_sorted_by_class_then_distance_then_
+    score_then_symbol` precedent) is exactly the sort of `_row_rank_key` over the SAME rows,
+    confirming the new field is a pure addition to row CONTENT, never a reordering."""
+    universe_store, bar_store, bar_index, dataset_store = ctx
+    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
+    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_DAILY_FIXTURE))
+    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_HOURLY_FIXTURE))
+
+    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
+    symbols = [r["symbol"] for r in screen["rows"]]
+    expected = [r["symbol"] for r in sorted(screen["rows"], key=_row_rank_key)]
+    assert symbols == expected
+    assert symbols == ["MSFT", "AAPL"], "pin the exact fixture-spread order so a silent reorder is caught"
+
+
+def test_aapl_row_reference_close_cross_checks_against_get_candles(ctx, monkeypatch):
+    """TC-2: `reference_close` is byte-identical to the `close` field of the `1d` bar dated at the
+    row's own `basis_as_of`, read via `GET /research/candles?symbol=AAPL&timeframe=1d` -- the SAME
+    route the chart itself reads -- mirroring `test_aapl_row_history_cross_checks_against_get_
+    candles`'s single-source-of-truth proof for the two history fields, applied to the new one."""
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
+    basis_bar = max(filtered, key=lambda b: b["ts"])
+    assert row["reference_close"] == basis_bar["close"]
+
+
+def test_reference_close_stays_byte_identical_on_a_recompute_under_identical_pins(ctx, tmp_path):
+    """TC-4: mirrors `test_history_fields_stay_byte_identical_on_a_recompute_under_identical_pins`
+    for `reference_close` specifically -- a screen recorded once, then a FRESH computation under
+    identical pins, is refused a second write, and the content already on disk (read back via
+    `list()`) is byte-identical to the second (unrecorded) computation's `reference_close` on every
+    ranked row."""
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
+    assert aapl_row["reference_close"] == next(
+        r for r in second_screen["rows"] if r["symbol"] == "AAPL"
+    )["reference_close"]
+
+
+def test_a_legacy_row_recorded_without_reference_close_serves_it_absent_never_backfilled(tmp_path):
+    """TC-5: the exact shape every screen snapshot recorded BEFORE this iteration has -- ranked rows
+    that OMIT `reference_close` entirely (never merely present-as-`null`) -- mirrors the basis/
+    history legacy-row precedents for the new field. `_record`'s own default row carries no such key
+    at all, so this is true by construction; this test pins that contract so a future change cannot
+    silently start defaulting or backfilling legacy rows on read."""
+    store = ScreenStore(tmp_path / "screen")
+    _record(store)  # `_record`'s own default row carries no reference_close key at all
+
+    records, errors = store.list()
+    assert errors == []
+    row = records[0]["rows"][0]
+    assert "reference_close" not in row
+
+
 # ==================================================================================================
 # screen ?id= read (goal-desk-iter-16, J-12) -- individual addressability, including an EARLIER
 # same-`screen_date` recording that `?date=` (which always resolves `matching[-1]`) can never reach.
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index a786acd..c0d8c3e 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -1,7 +1,7 @@
 """era-desk-iter-6 (J-05) source-introspection guard tests -- the ``test_copy_discipline.py``
 pattern (read a frontend .tsx file as TEXT, assert on substrings; no browser, no runtime).
 
-Two guards, each proving something about the frontend a backend-only test suite otherwise could
+Three guards, each proving something about the frontend a backend-only test suite otherwise could
 not see:
 
   (a) TC-5 -- ``apps/frontend/app/desk/page.tsx`` never references any of the structure-side
@@ -13,6 +13,10 @@ not see:
       ``J-05-PREFILL-START``/``J-05-PREFILL-END`` markers in ``structure/page.tsx``) calls the
       SAME ``handleLoad`` the manual Load button already calls, and introduces no second
       fetch/compute path.
+  (c) goal-desk-iter-17 (J-13) TC-8 -- ``apps/frontend/app/desk/page.tsx`` never derives a price
+      value via arithmetic on ``row.distance_bps``/``row.price_low``/``row.price_high`` -- the new
+      ``band`` column/tooltip line renders ``row.reference_close`` beside the row's own
+      ``price_low``/``price_high``, never a value recomputed from them client-side.
 
 A guard that can never fail proves nothing -- each carries a seeded counter-test proving the
 detection logic itself actually catches a violation (the ``test_copy_discipline.py``
@@ -21,6 +25,7 @@ seeded-violation precedent)."""
 from __future__ import annotations
 
 import pathlib
+import re
 
 _FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
 _DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"
@@ -117,3 +122,34 @@ def test_structure_prefill_guard_can_fail_on_a_seeded_violation():
         "// J-05-PREFILL-END\n"
     )
     assert "handleLoad(" not in seeded_block_missing_handle_load
+
+
+# goal-desk-iter-17 (J-13) TC-8: no expression in the desk page may derive a NEW price value via
+# arithmetic on `distance_bps`/`price_low`/`price_high` -- the honest disclosure this journey ships
+# (`row.reference_close`, `row.price_low`-`row.price_high`) is a verbatim render of already-served
+# values, never a client-side recomputation of the very number `reference_close` exists to disclose
+# instead of forcing an operator (or agent) to invert `distance_bps` against a band edge.
+_PRICE_ARITHMETIC_FIELDS = r"row\.(distance_bps|price_low|price_high)"
+_PRICE_ARITHMETIC_PATTERN = re.compile(
+    rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
+)
+
+
+def test_desk_page_never_derives_a_price_via_arithmetic_on_distance_or_band_edges():
+    """TC-8: scans `apps/frontend/app/desk/page.tsx`'s source for any expression combining
+    `row.distance_bps`/`row.price_low`/`row.price_high` with an arithmetic operator. The new
+    `band` column/tooltip line (goal-desk-iter-17, J-13) renders `row.reference_close` beside
+    `row.price_low`/`row.price_high` as two side-by-side values, never a derived third one."""
+    source = _DESK_PAGE.read_text()
+    hits = _PRICE_ARITHMETIC_PATTERN.findall(source)
+    assert not hits, (
+        f"apps/frontend/app/desk/page.tsx derives a price value via arithmetic on distance_bps/"
+        f"price_low/price_high ({hits}) -- the page must render only what "
+        "GET /research/desk/screen already served, never recompute a price client-side"
+    )
+
+
+def test_desk_page_price_arithmetic_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail -- a lint that cannot fail proves nothing."""
+    seeded_source = "const implied = row.price_high - row.reference_close;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_source) is not None
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index 9dcba63..6d57d73 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -466,6 +466,57 @@ async def test_get_endpoint_desk_screen_id_query_proxies_verbatim(mcp_env, backe
     assert result.content[0].text.encode("utf-8") == rest.content, "desk screen id-nonmatch not byte-identical"
 
 
+@pytest.mark.anyio
+async def test_desk_screen_reference_close_field_proxies_verbatim(mcp_env, backend_paths):
+    """goal-desk-iter-17 (J-13) TC-10: `reference_close` -- `desk_screen.py`'s new ranked-row field
+    -- is proxied byte-identical through both the `desk_screen` tool (no-arg) and `get_endpoint`'s
+    existing `/research/` allowlist prefix (`?date=`), with ZERO MCP code change -- the same proxy
+    contract every prior `desk_screen` row-field addition (basis/history) already covers
+    automatically. Seeded under its own distinct date so this test passes standalone."""
+    screen_dir = Path(backend_paths["TAPEOLOGY_DESK_SCREEN_DIR"])
+    ScreenStore(screen_dir).record(
+        screen_date="2026-07-29",
+        as_of="2026-07-29T21:00:00Z",
+        universe_snapshot_id="universe-2026-07-25-817cc184bbb3",
+        config_fingerprint=CONFIG.config_fingerprint(),
+        bar_store_signature="mcp-test-reference-close-signature",
+        rows=[
+            {
+                "symbol": "AMZN",
+                "side": "resistance",
+                "band_class": "A",
+                "distance_bps": 5.0,
+                "band_score": 4.2,
+                "price_low": 200.0,
+                "price_high": 202.0,
+                "coverage": {"1d": {"has_bars": True, "latest_window_end_utc": "2026-07-29T00:00:00Z"}},
+                "tick_evidence": True,
+                "reference_close": 199.9,
+            }
+        ],
+        skipped=[],
+    )
+
+    result = await call_tool("desk_screen", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/screen", timeout=5.0)
+    assert rest.status_code == 200
+    assert rest.json()["latest"]["rows"][0]["reference_close"] == 199.9
+    assert result.isError is False
+    assert result.content[0].text.encode("utf-8") == rest.content, (
+        "reference_close not byte-identical via the desk_screen tool"
+    )
+
+    date_path = "/research/desk/screen?date=2026-07-29"
+    result = await call_tool("get_endpoint", {"path": date_path})
+    rest = httpx.get(f"{mcp_env}{date_path}", timeout=5.0)
+    assert rest.status_code == 200
+    assert rest.json()["screen"]["rows"][0]["reference_close"] == 199.9
+    assert result.isError is False
+    assert result.content[0].text.encode("utf-8") == rest.content, (
+        "reference_close not byte-identical via get_endpoint"
+    )
+
+
 @pytest.mark.anyio
 async def test_datasets_tool_byte_identical_on_a_non_empty_live_list(mcp_env, backend_paths):
     """J-02 flips ``datasets`` from honest 404 to live data with ZERO MCP code changes: after
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index ee51f18..7c1ecda 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -104,6 +104,14 @@ import { fmt } from "@/lib/format";
 // `integrity_errors` carries an entry — the Universe ledger has no existing frontend section to
 // extend (never fetched/rendered on this page today, unlike the plan's premise; see the dev
 // handoff's Known Issues).
+//
+// goal-desk-iter-17 (J-13): a new `band` column on the ranked-rows table (`DeskRow`/
+// `DeskRowsTable`), plus one more line on the row's composite drill-in tooltip — the row's own
+// `reference_close` (the exact daily close its band selection and `distance_bps` were measured
+// against) rendered beside the row's already-recorded `price_low`–`price_high` band range, so
+// "the price is inside the wall" is a fact visible on screen instead of arithmetic recovered by
+// inverting `distance_bps` against a band edge. Read-only render, zero new endpoint, zero new
+// control — `reference_close` rides the already-fetched `GET /research/desk/screen` response.
 
 const NUMERIC_CELL = "px-2 py-1.5 text-right font-mono text-xs text-slate-200 whitespace-nowrap";
 const HEADER_CELL = "px-2 py-1 text-right text-[11px] font-medium text-slate-500";
@@ -245,6 +253,10 @@ function hasNoCoverageAtAll(coverage: Record<string, { has_bars: boolean }>): bo
 // `row.history_sessions` plus `row.history_start` untruncated (the visible "history" cell below
 // shows only the date portion, the SAME rounded-display/full-precision-on-hover split as basis) --
 // a legacy row (recorded before this iteration) has both keys absent, `== null` catches both.
+// era-desk-iter-17 (J-13): the SAME tooltip also carries the row's full-precision `reference_close`
+// beside its own `price_low`/`price_high` band range (the visible "band" cell below shows the
+// rounded values, the SAME split as distance/score/basis/history) -- a legacy row (recorded before
+// this iteration) has the key absent, `== null` catches both `undefined` and `null`.
 function deskRowDrillInTitle(row: DeskScreenRow): string {
   const coverageLines = Object.entries(row.coverage)
     .map(([timeframe, tf]) => `${timeframe} window last requested: ${tf.latest_window_end_utc ?? "never"}`)
@@ -257,7 +269,15 @@ function deskRowDrillInTitle(row: DeskScreenRow): string {
     row.history_sessions == null || row.history_start == null
       ? "history not recorded in this snapshot"
       : `history ${row.history_sessions} sessions from ${row.history_start}`;
-  return `distance ${row.distance_bps} bps · score ${row.band_score} · ${basisLine} · ${historyLine}${
+  // The band RANGE is recorded on every ranked row of every snapshot ever written (including every
+  // pre-iter-17 one), so it renders unconditionally -- only the CLOSE segment falls back when a
+  // legacy row has no `reference_close` key (goal.md J-13: "/desk renders their rows with their OWN
+  // recorded band range plus the honest 'close not recorded in this snapshot' state").
+  const bandLine =
+    row.reference_close == null
+      ? `band ${row.price_low}–${row.price_high} · close not recorded in this snapshot`
+      : `band ${row.price_low}–${row.price_high} · close ${row.reference_close}`;
+  return `distance ${row.distance_bps} bps · score ${row.band_score} · ${basisLine} · ${historyLine} · ${bandLine}${
     coverageLines ? ` · ${coverageLines}` : ""
   }`;
 }
@@ -276,8 +296,8 @@ function deskSkipDrillInTitle(skip: DeskScreenSkip): string {
 // DISPLAYED to two decimals (a `0.33523150389608725 bps` cell defeated the scanability the
 // briefing exists for — audit F3); the full-precision value is not lost — it is reachable via the
 // row's own drill-in anchor's composite `title` (`deskRowDrillInTitle` above, audit F2 fix), never
-// a per-cell `title` (iter-7 audit F1: this comment used to claim the opposite). The basis and
-// history columns follow the SAME split: a rounded, date-only display with the full-precision
+// a per-cell `title` (iter-7 audit F1: this comment used to claim the opposite). The basis,
+// history, and band columns follow the SAME split: a rounded display with the full-precision
 // value reachable only via that same composite tooltip. The band-class chip carries the "nearest
 // same-class band" caption
 // (assumptions.md iter-4 entry 1 — `_select_best_band` itself stays byte-unchanged; this copy
@@ -350,6 +370,21 @@ function DeskRow({ row, asOf }: { row: DeskScreenRow; asOf: string }) {
           ? "history not recorded in this snapshot"
           : `history ${row.history_sessions} sessions · from ${row.history_start.slice(0, 10)}`}
       </td>
+      {/* era-desk-iter-17 (J-13): the exact price the row's band was measured from, beside its own
+          already-recorded price_low-price_high band range -- "the price is inside the wall"
+          becomes a legible fact instead of arithmetic recovered by inverting distance_bps against
+          a band edge (full precision -- the untruncated reference_close/price_low/price_high --
+          lives in the row anchor's own composite title above, NEVER a per-cell title here, the
+          same F2 lesson the basis/history columns already apply). `== null` catches a legacy
+          row's ENTIRELY ABSENT key (`undefined`), not just an explicit `null` -- and only the
+          CLOSE segment falls back: `price_low`/`price_high` are recorded on every ranked row of
+          every snapshot ever written, so the range itself always renders (goal-desk-iter-17 audit
+          F1). */}
+      <td className={LABEL_CELL} data-testid="desk-row-band">
+        {row.reference_close == null
+          ? `band ${fmt(row.price_low)}–${fmt(row.price_high)} · close not recorded in this snapshot`
+          : `band ${fmt(row.price_low)}–${fmt(row.price_high)} · close ${fmt(row.reference_close)}`}
+      </td>
     </tr>
   );
 }
@@ -379,6 +414,7 @@ function DeskRowsTable({ rows, asOf }: { rows: DeskScreenRow[]; asOf: string })
             <th className={HEADER_CELL_LEFT}>tick evidence</th>
             <th className={HEADER_CELL_LEFT}>basis</th>
             <th className={HEADER_CELL_LEFT}>history</th>
+            <th className={HEADER_CELL_LEFT}>band</th>
           </tr>
         </thead>
         <tbody>
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 80471cc..e970b40 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -804,6 +804,14 @@ export type EdgeReportPayload = EdgeReportResponse | EdgeReportNotComputed;
 // non-null on a NEWLY computed ranked row, entirely ABSENT (not `null`) on a row recorded before
 // this iteration -- callers must check `row.history_sessions == null` (loose equality), same as
 // the basis fields above.
+// era-desk-iter-17 (J-13) -- reference-close disclosure: the exact daily close the row's band
+// selection and `distance_bps` were measured against, copied verbatim from the SAME `close` local
+// `desk_screen.py` already resolves for the basis/history fields above -- zero new backend read.
+// Renders beside the row's own already-typed `price_low`/`price_high` band range so "the price is
+// inside the wall" is a fact on screen instead of arithmetic inverted out of `distance_bps`. Same
+// presence contract as basis/history: always non-null on a NEWLY computed ranked row, entirely
+// ABSENT (not `null`) on a row recorded before this iteration -- callers must check
+// `row.reference_close == null` (loose equality).
 export interface DeskScreenRow {
   symbol: string;
   side: "support" | "resistance";
@@ -818,6 +826,7 @@ export interface DeskScreenRow {
   basis_age_days: number | null;
   history_sessions: number | null;
   history_start: string | null;
+  reference_close?: number | null;
 }
 
 // A member the screen walked but could not rank -- two honest, distinct reasons, never conflated:
```
