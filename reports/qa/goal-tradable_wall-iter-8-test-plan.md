# Goal Iteration 8 Functional Test Plan

**Phase:** goal-tradable_wall-iter-8
**Date:** 2026-07-15
**Frontend Present:** yes

## Phase Goal

Make J-03 visible and honest: the pinned AAPL 2026-06-22 case-study drill-in shows real recorded five-state tape timeline, and the Edge Report shows populated cells with real n and honest insufficient_sample labels on persisted credentialed recordings.

## Test Cases

### TC-01 — AAPL pinned drill-in shows populated tape timeline

**Type:** browser
**Preconditions:** Backend is running; `/structure` page loads; 11 persisted datasets exist at `apps/backend/.data/datasets/` including AAPL 2026-06-22 window (5c7f1a44…)

**Steps:**
1. Navigate to `/structure`
2. Click "Case Studies" section
3. Locate and click the pinned AAPL 2026-06-22 case study
4. Scroll to the "Tape Timeline" subsection (~300 touch area)
5. Extract DOM text from the timeline (per iter-6 lesson: use DOM extraction, not screenshot, for deep-scroll sections)

**Expected outcome:** Timeline displays five-state sequence (e.g., "INIT → RESTING → TRACKING → TRIGGERED → …") with transition timestamps around the touch; not the empty-state "No recorded tape for this event."

**Pass criteria:** DOM text contains at least 3 distinct state names from {INIT, RESTING, TRACKING, TRIGGERED, RESET} and at least 2 timestamps (ISO format or HH:MM:SS); no empty-state placeholder text present.

---

### TC-02 — Edge Report shows populated cells with real counts

**Type:** browser
**Preconditions:** Backend is running; `/structure` page loads; Edge Report section renders; at least one real dataset exists for a panel symbol

**Steps:**
1. Navigate to `/structure`
2. Scroll to "Edge Report" section
3. Inspect the table/grid cells for strategy × class × side × reaction rows
4. Extract text/values from cells in the `n` (sample count) column

**Expected outcome:** At least one cell shows a numeric `n` value (e.g., "n=42") for each of {v1, structure_tape, structure_tape_map} strategies; cells with n<5 are labelled `insufficient_sample`; no cells are vacuously empty

**Pass criteria:** DOM contains ≥3 rows (one per strategy), each row has ≥1 cell with either a count `n=X` or text `insufficient_sample`; no all-empty row exists.

---

### TC-03 — GET /research/datasets returns ≥10 windows / ≥5 symbols including pinned AAPL

**Type:** api
**Preconditions:** Backend is running on port 8301 (or configured backend port)

**Steps:**
1. Run: `curl -s http://localhost:8301/research/datasets | jq -r '.datasets | length'`
2. Run: `curl -s http://localhost:8301/research/datasets | jq -r '.datasets[] | .symbol' | sort | uniq | wc -l`
3. Run: `curl -s http://localhost:8301/research/datasets | jq '.datasets[] | select(.id == "5c7f1a44aa71412eb874cb639dde56e2")'`

**Expected outcome:** 
- Step 1 returns a number ≥10 (window count)
- Step 2 returns a number ≥5 (unique symbol count)
- Step 3 returns a non-empty JSON object for the pinned AAPL window

**Pass criteria:** All three steps succeed with exit code 0; counts are integers; Step 3 JSON contains `id`, `symbol`, `feed`, `split` fields; `feed` field equals `"sip"` (not iex or Yahoo).

---

### TC-04 — GET /research/setups/{pinned-id} returns populated tape_timeline

**Type:** api
**Preconditions:** Backend is running; pinned AAPL dataset ID is `5c7f1a44aa71412eb874cb639dde56e2`

**Steps:**
1. Run: `curl -s http://localhost:8301/research/setups/5c7f1a44aa71412eb874cb639dde56e2 | jq '.tape_timeline'`

**Expected outcome:** JSON object with `states` array containing ≥3 state objects, each with `name`, `start_time`, `end_time` fields; no empty array or null value

**Pass criteria:** Exit code 0; `states` is an array of length ≥3; each state has non-null `name` (string from {INIT, RESTING, TRACKING, TRIGGERED, RESET}) and `start_time`/`end_time` (ISO 8601 timestamps).

---

### TC-05 — GET /research/edge-report returns populated cells (not all-empty)

**Type:** api
**Preconditions:** Backend is running; at least one panel-symbol dataset recorded

**Steps:**
1. Run: `curl -s http://localhost:8301/research/edge-report | jq '.cells | length'`
2. Run: `curl -s http://localhost:8301/research/edge-report | jq '.cells[] | select(.n >= 5 or .insufficient_sample == true)' | wc -l`

**Expected outcome:** 
- Step 1 returns ≥1 (at least one cell exists)
- Step 2 shows at least one cell with either n≥5 or insufficient_sample=true (honest labelling)

**Pass criteria:** Both commands exit with 0; Step 1 count ≥1; Step 2 shows ≥1 valid cell (never manufactures a survivor by lowering n or pooling feeds).

---

### TC-06 — test_no_credential_in_artifacts.py passes

**Type:** artifact
**Preconditions:** Backend test suite environment is set up; pytest is available

**Steps:**
1. Run: `cd /home/dennis-chan/Git/tapeology/apps/backend && .venv/bin/python -m pytest tests/test_no_credential_in_artifacts.py -v`

**Expected outcome:** All tests pass; exit code 0; no Alpaca credentials found in any file, log, or artifact

**Pass criteria:** Pytest reports "passed" status; grep for `AKIAIOSFODNN`, `SK_`, `alpaca`, `api_key` across reports/ and logs/ returns no matches (case-insensitive).

---

### TC-07 — test_price_chart_confluence.py passes after Cleanup B

**Type:** artifact
**Preconditions:** Backend test suite environment is set up; T1 docstring and test #5 corrected; pytest available

**Steps:**
1. Run: `cd /home/dennis-chan/Git/tapeology/apps/backend && .venv/bin/python -m pytest tests/test_price_chart_confluence.py -v`

**Expected outcome:** All 9 tests pass; exit code 0; test #5 assertion correctly reflects the no-fallback, epoch_anchor-gated behavior; docstring describes keyed-on-epoch_anchor fetch, not wall-clock fallback

**Pass criteria:** Pytest reports "9 passed"; assertion in test #5 does NOT check for "new Date().toISOString()" string; docstring mentions early-return guard and epoch_anchor keying.

---

### TC-08 — PriceChart.tsx early-return gating on epoch_anchor (Cleanup A)

**Type:** browser
**Preconditions:** Frontend is running on port 3000; backend is running; a watched session with an epoch_anchor exists (e.g., historical replay AAPL 2026-06-22)

**Steps:**
1. Open browser DevTools (Network tab)
2. Navigate to `/` (Cockpit)
3. Load a watched session that has an epoch_anchor (e.g., historical replay)
4. Observe network requests: does a tradability fetch (GET /research/tradability) occur?
5. Clear the watched session (or select one with epoch_anchor=null); re-observe tradability fetch attempts

**Expected outcome:** 
- Step 4: tradability fetch DOES occur (the session has an anchor)
- Step 5: NO tradability fetch occurs (early-return prevents fetch); no wall-clock `asOf` value in logs

**Pass criteria:** Network tab shows fetch occurs only when epoch_anchor is truthy; no logs contain today's date as an `asOf` value during the waiting-for-anchor window; SIM symbols (which always have an anchor) fetch normally.

---

### TC-09 — SIM symbols keep honest "no tradable map" empty state

**Type:** browser
**Preconditions:** Frontend is running; backend is running; a SIM-*/no-bars symbol is available in a watched session (e.g., SIM-BUYER)

**Steps:**
1. Navigate to `/` (Cockpit)
2. Load a session with a SIM symbol that has no bar series
3. Inspect the `PriceChart` component area
4. Check whether bands/overlay are rendered or an empty-state placeholder is shown

**Expected outcome:** No tradable bands rendered; no error overlay; empty state or placeholder indicates "no tradable map available" (or similar honest message)

**Pass criteria:** DOM contains no `<line>` or band elements for price bands; if a text element exists, it reads "no tradable map", "no bars", or similar honest description; the component does not flash or show transient wrong-session bands.

---

### TC-10 — cockpit chip + band overlay re-verified on AAPL historical replay (J-06 regression)

**Type:** browser
**Preconditions:** Frontend is running; backend is running; datasets exist; AAPL 2026-06-22 historical replay accessible

**Steps:**
1. Navigate to `/` (Cockpit)
2. Select AAPL 2026-06-22 historical session/replay
3. Observe the `PriceChart` component: band overlay should render with correct basis (2026-06-18, the prior close of the replay anchor)
4. Verify the chip text is descriptive-only (e.g., "Edge: measured history per [link]"), not imperative ("Buy here", "Sell now")
5. Switch to live mode; verify PriceChart is not mounted at all (component hidden)

**Expected outcome:** 
- Band overlay renders with 2026-06-18 basis (no flash of today's date)
- Chip copy is descriptive and cites a source
- Live mode shows no chart or bands

**Pass criteria:** Screenshot shows band overlay present with correct date; chip text contains no imperative verbs (buy/sell/short/expect); live mode UI hides the entire PriceChart component (inspect DOM).

---

### TC-11 — /structure Tradable Map still defaults to ≤10 bands with pinned resistance (J-05 regression)

**Type:** browser
**Preconditions:** Frontend is running; backend is running; navigate to `/structure` page

**Steps:**
1. Navigate to `/structure`
2. Observe the default display: Tradable Map should be shown (not raw-levels)
3. Count the bands rendered
4. Check for the pinned resistance band (around ~300 for AAPL)

**Expected outcome:** Tradable Map is the default view; ≤10 bands are visible; at least one band is present near the expected resistance level

**Pass criteria:** DOM shows ≤10 `<line>` or band elements; no raw-levels toggle is selected; band labels/values align with expected zones for the chosen symbol.

---

### TC-12 — Navigation unchanged: Cockpit, Journal, Studies, Performance, Structure (J-07 regression)

**Type:** browser
**Preconditions:** Frontend is running; sidebar or top navigation is visible

**Steps:**
1. Inspect the main navigation bar/menu
2. Count and list all top-level nav items
3. Verify each is still present and clickable

**Expected outcome:** Exactly 5 nav items: Cockpit, Journal, Studies, Performance, Structure; no new items added

**Pass criteria:** Each nav item is present and has a click handler; no "Datasets", "/research", or other new pages in the nav; full regression sentinel passes.

---

### TC-13 — Full backend test suite passes (keyless via committed fixture)

**Type:** artifact
**Preconditions:** Backend test environment set up; no Alpaca credentials required; pytest available

**Steps:**
1. Run: `cd /home/dennis-chan/Git/tapeology/apps/backend && .venv/bin/python -m pytest tests/ -q`
2. Capture stdout and stderr
3. Count "passed", "skipped", "failed"

**Expected outcome:** All critical tests pass; baseline is 1348 passed / 7 skipped / 0 failed (or same pass baseline from iter-7)

**Pass criteria:** Exit code 0; "passed" count ≥1348; "failed" count = 0; no new failures introduced.

---

### TC-14 — config_fingerprint == 4d665603569b9dbf (no frozen files touched)

**Type:** artifact
**Preconditions:** Backend is runnable; Python environment set up

**Steps:**
1. Run: `cd /home/dennis-chan/Git/tapeology && python3 -c "from apps.backend.app.config import config_fingerprint; print(config_fingerprint())"`
2. Verify the printed value matches the expected fingerprint

**Expected outcome:** Fingerprint is `4d665603569b9dbf` (unchanged from iter-7)

**Pass criteria:** Printed value equals `4d665603569b9dbf`; exit code 0; no frozen file (levels.py, engine/, config.py, adapters/, etc.) is modified.

---

### TC-15 — sip feeds never pooled with iex or Yahoo lineages in Edge Report

**Type:** artifact
**Preconditions:** Backend is running; Edge Report endpoint accessible

**Steps:**
1. Run: `curl -s http://localhost:8301/research/edge-report | jq '.cells[] | select(.feed == "iex" or .feed == "yahoo")'`
2. Check if any cells exist with feed="iex" or feed="yahoo"
3. If cells exist, verify no row pools iex+sip or Yahoo+sip in the same strategy/class/side/reaction group

**Expected outcome:** All cells are either feed="sip" or are clearly separated by feed; no pooled analysis across iex and sip

**Pass criteria:** Step 1 returns no results (all cells are sip), OR Step 1 returns results but each row is independently labeled with its feed and never aggregated across feeds.

---

## Summary

**Total test cases:** 15
- **API tests:** 5 (TC-03, TC-04, TC-05, TC-06, TC-15)
- **Browser tests:** 7 (TC-01, TC-02, TC-08, TC-09, TC-10, TC-11, TC-12)
- **Artifact tests:** 3 (TC-07, TC-13, TC-14)

**Regression coverage:** J-01, J-02, J-04, J-05, J-06, J-07 all verified as green through dedicated tests (TC-10, TC-11, TC-12) and full suite run (TC-13).

**External integration:** TC-03, TC-04, TC-05 verify that persisted credentialed datasets (real Alpaca sip recordings) are readable by the backend without re-recording; closure of iter-3/iter-7 durability lesson.

**Anti-goal compliance:** TC-06 (no credentials), TC-15 (feed honesty), TC-09 (honest empty state), TC-02 (insufficient_sample never manufactured) address critical anti-goals.
