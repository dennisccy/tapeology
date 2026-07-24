# goal-clean_slate-iter-1 Functional Test Plan

**Phase:** goal-clean_slate-iter-1  
**Date:** 2026-07-24  
**Frontend Present:** no

## Phase Goal

Delete the backend half of the journal/studies/performance surfaces — 14 routes, 11 modules, `JournalStore`'s journal-era methods, and their ~24 tests — after relocating two shared helpers byte-identically first, so every kept backend endpoint stays serving byte-identical data and deleted routes return HTTP 404; no user-visible change yet.

---

## Test Cases

### TC-01 — Baseline capture before deletion

**Type:** api  
**Preconditions:** Backend running on committed fixtures; no code changes made; `kept-route-baseline.txt` does not exist.

**Steps:**
1. Start the backend service
2. Curl every KEPT `/research`, `/tape`, `/meta` GET route (see list below)
3. For each route, capture the response status and body
4. Compute sha256 hash of each response body
5. Write all hashes to `runs/goal-session-clean_slate/iter-1/kept-route-baseline.txt` in format: `<route> <status> <sha256hash>`

**Expected outcome:**  
- All KEPT routes return HTTP 200
- All responses are valid JSON
- All hashes are written to the baseline file

**Pass criteria:**  
- File `kept-route-baseline.txt` exists with entries for at least 12 kept routes (all endpoints in `/research`, `/tape`, `/meta` except the 14 DELETE routes listed in I-1)

**Routes to capture:**  
- `GET /research/bars` (all timeframes/symbols)
- `GET /research/levels`
- `GET /research/tradability`
- `GET /research/setups`
- `GET /research/backtests`
- `GET /research/pnl-ledger`
- `GET /research/profiles`
- `GET /research/strategies`
- `GET /research/edge-report`
- `GET /research/taxonomy` (baseline with current full payload)
- `GET /tape/*` (all endpoints)
- `GET /meta/*` (all endpoints)

---

### TC-02 — Relocation and suite green before deletion

**Type:** api  
**Preconditions:** Both relocations have been applied:
- `r_basis` moved from `app/research/marks.py` to `app/research/backtests.py`
- `SOURCE_REFERENCE`, `SOURCE_HISTORICAL`, `REFERENCE_SOURCE_ID`, `_load_reference_window` moved from `app/research/studies.py` to `app/research/datasets.py`
- Plus the third relocation (STATUS_* constants and state helpers) moved to `backtests.py` (per execution plan inventory gap)
- All importers updated: `datasets.py`, `backtests.py`, `pnl_baseline.py`, `edge_report.py`, and test files

**Steps:**
1. Verify the three relocation moves are in place (grep the destination files)
2. Run the full backend test suite: `cd apps/backend && python -m pytest tests/ -q`
3. Capture exit code and test count summary

**Expected outcome:**  
- All tests pass (0 failed, 0 errors)
- Test count is the same or higher than baseline (no tests deleted yet)
- No import errors when importing `backtests`, `datasets`, `pnl_baseline`, or `edge_report`

**Pass criteria:**  
- Exit code is 0
- Output shows "X passed" with zero failures/errors
- Output does NOT show any ImportError for the moved symbols

---

### TC-03 — Deleted routes return 404

**Type:** api  
**Preconditions:** 
- The 14 I-1 DELETE routes have been removed from `app/research/routes.py`
- Backend running on the modified code

**Steps:**
1. For each of the 14 deleted routes, issue its correct HTTP verb
2. Capture response status code
3. Record all results

**Expected outcome:**  
- Each deleted route returns exactly HTTP 404
- Response body is honest 404 (e.g., `{"detail": "Not Found"}` per FastAPI default)

**Pass criteria:**  
- All 14 routes return status 404
- No route returns 200, 500, 405, or a redirect

**Deleted routes to verify:**  
1. `GET /research/analytics`
2. `GET /research/thesis/active`
3. `GET /research/hints/active`
4. `GET /research/hints`
5. `GET /research/journal`
6. `GET /research/journal/{thesis_id}`
7. `POST /research/thesis`
8. `POST /research/thesis/{thesis_id}/resolve`
9. `POST /research/thesis/{thesis_id}/action`
10. `POST /research/thesis/{thesis_id}/review`
11. `POST /research/studies`
12. `GET /research/studies`
13. `GET /research/studies/{study_id}`
14. `POST /research/studies/{study_id}/cancel`

---

### TC-04 — Taxonomy slimmed correctly

**Type:** api  
**Preconditions:** `GET /research/taxonomy` has been SLIMMED per I-2 in `app/research/taxonomy.py`

**Steps:**
1. Curl `GET /research/taxonomy`
2. Parse JSON response
3. Verify presence of `feed_basis` block with at least one feed entry
4. Verify source labels are present for `sim`, `iex`, `sip`, `yahoo`
5. Search response for deleted label families: `verdict`, `thesis-status`, `stance`, `STUDY_COPY`

**Expected outcome:**  
- Response status 200
- Response body contains `feed_basis.feeds[]` array with feed entries
- Response contains source label entries for `sim`, `iex`, `sip`, `yahoo`
- Response does NOT contain any of the strings: `verdict`, `thesis-status`, `stance`, `STUDY_COPY`

**Pass criteria:**  
- `feed_basis` block present with ≥1 feed
- All four source labels (`sim`, `iex`, `sip`, `yahoo`) present
- Zero occurrences of deleted label families in the response body

---

### TC-05 — Kept routes remain byte-identical

**Type:** api  
**Preconditions:**
- All deletions and relocations complete
- `kept-route-baseline.txt` exists from TC-01
- Backend running on modified code

**Steps:**
1. Curl every KEPT route (same list as TC-01, excluding the 14 deleted routes)
2. For each route, compute sha256 of response body
3. Compare each hash against the baseline from TC-01
4. Except for `/research/taxonomy`, every hash must match exactly

**Expected outcome:**  
- All kept routes return HTTP 200
- All response hashes match the TC-01 baseline
- `GET /research/taxonomy` response may differ in size/content (payload shrink is expected)

**Pass criteria:**  
- 100% of non-taxonomy kept routes have byte-identical hashes to baseline
- `GET /research/taxonomy` returns 200 and response contains the slimmed structure (TC-04 verified)

---

### TC-06 — Deleted modules have zero live imports

**Type:** artifact  
**Preconditions:** All 11 journal-era modules deleted from `apps/backend/app/research/`:
- `journal_rows.py`
- `monitor.py`
- `hints.py`
- `stance.py`
- `verdict.py`
- `grades.py`
- `marks.py`
- `excursions.py`
- `execution_checks.py`
- `analytics.py`
- `studies.py`

**Steps:**
1. For each module name M, run: `grep -rn "from .M import\|from app.research.M import\|import M" apps/`
2. Record any hits
3. Whitelist hits that are inside `reports/**`, `runs/**`, or `docs/goal-archive/**` (these are allowed)
4. Verify zero hits remain outside the whitelisted paths

**Expected outcome:**  
- Each module grep returns zero hits, OR
- All hits are in whitelisted directories (`reports/`, `runs/`, `docs/goal-archive/`)

**Pass criteria:**  
- No live imports of any deleted module in `apps/backend/app/**` or `apps/frontend/**`
- No import errors when running the test suite

---

### TC-07 — JournalStore KEEP methods intact

**Type:** api  
**Preconditions:** 
- `JournalStore`'s journal-era methods and dataclasses deleted per I-3
- `JournalStore`'s I-3 KEEP methods remain: `insert_backtest`, `append_pnl_ledger_row`, `get_champion_pointer`, `list_pnl_ledger`
- Backend running on modified code
- Test suite exercising these methods

**Steps:**
1. Run the backend test suite: `cd apps/backend && python -m pytest tests/ -q`
2. Verify all tests using `insert_backtest`, `append_pnl_ledger_row`, `get_champion_pointer`, `list_pnl_ledger` pass
3. Record return shapes from any integration test that exercises these methods
4. Compare shapes against known expected types (e.g., `insert_backtest` returns BacktestRecord, `list_pnl_ledger` returns list of PnLLedgerRow)

**Expected outcome:**  
- All tests exercise these methods without ImportError or AttributeError
- Methods return expected shapes
- Zero test failures on KEEP method tests

**Pass criteria:**  
- Exit code 0 from test suite
- No "AttributeError: 'JournalStore' has no attribute 'insert_backtest'" or similar
- KEEP methods return the same types and structures as before deletion

---

### TC-08 — Test suite reflects deletions

**Type:** api  
**Preconditions:**
- ~24 journal-era test files deleted
- 5 backend test files updated per I-8 (reduced scope):
  - `test_research_api.py`
  - `test_research_store.py`
  - `test_studies_reference.py` (reworked per execution plan gap)
  - `conftest.py`
  - `test_copy_discipline.py` (served-copy walk only, not frontend-literal walk)

**Steps:**
1. Run backend tests: `cd apps/backend && python -m pytest tests/ -q`
2. Capture exit code and test count
3. Compare test count against baseline (iter-0: 1665 passed + 7 skipped = 1672 total)
4. Calculate expected count: 1672 - count of deleted test files' tests

**Expected outcome:**  
- All tests pass (0 failed, 0 errors)
- Test count is no higher than 1665 (the 7 skipped tests may persist)
- No regressions on kept tests

**Pass criteria:**  
- Exit code 0
- Collected test count ≤ 1665 (accounting for deletions)
- Zero new tests added that would inflate the count

---

### TC-09 — Config fingerprint unchanged

**Type:** artifact  
**Preconditions:** No `Config` fields or methods touched; no `config_fingerprint` changes this iteration (J-04's job only)

**Steps:**
1. Run: `python -c "from app.config import Config; print(Config().config_fingerprint())"`
2. Capture output

**Expected outcome:**  
- Output prints exactly: `4d665603569b9dbf`

**Pass criteria:**  
- Output is `4d665603569b9dbf` with no extra whitespace or characters

---

### TC-10 — Fingerprint pins unchanged

**Type:** artifact  
**Preconditions:** All 13 fingerprint pin assertion sites (in unit/integration tests) left byte-unmodified

**Steps:**
1. Check the 13 pinned assertion lines against the baseline commit `fa76460`:
   - `test_timeframe_history_api.py:194`
   - `test_levels.py:718`
   - `test_tradability.py:370`
   - `test_backtests.py:416`
   - `test_backtests.py:1485`
   - `test_profile_equivalence.py:114`
   - `test_pnl_scan.py:193`
   - `test_pnl_scan.py:266`
   - `test_pnl_scan.py:569`
   - `test_pnl_scan.py:646`
   - `test_edge_report.py:213`
   - `test_setups.py:409`
   - `test_setups.py:779`
2. Run git diff to verify these lines are identical

**Expected outcome:**  
- All 13 lines show no changes
- No assertion values modified
- No import or structure changes on these lines

**Pass criteria:**  
- `git diff fa76460 HEAD -- <file>:<line>` shows no differences for all 13 pinned sites

---

### TC-11 — No historical records touched

**Type:** artifact  
**Preconditions:** Iteration complete; full diff available

**Steps:**
1. Check `git diff` for any changes in:
   - `docs/goal-archive/`
   - `runs/goal-session-*` (except this iteration's new `iter-1/` artifacts)
   - `reports/goal-session-*-delivered.md`
   - `journal.db` (any existing rows or tables)
2. Record any unexpected changes

**Expected outcome:**  
- Zero lines edited in these historical directories
- Only this iteration's new `iter-1/` run artifacts are added under `runs/goal-session-clean_slate/`

**Pass criteria:**  
- No diff lines shown for `docs/goal-archive/**`
- No diff lines shown for `runs/goal-session-*` outside this iteration's own new `iter-1/` folder
- No diff lines shown for `reports/goal-session-*-delivered.md`
- No diff lines touching `journal.db` schema or rows

---

## Test Execution Matrix

| Test ID | Name | Type | Backend Service Needed | Status |
|---------|------|------|------------------------|--------|
| TC-01 | Baseline capture | api | yes (committed fixtures) | |
| TC-02 | Relocations + suite green | api | yes | |
| TC-03 | Deleted routes 404 | api | yes (modified code) | |
| TC-04 | Taxonomy slimmed | api | yes | |
| TC-05 | Kept routes identical | api | yes | |
| TC-06 | No live imports | artifact | no (grep only) | |
| TC-07 | KEEP methods intact | api | yes | |
| TC-08 | Suite reflects deletions | api | yes | |
| TC-09 | Fingerprint unchanged | artifact | no (local check) | |
| TC-10 | Pins unchanged | artifact | no (git diff) | |
| TC-11 | No historical records | artifact | no (git diff) | |

---

## Summary

**Total test cases:** 11  
**API tests:** 7 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-07, TC-08)  
**Artifact checks:** 4 (TC-06, TC-09, TC-10, TC-11)

**Critical test sequence:**
1. **TC-01** — Capture baseline before any changes
2. **TC-02** — Prove relocations work and suite is green before deletions
3. **TC-03, TC-04** — Verify deletions/slimming succeeded
4. **TC-05** — Verify byte-identity of kept routes (core acceptance criterion)
5. **TC-06, TC-07, TC-08** — Verify module cleanup, KEEP methods, test suite state
6. **TC-09, TC-10, TC-11** — Verify no unintended side effects (fingerprint, pins, records)

**Test environment:** Backend only; no frontend required (`Frontend Present: no`). All tests are curl/pytest/git-verifiable.
