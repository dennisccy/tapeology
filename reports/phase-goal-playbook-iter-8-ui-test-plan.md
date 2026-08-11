# Phase goal-playbook-iter-8 — UI Test Plan

**Phase:** goal-playbook-iter-8
**Date:** 2026-08-11
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301 (scoped fixture rig only — never the operator's real
`:8301`/`.data/` store)

---

## Setup (required before running any test below)

The evidence table and the Playbook Signals rows below depend on the iter-8 scoped fixture corpus
(2026-06-22 Capitulation/Range Trade/Double Top signals, 2026-06-25 open-high-break evidence corpus).
Start the scoped rig, not the operator's ambient backend:

```
bash apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh /tmp/playbook-iter8-fixture-qa 8301
rm -rf apps/frontend/.next
CHAIN_FRONTEND_PORT=3301 CHAIN_BACKEND_PORT=8301 bash scripts/start-frontend.sh
```

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/desk` loads and the Playbook Evidence panel is present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Scoped fixture rig running (see Setup above)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to finish loading (loading skeletons resolve)
3. Scroll to the bottom of the page

**Expected Result:**
- Page renders without a blank screen or error page
- A bordered panel with the heading "Playbook Evidence" is visible below the "Backscan" panel
- Inside it, a disclosure paragraph is visible starting with "every recorded playbook signal at ONE
  input signature..."
- No browser console errors

---

### UT-02 — Well-populated and below-min-n cells are both legible (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — Playbook Evidence cells table

**Preconditions:**
- UT-01 passed; scoped fixture rig running with the iter-8 evidence corpus seeded

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll to the "Playbook Evidence" panel
3. In the cells table (`data-testid="desk-evidence-cells-table"`), locate a row for setup
   `open_high_break`, side `long` with a Signal `n` value ≥ 12 (not tagged "low n")
4. In the same table, locate a row for setup `open_high_break`, side `long` whose Flag column shows
   the amber "low n" badge

**Expected Result:**
- Both rows are visible in the table (scroll/zoom out if needed to fit in one view)
- The `n >= 12` row's Signal median/p25/p75/mean columns show numeric values (not blank)
- The "low n" row's Flag column shows a badge reading exactly "low n" in amber styling
- The "low n" row's Signal median/p25/p75/mean columns STILL show numeric values (not blank, not
  "null", not hidden) — thin data is tagged, never suppressed

---

### UT-03 — Invalidation breaches table renders with real counts (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — Playbook Evidence breach table

**Preconditions:**
- UT-01 passed

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll past the Playbook Evidence cells table to the "Invalidation breaches" heading
   (`data-testid="desk-evidence-breach-table"`)

**Expected Result:**
- A table with columns Setup / Side / Horizon / Breached / Total is visible
- At least one row shows a numeric value (including possibly 0) in both the "Breached" and "Total"
  columns — neither column is blank or shows "undefined"

---

### UT-04 — Backscan "from day" field tolerates a half-typed date (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/desk` — Backscan panel

**Preconditions:**
- Navigate to the Backscan panel (above the Playbook Evidence panel)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll to the "Backscan" panel
3. Click into the "Backscan from day" field (`data-testid="desk-backscan-from-input"`) and clear it
4. Type `2026-06-2` (a deliberately half-typed date, one digit short) into the field
5. Wait 2 seconds for the plan preview to auto-refetch

**Expected Result:**
- No element with `data-testid="desk-backscan-plan-error"` (red error text) appears
- The plan preview (`data-testid="desk-backscan-plan"`) shows the text "0 dates planned · 0 missing
  at the current signature." — never a raw error, stack trace, or blank panel

---

### UT-05 — Playbook Evidence shows an honest "unavailable" state, never a fabricated table (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk` — Playbook Evidence panel

**Preconditions:**
- Scoped fixture rig running

**Steps:**
1. Navigate to `http://localhost:3301/desk` and confirm the Playbook Evidence panel loads normally
   (as in UT-01)
2. Stop the scoped backend process (`Ctrl+C` the `qa_playbook_iter7_fixture_scoped_backend.sh`
   process, or `kill` the process bound to port 8301)
3. Reload `http://localhost:3301/desk` (F5)
4. Scroll to the "Playbook Evidence" panel

**Expected Result:**
- An amber-bordered panel with `data-testid="desk-evidence-unavailable"` is shown in place of the
  cells table
- Its text reads "The playbook evidence view could not be loaded." (or a more specific fetch-error
  message) followed by "Nothing cached and nothing fabricated is shown in its place."
- The page does NOT show a crashed/blank layout, and no cell values are fabricated or left over from
  the prior successful load
5. Restart the scoped backend afterward (`bash apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh /tmp/playbook-iter8-fixture-qa 8301`) before running any further test in this plan

---

### UT-06 — Capitulation signal row still works after the J-05 assertion fix (regression)

**Type:** regression
**Priority:** P3
**Surface:** `/desk` — Playbook Signals section

**Preconditions:**
- Scoped fixture rig running

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Locate the "Playbook Signals" date field (`data-testid="desk-playbook-date-input"`), clear it,
   and type `2026-06-22`
3. Wait for the signals list to refresh
4. Locate a row whose setup cell (`data-testid="desk-playbook-signal-setup"`) reads "Capitulation"
   for symbol "DECOR"
5. Click the "DECOR" row

**Expected Result:**
- A "Capitulation" row for symbol DECOR is visible in the list
- After clicking, the expanded detail includes the text "euphoria recent"

---

### UT-07 — Range Trade and Double Top rows still expand correctly (regression, new J-06 coverage)

**Type:** regression
**Priority:** P3
**Surface:** `/desk` — Playbook Signals section

**Preconditions:**
- Scoped fixture rig running

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the "Playbook Signals" date field (`data-testid="desk-playbook-date-input"`), clear it and
   type `2026-06-22`
3. Locate a row whose setup cell reads "Range Trade", then click the "RTAAA" symbol/row
4. Locate a row/chip labeled "Double Top" and click it (do NOT click on the symbol text "DTAAA" —
   that symbol fires two different signals that day and the symbol click can hit the wrong one; click
   the "Double Top" chip specifically)

**Expected Result:**
- After step 3: the geometry disclosure line (`data-testid="desk-playbook-signal-range-trade-geometry"`)
  appears and is legible, including phrases like "MBR wide", "zone touches", and "broke at slot"
- After step 4: the geometry disclosure line
  (`data-testid="desk-playbook-signal-double-extreme-geometry"`) appears

---

### UT-08 — A non-default signature is listed but never folded into the main cells table (regression / data-integrity)

**Type:** regression
**Priority:** P3
**Surface:** `/desk` — Playbook Evidence panel

**Preconditions:**
- Scoped fixture rig running with more than one recorded playbook signature present (true by
  default on the seeded scoped rig — an older signature exists alongside the current default)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll past the Invalidation breaches table to the "Other signatures (listed, never pooled)"
   heading (`data-testid="desk-evidence-other-signatures"`)
3. Note the signature string and date count shown in the list
4. Scroll back up to the main cells table and note the `n` value for the
   `(open_high_break, long, 5m)` row

**Expected Result:**
- The "Other signatures (listed, never pooled)" section is visible and shows at least one entry with
  a signature string, an "N date(s)" count, and a created-span date range
- The `n` value noted in step 4 matches only the current-signature record count — it does not
  increase or change based on the other signature's own date count from step 3 (confirms the fold
  pools exactly one signature)

---

### UT-09 — Playbook Evidence is discoverable without any navigation change (ux)

**Type:** ux
**Priority:** P3
**Surface:** navigation / `/desk`

**Steps:**
1. Navigate to `http://localhost:3301` (the Cockpit / home page)
2. Look at the top navigation bar (`data-testid="app-nav"`)
3. Click the "Desk" link
4. Scroll down the resulting `/desk` page to the bottom

**Expected Result:**
- The nav bar shows exactly three links: "Cockpit", "Structure", "Desk" — no new nav entry for
  "Evidence" or "Playbook Evidence" was added (this is expected — the feature is a scroll-down
  section, not a new route)
- Scrolling to the bottom of `/desk` reveals the "Playbook Evidence" panel within 2–3 scroll actions
  from the top of the page, with a clear, non-technical heading ("Playbook Evidence")

---

### UT-10 — The rendered table matches the API response verbatim (happy path / consistency)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` + `GET /research/desk/playbook/evidence`

**Preconditions:**
- Scoped fixture rig running

**Steps:**
1. Run `curl http://localhost:8301/research/desk/playbook/evidence` and note the `signal.n` value
   for the cell where `setup_id == "open_high_break"`, `side == "long"`, `measure == "5m"`
2. Navigate to `http://localhost:3301/desk` in the browser
3. In the Playbook Evidence cells table, locate the row for setup `open_high_break`, side `long`,
   measure `5m`
4. Compare the on-screen `n` value (Signal column, `data-testid="desk-evidence-signal-n"`) to the
   value noted in step 1

**Expected Result:**
- The on-screen value is identical to the value returned by the raw API call — no rounding,
  recomputation, or discrepancy (the frontend performs no client-side arithmetic on this field)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads, Playbook Evidence panel present | smoke | P1 | `/desk` |
| UT-02 | Well-populated + below-min-n cells legible | happy-path | P1 | `/desk` cells table |
| UT-03 | Invalidation breaches table populated | happy-path | P1 | `/desk` breach table |
| UT-04 | Backscan half-typed date tolerated | validation | P2 | `/desk` Backscan panel |
| UT-05 | Evidence panel honest-unavailable on backend down | error | P2 | `/desk` Evidence panel |
| UT-06 | Capitulation row still works (J-05 fix) | regression | P3 | `/desk` Playbook Signals |
| UT-07 | Range Trade / Double Top rows still work (J-06) | regression | P3 | `/desk` Playbook Signals |
| UT-08 | Other signature listed, never pooled | regression | P3 | `/desk` Evidence panel |
| UT-09 | Feature discoverable, nav unchanged | ux | P3 | nav / `/desk` |
| UT-10 | On-screen value matches raw API verbatim | happy-path | P1 | `/desk` + API |

**P1 tests must all pass for browser QA verdict to be PASS.**
