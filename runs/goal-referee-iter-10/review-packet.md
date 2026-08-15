# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 11. Shown in full: 10.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/frontend/app/desk/page.tsx` (595 lines not shown)

```diff
diff --git a/apps/backend/app/mcp/__init__.py b/apps/backend/app/mcp/__init__.py
index 7c6a7e8..d6b6915 100644
--- a/apps/backend/app/mcp/__init__.py
+++ b/apps/backend/app/mcp/__init__.py
@@ -19,8 +19,9 @@ Result contract (locked by ``tests/test_mcp_server.py``):
     via ``get_endpoint`` — at J-05; ``bars`` at era-4 J-01; ``levels`` at era-4 J-02; ``strategies``
     at era-4 J-04; ``tradability`` at era-5B J-01; ``setups`` at era-5B J-02; ``edge_report`` at
     era-5B J-04; ``desk_universe``/``desk_screen`` at era-desk J-06; ``desk_playbook``/
-    ``desk_playbook_evidence`` at Era B2 J-09); an allowlisted-but-UNKNOWN path (any unshipped
-    ``/research/*``) still surfaces the backend's honest 404 this way — never placeholder data.
+    ``desk_playbook_evidence`` at Era B2 J-09; ``desk_referee``/``desk_referee_registry`` at Era 6
+    "The Referee" J-09); an allowlisted-but-UNKNOWN path (any unshipped ``/research/*``) still
+    surfaces the backend's honest 404 this way — never placeholder data.
   * backend unreachable — an explicit tool error naming the base URL and the failure
     (``BackendUnreachableError``); NEVER cached or fabricated data (no cache, no retry loop,
     no offline snapshot exists anywhere in this module).
@@ -127,6 +128,16 @@ _STATIC_PATHS: dict[str, str] = {
     # cross-product cell shape, honest `n: 0` before any playbook has ever been recorded -- never a
     # 404). The `?signature=` inspect-mode variant stays reachable only through `get_endpoint`.
     "desk_playbook_evidence": "/research/desk/playbook/evidence",
+    # `desk_referee`/`desk_referee_registry` (Era 6 "The Referee" J-09, MCP contract v5 -- 20 -> 22
+    # tools) are the IDENTICAL no-required-param shape as `desk_playbook`/`desk_playbook_evidence`
+    # directly above: each proxies an endpoint that already serves an explicit HTTP 200
+    # honest-empty/honest-live payload before any hypothesis is ever registered or evaluated (never
+    # a 404). `desk_referee` is the read-side adjudication fold (verdict + provenance per
+    # hypothesis, plus the served REFEREE_REGISTER text); `desk_referee_registry` is the
+    # family/hypothesis/withdrawal/certificate registry. Neither exposes any query-param variant --
+    # both routes take none.
+    "desk_referee": "/research/desk/referee/adjudications",
+    "desk_referee_registry": "/research/desk/referee/registry",
 }
 
 _TAPE_PATHS: dict[str, str] = {
@@ -370,6 +381,32 @@ TOOLS: tuple[types.Tool, ...] = (
         ),
         inputSchema=_object_schema({}),
     ),
+    types.Tool(
+        name="desk_referee",
+        description=(
+            "Read-only proxy of GET /research/desk/referee/adjudications -- Era 6 \"The Referee\" "
+            "J-06's read-side adjudication fold: for every registered hypothesis, its verdict in "
+            "the exact vocabulary (registered / pending_forward_confirmation / "
+            "insufficient_sample / fragile / no_evidence / corroborated / basis_retired), its "
+            "confirmatory_output_refused state and refusal_reason when refused, its recorded "
+            "checkpoint snapshot when one exists (family BH fold, fragility_triggers, "
+            "evaluation_basis hash, attestation pass/fail) or an honest live pre-checkpoint "
+            "accrual fold when none does yet, beside the served REFEREE_REGISTER disclosure text "
+            "(what a verdict does NOT mean), JSON verbatim. Never 404/500 on an empty or "
+            "partially-corrupted registry."
+        ),
+        inputSchema=_object_schema({}),
+    ),
+    types.Tool(
+        name="desk_referee_registry",
+        description=(
+            "Read-only proxy of GET /research/desk/referee/registry -- Era 6 \"The Referee\" "
+            "J-05's append-only pre-registration registry: every recorded family, hypothesis "
+            "(with its read-side status/discovery/accrual additions), withdrawal, and "
+            "certificate, JSON verbatim. Never 404/500 on an empty registry."
+        ),
+        inputSchema=_object_schema({}),
+    ),
     types.Tool(
         name="pnl_ledger",
         description=(
diff --git a/apps/backend/app/research/referee_adjudicate.py b/apps/backend/app/research/referee_adjudicate.py
index b282a71..f239d80 100644
--- a/apps/backend/app/research/referee_adjudicate.py
+++ b/apps/backend/app/research/referee_adjudicate.py
@@ -3,7 +3,8 @@ J-02 (``referee_evidence.py``) -> J-03 (``referee_stats.py``) -> J-04 (``referee
 (``referee_registry.py``) built for. Implements ``docs/referee-statistical-spec.md`` Sec3/Sec5/Sec8
 verbatim: the three estimand engines (A/B/C), evaluation as a recorded operator act, the single
 append-only confirmatory checkpoint with its family BH fold, the read-side adjudication fold, and
-``authorize_promotion`` (the J-08 interlock's pure decision function, unwired this iteration).
+``authorize_promotion`` (the J-08 interlock's pure decision function -- wired into
+``pnl_scan._promote`` as of iteration 9).
 
 **"Eligible occurrence" for a hypothesis, restated.** A hypothesis registers exactly ONE primary
 ``(measure_key, horizon)`` (spec Sec3) over ONE ``(setup_id, side)`` cell. The J-02 observation
@@ -518,7 +519,38 @@ def _pool_for_estimand(
 # === J-08 Step 1: the strategy-family analog pooling (spec Sec3.7) ====================================
 
 
-def _pool_strategy_trades(journal_store: JournalStore) -> dict:
+def _strategy_backtest_id(observation_id: str) -> str:
+    """The backtest id embedded in a strategy-family observation id -- the inverse of
+    ``referee_evidence._strategy_observation``'s own
+    ``f"strategy:{backtest_id}:{kind}:{index}"`` construction (mirrors
+    ``referee_null._parse_observation_id``'s identical parsing precedent for the Playbook
+    family's own ``f"playbook:{record_id}:{index}:{measure_key}"`` id shape)."""
+    prefix, backtest_id, _kind, _index_str = observation_id.split(":", 3)
+    if prefix != "strategy":
+        raise ValueError(f"not a strategy observation id: {observation_id!r}")
+    return backtest_id
+
+
+def _candidate_matches_observation(
+    journal_store: JournalStore, observation_id: str, candidate: dict, cache: dict[str, tuple]
+) -> bool:
+    """Whether ``observation_id``'s own backtest report was recorded under ``candidate``'s exact
+    ``(strategy_id, profile)`` -- read from the SAME ``result["strategy_id"]``/``result["profile"]``
+    fields ``backtests.py``'s result block already stamps on every journal record (no new field, no
+    second identity join: this is a single ``JournalStore.get_backtest`` read of a field
+    ``strategy_observations()`` itself never surfaces on the observation, not a re-derivation of
+    dataset identity). Memoized per ``backtest_id`` in ``cache`` so a dataset's many trades cost one
+    lookup each, never a rescan of the whole journal."""
+    backtest_id = _strategy_backtest_id(observation_id)
+    if backtest_id not in cache:
+        record = journal_store.get_backtest(backtest_id)
+        result = (record.payload.get("result") or {}) if record is not None else {}
+        cache[backtest_id] = (result.get("strategy_id"), result.get("profile"))
+    strategy_id, profile = cache[backtest_id]
+    return strategy_id == candidate.get("strategy_id") and profile == candidate.get("profile")
+
+
+def _pool_strategy_trades(journal_store: JournalStore, *, candidate: dict | None = None) -> dict:
     """The strategy-family analog of ``_pool_against_null`` (spec Sec3.7: "Cluster = dataset. Per
     dataset d with >=1 candidate trade: Delta_d = mean(candidate net_r in d) - mean(recorded
     random_null net_r in d)") -- reuses ``referee_evidence.strategy_observations()`` verbatim
@@ -527,6 +559,17 @@ def _pool_strategy_trades(journal_store: JournalStore) -> dict:
     so ``run_evaluation_and_record`` reuses every downstream step (coverage, permutation test,
     both bootstrap CIs, BH, snapshot) with zero branching beyond the POOLING call itself.
 
+    ``candidate`` (goal-referee-iter-10 rider 1, closing the iter-9-recorded MINOR anti-goal entry:
+    a certificate's declared candidate was never checked against the evidence it was minted from)
+    is an optional ``{"strategy_id": str, "profile": str}`` filter: when supplied, BOTH the
+    candidate trades and the recorded ``random_null`` trades are narrowed to observations whose own
+    backtest report was recorded under this EXACT ``(strategy_id, profile)``
+    (``_candidate_matches_observation``) before pooling -- so a dataset carrying trades from an
+    unrelated strategy's report can never leak into this candidate's evidence, and the paired
+    ``random_null`` values stay drawn from the SAME report as the candidate trades they are diffed
+    against (never a foreign strategy's null baseline). ``None`` (the default -- every existing
+    route/CLI caller today) pools the whole corpus unfiltered, byte-identical to before this rider.
+
     ``occurrence_diffs`` is honestly ``None`` (``_pool_cell_vs_complement``'s own "not defined at
     occurrence level" precedent, not ``_pool_against_null``'s occurrence-diff list): unlike
     estimand A/C's ToD-matched null (exactly ``K`` anchors per occurrence, a natural per-occurrence
@@ -538,14 +581,26 @@ def _pool_strategy_trades(journal_store: JournalStore) -> dict:
     ``occurrence_diffs``/``_ESTIMANDS_AGAINST_NULL`` in ``run_evaluation_and_record``), which is
     correct here -- there is no occurrence-level uncertainty quantity to disclose."""
     obs = strategy_observations(journal_store)
+    observations = obs["observations"]
+    null_observations = obs["null_observations"]
+    if candidate is not None:
+        match_cache: dict[str, tuple] = {}
+        observations = [
+            o for o in observations
+            if _candidate_matches_observation(journal_store, o["observation_id"], candidate, match_cache)
+        ]
+        null_observations = [
+            o for o in null_observations
+            if _candidate_matches_observation(journal_store, o["observation_id"], candidate, match_cache)
+        ]
     by_cluster_candidate: dict[str, list[float]] = {}
     by_cluster_null: dict[str, list[float]] = {}
     observation_ids_by_cluster: dict[str, set[str]] = {}
-    for observation in obs["observations"]:
+    for observation in observations:
         cluster_key = observation["cluster_key"]
         by_cluster_candidate.setdefault(cluster_key, []).append(observation["value"])
         observation_ids_by_cluster.setdefault(cluster_key, set()).add(observation["observation_id"])
-    for observation in obs["null_observations"]:
+    for observation in null_observations:
         by_cluster_null.setdefault(observation["cluster_key"], []).append(observation["value"])
 
     all_clusters = set(by_cluster_candidate) | set(by_cluster_null)
@@ -1200,8 +1255,20 @@ def run_evaluation_and_record(
             # session_date (``_pool_strategy_trades``, never ``_pool_for_estimand``'s playbook-only
             # occurrence gather). ``journal_store=None`` (no production caller reaches this branch
             # without one this era) pools an honest empty corpus rather than raise.
+            #
+            # goal-referee-iter-10 rider 1: ``candidate`` is passed through ONLY when
+            # ``certificate_mint`` is supplied -- the only path that can ever mint a certificate
+            # (still zero production callers this era) -- so the pooled evidence is narrowed to the
+            # exact ``(strategy_id, profile)`` the certificate is about to name. Every other caller
+            # (``certificate_mint=None``) keeps pooling whole-corpus and unfiltered, byte-identical
+            # to before this rider.
             pool = (
-                _pool_strategy_trades(journal_store)
+                _pool_strategy_trades(
+                    journal_store,
+                    candidate=(
+                        certificate_mint["candidate"] if certificate_mint is not None else None
+                    ),
+                )
                 if journal_store is not None
                 else {
                     "session_groups": {}, "occurrence_diffs": None, "occurrences_pooled": 0,
@@ -1717,19 +1784,20 @@ def adjudications_response(
     }
 
 
-# === authorize_promotion: the J-08 interlock's pure decision function (unwired this iteration) ========
+# === authorize_promotion: the J-08 interlock's pure decision function ==================================
 
 
 def authorize_promotion(
     candidate: dict, certificate_store, live_scan_context: dict,
 ) -> dict:
     """A pure function (spec Sec8): does a valid, candidate-specific Referee certificate authorize
-    promoting ``candidate = {"strategy_id": str, "profile": str}``? Reads the (still-empty this
-    iteration) ``CertificateStore`` and ``live_scan_context`` (the live scan's OWN current report
-    values: ``{"champion_identity": dict, "train_dataset": dict, "holdout_dataset": dict,
+    promoting ``candidate = {"strategy_id": str, "profile": str}``? Reads the ``CertificateStore``
+    and ``live_scan_context`` (the live scan's OWN current report values:
+    ``{"champion_identity": dict, "train_dataset": dict, "holdout_dataset": dict,
     "config_fingerprint": str, "gate_version": str, "referee_parameters_hash": str}``) -- returns
-    ``{"authorized": bool, "refusal_class": str|None, "reason": str|None}``. NOT wired into
-    ``pnl_scan._promote`` this iteration (J-08's job) -- a pure, unwired function only.
+    ``{"authorized": bool, "refusal_class": str|None, "reason": str|None}``. Wired into
+    ``pnl_scan._promote`` as of iteration 9 (J-08) -- called there BEFORE
+    ``append_validation_row``, so an unauthorized candidate is refused before anything is written.
 
     **The six refusal classes, partitioned** (spec Sec8 names all six but does not fully
     disambiguate their boundaries -- this partition is an iter-7 interpretation call, logged to
diff --git a/apps/backend/tests/test_desk_refresh_chain_guard.py b/apps/backend/tests/test_desk_refresh_chain_guard.py
index 9302c9a..b3d868b 100644
--- a/apps/backend/tests/test_desk_refresh_chain_guard.py
+++ b/apps/backend/tests/test_desk_refresh_chain_guard.py
@@ -157,8 +157,27 @@ _UNIVERSE_FETCH_PATH = "/research/desk/universe/fetch"
 # `forwardComputeRef` precedent, which that effect's own comment already anticipated), they start
 # no interval, and they wait on the chain's one existing sleep. A future step that cannot say the
 # same must re-derive these three numbers here rather than loosen them.
-_EXPECTED_EFFECT_COUNT = 19
-_EXPECTED_INTERVAL_COUNT = 7
+#
+# 19 -> 21 and 7 -> 9 for Referee Runs (goal-referee-iter-10, J-09) -- the EIGHTH and NINTH compute
+# managers (`RefereeNullComputeManager`, `RefereeEvaluationComputeManager`), and the first two that
+# are single-flight PER KEY (`null_spec_id` / `hypothesis_id`) rather than one page-wide singleton.
+# Neither joins the refresh chain (an operator-run null-build/evaluation is its own act, never an
+# eighth/ninth chain step) NOR the existing nine-GET mount effect (the `forwardComputeRef`-mirror
+# precedent does not apply here: unlike every prior manager, this page does not know WHICH keys
+# exist until the registry read resolves on first expand of "Referee Adjudications"/"Referee Runs" --
+# there is no fixed key to seed a live snapshot for at mount time, so none is fetched; an absent key
+# renders as idle, the backend's own `_IDLE_SNAPSHOT_TEMPLATE`-when-absent convention). +2 effects,
+# +2 intervals: ONE poll effect PER MANAGER (never per key -- each effect polls EVERY currently-
+# running key from a single `setInterval`, since the key set is dynamic and unbounded in principle,
+# unlike the fixed-arity managers before it), each mirroring the Backscan poll's own "stop on any
+# non-running status, refresh the ledger once on that terminal tick" shape. The Referee Adjudications
+# section's OWN deferred read (and Referee Runs' own registry/run-ledger reads) add NO effect at all
+# -- `toggleSection` is a plain event handler, never an effect (the `refereeRegistry` precedent
+# directly above). The timeout is untouched -- neither section has a wait-tick of its own; neither is
+# part of the chain. Neither new effect can reach a trigger, which is the property the scan below
+# actually polices; the counts are here so that scan stays provably complete.
+_EXPECTED_EFFECT_COUNT = 21
+_EXPECTED_INTERVAL_COUNT = 9
 _EXPECTED_TIMEOUT_COUNT = 1
 
 # Everything that could start real work. The chain's own driver is included: an effect that calls
@@ -188,6 +207,15 @@ _TRIGGER_CALLS = (
     # now a path to a trigger and must be as unreachable from an effect as the core it wraps.
     "handleRunPlaybookClick(",
     "handleRunBackscanClick(",
+    # goal-referee-iter-10 (J-09): Referee Runs' own handler/client pairs -- the SAME mirror, keyed
+    # per null_spec_id / hypothesis_id rather than a page-wide singleton. Neither pair ever joins
+    # the refresh chain (an operator-run null-build/evaluation is its own act, never an eighth/ninth
+    # chain step -- see _EXPECTED_EFFECT_COUNT's own rationale above), so both stay in
+    # _TRIGGER_CALLS with no REVERSED counterpart below: no useEffect may reach either.
+    "handleTriggerRefereeNullBuild(",
+    "triggerRefereeNullsCompute(",
+    "handleTriggerRefereeEvaluate(",
+    "triggerRefereeEvaluate(",
 )
 
 # Machinery that can invoke a handler without a user click. None of it is used by this page today;
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index e747bde..7d7217d 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -256,6 +256,24 @@ _PRICE_ARITHMETIC_FIELDS = (
     # the obvious client-side subtraction to reach for and the obvious thing to get wrong; the
     # backend already served both halves of the ratio as computed numbers).
     r"|hyp\.accrual\.(?:informative_post_boundary_sessions|target_sessions)"
+    # goal-referee-iter-10 (J-09): the Referee Adjudications section's own served numerics -- the
+    # live pre-checkpoint accrual pair (the SAME "sessions accrued so far" risk the `hyp.accrual.*`
+    # entry above already guards, applied to the adjudications response's own `live_coverage` fold
+    # -- `entry.live_coverage?.post_boundary_sessions`/`?.target_sessions` in
+    # `RefereeAdjudicationEntryRow`, `\??` covering the optional-chaining `?.` the JSX actually
+    # uses) and the recorded checkpoint snapshot's own Benjamini-Hochberg fold (`snapshot.bh.k_star`/
+    # `.m`/`.q` -- never combined into a client-computed pass rate or "how many below threshold"
+    # count).
+    r"|entry\.live_coverage\??\.(?:post_boundary_sessions|target_sessions)"
+    r"|snapshot\.bh\.(?:k_star|m|q)"
+    # goal-referee-iter-10 (J-09): the Referee Runs section's own served numerics -- both
+    # single-flight-PER-KEY compute managers' live `{done,total}` progress pair
+    # (`compute?.done`/`compute?.total` in `RefereeNullBuildControl`/`RefereeEvaluateControl`,
+    # `\??` covering the same optional-chaining usage), and the durable run-ledger's own
+    # `{done,total}` progress pair, nested one level deeper under `run.progress` (`RefereeNullRunRow`/
+    # `RefereeEvaluationRunRow`).
+    r"|compute\??\.(?:done|total)"
+    r"|run\.progress\.(?:done|total)"
 )
 _PRICE_ARITHMETIC_PATTERN = re.compile(
     rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
@@ -508,6 +526,57 @@ def test_desk_page_price_arithmetic_guard_catches_hyp_accrual_arithmetic_in_isol
     )
     assert _PRICE_ARITHMETIC_PATTERN.search(seeded_ratio) is not None
 
+
+def test_desk_page_price_arithmetic_guard_catches_referee_adjudications_and_runs_field_arithmetic():
+    """goal-referee-iter-10 (J-09) counter-test: the extended guard catches arithmetic on the new
+    Referee Adjudications section's `entry.live_coverage.*`/`snapshot.bh.*` bindings and the new
+    Referee Runs section's `compute.*`/`run.progress.*` bindings -- covering BOTH the
+    optional-chaining (`?.`) and plain-dot forms the guard's `\\??` now accepts, proving each new
+    field path is genuinely covered (not just listed, TC-20)."""
+    seeded_live_coverage = (
+        "const remaining = entry.live_coverage.target_sessions - "
+        "entry.live_coverage.post_boundary_sessions;"
+    )
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_live_coverage) is not None
+
+    seeded_live_coverage_optional = (
+        "const remaining = entry.live_coverage?.target_sessions - "
+        "entry.live_coverage?.post_boundary_sessions;"
+    )
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_live_coverage_optional) is not None
+
+    seeded_bh = "const nonSignificant = snapshot.bh.m - snapshot.bh.k_star;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_bh) is not None
+
+    seeded_bh_rate = "const passRate = snapshot.bh.k_star / snapshot.bh.m;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_bh_rate) is not None
+
+    seeded_compute = "const remaining = compute.total - compute.done;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_compute) is not None
+
+    seeded_compute_optional = "const remaining = compute?.total - compute?.done;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_compute_optional) is not None
+
+    seeded_run_progress = "const remaining = run.progress.total - run.progress.done;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_run_progress) is not None
+
+    # And the pattern does NOT over-match: the real page's own pass-through renderings -- the
+    # optional-chaining accrual pair, the BH template-literal display, the fmt()-wrapped compute
+    # progress, and the run-ledger progress pair -- stay clean (the EXACT JSX/template-literal
+    # idioms RefereeAdjudicationEntryRow/RefereeNullBuildControl/RefereeEvaluateControl/
+    # RefereeNullRunRow/RefereeEvaluationRunRow actually use).
+    assert _PRICE_ARITHMETIC_PATTERN.search(
+        '{entry.live_coverage?.post_boundary_sessions ?? 0} /{" "}\n'
+        "{entry.live_coverage?.target_sessions ?? 0} sessions"
+    ) is None
+    assert _PRICE_ARITHMETIC_PATTERN.search(
+        "`${snapshot.bh.k_star} / ${snapshot.bh.m} (q=${snapshot.bh.q})`"
+    ) is None
+    assert _PRICE_ARITHMETIC_PATTERN.search(
+        "{fmt(compute?.done ?? 0, 0)} / {fmt(compute?.total ?? 0, 0)}"
+    ) is None
+    assert _PRICE_ARITHMETIC_PATTERN.search("{run.progress.done} / {run.progress.total}") is None
+
     # The shipped pass-through rendering (page.tsx's own "X / Y" JSX line) stays clean.
     assert _PRICE_ARITHMETIC_PATTERN.search(
         "{hyp.accrual.informative_post_boundary_sessions} / {hyp.accrual.target_sessions}"
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index a043721..a700812 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -43,16 +43,20 @@ from app.research.desk_forward import FORWARD_REGISTER, ForwardStore, forward_pa
 from app.research.desk_playbook import PLAYBOOK_REGISTER, PlaybookStore, playbook_parameters
 from app.research.desk_screen import ScreenStore
 from app.research.desk_universe import UniverseStore
+from app.research.referee_adjudicate import REFEREE_REGISTER
+from app.research.referee_null import REFEREE_NULL_TOD_SPEC_ID, REFEREE_TEST_PERM_SPEC_ID
+from app.research.referee_registry import REFEREE_MIN_OCCURRENCES, REFEREE_MIN_SESSIONS
 
 BACKEND_DIR = Path(__file__).resolve().parents[1]
 
 # Capability 6, verbatim — order and content are the advertised contract. ``bars`` (era-4 J-01),
 # ``levels`` (era-4 J-02), ``strategies`` (era-4 J-04), ``tradability`` (era-5B J-01), ``setups``
 # (era-5B J-02), ``desk_universe``/``desk_screen`` (era-desk J-06, MCP contract v3 -- 15 -> 17
-# tools), ``desk_forward`` (forward-test era, 17 -> 18 tools), and ``desk_playbook``/
+# tools), ``desk_forward`` (forward-test era, 17 -> 18 tools), ``desk_playbook``/
 # ``desk_playbook_evidence`` (Era B2 "The Playbook" J-09, the era's own MCP contract v4 -- 18 -> 20
-# tools) are the newest additions, each positioned right after its dependency-order sibling (the
-# same store/registry+route+MCP shape, mirrored end to end).
+# tools), and ``desk_referee``/``desk_referee_registry`` (Era 6 "The Referee" J-09, MCP contract v5
+# -- 20 -> 22 tools) are the newest additions, each positioned right after its dependency-order
+# sibling (the same store/registry+route+MCP shape, mirrored end to end).
 EXPECTED_TOOLS = (
     "tape_state",
     "tape_features",
@@ -70,6 +74,8 @@ EXPECTED_TOOLS = (
     "desk_forward",
     "desk_playbook",
     "desk_playbook_evidence",
+    "desk_referee",
+    "desk_referee_registry",
     "pnl_ledger",
     "taxonomy",
     "ui_route_map",
@@ -753,6 +759,155 @@ async def test_desk_playbook_evidence_tool_byte_identical_on_a_populated_state(m
     assert result.content[0].text.encode("utf-8") == rest.content, "desk_playbook_evidence not byte-identical"
 
 
+# --- Era 6 "The Referee" J-09: desk_referee / desk_referee_registry (MCP contract v5, 20 -> 22
+# tools; empty + populated + a corrupted-file honest-error state) -----------------------------------
+#
+# Both routes read stores rooted at env-var-or-sibling-of-the-universe-dir defaults
+# (`resolve_referee_registry_dir`/`resolve_referee_eval_dir`, neither a `Config` field) -- SIBLINGS
+# of `backend_paths`' own `TAPEOLOGY_DESK_UNIVERSE_DIR`, so they resolve to their own fresh
+# env-scoped temp dirs automatically, with no new fixture entry needed. Nothing else in this module
+# ever registers a hypothesis, so the honest-empty states below are genuinely observed BEFORE the
+# populated-state tests register one -- file order matters here, same as every other store in this
+# module. The populated-state tests register ONE real hypothesis through the actual
+# `POST /research/desk/referee/registry/hypotheses` route (the real operator act, never a
+# hand-crafted store file), and the corrupted-file tests run LAST (after both populated-state tests)
+# since they plant a permanently-broken file into the SAME shared registry dir.
+
+_REFEREE_MCP_HYPOTHESIS_PAYLOAD = {
+    "confirm": True,
+    "hypothesis_id": "mcp-referee-hyp-1",
+    "family_id": "mcp-referee-fam-1",
+    "family_q": 0.10,
+    "family_candidate_hypothesis_ids": ["mcp-referee-hyp-1"],
+    "evidence_family": "playbook",
+    "estimand": "A",
+    "setup_id": "capitulation",
+    "side": "long",
+    "context_predicate": None,
+    "primary_measure_key": "5m",
+    "primary_horizon": "5m",
+    "sidedness": "greater",
+    "null_spec_id": REFEREE_NULL_TOD_SPEC_ID,
+    "test_spec_id": REFEREE_TEST_PERM_SPEC_ID,
+    "target_sessions": REFEREE_MIN_SESSIONS,
+    "min_occurrences": REFEREE_MIN_OCCURRENCES,
+}
+
+
+@pytest.mark.anyio
+async def test_desk_referee_registry_tool_byte_identical_on_the_honest_empty_state(mcp_env):
+    """Before any hypothesis has ever been registered, `desk_referee_registry` proxies
+    `GET /research/desk/referee/registry`'s explicit HTTP 200 honest-empty payload -- never a 404
+    (the `desk_playbook` convention `referee_registry.py` itself follows)."""
+    result = await call_tool("desk_referee_registry", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/referee/registry", timeout=5.0)
+    assert rest.status_code == 200
+    assert rest.json() == {
+        "families": [], "hypotheses": [], "withdrawals": [], "certificates": [],
+        "integrity_errors": [],
+    }
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_referee_registry not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_desk_referee_tool_byte_identical_on_the_honest_empty_state(mcp_env):
+    """Before any hypothesis has ever been registered, `desk_referee` proxies
+    `GET /research/desk/referee/adjudications`'s explicit HTTP 200 honest-empty payload -- an empty
+    `entries` list beside the served `REFEREE_REGISTER` disclosure text, never a 404. Runs BEFORE
+    the populated-state test below registers anything into the shared env-scoped registry dir."""
+    result = await call_tool("desk_referee", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/referee/adjudications", timeout=5.0)
+    assert rest.status_code == 200
+    assert rest.json() == {"entries": [], "register": REFEREE_REGISTER, "integrity_errors": []}
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_referee not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_desk_referee_registry_tool_byte_identical_on_a_populated_state(mcp_env):
+    """Registers ONE real hypothesis through the actual registration route (the real operator act,
+    never a hand-crafted store file), then proves `desk_referee_registry` is still byte-identical
+    to curl on a NON-EMPTY result."""
+    resp = httpx.post(
+        f"{mcp_env}/research/desk/referee/registry/hypotheses",
+        json=_REFEREE_MCP_HYPOTHESIS_PAYLOAD, timeout=5.0,
+    )
+    assert resp.status_code == 200, resp.text
+
+    result = await call_tool("desk_referee_registry", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/referee/registry", timeout=5.0)
+    assert rest.status_code == 200
+    body = rest.json()
+    assert len(body["hypotheses"]) >= 1, "the live registry must be non-empty for this proof"
+    assert any(h["hypothesis_id"] == "mcp-referee-hyp-1" for h in body["hypotheses"])
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_referee_registry not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_desk_referee_tool_byte_identical_on_a_populated_state(mcp_env):
+    """After the registration above, the fresh hypothesis has accrued zero post-boundary sessions
+    (no playbook signal was ever recorded in this module's own isolated playbook dir), so its live
+    fold reads `verdict: "registered"` -- `desk_referee` still proxies byte-identical over this
+    non-empty, still-pre-checkpoint entry."""
+    result = await call_tool("desk_referee", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/referee/adjudications", timeout=5.0)
+    assert rest.status_code == 200
+    body = rest.json()
+    assert len(body["entries"]) >= 1, "the live adjudications fold must be non-empty for this proof"
+    entry = next(e for e in body["entries"] if e["hypothesis_id"] == "mcp-referee-hyp-1")
+    assert entry["verdict"] == "registered"
+    assert body["register"] == REFEREE_REGISTER
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_referee not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_desk_referee_registry_tool_byte_identical_with_a_corrupted_hypothesis_file(
+    mcp_env, backend_paths,
+):
+    """Error case: an integrity-broken hypothesis file makes `GET /research/desk/referee/registry`
+    surface an honest `integrity_errors` entry rather than a 404/500 (the `test_referee_registry.py`
+    TC-30 precedent) -- `desk_referee_registry` still proxies byte-identical over that
+    degraded-but-200 body, never raising itself."""
+    universe_dir = Path(backend_paths["TAPEOLOGY_DESK_UNIVERSE_DIR"])
+    registry_dir = universe_dir.parent / "referee_registry"
+    registry_dir.mkdir(parents=True, exist_ok=True)
+    (registry_dir / "hypothesis-mcp-corrupt.json").write_text("not valid json at all")
+
+    result = await call_tool("desk_referee_registry", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/referee/registry", timeout=5.0)
+    assert rest.status_code == 200
+    assert len(rest.json()["integrity_errors"]) >= 1
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, (
+        "desk_referee_registry not byte-identical on a corrupted-file integrity-error state"
+    )
+
+
+@pytest.mark.anyio
+async def test_desk_referee_tool_byte_identical_with_a_corrupted_hypothesis_file(mcp_env):
+    """The SAME corrupted hypothesis file (seeded by the test above, into the shared env-scoped
+    registry dir) also surfaces through `GET /research/desk/referee/adjudications`'s own
+    `hypothesis_store.list()` read (`adjudications_response`'s iter-8 Rider-2 `integrity_errors`
+    disclosure) -- `desk_referee` still proxies byte-identical, never erroring."""
+    result = await call_tool("desk_referee", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/referee/adjudications", timeout=5.0)
+    assert rest.status_code == 200
+    assert len(rest.json()["integrity_errors"]) >= 1
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, (
+        "desk_referee not byte-identical on a corrupted-file integrity-error state"
+    )
+
+
 @pytest.mark.anyio
 async def test_desk_screen_reference_close_field_proxies_verbatim(mcp_env, backend_paths):
     """goal-desk-iter-17 (J-13) TC-10: `reference_close` -- `desk_screen.py`'s new ranked-row field
@@ -1368,7 +1523,9 @@ async def test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool(mcp_
     assert len(result.content) == 1
     assert result.content[0].text.encode("utf-8") == rest.content, "topup/runs not byte-identical"
     assert rest.json() == {"runs": [], "latest": None, "integrity_errors": []}
-    assert "desk_topup_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 20
+    # goal-referee-iter-10: the total grew 20 -> 22 (desk_referee/desk_referee_registry) -- this
+    # route's own no-new-tool claim is unaffected, so only the tracked total is re-derived here.
+    assert "desk_topup_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 22
 
 
 @pytest.mark.anyio
@@ -1387,7 +1544,9 @@ async def test_get_endpoint_desk_screen_runs_byte_identical_with_no_new_tool(mcp
     assert len(result.content) == 1
     assert result.content[0].text.encode("utf-8") == rest.content, "screen/runs not byte-identical"
     assert rest.json() == {"runs": [], "latest": None, "integrity_errors": []}
-    assert "desk_screen_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 20
+    # goal-referee-iter-10: the total grew 20 -> 22 (desk_referee/desk_referee_registry) -- this
+    # route's own no-new-tool claim is unaffected, so only the tracked total is re-derived here.
+    assert "desk_screen_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 22
 
 
 @pytest.mark.anyio
diff --git a/apps/backend/tests/test_pnl_scan.py b/apps/backend/tests/test_pnl_scan.py
index 814a845..8bcc513 100644
--- a/apps/backend/tests/test_pnl_scan.py
+++ b/apps/backend/tests/test_pnl_scan.py
@@ -256,14 +256,24 @@ def _strategy_trade(*, direction: str = "long", logical_ts: float = 100.0, net_r
 def _plant_strategy_backtest(
     journal_store: JournalStore, *, backtest_id: str, dataset: dict,
     candidate_net_r: float, null_net_r: float,
+    strategy_id: str = STRATEGY_V1_ID, profile: str = PROFILE_DEFAULT,
 ) -> None:
     """Plants one ``done`` backtest report whose ``result`` block already carries the dataset
     joined verbatim (``backtests.py``'s own result-block shape), reproduced by hand -- the
-    ``test_referee_evidence.py`` ``_plant_backtest_result`` precedent."""
+    ``test_referee_evidence.py`` ``_plant_backtest_result`` precedent.
+
+    ``strategy_id``/``profile`` (goal-referee-iter-10 rider 1) default to the champion identity but
+    are ALWAYS overridden by ``_mint_matching_certificate_through_the_real_rail`` below to match its
+    own caller-supplied ``candidate`` exactly -- before this rider, ``_pool_strategy_trades`` pooled
+    the whole journal unfiltered, so a hardcoded ``STRATEGY_V1_ID``/``PROFILE_DEFAULT`` stamp here
+    was harmless even when a caller's own ``candidate`` named a DIFFERENT strategy/profile (e.g.
+    ``STRATEGY_TAPE_ID``, or ``PROFILE_CANDIDATE_FASTER_WARMUP``); after the rider, the mint only
+    ever pools evidence whose OWN recorded identity matches the certificate's declared candidate, so
+    the planted fixture must genuinely BE that candidate's own evidence."""
     payload = {
         "id": backtest_id, "status": "done",
         "result": {
-            "dataset": dataset, "strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT,
+            "dataset": dataset, "strategy_id": strategy_id, "profile": profile,
             "config_fingerprint": CONFIG.config_fingerprint(),
             "trades": [_strategy_trade(net_r=candidate_net_r)],
             "null_baseline": {
@@ -294,6 +304,7 @@ def _mint_matching_certificate_through_the_real_rail(
         _plant_strategy_backtest(
             store, backtest_id=f"strategy-bt-{i}", dataset=dataset,
             candidate_net_r=1.0, null_net_r=-1.0,
+            strategy_id=candidate["strategy_id"], profile=candidate["profile"],
         )
 
     registry_dir = tmp_path / "referee_registry"
@@ -1210,26 +1221,43 @@ def test_a_survivor_with_zero_certificates_on_file_completes_the_sweep_honestly_
 
 # --- era-6 J-08 (TC-8): the no-bypass source-scan guard --------------------------------------------
 
+# goal-referee-iter-10 rider 3 (TC-17): the banned-token list and the scan assertion now live in ONE
+# helper (`_assert_no_bypass_tokens`) that BOTH the production lint below and its own can-fail proof
+# call -- before this rider, the can-fail test was a hand-typed string check
+# (`"--force" in lowered or "force" in lowered`) that never touched the real scan logic at all, so it
+# would have kept passing even if the production lint's own loop/assertion were gutted. Now the
+# can-fail test runs the SAME helper against a seeded, mutated copy of the real `pnl_scan.py` source,
+# so it genuinely fails only if that helper still does its job.
+_NO_BYPASS_BANNED_TOKENS = (
+    "--force", "force_promote", "force_certificate", "force=true",
+    "skip_certificate", "skip_cert", "no_certificate_required", "allow_without_certificate",
+    "default_allow", "tapeology_force", "tapeology_skip_cert",
+)
+
+
+def _assert_no_bypass_tokens(source: str, *, label: str) -> None:
+    """The promotion-interlock no-bypass scan itself (TC-8/TC-17): asserts none of
+    ``_NO_BYPASS_BANNED_TOKENS`` appears in ``source`` (case-insensitively), naming ``label`` and
+    the first offending token on failure. Every banned token is an underscore/flag-shaped
+    identifier (never a bare English word like "bypass" prose legitimately uses to describe the
+    ABSENCE of one -- this module's own docstrings do exactly that) so the scan cannot self-trip on
+    its own documentation."""
+    lowered = source.lower()
+    for token in _NO_BYPASS_BANNED_TOKENS:
+        assert token not in lowered, (
+            f"{label} contains a potential promotion-interlock bypass token: {token!r}"
+        )
+
 
 def test_no_bypass_path_exists_for_authorize_promotion():
     """TC-8: scans the two files implementing the promotion interlock's own source text for any
     CODE-shaped ``--force``/skip-flag/environment-override/default-allow IDENTIFIER that could
-    satisfy ``authorize_promotion`` without a genuine, matching, on-file certificate. Every banned
-    token below is an underscore/flag-shaped identifier (never a bare English word like "bypass"
-    prose legitimately uses to describe the ABSENCE of one -- this module's own docstrings do
-    exactly that) so the scan cannot self-trip on its own documentation. A lint that CAN fail on a
-    seeded violation (the ``test_desk_ui_guards.py`` precedent) — proven below."""
-    banned_tokens = (
-        "--force", "force_promote", "force_certificate", "force=true",
-        "skip_certificate", "skip_cert", "no_certificate_required", "allow_without_certificate",
-        "default_allow", "tapeology_force", "tapeology_skip_cert",
-    )
+    satisfy ``authorize_promotion`` without a genuine, matching, on-file certificate, via the SAME
+    ``_assert_no_bypass_tokens`` helper the can-fail proof below exercises. A lint that CAN fail on
+    a seeded violation (the ``test_desk_ui_guards.py`` precedent) — proven below."""
     for relative in ("research/pnl_scan.py", "research/referee_adjudicate.py"):
-        source = (BACKEND_DIR / "app" / relative).read_text().lower()
-        for token in banned_tokens:
-            assert token not in source, (
-                f"{relative} contains a potential promotion-interlock bypass token: {token!r}"
-            )
+        source = (BACKEND_DIR / "app" / relative).read_text()
+        _assert_no_bypass_tokens(source, label=relative)
     # `--strategy` is the ONE existing CLI flag on pnl_scan.py — proves this scan is not simply
     # rejecting every flag definition; it targets bypass-shaped tokens specifically.
     pnl_scan_source = (BACKEND_DIR / "app" / "research" / "pnl_scan.py").read_text()
@@ -1237,9 +1265,16 @@ def test_no_bypass_path_exists_for_authorize_promotion():
 
 
 def test_no_bypass_guard_can_fail_on_a_seeded_violation():
-    """The lint CAN fail — a lint that cannot fail proves nothing (the ``test_desk_ui_guards.py``
-    precedent)."""
-    seeded_source = "if args.force or os.environ.get('TAPEOLOGY_SKIP_CERTIFICATE'):\n    return authorized\n"
-    lowered = seeded_source.lower()
-    assert "--force" in lowered or "force" in lowered
-    assert "skip_certificate" in lowered
+    """TC-17: the lint CAN fail — a lint that cannot fail proves nothing (the
+    ``test_desk_ui_guards.py`` precedent). Exercises the REAL scan helper
+    (``_assert_no_bypass_tokens``), not a hand-typed string check, against a seeded, mutated copy of
+    the REAL ``pnl_scan.py`` source (the genuine, unmodified source passes it above) with a banned
+    bypass token appended -- so this test genuinely fails if the scan itself were gutted, rather
+    than merely proving an unrelated string contains "force"."""
+    real_source = (BACKEND_DIR / "app" / "research" / "pnl_scan.py").read_text()
+    seeded_source = (
+        real_source
+        + "\nif args.force or os.environ.get('TAPEOLOGY_SKIP_CERTIFICATE'):\n    return authorized\n"
+    )
+    with pytest.raises(AssertionError):
+        _assert_no_bypass_tokens(seeded_source, label="seeded pnl_scan.py")
diff --git a/apps/backend/tests/test_referee_adjudicate.py b/apps/backend/tests/test_referee_adjudicate.py
index 983b90a..b989e2f 100644
--- a/apps/backend/tests/test_referee_adjudicate.py
+++ b/apps/backend/tests/test_referee_adjudicate.py
@@ -1260,14 +1260,21 @@ def test_tc12_a_strategy_checkpoint_mints_exactly_one_certificate_through_the_re
 ):
     """TC-12: a strategy-family hypothesis reaching an attested, gate-passing confirmatory
     checkpoint mints EXACTLY one certificate, pinning every named field, reachable ONLY through
-    ``run_evaluation_and_record`` itself (never a hand-written fixture path in production code)."""
+    ``run_evaluation_and_record`` itself (never a hand-written fixture path in production code).
+
+    ``candidate`` is ``STRATEGY_V1_ID``/``PROFILE_DEFAULT`` (goal-referee-iter-10 rider 1) --
+    ``_plant_strong_strategy_effect``'s own planted trades are always recorded under that exact
+    identity, and the rider-1 pooling fix now genuinely requires the certificate's declared
+    candidate to match the evidence it is minted from (before this rider, an unrelated candidate
+    name here was harmless because pooling was unfiltered -- see the iter-9-recorded MINOR
+    anti-goal entry this rider closes)."""
     _plant_strong_strategy_effect(journal_store, n_clusters=12)
     registry_dir = tmp_path / "registry"
     family_store = FamilyStore(registry_dir)
     hypothesis_store = HypothesisStore(registry_dir)
     _register_strategy_hypothesis(family_store, hypothesis_store, "hyp-tc12", "fam-tc12")
     certificate_store = CertificateStore(registry_dir)
-    candidate = {"strategy_id": "structure_tape", "profile": PROFILE_DEFAULT}
+    candidate = {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
     champion_identity = {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
     train_dataset = {"id": "ds-train-pin", "checksum": "train-checksum", "split": "train"}
     holdout_dataset = {"id": "ds-holdout-pin", "checksum": "holdout-checksum", "split": "holdout"}
@@ -1343,7 +1350,12 @@ def test_tc13_a_failed_attestation_never_mints_a_strategy_certificate_role_stays
     eligible fixture as TC-12, forced through a deliberately failing oracle attestation --
     ``role`` stays ``"pending"`` (never ``"checkpoint"``), no snapshot, and therefore no
     certificate (the mint call site is only ever reached from inside the
-    ``recorded["role"] == "checkpoint"`` branch)."""
+    ``recorded["role"] == "checkpoint"`` branch).
+
+    ``candidate`` is ``STRATEGY_V1_ID``/``PROFILE_DEFAULT`` (goal-referee-iter-10 rider 1, the SAME
+    fix as TC-12 above) so ``confirmatory_eligible`` genuinely reflects real, matching pooled
+    coverage -- otherwise the rider-1 candidate filter would ALSO zero out coverage here, and this
+    test would no longer be isolating the attestation-failure gate it means to prove."""
     _plant_strong_strategy_effect(journal_store, n_clusters=12)
     registry_dir = tmp_path / "registry"
     family_store = FamilyStore(registry_dir)
@@ -1367,7 +1379,7 @@ def test_tc13_a_failed_attestation_never_mints_a_strategy_certificate_role_stays
         snapshot_store=AdjudicationSnapshotStore(tmp_path / "eval"),
         journal_store=journal_store,
         certificate_mint={
-            "candidate": {"strategy_id": "structure_tape", "profile": PROFILE_DEFAULT},
+            "candidate": {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT},
             "champion_identity_at_scan_time": {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT},
             "train_dataset": {"id": "ds-train", "checksum": "abc", "split": "train"},
             "holdout_dataset": {"id": "ds-holdout", "checksum": "def", "split": "holdout"},
@@ -1384,6 +1396,158 @@ def test_tc13_a_failed_attestation_never_mints_a_strategy_certificate_role_stays
     assert records == []
 
 
+# === goal-referee-iter-10 rider 1 (TC-13/14/15): the candidate-evidence-identity fix, closing the
+# iter-9-recorded MINOR anti-goal entry ("a strategy-family certificate's declared candidate was
+# never checked against the evidence it was minted from") =============================================
+
+
+def test_iter10_tc13_a_candidate_mismatched_mint_pools_none_of_the_unrelated_evidence_and_mints_nothing(
+    journal_store, tmp_path,
+):
+    """goal-referee-iter-10 TC-13: reproduces and closes the iter-9 evaluator's own probe
+    (``state/assumptions.md`` iter-9, goal-evaluator) -- 12 planted backtest trades all recorded
+    under ``strategy_id=STRATEGY_V1_ID``/``profile=PROFILE_DEFAULT`` (``_plant_strong_strategy_
+    effect``, the SAME fixture TC-12 above already proves mints a certificate for the MATCHING
+    candidate), evaluated with ``certificate_mint["candidate"]`` naming a totally unrelated
+    strategy/profile. Before this rider, ``_pool_strategy_trades`` pooled the whole corpus
+    unfiltered regardless of ``candidate``, so this unrelated candidate minted an attested,
+    gate-passing certificate anyway -- the exact exploit the iter-9 evaluator reproduced and
+    recorded as an open MINOR anti-goal entry. After this rider: the unrelated candidate's own
+    pool is empty (zero of the planted trades belong to it), so this evaluation is never even
+    confirmatory-eligible, and no certificate is minted naming the unrelated candidate."""
+    _plant_strong_strategy_effect(journal_store, n_clusters=12)
+    registry_dir = tmp_path / "registry"
+    family_store = FamilyStore(registry_dir)
+    hypothesis_store = HypothesisStore(registry_dir)
+    _register_strategy_hypothesis(family_store, hypothesis_store, "hyp-iter10-tc13", "fam-iter10-tc13")
+    certificate_store = CertificateStore(registry_dir)
+    unrelated_candidate = {
+        "strategy_id": "totally-unrelated-strategy", "profile": "totally-unrelated-profile",
+    }
+
+    result = run_evaluation_and_record(
+        "hyp-iter10-tc13",
+        hypothesis_store=hypothesis_store, family_store=family_store,
+        playbook_store=PlaybookStore(tmp_path / "unused-playbook"),
+        bar_store=BarStore(tmp_path / "unused-bars"), config=CONFIG,
+        null_store=RefereeNullStore(tmp_path / "unused-nulls"),
+        evaluation_store=RefereeEvaluationStore(tmp_path / "eval"),
+        snapshot_store=AdjudicationSnapshotStore(tmp_path / "eval"),
+        journal_store=journal_store,
+        certificate_mint={
+            "candidate": unrelated_candidate,
+            "champion_identity_at_scan_time": {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT},
+            "train_dataset": {"id": "ds-train", "checksum": "abc", "split": "train"},
+            "holdout_dataset": {"id": "ds-holdout", "checksum": "def", "split": "holdout"},
+            "certificate_store": certificate_store,
+        },
+    )
+    # Zero pooled evidence for the unrelated candidate -- never even confirmatory-eligible, so the
+    # write-side "checkpoint" role (the ONLY role that can reach the mint call site) is never
+    # reached.
+    assert result["record"]["coverage"]["post_boundary_informative_sessions"] == 0
+    assert result["record"]["coverage"]["occurrences_pooled"] == 0
+    assert result["record"]["confirmatory_eligible"] is False
+    assert result["record"]["role"] == "pending"
+    assert result["snapshot"] is None
+    assert result["certificate"] is None
+
+    records, errors = certificate_store.list()
+    assert errors == []
+    assert records == []  # no certificate minted naming the unrelated candidate
+
+
+def test_iter10_tc14_a_candidate_matched_mint_pools_the_evidence_and_mints_the_certificate(
+    journal_store, tmp_path,
+):
+    """goal-referee-iter-10 TC-14: the SAME 12 planted v1/default trades, evaluated with
+    ``certificate_mint["candidate"]`` naming the candidate the evidence ACTUALLY belongs to
+    (``STRATEGY_V1_ID``/``PROFILE_DEFAULT``) -- proves the rider-1 filter does not also break the
+    honest-match path: a certificate IS minted, with the identical p-value/gate-pass shape TC-12
+    above already proved for the unfiltered (``candidate=None``) path, since every planted trade
+    belongs to this exact candidate anyway (a filter that changes nothing when everything already
+    matches)."""
+    _plant_strong_strategy_effect(journal_store, n_clusters=12)
+    registry_dir = tmp_path / "registry"
+    family_store = FamilyStore(registry_dir)
+    hypothesis_store = HypothesisStore(registry_dir)
+    _register_strategy_hypothesis(family_store, hypothesis_store, "hyp-iter10-tc14", "fam-iter10-tc14")
+    certificate_store = CertificateStore(registry_dir)
+    matching_candidate = {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
+
+    result = run_evaluation_and_record(
+        "hyp-iter10-tc14",
+        hypothesis_store=hypothesis_store, family_store=family_store,
+        playbook_store=PlaybookStore(tmp_path / "unused-playbook"),
+        bar_store=BarStore(tmp_path / "unused-bars"), config=CONFIG,
+        null_store=RefereeNullStore(tmp_path / "unused-nulls"),
+        evaluation_store=RefereeEvaluationStore(tmp_path / "eval"),
+        snapshot_store=AdjudicationSnapshotStore(tmp_path / "eval"),
+        journal_store=journal_store,
+        certificate_mint={
+            "candidate": matching_candidate,
+            "champion_identity_at_scan_time": {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT},
+            "train_dataset": {"id": "ds-train", "checksum": "abc", "split": "train"},
+            "holdout_dataset": {"id": "ds-holdout", "checksum": "def", "split": "holdout"},
+            "certificate_store": certificate_store,
+        },
+    )
+    assert result["record"]["role"] == "checkpoint"
+    assert result["record"]["coverage"]["occurrences_pooled"] == 12  # all 12 candidate trades matched
+    assert result["record"]["permutation_p"] == pytest.approx(2.0 / (2**12 + 1))  # unchanged shape
+    assert result["snapshot"]["bh"]["bh_pass"] is True
+    certificate = result["certificate"]
+    assert certificate is not None
+    assert certificate["candidate"] == matching_candidate
+
+    records, errors = certificate_store.list()
+    assert errors == []
+    assert len(records) == 1
+    assert records[0]["candidate"] == matching_candidate
+
+
+def test_iter10_tc15_certificate_mint_none_keeps_whole_corpus_pooling_unfiltered_and_byte_identical(
+    journal_store,
+):
+    """goal-referee-iter-10 TC-15: ``candidate=None`` (the default -- every existing route/CLI
+    caller today, since ``certificate_mint`` still has zero production callers this era) pools the
+    whole ``JournalStore`` exactly as before this rider -- explicitly passing ``candidate=None``
+    produces the IDENTICAL pool as calling ``_pool_strategy_trades`` with no ``candidate`` argument
+    at all (the pre-rider call shape), proving the new parameter changes nothing for every caller
+    that does not supply it. Plants a MIXED corpus (never all one dataset cluster) so a real filter
+    regression would be visible here. The complementary real-corpus proof --
+    iter-9's own ``insufficient_sample``-on-real-corpus acceptance staying unchanged -- is
+    ``test_tc10_todays_real_corpus_shape_serves_insufficient_sample_with_caveats_and_null_
+    disclosure`` above, itself untouched by this rider and still exercised as-is."""
+    _plant_strategy_backtest(
+        journal_store, backtest_id="bt-1", dataset_id="ds-1",
+        candidate_net_rs=[1.0], null_net_rs=[-1.0],
+    )
+    _plant_strategy_backtest(
+        journal_store, backtest_id="bt-2", dataset_id="ds-1",
+        candidate_net_rs=[0.5], null_net_rs=[-0.5],
+    )
+    _plant_strategy_backtest(
+        journal_store, backtest_id="bt-3", dataset_id="ds-2",
+        candidate_net_rs=[2.0], null_net_rs=[-2.0],
+    )
+
+    default_pool = _pool_strategy_trades(journal_store)
+    explicit_none_pool = _pool_strategy_trades(journal_store, candidate=None)
+
+    assert explicit_none_pool["occurrences_pooled"] == default_pool["occurrences_pooled"] == 3
+    assert explicit_none_pool["informative_sessions"] == default_pool["informative_sessions"] == 2
+    assert (
+        set(explicit_none_pool["session_groups"]) == set(default_pool["session_groups"])
+        == {"ds-1", "ds-2"}
+    )
+    for cluster_key in default_pool["session_groups"]:
+        assert (
+            explicit_none_pool["session_groups"][cluster_key]
+            == default_pool["session_groups"][cluster_key]
+        )
+
+
 # === TC-14: referee_parameters()/referee_parameters_hash() -- the aggregator + Parameters
 # discipline counter-test ================================================================================
 
diff --git a/apps/backend/tests/test_referee_registry.py b/apps/backend/tests/test_referee_registry.py
index e063d3a..9eee4b2 100644
--- a/apps/backend/tests/test_referee_registry.py
+++ b/apps/backend/tests/test_referee_registry.py
@@ -871,7 +871,6 @@ def test_shortlist_s4_s5_s6_readiness_reflects_the_at_wall_context_resolve(
     assert by_id["S-4"]["n"] == 1 and by_id["S-4"]["n_sessions"] == 1
     assert by_id["S-5"]["n"] == 1 and by_id["S-5"]["n_sessions"] == 1
     assert by_id["S-6"]["n"] == 1 and by_id["S-6"]["n_sessions"] == 1
-    assert by_id["S-5"]["n"] == 1 and by_id["S-5"]["n_sessions"] == 1
 
 
 # === TC-9 / TC-10 (iter-8): the write path stays generic; discovery is boundary-gated on
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 4492f67..ce1cf23 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -43,9 +43,18 @@ import {
   triggerDeskScreenCompute,
   triggerDeskTopupCompute,
   triggerDeskUniverseFetch,
+  cancelRefereeEvaluate,
+  cancelRefereeNullsCompute,
+  fetchRefereeAdjudications,
+  fetchRefereeEvaluate,
+  fetchRefereeEvaluateRuns,
+  fetchRefereeNullRuns,
+  fetchRefereeNullsCompute,
   fetchRefereeRegistry,
   fetchRefereeShortlist,
   postRefereeRegistryHypothesis,
+  triggerRefereeEvaluate,
+  triggerRefereeNullsCompute,
 } from "@/lib/api";
 import type {
   DeskDeepBackfillComputeSnapshot,
@@ -109,7 +118,15 @@ import type {
   DeskTopupRun,
   DeskTopupRunMeta,
   DeskTopupRunsListResult,
+  RefereeAdjudicationEntry,
+  RefereeAdjudicationsResponse,
+  RefereeEvaluateRunsListResult,
+  RefereeEvaluationComputeSnapshot,
+  RefereeEvaluationRun,
   RefereeHypothesis,
+  RefereeNullComputeSnapshot,
+  RefereeNullRun,
+  RefereeNullRunsListResult,
   RefereeRegistryResponse,
   RefereeShortlistCandidate,
   RefereeShortlistResponse,
@@ -341,7 +358,9 @@ type DeskCollapsibleSection =
   | "screenComparison"
   | "provenance"
   | "playbookEvidence"
-  | "refereeRegistry";
+  | "refereeRegistry"
+  | "refereeAdjudications"
+  | "refereeRuns";
 // DESK-COLLAPSED-END
 
 const PRIMARY_BUTTON_CLASS =
@@ -4920,6 +4939,653 @@ function RefereeHypothesesTable({
   );
 }
 
+// goal-referee-iter-10 (J-09): the Referee Adjudications section -- the read-side adjudication fold
+// (verdict chips in the exact vocabulary + full provenance), rendered directly BELOW Referee
+// Registry. A single deferred GET, no compute manager, no poll (GET never computes, T-8) -- the
+// SAME "simplest state shape" pattern `PlaybookEvidenceSection` already uses. `hypothesesById` is a
+// plain lookup (never arithmetic) into the ALREADY-FETCHED registry response, cross-referencing
+// each entry's own `null_spec_id`/`test_spec_id` -- fields the adjudications response itself does
+// not carry (they are baked, unrecoverably, into its opaque `evaluation_basis` hash). Logged as a
+// T-1 interpretation: state/assumptions.md (goal-referee-iter-10, developer) -- "seed identity" is
+// rendered as the hypothesis_id itself, the one per-hypothesis component of the spec's pinned seed
+// recipe (`f"{REFEREE_SEED}:{hypothesis_id}:{purpose}..."`) that is not otherwise a numeric field
+// any endpoint serves.
+function RefereeAdjudicationEntryRow({
+  entry,
+  hypothesis,
+}: {
+  entry: RefereeAdjudicationEntry;
+  hypothesis: RefereeHypothesis | undefined;
+}) {
+  const snapshot = entry.snapshot;
+  return (
+    <tr
+      data-testid={`referee-adjudication-row-${entry.hypothesis_id}`}
+      className="border-b border-slate-900"
+    >
+      <td className="px-1.5 py-1.5 font-mono text-slate-300">{entry.hypothesis_id}</td>
+      <td className="px-1.5 py-1.5">
+        <span
+          data-testid={`referee-adjudication-verdict-${entry.hypothesis_id}`}
+          className={CHIP_CLASS}
+        >
+          {entry.verdict}
+        </span>
+      </td>
+      <td className="px-1.5 py-1.5 text-slate-400">
+        {entry.confirmatory_output_refused ? (
+          <span
+            data-testid={`referee-adjudication-refusal-${entry.hypothesis_id}`}
+            className="text-amber-200/70"
+          >
+            {entry.refusal_reason}
+          </span>
+        ) : snapshot ? (
+          <span className="text-slate-500">checkpointed {formatDateTimeET(snapshot.snapshot_at)}</span>
+        ) : (
+          <span className="font-mono text-slate-300">
+            {entry.live_coverage?.post_boundary_sessions ?? 0} /{" "}
+            {entry.live_coverage?.target_sessions ?? 0} sessions
+          </span>
+        )}
+      </td>
+      <td
+        className="px-1.5 py-1.5 text-slate-500"
+        data-testid={`referee-adjudication-provenance-${entry.hypothesis_id}`}
+      >
+        <div className="flex flex-col gap-0.5 font-mono text-[11px]">
+          <span>basis: {snapshot ? snapshot.evaluation_basis : "—"}</span>
+          <span>null spec: {hypothesis?.null_spec_id ?? "—"}</span>
+          <span>test spec: {hypothesis?.test_spec_id ?? "—"}</span>
+          <span>seed identity: {entry.hypothesis_id}</span>
+          <span>attestation: {snapshot ? (snapshot.attestation.passed ? "pass" : "fail") : "—"}</span>
+          <span>
+            BH:{" "}
+            {snapshot
+              ? `${snapshot.bh.k_star} / ${snapshot.bh.m} (q=${snapshot.bh.q})`
+              : "—"}
+          </span>
+        </div>
+      </td>
+      <td className="px-1.5 py-1.5 text-slate-500">
+        {snapshot && snapshot.fragility_triggers.length > 0
+          ? snapshot.fragility_triggers.join(", ")
+          : "—"}
+      </td>
+    </tr>
+  );
+}
+
+function RefereeAdjudicationsSection({
+  adjudicationsResult,
+  registryResult,
+}: {
+  adjudicationsResult: {
+    ok: boolean;
+    data: RefereeAdjudicationsResponse | null;
+    error?: string;
+  } | null;
+  registryResult: { ok: boolean; data: RefereeRegistryResponse | null; error?: string } | null;
+}) {
+  if (adjudicationsResult === null) {
+    return <LoadingPanel testid="referee-adjudications-loading" />;
+  }
+  if (!adjudicationsResult.ok || adjudicationsResult.data === null) {
+    return (
+      <UnavailablePanel
+        testid="referee-adjudications-unavailable"
+        message={adjudicationsResult.error ?? "The referee adjudications could not be loaded."}
+      />
+    );
+  }
+  const data = adjudicationsResult.data;
+  const hypothesesById = new Map(
+    registryResult?.ok && registryResult.data
+      ? registryResult.data.hypotheses.map((h) => [h.hypothesis_id, h] as const)
+      : [],
+  );
+  return (
+    <div data-testid="referee-adjudications-section">
+      <p className="mb-3 text-xs text-slate-500" data-testid="referee-adjudications-register">
+        {data.register}
+      </p>
+      {data.entries.length === 0 ? (
+        <EmptyState testid="referee-adjudications-empty" title="No hypotheses registered." />
+      ) : (
+        <div className="overflow-x-auto">
+          <table
+            data-testid="referee-adjudications-table"
+            className="w-full min-w-[980px] border-collapse text-xs"
+          >
+            <thead>
+              <tr className="border-b border-slate-800 text-[10px] uppercase tracking-wider text-slate-500">
+                <th className="px-1.5 py-1 text-left">Hypothesis</th>
+                <th className="px-1.5 py-1 text-left">Verdict</th>
+                <th className="px-1.5 py-1 text-left">Status</th>
+                <th className="px-1.5 py-1 text-left">Provenance</th>
+                <th className="px-1.5 py-1 text-left">Fragility triggers</th>
+              </tr>
+            </thead>
+            <tbody>
+              {data.entries.map((entry) => (
+                <RefereeAdjudicationEntryRow
+                  key={entry.hypothesis_id}
+                  entry={entry}
+                  hypothesis={hypothesesById.get(entry.hypothesis_id)}
+                />
+              ))}
+            </tbody>
+          </table>
+        </div>
+      )}
+      <IntegrityErrorsNote
+        errors={data.integrity_errors}
+        testid="referee-adjudications-integrity-errors"
+      />
+    </div>
+  );
+}
+
+// goal-referee-iter-10 (J-09): the Referee Runs section -- null-build + evaluation compute controls
+// with live progress + cancel, plus both durable run ledgers, rendered directly BELOW Referee
+// Adjudications (the era's THIRD and LAST Referee section). Both compute managers are single-flight
+// PER KEY (`null_spec_id` / `hypothesis_id`), never a page-wide singleton like every other desk
+// compute control -- so control/progress state here is keyed by `Record<key, ...>` rather than one
+// flat value per manager, and ONE shared `RefereeComputeControlState` shape (not four separate flat
+// maps) covers the trigger/cancel state both managers need identically.
+
+interface RefereeComputeControlState {
+  triggering: boolean;
+  triggerError: string | null;
+  cancelRequested: boolean;
+  cancelError: string | null;
+}
+
+const REFEREE_COMPUTE_CONTROL_IDLE: RefereeComputeControlState = {
+  triggering: false,
+  triggerError: null,
+  cancelRequested: false,
+  cancelError: null,
+};
+
+// The distinct null_spec_ids actually in play, read off the ALREADY-FETCHED registry's own
+// hypotheses (never a hand-typed constant list client-side -- a B-estimand hypothesis's
+// `null_spec_id` is honestly `null` and is excluded). Order is first-encountered in the registry's
+// OWN served hypothesis order (a `Set`'s iteration order is insertion order, never re-sorted --
+// this page's reorder guard permits exactly one sanctioned `.sort(`/`.reverse(` in the whole file,
+// already spent on `resolvedRange`'s own max-of-a-set idiom) -- deterministic given an unchanged
+// registry response, never a hand-rolled comparator.
+function distinctRefereeNullSpecIds(
+  registryResult: { ok: boolean; data: RefereeRegistryResponse | null } | null,
+): string[] {
+  if (!registryResult?.ok || !registryResult.data) return [];
+  const ids = new Set<string>();
+  for (const hyp of registryResult.data.hypotheses) {
+    if (hyp.null_spec_id !== null) ids.add(hyp.null_spec_id);
+  }
+  return Array.from(ids);
+}
+
+function RefereeNullBuildControl({
+  nullSpecId,
+  compute,
+  control,
+  onTrigger,
+  onCancel,
+}: {
+  nullSpecId: string;
+  compute: RefereeNullComputeSnapshot | undefined;
+  control: RefereeComputeControlState;
+  onTrigger: () => void;
+  onCancel: () => void;
+}) {
+  const isRunning = compute?.status === "running" || compute?.status === "cancelling";
+  return (
+    <div
+      data-testid={`referee-null-build-control-${nullSpecId}`}
+      className="flex flex-col items-start gap-1 rounded-md border border-slate-800 p-2"
+    >
+      <span className="font-mono text-[11px] text-slate-400">{nullSpecId}</span>
+      <button
+        type="button"
+        data-testid={`referee-null-build-trigger-${nullSpecId}`}
+        onClick={onTrigger}
+        disabled={control.triggering || isRunning}
+        className={PRIMARY_BUTTON_CLASS}
+      >
+        {isRunning ? "Building…" : "Build Null"}
+      </button>
+      {isRunning && (
+        <p
+          data-testid={`referee-null-build-progress-${nullSpecId}`}
+          className="text-xs text-amber-200/70"
+        >
+          <span
+            aria-hidden="true"
+            className="mr-1.5 inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-400 align-middle"
+          />
+          {fmt(compute?.done ?? 0, 0)} / {fmt(compute?.total ?? 0, 0)}
+        </p>
+      )}
+      {control.triggerError && (
+        <p
+          data-testid={`referee-null-build-trigger-error-${nullSpecId}`}
+          className="text-xs text-red-300"
+        >
+          {control.triggerError}
+        </p>
+      )}
+      {isRunning && (
+        <button
+          type="button"
+          data-testid={`referee-null-build-cancel-${nullSpecId}`}
+          onClick={onCancel}
+          disabled={control.cancelRequested}
+          className={CANCEL_BUTTON_CLASS}
+        >
+          {control.cancelRequested ? "Cancelling…" : "Cancel"}
+        </button>
+      )}
+      {control.cancelError && (
+        <p
+          data-testid={`referee-null-build-cancel-error-${nullSpecId}`}
+          className="text-xs text-red-300"
+        >
+          {control.cancelError}
+        </p>
+      )}
+    </div>
+  );
+}
+
+function RefereeNullBuildsBlock({
+  registryResult,
+  compute,
+  controls,
+  onTrigger,
+  onCancel,
+}: {
+  registryResult: { ok: boolean; data: RefereeRegistryResponse | null; error?: string } | null;
+  compute: Record<string, RefereeNullComputeSnapshot>;
+  controls: Record<string, RefereeComputeControlState>;
+  onTrigger: (nullSpecId: string) => void;
+  onCancel: (nullSpecId: string) => void;
+}) {
+  const nullSpecIds = distinctRefereeNullSpecIds(registryResult);
+  if (nullSpecIds.length === 0) {
+    return (
+      <EmptyState
+        testid="referee-null-build-controls-empty"
+        title="No hypotheses registered — nothing to build a null for yet."
+      />
+    );
+  }
+  return (
+    <div data-testid="referee-null-build-controls" className="flex flex-wrap gap-2">
+      {nullSpecIds.map((nullSpecId) => (
+        <RefereeNullBuildControl
+          key={nullSpecId}
+          nullSpecId={nullSpecId}
+          compute={compute[nullSpecId]}
+          control={controls[nullSpecId] ?? REFEREE_COMPUTE_CONTROL_IDLE}
+          onTrigger={() => onTrigger(nullSpecId)}
+          onCancel={() => onCancel(nullSpecId)}
+        />
+      ))}
+    </div>
+  );
+}
+
+function RefereeEvaluateControl({
+  hypothesisId,
+  compute,
+  control,
+  onTrigger,
+  onCancel,
+}: {
+  hypothesisId: string;
+  compute: RefereeEvaluationComputeSnapshot | undefined;
+  control: RefereeComputeControlState;
+  onTrigger: () => void;
+  onCancel: () => void;
+}) {
+  const isRunning = compute?.status === "running" || compute?.status === "cancelling";
+  return (
+    <div
+      data-testid={`referee-evaluate-control-${hypothesisId}`}
+      className="flex flex-col items-start gap-1 rounded-md border border-slate-800 p-2"
+    >
+      <span className="font-mono text-[11px] text-slate-400">{hypothesisId}</span>
+      <button
+        type="button"
+        data-testid={`referee-evaluate-trigger-${hypothesisId}`}
+        onClick={onTrigger}
+        disabled={control.triggering || isRunning}
+        className={PRIMARY_BUTTON_CLASS}
+      >
+        {isRunning ? "Evaluating…" : "Evaluate"}
+      </button>
+      {isRunning && (
+        <p
+          data-testid={`referee-evaluate-progress-${hypothesisId}`}
+          className="text-xs text-amber-200/70"
+        >
+          <span
+            aria-hidden="true"
+            className="mr-1.5 inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-400 align-middle"
+          />
+          {fmt(compute?.done ?? 0, 0)} / {fmt(compute?.total ?? 0, 0)}
+        </p>
+      )}
+      {control.triggerError && (
+        <p
+          data-testid={`referee-evaluate-trigger-error-${hypothesisId}`}
+          className="text-xs text-red-300"
+        >
+          {control.triggerError}
+        </p>
+      )}
... [diff_bound] apps/frontend/app/desk/page.tsx: 595 more diff lines omitted — Read the file for full detail
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 25eca23..1a283ad 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -41,8 +41,13 @@ import type {
   PnlLedger,
   ProfilesPayload,
   RecordBarSeriesResult,
+  RefereeAdjudicationsResponse,
+  RefereeEvaluateRunsListResult,
+  RefereeEvaluationComputeSnapshot,
   RefereeHypothesis,
   RefereeHypothesisRegistrationPayload,
+  RefereeNullComputeSnapshot,
+  RefereeNullRunsListResult,
   RefereeRegistryResponse,
   RefereeShortlistResponse,
   ResearchTaxonomy,
@@ -2141,3 +2146,232 @@ export async function postRefereeRegistryHypothesis(
     return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
   }
 }
+
+// --- Era 6 "The Referee" (goal-referee-iter-10, J-09) -- Referee Adjudications + Referee Runs, the
+// era's LAST two `/desk` sections. Every function below mirrors the established `{ok, data,
+// error?}`/compute-trigger-triplet shape every other function in this file already uses.
+
+// GET /research/desk/referee/adjudications -- the read-side adjudication fold, served VERBATIM,
+// beside the served REFEREE_REGISTER disclosure text.
+export async function fetchRefereeAdjudications(): Promise<{
+  ok: boolean;
+  data: RefereeAdjudicationsResponse | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/referee/adjudications`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as RefereeAdjudicationsResponse };
+    }
+    let error = "The referee adjudications could not be loaded.";
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
+// GET /research/desk/referee/nulls/runs -- the durable null-build run ledger, served VERBATIM.
+export async function fetchRefereeNullRuns(): Promise<{
+  ok: boolean;
+  data: RefereeNullRunsListResult | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/referee/nulls/runs`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as RefereeNullRunsListResult };
+    }
+    let error = "The referee null-build run history could not be loaded.";
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
+// GET /research/desk/referee/evaluate/runs -- the durable evaluation run ledger, served VERBATIM.
+export async function fetchRefereeEvaluateRuns(): Promise<{
+  ok: boolean;
+  data: RefereeEvaluateRunsListResult | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/referee/evaluate/runs`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as RefereeEvaluateRunsListResult };
+    }
+    let error = "The referee evaluation run history could not be loaded.";
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
+// POST /research/desk/referee/nulls/compute -- start (or, while one is already running for this
+// EXACT null_spec_id, observe UNCHANGED) the single-flight null-build job. Mirrors
+// `triggerDeskPlaybookBackscanCompute`'s exact shape; the backend's 422 (unknown null_spec_id)
+// `detail` is surfaced VERBATIM.
+export async function triggerRefereeNullsCompute(nullSpecId: string): Promise<{
+  ok: boolean;
+  data?: { started: boolean; compute: RefereeNullComputeSnapshot };
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/referee/nulls/compute`, {
+      method: "POST",
+      headers: { "Content-Type": "application/json" },
+      body: JSON.stringify({ null_spec_id: nullSpecId }),
+    });
+    if (res.ok) {
+      const data = await res.json();
+      return { ok: true, data };
+    }
+    let error = "The null build could not be started.";
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
+// GET /research/desk/referee/nulls/compute?null_spec_id= -- the named null-spec's compute job
+// current/last snapshot, served VERBATIM. Always a body (never null) -- "idle" before any compute
+// has ever run this process for this key.
+export async function fetchRefereeNullsCompute(nullSpecId: string): Promise<{
+  ok: boolean;
+  data: RefereeNullComputeSnapshot | null;
+}> {
+  try {
+    const res = await fetch(
+      `${API_BASE}/research/desk/referee/nulls/compute?null_spec_id=${encodeURIComponent(nullSpecId)}`,
+    );
+    if (!res.ok) return { ok: false, data: null };
+    const data = await res.json();
+    return { ok: true, data: (data as RefereeNullComputeSnapshot | null) ?? null };
+  } catch {
+    return { ok: false, data: null };
+  }
+}
+
+// POST /research/desk/referee/nulls/compute/cancel -- cancel the in-flight null build for this
+// EXACT null_spec_id. The backend's 409 (idle) `detail` is surfaced verbatim.
+export async function cancelRefereeNullsCompute(nullSpecId: string): Promise<{
+  ok: boolean;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/referee/nulls/compute/cancel`, {
+      method: "POST",
+      headers: { "Content-Type": "application/json" },
+      body: JSON.stringify({ null_spec_id: nullSpecId }),
+    });
+    if (res.ok) return { ok: true };
+    let error = "The null build could not be cancelled.";
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
+// POST /research/desk/referee/evaluate -- start (or, while one is already running for this EXACT
+// hypothesis_id, observe UNCHANGED) the single-flight evaluation job. 422s (no job started) on an
+// unknown hypothesis_id, surfaced verbatim.
+export async function triggerRefereeEvaluate(hypothesisId: string): Promise<{
+  ok: boolean;
+  data?: { started: boolean; compute: RefereeEvaluationComputeSnapshot };
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/referee/evaluate`, {
+      method: "POST",
+      headers: { "Content-Type": "application/json" },
+      body: JSON.stringify({ hypothesis_id: hypothesisId }),
+    });
+    if (res.ok) {
+      const data = await res.json();
+      return { ok: true, data };
+    }
+    let error = "The evaluation could not be started.";
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
+// GET /research/desk/referee/evaluate?hypothesis_id= -- the named hypothesis's evaluation-compute
+// job current/last snapshot, served VERBATIM. Always a body (never null).
+export async function fetchRefereeEvaluate(hypothesisId: string): Promise<{
+  ok: boolean;
+  data: RefereeEvaluationComputeSnapshot | null;
+}> {
+  try {
+    const res = await fetch(
+      `${API_BASE}/research/desk/referee/evaluate?hypothesis_id=${encodeURIComponent(hypothesisId)}`,
+    );
+    if (!res.ok) return { ok: false, data: null };
+    const data = await res.json();
+    return { ok: true, data: (data as RefereeEvaluationComputeSnapshot | null) ?? null };
+  } catch {
+    return { ok: false, data: null };
+  }
+}
+
+// POST /research/desk/referee/evaluate/cancel -- cancel the in-flight evaluation for this EXACT
+// hypothesis_id. The backend's 409 (idle) `detail` is surfaced verbatim.
+export async function cancelRefereeEvaluate(hypothesisId: string): Promise<{
+  ok: boolean;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/referee/evaluate/cancel`, {
+      method: "POST",
+      headers: { "Content-Type": "application/json" },
+      body: JSON.stringify({ hypothesis_id: hypothesisId }),
+    });
+    if (res.ok) return { ok: true };
+    let error = "The evaluation could not be cancelled.";
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
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 592a0ab..8fd875d 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -2259,3 +2259,142 @@ export interface RefereeHypothesisRegistrationPayload {
   target_sessions: number;
   min_occurrences: number;
 }
+
+// --- Era 6 "The Referee" (goal-referee-iter-10, J-09) -- Referee Adjudications + Referee Runs, the
+// era's LAST two `/desk` sections. Every field below is served VERBATIM by its owning backend fold
+// (referee_adjudicate.py's `adjudications_response()`, `RefereeNullComputeManager`/
+// `RefereeEvaluationComputeManager`, `RefereeNullRunStore`/`RefereeEvaluationRunStore`) -- no
+// client-side arithmetic or verdict derivation anywhere downstream
+// (test_desk_ui_guards.py's extended `_PRICE_ARITHMETIC_FIELDS` covers the numerics this
+// iteration's JSX actually reads).
+
+export interface RefereeBhFold {
+  q: number;
+  m: number;
+  k_star: number;
+  bh_pass: boolean;
+  by_adjusted_p: number;
+  by_pass: boolean;
+}
+
+// `expected`/`actual`/`tolerance` share one shape (referee_stats.py's `_ATTESTATION_EXPECTED`/
+// `_ATTESTATION_TOLERANCE`).
+export interface RefereeAttestationQuantities {
+  permutation_p: number;
+  permutation_enumeration: boolean;
+  ci_low: number;
+  ci_high: number;
+}
+
+export interface RefereeAttestation {
+  expected: RefereeAttestationQuantities;
+  actual: RefereeAttestationQuantities;
+  tolerance: RefereeAttestationQuantities;
+  stats_core_version: string;
+  passed: boolean;
+}
+
+// A hypothesis's ONE permanent, append-only confirmatory checkpoint -- present on an adjudication
+// entry only once that hypothesis has reached its checkpoint evaluation.
+export interface RefereeAdjudicationSnapshot {
+  snapshot_id: string;
+  hypothesis_id: string;
+  family_id: string;
+  checkpoint_evaluation_id: string;
+  snapshot_at: string;
+  bh: RefereeBhFold;
+  fragility_triggers: string[];
+  verdict: "no_evidence" | "fragile" | "corroborated";
+  evaluation_basis: string;
+  attestation: RefereeAttestation;
+}
+
+export type RefereeVerdict =
+  | "registered"
+  | "pending_forward_confirmation"
+  | "insufficient_sample"
+  | "fragile"
+  | "no_evidence"
+  | "corroborated"
+  | "basis_retired";
+
+// The live (pre-checkpoint) accrual fold -- present only when `snapshot` is `null`.
+export interface RefereeLiveCoverage {
+  post_boundary_sessions: number;
+  target_sessions: number;
+}
+
+export interface RefereeAdjudicationEntry {
+  hypothesis_id: string;
+  verdict: RefereeVerdict;
+  confirmatory_output_refused: boolean;
+  refusal_reason: string | null;
+  snapshot: RefereeAdjudicationSnapshot | null;
+  live_coverage: RefereeLiveCoverage | null;
+}
+
+// GET /research/desk/referee/adjudications -- the read-side adjudication fold, served verbatim,
+// beside the served REFEREE_REGISTER disclosure text (what a verdict does NOT mean).
+export interface RefereeAdjudicationsResponse {
+  entries: RefereeAdjudicationEntry[];
+  register: string;
+  integrity_errors: RefereeIntegrityError[];
+}
+
+// The process-scoped snapshot of ONE in-flight (or last-terminal) null-build / evaluation job --
+// mirrors `DeskPlaybookBackscanComputeSnapshot`'s `status`/`"idle"` shape. Keyed PER null_spec_id /
+// hypothesis_id in this page's own state (never a single page-wide singleton): both compute
+// managers are single-flight PER KEY, not process-global, unlike every other desk compute control.
+export interface RefereeNullComputeSnapshot {
+  id: string | null;
+  status: "idle" | "running" | "cancelling" | "done" | "error";
+  null_spec_id: string | null;
+  done: number;
+  total: number;
+  error: string | null;
+}
+
+export interface RefereeEvaluationComputeSnapshot {
+  id: string | null;
+  status: "idle" | "running" | "cancelling" | "done" | "error";
+  hypothesis_id: string | null;
+  done: number;
+  total: number;
+  error: string | null;
+}
+
+// One terminal null-build attempt from the durable, append-only, terminal-state-only run log.
+export interface RefereeNullRun {
+  run_id: string;
+  null_spec_id: string;
+  state: "completed" | "failed" | "cancelled";
+  started_at: string;
+  finished_at: string;
+  progress: { done: number; total: number };
+  error: string | null;
+}
+
+// GET /research/desk/referee/nulls/runs -- honest-empty-or-populated, HTTP 200 always, never 404.
+export interface RefereeNullRunsListResult {
+  runs: RefereeNullRun[];
+  latest: RefereeNullRun | null;
+  integrity_errors: RefereeIntegrityError[];
+}
+
+// One terminal evaluation attempt from the durable, append-only, terminal-state-only run log.
+export interface RefereeEvaluationRun {
+  run_id: string;
+  hypothesis_id: string;
+  state: "completed" | "failed" | "cancelled";
+  started_at: string;
+  finished_at: string;
+  progress: { done: number; total: number };
+  error: string | null;
+}
+
+// GET /research/desk/referee/evaluate/runs -- honest-empty-or-populated, HTTP 200 always, never 404.
+export interface RefereeEvaluateRunsListResult {
+  runs: RefereeEvaluationRun[];
+  latest: RefereeEvaluationRun | null;
+  integrity_errors: RefereeIntegrityError[];
+}
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-referee/state/assumptions.md | 49 ++++++++++++++++++++++++++
 runs/goal-session-referee/telemetry.jsonl      |  8 +++++
 runs/goal-session-referee/trace/trace.jsonl    |  2 ++
 3 files changed, 59 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
