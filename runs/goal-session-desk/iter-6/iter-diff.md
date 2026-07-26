# Iteration diff (bounded)

Files changed: 4. Shown in full: 3.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/frontend/app/desk/page.tsx` (71 lines not shown)

```diff
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index c0aa295..7627da6 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -1,10 +1,12 @@
 "use client";
 
+import Link from "next/link";
 import { useEffect, useState } from "react";
 import {
   cancelDeskScreenCompute,
   cancelDeskTopupCompute,
   fetchDeskScreen,
+  fetchDeskScreenByDate,
   fetchDeskScreenCompute,
   fetchDeskTopupCompute,
   triggerDeskScreenCompute,
@@ -44,6 +46,15 @@ import { fmt } from "@/lib/format";
 // Page-load GETs never trigger a compute (mount issues three GETs only; every POST is an explicit
 // button click). Nothing on this page is recomputed in the browser — every rendered value is a
 // verbatim re-format of what its owning endpoint already served.
+//
+// era-desk-iter-6 (J-05): the screen-history list is now interactive. Clicking a past entry issues
+// ONE new GET — `/research/desk/screen?date=<screen_date>` (already shipped J-03/iter-3,
+// `desk_routes.py:248-266`; this page is its first UI caller) — and renders THAT snapshot's own
+// `rows`/`skipped`/provenance in place of the currently-shown one (a read-only display swap, no
+// recompute, no route change). A "Latest" control reverts to the top-level `latest` snapshot
+// already held in `screenResult` state (no refetch). Every ranked/skip row is also a `Link` to
+// `/structure?symbol=<sym>&asof=<displayed snapshot's as_of>` — the era's one sanctioned additive
+// edit to `/structure` (its own query-param prefill, see that page's own comment).
 
 const NUMERIC_CELL = "px-2 py-1.5 text-right font-mono text-xs text-slate-200 whitespace-nowrap";
 const HEADER_CELL = "px-2 py-1 text-right text-[11px] font-medium text-slate-500";
@@ -56,6 +67,13 @@ const PRIMARY_BUTTON_CLASS =
 const CANCEL_BUTTON_CLASS =
   "mt-1 rounded-md border border-slate-700 bg-transparent px-2.5 py-1 text-xs font-medium text-slate-400 transition-colors hover:border-slate-500 hover:text-slate-200 focus:outline-none focus:ring-1 focus:ring-red-500 disabled:cursor-not-allowed disabled:opacity-50";
 
+// The secondary (quieter) button styling for the "Latest" history control — mirrors
+// structure/page.tsx's own `SECONDARY_BUTTON_CLASS` byte-for-byte (each page owns its own copy of
+// this tiny constant per this project's established convention — see this file's own
+// LoadingPanel/UnavailablePanel comment above).
+const SECONDARY_BUTTON_CLASS =
+  "rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm font-medium text-slate-400 transition-colors hover:border-slate-600 hover:bg-slate-800 hover:text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500 active:bg-slate-950";
+
 // Today's UTC calendar date (YYYY-MM-DD) — the value "Run Screen" submits as `screen_date`.
 // Mirrors /structure's own `todayUtcDate()` helper byte-for-byte (this project's own convention:
 // each module owns its tiny formatting helper rather than sharing one — see desk_screen.py's
@@ -169,15 +187,26 @@ function hasNoCoverageAtAll(coverage: Record<string, { has_bars: boolean }>): bo
 // (assumptions.md iter-4 entry 1 — `_select_best_band` itself stays byte-unchanged; this copy
 // keeps the chip honest about what the ranking actually selects rather than implying it is the
 // symbol's single strongest band).
-function DeskRow({ row }: { row: DeskScreenRow }) {
+// `asOf` is the DISPLAYED snapshot's own `as_of` (shared by every row in one screen, never a
+// per-row field) — the drill-in target's second query param. The `Link` fills the whole row via
+// the "stretched link" pattern (`position: relative` on the `<tr>`, `absolute inset-0` on the
+// `<a>`): one real `next/link` anchor, valid nested-in-a-`<td>` markup, clickable anywhere in the
+// row — never a raw `<a>` wrapping the `<tr>` directly (invalid HTML) and never `router.push`.
+function DeskRow({ row, asOf }: { row: DeskScreenRow; asOf: string }) {
   return (
     <tr
       data-testid="desk-screen-row"
       data-symbol={row.symbol}
       data-band-class={row.band_class ?? "none"}
-      className="border-b border-slate-800/60 last:border-b-0"
+      className="relative border-b border-slate-800/60 last:border-b-0 hover:bg-slate-900/40"
     >
       <td className={LABEL_CELL} data-testid="desk-row-symbol">
+        <Link
+          href={`/structure?symbol=${encodeURIComponent(row.symbol)}&asof=${encodeURIComponent(asOf)}`}
+          data-testid="desk-row-drill-in"
+          aria-label={`Open ${row.symbol} in Structure as of ${asOf}`}
+          className="absolute inset-0"
+        />
         {row.symbol}
       </td>
       <td className={LABEL_CELL} data-testid="desk-row-side">
@@ -209,7 +238,7 @@ function DeskRow({ row }: { row: DeskScreenRow }) {
   );
 }
 
-function DeskRowsTable({ rows }: { rows: DeskScreenRow[] }) {
+function DeskRowsTable({ rows, asOf }: { rows: DeskScreenRow[]; asOf: string }) {
   const uncoveredRanked = rows.filter((row) => hasNoCoverageAtAll(row.coverage)).length;
   return (
     <div className="overflow-x-auto">
@@ -236,7 +265,7 @@ function DeskRowsTable({ rows }: { rows: DeskScreenRow[] }) {
         </thead>
         <tbody>
           {rows.map((row) => (
-            <DeskRow key={row.symbol} row={row} />
+            <DeskRow key={row.symbol} row={row} asOf={asOf} />
           ))}
         </tbody>
       </table>
@@ -247,15 +276,26 @@ function DeskRowsTable({ rows }: { rows: DeskScreenRow[] }) {
 // --- Skipped-members section — grouped under an honest heading, "no_bars" vs "no_basis" never
 // conflated (two distinct, honest absences). ---------------------------------------------------
 
-function DeskSkipRow({ skip }: { skip: DeskScreenSkip }) {
+// Per the goal's own iter-6 assumption (a skipped symbol still drills into `/structure`, which
+// honestly shows its own no-bars/empty state there — no fabrication risk): skip rows link exactly
+// like ranked rows, same `asOf`, same "stretched link" pattern (see `DeskRow`'s comment above).
+function DeskSkipRow({ skip, asOf }: { skip: DeskScreenSkip; asOf: string }) {
   return (
     <tr
       data-testid="desk-skip-row"
       data-symbol={skip.symbol}
       data-reason={skip.reason}
-      className="border-b border-slate-800/60 last:border-b-0"
+      className="relative border-b border-slate-800/60 last:border-b-0 hover:bg-slate-900/40"
     >
-      <td className={LABEL_CELL}>{skip.symbol}</td>
+      <td className={LABEL_CELL}>
+        <Link
+          href={`/structure?symbol=${encodeURIComponent(skip.symbol)}&asof=${encodeURIComponent(asOf)}`}
+          data-testid="desk-skip-row-drill-in"
+          aria-label={`Open ${skip.symbol} in Structure as of ${asOf}`}
+          className="absolute inset-0"
+        />
+        {skip.symbol}
+      </td>
       <td className={LABEL_CELL} data-testid="desk-skip-reason">
         {skip.reason === "no_bars" ? "no bars" : "no basis"}
       </td>
@@ -269,7 +309,7 @@ function DeskSkipRow({ skip }: { skip: DeskScreenSkip }) {
   );
 }
 
-function DeskSkipTable({ rows }: { rows: DeskScreenSkip[] }) {
+function DeskSkipTable({ rows, asOf }: { rows: DeskScreenSkip[]; asOf: string }) {
   return (
     <div className="overflow-x-auto">
       <table className="w-full border-collapse">
@@ -283,7 +323,7 @@ function DeskSkipTable({ rows }: { rows: DeskScreenSkip[] }) {
         </thead>
         <tbody>
           {rows.map((skip) => (
-            <DeskSkipRow key={skip.symbol} skip={skip} />
+            <DeskSkipRow key={skip.symbol} skip={skip} asOf={asOf} />
           ))}
         </tbody>
       </table>
@@ -291,7 +331,7 @@ function DeskSkipTable({ rows }: { rows: DeskScreenSkip[] }) {
   );
 }
 
-function DeskSkippedSection({ skipped }: { skipped: DeskScreenSkip[] }) {
+function DeskSkippedSection({ skipped, asOf }: { skipped: DeskScreenSkip[]; asOf: string }) {
   const noBars = skipped.filter((s) => s.reason === "no_bars");
   const noBasis = skipped.filter((s) => s.reason === "no_basis");
   return (
@@ -304,7 +344,7 @@ function DeskSkippedSection({ skipped }: { skipped: DeskScreenSkip[] }) {
           >
             Skipped — no bars ({noBars.length})
           </h3>
-          <DeskSkipTable rows={noBars} />
+          <DeskSkipTable rows={noBars} asOf={asOf} />
         </div>
       )}
       {noBasis.length > 0 && (
@@ -315,21 +355,40 @@ function DeskSkippedSection({ skipped }: { skipped: DeskScreenSkip[] }) {
           >
             Skipped — no basis session ({noBasis.length})
           </h3>
-          <DeskSkipTable rows={noBasis} />
+          <DeskSkipTable rows={noBasis} asOf={asOf} />
         </div>
       )}
     </div>
   );
 }
 
-// --- Screen history — read-only (date + rows/skipped counts + provenance summary), from the
-// meta-only `screens` list. No click/select interaction and no per-entry full-row fetch this
-// iteration (J-05 scope, deferred — assumptions.md/blueprint.md iter-4 "screen-history
-// interactivity split"). --------------------------------------------------------------------------
+// --- Screen history — date + rows/skipped counts + provenance summary, from the meta-only
+// `screens` list. era-desk-iter-6 (J-05): now CLICKABLE — selecting a row fetches that exact
+// date's persisted snapshot (`GET /research/desk/screen?date=`) and swaps it into the page's
+// display in place; the click-through itself is a same-page state swap, never a navigation, so it
+// stays a plain `onClick` (not a `Link` — the `Link`/drill-in requirement below is only for
+// jumping to `/structure`). `selectedDate` highlights the currently-displayed row (`null` while
+// viewing the latest screen, since the latest need not be one of the listed historical rows). -----
 
-function DeskHistoryRow({ meta }: { meta: DeskScreenMeta }) {
+function DeskHistoryRow({
+  meta,
+  onSelect,
+  selected,
+}: {
+  meta: DeskScreenMeta;
+  onSelect: (date: string) => void;
+  selected: boolean;
+}) {
   return (
-    <tr data-testid="desk-history-row" className="border-b border-slate-800/60 last:border-b-0">
+    <tr
+      data-testid="desk-history-row"
+      data-screen-date={meta.screen_date}
+      data-selected={selected}
+      onClick={() => onSelect(meta.screen_date)}
+      className={`cursor-pointer border-b border-slate-800/60 transition-colors last:border-b-0 hover:bg-slate-900/40 ${
+        selected ? "bg-slate-800/60" : ""
+      }`}
+    >
       <td className={LABEL_CELL}>{meta.screen_date}</td>
       <td className={NUMERIC_CELL}>{meta.counts.rows}</td>
       <td className={NUMERIC_CELL}>{meta.counts.skipped}</td>
@@ -340,7 +399,15 @@ function DeskHistoryRow({ meta }: { meta: DeskScreenMeta }) {
   );
 }
 
-function DeskHistoryTable({ screens }: { screens: DeskScreenMeta[] }) {
+function DeskHistoryTable({
+  screens,
+  onSelect,
+  selectedDate,
+}: {
+  screens: DeskScreenMeta[];
+  onSelect: (date: string) => void;
+  selectedDate: string | null;
+}) {
   if (screens.length === 0) {
     return <EmptyState testid="desk-history-empty" title="No screens recorded yet." />;
   }
@@ -357,7 +424,12 @@ function DeskHistoryTable({ screens }: { screens: DeskScreenMeta[] }) {
         </thead>
         <tbody>
           {screens.map((meta) => (
-            <DeskHistoryRow key={meta.id} meta={meta} />
+            <DeskHistoryRow
+              key={meta.id}
+              meta={meta}
+              onSelect={onSelect}
+              selected={meta.screen_date === selectedDate}
+            />
           ))}
         </tbody>
       </table>
@@ -624,6 +696,103 @@ function DeskNotComputedPanel({
   );
 }
 
+// The populated view — a real snapshot exists (`latest !== null`), whether it is the latest one
+// or a history row the operator selected. `snapshot` is the ONE displayed record; the Provenance/
+// Briefing/Skipped sections read it verbatim, same as before this iteration — only the SOURCE of
+// `snapshot` (latest vs. a selected history entry) is new.
+function DeskPopulatedScreen({
+  snapshot,
+  screens,
+  isViewingLatest,
+  historyFetchError,
+  onSelectHistory,
+  onShowLatest,
+  selectedHistoryDate,
+  screenControlProps,
+  topupControlProps,
+}: {
+  snapshot: DeskScreenSnapshot;
+  screens: DeskScreenMeta[];
+  isViewingLatest: boolean;
+  historyFetchError: string | null;
+  onSelectHistory: (date: string) => void;
+  onShowLatest: () => void;
+  selectedHistoryDate: string | null;
+  screenControlProps: ScreenControlProps;
+  topupControlProps: TopupControlProps;
+}) {
+  return (
+    <div className="space-y-6">
+      {!isViewingLatest && (
+        <div
+          data-testid="desk-viewing-indicator"
+          className="flex flex-wrap items-center gap-3 rounded-md border border-slate-700 bg-slate-800/40 px-3 py-2 text-xs text-slate-400"
+        >
+          <span>Viewing the recorded screen for {snapshot.screen_date} — not the latest.</span>
+          <button
+            type="button"
+            data-testid="desk-history-latest-button"
+            onClick={onShowLatest}
+            className={SECONDARY_BUTTON_CLASS}
+          >
+            Latest
+          </button>
+        </div>
+      )}
+      {historyFetchError && (
+        <p data-testid="desk-history-fetch-error" className="text-xs text-amber-300">
+          {historyFetchError}
+        </p>
+      )}
+
+      <section aria-label="Provenance">
+        <Panel title="Provenance">
+          <DeskProvenance snapshot={snapshot} />
+        </Panel>
+      </section>
+
+      <section aria-label="Briefing">
+        <Panel title="Briefing">
+          {snapshot.rows.length === 0 ? (
+            <EmptyState testid="desk-rows-empty" title="No members ranked in this screen." />
+          ) : (
+            <DeskRowsTable rows={snapshot.rows} asOf={snapshot.as_of} />
+          )}
+        </Panel>
+      </section>
+
+      <section aria-label="Skipped members">
+        <Panel title="Skipped Members">
+          {snapshot.skipped.length === 0 ? (
+            <EmptyState testid="desk-skipped-empty" title="No members were skipped in this screen." />
+          ) : (
+            <DeskSkippedSection skipped={snapshot.skipped} asOf={snapshot.as_of} />
+          )}
+        </Panel>
+      </section>
+
+      <section aria-label="Screen history">
+        <Panel title="Screen History">
+          <DeskHistoryTable
+            screens={screens}
+            onSelect={onSelectHistory}
+            selectedDate={selectedHistoryDate}
+          />
+        </Panel>
+      </section>
+
+      <section aria-label="Run Screen and Top-up controls">
+        <Panel title="Run Screen / Top-up">
+          <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start sm:justify-center sm:gap-12">
+            <ScreenComputeControl {...screenControlProps} />
+            <TopupComputeControl {...topupControlProps} />
+          </div>
+        </Panel>
+      </section>
+    </div>
+  );
+}
+
 // --- The page --------------------------------------------------------------------------------------
 
 export default function DeskPage() {
@@ -645,6 +814,15 @@ export default function DeskPage() {
   const [topupCancelRequested, setTopupCancelRequested] = useState(false);
   const [topupCancelError, setTopupCancelError] = useState<string | null>(null);
 
+  // era-desk-iter-6 (J-05): the screen-history click-through. `viewingSnapshot` is `null` while
+  // showing the top-level `latest` snapshot already held in `screenResult` (no refetch needed to
+  // return to it — TC-2); once a history row is selected, it holds THAT date's own full snapshot,
+  // fetched via the already-shipped `?date=` read (`fetchDeskScreenByDate`, zero new backend
+  // route). `historyFetchError` surfaces a failed/no-match click WITHOUT disturbing whatever is
+  // currently displayed (no crash, no blank state — the plan's own error-case requirement).
+  const [viewingSnapshot, setViewingSnapshot] = useState<DeskScreenSnapshot | null>(null);
+  const [historyFetchError, setHistoryFetchError] = useState<string | null>(null);
+
   // Mount: exactly three GETs, zero POSTs (TC-19) — the screen list/latest, and BOTH compute
   // managers' current/last snapshot (seeds a page load mid-job or post-terminal without a
   // spurious extra click — the /structure edge-report mount-seeding precedent).
@@ -747,6 +925,30 @@ export default function DeskPage() {
     }
   }
 
+  // era-desk-iter-6 (J-05): select a past history row — fetch-and-swap, no POST, no recompute
+  // (TC-1). A date with no matching recorded screen (`{"screen": null}`) or an unreachable backend
+  // both leave the currently-displayed snapshot exactly as it was — only the error note changes.
+  async function handleSelectHistoryScreen(date: string) {
+    setHistoryFetchError(null);
+    const result = await fetchDeskScreenByDate(date);
+    if (result.ok && result.data !== null) {
+      setViewingSnapshot(result.data);
+      return;
+    }
+    setHistoryFetchError(
+      result.ok
+        ? `No recorded screen matches ${date} — still showing the previously displayed screen.`
+        : result.error ?? "That recorded screen could not be loaded.",
+    );
+  }
+
+  // Revert to the top-level `latest` snapshot already held in `screenResult` state (TC-2) — no
+  // refetch, since the page already has it.
+  function handleShowLatest() {
+    setViewingSnapshot(null);
+    setHistoryFetchError(null);
+  }
+
   const screenControlProps: ScreenControlProps = {
     compute: screenCompute,
     onTrigger: handleTriggerScreen,
@@ -768,6 +970,17 @@ export default function DeskPage() {
 
   const latest = screenResult?.ok ? screenResult.data?.latest ?? null : null;
   const screens = screenResult?.ok ? screenResult.data?.screens ?? [] : [];
+  // The snapshot actually on screen: a selected history entry, or `latest` when none is selected.
+  // `latest === null` (never `displayedSnapshot === null`) stays the ONE discriminator for the
+  // honest "Desk screen not computed yet." empty state — with no screen ever recorded there is
+  // nothing in `screens` to have selected in the first place, so the two states cannot diverge.
+  const displayedSnapshot = viewingSnapshot ?? latest;
+  // Whether what is ON SCREEN is the newest recorded screen — a comparison of the displayed
... [diff_bound] apps/frontend/app/desk/page.tsx: 71 more diff lines omitted — Read the file for full detail
diff --git a/apps/frontend/app/structure/page.tsx b/apps/frontend/app/structure/page.tsx
index 165a09b..3ee9f03 100644
--- a/apps/frontend/app/structure/page.tsx
+++ b/apps/frontend/app/structure/page.tsx
@@ -1,6 +1,7 @@
 "use client";
 
-import { useEffect, useRef, useState } from "react";
+import { Suspense, useEffect, useRef, useState } from "react";
+import { useSearchParams } from "next/navigation";
 import {
   cancelEdgeReportCompute,
   createBacktest,
@@ -59,6 +60,13 @@ import { FeedBasisBadge } from "@/components/FeedBasisBadge";
 // UI_ROUTES). Follows the /performance page pattern: client component, no business logic,
 // canonical endpoints read verbatim, `{ok, data, error}`-shaped fetch results.
 //
+// era-desk-iter-6 (J-05): the era's ONE sanctioned edit to this otherwise-frozen file — an
+// additive query-param prefill (`?symbol=&asof=`, reached from a `/desk` briefing row's drill-in
+// link). See the `useSearchParams` block below for the whole change: it seeds the SAME
+// `symbolInput`/`asOfInput` state and calls the SAME `handleLoad` a manual Load click already
+// uses. Nothing else on this page changed — every default, control, and rendered state when the
+// params are absent stays byte-for-byte what it was before this iteration (T-8).
+//
 // Era-5 J-05 added the page's first explicit write action: a fetch-control section (symbol +
 // timeframe + UTC date range + a "Fetch from Yahoo Finance" button). Submitting POSTs
 // `/research/bars` (keyless; store-first — an already-fetched window is served from storage with
@@ -1364,7 +1372,10 @@ function BacktestPanel({
   );
 }
 
-export default function StructurePage() {
+// The App Router requires any `useSearchParams()` reader to sit inside a `Suspense` boundary, so
+// the default export is now a thin wrapper (`StructurePage` below) — this renamed component holds
+// every pre-existing hook/handler/render byte-unchanged; only the wrapper is new.
+function StructurePageContent() {
   const [symbolInput, setSymbolInput] = useState("");
   const [asOfInput, setAsOfInput] = useState("");
   const [levelsState, setLevelsState] = useState<LoadState<LevelsResponse>>({ phase: "idle" });
@@ -1681,6 +1692,27 @@ export default function StructurePage() {
     };
   }, [showRawLevels, loadedQuery, tradabilityState.phase]);
 
+  // J-05-PREFILL-START -- era-desk-iter-6: additive-only query-param prefill of the Load form
+  // above, reached from a `/desk` briefing row's drill-in link (`/structure?symbol=&asof=`). ONLY
+  // when BOTH params are present and non-empty does this seed `symbolInput`/`asOfInput` and invoke
+  // `handleLoad` -- the SAME load path a manual Load click already uses (no second fetch/compute
+  // function -- TC-6). Runs at most once per mount (`prefillRanRef`), so a later in-page Load click
+  // is never overridden. Absent or partial params leave every default/control/rendered state
+  // byte-unchanged (T-8, TC-4) -- the effect returns before touching any state.
+  const searchParams = useSearchParams();
+  const prefillRanRef = useRef(false);
+  useEffect(() => {
+    if (prefillRanRef.current) return;
+    const symbol = searchParams.get("symbol")?.trim() ?? "";
+    const asOf = searchParams.get("asof")?.trim() ?? "";
+    if (!symbol || !asOf) return;
+    prefillRanRef.current = true;
+    setSymbolInput(symbol);
+    setAsOfInput(asOf);
+    handleLoad(symbol, asOf);
+  }, [searchParams]);
+  // J-05-PREFILL-END
+
   function handleSubmit(e: React.FormEvent) {
     e.preventDefault();
     handleLoad(symbolInput, asOfInput);
@@ -2811,3 +2843,16 @@ export default function StructurePage() {
     </div>
   );
 }
+
+// The real default export -- a thin `Suspense` wrapper around `StructurePageContent` (required by
+// the App Router for any page reading `useSearchParams()`). `fallback={null}` renders nothing
+// extra: `StructurePageContent` fetches its own data client-side and already owns every loading
+// state this page needs, so a second, page-level loading skeleton here would only flash a state
+// nothing in this iteration's baseline ever showed (TC-4's pixel-for-pixel requirement).
+export default function StructurePage() {
+  return (
+    <Suspense fallback={null}>
+      <StructurePageContent />
+    </Suspense>
+  );
+}
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index fa0d389..65af472 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -8,6 +8,7 @@ import type {
   DatasetsListResult,
   DeskScreenComputeSnapshot,
   DeskScreenListResult,
+  DeskScreenSnapshot,
   DeskTopupComputeSnapshot,
   EdgeReportComputeSnapshot,
   EdgeReportPayload,
@@ -944,6 +945,36 @@ export async function fetchDeskScreen(): Promise<{
   }
 }
 
+// GET /research/desk/screen?date= — the exact persisted snapshot recorded for that date, verbatim,
+// or `null` when nothing matches (an honest "nothing recorded for this date", never an error).
+// era-desk-iter-6 (J-05): the FIRST UI caller of this already-shipped `?date=` branch
+// (`desk_routes.py:248-266`, shipped J-03/iter-3) — no new backend route. Mirrors `fetchDeskScreen`'s
+// exact `{ok, data, error}` shape byte-for-byte; `data` here is the single `DeskScreenSnapshot | null`
+// the `?date=` branch serves, distinct from `fetchDeskScreen`'s list-shaped `DeskScreenListResult`.
+export async function fetchDeskScreenByDate(date: string): Promise<{
+  ok: boolean;
+  data: DeskScreenSnapshot | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/screen?date=${encodeURIComponent(date)}`);
+    if (res.ok) {
+      const data = await res.json();
+      return { ok: true, data: (data.screen as DeskScreenSnapshot | null) ?? null };
+    }
+    let error = "The desk screen for that date could not be loaded.";
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
 // POST /research/desk/screen/compute — start (or, while one is already running, observe) the
 // single-flight screen compute job. `screenDate` is the CALLER's own today (the `todayUtcDate()`
 // helper, /structure's own "Today" shortcut precedent) — this function takes it as a parameter
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
new file mode 100644
index 0000000..a786acd
--- /dev/null
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -0,0 +1,119 @@
+"""era-desk-iter-6 (J-05) source-introspection guard tests -- the ``test_copy_discipline.py``
+pattern (read a frontend .tsx file as TEXT, assert on substrings; no browser, no runtime).
+
+Two guards, each proving something about the frontend a backend-only test suite otherwise could
+not see:
+
+  (a) TC-5 -- ``apps/frontend/app/desk/page.tsx`` never references any of the structure-side
+      compute endpoints/functions (``/research/tradability``, ``/research/levels``,
+      ``compute_tradability``, ``compute_levels``) -- every number the desk briefing renders comes
+      from the already-fetched screen snapshot (``GET /research/desk/screen``), never a second,
+      divergent computation (single-source-of-truth -- the era's own hard anti-goal).
+  (b) TC-6 -- the NEW ``/structure`` query-param prefill block (delimited by the
+      ``J-05-PREFILL-START``/``J-05-PREFILL-END`` markers in ``structure/page.tsx``) calls the
+      SAME ``handleLoad`` the manual Load button already calls, and introduces no second
+      fetch/compute path.
+
+A guard that can never fail proves nothing -- each carries a seeded counter-test proving the
+detection logic itself actually catches a violation (the ``test_copy_discipline.py``
+seeded-violation precedent)."""
+
+from __future__ import annotations
+
+import pathlib
+
+_FRONTEND_ROOT = pathlib.Path(__file__).resolve().parents[2] / "frontend"
+_DESK_PAGE = _FRONTEND_ROOT / "app" / "desk" / "page.tsx"
+_STRUCTURE_PAGE = _FRONTEND_ROOT / "app" / "structure" / "page.tsx"
+
+_FORBIDDEN_DESK_REFERENCES = (
+    "/research/tradability",
+    "/research/levels",
+    "compute_tradability",
+    "compute_levels",
+)
+
+# Every fetch/compute-trigger function this page already imports from lib/api, PLUS a bare
+# `fetch(` -- if the prefill block ever grows a second network call of its own rather than
+# reusing `handleLoad`, one of these substrings will be present.
+_FORBIDDEN_PREFILL_CALLS = (
+    "fetchLevels(",
+    "fetchTradability(",
+    "recordBarSeries(",
+    "createBacktest(",
+    "triggerEdgeReportCompute(",
+    "fetch(",
+)
+
+
+def test_desk_page_never_references_structure_compute_endpoints():
+    """TC-5: every rendered desk value comes from the already-fetched screen snapshot -- the desk
+    page source contains zero references to the structure-side compute endpoints/functions."""
+    source = _DESK_PAGE.read_text()
+    hits = [needle for needle in _FORBIDDEN_DESK_REFERENCES if needle in source]
+    assert not hits, (
+        f"apps/frontend/app/desk/page.tsx references {hits} -- the desk briefing must read every "
+        "value from GET /research/desk/screen verbatim, never recompute a structure number "
+        "client-side"
+    )
+
+
+def test_desk_page_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail -- a lint that cannot fail proves nothing."""
+    seeded_source = "const x = fetch('/research/tradability?symbol=AAPL');"
+    hits = [needle for needle in _FORBIDDEN_DESK_REFERENCES if needle in seeded_source]
+    assert hits == ["/research/tradability"]
+
+
+def _extract_prefill_block(source: str) -> str:
+    start = source.index("// J-05-PREFILL-START")
+    end = source.index("// J-05-PREFILL-END")
+    assert start < end, "J-05-PREFILL-START must precede J-05-PREFILL-END"
+    return source[start:end]
+
+
+def test_structure_page_has_the_j05_prefill_markers():
+    """The extraction below is only meaningful if the markers actually exist -- an absent block
+    would otherwise make ``test_structure_prefill_reuses_the_existing_load_function`` vacuous
+    (``str.index`` raises ``ValueError`` rather than silently matching nothing, so a missing
+    marker already fails loudly; this test names that failure mode explicitly)."""
+    source = _STRUCTURE_PAGE.read_text()
+    assert "// J-05-PREFILL-START" in source
+    assert "// J-05-PREFILL-END" in source
+    assert "useSearchParams" in source
+
+
+def test_structure_prefill_reuses_the_existing_load_function():
+    """TC-6: the new query-param prefill block calls the SAME ``handleLoad`` the manual Load
+    button already calls -- no second fetch/compute function is introduced."""
+    source = _STRUCTURE_PAGE.read_text()
+    block = _extract_prefill_block(source)
+    assert "handleLoad(" in block, (
+        "the J-05 prefill block never calls handleLoad() -- it must reuse the manual Load "
+        "button's own load path, not a second one"
+    )
+    hits = [needle for needle in _FORBIDDEN_PREFILL_CALLS if needle in block]
+    assert not hits, (
+        f"the J-05 prefill block calls {hits} -- it must call ONLY the existing handleLoad(), "
+        "never a second fetch/compute function"
+    )
+
+
+def test_structure_prefill_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail (counter-test): a seeded second fetch call inside the prefill block is
+    caught, and a block missing the handleLoad() call is caught too."""
+    seeded_block_with_second_fetch = (
+        "// J-05-PREFILL-START\n"
+        "useEffect(() => { fetchLevels(symbol, asOf); handleLoad(symbol, asOf); }, []);\n"
+        "// J-05-PREFILL-END\n"
+    )
+    hits = [
+        needle for needle in _FORBIDDEN_PREFILL_CALLS if needle in seeded_block_with_second_fetch
+    ]
+    assert hits == ["fetchLevels("]
+
+    seeded_block_missing_handle_load = (
+        "// J-05-PREFILL-START\nuseEffect(() => { setSymbolInput(symbol); }, []);\n"
+        "// J-05-PREFILL-END\n"
+    )
+    assert "handleLoad(" not in seeded_block_missing_handle_load
```
