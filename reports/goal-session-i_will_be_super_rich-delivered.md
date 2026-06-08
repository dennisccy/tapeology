# Delivered — Tapeology: Real-Time Tape Reading for US Stocks

**Session:** i_will_be_super_rich
**Date:** 2026-06-07
**Final verdict:** GOAL_ACHIEVED
**Iterations:** 12 (iter-0 baseline through iter-11)

## What you can do today

- Watch any US stock one at a time and get a plain-language read of what the order flow is doing: whether buyers are in control, sellers are in control, heavy one-sided pressure is being absorbed while the price holds steady, or the tape is simply unclear — each with a confidence score.
- See the full cockpit for any watched ticker: live bid, ask, spread, and last price; a running list of recent trades labeled buy or sell; all the underlying order-flow features; plain-language observations; and a live event log that announces state changes as they happen.
- Choose where the data comes from: practice (simulated) mode, a real past session replayed at any speed, or a real live feed during market hours.
- Search for a stock by name or partial ticker — results appear immediately, even the very first search after the app starts.
- Pick a historical window in your own local time with one-click presets for the US market open (9:30 ET), the close (4:00 PM ET), and the full trading day — each preset shows your local-time equivalent.
- View a candlestick price chart above the cockpit in simulated and historical modes, with colored markers at each tape-state transition and a 10/30/60-second bar-size selector.
- Pause a running watch at any moment to study the screen, then resume from exactly where you left off — no data is invented to fill the gap.
- See an honest market-status indicator (open, closed with next open time, or unavailable) in Live mode.
- Get immediate feedback on every Watch click: a "Connecting…" acknowledgement within one second, a clear actionable error if something fails, an honest "waiting" state if the stream is open but quiet, and an inline hint if your input is invalid.
- Re-watch the same symbol and historical window near-instantly from a local cache.
- Receive a specific, actionable message when a window is too large to load ("try a shorter range") instead of a vague retry prompt.
- Know that no data is ever invented: unknown symbols, empty windows, a closed market, missing credentials, and feed gaps each give you a distinct honest screen, never a fake cockpit.

## How it came together

The project started with a deterministic practice simulator that proved the hardest ideas before any real market data was involved. A single-ticker cockpit took shape: a live quote, a running trade list, the core order-flow metrics, a confidence score, plain-language observations, and an event log. Two defining design principles were established early — the engine classifies price impact, not raw aggression (so heavy one-sided volume that does not move the price reads as absorption, not control), and the system never invents a reading when the evidence is weak or missing.

With the simulator working and tested, real US equity data entered the picture. A data-source selector appeared at the top of the screen. Historical replay arrived first — pick a real stock and a past date-and-time window, and the real trades and quotes from that session flow through the same unchanged engine. Symbol search followed, powered by real vendor data. The market-clock integration brought an honest "market is closed" state and a live status indicator for Live mode. Then live streaming itself arrived — during market hours, a real data feed streams trades and quotes in real time, with an honest amber "stale" light when the feed goes quiet. All fifteen original must-have journeys passed at that point.

A two-stage classifier replaced the naive approach to deciding whether each trade was a buy or a sell, reducing unknown-side prints to near zero on real data and making the directional read materially sharper. A candlestick price chart appeared above the cockpit with colored tape-state markers and a bar-size selector — for simulated and historical sessions, you can see price and the engine's calls side by side. Pause and Resume arrived next, and a local-time historical picker with one-click US-session presets fixed an earlier UTC gap. Real-historical chart rendering was verified with genuine browser screenshots for the first time, formally closing that evidence gap. All twenty must-have journeys passed.

The final phase first hardened the Watch click itself — every click gives immediate acknowledgement, every failure resolves to an explicit on-screen state within a bounded time, a connected stream with no data yet shows an honest "waiting" state, and invalid input is caught inline before any network call is made. Then the last three capabilities brought vendor responsiveness to full strength: historical loading became fast by design (trades and quotes fetched at the same time, a needless pre-flight removed, fetched windows cached for near-instant replay); symbol search pre-loads the full stock list at startup so the first keystroke is never a stall; and every vendor call is now bounded by a real network-level deadline so the app's error always arrives before the browser gives up. All 30 required capabilities now pass with concrete evidence.

## Watch it work

A full narrated walkthrough is embedded on the page that holds this document.
Open it in your browser to see the product in action.
