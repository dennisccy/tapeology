# goal-rapid-microscope-iter-11 — UI Test Plan

**Phase:** goal-rapid-microscope-iter-11
**Date:** 2026-08-19
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301 (pinned port, per dev handoff)

---

## Context for the tester

This iteration shipped **zero new UI capability** — it is a backend data-visibility correctness
fix (closing the "opaque research pool" leak: a recorded tranche must stay unidentifiable while any
of its members are unresolved). Every test below is therefore a **regression** check: proving the
already-shipped surfaces still render exactly as before, because the real data store has **zero
registered vault universes** today (no `micro_vault` ledger directory exists under
`apps/backend/.data`), which makes every backend change in this iteration provably inert against
production data right now. There is no "happy path" or "validation" test to author because no form,
button, or new field was added.

---

## Test Cases

---

### UT-01 — `/desk` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Backend running at http://localhost:8301 (`bash scripts/start-backend.sh`)
- Frontend running at http://localhost:3301 (`bash scripts/start-frontend.sh`)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to finish its initial data fetches (loading spinners resolve)

**Expected Result:**
- Page renders without a blank screen or a top-level error message
- The "Microscope Readiness" panel heading is visible near the bottom of the page
- No new browser console errors appear beyond whatever the pre-iteration baseline already showed

---

### UT-02 — `/structure` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Backend and frontend running (see UT-01)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the page to finish its initial data fetches

**Expected Result:**
- Page renders without a blank screen or a top-level error message
- The "Comparison" panel heading is visible
- No new browser console errors appear beyond the pre-iteration baseline

---

### UT-03 — Cockpit live tape and chart still work (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Cockpit)

**Preconditions:**
- Backend and frontend running

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Observe the price chart area for ~10 seconds
3. Observe the live tape panel for ~10 seconds

**Expected Result:**
- The price chart renders candles, not a blank canvas or an "Unavailable" panel
- The live tape panel shows an actively updating feed (a new tick/row appears within the
  observation window, or an explicit "connected/live" indicator is shown) — no error banner
- Nothing about this view differs from its pre-iteration behavior (this iteration touched no
  Cockpit-related file)

---

### UT-04 — `/desk` Microscope Readiness shard table is unchanged (regression, core proof)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` — Microscope Readiness — "Legacy Tick Shards" table

**Preconditions:**
- Backend and frontend running
- Real `.data` store has zero registered vault universes (current, expected state)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll down to the "Microscope Readiness" panel (the last section on the page)
3. In the "Legacy Tick Shards" table, read the "Symbol" and "Session Date" columns for every row

**Expected Result:**
- The table shows the same set of shard rows, in the same order, with the same Symbol / Session
  Date / Checksum values as the pre-iteration baseline
- No row is missing (would mean the new predicate is over-withholding) and no row is new (would
  mean nothing — the real store cannot gain a new dataset from this diff)
- The "Sealed" state column values (`shard.exposure_state`) are unchanged per row

---

### UT-05 — `/structure` Comparison dataset dropdown is unchanged (regression, core proof)

**Type:** regression
**Priority:** P1
**Surface:** `/structure` — Comparison panel — "Dataset" dropdown

**Preconditions:**
- Backend and frontend running

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Scroll down to the "Comparison" panel
3. Click the "Dataset" dropdown (below the "Dataset" label, left of the disabled "Run" button)
4. Count the options listed (excluding the placeholder "Choose a dataset…")

**Expected Result:**
- Exactly 18 dataset options are listed (the count the developer verified via a live curl against
  the running server immediately before handoff)
- Each option reads `SYMBOL · split · 8-char-id` (e.g. `AAPL · train · a1b2c3d4`)
- No option is missing compared to the pre-iteration baseline

---

### UT-06 — `/structure` Edge Report panel is unchanged (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/structure` — "Edge Report" panel

**Preconditions:**
- Backend and frontend running

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Scroll to the "Edge Report" panel

**Expected Result:**
- If the report is already computed: the v1 / structure_tape / structure_tape_map comparison
  table's per-cell n, R, and $ values match the pre-iteration baseline exactly
- If not yet computed: the "not computed yet" panel and its Compute control appear exactly as
  before — no new error state
- Either way, nothing differs from before this iteration (the dataset corpus this panel draws from
  is unaffected by the withhold-predicate change today)

---

### UT-07 — `/structure` Case Studies panel is unchanged (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/structure` — "Case Studies" panel

**Preconditions:**
- Backend and frontend running

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Scroll to the "Case Studies" panel
3. Leave the symbol and reaction filters at their default ("all") values

**Expected Result:**
- The event table's row count matches the pre-iteration baseline exactly
- No event row is missing or newly present

---

### UT-08 — `/desk` Screen-related panels are unchanged (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/desk` — "Screen history" and "Screen Runs" sections

**Preconditions:**
- Backend and frontend running

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll to the "Screen history" section
3. Scroll to the "Screen Runs" section

**Expected Result:**
- Both sections list the same runs, with the same result/member counts, as the pre-iteration
  baseline
- No new error or empty state appears where data previously rendered

---

### UT-09 — `/desk` full-page sentinel walk (regression, J-10 kept-product check)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` — every remaining shipped section

**Preconditions:**
- Backend and frontend running

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll from the top of the page to the bottom in one pass, pausing briefly at each section
   heading: "Forward Returns", "Briefing", "Skipped members", "Top-up runs", "Index
   Reconciliation", "Provenance", "Playbook Signals", "Backscan", "Playbook Evidence", "Referee
   Registry", "Referee Adjudications", "Referee Runs"

**Expected Result:**
- Every section listed renders its own data-or-empty-state panel — no section shows a blank white
  area, a stuck "Loading…" spinner, or an "Unavailable" panel with a network-error message
- This matches the plan's required "J-10 kept-product sentinel walk" — the whole page must still
  work end-to-end even though this iteration touched none of its rendering code

---

### UT-10 — Top navigation is unaffected (ux)

**Type:** ux
**Priority:** P3
**Surface:** navigation bar (all pages)

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Look at the top navigation bar
3. Click "Structure" in the nav bar
4. Click "Desk" in the nav bar
5. Click "Cockpit" in the nav bar

**Expected Result:**
- After step 2: the nav bar shows exactly 3 links — "Cockpit", "Structure", "Desk"
- After step 3: URL is `http://localhost:3301/structure`, and "Structure" is shown as the active
  (highlighted) link
- After step 4: URL is `http://localhost:3301/desk`, and "Desk" is shown as the active link
- After step 5: URL is `http://localhost:3301/`, and "Cockpit" is shown as the active link

---

### UT-11 — Recorder-progress endpoint serves aggregate-only data, no identity leak (API check, no browser)

**Type:** error
**Priority:** P2
**Surface:** `GET /research/desk/micro/recorder/compute` (no UI — API-only check)

**Preconditions:**
- Backend running at http://localhost:8301

**Steps:**
1. In a terminal, run: `curl -s http://localhost:8301/research/desk/micro/recorder/compute`
2. Inspect the returned JSON's `progress` object

**Expected Result:**
- The `progress` object contains exactly these 10 fields and no others: `chunks_total`,
  `chunks_done`, `chunks_fetched`, `chunks_reused`, `chunks_unchanged`, `chunks_failed`,
  `trades_total`, `quotes_total`, `percent_complete`, `elapsed_seconds`
- No `outcomes` key exists anywhere in the response
- No field named `symbol`, `date`, or `dataset_id` appears anywhere in the JSON body
- This is not a browser/UI test — there is no rendered panel for this endpoint yet — but it is the
  single most direct, independently-executable proof that this iteration's core fix holds

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads | smoke | P1 | `/desk` |
| UT-02 | `/structure` loads | smoke | P1 | `/structure` |
| UT-03 | Cockpit tape/chart | regression | P1 | `/` |
| UT-04 | Microscope Readiness shard table unchanged | regression | P1 | `/desk` |
| UT-05 | Comparison dataset dropdown unchanged | regression | P1 | `/structure` |
| UT-06 | Edge Report panel unchanged | regression | P2 | `/structure` |
| UT-07 | Case Studies panel unchanged | regression | P2 | `/structure` |
| UT-08 | Screen panels unchanged | regression | P2 | `/desk` |
| UT-09 | Full-page sentinel walk (J-10) | regression | P1 | `/desk` |
| UT-10 | Nav bar unaffected | ux | P3 | nav |
| UT-11 | Recorder-progress aggregate-only, no leak | error | P2 | API (no UI) |

**P1 tests must all pass for browser QA verdict to be PASS.**
