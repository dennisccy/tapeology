# Demo Script — goal-desk-iter-31

**Mode:** record
**Date:** 2026-07-31
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk page

- **Narration:** The Desk page is where screen runs are recorded and reviewed. Let's load it to see what's new.
- **Action:** Navigate to /desk
- **Point out:** The Desk page loads with a heading and several panels.
- **Screenshot:** reports/demo/goal-desk-iter-31/step-01.png

### Step 02 — View the latest screen run — it's a reused one  [NEW]

- **Narration:** A reused run means the system recognized the same universe and screen state, so it didn't need to walk through the members again. This is a good outcome — it just says so honestly.
- **Action:** Click the "Latest run" heading
- **Point out:** The latest run shows 'reused screen-...' with the outcome text. Notice: no amber warning below it, and no counts line — the fix suppresses those misleading signals for reused runs.
- **Screenshot:** reports/demo/goal-desk-iter-31/step-02.png

### Step 03 — See the Screen Runs history table — it still shows every run

- **Narration:** The history table keeps a full record of every screen run the system has performed. This append-only ledger is untouched by our fix.
- **Action:** Click "[data-testid='desk-screen-runs-table']"
- **Point out:** The table shows multiple rows, including at least one full walk (101 / 101) and the reused runs. Every record is preserved.
- **Screenshot:** reports/demo/goal-desk-iter-31/step-03.png

## Full tour (text only)

### Step 04 — Navigate to Structure from the ledger

- **Narration:** The ledger panel offers a drill-in link to the Structure page, where support and resistance levels are visualized in detail.
- **Action:** Click the "Structure" link
- **Point out:** Clicking the Structure link takes you to the full levels view with zones and bars.

### Step 05 — Return to Desk via navigation

- **Narration:** The top navigation makes it easy to jump between pages. Desk is now a first-class citizen in the app.
- **Action:** Click the "Desk" link
- **Point out:** Clicking the Desk link brings you back, and the page is still responsive and shows the same honest data.
