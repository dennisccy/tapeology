# Demo Script — goal-playbook-iter-4

**Mode:** record
**Date:** 2026-08-11
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk page

- **Narration:** The Desk is your intraday setup scanner. It loads with the Playbook Signals section, ready to analyze recorded trading sessions.
- **Action:** Navigate to /desk
- **Point out:** The Playbook Signals panel is visible with a date input field and a Run Playbook button.
- **Screenshot:** reports/demo/goal-playbook-iter-4/step-01.png

### Step 04 — View the signals table with new setup types  [NEW]

- **Narration:** The table displays every setup detected in the session. You now see three new setup types — Jump-Base Explosion, Drop-Base Implosion, and Cup and Handle — each with its own chip label in the setup column.
- **Action:** Click "desk-playbook-table"
- **Point out:** The signals table shows rows for LADDER (Jump-Base Explosion), DBI1 (Drop-Base Implosion), and CUP1 (Cup and Handle) with distinct setup chips.
- **Screenshot:** reports/demo/goal-playbook-iter-4/step-04.png

### Step 05 — Expand a Jump-Base Explosion signal  [NEW]

- **Narration:** JBE shows a tight consolidation base followed by a sharp upside move. Click the row to see the base width in MBR, the jump size, and the bar where it broke.
- **Action:** Click "[data-testid='desk-playbook-signal-row']:has-text('Jump-Base Explosion')"
- **Point out:** The detail panel expands, showing the JBE-specific geometry line: base width, bar count, jump size, breakout slot, and base quality notes.
- **Screenshot:** reports/demo/goal-playbook-iter-4/step-05.png

### Step 06 — Expand a Drop-Base Implosion signal  [NEW]

- **Narration:** DBI is the short-side mirror of JBE. The same geometry fields show base and jump magnitudes, direction-flipped for a downside move.
- **Action:** Click "[data-testid='desk-playbook-signal-row']:has-text('Drop-Base Implosion')"
- **Point out:** The detail panel shows the DBI geometry line with base width, bar count, jump size for the short side.
- **Screenshot:** reports/demo/goal-playbook-iter-4/step-06.png

### Step 07 — Expand a Cup and Handle signal  [NEW]

- **Narration:** Cup and Handle shows a different geometry: a rounded cup pullback, then a smaller handle retrace, then a breakout. The disclosure includes cup bar count, depth in MBR, handle retrace and duration fractions, and three relative volume medians.
- **Action:** Click "[data-testid='desk-playbook-signal-row']:has-text('Cup and Handle')"
- **Point out:** The detail panel displays Cup and Handle geometry: cup bars and depth, handle retrace fraction, handle duration, and the three RVOL medians describing volume distribution.
- **Screenshot:** reports/demo/goal-playbook-iter-4/step-07.png

## Full tour (text only)

### Step 02 — Enter a session date

- **Narration:** The Playbook analyzes one trading session at a time. We'll examine a session from June 22, 2026, which fired all three new setup types.
- **Action:** Type "2026-06-22" into "desk-playbook-date-input"
- **Point out:** The date field now contains the session date.

### Step 03 — Run the Playbook

- **Narration:** Click to scan the session for signals. The Playbook detects setup patterns using the pre-registered rules in the specification.
- **Action:** Click the "Run Playbook" button
- **Point out:** The button shows Computing… briefly, then returns to Run Playbook with a completion message.
