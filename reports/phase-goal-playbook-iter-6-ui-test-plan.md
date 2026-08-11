# Phase goal-playbook-iter-6 — UI Test Plan

**Phase:** goal-playbook-iter-6
**Date:** 2026-08-11
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301

---

## Fixture-rig precondition (applies to UT-02, UT-03, UT-04, UT-09, UT-11)

This iteration's three new detectors (`range_trade`, `double_top`, `double_bottom`) have NOT yet
fired on any session in the operator's real recorded universe — the real back-scan is J-07's job,
not this iteration's. The phase spec's own TC-1/TC-4/TC-9 are written against "the fixture rig," not
the live production store. Before running UT-02/UT-03/UT-04/UT-09/UT-11, the tester
(browser-qa-agent) must stand up that rig:

1. Start the backend with `TAPEOLOGY_BAR_DIR`, `TAPEOLOGY_DESK_UNIVERSE_DIR`,
   `TAPEOLOGY_DESK_PLAYBOOK_DIR`, and `TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR` ALL pointed at fresh, shared
   scratch directories — never the operator's real `.data/` store. This four-variable scoping
   together is this iteration's own fix for TC-19 (two prior orphaned run-ledger rows were traced to
   only `TAPEOLOGY_DESK_PLAYBOOK_DIR` being scoped, not its log-dir sibling); reuse it exactly.
2. Seed a `BarStore`/`UniverseStore` the backend actually reads from with:
   - A canonical `range_trade` support-bounce-long session for symbol `RTAAA`, session date
     `2026-06-22` — reuse the exact bar construction in `_plant_range_trade_session` plus
     `_plant_decoration_baseline_sessions(bar_store, "RTAAA", slots=8)`, both in
     `apps/backend/tests/test_desk_playbook.py` (used by
     `test_range_trade_wired_into_compute_playbook_is_measured_like_every_other_setup`).
   - A canonical `double_top` session for symbol `DTAAA`, same session date `2026-06-22` — reuse
     `_plant_double_top_session` plus `_plant_decoration_baseline_sessions(bar_store, "DTAAA", slots=20)`
     (used by `test_double_top_and_double_bottom_wired_into_compute_playbook_is_measured_like_every_other_setup`).
3. Confirm the backend is alive by request, not PID: `curl :8301/health` returns
   `{"status":"ok"}` (iter-2 lesson).
4. Note: the compute-walk-level (full `BarStore` → API) fixtures committed to the test suite only
   cover the LONG side of `range_trade` (support-bounce) and the SHORT side of the double-extreme
   pair (`double_top`). A live browser view of the resistance-fade short `range_trade` or the
   `double_bottom` mirror requires planting an additional fixture (the mirror of the fixtures above,
   same construction pattern flipped per `test_canonical_range_trade_short_mirrors_the_long_fixture`
   / `test_canonical_double_bottom_mirrors_the_double_top_fixture` in `test_desk_playbook_detect.py`)
   — this is optional and only required for UT-11's stretch coverage, not for TC-9's minimum bar
   (one `range_trade` + one `double_top`-or-`double_bottom` signal).

If the rig cannot be stood up, UT-02/UT-03/UT-04/UT-09/UT-11 cannot be executed — report them
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
2. Scroll down to the section with the heading "Playbook Signals" (`aria-label="Playbook Signals"`, panel title reads exactly "Playbook Signals")

**Expected Result:**
- The "Playbook Signals" panel renders without a blank screen or error message
- A text input labeled "Session date (yyyy-MM-dd) — blank = the most recent recorded session" is visible (`data-testid="desk-playbook-date-input"`)
- A "Run Playbook" button is visible (`data-testid="desk-playbook-compute-button"`) — label reads "Run Playbook" (not "Computing…" or "Retry Run Playbook") when idle
- The paragraph directly above the date input reads "The book's opening-range-break, jump-base-explosion, drop-base-implosion, cup-and-handle, capitulation, range-trade, double-top, and double-bottom signals, detected on this session's own recorded 5m/1m bars..." — all eight family names present
- No console errors

---

### UT-02 — Range Trade (support-bounce long) signal renders with its own chip and geometry (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Playbook Signals section

**Preconditions:**
- Fixture rig stood up per the precondition above, with the canonical `range_trade` fixture recorded for symbol `RTAAA`, session date `2026-06-22`

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the "Session date (yyyy-MM-dd)" field (`data-testid="desk-playbook-date-input"`), clear any existing value and type `2026-06-22`
3. Click the "Run Playbook" button (`data-testid="desk-playbook-compute-button"`)
4. Wait for the button label to return to "Run Playbook" (or for `data-testid="desk-playbook-compute-outcome"` to read "Playbook run complete for 2026-06-22.")
5. In the Playbook Signals table (`data-testid="desk-playbook-table"`), locate the row for symbol `RTAAA`
6. Click that row (`data-testid="desk-playbook-signal-row"`) to select it

**Expected Result:**
- The setup chip (`data-testid="desk-playbook-signal-setup"`) reads exactly "Range Trade" (not the raw string `range_trade`)
- The side chip (`data-testid="desk-playbook-signal-side"`) reads "long"
- Below the trigger/invalidation line in the expanded detail panel (`data-testid="desk-playbook-signal-detail"`), a paragraph with `data-testid="desk-playbook-signal-range-trade-geometry"` is present and reads in the form "range `<N>` MBR wide · low zone touches `<N>` · high zone touches `<N>` · broke at slot `<N>`", with `<N>` values being real numbers (not blank, "null", or "NaN")
- No paragraph with `data-testid="desk-playbook-signal-double-extreme-geometry"` is present on this row

---

### UT-03 — Double Top signal renders with its own chip and geometry (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Playbook Signals section

**Preconditions:**
- Fixture rig stood up with the canonical `double_top` fixture recorded for symbol `DTAAA`, session date `2026-06-22` (same "Run Playbook" click as UT-02 if both fixtures share the date — one click covers both)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. If not already computed by UT-02, enter `2026-06-22` in the "Session date (yyyy-MM-dd)" field and click "Run Playbook" (`data-testid="desk-playbook-compute-button"`); wait for completion
3. In the Playbook Signals table, locate the row for symbol `DTAAA`
4. Click that row to select it

**Expected Result:**
- The setup chip reads exactly "Double Top"
- The side chip reads "short"
- A paragraph with `data-testid="desk-playbook-signal-double-extreme-geometry"` is present, reading in the form "gap `<N>` MBR · separation `<N>` bar(s) · depth `<N>` MBR · nominal risk `<N>` MBR · broke at slot `<N>`", optionally followed by "· second RVOL vs first `<N>`"
- No paragraph with `data-testid="desk-playbook-signal-range-trade-geometry"` is present on this row
- The panel with `data-testid="desk-playbook-record"` shows both the `RTAAA` "Range Trade" row and this `DTAAA` "Double Top" row in the SAME signals table (TC-9's minimum bar: one of each new family legible in the same pass)

---

### UT-04 — All eight family names appear in the not-computed empty state and the register footer (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → Playbook Signals section

**Preconditions:**
- A session date that has NOT been computed yet (any date the fixture rig has bars for but no playbook record on file)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Enter an uncomputed session date in the "Session date (yyyy-MM-dd)" field
3. Read the amber panel with `data-testid="desk-playbook-not-computed"`
4. Click "Run Playbook" and wait for completion
5. Scroll to the bottom of the resulting record and read the amber register note (`data-testid="desk-playbook-register"`)

**Expected Result:**
- Step 3: the amber panel's sub-text reads "Run Playbook detects and measures the opening-range-break, jump-base-explosion, drop-base-implosion, cup-and-handle, capitulation, range-trade, double-top, and double-bottom families on `<date>`'s own recorded bars — an explicit operator act, nothing runs on page load." — all eight names present, ending "double-bottom"
- Step 5: the register footer text lists all eight family names, ending "...capitulation, range-trade, double-top, and double-bottom signals detected on the desk's own recorded 5m/1m bars — every threshold is fixed in advance..." — this confirms a NEWLY computed record carries the widened text (see UT-09 for the older-record contrast)

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
- A paragraph with `data-testid="desk-playbook-date-error"` appears
- The date input's border shows the amber invalid-state styling (`aria-invalid="true"`)
- The "Run Playbook" button is disabled (no compute is triggered)
- This is unchanged, already-shipped J-03 behavior — this iteration touches neither the date-parsing nor the validation logic

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
- A paragraph with `data-testid="desk-playbook-compute-trigger-error"` appears containing the text "is not a recorded trading session" (the verbatim backend refusal, unchanged from before this iteration)
- The user remains on `/desk` with the Playbook Signals section still visible

---

### UT-07 — Every previously-shipped setup family renders exactly as before (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → Playbook Signals section

**Preconditions:**
- A session with at least one recorded `open_high_break`/`open_low_break`, `jbe`/`dbi`, `cup_handle`, or `capitulation` signal is available (any J-01..J-05-era recorded session already on file, or that iteration's own fixture rig)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Enter that session's date and click "Run Playbook" (or leave blank if it is already the most recently recorded session)
3. Locate a row for one of the five prior families and click it to select it

**Expected Result:**
- The setup chip reads its pre-iteration label exactly ("Open-High Break", "Open-Low Break", "Jump-Base Explosion", "Drop-Base Implosion", "Cup and Handle", or "Capitulation")
- The detail panel shows that family's own pre-existing geometry line, unchanged in wording and values
- Neither `data-testid="desk-playbook-signal-range-trade-geometry"` nor `data-testid="desk-playbook-signal-double-extreme-geometry"` is present on this row
- The forward-measurement table, invalidation-breach note, and baseline-pool note below it are unchanged from before this iteration

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
4. Compare each section's heading text and visible layout against the stored `J-10.json` golden replay script, and separately replay the newly-recorded `J-05.json` golden script against the capitulation family

**Expected Result:**
- Every section heading listed above is present with unchanged text
- No `data-testid` or heading string introduced this iteration (`desk-playbook-signal-range-trade-geometry`, `desk-playbook-signal-double-extreme-geometry`) collides with any string the golden scripts or any of the 20 stored `goal-session-desk` scripts assert on
- Both golden replays report zero mismatches

---

### UT-09 — An already-recorded (pre-iteration) session's register footer does NOT retroactively change (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/desk` → Playbook Signals section

**Preconditions:**
- A playbook record that was computed BEFORE this iteration's code shipped is still on file for some session date (either on the operator's real store, or a fixture record deliberately planted with the pre-J-06 `PLAYBOOK_SETUPS`/register value, mirroring `test_j06_new_setups_tuple_moves_the_signature_and_mints_a_new_version_beside_the_old_file`)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Enter that pre-iteration session's date in the "Session date (yyyy-MM-dd)" field (do NOT click "Run Playbook" — loading the existing record only)
3. Scroll to the amber register note (`data-testid="desk-playbook-register"`) at the bottom of the record

**Expected Result:**
- The register text still shows the OLD wording naming only five families ("...capitulation signals detected..." with no "range-trade, double-top, and double-bottom" clause) — the record is append-only and was never rewritten by this iteration's code change
- If the operator instead clicks "Run Playbook" for the SAME date, a NEW record is minted (a different `playbook_input_signature`, since `PLAYBOOK_SETUPS` growing to nine entries moved it) showing "showing the newest recorded result of 2" (`data-testid="desk-playbook-versions"`) and the NEW record's own register footer shows the widened eight-family wording

---

### UT-10 — New setup types are discoverable with zero extra navigation (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/desk` → Playbook Signals section

**Steps:**
1. Navigate to `http://localhost:3301/desk` (home page for this app has no separate dashboard — `/desk` is the entry point)
2. Scroll to the "Playbook Signals" section (same location as before this iteration — no new nav link, no new section)
3. Run the Playbook for any session containing a `range_trade`, `double_top`, or `double_bottom` signal

**Expected Result:**
- The new setup types appear in the exact same table, using the exact same chip styling, at the exact same scroll position as every other setup — an operator who already knew how to use J-03's Playbook Signals section needs zero new navigation knowledge to find the new setup types
- No separate "new features" banner, tab, or link exists

---

### UT-11 — Range Trade's optional disclosure flags render only when true (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/desk` → Playbook Signals section

**Preconditions:**
- The UT-02 `RTAAA` fixture is recorded (`crossed_midrange`/`absorption_bar_present` are `False` on this canonical fixture per the developer's own degeneracy check — see the dev handoff)

**Steps:**
1. Navigate to `http://localhost:3301/desk`, select the `RTAAA` "Range Trade" row (as in UT-02)
2. Read the full text of the `data-testid="desk-playbook-signal-range-trade-geometry"` paragraph

**Expected Result:**
- On this fixture, the paragraph ends immediately after "· broke at slot `<N>`" with NEITHER "· crossed midrange" NOR "· absorption bar present" appended (both flags are `False` on this fixture)
- If a mirror/alternate fixture with either flag `True` is available (per the fixture-rig precondition's optional step 4), verify the corresponding suffix text DOES appear for that fixture's row, confirming both branches of the conditional render are reachable, not silently dead code

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Playbook Signals section loads, widened intro copy visible | smoke | P1 | `/desk` |
| UT-02 | Range Trade signal renders chip + geometry | happy-path | P1 | `/desk` |
| UT-03 | Double Top signal renders chip + geometry | happy-path | P1 | `/desk` |
| UT-04 | Empty-state + register footer name all eight families on a new compute | happy-path | P1 | `/desk` |
| UT-05 | Malformed date shows validation error | validation | P2 | `/desk` |
| UT-06 | Non-recorded date refused with backend message | error | P2 | `/desk` |
| UT-07 | Five prior setup families unchanged | regression | P1 | `/desk` |
| UT-08 | Every shipped section renders (J-10 sentinel + J-05 golden replay) | regression | P1 | `/desk` (whole page) |
| UT-09 | Pre-iteration record's register text is NOT retroactively rewritten | regression | P2 | `/desk` |
| UT-10 | New setups discoverable, zero extra navigation | ux | P2 | `/desk` |
| UT-11 | Range Trade's boolean disclosure flags render conditionally | happy-path | P2 | `/desk` |

**P1 tests must all pass for browser QA verdict to be PASS.**
