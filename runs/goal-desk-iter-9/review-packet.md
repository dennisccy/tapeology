# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 6. Shown in full: 6.

```diff
diff --git a/apps/backend/app/research/desk_screen.py b/apps/backend/app/research/desk_screen.py
index 55ac2e1..911c0ef 100644
--- a/apps/backend/app/research/desk_screen.py
+++ b/apps/backend/app/research/desk_screen.py
@@ -53,6 +53,18 @@ screen's final ``rows`` list (TC-14) -- one rule serves both jobs.
 (``basis_as_of: null``, ``bands: []``). Both honest, distinct absences -- a skip row's ``coverage``
 still reflects whichever pinned timeframes genuinely have bars (never a fabricated all-false).
 
+**Basis disclosure (goal-desk-iter-9, J-08).** Every RANKED row also carries ``basis_as_of``
+(copied VERBATIM from ``result["basis_as_of"]`` -- the SAME value ``_resolve_reference_close``
+already consumes to find the reference close, so this costs zero additional
+``BarStore``/``compute_tradability`` work) and ``basis_age_days`` (a plain calendar-date
+difference between that value and the row's own ``as_of``, mirroring ``_distance_bps``'s "plain
+arithmetic derivation" style -- see ``_basis_age_days`` below). Skip rows never carry these fields
+-- a skip row's own ``reason`` already means no basis resolved at all. A snapshot recorded BEFORE
+this addition simply has ranked rows that OMIT these two keys entirely; ``ScreenStore`` performs no
+row-shape validation or enrichment (a plain checksum-verified passthrough), so
+``GET /research/desk/screen`` serves that absence VERBATIM -- never defaulted, never backfilled
+(the append-only rail applies to row CONTENT, not just to the snapshot as a whole).
+
 **No new ``Config`` field.** The screen store's directory resolves via ``resolve_desk_screen_dir``
 below -- a bare ``TAPEOLOGY_DESK_SCREEN_DIR``-env-var-or-sibling-of-``desk_universe_dir_resolved()``
 default (the ``edge_report_cache.resolve_cache_db_path`` pattern) -- never a ``desk_screen_dir``
@@ -245,6 +257,24 @@ def _resolve_reference_close(store: BarStore, symbol: str, basis_as_of: str) ->
     )
 
 
+# --- basis disclosure (goal-desk-iter-9, J-08) -----------------------------------------------------
+
+
+def _basis_age_days(basis_as_of: str, as_of: str) -> int:
+    """``basis_age_days``: a plain calendar-date difference between ``basis_as_of`` (a ranked row's
+    own reference session -- ``compute_tradability``'s own already-resolved value, zero new read)
+    and ``as_of`` (the screen's own as-of) -- the ``_distance_bps`` precedent's "plain arithmetic
+    derivation" style, never a second bar read. Calendar DATES, not a raw hour delta:
+    ``basis_as_of`` carries the prior session's own bar-timestamp time-of-day (e.g. ``04:00:00``
+    UTC) while ``as_of`` is always ``screen_as_of``'s fixed ``23:59:59Z`` -- comparing the raw
+    instants would inflate the count by a fraction of a day for every symbol, so both sides are
+    reduced to a UTC calendar date first, the SAME ``.replace("Z", "+00:00")`` parsing style
+    ``_epoch`` above already uses."""
+    basis_date = datetime.fromisoformat(basis_as_of.replace("Z", "+00:00")).date()
+    as_of_date = datetime.fromisoformat(as_of.replace("Z", "+00:00")).date()
+    return (as_of_date - basis_date).days
+
+
 # --- the row computation (the SOLE walker; the manager and the CLI both call this) ----------------
 
 
@@ -264,7 +294,9 @@ def compute_screen(
     (``compute_tradability``, ``desk_coverage.get_desk_coverage``, ``DatasetStore.list``). Returns
     the full snapshot content MINUS the store-assigned ``id``/``created_utc`` (``ScreenStore.record``
     assigns those): ``{screen_date, as_of, universe_snapshot_id, config_fingerprint,
-    bar_store_signature, rows, skipped}``.
+    bar_store_signature, rows, skipped}``. Each RANKED row additionally carries ``basis_as_of``/
+    ``basis_age_days`` (goal-desk-iter-9, J-08 -- see the module docstring's "Basis disclosure"
+    section); skip rows never carry them.
 
     ``progress``, if given, is called after EACH member with ``{"symbol": symbol}`` (the caller
     tracks its own done/total counters -- the ``desk_topup_compute.run_topup`` precedent).
@@ -321,6 +353,8 @@ def compute_screen(
                     "price_high": best["price_high"],
                     "coverage": coverage,
                     "tick_evidence": tick_evidence,
+                    "basis_as_of": result["basis_as_of"],
+                    "basis_age_days": _basis_age_days(result["basis_as_of"], as_of),
                 }
             )
 
diff --git a/apps/backend/tests/test_desk_hover_tooltip_guard.py b/apps/backend/tests/test_desk_hover_tooltip_guard.py
index 872dacd..2947ab0 100644
--- a/apps/backend/tests/test_desk_hover_tooltip_guard.py
+++ b/apps/backend/tests/test_desk_hover_tooltip_guard.py
@@ -87,14 +87,21 @@ def test_ranked_row_drill_in_tooltip_is_built_from_distance_score_and_coverage_f
     """The ranked-row (``desk-row-drill-in``) anchor's tooltip-building function references the
     row's own full ``distance_bps``, full ``band_score``, and coverage ``latest_window_end_utc``
     -- the exact three fields audit F2 found unreachable once the anchor started painting above
-    their per-cell ``title``s."""
+    their per-cell ``title``s. goal-desk-iter-9 (J-08) adds two more required needles:
+    ``basis_as_of``/``basis_age_days`` -- the new basis column is a plain descriptive `<td>` with
+    NO per-cell ``title`` of its own (the same F2 lesson applied proactively), so its full-precision
+    detail must join this SAME consolidated tooltip or it is unreachable by pointer, exactly like
+    the three fields above."""
     source = _DESK_PAGE.read_text()
     fn_name = _anchor_title_function_name(source, "desk-row-drill-in")
     fn_source = _extract_function(source, fn_name)
-    for needle in ("row.distance_bps", "row.band_score", "latest_window_end_utc"):
+    for needle in (
+        "row.distance_bps", "row.band_score", "latest_window_end_utc",
+        "row.basis_as_of", "row.basis_age_days",
+    ):
         assert needle in fn_source, (
             f"{fn_name}() never references {needle!r} -- the ranked row's composite hover "
-            "tooltip must carry the row's own full-precision distance/score plus coverage "
+            "tooltip must carry the row's own full-precision distance/score/basis plus coverage "
             "freshness, not a static or empty string"
         )
 
diff --git a/apps/backend/tests/test_desk_screen.py b/apps/backend/tests/test_desk_screen.py
index 718a97d..a592a4d 100644
--- a/apps/backend/tests/test_desk_screen.py
+++ b/apps/backend/tests/test_desk_screen.py
@@ -30,7 +30,7 @@ from app.research.desk_screen import (
     resolve_desk_screen_dir,
     screen_as_of,
 )
-from app.research.desk_screen import _distance_bps, _row_rank_key, _select_best_band
+from app.research.desk_screen import _basis_age_days, _distance_bps, _row_rank_key, _select_best_band
 from app.research.desk_universe import UniverseStore
 
 FIXTURE_UNIVERSE_DIR = Path(__file__).parent / "fixtures" / "universe"
@@ -469,11 +469,16 @@ def test_fixture_universe_with_zero_bars_skips_every_member_as_no_bars(ctx):
 
 
 def test_aapl_row_cross_checks_byte_identical_to_the_real_tradability_route(ctx, monkeypatch):
-    """TC-1/TC-19: the persisted AAPL row's band_class/distance_bps/band_score/price_low/
+    """TC-1/TC-2/TC-19: the persisted AAPL row's band_class/distance_bps/band_score/price_low/
     price_high are byte-identical to what GET /research/tradability returns for the band
     desk_screen.py selected as AAPL's "best"; the reference close is the fixture bar's own
-    recorded close at basis_as_of. (``git diff`` on ``tradability.py``/``levels.py`` staying empty
-    is verified directly against the repo, not by a test in this file.)"""
+    recorded close at basis_as_of. TC-1: the row's own `basis_as_of` is byte-identical to the SAME
+    route's own `basis_as_of`. TC-2: `basis_age_days` is the exact calendar-day count between that
+    value and the screen's own `as_of` (the fixture's real 2026-06-18 -> 2026-06-22 span = 4 days;
+    goal.md's own 12-day illustration is golden-asserted separately, as a pure-function test of the
+    same formula, in `test_basis_age_days_matches_goal_mds_own_worked_example` below). (``git diff``
+    on ``tradability.py``/``levels.py`` staying empty is verified directly against the repo, not by
+    a test in this file.)"""
     from fastapi.testclient import TestClient
 
     from app.main import app, get_market_adapter, manager
@@ -510,6 +515,14 @@ def test_aapl_row_cross_checks_byte_identical_to_the_real_tradability_route(ctx,
     body = resp.json()
     assert body["basis_as_of"] == "2026-06-18T04:00:00.000000Z"
 
+    # TC-1: the row's own basis_as_of is byte-identical to the SAME route's own basis_as_of --
+    # never re-derived, copied verbatim from the identical compute_tradability result this row's
+    # band/distance/score were themselves selected from.
+    assert row["basis_as_of"] == body["basis_as_of"]
+    # TC-2: the exact calendar-day count between that basis and the screen's own as_of
+    # ("2026-06-22T23:59:59Z") -- 2026-06-18 -> 2026-06-22 is 4 calendar days.
+    assert row["basis_age_days"] == 4
+
     matching = [
         b for b in body["bands"]
         if b["side"] == row["side"] and b["price_low"] == row["price_low"] and b["price_high"] == row["price_high"]
@@ -648,3 +661,104 @@ def test_rows_are_sorted_by_class_then_distance_then_score_then_symbol(ctx):
     # The list-wide invariant: every row's own rank key is non-decreasing.
     keys = [_row_rank_key(r) for r in screen["rows"]]
     assert keys == sorted(keys)
+
+
+# ==================================================================================================
+# basis disclosure (goal-desk-iter-9, J-08) -- basis_as_of / basis_age_days
+# ==================================================================================================
+
+
+def test_basis_age_days_matches_goal_mds_own_worked_example():
+    """TC-2 (pure-function form): goal.md's own worked example -- "a basis 12 calendar days before
+    as_of yields basis_age_days == 12" -- asserted directly against the helper, independent of any
+    fixture's own real date spread (the AAPL cross-check test above golden-asserts the SAME formula
+    against a different, real 4-day gap -- 2026-06-18 to 2026-06-22)."""
+    assert _basis_age_days("2026-06-13T04:00:00.000000Z", "2026-06-25T23:59:59Z") == 12
+
+
+def test_basis_age_days_is_a_calendar_date_difference_not_a_raw_hour_delta():
+    """``basis_as_of``'s own time-of-day (e.g. ``04:00:00``, a bar's own recorded hour) must never
+    leak into the day count against ``as_of``'s fixed ``23:59:59`` -- both sides collapse to a UTC
+    calendar DATE first, so a same-calendar-day pair reads 0 even ~20 hours apart, and a
+    calendar-adjacent pair reads 1 even ~1 hour apart."""
+    assert _basis_age_days("2026-06-22T04:00:00.000000Z", "2026-06-22T23:59:59Z") == 0
+    assert _basis_age_days("2026-06-21T23:00:00.000000Z", "2026-06-22T00:00:01.000000Z") == 1
+
+
+def test_basis_fields_add_zero_extra_compute_tradability_calls(ctx, monkeypatch):
+    """TC-8: basis_as_of/basis_age_days are read/derived ENTIRELY from the per-member
+    ``compute_tradability`` result already fetched inside the walk -- instrumented exactly like
+    ``test_bar_store_signature_issues_zero_bar_store_calls`` (a call-COUNT assertion, not a
+    behavior one), this proves the call count equals exactly the member count: one call per member
+    (the existing contract), zero calls attributable to the two new fields."""
+    import app.research.desk_screen as desk_screen_module
+
+    universe_store, bar_store, bar_index, dataset_store = ctx
+    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
+
+    calls: list[str] = []
+    original = desk_screen_module.compute_tradability
+
+    def _tracked(store, symbol, as_of_epoch, config):
+        calls.append(symbol)
+        return original(store, symbol, as_of_epoch, config)
+
+    monkeypatch.setattr(desk_screen_module, "compute_tradability", _tracked)
+
+    screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
+
+    universe_records, _errors = universe_store.list()
+    members = universe_records[-1]["members"]
+    assert calls == members, "exactly one compute_tradability call per member, in walk order"
+    assert screen["rows"], "the walk must have actually produced at least one ranked row"
+
+
+def test_recording_a_freshly_computed_screen_twice_is_refused_and_basis_fields_stay_byte_identical(
+    ctx, tmp_path
+):
+    """TC-3: a REAL ``compute_screen()`` result (carrying ``basis_as_of``/``basis_age_days`` on its
+    ranked rows) recorded once, then a FRESH computation under the identical pins -- the second
+    ``record()`` call is refused (``ScreenAlreadyRecorded``, no second file written), and the
+    content already on disk -- read back via ``list()`` -- is byte-identical to the second
+    (unrecorded) computation, including both new fields on every ranked row."""
+    universe_store, bar_store, bar_index, dataset_store = ctx
+    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
+    screen_store = ScreenStore(tmp_path / "screen")
+
+    first_screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
+    recorded = screen_store.record(**first_screen)
+    assert len(list((tmp_path / "screen").glob("*.json"))) == 1
+
+    second_screen = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, SCREEN_DATE)
+    with pytest.raises(ScreenAlreadyRecorded) as excinfo:
+        screen_store.record(**second_screen)
+    assert excinfo.value.existing_id == recorded["id"]
+    assert len(list((tmp_path / "screen").glob("*.json"))) == 1, "no second file written"
+
+    stored_records, errors = screen_store.list()
+    assert errors == []
+    assert len(stored_records) == 1
+    assert json.dumps(stored_records[0]["rows"], sort_keys=True) == json.dumps(
+        second_screen["rows"], sort_keys=True
+    )
+    aapl_row = next(r for r in stored_records[0]["rows"] if r["symbol"] == "AAPL")
+    assert aapl_row["basis_as_of"] == "2026-06-18T04:00:00.000000Z"
+    assert aapl_row["basis_age_days"] == 4
+
+
+def test_a_legacy_row_recorded_without_basis_fields_serves_them_absent_never_backfilled(tmp_path):
+    """The exact shape every screen snapshot recorded BEFORE this iteration has: ranked rows that
+    OMIT ``basis_as_of``/``basis_age_days`` entirely (never merely present-as-``null``).
+    ``ScreenStore`` performs no row-shape validation or enrichment of any kind -- a plain
+    checksum-verified passthrough (``_record``'s own default row, reused across this whole file's
+    store-level suite, already carries no such keys) -- so this is true by construction; this test
+    pins that contract so a future change cannot silently start defaulting or backfilling legacy
+    rows on read."""
+    store = ScreenStore(tmp_path / "screen")
+    _record(store)  # `_record`'s own default row carries no basis_as_of/basis_age_days key at all
+
+    records, errors = store.list()
+    assert errors == []
+    row = records[0]["rows"][0]
+    assert "basis_as_of" not in row
+    assert "basis_age_days" not in row
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index b9ae0d2..ff49180 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -27,10 +27,12 @@ import { fmt } from "@/lib/format";
 // The /desk page (Era B "The Desk" J-04) — the third top-nav page, reached from the persistent
 // NavBar (data-driven from GET /meta/ui-routes; no client hardcoding, see apps/backend/app/meta.py
 // UI_ROUTES). Renders the LATEST screen snapshot as a dense, descriptive briefing: ranked rows
-// (band class/distance/score/coverage/tick-evidence, all read verbatim), an honestly-grouped
-// skipped-members section, a provenance line, and a read-only screen-history list. "Run Screen"
-// and "Top-up" wire the J-03/J-02 compute managers with live progress + cancel — mirrors the
-// Edge Report Compute button UX pattern already shipped on /structure (NotComputedPanel/poll-loop).
+// (band class/distance/score/coverage/tick-evidence/basis-age, all read verbatim — the "basis"
+// column is era-desk-iter-9/J-08, honestly absent as "basis not recorded in this snapshot" on any
+// row from a screen recorded before that iteration), an honestly-grouped skipped-members section,
+// a provenance line, and a read-only screen-history list. "Run Screen" and "Top-up" wire the
+// J-03/J-02 compute managers with live progress + cancel — mirrors the Edge Report Compute button
+// UX pattern already shipped on /structure (NotComputedPanel/poll-loop).
 //
 // FOUR canonical endpoints (three read, one write path split across two triggers), rendered
 // VERBATIM and nothing else:
@@ -186,11 +188,23 @@ function hasNoCoverageAtAll(coverage: Record<string, { has_bars: boolean }>): bo
 // titles carried is composed directly onto the ANCHOR's own `title` instead: hovering ANYWHERE in
 // the row now reveals one composite tooltip. Full precision -- never the rounded 2-decimal DISPLAY
 // audit F3 chose for scanability (this is a hover detail, not a rendered cell).
+// era-desk-iter-9 (J-08): the composite tooltip also carries the row's full-precision basis
+// detail -- `row.basis_as_of` untruncated (the visible "basis" cell below shows only the date
+// portion for scanability, the SAME rounded-display/full-precision-on-hover split already
+// established for distance/score) plus `row.basis_age_days`. A legacy row (recorded before this
+// iteration) has BOTH keys absent, not merely `null` -- `== null` (loose equality) catches both
+// `undefined` and `null` in one check, per this project's own `fmt()` convention (lib/format.ts).
 function deskRowDrillInTitle(row: DeskScreenRow): string {
   const coverageLines = Object.entries(row.coverage)
     .map(([timeframe, tf]) => `${timeframe} window last requested: ${tf.latest_window_end_utc ?? "never"}`)
     .join(" · ");
-  return `distance ${row.distance_bps} bps · score ${row.band_score}${coverageLines ? ` · ${coverageLines}` : ""}`;
+  const basisLine =
+    row.basis_as_of == null || row.basis_age_days == null
+      ? "basis not recorded in this snapshot"
+      : `basis ${row.basis_as_of} (${row.basis_age_days} d before as-of)`;
+  return `distance ${row.distance_bps} bps · score ${row.band_score} · ${basisLine}${
+    coverageLines ? ` · ${coverageLines}` : ""
+  }`;
 }
 
 // A skipped member has no distance_bps/band_score -- its anchor's tooltip carries ONLY the
@@ -202,13 +216,14 @@ function deskSkipDrillInTitle(skip: DeskScreenSkip): string {
 }
 
 // One ranked row: symbol, side, band-class chip, distance-bps chip, band score, per-timeframe
-// coverage badges, tick-evidence badge — the DoD's exact column list, every value read verbatim
-// from the snapshot. Distance and score are DISPLAYED to two decimals (a `0.33523150389608725 bps`
-// cell defeated the scanability the briefing exists for — audit F3); the full-precision value is
-// not lost — it is reachable via the row's own drill-in anchor's composite `title`
-// (`deskRowDrillInTitle` above, audit F2 fix), never a per-cell `title` (iter-7 audit F1: this
-// comment used to claim the opposite). The band-class chip carries the
-// "nearest same-class band" caption
+// coverage badges, tick-evidence badge, basis column (era-desk-iter-9/J-08) — every value read
+// verbatim from the snapshot. Distance and score are DISPLAYED to two decimals (a
+// `0.33523150389608725 bps` cell defeated the scanability the briefing exists for — audit F3); the
+// full-precision value is not lost — it is reachable via the row's own drill-in anchor's composite
+// `title` (`deskRowDrillInTitle` above, audit F2 fix), never a per-cell `title` (iter-7 audit F1:
+// this comment used to claim the opposite). The basis column follows the SAME split: a rounded,
+// date-only display with the full-precision `basis_as_of` reachable only via that same composite
+// tooltip. The band-class chip carries the "nearest same-class band" caption
 // (assumptions.md iter-4 entry 1 — `_select_best_band` itself stays byte-unchanged; this copy
 // keeps the chip honest about what the ranking actually selects rather than implying it is the
 // symbol's single strongest band).
@@ -260,6 +275,16 @@ function DeskRow({ row, asOf }: { row: DeskScreenRow; asOf: string }) {
       <td className="px-2 py-1.5 text-left">
         {row.tick_evidence && <TickEvidenceBadge testid="desk-row-tick-evidence" />}
       </td>
+      {/* era-desk-iter-9 (J-08): descriptive only, date portion of `basis_as_of` (full precision
+          lives in the row anchor's own composite `title` above -- NEVER a per-cell `title` here,
+          the iter-6/iter-7 F2 lesson applied proactively: a per-cell title under the stretched
+          `absolute inset-0` anchor is pointer-unreachable). `== null` catches a legacy row's
+          ENTIRELY ABSENT keys (`undefined`), not just an explicit `null`. */}
+      <td className={LABEL_CELL} data-testid="desk-row-basis">
+        {row.basis_as_of == null || row.basis_age_days == null
+          ? "basis not recorded in this snapshot"
+          : `basis ${row.basis_as_of.slice(0, 10)} · ${row.basis_age_days} d before as-of`}
+      </td>
     </tr>
   );
 }
@@ -287,6 +312,7 @@ function DeskRowsTable({ rows, asOf }: { rows: DeskScreenRow[]; asOf: string })
             <th className={HEADER_CELL}>score</th>
             <th className={HEADER_CELL_LEFT}>coverage</th>
             <th className={HEADER_CELL_LEFT}>tick evidence</th>
+            <th className={HEADER_CELL_LEFT}>basis</th>
           </tr>
         </thead>
         <tbody>
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 79bf11a..6a3ebc0 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -789,6 +789,15 @@ export type EdgeReportPayload = EdgeReportResponse | EdgeReportNotComputed;
 // recomputed here. `coverage` is keyed by timeframe (e.g. "1h"/"4h"/"1d"/"1w"), each entry read
 // verbatim from `desk_coverage.get_desk_coverage` -- rendered honestly per-timeframe (a symbol may
 // hold bars for some pinned timeframes and not others; never assumed uniform).
+// era-desk-iter-9 (J-08) -- basis disclosure: the daily bar `compute_tradability` actually
+// measured this row's distance/class from, and how many calendar days before the screen's own
+// `as_of` that bar is dated. Always present (non-null) on a NEWLY computed ranked row -- a row
+// only exists in this branch once `compute_tradability` resolved a basis (desk_screen.py's
+// row-builder `elif result["basis_as_of"] is None: skipped...` branch is the only other outcome).
+// Typed nullable because a screen snapshot recorded BEFORE this iteration has ranked rows that
+// OMIT these two keys ENTIRELY (the append-only rail: legacy snapshots are never backfilled) --
+// the runtime value there is `undefined`, not `null`, so callers must check
+// `row.basis_as_of == null` (loose equality) to catch both, never `=== null` alone.
 export interface DeskScreenRow {
   symbol: string;
   side: "support" | "resistance";
@@ -799,6 +808,8 @@ export interface DeskScreenRow {
   price_high: number;
   coverage: Record<string, { has_bars: boolean; latest_window_end_utc: string | null }>;
   tick_evidence: boolean;
+  basis_as_of: string | null;
+  basis_age_days: number | null;
 }
 
 // A member the screen walked but could not rank -- two honest, distinct reasons, never conflated:
diff --git a/docs/goal.md b/docs/goal.md
index 6d3bdcb..e29b188 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -513,6 +513,57 @@ order: J-01 → J-02 → J-03 → J-04 → J-05 → J-06, with J-07 guarding con
 
 <!-- AUTO:journeys -->
 
+- **J-08: Every ranked briefing row names the bar its distance was measured from**
+  - Steps:
+    1. Record the basis on every NEW screen row: `basis_as_of`, copied **verbatim** from the value
+       `compute_tradability` already returns (`tradability.py:381`'s
+       `{"bands", "no_bar_series_for_symbol", "basis_as_of"}` — the same value
+       `desk_screen._resolve_reference_close` already consumes), plus `basis_age_days`, a plain
+       arithmetic derivation from the row's own `basis_as_of` and the snapshot's own `as_of` (the
+       `distance_bps` precedent, `desk_screen.py:197`). Both are desk-owned row fields with exactly
+       one owner (`desk_screen.py`) and one serving endpoint (`GET /research/desk/screen`) — zero
+       diff to `tradability.py`/`levels.py`/`bars.py` (no new field on any frozen return shape) and
+       zero new `Config` field.
+    2. Register both fields in the Data Contract's "Screen snapshots, rank rows, skip rows" row; the
+       pinned snapshot key (screen date, as_of, universe snapshot id, `config_fingerprint`,
+       bar-store signature) is unchanged — only NEW snapshots' row content grows.
+    3. Keep the append-only rail absolute: never backfill, rewrite, or recompute an
+       already-recorded snapshot; `GET /research/desk/screen` serves legacy rows exactly as
+       recorded, and `/desk` renders their absent basis as an honest
+       `"basis not recorded in this snapshot"` — never a value computed at read time.
+    4. Surface it on `/desk`: a descriptive `basis` column beside `distance` on the ranked table
+       (e.g. `basis 2026-07-13 · 12 d before as-of`), full precision in the row anchor's existing
+       consolidated honesty tooltip (the iter-7 pattern), copy = descriptive measurement only (no
+       advice, imperative, urgency, or prediction language).
+    5. Test: a fixture-scoped golden screen asserting the exact `basis_as_of` + `basis_age_days` per
+       ranked row and byte-identical row content on a re-run under identical pins; a guard test that
+       the desk never re-derives the basis (it comes from `compute_tradability`'s return — no extra
+       bar scan in the row builder, none in the frontend); the MCP `desk_screen` tool stays a
+       byte-identical GET proxy (17-tool contract unchanged).
+  - Acceptance: on the fixture-scoped rig a NEW screen run records `basis_as_of` and
+    `basis_age_days` on every ranked row, and each row's `basis_as_of` is byte-identical to
+    `GET /research/tradability?symbol=<sym>&as_of=<that snapshot's own as_of>`'s `basis_as_of`
+    (**single source of truth**: the desk reads the canonical owner verbatim, and both new values
+    are registered in the Data Contract with `desk_screen.py` as their only owner and
+    `GET /research/desk/screen` as their only serving endpoint — this SSOT criterion stands in place
+    of a PnL-ledger append, which this era's Non-Goals forbid); a re-run under identical pins
+    reproduces byte-identical rows and a same-pins re-run still returns the honest already-recorded
+    response; the previously recorded screen snapshots are proven byte-identical on disk (checksums
+    unchanged, nothing backfilled) and `/desk` renders their rows with the honest
+    `"basis not recorded in this snapshot"` state; in a real browser after the T-9 clean rebuild,
+    `/desk` shows the `basis` column with at least one fresh row (age ≤ 2 d) and one stale row
+    (age ≥ 10 d) legible in the same screenshot (T-10: no screenshot ⇒ `unknown`, never
+    `passing`); a **`[NEW]`-flagged demo-narrator walkthrough** covers the briefing's basis
+    disclosure end to end; and the full backend suite is green with
+    `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new `Config` fields, the
+    `default` profile and `v1` byte-identical (engine equivalence green), zero diff to
+    `tradability.py`/`levels.py`/`bars.py`/`StructureChart.tsx`, and
+    `tests/test_copy_discipline.py` green unmodified. *(Keyless core; browser-verifiable. Why:
+    measured live on the canonical endpoint at as-of 2026-07-25 — `basis_as_of` spans 2026-07-24
+    for AAPL (1 d) to 2026-07-13 for META/NFLX/NVDA (12 d), while the recorded snapshot
+    `screen-2026-07-25-e184a7dc2f86` ranks NFLX #2 on `distance_bps 0.0` with no basis field in any
+    row, so an 11-day spread of reading ages is invisible on one rank scale.)*
+
 <!-- /AUTO:journeys -->
 
 ## Anti-goals
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-desk-index.html               |  13 +-
 runs/goal-session-desk/.engine.lock/epoch          |   2 +-
 runs/goal-session-desk/.engine.lock/pid            |   2 +-
 runs/goal-session-desk/dispatch/.pump-alive        |   4 +-
 runs/goal-session-desk/engine.pid                  |   2 +-
 runs/goal-session-desk/session.json                |   6 +-
 runs/goal-session-desk/state/assumptions.md        | 219 ++-------------------
 .../state/assumptions.md.archive.md                | 204 +++++++++++++++++++
 runs/goal-session-desk/state/blueprint.md          |  14 +-
 runs/goal-session-desk/state/lessons.md            |  65 +-----
 runs/goal-session-desk/summary.md                  |  60 +++---
 runs/goal-session-desk/telemetry.jsonl             |  28 +++
 runs/goal-session-desk/trace/trace.jsonl           |   5 +
 13 files changed, 330 insertions(+), 294 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
