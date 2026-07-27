# Phase goal-desk-iter-9 — What to Click (Operator Verification Guide)

**Phase:** goal-desk-iter-9 (Era B, Journey J-08 — basis disclosure)
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running at `http://localhost:8301` (the frontend calls it directly; no login is required
  anywhere on this page)
- At least one screen already recorded for the registered universe — true on the current instance:
  the "Screen History" panel already lists screens dated `2026-06-22` and `2026-07-25`

---

## Steps

1. Open `http://localhost:3301/desk` in your browser.
   - **Expect:** The page loads with the heading "Desk" and a ranked-rows table whose header row
     reads (left to right) `symbol, side, class, distance, score, coverage, tick evidence, basis` —
     8 columns, "basis" is the new, last one. No red or amber error banner.

2. In the "Screen History" panel near the bottom of the page, click the row dated "2026-07-25".
   - **Expect:** A banner appears reading "Viewing the recorded screen for 2026-07-25 — not the
     latest." and every row's rightmost "basis" column cell reads exactly
     "basis not recorded in this snapshot". This is old data, recorded before this feature shipped
     — the page honestly says so instead of guessing.

3. Click the "Latest" button inside that banner.
   - **Expect:** The banner disappears and the table returns to showing the latest screen.

4. Scroll down to the "Run Screen / Top-up" panel and click the "Run Screen" button.
   - **Expect:** The button changes to "Computing…" with a line below it counting up
     "`X` / `Y` members". When it finishes (well under a minute — this step reads only bars already
     stored, it does not fetch anything from the internet), the button goes back to reading
     "Run Screen" and a line just above it reads "Recorded a new snapshot — screen-2026-07-27-…"
     (or "Reused the snapshot already recorded for this key — …" if today's screen already existed
     — either wording is fine).

5. Look at the "basis" column of the ranked table now on screen.
   - **Expect:** Every row shows real text like "basis 2026-07-23 · 4 d before as-of" — a real date
     and a real day-count. Never blank, never a dash, never the word "undefined".

6. Compare the day-count across all the visible rows.
   - **Expect:** The counts are not all the same — some rows read a small number (the freshest
     price reading available) and others read a noticeably larger number, often 10 or more days.
     That spread is the entire point of this feature: a same-day wall and an 11-day-old one are now
     visibly different, where before they looked identical.

7. Hover your mouse over any part of one ranked row — anywhere in the row works, not just the
   basis cell — and hold still for a second.
   - **Expect:** One tooltip appears containing text like
     "distance 0.31 bps · score 93 · basis 2026-07-23T04:00:00.000000Z (4 d before as-of) · …" —
     the basis detail sits between "score" and the coverage text that follows it.

8. Click directly on the text inside that same row's "basis" cell.
   - **Expect:** The browser navigates to a `/structure?symbol=...` page. It must NOT do nothing —
     a click on the new column has to trigger the same navigation clicking anywhere else in the row
     would.

9. Scroll down to the "Skipped Members" panel.
   - **Expect:** Its table still shows only 4 columns — `symbol`, `reason`, `coverage`,
     `tick evidence` — with no "basis" column. This section is untouched by this update.

---

## What "Working Correctly" Looks Like

- The ranked table has 8 columns, ending in "basis"; every row of a freshly-run screen shows a real
  date and day-count there, and the day-counts visibly differ from row to row.
- A screen recorded before this update (any date in "Screen History" other than today) shows
  "basis not recorded in this snapshot" on every row instead — never a blank cell.
- Clicking anywhere in a row — including squarely on the new basis text — still opens that symbol
  in `/structure`.

## Common Issues

- **Basis column missing or the table still shows only 7 columns**: hard refresh the page
  (Ctrl+Shift+R / Cmd+Shift+R) — a stale cached frontend build is the most common cause.
- **Basis cell shows blank, a dash, or the literal word "null"/"undefined"** instead of either a
  real date or the "basis not recorded in this snapshot" sentence: this is a real defect — the
  fallback text should always render instead of a raw empty value.
- **Clicking the basis cell does nothing (step 8)**: this means the new column broke the row's
  existing "click anywhere to open in /structure" behavior — flag it, this is the one regression
  risk this iteration explicitly called out as unverified.
- **"Run Screen" shows a red error line instead of progress**: the backend may be unreachable —
  check `curl http://localhost:8301/research/desk/screen` returns a `200`.
