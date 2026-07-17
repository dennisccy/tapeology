# goal-fast_wall-iter-2 Functional Test Plan

**Phase:** goal-fast_wall-iter-2  
**Date:** 2026-07-17  
**Frontend Present:** no

## Phase Goal

Ship J-02: verified-content caches (stat-keyed, tamper-safe) and a durable dataset-metadata index (`dataset_index.db`) so bar-series and dataset metadata reads stop re-verifying unchanged content on every call. The in-process stat-keyed caches accelerate all metadata-only operations (`get()`, `list()`) while ensuring full verification is never bypassed for load-events paths. The durable index survives backend restarts, eliminating cold-start re-parsing costs (~31.4s baseline → sub-second warm).

## Test Cases

### TC-01 — BarStore.get() zero-read warm hit (same file)

**Type:** api  
**Preconditions:** A `BarStore` is initialized with a test bar directory containing a single `.json` bar series file at path P with known stat `(size_s, mtime_ns)`.

**Steps:**
1. Call `BarStore.get(bar_series_id)` for the file; capture the returned dict D₁ and the file-read count via a counting spy on I/O syscalls.
2. Call `BarStore.get(bar_series_id)` a second time with the file's stat unchanged.
3. Record the file-read count on the second call; capture the returned dict D₂.

**Expected outcome:** Zero additional file reads occur between call 1 and call 2 (spy shows 0 reads on second `get`).

**Pass criteria:** Spy records exactly 0 file reads on the second `get()` call; D₂ equals D₁ in content.

---

### TC-02 — BarStore.list() zero-read warm hit (full directory)

**Type:** api  
**Preconditions:** A `BarStore` is initialized with a test directory containing N healthy bar-series `.json` files, all with unchanged stats since initialization.

**Steps:**
1. Call `BarStore.list()` once; capture the returned list and the file-read count.
2. Call `BarStore.list()` again with all file stats unchanged.
3. Record the file-read count on the second call.

**Expected outcome:** Zero additional file reads occur across any of the N files on the second call.

**Pass criteria:** Spy records exactly 0 reads of any `.json` file on the second `list()` call.

---

### TC-03 — BarStore.get() detects tampering after warm read

**Type:** api  
**Preconditions:** A `BarStore` has served `get(bar_series_id)` once for file P (warm cache established). File P is currently intact on disk.

**Steps:**
1. Corrupt file P on disk (modify its bytes so its checksum no longer matches).
2. Call `BarStore.get(bar_series_id)` again.
3. Observe the exception and its type.

**Expected outcome:** A `BarSeriesIntegrityError` is raised, not a stale-good cache hit.

**Pass criteria:** Exception type is exactly `BarSeriesIntegrityError`; the exception is not suppressed and the corrupt data is never returned.

---

### TC-04 — DatasetStore.list() reports tampered file in errors list

**Type:** api  
**Preconditions:** A `DatasetStore` has served `list()` once, warm-caching the metadata of dataset Y. The metadata cache is warm (Y's file stat is unchanged).

**Steps:**
1. Corrupt dataset Y's `.json` file on disk.
2. Call `DatasetStore.list()` again.
3. Inspect the returned `errors` list and the healthy `records` list.

**Expected outcome:** Dataset Y appears in the returned `errors` list (not in `records`); the tampered file is never served as valid cached metadata.

**Pass criteria:** Y is present in `errors` with a `DatasetIntegrityError` detail; Y is absent from `records`.

---

### TC-05 — Racy-write guard refuses freshly-written file (both stores)

**Type:** api  
**Preconditions:** A test file is written to disk and immediately read via `BarStore.get()` or `DatasetStore.get()` within a ~2-second window after the write.

**Steps:**
1. Write file F to disk at time T₀.
2. Call `BarStore.get()` or `DatasetStore.get()` at time T₁ (T₁ - T₀ < ~2s); record the read count.
3. Call the same method again at time T₂ (T₂ - T₀ < ~2s) with F's bytes unchanged.
4. Record the second read count.

**Expected outcome:** The second call re-reads file F (the racy-write guard refuses to cache a freshly-written file).

**Pass criteria:** Spy records a nonzero read count on the second call (guard rejects cache within the ~2s window).

---

### TC-06 — BarStore.get() returns per-call row copies (isolation)

**Type:** api  
**Preconditions:** A `BarStore` has served `get(bar_series_id)` once, warm-caching the bar data (cache is warm, stat unchanged).

**Steps:**
1. Call `BarStore.get(bar_series_id)` once; receive dict D₁ with key `"bars"` pointing to a list L₁.
2. Mutate L₁ in place (append, modify, or delete an element).
3. Call `BarStore.get(bar_series_id)` immediately after (warm-cache hit); receive dict D₂ with list L₂.
4. Compare L₂ to the original unmutated content.

**Expected outcome:** L₂ equals the original unmutated bar list; the caller's mutation to L₁ did not poison the cache.

**Pass criteria:** L₂ is byte-equal to the known original bar list; no mutation from step 2 appears in D₂.

---

### TC-07 — DatasetStore.load_events() and replay() always full-verify

**Type:** api  
**Preconditions:** A `DatasetStore` has warm-cached metadata for dataset Z via a prior `list()` or `get()` call.

**Steps:**
1. Call `DatasetStore.load_events(Z)` or `DatasetStore.replay(Z, config)` while the metadata cache is warm.
2. Spy on I/O reads and checksum-computation calls during the call.
3. Record all observed reads and checksums computed.

**Expected outcome:** Despite warm metadata cache, a full file read and both checksums (SHA256 for size, SHA256 for content) are recomputed on the call.

**Pass criteria:** Spy records at least one full file read of Z's `.json` file; both checksums are recomputed (never served from cache).

---

### TC-08 — GET /research/datasets byte-identical warm-cache vs fresh

**Type:** api  
**Preconditions:** A test dataset registry is populated and accessible via `GET /research/datasets`. The `DatasetStore`'s metadata cache is cold.

**Steps:**
1. Call `GET /research/datasets` (cold cache); save the raw HTTP response body as B₁.
2. Call the test-only cache-reset helper to force a full fresh-verify pass on the cache.
3. Call `GET /research/datasets` again; save the raw HTTP response body as B₂.
4. Also call the MCP `datasets` tool proxy immediately after the warm call in step 3; save its response body as B₃.
5. Compare B₁, B₂, and B₃ byte-by-byte.

**Expected outcome:** B₁ == B₂ (HTTP response bytes are identical); B₃ == B₂ (MCP proxy bytes match the warm REST response).

**Pass criteria:** All three responses are byte-identical; no JSON field ordering or content drift. **Note:** Run this test both standalone and inside the full `test_mcp_server.py` module per the applied lesson (iter-1 order-coupling finding).

---

### TC-09 — Fresh DatasetStore (simulated restart) serves from durable index, zero reads

**Type:** api  
**Preconditions:** A `DatasetStore` process has verified N datasets and published their metadata into `dataset_index.db`. Both the in-process cache and the durable DB are populated and consistent.

**Steps:**
1. Create a brand-new `DatasetStore` instance (fresh in-process cache, same `index_db_path`, same `root`), simulating a backend restart.
2. Spy on I/O reads to dataset `.json` files.
3. Call `.list()` on the new instance.
4. Compare the returned records (sort-key-normalized JSON) to a reference from-scratch `.list()` call on a `DatasetStore` with no index DB.

**Expected outcome:** Zero reads of the underlying `.json` dataset files; the durable index supplies all N metadata records directly. The returned records are byte-identical (`json.dumps(sort_keys=True)`) to the reference.

**Pass criteria:** Spy records 0 reads of any `.json` files; returned records are exactly equal (`sort_keys=True`).

---

### TC-10 — Deleting dataset_index.db rebuilds in one pass, no data loss

**Type:** api  
**Preconditions:** A `DatasetStore` is operating with a populated `dataset_index.db` (N rows, N matching `.json` files in the registry, all intact).

**Steps:**
1. Delete the `dataset_index.db` file from disk (all `.json` files remain intact).
2. Spy on I/O reads to the N dataset files.
3. Create a fresh `DatasetStore` instance (same root, same `index_db_path`) and call `.list()`.
4. Check that `dataset_index.db` exists again after the call; count its rows.

**Expected outcome:** The call succeeds with no exception; each of the N files is fully re-verified exactly once (spy records N reads); `dataset_index.db` exists afterward with N rows (repopulated).

**Pass criteria:** No exception raised; spy records exactly N file reads (one per file); DB is recreated with N rows; all dataset records are returned (no data loss).

---

### TC-11 — BarStore.root is a public read-only property

**Type:** api  
**Preconditions:** A `BarStore` is constructed with a root directory path R.

**Steps:**
1. Access the `.root` property on the `BarStore` instance.
2. Verify it is a public property (no leading underscore), not a method.
3. Attempt to assign a new value to `.root` (should fail).

**Expected outcome:** `.root` returns the resolved path of R; assignment raises `AttributeError` (read-only).

**Pass criteria:** `.root` returns a string equal to `Path(R).resolve()`; assignment raises `AttributeError`.

---

### TC-12 — Autouse conftest fixture prevents cross-test cache leakage

**Type:** api  
**Preconditions:** The new autouse fixture is active in `conftest.py`. Two independent tests are written, each using a unique `tmp_path` root and registering distinct test content.

**Steps:**
1. Test A constructs a `BarStore` with its own `tmp_path` root, registers some bar data, and calls `get()` (warm cache).
2. Autouse fixture runs and resets both caches.
3. Test B constructs a `BarStore` with a different `tmp_path` root, registers different bar data.
4. Spy on I/O in Test B's first `get()` call.
5. Verify that Test B's first `get()` is a cache miss (real file read), not serving Test A's cached content.

**Expected outcome:** Test B's first `get()` reads from disk (spy records nonzero read count); it returns Test B's own content, not Test A's stale cache.

**Pass criteria:** Spy records a nonzero file read in Test B's first `get()`; returned content matches Test B's registry (not Test A's).

---

### TC-13 — Full backend suite green, fingerprint unchanged

**Type:** api  
**Preconditions:** All changes from this iteration are implemented and integrated.

**Steps:**
1. Run the full backend unit/integration test suite: `pytest apps/backend/tests/ -v`.
2. Record pass/fail counts and any skipped tests.
3. Call `config.config_fingerprint()` and record its value.

**Expected outcome:** Zero test failures; zero newly-skipped or deleted tests (pre-existing skip counts unchanged); `config_fingerprint()` == `4d665603569b9dbf` (exactly as before this iteration).

**Pass criteria:** Exit code is 0 (all tests pass); fingerprint is exactly `4d665603569b9dbf`; no test deleted or newly skipped.

---

### TC-14 — GET /research/edge-report integrity errors still bubble (J-01 unchanged)

**Type:** api  
**Preconditions:** A dataset store has one file with integrity-error status in its `list()` result (an unrelated corrupt file present in the registry).

**Steps:**
1. Call `GET /research/edge-report` via the unchanged route (no J-02 code change to this route).
2. Inspect the HTTP response status and body.

**Expected outcome:** HTTP 500 response with `"integrity"` present in the `detail` field; the route's existing error path is unaffected by the new metadata cache.

**Pass criteria:** Status is 500; `detail` field contains substring `"integrity"` (the existing error message); the cache never masks the integrity error.

---

### TC-15 — GET /research/datasets cold→warm latency on real corpus (operator-verified, non-blocking)

**Type:** api  
**Preconditions:** The real operator corpus (18 datasets, 882MB) is available in the dev/QA environment. The backend is running.

**Steps:**
1. Clear both the in-process cache and `dataset_index.db` (simulating cold start).
2. Call `GET /research/datasets` and time the response.
3. Populate the cache (call `GET /research/datasets` again or wait for the index to be written).
4. Call `GET /research/datasets` a third time (warm cache, index populated) and time the response.
5. Record both timings.

**Expected outcome:** Warm latency is under 1 second; cold latency is ~31.4 seconds (the baseline). Warm / cold ratio shows at least 30× improvement.

**Pass criteria:** Warm latency < 1s; cold latency documented as baseline (~31.4s). **Note:** This test is encouraged supplementary evidence (operator-verified) but is NOT a blocking gate if the real corpus is unavailable. The keyless TC-1..TC-14 suite is the blocking gate.

---

## Summary

**Total test cases:** 15  
**API tests:** 15  
**Browser tests:** 0 (Frontend Present: no)  
**Artifact checks:** 0  

**Blocking gate (Definition of Done):** TC-1 through TC-14 must all pass.  
**Supplementary evidence (encouraged, non-blocking):** TC-15 (real-corpus timing).

All tests verify the core anti-goals: verified-content caches stay rebuildable (TC-9, TC-10), full verification is never bypassed for load paths (TC-7), tampering is always detected (TC-3, TC-4), and cached outputs are byte-identical to fresh computes (TC-8, TC-9). Cross-test isolation (TC-12) and racy-write safety (TC-5) complete the mechanical proof.
