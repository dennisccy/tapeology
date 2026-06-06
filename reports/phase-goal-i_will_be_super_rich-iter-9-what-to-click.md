# Phase goal-i_will_be_super_rich-iter-9 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_super_rich-iter-9
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend running (required for steps 1–5; intentionally stopped for step 6)
- No login required

---

## Verification Steps

1. Open `http://localhost:3650` in your browser
   - **Expect:** The Tapeology page loads. A TopBar with "SIM", "LIVE", "HIST" tabs, a symbol input field, and a "Watch" button are visible. The cockpit area shows an idle placeholder. No red error banner.

2. With the "SIM" tab active, clear the symbol input field completely, then look at the Watch button
   - **Expect:** The Watch button is grayed out (disabled). Amber text "Enter a ticker symbol" appears immediately beside the Watch button — no click needed, no page reload.
   - **Broken looks like:** Watch button is still clickable, or no text appears near the Watch button.

3. Type `SIM-BUYER` into the symbol input field (do NOT click Watch yet)
   - **Expect:** The amber "Enter a ticker symbol" message disappears the instant you type the first character. The Watch button becomes active (no longer grayed out).
   - **Broken looks like:** The amber message stays visible after typing, or the Watch button remains grayed out.

4. Click the "Watch" button
   - **Expect:** Within approximately 1 second, the cockpit area changes from the idle placeholder to a state showing an amber pulsing dot and the text "Connecting to SIM-BUYER…". The idle placeholder ("No ticker watched") is no longer visible.
   - **Broken looks like:** The idle screen stays visible for more than 2–3 seconds after clicking Watch, or the cockpit stays blank.

5. Wait up to 10 seconds for the cockpit to populate
   - **Expect:** The "Connecting to SIM-BUYER…" state is replaced by a fully populated cockpit with at least one tape row and a confidence score. The TopBar status dot changes from "connecting" to an active state.
   - **Broken looks like:** The "Connecting to SIM-BUYER…" state never resolves, or the cockpit remains empty.

6. Click the "HIST" tab, then leave the start/end date fields blank with a symbol typed in the symbol field — type `AAPL` if the field is empty
   - **Expect:** The Watch button is grayed out (disabled) and amber text "Choose a valid time window" appears beside it.
   - **Broken looks like:** Watch button is still clickable, or no message about the time window appears.

7. Stop the backend server, then navigate back to `http://localhost:3650`, switch to the "SIM" tab, type `SIM-BUYER`, and click "Watch"
   - **Expect:** The cockpit immediately shows "Connecting to SIM-BUYER…" (within 1 second), then within approximately 12 seconds transitions to an error state. A rose-colored error banner appears below the TopBar header containing the word "timed out" or "Couldn't connect". The UI does not freeze or show an infinite spinner.
   - **Broken looks like:** The cockpit stays on the idle screen after clicking Watch, or the "Connecting to SIM-BUYER…" state never resolves even after 15 seconds.

---

## What "Working Correctly" Looks Like

- The cockpit area transitions away from idle to "Connecting to \<SYMBOL\>…" within 1 second of every Watch click
- Inline amber validation text appears beside the Watch button whenever the symbol is empty or the Historical time window is missing — no click needed to trigger it, and it clears the instant valid input is entered
- When the connection fails (backend stopped or unreachable), a rose panel with "Couldn't connect to the tape stream" and the instruction "Try Watch again" appears in the cockpit, and the TopBar error banner shows a message containing "timed out" or "Couldn't connect"
- The TopBar status dot turns rose/red and shows the label "failed" after a stream connection failure (not "connecting" or "closed")

## Common Issues

- **Idle screen persists after clicking Watch**: Confirm the backend is running (`curl http://localhost:3650/api/health` or check the backend terminal). If the backend is up but the screen does not change within 2 seconds, the pending/connecting state may not have been implemented correctly.
- **Inline validation message not appearing**: Ensure the symbol input field is fully empty (no spaces). If spaces remain, the field may look empty but still contain whitespace — select all and delete.
- **"Connecting to…" state never resolves**: If the backend is running and data should flow, wait up to 15 seconds. If still stuck, check the browser console for errors. This may indicate the stream-failure path is not rendering correctly.
- **Error banner does not appear after stopping the backend**: The frontend client-side timeout fires after approximately 12 seconds. If no error appears after 15 seconds, the `AbortController` timeout may not be wired correctly.
