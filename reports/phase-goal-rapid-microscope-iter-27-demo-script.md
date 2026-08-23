# Demo Script — goal-rapid-microscope-iter-27

**Mode:** record
**Date:** 2026-08-23
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk page

- **Narration:** Navigate to the Desk page, which displays research readiness data and pilot study information.
- **Action:** Navigate to /desk
- **Point out:** The page loads with 'Playbook Signals' as the main heading. Below are collapsible sections for Microscope Readiness, Scout Ledger, and other research tools.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-27/step-01.png

### Step 02 — Expand Microscope Readiness to view corpus data

- **Narration:** Click the Microscope Readiness section to see the corpus totals and readiness figures. This data now loads faster on repeat views thanks to improved caching.
- **Action:** Click "desk-section-expand-microReadiness"
- **Point out:** The section expands to show a 'Corpus Totals' table with values like distinct symbol-days, datasets, RTH minutes, and session-equivalents.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-27/step-02.png

### Step 03 — Scroll to the Referee Registry section

- **Narration:** Scroll down to find the Referee Registry section. This section shows the legacy readiness metric and pilot-study strategy information.
- **Action:** Click "desk-section-expand-refereeRegistry"
- **Point out:** You see section headers for Referee Registry, Referee Adjudications, and Referee Runs. The page structure remains unchanged from previous iterations.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-27/step-03.png

### Step 04 — View the disclosure about the legacy readiness metric  [NEW]

- **Narration:** The Referee Registry now displays a clarification message. This explains that the legacy metric may include withheld Rapid Microscope shards and must not be used as the canonical readiness count.
- **Action:** Click "referee-evidence-seal-aware-caveat-disclosure"
- **Point out:** Inside the Strategy Family block, you see the new disclosure text: 'Legacy Referee readiness metric — seal-unaware in the Rapid Microscope era. It may include withheld/unexposed Rapid-Microscope shards and must not be used as the canonical Rapid-Microscope readiness count.' This text appears beside the Datasets and Trades figures.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-27/step-04.png

### Step 08 — Verify Referee Adjudications is ready

- **Narration:** Expand the Referee Adjudications section. It tracks hypotheses registered for evaluation and remains empty until pilot studies are fully registered.
- **Action:** Click "desk-section-expand-refereeAdjudications"
- **Point out:** The Referee Adjudications section displays 'No hypotheses registered.' This is the expected state for the current test corpus.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-27/step-08.png

## Full tour (text only)

### Step 05 — Expand Scout Ledger to verify pilot studies

- **Narration:** Scroll back up and open the Scout Ledger section. It shows the pilot-study families and their trial variants, now rendered with consolidated internal wiring.
- **Action:** Click "desk-section-expand-scoutLedger"
- **Point out:** The section displays 'Ledger chain verification: ok' followed by pilot-study family rows. Each row shows the family name, root ID, and variants tried.

### Step 06 — Expand Walk-Forward section to verify fold integrity

- **Narration:** Click the Walk-Forward section to view the diagnostic fold results. This section demonstrates the chronological and integrity checks that run during the analysis.
- **Action:** Click "desk-section-expand-walkForward"
- **Point out:** The Walk-Forward section shows fold specifications and verification status. You see the section displays cleanly with no errors.

### Step 07 — Expand Validation Vault to view sealed tranche

- **Narration:** Open the Validation Vault section to see the sealed-at dates and exposure status. This section records which datasets have been sealed for validation.
- **Action:** Click "desk-section-expand-validationVault"
- **Point out:** The Validation Vault shows registered datasets with their sealed status. All sections render correctly with no blank panels or errors.
