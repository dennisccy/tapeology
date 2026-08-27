# Demo Script — goal-hypothesis-foundry-iter-5

**Mode:** record
**Date:** 2026-08-27
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Desk page loads with Hypothesis Foundry panel

- **Narration:** The Desk page is the operations center for research data. The Hypothesis Foundry panel contains research subsections ready to explore.
- **Action:** Navigate to /desk
- **Point out:** The Hypothesis Foundry section is visible and ready to expand.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-5/step-01.png

### Step 02 — Hypothesis Foundry panel expands with five subsections  [NEW]

- **Narration:** The panel header shows the Source registry hash—now displaying a real, committed epoch identifier instead of a placeholder value.
- **Action:** Click the "Hypothesis Foundry" button
- **Point out:** The Source registry hash field is populated with a real committed value, and five subsection headers are ready to explore.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-5/step-02.png

### Step 03 — Sources/Compiler shows complete fixture metadata  [NEW]

- **Narration:** The Sources subsection now displays three new fields on every fixture record. Both variants of the alias-family example appear as separate entries, each with full metadata.
- **Action:** Click the "Sources / Compiler" button
- **Point out:** Each fixture shows Operative formula refs, Superseded fields, and Aliases/lineage ids. Notice both fixture-variant-a and fixture-variant-b are now visible as distinct rows.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-5/step-03.png

### Step 04 — Hermetic Oracles displays kill-type mapping and sampling metrics  [NEW]

- **Narration:** Hermetic Oracles now shows how outcome labels map to their internal foundry states. A Best-of-N disclosure line reports sampling details.
- **Action:** Click the "Hermetic Oracles" button
- **Point out:** The kill-type mapping pairs each outcome (fragile, survive, insufficient, etc.) with its real diagnostic state. The best-of-N line shows n_variants_tried and the decision threshold_bps.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-5/step-04.png

### Step 05 — Epoch/Manifest subsection shows the real committed epoch  [NEW]

- **Narration:** This new subsection is the iteration's main achievement: the era's first real, Git-frozen research epoch with an emerald banner marking it as production data.
- **Action:** Click the "Epoch / Manifest" button
- **Point out:** The 'Real Epoch — not a fixture' banner uses emerald/green color, visually distinct from the amber banners on fixture sections. The status confirms 'Committed — Git-visible pre-outcome barrier crossed.'
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-5/step-05.png

### Step 06 — Interpreter Fixtures subsection still renders correctly

- **Narration:** Prior-iteration subsections remain stable. Interpreter Fixtures shows the expected hermetic fixture banner and scenario rows—confirming earlier work still passes.
- **Action:** Click the "Interpreter Fixtures" button
- **Point out:** The amber 'Hermetic Fixture — not the real epoch' banner and the fixture scenario rows are intact, showing no regression in earlier iterations.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-5/step-06.png

### Step 07 — Cockpit page loads normally

- **Narration:** The Foundry changes are isolated to /desk. The Cockpit page loads with all controls and charts responsive, confirming no cross-page regressions.
- **Action:** Navigate to /
- **Point out:** The navigation, ticker watch form, and example content all render correctly. The Hypothesis Foundry work didn't affect the main trading interface.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-5/step-07.png

### Step 08 — Structure page loads normally

- **Narration:** The Structure analysis page also works without issue, showing all panels are responsive. This confirms the iteration introduced no regressions.
- **Action:** Navigate to /structure
- **Point out:** The Tradable Map, Case Studies, and Edge Report sections all load as expected, with no errors or broken functionality.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-5/step-08.png
