# Goal Iteration 29 Functional Test Plan

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-29
**Date:** 2026-06-16
**Frontend Present:** yes

## Phase Goal

Capture market-hours-gated live-feed evidence for J-15 (live status flipping `live → stale → live` across a genuine feed lull with no fabricated trades) and J-67 live leg (live IEX cockpit rendering `FeedBasisBadge` + disclosure and a live-declared thesis stamped `data_feed = iex`), backed by a credentialed live-socket integration run, while keeping app source byte-identical and all required-still-passing journeys green.

## Test Cases

### TC-01 — Live IEX feed integration test (gated, credentialed)

**Type:** api
**Preconditions:**
- US regular market session is OPEN (Tue 2026-06-16 ~14:00 ET)
- `ALPACA_API_KEY` and `ALPACA_API_SECRET` are set in `apps/backend/.env`
- Backend is running with `.env` loaded (creds in `os.environ`)
- `apps/backend/tests/test_live_integration.py` exists and is runnable

**Steps:**
1. Run the gated credentialed integration test: `TAPEOLOGY_LIVE_INTEGRATION=1 .venv/bin/python -m pytest apps/backend/tests/test_live_integration.py -v -s`
2. Observe the test execution against the real Alpaca IEX socket

**Expected outcome:** Test passes with assertions for `stream_status == "live"`, `event_count > 0`, real bid/ask values, valid tape state, and correct live scenario descriptor.

**Pass criteria:** Exit code 0; output contains "PASSED" or "passed"; `stream_status` confirmed as `live`; `event_count > 0`; no "fabricated" or "simulated" data in the live run.

---

### TC-02 — Live status indicator: initial `live` state

**Type:** browser
**Preconditions:**
- Backend is running with `.env` loaded (live creds in `os.environ`)
- Frontend is running on http://localhost:3000
- US regular market session is OPEN
- A liquid, tight-spread symbol is chosen (e.g., `F` or `AAPL`)

**Steps:**
1. Navigate to http://localhost:3000 (Cockpit home)
2. Enter the chosen symbol in the Watch input and submit
3. Wait for the cockpit to populate (status → `connecting` → `live`)
4. Observe the status indicator area (row 6, `stream_status`)
5. Verify the status dot and label show `live` (green, distinct visual treatment)

**Expected outcome:** The status indicator renders with a green visual treatment (color: emerald-400/emerald-500) and the label reads `live`.

**Pass criteria:** Screenshot confirms the status dot is green/emerald and the label text is "live"; `GET /tape/{symbol}/summary` REST query confirms `stream_status == "live"`.

---

### TC-03 — Live status indicator: transient `stale` flip across feed lull

**Type:** browser
**Preconditions:**
- Backend is running with live creds; frontend is running
- A live watch is active on a liquid symbol (e.g., `F`)
- Initial status is confirmed as `live` (from TC-02)
- A natural IEX feed lull (gap > `stale_gap_seconds` = 10s) is expected to occur within the test window

**Steps:**
1. Hold the cockpit view open and monitor the status indicator continuously
2. Await a feed lull (no new trades/quotes for >10 seconds)
3. At the moment the status indicator visibly changes to `stale` (amber/neutral treatment), take a full-page screenshot
4. Verify the recent-trades count is frozen (not advancing during the gap — no fabricated trades)
5. Await the feed to resume (new trades appear); verify the status recovers to `live`
6. Take a screenshot showing the recovery

**Expected outcome:** 
- The status indicator visibly flips to `stale` (amber visual treatment, distinct from `live`) during the lull
- Recent-trades count is frozen during the gap (no new entries added while status is `stale`)
- Status recovers to `live` when feed resumes

**Pass criteria:**
- Screenshot 1 clearly shows the `stale` indicator (amber color, label text "stale") with recent-trades count frozen
- The `stale` indicator is visually distinct from `live` (different color, same position, same dot+label layout)
- Recent-trades table shows no new rows added during the gap window
- Screenshot 2 shows status returned to `live` with new trades now advancing
- `/tape/{symbol}/summary` REST polls during the gap confirm `stream_status == "stale"`; after recovery confirm `stream_status == "live"`

---

### TC-04 — Live IEX FeedBasisBadge: renders with `iex` basis and disclosure

**Type:** browser
**Preconditions:**
- Backend is running with live creds; frontend is running
- A live watch is active on the IEX feed (status is `live`)
- The status area (row 29, current-watch feed basis) is visible in the cockpit viewport

**Steps:**
1. Navigate to the cockpit (http://localhost:3000)
2. Watch a live symbol (e.g., `F` or `AAPL`) to activate the live IEX feed
3. Locate the `FeedBasisBadge` in the status area (row 29, below the status indicator)
4. Verify the badge reads `iex` (the feed basis)
5. Verify the IEX-vs-SIP disclosure line is visible in the viewport: "live verdicts read the single-venue IEX feed; historical replay and studies use SIP — spreads and prints differ"

**Expected outcome:**
- The `FeedBasisBadge` renders and displays `iex` as the feed basis
- The disclosure line is legible and present on screen

**Pass criteria:**
- Screenshot shows the badge containing the text "iex"
- Screenshot shows the full disclosure line: "live verdicts read the single-venue IEX feed; historical replay and studies use SIP — spreads and prints differ"
- `GET /tape/{symbol}/summary` REST response includes `feed_basis == "iex"` in the snapshot metadata (row 29)

---

### TC-05 — Live thesis declaration and IEX journal row (`data_feed = iex`)

**Type:** browser
**Preconditions:**
- Backend is running with live creds; frontend is running
- A live watch is active on a symbol (status is `live`)
- The cockpit thesis panel is visible (thesis strip below the main panel grid)
- The `/journal` page is accessible

**Steps:**
1. In the cockpit, declare a live thesis (e.g., "absorption_reversal long with invalidation at X")
2. Confirm the thesis is submitted (UI updates to show thesis state)
3. Wait for a new trade/quote that matches the thesis context (or trigger one by natural feed activity)
4. Navigate to the `/journal` page
5. Locate the row corresponding to the live-declared thesis
6. Verify the row contains `data_feed = iex` (proving the live IEX feed is labeled)

**Expected outcome:**
- The thesis is declared and accepted by the UI (no error)
- A `/journal` row is created with the thesis metadata
- The row's `data_feed` field is stamped `iex` (not "sim" or "sip")

**Pass criteria:**
- `/journal` API response includes a row with `data_feed == "iex"` corresponding to the declared thesis timestamp
- The `data_feed` value is visible in the `/journal` table UI or can be confirmed via REST (`GET /research/journal`)
- No SIP rows appear in the same journal for this live session (single-source, no pooling)

---

### TC-06 — Required-still-passing J-01: SIM-BUYER cockpit and REST==UI

**Type:** browser
**Preconditions:**
- Backend is running
- Frontend is running
- Database or cached state is clean (or previous sessions do not interfere)

**Steps:**
1. Navigate to http://localhost:3000 (Cockpit home)
2. Ensure the mode selector shows "SIM" (Simulated mode, not Live)
3. Enter a symbol (e.g., `TEST_BUYER_CONTROL`) that triggers a buyer-control scenario
4. Wait for the cockpit to populate with the simulated tape
5. Observe the tape state label (should read `buyer_control`)
6. Fetch `GET /tape/{symbol}/summary` via REST and compare to UI
7. Verify REST response matches the cockpit display (same tape state, confidence, bid/ask, recent trades)

**Expected outcome:** The SIM cockpit renders the `buyer_control` state with high confidence; REST and UI agree.

**Pass criteria:**
- Cockpit displays tape state = `buyer_control`
- `GET /tape/{symbol}/summary` REST response contains `tape_state == "buyer_control"`
- Recent-trades count, bid/ask, and confidence score match between UI and REST

---

### TC-07 — Required-still-passing J-02: SIM-SELLER cockpit and REST==UI

**Type:** browser
**Preconditions:**
- Backend is running; frontend is running
- Mode is set to "SIM"

**Steps:**
1. Watch a simulated symbol that triggers a seller-control scenario (e.g., `TEST_SELLER_CONTROL`)
2. Observe the cockpit for the tape state
3. Verify the state label reads `seller_control`
4. Fetch `GET /tape/{symbol}/summary` and compare to UI

**Expected outcome:** The SIM cockpit renders `seller_control`; REST and UI match.

**Pass criteria:**
- Cockpit displays `seller_control`
- REST response confirms `tape_state == "seller_control"`

---

### TC-08 — Required-still-passing J-08: SIM-ABSORPTION cockpit

**Type:** browser
**Preconditions:**
- Backend is running; frontend is running
- Mode is "SIM"

**Steps:**
1. Watch a simulated symbol that triggers a bid-absorption scenario
2. Observe the cockpit tape state
3. Verify the label reads `bid_absorption` or `ask_absorption` (whichever scenario is triggered)

**Expected outcome:** The cockpit renders the absorption state with amber/neutral visual treatment.

**Pass criteria:**
- Tape state label contains "absorption"; color treatment is amber (not green or red)

---

### TC-09 — Required-still-passing J-11: Historical SIP real data

**Type:** browser
**Preconditions:**
- Backend is running with SIP credentials (from `apps/backend/.env`)
- Frontend is running
- Historical mode is available

**Steps:**
1. Navigate to the cockpit
2. Switch to Historical mode (if available) or verify historical data can be fetched
3. Select a real symbol (e.g., `AAPL`) and a past date/time window
4. Fetch the historical data (should use the real SIP feed via Alpaca)
5. Observe the cockpit populates with historical trades/quotes

**Expected outcome:** Historical data loads without error; the cockpit renders a tape state based on real SIP data.

**Pass criteria:**
- Historical window is fetched successfully (no "unavailable" or "error" state)
- Cockpit displays historical tape state, bid/ask, and trades; no fabricated data

---

### TC-10 — Required-still-passing J-14: Unknown symbol honest-failure (J-14 carry)

**Type:** browser
**Preconditions:**
- Backend is running; frontend is running
- Any mode (SIM, Live, or Historical)

**Steps:**
1. Watch a non-existent symbol (e.g., `ZZZNOEXIST`)
2. Wait for the backend to reject the symbol
3. Observe the UI for an explicit error or failure state

**Expected outcome:** The cockpit displays an explicit "not a tradable symbol" error or similar honest-failure message (not a blank screen or generic error).

**Pass criteria:**
- UI renders an explicit error panel with a message indicating the symbol is unknown or not tradable
- No fabricated tape state is shown

---

### TC-11 — Required-still-passing J-16: Historical SIP real data (additional symbol)

**Type:** browser
**Preconditions:**
- Backend is running with SIP credentials
- Frontend is running
- Historical mode is available

**Steps:**
1. Select a different real symbol (e.g., `SPY`) in Historical mode
2. Select a past date/time window
3. Fetch the historical data

**Expected outcome:** Historical data loads for a different symbol; tape state is computed from real SIP data.

**Pass criteria:**
- Historical window loads without error
- Cockpit renders a valid tape state for the selected symbol and window

---

### TC-12 — Required-still-passing J-18: Historical SIP real data (edge case)

**Type:** browser
**Preconditions:**
- Backend is running with SIP credentials
- Frontend is running
- Historical mode is available

**Steps:**
1. Select a symbol and an edge-case historical window (e.g., very short window, off-hours, or weekend)
2. Attempt to fetch the data

**Expected outcome:** The UI returns an honest-failure message if the window is invalid (e.g., "market closed", "no data available for this window") — not a blank cockpit or fabricated state.

**Pass criteria:**
- UI renders an explicit error or "no data" state
- No fabricated tape state is shown for invalid windows

---

### TC-13 — Required-still-passing J-23: Explicit failure panel visibility

**Type:** browser
**Preconditions:**
- Backend is running; frontend is running
- An error condition is triggered (e.g., unknown symbol, no data, or provider unavailable)

**Steps:**
1. Trigger a failure condition (e.g., watch a bad symbol)
2. Observe the cockpit for an explicit error/failure panel

**Expected outcome:** An explicit failure panel is rendered on screen (not hidden, not collapsed, not a generic message).

**Pass criteria:**
- Screenshot shows a visible failure panel with clear text indicating the error type

---

### TC-14 — Required-still-passing J-68: No-thesis cockpit unchanged (full grid + idle thesis + sound toggle)

**Type:** browser
**Preconditions:**
- Backend is running; frontend is running
- A watch is active (simulated or live) with a valid tape state
- No thesis has been declared

**Steps:**
1. Navigate to the cockpit
2. Watch a symbol (e.g., simulated `TEST_BUYER_CONTROL`)
3. Observe the cockpit layout without a declared thesis
4. Verify all components are visible:
   - Full panel grid (status, bid/ask, recent-trades, confidence, etc.)
   - Idle thesis strip (placeholder or disabled state, not removed)
   - Sound toggle control (visible and functional)
5. Take a full-page screenshot

**Expected outcome:** All layout elements render without displacement; the thesis strip is present but idle; the sound toggle is visible.

**Pass criteria:**
- Full-page screenshot shows all expected panels and controls in their correct positions
- Thesis strip is present but visually idle/disabled (no declared thesis yet)
- Sound toggle is accessible and functional

---

### TC-15 — App source byte-identity check (git diff)

**Type:** artifact
**Preconditions:**
- Iteration development is complete
- Git working tree is clean (no uncommitted changes outside the intended scope)

**Steps:**
1. Run: `git status --porcelain apps/backend/ apps/frontend/`
2. Run: `git diff --stat HEAD -- apps/backend/ apps/frontend/`
3. Verify the output is empty (no changes) or contains only justified, re-pinned bug fixes

**Expected outcome:**
- `git status --porcelain` returns empty (no modified, added, or deleted files in `apps/backend/` or `apps/frontend/`)
- `git diff --stat HEAD` returns empty (no diff) OR contains only a justified fix with clear changelog

**Pass criteria:**
- Both commands return empty output, OR
- Any changes are explicitly documented in the dev handoff as justified bug fixes (with description of the genuine live-feed defect and the fix applied)

---

### TC-16 — Backend test suite passes with zero re-pins

**Type:** api
**Preconditions:**
- Backend is running or tests can be executed against it
- All backend dependencies are installed

**Steps:**
1. Run the backend test suite: `cd apps/backend && python -m pytest` (or per `.claude/project-template.md`)
2. Capture the exit code and output
3. Verify no re-pins are present (no `# @re-pin` markers added or modified)

**Expected outcome:** All tests pass; exit code is 0; no re-pins are introduced.

**Pass criteria:**
- Pytest exit code = 0
- Output shows "X passed" with no "failed" or "error"
- No new or modified `# @re-pin` markers in test files or source code

---

### TC-17 — Observer equivalence re-run (`test_observer_equivalence.py`)

**Type:** api
**Preconditions:**
- Backend is running
- `apps/backend/tests/test_observer_equivalence.py` exists and is runnable

**Steps:**
1. Run the observer equivalence test: `cd apps/backend && python -m pytest tests/test_observer_equivalence.py -v`
2. Capture the exit code and output

**Expected outcome:** The test passes, confirming the engine produces byte-identical results with and without research observers.

**Pass criteria:**
- Exit code = 0
- Output contains "PASSED" or "passed" for all observer equivalence assertions

---

### TC-18 — No fabricated data during `stale` lull (recent-trades count frozen)

**Type:** artifact
**Preconditions:**
- TC-03 (live status `stale` flip) has been executed and a screenshot captured during the lull
- REST API is accessible

**Steps:**
1. Review the screenshot from TC-03 showing the `stale` state
2. Note the recent-trades count at the moment `stale` was captured
3. Poll the REST API multiple times during the next 5–10 seconds (while still `stale`)
4. Verify the recent-trades count does not increase

**Expected outcome:**
- Recent-trades count remains the same during the `stale` lull
- No new trades are fabricated or injected to mask the gap

**Pass criteria:**
- Recent-trades count in screenshot matches the count in subsequent REST polls while status is `stale`
- After recovery to `live`, new trades appear and the count increases (proving the feed resumed, not a stuck counter)

---

## Summary

**Total test cases:** 18

**Test breakdown by type:**
- **API tests:** 4 (TC-01, TC-16, TC-17, TC-18 artifact-verification)
- **Browser tests:** 11 (TC-02 through TC-15, TC-03 primary)
- **Artifact checks:** 3 (TC-15 git diff, TC-18 no-fabrication, TC-17 observer equivalence)

**Critical test cases (gates to J-15/J-67 passing):**
- TC-01: Credentialed live integration run (authoritative pipeline proof)
- TC-03: Live status `stale` flip with frozen recent-trades (J-15 core requirement)
- TC-04: Live IEX `FeedBasisBadge` + disclosure (J-67 live leg)
- TC-05: Live thesis + `data_feed = iex` journal row (J-67 live leg, feed labeling)

**Anti-goal compliance checks:**
- TC-18: No fabricated data (frozen recent-trades during `stale` lull)
- TC-04/TC-05: Feed labeling (explicit `iex` badge + disclosure + journal stamp)
- TC-06 through TC-14: No SIP/IEX pooling, honest-failure states, no order/broker surface

**All required-still-passing journeys spot-checked:** TC-06 (J-01), TC-07 (J-02), TC-08 (J-08), TC-09/TC-11/TC-12 (J-11/J-16/J-18), TC-10 (J-14), TC-13 (J-23), TC-14 (J-68), TC-15 (byte-identity).
