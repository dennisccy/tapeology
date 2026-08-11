# Phase goal-playbook-iter-4 — UI Test Plan

**Phase:** goal-playbook-iter-4
**Date:** 2026-08-11
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301

---

## Fixture-rig precondition (applies to UT-02, UT-03, UT-04, UT-11)

This iteration's three new detectors (`jbe`, `dbi`, `cup_handle`) have NOT yet fired on any session
in the operator's real recorded universe — per the dev handoff's own "Known Issues," the real
back-scan validation is J-07's job, not this iteration's. TC-1/TC-2/TC-3 of the phase spec
themselves are written against "the fixture rig," not the live production store. Before running
UT-02/UT-03/UT-04/UT-11, the tester (browser-qa-agent) must stand up that fixture rig:

1. Start the backend with `TAPEOLOGY_DESK_PLAYBOOK_DIR`, `TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR`, and
   `TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR` pointed at fresh scratch directories (never the
   operator's real `.data/playbook/` store — this is the same discipline the dev handoff documents
   it used for its own scratch computes, and TC-18 requires it).
2. Seed a `BarStore`/`UniverseStore` the backend actually reads from with a canonical two-firing
   `jbe` session, reusing the exact bar construction already proven correct in
   `apps/backend/tests/test_desk_playbook.py`'s `_plant_ladder_baseline_sessions` /
   `_plant_ladder_jbe_session` helpers (symbol `"LADDER"`, `SESSION_DATE = "2026-06-22"` in that
   file) — `dbi` is the direction-flipped mirror per `test_canonical_dbi_mirrors_the_jbe_fixture`
   in `test_desk_playbook_detect.py`. Seed a separate canonical `cup_handle` session using the bar
   construction in `test_canonical_cup_handle_matches_the_hand_computed_signal`
   (`test_desk_playbook_detect.py`).
3. Confirm the backend is alive by request, not PID: `curl :8301/health` returns
   `{"status":"ok"}` (iter-2 lesson).
4. Do NOT reuse the deleted stray fixture date `2026-08-04` — see UT-09, that date's absence is
   itself part of this iteration's expected behavior.

If the rig cannot be stood up, UT-02/UT-03/UT-04/UT-11 cannot be executed — report them
`NOT-RUN (fixture rig unavailable)`, do not mark them PASS on faith.

---

## Test Cases

### UT-01 — Playbook Signals section loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend running at http://localhost:3301, backend at :8301 (`curl :8301/health` → `{"status":"ok"}`)
- No login required (no auth on this app)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll down to the section with the heading "Playbook Signals" (`aria-label="Playbook Signals"`, panel `<h2>` reads exactly "Playbook Signals")

**Expected Result:**
- The "Playbook Signals" panel renders without a blank screen or error message
- A text input labeled "Session date (yyyy-MM-dd) — blank = the most recent recorded session" is visible (`data-testid="desk-playbook-date-input"`)
- A "Run Playbook" button is visible (`data-testid="desk-playbook-compute-button"`) — label reads "Run Playbook" (not "Computing…" or "Retry Run Playbook") when idle
- No console errors

---

### UT-02 — JBE signal renders with its own chip and continuation geometry (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Playbook Signals section

**Preconditions:**
- Fixture rig stood up per the precondition above, with a canonical `jbe`-firing session recorded (or recordable) for symbol `LADDER`, session date `2026-06-22`

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the "Session date (yyyy-MM-dd)" field (`data-testid="desk-playbook-date-input"`), clear any existing value and type `2026-06-22`
3. Click the "Run Playbook" button (`data-testid="desk-playbook-compute-button"`)
4. Wait for the button label to return to "Run Playbook" (or for `data-testid="desk-playbook-compute-outcome"` to read "Playbook run complete for 2026-06-22.")
5. In the Playbook Signals table (`data-testid="desk-playbook-table"`), locate the row for symbol `LADDER` whose setup cell (`data-testid="desk-playbook-signal-setup"`) shows a chip
6. Click that row (`data-testid="desk-playbook-signal-row"`) to select it

**Expected Result:**
- The setup chip reads exactly "Jump-Base Explosion" (not the raw string `jbe`)
- The side chip (`data-testid="desk-playbook-signal-side"`) reads "long"
- Below the trigger/invalidation line in the expanded detail panel (`data-testid="desk-playbook-signal-detail"`), a paragraph with `data-testid="desk-playbook-signal-continuation-geometry"` is present and reads in the form "base `<N>` MBR wide (`<N>` bars) · jump `<N>` MBR · broke at slot `<N>`"
- No paragraph with `data-testid="desk-playbook-signal-cup-handle-geometry"` is present on this row

---

### UT-03 — DBI signal renders with its own chip, mirrored side (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Playbook Signals section

**Preconditions:**
- Fixture rig stood up with a canonical `dbi`-firing session recorded (the direction-flipped mirror of the `jbe` fixture, per `test_canonical_dbi_mirrors_the_jbe_fixture`)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Enter the `dbi` fixture's session date in the "Session date (yyyy-MM-dd)" field
3. Click "Run Playbook" (`data-testid="desk-playbook-compute-button"`) and wait for completion
4. Locate the row whose setup cell shows a chip for the `dbi` symbol
5. Click that row to select it

**Expected Result:**
- The setup chip reads exactly "Drop-Base Implosion"
- The side chip reads "short"
- The `data-testid="desk-playbook-signal-continuation-geometry"` paragraph is present, showing the mirrored base/jump values for the short side
- No `data-testid="desk-playbook-signal-cup-handle-geometry"` paragraph is present on this row

---

### UT-04 — Cup and Handle signal renders with its own chip and geometry (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Playbook Signals section

**Preconditions:**
- Fixture rig stood up with a canonical `cup_handle`-firing session recorded (per `test_canonical_cup_handle_matches_the_hand_computed_signal`)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Enter the `cup_handle` fixture's session date in the "Session date (yyyy-MM-dd)" field
3. Click "Run Playbook" (`data-testid="desk-playbook-compute-button"`) and wait for completion
4. Locate the row whose setup cell shows a chip for the `cup_handle` symbol
5. Click that row to select it

**Expected Result:**
- The setup chip reads exactly "Cup and Handle"
- The side chip reads "long"
- A paragraph with `data-testid="desk-playbook-signal-cup-handle-geometry"` is present, reading in the form "cup `<N>` bars · depth `<N>` MBR · handle retrace `<N>` · handle duration `<N>` of cup · broke at slot `<N>`" followed by "· RVOL cup mid `<N>` / cup outer `<N>` / handle `<N>`"
- No `data-testid="desk-playbook-signal-continuation-geometry"` paragraph is present on this row

---

### UT-05 — Malformed session date shows inline validation error (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/desk` → Playbook Signals section

**Preconditions:**
- Navigate to `/desk`, no compute needs to be running

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the "Session date (yyyy-MM-dd)" field, type `not-a-date`

**Expected Result:**
- A paragraph with `data-testid="desk-playbook-date-error"` appears reading exactly: "Enter the session date as a real yyyy-MM-dd, or leave it blank for the most recent recorded session."
- The date input's border shows the amber invalid-state styling (`aria-invalid="true"`)
- The "Run Playbook" button is disabled (no compute is triggered)

---

### UT-06 — Non-recorded session date is refused with the backend's own message (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk` → Playbook Signals section

**Preconditions:**
- A well-formed but genuinely non-recorded trading date is available (e.g., a weekend date, or any date outside the fixture rig's recorded range)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the "Session date (yyyy-MM-dd)" field, type a well-formed date that is NOT a recorded trading session (e.g., a Saturday date)
3. Click "Run Playbook" (`data-testid="desk-playbook-compute-button"`)

**Expected Result:**
- No signals table appears
- A paragraph with `data-testid="desk-playbook-compute-trigger-error"` appears containing the text "is not a recorded trading session" (the verbatim backend refusal from `desk_sessions.py`, e.g. "`<date>` is not a recorded trading session -- the daily bars on file for ...")
- The user remains on `/desk` with the Playbook Signals section still visible

---

### UT-07 — Opening-range-break signals render exactly as before this iteration (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Playbook Signals section

**Preconditions:**
- A session with a recorded `open_high_break` or `open_low_break` signal is available (any J-01/J-02/J-03-era recorded session already on file, or the fixture rig's own OR-break fixture)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Enter the OR-break session's date and click "Run Playbook" (or leave blank if it is already the most recently recorded session)
3. Locate the row for the `open_high_break` or `open_low_break` signal and click it to select it

**Expected Result:**
- The setup chip reads "Open-High Break" or "Open-Low Break" exactly as before this iteration
- The detail panel shows the opening-range geometry line reading "opening range `<low>`–`<high>` (`<basis>` basis, `<N>` bars) · width `<N>` MBR · broke at slot `<N>`", optionally followed by "· open vs prior close `<N>`%"
- Neither `data-testid="desk-playbook-signal-continuation-geometry"` nor `data-testid="desk-playbook-signal-cup-handle-geometry"` is present on this row
- The forward-measurement table, invalidation-breach note, and baseline-pool note below it are unchanged from the J-03 shipped behavior

---

### UT-08 — Every other shipped Desk section still renders after a clean rebuild (regression, J-10 sentinel)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` (whole page)

**Preconditions:**
- `apps/frontend/.next` removed and the frontend rebuilt/restarted (T-9 discipline) before this check

**Steps:**
1. Run `rm -rf apps/frontend/.next`, rebuild, and restart the frontend
2. Navigate to `http://localhost:3301/desk`
3. Walk every shipped section from top to bottom: Screen History calendar, Forward Returns, Refresh Chain, ranked Briefing, Skipped members, Runs, Pins, Compare, Provenance, and Playbook Signals — for sections below the fold, use the sibling-`display:none`-collapse technique (collapse the sections already screenshotted so the target section scrolls into view) rather than a blind deep `scrollTo`
4. Compare each section's heading text and visible layout against the stored `J-10.json` golden replay script (`runs/goal-session-playbook/journey-scripts/J-10.json`)

**Expected Result:**
- Every section heading listed above is present with unchanged text
- No `data-testid` or heading string introduced this iteration (`desk-playbook-signal-continuation-geometry`, `desk-playbook-signal-cup-handle-geometry`) collides with any string the golden script or any of the 20 stored `goal-session-desk` scripts assert on
- The golden replay reports zero mismatches

---

### UT-09 — The deleted stray fixture date shows an honest "not computed" state (regression)

**Type:** regression
**Priority:** P3
**Surface:** `/desk` → Playbook Signals section

**Preconditions:**
- Running against the operator's real backend store (NOT the fixture-scoped rig from UT-02–UT-04) — this checks the real `.data/playbook/` store's post-deletion state

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the "Session date (yyyy-MM-dd)" field, type `2026-08-04`

**Expected Result:**
- If no other legitimate record exists for `2026-08-04`, the amber panel with `data-testid="desk-playbook-not-computed"` appears, reading "Playbook not computed for this session." — the stray git-ignored fixture record that previously existed for this date has been deleted as this iteration's hygiene item
- The "Run Playbook" button is present and enabled, ready to compute a fresh record for this date if desired

---

### UT-10 — New setup types are discoverable with zero extra navigation (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/desk` → Playbook Signals section

**Steps:**
1. Navigate to `http://localhost:3301/desk` (home page for this app has no separate dashboard — `/desk` is the entry point named in the phase spec)
2. Scroll to the "Playbook Signals" section (same location as before this iteration — no new nav link, no new section)
3. Run the Playbook for any session containing a `jbe`, `dbi`, or `cup_handle` signal

**Expected Result:**
- The new setup types appear in the exact same table, using the exact same chip styling, at the exact same scroll position as the opening-range-break signals — an operator who already knew how to use J-03's Playbook Signals section needs zero new navigation knowledge to find the new setup types
- No separate "new features" banner, tab, or link exists (would indicate an inconsistent UI pattern versus this project's own house style)

---

### UT-11 — A two-firing JBE ladder discloses independent step geometry (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/desk` → Playbook Signals section

**Preconditions:**
- Fixture rig stood up with the real two-firing `LADDER` session (`_plant_ladder_baseline_sessions` + `_plant_ladder_jbe_session`, session date `2026-06-22`) — the same rig as UT-02

**Steps:**
1. Navigate to `http://localhost:3301/desk`, enter `2026-06-22`, click "Run Playbook", wait for completion
2. In the Playbook Signals table, locate BOTH `LADDER` / "Jump-Base Explosion" rows (there should be exactly two)
3. Click the row with the EARLIER "trigger (ET)" time to select it
4. Read its `data-testid="desk-playbook-signal-continuation-geometry"` line
5. Click the row with the LATER "trigger (ET)" time to select it
6. Read its `data-testid="desk-playbook-signal-continuation-geometry"` line

**Expected Result:**
- Exactly two rows show the "Jump-Base Explosion" chip for symbol `LADDER` in this session
- The FIRST (earlier-triggering) row's geometry line does NOT include a "· ladder step ratio" suffix
- The SECOND (later-triggering) row's geometry line DOES include a "· ladder step ratio `<N>`" suffix, and `<N>` is a numeric value (not blank, not "null", not "NaN")

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Playbook Signals section loads | smoke | P1 | `/desk` |
| UT-02 | JBE signal renders chip + geometry | happy-path | P1 | `/desk` |
| UT-03 | DBI signal renders chip + geometry | happy-path | P1 | `/desk` |
| UT-04 | Cup and Handle signal renders chip + geometry | happy-path | P1 | `/desk` |
| UT-05 | Malformed date shows validation error | validation | P2 | `/desk` |
| UT-06 | Non-recorded date refused with backend message | error | P2 | `/desk` |
| UT-07 | Opening-range-break signals unchanged | regression | P1 | `/desk` |
| UT-08 | Every shipped section renders (J-10 sentinel) | regression | P1 | `/desk` (whole page) |
| UT-09 | Deleted stray fixture date shows honest absence | regression | P3 | `/desk` |
| UT-10 | New setups discoverable, zero extra navigation | ux | P2 | `/desk` |
| UT-11 | Two-firing JBE ladder discloses step ratio | happy-path | P2 | `/desk` |

**P1 tests must all pass for browser QA verdict to be PASS.**
