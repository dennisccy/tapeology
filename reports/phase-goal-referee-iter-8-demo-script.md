# Demo Script — goal-referee-iter-8

**Mode:** record
**Date:** 2026-08-15
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk page

- **Narration:** The Desk is where operators screen setups with the playbook and manage research hypotheses.
- **Action:** Navigate to /desk
- **Point out:** The Desk page has loaded, showing the title and navigation.
- **Screenshot:** reports/demo/goal-referee-iter-8/step-01.png

### Step 02 — Expand the Referee Registry section  [NEW]

- **Narration:** The Referee Registry is the new section at the bottom of the page where operators review candidate research questions and register permanent hypotheses.
- **Action:** Click the "Referee Registry" button
- **Point out:** The Referee Registry section expands, revealing a table with five shortlist candidates (S-1 through S-5), each showing their estimand, setup/side, rationale, and live readiness numbers—including S-4 and S-5 which currently have zero recorded evidence but render honestly with 0.00 accrual and '—' projected days.
- **Screenshot:** reports/demo/goal-referee-iter-8/step-02.png

### Step 03 — Select a candidate to review registration  [NEW]

- **Narration:** Click Select on candidate S-4 to see what registering a hypothesis looks like—a confirmation panel with the candidate's setup details and a reminder that registration writes a permanent, boundary-stamped hypothesis.
- **Action:** Click "[data-testid="referee-shortlist-select-S-4"]"
- **Point out:** A confirmation panel appears below the table with the candidate details (S-4, range_trade:long, Estimand B) and two action buttons: Confirm Registration and Cancel.
- **Screenshot:** reports/demo/goal-referee-iter-8/step-03.png

### Step 04 — Cancel the pending registration  [NEW]

- **Narration:** Click Cancel to dismiss the confirmation panel without writing anything—every action before confirmation is fully reversible.
- **Action:** Click "[data-testid="referee-registration-cancel-button"]"
- **Point out:** The confirmation panel closes; the S-4 button still reads Select, confirming no write occurred.
- **Screenshot:** reports/demo/goal-referee-iter-8/step-04.png

## Full tour (text only)

### Step 05 — Verify the Playbook Evidence section is unaffected

- **Narration:** Scroll up to the Playbook Evidence section to confirm the new Referee Registry did not disturb any existing page content.
- **Action:** Click the "Playbook Evidence" button
- **Point out:** The Playbook Evidence section expands and displays its content exactly as before—no layout shifts or missing data.
