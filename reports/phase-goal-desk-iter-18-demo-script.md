# Demo Script — goal-desk-iter-18

**Mode:** record
**Date:** 2026-07-29
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk page  [NEW]

- **Narration:** We're visiting the /desk page to see the new disclosure features this iteration adds.
- **Action:** Navigate to /desk
- **Point out:** The page loads with a 'Desk' heading and a short description about the screen.
- **Screenshot:** reports/demo/goal-desk-iter-18/step-01.png

### Step 02 — Scroll the ranked table to see the new 'opposite' column  [NEW]

- **Narration:** The table now has eleven columns instead of ten. The new rightmost 'opposite' column reveals information that was previously invisible.
- **Action:** Click the element
- **Point out:** The header row shows all eleven columns: symbol, side, class, distance, score, coverage, tick evidence, basis, history, band, and the new 'opposite' column at the far right.
- **Screenshot:** reports/demo/goal-desk-iter-18/step-02.png

### Step 03 — Examine the top-ranked row (BRK-B)  [NEW]

- **Narration:** Looking at the first ranked row, BRK-B ranks on a support wall at 0.00 bps with a high score of 1787. But every row now discloses: what's the nearest wall on the OTHER side of price?
- **Action:** Click "tr[data-symbol='BRK-B']"
- **Point out:** The BRK-B row shows its existing columns unchanged: support, Class A, 0.00 bps, score 1787, and the band it selected. The new 'opposite' column appears at the far right.
- **Screenshot:** reports/demo/goal-desk-iter-18/step-03.png

### Step 04 — Hover over a row to see the new tooltip line  [NEW]

- **Narration:** When you hover over any ranked row, the drill-in tooltip now includes one more piece of information: how many candidate walls of each class the row's displayed wall was chosen from.
- **Action:** Click "tr[data-symbol='BRK-B'] a"
- **Point out:** The composite tooltip shows the row's distance, score, basis, history, band, and now also the 'bands by class' count breakdown at the end before the coverage timestamps.
- **Screenshot:** reports/demo/goal-desk-iter-18/step-04.png

### Step 05 — Scroll through the table to see multiple rows  [NEW]

- **Narration:** Every ranked row on this page was recorded before this feature existed, so they all show the honest fallback text: 'opposite wall not recorded in this snapshot'. This is the correct behavior—the data simply wasn't captured when these rows were recorded.
- **Action:** Click "[data-testid='desk-screen-rows-table']"
- **Point out:** Every visible row's 'opposite' column reads exactly 'opposite wall not recorded in this snapshot' because these legacy snapshots predate the feature.
- **Screenshot:** reports/demo/goal-desk-iter-18/step-05.png

### Step 07 — Review the column headers one more time  [NEW]

- **Narration:** The new eleven-column table design is purely additive—every existing column (symbol, side, class, distance, score, coverage, tick evidence, basis, history, band) remains exactly as it was, and the new 'opposite' column adds the dimension that was previously invisible.
- **Action:** Navigate to /desk
- **Point out:** All eleven header cells are visible, in order. The 'opposite' column is the rightmost header, revealing a data point that multiplies the value of every ranked row.
- **Screenshot:** reports/demo/goal-desk-iter-18/step-07.png

## Full tour (text only)

### Step 06 — Confirm the skip table remains unchanged

- **Narration:** The Skipped Members section below still shows only four columns, as it should—a skipped member was never ranked, so it has no opposite wall to disclose.
- **Action:** Click "Skipped"
- **Point out:** Scroll down to see the 'Skipped' sections. Their tables show only the original four columns: symbol, reason, coverage, and tick evidence.
