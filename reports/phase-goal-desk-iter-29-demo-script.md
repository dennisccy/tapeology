# Demo Script — goal-desk-iter-29

**Mode:** record
**Date:** 2026-07-31
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk page  [NEW]

- **Narration:** The Desk shows a ranked briefing of the universe at today's date, along with historical ledgers of every operation that built it.
- **Action:** Navigate to /desk
- **Point out:** The Desk page loads with the 'Desk' heading at the top.
- **Screenshot:** reports/demo/goal-desk-iter-29/step-01.png

### Step 02 — Scroll down to see the Screen Runs panel  [NEW]

- **Narration:** At the bottom of the page, below the Index Reconciliation section, a new Screen Runs panel now shows a ledger of every screen computation that was attempted — including runs that reused an already-recorded result, or failed partway.
- **Action:** Click the "Screen Runs" heading
- **Point out:** The Screen Runs section is visible, showing a table with columns for date, run, state, attempted / total, and produced.
- **Screenshot:** reports/demo/goal-desk-iter-29/step-02.png

### Step 03 — Observe the populated Screen Runs ledger  [NEW]

- **Narration:** Each row in the table shows the date the run happened, its run id, the terminal state (done, cancelled, or failed), how many members were actually checked versus the total, and what was produced — a snapshot id, or an honest note if it was reused or produced nothing.
- **Action:** Click "[data-testid='desk-screen-runs-table']"
- **Point out:** The Screen Runs table shows at least one completed run with date, state, member count, and outcome.
- **Screenshot:** reports/demo/goal-desk-iter-29/step-03.png

### Step 04 — Scroll down further to see the Latest run detail block  [NEW]

- **Narration:** Below the Screen Runs table, the 'Latest run' detail block shows additional information about the most recent screen computation — elapsed time, ranked and skipped counts, and on failure, the exact member name and error message.
- **Action:** Click "[data-testid='desk-screen-run-latest-detail']"
- **Point out:** The Latest run detail block is visible with the state, member count, elapsed time, and outcome of the most recent run.
- **Screenshot:** reports/demo/goal-desk-iter-29/step-04.png

## Full tour (text only)

### Step 05 — Scroll back up to see the Run Screen button

- **Narration:** The existing 'Run Screen' button above the Desk briefing is now smarter — if you click it a second time on the same day with unchanged inputs, it short-circuits immediately and records the reuse instead of re-walking all ~101 members.
- **Action:** Click the "Run Screen" button
- **Point out:** The Run Screen button is visible in the middle of the page.

### Step 06 — Observe the ranked briefing table unchanged

- **Narration:** The ranked briefing table above the Run Screen button — showing symbol, wall distance, score, and class — is pixel-identical to before. No new columns, no layout shift, and no horizontal scrollbar at the standard 1440-pixel width.
- **Action:** Click the "Briefing" heading
- **Point out:** The ranked table displays the familiar columns (symbol, side, class, distance, score, coverage, and more) with no horizontal scroll.
