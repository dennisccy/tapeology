# Demo Script — goal-rapid-microscope-iter-17

**Mode:** record
**Date:** 2026-08-20
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the research command center

- **Narration:** The Desk page is the hub for all research workflows—corpus readiness, candidate tracking, and validation analysis. This regression test confirms the entire surface works after the backend refactoring this round.
- **Action:** Navigate to /desk
- **Point out:** The page loads cleanly with the heading 'Desk' visible and all research sections ready to expand.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-17/step-01.png

### Step 02 — Check corpus readiness

- **Narration:** The Microscope Readiness section shows diagnostics about the research corpus—symbol-days, distinct datasets, and RTH minutes available. Expanding it verifies the readiness aggregates survived the sealed-verdict module refactoring.
- **Action:** Click "[data-testid="desk-section-expand-microReadiness"]"
- **Point out:** The section expands to show the Corpus Totals table with counts of available data.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-17/step-02.png

### Step 03 — Review the candidate ledger

- **Narration:** The Scout Ledger tracks all registered candidate strategies and their trial results. This confirms the ledger chain verification holds and the scout data remains accessible.
- **Action:** Click "[data-testid="desk-section-expand-scoutLedger"]"
- **Point out:** The section expands showing the chain verification status and the ledger state, whether empty or populated with registered families.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-17/step-03.png

### Step 04 — Inspect walk-forward validation

- **Narration:** The Walk-Forward section shows the fold sequences registered for candidate testing. Each fold ensures chronological evaluation without lookahead, a core protection. This confirms the fence logic is sound.
- **Action:** Click "[data-testid="desk-section-expand-walkForward"]"
- **Point out:** The section expands cleanly, displaying either fold specifications or an honest empty state, with no errors.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-17/step-04.png

### Step 05 — Load the structure and resistance bands

- **Narration:** The Structure page analyzes support and resistance bands for any symbol and timestamp. We navigate there to verify this core analysis surface works independent of the sealed-verdict refactoring.
- **Action:** Navigate to /structure
- **Point out:** The page loads and displays the input fields ready for analysis.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-17/step-05.png

### Step 06 — Watch live market data on the Cockpit

- **Narration:** The Cockpit is where users see live market data in real time. This is the sentinel check that the product's core live-update pipeline still works—our kept-product regression test.
- **Action:** Navigate to /
- **Point out:** The Cockpit page loads with the chart ready and the ticker input waiting. We'll type a simulated ticker and watch it update.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-17/step-06.png

### Step 07 — Enter a simulated ticker and begin watching

- **Narration:** We type a simulated ticker (SIM-BUYER) to start the live tape. The chart should render and the quote data should update in real time.
- **Action:** Type "SIM-BUYER" into "Ticker e.g. SIM-BUYER"
- **Point out:** The live tape activates, showing confidence, quote levels, and recent trades updating continuously.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-17/step-07.png

### Step 08 — Click Watch to activate the feed

- **Narration:** The Watch button starts the simulated feed and renders the live trading surface.
- **Action:** Click the "Watch" button
- **Point out:** Live trading data appears: the confidence level, quote levels, and a tape of recent trades all update continuously with no errors.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-17/step-08.png
