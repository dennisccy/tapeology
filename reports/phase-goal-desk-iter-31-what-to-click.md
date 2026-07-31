# Phase goal-desk-iter-31 — What to Click (Operator Verification Guide)

**Phase:** goal-desk-iter-31
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running at `http://localhost:8301`
- No login required, no seed data required — the ambient `/desk` store already has recorded
  screen runs from prior iterations

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The page loads with a heading "Desk" and no error screen. Several panels are
     visible, including one titled "Screen Runs".

2. Scroll down to the "Screen Runs" panel and find the sub-heading starting "Latest run — 2026-07-31 · screenrun-..."
   - **Expect:** Just below it, one line of small text ends with "reused screen-2026-07-31-c169546856c7 — no walk was performed".

3. Look immediately below that outcome text for an amber warning or a second line of counts
   - **Expect:** Neither appears. Specifically, you should NOT see any amber text like "101 members not reached", and you should NOT see a line like "0 ranked · 0 skipped (no bars) · 0 skipped (no basis)". This is the fix — a reused run used to show both of those, making it look like something had failed even though it hadn't.

4. Still on `/desk`, look at the table above the "Latest run" detail (the "Screen Runs" history table)
   - **Expect:** Multiple rows are present, at least one showing "101 / 101" in the "attempted / total" column and at least one showing "no walk was performed" in the "produced" column. This proves the full history is still intact and unaffected by step 3's fix.

5. Refresh the page (press F5 or Cmd+R)
   - **Expect:** The same "Latest run" block still shows the honest "reused ... — no walk was performed" outcome text with no amber note and no counts line — the fix is not a one-time render fluke.

6. Click "Desk" (or whichever entry is highlighted) in the top navigation bar, then click it again
   - **Expect:** You stay on / return to `http://localhost:3301/desk`, and the page still renders exactly as in step 2 — confirms normal navigation is unaffected.

---

## What "Working Correctly" Looks Like

- The "Latest run" block for a reused run shows exactly one outcome line ("reused `<id>` — no walk was performed") and nothing else warning-shaped below it.
- The "Screen Runs" history table above it is untouched — full historical rows, including a "101 / 101" completed walk, are still all present.

## Common Issues

- **Blank page / error screen on `/desk`**: check that the backend is running
  (`curl http://localhost:8301/research/desk/screen/runs`); the "Screen Runs" panel will show an
  "unavailable" message instead of a blank page if the backend is unreachable, so a truly blank
  page points at a frontend build problem instead.
- **Amber "N members not reached" note still visible on the reused run**: the frontend was not
  rebuilt after this iteration's `page.tsx` change — rebuild with
  `cd apps/frontend && rm -rf .next && npm run build && npm start` (or restart the dev server) and
  retry.
- **`/desk` latest run is no longer the reused one described above**: someone clicked "Run Screen"
  since this guide was written. Re-derive the current latest run's `state`/`reused`/`id` with
  `curl -s http://localhost:8301/research/desk/screen/runs | python3 -m json.tool` and re-check
  step 3's expectation against whichever state it now shows (reused → no amber/counts; fresh walk →
  amber/counts are correctly still visible, since the fix only suppresses them for reused runs).
