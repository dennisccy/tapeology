# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 4. Shown in full: 3.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/frontend/app/desk/page.tsx` (636 lines not shown)

```diff
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index 5a5177b..caa10b2 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -305,6 +305,24 @@ _PRICE_ARITHMETIC_FIELDS = (
     r"|session_equivalents|referee_tick_gate_symbol_days)"
     r"|shard\.(?:trade_count|quote_count|bytes|fallback_frac)"
     r"|floor\.(?:required_sessions|available_sessions)"
+    # goal-rapid-microscope-iter-14 (J-08 half 1): the new Scout Ledger / Walk-Forward / Validation
+    # Vault sections' own served numerics -- GET /research/desk/micro/{scout,walkforward,vault}
+    # read verbatim for the first time in the browser. The Scout Ledger's `screen_result` and the
+    # Walk-Forward sequence's `sequence_verdict`/raw `fold_results`/fold-spec geometry are rendered
+    # via `JSON.stringify(...)` (a serialization call, never arithmetic, the SAME class as
+    # `.toFixed()`/`.toLocaleString()` above) rather than destructured field-by-field, so no
+    # per-field entry is needed for those -- only the fields this page actually binds to a local
+    # name join this list. `size_bucket` (Vault, order-of-magnitude only) and
+    # `checksum_commitment`/`rule_commitment`/`vault_secret_commitment`/`commitment_nonce` (opaque
+    # strings) carry no numeric value and are deliberately absent from every alternation below.
+    r"|family\.(?:variants_tried)"
+    r"|trial\.(?:withheld_excluded)"
+    r"|fold\.(?:fold_index|effect|n|n_sessions)"
+    r"|sequence\.decay_view\.recency\.(?:older_fold_count|recent_fold_count|older_positive_share"
+    r"|recent_positive_share)"
+    r"|compute\??\.progress\.(?:candidates_done|candidates_total|steps_done|steps_total)"
+    r"|run\.(?:candidates_done|candidates_total|steps_done|steps_total|folds_evaluated)"
+    r"|universe\.(?:symbol_rule_size|date_rule_size)"
 )
 _PRICE_ARITHMETIC_PATTERN = re.compile(
     rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 41bf16e..fc5b9d0 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -57,6 +57,17 @@ import {
   triggerRefereeEvaluate,
   triggerRefereeNullsCompute,
   fetchMicroReadiness,
+  cancelDeskScoutCompute,
+  cancelDeskWalkforwardCompute,
+  fetchDeskScout,
+  fetchDeskScoutCompute,
+  fetchDeskScoutRuns,
+  fetchDeskVault,
+  fetchDeskWalkforward,
+  fetchDeskWalkforwardCompute,
+  fetchDeskWalkforwardRuns,
+  triggerDeskScoutCompute,
+  triggerDeskWalkforwardCompute,
 } from "@/lib/api";
 import type {
   DeskDeepBackfillComputeSnapshot,
@@ -121,6 +132,16 @@ import type {
   DeskTopupRunMeta,
   DeskTopupRunsListResult,
   MicroReadinessResponse,
+  DeskScoutResponse,
+  DeskScoutComputeSnapshot,
+  DeskScoutRunsResponse,
+  DeskVaultResponse,
+  VaultShardRow,
+  VaultUniverseRow,
+  DeskWalkforwardResponse,
+  DeskWalkforwardComputeSnapshot,
+  DeskWalkforwardRunsResponse,
+  WalkForwardSequence,
   RefereeAdjudicationEntry,
   RefereeAdjudicationsResponse,
   RefereeEvaluateRunsListResult,
@@ -365,7 +386,10 @@ type DeskCollapsibleSection =
   | "refereeRegistry"
   | "refereeAdjudications"
   | "refereeRuns"
-  | "microReadiness";
+  | "microReadiness"
+  | "scoutLedger"
+  | "walkForward"
+  | "validationVault";
 // DESK-COLLAPSED-END
 
 const PRIMARY_BUTTON_CLASS =
@@ -6072,6 +6096,702 @@ function MicroReadinessSection({
   );
 }
 
+// goal-rapid-microscope-iter-14 (J-08 half 1): the Scout Ledger section -- the era's SECOND
+// Rapid-Microscope section, rendered directly BELOW Microscope Readiness. Every field is read
+// verbatim off GET /research/desk/micro/scout (families/chain_verification) and GET .../scout/runs
+// (the durable run log) -- nothing computed client-side. A candidate's own `screen_result` is a
+// large, candidate-type-dependent payload (concentration/ToD/fallback-tercile disclosures, the
+// economic-relevance column, etc.) and is rendered as an opaque, verbatim JSON detail rather than
+// guessed at field-by-field, so nothing the backend serves is ever silently dropped.
+function ScoutLedgerSection({
+  scoutResult,
+  runsResult,
+  compute,
+  control,
+  onTrigger,
+  onCancel,
+}: {
+  scoutResult: { ok: boolean; data: DeskScoutResponse | null; error?: string } | null;
+  runsResult: { ok: boolean; data: DeskScoutRunsResponse | null; error?: string } | null;
+  compute: DeskScoutComputeSnapshot | null;
+  control: RefereeComputeControlState;
+  onTrigger: () => void;
+  onCancel: () => void;
+}) {
+  const isRunning = compute?.state === "running";
+  return (
+    <div data-testid="scout-ledger-section">
+      <p className="mb-3 text-xs text-slate-500">
+        The Scout&apos;s exploratory candidate ledger (GET /research/desk/micro/scout, read
+        verbatim): every registered family&apos;s trials, its union-N denominator across every
+        grid version, and each trial&apos;s kill reason.
+      </p>
+
+      <div
+        data-testid="scout-ledger-control-block"
+        className="mb-4 flex flex-col items-start gap-1 rounded-md border border-slate-800 p-2"
+      >
+        <button
+          type="button"
+          data-testid="scout-ledger-trigger"
+          onClick={onTrigger}
+          disabled={control.triggering || isRunning}
+          className={PRIMARY_BUTTON_CLASS}
+        >
+          {isRunning ? "Screening…" : "Run Screen"}
+        </button>
+        {isRunning && (
+          <p data-testid="scout-ledger-progress" className="text-xs text-amber-200/70">
+            <span
+              aria-hidden="true"
+              className="mr-1.5 inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-400 align-middle"
+            />
+            {compute?.progress.candidates_done ?? 0} / {compute?.progress.candidates_total ?? 0}{" "}
+            candidates
+          </p>
+        )}
+        {control.triggerError && (
+          <p data-testid="scout-ledger-trigger-error" className="text-xs text-red-300">
+            {control.triggerError}
+          </p>
+        )}
+        {isRunning && (
+          <button
+            type="button"
+            data-testid="scout-ledger-cancel"
+            onClick={onCancel}
+            disabled={control.cancelRequested}
+            className={CANCEL_BUTTON_CLASS}
+          >
+            {control.cancelRequested ? "Cancelling…" : "Cancel"}
+          </button>
+        )}
+        {control.cancelError && (
+          <p data-testid="scout-ledger-cancel-error" className="text-xs text-red-300">
+            {control.cancelError}
+          </p>
+        )}
+      </div>
+
+      {scoutResult === null ? (
+        <LoadingPanel testid="scout-ledger-loading" />
+      ) : !scoutResult.ok || scoutResult.data === null ? (
+        <UnavailablePanel
+          testid="scout-ledger-unavailable"
+          message={scoutResult.error ?? "The scout ledger could not be loaded."}
+        />
+      ) : (
+        <div data-testid="scout-ledger-families-block" className="mb-4">
+          <p data-testid="scout-ledger-chain-verification" className="mb-2 text-[11px] text-slate-500">
+            Ledger chain verification:{" "}
+            <span className="font-mono text-slate-300">
+              {scoutResult.data.chain_verification.ok
+                ? "ok"
+                : `failed at row ${scoutResult.data.chain_verification.failed_at_row} (${scoutResult.data.chain_verification.reason})`}
+            </span>
+          </p>
+          {scoutResult.data.families.length === 0 ? (
+            <EmptyState testid="scout-ledger-families-empty" title="No candidates ledgered." />
+          ) : (
+            scoutResult.data.families.map((family) => (
+              <div key={family.family_id} data-testid={`scout-family-${family.family_id}`} className="mb-4">
+                <h4 className="mb-1 text-xs font-semibold text-slate-400">
+                  {family.family_id}{" "}
+                  <span className="font-normal text-slate-500">
+                    — {family.variants_tried} variants tried
+                  </span>
+                </h4>
+                <div className="overflow-x-auto">
+                  <table className="w-full min-w-[900px] border-collapse text-xs">
+                    <thead>
+                      <tr className="border-b border-slate-800 text-left text-slate-500">
+                        <th className="px-1.5 py-1">Candidate</th>
+                        <th className="px-1.5 py-1">Feature</th>
+                        <th className="px-1.5 py-1">Horizon</th>
+                        <th className="px-1.5 py-1">Registered</th>
+                        <th className="px-1.5 py-1">Decision</th>
+                        <th className="px-1.5 py-1">Reason</th>
+                        <th className="px-1.5 py-1">Notes</th>
+                        <th className="px-1.5 py-1 text-right">Withheld excluded</th>
+                        <th className="px-1.5 py-1">Screen detail</th>
+                      </tr>
+                    </thead>
+                    <tbody data-testid={`scout-family-${family.family_id}-trial-rows`}>
+                      {family.trials.map((trial) => (
+                        <tr key={trial.candidate_id} className="border-b border-slate-900">
+                          <td className="whitespace-nowrap px-1.5 py-1 font-mono text-[10px] text-slate-500">
+                            {trial.candidate_id}
+                          </td>
+                          <td className="px-1.5 py-1 text-slate-300">
+                            {trial.feature.name} / {trial.feature.transform}
+                          </td>
+                          <td className="px-1.5 py-1 text-slate-400">{trial.outcome.horizon_key}</td>
+                          <td className="whitespace-nowrap px-1.5 py-1 font-mono text-slate-400">
+                            {formatDateTimeET(trial.registered_at, { seconds: false })}
+                          </td>
+                          <td className="px-1.5 py-1 text-slate-300">{trial.decision}</td>
+                          <td className="px-1.5 py-1 text-slate-400">{trial.reason ?? "—"}</td>
+                          <td className="px-1.5 py-1 text-slate-400">{trial.notes ?? "—"}</td>
+                          <td className="px-1.5 py-1 text-right font-mono text-slate-300">
+                            {trial.withheld_excluded}
+                          </td>
+                          <td className="px-1.5 py-1">
+                            <details>
+                              <summary className="cursor-pointer text-slate-500">
+                                screen_result
+                              </summary>
+                              <pre className="mt-1 max-w-[420px] overflow-x-auto whitespace-pre-wrap break-all text-[10px] text-slate-500">
+                                {JSON.stringify(trial.screen_result, null, 2)}
+                              </pre>
+                            </details>
+                          </td>
+                        </tr>
+                      ))}
+                    </tbody>
+                  </table>
+                </div>
+              </div>
+            ))
+          )}
+        </div>
+      )}
+
+      <div data-testid="scout-ledger-runs-block">
+        <h4 className="mb-2 text-xs font-semibold text-slate-400">Run History</h4>
+        {runsResult === null ? (
+          <LoadingPanel testid="scout-ledger-runs-loading" />
+        ) : !runsResult.ok || runsResult.data === null ? (
+          <UnavailablePanel
+            testid="scout-ledger-runs-unavailable"
+            message={runsResult.error ?? "The scout run history could not be loaded."}
+          />
+        ) : runsResult.data.runs.length === 0 ? (
+          <EmptyState testid="scout-ledger-runs-empty" title="No scout runs recorded yet." />
+        ) : (
+          <div className="overflow-x-auto">
+            <table
+              data-testid="scout-ledger-runs-table"
+              className="w-full min-w-[720px] border-collapse text-xs"
+            >
+              <thead>
+                <tr className="border-b border-slate-800 text-left text-slate-500">
+                  <th className="px-1.5 py-1">Run</th>
+                  <th className="px-1.5 py-1">State</th>
+                  <th className="px-1.5 py-1">Started</th>
+                  <th className="px-1.5 py-1">Finished</th>
+                  <th className="px-1.5 py-1 text-right">Candidates</th>
+                  <th className="px-1.5 py-1">Error</th>
+                </tr>
+              </thead>
+              <tbody data-testid="scout-ledger-run-rows">
+                {runsResult.data.runs.map((run) => (
+                  <tr key={run.run_id} className="border-b border-slate-900">
+                    <td className="whitespace-nowrap px-1.5 py-1 font-mono text-[10px] text-slate-500">
+                      {run.run_id}
+                    </td>
+                    <td className="px-1.5 py-1 text-slate-300">{run.state}</td>
+                    <td className="whitespace-nowrap px-1.5 py-1 font-mono text-slate-400">
+                      {formatDateTimeET(run.started_utc, { seconds: false })}
+                    </td>
+                    <td className="whitespace-nowrap px-1.5 py-1 font-mono text-slate-400">
+                      {formatDateTimeET(run.finished_utc, { seconds: false })}
+                    </td>
+                    <td className="px-1.5 py-1 text-right font-mono text-slate-300">
+                      {run.candidates_done} / {run.candidates_total}
+                    </td>
+                    <td className="px-1.5 py-1 text-red-300">{run.error ?? ""}</td>
+                  </tr>
+                ))}
+              </tbody>
+            </table>
+          </div>
+        )}
+      </div>
+    </div>
+  );
+}
+
+// goal-rapid-microscope-iter-14 (J-08 half 1): the Walk-Forward section -- the era's THIRD
+// Rapid-Microscope section, rendered directly BELOW Scout Ledger. Every field is read verbatim off
+// GET /research/desk/micro/walkforward (fold_specs/sequences/chain_verification) and GET
+// .../walkforward/runs. The per-fold table renders `decay_view.fold_rows` (spec section 6.6's own
+// "per-fold, never a merged statistic" reporting view) rather than re-deriving one from the raw
+// `fold_results`; the raw rows and the full `sequence_verdict`/fold-spec geometry are still
+// disclosed in full via an opaque, verbatim JSON detail each, so nothing served is ever dropped.
+function WalkForwardSection({
+  walkforwardResult,
+  runsResult,
+  compute,
+  control,
+  onTrigger,
+  onCancel,
+}: {
+  walkforwardResult: { ok: boolean; data: DeskWalkforwardResponse | null; error?: string } | null;
+  runsResult: { ok: boolean; data: DeskWalkforwardRunsResponse | null; error?: string } | null;
+  compute: DeskWalkforwardComputeSnapshot | null;
+  control: RefereeComputeControlState;
+  onTrigger: () => void;
+  onCancel: () => void;
+}) {
+  const isRunning = compute?.state === "running";
+  return (
+    <div data-testid="walk-forward-section">
+      <p className="mb-3 text-xs text-slate-500">
+        The chronological walk-forward engine (GET /research/desk/micro/walkforward, read
+        verbatim): every registered fold spec, and every sequence&apos;s per-fold results, decay
+        view, and verdict.
+      </p>
+
+      <div
+        data-testid="walk-forward-control-block"
+        className="mb-4 flex flex-col items-start gap-1 rounded-md border border-slate-800 p-2"
+      >
+        <button
+          type="button"
+          data-testid="walk-forward-trigger"
+          onClick={onTrigger}
+          disabled={control.triggering || isRunning}
+          className={PRIMARY_BUTTON_CLASS}
+        >
+          {isRunning ? "Running…" : "Run Walk-Forward"}
+        </button>
+        {isRunning && (
+          <p data-testid="walk-forward-progress" className="text-xs text-amber-200/70">
+            <span
+              aria-hidden="true"
+              className="mr-1.5 inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-400 align-middle"
+            />
+            {compute?.progress.steps_done ?? 0} / {compute?.progress.steps_total ?? 0} steps
+          </p>
+        )}
+        {control.triggerError && (
+          <p data-testid="walk-forward-trigger-error" className="text-xs text-red-300">
+            {control.triggerError}
+          </p>
+        )}
+        {isRunning && (
+          <button
+            type="button"
+            data-testid="walk-forward-cancel"
+            onClick={onCancel}
+            disabled={control.cancelRequested}
+            className={CANCEL_BUTTON_CLASS}
+          >
+            {control.cancelRequested ? "Cancelling…" : "Cancel"}
+          </button>
+        )}
+        {control.cancelError && (
+          <p data-testid="walk-forward-cancel-error" className="text-xs text-red-300">
+            {control.cancelError}
+          </p>
+        )}
+      </div>
+
+      {walkforwardResult === null ? (
+        <LoadingPanel testid="walk-forward-loading" />
+      ) : !walkforwardResult.ok || walkforwardResult.data === null ? (
+        <UnavailablePanel
+          testid="walk-forward-unavailable"
+          message={walkforwardResult.error ?? "The walk-forward ledger could not be loaded."}
+        />
+      ) : (
+        <div data-testid="walk-forward-ledger-block" className="mb-4">
+          <p data-testid="walk-forward-chain-verification" className="mb-2 text-[11px] text-slate-500">
+            Ledger chain verification:{" "}
+            <span className="font-mono text-slate-300">
+              {walkforwardResult.data.chain_verification.ok
+                ? "ok"
+                : `failed at row ${walkforwardResult.data.chain_verification.failed_at_row} (${walkforwardResult.data.chain_verification.reason})`}
+            </span>
+          </p>
+
+          <div data-testid="walk-forward-fold-specs-block" className="mb-4">
+            <h4 className="mb-2 text-xs font-semibold text-slate-400">Fold Specs</h4>
+            {walkforwardResult.data.fold_specs.length === 0 ? (
+              <EmptyState testid="walk-forward-fold-specs-empty" title="No fold specs registered." />
+            ) : (
+              <ul data-testid="walk-forward-fold-spec-rows" className="space-y-1">
+                {walkforwardResult.data.fold_specs.map((spec) => (
+                  <li key={spec.corpus_id}>
+                    <details>
+                      <summary className="cursor-pointer font-mono text-[11px] text-slate-400">
+                        {spec.corpus_id}
+                      </summary>
+                      <pre className="mt-1 max-w-[640px] overflow-x-auto whitespace-pre-wrap break-all text-[10px] text-slate-500">
+                        {JSON.stringify(spec, null, 2)}
+                      </pre>
+                    </details>
+                  </li>
+                ))}
+              </ul>
+            )}
+          </div>
+
+          {walkforwardResult.data.sequences.length === 0 ? (
+            <EmptyState testid="walk-forward-sequences-empty" title="No candidates ledgered." />
+          ) : (
+            walkforwardResult.data.sequences.map((sequence) => {
+              const verdict = sequence.sequence_verdict;
+              return (
+                <div
+                  key={sequence.sequence_id}
+                  data-testid={`walk-forward-sequence-${sequence.sequence_id}`}
+                  className="mb-5"
+                >
+                  <h4 className="mb-1 text-xs font-semibold text-slate-400">
+                    {sequence.sequence_id}
+                    <span className="ml-2 font-normal text-slate-500">
... [diff_bound] apps/frontend/app/desk/page.tsx: 636 more diff lines omitted — Read the file for full detail
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index b4d44e4..a132760 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -10,6 +10,10 @@ import type {
   DeskDeepBackfillPlan,
   DeskReconcileComputeSnapshot,
   DeskReconcileRunsListResult,
+  DeskScoutComputeSnapshot,
+  DeskScoutComputeTriggerResponse,
+  DeskScoutResponse,
+  DeskScoutRunsResponse,
   DeskScreenCompareResult,
   DeskScreenComputeSnapshot,
   DeskScreenListResult,
@@ -33,6 +37,11 @@ import type {
   DeskTopupComputeSnapshot,
   DeskTopupRunsListResult,
   DeskUniverseSnapshotMeta,
+  DeskVaultResponse,
+  DeskWalkforwardComputeSnapshot,
+  DeskWalkforwardComputeTriggerResponse,
+  DeskWalkforwardResponse,
+  DeskWalkforwardRunsResponse,
   EdgeReportComputeSnapshot,
   EdgeReportPayload,
   LevelsResponse,
@@ -2432,3 +2441,266 @@ export async function cancelRefereeEvaluate(hypothesisId: string): Promise<{
     return { ok: false, error: "Backend unreachable — is the API running?" };
   }
 }
+
+// goal-rapid-microscope-iter-14 (J-08 half 1): Scout Ledger / Walk-Forward / Validation Vault --
+// three already-shipped, already-tested backend endpoints, their first-ever frontend consumers.
+// Every function below mirrors `fetchMicroReadiness`'s exact `{ok, data, error?}` envelope and
+// "Backend unreachable — is the API running?" fallback string verbatim.
+
+// GET /research/desk/micro/scout — every registered family's trials, verbatim, beside the ledger's
+// own chain-verification verdict. Never 404 on an empty ledger (an honest `families: []`).
+export async function fetchDeskScout(): Promise<{
+  ok: boolean;
+  data: DeskScoutResponse | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/micro/scout`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskScoutResponse };
+    }
+    let error = "The scout ledger could not be loaded.";
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
+// POST /research/desk/micro/scout/compute — starts a screening run over the bounded reference
+// grid, or refuses (single-flight). Unlike triggerDeskTopupCompute/triggerDeskReconcileCompute, a
+// refusal is NOT an HTTP error here — both "running" and "refused" arrive at HTTP 200 with a
+// `state` field distinguishing them (confirmed against `trigger_scout_compute`'s own body); `res.ok
+// === false` is reserved for a genuine non-200/unreachable backend. This route takes no body — an
+// operator names no candidate/date, unlike the recorder or the screen compute triggers.
+export async function triggerDeskScoutCompute(): Promise<{
+  ok: boolean;
+  data: DeskScoutComputeTriggerResponse | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/micro/scout/compute`, { method: "POST" });
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskScoutComputeTriggerResponse };
+    }
+    let error = "The scout screening run could not be started.";
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
+// GET /research/desk/micro/scout/compute — the current (or last-terminal) run's progress, served
+// verbatim. Never 404 (the idle default before any job has ever run this process).
+export async function fetchDeskScoutCompute(): Promise<{
+  ok: boolean;
+  data: DeskScoutComputeSnapshot | null;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/micro/scout/compute`);
+    if (!res.ok) return { ok: false, data: null };
+    const data = await res.json();
+    return { ok: true, data: (data as DeskScoutComputeSnapshot | null) ?? null };
+  } catch {
+    return { ok: false, data: null };
+  }
+}
+
+// POST /research/desk/micro/scout/compute/cancel — cancel the in-flight screening run. The
+// backend's 409 (idle) `detail` is surfaced verbatim.
+export async function cancelDeskScoutCompute(): Promise<{ ok: boolean; error?: string }> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/micro/scout/compute/cancel`, {
+      method: "POST",
+    });
+    if (res.ok) return { ok: true };
+    let error = "The scout screening run could not be cancelled.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, error };
+  } catch {
+    return { ok: false, error: "Backend unreachable — is the API running?" };
+  }
+}
+
+// GET /research/desk/micro/scout/runs — the durable run history, newest first. Never 404 on zero
+// runs (an honest empty list).
+export async function fetchDeskScoutRuns(): Promise<{
+  ok: boolean;
+  data: DeskScoutRunsResponse | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/micro/scout/runs`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskScoutRunsResponse };
+    }
+    let error = "The scout run history could not be loaded.";
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
+// GET /research/desk/micro/walkforward — every fold spec plus every sequence's fold results, decay
+// view, and sequence verdict, beside the ledger's own chain-verification verdict. Never 404 on an
+// empty ledger. Mirrors fetchDeskScout exactly.
+export async function fetchDeskWalkforward(): Promise<{
+  ok: boolean;
+  data: DeskWalkforwardResponse | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/micro/walkforward`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskWalkforwardResponse };
+    }
+    let error = "The walk-forward ledger could not be loaded.";
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
+// POST /research/desk/micro/walkforward/compute — starts the diagnostic acceptance run against the
+// operator's real playbook/universe/bar stores, or refuses (single-flight). Same two-shape-at-200
+// body as triggerDeskScoutCompute; this route also takes no body.
+export async function triggerDeskWalkforwardCompute(): Promise<{
+  ok: boolean;
+  data: DeskWalkforwardComputeTriggerResponse | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/micro/walkforward/compute`, {
+      method: "POST",
+    });
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskWalkforwardComputeTriggerResponse };
+    }
+    let error = "The walk-forward run could not be started.";
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
+// GET /research/desk/micro/walkforward/compute — mirrors fetchDeskScoutCompute exactly.
+export async function fetchDeskWalkforwardCompute(): Promise<{
+  ok: boolean;
+  data: DeskWalkforwardComputeSnapshot | null;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/micro/walkforward/compute`);
+    if (!res.ok) return { ok: false, data: null };
+    const data = await res.json();
+    return { ok: true, data: (data as DeskWalkforwardComputeSnapshot | null) ?? null };
+  } catch {
+    return { ok: false, data: null };
+  }
+}
+
+// POST /research/desk/micro/walkforward/compute/cancel — mirrors cancelDeskScoutCompute exactly.
+export async function cancelDeskWalkforwardCompute(): Promise<{ ok: boolean; error?: string }> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/micro/walkforward/compute/cancel`, {
+      method: "POST",
+    });
+    if (res.ok) return { ok: true };
+    let error = "The walk-forward run could not be cancelled.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, error };
+  } catch {
+    return { ok: false, error: "Backend unreachable — is the API running?" };
+  }
+}
+
+// GET /research/desk/micro/walkforward/runs — mirrors fetchDeskScoutRuns exactly.
+export async function fetchDeskWalkforwardRuns(): Promise<{
+  ok: boolean;
+  data: DeskWalkforwardRunsResponse | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/micro/walkforward/runs`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskWalkforwardRunsResponse };
+    }
+    let error = "The walk-forward run history could not be loaded.";
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
+// GET /research/desk/micro/vault — READ-ONLY this iteration (state/assumptions.md's iter-14
+// entry): every shard's CURRENT lifecycle state (opaque-only while sealed) and every registered
+// universe (committed-only until whole-ORIGINAL-pool release), beside BOTH ledgers' own
+// chain-verification verdicts. The ONLY fetch the Validation Vault section issues — never
+// /research/datasets, never the readiness result, to enrich or cross-reference a row (Guardrails/
+// TC-6).
+export async function fetchDeskVault(): Promise<{
+  ok: boolean;
+  data: DeskVaultResponse | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/micro/vault`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskVaultResponse };
+    }
+    let error = "The validation vault could not be loaded.";
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
index 55bf380..990b082 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -2517,3 +2517,309 @@ export interface MicroReadinessResponse {
   study_floors: MicroReadinessStudyFloor[];
   integrity_errors: { file: string; error: string }[];
 }
+
+// goal-rapid-microscope-iter-14 (J-08 half 1): Scout Ledger, Walk-Forward, and Validation Vault --
+// three already-shipped backend endpoints rendered on /desk for the first time. Every shape below
+// is transcribed directly from `apps/backend/app/research/{micro_routes,scout,scout_ledger,
+// walkforward,walkforward_ledger,vault}.py`, read this planning pass -- never re-derived from
+// goal.md prose alone. A candidate/fold's own inner payload (`screen_result`, `econ_floor`,
+// `feature`, `outcome`, `structure_context`, a fold's `missing`) varies by candidate/fold type and
+// is typed as `Record<string, unknown>` rather than enumerated -- the page renders it as an opaque,
+// verbatim JSON detail (never guesses a fixed shape, so a field already served is never silently
+// dropped by a mis-typed interface).
+
+export interface MicroChainVerification {
+  ok: boolean;
+  failed_at_row: number | null;
+  reason: string | null;
+}
+
+// --- Scout Ledger -- GET /research/desk/micro/scout (scout.py `list_scout_families`,
+// `register_and_screen_candidate`/`build_candidate_spec_fields`'s own row shape) -----------------
+
+export interface ScoutTrialRow {
+  family_id: string;
+  family_root_id: string;
+  candidate_id: string;
+  spec_hash: string;
+  feature: { name: string; transform: string; params: Record<string, unknown> };
+  structure_context: { kind: string };
+  outcome: { horizon_key: string; sidedness: string | null };
+  fitting_rule: string | null;
+  econ_floor: Record<string, unknown>;
+  corpus_manifest: unknown[];
+  grid_version: number;
+  registered_at: string;
+  econ_floor_computed_at: string;
+  params_hash: string;
+  decision: string;
+  reason: string | null;
+  notes: string | null;
+  screen_result: Record<string, unknown>;
+  superseded_by: string | null;
+  // spec section 7.5 point 6 (r4): how many registered datasets this candidate's corpus manifest
+  // left out because their vault shards are withheld -- a disclosed COUNT, never an id.
+  withheld_excluded: number;
+}
+
+export interface ScoutFamily {
+  family_id: string;
+  family_root_id: string;
+  // The union-N denominator across every grid_version ever run for this family -- never a
+  // client-recount of `trials.length` (a superseded/tampered row must not silently change it).
+  variants_tried: number;
+  trials: ScoutTrialRow[];
+}
+
+export interface DeskScoutResponse {
+  families: ScoutFamily[];
+  chain_verification: MicroChainVerification;
+}
+
+export interface DeskScoutComputeProgress {
+  candidates_total: number;
+  candidates_done: number;
+  current_candidate_id: string | null;
+}
+
+// GET/POST /research/desk/micro/scout/compute -- served verbatim, no `id`/`run_id` field on the
+// GET shape (unlike DeskScreenComputeSnapshot/DeskTopupComputeSnapshot; confirmed against
+// `get_scout_compute`'s own return statement, not assumed from a sibling type).
+export interface DeskScoutComputeSnapshot {
+  state: "idle" | "running" | "done" | "cancelled" | "failed";
+  progress: DeskScoutComputeProgress;
+  started_utc: string | null;
+  finished_utc: string | null;
+  error: string | null;
+}
+
+// POST /research/desk/micro/scout/compute's own two-shape body (both at HTTP 200 -- a refusal is
+// NOT an HTTP error here, unlike the topup/reconcile precedent): confirmed against
+// `trigger_scout_compute`'s own body.
+export type DeskScoutComputeTriggerResponse =
+  | { state: "running"; run_id: string }
+  | { state: "refused"; reason: string };
+
+export interface DeskScoutRunLogEntry {
+  run_id: string;
+  state: "done" | "cancelled" | "failed";
+  started_utc: string;
+  finished_utc: string;
+  candidates_done: number;
+  candidates_total: number;
+  error: string | null;
+}
+
+export interface DeskScoutRunsResponse {
+  runs: DeskScoutRunLogEntry[];
+}
+
+// --- Walk-Forward -- GET /research/desk/micro/walkforward (walkforward.py `list_fold_specs`,
+// `list_walkforward_sequences`, `decay_view`, `sequence_verdict`/`evaluate_survivor_rule`) -------
+
+export interface WalkForwardFoldResultRow {
+  sequence_id: string;
+  corpus_id: string;
+  mode: string;
+  rule_id?: string;
+  fitting_rule?: string | null;
+  spec_hash?: string;
+  fold_index: number;
+  sidedness: string;
+  econ_floor: Record<string, unknown> | null;
+  evidence_class: string;
+  process_label: string;
+  registered_at: string;
+  status: string;
+  n: number;
+  n_sessions: number;
+  n_symbols: number;
+  effect: number | null;
+  sign: string | null;
+  missing: Record<string, string>;
+}
+
+export interface WalkForwardDecayFoldRow {
+  fold_index: number;
+  status: string;
+  effect: number | null;
+  n: number;
+  n_sessions: number;
+  sign: string | null;
+  evidence_class: string;
+  process_label: string;
+}
+
+export interface WalkForwardDecayView {
+  fold_rows: WalkForwardDecayFoldRow[];
+  recency: {
+    older_fold_count: number;
+    recent_fold_count: number;
+    older_positive_share: number | null;
+    recent_positive_share: number | null;
+  };
+}
+
+// WF_SURVIVOR_RULE_V1's own two-shape verdict (walkforward.py `sequence_verdict`): a refusal below
+// WF_MIN_SUFFICIENT_FOLDS, never a fabricated result, or the full five-condition predicate.
+export interface WalkForwardSurvivorConditions {
+  sufficient_oos_rule_process_folds: boolean;
+  sign_agreement: boolean;
+  pooled_effect_clears_econ_floor: boolean;
+  no_opposite_direction_sufficient_fold: boolean;
+  zero_voiding_events: boolean;
+}
+
+export type WalkForwardSequenceVerdict =
+  | { refused: true; reason: string; n_sufficient_folds: number }
+  | {
+      refused: false;
+      verdict: string;
+      rule_name: string;
+      conditions: WalkForwardSurvivorConditions;
+      n_sufficient_folds: number;
+      n_eligible_folds: number;
+      sign_agreement: number;
+      pooled_effect: number | null;
+    };
+
+export interface WalkForwardSequence {
+  sequence_id: string;
+  corpus_id: string;
+  mode: string | null;
+  fitting_rule: string | null;
+  rule_id: string | null;
+  sidedness: string;
+  econ_floor: Record<string, unknown> | null;
+  voided: boolean;
+  fold_results: WalkForwardFoldResultRow[];
+  decay_view: WalkForwardDecayView;
+  sequence_verdict: WalkForwardSequenceVerdict;
+}
+
+// `latest_fold_spec`'s own row -- carries at least `corpus_id`; the rest of the frozen geometry
+// (fold counts/day-widths/purge/embargo) rendered verbatim via an index signature rather than
+// enumerated field-for-field (T-1: never invent a shape not directly verified this pass).
+export interface WalkForwardFoldSpec {
+  corpus_id: string;
+  [key: string]: unknown;
+}
+
+export interface DeskWalkforwardResponse {
+  fold_specs: WalkForwardFoldSpec[];
+  sequences: WalkForwardSequence[];
+  chain_verification: MicroChainVerification;
+}
+
+export interface DeskWalkforwardComputeProgress {
+  steps_total: number;
+  steps_done: number;
+  current_step: string | null;
+}
+
+export interface DeskWalkforwardComputeSnapshot {
+  state: "idle" | "running" | "done" | "cancelled" | "failed";
+  progress: DeskWalkforwardComputeProgress;
+  started_utc: string | null;
+  finished_utc: string | null;
+  error: string | null;
+}
+
+export type DeskWalkforwardComputeTriggerResponse =
+  | { state: "running"; run_id: string }
+  | { state: "refused"; reason: string };
+
+export interface DeskWalkforwardRunLogEntry {
+  run_id: string;
+  state: "done" | "cancelled" | "failed";
+  started_utc: string;
+  finished_utc: string;
+  steps_done: number;
+  steps_total: number;
+  error: string | null;
+  // `trigger_walkforward_compute`'s own extra terminal-log fields (merged onto the run-log entry
+  // on success only -- absent on a `failed`/`cancelled` entry, since `_work`'s return is never
+  // reached in that path).
+  folds_evaluated?: number;
+  folds_replayed?: number;
+  validation_sessions?: number;
+  session_count?: number;
+}
+
+export interface DeskWalkforwardRunsResponse {
+  runs: DeskWalkforwardRunLogEntry[];
+}
+
+// --- Validation Vault -- GET /research/desk/micro/vault, READ-ONLY this iteration (vault.py
+// `build_vault_state`/`_serialize_shard`/`_serialize_universe`) ------------------------------------
+//
+// Section 7.5's three-stage shard reveal and the r7 two-stage universe reveal, both transcribed as
+// an explicit per-stage whitelist matching `vault.py`'s own positive whitelist (never a superset --
+// TC-4/TC-5/TC-15 depend on the FRONTEND never widening what the backend already narrowed).
+
+// `exposure_state` is the discriminant across BOTH interfaces (disjoint literal sets, never
+// widened to the full three-value union on either side) so the page can narrow on
+// `shard.exposure_state === "sealed"` — the server's own stage label — rather than on which
+// optional fields happen to be present (vault.py's own "never field-presence inference" rule,
+// carried into the type layer).
+export interface VaultOpaqueShard {
+  shard_id: string;
+  universe_id: string;
+  // Order-of-magnitude ONLY (`vault._coarse_size_bucket`: "~0" or "~10^N") -- never an exact count,
+  // and never arithmetic material (TC-9/Guardrails: no count is ever derived from this field).
+  size_bucket: string;
+  checksum_commitment: string;
+  sealed_at: string;
+  exposure_state: "sealed";
+}
+
+export interface VaultRevealedShard {
+  shard_id: string;
+  universe_id: string;
+  size_bucket: string;
+  checksum_commitment: string;
+  sealed_at: string;
+  exposure_state: "assigned" | "exposed";
+  dataset_id: string;
+  family_root_id: string;
+  symbol: string;
+  session_date: string;
+  assigned_at: string;
+  exposed_at: string | null;
+  // Present only once `exposure_state === "exposed"` (vault.py `_serialize_shard`).
+  content_checksum?: string;
+}
+
+export type VaultShardRow = VaultOpaqueShard | VaultRevealedShard;
+
+export interface VaultCommittedUniverse {
+  universe_id: string;
+  registered_at: string;
+  rule_commitment: string;
+  vault_secret_commitment: string;
+  symbol_rule_size: number;
+  date_rule_size: number;
+  rule_disclosure: "committed";
+}
+
+export interface VaultRevealedUniverse {
+  universe_id: string;
+  registered_at: string;
+  rule_commitment: string;
+  vault_secret_commitment: string;
+  symbol_rule: string[];
+  date_rule: string[];
+  commitment_nonce: string;
+  rule_disclosure: "revealed";
+}
+
+export type VaultUniverseRow = VaultCommittedUniverse | VaultRevealedUniverse;
+
+export interface DeskVaultResponse {
+  universes: VaultUniverseRow[];
+  shards: VaultShardRow[];
+  // TWO distinct chain-verification fields (never one shared `chain_verification` like Scout/
+  // Walk-Forward) -- the shard ledger and the universe ledger are separate hash chains.
+  shard_ledger_chain_verification: MicroChainVerification;
+  universe_ledger_chain_verification: MicroChainVerification;
+}
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-rapid-microscope/telemetry.jsonl   | 7 +++++++
 runs/goal-session-rapid-microscope/trace/trace.jsonl | 2 ++
 2 files changed, 9 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
