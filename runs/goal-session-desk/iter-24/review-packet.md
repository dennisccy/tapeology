# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index 7a660a0..ed66dc4 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -1,7 +1,7 @@
 """era-desk-iter-6 (J-05) source-introspection guard tests -- the ``test_copy_discipline.py``
 pattern (read a frontend .tsx file as TEXT, assert on substrings; no browser, no runtime).
 
-Three guards, each proving something about the frontend a backend-only test suite otherwise could
+Guards, each proving something about the frontend a backend-only test suite otherwise could
 not see:
 
   (a) TC-5 -- ``apps/frontend/app/desk/page.tsx`` never references any of the structure-side
@@ -21,6 +21,12 @@ not see:
       ``row.opposite_band``'s ``distance_bps``/``price_low``/``price_high``/``band_score`` and
       ``row.bands_by_class``'s ``A``/``B``/``C``/``unclassified`` counts -- the new ``opposite``
       column/tooltip line renders these fields verbatim, never a derived distance, price, or count.
+  (e) goal-desk-iter-24 (J-16) TC-7 -- the ranked table's own layout REFLOW must not become a
+      layout that silently changes what's rendered: `rows` renders in served order only (no
+      `.sort(`/`.reverse(`/re-slice/comparator anywhere over `rows` -- the new `rank` cell is the
+      `.map` index, never a client-recomputed position), and every `data-testid` a shipped
+      journey's golden script or guard test depends on is still present in source after the
+      reflow.
 
 A guard that can never fail proves nothing -- each carries a seeded counter-test proving the
 detection logic itself actually catches a violation (the ``test_copy_discipline.py``
@@ -181,3 +187,172 @@ def test_desk_page_price_arithmetic_guard_catches_opposite_band_and_bands_by_cla
 
     seeded_bands_by_class = "const total = row.bands_by_class.A + row.bands_by_class.B;"
     assert _PRICE_ARITHMETIC_PATTERN.search(seeded_bands_by_class) is not None
+
+
+# goal-desk-iter-24 (J-16) TC-7 (a): the ranked table's own reflow adds a `rank` cell rendering
+# each row's own 1-based position in the served `rows` array (the `.map` index) -- this guard
+# proves the page never sorts, reverses, or re-slices `rows` to produce that position (or any
+# other display order) client-side. Matches a direct chain (`rows.sort(`), a spread-then-chain
+# (`[...rows].sort(`), and an intervening simple call (e.g. `rows.filter(...).sort(`) -- `.filter(`
+# alone (used elsewhere on this page only to COUNT rows, never to reorder or re-render them) is not
+# itself forbidden.
+_ROWS_REORDER_PATTERN = re.compile(
+    r"(?:\[\s*\.\.\.\s*rows\s*\]|\brows\b)\s*(?:\.\s*\w+\([^()]*\)\s*)*\.\s*(?:sort|reverse|slice)\s*\("
+)
+
+
+def test_desk_page_never_reorders_rows_client_side():
+    """TC-7: `rows` renders in the exact order `GET /research/desk/screen` served it in -- the
+    page never sorts, reverses, or re-slices it. The new `rank` cell renders each row's own
+    position in that SAME served order (the `.map` index), never a client-recomputed one."""
+    source = _DESK_PAGE.read_text()
+    match = _ROWS_REORDER_PATTERN.search(source)
+    assert match is None, (
+        f"apps/frontend/app/desk/page.tsx reorders `rows` client-side ({match.group(0)!r}) -- the "
+        "page must render the served order verbatim; the rank cell renders each row's own array "
+        "index, never a value derived from a client-side sort/reverse/slice"
+    )
+
+
+def test_desk_page_rows_reorder_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail -- a lint that cannot fail proves nothing."""
+    seeded_sort = "const ranked = [...rows].sort((a, b) => a.distance_bps - b.distance_bps);"
+    assert _ROWS_REORDER_PATTERN.search(seeded_sort) is not None
+
+    seeded_reverse = "const reversed = rows.reverse();"
+    assert _ROWS_REORDER_PATTERN.search(seeded_reverse) is not None
+
+    seeded_slice = "const page1 = rows.slice(0, 10);"
+    assert _ROWS_REORDER_PATTERN.search(seeded_slice) is not None
+
+    seeded_chained = "const top = rows.filter(hasTickEvidence).sort((a, b) => a.rank - b.rank);"
+    assert _ROWS_REORDER_PATTERN.search(seeded_chained) is not None
+
+
+# goal-desk-iter-24 (J-16) TC-7 (b): every `data-testid` a shipped journey's golden replay script,
+# guard test, or hover-tooltip contract depends on is still present in the source after the
+# reflow -- the reflow may move a disclosure's markup (a new element, a new line inside the SAME
+# row), but it must never drop, hide, or rename the testid itself. "the compute controls" (goal.md
+# J-16 step 4) are the three primary trigger buttons this page ships (Run Screen / Top-up /
+# Reconcile Index) -- untouched by this iteration's ranked-row-only reflow, checked here anyway as
+# the cheapest possible proof nothing regressed.
+_REQUIRED_DESK_TESTIDS = (
+    "desk-screen-rows-table",
+    "desk-row-drill-in",
+    "desk-row-side",
+    "desk-row-band-class",
+    "desk-row-distance",
+    "desk-row-score",
+    "desk-coverage-badges",
+    "desk-coverage-badge",
+    "desk-row-tick-evidence",
+    "desk-row-basis",
+    "desk-row-history",
+    "desk-row-band",
+    "desk-row-opposite",
+    "desk-row-levels",
+    "desk-skip-row",
+    "desk-history-row",
+    "desk-provenance",
+    "desk-title",
+    "desk-run-screen-button",
+    "desk-topup-button",
+    "desk-reconcile-button",
+)
+
+
+def test_desk_page_keeps_every_shipped_testid_after_the_reflow():
+    """TC-7: every testid a shipped journey's golden script/guard test/tooltip contract depends
+    on is still present in the reflowed source -- the layout changed, nothing else did."""
+    source = _DESK_PAGE.read_text()
+    missing = [testid for testid in _REQUIRED_DESK_TESTIDS if testid not in source]
+    assert not missing, (
+        f"apps/frontend/app/desk/page.tsx is missing testid(s) {missing} after the reflow -- a "
+        "shipped journey's golden script/guard test/tooltip contract depends on each of these "
+        "remaining present with the same text"
+    )
+
+
+def test_desk_page_testid_presence_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail -- a lint that cannot fail proves nothing."""
+    seeded_source = "const x = 1;"
+    missing = [testid for testid in _REQUIRED_DESK_TESTIDS if testid not in seeded_source]
+    assert missing == list(_REQUIRED_DESK_TESTIDS)
+
+
+# goal-desk-iter-24 (J-16) TC-6/TC-7 (c): the reflow's own regression guard for the defect the
+# iter-24 review caught -- dropping a ranked cell's in-cell label prefix ALSO deletes the literal
+# page text a stored golden replay script asserts through `page.get_by_text`, which matches
+# VISIBLE DOM TEXT only (the composite drill-in `title` carrying the same word is invisible to it).
+# TC-6 allows zero golden-script edits, so the two cells a golden pins by literal text
+# (`desk-row-band` <- J-13.json, `desk-row-opposite` <- J-14.json) must keep the prefix WORD the
+# script's expected text starts with. This guard reads BOTH artifacts and ties them together, so a
+# future prefix drop fails here (a fast, keyless, browser-free test) instead of only in a browser
+# replay lane. The other three disclosure cells (basis/history/levels) are deliberately absent from
+# this list: no stored golden asserts their prefixed text (J-08 pins "d before as-of", J-11 pins
+# "sessions", J-15 has no script), which is exactly why dropping THOSE prefixes was safe.
+_JOURNEY_SCRIPTS_DIR = (
+    pathlib.Path(__file__).resolve().parents[3] / "runs" / "goal-session-desk" / "journey-scripts"
+)
+
+_GOLDEN_TEXT_PINNED_CELLS = (
+    ("J-13.json", "desk-row-band", "band "),
+    ("J-14.json", "desk-row-opposite", "opposite "),
+)
+
+
+def _desk_cell_source(source: str, testid: str) -> str:
+    """The source of the single `<td ... data-testid="<testid>"> ... </td>` block."""
+    start = source.index(f'data-testid="{testid}"')
+    end = source.index("</td>", start)
+    return source[start:end]
+
+
+def _golden_expected_texts(script_name: str) -> list[str]:
+    """Every literal `text` a golden script asserts (step `expect` action or `expect` clause)."""
+    import json
+
+    data = json.loads((_JOURNEY_SCRIPTS_DIR / script_name).read_text())
+    texts: list[str] = []
+    for step in data.get("steps", []):
+        for holder in (step.get("action") or {}, step.get("expect") or {}):
+            text = holder.get("text")
+            if isinstance(text, str):
+                texts.append(text)
+    return texts
+
+
+def test_desk_row_cells_keep_the_label_prefix_their_golden_script_asserts():
+    """TC-6: the `band`/`opposite` cells still render the prefix WORD their stored golden replay
+    script's expected page text starts with -- dropping it fails J-13/J-14 on replay."""
+    source = _DESK_PAGE.read_text()
+    for script_name, testid, prefix in _GOLDEN_TEXT_PINNED_CELLS:
+        pinned = [t for t in _golden_expected_texts(script_name) if t.startswith(prefix)]
+        assert pinned, (
+            f"{script_name} no longer asserts any page text starting with {prefix!r} -- this pin "
+            f"has gone vacuous; re-derive it from the script's own expected texts"
+        )
+        cell = _desk_cell_source(source, testid)
+        assert f"`{prefix}" in cell, (
+            f"apps/frontend/app/desk/page.tsx's {testid} cell no longer renders the {prefix!r} "
+            f"label prefix, but {script_name} asserts the literal page text {pinned[0]!r} via "
+            f"page.get_by_text (visible DOM text only -- a `title` attribute does not satisfy it). "
+            f"TC-6 permits zero golden-script edits, so this cell must keep the prefix word."
+        )
+
+
+def test_desk_row_label_prefix_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail -- a lint that cannot fail proves nothing."""
+    seeded_cell = (
+        'data-testid="desk-row-band">\n'
+        "  {row.reference_close == null\n"
+        "    ? `${fmt(row.price_low)}–${fmt(row.price_high)} · close not recorded in this snapshot`\n"
+        "    : `${fmt(row.price_low)}–${fmt(row.price_high)} · close ${fmt(row.reference_close)}`}\n"
+        "</td>"
+    )
+    cell = _desk_cell_source(seeded_cell, "desk-row-band")
+    assert "`band " not in cell
+
+    # and the pin itself is non-vacuous: J-13/J-14 really do assert those literal texts today
+    assert any(t.startswith("band ") for t in _golden_expected_texts("J-13.json"))
+    assert any(t.startswith("opposite ") for t in _golden_expected_texts("J-14.json"))
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index e9c168b..1572e67 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -134,12 +134,60 @@ import { fmt } from "@/lib/format";
 // or inferred fallback from `band_score`/the band range/`bands_by_class`). Read-only render, zero
 // new endpoint, zero new control — all three fields ride the already-fetched `GET
 // /research/desk/screen` response verbatim.
+//
+// goal-desk-iter-24 (J-16) — the ranked table's own REFLOW, zero backend diff, zero new value.
+// Iter-23's own `UT-07` measured the table at `scrollWidth` 1795px inside a 1214px container (the
+// `levels`/`opposite` columns fell entirely off-screen) and each row at ~115px tall (the coverage
+// badges wrapped into four lines). This iteration renders the SAME twelve disclosures, plus one
+// new `rank` cell (the row's own 1-based position in the served `rows` array -- rendered from the
+// `.map` index, never a client-side sort/reorder), inside a `table-fixed` + `<colgroup>` layout
+// sized to the page's own `mx-auto max-w-7xl` container: the coverage badges lose their
+// `flex-wrap` (one line, not four), the class/distance cells gain the page's own existing chip
+// style (`CHIP_CLASS` above), and the five widest disclosure cells (basis/history/band/opposite/
+// levels) relax `whitespace-nowrap` so long values wrap onto a second line inside a fixed column
+// width instead of stretching the table. Three of those five (basis/history/levels) also drop the
+// in-cell label prefix the column header already states; `band ` and `opposite ` KEEP theirs,
+// because the stored golden replay scripts J-13.json/J-14.json assert those two cells' literal
+// rendered text and TC-6 permits zero script edits (iter-24 review, two CRITICAL findings). Every
+// `data-testid`, every honest legacy-absence string ("basis not recorded in this snapshot", etc.),
+// and the row's stretched drill-in anchor (`href`, `absolute inset-0`, `data-testid`, composite
+// `title`) stay byte-unchanged -- only the layout and three redundant label words moved.
 
 const NUMERIC_CELL = "px-2 py-1.5 text-right font-mono text-xs text-slate-200 whitespace-nowrap";
 const HEADER_CELL = "px-2 py-1 text-right text-[11px] font-medium text-slate-500";
 const HEADER_CELL_LEFT = "px-2 py-1 text-left text-[11px] font-medium text-slate-500";
 const LABEL_CELL = "px-2 py-1.5 text-left text-xs text-slate-400 whitespace-nowrap";
 
+// goal-desk-iter-24 (J-16): the ranked table's own reflow, so every disclosure fits the page's
+// own `mx-auto max-w-7xl` container at a 1440px viewport with zero horizontal scroll (see the
+// comment above `DeskRowsTable`). `WRAP_LABEL_CELL` is `LABEL_CELL` minus `whitespace-nowrap` --
+// used ONLY on the five long disclosure cells (basis/history/band/opposite/levels), which now wrap
+// onto a second line inside their own `<colgroup>`-fixed column width instead of stretching the
+// table wider than its container. `CHIP_CLASS` is the page's OWN existing bordered badge style
+// (`desk-coverage-badge`'s non-conditional half, `TickEvidenceBadge`, and the `band_round_number`
+// badge already use this exact className) -- reused verbatim, never a new visual effect, for the
+// new class/distance chips.
+const WRAP_LABEL_CELL = "px-1.5 py-1 text-left text-xs text-slate-400 align-top";
+// The ranked table's OWN cell padding -- `py-1` (4px, vertical) and `px-1.5` (6px, horizontal)
+// instead of the `py-1.5`/`px-2` the shared constants above keep for the history/top-up/
+// reconciliation tables. Both numbers are load-bearing measurements, not taste:
+//   * `py-1` -- 4px less row height per cell is the difference between a 3-line ranked row
+//     measuring 61px (OVER J-16's own <=60px target) and 57px (inside it).
+//   * `px-1.5` -- 2px per cell side x 13 columns = 52px of the fixed 1214px container handed back
+//     to content instead of gutter, which is what lets the five wrapping disclosure columns hold
+//     their values in 3 lines instead of 4-5 (a 4-line row is 73px). The gutter between two
+//     columns' text is still 12px.
+// Type scale is untouched (`text-xs` body, `text-[11px]` chips/header) and only this one table is
+// affected -- `LABEL_CELL`/`NUMERIC_CELL`/`HEADER_CELL`/`HEADER_CELL_LEFT` above stay byte-
+// unchanged for the other three tables on this page.
+const ROW_LABEL_CELL = "px-1.5 py-1 text-left text-xs text-slate-400 whitespace-nowrap";
+const ROW_NUMERIC_CELL = "px-1.5 py-1 text-right font-mono text-xs text-slate-200 whitespace-nowrap";
+const ROW_BADGE_CELL = "px-1.5 py-1 text-left";
+const ROW_HEADER_CELL = "px-1.5 py-1 text-right text-[11px] font-medium text-slate-500";
+const ROW_HEADER_CELL_LEFT = "px-1.5 py-1 text-left text-[11px] font-medium text-slate-500";
+const CHIP_CLASS =
+  "inline-block whitespace-nowrap rounded border border-slate-700 bg-slate-800/60 px-1.5 py-0.5 text-[11px] text-slate-300";
+
 const PRIMARY_BUTTON_CLASS =
   "rounded-md border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 transition-colors hover:border-slate-500 hover:bg-slate-700 focus:outline-none focus:ring-1 focus:ring-emerald-500 active:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-slate-600 disabled:hover:bg-slate-800";
 
@@ -215,7 +263,10 @@ function DeskCoverageBadges({
   coverage: Record<string, { has_bars: boolean; latest_window_end_utc: string | null }>;
 }) {
   return (
-    <span data-testid="desk-coverage-badges" className="flex flex-wrap gap-1">
+    // goal-desk-iter-24 (J-16): `flex-wrap` dropped -- the four badges now render on ONE line
+    // (TC-3), the direct fix for the ~115px row height `UT-07-fail.png` measured (four badges
+    // wrapping into four lines).
+    <span data-testid="desk-coverage-badges" className="flex flex-nowrap items-center gap-1">
       {Object.entries(coverage).map(([timeframe, tf]) => (
         <span
           key={timeframe}
@@ -341,7 +392,11 @@ function deskSkipDrillInTitle(skip: DeskScreenSkip): string {
 // the "stretched link" pattern (`position: relative` on the `<tr>`, `absolute inset-0` on the
 // `<a>`): one real `next/link` anchor, valid nested-in-a-`<td>` markup, clickable anywhere in the
 // row — never a raw `<a>` wrapping the `<tr>` directly (invalid HTML) and never `router.push`.
-function DeskRow({ row, asOf }: { row: DeskScreenRow; asOf: string }) {
+// goal-desk-iter-24 (J-16): `rank` is the row's own 1-based position in the DISPLAYED snapshot's
+// served `rows` array -- passed down from `DeskRowsTable`'s own `.map((row, index) => ...)`
+// index, never a value this component (or any client-side sort/reorder) computes itself. A plain
+// integer, no label implying action/quality/urgency (goal.md J-16 step 2).
+function DeskRow({ row, asOf, rank }: { row: DeskScreenRow; asOf: string; rank: number }) {
   return (
     <tr
       data-testid="desk-screen-row"
@@ -349,7 +404,10 @@ function DeskRow({ row, asOf }: { row: DeskScreenRow; asOf: string }) {
       data-band-class={row.band_class ?? "none"}
       className="relative border-b border-slate-800/60 last:border-b-0 hover:bg-slate-900/40"
     >
-      <td className={LABEL_CELL} data-testid="desk-row-symbol">
+      <td className={ROW_NUMERIC_CELL} data-testid="desk-row-rank">
+        {rank}
+      </td>
+      <td className={ROW_LABEL_CELL} data-testid="desk-row-symbol">
         <Link
           href={`/structure?symbol=${encodeURIComponent(row.symbol)}&asof=${encodeURIComponent(asOf)}`}
           data-testid="desk-row-drill-in"
@@ -359,49 +417,61 @@ function DeskRow({ row, asOf }: { row: DeskScreenRow; asOf: string }) {
         />
         {row.symbol}
       </td>
-      <td className={LABEL_CELL} data-testid="desk-row-side">
+      <td className={ROW_LABEL_CELL} data-testid="desk-row-side">
         {row.side}
       </td>
-      <td className={LABEL_CELL} data-testid="desk-row-band-class">
+      {/* goal-desk-iter-24 (J-16): the class/distance cells now render inside the page's OWN
+          existing chip style (`CHIP_CLASS` -- the same className `TickEvidenceBadge`/the
+          `band_round_number` badge already use), with the SAME text either cell rendered before
+          this iteration -- every stored golden's text expect stays true. */}
+      <td className={ROW_LABEL_CELL} data-testid="desk-row-band-class">
         {row.band_class !== null ? (
           <>
-            <span>{`Class ${row.band_class}`}</span>
-            <span className="block text-[11px] text-slate-500">nearest same-class band</span>
+            <span className={CHIP_CLASS}>{`Class ${row.band_class}`}</span>
+            <span className="block whitespace-normal text-[11px] text-slate-500">
+              nearest same-class band
+            </span>
           </>
         ) : (
-          "Unclassified"
+          <span className={CHIP_CLASS}>Unclassified</span>
         )}
       </td>
-      <td className={NUMERIC_CELL} data-testid="desk-row-distance" title={String(row.distance_bps)}>
-        {fmt(row.distance_bps)} bps
+      <td className={ROW_NUMERIC_CELL} data-testid="desk-row-distance" title={String(row.distance_bps)}>
+        <span className={CHIP_CLASS}>{fmt(row.distance_bps)} bps</span>
       </td>
-      <td className={NUMERIC_CELL} data-testid="desk-row-score" title={String(row.band_score)}>
+      <td className={ROW_NUMERIC_CELL} data-testid="desk-row-score" title={String(row.band_score)}>
         {fmt(row.band_score)}
       </td>
-      <td className="px-2 py-1.5 text-left" data-testid="desk-row-coverage">
+      <td className={ROW_BADGE_CELL} data-testid="desk-row-coverage">
         <DeskCoverageBadges coverage={row.coverage} />
       </td>
-      <td className="px-2 py-1.5 text-left">
+      <td className={ROW_BADGE_CELL}>
         {row.tick_evidence && <TickEvidenceBadge testid="desk-row-tick-evidence" />}
       </td>
       {/* era-desk-iter-9 (J-08): descriptive only, date portion of `basis_as_of` (full precision
           lives in the row anchor's own composite `title` above -- NEVER a per-cell `title` here,
           the iter-6/iter-7 F2 lesson applied proactively: a per-cell title under the stretched
           `absolute inset-0` anchor is pointer-unreachable). `== null` catches a legacy row's
-          ENTIRELY ABSENT keys (`undefined`), not just an explicit `null`. */}
-      <td className={LABEL_CELL} data-testid="desk-row-basis">
+          ENTIRELY ABSENT keys (`undefined`), not just an explicit `null`.
+          goal-desk-iter-24 (J-16): the redundant "basis " label prefix is dropped (the column
+          header already states it) and the cell switches to `WRAP_LABEL_CELL` so a long populated
+          value wraps onto a second line inside its own fixed column width instead of stretching
+          the table -- the honest-absence string itself is untouched. */}
+      <td className={WRAP_LABEL_CELL} data-testid="desk-row-basis">
         {row.basis_as_of == null || row.basis_age_days == null
           ? "basis not recorded in this snapshot"
-          : `basis ${row.basis_as_of.slice(0, 10)} · ${row.basis_age_days} d before as-of`}
+          : `${row.basis_as_of.slice(0, 10)} · ${row.basis_age_days} d before as-of`}
       </td>
       {/* era-desk-iter-15 (J-11): descriptive only, session count + start date (full precision --
           the untruncated `history_start` -- lives in the row anchor's own composite `title` above,
           NEVER a per-cell `title` here, the same F2 lesson the basis column above already applies).
-          `== null` catches a legacy row's ENTIRELY ABSENT keys (`undefined`), not just `null`. */}
-      <td className={LABEL_CELL} data-testid="desk-row-history">
+          `== null` catches a legacy row's ENTIRELY ABSENT keys (`undefined`), not just `null`.
+          goal-desk-iter-24 (J-16): "history " label prefix dropped, `WRAP_LABEL_CELL` -- same
+          reflow as the basis cell above. */}
+      <td className={WRAP_LABEL_CELL} data-testid="desk-row-history">
         {row.history_sessions == null || row.history_start == null
           ? "history not recorded in this snapshot"
-          : `history ${row.history_sessions} sessions · from ${row.history_start.slice(0, 10)}`}
+          : `${row.history_sessions} sessions · from ${row.history_start.slice(0, 10)}`}
       </td>
       {/* era-desk-iter-17 (J-13): the exact price the row's band was measured from, beside its own
           already-recorded price_low-price_high band range -- "the price is inside the wall"
@@ -412,8 +482,13 @@ function DeskRow({ row, asOf }: { row: DeskScreenRow; asOf: string }) {
           row's ENTIRELY ABSENT key (`undefined`), not just an explicit `null` -- and only the
           CLOSE segment falls back: `price_low`/`price_high` are recorded on every ranked row of
           every snapshot ever written, so the range itself always renders (goal-desk-iter-17 audit
-          F1). */}
-      <td className={LABEL_CELL} data-testid="desk-row-band">
+          F1). goal-desk-iter-24 (J-16): this cell keeps its "band " label prefix on BOTH branches,
+          byte-unchanged -- iter-24's own review caught that J-13.json step 3 asserts the LITERAL
+          rendered text "band 488.50–490.91 · close 490.91" through `page.get_by_text` (visible DOM
+          text only -- the composite drill-in `title` this word also appears in is invisible to that
+          matcher), so dropping it here would fail a stored golden replay with zero script edits
+          allowed (TC-6). Only `WRAP_LABEL_CELL` (wrap instead of `whitespace-nowrap`) applies. */}
+      <td className={WRAP_LABEL_CELL} data-testid="desk-row-band">
         {row.reference_close == null
           ? `band ${fmt(row.price_low)}–${fmt(row.price_high)} · close not recorded in this snapshot`
           : `band ${fmt(row.price_low)}–${fmt(row.price_high)} · close ${fmt(row.reference_close)}`}
@@ -422,11 +497,15 @@ function DeskRow({ row, asOf }: { row: DeskScreenRow; asOf: string }) {
           did NOT choose -- descriptive only, rounded display (full precision for this field is not
           carried in the tooltip this iteration; the tooltip instead gains the row's `bands_by_class`
           breakdown, see `deskRowDrillInTitle` above). Three distinguishable states: a populated
-          `opposite_band` (`opposite <side> <class> <low>–<high> · <distance> bps`), an honest
-          "no band on the other side" for a recorded `null` (the canonical band computation served
-          no band on that side at all), and the established legacy-absent copy "opposite wall not
-          recorded in this snapshot" for a row from before this iteration (`undefined`, not `null`). */}
-      <td className={LABEL_CELL} data-testid="desk-row-opposite">
+          `opposite_band` (`opposite <side> <class> <low>–<high> · <distance> bps`), an honest "no
+          band on the other side" for a recorded `null` (the canonical band computation served no band on
+          that side at all), and the established legacy-absent copy "opposite wall not recorded in
+          this snapshot" for a row from before this iteration (`undefined`, not `null`).
+          goal-desk-iter-24 (J-16): this cell keeps its "opposite " label prefix on the populated
+          branch, byte-unchanged, for the SAME reason the band cell above does -- J-14.json step 3
+          asserts the literal rendered text "opposite resistance A 490.97–494.39 · 1.22 bps" via
+          `page.get_by_text`, and TC-6 allows zero script edits. Only `WRAP_LABEL_CELL` applies. */}
+      <td className={WRAP_LABEL_CELL} data-testid="desk-row-opposite">
         {row.opposite_band === undefined
           ? "opposite wall not recorded in this snapshot"
           : row.opposite_band === null
@@ -443,13 +522,16 @@ function DeskRow({ row, asOf }: { row: DeskScreenRow; asOf: string }) {
           full-precision detail to hide behind a hover). `=== undefined` catches a legacy row's
           ENTIRELY ABSENT key (band_member_count is always >= 1 by construction whenever it is
           recorded at all, so it is never legitimately null) -- the same strict check
-          bands_by_class already uses. */}
-      <td className={LABEL_CELL} data-testid="desk-row-levels">
+          bands_by_class already uses.
+          goal-desk-iter-24 (J-16): the redundant " levels" label word is dropped from the tally
+          (the column header already says "levels"; the count/breakdown itself is unchanged text),
+          `WRAP_LABEL_CELL`. */}
+      <td className={WRAP_LABEL_CELL} data-testid="desk-row-levels">
         {row.band_member_count === undefined || row.band_member_timeframes === undefined
           ? "composition not recorded in this snapshot"
           : (
               <>
-                {`${row.band_member_count} levels · ${Object.entries(row.band_member_timeframes)
+                {`${row.band_member_count} · ${Object.entries(row.band_member_timeframes)
                   .map(([timeframe, count]) => `${timeframe} ${count}`)
                   .join(" · ")}`}{" "}
                 {row.band_round_number && (
@@ -480,26 +562,57 @@ function DeskRowsTable({ rows, asOf }: { rows: DeskScreenRow[]; asOf: string })
           ranked a symbol whose bars it never read.
         </p>
       )}
-      <table data-testid="desk-screen-rows-table" className="w-full border-collapse">
+      {/* goal-desk-iter-24 (J-16): `table-fixed` + an explicit `<colgroup>` -- each column takes
+          exactly its own assigned width regardless of content, so the table's OWN total width
+          (the sum of these thirteen widths) is a fixed, known quantity instead of the browser's
+          auto layout expanding to fit each column's widest single-line content (the direct cause
+          of iter-23's 1795px `scrollWidth`). The five long disclosure columns pair with
+          `WRAP_LABEL_CELL` (no `whitespace-nowrap`) so a value too long for its own column wraps
+          onto a second line instead of stretching the table wider than its container.
+          Every width below is a MEASURED number, not an estimate: the eight non-wrapping columns
+          each hold their own widest rendered content (measured cell-by-cell over the header plus
+          all 100 ranked rows of the latest populated screen, with zero overflow past any cell's
+          border box), and the remaining width is split across the five wrapping columns so each
+          one's longest value lands in 3 text lines -- a 3-line row measures 57px, inside J-16's
+          own <=60px target. They sum to 1214px, which is exactly this page's own
+          `mx-auto max-w-7xl` container width inside its `Panel` padding at a 1440px viewport, so
+          `scrollWidth === clientWidth` and no horizontal scrollbar can appear. */}
+      <table data-testid="desk-screen-rows-table" className="w-full table-fixed border-collapse">
+        <colgroup>
+          <col className="w-[36px]" />
+          <col className="w-[52px]" />
+          <col className="w-[66px]" />
+          <col className="w-[140px]" />
+          <col className="w-[96px]" />
+          <col className="w-[60px]" />
+          <col className="w-[122px]" />
+          <col className="w-[87px]" />
+          <col className="w-[81px]" />
+          <col className="w-[86px]" />
+          <col className="w-[96px]" />
+          <col className="w-[126px]" />
+          <col className="w-[166px]" />
+        </colgroup>
         <thead>
           <tr className="border-b border-slate-800">
-            <th className={HEADER_CELL_LEFT}>symbol</th>
-            <th className={HEADER_CELL_LEFT}>side</th>
-            <th className={HEADER_CELL_LEFT}>class</th>
-            <th className={HEADER_CELL}>distance</th>
-            <th className={HEADER_CELL}>score</th>
-            <th className={HEADER_CELL_LEFT}>coverage</th>
-            <th className={HEADER_CELL_LEFT}>tick evidence</th>
-            <th className={HEADER_CELL_LEFT}>basis</th>
-            <th className={HEADER_CELL_LEFT}>history</th>
-            <th className={HEADER_CELL_LEFT}>band</th>
-            <th className={HEADER_CELL_LEFT}>opposite</th>
-            <th className={HEADER_CELL_LEFT}>levels</th>
+            <th className={ROW_HEADER_CELL}>rank</th>
+            <th className={ROW_HEADER_CELL_LEFT}>symbol</th>
+            <th className={ROW_HEADER_CELL_LEFT}>side</th>
+            <th className={ROW_HEADER_CELL_LEFT}>class</th>
+            <th className={ROW_HEADER_CELL}>distance</th>
+            <th className={ROW_HEADER_CELL}>score</th>
+            <th className={ROW_HEADER_CELL_LEFT}>coverage</th>
+            <th className={ROW_HEADER_CELL_LEFT}>tick evidence</th>
+            <th className={ROW_HEADER_CELL_LEFT}>basis</th>
+            <th className={ROW_HEADER_CELL_LEFT}>history</th>
+            <th className={ROW_HEADER_CELL_LEFT}>band</th>
+            <th className={ROW_HEADER_CELL_LEFT}>opposite</th>
+            <th className={ROW_HEADER_CELL_LEFT}>levels</th>
           </tr>
         </thead>
         <tbody>
-          {rows.map((row) => (
-            <DeskRow key={row.symbol} row={row} asOf={asOf} />
+          {rows.map((row, index) => (
+            <DeskRow key={row.symbol} row={row} asOf={asOf} rank={index + 1} />
           ))}
         </tbody>
       </table>
diff --git a/docs/goal.md b/docs/goal.md
index 563296a..a95f9a8 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -1176,6 +1176,106 @@ order: J-01 → J-02 → J-03 → J-04 → J-05 → J-06, with J-07 guarding con
     side, class, distance, score, coverage, tick evidence, basis, history, band, opposite — have no cell
     for it.)*
 
+- **J-16: The briefing fits the page it is read on — every recorded disclosure legible without a sideways scroll**
+  - Steps:
+    1. Reflow the ranked table so the ROW's own content fits the width the page actually gives it. The
+       scroll container is capped by `/desk`'s own `mx-auto max-w-7xl` (`apps/frontend/app/desk/page.tsx:1829`
+       — 1280 px), and the table's intrinsic content width is 1795 px, so simply widening the container
+       cannot fix it: at a 1440 px viewport even an uncapped container offers ~1408 px < 1795 px. Sanctioned
+       mechanisms, builder's choice, any combination: drop the in-cell label prefixes the column headers
+       (`:486`–`:497`) already state (`basis `/`history `/`band `/`opposite `/`N levels` ≈ 35 characters per
+       row), render the four coverage badges on ONE line instead of today's wrap-into-four
+       (`DeskCoverageBadges`' `flex flex-wrap`, `:218`), relax `LABEL_CELL`'s `whitespace-nowrap` (`:141`)
+       on the long disclosure cells, and/or lay the five disclosure fields out as a second line of the SAME
+       row. What is NOT sanctioned: dropping, hiding, collapsing behind a click, or moving into a native
+       `title` tooltip ANY of the twelve disclosures — each one is a shipped journey's own acceptance
+       clause (J-08 `basis`, J-11 `history`, J-13 `band`, J-14 `opposite`, J-15 `levels`) — and NOT shrinking
+       the table's base type below the page's existing `text-xs` scale to buy width.
+    2. Add the `rank` cell Key Capability 4 and J-04 step 2 both name first: the row's own 1-based position
+       in the DISPLAYED snapshot's own served `rows` array, rendered as a plain integer position (never a
+       label implying action, quality, or urgency). The rank ORDER is already recorded data (J-03 step 2:
+       "the order is data, recorded in the snapshot"), so this RENDERS recorded data and computes no new
+       value: zero new recorded field, zero backend diff — `desk_screen.py`'s row shape, the five-pin
+       snapshot key and `_row_rank_key` are untouched — and the page never sorts, re-orders, filters or
+       paginates `rows`, it renders the served order verbatim.
+    3. Render the class and distance cells as the chips Key Capability 4 ("band class chip, distance chip")
+       and Success Criterion 4 ("descriptive chips") name — and which this page's own source comment
+       (`:326`) already calls chips while the DOM carries none — reusing the page's OWN existing badge style
+       (the bordered `text-[11px]` style `desk-coverage-badge` / `tick evidence` / `round number` already
+       use), with the SAME text those cells render today so every stored golden's text expect stays true.
+    4. Keep every browser contract the shipped journeys rest on: each existing `data-testid` on `/desk`
+       keeps its element and its exact text (`desk-screen-rows-table`, `desk-row-drill-in`, `desk-row-side`,
+       `desk-row-band-class`, `desk-row-distance`, `desk-row-score`, `desk-coverage-badges`/`-badge`,
+       `desk-row-tick-evidence`, `desk-row-basis`, `desk-row-history`, `desk-row-band`, `desk-row-opposite`,
+       `desk-row-levels`, `desk-skip-row*`, `desk-history-row`, `desk-provenance`, `desk-title`, the compute
+       controls), and the row's stretched drill-in anchor keeps its `href`, its `absolute inset-0`, its
+       `data-testid` and its dynamic consolidated `title` byte-unchanged — so
+       `tests/test_desk_hover_tooltip_guard.py` and `tests/test_desk_ui_guards.py` stay green UNMODIFIED,
+       J-14's already-photographed `bands_by_class` tooltip keeps working, and the 13 stored golden replay
+       scripts (`runs/goal-session-desk/journey-scripts/J-01`…`J-14`; there is no `J-06` script) replay
+       green without a single script edit. If the reflow moves a disclosure out of its own `<td>`, its
+       testid moves WITH it and keeps the same text.
+    5. Zero backend diff, zero new value: no new field on any recorded shape, no new Data-Contract row
+       (nothing new is computed — the page renders `GET /research/desk/screen`'s served payload verbatim, as
+       it already does), no new endpoint/route/`Config` field, no new MCP tool. The page still derives no
+       price and no distance of its own (`test_desk_ui_guards.py`'s price-arithmetic guard stays green
+       unmodified), and legacy rows keep every honest-absence string exactly as shipped ("basis / history /
+       close / opposite wall / composition not recorded in this snapshot").
+    6. Test: extend the source-introspection guard suite (the `test_desk_ui_guards.py` pattern, with its own
+       seeded can-fail counter-test) with (a) the page renders `rows` in served order — no `.sort(`,
+       `.reverse(`, re-slice or comparator over `rows` anywhere in `page.tsx` — and (b) every testid named
+       in step 4 is still present in the source. Copy stays descriptive measurement only and
+       `tests/test_copy_discipline.py` stays green unmodified.
+  - Acceptance: in a real browser after the T-9 clean rebuild, at a 1440×900 viewport with NO horizontal
+    scrolling and no click, ONE screenshot of `/desk`'s populated briefing shows the top-ranked row's
+    `rank`, symbol, side, class, distance, score, coverage badges, tick-evidence, `basis`, `history`,
+    `band`, `opposite` AND `levels` values all legible at once, and the ranked table's own measured
+    `scrollWidth` is ≤ its scroll container's `clientWidth` with both numbers quoted in the UI-test results
+    row (this is iter-23's UT-07 turned PASS, measured exactly the way it was measured FAIL: 1795 px inside
+    1214 px); each ranked row's four coverage badges render on ONE line and a ranked row's own measured
+    height is ≤ 60 px (today ~115 px — the BRK-B / AMZN / MDLZ row baselines sit 115 px apart in
+    `reports/qa/goal-desk-iter-23-evidence/UT-07-fail.png`); a further screenshot of that same rendered
+    screen shows at least the first EIGHT ranked rows legible with their rank positions 1…8 in the served
+    order (a full-page capture or a crop of one is fine — today three ranked rows fill a 1440×900 frame);
+    and the skipped-members table still groups `no bars` / `no basis` honestly while a pre-J-15 snapshot
+    still renders every honest legacy-absence string (screenshot) (T-10: no screenshot ⇒ `unknown`, never
+    `passing`; **no native `title` tooltip is required by this journey** — every reveal is DOM content, so
+    the T-10a headed rig is NOT needed and no capture may depend on one) (**single source of truth**: this
+    journey renders only what `GET /research/desk/screen` already serves — `desk_screen.ScreenStore` remains
+    the only owner and that GET the only serving endpoint; the `rank` cell renders the row's own position in
+    the SERVED order (the order J-03 already records as data) and the page never re-orders, sorts, filters
+    or paginates it; zero new value is computed, zero recorded shape changes, no new Data-Contract row is
+    needed, and the BACKEND TAKES A ZERO DIFF — this SSOT criterion stands in place of a PnL-ledger append,
+    which this era's Non-Goals forbid); every stored golden replay script replays green with zero script
+    edits, `tests/test_desk_ui_guards.py` and `tests/test_desk_hover_tooltip_guard.py` pass unmodified, and
+    every recorded universe, screen, top-up and reconciliation file is proven byte-identical on disk
+    (SHA-256 listing — a render-only iteration writes no record at all); a **`[NEW]`-flagged demo-narrator
+    walkthrough** covers the briefing end to end with the `opposite` and `levels` columns visible IN ITS OWN
+    FRAMES and its click targets naming ONE row (closing iter-21's and iter-23's RECORDED_WITH_NOTES frame
+    gap, where the film narrated columns its own frames could not show); and the full backend suite is green
+    with `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new `Config` fields, the `default`
+    profile and `v1` byte-identical (engine equivalence green), the MCP surface still exactly 17 tools, zero
+    diff to `desk_screen.py`/`tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`, and
+    `tests/test_copy_discipline.py` green unmodified. *(Keyless core; browser-verifiable. Why: measured
+    2026-07-30. Width — iter-23's own browser-QA measured the ranked table at `scrollWidth` 1795 px inside a
+    `clientWidth` 1214 px `overflow-x: auto` container at a 1440 px viewport, with the `levels` header's
+    rect at left 1658 / right 1901, entirely outside the visible window (`UT-07` = **FAIL**, P2/non-gating;
+    `UT-07-fail.png` shows the table cut off after `band`, so `opposite` (J-14) and `levels` (J-15) — the two
+    newest and densest disclosures — are unreachable at any monitor size because the cap is the page's own
+    `max-w-7xl`). Cause — for the #1 row of `screen-2026-07-30-bad6387963ef` (100 ranked / 1 skipped, all
+    100 rows `band_class A`, `distance_bps` median 3.38, 15 rows tied at 0.00) the five disclosure cells
+    carry 194 of the row's 263 rendered characters (74%), all inside `LABEL_CELL`'s `whitespace-nowrap`, and
+    the per-column maxima across the 100 rows sum to 309 characters (`opposite` 50, `levels` 62, `history`
+    38, `band` 36, `basis` 35) — about 35 of them per row being label prefixes the headers already state.
+    Height — `DeskCoverageBadges` is `flex flex-wrap`, so the four badges stack into four lines and each
+    ranked row is ~115 px tall: three rows fill a 1440×900 frame and 100 rows span ~11,500 px. Vision gap —
+    Key Capability 4 and J-04 step 2 both name `(rank, symbol, …)` first and Success Criterion 4 says
+    "descriptive chips", yet `grep rank app/desk/page.tsx` matches only comments and prose (16 hits, zero
+    cells) and the class/distance cells carry no chip styling. And iter-23's own iteration summary records
+    that "a layout decision … is due before any 13th column is added" and asks the next proposer cycle to
+    own it, while the iter-21 and iter-23 walkthrough films were RECORDED_WITH_NOTES for exactly this
+    reason.)*
+
 <!-- /AUTO:journeys -->
 
 ## Anti-goals
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-desk-index.html               |  13 ++-
 runs/goal-session-desk/.engine.lock/epoch          |   2 +-
 runs/goal-session-desk/.engine.lock/pid            |   2 +-
 runs/goal-session-desk/engine.pid                  |   2 +-
 runs/goal-session-desk/session.json                |   6 +-
 runs/goal-session-desk/state/assumptions.md        |  71 -------------
 .../state/assumptions.md.archive.md                |  74 ++++++++++++++
 runs/goal-session-desk/state/blueprint.md          |  40 +++++++-
 .../state/enhancement-proposals.jsonl              |   2 +
 runs/goal-session-desk/state/lessons.md            |  34 +------
 runs/goal-session-desk/state/lessons.md.archive.md |  47 +++++++++
 runs/goal-session-desk/state/proposer-result.json  |   4 +-
 runs/goal-session-desk/summary.md                  | 112 ++++++++++++++-------
 runs/goal-session-desk/telemetry.jsonl             |  48 +++++++++
 runs/goal-session-desk/trace/trace.jsonl           |   5 +
 15 files changed, 310 insertions(+), 152 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
