# Demo Script — goal-rapid-microscope-iter-24

**Mode:** record
**Date:** 2026-08-23
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk

- **Narration:** The Desk page shows sealed research in motion through four stages: readiness, screening, validation, and exposure. This iteration tightens the privacy of one timestamp.
- **Action:** Navigate to /desk
- **Point out:** The page title 'Playbook Signals' and the section headers: Microscope Readiness, Scout Ledger, Walk-Forward, Validation Vault.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-24/step-01.png

### Step 02 — Scout Ledger — screening decisions recorded

- **Narration:** The Scout Ledger shows every study the engine proposed and screened. This iteration seeds a pilot study row so you can see the recorded decision.
- **Action:** Click "[data-testid='desk-section-expand-scoutLedger']"
- **Point out:** The pilot study 'failed_aggression_score__playbook_signal__trades_20' with its decision and reason for rejection.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-24/step-02.png

### Step 03 — Walk-Forward — results confirmed on new data

- **Narration:** Walk-Forward re-tests each study's results against fresh out-of-sample data. The rows show whether each meets the verification floor.
- **Action:** Click "[data-testid='desk-section-expand-walkForward']"
- **Point out:** The Walk-Forward section with its floor-check rows and verification status for each study.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-24/step-03.png

### Step 04 — Validation Vault — sealed research and exposure timeline

- **Narration:** The Validation Vault tracks sealed research shards through three release stages: sealed, assigned, and exposed. Each row shows when it was sealed, its current state, and disclosure dates.
- **Action:** Click "[data-testid='desk-section-expand-validationVault']"
- **Point out:** The table with columns for Universe, Size bucket, Sealed at, State, Assigned at, Exposed at. This iteration shows only the calendar date in the Sealed at column, narrowing the privacy of sealing timestamp.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-24/step-04.png
