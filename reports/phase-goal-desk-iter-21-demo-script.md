# Demo Script — goal-desk-iter-21

**Mode:** record
**Date:** 2026-07-30
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the ranked briefing page

- **Narration:** The desk page shows a ranked briefing of support and resistance levels. Each row displays the symbol, the wall's price range, and how it was measured.
- **Action:** Navigate to /desk
- **Point out:** You see the ranked briefing with columns for symbol, distance, coverage, bar, band, and opposite wall. The table scrolls to show 100 rows of levels sorted by distance.
- **Screenshot:** reports/demo/goal-desk-iter-21/step-01.png

### Step 02 — See the band column: wall price range and close  [NEW]

- **Narration:** Each row in the band column shows the wall's recorded price range and the closing price it was measured from. If the close sits inside the wall's range, it is at the level right now. If it sits outside, the wall is stale.
- **Action:** Click the "Desk" heading
- **Point out:** Look at the band column: you see entries like 'band 488.50–490.91 · close 490.91', where the close is right at the top of the band. Lower down you see 'band 508.79–512.31 · close 508.77', where the close is below the band's bottom—the wall is above price. Both show in the same view.
- **Screenshot:** reports/demo/goal-desk-iter-21/step-02.png

### Step 03 — See the opposite wall column: the nearest level on the other side  [NEW]

- **Narration:** The opposite column shows the nearest wall on the other side of the current price. It names whether it is support or resistance, which A/B/C class, the price range, and how many basis points away it sits.
- **Action:** Click the "Desk" heading
- **Point out:** You see entries like 'opposite resistance A 490.97–494.39 · 1.22 bps'—a very close opposing wall, just over 1 basis point away. Further down you see 'opposite resistance A 108.69–109.45 · 1128.29 bps'—a wall more than 1,000 basis points away. Both are legible in one frame, showing the range from near to far walls.
- **Screenshot:** reports/demo/goal-desk-iter-21/step-03.png
