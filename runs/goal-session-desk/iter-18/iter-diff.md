# Iteration diff (bounded)

Files changed: 6. Shown in full: 6.

```diff
diff --git a/apps/backend/app/research/desk_screen.py b/apps/backend/app/research/desk_screen.py
index 87bf412..2c7c3dd 100644
--- a/apps/backend/app/research/desk_screen.py
+++ b/apps/backend/app/research/desk_screen.py
@@ -87,6 +87,23 @@ this addition simply has ranked rows that OMIT this key entirely -- the SAME app
 discipline the basis/history fields established: never defaulted, never backfilled, never present
 as ``null``.
 
+**Opposite-band disclosure (goal-desk-iter-18, J-14).** Every RANKED row also carries
+``opposite_band`` -- the nearest band on the side of price the row's own selected ``best`` band did
+NOT choose, selected from the SAME ``result["bands"]`` list ``_select_best_band`` already ran over
+(zero new ``BarStore`` read, zero second ``compute_tradability`` call), ranked by the IDENTICAL
+``(class rank DESCENDING, distance_bps ascending, quality_score descending)`` tuple via ``min``'s
+own first-of-tie stability (see ``_select_opposite_band`` below) -- ``None`` when
+``compute_tradability`` returned no band on that other side at all, never an invented or
+wrong-side band. It also carries ``bands_by_class`` -- a plain count of ``result["bands"]`` under
+the four fixed keys ``"A"``/``"B"``/``"C"``/``"unclassified"`` (a band with ``class: None`` counts
+under ``"unclassified"``), all four always present even at zero -- no grade, threshold, or quality
+number, a count only. Skip rows never carry either field, matching the basis/history/reference-close
+precedent exactly. A snapshot recorded BEFORE this addition simply has ranked rows that OMIT these
+two keys entirely -- the SAME append-only-row-content discipline the basis/history/reference-close
+fields established: never defaulted, never backfilled (``opposite_band`` ITSELF may legitimately be
+recorded as ``null`` on a NEW row, when the canonical return holds no band on the other side -- that
+is distinct from the ROW omitting the key entirely, which only a pre-iteration snapshot ever does).
+
 **No new ``Config`` field.** The screen store's directory resolves via ``resolve_desk_screen_dir``
 below -- a bare ``TAPEOLOGY_DESK_SCREEN_DIR``-env-var-or-sibling-of-``desk_universe_dir_resolved()``
 default (the ``edge_report_cache.resolve_cache_db_path`` pattern) -- never a ``desk_screen_dir``
@@ -249,6 +266,29 @@ def _select_best_band(bands: list[dict], close: float) -> dict:
     return min(bands, key=key)
 
 
+def _select_opposite_band(bands: list[dict], close: float, best_side: str) -> dict | None:
+    """The nearest band on the side of price ``best_side`` did NOT select (goal-desk-iter-18, J-14)
+    -- filtered from the SAME ``bands`` list ``_select_best_band`` already ran over, then selected
+    by the IDENTICAL tie-break tuple via ``min``'s own first-of-tie stability (no second, invented
+    tie-break rule). ``None`` when no band exists on the other side at all -- never a guessed or
+    wrong-side substitute."""
+    opposite_side_bands = [band for band in bands if band["side"] != best_side]
+    if not opposite_side_bands:
+        return None
+    return _select_best_band(opposite_side_bands, close)
+
+
+def _bands_by_class(bands: list[dict]) -> dict[str, int]:
+    """A plain per-class count of ``bands`` (goal-desk-iter-18, J-14) -- a band with ``class: None``
+    counts under ``"unclassified"``; all four keys are always present, even at zero. A count only --
+    no grade, threshold, weight, or quality number."""
+    counts = {"A": 0, "B": 0, "C": 0, "unclassified": 0}
+    for band in bands:
+        key = band["class"] if band["class"] is not None else "unclassified"
+        counts[key] += 1
+    return counts
+
+
 def _row_rank_key(row: dict) -> tuple[int, float, float, str]:
     """The FINAL cross-symbol ``rows`` order (TC-14): the identical selection tuple above, plus
     ``symbol`` ascending as the final tie-break."""
@@ -333,9 +373,10 @@ def compute_screen(
     assigns those): ``{screen_date, as_of, universe_snapshot_id, config_fingerprint,
     bar_store_signature, rows, skipped}``. Each RANKED row additionally carries ``basis_as_of``/
     ``basis_age_days`` (goal-desk-iter-9, J-08), ``history_sessions``/``history_start``
-    (goal-desk-iter-15, J-11), and ``reference_close`` (goal-desk-iter-17, J-13) -- see the module
-    docstring's "Basis disclosure", "History disclosure", and "Reference-close disclosure" sections;
-    skip rows never carry any of the five.
+    (goal-desk-iter-15, J-11), ``reference_close`` (goal-desk-iter-17, J-13), and
+    ``opposite_band``/``bands_by_class`` (goal-desk-iter-18, J-14) -- see the module docstring's
+    "Basis disclosure", "History disclosure", "Reference-close disclosure", and "Opposite-band
+    disclosure" sections; skip rows never carry any of the seven.
 
     ``progress``, if given, is called after EACH member with ``{"symbol": symbol}`` (the caller
     tracks its own done/total counters -- the ``desk_topup_compute.run_topup`` precedent).
@@ -383,6 +424,7 @@ def compute_screen(
                 bar_store, symbol, result["basis_as_of"]
             )
             best = _select_best_band(result["bands"], close)
+            opposite = _select_opposite_band(result["bands"], close, best["side"])
             rows.append(
                 {
                     "symbol": symbol,
@@ -399,6 +441,19 @@ def compute_screen(
                     "history_sessions": history_sessions,
                     "history_start": history_start,
                     "reference_close": close,
+                    "opposite_band": (
+                        {
+                            "side": opposite["side"],
+                            "band_class": opposite["class"],
+                            "price_low": opposite["price_low"],
+                            "price_high": opposite["price_high"],
+                            "band_score": opposite["quality_score"],
+                            "distance_bps": _distance_bps(opposite, close),
+                        }
+                        if opposite is not None
+                        else None
+                    ),
+                    "bands_by_class": _bands_by_class(result["bands"]),
                 }
             )
 
diff --git a/apps/backend/tests/test_desk_screen.py b/apps/backend/tests/test_desk_screen.py
index 05a9256..3cc6d45 100644
--- a/apps/backend/tests/test_desk_screen.py
+++ b/apps/backend/tests/test_desk_screen.py
@@ -32,11 +32,13 @@ from app.research.desk_screen import (
     screen_as_of,
 )
 from app.research.desk_screen import (
+    _bands_by_class,
     _basis_age_days,
     _distance_bps,
     _epoch,
     _row_rank_key,
     _select_best_band,
+    _select_opposite_band,
 )
 from app.research.desk_universe import UniverseStore
 
@@ -230,6 +232,69 @@ def test_select_best_band_null_class_ranks_below_every_graded_class():
     assert best is graded
 
 
+# ==================================================================================================
+# opposite-band selection + bands-by-class count (goal-desk-iter-18, J-14) -- pure-function unit
+# tests, mirroring the best-band-selection suite immediately above.
+# ==================================================================================================
+
+
+def test_select_opposite_band_returns_the_nearest_band_on_the_other_side():
+    best_side = _band("resistance", 105.0, 106.0, "A", 1.0)
+    near_opposite = _band("support", 99.0, 99.5, "B", 5.0)
+    far_opposite = _band("support", 80.0, 81.0, "B", 5.0)
+    opposite = _select_opposite_band([best_side, near_opposite, far_opposite], 100.0, "resistance")
+    assert opposite is near_opposite
+
+
+def test_select_opposite_band_is_null_when_no_band_exists_on_the_other_side():
+    """TC-8: an honest ``None`` -- never an invented or wrong-side band -- when every served band
+    shares the SAME side as the row's own selected ``best`` band."""
+    resistance_only = [
+        _band("resistance", 101.0, 102.0, "A", 10.0),
+        _band("resistance", 110.0, 111.0, "B", 1.0),
+    ]
+    assert _select_opposite_band(resistance_only, 100.0, "resistance") is None
+
+
+def test_select_opposite_band_prefers_higher_class_over_closer_distance():
+    """The opposite selection reuses `_select_best_band`'s IDENTICAL tie-break tuple -- class rank
+    outranks distance, exactly as the best-band suite above already proves for the same-side case."""
+    best_side = _band("resistance", 105.0, 106.0, "A", 1.0)
+    close_but_low_class = _band("support", 99.9, 99.95, "C", 500.0)
+    far_but_high_class = _band("support", 90.0, 91.0, "A", 1.0)
+    opposite = _select_opposite_band(
+        [best_side, close_but_low_class, far_but_high_class], 100.0, "resistance"
+    )
+    assert opposite is far_but_high_class
+
+
+def test_select_opposite_band_exact_tie_keeps_the_served_order_first_item():
+    """TC-9: tie-break stability across repeated calls on a tied fixture -- `min`'s own
+    first-of-tie order (never a second, invented tie-break), mirroring
+    `test_select_best_band_exact_tie_keeps_the_served_order_first_item` for the opposite side."""
+    best_side = _band("resistance", 105.0, 106.0, "A", 1.0)
+    a = _band("support", 99.0, 99.0, "B", 5.0)
+    b = _band("support", 99.0, 99.0, "B", 5.0)
+    assert _select_opposite_band([best_side, a, b], 100.0, "resistance") is a
+    assert _select_opposite_band([best_side, b, a], 100.0, "resistance") is b
+    # Repeated calls on the identical input return the identical result every time.
+    assert _select_opposite_band([best_side, a, b], 100.0, "resistance") is a
+    assert _select_opposite_band([best_side, a, b], 100.0, "resistance") is a
+
+
+def test_bands_by_class_counts_each_class_including_zero_and_unclassified():
+    bands = [
+        _band("resistance", 105.0, 106.0, "A", 1.0),
+        _band("resistance", 110.0, 111.0, "A", 1.0),
+        _band("support", 90.0, 91.0, None, 1.0),
+    ]
+    assert _bands_by_class(bands) == {"A": 2, "B": 0, "C": 0, "unclassified": 1}
+
+
+def test_bands_by_class_empty_list_is_all_zero():
+    assert _bands_by_class([]) == {"A": 0, "B": 0, "C": 0, "unclassified": 0}
+
+
 # ==================================================================================================
 # ScreenStore discipline -- mirrors test_desk_universe.py's store-level suite exactly
 # ==================================================================================================
@@ -557,6 +622,45 @@ def test_aapl_row_cross_checks_byte_identical_to_the_real_tradability_route(ctx,
     ) / expected_close * 10_000.0
     assert row["distance_bps"] == pytest.approx(expected_distance)
 
+    # goal-desk-iter-18 (J-14) TC-2/TC-3/TC-4, against the REAL route rather than an injected band
+    # list: `bands_by_class` is a recount of the SAME served `bands`, and `opposite_band` -- when
+    # present -- is a real, uniquely-identifiable served band on the OTHER side whose distance
+    # reproduces the row's own `_distance_bps` formula against the row's own `reference_close`.
+    served_counts = {"A": 0, "B": 0, "C": 0, "unclassified": 0}
+    for band in body["bands"]:
+        served_counts[band["class"] if band["class"] is not None else "unclassified"] += 1
+    assert row["bands_by_class"] == served_counts
+    assert sum(row["bands_by_class"].values()) == len(body["bands"])
+
+    served_opposite = [b for b in body["bands"] if b["side"] != row["side"]]
+    if row["opposite_band"] is None:
+        assert served_opposite == [], (
+            "opposite_band may only be null when the canonical route served NO band on the other side"
+        )
+    else:
+        opposite_matching = [
+            b for b in served_opposite
+            if b["price_low"] == row["opposite_band"]["price_low"]
+            and b["price_high"] == row["opposite_band"]["price_high"]
+        ]
+        assert len(opposite_matching) == 1, (
+            "the disclosed opposite band must be a real, uniquely-identifiable served band on the "
+            "side the row's own band is NOT on"
+        )
+        served_opp = opposite_matching[0]
+        assert row["opposite_band"]["side"] == served_opp["side"] != row["side"]
+        assert row["opposite_band"]["band_class"] == served_opp["class"]
+        assert row["opposite_band"]["band_score"] == served_opp["quality_score"]
+        expected_opposite_distance = abs(
+            (
+                served_opp["price_low"]
+                if served_opp["side"] == "resistance"
+                else served_opp["price_high"]
+            )
+            - row["reference_close"]
+        ) / row["reference_close"] * 10_000.0
+        assert row["opposite_band"]["distance_bps"] == pytest.approx(expected_opposite_distance)
+
 
 def test_msft_partial_coverage_still_resolves_a_ranked_row_with_honest_coverage(ctx):
     """TC-2: MSFT (real symbol, 1h+1d bars only -- never 1w/4h) is never mis-skipped merely for
@@ -1188,6 +1292,229 @@ def test_a_legacy_row_recorded_without_reference_close_serves_it_absent_never_ba
     assert "reference_close" not in row
 
 
+# ==================================================================================================
+# opposite-band disclosure (goal-desk-iter-18, J-14) -- opposite_band: the nearest band on the side
+# of price the row's own selected band did NOT choose; bands_by_class: a per-class count of every
+# band compute_tradability returned for that symbol. Both drawn from the SAME result["bands"] list
+# already held for `reference_close`/`distance_bps` -- zero new BarStore read, zero second
+# compute_tradability call.
+# ==================================================================================================
+
+
+def test_opposite_band_golden_near_far_and_null_class_rows(ctx, monkeypatch):
+    """TC-1/TC-2/TC-3/TC-4: three controlled ranked rows -- one whose nearest opposite-side band is
+    within 25 bps, one whose nearest opposite-side band is beyond 1,000 bps, and one whose nearest
+    opposite-side band carries `class: None` -- each proving `opposite_band`'s fields are copied
+    verbatim from `compute_tradability`'s own served band and `bands_by_class` sums to the symbol's
+    total band count. Mirrors the `test_reference_close_golden_in_band_and_out_of_band_rows`
+    precedent: `compute_tradability` is monkeypatched to return exact, controlled bands so all three
+    scenarios are deterministic, while the reference CLOSE itself is real -- resolved by the real
+    `_resolve_reference_close_and_history` walk over a synthetic daily bar seeded through the real
+    `BarStore`, never hand-set on the row."""
+    import app.research.desk_screen as desk_screen_module
+
+    universe_store, bar_store, bar_index, dataset_store = ctx
+    near_bar = _daily_bars("ABBV", start=date(2026, 6, 18), count=1)[0]
+    far_bar = _daily_bars("ACN", start=date(2026, 6, 18), count=1)[0]
+    null_bar = _daily_bars("ADBE", start=date(2026, 6, 18), count=1)[0]
+    _seed_daily_bars(bar_store, bar_index, [near_bar])
+    _seed_daily_bars(bar_store, bar_index, [far_bar])
+    _seed_daily_bars(bar_store, bar_index, [null_bar])
+
+    near_basis = _iso_of(near_bar.epoch)
+    far_basis = _iso_of(far_bar.epoch)
+    null_basis = _iso_of(null_bar.epoch)
+
+    # ABBV: best band = resistance A right at close (distance_bps 0.0, always wins on class alone);
+    # opposite (support) band ~20 bps below close -- within the 25 bps evidence floor TC-12 names.
+    abbv_best = _band("resistance", near_bar.close, near_bar.close + 5.0, "A", 10.0)
+    abbv_opposite = _band("support", near_bar.close - 1.0, near_bar.close - 0.2, "B", 5.0)
+
+    # ACN: best band = resistance A right at close; opposite (support) band $20 below close --
+    # ~1,990 bps, well beyond the 1,000 bps evidence floor.
+    acn_best = _band("resistance", far_bar.close, far_bar.close + 5.0, "A", 10.0)
+    acn_opposite = _band("support", far_bar.close - 25.0, far_bar.close - 20.0, "C", 3.0)
+
+    # ADBE: best band = resistance A right at close; the ONLY opposite (support) band carries
+    # `class: None` -- proving `bands_by_class` counts it under "unclassified" and `opposite_band`
+    # still discloses it (an ungraded band is still a real, servable disclosure).
+    adbe_best = _band("resistance", null_bar.close, null_bar.close + 5.0, "A", 10.0)
+    adbe_opposite = _band("support", null_bar.close - 2.0, null_bar.close - 1.0, None, 1.0)
+
+    original = desk_screen_module.compute_tradability
+
+    def _tracked(store, symbol, as_of_epoch, config):
+        if symbol == "ABBV":
+            return {"no_bar_series_for_symbol": False, "basis_as_of": near_basis, "bands": [abbv_best, abbv_opposite]}
+        if symbol == "ACN":
+            return {"no_bar_series_for_symbol": False, "basis_as_of": far_basis, "bands": [acn_best, acn_opposite]}
+        if symbol == "ADBE":
+            return {"no_bar_series_for_symbol": False, "basis_as_of": null_basis, "bands": [adbe_best, adbe_opposite]}
+        return original(store, symbol, as_of_epoch, config)
+
+    monkeypatch.setattr(desk_screen_module, "compute_tradability", _tracked)
+
+    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
+    by_symbol = {r["symbol"]: r for r in screen["rows"]}
+
+    abbv_row = by_symbol["ABBV"]
+    assert abbv_row["opposite_band"] == {
+        "side": "support",
+        "band_class": "B",
+        "price_low": abbv_opposite["price_low"],
+        "price_high": abbv_opposite["price_high"],
+        "band_score": abbv_opposite["quality_score"],
+        "distance_bps": _distance_bps(abbv_opposite, near_bar.close),
+    }
+    assert abbv_row["opposite_band"]["distance_bps"] <= 25.0
+    assert abbv_row["bands_by_class"] == {"A": 1, "B": 1, "C": 0, "unclassified": 0}
+    assert sum(abbv_row["bands_by_class"].values()) == 2
+
+    acn_row = by_symbol["ACN"]
+    assert acn_row["opposite_band"] == {
+        "side": "support",
+        "band_class": "C",
+        "price_low": acn_opposite["price_low"],
+        "price_high": acn_opposite["price_high"],
+        "band_score": acn_opposite["quality_score"],
+        "distance_bps": _distance_bps(acn_opposite, far_bar.close),
+    }
+    assert acn_row["opposite_band"]["distance_bps"] > 1000.0
+    assert acn_row["bands_by_class"] == {"A": 1, "B": 0, "C": 1, "unclassified": 0}
+    assert sum(acn_row["bands_by_class"].values()) == 2
+
+    adbe_row = by_symbol["ADBE"]
+    assert adbe_row["opposite_band"] == {
+        "side": "support",
+        "band_class": None,
+        "price_low": adbe_opposite["price_low"],
+        "price_high": adbe_opposite["price_high"],
+        "band_score": adbe_opposite["quality_score"],
+        "distance_bps": _distance_bps(adbe_opposite, null_bar.close),
+    }
+    assert adbe_row["bands_by_class"] == {"A": 1, "B": 0, "C": 0, "unclassified": 1}
+    assert sum(adbe_row["bands_by_class"].values()) == 2
+
+
+def test_row_order_is_unchanged_by_the_opposite_band_addition(ctx):
+    """TC-5: `_row_rank_key` is computed entirely from `band_class`/`distance_bps`/`band_score`/
+    `symbol` -- unchanged this iteration (verify via `git diff`, appearing only as unchanged
+    CONTEXT) -- neither `opposite_band` nor `bands_by_class` touches it. The ranked-row symbol
+    SEQUENCE for this same fixture spread is exactly the sort of `_row_rank_key` over the SAME rows,
+    confirming both new fields are a pure addition to row CONTENT, never a reordering."""
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
+def test_opposite_band_stays_byte_identical_on_a_recompute_under_identical_pins(ctx, tmp_path):
+    """TC-6: mirrors `test_reference_close_stays_byte_identical_on_a_recompute_under_identical_pins`
+    for `opposite_band`/`bands_by_class` specifically -- a screen recorded once, then a FRESH
+    computation under identical pins, is refused a second write, and the content already on disk
+    (read back via `list()`) is byte-identical to the second (unrecorded) computation's
+    `opposite_band`/`bands_by_class` on every ranked row."""
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
+    assert aapl_row["opposite_band"] == expected_aapl_row["opposite_band"]
+    assert aapl_row["bands_by_class"] == expected_aapl_row["bands_by_class"]
+
+
+def test_a_legacy_row_recorded_without_opposite_band_fields_serves_them_absent_never_backfilled(
+    tmp_path,
+):
+    """TC-7: the exact shape every screen snapshot recorded BEFORE this iteration has -- ranked rows
+    that OMIT `opposite_band`/`bands_by_class` entirely (never merely present-as-`null`) -- mirrors
+    the basis/history/reference-close legacy-row precedents for the two new fields. `_record`'s own
+    default row carries no such keys at all, so this is true by construction; this test pins that
+    contract so a future change cannot silently start defaulting or backfilling legacy rows on read."""
+    store = ScreenStore(tmp_path / "screen")
+    _record(store)  # `_record`'s own default row carries neither key at all
+
+    records, errors = store.list()
+    assert errors == []
+    row = records[0]["rows"][0]
+    assert "opposite_band" not in row
+    assert "bands_by_class" not in row
+
+
+def test_opposite_band_and_bands_by_class_add_zero_extra_compute_tradability_or_merged_bars_calls(
+    ctx, monkeypatch
+):
+    """TC-10: `opposite_band`/`bands_by_class` are pure selections/counts over the SAME
+    `result["bands"]` a symbol's SINGLE `compute_tradability` call already returned -- mirrors
+    `test_history_fields_add_zero_extra_merged_bars_calls`'s own call-count-guard style, extended to
+    also assert `compute_tradability` itself is invoked exactly once per symbol in a full screen
+    walk (never a second call to derive the opposite side), and that the derivation adds ZERO
+    `BarStore.merged_bars(symbol, "1d")` calls beyond what iteration 17 (`reference_close`/history)
+    already required."""
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
+    assert any(r["symbol"] == "AAPL" for r in screen["rows"])
+
+    assert tradability_calls.count("AAPL") == 1, (
+        "opposite_band/bands_by_class must be derived from the symbol's single existing "
+        "compute_tradability call, never a second call"
+    )
+    full_1d_calls = sum(1 for symbol, tf in merged_calls if symbol == "AAPL" and tf == "1d")
+    assert full_1d_calls == baseline_1d_calls + 1, (
+        "opposite_band/bands_by_class must add ZERO extra merged_bars calls beyond what "
+        "iteration 17's reference_close/history disclosure already required"
+    )
+
+
 # ==================================================================================================
 # screen ?id= read (goal-desk-iter-16, J-12) -- individual addressability, including an EARLIER
 # same-`screen_date` recording that `?date=` (which always resolves `matching[-1]`) can never reach.
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index c0d8c3e..7a660a0 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -17,6 +17,10 @@ not see:
       value via arithmetic on ``row.distance_bps``/``row.price_low``/``row.price_high`` -- the new
       ``band`` column/tooltip line renders ``row.reference_close`` beside the row's own
       ``price_low``/``price_high``, never a value recomputed from them client-side.
+  (d) goal-desk-iter-18 (J-14) TC-11 -- the SAME arithmetic guard, extended to also cover
+      ``row.opposite_band``'s ``distance_bps``/``price_low``/``price_high``/``band_score`` and
+      ``row.bands_by_class``'s ``A``/``B``/``C``/``unclassified`` counts -- the new ``opposite``
+      column/tooltip line renders these fields verbatim, never a derived distance, price, or count.
 
 A guard that can never fail proves nothing -- each carries a seeded counter-test proving the
 detection logic itself actually catches a violation (the ``test_copy_discipline.py``
@@ -129,23 +133,33 @@ def test_structure_prefill_guard_can_fail_on_a_seeded_violation():
 # (`row.reference_close`, `row.price_low`-`row.price_high`) is a verbatim render of already-served
 # values, never a client-side recomputation of the very number `reference_close` exists to disclose
 # instead of forcing an operator (or agent) to invert `distance_bps` against a band edge.
-_PRICE_ARITHMETIC_FIELDS = r"row\.(distance_bps|price_low|price_high)"
+# goal-desk-iter-18 (J-14): extended (never duplicated -- the iter-17 direct precedent) to also
+# cover `row.opposite_band.*`'s distance/price/score fields and `row.bands_by_class.*`'s per-class
+# counts -- the new `opposite` column/tooltip line renders these verbatim too, never a derived
+# distance, price, or count (e.g. a client-side "total bands" sum or an implied spread).
+_PRICE_ARITHMETIC_FIELDS = (
+    r"row\.(?:distance_bps|price_low|price_high"
+    r"|opposite_band\.(?:distance_bps|price_low|price_high|band_score)"
+    r"|bands_by_class\.(?:A|B|C|unclassified))"
+)
 _PRICE_ARITHMETIC_PATTERN = re.compile(
     rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
 )
 
 
 def test_desk_page_never_derives_a_price_via_arithmetic_on_distance_or_band_edges():
-    """TC-8: scans `apps/frontend/app/desk/page.tsx`'s source for any expression combining
-    `row.distance_bps`/`row.price_low`/`row.price_high` with an arithmetic operator. The new
-    `band` column/tooltip line (goal-desk-iter-17, J-13) renders `row.reference_close` beside
-    `row.price_low`/`row.price_high` as two side-by-side values, never a derived third one."""
+    """TC-8/TC-11: scans `apps/frontend/app/desk/page.tsx`'s source for any expression combining
+    `row.distance_bps`/`row.price_low`/`row.price_high` (goal-desk-iter-17, J-13) or
+    `row.opposite_band.*`/`row.bands_by_class.*` (goal-desk-iter-18, J-14) with an arithmetic
+    operator. The `band` column/tooltip line renders `row.reference_close` beside
+    `row.price_low`/`row.price_high`, and the new `opposite` column/tooltip line renders
+    `row.opposite_band`/`row.bands_by_class` verbatim -- never a derived value."""
     source = _DESK_PAGE.read_text()
     hits = _PRICE_ARITHMETIC_PATTERN.findall(source)
     assert not hits, (
-        f"apps/frontend/app/desk/page.tsx derives a price value via arithmetic on distance_bps/"
-        f"price_low/price_high ({hits}) -- the page must render only what "
-        "GET /research/desk/screen already served, never recompute a price client-side"
+        f"apps/frontend/app/desk/page.tsx derives a value via arithmetic on distance_bps/price_low/"
+        f"price_high/opposite_band/bands_by_class ({hits}) -- the page must render only what "
+        "GET /research/desk/screen already served, never recompute a value client-side"
     )
 
 
@@ -153,3 +167,17 @@ def test_desk_page_price_arithmetic_guard_can_fail_on_a_seeded_violation():
     """The lint CAN fail -- a lint that cannot fail proves nothing."""
     seeded_source = "const implied = row.price_high - row.reference_close;"
     assert _PRICE_ARITHMETIC_PATTERN.search(seeded_source) is not None
+
+
+def test_desk_page_price_arithmetic_guard_catches_opposite_band_and_bands_by_class_arithmetic():
+    """TC-11 (goal-desk-iter-18, J-14) counter-test: the extended guard also catches arithmetic on
+    the new `opposite_band`/`bands_by_class` fields, not just the pre-existing distance_bps/
+    price_low/price_high ones."""
+    seeded_opposite = "const gap = row.opposite_band.price_high - row.price_high;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_opposite) is not None
+
+    seeded_score = "const combined = row.opposite_band.band_score + row.band_score;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_score) is not None
+
+    seeded_bands_by_class = "const total = row.bands_by_class.A + row.bands_by_class.B;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_bands_by_class) is not None
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index 6d57d73..75253e8 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -517,6 +517,71 @@ async def test_desk_screen_reference_close_field_proxies_verbatim(mcp_env, backe
     )
 
 
+@pytest.mark.anyio
+async def test_desk_screen_opposite_band_and_bands_by_class_fields_proxy_verbatim(mcp_env, backend_paths):
+    """goal-desk-iter-18 (J-14) TC-14: `opposite_band`/`bands_by_class` -- `desk_screen.py`'s two
+    newest ranked-row fields -- are proxied byte-identical through both the `desk_screen` tool
+    (no-arg) and `get_endpoint`'s existing `/research/` allowlist prefix (`?date=`), with ZERO MCP
+    code change -- the same proxy contract every prior `desk_screen` row-field addition (basis/
+    history/reference-close) already covers automatically. Seeded under its own distinct date so
+    this test passes standalone."""
+    screen_dir = Path(backend_paths["TAPEOLOGY_DESK_SCREEN_DIR"])
+    ScreenStore(screen_dir).record(
+        screen_date="2026-07-30",
+        as_of="2026-07-30T21:00:00Z",
+        universe_snapshot_id="universe-2026-07-25-817cc184bbb3",
+        config_fingerprint=CONFIG.config_fingerprint(),
+        bar_store_signature="mcp-test-opposite-band-signature",
+        rows=[
+            {
+                "symbol": "AMZN",
+                "side": "resistance",
+                "band_class": "A",
+                "distance_bps": 5.0,
+                "band_score": 4.2,
+                "price_low": 200.0,
+                "price_high": 202.0,
+                "coverage": {"1d": {"has_bars": True, "latest_window_end_utc": "2026-07-30T00:00:00Z"}},
+                "tick_evidence": True,
+                "reference_close": 199.9,
+                "opposite_band": {
+                    "side": "support",
+                    "band_class": "B",
+                    "price_low": 190.0,
+                    "price_high": 191.0,
+                    "band_score": 2.1,
+                    "distance_bps": 452.2,
+                },
+                "bands_by_class": {"A": 1, "B": 1, "C": 0, "unclassified": 0},
+            }
+        ],
+        skipped=[],
+    )
+
+    result = await call_tool("desk_screen", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/screen", timeout=5.0)
+    assert rest.status_code == 200
+    row = rest.json()["latest"]["rows"][0]
+    assert row["opposite_band"]["band_class"] == "B"
+    assert row["bands_by_class"] == {"A": 1, "B": 1, "C": 0, "unclassified": 0}
+    assert result.isError is False
+    assert result.content[0].text.encode("utf-8") == rest.content, (
+        "opposite_band/bands_by_class not byte-identical via the desk_screen tool"
+    )
+
+    date_path = "/research/desk/screen?date=2026-07-30"
+    result = await call_tool("get_endpoint", {"path": date_path})
+    rest = httpx.get(f"{mcp_env}{date_path}", timeout=5.0)
+    assert rest.status_code == 200
+    row = rest.json()["screen"]["rows"][0]
+    assert row["opposite_band"]["band_class"] == "B"
+    assert row["bands_by_class"] == {"A": 1, "B": 1, "C": 0, "unclassified": 0}
+    assert result.isError is False
+    assert result.content[0].text.encode("utf-8") == rest.content, (
+        "opposite_band/bands_by_class not byte-identical via get_endpoint"
+    )
+
+
 @pytest.mark.anyio
 async def test_datasets_tool_byte_identical_on_a_non_empty_live_list(mcp_env, backend_paths):
     """J-02 flips ``datasets`` from honest 404 to live data with ZERO MCP code changes: after
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 7c1ecda..a5874f8 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -112,6 +112,17 @@ import { fmt } from "@/lib/format";
 // "the price is inside the wall" is a fact visible on screen instead of arithmetic recovered by
 // inverting `distance_bps` against a band edge. Read-only render, zero new endpoint, zero new
 // control — `reference_close` rides the already-fetched `GET /research/desk/screen` response.
+//
+// goal-desk-iter-18 (J-14): a new `opposite` column on the ranked-rows table — the row's own
+// `opposite_band` (the nearest band on the side of price the row's selected band did NOT choose),
+// rendered beside the existing columns with the same rounded-display split (full precision is not
+// carried in the tooltip for this field this iteration — only `bands_by_class` is, see below), an
+// honest "no band on the other side" for a recorded `null`, and the established legacy-absent copy
+// "opposite wall not recorded in this snapshot" for a pre-iteration row. Plus one more composite
+// drill-in tooltip line carrying the row's full-precision `bands_by_class` (a per-class count of
+// every band the canonical tradability computation returned for the symbol). Read-only render,
+// zero new endpoint, zero new control, zero client-side arithmetic — both fields ride the
+// already-fetched `GET /research/desk/screen` response verbatim.
 
 const NUMERIC_CELL = "px-2 py-1.5 text-right font-mono text-xs text-slate-200 whitespace-nowrap";
 const HEADER_CELL = "px-2 py-1 text-right text-[11px] font-medium text-slate-500";
@@ -257,6 +268,13 @@ function hasNoCoverageAtAll(coverage: Record<string, { has_bars: boolean }>): bo
 // beside its own `price_low`/`price_high` band range (the visible "band" cell below shows the
 // rounded values, the SAME split as distance/score/basis/history) -- a legacy row (recorded before
 // this iteration) has the key absent, `== null` catches both `undefined` and `null`.
+// era-desk-iter-18 (J-14): the SAME tooltip also carries the row's full-precision `bands_by_class`
+// -- a per-class count of every band the canonical tradability computation returned for the symbol
+// (the visible "opposite" cell below shows only the nearest opposite band, never this per-class
+// breakdown). A legacy row (recorded before this iteration) has the key entirely absent
+// (`undefined`, not `null`) -- `=== undefined` catches exactly that (unlike the `== null` fields
+// above, `bands_by_class` itself is never legitimately recorded as `null` on a new row, only absent
+// on a legacy one, so the stricter check is the honest one here).
 function deskRowDrillInTitle(row: DeskScreenRow): string {
   const coverageLines = Object.entries(row.coverage)
     .map(([timeframe, tf]) => `${timeframe} window last requested: ${tf.latest_window_end_utc ?? "never"}`)
@@ -277,7 +295,11 @@ function deskRowDrillInTitle(row: DeskScreenRow): string {
     row.reference_close == null
       ? `band ${row.price_low}–${row.price_high} · close not recorded in this snapshot`
       : `band ${row.price_low}–${row.price_high} · close ${row.reference_close}`;
-  return `distance ${row.distance_bps} bps · score ${row.band_score} · ${basisLine} · ${historyLine} · ${bandLine}${
+  const bandsByClassLine =
+    row.bands_by_class === undefined
+      ? "bands by class not recorded in this snapshot"
+      : `bands by class A ${row.bands_by_class.A} · B ${row.bands_by_class.B} · C ${row.bands_by_class.C} · unclassified ${row.bands_by_class.unclassified}`;
+  return `distance ${row.distance_bps} bps · score ${row.band_score} · ${basisLine} · ${historyLine} · ${bandLine} · ${bandsByClassLine}${
     coverageLines ? ` · ${coverageLines}` : ""
   }`;
 }
@@ -385,6 +407,23 @@ function DeskRow({ row, asOf }: { row: DeskScreenRow; asOf: string }) {
           ? `band ${fmt(row.price_low)}–${fmt(row.price_high)} · close not recorded in this snapshot`
           : `band ${fmt(row.price_low)}–${fmt(row.price_high)} · close ${fmt(row.reference_close)}`}
       </td>
+      {/* era-desk-iter-18 (J-14): the nearest band on the side of price the row's OWN selected band
+          did NOT choose -- descriptive only, rounded display (full precision for this field is not
+          carried in the tooltip this iteration; the tooltip instead gains the row's `bands_by_class`
+          breakdown, see `deskRowDrillInTitle` above). Three distinguishable states: a populated
+          `opposite_band` (`opposite <side> <class> <low>–<high> · <distance> bps`), an honest
+          "no band on the other side" for a recorded `null` (the canonical band computation served
+          no band on that side at all), and the established legacy-absent copy "opposite wall not
+          recorded in this snapshot" for a row from before this iteration (`undefined`, not `null`). */}
+      <td className={LABEL_CELL} data-testid="desk-row-opposite">
+        {row.opposite_band === undefined
+          ? "opposite wall not recorded in this snapshot"
+          : row.opposite_band === null
+            ? "no band on the other side"
+            : `opposite ${row.opposite_band.side} ${row.opposite_band.band_class ?? "unclassified"} ${fmt(
+                row.opposite_band.price_low
+              )}–${fmt(row.opposite_band.price_high)} · ${fmt(row.opposite_band.distance_bps)} bps`}
+      </td>
     </tr>
   );
 }
@@ -415,6 +454,7 @@ function DeskRowsTable({ rows, asOf }: { rows: DeskScreenRow[]; asOf: string })
             <th className={HEADER_CELL_LEFT}>basis</th>
             <th className={HEADER_CELL_LEFT}>history</th>
             <th className={HEADER_CELL_LEFT}>band</th>
+            <th className={HEADER_CELL_LEFT}>opposite</th>
           </tr>
         </thead>
         <tbody>
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index e970b40..631460a 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -812,6 +812,17 @@ export type EdgeReportPayload = EdgeReportResponse | EdgeReportNotComputed;
 // presence contract as basis/history: always non-null on a NEWLY computed ranked row, entirely
 // ABSENT (not `null`) on a row recorded before this iteration -- callers must check
 // `row.reference_close == null` (loose equality).
+// era-desk-iter-18 (J-14) -- opposite-band disclosure: the nearest band on the side of price the
+// row's own selected band did NOT choose (`opposite_band`, itself nullable when
+// `compute_tradability` served no band on that other side at all), plus a per-class count of every
+// band `compute_tradability` returned for that symbol (`bands_by_class`) -- both selected/counted
+// from the SAME `result["bands"]` list `desk_screen.py` already holds for `reference_close`, zero
+// new backend read. Same legacy-row presence contract as basis/history/reference-close: both keys
+// are always present (though `opposite_band` may itself legitimately be `null`) on a NEWLY computed
+// ranked row, entirely ABSENT (not merely `null`) on a row recorded before this iteration --
+// callers must check `row.opposite_band === undefined` / `row.bands_by_class === undefined` (a
+// present `opposite_band: null` is an honest "no band on the other side", distinct from "not
+// recorded in this snapshot").
 export interface DeskScreenRow {
   symbol: string;
   side: "support" | "resistance";
@@ -827,6 +838,15 @@ export interface DeskScreenRow {
   history_sessions: number | null;
   history_start: string | null;
   reference_close?: number | null;
+  opposite_band?: {
+    side: "support" | "resistance";
+    band_class: "A" | "B" | "C" | null;
+    price_low: number;
+    price_high: number;
+    band_score: number;
+    distance_bps: number;
+  } | null;
+  bands_by_class?: { A: number; B: number; C: number; unclassified: number };
 }
 
 // A member the screen walked but could not rank -- two honest, distinct reasons, never conflated:
```
