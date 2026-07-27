# Phase goal-desk-iter-7 — What to Click (Operator Verification Guide)

**Phase:** goal-desk-iter-7
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running at `http://localhost:8301`
- No login required
- Backend must have at least the recorded desk screen dated `2026-06-22` (it contains an `AAPL`
  row and an `ABBV` row among 91 skipped members) — this is already present in the seeded test data
  for this session. If verifying against a fresh backend with none of this data, steps 2–5 below
  will not apply as written; verify only step 1 and step 7 instead.

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The "Desk" heading appears, followed by a "Provenance" panel, a "Briefing" table
     of ranked symbols, a "Skipped Members" table, and a "Screen History" table.

2. In the "Screen History" table, click the row whose "date" column reads `2026-06-22`
   - **Expect:** A banner appears reading "Viewing the recorded screen for 2026-06-22 — not the
     latest." The Briefing table's first row now shows symbol `AAPL`.

3. Hover your mouse over the `AAPL` row — anywhere in the row, including plain cells like the
   "side" column that shows `resistance` (not just the small distance/score numbers)
   - **Expect:** After about 1–2 seconds, a browser tooltip appears showing the row's full detail:
     `distance 0.33523150389608725 bps · score 97 ·` followed by a "window last requested" line for
     each timeframe. This is this iteration's fix — the tooltip used to only show up over a couple
     of tiny spots; now it shows up anywhere in the row.

4. Click anywhere in that same `AAPL` row (e.g. on the "Class A" text, not just the symbol)
   - **Expect:** The browser navigates to a URL starting with
     `http://localhost:3301/structure?symbol=AAPL&asof=2026-06-22`. The Symbol and As-of fields on
     the new page are already filled in, and a "Tradable Map" table is already showing band rows —
     no extra typing or clicking needed. This confirms the tooltip fix did NOT break the click.

5. Click your browser's Back button to return to `/desk`, then hover over the `ABBV` row in the
   "Skipped Members" table
   - **Expect:** A tooltip appears with only "window last requested" lines (all reading "never") —
     it must NOT show any distance or score number, since a skipped symbol has neither.

6. Click that same `ABBV` row
   - **Expect:** The browser navigates to `/structure?symbol=ABBV&asof=...` and shows an honest
     message such as "No bar series recorded for ABBV." — not a crash, not a blank page.

7. Look at the top navigation bar (visible on every page)
   - **Expect:** Exactly three links: "Cockpit", "Structure", "Desk" — nothing added, nothing
     missing, nothing renamed.

---

## What "Working Correctly" Looks Like

- Hovering ANYWHERE inside a Briefing or Skipped row on `/desk` — not just a specific number or
  badge — shows one tooltip with that row's full-precision detail.
- Clicking anywhere in that same row still jumps straight to `/structure` with the symbol and date
  already filled in, exactly as it did before this fix — the tooltip change must never interfere
  with the click.
- A skipped row's tooltip never shows a distance or score value, only coverage-freshness lines.
- The rest of the product (Cockpit, Structure, the nav) looks and behaves exactly as it always has
  — this iteration touched nothing else.

## Common Issues

- **No tooltip appears after hovering**: wait a bit longer (up to 2 seconds — this is the browser's
  native tooltip, not something the page draws immediately) before concluding it is missing.
- **Tooltip only appears over the distance/score numbers, not the rest of the row**: this would mean
  the fix regressed — the whole row (via its single drill-in link) should carry the tooltip now, not
  just those two small cells.
- **Clicking the row does nothing anymore**: open browser DevTools and check the row's `<a
  data-testid="desk-row-drill-in">` element still has its `href` and `absolute inset-0` class — if
  either is missing, the click geometry broke, which is exactly what this iteration was built to
  avoid.
- **Blank page / error screen**: confirm the backend is running (`curl
  http://localhost:8301/research/desk/screen`) and reload `/desk`.
