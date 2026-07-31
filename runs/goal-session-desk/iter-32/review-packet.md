# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

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
diff --git a/docs/goal.md b/docs/goal.md
index 5f51789..8e1621f 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -1551,6 +1551,126 @@ order: J-01 → J-02 → J-03 → J-04 → J-05 → J-06, with J-07 guarding con
     exception discards all 100 ranked rows already computed — today into a process-scoped snapshot the
     next restart erases.)*
 
+- **J-19: Every top-up run records the date each pair's frozen history actually reaches**
+  - Steps:
+    1. Record ONE new desk-owned field on every per-pair outcome entry the shared walker already
+       builds (`run_topup`'s `entry` dict, `desk_topup_compute.py:304`): `store_frozen_through_after`
+       (name at build discretion) — that pair's own newest frozen bar AFTER the attempt, read
+       VERBATIM from the canonical owner through the SAME pure accessor J-17 already uses,
+       `_pair_window` over `BarStore.merged_bars(symbol, timeframe)` (`desk_topup_compute.py:162`/
+       `:182`, whose own docstring already sanctions repeat calls — "A PURE read (zero vendor calls,
+       zero writes) — safe to call more than once"), called once more immediately after
+       `_run_one_pair` returns and recorded beside the pre-fetch `store_frozen_through` J-17 already
+       records. Never `bar_index`'s `window_end_utc` (whose single owner stays `desk_coverage`),
+       never a new accessor, never a second fetch, never arithmetic over bars, and never a change to
+       `_run_one_pair`'s two-value return shape — the manager-mechanics tests substitute a FAKE
+       `_run_one_pair` returning a two-tuple (`tests/test_desk_topup_compute.py:139`/`:192`/`:339`/
+       `:870`) and every one of them must keep passing unmodified. The value is `null` only when the
+       pair holds nothing at all, exactly the shape `store_frozen_through` already uses. **Zero
+       diff** to `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py`,
+       `levels.py` and `routes.py`'s `record_bar_series`; zero new `Config` field; no new store,
+       endpoint, route or MCP tool.
+    2. State what it does NOT mean, structurally. The record describes THIS RUN's own observation of
+       the frozen store at attempt time — the J-09 rule verbatim: coverage and freshness keep their
+       single existing owner (`desk_coverage.get_desk_coverage` over `bar_index`), this journey
+       creates no second coverage path, cache or copy, serves no coverage value, adds no coverage
+       read anywhere, and leaves the ranked table's own coverage badges and their "window last
+       requested" tooltip byte-unchanged (`apps/frontend/app/desk/page.tsx:284`/`:357`). `/desk`
+       still fetches no coverage endpoint, and no screen row shape changes.
+    3. Own it exactly once: register the added per-pair field on the blueprint Data Contract's
+       "Top-up run records" row BEFORE the code lands — `desk_topup_log` stays the only owner and
+       `GET /research/desk/topup/runs` the only serving endpoint, written by the SAME single shared
+       writer both callers already use (`desk_topup_log.record_topup_run`, from the manager's resolve
+       path `desk_topup_compute.py:413` and the CLI's `main` `:547`) — never a second writer, never a
+       second outcome shape. The append-only rail is absolute: no recorded run is backfilled,
+       rewritten or recomputed; `GET /research/desk/topup/runs` serves legacy runs exactly as
+       recorded and `/desk` renders their absent field as an honest `"library reach not recorded in
+       this run"` (the established J-08/J-11/J-13/J-17 legacy-absence pattern), never a value derived
+       at read time. The top-up stays an explicit operator act (POST + CLI + the shipped button),
+       page-load GETs trigger nothing, and no scheduler, retry loop or auto-refresh is added
+       anywhere.
+    4. Surface it on `/desk` inside the SHIPPED Top-up Runs section — no new section, no new control,
+       no new column on the runs table and NO new column on the ranked briefing table, so J-16's
+       measured width contract stands untouched: the latest-run detail gains one descriptive line
+       naming the newest date this run's own pairs reach and how many pairs reach it, plus a short
+       list of the pairs whose recorded date is earlier (or `null`), each rendered with its own
+       symbol, timeframe and recorded date verbatim — both a plain tally/extreme over the served
+       payload, nothing derived from bars (the `topupOutcomeCounts`/`topupWindowBasisCounts`
+       precedent, `apps/frontend/app/desk/page.tsx:834`/`:857`). Copy = descriptive measurement only:
+       the page states the dates the run recorded and never a fresh/stale/current/behind/up-to-date
+       judgement, an advice, imperative, urgency or prediction, and never a saving, waste,
+       efficiency, speed or recommendation claim; `tests/test_copy_discipline.py` stays green
+       unmodified.
+    5. Test fixture-scoped with the suite's own injected fake adapter (the
+       `test_desk_topup_compute.py` pattern — no test touches the network): a pair whose fetch
+       genuinely appends bars records an `after` value later than its own recorded
+       `store_frozen_through` and byte-identical to the newest bar `BarStore.merged_bars` then
+       reports for that pair; a pair recorded `unchanged` and a pair recorded `failed` each record
+       their pre-fetch value verbatim; a `reused` pair records its pre-fetch value; a pair that held
+       nothing and whose fetch failed records `null`; a second run appends a new record while the
+       first record file stays byte-identical; the GET is honest-empty before any run and triggers
+       nothing; and every EXISTING test in `test_desk_topup_compute.py` and `test_desk_topup_log.py`
+       — including TC-7's "a second run is all-reused with zero vendor calls", TC-8's resumability
+       guarantee, the manager-mechanics tests' fake `_run_one_pair`, and
+       `test_desk_topup_compute_reads_merged_bars_and_never_reads_bar_index_window_end_utc` (`:614`)
+       — passes UNMODIFIED (if one genuinely pins the walker's per-pair read count, disclose it in
+       the iteration record rather than edit it — the J-17 precedent).
+  - Acceptance: on the fixture-scoped rig every per-pair outcome entry of a NEW top-up run carries
+    `store_frozen_through_after` byte-identical to the newest bar
+    `BarStore.merged_bars(symbol, timeframe)` reports for that pair after the walk — later than its
+    own recorded `store_frozen_through` exactly for the pairs whose fetch appended bars, equal to it
+    for every `reused`/`unchanged`/`failed` pair, and `null` only for a pair holding nothing
+    (**single source of truth**: the value is read verbatim from the canonical `BarStore`'s own
+    merged read through the accessor J-17 already calls — never `bar_index`'s request-bound
+    `window_end_utc`, never a second fetch, never a new accessor — the run record stays owned by
+    `desk_topup_log` alone and served by `GET /research/desk/topup/runs` alone, with the added field
+    registered in the Data Contract BEFORE the code lands; it records this run's own ATTEMPT-time
+    observation and never current coverage, and coverage/freshness still come solely from
+    `desk_coverage` over `bar_index`, with the briefing's coverage badges and their tooltip
+    byte-unchanged — this SSOT criterion stands in place of a PnL-ledger append, which this era's
+    Non-Goals forbid); every bar series file already on disk is proven byte-identical before and
+    after the iteration (SHA-256 listing — a top-up only ever APPENDS a new series; nothing is
+    deleted, re-keyed, superseded or rewritten) and every previously recorded universe, screen,
+    top-up and reconciliation record is proven byte-identical too, with legacy top-up runs rendering
+    the honest `"library reach not recorded in this run"` state; in a real browser after the T-9
+    clean rebuild, `/desk`'s Top-up Runs section shows the latest run's reach line AND at least one
+    pair whose own recorded date is earlier than that newest date, both legible in ONE screenshot at
+    a 1440×900 viewport with no horizontal scroll, and the ranked briefing table renders exactly as
+    J-16 shipped it (T-10: no screenshot ⇒ `unknown`, never `passing`; no native `title` tooltip is
+    required by this journey, so the T-10a headed rig is not needed); a **`[NEW]`-flagged
+    demo-narrator walkthrough** covers the top-up's library-reach disclosure end to end, narrated
+    over a populated run; and the full backend suite is green with
+    `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new `Config` fields, the `default`
+    profile and `v1` byte-identical (engine equivalence green), the MCP surface still exactly 17
+    tools, zero diff to
+    `bars.py`/`bar_index.py`/`desk_coverage.py`/`desk_screen.py`/`tradability.py`/`levels.py`/`StructureChart.tsx`,
+    and `tests/test_copy_discipline.py` + `tests/test_desk_ui_guards.py` +
+    `tests/test_desk_hover_tooltip_guard.py` green unmodified. *(Keyless core; browser-verifiable.
+    The real ~101-member top-up stays an operator-run act, reported honestly as run-or-not-run —
+    never a CI gate. Why: measured 2026-07-31 read-only over the frozen artifacts (no service
+    started, no product code run). **A top-up says what it asked for and what came back, never what
+    the library then holds.** The one recorded real run, `topup-2026-07-29-5de907c83fc4` (404 pairs,
+    12:00:29.889748Z → 12:04:53.521809Z, `0 reused · 390 fetched · 14 failed`), carries only
+    `{symbol, timeframe, outcome, detail}` per pair, and even a post-J-17 run records the store's
+    content only as it stood BEFORE each fetch (`store_frozen_through`) — so no artifact anywhere
+    states the date a pair's history reaches once a run ends. Reconstructing it took a walk of all
+    759 series files: that run advanced 235 pairs (by 3 d ×58, 4 d ×110, 5 d ×1, 6 d ×1, 7 d ×58,
+    14 d ×3, 15 d ×3, 22 d ×1), recorded 155 pairs for the first time, and failed 14. **What the
+    silence hides today:** the newest bar each pinned pair actually holds now spans 2026-07-21 to
+    2026-07-28 — `1h`: 88 members through 07-28, AAPL/AMT/BLK/LOW through 07-24, MSFT through 07-21,
+    and 8 members (MDT, MRK, MU, NEE, PEP, TMO, UNH, UPS) hold none; `4h`: 101 through 07-28; `1d`:
+    100 through 07-27 (NOW holds none — the screen's one `skipped: no basis` row); `1w`: 101 through
+    07-27. The only freshness the desk serves is `bar_index`'s `MAX(window_end_utc)` — the window a
+    run ASKED for — which for 394 of the 395 member × timeframe pairs that hold bars postdates the
+    newest bar actually held, by 1 day (193 pairs) or 2 days (201 pairs); the single exception is
+    MSFT `1h` (both read 2026-07-21). On `screen-2026-07-31-c169546856c7` (100 ranked / 1 skipped)
+    that renders as BLK #17 — a band of 134 levels, 53 of them `1h`, over a `1h` series that stops
+    2026-07-24 — beside BRK-B #1's 155-level band with 57 `1h` members over a series through
+    2026-07-28, both rows showing an identical lit `1h` badge whose only difference is a requested
+    window in a hover tooltip (`2026-07-25T00:00:00Z` vs `2026-07-29T00:00:00Z`). And J-17's tail
+    window ends at wall-clock today for every pair it applies to, so after the next daily top-up even
+    that faint request-bound difference collapses to one identical date for every successful pair.)*
+
 <!-- /AUTO:journeys -->
 
 ## Anti-goals
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-desk/state/assumptions.md        | 36 ++++++++++++++++++++++
 runs/goal-session-desk/state/blueprint.md          |  5 ++-
 .../state/enhancement-proposals.jsonl              |  3 ++
 runs/goal-session-desk/state/proposer-result.json  |  2 +-
 runs/goal-session-desk/telemetry.jsonl             | 20 ++++++++++++
 runs/goal-session-desk/trace/trace.jsonl           |  3 ++
 6 files changed, 67 insertions(+), 2 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
