# goal-tradable_wall-iter-9 Functional Test Plan

**Phase:** goal-tradable_wall-iter-9  
**Date:** 2026-07-15  
**Frontend Present:** yes

## Phase Goal

Make the era's central "what actually profits" deliverable observable: wrap `edge_report.py`'s ~10+h backtest sweep in a rebuildable, dataset-checksum-keyed result cache so `GET /research/edge-report` (and its MCP proxy) return the full 3-way register within an interactive time budget on a warm cache — byte-identical to a fresh compute, never a second source of truth, champion untouched.

## Test Cases

### TC-01 — Warm-cache Edge Report renders in interactive time

**Type:** browser  
**Preconditions:** Backend is running with a pre-warmed edge-report cache (initial compute completed); `/structure` page is accessible.

**Steps:**
1. Navigate to `/structure` in Chrome.
2. Scroll to the Edge Report section.
3. Verify the section renders the 3-way comparison table (v1 / structure_tape / structure_tape_map).
4. Measure time from page load to first rendered report cell.

**Expected outcome:** Edge Report section renders all populated cells (or the honest all-`insufficient_sample`/empty state) verbatim from `GET /research/edge-report` within the interactive budget (≤5 seconds).  
**Pass criteria:** Screenshot shows fully-rendered Edge Report table with no loading spinner; time ≤ 5 seconds from page load to visible populated cells.

---

### TC-02 — Cold-cache Edge Report endpoint request completes

**Type:** api  
**Preconditions:** Cache has been cleared; backend is running.

**Steps:**
1. Send `curl -X GET http://localhost:8301/research/edge-report -H "Content-Type: application/json"`.
2. Capture HTTP status code and response body.
3. Verify response shape contains `cells: [...]` (even if empty or all-`insufficient_sample`).

**Expected outcome:** HTTP 200; response is valid JSON with edge-report structure (cells array, each cell with train/holdout/feed/strategy labels, or empty state).  
**Pass criteria:** Status code is 200; response body is valid JSON; structure conforms to the edge-report schema (no truncation or partial JSON).

---

### TC-03 — Determinism: warm-cache report byte-identical to fresh cleared compute

**Type:** api  
**Preconditions:** Backend running with a pre-warmed cache over a non-degenerate store (populated cells or all-`insufficient_sample`, not empty `cells: []`).

**Steps:**
1. Fetch `GET /research/edge-report` and store response as `result_warm.json`.
2. Clear the edge-report cache (delete persisted cache file or purge in-process state).
3. Fetch `GET /research/edge-report` again and store response as `result_fresh.json`.
4. Compare `result_warm.json` and `result_fresh.json` byte-for-byte (checksums, JSON object key order, numeric precision).

**Expected outcome:** Byte-identical JSON payloads (same cell counts, same strategy results, same `insufficient_sample` labels, same null baseline baseline, same assumptions).  
**Pass criteria:** `md5sum(result_warm.json) == md5sum(result_fresh.json)` (or other byte-identical proof); no fields dropped, no numeric rounding introduced.

---

### TC-04 — Concurrency: cold-cache concurrent reads never observe torn state

**Type:** api  
**Preconditions:** Backend running; edge-report cache is cold (cleared).

**Steps:**
1. Clear the edge-report cache.
2. Launch 3 concurrent requests to `GET /research/edge-report` from separate threads/processes.
3. Capture all responses and HTTP status codes.
4. For each response, verify it is either a complete valid edge-report JSON or an in-progress loading state; never a partial/truncated JSON object.

**Expected outcome:** All 3 concurrent requests receive either a complete valid edge-report response or an honest loading/empty state; no torn reads (partial JSON, mismatched array bounds, truncated cell objects).  
**Pass criteria:** Every response passes JSON validation; no response contains broken/truncated objects; at least one request completes the full compute (others may see the cached result).

---

### TC-05 — Cache key busting: dataset checksum change forces recompute

**Type:** api  
**Preconditions:** Backend running with a warm cache; a registered dataset is available.

**Steps:**
1. Fetch and record `GET /research/edge-report` and its response checksum (as `initial_result`).
2. Simulate a dataset registry change (modify the dataset entry in the registry, add/remove a dataset, or alter its checksum).
3. Fetch `GET /research/edge-report` again.
4. Verify the new response either reflects the new registry state or the cache was invalidated (recompute triggered).

**Expected outcome:** The cache key included the dataset checksums; changing the registry invalidates the key and forces a fresh compute.  
**Pass criteria:** The new response differs from the initial result (reflecting the new dataset state) or backend logs show a cache miss and recompute.

---

### TC-06 — Cache key busting: config fingerprint change forces recompute

**Type:** api  
**Preconditions:** Backend running with a warm cache; config `fingerprint == "4d665603569b9dbf"`.

**Steps:**
1. Fetch and record `GET /research/edge-report` (as `initial_result`).
2. Simulate a config change that would alter the fingerprint (e.g., via test override; do not mutate the actual config file).
3. Fetch `GET /research/edge-report` again.
4. Verify the cache key was invalidated and a recompute occurred.

**Expected outcome:** The cache is keyed on the current `config_fingerprint`; a fingerprint change invalidates the cache.  
**Pass criteria:** Backend logs show "cache miss" on the second request; recompute is triggered; fingerprint remains byte-identical to `4d665603569b9dbf` after the iteration (no persistent mutation).

---

### TC-07 — Durability: persisted cache survives simulated backend restart

**Type:** api  
**Preconditions:** Backend running; edge-report cache is warmed and persisted to disk.

**Steps:**
1. Fetch `GET /research/edge-report` and record the result (as `pre_restart`).
2. Stop the backend server.
3. Restart the backend server (simulating a restart without clearing the cache file).
4. Fetch `GET /research/edge-report` again and record the result (as `post_restart`).
5. Compare the two results byte-for-byte.

**Expected outcome:** The persisted cache on disk is loaded on restart; the result is byte-identical to the pre-restart result.  
**Pass criteria:** `post_restart == pre_restart` (byte-identical JSON); no re-computation required on restart.

---

### TC-08 — PnL-history append: keyless unit test of 3-way row composition

**Type:** artifact  
**Preconditions:** Unit test `test_pnl_ledger.py` exists and can execute in isolation (no committed `reports/pnl/pnl-history.md` mutation).

**Steps:**
1. Run `pytest apps/backend/tests/test_pnl_ledger.py::test_append_3way_comparison_row -v`.
2. Verify the test constructs a 3-way row from a mock edge-report (v1 vs structure_tape vs structure_tape_map).
3. Verify the row includes train/holdout separation (never pooled), feeds never pooled, n<5 → `insufficient_sample`, null baseline, and "simulated — not indicative of live results" register.
4. Verify the row can be re-rendered to markdown without mutation (byte-level no-op).

**Expected outcome:** Test passes; the appended row structure is correct; `reports/pnl/pnl-history.md` (committed file) remains unchanged.  
**Pass criteria:** Test exit code 0; row schema includes all required fields; committed pnl-history.md is unmodified.

---

### TC-09 — Frozen foundations: config fingerprint unchanged

**Type:** artifact  
**Preconditions:** Backend is running; code has been committed/built.

**Steps:**
1. Run `python3 -c "from apps.backend.app.config import config_fingerprint; print(config_fingerprint())"`.
2. Capture the output.

**Expected outcome:** The fingerprint is exactly `4d665603569b9dbf`.  
**Pass criteria:** Output is `4d665603569b9dbf`; no mutation of fingerprinted config fields.

---

### TC-10 — Frozen foundations: levels.py, setups.py, tradability.py byte-identical

**Type:** artifact  
**Preconditions:** Source code is checked out on the current branch.

**Steps:**
1. Compute SHA-256 checksums of `apps/backend/app/research/levels.py`, `apps/backend/app/research/setups.py`, `apps/backend/app/research/tradability.py`.
2. Compare against the baseline from iter-8 (if documented) or verify via git diff that no computation logic changed.

**Expected outcome:** Files are byte-identical or show only additive changes (new cache module, route wiring) — no mutation to computation.  
**Pass criteria:** `git diff HEAD~1 -- apps/backend/app/research/{levels,setups,tradability}.py` shows no changes (or only comment/docstring additions).

---

### TC-11 — Frozen foundations: v1 and structure_tape strategy code unchanged

**Type:** artifact  
**Preconditions:** Backend code is built.

**Steps:**
1. Run `pytest apps/backend/tests/test_edge_report.py::test_frozen_strategy_v1_byte_identical -v` (or equivalent equivalence test).
2. Run `pytest apps/backend/tests/test_edge_report.py::test_frozen_strategy_structure_tape_byte_identical -v`.

**Expected outcome:** Both tests pass; the strategies compute identical outputs on identical inputs compared to iter-8.  
**Pass criteria:** Test exit codes 0; no regression in strategy results.

---

### TC-12 — MCP edge_report proxy returns cache-served result byte-identical

**Type:** api  
**Preconditions:** Backend and MCP server are running.

**Steps:**
1. Fetch `GET /research/edge-report` from the HTTP backend (via curl).
2. Call the MCP `edge_report` tool (via the registered MCP interface).
3. Compare both responses.

**Expected outcome:** Byte-identical JSON payloads; the MCP proxy is a pure passthrough (no recomputation, no filtering, no re-serialization).  
**Pass criteria:** Both responses are identical JSON (same checksum); existing MCP proxy test stays green.

---

### TC-13 — Edge Report Section renders J-05 Tradable Map page shell unregressed

**Type:** browser  
**Preconditions:** Frontend is running; `/structure` is accessible.

**Steps:**
1. Navigate to `/structure`.
2. Verify the Tradable Map section is displayed (default state, not raw-mode).
3. Verify the "raw toggle" is present and off-by-default.
4. Verify the "Case Studies" section is visible below the map.
5. Take a screenshot of the full structure page.

**Expected outcome:** All three elements (Tradable Map default view, toggle control, Case Studies) are rendered and unmodified from iter-8.  
**Pass criteria:** Screenshot shows Tradable Map in default state (not raw); toggle control is off; Case Studies section is visible.

---

### TC-14 — Cockpit chip and overlay render J-06 unregressed

**Type:** browser  
**Preconditions:** Frontend is running; a cockpit page is accessible (or the cockpit section exists on `/structure`).

**Steps:**
1. Navigate to the cockpit view (or the cockpit overlay on `/structure`).
2. Verify the chip (condensed state label) is rendered.
3. Verify the overlay (expanded view) is renderable without errors.
4. Take a screenshot.

**Expected outcome:** Cockpit chip and overlay are displayed and unmodified from iter-8.  
**Pass criteria:** Screenshots show both chip and overlay; no visual regressions or broken layouts.

---

### TC-15 — Backend unit test suite: new cache tests pass

**Type:** api  
**Preconditions:** Backend code is built; pytest is available.

**Steps:**
1. Run `pytest apps/backend/tests/test_edge_report_cache.py -v`.
2. Capture the output.

**Expected outcome:** All determinism, concurrency, durability, and key-busting tests pass.  
**Pass criteria:** Test exit code 0; all new test cases listed in the TESTING REQUIREMENTS section pass.

---

### TC-16 — Full backend suite: no regressions, no deletions, ~1348+ passing

**Type:** api  
**Preconditions:** Backend is built; all dependencies installed.

**Steps:**
1. Run `pytest apps/backend/tests/ -v --tb=short 2>&1 | tee test-report.log`.
2. Count passed, failed, skipped, and xpassed test counts.
3. Compare to iter-8 baseline: 1348 passed, 7 skipped (expect pass count ≥ 1348 + new tests).

**Expected outcome:** All prior tests remain passing; new cache tests are added (not deleted); exit code 0.  
**Pass criteria:** Exit code 0; passed count ≥ 1348; skipped count ≤ 7 (or unchanged); failed count 0; no test file deleted or marked skip.

---

### TC-17 — Anti-goal compliance: no credential/paid-SaaS/vocabulary drift

**Type:** artifact  
**Preconditions:** Code is committed to the branch.

**Steps:**
1. Run `bash scripts/automation/scan-report.sh --output=scan-report.md`.
2. Review the scan report for credential leaks, paid-SaaS references, or non-descriptive language ("profitable", "guaranteed", "buy/sell signals").

**Expected outcome:** Scan passes; no new credentials, no paid-SaaS drift, no vocabulary violations.  
**Pass criteria:** Scan exit code 0; no new violations logged.

---

### TC-18 — Dev handoff exists at required path

**Type:** artifact  
**Preconditions:** Phase implementation is complete.

**Steps:**
1. Check for the file `docs/handoffs/goal-tradable_wall-iter-9-dev.md`.
2. Verify it contains a summary of changes, decision rationale, and a pointer to the cached implementation.

**Expected outcome:** File exists and is non-empty.  
**Pass criteria:** File path exists; file size > 0; contains developer-facing summary.

---

## Summary

**Total test cases:** 18

- **Browser tests:** 3 (TC-01, TC-13, TC-14)
- **API tests:** 11 (TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-12, TC-15, TC-16, TC-17)
- **Artifact checks:** 4 (TC-09, TC-10, TC-11, TC-18)

**Key coverage areas:**

- **Cache correctness:** determinism, key-busting, durability, concurrency (TC-03–TC-07)
- **Single source of truth:** frozen strategies, MCP proxy byte-identity, config unchanged (TC-09–TC-12)
- **Frontend observability:** warm-cache render within budget, no regressions on adjacent surfaces (TC-01, TC-13–TC-14)
- **Data integrity:** PnL-history append format, no pooling, `insufficient_sample` gating (TC-08)
- **Regression prevention:** backend suite passing, no tests deleted, anti-goal compliance (TC-16–TC-17)
