# Phase goal-desk-iter-34 — What to Click (Operator Verification Guide)

**Phase:** goal-desk-iter-34
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3301`, backend at `http://localhost:8301`
- No login required
- The ambient store already has at least one recorded top-up run (currently
  `topup-2026-07-31-8fb5c9a1f737`) — no need to trigger a new one

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The Desk page loads, no error page or blank screen

2. Scroll down to the "Top-up Runs" section, then to the "Latest run — `<date>` · `<run-id>`"
   heading below its summary table
   - **Expect:** A line reading "newest recorded reach `<date>` · `<N>` pairs reach it" is visible
     (e.g. "newest recorded reach 2026-07-30 · 303 pairs reach it")

3. Write down the calendar day printed in that line (e.g. `2026-07-30`)
   - **Expect:** Just below it, a heading "Pairs recorded earlier (`<M>`)" is visible (e.g.
     "Pairs recorded earlier (101)")

4. Read every row listed under that heading (each row reads `SYMBOL TIMEFRAME — YYYY-MM-DD`)
   - **Expect:** None of the rows show the same date you wrote down in step 3 — e.g. every row
     shows `2026-07-27`, never `2026-07-30`

5. Check whether a one-line sentence "showing `<shown>` of `<M>`" appears directly beneath the
   "Pairs recorded earlier" heading, above the first row
   - **Expect:** If `<M>` (from step 3) is greater than 20, this sentence IS present (e.g.
     "showing 20 of 101"); if `<M>` is 20 or fewer, this sentence is ABSENT

6. Count the rows rendered under "Pairs recorded earlier"
   - **Expect:** At most 20 rows are shown, even when the heading's count `<M>` is larger

7. Refresh the page (press F5 or Cmd+R)
   - **Expect:** The same reach date, same "Pairs recorded earlier (`<M>`)" count, and the same
     "showing 20 of `<M>`" text (if present) reappear identically — confirms the data is persisted
     server-side, not a client-only artifact

8. Click "Cockpit" and then "Structure" in the top navigation bar
   - **Expect:** Both pages (`http://localhost:3301/` and `http://localhost:3301/structure`) load
     normally with no errors — confirms this fix (scoped entirely to `/desk`) did not disturb them

---

## What "Working Correctly" Looks Like

- The "newest recorded reach `<date>`" line and every row under "Pairs recorded earlier" always
  show DIFFERENT calendar days from each other — never the same day appearing in both places
- When more than 20 pairs are genuinely earlier, a plain "showing 20 of `<M>`" sentence appears
  right under the "Pairs recorded earlier (`<M>`)" heading, and no more than 20 rows are listed

## Common Issues

- **Blank page / error screen on `/desk`**: check that the backend is running
  (`curl http://localhost:8301/research/desk/topup/runs`)
- **Old page still shows a row matching the "newest" date, or the list looks unbounded (>20 rows,
  no "showing" text)**: the frontend build is stale — stop the frontend, run
  `rm -rf apps/frontend/.next`, and restart it (a clean rebuild is required after this fix, per this
  iteration's own verification note)
- **"showing N of M" text never appears no matter what**: confirm the ambient run's true
  "Pairs recorded earlier" count (the heading's own number) is actually greater than 20 — if it is
  20 or fewer, the sentence is correctly absent (see step 5)
