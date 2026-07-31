# Iteration diff (bounded)

Files changed: 6. Shown in full: 6.

```diff
diff --git a/apps/backend/app/research/desk_routes.py b/apps/backend/app/research/desk_routes.py
index 1cfa461..a701976 100644
--- a/apps/backend/app/research/desk_routes.py
+++ b/apps/backend/app/research/desk_routes.py
@@ -70,6 +70,17 @@ triggering ``compute_tradability`` or any other recompute. No new store, no new
 new MCP tool (the existing ``/research/`` allowlist already reaches the new path); no new router, no
 ``main.py`` change.
 
+J-21 (this iteration, goal-desk-iter-36) adds ONE new read: ``GET /research/desk/screen/pins``
+(``screen_date`` REQUIRED query param) — the five pins a screen run for that date would resolve
+RIGHT NOW, and whether a screen is already recorded under them, computed entirely by the new
+``desk_screen_pins.py`` over the SAME accessors ``run_screen_and_record`` already uses. This route
+takes a ``UniverseStore``/``BarIndex``/``ScreenStore`` dependency but NO ``BarStore``/
+``DatasetStore``/compute-manager dependency at all — it is structurally incapable of triggering
+``compute_tradability`` or any other recompute. An honest empty payload at HTTP 200 before any
+universe snapshot is registered (never a 4xx/5xx). No new store, no new compute manager, no new
+``Config`` field, no new MCP tool (the existing ``/research/`` allowlist already reaches the new
+path); no new router, no ``main.py`` change.
+
 **Compute managers are module-level singletons here, NOT ``ResearchRegistry`` properties.**
 ``DeskTopupComputeManager`` (``desk_topup_compute.py``) reuses ``routes.record_bar_series``
 in-process, so it must import FROM ``routes.py`` — if ``ResearchRegistry`` held the manager (the
@@ -102,6 +113,7 @@ from .desk_screen import ScreenStore, resolve_desk_screen_dir
 from .desk_screen_compute import DeskScreenComputeManager
 from .desk_screen_diff import ScreenDiffSelfCompareError, compute_screen_diff
 from .desk_screen_log import ScreenRunStore, resolve_desk_screen_log_dir
+from .desk_screen_pins import resolve_desk_screen_pins
 from .desk_topup_compute import DeskTopupComputeManager
 from .desk_topup_log import TopupRunStore, resolve_desk_topup_log_dir
 from .desk_universe import (
@@ -416,6 +428,25 @@ def get_screen_compare(
         raise HTTPException(status_code=422, detail=str(exc)) from exc
 
 
+@router.get("/screen/pins")
+def get_desk_screen_pins(
+    screen_date: str,
+    universe_store: UniverseStore = Depends(get_universe_store),
+    bar_index: BarIndex = Depends(get_bar_index),
+    screen_store: ScreenStore = Depends(get_screen_store),
+) -> dict:
+    """goal-desk-iter-36 (J-21): the five pins a screen run for ``screen_date`` would resolve RIGHT
+    NOW, and whether a screen is already recorded under them — see ``desk_screen_pins.py``'s module
+    docstring. ``screen_date`` is a REQUIRED query param (FastAPI 422s a missing one — mirrors
+    ``ScreenComputeRequest.screen_date``'s own required convention; this endpoint never defaults to
+    the current wall-clock date, T-6). A plain read: writes nothing, triggers nothing, recomputes
+    nothing — this route takes no ``BarStore``/``DatasetStore``/compute-manager dependency at all,
+    so it is structurally incapable of a ``compute_tradability`` call or a ``BarStore`` read. An
+    honest empty payload at HTTP 200 before any universe snapshot is registered (never a 4xx/5xx —
+    mirrors ``get_universe``/``get_coverage``'s own honest-empty convention)."""
+    return resolve_desk_screen_pins(screen_date, universe_store, bar_index, CONFIG, screen_store)
+
+
 class ScreenComputeRequest(BaseModel):
     """Body for ``POST /research/desk/screen/compute`` — ``screen_date`` is REQUIRED (FastAPI 422s
     a missing/absent body before the route handler runs, TC-9); this endpoint never defaults to
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 296f656..d4e7702 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -12,6 +12,7 @@ import {
   fetchDeskScreenById,
   fetchDeskScreenCompare,
   fetchDeskScreenCompute,
+  fetchDeskScreenPins,
   fetchDeskScreenRuns,
   fetchDeskTopupCompute,
   fetchDeskTopupRuns,
@@ -31,6 +32,7 @@ import type {
   DeskScreenComputeSnapshot,
   DeskScreenListResult,
   DeskScreenMeta,
+  DeskScreenPinsResult,
   DeskScreenRow,
   DeskScreenRun,
   DeskScreenRunMeta,
@@ -160,6 +162,23 @@ import { fmt } from "@/lib/format";
 // `data-testid`, every honest legacy-absence string ("basis not recorded in this snapshot", etc.),
 // and the row's stretched drill-in anchor (`href`, `absolute inset-0`, `data-testid`, composite
 // `title`) stay byte-unchanged -- only the layout and three redundant label words moved.
+//
+// goal-desk-iter-36 (J-21) -- the screen-pin disclosure. Before clicking Run Screen (or before
+// reading a past screen's own provenance), the operator sees whether a run right now would reuse
+// an already-recorded snapshot or walk the universe fresh -- an 8th mount-time GET (`GET
+// /research/desk/screen/pins?screen_date=`), rendered in TWO places, both extensions of already-
+// shipped sections (no new section, no new page): (a) `DeskProvenance` gains the pins resolved for
+// the DISPLAYED snapshot's own `screen_date`, refetched whenever the displayed snapshot changes
+// (mirrors `screenCompareResult`'s own effect, keyed the same way); (b) `ScreenComputeControl`
+// gains one descriptive line querying the SAME endpoint for `todayUtcDate()` -- the identical value
+// the trigger already submits -- so it renders beside the Run Screen button in BOTH the empty-state
+// panel and the populated page (the ONE shared component, never duplicated). In both places, the
+// served `recorded`-or-`null` answer IS the match/differ statement -- this page computes no
+// equality of its own (the J-20 rule; see `assumptions.md` iter-36 entry 1): a non-null `recorded`
+// names the snapshot a run would reuse (its own id + recorded-at), a `null` states that no screen
+// is recorded under the resolved pins and that a run would walk `members_total` members. Zero new
+// ranked-table column, zero change to any existing `data-testid`'s element or text -- purely
+// additive disclosure.
 
 const NUMERIC_CELL = "px-2 py-1.5 text-right font-mono text-xs text-slate-200 whitespace-nowrap";
 const HEADER_CELL = "px-2 py-1 text-right text-[11px] font-medium text-slate-500";
@@ -1699,12 +1718,62 @@ function ScreenComparisonSection({
 // (`created_utc`-sorted newest recording, TC-12), the copy describes itself as "the most recently
 // recorded screen", never "the latest screen date" — a same-date recording can still exist earlier
 // and be reachable from Screen History below.
+// goal-desk-iter-36 (J-21): the resolved-pins block appended to `DeskProvenance` below -- the pins
+// a run for THIS DISPLAYED snapshot's own `screen_date` would resolve right now, fetched via
+// `GET /research/desk/screen/pins`. `recorded === null` here means the DISPLAYED snapshot's own
+// key no longer matches what would resolve today (a "differ" state -- see the top-of-file comment
+// for why the page itself computes no separate match/differ equality).
+function DeskProvenancePins({
+  pins,
+}: {
+  pins: { ok: boolean; data: DeskScreenPinsResult | null; error?: string } | null;
+}) {
+  if (pins === null) {
+    return <p data-testid="desk-provenance-pins-loading" className="mt-2 text-[11px] text-slate-600">
+      Resolving the pins a run would use right now…
+    </p>;
+  }
+  if (!pins.ok || pins.data === null) {
+    return (
+      <p data-testid="desk-provenance-pins-unavailable" className="mt-2 text-[11px] text-amber-300">
+        {pins.error ?? "The pins that would resolve right now could not be loaded."}
+      </p>
+    );
+  }
+  // A screen only ever exists once a universe does (snapshots are never deleted -- Anti-goals'
+  // append-only rail), so `data.universe_snapshot_id` is never null here in practice; no separate
+  // empty-state branch is needed (the "differ" branch below already renders correctly on an all-
+  // null payload, see the module docstring precedent in `desk_screen_pins.py`).
+  const { data } = pins;
+  return (
+    <div data-testid="desk-provenance-pins" className="mt-2 border-t border-slate-800 pt-2">
+      <p className="text-[11px] font-medium text-slate-500">Pins resolved right now for this screen date</p>
+      <Metric label="Universe snapshot (resolved now)" value={data.universe_snapshot_id ?? "—"} />
+      <Metric label="Config fingerprint (resolved now)" value={data.config_fingerprint} />
+      <Metric label="Bar-store signature (resolved now)" value={data.bar_store_signature ?? "—"} />
+      {data.recorded !== null ? (
+        <p data-testid="desk-provenance-pins-match" className="mt-1 text-[11px] text-slate-400">
+          A screen is recorded under these exact pins — {data.recorded.id}, recorded{" "}
+          {data.recorded.created_utc}.
+        </p>
+      ) : (
+        <p data-testid="desk-provenance-pins-differ" className="mt-1 text-[11px] text-slate-400">
+          No screen is recorded under the pins that resolve right now for this date — a run would
+          walk {data.members_total} members.
+        </p>
+      )}
+    </div>
+  );
+}
+
 function DeskProvenance({
   snapshot,
   isViewingLatest,
+  pins,
 }: {
   snapshot: DeskScreenSnapshot;
   isViewingLatest: boolean;
+  pins: { ok: boolean; data: DeskScreenPinsResult | null; error?: string } | null;
 }) {
   return (
     <div data-testid="desk-provenance">
@@ -1727,6 +1796,7 @@ function DeskProvenance({
         timestamp at the moment this screen was computed — a pin, never a time. Each coverage
         badge&apos;s tooltip carries that member&apos;s own window-last-requested value.
       </p>
+      <DeskProvenancePins pins={pins} />
     </div>
   );
 }
@@ -1737,6 +1807,58 @@ function DeskProvenance({
 // components (rather than one shared abstraction) since their progress shapes genuinely differ
 // (members vs pairs+outcomes) — this project's own simplicity convention. --------------------------
 
+// goal-desk-iter-36 (J-21): the descriptive line beside the Run Screen control, querying
+// `GET /research/desk/screen/pins` for `todayUtcDate()` -- the SAME value `handleTriggerScreen`
+// already submits to the trigger (below). Renders in BOTH places `ScreenComputeControl` itself
+// renders (the empty-state panel and the populated page's own control panel), since it lives
+// inside that ONE shared component -- no duplication. Honest empty state (T-11): before any
+// universe snapshot is registered, `data.universe_snapshot_id` is `null` and this renders that
+// fact plainly rather than a "0 members" claim that would misleadingly imply a real, resolvable
+// walk.
+function TodayScreenPinsNote({
+  pins,
+}: {
+  pins: { ok: boolean; data: DeskScreenPinsResult | null; error?: string } | null;
+}) {
+  if (pins === null) {
+    return (
+      <p data-testid="desk-run-screen-pins-loading" className="text-[11px] text-slate-600">
+        Resolving whether today&apos;s pins would reuse a recorded screen…
+      </p>
+    );
+  }
+  if (!pins.ok || pins.data === null) {
+    return (
+      <p data-testid="desk-run-screen-pins-unavailable" className="text-[11px] text-amber-300">
+        {pins.error ?? "Whether today's pins would reuse a recorded screen could not be loaded."}
+      </p>
+    );
+  }
+  const { data } = pins;
+  if (data.universe_snapshot_id === null) {
+    return (
+      <p data-testid="desk-run-screen-pins-empty" className="text-[11px] text-slate-600">
+        No universe snapshot is registered — whether a run today would reuse a recorded screen
+        cannot be named.
+      </p>
+    );
+  }
+  if (data.recorded !== null) {
+    return (
+      <p data-testid="desk-run-screen-pins-match" className="text-[11px] text-slate-500">
+        A run today would reuse the snapshot already recorded under today&apos;s pins —{" "}
+        {data.recorded.id}, recorded {data.recorded.created_utc}.
+      </p>
+    );
+  }
+  return (
+    <p data-testid="desk-run-screen-pins-differ" className="text-[11px] text-slate-500">
+      No screen is recorded under the pins that resolve for today — a run would walk{" "}
+      {data.members_total} members.
+    </p>
+  );
+}
+
 function ScreenComputeControl({
   compute,
   onTrigger,
@@ -1745,6 +1867,7 @@ function ScreenComputeControl({
   onCancel,
   cancelRequested,
   cancelError,
+  pins,
 }: {
   compute: DeskScreenComputeSnapshot | null;
   onTrigger: () => void;
@@ -1753,6 +1876,7 @@ function ScreenComputeControl({
   onCancel: () => void;
   cancelRequested: boolean;
   cancelError: string | null;
+  pins: { ok: boolean; data: DeskScreenPinsResult | null; error?: string } | null;
 }) {
   const isRunning = compute?.state === "running";
   const isFailed = compute?.state === "failed";
@@ -1786,6 +1910,7 @@ function ScreenComputeControl({
             : `Recorded a new snapshot — ${compute.screen_id}`}
         </p>
       )}
+      <TodayScreenPinsNote pins={pins} />
       <button
         type="button"
         data-testid="desk-run-screen-button"
@@ -2002,6 +2127,7 @@ interface ScreenControlProps {
   onCancel: () => void;
   cancelRequested: boolean;
   cancelError: string | null;
+  pins: { ok: boolean; data: DeskScreenPinsResult | null; error?: string } | null;
 }
 
 interface TopupControlProps {
@@ -2071,6 +2197,7 @@ function DeskPopulatedScreen({
   screenControlProps,
   topupControlProps,
   reconcileControlProps,
+  displayedPins,
 }: {
   snapshot: DeskScreenSnapshot;
   screens: DeskScreenMeta[];
@@ -2083,6 +2210,7 @@ function DeskPopulatedScreen({
   screenControlProps: ScreenControlProps;
   topupControlProps: TopupControlProps;
   reconcileControlProps: ReconcileControlProps;
+  displayedPins: { ok: boolean; data: DeskScreenPinsResult | null; error?: string } | null;
 }) {
   return (
     <div className="space-y-6">
@@ -2110,7 +2238,7 @@ function DeskPopulatedScreen({
 
       <section aria-label="Provenance">
         <Panel title="Provenance">
-          <DeskProvenance snapshot={snapshot} isViewingLatest={isViewingLatest} />
+          <DeskProvenance snapshot={snapshot} isViewingLatest={isViewingLatest} pins={displayedPins} />
         </Panel>
       </section>
 
@@ -2235,12 +2363,31 @@ export default function DeskPage() {
     error?: string;
   } | null>(null);
 
-  // Mount: seven GETs, zero POSTs (TC-19/TC-8, extended era-desk-iter-14/goal-desk-iter-29) — the
-  // screen list/latest, ALL THREE compute managers' current/last snapshot (seeds a page load
-  // mid-job or post-terminal without a spurious extra click — the /structure edge-report
-  // mount-seeding precedent), the top-up run log's list + latest full record (era-desk-iter-11,
-  // J-09), the reconciliation run log's list + latest full record (era-desk-iter-14, J-10), and
-  // (goal-desk-iter-29, J-18) the screen run log's list + latest full record.
+  // goal-desk-iter-36 (J-21): the screen-pin disclosure's two independent fetches. `todayPinsResult`
+  // answers "would a run RIGHT NOW reuse or walk?" for `todayUtcDate()` — the SAME value the Run
+  // Screen trigger already submits — and is rendered beside that control (both empty-state and
+  // populated views, since it lives inside the ONE shared `ScreenComputeControl`). `displayedPins`
+  // answers the SAME question for the currently DISPLAYED snapshot's own `screen_date` and is
+  // rendered inside `DeskProvenance`; it is refetched by its own effect below whenever the
+  // displayed snapshot changes (mirrors `screenCompareResult`'s own effect).
+  const [todayPinsResult, setTodayPinsResult] = useState<{
+    ok: boolean;
+    data: DeskScreenPinsResult | null;
+    error?: string;
+  } | null>(null);
+  const [displayedPinsResult, setDisplayedPinsResult] = useState<{
+    ok: boolean;
+    data: DeskScreenPinsResult | null;
+    error?: string;
+  } | null>(null);
+
+  // Mount: eight GETs, zero POSTs (TC-19/TC-8, extended era-desk-iter-14/goal-desk-iter-29/
+  // goal-desk-iter-36) — the screen list/latest, ALL THREE compute managers' current/last snapshot
+  // (seeds a page load mid-job or post-terminal without a spurious extra click — the /structure
+  // edge-report mount-seeding precedent), the top-up run log's list + latest full record
+  // (era-desk-iter-11, J-09), the reconciliation run log's list + latest full record
+  // (era-desk-iter-14, J-10), the screen run log's list + latest full record (goal-desk-iter-29,
+  // J-18), and (goal-desk-iter-36, J-21) today's own screen-pin resolution.
   useEffect(() => {
     let alive = true;
     fetchDeskScreen().then((result) => {
@@ -2264,6 +2411,9 @@ export default function DeskPage() {
     fetchDeskReconcileRuns().then((result) => {
       if (alive) setReconcileRunsResult(result);
     });
+    fetchDeskScreenPins(todayUtcDate()).then((result) => {
+      if (alive) setTodayPinsResult(result);
+    });
     return () => {
       alive = false;
     };
@@ -2296,6 +2446,14 @@ export default function DeskPage() {
         setScreenRunsResult((previous) =>
           refreshedRuns.ok || previous === null || !previous.ok ? refreshedRuns : previous,
         );
+        // goal-desk-iter-36 (J-21): a just-finished run changes whether TODAY's pins would now
+        // reuse or walk — the SAME "on terminal, refresh once" precedent the two refetches above
+        // already establish (NOTES: "at most a refetch where the page already refetches its
+        // ledgers on a terminal compute tick" — never a timer/poll of its own).
+        const refreshedTodayPins = await fetchDeskScreenPins(todayUtcDate());
+        setTodayPinsResult((previous) =>
+          refreshedTodayPins.ok || previous === null || !previous.ok ? refreshedTodayPins : previous,
+        );
       }
     }, 700);
     return () => clearInterval(handle);
@@ -2450,6 +2608,7 @@ export default function DeskPage() {
     onCancel: handleCancelScreen,
     cancelRequested: screenCancelRequested,
     cancelError: screenCancelError,
+    pins: todayPinsResult,
   };
   const topupControlProps: TopupControlProps = {
     compute: topupCompute,
@@ -2511,6 +2670,25 @@ export default function DeskPage() {
     };
   }, [displayedSnapshot]);
 
+  // goal-desk-iter-36 (J-21): fetch the screen-pin resolution for the DISPLAYED snapshot's own
+  // `screen_date` — the SAME `displayedSnapshot` dependency the Screen Comparison effect above
+  // uses, since `DeskProvenance` (which renders this) describes that same snapshot. A page-load/
+  // selection-change GET only, never a timer or a click.
+  useEffect(() => {
+    const screenDate = displayedSnapshot?.screen_date ?? null;
+    if (screenDate === null) {
+      setDisplayedPinsResult(null);
+      return;
+    }
+    let alive = true;
+    fetchDeskScreenPins(screenDate).then((result) => {
+      if (alive) setDisplayedPinsResult(result);
+    });
+    return () => {
+      alive = false;
+    };
+  }, [displayedSnapshot]);
+
   return (
     <div className="min-h-screen">
       <main className="mx-auto max-w-7xl px-4 py-6">
@@ -2554,6 +2732,7 @@ export default function DeskPage() {
             screenControlProps={screenControlProps}
             topupControlProps={topupControlProps}
             reconcileControlProps={reconcileControlProps}
+            displayedPins={displayedPinsResult}
           />
         )}
 
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index f170c8a..f1f413c 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -11,6 +11,7 @@ import type {
   DeskScreenCompareResult,
   DeskScreenComputeSnapshot,
   DeskScreenListResult,
+  DeskScreenPinsResult,
   DeskScreenRunsListResult,
   DeskScreenSnapshot,
   DeskTopupComputeSnapshot,
@@ -1298,6 +1299,38 @@ export async function fetchDeskScreenRuns(): Promise<{
   }
 }
 
+// goal-desk-iter-36 (J-21): GET /research/desk/screen/pins?screen_date= — the five pins a screen
+// run for that date would resolve RIGHT NOW, and whether a screen is already recorded under them,
+// served VERBATIM. Mirrors `fetchDeskScreenRuns`'s exact `{ok, data, error}` shape; the backend
+// always answers HTTP 200 (an honest empty payload before any universe snapshot is registered) —
+// `screen_date` is the ONLY required param, and this helper never defaults it itself (the caller
+// always passes its own already-resolved date, e.g. `todayUtcDate()` or a displayed snapshot's own
+// `screen_date`).
+export async function fetchDeskScreenPins(screenDate: string): Promise<{
+  ok: boolean;
+  data: DeskScreenPinsResult | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(
+      `${API_BASE}/research/desk/screen/pins?screen_date=${encodeURIComponent(screenDate)}`,
+    );
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskScreenPinsResult };
+    }
+    let error = "The screen-pin resolution could not be loaded.";
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
+
 // goal-desk-iter-35 (J-20): GET /research/desk/screen/compare?id= — how the named snapshot differs
 // from the screen recorded immediately before it, served VERBATIM (the default base; no `base=`
 // override ships a control this iteration — the section always describes whichever screen `/desk`
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index af9e498..e6b1ef9 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -1198,3 +1198,30 @@ export interface DeskScreenCompareResult {
   identical: boolean;
   counts: DeskScreenCompareCounts;
 }
+
+// goal-desk-iter-36 (J-21) -- `GET /research/desk/screen/pins?screen_date=`: the five pins a
+// screen run for that date would resolve RIGHT NOW, and whether a screen is already recorded
+// under them. `recorded` names the already-registered snapshot verbatim (its own `id`/
+// `created_utc`/`bar_store_signature`/ranked+skipped counts) or is an honest `null` -- the
+// presence/absence of `recorded` IS the match/differ statement (computed at the owner, served;
+// the page derives no equality of its own, the J-20 rule). An honest empty payload
+// (`universe_snapshot_id`/`bar_store_signature`: `null`, `members_total: 0`, `recorded: null`)
+// before any universe snapshot is registered -- HTTP 200, never a 404.
+export interface DeskScreenPinsRecorded {
+  id: string;
+  screen_date: string;
+  created_utc: string;
+  bar_store_signature: string;
+  ranked_count: number;
+  skipped_count: number;
+}
+
+export interface DeskScreenPinsResult {
+  screen_date: string;
+  as_of: string;
+  universe_snapshot_id: string | null;
+  config_fingerprint: string;
+  bar_store_signature: string | null;
+  members_total: number;
+  recorded: DeskScreenPinsRecorded | null;
+}
diff --git a/apps/backend/app/research/desk_screen_pins.py b/apps/backend/app/research/desk_screen_pins.py
new file mode 100644
index 0000000..ee86583
--- /dev/null
+++ b/apps/backend/app/research/desk_screen_pins.py
@@ -0,0 +1,121 @@
+"""Screen-pin resolution (Era B "The Desk", goal-desk-iter-36, J-21) -- answers, for a
+caller-supplied ``screen_date``, whether a screen run right now would reuse an already-recorded
+snapshot or walk the universe fresh. The Data Contract's "Screen-pin resolution" row's ONE owner,
+served by ``GET /research/desk/screen/pins``.
+
+THIS MODULE computes NOTHING new -- every pin is resolved through the SAME accessor that already
+owns it, in the SAME order ``run_screen_and_record`` resolves them
+(``desk_screen_compute.py:155``-``:161``): ``desk_screen.screen_as_of`` (``as_of``),
+``UniverseStore.list()``'s own latest record id and member count (``universe_snapshot_id``,
+``members_total`` -- read the way ``DeskScreenComputeManager.trigger`` already reads it,
+``len(records[-1]["members"])``), ``Config.config_fingerprint()`` (``config_fingerprint``), and
+``desk_screen.compute_bar_store_signature`` over ``desk_coverage.get_desk_coverage``'s index-only
+read (``bar_store_signature``) -- zero new derivation, zero second owner, no ``BarStore`` read of
+any kind (T-4). The recorded-or-not answer comes from ``ScreenStore.find_by_key`` on exactly those
+five pins -- the SAME lookup J-18's pre-check already makes (``desk_screen_compute.py:209``). This
+resolution and a run's own therefore cannot disagree: same functions, same order, same immutable
+stores.
+
+**Honest empty (TC-5).** Before any universe snapshot is ever registered, there is nothing to
+resolve a bar-store signature OVER -- ``desk_coverage.get_desk_coverage`` itself would report
+``members: []``, and hashing a signature over zero pairs would misleadingly look like a real,
+resolvable pin. This module reports the honest ``universe_snapshot_id: None``,
+``bar_store_signature: None``, ``members_total: 0``, ``recorded: None`` instead of computing a
+signature over nothing -- HTTP 200, never a 4xx/5xx (mirrors ``get_universe``/``get_coverage``'s
+own honest-empty convention). ``run_screen_and_record`` never reaches this state itself (its own
+caller, ``trigger_desk_screen_compute``, refuses with a 422 before a universe-less pin resolution
+is ever attempted) -- this is the first caller that must answer it honestly rather than refuse,
+since disclosure (unlike a run) has nothing destructive to refuse.
+
+**Disclose, never judge (T-copy discipline).** The response states what the pins ARE and whether a
+recording exists under them, and stops there -- no threshold, staleness, or confidence number; no
+fresh/stale/current/behind/up-to-date judgement; no advice or prediction. A differing signature
+proves exactly one thing: no recorded screen carries these pins, i.e. a run for this date would
+walk rather than reuse.
+
+**Persists nothing.** No store, no file, no cache, no index, no new ``Config`` field -- a pure
+read over three already-constructed dependencies (``UniverseStore``, ``BarIndex``, ``ScreenStore``)
+plus the process-wide ``Config``. Writes nothing, triggers nothing, recomputes nothing: zero
+``compute_tradability`` calls, zero band selections, zero rank-key evaluations, zero bar reads
+(structurally -- this module never imports ``compute_tradability`` and never receives a
+``BarStore`` reference of any kind, mirroring ``desk_screen._bar_store_signature``'s own "cannot
+call what it never received" argument)."""
+
+from __future__ import annotations
+
+from ..config import Config
+from .bar_index import BarIndex
+from .desk_screen import ScreenStore, compute_bar_store_signature, screen_as_of
+from .desk_universe import UniverseStore
+
+
+def resolve_desk_screen_pins(
+    screen_date: str,
+    universe_store: UniverseStore,
+    bar_index: BarIndex,
+    config: Config,
+    screen_store: ScreenStore,
+) -> dict:
+    """The five pins a screen run for ``screen_date`` would resolve RIGHT NOW, plus whether a
+    screen is already recorded under them -- see the module docstring. ``screen_date`` is the
+    caller's own value (the page passes the SAME ``todayUtcDate()`` it already submits to the
+    trigger, ``apps/frontend/app/desk/page.tsx:228``/``:2350``) -- nothing here calls ``now()``
+    (T-6): identical inputs (this date, the pinned universe record, the index's rows as they stand)
+    reproduce a byte-identical body, and the payload carries no wall-clock field of its own.
+
+    Shape::
+
+        {
+          "screen_date": str, "as_of": str, "universe_snapshot_id": str | None,
+          "config_fingerprint": str, "bar_store_signature": str | None,
+          "members_total": int,
+          "recorded": {
+            "id": str, "screen_date": str, "created_utc": str, "bar_store_signature": str,
+            "ranked_count": int, "skipped_count": int,
+          } | None,
+        }
+    """
+    as_of = screen_as_of(screen_date)
+    config_fingerprint = config.config_fingerprint()
+    universe_records, _universe_errors = universe_store.list()
+
+    if not universe_records:
+        # Honest empty (TC-5): nothing is registered to resolve a coverage signature over.
+        return {
+            "screen_date": screen_date,
+            "as_of": as_of,
+            "universe_snapshot_id": None,
+            "config_fingerprint": config_fingerprint,
+            "bar_store_signature": None,
+            "members_total": 0,
+            "recorded": None,
+        }
+
+    latest_universe = universe_records[-1]
+    universe_snapshot_id = latest_universe["id"]
+    members_total = len(latest_universe["members"])
+    bar_store_signature = compute_bar_store_signature(universe_store, bar_index)
+
+    existing = screen_store.find_by_key(
+        screen_date, as_of, universe_snapshot_id, config_fingerprint, bar_store_signature
+    )
+    recorded = None
+    if existing is not None:
+        recorded = {
+            "id": existing["id"],
+            "screen_date": existing["screen_date"],
+            "created_utc": existing["created_utc"],
+            "bar_store_signature": existing["bar_store_signature"],
+            "ranked_count": len(existing["rows"]),
+            "skipped_count": len(existing["skipped"]),
+        }
+
+    return {
+        "screen_date": screen_date,
+        "as_of": as_of,
+        "universe_snapshot_id": universe_snapshot_id,
+        "config_fingerprint": config_fingerprint,
+        "bar_store_signature": bar_store_signature,
+        "members_total": members_total,
+        "recorded": recorded,
+    }
diff --git a/apps/backend/tests/test_desk_screen_pins.py b/apps/backend/tests/test_desk_screen_pins.py
new file mode 100644
index 0000000..d112594
--- /dev/null
+++ b/apps/backend/tests/test_desk_screen_pins.py
@@ -0,0 +1,338 @@
+"""``desk_screen_pins.py`` (Era B "The Desk", goal-desk-iter-36, J-21) -- the pin-resolution read
+that answers, for a caller-supplied ``screen_date``, whether a screen run right now would reuse an
+already-recorded snapshot or walk the universe fresh. Backend tests over planted, scoped stores
+(goal.md step 6, never ``apps/backend/.data``) -- mirrors ``test_desk_screen_diff.py``'s /
+``test_desk_screen_compute.py``'s own fixture conventions.
+
+TC references below are this file's own copy of the phase spec's test-first contract
+(``docs/phases/goal-desk-iter-36.md``): TC-1/TC-2 (already-recorded pins name the exact snapshot a
+trigger reuses), TC-3/TC-4 (a planted bar-index row shifts the signature and a trigger then walks
+fresh, leaving the earlier file untouched), TC-5 (honest empty before any universe), TC-6 (zero
+``compute_tradability``/``BarStore`` calls -- structural, not just behavioral), TC-7 (byte-identical
+repeat), TC-8 (422 on a missing ``screen_date``).
+"""
+
+from __future__ import annotations
+
+import json
+import shutil
+from pathlib import Path
+
+import pytest
+from fastapi.testclient import TestClient
+
+from app.config import CONFIG
+from app.main import app, get_market_adapter, manager as ws_manager
+from app.providers.adapters.base import RawBar
+from app.research import tradability as tradability_module
+from app.research.bar_index import BarIndex
+from app.research.bars import BarStore
+from app.research.datasets import DatasetStore
+from app.research.desk_screen import ScreenStore
+from app.research.desk_screen_compute import run_screen_and_record
+from app.research.desk_screen_pins import resolve_desk_screen_pins
+from app.research.desk_universe import UniverseStore
+from app.research.routes import ResearchRegistry, set_registry
+from app.research.store import JournalStore
+
+FIXTURE_UNIVERSE_DIR = Path(__file__).parent / "fixtures" / "universe"
+REGISTERED_SNAPSHOT_PATH = FIXTURE_UNIVERSE_DIR / "universe-2026-07-25-817cc184bbb3.json"
+FIXTURE_YAHOO_DIR = Path(__file__).parent / "fixtures" / "yahoo"
+AAPL_DAILY_FIXTURE = "AAPL_1d_20260101_20260626.json"
+
+SCREEN_DATE = "2026-06-22"
+
+
+def _load_yahoo_fixture(name: str) -> dict:
+    return json.loads((FIXTURE_YAHOO_DIR / name).read_text())
+
+
+def _seed_yahoo_fixture(bar_store: BarStore, bar_index: BarIndex, fixture: dict) -> None:
+    bars = [
+        RawBar(
+            fixture["symbol"], fixture["timeframe"], b["epoch"],
+            b["open"], b["high"], b["low"], b["close"], b["volume"],
+        )
+        for b in fixture["bars"]
+    ]
+    meta = bar_store.record(
+        symbol=fixture["symbol"], timeframe=fixture["timeframe"],
+        window_start_utc=fixture["start"], window_end_utc=fixture["end"],
+        feed="yahoo", bars=bars,
+    )
+    bar_index.insert(meta)
+
+
+def _register_fixture_universe(universe_dir: Path) -> UniverseStore:
+    universe_dir.mkdir(parents=True, exist_ok=True)
+    shutil.copy(REGISTERED_SNAPSHOT_PATH, universe_dir / REGISTERED_SNAPSHOT_PATH.name)
+    return UniverseStore(universe_dir)
+
+
+def _plant_extra_index_row(bar_index: BarIndex) -> None:
+    """Plants ONE new ``bar_index`` row for a member/timeframe pair the fixture universe never
+    seeded (AAPL/``1h``) -- changes that member's OWN frozen coverage (T-4: ``bar_index`` only,
+    never touching ``BarStore``/the recorded screen files at all) so
+    ``compute_bar_store_signature`` resolves a DIFFERENT signature than before (TC-3)."""
+    bar_index.insert(
+        {
+            "symbol": "AAPL", "timeframe": "1h",
+            "window_start_utc": "2026-06-20T00:00:00Z", "window_end_utc": "2026-06-21T00:00:00Z",
+            "feed": "yahoo", "id": "planted-synthetic-series", "checksum": "0" * 64,
+            "bar_count": 1,
+        }
+    )
+
+
+@pytest.fixture
+def real_ctx(tmp_path):
+    """Mirrors ``test_desk_screen_compute.py``'s own ``real_ctx`` fixture exactly -- the REAL
+    fixture universe (103 members) plus real AAPL daily bars, so pin resolution and an actual
+    ``run_screen_and_record`` walk share the identical stores."""
+    universe_store = _register_fixture_universe(tmp_path / "universe")
+    bar_store = BarStore(tmp_path / "bars")
+    bar_index = BarIndex(str(tmp_path / "index.db"))
+    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    screen_store = ScreenStore(tmp_path / "screen")
+    return universe_store, bar_store, bar_index, dataset_store, screen_store
+
+
+# ==================================================================================================
+# TC-5: honest empty before any universe snapshot exists.
+# ==================================================================================================
+
+
+def test_tc5_no_universe_snapshot_is_an_honest_empty_payload(tmp_path):
+    universe_store = UniverseStore(tmp_path / "universe")
+    bar_index = BarIndex(str(tmp_path / "index.db"))
+    screen_store = ScreenStore(tmp_path / "screen")
+
+    result = resolve_desk_screen_pins(SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store)
+
+    assert result == {
+        "screen_date": SCREEN_DATE,
+        "as_of": f"{SCREEN_DATE}T23:59:59Z",
+        "universe_snapshot_id": None,
+        "config_fingerprint": CONFIG.config_fingerprint(),
+        "bar_store_signature": None,
+        "members_total": 0,
+        "recorded": None,
+    }
+
+
+# ==================================================================================================
+# TC-1/TC-2: an already-recorded pin set names the exact snapshot ``run_screen_and_record`` reuses.
+# ==================================================================================================
+
+
+def test_tc1_tc2_resolved_pins_name_the_exact_snapshot_a_trigger_reuses(real_ctx):
+    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
+
+    # Before any screen has ever been computed, the pins are already resolvable (universe + index
+    # both exist) but nothing is recorded under them yet.
+    before = resolve_desk_screen_pins(SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store)
+    assert before["recorded"] is None
+    assert before["universe_snapshot_id"] == "universe-2026-07-25-817cc184bbb3"
+    assert before["members_total"] == 103
+    assert before["bar_store_signature"] is not None
+
+    first, first_reused = run_screen_and_record(
+        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
+    )
+    assert first_reused is False
+
+    after = resolve_desk_screen_pins(SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store)
+
+    # TC-1: every resolved pin is byte-identical to ``run_screen_and_record``'s OWN resolution --
+    # the two can never disagree (same accessors, same order, same stores).
+    assert after["screen_date"] == first["screen_date"]
+    assert after["as_of"] == first["as_of"]
+    assert after["universe_snapshot_id"] == first["universe_snapshot_id"]
+    assert after["config_fingerprint"] == first["config_fingerprint"]
+    assert after["bar_store_signature"] == first["bar_store_signature"]
+    assert after["members_total"] == 103
+
+    assert after["recorded"] is not None
+    assert after["recorded"]["id"] == first["id"]
+    assert after["recorded"]["screen_date"] == first["screen_date"]
+    assert after["recorded"]["created_utc"] == first["created_utc"]
+    assert after["recorded"]["bar_store_signature"] == first["bar_store_signature"]
+    assert after["recorded"]["ranked_count"] == len(first["rows"])
+    assert after["recorded"]["skipped_count"] == len(first["skipped"])
+
+    # TC-2: a trigger for the same date reuses exactly the snapshot the pins already named --
+    # J-18's shipped reuse behaviour, unchanged.
+    second, second_reused = run_screen_and_record(
+        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
+    )
+    assert second_reused is True
+    assert second["id"] == first["id"] == after["recorded"]["id"]
+
+
+# ==================================================================================================
+# TC-3/TC-4: one planted bar-index row shifts the signature; a trigger then walks fresh, leaving
+# the earlier snapshot file byte-identical on disk.
+# ==================================================================================================
+
+
+def test_tc3_tc4_a_planted_index_row_differs_the_signature_and_a_trigger_records_a_new_snapshot(
+    real_ctx,
+):
+    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
+
+    first, first_reused = run_screen_and_record(
+        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
+    )
+    assert first_reused is False
+    first_path = screen_store.root / f"{first['id']}.json"
+    first_bytes_before = first_path.read_bytes()
+
+    before_plant = resolve_desk_screen_pins(
+        SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store
+    )
+    assert before_plant["recorded"]["id"] == first["id"]
+
+    _plant_extra_index_row(bar_index)
+
+    # TC-3: the same GET for the same date now resolves a DIFFERENT signature and an honest
+    # ``recorded: null`` -- the earlier snapshot's own key no longer matches what's live.
+    after_plant = resolve_desk_screen_pins(
+        SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store
+    )
+    assert after_plant["bar_store_signature"] != before_plant["bar_store_signature"]
+    assert after_plant["universe_snapshot_id"] == before_plant["universe_snapshot_id"]
+    assert after_plant["recorded"] is None
+
+    # TC-4: a trigger for the same date now walks every member fresh and records a NEW snapshot --
+    # the earlier file stays byte-identical on disk, never rewritten.
+    second, second_reused = run_screen_and_record(
+        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
+    )
+    assert second_reused is False
+    assert second["id"] != first["id"]
+    assert second["bar_store_signature"] == after_plant["bar_store_signature"]
+    assert first_path.read_bytes() == first_bytes_before
+
+    records, errors = screen_store.list()
+    assert errors == []
+    assert {r["id"] for r in records} == {first["id"], second["id"]}
+
+
+# ==================================================================================================
+# TC-6: zero ``compute_tradability`` calls and zero ``BarStore`` reads -- structural, not just
+# behavioral (every ``BarStore`` method is poisoned to raise; the call still succeeds).
+# ==================================================================================================
+
+
+def test_tc6_zero_compute_tradability_calls_and_zero_bar_store_reads(real_ctx, monkeypatch):
+    universe_store, _bar_store, bar_index, _dataset_store, screen_store = real_ctx
+
+    def _boom(*_args, **_kwargs):
+        raise AssertionError("resolve_desk_screen_pins must never call this")
+
+    monkeypatch.setattr(tradability_module, "compute_tradability", _boom)
+    for name in ("get", "list", "candles", "merged_candles", "merged_bars", "load_bars", "record"):
+        monkeypatch.setattr(BarStore, name, _boom)
+
+    result = resolve_desk_screen_pins(SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store)
+
+    # Resolves fine despite EVERY BarStore method and compute_tradability itself being poisoned --
+    # proof this module never reaches either.
+    assert result["universe_snapshot_id"] is not None
+    assert result["bar_store_signature"] is not None
+
+
+# ==================================================================================================
+# TC-7: the same ``screen_date`` requested twice in succession is byte-identical (no wall-clock
+# field, T-6).
+# ==================================================================================================
+
+
+def test_tc7_the_same_request_twice_in_succession_is_byte_identical(real_ctx):
+    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
+    run_screen_and_record(
+        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
+    )
+
+    first = resolve_desk_screen_pins(SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store)
+    second = resolve_desk_screen_pins(SCREEN_DATE, universe_store, bar_index, CONFIG, screen_store)
+
+    assert first == second
+    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
+
+
+# ==================================================================================================
+# Route-level: TC-8 (422 on a missing ``screen_date``), honest empty at HTTP 200, basic wiring.
+# ==================================================================================================
+
+
+@pytest.fixture
+def route_ctx(tmp_path, monkeypatch):
+    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
+    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
+    monkeypatch.setenv("TAPEOLOGY_DESK_SCREEN_DIR", str(tmp_path / "screen"))
+    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
+    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
+    registry = ResearchRegistry(store, CONFIG)
+    set_registry(registry)
+    with TestClient(app) as client:
+        yield client, tmp_path
+    for ticker in list(ws_manager._engines.keys()):
+        ws_manager.stop(ticker)
+    set_registry(None)
+    app.dependency_overrides.pop(get_market_adapter, None)
+    store.close()
+
+
+def test_route_missing_screen_date_is_422(route_ctx):
+    """TC-8: the endpoint never defaults to the current wall-clock date."""
+    client, _tmp_path = route_ctx
+    r = client.get("/research/desk/screen/pins")
+    assert r.status_code == 422
+
+
+def test_route_no_universe_snapshot_is_an_honest_empty_200(route_ctx):
+    """TC-5 via HTTP."""
+    client, _tmp_path = route_ctx
+    r = client.get("/research/desk/screen/pins", params={"screen_date": SCREEN_DATE})
+    assert r.status_code == 200
+    assert r.json() == {
+        "screen_date": SCREEN_DATE,
+        "as_of": f"{SCREEN_DATE}T23:59:59Z",
+        "universe_snapshot_id": None,
+        "config_fingerprint": CONFIG.config_fingerprint(),
+        "bar_store_signature": None,
+        "members_total": 0,
+        "recorded": None,
+    }
+
+
+def test_route_names_the_recorded_snapshot_after_a_real_trigger(route_ctx):
+    client, tmp_path = route_ctx
+    UniverseStore(tmp_path / "universe").record(
+        members=["AAA"], raw_members={"AAA": "AAA"},
+        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
+    )
+
+    r = client.post("/research/desk/screen/compute", json={"screen_date": SCREEN_DATE})
+    assert r.status_code == 200
+    assert r.json()["started"] is True
+
+    import time
+
+    deadline = time.time() + 5
+    snap = None
+    while time.time() < deadline:
+        snap = client.get("/research/desk/screen/compute").json()
+        if snap is not None and snap["state"] != "running":
+            break
+        time.sleep(0.02)
+    assert snap["state"] == "done"
+
+    r = client.get("/research/desk/screen/pins", params={"screen_date": SCREEN_DATE})
+    assert r.status_code == 200
+    body = r.json()
+    assert body["recorded"] is not None
+    assert body["recorded"]["id"] == snap["screen_id"]
+    assert body["members_total"] == 1
```
