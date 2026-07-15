# Phase goal-tradable_wall-iter-8 — What to Click (Operator Verification Guide)

**Phase:** goal-tradable_wall-iter-8
**Time required:** ~5 minutes of hands-on clicking, plus a background wait of up to ~20 minutes
baked into step 2 (you do other things in steps 3-5 while it runs in another tab — this is a known,
documented delay, not a bug; see step 2's note).
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3301`; backend running at `http://localhost:8301`.
- No login is required anywhere in this app.
- This backend already has 11 real recorded market-data windows on disk from the operator's own
  prior recording session (including a pinned AAPL 2026-06-22 window) — nothing new to set up.
- Patience for one slow step: step 2 below intentionally takes up to ~20 minutes to finish loading.
  This is a known, documented computation time (it replays real recorded tick data from scratch),
  not something broken. A second, much longer computation (Edge Report, up to 10+ hours) is only
  smoke-checked in step 6 below — you are not expected to wait for it to finish in this guide.

---

## Verification Steps

1. Open `http://localhost:3301/structure` in your browser.
   - **Expect:** The page loads with the heading "Structure" visible, no error banner, no blank page.

2. In the "Case Studies" panel, type `AAPL` into the "Symbol" field, then click the table row whose
   "session" column reads `2026-06-22`.
   - **Expect:** A "Case Studies — drill-in" panel opens below the table showing a pulsing gray
     loading placeholder. **This is the slowest step in this guide — leave this tab open and don't
     touch it. Continue to step 3 in a new browser tab while this one keeps loading in the
     background** (budget up to ~20 minutes before checking back in step 5).

3. Open a **new tab** and go to `http://localhost:3301/`.
   - **Expect:** The cockpit loads with no error banner. The "Simulated" button (top area, next to
     "Tapeology") is already selected.

4. Type `SIM-BUYER` into the "Ticker" field, then click the green "Watch" button.
   - **Expect:** A panel titled "Price Chart — Tape-State Markers" appears with a candlestick chart.
     Directly below the chart, a small gray line of text reads exactly **"No tradable map for
     SIM-BUYER."** — there should be no colored band line and no other gray banner beneath it.

5. Click "Stop", then click "Live", type `AAPL` into the symbol field, and click "Watch".
   - **Expect:** No "Price Chart — Tape-State Markers" panel appears anywhere on the page (scroll to
     confirm) — this panel must be completely absent in Live mode, exactly as it always was before
     this phase.

6. Go back to the `/structure` tab from step 2 (do not reload it). Scroll down past "Case Studies"
   to the "Edge Report" panel.
   - **Expect:** A pulsing gray loading placeholder is visible here too. This confirms it started
     correctly — **do not wait for this one to finish now** (it can legitimately take 10+ hours) and
     **do not reload the page** (reloading restarts this computation from zero).

7. Check the Case Studies drill-in from step 2 (same tab, still not reloaded). If at least ~20
   minutes have passed since step 2, look at the "Tape timeline" area inside the drill-in panel.
   - **Expect:** A list of multiple dated entries, each showing a timestamp and a state name like
     `buyer_control`, `seller_control`, `bid_absorption`, or `ask_absorption` — **not** the message
     "No recorded tape for this event." (If less than ~20 minutes have passed, it may still be
     loading — that's expected, not broken; check back later rather than reloading.)

---

## What "Working Correctly" Looks Like

- The AAPL 2026-06-22 Case Studies drill-in eventually shows a real list of tape-timeline entries
  (state names + timestamps) once it finishes loading — never the "No recorded tape for this event."
  placeholder for this specific pinned case.
- The Edge Report panel shows its pulsing loading placeholder immediately when `/structure` loads —
  confirming it started; full population is a separate, much longer check not covered by this guide.
- Watching `SIM-BUYER` shows the chart with the honest "No tradable map for SIM-BUYER." message —
  never a fake band line.
- Live mode never shows the Price Chart panel at all, no matter the symbol.

## If Something Looks Wrong

- **Blank page / error screen anywhere**: check the backend is running —
  `curl http://localhost:8301/health` should return a JSON response, not a connection error.
- **The Case Studies drill-in (step 2) is still on its loading placeholder after ~25-30 minutes**:
  this is longer than the documented estimate (~13 minutes measured) and may be worth flagging —
  but anything under ~20 minutes is expected, not a bug, since this replays the entire recorded
  window from scratch with nothing cached.
- **The Edge Report panel (step 6) never even shows its loading placeholder, or shows a red "could
  not be loaded" panel instead**: worth flagging — it should always reach its loading state almost
  instantly, even though full completion is a separate, very long wait.
- **You reloaded `/structure` while waiting**: this restarts both the Case Studies drill-in (you'll
  need to click the row again) and the Edge Report computation (starts over from zero) — avoid
  reloading that tab if you want to preserve progress.
- **No band line or chip appears anywhere in steps 3-5**: expected for `SIM-BUYER` (step 4 — SIM
  tickers never have a tradable map) — this only matters if you separately try a real historical
  AAPL replay, which is not part of this 5-minute guide.
