# Demo Script — goal-playbook-iter-11

**Mode:** record
**Date:** 2026-08-12
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Playbook Signals screen

- **Narration:** The Playbook surface lets you scan historical sessions for recorded trading patterns. Here we land on the /desk page where all eight signal families are ready to detect.
- **Action:** Navigate to /desk
- **Point out:** The Playbook Signals panel with eight setup types: opening range, continuation, climax, and range families.
- **Screenshot:** reports/demo/goal-playbook-iter-11/step-01.png

### Step 02 — Show the invalid-date error state with colored border  [NEW]

- **Narration:** When you type an invalid date, the input shows an error border in amber and displays a helpful message. This makes it clear what needs to be fixed.
- **Action:** Type "not-a-date" into "desk-playbook-date-input"
- **Point out:** The date input border turns amber to indicate an error; an error message appears below it.
- **Screenshot:** reports/demo/goal-playbook-iter-11/step-02.png

### Step 03 — Clear the error with a valid session date

- **Narration:** Once you enter a valid date from a recorded session, the border returns to normal. Now you can run the playbook scanner.
- **Action:** Type "2026-06-22" into "desk-playbook-date-input"
- **Point out:** The input border changes back to the default color; the error clears.
- **Screenshot:** reports/demo/goal-playbook-iter-11/step-03.png

### Step 04 — Run the Playbook scanner

- **Narration:** Click Run Playbook to scan that session for all eight signal families. The detector checks opening ranges, continuations, climaxes, and range trades.
- **Action:** Click "desk-playbook-compute-button"
- **Point out:** The scanner runs and loads signals found in that session, organized by family.
- **Screenshot:** reports/demo/goal-playbook-iter-11/step-04.png

### Step 05 — View the signal families detected

- **Narration:** The Playbook Signals results show all patterns found: opening-range breaks, JBE continuations, cup-and-handles, climax reversals, and range trades. Each signal includes exact entry prices and invalidation levels.
- **Action:** Click the "Evidence" tab
- **Point out:** The signal table displays detected patterns with their entry prices, invalidation levels, and timing for each pattern type.
- **Screenshot:** reports/demo/goal-playbook-iter-11/step-05.png

### Step 06 — Review evidence distributions  [NEW]

- **Narration:** The Evidence tab shows statistical distributions of how each signal family performed historically. You see the count of signals found and minimum-sample guards for honest reporting. The data is served by read-only tools that proxy the backend securely.
- **Action:** Click the "Signals" tab
- **Point out:** Distribution data for each setup family with sample counts and performance metrics. The signature badge confirms the data contract is verified.
- **Screenshot:** reports/demo/goal-playbook-iter-11/step-06.png

### Step 07 — All playbook families working end to end

- **Narration:** All eight pre-registered signal families work end to end: opening ranges, JBE, DBI, cup-and-handle, capitulation, euphoria, range trades, and double tops. Evidence is always honestly reported with sample-size guards.
- **Action:** Navigate to /desk
- **Point out:** The complete Playbook Signals surface with all signal families ready to detect and evidence honestly disclosed.
- **Screenshot:** reports/demo/goal-playbook-iter-11/step-07.png
