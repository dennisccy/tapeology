# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/tests/test_desk_topup_library_reach_guard.py b/apps/backend/tests/test_desk_topup_library_reach_guard.py
index 43397d2..2b9b93c 100644
--- a/apps/backend/tests/test_desk_topup_library_reach_guard.py
+++ b/apps/backend/tests/test_desk_topup_library_reach_guard.py
@@ -15,7 +15,19 @@ the DoD requires:
 
 A guard that can never fail proves nothing -- ``test_the_fallback_text_guard_can_fail_on_a_seeded_
 violation`` below seeds a violation (a second, drifted copy of the fallback string) and proves the
-same check catches it."""
+same check catches it.
+
+goal-desk-iter-34 (J-19 fix) extends this file with two more structural checks, each with its own
+seeded-violation counterpart:
+
+  (d) the grouping decision inside ``topupLibraryReach`` compares a DAY-TRUNCATED key
+      (``store_frozen_through_after.slice(0, 10)``), never the raw microsecond-precision string --
+      the iter-32/33 bug compared ``store_frozen_through_after === newestDate`` /
+      ``!== newestDate`` directly, so two pairs recorded on the SAME calendar day at different
+      times were miscounted as "earlier" relative to each other;
+  (e) the returned ``earlier`` array is capped at ``EARLIER_PAIRS_DISPLAY_CAP`` (20) entries while
+      a separate true-total value is preserved, so the heading can disclose an honest
+      "showing 20 of N" instead of silently truncating or rendering an unbounded list."""
 
 from __future__ import annotations
 
@@ -60,6 +72,36 @@ def test_the_reach_line_and_earlier_list_are_present_beside_the_window_basis_lin
     assert window_basis_idx < reach_idx < earlier_idx < failed_idx
 
 
+# goal-desk-iter-34 (J-19 fix, TC-4/TC-5): the "showing 20 of N" disclosure sits inside the
+# already-registered earlier-pairs block (between its heading and the failed-pairs block below),
+# is gated on the TRUE total exceeding the cap (never shown for a run whose true total is <= 20),
+# and the heading itself counts the true total, not the capped, rendered array length.
+def test_the_cap_disclosure_sits_inside_the_earlier_block_and_is_conditionally_gated():
+    source = _source()
+    earlier_idx = source.index('data-testid="desk-topup-run-latest-reach-earlier"')
+    failed_idx = source.index('data-testid="desk-topup-run-latest-failed"')
+    cap_note_idx = source.index('data-testid="desk-topup-run-latest-reach-earlier-cap"')
+    assert earlier_idx < cap_note_idx < failed_idx
+    # The cap note only renders when the true total exceeds the cap -- never unconditionally.
+    cap_note_line_start = source.rindex("\n", 0, cap_note_idx)
+    guard_clause = source[max(0, cap_note_line_start - 200) : cap_note_idx]
+    assert "earlierTotal > EARLIER_PAIRS_DISPLAY_CAP" in guard_clause
+    # The literal disclosure text carries the word "showing" plus both the shown and true counts.
+    assert "showing {libraryReach.earlier.length} of {libraryReach.earlierTotal}" in source
+    # The heading counts the TRUE total (earlierTotal), never the capped array's own length --
+    # otherwise a run with 25 true earlier pairs would print "Pairs recorded earlier (20)", quietly
+    # hiding the truncation instead of disclosing it.
+    assert "Pairs recorded earlier ({libraryReach.earlierTotal})" in source
+    assert "Pairs recorded earlier ({libraryReach.earlier.length})" not in source
+
+
+def test_the_cap_disclosure_guard_can_fail_on_a_seeded_violation():
+    """A guard that can never fail proves nothing -- a seeded heading that counts the CAPPED array
+    length instead of the true total (silently hiding truncation) is caught by the check above."""
+    seeded_source = "Pairs recorded earlier ({libraryReach.earlier.length})"
+    assert "Pairs recorded earlier ({libraryReach.earlierTotal})" not in seeded_source
+
+
 def test_topup_library_reach_returns_null_when_any_outcome_lacks_store_frozen_through_after():
     """``topupLibraryReach``'s own source slice (from its declaration to the NEXT top-level
     ``function`` declaration) structurally returns ``null`` on an absent field rather than
@@ -82,3 +124,94 @@ def test_the_fallback_text_guard_can_fail_on_a_seeded_violation():
     )
     literal_occurrences = seeded.count(f'"{_FALLBACK_TEXT}"')
     assert literal_occurrences != 1
+
+
+def _topup_library_reach_body(source: str) -> str:
+    marker = "function topupLibraryReach("
+    start = source.index(marker)
+    next_fn = source.index("\nfunction ", start + len(marker))
+    return source[start:next_fn]
+
+
+# goal-desk-iter-34 (J-19 fix, TC-2/TC-7): the grouping decision must compare a day-truncated key,
+# never the raw microsecond-precision `store_frozen_through_after` string directly against the
+# selected extreme -- that raw comparison is EXACTLY the iter-32/33 bug (confirmed live: 202 of 303
+# pairs shown under "Pairs recorded earlier" printed the SAME calendar day the reach line named as
+# newest). This check is a pure function of the source text so it can be re-run, unmodified,
+# against a seeded violation below.
+def _day_truncation_check(body: str) -> bool:
+    has_day_truncated_key = (
+        re.search(r"store_frozen_through_after[^\n;]*\.slice\(0,\s*10\)", body) is not None
+    )
+    has_raw_precision_bug = (
+        "store_frozen_through_after === newestDate" in body
+        or "store_frozen_through_after !== newestDate" in body
+    )
+    return has_day_truncated_key and not has_raw_precision_bug
+
+
+def test_topup_library_reach_groups_by_day_truncated_key_not_raw_timestamp():
+    """TC-2: two outcomes whose `store_frozen_through_after` values share a calendar day but carry
+    different microsecond timestamps must be grouped as the SAME day -- structurally proven by
+    (a) a day-truncated key derived from the field inside the function body, and (b) the absence
+    of the iter-32/33 bug's raw full-precision equality/inequality comparison against the selected
+    extreme."""
+    body = _topup_library_reach_body(_source())
+    assert _day_truncation_check(body) is True, (
+        "topupLibraryReach must derive a day-truncated key from store_frozen_through_after and use "
+        "it for every grouping/comparison decision -- comparing the raw timestamp directly against "
+        "newestDate is exactly the iter-32/33 bug"
+    )
+
+
+def test_day_truncation_guard_can_fail_on_a_seeded_violation():
+    """A guard that can never fail proves nothing -- a seeded copy of the ACTUAL iter-32/33 buggy
+    body (raw full-precision comparison, no day-truncated key) is caught by the same check above."""
+    seeded_body = (
+        "function topupLibraryReach(outcomes) {\n"
+        "  const newestDate = dates.reduce((max, d) => (d > max ? d : max), dates[0]);\n"
+        "  const newestCount = outcomes.filter((o) => o.store_frozen_through_after === newestDate)"
+        ".length;\n"
+        "  const earlier = outcomes.filter((o) => o.store_frozen_through_after !== newestDate);\n"
+        "}\n"
+    )
+    assert _day_truncation_check(seeded_body) is False
+
+
+# goal-desk-iter-34 (J-19 fix, TC-3/TC-8): the returned `earlier` array is capped at
+# `EARLIER_PAIRS_DISPLAY_CAP` entries while a separate true-total value survives, so the render can
+# disclose an honest "showing 20 of N" rather than truncating silently or rendering an unbounded
+# list (the iter-32/33 bug: 303 rows, no cap, no disclosure).
+def _cap_check(body: str) -> bool:
+    has_cap_constant = "EARLIER_PAIRS_DISPLAY_CAP" in body
+    has_capped_slice = re.search(r"\.slice\(0,\s*EARLIER_PAIRS_DISPLAY_CAP\)", body) is not None
+    has_separate_true_total = re.search(r"\bearlierTotal\b", body) is not None
+    return has_cap_constant and has_capped_slice and has_separate_true_total
+
+
+def test_topup_library_reach_caps_the_earlier_list_and_preserves_the_true_total():
+    """TC-3: the returned `earlier` array is capped at 20 entries; a separate true-total value is
+    preserved so the heading can disclose the real count honestly."""
+    source = _source()
+    assert "const EARLIER_PAIRS_DISPLAY_CAP = 20;" in source
+    body = _topup_library_reach_body(source)
+    assert _cap_check(body) is True, (
+        "topupLibraryReach must cap the returned `earlier` array at EARLIER_PAIRS_DISPLAY_CAP "
+        "entries while preserving the true total separately (earlierTotal) -- an uncapped list "
+        "silently renders every recorded pair, unbounded"
+    )
+
+
+def test_cap_guard_can_fail_on_a_seeded_violation():
+    """A guard that can never fail proves nothing -- a seeded uncapped `earlier` array (the
+    iter-32/33 bug: every pair earlier than the newest day, however many there are, with no
+    separate true-total tracked) is caught by the same check above."""
+    seeded_body = (
+        "function topupLibraryReach(outcomes) {\n"
+        "  const earlier = outcomes\n"
+        "    .filter((o) => o.store_frozen_through_after !== newestDate)\n"
+        "    .map((o) => ({ symbol: o.symbol, timeframe: o.timeframe }));\n"
+        "  return { newestDate, newestCount, earlier };\n"
+        "}\n"
+    )
+    assert _cap_check(seeded_body) is False
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index a451aa1..46fe418 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -875,32 +875,60 @@ function topupWindowBasisCounts(
 // LIBRARY_REACH_NOT_RECORDED fallback, never computed or backfilled.
 const LIBRARY_REACH_NOT_RECORDED = "library reach not recorded in this run";
 
+// goal-desk-iter-34 (J-19 fix) -- the "earlier" list renders at most this many rows; the TRUE
+// total is preserved separately (`earlierTotal`) so the heading can disclose an honest
+// "showing 20 of N" instead of silently truncating or rendering an unbounded, fourteen-screen-tall
+// list (the iter-32/33 bug: 303 rows, no cap, no disclosure).
+const EARLIER_PAIRS_DISPLAY_CAP = 20;
+
 function topupLibraryReach(
   outcomes: DeskTopupOutcome[],
 ): {
   newestDate: string | null;
   newestCount: number;
   earlier: { symbol: string; timeframe: string; date: string | null }[];
+  earlierTotal: number;
 } | null {
   if (outcomes.some((o) => o.store_frozen_through_after === undefined)) return null;
-  const dates = outcomes
-    .map((o) => o.store_frozen_through_after)
-    .filter((d): d is string => typeof d === "string");
-  if (dates.length === 0) {
+  // goal-desk-iter-34 (J-19 fix) -- one day-truncated grouping key per outcome, derived ONCE
+  // (the SAME calendar-day precision the render already displays via `.slice(0, 10)`). Every
+  // grouping/comparison decision below reads this key -- never the raw microsecond-precision
+  // timestamp -- so a pair recorded a few hours behind another pair on the IDENTICAL calendar day
+  // can never be misclassified as "earlier" purely because of its own sub-day precision (the
+  // iter-32/33 bug, reproduced live: 202 of 303 pairs shown under "Pairs recorded earlier" printed
+  // the SAME day the reach line named as newest).
+  const dayKeyed = outcomes.map((o) => ({
+    outcome: o,
+    day:
+      typeof o.store_frozen_through_after === "string"
+        ? o.store_frozen_through_after.slice(0, 10)
+        : null,
+  }));
+  const days = dayKeyed.map((d) => d.day).filter((d): d is string => d !== null);
+  if (days.length === 0) {
     // Every pair in this run holds no frozen bars at all -- an honest all-null run, never a
     // computed extreme over an empty set.
-    return { newestDate: null, newestCount: 0, earlier: [] };
+    return { newestDate: null, newestCount: 0, earlier: [], earlierTotal: 0 };
   }
-  const newestDate = dates.reduce((max, d) => (d > max ? d : max), dates[0]);
-  const newestCount = outcomes.filter((o) => o.store_frozen_through_after === newestDate).length;
-  const earlier = outcomes
-    .filter((o) => o.store_frozen_through_after !== newestDate)
-    .map((o) => ({
-      symbol: o.symbol,
-      timeframe: o.timeframe,
-      date: o.store_frozen_through_after ?? null,
+  const newestDay = days.reduce((max, d) => (d > max ? d : max), days[0]);
+  const newestCount = dayKeyed.filter((d) => d.day === newestDay).length;
+  // Full precision is kept for the RETURNED `newestDate` (the render already truncates it to a
+  // calendar day at display time via `.slice(0, 10)`) -- only the grouping decision above used the
+  // truncated key.
+  const newestOutcome = dayKeyed.find((d) => d.day === newestDay)!.outcome;
+  const earlierAll = dayKeyed
+    .filter((d) => d.day !== newestDay)
+    .map(({ outcome }) => ({
+      symbol: outcome.symbol,
+      timeframe: outcome.timeframe,
+      date: outcome.store_frozen_through_after ?? null,
     }));
-  return { newestDate, newestCount, earlier };
+  return {
+    newestDate: newestOutcome.store_frozen_through_after ?? null,
+    newestCount,
+    earlier: earlierAll.slice(0, EARLIER_PAIRS_DISPLAY_CAP),
+    earlierTotal: earlierAll.length,
+  };
 }
 
 function TopupRunRow({ meta }: { meta: DeskTopupRunMeta }) {
@@ -996,11 +1024,16 @@ function LatestTopupRunDetail({ run }: { run: DeskTopupRun }) {
           : `newest recorded reach ${libraryReach.newestDate.slice(0, 10)} · ` +
             `${libraryReach.newestCount} pair${libraryReach.newestCount === 1 ? "" : "s"} reach it`}
       </div>
-      {libraryReach !== null && libraryReach.earlier.length > 0 && (
+      {libraryReach !== null && libraryReach.earlierTotal > 0 && (
         <div data-testid="desk-topup-run-latest-reach-earlier">
           <h4 className="mb-1 text-[11px] font-medium text-slate-500">
-            Pairs recorded earlier ({libraryReach.earlier.length})
+            Pairs recorded earlier ({libraryReach.earlierTotal})
           </h4>
+          {libraryReach.earlierTotal > EARLIER_PAIRS_DISPLAY_CAP && (
+            <p data-testid="desk-topup-run-latest-reach-earlier-cap" className="mb-1 text-xs text-slate-400">
+              showing {libraryReach.earlier.length} of {libraryReach.earlierTotal}
+            </p>
+          )}
           <ul className="space-y-1">
             {libraryReach.earlier.map((item, index) => (
               <li
```
