# Phase goal-observation-contract-iter-6 — What to Click (Operator Verification Guide)

**Phase:** goal-observation-contract-iter-6
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Backend running at `http://localhost:8301` and frontend running at `http://localhost:3301`
  (`scripts/dev.sh` default pair)
- No login required — the app has no auth
- No seed data needs to be created — this guide only uses the built-in `SIM-BIDABS` simulated
  ticker

**Why this check matters:** this iteration adds **zero** user-facing capability. It ships one new
backend test file (a "guard suite" that runs invisibly in CI) and closes two evidence gaps by
independently re-reading an already-shipped JSON endpoint. Steps 1-2 and 8-10 below should look
and behave exactly as they did after the previous iteration — you are confirming nothing broke.
Steps 3-7 are the one piece of substantive re-verification this iteration performs.

---

## Verification Steps

1. Open `http://localhost:3301/` in your browser
   - **Expect:** Page loads, header reads "Tapeology", a "Data source" control shows "Live" / "Historical" / "Simulated"

2. With "Simulated" selected, type "SIM-BIDABS" into the "Ticker" field, then click the green "Watch" button
   - **Expect:** The text "Watching SIM-BIDABS" appears; within about 15 seconds the status dot in the top-right of the header reads "live"

3. Open a new browser tab and navigate to `http://localhost:8301/tape/SIM-BIDABS/observation`
   - **Expect:** Raw JSON text appears, starting with `{"schema_version":"tape-observation-v1","provider":"tapeology","ticker":"SIM-BIDABS"`. Note the value shown for `"observation_hash"`.

4. Go back to the first tab and click the amber "Pause" button next to "Watching SIM-BIDABS"
   - **Expect:** The status dot changes to "paused"

5. Go to the JSON tab and reload the page (F5) twice in a row
   - **Expect:** On every reload, `"observation_hash"` shows the exact same value you noted in step 3, but `"generated_at_utc"` and `"artifact_hash"` show a new value each time

6. Back in the first tab, click "Stop"
   - **Expect:** The "Watching SIM-BIDABS" row disappears and the page returns to its idle state

7. Reload the JSON tab (`http://localhost:8301/tape/SIM-BIDABS/observation`) once more
   - **Expect:** The page now shows `{"detail":"Ticker 'SIM-BIDABS' is not being watched"}` — a 404, not the observation data

8. Click "Structure" in the top navigation bar
   - **Expect:** Navigates to `http://localhost:3301/structure`; heading reads "Structure"; page looks exactly as before

9. Click "Desk" in the top navigation bar
   - **Expect:** Navigates to `http://localhost:3301/desk`; heading reads "Desk"; page looks exactly as before

10. Look at the top navigation bar one final time
    - **Expect:** Still exactly three links — "Cockpit", "Structure", "Desk" — no fourth link (e.g. no "Observation" or "Guards") has appeared anywhere

---

## What "Working Correctly" Looks Like

- Steps 1-2 and 8-10 look and behave identically to how the product behaved before this
  iteration — this iteration is a pure regression check on everything you can see and click.
- Steps 3-7 are the one substantive verification this iteration performs: the same underlying
  observation (`observation_hash`) is provably stable across repeated reads while its wrapping
  envelope (`generated_at_utc`, `artifact_hash`) is provably fresh each time, and the endpoint
  honestly refuses to answer once you stop watching.

## Common Issues

- **Blank page / error screen on `/`, `/structure`, or `/desk`**: confirm the backend process
  (the terminal running `uvicorn` on port 8301) has not crashed.
- **Step 3's tab shows a Next.js "404 — This page could not be found" page instead of raw JSON**:
  you likely typed the URL on port 3301 instead of 8301 — the observation JSON is served only
  from the backend origin (`:8301`), never the frontend (`:3301`).
- **`observation_hash` changes between the two reloads in step 5**: this is a real regression —
  report it immediately. The entire point of this era's paused-reload guarantee is that it must
  NOT change while the watch is paused.
- **A fourth nav link appears in step 10**: this is a regression — report it immediately, do not
  dismiss it as cosmetic.
