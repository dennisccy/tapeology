# Iteration diff (bounded)

Files changed: 6. Shown in full: 6.

```diff
diff --git a/apps/backend/app/research/desk_topup_compute.py b/apps/backend/app/research/desk_topup_compute.py
index 7941036..bfe6f4a 100644
--- a/apps/backend/app/research/desk_topup_compute.py
+++ b/apps/backend/app/research/desk_topup_compute.py
@@ -79,7 +79,33 @@ thing as a per-pair ``outcome: "failed"`` (already caught inside ``_run_one_pair
 whatever outcomes were published before the crash (a local ``collected`` list, independent of the
 shared ``self._snapshot`` to avoid any race with a superseding job); the CLI path has no cancel
 signal and normally only ever terminates ``"done"``, so an uncaught crash BEFORE its own writer
-call is the correct interrupted-run case — zero record, never a bug to guard against."""
+call is the correct interrupted-run case — zero record, never a bug to guard against.
+
+**goal-desk-iter-32, J-19 — the date each pair's frozen history actually reaches AFTER the run.**
+Every recorded run's own artifact (``requested_window``/``store_frozen_from``/
+``store_frozen_through``) describes the store's content BEFORE that pair's own fetch attempt —
+nothing anywhere records what the pair's frozen history reaches once the attempt ENDS. ``run_topup``
+closes that gap with ONE additive field, ``store_frozen_through_after``: immediately after
+``_run_one_pair`` returns for a pair, a SECOND, independent call to the SAME pure accessor,
+``_pair_window(bar_store, symbol, timeframe)`` (never a new accessor, never ``bar_index``'s
+``window_end_utc``, never arithmetic over bars), reads that pair's newest frozen bar as it stands
+right now and the value is copied onto the outcome entry verbatim. For a ``"reused"``/``"unchanged"``/
+``"failed"`` pair nothing was written to the store between the two calls, so the two reads always
+agree byte-for-byte with the pair's own pre-fetch ``store_frozen_through``; for a ``"fetched"`` pair
+the store gained a brand new series between the two calls, so the second read genuinely differs
+(later) from the first. The value is ``null`` only when the pair holds no frozen bars at all (never
+fetched anything, or fetched and failed) — exactly the shape ``store_frozen_through`` already uses.
+This is a strictly LOCAL, per-pair, attempt-time OBSERVATION — it states nothing about current
+coverage or freshness generally (that stays ``desk_coverage.get_desk_coverage`` over ``bar_index``,
+untouched), creates no second coverage path, and adds no new accessor, fetch, store, route, Config
+field, or MCP tool. ``_run_one_pair``'s own two-value return contract
+(``(symbol, timeframe, bar_store, bar_index, registry) -> (outcome, str | None)``) is UNCHANGED, so
+every existing test that monkeypatches it wholesale keeps working unmodified — the new field is
+computed entirely inside ``run_topup`` itself, one level above the fake boundary. The append-only
+writer, ``desk_topup_log.record_topup_run``, needs no change (a pure, schema-agnostic passthrough):
+a run recorded BEFORE this field existed keeps its outcome entries exactly as recorded, served
+verbatim, and ``/desk`` renders their absence as the honest ``"library reach not recorded in this
+run"`` fallback — never a computed or backfilled value."""
 
 from __future__ import annotations
 
@@ -286,7 +312,11 @@ def run_topup(
     ``"window_basis"`` — that pair's own pre-fetch provenance, captured via ``_pair_window``
     IMMEDIATELY before ``_run_one_pair`` runs (so it reflects the store's content BEFORE this run's
     fetch, exactly as the Data Contract requires) and independent of whatever ``_run_one_pair``
-    itself is (real or a test fake) — see the module docstring's J-17 section.
+    itself is (real or a test fake) — see the module docstring's J-17 section; plus (goal-desk-
+    iter-32, J-19) ``"store_frozen_through_after"`` — that SAME pair's own newest frozen bar AFTER
+    the attempt, read via a SECOND, independent ``_pair_window`` call immediately AFTER
+    ``_run_one_pair`` returns, ``null`` only when the pair holds nothing at all — see the module
+    docstring's J-19 section.
 
     ``progress``, if given, is called after EACH pair with the outcome dict just appended (so a
     caller can publish incremental state). ``should_abort``, if given and it returns ``True``
@@ -301,6 +331,15 @@ def run_topup(
                 return outcomes
             window = _pair_window(bar_store, symbol, timeframe)
             outcome, detail = _run_one_pair(symbol, timeframe, bar_store, bar_index, registry)
+            # goal-desk-iter-32 (J-19): a SECOND, independent call to the SAME pure accessor,
+            # immediately after the attempt, captures what this pair's frozen history actually
+            # reaches AFTER the walk -- never bar_index's window_end_utc (what the run ASKED for),
+            # never a new accessor, never arithmetic over bars. For "reused"/"unchanged"/"failed"
+            # pairs nothing was written between the two calls, so the two reads always agree; for
+            # a "fetched" pair the store gained a new series, so this second read genuinely
+            # reflects it. `null` only when the pair holds nothing at all (see the module
+            # docstring's J-19 section).
+            window_after = _pair_window(bar_store, symbol, timeframe)
             entry = {
                 "symbol": symbol,
                 "timeframe": timeframe,
@@ -310,6 +349,7 @@ def run_topup(
                 "store_frozen_from": window["store_frozen_from"],
                 "store_frozen_through": window["store_frozen_through"],
                 "window_basis": window["window_basis"],
+                "store_frozen_through_after": window_after["store_frozen_through"],
             }
             outcomes.append(entry)
             if progress is not None:
diff --git a/apps/backend/tests/test_desk_topup_compute.py b/apps/backend/tests/test_desk_topup_compute.py
index df25dc5..9616e07 100644
--- a/apps/backend/tests/test_desk_topup_compute.py
+++ b/apps/backend/tests/test_desk_topup_compute.py
@@ -592,6 +592,16 @@ def test_a_failing_pair_reports_failed_with_the_detail_preserved_and_the_run_con
 # pre-existing assertion in this file -- TC-7 (all-reused second run) and TC-8 (resumability), the
 # two the spec names explicitly, pass untouched. See `docs/handoffs/goal-desk-iter-26-dev.md`.
 # ==================================================================================================
+#
+# goal-desk-iter-32 (J-19) EXTENDS THE SAME CARVE-OUT BY ONE MORE KEY: `run_topup` now adds
+# `store_frozen_through_after` to every per-pair outcome entry (the date each pair's frozen history
+# actually reaches AFTER the attempt), for the IDENTICAL structural reason -- the byte-identity
+# assertion between `run_topup`'s own return value and the persisted record forces every new field
+# to originate inside `run_topup`/`_run_one_pair` itself, so a REAL run's outcome entries now carry
+# nine keys, not eight. The same single existing assertion (`outcome.keys() == {...}`, below) is
+# extended again, in place, to the nine-key set -- still an exact key-SET equality, so cross-path
+# schema drift still fails it. No OTHER pre-existing assertion in this file is touched.
+# ==================================================================================================
 
 
 def _epoch_days_ago(days: float) -> float:
@@ -769,6 +779,127 @@ def test_a_vendor_answer_holding_only_already_frozen_bars_records_unchanged_not_
     assert same_after == same_before
 
 
+# ==================================================================================================
+# goal-desk-iter-32 (J-19) -- `store_frozen_through_after`: the date each pair's frozen history
+# actually reaches AFTER the attempt, across all four outcome branches plus the holds-nothing/null
+# case. Fixture-scoped, no network -- the SAME `_plant_bar_series`/`_inject_adapter` seams the J-17
+# section above uses.
+# ==================================================================================================
+
+
+def test_store_frozen_through_after_equals_the_newest_bar_after_a_fetched_pair(manager_env):
+    """TC-1 (goal.md J-19): a pair whose fetch genuinely appends new bars records
+    `store_frozen_through_after` byte-identical to the newest bar `BarStore.merged_bars` reports
+    for that pair AFTER the walk -- later than its own pre-fetch `store_frozen_through`."""
+    _universe_store, bar_store, bar_index, registry, _topup_run_store = manager_env
+    deep_epoch = _epoch_days_ago(desk_topup_compute._TOPUP_LOOKBACK_DAYS + 70)
+    newest_epoch = _epoch_days_ago(5)
+    from app.providers.adapters.base import RawBar
+
+    _plant_bar_series(
+        bar_store, symbol="ADV", timeframe="1d", feed=registry.config.historical_feed,
+        bars=[
+            RawBar("ADV", "1d", deep_epoch, 10.0, 11.0, 9.0, 10.5, 500),
+            RawBar("ADV", "1d", newest_epoch, 20.0, 21.0, 19.0, 20.5, 700),
+        ],
+    )
+    fresh_epoch = _epoch_days_ago(1)  # strictly newer than the planted `newest_epoch` (5 days ago)
+    _inject_adapter(
+        bars=(
+            RawBar("ADV", "1d", newest_epoch, 20.0, 21.0, 19.0, 20.5, 700),
+            RawBar("ADV", "1d", fresh_epoch, 25.0, 26.0, 24.0, 25.5, 800),
+        )
+    )
+
+    outcomes = run_topup(["ADV"], bar_store, bar_index, registry)
+
+    entry = next(o for o in outcomes if o["symbol"] == "ADV" and o["timeframe"] == "1d")
+    assert entry["outcome"] == "fetched"
+    after_bars = bar_store.merged_bars("ADV", "1d")
+    expected_after = desk_topup_compute._iso_bar_epoch(after_bars[-1].epoch)
+    assert entry["store_frozen_through_after"] == expected_after
+    assert entry["store_frozen_through_after"] > entry["store_frozen_through"]
+
+
+def test_store_frozen_through_after_equals_the_pre_fetch_value_for_an_unchanged_pair(manager_env):
+    """TC-2 (goal.md J-19): a pair whose fetch is classified `"unchanged"` (a real vendor call
+    returned only content already frozen) records `store_frozen_through_after` byte-identical to
+    its own pre-fetch `store_frozen_through` -- nothing was written to the store."""
+    _universe_store, bar_store, bar_index, registry, _topup_run_store = manager_env
+    already_frozen = _bars()
+    _plant_bar_series(
+        bar_store, symbol="SAME2", timeframe="1d", feed=registry.config.historical_feed,
+        bars=already_frozen,
+    )
+    _inject_adapter(bars=already_frozen)
+
+    outcomes = run_topup(["SAME2"], bar_store, bar_index, registry)
+
+    entry = next(o for o in outcomes if o["symbol"] == "SAME2" and o["timeframe"] == "1d")
+    assert entry["outcome"] == "unchanged"
+    assert entry["store_frozen_through_after"] == entry["store_frozen_through"]
+    assert entry["store_frozen_through_after"] is not None
+
+
+def test_store_frozen_through_after_equals_the_pre_fetch_value_for_a_reused_pair(manager_env):
+    """TC-4 (goal.md J-19): a store-first exact-key hit (`"reused"`, zero vendor calls) records
+    `store_frozen_through_after` byte-identical to its own pre-fetch `store_frozen_through`."""
+    _universe_store, bar_store, bar_index, registry, _topup_run_store = manager_env
+    adapter = _inject_adapter(bars=_bars())
+    first = run_topup(["RSD"], bar_store, bar_index, registry)
+    assert {o["outcome"] for o in first} == {"fetched"}
+    calls_after_first = len(adapter.fetch_bars_calls)
+
+    second = run_topup(["RSD"], bar_store, bar_index, registry)
+
+    entry = next(o for o in second if o["symbol"] == "RSD" and o["timeframe"] == "1d")
+    assert entry["outcome"] == "reused"
+    assert len(adapter.fetch_bars_calls) == calls_after_first  # zero new vendor calls
+    assert entry["store_frozen_through_after"] == entry["store_frozen_through"]
+    assert entry["store_frozen_through_after"] is not None
+
+
+def test_store_frozen_through_after_equals_the_pre_fetch_value_for_a_failed_pair_holding_bars(
+    manager_env,
+):
+    """TC-3 (goal.md J-19): a pair whose fetch is classified `"failed"` -- but which already held
+    frozen bars before the attempt -- records `store_frozen_through_after` byte-identical to its
+    own pre-fetch `store_frozen_through`, never `null` (the pair still holds what it held before)."""
+    _universe_store, bar_store, bar_index, registry, _topup_run_store = manager_env
+    held_epoch = _epoch_days_ago(3)
+    from app.providers.adapters.base import RawBar
+
+    _plant_bar_series(
+        bar_store, symbol="FAILHOLD", timeframe="1d", feed=registry.config.historical_feed,
+        bars=[RawBar("FAILHOLD", "1d", held_epoch, 10.0, 11.0, 9.0, 10.5, 500)],
+    )
+    _inject_adapter(bars_raise=NoDataForWindow("no data for that window"))
+
+    outcomes = run_topup(["FAILHOLD"], bar_store, bar_index, registry)
+
+    entry = next(o for o in outcomes if o["symbol"] == "FAILHOLD" and o["timeframe"] == "1d")
+    assert entry["outcome"] == "failed"
+    assert entry["store_frozen_through"] is not None
+    assert entry["store_frozen_through_after"] == entry["store_frozen_through"]
+
+
+def test_store_frozen_through_after_is_null_when_the_pair_holds_nothing_and_the_fetch_fails(
+    manager_env,
+):
+    """TC-5 (goal.md J-19): a pair that holds NO frozen bars before the run, and whose fetch does
+    not result in any bars being recorded (`"failed"`), records `store_frozen_through_after` as
+    `null` -- exactly the shape `store_frozen_through` already uses for the same case."""
+    _universe_store, bar_store, bar_index, registry, _topup_run_store = manager_env
+    _inject_adapter(bars_raise=NoDataForWindow("no data for that window"))
+
+    outcomes = run_topup(["NOTHING"], bar_store, bar_index, registry)
+
+    entry = next(o for o in outcomes if o["symbol"] == "NOTHING" and o["timeframe"] == "1d")
+    assert entry["outcome"] == "failed"
+    assert entry["store_frozen_through"] is None
+    assert entry["store_frozen_through_after"] is None
+
+
 # ==================================================================================================
 # Routes -- GET-never-computes, single-flight/cancel through HTTP, idle-cancel 409 (TC-15).
 # ==================================================================================================
@@ -1084,15 +1215,19 @@ def test_cli_triggered_run_persists_a_record_with_the_identical_shape_as_a_manag
     assert {o["outcome"] for o in record["outcomes"]} == {"fetched"}
     for outcome in record["outcomes"]:
         # goal-desk-iter-26 (J-17), the ONE reviewer-sanctioned carve-out to this iteration's
-        # "existing assertions pass unmodified" rule: this pin is a mirror of the SHARED writer's
-        # per-pair schema, extended -- not relaxed -- with the four Data-Contract fields every path
-        # now carries. It stays an exact key-SET equality, so cross-path schema drift (the property
-        # this test's own name claims) still fails it. See the section header below and
-        # `docs/handoffs/goal-desk-iter-26-dev.md` for why no implementation of the mandated
-        # contract can keep a real run's outcome entries at four keys.
+        # "existing assertions pass unmodified" rule -- EXTENDED AGAIN by goal-desk-iter-32 (J-19)
+        # for the identical structural reason: this pin is a mirror of the SHARED writer's per-pair
+        # schema, extended -- not relaxed -- with the Data-Contract fields every path now carries
+        # (four from J-17, plus `store_frozen_through_after` from J-19). It stays an exact key-SET
+        # equality, so cross-path schema drift (the property this test's own name claims) still
+        # fails it. See the section header above `_epoch_days_ago` and
+        # `docs/handoffs/goal-desk-iter-26-dev.md` / `docs/handoffs/goal-desk-iter-32-dev.md` for
+        # why no implementation of the mandated contract can keep a real run's outcome entries at a
+        # smaller key count.
         assert outcome.keys() == {
             "symbol", "timeframe", "outcome", "detail",
             "requested_window", "store_frozen_from", "store_frozen_through", "window_basis",
+            "store_frozen_through_after",
         }
 
 
diff --git a/apps/backend/tests/test_desk_topup_log.py b/apps/backend/tests/test_desk_topup_log.py
index cf494a3..dcb5b1c 100644
--- a/apps/backend/tests/test_desk_topup_log.py
+++ b/apps/backend/tests/test_desk_topup_log.py
@@ -292,3 +292,50 @@ def test_a_legacy_pre_iter26_run_record_round_trips_without_the_new_fields(tmp_p
     records, errors = store.list()
     assert errors == []
     assert records[0]["outcomes"] == legacy_outcomes
+
+
+# goal-desk-iter-32 (J-19): one more additive field, `store_frozen_through_after` -- the SAME pure
+# passthrough contract, proven the same way: a fresh record round-trips the new field verbatim, and
+# a legacy record (pre-iter-32, or even pre-iter-26) never gains it at read time.
+
+J19_OUTCOMES = [
+    {
+        "symbol": "AAA", "timeframe": "1d", "outcome": "fetched", "detail": None,
+        "requested_window": {"start": "2024-07-30T00:00:00Z", "end": "2026-07-31T00:00:00Z"},
+        "store_frozen_from": None, "store_frozen_through": None, "window_basis": "full_lookback",
+        "store_frozen_through_after": "2026-07-30T00:00:00.000000Z",
+    },
+    {
+        "symbol": "BBB", "timeframe": "1d", "outcome": "reused", "detail": None,
+        "requested_window": {"start": "2024-07-31T00:00:00Z", "end": "2026-07-31T00:00:00Z"},
+        "store_frozen_from": "2024-06-01T00:00:00.000000Z",
+        "store_frozen_through": "2026-07-25T00:00:00.000000Z", "window_basis": "tail",
+        "store_frozen_through_after": "2026-07-25T00:00:00.000000Z",
+    },
+]
+
+
+def test_record_and_list_round_trip_the_new_j19_store_frozen_through_after_field_verbatim(tmp_path):
+    store = TopupRunStore(tmp_path / "topup_runs")
+    meta = _record_sample(store, outcomes=J19_OUTCOMES)
+
+    assert meta["outcomes"] == J19_OUTCOMES
+    records, errors = store.list()
+    assert errors == []
+    assert records[0]["outcomes"] == J19_OUTCOMES
+
+
+def test_a_legacy_pre_iter32_run_record_round_trips_without_store_frozen_through_after(tmp_path):
+    """A run recorded BEFORE this iteration's code shipped (including a pre-iter-26 run, which
+    lacks ALL five new fields) never gains `store_frozen_through_after` at read time."""
+    store = TopupRunStore(tmp_path / "topup_runs")
+    legacy_outcomes = [{"symbol": "AAA", "timeframe": "1h", "outcome": "fetched", "detail": None}]
+    meta = _record_sample(store, outcomes=legacy_outcomes)
+
+    assert meta["outcomes"] == legacy_outcomes
+    for outcome in meta["outcomes"]:
+        assert "store_frozen_through_after" not in outcome
+
+    records, errors = store.list()
+    assert errors == []
+    assert records[0]["outcomes"] == legacy_outcomes
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 3bcdb64..a451aa1 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -864,6 +864,45 @@ function topupWindowBasisCounts(
   };
 }
 
+// goal-desk-iter-32 (J-19) -- the actual date each pair's frozen history reaches AFTER the run,
+// distinct from `store_frozen_through` (this pair's PRE-fetch value, never rendered standalone on
+// this page) and from `window_basis`'s tail/full_lookback tally above: an EXTREME (the newest
+// `store_frozen_through_after` across the run's own pairs) plus how many pairs reach it, plus a
+// short list of the pairs whose own recorded reach date is earlier than that newest date (or
+// `null`) -- a plain read of the served payload, nothing derived from bars (the
+// `topupWindowBasisCounts` precedent). `null` when ANY outcome in the run lacks
+// `store_frozen_through_after` (a legacy run, pre-iter-32) -- rendered as the honest
+// LIBRARY_REACH_NOT_RECORDED fallback, never computed or backfilled.
+const LIBRARY_REACH_NOT_RECORDED = "library reach not recorded in this run";
+
+function topupLibraryReach(
+  outcomes: DeskTopupOutcome[],
+): {
+  newestDate: string | null;
+  newestCount: number;
+  earlier: { symbol: string; timeframe: string; date: string | null }[];
+} | null {
+  if (outcomes.some((o) => o.store_frozen_through_after === undefined)) return null;
+  const dates = outcomes
+    .map((o) => o.store_frozen_through_after)
+    .filter((d): d is string => typeof d === "string");
+  if (dates.length === 0) {
+    // Every pair in this run holds no frozen bars at all -- an honest all-null run, never a
+    // computed extreme over an empty set.
+    return { newestDate: null, newestCount: 0, earlier: [] };
+  }
+  const newestDate = dates.reduce((max, d) => (d > max ? d : max), dates[0]);
+  const newestCount = outcomes.filter((o) => o.store_frozen_through_after === newestDate).length;
+  const earlier = outcomes
+    .filter((o) => o.store_frozen_through_after !== newestDate)
+    .map((o) => ({
+      symbol: o.symbol,
+      timeframe: o.timeframe,
+      date: o.store_frozen_through_after ?? null,
+    }));
+  return { newestDate, newestCount, earlier };
+}
+
 function TopupRunRow({ meta }: { meta: DeskTopupRunMeta }) {
   return (
     <tr data-testid="desk-topup-run-row" className="border-b border-slate-800/60 last:border-b-0">
@@ -918,6 +957,7 @@ function TopupRunsTable({ runs }: { runs: DeskTopupRunMeta[] }) {
 function LatestTopupRunDetail({ run }: { run: DeskTopupRun }) {
   const counts = topupOutcomeCounts(run.outcomes);
   const windowBasisCounts = topupWindowBasisCounts(run.outcomes);
+  const libraryReach = topupLibraryReach(run.outcomes);
   const unreached = run.pairs_total - run.pairs_attempted;
   const failedOutcomes = run.outcomes.filter((o) => o.outcome === "failed");
   return (
@@ -950,6 +990,33 @@ function LatestTopupRunDetail({ run }: { run: DeskTopupRun }) {
             `tail window · ${windowBasisCounts.full_lookback} pair` +
             `${windowBasisCounts.full_lookback === 1 ? "" : "s"} asked for the full lookback window`}
       </div>
+      <div data-testid="desk-topup-run-latest-reach" className="text-xs text-slate-400">
+        {libraryReach === null || libraryReach.newestDate === null
+          ? LIBRARY_REACH_NOT_RECORDED
+          : `newest recorded reach ${libraryReach.newestDate.slice(0, 10)} · ` +
+            `${libraryReach.newestCount} pair${libraryReach.newestCount === 1 ? "" : "s"} reach it`}
+      </div>
+      {libraryReach !== null && libraryReach.earlier.length > 0 && (
+        <div data-testid="desk-topup-run-latest-reach-earlier">
+          <h4 className="mb-1 text-[11px] font-medium text-slate-500">
+            Pairs recorded earlier ({libraryReach.earlier.length})
+          </h4>
+          <ul className="space-y-1">
+            {libraryReach.earlier.map((item, index) => (
+              <li
+                key={`${item.symbol}-${item.timeframe}-${index}`}
+                data-testid="desk-topup-run-latest-reach-earlier-row"
+                className="text-xs text-slate-400"
+              >
+                <span className="font-mono text-slate-300">
+                  {item.symbol} {item.timeframe}
+                </span>{" "}
+                — {item.date ? item.date.slice(0, 10) : "no bars recorded"}
+              </li>
+            ))}
+          </ul>
+        </div>
+      )}
       {failedOutcomes.length > 0 && (
         <div data-testid="desk-topup-run-latest-failed">
           <h4 className="mb-1 text-[11px] font-medium text-slate-500">
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index e534556..2ee6090 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -956,6 +956,10 @@ export interface DeskTopupOutcome {
   store_frozen_from?: string | null;
   store_frozen_through?: string | null;
   window_basis?: "tail" | "full_lookback";
+  // goal-desk-iter-32 (J-19) -- this pair's own newest frozen bar AFTER the attempt (never
+  // `bar_index`'s `window_end_utc`); optional/additive, absent on a run recorded before this
+  // iteration's code shipped (the `store_frozen_through`-absence legacy contract, mirrored).
+  store_frozen_through_after?: string | null;
 }
 
 export interface DeskTopupComputeProgress {
diff --git a/apps/backend/tests/test_desk_topup_library_reach_guard.py b/apps/backend/tests/test_desk_topup_library_reach_guard.py
new file mode 100644
index 0000000..43397d2
--- /dev/null
+++ b/apps/backend/tests/test_desk_topup_library_reach_guard.py
@@ -0,0 +1,84 @@
+"""goal-desk-iter-32 (J-19) source-introspection guard test -- the ``test_desk_ui_guards.py``/
+``test_desk_topup_window_disclosure_guard.py`` pattern (read ``apps/frontend/app/desk/page.tsx`` as
+TEXT, assert on substrings/structure; no browser, no runtime).
+
+Proves the Top-up Runs section's library-reach disclosure actually landed and stays wired the way
+the DoD requires:
+
+  (a) the honest legacy-run fallback text ``"library reach not recorded in this run"`` exists as
+      ONE shared constant (never a second, divergent copy of the string);
+  (b) the new descriptive line and the earlier-pairs list are both present, rendered beside the
+      existing ``desk-topup-run-latest-window-basis`` line -- no new section, no new control;
+  (c) ``topupLibraryReach`` never computes a value when any outcome lacks
+      `store_frozen_through_after` -- it returns ``null`` in that case, which the render layer maps
+      to the honest fallback rather than a guessed/backfilled date.
+
+A guard that can never fail proves nothing -- ``test_the_fallback_text_guard_can_fail_on_a_seeded_
+violation`` below seeds a violation (a second, drifted copy of the fallback string) and proves the
+same check catches it."""
+
+from __future__ import annotations
+
+import pathlib
+import re
+
+_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
+_DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"
+
+_FALLBACK_TEXT = "library reach not recorded in this run"
+
+
+def _source() -> str:
+    return _DESK_PAGE.read_text()
+
+
+def test_the_legacy_fallback_text_is_a_single_shared_constant():
+    source = _source()
+    # Exactly ONE string literal carries the fallback text (a `const` definition) -- every OTHER
+    # occurrence in the file references that constant by name, never repeats the literal.
+    literal_occurrences = source.count(f'"{_FALLBACK_TEXT}"')
+    assert literal_occurrences == 1, (
+        f"expected the fallback text to be defined as ONE shared string literal, found "
+        f"{literal_occurrences} -- a second, independently-typed copy risks drifting out of sync"
+    )
+    assert "LIBRARY_REACH_NOT_RECORDED" in source
+
+
+def test_the_reach_line_uses_the_shared_constant():
+    source = _source()
+    assert source.count("LIBRARY_REACH_NOT_RECORDED") >= 2  # 1 definition + >=1 usage
+
+
+def test_the_reach_line_and_earlier_list_are_present_beside_the_window_basis_line():
+    source = _source()
+    window_basis_idx = source.index('data-testid="desk-topup-run-latest-window-basis"')
+    reach_idx = source.index('data-testid="desk-topup-run-latest-reach"')
+    earlier_idx = source.index('data-testid="desk-topup-run-latest-reach-earlier"')
+    failed_idx = source.index('data-testid="desk-topup-run-latest-failed"')
+    # The new block sits AFTER the existing window-basis line and BEFORE the existing failed-pairs
+    # block -- no new section, no reordering of already-shipped disclosures.
+    assert window_basis_idx < reach_idx < earlier_idx < failed_idx
+
+
+def test_topup_library_reach_returns_null_when_any_outcome_lacks_store_frozen_through_after():
+    """``topupLibraryReach``'s own source slice (from its declaration to the NEXT top-level
+    ``function`` declaration) structurally returns ``null`` on an absent field rather than
+    defaulting/backfilling a date."""
+    source = _source()
+    marker = "function topupLibraryReach("
+    start = source.index(marker)
+    next_fn = source.index("\nfunction ", start + len(marker))
+    body = source[start:next_fn]
+    assert "store_frozen_through_after === undefined" in body
+    assert re.search(r"return\s+null", body) is not None
+
+
+def test_the_fallback_text_guard_can_fail_on_a_seeded_violation():
+    """A guard that can never fail proves nothing -- a seeded SECOND, independently-typed copy of
+    the fallback text is caught by the same counting check above."""
+    seeded = (
+        'const LIBRARY_REACH_NOT_RECORDED = "library reach not recorded in this run";\n'
+        'const other = "library reach not recorded in this run";\n'
+    )
+    literal_occurrences = seeded.count(f'"{_FALLBACK_TEXT}"')
+    assert literal_occurrences != 1
```
