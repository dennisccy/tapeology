# Delivered — Tapeology: Real-Time Tape Reading for US Stocks

**Session:** i_will_be_super_rich
**Date:** 2026-06-10
**Final verdict:** GOAL_ACHIEVED
**Iterations:** 15 (iter-0 through iter-14)

## What you can do today

- Watch one US stock at a time in three modes: a built-in simulator (no account needed), a historical replay of any past session, or a live real-time stream during market hours.
- Read the tape in plain language — buyer control, seller control, bid absorption, ask absorption, or unclear — each with a confidence score so you always know how sure the system is.
- See a live quote (bid, ask, spread, last price) and a running list of recent trades, each labeled with direction.
- Read key order-flow features — trade speed, aggressive buy and sell ratios, price impact, absorption score, and more — updating in real time over a live connection.
- Follow plain-language observations and an event log that announce meaningful changes as they happen: "Tape state changed to seller control", "Large sell print absorbed", and so on.
- Watch a candlestick price chart with colored markers at tape-state transitions, so you can judge whether a state actually preceded the next price move. The chart axis shows real market clock times, not a playback counter.
- Switch the chart between 10-second, 30-second, and 60-second candle bars.
- Pause a running watch and resume it later without losing anything on screen. Stop a watch and start a fresh one on the same or a different stock.
- Search for a stock by name or partial symbol and get suggestions instantly, even right after the app starts.
- Pick historical replay windows in your own local time, with one-click presets for the US market open (9:30 ET), close (4:00 PM ET), and full trading day — each preset also shows your local-time equivalent.
- Enter and read dates in day-month-year format everywhere in the app, via a custom date field rather than a locale-dependent browser picker.
- Change the replay speed (1×, 2×, 5×, or 10×) while a historical replay is actively running — no restart, no lost position — and the new pace takes effect within about one second.
- Load long historical windows including a full trading day for busy stocks; the cockpit starts filling from the very first piece of data while the rest loads in the background.
- Re-watch the same historical window near-instantly from a local cache.
- Get immediate feedback the instant you click Watch — a connecting state labeled with the symbol appears right away. If a request times out or the backend is unreachable, a clear actionable error appears rather than a frozen spinner. Invalid input (empty symbol, missing date) is caught inline before any request is made.
- Trust that a genuine directional move on real consolidated-tape data — proven against a committed real GME session with 17,342 actual trades — reads correctly as buyer or seller control, not a perpetual "unclear." The system also never invents data: unknown symbols, empty windows, a closed market, missing credentials, and feed gaps each give a distinct honest screen.

## How it came together

The project started by building the hard conceptual core on a simulator before any real market data was involved. The first working version introduced a single-ticker "tape cockpit" driven by deterministic practice scenarios: buyer control, seller control, two absorption scenarios, and a choppy unclear tape. The principle of honesty was built in from the start — when heavy buying or selling was being absorbed (price refusing to move), the system said so rather than mistaking that for control.

With the engine proven on practice data, the next phase brought in real US market data. A data-source selector appeared, followed by real historical replay through a vendor-agnostic adapter (Alpaca's SIP consolidated feed), symbol search, a two-stage aggressor classifier that resolved the direction of most trades, and a candlestick price chart with tape-state markers. Live streaming arrived, then pause and resume, and a local-time historical picker with US-session quick-picks.

The third phase addressed reliability and responsiveness: concurrent trades-and-quotes fetching, a window cache for near-instant re-watches, a pre-loaded symbol universe for fast search, and real network-level deadlines on every vendor call with clear actionable error messages. A fourth wave tackled the experience of clicking Watch: immediate acknowledgement, explicit error states for slow or unreachable backends, an honest "waiting" state while connected but before the first trade, and inline validation. Iteration 12 completed the experience layer — real clock times on the chart axis, the custom day-month-year date field, mid-session speed changes, and parallel-chunk loading for long windows.

Iteration 13 declared the goal achieved — but two proofs rested on synthetic test fixtures. A review against real Alpaca data showed they still failed on actual market data, and both were immediately reopened.

Iteration 14 closed those defects with real evidence. The reference case is GME's sharp drop on 14 May 2024: 17,342 actual SIP trades and 1,946 real quotes, committed to the test suite and running in automated CI without live credentials. The engine now correctly reads seller control at confidence 0.925 on that real drop — the same window with the old logic stays stuck on "unclear" at 0.200. Historical replay now pulls the SIP consolidated feed with realistic spreads, and the engine treats a momentarily wide quote as a confidence dip rather than a hard veto on an otherwise obvious move. Long windows stream from the very first chunk while the rest loads behind the scenes. The full test suite stands at 283 automated tests; all 37 must-have capabilities are proven and passing.

## Watch it work

A full narrated walkthrough is embedded on the page that holds this document.
Open it in your browser to see the product in action.
