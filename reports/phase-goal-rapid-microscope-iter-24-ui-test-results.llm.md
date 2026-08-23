# Phase goal-rapid-microscope-iter-24 — UI Test Results

**Phase:** goal-rapid-microscope-iter-24
**Date:** 2026-08-23
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: UT-03 (P1, regression) fails — the "Sealed at" display defect flagged by the
     ui-impact-analyst as a known-risk-but-unconfirmed regression is REPRODUCED live in the
     browser. -->

**Overall:** 6/9 tests passed (2 skipped, 1 failed)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads without errors | smoke | P1 | Page renders, "Playbook Signals" visible, no console errors | Page rendered fully, "Playbook Signals" heading visible, no console errors captured | PASS | `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-01-result.png` |
| UT-02 | Validation Vault section expands and shows shard rows | happy-path | P1 | Table `validation-vault-shards-table` appears with the 13 named column headers; ≥1 row with Universe=`iter18-qa-universe` | Table rendered with exactly those headers; 1 row present, Universe=`iter18-qa-universe` | PASS | `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-02-result.png` |
| UT-03 | "Sealed at" column value check | regression | P1 | A bare calendar date, no time-of-day, no ET suffix (e.g. `2026-06-09`) | Backend serves `sealed_at: "2026-05-01"` (verified via `GET /research/desk/micro/vault`) but the page renders it as **`2026-04-30 20:00 ET`** — shifted one day earlier plus a spurious time, exactly the defect pattern the analysis predicted | FAIL | `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-03-fail.png` |
| UT-04 | "Assigned at"/"Exposed at" unaffected | regression | P2 | Normal full date-time with ET suffix, e.g. `2026-06-09 14:32 ET` | Same row: Assigned at = `2026-06-04 20:00 ET`, Exposed at = `2026-06-05 20:00 ET` — both normal full date-times with ET suffix, contrasting correctly against the broken "Sealed at" cell | PASS | `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-04-result.png` |
| UT-05 | Sealed rows stay opaque | validation | P1 | Every non-identity cell of a `sealed`-state row reads exactly `sealed — opaque` | Untestable — this scoped rig's Validation Vault currently contains exactly ONE shard, already in `exposed` state (confirmed via `GET /research/desk/micro/vault`: 1 shard total; `GET /research/desk/micro/readiness`: `sealed_tranche.shard_count: 0`). No row with State=`sealed` exists to inspect. | SKIP | `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-05-skip.png` |
| UT-06 | Scout Ledger shows seeded pilot row | happy-path | P2 | Text `failed_aggression_score__playbook_signal__trades_20` visible; a closed-vocabulary decision (`killed_insufficient_n` expected) also visible | Both visible: family `failed_aggression_score__playbook_signal__trades_20 (root e47904f2f7f4f0e1)`, decision `killed_insufficient_n`, reason detail `n_candidate=0, n_comparator=1` | PASS | `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-06-result.png` |
| UT-07 | Scout Ledger empty-state unchanged (ordinary backend) | error | P2 | "No candidates ledgered." visible against a fresh/empty ordinary backend | Not tested — this dispatch only has the scoped QA fixture rig running on :8301 (confirmed non-empty ledger, per UT-06). No ordinary/ambient backend instance is provisioned; ports 8000/8080/8300/3000 unreachable. Starting a second backend instance is outside this agent's scope (no app restart/infra management). | SKIP | none |
| UT-08 | Graduation fresh evidence | regression | P1 | Sealed-shard evidence identical to iter-22 (same universe id, same `exposed` state), with a screenshot dated 2026-08-23 or later | `iter18-qa-universe` shard present, State=`exposed`, Dataset/Family root/Symbol/Session date all disclosed exactly as before; screenshot file dated 2026-08-23 (today) | PASS | `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-08-result.png` |
| UT-09 | Validation Vault discoverable | ux | P3 | Collapsed header "Validation Vault" reachable in one click; order Scout Ledger → Walk-Forward → Validation Vault | Confirmed via full-page capture and DOM extract: section order is Microscope Readiness → Scout Ledger → Walk-Forward → Validation Vault, unchanged; "Validation Vault" header visible without expanding any other section | PASS | `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-09-result.png` |

---

## Passed Tests

### UT-01 — `/desk` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-01-result.png`
- Navigated to `http://localhost:3301/desk`, page rendered the full section list ("Desk" heading, Playbook Signals panel, all collapsed sections). `get_console_messages` after `enable_console_logging` returned no captured errors.

### UT-02 — Validation Vault section expands and shows shard rows
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-02-result.png`
- Clicked `[data-testid="desk-section-expand-validationVault"]`; the section expanded and `[data-testid="validation-vault-shards-table"]` rendered with headers `Shard | Universe | Size bucket | Checksum commitment | Sealed at | State | Dataset | Family root | Symbol | Session date | Assigned at | Exposed at | Content checksum` (confirmed verbatim via `extract`). One row present, Universe=`iter18-qa-universe`.

### UT-04 — "Assigned at"/"Exposed at" unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-04-result.png`
- Same row as UT-03/UT-05: Assigned at=`2026-06-04 20:00 ET`, Exposed at=`2026-06-05 20:00 ET`. Both are normal full date-times with time-of-day and an ET suffix — this matches the backend's real full-precision ISO timestamps for these two fields (`assigned_at: "2026-06-05T00:00:00.000000Z"`, `exposed_at: "2026-06-06T00:00:00.000000Z"` per the API), which the ET-conversion formatter renders correctly (midnight UTC → prior-day evening ET is the CORRECT conversion for a genuine full timestamp — unlike the coarsened `sealed_at`, which is a bare date being run through the same converter incorrectly). Confirms the regression is isolated to the one coarsened field.

### UT-06 — Scout Ledger shows seeded pilot row
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-06-result.png`
- Clicked `[data-testid="desk-section-expand-scoutLedger"]`; section shows `failed_aggression_score__playbook_signal__trades_20 (root e47904f2f7f4f0e1) — 1 variants tried` with a table row: Decision=`killed_insufficient_n`, Reason=`killed_insufficient_n`, Notes=`usable_sessions=0 (need >= 2), n_candidate=0, n_comparator=1 (each need >= 5)`. This matches the dev handoff's stated seeded outcome exactly.
- Golden replay: `runs/goal-session-rapid-microscope/journey-scripts/J-09.json` (already authored by dev this iteration) was re-verified live — its two steps (`goto /desk` expecting "Playbook Signals", then `click desk-section-expand-scoutLedger` expecting `failed_aggression_score__playbook_signal__trades_20`) reproduce exactly what this browser session just did. No changes needed; left as-is.

### UT-08 — Graduation fresh evidence
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-08-result.png`
- Validation Vault's `iter18-qa-universe` shard reaches `exposed` state (Dataset=`6b14c35632e142a3b444febef18a9106`, Family root=`240dd966c1aceca2`, Symbol=`PGQA`, Session date=`2026-06-09`) — matches the iter-22-verified graduation pipeline's disclosed evidence shape. Screenshot file is dated 2026-08-23 (today), satisfying the "no carried-forward stamp" requirement. Note: this same row's "Sealed at" cell exhibits the UT-03 display defect, but the graduation-relevant identity/state fields themselves (state, symbol, session date, dataset, family root) are all disclosed correctly and unaffected.

### UT-09 — Validation Vault discoverable
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-09-result.png`
- Full-page screenshot and DOM `extract` both confirm the section order is unchanged: Microscope Readiness → Scout Ledger → Walk-Forward → Validation Vault. "Validation Vault" header text visible and reachable without expanding any other section.

---

## Failed Tests

### UT-03 — "Sealed at" column value check
**Verdict:** FAIL
**Failure:** The backend correctly serves a coarsened bare date (`sealed_at: "2026-05-01"`, confirmed directly via `curl http://localhost:8301/research/desk/micro/vault`), but the `/desk` page renders it in the "Sealed at" column as **`2026-04-30 20:00 ET`** — one calendar day earlier than served, plus a spurious time-of-day and `ET` suffix. This is precisely the display regression the ui-impact-analyst's static analysis predicted (frontend's `formatDateTimeET` parses a bare date string as UTC midnight and converts to `America/New_York`, which always lands on the prior day with an evening time) and is now confirmed live, not merely analytically.
**Evidence:** `reports/qa/goal-rapid-microscope-iter-24-evidence/UT-03-fail.png`

**Steps taken:**
1. Navigated to `http://localhost:3301/desk`.
2. Clicked `[data-testid="desk-section-expand-validationVault"]`.
3. Read the `validation-vault-shards-table` via DOM `extract`: row for `iter18-qa-universe` shows `Sealed at` = `2026-04-30 20:00 ET`.
4. Cross-checked the backend directly: `GET /research/desk/micro/vault` → `"sealed_at": "2026-05-01"` (bare `YYYY-MM-DD`, exactly matching the phase's own TC-1 backend proof).

**Expected:** A bare date with no time-of-day, e.g. `2026-05-01`.
**Actual:** `2026-04-30 20:00 ET` — wrong date (off by one day) plus an incorrect time-of-day component.

---

## Skipped Tests

### UT-05 — Sealed rows stay opaque
**Verdict:** SKIPPED
**Reason:** Prerequisite data missing. This test requires at least one Validation Vault row whose State column reads `sealed`. The currently running scoped QA rig's vault contains exactly ONE shard total, and it is already in `exposed` state (confirmed via `GET /research/desk/micro/vault`: `shards` array length 1, `exposure_state: "exposed"`; and `GET /research/desk/micro/readiness`: `sealed_tranche.shard_count: 0`). Tracing the seeder (`apps/backend/scripts/seed_micro_graduation_iter18_fixture.py`) confirms it always seals → assigns → exposes its one shard in sequence, never leaving a shard in `sealed` state at rest. This is a data-availability limitation of the fixture rig, not a product defect — the `sealed — opaque` invariant itself could not be exercised this iteration.

### UT-07 — Scout Ledger empty-state unchanged (ordinary backend)
**Verdict:** SKIPPED
**Reason:** This test explicitly requires "the ORDINARY backend, NOT the scoped QA rig — a fresh or empty `.data/` store with zero Scout candidates ledgered." This browser-qa dispatch is provisioned with only the scoped QA fixture rig on port 8301 (confirmed non-empty Scout Ledger per UT-06's pass). No ordinary/ambient backend instance is running or reachable (checked ports 8000, 8080, 8300, 3000 — all unreachable). Standing up a second backend instance is outside this agent's scope (no app restart or infrastructure management per the browser-qa-agent's own rules).

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (scoped QA fixture rig — `qa_playbook_iter7_fixture_scoped_backend.sh`)
- **Browser:** Headless Chrome via Chrome MCP (CDP port 9222)
- **Test Date:** 2026-08-23
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-24-evidence/`

## Notes for the goal-evaluator

- **J-06** ("The recorder and the Vault — new tape, sealed at birth"): this iteration's DoD required "the Validation Vault section renders sealed shard rows with the new date-only `sealed_at` precision." The backend half of that is true (verified via direct API read), but the RENDERED page does not show a date-only value — it shows a shifted date plus a spurious time (UT-03). **J-06 does not meet its own DoD wording this iteration** on the display side, even though the underlying serialized value and the anti-goal opacity invariant (UT-04, no symbol/date leak for the one row inspected) are otherwise intact. No `journey-scripts/J-06.json` was rewritten — the existing one (unchanged this iteration, dated 2026-08-19) only checks the Microscope Readiness panel's "No integrity errors." text and does not touch this regression either way.
- **J-07** ("Graduation"): re-verified via UT-08 with a fresh 2026-08-23 screenshot — the graduation-relevant identity/state evidence (universe id, exposed state, symbol, session date, dataset/family root) renders correctly and matches the iter-22-verified shape. PASS on its own narrow acceptance text, independent of the UT-03 defect (which affects only the adjacent "Sealed at" cell, not any graduation-owned field).
- **J-09** ("The pilot studies"): PASS via both the live browser pass (UT-06) and the pre-existing stored golden `journey-scripts/J-09.json` (authored by dev this iteration, re-verified live and left unchanged — it already asserts the correct discriminating string).
- Required-still-passing journeys J-01, J-02, J-03, J-04, J-05, J-08, J-10 were not re-tested here per the dispatch instructions (already re-verified via deterministic replay).
