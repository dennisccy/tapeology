# Phase goal-referee-iter-8 — What to Click (Operator Verification Guide)

**Phase:** goal-referee-iter-8
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running at `http://localhost:8301`
- No login needed (this project has no auth gate)
- Steps 1–5 and 7–8 below are read-only and safe to run anytime. Step 6 performs a real,
  permanent registration write — it is marked optional and should only be done intentionally (see
  the note at that step).

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The "Desk" page loads, no error page, no blank screen.

2. Scroll to the very bottom of the page and click the "Referee Registry" section header (the
   last section on the page)
   - **Expect:** The section expands, showing a table with 5 rows starting with candidate "S-1"
     and ending with "S-5", and a "Registered Hypotheses" heading below it.

3. Look at the shortlist table's "n", "Sessions", "Accrual / day", and "Projected days" columns
   for all 5 rows
   - **Expect:** Every row shows a real number in every column — never a blank cell, "NaN", or
     "Infinity". Rows S-4 and S-5 (which currently have no recorded evidence) show "0.00" and
     "—" rather than crashing.

4. Click the "Select" button on the S-4 row
   - **Expect:** A confirmation panel appears below the table with the text "Register S-4
     (range_trade:long, Estimand B)?" and two buttons: "Confirm Registration" and "Cancel".

5. Click "Cancel"
   - **Expect:** The confirmation panel disappears. The S-4 row's button still reads "Select" —
     nothing was registered. (This step is safe to repeat any number of times.)

6. **[OPTIONAL — permanent, real write]** To verify the actual registration path works: click
   "Select" on any row still showing "Select", then click "Confirm Registration"
   - **Expect:** The button briefly reads "Registering…", then a new row appears in the
     "Registered Hypotheses" table below, showing that candidate's setup/side, a boundary date
     (today's date), the origin "historical-exploration", and a "discovery (exploratory)" count
     next to its accrual count. This is a real, permanent write to the registry the running
     backend uses — only do this intentionally, and prefer a disposable/test backend if one is
     available.

7. Refresh the page (F5) and re-expand "Referee Registry"
   - **Expect:** The same 5-row shortlist renders again, and the "Registered Hypotheses" table
     still shows anything registered in step 6 — confirms the data persisted and the section
     survives a reload.

8. Scroll up and click the "Playbook Evidence" section header (directly above "Referee Registry")
   - **Expect:** It still expands and shows its existing content unchanged — confirms the new
     section didn't break the page's previous last section.

---

## What "Working Correctly" Looks Like

- The shortlist always shows exactly 5 rows (S-1 through S-5), even though two of them currently
  have zero recorded evidence — the table never goes blank or shows an error for those rows.
- The "discovery (exploratory)" label always appears as plain italic text next to a number, never
  as a colored badge — this page deliberately avoids implying advice or a verdict.
- Selecting a candidate never performs a write by itself — only clicking "Confirm Registration"
  does. Everything up through step 5 is fully reversible.

## Common Issues

- **Blank page / error screen**: Check that the backend is running —
  `curl http://localhost:8301/health` should return `{"status":"ok"}`.
- **New "Referee Registry" section is missing, or the page looks exactly like before**: the
  frontend may be serving a stale build. Run `rm -rf apps/frontend/.next`, then rebuild/restart
  the frontend dev server — this project's own known gotcha for this page.
- **"Confirm Registration" shows a red error message**: expected if that candidate was already
  registered (e.g., from another browser tab, or a previous run of step 6) — the message is the
  backend's own explanation, not a crash.
