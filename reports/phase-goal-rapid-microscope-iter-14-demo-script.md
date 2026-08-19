# Demo Script — goal-rapid-microscope-iter-14

**Mode:** record
**Date:** 2026-08-19
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open /desk to view all sections  [NEW]

- **Narration:** The Desk page now shows three new sections below Microscope Readiness. Each is collapsed (arrow points right). Let's expand them to see how ideas move through screening, testing, and validation.
- **Action:** Navigate to /desk
- **Point out:** You see four section headers in order: Microscope Readiness, Scout Ledger, Walk-Forward, Validation Vault. Each arrow points right (collapsed).
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-14/step-01.png

### Step 02 — Expand Scout Ledger to see the screening record  [NEW]

- **Narration:** Scout Ledger records every candidate idea that gets tested. Today it's empty—no ideas have been screened yet. Below that, Run History shows when screening runs happened.
- **Action:** Click the "Scout Ledger" button
- **Point out:** Scout Ledger opens. You see 'Ledger chain verification: ok', then 'No candidates ledgered.' (the honest empty state), then 'No scout runs recorded yet.' The enabled 'Run Screen' button sits below—we won't click it to avoid starting a long computation.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-14/step-02.png

### Step 03 — Expand Walk-Forward to see diagnostic test sequences  [NEW]

- **Narration:** Walk-Forward tests ideas against data they haven't seen before, in time order. Today one sequence exists. You can see the fold results and whether it passed or failed.
- **Action:** Click the "Walk-Forward" button
- **Point out:** Walk-Forward opens. You see 'Ledger chain verification: ok', then Fold Specs, then a sequence with its test results. The verdict line says whether it passed or was refused (and why).
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-14/step-03.png

### Step 04 — Expand Validation Vault to see the read-only record  [NEW]

- **Narration:** Validation Vault holds data sealed away from research—untouched data to test a finished idea against. Today it's empty; no data has been sealed yet. This section is read-only; there are no controls to change anything here.
- **Action:** Click the "Validation Vault" button
- **Point out:** Validation Vault opens. Two chain-verification lines appear: 'Shard ledger chain verification: ok' and 'Universe ledger chain verification: ok'. Below: 'No shards recorded.' and 'No universes registered.' No buttons anywhere—the section is read-only.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-14/step-04.png

### Step 05 — Verify Microscope Readiness section was unaffected

- **Narration:** Microscope Readiness sits above the three new sections. It still shows what it always has: the corpus facts (12 symbol-days, 18 datasets) and readiness metrics.
- **Action:** Click the "Microscope Readiness" button
- **Point out:** Microscope Readiness opens and shows its tables unchanged. The three new sections sit cleanly below with no visual disruption.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-14/step-05.png

## Full tour (text only)

### Step 06 — Navigate to /structure to check the other pages

- **Narration:** The Structure page shows the tradable map for the corpus. This page didn't change—all the new work went only to /desk.
- **Action:** Navigate to /structure
- **Point out:** /structure loads without error. The Tradable Map and comparison dropdown are visible.

### Step 07 — Navigate to Cockpit to confirm the main page stayed the same

- **Narration:** The Cockpit shows the live tape chart. This page also stayed the same—all changes went to /desk.
- **Action:** Navigate to /
- **Point out:** The Cockpit loads and the chart renders. No errors.
