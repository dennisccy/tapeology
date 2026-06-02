# Phase goal-i_will_be_rich-iter-1 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_rich-iter-1
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend (API) running at `http://localhost:8000` — the cockpit pulls all data from it
- No login or seed data required (the `SIM-BUYER` scenario is built in)

---

## Verification Steps

1. Open `http://localhost:3650/` in your browser
   - **Expect:** The **Tapeology** top bar with a ticker input and a green **Watch** button; the center reads **"No ticker watched"** with the hint **"Try: SIM-BUYER"**; the footer says **"Descriptive only — not trading advice."**
   - **Expect:** NO numbers anywhere (no bid/ask, no tape state, no trades) — the empty state is honest.

2. Click the ticker input, type `SIM-BUYER`, and click **Watch**
   - **Expect:** A **"Watching SIM-BUYER"** label appears; a chip reads **"scenario: buyer_control"**; the status indicator at top-right goes from **idle** → **connecting** → **live** (green dot).

3. Look at the six-panel grid that replaces the empty state
   - **Expect:** Six panels appear — **Tape State**, **Quote**, **Features**, **Recent Trades**, **Observations**, **Event Log**.

4. Read the **Quote** panel
   - **Expect:** **Bid** (green) and **Ask** (red) are numbers, plus **Spread** and **Last**; `Spread` ≈ `Ask − Bid`.

5. Read the **Tape State** panel (wait ~10–15 seconds if it still says "Warming up…")
   - **Expect:** Large green label **"Buyer Control"** with a **Confidence** decimal (e.g. `0.82`) and a green confidence bar.

6. Read the **Features** panel, then click the **10s** tab and the **300s** tab
   - **Expect:** Nine metrics show numbers; **Aggressive buy ratio** is high and **Buy price impact** is positive (green); the feature values change when you switch window tabs.

7. Read the **Event Log** panel
   - **Expect:** A line **"Tape state changed to buyer_control"** (newest entries at the top).

8. Watch any panel for ~5–10 seconds WITHOUT refreshing the page
   - **Expect:** New trade rows / updated feature numbers appear on their own (live over WebSocket); the page never reloads and the status dot stays green/"live".

9. (Honesty check) Refresh the page, type `NOPE`, and click **Watch**
   - **Expect:** A red error message in the top bar (e.g. **"'NOPE' could not be watched"**); NO panels appear and NO numbers are shown — it errors instead of faking data.

---

## What "Working Correctly" Looks Like

- After watching `SIM-BUYER`, the **Tape State** reads **Buyer Control** in green with a visible confidence bar, and the **Event Log** shows the `buyer_control` transition.
- Numbers update live (new trades, changing feature values) with no page reload.
- An unknown ticker (`NOPE`) produces a clear error and never any fabricated bid/ask/state values.

## Common Issues

- **Blank page or panels stuck empty / "Connecting…":** confirm the backend is running — `curl http://localhost:8000/tape/SIM-BUYER/state` should return JSON after watching. If the top bar shows **"Backend unreachable — is the API running?"**, the API is down.
- **Tape State stays "Warming up…":** give it 10–20 seconds; the engine needs a minimum number of events before it makes a directional call (this is intentional, not a bug).
- **Status dot stuck on amber ("connecting"):** the WebSocket isn't connecting — check the backend is reachable at `http://localhost:8000` and that `NEXT_PUBLIC_API_URL` points to it.
