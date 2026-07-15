# Phase goal-tradable_wall-iter-6 — What to Click (Operator Verification Guide)

**Phase:** goal-tradable_wall-iter-6 (J-05: `/structure` decluttered — Tradable Map default + Case Studies + Edge Report)
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301`, backend running at `http://localhost:8301`
- No login required — this application has no authentication
- The backend's bar store should already hold AAPL historical data through at least
  `2026-06-22` (true on the operator's real, populated 12-symbol panel store). If your
  environment's store is empty or different, the exact numbers in steps 2–5 below will differ,
  but the honest-state behavior described still applies.

---

## Verification Steps

1. Open `http://localhost:3301` in your browser, then click "Structure" in the top navigation bar
   - **Expect:** Navigates to `http://localhost:3301/structure`. The heading "Structure" is
     visible, and a "Tradable Map" panel shows "Choose a symbol and an as-of time, then Load, to
     see its tradable level map." Nothing on the page looks broken or blank.

2. In the form near the top, type `AAPL` into "Symbol" and `2026-06-22T15:00:00Z` into "As-of
   (UTC, ISO-8601)", then click "Load"
   - **Expect:** The "Tradable Map" panel fills in with a price chart plus a table of **exactly
     10 rows**. This is the headline change this phase makes — the page used to dump a raw list
     that could run into the hundreds or thousands of lines; now it shows a short, scored list. In
     that table, find the row spanning roughly 300–302 — it should show "Class A", a "round
     number" badge, and the highest score of all 10 rows (153.0).

3. Directly below the Tradable Map, click the "Show raw levels" button
   - **Expect:** The button's label flips to "Hide raw levels", and the old "Price chart — S/R
     levels" + "Confluence zones" panels reappear beneath it, looking exactly as they did before
     this phase (dashed chart lines, A/B/C zone cards). Click the button again — both panels
     should disappear and the label should revert to "Show raw levels".

4. Scroll down to "Case Studies". Type `AAPL` into the Symbol field just above its table, then
   click the row dated `2026-06-22`
   - **Expect:** A drill-in panel opens below the table showing "reaction" = `rejected` and two
     forward-return numbers (labeled `78b:` and `234b:`), both negative.

5. Scroll down to "Edge Report"
   - **Expect:** You should see the text "No edge-report cells yet." This is the correct, honest
     result on this environment right now (no watchlist-symbol trade recordings exist yet) — it
     is not a bug or a broken page. A "simulated — assumed fees/slippage — not indicative of live
     results" disclosure line should also be visible just above it.

6. Scroll further down and confirm "Fetch from Yahoo Finance", "Registry", and "Comparison" all
   still appear, in that order
   - **Expect:** All three panels are present and show real content — a fetch form with Symbol/
     Timeframe/Start/End fields, a "Champion" box plus three strategy cards (`v1`,
     `structure_tape`, `structure_tape_map`), and a dataset picker with a "Run comparison" button.
     Nothing was lost when the page was reorganized — they are simply lower on the page than
     before.

7. Refresh the page (press F5 or Cmd+R)
   - **Expect:** The page reloads to its default idle state — an empty Load form and the
     Tradable Map's "Choose a symbol and an as-of time…" message. This is correct: the page
     always starts fresh on load and has never persisted a prior search, so this is not a
     regression.

---

## What "Working Correctly" Looks Like

- Loading AAPL as-of `2026-06-22` shows a short table of ~10 tradable bands with solid, color-coded
  lines on the chart — not the old giant list of raw levels
- The "Show raw levels" toggle is OFF by default, and turning it on reveals the exact same S/R
  levels/confluence-zones view that existed before this phase
- Case Studies and Edge Report always show real content or an honest "nothing here yet" message —
  never a blank white area or a spinner that never stops
- Fetch-from-Yahoo, Registry, and Comparison still work exactly as before — just lower on the page

## If Something Looks Wrong

- **Blank page / error screen**: confirm both the backend (`http://localhost:8301`) and frontend
  (`http://localhost:3301`) dev servers are running
- **Tradable Map table shows far more than ~10 rows, or looks like a giant raw list**: you may be
  looking at the raw-levels panel instead (check whether the toggle button reads "Hide raw
  levels" — if so, click it once to collapse the raw view and re-check the Tradable Map above it)
- **Edge Report looks stuck on a loading spinner** rather than showing "No edge-report cells
  yet.": wait a few extra seconds; if it never resolves, open the browser's developer console and
  check for a failed request to `/research/edge-report` — the backend may be unreachable
- **Clicking a Case Studies row does nothing**: make sure you clicked directly on the row itself
  (not just typed into the filter field above it) — the whole row is the click target
