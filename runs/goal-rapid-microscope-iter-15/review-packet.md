# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 5. Shown in full: 4.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_mcp_server.py` (47 lines not shown)

```diff
diff --git a/apps/backend/app/mcp/__init__.py b/apps/backend/app/mcp/__init__.py
index d6b6915..7125678 100644
--- a/apps/backend/app/mcp/__init__.py
+++ b/apps/backend/app/mcp/__init__.py
@@ -20,8 +20,10 @@ Result contract (locked by ``tests/test_mcp_server.py``):
     at era-4 J-04; ``tradability`` at era-5B J-01; ``setups`` at era-5B J-02; ``edge_report`` at
     era-5B J-04; ``desk_universe``/``desk_screen`` at era-desk J-06; ``desk_playbook``/
     ``desk_playbook_evidence`` at Era B2 J-09; ``desk_referee``/``desk_referee_registry`` at Era 6
-    "The Referee" J-09); an allowlisted-but-UNKNOWN path (any unshipped ``/research/*``) still
-    surfaces the backend's honest 404 this way — never placeholder data.
+    "The Referee" J-09; ``desk_micro_readiness``/``desk_scout``/``desk_walkforward``/``desk_vault``
+    at Era "The Rapid Microscope" J-08, MCP contract v6 — 22 -> 26 tools); an
+    allowlisted-but-UNKNOWN path (any unshipped ``/research/*``) still surfaces the backend's
+    honest 404 this way — never placeholder data.
   * backend unreachable — an explicit tool error naming the base URL and the failure
     (``BackendUnreachableError``); NEVER cached or fabricated data (no cache, no retry loop,
     no offline snapshot exists anywhere in this module).
@@ -138,6 +140,16 @@ _STATIC_PATHS: dict[str, str] = {
     # both routes take none.
     "desk_referee": "/research/desk/referee/adjudications",
     "desk_referee_registry": "/research/desk/referee/registry",
+    # `desk_micro_readiness`/`desk_scout`/`desk_walkforward`/`desk_vault` (Era "The Rapid
+    # Microscope" J-08, MCP contract v6 -- 22 -> 26 tools) are the IDENTICAL no-required-param
+    # shape as `desk_referee`/`desk_referee_registry` directly above: each proxies an endpoint
+    # that already serves an explicit HTTP 200 honest-empty/honest-live payload before any
+    # snapshot/trial/fold/shard is ever built or recorded (never a 404). None exposes any
+    # query-param variant -- all four routes take none.
+    "desk_micro_readiness": "/research/desk/micro/readiness",
+    "desk_scout": "/research/desk/micro/scout",
+    "desk_walkforward": "/research/desk/micro/walkforward",
+    "desk_vault": "/research/desk/micro/vault",
 }
 
 _TAPE_PATHS: dict[str, str] = {
@@ -407,6 +419,56 @@ TOOLS: tuple[types.Tool, ...] = (
         ),
         inputSchema=_object_schema({}),
     ),
+    types.Tool(
+        name="desk_micro_readiness",
+        description=(
+            "Read-only proxy of GET /research/desk/micro/readiness -- Era \"The Rapid Microscope\" "
+            "J-01's honest corpus-truth surface: per-shard symbol/date/feed/window/counts/"
+            "coverage-gaps/fallback_frac/checksum for every EXPOSED tick dataset, corpus totals "
+            "(distinct symbol-days, RTH minutes, session-equivalents) beside the referee's "
+            "file-count gate, per-pilot-study predeclared-floor met/unmet status, the joinable "
+            "playbook-signal corpus count, and the AGGREGATE-ONLY sealed-tranche totals (shard "
+            "count and distinct symbol-days per registered universe) -- JSON verbatim. A dataset "
+            "caught in an unresolved sealed pool carries no per-shard row and no identity anywhere "
+            "in this payload (spec section 7.5)."
+        ),
+        inputSchema=_object_schema({}),
+    ),
+    types.Tool(
+        name="desk_scout",
+        description=(
+            "Read-only proxy of GET /research/desk/micro/scout -- the Scout's exploratory "
+            "candidate ledger: every registered family's hash-chained, append-only trials, the "
+            "union-N denominator across every grid version ever run, each trial's closed-"
+            "vocabulary decision/kill reason and withheld_excluded count, beside the ledger's own "
+            "chain-verification verdict -- JSON verbatim. Never 404/500 on an empty ledger."
+        ),
+        inputSchema=_object_schema({}),
+    ),
+    types.Tool(
+        name="desk_walkforward",
+        description=(
+            "Read-only proxy of GET /research/desk/micro/walkforward -- the chronological "
+            "walk-forward engine's registered fold specs plus every sequence's per-fold results, "
+            "evidence-class labeling, temporal-stability/decay view, and sequence verdict, beside "
+            "the ledger's own chain-verification verdict -- JSON verbatim. Never 404/500 on an "
+            "empty ledger."
+        ),
+        inputSchema=_object_schema({}),
+    ),
+    types.Tool(
+        name="desk_vault",
+        description=(
+            "Read-only proxy of GET /research/desk/micro/vault -- the Validation Vault's current "
+            "state: every registered universe's rule disclosure (opaque/committed while any "
+            "member of its original pool is unresolved) and every shard's one-way lifecycle state "
+            "(sealed / assigned / exposed), beside both ledgers' own chain-verification verdicts "
+            "-- JSON verbatim. A sealed or not-yet-fully-released shard carries only the opaque "
+            "pre-exposure fields (shard_id, universe_id, size_bucket, checksum_commitment, "
+            "sealed_at, exposure_state) -- never a symbol, date, dataset id, or raw checksum."
+        ),
+        inputSchema=_object_schema({}),
+    ),
     types.Tool(
         name="pnl_ledger",
         description=(
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index caa10b2..1d5d21b 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -323,6 +323,16 @@ _PRICE_ARITHMETIC_FIELDS = (
     r"|compute\??\.progress\.(?:candidates_done|candidates_total|steps_done|steps_total)"
     r"|run\.(?:candidates_done|candidates_total|steps_done|steps_total|folds_evaluated)"
     r"|universe\.(?:symbol_rule_size|date_rule_size)"
+    # goal-rapid-microscope-iter-15 (J-08 half 2): the Microscope Readiness section's own TWO new
+    # aggregate-only served numerics -- the sealed-tranche totals (`sealed_tranche.shard_count`/
+    # `.symbol_days`, plus the per-universe breakdown's own `shard_count`/`symbol_days` counts,
+    # rendered off the destructured `[universeId, universeCounts]` entry) and the joinable-corpus
+    # `withheld_excluded` count. Both are ALREADY served by unchanged `micro_readiness.py` code --
+    # this iteration only adds a reader -- but per this file's own "every new served numeric joins
+    # this list" contract, they join it on the same footing as every other readiness field above.
+    r"|readiness\.sealed_tranche\.(?:shard_count|symbol_days)"
+    r"|universeCounts\.(?:shard_count|symbol_days)"
+    r"|readiness\.joinable_corpus\.(?:withheld_excluded)"
 )
 _PRICE_ARITHMETIC_PATTERN = re.compile(
     rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index 0bb7771..b8918bc 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -38,6 +38,9 @@ from app.mcp import (
     list_tools,
 )
 from app.providers.adapters.base import RawBar
+from app.research import vault
+from app.research import walkforward as wf
+from app.research import walkforward_ledger as wl
 from app.research.bars import BarSeriesAlreadyRegistered, BarStore
 from app.research.desk_forward import FORWARD_REGISTER, ForwardStore, forward_parameters
 from app.research.desk_playbook import PLAYBOOK_REGISTER, PlaybookStore, playbook_parameters
@@ -46,6 +49,25 @@ from app.research.desk_universe import UniverseStore
 from app.research.referee_adjudicate import REFEREE_REGISTER
 from app.research.referee_null import REFEREE_NULL_TOD_SPEC_ID, REFEREE_TEST_PERM_SPEC_ID
 from app.research.referee_registry import REFEREE_MIN_OCCURRENCES, REFEREE_MIN_SESSIONS
+from app.research.scout_ledger import ScoutLedger
+
+# Era "The Rapid Microscope" J-08's own opaque-pool-critical proof reuses, rather than
+# reimplements, `test_vault.py`'s own TR-2 fixture rig (its module docstring: "an ADVERSARIAL
+# JOIN-RESISTANCE SWEEP, not a whitelist review") -- the cross-test-file import precedent this
+# codebase already establishes (`test_desk_forward.py`'s `from test_copy_discipline import
+# find_violations`, `test_edge_report.py`'s `from test_backtests import _sim_events`, etc.).
+from test_vault import (
+    _FIXTURE_SECRET,
+    _SWEEP_QUOTES,
+    _SWEEP_SYMBOL,
+    _SWEEP_TRADES,
+    _SWEEP_WINDOW_END,
+    _SWEEP_WINDOW_START,
+    _combined_fixture_store,
+    _record_distinctive_dataset,
+    _scalars,
+    _scope_everything_to,
+)
 
 BACKEND_DIR = Path(__file__).resolve().parents[1]
 
@@ -54,9 +76,11 @@ BACKEND_DIR = Path(__file__).resolve().parents[1]
 # (era-5B J-02), ``desk_universe``/``desk_screen`` (era-desk J-06, MCP contract v3 -- 15 -> 17
 # tools), ``desk_forward`` (forward-test era, 17 -> 18 tools), ``desk_playbook``/
 # ``desk_playbook_evidence`` (Era B2 "The Playbook" J-09, the era's own MCP contract v4 -- 18 -> 20
-# tools), and ``desk_referee``/``desk_referee_registry`` (Era 6 "The Referee" J-09, MCP contract v5
-# -- 20 -> 22 tools) are the newest additions, each positioned right after its dependency-order
-# sibling (the same store/registry+route+MCP shape, mirrored end to end).
+# tools), ``desk_referee``/``desk_referee_registry`` (Era 6 "The Referee" J-09, MCP contract v5 --
+# 20 -> 22 tools), and ``desk_micro_readiness``/``desk_scout``/``desk_walkforward``/``desk_vault``
+# (Era "The Rapid Microscope" J-08, the era's own MCP contract v6 -- 22 -> 26 tools) are the newest
+# additions, each positioned right after its dependency-order sibling (the same store/registry+
+# route+MCP shape, mirrored end to end).
 EXPECTED_TOOLS = (
     "tape_state",
     "tape_features",
@@ -76,6 +100,10 @@ EXPECTED_TOOLS = (
     "desk_playbook_evidence",
     "desk_referee",
     "desk_referee_registry",
+    "desk_micro_readiness",
+    "desk_scout",
+    "desk_walkforward",
+    "desk_vault",
     "pnl_ledger",
     "taxonomy",
     "ui_route_map",
@@ -129,6 +157,9 @@ def backend_paths(tmp_path_factory):
         "TAPEOLOGY_DESK_SCREEN_DIR": str(tmp_path_factory.mktemp("mcp-desk-screen")),
         "TAPEOLOGY_DESK_FORWARD_DIR": str(tmp_path_factory.mktemp("mcp-desk-forward")),
         "TAPEOLOGY_DESK_PLAYBOOK_DIR": str(tmp_path_factory.mktemp("mcp-desk-playbook")),
+        "TAPEOLOGY_MICRO_SCOUT_DIR": str(tmp_path_factory.mktemp("mcp-micro-scout")),
+        "TAPEOLOGY_MICRO_WALKFORWARD_DIR": str(tmp_path_factory.mktemp("mcp-micro-walkforward")),
+        "TAPEOLOGY_MICRO_VAULT_DIR": str(tmp_path_factory.mktemp("mcp-micro-vault")),
     }
 
 
@@ -908,6 +939,342 @@ async def test_desk_referee_tool_byte_identical_with_a_corrupted_hypothesis_file
     )
 
 
+# --- Era "The Rapid Microscope" J-08: desk_micro_readiness / desk_scout / desk_walkforward /
+# desk_vault (MCP contract v6, 22 -> 26 tools; empty + populated + the MCP-surface TR-2 sweep) -----
+#
+# Placed HERE, deliberately BEFORE `test_datasets_tool_byte_identical_on_a_non_empty_live_list`
+# (the first test anywhere in this module that ever records a tick dataset) and before any test
+# that ever touches the scout/walkforward/vault stores (nothing before this point does) -- so every
+# "honest empty" assertion below is genuinely observed on a corpus with ZERO recorded datasets and
+# ZERO registered vault universes, the SAME file-order-matters discipline every other store in this
+# module already follows. Each populated-state test seeds its OWN env-scoped store directly through
+# its ledger's own public write path (`ScoutLedger.append_row`/`walkforward_ledger.
+# append_fold_result`/`vault.register_universe`+`vault.seal_shard`) -- NEVER a live
+# screen/fold-run/recorder compute, which the era's own evidence shows can run past 25 minutes
+# against the real corpus with zero completed candidates (goal.md's own performance trap).
+
+
+@pytest.mark.anyio
+async def test_desk_micro_readiness_tool_byte_identical_on_the_honest_empty_state(mcp_env):
+    """Before any tick dataset has ever been recorded and before any vault universe has ever been
+    registered on this test backend, `desk_micro_readiness` proxies `GET /research/desk/micro/
+    readiness`'s explicit HTTP 200 honest-empty payload -- an empty `shards` list, zero totals, and
+    an all-zero `sealed_tranche` -- never a 404 (the `desk_referee` convention this route itself
+    follows)."""
+    result = await call_tool("desk_micro_readiness", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/micro/readiness", timeout=15.0)
+    assert rest.status_code == 200
+    body = rest.json()
+    assert body["shards"] == []
+    assert body["totals"]["distinct_datasets"] == 0
+    assert body["sealed_tranche"] == {"shard_count": 0, "symbol_days": 0, "by_universe": {}}
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_micro_readiness not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_desk_micro_readiness_tool_byte_identical_on_a_populated_state(mcp_env):
+    """The `datasets`/`backtests`/`edge_report` J-02/J-03 precedent, applied to readiness: after
+    recording ONE real (keyless, synthetic `reference`-source) dataset through the live backend's
+    own public `POST /research/datasets` route -- the SAME call, same window, and same 200/409
+    idempotence tolerance every other "flip to live" test in this module already uses -- the tool's
+    JSON is still byte-identical to its curl equivalent, now over a NON-EMPTY `shards` list."""
+    recorded = httpx.post(
+        f"{mcp_env}/research/datasets",
+        json={
+            "source_kind": "reference",
+            "split": "train",
+            "start": "2026-06-09T17:00:00Z",
+            "end": "2026-06-09T17:00:30Z",
+        },
+        timeout=15.0,
+    )
+    assert recorded.status_code in (200, 409)  # 409 = already recorded by an earlier run/test
+    result = await call_tool("desk_micro_readiness", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/micro/readiness", timeout=15.0)
+    assert rest.status_code == 200
+    body = rest.json()
+    assert len(body["shards"]) >= 1, "the live result must be non-empty for this proof"
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_micro_readiness not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_desk_scout_tool_byte_identical_on_the_honest_empty_state(mcp_env):
+    """Before any trial has ever been ledgered, `desk_scout` proxies `GET /research/desk/micro/
+    scout`'s explicit HTTP 200 honest-empty payload -- an empty `families` list beside an `ok`
+    chain verification -- never a 404 (the `desk_referee` convention this route itself follows)."""
+    result = await call_tool("desk_scout", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/micro/scout", timeout=5.0)
+    assert rest.status_code == 200
+    assert rest.json() == {
+        "families": [],
+        "chain_verification": {"ok": True, "failed_at_row": None, "reason": None},
+    }
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_scout not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_desk_scout_tool_byte_identical_on_a_populated_state(mcp_env, backend_paths):
+    """Seed ONE real trial directly through `ScoutLedger.append_row()` -- the ledger's own public
+    write path, NEVER a live `POST /scout/compute` run (goal.md's own performance trap: a real
+    Scout screen against the real corpus has run past 25 minutes without producing one completed
+    candidate) -- into the live backend's env-scoped `TAPEOLOGY_MICRO_SCOUT_DIR`, then prove the
+    tool's JSON is byte-identical to its curl equivalent on a NON-EMPTY result."""
+    scout_dir = Path(backend_paths["TAPEOLOGY_MICRO_SCOUT_DIR"])
+    ScoutLedger(scout_dir).append_row(
+        {
+            "family_id": "mcp-test-family",
+            "family_root_id": "mcp-test-root",
+            "candidate_id": "mcp-test-candidate",
+            "decision": "killed_null",
+            "reason": "no_edge",
+        }
+    )
+    result = await call_tool("desk_scout", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/micro/scout", timeout=5.0)
+    assert rest.status_code == 200
+    body = rest.json()
+    assert len(body["families"]) >= 1, "the live list must be non-empty for this proof"
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_scout not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_desk_walkforward_tool_byte_identical_on_the_honest_empty_state(mcp_env):
+    """Before any fold has ever been ledgered, `desk_walkforward` proxies `GET /research/desk/
+    micro/walkforward`'s explicit HTTP 200 honest-empty payload -- empty `fold_specs`/`sequences`
+    beside an `ok` chain verification -- never a 404."""
+    result = await call_tool("desk_walkforward", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/micro/walkforward", timeout=5.0)
+    assert rest.status_code == 200
+    assert rest.json() == {
+        "fold_specs": [],
+        "sequences": [],
+        "chain_verification": {"ok": True, "failed_at_row": None, "reason": None},
+    }
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_walkforward not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_desk_walkforward_tool_byte_identical_on_a_populated_state(mcp_env, backend_paths):
+    """Seed ONE real fold result directly through `walkforward_ledger.append_fold_result()` -- the
+    ledger's own public write path (the `test_walkforward.py` row shape every fold-result test in
+    that file already uses), NEVER a live `POST /walkforward/compute` run -- into the live
+    backend's env-scoped `TAPEOLOGY_MICRO_WALKFORWARD_DIR`, then prove the tool's JSON is
+    byte-identical to its curl equivalent on a NON-EMPTY result."""
+    wf_dir = Path(backend_paths["TAPEOLOGY_MICRO_WALKFORWARD_DIR"])
+    wl.append_fold_result(
+        wl.WalkForwardLedger(str(wf_dir)),
+        {
+            "sequence_id": "mcp-test-sequence",
+            "corpus_id": "mcp-test-corpus",
+            "fold_index": 0,
+            "spec_hash": "mcp-test-spec-hash",
+            "status": wf.FOLD_STATUS_SUFFICIENT,
+            "evidence_class": wf.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC,
+            "process_label": wf.PROCESS_LABEL_RULE,
+            "effect": 0.01,
+            "sign": "positive",
+            "n": 10,
+            "n_sessions": 5,
+            "n_symbols": 3,
+            "missing": {},
+            "sidedness": "long",
+            "econ_floor": None,
+        },
+    )
+    result = await call_tool("desk_walkforward", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/micro/walkforward", timeout=5.0)
+    assert rest.status_code == 200
+    body = rest.json()
+    assert len(body["sequences"]) >= 1, "the live list must be non-empty for this proof"
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_walkforward not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_desk_vault_tool_byte_identical_on_the_honest_empty_state(mcp_env):
+    """Before any universe has ever been registered or any shard sealed, `desk_vault` proxies
+    `GET /research/desk/micro/vault`'s explicit HTTP 200 honest-empty payload -- empty
+    `universes`/`shards` beside both ledgers' own `ok` chain verifications -- never a 404."""
+    result = await call_tool("desk_vault", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/micro/vault", timeout=5.0)
+    assert rest.status_code == 200
+    assert rest.json() == {
+        "universes": [],
+        "shards": [],
+        "shard_ledger_chain_verification": {"ok": True, "failed_at_row": None, "reason": None},
+        "universe_ledger_chain_verification": {"ok": True, "failed_at_row": None, "reason": None},
+    }
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_vault not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_desk_vault_tool_byte_identical_on_a_populated_state(mcp_env, backend_paths):
+    """Seed ONE real registered universe AND one sealed shard directly through `vault.py`'s own
+    public write path (`register_universe`/`seal_shard` -- the `test_vault.py` TC-2/TC-6
+    precedent), NEVER through a live compute run, into the live backend's env-scoped
+    `TAPEOLOGY_MICRO_VAULT_DIR`, then prove the tool's JSON is byte-identical to its curl
+    equivalent on a NON-EMPTY result -- including a sealed shard's own opaque, aggregate-only
+    projection (the section 7.5 field whitelist), never its raw dataset id/checksum."""
+    vault_dir = Path(backend_paths["TAPEOLOGY_MICRO_VAULT_DIR"])
+    universe_ledger = vault.VaultUniverseLedger(str(vault_dir))
+    shard_ledger = vault.VaultShardLedger(str(vault_dir))
+    secret = b"mcp-test-vault-secret"
+    commitment = vault.commit_vault_secret(secret)
+    vault.register_universe(
+        universe_ledger,
+        universe_id="mcp-test-universe",
+        symbol_rule=["ZQXVLT-MCP"],
+        date_rule=["2026-06-09"],
+        vault_secret_commitment=commitment,
+    )
+    vault.seal_shard(
+        shard_ledger,
+        dataset_id="mcp-test-sealed-dataset",
+        universe_id="mcp-test-universe",
+        content_checksum="f" * 64,
+        event_count=42,
+        vault_secret=secret,
+    )
+    result = await call_tool("desk_vault", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/micro/vault", timeout=5.0)
+    assert rest.status_code == 200
+    body = rest.json()
+    assert len(body["universes"]) >= 1 and len(body["shards"]) >= 1, (
+        "the live lists must be non-empty for this proof"
+    )
+    assert set(body["shards"][0]) == {
+        "shard_id", "universe_id", "size_bucket", "checksum_commitment", "sealed_at", "exposure_state",
+    }
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_vault not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_tr2_the_new_mcp_tools_leak_nothing_about_a_sealed_shard(tmp_path, monkeypatch):
+    """The round's opaque-pool-critical proof (goal.md's own carried-forward reminder): closes the
+    gap `test_vault.py`'s own `test_tr2_the_mcp_surface_is_closed_structurally_not_route_by_route`
+    documents but does not itself execute -- the MCP server is a genuinely SEPARATE process the
+    existing REST-only `app.openapi()`-driven TR-2 sweep never actually calls over the wire.
+
+    Reuses `test_vault.py`'s own TR-2 fixture rig verbatim (`_combined_fixture_store`/
+    `_record_distinctive_dataset`/`_scope_everything_to`/`_scalars`) -- seals ONE globally-
+    distinctive shard under an UNREGISTERED universe id (the `test_vault.py` TR-2 precedent
+    itself: an unregistered `universe_id` can never be "whole-pool released", so the shard stays
+    withheld by construction) -- then spawns a DEDICATED, freshly hermetic backend subprocess over
+    that exact store (never the shared module-scoped `backend` fixture, whose dataset dir has
+    already accumulated many other tests' recordings by the time this test runs) and calls every
+    one of the 26 registered MCP tools against it, asserting the sealed shard's raw dataset id,
+    raw content checksum, symbol, window bounds, and exact trade/quote counts appear in ZERO tool
+    response bodies."""
+    _scope_everything_to(tmp_path, monkeypatch)
+    store = _combined_fixture_store(tmp_path)
+    sealed_meta = _record_distinctive_dataset(store)
+    assert len(store.list()[0]) == 3  # 2 public PG fixtures + the 1 distinctive shard, pre-seal
+
+    vault.seal_shard(
+        vault.shard_ledger_for_dataset_dir(str(tmp_path / "datasets")),
+        dataset_id=sealed_meta["id"],
+        universe_id="starter-tranche-v1",
+        content_checksum=sealed_meta["checksum"],
+        event_count=sealed_meta["event_counts"]["total"],
+        vault_secret=_FIXTURE_SECRET,
+    )
+
+    port = _free_port()
+    base = f"http://127.0.0.1:{port}"
+    env = os.environ.copy()  # carries every _scope_everything_to monkeypatch override forward
+    log_path = tmp_path / "tr2-mcp-uvicorn.log"
+    with open(log_path, "wb") as log:
+        proc = subprocess.Popen(
+            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
+            cwd=BACKEND_DIR, env=env, stdout=log, stderr=subprocess.STDOUT,
+        )
+    try:
+        deadline = time.time() + 20
+        while True:
+            try:
+                if httpx.get(f"{base}/health", timeout=1.0).status_code == 200:
+                    break
+            except httpx.HTTPError:
+                pass
+            if proc.poll() is not None or time.time() > deadline:
+                raise AssertionError(f"TR-2 MCP sweep backend failed to start:\n{log_path.read_text()[-2000:]}")
+            time.sleep(0.2)
+
+        monkeypatch.setenv("TAPEOLOGY_API_BASE", base)
+
+        forbidden_substrings = {
+            "dataset id": sealed_meta["id"],
+            "raw content checksum": sealed_meta["checksum"],
+            "symbol": _SWEEP_SYMBOL,
+            "window start": _SWEEP_WINDOW_START,
+            "window end": _SWEEP_WINDOW_END,
+        }
+        forbidden_scalars = {_SWEEP_TRADES, _SWEEP_QUOTES, sealed_meta["event_counts"]["total"]}
+        args_for = {
+            "tape_state": {"ticker": "SIM-BUYER"},
+            "tape_features": {"ticker": "SIM-BUYER"},
+            "tape_history": {"ticker": "SIM-BUYER"},
+            "levels": {"symbol": "PG", "as_of": "2026-06-09T21:00:00Z"},
+            "tradability": {"symbol": "PG", "as_of": "2026-06-09T21:00:00Z"},
+            "get_endpoint": {"path": "/research/datasets"},
+        }
+
+        assert len(TOOL_NAMES) == 26, "the 26-tool contract must hold for this sweep to be complete"
+        leaks: list[str] = []
+        for name in TOOL_NAMES:
+            result = await call_tool(name, args_for.get(name, {}))
+            for content_item in result.content:
+                for leak_kind, token in forbidden_substrings.items():
+                    if token in content_item.text:
+                        leaks.append(f"tool {name!r} serves the sealed shard's {leak_kind}")
+            try:
+                payload = json.loads(result.content[0].text)
+            except ValueError:
+                payload = None
+            if payload is not None:
+                hits = sorted(set(_scalars(payload, [])) & forbidden_scalars)
+                if hits:
+                    leaks.append(f"tool {name!r} serves the sealed shard's exact event counts {hits}")
+
+        assert leaks == [], "join-resistance breached over the MCP surface:\n  " + "\n  ".join(leaks)
+
+        # Counter-test: the sweep is not vacuous -- the sealed shard genuinely IS being withheld,
+        # its two public PG siblings are still fully served, and the tool proxies really did run
+        # against a live surface carrying real data (never a coincidentally-empty backend).
+        readiness = await call_tool("desk_micro_readiness", {})
+        readiness_body = json.loads(readiness.content[0].text)
+        assert readiness_body["sealed_tranche"]["shard_count"] >= 1
... [diff_bound] apps/backend/tests/test_mcp_server.py: 47 more diff lines omitted — Read the file for full detail
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index ee20e43..a708654 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -5966,6 +5966,82 @@ function MicroReadinessSection({
         </div>
       </div>
 
+      <div data-testid="micro-readiness-sealed-tranche-block" className="mb-4">
+        <h4 className="mb-2 text-xs font-semibold text-slate-400">Sealed Tranche (Aggregate Only)</h4>
+        <p className="mb-2 text-[11px] text-slate-500">
+          A recorded tranche is one opaque pool until its shards are exposed — aggregate counts
+          only, never a per-shard identity for a withheld shard.
+        </p>
+        <div className="overflow-x-auto">
+          <table
+            data-testid="micro-readiness-sealed-tranche-table"
+            className="w-full min-w-[420px] border-collapse text-xs"
+          >
+            <tbody>
+              <tr className="border-b border-slate-900">
+                <td className="px-1.5 py-1 text-slate-500">Sealed shard count</td>
+                <td
+                  data-testid="micro-readiness-sealed-shard-count"
+                  className="px-1.5 py-1 text-right font-mono text-slate-300"
+                >
+                  {readiness.sealed_tranche.shard_count}
+                </td>
+              </tr>
+              <tr className="border-b border-slate-900">
+                <td className="px-1.5 py-1 text-slate-500">Sealed symbol-days</td>
+                <td
+                  data-testid="micro-readiness-sealed-symbol-days"
+                  className="px-1.5 py-1 text-right font-mono text-slate-300"
+                >
+                  {readiness.sealed_tranche.symbol_days}
+                </td>
+              </tr>
+              <tr>
+                <td className="px-1.5 py-1 text-slate-500">Joinable corpus — withheld (excluded)</td>
+                <td
+                  data-testid="micro-readiness-withheld-excluded"
+                  className="px-1.5 py-1 text-right font-mono text-slate-300"
+                >
+                  {readiness.joinable_corpus.withheld_excluded}
+                </td>
+              </tr>
+            </tbody>
+          </table>
+        </div>
+
+        {Object.keys(readiness.sealed_tranche.by_universe).length === 0 ? (
+          <EmptyState testid="micro-readiness-sealed-by-universe-empty" title="No sealed shards recorded." />
+        ) : (
+          <div className="mt-2 overflow-x-auto">
+            <table
+              data-testid="micro-readiness-sealed-by-universe-table"
+              className="w-full min-w-[420px] border-collapse text-xs"
+            >
+              <thead>
+                <tr className="border-b border-slate-800 text-left text-slate-500">
+                  <th className="px-1.5 py-1">Universe</th>
+                  <th className="px-1.5 py-1 text-right">Shard count</th>
+                  <th className="px-1.5 py-1 text-right">Symbol-days</th>
+                </tr>
+              </thead>
+              <tbody data-testid="micro-readiness-sealed-by-universe-rows">
+                {Object.entries(readiness.sealed_tranche.by_universe).map(([universeId, universeCounts]) => (
+                  <tr key={universeId} className="border-b border-slate-900">
+                    <td className="px-1.5 py-1 text-slate-300">{universeId}</td>
+                    <td className="px-1.5 py-1 text-right font-mono text-slate-300">
+                      {universeCounts.shard_count}
+                    </td>
+                    <td className="px-1.5 py-1 text-right font-mono text-slate-300">
+                      {universeCounts.symbol_days}
+                    </td>
+                  </tr>
+                ))}
+              </tbody>
+            </table>
+          </div>
+        )}
+      </div>
+
       <div data-testid="micro-readiness-shards-block" className="mb-4">
         <h4 className="mb-2 text-xs font-semibold text-slate-400">Legacy Tick Shards</h4>
         {readiness.shards.length === 0 ? (
@@ -6198,7 +6274,7 @@ function ScoutLedgerSection({
                 <h4 className="mb-1 text-xs font-semibold text-slate-400">
                   {family.family_id}{" "}
                   <span className="font-normal text-slate-500">
-                    — {family.variants_tried} variants tried
+                    (root {family.family_root_id}) — {family.variants_tried} variants tried
                   </span>
                 </h4>
                 <div className="overflow-x-auto">
@@ -6441,7 +6517,7 @@ function WalkForwardSection({
           </div>
 
           {walkforwardResult.data.sequences.length === 0 ? (
-            <EmptyState testid="walk-forward-sequences-empty" title="No candidates ledgered." />
+            <EmptyState testid="walk-forward-sequences-empty" title="No walk-forward sequences run." />
           ) : (
             walkforwardResult.data.sequences.map((sequence) => {
               const verdict = sequence.sequence_verdict;
@@ -6458,7 +6534,7 @@ function WalkForwardSection({
                       {sequence.voided ? "voided" : "not voided"}
                     </span>
                   </h4>
-                  <p className="mb-1 text-[11px] text-slate-500">
+                  <div className="mb-1 text-[11px] text-slate-500">
                     Sequence verdict:{" "}
                     <span className="font-mono text-slate-300">
                       {verdict.refused ? `refused — ${verdict.reason}` : verdict.verdict}
@@ -6469,7 +6545,7 @@ function WalkForwardSection({
                         {JSON.stringify(verdict, null, 2)}
                       </pre>
                     </details>
-                  </p>
+                  </div>
                   <div className="overflow-x-auto">
                     <table className="w-full min-w-[760px] border-collapse text-xs">
                       <thead>
@@ -6606,14 +6682,20 @@ function ValidationVaultSection({
   vaultResult: { ok: boolean; data: DeskVaultResponse | null; error?: string } | null;
 }) {
   if (vaultResult === null) {
-    return <LoadingPanel testid="validation-vault-loading" />;
+    return (
+      <div data-testid="validation-vault-section">
+        <LoadingPanel testid="validation-vault-loading" />
+      </div>
+    );
   }
   if (!vaultResult.ok || vaultResult.data === null) {
     return (
-      <UnavailablePanel
-        testid="validation-vault-unavailable"
-        message={vaultResult.error ?? "The validation vault could not be loaded."}
-      />
+      <div data-testid="validation-vault-section">
+        <UnavailablePanel
+          testid="validation-vault-unavailable"
+          message={vaultResult.error ?? "The validation vault could not be loaded."}
+        />
+      </div>
     );
   }
   const vault = vaultResult.data;
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 990b082..c5866f9 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -2511,11 +2511,34 @@ export interface MicroReadinessStudyFloor {
   status: string;
 }
 
+// goal-rapid-microscope-iter-15 (J-08 half 2): `joinable_corpus` and `sealed_tranche` -- both
+// ALREADY served by `micro_readiness.py`'s unchanged `build_readiness` (transcribed verbatim from
+// its own return statement) -- were fetched but silently dropped by this interface until now. Only
+// `joinable_corpus.withheld_excluded` and every `sealed_tranche` field are rendered this iteration
+// (aggregate-only, spec section 7.5); `total`/`playbook_signal_count`/`band_touch_count`/
+// `by_setup_id`/`playbook_integrity_errors` stay typed/fetched but UNRENDERED (a future J-09 home).
+export interface MicroReadinessJoinableCorpus {
+  total: number;
+  playbook_signal_count: number;
+  band_touch_count: { status: string; count: number | null };
+  by_setup_id: Record<string, number>;
+  playbook_integrity_errors: { file: string; error: string }[];
+  withheld_excluded: number;
+}
+
+export interface MicroReadinessSealedTranche {
+  shard_count: number;
+  symbol_days: number;
+  by_universe: Record<string, { shard_count: number; symbol_days: number }>;
+}
+
 export interface MicroReadinessResponse {
   totals: MicroReadinessTotals;
   shards: MicroReadinessShard[];
   study_floors: MicroReadinessStudyFloor[];
   integrity_errors: { file: string; error: string }[];
+  joinable_corpus: MicroReadinessJoinableCorpus;
+  sealed_tranche: MicroReadinessSealedTranche;
 }
 
 // goal-rapid-microscope-iter-14 (J-08 half 1): Scout Ledger, Walk-Forward, and Validation Vault --
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-rapid-microscope/telemetry.jsonl   | 7 +++++++
 runs/goal-session-rapid-microscope/trace/trace.jsonl | 2 ++
 2 files changed, 9 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
