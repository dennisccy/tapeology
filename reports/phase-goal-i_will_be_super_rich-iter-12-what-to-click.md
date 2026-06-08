# Phase goal-i_will_be_super_rich-iter-12 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_super_rich-iter-12
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend running at `http://localhost:8000`
- No login required — the app is unauthenticated
- No seed data required for simulated mode; historical mode requires market data for `AAPL` on `08-01-2024`

---

## Verification Steps

1. Open `http://localhost:3650/` in your browser
   - **Expect:** The cockpit page loads. A price chart pane and a control row are visible. The date field (in Historical mode) shows a plain text box with placeholder text `dd-MM-yyyy` — no browser calendar popup control.
   - **Broken looks like:** A calendar icon or native OS date-picker appears when you click the date field, OR the page shows a blank screen or error banner.

2. Clear the ticker field, type `SIM-BUYER`, then click the "Watch" button
   - **Expect:** Bars begin appearing in the price chart within 30 seconds. The horizontal axis tick labels read dates and times such as `02-01-2024 09:30:00` — NOT bare numbers like `0`, `60`, or `120`.
   - **Broken looks like:** The axis shows numbers such as `0`, `60`, `120`, `600` with no date portion, OR the format reads `2024-01-02` (ISO), OR no bars appear after 60 seconds.

3. Move your mouse over the center of the candlestick bars until the crosshair appears
   - **Expect:** The crosshair legend or tooltip shows a timestamp in `dd-MM-yyyy HH:mm:ss` format (e.g., `02-01-2024 09:30:45`).
   - **Broken looks like:** The crosshair shows a bare number like `45` or an ISO timestamp like `2024-01-02T09:30:45Z`.

4. Click the `60` bar-size button (the control labeled `60` for 60-second bars)
   - **Expect:** The chart re-renders with wider bars. The horizontal axis tick labels still show `dd-MM-yyyy HH:mm:ss` format — the format does NOT revert to elapsed seconds.
   - **Broken looks like:** After switching bar size the axis reverts to numbers like `0`, `60`, `120`.

5. In the Historical mode controls, click the date field, clear it, and type `31-02-2026`, then click away from the field
   - **Expect:** The date field border turns amber (orange/yellow highlight). An inline error message appears near the field (e.g., "Invalid date" or "Date does not exist"). The "Watch" button is grayed out and cannot be clicked.
   - **Broken looks like:** No color change on the field, no error message, or the Watch button becomes active despite the invalid date.

6. Clear the date field and type `08-01-2024`, then click the "Watch" button (ensure ticker is `AAPL`)
   - **Expect:** The error state clears. Bars load for AAPL on January 8, 2024. The watched-source descriptor at the top of the cockpit reads something like `historical AAPL 08-01-2024 09:30` — using `dd-MM-yyyy` notation, NOT a raw ISO string like `2024-01-08T13:30:00.000Z`.
   - **Broken looks like:** The descriptor shows `2024-01-08T13:30:00.000Z` or the chart loads data for the wrong date (indicating a UTC shift).

7. Locate the market-status indicator panel (top area of the page) and read any "next open" or "market closed" time shown
   - **Expect:** The time appears in the format `dd-MM-yyyy HH:mm UTC+HH:MM` (e.g., `09-06-2026 09:30 UTC+08:00`). No locale shorthand like `Jun 9` or ISO format `2026-06-09` is visible.
   - **Broken looks like:** The status panel shows a date in "Jun 9" style, "6/9/2026", or bare ISO `2026-06-09` format.

---

## What "Working Correctly" Looks Like

- The price chart time axis reads real clock dates (e.g., `02-01-2024 09:30:00`) for both simulated and historical modes — never a 0-to-600 elapsed-seconds counter
- The Historical date field is a plain text input accepting `dd-MM-yyyy`; impossible dates trigger an amber border and inline error; the Watch button stays disabled until the date is valid
- All dates and times across the cockpit (chart axis, crosshair, tape-state markers, market-status panel, watched-source descriptor) use the unified `dd-MM-yyyy` or `dd-MM-yyyy HH:mm:ss` format

## Common Issues

- **Bars never appear for SIM-BUYER:** Check that the backend is running (`curl http://localhost:8000/health`) and that the watch was triggered by clicking "Watch" after typing the ticker
- **Date field still shows a calendar popup:** The old native `<input type="date">` may still be in the bundle — verify the frontend was rebuilt after the iteration's changes; check that the running Next.js server is serving the latest build
- **Axis still shows elapsed seconds (0, 60, 120):** The frontend may be running a stale build or the backend `/history` endpoint may not be returning `epoch_anchor`. Check the browser's Network tab for the `/api/tape/SIM-BUYER/history` response and confirm it contains an `epoch_anchor` field with a non-null numeric value
