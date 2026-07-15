# Phase goal-tradable_wall-iter-9 — What to Click (Operator Verification Guide)

**Phase:** goal-tradable_wall-iter-9
**Time required:** ~5 minutes of hands-on clicking. Step 2 below may already be instant, or may still
be showing its "still loading" placeholder — **both are correct outcomes** depending on whether anyone
has warmed this feature up yet on this backend; see step 2's note. This guide does not ask you to wait
out the slow first-time case.
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301`; backend running at `http://localhost:8301`.
- No login is required anywhere in this app.
- Real market-data credentials and AAPL's recorded bar history are already configured on this backend
  (established in prior iterations) — nothing new to set up.

---

## Verification Steps

1. Open `http://localhost:3301/structure` in your browser.
   - **Expect:** The page loads with the heading "Structure" visible, no error banner, no blank page.

2. Scroll down past the "Tradable Map" and "Case Studies" panels to the panel titled "Edge Report".
   - **Expect:** One of two things, and **either one is correct**:
     - It is still showing a pulsing gray loading block. This is the normal, expected state if nobody
       has ever let this specific computation finish on this backend before — it is not broken, it
       behaves exactly like it always has until someone warms it up once.
     - OR it has already resolved: an amber banner reading `simulated — assumed fees/slippage — not
       indicative of live results`, followed by "Train" and "Hold-out" tables (or the honest message
       "No edge-report cells yet."). **This is the new thing this phase adds** — the exact same panel
       that used to take 10+ hours on every single visit now finishes in seconds once it has been
       warmed up.

3. If step 2 showed the already-resolved outcome, refresh this page (press F5) and watch the "Edge
   Report" panel again.
   - **Expect:** It resolves again within a few seconds — this proves the fast result is genuinely
     saved (survives a normal page refresh), not a one-time coincidence.

4. Scroll back to the top of the page. Type `AAPL` into the "Symbol" field, type
   `2026-06-22T21:00:00Z` into the "As-of (UTC, ISO-8601)" field, then click the "Load" button.
   - **Expect:** The "Tradable Map" panel (above Case Studies) fills in with a small table of 10 rows
     (5 resistance + 5 support). One row's "range" column should fall around 300–302, with its "class"
     column reading "Class A".

5. Look at the button just below the Tradable Map panel.
   - **Expect:** It still reads "Show raw levels" (not "Hide raw levels") — proving the older, noisier
     levels view is still hidden by default, unaffected by this phase's changes.

6. Open a **new tab**, go to `http://localhost:3301/`, type `SIM-BUYER` into the field labeled
   "Ticker", then click the green "Watch" button.
   - **Expect:** A panel titled "Price Chart — Tape-State Markers" appears with a candlestick chart.
     Directly below the chart, a small gray line of text reads exactly **"No tradable map for
     SIM-BUYER."**

7. Click the red "Stop" button, then click "Live", type `AAPL` into the symbol field, and click
   "Watch". Scroll the whole page top to bottom.
   - **Expect:** No "Price Chart — Tape-State Markers" panel appears anywhere on the page — this panel
     must be completely absent in Live mode, exactly as it always was before this phase.

---

## What "Working Correctly" Looks Like

- The Edge Report panel (step 2) either shows its normal loading placeholder (fine, if nobody warmed
  it up yet) or resolves to real Train/Hold-out tables or an honest "No edge-report cells yet." message
  within seconds — never a red error, never a half-drawn table, and a repeat refresh (step 3) is just
  as fast the second time.
- The Tradable Map (step 4) shows a short table (10 rows or fewer) once loaded — never the old,
  1,800-line raw levels dump, which stays tucked behind the still-labeled "Show raw levels" button.
- Watching `SIM-BUYER` shows the chart with the honest "No tradable map for SIM-BUYER." message —
  never a fake band line or chip.
- Live mode never shows the Price Chart panel at all, no matter the symbol.

## Common Issues

- **Blank page / error screen anywhere**: check the backend is running —
  `curl http://localhost:8301/health` should return a JSON response, not a connection error.
- **The Edge Report panel (step 2) is still loading and you expected it to be fast**: this only means
  nobody has warmed it up yet on this backend — it is not a defect. The first time this computation
  runs over the full real dataset corpus it can take upwards of 10 hours; once that finishes once, every
  later visit (including after restarting the backend) should be fast. If it was fast before and is now
  slow again, that is worth flagging.
- **The Edge Report panel shows a red "could not be loaded" panel**: worth flagging — a cold/still-
  computing state should never look like this; a red panel means the backend reported an actual error.
- **Tradable Map (step 4) shows nothing or an error after clicking Load**: worth flagging — try
  reloading `/structure` once first; if it persists, check the backend is reachable.
- **A band line or chip appears while watching `SIM-BUYER`**: worth flagging — simulated tickers never
  have a tradable map, so nothing beyond the honest text message should appear there.
