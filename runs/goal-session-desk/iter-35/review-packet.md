# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

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
diff --git a/docs/goal.md b/docs/goal.md
index 8e1621f..150bab4 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -1671,6 +1671,149 @@ order: J-01 → J-02 → J-03 → J-04 → J-05 → J-06, with J-07 guarding con
     window ends at wall-clock today for every pair it applies to, so after the next daily top-up even
     that faint request-bound difference collapses to one identical date for every successful pair.)*
 
+- **J-20: Every recorded screen states how it differs from the screen recorded before it**
+  - Steps:
+    1. Compare exactly TWO already-recorded snapshots, read verbatim through the accessor that already
+       owns them — `ScreenStore.list()` (`desk_screen.py:581`, the SAME `(records, errors)` read all
+       three branches of `GET /research/desk/screen` already make, `desk_routes.py:353`/`:377`/`:381`).
+       For every symbol ranked in the COMPARE snapshot, in that snapshot's OWN served rank order (the
+       order J-03 step 2 already records as data — never re-sorted, never re-ranked, never re-scored),
+       copy VERBATIM its own 1-based position plus its recorded `side`, `band_class`, `distance_bps`
+       and `basis_as_of`, and the same values from the BASE snapshot's own recorded row for that
+       symbol, plus `rank_change` — a plain integer subtraction of two ALREADY-RECORDED positions (the
+       `basis_age_days` precedent, `desk_screen.py:388`: arithmetic over recorded values, never a new
+       measurement). A symbol ranked in the compare snapshot but not in the base is reported as
+       `entered` carrying the base snapshot's own recorded skip `reason` (`no_bars`/`no_basis`) when it
+       has one and an honest `null` when that snapshot does not mention the symbol at all; a symbol
+       ranked in the base but not in the compare is `left`, the same way. **Zero diff** to
+       `desk_screen.py`'s recorded row/snapshot shapes and to
+       `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`desk_coverage.py`; zero new `Config`
+       field; no `BarStore`, `bar_index` or dataset read of ANY kind; and nothing is recomputed — no
+       `compute_tradability` call, no band selection, no rank-key evaluation (assert the call counts,
+       the J-11/J-13/J-14/J-15 precedent).
+    2. Resolve the base in the OWNER, never on the page: the default base for a compare snapshot is the
+       recorded snapshot with the greatest `screen_date` STRICTLY earlier than the compare snapshot's
+       own `screen_date`, ties (two recordings of one earlier date) broken by the later `created_utc` —
+       i.e. exactly the record `GET /research/desk/screen?date=<that earlier date>` already serves
+       (`matching[-1]`, `desk_routes.py:381`), so the two reads can never disagree. An explicit
+       `base=<id>` overrides it. The payload ALWAYS names both snapshots it compared — `id`,
+       `screen_date`, `as_of`, `created_utc`, `bar_store_signature`, `universe_snapshot_id` and
+       ranked/skipped counts, each copied verbatim from that record's own meta — and states how the
+       base was chosen. When no earlier `screen_date` exists the payload is an honest "no earlier
+       recorded screen" state with `base: null`, never a fabricated comparison; an unknown id is an
+       honest `null` at HTTP 200 (the `?id=` convention, `desk_routes.py:377`); a snapshot compared
+       with itself is an honest refusal, never a silent no-op.
+    3. Own it exactly once: a new desk module (name at build discretion, e.g.
+       `app/research/desk_screen_diff.py`) as the ONLY owner and ONE serving endpoint (exact path at
+       build discretion, e.g. `GET /research/desk/screen/compare`) — registered as a NEW row in the
+       blueprint's Data Contract BEFORE the code lands. It PERSISTS NOTHING: no store, no file, no
+       cache, no index, no new `Config` field, no new MCP tool (J-06's exactly-17-tool contract stays
+       green and `get_endpoint`'s `/research/` allowlist already reaches the new path). The GET
+       recomputes nothing, writes nothing and triggers nothing (the 5C lesson); screen rows, skip rows,
+       the five-pin snapshot key and the rank key keep `desk_screen.ScreenStore` as their sole owner
+       and `GET /research/desk/screen` as their sole serving endpoint, and nothing about what a
+       snapshot records, how it is keyed, or how rows are ranked changes. Determinism is structural:
+       the body is a pure function of two IMMUTABLE recorded files, so the same two ids reproduce a
+       byte-identical body, and the payload carries no wall-clock field of its own (T-6).
+    4. Disclose, never judge. This journey states what two recordings say and stops there: it never
+       ranks, filters, gates, weights, scores, or orders by size of change, and it never measures
+       whether a wall held, broke, was reached, or produced any reaction — outcome measurement is
+       era-6 "The Referee" and stays entirely out (this era's Non-Goals). Concretely: no threshold, no
+       significance/confidence number, no churn/stability/volatility metric, no "notable"/"biggest
+       mover"/"top movers" framing, no ordering by `|rank_change|` anywhere (the compare snapshot's own
+       served order is the only order), no arrow or colour that gives a direction a valence, and no
+       advice, imperative, urgency or prediction language; `tests/test_copy_discipline.py` stays green
+       unmodified.
+    5. Surface it on `/desk` as ONE new read-only "Screen Comparison" section rendered AFTER the ranked
+       briefing table, beside the shipped Screen History / Top-up Runs / Index Reconciliation / Screen
+       Runs sections (the same table-plus-detail pattern, no new control, no recompute, page-load GETs
+       trigger nothing): both snapshots' own ids, screen dates, recorded-at and `bar_store_signature`s;
+       one descriptive counts line (rows compared, rank changed, side changed, entered, left); an
+       honest "the compared snapshots' ranked rows are identical" line when every compared field
+       matches; the honest no-earlier-screen state; and a capped table of the compare snapshot's own
+       first N rows (the shipped `EARLIER_PAIRS_DISPLAY_CAP` precedent,
+       `apps/frontend/app/desk/page.tsx:882`/`:1032`, with its honest "showing N of M" line) each
+       showing the symbol, this snapshot's recorded rank/side/distance and the base's own recorded
+       rank/side/distance, with an honest "not recorded in the compared snapshot" for a field the
+       base's row does not carry (the J-08/J-13/J-14 legacy-absence pattern) — never a value derived on
+       the page. The section describes whichever snapshot the page is DISPLAYING (the shipped `?id=`
+       history selection), so opening a past screen compares THAT screen. **No new ranked-table column
+       and no change to the ranked table**, so J-16's measured width contract stands untouched.
+    6. Keep every browser and test contract the shipped journeys rest on, and test fixture-scoped:
+       every existing `data-testid` keeps its element and its exact text; the new section introduces no
+       attribute or selector an existing golden's click target can match (it never reuses
+       `data-screen-id`, `desk-history-row`, `desk-screen-row` or any `desk-row-*` testid) and —
+       because the replay tool's text matcher takes the FIRST visible match
+       (`incredible_auto_dev/scripts/automation/lib/demo_runner.py:641`) — it renders after the ranked
+       table so no stored expect (J-16.json's `BRK-B`, J-13/J-14's literal band strings,
+       J-12/J-13/J-14's snapshot ids) can resolve into it; all 19 stored golden replay scripts replay
+       green with ZERO script edits and `tests/test_desk_ui_guards.py` +
+       `tests/test_desk_hover_tooltip_guard.py` pass unmodified. Backend tests over planted scoped
+       snapshots: two snapshots whose ranked rows are identical report zero changes; a pair with moved
+       ranks, a flipped side, an entered symbol and a left symbol reports each exactly once with both
+       recorded values verbatim; the oldest recorded snapshot reports the honest no-earlier-screen
+       state; an unknown id is an honest null; the same two ids twice produce a byte-identical body;
+       the GET writes nothing and issues no `compute_tradability` call (assert the call count); and a
+       legacy base row missing `basis_as_of` is reported absent, never derived.
+  - Acceptance: `GET` the new comparison endpoint for a recorded snapshot and it names both snapshots it
+    compared and reports, for every symbol ranked in the compare snapshot in that snapshot's OWN served
+    order, its recorded rank/side/`band_class`/`distance_bps`/`basis_as_of` beside the base snapshot's
+    own recorded values for the same symbol — each byte-identical to what
+    `GET /research/desk/screen?id=<that snapshot's id>` serves for that row — plus the entered/left sets
+    with the other snapshot's own recorded skip reason where it has one (**single source of truth**: the
+    comparison is a NEW value with exactly one owner, the new desk module, and exactly one serving
+    endpoint, registered in the Data Contract BEFORE the code lands; it reads two immutable recorded
+    snapshots through `ScreenStore.list` and copies their values verbatim — zero recompute, zero second
+    read of any store, zero change to what a snapshot records, to its five-pin key, or to the rank key,
+    which keep `desk_screen.ScreenStore` and `GET /research/desk/screen` as their sole owner and sole
+    serving endpoint, and the page derives no rank, distance or difference of its own — this SSOT
+    criterion stands in place of a PnL-ledger append, which this era's Non-Goals forbid); the default
+    base is the record `?date=` already serves for the greatest strictly-earlier screen date, the same
+    two ids reproduce a byte-identical body, the endpoint writes nothing, and every recorded universe,
+    screen, top-up, reconciliation and screen-run file is proven byte-identical on disk before and after
+    the iteration (SHA-256 listing — a read-only iteration records nothing); in a real browser after the
+    T-9 clean rebuild, at a 1440×900 viewport with no horizontal scroll and the ranked briefing table
+    rendering exactly as J-16 shipped it, `/desk` shows the Screen Comparison section in three states
+    across screenshots — the identical state (zero rank changes, zero side changes, zero entered, zero
+    left, both `bar_store_signature`s equal), a churned state with at least one row whose recorded rank
+    moved by ≥ 20 places and one whose side differs between the two recordings, and the honest
+    no-earlier-recorded-screen state on the ledger's oldest snapshot (on the ambient ledger as it stands
+    these are, respectively, `screen-2026-07-31-c169546856c7` vs `screen-2026-07-30-bad6387963ef`,
+    `screen-2026-07-25-bd0b37ebc426` vs `screen-2026-07-20-ca185294a384` — 95 of 100 rows changed rank,
+    12 changed side, PLTR recorded 7 then 84 — and `screen-2026-06-22-3ecd45c062c7`; if the ledger has
+    moved by build time, the same three states over whatever snapshots it then holds, reported honestly)
+    (T-10: no screenshot ⇒ `unknown`, never `passing`; no native `title` tooltip is required by this
+    journey, so the T-10a headed rig is not needed and no capture may depend on one); a
+    **`[NEW]`-flagged demo-narrator walkthrough** covers the screen-comparison disclosure end to end,
+    narrated over a populated ledger and over both the identical and the churned pair; and the full
+    backend suite is green with `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new
+    `Config` fields, the `default` profile and `v1` byte-identical (engine equivalence green), the MCP
+    surface still exactly 17 tools, zero diff to
+    `desk_screen.py`/`desk_coverage.py`/`tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`,
+    and `tests/test_copy_discipline.py` + `tests/test_desk_ui_guards.py` +
+    `tests/test_desk_hover_tooltip_guard.py` green unmodified. *(Keyless core; browser-verifiable. Why:
+    measured 2026-07-31 read-only over the frozen artifacts (no service started, no product code run).
+    **The desk records 12 screens and relates none of them to any other.** No desk module and no line of
+    `apps/frontend/app/desk/page.tsx` compares two snapshots: `GET /research/desk/screen` serves a
+    meta-only `screens` list, a `latest`, and single snapshots by `?date=`/`?id=`, and every rendered
+    view is standalone. Yet the ledger's own pairs sit at both extremes and print identically. Pairing
+    each of the 12 with the record for its greatest strictly-earlier screen date: FOUR pairs changed
+    nothing at all — `screen-2026-07-31-c169546856c7` vs `screen-2026-07-30-bad6387963ef`, that one vs
+    `screen-2026-07-29-2a57de4e7415`, that one vs `screen-2026-07-28-817d92d9c924`, and
+    `screen-2026-07-28-ac07c9581a4f` vs `screen-2026-07-27-3ad3c57aa6ba` — 0 of 100 (0 of 63) rows
+    changed rank, side or `distance_bps`. A field-by-field diff of the four consecutive 100-row screens
+    07-28 → 07-29 → 07-30 → 07-31 shows the ONLY field that differs across all 100 ranked rows is
+    `basis_age_days` (3 → 4 for every row on the last step): all four share basis
+    `2026-07-27T04:00:00.000000Z` and bar-store signature `ae2c740d1a70c9c7`, and each cost a full walk —
+    `screenrun-2026-07-31-725c4ec2bfcd` records 101 members attempted, 01:58:48.238Z → 02:00:29.056Z.
+    SEVEN pairs churned instead: `screen-2026-07-25-bd0b37ebc426` vs `screen-2026-07-20-ca185294a384` —
+    95 of 100 common rows changed rank, 89 changed `distance_bps`, 12 changed side, PLTR 7 → 84, JPM
+    19 → 96, UBER 2 → 77, and only 5 of the top ten symbols stayed in it — and
+    `screen-2026-07-28-817d92d9c924` vs `screen-2026-07-27-3ad3c57aa6ba` — 61 of 63 common rows changed
+    rank, 8 changed side, 37 symbols entered the ranked set (AAPL 19 → 100). On `/desk` today, "the same
+    100 rows for the fourth day running" and "95 of 100 rows moved and 12 flipped side" render as the
+    same screen: one ranked table, with no relation to anything recorded before it.)*
+
 <!-- /AUTO:journeys -->
 
 ## Anti-goals
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-desk/state/assumptions.md        | 37 ++++++++++++++++++++++
 runs/goal-session-desk/state/blueprint.md          |  4 +++
 .../state/enhancement-proposals.jsonl              |  2 ++
 runs/goal-session-desk/state/proposer-result.json  |  8 ++++-
 runs/goal-session-desk/telemetry.jsonl             | 20 ++++++++++++
 runs/goal-session-desk/trace/trace.jsonl           |  3 ++
 6 files changed, 73 insertions(+), 1 deletion(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
