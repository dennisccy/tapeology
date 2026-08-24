# Iteration diff (bounded)

Files changed: 12. Shown in full: 12.

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
diff --git a/apps/backend/scripts/seed_micro_snapshots_iter33_disclosure_fixture.py b/apps/backend/scripts/seed_micro_snapshots_iter33_disclosure_fixture.py
new file mode 100644
index 00000000..03a4de14
--- /dev/null
+++ b/apps/backend/scripts/seed_micro_snapshots_iter33_disclosure_fixture.py
@@ -0,0 +1,201 @@
+"""Seed ONE valid snapshot, ONE stale meta, and ONE withheld pool member into a throwaway rig
+root, for J-12's browser-QA "fixture-scoped" capture (Era "The Rapid Microscope",
+goal-rapid-microscope-iter-33).
+
+**Why this exists.** TC-2 requires all three states on screen at once: a valid snapshot's every
+served identity field, a stale meta appearing nowhere as a row (only inside `stale_excluded`), and
+a withheld pool member appearing nowhere by id/symbol/session-date/checksum/row-count/bytes (only
+inside `withheld_excluded`). The real `.data` corpus cannot reliably discriminate all three at once
+on demand, so this script plants them the SAME way every other fixture in this ``scripts/``
+directory does: it plants REAL datasets through ``DatasetStore.record``'s own public write path
+and builds a REAL snapshot through ``micro_snapshots.run_snapshot_build_and_record`` -- never a
+hand-rolled JSON blob standing in for either.
+
+**The one deliberate exception, and why it is the only faithful way to build it.** A "stale" meta
+is, by definition, a meta file whose recorded identity no longer matches a FRESH computation
+(TR-7) -- normally produced by an algo/format/feature-source/fingerprint code move. A fixture
+script cannot change the running code's own bytes out from under itself and remain "the same
+production code", so after building the stale-symbol's snapshot for real, this script mutates
+ONLY that one persisted meta file's own `dataset_checksum` field directly (the SAME technique
+``tests/test_micro_snapshots.py::test_snapshot_meta_report_counts_a_present_but_no_longer_
+identity_matching_meta_as_stale`` uses at the unit level) -- never touching the rows file, never
+touching any OTHER snapshot's meta, and never inventing a value ``load_snapshot_meta`` would ever
+serve (a mismatched identity is a MISS, so nothing about this stale meta's stored fields is ever
+read back as current).
+
+**What this plants** (three distinct symbols, none colliding with any other seed script in this
+directory -- ``PGVAULT``/``PGQA``/``CALDR``/etc. per those scripts' own registries):
+
+* ``PGSNAPOK`` -- a real tiny tick dataset, snapshot built for real via
+  ``run_snapshot_build_and_record``. Stays a genuinely CURRENT, servable snapshot.
+* ``PGSNAPST`` -- a real tiny tick dataset, snapshot built for real, THEN its own persisted meta
+  file's ``dataset_checksum`` is overwritten with a value that can never match a fresh
+  recomputation -- an honest MISS on the very next read (never served as a row; counted only in
+  ``stale_excluded``).
+* ``PGSNAPWH`` -- a real tiny tick dataset that is NEVER snapshotted. A universe is registered
+  whose ``symbol_rule``/``date_rule`` matches its own ``(symbol, session_date)`` (the r5
+  rule-membership withholding case, ``vault.unresolved_pool_universe_by_dataset_id``'s own (b)
+  test), with a ``registered_at`` well before the dataset's real ``created_utc`` -- so it is
+  withheld from BOTH the snapshot listing AND any snapshot build, with no vault shard-ledger row
+  needed at all (mirrors ``tests/test_vault.py::test_tc7_micro_snapshots_withheld_excluded_is_
+  pool_derived_not_snapshot_file_derived``).
+
+**Never touches the real ``.data`` store.** Every path this script writes to is derived from the
+``root`` argument's own env-var scoping, exactly like every other seed script in this directory --
+run it against a fresh, never-seeded root via ``TAPEOLOGY_DATASET_DIR=<root>/datasets`` (the
+``seed_micro_vault_iter25_sealed_fixture.py`` convention).
+
+Usage:
+
+    TAPEOLOGY_DATASET_DIR=<root>/datasets \\
+        .venv/bin/python scripts/seed_micro_snapshots_iter33_disclosure_fixture.py ROOT
+"""
+
+from __future__ import annotations
+
+import json
+import sys
+from pathlib import Path
+
+_SCRIPTS_DIR = Path(__file__).resolve().parent
+sys.path.insert(0, str(_SCRIPTS_DIR))
+sys.path.insert(0, str(_SCRIPTS_DIR.parent))
+
+from app.config import CONFIG  # noqa: E402
+from app.providers.base import QuoteEvent, Side, TradeEvent  # noqa: E402
+from app.research import micro_snapshots as ms  # noqa: E402
+from app.research import vault  # noqa: E402
+from app.research.datasets import DatasetStore  # noqa: E402
+
+_SYMBOL_OK = "PGSNAPOK"
+_SYMBOL_STALE = "PGSNAPST"
+_SYMBOL_WITHHELD = "PGSNAPWH"
+
+_WINDOW_START_UTC = "2026-06-10T13:00:00Z"
+_WINDOW_END_UTC = "2026-06-10T13:01:00Z"
+# The ET calendar date of `_WINDOW_START_UTC` (EDT, UTC-4 in June) -- the withheld universe's own
+# `date_rule` must match this exactly for the rule-membership test to catch the dataset.
+_SESSION_DATE = "2026-06-10"
+
+_WITHHELD_UNIVERSE_ID = "iter33-qa-withheld-only-universe"
+# Well before ANY real `created_utc` this script's own `DatasetStore.record` call will ever stamp
+# (real wall-clock "now") -- the `created_utc >= registered_at` guard that makes rule-membership
+# withholding apply.
+_WITHHELD_UNIVERSE_REGISTERED_AT = "2020-01-01T00:00:00.000000Z"
+_FIXTURE_VAULT_SECRET = b"goal-rapid-microscope-iter33-qa-withheld-only-fixture-vault-secret"
+
+# A stale meta's mutated identity component must never coincidentally match a fresh
+# recomputation -- 64 zero hex digits is not a real sha256 digest of anything this script ever
+# computes.
+_STALE_DATASET_CHECKSUM = "0" * 64
+
+
+def _events_for_store(symbol: str) -> list:
+    """A tiny, REAL trade/quote sequence -- the ``seed_micro_vault_iter25_sealed_fixture.py``/
+    ``test_micro_observer.py`` ``_events_for_store`` shape, mirrored verbatim (never re-derived):
+    one quote, one aggressor-classified BUY, one SELL."""
+    return [
+        QuoteEvent(symbol, 0.0, 99.99, 100.02, 100, 100),
+        TradeEvent(symbol, 0.1, 100.03, 10, Side.UNKNOWN),  # >= ask -> engine classifies BUY
+        TradeEvent(symbol, 0.2, 99.99, 10, Side.UNKNOWN),  # <= bid -> engine classifies SELL
+    ]
+
+
+def _plant(dataset_store: DatasetStore, symbol: str, source_id: str) -> dict:
+    return dataset_store.record(
+        symbol=symbol, source="fixture", source_kind="fixture", source_id=source_id,
+        split="train", window_start_utc=_WINDOW_START_UTC, window_end_utc=_WINDOW_END_UTC,
+        data_feed="sip", epoch_anchor=0.0, events=_events_for_store(symbol),
+    )
+
+
+def plant_disclosure_fixture(root: Path) -> dict:
+    """Plants all three for real; returns the identifiers a caller (this module's own ``main``,
+    or a test) needs to assert against."""
+    dataset_dir = root / "datasets"
+    dataset_dir.mkdir(parents=True, exist_ok=True)
+    dataset_store = DatasetStore(dataset_dir)
+    snapshots_dir = ms.resolve_micro_snapshots_dir(str(dataset_dir))
+    vault_dir = vault.resolve_vault_dir(str(dataset_dir))
+
+    valid_meta = _plant(dataset_store, _SYMBOL_OK, "goal-rapid-microscope-iter33-qa-valid")
+    stale_meta = _plant(dataset_store, _SYMBOL_STALE, "goal-rapid-microscope-iter33-qa-stale")
+    withheld_meta = _plant(dataset_store, _SYMBOL_WITHHELD, "goal-rapid-microscope-iter33-qa-withheld")
+
+    # Real builds for the OK and (soon-to-be-mutated) STALE datasets -- never for WITHHELD, which
+    # `run_snapshot_build_and_record`'s own filter would refuse to build for anyway.
+    ms.run_snapshot_build_and_record(dataset_store, CONFIG, snapshots_dir, [valid_meta["id"], stale_meta["id"]])
+
+    # Mutate ONLY the stale dataset's own persisted meta file's identity -- see module docstring.
+    stale_meta_path = Path(snapshots_dir) / f"{stale_meta['id']}.meta.json"
+    stored = json.loads(stale_meta_path.read_text())
+    stored["dataset_checksum"] = _STALE_DATASET_CHECKSUM
+    stale_meta_path.write_text(json.dumps(stored, sort_keys=True))
+
+    universe_ledger = vault.universe_ledger_for_dataset_dir(str(dataset_dir))
+    vault.register_universe(
+        universe_ledger,
+        universe_id=_WITHHELD_UNIVERSE_ID,
+        symbol_rule=[_SYMBOL_WITHHELD],
+        date_rule=[_SESSION_DATE],
+        vault_secret_commitment=vault.commit_vault_secret(_FIXTURE_VAULT_SECRET),
+        registered_at=_WITHHELD_UNIVERSE_REGISTERED_AT,
+    )
+
+    return {
+        "dataset_dir": str(dataset_dir),
+        "snapshots_dir": snapshots_dir,
+        "vault_dir": vault_dir,
+        "valid_dataset_id": valid_meta["id"],
+        "stale_dataset_id": stale_meta["id"],
+        "withheld_dataset_id": withheld_meta["id"],
+        "withheld_universe_id": _WITHHELD_UNIVERSE_ID,
+    }
+
+
+def main(root: Path) -> int:
+    planted = plant_disclosure_fixture(root)
+    print(
+        f"[seed-micro-snapshots-iter33] valid dataset_id={planted['valid_dataset_id']} "
+        f"({_SYMBOL_OK}), stale dataset_id={planted['stale_dataset_id']} ({_SYMBOL_STALE}, "
+        "meta mutated post-build), withheld dataset_id="
+        f"{planted['withheld_dataset_id']} ({_SYMBOL_WITHHELD}, universe="
+        f"{planted['withheld_universe_id']})",
+        file=sys.stderr,
+    )
+
+    # Self-check: the served report matches the intended three-way split before handing off to a
+    # browser pass.
+    dataset_store = DatasetStore(Path(planted["dataset_dir"]))
+    report = ms.snapshot_meta_report(planted["snapshots_dir"], dataset_store, CONFIG)
+    served_ids = {row["dataset_id"] for row in report["snapshots"]}
+    ok = True
+    if planted["valid_dataset_id"] not in served_ids:
+        print("[seed-micro-snapshots-iter33] ERROR: the valid snapshot is not served", file=sys.stderr)
+        ok = False
+    if planted["stale_dataset_id"] in served_ids:
+        print("[seed-micro-snapshots-iter33] ERROR: the stale meta is served as a row", file=sys.stderr)
+        ok = False
+    if planted["withheld_dataset_id"] in served_ids:
+        print("[seed-micro-snapshots-iter33] ERROR: the withheld member is served as a row", file=sys.stderr)
+        ok = False
+    if report["stale_excluded"] != 1:
+        print(
+            f"[seed-micro-snapshots-iter33] ERROR: stale_excluded={report['stale_excluded']!r}, expected 1",
+            file=sys.stderr,
+        )
+        ok = False
+    if report["withheld_excluded"] != 1:
+        print(
+            f"[seed-micro-snapshots-iter33] ERROR: withheld_excluded={report['withheld_excluded']!r}, expected 1",
+            file=sys.stderr,
+        )
+        ok = False
+    if not ok:
+        return 1
+    print("[seed-micro-snapshots-iter33] self-check ok: 1 valid served, 1 stale excluded, 1 withheld excluded", file=sys.stderr)
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()))
diff --git a/apps/backend/tests/test_seed_micro_snapshots_iter33_disclosure_fixture.py b/apps/backend/tests/test_seed_micro_snapshots_iter33_disclosure_fixture.py
new file mode 100644
index 00000000..54c308b6
--- /dev/null
+++ b/apps/backend/tests/test_seed_micro_snapshots_iter33_disclosure_fixture.py
@@ -0,0 +1,68 @@
+"""Regression coverage for ``scripts/seed_micro_snapshots_iter33_disclosure_fixture.py`` (Era
+"The Rapid Microscope", goal-rapid-microscope-iter-33, J-12's "fixture-scoped" browser-QA capture,
+TC-2) -- a guard for the FIXTURE SCRIPT itself, not for production code (the script imports and
+calls ``micro_snapshots.py``/``vault.py`` exactly as shipped; see the phase spec's OUT OF SCOPE
+list). Asserts the seed script's own fixture is well-formed end to end: the valid snapshot serves
+every identity field, the stale meta never appears as a row, and the withheld member never appears
+as a row -- with both disclosure counts exactly ``1`` -- and that the CLI entry point (``main``)
+runs its own self-check and exits clean on a fresh root."""
+
+from __future__ import annotations
+
+import sys
+from pathlib import Path
+
+_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
+sys.path.insert(0, str(_SCRIPTS_DIR))
+
+import seed_micro_snapshots_iter33_disclosure_fixture as seed  # noqa: E402
+
+from app.config import CONFIG  # noqa: E402
+from app.research import micro_snapshots as ms  # noqa: E402
+from app.research.datasets import DatasetStore  # noqa: E402
+
+
+def _report_for(root: Path, planted: dict) -> dict:
+    dataset_store = DatasetStore(Path(planted["dataset_dir"]))
+    return ms.snapshot_meta_report(planted["snapshots_dir"], dataset_store, CONFIG)
+
+
+def test_the_valid_snapshot_serves_every_identity_field_and_the_other_two_are_excluded(tmp_path):
+    planted = seed.plant_disclosure_fixture(tmp_path)
+    report = _report_for(tmp_path, planted)
+
+    assert len(report["snapshots"]) == 1
+    row = report["snapshots"][0]
+    assert row["dataset_id"] == planted["valid_dataset_id"]
+    for key in (
+        "dataset_id", "dataset_checksum", "micro_algo_version", "snapshot_format_version",
+        "feature_source_hash", "config_fingerprint", "params_hash", "quote_size_unit",
+        "row_count", "bytes_on_disk", "built_utc",
+    ):
+        assert key in row, f"the valid snapshot's own served meta is missing {key!r}"
+
+    served_ids = {r["dataset_id"] for r in report["snapshots"]}
+    assert planted["stale_dataset_id"] not in served_ids
+    assert planted["withheld_dataset_id"] not in served_ids
+    assert report["stale_excluded"] == 1
+    assert report["withheld_excluded"] == 1
+
+
+def test_the_stale_meta_never_carries_its_stale_value_anywhere(tmp_path):
+    """TR-7: `load_snapshot_meta` must MISS on the mutated meta, never re-serving the mutated
+    (or the original, pre-mutation) identity as a current row."""
+    planted = seed.plant_disclosure_fixture(tmp_path)
+    dataset_store = DatasetStore(Path(planted["dataset_dir"]))
+    loaded = ms.load_snapshot_meta(
+        planted["snapshots_dir"], dataset_store, planted["stale_dataset_id"], CONFIG
+    )
+    assert loaded is None
+
+
+def test_main_runs_its_own_self_check_and_exits_clean(tmp_path):
+    """``main`` (the CLI entry point ``TAPEOLOGY_DATASET_DIR=... .venv/bin/python scripts/
+    seed_micro_snapshots_iter33_disclosure_fixture.py ROOT`` actually invokes) plants the fixture
+    AND runs its own self-check against the served report before returning -- exercised here
+    exactly as a QA operator would invoke it, on a fresh root."""
+    exit_code = seed.main(tmp_path)
+    assert exit_code == 0
```
