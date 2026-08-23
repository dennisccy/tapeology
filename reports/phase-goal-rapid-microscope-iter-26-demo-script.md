# Demo Script — goal-rapid-microscope-iter-26

**Mode:** record
**Date:** 2026-08-23
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk page

- **Narration:** Navigate to the Desk page, which displays research readiness data and pilot studies.
- **Action:** Navigate to /desk
- **Point out:** The 'Desk' link in the top nav is highlighted, and you see section headers below for 'Microscope Readiness' and 'Scout Ledger'.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-26/step-01.png

### Step 02 — Expand the Microscope Readiness section

- **Narration:** Click the Microscope Readiness section to see the corpus totals and band-touch count. This data now loads faster on repeat views thanks to internal caching.
- **Action:** Click "desk-section-expand-microReadiness"
- **Point out:** The section expands to show 'Corpus Totals' table with figures like distinct symbol-days, datasets, and RTH minutes. Below that is the 'Joinable corpus — band touches' value.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-26/step-02.png

### Step 03 — Collapse and re-expand to verify stability

- **Narration:** Click the header again to collapse, then expand once more. The band-touch value remains identical—this confirms the caching change preserves correctness.
- **Action:** Click "desk-section-expand-microReadiness"
- **Point out:** The 'Joinable corpus — band touches' value is the same both times you open the section.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-26/step-03.png

### Step 04 — Expand Scout Ledger

- **Narration:** Scroll down and open the Scout Ledger section to view pilot-study families and their trial variants. The selector table has been consolidated internally.
- **Action:** Click "desk-section-expand-scoutLedger"
- **Point out:** The section shows a 'Ledger chain verification: ok' line, followed by pilot-study family blocks with headers and trial-row tables.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-26/step-04.png
