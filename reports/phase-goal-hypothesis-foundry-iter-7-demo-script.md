# Demo Script — goal-hypothesis-foundry-iter-7

**Mode:** record
**Date:** 2026-08-27
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk

- **Narration:** Go to the Desk page to see your research panels.
- **Action:** Navigate to /desk
- **Point out:** The Desk page displays your research panels, including Hypothesis Foundry.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-7/step-01.png

### Step 02 — Check the Foundry era

- **Narration:** Expand the Foundry section to see the current research era. It opened as a new era, and the old automatic loop is now stopped.
- **Action:** Click "[data-testid="desk-section-expand-hypothesisFoundry"]"
- **Point out:** The current era is hypothesis-foundry (active). The previous era, rapid-microscope, is closed. Backend status is shown below.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-7/step-02.png

### Step 03 — Review source specifications

- **Narration:** Expand Sources. Each source compiles into a specification without reading outcomes first. This proves no bias shapes the specs.
- **Action:** Click "[data-testid="desk-section-expand-foundry-sources-compiler-section"]"
- **Point out:** All sources are listed with their types and specifications. The system confirms outcome-blind compilation.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-7/step-03.png

### Step 04 — Check interpretation fidelity

- **Narration:** Expand Interpreter. The system interprets sources while keeping Scout's original decisions intact.
- **Action:** Click "[data-testid="desk-section-expand-foundry-interpreter-fixtures-section"]"
- **Point out:** Each interpreted source matches Scout's original work. Timing and direction are preserved exactly.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-7/step-04.png

### Step 05 — Verify integrity and freeze

- **Narration:** Expand Freeze and Integrity. The system owns the candidate count and prevents late changes after the epoch is frozen.
- **Action:** Click "[data-testid="desk-section-expand-foundry-freeze-integrity-section"]"
- **Point out:** The Freeze section shows the family count, lock status, and refusal of late insertion attempts.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-7/step-05.png

### Step 06 — Test all decision logic

- **Narration:** Expand Hermetic Oracles. The complete system is tested with all outcome types to ensure it handles null results, planted effects, and edge cases.
- **Action:** Click "[data-testid="desk-section-expand-foundry-hermetic-oracles-section"]"
- **Point out:** Every outcome type is tested. The system counts candidates correctly and survives all safety tests.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-7/step-06.png

### Step 07 — Confirm epoch committed

- **Narration:** Expand Epoch and Manifest. The real epoch is created and saved without reading any outcomes. All sources are recorded with their disposition.
- **Action:** Click "[data-testid="desk-section-expand-foundry-epoch-manifest-section"]"
- **Point out:** The epoch is committed and saved. All required sources are listed with their status. The outcome-access count is zero.
- **Screenshot:** reports/demo/goal-hypothesis-foundry-iter-7/step-07.png
