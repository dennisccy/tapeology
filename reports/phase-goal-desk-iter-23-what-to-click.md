# Phase goal-desk-iter-23 — What to Click (Operator Verification Guide)

**Phase:** goal-desk-iter-23
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running at `http://localhost:8301`
- No login required (this project has no auth)
- At least one `/desk` screen must already exist (true in the current ambient environment — the
  latest recorded screen as of this writing is `screen-2026-07-20-ca185294a384`)

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The page loads with a ranked table of symbols (or, if no screen has ever been
     computed, an amber "Desk screen not computed yet." panel — in that case click "Run Screen"
     first and wait for it to finish before continuing)

2. Look at the far-right end of the ranked table's header row
   - **Expect:** A column header labeled `levels` appears immediately after the `opposite` column
     — it is the last column in the table

3. Look at the `levels` cell in the first few ranked rows
   - **Expect:** Either the honest text "composition not recorded in this snapshot" (if the
     currently-displayed screen predates this update), or a tally like `155 levels · 1d 68 · 1h 57
     · 4h 19 · 1w 11` (if the screen was computed after this update)

4. If every row shows "composition not recorded in this snapshot", click the "Run Screen" button
   (in the "Run Screen / Top-up / Reconcile Index" panel below the table) and wait for the
   progress indicator ("N / N members") to finish and disappear
   - **Expect:** The page updates to show a newly-computed screen; the `levels` column now shows
     populated tally text on its ranked rows instead of the absent-composition message

5. Re-check the `levels` cell of a populated row
   - **Expect:** A tally string whose per-timeframe numbers add up to the leading count (e.g. `1d
     68 · 1h 57 · 4h 19 · 1w 11` sums to `155`, matching the leading `155 levels`)

6. Look for a small bordered badge reading "round number" next to the tally text on any row
   - **Expect:** The badge appears only on SOME rows (not all) — it marks rows whose wall sits at
     a round price number; rows without the badge simply show the tally text alone

7. Refresh the page (press F5 or Cmd+R)
   - **Expect:** The same `levels` column, tally values, and any round-number badges reappear
     unchanged — the data is served from the recorded screen snapshot, not recomputed on refresh

8. Scroll left to the earlier columns (`band`, `opposite`, `basis`, `history`, `score`, `distance`,
   `band class`, `side`, `symbol`)
   - **Expect:** All of these still show their normal values exactly as before — nothing about
     them changed by adding the `levels` column

---

## What "Working Correctly" Looks Like

- The ranked table has a `levels` column as its last column, after `opposite`.
- On any screen computed after this update, populated rows show a tally string whose numbers sum
  correctly, plus a "round number" badge on the subset of rows where it applies.
- On any screen computed before this update, every row honestly says "composition not recorded in
  this snapshot" instead of showing a blank cell or a made-up number.

## Common Issues

- **Every row shows "composition not recorded in this snapshot" and clicking "Run Screen" doesn't
  change that**: the screen compute may have returned an already-recorded snapshot for the same
  date/pins (a same-day re-run is expected to reuse the existing recording, not recompute) — check
  the small status line under the "Run Screen" button; it reads "Reused the snapshot already
  recorded for this key" vs. "Recorded a new snapshot" to tell you which happened. If it reused an
  old one, wait for the next calendar day or use a screen already known to be freshly computed.
- **Blank page / error screen**: check that the backend is running
  (`curl http://localhost:8301/research/desk/screen`) and the frontend is running
  (`curl http://localhost:3301/desk`).
- **`levels` column is entirely missing (no header, no cells)**: the frontend may be serving a
  stale build — restart the frontend dev server (see `scripts/dev.sh`) so it picks up this
  iteration's `apps/frontend/app/desk/page.tsx` change.
