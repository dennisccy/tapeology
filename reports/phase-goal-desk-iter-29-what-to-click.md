# Phase goal-desk-iter-29 — What to Click (Operator Verification Guide)

**Phase:** goal-desk-iter-29
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3301`, backend at `http://localhost:8301`
- No login required
- A universe snapshot must already be registered (if `/desk` shows a "not computed" panel with no
  "Run Screen" button, a universe fetch must happen first — this is pre-existing behavior from an
  earlier iteration, not something this phase changes)

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The "Desk" page loads (heading "Desk" at the top), no error page, no blank screen

2. Scroll to the bottom of the page, past "Top-up Runs" and "Index Reconciliation"
   - **Expect:** A fourth panel titled "SCREEN RUNS" is visible. It shows either the text
     "No screen runs recorded yet." or a table with columns "date / run / state / attempted /
     total / produced"

3. Scroll back up and click the "Run Screen" button
   - **Expect:** The button changes to "Computing…" and a progress line appears showing
     "`<N>` / `<total>` members" climbing (e.g. "0 / 101" rising toward "101 / 101")

4. Wait for the button to return to reading "Run Screen" (progress finishes)
   - **Expect:** A message appears below the button reading either "Recorded a new snapshot —
     `<id>`" or "Reused the snapshot already recorded for this key — `<id>`"

5. Scroll back down to the "Screen Runs" panel
   - **Expect:** A new row now appears in the table with today's date, the same run id from step
     4's message, state "done", and a "produced" value matching that same id (or "reused `<id>` —
     no walk was performed" if it reused an existing result)

6. Click "Run Screen" a second time, immediately
   - **Expect:** This time the button resolves noticeably faster, and the members-progress counter
     does NOT climb through its full range the way it did in step 3

7. Scroll down to "Screen Runs" again
   - **Expect:** A second new row appears, with "attempted / total" reading "0 / `<total>`" and
     "produced" reading "reused `<id>` — no walk was performed", where `<id>` is the SAME id as the
     row from step 5

8. Refresh the page (press F5 or Cmd+R)
   - **Expect:** Both rows from steps 5 and 7 are still visible in the "Screen Runs" table — the
     ledger persisted, it was not just in-memory browser state

9. Scroll up and confirm the ranked briefing table above "Run Screen" still shows its usual
   columns (symbol, wall distance, score, class) with the same rows as before this test
   - **Expect:** No new column, no layout shift, no horizontal scrollbar

---

## What "Working Correctly" Looks Like

- The "Screen Runs" panel exists as the last section on `/desk`, below "Index Reconciliation",
  and its table grows by one row every time "Run Screen" is clicked to completion
- A duplicate "Run Screen" click on the same day resolves fast and its row honestly says
  "reused `<id>` — no walk was performed" rather than pretending to redo the work
- The ranked table above it and the "Top-up Runs" / "Index Reconciliation" panels are unchanged

## Common Issues

- **"Screen Runs" panel missing entirely**: Check that the frontend build is current
  (`rm -rf apps/frontend/.next` and rebuild) — a stale `.next` cache can serve the pre-iteration
  page.
- **Blank page / error screen**: Check the backend is running
  (`curl http://localhost:8301/research/desk/screen/runs` should return
  `{"runs": [...], "latest": ..., "integrity_errors": []}`, HTTP 200, never a 404).
- **Second "Run Screen" click still looks slow**: Confirm you clicked it for the SAME UTC date as
  the first run — a different day is a genuine cache miss and will walk every member again, which
  is correct behavior, not a bug.
