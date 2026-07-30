# Demo Script — goal-desk-iter-25

**Mode:** record
**Date:** 2026-07-30
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the desk screen

- **Narration:** The desk screen shows your complete ranked briefing — every wall worth tracking, ordered by strength and distance. Let's look at how all the information fits on one page.
- **Action:** Navigate to /desk
- **Point out:** The ranked table loads with 100 rows, one for each symbol in the universe. You can see the first few columns: rank, symbol, side, class, distance, and score.
- **Screenshot:** reports/demo/goal-desk-iter-25/step-01.png

### Step 02 — View the complete row — every column legible  [NEW]

- **Narration:** The page layout has been tuned so every column fits without needing to scroll sideways. That means you can see the wall composition, price range, and opposite wall all in one glance.
- **Action:** Click "tr[data-symbol="BRK-B"] [data-testid="desk-row-levels"]"
- **Point out:** Notice that the table stays within the viewport width. All 13 columns are visible: rank, symbol, side, class, distance, score, coverage badges, basis, history, band, opposite, and levels. No horizontal scrollbar.
- **Screenshot:** reports/demo/goal-desk-iter-25/step-02.png

### Step 03 — See a thick wall — many levels across timeframes  [NEW]

- **Narration:** Some walls are built from over a hundred price levels. The tally shows you how many levels contributed at each timeframe: daily, hourly, weekly, and 4-hour. A wall with 155 levels is heavily confirmed.
- **Action:** Click "tr[data-symbol="BRK-B"] [data-testid="desk-row-opposite"]"
- **Point out:** The first row (BRK-B) shows '155 · 1d 68 · 1h 57 · 1w 11 · 4h 19' in the levels column. That means 155 total levels: 68 from daily touches, 57 from hourly, and so on. Each dot separates the counts.
- **Screenshot:** reports/demo/goal-desk-iter-25/step-03.png

### Step 04 — Check the opposite wall distance

- **Narration:** The opposite column tells you where the nearest wall sits on the other side of price. If you're trading near a support, knowing where the resistance is helps you plan your exit.
- **Action:** Click "tr[data-symbol="AMT"] [data-testid="desk-row-levels"]"
- **Point out:** For BRK-B, the opposite wall is 'resistance · Class A · 497.20–500.67 · 0.40 bps'. That's 0.40 basis points away. The class badge tells you it's the same quality as the support wall you're looking at.
- **Screenshot:** reports/demo/goal-desk-iter-25/step-04.png

### Step 05 — Compare thin and thick walls side by side  [NEW]

- **Narration:** Not all walls are equal. Some are built from just a handful of levels — thin walls that might be noise. See how you can compare them without scrolling? The layout lets you read multiple walls at once.
- **Action:** Click "tr[data-symbol="MSFT"] [data-testid="desk-row-levels"]"
- **Point out:** Rank 13 (AMT) shows just '5 · 1d 3 · 1h 1 · 4h 1'. That's a thin wall — only 5 levels total, and just 3 on the daily chart. By keeping all columns visible, you can instantly compare wall thickness across the whole ranked list.
- **Screenshot:** reports/demo/goal-desk-iter-25/step-05.png

### Step 08 — Return to the latest screen

- **Narration:** You're now back at the latest screen with all the current wall composition data. This briefing is your single source of truth for wall strength, distance, price, and thickness across your entire universe.
- **Action:** Navigate to /desk
- **Point out:** The desk page is fully loaded with the latest screen. Every row shows rank, symbol, class, distance, score, coverage, basis, history, band price range, opposite wall distance, and wall composition — all on screen at once, no scrolling.
- **Screenshot:** reports/demo/goal-desk-iter-25/step-08.png

## Full tour (text only)

### Step 06 — Look for the round-number badge  [NEW]

- **Narration:** Some walls sit at psychologically important prices like 100.00 or 300.00. When that happens, a small badge appears right on the ranked list. No need to drill into details — you see it immediately.
- **Action:** Click "tradable-band-round-number"
- **Point out:** Look for a small bordered badge labeled 'round number'. Not every row has one, but when a wall is at a round price, the badge shows you right here on the briefing. A wall at 300.00 might be more sticky than one at 299.37.

### Step 07 — Check screen history for honest legacy data

- **Narration:** Older snapshots don't have the wall composition recorded. Rather than guessing, the system shows you the honest truth: 'composition not recorded in this snapshot'. This way you always know what data you're working with.
- **Action:** Click the "Screen History" button
- **Point out:** Open the Screen History and select an older screen. Its levels column will say 'composition not recorded in this snapshot' instead of a number. That's honest — the wall composition wasn't computed when that snapshot was taken.
