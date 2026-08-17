# Iteration diff (bounded)

Files changed: 8. Shown in full: 7.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_micro_readiness.py` (47 lines not shown)

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
diff --git a/apps/backend/app/research/micro_readiness.py b/apps/backend/app/research/micro_readiness.py
new file mode 100644
index 0000000..bc7f58a
--- /dev/null
+++ b/apps/backend/app/research/micro_readiness.py
@@ -0,0 +1,367 @@
+"""``micro_readiness.py`` -- Era "The Rapid Microscope" J-01: the corpus-truth surface.
+
+THIS MODULE is the era's first served value (``docs/goal.md`` Key Capability 1, Data Contract
+row "Corpus readiness truth"): an honest, served-from-disk statement of what tick evidence
+actually exists today, and which of the three predeclared pilot-study floors it clears (none,
+honestly). It never fabricates, never re-derives a value another store already owns, and never
+computes at GET time beyond the one per-shard cost documented below.
+
+**Reads verbatim, never re-derives.** Every shard's ``checksum``/``trade_count``/``quote_count``/
+``data_feed``/``window_start_utc``/``window_end_utc`` is read straight off
+``DatasetStore.list()``'s own already-checksum-verified metadata -- this module performs no
+second parse of a dataset file's content and no second checksum. ``referee_tick_gate_symbol_days``
+is imported verbatim from ``referee_evidence.REFEREE_TICK_GATE_SYMBOL_DAYS`` (150) -- never a
+second hardcoded copy of the same gate (single-source-of-truth rail).
+
+**Two genuinely NEW per-shard computations, both cheap except one:**
+
+  * ``session_date``/``coverage_gaps``/``bytes`` -- cheap arithmetic over already-known window
+    bounds (an ET conversion, an interval overlap against the fixed 09:30-16:00 RTH window, a
+    ``stat()`` call) -- no event replay needed. Session dates are ET calendar dates
+    (``docs/rapid-validation-spec.md`` §0: "A session is an ET RTH trading date"); this module
+    owns a private ``ZoneInfo`` constant for that conversion, the SAME per-module idiom
+    ``referee_evidence.py`` documents ("each module that needs ET wall-clock resolution owns a
+    private ZoneInfo constant rather than reaching [into another module's private one]") --
+    ``desk_sessions.py`` is the arbiter of WHICH dates are known trading sessions (spec §0), but
+    its own ``_session_date`` is UTC-calendar and serves a different purpose (the exact
+    distinction ``referee_evidence.py`` itself draws), so it offers no ET conversion to reuse.
+
+  * ``fallback_frac`` -- THE one genuinely expensive per-shard computation: which fraction of a
+    shard's trades were classified via the Lee-Ready tick-test FALLBACK (``aggressor.py``'s Stage
+    2) rather than decided outright by the quote rule (Stage 1). ``classify_aggressor`` itself
+    does not expose which stage fired, and Stage 2's resolved side depends on state
+    (``prior_trade_price``/``last_tick_dir``) this metric does not need -- only WHETHER Stage 1
+    decided does, and that depends on nothing but the trade's price and the quote in effect
+    (``aggressor.py``'s own docstring, verbatim: "Stage 2 ... fires ONLY when stage 1 yields no
+    decision: no quote in effect, OR the print is strictly between bid and ask"). ``_quote_rule_
+    decides`` below mirrors exactly that documented precondition -- not a reimplementation of
+    hidden branching, but the one public boolean ``classify_aggressor`` does not itself return --
+    and ``tests/test_micro_readiness.py`` cross-validates it against ``classify_aggressor``'s own
+    observable behavior (never merely against a second copy of the same formula). Cached keyed on
+    the dataset's content ``checksum`` (``MicroReadinessCache``, below) -- the ``dataset_index.py``
+    derived/rebuildable precedent: losing the cache loses nothing, the next GET rebuilds it -- so
+    a repeat request never re-replays ~0.92 GB of tick events (T-8, "page-load GETs never
+    compute").
+
+**Corrupted files are surfaced, never dropped, never a crash.** ``DatasetStore.list()``'s own
+``errors`` half is served verbatim as ``integrity_errors``; every OTHER, healthy shard still
+appears in ``shards`` with every field populated, unaffected by the corrupted one.
+
+**The three pilot-study floors read one shared, frozen geometry constant.** No study-specific
+floor exists yet (J-09, the studies' own Scout registration, is eight iterations away) --
+``runs/goal-session-rapid-microscope/state/assumptions.md`` (iter-1, goal-decomposer) already
+records this as a reversible, gate-free reading: all three rows compare today's corpus-wide
+distinct session-date count against the SAME frozen walk-forward fold-geometry floor
+(``docs/rapid-validation-spec.md`` §1: ``WF_TRAIN_MIN_SESSIONS`` (40) + ``WF_TEST_MIN_SESSIONS``
+(20) = 60). Neither constant is owned by any module yet -- ``walkforward.py`` (J-05) becomes the
+canonical owner; this iteration transcribes the frozen spec values as the FIRST code
+representation of them (a future J-05 dev should import these two names from here, or supersede
+them, never mint a second, independently-valued copy)."""
+
+from __future__ import annotations
+
+import os
+import sqlite3
+from datetime import date, datetime, time, timezone
+from pathlib import Path
+from zoneinfo import ZoneInfo
+
+from ..providers.base import Event, QuoteEvent, TradeEvent
+from .datasets import DatasetStore
+from .referee_evidence import REFEREE_TICK_GATE_SYMBOL_DAYS
+
+__all__ = [
+    "WF_TRAIN_MIN_SESSIONS",
+    "WF_TEST_MIN_SESSIONS",
+    "PILOT_STUDY_IDS",
+    "SPLIT_PROVENANCE_HAND_ASSIGNED",
+    "EXPOSURE_STATE_EXPLORATORY",
+    "MicroReadinessCache",
+    "resolve_micro_readiness_cache_db_path",
+    "build_readiness",
+]
+
+# --- the frozen constants this iteration serves (see module docstring for provenance) ---------------
+
+# docs/rapid-validation-spec.md §1 -- transcribed verbatim, not invented (see module docstring).
+WF_TRAIN_MIN_SESSIONS = 40
+WF_TEST_MIN_SESSIONS = 20
+
+# The three studies goal.md J-09 predeclares, in its own stated priority order -- named here only
+# for the floor-comparison table; registering their actual Scout specs is J-09's work.
+PILOT_STUDY_IDS = (
+    "range_wall_failed_aggression",
+    "delta_divergence_level_tests",
+    "capitulation_exhaustion",
+)
+
+SPLIT_PROVENANCE_HAND_ASSIGNED = "hand_assigned"
+EXPOSURE_STATE_EXPLORATORY = "exploratory"
+
+_FLOOR_NAME = "wf_fold_geometry"
+_FLOOR_STATUS_MET = "floor_met"
+_FLOOR_STATUS_UNMET = "floor_unmet"
+
+# This module's own private ZoneInfo constant -- the referee_evidence.py per-module idiom (module
+# docstring). RTH bounds are the spec's own "09:30-16:00 ET" (docs/rapid-validation-spec.md, and
+# goal.md's Data-contract section, verbatim).
+_ET_ZONE = ZoneInfo("America/New_York")
+_RTH_OPEN = time(9, 30)
+_RTH_CLOSE = time(16, 0)
+_RTH_MINUTES_PER_SESSION = 390.0  # 16:00 - 09:30, the standard-session-equivalents denominator
+
+
+# --- session-date / RTH-coverage arithmetic (cheap; no event replay) --------------------------------
+
+
+def _et_datetime(iso_utc: str) -> datetime:
+    """A stored UTC ISO timestamp (``window_start_utc``/``window_end_utc``, possibly carrying
+    fractional seconds), converted to this module's own ET zone."""
+    parsed = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
+    if parsed.tzinfo is None:
+        parsed = parsed.replace(tzinfo=timezone.utc)
+    return parsed.astimezone(_ET_ZONE)
+
+
+def _fmt_et(value: datetime) -> str:
+    return value.strftime("%H:%M")
+
+
+def _rth_overlap(start_et: datetime, end_et: datetime, session_date: date) -> tuple[float, list[str]]:
+    """Minutes of ``[start_et, end_et)`` covered by ``session_date``'s 09:30-16:00 ET RTH window,
+    plus the honest coverage-gap sentence(s) -- ``[]`` when the window fully covers RTH end to
+    end; a single whole-session gap when the window does not overlap RTH at all."""
+    rth_open = datetime.combine(session_date, _RTH_OPEN, tzinfo=_ET_ZONE)
+    rth_close = datetime.combine(session_date, _RTH_CLOSE, tzinfo=_ET_ZONE)
+    overlap_start = max(start_et, rth_open)
+    overlap_end = min(end_et, rth_close)
+    if overlap_start >= overlap_end:
+        return 0.0, [f"{_fmt_et(rth_open)}–{_fmt_et(rth_close)} ET not covered"]
+    minutes = (overlap_end - overlap_start).total_seconds() / 60.0
+    gaps: list[str] = []
+    if overlap_start > rth_open:
+        gaps.append(f"{_fmt_et(rth_open)}–{_fmt_et(overlap_start)} ET not covered")
+    if overlap_end < rth_close:
+        gaps.append(f"{_fmt_et(overlap_end)}–{_fmt_et(rth_close)} ET not covered")
+    return minutes, gaps
+
+
+# --- fallback_frac: the one expensive per-shard computation, plus its checksum-keyed cache ----------
+
+
+def _quote_rule_decides(trade: TradeEvent, quote: QuoteEvent | None) -> bool:
+    """Whether ``aggressor.classify_aggressor``'s Stage 1 (the quote rule) decides this trade --
+    mirrors that function's own documented precondition verbatim (module docstring); the ONLY
+    factor is the trade's price against the quote in effect, independent of any prior-trade
+    state. ``False`` means Stage 2 (the Lee-Ready tick-test fallback) fires."""
+    return quote is not None and (trade.price >= quote.ask or trade.price <= quote.bid)
+
+
+def _compute_fallback_frac(events: list[Event]) -> float:
+    """The fraction of a shard's trades classified via the Stage-2 fallback rather than the
+    Stage-1 quote rule -- a single linear scan carrying forward the most recently seen quote (the
+    ONLY state ``_quote_rule_decides`` reads), exactly the state ``TapeEngine.process_event``
+    itself carries at the instant it classifies a trade (module docstring). A shard with zero
+    trades reads ``0.0`` (never a division by zero, never fabricated)."""
+    current_quote: QuoteEvent | None = None
+    total_trades = 0
+    fallback_trades = 0
+    for event in events:
+        if isinstance(event, QuoteEvent):
+            current_quote = event
+            continue
+        total_trades += 1
+        if not _quote_rule_decides(event, current_quote):
+            fallback_trades += 1
+    if total_trades == 0:
+        return 0.0
+    return fallback_trades / total_trades
+
+
+# Mirrors every sibling durable cache's identical brief writer-contention tolerance
+# (tradability_cache.py/dataset_index.py's own constant).
+_BUSY_TIMEOUT_MS = 5000
+
+_SCHEMA = """
+CREATE TABLE IF NOT EXISTS micro_fallback_frac_cache (
+    checksum       TEXT PRIMARY KEY,
+    fallback_frac  REAL NOT NULL,
+    created_utc    TEXT NOT NULL
+)
+"""
+
+# Deliberately its own env var, distinct from every sibling durable cache's (Constraints:
+# "storage dirs are env-var-or-sibling defaults -- the TAPEOLOGY_MICRO_* family").
+_CACHE_DB_ENV = "TAPEOLOGY_MICRO_READINESS_CACHE_DB"
+
+
+def _iso_utc_now() -> str:
+    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
+
+
+def resolve_micro_readiness_cache_db_path(dataset_dir: str) -> str:
+    """The cache DB path resolution policy -- the ``resolve_tradability_cache_db_path`` env-else-
+    sibling shape: ``TAPEOLOGY_MICRO_READINESS_CACHE_DB`` if set, else ``micro_readiness_cache.db``
+    co-located as a SIBLING of the caller's dataset-store directory (e.g. ``.data/datasets`` ->
+    ``.data/micro_readiness_cache.db``)."""
+    override = os.environ.get(_CACHE_DB_ENV)
+    if override:
+        return override
+    return str(Path(dataset_dir).parent / "micro_readiness_cache.db")
+
+
+class MicroReadinessCache:
+    """One durable SQLite row per dataset content ``checksum`` -> its ``fallback_frac`` --
+    ``TradabilityCache``'s "rebuildable result only, owns nothing" contract (see that module's own
+    docstring for the full discipline), applied to a single-float value instead of a whole map. A
+    miss NEVER computes -- ``lookup`` has no ``compute_fn``, mechanically incapable of running the
+    replay; a corrupted/unreadable DB is a full miss, never a crash; a ``publish`` failure is
+    swallowed, never propagated -- the caller is still holding its own freshly-computed value."""
+
+    def __init__(self, db_path: str) -> None:
+        self._db_path = str(db_path)
+        if self._db_path != ":memory:":
+            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
+        try:
+            conn = self._connect()
+            try:
+                with conn:
+                    conn.execute(_SCHEMA)
+            finally:
+                conn.close()
+        except sqlite3.Error:
+            pass  # self-heals: every subsequent lookup/publish independently re-attempts
+
+    @property
+    def db_path(self) -> str:
+        return self._db_path
+
+    def _connect(self) -> sqlite3.Connection:
+        """A FRESH, short-lived connection per call (the ``TradabilityCache._connect`` precedent)."""
+        conn = sqlite3.connect(
+            self._db_path, check_same_thread=False, timeout=_BUSY_TIMEOUT_MS / 1000.0
+        )
+        conn.row_factory = sqlite3.Row
+        if self._db_path != ":memory:":
+            conn.execute("PRAGMA journal_mode=WAL")
+        conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
+        return conn
+
+    def lookup(self, checksum: str) -> float | None:
+        try:
+            conn = self._connect()
+            try:
+                row = conn.execute(
+                    "SELECT fallback_frac FROM micro_fallback_frac_cache WHERE checksum=?",
+                    (checksum,),
+                ).fetchone()
+            finally:
+                conn.close()
+        except sqlite3.Error:
+            return None
+        return None if row is None else float(row["fallback_frac"])
+
+    def publish(self, checksum: str, fallback_frac: float) -> None:
+        try:
+            conn = self._connect()
+            try:
+                with conn:
+                    conn.execute(
+                        "INSERT OR REPLACE INTO micro_fallback_frac_cache "
+                        "(checksum, fallback_frac, created_utc) VALUES (?,?,?)",
+                        (checksum, fallback_frac, _iso_utc_now()),
+                    )
+            finally:
+                conn.close()
+        except sqlite3.Error:
+            pass
+
+
+# --- the whole readiness aggregation -----------------------------------------------------------------
+
+
+def build_readiness(store: DatasetStore, cache: MicroReadinessCache, *, dataset_dir: str) -> dict:
+    """The whole ``GET /research/desk/micro/readiness`` body -- a pure aggregation over
+    ``DatasetStore.list()``'s already-verified records (module docstring). Deterministic and
+    byte-reproducible: an unchanged store + a warm cache yields a byte-identical response on
+    every call (TC-7) -- nothing here reads the wall clock into the served shape (the cache's own
+    ``created_utc`` never leaves the cache)."""
+    records, errors = store.list()
+    root = Path(dataset_dir)
+
+    shards: list[dict] = []
+    symbol_days: set[tuple[str, str]] = set()
+    session_dates: set[str] = set()
+    rth_minutes_total = 0.0
+
+    for meta in records:
+        start_et = _et_datetime(meta["window_start_utc"])
+        end_et = _et_datetime(meta["window_end_utc"])
+        session_date = start_et.date()
+        session_date_str = session_date.isoformat()
+        minutes, gaps = _rth_overlap(start_et, end_et, session_date)
+        rth_minutes_total += minutes
+        symbol_days.add((meta["symbol"], session_date_str))
+        session_dates.add(session_date_str)
+
+        checksum = meta["checksum"]
+        fallback_frac = cache.lookup(checksum)
+        if fallback_frac is None:
+            events = store.load_events(meta["id"])
+            fallback_frac = _compute_fallback_frac(events)
+            cache.publish(checksum, fallback_frac)
+
+        try:
+            shard_bytes = (root / f"{meta['id']}.json").stat().st_size
+        except OSError:
+            # Honest zero on a file removed between store.list()'s own verify and this stat --
+            # never a crash, and store.list() already proved the metadata itself is trustworthy.
+            shard_bytes = 0
+
+        shards.append(
+            {
+                "dataset_id": meta["id"],
+                "symbol": meta["symbol"],
+                "session_date": session_date_str,
+                "data_feed": meta["data_feed"],
+                "window_start_utc": meta["window_start_utc"],
+                "window_end_utc": meta["window_end_utc"],
+                "trade_count": meta["event_counts"]["trades"],
+                "quote_count": meta["event_counts"]["quotes"],
+                "bytes": shard_bytes,
+                "coverage_gaps": gaps,
+                "fallback_frac": fallback_frac,
+                "checksum": checksum,
+                "split_provenance": SPLIT_PROVENANCE_HAND_ASSIGNED,
+                "exposure_state": EXPOSURE_STATE_EXPLORATORY,
+            }
+        )
+
+    available_sessions = len(session_dates)
+    required_sessions = WF_TRAIN_MIN_SESSIONS + WF_TEST_MIN_SESSIONS
+    floor_status = _FLOOR_STATUS_MET if available_sessions >= required_sessions else _FLOOR_STATUS_UNMET
+    study_floors = [
+        {
+            "study_id": study_id,
+            "floor_name": _FLOOR_NAME,
+            "required_sessions": required_sessions,
+            "available_sessions": available_sessions,
+            "status": floor_status,
+        }
+        for study_id in PILOT_STUDY_IDS
+    ]
+
+    totals = {
+        "distinct_symbol_days": len(symbol_days),
+        "distinct_datasets": len(records),
+        "rth_minutes_covered": round(rth_minutes_total, 2),
+        "session_equivalents": round(rth_minutes_total / _RTH_MINUTES_PER_SESSION, 4),
+        "referee_tick_gate_symbol_days": REFEREE_TICK_GATE_SYMBOL_DAYS,
+    }
+
+    return {
+        "totals": totals,
+        "shards": shards,
+        "study_floors": study_floors,
+        "integrity_errors": errors,
+    }
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
new file mode 100644
index 0000000..b5d34af
--- /dev/null
+++ b/apps/backend/app/research/micro_routes.py
@@ -0,0 +1,52 @@
+"""``/research/desk/micro/*`` -- Era "The Rapid Microscope": J-01's readiness fold, the era's
+first route. A fresh router/file mounted separately in ``main.py``, mirroring
+``referee_routes.py``'s own precedent and rationale (that file's own docstring: "the SAME
+rationale desk_routes.py itself gives for splitting off routes.py"). The era's own Data Contract
+table (``docs/goal.md``'s Product Shape) names six MORE micro routes landing in later iterations
+(snapshots, scout, walkforward, vault, recorder, graduation) under this SAME
+``/research/desk/micro`` prefix -- a dedicated file is the right home from the start.
+
+Depends on a store this route does NOT own: the dataset store dependency is imported verbatim
+from ``routes.get_dataset_store`` (never a second, redefined provider). The readiness cache is
+this module's OWN wiring (the ``referee_routes.py`` precedent: "this module owns its own wiring
+end to end") -- a config-derived, env-overridable path exactly like every sibling durable cache's
+own FastAPI dependency (``get_edge_report_cache``/``get_bar_index`` in ``routes.py``).
+
+``GET /readiness`` is a plain read: it triggers nothing but the readiness fold's own documented
+one-time-then-cached per-shard classification (page-load GETs never compute a SECOND time, T-8;
+the module itself is the ONE place, this route only wires it)."""
+
+from __future__ import annotations
+
+from fastapi import APIRouter, Depends
+
+from ..config import CONFIG
+from .datasets import DatasetStore
+from .micro_readiness import MicroReadinessCache, build_readiness, resolve_micro_readiness_cache_db_path
+from .routes import get_dataset_store
+
+router = APIRouter(prefix="/research/desk/micro", tags=["micro"])
+
+
+def get_micro_readiness_cache() -> MicroReadinessCache:
+    """The durable ``fallback_frac`` cache -- a config-DERIVED, env-overridable path so
+    ``config.py`` stays byte-identical (``config_fingerprint`` unaffected -- the
+    ``get_edge_report_cache``/``get_bar_index`` rationale, reused verbatim): the
+    ``TAPEOLOGY_MICRO_READINESS_CACHE_DB`` env var if set, else a file co-located as a SIBLING of
+    the config-owned dataset directory. A FastAPI dependency so tests can override it outright or
+    point it at a temp path via the env var -- the established pattern."""
+    return MicroReadinessCache(resolve_micro_readiness_cache_db_path(CONFIG.dataset_dir_resolved()))
+
+
+@router.get("/readiness")
+def get_micro_readiness(
+    dataset_store: DatasetStore = Depends(get_dataset_store),
+    cache: MicroReadinessCache = Depends(get_micro_readiness_cache),
+) -> dict:
+    """J-01's corpus-truth fold: the honest per-shard inventory, corpus totals beside the
+    referee's tick-gate figure, and the three pilot studies' floor table -- see
+    ``micro_readiness.build_readiness``'s own docstring for the full contract. Never 404/500 on
+    an empty corpus (the desk router's established never-404-on-absence convention) -- an empty
+    ``shards`` list (``study_floors`` still carries its 3 rows, each read against a 0-session
+    corpus) at HTTP 200."""
+    return build_readiness(dataset_store, cache, dataset_dir=CONFIG.dataset_dir_resolved())
diff --git a/apps/backend/tests/test_micro_readiness.py b/apps/backend/tests/test_micro_readiness.py
new file mode 100644
index 0000000..80c6acc
--- /dev/null
+++ b/apps/backend/tests/test_micro_readiness.py
@@ -0,0 +1,441 @@
+"""``micro_readiness.py`` + ``GET /research/desk/micro/readiness`` (Era "The Rapid Microscope",
+J-01) -- the corpus-truth fold. Test-first contract: TC-1 through TC-7 in
+``docs/phases/goal-rapid-microscope-iter-1.md``.
+
+The real-corpus tests (TC-1 through TC-5) run against the ACTUAL committed 18-dataset legacy tick
+corpus at ``apps/backend/.data/datasets`` -- the acceptance values ARE the real 18-dataset/
+12-symbol-day counts, and a fixture cannot substitute for this check (the phase spec's own
+TESTING REQUIREMENTS). They share ONE module-scoped ``real_readiness`` fixture (the per-shard
+``fallback_frac`` classification is genuinely expensive over ~0.92 GB of real tick events) so the
+cost is paid once for the whole file. Every OTHER test builds its own small, hermetic,
+``tmp_path``-scoped ``DatasetStore`` (never the real corpus) -- the ``test_referee_evidence.py``
+"hand-crafted records through the store's own public write path" precedent."""
+
+from __future__ import annotations
+
+import json
+from datetime import date, datetime
+from zoneinfo import ZoneInfo
+
+import pytest
+from fastapi.testclient import TestClient
+
+from app.config import CONFIG
+from app.main import app
+from app.engine.aggressor import classify_aggressor
+from app.providers.base import QuoteEvent, Side, TradeEvent
+from app.research import micro_readiness as micro_readiness_module
+from app.research.datasets import DatasetStore
+from app.research.micro_readiness import (
+    EXPOSURE_STATE_EXPLORATORY,
+    PILOT_STUDY_IDS,
+    SPLIT_PROVENANCE_HAND_ASSIGNED,
+    WF_TEST_MIN_SESSIONS,
+    WF_TRAIN_MIN_SESSIONS,
+    MicroReadinessCache,
+    build_readiness,
+    resolve_micro_readiness_cache_db_path,
+)
+from app.research.micro_routes import get_micro_readiness_cache
+from app.research.referee_evidence import REFEREE_TICK_GATE_SYMBOL_DAYS
+from app.research.routes import get_dataset_store
+
+_ET = ZoneInfo("America/New_York")
+
+
+# --- fixture builders (the store's own public write path -- never a hand-typed file) ---------------
+
+
+def _events(symbol: str) -> list:
+    """One quote followed by three trades spanning every `_quote_rule_decides` branch (a Stage-1
+    BUY, a Stage-1 SELL, and one strictly-between-bid-ask fallback) -- never all-decided or
+    all-fallback, so a fixture's own `fallback_frac` is a genuine, non-degenerate fraction."""
+    return [
+        QuoteEvent(symbol, 0.0, 99.99, 100.02, 100, 100),
+        TradeEvent(symbol, 0.1, 100.03, 10, Side.BUY),  # >= ask -> Stage 1
+        TradeEvent(symbol, 0.2, 100.00, 10, Side.BUY),  # strictly between -> fallback
+        TradeEvent(symbol, 0.3, 99.99, 10, Side.SELL),  # <= bid -> Stage 1
+    ]
+
+
+def _plant_dataset(
+    store: DatasetStore,
+    *,
+    symbol: str,
+    split: str = "train",
+    window_start_utc: str = "2026-06-09T13:00:00Z",
+    window_end_utc: str = "2026-06-09T13:01:00Z",
+) -> dict:
+    return store.record(
+        symbol=symbol,
+        source="fixture",
+        source_kind="fixture",
+        source_id=f"{symbol}-fixture",
+        split=split,
+        window_start_utc=window_start_utc,
+        window_end_utc=window_end_utc,
+        data_feed="sip",
+        epoch_anchor=0.0,
+        events=_events(symbol),
+    )
+
+
+@pytest.fixture
+def client(tmp_path):
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
+    app.dependency_overrides[get_dataset_store] = lambda: dataset_store
+    app.dependency_overrides[get_micro_readiness_cache] = lambda: cache
+    with TestClient(app) as c:
+        yield c, dataset_store, cache
+    app.dependency_overrides.pop(get_dataset_store, None)
+    app.dependency_overrides.pop(get_micro_readiness_cache, None)
+
+
+# --- _quote_rule_decides: cross-validated against classify_aggressor's own OBSERVABLE behavior ------
+#
+# classify_aggressor itself never exposes which stage decided a trade. The oracle below is
+# independent of _quote_rule_decides' own formula: with prior_trade_price AND last_tick_dir both
+# None, Stage 2 is STRUCTURALLY forced to Side.UNKNOWN (aggressor.py's own documented rule -- "no
+# quote AND no prior trade" is the one undecidable case) -- so
+# "classify_aggressor(...) is not Side.UNKNOWN" is a reliable, independent ground truth for
+# "Stage 1 decided" in this specific probe, never a second copy of the same two-line condition.
+
+
+@pytest.mark.parametrize(
+    "price,bid,ask,expected_stage1",
+    [
+        (100.03, 99.99, 100.02, True),  # price >= ask -> Stage 1 BUY
+        (100.02, 99.99, 100.02, True),  # price == ask -> Stage 1 BUY (>=)
+        (99.99, 99.99, 100.02, True),  # price == bid -> Stage 1 SELL (<=)
+        (99.98, 99.99, 100.02, True),  # price < bid -> Stage 1 SELL
+        (100.01, 99.99, 100.02, False),  # strictly between -> Stage 1 does not decide
+        (100.005, 99.99, 100.02, False),  # strictly between -> Stage 1 does not decide
+    ],
+)
+def test_quote_rule_decides_matches_classify_aggressor_with_no_prior_trade(
+    price, bid, ask, expected_stage1
+):
+    quote = QuoteEvent("AAPL", 0.0, bid, ask, 100, 100)
+    trade = TradeEvent("AAPL", 0.0, price, 10, Side.BUY)
+    mirrored = micro_readiness_module._quote_rule_decides(trade, quote)
+    assert mirrored is expected_stage1
+    result = classify_aggressor(trade, quote, prior_trade_price=None, last_tick_dir=None)
+    assert mirrored == (result is not Side.UNKNOWN)
+
+
+def test_quote_rule_decides_is_false_with_no_quote_in_effect():
+    trade = TradeEvent("AAPL", 0.0, 100.0, 10, Side.BUY)
+    assert micro_readiness_module._quote_rule_decides(trade, None) is False
+    assert classify_aggressor(trade, None, None, None) is Side.UNKNOWN
+
+
+# --- _compute_fallback_frac: hand-computed over a small event list ----------------------------------
+
+
+def test_compute_fallback_frac_hand_computed():
+    # 3 trades: BUY@100.03 (Stage 1), BUY@100.00 (fallback), SELL@99.99 (Stage 1) -> 1/3 fallback.
+    events = _events("AAPL")
+    assert micro_readiness_module._compute_fallback_frac(events) == pytest.approx(1.0 / 3.0)
+
+
+def test_compute_fallback_frac_no_trades_is_zero():
+    events = [QuoteEvent("AAPL", 0.0, 99.99, 100.02, 100, 100)]
+    assert micro_readiness_module._compute_fallback_frac(events) == 0.0
+
+
+def test_compute_fallback_frac_before_any_quote_is_always_fallback():
+    events = [TradeEvent("AAPL", 0.0, 100.0, 10, Side.BUY)]
+    assert micro_readiness_module._compute_fallback_frac(events) == 1.0
+
+
+# --- _rth_overlap: cheap RTH-coverage arithmetic, hand-computed (locks in the real corpus's own
+#     shapes: a window starting before open, one starting after close, one strictly inside RTH,
+#     one with zero overlap, and one that exactly covers the session end to end) -------------------
+
+
+def test_rth_overlap_window_starts_before_open_ends_before_close():
+    start = datetime(2026, 6, 22, 8, 30, tzinfo=_ET)
+    end = datetime(2026, 6, 22, 11, 0, tzinfo=_ET)
+    minutes, gaps = micro_readiness_module._rth_overlap(start, end, date(2026, 6, 22))
+    assert minutes == 90.0
+    assert gaps == ["11:00–16:00 ET not covered"]
+
+
+def test_rth_overlap_window_starts_after_open_ends_after_close():
+    start = datetime(2026, 5, 27, 14, 0, tzinfo=_ET)
+    end = datetime(2026, 5, 27, 16, 30, tzinfo=_ET)
+    minutes, gaps = micro_readiness_module._rth_overlap(start, end, date(2026, 5, 27))
+    assert minutes == 120.0
+    assert gaps == ["09:30–14:00 ET not covered"]
+
+
+def test_rth_overlap_window_strictly_inside_rth_has_two_gaps():
+    start = datetime(2026, 6, 26, 10, 25, tzinfo=_ET)
+    end = datetime(2026, 6, 26, 12, 55, tzinfo=_ET)
+    minutes, gaps = micro_readiness_module._rth_overlap(start, end, date(2026, 6, 26))
+    assert minutes == 150.0
+    assert gaps == ["09:30–10:25 ET not covered", "12:55–16:00 ET not covered"]
+
+
+def test_rth_overlap_window_entirely_outside_rth_is_one_whole_session_gap():
+    start = datetime(2026, 6, 1, 20, 0, tzinfo=_ET)
+    end = datetime(2026, 6, 1, 21, 0, tzinfo=_ET)
+    minutes, gaps = micro_readiness_module._rth_overlap(start, end, date(2026, 6, 1))
+    assert minutes == 0.0
+    assert gaps == ["09:30–16:00 ET not covered"]
+
+
+def test_rth_overlap_window_exactly_covers_rth_has_no_gaps():
+    start = datetime(2026, 6, 1, 9, 30, tzinfo=_ET)
+    end = datetime(2026, 6, 1, 16, 0, tzinfo=_ET)
+    minutes, gaps = micro_readiness_module._rth_overlap(start, end, date(2026, 6, 1))
+    assert minutes == 390.0
+    assert gaps == []
+
+
+def test_et_datetime_converts_a_utc_iso_timestamp_with_microseconds():
+    # 2026-06-09T17:00:00.002286Z is EDT (UTC-4) -> 13:00:00.002286 ET, same calendar date.
+    result = micro_readiness_module._et_datetime("2026-06-09T17:00:00.002286Z")
+    assert (result.hour, result.minute) == (13, 0)
+    assert result.date().isoformat() == "2026-06-09"
+
+
+# --- resolve_micro_readiness_cache_db_path: env-else-sibling-of-dataset-dir -------------------------
+
+
+def test_resolve_defaults_to_a_sibling_of_the_dataset_dir(tmp_path, monkeypatch):
+    monkeypatch.delenv("TAPEOLOGY_MICRO_READINESS_CACHE_DB", raising=False)
+    assert resolve_micro_readiness_cache_db_path(str(tmp_path / "datasets")) == str(
+        tmp_path / "micro_readiness_cache.db"
+    )
+
+
+def test_resolve_honors_the_env_override(tmp_path, monkeypatch):
+    override = str(tmp_path / "elsewhere" / "cache.db")
+    monkeypatch.setenv("TAPEOLOGY_MICRO_READINESS_CACHE_DB", override)
+    assert resolve_micro_readiness_cache_db_path(str(tmp_path / "datasets")) == override
+
+
+# --- MicroReadinessCache: lookup/publish round trip --------------------------------------------------
+
+
+def test_cache_lookup_is_none_on_a_genuine_miss(tmp_path):
+    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
+    assert cache.lookup("no-such-checksum") is None
+
+
+def test_cache_publish_then_lookup_round_trips(tmp_path):
+    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
+    cache.publish("checksum-a", 0.42)
+    assert cache.lookup("checksum-a") == 0.42
+
+
+def test_cache_survives_a_corrupted_db_file_as_a_full_miss(tmp_path):
+    db_path = tmp_path / "cache.db"
+    db_path.write_text("not a sqlite file")
+    cache = MicroReadinessCache(str(db_path))
+    assert cache.lookup("anything") is None
+    cache.publish("anything", 0.5)  # swallowed, never raises
+
+
+# --- TC-6: a hand-corrupted legacy dataset is surfaced, never dropped, never a crash -----------------
+
+
+def test_corrupted_dataset_is_surfaced_never_dropped_never_a_crash(tmp_path):
+    store = DatasetStore(tmp_path / "datasets")
+    healthy = _plant_dataset(store, symbol="AAPL")
+    corrupted = _plant_dataset(
+        store, symbol="MSFT", window_start_utc="2026-06-10T13:00:00Z", window_end_utc="2026-06-10T13:01:00Z"
+    )
+    path = tmp_path / "datasets" / f"{corrupted['id']}.json"
+    payload = json.loads(path.read_text())
+    payload["record"]["meta"]["checksum"] = "deadbeef" * 8
+    path.write_text(json.dumps(payload))
+
+    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
+    result = build_readiness(store, cache, dataset_dir=str(tmp_path / "datasets"))
+
+    assert len(result["integrity_errors"]) == 1
+    assert result["integrity_errors"][0]["file"] == f"{corrupted['id']}.json"
+
+    assert result["totals"]["distinct_datasets"] == 1
+    assert [s["dataset_id"] for s in result["shards"]] == [healthy["id"]]
+    shard = result["shards"][0]
+    assert shard["symbol"] == "AAPL"
+    assert shard["checksum"] == healthy["checksum"]
+    assert shard["trade_count"] == healthy["event_counts"]["trades"]
+    assert shard["quote_count"] == healthy["event_counts"]["quotes"]
+    assert 0.0 <= shard["fallback_frac"] <= 1.0
+    assert shard["split_provenance"] == SPLIT_PROVENANCE_HAND_ASSIGNED
+    assert shard["exposure_state"] == EXPOSURE_STATE_EXPLORATORY
+
+
+def test_corrupted_dataset_surfaces_through_the_route_too(client, tmp_path):
+    c, store, _cache = client
+    healthy = _plant_dataset(store, symbol="AAPL")
+    corrupted = _plant_dataset(
+        store, symbol="MSFT", window_start_utc="2026-06-10T13:00:00Z", window_end_utc="2026-06-10T13:01:00Z"
+    )
+    # `tmp_path` resolves to the SAME directory the `client` fixture built `store` from (pytest
+    # caches a function-scoped fixture once per test call and shares it across every consumer).
+    path = tmp_path / "datasets" / f"{corrupted['id']}.json"
+    payload = json.loads(path.read_text())
+    payload["record"]["meta"]["checksum"] = "deadbeef" * 8
+    path.write_text(json.dumps(payload))
+
+    resp = c.get("/research/desk/micro/readiness")
+    assert resp.status_code == 200
+    body = resp.json()
+    assert len(body["integrity_errors"]) == 1
+    assert [s["dataset_id"] for s in body["shards"]] == [healthy["id"]]
+
+
+# --- TC-7: a repeat call/GET never re-classifies, and the response is byte-identical ----------------
+
+
+def test_repeat_build_readiness_call_does_not_reclassify(tmp_path, monkeypatch):
+    store = DatasetStore(tmp_path / "datasets")
+    _plant_dataset(store, symbol="AAPL")
+    cache = MicroReadinessCache(str(tmp_path / "cache.db"))
+    dataset_dir = str(tmp_path / "datasets")
+
+    call_count = {"n": 0}
+    original = micro_readiness_module._compute_fallback_frac
+
+    def _spy(events):
+        call_count["n"] += 1
+        return original(events)
+
+    monkeypatch.setattr(micro_readiness_module, "_compute_fallback_frac", _spy)
+
+    first = build_readiness(store, cache, dataset_dir=dataset_dir)
+    assert call_count["n"] == 1
+    second = build_readiness(store, cache, dataset_dir=dataset_dir)
+    assert call_count["n"] == 1  # served from cache -- no second replay
+    assert second == first
+
+
+def test_repeat_get_does_not_reclassify_and_response_bytes_are_identical(client, monkeypatch):
+    c, store, _cache = client
+    _plant_dataset(store, symbol="AAPL")
+
+    call_count = {"n": 0}
+    original = micro_readiness_module._compute_fallback_frac
+
+    def _spy(events):
+        call_count["n"] += 1
+        return original(events)
+
+    monkeypatch.setattr(micro_readiness_module, "_compute_fallback_frac", _spy)
+
+    first = c.get("/research/desk/micro/readiness")
+    second = c.get("/research/desk/micro/readiness")
+    assert call_count["n"] == 1
+    assert first.status_code == 200 and second.status_code == 200
+    assert first.content == second.content
+
+
+# --- the honest zero-corpus case: still HTTP 200, study_floors still 3 rows -------------------------
+
+
+def test_zero_corpus_is_an_honest_200_with_three_unmet_floor_rows(client):
+    c, _store, _cache = client
+    resp = c.get("/research/desk/micro/readiness")
+    assert resp.status_code == 200
+    body = resp.json()
+    assert body["totals"]["distinct_symbol_days"] == 0
+    assert body["totals"]["distinct_datasets"] == 0
+    assert body["totals"]["rth_minutes_covered"] == 0.0
+    assert body["totals"]["session_equivalents"] == 0.0
+    assert body["shards"] == []
+    assert body["integrity_errors"] == []
+    assert len(body["study_floors"]) == 3
+    assert {f["study_id"] for f in body["study_floors"]} == set(PILOT_STUDY_IDS)
+    for floor in body["study_floors"]:
+        assert floor["required_sessions"] == WF_TRAIN_MIN_SESSIONS + WF_TEST_MIN_SESSIONS == 60
+        assert floor["available_sessions"] == 0
+        assert floor["status"] == "floor_unmet"
+
+
+# --- TC-1 through TC-5: the REAL 18-dataset / 12-symbol-day legacy corpus ---------------------------
+#
+# Module-scoped -- the per-shard fallback_frac classification over the real corpus (~0.92 GB of
+# tick events) is genuinely expensive; every TC below shares ONE computed response.
+
+
+@pytest.fixture(scope="module")
+def real_readiness(tmp_path_factory):
+    # CONFIG.dataset_dir (never `_resolved()`) is the un-overridden package default -- the
+    # committed real corpus, independent of any ambient TAPEOLOGY_DATASET_DIR the environment
+    # might carry.
+    dataset_dir = CONFIG.dataset_dir
+    store = DatasetStore(dataset_dir)
+    cache_dir = tmp_path_factory.mktemp("micro_readiness_real_cache")
+    cache = MicroReadinessCache(str(cache_dir / "cache.db"))
+    return build_readiness(store, cache, dataset_dir=dataset_dir)
+
+
+@pytest.fixture(scope="module")
+def real_dataset_records():
+    store = DatasetStore(CONFIG.dataset_dir)
+    records, errors = store.list()
+    assert errors == []  # the committed corpus is healthy -- a real integrity error here would
+    # be a repo-hygiene regression, not something this iteration's tests should silently paper
+    # over.
+    return {record["id"]: record for record in records}
+
+
+def test_tc1_real_corpus_distinct_symbol_days_and_datasets(real_readiness):
+    assert real_readiness["totals"]["distinct_symbol_days"] == 12
+    assert real_readiness["totals"]["distinct_datasets"] == 18
+    assert len(real_readiness["shards"]) == 18
+    assert real_readiness["integrity_errors"] == []
+
... [diff_bound] apps/backend/tests/test_micro_readiness.py: 47 more diff lines omitted — Read the file for full detail
```
