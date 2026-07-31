# Iteration diff (bounded)

Files changed: 7. Shown in full: 6.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_desk_screen_diff.py` (162 lines not shown)

```diff
diff --git a/apps/backend/app/research/desk_routes.py b/apps/backend/app/research/desk_routes.py
index d4fe2e7..1cfa461 100644
--- a/apps/backend/app/research/desk_routes.py
+++ b/apps/backend/app/research/desk_routes.py
@@ -61,6 +61,15 @@ itself is a pure read, mirroring ``GET /research/desk/topup/runs``'s single-sync
 exactly. No new MCP tool (``get_endpoint``'s existing ``/research/`` allowlist already reaches the
 new GET path); no new router, no ``main.py`` change.
 
+J-20 (this iteration, goal-desk-iter-35) adds ONE new read: ``GET /research/desk/screen/compare``
+(``?id=<compare id>&base=<base id>``) — how the named snapshot differs from the one recorded
+immediately before it, computed entirely by the new ``desk_screen_diff.py`` over two records already
+returned by ``get_screen_store``'s own ``ScreenStore.list()``. This route takes NO
+``BarStore``/``bar_index``/``DatasetStore`` dependency at all — it is structurally incapable of
+triggering ``compute_tradability`` or any other recompute. No new store, no new compute manager, no
+new MCP tool (the existing ``/research/`` allowlist already reaches the new path); no new router, no
+``main.py`` change.
+
 **Compute managers are module-level singletons here, NOT ``ResearchRegistry`` properties.**
 ``DeskTopupComputeManager`` (``desk_topup_compute.py``) reuses ``routes.record_bar_series``
 in-process, so it must import FROM ``routes.py`` — if ``ResearchRegistry`` held the manager (the
@@ -91,6 +100,7 @@ from .desk_index_reconcile import (
 )
 from .desk_screen import ScreenStore, resolve_desk_screen_dir
 from .desk_screen_compute import DeskScreenComputeManager
+from .desk_screen_diff import ScreenDiffSelfCompareError, compute_screen_diff
 from .desk_screen_log import ScreenRunStore, resolve_desk_screen_log_dir
 from .desk_topup_compute import DeskTopupComputeManager
 from .desk_topup_log import TopupRunStore, resolve_desk_topup_log_dir
@@ -387,6 +397,25 @@ def get_screen(
     }
 
 
+@router.get("/screen/compare")
+def get_screen_compare(
+    id: str, base: str | None = None, store: ScreenStore = Depends(get_screen_store)
+) -> dict:
+    """goal-desk-iter-35 (J-20): how the snapshot named by ``id`` differs from the snapshot recorded
+    immediately before it (or from ``base``, when given) — Data Contract addition, see
+    ``desk_screen_diff.py``'s module docstring for the full computation. A plain read over
+    ``store.list()`` only: this route takes NO ``BarStore``/``bar_index``/``DatasetStore``
+    dependency, so it is structurally incapable of triggering a ``compute_tradability`` call or any
+    other recompute (TC-9). ``id == base`` is refused as an honest 422 (``ScreenDiffSelfCompareError``
+    — "a snapshot compared with itself", never a silent zero-diff no-op); an unresolved ``id`` is an
+    honest ``{"compare": null, ...}`` at HTTP 200, mirroring ``GET /research/desk/screen?id=``'s own
+    unknown-id convention (never a 404)."""
+    try:
+        return compute_screen_diff(store, id, base)
+    except ScreenDiffSelfCompareError as exc:
+        raise HTTPException(status_code=422, detail=str(exc)) from exc
+
+
 class ScreenComputeRequest(BaseModel):
     """Body for ``POST /research/desk/screen/compute`` — ``screen_date`` is REQUIRED (FastAPI 422s
     a missing/absent body before the route handler runs, TC-9); this endpoint never defaults to
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 46fe418..296f656 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -10,6 +10,7 @@ import {
   fetchDeskReconcileRuns,
   fetchDeskScreen,
   fetchDeskScreenById,
+  fetchDeskScreenCompare,
   fetchDeskScreenCompute,
   fetchDeskScreenRuns,
   fetchDeskTopupCompute,
@@ -24,6 +25,9 @@ import type {
   DeskReconcileRun,
   DeskReconcileRunMeta,
   DeskReconcileRunsListResult,
+  DeskScreenCompareResult,
+  DeskScreenCompareRow,
+  DeskScreenCompareSnapshotMeta,
   DeskScreenComputeSnapshot,
   DeskScreenListResult,
   DeskScreenMeta,
@@ -1485,6 +1489,198 @@ function ScreenRunsSection({
   );
 }
 
+// --- Screen comparison (goal-desk-iter-35, J-20) — a new read-only disclosure of how the screen
+// `/desk` is currently DISPLAYING differs from the screen recorded immediately before it. A pure,
+// stateless GET (`GET /research/desk/screen/compare?id=<the displayed screen's own id>`), fed by
+// its own mount/id-change effect in the page component below — no new control, no recompute
+// trigger (page-load GETs never trigger a compute, T-4/5C). Rendered as the LAST section on the
+// page (after Screen Runs, in its own top-level `<section>` below `DeskPopulatedScreen`) so no
+// EXISTING golden's own first-visible-match text search can ever resolve into it instead of its
+// real target (goal.md step 6) — the section also introduces no attribute/selector any shipped
+// golden's click target matches (never `data-screen-id`/`desk-history-row`/`desk-screen-row`/any
+// `desk-row-*` testid; every testid here is its own `desk-screen-compare-*` namespace). Every value
+// rendered is a verbatim re-format of the compare endpoint's own response; the one client-side
+// operation is a plain array slice for the display cap (the shipped `EARLIER_PAIRS_DISPLAY_CAP`
+// pattern, `topupLibraryReach` above), never a re-rank, re-score, or client-derived diff.
+
+const SCREEN_COMPARE_ROWS_DISPLAY_CAP = 20;
+
+function ScreenCompareMeta({
+  label,
+  meta,
+  testid,
+}: {
+  label: string;
+  meta: DeskScreenCompareSnapshotMeta;
+  testid: string;
+}) {
+  return (
+    <div data-testid={testid} className="text-xs text-slate-400">
+      <p className="text-slate-300">{label}</p>
+      <p data-testid={`${testid}-id`}>id {meta.id}</p>
+      <p data-testid={`${testid}-dates`}>
+        screen date {meta.screen_date} · recorded {meta.created_utc}
+      </p>
+      <p data-testid={`${testid}-signature`}>bar-store signature {meta.bar_store_signature}</p>
+    </div>
+  );
+}
+
+// Every cell renders the served value verbatim; a `null` field is only ever reached on an
+// "entered"/"left" row (the symbol has no row at all on that side — `side`/`distance_bps` have
+// carried no legacy-absence case since J-03's very first shipment), so the honest copy names WHICH
+// snapshot has no row for this symbol — the J-08/J-13/J-14 legacy-absence phrasing pattern, applied
+// here to a structurally-absent row rather than an omitted field on an existing one.
+function ScreenCompareRowView({ row }: { row: DeskScreenCompareRow }) {
+  const compareRankText = row.compare_rank ?? "not recorded in the compared snapshot";
+  const baseRankText = row.base_rank ?? "not recorded in the base snapshot";
+  const compareSideText = row.compare_side ?? "not recorded in the compared snapshot";
+  const baseSideText = row.base_side ?? "not recorded in the base snapshot";
+  const compareDistanceText =
+    row.compare_distance_bps == null
+      ? "not recorded in the compared snapshot"
+      : fmt(row.compare_distance_bps);
+  const baseDistanceText =
+    row.base_distance_bps == null ? "not recorded in the base snapshot" : fmt(row.base_distance_bps);
+  return (
+    <tr
+      data-testid="desk-screen-compare-row"
+      className="border-b border-slate-800/60 last:border-b-0"
+    >
+      <td className={LABEL_CELL} data-testid="desk-screen-compare-row-symbol">
+        {row.symbol}
+      </td>
+      <td className={LABEL_CELL} data-testid="desk-screen-compare-row-status">
+        {row.status}
+      </td>
+      <td className={NUMERIC_CELL} data-testid="desk-screen-compare-row-compare-rank">
+        {compareRankText}
+      </td>
+      <td className={NUMERIC_CELL} data-testid="desk-screen-compare-row-base-rank">
+        {baseRankText}
+      </td>
+      <td className={NUMERIC_CELL} data-testid="desk-screen-compare-row-rank-change">
+        {row.rank_change ?? "—"}
+      </td>
+      <td className={LABEL_CELL} data-testid="desk-screen-compare-row-compare-side">
+        {compareSideText}
+      </td>
+      <td className={LABEL_CELL} data-testid="desk-screen-compare-row-base-side">
+        {baseSideText}
+      </td>
+      <td className={NUMERIC_CELL} data-testid="desk-screen-compare-row-compare-distance">
+        {compareDistanceText}
+      </td>
+      <td className={NUMERIC_CELL} data-testid="desk-screen-compare-row-base-distance">
+        {baseDistanceText}
+      </td>
+    </tr>
+  );
+}
+
+// The capped table of the COMPARE snapshot's own first N rows (goal.md step 5, the shipped
+// `EARLIER_PAIRS_DISPLAY_CAP` pattern) — "left" rows describe symbols the compare snapshot never
+// ranked at all, so they are excluded from "the compare snapshot's own first N rows" and never
+// counted toward the cap. Order is rendered EXACTLY as `rows` already carries it (the compare
+// snapshot's own served rank order) — no `.sort(`/`.reverse(` of any kind, only a `.slice(` for the
+// cap (never applied to a variable literally named `rows`, so this table's own cap can never be
+// mistaken for a client-side reorder of the ranked briefing table above).
+function ScreenCompareTable({ rows }: { rows: DeskScreenCompareRow[] }) {
+  const compareOrdered = rows.filter((entry) => entry.status !== "left");
+  if (compareOrdered.length === 0) {
+    return (
+      <EmptyState
+        testid="desk-screen-compare-rows-empty"
+        title="No members ranked in the compared snapshot."
+      />
+    );
+  }
+  const shown = compareOrdered.slice(0, SCREEN_COMPARE_ROWS_DISPLAY_CAP);
+  return (
+    <div>
+      {compareOrdered.length > SCREEN_COMPARE_ROWS_DISPLAY_CAP && (
+        <p data-testid="desk-screen-compare-cap-note" className="mb-1 text-xs text-slate-400">
+          showing {shown.length} of {compareOrdered.length} rows
+        </p>
+      )}
+      <table data-testid="desk-screen-compare-table" className="w-full border-collapse">
+        <thead>
+          <tr>
+            <th className={HEADER_CELL_LEFT}>symbol</th>
+            <th className={HEADER_CELL_LEFT}>status</th>
+            <th className={HEADER_CELL}>rank (this)</th>
+            <th className={HEADER_CELL}>rank (base)</th>
+            <th className={HEADER_CELL}>rank change</th>
+            <th className={HEADER_CELL_LEFT}>side (this)</th>
+            <th className={HEADER_CELL_LEFT}>side (base)</th>
+            <th className={HEADER_CELL}>distance (this)</th>
+            <th className={HEADER_CELL}>distance (base)</th>
+          </tr>
+        </thead>
+        <tbody>
+          {shown.map((row) => (
+            <ScreenCompareRowView key={row.symbol} row={row} />
+          ))}
+        </tbody>
+      </table>
+    </div>
+  );
+}
+
+// The section's own Loading/Unavailable/Populated states — mirrors `TopupRunsSection`'s/
+// `ScreenRunsSection`'s identical three-state shape, fed by its own mount/id-change effect in the
+// page component below. `data.compare === null` (an unresolved id) folds into the SAME Unavailable
+// rendering as a genuine fetch failure — this page never requests a compare for anything other
+// than the screen it is already displaying, so an honest "not found" here would only ever mean a
+// stale/raced fetch, not a state an operator can act on.
+function ScreenComparisonSection({
+  result,
+}: {
+  result: { ok: boolean; data: DeskScreenCompareResult | null; error?: string } | null;
+}) {
+  if (result === null) {
+    return <LoadingPanel testid="desk-screen-compare-loading" />;
+  }
+  if (!result.ok || result.data === null || result.data.compare === null) {
+    return (
+      <UnavailablePanel
+        testid="desk-screen-compare-unavailable"
+        message={result.error ?? "The screen comparison could not be loaded."}
+      />
+    );
+  }
+  const { compare, base, rows, identical, counts } = result.data;
+  return (
+    <div data-testid="desk-screen-compare-section" className="space-y-3">
+      <ScreenCompareMeta
+        label="This screen"
+        meta={compare}
+        testid="desk-screen-compare-meta-compare"
+      />
+      {base === null ? (
+        <p data-testid="desk-screen-compare-no-earlier" className="text-sm text-slate-400">
+          No earlier recorded screen exists to compare against.
+        </p>
+      ) : (
+        <>
+          <ScreenCompareMeta label="Compared against" meta={base} testid="desk-screen-compare-meta-base" />
+          <p data-testid="desk-screen-compare-counts" className="text-xs text-slate-400">
+            rows compared {counts.compared} · rank changed {counts.rank_changed} · side changed{" "}
+            {counts.side_changed} · entered {counts.entered} · left {counts.left}
+          </p>
+          {identical ? (
+            <p data-testid="desk-screen-compare-identical" className="text-sm text-slate-300">
+              The compared snapshots&apos; ranked rows are identical.
+            </p>
+          ) : (
+            <ScreenCompareTable rows={rows} />
+          )}
+        </>
+      )}
+    </div>
+  );
+}
+
 // --- Provenance line — snapshot id + recorded-at time, universe snapshot id + date, as_of,
 // config_fingerprint, and the pinned bar-store signature. -------------------------------------
 //
@@ -2029,6 +2225,16 @@ export default function DeskPage() {
   const [viewingSnapshot, setViewingSnapshot] = useState<DeskScreenSnapshot | null>(null);
   const [historyFetchError, setHistoryFetchError] = useState<string | null>(null);
 
+  // goal-desk-iter-35 (J-20): the Screen Comparison section's own fetch result, keyed off
+  // WHICHEVER screen is currently displayed (`viewingSnapshot ?? latest`, the SAME
+  // `displayedSnapshot` value computed below) — refetched by its own effect whenever that id
+  // changes, independent of the seven mount-time GETs above.
+  const [screenCompareResult, setScreenCompareResult] = useState<{
+    ok: boolean;
+    data: DeskScreenCompareResult | null;
+    error?: string;
+  } | null>(null);
+
   // Mount: seven GETs, zero POSTs (TC-19/TC-8, extended era-desk-iter-14/goal-desk-iter-29) — the
   // screen list/latest, ALL THREE compute managers' current/last snapshot (seeds a page load
   // mid-job or post-terminal without a spurious extra click — the /structure edge-report
@@ -2284,6 +2490,27 @@ export default function DeskPage() {
   // when it shares its `screen_date` with another recorded entry.
   const selectedHistoryId = viewingSnapshot?.id ?? latest?.id ?? null;
 
+  // goal-desk-iter-35 (J-20): fetch the Screen Comparison payload for whichever screen is
+  // currently DISPLAYED (`displayedSnapshot`'s own id, the SAME snapshot the Briefing/Provenance
+  // sections above already render) — a page-load/id-change GET only, never triggered by a click
+  // (no new control ships this iteration). Re-fetches whenever the displayed screen changes (a
+  // history row selected, or reverting to Latest); `alive` guards against a stale response landing
+  // after a fast second switch, mirroring every other mount-time fetch effect on this page.
+  useEffect(() => {
+    const id = displayedSnapshot?.id ?? null;
+    if (id === null) {
+      setScreenCompareResult(null);
+      return;
+    }
+    let alive = true;
+    fetchDeskScreenCompare(id).then((result) => {
+      if (alive) setScreenCompareResult(result);
+    });
+    return () => {
+      alive = false;
+    };
+  }, [displayedSnapshot]);
+
   return (
     <div className="min-h-screen">
       <main className="mx-auto max-w-7xl px-4 py-6">
@@ -2359,6 +2586,21 @@ export default function DeskPage() {
             <ScreenRunsSection result={screenRunsResult} />
           </Panel>
         </section>
+
+        {/* goal-desk-iter-35 (J-20): rendered LAST on the page — after the ranked briefing table
+            (inside DeskPopulatedScreen, far above) and after every other existing section — so no
+            shipped golden's own first-visible-match text search can resolve into it (goal.md step
+            6). Unlike Top-up Runs/Index Reconciliation/Screen Runs above, this section describes a
+            SPECIFIC screen (whichever one is currently displayed), so it only renders once a
+            screen exists at all (`latest !== null`) — mirroring the Briefing/Provenance sections'
+            own precondition instead of those three's "always rendered" one. */}
+        {latest !== null && (
+          <section aria-label="Screen Comparison" className="mt-6">
+            <Panel title="Screen Comparison">
+              <ScreenComparisonSection result={screenCompareResult} />
+            </Panel>
+          </section>
+        )}
       </main>
     </div>
   );
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index c70b4cf..f170c8a 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -8,6 +8,7 @@ import type {
   DatasetsListResult,
   DeskReconcileComputeSnapshot,
   DeskReconcileRunsListResult,
+  DeskScreenCompareResult,
   DeskScreenComputeSnapshot,
   DeskScreenListResult,
   DeskScreenRunsListResult,
@@ -1296,3 +1297,35 @@ export async function fetchDeskScreenRuns(): Promise<{
     return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
   }
 }
+
+// goal-desk-iter-35 (J-20): GET /research/desk/screen/compare?id= — how the named snapshot differs
+// from the screen recorded immediately before it, served VERBATIM (the default base; no `base=`
+// override ships a control this iteration — the section always describes whichever screen `/desk`
+// is currently DISPLAYING against ITS OWN default prior recording). Mirrors `fetchDeskScreenById`'s
+// exact `{ok, data, error}` shape; a 200 body is always returned (an unresolved `id` still comes
+// back `ok: true` with `data.compare === null` — the backend's own honest-null convention, never
+// surfaced here as an `ok: false` failure).
+export async function fetchDeskScreenCompare(id: string): Promise<{
+  ok: boolean;
+  data: DeskScreenCompareResult | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(
+      `${API_BASE}/research/desk/screen/compare?id=${encodeURIComponent(id)}`,
+    );
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskScreenCompareResult };
+    }
+    let error = "The screen comparison could not be loaded.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, data: null, error };
+  } catch {
+    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
+  }
+}
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 2ee6090..af9e498 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -1145,3 +1145,56 @@ export interface DeskScreenRunsListResult {
   latest: DeskScreenRun | null;
   integrity_errors: { file: string; error: string }[];
 }
+
+// goal-desk-iter-35 (J-20) -- the screen-comparison payload served by
+// `GET /research/desk/screen/compare`. `compare`/`base` are each a lightweight snapshot-identity
+// projection (pins + counts only -- never the full `rows`/`skipped` arrays, mirroring
+// `DeskScreenMeta`'s own convention); `base` is `null` on the ledger's oldest recorded snapshot
+// (`base_resolution: "none_earlier"`) or when an explicit `base=` id does not resolve
+// (`base_resolution` stays `"explicit"` either way -- a specific base WAS asked for, it just isn't
+// there). Every `compare_*`/`base_*` field on a row is copied VERBATIM from that snapshot's own
+// recorded row -- never derived client-side.
+export interface DeskScreenCompareSnapshotMeta {
+  id: string;
+  screen_date: string;
+  as_of: string;
+  created_utc: string;
+  bar_store_signature: string;
+  universe_snapshot_id: string | null;
+  ranked_count: number;
+  skipped_count: number;
+}
+
+export interface DeskScreenCompareRow {
+  symbol: string;
+  status: "compared" | "entered" | "left";
+  compare_rank: number | null;
+  base_rank: number | null;
+  rank_change: number | null;
+  compare_side: "support" | "resistance" | null;
+  base_side: "support" | "resistance" | null;
+  compare_band_class: "A" | "B" | "C" | null;
+  base_band_class: "A" | "B" | "C" | null;
+  compare_distance_bps: number | null;
+  base_distance_bps: number | null;
+  compare_basis_as_of: string | null;
+  base_basis_as_of: string | null;
+  skip_reason: "no_bars" | "no_basis" | null;
+}
+
+export interface DeskScreenCompareCounts {
+  compared: number;
+  rank_changed: number;
+  side_changed: number;
+  entered: number;
+  left: number;
+}
+
+export interface DeskScreenCompareResult {
+  compare: DeskScreenCompareSnapshotMeta | null;
+  base: DeskScreenCompareSnapshotMeta | null;
+  base_resolution: "explicit" | "default_prior_date" | "none_earlier" | null;
+  rows: DeskScreenCompareRow[];
+  identical: boolean;
+  counts: DeskScreenCompareCounts;
+}
diff --git a/apps/backend/app/research/desk_screen_diff.py b/apps/backend/app/research/desk_screen_diff.py
new file mode 100644
index 0000000..1878ee2
--- /dev/null
+++ b/apps/backend/app/research/desk_screen_diff.py
@@ -0,0 +1,242 @@
+"""Screen comparison (Era B "The Desk", J-20) -- discloses how the screen the operator is currently
+viewing differs from the screen recorded immediately before it. The Data Contract's "Screen
+comparison" row's ONE owner, served by ``GET /research/desk/screen/compare``.
+
+THIS MODULE computes NOTHING new about tradable structure and reads NO store of any kind -- it is a
+pure, stateless read over exactly two ALREADY-RECORDED, immutable snapshots fetched through
+``desk_screen.ScreenStore.list()`` (the SAME ``(records, errors)`` read ``GET /research/desk/screen``
+already performs for its ``?id=``/``?date=``/no-param branches). Every per-symbol field in the
+response is copied VERBATIM from one of the two snapshots' own recorded rows; ``rank_change`` is a
+plain integer subtraction of two already-recorded 1-based positions (the ``basis_age_days``
+precedent, ``desk_screen.py:388`` -- arithmetic over recorded values, never a new measurement). No
+``compute_tradability`` call, no ``BarStore``/``bar_index``/dataset read, no re-rank, no re-score --
+structurally impossible, since this module's only input is the two records themselves (it never
+receives a store reference of any kind, mirroring ``desk_screen._bar_store_signature``'s own
+"cannot call what it never received" argument).
+
+**Base resolution (goal.md J-20 step 2).** The default base for a compare snapshot is the recorded
+snapshot with the greatest ``screen_date`` STRICTLY earlier than the compare snapshot's own
+``screen_date``, ties (two recordings of one earlier date) broken by the later ``created_utc`` --
+exactly the record ``GET /research/desk/screen?date=<that earlier date>`` already serves
+(``matching[-1]``, ``desk_routes.py:381``), reusing ``ScreenStore.list()``'s own
+``(created_utc, id)``-ascending sort so the two reads can never disagree. An explicit ``base=<id>``
+overrides it. No earlier ``screen_date`` exists -> an honest ``base: null`` / ``base_resolution:
+"none_earlier"`` -- and, since there is then nothing to compare against, ``rows`` is empty rather
+than reporting every compare row as "entered" against a nonexistent base (a comparison needs TWO
+sides; "no earlier screen" is its own honest state, not "compare vs. nothing"). An unknown ``id`` (of
+either kind) is an honest ``null`` at HTTP 200 (the ``?id=`` convention, mirrored) -- never a 404 or
+a fabricated body. A snapshot compared with itself raises ``ScreenDiffSelfCompareError`` -- an
+honest refusal, never a silent zero-diff no-op.
+
+**Row construction (goal.md J-20 step 1).** Walked TWICE, each in a snapshot's own served rank
+order (never re-sorted): first every symbol ranked in the COMPARE snapshot (``"compared"`` when the
+base snapshot also ranked it, ``"entered"`` otherwise, carrying the base's own recorded skip
+``reason`` when its skip list names the symbol and an honest ``null`` when it does not mention the
+symbol at all); then every symbol ranked in the BASE snapshot that the compare snapshot's ranked set
+did NOT already cover (``"left"``, the mirror image, carrying the COMPARE snapshot's own recorded
+skip reason where it has one). ``rank_change`` is only ever set on a ``"compared"`` row.
+
+**Disclose, never judge (goal.md J-20 step 4).** ``rows`` carries no ordering by size of change --
+compare-ranked rows keep the compare snapshot's own served order, left rows are appended after in
+the base snapshot's own served order. ``counts``/``identical`` are plain tallies/equality checks,
+never a threshold, significance number, or "notable" framing.
+
+**No new ``Config`` field, no new store.** This module persists nothing -- no store, no file, no
+cache, no index. It takes a already-constructed ``ScreenStore`` and two ids; nothing here resolves
+a storage directory of its own.
+"""
+
+from __future__ import annotations
+
+from .desk_screen import ScreenStore
+
+# The four fields copied verbatim onto every "compared"/"entered"/"left" row, alongside `symbol`.
+# Kept as a tuple (not hardcoded per-field below) so the compare/base row-projection helper and its
+# call sites can never drift out of sync with each other.
+_DISCLOSED_FIELDS = ("side", "band_class", "distance_bps", "basis_as_of")
+
+
+class ScreenDiffSelfCompareError(Exception):
+    """A compare request named the SAME snapshot id as both the compare and the base -- an honest
+    refusal (goal.md J-20 step 2: "a snapshot compared with itself is an honest refusal, never a
+    silent no-op"), never a silent zero-diff body."""
+
+    def __init__(self, snapshot_id: str) -> None:
+        self.snapshot_id = snapshot_id
+        super().__init__(
+            f"cannot compare snapshot '{snapshot_id}' with itself -- a comparison requires two "
+            f"distinct recorded snapshots"
+        )
+
+
+def _snapshot_meta(record: dict) -> dict:
+    """The Data Contract's `compare`/`base` shape -- id/pins/created_utc/counts copied verbatim off
+    a full `ScreenStore.list()` record (never re-derived; `ranked_count`/`skipped_count` are plain
+    `len()`s of that SAME record's own `rows`/`skipped` lists)."""
+    return {
+        "id": record["id"],
+        "screen_date": record["screen_date"],
+        "as_of": record["as_of"],
+        "created_utc": record["created_utc"],
+        "bar_store_signature": record["bar_store_signature"],
+        "universe_snapshot_id": record["universe_snapshot_id"],
+        "ranked_count": len(record["rows"]),
+        "skipped_count": len(record["skipped"]),
+    }
+
+
+def _resolve_default_base(records: list[dict], compare_record: dict) -> dict | None:
+    """goal.md J-20 step 2: the recorded snapshot with the greatest `screen_date` STRICTLY earlier
+    than `compare_record`'s own `screen_date`, ties broken by the later `created_utc` -- exactly
+    `desk_routes.get_screen`'s own `?date=` branch's `matching[-1]` (`records` is already sorted
+    `(created_utc, id)` ascending by `ScreenStore.list()`, so the LAST of a same-date group is
+    always the latest-recorded one). `None` when no strictly-earlier `screen_date` exists at all."""
+    earlier = [r for r in records if r["screen_date"] < compare_record["screen_date"]]
+    if not earlier:
+        return None
+    newest_date = max(r["screen_date"] for r in earlier)
+    matching = [r for r in earlier if r["screen_date"] == newest_date]
+    return matching[-1]
+
+
+def _empty_counts() -> dict:
+    return {"compared": 0, "rank_changed": 0, "side_changed": 0, "entered": 0, "left": 0}
+
+
+def _not_found_response() -> dict:
+    """`?id=` (the compare snapshot) did not resolve to any recorded snapshot -- an honest
+    `compare: null` at HTTP 200 (never a 404/500/fabricated body), mirroring `GET
+    /research/desk/screen?id=`'s own unknown-id convention."""
+    return {
+        "compare": None,
+        "base": None,
+        "base_resolution": None,
+        "rows": [],
+        "identical": False,
+        "counts": _empty_counts(),
+    }
+
+
+def _diff_rows(compare_record: dict, base_record: dict) -> tuple[list[dict], dict, bool]:
+    """The row walk (goal.md J-20 step 1) -- compare-ranked rows first, in the compare snapshot's
+    OWN served order, then base-only ("left") rows in the base snapshot's OWN served order. Returns
+    `(rows, counts, identical)`."""
+    compare_rank_by_symbol = {row["symbol"]: i + 1 for i, row in enumerate(compare_record["rows"])}
+    base_rank_by_symbol = {row["symbol"]: i + 1 for i, row in enumerate(base_record["rows"])}
+    base_row_by_symbol = {row["symbol"]: row for row in base_record["rows"]}
+    compare_row_by_symbol = {row["symbol"]: row for row in compare_record["rows"]}
+    base_skip_reason_by_symbol = {s["symbol"]: s["reason"] for s in base_record["skipped"]}
+    compare_skip_reason_by_symbol = {s["symbol"]: s["reason"] for s in compare_record["skipped"]}
+
+    rows: list[dict] = []
+
+    for crow in compare_record["rows"]:
+        symbol = crow["symbol"]
+        brow = base_row_by_symbol.get(symbol)
+        if brow is not None:
+            status = "compared"
+            base_rank = base_rank_by_symbol[symbol]
+            # Sign convention: compare_rank - base_rank. Positive == the symbol's 1-based position
+            # moved to a HIGHER (worse) number since the base recording; negative == a LOWER
+            # (better) number. Purely descriptive (goal.md step 4: "never gives a direction a
+            # valence") -- the sign is not rendered as an arrow/colour anywhere.
+            rank_change = compare_rank_by_symbol[symbol] - base_rank
+            skip_reason = None
+        else:
+            status = "entered"
+            base_rank = None
+            rank_change = None
+            skip_reason = base_skip_reason_by_symbol.get(symbol)
+        row = {
+            "symbol": symbol,
+            "status": status,
+            "compare_rank": compare_rank_by_symbol[symbol],
+            "base_rank": base_rank,
+            "rank_change": rank_change,
+            "skip_reason": skip_reason,
+        }
+        for field in _DISCLOSED_FIELDS:
+            row[f"compare_{field}"] = crow.get(field)
+            row[f"base_{field}"] = brow.get(field) if brow is not None else None
+        rows.append(row)
+
+    for brow in base_record["rows"]:
+        symbol = brow["symbol"]
+        if symbol in compare_rank_by_symbol:
+            continue  # already emitted above as "compared"
+        row = {
+            "symbol": symbol,
+            "status": "left",
+            "compare_rank": None,
+            "base_rank": base_rank_by_symbol[symbol],
+            "rank_change": None,
+            "skip_reason": compare_skip_reason_by_symbol.get(symbol),
+        }
+        for field in _DISCLOSED_FIELDS:
+            row[f"compare_{field}"] = None
+            row[f"base_{field}"] = brow.get(field)
+        rows.append(row)
+
+    compared_rows = [r for r in rows if r["status"] == "compared"]
+    counts = {
+        "compared": len(compared_rows),
+        "rank_changed": sum(1 for r in compared_rows if r["rank_change"] != 0),
+        "side_changed": sum(1 for r in compared_rows if r["compare_side"] != r["base_side"]),
+        "entered": sum(1 for r in rows if r["status"] == "entered"),
+        "left": sum(1 for r in rows if r["status"] == "left"),
+    }
+    identical = (
+        counts["entered"] == 0
+        and counts["left"] == 0
+        and all(
+            r["rank_change"] == 0 and all(r[f"compare_{f}"] == r[f"base_{f}"] for f in _DISCLOSED_FIELDS)
+            for r in compared_rows
+        )
+    )
+    return rows, counts, identical
+
+
+def compute_screen_diff(store: ScreenStore, compare_id: str, base_id: str | None = None) -> dict:
+    """The comparison's ONE computation (goal.md J-20): read exactly two recorded snapshots via
+    ``store.list()`` and return the Data Contract's ``{compare, base, base_resolution, rows,
+    identical, counts}`` shape. Raises ``ScreenDiffSelfCompareError`` when ``base_id == compare_id``
+    (checked BEFORE any lookup, so a self-compare is refused even if the id happens not to resolve).
+    ``compare_id`` unresolved -> ``_not_found_response()`` (honest, HTTP-200-shaped null). An
+    explicit ``base_id`` that does not resolve is treated identically to "no earlier snapshot"
+    (``base: null``) but keeps ``base_resolution: "explicit"``, distinguishing "asked for a specific
+    base that does not exist" from "asked for the default and none exists"."""
+    if base_id is not None and base_id == compare_id:
+        raise ScreenDiffSelfCompareError(compare_id)
+
+    records, _errors = store.list()
+    by_id = {r["id"]: r for r in records}
+
+    compare_record = by_id.get(compare_id)
+    if compare_record is None:
+        return _not_found_response()
+
+    if base_id is not None:
+        base_record = by_id.get(base_id)
+        base_resolution = "explicit"
+    else:
+        base_record = _resolve_default_base(records, compare_record)
+        base_resolution = "default_prior_date" if base_record is not None else "none_earlier"
+
+    compare_meta = _snapshot_meta(compare_record)
+    base_meta = _snapshot_meta(base_record) if base_record is not None else None
+
+    if base_record is None:
+        rows: list[dict] = []
+        counts = _empty_counts()
+        identical = False
+    else:
+        rows, counts, identical = _diff_rows(compare_record, base_record)
+
+    return {
+        "compare": compare_meta,
+        "base": base_meta,
+        "base_resolution": base_resolution,
+        "rows": rows,
+        "identical": identical,
+        "counts": counts,
+    }
diff --git a/apps/backend/tests/test_desk_screen_compare_ui_guard.py b/apps/backend/tests/test_desk_screen_compare_ui_guard.py
new file mode 100644
index 0000000..efd19b5
--- /dev/null
+++ b/apps/backend/tests/test_desk_screen_compare_ui_guard.py
@@ -0,0 +1,107 @@
+"""goal-desk-iter-35 (J-20) source-introspection guard test -- the ``test_desk_ui_guards.py``
+pattern (read ``apps/frontend/app/desk/page.tsx`` as TEXT, assert on substrings/structure; no
+browser, no runtime) applied to the new Screen Comparison section.
+
+Proves the two structural properties goal.md J-20 step 6 names explicitly:
+
+  (a) the new section introduces no attribute/selector an EXISTING shipped golden's click target
+      could resolve into -- it never reuses ``data-screen-id``, ``desk-history-row``,
+      ``desk-screen-row``, or any ``desk-row-*`` testid.
+  (b) the section is rendered strictly AFTER the ranked briefing table in the actual JSX call
+      order (not merely the source TEXT order of function *definitions*, which does not determine
+      DOM order) -- so the replay tool's first-visible-match text search
+      (``incredible_auto_dev/scripts/automation/lib/demo_runner.py:641``) can never resolve into
+      it instead of its real target.
+
+A guard that can never fail proves nothing -- each check carries a seeded counter-test."""
+
+from __future__ import annotations
+
+import pathlib
+import re
+
+_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
+_DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"
+
+# Actual JSX ATTRIBUTE usages only (`data-testid="..."`/`data-screen-id=...`) -- a bare mention of
+# these names in a prose comment (this guard's OWN docstring included) must never trip the check,
+# so the pattern requires the real attribute syntax, not just the substring anywhere in the file.
+_FORBIDDEN_TESTID_ATTRS = ('data-testid="desk-history-row"', 'data-testid="desk-screen-row"')
+# `data-screen-id` (`DeskHistoryRow`, `page.tsx:759`) is its OWN bare custom attribute, not a
+# `data-testid` value -- checked separately, by its real attribute-name syntax.
+_FORBIDDEN_DATA_SCREEN_ID_ATTR = "data-screen-id="
+_FORBIDDEN_ROW_TESTID_ATTR_RE = re.compile(r'data-testid="desk-row-[a-z-]+"')
+
+
+def _compare_block(source: str) -> str:
+    """The full source text of every J-20 component definition -- from the section's own leading
+    comment through the next section's own leading comment, so every helper component
+    (``ScreenCompareMeta``/``ScreenCompareRowView``/``ScreenCompareTable``/
+    ``ScreenComparisonSection``) is covered, never just one of them."""
+    start = source.index("// --- Screen comparison (goal-desk-iter-35, J-20)")
+    end = source.index("// --- Provenance line", start)
+    return source[start:end]
+
+
+def test_screen_comparison_block_never_reuses_a_golden_click_target_testid():
+    block = _compare_block(_DESK_PAGE.read_text())
+    attr_hits = [attr for attr in _FORBIDDEN_TESTID_ATTRS if attr in block]
+    assert not attr_hits, (
+        f"the Screen Comparison section reuses the JSX attribute(s) {attr_hits} -- it must "
+        "introduce ONLY its own desk-screen-compare-* testids, never an attribute an existing "
+        "golden's click target already matches"
+    )
+    assert _FORBIDDEN_DATA_SCREEN_ID_ATTR not in block, (
+        "the Screen Comparison section reuses the data-screen-id attribute"
+    )
+    row_hits = _FORBIDDEN_ROW_TESTID_ATTR_RE.findall(block)
+    assert not row_hits, (
+        f"the Screen Comparison section reuses desk-row-* testid attribute(s) {row_hits} -- it "
+        "must never share a selector with the ranked briefing table's own row cells"
+    )
+
+
+def test_screen_comparison_block_reused_testid_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail -- a lint that cannot fail proves nothing."""
+    seeded_source = '<tr data-testid="desk-screen-row">'
+    attr_hits = [attr for attr in _FORBIDDEN_TESTID_ATTRS if attr in seeded_source]
+    assert attr_hits == ['data-testid="desk-screen-row"']
+
+    seeded_row_source = '<td data-testid="desk-row-symbol">'
+    assert _FORBIDDEN_ROW_TESTID_ATTR_RE.findall(seeded_row_source) == ['data-testid="desk-row-symbol"']
+
+    # and a bare PROSE mention (this guard's own docstring style) must NOT trip either check --
+    # the lint targets real JSX attribute syntax only.
+    seeded_prose = "// never reuses desk-screen-row or any desk-row-* testid"
+    assert not [attr for attr in _FORBIDDEN_TESTID_ATTRS if attr in seeded_prose]
+    assert _FORBIDDEN_ROW_TESTID_ATTR_RE.findall(seeded_prose) == []
+
+
+def test_screen_comparison_section_is_used_after_the_ranked_table_in_render_order():
+    """(b): the ranked table's own JSX CALL site (``<DeskRowsTable``, rendered inside
+    ``DeskPopulatedScreen``) precedes the new section's own JSX CALL site
+    (``<ScreenComparisonSection``, rendered as the page's own last section) -- comparing call
+    sites, not component *definitions* (which do not determine DOM order in JS/TSX)."""
+    source = _DESK_PAGE.read_text()
+    ranked_table_call = source.index("<DeskRowsTable")
+    compare_section_call = source.index("<ScreenComparisonSection")
+    assert compare_section_call > ranked_table_call, (
+        "<ScreenComparisonSection> is rendered before <DeskRowsTable> -- the Screen Comparison "
+        "section must render strictly AFTER the ranked briefing table so the replay tool's "
+        "first-visible-match text search cannot resolve into it"
+    )
+
+
+def test_render_order_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail -- a lint that cannot fail proves nothing."""
+    seeded_source = "<ScreenComparisonSection result={x} />\n<DeskRowsTable rows={y} asOf={z} />"
+    ranked_table_call = seeded_source.index("<DeskRowsTable")
+    compare_section_call = seeded_source.index("<ScreenComparisonSection")
+    assert not (compare_section_call > ranked_table_call)
+
+
+def test_screen_comparison_section_carries_its_own_namespaced_testid():
+    """A cheap sanity check that the section's own root testid actually exists at all -- otherwise
+    the two tests above would both vacuously pass on a page that never renders the section."""
+    source = _DESK_PAGE.read_text()
+    assert 'data-testid="desk-screen-compare-section"' in source
diff --git a/apps/backend/tests/test_desk_screen_diff.py b/apps/backend/tests/test_desk_screen_diff.py
new file mode 100644
index 0000000..f96eeae
--- /dev/null
+++ b/apps/backend/tests/test_desk_screen_diff.py
@@ -0,0 +1,556 @@
+"""``desk_screen_diff.py`` (Era B "The Desk", J-20) -- the screen-comparison computation over
+planted, scoped ``ScreenStore`` snapshots (goal.md step 6: "Backend tests over planted scoped
+snapshots"). Synthetic ``AAA``/``BBB``/``CCC``... symbols are used throughout (the
+``test_desk_screen_compute.py``/``test_desk_topup_compute.py`` convention for generic plumbing
+tests over planted store records) -- lessons.md iter-2's "never a synthetic symbol for a clause
+naming a REAL symbol" applies to ``compute_screen``'s real-tradability cross-checks, not to this
+module's pure row-diffing logic, which names no real symbol in its own acceptance criteria.
+
+Route-level tests (``GET /research/desk/screen/compare``) live in the second half of this file,
+mirroring ``test_desk_screen.py``'s ``screen_route_ctx``/``_plant_same_date_pair`` fixtures.
+"""
+
+from __future__ import annotations
+
+import hashlib
+import json
+
+import pytest
+
+from app.config import CONFIG
+from app.research.desk_screen import ScreenStore
+from app.research.desk_screen_diff import (
+    ScreenDiffSelfCompareError,
+    compute_screen_diff,
+)
+
+UNIVERSE_SNAPSHOT_ID = "universe-2026-01-01-000000000000"
+BAR_STORE_SIGNATURE = "aaaaaaaaaaaaaaaa"
+
+
+def _row(symbol: str, *, side="resistance", band_class="B", distance_bps=10.0,
+         basis_as_of="2026-01-01T04:00:00.000000Z", omit: tuple[str, ...] = ()) -> dict:
+    """A minimal ranked-row dict carrying only the four fields this module discloses
+    (``side``/``band_class``/``distance_bps``/``basis_as_of``) plus ``symbol`` -- ``ScreenStore``
+    performs no row-shape validation, so a planted test row never needs the full
+    ``compute_screen``-produced shape. ``omit`` drops named keys entirely (the legacy-row
+    precedent, TC-10)."""
+    row = {
+        "symbol": symbol, "side": side, "band_class": band_class, "distance_bps": distance_bps,
+        "basis_as_of": basis_as_of,
+    }
+    for key in omit:
+        row.pop(key, None)
+    return row
+
+
+def _skip(symbol: str, reason: str = "no_bars") -> dict:
+    return {"symbol": symbol, "skipped": True, "reason": reason}
+
+
+def _plant(store: ScreenStore, *, screen_date: str, rows: list[dict], skipped: list[dict] | None = None,
+           bar_store_signature: str = BAR_STORE_SIGNATURE) -> dict:
+    return store.record(
+        screen_date=screen_date, as_of=f"{screen_date}T23:59:59Z",
+        universe_snapshot_id=UNIVERSE_SNAPSHOT_ID, config_fingerprint=CONFIG.config_fingerprint(),
+        bar_store_signature=bar_store_signature, rows=rows, skipped=skipped or [],
+    )
+
+
+@pytest.fixture
+def store(tmp_path) -> ScreenStore:
+    return ScreenStore(tmp_path / "screen")
+
+
+def _row_by_symbol(result: dict, symbol: str) -> dict:
+    matching = [r for r in result["rows"] if r["symbol"] == symbol]
+    assert len(matching) == 1, f"expected exactly one row for {symbol!r}, got {len(matching)}"
+    return matching[0]
+
+
+# ==================================================================================================
+# TC-1: identical ranked rows report zero changes
+# ==================================================================================================
+
+
+def test_identical_ranked_rows_report_zero_changes(store):
+    _plant(store, screen_date="2026-01-01", rows=[_row("AAA"), _row("BBB", side="support")])
+    later = _plant(store, screen_date="2026-01-02", rows=[_row("AAA"), _row("BBB", side="support")])
+
+    result = compute_screen_diff(store, later["id"])
+
+    assert result["identical"] is True
+    assert result["counts"] == {
+        "compared": 2, "rank_changed": 0, "side_changed": 0, "entered": 0, "left": 0,
+    }
+    assert result["base_resolution"] == "default_prior_date"
+    for row in result["rows"]:
+        assert row["status"] == "compared"
+        assert row["rank_change"] == 0
+        assert row["compare_side"] == row["base_side"]
+        assert row["compare_band_class"] == row["base_band_class"]
+        assert row["compare_distance_bps"] == row["base_distance_bps"]
+        assert row["compare_basis_as_of"] == row["base_basis_as_of"]
+
+
+# ==================================================================================================
+# TC-2/TC-4/TC-5 (compound, goal.md's own worked acceptance): a moved rank, a flipped side, an
+# entered symbol, and a left symbol -- each reported EXACTLY ONCE with both recorded values verbatim.
+# ==================================================================================================
+
+
+def test_moved_rank_flipped_side_entered_and_left_each_report_exactly_once(store):
+    base = _plant(
+        store, screen_date="2026-01-01",
+        rows=[
+            _row("AAA", side="resistance", band_class="A", distance_bps=5.0),   # rank 1
+            _row("BBB", side="support", band_class="B", distance_bps=20.0),    # rank 2
+            _row("CCC", side="support", band_class="C", distance_bps=50.0),    # rank 3 -- will "leave"
+        ],
+    )
+    compare = _plant(
+        store, screen_date="2026-01-02",
+        rows=[
+            _row("BBB", side="resistance", band_class="B", distance_bps=20.0),  # rank 1 -- flipped side
+            _row("AAA", side="resistance", band_class="A", distance_bps=5.0),   # rank 2 -- moved from 1
+            _row("DDD", side="support", band_class="C", distance_bps=99.0),     # rank 3 -- "entered"
+        ],
+    )
+
+    result = compute_screen_diff(store, compare["id"], base["id"])
+
+    assert result["base_resolution"] == "explicit"
+    assert result["identical"] is False
+    assert len(result["rows"]) == 4  # AAA, BBB, DDD (compare order) + CCC (left)
+
+    aaa = _row_by_symbol(result, "AAA")
+    assert aaa["status"] == "compared"
+    assert aaa["base_rank"] == 1 and aaa["compare_rank"] == 2
+    assert aaa["rank_change"] == 1
+    assert aaa["compare_side"] == aaa["base_side"] == "resistance"
+
+    bbb = _row_by_symbol(result, "BBB")
+    assert bbb["status"] == "compared"
+    assert bbb["base_rank"] == 2 and bbb["compare_rank"] == 1
+    assert bbb["rank_change"] == -1
+    assert bbb["base_side"] == "support" and bbb["compare_side"] == "resistance"
+
+    ddd = _row_by_symbol(result, "DDD")
+    assert ddd["status"] == "entered"
+    assert ddd["base_rank"] is None and ddd["compare_rank"] == 3
+    assert ddd["compare_side"] == "support" and ddd["base_side"] is None
+    assert ddd["skip_reason"] is None  # base doesn't mention DDD at all
+
+    ccc = _row_by_symbol(result, "CCC")
+    assert ccc["status"] == "left"
+    assert ccc["compare_rank"] is None and ccc["base_rank"] == 3
+    assert ccc["base_side"] == "support" and ccc["compare_side"] is None
+    assert ccc["skip_reason"] is None  # compare doesn't mention CCC at all
+
+    assert result["counts"] == {
+        "compared": 2, "rank_changed": 2, "side_changed": 1, "entered": 1, "left": 1,
+    }
+
+
+# ==================================================================================================
+# TC-4: an entered symbol carries the base's own recorded skip reason when it has one
+# ==================================================================================================
+
+
+def test_entered_symbol_carries_the_base_skip_reason_when_it_has_one(store):
+    base = _plant(store, screen_date="2026-01-01", rows=[_row("AAA")], skipped=[_skip("EEE", "no_bars")])
+    compare = _plant(store, screen_date="2026-01-02", rows=[_row("AAA"), _row("EEE")])
+
+    result = compute_screen_diff(store, compare["id"], base["id"])
+
+    eee = _row_by_symbol(result, "EEE")
+    assert eee["status"] == "entered"
+    assert eee["skip_reason"] == "no_bars"
+
+
+# ==================================================================================================
+# TC-5: a left symbol carries the compare's own recorded skip reason when it has one
+# ==================================================================================================
+
+
+def test_left_symbol_carries_the_compare_skip_reason_when_it_has_one(store):
+    base = _plant(store, screen_date="2026-01-01", rows=[_row("AAA"), _row("FFF")])
+    compare = _plant(
+        store, screen_date="2026-01-02", rows=[_row("AAA")], skipped=[_skip("FFF", "no_basis")]
+    )
+
+    result = compute_screen_diff(store, compare["id"], base["id"])
+
+    fff = _row_by_symbol(result, "FFF")
+    assert fff["status"] == "left"
+    assert fff["skip_reason"] == "no_basis"
+
+
+# ==================================================================================================
+# TC-3: the oldest recorded snapshot reports the honest no-earlier-screen state
+# ==================================================================================================
+
+
+def test_oldest_recorded_snapshot_reports_the_honest_no_earlier_screen_state(store):
+    only = _plant(store, screen_date="2026-01-01", rows=[_row("AAA")])
+
+    result = compute_screen_diff(store, only["id"])
+
+    assert result["base"] is None
+    assert result["base_resolution"] == "none_earlier"
+    assert result["rows"] == []
+    assert result["counts"] == {"compared": 0, "rank_changed": 0, "side_changed": 0, "entered": 0, "left": 0}
+    assert result["compare"]["id"] == only["id"]
+
+
+# ==================================================================================================
+# TC-6: the same two ids requested twice in succession produce a byte-identical body
+# ==================================================================================================
+
+
+def test_the_same_two_ids_requested_twice_produce_a_byte_identical_body(store):
+    base = _plant(store, screen_date="2026-01-01", rows=[_row("AAA")])
+    compare = _plant(store, screen_date="2026-01-02", rows=[_row("AAA")])
+
+    first = compute_screen_diff(store, compare["id"], base["id"])
+    second = compute_screen_diff(store, compare["id"], base["id"])
+
+    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
+
+
+# ==================================================================================================
+# TC-7: an unknown snapshot id is an honest null, never an error
+# ==================================================================================================
+
+
+def test_unknown_compare_id_is_an_honest_null(store):
+    _plant(store, screen_date="2026-01-01", rows=[_row("AAA")])
+
+    result = compute_screen_diff(store, "does-not-exist")
+
+    assert result["compare"] is None
+    assert result["base"] is None
+    assert result["base_resolution"] is None
+    assert result["rows"] == []
+    assert result["identical"] is False
+
+
+def test_unknown_explicit_base_id_is_an_honest_null_but_stays_explicit(store):
+    """An explicit ``base=`` that does not resolve is distinct from "no earlier snapshot exists at
+    all" -- ``base_resolution`` stays ``"explicit"`` (a specific base WAS asked for; it just isn't
+    there), never silently reclassified as ``"none_earlier"``."""
+    compare = _plant(store, screen_date="2026-01-02", rows=[_row("AAA")])
+
+    result = compute_screen_diff(store, compare["id"], "does-not-exist")
+
+    assert result["base"] is None
+    assert result["base_resolution"] == "explicit"
+    assert result["rows"] == []
+
+
+# ==================================================================================================
+# TC-8: a snapshot compared with itself is an honest refusal, never a silent zero-diff no-op
+# ==================================================================================================
+
+
+def test_self_compare_is_refused(store):
+    only = _plant(store, screen_date="2026-01-01", rows=[_row("AAA")])
+
+    with pytest.raises(ScreenDiffSelfCompareError) as excinfo:
+        compute_screen_diff(store, only["id"], only["id"])
+    assert only["id"] in str(excinfo.value)
+
+
+def test_self_compare_is_refused_even_when_the_id_does_not_resolve():
+    """The self-compare check runs BEFORE any store lookup -- ``id == base`` is refused
+    unconditionally, never silently falling through to the not-found branch."""
+    store = ScreenStore.__new__(ScreenStore)  # never touched -- proves no lookup precedes the check
+    with pytest.raises(ScreenDiffSelfCompareError):
+        compute_screen_diff(store, "same-id", "same-id")
+
+
+# ==================================================================================================
+# TC-9: zero compute_tradability / BarStore / bar_index / dataset read of any kind -- structural,
+# not merely behavioral: this module never imports any of those names in the first place.
+# ==================================================================================================
+
+
+def test_module_imports_no_store_or_compute_dependency():
+    import app.research.desk_screen_diff as module
+
+    for forbidden_name in ("BarStore", "compute_tradability", "BarIndex", "DatasetStore"):
+        assert not hasattr(module, forbidden_name), (
+            f"desk_screen_diff.py imports {forbidden_name!r} -- it must be structurally incapable "
+            "of a BarStore/bar_index/dataset read or a compute_tradability call, since it never "
+            "receives a store reference of any kind"
+        )
+
+
+def test_compute_screen_diff_only_calls_screen_store_list(store, monkeypatch):
+    """A call-count instrumentation counterpart to the structural test above -- the ONE method this
+    module calls on its store argument is ``list()``, exactly once per ``compute_screen_diff``
+    invocation (mirrors ``test_bar_store_signature_issues_zero_bar_store_calls``'s instrumentation
+    style)."""
+    base = _plant(store, screen_date="2026-01-01", rows=[_row("AAA")])
+    compare = _plant(store, screen_date="2026-01-02", rows=[_row("AAA")])
+
+    calls: list[str] = []
+    original_list = ScreenStore.list
+
+    def _tracked_list(self):
+        calls.append("list")
+        return original_list(self)
+
+    monkeypatch.setattr(ScreenStore, "list", _tracked_list)
+
+    compute_screen_diff(store, compare["id"], base["id"])
+
+    assert calls == ["list"]
+
+
+# ==================================================================================================
+# TC-10: a legacy base row missing basis_as_of is reported absent, never derived or backfilled
+# ==================================================================================================
+
+
+def test_legacy_base_row_missing_basis_as_of_is_reported_absent_never_derived(store):
+    base = _plant(store, screen_date="2026-01-01", rows=[_row("AAA", omit=("basis_as_of",))])
+    compare = _plant(store, screen_date="2026-01-02", rows=[_row("AAA", basis_as_of="2026-01-02T04:00:00.000000Z")])
+
+    result = compute_screen_diff(store, compare["id"], base["id"])
+
+    aaa = _row_by_symbol(result, "AAA")
+    assert aaa["base_basis_as_of"] is None
+    assert aaa["compare_basis_as_of"] == "2026-01-02T04:00:00.000000Z"
+
+
+# ==================================================================================================
+# Row order: each snapshot's own served order, never re-sorted
+# ==================================================================================================
+
+
+def test_rows_use_each_snapshots_own_served_order_never_resorted(store):
+    base = _plant(store, screen_date="2026-01-01", rows=[_row("ZZZ"), _row("MMM")])  # deliberately non-alpha
+    compare = _plant(store, screen_date="2026-01-02", rows=[_row("BBB"), _row("ZZZ"), _row("AAA")])
+
+    result = compute_screen_diff(store, compare["id"], base["id"])
+
+    symbols = [r["symbol"] for r in result["rows"]]
+    # compare-ranked symbols first, in compare's own served order (BBB, ZZZ, AAA), then base-only
+    # ("left") symbols in base's own served order (MMM, since ZZZ was already emitted above).
+    assert symbols == ["BBB", "ZZZ", "AAA", "MMM"]
+
+
+# ==================================================================================================
+# Default base resolution -- greatest strictly-earlier screen_date, ties broken by later created_utc
+# ==================================================================================================
+
+
+def test_default_base_picks_the_greatest_strictly_earlier_screen_date(store):
+    _plant(store, screen_date="2026-01-01", rows=[_row("AAA")])
+    middle = _plant(store, screen_date="2026-01-05", rows=[_row("AAA")])
+    compare = _plant(store, screen_date="2026-01-10", rows=[_row("AAA")])
+
+    result = compute_screen_diff(store, compare["id"])
+
+    assert result["base"]["id"] == middle["id"]
+    assert result["base_resolution"] == "default_prior_date"
+
+
+def test_default_base_tie_break_prefers_the_later_created_utc_among_same_earlier_date(store):
+    _plant(store, screen_date="2026-01-01", rows=[_row("AAA")], bar_store_signature="a" * 16)
+    later_same_date = _plant(
+        store, screen_date="2026-01-01", rows=[_row("AAA")], bar_store_signature="b" * 16
+    )
+    compare = _plant(store, screen_date="2026-01-02", rows=[_row("AAA")])
+
+    result = compute_screen_diff(store, compare["id"])
+
+    assert result["base"]["id"] == later_same_date["id"]
+
+
+def test_ranked_count_and_skipped_count_are_plain_lengths(store):
+    base = _plant(
+        store, screen_date="2026-01-01", rows=[_row("AAA"), _row("BBB")],
+        skipped=[_skip("CCC"), _skip("DDD"), _skip("EEE")],
+    )
+    compare = _plant(store, screen_date="2026-01-02", rows=[_row("AAA")], skipped=[])
+
+    result = compute_screen_diff(store, compare["id"], base["id"])
+
+    assert result["base"]["ranked_count"] == 2
+    assert result["base"]["skipped_count"] == 3
+    assert result["compare"]["ranked_count"] == 1
+    assert result["compare"]["skipped_count"] == 0
+
+
+def test_snapshot_meta_carries_every_named_field_verbatim(store):
+    compare = _plant(store, screen_date="2026-01-02", rows=[_row("AAA")])
+
+    result = compute_screen_diff(store, compare["id"])
+
+    meta = result["compare"]
+    assert meta["id"] == compare["id"]
+    assert meta["screen_date"] == compare["screen_date"]
... [diff_bound] apps/backend/tests/test_desk_screen_diff.py: 162 more diff lines omitted — Read the file for full detail
```
