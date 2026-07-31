# Demo Script — goal-desk-iter-34

**Mode:** record
**Date:** 2026-07-31
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk briefing page

- **Narration:** We're looking at the top-up runs panel on the Desk page, where operators track the universe snapshots and bar history that power support and resistance analysis.
- **Action:** Navigate to /desk
- **Point out:** The Desk page loads with the Top-up Runs table showing recorded runs, their states, and how many pairs were successfully handled.
- **Screenshot:** reports/demo/goal-desk-iter-34/step-01.png

### Step 02 — Scroll to the latest run detail  [NEW]

- **Narration:** Each top-up run records the latest date our frozen store can demonstrate history for, called the recorded reach. For pairs recorded earlier than that reach date, the page now shows exactly when they were recorded.
- **Action:** Click "[data-testid='desk-topup-run-latest-detail']"
- **Point out:** The latest run detail section displays the newest recorded reach date and a list of pairs recorded on earlier dates, with the dates matching exactly as printed.
- **Screenshot:** reports/demo/goal-desk-iter-34/step-02.png

### Step 03 — Observe the fixed reach line  [NEW]

- **Narration:** The reach line now correctly states the date all pairs reach, using calendar-day precision. This date and the dates in the earlier-pairs list below never overlap anymore.
- **Action:** Click the "newest recorded reach" heading
- **Point out:** The 'newest recorded reach' line reads a single calendar date. Every row below it in 'Pairs recorded earlier' shows an earlier date — they never contradict each other.
- **Screenshot:** reports/demo/goal-desk-iter-34/step-03.png

### Step 04 — Check the honest disclosure cap  [NEW]

- **Narration:** When a run has more than 20 pairs recorded earlier, the page now shows a plain, honest statement: 'showing X of Y', so you know the list was shortened and by exactly how much.
- **Action:** Click "[data-testid='desk-topup-run-latest-reach-earlier-cap']"
- **Point out:** Below the 'Pairs recorded earlier (N)' heading, a muted line reads 'showing 20 of 101', disclosing that 20 rows are displayed out of 101 total earlier pairs.
- **Screenshot:** reports/demo/goal-desk-iter-34/step-04.png

### Step 05 — Verify exactly 20 rows render  [NEW]

- **Narration:** The earlier-pairs list is now capped at 20 rows for readability. No matter the true total, you'll never scroll through hundreds of rows; the heading always tells you the real count.
- **Action:** Click "[data-testid='desk-topup-run-latest-reach-earlier-row']:first-of-type"
- **Point out:** The list under 'Pairs recorded earlier' displays exactly 20 symbol/timeframe/date rows. Each row shows a consistent earlier date, never matching the newest recorded reach date.
- **Screenshot:** reports/demo/goal-desk-iter-34/step-05.png

### Step 06 — Confirm the table column width is unchanged

- **Narration:** The fix only touched the display logic for reach disclosure and the earlier-pairs list. The main Top-up Runs summary table keeps its original five columns at their original widths.
- **Action:** Click "[data-testid='desk-topup-runs-table']"
- **Point out:** Scroll back up to the summary table. The columns 'date', 'run', 'state', 'attempted / total', and 'universe snapshot' are all present with no new columns added.
- **Screenshot:** reports/demo/goal-desk-iter-34/step-06.png

## Full tour (text only)

### Step 07 — Navigate to Cockpit to check adjacent pages

- **Narration:** The Cockpit page shows the live trading dashboard with historical bars and support/resistance analysis. This page and the Structure page are completely unaffected by the reach-disclosure fix.
- **Action:** Click the "Cockpit" link
- **Point out:** Cockpit page loads without errors, showing the live chart and any open positions.

### Step 08 — Navigate to Structure to verify no regression

- **Narration:** The Structure page serves the tradable-map chart and level/zone details. This page continues to work as before — the fix was scoped only to the Desk page's reach disclosure.
- **Action:** Click the "Structure" link
- **Point out:** Structure page loads with the tradable-map chart and level/zone information visible.
