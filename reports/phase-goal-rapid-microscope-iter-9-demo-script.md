# Demo Script — goal-rapid-microscope-iter-9

**Mode:** record
**Date:** 2026-08-18
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Cockpit home page loads

- **Narration:** The home page shows the cockpit with live market tape and chart, ready to monitor any ticker.
- **Action:** Navigate to /
- **Point out:** Notice the 'No ticker watched' message, indicating no active ticker is being monitored yet. The page is fully loaded with the tape viewer and chart components.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-9/step-01.png

### Step 03 — Watch ticker live activity

- **Narration:** Clicking Watch activates the live tape for this symbol, showing real-time market events and dominance patterns.
- **Action:** Click the "Watch" button
- **Point out:** The 'Buyer Control' tape state has loaded, displaying the live market activity for the symbol. The Tape State panel shows the current dominance, and recent trades, quotes, and events appear below.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-9/step-03.png

### Step 04 — Structure analysis page

- **Narration:** The Structure page provides tools to analyze support and resistance levels for any symbol on any date.
- **Action:** Navigate to /structure
- **Point out:** The Tradable Map form is ready with input fields for symbol, date, and other parameters. The page is fully loaded and ready to analyze market structures.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-9/step-04.png

### Step 07 — Load Tradable Map

- **Narration:** Computing the Tradable Map displays the support and resistance bands, showing exactly where the market traded in compact, actionable zones.
- **Action:** Click the element
- **Point out:** The pinned S/R band 300.11–302.2 appears for AAPL on that date. This band represents real, verified historical levels where the market clustered—the Tradable Map distills noise away to show only meaningful bands.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-9/step-07.png

### Step 08 — Desk operations hub

- **Narration:** The Desk page is the central command center, showing playbook signals, screen runs, referee status, and the microscope readiness report.
- **Action:** Navigate to /desk
- **Point out:** The page displays multiple collapsible sections: Playbook Signals, Top-up Runs, Index Reconciliation, Screen Runs, Playbook Evidence, Referee Registry, Referee Adjudications, Referee Runs, and Microscope Readiness. Each section can be expanded to show detailed operational data.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-9/step-08.png

### Step 09 — Microscope Readiness: corpus status

- **Narration:** Expanding Microscope Readiness shows the current corpus state including dataset counts, symbol-date coverage, session equivalents, and the registry of all recorded tick shards.
- **Action:** Click the element
- **Point out:** The Corpus Totals table shows 1 distinct symbol-day and 2 distinct datasets (the fixture rig's seeded PG shards). The Legacy Tick Shards table lists both with full metadata: Feed, Window, Trade/Quote counts, Bytes, Coverage gaps, Fallback fraction, Checksums, Split provenance (hand_assigned), and Exposure state (exploratory). Importantly, no 'Validation Vault' section appears anywhere on this page—it is built but not yet wired into the UI.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-9/step-09.png

### Step 10 — Referee Registry: frozen foundation

- **Narration:** The Referee Registry section displays the frozen configuration fingerprint and other operational metadata, proving the research foundation is stable.
- **Action:** Click the element
- **Point out:** The fingerprint 08e471b10130e1e2 matches the expected value. This frozen fingerprint proves no configuration fields were added or changed this iteration, maintaining the integrity of the research platform.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-9/step-10.png

### Step 11 — Referee Adjudications: no hypotheses yet

- **Narration:** The Referee Adjudications section tracks evaluation hypotheses and judgments in the research ledger.
- **Action:** Click the element
- **Point out:** The section shows the honest empty state: 'No hypotheses registered.' This is the correct state for a fresh environment before any hypotheses are formally registered.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-9/step-11.png

## Full tour (text only)

### Step 02 — Enter ticker symbol

- **Narration:** Type a ticker symbol to start monitoring live market activity.
- **Action:** Type "SIM-BUYER" into the "Ticker" field

### Step 05 — Enter symbol for structure analysis

- **Narration:** Enter the ticker symbol to analyze its support and resistance levels.
- **Action:** Type "AAPL" into the "Structure symbol" field

### Step 06 — Set analysis date

- **Narration:** Set the date and time for the analysis. This date (June 22, 2026 at 5 PM ET) has been pre-analyzed with real support and resistance levels.
- **Action:** Type "2026-06-22 17:00:00" into the element

### Step 12 — Referee Runs: evaluation history

- **Narration:** The Referee Runs section records the ledger of completed evaluation runs and their outcomes.
- **Action:** Click the element

### Step 13 — Playbook Evidence: recorded signals

- **Narration:** The Playbook Evidence section shows the detected trading signals for each setup, filtered by date.
- **Action:** Click the element

### Step 14 — Filter by date

- **Narration:** Type a date to see signals recorded on that day.
- **Action:** Type "2026-06-22" into the element
