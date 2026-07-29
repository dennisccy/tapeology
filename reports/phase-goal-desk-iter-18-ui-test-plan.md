# Phase goal-desk-iter-18 — UI Test Plan

**Phase:** goal-desk-iter-18 (J-14 — every ranked row discloses the nearest wall on the OTHER side
of price)
**Date:** 2026-07-29
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301

---

## Data used by this plan

This plan is grounded in the REAL running rig as read live on 2026-07-29:
`GET http://localhost:8301/research/desk/screen` — the same store the running `/desk` page at
`http://localhost:3301/desk` serves.

**The live `latest` snapshot right now:** `id=screen-2026-07-28-ac07c9581a4f`, `screen_date=2026-07-28`,
`as_of=2026-07-28T23:59:59Z`, `universe_snapshot_id=universe-2026-07-25-49b33fa31680`,
`bar_store_signature=350c85d18b1ff234`, 63 ranked rows, 38 skipped. **Every one of its 63 ranked rows
was recorded before this iteration's backend code existed**, confirmed by direct inspection of the raw
JSON: zero rows carry an `opposite_band` or `bands_by_class` key at all (absent, not `null`). This means
**every row currently visible on the live `/desk` page shows the honest "opposite wall not recorded in
this snapshot" fallback — there is no populated example on the ambient store today.** This is the same
disclosed gap the dev handoff and QA report both document (QA marked TC-12/TC-16 SKIPPED/PENDING for
exactly this reason) — not a defect. UT-02/UT-04/UT-07 below test this honest current state; UT-03/
UT-05/UT-06 cover the populated cases a scoped-rig capture is required to produce.

**Populated-state reference values (independently verified, not yet visible in the running UI):** the
live `GET /research/tradability?symbol=<sym>&as_of=2026-07-28T23:59:59Z` endpoint — the SAME canonical
source `_select_opposite_band` reads from — was queried directly for four of this snapshot's real
ranked members and the shipped `_select_opposite_band`/`_bands_by_class` selection logic
(`apps/backend/app/research/desk_screen.py:257-289`) was replicated by hand against each response. The
results reproduce the phase spec's own background numbers almost to the decimal (BRK-B's 0.6 bps,
CRM's 6,067.7 bps), confirming this near/far/inversion shape is real, not hypothetical:

| Symbol | Row's own selected band | Opposite band (`_select_opposite_band`) | `bands_by_class` |
|---|---|---|---|
| `BRK-B` (row 1) | `support A`, `488.50–490.85`, `0.00 bps`, score `1787.00` | `resistance A`, `490.88–494.22`, **`0.61 bps`** | `A 10 · B 0 · C 0 · unclassified 0` |
| `CRM` | `support A`, `156.25–156.93`, `0.00 bps`, score `63.00` | `resistance A`, `252.15–253.86`, **`6067.70 bps`** | `A 10 · B 0 · C 0 · unclassified 0` |
| `ISRG` | `resistance A`, `475.17–478.49`, `4311.49 bps`, score `789.20` | `support`, `band_class: null`, `332.02–332.02`, **`0.00 bps`** | `A 5 · B 0 · C 0 · unclassified 2` |
| `CMCSA` | `resistance A`, `30.10–30.30`, `3730.71 bps`, score `455.17` | `support B`, `21.83–21.92`, **`0.00 bps`** | `A 5 · B 1 · C 0 · unclassified 0` |

`ISRG`/`CMCSA` are the two "inversion" rows the phase spec's background names: each ranks on a wall
thousands of bps out while an *unranked-class* band sits ~0.0 bps away on the other side (ISRG's
opposite band's own `class` is `null`, rendered as `unclassified` per the frontend's `?? "unclassified"`
fallback — `apps/frontend/app/desk/page.tsx:423`). All four rows above are real members of the SAME
`screen-2026-07-28-ac07c9581a4f` snapshot, so a screen computed for the identical universe/bar-store
pins would be expected to reproduce numerically close values (`compute_tradability` is deterministic
given the same bars) — but a scoped-rig capture (which must never write to `apps/backend/.data`, per
this iteration's OUT OF SCOPE list) will most likely be seeded from its OWN fixture data, so the exact
rows satisfying "≤25 bps" / ">1,000 bps" may differ. Treat the table above as proof this shape occurs
in real data and as a format reference, not as a byte-exact requirement for the scoped-rig screenshot —
the actual pass bar is TC-12's own generic one (at least one row ≤25 bps, one row >1,000 bps, both
legible in one screenshot).

**If the store has changed by the time these tests run** (a new screen was computed since 2026-07-29,
e.g. via the "Run Screen" button on a date not already recorded under the same five pins): re-locate
the current `latest` snapshot via the same GET, confirm whether any row now carries `opposite_band`/
`bands_by_class`, and substitute that row's own values into UT-02/UT-04/UT-07 (fallback pattern) or
UT-03/UT-05/UT-06 (populated pattern) using the same relative logic.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — `/desk` loads and the ranked table's new `opposite` header cell is present as the 11th column (smoke)

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
3. Locate the ranked-rows table (`data-testid="desk-screen-rows-table"`, inside the "Briefing" panel)
4. Scroll the table horizontally to its rightmost edge (it does not fully fit the viewport width —
   this is pre-existing, unchanged behavior, not new this iteration)
5. Read every `<th>` cell in the header row, left to right

**Expected Result:**
- The heading "Desk" is visible, no blank screen, no "The desk screen could not be loaded." panel
- The header row contains exactly 11 cells, in this exact order:
  `symbol, side, class, distance, score, coverage, tick evidence, basis, history, band, opposite`
- `opposite` is the 11th and final header cell — no header appears after it (one more column than
  the ten that existed before this iteration; `opposite` is the only addition)
- No console errors

---

### UT-02 — Every currently-recorded ranked row shows the honest "opposite wall not recorded in this snapshot" fallback (happy path — current true state)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — `DeskRow` opposite cell, `data-testid="desk-row-opposite"`

**Preconditions:**
- The real ambient store's `latest` snapshot is `screen-2026-07-28-ac07c9581a4f` (63 rows, all
  recorded before this iteration's code — see "Data used by this plan" above)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the ranked table, find the row whose leftmost (`symbol`) cell reads exactly `BRK-B` (it is the
   first/topmost ranked row)
3. Scroll the table to its rightmost edge and read that row's last cell
   (`data-testid="desk-row-opposite"`, the new `opposite` column)
4. Repeat steps 2–3 for the rows whose `symbol` cell reads `CRM`, `ISRG`, and `CMCSA`

**Expected Result:**
- All four rows' `opposite` cells contain exactly the text `opposite wall not recorded in this
  snapshot` — no numbers, no `opposite <side> <class> <low>–<high> · <n> bps` pattern, no `"no band
  on the other side"` text
- Spot-check at least 3 more rows beyond the four named above — every visible ranked row's `opposite`
  cell reads this identical fallback text, because every row in this snapshot predates the field

---

### UT-03 — A newly-computed screen's `opposite` column shows a near example (≤25 bps) and a far example (>1,000 bps), both legible in one screenshot (happy path — TC-12 acceptance)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — `DeskRow` opposite cell on a NEW (non-legacy) snapshot

**Preconditions:**
- A scoped backend rig is running (NEVER pointed at `apps/backend/.data`) with its own
  `TAPEOLOGY_DESK_SCREEN_DIR`/`TAPEOLOGY_DESK_UNIVERSE_DIR`/`TAPEOLOGY_BAR_DIR` (see
  `test_desk_screen.py`'s `ctx` fixture for the authoritative env-var list) pointed at fresh temp
  directories, per the iter-9/11/14/15/16/17 scoped-rig discipline this phase's own NOTES section
  requires
- That scoped rig's universe/bar stores are seeded (fixture or real) so that computing a screen
  produces at least one ranked row whose `opposite_band.distance_bps` is ≤25 bps and at least one
  ranked row whose `opposite_band.distance_bps` is >1,000 bps — the "Data used by this plan" table
  above proves this shape genuinely occurs in this project's real data (`BRK-B` at 0.61 bps, `CRM` at
  6067.70 bps, both members of the SAME real screen)
- The target store was checked for an existing snapshot under the same five pins before computing
  (iter-10 lesson) — no collision, or any unavoidable collision disclosed in the executing lane's own
  report
- The frontend at the scoped rig's own port is built/configured to read from that scoped backend
  (never `apps/backend/.data`) — the capturing lane must assert the captured page's own origin
  matches the rig's own base URL (iter-16 lesson) before treating any screenshot as evidence

**Steps:**
1. On the scoped rig's own frontend URL (NOT `http://localhost:3301`, which serves the live ambient
   store), trigger a NEW screen compute for the seeded pins — either via the `/desk` page's "Run
   Screen" button or the scoped backend's own `POST /research/desk/screen/compute`
2. Wait for the compute to finish (the button's label reads "Computing…" while in flight, and reverts
   to "Run Screen" — or the page re-renders with the new snapshot — on completion; the outcome note
   below the button should read "Recorded a new snapshot — <id>", never "Reused…")
3. Navigate to (or stay on) `/desk` on that scoped rig
4. Scroll the ranked table to its rightmost edge; locate one row whose `opposite` cell shows a
   distance ≤25 bps and one row whose `opposite` cell shows a distance >1,000 bps
5. Take one screenshot showing both rows' `opposite` cells together, both legible

**Expected Result:**
- The near row's `opposite` cell reads the pattern `opposite <side> <class-or-unclassified> <low>–
  <high> · <n> bps` where `<n>` is ≤25.00 (e.g. `opposite resistance A 490.88–494.22 · 0.61 bps`)
- The far row's `opposite` cell reads the same pattern with `<n>` >1,000.00 (e.g. `opposite resistance
  A 252.15–253.86 · 6067.70 bps`)
- Both cells show four legible values (side, class, price range, distance) — never blank, never
  `NaN`, never the fallback text
- Both rows are visible together in the one captured screenshot

---

### UT-04 — Legacy row's composite hover tooltip carries the "bands by class not recorded in this snapshot" fallback line after the band/close segment (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — `deskRowDrillInTitle` composite tooltip

**Preconditions:**
- Same live store as UT-02 (`BRK-B` row present, legacy/fallback state)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Locate the `BRK-B` ranked row (topmost row)
3. Hover the mouse anywhere over that row (the drill-in anchor is stretched across the entire row, so
   any point works) and wait for the browser's native tooltip to appear — or, without a real mouse,
   read the `title` attribute of `document.querySelector('tr[data-symbol="BRK-B"] a')`
4. Read the full tooltip text

**Expected Result:**
- The tooltip text is exactly:
  `distance 0 bps · score 1787 · basis 2026-07-23T04:00:00.000000Z (5 d before as-of) · history 500 sessions from 2024-07-25T04:00:00.000000Z · band 488.5–490.8500061035156 · close not recorded in this snapshot · bands by class not recorded in this snapshot · 1h window last requested: 2026-07-25T00:00:00Z · 4h window last requested: 2026-07-25T00:00:00Z · 1d window last requested: 2026-07-25T00:00:00Z · 1w window last requested: 2026-07-25T00:00:00Z`
- The new `bands by class not recorded in this snapshot` segment appears immediately AFTER the
  band/close segment and BEFORE the coverage (`1h window last requested: ...`) segments — matching
  the source order in `deskRowDrillInTitle` (`apps/frontend/app/desk/page.tsx:278-305`)
- No separate/new `title` attribute exists on the `opposite` `<td>` cell itself
  (`document.querySelector('[data-testid="desk-row-opposite"]')`'s own `title` attribute is `null` or
  absent) — the F2 lesson: only the row's ONE composite anchor tooltip carries this detail

---

### UT-05 — A newly-computed screen's row tooltip carries the full-precision, populated `bands_by_class` line (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — `deskRowDrillInTitle` composite tooltip on a NEW (non-legacy) snapshot

**Preconditions:**
- Same scoped rig as UT-03, same freshly-computed screen

**Steps:**
1. On the scoped rig's own frontend URL, locate any ranked row of the newly computed screen
2. Hover over that row (or read its anchor's `title` attribute) to reveal the composite tooltip
3. Read the tooltip's last segment before the coverage (`... window last requested`) list

**Expected Result:**
- The tooltip's last pre-coverage segment reads `bands by class A <n> · B <n> · C <n> · unclassified
  <n>` with all four counts as literal non-negative integers — e.g. for a row shaped like `BRK-B`
  above, `bands by class A 10 · B 0 · C 0 · unclassified 0`
- All four counts sum to that symbol's total band count from `GET /research/tradability` (never a
  blank count, never a missing key)
- This line still appears immediately after the band/close segment and before the coverage segments,
  same position as the fallback line in UT-04

---

### UT-06 — A newly-computed screen shows a row whose opposite band's class is unclassified, rendered as the literal word "unclassified" (not blank, not "null") (happy path — golden null-class case)

**Type:** happy-path
**Priority:** P2
**Surface:** `/desk` — `DeskRow` opposite cell, `band_class: null` case

**Preconditions:**
- Same scoped rig as UT-03; the seeded fixture (or the "Data used by this plan" table's real `ISRG`/
  `CMCSA` example) produces at least one ranked row whose `opposite_band.band_class` is `null`

**Steps:**
1. On the scoped rig's own frontend URL, locate a ranked row whose `opposite` cell's class token
   reads `unclassified` rather than `A`/`B`/`C` (using the `ISRG` shape above as reference: selected
   band `resistance A` far out, opposite band `support`, `class: null`, `distance ≈0 bps`)
2. Read that row's full `opposite` cell text

**Expected Result:**
- The cell reads the pattern `opposite <side> unclassified <low>–<high> · <n> bps` — e.g. `opposite
  support unclassified 332.02–332.02 · 0.00 bps` — never a blank class token, never the literal text
  `"null"`
- This is a genuinely DIFFERENT state from the recorded-`null` `opposite_band` case (TC-8: no band
  exists on the other side at all, cell reads `"no band on the other side"`) — here a band DOES exist
  on the other side, it simply carries no class grade

---

### UT-07 — Pre-existing columns' exact content is unchanged for `BRK-B`/`CRM` after the `opposite` column addition; Skipped Members table gains no new column (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` — `DeskRow` cells other than `opposite`; `DeskSkipTable`

**Preconditions:**
- Same live ambient store as UT-02/UT-04

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Locate the `BRK-B` row and read its `side`, `class`, `distance`, `score`, `basis`, `history`, and
   `band` cells
3. Locate the `CRM` row and read the same seven cells
4. Scroll to the "Skipped — no bars" and/or "Skipped — no basis session" section(s) and read the skip
   table's header row

**Expected Result:**
- `BRK-B`: `side` = `support`; `class` = `Class A` with caption `nearest same-class band`; `distance`
  = `0.00 bps`; `score` = `1787.00`; `basis` = `basis 2026-07-23 · 5 d before as-of`; `history` =
  `history 500 sessions · from 2024-07-25`; `band` = `band 488.50–490.85 · close not recorded in this
  snapshot`
- `CRM`: `side` = `support`; `class` = `Class A`; `distance` = `0.00 bps`; `score` = `63.00`; `band` =
  `band 156.25–156.93 · close not recorded in this snapshot`; `basis`/`history` same as `BRK-B`
- None of these values differ from what the same rows showed before this iteration — the `opposite`
  column is a pure append, it disturbs nothing to its left
- The skip table's header reads exactly 4 columns: `symbol, reason, coverage, tick evidence` — no
  `opposite` (or `band`) column; this is correct, not a bug — a skipped member was never ranked, so it
  has no `opposite_band`/`bands_by_class` to disclose

---

### UT-08 — Row drill-in and Screen History click-through still work with the new column present (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/desk` — row drill-in `Link`, Screen History table

**Preconditions:**
- Same live ambient store; Screen History panel lists at least 2 entries (currently 6, per "Data used
  by this plan")

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click anywhere in the `BRK-B` ranked row (not on any specific cell — the whole row is one
   stretched link)
3. Confirm the browser navigates to a URL matching
   `http://localhost:3301/structure?symbol=BRK-B&asof=2026-07-28T23:59:59Z`
4. Navigate back to `http://localhost:3301/desk`
5. In the "Screen History" panel, click any row other than the currently-highlighted one (e.g. the
   row dated `2026-06-22`)

**Expected Result:**
- Step 3: navigation succeeds to `/structure` with the `BRK-B` symbol pre-filled — the row's
  stretched-link click-through is unaffected by the new trailing `opposite` `<td>`
- Step 5: the page swaps to that history entry's own snapshot in place (no navigation, a
  `data-testid="desk-history-row"` highlights via `data-selected="true"`), and its ranked table (now
  11 columns) renders correctly including an `opposite` column for every row of that OLDER snapshot
  too (also showing the legacy fallback, since it long predates this iteration)

---

### UT-09 — New `opposite` column is discoverable with zero extra clicks — directly visible in the Briefing table on page load (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/desk` — Briefing panel

**Steps:**
1. Navigate to `http://localhost:3301` (home/Cockpit)
2. Click "Desk" in the top navigation bar (`data-testid="nav-link"`, label "Desk")
3. Without clicking anything else, scroll the Briefing table horizontally to its rightmost edge

**Expected Result:**
- Step 2: navigates to `http://localhost:3301/desk`, heading "Desk" is visible (1 click from home)
- Step 3: the `opposite` column and its header are visible — no button, toggle, or additional
  navigation was required to reveal this new information; the only "cost" is the same horizontal
  scroll every column past `coverage` already required before this iteration (pre-existing table
  width behavior, not a new UX regression this phase introduces)
- The header label "opposite" is a plain, unambiguous lower-case word consistent with the table's
  existing header style (`symbol`, `side`, `class`, `distance`, ...) — no jargon or abbreviation

---

### UT-10 — New `opposite`/`bands_by_class` copy contains no advice, imperative, or prediction language (ux — manual copy-discipline spot check)

**Type:** ux
**Priority:** P3
**Surface:** `/desk` — `opposite` cell text and tooltip `bands_by_class` line

**Preconditions:**
- UT-02/UT-03/UT-04/UT-05/UT-06 have been read (fallback, populated, and null-class copy strings)

**Steps:**
1. Re-read the fallback strings: `opposite wall not recorded in this snapshot`, `no band on the other
   side`, `bands by class not recorded in this snapshot`
2. Re-read the populated patterns: `opposite <side> <class> <low>–<high> · <n> bps`, `bands by class A
   <n> · B <n> · C <n> · unclassified <n>`
3. Check both for any of: "buy", "sell", "watch", "opportunity", "should", "recommend", "target", or
   any wording implying an action or prediction

**Expected Result:**
- None of the listed strings contain any of the checked words or similar advice/imperative/prediction
  language
- All strings are purely descriptive (a measurement, a count, or an honest absence), consistent with
  every other column on this page (`distance`, `score`, `basis`, `history`, `band`)
- This manual check should agree with the automated `tests/test_copy_discipline.py` result (TC-15),
  which the dev handoff and QA report both confirm passes unmodified (30 passed)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads, `opposite` header present as 11th column | smoke | P1 | `/desk` |
| UT-02 | Legacy rows show honest fallback text | happy-path | P1 | `/desk` `desk-row-opposite` |
| UT-03 | Populated near (≤25bps) + far (>1000bps) rows in one screenshot | happy-path | P1 | `/desk` (scoped rig) |
| UT-04 | Legacy tooltip carries `bands by class not recorded` line | happy-path | P1 | `/desk` composite tooltip |
| UT-05 | Populated tooltip carries full-precision `bands_by_class` line | happy-path | P1 | `/desk` composite tooltip (scoped rig) |
| UT-06 | Populated row with unclassified opposite band renders "unclassified" | happy-path | P2 | `/desk` `desk-row-opposite` (scoped rig) |
| UT-07 | Pre-existing columns unchanged; skip table unaffected | regression | P1 | `/desk` `DeskRow`/`DeskSkipTable` |
| UT-08 | Row drill-in + Screen History click-through still work | regression | P2 | `/desk` |
| UT-09 | New column discoverable with zero extra clicks | ux | P2 | `/desk` Briefing panel |
| UT-10 | New copy carries no advice/prediction language | ux | P3 | `/desk` opposite/bands-by-class copy |

**P1 tests must all pass for browser QA verdict to be PASS.**

**Note on coverage:** No "validation" (form-input) test case is included — J-14 adds no new form,
input, or control (plan.md: "New user actions: none -- read-only render, no new button or control").
No "error" (backend error surfaced to user) test case is included — J-14 adds no new endpoint, route,
or error path; it rides the already-registered `GET /research/desk/screen` response, whose existing
error handling is unchanged and already covered by prior iterations' test plans. The recorded-`null`
`opposite_band` state (TC-8: "no band on the other side") is not required by the DoD's demo-narrator
walkthrough (TC-16's own acceptance list omits it) and no real member of the sampled live snapshot
exhibits it, so it is not given its own dedicated browser test case here — it is proven at the backend
layer (`test_opposite_band_is_null_when_no_band_on_other_side`) and, per the "Data used by this plan"
note above, should be spot-checked opportunistically by the browser-qa-agent/demo-narrator lanes only
if their own scoped-rig data happens to produce it.
