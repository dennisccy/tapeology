# Phase goal-desk-iter-18 — What to Click (Operator Verification Guide)

**Phase:** goal-desk-iter-18
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running and reachable, serving the real ambient desk data store (no login required)
- No seed data needed — the real store already contains a computed screen (latest snapshot
  `screen-2026-07-28-ac07c9581a4f`, 63 ranked rows including `BRK-B` and `CRM`, as of 2026-07-28)

**Heads up before you start:** every screen snapshot on record today predates this feature, so every
row you see will show the honest text `"opposite wall not recorded in this snapshot"` rather than a
populated wall — that is the CORRECT, expected behavior for this store right now, not a bug. See step
7 below for what a populated row would look like instead.

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The page loads with a "Desk" heading and a short description paragraph, no blank
     screen, no amber "could not be loaded" panel

2. Scroll down to the ranked table (inside the "Briefing" panel, below "Provenance") and scroll it
   horizontally all the way to the right
   - **Expect:** The last column header now reads **"opposite"** — this is the new column this
     iteration adds (11 columns total: symbol, side, class, distance, score, coverage, tick evidence,
     basis, history, band, opposite)

3. Find the row whose leftmost cell reads **"BRK-B"** (it is the first/topmost ranked row) and read
   its rightmost cell (the new "opposite" column)
   - **Expect:** The cell reads exactly **"opposite wall not recorded in this snapshot"**

4. Hover your mouse anywhere over that same `BRK-B` row (the whole row is one clickable link, so any
   spot works) and wait for the tooltip to appear
   - **Expect:** The tooltip's text ends with "... close not recorded in this snapshot ·
     **bands by class not recorded in this snapshot** · 1h window last requested: ..." — the new
     per-class-count detail is appended right after the "band"/"close" detail and right before the
     coverage-timestamp list

5. Look at the `BRK-B` row's other cells: "distance", "score", and "band"
   - **Expect:** "distance" reads `0.00 bps`, "score" reads `1787.00`, and "band" reads `band
     488.50–490.85 · close not recorded in this snapshot` — all unchanged from before this iteration,
     confirming the new "opposite" column didn't disturb any existing column

6. Click anywhere in the `BRK-B` row (whole-row link) to confirm the drill-in still works, then use
   your browser's Back button to return to `/desk`
   - **Expect:** Step 6a navigates to `http://localhost:3301/structure?symbol=BRK-B&asof=...` with a
     "Structure" page loading for `BRK-B`; Back returns you to `/desk` with the same screen showing

7. Compare what you saw in step 3 against this reference: a row belonging to a BRAND NEW screen (one
   computed after this code shipped) would instead show something like `opposite resistance A
   490.88–494.22 · 0.61 bps` in that same cell — four legible values instead of the fallback text.
   Similarly, a NEW row's tooltip would show something like `bands by class A 10 · B 0 · C 0 ·
   unclassified 0` instead of the fallback sentence from step 4
   - **Expect:** You will NOT see this populated form anywhere on `http://localhost:3301/desk` today
     — every recorded screen predates the feature. This is disclosed and expected (see "Common
     Issues" below), not something to report as broken

8. Scroll to the "Skipped Members" section further down the page and check its table's header row
   - **Expect:** The skip table's header still reads exactly 4 columns — `symbol, reason, coverage,
     tick evidence` — with NO "opposite" column. This is correct: a skipped member was never ranked,
     so it has nothing to disclose an opposite wall for

---

## What "Working Correctly" Looks Like

- Every ranked row's rightmost cell is a new "opposite" column that reads `"opposite wall not
  recorded in this snapshot"` for every row visible today (all snapshots on record predate this
  feature).
- Hovering any ranked row shows a tooltip whose last detail segment (before the coverage-timestamp
  list) is the "bands by class not recorded in this snapshot" fallback.
- Every other column (symbol, side, class, distance, score, coverage, tick evidence, basis, history,
  band) looks exactly as it did before this iteration — the new column is purely additive.
- The row's whole-row drill-in link to `/structure` still works, and the Skipped Members table has
  not grown an "opposite" column of its own.

## Common Issues

- **"opposite" column is missing entirely, or the table still has only 10 columns**: the frontend
  build is stale — do a clean `.next` rebuild and restart the frontend (a known gotcha on this
  project, per prior iterations' notes).
- **A row's "opposite" cell is blank, or shows "undefined"/"NaN"**: this IS a bug — file it. The
  correct states are only the exact fallback text, the exact `"no band on the other side"` text, or
  the four-value `opposite <side> <class> <low>–<high> · <n> bps` pattern — never blank/undefined.
- **You expected to see real numbers in the "opposite" column but only see the fallback text**: this
  is correct, not a bug — every screen snapshot in the live store was recorded before this
  iteration's code existed. Seeing real numbers requires a brand-new screen snapshot computed after
  this code shipped; the backend's own automated tests already prove the populated rendering is
  correct even though it isn't visible on this particular store today.
- **You tried clicking "Run Screen" to force a populated example**: be aware the button submits
  TODAY's own calendar date as `screen_date`. If a screen for today's date is already recorded (very
  likely — check the "Screen History" panel for today's date), the backend reuses that already-
  recorded (and therefore still-legacy) snapshot instead of computing a new one — you will see the
  message "Reused the snapshot already recorded for this key — ..." beneath the button and the
  "opposite" column will still show the fallback text. This is expected dedup behavior (TC-6), not a
  bug; producing a genuinely new, populated example requires either waiting for a not-yet-recorded
  date or a dedicated fixture-scoped rig (see the QA/dev handoffs for this iteration).
- **Blank page / error screen**: check that the backend is running and reachable at the port the
  frontend's `NEXT_PUBLIC_API_URL` was built with.
