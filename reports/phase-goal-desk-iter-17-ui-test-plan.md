# Phase goal-desk-iter-17 — UI Test Plan

**Phase:** goal-desk-iter-17 (J-13 — every ranked row discloses the price its wall sits at)
**Date:** 2026-07-29
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301

---

## Data used by this plan

This plan is grounded in the REAL `apps/backend/.data/screen` store as read live from the running
rig on 2026-07-29 (`GET http://localhost:8301/research/desk/screen` — the same store the running
`/desk` page at `http://localhost:3301/desk` serves; nothing here is fabricated).

**The live `latest` snapshot right now:** `id=screen-2026-07-28-ac07c9581a4f`,
`screen_date=2026-07-28`, 63 ranked rows, 38 skipped. **Every one of its 63 ranked rows was recorded
before this iteration's backend code existed**, so `"reference_close"` is entirely absent from every
row in the raw JSON (verified: `grep -c reference_close` on the full response returns 0 hits). This
means **every row currently visible on the live `/desk` page shows the honest
`"close not recorded in this snapshot"` fallback — there is no populated example on the ambient
store today.** This is a disclosed, expected state (see the dev handoff's Known Issues note and the
QA report's TC-06 result), not a defect — UT-03/UT-06 below test exactly this honest state, and
UT-05/UT-10 cover the populated case and the gap explicitly.

Two rows used as concrete, exact-value grounding throughout this plan:

| Field | `BRK-B` row (in-band, `distance_bps 0.0`) | `LIN` row (out-of-band, `distance_bps` non-zero) |
|---|---|---|
| side | `support` | `resistance` |
| band_class | `A` | `A` |
| distance_bps | `0.0` → displayed `0.00 bps` | `0.19709369376124322` → displayed `0.20 bps` |
| band_score | `1787.0` → displayed `1787.00` | `273.0` → displayed `273.00` |
| price_low / price_high | `488.5` / `490.8500061035156` → displayed `488.50`–`490.85` | `506.3299865722656` / `509.6099853515625` → displayed `506.33`–`509.61` |
| coverage | all 4 timeframes (`1h`/`4h`/`1d`/`1w`) lit (`has_bars: true`) | all 4 timeframes lit |
| tick_evidence | `false` (no badge) | `false` (no badge) |
| basis_as_of | `2026-07-23T04:00:00.000000Z` → cell shows `basis 2026-07-23 · 5 d before as-of` | same: `basis 2026-07-23 · 5 d before as-of` |
| history_sessions / history_start | `500` / `2024-07-25T04:00:00.000000Z` → cell shows `history 500 sessions · from 2024-07-25` | same |
| **band (NEW this iteration)** | `"close not recorded in this snapshot"` (legacy row) | `"close not recorded in this snapshot"` (legacy row) |

**If the store has changed by the time these tests run** (a new screen was computed since
2026-07-29): re-locate the current `latest` snapshot via the same GET, confirm whether any row now
carries `reference_close`, and substitute that row's own values into UT-03/UT-04/UT-06 using the same
relative logic (a populated row uses UT-05's pattern instead of UT-03's fallback pattern).

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — `/desk` loads and the ranked table's new `band` header cell is present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301
- Backend is reachable and serving the real ambient desk store
- No login required

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load
3. Locate the ranked-rows table (`data-testid="desk-screen-rows-table"`, inside the "Briefing"
   section)
4. Scroll the table horizontally to its rightmost edge if it does not already fit the viewport width

**Expected Result:**
- The heading "Desk" is visible, no blank screen, no "The desk screen could not be loaded." panel
- The ranked table's header row is visible and its LAST (rightmost) header cell reads exactly
  `band` (lower case, no colon)
- No console errors

---

### UT-02 — Ranked table header shows exactly ten columns in the exact new order (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk` — ranked-rows table header

**Preconditions:**
- Same as UT-01

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the ranked table's header row, read every `<th>` cell left to right
3. Count the total number of header cells

**Expected Result:**
- Exactly 10 header cells, in this exact order:
  `symbol, side, class, distance, score, coverage, tick evidence, basis, history, band`
- `band` is the 10th and final cell — no header appears after it
- This is one more column than the nine that existed before this iteration (`band` is the only
  addition)

---

### UT-03 — Every currently-recorded ranked row shows the honest `"close not recorded in this snapshot"` fallback (happy path — current true state)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — `DeskRow` band cell, `data-testid="desk-row-band"`

**Preconditions:**
- The real ambient store's `latest` snapshot is `screen-2026-07-28-ac07c9581a4f` (63 rows, all
  recorded before this iteration's code — see "Data used by this plan" above)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the ranked table, find the row whose leftmost (`symbol`) cell reads exactly `BRK-B`
3. Read that row's rightmost cell (`data-testid="desk-row-band"`, the new `band` column)
4. Repeat steps 2–3 for the row whose `symbol` cell reads `LIN`

**Expected Result:**
- The `BRK-B` row's `band` cell contains exactly the text `close not recorded in this snapshot` —
  no numbers, no `band X–Y` pattern
- The `LIN` row's `band` cell contains the identical text `close not recorded in this snapshot`
- Every OTHER visible ranked row's `band` cell also reads this exact same fallback text (spot-check
  at least 3 more rows) — none show numeric band/close values, because every row in this snapshot
  predates the field

---

### UT-04 — Row's composite hover tooltip carries the full-precision band/close segment after basis/history (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — `deskRowDrillInTitle` composite tooltip

**Preconditions:**
- Same live store as UT-03 (`BRK-B` row present, legacy/fallback state)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Locate the `BRK-B` ranked row
3. Hover the mouse anywhere over that row (the drill-in anchor is stretched across the entire row,
   so any point works) and wait for the browser's native tooltip to appear — or, without a real
   mouse, read the `title` attribute of `document.querySelector('tr[data-symbol="BRK-B"] a')`
4. Read the full tooltip text

**Expected Result:**
- The tooltip text is exactly:
  `distance 0 bps · score 1787 · basis 2026-07-23T04:00:00.000000Z (5 d before as-of) · history 500 sessions from 2024-07-25T04:00:00.000000Z · close not recorded in this snapshot · 1h window last requested: 2026-07-25T00:00:00Z · 4h window last requested: 2026-07-25T00:00:00Z · 1d window last requested: 2026-07-25T00:00:00Z · 1w window last requested: 2026-07-25T00:00:00Z`
  (exact numeric formatting of `distance`/`score` may render as `0` and `1787` respectively — this
  is JavaScript's default `String()` coercion of `0.0`/`1787.0`, not `fmt()`'s 2-decimal rounding
  used in the visible cells)
- The new close/band segment (`close not recorded in this snapshot`) appears immediately AFTER the
  `history` segment and BEFORE the coverage (`1h window last requested: ...`) segments — matching
  the source order in `deskRowDrillInTitle` (`apps/frontend/app/desk/page.tsx:260-279`)
- No separate/new `title` attribute exists on the `band` `<td>` cell itself
  (`document.querySelector('[data-testid="desk-row-band"]')`'s own `title` attribute is `null` or
  absent) — the F2 lesson: only the row's ONE composite anchor tooltip carries this detail

---

### UT-05 — A newly-computed screen's `band` column shows a populated in-band row and out-of-band row, both legible in one screenshot (happy path — TC-6 acceptance)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — `DeskRow` band cell on a NEW (non-legacy) snapshot

**Preconditions:**
- A scoped backend rig is running (NEVER pointed at `apps/backend/.data`) with its own
  `TAPEOLOGY_DESK_SCREEN_DIR` / `TAPEOLOGY_DESK_UNIVERSE_DIR` / `TAPEOLOGY_BAR_DIR` (and any other
  store-path env var this era's scoped-rig convention uses — see `test_desk_screen.py`'s `ctx`
  fixture for the authoritative list) pointed at fresh, empty temp directories, per the
  iter-9/11/14/15/16 scoped-rig discipline this phase's own NOTES section requires
- That scoped rig's universe/bar stores are seeded (fixture or real) so that computing a screen
  produces at least one ranked row with `distance_bps == 0.0` (its `reference_close` sits ON a band
  edge) and at least one ranked row with `distance_bps != 0.0` (its `reference_close` sits outside
  its band) — the same two-case shape `test_reference_close_golden_in_band_and_out_of_band_rows`
  (`apps/backend/tests/test_desk_screen.py:1035`) already proves at the API layer
- The target store was checked for an existing snapshot under the same five pins before computing
  (iter-10 lesson) — no collision, or any unavoidable collision disclosed in the executing lane's
  own report
- The frontend at the scoped rig's own port is built/configured to read from that scoped backend
  (never `apps/backend/.data`) — the capturing lane must assert the captured page's own origin
  matches the rig's own base URL (iter-16 lesson) before treating any screenshot as evidence

**Steps:**
1. On the scoped rig's own frontend URL (NOT `http://localhost:3301`, which serves the live
   ambient store), trigger a NEW screen compute for the seeded pins — either via the `/desk` page's
   "Run Screen" button or the scoped backend's own `POST /research/desk/screen/compute`
2. Wait for the compute to finish (the button's label reads "Computing…" while in flight, and reverts
   to "Run Screen" — or the page re-renders with the new snapshot — on completion)
3. Navigate to (or stay on) `/desk` on that scoped rig
4. In the ranked table, locate one row whose `distance` cell reads `0.00 bps` and one row whose
   `distance` cell reads a non-zero value
5. Read both rows' `band` cells
6. Take one screenshot showing both rows together

**Expected Result:**
- The in-band row's `band` cell reads `band <low>–<high> · close <val>` where `<val>` is numerically
  between (or equal to an edge of) `<low>` and `<high>` — e.g. `band 488.50–490.85 · close 488.50`
- The out-of-band row's `band` cell reads the same pattern, but `<val>` lies OUTSIDE the `<low>`–
  `<high>` range it shows — e.g. `band 506.33–509.61 · close 505.40`
- Both cells show three legible numeric values (never blank, never `NaN`, never the fallback text)
- Both rows are visible together in the one captured screenshot

---

### UT-06 — Pre-existing columns' exact content is unchanged for `BRK-B`/`LIN` after the `band` column addition (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` — `DeskRow` cells other than `band`

**Preconditions:**
- Same live ambient store as UT-03/UT-04

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Locate the `BRK-B` row and read its `side`, `class`, `distance`, `score`, `basis`, and `history`
   cells
3. Locate the `LIN` row and read the same six cells

**Expected Result:**
- `BRK-B`: `side` = `support`; `class` = `Class A` with caption `nearest same-class band`;
  `distance` = `0.00 bps`; `score` = `1787.00`; `basis` = `basis 2026-07-23 · 5 d before as-of`;
  `history` = `history 500 sessions · from 2024-07-25`
- `LIN`: `side` = `resistance`; `class` = `Class A` with caption `nearest same-class band`;
  `distance` = `0.20 bps`; `score` = `273.00`; `basis` = `basis 2026-07-23 · 5 d before as-of`;
  `history` = `history 500 sessions · from 2024-07-25`
- Both rows' `coverage` cells show all four timeframe badges (`1h`/`4h`/`1d`/`1w`) in the LIT
  (green) style, and neither row shows a tick-evidence badge (`tick_evidence: false` for both)
- None of these six values differ from what the same row showed before this iteration — the `band`
  column is a pure append, it disturbs nothing to its left

---

### UT-07 — Row drill-in and Screen History click-through still work with the new column present (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/desk` — row drill-in `Link`, Screen History table

**Preconditions:**
- Same live ambient store; Screen History panel lists at least 2 entries (currently 6, per "Data
  used by this plan")

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click anywhere in the `BRK-B` ranked row (not on any specific cell — the whole row is one
   stretched link)
3. Confirm the browser navigates to a URL matching
   `http://localhost:3301/structure?symbol=BRK-B&asof=<as_of-value>`
4. Navigate back to `http://localhost:3301/desk`
5. In the "Screen History" panel, click any row other than the currently-highlighted one (e.g. the
   row dated `2026-06-22`)

**Expected Result:**
- Step 3: navigation succeeds to `/structure` with the `BRK-B` symbol pre-filled — the row's
  stretched-link click-through is unaffected by the new trailing `band` `<td>`
- Step 5: the page swaps to that history entry's own snapshot in place (no navigation), that row
  highlights, and its ranked table (now 10 columns) renders correctly including a `band` column for
  every row of that OLDER snapshot too (also showing the legacy fallback, since it long predates
  this iteration)

---

### UT-08 — Skipped-members table intentionally has no `band` column (ux sanity, not a defect)

**Type:** ux
**Priority:** P2
**Surface:** `/desk` — `DeskSkipTable`

**Preconditions:**
- The live ambient store's latest snapshot has 38 skipped members (non-zero skip count)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll to the "Skipped — no bars" and/or "Skipped — no basis session" section(s)
3. Read the skip table's header row

**Expected Result:**
- The skip table's header reads exactly 4 columns: `symbol, reason, coverage, tick evidence` — no
  `band` column
- This is correct and expected: a skipped member has no `distance_bps`/`band_score`/
  `reference_close` (it was never ranked), so `band` never applies to a skip row — confirm this is
  NOT rendered as a missing/broken column, simply absent

---

### UT-09 — New `band`/`close` copy contains no advice, imperative, or prediction language (ux — manual copy-discipline spot check)

**Type:** ux
**Priority:** P3
**Surface:** `/desk` — `band` cell text and tooltip segment

**Preconditions:**
- UT-03 and UT-05 have been read (both the fallback and populated copy strings)

**Steps:**
1. Re-read the fallback string: `close not recorded in this snapshot`
2. Re-read the populated pattern: `band <low>–<high> · close <val>`
3. Check both for any of: "buy", "sell", "watch", "opportunity", "should", "recommend", "target",
   or any wording implying an action or prediction

**Expected Result:**
- Neither string contains any of the listed words or similar advice/imperative/prediction language
- Both strings are purely descriptive (a measurement and an honest absence), consistent with every
  other column on this page (`distance`, `score`, `basis`, `history`)
- This manual check should agree with the automated `tests/test_copy_discipline.py` result (TC-11)

---

### UT-10 — Documented gap: the populated `band` example is not observable on the live ambient store today (ux, documented gap)

**Type:** ux
**Priority:** P3
**Surface:** `/desk` (whole ranked table)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll through EVERY ranked row across the currently-viewable snapshot (and, optionally, every
   Screen History entry)
3. Look for any row whose `band` cell shows numeric values instead of the fallback text

**Expected Result:**
- No such row exists anywhere on the live ambient store as of 2026-07-29 — every ranked row in every
  recorded snapshot predates this iteration's backend code
- This is a documented, honest, and EXPECTED current state (see the dev handoff's Known Issues note
  and the QA report's TC-06 result) — NOT a regression or a half-shipped feature; the populated
  rendering path is independently proven by backend tests
  (`test_reference_close_golden_in_band_and_out_of_band_rows`) and will be captured live by the
  scoped-rig lane covering UT-05 above
- Do not fail this test case over the absence of a populated row on THIS store — only fail it if a
  row's `band` cell is blank, shows `undefined`/`NaN`, or shows anything other than the exact
  fallback text

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads, `band` header present | smoke | P1 | `/desk` |
| UT-02 | Header shows exactly 10 columns in order | smoke | P1 | `/desk` ranked table header |
| UT-03 | Legacy rows show honest fallback text | happy-path | P1 | `/desk` `desk-row-band` |
| UT-04 | Tooltip carries band/close segment after history | happy-path | P1 | `/desk` composite tooltip |
| UT-05 | Populated in-band + out-of-band rows in one screenshot | happy-path | P1 | `/desk` (scoped rig) |
| UT-06 | Pre-existing columns unchanged for known rows | regression | P1 | `/desk` `DeskRow` |
| UT-07 | Row drill-in + Screen History click-through still work | regression | P2 | `/desk` |
| UT-08 | Skip table intentionally has no `band` column | ux | P2 | `/desk` `DeskSkipTable` |
| UT-09 | New copy carries no advice/prediction language | ux | P3 | `/desk` band copy |
| UT-10 | Documented gap: no populated example on live store today | ux | P3 | `/desk` (whole page) |

**P1 tests must all pass for browser QA verdict to be PASS.**

**Note on coverage:** No "validation" (form-input) test case is included — J-13 adds no new form,
input, or control; the surface is a pure read-only column/tooltip disclosure. No "error" (backend
error surfaced to user) test case is included — J-13 adds no new endpoint, route, or error path; it
rides the already-registered `GET /research/desk/screen` response, whose existing error handling is
unchanged and already covered by prior iterations' test plans.
