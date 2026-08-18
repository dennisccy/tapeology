# Phase goal-rapid-microscope-iter-9 — UI Test Plan

**Phase:** goal-rapid-microscope-iter-9
**Date:** 2026-08-18
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301 (store-scoped rig — do NOT point at the real
`.data/datasets` store; the rig seeds exactly 2 committed PG fixture datasets by design, never the
real 18-dataset/12-symbol-day corpus)

---

**Why this plan is regression-plus-one-negative-check:** this iteration's diff is 5 backend source
files (one new: `vault.py`) plus 4 test files (one new: `test_vault.py`), zero frontend changes
(confirmed via `git status --porcelain`; see
`reports/phase-goal-rapid-microscope-iter-9-ui-surface-map.md`). There is no new capability, form,
or page to design happy-path, validation, or error test cases around — writing any would invent a
surface that does not exist. Instead:

- **UT-01** is the one genuinely new thing this iteration's browser pass must prove: the phase
  spec's own Testing Requirements state that J-06's browser evidence this iteration is "an element
  capture of `/desk` confirming the Validation Vault section is genuinely ABSENT" — not a walkthrough
  of a new feature, but proof that OUT OF SCOPE held.
- **UT-02 through UT-08** re-verify pre-existing surfaces, because `Frontend Present: yes` is this
  iteration's mechanism for letting the browser-QA lane dispatch the required-still-passing
  regression set (J-01–J-05) and the J-10 sentinel.

This iteration's actual backend deliverable — universe registration, the sealed → assigned →
exposed shard lifecycle, the HMAC seal assignment, the exposure-registry sealed filter, and the two
new §2.6 manifest fields — has no UI wiring at all; it is covered by the backend test suite
(`test_vault.py`'s 24 tests plus the TC-1 through TC-14 scenarios in
`docs/handoffs/goal-rapid-microscope-iter-9-dev.md`), not by a browser test here.

**Correction carried forward from iteration 6/7 (reconfirmed fresh for this report):** iteration 6's
Microscope Readiness test asserted the real store's `Distinct symbol-days = 12` / `Distinct
datasets = 18` against this same fixture-scoped rig and failed spuriously as a result — the rig
structurally cannot show those numbers (`docs/handoffs/goal-rapid-microscope-iter-6-audit.md`,
finding E3). UT-03 below is pinned to what the rig actually seeds instead: 1 symbol-day / 2
datasets, both symbol PG, session date 2026-06-09 — independently re-verified for this report by
opening both fixture JSON files directly, not merely copied from a prior report.

**Preconditions for the whole plan:**
- Backend running at `http://localhost:8301` against the store-scoped rig (start via
  `apps/backend/scripts/start_scoped_qa_backend.sh`), healthy (`GET /health` returns
  `{"status":"ok"}`).
- Frontend running at `http://localhost:3301`, after a clean `rm -rf apps/frontend/.next` rebuild,
  to rule out a stale build masking real evidence.
- No login/auth required (this product has none).

---

## Test Cases

### UT-01 — `/desk` confirms the Validation Vault section is genuinely absent (smoke + J-06 acceptance proof)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301
- Backend is running at http://localhost:8301

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load — verify the heading "Playbook Signals" is visible
3. Scroll from the top of the page to the very bottom, passing every collapsible section header
4. At the bottom of the page, verify the last section header is "Microscope Readiness"
   (`data-testid="desk-section-expand-microReadiness"`)

**Expected Result:**
- No blank screen, no error banner, no unhandled exception in the browser console
- The text "Validation Vault" does **not** appear anywhere on the page
- No element with `data-testid="desk-section-expand-vault"` exists anywhere on the page
- "Microscope Readiness" is the last section on the page — nothing renders below it
- This is not a gap: `vault.py` and `GET /research/desk/micro/vault` are fully built and tested
  this iteration, but rendering them on `/desk` is explicitly J-08 scope, not this iteration's

---

### UT-02 — `/desk` still has no "Scout Ledger" or "Walk-Forward" section (regression — J-02/J-03/J-04/J-05)

**Type:** regression
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- UT-01 passed (page already loaded)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Confirm these 8 section headers are present somewhere on the page: "Top-up Runs", "Index
   Reconciliation", "Screen Runs", "Playbook Evidence", "Referee Registry", "Referee Adjudications",
   "Referee Runs", "Microscope Readiness"
3. Note whether "Screen Comparison" and "Provenance" are also present (they render only if a screen
   has already been computed in this rig session — their absence on a fresh rig is expected, not a
   bug)

**Expected Result:**
- All 8 always-rendered section headers from step 2 are present
- No section titled "Scout Ledger" or "Walk-Forward" exists anywhere on the page — this satisfies
  J-02's, J-03's, J-04's, and J-05's "no dedicated UI element of their own" regression check, since
  none of the four has a browser surface more specific than this whole-page check (that UI lands
  with J-08)

---

### UT-03 — Microscope Readiness shows the fixture rig's real (2-dataset) corpus data, no new columns (regression — J-01, this iteration's byte-compat)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Microscope Readiness section

**Preconditions:**
- UT-01 passed (page already loaded)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll to the bottom of the page and click the section header with
   `data-testid="desk-section-expand-microReadiness"` (title text "Microscope Readiness")
3. Read the "Corpus Totals" table (`data-testid="micro-readiness-totals-table"`)
4. Read the "Legacy Tick Shards" table (`data-testid="micro-readiness-shards-table"`), including its
   column headers

**Expected Result:**
- The Corpus Totals table shows "Distinct symbol-days" = `1` and "Distinct datasets" = `2`
  (element `data-testid="micro-readiness-distinct-symbol-days"` and
  `data-testid="micro-readiness-distinct-datasets"` respectively) — **not** `12`/`18`; this rig
  seeds exactly the 2 committed fixtures (`tests/fixtures/datasets/6c9bf2c700d749e0993efd92c5807de3.json`,
  `.../d9f9dbe04fb24a7caccc53f0c6805412.json`), never the real store
- The "RTH minutes covered" and "Session-equivalents" cells each show some non-empty numeric value
  (no specific number asserted here — not independently pre-measured against this rig)
- The Legacy Tick Shards table renders exactly **2** data rows
  (`data-testid="micro-readiness-shard-rows"`), both with Symbol = `PG` and Session date =
  `2026-06-09`, each with a non-empty Feed, Window (ET), Trades, Quotes, Bytes, Coverage gaps, and
  Fallback frac cell
- Both rows' "Split provenance" column read `hand_assigned` — the exact text
  `journey-scripts/J-01.json` step 2 asserts
- Both rows' "Exposure state" column read `exploratory` (never `sealed`, `assigned`, or `exposed` —
  those states belong only to `vault.py`'s own shard lifecycle, which this endpoint does not read)
- The shard table's header row has exactly 12 columns, in this order: Symbol, Session date, Feed,
  Window (ET), Trades, Quotes, Bytes, Coverage gaps, Fallback frac, Checksum, Split provenance,
  Exposure state — **no new column** for `quote_size_unit_rule_text` or
  `quote_size_unit_verification_note`. This is the load-bearing assertion for this iteration
  specifically: it proves this iteration's two new optional §2.6 manifest fields are not surfaced
  anywhere in the UI, exactly as the plan scopes them

---

### UT-04 — Cockpit ticker watch still works (regression — J-10 steps 1–3)

**Type:** regression
**Priority:** P1
**Surface:** `/` (cockpit)

**Preconditions:**
- None (cockpit loads with no watched ticker by default)

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Verify the text "No ticker watched" is visible
3. Type `SIM-BUYER` into the field labeled "Ticker"
4. Click the "Watch" button

**Expected Result:**
- After step 2: the empty-state text "No ticker watched" is visible before any ticker is set
- After step 4: the text "Buyer Control" appears, confirming the watch flow still completes
- No error toast or blank panel appears at any point — the cockpit's live-tape rendering does not
  depend on this iteration's vault/tick-recording backend changes

---

### UT-05 — `/structure` Tradable Map still loads (regression — J-10 steps 4–7)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Verify the text "Tradable Map" is visible
3. Type `AAPL` into the field labeled "Structure symbol"
4. Type `2026-06-22 17:00:00` into the field with `data-testid="structure-as-of-input"`
5. Click the element with `data-testid="structure-load-button"`

**Expected Result:**
- After step 2: "Tradable Map" heading/label is visible on page load
- After step 5: the text "300.11–302.2" appears (the pinned real S/R band for AAPL as-of
  2026-06-22 17:00:00 ET), proving the structure engine still serves byte-identical output — this
  page reads the Yahoo/BarStore bar pipeline, entirely separate from this iteration's vault/tick
  diff
- No error message replaces the expected band text

---

### UT-06 — Playbook Evidence section still renders real signals (regression — J-10 steps 8–10)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Playbook Evidence section

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Verify the heading "Playbook Signals" is visible
3. Click `data-testid="desk-section-expand-playbookEvidence"`
4. Verify the text "Built from signature:" appears
5. Type `2026-06-22` into the field with `data-testid="desk-playbook-date-input"`

**Expected Result:**
- After step 4: "Built from signature:" is visible, confirming the section reads a real,
  already-computed playbook signature (not a placeholder)
- After step 5: the text "recorded signals, none hidden" appears, confirming the date-filtered
  view still serves the full, unfiltered signal set for that date

---

### UT-07 — Referee Registry section still shows the frozen fingerprint (regression — J-10 step 11)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Referee Registry section

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click `data-testid="desk-section-expand-refereeRegistry"`

**Expected Result:**
- The text "config fingerprint 08e471b10130e1e2" appears
- This is the exact fingerprint value this iteration's own backend check independently re-verifies
  (dev handoff: `Config().config_fingerprint()` → `08e471b10130e1e2`, zero new `Config` fields
  added) — a mismatch here would mean the frozen foundation moved, which this iteration must not
  touch

---

### UT-08 — Referee Adjudications and Runs sections still render their honest-empty states (regression — J-10 steps 12–13)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Referee Adjudications section, Referee Runs section

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click `data-testid="desk-section-expand-refereeAdjudications"`
3. Verify the text "No hypotheses registered" appears
4. Click `data-testid="desk-section-expand-refereeRuns"`
5. Verify the text "No evaluation runs recorded yet." appears

**Expected Result:**
- Both empty-state messages appear exactly as written above — neither section shows a fabricated
  row, a loading spinner that never resolves, or an error message in place of the honest-empty
  state

---

## Absent Test Categories (and why)

- **Happy-path / validation / error tests for a new UI capability:** not written. This iteration
  ships no new form, button, or page — writing one would invent a UI surface the diff does not
  contain.
- **The Validation Vault's own mechanics** (universe registration, seal assignment, the
  sealed/assigned/exposed transitions, TR-2/4/12/20): not browser-tested — there is no UI to click.
  Covered entirely by `apps/backend/tests/test_vault.py`'s 24 tests and the TC-1 through TC-9
  scenarios in the dev handoff.
- **The exposure-registry sealed filter**: not browser-tested — it fires only inside a diagnostic
  walk-forward code path with no `/desk` section (J-08 scope). Covered by
  `apps/backend/tests/test_walkforward.py`'s new TC-10/TC-11 tests.
- **The two new §2.6 manifest fields**: not browser-tested directly — UT-03 above proves their
  absence from the UI (no new column), which is the correct UI-facing assertion for a storage-only
  capability with no consumer this iteration. Their correctness is covered by
  `apps/backend/tests/test_datasets.py`'s new TC-12/TC-13 tests and
  `apps/backend/tests/test_tick_recorder.py`'s new test.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Validation Vault section genuinely absent from `/desk` | smoke | P1 | `/desk` |
| UT-02 | No Scout Ledger/Walk-Forward section on `/desk` | regression | P1 | `/desk` |
| UT-03 | Microscope Readiness shows fixture-rig corpus data, no new columns | regression | P1 | `/desk` → Microscope Readiness |
| UT-04 | Cockpit ticker watch still works | regression | P1 | `/` |
| UT-05 | `/structure` Tradable Map still loads | regression | P1 | `/structure` |
| UT-06 | Playbook Evidence section still renders | regression | P1 | `/desk` → Playbook Evidence |
| UT-07 | Referee Registry shows frozen fingerprint | regression | P1 | `/desk` → Referee Registry |
| UT-08 | Referee Adjudications/Runs honest-empty states | regression | P1 | `/desk` → Referee Adjudications, Referee Runs |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-01 is this iteration's genuinely
new check — the absence proof J-06's own acceptance criteria requires. UT-03's expected values are
independently reconfirmed against the fixture files (not merely copied forward) and match last
iteration's equivalent, corrected assertion. UT-04 through UT-08 collectively re-run
`journey-scripts/J-10.json`'s 13-step sentinel by surface.
