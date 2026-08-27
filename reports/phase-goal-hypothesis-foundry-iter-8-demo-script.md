# Demo Script — goal-hypothesis-foundry-iter-8

**Mode:** record
**Date:** 2026-08-27
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Navigate to the Desk

- **Narration:** Open the Desk page to access hypothesis testing results.
- **Action:** Navigate to /desk
- **Point out:** The Desk page loads with the navigation bar and Hypothesis Foundry panel visible.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-8/step-01.png

### Step 02 — Expand the Hypothesis Foundry Panel

- **Narration:** Click the Hypothesis Foundry section header to reveal the panel with epoch analysis.
- **Action:** Click the element
- **Point out:** The panel expands, showing the era-open baseline header and available subsections.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-8/step-02.png

### Step 03 — View the New Final Summary  [NEW]

- **Narration:** Click to expand Final Summary. This new subsection shows the epoch's complete state at a glance—source counts, family count, freeze status, and more.
- **Action:** Click the element
- **Point out:** The Final Summary section displays source disposition counts summing to 11, family and variant counts of zero, and freeze integrity status showing green.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-8/step-03.png

### Step 04 — Explore Source Canonical Provenance  [NEW]

- **Narration:** Click on a source record to expand and view its full canonical provenance. You can see the mechanism statement, audit note, direction derivation, and quoted text spans that justified its disposition.
- **Action:** Click "Canonical provenance"
- **Point out:** The source detail expands showing mechanism, audit note, direction derivation, comparator derivation, threshold provenance, and source hash for this record.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-8/step-04.png

### Step 05 — Verify Sources/Compiler Still Works

- **Narration:** Expand the Sources/Compiler section to confirm that the new Final Summary feature did not break existing functionality.
- **Action:** Click the element
- **Point out:** The Sources/Compiler section renders correctly, showing that the six pre-existing subsections remain intact.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-8/step-05.png

### Step 06 — Check All 11 Source Rows Render

- **Narration:** Expand Epoch/Manifest to verify all 11 real source-disposition rows still render unchanged and intact from the real committed registry.
- **Action:** Click the element
- **Point out:** The section lists all 11 source records with their disposition badges and lineage references displayed correctly.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-8/step-06.png

### Step 07 — Verify Freeze/Integrity Section

- **Narration:** Expand Freeze/Integrity to show that the freeze status and integrity checks render correctly alongside the new Final Summary.
- **Action:** Click the element
- **Point out:** The Freeze/Integrity subsection displays the freeze-set validation and hash pinning information without errors.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-8/step-07.png

### Step 08 — Confirm Runner/Checkpoint Verdicts

- **Narration:** Expand Runner/Checkpoint to verify the freeze integrity verdict and exhaust completion state match what Final Summary displays. This confirms cross-subsection consistency.
- **Action:** Click the element
- **Point out:** The Runner/Checkpoint section shows the freeze integrity verdict as green and the exhaust completion status, matching the values shown in Final Summary.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-8/step-08.png
