# Phase goal-desk-iter-17 — What to Click (Operator Verification Guide)

**Phase:** goal-desk-iter-17
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running and reachable, serving the real ambient desk data store (no login required)
- No seed data needed — the real store already contains a computed screen (latest snapshot
  `screen-2026-07-28-ac07c9581a4f`, 63 ranked rows including `BRK-B` and `LIN`, as of 2026-07-29)

**Heads up before you start:** every screen snapshot on record today predates this feature, so
every row you see will show the honest text `"close not recorded in this snapshot"` rather than a
number — that is the CORRECT, expected behavior for this store right now, not a bug. See step 6
below.

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The page loads with a "Desk" heading, no blank screen, no error panel

2. Scroll down to the ranked table (below "Provenance", inside the "Briefing" section) and look at
   its header row — scroll it horizontally to the right edge if it doesn't fully fit
   - **Expect:** The last column header, after "history", now reads **"band"** — this is the new
     column this iteration adds (10 columns total: symbol, side, class, distance, score, coverage,
     tick evidence, basis, history, band)

3. Find the row whose leftmost cell reads **"BRK-B"** and read its rightmost cell (the new "band"
   column)
   - **Expect:** The cell reads exactly **"close not recorded in this snapshot"**

4. Hover your mouse anywhere over that same `BRK-B` row (the whole row is one clickable link, so any
   spot works) and wait for the tooltip to appear
   - **Expect:** The tooltip's text ends with "... history 500 sessions from
     2024-07-25T04:00:00.000000Z · **close not recorded in this snapshot** · 1h window last
     requested: ..." — the new close/band detail is appended right after the "history" detail

5. Look at the `BRK-B` row's other cells: "distance" and "score"
   - **Expect:** "distance" reads `0.00 bps` and "score" reads `1787.00` — unchanged from before
     this iteration, confirming the new "band" column didn't disturb any existing column

6. Compare what you saw in step 3 against this reference: a row belonging to a BRAND NEW screen
   (one computed after this code shipped) would instead show something like
   `band 488.50–490.85 · close 488.50` in that same cell — three legible numbers instead of the
   fallback text
   - **Expect:** You will NOT see this populated form anywhere on `http://localhost:3301/desk`
     today — every recorded screen predates the feature. This is disclosed and expected (see
     "Common Issues" below), not something to report as broken.

---

## What "Working Correctly" Looks Like

- Every ranked row's rightmost cell is a new "band" column that reads
  `"close not recorded in this snapshot"` for every row visible today (all snapshots on record
  predate this feature).
- Hovering any ranked row shows a tooltip whose last detail segment (before the coverage-timestamp
  list) is this same close/band information.
- Every other column (symbol, side, class, distance, score, coverage, tick evidence, basis, history)
  looks exactly as it did before this iteration — the new column is purely additive.

## Common Issues

- **"band" column is missing entirely, or the table still has only 9 columns**: the frontend build
  is stale — do a clean `.next` rebuild and restart the frontend (a known gotcha on this project,
  per prior iterations' notes).
- **A row's "band" cell is blank, or shows "undefined"/"NaN"**: this IS a bug — file it. The correct
  states are only the exact fallback text or the three-number `band X–Y · close Z` pattern, never
  blank/undefined.
- **You expected to see real numbers in the "band" column but only see the fallback text**: this is
  correct, not a bug — every screen snapshot in the live store was recorded before this iteration's
  code existed. Seeing real numbers requires a brand-new screen computed after this code shipped;
  the backend's own automated tests already prove the populated rendering is correct even though it
  isn't visible on this particular store today.
- **Blank page / error screen**: check that the backend is running and reachable at the port the
  frontend's `NEXT_PUBLIC_API_URL` was built with.
