# Iteration diff (bounded)

Files changed: 9. Shown in full: 9.

```diff
diff --git a/apps/backend/app/mcp/__init__.py b/apps/backend/app/mcp/__init__.py
index 5a132cf..7c6a7e8 100644
--- a/apps/backend/app/mcp/__init__.py
+++ b/apps/backend/app/mcp/__init__.py
@@ -18,9 +18,9 @@ Result contract (locked by ``tests/test_mcp_server.py``):
     (era-3) J-02, ``backtests`` at J-03, ``pnl_ledger`` at J-04; ``/research/profiles`` — reached
     via ``get_endpoint`` — at J-05; ``bars`` at era-4 J-01; ``levels`` at era-4 J-02; ``strategies``
     at era-4 J-04; ``tradability`` at era-5B J-01; ``setups`` at era-5B J-02; ``edge_report`` at
-    era-5B J-04; ``desk_universe``/``desk_screen`` at era-desk J-06); an allowlisted-but-UNKNOWN
-    path (any unshipped ``/research/*``) still surfaces the backend's honest 404 this way — never
-    placeholder data.
+    era-5B J-04; ``desk_universe``/``desk_screen`` at era-desk J-06; ``desk_playbook``/
+    ``desk_playbook_evidence`` at Era B2 J-09); an allowlisted-but-UNKNOWN path (any unshipped
+    ``/research/*``) still surfaces the backend's honest 404 this way — never placeholder data.
   * backend unreachable — an explicit tool error naming the base URL and the failure
     (``BackendUnreachableError``); NEVER cached or fabricated data (no cache, no retry loop,
     no offline snapshot exists anywhere in this module).
@@ -115,6 +115,18 @@ _STATIC_PATHS: dict[str, str] = {
     # (honest-empty 200 before any compute). The `?screen_id=` per-screen variant stays reachable
     # only through `get_endpoint`, exactly like `desk_screen`'s own `?date=`.
     "desk_forward": "/research/desk/forward",
+    # `desk_playbook` (Era B2 "The Playbook" J-09) is the IDENTICAL no-required-param shape as
+    # `desk_forward` directly above: the append-only playbook-signal ledger's own base read serves
+    # a meta-only list + the newest full record (honest-empty 200 before any compute). The
+    # `?date=`/`?id=` parameterized reads stay reachable only through `get_endpoint`, exactly like
+    # `desk_screen`'s own `?date=`.
+    "desk_playbook": "/research/desk/playbook",
+    # `desk_playbook_evidence` (Era B2 J-09) is the IDENTICAL no-required-param shape: the
+    # distribution fold over every recorded playbook signal at the CURRENT default signature takes
+    # no query params for its base read (an always-populated full setup x side x measure
+    # cross-product cell shape, honest `n: 0` before any playbook has ever been recorded -- never a
+    # 404). The `?signature=` inspect-mode variant stays reachable only through `get_endpoint`.
+    "desk_playbook_evidence": "/research/desk/playbook/evidence",
 }
 
 _TAPE_PATHS: dict[str, str] = {
@@ -328,6 +340,36 @@ TOOLS: tuple[types.Tool, ...] = (
         ),
         inputSchema=_object_schema({}),
     ),
+    types.Tool(
+        name="desk_playbook",
+        description=(
+            "Read-only proxy of GET /research/desk/playbook -- Era B2 \"The Playbook\"'s "
+            "append-only signal ledger: for a recorded trading session, every detected book-setup "
+            "signal (symbol, setup_id, side, trigger price/time, invalidation_price, geometry, "
+            "volume character, market context, principles) plus its trigger-anchored forward "
+            "measurement (the desk forward rail's own horizons/dual-MDD/seed conventions, imported "
+            "verbatim) and invalidation_breached disclosure, beside a seeded baseline and the "
+            "record's own descriptive register (a meta-only list of every record plus the newest "
+            "full one -- `latest`, `null` before any compute, an explicit honest-empty 200, never a "
+            "404), JSON verbatim. Takes no arguments here; `get_endpoint` reaches the `?date=`/"
+            "`?id=` per-record variants."
+        ),
+        inputSchema=_object_schema({}),
+    ),
+    types.Tool(
+        name="desk_playbook_evidence",
+        description=(
+            "Read-only proxy of GET /research/desk/playbook/evidence -- Era B2's distribution "
+            "view: every recorded playbook signal at the CURRENT default input signature, folded "
+            "into per (setup, side, measure) forward-return/MDD distribution cells (median/"
+            "quartiles/mean, n, n_truncated, below_min_n) beside the pooled seeded baseline and "
+            "invalidation-breach counts -- the FULL declared setup x side x measure cross product "
+            "is always served (a combination with zero recorded signals reads n: 0, never omitted); "
+            "other recorded signatures are listed, never pooled, JSON verbatim. Takes no arguments "
+            "here; `get_endpoint` reaches the `?signature=` inspect variant."
+        ),
+        inputSchema=_object_schema({}),
+    ),
     types.Tool(
         name="pnl_ledger",
         description=(
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index c6b0233..2b1ce10 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -40,6 +40,7 @@ from app.mcp import (
 from app.providers.adapters.base import RawBar
 from app.research.bars import BarSeriesAlreadyRegistered, BarStore
 from app.research.desk_forward import FORWARD_REGISTER, ForwardStore, forward_parameters
+from app.research.desk_playbook import PLAYBOOK_REGISTER, PlaybookStore, playbook_parameters
 from app.research.desk_screen import ScreenStore
 from app.research.desk_universe import UniverseStore
 
@@ -48,9 +49,10 @@ BACKEND_DIR = Path(__file__).resolve().parents[1]
 # Capability 6, verbatim — order and content are the advertised contract. ``bars`` (era-4 J-01),
 # ``levels`` (era-4 J-02), ``strategies`` (era-4 J-04), ``tradability`` (era-5B J-01), ``setups``
 # (era-5B J-02), ``desk_universe``/``desk_screen`` (era-desk J-06, MCP contract v3 -- 15 -> 17
-# tools), and ``desk_forward`` (forward-test era, MCP contract v4 -- 17 -> 18 tools) are the
-# newest additions, each positioned right after its dependency-order sibling (the same
-# store/registry+route+MCP shape, mirrored end to end).
+# tools), ``desk_forward`` (forward-test era, 17 -> 18 tools), and ``desk_playbook``/
+# ``desk_playbook_evidence`` (Era B2 "The Playbook" J-09, the era's own MCP contract v4 -- 18 -> 20
+# tools) are the newest additions, each positioned right after its dependency-order sibling (the
+# same store/registry+route+MCP shape, mirrored end to end).
 EXPECTED_TOOLS = (
     "tape_state",
     "tape_features",
@@ -66,6 +68,8 @@ EXPECTED_TOOLS = (
     "desk_universe",
     "desk_screen",
     "desk_forward",
+    "desk_playbook",
+    "desk_playbook_evidence",
     "pnl_ledger",
     "taxonomy",
     "ui_route_map",
@@ -118,6 +122,7 @@ def backend_paths(tmp_path_factory):
         "TAPEOLOGY_DESK_UNIVERSE_DIR": str(tmp_path_factory.mktemp("mcp-desk-universe")),
         "TAPEOLOGY_DESK_SCREEN_DIR": str(tmp_path_factory.mktemp("mcp-desk-screen")),
         "TAPEOLOGY_DESK_FORWARD_DIR": str(tmp_path_factory.mktemp("mcp-desk-forward")),
+        "TAPEOLOGY_DESK_PLAYBOOK_DIR": str(tmp_path_factory.mktemp("mcp-desk-playbook")),
     }
 
 
@@ -577,6 +582,169 @@ async def test_desk_forward_tool_byte_identical_on_a_populated_state(mcp_env, ba
     assert proxied.content[0].text.encode("utf-8") == rest2.content, "desk forward screen_id-query not byte-identical"
 
 
+# --- Era B2 "The Playbook" J-09: desk_playbook / desk_playbook_evidence (MCP contract v4, 18 -> 20
+# tools; empty + populated + ?date=/?signature= proxy) --------------------------------------------
+#
+# Both stores are rooted at their OWN env-scoped temp dirs (``backend_paths`` above) that nothing
+# else in this module ever touches, so the honest-empty states below are genuinely observed BEFORE
+# any playbook record is ever seeded -- file order matters here, same as every other store in this
+# module. The evidence tool folds over the SAME playbook store, so its own honest-empty test runs
+# FIRST too (before either desk_playbook test below writes anything), and its own populated-state
+# test runs LAST (after both desk_playbook tests have already recorded arbitrary-signature files) --
+# those records can never match the REAL current default signature this module never computes via
+# `compute_playbook` (no real bar-backed session is walked here), so they surface honestly under
+# `other_signatures`, never pooled into `cells` (the T-7 "one signature" discipline, proven exactly
+# as `test_desk_playbook_evidence.py`'s own TC-5 proves it -- this module only proves the MCP proxy
+# is byte-identical to the REST body, not the fold's own pooling math).
+
+DESK_PLAYBOOK_DATE = "2026-06-22"
+DESK_PLAYBOOK_ISOLATED_DATE = "2026-06-24"
+DESK_PLAYBOOK_NONMATCH_DATE = "2020-01-01"
+
+
+@pytest.mark.anyio
+async def test_desk_playbook_tool_byte_identical_on_the_honest_empty_state(mcp_env):
+    """Before any playbook has ever been computed, ``desk_playbook`` proxies
+    ``GET /research/desk/playbook``'s explicit HTTP 200 honest-empty payload -- never a 404 (the
+    ``desk_forward`` convention ``desk_playbook.py`` itself follows)."""
+    result = await call_tool("desk_playbook", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/playbook", timeout=5.0)
+    assert rest.status_code == 200
+    assert rest.json() == {"playbooks": [], "latest": None, "integrity_errors": []}
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_playbook not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_desk_playbook_evidence_tool_byte_identical_on_the_honest_empty_state(mcp_env):
+    """TC-4: before any playbook record has ever been recorded (this test runs BEFORE either
+    ``desk_playbook`` populated-state test below writes anything into the shared env-scoped
+    playbook dir), ``desk_playbook_evidence`` proxies ``GET /research/desk/playbook/evidence``'s
+    honest-empty fold -- the FULL declared setup x side x measure cross product still served, every
+    cell reading ``n: 0`` (never omitted, never a 404) -- byte-identical to curl."""
+    result = await call_tool("desk_playbook_evidence", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/playbook/evidence", timeout=5.0)
+    assert rest.status_code == 200
+    payload = rest.json()
+    assert set(payload) == {
+        "signature", "cells", "invalidation_breached", "other_signatures", "parameters", "register",
+    }
+    assert payload["other_signatures"] == []
+    assert payload["cells"], "the declared cross product must be non-empty even with no records"
+    assert all(cell["signal"]["n"] == 0 for cell in payload["cells"]), "no record yet -- every cell must read n: 0"
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_playbook_evidence not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_desk_playbook_tool_byte_identical_on_a_populated_state(mcp_env, backend_paths):
+    """The ``desk_forward`` populated-state precedent, applied to the playbook store: seed ONE real
+    record directly through ``PlaybookStore.record()`` -- the exact persistence call
+    ``compute_playbook`` itself makes -- into the live backend's env-scoped
+    ``TAPEOLOGY_DESK_PLAYBOOK_DIR``, carrying an actual signal, then prove the tool's JSON is
+    byte-identical to its curl equivalent on a NON-EMPTY result."""
+    playbook_dir = Path(backend_paths["TAPEOLOGY_DESK_PLAYBOOK_DIR"])
+    PlaybookStore(playbook_dir).record(
+        session_date=DESK_PLAYBOOK_DATE,
+        config_fingerprint=CONFIG.config_fingerprint(),
+        playbook_input_signature="mcp-test-playbook-signature",
+        payload_version=1,
+        parameters=playbook_parameters(),
+        register=PLAYBOOK_REGISTER,
+        signals=[
+            {
+                "symbol": "AAPL",
+                "setup_id": "open_high_break",
+                "side": "long",
+                "trigger": {"price": 300.5, "at_utc": "2026-06-22T13:45:00Z"},
+                "invalidation_price": 299.8,
+            }
+        ],
+        absences=[],
+        diagnostics=[],
+    )
+    result = await call_tool("desk_playbook", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/playbook", timeout=5.0)
+    assert rest.status_code == 200
+    body = rest.json()
+    assert len(body["playbooks"]) >= 1, "the live list must be non-empty for this proof"
+    assert body["latest"] is not None
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_playbook not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_get_endpoint_desk_playbook_date_query_proxies_verbatim(mcp_env, backend_paths):
+    """TC-6: ``get_endpoint`` reaches the ``?date=`` lookup variant ``desk_playbook`` itself does
+    not expose -- byte-identical for a matching date (seeded HERE, under its own distinct date --
+    the ``desk_screen``/``desk_forward`` isolated-date precedent, so this test passes standalone),
+    and the honest ``{"playbook": null, "versions": 0}`` 200 for a non-matching one."""
+    playbook_dir = Path(backend_paths["TAPEOLOGY_DESK_PLAYBOOK_DIR"])
+    PlaybookStore(playbook_dir).record(
+        session_date=DESK_PLAYBOOK_ISOLATED_DATE,
+        config_fingerprint=CONFIG.config_fingerprint(),
+        playbook_input_signature="mcp-test-playbook-isolated-signature",
+        payload_version=1,
+        parameters=playbook_parameters(),
+        register=PLAYBOOK_REGISTER,
+        signals=[
+            {
+                "symbol": "MSFT",
+                "setup_id": "jump_base_explosion",
+                "side": "long",
+                "trigger": {"price": 410.0, "at_utc": "2026-06-24T14:00:00Z"},
+                "invalidation_price": 405.0,
+            }
+        ],
+        absences=[],
+        diagnostics=[],
+    )
+
+    matching_path = f"/research/desk/playbook?date={DESK_PLAYBOOK_ISOLATED_DATE}"
+    result = await call_tool("get_endpoint", {"path": matching_path})
+    rest = httpx.get(f"{mcp_env}{matching_path}", timeout=5.0)
+    assert rest.status_code == 200
+    assert rest.json()["playbook"] is not None
+    assert rest.json()["versions"] == 1
+    assert result.isError is False
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk playbook date-match not byte-identical"
+
+    nonmatch_path = f"/research/desk/playbook?date={DESK_PLAYBOOK_NONMATCH_DATE}"
+    result = await call_tool("get_endpoint", {"path": nonmatch_path})
+    rest = httpx.get(f"{mcp_env}{nonmatch_path}", timeout=5.0)
+    assert rest.status_code == 200
+    assert rest.json() == {"playbook": None, "versions": 0}
+    assert result.isError is False
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk playbook date-nonmatch not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_desk_playbook_evidence_tool_byte_identical_on_a_populated_state(mcp_env):
+    """TC-5: after the two ``desk_playbook`` tests above have recorded two arbitrary-signature
+    files, ``desk_playbook_evidence`` still proxies byte-identical -- and now honestly lists both
+    recorded signatures under ``other_signatures`` (never pooled into ``cells``, since neither
+    arbitrary test signature can ever equal the REAL current default signature this module never
+    computes via ``compute_playbook``), proving the ``signature``/``cells``/``register`` fields the
+    acceptance names are all proxied verbatim."""
+    result = await call_tool("desk_playbook_evidence", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/playbook/evidence", timeout=5.0)
+    assert rest.status_code == 200
+    payload = rest.json()
+    assert set(payload) == {
+        "signature", "cells", "invalidation_breached", "other_signatures", "parameters", "register",
+    }
+    assert len(payload["other_signatures"]) >= 2, "both arbitrary-signature records must surface here"
+    assert all(cell["signal"]["n"] == 0 for cell in payload["cells"]), (
+        "arbitrary-signature records must never pool into cells"
+    )
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_playbook_evidence not byte-identical"
+
+
 @pytest.mark.anyio
 async def test_desk_screen_reference_close_field_proxies_verbatim(mcp_env, backend_paths):
     """goal-desk-iter-17 (J-13) TC-10: `reference_close` -- `desk_screen.py`'s new ranked-row field
@@ -1192,7 +1360,7 @@ async def test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool(mcp_
     assert len(result.content) == 1
     assert result.content[0].text.encode("utf-8") == rest.content, "topup/runs not byte-identical"
     assert rest.json() == {"runs": [], "latest": None, "integrity_errors": []}
-    assert "desk_topup_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 18
+    assert "desk_topup_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 20
 
 
 @pytest.mark.anyio
@@ -1211,7 +1379,7 @@ async def test_get_endpoint_desk_screen_runs_byte_identical_with_no_new_tool(mcp
     assert len(result.content) == 1
     assert result.content[0].text.encode("utf-8") == rest.content, "screen/runs not byte-identical"
     assert rest.json() == {"runs": [], "latest": None, "integrity_errors": []}
-    assert "desk_screen_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 18
+    assert "desk_screen_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 20
 
 
 @pytest.mark.anyio
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index eb31c98..da793db 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -3923,6 +3923,9 @@ function PlaybookEvidenceSection({
   const hasAnySignal = data.cells.some((cell) => cell.signal.n > 0);
   return (
     <div data-testid="desk-evidence-section">
+      <p className="mb-1 text-xs text-slate-400" data-testid="desk-evidence-signature">
+        Built from signature: <span className="font-mono text-slate-300">{data.signature}</span>
+      </p>
       <p className="mb-3 text-xs text-slate-500">{data.register}</p>
       {hasAnySignal ? (
         <PlaybookEvidenceCellsTable cells={data.cells} />
diff --git a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
index 392112c..98d3315 100755
--- a/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
+++ b/incredible_auto_dev/scripts/automation/browser-qa-phase.sh
@@ -480,9 +480,15 @@ fi
 # before the lanes ran. CLEAN writes the disclosure artifact a later reader can
 # cite instead of prose; a BREACH additionally lands a loud section IN the
 # authoritative results file, because that is the one artifact the evaluator and
-# the achievement gate are guaranteed to read. Deliberately NOT an exit: the
-# run's verdicts still have to be published and read — a silent pipeline abort
-# would hide the very thing this section exists to disclose.
+# the achievement gate are guaranteed to read — THEN aborts this script (goal-
+# playbook-iter-9 T-1: "a safe launcher nothing is obliged to use is not a
+# mechanism, only a gate is" — a BREACH means an automated lane already wrote
+# into the operator's real store, so this run's verdicts are not trustworthy
+# and must not be silently accepted as a normal pass/fail cycle). The
+# disclosure is written and published FIRST, so the abort never hides it; the
+# non-zero exit itself is what makes the calling chain (run-phase.sh's
+# `|| { ...; return $rc; }` branch, or the sequential branch's own warning +
+# continue) treat this as a failed step rather than a quiet success.
 if ! store_scope_verify "$STORE_SCOPE_MANIFEST" "$STORE_SCOPE_REPORT"; then
   echo "[browser-qa] STORE-SCOPE BREACH — a browser lane wrote into a protected store path this run. See $STORE_SCOPE_REPORT." >&2
   if [[ -f "$UI_TEST_RESULTS" ]]; then
@@ -500,6 +506,9 @@ if ! store_scope_verify "$STORE_SCOPE_MANIFEST" "$STORE_SCOPE_REPORT"; then
     record_telemetry_event "store_scope_breach" "$(jq -cn --arg n "$PHASE" --arg r "reports/qa/${PHASE}-store-scope-guard.md" \
         '{iter_name:$n, disclosure:$r}' 2>/dev/null || printf '{"iter_name":"%s"}' "$PHASE")"
   fi
+  rm -f "$STORE_SCOPE_MANIFEST" 2>/dev/null || true
+  echo "[browser-qa] ABORTING browser-qa-phase.sh: a store-scope breach makes this run's browser-qa verdicts untrustworthy. Investigate $STORE_SCOPE_REPORT before re-running." >&2
+  exit 1
 fi
 rm -f "$STORE_SCOPE_MANIFEST" 2>/dev/null || true
 
diff --git a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
index df0aba9..241c1d8 100755
--- a/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
+++ b/incredible_auto_dev/scripts/automation/goal-iter-lean.sh
@@ -914,8 +914,20 @@ replay_lane_golden_coverage "$UI_TEST_RESULTS" "$ITER_NAME"
 # store paths and compare against the pre-lane baseline. CLEAN writes the
 # disclosure artifact a later reader cites instead of prose; a BREACH also lands
 # a loud section in the authoritative results file — the one artifact the
-# evaluator and the achievement gate always read. Never an exit: the verdicts
-# still have to be published, and a silent abort would hide the disclosure.
+# evaluator and the achievement gate always read — THEN aborts this script
+# (goal-playbook-iter-9 T-1: "a safe launcher nothing is obliged to use is not
+# a mechanism, only a gate is" — a BREACH means an automated lane already wrote
+# into the operator's real store, so this run's verdicts are not trustworthy).
+# The disclosure is written and published FIRST, so the abort never hides it.
+# Deliberately does NOT reach the checkpoint block below (step_mark_done
+# browser-qa): the browser-qa lane must NOT be recorded done on a breached run,
+# so a later resume of this iteration genuinely re-runs it rather than reusing
+# a checkpoint stamped over an untrustworthy result. run-goal.sh does not
+# special-case this script's non-zero exit beyond the DISPATCH_UNAVAILABLE_EXIT_CODE
+# (70) check right after the dispatch, so the outer loop falls through to the
+# coherence-auditor/evaluator as usual — they read the merged results file
+# (which now carries the loud disclosure section) and score accordingly,
+# exactly like any other unmarked/incomplete step.
 if ! store_scope_verify "${STORE_SCOPE_MANIFEST:-}" "$REPO_ROOT/reports/qa/${ITER_NAME}-store-scope-guard.md"; then
   echo "[goal-iter-lean] STORE-SCOPE BREACH — a browser lane wrote into a protected store path this run. See reports/qa/${ITER_NAME}-store-scope-guard.md" >&2
   if [[ -f "$UI_TEST_RESULTS" ]]; then
@@ -930,6 +942,9 @@ if ! store_scope_verify "${STORE_SCOPE_MANIFEST:-}" "$REPO_ROOT/reports/qa/${ITE
     } >> "$UI_TEST_RESULTS" 2>/dev/null || true
   fi
   record_telemetry_event "store_scope_breach" "$(jq -cn --arg n "$ITER_NAME" --arg r "reports/qa/${ITER_NAME}-store-scope-guard.md" '{iter_name:$n, disclosure:$r}' 2>/dev/null || printf '{"iter_name":"%s"}' "$ITER_NAME")"
+  rm -f "${STORE_SCOPE_MANIFEST:-/nonexistent}" 2>/dev/null || true
+  echo "[goal-iter-lean] ABORTING goal-iter-lean.sh: a store-scope breach makes this run's browser-qa verdicts untrustworthy. Investigate reports/qa/${ITER_NAME}-store-scope-guard.md before re-running." >&2
+  exit 1
 fi
 rm -f "${STORE_SCOPE_MANIFEST:-/nonexistent}" 2>/dev/null || true
 
diff --git a/incredible_auto_dev/scripts/automation/qa-phase.sh b/incredible_auto_dev/scripts/automation/qa-phase.sh
index 1e2b9a3..35cd5ff 100755
--- a/incredible_auto_dev/scripts/automation/qa-phase.sh
+++ b/incredible_auto_dev/scripts/automation/qa-phase.sh
@@ -14,6 +14,13 @@ source "$SCRIPT_DIR/lib/common.sh"
 # Telemetry (no-op unless GOAL_SESSION_DIR is set, i.e. goal-mode full depth):
 # needed so the missing-evidence tripwire below can record its event.
 source "$SCRIPT_DIR/lib/telemetry.sh"
+# store_scope_require (no-op without project-extensions/store-scope/store-scope.env)
+# -- goal-playbook-iter-8 audit finding B3: this agent's own Chrome MCP browser
+# pass was the THIRD lane the guard did not cover (browser-qa-phase.sh's replay
+# + LLM lanes were the other two, gated at goal-playbook-iter-8). Only the
+# store_scope_require wrapper is used below; the rest of this file (demo/replay
+# lane machinery) does not apply to the qa agent's own dispatch.
+source "$SCRIPT_DIR/lib/replay-lane.sh"
 
 PHASE="${1:-}"
 require_phase_arg "$PHASE"
@@ -137,6 +144,21 @@ if [[ -f "$SCRIPT_DIR/host-guard/browser-confine.sh" ]]; then
   HOST_GUARD_ROOT="$REPO_ROOT" bash "$SCRIPT_DIR/host-guard/browser-confine.sh" || true
 fi
 
+# ── Store-scope gate (project-declared; automation/store-scope/) ─────────────
+# BEFORE the agent is told a browser check is required: prove the backend under
+# test is the project's scoped QA backend. A project without
+# project-extensions/store-scope/store-scope.env is unaffected (store_scope_require
+# no-ops). A refusal downgrades FRONTEND_PRESENT honestly (the non-browser QA
+# checks below still run) rather than blocking the whole qa-phase.sh dispatch --
+# the same REL-14-style graceful-skip shape browser-qa-phase.sh uses for its own
+# refusals.
+QA_STORE_SCOPE_SKIP_REASON=""
+if [[ "$FRONTEND_PRESENT" == "yes" ]] && ! store_scope_require; then
+  FRONTEND_PRESENT="no"
+  QA_STORE_SCOPE_SKIP_REASON="backend under test is not the project's scoped QA backend -- browser checks refused (store-scope guard)"
+  echo "[qa-phase] STORE-SCOPE REFUSAL: the backend serving $FRONTEND_URL is not the project's scoped QA backend -- Chrome MCP browser checks will be SKIPPED this run (non-browser QA checks still run)." >&2
+fi
+
 # ── Run QA agent ──────────────────────────────────────────────────────────
 cd "$REPO_ROOT"
 record_agent_invocation_start qa
@@ -158,6 +180,8 @@ Agent instructions: .claude/agents/qa.md  <-- read this first, follow MODE 2 ins
 Frontend Present for this phase: $FRONTEND_PRESENT
 $(if [[ "$FRONTEND_PRESENT" == "yes" ]]; then
   echo "Chrome MCP browser checks ARE required. The frontend should be accessible at $FRONTEND_URL."
+elif [[ -n "$QA_STORE_SCOPE_SKIP_REASON" ]]; then
+  echo "Frontend IS present, but browser checks are SKIPPED this run: $QA_STORE_SCOPE_SKIP_REASON. Do NOT open a browser. Mark every browser-dependent test case SKIPPED with this reason."
 else
   echo "No frontend in this phase -- skip browser checks entirely."
 fi)
diff --git a/incredible_auto_dev/tests/automation/test-store-scope-guard.sh b/incredible_auto_dev/tests/automation/test-store-scope-guard.sh
index 97c531e..ca12b93 100755
--- a/incredible_auto_dev/tests/automation/test-store-scope-guard.sh
+++ b/incredible_auto_dev/tests/automation/test-store-scope-guard.sh
@@ -168,6 +168,109 @@ rc=0; run_wrapper 'store_scope_require' || rc=$?
 [[ "$rc" == "0" ]] && assert "wrappers no-op when the guard script is absent" pass || assert "wrappers no-op when the guard script is absent (rc=$rc)" fail
 mv "$WORK/store-scope-away" "$SBX/scripts/automation/store-scope"
 
+echo "== 9. goal-playbook-iter-9: a verify BREACH aborts the calling lane, not just discloses =="
+# Structural (source-scan), not functional: standing up the full callers
+# (browser-qa-phase.sh dispatches claude, goal-iter-lean.sh runs the whole lean
+# pipeline) would need a mock Claude CLI + backend/frontend, which no test in
+# this suite does for these two orchestration scripts. This proves the SHAPE
+# the iter-9 hardening requires: both call sites now `exit` non-zero inside
+# their own `store_scope_verify` failure branch (previously they fell through
+# to `rm -f ...manifest` and continued unconditionally), and in
+# goal-iter-lean.sh that exit appears BEFORE the `step_mark_done browser-qa`
+# checkpoint call in file order, so a breached run can never be checkpointed
+# done.
+BQA_PHASE="$ENGINE_ROOT/scripts/automation/browser-qa-phase.sh"
+LEAN_ITER="$ENGINE_ROOT/scripts/automation/goal-iter-lean.sh"
+
+# Each caller's abort line sits right after its own distinctive "ABORTING
+# <script>.sh:" log line -- grep -A2 catches it regardless of indentation,
+# without needing a fragile block-boundary extraction (the natural end-of-block
+# marker, `rm -f "..MANIFEST" ... || true`, also appears once BEFORE the abort,
+# inside the same branch, so a start/end awk scan finds that occurrence first
+# and never reaches the exit line).
+grep -A2 'ABORTING browser-qa-phase.sh:' "$BQA_PHASE" | grep -qE '^[[:space:]]*exit 1[[:space:]]*$' \
+  && assert "browser-qa-phase.sh: verify-BREACH branch exits 1" pass \
+  || assert "browser-qa-phase.sh: verify-BREACH branch exits 1" fail
+
+grep -A2 'ABORTING goal-iter-lean.sh:' "$LEAN_ITER" | grep -qE '^[[:space:]]*exit 1[[:space:]]*$' \
+  && assert "goal-iter-lean.sh: verify-BREACH branch exits 1" pass \
+  || assert "goal-iter-lean.sh: verify-BREACH branch exits 1" fail
+
+_lean_exit_line="$(grep -n 'ABORTING goal-iter-lean.sh:' "$LEAN_ITER" | head -1 | cut -d: -f1)"
+_lean_checkpoint_line="$(grep -n 'step_mark_done browser-qa --dir' "$LEAN_ITER" | tail -1 | cut -d: -f1)"
+[[ -n "$_lean_exit_line" && -n "$_lean_checkpoint_line" && "$_lean_exit_line" -lt "$_lean_checkpoint_line" ]] \
+  && assert "goal-iter-lean.sh: the breach abort precedes the browser-qa checkpoint" pass \
+  || assert "goal-iter-lean.sh: the breach abort precedes the browser-qa checkpoint" fail
+
+echo "== 10. goal-playbook-iter-9: qa-phase.sh's own browser pass is gated (audit B3) =="
+# goal-playbook-iter-8 audit finding B3: browser-qa-phase.sh's replay + LLM
+# lanes were gated at iter-8, but the plain `qa` agent's OWN Chrome MCP pass
+# (dispatched from qa-phase.sh whenever FRONTEND_PRESENT=yes) was a third,
+# ungated lane -- and it drove the operator's real backend during iter-8 itself
+# (read-only that time; the page it drove carries a "Run Backscan" button).
+# Structural, same rationale as section 9: qa-phase.sh also dispatches a real
+# `claude` call this suite cannot mock.
+QA_PHASE="$ENGINE_ROOT/scripts/automation/qa-phase.sh"
+
+grep -qE '^source "\$SCRIPT_DIR/lib/replay-lane\.sh"' "$QA_PHASE" \
+  && assert "qa-phase.sh sources lib/replay-lane.sh (for store_scope_require)" pass \
+  || assert "qa-phase.sh sources lib/replay-lane.sh (for store_scope_require)" fail
+
+grep -qF 'if [[ "$FRONTEND_PRESENT" == "yes" ]] && ! store_scope_require; then' "$QA_PHASE" \
+  && assert "qa-phase.sh calls store_scope_require, gated on FRONTEND_PRESENT" pass \
+  || assert "qa-phase.sh calls store_scope_require, gated on FRONTEND_PRESENT" fail
+
+_qa_gate_line="$(grep -n 'store_scope_require' "$QA_PHASE" | grep -v '^[0-9]*:#' | head -1 | cut -d: -f1)"
+_qa_dispatch_line="$(grep -n 'record_agent_invocation_start qa' "$QA_PHASE" | head -1 | cut -d: -f1)"
+[[ -n "$_qa_gate_line" && -n "$_qa_dispatch_line" && "$_qa_gate_line" -lt "$_qa_dispatch_line" ]] \
+  && assert "qa-phase.sh: the store-scope gate runs BEFORE the agent is dispatched" pass \
+  || assert "qa-phase.sh: the store-scope gate runs BEFORE the agent is dispatched" fail
+
+# Functional: the gate really does refuse a browser pass when the project
+# declares scope and the backend fails the assert -- reusing this file's own
+# sandbox fixture rather than re-deriving the refusal logic.
+write_env 'STORE_SCOPE_ASSERT_CMD="bash scripts-assert.sh"'
+: > "$SBX_STAMP"; rm -f "$SBX_SCOPED_MARKER"
+(
+  set -euo pipefail
+  source "$SBX/scripts/automation/lib/replay-lane.sh"
+  REPO_ROOT="$SBX"; STORE_SCOPE_ROOT="$SBX"
+  FRONTEND_PRESENT="yes"; QA_STORE_SCOPE_SKIP_REASON=""
+  # verbatim the qa-phase.sh gate line under test
+  if [[ "$FRONTEND_PRESENT" == "yes" ]] && ! store_scope_require; then
+    FRONTEND_PRESENT="no"
+    QA_STORE_SCOPE_SKIP_REASON="refused"
+  fi
+  echo "FRONTEND_PRESENT=$FRONTEND_PRESENT REASON=$QA_STORE_SCOPE_SKIP_REASON"
+) > "$WORK/qa-gate.out" 2>&1 || true
+grep -q "FRONTEND_PRESENT=no REASON=refused" "$WORK/qa-gate.out" \
+  && assert "qa-phase.sh gate: an unscoped backend flips FRONTEND_PRESENT to no" pass \
+  || assert "qa-phase.sh gate: an unscoped backend flips FRONTEND_PRESENT to no (got: $(cat "$WORK/qa-gate.out"))" fail
+
+echo "== 11. goal-playbook-iter-9: tapeology's own store-scope.env never forces playbook fixtures onto an unrelated project (TC-17) =="
+# This section reads tapeology's REAL project-extensions/store-scope/store-scope.env (the actual
+# project config, not the synthetic sandbox one `write_env` builds above) -- unlike every other
+# section, which proves the GENERIC framework mechanism, this proves tapeology's own identity guard
+# fires correctly. ENGINE_ROOT is this checkout's engine dir, so its PARENT is the real tapeology
+# project root.
+TAPEOLOGY_ROOT="$(cd "$ENGINE_ROOT/.." && pwd)"
+TAPEOLOGY_ENV="$TAPEOLOGY_ROOT/project-extensions/store-scope/store-scope.env"
+if [[ -f "$TAPEOLOGY_ENV" ]]; then
+  _out="$(bash -c "ROOT='$TAPEOLOGY_ROOT'; source '$TAPEOLOGY_ENV'; echo \"E=\${STORE_SCOPE_ENABLED:-unset}\"" 2>&1)"
+  [[ "$_out" == "E=1" ]] \
+    && assert "tapeology's store-scope.env enables scope for its OWN project root" pass \
+    || assert "tapeology's store-scope.env enables scope for its OWN project root (got: $_out)" fail
+
+  _fake="$WORK/unrelated-project"
+  mkdir -p "$_fake/apps/backend"
+  _out="$(bash -c "ROOT='$_fake'; source '$TAPEOLOGY_ENV'; echo \"E=\${STORE_SCOPE_ENABLED:-unset}\"" 2>&1)"
+  [[ "$_out" == "E=unset" ]] \
+    && assert "tapeology's store-scope.env no-ops for an unrelated project root (no remote, no playbook module)" pass \
+    || assert "tapeology's store-scope.env no-ops for an unrelated project root (got: $_out)" fail
+else
+  echo "  (skipped -- no project-extensions/store-scope/store-scope.env in this checkout)"
+fi
+
 echo ""
 echo "test-store-scope-guard: $PASS passed, $FAIL failed"
 [[ "$FAIL" -eq 0 ]]
diff --git a/project-extensions/store-scope/README.md b/project-extensions/store-scope/README.md
index b71580f..385d397 100644
--- a/project-extensions/store-scope/README.md
+++ b/project-extensions/store-scope/README.md
@@ -60,6 +60,18 @@ bash incredible_auto_dev/scripts/automation/store-scope/store-scope.sh verify /t
      reports/qa/<iter>-store-scope-guard.md
 ```
 
+## Project-identity guard (goal-playbook-iter-9)
+
+`store-scope.env`'s commands are tapeology-specific — `STORE_SCOPE_PREPARE_CMD` force-swaps the QA
+port to tapeology's own playbook fixture rig. `project-extensions/` is deliberately NOT part of the
+`incredible_auto_dev/` vendored subtree, so a project that pulls the framework the sanctioned way
+never sees this file. The residual risk is a project bootstrapped by copying this whole repo as a
+starting template, carrying `project-extensions/` along by accident. The file now opens with a
+guard: it declares nothing (leaves `STORE_SCOPE_ENABLED` unset, so `store-scope.sh`'s own
+no-config no-op applies) unless the resolved project root's git remote names `tapeology`, or — when
+there is no remote at all — `apps/backend/app/research/desk_playbook.py` exists. Either check absent
+⇒ this file never forces playbook fixture data onto an unrelated project's lanes.
+
 ## What is deliberately NOT protected
 
 The derived accelerator DBs (`bar_index.db`, `*_meta_cache.db`, `tradability_cache.db`,
diff --git a/project-extensions/store-scope/store-scope.env b/project-extensions/store-scope/store-scope.env
index d0cf68a..fa12eb5 100644
--- a/project-extensions/store-scope/store-scope.env
+++ b/project-extensions/store-scope/store-scope.env
@@ -12,6 +12,26 @@
 # own immutable-data rail forbids ever pruning. The launcher that would have prevented it existed
 # and was correct; nothing obliged the lane to use it. These four lines are that obligation.
 
+# Project-identity guard (goal-playbook-iter-9, T-1/TC-17): everything below is
+# tapeology-SPECIFIC — the ASSERT/PREPARE commands invoke tapeology's own scripts and force
+# tapeology's playbook fixture rig onto the QA port. `project-extensions/` is deliberately NOT part
+# of the `incredible_auto_dev/` vendored subtree (see `incredible_auto_dev/CLAUDE.md`'s MODES
+# table), so a project that pulls the framework the sanctioned way never sees this file at all. The
+# residual risk this guards against is a project bootstrapped by copying this whole repo as a
+# starting template — carrying `project-extensions/` along by accident, onto a QA port this file
+# would then silently force-swap to tapeology's playbook fixtures. Fail closed: when the resolved
+# project root ($ROOT, set by store-scope.sh before sourcing this file) has a git remote that does
+# not name tapeology, OR has no remote AND lacks the playbook module these commands assume exists,
+# this file declares nothing below and store-scope.sh's own "no config -> no-op" path applies
+# unchanged — the guard never forces playbook test data onto an unrelated project's lanes.
+_ss_remote="$(git -C "${ROOT:-.}" remote get-url origin 2>/dev/null || true)"
+if [[ -n "$_ss_remote" ]]; then
+  [[ "$_ss_remote" == *tapeology* ]] || { return 0 2>/dev/null || exit 0; }
+elif [[ ! -f "${ROOT:-.}/apps/backend/app/research/desk_playbook.py" ]]; then
+  return 0 2>/dev/null || exit 0
+fi
+unset _ss_remote
+
 STORE_SCOPE_ENABLED=1
 STORE_SCOPE_LABEL="tapeology real .data store"
 
```
