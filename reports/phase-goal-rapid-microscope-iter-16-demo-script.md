# Demo Script — goal-rapid-microscope-iter-16

**Mode:** record
**Date:** 2026-08-20
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk page

- **Narration:** The Desk page loads cleanly with all collapsible sections ready. Each section starts collapsed—expand them to view content.
- **Action:** Navigate to /desk
- **Point out:** The 'Desk' heading and collapsed section headers are visible, zero console errors.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-16/step-01.png

### Step 02 — Expand Microscope Readiness—shows testid retained in all states

- **Narration:** Microscope Readiness expands showing 2 tick shards (symbol PG, session 2026-06-09) and corpus totals. This panel's DOM identifier is now retained whether loading, unavailable, or fully loaded.
- **Action:** Click the "Microscope Readiness" button
- **Point out:** Shows 'Distinct symbol-days: 1', 'Distinct datasets: 2', and 2 PG rows in Legacy Tick Shards.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-16/step-02.png

### Step 03 — Expand Scout Ledger—shows defensive degradation

- **Narration:** Scout Ledger expands showing 'No candidates ledgered'—the honest empty state. The table now degrades gracefully: if any row were malformed, only that cell renders a placeholder instead of blanking the entire page.
- **Action:** Click the "Scout Ledger" button
- **Point out:** Shows 'No candidates ledgered' and 'No scout runs recorded yet', and the 'Run Screen' button is visible but not clicked.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-16/step-03.png

### Step 04 — Expand Walk-Forward section—unaffected regression check

- **Narration:** Walk-Forward expands showing no fold specs registered. This section is unaffected by this round's work, confirming changes stayed isolated.
- **Action:** Click the "Walk-Forward" button
- **Point out:** Shows 'No fold specs registered' and 'No walk-forward sequences run'.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-16/step-04.png

### Step 05 — Expand Validation Vault—read-only state unchanged

- **Narration:** Validation Vault expands showing no shards recorded and no universes registered. This section is read-only by design, and this round did not alter it.
- **Action:** Click the "Validation Vault" button
- **Point out:** Shows 'No shards recorded' and 'No universes registered'—the correct read-only empty state.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-16/step-05.png

### Step 06 — Expand Referee Registry—all sections load cleanly

- **Narration:** Referee Registry (plus Referee Adjudications and Referee Runs) expand without errors, showing real content. All Desk sections remain stable and unaffected.
- **Action:** Click the "Referee Registry" button
- **Point out:** Referee Registry expands with content and zero console errors, confirming the entire Desk page is resilient.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-16/step-06.png

### Step 07 — Navigate to Structure page

- **Narration:** The Structure page loads without error. This page is unaffected by this round's work—included to confirm changes stayed isolated.
- **Action:** Navigate to /structure
- **Point out:** Structure page loads with Symbol and As-of date input fields ready.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-16/step-07.png

### Step 08 — Enter AAPL and load Tradable Map

- **Narration:** Entering AAPL and the as-of date (2026-06-22 16:00:00 ET), then clicking Load, renders the Tradable Map with exactly 10 bands. This confirms the Structure page's data pipeline is unaffected and stable.
- **Action:** Type "AAPL" into the "Symbol" field
- **Point out:** The Tradable Map displays 10 band rows (5 resistance, 5 support), with the first resistance at 300.11–302.2 marked round-number.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-16/step-08.png

## Full tour (text only)

### Step 09 — Fill as-of date and load

- **Narration:** The as-of date field accepts the timestamp. Once submitted, the Tradable Map data loads immediately.
- **Action:** Type "2026-06-22 16:00:00" into the "As-of (ET)" field
- **Point out:** Date field shows '2026-06-22 16:00:00'.

### Step 10 — Click Load to render Tradable Map

- **Narration:** The Load button fetches and displays all 10 Tradable Map bands immediately, confirming the load logic is unaffected.
- **Action:** Click the "Load" button
- **Point out:** Tradable Map renders 10 rows, comparison dropdown is present, no error.

### Step 11 — Watch Cockpit live tape update

- **Narration:** The Cockpit page shows the live tape updating for SIM-BUYER in Simulated mode. Chart and tape are unaffected, confirming the round's backend and Desk changes stayed isolated.
- **Action:** Navigate to /
- **Point out:** Live tape shows 'Buyer Control' with confidence and bid/ask updating between reads, confirming genuine live updates.
