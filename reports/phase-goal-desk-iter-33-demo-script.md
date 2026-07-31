# Demo Script — goal-desk-iter-33

**Mode:** record
**Date:** 2026-07-31
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk page

- **Narration:** The Desk page shows all recorded runs and results from screening and updating bar history. Let's start there.
- **Action:** Navigate to /desk
- **Point out:** The Desk page loads with the heading and main content panels visible.
- **Screenshot:** reports/demo/goal-desk-iter-33/step-01.png

### Step 02 — View the top-up run with corrected reach disclosure  [NEW]

- **Narration:** The top-up run section now shows the date each symbol's frozen history reached accurately. The newest date and the earlier-pairs list now agree with each other.
- **Action:** Click "desk-topup-run-latest-reach"
- **Point out:** The Top-up Runs section displays the reach line (newest recorded reach with count) and a short list of pairs recorded on earlier dates. The list is now capped to show only a sample, not hundreds of rows.
- **Screenshot:** reports/demo/goal-desk-iter-33/step-02.png

### Step 03 — Scroll to see the earlier-pairs list  [NEW]

- **Narration:** Below the reach line, earlier pairs are listed — now capped to a manageable length so the page stays readable at standard viewport sizes.
- **Action:** Click "desk-topup-run-latest-reach-earlier"
- **Point out:** The earlier-pairs section shows a short table with pairs and their recorded dates. The count in the heading states the true total, so you know how many exist even if not all are shown.
- **Screenshot:** reports/demo/goal-desk-iter-33/step-03.png

### Step 04 — View the ranked briefing table with window disclosure

- **Narration:** The ranked briefing shows support and resistance zones ranked by strength. Each row also states how many bars the vendor was asked to fetch.
- **Action:** Click "desk-topup-run-latest-outcomes"
- **Point out:** The table displays each symbol's band, the closest opposite wall, levels count, and the history span. The window-basis line shows how many pairs asked for tail vs. full-lookback data.
- **Screenshot:** reports/demo/goal-desk-iter-33/step-04.png

### Step 05 — Check the briefing fits without horizontal scroll

- **Narration:** The disclosure is legible at standard widths. No sideways scrolling is needed to read any row.
- **Action:** Click "desk-screen-rows-table"
- **Point out:** At 1440×900, all columns are visible and readable. The table layout is compact yet clear.
- **Screenshot:** reports/demo/goal-desk-iter-33/step-05.png

## Full tour (text only)

### Step 06 — View the Screen Runs history table

- **Narration:** The history panel shows every screen run that has been performed on this desk. This append-only ledger is untouched.
- **Action:** Click "desk-history-table"
- **Point out:** The table lists multiple screen run records with dates and outcomes. The system preserves the full history of operations.

### Step 07 — View the provenance block — configuration and bar store state

- **Narration:** The provenance section confirms the configuration fingerprint and bar store signature, so you know exactly what build and data you're looking at.
- **Action:** Click "desk-provenance"
- **Point out:** The block shows the config fingerprint and bar-store signature. These values identify the exact build and data set in use.
