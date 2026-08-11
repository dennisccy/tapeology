# Demo Script — goal-playbook-iter-8

**Mode:** record
**Date:** 2026-08-11
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk page

- **Narration:** The Desk page is where traders can see their playbook signals, scan history, and now the evidence view. Let's start there.
- **Action:** Navigate to /desk
- **Point out:** The page loads without errors and shows the Desk section with trading setup signals at the top.
- **Screenshot:** reports/demo/goal-playbook-iter-8/step-01.png

### Step 02 — Scroll to the Playbook Evidence section  [NEW]

- **Narration:** Below the Backscan panel, a new Playbook Evidence section shows the statistical outcomes of every recorded signal. Scroll down to see it.
- **Action:** Click "[data-testid='desk-evidence-cells-table']"
- **Point out:** The Playbook Evidence panel appears below Backscan with a clear heading and disclosure text about what was measured.
- **Screenshot:** reports/demo/goal-playbook-iter-8/step-02.png

### Step 03 — View a well-populated signal cell  [NEW]

- **Narration:** The main table shows setup families (like open-high break and jump-base explosion), their long and short sides, and measurement timeframes. Each cell shows how many signals fired and their median, percentile, and mean returns.
- **Action:** Click "[data-testid='desk-evidence-cells-table'] tbody tr"
- **Point out:** A row with setup 'jbe', side 'long', and measure '5m' shows n=14 signals with real return statistics: median -4%, p25 -7%, p75 6%, mean 2%.
- **Screenshot:** reports/demo/goal-playbook-iter-8/step-03.png

### Step 04 — Find a low-n tagged cell  [NEW]

- **Narration:** Some setups have very few recorded signals. These cells are still shown with their numbers, but tagged with an amber badge so you know the sample size is small.
- **Action:** Click "[data-testid='desk-evidence-cells-table'] tbody tr:has([data-testid*='low'])"
- **Point out:** A row for 'jbe', side 'long', measure '1m' shows n=3 with an amber 'low n' badge beside it, yet the median, p25, p75, and mean values remain visible, not hidden.
- **Screenshot:** reports/demo/goal-playbook-iter-8/step-04.png

### Step 05 — Check the invalidation breaches table  [NEW]

- **Narration:** Below the cells table is a second table showing how many recorded signals breached their invalidation level for each setup, side, and timeframe. This helps you see which setups held their boundaries.
- **Action:** Click "[data-testid='desk-evidence-breach-table'] tbody tr"
- **Point out:** The Invalidation breaches table lists rows like 'capitulation / long / 1h' with Breached and Total counts, for example Breached=14, Total=29.
- **Screenshot:** reports/demo/goal-playbook-iter-8/step-05.png

### Step 06 — Scroll up to Playbook Signals and view a capitulation signal

- **Narration:** Above the Playbook Evidence section, the Playbook Signals area shows individual setups that fired on a given day. Let's look at the capitulation signal for a recorded trading day.
- **Action:** Type "2026-06-22" into "[data-testid='desk-playbook-date-input']"
- **Point out:** The Capitulation row for symbol DECOR is visible. When expanded, it shows 'euphoria recent' — a marker that signals high emotion in the price action at that moment.
- **Screenshot:** reports/demo/goal-playbook-iter-8/step-06.png

### Step 07 — Expand the Capitulation row to see the euphoria marker

- **Narration:** Click on the Capitulation row to expand its detail. The expanded view shows the signal's geometry and context.
- **Action:** Click the "DECOR" button
- **Point out:** The expanded detail shows '67 bar(s) to close' and 'euphoria recent' in the geometry disclosure line, confirming the signal's full characteristics are captured.
- **Screenshot:** reports/demo/goal-playbook-iter-8/step-07.png

### Step 08 — Refresh the page and confirm the evidence data persists

- **Narration:** The Playbook Evidence numbers come from stored records. Refreshing the page shows the same numbers, proving they are read from disk, not regenerated.
- **Action:** Navigate to /desk
- **Point out:** After refreshing, the same low-n tagged cell from step 4 appears with identical values, and the Invalidation breaches table is unchanged.
- **Screenshot:** reports/demo/goal-playbook-iter-8/step-08.png
