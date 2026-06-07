# Phase goal-i_will_be_super_rich-iter-10 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_super_rich-iter-10
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend running (Simulated mode must work; check with a normal `SIM-BUYER` watch first)
- No login required

---

## Verification Steps

1. Open `http://localhost:3650` in your browser
   - **Expect:** The idle/home screen loads — a symbol input field and a "Watch" button are visible. No error overlay. No blank screen.

2. Type `SIM-BUYER` into the symbol input field and click the "Watch" button
   - **Expect:** Within ~1 second the idle screen disappears and a "Connecting…" message or the cockpit begins to load. Within ~10 seconds the full cockpit is visible with populated panels (Quote, Trades, Features, TapeState). The TopBar status dot reads "live" (green). The TapeState panel shows "buyer_control" (or "Buyer Control").
   - **Broken if:** The idle screen persists for more than 1–2 seconds after clicking Watch, OR the cockpit shows blank/zeroed panels under a green "live" dot, OR the "buyer_control" state is missing.

3. Click the "Stop" button (or navigate back to idle) to clear the current watch, then type `WAIT-TEST` into the symbol field and click "Watch"
   - **Expect:** Within ~1 second the idle screen leaves. A waiting treatment screen appears in the cockpit area. The screen contains the text "waiting for the first trade" and includes the symbol name `WAIT-TEST` and a mode label (e.g., "Simulated" or "sim"). The full panel grid (Quote, Trades, Features, etc.) is NOT shown — only the waiting message.
   - **Broken if:** The cockpit shows a blank panel grid instead of the waiting message, OR the status dot reads "live" (green) while the waiting screen is visible, OR the idle screen does not change at all.

4. While the waiting screen from step 3 is visible, look at the TopBar status dot (small coloured badge near the top of the page)
   - **Expect:** The status dot is amber/yellow and pulsing (animated). The label next to or within the dot reads "waiting" — NOT "live", NOT "connecting".
   - **Broken if:** The dot reads "live" or remains on "connecting" after the stream has opened, OR the dot is green instead of amber.

5. Locate the data-source mode selector (dropdown or tab near the top of the page). Click through "Live", "Historical", and "Simulated" modes in sequence
   - **Expect:** Each mode shows the correct controls: Live shows a symbol search (no date picker); Historical shows a symbol search AND a date/window picker; Simulated shows a plain ticker input (no date picker). Switching modes does not crash the page or produce an error overlay.

6. In Simulated mode, type `SIM-BUYER` and click "Watch" again to confirm no regression
   - **Expect:** The cockpit returns to the full buyer_control state with populated panels. Status dot reads "live" (green).

7. Attempt a Watch with the symbol field left empty — click the "Watch" button without typing anything
   - **Expect:** Either the Watch button is disabled/greyed out when the field is empty, OR an inline validation message appears (e.g., "Enter a ticker symbol") near the field. The idle screen remains; the app does NOT silently do nothing.

---

## What "Working Correctly" Looks Like

- After clicking Watch on `WAIT-TEST`: a centred screen appears with amber pulsing dot in the TopBar and text containing both the ticker symbol and the phrase "waiting for the first trade". No blank panel grid. No green "live" dot.
- After clicking Watch on `SIM-BUYER`: the full cockpit populates within ~10 seconds, the TapeState panel reads "buyer_control", and the status dot turns green ("live").
- Empty Watch submit: either the Watch button is non-clickable, or a validation hint appears immediately below the input field.

## Common Issues

- **Idle screen never leaves after clicking Watch**: Check that the backend is running. Try `curl http://localhost:8650/health` (or the backend's health endpoint) in a terminal.
- **Blank cockpit panels under a green "live" dot**: This is the exact regression this iteration fixes. If you see it, the `WaitingState` component is not being rendered — check the frontend build.
- **Waiting screen appears but reads "live" in the TopBar**: The `STREAM_DOT` `waiting` entry in TopBar may not be deployed. Verify the frontend is running the latest build.
- **`SIM-BUYER` shows waiting screen instead of full cockpit**: The `waiting → live` rung promotion on first event may be broken in the backend engine. Check backend logs.
