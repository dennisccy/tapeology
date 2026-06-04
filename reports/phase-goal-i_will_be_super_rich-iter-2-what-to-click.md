# Phase goal-i_will_be_super_rich-iter-2 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_super_rich-iter-2
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend running at `http://localhost:8000`
- **Real data is optional.** With Alpaca credentials configured (or a fixture-backed historical
  path), steps 3–5 show real suggestions and a real cockpit. **Without** credentials, those steps
  instead show the honest amber panel — that is the expected no-creds outcome, not a failure. Steps
  1–2 and 6–7 work either way.

---

## Verification Steps

1. Open `http://localhost:3650/` in your browser
   - **Expect:** Header shows "Tapeology"; a "Live / Historical / Simulated" control with "Simulated" highlighted; symbol box placeholder "Ticker e.g. SIM-BUYER"; main area reads "No ticker watched"

2. Click "Simulated" (if not already selected), type `SIM-BUYER` in the symbol box, click the green "Watch" button
   - **Expect:** Header shows "Watching SIM-BUYER"; the cockpit fills with quote/trades/features and a tape state; the state reaches `buyer_control` as it plays (confirms the sim path did NOT regress)

3. Click the red "Stop" button, then click "Historical"
   - **Expect:** Cockpit clears back to "No ticker watched"; the symbol box placeholder changes to "Symbol e.g. AAPL"; Date, Start time, End time, and a Replay-speed dropdown appear

4. Type `AAP` in the symbol box and wait ~¼ second (do not press Enter)
   - **Expect (with creds):** A dropdown appears with rows like `AAPL` on the left and `Apple Inc` on the right
   - **Expect (no creds):** No dropdown — this is fine; continue with free text
   - **Broken looks like:** a dropdown of made-up tickers with no company names, or a JavaScript error

5. Clear the box, type `F`, set Date + Start time + End time to a recent regular-market-hours window, choose `10×`, click "Watch"
   - **Expect (with data):** The cockpit fills with **real** bid/ask/spread/last, recent trades, features, tape state + confidence, observations, and an event log; the header chip reads `scenario: historical F …`
   - **Expect (no creds/empty window):** An amber panel ("Real-data provider unavailable" or "No data for that window") replaces the cockpit — never a fabricated tape

6. Click "Historical" (clear state), type `ZZZZNOPE`, fill any valid past window, click "Watch"
   - **Expect:** An amber panel titled "Symbol not tradable" with the phrase "not a tradable symbol"; NO cockpit; header does NOT say "Watching ZZZZNOPE"
   - **Broken looks like:** a cockpit appearing with invented numbers for a fake symbol

7. Click "Simulated" and confirm the symbol box has no suggestions dropdown when you type `SIM`
   - **Expect:** Plain "Ticker e.g. SIM-BUYER" input, NO dropdown, no Historical date/time controls — Simulated mode is unchanged

---

## What "Working Correctly" Looks Like

- Simulated mode behaves exactly as before (step 2/7): plain ticker input, SIM-BUYER classifies, Stop returns to idle
- Historical/Live symbol box offers a real suggestions dropdown (step 4) and selecting/typing both lead to a Watch
- Every real-data refusal shows a **distinct amber honest panel** (steps 5/6) in place of the cockpit — the cockpit is never shown next to a honest panel, and the app never invents a tape

## Common Issues

- **Blank page / error screen:** Confirm the backend is up — `curl http://localhost:8000/health`
- **No dropdown when typing in Historical/Live:** Most likely no Alpaca credentials configured; free-text Watch still works and the no-creds amber panel is the correct honest result
- **Historical Watch shows amber instead of a cockpit:** Expected without credentials or for an empty/closed window; try a known busy regular-hours window with credentials set
- **Suggestions dropdown appears in Simulated mode:** This is a regression — Simulated must keep the plain input
