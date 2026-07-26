# Demo Script — goal-desk-iter-6

**Mode:** record
**Date:** 2026-07-26
**Frontend URL:** http://localhost:3301
**Iteration:** 6

## Highlights

### Step 01 — Open the Desk

- **Narration:** This is the Desk, a daily briefing. It lists the symbols sitting closest to a real support or resistance wall, plus a history of every past briefing.
- **Action:** Navigate to /desk
- **Point out:** Four panels: Provenance, Briefing, Skipped Members, and Screen History.
- **Screenshot:** reports/demo/goal-desk-iter-6/step-01.png

### Step 02 — Look back at a past day's briefing  [NEW]

- **Narration:** Click any date in the history list and the page instantly shows exactly what was recorded that day. Nothing is recalculated — it is a plain read-back of the saved snapshot.
- **Action:** Click "[data-testid="desk-history-row"][data-screen-date="2026-06-22"]"
- **Point out:** A banner confirms you are now viewing 2026-06-22, not today's screen.
- **Screenshot:** reports/demo/goal-desk-iter-6/step-02.png

### Step 05 — Jump from a briefing row straight into its chart  [NEW]

- **Narration:** Click any symbol in the Briefing list and it opens the deeper chart page already filled in and already loaded. There is no retyping the symbol or the date.
- **Action:** Click "[data-testid="desk-screen-row"][data-symbol="AAPL"]"
- **Point out:** The chart page opens with AAPL's real wall already drawn, at the band 298.02–300.1001.
- **Screenshot:** reports/demo/goal-desk-iter-6/step-05.png

### Step 08 — A skipped symbol still opens honestly  [NEW]

- **Narration:** Skipped symbols are clickable too. Clicking one still opens the deeper chart page, but it tells the truth: no price history was recorded for it, instead of showing a made-up chart.
- **Action:** Click "[data-testid="desk-skip-row"][data-symbol="ABBV"]"
- **Point out:** "No bar series recorded for ABBV." appears instead of a fabricated chart.
- **Screenshot:** reports/demo/goal-desk-iter-6/step-08.png

### Step 09 — Opening the chart page on its own still works the old way

- **Narration:** Opened directly, with no symbol or date already picked, the chart page looks exactly as it always has. Both fields stay empty until you choose a symbol and press Load.
- **Action:** Navigate to /structure
- **Point out:** Both fields are empty and the page waits for you, unchanged from before this update.
- **Screenshot:** reports/demo/goal-desk-iter-6/step-09.png

## Full tour (text only)

### Step 03 — Snap back to today with one click  [NEW]

- **Narration:** A "Latest" button shows up whenever you are looking at an older day. Click it and the page returns to today's screen right away, with no waiting.
- **Action:** Click the "Latest" button
- **Point out:** The banner disappears and today's briefing is back on screen.

### Step 04 — Select that past day again  [NEW]

- **Narration:** Selecting 2026-06-22 once more sets up the next step: jumping from one of its rows straight into a deeper chart.
- **Action:** Click "[data-testid="desk-history-row"][data-screen-date="2026-06-22"]"
- **Point out:** The 2026-06-22 banner is back.

### Step 06 — Back to the Desk

- **Narration:** Returning to the Desk to show the other kind of row: one that was skipped because it had no recorded price history.
- **Action:** Navigate to /desk
- **Point out:** The Desk is back to its normal view.

### Step 07 — Select the same past day once more  [NEW]

- **Narration:** Selecting 2026-06-22 again brings back the list of symbols that were skipped that day.
- **Action:** Click "[data-testid="desk-history-row"][data-screen-date="2026-06-22"]"
- **Point out:** The 91 skipped symbols are listed again, including ABBV.

### Step 10 — The old manual way still works too

- **Narration:** Typing a symbol by hand still works exactly as before. This update only added new shortcuts — it did not change the original way of using the page.
- **Action:** Type "AAPL" into the "Symbol" field
- **Point out:** "AAPL" is now typed into the Symbol field.

### Step 11 — Fill in today's date with one click

- **Narration:** A "Today" button fills in the as-of date for you, saving a manual date entry.
- **Action:** Click the "Today" button
- **Point out:** The as-of field now shows today's date.

### Step 12 — Load the chart by hand

- **Narration:** Pressing Load fills in the tradable-level table exactly as it always has, proving the original manual workflow is untouched by this update.
- **Action:** Click the "Load" button
- **Point out:** The bands table appears, same as always.
