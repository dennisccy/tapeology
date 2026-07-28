# Phase goal-desk-iter-13 — UI Test Plan

**Phase:** goal-desk-iter-13
**Date:** 2026-07-28
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301 — this iteration's own scoped rig, NOT the ambient app (`:3000`/`:8000`)

---

## Why this plan looks the way it does

This iteration made **zero product/application code changes** (verified: `git diff --stat -- apps/backend/app apps/frontend` = no output; every one of the 16 named out-of-scope files carries zero diff). The UI surface map's "Affected UI Surfaces" table is therefore empty — nothing *changed*. But the iteration's entire job was to prove, with fresh browser evidence in the correct order, that the already-shipped `/desk` "Top-up Runs" panel (J-09, shipped iteration 11) genuinely transitions from its honest-empty state to a populated state on ONE continuously-running rig. That makes this a **re-verification plan**, not a new-feature plan: every test case below either confirms J-09's already-implemented behavior still holds, or confirms the regression set (J-01–J-05, J-07, J-08) still passes on the same scoped rig. There is no happy-path test for a *new* capability because none shipped.

Test cases derive from `reports/phase-goal-desk-iter-13-ui-surface-map.md`'s "Re-Verified This Iteration" table (the operative surface list this iteration, since "Affected UI Surfaces" is empty by design).

---

## Critical constraints — read before executing ANY test case below

- **This is the exact rig the developer used to capture this iteration's evidence**, deliberately left running for downstream lanes. Absolute scoped data root (cite this in any evidence report, per this session's own established convention):
  ```
  /home/dennis-chan/.cache/iad/iad.goal-desk-iter-13.154299/desk-iter13-scoped-qa
  ```
  Backend on `:8301` (uvicorn, PID `1419904` as of the dev handoff), frontend on `:3301` (`next dev`, PID `1421592`/`1421611` as of the dev handoff). If either is unresponsive, use the exact restart recipe in `docs/handoffs/goal-desk-iter-13-dev.md` ("Live scoped processes left running for downstream lanes") — it restarts the two processes against the SAME on-disk root; nothing is reseeded or lost.
- **DO NOT click "Top-up" / "Retry Top-up" (`data-testid="desk-topup-button"`) or "Run Screen" / "Retry Run Screen" (`data-testid="desk-run-screen-button"`) anywhere on this rig, ever, in any test case.** A real click starts an uncontrolled new run against the real keyless Yahoo adapter, which would supersede checkpoint 3 (`topup-2026-07-28-c4de94d71e04`) as "latest" and permanently bury the failed-pair evidence this iteration exists to produce. Every step below is read-only: navigate, read, screenshot, or a non-mutating history-row/drill-in click.
- **The honest-empty Top-up Runs state cannot be reproduced live on this rig anymore.** It was captured exactly once (see UT-05), before the first checkpoint run was recorded; the store is append-only, so that window closed permanently the moment checkpoint 1 landed. Do not attempt to "reset" or re-empty this rig — re-verifying the empty state requires seeding an entirely new rig, which is explicitly out of this iteration's scope.
- Functional/API-only assertions (raw `GET /research/desk/topup/runs` JSON shape, ambient-store checksum diff, the full pytest suite, the MCP 17-tool contract, `git diff --stat`, port hygiene) are already covered in `reports/qa/goal-desk-iter-13-test-plan.md` (TC-01, TC-02, TC-06, TC-08, TC-09, TC-10, TC-11) and are **not duplicated here** — this plan covers only what is observable through the browser.

---

## Test Cases

### UT-01 — `/desk` loads without errors on the iteration-13 scoped rig (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- The scoped rig above is live.
- This test case only navigates and reads — no mutating action.

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error message
- The heading "Desk" (`data-testid="desk-title"`) is visible
- The top nav bar (`data-testid="app-nav"`) shows both "Cockpit" and "Desk" labels, with "Desk" marked as the active link (`aria-current="page"`)
- No console errors
- Scrolling to the very bottom of the page reveals a section headed "Top-up Runs"

---

### UT-02 — Top-up Runs table lists all 3 recorded checkpoint runs with correct columns (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — `data-testid="desk-topup-runs-table"`

**Preconditions:**
- Page loaded per UT-01.

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll down to the "Top-up Runs" section (the last section on the page)
3. Locate the run history table (`data-testid="desk-topup-runs-table"`)

**Expected Result:**
- The empty-state message "No top-up runs recorded yet." does NOT appear
- The table has a header row reading "date / run / state / attempted / total / universe snapshot"
- Exactly 3 rows appear (`data-testid="desk-topup-run-row"`), in this recorded order: `done` "404 / 404", `cancelled` "3 / 404", `done` "404 / 404"
- Every row's "universe snapshot" column reads `universe-2026-07-25-49b33fa31680`
- Evidence for this exact state already exists at `reports/qa/goal-desk-iter-13-evidence/UT-J-09-populated-fullpage.png` (captured by the dev lane on this same rig); a fresh confirming screenshot is safe to take since this state is stable and read-only

---

### UT-03 — Latest-run detail block shows correct attempted/total and per-outcome counts (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — `data-testid="desk-topup-run-latest-detail"`

**Preconditions:**
- Page loaded per UT-01; the run table from UT-02 is visible.

**Steps:**
1. Navigate to `http://localhost:3301/desk`, scroll to Top-up Runs
2. Locate the "Latest run" detail block directly beneath the run table

**Expected Result:**
- Heading reads "Latest run — 2026-07-28 · topup-2026-07-28-c4de94d71e04"
- `data-testid="desk-topup-run-latest-state"` reads exactly "state: done"
- `data-testid="desk-topup-run-latest-attempted"` reads exactly "404 of 404 pairs attempted"
- `data-testid="desk-topup-run-latest-counts"` reads exactly "0 reused · 403 fetched · 1 failed"
- The amber `data-testid="desk-topup-run-latest-unreached"` note does **NOT** appear (unreached = 404 − 404 = 0; the component only renders that note when the count is greater than zero — its honest absence here is itself part of the check)

---

### UT-04 — A failed pair's real error detail is shown verbatim and fully legible (error)

**Type:** error
**Priority:** P1

**Surface:** `/desk` — `data-testid="desk-topup-run-latest-failed"`

**Preconditions:**
- Page loaded per UT-01; latest-run block from UT-03 is visible.

**Steps:**
1. Navigate to `http://localhost:3301/desk`, scroll to Top-up Runs
2. Locate the "Failed pairs" block beneath the latest-run counts line

**Expected Result:**
- Heading reads exactly "Failed pairs (1)"
- Exactly one row (`data-testid="desk-topup-run-latest-failed-row"`) reads "AAPL 1h — no data for that window"
- The detail text is the adapter's real, verbatim error string — NOT a generic "An error occurred", NOT blank, NOT "(no detail recorded)"
- Text is fully legible on screen — not truncated, clipped, or requiring a hover/tooltip to read

---

### UT-05 — Honest-empty Top-up Runs state, verified via this iteration's own archived evidence (happy-path / evidence-review)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — Top-up Runs panel, empty variant (`data-testid="desk-topup-runs-empty"`) — **not reproducible live on this rig** (see Critical Constraints)

**Preconditions:**
- None server-related — this test case reviews two already-captured image files, not a live page.
- Do NOT attempt to satisfy this test case by restarting, clearing, or re-seeding the iteration-13 rig.

**Steps:**
1. Open `reports/qa/goal-desk-iter-13-evidence/UT-J-09-empty-fullpage.png` in any image viewer
2. Open `reports/qa/goal-desk-iter-13-evidence/UT-J-09-empty-topup-section.png` (cropped, upscaled close-up) in any image viewer
3. Confirm both images show a fully hydrated, live `/desk` page (a real Briefing/Screen History above it), not a loading skeleton or blank tab

**Expected Result:**
- The Top-up Runs section reads exactly "No top-up runs recorded yet." next to the ∅ empty-state glyph, with zero run rows and no "Latest run" detail block anywhere in the image
- Per `docs/handoffs/goal-desk-iter-13-dev.md` §5, this was independently confirmed live at capture time via `GET /research/desk/topup/runs` → `{"runs": [], "latest": null}` on the same rig, with the frontend already booted (not captured before the frontend existed — the specific defect this iteration exists to fix)
- If a tester wants to reproduce this live rather than review the archive, that requires seeding a brand-new scoped rig — out of scope for this test pass and not required

---

### UT-06 — Every pre-existing `/desk` section still renders, unaffected, around the Top-up Runs panel (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` — Provenance / Briefing / Skipped Members / Screen History / Run Screen-Top-up controls

**Preconditions:**
- Page loaded per UT-01.

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll from top to bottom, reading each section heading in order

**Expected Result:** the page shows sections in this exact order, all populated (none showing an "unavailable" or crashed state):
1. "Provenance" (`data-testid="desk-provenance"`) — shows "Universe snapshot", "Screen date", "As of", "Config fingerprint" = `08e471b10130e1e2`, "Bar-store signature"
2. "Briefing" — a ranked rows table (`data-testid="desk-screen-rows-table"`)
3. "Skipped Members" — either a populated list or the honest "No members were skipped in this screen." empty state
4. "Screen History" — a dated table (`data-testid="desk-history-table"`)
5. "Run Screen / Top-up" — the two compute-control buttons (see Critical Constraints — do not click them)
6. "Top-up Runs" — the panel covered by UT-02–UT-05, correctly the LAST section on the page

---

### UT-07 — J-01: Universe ingestion provenance still renders (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Reproduces `journey-scripts/J-01.json` exactly.

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Confirm the text "Desk" is visible somewhere on the page
3. Read the Provenance block (`data-testid="desk-provenance"`)

**Expected Result:**
- Provenance block contains the text "Universe snapshot"
- Provenance block contains the text "08e471b10130e1e2" (the frozen config fingerprint)
- Matches golden replay `UT-J-01` — already re-confirmed PASS this iteration, evidence at `reports/qa/goal-desk-iter-13-evidence/J-01-verify.png`

---

### UT-08 — J-02: Coverage + tick-evidence columns still populated (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Reproduces `journey-scripts/J-02.json` exactly.

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Read the screen rows table (`data-testid="desk-screen-rows-table"`)

**Expected Result:**
- Table contains the text "coverage"
- Table contains the text "tick evidence"
- Both columns show real, non-blank values in at least one row
- Matches golden replay `UT-J-02` — already re-confirmed PASS this iteration, evidence at `reports/qa/goal-desk-iter-13-evidence/J-02-verify.png`

---

### UT-09 — J-03: The screen still ranks a Class A row with a dated history (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Reproduces `journey-scripts/J-03.json` exactly.

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Read the screen rows table (`data-testid="desk-screen-rows-table"`)
3. Read the history table (`data-testid="desk-history-table"`)
4. Read the Provenance block (`data-testid="desk-provenance"`)

**Expected Result:**
- Screen rows table contains at least one "Class A" row
- History table shows a "date" column header and at least one dated row
- Provenance block contains the text "Config fingerprint"
- Matches golden replay `UT-J-03` — already re-confirmed PASS this iteration, evidence at `reports/qa/goal-desk-iter-13-evidence/J-03-verify.png`

---

### UT-10 — J-04: The full `/desk` briefing layout and nav still render (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Reproduces `journey-scripts/J-04.json` exactly.

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Confirm the nav bar (`data-testid="app-nav"`) shows both "Desk" and "Cockpit"
3. Confirm the title (`data-testid="desk-title"`) reads "Desk"
4. Confirm the page body contains the sentence "The latest screen over the registered universe"
5. Confirm `data-testid="desk-screen-rows-table"` has a "symbol" column header
6. Confirm `data-testid="desk-history-table"` has a "date" column header
7. Confirm `data-testid="desk-provenance"` shows "Universe snapshot"

**Expected Result:**
- All 6 checks above hold simultaneously on one page load; no missing section
- Matches golden replay `UT-J-04` — already re-confirmed PASS this iteration, evidence at `reports/qa/goal-desk-iter-13-evidence/J-04-verify.png`

---

### UT-11 — J-05: Ledger history drill-in still reaches `/structure`'s tradable-map (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → `/structure`

**Preconditions:**
- Reproduces `journey-scripts/J-05.json` exactly. This is a client-side navigation click, not a compute/fetch trigger — safe on this rig.

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Confirm the text "Screen History" is visible
3. Click the history row whose date cell reads "2026-06-22" (`data-testid="desk-history-row"`, `data-screen-date="2026-06-22"` — the whole row is clickable)
4. Confirm the text "Viewing the recorded screen for 2026-06-22 — not the latest." appears
5. Confirm a "Latest" button (`data-testid="desk-history-latest-button"`) is now visible next to that text
6. Click a ranked row in the screen table (`data-testid="desk-screen-row"`) to drill in
7. Wait up to 4 seconds for the destination page to render

**Expected Result:**
- The browser navigates (client-side, no full page reload) to `/structure`
- `data-testid="structure-title"` reads "Structure"
- `data-testid="tradable-map-table"` shows the band "298.02–300.1001"
- Matches golden replay `UT-J-05` — already re-confirmed PASS this iteration, evidence at `reports/qa/goal-desk-iter-13-evidence/J-05-verify.png`

---

### UT-12 — J-07: Regression sentinel — Cockpit Watch flow + `/structure` chart still work (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` and `/structure`

**Preconditions:**
- Reproduces `journey-scripts/J-07.json` exactly.
- **Cleanup note:** this test starts a live SIMULATED watch feed (`SIM-BUYER`) — unrelated to the Top-up Runs rig, but should be stopped afterward (`DELETE /watch/SIM-BUYER`) so it does not keep running as a leftover feeder task for the next test (the iteration-12 lesson, applied by the dev lane already this iteration).

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Confirm "Tapeology" is visible
3. Click the "Simulated" button
4. Type "SIM-BUYER" into the "Ticker" field
5. Click the "Watch" button
6. Confirm the text "Buyer Control" appears (this step has a known ~15s script-embedded timeout independent of any CLI flag — allow up to 15 seconds before declaring failure)
7. Navigate to `http://localhost:3301/structure`
8. Type "AAPL" into the "Structure symbol" field
9. Type "2026-06-22T21:00:00Z" into the as-of field (`data-testid="structure-as-of-input"`)
10. Click the "Load" button (`data-testid="structure-load-button"`)
11. Confirm the text "300.11" appears
12. Wait up to 4 seconds

**Expected Result:**
- Step 6's "Buyer Control" text appears (may take up to ~15s — a pre-existing timing property of the simulated tape engine, not a regression; disclosed in `reports/phase-goal-desk-iter-13-smoke-replay-results.md`)
- `data-testid="tradable-map-chart-caption"` shows "300.11"
- A `<canvas>` element renders inside `data-testid="structure-chart-canvas"`
- Matches golden replay `UT-J-07` — already re-confirmed PASS this iteration (after one disclosed transient retry), evidence at `reports/qa/goal-desk-iter-13-evidence/J-07-verify.png`

---

### UT-13 — J-08: Ranked briefing rows still name their basis bar, both variants (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Reproduces `journey-scripts/J-08.json` exactly.

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Confirm the screen rows table (`data-testid="desk-screen-rows-table"`) has a "basis" column header
3. Read a `data-testid="desk-row-basis"` cell on the latest screen — confirm it contains "d before as-of"
4. Click the history row whose date cell reads "2026-07-25" (`data-testid="desk-history-row"`, `data-screen-date="2026-07-25"`)
5. Confirm the text "Viewing the recorded screen for 2026-07-25 — not the latest." appears
6. Read `data-testid="desk-row-basis"` again — confirm it now reads "basis not recorded in this snapshot"
7. Click the "Latest" button (`data-testid="desk-history-latest-button"`)
8. Read `data-testid="desk-row-basis"` again — confirm it reads "d before as-of" once more (restored)
9. Confirm `data-testid="desk-title"` still reads "Desk" (post-match liveness check — proves the page is still alive, not merely that the prior match happened a moment before a crash)

**Expected Result:**
- All 3 basis-text states are observed in sequence exactly as above (present-for-latest → honestly-absent-for-older → present-again-after-Latest-click)
- Matches golden replay `UT-J-08` — already re-confirmed PASS this iteration, evidence at `reports/qa/goal-desk-iter-13-evidence/J-08-verify.png`

---

### UT-14 — Top-up Runs panel is discoverable without scrolling tricks or extra clicks (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/desk`

**Preconditions:**
- Page loaded per UT-01.

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll down using ordinary mouse-wheel/trackpad scrolling only — no keyboard shortcuts, no browser dev tools, no "find in page"

**Expected Result:**
- The "Top-up Runs" heading becomes visible through ordinary scrolling alone, as the last section on the page
- No extra click, toggle, tab switch, or "show more" interaction is required to reveal it
- The section is clearly labeled "Top-up Runs" in plain text (not an icon-only or ambiguous heading)

---

### UT-15 — Top-up Runs copy stays descriptive measurement only, never advice or urgency language (ux / anti-goal)

**Type:** ux
**Priority:** P3
**Surface:** `/desk` — Top-up Runs panel

**Preconditions:**
- Page loaded per UT-01; run table and latest-run detail populated (per UT-02–UT-04).

**Steps:**
1. Navigate to `http://localhost:3301/desk`, scroll to Top-up Runs
2. Read every visible string of text inside the panel (table cells, latest-run line, failed-pairs list)

**Expected Result:**
- All copy is measurement/description only: run id, date, state word, pair counts, verbatim error text
- No advice, imperative, prediction, or ranking language appears anywhere in the panel — specifically absent: "should", "buy", "sell", "watch this", "opportunity", "recommended", or any similar cue implying action
- Matches `docs/goal.md`'s critical anti-goal "The briefing describes, never advises" — unchanged behavior since iteration 11, zero copy diff this iteration

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads without errors | smoke | P1 | `/desk` |
| UT-02 | Top-up Runs table lists all 3 runs correctly | happy-path | P1 | `/desk` |
| UT-03 | Latest-run attempted/total + per-outcome counts | happy-path | P1 | `/desk` |
| UT-04 | Failed pair's verbatim error detail, legible | error | P1 | `/desk` |
| UT-05 | Honest-empty state (evidence review, not live-reproducible) | happy-path | P1 | `/desk` |
| UT-06 | Every pre-existing `/desk` section unaffected | regression | P1 | `/desk` |
| UT-07 | J-01 Universe ingestion provenance | regression | P1 | `/desk` |
| UT-08 | J-02 Coverage + tick-evidence columns | regression | P1 | `/desk` |
| UT-09 | J-03 Class A row + dated history | regression | P1 | `/desk` |
| UT-10 | J-04 Full briefing layout + nav | regression | P1 | `/desk` |
| UT-11 | J-05 Ledger drill-in to `/structure` | regression | P1 | `/desk` → `/structure` |
| UT-12 | J-07 Cockpit Watch flow + `/structure` chart | regression | P1 | `/`, `/structure` |
| UT-13 | J-08 Ranked rows name their basis bar (both variants) | regression | P1 | `/desk` |
| UT-14 | Top-up Runs discoverable, no scrolling tricks | ux | P3 | `/desk` |
| UT-15 | Top-up Runs copy stays descriptive, no advice language | ux | P3 | `/desk` |

**P1 tests must all pass for browser QA verdict to be PASS.**

### Coverage notes

- **No validation-type test case.** The Top-up Runs panel — this iteration's sole re-verified target — is a read-only display with no form or input a user submits; zero forms were added or changed this iteration (zero product diff overall). The validation test type from the skill's methodology does not apply.
- **`journey-scripts/J-09.json` is intentionally excluded** from this plan's regression set. It is deliberately read-only/goto-only and asserts the AMBIENT store's own continued honest-empty state (still true — proven by this iteration's own zero-write checksum diff), not this scoped rig's state. Per the phase spec it is independent of this iteration's scoped-rig work and not part of the required regression set.
- **J-06 (MCP contract) has no browser surface** — re-confirmed separately via `test_mcp_server.py`'s existing 17-tool contract; not part of this UI plan.
- Functional/API-level assertions already covered by `reports/qa/goal-desk-iter-13-test-plan.md` (raw JSON shape checks, ambient checksum diff, full pytest suite, MCP contract, `git diff --stat`, port hygiene) are deliberately not repeated here.
