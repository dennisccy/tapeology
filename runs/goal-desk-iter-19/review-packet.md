# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/app/research/desk_screen.py b/apps/backend/app/research/desk_screen.py
index 2c7c3dd..34b0ba4 100644
--- a/apps/backend/app/research/desk_screen.py
+++ b/apps/backend/app/research/desk_screen.py
@@ -87,14 +87,19 @@ this addition simply has ranked rows that OMIT this key entirely -- the SAME app
 discipline the basis/history fields established: never defaulted, never backfilled, never present
 as ``null``.
 
-**Opposite-band disclosure (goal-desk-iter-18, J-14).** Every RANKED row also carries
-``opposite_band`` -- the nearest band on the side of price the row's own selected ``best`` band did
-NOT choose, selected from the SAME ``result["bands"]`` list ``_select_best_band`` already ran over
-(zero new ``BarStore`` read, zero second ``compute_tradability`` call), ranked by the IDENTICAL
-``(class rank DESCENDING, distance_bps ascending, quality_score descending)`` tuple via ``min``'s
-own first-of-tie stability (see ``_select_opposite_band`` below) -- ``None`` when
-``compute_tradability`` returned no band on that other side at all, never an invented or
-wrong-side band. It also carries ``bands_by_class`` -- a plain count of ``result["bands"]`` under
+**Opposite-band disclosure (goal-desk-iter-18, J-14; tie-break corrected goal-desk-iter-19).**
+Every RANKED row also carries ``opposite_band`` -- the band GENUINELY NEAREST to price on the side
+the row's own selected ``best`` band did NOT choose, selected from the SAME ``result["bands"]``
+list ``_select_best_band`` already ran over (zero new ``BarStore`` read, zero second
+``compute_tradability`` call), ranked by its OWN distance-first tuple -- ``(distance_bps ascending,
+class rank DESCENDING, quality_score descending)`` -- via ``min``'s own first-of-tie stability (see
+``_select_opposite_band`` below) -- ``None`` when ``compute_tradability`` returned no band on that
+other side at all, never an invented or wrong-side band. **goal-desk-iter-19 correction:** iter-18
+shipped this selector delegating straight to ``_select_best_band``'s class-first tuple, which
+diverged from goal.md J-14 step 1's own distance-first wording on 2 of 63 real screen rows
+(HONA/META) -- ``_select_opposite_band`` now carries its OWN tie-break key, distinct from
+``_select_best_band``'s (whose same-side, class-first selection is unchanged). It also carries
+``bands_by_class`` -- a plain count of ``result["bands"]`` under
 the four fixed keys ``"A"``/``"B"``/``"C"``/``"unclassified"`` (a band with ``class: None`` counts
 under ``"unclassified"``), all four always present even at zero -- no grade, threshold, or quality
 number, a count only. Skip rows never carry either field, matching the basis/history/reference-close
@@ -267,15 +272,27 @@ def _select_best_band(bands: list[dict], close: float) -> dict:
 
 
 def _select_opposite_band(bands: list[dict], close: float, best_side: str) -> dict | None:
-    """The nearest band on the side of price ``best_side`` did NOT select (goal-desk-iter-18, J-14)
-    -- filtered from the SAME ``bands`` list ``_select_best_band`` already ran over, then selected
-    by the IDENTICAL tie-break tuple via ``min``'s own first-of-tie stability (no second, invented
-    tie-break rule). ``None`` when no band exists on the other side at all -- never a guessed or
-    wrong-side substitute."""
+    """The band GENUINELY NEAREST to price on the side ``best_side`` did NOT select
+    (goal-desk-iter-18, J-14; tie-break corrected goal-desk-iter-19) -- filtered from the SAME
+    ``bands`` list ``_select_best_band`` already ran over, then selected by its OWN distance-first
+    tie-break tuple ``(distance_bps ascending, class rank DESCENDING preference, quality_score
+    descending)`` via ``min``'s own first-of-tie stability (goal.md J-14 step 1, verbatim: "distance
+    ascending, then class rank descending ... then band_score descending, resolved by min's
+    first-of-tie stability over compute_tradability's own served order"). Deliberately its OWN
+    local key -- NOT a delegation to ``_select_best_band`` (whose class-first tuple governs only the
+    row's own same-side selection and is otherwise unchanged) -- because the two rules diverge
+    whenever a closer, lower-class opposite-side band competes with a farther, higher-class one
+    (iter-18 shipped the class-first delegation, which the iter-18 evaluator measured diverging on
+    2 of 63 real screen rows: HONA/META). ``None`` when no band exists on the other side at all --
+    never a guessed or wrong-side substitute."""
     opposite_side_bands = [band for band in bands if band["side"] != best_side]
     if not opposite_side_bands:
         return None
-    return _select_best_band(opposite_side_bands, close)
+
+    def key(band: dict) -> tuple[float, int, float]:
+        return (_distance_bps(band, close), -_CLASS_RANK[band["class"]], -band["quality_score"])
+
+    return min(opposite_side_bands, key=key)
 
 
 def _bands_by_class(bands: list[dict]) -> dict[str, int]:
diff --git a/apps/backend/tests/test_desk_screen.py b/apps/backend/tests/test_desk_screen.py
index 3cc6d45..3cd1bb3 100644
--- a/apps/backend/tests/test_desk_screen.py
+++ b/apps/backend/tests/test_desk_screen.py
@@ -256,16 +256,20 @@ def test_select_opposite_band_is_null_when_no_band_exists_on_the_other_side():
     assert _select_opposite_band(resistance_only, 100.0, "resistance") is None
 
 
-def test_select_opposite_band_prefers_higher_class_over_closer_distance():
-    """The opposite selection reuses `_select_best_band`'s IDENTICAL tie-break tuple -- class rank
-    outranks distance, exactly as the best-band suite above already proves for the same-side case."""
+def test_select_opposite_band_prefers_closer_distance_over_higher_class():
+    """TC-1 (goal-desk-iter-19 correction): the opposite selection uses its OWN distance-first
+    tie-break tuple -- distinct from `_select_best_band`'s class-first tuple, which governs only
+    the row's own same-side selection (`test_select_best_band_prefers_higher_class_over_closer_
+    distance` above, unchanged). goal.md J-14 step 1: "distance ascending, then class rank
+    descending... then band_score descending" -- a close-but-lower-class opposite-side band beats a
+    farther-but-higher-class one."""
     best_side = _band("resistance", 105.0, 106.0, "A", 1.0)
     close_but_low_class = _band("support", 99.9, 99.95, "C", 500.0)
     far_but_high_class = _band("support", 90.0, 91.0, "A", 1.0)
     opposite = _select_opposite_band(
         [best_side, close_but_low_class, far_but_high_class], 100.0, "resistance"
     )
-    assert opposite is far_but_high_class
+    assert opposite is close_but_low_class
 
 
 def test_select_opposite_band_exact_tie_keeps_the_served_order_first_item():
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-desk/telemetry.jsonl   | 13 +++++++++++++
 runs/goal-session-desk/trace/trace.jsonl |  3 +++
 2 files changed, 16 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
