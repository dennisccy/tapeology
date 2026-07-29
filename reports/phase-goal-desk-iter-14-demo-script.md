# Demo Script — goal-desk-iter-14

**Mode:** record
**Date:** 2026-07-29
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the desk

- **Narration:** The desk shows your holdings ranked by how close they sit to key price levels. Each row has small coverage badges showing which timeframes have price data stored.
- **Action:** Navigate to /desk
- **Point out:** The desk page loads with the briefing ranked table and small coverage badges next to each symbol.
- **Screenshot:** reports/demo/goal-desk-iter-14/step-01.png

### Step 02 — See the index reconciliation panel before any run  [NEW]

- **Narration:** Scrolling to the bottom, you see a new Index Reconciliation panel. It is empty right now because no reconciliation has ever run. One stock in the briefing above has a dark coverage badge—the system thinks there is no data for that timeframe, even though data might be stored.
- **Action:** Navigate to /desk
- **Point out:** The Index Reconciliation section reads 'No reconciliation run recorded yet.' Scroll up to find a stock with a dark (gray) coverage badge showing no data.
- **Screenshot:** reports/demo/goal-desk-iter-14/step-02.png

### Step 03 — Click Reconcile Index to repair the internal list  [NEW]

- **Narration:** Clicking Reconcile Index checks the system's internal file list against the real stored files, repairing any mismatches. The operation is fast and needs no network calls.
- **Action:** Click the "Reconcile Index" button
- **Point out:** The Reconcile Index button briefly shows it is working, then returns to normal within seconds.
- **Screenshot:** reports/demo/goal-desk-iter-14/step-03.png

### Step 04 — Read the repair results  [NEW]

- **Narration:** The panel now shows the reconciliation run's results: how many price-bar files exist on disk, how many rows the index had before the repair, and how many after. The Drift Before list shows which stock-timeframe pairs were missing from the index.
- **Action:** Click "[data-testid='desk-reconcile-run-latest-detail']"
- **Point out:** The run finished with state: done. The rows-indexed count shows before and after numbers, and the Drift Before list names the pairs that were missing.
- **Screenshot:** reports/demo/goal-desk-iter-14/step-04.png

### Step 05 — Run a fresh screen to capture the fixed coverage  [NEW]

- **Narration:** Now that the index is repaired, you run a fresh screen. This records a new briefing with the corrected coverage badges based on what you just fixed.
- **Action:** Click the "Run Screen" button
- **Point out:** The outcome line confirms 'Recorded a new snapshot' — not a reused one. A genuinely new snapshot was added.
- **Screenshot:** reports/demo/goal-desk-iter-14/step-05.png

### Step 06 — See the coverage badge now lit  [NEW]

- **Narration:** Scroll back up to the briefing table and look at the same stock that had a dark badge before. After the reconciliation and the new screen run, that badge is now lit, matching its neighbors. The system now correctly recognizes the data.
- **Action:** Navigate to /desk
- **Point out:** The coverage badge that was dark is now colored (lit), showing the data is confirmed. It matches the other badges on that row.
- **Screenshot:** reports/demo/goal-desk-iter-14/step-06.png

### Step 07 — Check that older records stayed unchanged  [NEW]

- **Narration:** To prove the system never rewrites old records, scroll to Screen History and click a date before today. That older screen's own coverage badge for the same pair still shows dark — it was never changed. Only a new snapshot was added.
- **Action:** Click the "Latest" button
- **Point out:** A banner confirms 'Viewing the recorded screen for [date] — not the latest.' The same badge that is now lit in today's screen still shows dark in the older screen.
- **Screenshot:** reports/demo/goal-desk-iter-14/step-07.png

### Step 08 — Coverage is now independently verifiable  [NEW]

- **Narration:** The cycle is complete. You triggered a reconciliation, the system repaired its internal index, you ran a fresh screen, and the stuck coverage badge is now lit. The old screen record stayed intact, proving the repair was additive, never destructive. Your desk now shows coverage you can trust.
- **Action:** Click the "Index Reconciliation" region
- **Point out:** The desk displays a full history of reconciliation runs and their results. You can run reconciliations whenever you need to keep coverage accurate.
- **Screenshot:** reports/demo/goal-desk-iter-14/step-08.png
