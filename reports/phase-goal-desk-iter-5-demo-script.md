# Demo Script — goal-desk-iter-5

**Mode:** record
**Date:** 2026-07-26
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open Tapeology

- **Narration:** Here's the app's home screen, the live Cockpit. The navigation bar across the top now leads to all three of the product's pages.
- **Action:** Navigate to /
- **Point out:** The top nav reads Cockpit, Structure, Desk — the third page, Desk, is what this update is about.
- **Screenshot:** reports/demo/goal-desk-iter-5/step-01.png

### Step 05 — Load the tradable map

- **Narration:** Clicking Load draws the chart and highlights the nearest tradable support/resistance band.
- **Action:** Click "structure-load-button"
- **Point out:** The candlestick chart and the highlighted price band, right where the team expects it — proof this page still works exactly as before.
- **Screenshot:** reports/demo/goal-desk-iter-5/step-05.png

### Step 06 — Open the Desk

- **Narration:** Now the page this update is all about: Desk, the operator's daily briefing. It pulls together every stock in the tracked universe into one ranked list.
- **Action:** Click the "Desk" link
- **Point out:** The Provenance panel, showing exactly which snapshot of the stock universe and which pricing data this briefing was built from — so anyone can tell two briefings apart or confirm they're identical.
- **Screenshot:** reports/demo/goal-desk-iter-5/step-06.png

### Step 07 — See today's ranked briefing

- **Narration:** Below the provenance panel sits the actual briefing: every stock with enough price history is ranked by how close it sits to a real support or resistance level.
- **Action:** Click "[data-testid="desk-screen-rows-table"]"
- **Point out:** Each row shows the side (support or resistance), a letter grade for the level's strength, the distance to it, and a badge for every timeframe of price data behind it.
- **Screenshot:** reports/demo/goal-desk-iter-5/step-07.png

### Step 08 — See what got skipped, honestly

- **Narration:** Any stock without enough price history isn't hidden or silently dropped — it's listed in its own clearly labeled group, so nothing is quietly missing from the picture.
- **Action:** Click "[data-testid="desk-skipped-section"]"
- **Point out:** The "Skipped" section, grouped by the exact reason each stock couldn't be ranked.
- **Screenshot:** reports/demo/goal-desk-iter-5/step-08.png

## Full tour (text only)

### Step 02 — Open Structure

- **Narration:** Jumping over to the Structure page, where the app maps out a stock's support and resistance levels.
- **Action:** Click the "Structure" link
- **Point out:** The Symbol and As-of fields, ready for a lookup.

### Step 03 — Look up a stock

- **Narration:** Typing in a symbol — AAPL — to pull up its price map.
- **Action:** Type "AAPL" into the "Structure symbol" field

### Step 04 — Pick a point in time

- **Narration:** And a specific moment in time to look at — this is the same pinned example the team uses to prove the chart still works correctly after every change.
- **Action:** Type "2026-06-22T21:00:00Z" into "structure-as-of-input"
