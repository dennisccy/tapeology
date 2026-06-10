# goal-i_will_be_super_rich_with_my_loved_ones-iter-5 Functional Test Plan

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-5
**Date:** 2026-06-10
**Frontend Present:** yes

## Phase Goal

Unblock the verdict engine by fixing the SQLite schema migration defect: `POST /research/thesis` returns 200 against the persistent dev DB (migrated in place to v2), the orphaned thesis is swept to expired, and all 12 target browser journeys (J-38, J-39–J-46, J-68) are proven against the real dev stack.

---

## Test Cases

### TC-01 — POST /research/thesis succeeds (200) on persistent dev DB after migration

**Type:** api
**Preconditions:** 
- Backend running against the persistent `apps/backend/tapeology_journal.db`
- Dev DB has been migrated (schema_version bumped to 2, verdict_events has rule_first_true_ts/price columns)
- A ticker is being watched on the watched instance (e.g., SIM-BUYER)

**Steps:**
1. Ensure backend is running and health endpoint (`GET /health`) returns 200
2. Watch a ticker: `curl -X POST http://localhost:8000/watch/SIM-BUYER -H "Content-Type: application/json" -d '{"mode": "sim"}'`
3. POST a thesis declaration: `curl -X POST http://localhost:8000/research/thesis -H "Content-Type: application/json" -d '{"ticker": "SIM-BUYER", "setup_type": "absorption_reversal", "direction": "long", "invalidation_price": 95.0}'`

**Expected outcome:** HTTP 200 response with a thesis object containing `id`, `setup_type`, `direction`, `invalidation_price`, `verdict` (initially "pending"), and `entry_risk_flags` array.

**Pass criteria:** Response status is exactly 200; response body is valid JSON; thesis object contains all required fields; no 503 errors.

---

### TC-02 — Orphaned thesis resolved to expired by startup sweep

**Type:** api
**Preconditions:**
- Backend has restarted and run the startup sweep
- Orphaned active thesis `4beae280…` exists in the dev DB with zero verdict_events rows

**Steps:**
1. Query the research journal endpoint: `curl -s http://localhost:8000/research/journal`
2. Filter for thesis ID `4beae280…` (or check via DB: `SELECT active, resolution FROM theses WHERE id = '4beae280…'`)
3. Attempt to declare a new thesis on SIM-BUYER: `curl -X POST http://localhost:8000/research/thesis -H "Content-Type: application/json" -d '{"ticker": "SIM-BUYER", "setup_type": "trend_continuation", "direction": "long", "invalidation_price": 90.0}'`

**Expected outcome:** 
- The orphaned thesis's `resolution` is set to `expired` (or its active flag is false)
- The row is NOT deleted (survives in the journal for audit)
- The new declaration succeeds with 200 (not 409)

**Pass criteria:** Orphaned thesis visible in journal with resolution = "expired" or active = false; new thesis declaration returns 200; no 409 error.

---

### TC-03 — Migration preserves old rows with NULL rule_first_true (append-only timeline)

**Type:** artifact
**Preconditions:**
- Backend opened against the committed v1-schema fixture (located at `apps/backend/tests/fixtures/<v1-journal>.db`)
- Migration has run on the fixture copy

**Steps:**
1. Open the migrated fixture DB: `sqlite3 <temp-path>/.db "SELECT COUNT(*), COUNT(CASE WHEN rule_first_true_ts IS NULL THEN 1 END) FROM verdict_events"`
2. Verify schema version: `SELECT value FROM config WHERE key = 'journal_schema_version'`
3. Verify columns exist: `PRAGMA table_info(verdict_events)` and check for rule_first_true_ts and rule_first_true_price

**Expected outcome:**
- Schema version row shows value = 2
- verdict_events table has both new columns (rule_first_true_ts, rule_first_true_price)
- All pre-existing verdict_events rows have NULL for both new columns (never backfilled)
- Column count matches (no duplicate columns)

**Pass criteria:** schema_version = 2; new columns present; old rows retain NULL rule_first_true_* values; no errors on column existence checks.

---

### TC-04 — Idempotent re-open of v2 DB (no double migration)

**Type:** api
**Preconditions:**
- DB has been migrated to v2 (schema_version = 2, columns present)

**Steps:**
1. Backend opens the v2 DB
2. Backend performs the migration check logic (reads schema_version, checks column presence, executes migration if version < 2)
3. Verify schema_version remains 2 (no re-migration)
4. Verify columns are still present and no duplication errors

**Expected outcome:** Backend starts cleanly; migration logic skips (version >= 2); no "already exists" or duplicate-column errors.

**Pass criteria:** Backend starts without errors; schema_version unchanged; columns present; backend logs show version 2 on second open.

---

### TC-05 — Stale version row with columns already present does not crash

**Type:** api
**Preconditions:**
- DB has version row = 1 but columns rule_first_true_ts/price already exist (edge case: manual column add without version bump)

**Steps:**
1. Create a test DB with v1 version row but v2 columns present (via schema guard / PRAGMA table_info check)
2. Backend attempts to open the store
3. Verify the migration logic handles the guard (e.g., version < 2 → check columns with PRAGMA; if present, just update version row)

**Expected outcome:** Backend opens without crashing; version row is updated to 2; no duplicate-column errors.

**Pass criteria:** Backend starts; schema_version = 2; no fatal errors; handles mismatch gracefully.

---

### TC-06 — Atomic declaration: no orphan on forced event-insert failure

**Type:** api
**Preconditions:**
- Store is injected with a failure hook (e.g., monkeypatch) that raises an exception on the initial `append_verdict_event` INSERT
- Backend is running against a test DB

**Steps:**
1. Trigger the failure: call `POST /research/thesis` with valid params while the fault is active
2. Catch the error response (should be 500 or explicit API error)
3. Query the DB: `SELECT COUNT(*) FROM theses WHERE id = '<declared-id>'`
4. Verify no thesis row persists

**Expected outcome:** 
- API surfaces an explicit error (500 or 422, depending on error type) — not a silent partial save
- Transaction rolled back: thesis row does NOT exist in DB
- No orphaned row

**Pass criteria:** Error response received; thesis row absent from DB; transaction rolled back atomically.

---

### TC-07 — J-38: Declare and verify REST /thesis/active == WS thesis frame

**Type:** browser
**Preconditions:**
- Frontend running at http://localhost:3000
- Backend running at http://localhost:8000
- SIM-BUYER is being watched; cockpit is visible

**Steps:**
1. Navigate to `/` (cockpit)
2. Verify SIM-BUYER is being watched and the thesis strip shows an idle "declare" state
3. Locate and click the declare button / form in the thesis strip
4. Fill in: setup_type=absorption_reversal, direction=long, invalidation_price=95.0
5. Submit the form
6. Wait for the strip to show an ACTIVE thesis (not idle)
7. Capture the WS `thesis` key from the stream
8. Make a REST call: `GET /research/thesis/active?ticker=SIM-BUYER`
9. Compare the WS thesis object to the REST response verbatim

**Expected outcome:**
- Thesis appears in the strip (not idle state) with setup + direction + invalidation visible
- REST response `thesis` object matches WS stream `thesis` key exactly (same fields, same values)
- No page reload needed

**Pass criteria:** Thesis declared successfully; WS thesis == REST thesis (byte-identical); strip shows active thesis.

---

### TC-08 — J-39: Error matrix (404, 422×3, 409) with inline 422 in pixels

**Type:** browser
**Preconditions:**
- Frontend and backend running
- No active thesis on SIM-BUYER

**Steps:**

#### 39a: Unknown ticker → 404
1. Attempt to declare a thesis on a non-existent ticker: fill declare form with ticker="UNKNOWN", setup_type=absorption_reversal, direction=long, invalidation_price=100.0
2. Submit
3. Observe the error message displayed in the strip or a modal

#### 39b: Wrong-side invalidation → 422 inline
1. Declare a LONG thesis on SIM-BUYER
2. Set invalidation_price ABOVE current last (invalid for long)
3. Submit
4. Observe the error inline in the form (NOT a modal or log; visible in pixels on the strip)
5. Take a screenshot showing the error text is in-pixel on the cockpit

#### 39c: Missing level for level-required setup → 422
1. Declare a LEVEL_BREAK thesis
2. Leave level_price empty
3. Submit
4. Observe the 422 error (missing required level_price)

#### 39d: Forbidden level for level-forbidden setup → 422
1. Declare an ABSORPTION_REVERSAL thesis
2. Populate level_price (not allowed for this setup)
3. Submit
4. Observe the 422 error (level forbidden for this setup)

#### 39e: Second active thesis → 409
1. Declare a thesis on SIM-BUYER (succeeds)
2. While thesis is active, attempt to declare a second thesis on the same ticker
3. Observe a 409 error (one active per ticker) with an explicit message

**Expected outcome:**
- 404: error message displayed for unwatched/unknown ticker
- 422 (all three cases): error displayed inline/visible in pixels; no full-page error; form remains accessible
- 409: explicit message stating "only one active thesis per ticker"

**Pass criteria:** 
- All error cases handled distinctly
- 422 errors visible in pixels on the cockpit (inline form error, not hidden in console)
- No partial saves (second attempt after 409 still fails 409)

---

### TC-09 — J-40: SIM-REVERSAL pending through absorption → confirming on flip with rule_first_true

**Type:** browser
**Preconditions:**
- Frontend and backend running against persistent dev DB
- SIM-REVERSAL scenario is available and watched
- Backend has migrated schema (rule_first_true_ts/price columns present)

**Steps:**
1. Watch SIM-REVERSAL
2. Declare a LONG thesis with setup_type=absorption_reversal
3. Observe tape state settle on bid_absorption (absorption phase)
4. Verify verdict chip shows **pending** (premise met, trigger not yet)
5. Observe tape state transition to buyer_control (the reversal)
6. Verify verdict chip transitions to **confirming** (green)
7. Inspect the published verdict timeline: verify `rule_first_true_ts` and `rule_first_true_price` are recorded with a non-null value
8. Verify the timeline shows both the pending and confirming events with published timestamps

**Expected outcome:**
- Verdict chip shows pending while tape is absorbing
- Verdict transitions to confirming on the buyer_control flip
- Timeline records rule_first_true (the price at which reversal confirmed)
- Published events carry evidence text

**Pass criteria:** Verdict correctly tracks J-40 flow; rule_first_true is recorded; timeline visible and not backfilled.

---

### TC-10 — J-41: SIM-SELLER rejecting thesis stays active

**Type:** browser
**Preconditions:**
- Frontend and backend running
- SIM-SELLER scenario is available

**Steps:**
1. Watch SIM-SELLER
2. Declare a LONG thesis
3. Observe tape state settle on seller_control
4. Verify verdict chip shows **rejecting** (red)
5. Observe tape remains in seller_control (supporting the rejection, not the long thesis)
6. Verify thesis remains ACTIVE (not auto-resolved)
7. Check the timeline shows the rejecting transition with evidence

**Expected outcome:**
- Verdict chip shows rejecting (red background)
- Thesis stays active (no auto-resolve on rejection)
- Evidence text is visible (e.g., "tape selling aggressively")

**Pass criteria:** Verdict = rejecting; thesis active; evidence visible.

---

### TC-11 — J-42: SIM-BUYER confirming after dwell, no flapping

**Type:** browser
**Preconditions:**
- Frontend and backend running
- SIM-BUYER scenario available

**Steps:**
1. Watch SIM-BUYER
2. Declare a LONG thesis with setup_type=trend_continuation
3. Observe tape state settle on buyer_control (within warm-up dwell)
4. Verify verdict chip shows **pending** initially
5. Wait for the dwell period to elapse (~5 seconds in the config)
6. Verify verdict transitions to **confirming** (green)
7. Monitor the timeline: confirm only ONE pending→confirming transition (no flapping back to pending)
8. Observe tape state remains buyer_control throughout

**Expected outcome:**
- Verdict stays pending during dwell
- Verdict transitions to confirming after dwell
- No re-flapping to pending

**Pass criteria:** Single pending→confirming transition; verdict sticky; evidence visible.

---

### TC-12 — J-43: SIM-SHIFT confirming → weakening, both on timeline

**Type:** browser
**Preconditions:**
- Frontend and backend running
- SIM-SHIFT scenario available (sustained buyer_control → unclear/chop phase below old price)

**Steps:**
1. Watch SIM-SHIFT
2. Declare a LONG thesis
3. Observe tape state move through buyer_control
4. Verify verdict transitions to **confirming** (green)
5. Observe tape state transition to unclear/chop (the shift)
6. Verify verdict transitions to **weakening** (amber) — NOT a silent return to pending
7. Inspect the timeline: both confirming and weakening events visible with distinct timestamps
8. Verify evidence text explains the weakening (e.g., "supporting evidence faded")

**Expected outcome:**
- Verdict: pending → confirming (buyer_control) → weakening (unclear/chop)
- Timeline shows both transitions explicitly
- No silent regression to pending

**Pass criteria:** Both transitions recorded; never silent pending; evidence in timeline.

---

### TC-13 — J-44: SIM-SELLER invalidation dwell-exempt, auto-resolve, terminal treatment

**Type:** browser
**Preconditions:**
- Frontend and backend running
- SIM-SELLER scenario available

**Steps:**
1. Watch SIM-SELLER
2. Declare a LONG thesis with invalidation_price set just above the current last
3. Observe tape state move toward seller_control
4. Watch for a trade print below the invalidation level
5. Verify verdict chip immediately transitions to **invalidated** (red, terminal styling)
6. Verify the thesis auto-resolves (status changes from ACTIVE to INVALIDATED)
7. Capture the offending print/price in the evidence
8. Verify the timeline shows the invalidation event with the exact offending print

**Expected outcome:**
- Verdict flips to invalidated immediately on the bad print (no dwell for invalidation)
- Thesis auto-resolves and shows terminal treatment (no further eval)
- Offending print visible in evidence

**Pass criteria:** Invalidation immediate; thesis resolves; evidence includes offending print.

---

### TC-14 — J-45: SIM-BUYER level_break latch (pending pre-cross, confirming post-cross)

**Type:** browser
**Preconditions:**
- Frontend and backend running
- SIM-BUYER scenario available

**Steps:**
1. Watch SIM-BUYER
2. Declare a LONG thesis with setup_type=level_break, level_price set at a resistance above current price, invalidation_price below
3. Observe tape state show buyer_control
4. Verify verdict shows **pending** (premise met but price has not crossed level yet)
5. Watch for price to cross above the declared level_price
6. Verify verdict immediately transitions to **confirming** upon the cross (latch behavior)
7. Verify the timeline records the level-cross event with rule_first_true_price at or just above the level

**Expected outcome:**
- Verdict holds pending until the level is crossed
- Verdict transitions to confirming on the cross
- Timeline records the latch event

**Pass criteria:** Pending until cross; confirming after cross; level-cross recorded.

---

### TC-15 — J-46: SIM-REVERSAL failed_move_fade confirms DURING absorption (asymmetry)

**Type:** browser
**Preconditions:**
- Frontend and backend running
- SIM-REVERSAL scenario available

**Steps:**
1. Watch SIM-REVERSAL
2. Declare a LONG thesis with setup_type=failed_move_fade (the asymmetric rule)
3. Observe tape state settle on bid_absorption (sellers trying to push but bids absorb)
4. Verify verdict transitions to **confirming** (green) **while tape is still absorbing** (before any flip to buyer_control)
5. Note the difference from J-40 (absorption_reversal): failed_move_fade confirms on the absorption premise, not the flip
6. Verify timeline shows the confirming event with evidence ("aggressive selling being absorbed")

**Expected outcome:**
- Verdict = confirming while tape is absorbing (not pending)
- Distinct from absorption_reversal rule (J-40)

**Pass criteria:** Confirms during absorption; distinct from reversal rule.

---

### TC-16 — J-68: Idle cockpit thesis strip is locatable via data-testid and matches narrative

**Type:** browser
**Preconditions:**
- Frontend running at http://localhost:3000
- No active thesis on the watched ticker

**Steps:**
1. Navigate to `/` with no thesis declared
2. Use browser DevTools or a test selector to locate the element: `[data-testid="thesis-strip"]`
3. Verify the element is visible in the DOM
4. Inspect the content: should show a "declare" affordance (button or form entry point)
5. Take a full-page screenshot showing the idle strip in context (chart above, panels below)
6. Compare the visual state to the specification narrative (idle state = single declare affordance, no active thesis)

**Expected outcome:**
- Element found with data-testid="thesis-strip"
- Strip shows idle UI (declare affordance visible)
- Screenshot shows strip in-pixel and matches the narrative

**Pass criteria:** data-testid attribute present; element locatable; screenshot shows idle state; visual matches spec.

---

## Summary

**Total test cases:** 16
- **API tests:** 6 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06)
- **Browser tests:** 10 (TC-07 through TC-16)
- **Artifact checks:** 0 (covered by TC-03 artifact verification)

### Key Coverage

- ✅ Schema migration (v1→v2) with backward compatibility
- ✅ Atomic thesis declaration (no orphans on failure)
- ✅ Orphan cleanup via startup sweep
- ✅ All 9 target browser journeys (J-38–J-46, J-68)
- ✅ Error matrix and inline error display (J-39)
- ✅ Verdict timelines with rule_first_true timestamps
- ✅ Binding evidence rule (all assertions visible in pixels via screenshots)
- ✅ Persistent dev DB verification (not temp DB)
