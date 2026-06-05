# Demo Script — goal-i_will_be_super_rich-iter-7

**Mode:** record
**Date:** 2026-06-05
**Frontend URL:** http://localhost:3650

## Highlights

### Step 01 — Home page — idle state with Watch controls

- **Narration:** The Tapeology cockpit opens clean. The top bar shows the provider selector and Watch button, and the status indicator sits idle — no Pause or Resume button in sight until you actually start a watch.
- **Action:** Navigate to /
- **Point out:** Notice the grey idle dot top-right and that there are no Pause or Resume buttons anywhere in the header.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-7/step-01.png

### Step 02 — Start watching SIM-BUYER

- **Narration:** Type in SIM-BUYER and hit Watch. Within seconds the stream goes live — a green dot lights up in the top-right and an amber Pause button appears beside Stop.
- **Action:** Type "SIM-BUYER" into "Ticker"
- **Point out:** The amber Pause button is new this iteration. It sits right next to Stop in the watch-control cluster.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-7/step-02.png

### Step 03 — Click Watch to start the stream

- **Narration:** Once Watch is clicked the cockpit comes alive: quote prices, recent trades, and feature counters begin populating in real time.
- **Action:** Click the "Watch" button
- **Point out:** The green live dot and the Pause button both appear once the stream connects.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-7/step-03.png

### Step 04 — Pause the live watch  [NEW]

- **Narration:** Click Pause and the cockpit freezes in place. Every panel — quote, recent trades, feature counters, tape state, and the price chart — holds its last values. The stream stays alive in the background; nothing is closed.
- **Action:** Click the "Pause" button
- **Point out:** The amber dot now says 'paused' instead of 'live', and the Pause button has been replaced by a Resume button.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-7/step-04.png

### Step 05 — Cockpit frozen — data intact while paused  [NEW]

- **Narration:** While paused you can read the snapshot at your own pace. Trade counts, quote prices, and chart candles are completely frozen — no new data appears even after several seconds.
- **Action:** Navigate to /
- **Point out:** The amber 'paused' dot in the top-right confirms the stream is frozen, yet all panel data remains fully visible and readable.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-7/step-05.png

### Step 06 — Resume the stream  [NEW]

- **Narration:** Click Resume and the cockpit picks up right where it left off. The green live dot returns immediately, and new trades trickle in at the normal one-per-second cadence — no sudden backfill spike.
- **Action:** Click the "Resume" button
- **Point out:** The Pause button reappears in place of Resume, and trade counts start incrementing again at a steady rate.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-7/step-06.png

### Step 07 — Price chart survives Pause and Resume

- **Narration:** The candlestick price chart with tape-state markers keeps rendering cleanly through the entire pause-resume cycle. No blank canvas, no reload, no lost candles.
- **Action:** Navigate to /
- **Point out:** Look for the PRICE CHART section below the cockpit — it should show candles with emerald markers for SIM-BUYER buyer-control signals.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-7/step-07.png

### Step 08 — Stop from any state — cockpit clears cleanly

- **Narration:** Whether the watch is live or paused, clicking Stop always closes the session completely. The watch-control cluster disappears, the cockpit returns to its idle placeholder, and the app is ready for a fresh watch.
- **Action:** Click the "Stop" button
- **Point out:** All buttons (Pause/Resume/Stop) vanish and the cockpit shows the 'No ticker watched' placeholder.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-7/step-08.png
