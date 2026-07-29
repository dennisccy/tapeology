# Phase goal-desk-iter-19 — UI Test Plan

**Phase:** goal-desk-iter-19 (J-14 correction — the `/desk` ranked table's `opposite` column now
names the wall genuinely NEAREST to price on the other side, distance-first, not the best-graded one)
**Date:** 2026-07-29
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301

---

## Scope note — read before executing

This iteration ships **zero `page.tsx`/component changes**. The `opposite` column, its header, its
composite hover tooltip, and every other cell on `/desk` are byte-identical in markup to what
iter-18 shipped (`reports/phase-goal-desk-iter-18-ui-test-plan.md`). The ONLY thing this iteration
changes is which band the backend's `_select_opposite_band` picks for the `opposite` cell on a
**freshly computed** screen — distance-first (nearest wall) instead of class-first (best-graded
wall). Per `docs/handoffs/goal-desk-iter-19-dev.md`, the dev agent verified the corrected rule
against real HONA/META data with a **read-only** recompute script and made **zero writes** to any
store (`ScreenStore.record` was never called) — so **no screen snapshot anywhere yet contains the
corrected values**. Producing browser-visible evidence of the fix requires a screen freshly computed
(via the "Run Screen" button or `POST /research/desk/screen/compute`) on a fixture-scoped rig,
per this iteration's own scoped-rig requirement (never `apps/backend/.data`) and the `rm -rf
apps/frontend/.next` + rebuild step (T-9).

**Reference values** (from `docs/handoffs/goal-desk-iter-19-dev.md`'s own real-data verification,
`as_of=2026-07-29T23:59:59Z`, reproducing the iter-18 evaluator's own cited figures byte-for-byte):

| Symbol | Row's own selected band (unchanged) | OLD rule (pre-fix) `opposite` | NEW rule (this fix) `opposite` |
|---|---|---|---|
| `HONA` | support / Class A / 0.00 bps | Class A, **336.96 bps** | Class B, **153.67 bps** |
| `META` | resistance / Class A / 78.37 bps | Class A, **232.58 bps** | Class C, **92.05 bps** |

Both symbols are confirmed real members of this session's registered universe (the same 63-row real
screen the iter-18 evaluator measured, per `docs/phases/goal-desk-iter-19.md`'s BACKGROUND). These
are the numbers to look for on a freshly computed screen. If the browser-qa-agent's fixture-scoped
rig does not carry `HONA`/`META` specifically, substitute any row on that rig whose own selected band
has two or more candidate opposite-side walls of different class — the pass bar is "nearest wins",
not these exact symbols.

**Neither HONA (153.67 bps) nor META (92.05 bps) satisfies TC-13's own separate "≤25 bps / >1,000
bps" evidence requirement** — that is a different, generic legibility requirement (any two rows, any
symbols) covered by UT-04 below, not the specific HONA/META divergence covered by UT-02/UT-03.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — `/desk` loads and the `opposite` column is present and unmoved (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at `http://localhost:3301`
- Backend is reachable
- No login required

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load
3. Confirm the heading text (`data-testid="desk-title"`) reads exactly `Desk`
4. Locate the ranked-rows table (`data-testid="desk-screen-rows-table"`, inside the "Briefing" panel)
5. Scroll the table horizontally to its rightmost edge
6. Read every `<th>` cell in the header row, left to right

**Expected Result:**
- No blank screen and no amber "The desk screen could not be loaded." panel
  (`data-testid="desk-screen-unavailable"`) — either the populated view or the honest "Desk screen
  not computed yet." panel (`data-testid="desk-screen-not-computed"`) renders
- If populated: the header row contains exactly 11 cells, in this exact order:
  `symbol, side, class, distance, score, coverage, tick evidence, basis, history, band, opposite`
  — identical to iter-18's shipped shape; this iteration adds/removes/reorders no column
- `opposite` is the last (11th) header cell
- No console errors

---

### UT-02 — A freshly computed screen's HONA row shows the corrected, nearer Class B wall (153.67 bps), not the farther Class A wall (336.96 bps) (happy path — core fix, TC-1/TC-6)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — `DeskRow` opposite cell, `data-testid="desk-row-opposite"`, HONA row

**Preconditions:**
- A fixture-scoped backend rig is running (never pointed at `apps/backend/.data`), seeded so a
  computed screen includes a `HONA` row shaped like the reference table above (own band: support /
  Class A / ~0.00 bps; two candidate opposite-side resistance walls: Class A at ~336.96 bps and
  Class B at ~153.67 bps) — or an equivalent row reproducing the same class-vs-distance conflict
- The frontend has been rebuilt (`rm -rf apps/frontend/.next` + restart) pointed at that scoped
  backend, per this iteration's own T-9 requirement — never the ambient store
- A screen has been freshly computed on that rig for pins not already recorded (the outcome note
  below the "Run Screen" button reads "Recorded a new snapshot — ...", never "Reused…")

**Steps:**
1. On the scoped rig's own frontend (rebuilt per the precondition above), navigate to `/desk`
2. If no screen exists yet for the seeded pins, click the "Run Screen" button
   (`data-testid="desk-run-screen-button"`) and wait for its label to revert from "Computing…" back
   to "Run Screen"
3. Scroll the ranked table (`data-testid="desk-screen-rows-table"`) to its rightmost edge
4. Locate the row whose symbol cell (`data-testid="desk-row-symbol"`) reads exactly `HONA`
5. Read that row's `class` cell (`data-testid="desk-row-band-class"`) and `opposite` cell
   (`data-testid="desk-row-opposite"`)

**Expected Result:**
- The `class` cell still reads `Class A` with caption `nearest same-class band` — the row's OWN
  selected band is unchanged by this fix (`_select_best_band` is byte-unchanged)
- The `opposite` cell reads the pattern `opposite resistance B <price_low>–<price_high> · <n> bps`
  where `<n>` is approximately `153.67` (Class B)
- The `opposite` cell does NOT read `opposite resistance A <price_low>–<price_high> · 336.96 bps`
  (the old, pre-fix Class A selection) — this is the exact regression the fix closes

---

### UT-03 — A freshly computed screen's META row shows the corrected, nearer Class C wall (92.05 bps), not the farther Class A wall (232.58 bps) (happy path — core fix, second reproduction, TC-6)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — `DeskRow` opposite cell, `data-testid="desk-row-opposite"`, META row

**Preconditions:**
- Same scoped rig as UT-02, seeded so the same freshly computed screen also includes a `META` row
  shaped like the reference table above (own band: resistance / Class A / ~78.37 bps; opposite-side
  support candidates: Class A at ~232.58 bps and Class C at ~92.05 bps)

**Steps:**
1. On the same scoped rig/screen as UT-02, scroll the ranked table to its rightmost edge
2. Locate the row whose symbol cell reads exactly `META`
3. Read that row's `class` cell and `opposite` cell

**Expected Result:**
- The `class` cell still reads `Class A` with caption `nearest same-class band` (own selected band
  unaffected)
- The `opposite` cell reads the pattern `opposite support C <price_low>–<price_high> · <n> bps` where
  `<n>` is approximately `92.05` (Class C)
- The `opposite` cell does NOT read `opposite support A <price_low>–<price_high> · 232.58 bps` (the
  old, pre-fix Class A selection)

---

### UT-04 — Near (≤25 bps) and far (>1,000 bps) `opposite` rows legible together in one screenshot, plus a tooltip screenshot showing `bands_by_class` (happy path — TC-13 browser-evidence requirement)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — `DeskRow` opposite cell + composite drill-in tooltip on a freshly computed screen

**Preconditions:**
- Same scoped rig as UT-02/UT-03 (or any fixture-scoped rig with a freshly computed screen), with at
  least one ranked row whose `opposite_band.distance_bps` is ≤25 and at least one whose
  `opposite_band.distance_bps` is >1,000 — this shape is proven to occur in this project's real data
  (iter-18's own live check found `BRK-B` at ~0.6 bps and `CRM` at ~6,067.7 bps on the same real
  screen; treat those as a format reference, not a byte-exact requirement — any two qualifying rows
  from the scoped rig's own seeded data satisfy this test)

**Steps:**
1. On the scoped rig's frontend, scroll the ranked table to its rightmost edge
2. Locate one row whose `opposite` cell (`data-testid="desk-row-opposite"`) shows a distance ≤25 bps
   and one row whose `opposite` cell shows a distance >1,000 bps
3. Take one screenshot showing both rows' `opposite` cells together, both legible in frame
4. Hover the mouse anywhere over either row (the drill-in anchor is stretched across the whole row —
   any point works) to reveal the composite tooltip
5. Take a second screenshot of that tooltip

**Expected Result:**
- Screenshot 1: the near row's `opposite` cell reads `opposite <side> <class-or-unclassified>
  <low>–<high> · <n> bps` with `<n>` ≤25.00; the far row's `opposite` cell reads the same pattern
  with `<n>` >1,000.00; both cells show four legible values (side, class, price range, distance) —
  never blank, never `NaN`, never the fallback text
- Screenshot 2: the tooltip text includes a segment reading `bands by class A <n> · B <n> · C <n> ·
  unclassified <n>` with all four counts as literal non-negative integers — this line is unaffected
  by this iteration's fix (it lists per-class band counts, not the selected opposite band)

---

### UT-05 — Clicking "Run Screen" for already-recorded pins reuses the existing snapshot without rewriting its `opposite` values (regression — append-only, TC-8)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` — `ScreenComputeControl`, `data-testid="desk-run-screen-button"`

**Preconditions:**
- A screen is already recorded for today's date under the current five pins (universe snapshot id,
  screen date, as_of, config fingerprint, bar-store signature) — check the "Screen History" panel
  (`data-testid="desk-history-table"`) for an entry dated today before starting

**Steps:**
1. Navigate to `http://localhost:3301/desk` (or the rig under test)
2. Scroll the ranked table to its rightmost edge and note the exact `opposite` cell text for the
   first two visible rows
3. Click the "Run Screen" button (`data-testid="desk-run-screen-button"`)
4. Wait for the button label to revert from "Computing…" back to "Run Screen"
5. Read the outcome note below the button (`data-testid="desk-screen-compute-outcome"`)
6. Re-read the same two rows' `opposite` cell text

**Expected Result:**
- Step 5: the outcome note reads `Reused the snapshot already recorded for this key — <id>` (never
  `Recorded a new snapshot — <id>`)
- Step 6: both rows' `opposite` cell text is byte-identical to what was recorded in step 2 — no
  in-place rewrite occurred, proving the append-only guarantee holds even after this iteration's
  selection-rule change

---

### UT-06 — Opening an older Screen History entry still shows that snapshot's own originally-recorded `opposite` values, untouched by this fix (regression — legacy display fidelity)

**Type:** regression
**Priority:** P2
**Surface:** `/desk` — `desk-history-table` / `desk-history-row`

**Preconditions:**
- The "Screen History" panel lists at least one entry recorded before today (an older `screen_date`
  or an older `created_utc`)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the "Screen History" panel, click a row other than the currently-highlighted (latest) one —
   prefer the oldest available entry
3. Confirm the "viewing" indicator (`data-testid="desk-viewing-indicator"`) appears, naming that
   entry's own `screen_date`
4. Scroll the now-displayed ranked table to its rightmost edge and read a few rows' `opposite` cells
5. Reload the page (F5) and repeat steps 2–4 on the same history entry

**Expected Result:**
- The displayed `opposite` values are whatever that OLDER snapshot originally recorded — either the
  legacy-absent text `opposite wall not recorded in this snapshot` (if it predates iter-18) or a
  class-first (pre-iter-19-fix) selection (if it was computed between iter-18 and this fix) — either
  is CORRECT for an already-recorded snapshot and must NOT be reported as a bug
- The values read identically before and after the page reload in step 5 — proving the fix did not
  retroactively alter any stored snapshot
- Clicking the "Latest" button (`data-testid="desk-history-latest-button"`) returns the page to the
  `latest` snapshot's own values

---

### UT-07 — Pre-existing columns (side, class, distance, score, basis, history, band) are unaffected by the `opposite`-selection fix (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/desk` — `DeskRow` cells other than `opposite`

**Preconditions:**
- A populated `/desk` screen is displayed (ambient or scoped rig)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Pick any two ranked rows and read their `side`, `class`, `distance`, `score`, `basis`, `history`,
   and `band` cells (`data-testid` values `desk-row-side`, `desk-row-band-class`,
   `desk-row-distance`, `desk-row-score`, `desk-row-basis`, `desk-row-history`, `desk-row-band`)
3. Compare against the same rows' values as recorded prior to this iteration (from the QA/dev
   evidence of iter-17/iter-18, or by re-reading a Screen History entry recorded before this fix)

**Expected Result:**
- None of these seven cells differ from their pre-iter-19 values on any row — `_select_best_band` and
  `_row_rank_key` are byte-unchanged, so the row's own side/class/distance/score and the cross-symbol
  rank order are identical; only the trailing `opposite` cell can differ, and only on rows where the
  two selection rules genuinely disagree

---

### UT-08 — Row drill-in link and Screen History click-through still work with the corrected selection in place (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/desk` — row drill-in `Link` (`data-testid="desk-row-drill-in"`)

**Preconditions:**
- A populated `/desk` screen is displayed with at least one ranked row and at least 2 Screen History
  entries

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click anywhere in a ranked row (the whole row is one stretched link — any cell works, including
   the `opposite` cell)
3. Confirm the browser navigates to a URL matching
   `http://localhost:3301/structure?symbol=<that row's symbol>&asof=<the displayed snapshot's as_of>`
4. Navigate back to `http://localhost:3301/desk`
5. In the "Screen History" panel, click a different row than the one currently highlighted

**Expected Result:**
- Step 3: navigation to `/structure` succeeds with the correct symbol pre-filled — the trailing
  `opposite` `<td>` does not interfere with the stretched-link click target
- Step 5: the page swaps in place to that history entry's own snapshot (no navigation), the clicked
  row highlights via `data-selected="true"`, and its ranked table (still 11 columns) renders
  correctly, `opposite` column included

---

### UT-09 — The corrected `opposite` content remains discoverable with zero extra clicks (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/desk` — Briefing panel

**Steps:**
1. Navigate to `http://localhost:3301` (home/Cockpit)
2. Click "Desk" in the top navigation bar (`data-testid="nav-link"`, label "Desk")
3. Without clicking anything else, scroll the Briefing table horizontally to its rightmost edge

**Expected Result:**
- Step 2: navigates to `http://localhost:3301/desk`, heading "Desk" is visible (1 click from home)
- Step 3: the `opposite` column and its (possibly corrected) values are visible with no button,
  toggle, or additional navigation required — unchanged discoverability from iter-18, since this
  iteration ships no UI change of its own
- The header label remains the plain lower-case word `opposite`, consistent with the table's other
  headers

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads, `opposite` column unmoved | smoke | P1 | `/desk` |
| UT-02 | HONA row: corrected Class B / 153.67 bps, not Class A / 336.96 bps | happy-path | P1 | `/desk` (scoped rig) |
| UT-03 | META row: corrected Class C / 92.05 bps, not Class A / 232.58 bps | happy-path | P1 | `/desk` (scoped rig) |
| UT-04 | Near (≤25bps) + far (>1000bps) rows legible + tooltip `bands_by_class` | happy-path | P1 | `/desk` (scoped rig) |
| UT-05 | "Run Screen" on already-recorded pins reuses, never rewrites | regression | P1 | `/desk` `desk-run-screen-button` |
| UT-06 | Older Screen History entries keep their original `opposite` value | regression | P2 | `/desk` `desk-history-table` |
| UT-07 | Other columns (side/class/distance/score/basis/history/band) unaffected | regression | P2 | `/desk` `DeskRow` |
| UT-08 | Row drill-in + Screen History click-through still work | regression | P2 | `/desk` |
| UT-09 | `opposite` content still discoverable, zero extra clicks | ux | P3 | `/desk` Briefing panel |

**P1 tests must all pass for browser QA verdict to be PASS.**

**Note on coverage:** No "validation" (form-input) test case is included — this iteration adds no
new form, input, or control (plan.md: "New user actions: none"). No "error" (backend error surfaced
to user) test case is included — this iteration adds no new endpoint or route; it corrects the
selection logic behind the already-registered `GET /research/desk/screen` response, whose existing
error handling (`desk-screen-unavailable` panel) is unchanged and already covered by prior
iterations' test plans. The recorded-`null` `opposite_band` state ("no band on the other side") and
the legacy-absent state ("opposite wall not recorded in this snapshot") are unaffected by this fix
(both proven by `test_a_legacy_row_recorded_without_opposite_band_fields_serves_them_absent_never_
backfilled` and `_select_opposite_band`'s own `None`-returning unit test) and were already covered by
UT-02/UT-08 in `reports/phase-goal-desk-iter-18-ui-test-plan.md`, so they are not re-tested here in
full — only re-verified indirectly via UT-06's "either is correct" framing.
