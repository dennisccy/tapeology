# Delivered — Tapeology: Real-Time Tape Reading for US Stocks

**Session:** i_will_be_super_rich
**Date:** 2026-06-09
**Final verdict:** GOAL_ACHIEVED
**Iterations:** 13

## What you can do today

- Watch any US stock one at a time and get a plain-language read of the order flow: buyer in control, seller in control, bid or ask absorption (the price refusing to move despite heavy one-sided pressure), or an unclear tape — each with a confidence score.
- See the full cockpit for any watched ticker: live bid, ask, spread, and last price; a running list of recent trades labeled buy or sell; all the underlying order-flow features; plain-language observations; and a live event log that announces state changes as they happen.
- Choose where the data comes from: simulated practice mode (no account needed), a real past session replayed at a speed you pick, or a real live feed during market hours.
- Search for a stock by name or partial ticker — results appear immediately, even the very first search after the app starts.
- Pick a historical window in your own local time zone using a custom day-month-year date field, or click one button to jump to the market open (9:30 ET), the market close (4:00 PM ET), or the full trading day — each preset shows both the New York time and your local-time equivalent.
- See dates in the familiar day-month-year format (for example, "08-01-2024") consistently everywhere in the product.
- Watch a candlestick price chart above the cockpit in simulated and historical modes, with real market clock times on the axis, colored markers at each significant tape-state transition (green for buyer control, rose for seller control, amber for absorption), and a 10/30/60-second bar-size selector.
- Change the replay speed (1x, 2x, 5x, or 10x) while a historical session is actively replaying — the new pace takes effect within about one second with no restart or reload.
- Load long historical windows, including the full trading day for busy stocks, without hitting a "very high-volume" error.
- Pause a running watch to study the chart at a specific moment, then resume from exactly where you left off — no data is invented to fill the gap.
- See an honest market-status indicator in Live mode, and an amber "stale" signal if the feed goes quiet, with no invented data during the lull.
- Get immediate feedback on every Watch click: a "Connecting…" acknowledgement within one second, a clear actionable error if something fails, an honest "waiting" state if the stream is open but quiet, and an inline hint if your input is invalid.
- Re-watch the same symbol and historical window near-instantly from a local cache.
- Know that no data is ever invented: unknown symbols, empty windows, a closed market, missing credentials, and feed gaps each give you a distinct honest screen, never a fake cockpit.

## How it came together

The project began with a deterministic practice simulator that proved the hardest ideas before any real market data was involved. A single-ticker cockpit took shape: a live quote, a running trade list, core order-flow metrics, a confidence score, plain-language observations, and an event log. Two defining principles were established early — the engine reads price impact rather than raw aggression (so heavy one-sided volume that does not move the price reads as absorption, not control), and the system never invents a reading when evidence is weak or missing.

With the simulator working, real US equity data entered the picture. A data-source selector appeared at the top of the screen. Historical replay arrived first — pick a real stock and a past date-and-time window, and the real trades and quotes flow through the same unchanged engine. Symbol search followed, backed by real vendor data. The market-clock integration brought an honest "market is closed" state and a live status indicator. Then live streaming itself arrived: during market hours, a real feed streams trades and quotes with an honest amber "stale" light when the feed goes quiet.

The product then grew across several quality waves. A two-stage classifier resolved most real trades to buy or sell instead of "unknown," sharpening the directional read. A candlestick price chart with tape-state markers and a bar-size selector appeared above the cockpit for simulated and historical sessions. Pause and resume arrived, along with a local-time historical picker with one-click US-session presets — fixing an earlier UTC conversion gap. The Watch click was hardened so every action gives immediate visible acknowledgement, every failure resolves to an explicit screen, and invalid input is caught before any network call is made.

Then vendor responsiveness came to full strength: historical windows load fast by design (concurrent trades-and-quotes fetching, a window cache for near-instant replays, a symbol universe pre-loaded at startup). Finally the last three refinements completed the picture: the chart axis now shows real clock times in day-month-year format; replay speed can be changed mid-replay without stopping; long historical windows including the full trading day load by splitting the fetch into parallel bounded chunks; and the classifier now judges spread and price impact relative to each stock's own price level, so a genuine directional move on a real stock reads correctly as buyer or seller control rather than being stuck on "unclear."

## Watch it work

A full narrated walkthrough is embedded on the page that holds this document.
Open it in your browser to see the product in action.
