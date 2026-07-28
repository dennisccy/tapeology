# Phase goal-desk-iter-11 — What to Click (Operator Verification Guide)

**Phase:** goal-desk-iter-11 (Era B, Journey J-09 — durable top-up run log)
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running at `http://localhost:8301` (the frontend calls it directly; no login is required
  anywhere on this page)
- A universe snapshot already registered — true on the current instance (the "Provenance" panel, or
  the amber "Desk screen not computed yet." panel's own controls, will show a working "Top-up"
  button either way)
- Note before you start: step 4 below deliberately starts and then cancels a REAL top-up run. This
  writes one small, genuine "cancelled" record into this instance's permanent history — that is
  expected and is exactly what this feature is for, not a mistake to undo.

---

## Steps

1. Open `http://localhost:3301/desk` in your browser.
   - **Expect:** The page loads with the heading "Desk". No red or amber error banner across the
     top of the page.

2. Scroll all the way to the bottom of the page.
   - **Expect:** A panel titled "Top-up Runs" is the very LAST thing on the page. If no top-up run
     has ever completed on this instance yet, it reads exactly "No top-up runs recorded yet." with
     no rows below it — that is the correct, honest starting state, not a bug.

3. Scroll back up to the "Run Screen / Top-up" panel (or the amber "Desk screen not computed yet."
   panel, if no screen has ever been run — the Top-up button lives there too) and click the
   "Top-up" button.
   - **Expect:** The button's label changes to "Topping up…" and a progress line appears beneath it
     counting pairs (e.g. "3 / 300 pairs").

4. Wait about 5–10 seconds, then click the "Cancel" button that appeared next to the progress line.
   - **Expect:** The label briefly reads "Cancelling — finishing the current pair…", then settles.
     An amber line appears reading "Top-up cancelled — pairs already recorded before the cancel
     stay stored."

5. WITHOUT refreshing the page, scroll back down to the "Top-up Runs" panel.
   - **Expect:** Within a couple of seconds, a new row appears at the top of the table showing
     today's date, a run id starting with `topup-`, the state "cancelled", and an
     "attempted / total" count where the first number is smaller than the second (e.g. "4 / 300") —
     it appears automatically, with no page reload.

6. Read the "Latest run" detail text just below the table.
   - **Expect:** It reads "state: cancelled", "`N` of `M` pairs attempted", and an amber note
     reading "`X` pairs not reached" — where `X` is the difference between the two numbers in step
     5's row (e.g. if the row read "4 / 300", this note should read "296 pairs not reached").

7. Refresh the page (press F5 or Cmd+R).
   - **Expect:** The exact same cancelled run still appears as a row in the table, and the same
     "Latest run" detail is still shown below it — the record survived the reload because it is
     saved to disk, not just held in the browser's memory.

8. Scroll up to the "Screen History" panel (above Top-up Runs).
   - **Expect:** It still lists whatever screens were recorded before you started — completely
     unaffected by the new panel below it.

---

## What "Working Correctly" Looks Like

- Before any top-up run, the Top-up Runs panel plainly says "No top-up runs recorded yet." — never
  blank, never a spinner stuck forever.
- After starting and cancelling a real Top-up run, a new row appears in the Top-up Runs table
  WITHOUT a manual page refresh, and the same row survives a manual refresh afterward.
- The cancelled run's detail honestly shows how many pairs it never reached — it never claims "0
  pairs not reached" for a run that was actually cut short.
- Every other section on `/desk` (Provenance, Briefing, Skipped Members, Screen History, Run
  Screen/Top-up controls) looks and behaves exactly as it did before this update.

## Common Issues

- **Blank page / error banner**: Check that the backend is running
  (`curl http://localhost:8301/research/desk/topup/runs` should return
  `{"runs":[...],"latest":...}`, not a connection error).
- **"Top-up Runs" panel never appears at the bottom of the page**: hard refresh
  (Ctrl+Shift+R / Cmd+Shift+R) — a stale cached frontend build is the most common cause.
- **New cancelled run doesn't appear after step 5, even after a few seconds**: try the manual
  refresh from step 7 — if it appears only after a manual refresh and never on its own, the
  auto-refresh behavior is broken (flag it); if it never appears even after a manual refresh, the
  write itself failed (flag it as a more serious defect).
- **The "pairs not reached" note is missing, or reads "0 pairs not reached"**: this is a real
  defect for a run you know you cancelled early — the note should always be present with an
  accurate, non-zero count in that situation.
