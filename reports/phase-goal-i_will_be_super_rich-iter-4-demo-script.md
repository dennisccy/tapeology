# Demo Script — goal-i_will_be_super_rich-iter-4

**Mode:** record
**Date:** 2026-06-04
**Frontend URL:** http://localhost:3650
**Iteration:** 4

## Highlights

### Step 01 — Open Tapeology

- **Narration:** Tapeology watches a single US stock and tells you, in plain language, what the order flow is doing right now. We start on the idle home screen, before any ticker is being watched.
- **Action:** Navigate to /
- **Point out:** The top bar holds a status dot and a Live / Historical / Simulated source selector; the body invites you to enter a ticker.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-4/step-01.png

### Step 03 — Read the practice tape

- **Narration:** Press Watch and the single-ticker cockpit comes alive: here the simulated tape is clearly buyer-controlled, shown with a confidence score, a live quote, recent trades, the core flow features, plain-language observations, and an event log.
- **Action:** Click the "Watch" button
- **Point out:** The Tape State reads "Buyer Control" with a full confidence bar — the product's plain-language verdict on the order flow.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-4/step-03.png

### Step 10 — Replay the real session

- **Narration:** Press Watch and Apple's real trades and quotes from that window replay through the same engine — same cockpit, same readouts, now driven by genuine market data.
- **Action:** Click the "Watch" button
- **Point out:** The source label reads "historical AAPL ..." and the cockpit fills with the real replayed tape; a wide, mixed read honestly shows as "Unclear" rather than a forced call.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-4/step-10.png

### Step 11 — Go Live

- **Narration:** Live mode is where this update lands. Switching to Live shows the real US market session right in the top bar and reveals the live symbol search.
- **Action:** Click the "Live" button
- **Point out:** A "market" status chip shows the real session — open, or closed with the next open time — beside the live symbol search box.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-4/step-11.png

### Step 12 — Find a stock by search

- **Narration:** Start typing and a real symbol search suggests matches as you go — here "AAP" surfaces Apple and its relatives, each with its full company name.
- **Action:** Type "AAP" into the "Symbol search" field
- **Point out:** A live suggestions dropdown lists real matches like "AAPL — Apple Inc. Common Stock".
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-4/step-12.png

### Step 14 — Stream Ford live  [NEW]

- **Narration:** This is the new capability: press Watch during market hours and Ford's real-time trades and quotes stream straight into the cockpit, with the status dot glowing emerald "live" and the source labelled "live F". Outside market hours it says so honestly, never a fake cockpit.
- **Action:** Click the "Watch" button
- **Point out:** An emerald "live" status dot and a "scenario: live F" label over a cockpit fed by the real market — or, off-hours, a plain "Market is closed" message with the next open time.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-4/step-14.png

### Step 16 — Honest "stale" — no invented trades  [NEW]

- **Narration:** With no trades arriving, the status dot turns amber and reads "stale" once the quiet passes the configured window — and crucially it invents zero trades to fill the silence, flipping back to "live" only when real data resumes.
- **Action:** Click the "Watch" button
- **Point out:** An amber "stale" dot with an empty trade list — proof the product reports a feed gap honestly instead of fabricating activity.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-4/step-16.png

## Full tour (text only)

### Step 02 — Type a practice ticker

- **Narration:** Simulated mode is selected by default — a deterministic practice feed for trying the read without touching real market data. We type the built-in SIM-BUYER scenario into the ticker box.
- **Action:** Type "SIM-BUYER" into the "Ticker" field
- **Point out:** The ticker field now holds SIM-BUYER, ready to watch.

### Step 04 — Stop watching

- **Narration:** One click on Stop tears the watch down completely and returns to the idle screen — no leftover stream left running in the background.
- **Action:** Click the "Stop watching" button
- **Point out:** We are back to "No ticker watched", a clean slate for the next source.

### Step 05 — Switch to real historical data

- **Narration:** Now to real market data. Historical mode replays a real past trading session through the very same engine — you choose a stock, a date, and a time window.
- **Action:** Click the "Historical" button
- **Point out:** New controls appear: a symbol box, a date, a start and end time, and a replay speed.

### Step 06 — Pick a real stock

- **Narration:** We choose Apple (AAPL) — a real, tradable US stock — for the replay.
- **Action:** Type "AAPL" into the "Symbol search" field
- **Point out:** The symbol box accepts the real ticker.

### Step 07 — Choose the session date

- **Narration:** We set the date to a recent past trading session.
- **Action:** Type "2026-06-03" into the "Date" field
- **Point out:** The date field is set.

### Step 08 — Set the window start

- **Narration:** Then a short two-minute window within that session, starting at 15:00.
- **Action:** Type "15:00" into the "Start time" field
- **Point out:** The start time is set.

### Step 09 — Set the window end

- **Narration:** ...and ending at 15:02.
- **Action:** Type "15:02" into the "End time" field
- **Point out:** The replay window is now 15:00 to 15:02.

### Step 13 — Choose a live ticker

- **Narration:** For the live read we pick Ford (F) — a heavily traded name with a tight penny spread, which makes for a clean real-time tape.
- **Action:** Type "F" into the "Symbol search" field
- **Point out:** The symbol box now holds F, with Ford Motor Company suggested.

### Step 15 — Watch a deliberately quiet feed

- **Narration:** To show the honesty guarantee when a live feed goes quiet, we point Live at a deliberately silent test symbol that does not print on the public feed.
- **Action:** Type "ZZZQQ" into the "Symbol search" field
- **Point out:** The symbol box holds ZZZQQ, a feed with no incoming trades.
