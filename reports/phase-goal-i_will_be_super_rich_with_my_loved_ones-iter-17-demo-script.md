# Demo Script — goal-i_will_be_super_rich_with_my_loved_ones-iter-17

**Mode:** record
**Date:** 2026-06-12
**Frontend URL:** http://localhost:3650
**Iteration:** 17

## Highlights

### Step 01 — Open the app home page

- **Narration:** This iteration made no visible changes — the tape-reading engine was optimised internally to process dense streams roughly 18 times faster, but every screen, panel, and number looks identical to before. This walkthrough confirms the cockpit still works correctly after that internal work.
- **Action:** Navigate to /
- **Point out:** The ticker input and Watch button appear exactly as before. Nothing on screen changed.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-17/step-01.png

### Step 02 — Type SIM-BUYER into the ticker input

- **Narration:** Entering the simulated buyer-control ticker to start the cockpit watch session, exactly as QA verified.
- **Action:** Type "SIM-BUYER" into "Enter ticker"
- **Point out:** The ticker field accepts input normally.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-17/step-02.png

### Step 03 — Click Watch to launch the cockpit

- **Narration:** Clicking Watch immediately acknowledges the request and navigates to the live cockpit page — the same instant-feedback behaviour that has been working since the beginning.
- **Action:** Click the "Watch" button
- **Point out:** The browser navigates to the SIM-BUYER cockpit and begins populating panels within seconds.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-17/step-03.png

### Step 04 — Cockpit renders all five panels with live content

- **Narration:** After a short warm-up the cockpit fills in: the price chart with its Control marker, the tape-state label, a confidence reading, the observations list, and the event log — all identical to the previous iteration.
- **Action:** Navigate to /watch/SIM-BUYER
- **Point out:** Look for 'Buyer Control' in the state label and a confidence value near 0.90–0.95. The chart canvas should be populated, and the Observations and Event Log panels should each have at least one entry.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-17/step-04.png

### Step 05 — REST endpoint agrees with the cockpit display

- **Narration:** The backend REST endpoint returns the same classification and confidence the cockpit is showing — confirming there is still a single source of truth after the engine refactor.
- **Action:** Navigate to /tape/SIM-BUYER/state
- **Point out:** The JSON response at /tape/SIM-BUYER/state should show buyer_control and a confidence value in the same range as the cockpit (roughly 0.90–0.95). No error fields should be present.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-17/step-05.png
