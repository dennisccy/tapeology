# Demo Script — goal-hypothesis-foundry-iter-6

**Mode:** record
**Date:** 2026-08-27
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk page

- **Narration:** The Desk page is where operators monitor the Hypothesis Foundry state. We'll start by navigating there.
- **Action:** Navigate to /desk
- **Point out:** The page loads with several sections, including the Hypothesis Foundry panel at the bottom.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-6/step-01.png

### Step 02 — Expand the Hypothesis Foundry section

- **Narration:** The Hypothesis Foundry panel starts collapsed. We click the section header to expand it and see all subsections.
- **Action:** Click the "▸Hypothesis Foundry" button
- **Point out:** The panel expands to reveal six subsections: Sources / Compiler, Interpreter Fixtures, Freeze / Integrity, Hermetic Oracles, Epoch / Manifest, and the new Runner / Checkpoint.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-6/step-02.png

### Step 03 — Expand the Epoch / Manifest subsection

- **Narration:** We click Epoch / Manifest to confirm the sibling subsection still works as before—this regression check proves nothing broke.
- **Action:** Click the "Epoch / Manifest" button
- **Point out:** The Epoch / Manifest subsection shows the frozen epoch ID and the 'Real Epoch — not a fixture' green banner.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-6/step-03.png

### Step 04 — Expand the new Runner / Checkpoint subsection  [NEW]

- **Narration:** This is the new subsection for this iteration. It shows the real exhaust pass state after running the Foundry CLI.
- **Action:** Click the "Runner / Checkpoint" button
- **Point out:** The subsection expands to show the checkpoint details, including the first-read lock timestamp, the manifest hash, and the exhaust completion status.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-6/step-04.png

### Step 05 — Verify the first-read lock timestamp  [NEW]

- **Narration:** The first-read lock marks the moment when the exhaust pass definitively evaluated the frozen epoch. This timestamp proves the lock was recorded.
- **Action:** Click "First-read lock recorded at:"
- **Point out:** The 'First-read lock recorded at:' line shows the exact UTC timestamp (2026-08-27T06:55:51.071173Z), confirming the exhaust run completed.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-6/step-05.png

### Step 06 — Check the checkpoint count and protected-read census  [NEW]

- **Narration:** The checkpoint line shows how many candidates reached a final state. The protected-read count, displayed in green, proves no off-limits data was touched.
- **Action:** Click "Protected/withheld/sealed reads:"
- **Point out:** The 'Checkpoint: 0 of 0' and 'Protected/withheld/sealed reads: 0' lines confirm the honest, zero-candidate result for this frozen epoch.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-6/step-06.png

### Step 07 — View the completion message and freeze integrity status  [NEW]

- **Narration:** The bottom of the subsection shows the exhaust-complete verdict and the freeze integrity verdict. For this epoch, completion is honest and vacuous—zero candidates ever existed.
- **Action:** Click "Exhaust complete"
- **Point out:** The 'Exhaust complete' message plainly states the result: 'zero FROZEN_READY variants this epoch — an honest, vacuous completion.' The 'Freeze integrity: green' line confirms all integrity checks passed.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-6/step-07.png

### Step 08 — Verify sibling subsections remain unchanged

- **Narration:** We check the Sources / Compiler subsection to confirm no other subsections were accidentally modified. This regression test ensures the change was purely additive.
- **Action:** Click the "Sources / Compiler" button
- **Point out:** The Sources / Compiler subsection still displays 'Hashes match — outcome-blind compilation proven.' exactly as before.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-6/step-08.png
