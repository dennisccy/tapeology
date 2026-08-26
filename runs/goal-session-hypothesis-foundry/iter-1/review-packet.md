# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

```diff
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index 9ffad11d..c912ab05 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -46,6 +46,11 @@ from .desk_playbook import PlaybookStore
 from .desk_playbook_context import BandMapResolver
 from .desk_routes import get_playbook_store, get_universe_store
 from .desk_universe import UniverseStore
+from .foundry_source_registry import (
+    foundry_era_identity,
+    read_era_open_baseline,
+    resolve_foundry_dir,
+)
 from .micro_accessor import ExposureRegistry, resolve_micro_exposure_registry_dir
 from .micro_graduation import EMPTY_LEDGER_MESSAGE, GraduationLedger, list_graduation_families, resolve_micro_graduation_dir
 from .micro_readiness import (
@@ -729,3 +734,41 @@ def get_graduation(graduation_dir: str = Depends(get_micro_graduation_dir)) -> d
         "message": None if families else EMPTY_LEDGER_MESSAGE,
         "chain_verification": ledger.verify_chain(),
     }
+
+
+# --- Era "The Hypothesis Foundry" -- J-01: the panel header (era identity + era-open baseline) --
+# GET-only this iteration, exactly like every sibling route above (T-8: page-load GETs never
+# compute). This route's OWN scope this iteration (goal-hypothesis-foundry-iter-1) is deliberately
+# narrow: era/session identity, the Foundry methodology spec version, and the era-open baseline
+# block -- see `docs/phases/goal-hypothesis-foundry-iter-1.md` IN SCOPE. `source_registry_hash`
+# renders `null` with an explicit `not_yet_generated` status (goal.md: "the real registry does not
+# exist until Binding Execution Order step 6 / J-06") -- never a fabricated placeholder hash. The
+# CandidateSpec/compiler machinery this iteration DOES build (`foundry_source_registry.py`/
+# `foundry_compiler.py`) is proven hermetically by its own test suite and is NOT yet served here --
+# the consolidated Foundry read surface (Sources/Compiler and every other subview) is a later,
+# single iteration per the goal's own Binding Execution Order step 5 (state/assumptions.md's
+# iter-1 entry).
+
+
+def get_foundry_dir() -> str:
+    """The era-open baseline snapshot's storage directory -- ``TAPEOLOGY_FOUNDRY_DIR`` if set,
+    else a ``foundry`` SIBLING of the config-owned dataset directory
+    (``foundry_source_registry.resolve_foundry_dir`` -- see that function's own docstring)."""
+    return resolve_foundry_dir(CONFIG.dataset_dir_resolved())
+
+
+@router.get("/foundry")
+def get_foundry(foundry_dir: str = Depends(get_foundry_dir)) -> dict:
+    """Serves era/session identity (``foundry_source_registry.foundry_era_identity`` -- a static
+    dict, never derived per-request), the persisted era-open baseline snapshot VERBATIM
+    (``read_era_open_baseline`` -- ``None`` until the operator's one-time recording act has run,
+    never fabricated), and the explicit not-yet-generated `source_registry_hash` state. Never
+    404/500 before that recording act runs -- the desk router's own never-404-on-absence
+    convention: an honest ``era_open_baseline: null`` on a fresh install, exactly like ``GET
+    /vault``'s honest empty ``shards``/``universes`` before the first registration."""
+    return {
+        "era": foundry_era_identity(),
+        "era_open_baseline": read_era_open_baseline(foundry_dir),
+        "source_registry_hash": None,
+        "source_registry_status": "not_yet_generated",
+    }
diff --git a/apps/backend/scripts/seed_micro_graduation_iter18_fixture.py b/apps/backend/scripts/seed_micro_graduation_iter18_fixture.py
index 16a8128f..dd30b988 100644
--- a/apps/backend/scripts/seed_micro_graduation_iter18_fixture.py
+++ b/apps/backend/scripts/seed_micro_graduation_iter18_fixture.py
@@ -101,7 +101,15 @@ def _events_for_store() -> list:
 
 
 def _observation(session_date: str, symbol: str, value: float) -> dict:
-    return {"session_date": session_date, "symbol": symbol, "value": value}
+    # goal-hypothesis-foundry-iter-1 (TC-1/TC-2): every observation must declare the canonical
+    # unit its `value` is already expressed in, or `walkforward.require_canonical_observation_units`
+    # refuses it before a single value is averaged (r13/r14 unit-discipline guard -- see that
+    # function's own docstring). This fixture's values were ALWAYS basis points (`_ECON_FLOOR`
+    # above compares them against a `floor_bps` in the SAME `long`/positive direction) -- the bug
+    # was a missing declaration, never a wrong unit, so the fix names the SAME canonical constant
+    # the guard itself checks against (`walkforward.WF_OBSERVATION_UNIT`, itself
+    # `micro_features.OUTCOME_UNIT` -- never a second, independently-spelled unit string).
+    return {"session_date": session_date, "symbol": symbol, "value": value, "value_unit": wf.WF_OBSERVATION_UNIT}
 
 
 def _passing_observations() -> list[dict]:
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 55365438..eb9c00e9 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -62,6 +62,7 @@ import {
   fetchDeskScout,
   fetchDeskScoutCompute,
   fetchDeskScoutRuns,
+  fetchDeskFoundry,
   fetchDeskGraduation,
   fetchDeskMicroSnapshots,
   fetchDeskMicroSnapshotsRuns,
@@ -85,6 +86,7 @@ import type {
   DeskForwardRun,
   DeskForwardRunsListResult,
   DeskForwardTouch,
+  DeskFoundryResponse,
   DeskGraduationResponse,
   DeskMicroSnapshotRunsResponse,
   DeskMicroSnapshotsResponse,
@@ -397,7 +399,8 @@ type DeskCollapsibleSection =
   | "walkForward"
   | "validationVault"
   | "graduation"
-  | "featureSnapshots";
+  | "featureSnapshots"
+  | "hypothesisFoundry";
 // DESK-COLLAPSED-END
 
 const PRIMARY_BUTTON_CLASS =
@@ -7361,6 +7364,123 @@ function FeatureSnapshotsSection({
   );
 }
 
+// goal-hypothesis-foundry-iter-1 (J-01): the Hypothesis Foundry panel header -- era/session
+// identity + the era-open baseline, rendered VERBATIM from `GET /research/desk/micro/foundry`
+// (no client-side recomputation, per the goal's own Product Shape). The `foundry-panel`
+// data-testid family this iteration's IN SCOPE names; every other Foundry subview (Sources/
+// Compiler, Interpreter, Freeze/Integrity, ...) is deferred to a later, consolidated
+// read-surface iteration (Binding Execution Order step 5).
+function HypothesisFoundrySection({
+  foundryResult,
+}: {
+  foundryResult: { ok: boolean; data: DeskFoundryResponse | null; error?: string } | null;
+}) {
+  if (foundryResult === null) {
+    return (
+      <div data-testid="foundry-panel">
+        <LoadingPanel testid="foundry-panel-loading" />
+      </div>
+    );
+  }
+  if (!foundryResult.ok || foundryResult.data === null) {
+    return (
+      <div data-testid="foundry-panel">
+        <UnavailablePanel
+          testid="foundry-panel-unavailable"
+          message={foundryResult.error ?? "The Hypothesis Foundry panel could not be loaded."}
+        />
+      </div>
+    );
+  }
+  const foundry = foundryResult.data;
+  const baseline = foundry.era_open_baseline;
+  return (
+    <div data-testid="foundry-panel">
+      <p className="mb-3 text-xs text-slate-500">
+        The Hypothesis Foundry (GET /research/desk/micro/foundry, read verbatim; read-only this
+        era): the era boundary and the frozen era-open baseline the whole epoch is audited
+        against. Foundry methodology spec version{" "}
+        <span className="font-mono text-slate-300">{foundry.era.foundry_spec_version}</span>.
+      </p>
+
+      <div data-testid="foundry-era-identity" className="mb-4 text-[11px] text-slate-500">
+        <p>
+          Previous era:{" "}
+          <span className="font-mono text-slate-300">{foundry.era.previous_era}</span>
+          {" ("}
+          <span className="font-mono text-slate-300">{foundry.era.previous_era_status}</span>
+          {")"}
+        </p>
+        <p>
+          Current era:{" "}
+          <span className="font-mono text-emerald-300">{foundry.era.current_era}</span>
+          {" ("}
+          <span className="font-mono text-emerald-300">{foundry.era.current_era_status}</span>
+          {")"}
+        </p>
+        <p>
+          Source registry hash:{" "}
+          <span className="font-mono text-slate-300">
+            {foundry.source_registry_hash ?? foundry.source_registry_status}
+          </span>
+        </p>
+      </div>
+
+      <div data-testid="foundry-era-open-baseline">
+        <h4 className="mb-2 text-xs font-semibold text-slate-400">Era-Open Baseline</h4>
+        {baseline === null ? (
+          <EmptyState
+            testid="foundry-era-open-baseline-empty"
+            title="The era-open baseline has not been recorded yet."
+          />
+        ) : (
+          <div className="text-xs text-slate-300">
+            <p data-testid="foundry-baseline-suite-counts" className="mb-1">
+              Backend suite:{" "}
+              <span className="font-mono">{baseline.backend_suite.passed} passed</span>
+              {" · "}
+              <span className="font-mono">{baseline.backend_suite.skipped} skipped</span>
+              {" · "}
+              <span className="font-mono">{baseline.backend_suite.failed} failed</span>
+            </p>
+            <p data-testid="foundry-baseline-tsc-errors" className="mb-1">
+              tsc --noEmit errors: <span className="font-mono">{baseline.tsc_error_count}</span>
+            </p>
+            <p data-testid="foundry-baseline-config-fingerprint" className="mb-3">
+              Config fingerprint:{" "}
+              <span className="font-mono text-[10px] text-slate-400">{baseline.config_fingerprint}</span>
+            </p>
+            <h5 className="mb-2 text-xs font-semibold text-slate-400">Referee Module SHA-256</h5>
+            <div className="overflow-x-auto">
+              <table
+                data-testid="foundry-referee-module-hashes-table"
+                className="w-full min-w-[640px] border-collapse text-xs"
+              >
+                <thead>
+                  <tr className="border-b border-slate-800 text-left text-slate-500">
+                    <th className="px-1.5 py-1">Module</th>
+                    <th className="px-1.5 py-1">SHA-256</th>
+                  </tr>
+                </thead>
+                <tbody data-testid="foundry-referee-module-hash-rows">
+                  {Object.entries(baseline.referee_module_sha256).map(([moduleName, hash]) => (
+                    <tr key={moduleName} className="border-b border-slate-900">
+                      <td className="px-1.5 py-1 font-mono text-slate-300">{moduleName}</td>
+                      <td className="whitespace-nowrap px-1.5 py-1 font-mono text-[10px] text-slate-500">
+                        {hash}
+                      </td>
+                    </tr>
+                  ))}
+                </tbody>
+              </table>
+            </div>
+          </div>
+        )}
+      </div>
+    </div>
+  );
+}
+
 // era-desk-iter-14 (J-10): a third compute control, wired exactly like `TopupComputeControl` — the
 // operation has no per-pair counters (it is a single classify-repair-verify walk, not a walk over
 // many pairs), so the running indicator shows the compute's own `progress.phase` label instead of
@@ -10277,6 +10397,15 @@ export default function DeskPage() {
     error?: string;
   } | null>(null);
 
+  // goal-hypothesis-foundry-iter-1 (J-01): the Hypothesis Foundry panel header's own fetch-on-
+  // expand result -- the SAME `null` (not yet fetched) / `{ok, data, error}` shape every other
+  // Desk section already uses.
+  const [foundryResult, setFoundryResult] = useState<{
+    ok: boolean;
+    data: DeskFoundryResponse | null;
+    error?: string;
+  } | null>(null);
+
   // iter-14 audit (finding F1): the ONE stop flag both plain-async compute polls below observe.
   // This page's own contract for a plain `for(;;)` driver that awaits `refreshChainSleep` is the
   // `refreshChainStopRef` pattern further down ("Unmounting (a nav away mid-chain) stops the driver
@@ -10373,6 +10502,11 @@ export default function DeskPage() {
       // on first expand.
       fetchDeskMicroSnapshots().then(setSnapshotsResult);
       fetchDeskMicroSnapshotsRuns().then(setSnapshotsRunsResult);
+    } else if (section === "hypothesisFoundry") {
+      // goal-hypothesis-foundry-iter-1 (J-01): the Hypothesis Foundry panel header's own ONE
+      // fetch -- read-only, no compute control (the Foundry surface is read-only per the goal's
+      // own Product Shape).
+      fetchDeskFoundry().then(setFoundryResult);
     }
   }
 
@@ -12700,6 +12834,23 @@ export default function DeskPage() {
             <FeatureSnapshotsSection snapshotsResult={snapshotsResult} runsResult={snapshotsRunsResult} />
           </CollapsibleSection>
         </section>
+
+        {/* goal-hypothesis-foundry-iter-1 (J-01): the Hypothesis Foundry panel -- the new era's
+            FIRST section, rendered directly BELOW every existing shipped Rapid-Microscope section
+            above (T-11: new `foundry-*` data-testid family, no shipped data-testid or heading
+            string reused anywhere else on this page). Panel header only this iteration (era
+            identity + era-open baseline) -- every other Foundry subview is deferred to a later,
+            consolidated read-surface iteration. */}
+        <section aria-label="Hypothesis Foundry" className="mt-6">
+          <CollapsibleSection
+            id="hypothesisFoundry"
+            title="Hypothesis Foundry"
+            open={expandedSections.has("hypothesisFoundry")}
+            onToggle={() => toggleSection("hypothesisFoundry")}
+          >
+            <HypothesisFoundrySection foundryResult={foundryResult} />
+          </CollapsibleSection>
+        </section>
       </main>
     </div>
   );
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index d46f76a4..3fbcd5ab 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -21,6 +21,7 @@ import type {
   DeskForwardPinsResult,
   DeskForwardReadResult,
   DeskForwardRunsListResult,
+  DeskFoundryResponse,
   DeskGraduationResponse,
   DeskMicroSnapshotsResponse,
   DeskMicroSnapshotRunsResponse,
@@ -2790,3 +2791,30 @@ export async function fetchDeskMicroSnapshotsRuns(): Promise<{
     return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
   }
 }
+
+// GET /research/desk/micro/foundry (goal-hypothesis-foundry-iter-1, J-01) — era/session identity
+// + the era-open baseline, read verbatim (no client-side recomputation). The ONLY fetch the
+// Hypothesis Foundry panel header issues this iteration — the Sources/Compiler and every other
+// Foundry subview are deferred to a later, consolidated read-surface iteration.
+export async function fetchDeskFoundry(): Promise<{
+  ok: boolean;
+  data: DeskFoundryResponse | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/micro/foundry`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskFoundryResponse };
+    }
+    let error = "The Hypothesis Foundry panel could not be loaded.";
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
index 940be1f3..1d7403f0 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -2961,3 +2961,33 @@ export interface DeskMicroSnapshotRunLogEntry {
 export interface DeskMicroSnapshotRunsResponse {
   runs: DeskMicroSnapshotRunLogEntry[];
 }
+
+// --- Era "The Hypothesis Foundry" -- GET /research/desk/micro/foundry (goal-hypothesis-foundry-
+// iter-1, J-01): the panel header only this iteration -- era/session identity + the era-open
+// baseline (full-suite pass/skip/failed counts, tsc error count, config fingerprint, six
+// Referee-module SHA-256 hashes). `source_registry_hash` is always `null` this iteration (the
+// real registry does not exist until J-06) -- rendered beside an explicit status string, never a
+// fabricated placeholder hash.
+export interface FoundryEraIdentity {
+  previous_era: string;
+  previous_era_status: string;
+  current_era: string;
+  current_era_status: string;
+  foundry_spec_version: string;
+}
+
+export interface FoundryEraOpenBaseline {
+  backend_suite: { passed: number; skipped: number; failed: number };
+  tsc_error_count: number;
+  config_fingerprint: string;
+  referee_module_sha256: Record<string, string>;
+}
+
+export interface DeskFoundryResponse {
+  era: FoundryEraIdentity;
+  // `null` on a fresh install before the operator's one-time recording act has run -- never
+  // fabricated (the same honest-absence convention every other Desk section already uses).
+  era_open_baseline: FoundryEraOpenBaseline | null;
+  source_registry_hash: string | null;
+  source_registry_status: string;
+}
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-hypothesis-foundry/telemetry.jsonl   | 6 ++++++
 runs/goal-session-hypothesis-foundry/trace/trace.jsonl | 1 +
 2 files changed, 7 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
