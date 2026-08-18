# Phase goal-rapid-microscope-iter-7 — UI Test Plan

**Phase:** goal-rapid-microscope-iter-7
**Date:** 2026-08-18
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301 (store-scoped rig — do NOT point at the real
`.data/datasets` store; the rig seeds exactly 2 committed PG fixture datasets by design, never the
real 18-dataset/12-symbol-day corpus)

---

**Why this plan is regression-only:** this iteration's diff is 6 backend Python source files plus 2
test files, zero frontend changes (confirmed via `git status`; see
`reports/phase-goal-rapid-microscope-iter-7-ui-surface-map.md`). There is no new capability, form,
or page to design happy-path, validation, or error test cases around — writing any would invent a
surface that does not exist. Instead, every test case below re-verifies a pre-existing surface,
because `Frontend Present: yes` is this iteration's mechanism for letting the browser-QA lane
dispatch the required-still-passing regression set and the J-10 sentinel. The two new backend entry
points this iteration adds — the optional trade/quote preservation fields and the `--family
tick_legacy` CLI flag — have no UI wiring at all; they are covered by the backend test suite
(TC-1/TC-2/TC-3/TC-6/TC-7/TC-9 in `docs/handoffs/goal-rapid-microscope-iter-7-dev.md`), not by a
browser test here.

**Correction versus the last iteration's equivalent plan:** iteration 6's Microscope Readiness test
asserted the real store's `Distinct symbol-days = 12` / `Distinct datasets = 18` against this same
fixture-scoped rig and failed spuriously as a result — the rig structurally cannot show those
numbers (`docs/handoffs/goal-rapid-microscope-iter-6-audit.md`, finding E3). UT-02 below is pinned
to what the rig actually seeds instead: 1 symbol-day / 2 datasets, both symbol PG, session date
2026-06-09.

**Preconditions for the whole plan:**
- Backend running at `http://localhost:8301` against the store-scoped rig (start via
  `apps/backend/scripts/start_scoped_qa_backend.sh`), healthy (`GET /health` returns
  `{"status":"ok"}`).
- Frontend running at `http://localhost:3301`, after a clean `rm -rf apps/frontend/.next` rebuild
  (the plan's own T-9 instruction, to rule out a stale build masking real evidence).
- No login/auth required (this product has none).

---

## Test Cases

### UT-01 — `/desk` loads without errors, all 10 sections present, no "Scout Ledger" section (smoke + regression J-02/J-03/J-04)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301
- Backend is running at http://localhost:8301

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load
3. Scroll from the top of the page to the bottom, passing every collapsible section header

**Expected Result:**
- The heading "Playbook Signals" is visible
- No blank screen, no error banner, no unhandled exception in the browser console
- Exactly 10 section headers are present in this order (top to bottom, after Playbook Signals):
  Top-up Runs, Index Reconciliation, Screen Runs, (Screen Comparison and Provenance if a screen was
  computed), Playbook Evidence, Referee Registry, Referee Adjudications, Referee Runs, Microscope
  Readiness (last)
- No section titled "Scout Ledger", "Walk-Forward", or "Validation Vault" exists anywhere on the
  page — this is expected, not a gap (that UI is J-08 scope, not yet built); this satisfies J-02's,
  J-03's, and J-04's "no dedicated UI element of their own" regression check, since none of the
  three has a browser surface to test more specifically

---

### UT-02 — Microscope Readiness shows the fixture rig's real (2-dataset) corpus data, no new columns (regression — J-01, J-06 byte-compat)

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
- Both rows' "Exposure state" column read `exploratory` (never `hand_assigned` or
  `historical_oos`)
- The shard table's header row has exactly 12 columns, in this order: Symbol, Session date, Feed,
  Window (ET), Trades, Quotes, Bytes, Coverage gaps, Fallback frac, Checksum, Split provenance,
  Exposure state — **no new column** for `conditions`, `exchange`, `tape`, `trade_id`,
  `schema_basis`, or `quote_size_unit`. This is the load-bearing assertion for this iteration
  specifically: it proves J-06 step 1's new optional preservation fields (added to the backend
  pipeline this iteration) are not surfaced anywhere in the UI yet, exactly as the plan scopes them

---

### UT-03 — Cockpit ticker watch still works (regression — J-10 steps 1–3)

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
  depend on this iteration's Alpaca historical-recording provider changes

---

### UT-04 — `/structure` Tradable Map still loads (regression — J-10 steps 4–7)

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
  page reads the Yahoo/BarStore bar pipeline, entirely separate from this iteration's Alpaca
  trade/quote provider diff
- No error message replaces the expected band text

---

### UT-05 — Playbook Evidence section still renders real signals (regression — J-10 steps 8–10)

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

### UT-06 — Referee Registry section still shows the frozen fingerprint (regression — J-10 step 11)

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
- This is the exact fingerprint value this iteration's own backend check (TC-4/TC-10,
  `Config().config_fingerprint()`) independently re-verifies — a mismatch here would mean the
  frozen foundation moved, which this iteration must not touch

---

### UT-07 — Referee Adjudications and Runs sections still render their honest-empty states (regression — J-10 steps 12–13)

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

### UT-08 — Microscope Readiness section is discoverable without prior knowledge (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/desk` navigation / section list

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll down through the page's collapsible sections without using browser search (Ctrl+F)

**Expected Result:**
- A section labeled "Microscope Readiness" is visible as the last section on the page, directly
  below "Referee Runs" — reachable by scrolling alone, no more than a few seconds of scanning
- The section header text is human-readable ("Microscope Readiness"), not an internal code name

---

## Absent Test Categories (and why)

- **Happy-path / validation / error tests:** not written. This iteration ships no new form, button,
  or page — writing one would invent a UI surface the diff does not contain.
- **The new `--family tick_legacy` CLI flag:** not browser-tested. It has no UI wiring — it is a
  terminal-only tool covered by the backend suite (`test_walkforward.py`'s new TC-6 test, plus TC-7
  the developer ran by hand against the real store). `POST /walkforward/compute`'s route-level
  family parameter is explicitly deferred, so there is no route for a UI test to exercise either.
- **The new trade/quote preservation fields:** not browser-tested directly — UT-02 above proves
  their absence from the UI (no new column), which is the correct UI-facing assertion for a
  storage-only capability with no consumer yet. Their correctness is covered by the backend suite
  (`test_datasets.py`'s new TC-1/TC-2/TC-3/TC-9 tests).

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads, all 10 sections present, no Scout Ledger section | smoke | P1 | `/desk` |
| UT-02 | Microscope Readiness shows fixture-rig corpus data, no new columns | regression | P1 | `/desk` → Microscope Readiness |
| UT-03 | Cockpit ticker watch still works | regression | P1 | `/` |
| UT-04 | `/structure` Tradable Map still loads | regression | P1 | `/structure` |
| UT-05 | Playbook Evidence section still renders | regression | P1 | `/desk` → Playbook Evidence |
| UT-06 | Referee Registry shows frozen fingerprint | regression | P1 | `/desk` → Referee Registry |
| UT-07 | Referee Adjudications/Runs honest-empty states | regression | P1 | `/desk` → Referee Adjudications, Referee Runs |
| UT-08 | Microscope Readiness discoverable | ux | P2 | `/desk` navigation |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-02's expected values are corrected
against last iteration's spuriously-failing equivalent (see the note under "Why this plan is
regression-only" above) — a re-run of the same mistake this iteration would be a false regression
signal, not a real one. UT-03 through UT-07 collectively re-run `journey-scripts/J-10.json`'s
13-step sentinel by surface.
