# Phase goal-tradable_wall-iter-7 — What to Click (Operator Verification Guide)

**Phase:** goal-tradable_wall-iter-7
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301`; backend running at `http://localhost:8301`.
- No login is required anywhere in this app.
- This environment's backend already has real market-data credentials configured, so the
  "AAPL historical replay" step below works out of the box — no setup needed from you.

---

## Verification Steps

1. Open `http://localhost:3301` in your browser.
   - **Expect:** The cockpit loads with no error banner. The "Simulated" button (top-left, next to
     "Tapeology") is already selected.

2. Type `SIM-BUYER` into the "Ticker" field, then click the green "Watch" button.
   - **Expect:** A panel titled "Price Chart — Tape-State Markers" appears with a candlestick chart.
     Directly below the chart, a small gray line of text reads exactly
     **"No tradable map for SIM-BUYER."** — this is the new, honest empty state; there should be NO
     colored horizontal lines drawn on the chart and no other gray banner beneath it.

3. Click the red "Stop" button. Then click the "Historical" button (in the same control as
   "Simulated"), type `AAPL` into the "Symbol search" field, and type `22-06-2026` into the "Date"
   field.
   - **Expect:** A row of buttons appears including one starting with "Full RTH 9:30–16:00 ET".

4. Click that "Full RTH 9:30–16:00 ET" button, change the "Replay speed" dropdown to `10×`, then
   click "Watch".
   - **Expect:** The chart starts loading AAPL candlesticks.

5. Watch the chart for about 30 seconds as candles climb toward the $300 price level.
   - **Expect:** One or two **solid** (not dashed) horizontal lines appear on the chart near $300 —
     this is the new tradable-band overlay. A rose/pink line means resistance, a green line means
     support. This is the single most important new thing this phase adds — if you see it, the
     headline feature works.

6. *(Bonus — optional, up to 2 more minutes)* Keep watching the same replay.
   - **Expect (if it happens):** A small gray banner appears directly below the chart starting with
     "Inside R-band" or "Inside S-band" and ending "measured history: edge report." This chip is
     timing-dependent — it only appears at the exact moment price sits inside the band AND the tape
     reading matches. **If it does not appear in this window, that is expected and not a sign of a
     bug** — do not treat this bonus step as pass/fail.

7. Click "Stop". Click the "Live" button, type `AAPL` into the symbol field, and click "Watch".
   - **Expect:** No "Price Chart — Tape-State Markers" panel appears anywhere on the page (scroll to
     confirm) — regardless of whether the real market happens to be open or closed right now, this
     panel must be completely absent in Live mode, exactly as it always was before this phase.

8. Look at the very top of the page, above the "Tapeology" header row.
   - **Expect:** Exactly 5 navigation links: "Cockpit", "Journal", "Studies", "Performance",
     "Structure" — nothing new was added.

---

## What "Working Correctly" Looks Like

- Watching `SIM-BUYER` shows the chart with an honest "No tradable map for SIM-BUYER." message —
  never a fake band line.
- Watching `AAPL` in Historical mode over 22-06-2026 shows one or more solid rose/green price lines
  near $300 on top of the candlestick chart.
- Live mode never shows the price-chart panel at all, no matter the symbol.

## Common Issues

- **Blank page / error screen**: Check the backend is running — `curl http://localhost:8301/health`
  should return a JSON response, not a connection error.
- **"Real-data provider unavailable" panel instead of the AAPL chart in step 4**: this environment's
  Alpaca credentials are not configured/reachable right now — this is an honest block, not a bug;
  steps 1-2 and 7-8 (which use only the built-in `SIM-BUYER` scenario) still fully verify the phase
  without needing real credentials.
- **No band line appears in step 5**: confirm you actually selected "Historical" (not "Simulated")
  and that the date field shows `22-06-2026` before you clicked the RTH quick-pick button — a band
  overlay never appears for a SIM ticker (see step 2) or before a valid Historical window is set.
- **The gray chip banner never appears in step 6**: expected — see the note in step 6 itself.
