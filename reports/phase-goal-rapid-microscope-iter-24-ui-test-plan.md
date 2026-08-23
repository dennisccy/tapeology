# Phase goal-rapid-microscope-iter-24 — UI Test Plan

**Phase:** goal-rapid-microscope-iter-24
**Date:** 2026-08-23
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301

**Rig note:** most cases below require the scoped QA rig (which seeds real fixture data, including
this iteration's new J-09 pilot-study row) rather than the ordinary backend against a fresh/empty
`.data` store. Start it with:

```
bash apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh <root_dir> 8301
CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301 bash scripts/start-frontend.sh
```

Each test case below states whether it needs the scoped rig or the ordinary backend.

---

### UT-01 — `/desk` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Scoped QA rig running (backend :8301, frontend :3301) per the rig note above.

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error message
- The text "Playbook Signals" is visible somewhere on the page
- No console errors

---

### UT-02 — Validation Vault section expands and shows shard rows (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Validation Vault section

**Preconditions:**
- Same as UT-01 (scoped QA rig).

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the element with `data-testid="desk-section-expand-validationVault"` (the "Validation
   Vault" section header/button)
3. Wait for the section body to render

**Expected Result:**
- A table with `data-testid="validation-vault-shards-table"` appears, with column headers
  `Shard | Universe | Size bucket | Checksum commitment | Sealed at | State | Dataset | Family
  root | Symbol | Session date | Assigned at | Exposed at | Content checksum`
- At least one row is visible, including one whose "Universe" cell reads `iter18-qa-universe`

---

### UT-03 — "Sealed at" column value check (regression — this iteration's core change)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Validation Vault section → shards table, "Sealed at" column

**Preconditions:**
- Section already expanded per UT-02.

**Steps:**
1. In the shards table, locate the row whose "Universe" cell reads `iter18-qa-universe`
2. Read the value in that row's "Sealed at" column (5th column)
3. Record the exact displayed string verbatim

**Expected Result (what this iteration intends):**
- A bare calendar date with no time-of-day and no `ET` suffix, e.g. `2026-06-09`

**Known-risk outcome to watch for and report as a defect if reproduced:**
- A shifted date one day EARLIER than expected, plus a spurious time-of-day and `ET` suffix, e.g.
  `2026-06-08 20:00 ET` (summer/EDT) or a similar `19:00 ET`/`20:00 ET` pattern (winter/EST). This
  was reproduced analytically against the exact frontend formatter code
  (`apps/frontend/lib/datetime.ts`) and the exact backend-served shape
  (`apps/backend/tests/test_vault.py`'s new assertions confirm the served value is exactly
  `"2026-06-09"`, 10 characters) — `formatDateTimeET` parses a bare date string as UTC midnight and
  converts it into `America/New_York` time, which always lands on the prior day with an evening
  time. **This has not yet been confirmed against a live screenshot — capturing that screenshot IS
  this test.**

---

### UT-04 — "Assigned at" / "Exposed at" columns unaffected (regression, contrast check)

**Type:** regression
**Priority:** P2
**Surface:** `/desk` → Validation Vault section → shards table, "Assigned at"/"Exposed at" columns

**Preconditions:**
- Section already expanded per UT-02. Requires a row whose "State" column reads `exposed` (the
  graduation fixture's seeded shard reaches `exposed` state via `seal_shard` → `assign_shard` →
  `expose_shard`).

**Steps:**
1. In the shards table, locate the row whose "State" column reads `exposed`
2. Read the "Assigned at" and "Exposed at" columns for that same row

**Expected Result:**
- Both values render as a normal full date-time with a time-of-day and `ET` suffix, e.g.
  `2026-06-09 14:32 ET` — these two columns were NOT touched by this iteration's backend change
  (only `sealed_at` was coarsened) and must look exactly as they did before. Contrast this against
  the SAME row's "Sealed at" cell (UT-03) — if "Sealed at" shows the shifted-date defect while
  "Assigned at"/"Exposed at" are correct, that confirms the regression is isolated to the one
  coarsened field.

---

### UT-05 — Still-sealed shard rows never disclose symbol/date (validation — anti-goal invariant)

**Type:** validation
**Priority:** P1
**Surface:** `/desk` → Validation Vault section → shards table, sealed-state rows

**Preconditions:**
- Section already expanded per UT-02. Requires at least one row whose "State" column reads
  `sealed`.

**Steps:**
1. In the shards table, locate any row whose "State" column reads `sealed`
2. Read the "Dataset", "Family root", "Symbol", "Session date", "Assigned at", "Exposed at", and
   "Content checksum" cells for that row

**Expected Result:**
- Every one of those 7 cells reads exactly `sealed — opaque` — never a real symbol, dataset id, or
  date. This is a pre-existing invariant (unchanged by this iteration) that must still hold after
  the `sealed_at` serialization change.

---

### UT-06 — Scout Ledger section shows the new pilot-study row (happy-path, scoped rig only)

**Type:** happy-path
**Priority:** P2
**Surface:** `/desk` → Scout Ledger section

**Preconditions:**
- Scoped QA rig running (this content exists ONLY there — see the "Not Visible Yet" note in the
  user-visible-changes report; it will NOT appear against an ordinary/ambient backend).

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the element with `data-testid="desk-section-expand-scoutLedger"` (the "Scout Ledger"
   section header/button)
3. Wait for the section body to render

**Expected Result:**
- The text `failed_aggression_score__playbook_signal__trades_20` is visible in the ledger content
  (the seeded Study-3 pilot family's `family_id`)
- A decision string from the closed vocabulary is also visible (per the dev handoff, expect
  `killed_insufficient_n` for this seeded family, given `n_candidate=0, n_comparator=1`)

---

### UT-07 — Scout Ledger empty-state text is unchanged in production (error/empty-state handling)

**Type:** error
**Priority:** P2
**Surface:** `/desk` → Scout Ledger section, empty state

**Preconditions:**
- The ORDINARY backend, NOT the scoped QA rig — a fresh or empty `.data/` store with zero Scout
  candidates ledgered.

**Steps:**
1. Navigate to `http://localhost:3301/desk` (against the ordinary backend)
2. Click the element with `data-testid="desk-section-expand-scoutLedger"`

**Expected Result:**
- The text "No candidates ledgered." is visible (`data-testid="scout-ledger-families-empty"`) —
  proves the two stored QA-replay scripts' assertion swap (J-08.json/J-10.json, from
  `"No candidates ledgered."` to `"Ledger chain verification:"`) reflects only a QA-fixture-rig
  side effect, not a change to the actual empty-state message real operators see.

---

### UT-08 — Graduation-relevant sections still show sealed-pipeline data (regression, fresh evidence required)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Scout Ledger / Walk-Forward / Validation Vault sections (Graduation, J-07)

**Preconditions:**
- Scoped QA rig running. Zero diff to `micro_graduation.py`/`micro_sealed_evaluation.py` this
  iteration (grep-confirmed by dev handoff), so behavior should be identical to iter-22's
  verified state.

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Expand the Validation Vault section (`data-testid="desk-section-expand-validationVault"`) and
   confirm the `iter18-qa-universe` shard row is present and reaches `exposed` state
3. Take a fresh screenshot dated 2026-08-23 or later

**Expected Result:**
- The graduation pipeline's sealed-shard evidence renders identically to the iter-22-verified
  state (same universe id, same eventual `exposed` state). A carried-forward iter-22 screenshot is
  explicitly NOT acceptable — the phase DoD requires this iteration's own dated capture.

---

### UT-09 — Validation Vault section is reachable and clearly labeled (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/desk` navigation / section list

**Preconditions:**
- Scoped QA rig running.

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll down and look for a section titled "Validation Vault"

**Expected Result:**
- A collapsed section header reading exactly "Validation Vault" is visible without needing to
  expand any other section first (one click reaches its content) — confirms this iteration's
  precision-only change did not alter section discoverability or ordering (Scout Ledger →
  Walk-Forward → Validation Vault, in that order, per the existing page layout)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads | smoke | P1 | `/desk` |
| UT-02 | Validation Vault section expands | happy-path | P1 | `/desk` Validation Vault |
| UT-03 | "Sealed at" column value check | regression | P1 | `/desk` Validation Vault shards table |
| UT-04 | "Assigned at"/"Exposed at" unaffected | regression | P2 | `/desk` Validation Vault shards table |
| UT-05 | Sealed rows stay opaque | validation | P1 | `/desk` Validation Vault shards table |
| UT-06 | Scout Ledger shows seeded pilot row | happy-path | P2 | `/desk` Scout Ledger (scoped rig) |
| UT-07 | Scout Ledger empty-state unchanged | error | P2 | `/desk` Scout Ledger (ordinary backend) |
| UT-08 | Graduation fresh evidence | regression | P1 | `/desk` (J-07 surfaces) |
| UT-09 | Validation Vault discoverable | ux | P3 | `/desk` navigation |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-03 is the highest-priority new
check this iteration introduces — it targets a display regression identified during this analysis
that has not yet been confirmed or refuted against a live screenshot.
