# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

```diff
diff --git a/apps/backend/app/research/desk_screen.py b/apps/backend/app/research/desk_screen.py
index 34b0ba4..624ebc3 100644
--- a/apps/backend/app/research/desk_screen.py
+++ b/apps/backend/app/research/desk_screen.py
@@ -109,6 +109,20 @@ fields established: never defaulted, never backfilled (``opposite_band`` ITSELF
 recorded as ``null`` on a NEW row, when the canonical return holds no band on the other side -- that
 is distinct from the ROW omitting the key entirely, which only a pre-iteration snapshot ever does).
 
+**Wall-composition disclosure (goal-desk-iter-23, J-15).** Every RANKED row also carries
+``band_member_count`` (int) and ``band_round_number`` (bool) -- copied VERBATIM from the SAME
+``best`` band dict ``_select_best_band`` already returns (that band's own ``member_count``/
+``round_number`` keys, ``tradability.py:343`` -- zero second ``compute_tradability`` call, zero
+second ``BarStore`` read, zero touch to ``_select_best_band``/``_select_opposite_band``/
+``_row_rank_key``) -- plus ``band_member_timeframes`` (dict[str, int]), a plain per-timeframe tally
+of that SAME band's own ``members`` list (see ``_band_member_timeframes`` above). The band's own
+``members`` list itself is NEVER copied onto the row -- no member price/``touch_count``/``strength``
+is copied, only the count/flag/tally. Skip rows never carry any of the three, matching the basis/
+history/reference-close/opposite-band precedent exactly. A snapshot recorded BEFORE this addition
+simply has ranked rows that OMIT these three keys entirely -- the SAME append-only-row-content
+discipline the prior disclosures established: never defaulted, never backfilled, never present as
+``null``.
+
 **No new ``Config`` field.** The screen store's directory resolves via ``resolve_desk_screen_dir``
 below -- a bare ``TAPEOLOGY_DESK_SCREEN_DIR``-env-var-or-sibling-of-``desk_universe_dir_resolved()``
 default (the ``edge_report_cache.resolve_cache_db_path`` pattern) -- never a ``desk_screen_dir``
@@ -295,6 +309,23 @@ def _select_opposite_band(bands: list[dict], close: float, best_side: str) -> di
     return min(opposite_side_bands, key=key)
 
 
+def _band_member_timeframes(members: list[dict]) -> dict[str, int]:
+    """A plain per-timeframe tally of a SINGLE band's own ``members`` list (goal-desk-iter-23,
+    J-15) -- mirrors ``_bands_by_class``'s "plain dict tally" construction style, but UNLIKE that
+    precedent never fabricates a zero for an absent timeframe: only timeframes actually present
+    among ``members`` appear as keys at all. Key order is first-seen while walking ``members`` in
+    ``compute_tradability``'s own already-sorted order (``tradability.py:364``'s
+    ``sorted(..., key=itemgetter("price", "timeframe", "type"))``) -- Python dict insertion order
+    is stable, so this order is deterministic and reproducible across runs without any extra sort
+    of its own. Values always sum to ``len(members)`` (== the SAME band's own ``member_count``) by
+    construction -- every member increments exactly one key."""
+    tally: dict[str, int] = {}
+    for member in members:
+        timeframe = member["timeframe"]
+        tally[timeframe] = tally.get(timeframe, 0) + 1
+    return tally
+
+
 def _bands_by_class(bands: list[dict]) -> dict[str, int]:
     """A plain per-class count of ``bands`` (goal-desk-iter-18, J-14) -- a band with ``class: None``
     counts under ``"unclassified"``; all four keys are always present, even at zero. A count only --
@@ -390,10 +421,12 @@ def compute_screen(
     assigns those): ``{screen_date, as_of, universe_snapshot_id, config_fingerprint,
     bar_store_signature, rows, skipped}``. Each RANKED row additionally carries ``basis_as_of``/
     ``basis_age_days`` (goal-desk-iter-9, J-08), ``history_sessions``/``history_start``
-    (goal-desk-iter-15, J-11), ``reference_close`` (goal-desk-iter-17, J-13), and
-    ``opposite_band``/``bands_by_class`` (goal-desk-iter-18, J-14) -- see the module docstring's
-    "Basis disclosure", "History disclosure", "Reference-close disclosure", and "Opposite-band
-    disclosure" sections; skip rows never carry any of the seven.
+    (goal-desk-iter-15, J-11), ``reference_close`` (goal-desk-iter-17, J-13),
+    ``opposite_band``/``bands_by_class`` (goal-desk-iter-18, J-14), and ``band_member_count``/
+    ``band_round_number``/``band_member_timeframes`` (goal-desk-iter-23, J-15) -- see the module
+    docstring's "Basis disclosure", "History disclosure", "Reference-close disclosure",
+    "Opposite-band disclosure", and "Wall-composition disclosure" sections; skip rows never carry
+    any of the ten.
 
     ``progress``, if given, is called after EACH member with ``{"symbol": symbol}`` (the caller
     tracks its own done/total counters -- the ``desk_topup_compute.run_topup`` precedent).
@@ -471,6 +504,9 @@ def compute_screen(
                         else None
                     ),
                     "bands_by_class": _bands_by_class(result["bands"]),
+                    "band_member_count": best["member_count"],
+                    "band_round_number": best["round_number"],
+                    "band_member_timeframes": _band_member_timeframes(best["members"]),
                 }
             )
 
diff --git a/apps/backend/tests/test_desk_screen.py b/apps/backend/tests/test_desk_screen.py
index 3cd1bb3..de5fa08 100644
--- a/apps/backend/tests/test_desk_screen.py
+++ b/apps/backend/tests/test_desk_screen.py
@@ -183,8 +183,22 @@ def test_bar_store_signature_is_deterministic_across_fresh_instances(ctx):
 # ==================================================================================================
 
 
-def _band(side: str, price_low: float, price_high: float, band_class: str | None, quality: float) -> dict:
-    return {"side": side, "price_low": price_low, "price_high": price_high, "class": band_class, "quality_score": quality}
+def _band(
+    side: str, price_low: float, price_high: float, band_class: str | None, quality: float,
+    *, members: list[dict] | None = None, round_number: bool = False,
+) -> dict:
+    """A minimal band dict carrying every key `_select_best_band`/`_select_opposite_band`/the row
+    builder read. `members` defaults to a single synthetic `1d` level at `price_low` (goal-desk-
+    iter-23, J-15) -- an honest, valid single-member band -- so every EXISTING call site (none of
+    which cares about wall-composition) keeps working unchanged; `member_count` is ALWAYS
+    `len(members)`, mirroring `tradability.py`'s own `_band`, which never lets the two diverge."""
+    if members is None:
+        members = [{"price": price_low, "timeframe": "1d", "type": "level", "touch_count": 1}]
+    return {
+        "side": side, "price_low": price_low, "price_high": price_high, "class": band_class,
+        "quality_score": quality, "member_count": len(members), "round_number": round_number,
+        "members": members,
+    }
 
 
 def test_distance_bps_resistance_uses_the_low_edge():
@@ -665,6 +679,17 @@ def test_aapl_row_cross_checks_byte_identical_to_the_real_tradability_route(ctx,
         ) / row["reference_close"] * 10_000.0
         assert row["opposite_band"]["distance_bps"] == pytest.approx(expected_opposite_distance)
 
+    # goal-desk-iter-23 (J-15) TC-2/TC-3: band_member_count/band_round_number are copied verbatim
+    # off the SAME served band's own member_count/round_number, and band_member_timeframes is a
+    # plain tally of that SAME band's own members list, summing to band_member_count.
+    assert row["band_member_count"] == served["member_count"]
+    assert row["band_round_number"] == served["round_number"]
+    expected_timeframes: dict[str, int] = {}
+    for member in served["members"]:
+        expected_timeframes[member["timeframe"]] = expected_timeframes.get(member["timeframe"], 0) + 1
+    assert row["band_member_timeframes"] == expected_timeframes
+    assert sum(row["band_member_timeframes"].values()) == row["band_member_count"]
+
 
 def test_msft_partial_coverage_still_resolves_a_ranked_row_with_honest_coverage(ctx):
     """TC-2: MSFT (real symbol, 1h+1d bars only -- never 1w/4h) is never mis-skipped merely for
@@ -1519,6 +1544,237 @@ def test_opposite_band_and_bands_by_class_add_zero_extra_compute_tradability_or_
     )
 
 
+# ==================================================================================================
+# wall-composition disclosure (goal-desk-iter-23, J-15) -- band_member_count/band_round_number/
+# band_member_timeframes, copied/tallied VERBATIM off the SAME `best` band `_select_best_band`
+# already returns. Mirrors the opposite-band/bands_by_class suite immediately above.
+# ==================================================================================================
+
+
+def test_band_member_fields_golden_single_member_and_intraday_dominated_rows(ctx, monkeypatch):
+    """TC-1/TC-4/TC-5: three controlled ranked rows -- one whose selected band holds a SINGLE
+    member (a zero-width `price_low == price_high` band, the goal.md worked example's own #45 SPG
+    shape), one whose selected band is dominated by intraday (`1m`/`5m`) members (the worked
+    example's own MSFT/AAPL shape), and one "normal" multi-timeframe confluence that is ALSO a
+    round-number band -- each proving `band_member_count`/`band_round_number` are copied verbatim
+    off the SAME `best` band dict, and `band_member_timeframes` is a plain per-timeframe tally of
+    that SAME band's own `members` list, summing to `band_member_count`, with an absent timeframe
+    simply missing (never a fabricated zero). Mirrors
+    `test_opposite_band_golden_near_far_and_null_class_rows`'s controlled-band monkeypatch style."""
+    import app.research.desk_screen as desk_screen_module
+
+    universe_store, bar_store, bar_index, dataset_store = ctx
+    single_bar = _daily_bars("AIG", start=date(2026, 6, 18), count=1)[0]
+    intraday_bar = _daily_bars("AMGN", start=date(2026, 6, 18), count=1)[0]
+    normal_bar = _daily_bars("AMT", start=date(2026, 6, 18), count=1)[0]
+    _seed_daily_bars(bar_store, bar_index, [single_bar])
+    _seed_daily_bars(bar_store, bar_index, [intraday_bar])
+    _seed_daily_bars(bar_store, bar_index, [normal_bar])
+
+    single_basis = _iso_of(single_bar.epoch)
+    intraday_basis = _iso_of(intraday_bar.epoch)
+    normal_basis = _iso_of(normal_bar.epoch)
+
+    single_member = [{"price": single_bar.close, "timeframe": "1d", "type": "level", "touch_count": 1}]
+    aig_best = _band(
+        "resistance", single_bar.close, single_bar.close, "A", 10.0,
+        members=single_member, round_number=False,
+    )
+
+    intraday_members = (
+        [{"price": intraday_bar.close, "timeframe": "1m", "type": "level", "touch_count": 1} for _ in range(6)]
+        + [{"price": intraday_bar.close, "timeframe": "5m", "type": "level", "touch_count": 1} for _ in range(2)]
+        + [{"price": intraday_bar.close, "timeframe": "1d", "type": "level", "touch_count": 1}]
+    )
+    amgn_best = _band(
+        "resistance", intraday_bar.close, intraday_bar.close + 1.0, "B", 5.0,
+        members=intraday_members, round_number=False,
+    )
+
+    normal_members = (
+        [{"price": normal_bar.close, "timeframe": "1d", "type": "level", "touch_count": 1} for _ in range(3)]
+        + [{"price": normal_bar.close, "timeframe": "1h", "type": "level", "touch_count": 1} for _ in range(2)]
+        + [{"price": normal_bar.close, "timeframe": "4h", "type": "level", "touch_count": 1}]
+    )
+    amt_best = _band(
+        "resistance", normal_bar.close, normal_bar.close + 2.0, "A", 20.0,
+        members=normal_members, round_number=True,
+    )
+
+    original = desk_screen_module.compute_tradability
+
+    def _tracked(store, symbol, as_of_epoch, config):
+        if symbol == "AIG":
+            return {"no_bar_series_for_symbol": False, "basis_as_of": single_basis, "bands": [aig_best]}
+        if symbol == "AMGN":
+            return {"no_bar_series_for_symbol": False, "basis_as_of": intraday_basis, "bands": [amgn_best]}
+        if symbol == "AMT":
+            return {"no_bar_series_for_symbol": False, "basis_as_of": normal_basis, "bands": [amt_best]}
+        return original(store, symbol, as_of_epoch, config)
+
+    monkeypatch.setattr(desk_screen_module, "compute_tradability", _tracked)
+
+    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
+    by_symbol = {r["symbol"]: r for r in screen["rows"]}
+
+    aig_row = by_symbol["AIG"]
+    assert aig_row["price_low"] == aig_row["price_high"], "the zero-width band this fixture builds"
+    assert aig_row["band_member_count"] == 1
+    assert aig_row["band_round_number"] is False
+    assert aig_row["band_member_timeframes"] == {"1d": 1}
+    assert sum(aig_row["band_member_timeframes"].values()) == aig_row["band_member_count"]
+
+    amgn_row = by_symbol["AMGN"]
+    assert amgn_row["band_member_count"] == 9
+    assert amgn_row["band_round_number"] is False
+    assert amgn_row["band_member_timeframes"] == {"1m": 6, "5m": 2, "1d": 1}
+    assert list(amgn_row["band_member_timeframes"].keys()) == ["1m", "5m", "1d"], (
+        "key order is first-seen over the band's own already-sorted members list"
+    )
+    assert sum(amgn_row["band_member_timeframes"].values()) == amgn_row["band_member_count"]
+
+    amt_row = by_symbol["AMT"]
+    assert amt_row["band_member_count"] == 6
+    assert amt_row["band_round_number"] is True
+    assert amt_row["band_member_timeframes"] == {"1d": 3, "1h": 2, "4h": 1}
+    assert "1w" not in amt_row["band_member_timeframes"], (
+        "a timeframe with no member in this band is simply absent, never a fabricated zero"
+    )
+    assert sum(amt_row["band_member_timeframes"].values()) == amt_row["band_member_count"]
+
+
+def test_sum_of_band_member_timeframes_equals_band_member_count_on_every_ranked_row(ctx):
+    """TC-3: the sum invariant holds on EVERY ranked row of a REAL (non-monkeypatched) screen --
+    not just the controlled golden rows above."""
+    universe_store, bar_store, bar_index, dataset_store = ctx
+    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
+    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_DAILY_FIXTURE))
+    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(MSFT_HOURLY_FIXTURE))
+
+    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
+    assert len(screen["rows"]) >= 1
+    for row in screen["rows"]:
+        assert sum(row["band_member_timeframes"].values()) == row["band_member_count"]
+
+
+def test_row_order_is_unchanged_by_the_band_member_fields_addition(ctx):
+    """TC-7: `_row_rank_key` is computed entirely from `band_class`/`distance_bps`/`band_score`/
+    `symbol` -- unchanged this iteration (verify via `git diff`, appearing only as unchanged
+    CONTEXT) -- none of `band_member_count`/`band_round_number`/`band_member_timeframes` touches
+    it. Mirrors `test_row_order_is_unchanged_by_the_opposite_band_addition`."""
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
+def test_band_member_fields_stay_byte_identical_on_a_recompute_under_identical_pins(ctx, tmp_path):
+    """TC-8: mirrors `test_opposite_band_stays_byte_identical_on_a_recompute_under_identical_pins`
+    for band_member_count/band_round_number/band_member_timeframes specifically -- a screen
+    recorded once, then a FRESH computation under identical pins, is refused a second write, and
+    the content already on disk is byte-identical to the second (unrecorded) computation's fields
+    on every ranked row."""
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
+    expected_aapl_row = next(r for r in second_screen["rows"] if r["symbol"] == "AAPL")
+    assert aapl_row["band_member_count"] == expected_aapl_row["band_member_count"]
+    assert aapl_row["band_round_number"] == expected_aapl_row["band_round_number"]
+    assert aapl_row["band_member_timeframes"] == expected_aapl_row["band_member_timeframes"]
+
+
+def test_a_legacy_row_recorded_without_band_member_fields_serves_them_absent_never_backfilled(
+    tmp_path,
+):
+    """TC-9: the exact shape every screen snapshot recorded BEFORE this iteration has -- ranked
+    rows that OMIT band_member_count/band_round_number/band_member_timeframes entirely (never
+    merely present-as-`null`) -- mirrors the basis/history/reference-close/opposite-band legacy-row
+    precedents. `_record`'s own default row carries no such keys at all, so this is true by
+    construction; this test pins that contract so a future change cannot silently start
+    defaulting or backfilling legacy rows on read."""
+    store = ScreenStore(tmp_path / "screen")
+    _record(store)  # `_record`'s own default row carries none of the three keys at all
+
+    records, errors = store.list()
+    assert errors == []
+    row = records[0]["rows"][0]
+    assert "band_member_count" not in row
+    assert "band_round_number" not in row
+    assert "band_member_timeframes" not in row
+
+
+def test_band_member_fields_add_zero_extra_compute_tradability_or_merged_bars_calls(ctx, monkeypatch):
+    """TC-6: band_member_count/band_round_number/band_member_timeframes are a pure copy/tally over
+    the SAME `best` band dict a symbol's SINGLE `compute_tradability` call already returned --
+    mirrors `test_opposite_band_and_bands_by_class_add_zero_extra_compute_tradability_or_merged_bars_calls`:
+    zero additional `compute_tradability` calls per symbol, zero additional `BarStore.merged_bars`
+    calls beyond what iteration 17/18's disclosures already required."""
+    universe_store, bar_store, bar_index, dataset_store = ctx
+    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
+
+    as_of_epoch = _epoch(screen_as_of(SCREEN_DATE))
+    merged_calls: list[tuple[str, str]] = []
+    original_merged = BarStore.merged_bars
+
+    def _tracked_merged(self, symbol, timeframe):
+        merged_calls.append((symbol, timeframe))
+        return original_merged(self, symbol, timeframe)
+
+    monkeypatch.setattr(BarStore, "merged_bars", _tracked_merged)
+
+    from app.research.tradability import compute_tradability as _compute_tradability
+
+    _compute_tradability(bar_store, "AAPL", as_of_epoch, CONFIG)
+    baseline_1d_calls = sum(1 for symbol, tf in merged_calls if symbol == "AAPL" and tf == "1d")
+    merged_calls.clear()
+
+    import app.research.desk_screen as desk_screen_module
+
+    tradability_calls: list[str] = []
+    original_tradability = desk_screen_module.compute_tradability
+
+    def _tracked_tradability(store, symbol, as_of_epoch_arg, config):
+        tradability_calls.append(symbol)
+        return original_tradability(store, symbol, as_of_epoch_arg, config)
+
+    monkeypatch.setattr(desk_screen_module, "compute_tradability", _tracked_tradability)
+
+    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
+    aapl_row = next(r for r in screen["rows"] if r["symbol"] == "AAPL")
+    assert "band_member_count" in aapl_row
+
+    assert tradability_calls.count("AAPL") == 1, (
+        "band_member_count/band_round_number/band_member_timeframes must be derived from the "
+        "symbol's single existing compute_tradability call, never a second call"
+    )
+    full_1d_calls = sum(1 for symbol, tf in merged_calls if symbol == "AAPL" and tf == "1d")
+    assert full_1d_calls == baseline_1d_calls + 1, (
+        "band_member_count/band_round_number/band_member_timeframes must add ZERO extra "
+        "merged_bars calls beyond what iteration 17/18's disclosures already required"
+    )
+
+
 # ==================================================================================================
 # screen ?id= read (goal-desk-iter-16, J-12) -- individual addressability, including an EARLIER
 # same-`screen_date` recording that `?date=` (which always resolves `matching[-1]`) can never reach.
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index a5874f8..e9c168b 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -123,6 +123,17 @@ import { fmt } from "@/lib/format";
 // every band the canonical tradability computation returned for the symbol). Read-only render,
 // zero new endpoint, zero new control, zero client-side arithmetic — both fields ride the
 // already-fetched `GET /research/desk/screen` response verbatim.
+//
+// goal-desk-iter-23 (J-15): a new `levels` column on the ranked-rows table — the row's own
+// `band_member_count`/`band_member_timeframes` rendered as a tally string (e.g. `155 levels · 1d
+// 68 · 1h 57 · 4h 19 · 1w 11`) plus `/structure`'s own "round number" badge (reused verbatim,
+// including its `data-testid`/className) when `band_round_number` is true. No new tooltip line —
+// every one of the three values is an exact integer or boolean, so there is nothing rounded to
+// disclose full precision for. The established legacy-absent copy "composition not recorded in
+// this snapshot" covers a pre-iteration row (`band_member_count === undefined`, never a computed
+// or inferred fallback from `band_score`/the band range/`bands_by_class`). Read-only render, zero
+// new endpoint, zero new control — all three fields ride the already-fetched `GET
+// /research/desk/screen` response verbatim.
 
 const NUMERIC_CELL = "px-2 py-1.5 text-right font-mono text-xs text-slate-200 whitespace-nowrap";
 const HEADER_CELL = "px-2 py-1 text-right text-[11px] font-medium text-slate-500";
@@ -424,6 +435,34 @@ function DeskRow({ row, asOf }: { row: DeskScreenRow; asOf: string }) {
                 row.opposite_band.price_low
               )}–${fmt(row.opposite_band.price_high)} · ${fmt(row.opposite_band.distance_bps)} bps`}
       </td>
+      {/* goal-desk-iter-23 (J-15): what the row's own selected wall is actually made of --
+          band_member_count/band_member_timeframes as an exact tally string, plus /structure's own
+          "round number" badge (same data-testid/className, reused verbatim) when
+          band_round_number is true. Every value here is an exact integer or boolean -- no
+          rounding -- so no per-cell title is added (the F2 lesson does not apply: there is no
+          full-precision detail to hide behind a hover). `=== undefined` catches a legacy row's
+          ENTIRELY ABSENT key (band_member_count is always >= 1 by construction whenever it is
+          recorded at all, so it is never legitimately null) -- the same strict check
+          bands_by_class already uses. */}
+      <td className={LABEL_CELL} data-testid="desk-row-levels">
+        {row.band_member_count === undefined || row.band_member_timeframes === undefined
+          ? "composition not recorded in this snapshot"
+          : (
+              <>
+                {`${row.band_member_count} levels · ${Object.entries(row.band_member_timeframes)
+                  .map(([timeframe, count]) => `${timeframe} ${count}`)
+                  .join(" · ")}`}{" "}
+                {row.band_round_number && (
+                  <span
+                    data-testid="tradable-band-round-number"
+                    className="inline-block whitespace-nowrap rounded border border-slate-700 bg-slate-800/60 px-1.5 py-0.5 text-[11px] text-slate-300"
+                  >
+                    round number
+                  </span>
+                )}
+              </>
+            )}
+      </td>
     </tr>
   );
 }
@@ -455,6 +494,7 @@ function DeskRowsTable({ rows, asOf }: { rows: DeskScreenRow[]; asOf: string })
             <th className={HEADER_CELL_LEFT}>history</th>
             <th className={HEADER_CELL_LEFT}>band</th>
             <th className={HEADER_CELL_LEFT}>opposite</th>
+            <th className={HEADER_CELL_LEFT}>levels</th>
           </tr>
         </thead>
         <tbody>
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 631460a..951d3fe 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -847,6 +847,16 @@ export interface DeskScreenRow {
     distance_bps: number;
   } | null;
   bands_by_class?: { A: number; B: number; C: number; unclassified: number };
+  // goal-desk-iter-23 (J-15): copied VERBATIM from the SAME `best` band `desk_screen.py` already
+  // selected -- that band's own `member_count`/`round_number` (tradability.py:343) plus a plain
+  // per-timeframe tally of that SAME band's own `members` list (keys are only the timeframes
+  // actually present, never a fabricated zero). A row from a snapshot recorded BEFORE this
+  // iteration has all three keys entirely ABSENT (`undefined`), never present as `null` --
+  // `band_member_count` is always >= 1 on any row that carries it at all, so `=== undefined` is
+  // the honest legacy-absence check, matching `bands_by_class`'s own convention.
+  band_member_count?: number;
+  band_round_number?: boolean;
+  band_member_timeframes?: Record<string, number>;
 }
 
 // A member the screen walked but could not rank -- two honest, distinct reasons, never conflated:
diff --git a/docs/goal.md b/docs/goal.md
index 8a7a061..563296a 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -1072,6 +1072,110 @@ order: J-01 → J-02 → J-03 → J-04 → J-05 → J-06, with J-07 guarding con
     and 42 of them hold ten class-A bands, so `bands_by_class` is what makes the class column's constancy
     legible instead of mysterious.)*
 
+- **J-15: Every ranked briefing row states what its wall is actually made of**
+  - Steps:
+    1. Record three desk-owned fields on every NEW ranked screen row, all taken from the SAME band dict
+       `_select_best_band` (`desk_screen.py:262`) already returns — the band `compute_tradability` itself
+       built (`tradability._band`, `tradability.py:343`): `band_member_count` and `band_round_number`,
+       copied **VERBATIM** out of that band's own `member_count` / `round_number` keys (never
+       recomputed, never re-derived, never compared against a threshold), and `band_member_timeframes`,
+       a plain count of that SAME band's own `members` list under those members' own `timeframe` values
+       (the `bands_by_class` precedent, `_bands_by_class`, `desk_screen.py:298`) — keys are exactly the
+       timeframes present among those members in a deterministic order, values are integer counts whose
+       sum EQUALS `band_member_count`, and a timeframe with no member in this band is simply absent,
+       never a fabricated zero for a timeframe the symbol's own level computation never read. The band's
+       `members` list itself is NEVER copied into the record (the J-14 rule), no member price /
+       `touch_count` / `strength` is copied, and no second store read and no second `compute_tradability`
+       call is made: zero diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py` (no new field on
+       any frozen return shape), zero new `Config` field, no new index, no new cache. Skip rows carry
+       none of the three (the J-08/J-11/J-13/J-14 shape).
+    2. Register all three in the blueprint's Data Contract "Screen snapshots, rank rows, skip rows" row
+       BEFORE the code lands — one owner (`desk_screen.py`), one serving endpoint
+       (`GET /research/desk/screen`). The snapshot key (screen date, as_of, universe snapshot id,
+       `config_fingerprint`, bar-store signature) is unchanged, and the rank key — band class A>B>C,
+       then distance asc, then band score desc, then symbol asc — is UNCHANGED: this journey DISCLOSES,
+       it never ranks, filters, gates, weights, or scores. Neither count nor the flag enters
+       `_row_rank_key` (`desk_screen.py:309`) or any band selection, and no "confluence quality",
+       "evidence depth", intraday-share ratio, threshold, or judgement about which composition is
+       BETTER is computed anywhere (this era's Non-Goals forbid new statistics and gates outright); the
+       copy never advises, predicts, or implies action.
+    3. Keep the append-only rail: never backfill, rewrite, or recompute an already-recorded snapshot;
+       `GET /research/desk/screen` serves legacy rows exactly as recorded, and `/desk` renders their
+       absent composition as an honest `"composition not recorded in this snapshot"` — the established
+       J-08/J-11/J-13/J-14 pattern (`apps/frontend/app/desk/page.tsx:383/392/407/420`) — never a value
+       computed at read time, and in particular never inferred on the page from `band_score`, the band
+       range, or `bands_by_class`, which is precisely the client-side recomputation the
+       single-source-of-truth rail forbids.
+    4. Surface it on `/desk`: exactly ONE new descriptive column, `levels`, beside the existing
+       `band`/`opposite` columns, rendering the row's OWN recorded counts and flag (e.g.
+       `155 levels · 1d 68 · 1h 57 · 4h 19 · 1w 11`) together with the same `round number` badge
+       `/structure`'s own band table already renders for the identical canonical field
+       (`apps/frontend/app/structure/page.tsx:612/619`), so the two pages describe one band in one
+       vocabulary. Every new value is an exact integer or boolean, so there is NO rounded display and
+       therefore NO new row-tooltip line is required or added by this journey (the iter-7 full-precision
+       tooltip pattern covers rounded numerics only; J-14's `bands_by_class` tooltip line stays exactly
+       as shipped, and no per-cell `title` is ever added under the stretched drill-in anchor). Copy =
+       descriptive measurement only, and `tests/test_copy_discipline.py` stays green unmodified.
+    5. Test fixture-scoped: a golden screen asserting the exact `band_member_count`,
+       `band_round_number` and `band_member_timeframes` per ranked row — including one row whose band
+       holds a SINGLE member (a zero-width `price_low == price_high` band) and one whose band is
+       dominated by intraday (`1m`/`5m`) members — plus the
+       `sum(band_member_timeframes.values()) == band_member_count` invariant asserted on every ranked
+       row, and byte-identical row content on a re-run under identical pins; a guard test that the row
+       builder issues NO additional `BarStore` read and NO second `compute_tradability` call beyond the
+       ones it already makes (assert the call counts — the J-11/J-13/J-14 precedent) and that the
+       frontend derives no count of its own; a golden comparison proving the recorded rank order is
+       byte-identical to what the same pins produced before this change; the MCP `desk_screen` tool
+       stays a byte-identical GET proxy (J-06's exactly-17-tool contract unchanged).
+  - Acceptance: on the fixture-scoped rig a NEW screen run — for a screen date not already recorded
+    under the same five pins, so the store's identical-pin refusal is respected rather than worked
+    around — records `band_member_count`, `band_round_number` and `band_member_timeframes` on every
+    ranked row, and each row's `band_member_count`/`band_round_number` are byte-identical to the
+    `member_count`/`round_number` of the corresponding band in
+    `GET /research/tradability?symbol=<sym>&as_of=<that snapshot's own as_of>`'s own `bands` list, while
+    `band_member_timeframes` is a plain tally of that SAME band's own `members` list by `timeframe` and
+    sums to that band's own `member_count` (**single source of truth**: the desk copies the canonical
+    owner's own band fields verbatim and counts that same band's own members inside the call it already
+    makes — no second read, no second compute, no re-grading, no re-scoring — and all three values are
+    registered in the Data Contract with `desk_screen.py` as their only owner and
+    `GET /research/desk/screen` as their only serving endpoint; this SSOT criterion stands in place of a
+    PnL-ledger append, which this era's Non-Goals forbid); the recorded rank order is byte-identical to
+    what the same pins produced before this change (disclosure only — a golden comparison proves the
+    rank key did not move); a re-run under identical pins reproduces byte-identical rows and a
+    same-pins re-run still returns the honest already-recorded response; every previously recorded
+    screen snapshot is proven byte-identical on disk (checksums unchanged, nothing backfilled) and
+    `/desk` renders their rows with the honest `"composition not recorded in this snapshot"` state; in a
+    real browser after the T-9 clean rebuild, `/desk` shows the `levels` column with at least one ranked
+    row whose band holds ≤ 5 levels and one whose band holds ≥ 100 levels legible in the SAME
+    screenshot, plus one row carrying the `round number` badge legible in that same frame or in one
+    further screenshot of the SAME rendered screen (T-10: no screenshot ⇒ `unknown`, never `passing`; no
+    native `title` tooltip is required by this journey, so the T-10a headed rig is not needed for it); a
+    **`[NEW]`-flagged demo-narrator walkthrough** covers the briefing's wall-composition disclosure end
+    to end, narrated over POPULATED ranked rows; and the full backend suite is green with
+    `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new `Config` fields, the `default`
+    profile and `v1` byte-identical (engine equivalence green), the MCP surface still exactly 17 tools,
+    zero diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`, and
+    `tests/test_copy_discipline.py` green unmodified. *(Keyless core; browser-verifiable. Why: measured
+    2026-07-30 against the canonical owner's own recorded output — all 100 ranked rows of
+    `screen-2026-07-29-2a57de4e7415` (100 ranked / 1 skipped) matched to their own
+    `compute_tradability` returns cached in `.data/tradability_cache.db` on
+    (`side`,`price_low`,`price_high`,`quality_score`), 100/100 matched. The selected bands'
+    `member_count` spans **1 to 4,014** (quartiles 19 / 45.5 / 87) and `round_number` is **true on 16 of
+    the 100 rows** — and NEITHER value is recorded on any screen row or rendered anywhere on `/desk`,
+    while `/structure`'s own band table renders BOTH for the identical bands (a `member count` column
+    plus a `round number` badge, `app/structure/page.tsx:612/619`), so the briefing says less about a
+    wall than the page it drills into. The 15 top-ranked rows every one read `support · Class A ·
+    0.00 bps`, yet their walls are built of 2 to 609 levels: #4 MSFT's band holds **609** members of
+    which **572 are `1m`/`5m`** and only 28 are `1d`; #1 BRK-B's holds 155 (68 of them `1d`); #15 ORCL's
+    holds **2** (one `1h` + one `1d`); and #45 SPG's holds a **single** member, which is why its
+    recorded band is zero-width (`price_low == price_high == 231.72999572753906`) and prints today as
+    `band 231.73–231.73` with nothing saying why. Across the 100 rows composition spans 1 to 6 distinct
+    timeframes (75 rows are 4-timeframe confluences, 1 row a single timeframe) and 8 rows carry
+    intraday members, up to AAPL's 4,014-member band (3,895 of them `1m`/`5m`). `DeskScreenRow`
+    (`lib/types.ts:826`) carries no field for any of it, and the ranked table's eleven columns — symbol,
+    side, class, distance, score, coverage, tick evidence, basis, history, band, opposite — have no cell
+    for it.)*
+
 <!-- /AUTO:journeys -->
 
 ## Anti-goals
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/.phase.lock/epoch                             |  2 +-
 runs/.phase.lock/pid                               |  2 +-
 runs/goal-session-desk/state/blueprint.md          | 45 ++++++++++++++++++++--
 .../state/enhancement-proposals.jsonl              |  5 +++
 runs/goal-session-desk/state/proposer-result.json  |  4 +-
 runs/goal-session-desk/telemetry.jsonl             | 22 +++++++++++
 runs/goal-session-desk/trace/trace.jsonl           |  4 ++
 7 files changed, 77 insertions(+), 7 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
