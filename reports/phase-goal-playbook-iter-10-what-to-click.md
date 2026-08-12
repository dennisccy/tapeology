# Phase goal-playbook-iter-10 — What to Click (Operator Verification Guide)

**Phase:** goal-playbook-iter-10
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3301`, backend reachable (check
  `curl http://localhost:8301/health` returns `200` if unsure)
- No login required
- No seed data setup needed — a `range_trade` signal for session date `2026-06-22` (symbol
  `RTAAA`) was already on file on the instance this guide was written against

## Note on this iteration's new feature before you start

This iteration adds one small new note that CAN appear on a `range_trade` signal's detail line:
`· turned at midrange`. It only shows up when that specific fact is true for that specific signal
— on the one sample signal available right now, it happens to be **false**, so you will NOT see
that text in step 4 below. That is correct, expected behavior, not a bug — the same way the
neighboring `· crossed midrange` note only shows when true. This guide verifies the feature is
wired correctly (present-but-false renders nothing extra, nothing breaks), not that the chip
visually fires — no build currently has a live example of it firing true.

---

## Verification Steps

1. Open `http://localhost:3301` in your browser
   - **Expect:** Cockpit page loads, no error page, "Cockpit" is highlighted in the top nav bar

2. Click "Desk" in the top navigation bar
   - **Expect:** Navigate to `http://localhost:3301/desk`; the heading "Desk" is visible near the
     top of the page

3. Scroll down to the "Playbook Signals" section. In the field labeled "Session date (yyyy-MM-dd)
   — blank = the most recent recorded session", type `2026-06-22`
   - **Expect:** The signals table refreshes and shows a row with `RTAAA` in the symbol column and
     a "Range Trade" chip in the setup column

4. Click that `RTAAA` / "Range Trade" row
   - **Expect:** A detail panel opens below the table. One of its lines reads exactly: `range 5.00
     MBR wide · low zone touches 2 · high zone touches 2 · broke at slot 7 · crossed midrange` —
     it does NOT include the text "turned at midrange" (expected — see the note above)

5. Scroll further down the same page, past "Playbook Signals"
   - **Expect:** The section headings "Backscan" and "Playbook Evidence" are both visible with no
     error banners; scrolling back up, "Top-up Runs", "Index Reconciliation", and "Screen Runs"
     are also all present and error-free

6. Refresh the page (press F5 or Cmd+R), then repeat step 3 (type `2026-06-22` into the Session
   date field again)
   - **Expect:** The exact same detail line from step 4 reappears once you click the `RTAAA` row
     again — confirms the data is read from the backend consistently, not randomly generated

---

## What "Working Correctly" Looks Like

- The `range_trade` signal's detail line shows a short list of factual notes separated by " · "
  (e.g. "crossed midrange"); "turned at midrange" is now one more possible note in that same list,
  appearing right after "crossed midrange" whenever it applies.
- Every other `/desk` section (Top-up Runs, Index Reconciliation, Screen Runs, Backscan, Playbook
  Evidence, and the rest of the page above them) still loads normally with no new errors.

## Common Issues

- **Blank page / error screen:** Check that the backend is running
  (`curl http://localhost:8301/health` should return `200`).
- **No `RTAAA` row appears for session date `2026-06-22`:** the backend may currently be pointed
  at a different data store than the one this guide was written against. Pick any other
  `range_trade` signal you can find in the table instead — as long as clicking it shows no error
  and the detail line renders cleanly, the feature is working; whether "turned at midrange" text
  appears on that particular signal depends on its own data, not on which backend is active.
- **"Turned at midrange" never appears no matter what you click:** expected on this build — see
  the note at the top of this guide. This does not indicate a problem.
