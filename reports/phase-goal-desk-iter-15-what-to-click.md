# Phase goal-desk-iter-15 — What to Click (Operator Verification Guide)

**Phase:** goal-desk-iter-15 (Era B, Journey J-11 — history-depth disclosure on `/desk`)
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- This iteration adds exactly ONE thing: a new **`history`** column on the `/desk` ranked
  table (immediately right of the existing `basis` column), plus one more line in each row's
  hover tooltip. No new page, no new button, no navigation change.
- Frontend running at `http://localhost:3301`, with a reachable backend. This is a dedicated
  evidence rig for this iteration — do not substitute other ports.
- No login required.
- **This feature has likely already been exercised** by an earlier dev/QA pass on this same rig
  — a screen with a wide session-count split (short and long history side by side) should
  already be recorded and showing by default. If the ranked table's `history` column looks
  empty or shows only similar numbers, click "Run Screen" (step 6 below) to record a fresh one,
  or pick a different history row.

---

## Steps

1. Open `http://localhost:3301/desk` in your browser.
   - **Expect:** the "Desk" page loads, the top nav shows "Cockpit", "Structure", "Desk", and
     there is no red or amber error banner.

2. Look at the ranked table's header row (inside the "Briefing" panel). Scroll the table
   horizontally to the right if the rightmost columns are cut off.
   - **Expect:** the last column header reads **"history"**, immediately after "basis".

3. Scan down the `history` column values.
   - **Expect:** most cells read a pattern like `history 500 sessions · from 2024-07-25` — a
     number, the word "sessions", and a date. Look for at least one row with a small number
     (roughly 60 or fewer) and at least one row with a large number (400 or more) — both should
     be readable without scrolling the page vertically far from each other. Neither cell should
     ever say `null` or be blank.

4. Hover your mouse over any ranked row (anywhere in the row — the whole row is one link) and
   hold still for about a second.
   - **Expect:** a tooltip pops up ending in a segment like `history 500 sessions from
     2024-07-25T04:00:00.000000Z` — the same number as the visible cell, but with the FULL
     timestamp instead of just the date, and the word "from" (no dot before it, unlike the cell).

5. Scroll down to the "Screen History" panel (below "Skipped Members"). Click on any row in that
   table whose date is NOT the one you're currently viewing — pick the oldest date available.
   - **Expect:** a banner appears reading "Viewing the recorded screen for `<date>` — not the
     latest." with a "Latest" button. If that older screen predates this feature, every row's
     `history` cell now reads exactly **"history not recorded in this snapshot"** — not blank,
     not "null". (If every history row on that older date still shows real numbers instead, that
     screen was recorded after this feature shipped — try an even older row, or skip this check.)

6. Click the **"Latest"** button to return to the current screen.
   - **Expect:** the `history` column goes back to showing real session-count values (not the
     fallback text) — confirming the fallback only applies to genuinely old snapshots.

7. Scroll further down and confirm the "Top-up Runs" and "Index Reconciliation" sections are
   still there, below "Screen History".
   - **Expect:** both sections look and behave exactly as before this update — no `history`
     column or text appears in either of them; they may just sit a little lower on the page
     since the ranked table above is now one column wider.

---

## What "Working Correctly" Looks Like

- The ranked table's `history` column shows a session count and a start date for every row from
  a recent screen, with a visibly wide range across rows (e.g. 27 vs. 500) — not identical
  numbers on every row.
- Hovering a row shows the SAME session count but the FULL, untruncated timestamp in the
  tooltip.
- Any screen recorded before this feature shipped shows the honest text "history not recorded
  in this snapshot" instead of a fabricated number — never blank, never the word "null".
- Nothing else on `/desk` — basis column, distance, score, coverage badges, Run Screen, Top-up,
  Reconcile Index, Screen History click-through — looks or behaves any differently than it did
  before this update.

## Common Issues

- **Amber "The desk screen could not be loaded." banner**: the backend is unreachable — restart
  it and reload; nothing is lost (screens are append-only).
- **Amber "Desk screen not computed yet." panel instead of a table**: no screen has ever been
  recorded on this rig — click "Run Screen" to record the first one.
- **`history` column missing entirely, or table only shows 8 columns instead of 9**: hard
  refresh (Ctrl+Shift+R / Cmd+Shift+R) — a stale cached frontend build is the most common cause.
- **Every row's `history` cell shows the same small number, or you can't find a short/long
  split**: the currently-displayed screen may not have a wide split recorded yet — click "Run
  Screen" to record a fresh one against the live universe, which should produce a genuine
  short-vs-long spread.
- **A cell literally shows the text "null" or is blank**: this is a real defect — the honest
  contract is either a real value or the exact fallback sentence, never anything else.
