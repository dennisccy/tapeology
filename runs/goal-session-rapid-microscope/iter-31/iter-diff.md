# Iteration diff (bounded)

Files changed: 7. Shown in full: 7.

```diff
diff --git a/apps/backend/app/mcp/__init__.py b/apps/backend/app/mcp/__init__.py
index 71256789..40f5d21a 100644
--- a/apps/backend/app/mcp/__init__.py
+++ b/apps/backend/app/mcp/__init__.py
@@ -21,9 +21,9 @@ Result contract (locked by ``tests/test_mcp_server.py``):
     era-5B J-04; ``desk_universe``/``desk_screen`` at era-desk J-06; ``desk_playbook``/
     ``desk_playbook_evidence`` at Era B2 J-09; ``desk_referee``/``desk_referee_registry`` at Era 6
     "The Referee" J-09; ``desk_micro_readiness``/``desk_scout``/``desk_walkforward``/``desk_vault``
-    at Era "The Rapid Microscope" J-08, MCP contract v6 — 22 -> 26 tools); an
-    allowlisted-but-UNKNOWN path (any unshipped ``/research/*``) still surfaces the backend's
-    honest 404 this way — never placeholder data.
+    at Era "The Rapid Microscope" J-08, MCP contract v6 — 22 -> 26 tools; ``desk_graduation`` at
+    J-11, MCP contract v7 — 26 -> 27 tools); an allowlisted-but-UNKNOWN path (any unshipped
+    ``/research/*``) still surfaces the backend's honest 404 this way — never placeholder data.
   * backend unreachable — an explicit tool error naming the base URL and the failure
     (``BackendUnreachableError``); NEVER cached or fabricated data (no cache, no retry loop,
     no offline snapshot exists anywhere in this module).
@@ -150,6 +150,12 @@ _STATIC_PATHS: dict[str, str] = {
     "desk_scout": "/research/desk/micro/scout",
     "desk_walkforward": "/research/desk/micro/walkforward",
     "desk_vault": "/research/desk/micro/vault",
+    # `desk_graduation` (J-11, MCP contract v7 -- 26 -> 27 tools) is the IDENTICAL no-required-
+    # param shape as its four dependency-order siblings directly above: it proxies the funnel's
+    # terminal-state endpoint, which already serves an explicit HTTP 200 honest-empty payload
+    # (an empty `families` list plus the ledger's own `message`) before any candidate has ever
+    # graduated (never a 404). No query-param variant exists.
+    "desk_graduation": "/research/desk/micro/graduation",
 }
 
 _TAPE_PATHS: dict[str, str] = {
@@ -469,6 +475,18 @@ TOOLS: tuple[types.Tool, ...] = (
         ),
         inputSchema=_object_schema({}),
     ),
+    types.Tool(
+        name="desk_graduation",
+        description=(
+            "Read-only proxy of GET /research/desk/micro/graduation -- the Rapid Microscope "
+            "funnel's terminal state: every candidate family's current graduation stage "
+            "(exploratory / walkforward_survivor / sealed_survivor / referee_handoff_ready), its "
+            "complete transition history, and its complete sealed-shard-evaluation history "
+            "(including permanent failed verdicts), beside the ledger's own chain-verification "
+            "verdict -- JSON verbatim. Never 404/500 on an empty ledger."
+        ),
+        inputSchema=_object_schema({}),
+    ),
     types.Tool(
         name="pnl_ledger",
         description=(
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index ba02cc52..d3c2d5bf 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -333,6 +333,15 @@ _PRICE_ARITHMETIC_FIELDS = (
     r"|readiness\.sealed_tranche\.(?:shard_count|symbol_days)"
     r"|universeCounts\.(?:shard_count|symbol_days)"
     r"|readiness\.joinable_corpus\.(?:withheld_excluded)"
+    # goal-rapid-microscope-iter-31 (J-11): the new Graduation section's own served numeric --
+    # GET /research/desk/micro/graduation read verbatim for the first time in the browser. Each
+    # sealed-evaluation row's own observation count (`evaluation.n`, `GraduationSealedEvaluation
+    # Row`'s destructured field) is the only graduation numeric the section binds to a local name
+    # directly -- every OTHER field of a transition/sealed-evaluation row (heterogeneous by
+    # transition target state / evaluation artifact shape) is rendered via `JSON.stringify(...)`
+    # (a serialization call, never arithmetic, the `screen_result`/raw `fold_results` precedent),
+    # so no per-field entry is needed for those.
+    r"|evaluation\.(?:n)"
 )
 _PRICE_ARITHMETIC_PATTERN = re.compile(
     rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
@@ -1970,3 +1979,30 @@ def test_the_cohort_filter_copy_is_clean():
     for phrase in phrases:
         assert phrase in source, f"expected cohort copy missing: {phrase!r}"
         assert find_violations(phrase) == [], phrase
+
+
+# goal-rapid-microscope-iter-31 (J-11): the new Graduation section's price-arithmetic guard --
+# TC-5's own seeded counter-test proving the extended `_PRICE_ARITHMETIC_FIELDS` pattern is live,
+# not vacuous.
+
+
+def test_desk_page_price_arithmetic_guard_catches_graduation_evaluation_n_arithmetic():
+    """TC-5 counter-test: a client-side sum/rate over the new `evaluation.n` binding (the Graduation
+    section's own sealed-evaluation observation count) is caught, exactly like every other served
+    numeric this guard already covers."""
+    seeded_sum = "const total = evaluation.n + evaluation.n;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_sum) is not None
+
+
+def test_desk_page_graduation_section_never_derives_a_second_computation_of_the_referee_note():
+    """J-11's own Acceptance text ("no second computation path"): the Graduation section's static
+    `referee_handoff_ready` copy is transcribed BYTE-FOR-BYTE from `micro_graduation.py`'s own
+    `REFEREE_FUTURE_REVISION_SENTENCE` -- proven here by importing the backend constant directly and
+    asserting it appears verbatim in the frontend source, so the two can never silently drift."""
+    from app.research.micro_graduation import REFEREE_FUTURE_REVISION_SENTENCE
+
+    source = _DESK_PAGE.read_text()
+    assert REFEREE_FUTURE_REVISION_SENTENCE in source, (
+        "the Graduation section's referee_handoff_ready copy does not match "
+        "micro_graduation.REFEREE_FUTURE_REVISION_SENTENCE byte-for-byte"
+    )
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index 55cc863a..acbcc198 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -49,6 +49,11 @@ from app.research.desk_universe import UniverseStore
 from app.research.referee_adjudicate import REFEREE_REGISTER
 from app.research.referee_null import REFEREE_NULL_TOD_SPEC_ID, REFEREE_TEST_PERM_SPEC_ID
 from app.research.referee_registry import REFEREE_MIN_OCCURRENCES, REFEREE_MIN_SESSIONS
+from app.research.micro_graduation import (
+    GRADUATION_STATE_WALKFORWARD_SURVIVOR,
+    GraduationLedger,
+    ROW_KIND_STATE_TRANSITION,
+)
 from app.research.scout_ledger import ScoutLedger
 
 # Era "The Rapid Microscope" J-08's own opaque-pool-critical proof reuses, rather than
@@ -77,10 +82,11 @@ BACKEND_DIR = Path(__file__).resolve().parents[1]
 # tools), ``desk_forward`` (forward-test era, 17 -> 18 tools), ``desk_playbook``/
 # ``desk_playbook_evidence`` (Era B2 "The Playbook" J-09, the era's own MCP contract v4 -- 18 -> 20
 # tools), ``desk_referee``/``desk_referee_registry`` (Era 6 "The Referee" J-09, MCP contract v5 --
-# 20 -> 22 tools), and ``desk_micro_readiness``/``desk_scout``/``desk_walkforward``/``desk_vault``
-# (Era "The Rapid Microscope" J-08, the era's own MCP contract v6 -- 22 -> 26 tools) are the newest
-# additions, each positioned right after its dependency-order sibling (the same store/registry+
-# route+MCP shape, mirrored end to end).
+# 20 -> 22 tools), ``desk_micro_readiness``/``desk_scout``/``desk_walkforward``/``desk_vault``
+# (Era "The Rapid Microscope" J-08, the era's own MCP contract v6 -- 22 -> 26 tools), and
+# ``desk_graduation`` (J-11, MCP contract v7 -- 26 -> 27 tools) are the newest additions, each
+# positioned right after its dependency-order sibling (the same store/registry+route+MCP shape,
+# mirrored end to end).
 EXPECTED_TOOLS = (
     "tape_state",
     "tape_features",
@@ -104,6 +110,7 @@ EXPECTED_TOOLS = (
     "desk_scout",
     "desk_walkforward",
     "desk_vault",
+    "desk_graduation",
     "pnl_ledger",
     "taxonomy",
     "ui_route_map",
@@ -160,6 +167,7 @@ def backend_paths(tmp_path_factory):
         "TAPEOLOGY_MICRO_SCOUT_DIR": str(tmp_path_factory.mktemp("mcp-micro-scout")),
         "TAPEOLOGY_MICRO_WALKFORWARD_DIR": str(tmp_path_factory.mktemp("mcp-micro-walkforward")),
         "TAPEOLOGY_MICRO_VAULT_DIR": str(tmp_path_factory.mktemp("mcp-micro-vault")),
+        "TAPEOLOGY_MICRO_GRADUATION_DIR": str(tmp_path_factory.mktemp("mcp-micro-graduation")),
     }
 
 
@@ -1163,6 +1171,58 @@ async def test_desk_vault_tool_byte_identical_on_a_populated_state(mcp_env, back
     assert result.content[0].text.encode("utf-8") == rest.content, "desk_vault not byte-identical"
 
 
+# desk_graduation (J-11, MCP contract v7, 26 -> 27 tools; empty + populated) -------------------------
+#
+# The IDENTICAL desk_vault precedent directly above: seeded through `GraduationLedger.append_row()`
+# -- the ledger's own public write path -- into the live backend's env-scoped
+# `TAPEOLOGY_MICRO_GRADUATION_DIR`, never through a live graduation-evaluation compute (J-11 is
+# keyless/automated; no operator compute act triggers a graduation transition this era).
+
+
+@pytest.mark.anyio
+async def test_desk_graduation_tool_byte_identical_on_the_honest_empty_state(mcp_env):
+    """Before any candidate has ever graduated, `desk_graduation` proxies `GET /research/desk/
+    micro/graduation`'s explicit HTTP 200 honest-empty payload -- an empty `families` list, the
+    ledger's own `EMPTY_LEDGER_MESSAGE`, and an `ok` chain verification -- never a 404."""
+    result = await call_tool("desk_graduation", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/micro/graduation", timeout=5.0)
+    assert rest.status_code == 200
+    assert rest.json() == {
+        "families": [],
+        "message": "No candidates ledgered.",
+        "chain_verification": {"ok": True, "failed_at_row": None, "reason": None},
+    }
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_graduation not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_desk_graduation_tool_byte_identical_on_a_populated_state(mcp_env, backend_paths):
+    """Seed ONE real state-transition row directly through `GraduationLedger.append_row()` into the
+    live backend's env-scoped `TAPEOLOGY_MICRO_GRADUATION_DIR`, then prove the tool's JSON is
+    byte-identical to its curl equivalent on a NON-EMPTY result."""
+    graduation_dir = Path(backend_paths["TAPEOLOGY_MICRO_GRADUATION_DIR"])
+    GraduationLedger(graduation_dir).append_row(
+        {
+            "row_kind": ROW_KIND_STATE_TRANSITION,
+            "family_root_id": "mcp-test-graduation-root",
+            "sequence_id": "mcp-test-sequence",
+            "from_state": "exploratory",
+            "to_state": GRADUATION_STATE_WALKFORWARD_SURVIVOR,
+            "evaluated_at": "2026-08-24T00:00:00Z",
+        }
+    )
+    result = await call_tool("desk_graduation", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/micro/graduation", timeout=5.0)
+    assert rest.status_code == 200
+    body = rest.json()
+    assert len(body["families"]) >= 1, "the live list must be non-empty for this proof"
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_graduation not byte-identical"
+
+
 @pytest.mark.anyio
 async def test_tr2_the_new_mcp_tools_leak_nothing_about_a_sealed_shard(tmp_path, monkeypatch):
     """The round's opaque-pool-critical proof (goal.md's own carried-forward reminder): closes the
@@ -1174,7 +1234,7 @@ async def test_tr2_the_new_mcp_tools_leak_nothing_about_a_sealed_shard(tmp_path,
     `_record_distinctive_dataset`/`_scope_everything_to`/`_scalars`) -- then spawns a DEDICATED,
     freshly hermetic backend subprocess over that exact store (never the shared module-scoped
     `backend` fixture, whose dataset dir has already accumulated many other tests' recordings by
-    the time this test runs) and calls every one of the 26 registered MCP tools against it,
+    the time this test runs) and calls every one of the 27 registered MCP tools against it,
     asserting the sealed shard's raw dataset id, raw content checksum, symbol, session date,
     window bounds, and exact trade/quote counts appear in ZERO tool response bodies.
 
@@ -1257,7 +1317,7 @@ async def test_tr2_the_new_mcp_tools_leak_nothing_about_a_sealed_shard(tmp_path,
             "get_endpoint": {"path": "/research/datasets"},
         }
 
-        assert len(TOOL_NAMES) == 26, "the 26-tool contract must hold for this sweep to be complete"
+        assert len(TOOL_NAMES) == 27, "the 27-tool contract must hold for this sweep to be complete"
         leaks: list[str] = []
         for name in TOOL_NAMES:
             result = await call_tool(name, args_for.get(name, {}))
@@ -1927,9 +1987,10 @@ async def test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool(mcp_
     assert result.content[0].text.encode("utf-8") == rest.content, "topup/runs not byte-identical"
     assert rest.json() == {"runs": [], "latest": None, "integrity_errors": []}
     # goal-rapid-microscope-iter-15: the total grew 22 -> 26 (desk_micro_readiness/desk_scout/
-    # desk_walkforward/desk_vault) -- this route's own no-new-tool claim is unaffected, so only
-    # the tracked total is re-derived here.
-    assert "desk_topup_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 26
+    # desk_walkforward/desk_vault); iter-31 (J-11) grew it again, 26 -> 27 (desk_graduation) --
+    # this route's own no-new-tool claim is unaffected, so only the tracked total is re-derived
+    # here.
+    assert "desk_topup_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 27
 
 
 @pytest.mark.anyio
@@ -1949,9 +2010,10 @@ async def test_get_endpoint_desk_screen_runs_byte_identical_with_no_new_tool(mcp
     assert result.content[0].text.encode("utf-8") == rest.content, "screen/runs not byte-identical"
     assert rest.json() == {"runs": [], "latest": None, "integrity_errors": []}
     # goal-rapid-microscope-iter-15: the total grew 22 -> 26 (desk_micro_readiness/desk_scout/
-    # desk_walkforward/desk_vault) -- this route's own no-new-tool claim is unaffected, so only
-    # the tracked total is re-derived here.
-    assert "desk_screen_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 26
+    # desk_walkforward/desk_vault); iter-31 (J-11) grew it again, 26 -> 27 (desk_graduation) --
+    # this route's own no-new-tool claim is unaffected, so only the tracked total is re-derived
+    # here.
+    assert "desk_screen_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 27
 
 
 @pytest.mark.anyio
diff --git a/apps/backend/tests/test_vault.py b/apps/backend/tests/test_vault.py
index 06ee5c8b..81cfdd97 100644
--- a/apps/backend/tests/test_vault.py
+++ b/apps/backend/tests/test_vault.py
@@ -773,6 +773,9 @@ def test_tr2_no_registered_get_route_serves_or_derives_a_sealed_shards_identity(
         assert swept["/research/datasets"] == 200
         assert swept["/research/desk/micro/vault"] == 200
         assert swept["/research/desk/micro/readiness"] == 200
+        # goal-rapid-microscope-iter-31 (J-11): `desk_graduation`'s own REST route -- confirmed
+        # covered by this SAME structural sweep (never a second, route-by-route sweep of its own).
+        assert swept["/research/desk/micro/graduation"] == 200
         assert swept["/research/datasets/{dataset_id}"] == 403  # the sealed id, refused
 
         # --- the join attack, EXECUTED (not merely asserted absent) -------------------------
@@ -897,6 +900,10 @@ def test_tr2_the_mcp_surface_is_closed_structurally_not_route_by_route(tmp_path,
     swept = set(_sweepable_get_paths())
     research_tool_paths = {p for p in _STATIC_PATHS.values() if p.startswith("/research/")}
     assert "/research/datasets" in research_tool_paths  # the `datasets` tool r3 names explicitly
+    # goal-rapid-microscope-iter-31 (J-11): `desk_graduation` is now wired into `_STATIC_PATHS` --
+    # a direct, non-vacuous proof the new tool is actually present in this set (not merely implied
+    # by the subset assertion below, which would still pass if the entry were silently missing).
+    assert "/research/desk/micro/graduation" in research_tool_paths
     assert research_tool_paths <= swept
 
     reachable = {p for p in swept if p.startswith(ALLOWED_GET_PREFIXES) and "{" not in p}
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 652cc174..86a96abd 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -62,6 +62,7 @@ import {
   fetchDeskScout,
   fetchDeskScoutCompute,
   fetchDeskScoutRuns,
+  fetchDeskGraduation,
   fetchDeskVault,
   fetchDeskWalkforward,
   fetchDeskWalkforwardCompute,
@@ -82,6 +83,7 @@ import type {
   DeskForwardRun,
   DeskForwardRunsListResult,
   DeskForwardTouch,
+  DeskGraduationResponse,
   DeskPlaybookAbsence,
   DeskPlaybookBackscanComputeSnapshot,
   DeskPlaybookBackscanOutcomeCounts,
@@ -389,7 +391,8 @@ type DeskCollapsibleSection =
   | "microReadiness"
   | "scoutLedger"
   | "walkForward"
-  | "validationVault";
+  | "validationVault"
+  | "graduation";
 // DESK-COLLAPSED-END
 
 const PRIMARY_BUTTON_CLASS =
@@ -6939,6 +6942,199 @@ function ValidationVaultSection({
   );
 }
 
+// goal-rapid-microscope-iter-31 (J-11): the era's own module-level copy of `micro_graduation.py`'s
+// `REFEREE_FUTURE_REVISION_SENTENCE` -- transcribed byte-for-byte (guarded below by
+// `test_desk_ui_guards.py`'s own copy-drift test). This is static UI copy tied to the SERVED
+// `referee_handoff_ready` stage token, never a second computation of a value the backend already
+// owns -- the same class as the Design Direction's own "Sealed — metadata only until exposure."
+// example: a fixed sentence keyed off a state string, not a value read off the response body,
+// because `GET /research/desk/micro/graduation` does not itself serve this sentence (it is only
+// ever composed inside a Referee-handoff bundle, a research artifact this iteration's Acceptance
+// text explicitly keeps off the surface -- "no second computation path, no new endpoint").
+// One unbroken literal (never `+`-concatenated across lines) so it is byte-identical, as a raw
+// SOURCE substring, to the backend's own joined `REFEREE_FUTURE_REVISION_SENTENCE` value -- what
+// the copy-drift guard test actually scans for.
+const GRADUATION_REFEREE_HANDOFF_NOTE =
+  "This referee_handoff_ready state does not imply the current Referee can register or adjudicate this candidate: a flow-context predicate requires a future named revision of docs/referee-statistical-spec.md. Where a candidate maps onto the existing referee vocabulary (setup, side, existing context predicates, existing measures), the bundle is registrable through the existing operator act unchanged.";
+
+// J-11: the Graduation section -- the funnel's terminal state, rendered directly BELOW Validation
+// Vault (T-11). Read-only: no compute/transition control, graduation transitions are not a UI act
+// (T-8). Renders `GET /research/desk/micro/graduation` verbatim: per family its `family_root_id`,
+// current stage token, complete `transitions` history, and complete `sealed_evaluations` history
+// (including permanent failed verdicts) -- no client-side aggregate, derived count, re-ordering, or
+// recomputation. Each row's full payload (heterogeneous by transition target state / evaluation
+// artifact shape) is ALSO disclosed via an opaque, verbatim JSON detail -- the `screen_result`/raw
+// `fold_results` precedent -- so nothing served is ever dropped, while the columns a reader needs
+// at a glance (state, verdict, n) render directly, guarded by `_PRICE_ARITHMETIC_FIELDS` below.
+function GraduationSection({
+  graduationResult,
+}: {
+  graduationResult: { ok: boolean; data: DeskGraduationResponse | null; error?: string } | null;
+}) {
+  if (graduationResult === null) {
+    return (
+      <div data-testid="graduation-section">
+        <LoadingPanel testid="graduation-loading" />
+      </div>
+    );
+  }
+  if (!graduationResult.ok || graduationResult.data === null) {
+    return (
+      <div data-testid="graduation-section">
+        <UnavailablePanel
+          testid="graduation-unavailable"
+          message={graduationResult.error ?? "The graduation ledger could not be loaded."}
+        />
+      </div>
+    );
+  }
+  const graduation = graduationResult.data;
+  return (
+    <div data-testid="graduation-section">
+      <p className="mb-3 text-xs text-slate-500">
+        Graduation (GET /research/desk/micro/graduation, read verbatim; read-only -- graduation
+        transitions are not a UI act): every candidate family&apos;s current stage
+        (exploratory / walkforward_survivor / sealed_survivor / referee_handoff_ready), its
+        complete transition history, and its complete sealed-evaluation history including any
+        permanent failed verdicts.
+      </p>
+
+      <p data-testid="graduation-chain-verification" className="mb-4 text-[11px] text-slate-500">
+        Ledger chain verification:{" "}
+        <span className="font-mono text-slate-300">
+          {graduation.chain_verification.ok
+            ? "ok"
+            : `failed at row ${graduation.chain_verification.failed_at_row} (${graduation.chain_verification.reason})`}
+        </span>
+      </p>
+
+      <div data-testid="graduation-families-block">
+        {graduation.families.length === 0 ? (
+          <EmptyState testid="graduation-families-empty" title={graduation.message ?? "No candidates ledgered."} />
+        ) : (
+          graduation.families.map((family) => (
+            <div
+              key={family.family_root_id}
+              data-testid={`graduation-family-${family.family_root_id}`}
+              className="mb-4"
+            >
+              <h4 className="mb-1 text-xs font-semibold text-slate-400">
+                {family.family_root_id}{" "}
+                <span className="font-normal text-slate-500">— {family.state}</span>
+              </h4>
+              {family.state === "referee_handoff_ready" && (
+                <p
+                  data-testid={`graduation-family-${family.family_root_id}-referee-note`}
+                  className="mb-2 text-[11px] text-slate-500"
+                >
+                  {GRADUATION_REFEREE_HANDOFF_NOTE}
+                </p>
+              )}
+
+              <div
+                data-testid={`graduation-family-${family.family_root_id}-transitions-block`}
+                className="mb-2"
+              >
+                <h5 className="mb-1 text-[11px] font-semibold text-slate-500">Transitions</h5>
+                {family.transitions.length === 0 ? (
+                  <EmptyState
+                    testid={`graduation-family-${family.family_root_id}-transitions-empty`}
+                    title="No transitions recorded."
+                  />
+                ) : (
+                  <div className="overflow-x-auto">
+                    <table className="w-full min-w-[640px] border-collapse text-xs">
+                      <thead>
+                        <tr className="border-b border-slate-800 text-left text-slate-500">
+                          <th className="px-1.5 py-1">From</th>
+                          <th className="px-1.5 py-1">To</th>
+                          <th className="px-1.5 py-1">Evaluated at</th>
+                          <th className="px-1.5 py-1">Detail</th>
+                        </tr>
+                      </thead>
+                      <tbody data-testid={`graduation-family-${family.family_root_id}-transition-rows`}>
+                        {family.transitions.map((transition, transitionIndex) => (
+                          <tr key={transitionIndex} className="border-b border-slate-900">
+                            <td className="px-1.5 py-1 text-slate-300">{transition.from_state}</td>
+                            <td className="px-1.5 py-1 text-slate-300">{transition.to_state}</td>
+                            <td className="whitespace-nowrap px-1.5 py-1 font-mono text-slate-400">
+                              {formatDateTimeET(transition.evaluated_at, { seconds: false })}
+                            </td>
+                            <td className="px-1.5 py-1">
+                              <details>
+                                <summary className="cursor-pointer text-slate-500">transition</summary>
+                                <pre className="mt-1 max-w-[420px] overflow-x-auto whitespace-pre-wrap break-all text-[10px] text-slate-500">
+                                  {JSON.stringify(transition, null, 2)}
+                                </pre>
+                              </details>
+                            </td>
+                          </tr>
+                        ))}
+                      </tbody>
+                    </table>
+                  </div>
+                )}
+              </div>
+
+              <div
+                data-testid={`graduation-family-${family.family_root_id}-sealed-evaluations-block`}
+              >
+                <h5 className="mb-1 text-[11px] font-semibold text-slate-500">Sealed evaluations</h5>
+                {family.sealed_evaluations.length === 0 ? (
+                  <EmptyState
+                    testid={`graduation-family-${family.family_root_id}-sealed-evaluations-empty`}
+                    title="No sealed evaluations recorded."
+                  />
+                ) : (
+                  <div className="overflow-x-auto">
+                    <table className="w-full min-w-[640px] border-collapse text-xs">
+                      <thead>
+                        <tr className="border-b border-slate-800 text-left text-slate-500">
+                          <th className="px-1.5 py-1">Dataset</th>
+                          <th className="px-1.5 py-1">Verdict</th>
+                          <th className="px-1.5 py-1 text-right">n</th>
+                          <th className="px-1.5 py-1">Evaluated at</th>
+                          <th className="px-1.5 py-1">Detail</th>
+                        </tr>
+                      </thead>
+                      <tbody
+                        data-testid={`graduation-family-${family.family_root_id}-sealed-evaluation-rows`}
+                      >
+                        {family.sealed_evaluations.map((evaluation, evaluationIndex) => (
+                          <tr key={evaluationIndex} className="border-b border-slate-900">
+                            <td className="whitespace-nowrap px-1.5 py-1 font-mono text-[10px] text-slate-500">
+                              {evaluation.dataset_id}
+                            </td>
+                            <td className="px-1.5 py-1 text-slate-300">{evaluation.verdict}</td>
+                            <td className="px-1.5 py-1 text-right font-mono text-slate-300">
+                              {evaluation.n}
+                            </td>
+                            <td className="whitespace-nowrap px-1.5 py-1 font-mono text-slate-400">
+                              {formatDateTimeET(evaluation.evaluated_at, { seconds: false })}
+                            </td>
+                            <td className="px-1.5 py-1">
+                              <details>
+                                <summary className="cursor-pointer text-slate-500">sealed_evaluation</summary>
+                                <pre className="mt-1 max-w-[420px] overflow-x-auto whitespace-pre-wrap break-all text-[10px] text-slate-500">
+                                  {JSON.stringify(evaluation, null, 2)}
+                                </pre>
+                              </details>
+                            </td>
+                          </tr>
+                        ))}
+                      </tbody>
+                    </table>
+                  </div>
+                )}
+              </div>
+            </div>
+          ))
+        )}
+      </div>
+    </div>
+  );
+}
+
 // era-desk-iter-14 (J-10): a third compute control, wired exactly like `TopupComputeControl` — the
 // operation has no per-pair counters (it is a single classify-repair-verify walk, not a walk over
 // many pairs), so the running indicator shows the compute's own `progress.phase` label instead of
@@ -9832,6 +10028,14 @@ export default function DeskPage() {
     error?: string;
   } | null>(null);
 
+  // J-11: the Graduation section's own fetch-on-expand result -- the SAME `null` (not yet
+  // fetched) / `{ok, data, error}` shape every other Rapid Microscope section already uses.
+  const [graduationResult, setGraduationResult] = useState<{
+    ok: boolean;
+    data: DeskGraduationResponse | null;
+    error?: string;
+  } | null>(null);
+
   // iter-14 audit (finding F1): the ONE stop flag both plain-async compute polls below observe.
   // This page's own contract for a plain `for(;;)` driver that awaits `refreshChainSleep` is the
   // `refreshChainStopRef` pattern further down ("Unmounting (a nav away mid-chain) stops the driver
@@ -9917,6 +10121,10 @@ export default function DeskPage() {
       // /research/datasets, never a re-read of microReadinessResult to enrich or cross-reference a
       // shard/universe row. This is that one fetch.
       fetchDeskVault().then(setVaultResult);
+    } else if (section === "graduation") {
+      // J-11: the Graduation section's own ONE fetch -- read-only, no compute/transition control
+      // (graduation transitions are not a UI act, T-8).
+      fetchDeskGraduation().then(setGraduationResult);
     }
   }
 
@@ -12216,6 +12424,20 @@ export default function DeskPage() {
             <ValidationVaultSection vaultResult={vaultResult} />
           </CollapsibleSection>
         </section>
+
+        {/* goal-rapid-microscope-iter-31 (J-11): the Graduation section -- the funnel's terminal
+            state, rendered directly BELOW Validation Vault (T-11). READ-ONLY: no compute/
+            transition control (transitions are not a UI act, T-8). */}
+        <section aria-label="Graduation" className="mt-6">
+          <CollapsibleSection
+            id="graduation"
+            title="Graduation"
+            open={expandedSections.has("graduation")}
+            onToggle={() => toggleSection("graduation")}
+          >
+            <GraduationSection graduationResult={graduationResult} />
+          </CollapsibleSection>
+        </section>
       </main>
     </div>
   );
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index a132760b..d846b271 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -21,6 +21,7 @@ import type {
   DeskForwardPinsResult,
   DeskForwardReadResult,
   DeskForwardRunsListResult,
+  DeskGraduationResponse,
   DeskPlaybookBackscanComputeSnapshot,
   DeskPlaybookBackscanPlan,
   DeskPlaybookBackscanRunsListResult,
@@ -2704,3 +2705,31 @@ export async function fetchDeskVault(): Promise<{
     return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
   }
 }
+
+// GET /research/desk/micro/graduation — J-11, READ-ONLY: graduation transitions are not a UI
+// act (T-8), so this is the section's ONLY fetch. Every family's current stage token, complete
+// transition history, and complete sealed-evaluation history (including permanent failed
+// verdicts), beside the ledger's own chain-verification verdict. Never 404/500 on an empty
+// ledger — the honest `message` field covers that case.
+export async function fetchDeskGraduation(): Promise<{
+  ok: boolean;
+  data: DeskGraduationResponse | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/micro/graduation`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskGraduationResponse };
+    }
+    let error = "The graduation ledger could not be loaded.";
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
index a78a57d5..e06330f6 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -2852,3 +2852,40 @@ export interface DeskVaultResponse {
   shard_ledger_chain_verification: MicroChainVerification;
   universe_ledger_chain_verification: MicroChainVerification;
 }
+
+// --- Graduation -- GET /research/desk/micro/graduation (micro_graduation.py
+// `list_graduation_families`), J-11: the funnel's terminal state, read verbatim for the first
+// time -- zero UI readers before this iteration. A family's own `transitions`/`sealed_evaluations`
+// rows vary in shape by transition target state / evaluation artifact (the `WalkForwardFoldSpec`
+// precedent above): each carries the few fields this page destructures directly, plus an index
+// signature for everything else, rendered as an opaque, verbatim JSON detail (never enumerated
+// field-by-field -- the `screen_result`/raw `fold_results` precedent).
+export interface GraduationTransitionRow {
+  from_state: string;
+  to_state: string;
+  evaluated_at: string;
+  [key: string]: unknown;
+}
+
+export interface GraduationSealedEvaluationRow {
+  dataset_id: string;
+  verdict: string;
+  n: number;
+  evaluated_at: string;
+  [key: string]: unknown;
+}
+
+export interface GraduationFamily {
+  family_root_id: string;
+  state: string;
+  transitions: GraduationTransitionRow[];
+  sealed_evaluations: GraduationSealedEvaluationRow[];
+}
+
+export interface DeskGraduationResponse {
+  families: GraduationFamily[];
+  // Set to the ledger's own `EMPTY_LEDGER_MESSAGE` ("No candidates ledgered.") when `families` is
+  // empty, `null` otherwise -- rendered verbatim, never a hardcoded fallback string.
+  message: string | null;
+  chain_verification: MicroChainVerification;
+}
```
