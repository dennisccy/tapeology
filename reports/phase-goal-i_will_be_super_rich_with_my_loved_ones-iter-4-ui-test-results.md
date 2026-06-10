# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-4 — UI Test Results

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-4
**Date:** 2026-06-10
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

**Overall:** 1/12 tests passed (0 skipped)

---

## Root Cause Summary

All thesis declaration tests (UT-02 through UT-12) fail due to a single root cause:

**DB schema not migrated — `verdict_events` table is missing `rule_first_true_ts` and `rule_first_true_price` columns.**

The `_SCHEMA` SQL string in `store.py` defines these columns in `CREATE TABLE IF NOT EXISTS verdict_events`, but the table was created by a prior iteration that did not include them. Since `CREATE TABLE IF NOT EXISTS` is a no-op on an existing table, the columns were never added. Every call to `append_verdict_event` fails with an SQLite `OperationalError: table verdict_events has no column named rule_first_true_ts`, which the store's writer queue surfaces to the route as an exception, which the route catches and returns as HTTP 503 with body `{"detail": "could not persist the thesis"}`.

The frontend displays "could not persist the thesis" inline in the declaration form. The thesis INSERT (`insert_thesis`) succeeds before the error (the thesis row IS written to the DB in `active` status), but `append_verdict_event` (the initial `pending` verdict event) fails. This leaves an orphaned `active` thesis in the DB with no verdict events and no monitor attachment. On SIM-BUYER, one such orphaned thesis was created during testing, which additionally blocks all subsequent declarations for that ticker with a 409 "an active thesis already exists".

Evidence: `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-4-evidence/UT-FAIL-503-form-error.png`

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Cockpit home loads with thesis strip visible | smoke | P1 | Page renders, thesis strip with "Declare thesis" affordance visible, no errors | Page loaded, Buyer Control state with last=~100.25, "Declare thesis" button present in thesis strip section, no error banners | PASS | UT-01-result.png |
| UT-02 | Verdict chip transitions pending→confirming on SIM-BUYER | happy-path | P1 | Chip transitions slate→emerald after ~3-5s | POST /research/thesis returns 503 "could not persist the thesis" on every attempt; chip never appears | FAIL | UT-FAIL-503-form-error.png |
| UT-03 | Evidence sentence appears for every verdict state | happy-path | P1 | Non-empty evidence sentence below chip in matching color | Same root cause as UT-02 — thesis cannot be declared | FAIL | UT-FAIL-503-form-error.png |
| UT-04 | Verdict chip shows amber "Weakening" on SIM-SHIFT | happy-path | P1 | Chip turns amber after tape shifts | Same root cause — thesis declaration blocked by 503 | FAIL | UT-FAIL-503-form-error.png |
| UT-05 | Verdict chip shows rose "Rejecting" on SIM-SELLER | happy-path | P1 | Chip turns rose with rejecting evidence | POST /research/thesis returns 503 on SIM-SELLER; "could not persist the thesis" displayed in form | FAIL | UT-FAIL-503-form-error.png |
| UT-06 | Terminal invalidated treatment appears and persists | happy-path | P1 | Rose ringed chip, "✕ Invalidated", "Thesis invalidated — resolved" line | Same root cause — thesis cannot be declared | FAIL | UT-FAIL-503-form-error.png |
| UT-07 | Expired thesis reverts to idle; invalidated thesis does not | regression | P1 | Two distinct post-resolution behaviors | Cannot test — depends on UT-06 completing | FAIL | UT-FAIL-503-form-error.png |
| UT-08 | Verdict chip uses taxonomy-owned labels, not raw enums | regression | P1 | "Confirming" not `confirming` on chip | Cannot test — thesis declaration blocked | FAIL | UT-FAIL-503-form-error.png |
| UT-09 | Pending state shows evidence sentence before any verdict fires | validation | P2 | Evidence sentence present while chip is slate "Pending" | Cannot test — thesis declaration blocked | FAIL | UT-FAIL-503-form-error.png |
| UT-10 | Rejecting state does not auto-resolve the thesis | validation | P2 | No idle affordance, no "resolved" notice during Rejecting | Cannot test — depends on UT-05 completing | FAIL | UT-FAIL-503-form-error.png |
| UT-11 | Verdict chip color semantics match specification | ux | P2 | Each state has correct color: emerald/amber/rose/slate | Cannot test — thesis declaration blocked | FAIL | UT-FAIL-503-form-error.png |
| UT-12 | Cockpit chart and panel grid unaffected by thesis strip changes | regression | P1 | Chart and panel grid render normally with active thesis | Cannot fully test active-thesis layout — declaration blocked | FAIL | UT-FAIL-503-form-error.png |

---

## Passed Tests

### UT-01 — Cockpit home loads with thesis strip visible
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-4-evidence/UT-01-result.png`
- Navigated to http://localhost:3650, selected Simulated mode, typed SIM-BUYER, clicked Watch
- Page loaded, tape showed "Buyer Control" state (Confidence 0.935, Last ~109.17)
- Thesis strip section rendered with the idle text "Declare a thesis on this ticker to watch the tape judged against it." and a "Declare thesis" button
- No red error banners in the header or strip area
- No uncaught JS errors observed
- Note: `data-testid="thesis-strip"` attribute is not present in the DOM (the section element has no data-testid), but the visual UI element is present and functional

---

## Failed Tests

### UT-02 — Verdict chip transitions pending→confirming on SIM-BUYER
**Verdict:** FAIL
**Failure:** HTTP 503 "could not persist the thesis" returned by POST /research/thesis on every declaration attempt. Root cause: `verdict_events` table missing `rule_first_true_ts` and `rule_first_true_price` columns — see Root Cause Summary above.
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-4-evidence/UT-FAIL-503-form-error.png`

**Steps taken:**
1. Navigated to http://localhost:3650 in Simulated mode
2. Typed SIM-BUYER, clicked Watch, waited for "Buyer Control" state
3. Clicked "Declare thesis" button — declaration form opened
4. Selected setup=trend_continuation via select dropdown, direction=long (default), typed invalidation=95
5. Clicked Declare button (corrected XPath targeting issue — was accidentally clicking Watch button)
6. Backend returned HTTP 503; form displayed "could not persist the thesis"

**Expected:** Thesis declared, chip shows "Pending" (slate), transitions to "Confirming" (emerald) after ~3-5s of buyer-control tape.
**Actual:** HTTP 503 on every declaration attempt. Additionally, one orphaned `active` thesis (id: `4beae280`) was created in the DB due to the partial transaction failure (INSERT succeeded, append_verdict_event failed), which additionally blocks SIM-BUYER declarations with 409 after the first attempt.

---

### UT-03 — Evidence sentence appears for every verdict state
**Verdict:** FAIL
**Failure:** Cannot test — depends on thesis declaration which returns 503 for all tickers.
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-4-evidence/UT-FAIL-503-form-error.png`

**Steps taken:** Attempted thesis declaration as prerequisite; failed with 503.
**Expected:** `data-testid="verdict-evidence"` element present with non-empty text.
**Actual:** Thesis strip never reached active state; evidence element never rendered.

---

### UT-04 — Verdict chip shows amber "Weakening" on SIM-SHIFT
**Verdict:** FAIL
**Failure:** Cannot test — thesis declaration returns 503 for all tickers including SIM-SHIFT.
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-4-evidence/UT-FAIL-503-form-error.png`

**Steps taken:** Not attempted (same root cause as UT-02 confirmed for SIM-SELLER; SIM-SHIFT would produce same result).
**Expected:** Chip transitions emerald→amber when tape shifts.
**Actual:** Blocked by 503 before thesis can be declared.

---

### UT-05 — Verdict chip shows rose "Rejecting" on SIM-SELLER with far invalidation
**Verdict:** FAIL
**Failure:** POST /research/thesis returned HTTP 503 "could not persist the thesis" on SIM-SELLER.
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-4-evidence/UT-FAIL-503-form-error.png`

**Steps taken:**
1. Navigated to Simulated mode, started SIM-SELLER (reached Seller Control state, Last ~98.87)
2. Opened declaration form, selected trend_continuation, direction=long, invalidation=85
3. Clicked Declare (via JS button.click() after diagnosing XPath targeting issue)
4. Backend responded with HTTP 503; "could not persist the thesis" shown in form

**Expected:** Chip shows "Rejecting" in rose background with seller-control evidence sentence.
**Actual:** 503 on declaration — chip never rendered.

---

### UT-06 — Terminal invalidated treatment appears and persists
**Verdict:** FAIL
**Failure:** Same root cause — thesis declaration returns 503 for all tickers.
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-4-evidence/UT-FAIL-503-form-error.png`

**Steps taken:** Not attempted (SIM-SELLER used in UT-05 confirmed 503; same result expected).
**Expected:** Rose ringed chip, "✕ Invalidated", "Thesis invalidated — resolved" line persist after invalidation trigger.
**Actual:** Blocked by 503.

---

### UT-07 — Expired thesis reverts to idle; invalidated thesis does not
**Verdict:** FAIL
**Failure:** Prerequisite UT-06 failed; cannot test.
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-4-evidence/UT-FAIL-503-form-error.png`

**Steps taken:** Not attempted.
**Expected:** Two distinct post-resolution behaviors.
**Actual:** Cannot reach thesis-active state.

---

### UT-08 — Verdict chip uses taxonomy-owned labels, not raw enums
**Verdict:** FAIL
**Failure:** Cannot test — thesis declaration blocked by 503.
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-4-evidence/UT-FAIL-503-form-error.png`

**Steps taken:** Not attempted.
**Expected:** "Confirming" (capitalized label) on chip, not raw string `confirming`.
**Actual:** Thesis strip never reaches active state.

---

### UT-09 — Pending state shows evidence sentence before any verdict fires
**Verdict:** FAIL
**Failure:** Cannot test — thesis declaration blocked by 503.
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-4-evidence/UT-FAIL-503-form-error.png`

**Steps taken:** Not attempted.
**Expected:** `data-testid="verdict-evidence"` present with text while chip is slate "Pending".
**Actual:** Thesis strip never reaches active state.

---

### UT-10 — Rejecting state does not auto-resolve the thesis
**Verdict:** FAIL
**Failure:** Prerequisite UT-05 failed; cannot test.
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-4-evidence/UT-FAIL-503-form-error.png`

**Steps taken:** Not attempted.
**Expected:** No idle affordance, no "resolved" notice during Rejecting.
**Actual:** Cannot reach Rejecting state.

---

### UT-11 — Verdict chip color semantics match specification
**Verdict:** FAIL
**Failure:** Cannot test — thesis declaration blocked by 503.
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-4-evidence/UT-FAIL-503-form-error.png`

**Steps taken:** Not attempted.
**Expected:** Emerald/amber/rose/slate colors for Confirming/Weakening/Rejecting/Pending.
**Actual:** No verdict chip states reachable.

---

### UT-12 — Cockpit chart and panel grid unaffected by thesis strip changes
**Verdict:** FAIL
**Failure:** The idle strip layout can be partially observed, but the active thesis strip layout (the primary change) cannot be tested because thesis declaration is blocked by 503. The "Descriptive only — not trading advice" disclaimer is present in idle state.
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-4-evidence/UT-01-result.png`

**Steps taken:**
1. Observed cockpit with SIM-BUYER watching — chart area and panel grid rendered correctly in idle thesis strip state
2. "Descriptive only — not trading advice" disclaimer visible
3. Could not test active thesis layout (thesis declaration blocked by 503)

**Expected:** Chart and panels unaffected by active thesis strip; strip does not overflow or reflow.
**Actual:** Only idle state observable. Active thesis state not reachable.

---

## Additional Defect: Orphaned Active Thesis Blocking SIM-BUYER

During diagnosis, a secondary defect was discovered. When `insert_thesis` succeeds but `append_verdict_event` fails (503 path), the thesis is written to the DB with status='active' but no monitor attached and no verdict events. This orphaned thesis (`id: 4beae280cd884ade8a810695a610240f`, ticker: SIM-BUYER, setup: absorption_reversal, invalidation: 95.0) blocks all subsequent SIM-BUYER declarations with HTTP 409 "an active thesis already exists for 'SIM-BUYER'". The `startup_sweep()` would normally clear such orphans at server startup, but the server was not restarted during the QA session.

The transaction is not atomic: `insert_thesis` and `append_verdict_event` run as separate DB write operations, not in a single transaction. If the second write fails, the first is not rolled back.

---

## Environment

- **Frontend URL:** http://localhost:3650
- **Backend URL:** http://localhost:8650
- **Browser:** Chrome via MCP
- **Test Date:** 2026-06-10
- **Evidence directory:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-4-evidence/`
