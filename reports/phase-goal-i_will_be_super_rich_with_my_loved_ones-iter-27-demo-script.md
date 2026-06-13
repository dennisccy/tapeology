# Demo Script — goal-i_will_be_super_rich_with_my_loved_ones-iter-27

**Mode:** record
**Date:** 2026-06-13
**Frontend URL:** http://localhost:3650
**Iteration:** 27

## Highlights

### Step 01 — Open the tape cockpit

- **Narration:** This is Tapeology — a tape-reading cockpit for real US equities. Enter a symbol, pick a data source, and the cockpit streams every trade in real time.
- **Action:** Navigate to /
- **Point out:** The watch form with symbol input, source selector, and Watch button — ready for input.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-27/step-01.png

### Step 02 — Select Historical mode and pick a date

- **Narration:** Switch to Historical mode and type in a date to replay a real past session tick-by-tick. Tapeology fetches the actual SIP trade-and-quote feed — no simulated data.
- **Action:** Click the "Historical" radio
- **Point out:** The source selector now shows Historical, and the date input and time-window picker have appeared.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-27/step-02.png

### Step 03 — Open the time-window picker

- **Narration:** The time-window picker shows your local timezone and quick-pick buttons for common US market windows — Open 30, Last 1 hr, and more — so you never have to do mental timezone arithmetic.
- **Action:** Click the "Open 30" button
- **Point out:** The timezone label (Europe/London) and quick-pick buttons like 'Open 30' and 'Last 1 hr' inside the picker.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-27/step-03.png

### Step 04 — Watch AAPL historical — cockpit populates with real data

- **Narration:** Type AAPL, choose a recent trading day, and hit Watch. Within 30 seconds the cockpit fills with real bid, ask, spread, and last-price figures pulled straight from the SIP consolidated tape.
- **Action:** Type "AAPL" into the "Symbol" field
- **Point out:** Live bid/ask/spread/last numbers in the quote panel, a tape-state reading (e.g. Bullish), and the candlestick chart starting to build from the first bars.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-27/step-04.png

### Step 05 — Recent trades — every print has a side

- **Narration:** Scroll down to the recent-trades list. Every single print is stamped Buy or Sell — none are left as Unknown. The trade-side classifier runs on the full SIP quote feed, resolving each trade against the prevailing bid and ask.
- **Action:** Navigate to /
- **Point out:** The recent-trades list with Buy/Sell labels on every row and zero Unknown entries.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-27/step-05.png

### Step 06 — Price chart shows real clock times, not elapsed seconds

- **Narration:** The candlestick chart's time axis shows real market clock times — 09:30, 09:35 — anchored to the actual session open. Tape-state transition markers appear exactly where the engine detected a regime change.
- **Action:** Navigate to /
- **Point out:** Human-readable time labels on the chart x-axis (09:30, 09:35, etc.) and coloured tape-state marker flags at regime-change points.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-27/step-06.png

### Step 07 — Closed-market: honest panel instead of a spinner

- **Narration:** Try watching AAPL in Live mode when the US market is closed. Instead of an infinite spinner or silence, the cockpit tells you exactly when the next session opens — down to the minute, in your local timezone.
- **Action:** Click the "Live" radio
- **Point out:** The 'market is currently closed' panel with the next-open date and time shown in your local timezone.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-27/step-07.png

### Step 08 — Unknown symbol: clear rejection, no fabricated data

- **Narration:** Enter a nonsense ticker and Tapeology says so plainly — it is not a tradable symbol — rather than hanging or silently returning an empty cockpit. The honesty-first design means every edge case surfaces a real explanation.
- **Action:** Type "ZZZZNOTREAL" into the "Symbol" field
- **Point out:** The rejection panel with the plain-language message about the symbol not being tradable, and no cockpit panels populated.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich_with_my_loved_ones-iter-27/step-08.png
