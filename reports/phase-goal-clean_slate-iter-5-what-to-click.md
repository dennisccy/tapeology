# Phase goal-clean_slate-iter-5 — What to Click (Operator Verification Guide)

**Phase:** goal-clean_slate-iter-5
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301` — rebuilt fresh this iteration. If you see an old
  Journal/Studies page, or `/structure` looks unchanged from before, ask a developer to run
  `rm -rf apps/frontend/.next` and restart the frontend before you test.
- Backend running at `http://localhost:8301`
- No login required
- No test-data setup required — the AAPL `2026-06-22T21:00:00Z` recorded window used below was
  already captured in a prior iteration

---

## Verification Steps

1. Open `http://localhost:3301/` in your browser
   - **Expect:** The heading "No ticker watched" appears; the top nav bar shows exactly two
     items — "Cockpit" and "Structure" — and nothing labeled "Journal", "Studies", or
     "Performance"

2. Type `SIM-BUYER` into the ticker field (placeholder "Ticker e.g. SIM-BUYER"), then click the
   green "Watch" button
   - **Expect:** Within a few seconds, a panel titled "Tape State" shows the large text "Buyer
     Control", and a candlestick chart appears above the panel grid

3. Click the red "Stop" button (next to the text "Watching SIM-BUYER")
   - **Expect:** The page returns to "No ticker watched" — confirms the cockpit's core watch/stop
     loop still works after this iteration's changes

4. Navigate to `http://localhost:3301/structure`
   - **Expect:** The heading "Structure" loads; the small gray paragraph beneath it contains the
     sentence "Case Studies lists every band-touch event with its reaction, forward returns, and
     — once recorded — its tape timeline;" — this sentence was reinstated this iteration

5. Type `AAPL` into the "Symbol" field (placeholder "e.g. PG") and `2026-06-22T21:00:00Z` into the
   "As-of (UTC, ISO-8601)" field, then click "Load"
   - **Expect:** A candlestick chart renders in the "Tradable Map" section, and a table below it
     shows a band row whose range text includes `300.11`

6. Scroll down to the "Case Studies" section
   - **Expect:** This section is now visible — it was completely missing before this iteration —
     with a table whose columns read `symbol`, `session`, `band`, `reaction`, `forward returns`,
     populated with at least one row

7. Refresh the page (press F5 or Cmd+R), then scroll back down to "Case Studies"
   - **Expect:** The Case Studies section and its populated table are still there after the
     reload — confirms this is a real rebuilt-and-deployed change, not a client-side-only toggle

8. Click any row in the Case Studies table
   - **Expect:** A panel titled "Case Studies — drill-in" opens below the table, showing that
     event's band and reaction, plus either a tape-timeline list or the exact text "No recorded
     tape for this event."

9. Scroll down to the "Edge Report" section
   - **Expect:** Either a populated Train/Hold-out comparison table, or the exact text "Edge
     report not computed yet." next to a button labeled "Compute edge report" — never a blank
     panel

---

## What "Working Correctly" Looks Like

- The "Case Studies" section is visible on `/structure` (positioned between "Tradable Map"/"Show
  raw levels" and "Edge Report"), survives a page refresh, and clicking a row opens a working
  drill-in — this is the one new thing this iteration ships
- The top nav bar shows only "Cockpit" and "Structure" — nothing from the old Journal, Studies, or
  Performance pages survives anywhere in the UI
- The sim cockpit's core loop (Watch → "Buyer Control" → Stop → "No ticker watched") still works
  exactly as it did before this iteration

## Common Issues

- **Blank page, or the old Journal/Studies UI still showing**: the frontend is serving a stale
  build. Ask a developer to run `rm -rf apps/frontend/.next`, then rebuild and restart the
  frontend.
- **Case Studies section still missing after a fresh rebuild**: check
  `apps/frontend/app/structure/page.tsx` around line 335 — `SHOW_CASE_STUDIES` must read `true`,
  not `false`.
- **Edge Report panel is truly blank, or reads "not computed yet." with no visible "Compute edge
  report" button**: this is a real defect — the honest not-computed state must always include a
  Compute button, never a dead end.
- **Backend appears unreachable**: confirm `http://localhost:8301/health` responds; if it does
  not, the nav bar itself will show the text "navigation unavailable — backend unreachable"
  instead of the two nav links.
