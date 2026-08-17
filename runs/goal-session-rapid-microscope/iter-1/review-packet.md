# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

```diff
diff --git a/apps/backend/app/main.py b/apps/backend/app/main.py
index eb779be..47a6983 100644
--- a/apps/backend/app/main.py
+++ b/apps/backend/app/main.py
@@ -40,6 +40,7 @@ from .providers.adapters.base import (
 from .providers.historical import HistoricalProvider
 from .providers.live import LiveProvider
 from .research.desk_routes import router as desk_router
+from .research.micro_routes import router as micro_router
 from .research.referee_routes import router as referee_router
 from .research.routes import (
     ResearchRegistry,
@@ -208,6 +209,13 @@ app.include_router(desk_router)
 # prefix allowlist automatically — no MCP change needed.
 app.include_router(referee_router)
 
+# Era "The Rapid Microscope" (J-01): the corpus-truth fold, under /research/desk/micro — its own
+# module for the SAME reason referee_routes.py itself is separate (already large; see
+# micro_routes.py's own docstring). Reached by the MCP get_endpoint's existing /research/ prefix
+# allowlist automatically — no MCP change needed (no new MCP tool this iteration; desk_micro_
+# readiness lands in J-08).
+app.include_router(micro_router)
+
 # The meta namespace (Data Contract row 35, J-01): the canonical UI route map. The rendered nav
 # and the MCP ``ui_route_map`` tool read it — never a hand-maintained duplicate list.
 app.include_router(meta_router)
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index a8d8b85..c7d8b12 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -295,6 +295,16 @@ _PRICE_ARITHMETIC_FIELDS = (
     r"|evidence\.playbook_occurrence\.(?:records|distinct_sessions|signals_at_current_basis)"
     r"|evidence\.strategy_trade\.(?:dataset_count|trade_count)"
     r"|evidence\.strategy_trade\.per_split_counts\.(?:train|holdout)"
+    # goal-rapid-microscope-iter-1 (J-01): the new Microscope Readiness section's own served
+    # numerics -- GET /research/desk/micro/readiness read verbatim for the first time in the
+    # browser. Every corpus total, per-shard count/byte-size/fallback-fraction, and per-study
+    # floor pair renders as served (`.toFixed()`/`.toLocaleString()` are FORMATTING calls, never
+    # arithmetic); no client-side symbol-day share, byte-to-MB conversion, fallback percentage,
+    # or floor-shortfall arithmetic is ever legitimate here.
+    r"|readiness\.totals\.(?:distinct_symbol_days|distinct_datasets|rth_minutes_covered"
+    r"|session_equivalents|referee_tick_gate_symbol_days)"
+    r"|shard\.(?:trade_count|quote_count|bytes|fallback_frac)"
+    r"|floor\.(?:required_sessions|available_sessions)"
 )
 _PRICE_ARITHMETIC_PATTERN = re.compile(
     rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
@@ -507,6 +517,27 @@ def test_desk_page_price_arithmetic_guard_catches_evidence_basis_field_arithmeti
     seeded_signal_unmeasured = "const measured = cell.signal.n - cell.signal.n_unmeasured;"
     assert _PRICE_ARITHMETIC_PATTERN.search(seeded_signal_unmeasured) is not None
 
+
+def test_desk_page_price_arithmetic_guard_catches_micro_readiness_field_arithmetic():
+    """goal-rapid-microscope-iter-1 (J-01) TC-9 counter-test: the extended guard catches
+    arithmetic on the new Microscope Readiness section's own served numerics -- proving the
+    widened pattern actually fails on injected client-side arithmetic, not just that it passes on
+    unmodified source."""
+    seeded_share = (
+        "const share = readiness.totals.distinct_symbol_days / "
+        "readiness.totals.referee_tick_gate_symbol_days;"
+    )
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_share) is not None
+
+    seeded_pct = "const pct = shard.fallback_frac * 100;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_pct) is not None
+
+    seeded_mb = "const mb = shard.bytes / 1_000_000;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_mb) is not None
+
+    seeded_shortfall = "const shortfall = floor.required_sessions - floor.available_sessions;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_shortfall) is not None
+
     seeded_signal_sessions = "const perSession = cell.signal.n / cell.signal.n_sessions;"
     assert _PRICE_ARITHMETIC_PATTERN.search(seeded_signal_sessions) is not None
 
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index a990272..41bf16e 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -56,6 +56,7 @@ import {
   postRefereeRegistryHypothesis,
   triggerRefereeEvaluate,
   triggerRefereeNullsCompute,
+  fetchMicroReadiness,
 } from "@/lib/api";
 import type {
   DeskDeepBackfillComputeSnapshot,
@@ -119,6 +120,7 @@ import type {
   DeskTopupRun,
   DeskTopupRunMeta,
   DeskTopupRunsListResult,
+  MicroReadinessResponse,
   RefereeAdjudicationEntry,
   RefereeAdjudicationsResponse,
   RefereeEvaluateRunsListResult,
@@ -362,7 +364,8 @@ type DeskCollapsibleSection =
   | "playbookEvidence"
   | "refereeRegistry"
   | "refereeAdjudications"
-  | "refereeRuns";
+  | "refereeRuns"
+  | "microReadiness";
 // DESK-COLLAPSED-END
 
 const PRIMARY_BUTTON_CLASS =
@@ -5846,6 +5849,229 @@ function RefereeRunsSection({
   );
 }
 
+// goal-rapid-microscope-iter-1 (J-01): the Microscope Readiness section -- the era's FIRST
+// Rapid-Microscope `/desk` section, rendered directly BELOW the shipped Referee Runs section
+// (the current last section, T-11: new data-testids only, no shipped data-testid or heading
+// string reused). A plain deferred read (no compute manager, T-8 -- "page-load GETs never
+// compute"): the totals line, the per-shard inventory table, and the per-study floor table all
+// render GET /research/desk/micro/readiness's own fetched body, zero client-side arithmetic on
+// any numeric read here (test_desk_ui_guards.py's widened _PRICE_ARITHMETIC_FIELDS covers every
+// one -- `.toFixed()`/`.toLocaleString()` below are FORMATTING calls, never `+`/`-`/`*`/`/`
+// combined with a served field), and every honest-absence/degraded case reuses the shipped
+// EmptyState/UnavailablePanel components rather than rendering blank.
+function MicroReadinessSection({
+  readinessResult,
+}: {
+  readinessResult: { ok: boolean; data: MicroReadinessResponse | null; error?: string } | null;
+}) {
+  if (readinessResult === null) {
+    return <LoadingPanel testid="micro-readiness-loading" />;
+  }
+  if (!readinessResult.ok || readinessResult.data === null) {
+    return (
+      <UnavailablePanel
+        testid="micro-readiness-unavailable"
+        message={readinessResult.error ?? "The microscope readiness corpus could not be loaded."}
+      />
+    );
+  }
+  const readiness = readinessResult.data;
+  return (
+    <div data-testid="micro-readiness-section">
+      <p className="mb-3 text-xs text-slate-500">
+        The era&apos;s honest corpus truth (GET /research/desk/micro/readiness, read verbatim):
+        exactly what tick evidence exists on disk today, and which predeclared pilot-study floor
+        it clears — today, none.
+      </p>
+
+      <div data-testid="micro-readiness-totals-block" className="mb-4">
+        <h4 className="mb-2 text-xs font-semibold text-slate-400">Corpus Totals</h4>
+        <div className="overflow-x-auto">
+          <table
+            data-testid="micro-readiness-totals-table"
+            className="w-full min-w-[420px] border-collapse text-xs"
+          >
+            <tbody>
+              <tr className="border-b border-slate-900">
+                <td className="px-1.5 py-1 text-slate-500">Distinct symbol-days</td>
+                <td
+                  data-testid="micro-readiness-distinct-symbol-days"
+                  className="px-1.5 py-1 text-right font-mono text-slate-300"
+                >
+                  {readiness.totals.distinct_symbol_days}
+                </td>
+              </tr>
+              <tr className="border-b border-slate-900">
+                <td className="px-1.5 py-1 text-slate-500">Distinct datasets</td>
+                <td
+                  data-testid="micro-readiness-distinct-datasets"
+                  className="px-1.5 py-1 text-right font-mono text-slate-300"
+                >
+                  {readiness.totals.distinct_datasets}
+                </td>
+              </tr>
+              <tr className="border-b border-slate-900">
+                <td className="px-1.5 py-1 text-slate-500">RTH minutes covered</td>
+                <td
+                  data-testid="micro-readiness-rth-minutes-covered"
+                  className="px-1.5 py-1 text-right font-mono text-slate-300"
+                >
+                  {readiness.totals.rth_minutes_covered.toFixed(2)}
+                </td>
+              </tr>
+              <tr className="border-b border-slate-900">
+                <td className="px-1.5 py-1 text-slate-500">Session-equivalents</td>
+                <td
+                  data-testid="micro-readiness-session-equivalents"
+                  className="px-1.5 py-1 text-right font-mono text-slate-300"
+                >
+                  {readiness.totals.session_equivalents.toFixed(4)}
+                </td>
+              </tr>
+              <tr>
+                <td className="px-1.5 py-1 text-slate-500">Referee tick-gate (symbol-days)</td>
+                <td
+                  data-testid="micro-readiness-referee-tick-gate-symbol-days"
+                  className="px-1.5 py-1 text-right font-mono text-slate-300"
+                >
+                  {readiness.totals.referee_tick_gate_symbol_days}
+                </td>
+              </tr>
+            </tbody>
+          </table>
+        </div>
+      </div>
+
+      <div data-testid="micro-readiness-shards-block" className="mb-4">
+        <h4 className="mb-2 text-xs font-semibold text-slate-400">Legacy Tick Shards</h4>
+        {readiness.shards.length === 0 ? (
+          <EmptyState testid="micro-readiness-shards-empty" title="No tick shards recorded." />
+        ) : (
+          <div className="overflow-x-auto">
+            <table
+              data-testid="micro-readiness-shards-table"
+              className="w-full min-w-[1100px] border-collapse text-xs"
+            >
+              <thead>
+                <tr className="border-b border-slate-800 text-left text-slate-500">
+                  <th className="px-1.5 py-1">Symbol</th>
+                  <th className="px-1.5 py-1">Session date</th>
+                  <th className="px-1.5 py-1">Feed</th>
+                  <th className="px-1.5 py-1">Window (ET)</th>
+                  <th className="px-1.5 py-1 text-right">Trades</th>
+                  <th className="px-1.5 py-1 text-right">Quotes</th>
+                  <th className="px-1.5 py-1 text-right">Bytes</th>
+                  <th className="px-1.5 py-1">Coverage gaps</th>
+                  <th className="px-1.5 py-1 text-right">Fallback frac</th>
+                  <th className="px-1.5 py-1">Checksum</th>
+                  <th className="px-1.5 py-1">Split provenance</th>
+                  <th className="px-1.5 py-1">Exposure state</th>
+                </tr>
+              </thead>
+              <tbody data-testid="micro-readiness-shard-rows">
+                {readiness.shards.map((shard) => (
+                  <tr key={shard.dataset_id} className="border-b border-slate-900">
+                    <td className="px-1.5 py-1 text-slate-300">{shard.symbol}</td>
+                    <td className="px-1.5 py-1 font-mono text-slate-300">{shard.session_date}</td>
+                    <td className="px-1.5 py-1 text-slate-400">{shard.data_feed}</td>
+                    <td className="whitespace-nowrap px-1.5 py-1 font-mono text-slate-400">
+                      {formatDateTimeET(shard.window_start_utc, { seconds: false })}
+                      {" – "}
+                      {formatDateTimeET(shard.window_end_utc, { seconds: false })}
+                    </td>
+                    <td className="px-1.5 py-1 text-right font-mono text-slate-300">
+                      {shard.trade_count.toLocaleString()}
+                    </td>
+                    <td className="px-1.5 py-1 text-right font-mono text-slate-300">
+                      {shard.quote_count.toLocaleString()}
+                    </td>
+                    <td className="px-1.5 py-1 text-right font-mono text-slate-300">
+                      {shard.bytes.toLocaleString()}
+                    </td>
+                    <td className="px-1.5 py-1 text-amber-300">
+                      {shard.coverage_gaps.length === 0 ? (
+                        <span className="text-slate-500">none</span>
+                      ) : (
+                        shard.coverage_gaps.join("; ")
+                      )}
+                    </td>
+                    <td className="px-1.5 py-1 text-right font-mono text-slate-300">
+                      {shard.fallback_frac.toFixed(2)}
+                    </td>
+                    <td className="whitespace-nowrap px-1.5 py-1 font-mono text-[10px] text-slate-500">
+                      {shard.checksum}
+                    </td>
+                    <td className="px-1.5 py-1 text-slate-400">{shard.split_provenance}</td>
+                    <td className="px-1.5 py-1 text-slate-400">{shard.exposure_state}</td>
+                  </tr>
+                ))}
+              </tbody>
+            </table>
+          </div>
+        )}
+      </div>
+
+      <div data-testid="micro-readiness-floors-block" className="mb-4">
+        <h4 className="mb-2 text-xs font-semibold text-slate-400">Pilot-Study Floors</h4>
+        <div className="overflow-x-auto">
+          <table
+            data-testid="micro-readiness-floors-table"
+            className="w-full min-w-[560px] border-collapse text-xs"
+          >
+            <thead>
+              <tr className="border-b border-slate-800 text-left text-slate-500">
+                <th className="px-1.5 py-1">Study</th>
+                <th className="px-1.5 py-1">Floor</th>
+                <th className="px-1.5 py-1 text-right">Required sessions</th>
+                <th className="px-1.5 py-1 text-right">Available sessions</th>
+                <th className="px-1.5 py-1">Status</th>
+              </tr>
+            </thead>
+            <tbody data-testid="micro-readiness-floor-rows">
+              {readiness.study_floors.map((floor) => (
+                <tr key={floor.study_id} className="border-b border-slate-900">
+                  <td className="px-1.5 py-1 text-slate-300">{floor.study_id}</td>
+                  <td className="px-1.5 py-1 text-slate-400">{floor.floor_name}</td>
+                  <td className="px-1.5 py-1 text-right font-mono text-slate-300">
+                    {floor.required_sessions}
+                  </td>
+                  <td className="px-1.5 py-1 text-right font-mono text-slate-300">
+                    {floor.available_sessions}
+                  </td>
+                  <td
+                    className={
+                      floor.status === "floor_met"
+                        ? "px-1.5 py-1 text-emerald-400"
+                        : "px-1.5 py-1 text-amber-300"
+                    }
+                  >
+                    {floor.status}
+                  </td>
+                </tr>
+              ))}
+            </tbody>
+          </table>
+        </div>
+      </div>
+
+      {readiness.integrity_errors.length === 0 ? (
+        <EmptyState testid="micro-readiness-integrity-errors-empty" title="No integrity errors." />
+      ) : (
+        <ul
+          data-testid="micro-readiness-integrity-errors"
+          className="mt-2 space-y-0.5 text-[11px] text-red-300"
+        >
+          {readiness.integrity_errors.map((e) => (
+            <li key={e.file}>
+              {e.file}: {e.error}
+            </li>
+          ))}
+        </ul>
+      )}
+    </div>
+  );
+}
+
 // era-desk-iter-14 (J-10): a third compute control, wired exactly like `TopupComputeControl` — the
 // operation has no per-pair counters (it is a single classify-repair-verify walk, not a walk over
 // many pairs), so the running indicator shows the compute's own `progress.phase` label instead of
@@ -8686,6 +8912,16 @@ export default function DeskPage() {
     Record<string, RefereeComputeControlState>
   >({});
 
+  // goal-rapid-microscope-iter-1 (J-01): the Microscope Readiness section's own state -- a plain
+  // deferred read (no compute manager, T-8 -- "page-load GETs never compute"), the SAME shape
+  // every other read-only desk section's own result state already uses (e.g.
+  // refereeEvidenceResult immediately above).
+  const [microReadinessResult, setMicroReadinessResult] = useState<{
+    ok: boolean;
+    data: MicroReadinessResponse | null;
+    error?: string;
+  } | null>(null);
+
   // --- the six collapsed sections (see the DESK-COLLAPSED block at the top of this file) ---------
   // Which are currently open. A Set keyed by section, mirroring `PlaybookSummaryView`'s own
   // `expandedPools` — nothing outside this component reads it, and it is deliberately NOT
@@ -8742,6 +8978,8 @@ export default function DeskPage() {
       fetchRefereeRegistry().then(setRefereeRegistryResult);
       fetchRefereeNullRuns().then(setRefereeNullRunsResult);
       fetchRefereeEvaluateRuns().then(setRefereeEvaluateRunsResult);
+    } else if (section === "microReadiness") {
+      fetchMicroReadiness().then(setMicroReadinessResult);
     }
   }
 
@@ -10818,6 +11056,21 @@ export default function DeskPage() {
             />
           </CollapsibleSection>
         </section>
+
+        {/* goal-rapid-microscope-iter-1 (J-01): the Microscope Readiness section -- the era's
+            FIRST Rapid-Microscope section, rendered directly BELOW the shipped Referee Runs
+            section above (the current last section, T-11: new data-testids only, no shipped
+            data-testid or heading string reused anywhere else on this page). */}
+        <section aria-label="Microscope Readiness" className="mt-6">
+          <CollapsibleSection
+            id="microReadiness"
+            title="Microscope Readiness"
+            open={expandedSections.has("microReadiness")}
+            onToggle={() => toggleSection("microReadiness")}
+          >
+            <MicroReadinessSection readinessResult={microReadinessResult} />
+          </CollapsibleSection>
+        </section>
       </main>
     </div>
   );
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index fed8889..b4d44e4 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -38,6 +38,7 @@ import type {
   LevelsResponse,
   MarketClock,
   MergedCandlesPage,
+  MicroReadinessResponse,
   PnlLedger,
   ProfilesPayload,
   RecordBarSeriesResult,
@@ -2148,6 +2149,32 @@ export async function fetchRefereeEvidence(): Promise<{
   }
 }
 
+// GET /research/desk/micro/readiness -- goal-rapid-microscope-iter-1 (J-01): the era's FIRST
+// Rapid-Microscope route. Served VERBATIM -- zero client-side arithmetic on any numeric this
+// component reads (test_desk_ui_guards.py's widened _PRICE_ARITHMETIC_FIELDS covers every one).
+export async function fetchMicroReadiness(): Promise<{
+  ok: boolean;
+  data: MicroReadinessResponse | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/micro/readiness`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as MicroReadinessResponse };
+    }
+    let error = "The microscope readiness corpus could not be loaded.";
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
 // POST /research/desk/referee/registry/hypotheses — the real registration act (goal.md J-07 Step
 // 3): registers ONE hypothesis (through its family, create-if-absent) only when `confirm: true`.
 // The backend's 422 (malformed / unrecognised spec id / retroactive boundary) and 409 (duplicate
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 603f2be..55bf380 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -2474,3 +2474,46 @@ export interface RefereeEvidenceResponse {
   playbook_occurrence: RefereePlaybookOccurrenceReadiness;
   strategy_trade: RefereeStrategyTradeReadiness;
 }
+
+// GET /research/desk/micro/readiness -- goal-rapid-microscope-iter-1 (J-01): the era's first
+// served value, the corpus-truth surface every later Rapid-Microscope journey depends on. Served
+// verbatim -- see MicroReadinessSection in app/desk/page.tsx.
+export interface MicroReadinessTotals {
+  distinct_symbol_days: number;
+  distinct_datasets: number;
+  rth_minutes_covered: number;
+  session_equivalents: number;
+  referee_tick_gate_symbol_days: number;
+}
+
+export interface MicroReadinessShard {
+  dataset_id: string;
+  symbol: string;
+  session_date: string;
+  data_feed: string;
+  window_start_utc: string;
+  window_end_utc: string;
+  trade_count: number;
+  quote_count: number;
+  bytes: number;
+  coverage_gaps: string[];
+  fallback_frac: number;
+  checksum: string;
+  split_provenance: string;
+  exposure_state: string;
+}
+
+export interface MicroReadinessStudyFloor {
+  study_id: string;
+  floor_name: string;
+  required_sessions: number;
+  available_sessions: number;
+  status: string;
+}
+
+export interface MicroReadinessResponse {
+  totals: MicroReadinessTotals;
+  shards: MicroReadinessShard[];
+  study_floors: MicroReadinessStudyFloor[];
+  integrity_errors: { file: string; error: string }[];
+}
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/goal-session-rapid-microscope-index.html   | 11 +++++++----
 .../.engine.lock/epoch                             |  2 +-
 .../goal-session-rapid-microscope/.engine.lock/pid |  2 +-
 runs/goal-session-rapid-microscope/engine.pid      |  2 +-
 runs/goal-session-rapid-microscope/session.json    |  6 +++++-
 runs/goal-session-rapid-microscope/telemetry.jsonl | 22 ++++++++++++++++++++++
 .../trace/trace.jsonl                              |  1 +
 7 files changed, 38 insertions(+), 8 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
