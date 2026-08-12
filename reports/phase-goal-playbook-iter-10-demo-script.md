# Demo Script — goal-playbook-iter-10

**Mode:** record
**Date:** 2026-08-12
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open Cockpit homepage

- **Narration:** We start on the Cockpit page, the main trading dashboard showing live tape and market data.
- **Action:** Navigate to /
- **Point out:** The Cockpit page is fully loaded with no error messages, and the top navigation bar is visible.
- **Screenshot:** reports/demo/goal-playbook-iter-10/step-01.png

### Step 03 — Desk page loads with all sections

- **Narration:** The Desk page is now fully loaded, showing the main heading and all sections including Playbook Signals, Backscan, and Evidence.
- **Action:** Navigate to /desk
- **Point out:** The Desk heading is visible at the top of the page with no errors, and all section headings are present in order.
- **Screenshot:** reports/demo/goal-playbook-iter-10/step-03.png

### Step 05 — Playbook Signals table shows Range Trade signal

- **Narration:** The signals table refreshes and displays the RTAAA Range Trade signal, which is one of the key setups from the recorded session.
- **Action:** Navigate to /desk
- **Point out:** A table row appears with RTAAA in the symbol column and Range Trade as the setup type.
- **Screenshot:** reports/demo/goal-playbook-iter-10/step-05.png

### Step 07 — Range Trade geometry line with disclosure fields  [NEW]

- **Narration:** The detail panel shows the geometry line describing the range setup: its width in MBR, zone touches, break slot, and whether the price crossed the midrange. This iteration adds a new optional disclosure field for whether the approach swing turned at midrange.
- **Action:** Navigate to /desk
- **Point out:** The geometry line reads exactly: 'range 5.00 MBR wide · low zone touches 2 · high zone touches 2 · broke at slot 7 · crossed midrange'. The new field is present but false for this signal, so the 'turned at midrange' text does not appear—exactly as expected.
- **Screenshot:** reports/demo/goal-playbook-iter-10/step-07.png

### Step 08 — All Desk sections remain intact and error-free

- **Narration:** Scrolling through the full Desk page confirms that all sections—Top-up Runs, Index Reconciliation, Screen Runs, Playbook Signals, Backscan, and Playbook Evidence—are present and working correctly. No new errors were introduced by this iteration's disclosure field.
- **Action:** Navigate to /desk
- **Point out:** All six section headings are visible in order from top to bottom with no error banners or broken layouts. The Backscan section shows a completed run from 2026-06-22 to 2026-06-24, and the Evidence section displays the full distribution table.
- **Screenshot:** reports/demo/goal-playbook-iter-10/step-08.png

## Full tour (text only)

### Step 02 — Navigate to Desk page

- **Narration:** Click the Desk link in the top navigation to see the playbook signals and desk features.
- **Action:** Click the "Desk" link
- **Point out:** The page navigates to /desk and the Desk nav link is now highlighted as active.

### Step 04 — Enter session date to load playbook signals

- **Narration:** We enter the session date 2026-06-22 in the date input field to load the recorded trading signals for that day.
- **Action:** Type "2026-06-22" into the element
- **Point out:** The date input field now contains the date 2026-06-22.

### Step 06 — Open Range Trade signal detail panel

- **Narration:** We click the RTAAA Range Trade row to open its detail panel and see the full geometry information.
- **Action:** Click the "RTAAA Range Trade long" row
- **Point out:** The detail panel expands below the table, showing the signal's header with trigger price, entry, and invalidation level.
