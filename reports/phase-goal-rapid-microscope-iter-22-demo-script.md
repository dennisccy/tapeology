# Demo Script — goal-rapid-microscope-iter-22

**Mode:** record
**Date:** 2026-08-21
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk to see research studies

- **Narration:** The Desk displays all research studies that have been screened against the product's historical record. Let's open it to see what screening questions have been answered.
- **Action:** Navigate to /desk
- **Point out:** The Desk page loads with section headers including Scout Ledger and Walk-Forward sections.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-22/step-01.png

### Step 02 — Expand Scout Ledger to see all screened studies

- **Narration:** Scout Ledger holds the trial results for each feature question we've tested. When expanded, it shows every candidate we screened and its recorded decision—survive or killed, with a stated reason.
- **Action:** Click the "Scout Ledger" button
- **Point out:** The Scout Ledger section expands to show trial-row tables organized by family. Multiple families now appear, each one a different screening question.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-22/step-02.png

### Step 03 — View Study 1: range-wall failed aggression  [NEW]

- **Narration:** Study 1 asks: when we see aggressive buying or selling into a price wall, does that aggression—measured by our failed-aggression signal—predict the wall will reject the aggressor? This family shows the screened answer.
- **Action:** Click "[data-testid='scout-family-failed_aggression_score__band_touch__trades_20']"
- **Point out:** The first family block displays Study 1's trial row. Its Feature column reads 'failed_aggression_score / threshold (band_touch)', showing the specific question. The Decision column records whether this candidate survived or was killed.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-22/step-03.png

### Step 04 — View Study 3: capitulation exhaustion  [NEW]

- **Narration:** Study 3 asks: when the playbook detects capitulation—exhaustion of selling interest—does that signal predict rejection? This is the second new screening question now visible in the same ledger.
- **Action:** Click "[data-testid='scout-family-failed_aggression_score__playbook_signal__trades_20']"
- **Point out:** Another family block shows Study 3's trial row. Its Feature reads 'failed_aggression_score / threshold (playbook_signal)', using the same feature name but keyed to a different structure context: playbook signals instead of price bands.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-22/step-04.png

### Step 05 — See the walk-forward floor-check row  [NEW]

- **Narration:** For each screening study, a second row records an honest eligibility check: 'Do we yet have enough independently-verified evidence to trust this answer?' Both new studies show that the product has zero confirmed independent trading sessions on record. The honest answer is killed_insufficient_n—never a fabricated pass.
- **Action:** Click "details"
- **Point out:** Below each family's screen-decision row, a floor-check row shows em-dashes in Feature and Horizon columns, and 'killed_insufficient_n' in the Decision column. This is the product saying: the screening question is real, the answer is recorded, but we do not yet have enough confirmed independent evidence.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-22/step-05.png

### Step 06 — Expand Walk-Forward section to confirm eligibility

- **Narration:** The Walk-Forward section summarizes the walk-forward eligibility picture across all screened studies. Let's expand it to confirm that Studies 1 and 3 appear here too—proof the screening flows through the full chain.
- **Action:** Click the "Walk-Forward" button
- **Point out:** The Walk-Forward section expands below Scout Ledger. It mirrors the same families and their eligibility status, confirming the walk-forward checks were recorded.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-22/step-06.png

### Step 07 — View the Graduation surface—the immutable ledger

- **Narration:** The Graduation endpoint records sealed readings—an immutable ledger of what has already passed sufficiently tight filters to graduate to the next stage. This is the record of confirmed evidence, never backdated, never altered.
- **Action:** Navigate to /research/desk/micro/graduation
- **Point out:** The Graduation endpoint displays JSON with families, their sealed readings, verdicts, and observation counts. This is proof that the backend maintains an immutable chain of what has been verified and what remains exploratory.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-22/step-07.png
