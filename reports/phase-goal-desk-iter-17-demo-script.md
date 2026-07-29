# Demo Script — goal-desk-iter-17

**Mode:** record
**Date:** 2026-07-29
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk page

- **Narration:** We're heading to the Desk page to see the new price disclosure in the ranked briefing table.
- **Action:** Navigate to /desk
- **Point out:** The page loads with a Desk heading and ranked table below the Provenance section.
- **Screenshot:** reports/demo/goal-desk-iter-17/step-01.png

### Step 02 — View the ranked table header — now with the new band column  [NEW]

- **Narration:** The table header has grown from nine columns to ten. The new 'band' column appears last, after 'history', and shows the exact closing price each row's wall sits at.
- **Action:** Click "table[data-testid='desk-screen-rows-table'] th:last-child"
- **Point out:** Scroll the table horizontally if needed to see the rightmost 'band' header cell. The full ten-column order is: symbol, side, class, distance, score, coverage, tick evidence, basis, history, band.
- **Screenshot:** reports/demo/goal-desk-iter-17/step-02.png

### Step 03 — See the BRK-B row's new band cell  [NEW]

- **Narration:** Every ranked row now displays its closing price and band range in the new rightmost cell. On the live store today, all recorded snapshots predate this feature, so this row shows the honest fallback text.
- **Action:** Click "tr[data-symbol='BRK-B'] td[data-testid='desk-row-band']"
- **Point out:** Find the BRK-B row (leftmost symbol cell). Read its rightmost cell (the new band column) — it shows 'close not recorded in this snapshot'. This is the correct state for legacy snapshots.
- **Screenshot:** reports/demo/goal-desk-iter-17/step-03.png

### Step 04 — Hover the BRK-B row to see the updated tooltip  [NEW]

- **Narration:** The row's composite tooltip has been extended with the new close/band detail, placed right after the existing basis and history information, and before the coverage timestamps.
- **Action:** Click "tr[data-symbol='BRK-B'] a"
- **Point out:** Hover over any part of the BRK-B row. The tooltip shows: distance · score · basis · history · 'close not recorded in this snapshot' · coverage windows. The new close detail is positioned between history and the coverage list.
- **Screenshot:** reports/demo/goal-desk-iter-17/step-04.png

### Step 05 — Verify pre-existing columns are unchanged

- **Narration:** The new band column is purely additive — every other column on the BRK-B row keeps its original value and position. Distance still shows 0.00 bps, score still shows 1787.00, and basis and history information are unchanged.
- **Action:** Click "tr[data-symbol='BRK-B']"
- **Point out:** Scan across the BRK-B row: side (support), class (Class A), distance (0.00 bps), score (1787.00), coverage (4 timeframe badges lit), basis, and history all render exactly as they did before this iteration.
- **Screenshot:** reports/demo/goal-desk-iter-17/step-05.png

### Step 06 — Check another row — LIN shows the same pattern

- **Narration:** Scrolling down to find the LIN row confirms the new band column works consistently across all ranked rows. Like BRK-B, it also shows the fallback text because this snapshot predates the feature.
- **Action:** Click "tr[data-symbol='LIN'] td[data-testid='desk-row-band']"
- **Point out:** The LIN row's band cell also reads 'close not recorded in this snapshot'. The distance, score, basis, and history cells match what was recorded before this iteration.
- **Screenshot:** reports/demo/goal-desk-iter-17/step-06.png

### Step 07 — Confirm the skip table was not affected

- **Narration:** The new band column only appears on ranked rows — the skipped members table below deliberately has no band column. This is correct because skipped rows have no distance or band data to disclose.
- **Action:** Click "table"
- **Point out:** Scroll down to the 'Skipped — no bars' section. The skip table has exactly four columns: symbol, reason, coverage, tick evidence. No band column here — this is intentional and working correctly.
- **Screenshot:** reports/demo/goal-desk-iter-17/step-07.png

### Step 08 — Summary — the new band disclosure in action  [NEW]

- **Narration:** The Desk briefing now surfaces the exact closing price and band range for every ranked row, right where it matters on screen. For snapshots computed after this code ships, operators will see real price numbers. For older snapshots like today's store, the honest fallback message appears instead.
- **Action:** Navigate to /desk
- **Point out:** This purely additive column and tooltip detail move 'price is inside the wall' from unrecoverable arithmetic into a visible, legible fact on every row.
- **Screenshot:** reports/demo/goal-desk-iter-17/step-08.png
