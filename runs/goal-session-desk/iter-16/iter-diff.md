# Iteration diff (bounded)

Files changed: 8. Shown in full: 8.

```diff
diff --git a/apps/backend/app/research/desk_routes.py b/apps/backend/app/research/desk_routes.py
index d65bbe3..13a7962 100644
--- a/apps/backend/app/research/desk_routes.py
+++ b/apps/backend/app/research/desk_routes.py
@@ -13,29 +13,39 @@ shape) and the desk bar top-up's three compute-manager routes (``POST``/``GET
 /research/desk/topup/compute``, ``POST /research/desk/topup/compute/cancel`` — mirrors
 ``routes.py``'s ``/edge-report/compute`` trio verbatim).
 
-J-03 (unmodified this iteration) adds the screen: ``GET /research/desk/screen`` (latest + ``?date=``
-+ a lightweight meta-only snapshot list — never full ``rows``/``skipped`` for every historical
-snapshot, see ``desk_screen.py``'s module docstring) and the screen's own three compute-manager
-routes (``POST``/``GET /research/desk/screen/compute``, ``POST
-/research/desk/screen/compute/cancel`` — mirrors the top-up trio exactly). Kept as its own module
-(mirroring the plan's stated preference) rather than folding into ``routes.py``, which is already
-large; mounted separately in ``app/main.py``.
-
-J-09 (unmodified this iteration) adds ONE new read: ``GET /research/desk/topup/runs`` (the durable,
-append-only top-up run log — ``desk_topup_log.py``'s lightweight run-meta list + the latest full
-record; honest-empty ``{"runs": [], "latest": null}`` before any run, never a 404). No new compute
+J-03 (base shape unmodified; ``GET /research/desk/screen`` extended goal-desk-iter-16) adds the
+screen: latest + ``?date=`` + ``?id=`` (J-12, below) + a lightweight meta-only snapshot list — never
+full ``rows``/``skipped`` for every historical snapshot, see ``desk_screen.py``'s module docstring —
+and the screen's own three compute-manager routes (``POST``/``GET /research/desk/screen/compute``,
+``POST /research/desk/screen/compute/cancel`` — mirrors the top-up trio exactly). Kept as its own
+module (mirroring the plan's stated preference) rather than folding into ``routes.py``, which is
+already large; mounted separately in ``app/main.py``.
+
+J-09 (base shape unmodified; response body extended goal-desk-iter-16) adds ONE new read:
+``GET /research/desk/topup/runs`` (the durable, append-only top-up run log — ``desk_topup_log.py``'s
+lightweight run-meta list + the latest full record + ``integrity_errors`` (J-12, below); honest-empty
+``{"runs": [], "latest": null, "integrity_errors": []}`` before any run, never a 404). No new compute
 manager, no new POST — the log is written by the ALREADY-existing top-up trigger/CLI paths
 (``desk_topup_compute.py`` threads the write through internally); this route is a pure read,
 mirroring ``GET /research/desk/universe``'s single-synchronous-read shape exactly.
 
-J-10 (this iteration, goal-desk-iter-14) adds the coverage-index reconciliation: a trigger/poll/
-cancel trio (``POST``/``GET /research/desk/coverage/reconcile/compute``,
-``POST /research/desk/coverage/reconcile/compute/cancel`` — mirrors the top-up trio exactly) plus
-ONE durable read (``GET /research/desk/coverage/reconcile/runs`` — mirrors ``GET
-/research/desk/topup/runs``'s exact honest-empty/meta-only-list/full-latest shape). All four routes
-are pure wiring over ``desk_index_reconcile.py`` — see that module's own docstring for the
-classify/repair/record mechanics. No new MCP tool (``get_endpoint``'s existing ``/research/``
-allowlist already reaches the new GET path); no new router, no ``main.py`` change.
+J-10 (base shape from goal-desk-iter-14; response body extended goal-desk-iter-16) adds the
+coverage-index reconciliation: a trigger/poll/cancel trio (``POST``/``GET
+/research/desk/coverage/reconcile/compute``, ``POST /research/desk/coverage/reconcile/compute/cancel``
+— mirrors the top-up trio exactly) plus ONE durable read (``GET
+/research/desk/coverage/reconcile/runs`` — mirrors ``GET /research/desk/topup/runs``'s exact
+honest-empty/meta-only-list/full-latest/``integrity_errors`` shape). All four routes are pure wiring
+over ``desk_index_reconcile.py`` — see that module's own docstring for the classify/repair/record
+mechanics. No new MCP tool (``get_endpoint``'s existing ``/research/`` allowlist already reaches the
+new GET path); no new router, no ``main.py`` change.
+
+J-12 (this iteration, goal-desk-iter-16) is a pure additive-read + disclosure change, no new
+module/route/MCP tool: (a) ``GET /research/desk/screen`` gains a sibling ``?id=`` read so an
+EARLIER same-``screen_date`` recording — unreachable via ``?date=``, which always resolves to the
+newest match — becomes individually addressable by its own id; supplying both ``?id=`` and
+``?date=`` is an honest 4xx refusal. (b) ``get_topup_runs``/``get_desk_index_reconcile_runs`` stop
+discarding their own ``store.list()``'s ``errors`` return — both now serve it as
+``integrity_errors``, the identical key/shape ``get_screen``/``get_universe`` already used.
 
 **Compute managers are module-level singletons here, NOT ``ResearchRegistry`` properties.**
 ``DeskTopupComputeManager`` (``desk_topup_compute.py``) reuses ``routes.record_bar_series``
@@ -269,15 +279,21 @@ def _topup_run_meta_only(record: dict) -> dict:
 
 @router.get("/topup/runs")
 def get_topup_runs(store: TopupRunStore = Depends(get_topup_run_store)) -> dict:
-    """``{"runs": [...meta-only...], "latest": <full record>|null}`` — an explicit HTTP 200
-    honest-empty payload (``{"runs": [], "latest": null}``) before any top-up run has ever reached
-    its terminal state, never a 404 (the ``GET /research/desk/universe`` convention). ``latest`` is
-    the most recently STARTED run, verbatim from disk — never recomputed on the GET (the
-    ``GET /research/desk/screen`` convention: a plain read, triggers nothing)."""
-    records, _errors = store.list()
+    """``{"runs": [...meta-only...], "latest": <full record>|null, "integrity_errors": [...]}`` —
+    an explicit HTTP 200 honest-empty payload (``{"runs": [], "latest": null,
+    "integrity_errors": []}``) before any top-up run has ever reached its terminal state, never a
+    404 (the ``GET /research/desk/universe`` convention). ``latest`` is the most recently STARTED
+    run, verbatim from disk — never recomputed on the GET (the ``GET /research/desk/screen``
+    convention: a plain read, triggers nothing). ``integrity_errors`` is ``store.list()``'s own
+    ``errors`` return, surfaced verbatim (goal-desk-iter-16, J-12) — the identical key/shape
+    ``get_screen``/``get_universe`` already use; a corrupted run-record file stays excluded from
+    ``runs``/``latest`` either way, this only stops silently dropping the store's own honesty
+    channel."""
+    records, errors = store.list()
     return {
         "runs": [_topup_run_meta_only(r) for r in records],
         "latest": records[-1] if records else None,
+        "integrity_errors": errors,
     }
 
 
@@ -311,16 +327,32 @@ def _screen_meta_only(record: dict) -> dict:
 
 
 @router.get("/screen")
-def get_screen(date: str | None = None, store: ScreenStore = Depends(get_screen_store)) -> dict:
-    """Two shapes, selected by whether ``?date=`` is given (Data Contract addition #1):
+def get_screen(
+    date: str | None = None, id: str | None = None, store: ScreenStore = Depends(get_screen_store)
+) -> dict:
+    """Three shapes, selected by ``?date=``/``?id=`` (Data Contract addition #1, extended
+    goal-desk-iter-16 J-12):
 
-      * no ``date``: ``{"screens": [...meta-only...], "latest": <full snapshot>|null,
+      * neither given: ``{"screens": [...meta-only...], "latest": <full snapshot>|null,
         "integrity_errors": [...]}`` — an explicit HTTP 200 honest-empty payload
         (``{"screens": [], "latest": null, "integrity_errors": []}``) before any screen has ever
         been computed, never a 404 (the ``GET /research/desk/universe`` convention).
-      * ``date=YYYY-MM-DD``: ``{"screen": <the exact persisted snapshot for the latest recording
-        on that date, verbatim>|null}`` — a plain read, NEVER recomputed on the GET (TC-6)."""
+      * ``date=YYYY-MM-DD`` (``id`` absent): ``{"screen": <the exact persisted snapshot for the
+        latest recording on that date, verbatim>|null}`` — a plain read, NEVER recomputed on the
+        GET (TC-6). Byte-unchanged by this iteration.
+      * ``id=<snapshot id>`` (``date`` absent): ``{"screen": <that exact persisted snapshot,
+        verbatim>|null}`` — the only way to reach an EARLIER same-``screen_date`` recording once a
+        later one exists (``?date=`` always resolves to the newest match); an unknown ``id`` is an
+        honest ``null`` at HTTP 200, never a 404 (the ``?date=`` convention, mirrored).
+      * ``id`` and ``date`` both given: an honest 4xx refusal — never a silent precedence rule."""
+    if id is not None and date is not None:
+        raise HTTPException(
+            status_code=422, detail="only one of `id` or `date` may be supplied, not both"
+        )
     records, errors = store.list()
+    if id is not None:
+        found = next((r for r in records if r["id"] == id), None)
+        return {"screen": found}
     if date is not None:
         matching = [r for r in records if r["screen_date"] == date]
         return {"screen": matching[-1] if matching else None}
@@ -494,16 +526,18 @@ def _reconcile_run_meta_only(record: dict) -> dict:
 
 @router.get("/coverage/reconcile/runs")
 def get_desk_index_reconcile_runs(store: ReconcileRunStore = Depends(get_reconcile_run_store)) -> dict:
-    """``{"runs": [...meta-only...], "latest": <full record>|null}`` — an explicit HTTP 200
-    honest-empty payload (``{"runs": [], "latest": null}``) before any reconciliation has ever
-    reached its terminal state, never a 404 (the ``GET /research/desk/topup/runs`` convention).
-    ``latest`` is the most recently STARTED run, verbatim from disk — never recomputed on the GET. A
-    corrupted run-record file is excluded from ``runs``/``latest`` (never fabricated, never crashes
-    this route) — ``ReconcileRunStore.list()``'s own ``errors`` return already surfaces it
-    explicitly at the store layer (mirrors ``get_topup_runs``'s identical choice not to duplicate
-    that channel into this response body)."""
-    records, _errors = store.list()
+    """``{"runs": [...meta-only...], "latest": <full record>|null, "integrity_errors": [...]}`` —
+    an explicit HTTP 200 honest-empty payload (``{"runs": [], "latest": null,
+    "integrity_errors": []}``) before any reconciliation has ever reached its terminal state, never
+    a 404 (the ``GET /research/desk/topup/runs`` convention). ``latest`` is the most recently
+    STARTED run, verbatim from disk — never recomputed on the GET. A corrupted run-record file is
+    excluded from ``runs``/``latest`` (never fabricated, never crashes this route) —
+    ``ReconcileRunStore.list()``'s own ``errors`` return is now surfaced verbatim as
+    ``integrity_errors`` (goal-desk-iter-16, J-12) — the identical key/shape ``get_screen``/
+    ``get_universe``/``get_topup_runs`` already use, instead of being silently discarded."""
+    records, errors = store.list()
     return {
         "runs": [_reconcile_run_meta_only(r) for r in records],
         "latest": records[-1] if records else None,
+        "integrity_errors": errors,
     }
diff --git a/apps/backend/tests/test_desk_index_reconcile.py b/apps/backend/tests/test_desk_index_reconcile.py
index 14f2d29..5d1e02b 100644
--- a/apps/backend/tests/test_desk_index_reconcile.py
+++ b/apps/backend/tests/test_desk_index_reconcile.py
@@ -718,11 +718,13 @@ def test_get_reconcile_compute_before_any_trigger_is_an_honest_null_and_starts_n
 
 
 def test_get_reconcile_runs_before_any_run_is_the_honest_empty_payload_and_starts_nothing(route_ctx):
-    """TC-6."""
+    """TC-6. ``integrity_errors`` added goal-desk-iter-16 (J-12) — see
+    ``test_get_reconcile_runs_surfaces_a_corrupted_run_records_integrity_error`` below for the
+    non-empty case."""
     client, fresh_manager, _tmp_path = route_ctx
     r = client.get("/research/desk/coverage/reconcile/runs")
     assert r.status_code == 200
-    assert r.json() == {"runs": [], "latest": None}
+    assert r.json() == {"runs": [], "latest": None, "integrity_errors": []}
     assert fresh_manager.snapshot() is None  # the unrelated compute snapshot stayed untouched
 
 
@@ -852,8 +854,11 @@ def test_tc20_get_reconcile_runs_survives_a_corrupted_run_record_file_alongside_
             break
         time.sleep(0.02)
 
+    # goal-desk-iter-16 (J-12) TC-6: the corrupt file is planted in this test's OWN scoped
+    # `route_ctx` dir (rooted under `tmp_path`) -- never `apps/backend/.data`.
     reconcile_dir = tmp_path / "index_reconcile_runs"
-    (reconcile_dir / "reconcile-2026-01-01-deadbeef0000.json").write_text("{not json")
+    corrupt_path = reconcile_dir / "reconcile-2026-01-01-deadbeef0000.json"
+    corrupt_path.write_text("{not json")
 
     r = client.get("/research/desk/coverage/reconcile/runs")
     assert r.status_code == 200
@@ -861,6 +866,10 @@ def test_tc20_get_reconcile_runs_survives_a_corrupted_run_record_file_alongside_
     assert len(body["runs"]) == 1  # the corrupted file is excluded, never fabricated, never a crash
     assert body["latest"] is not None
     assert body["latest"]["state"] == "done"
+    # TC-6: the store's own `errors` return is now surfaced, never silently discarded.
+    assert len(body["integrity_errors"]) == 1
+    assert body["integrity_errors"][0]["file"] == corrupt_path.name
+    assert "corrupted or tampered" in body["integrity_errors"][0]["error"]
 
 
 def test_tc8_route_level_a_reconcile_run_leaves_the_universe_snapshot_file_byte_identical(route_ctx):
diff --git a/apps/backend/tests/test_desk_screen.py b/apps/backend/tests/test_desk_screen.py
index 546ec97..7e80866 100644
--- a/apps/backend/tests/test_desk_screen.py
+++ b/apps/backend/tests/test_desk_screen.py
@@ -999,3 +999,196 @@ def test_aapl_row_history_cross_checks_against_get_candles(ctx, monkeypatch):
     assert len(filtered) == row["history_sessions"]
     earliest_ts = min(bar["ts"] for bar in filtered)
     assert _iso_of(earliest_ts) == row["history_start"]
+
+
+# ==================================================================================================
+# screen ?id= read (goal-desk-iter-16, J-12) -- individual addressability, including an EARLIER
+# same-`screen_date` recording that `?date=` (which always resolves `matching[-1]`) can never reach.
+# ==================================================================================================
+
+
+@pytest.fixture
+def screen_route_ctx(tmp_path, monkeypatch):
+    """A live-routed screen store, scoped entirely under `tmp_path` (never `apps/backend/.data`):
+    same `TestClient`/`ResearchRegistry` wiring `test_aapl_row_cross_checks_byte_identical_to_the_
+    real_tradability_route` above already uses inline, lifted into a shared fixture for this
+    section's four route-level `?id=` tests."""
+    from fastapi.testclient import TestClient
+
+    from app.main import app, get_market_adapter, manager as ws_manager
+    from app.research.routes import ResearchRegistry, set_registry
+    from app.research.store import JournalStore
+
+    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
+    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
+    monkeypatch.setenv("TAPEOLOGY_DESK_SCREEN_DIR", str(tmp_path / "screen"))
+    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
+    registry = ResearchRegistry(store, CONFIG)
+    set_registry(registry)
+    with TestClient(app) as client:
+        yield client, tmp_path
+    for ticker in list(ws_manager._engines.keys()):
+        ws_manager.stop(ticker)
+    set_registry(None)
+    app.dependency_overrides.pop(get_market_adapter, None)
+    store.close()
+
+
+def _plant_same_date_pair(screen_dir) -> tuple[dict, dict, dict]:
+    """Two records sharing `screen_date` but differing `bar_store_signature` -- the REAL shape
+    goal.md's own worked example names (a pre-/post-repair pair whose reconciliation changed
+    coverage, not the requested date). Returns `(store, earlier, later)`, `earlier`/`later`
+    determined by the store's OWN `created_utc`-then-`id` sort (never assumed from call order, since
+    two same-microsecond wall-clock writes would otherwise make that assumption flaky)."""
+    store = ScreenStore(screen_dir)
+    _record(store, screen_date="2026-07-27", as_of="2026-07-27T23:59:59Z", bar_store_signature="a" * 16)
+    _record(store, screen_date="2026-07-27", as_of="2026-07-27T23:59:59Z", bar_store_signature="b" * 16)
+    records, errors = store.list()
+    assert errors == []
+    matching = [r for r in records if r["screen_date"] == "2026-07-27"]
+    assert len(matching) == 2
+    return store, matching[0], matching[-1]
+
+
+def test_get_screen_by_id_returns_the_exact_record_byte_identical_to_disk(screen_route_ctx):
+    """TC-1: `?id=<the earlier id>` returns that exact record, byte-identical to its own file on
+    disk -- same `id`/`screen_date`/`as_of`/`rows`/`skipped` -- distinct from what `?date=` (which
+    still resolves only the later recording, TC-2 below) would return for the same date."""
+    client, tmp_path = screen_route_ctx
+    _store, earlier, _later = _plant_same_date_pair(tmp_path / "screen")
+
+    r = client.get("/research/desk/screen", params={"id": earlier["id"]})
+    assert r.status_code == 200
+    body = r.json()
+    assert body["screen"] == earlier
+
+    on_disk = json.loads((tmp_path / "screen" / f"{earlier['id']}.json").read_text())
+    assert body["screen"] == on_disk["record"]["meta"]
+
+
+def test_get_screen_by_date_alone_still_resolves_only_the_later_recording(screen_route_ctx):
+    """TC-2: `?date=` (no `?id=`) is byte-unchanged by this iteration -- it still serves ONLY the
+    later of the two same-date recordings."""
+    client, tmp_path = screen_route_ctx
+    _store, earlier, later = _plant_same_date_pair(tmp_path / "screen")
+
+    r = client.get("/research/desk/screen", params={"date": "2026-07-27"})
+    assert r.status_code == 200
+    body = r.json()
+    assert body["screen"]["id"] == later["id"]
+    assert body["screen"]["id"] != earlier["id"]
+    assert body["screen"] == later
+
+
+def test_get_screen_by_unknown_id_is_an_honest_null_never_a_404(screen_route_ctx):
+    """TC-3: mirrors the `?date=` no-match convention -- an unrecognized `id` is `{"screen": null}`
+    at HTTP 200, never a 404."""
+    client, tmp_path = screen_route_ctx
+    _plant_same_date_pair(tmp_path / "screen")
+
+    r = client.get("/research/desk/screen", params={"id": "does-not-exist"})
+    assert r.status_code == 200
+    assert r.json() == {"screen": None}
+
+
+def test_get_screen_with_both_id_and_date_is_an_honest_4xx_refusal(screen_route_ctx):
+    """TC-4: supplying both query params is refused explicitly -- never a silent precedence rule
+    between the two lookup modes."""
+    client, tmp_path = screen_route_ctx
+    _store, earlier, _later = _plant_same_date_pair(tmp_path / "screen")
+
+    r = client.get(
+        "/research/desk/screen", params={"id": earlier["id"], "date": earlier["screen_date"]}
+    )
+    assert 400 <= r.status_code < 500
+    detail = r.json()["detail"]
+    assert "id" in detail and "date" in detail
+
+
+def test_get_screen_id_lookup_never_recomputes_and_the_meta_only_list_is_unaffected(screen_route_ctx):
+    """`?id=` is a plain read exactly like `?date=` (TC-6's own "recomputes nothing" clause,
+    extended): the no-param meta-only list/`latest`/`integrity_errors` shape is untouched by this
+    iteration, and issuing an `?id=` lookup leaves the store's own files byte-unchanged."""
+    client, tmp_path = screen_route_ctx
+    _store, earlier, later = _plant_same_date_pair(tmp_path / "screen")
+    earlier_path = tmp_path / "screen" / f"{earlier['id']}.json"
+    before = earlier_path.read_bytes()
+
+    client.get("/research/desk/screen", params={"id": earlier["id"]})
+
+    assert earlier_path.read_bytes() == before
+
+    listed = client.get("/research/desk/screen").json()
+    assert {row["id"] for row in listed["screens"]} == {earlier["id"], later["id"]}
+    assert listed["latest"]["id"] == later["id"]
+    assert listed["integrity_errors"] == []
+
+
+def test_sha256_of_every_universe_screen_topup_run_reconcile_run_file_is_unchanged_by_this_iteration(
+    screen_route_ctx,
+):
+    """TC-15: this iteration is a pure additive-READ (screen's new `?id=` branch) plus a
+    response-shape-only disclosure (`integrity_errors` surfaced on the two run-ledger GETs) --
+    neither touches a single byte on disk. A SHA-256 checksum of EVERY universe/screen/topup-run/
+    reconcile-run file, taken before and after exercising every GET this iteration touched
+    (including the new `?id=`/`?date=` reads and both ledger GETs, each called more than once), must
+    come back identical -- proving nothing was backfilled, rewritten, or re-tagged."""
+    import hashlib
+
+    from app.research.desk_index_reconcile import ReconcileRunStore
+    from app.research.desk_routes import get_reconcile_run_store, get_topup_run_store
+    from app.research.desk_topup_log import TopupRunStore
+
+    client, tmp_path = screen_route_ctx
+
+    UniverseStore(tmp_path / "universe").record(
+        members=["AAPL", "MSFT"], raw_members={"AAPL": "AAPL", "MSFT": "MSFT"},
+        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
+    )
+    _screen_store, earlier, later = _plant_same_date_pair(tmp_path / "screen")
+
+    topup_store: TopupRunStore = get_topup_run_store()
+    topup_store.record(
+        universe_snapshot_id="universe-2026-07-25-49b33fa31680",
+        requested_window={"start": "2024-07-28T00:00:00Z", "end": "2026-07-28T00:00:00Z"},
+        config_fingerprint=CONFIG.config_fingerprint(),
+        started_utc="2026-07-28T09:00:00.000000Z", finished_utc="2026-07-28T09:05:00.000000Z",
+        state="done", pairs_total=1,
+        outcomes=[{"symbol": "AAA", "timeframe": "1h", "outcome": "fetched", "detail": None}],
+    )
+
+    reconcile_store: ReconcileRunStore = get_reconcile_run_store()
+    empty_drift = {"unindexed_series": [], "orphan_index_rows": [], "stale_checksum_rows": []}
+    reconcile_store.record(
+        config_fingerprint=CONFIG.config_fingerprint(),
+        started_utc="2026-07-28T09:00:00.000000Z", finished_utc="2026-07-28T09:05:00.000000Z",
+        state="done", series_on_disk=0, rows_indexed_before=0, rows_indexed_after=0,
+        drift_before=empty_drift, drift_after=empty_drift, store_errors=[],
+    )
+
+    tracked_dirs = [
+        tmp_path / "universe", tmp_path / "screen", topup_store.root, reconcile_store.root,
+    ]
+
+    def _checksums() -> dict[str, str]:
+        return {
+            str(path): hashlib.sha256(path.read_bytes()).hexdigest()
+            for directory in tracked_dirs
+            for path in sorted(directory.glob("*.json"))
+        }
+
+    before = _checksums()
+    assert len(before) == 5  # 1 universe + 2 screen + 1 topup-run + 1 reconcile-run
+
+    client.get("/research/desk/screen")
+    client.get("/research/desk/screen", params={"date": "2026-07-27"})
+    client.get("/research/desk/screen", params={"id": earlier["id"]})
+    client.get("/research/desk/screen", params={"id": later["id"]})
+    client.get("/research/desk/screen", params={"id": "does-not-exist"})
+    client.get("/research/desk/topup/runs")
+    client.get("/research/desk/topup/runs")
+    client.get("/research/desk/coverage/reconcile/runs")
+    client.get("/research/desk/coverage/reconcile/runs")
+
+    after = _checksums()
+    assert after == before
diff --git a/apps/backend/tests/test_desk_topup_compute.py b/apps/backend/tests/test_desk_topup_compute.py
index 34b84bf..a4ccfd6 100644
--- a/apps/backend/tests/test_desk_topup_compute.py
+++ b/apps/backend/tests/test_desk_topup_compute.py
@@ -687,15 +687,17 @@ def test_cancel_while_running_succeeds_and_a_subsequent_cancel_is_409(route_ctx,
 
 
 def test_get_topup_runs_before_any_run_is_the_honest_empty_payload_and_starts_nothing(route_ctx):
-    """TC-1 + TC-8: HTTP 200 ``{"runs": [], "latest": null}`` before any top-up run has ever
-    completed, and the GET itself triggers no compute (the ``/topup/compute`` snapshot stays
-    untouched)."""
+    """TC-1 + TC-8: HTTP 200 ``{"runs": [], "latest": null, "integrity_errors": []}`` before any
+    top-up run has ever completed, and the GET itself triggers no compute (the ``/topup/compute``
+    snapshot stays untouched). ``integrity_errors`` added goal-desk-iter-16 (J-12) — see
+    ``test_get_topup_runs_surfaces_a_corrupted_run_records_integrity_error`` below for the
+    non-empty case."""
     client, _fresh_manager, _tmp_path = route_ctx
     adapter = _inject_adapter(bars=_bars())
 
     r = client.get("/research/desk/topup/runs")
     assert r.status_code == 200
-    assert r.json() == {"runs": [], "latest": None}
+    assert r.json() == {"runs": [], "latest": None, "integrity_errors": []}
     assert adapter.fetch_bars_calls == []
 
     # TC-8, precisely: calling the new GET (any number of times) never starts a top-up compute --
@@ -750,6 +752,40 @@ def test_get_topup_runs_after_a_completed_run_serves_the_full_latest_record_and_
     assert meta["state"] == latest["state"]
     assert meta["pairs_total"] == latest["pairs_total"]
     assert meta["pairs_attempted"] == latest["pairs_attempted"]
+    assert body["integrity_errors"] == []  # a genuinely clean run has no integrity problem to name
+
+
+def test_get_topup_runs_surfaces_a_corrupted_run_records_integrity_error(route_ctx):
+    """goal-desk-iter-16 (J-12) TC-5: a corrupt run-record file planted in the run log's own
+    directory -- a SIBLING of `route_ctx`'s scoped `TAPEOLOGY_DESK_UNIVERSE_DIR`, resolved via
+    `get_topup_run_store` exactly as the route itself resolves it, never `apps/backend/.data` --
+    is named in `integrity_errors` and excluded from `runs`/`latest`, alongside one genuine record
+    that survives untouched."""
+    client, _fresh_manager, _tmp_path = route_ctx
+    store = get_topup_run_store()
+    genuine = store.record(
+        universe_snapshot_id="universe-2026-07-25-49b33fa31680",
+        requested_window={"start": "2024-07-28T00:00:00Z", "end": "2026-07-28T00:00:00Z"},
+        config_fingerprint=CONFIG.config_fingerprint(),
+        started_utc="2026-07-28T09:00:00.000000Z",
+        finished_utc="2026-07-28T09:05:00.000000Z",
+        state="done",
+        pairs_total=1,
+        outcomes=[{"symbol": "AAA", "timeframe": "1h", "outcome": "fetched", "detail": None}],
+    )
+    corrupt_path = store.root / "topup-2026-01-01-deadbeef0000.json"
+    corrupt_path.write_text("{not json")
+
+    r = client.get("/research/desk/topup/runs")
+    assert r.status_code == 200
+    body = r.json()
+    assert len(body["runs"]) == 1
+    assert body["runs"][0]["id"] == genuine["id"]
+    assert body["latest"]["id"] == genuine["id"]
+    assert body["integrity_errors"] == [
+        {"file": corrupt_path.name, "error": body["integrity_errors"][0]["error"]}
+    ]
+    assert "corrupted or tampered" in body["integrity_errors"][0]["error"]
 
 
 def test_topup_run_store_directory_defaults_to_a_sibling_of_the_scoped_universe_dir(route_ctx):
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index 4dfdb07..9dcba63 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -419,6 +419,53 @@ async def test_get_endpoint_desk_screen_date_query_proxies_verbatim(mcp_env, bac
     assert result.content[0].text.encode("utf-8") == rest.content, "desk screen date-nonmatch not byte-identical"
 
 
+@pytest.mark.anyio
+async def test_get_endpoint_desk_screen_id_query_proxies_verbatim(mcp_env, backend_paths):
+    """goal-desk-iter-16 (J-12) TC-7: ``get_endpoint`` reaches the NEW ``?id=`` lookup variant with
+    ZERO MCP code change (the existing ``/research/`` allowlist prefix already covers it) --
+    byte-identical for a matching id (seeded HERE, under its own distinct date so this test passes
+    standalone) and the honest ``{"screen": null}`` 200 for an unknown id (never a 404)."""
+    screen_dir = Path(backend_paths["TAPEOLOGY_DESK_SCREEN_DIR"])
+    recorded = ScreenStore(screen_dir).record(
+        screen_date="2026-07-27",
+        as_of="2026-07-27T21:00:00Z",
+        universe_snapshot_id="universe-2026-07-25-817cc184bbb3",
+        config_fingerprint=CONFIG.config_fingerprint(),
+        bar_store_signature="mcp-test-id-query-signature",
+        rows=[
+            {
+                "symbol": "NFLX",
+                "side": "resistance",
+                "band_class": "A",
+                "distance_bps": 8.0,
+                "band_score": 2.5,
+                "price_low": 400.0,
+                "price_high": 402.0,
+                "coverage": {"1d": {"has_bars": True, "latest_window_end_utc": "2026-07-27T00:00:00Z"}},
+                "tick_evidence": True,
+            }
+        ],
+        skipped=[],
+    )
+
+    matching_path = f"/research/desk/screen?id={recorded['id']}"
+    result = await call_tool("get_endpoint", {"path": matching_path})
+    rest = httpx.get(f"{mcp_env}{matching_path}", timeout=5.0)
+    assert rest.status_code == 200
+    assert rest.json()["screen"] is not None
+    assert rest.json()["screen"]["id"] == recorded["id"]
+    assert result.isError is False
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk screen id-match not byte-identical"
+
+    nonmatch_path = "/research/desk/screen?id=does-not-exist"
+    result = await call_tool("get_endpoint", {"path": nonmatch_path})
+    rest = httpx.get(f"{mcp_env}{nonmatch_path}", timeout=5.0)
+    assert rest.status_code == 200
+    assert rest.json() == {"screen": None}
+    assert result.isError is False
+    assert result.content[0].text.encode("utf-8") == rest.content, "desk screen id-nonmatch not byte-identical"
+
+
 @pytest.mark.anyio
 async def test_datasets_tool_byte_identical_on_a_non_empty_live_list(mcp_env, backend_paths):
     """J-02 flips ``datasets`` from honest 404 to live data with ZERO MCP code changes: after
@@ -906,8 +953,9 @@ async def test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool(mcp_
     """goal-desk-iter-11 TC-9 (J-09): the NEW ``GET /research/desk/topup/runs`` route is reachable
     through ``get_endpoint``'s existing ``/research/`` allowlist prefix with ZERO MCP code change —
     no new tool, no ``_STATIC_PATHS`` entry — and the proxied body is byte-identical to its curl
-    equivalent (here the honest-empty ``{"runs": [], "latest": null}`` this module-scoped backend's
-    own temp desk dirs genuinely produce). The tool count assertion lives in
+    equivalent (here the honest-empty ``{"runs": [], "latest": null, "integrity_errors": []}`` this
+    module-scoped backend's own temp desk dirs genuinely produce — the ``integrity_errors`` key
+    goal-desk-iter-16/J-12 added). The tool count assertion lives in
     ``test_advertised_tool_set_is_exactly_capability_6``; this is the reachability half TC-9 names
     separately."""
     result = await call_tool("get_endpoint", {"path": "/research/desk/topup/runs"})
@@ -916,7 +964,7 @@ async def test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool(mcp_
     assert result.isError is False
     assert len(result.content) == 1
     assert result.content[0].text.encode("utf-8") == rest.content, "topup/runs not byte-identical"
-    assert rest.json() == {"runs": [], "latest": None}
+    assert rest.json() == {"runs": [], "latest": None, "integrity_errors": []}
     assert "desk_topup_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 17
 
 
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index 0181955..ee51f18 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -9,7 +9,7 @@ import {
   fetchDeskReconcileCompute,
   fetchDeskReconcileRuns,
   fetchDeskScreen,
-  fetchDeskScreenByDate,
+  fetchDeskScreenById,
   fetchDeskScreenCompute,
   fetchDeskTopupCompute,
   fetchDeskTopupRuns,
@@ -91,6 +91,19 @@ import { fmt } from "@/lib/format";
 // unconditionally, immediately after "Top-up runs" — the SAME "independent of screen state"
 // placement precedent iter-11 established, since reconciliation touches only the bar store/index,
 // never a screen. Page-load GETs still trigger nothing (T-4/5C, unchanged).
+//
+// goal-desk-iter-16 (J-12): individual addressability + honest ledger disclosure, zero new
+// endpoint/section. Screen History selection/highlighting switches from `screen_date`-keyed to
+// `id`-keyed (`fetchDeskScreenById`, the new `?id=` read) so an EARLIER same-`screen_date`
+// recording — unreachable via `?date=`, which always resolves the newest match — is individually
+// openable, and each history row now shows its own `created_utc` so two same-date rows read
+// distinctly. Provenance gains the displayed snapshot's own `id`/`created_utc` and, in the
+// default (latest) view only, describes itself as the most recently RECORDED screen rather than
+// "the latest screen date". The Screen History, Top-up Runs, and Index Reconciliation sections
+// each gained a count-plus-filename `IntegrityErrorsNote` whenever that ledger's own
+// `integrity_errors` carries an entry — the Universe ledger has no existing frontend section to
+// extend (never fetched/rendered on this page today, unlike the plan's premise; see the dev
+// handoff's Known Issues).
 
 const NUMERIC_CELL = "px-2 py-1.5 text-right font-mono text-xs text-slate-200 whitespace-nowrap";
 const HEADER_CELL = "px-2 py-1 text-right text-[11px] font-medium text-slate-500";
@@ -473,8 +486,15 @@ function DeskSkippedSection({ skipped, asOf }: { skipped: DeskScreenSkip[]; asOf
 // date's persisted snapshot (`GET /research/desk/screen?date=`) and swaps it into the page's
 // display in place; the click-through itself is a same-page state swap, never a navigation, so it
 // stays a plain `onClick` (not a `Link` — the `Link`/drill-in requirement below is only for
-// jumping to `/structure`). `selectedDate` highlights the currently-displayed row (`null` while
-// viewing the latest screen, since the latest need not be one of the listed historical rows). -----
+// jumping to `/structure`).
+//
+// goal-desk-iter-16 (J-12): selection/highlighting switches from `screen_date`-keyed to
+// `id`-keyed — the store's own 5-pin key already allows two recordings under the SAME
+// `screen_date` (a pre-/post-repair pair, e.g.), and a `screen_date`-keyed select/highlight could
+// only ever reach or distinguish one of the two. Each row now also shows its own `created_utc`
+// beside `screen_date` so two same-date rows read distinctly without opening either. `selectedId`
+// highlights the currently-displayed row's own id (see `DeskPage`'s `displayedSnapshot?.id`, which
+// covers BOTH a selected history entry and the default latest view). ------------------------------
 
 function DeskHistoryRow({
   meta,
@@ -482,20 +502,24 @@ function DeskHistoryRow({
   selected,
 }: {
   meta: DeskScreenMeta;
-  onSelect: (date: string) => void;
+  onSelect: (id: string) => void;
   selected: boolean;
 }) {
   return (
     <tr
       data-testid="desk-history-row"
+      data-screen-id={meta.id}
       data-screen-date={meta.screen_date}
       data-selected={selected}
-      onClick={() => onSelect(meta.screen_date)}
+      onClick={() => onSelect(meta.id)}
       className={`cursor-pointer border-b border-slate-800/60 transition-colors last:border-b-0 hover:bg-slate-900/40 ${
         selected ? "bg-slate-800/60" : ""
       }`}
     >
       <td className={LABEL_CELL}>{meta.screen_date}</td>
+      <td className={LABEL_CELL} data-testid="desk-history-created-utc">
+        {meta.created_utc}
+      </td>
       <td className={NUMERIC_CELL}>{meta.counts.rows}</td>
       <td className={NUMERIC_CELL}>{meta.counts.skipped}</td>
       <td className={LABEL_CELL} data-testid="desk-history-provenance">
@@ -508,11 +532,11 @@ function DeskHistoryRow({
 function DeskHistoryTable({
   screens,
   onSelect,
-  selectedDate,
+  selectedId,
 }: {
   screens: DeskScreenMeta[];
-  onSelect: (date: string) => void;
-  selectedDate: string | null;
+  onSelect: (id: string) => void;
+  selectedId: string | null;
 }) {
   if (screens.length === 0) {
     return <EmptyState testid="desk-history-empty" title="No screens recorded yet." />;
@@ -523,6 +547,7 @@ function DeskHistoryTable({
         <thead>
           <tr className="border-b border-slate-800">
             <th className={HEADER_CELL_LEFT}>date</th>
+            <th className={HEADER_CELL_LEFT}>recorded</th>
             <th className={HEADER_CELL}>rows</th>
             <th className={HEADER_CELL}>skipped</th>
             <th className={HEADER_CELL_LEFT}>provenance</th>
@@ -534,7 +559,7 @@ function DeskHistoryTable({
               key={meta.id}
               meta={meta}
               onSelect={onSelect}
-              selected={meta.screen_date === selectedDate}
+              selected={meta.id === selectedId}
             />
           ))}
         </tbody>
@@ -670,6 +695,29 @@ function LatestTopupRunDetail({ run }: { run: DeskTopupRun }) {
   );
 }
 
+// --- Ledger integrity-error disclosure (goal-desk-iter-16, J-12) — a count-plus-filename inline
+// note, mirroring `desk-provenance-signature-note`'s plain-text styling (never a new alert/badge
+// component). Renders ONLY when the ledger's own payload carries at least one entry — absent
+// otherwise, never an empty-array placeholder. Shared across the Screen History, Top-up Runs, and
+// Index Reconciliation sections below (each already receives `integrity_errors` verbatim from its
+// own GET). ------------------------------------------------------------------------------------
+
+function IntegrityErrorsNote({
+  errors,
+  testid,
+}: {
+  errors: { file: string; error: string }[];
+  testid: string;
+}) {
+  if (errors.length === 0) return null;
+  return (
+    <p data-testid={testid} className="mt-2 text-[11px] text-amber-300">
+      {errors.length} file{errors.length === 1 ? "" : "s"} failed an integrity check and{" "}
+      {errors.length === 1 ? "is" : "are"} excluded: {errors.map((e) => e.file).join(", ")}
+    </p>
+  );
+}
+
 // The section's own Loading/Unavailable/Populated states — independent of `screenResult` (a
 // top-up run's history is a separate concern from a screen's), fed by its own mount-time GET (see
 // `DeskPage` below). Mirrors the top-level ternary's exact three-state shape.
@@ -693,6 +741,10 @@ function TopupRunsSection({
     <div>
       <TopupRunsTable runs={result.data.runs} />
       {result.data.latest !== null && <LatestTopupRunDetail run={result.data.latest} />}
+      <IntegrityErrorsNote
+        errors={result.data.integrity_errors}
+        testid="desk-topup-runs-integrity-errors"
+      />
     </div>
   );
 }
@@ -872,12 +924,16 @@ function ReconciliationSection({
     <div>
       <IndexReconciliationTable runs={result.data.runs} />
       {result.data.latest !== null && <LatestReconciliationDetail run={result.data.latest} />}
+      <IntegrityErrorsNote
+        errors={result.data.integrity_errors}
+        testid="desk-reconcile-runs-integrity-errors"
+      />
     </div>
   );
 }
 
-// --- Provenance line — universe snapshot id + date, as_of, config_fingerprint, and the pinned
-// bar-store signature. --------------------------------------------------------------------------
+// --- Provenance line — snapshot id + recorded-at time, universe snapshot id + date, as_of,
+// config_fingerprint, and the pinned bar-store signature. -------------------------------------
 //
 // The signature's LABEL (era-desk-iter-4 audit F1): `bar_store_signature` is a checksum —
 // `sha256(sorted (symbol, timeframe, latest_window_end_utc) tuples)[:16]` (desk_screen.py) — not a
@@ -887,14 +943,36 @@ function ReconciliationSection({
 // is a window end — each coverage badge's own `latest_window_end_utc` tooltip, which keeps it. Here
 // the honest name is the signature's own, with a caption saying what it summarizes. The blueprint's
 // registered wording is amended in the same commit.
-function DeskProvenance({ snapshot }: { snapshot: DeskScreenSnapshot }) {
+//
+// goal-desk-iter-16 (J-12): `id`/`created_utc` (a straight re-format of fields `DeskScreenSnapshot`
+// already carries — nothing derived) name EXACTLY which of possibly several same-date recordings is
+// on screen. `isViewingLatest` gates a default-view-only note: while showing `latest`
+// (`created_utc`-sorted newest recording, TC-12), the copy describes itself as "the most recently
+// recorded screen", never "the latest screen date" — a same-date recording can still exist earlier
+// and be reachable from Screen History below.
+function DeskProvenance({
+  snapshot,
+  isViewingLatest,
+}: {
+  snapshot: DeskScreenSnapshot;
+  isViewingLatest: boolean;
+}) {
   return (
     <div data-testid="desk-provenance">
+      <Metric label="Snapshot id" value={snapshot.id} />
+      <Metric label="Recorded at" value={snapshot.created_utc} />
       <Metric label="Universe snapshot" value={snapshot.universe_snapshot_id ?? "—"} />
       <Metric label="Screen date" value={snapshot.screen_date} />
       <Metric label="As of" value={snapshot.as_of} />
       <Metric label="Config fingerprint" value={snapshot.config_fingerprint} />
       <Metric label="Bar-store signature" value={snapshot.bar_store_signature} />
+      {isViewingLatest && (
+        <p data-testid="desk-provenance-latest-note" className="mt-1 text-[11px] text-slate-600">
+          This is the most recently recorded screen (by recorded-at time), not necessarily the
+          latest screen date — an earlier same-date recording can still exist and be opened from
+          Screen History below.
+        </p>
+      )}
       <p data-testid="desk-provenance-signature-note" className="mt-1 text-[11px] text-slate-600">
         The bar-store signature is a checksum over every member&apos;s window-last-requested
         timestamp at the moment this screen was computed — a pin, never a time. Each coverage
@@ -1235,22 +1313,24 @@ function DeskNotComputedPanel({
 function DeskPopulatedScreen({
   snapshot,
   screens,
+  screenIntegrityErrors,
   isViewingLatest,
   historyFetchError,
   onSelectHistory,
   onShowLatest,
-  selectedHistoryDate,
+  selectedHistoryId,
   screenControlProps,
   topupControlProps,
   reconcileControlProps,
 }: {
   snapshot: DeskScreenSnapshot;
   screens: DeskScreenMeta[];
+  screenIntegrityErrors: { file: string; error: string }[];
   isViewingLatest: boolean;
   historyFetchError: string | null;
-  onSelectHistory: (date: string) => void;
+  onSelectHistory: (id: string) => void;
   onShowLatest: () => void;
-  selectedHistoryDate: string | null;
+  selectedHistoryId: string | null;
   screenControlProps: ScreenControlProps;
   topupControlProps: TopupControlProps;
   reconcileControlProps: ReconcileControlProps;
@@ -1281,7 +1361,7 @@ function DeskPopulatedScreen({
 
       <section aria-label="Provenance">
         <Panel title="Provenance">
-          <DeskProvenance snapshot={snapshot} />
+          <DeskProvenance snapshot={snapshot} isViewingLatest={isViewingLatest} />
         </Panel>
       </section>
 
@@ -1310,7 +1390,11 @@ function DeskPopulatedScreen({
           <DeskHistoryTable
             screens={screens}
             onSelect={onSelectHistory}
-            selectedDate={selectedHistoryDate}
+            selectedId={selectedHistoryId}
+          />
+          <IntegrityErrorsNote
+            errors={screenIntegrityErrors}
+            testid="desk-screen-history-integrity-errors"
           />
         </Panel>
       </section>
@@ -1373,10 +1457,11 @@ export default function DeskPage() {
 
   // era-desk-iter-6 (J-05): the screen-history click-through. `viewingSnapshot` is `null` while
   // showing the top-level `latest` snapshot already held in `screenResult` (no refetch needed to
-  // return to it — TC-2); once a history row is selected, it holds THAT date's own full snapshot,
-  // fetched via the already-shipped `?date=` read (`fetchDeskScreenByDate`, zero new backend
-  // route). `historyFetchError` surfaces a failed/no-match click WITHOUT disturbing whatever is
-  // currently displayed (no crash, no blank state — the plan's own error-case requirement).
+  // return to it — TC-2); once a history row is selected, it holds THAT row's own full snapshot,
+  // fetched via the `?id=` read (`fetchDeskScreenById`, goal-desk-iter-16/J-12 — switched from the
+  // date-keyed variant so an earlier same-`screen_date` recording is individually reachable).
+  // `historyFetchError` surfaces a failed/no-match click WITHOUT disturbing whatever is currently
+  // displayed (no crash, no blank state — the plan's own error-case requirement).
   const [viewingSnapshot, setViewingSnapshot] = useState<DeskScreenSnapshot | null>(null);
   const [historyFetchError, setHistoryFetchError] = useState<string | null>(null);
 
@@ -1548,18 +1633,22 @@ export default function DeskPage() {
   }
 
   // era-desk-iter-6 (J-05): select a past history row — fetch-and-swap, no POST, no recompute
-  // (TC-1). A date with no matching recorded screen (`{"screen": null}`) or an unreachable backend
-  // both leave the currently-displayed snapshot exactly as it was — only the error note changes.
-  async function handleSelectHistoryScreen(date: string) {
+  // (TC-1). goal-desk-iter-16 (J-12): switched from `?date=` to `?id=` — a `screen_date`-keyed
+  // fetch could only ever resolve the NEWER of two same-date recordings (`?date=`'s own
+  // `matching[-1]` convention), so it structurally could not reach an earlier same-date entry;
+  // `?id=` addresses each recording individually. An unknown id (`{"screen": null}`) or an
+  // unreachable backend both leave the currently-displayed snapshot exactly as it was — only the
+  // error note changes.
+  async function handleSelectHistoryScreen(id: string) {
     setHistoryFetchError(null);
-    const result = await fetchDeskScreenByDate(date);
+    const result = await fetchDeskScreenById(id);
     if (result.ok && result.data !== null) {
       setViewingSnapshot(result.data);
       return;
     }
     setHistoryFetchError(
       result.ok
-        ? `No recorded screen matches ${date} — still showing the previously displayed screen.`
+        ? "No recorded screen matches that entry — still showing the previously displayed screen."
         : result.error ?? "That recorded screen could not be loaded.",
     );
   }
@@ -1601,6 +1690,7 @@ export default function DeskPage() {
 
   const latest = screenResult?.ok ? screenResult.data?.latest ?? null : null;
   const screens = screenResult?.ok ? screenResult.data?.screens ?? [] : [];
+  const screenIntegrityErrors = screenResult?.ok ? screenResult.data?.integrity_errors ?? [] : [];
   // The snapshot actually on screen: a selected history entry, or `latest` when none is selected.
   // `latest === null` (never `displayedSnapshot === null`) stays the ONE discriminator for the
   // honest "Desk screen not computed yet." empty state — with no screen ever recorded there is
@@ -1612,6 +1702,11 @@ export default function DeskPage() {
   // and a banner claiming "not the latest" there would state something false about the very
   // snapshot it is describing.
   const isViewingLatest = viewingSnapshot === null || viewingSnapshot.id === latest?.id;
+  // goal-desk-iter-16 (J-12): the id-based highlight for `DeskHistoryTable` — the SAME id the
+  // above `isViewingLatest` check already compares against, so the currently-displayed snapshot
+  // (a selected history entry OR the default `latest`) is always the one highlighted row, even
+  // when it shares its `screen_date` with another recorded entry.
+  const selectedHistoryId = viewingSnapshot?.id ?? latest?.id ?? null;
 
   return (
     <div className="min-h-screen">
@@ -1647,11 +1742,12 @@ export default function DeskPage() {
           <DeskPopulatedScreen
             snapshot={displayedSnapshot ?? latest}
             screens={screens}
+            screenIntegrityErrors={screenIntegrityErrors}
             isViewingLatest={isViewingLatest}
             historyFetchError={historyFetchError}
             onSelectHistory={handleSelectHistoryScreen}
             onShowLatest={handleShowLatest}
-            selectedHistoryDate={viewingSnapshot?.screen_date ?? null}
+            selectedHistoryId={selectedHistoryId}
             screenControlProps={screenControlProps}
             topupControlProps={topupControlProps}
             reconcileControlProps={reconcileControlProps}
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 29d5599..5858863 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -978,6 +978,35 @@ export async function fetchDeskScreenByDate(date: string): Promise<{
   }
 }
 
+// GET /research/desk/screen?id= — the exact persisted snapshot recorded under that id, verbatim,
+// or `null` when nothing matches (an honest "nothing recorded under this id", never an error).
+// goal-desk-iter-16 (J-12): the ONLY way to reach an EARLIER same-`screen_date` recording once a
+// later one exists (`?date=` always resolves the newest match) — mirrors `fetchDeskScreenByDate`
+// byte-for-byte except the query param name.
+export async function fetchDeskScreenById(id: string): Promise<{
+  ok: boolean;
+  data: DeskScreenSnapshot | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/screen?id=${encodeURIComponent(id)}`);
+    if (res.ok) {
+      const data = await res.json();
+      return { ok: true, data: (data.screen as DeskScreenSnapshot | null) ?? null };
+    }
+    let error = "The desk screen for that id could not be loaded.";
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
 // POST /research/desk/screen/compute — start (or, while one is already running, observe) the
 // single-flight screen compute job. `screenDate` is the CALLER's own today (the `todayUtcDate()`
 // helper, /structure's own "Today" shortcut precedent) — this function takes it as a parameter
@@ -1115,9 +1144,11 @@ export async function cancelDeskTopupCompute(): Promise<{ ok: boolean; error?: s
 
 // era-desk-iter-11 (J-09): GET /research/desk/topup/runs — the durable, append-only top-up run
 // log's meta-only list + the latest full record, served VERBATIM. Mirrors `fetchDeskScreen`'s
-// exact `{ok, data, error}` shape byte-for-byte. An honest-empty (`{runs: [], latest: null}`)
-// result is a valid `ok:true` outcome — the caller renders it as "No top-up runs recorded yet.",
-// never a failure; `data: null` is reserved for a genuine non-200 / unreachable backend.
+// exact `{ok, data, error}` shape byte-for-byte. An honest-empty (`{runs: [], latest: null,
+// integrity_errors: []}`) result is a valid `ok:true` outcome — the caller renders it as "No top-up
+// runs recorded yet.", never a failure; `data: null` is reserved for a genuine non-200 /
+// unreachable backend. `integrity_errors` (goal-desk-iter-16, J-12) passes through `res.json()`
+// verbatim — no function-body change needed, just the widened `DeskTopupRunsListResult` type.
 export async function fetchDeskTopupRuns(): Promise<{
   ok: boolean;
   data: DeskTopupRunsListResult | null;
@@ -1208,9 +1239,11 @@ export async function cancelDeskReconcileCompute(): Promise<{ ok: boolean; error
 // era-desk-iter-14 (J-10): GET /research/desk/coverage/reconcile/runs — the durable, append-only
 // reconciliation run log's meta-only list + the latest full record, served VERBATIM. Mirrors
 // `fetchDeskTopupRuns`'s exact `{ok, data, error}` shape byte-for-byte. An honest-empty
-// (`{runs: [], latest: null}`) result is a valid `ok:true` outcome — the caller renders it as
-// "No reconciliation run recorded yet.", never a failure; `data: null` is reserved for a genuine
-// non-200 / unreachable backend.
+// (`{runs: [], latest: null, integrity_errors: []}`) result is a valid `ok:true` outcome — the
+// caller renders it as "No reconciliation run recorded yet.", never a failure; `data: null` is
+// reserved for a genuine non-200 / unreachable backend. `integrity_errors` (goal-desk-iter-16,
+// J-12) passes through `res.json()` verbatim — no function-body change needed, just the widened
+// `DeskReconcileRunsListResult` type.
 export async function fetchDeskReconcileRuns(): Promise<{
   ok: boolean;
   data: DeskReconcileRunsListResult | null;
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 7ce9eba..80471cc 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -951,10 +951,13 @@ export interface DeskTopupRun extends DeskTopupRunMeta {
 
 // `GET /research/desk/topup/runs` -- honest-empty-or-populated, HTTP 200 always, never 404.
 // `latest === null` iff no top-up run has EVER reached a terminal state -- the page's ONE
-// discriminator for the "No top-up runs recorded yet." empty state.
+// discriminator for the "No top-up runs recorded yet." empty state. `integrity_errors`
+// (goal-desk-iter-16, J-12) mirrors `DeskScreenListResult`/`DeskUniverseResult`'s identical field
+// -- surfaced from the store's own `.list()` return, never silently dropped.
 export interface DeskTopupRunsListResult {
   runs: DeskTopupRunMeta[];
   latest: DeskTopupRun | null;
+  integrity_errors: { file: string; error: string }[];
 }
 
 // era-desk-iter-14 (J-10) -- the coverage-index reconciliation: drift classification between the
@@ -1015,9 +1018,13 @@ export interface DeskReconcileRun extends DeskReconcileRunMeta {
 // `GET /research/desk/coverage/reconcile/runs` -- honest-empty-or-populated, HTTP 200 always,
 // never 404. `latest === null` iff no reconciliation has EVER reached a terminal state -- the
 // page's ONE discriminator for the "No reconciliation run recorded yet." empty state.
+// `integrity_errors` (goal-desk-iter-16, J-12) mirrors `DeskScreenListResult`/
+// `DeskUniverseResult`'s identical field -- surfaced from the store's own `.list()` return, never
+// silently dropped.
 export interface DeskReconcileRunsListResult {
   runs: DeskReconcileRunMeta[];
   latest: DeskReconcileRun | null;
+  integrity_errors: { file: string; error: string }[];
 }
 
 // The reconciliation compute manager's job snapshot, served VERBATIM by GET/POST
```
