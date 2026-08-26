# Iteration diff (bounded)

Files changed: 13. Shown in full: 12.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_foundry_source_registry.py` (16 lines not shown)

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
diff --git a/apps/backend/app/research/foundry_compiler.py b/apps/backend/app/research/foundry_compiler.py
new file mode 100644
index 00000000..ae730e09
--- /dev/null
+++ b/apps/backend/app/research/foundry_compiler.py
@@ -0,0 +1,309 @@
+"""The Hypothesis Foundry -- the compiler: the canonical ``CandidateSpec`` schema (spec §3) and
+compilation of ``COMPILED``-disposition ``SourceRecord``s (``foundry_source_registry.py``) into
+real ``CandidateSpec`` objects. See ``docs/hypothesis-foundry-spec.md`` §3 for the schema
+rationale and the hash discipline this module implements verbatim.
+
+**Scope this iteration (goal-hypothesis-foundry-iter-1).** Deferred/population-resolution
+machinery -- the generic interpreter that would derive ``coordinates``/``population``/``outcome``
+content from a ``mechanism_statement``'s own prose, or resolve a multi-coordinate/deferred
+membership corner -- is ``foundry_interpreter.py``, explicitly future work (``docs/goal.md``
+Binding Execution Order step 3 / J-03). This module only compiles a source whose scientific
+content is ALREADY fully resolved and non-deferred: the caller of ``compile_sources`` passes
+one ``CandidateBlueprint`` per compileable ``source_id`` -- the rest of the §3 schema, already
+frozen by the same audited authoring act that filled in the record's §1.4 fields, exactly as
+mechanical as those fields are (never derived from parsing ``mechanism_statement`` text at
+compile time). A record this module cannot build a spec for despite reaching ``COMPILED`` (no
+blueprint supplied, or one naming a deferred join) is left ``FROZEN_READY``-incomplete this
+revision rather than approximated -- see ``docs/hypothesis-foundry-spec.md`` §12."""
+
+from __future__ import annotations
+
+import hashlib
+import json
+from collections import defaultdict
+from dataclasses import asdict, dataclass, field
+from pathlib import Path
+from typing import Mapping, Sequence
+
+from . import scout
+from .foundry_source_registry import (
+    DISPOSITION_COMPILED,
+    SourceRecord,
+    compile_source_disposition,
+    lint_quoted_spans,
+    source_registry_hash as _registry_hash,
+)
+
+__all__ = [
+    "AVAILABILITY_RULE",
+    "UNRESOLVED_COMPONENT_POLICY",
+    "COMPARATOR_RULE",
+    "OUTCOME_MEASURE",
+    "CandidateCoordinate",
+    "CandidatePopulation",
+    "CandidateRelation",
+    "CandidateOutcome",
+    "EconomicFloorRule",
+    "CandidateBlueprint",
+    "CandidateSpec",
+    "CompilationResult",
+    "FamilyOrdinalCollision",
+    "compile_sources",
+    "compiler_hash",
+]
+
+# --- §3 frozen literal-valued fields -- named constants so a caller/test never re-types the
+# literal string (and so a typo can't silently mint a second value that MEANS the same thing). ---
+AVAILABILITY_RULE = "max_conditioning_available_at"
+UNRESOLVED_COMPONENT_POLICY = "exclude_and_count"
+COMPARATOR_RULE = "complement_within_same_eligible_population"
+OUTCOME_MEASURE = "return_bps"
+
+
+@dataclass(frozen=True)
+class CandidateCoordinate:
+    """One §3 ``coordinates[]`` entry. ``resolution_join_rule`` is ``"immediate"`` for every
+    fixture this revision compiles (no deferred construct -- that is ``foundry_interpreter.py``'s
+    future job); a non-``"immediate"`` value is accepted by the schema (future-proofing §3's own
+    "if a deferred completion cannot be uniquely joined... compilation blocks" rule) but this
+    module's ``compile_sources`` refuses to build a spec around one this revision."""
+
+    feature_construct_id: str
+    semantic_role: str
+    transform_orientation: str
+    threshold_corner_predicate: str
+    threshold_provenance: str | None
+    aggressor_derived: bool
+    unit_basis: str
+    anchor_at: str
+    available_at: str
+    resolution_join_rule: str = "immediate"
+
+
+@dataclass(frozen=True)
+class CandidatePopulation:
+    structure_context_kind: str
+    side_filter: str | None
+    setup_context_id: str | None
+
+
+@dataclass(frozen=True)
+class CandidateRelation:
+    kind: str
+    parameters: Mapping[str, object] = field(default_factory=dict)
+
+
+@dataclass(frozen=True)
+class CandidateOutcome:
+    horizon_key: str
+    sidedness: str
+    measure: str = OUTCOME_MEASURE
+
+    def __post_init__(self) -> None:
+        if self.horizon_key not in scout.HORIZON_KEYS:
+            # §3.1: "Foundry candidates may use only horizon keys actually accepted by the existing
+            # block-length rail... implementation must verify this from current code rather than
+            # infer it." Verified against `scout.HORIZON_KEYS` directly, never a second literal set.
+            raise ValueError(
+                f"horizon_key {self.horizon_key!r} is not a legal Scout horizon "
+                f"(scout.HORIZON_KEYS={sorted(scout.HORIZON_KEYS)!r})"
+            )
+        if self.sidedness not in ("long", "short"):
+            raise ValueError(f"sidedness must be 'long' or 'short', got {self.sidedness!r}")
+
+
+@dataclass(frozen=True)
+class EconomicFloorRule:
+    """§6: "the manifest freezes the existing economic-floor RULE, not a result-dependent floor
+    number." ``numeric_floor_bps`` is always ``None`` out of this module -- it "materializes later
+    before outcome read and cannot be back-filled" (§6/§3), which is real-epoch/exhaust-runner
+    territory (J-07), not compile-time territory."""
+
+    rule: str = "scout_quoted_spread_floor"
+    multiple: float = 0.0
+    numeric_floor_bps: float | None = None
+
+
+@dataclass(frozen=True)
+class CandidateBlueprint:
+    """The non-deferred rest of the §3 schema a ``SourceRecord`` author already froze by hand --
+    see this module's own docstring for why this is a fixture/hermetic-authoring input this
+    revision, not a derivation."""
+
+    population: CandidatePopulation
+    coordinates: tuple[CandidateCoordinate, ...]
+    relation: CandidateRelation
+    membership_corner: str
+    outcome: CandidateOutcome
+    economic_floor_rule: EconomicFloorRule = field(default_factory=EconomicFloorRule)
+
+    def is_immediate(self) -> bool:
+        """``True`` only when every coordinate resolves without a deferred join -- the condition
+        under which THIS module (rather than the future ``foundry_interpreter.py``) may compile
+        it."""
+        return all(c.resolution_join_rule == "immediate" for c in self.coordinates)
+
+
+@dataclass(frozen=True)
+class CandidateSpec:
+    """The canonical, frozen scientific object (spec §3), implementing every required field.
+    ``candidate_spec_hash`` (set by ``compile_sources``, never at construction) is a ``sha256``
+    over every field below EXCEPT the four hash/pointer fields themselves
+    (``manifest_hash``, ``source_registry_hash``, ``compiler_hash``, ``candidate_spec_hash``) --
+    see ``_canonical_fields`` below and ``docs/hypothesis-foundry-spec.md`` §3."""
+
+    foundry_spec_version: str
+    epoch_id: str
+    source_ids: tuple[str, ...]
+    lineage_id: str
+    foundry_family_id: str
+    variant_id: str
+    variant_ordinal: int
+    population: CandidatePopulation
+    coordinates: tuple[CandidateCoordinate, ...]
+    relation: CandidateRelation
+    membership_corner: str
+    outcome: CandidateOutcome
+    economic_floor_rule: EconomicFloorRule
+    foundry_family_variant_count: int
+    availability_rule: str = AVAILABILITY_RULE
+    unresolved_component_policy: str = UNRESOLVED_COMPONENT_POLICY
+    comparator: str = COMPARATOR_RULE
+    manifest_hash: str | None = None
+    source_registry_hash: str = ""
+    compiler_hash: str = ""
+    candidate_spec_hash: str = ""
+
+    def _canonical_fields(self) -> dict:
+        """Every field EXCEPT the four hash/pointer fields -- ``manifest_hash`` is excluded
+        because it is computed FROM the whole compiled manifest (including this spec), so
+        including it here would be circular; ``source_registry_hash``/``compiler_hash`` are
+        excluded for the SAME reason this schema keeps them as separate provenance pointers
+        rather than folding them into the spec's own scientific identity; ``candidate_spec_hash``
+        obviously excludes itself. ``dataclasses.asdict`` + ``sort_keys=True`` below makes this
+        invariant to Python field-construction/serialization order (TC-10)."""
+        raw = asdict(self)
+        for key in ("manifest_hash", "source_registry_hash", "compiler_hash", "candidate_spec_hash"):
+            raw.pop(key, None)
+        return raw
+
+    def compute_hash(self) -> str:
+        blob = json.dumps(self._canonical_fields(), sort_keys=True, default=str)
+        return hashlib.sha256(blob.encode("utf-8")).hexdigest()
+
+    def with_hash(self) -> "CandidateSpec":
+        """Returns a copy with ``candidate_spec_hash`` filled in -- the ONE place this module ever
+        sets it, always computed AFTER every other field is final."""
+        object.__setattr__(self, "candidate_spec_hash", self.compute_hash())
+        return self
+
+
+class FamilyOrdinalCollision(Exception):
+    """Two ``COMPILED`` records share one ``foundry_family_key`` and the SAME ``variant_ordinal``
+    -- refused before any ``CandidateSpec`` is built (never silently overwritten)."""
+
+
+@dataclass(frozen=True)
+class CompilationResult:
+    source_registry_hash: str
+    dispositions: Mapping[str, str]
+    candidate_specs: Mapping[str, CandidateSpec]
+
+
+def compiler_hash() -> str:
+    """A ``sha256`` of THIS module's own source file -- the compiler's own identity, exactly like
+    ``docs/goal.md §8.4``'s freeze-set will later pin every science-affecting module by content
+    hash. Recomputed fresh every call (cheap, deterministic) rather than cached, so it can never
+    silently go stale after an edit."""
+    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
+
+
+def compile_sources(
+    records: Sequence[SourceRecord],
+    *,
+    foundry_spec_version: str,
+    epoch_id: str,
+    blueprints: Mapping[str, CandidateBlueprint] | None = None,
+    manifest_hash: str | None = None,
+) -> CompilationResult:
+    """Compiles a WHOLE batch of ``SourceRecord``s (spec §0/§2): lints every quoted span first
+    (fails closed before any ``CandidateSpec`` is built -- TC-12), derives each record's
+    disposition via the fixed §2 precedence, groups ``COMPILED`` records sharing a
+    ``foundry_family_key`` into one family (TC-4: shared ``foundry_family_id``, shared
+    ``foundry_family_variant_count``, distinct ``variant_ordinal``), and builds a ``CandidateSpec``
+    for every ``COMPILED`` record whose ``source_id`` key appears in ``blueprints`` with a fully
+    immediate blueprint (no deferred coordinate -- ``foundry_interpreter.py`` future work
+    otherwise, TC-5/TC-6/TC-7/TC-9's blocked/aliased fixtures never reach this branch at all since
+    their disposition is not ``COMPILED``).
+
+    ``blueprints`` is keyed by ``source_id`` and passed SEPARATELY from ``records`` rather than
+    living as a field on ``SourceRecord`` -- the §1.4 source-record schema
+    (``foundry_source_registry.SourceRecord``) and the §3 ``CandidateSpec`` schema this module
+    owns are deliberately two separate schemas (goal.md itself lists them as two distinct
+    sections); keeping ``CandidateBlueprint`` out of ``SourceRecord`` avoids a needless import
+    cycle between the two modules and keeps each module's own schema self-contained."""
+    lint_quoted_spans(records)
+    blueprints = blueprints or {}
+    registry_hash = _registry_hash(records)
+    this_compiler_hash = compiler_hash()
+
+    dispositions: dict[str, str] = {}
+    family_members: dict[str, list[SourceRecord]] = defaultdict(list)
+    for record in records:
+        disposition = compile_source_disposition(record)
+        dispositions[record.source_id] = disposition
+        if disposition == DISPOSITION_COMPILED and record.foundry_family_key is not None:
+            family_members[record.foundry_family_key].append(record)
+
+    for family_key, members in family_members.items():
+        ordinals = [m.variant_ordinal for m in members]
+        if len(set(ordinals)) != len(ordinals):
+            raise FamilyOrdinalCollision(
+                f"foundry family {family_key!r} has a duplicate variant_ordinal among {ordinals!r}"
+            )
+
+    specs: dict[str, CandidateSpec] = {}
+    for record in records:
+        if dispositions[record.source_id] != DISPOSITION_COMPILED:
+            continue
+        blueprint = blueprints.get(record.source_id)
+        if blueprint is None or not blueprint.is_immediate():
+            # This revision's scope: only fully-immediate, non-deferred blueprints compile here.
+            # A COMPILED-but-not-yet-spec'd record simply produces no CandidateSpec this revision
+            # (§7.2's FROZEN_READY-incomplete state) -- never approximated.
+            continue
+
+        if record.foundry_family_key is not None:
+            family_key = record.foundry_family_key
+            members = family_members[family_key]
+            family_variant_count = len(members)
+        else:
+            family_key = record.source_id
+            family_variant_count = 1
+
+        foundry_family_id = f"family:{family_key}"
+        variant_ordinal = record.variant_ordinal if record.variant_ordinal is not None else 0
+        variant_id = f"{foundry_family_id}:{variant_ordinal}"
+
+        spec = CandidateSpec(
+            foundry_spec_version=foundry_spec_version,
+            epoch_id=epoch_id,
+            source_ids=(record.source_id,),
+            lineage_id=record.lineage_id or record.source_id,
+            foundry_family_id=foundry_family_id,
+            variant_id=variant_id,
+            variant_ordinal=variant_ordinal,
+            population=blueprint.population,
+            coordinates=blueprint.coordinates,
+            relation=blueprint.relation,
+            membership_corner=blueprint.membership_corner,
+            outcome=blueprint.outcome,
+            economic_floor_rule=blueprint.economic_floor_rule,
+            foundry_family_variant_count=family_variant_count,
+            manifest_hash=manifest_hash,
+            source_registry_hash=registry_hash,
+            compiler_hash=this_compiler_hash,
+        ).with_hash()
+        specs[record.source_id] = spec
+
+    return CompilationResult(source_registry_hash=registry_hash, dispositions=dispositions, candidate_specs=specs)
diff --git a/apps/backend/app/research/foundry_source_registry.py b/apps/backend/app/research/foundry_source_registry.py
new file mode 100644
index 00000000..3dde0c6c
--- /dev/null
+++ b/apps/backend/app/research/foundry_source_registry.py
@@ -0,0 +1,392 @@
+"""The Hypothesis Foundry (goal-hypothesis-foundry) -- the source registry: the closed §7.1
+disposition vocabulary, the §1.4 per-source-record schema, the §2 owner meta-policy compile
+precedence, the §1.4 exact-quote lint, and the era-open baseline snapshot. See
+``docs/hypothesis-foundry-spec.md`` (this module implements that spec's §1.4/§2/§7.1 verbatim;
+section numbers below match both that file and ``docs/goal.md``'s Foundry Constitution).
+
+**What this module deliberately is NOT.** It never reads a candidate outcome, Scout result,
+p-value, effect, or sample count -- ``compile_source_disposition`` below takes only the
+mechanically-declared fields a ``SourceRecord`` already carries and returns one disposition from
+the closed vocabulary, with no branch anywhere keyed on anything outcome-shaped. It authors no
+real source object this iteration (that is ``J-06``); every record this module's own tests build
+is one of the seven hermetic fixture taxonomy examples ``docs/goal.md`` J-02 step 2 names.
+
+**Why ``compile_source_disposition`` takes a single ``SourceRecord`` and not a batch.** Disposition
+is a per-record decision (proxy / supersession / spec-gap / direction / study-form / natural
+threshold), fully determined by that record's own declared fields -- it never depends on which
+other records exist. Family bookkeeping (grouping ``COMPILED`` records that share a
+``foundry_family_key``, assigning ``foundry_family_variant_count``) is instead ``foundry_compiler.
+compile_sources``'s job, because THAT decision genuinely needs the whole batch."""
+
+from __future__ import annotations
+
+import hashlib
+import json
+import os
+from dataclasses import dataclass, field
+from pathlib import Path
+from typing import Mapping, Sequence
+
+__all__ = [
+    "SOURCE_DISPOSITIONS",
+    "DISPOSITION_COMPILED",
+    "DISPOSITION_ALIASED_PROXY_ONLY",
+    "DISPOSITION_ALIASED_VARIANT_VOCABULARY",
+    "DISPOSITION_ALIASED_LINEAGE",
+    "DISPOSITION_EXCLUDED_PREVIOUSLY_KILLED",
+    "DISPOSITION_EXCLUDED_PREREQUISITE_UNMET",
+    "DISPOSITION_EXCLUDED_GATE_CLOSED",
+    "DISPOSITION_BLOCKED_SPEC_GAP",
+    "DISPOSITION_BLOCKED_MISSING_PRIMITIVE",
+    "DISPOSITION_BLOCKED_UNSUPPORTED_STUDY_FORM",
+    "DISPOSITION_BLOCKED_UNSUPPORTED_RELATION",
+    "DISPOSITION_BLOCKED_DIRECTION",
+    "DISPOSITION_BLOCKED_VARIANT_EXPLOSION",
+    "DISPOSITION_BLOCKED_UNIT_CONTRACT",
+    "BLOCKED_DIRECTION_SENTINEL",
+    "BLOCKED_UNSUPPORTED_STUDY_FORM_SENTINEL",
+    "THRESHOLD_LITERAL_RATIFIED",
+    "THRESHOLD_FROZEN_FEATURE_CONTRACT",
+    "THRESHOLD_NATURAL_SEMANTIC_BOUNDARY",
+    "LEGAL_THRESHOLD_PROVENANCES",
+    "QuotedSpan",
+    "ProxyDeclaration",
+    "SupersessionDeclaration",
+    "SourceRecord",
+    "QuoteMismatch",
+    "compile_source_disposition",
+    "lint_quoted_spans",
+    "source_registry_hash",
+    "resolve_foundry_dir",
+    "record_era_open_baseline",
+    "read_era_open_baseline",
+    "REFEREE_MODULES",
+    "FOUNDRY_SPEC_VERSION",
+    "PREVIOUS_ERA",
+    "PREVIOUS_ERA_STATUS",
+    "CURRENT_ERA",
+    "CURRENT_ERA_STATUS",
+    "foundry_era_identity",
+]
+
+# --- §7.1: the closed source-disposition vocabulary -----------------------------------------------
+DISPOSITION_COMPILED = "COMPILED"
+DISPOSITION_ALIASED_PROXY_ONLY = "ALIASED_PROXY_ONLY"
+DISPOSITION_ALIASED_VARIANT_VOCABULARY = "ALIASED_VARIANT_VOCABULARY"
+DISPOSITION_ALIASED_LINEAGE = "ALIASED_LINEAGE"
+DISPOSITION_EXCLUDED_PREVIOUSLY_KILLED = "EXCLUDED_PREVIOUSLY_KILLED"
+DISPOSITION_EXCLUDED_PREREQUISITE_UNMET = "EXCLUDED_PREREQUISITE_UNMET"
+DISPOSITION_EXCLUDED_GATE_CLOSED = "EXCLUDED_GATE_CLOSED"
+DISPOSITION_BLOCKED_SPEC_GAP = "BLOCKED_SPEC_GAP"
+DISPOSITION_BLOCKED_MISSING_PRIMITIVE = "BLOCKED_MISSING_PRIMITIVE"
+DISPOSITION_BLOCKED_UNSUPPORTED_STUDY_FORM = "BLOCKED_UNSUPPORTED_STUDY_FORM"
+DISPOSITION_BLOCKED_UNSUPPORTED_RELATION = "BLOCKED_UNSUPPORTED_RELATION"
+DISPOSITION_BLOCKED_DIRECTION = "BLOCKED_DIRECTION"
+DISPOSITION_BLOCKED_VARIANT_EXPLOSION = "BLOCKED_VARIANT_EXPLOSION"
+DISPOSITION_BLOCKED_UNIT_CONTRACT = "BLOCKED_UNIT_CONTRACT"
+
+SOURCE_DISPOSITIONS = frozenset(
+    {
+        DISPOSITION_COMPILED,
+        DISPOSITION_ALIASED_PROXY_ONLY,
+        DISPOSITION_ALIASED_VARIANT_VOCABULARY,
+        DISPOSITION_ALIASED_LINEAGE,
+        DISPOSITION_EXCLUDED_PREVIOUSLY_KILLED,
+        DISPOSITION_EXCLUDED_PREREQUISITE_UNMET,
+        DISPOSITION_EXCLUDED_GATE_CLOSED,
+        DISPOSITION_BLOCKED_SPEC_GAP,
+        DISPOSITION_BLOCKED_MISSING_PRIMITIVE,
+        DISPOSITION_BLOCKED_UNSUPPORTED_STUDY_FORM,
+        DISPOSITION_BLOCKED_UNSUPPORTED_RELATION,
+        DISPOSITION_BLOCKED_DIRECTION,
+        DISPOSITION_BLOCKED_VARIANT_EXPLOSION,
+        DISPOSITION_BLOCKED_UNIT_CONTRACT,
+    }
+)
+
+# A record with no mechanical direction rule declares this literal sentinel rather than leaving
+# `direction_derivation` empty/None -- an explicit typed refusal, never an absence a caller could
+# mistake for "not yet filled in" (spec §3.2 / goal.md §2.2).
+BLOCKED_DIRECTION_SENTINEL = "BLOCKED_DIRECTION"
+BLOCKED_UNSUPPORTED_STUDY_FORM_SENTINEL = "BLOCKED_UNSUPPORTED_STUDY_FORM"
+
+# --- §2.3: the natural-boundary law's three (and only three) legal threshold provenances ----------
+THRESHOLD_LITERAL_RATIFIED = "literal_ratified_threshold"
+THRESHOLD_FROZEN_FEATURE_CONTRACT = "frozen_rapid_validation_feature_contract"
+THRESHOLD_NATURAL_SEMANTIC_BOUNDARY = "natural_semantic_boundary"
+LEGAL_THRESHOLD_PROVENANCES = frozenset(
+    {THRESHOLD_LITERAL_RATIFIED, THRESHOLD_FROZEN_FEATURE_CONTRACT, THRESHOLD_NATURAL_SEMANTIC_BOUNDARY}
+)
+
+
+@dataclass(frozen=True)
+class QuotedSpan:
+    """One exact quoted source span backing a load-bearing compile/audit decision (spec §1.4).
+    ``location`` is the exact character OFFSET into the owning record's ``source_excerpt`` -- the
+    lint below checks the substring AT that offset, never "appears somewhere", so a span whose
+    text matches but whose location does not is still a lint failure (TC-12's "fails closed")."""
+
+    text: str
+    location: int
+
+
+@dataclass(frozen=True)
+class ProxyDeclaration:
+    """Marks a ``SourceRecord`` as a frozen pilot-proxy request for a parked study (goal.md
+    §1.1's "these proxies are source objects for provenance, not permission to launder a partial
+    proxy as the full mechanism"). ``do_not`` is the proxy's own existing restriction, preserved
+    verbatim onto the compiled record (TC-6)."""
+
+    parked_study_source_id: str
+    do_not: str
+
+
+@dataclass(frozen=True)
+class SupersessionDeclaration:
+    """Marks a ``SourceRecord`` as the OLDER member of a formula-scoped supersession pair (spec
+    §1.3). ``newer_source_ref`` is what ``superseded_fields`` cites; ``alias_kind`` selects which
+    of the two alias dispositions this record reaches."""
+
+    newer_source_ref: str
+    alias_kind: str = DISPOSITION_ALIASED_VARIANT_VOCABULARY
+
+    def __post_init__(self) -> None:
+        if self.alias_kind not in (DISPOSITION_ALIASED_VARIANT_VOCABULARY, DISPOSITION_ALIASED_LINEAGE):
+            raise ValueError(f"alias_kind must be one of the two alias dispositions, got {self.alias_kind!r}")
+
+
+@dataclass(frozen=True)
+class SourceRecord:
+    """The §1.4 per-source-record schema, verbatim. See ``docs/hypothesis-foundry-spec.md`` §1.4
+    for the full field-by-field rationale. Every collection field is a ``tuple``/mapping-of-str so
+    the whole record stays hashable and JSON-serializes deterministically for
+    ``source_registry_hash`` below."""
+
+    source_id: str
+    source_path: str
+    section_ref: str
+    quoted_spans: tuple[QuotedSpan, ...]
+    source_excerpt: str
+    mechanism_statement: str
+    operative_formula_refs: tuple[str, ...]
+    direction_derivation: str
+    comparator_derivation: str
+    audit_note: str
+    lineage_id: str | None = None
+    foundry_family_key: str | None = None
+    variant_ordinal: int | None = None
+    threshold_provenance: str | None = None
+    unresolved_magnitude_words: tuple[str, ...] = ()
+    superseded_fields: Mapping[str, str] = field(default_factory=dict)
+    proxy_of: ProxyDeclaration | None = None
+    supersession: SupersessionDeclaration | None = None
+    explicit_exclusion: str | None = None  # one of the three EXCLUDED_* dispositions, or None
+    aliases_lineage_ids: tuple[str, ...] = ()
+    # Caller-supplied metadata the compiler NEVER reads (TC-11): an injected effect/p-value/n
+    # fixture field lives here and provably cannot move a disposition or a CandidateSpec hash,
+    # because nothing below ever looks at this mapping.
+    extra: Mapping[str, object] = field(default_factory=dict)
+
+    def __post_init__(self) -> None:
+        if self.threshold_provenance is not None and self.threshold_provenance not in LEGAL_THRESHOLD_PROVENANCES:
+            # Spec §2.3: an illegal/unratified threshold provenance is exactly the shape of source
+            # this era must not silently compile -- refuse the OBJECT at construction rather than
+            # let a caller build one and forget to route it through `unresolved_magnitude_words`.
+            raise ValueError(
+                f"{self.source_id}: threshold_provenance {self.threshold_provenance!r} is not one "
+                f"of the three §2.3 natural-boundary categories -- represent an unratified "
+                "magnitude/threshold as `unresolved_magnitude_words` instead, never as a fourth "
+                "threshold_provenance value"
+            )
+        if self.explicit_exclusion is not None and self.explicit_exclusion not in (
+            DISPOSITION_EXCLUDED_PREVIOUSLY_KILLED,
+            DISPOSITION_EXCLUDED_PREREQUISITE_UNMET,
+            DISPOSITION_EXCLUDED_GATE_CLOSED,
+        ):
+            raise ValueError(f"{self.source_id}: explicit_exclusion must be one of the three EXCLUDED_* dispositions")
+
+
+class QuoteMismatch(Exception):
+    """Raised by ``lint_quoted_spans`` (never swallowed -- fail closed, spec §1.4)."""
+
+
+def lint_quoted_spans(records: Sequence[SourceRecord]) -> None:
+    """Verifies every ``QuotedSpan`` across ``records`` is an EXACT substring of its own record's
+    ``source_excerpt`` AT the recorded character offset. Raises ``QuoteMismatch`` on the first
+    failure (TC-12's "fails closed on an injected mismatched span") -- never a keyword/fuzzy
+    match, per spec §1.4's own explicit "deliberately does not use keyword matching"."""
+    for record in records:
+        for span in record.quoted_spans:
+            end = span.location + len(span.text)
+            actual = record.source_excerpt[span.location:end]
+            if actual != span.text:
+                raise QuoteMismatch(
+                    f"{record.source_id}: quoted span {span.text!r} does not match "
+                    f"source_excerpt[{span.location}:{end}] = {actual!r}"
+                )
+
+
+def compile_source_disposition(record: SourceRecord) -> str:
+    """The §2 owner meta-policy, as one fixed precedence -- no branch below is keyed on which
+    fixture archetype a caller thinks it is building; every decision reads only the record's own
+    declared fields. See ``docs/hypothesis-foundry-spec.md`` §2 for the full rationale behind this
+    exact order."""
+    if record.explicit_exclusion is not None:
+        return record.explicit_exclusion
+    if record.proxy_of is not None:
+        return DISPOSITION_ALIASED_PROXY_ONLY
+    if record.supersession is not None:
+        return record.supersession.alias_kind
+    if record.unresolved_magnitude_words:
+        return DISPOSITION_BLOCKED_SPEC_GAP
+    if record.direction_derivation == BLOCKED_DIRECTION_SENTINEL:
+        return DISPOSITION_BLOCKED_DIRECTION
+    if record.comparator_derivation == BLOCKED_UNSUPPORTED_STUDY_FORM_SENTINEL:
+        return DISPOSITION_BLOCKED_UNSUPPORTED_STUDY_FORM
+    return DISPOSITION_COMPILED
+
+
+def _canonical_source_record(record: SourceRecord) -> dict:
+    """A plain, JSON-serializable, order-independent projection of ``record`` -- the ONE
+    canonicalization ``source_registry_hash`` and ``foundry_compiler``'s CandidateSpec hashing
+    both build on, so a family's registry hash and a variant's spec hash can never silently
+    diverge in how they see the same record."""
+    return {
+        "source_id": record.source_id,
+        "source_path": record.source_path,
+        "section_ref": record.section_ref,
+        "quoted_spans": [{"text": s.text, "location": s.location} for s in record.quoted_spans],
+        "source_excerpt": record.source_excerpt,
+        "mechanism_statement": record.mechanism_statement,
+        "operative_formula_refs": list(record.operative_formula_refs),
+        "direction_derivation": record.direction_derivation,
+        "comparator_derivation": record.comparator_derivation,
+        "lineage_id": record.lineage_id,
+        "foundry_family_key": record.foundry_family_key,
+        "variant_ordinal": record.variant_ordinal,
+        "threshold_provenance": record.threshold_provenance,
+        "unresolved_magnitude_words": list(record.unresolved_magnitude_words),
+        "superseded_fields": dict(record.superseded_fields),
+        "proxy_of": (
+            {"parked_study_source_id": record.proxy_of.parked_study_source_id, "do_not": record.proxy_of.do_not}
+            if record.proxy_of is not None
+            else None
+        ),
+        "supersession": (
+            {"newer_source_ref": record.supersession.newer_source_ref, "alias_kind": record.supersession.alias_kind}
+            if record.supersession is not None
+            else None
+        ),
+        "explicit_exclusion": record.explicit_exclusion,
+        "aliases_lineage_ids": list(record.aliases_lineage_ids),
+    }
+
+
+def source_registry_hash(records: Sequence[SourceRecord]) -> str:
+    """A deterministic ``sha256`` over the whole registry batch, order-invariant in field
+    serialization (``sort_keys=True``) but sensitive to record CONTENT and to which records are
+    present -- the same discipline ``CandidateSpec.candidate_spec_hash`` uses one level down.
+    Deliberately excludes ``record.extra`` (TC-11's non-science escape hatch, spec §1.4)."""
+    canonical = [_canonical_source_record(r) for r in records]
+    blob = json.dumps(canonical, sort_keys=True, default=str)
+    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
+
+
+# --- era-open baseline: recorded ONCE, never recomputed on a page-load GET ------------------------
+
+_FOUNDRY_DIR_ENV = "TAPEOLOGY_FOUNDRY_DIR"
+_BASELINE_FILENAME = "era_open_baseline.json"
+
+# The six referee_*.py modules whose SHA-256 the era-open baseline pins (goal.md J-01 step 5 /
+# this iteration's IN SCOPE list) -- one fixed list, never derived from a directory glob, so an
+# unrelated future referee_*.py addition cannot silently widen what "the baseline" means.
+REFEREE_MODULES = (
+    "referee_adjudicate.py",
+    "referee_evidence.py",
+    "referee_null.py",
+    "referee_registry.py",
+    "referee_routes.py",
+    "referee_stats.py",
+)
+
+
+def resolve_foundry_dir(dataset_dir_resolved: str) -> str:
+    """``TAPEOLOGY_FOUNDRY_DIR`` if set, else a ``foundry`` SIBLING of the caller's already-
+    resolved dataset directory -- the ``micro_graduation.resolve_micro_graduation_dir``/
+    ``vault.resolve_vault_dir`` pattern verbatim. Never a ``Config`` field (an operational
+    storage-location knob, goal.md Constraints)."""
+    override = os.environ.get(_FOUNDRY_DIR_ENV)
+    if override:
+        return override
+    return str(Path(dataset_dir_resolved).parent / "foundry")
+
+
+def _hash_file(path: Path) -> str:
+    return hashlib.sha256(path.read_bytes()).hexdigest()
+
+
+def record_era_open_baseline(
+    foundry_dir: str | Path,
+    *,
+    suite_passed: int,
+    suite_skipped: int,
+    suite_failed: int,
+    tsc_error_count: int,
+    config_fingerprint: str,
+    research_dir: str | Path,
+) -> dict:
+    """Computes ONCE and persists the static era-open baseline snapshot (goal.md J-01 step 5):
+    the full-suite pass/skip/failed counts and ``tsc --noEmit`` error count are supplied by the
+    caller (an operator/CLI act that actually ran those -- this function never shells out to
+    pytest/tsc itself, exactly like every other recording act in this codebase is a distinct step
+    from the GET route that later serves it verbatim); ``config_fingerprint`` likewise comes from
+    the caller's own ``CONFIG.config_fingerprint()`` read. The six ``referee_*.py`` module hashes
+    ARE computed here (cheap, deterministic file reads, no external process). Overwrites any prior
+    snapshot at this path -- re-recording is itself an explicit operator act, never something a
+    GET triggers (spec §0 / goal.md T-8: page loads never compute)."""
+    research_path = Path(research_dir)
+    referee_hashes = {name: _hash_file(research_path / name) for name in REFEREE_MODULES}
+    snapshot = {
+        "backend_suite": {"passed": suite_passed, "skipped": suite_skipped, "failed": suite_failed},
+        "tsc_error_count": tsc_error_count,
+        "config_fingerprint": config_fingerprint,
+        "referee_module_sha256": referee_hashes,
+    }
+    out_dir = Path(foundry_dir)
+    out_dir.mkdir(parents=True, exist_ok=True)
+    out_path = out_dir / _BASELINE_FILENAME
+    out_path.write_text(json.dumps(snapshot, sort_keys=True, indent=2), encoding="utf-8")
+    return snapshot
+
+
+def read_era_open_baseline(foundry_dir: str | Path) -> dict | None:
+    """Reads the persisted snapshot VERBATIM -- no recomputation, ever (this is the only function
+    the GET route calls). ``None`` when no snapshot has been recorded yet (a fresh install before
+    the operator recording act ran) -- never a fabricated placeholder."""
+    path = Path(foundry_dir) / _BASELINE_FILENAME
+    if not path.exists():
+        return None
+    return json.loads(path.read_text(encoding="utf-8"))
+
+
+# --- era/session identity (goal.md J-01 step 2: distinguishes Rapid Microscope, closed
+# foundation, from the Foundry, the active era) -----------------------------------------------
+
+FOUNDRY_SPEC_VERSION = "v1"  # docs/hypothesis-foundry-spec.md's own revision tag (top of that file)
+PREVIOUS_ERA = "rapid-microscope"
+PREVIOUS_ERA_STATUS = "closed"
+CURRENT_ERA = "hypothesis-foundry"
+CURRENT_ERA_STATUS = "active"
+
+
+def foundry_era_identity() -> dict:
+    """A plain, static dict -- never derived from anything computed per-request, so
+    ``GET /research/desk/micro/foundry`` can serve it on every call with no recomputation
+    (goal.md's own page-load-never-computes convention)."""
+    return {
+        "previous_era": PREVIOUS_ERA,
+        "previous_era_status": PREVIOUS_ERA_STATUS,
+        "current_era": CURRENT_ERA,
+        "current_era_status": CURRENT_ERA_STATUS,
+        "foundry_spec_version": FOUNDRY_SPEC_VERSION,
+    }
diff --git a/apps/backend/scripts/record_foundry_era_open_baseline.py b/apps/backend/scripts/record_foundry_era_open_baseline.py
new file mode 100644
index 00000000..764790d5
--- /dev/null
+++ b/apps/backend/scripts/record_foundry_era_open_baseline.py
@@ -0,0 +1,82 @@
+"""Records the Hypothesis Foundry era-open baseline snapshot ONCE (goal-hypothesis-foundry-iter-1,
+J-01 step 5) -- the full backend suite pass/skip/failed counts and ``tsc --noEmit`` error count are
+supplied by the CALLER as CLI flags. This script deliberately never shells out to ``pytest``/
+``tsc`` itself: running the full suite and the TypeScript compile is the operator's own
+already-necessary verification act (the SAME numbers the dev handoff's "Tests Run" section
+reports), and re-running them a second time from inside this script would be slow, redundant, and
+would risk a DIFFERENT number than what was actually verified. ``config_fingerprint`` is read live
+from ``CONFIG`` (never hand-typed); the six ``referee_*.py`` module SHA-256 hashes are computed
+here directly (cheap, deterministic file reads -- see
+``foundry_source_registry.record_era_open_baseline``'s own docstring).
+
+Writes into the REAL project dataset-dir sibling (``apps/backend/.data/foundry/``, or the
+``TAPEOLOGY_FOUNDRY_DIR``/``TAPEOLOGY_DATASET_DIR`` overrides if set) -- this is era build/test
+provenance metadata, never market/tick data, so it belongs beside the other Rapid-Microscope-era
+sibling directories (``vault``, ``micro_graduation``, ...) under the SAME real store.
+
+Idempotent-by-explicit-act: re-running this script overwrites the prior snapshot (an intentional
+operator re-recording, never something a page load triggers -- ``GET /research/desk/micro/foundry``
+only ever READS the persisted file).
+
+Run from ``apps/backend`` after a full green suite + clean ``tsc --noEmit``:
+
+    .venv/bin/python -m pytest tests/ -q --junitxml=/tmp/junit.xml   # note the counts
+    (cd ../frontend && ./node_modules/.bin/tsc --noEmit)             # note the error count
+    .venv/bin/python scripts/record_foundry_era_open_baseline.py \\
+        --passed 3788 --skipped 8 --failed 0 --tsc-errors 0
+"""
+
+from __future__ import annotations
+
+import argparse
+import sys
+from pathlib import Path
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+sys.path.insert(0, str(BACKEND_DIR))
+
+from app.env import load_env  # noqa: E402
+
+load_env()
+
+from app.config import CONFIG  # noqa: E402
+from app.research.foundry_source_registry import (  # noqa: E402
+    record_era_open_baseline,
+    resolve_foundry_dir,
+)
+
+
+def main(argv: list[str] | None = None) -> int:
+    parser = argparse.ArgumentParser(description=__doc__)
+    parser.add_argument("--passed", type=int, required=True, help="pytest pass count")
+    parser.add_argument("--skipped", type=int, required=True, help="pytest skip count")
+    parser.add_argument("--failed", type=int, required=True, help="pytest failure count")
+    parser.add_argument("--tsc-errors", type=int, required=True, help="`tsc --noEmit` error count")
+    args = parser.parse_args(argv)
+
+    dataset_dir = CONFIG.dataset_dir_resolved()
+    foundry_dir = resolve_foundry_dir(dataset_dir)
+    research_dir = BACKEND_DIR / "app" / "research"
+
+    snapshot = record_era_open_baseline(
+        foundry_dir,
+        suite_passed=args.passed,
+        suite_skipped=args.skipped,
+        suite_failed=args.failed,
+        tsc_error_count=args.tsc_errors,
+        config_fingerprint=CONFIG.config_fingerprint(),
+        research_dir=research_dir,
+    )
+    print(
+        f"[record-foundry-era-open-baseline] recorded to {foundry_dir}:\n"
+        f"  backend_suite={snapshot['backend_suite']}\n"
+        f"  tsc_error_count={snapshot['tsc_error_count']}\n"
+        f"  config_fingerprint={snapshot['config_fingerprint']}\n"
+        f"  referee_module_sha256={snapshot['referee_module_sha256']}",
+        file=sys.stderr,
+    )
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/tests/test_foundry_compiler.py b/apps/backend/tests/test_foundry_compiler.py
new file mode 100644
index 00000000..fdba6f9b
--- /dev/null
+++ b/apps/backend/tests/test_foundry_compiler.py
@@ -0,0 +1,313 @@
+"""``foundry_compiler.py`` -- the Hypothesis Foundry's ``CandidateSpec`` schema and batch compiler
+(goal-hypothesis-foundry-iter-1). Test-first contract: TC-3, TC-4, TC-10, TC-11 in
+``docs/phases/goal-hypothesis-foundry-iter-1.md``. TC-5 through TC-9/TC-12 (the blocked/aliased/
+lint cases) live in ``test_foundry_source_registry.py`` -- those need no ``CandidateBlueprint``."""
+
+from __future__ import annotations
+
+import dataclasses
+
+import pytest
+
+from app.research import foundry_compiler as fc
+from app.research import foundry_source_registry as fsr
+from app.research import scout
+
+
+def _span(text: str, excerpt: str) -> fsr.QuotedSpan:
+    return fsr.QuotedSpan(text=text, location=excerpt.index(text))
+
+
+def _blueprint(horizon: str = "trades_20", sidedness: str = "long") -> fc.CandidateBlueprint:
+    return fc.CandidateBlueprint(
+        population=fc.CandidatePopulation(
+            structure_context_kind="band_wall_touch", side_filter=None, setup_context_id=None
+        ),
+        coordinates=(
+            fc.CandidateCoordinate(
+                feature_construct_id="quote_imbalance",
+                semantic_role="primary",
+                transform_orientation="positive_zero_boundary",
+                threshold_corner_predicate="quote_imbalance > 0",
+                threshold_provenance=fsr.THRESHOLD_NATURAL_SEMANTIC_BOUNDARY,
+                aggressor_derived=False,
+                unit_basis="ratio",
+                anchor_at="touch",
+                available_at="touch",
+            ),
+        ),
+        relation=fc.CandidateRelation(kind="direct_scalar_membership"),
+        membership_corner="quote_imbalance > 0",
+        outcome=fc.CandidateOutcome(horizon_key=horizon, sidedness=sidedness),
+    )
+
+
+# --- TC-3: the natural-boundary-scalar fixture compiles to a real CandidateSpec with a non-null
+# candidate_spec_hash. -----------------------------------------------------------------------------
+
+
+def test_tc3_natural_boundary_scalar_compiles_to_a_candidate_spec_with_a_hash():
+    excerpt = "A signed variable's zero boundary is bid-heavy when quote_imbalance is positive."
+    span_text = "signed variable's zero boundary is bid-heavy when quote_imbalance is positive"
+    record = fsr.SourceRecord(
+        source_id="fixture-natural-boundary",
+        source_path="docs/fixtures/mechanism.md",
+        section_ref="2.3",
+        quoted_spans=(_span(span_text, excerpt),),
+        source_excerpt=excerpt,
+        mechanism_statement="quote imbalance zero-crossing implies bid-heavy",
+        operative_formula_refs=("quote_imbalance",),
+        direction_derivation="positive quote_imbalance implies bid-heavy -> long",
+        comparator_derivation="complement_within_same_eligible_population",
+        audit_note="zero boundary intrinsic to the signed variable's own definition, per quoted text",
+        threshold_provenance=fsr.THRESHOLD_NATURAL_SEMANTIC_BOUNDARY,
+    )
+    result = fc.compile_sources(
+        [record],
+        foundry_spec_version="v1",
+        epoch_id="hermetic-fixture-epoch",
+        blueprints={"fixture-natural-boundary": _blueprint()},
+    )
+    assert result.dispositions["fixture-natural-boundary"] == fsr.DISPOSITION_COMPILED
+    spec = result.candidate_specs["fixture-natural-boundary"]
+    assert spec.candidate_spec_hash  # non-empty / non-null
+    assert spec.foundry_family_variant_count == 1
+    assert spec.outcome.horizon_key == "trades_20"
+
+
+# --- TC-4: two explicitly-frozen legal variants in one family share foundry_family_id, both carry
+# foundry_family_variant_count == 2, and have distinct variant_ordinal values. --------------------
+
+
+def _variant_record(source_id: str, ordinal: int) -> fsr.SourceRecord:
+    excerpt = f"{source_id}: trades_20 and trades_100 are both already-legal outcome horizons."
+    span_text = "trades_20 and trades_100 are both already-legal outcome horizons"
+    return fsr.SourceRecord(
+        source_id=source_id,
+        source_path="docs/fixtures/mechanism.md",
+        section_ref="4.1",
+        quoted_spans=(_span(span_text, excerpt),),
+        source_excerpt=excerpt,
+        mechanism_statement="two legal horizon variants of one mechanism",
+        operative_formula_refs=("cumulative_delta",),
+        direction_derivation="positive cumulative_delta -> long",
+        comparator_derivation="complement_within_same_eligible_population",
+        audit_note="two already-defined legal outcome horizons enumerated per the frozen vocabulary, §2.1",
+        foundry_family_key="fixture-family-horizon-variants",
+        variant_ordinal=ordinal,
+    )
+
+
+def test_tc4_two_legal_variants_share_family_and_have_distinct_ordinals():
+    record_a = _variant_record("fixture-variant-a", 0)
+    record_b = _variant_record("fixture-variant-b", 1)
+    result = fc.compile_sources(
+        [record_a, record_b],
+        foundry_spec_version="v1",
+        epoch_id="hermetic-fixture-epoch",
+        blueprints={
+            "fixture-variant-a": _blueprint(horizon="trades_20"),
+            "fixture-variant-b": _blueprint(horizon="trades_100"),
+        },
+    )
+    spec_a = result.candidate_specs["fixture-variant-a"]
+    spec_b = result.candidate_specs["fixture-variant-b"]
+    assert spec_a.foundry_family_id == spec_b.foundry_family_id
+    assert spec_a.foundry_family_variant_count == 2
+    assert spec_b.foundry_family_variant_count == 2
+    assert spec_a.variant_ordinal != spec_b.variant_ordinal
+    assert {spec_a.variant_ordinal, spec_b.variant_ordinal} == {0, 1}
+
+
+def test_family_ordinal_collision_is_refused():
+    record_a = _variant_record("fixture-collide-a", 0)
+    record_b = _variant_record("fixture-collide-b", 0)  # SAME ordinal, same family -- illegal
+    with pytest.raises(fc.FamilyOrdinalCollision):
+        fc.compile_sources(
+            [record_a, record_b],
+            foundry_spec_version="v1",
+            epoch_id="hermetic-fixture-epoch",
+            blueprints={
+                "fixture-collide-a": _blueprint(),
+                "fixture-collide-b": _blueprint(),
+            },
+        )
+
+
+# --- TC-10: mutating one §3 science-affecting field (horizon_key) changes candidate_spec_hash;
+# shuffling field-serialization order does not. -----------------------------------------------
+
+
+def test_tc10_mutating_horizon_key_changes_the_hash():
+    excerpt = "The mechanism has one already-ratified horizon."
+    span_text = "one already-ratified horizon"
+    record = fsr.SourceRecord(
+        source_id="fixture-horizon-mutation",
+        source_path="docs/fixtures/mechanism.md",
+        section_ref="3.1",
+        quoted_spans=(_span(span_text, excerpt),),
+        source_excerpt=excerpt,
+        mechanism_statement="m",
+        operative_formula_refs=(),
+        direction_derivation="long",
+        comparator_derivation="complement",
+        audit_note="note",
+    )
+    result_20 = fc.compile_sources(
+        [record], foundry_spec_version="v1", epoch_id="e",
+        blueprints={"fixture-horizon-mutation": _blueprint(horizon="trades_20")},
+    )
+    result_100 = fc.compile_sources(
+        [record], foundry_spec_version="v1", epoch_id="e",
+        blueprints={"fixture-horizon-mutation": _blueprint(horizon="trades_100")},
+    )
+    hash_20 = result_20.candidate_specs["fixture-horizon-mutation"].candidate_spec_hash
+    hash_100 = result_100.candidate_specs["fixture-horizon-mutation"].candidate_spec_hash
+    assert hash_20 != hash_100
+
+
+def test_tc10_shuffling_canonical_field_order_does_not_change_the_hash():
+    excerpt = "one field-order fixture"
+    record = fsr.SourceRecord(
+        source_id="fixture-order",
+        source_path="docs/fixtures/mechanism.md",
+        section_ref="3.1",
+        quoted_spans=(),
+        source_excerpt=excerpt,
+        mechanism_statement="m",
+        operative_formula_refs=(),
+        direction_derivation="long",
+        comparator_derivation="complement",
+        audit_note="note",
+    )
+    result = fc.compile_sources(
+        [record], foundry_spec_version="v1", epoch_id="e", blueprints={"fixture-order": _blueprint()}
+    )
+    spec = result.candidate_specs["fixture-order"]
+    canonical = spec._canonical_fields()
+    import json
+
+    forward = json.dumps(canonical, sort_keys=True, default=str)
+    shuffled = json.dumps(dict(reversed(list(canonical.items()))), sort_keys=True, default=str)
+    assert forward == shuffled
+    assert spec.compute_hash() == spec.candidate_spec_hash
+
+
+def test_invalid_horizon_key_is_refused_at_outcome_construction():
+    """§3.1: only ``scout.HORIZON_KEYS`` members are legal -- verified from the real module, never
+    a second hard-coded set that could silently drift."""
+    with pytest.raises(ValueError):
+        fc.CandidateOutcome(horizon_key="clock_5m", sidedness="long")
+    assert "clock_5m" not in scout.HORIZON_KEYS  # sanity: this really is an illegal horizon
+
+
+def test_invalid_sidedness_is_refused():
+    with pytest.raises(ValueError):
+        fc.CandidateOutcome(horizon_key="trades_20", sidedness="sideways")
+
+
+# --- TC-11: an injected effect_bps/p_value/n fixture field (outside source inputs) cannot change
+# candidate_spec_hash or disposition. -----------------------------------------------------------
+
+
+def test_tc11_injected_outcome_fields_do_not_move_hash_or_disposition():
+    excerpt = "one non-science-field fixture"
+    record = fsr.SourceRecord(
+        source_id="fixture-extra",
+        source_path="docs/fixtures/mechanism.md",
+        section_ref="3.1",
+        quoted_spans=(),
+        source_excerpt=excerpt,
+        mechanism_statement="m",
+        operative_formula_refs=(),
+        direction_derivation="long",
+        comparator_derivation="complement",
+        audit_note="note",
+    )
+    record_with_extra = dataclasses.replace(
+        record, extra={"effect_bps": 37.5, "p_value": 0.002, "n": 812, "scout_verdict": "survive"}
+    )
+
+    result_plain = fc.compile_sources(
+        [record], foundry_spec_version="v1", epoch_id="e", blueprints={"fixture-extra": _blueprint()}
+    )
+    result_extra = fc.compile_sources(
+        [record_with_extra], foundry_spec_version="v1", epoch_id="e",
+        blueprints={"fixture-extra": _blueprint()},
+    )
+    assert result_plain.dispositions["fixture-extra"] == result_extra.dispositions["fixture-extra"]
+    spec_plain = result_plain.candidate_specs["fixture-extra"]
+    spec_extra = result_extra.candidate_specs["fixture-extra"]
+    assert spec_plain.candidate_spec_hash == spec_extra.candidate_spec_hash
+
+
+# --- A record without a supplied blueprint (or one naming a deferred join) produces no
+# CandidateSpec this revision -- FROZEN_READY-incomplete, never approximated. ----------------------
+
+
+def test_compiled_record_with_no_blueprint_produces_no_candidate_spec():
+    excerpt = "one no-blueprint fixture"
+    record = fsr.SourceRecord(
+        source_id="fixture-no-blueprint",
+        source_path="docs/fixtures/mechanism.md",
+        section_ref="3.1",
+        quoted_spans=(),
+        source_excerpt=excerpt,
+        mechanism_statement="m",
+        operative_formula_refs=(),
+        direction_derivation="long",
+        comparator_derivation="complement",
+        audit_note="note",
+    )
+    result = fc.compile_sources([record], foundry_spec_version="v1", epoch_id="e", blueprints={})
+    assert result.dispositions["fixture-no-blueprint"] == fsr.DISPOSITION_COMPILED
+    assert "fixture-no-blueprint" not in result.candidate_specs
+
+
+def test_compiled_record_with_a_deferred_coordinate_produces_no_candidate_spec_this_revision():
+    excerpt = "one deferred-join fixture"
+    record = fsr.SourceRecord(
+        source_id="fixture-deferred",
+        source_path="docs/fixtures/mechanism.md",
+        section_ref="3.1",
+        quoted_spans=(),
+        source_excerpt=excerpt,
+        mechanism_statement="refill_consistent deferred conjunction",
+        operative_formula_refs=(),
+        direction_derivation="long",
+        comparator_derivation="complement",
+        audit_note="note",
+    )
+    deferred_blueprint = fc.CandidateBlueprint(
+        population=fc.CandidatePopulation(structure_context_kind="band_wall_touch", side_filter=None, setup_context_id=None),
+        coordinates=(
+            fc.CandidateCoordinate(
+                feature_construct_id="refill_consistent",
+                semantic_role="deferred_conjunct",
+                transform_orientation="boolean",
+                threshold_corner_predicate="refill_consistent == True",
+                threshold_provenance=fsr.THRESHOLD_NATURAL_SEMANTIC_BOUNDARY,
+                aggressor_derived=False,
+                unit_basis="boolean",
+                anchor_at="touch",
+                available_at="resolution",
+                resolution_join_rule="deferred_via_observer_provenance_id",
+            ),
+        ),
+        relation=fc.CandidateRelation(kind="conjunction"),
+        membership_corner="refill_consistent == True",
+        outcome=fc.CandidateOutcome(horizon_key="trades_20", sidedness="long"),
+    )
+    assert deferred_blueprint.is_immediate() is False
+    result = fc.compile_sources(
+        [record], foundry_spec_version="v1", epoch_id="e", blueprints={"fixture-deferred": deferred_blueprint}
+    )
+    assert result.dispositions["fixture-deferred"] == fsr.DISPOSITION_COMPILED
+    assert "fixture-deferred" not in result.candidate_specs
+
+
+def test_compiler_hash_is_stable_and_non_empty():
+    h1 = fc.compiler_hash()
+    h2 = fc.compiler_hash()
+    assert h1 == h2
+    assert len(h1) == 64  # sha256 hex digest
diff --git a/apps/backend/tests/test_foundry_fixture_unit_regression.py b/apps/backend/tests/test_foundry_fixture_unit_regression.py
new file mode 100644
index 00000000..c039b665
--- /dev/null
+++ b/apps/backend/tests/test_foundry_fixture_unit_regression.py
@@ -0,0 +1,37 @@
+"""Regression test for the QA-rig-crashing fixture bug the iter-0 evaluator found (goal-hypothesis-
+foundry-iter-1, TC-2): ``seed_micro_graduation_iter18_fixture.py::_observation()`` was missing
+``value_unit`` on all 30 seeded observations, which trips ``walkforward.
+require_canonical_observation_units`` and prevents the scoped :8301 QA rig from ever starting
+(``lessons.md`` iter-0). TC-1 (the rig itself starts healthy on port 8301) is an infra-level check
+outside a unit test's reach -- verified operationally instead (see the dev handoff).
+
+This test does NOT touch the real ``.data`` store: it imports the seed script's own pure
+functions and calls the SAME production ``walkforward.require_canonical_observation_units`` guard
+directly, never spinning up a backend or writing any file."""
+
+from __future__ import annotations
+
+from app.research import walkforward as wf
+from scripts import seed_micro_graduation_iter18_fixture as seed_script
+
+
+def test_observation_declares_the_canonical_return_bps_unit():
+    row = seed_script._observation("2026-06-09", "PGQA", 10.0)
+    assert row["value_unit"] == wf.WF_OBSERVATION_UNIT == "return_bps"
+
+
+def test_tc2_thirty_seeded_observations_pass_the_canonical_unit_guard_without_raising():
+    observations = seed_script._passing_observations()
+    assert len(observations) == 30
+    # Must not raise UnitMismatchError -- the exact failure the iter-0 evaluator reproduced at
+    # `seed_micro_graduation_iter18_fixture.py:175` before this fix.
+    wf.require_canonical_observation_units(observations)
+
+
+def test_seeded_observation_values_are_unchanged_only_the_unit_declaration_was_added():
+    """The bug was a missing DECLARATION, never a wrong unit (docstring rationale in the fix
+    itself): the 30 values still average to exactly 10.0, clearing the fixture's own 5.0 bps
+    floor in the registered `long` direction."""
+    values = [row["value"] for row in seed_script._passing_observations()]
+    assert len(values) == 30
+    assert sum(values) / len(values) == 10.0
diff --git a/apps/backend/tests/test_foundry_route.py b/apps/backend/tests/test_foundry_route.py
new file mode 100644
index 00000000..90076087
--- /dev/null
+++ b/apps/backend/tests/test_foundry_route.py
@@ -0,0 +1,85 @@
+"""``GET /research/desk/micro/foundry`` (goal-hypothesis-foundry-iter-1, J-01). TC-13/TC-14/TC-15
+in ``docs/phases/goal-hypothesis-foundry-iter-1.md``: the era-open baseline is recorded once and
+served byte-identically across calls; ``source_registry_hash`` always renders ``null`` with an
+explicit ``not_yet_generated`` status (the real registry does not exist until J-06); the route
+never 404s/500s before the operator recording act has run."""
+
+from __future__ import annotations
+
+from fastapi.testclient import TestClient
+
+from app.config import CONFIG
+from app.main import app
+from app.research import foundry_source_registry as fsr
+
+
+def _scope_dataset_dir(tmp_path, monkeypatch):
+    dataset_dir = tmp_path / "datasets"
+    dataset_dir.mkdir()
+    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(dataset_dir))
+    monkeypatch.delenv("TAPEOLOGY_FOUNDRY_DIR", raising=False)
+    return dataset_dir
+
+
+def test_foundry_route_before_any_recording_serves_a_null_baseline_never_a_404(tmp_path, monkeypatch):
+    _scope_dataset_dir(tmp_path, monkeypatch)
+    with TestClient(app) as client:
+        response = client.get("/research/desk/micro/foundry")
+    assert response.status_code == 200
+    body = response.json()
+    assert body["era_open_baseline"] is None
+    assert body["era"]["previous_era"] == "rapid-microscope"
+    assert body["era"]["previous_era_status"] == "closed"
+    assert body["era"]["current_era"] == "hypothesis-foundry"
+    assert body["era"]["current_era_status"] == "active"
+    assert body["era"]["foundry_spec_version"] == fsr.FOUNDRY_SPEC_VERSION
+
+
+def test_tc15_source_registry_hash_renders_null_not_yet_generated_on_two_calls(tmp_path, monkeypatch):
+    _scope_dataset_dir(tmp_path, monkeypatch)
+    with TestClient(app) as client:
+        first = client.get("/research/desk/micro/foundry").json()
+        second = client.get("/research/desk/micro/foundry").json()
+    for body in (first, second):
+        assert body["source_registry_hash"] is None
+        assert body["source_registry_status"] == "not_yet_generated"
+
+
+def test_tc13_route_serves_the_recorded_baseline_byte_identically_across_two_calls(tmp_path, monkeypatch):
+    dataset_dir = _scope_dataset_dir(tmp_path, monkeypatch)
+    foundry_dir = fsr.resolve_foundry_dir(str(dataset_dir))
+    research_dir = str((tmp_path.parent / "app_research_stub"))
+    import pathlib
+
+    research_path = pathlib.Path(research_dir)
+    research_path.mkdir(parents=True, exist_ok=True)
+    for name in fsr.REFEREE_MODULES:
+        (research_path / name).write_text(f"# stub {name}\n", encoding="utf-8")
+
+    fsr.record_era_open_baseline(
+        foundry_dir,
+        suite_passed=3762,
+        suite_skipped=8,
+        suite_failed=0,
+        tsc_error_count=0,
+        config_fingerprint=CONFIG.config_fingerprint(),
+        research_dir=research_path,
+    )
+
+    with TestClient(app) as client:
+        first = client.get("/research/desk/micro/foundry").json()
+        second = client.get("/research/desk/micro/foundry").json()
+
+    assert first == second
+    assert first["era_open_baseline"]["backend_suite"] == {"passed": 3762, "skipped": 8, "failed": 0}
+    assert first["era_open_baseline"]["config_fingerprint"] == CONFIG.config_fingerprint()
+    assert set(first["era_open_baseline"]["referee_module_sha256"]) == set(fsr.REFEREE_MODULES)
+
+
+def test_foundry_route_is_get_only_no_mutation_endpoint_exists():
+    """Product Shape / anti-goals: the Foundry surface is read-only this era -- there must be no
+    ``POST``/``PUT``/``DELETE`` sibling under ``/research/desk/micro/foundry``."""
+    paths = app.openapi()["paths"]
+    assert "/research/desk/micro/foundry" in paths
+    ops = paths["/research/desk/micro/foundry"]
+    assert set(ops.keys()) == {"get"}
diff --git a/apps/backend/tests/test_foundry_source_registry.py b/apps/backend/tests/test_foundry_source_registry.py
new file mode 100644
index 00000000..8316d6c8
--- /dev/null
+++ b/apps/backend/tests/test_foundry_source_registry.py
@@ -0,0 +1,410 @@
+"""``foundry_source_registry.py`` -- the Hypothesis Foundry's source registry (goal-hypothesis-
+foundry-iter-1). Test-first contract: TC-5 through TC-9 and TC-12/TC-13 in
+``docs/phases/goal-hypothesis-foundry-iter-1.md`` (the blocked/aliased/proxy dispositions, the
+exact-quote lint, and the era-open baseline snapshot). ``test_foundry_compiler.py`` covers TC-3/
+TC-4/TC-10/TC-11 (the compileable/family/hash cases), since those need the compiler module too.
+
+Fixtures cover exactly the seven hermetic source archetypes ``docs/goal.md`` J-02 step 2 names.
+Each fixture's ``source_excerpt``/``quoted_spans`` are deliberately synthetic sentences invented
+for this test -- never real ratified repository text -- since J-02 step 2 explicitly scopes this
+iteration to compiler-RULE machinery proven on hermetic fixtures, not the real 11 required source
+objects (that is J-06)."""
+
+from __future__ import annotations
+
+import json
+
+import pytest
+
+from app.research import foundry_source_registry as fsr
+
+
+def _span(text: str, excerpt: str) -> fsr.QuotedSpan:
+    """A ``QuotedSpan`` located at ``text``'s real offset inside ``excerpt`` -- computed, never
+    hand-counted, so a fixture's own wording can change without silently mis-locating the span."""
+    return fsr.QuotedSpan(text=text, location=excerpt.index(text))
+
+
+# --- TC-3 (compileable natural-boundary scalar) is exercised in test_foundry_compiler.py, since
+# it also needs a CandidateBlueprint. This file keeps the disposition-only half of that fixture
+# for the registry-level assertions (TC-13-adjacent: disposition alone, no CandidateSpec). -------
+
+
+def test_natural_boundary_scalar_compiles():
+    excerpt = "A signed variable's zero boundary is bid-heavy when quote_imbalance is positive."
+    span_text = "signed variable's zero boundary is bid-heavy when quote_imbalance is positive"
+    record = fsr.SourceRecord(
+        source_id="fixture-natural-boundary",
+        source_path="docs/fixtures/mechanism.md",
+        section_ref="2.3",
+        quoted_spans=(_span(span_text, excerpt),),
+        source_excerpt=excerpt,
+        mechanism_statement="quote imbalance zero-crossing implies bid-heavy",
+        operative_formula_refs=("quote_imbalance",),
+        direction_derivation="positive quote_imbalance implies bid-heavy -> long",
+        comparator_derivation="complement_within_same_eligible_population",
+        audit_note="zero boundary intrinsic to the signed variable's own definition, per quoted text",
+        threshold_provenance=fsr.THRESHOLD_NATURAL_SEMANTIC_BOUNDARY,
+    )
+    assert fsr.compile_source_disposition(record) == fsr.DISPOSITION_COMPILED
+
+
+# --- TC-5: unresolved magnitude word -> BLOCKED_SPEC_GAP, disposition only (no CandidateSpec). ---
+
+
+def test_unresolved_magnitude_word_blocks_spec_gap():
+    excerpt = "A collapse in impact defines a high-aggression signal at the wall."
+    span_text = "collapse in impact defines a high-aggression signal"
+    record = fsr.SourceRecord(
+        source_id="fixture-magnitude-word",
+        source_path="docs/fixtures/mechanism.md",
+        section_ref="1.9",
+        quoted_spans=(_span(span_text, excerpt),),
+        source_excerpt=excerpt,
+        mechanism_statement="impact collapse at the wall implies reversal",
+        operative_formula_refs=("impact_efficiency",),
+        direction_derivation="collapse implies reversal -> long",
+        comparator_derivation="complement_within_same_eligible_population",
+        audit_note="'collapse'/'high' are undefined magnitude words -- no ratified numeric meaning exists",
+        unresolved_magnitude_words=("collapse", "high"),
+    )
+    assert fsr.compile_source_disposition(record) == fsr.DISPOSITION_BLOCKED_SPEC_GAP
+
+
+# --- TC-6: proxy-only -> ALIASED_PROXY_ONLY, do_not preserved. -----------------------------------
+
+
+def test_proxy_only_source_aliases_and_preserves_do_not():
+    excerpt = "The frozen pilot proxy stands in for Study 1's impact_efficiency mechanism."
+    span_text = "frozen pilot proxy stands in for Study 1's impact_efficiency mechanism"
+    record = fsr.SourceRecord(
+        source_id="fixture-proxy",
+        source_path="docs/fixtures/mechanism.md",
+        section_ref="1.1-proxy",
+        quoted_spans=(_span(span_text, excerpt),),
+        source_excerpt=excerpt,
+        mechanism_statement="pilot proxy candidate request for Study 1",
+        operative_formula_refs=("impact_efficiency_pilot_proxy",),
+        direction_derivation="long",
+        comparator_derivation="complement_within_same_eligible_population",
+        audit_note="a frozen pilot proxy is provenance only, never the full mechanism",
+        proxy_of=fsr.ProxyDeclaration(
+            parked_study_source_id="study-1-range-wall-failed-aggression",
+            do_not="do_not_claim_full_study_1_mechanism",
+        ),
+    )
+    assert fsr.compile_source_disposition(record) == fsr.DISPOSITION_ALIASED_PROXY_ONLY
+    assert record.proxy_of.do_not == "do_not_claim_full_study_1_mechanism"
+
+
+# --- TC-7: unsupported statistic -> BLOCKED_UNSUPPORTED_STUDY_FORM. ------------------------------
+
+
+def test_unsupported_statistic_blocks_study_form():
+    excerpt = "A shuffled-side persistence statistic is not a supported Scout study form here."
+    span_text = "shuffled-side persistence statistic is not a supported Scout study form"
+    record = fsr.SourceRecord(
+        source_id="fixture-unsupported-stat",
+        source_path="docs/fixtures/mechanism.md",
+        section_ref="9.6",
+        quoted_spans=(_span(span_text, excerpt),),
+        source_excerpt=excerpt,
+        mechanism_statement="shuffled-side persistence statistic",
+        operative_formula_refs=(),
+        direction_derivation="long",
+        comparator_derivation=fsr.BLOCKED_UNSUPPORTED_STUDY_FORM_SENTINEL,
+        audit_note="the existing Scout screen has no shuffled-side permutation null; unsupported study form",
+    )
+    assert fsr.compile_source_disposition(record) == fsr.DISPOSITION_BLOCKED_UNSUPPORTED_STUDY_FORM
+
+
+# --- TC-8: alias/supersession -> ALIASED_VARIANT_VOCABULARY (or ALIASED_LINEAGE), superseded_fields
+# cite the newer ref. -------------------------------------------------------------------------
+
+
+def test_alias_supersession_cites_the_newer_ref():
+    excerpt = "Card 9.7 event-time windows are now embodied by the current frozen feature windows."
+    span_text = "event-time windows are now embodied by the current frozen feature windows"
+    record = fsr.SourceRecord(
+        source_id="fixture-alias-older",
+        source_path="docs/fixtures/mechanism.md",
+        section_ref="9.7",
+        quoted_spans=(_span(span_text, excerpt),),
+        source_excerpt=excerpt,
+        mechanism_statement="event-time feature windows",
+        operative_formula_refs=("event_time_window",),
+        direction_derivation="long",
+        comparator_derivation="complement_within_same_eligible_population",
+        audit_note="Card 9.7 is variant vocabulary for an already-frozen current feature window, per §1.3",
+        superseded_fields={"event_time_window": "docs/rapid-validation-spec.md#feature-windows"},
+        supersession=fsr.SupersessionDeclaration(
+            newer_source_ref="docs/rapid-validation-spec.md#feature-windows",
+            alias_kind=fsr.DISPOSITION_ALIASED_VARIANT_VOCABULARY,
+        ),
+    )
+    assert fsr.compile_source_disposition(record) == fsr.DISPOSITION_ALIASED_VARIANT_VOCABULARY
+    assert record.superseded_fields["event_time_window"] == "docs/rapid-validation-spec.md#feature-windows"
+
+
+def test_alias_supersession_may_select_lineage_instead():
+    record = fsr.SourceRecord(
+        source_id="fixture-alias-lineage",
+        source_path="docs/fixtures/mechanism.md",
+        section_ref="9.4",
+        quoted_spans=(),
+        source_excerpt="",
+        mechanism_statement="burst/climax lineage",
+        operative_formula_refs=(),
+        direction_derivation="long",
+        comparator_derivation="complement",
+        audit_note="distinct lineage id, same underlying exhaustion mechanism as Study 3",
+        supersession=fsr.SupersessionDeclaration(
+            newer_source_ref="study-3-capitulation-exhaustion", alias_kind=fsr.DISPOSITION_ALIASED_LINEAGE
+        ),
+    )
+    assert fsr.compile_source_disposition(record) == fsr.DISPOSITION_ALIASED_LINEAGE
+
+
+def test_supersession_alias_kind_rejects_a_non_alias_disposition():
+    with pytest.raises(ValueError):
+        fsr.SupersessionDeclaration(newer_source_ref="x", alias_kind=fsr.DISPOSITION_COMPILED)
+
+
+# --- TC-9: directionless mechanism -> BLOCKED_DIRECTION. -----------------------------------------
+
+
+def test_directionless_mechanism_blocks_direction():
+    excerpt = "The mechanism describes co-occurrence with no stated directional implication."
+    span_text = "co-occurrence with no stated directional implication"
+    record = fsr.SourceRecord(
+        source_id="fixture-directionless",
+        source_path="docs/fixtures/mechanism.md",
+        section_ref="9.5",
+        quoted_spans=(_span(span_text, excerpt),),
+        source_excerpt=excerpt,
+        mechanism_statement="spread-dynamics regime co-occurrence",
+        operative_formula_refs=("spread_regime",),
+        direction_derivation=fsr.BLOCKED_DIRECTION_SENTINEL,
+        comparator_derivation="complement_within_same_eligible_population",
+        audit_note="the quoted text states co-occurrence only; no mechanical long/short implication exists",
+    )
+    assert fsr.compile_source_disposition(record) == fsr.DISPOSITION_BLOCKED_DIRECTION
+
+
+# --- TC-12: exact-quote lint fails closed on a mismatched span; passes over correct ones. --------
+
+
+def _good_record(source_id: str) -> fsr.SourceRecord:
+    excerpt = f"{source_id}: the quoted span below exists verbatim in this excerpt."
+    span_text = "the quoted span below exists verbatim in this excerpt"
+    return fsr.SourceRecord(
+        source_id=source_id,
+        source_path="docs/fixtures/mechanism.md",
+        section_ref="0",
+        quoted_spans=(_span(span_text, excerpt),),
+        source_excerpt=excerpt,
+        mechanism_statement="m",
+        operative_formula_refs=(),
+        direction_derivation="long",
+        comparator_derivation="complement",
+        audit_note="note",
+    )
+
+
+def test_lint_passes_over_exact_spans():
+    fsr.lint_quoted_spans([_good_record("a"), _good_record("b")])  # must not raise
+
+
+def test_lint_fails_closed_on_a_mismatched_span():
+    bad = fsr.SourceRecord(
+        source_id="fixture-bad-quote",
+        source_path="docs/fixtures/mechanism.md",
+        section_ref="0",
+        quoted_spans=(fsr.QuotedSpan(text="says Y", location=4),),
+        source_excerpt="The real text says X.",
+        mechanism_statement="m",
+        operative_formula_refs=(),
+        direction_derivation="long",
+        comparator_derivation="complement",
+        audit_note="note",
+    )
+    with pytest.raises(fsr.QuoteMismatch):
+        fsr.lint_quoted_spans([_good_record("a"), bad])
+
+
+def test_lint_fails_closed_on_correct_text_at_the_wrong_location():
+    """The text matches SOMEWHERE in the excerpt but not at the recorded offset -- must still
+    fail (never a "appears anywhere" fallback, per the module's own "deliberately does not use
+    keyword matching" rule)."""
+    excerpt = "wrong here, right over there: right"
+    bad = fsr.SourceRecord(
+        source_id="fixture-wrong-location",
+        source_path="docs/fixtures/mechanism.md",
+        section_ref="0",
+        quoted_spans=(fsr.QuotedSpan(text="right", location=0),),
+        source_excerpt=excerpt,
+        mechanism_statement="m",
+        operative_formula_refs=(),
+        direction_derivation="long",
+        comparator_derivation="complement",
+        audit_note="note",
+    )
+    with pytest.raises(fsr.QuoteMismatch):
+        fsr.lint_quoted_spans([bad])
+
+
+# --- Illegal threshold_provenance is refused at construction, never silently accepted. -----------
+
+
+def test_illegal_threshold_provenance_is_refused_at_construction():
+    with pytest.raises(ValueError):
+        fsr.SourceRecord(
+            source_id="fixture-illegal-threshold",
+            source_path="docs/fixtures/mechanism.md",
+            section_ref="0",
+            quoted_spans=(),
+            source_excerpt="",
+            mechanism_statement="m",
+            operative_formula_refs=(),
+            direction_derivation="long",
+            comparator_derivation="complement",
+            audit_note="note",
+            threshold_provenance="an_invented_fourth_category",
+        )
+
+
+def test_explicit_exclusion_must_be_a_closed_vocabulary_member():
+    with pytest.raises(ValueError):
+        fsr.SourceRecord(
+            source_id="fixture-illegal-exclusion",
+            source_path="docs/fixtures/mechanism.md",
+            section_ref="0",
+            quoted_spans=(),
+            source_excerpt="",
+            mechanism_statement="m",
+            operative_formula_refs=(),
+            direction_derivation="long",
+            comparator_derivation="complement",
+            audit_note="note",
+            explicit_exclusion="NOT_A_REAL_DISPOSITION",
+        )
+
+
+def test_explicit_exclusion_short_circuits_every_other_rule():
+    """A source explicitly marked excluded reaches its exclusion disposition even if it ALSO
+    carries fields that would otherwise block/alias it -- exclusion is decided first (§2's fixed
+    precedence, step 0)."""
+    record = fsr.SourceRecord(
+        source_id="fixture-excluded",
+        source_path="docs/fixtures/mechanism.md",
+        section_ref="9.1",
+        quoted_spans=(),
+        source_excerpt="",
+        mechanism_statement="m",
+        operative_formula_refs=(),
+        direction_derivation=fsr.BLOCKED_DIRECTION_SENTINEL,
+        comparator_derivation="complement",
+        audit_note="Card 9.1/Study 2 was previously killed -- may not be recompiled",
+        explicit_exclusion=fsr.DISPOSITION_EXCLUDED_PREVIOUSLY_KILLED,
+    )
+    assert fsr.compile_source_disposition(record) == fsr.DISPOSITION_EXCLUDED_PREVIOUSLY_KILLED
+
+
+# --- The closed vocabulary itself. ----------------------------------------------------------------
+
+
+def test_disposition_vocabulary_is_exactly_fourteen_members():
+    assert len(fsr.SOURCE_DISPOSITIONS) == 14
+    for name in (
+        "COMPILED", "ALIASED_PROXY_ONLY", "ALIASED_VARIANT_VOCABULARY", "ALIASED_LINEAGE",
+        "EXCLUDED_PREVIOUSLY_KILLED", "EXCLUDED_PREREQUISITE_UNMET", "EXCLUDED_GATE_CLOSED",
+        "BLOCKED_SPEC_GAP", "BLOCKED_MISSING_PRIMITIVE", "BLOCKED_UNSUPPORTED_STUDY_FORM",
+        "BLOCKED_UNSUPPORTED_RELATION", "BLOCKED_DIRECTION", "BLOCKED_VARIANT_EXPLOSION",
+        "BLOCKED_UNIT_CONTRACT",
+    ):
+        assert name in fsr.SOURCE_DISPOSITIONS
+
+
+# --- source_registry_hash: content-sensitive, order-invariant, excludes `extra`. -----------------
+
+
+def test_source_registry_hash_changes_when_a_record_changes():
+    import dataclasses
+
+    a = _good_record("a")
+    b = _good_record("b")
+    hash_ab = fsr.source_registry_hash([a, b])
+    b_mutated = dataclasses.replace(b, mechanism_statement="a different mechanism entirely")
+    hash_ab_mutated = fsr.source_registry_hash([a, b_mutated])
+    assert hash_ab != hash_ab_mutated
+
+
+def test_source_registry_hash_ignores_extra_field():
+    import dataclasses
+
+    a = _good_record("a")
+    a_extra = dataclasses.replace(a, extra={"effect_bps": 99.0, "p_value": 0.0001, "n": 10_000})
+    assert fsr.source_registry_hash([a]) == fsr.source_registry_hash([a_extra])
+
+
+# --- Era-open baseline: recorded once, served verbatim, never recomputed on read. ----------------
+
+
+def test_era_open_baseline_round_trips_byte_identically_across_two_reads(tmp_path):
+    foundry_dir = tmp_path / "foundry"
+    research_dir = tmp_path / "research"
+    research_dir.mkdir()
+    for name in fsr.REFEREE_MODULES:
+        (research_dir / name).write_text(f"# fixture stand-in for {name}\n", encoding="utf-8")
+
+    recorded = fsr.record_era_open_baseline(
+        foundry_dir,
+        suite_passed=3762,
+        suite_skipped=8,
+        suite_failed=0,
+        tsc_error_count=0,
+        config_fingerprint="08e471b10130e1e2",
+        research_dir=research_dir,
+    )
+    assert recorded["backend_suite"] == {"passed": 3762, "skipped": 8, "failed": 0}
+    assert recorded["config_fingerprint"] == "08e471b10130e1e2"
+    assert set(recorded["referee_module_sha256"]) == set(fsr.REFEREE_MODULES)
+
+    first_read = fsr.read_era_open_baseline(foundry_dir)
+    second_read = fsr.read_era_open_baseline(foundry_dir)
+    assert first_read == second_read == recorded
+    # Byte-identical on-disk persistence too (TC-13: "serve byte-identically with no recomputation
+    # between calls") -- re-serializing the read-back dict reproduces the same bytes.
+    assert json.dumps(first_read, sort_keys=True) == json.dumps(second_read, sort_keys=True)
+
+
+def test_era_open_baseline_read_before_any_recording_is_none_never_fabricated(tmp_path):
+    assert fsr.read_era_open_baseline(tmp_path / "never-recorded") is None
+
+
+def test_era_open_baseline_hashes_a_real_referee_module_file(tmp_path):
+    """Uses the REAL ``app/research`` directory (not a fixture stand-in) so the recorded hash is
+    the actual current ``referee_registry.py`` content -- proves this isn't a fabricated digest."""
+    import hashlib
+    from pathlib import Path
+
+    research_dir = Path(__file__).resolve().parent.parent / "app" / "research"
+    foundry_dir = tmp_path / "foundry"
+    recorded = fsr.record_era_open_baseline(
+        foundry_dir, suite_passed=1, suite_skipped=0, suite_failed=0, tsc_error_count=0,
... [diff_bound] apps/backend/tests/test_foundry_source_registry.py: 16 more diff lines omitted — Read the file for full detail
diff --git a/docs/hypothesis-foundry-spec.md b/docs/hypothesis-foundry-spec.md
new file mode 100644
index 00000000..f3cbc9b9
--- /dev/null
+++ b/docs/hypothesis-foundry-spec.md
@@ -0,0 +1,316 @@
+# The Hypothesis Foundry Spec — candidate construction, freeze, and exhaustion
+
+> **This file is the implementation-ready methodology spec for the Foundry era's OWN new
+> machinery: source compilation, `CandidateSpec` construction, the generic interpreter, the
+> freeze barrier, and the deterministic exhaust runner.** It is subordinate to `docs/goal.md`
+> (the "Foundry Constitution", sections 1-12) — that file is the ratified owner-policy source of
+> truth; this file is its condensed, section-numbered implementation reference so a developer or
+> a source-record author can cite one short document instead of the whole goal file. Every
+> section number below (`§1`-`§12`) matches the corresponding goal.md Foundry Constitution
+> section, so a citation such as "spec §2.3" and "goal.md §2.3" name the identical rule. Where
+> this file and `docs/goal.md` ever appear to disagree, `docs/goal.md` wins — this file is a
+> derivation, never an amendment.
+>
+> **This spec explicitly does NOT restate or fork the Rapid Validation statistical decision
+> rail.** `scout.screen_candidate` (`app/research/scout.py`) remains the sole statistical judge:
+> its null, permutation count, alpha, minimum cell/session floors, concentration ceiling,
+> economic-floor multiple, fragility rule, and decision vocabulary are frozen by
+> `docs/rapid-validation-spec.md` and are referenced here by name only. This spec defines only
+> how a candidate is CONSTRUCTED, FROZEN, and EXHAUSTED before and after it reaches that
+> unchanged judge.
+>
+> **Revision v1 (2026-08-26, goal-hypothesis-foundry-iter-1).** First committed revision. Written
+> alongside the source-registry/CandidateSpec compiler machinery it documents
+> (`app/research/foundry_source_registry.py`, `app/research/foundry_compiler.py`) and proven only
+> against seven hermetic fixture source records — no real source object is authored under this
+> revision (that is `J-06`, Binding Execution Order step 6). A future revision that changes
+> scientific meaning re-keys forward (new spec hash, never a silent edit of a decision already
+> compiled under an earlier hash) exactly like `docs/rapid-validation-spec.md`'s own revision
+> discipline.
+
+---
+
+## 0. Scope of this document
+
+This spec fixes the meaning of:
+
+- the closed source-disposition vocabulary (`§7.1`) and the fields every checked-in source
+  record must carry (`§1.4`);
+- the owner meta-policy that decides, mechanically, whether a source compiles, aliases, excludes,
+  or blocks (`§2`);
+- the canonical `CandidateSpec` schema and its hash discipline (`§3`);
+- the generic candidate interpreter's population-symmetry and boolean-projection rules (`§4`);
+- the Foundry family/denominator contract (`§5`);
+- the economic-floor ordering rule (`§6`);
+- the source/variant state machines (`§7`);
+- the real epoch, manifest, and freeze-barrier contract (`§8`);
+- the deterministic exhaust runner's resume/replay contract (`§9`);
+- the evidence boundary this era may spend (`§10`);
+- what an `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN` label does and does not mean (`§11`).
+
+Sections are numbered to match `docs/goal.md`'s Foundry Constitution exactly. Only `§1.4`, `§2`,
+and `§3` are implemented in code as of this revision (`goal-hypothesis-foundry-iter-1`,
+`app/research/foundry_source_registry.py` + `app/research/foundry_compiler.py`); `§4`-`§9` are
+fixed in MEANING here so later iterations implement against a stable text, not a moving target,
+per the goal's own Binding Execution Order.
+
+---
+
+## 1. Source scope — finite and ratified
+
+The first real Foundry epoch may consider only source statements already ratified in the
+repository before `docs/goal.md` (this era's goal document) opened: the Rapid Microscope's parked
+Study 1 (`range_wall_failed_aggression`) and Study 3 (`capitulation_exhaustion`); Era 9 Wave-1
+Cards 9.3-9.7; the frozen Study 1/Study 3 pilot proxy declarations; and the explicit exclusions
+(Card 9.1/Study 2 previously-killed, Card 9.2 prerequisite-unmet, Cards 9.8-9.11 gate-closed, and
+everything outside this registry). See `docs/goal.md §1.1`/`§1.2` for the complete required-object
+list — this spec does not re-enumerate it, since goal.md is its single source of truth and
+duplicating it here would create two places a future reader could disagree about the list.
+
+### 1.3 Formula-scoped supersession law
+
+Supersession is **formula/meaning scoped, not card-number scoped**: when a later frozen Rapid
+Validation revision replaced an operational formula/window/threshold for a concept a card
+originally named, the newer frozen rule wins for that field and the older card value becomes
+provenance only (`ALIASED_VARIANT_VOCABULARY`/`ALIASED_LINEAGE`, never a silently-reused stale
+constant). Implemented as the `supersession` field on `SourceRecord`
+(`app/research/foundry_source_registry.py`): a non-`None` value marks the record as the OLDER
+member of a supersession pair, names the newer ref its `superseded_fields` cite, and selects
+which alias disposition applies.
+
+### 1.4 Source-record decision audit
+
+Every checked-in source record — real or hermetic-fixture — carries exactly these fields (the
+`SourceRecord` dataclass in `app/research/foundry_source_registry.py` is this list, verbatim):
+
+| Field | Meaning |
+|---|---|
+| `source_id` | canonical, stable identifier |
+| `source_path`, `section_ref` | exact repository path + stable section/card/study reference |
+| `quoted_spans` | one or more `(text, location)` pairs — the exact quoted source span(s) and precise location backing every load-bearing decision below |
+| `source_excerpt` | the cited source text itself, so the exact-quote lint (`§1.4` mechanical lint, below) can verify a span against it without a live repository read |
+| `source_hash` | `sha256` of `source_excerpt` |
+| `mechanism_statement` | the mechanism this record represents, in the source's own terms |
+| `operative_formula_refs` | current operative formula/feature identifiers this record compiles against |
+| `superseded_fields` | mapping of field name → superseding ref, empty unless this record is superseded |
+| `foundry_family_key`, `variant_ordinal` | pre-declared family grouping + this variant's position within it (mechanical bookkeeping, never chosen by outcome) |
+| `threshold_provenance` | one of the three `§2.3` natural-boundary categories, or `None` when the mechanism needs no threshold |
+| `unresolved_magnitude_words` | non-empty exactly when compiling this record would require inventing a numeric meaning for a magnitude word (`§2.2`) — forces a block |
+| `direction_derivation` | the mechanical direction rule, or the literal sentinel `BLOCKED_DIRECTION` |
+| `comparator_derivation` | the mechanical comparator rule, or the literal sentinel `BLOCKED_UNSUPPORTED_STUDY_FORM` |
+| `proxy_of` | non-`None` only for a pilot-proxy record; carries the parked study it stands in for and its preserved `do_not` restriction |
+| `supersession` | non-`None` only for an older, formula-superseded record; carries the newer ref and the alias disposition it selects |
+| `aliases_lineage_ids` | lineage/alias ids this record is linked to |
+| `audit_note` | why each decision follows from the quoted rules — **never** citing a candidate outcome, p-value, effect, observation count, Scout verdict, or PnL result |
+| `extra` | caller-supplied metadata the compiler NEVER reads (proves TC-11: an injected `effect_bps`/`p_value`/`n` cannot move a disposition or hash) |
+
+Mechanical registry lint (`foundry_source_registry.lint_quoted_spans`) verifies every recorded
+quoted span is an exact substring of `source_excerpt` at its recorded character offset. It
+deliberately does not use keyword matching as a proxy for scientific meaning — an exact-position
+substring match only, so a mismatched span fails closed rather than fuzzily "close enough".
+
+---
+
+## 2. Owner meta-policy — block unresolved science
+
+The compile function (`foundry_source_registry.compile_source_disposition`) evaluates a
+`SourceRecord` against this fixed precedence, deterministically, with no fixture/source-specific
+branch anywhere in the function body:
+
+1. **Proxy** (`proxy_of` set) → `ALIASED_PROXY_ONLY`, `do_not` preserved verbatim.
+2. **Supersession** (`supersession` set) → `ALIASED_VARIANT_VOCABULARY` or `ALIASED_LINEAGE`
+   (whichever the record's `supersession.alias_kind` names), `superseded_fields` cite the newer
+   ref.
+3. **Unresolved magnitude word** (`unresolved_magnitude_words` non-empty) → `BLOCKED_SPEC_GAP`
+   (`§2.2`: "defining what words such as `high`, `extreme`, `collapse`... mean numerically" is
+   new science, never a mechanical choice).
+4. **No mechanical direction** (`direction_derivation == "BLOCKED_DIRECTION"`) → `BLOCKED_DIRECTION`.
+5. **Unsupported statistical form** (`comparator_derivation == "BLOCKED_UNSUPPORTED_STUDY_FORM"`)
+   → `BLOCKED_UNSUPPORTED_STUDY_FORM`.
+6. **Illegal threshold provenance** (`threshold_provenance` set but not one of the three `§2.3`
+   categories) → `BLOCKED_UNIT_CONTRACT` is reserved for cross-unit arithmetic specifically (see
+   `docs/goal.md` Anti-goals); an out-of-band threshold is a `§2.2` new-science case and is
+   caught by step 3 above via `unresolved_magnitude_words`, so this step never independently
+   fires for the fixtures this revision defines. It is reserved here for a future source whose
+   gap is a genuine unverified unit crossing rather than a magnitude word.
+7. Otherwise → `COMPILED`.
+
+Exclusion dispositions (`EXCLUDED_PREVIOUSLY_KILLED`/`EXCLUDED_PREREQUISITE_UNMET`/
+`EXCLUDED_GATE_CLOSED`) are not reached by this function at all — they are declared directly on a
+`SourceRecord` via its `explicit_exclusion` field (checked before step 1) for the real registry's
+Study 2/Card 9.1/9.2/9.8-9.11 rows (`J-06`); no hermetic fixture this revision uses one, since none
+of the seven required taxonomy examples is an exclusion case.
+
+### 2.1/2.2 Enumeration vs. block
+
+A finite family enumerates only when each member is a SEPARATE, individually-authored
+`SourceRecord` sharing one `foundry_family_key` — the compiler never expands one record into many
+alternatives on its own initiative (that would be exactly the "mere existence of two features in
+code is not permission to enumerate" trap `§2.1` warns against). Two records sharing a family key
+must each independently reach `COMPILED` on their own merits; the family's `variant_ordinal`
+values are author-declared (mechanical bookkeeping, not derived from anything the compiler
+computes), and the compiler only verifies they are unique within the family.
+
+### 2.3 Natural-boundary law
+
+`threshold_provenance`, when present, must be one of exactly three values (module constants in
+`foundry_source_registry.py`): `THRESHOLD_LITERAL_RATIFIED`, `THRESHOLD_FROZEN_FEATURE_CONTRACT`,
+`THRESHOLD_NATURAL_SEMANTIC_BOUNDARY`. A zero/boolean boundary is legal only under the third
+category and never licenses reinterpreting a magnitude word — that case is represented as
+`unresolved_magnitude_words`, not as an illegal `threshold_provenance` value, so it is caught at
+step 3 of the precedence above.
+
+---
+
+## 3. CandidateSpec — the frozen scientific object
+
+`app/research/foundry_compiler.py`'s `CandidateSpec` dataclass implements every field
+`docs/goal.md §3` requires. `candidate_spec_hash` is `sha256` over a canonical JSON serialization
+(`json.dumps(..., sort_keys=True)`) of every field EXCEPT the hash fields themselves
+(`manifest_hash`, `source_registry_hash`, `compiler_hash`, `candidate_spec_hash`) — so:
+
+- shuffling the order fields are constructed/serialized in never changes the hash (dict key
+  order is normalized by `sort_keys=True`);
+- mutating any other field — `horizon_key` is the canonical worked example — always changes the
+  hash;
+- a caller-attached, non-schema value (the `extra` escape hatch on `SourceRecord`, or any field
+  outside the dataclass entirely) can never reach the hash, because the hash walks only the
+  dataclass's own declared fields.
+
+This revision's `foundry_compiler.compile_sources()` produces a `CandidateSpec` only for a source
+that reaches `COMPILED` and needs no deferred/population resolution — i.e. every coordinate is
+immediately available (no `refill_consistent`-style deferred join). The generic interpreter that
+resolves deferred conditioning (`§4`, `foundry_interpreter.py`) is explicitly future work
+(`docs/goal.md` Binding Execution Order step 3); a source whose compilation would require it is
+left `FROZEN_READY`-incomplete this revision rather than approximated.
+
+### 3.1 Legal outcome horizons
+
+`horizon_key` must be a member of `scout.HORIZON_KEYS` — verified from that module at compile
+time, never hard-coded twice. As of this revision that set is `{"trades_20", "trades_100"}`.
+
+### 3.2 Direction is mandatory
+
+Enforced structurally: `foundry_compiler` never constructs a `CandidateSpec` for a source whose
+disposition is not `COMPILED`, and `COMPILED` is unreachable (`§2` step 4) for a record whose
+`direction_derivation` is the `BLOCKED_DIRECTION` sentinel.
+
+---
+
+## 4. Generic candidate interpretation (future work, meaning fixed here)
+
+The interpreter is new candidate-CONSTRUCTION machinery, never a second statistical rail. Per
+`docs/goal.md §4.1`, for each source population anchor: resolve every conditioning component via
+its `resolution_join_rule` (joining only through the observer's own emitted provenance identity,
+never nearest-time matching); exclude-and-count an anchor with any unresolved component from BOTH
+cells; set `candidate_available_at = max(component.available_at)`; measure identical outcomes for
+candidate and comparator from that instant; the comparator is the complement of membership inside
+that same eligible/timing-resolved population. `§4.2`'s boolean projection
+(`feature_value >= 1.0`) into `scout.screen_candidate` and `§4.2.1`'s Foundry-owned trial-ledger
+boundary (never the Scout ledger) apply unchanged when this module is built.
+
+## 5. Foundry family denominator and multiplicity (future work, meaning fixed here)
+
+`foundry_family_id` groups every predeclared alternative representation of one mechanism lineage,
+frozen before outcomes (`§5.1`). The complete family variant count must be
+`<= scout.SCOUT_MAX_VARIANTS_PER_FAMILY` before evaluation or the whole family is
+`BLOCKED_VARIANT_EXPLOSION` — never truncated, split, or subset-evaluated (`§5.2`). Every sibling
+variant is screened with the COMPLETE frozen denominator as `n_variants_tried`, even before
+siblings execute (`§5.3`). This era adds no Bonferroni/FDR correction (`§5.4`).
+
+## 6. Economic-floor ordering (future work, meaning fixed here)
+
+The manifest freezes the EXISTING quoted-spread floor RULE, never a result-dependent number
+(`docs/goal.md §6`). The numeric floor materializes only during real evaluation, from the legal
+already-exposed corpus, and is appended as an `EVALUATION_INTENT_RECORDED` row BEFORE the outcome
+is measured — it can never be back-filled after the fact.
+
+## 7. State machine
+
+### 7.1 Source dispositions (implemented this revision)
+
+The closed vocabulary — `app/research/foundry_source_registry.py`'s `SOURCE_DISPOSITIONS`:
+
+```
+COMPILED
+ALIASED_PROXY_ONLY
+ALIASED_VARIANT_VOCABULARY
+ALIASED_LINEAGE
+EXCLUDED_PREVIOUSLY_KILLED
+EXCLUDED_PREREQUISITE_UNMET
+EXCLUDED_GATE_CLOSED
+BLOCKED_SPEC_GAP
+BLOCKED_MISSING_PRIMITIVE
+BLOCKED_UNSUPPORTED_STUDY_FORM
+BLOCKED_UNSUPPORTED_RELATION
+BLOCKED_DIRECTION
+BLOCKED_VARIANT_EXPLOSION
+BLOCKED_UNIT_CONTRACT
+```
+
+No required source may silently disappear from this vocabulary; a source not otherwise decided
+reaches `COMPILED` only via the `§2` precedence above, never a default.
+
+### 7.2 Variant states (future work, meaning fixed here)
+
+`FROZEN_READY → EVALUATION_INTENT_RECORDED → {EVALUATED_INSUFFICIENT, EVALUATED_KILLED,
+DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN}`, mapped mechanically from the unchanged Scout kill ladder
+(`docs/goal.md §7.2`). There is no second Foundry verdict.
+
+### 7.3 Integrity/refusal (future work, meaning fixed here)
+
+A ledger/freeze/replay/protected-access defect halts the epoch as `FOUNDRY_INTEGRITY_HALT` — not
+a scientific terminal result, and never silently patched after a first outcome read.
+
+---
+
+## 8. Real generation epoch and freeze barrier (future work, meaning fixed here)
+
+Exactly one real `epoch_id` may ever exist this era (`§8.1`); hermetic fixture epochs — including
+every fixture this revision defines — do not count and never share an `epoch_id` namespace with
+it. The tracked manifest artifacts live under `docs/hypothesis-foundry/` (`§8.2`) and are NOT
+created by this revision — they are generated once, at Binding Execution Order step 6 (`J-06`),
+by running this revision's compiler against the real ratified sources. The freeze record pins
+every science-affecting hash including this spec's own (`§8.4`); the freeze-set is an enumerated
+checked-in path+sha256 manifest, never an adjective chosen at runtime.
+
+## 9. Deterministic exhaust runner (future work, meaning fixed here)
+
+Canonical family-then-ordinal order, invariant to effect/p-value/n/sibling verdicts (`§9.1`); the
+Foundry trial ledger is the source of truth and the checkpoint is only a derived cache (`§9.2`);
+no candidate rescue after first-read lock (`§9.3`).
+
+## 10. Evidence boundary (future work, meaning fixed here)
+
+Every real Foundry candidate uses only the already-exposed `historical_exposed_diagnostic`
+corpus through the sanctioned accessor (`§10.1`); no fresh corpus registration, retention probe,
+storage provisioning, recording, release, Vault act, historical-OOS fold, graduation, or Referee
+act occurs in this era (`§10.2`).
+
+## 11. OOS-rule-frozen survivor semantics (future work, meaning fixed here)
+
+`DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN` means only that a pre-outcome, already-frozen
+`CandidateSpec` passed the unchanged Scout diagnostic rail on already-exposed evidence; it is
+never walk-forward survivor, historical OOS evidence, Vault survivor, Referee-ready, confirmed
+edge, or a profitable-strategy claim (`docs/goal.md §11`).
+
+---
+
+## 12. What this revision proves, and what it deliberately does not
+
+Proven this revision, hermetically, over exactly the seven fixture source archetypes
+`docs/goal.md` J-02 step 2 names (a compileable natural-boundary scalar; two explicitly-frozen
+legal variants in one family; an unresolved-magnitude-word source; a proxy-only source; an
+unsupported-statistic source; an alias/supersession pair; a directionless mechanism):
+
+- the `§7.1` disposition vocabulary is closed and every fixture reaches exactly one member of it;
+- the `§2` owner meta-policy precedence is mechanical and fixture-agnostic;
+- the `§1.4` exact-quote lint fails closed on a mismatched span;
+- the `§3` `CandidateSpec` schema is complete, its hash is order-invariant and
+  science-field-sensitive, and no non-schema fixture field can move it.
+
+Deliberately NOT built this revision: the real 11 required source objects (`J-06`); the generic
+interpreter / deferred-conditioning resolution (`§4`, `J-03`); the Foundry family registry, ledger,
+and freeze barrier (`§5`-`§8`, `J-03`/`J-04`); the exhaust runner (`§9`, `J-07`); any real epoch,
+manifest, freeze commit, or candidate outcome read. A block is a legitimate scientific output, not
+an implementation gap — nothing in this revision "rescues" a fixture that should honestly block.
```
