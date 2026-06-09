# Project story so far

Tapeology is a real-time tape-reading tool for US stocks: you point it at one ticker and it tells you, in plain language, what the order flow is doing right now — and how sure it is.

## How it has grown

An earlier run built the **practice mode** first, proving the hard ideas on a deterministic simulator before touching real market data. The single-ticker cockpit came to life — a live quote, a running trade list, the core flow readouts, a confidence score, plain-language observations, and an event log. The product's defining habit of honesty was established early: it recognizes when heavy buying or selling is being *absorbed* (the price refuses to move) rather than mistaking that pressure for control.

This session then brought in real US market data through that same engine without ever inventing a number. A data-source selector (Live, Historical, or Simulated) arrived first, followed by real historical replays, a two-stage aggressor classifier, a candlestick price chart with tape-state markers, pause and resume, and a local-time historical picker with one-click US-session presets. A third wave added vendor responsiveness: concurrent trades-and-quotes fetching, a window cache for near-instant re-watches, a pre-loaded symbol universe, and every vendor call bounded by a real network-level deadline with actionable error messages.

A fourth expansion addressed the experience of watching the product in action. The Watch button now always gives immediate feedback. Slow or unreachable backends surface an explicit error. A stream with no data yet shows an honest "waiting" state; a background feed failure surfaces as a clear error, never a frozen screen. Invalid input is caught inline.

The penultimate iteration completed a time-display overhaul: the chart axis now shows real market clock times (a synthetic session clock for simulated mode, exact wall-clock times for historical), and a custom day-month-year date field with strict inline validation replaced the native calendar picker everywhere.

The final iteration closed the last three capabilities. The replay-speed control now works mid-replay: select a new speed and the cadence changes within about one second, no reload or restart. Long historical windows — including the full trading day — now load for busy stocks by fetching the data in parallel bounded chunks and stitching them together; the "shorter range" message is now a true backstop rather than a routine refusal. And the tape-state classifier now judges spread and price impact relative to each stock's own price level, so a real stock making a genuine directional move reads as buyer or seller control instead of being stuck on "unclear". All 35 must-have capabilities are now complete.

## What it can do today

The product lets users watch one US stock at a time — in simulated mode, a real past session replayed at any speed (including speed changes mid-replay), or a real live feed — and read the tape in plain language: buyer control, seller control, bid or ask absorption, or an unclear tape, each with a confidence score, live quote, running trades list, and plain-language observations. Users can search for a stock by name, choose the data source, and pick historical windows in their own local time using one-click US-session presets entered via a custom day-month-year date field. A candlestick price chart shows true clock times on its axis in simulated and historical modes with colored tape-state markers and a bar-size selector. Users can pause and resume a running watch. Every Watch click gives immediate feedback; connection failures and slow requests surface explicit error messages. Re-watching the same historical window is near-instant from a local cache. Long historical windows including the full trading day load without error. A stock making a clear directional move reads as buyer or seller control, not perpetual "unclear". Dates appear consistently in day-month-year format across the entire product. All 35 must-have capabilities are complete.

_Last updated: 2026-06-09 after iteration 13 (GOAL_ACHIEVED)._
