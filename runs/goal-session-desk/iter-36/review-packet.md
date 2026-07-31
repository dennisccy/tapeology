# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

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
diff --git a/docs/goal.md b/docs/goal.md
index 150bab4..aa29caf 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -1814,6 +1814,145 @@ order: J-01 → J-02 → J-03 → J-04 → J-05 → J-06, with J-07 guarding con
     100 rows for the fourth day running" and "95 of 100 rows moved and 12 flipped side" render as the
     same screen: one ranked table, with no relation to anything recorded before it.)*
 
+- **J-21: The desk says, before the click, whether a screen is already recorded under the pins a run would resolve now**
+  - Steps:
+    1. Resolve the five pins for a CALLER-SUPPLIED screen date using ONLY the accessors that already own
+       each one, in the SAME order `run_screen_and_record` resolves them (`desk_screen_compute.py:155`–
+       `:161`): `desk_screen.screen_as_of` (`desk_screen.py:233`), the universe store's own latest record
+       id (`UniverseStore.list()`'s `records[-1]["id"]`), `Config.config_fingerprint()`, and
+       `desk_screen.compute_bar_store_signature` (`desk_screen.py:255`) over
+       `desk_coverage.get_desk_coverage`'s index-only read (`desk_coverage.py:40` → `BarIndex.coverage`,
+       `bar_index.py:154`) — **no `BarStore` read of any kind** (T-4), no new derivation, no new pin, no
+       second owner: the same functions over the same immutable store, so this resolution and a run's own
+       cannot disagree (the J-18 rule verbatim). The date comes from the caller — the page passes the SAME
+       `todayUtcDate()` value it already submits to the trigger (`apps/frontend/app/desk/page.tsx:228`/
+       `:2350`) — so nothing on the new path calls `now()`; the body is a pure function of (requested
+       date, the pinned universe record, the index's rows as they stand), identical inputs reproduce a
+       byte-identical body, and the payload carries no wall-clock field of its own (T-6).
+    2. Answer the one question those pins decide, through the owner that already answers it:
+       `ScreenStore.find_by_key` on exactly those five pins (`desk_screen.py:602` — the SAME lookup
+       J-18's pre-check makes at `desk_screen_compute.py:209`) either NAMES the snapshot already recorded
+       under them — its own `id`, `screen_date`, `created_utc`, `bar_store_signature` and ranked/skipped
+       counts copied VERBATIM out of that record's own meta — or is an honest `null`. Beside it,
+       `members_total`: the pinned universe record's own member count, read the way
+       `DeskScreenComputeManager.trigger` already reads it (`len(records[-1]["members"])`,
+       `desk_screen_compute.py:336`), so "a run would walk N members" is a recorded count and never an
+       estimate. Nothing is recomputed and nothing is ranked: zero `compute_tradability` calls, zero band
+       selections, zero rank-key evaluations, zero bar reads.
+    3. Own it exactly once: a new desk module (name at build discretion, e.g.
+       `app/research/desk_screen_pins.py`) as the ONLY owner and ONE serving endpoint (exact path at
+       build discretion, e.g. `GET /research/desk/screen/pins`) — registered as a NEW row in the
+       blueprint's Data Contract BEFORE the code lands. It PERSISTS NOTHING: no store, no file, no cache,
+       no index, no new `Config` field, no new MCP tool (J-06's exactly-17-tool contract stays green and
+       `get_endpoint`'s `/research/` allowlist already reaches the new path). The GET writes nothing,
+       computes nothing and triggers nothing (the 5C lesson): screen rows, skip rows, the five-pin
+       snapshot key and the rank key keep `desk_screen.ScreenStore` as their sole owner and
+       `GET /research/desk/screen` as their sole serving endpoint, with zero change to what any desk store
+       RECORDS or to any recorded shape; coverage and freshness keep their single existing owner
+       (`desk_coverage.get_desk_coverage` over `bar_index`) and no second coverage path, cache or copy is
+       created anywhere; and nothing this journey adds starts, schedules, retries or auto-refreshes any
+       screen, top-up or reconciliation run — every run stays an explicit operator act.
+    4. Disclose, never judge. The endpoint and the page state what the pins ARE and whether a recording
+       exists under them, and stop there. The bar-store signature is a checksum over every member's
+       window-LAST-REQUESTED value — the page's own shipped note already says so
+       (`apps/frontend/app/desk/page.tsx:1725`) — so a differing signature proves exactly ONE thing: that
+       no recorded screen carries these pins, i.e. a run for this date would walk rather than reuse. The
+       copy therefore never claims that bars arrived, that the library advanced, or that any ranked row
+       would change, never uses a fresh / stale / current / behind / up-to-date / outdated judgement, and
+       never advises, predicts, implies urgency or names an action to take; no threshold, score,
+       confidence or staleness number is computed anywhere (this era's Non-Goals forbid new statistics and
+       gates outright), and `tests/test_copy_discipline.py` stays green unmodified.
+    5. Surface it on `/desk` as ONE more mount-time GET beside the shipped ones (no timer, no polling
+       loop, no auto-refresh — at most a refetch where the page already refetches its ledgers on a
+       terminal compute tick): (a) the Provenance panel (`DeskProvenance`,
+       `apps/frontend/app/desk/page.tsx:1702`) renders the resolved pins beside the DISPLAYED snapshot's
+       own recorded pins, with the match/differ statement computed at the OWNER and served — the page
+       derives nothing, not even an equality (the J-20 rule); (b) one descriptive line beside the Run
+       Screen control names the snapshot a run for that date would reuse (its own recorded id and
+       recorded-at) or states that no screen is recorded under the resolved pins and that a run would walk
+       `members_total` members; and (c) an honest empty state when no universe snapshot is registered.
+       **No new ranked-table column and no change to the ranked table**, so J-16's measured width contract
+       stands untouched at a 1440×900 viewport; every existing `data-testid` keeps its element and its
+       exact text; the row's stretched drill-in anchor keeps its `href`, `absolute inset-0`, `data-testid`
+       and dynamic consolidated `title` byte-unchanged.
+    6. Test fixture-scoped, over scoped universe/screen/bar-index stores (never `apps/backend/.data`): the
+       GET's resolved pins are byte-identical, value by value, to the pins `run_screen_and_record` resolves
+       for the SAME date over the SAME stores (the two resolutions cannot disagree); with a snapshot
+       recorded under those pins the payload names it and every copied meta field is byte-identical to that
+       record's own file, and a trigger for that date still reuses exactly the named snapshot (J-18's
+       shipped behaviour, unchanged); after ONE row is planted in the scoped index the same GET for the same
+       date resolves a different `bar_store_signature` and reports `recorded: null`, and a trigger then
+       walks and records a NEW snapshot while the earlier file stays byte-identical; with no universe
+       snapshot the payload is an honest empty at HTTP 200; the GET writes nothing and makes ZERO
+       `compute_tradability` calls and ZERO `BarStore` reads (assert the call counts — the
+       J-11/J-13/J-14/J-15 precedent); the same inputs twice produce a byte-identical body; every EXISTING
+       test in `test_desk_screen.py`, `test_desk_screen_compute.py`, `test_desk_coverage.py`,
+       `test_desk_ui_guards.py` and `test_desk_hover_tooltip_guard.py` passes UNMODIFIED; and a static
+       sweep of all 20 stored golden replay scripts proves no string this journey adds can resolve ahead of
+       any script's intended target (the J-20 rule — the replay matcher takes the FIRST visible match), so
+       every golden replays green with ZERO script edits (if a collision is unavoidable, MOVE the added
+       copy rather than edit a script).
+  - Acceptance: on the fixture-scoped rig the new GET, for a screen date whose five pins a recorded
+    snapshot already carries, names THAT snapshot with its `id`/`created_utc`/`bar_store_signature` and
+    ranked/skipped counts byte-identical to the record on disk and reports `members_total` equal to the
+    pinned universe record's own member count, while a trigger for that date reuses exactly that snapshot;
+    after a single row is planted in the scoped bar index, the same GET resolves a different
+    `bar_store_signature`, reports `recorded: null`, and a trigger then walks every member and records a
+    NEW snapshot with the earlier file byte-identical on disk (**single source of truth**: the resolution
+    is a NEW value with exactly one owner — the new desk module — and exactly one serving endpoint,
+    registered in the Data Contract BEFORE the code lands; every pin is resolved through the accessor that
+    already owns it (`screen_as_of`, `UniverseStore.list`, `Config.config_fingerprint`,
+    `compute_bar_store_signature` over `desk_coverage`'s index-only read), never a second derivation, and
+    the recorded-or-not answer comes from `ScreenStore.find_by_key` — the same lookup the run path makes —
+    with `desk_screen.ScreenStore` remaining the sole owner of rows, skip rows, the five-pin key and the
+    rank key and `GET /research/desk/screen` their sole serving endpoint; the endpoint persists nothing,
+    computes nothing, reads no bar and serves no coverage value, and the page derives nothing, not even a
+    match/differ equality — this SSOT criterion stands in place of a PnL-ledger append, which this era's
+    Non-Goals forbid); the honest empty state is served at HTTP 200 when no universe snapshot is
+    registered; every recorded universe, screen, top-up, reconciliation and screen-run file is proven
+    byte-identical on disk before and after the iteration apart from the snapshots the iteration's own
+    fixture-scoped runs deliberately create (SHA-256 listing — this journey's own code records nothing);
+    in a real browser after the T-9 clean rebuild, at a 1440×900 viewport with no horizontal scroll and
+    the ranked briefing table rendering exactly as J-16 shipped it, `/desk` shows BOTH states across
+    screenshots — one in which the displayed screen's own recorded pins match the resolved ones and the
+    page names the snapshot a run would reuse, and one in which they differ and the page states that no
+    screen is recorded under the resolved pins and that a run would walk `members_total` members — plus
+    one screenshot of the honest empty state (T-10: no screenshot ⇒ `unknown`, never `passing`; no native
+    `title` tooltip is required by this journey, so the T-10a headed rig is NOT needed and no capture may
+    depend on one); a **`[NEW]`-flagged demo-narrator walkthrough** covers the pin disclosure end to end,
+    narrated over both states; and the full backend suite is green with `Config().config_fingerprint()`
+    still `08e471b10130e1e2`, zero new `Config` fields, the `default` profile and `v1` byte-identical
+    (engine equivalence green), the MCP surface still exactly 17 tools, zero diff to
+    `desk_screen.py`/`desk_screen_compute.py`/`desk_coverage.py`/`tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`,
+    and `tests/test_copy_discipline.py` + `tests/test_desk_ui_guards.py` +
+    `tests/test_desk_hover_tooltip_guard.py` green unmodified. *(Keyless core; browser-verifiable. Why:
+    measured 2026-07-31 read-only over the frozen artifacts (no service started, no product code run) —
+    the bar-store signature was reconstructed with the module's OWN algorithm (`_bar_store_signature`,
+    `desk_screen.py:242`: sorted `(symbol, timeframe, MAX(window_end_utc))` tuples over the pinned
+    universe's members × `DESK_TOPUP_TIMEFRAMES`, canonical JSON, `sha256[:16]`) directly from
+    `.data/bar_index.db`. **No recorded screen can be reused today, and the page cannot say so.** The 12
+    snapshots in `.data/screen` carry four distinct signatures (`d7bc8f8127904d0a` ×2,
+    `7eab5f03cf23e8c7`, `350c85d18b1ff234` ×3, `ae2c740d1a70c9c7` ×6); the index as it stands resolves
+    **`2ce14e8f252966f7`** — a value NO recorded screen carries. The displayed briefing
+    `screen-2026-07-31-c169546856c7` (100 ranked / 1 skipped, recorded `2026-07-31T02:00:29.054546Z` under
+    `ae2c740d1a70c9c7`) carries today's own screen date and looks current, but the 06:52→06:56Z top-up
+    `topup-2026-07-31-8fb5c9a1f737` moved `MAX(window_end_utc)` to `2026-07-31T00:00:00Z` for **404 of 404**
+    pinned member × timeframe pairs, so that snapshot's own recorded coverage differs from the live index
+    on 404 of 404 pairs and its pin can no longer be hit. **The same click therefore has two behaviours
+    and nothing distinguishes them:** the desk's own screen-run ledger records
+    `screenrun-2026-07-31-725c4ec2bfcd` walking 101 members in 1m41s (`01:58:48.238Z` → `02:00:29.056Z`)
+    beside `screenrun-2026-07-31-0662273df270` and `screenrun-2026-07-31-fe0829e64a0d`, which J-18's
+    pre-check resolved as `reused` in 14 ms and 16 ms — all three for screen date 2026-07-31, all three
+    invisible in advance. **And the briefing reads as if nothing were pending:** every one of its 100 rows
+    prints `basis 2026-07-27 · 4 d before as-of` while the frozen store now holds `1d` bars through
+    2026-07-30 for all 101 members (read from the series files' own `covered_end_utc`; the 40 pairs whose
+    legacy files predate that meta field were all recorded on or before `2026-07-21T22:35:58Z` and cannot
+    hold newer content), which invites the reading "no newer daily close exists" when the truth is that
+    this screen predates the top-up. `GET /research/desk/screen/compute` serves only the process-scoped
+    manager snapshot (`null` after a restart, its own docstring), and `compute_bar_store_signature` exists
+    precisely so a caller can resolve the pin "WITHOUT running the full per-member walk" — no endpoint,
+    no page and no MCP tool exposes it today.)*
+
 <!-- /AUTO:journeys -->
 
 ## Anti-goals
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-desk/state/assumptions.md        | 26 ++++++++++++++++++++++
 runs/goal-session-desk/state/blueprint.md          |  4 ++++
 .../state/enhancement-proposals.jsonl              |  3 +++
 runs/goal-session-desk/state/proposer-result.json  |  4 ++--
 runs/goal-session-desk/telemetry.jsonl             | 20 +++++++++++++++++
 runs/goal-session-desk/trace/trace.jsonl           |  3 +++
 6 files changed, 58 insertions(+), 2 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
