# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 11. Shown in full: 11.

```diff
diff --git a/apps/backend/app/mcp/__init__.py b/apps/backend/app/mcp/__init__.py
index 40f5d21a..02553af6 100644
--- a/apps/backend/app/mcp/__init__.py
+++ b/apps/backend/app/mcp/__init__.py
@@ -22,7 +22,8 @@ Result contract (locked by ``tests/test_mcp_server.py``):
     ``desk_playbook_evidence`` at Era B2 J-09; ``desk_referee``/``desk_referee_registry`` at Era 6
     "The Referee" J-09; ``desk_micro_readiness``/``desk_scout``/``desk_walkforward``/``desk_vault``
     at Era "The Rapid Microscope" J-08, MCP contract v6 — 22 -> 26 tools; ``desk_graduation`` at
-    J-11, MCP contract v7 — 26 -> 27 tools); an allowlisted-but-UNKNOWN path (any unshipped
+    J-11, MCP contract v7 — 26 -> 27 tools; ``desk_micro_snapshots`` at J-12, MCP contract v8 —
+    27 -> 28 tools); an allowlisted-but-UNKNOWN path (any unshipped
     ``/research/*``) still surfaces the backend's honest 404 this way — never placeholder data.
   * backend unreachable — an explicit tool error naming the base URL and the failure
     (``BackendUnreachableError``); NEVER cached or fabricated data (no cache, no retry loop,
@@ -147,6 +148,13 @@ _STATIC_PATHS: dict[str, str] = {
     # snapshot/trial/fold/shard is ever built or recorded (never a 404). None exposes any
     # query-param variant -- all four routes take none.
     "desk_micro_readiness": "/research/desk/micro/readiness",
+    # `desk_micro_snapshots` (J-12, MCP contract v8 -- 27 -> 28 tools) is the IDENTICAL
+    # no-required-param shape, positioned immediately after `desk_micro_readiness` (the
+    # dependency-order sibling rule: readiness -> snapshots -> scout) and before `desk_scout`
+    # directly below. Proxies the observer's already-registered build-metadata endpoint (never a
+    # second endpoint, never a second computation path) -- an explicit HTTP 200 honest-empty
+    # payload before any snapshot is ever built (never a 404). No query-param variant.
+    "desk_micro_snapshots": "/research/desk/micro/snapshots",
     "desk_scout": "/research/desk/micro/scout",
     "desk_walkforward": "/research/desk/micro/walkforward",
     "desk_vault": "/research/desk/micro/vault",
@@ -440,6 +448,20 @@ TOOLS: tuple[types.Tool, ...] = (
         ),
         inputSchema=_object_schema({}),
     ),
+    types.Tool(
+        name="desk_micro_snapshots",
+        description=(
+            "Read-only proxy of GET /research/desk/micro/snapshots -- the micro observer's "
+            "build-metadata surface: per CURRENTLY VALID snapshot its identity tuple "
+            "(dataset_id/dataset_checksum/micro_algo_version/snapshot_format_version/"
+            "feature_source_hash/config_fingerprint/params_hash), quote_size_unit, row_count, "
+            "bytes_on_disk and built_utc, beside two disclosure counts -- withheld_excluded "
+            "(pool-derived, never a snapshot-file-derived count) and stale_excluded (a present "
+            "meta file whose identity no longer re-verifies) -- JSON verbatim. Never raw "
+            "per-event feature rows. Never 404/500 on zero built snapshots."
+        ),
+        inputSchema=_object_schema({}),
+    ),
     types.Tool(
         name="desk_scout",
         description=(
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index 03fa0e1d..9ffad11d 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -57,9 +57,9 @@ from .micro_readiness import (
 )
 from .micro_snapshots import (
     MicroSnapshotComputeManager,
-    list_snapshot_meta,
     read_run_log,
     resolve_micro_snapshots_dir,
+    snapshot_meta_report,
 )
 from .routes import get_bar_index, get_bar_store, get_dataset_store, get_registry, get_study_market_adapter
 from .scout import (
@@ -173,8 +173,15 @@ def get_micro_snapshots(
     -- for every CURRENTLY VALID (identity re-verified) snapshot; never raw per-event feature
     rows (the boundary note: an origin-fenced, event-level read is ``micro_accessor.py``'s
     exclusive door, J-05, not this route). Never 404/500 on zero built snapshots -- an honest
-    empty list, the desk router's established convention."""
-    return {"snapshots": list_snapshot_meta(snapshots_dir, dataset_store, CONFIG)}
+    empty list, the desk router's established convention.
+
+    goal-rapid-microscope-iter-33 (J-12): grows to ``{"snapshots": [...], "withheld_excluded":
+    int, "stale_excluded": int}`` -- existing ``snapshots`` key byte-identical, no second
+    computation path, no new endpoint. Both disclosure counts are ``snapshot_meta_report``'s own
+    (see that function's docstring): ``withheld_excluded`` is pool-derived, never a count of which
+    withheld ids happen to have a meta file on disk; ``stale_excluded`` counts a present-but-no-
+    longer-identity-matching meta file, never carrying the stale VALUE itself."""
+    return snapshot_meta_report(snapshots_dir, dataset_store, CONFIG)
 
 
 @router.post("/snapshots/compute")
diff --git a/apps/backend/app/research/micro_snapshots.py b/apps/backend/app/research/micro_snapshots.py
index 9917562e..fe1d3fb8 100644
--- a/apps/backend/app/research/micro_snapshots.py
+++ b/apps/backend/app/research/micro_snapshots.py
@@ -58,6 +58,7 @@ __all__ = [
     "read_snapshot_rows",
     "load_snapshot_meta",
     "list_snapshot_meta",
+    "snapshot_meta_report",
     "run_snapshot_build_and_record",
     "MicroSnapshotComputeManager",
     "append_run_log",
@@ -360,30 +361,68 @@ def load_snapshot_meta(
     return stored
 
 
+def snapshot_meta_report(root_dir: str, dataset_store: DatasetStore, config: Config) -> dict:
+    """The ONE walk this module's listing surface performs (goal-rapid-microscope-iter-33, J-12) --
+    ``list_snapshot_meta`` (below, existing callers, list-only) and ``GET /research/desk/micro/
+    snapshots`` (the disclosure-aware route) both read off THIS single enumeration, never two
+    divergent walks of the same directory. Returns ``{"snapshots": [...], "withheld_excluded":
+    int, "stale_excluded": int}``, sorted by ``dataset_id`` for deterministic ordering.
+
+    ``withheld_excluded`` is POOL-derived -- the SAME choke point (``_unresolved_pool_ids``) every
+    other corpus-wide enumerator in this module already shares (``withheld_dataset_ids_for_store``/
+    ``exclude_withheld``), counted over the store's FULL ``list()`` record set. It is deliberately
+    **NEVER** a count of which withheld ids happen to have a ``*.meta.json`` file present on disk:
+    a withheld shard's snapshot build never runs at all (``run_snapshot_build_and_record``'s own
+    filter), so "does a meta file exist for this withheld id" is never an honest question to ask --
+    answering it would leak sealed-pool build state (TC-7, spec section 7.5 point 6/point 3, r4/r3).
+
+    ``stale_excluded`` is computed AFTER the withheld filter, over the meta files actually present
+    on disk: a meta file whose id is withheld is silently skipped (as before -- iter-9 audit B1 --
+    it never entered the corpus this route serves at all, so it is neither a "current" row nor a
+    "stale" one, and is never counted twice). Every OTHER meta file counts as stale iff
+    ``load_snapshot_meta``'s identity re-verification misses (TR-7) -- "built, then invalidated" by
+    an algo/format/feature-source/fingerprint move, never "never built". The stale VALUE itself is
+    never carried anywhere, only its count."""
+    records, _errors = dataset_store.list()
+    # The one choke point `withheld_dataset_ids_for_store`/`exclude_withheld` already share --
+    # reused directly (never a second, divergent predicate, and never a second `dataset_store.
+    # list()` call: `records` is used AS GIVEN, the `exclude_withheld` precedent).
+    withheld = _unresolved_pool_ids(dataset_store, records)
+    withheld_excluded = sum(1 for record in records if record["id"] in withheld)
+
+    root = Path(root_dir)
+    snapshots: list[dict] = []
+    stale_excluded = 0
+    if root.exists():
+        for meta_file in sorted(root.glob("*.meta.json")):
+            dataset_id = meta_file.name[: -len(".meta.json")]
+            if dataset_id in withheld:
+                # Spec section 7.5 point 3 (r3), iter-9 audit B1: a withheld shard's meta carries
+                # its `dataset_id`, its RAW `dataset_checksum`, its exact `row_count` and
+                # `bytes_on_disk` -- the identity, counts and bytes withheld until exposure.
+                # Omitted here even if a snapshot file for it exists on disk (a shard sealed AFTER
+                # its snapshot was built), so the withholding is fail-closed rather than dependent
+                # on build order.
+                continue
+            meta = load_snapshot_meta(root_dir, dataset_store, dataset_id, config)
+            if meta is not None:
+                snapshots.append(meta)
+            else:
+                stale_excluded += 1
+    snapshots.sort(key=lambda m: m["dataset_id"])
+    return {"snapshots": snapshots, "withheld_excluded": withheld_excluded, "stale_excluded": stale_excluded}
+
+
 def list_snapshot_meta(root_dir: str, dataset_store: DatasetStore, config: Config) -> list[dict]:
     """Every CURRENTLY VALID (identity re-verified) snapshot's meta, sorted by ``dataset_id`` for
     deterministic ordering. A stale meta file (present but no longer identity-matching) is
     silently excluded -- exactly the honest "never serve stale" TR-7 discipline applied to the
-    listing surface, not merely the single-dataset loader."""
-    root = Path(root_dir)
-    if not root.exists():
-        return []
-    # Spec section 7.5 point 3 (r3), iter-9 audit B1: a withheld shard's meta carries its
-    # `dataset_id`, its RAW `dataset_checksum`, its exact `row_count` and `bytes_on_disk` -- the
-    # identity, counts and bytes withheld until exposure. Omitted here even if a snapshot file
-    # for it exists on disk (a shard sealed AFTER its snapshot was built), so the withholding is
-    # fail-closed rather than dependent on build order.
-    withheld = withheld_dataset_ids_for_store(dataset_store)
-    out: list[dict] = []
-    for meta_file in sorted(root.glob("*.meta.json")):
-        dataset_id = meta_file.name[: -len(".meta.json")]
-        if dataset_id in withheld:
-            continue
-        meta = load_snapshot_meta(root_dir, dataset_store, dataset_id, config)
-        if meta is not None:
-            out.append(meta)
-    out.sort(key=lambda m: m["dataset_id"])
-    return out
+    listing surface, not merely the single-dataset loader.
+
+    Delegates to ``snapshot_meta_report`` above (goal-rapid-microscope-iter-33, J-12) -- the SAME
+    single walk, list-only for this function's existing callers (none of which need the two
+    disclosure counts)."""
+    return snapshot_meta_report(root_dir, dataset_store, config)["snapshots"]
 
 
 # --- the run-and-record orchestration (reuse-or-build per dataset) -------------------------------
diff --git a/apps/backend/tests/test_desk_ui_guards.py b/apps/backend/tests/test_desk_ui_guards.py
index d3c2d5bf..9938732e 100644
--- a/apps/backend/tests/test_desk_ui_guards.py
+++ b/apps/backend/tests/test_desk_ui_guards.py
@@ -342,6 +342,16 @@ _PRICE_ARITHMETIC_FIELDS = (
     # (a serialization call, never arithmetic, the `screen_result`/raw `fold_results` precedent),
     # so no per-field entry is needed for those.
     r"|evaluation\.(?:n)"
+    # goal-rapid-microscope-iter-33 (J-12): the new Feature Snapshots section's own served
+    # numerics -- GET /research/desk/micro/snapshots read verbatim for the first time in the
+    # browser (registered since era baseline; zero UI/MCP readers before this iteration). Each
+    # snapshot row's own `row_count`/`bytes_on_disk` (`FeatureSnapshotsSection`'s `snapshot.`
+    # destructured field) and the route's own two disclosure counts (`report.withheld_excluded`/
+    # `report.stale_excluded`, the fetched response body's own local binding) join this list on
+    # the same footing as every other served numeric above -- no client-side byte-to-MB
+    # conversion, no withheld/stale share arithmetic, is ever legitimate here.
+    r"|snapshot\.(?:row_count|bytes_on_disk)"
+    r"|report\.(?:withheld_excluded|stale_excluded)"
 )
 _PRICE_ARITHMETIC_PATTERN = re.compile(
     rf"({_PRICE_ARITHMETIC_FIELDS})\s*[-+*/]|[-+*/]\s*({_PRICE_ARITHMETIC_FIELDS})"
@@ -397,6 +407,18 @@ def test_desk_page_price_arithmetic_guard_catches_referee_evidence_arithmetic():
     )
     assert _PRICE_ARITHMETIC_PATTERN.search(seeded_total) is not None
 
+
+def test_desk_page_price_arithmetic_guard_catches_feature_snapshots_arithmetic():
+    """goal-rapid-microscope-iter-33 (J-12) TC-5 counter-test: the widened guard also catches
+    arithmetic over the new Feature Snapshots numerics (GET /research/desk/micro/snapshots' first
+    UI reader), proving the widened pattern actually fails on injected client-side arithmetic --
+    not just that it passes on unmodified source."""
+    seeded_bytes = "const avgBytes = snapshot.bytes_on_disk / snapshot.row_count;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_bytes) is not None
+
+    seeded_share = "const share = report.withheld_excluded + report.stale_excluded;"
+    assert _PRICE_ARITHMETIC_PATTERN.search(seeded_share) is not None
+
     seeded_signals = (
         "const share = evidence.playbook_occurrence.signals_at_current_basis / "
         "evidence.playbook_occurrence.records;"
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index acbcc198..3c52d783 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -46,6 +46,8 @@ from app.research.desk_forward import FORWARD_REGISTER, ForwardStore, forward_pa
 from app.research.desk_playbook import PLAYBOOK_REGISTER, PlaybookStore, playbook_parameters
 from app.research.desk_screen import ScreenStore
 from app.research.desk_universe import UniverseStore
+from app.research.datasets import DatasetStore
+from app.research.micro_snapshots import resolve_micro_snapshots_dir, run_snapshot_build_and_record
 from app.research.referee_adjudicate import REFEREE_REGISTER
 from app.research.referee_null import REFEREE_NULL_TOD_SPEC_ID, REFEREE_TEST_PERM_SPEC_ID
 from app.research.referee_registry import REFEREE_MIN_OCCURRENCES, REFEREE_MIN_SESSIONS
@@ -83,10 +85,10 @@ BACKEND_DIR = Path(__file__).resolve().parents[1]
 # ``desk_playbook_evidence`` (Era B2 "The Playbook" J-09, the era's own MCP contract v4 -- 18 -> 20
 # tools), ``desk_referee``/``desk_referee_registry`` (Era 6 "The Referee" J-09, MCP contract v5 --
 # 20 -> 22 tools), ``desk_micro_readiness``/``desk_scout``/``desk_walkforward``/``desk_vault``
-# (Era "The Rapid Microscope" J-08, the era's own MCP contract v6 -- 22 -> 26 tools), and
-# ``desk_graduation`` (J-11, MCP contract v7 -- 26 -> 27 tools) are the newest additions, each
-# positioned right after its dependency-order sibling (the same store/registry+route+MCP shape,
-# mirrored end to end).
+# (Era "The Rapid Microscope" J-08, the era's own MCP contract v6 -- 22 -> 26 tools),
+# ``desk_graduation`` (J-11, MCP contract v7 -- 26 -> 27 tools), and ``desk_micro_snapshots``
+# (J-12, MCP contract v8 -- 27 -> 28 tools) are the newest additions, each positioned right after
+# its dependency-order sibling (the same store/registry+route+MCP shape, mirrored end to end).
 EXPECTED_TOOLS = (
     "tape_state",
     "tape_features",
@@ -107,6 +109,7 @@ EXPECTED_TOOLS = (
     "desk_referee",
     "desk_referee_registry",
     "desk_micro_readiness",
+    "desk_micro_snapshots",
     "desk_scout",
     "desk_walkforward",
     "desk_vault",
@@ -1009,6 +1012,58 @@ async def test_desk_micro_readiness_tool_byte_identical_on_a_populated_state(mcp
     assert result.content[0].text.encode("utf-8") == rest.content, "desk_micro_readiness not byte-identical"
 
 
+@pytest.mark.anyio
+async def test_desk_micro_snapshots_tool_byte_identical_on_the_honest_empty_state(mcp_env):
+    """J-12: before any snapshot has ever been built on this test backend, `desk_micro_snapshots`
+    proxies `GET /research/desk/micro/snapshots`'s explicit HTTP 200 honest-empty payload -- an
+    empty `snapshots` list beside both disclosure counts at zero -- never a 404."""
+    result = await call_tool("desk_micro_snapshots", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/micro/snapshots", timeout=5.0)
+    assert rest.status_code == 200
+    assert rest.json() == {"snapshots": [], "withheld_excluded": 0, "stale_excluded": 0}
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_micro_snapshots not byte-identical"
+
+
+@pytest.mark.anyio
+async def test_desk_micro_snapshots_tool_byte_identical_on_a_populated_state(mcp_env, backend_paths):
+    """J-12: seed ONE real snapshot directly through `run_snapshot_build_and_record()` -- the
+    module's own public build-and-persist path (the `test_micro_snapshots.py` precedent), NEVER a
+    live `POST /snapshots/compute` run -- after recording one real (keyless, synthetic
+    `reference`-source) dataset through the live backend's own public `POST /research/datasets`
+    route, the SAME call `test_desk_micro_readiness_tool_byte_identical_on_a_populated_state`
+    above already uses. Both write into the live backend's own env-scoped `TAPEOLOGY_DATASET_DIR`
+    and its resolved snapshots directory (a sibling of it, un-scoped by `backend_paths` --
+    `resolve_micro_snapshots_dir`'s own default), so the SEPARATE backend subprocess reads
+    exactly what this test just wrote on its next GET. Proves the tool's JSON is byte-identical
+    to its curl equivalent on a NON-EMPTY result."""
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
+    dataset_dir = Path(backend_paths["TAPEOLOGY_DATASET_DIR"])
+    dataset_store = DatasetStore(dataset_dir)
+    snapshots_dir = resolve_micro_snapshots_dir(str(dataset_dir))
+    run_snapshot_build_and_record(dataset_store, CONFIG, snapshots_dir)
+
+    result = await call_tool("desk_micro_snapshots", {})
+    rest = httpx.get(f"{mcp_env}/research/desk/micro/snapshots", timeout=15.0)
+    assert rest.status_code == 200
+    body = rest.json()
+    assert len(body["snapshots"]) >= 1, "the live list must be non-empty for this proof"
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk_micro_snapshots not byte-identical"
+
+
 @pytest.mark.anyio
 async def test_desk_scout_tool_byte_identical_on_the_honest_empty_state(mcp_env):
     """Before any trial has ever been ledgered, `desk_scout` proxies `GET /research/desk/micro/
@@ -1317,7 +1372,7 @@ async def test_tr2_the_new_mcp_tools_leak_nothing_about_a_sealed_shard(tmp_path,
             "get_endpoint": {"path": "/research/datasets"},
         }
 
-        assert len(TOOL_NAMES) == 27, "the 27-tool contract must hold for this sweep to be complete"
+        assert len(TOOL_NAMES) == 28, "the 28-tool contract must hold for this sweep to be complete"
         leaks: list[str] = []
         for name in TOOL_NAMES:
             result = await call_tool(name, args_for.get(name, {}))
@@ -1987,10 +2042,10 @@ async def test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool(mcp_
     assert result.content[0].text.encode("utf-8") == rest.content, "topup/runs not byte-identical"
     assert rest.json() == {"runs": [], "latest": None, "integrity_errors": []}
     # goal-rapid-microscope-iter-15: the total grew 22 -> 26 (desk_micro_readiness/desk_scout/
-    # desk_walkforward/desk_vault); iter-31 (J-11) grew it again, 26 -> 27 (desk_graduation) --
-    # this route's own no-new-tool claim is unaffected, so only the tracked total is re-derived
-    # here.
-    assert "desk_topup_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 27
+    # desk_walkforward/desk_vault); iter-31 (J-11) grew it again, 26 -> 27 (desk_graduation);
+    # iter-33 (J-12) grew it again, 27 -> 28 (desk_micro_snapshots) -- this route's own
+    # no-new-tool claim is unaffected, so only the tracked total is re-derived here.
+    assert "desk_topup_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 28
 
 
 @pytest.mark.anyio
@@ -2010,10 +2065,10 @@ async def test_get_endpoint_desk_screen_runs_byte_identical_with_no_new_tool(mcp
     assert result.content[0].text.encode("utf-8") == rest.content, "screen/runs not byte-identical"
     assert rest.json() == {"runs": [], "latest": None, "integrity_errors": []}
     # goal-rapid-microscope-iter-15: the total grew 22 -> 26 (desk_micro_readiness/desk_scout/
-    # desk_walkforward/desk_vault); iter-31 (J-11) grew it again, 26 -> 27 (desk_graduation) --
-    # this route's own no-new-tool claim is unaffected, so only the tracked total is re-derived
-    # here.
-    assert "desk_screen_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 27
+    # desk_walkforward/desk_vault); iter-31 (J-11) grew it again, 26 -> 27 (desk_graduation);
+    # iter-33 (J-12) grew it again, 27 -> 28 (desk_micro_snapshots) -- this route's own
+    # no-new-tool claim is unaffected, so only the tracked total is re-derived here.
+    assert "desk_screen_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 28
 
 
 @pytest.mark.anyio
diff --git a/apps/backend/tests/test_micro_snapshots.py b/apps/backend/tests/test_micro_snapshots.py
index 9419bbbf..b4410be4 100644
--- a/apps/backend/tests/test_micro_snapshots.py
+++ b/apps/backend/tests/test_micro_snapshots.py
@@ -21,9 +21,11 @@ persistent TEST-OWNED db, never the operator's."""
 
 from __future__ import annotations
 
+import json
 import threading
 import time
 from contextlib import contextmanager
+from pathlib import Path
 
 import pytest
 from fastapi.testclient import TestClient
@@ -368,7 +370,10 @@ def test_get_snapshots_is_an_honest_empty_list_on_a_fresh_store(client):
     c, _store, _dir, _manager = client
     resp = c.get("/research/desk/micro/snapshots")
     assert resp.status_code == 200
-    assert resp.json() == {"snapshots": []}
+    # goal-rapid-microscope-iter-33 (J-12): grows to include the two disclosure counts, both `0`
+    # on a fresh store with no vault ledger and nothing on disk -- existing `snapshots` key
+    # byte-identical.
+    assert resp.json() == {"snapshots": [], "withheld_excluded": 0, "stale_excluded": 0}
 
 
 def test_snapshots_route_lists_a_built_snapshot(client):
@@ -383,6 +388,52 @@ def test_snapshots_route_lists_a_built_snapshot(client):
     assert "row_count" in body["snapshots"][0] and "bytes_on_disk" in body["snapshots"][0]
     # never raw per-event rows (the boundary note) -- only metadata keys are served
     assert "deferred" not in body["snapshots"][0] and "cumulative_delta" not in body["snapshots"][0]
+    assert body["withheld_excluded"] == 0
+    assert body["stale_excluded"] == 0
+
+
+# --- goal-rapid-microscope-iter-33 (J-12): snapshot_meta_report's own two disclosure counts -------
+
+
+def test_snapshot_meta_report_counts_a_present_but_no_longer_identity_matching_meta_as_stale(tmp_path):
+    """TC-2/TR-7: a meta file present on disk whose stored identity no longer re-verifies (here,
+    a mutated `dataset_checksum`) is excluded from `snapshots`, never served as a row and never
+    carrying its stale VALUE anywhere -- counted ONLY in `stale_excluded`."""
+    store = DatasetStore(tmp_path / "datasets")
+    meta = _plant(store)
+    snapshots_dir = str(tmp_path / "snapshots")
+    ms.run_snapshot_build_and_record(store, CONFIG, snapshots_dir, [meta["id"]])
+
+    report = ms.snapshot_meta_report(snapshots_dir, store, CONFIG)
+    assert report == {"snapshots": [ms.load_snapshot_meta(snapshots_dir, store, meta["id"], CONFIG)], "withheld_excluded": 0, "stale_excluded": 0}
+
+    # Mutate the persisted meta's own identity so it no longer re-verifies against a fresh
+    # computation -- exactly what "built, then invalidated" looks like on disk (TR-7).
+    meta_path = Path(snapshots_dir) / f"{meta['id']}.meta.json"
+    stored = json.loads(meta_path.read_text())
+    stored["dataset_checksum"] = "0" * 64
+    meta_path.write_text(json.dumps(stored, sort_keys=True))
+
+    report = ms.snapshot_meta_report(snapshots_dir, store, CONFIG)
+    assert report["snapshots"] == []
+    assert report["withheld_excluded"] == 0
+    assert report["stale_excluded"] == 1
+    assert ms.list_snapshot_meta(snapshots_dir, store, CONFIG) == []  # the list-only wrapper agrees
+
+
+def test_snapshot_meta_report_withheld_excluded_is_pool_derived_over_the_full_registered_corpus(tmp_path, monkeypatch):
+    """TC-7: `withheld_excluded` counts the store's FULL unresolved-pool membership (via
+    `_unresolved_pool_ids`, the SAME choke point `exclude_withheld` shares), never a count of
+    which withheld ids happen to have a meta file present on disk -- proven here by a withheld
+    dataset for which NO snapshot was ever built (so a file-derived count would report 0)."""
+    store = DatasetStore(tmp_path / "datasets")
+    withheld_meta = _plant(store, symbol="WITHHELDSYM")
+
+    monkeypatch.setattr(
+        ms, "_unresolved_pool_ids", lambda dataset_store, records: frozenset({withheld_meta["id"]})
+    )
+    report = ms.snapshot_meta_report(str(tmp_path / "snapshots"), store, CONFIG)
+    assert report == {"snapshots": [], "withheld_excluded": 1, "stale_excluded": 0}
 
 
 def test_compute_route_triggers_a_build_and_reports_progress_to_done(client):
@@ -539,6 +590,15 @@ def test_tc12_real_corpus_listed_via_the_route(real_snapshots):
             assert resp.status_code == 200
             body = resp.json()
             assert len(body["snapshots"]) == 18
+            # goal-rapid-microscope-iter-33 (J-12): the two disclosure counts are present and
+            # honest non-negative ints. NOT asserted at a specific value here: this real `.data`
+            # store carries whatever vault universes the operator has actually registered across
+            # later eras (a real, evolving number, not this fixture's concern) -- the dedicated
+            # pool-derived-vs-file-derived proof (TC-7) lives in `test_vault.py` and
+            # `test_snapshot_meta_report_withheld_excluded_is_pool_derived_over_the_full_
+            # registered_corpus` below, both on hermetic throwaway stores.
+            assert isinstance(body["withheld_excluded"], int) and body["withheld_excluded"] >= 0
+            assert isinstance(body["stale_excluded"], int) and body["stale_excluded"] >= 0
     finally:
         app.dependency_overrides.pop(get_dataset_store, None)
         app.dependency_overrides.pop(get_micro_snapshots_dir, None)
diff --git a/apps/backend/tests/test_vault.py b/apps/backend/tests/test_vault.py
index 81cfdd97..2504b135 100644
--- a/apps/backend/tests/test_vault.py
+++ b/apps/backend/tests/test_vault.py
@@ -776,6 +776,10 @@ def test_tr2_no_registered_get_route_serves_or_derives_a_sealed_shards_identity(
         # goal-rapid-microscope-iter-31 (J-11): `desk_graduation`'s own REST route -- confirmed
         # covered by this SAME structural sweep (never a second, route-by-route sweep of its own).
         assert swept["/research/desk/micro/graduation"] == 200
+        # goal-rapid-microscope-iter-33 (J-12): `desk_micro_snapshots`'s own REST route (already
+        # registered since J-02, now carrying two new disclosure fields) -- confirmed covered by
+        # this SAME structural sweep too.
+        assert swept["/research/desk/micro/snapshots"] == 200
         assert swept["/research/datasets/{dataset_id}"] == 403  # the sealed id, refused
 
         # --- the join attack, EXECUTED (not merely asserted absent) -------------------------
@@ -889,6 +893,50 @@ def test_tr2_holds_after_the_operator_runs_every_micro_compute_act(tmp_path, mon
         assert swept["/research/desk/micro/scout"] == 200
 
 
+def test_tc7_micro_snapshots_withheld_excluded_is_pool_derived_not_snapshot_file_derived(tmp_path, monkeypatch):
+    """TC-7 (goal-rapid-microscope-iter-33, J-12; spec section 7.5 point 6, r4): `GET
+    /research/desk/micro/snapshots`'s `withheld_excluded` must be POOL-derived (through
+    `micro_snapshots`'s shared `_unresolved_pool_ids` choke point -- the SAME one
+    `withheld_dataset_ids_for_store`/`exclude_withheld` already share), never a count of which
+    withheld ids happen to have a `*.meta.json` file present on disk. A withheld shard's snapshot
+    build NEVER RUNS at all (`run_snapshot_build_and_record`'s own filter), so a snapshot-file-
+    derived implementation would ALWAYS report `0` for a withheld dataset that has, correctly,
+    never had a snapshot built for it -- silently under-disclosing the pool and leaking sealed-
+    pool build state by omission.
+
+    This test registers a universe whose RULE matches one real dataset's own (symbol,
+    session_date) -- never sealing it, never building any snapshot at all (the rule-membership
+    withholding case, spec section 7.5 point 7/r5, exercised without any vault shard-ledger row)
+    -- and asserts the served count is `1` while the snapshots directory stays entirely empty
+    throughout, non-vacuously proving the count comes from the POOL predicate, not from counting
+    meta files on disk."""
+    _scope_everything_to(tmp_path, monkeypatch)
+    store = _combined_fixture_store(tmp_path)
+    withheld_meta = _record_distinctive_dataset(store)
+
+    universe_ledger = vault.universe_ledger_for_dataset_dir(str(tmp_path / "datasets"))
+    vault.register_universe(
+        universe_ledger,
+        universe_id="tc7-pool-only-universe",
+        symbol_rule=[_SWEEP_SYMBOL],
+        date_rule=["2031-03-17"],  # the ET calendar date of _SWEEP_WINDOW_START (EDT, UTC-4)
+        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_SECRET),
+        registered_at="2020-01-01T00:00:00.000000Z",  # well before the dataset's real created_utc
+    )
+
+    with TestClient(app) as client:
+        body = client.get("/research/desk/micro/snapshots").json()
+        assert body["snapshots"] == [], (
+            "no snapshot was ever built for anything -- a file-derived count would report 0 here"
+        )
+        assert body["withheld_excluded"] == 1, (
+            "withheld_excluded did not count the rule-matched pool member -- it is snapshot-file-"
+            "derived, not pool-derived (TC-7)"
+        )
+        assert body["stale_excluded"] == 0
+        assert withheld_meta["id"] not in {row.get("dataset_id") for row in body["snapshots"]}
+
+
 def test_tr2_the_mcp_surface_is_closed_structurally_not_route_by_route(tmp_path, monkeypatch):
     """Spec section 7.5's "TR-2 sweeps every registered route, closing the ``get_endpoint`` path
     STRUCTURALLY". The MCP server is a byte-identical GET proxy that imports nothing from ``app``
@@ -904,6 +952,10 @@ def test_tr2_the_mcp_surface_is_closed_structurally_not_route_by_route(tmp_path,
     # a direct, non-vacuous proof the new tool is actually present in this set (not merely implied
     # by the subset assertion below, which would still pass if the entry were silently missing).
     assert "/research/desk/micro/graduation" in research_tool_paths
+    # goal-rapid-microscope-iter-33 (J-12): `desk_micro_snapshots` is now wired into
+    # `_STATIC_PATHS` too -- the SAME direct, non-vacuous proof, now that the route it proxies
+    # carries two new disclosure fields.
+    assert "/research/desk/micro/snapshots" in research_tool_paths
     assert research_tool_paths <= swept
 
     reachable = {p for p in swept if p.startswith(ALLOWED_GET_PREFIXES) and "{" not in p}
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 86a96abd..1ef47e21 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -63,6 +63,8 @@ import {
   fetchDeskScoutCompute,
   fetchDeskScoutRuns,
   fetchDeskGraduation,
+  fetchDeskMicroSnapshots,
+  fetchDeskMicroSnapshotsRuns,
   fetchDeskVault,
   fetchDeskWalkforward,
   fetchDeskWalkforwardCompute,
@@ -84,6 +86,8 @@ import type {
   DeskForwardRunsListResult,
   DeskForwardTouch,
   DeskGraduationResponse,
+  DeskMicroSnapshotRunsResponse,
+  DeskMicroSnapshotsResponse,
   DeskPlaybookAbsence,
   DeskPlaybookBackscanComputeSnapshot,
   DeskPlaybookBackscanOutcomeCounts,
@@ -392,7 +396,8 @@ type DeskCollapsibleSection =
   | "scoutLedger"
   | "walkForward"
   | "validationVault"
-  | "graduation";
+  | "graduation"
+  | "featureSnapshots";
 // DESK-COLLAPSED-END
 
 const PRIMARY_BUTTON_CLASS =
@@ -7135,6 +7140,178 @@ function GraduationSection({
   );
 }
 
+// goal-rapid-microscope-iter-33 (J-12): the Feature Snapshots section -- the observer's build
+// truth, rendered directly BELOW Graduation (T-11: a new `micro-snapshots-*` testid family, no
+// shipped testid/heading string reused). Read-only: no build button, no POST -- `/snapshots/
+// compute` stays UI-unreachable (T-8; a snapshot build is a heavy operator act, manager/CLI-
+// driven). Renders `GET /research/desk/micro/snapshots` verbatim: per snapshot its full
+// seven-component identity tuple, quote_size_unit, row_count, bytes_on_disk, built_utc, plus the
+// route's own `withheld_excluded`/`stale_excluded` disclosure counts -- no client-side aggregate,
+// derived count, re-ordering, or recomputation of any served value (guarded by
+// `_PRICE_ARITHMETIC_FIELDS` below) -- beside `GET .../snapshots/runs`' build-run history,
+// newest-first, exactly as served (never re-sorted client-side).
+function FeatureSnapshotsSection({
+  snapshotsResult,
+  runsResult,
+}: {
+  snapshotsResult: { ok: boolean; data: DeskMicroSnapshotsResponse | null; error?: string } | null;
+  runsResult: { ok: boolean; data: DeskMicroSnapshotRunsResponse | null; error?: string } | null;
+}) {
+  if (snapshotsResult === null) {
+    return (
+      <div data-testid="micro-snapshots-section">
+        <LoadingPanel testid="micro-snapshots-loading" />
+      </div>
+    );
+  }
+  if (!snapshotsResult.ok || snapshotsResult.data === null) {
+    return (
+      <div data-testid="micro-snapshots-section">
+        <UnavailablePanel
+          testid="micro-snapshots-unavailable"
+          message={snapshotsResult.error ?? "The feature snapshots could not be loaded."}
+        />
+      </div>
+    );
+  }
+  const report = snapshotsResult.data;
+  return (
+    <div data-testid="micro-snapshots-section">
+      <p className="mb-3 text-xs text-slate-500">
+        Feature Snapshots (GET /research/desk/micro/snapshots, read verbatim; read-only -- a
+        snapshot build is an operator/CLI act, not a UI control): the micro observer&apos;s
+        build-metadata inventory -- every currently valid snapshot&apos;s identity, plus how many
+        pool members this listing withheld or dropped as stale.
+      </p>
+
+      <p data-testid="micro-snapshots-disclosure" className="mb-4 text-[11px] text-slate-500">
+        Withheld (excluded): <span className="font-mono text-slate-300">{report.withheld_excluded}</span>
+        {" · "}
+        Stale (excluded): <span className="font-mono text-slate-300">{report.stale_excluded}</span>
+      </p>
+
+      <div data-testid="micro-snapshots-block" className="mb-4">
+        <h4 className="mb-2 text-xs font-semibold text-slate-400">Snapshots</h4>
+        {report.snapshots.length === 0 ? (
+          <EmptyState testid="micro-snapshots-empty" title="No feature snapshots built yet." />
+        ) : (
+          <div className="overflow-x-auto">
+            <table
+              data-testid="micro-snapshots-table"
+              className="w-full min-w-[1400px] border-collapse text-xs"
+            >
+              <thead>
+                <tr className="border-b border-slate-800 text-left text-slate-500">
+                  <th className="px-1.5 py-1">Dataset</th>
+                  <th className="px-1.5 py-1">Snapshot format</th>
+                  <th className="px-1.5 py-1">Algo version</th>
+                  <th className="px-1.5 py-1">Config fingerprint</th>
+                  <th className="px-1.5 py-1">Feature source hash</th>
+                  <th className="px-1.5 py-1">Params hash</th>
+                  <th className="px-1.5 py-1">Quote size unit</th>
+                  <th className="px-1.5 py-1 text-right">Row count</th>
+                  <th className="px-1.5 py-1 text-right">Bytes on disk</th>
+                  <th className="px-1.5 py-1">Built at</th>
+                </tr>
+              </thead>
+              <tbody data-testid="micro-snapshots-rows">
+                {report.snapshots.map((snapshot) => (
+                  <tr key={snapshot.dataset_id} className="border-b border-slate-900">
+                    <td className="whitespace-nowrap px-1.5 py-1 font-mono text-[10px] text-slate-500">
+                      {snapshot.dataset_id}
+                    </td>
+                    <td className="px-1.5 py-1 font-mono text-slate-300">
+                      {snapshot.snapshot_format_version}
+                    </td>
+                    <td className="px-1.5 py-1 text-right font-mono text-slate-300">
+                      {snapshot.micro_algo_version}
+                    </td>
+                    <td className="whitespace-nowrap px-1.5 py-1 font-mono text-[10px] text-slate-500">
+                      {snapshot.config_fingerprint}
+                    </td>
+                    <td className="whitespace-nowrap px-1.5 py-1 font-mono text-[10px] text-slate-500">
+                      {snapshot.feature_source_hash}
+                    </td>
+                    <td className="whitespace-nowrap px-1.5 py-1 font-mono text-[10px] text-slate-500">
+                      {snapshot.params_hash}
+                    </td>
+                    <td className="px-1.5 py-1 text-slate-300">{snapshot.quote_size_unit}</td>
+                    <td className="px-1.5 py-1 text-right font-mono text-slate-300">
+                      {snapshot.row_count}
+                    </td>
+                    <td className="px-1.5 py-1 text-right font-mono text-slate-300">
+                      {snapshot.bytes_on_disk}
+                    </td>
+                    <td className="whitespace-nowrap px-1.5 py-1 font-mono text-slate-400">
+                      {formatDateTimeET(snapshot.built_utc, { seconds: false })}
+                    </td>
+                  </tr>
+                ))}
+              </tbody>
+            </table>
+          </div>
+        )}
+      </div>
+
+      <div data-testid="micro-snapshots-runs-block">
+        <h4 className="mb-2 text-xs font-semibold text-slate-400">Run History</h4>
+        {runsResult === null ? (
+          <LoadingPanel testid="micro-snapshots-runs-loading" />
+        ) : !runsResult.ok || runsResult.data === null ? (
+          <UnavailablePanel
+            testid="micro-snapshots-runs-unavailable"
+            message={runsResult.error ?? "The snapshot build-run history could not be loaded."}
+          />
+        ) : runsResult.data.runs.length === 0 ? (
+          <EmptyState testid="micro-snapshots-runs-empty" title="No snapshot build runs recorded yet." />
+        ) : (
+          <div className="overflow-x-auto">
+            <table
+              data-testid="micro-snapshots-runs-table"
+              className="w-full min-w-[820px] border-collapse text-xs"
+            >
+              <thead>
+                <tr className="border-b border-slate-800 text-left text-slate-500">
+                  <th className="px-1.5 py-1">Run</th>
+                  <th className="px-1.5 py-1">State</th>
+                  <th className="px-1.5 py-1">Started</th>
+                  <th className="px-1.5 py-1">Finished</th>
+                  <th className="px-1.5 py-1 text-right">Datasets</th>
+                  <th className="px-1.5 py-1 text-right">Withheld (excluded)</th>
+                  <th className="px-1.5 py-1">Error</th>
+                </tr>
+              </thead>
+              <tbody data-testid="micro-snapshots-run-rows">
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
+                      {run.datasets_done} / {run.datasets_total}
+                    </td>
+                    <td className="px-1.5 py-1 text-right font-mono text-slate-300">
+                      {run.withheld_excluded}
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
 // era-desk-iter-14 (J-10): a third compute control, wired exactly like `TopupComputeControl` — the
 // operation has no per-pair counters (it is a single classify-repair-verify walk, not a walk over
 // many pairs), so the running indicator shows the compute's own `progress.phase` label instead of
@@ -10036,6 +10213,21 @@ export default function DeskPage() {
     error?: string;
   } | null>(null);
 
+  // J-12: the Feature Snapshots section's own fetch-on-expand results -- the SAME `null` (not
+  // yet fetched) / `{ok, data, error}` shape every other Rapid Microscope section already uses,
+  // TWO independent slices (the snapshot listing plus its own build-run history) mirroring the
+  // Scout Ledger / Walk-Forward sections' own `<x>Result`/`<x>RunsResult` pair.
+  const [snapshotsResult, setSnapshotsResult] = useState<{
+    ok: boolean;
+    data: DeskMicroSnapshotsResponse | null;
+    error?: string;
+  } | null>(null);
+  const [snapshotsRunsResult, setSnapshotsRunsResult] = useState<{
+    ok: boolean;
+    data: DeskMicroSnapshotRunsResponse | null;
+    error?: string;
+  } | null>(null);
+
   // iter-14 audit (finding F1): the ONE stop flag both plain-async compute polls below observe.
   // This page's own contract for a plain `for(;;)` driver that awaits `refreshChainSleep` is the
   // `refreshChainStopRef` pattern further down ("Unmounting (a nav away mid-chain) stops the driver
@@ -10125,6 +10317,13 @@ export default function DeskPage() {
       // J-11: the Graduation section's own ONE fetch -- read-only, no compute/transition control
       // (graduation transitions are not a UI act, T-8).
       fetchDeskGraduation().then(setGraduationResult);
+    } else if (section === "featureSnapshots") {
+      // J-12: the Feature Snapshots section's own two reads -- read-only, no build control
+      // (/snapshots/compute stays UI-unreachable, T-8). Mirrors the scoutLedger/walkForward
+      // precedent immediately above: the listing plus its own durable run history, both issued
+      // on first expand.
+      fetchDeskMicroSnapshots().then(setSnapshotsResult);
+      fetchDeskMicroSnapshotsRuns().then(setSnapshotsRunsResult);
     }
   }
 
@@ -12438,6 +12637,20 @@ export default function DeskPage() {
             <GraduationSection graduationResult={graduationResult} />
           </CollapsibleSection>
         </section>
+
+        {/* goal-rapid-microscope-iter-33 (J-12): the Feature Snapshots section -- the era's own
+            sixth Rapid-Microscope section, rendered directly BELOW Graduation (T-11). READ-ONLY:
+            no build control (/snapshots/compute stays UI-unreachable, T-8). */}
+        <section aria-label="Feature Snapshots" className="mt-6">
+          <CollapsibleSection
+            id="featureSnapshots"
+            title="Feature Snapshots"
+            open={expandedSections.has("featureSnapshots")}
+            onToggle={() => toggleSection("featureSnapshots")}
+          >
+            <FeatureSnapshotsSection snapshotsResult={snapshotsResult} runsResult={snapshotsRunsResult} />
+          </CollapsibleSection>
+        </section>
       </main>
     </div>
   );
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index d846b271..d46f76a4 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -22,6 +22,8 @@ import type {
   DeskForwardReadResult,
   DeskForwardRunsListResult,
   DeskGraduationResponse,
+  DeskMicroSnapshotsResponse,
+  DeskMicroSnapshotRunsResponse,
   DeskPlaybookBackscanComputeSnapshot,
   DeskPlaybookBackscanPlan,
   DeskPlaybookBackscanRunsListResult,
@@ -2733,3 +2735,58 @@ export async function fetchDeskGraduation(): Promise<{
     return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
   }
 }
+
+// GET /research/desk/micro/snapshots — J-12, READ-ONLY: the observer's build-metadata surface,
+// registered since era baseline (J-02) but never read from the browser before this iteration.
+// Every CURRENTLY VALID snapshot's identity tuple plus quote_size_unit/row_count/bytes_on_disk/
+// built_utc, beside the route's own two disclosure counts (withheld_excluded, pool-derived;
+// stale_excluded, a present-but-no-longer-identity-matching meta file). Never 404/500 on zero
+// built snapshots — an honest empty list.
+export async function fetchDeskMicroSnapshots(): Promise<{
+  ok: boolean;
+  data: DeskMicroSnapshotsResponse | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/micro/snapshots`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskMicroSnapshotsResponse };
+    }
+    let error = "The feature snapshots could not be loaded.";
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
+// GET /research/desk/micro/snapshots/runs — the durable build-run history, newest first. Never
+// 404 on zero runs (an honest empty list). Mirrors fetchDeskScoutRuns/fetchDeskWalkforwardRuns
+// exactly.
+export async function fetchDeskMicroSnapshotsRuns(): Promise<{
+  ok: boolean;
+  data: DeskMicroSnapshotRunsResponse | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/micro/snapshots/runs`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskMicroSnapshotRunsResponse };
+    }
+    let error = "The snapshot build-run history could not be loaded.";
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
index e06330f6..3ad9eb50 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -2889,3 +2889,47 @@ export interface DeskGraduationResponse {
   message: string | null;
   chain_verification: MicroChainVerification;
 }
+
+// --- Feature Snapshots -- GET /research/desk/micro/snapshots (micro_snapshots.py
+// `snapshot_meta_report`), J-12: the observer's build-metadata surface -- registered since era
+// baseline (J-02), read verbatim for the first time in the browser this iteration. Every field is
+// the snapshot's own seven-component identity tuple (spec section 2.3) plus quote_size_unit/
+// row_count/bytes_on_disk/built_utc, beside two disclosure counts the SAME route now serves.
+export interface SnapshotMeta {
+  dataset_id: string;
+  dataset_checksum: string;
+  micro_algo_version: number;
+  snapshot_format_version: string;
+  feature_source_hash: string;
+  config_fingerprint: string;
+  params_hash: string;
+  quote_size_unit: string;
+  row_count: number;
+  bytes_on_disk: number;
+  built_utc: string;
+}
+
+export interface DeskMicroSnapshotsResponse {
+  snapshots: SnapshotMeta[];
+  // Pool-derived (never snapshot-file-derived, TC-7): how many unresolved-pool datasets this
+  // enumeration withheld.
+  withheld_excluded: number;
+  // A meta file present on disk whose identity re-verification failed (TR-7) -- "built, then
+  // invalidated", never "never built". Never carries the stale value itself, only its count.
+  stale_excluded: number;
+}
+
+export interface DeskMicroSnapshotRunLogEntry {
+  run_id: string;
+  state: "done" | "cancelled" | "failed";
+  started_utc: string;
+  finished_utc: string;
+  datasets_done: number;
+  datasets_total: number;
+  error: string | null;
+  withheld_excluded: number;
+}
+
+export interface DeskMicroSnapshotRunsResponse {
+  runs: DeskMicroSnapshotRunLogEntry[];
+}
diff --git a/docs/goal.md b/docs/goal.md
index 796ccd9b..af15015b 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -742,6 +742,90 @@ operator-attended act inside the era.
     asserting a Graduation-section string unique to it, and `state/golden-gaps` no longer
     lists `J-07`.
 
+- **J-12: The observer's build truth gets a surface — and its enumerator stops excluding silently**
+  - Steps:
+    1. Render a **Feature Snapshots** section on `/desk`, directly BELOW the shipped Graduation
+       section (T-11: below the shipped ones, reusing no shipped `data-testid` or heading
+       string — a new `micro-snapshots-*` testid family), reading `GET
+       /research/desk/micro/snapshots` and `GET /research/desk/micro/snapshots/runs` — the ONE
+       canonical owner (`micro_snapshots.py`; Product Shape Data Contract row "Feature snapshot
+       metadata + build progress/runs"), which today reaches no surface at all: zero UI readers
+       and no named MCP tool (measured by grep over `apps/frontend/` and
+       `tests/test_mcp_server.py`'s `EXPECTED_TOOLS`), so the whole build truth of Vision
+       pillar 2 / capability 2 — 18 snapshot meta files on disk — is curl-only. The section
+       renders the served payload verbatim: per snapshot its `dataset_id`,
+       `snapshot_format_version`, `micro_algo_version`, `config_fingerprint`,
+       `feature_source_hash`, `params_hash`, `quote_size_unit`, `row_count`, `bytes_on_disk`
+       and `built_utc`, plus the build-run history newest-first — with no client-side
+       aggregate, derived count, re-ordering, or recomputation of any served value, and the
+       served empty-state copy rendered verbatim (never a fabricated row) when the list or the
+       run log is empty. Read-only: no build button, no POST — the `/snapshots/compute` triple
+       stays UI-unreachable (T-8; a snapshot build is a heavy operator act and stays
+       manager/CLI-driven, and page-load GETs never compute).
+    2. Close the enumerator's two SILENT exclusions at the owner — additively, existing keys
+       byte-identical, no second computation path and no new endpoint. `GET
+       /research/desk/micro/snapshots` gains, beside `snapshots`: (a) `withheld_excluded` — how
+       many unresolved-pool datasets this enumeration withheld, computed by the SAME
+       `micro_snapshots` choke point every other corpus-wide enumerator already shares
+       (`withheld_dataset_ids_for_store` / `exclude_withheld`), matching the disclosure
+       convention `GET /research/datasets` (`sealed_withheld`) and `GET
+       /research/desk/micro/snapshots/compute` (`withheld_excluded`) already keep, and NEVER a
+       number derived from which withheld shards happen to have a snapshot file (that would
+       leak sealed-pool build state); and (b) `stale_excluded` — how many stored snapshot metas
+       failed load-time identity re-verification and were therefore dropped, which today is
+       invisible: the listing can serve `[]` with 18 meta files on disk and no explanation,
+       so an operator cannot tell "never built" from "built, then invalidated by an algo /
+       format / feature-source / fingerprint move". Both counts are computed AFTER the withheld
+       filter; `stale_excluded` never carries a stale VALUE, only its count.
+    3. Add `desk_micro_snapshots` as a byte-identical GET proxy of that route, positioned
+       immediately after `desk_micro_readiness` (the dependency-order sibling rule: readiness →
+       snapshots → scout), bumping the MCP contract to **v8 (27 → 28 tools)** and growing
+       `tests/test_mcp_server.py`'s `EXPECTED_TOOLS` to the 28-tuple in the same commit (guard
+       tests are EXTENDED, never edited). Extend `tests/test_desk_ui_guards.py`'s
+       `_PRICE_ARITHMETIC_FIELDS` with every served snapshot numeric plus its seeded
+       counter-test, and run the existing TR-2 join-resistance/inference sweep over the new
+       tool, the two new counts, and the new section.
+    4. Clean rebuild (`rm -rf apps/frontend/.next`, rebuild, restart — T-9), browser pass via
+       the store-scoped rig, element-capture of the new section (T-10) against the real store
+       AND against a fixture-scoped rig carrying at least one valid snapshot, one stale meta,
+       and one withheld pool member.
+    5. Extend (never weaken) **J-02**'s stored golden replay script with an additional assertion
+       on a statically rendered Feature-Snapshots string unique to it — the era-5 lesson: assert
+       the SSR'd section shell, never async-loaded row or `<option>` text — and let that element
+       capture also serve as J-02's owed element close-up.
+  - Acceptance: `GET /research/desk/micro/snapshots` remains the single owner of every snapshot
+    value — no second computation path, no new endpoint, no Data Contract row added, existing
+    keys byte-identical with only `withheld_excluded` and `stale_excluded` added — and the
+    `/desk` Feature Snapshots section renders that payload verbatim: against the real store it
+    shows the served list (or the served empty state) beside both disclosure counts and the
+    build-run history, with an element screenshot on record (no screenshot ⇒ `unknown`, never
+    `passing`); against the fixture-scoped rig a valid snapshot renders every served identity
+    field, a stale meta appears ONLY inside `stale_excluded` (never as a row, never as a stale
+    value), and a withheld pool member appears ONLY inside `withheld_excluded` (never by id,
+    symbol, session date, checksum, row count, or bytes) — with a counter-test proving
+    `withheld_excluded` is pool-derived rather than snapshot-file-derived, so no sealed-pool
+    build state is derivable from any served number. `desk_micro_snapshots` returns a body
+    byte-identical to its GET route; the 28-tuple contract test, the extended
+    `_PRICE_ARITHMETIC_FIELDS` counter-test, the TR-2 inference sweep over the new tool, counts
+    and section, and the replay-script static sweep all pass; the MCP surface stays read-only
+    and `/snapshots/compute` stays UI-unreachable. **No PnL number moves and none is invented:**
+    this journey registers no strategy, profile, or candidate, so in place of a PnL-ledger
+    append it proves the ledger untouched — `GET /research/pnl/ledger` and
+    `reports/pnl/pnl-history.md` byte-identical before and after, the champion pointer still
+    `v1`/`default`, both founding rows keeping their `n = 1 < 5` insufficient-sample labels
+    (fabricating a row for a surface change would breach "no fabricated data" and this era's
+    `pnl_scan` freeze). The `default` profile stays byte-identical — engine equivalence and the
+    golden feature trace pass byte-unmodified, `config_fingerprint` prints `08e471b10130e1e2`,
+    zero new `Config` fields (the two disclosures are payload fields, never config), every
+    `referee_*` module still matches the iteration-0 SHA-256 listing — every shipped `/`,
+    `/structure`, and `/desk` section renders as shipped, and the full backend suite passes at
+    a count ≥ the era-open baseline with 0 regressions. A **`[NEW]`-flagged demo-narrator
+    walkthrough** navigates `/desk` to the new Feature Snapshots section and shows the served
+    inventory, both disclosure counts, and the honest empty-state copy on screen, with that
+    step's own screenshot actually containing what the narration claims. Finally J-02's stored
+    golden asserts a Feature-Snapshots string unique to it and the full stored replay set
+    re-runs green.
+
 <!-- /AUTO:journeys -->
 
 ## Anti-goals
```

## Excluded-path stat (dependency/lockfile visibility)

 .../journey-scripts/J-02.json                      |  3 +-
 .../state/assumptions.md                           | 36 ++++++++++++++++++++
 .../state/blueprint.md                             | 38 ++++++++++++++++++++--
 .../state/enhancement-proposals.jsonl              |  2 ++
 .../state/proposer-result.json                     |  4 +--
 runs/goal-session-rapid-microscope/telemetry.jsonl | 16 +++++++++
 .../trace/trace.jsonl                              |  3 ++
 7 files changed, 97 insertions(+), 5 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
