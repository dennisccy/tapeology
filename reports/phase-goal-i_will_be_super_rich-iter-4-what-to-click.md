# Phase goal-i_will_be_super_rich-iter-4 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_super_rich-iter-4
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend running at `http://localhost:8000`
- **For the real live watch (step 4):** US market must be **open** AND Alpaca credentials
  configured in the backend. If the market is closed or credentials are absent, the live watch
  will show an honest message instead — that is the expected, correct behavior (see step 5),
  not a failure.

---

## Verification Steps

<!-- Prioritized: 1) the new Live capability, 2) honest gated states, 3) sim regression. -->

1. Open `http://localhost:3650` in your browser
   - **Expect:** The screen loads with a TopBar (status dot) and a data-source/mode selector. No error overlay.

2. Open the data-source selector and choose **Live**
   - **Expect:** A symbol search field and a market-status indicator appear (status shows open, or closed + next open time).

3. Type `AAPL` in the symbol search field and select it from the suggestions
   - **Expect:** The symbol box fills with `AAPL`; a matching suggestion list appeared while typing.

4. Type/select `F` as the symbol, then click **Watch**
   - **Expect (market open + creds):** The cockpit mounts (tape panels appear), the status dot turns **emerald**, and the source label reads `scenario: live F`. This is the headline new capability — before this iteration this exact click showed an error and no cockpit.
   - **Expect (market closed or no creds):** No cockpit; instead an honest message — **"market is closed"** (with next open time) or **"provider unavailable"**. This is correct behavior, not a bug.

5. (Only if a live watch started in step 4) Stop interacting and watch the status dot for ~15 seconds during any lull in trades
   - **Expect:** If no live trade arrives for longer than ~10s, the dot turns **amber** (`stale`) and the recent-trades count does NOT grow; it returns to **emerald** when trades resume. No invented trades.

6. Click the **Stop** button
   - **Expect:** The cockpit clears and the status dot returns to `closed`. The watch is fully torn down (no leftover stream).

7. Open the data-source selector, choose **Sim**, select the **SIM-BUYER** scenario, click **Watch**
   - **Expect:** The cockpit mounts and the tape state reads `buyer_control` with a populated confidence bar — confirms the existing sim path still works (no regression).

---

## What "Working Correctly" Looks Like

- In Live mode with the market open + creds: a cockpit with live tape, an **emerald** status dot, and the `scenario: live F` source label.
- In Live mode otherwise: a clear **"market is closed"** or **"provider unavailable"** message — and never a fake/simulated cockpit pretending to be live.
- Sim mode still classifies `SIM-BUYER` as `buyer_control`.

## Common Issues

- **Blank page / error screen:** Confirm the backend is up — `curl http://localhost:8000/health`.
- **Live Watch shows "provider unavailable" even at market open:** Alpaca credentials are not configured in the backend — this is the honest no-creds state, not a frontend bug.
- **Live Watch shows "market is closed":** The US market is closed right now. The real live/stale stream (steps 4–5) can only be browser-verified during market hours; the live→stale→live transition is otherwise covered by the backend hermetic tests.
- **Dot stays amber (`stale`):** Expected for a quiet symbol or off-peak moment — there is no auto-reconnect affordance; it recovers to `live` when real events resume.
