# Demo Script — goal-rapid-microscope-iter-28

**Mode:** record
**Date:** 2026-08-23
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk page

- **Narration:** The Desk page is the command center for all research journeys. It brings together playbook signals, microscope readiness, scout ledger, walk-forward results, and the referee registry—everything you need to evaluate a live strategy.
- **Action:** Navigate to /desk
- **Point out:** The page title 'Desk' at the top and 'Playbook Signals' section visible below.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-28/step-01.png

### Step 02 — Expand the Microscope Readiness section

- **Narration:** The Microscope Readiness section shows the corpus totals and pilot-study floor status. This is where we verify the era transition is working and the sealed tranche has been recorded correctly.
- **Action:** Click "[data-testid="desk-section-expand-microReadiness"]"
- **Point out:** The Microscope Readiness section expands and you can see the corpus totals and tranche data.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-28/step-02.png

### Step 03 — Expand the Referee Registry section

- **Narration:** The Referee Registry holds the evidence metrics and strategy families. A new disclosure has been added here to clarify an important limit in the legacy readiness count.
- **Action:** Click "[data-testid="desk-section-expand-refereeRegistry"]"
- **Point out:** The Referee Registry section expands to reveal its subsections.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-28/step-03.png

### Step 04 — Locate the new seal-unaware caveat in Strategy Family  [NEW]

- **Narration:** Inside the Referee Registry's Evidence Readiness section, the Strategy Family block now includes a disclosure: the legacy readiness metric is seal-unaware in the Rapid Microscope era. It may include withheld shards and must not be used as the canonical readiness count. This protects against misinterpreting the numbers.
- **Action:** Click "[data-testid="referee-evidence-strategy-seal-unaware-caveat"]"
- **Point out:** The new disclosure line appears directly below the tick-gate statement and above the basis caveats, styled as small gray text to match the surrounding disclosures.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-28/step-04.png

### Step 05 — Expand the Scout Ledger section

- **Narration:** The Scout Ledger shows every trial family that was evaluated during the structured grid search. Each row lists how many variants were tried for that family.
- **Action:** Click "[data-testid="desk-section-expand-scoutLedger"]"
- **Point out:** The Scout Ledger section expands and shows the family entries with their variant counts.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-28/step-05.png

## Full tour (text only)

### Step 06 — View the Walk-Forward Diagnostic

- **Narration:** The Walk-Forward Engine shows the diagnostic runs registered for this session. Each run traces through time in historical order, respecting fold boundaries and chronology.
- **Action:** Click "[data-testid="desk-section-expand-walkForward"]"
- **Point out:** The Walk-Forward section expands, confirming the structure is in place.

### Step 07 — Confirm the Validation Vault is intact

- **Narration:** The Validation Vault stores the sealed evaluation records. It remains protected and read-only, holding the truth about which variants were valid on unseen data.
- **Action:** Click "[data-testid="desk-section-expand-validationVault"]"
- **Point out:** The Validation Vault section expands with its integrity status visible.

### Step 08 — Check the Referee Runs section

- **Narration:** The Referee Runs section records any past evaluations. In this session, none have been recorded yet, confirming we are still in the exploration and validation phase.
- **Action:** Click "[data-testid="desk-section-expand-refereeRuns"]"
- **Point out:** The Referee Runs section is present and shows its initial state.
