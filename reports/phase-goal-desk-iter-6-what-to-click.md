# Phase goal-desk-iter-6 — What to Click (Operator Verification Guide)

**Phase:** goal-desk-iter-6
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301`
- Backend running at `http://localhost:8301`
- No login required
- Backend must have at least the recorded desk screen dated `2026-06-22` (it contains an AAPL
  row and 91 skipped rows) — this is already present in the seeded test data for this session.
  If verifying against a fresh backend with no recorded screens, this guide's steps 2–5 will not
  apply; verify only step 1 and step 6 instead.

---

## Verification Steps

1. Open `http://localhost:3301/desk` in your browser
   - **Expect:** The "Desk" heading appears, followed by a "Provenance" panel, a "Briefing"
     table of ranked symbols, a "Skipped Members" table, and a "Screen History" table near the
     bottom of the page.

2. In the "Screen History" table, click the row whose "date" column reads `2026-06-22`
   - **Expect:** A banner appears above the Provenance panel reading "Viewing the recorded
     screen for 2026-06-22 — not the latest." with a "Latest" button next to it. The Briefing
     table's first row now shows symbol `AAPL`, class "Class A", and a distance around
     `0.34 bps`.

3. Click the "Latest" button in that banner
   - **Expect:** The banner disappears completely, and the Briefing table reverts to whatever
     it showed before step 2 (the newest recorded screen, dated `2026-07-25`).

4. Click the row dated `2026-06-22` again, then click anywhere on the `AAPL` row in the
   Briefing table (the symbol text, or any cell in that row)
   - **Expect:** The browser navigates to a new URL starting with
     `http://localhost:3301/structure?symbol=AAPL&asof=2026-06-22`. The "Structure" page loads
     with the Symbol field already showing "AAPL" and the As-of field already showing
     `2026-06-22T23:59:59Z` — no typing and no extra click needed. A "Tradable Map" table
     appears already populated with band rows (not the "Choose a symbol..." placeholder).

5. Look at the Tradable Map table's "range" column for the first row
   - **Expect:** It reads `298.02–300.1001` — the same band the desk briefing row pointed at.

6. Click your browser's Back button twice to return to `/desk`, then click any row in the
   "Skipped Members" table (e.g. the first one listed, `ABBV`)
   - **Expect:** The browser navigates to `/structure?symbol=ABBV&asof=...`. The page does not
     crash or go blank — it shows an honest empty message such as "No bar series recorded for
     ABBV." instead of a chart, because that symbol was skipped for lacking bars.

7. Navigate directly to `http://localhost:3301/structure` (type the bare URL, no `?` params)
   - **Expect:** The Symbol and As-of fields are both empty, and no chart or band table is
     shown — just the plain Load form, exactly as it looked before this phase shipped.

---

## What "Working Correctly" Looks Like

- Clicking a past date in `/desk`'s Screen History table instantly swaps the Briefing/Skipped
  tables to that date's own recorded numbers, with a clear "Viewing the recorded screen for
  <date> — not the latest." banner and a one-click "Latest" button to undo it.
- Clicking any row — ranked or skipped — in the Briefing/Skipped tables jumps straight to
  `/structure` with the symbol and date already filled in and the chart already drawn, with no
  manual re-typing.
- `/structure` opened with no link parameters (or only one of `symbol`/`asof`) looks and behaves
  exactly as it always has — empty fields, nothing loaded until you click "Load".

## Common Issues

- **Clicking a history row does nothing / page looks unchanged**: open browser devtools →
  Network tab and check for a GET request to `/research/desk/screen?date=2026-06-22`. If it's
  missing or returns an error, the backend at `:8301` may not have that screen recorded — check
  `curl http://localhost:8301/research/desk/screen?date=2026-06-22`.
- **Clicking a Briefing/Skipped row does nothing**: make sure you clicked inside the row's cells,
  not in empty whitespace outside the table.
- **`/structure` doesn't auto-load after a drill-in click**: check the URL bar — both `symbol=`
  and `asof=` must be present and non-empty; if either is missing, this is expected behavior (no
  partial auto-load), not a bug.
- **Blank page / error screen on either page**: confirm the backend is running
  (`curl http://localhost:8301/health` if that route exists, or just reload `/desk`).
