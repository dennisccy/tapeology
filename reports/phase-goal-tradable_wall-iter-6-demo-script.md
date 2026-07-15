# Demo Script — goal-tradable_wall-iter-6

**Mode:** record
**Date:** 2026-07-15
**Frontend URL:** http://localhost:3301
**Iteration:** 6

## Highlights

### Step 02 — Open the Structure page  [NEW]

- **Narration:** Click into Structure, home of the app's price-structure research tools.
- **Action:** Click the "Structure" link
- **Point out:** The page now opens to a simple prompt instead of a wall of numbers — pick a symbol and a moment in time to see its map.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-6/step-02.png

### Step 05 — See the short list of zones that matter  [NEW]

- **Narration:** Click Load. Instead of a giant list of every minor price level, the page now shows a short, ranked list of the handful of zones that actually matter for this stock.
- **Action:** Click the "Load" button
- **Point out:** Exactly ten rows appear, with the zone around $300 to $302 near the top, marked Class A and flagged as a round number.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-6/step-05.png

### Step 06 — Peek behind the curtain  [NEW]

- **Narration:** Curious how this page used to look? Click Show raw levels to bring back the original, longer view.
- **Action:** Click the "Show raw levels" button
- **Point out:** The original chart and level list reappear completely unchanged — now tucked one click away instead of being the only option.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-6/step-06.png

### Step 08 — Open a real example  [NEW]

- **Narration:** Click one of the AAPL rows from June 22, 2026 — a day price actually tested that same top zone.
- **Action:** Click "tr[data-testid="case-studies-row"]:has-text("2026-06-22")"
- **Point out:** The example opens to show exactly what happened: the touch was rejected, and price moved lower afterward across both tracked follow-up windows.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-6/step-08.png

### Step 09 — An honest too-soon-to-know case  [NEW]

- **Narration:** Now click the most recent AAPL example instead, the one marked truncated horizon.
- **Action:** Click "tr[data-testid="case-studies-row"]:has-text("2026-07-13")"
- **Point out:** Rather than guessing at an outcome, the app says plainly that not enough time has passed yet to know how this one turned out.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-6/step-09.png

### Step 10 — Check the honest scorecard  [NEW]

- **Narration:** Further down, the new Edge Report compares three trading approaches side by side.
- **Action:** Click "edge-report-register"
- **Point out:** Right now it states plainly that there isn't qualifying trade data yet, rather than making up a result.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-6/step-10.png

### Step 11 — Confirm nothing else moved

- **Narration:** Scroll further still, and the strategy list and current champion are exactly where they've always worked.
- **Action:** Click "champion-summary"
- **Point out:** Fetching real prices from Yahoo Finance, the strategy list, and the head-to-head comparison tool are all still here, just moved below the new sections.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-6/step-11.png

## Full tour (text only)

### Step 01 — Open Tapeology

- **Narration:** Start on the Cockpit, the app's home screen for watching a stock's simulated tape.
- **Action:** Navigate to /
- **Point out:** The navigation bar across the top, with Structure as one of its five pages.

### Step 03 — Pick a stock

- **Narration:** Type AAPL into the Symbol field.
- **Action:** Type "AAPL" into the "Structure symbol" field
- **Point out:** The Symbol field now reads AAPL.

### Step 04 — Pick a moment in time

- **Narration:** Enter an as-of time from the middle of a real trading session — everything shown afterward is built only from data available up to that exact moment, never a peek into the future.
- **Action:** Type "2026-06-22T15:00:00Z" into the "As-of (UTC, ISO-8601)" field
- **Point out:** The As-of field now reads the chosen date and time.

### Step 07 — Search real examples

- **Narration:** Scroll down to Case Studies and narrow its history to one stock by typing into its Symbol box.
- **Action:** Type "AAPL" into "case-studies-filter-symbol"
- **Point out:** The list narrows down to AAPL's own history of price touching a mapped zone.
