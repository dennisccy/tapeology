# goal-desk-iter-1 Functional Test Plan

**Phase:** goal-desk-iter-1
**Date:** 2026-07-25
**Frontend Present:** no

## Phase Goal

Add a backend-only universe subsystem — a Wikipedia vendor seam, an honest parser, and an append-only checksummed snapshot store — so `POST /research/desk/universe/fetch` registers a validated S&P 100 membership snapshot and `GET /research/desk/universe` serves it, unblocking J-02 through J-06.

## Test Cases

### TC-01 — Empty universe state

**Type:** api
**Preconditions:** A test-scoped universe directory is fresh (no snapshots registered); TAPEOLOGY_UNIVERSE_DIR env is set to the test directory

**Steps:**
1. Call `GET /research/desk/universe` against the running backend
2. Inspect the response body

**Expected outcome:** HTTP 200 response with an explicitly empty payload (no snapshots listed, no latest membership defined)
**Pass criteria:** Response code is 200; response body contains empty snapshots list (e.g., `{"snapshots": [], "latest": null}` or similar); status is NOT 404

---

### TC-02 — Valid fixture registration

**Type:** api
**Preconditions:** A test-scoped universe directory is fresh; the valid constituents-table HTML fixture (90–110 tickers, including at least one dual-class ticker like BRK.B) is committed under `apps/backend/tests/fixtures/universe/`; the fake vendor seam is injected to return this fixture on `POST /research/desk/universe/fetch`

**Steps:**
1. Call `POST /research/desk/universe/fetch` with the injected fake vendor
2. Inspect the response body and the filesystem
3. Call `GET /research/desk/universe` and inspect the updated payload

**Expected outcome:** 
- `POST` returns HTTP 200 with a body containing: a 12-character content checksum, a member count between 90 and 110 (inclusive), and the normalized+sorted ticker list
- The response includes normalized form (e.g., `BRK-B`, never `BRK.B`) with no duplicate entries
- A snapshot JSON file is written to `.data/universe/universe-<YYYY-MM-DD>-<checksum12>.json`
- `GET /research/desk/universe` lists that snapshot and returns its membership as `latest`

**Pass criteria:** Checksum is exactly 12 characters; member count is between 90 and 110; `BRK.B` is normalized to `BRK-B`; no duplicates in the normalized list; file exists on disk with expected naming; `GET` response includes the snapshot in the list and as latest

---

### TC-03 — Latest snapshot retrieval after registration

**Type:** api
**Preconditions:** TC-02 has completed and a snapshot is registered

**Steps:**
1. Call `GET /research/desk/universe`
2. Inspect the response body

**Expected outcome:** 
- Response includes the snapshot in the snapshots list (with date, checksum, member count)
- Response includes a `latest` field with the membership from the registered snapshot

**Pass criteria:** Snapshots list contains at least one entry; `latest` field is non-null and contains the member list as an array; member count in the snapshot metadata matches the actual member count in `latest`

---

### TC-04 — Corrupted fixture rejected with explicit error

**Type:** api
**Preconditions:** A corrupted fixture (contains a ticker outside the `[A-Z.-]{1,6}` charset, OR has a total row count outside 90–110) is committed under `apps/backend/tests/fixtures/universe/`; the fake vendor seam is injected to return this corrupted fixture; a baseline `GET /research/desk/universe` is called first to record the state

**Steps:**
1. Call `POST /research/desk/universe/fetch` with the fake vendor returning the corrupted fixture
2. Inspect the response status code and error body
3. Call `GET /research/desk/universe` again and verify the store is unchanged

**Expected outcome:** 
- `POST` returns HTTP 4xx (e.g., 400, 422) with an explicit error message naming the specific validation failure (e.g., "invalid ticker charset" or "member count 50 outside bounds [90, 110]")
- No new snapshot file is written to `.data/universe/`
- A subsequent `GET` returns the same snapshots list as the baseline

**Pass criteria:** HTTP status is 4xx; error body names the specific failure (not vague or generic); zero new files created in `.data/universe/`; subsequent GET is identical to baseline

---

### TC-05 — Duplicate content refused, file not rewritten

**Type:** api
**Preconditions:** TC-02 has completed and a snapshot for the valid fixture is registered; the snapshot file path and its content checksum are known

**Steps:**
1. Capture the file modification time (mtime) and byte content of the snapshot file from TC-02
2. Call `POST /research/desk/universe/fetch` again with the IDENTICAL valid fixture (injected via the fake vendor)
3. Capture the file mtime and byte content again
4. Inspect the response status code and body

**Expected outcome:** 
- `POST` returns HTTP 409 (or similar 4xx refusal code) with an explicit message naming the already-registered snapshot (e.g., "Snapshot already registered: universe-2026-07-25-abc123def456.json")
- The snapshot file mtime and content are byte-identical to the baseline (no rewrite)

**Pass criteria:** HTTP status is 409; response body names the existing snapshot by filename or checksum; file mtime is unchanged; file byte-content is identical to baseline

---

### TC-06 — Normalization and raw-form preservation

**Type:** api
**Preconditions:** TC-02 has completed; the fixture contained `BRK.B` and possibly `BF.B`

**Steps:**
1. Load the registered snapshot JSON file from disk
2. Inspect the normalized membership list and metadata structure

**Expected outcome:** 
- The normalized membership list contains `BRK-B` (never `BRK.B`)
- If `BF.B` is in the fixture, it is normalized to `BF-B` in the membership list
- The raw/original form (`BRK.B`, `BF.B`) is preserved in the snapshot's metadata (e.g., a `raw_forms` or equivalent field)
- No duplicate entries exist in the normalized list (e.g., if both `BRK.B` and `BRK` somehow appeared, deduping ensures only `BRK-B` is listed)

**Pass criteria:** Normalized membership contains only dashes (`BRK-B`), never dots; raw forms are stored separately; normalized list has no duplicate entries; sorted alphabetically

---

### TC-07 — Universe store isolation from dataset store (T-3 guard)

**Type:** artifact
**Preconditions:** The implementation is complete and source code is committed

**Steps:**
1. Run: `grep -r "from.*research\.datasets import\|from.*datasets import\|DatasetStore" apps/backend/app/research/desk_universe.py` (or whatever the universe module is named)
2. Inspect the grep results

**Expected outcome:** Zero matches — the universe module does not import the dataset registration function or `DatasetStore`

**Pass criteria:** grep returns no results (exit code 1); universe module is entirely separate from dataset-store machinery

---

### TC-08 — Fingerprint stability after Config field addition

**Type:** api
**Preconditions:** The new Config fields (`desk_universe_source_url`, `desk_universe_min_members`, `desk_universe_max_members`) are added to `config.py` and included in the exclusion set; the backend is running with the committed implementation

**Steps:**
1. Call the backend's Config introspection endpoint or run `python3 -c "from app.config import Config; print(Config().config_fingerprint())"`
2. Compare the output to the baseline `08e471b10130e1e2`

**Expected outcome:** The fingerprint is exactly `08e471b10130e1e2` (unchanged from the pre-iteration value)

**Pass criteria:** Fingerprint string matches `08e471b10130e1e2` exactly

---

### TC-09 — Counter-test for Config field integration

**Type:** api
**Preconditions:** TC-08 passes; the implementation is complete; a counter-test override mechanism exists (e.g., via env var or test-injection)

**Steps:**
1. Override `desk_universe_min_members` to a value higher than the actual member count in the valid fixture (e.g., set it to 150 when the fixture has 100 members)
2. Call `POST /research/desk/universe/fetch` with the SAME valid fixture from TC-02
3. Inspect the response

**Expected outcome:** 
- `POST` returns HTTP 4xx with an error message indicating the member count is out of bounds (e.g., "member count 100 outside bounds [150, 110]")
- The field is demonstrably live-wired into the validation logic
- Fingerprint (TC-08) still equals `08e471b10130e1e2` (the override does not change the pin)

**Pass criteria:** Request fails with count-out-of-bounds error; error message reflects the overridden min threshold; fingerprint is unchanged from TC-08

---

### TC-10 — Provenance embedding in snapshot payload

**Type:** artifact
**Preconditions:** TC-02 has completed and a snapshot is registered; the three Config field values at registration time are known

**Steps:**
1. Load the registered snapshot JSON file from disk or retrieve it via `GET /research/desk/universe`
2. Inspect the snapshot's metadata/payload structure for Config-field values

**Expected outcome:** 
- The snapshot payload embeds the exact three Config field values used at registration:
  - `desk_universe_source_url` (the Wikipedia URL or equivalent)
  - `desk_universe_min_members` (e.g., 90)
  - `desk_universe_max_members` (e.g., 110)
- These values are readable in the served JSON payload

**Pass criteria:** All three fields are present in the snapshot JSON; values match the Config values used at registration time; provenance is human-readable and complete

---

### TC-11 — Kept-route regression check (J-07 backend subset)

**Type:** api
**Preconditions:** 
- The backend is running with the pre-iteration codebase
- A baseline sha256 hash is captured for every existing `/research`, `/tape`, `/meta` GET route
- The backend is rebuilt/restarted with the post-iteration implementation

**Steps:**
1. With the pre-iteration backend running, for each of these routes, capture the full response body and compute sha256:
   - `GET /research/setups` (with default query params)
   - `GET /research/tradability?symbol=AAPL` (or equivalent; list all covered GET routes under `/research/`)
   - `GET /research/bars` (GET endpoints only; skip POST)
   - `GET /tape/history` (or all GET `/tape` routes)
   - `GET /meta/ui-routes` (and other GET `/meta` routes)
2. Document the sha256 hashes as the pre-iteration baseline
3. Restart the backend with the post-iteration implementation
4. Re-capture the response bodies and hashes for the same routes
5. Compare each post-iteration hash to its pre-iteration baseline

**Expected outcome:** Every hash is identical to the pre-iteration baseline; zero routes have changed their output

**Pass criteria:** All sha256 hashes match exactly; no route output has been modified; only NEW routes (universe fetch/get) are added, existing routes are byte-identical

---

### TC-12 — Full test suite pass rate

**Type:** artifact
**Preconditions:** The implementation is complete; the backend source is committed

**Steps:**
1. Run the full backend test suite: `cd apps/backend && pytest -v --tb=short`
2. Capture the final summary line showing pass/skip/fail counts

**Expected outcome:** 
- At least 1169 tests passed
- Exactly 7 tests skipped
- 0 tests failed
- 0 errors

**Pass criteria:** Output includes a line like "1169 passed, 7 skipped in X.XXs"; no failures or errors

---

### TC-13 — Hermetic default suite (zero network calls)

**Type:** artifact
**Preconditions:** The implementation is complete; test collection includes the universe tests

**Steps:**
1. Run the default test suite (without the `integration` marker): `cd apps/backend && pytest -v -m "not integration"`
2. Inspect the test output and network activity logs (if any)

**Expected outcome:** 
- All tests pass (or skip) as expected
- Zero tests perform a live network call to Wikipedia or any external URL
- Only fixture HTML is used; the fake vendor seam is injected

**Pass criteria:** Test count matches expectations; no network-call evidence in logs; fixture-based tests only

---

### TC-14 — Live Wikipedia integration test outcome

**Type:** api
**Preconditions:** 
- The implementation is complete and committed
- The `@pytest.mark.integration`-gated test is present in the test suite
- This test is run at least once during this iteration, either manually or as part of an integration test pass

**Steps:**
1. Run the integration test (with network enabled): `cd apps/backend && pytest -v -m integration tests/test_desk_universe_api.py::test_fetch_live_wikipedia` (or equivalent)
2. Record the outcome: success + member count, or the specific failure reason

**Expected outcome:** 
- If successful: the test reports the exact number of members parsed (should be between 90 and 110)
- If failed: the test reports a specific, honest failure reason (e.g., "no network connectivity", "bot detection (HTTP 403)", "page layout changed — table not found")
- The outcome is documented explicitly in `docs/handoffs/goal-desk-iter-1-dev.md`

**Pass criteria:** 
- Outcome is explicitly recorded in the dev handoff (success or specific failure)
- No vague "test skipped" or "unknown" outcomes — the attempt was made and the result is stated
- If successful, member count is within bounds [90, 110]

---

## Summary

**Total test cases:** 14
**API tests:** 10 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-08, TC-09, TC-11, TC-13, TC-14)
**Artifact checks:** 4 (TC-07, TC-10, TC-12)

All test cases are backend-only; no browser/frontend testing is required (Frontend Present: no). The tests cover:
- Empty state and registration happy path
- Validation failures and duplicate detection
- Config field wiring and fingerprint stability
- Store isolation and data integrity
- Kept-route regression protection
- Suite pass rates and network hermiticity
- Live Wikipedia integration outcome reporting
