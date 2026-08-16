# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 6. Shown in full: 6.

```diff
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index 141a621..a8d8b85 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -285,6 +285,16 @@ _PRICE_ARITHMETIC_FIELDS = (
     # `RefereeEvaluationRunRow`).
     r"|compute\??\.(?:done|total)"
     r"|run\.progress\.(?:done|total)"
+    # goal-referee-iter-13 (J-12): the Referee Registry section's own new evidence-readiness
+    # blocks -- GET /research/desk/referee/evidence read verbatim for the FIRST time in the
+    # browser. J-12's whole point is "zero client-side arithmetic on any served numeric", so
+    # every one of the seven counts this component renders joins this list on the same footing
+    # as every other referee numeric above (evidence.playbook_occurrence.*/
+    # evidence.strategy_trade.* -- the RefereeEvidenceReadinessSection's own local binding for
+    # the fetched `GET /research/desk/referee/evidence` body).
+    r"|evidence\.playbook_occurrence\.(?:records|distinct_sessions|signals_at_current_basis)"
+    r"|evidence\.strategy_trade\.(?:dataset_count|trade_count)"
+    r"|evidence\.strategy_trade\.per_split_counts\.(?:train|holdout)"
 )
 _PRICE_ARITHMETIC_PATTERN = re.compile(
     rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
@@ -328,6 +338,36 @@ def test_desk_page_price_arithmetic_guard_catches_opposite_band_and_bands_by_cla
     seeded_score = "const combined = row.opposite_band.band_score + row.band_score;"
     assert _PRICE_ARITHMETIC_PATTERN.search(seeded_score) is not None
 
+
+def test_desk_page_price_arithmetic_guard_catches_referee_evidence_arithmetic():
+    """goal-referee-iter-13 (J-12) TC-12 counter-test: the widened guard also catches arithmetic
+    over the new Referee evidence-readiness numerics (GET /research/desk/referee/evidence's first
+    UI reader), proving the widened pattern actually fails on injected client-side arithmetic --
+    not just that it passes on unmodified source."""
+    seeded_total = (
+        "const total = evidence.playbook_occurrence.records + "
+        "evidence.playbook_occurrence.distinct_sessions;"
+    )
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_total) is not None
+
+    seeded_signals = (
+        "const share = evidence.playbook_occurrence.signals_at_current_basis / "
+        "evidence.playbook_occurrence.records;"
+    )
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_signals) is not None
+
+    seeded_split = (
+        "const combined = evidence.strategy_trade.per_split_counts.train + "
+        "evidence.strategy_trade.per_split_counts.holdout;"
+    )
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_split) is not None
+
+    seeded_trades = (
+        "const perDataset = evidence.strategy_trade.trade_count / "
+        "evidence.strategy_trade.dataset_count;"
+    )
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_trades) is not None
+
     seeded_bands_by_class = "const total = row.bands_by_class.A + row.bands_by_class.B;"
     assert _PRICE_ARITHMETIC_PATTERN.search(seeded_bands_by_class) is not None
 
diff --git a/apps/backend/tests/test_referee_evidence.py b/apps/backend/tests/test_referee_evidence.py
index 5b39f4b..fe2ffac 100644
--- a/apps/backend/tests/test_referee_evidence.py
+++ b/apps/backend/tests/test_referee_evidence.py
@@ -291,6 +291,121 @@ def test_module_docstring_pins_integrity_errors_as_part_of_the_response_shape():
     assert "strategy_trade.integrity_errors" in doc
 
 
+# --- goal-referee-iter-13 (J-12): the readiness fold gets its FIRST direct UI reader -----------------
+#
+# J-12 is a frontend-only iteration (apps/frontend/lib/api.ts::fetchRefereeEvidence() +
+# RefereeRegistrySection's own new blocks on /desk) -- zero production diff to this module. The two
+# tests below are the Backend (tests only) scope's own required proofs: a byte-identity check that
+# referee_evidence()'s served body never moved, and the unowned-frontend-literal guard (the
+# iteration-9 REFEREE_STARTER_FAMILY_ID/_Q precedent, test_referee_registry.py TC-17) extended to
+# the two disclosure strings this iteration's UI first renders.
+
+
+def test_referee_evidence_served_body_matches_the_pinned_golden_fixture(client):
+    """A byte-identity check proving referee_evidence()'s served body is unchanged by this
+    iteration's diff -- the WHOLE response dict, both blocks, every key, pinned against a
+    hand-computed fixture built through each store's own public write path (never a real
+    detect/backtest run). J-12 reads this endpoint for the first time in the browser; this test is
+    the durable proof its shape and values never moved (a future accidental edit to
+    referee_evidence.py breaks this test immediately, forcing a deliberate, named update)."""
+    c, playbook_store, dataset_store, journal_store = client
+    fingerprint = CONFIG.config_fingerprint()
+
+    record = _plant_playbook_record(
+        playbook_store, session_date="2026-06-08", signature="sig-golden",
+        signals=[_signal("capitulation", "long")],
+    )
+    basis = _record_detector_basis(record)
+    _plant_dataset(dataset_store, symbol="AAPL", split=SPLIT_TRAIN, source_id="ds-golden")
+    _plant_backtest(journal_store, backtest_id="bt-golden", trades=[{"net_r": 1.0}])
+
+    response = c.get("/research/desk/referee/evidence")
+    assert response.status_code == 200
+    # The one field derived through the module's own helper rather than hand-retyped: the
+    # met/unmet English sentence is already locked down exactly by
+    # test_strategy_readiness_names_the_unmet_tick_gate_and_the_forming_bar_caveat and
+    # test_tick_gate_state_unmet_branch above -- re-typing its full prose here would only risk a
+    # transcription mismatch against those tests' own source of truth, `_tick_gate_state` itself.
+    tick_gate_met, tick_gate_statement = _tick_gate_state(1)
+
+    assert response.json() == {
+        "playbook_occurrence": {
+            "detector_basis": basis,
+            "config_fingerprint": fingerprint,
+            "records": 1,
+            "distinct_sessions": 1,
+            "signals_at_current_basis": 1,
+            "per_setup_side": [
+                {"setup": "capitulation", "side": "long", "n": 1, "n_sessions": 1},
+            ],
+            "stale_basis_dates": [],
+            "integrity_errors": [],
+        },
+        "strategy_trade": {
+            "dataset_count": 1,
+            "per_split_counts": {"train": 1, "holdout": 0},
+            "trade_count": 1,
+            "tick_gate_met": tick_gate_met,
+            "tick_gate_statement": tick_gate_statement,
+            "basis_caveats": [REFEREE_FORMING_BAR_BASIS_CAVEAT],
+            "integrity_errors": [],
+        },
+    }
+
+
+# A substring invariant across BOTH the met/unmet branches of `_tick_gate_state` (the numeric
+# counts vary; this fragment does not) -- distinctive enough that no frontend prose would ever
+# coincidentally contain it, so its absence from frontend source is a meaningful guard.
+_TICK_GATE_STATEMENT_DISTINCTIVE_SUBSTRING = "Era-6 tick-corpus gate"
+
+# The SAME `apps/frontend` root + component/app/lib glob set `test_copy_discipline.py`'s own
+# frontend-literal scan already uses (re-declared locally per this codebase's own convention --
+# test_desk_ui_guards.py re-declares its own `_FRONTEND_ROOT` rather than importing one too).
+_EVIDENCE_LITERAL_GUARD_FRONTEND_ROOT = Path(__file__).resolve().parents[2] / "frontend"
+
+
+def _evidence_literal_guard_frontend_files() -> list[Path]:
+    root = _EVIDENCE_LITERAL_GUARD_FRONTEND_ROOT
+    return (
+        sorted(root.glob("components/**/*.tsx"))
+        + sorted(root.glob("components/**/*.ts"))
+        + sorted(root.glob("app/**/*.tsx"))
+        + sorted(root.glob("app/**/*.ts"))
+        + sorted(root.glob("lib/**/*.ts"))
+    )
+
+
+def test_tick_gate_statement_and_forming_bar_caveat_are_unowned_frontend_literals():
+    """TC-11: mirrors the iteration-9 REFEREE_STARTER_FAMILY_ID/_Q unowned-literal guard
+    (test_referee_registry.py TC-17) -- now that J-12 gives `tick_gate_statement`/
+    `REFEREE_FORMING_BAR_BASIS_CAVEAT` their first UI reader, neither string may ALSO be typed into
+    a frontend source file as a second, independently-drifting copy. Both reach the DOM only from
+    the GET /research/desk/referee/evidence payload at runtime."""
+    files = _evidence_literal_guard_frontend_files()
+    assert files, "no frontend source files found -- the scan cannot be vacuous"
+    offenders: list[str] = []
+    for path in files:
+        source = path.read_text()
+        rel = path.relative_to(_EVIDENCE_LITERAL_GUARD_FRONTEND_ROOT)
+        if _TICK_GATE_STATEMENT_DISTINCTIVE_SUBSTRING in source:
+            offenders.append(f"{rel}: hardcodes the tick-gate statement")
+        if REFEREE_FORMING_BAR_BASIS_CAVEAT in source:
+            offenders.append(f"{rel}: hardcodes the forming-bar basis caveat")
+    assert not offenders, (
+        "a referee evidence disclosure string was hardcoded into frontend source instead of read "
+        f"from the GET /research/desk/referee/evidence runtime payload: {offenders}"
+    )
+
+
+def test_tick_gate_statement_and_forming_bar_caveat_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail -- a lint that cannot fail proves nothing."""
+    seeded_tick_gate = f'const x = "{_TICK_GATE_STATEMENT_DISTINCTIVE_SUBSTRING} is unmet";'
+    assert _TICK_GATE_STATEMENT_DISTINCTIVE_SUBSTRING in seeded_tick_gate
+
+    seeded_caveat = f"const y = {REFEREE_FORMING_BAR_BASIS_CAVEAT!r};"
+    assert REFEREE_FORMING_BAR_BASIS_CAVEAT in seeded_caveat
+
+
 # === J-02: the typed evidence contract -- fixture builders (goal-referee-iter-2 TC-1..TC-9) ==========
 #
 # Every fixture below plants records through each store's own public write path
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 3771424..a990272 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -48,6 +48,7 @@ import {
   fetchRefereeAdjudications,
   fetchRefereeEvaluate,
   fetchRefereeEvaluateRuns,
+  fetchRefereeEvidence,
   fetchRefereeNullRuns,
   fetchRefereeNullsCompute,
   fetchRefereeRegistry,
@@ -123,6 +124,7 @@ import type {
   RefereeEvaluateRunsListResult,
   RefereeEvaluationComputeSnapshot,
   RefereeEvaluationRun,
+  RefereeEvidenceResponse,
   RefereeHypothesis,
   RefereeNullComputeSnapshot,
   RefereeNullRun,
@@ -4708,6 +4710,7 @@ function PlaybookEvidenceSection({
 function RefereeRegistrySection({
   shortlistResult,
   registryResult,
+  evidenceResult,
   selectedCandidateId,
   onSelect,
   onCancel,
@@ -4717,6 +4720,7 @@ function RefereeRegistrySection({
 }: {
   shortlistResult: { ok: boolean; data: RefereeShortlistResponse | null; error?: string } | null;
   registryResult: { ok: boolean; data: RefereeRegistryResponse | null; error?: string } | null;
+  evidenceResult: { ok: boolean; data: RefereeEvidenceResponse | null; error?: string } | null;
   selectedCandidateId: string | null;
   onSelect: (candidateId: string) => void;
   onCancel: () => void;
@@ -4910,6 +4914,8 @@ function RefereeRegistrySection({
         </h3>
         <RefereeHypothesesTable registryResult={registryResult} />
       </div>
+
+      <RefereeEvidenceReadinessSection evidenceResult={evidenceResult} />
     </div>
   );
 }
@@ -4984,6 +4990,215 @@ function RefereeHypothesesTable({
   );
 }
 
+// goal-referee-iter-13 (J-12): the readiness-fold blocks -- GET /research/desk/referee/evidence's
+// FIRST direct UI reader (registered since J-01/iteration-1; previously curl/tests-only). Rendered
+// directly BELOW the shipped Registered Hypotheses table above, inside the SAME "Referee Registry"
+// section -- not a new page, not a new nav entry, not a new CollapsibleSection (goal.md J-12 Step
+// 2). Its own Loading/Unavailable states, independent of shortlistResult/registryResult above (the
+// RefereeAdjudicationsSection precedent: each section's own deferred read gates its own slice,
+// never blocking an already-resolved sibling's render on a third, unrelated fetch). Two dense
+// text/table blocks, no cards/gauges (house style) -- every value a straight pass-through of the
+// fetched body, zero client-side arithmetic (test_desk_ui_guards.py's widened
+// _PRICE_ARITHMETIC_FIELDS covers every numeric read here), and every honest-absence case reuses
+// the shipped EmptyState component rather than rendering blank.
+function RefereeEvidenceReadinessSection({
+  evidenceResult,
+}: {
+  evidenceResult: { ok: boolean; data: RefereeEvidenceResponse | null; error?: string } | null;
+}) {
+  if (evidenceResult === null) {
+    return <LoadingPanel testid="referee-evidence-loading" />;
+  }
+  if (!evidenceResult.ok || evidenceResult.data === null) {
+    return (
+      <UnavailablePanel
+        testid="referee-evidence-unavailable"
+        message={evidenceResult.error ?? "The referee evidence readiness could not be loaded."}
+      />
+    );
+  }
+  const evidence = evidenceResult.data;
+  return (
+    <div data-testid="referee-evidence-section" className="mt-4 border-t border-slate-800 pt-4">
+      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
+        Evidence Readiness
+      </h3>
+      <p className="mb-3 text-xs text-slate-500">
+        Why each evidence family is or is not ready for confirmatory statistics (GET
+        /research/desk/referee/evidence, read verbatim) — the tick-gate statement and the
+        no-lookahead forming-bar caveat below gate confirmatory use of the strategy family.
+      </p>
+
+      <div data-testid="referee-evidence-playbook-block" className="mb-4">
+        <h4 className="mb-2 text-xs font-semibold text-slate-400">Playbook Family</h4>
+        <div className="overflow-x-auto">
+          <table
+            data-testid="referee-evidence-playbook-table"
+            className="w-full min-w-[420px] border-collapse text-xs"
+          >
+            <tbody>
+              <tr className="border-b border-slate-900">
+                <td className="px-1.5 py-1 text-slate-500">Records</td>
+                <td
+                  data-testid="referee-evidence-playbook-records"
+                  className="px-1.5 py-1 text-right font-mono text-slate-300"
+                >
+                  {evidence.playbook_occurrence.records}
+                </td>
+              </tr>
+              <tr className="border-b border-slate-900">
+                <td className="px-1.5 py-1 text-slate-500">Distinct sessions</td>
+                <td
+                  data-testid="referee-evidence-playbook-distinct-sessions"
+                  className="px-1.5 py-1 text-right font-mono text-slate-300"
+                >
+                  {evidence.playbook_occurrence.distinct_sessions}
+                </td>
+              </tr>
+              <tr>
+                <td className="px-1.5 py-1 text-slate-500">Signals at current basis</td>
+                <td
+                  data-testid="referee-evidence-playbook-signals-at-current-basis"
+                  className="px-1.5 py-1 text-right font-mono text-slate-300"
+                >
+                  {evidence.playbook_occurrence.signals_at_current_basis}
+                </td>
+              </tr>
+            </tbody>
+          </table>
+        </div>
+        <p
+          data-testid="referee-evidence-playbook-basis-line"
+          className="mt-2 text-[11px] text-slate-500"
+        >
+          Detector basis{" "}
+          <span
+            data-testid="referee-evidence-playbook-detector-basis"
+            className="font-mono text-slate-400"
+          >
+            {evidence.playbook_occurrence.detector_basis}
+          </span>
+          {" · "}config fingerprint{" "}
+          <span
+            data-testid="referee-evidence-playbook-config-fingerprint"
+            className="font-mono text-slate-400"
+          >
+            {evidence.playbook_occurrence.config_fingerprint}
+          </span>
+        </p>
+        {evidence.playbook_occurrence.stale_basis_dates.length === 0 ? (
+          <EmptyState
+            testid="referee-evidence-playbook-stale-basis-empty"
+            title="No stale basis dates."
+          />
+        ) : (
+          <ul
+            data-testid="referee-evidence-playbook-stale-basis-dates"
+            className="mt-2 space-y-0.5 text-[11px] text-amber-300"
+          >
+            {evidence.playbook_occurrence.stale_basis_dates.map((entry) => (
+              <li key={`${entry.session_date}:${entry.record_detector_basis}`}>
+                {entry.session_date} — {entry.record_detector_basis}
+              </li>
+            ))}
+          </ul>
+        )}
+        {evidence.playbook_occurrence.integrity_errors.length === 0 ? (
+          <EmptyState
+            testid="referee-evidence-playbook-integrity-errors-empty"
+            title="No integrity errors."
+          />
+        ) : (
+          <ul
+            data-testid="referee-evidence-playbook-integrity-errors"
+            className="mt-2 space-y-0.5 text-[11px] text-red-300"
+          >
+            {evidence.playbook_occurrence.integrity_errors.map((e) => (
+              <li key={e.file}>
+                {e.file}: {e.error}
+              </li>
+            ))}
+          </ul>
+        )}
+      </div>
+
+      <div data-testid="referee-evidence-strategy-block">
+        <h4 className="mb-2 text-xs font-semibold text-slate-400">Strategy Family</h4>
+        <div className="overflow-x-auto">
+          <table
+            data-testid="referee-evidence-strategy-table"
+            className="w-full min-w-[420px] border-collapse text-xs"
+          >
+            <tbody>
+              <tr className="border-b border-slate-900">
+                <td className="px-1.5 py-1 text-slate-500">Datasets</td>
+                <td
+                  data-testid="referee-evidence-strategy-dataset-count"
+                  className="px-1.5 py-1 text-right font-mono text-slate-300"
+                >
+                  {evidence.strategy_trade.dataset_count}
+                </td>
+              </tr>
+              <tr className="border-b border-slate-900">
+                <td className="px-1.5 py-1 text-slate-500">Train / Holdout</td>
+                <td className="px-1.5 py-1 text-right font-mono text-slate-300">
+                  <span data-testid="referee-evidence-strategy-train-count">
+                    {evidence.strategy_trade.per_split_counts.train}
+                  </span>
+                  {" / "}
+                  <span data-testid="referee-evidence-strategy-holdout-count">
+                    {evidence.strategy_trade.per_split_counts.holdout}
+                  </span>
+                </td>
+              </tr>
+              <tr>
+                <td className="px-1.5 py-1 text-slate-500">Trades</td>
+                <td
+                  data-testid="referee-evidence-strategy-trade-count"
+                  className="px-1.5 py-1 text-right font-mono text-slate-300"
+                >
+                  {evidence.strategy_trade.trade_count}
+                </td>
+              </tr>
+            </tbody>
+          </table>
+        </div>
+        <p
+          data-testid="referee-evidence-strategy-tick-gate"
+          className="mt-2 text-[11px] text-slate-400"
+        >
+          {evidence.strategy_trade.tick_gate_statement}
+        </p>
+        <ul
+          data-testid="referee-evidence-strategy-basis-caveats"
+          className="mt-2 space-y-1 text-[11px] text-slate-500"
+        >
+          {evidence.strategy_trade.basis_caveats.map((caveat) => (
+            <li key={caveat}>{caveat}</li>
+          ))}
+        </ul>
+        {evidence.strategy_trade.integrity_errors.length === 0 ? (
+          <EmptyState
+            testid="referee-evidence-strategy-integrity-errors-empty"
+            title="No integrity errors."
+          />
+        ) : (
+          <ul
+            data-testid="referee-evidence-strategy-integrity-errors"
+            className="mt-2 space-y-0.5 text-[11px] text-red-300"
+          >
+            {evidence.strategy_trade.integrity_errors.map((e) => (
+              <li key={e.file}>
+                {e.file}: {e.error}
+              </li>
+            ))}
+          </ul>
+        )}
+      </div>
+    </div>
+  );
+}
+
 // goal-referee-iter-10 (J-09): the Referee Adjudications section -- the read-side adjudication fold
 // (verdict chips in the exact vocabulary + full provenance), rendered directly BELOW Referee
 // Registry. A single deferred GET, no compute manager, no poll (GET never computes, T-8) -- the
@@ -8420,6 +8635,16 @@ export default function DeskPage() {
     data: RefereeRegistryResponse | null;
     error?: string;
   } | null>(null);
+  // goal-referee-iter-13 (J-12): the readiness-fold blocks' own state -- a THIRD independent
+  // deferred read issued alongside the shortlist/registry pair on first expand (same
+  // `toggleSection("refereeRegistry")` branch, T-8: GETs never compute). GET
+  // /research/desk/referee/evidence's first UI reader; ZERO backend product diff (referee_evidence()
+  // has served this shape since J-01/iteration-1).
+  const [refereeEvidenceResult, setRefereeEvidenceResult] = useState<{
+    ok: boolean;
+    data: RefereeEvidenceResponse | null;
+    error?: string;
+  } | null>(null);
   const [refereeSelectedCandidateId, setRefereeSelectedCandidateId] = useState<string | null>(null);
   const [refereeRegistering, setRefereeRegistering] = useState(false);
   const [refereeRegisterError, setRefereeRegisterError] = useState<string | null>(null);
@@ -8499,6 +8724,10 @@ export default function DeskPage() {
     } else if (section === "refereeRegistry") {
       fetchRefereeShortlist().then(setRefereeShortlistResult);
       fetchRefereeRegistry().then(setRefereeRegistryResult);
+      // goal-referee-iter-13 (J-12): the readiness-fold blocks' own read, issued alongside the
+      // shortlist/registry pair above -- a THIRD call inside this SAME branch, not a new
+      // useEffect, so test_desk_refresh_chain_guard.py's _EXPECTED_EFFECT_COUNT stays unchanged.
+      fetchRefereeEvidence().then(setRefereeEvidenceResult);
     } else if (section === "refereeAdjudications") {
       fetchRefereeAdjudications().then(setRefereeAdjudicationsResult);
       // Also (re)fetches the registry -- Adjudications cross-references each entry's own
@@ -10534,6 +10763,7 @@ export default function DeskPage() {
             <RefereeRegistrySection
               shortlistResult={refereeShortlistResult}
               registryResult={refereeRegistryResult}
+              evidenceResult={refereeEvidenceResult}
               selectedCandidateId={refereeSelectedCandidateId}
               onSelect={setRefereeSelectedCandidateId}
               onCancel={() => {
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 1a283ad..fed8889 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -44,6 +44,7 @@ import type {
   RefereeAdjudicationsResponse,
   RefereeEvaluateRunsListResult,
   RefereeEvaluationComputeSnapshot,
+  RefereeEvidenceResponse,
   RefereeHypothesis,
   RefereeHypothesisRegistrationPayload,
   RefereeNullComputeSnapshot,
@@ -2118,6 +2119,35 @@ export async function fetchRefereeRegistry(): Promise<{
   }
 }
 
+// GET /research/desk/referee/evidence -- the readiness fold (goal-referee-iter-13, J-12): this
+// endpoint's FIRST direct UI reader (registered since J-01/iteration-1; previously curl/tests-only
+// -- zero frontend grep hits beyond an unrelated type name). Served VERBATIM -- zero client-side
+// arithmetic on any numeric this component reads (test_desk_ui_guards.py's widened
+// _PRICE_ARITHMETIC_FIELDS covers every one). ZERO backend product diff this iteration: no new
+// field, no new value, no new Data Contract row, no new owner, no new MCP tool.
+export async function fetchRefereeEvidence(): Promise<{
+  ok: boolean;
+  data: RefereeEvidenceResponse | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/referee/evidence`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as RefereeEvidenceResponse };
+    }
+    let error = "The referee evidence readiness could not be loaded.";
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
index 55054f1..603f2be 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -2424,3 +2424,53 @@ export interface RefereeEvaluateRunsListResult {
   latest: RefereeEvaluationRun | null;
   integrity_errors: RefereeIntegrityError[];
 }
+
+// --- Era 6 "The Referee" (goal-referee-iter-13, J-12) -- GET /research/desk/referee/evidence's
+// FIRST direct UI reader. `app/research/referee_evidence.py::referee_evidence()` has served this
+// shape since J-01 (iteration 1); this iteration adds ZERO backend field/value -- every interface
+// below matches the served body field-for-field (docs/goal.md J-12 Step 1). Each block's own
+// `integrity_errors` is the plain `{file, error}[]` shape every OTHER single-store desk section
+// already uses (DeskTopupRunsListResult et al., types.ts:1020/1087/1152/... — 9+ precedents) --
+// distinct from `RefereeIntegrityError[]` above (registry/adjudications), which labels errors
+// across FOUR stores and so carries an extra `store` field neither `playbook_occurrence` nor
+// `strategy_trade` needs (each reads exactly ONE store's own `.list()`, confirmed by reading
+// referee_evidence.py's `playbook_occurrence_readiness()`/`strategy_trade_readiness()` live).
+
+export interface RefereeEvidencePerSetupSideCell {
+  setup: string;
+  side: string;
+  n: number;
+  n_sessions: number;
+}
+
+export interface RefereeEvidenceStaleBasisDate {
+  session_date: string;
+  record_detector_basis: string;
+}
+
+export interface RefereePlaybookOccurrenceReadiness {
+  detector_basis: string;
+  config_fingerprint: string;
+  records: number;
+  distinct_sessions: number;
+  signals_at_current_basis: number;
+  per_setup_side: RefereeEvidencePerSetupSideCell[];
+  stale_basis_dates: RefereeEvidenceStaleBasisDate[];
+  integrity_errors: { file: string; error: string }[];
+}
+
+export interface RefereeStrategyTradeReadiness {
+  dataset_count: number;
+  per_split_counts: { train: number; holdout: number };
+  trade_count: number;
+  tick_gate_met: boolean;
+  tick_gate_statement: string;
+  basis_caveats: string[];
+  integrity_errors: { file: string; error: string }[];
+}
+
+// GET /research/desk/referee/evidence -- the readiness fold, served verbatim.
+export interface RefereeEvidenceResponse {
+  playbook_occurrence: RefereePlaybookOccurrenceReadiness;
+  strategy_trade: RefereeStrategyTradeReadiness;
+}
diff --git a/docs/goal.md b/docs/goal.md
index dad6746..5cc6e70 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -803,6 +803,79 @@ certificate checking).
     actions (`goto`/`click`/`fill`/`expect`/`wait_for`; it rejects `scroll`).
     *(Browser-verifiable; keyless via the fixture-scoped backend; no real store written.)*
 
+- **J-12: The readiness fold gets its reader — why a family cannot speak, visible on the desk**
+  - Steps:
+    1. Bind the ALREADY-CANONICAL endpoint to the UI without adding one value to it: a
+       `fetchRefereeEvidence()` in `apps/frontend/lib/api.ts` plus its response types in
+       `lib/types.ts`, in the established `{ok, data, error?}` shape, reading
+       `GET /research/desk/referee/evidence` — the Data Contract row "Referee evidence coverage +
+       per-family readiness", whose owner `app/research/referee_evidence.py` already computes every
+       field exactly once. ZERO backend product diff: `referee_evidence()`'s served body stays
+       byte-identical (golden before/after), no new field, no new value, no new Data Contract row,
+       no new owner, and no new MCP tool (the contract stays exactly 22 — the endpoint remains
+       readable from a conversation through the existing `get_endpoint` `/research/` allowlist).
+    2. Render it inside the shipped **Referee Registry** section on `/desk`, BELOW the shipped
+       registered-hypotheses table so not one shipped row, column, heading, or `data-testid`
+       moves — two dense blocks in house style (tables and text, no cards/gauges):
+       **playbook family** — `records`, `distinct_sessions`, `signals_at_current_basis`, the
+       `detector_basis` + `config_fingerprint` identity, and the `stale_basis_dates` list verbatim
+       in served order (an empty list renders its own honest sentence, never a blank);
+       **strategy family** — `dataset_count`, `per_split_counts.train`/`.holdout`, `trade_count`,
+       the `tick_gate_statement` verbatim, and every `basis_caveats` entry verbatim (today the
+       Card-6.4 forming-bar lookahead disclosure — the era's own stated condition for deferring
+       that fix, currently served to `curl` and to nothing else); plus each block's
+       `integrity_errors` as an explicit disclosure row (empty ⇒ its own "no integrity errors"
+       line) so a corrupt playbook/dataset file is visible to the operator, not only to a reader
+       of the raw endpoint. The fetch rides the section's established deferred-fetch dispatch (the
+       same `toggleSection("refereeRegistry")` branch that already calls `fetchRefereeShortlist`/
+       `fetchRefereeRegistry`) and is NOT a new React effect, so
+       `tests/test_desk_refresh_chain_guard.py`'s `_EXPECTED_EFFECT_COUNT` stays byte-unchanged and
+       page load still fetches and computes nothing (T-8).
+    3. Prove the copy keeps ONE owner: a guard test asserts the served `tick_gate_statement` and
+       `REFEREE_FORMING_BAR_BASIS_CAVEAT` sentences appear in NO frontend source file — they reach
+       the DOM only from the payload at runtime — applying the iteration-9 rider's own
+       unowned-frontend-literal lesson (`REFEREE_STARTER_FAMILY_ID`/`_Q`) before a second copy of
+       an honesty disclosure can be born.
+    4. Extend the guards deliberately: every served referee numeric this component reads joins
+       `tests/test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS` with its seeded counter-test in
+       the established referee shape (these are counts, not prices — the section's "no client-side
+       arithmetic on any served numeric" contract, full stop); new `data-testid`s and new heading
+       strings only, reusing no shipped heading or `data-testid` and statically swept against the
+       stored replay scripts (T-11); `tests/test_copy_discipline.py` stays green with the rendered
+       gate/caveat copy included (descriptive statistics only — no advice, no prediction, no profit
+       phrasing).
+  - Acceptance: on the fixture rig, the Referee Registry section renders both readiness blocks with
+    the fixture's hand-computed counts exact, and the strategy family's `tick_gate_statement` and
+    every `basis_caveats` entry byte-identical to the strings
+    `GET /research/desk/referee/evidence` serves (compared string-for-string against that same
+    rig's served body in the test, never against a re-typed literal); an empty-corpus fixture
+    renders the honest all-zero/absent state rather than a blank, a spinner, or a 404 path. Single
+    source of truth: this journey introduces NO new value anywhere — every rendered number and
+    sentence is read verbatim from the one canonical endpoint the Data Contract already names
+    (`app/research/referee_evidence.py` / `GET /research/desk/referee/evidence`), with zero
+    client-side arithmetic, zero client-authored copy, no second computation path, no new owner,
+    and no new Data Contract row; MCP stays exactly 22 tools. In a real browser after the T-9 clean
+    rebuild: the Referee Registry section renders both blocks with every value matching that
+    backend's own served `/research/desk/referee/evidence` body exactly, and every other shipped
+    `/desk` section renders exactly as shipped in the same pass (screenshots; no screenshot ⇒
+    `unknown`, never `passing`). Frozen foundations: engine equivalence green,
+    `Config().config_fingerprint()` prints `08e471b10130e1e2`, zero new `Config` fields,
+    `referee_parameters()` byte-unchanged, zero diff to every `app/research/referee_*.py` module,
+    to `desk_playbook*.py`, `desk_forward.py`, `levels.py`, `tradability.py`, and `pnl_scan.py`,
+    and every previously recorded store file byte-identical (SHA-256 listing before/after, referee
+    dirs included — the endpoint is a pure read and this journey writes no store). PnL basis,
+    stated rather than fabricated: this journey changes no strategy, profile, backtest, or
+    champion, so it appends NO PnL-ledger row and proves it — the `default`-profile equivalence
+    test green and the PnL ledger + champion pointer byte-identical before/after (SHA-256);
+    inventing a ledger row for a read-side disclosure would breach the era's append-only ledger
+    rail. Full backend suite green with no test removed or weakened (iteration-12 baseline: 2,695
+    collected / 2,687 passed / 8 skipped). Walkthrough: a `[NEW]`-flagged demo-narrator walkthrough
+    of the new surface — `goto /desk` → `click` the "Referee Registry" section header → `expect`
+    the strategy family's tick-gate sentence and the forming-bar caveat — written with only the
+    shared recorder's supported actions (`goto`/`click`/`fill`/`expect`/`wait_for`; it rejects
+    `scroll`).
+    *(Browser-verifiable; keyless — a pure read over already-recorded stores.)*
+
 <!-- /AUTO:journeys -->
 
 ## Anti-goals
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-referee/state/assumptions.md     | 32 ++++++++++++++++++++++
 runs/goal-session-referee/state/blueprint.md       | 25 ++++++++++++++++-
 .../state/enhancement-proposals.jsonl              |  1 +
 .../state/proposer-result.json                     |  8 +++++-
 runs/goal-session-referee/telemetry.jsonl          | 18 ++++++++++++
 runs/goal-session-referee/trace/trace.jsonl        |  3 ++
 6 files changed, 85 insertions(+), 2 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
