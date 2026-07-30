# Demo Script — goal-desk-iter-23

**Mode:** record
**Date:** 2026-07-30
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the desk screen

- **Narration:** We're starting at the ranked briefing page that shows you, at a glance, which trading walls are worth tracking across your universe. This is where you make most of your decisions.
- **Action:** Navigate to /desk
- **Point out:** The ranked table with 100 rows, one for each symbol in the universe. The page loads the screen snapshot and your briefing — the ranked list by wall strength and distance.
- **Screenshot:** reports/demo/goal-desk-iter-23/step-01.png

### Step 02 — Scroll right to the new levels column  [NEW]

- **Narration:** Every ranked row now shows you how thick its wall actually is — not just where it sits and how close it is, but how many price levels built that wall. Scroll to the right to see it.
- **Action:** Click the "opposite" columnheader
- **Point out:** The new `levels` column appears to the right of `opposite`. It shows a tally string like '155 levels · 1d 68 · 1h 57 · 4h 19 · 1w 11', describing how many levels the wall was built from at each timeframe.
- **Screenshot:** reports/demo/goal-desk-iter-23/step-02.png

### Step 03 — Look at a high-evidence row  [NEW]

- **Narration:** Some walls are built from hundreds of levels across multiple timeframes. When you see a wall with 50+ or 100+ levels, you know it's confirmed by many touches across days, hours, and minutes.
- **Action:** Click "[data-testid='desk-row-levels']"
- **Point out:** A row with a high level count (e.g., 155 levels, or higher). Notice how the per-timeframe split tells you whether most of the levels come from daily touches (1d), intraday touches (1h/4h/1w), or a mix.
- **Screenshot:** reports/demo/goal-desk-iter-23/step-03.png

### Step 04 — Spot the round-number badge  [NEW]

- **Narration:** Some walls sit at round-number prices — like 100.00 or 50.00. When a wall is built at a round number, a small badge shows you that detail right on the ranked list. No need to drill into the details page.
- **Action:** Click "tradable-band-round-number"
- **Point out:** On some rows (not all), look for a small bordered badge reading 'round number' right next to the level tally. This wall is at a psychologically significant price level.
- **Screenshot:** reports/demo/goal-desk-iter-23/step-04.png

### Step 05 — Compare low-evidence and high-evidence rows  [NEW]

- **Narration:** Two rows might read identical at every other column — 'support · Class A · 0.00 bps' — but their walls can be completely different. One might be a single touch, another might be 600+ levels. Now you can see that difference right here on the ranked list.
- **Action:** Click "[data-testid='desk-row-levels']"
- **Point out:** Scroll vertically or left to compare multiple rows' levels columns. Find one row with just a few levels (2, 3, 5) and another with dozens. The briefing now closes the gap — you don't need to drill into the structure page to understand wall thickness.
- **Screenshot:** reports/demo/goal-desk-iter-23/step-05.png

## Full tour (text only)

### Step 06 — Open the screen history to show legacy behavior

- **Narration:** Screens computed before this feature was built show an honest message: 'composition not recorded in this snapshot'. The system never guesses or backfills. You see exactly what was recorded when the snapshot was taken.
- **Action:** Click the "Screen History" button
- **Point out:** If you select an older screen from the history, its rows will show 'composition not recorded in this snapshot' in the levels column. No fake data, ever.
