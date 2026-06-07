# Project story so far

Tapeology is a real-time tape-reading tool for US stocks: you point it at one ticker and it tells you, in plain language, what the order flow is doing right now — and how sure it is.

## How it has grown

An earlier run built the **practice mode** first, proving the hard ideas on a deterministic simulator before touching real market data. The single-ticker cockpit came to life — a live quote, a running trade list, the core flow readouts, a confidence score, plain-language observations, and an event log. The product's defining habit of honesty was established early: it recognizes when heavy buying or selling is being *absorbed* (the price refuses to move) rather than mistaking that pressure for control.

This session then set out to bring in real US market data through that same engine without ever inventing a number. Real data arrived in stages. First came a **data-source selector** (Live, Historical, or Simulated). Then **real historical replays**: enter a US stock, pick a past date and window, and watch that session's real trades and quotes flow through the unchanged engine — with honest messages for every dead end. The session then **completed the live promise**: a real ticker streams live with a green "live" light, an amber "stale" light during quiet gaps, and zero invented trades during lulls.

Later iterations sharpened the accuracy. A two-stage aggressor classifier now resolves nearly all "unknown" trade sides. A **candlestick price chart** appeared above the cockpit, with colored tape-state markers and a 10/30/60-second bar-size selector. **Pause/Resume** arrived: a single button freezes the cockpit at a chosen moment without closing the session. **Local-time historical picking** landed next: enter your date and time in your own timezone, with three one-click US-session presets.

After twenty journeys reached their first GOAL_ACHIEVED, a spec commit raised the bar with four new requirements around **Watch responsiveness**. The idle screen now leaves within one second of clicking Watch. Slow or unreachable backends surface an explicit error within a bounded time. A previously-silent connection failure is now shown as a clear message. Empty or invalid input disables the Watch button and shows an inline hint.

The most recent iteration closed the **"no mute cockpit" requirement**. After a Watch connects, the app now shows an explicit "Connected to SYMBOL — waiting for the first trade…" screen (with an amber pulsing indicator) instead of drawing a wall of blank panels. If the feed breaks in the background, a clear red error screen appears and the failure is recorded in the server log — nothing is silently swallowed. A live watch that stays quiet long enough automatically moves from "waiting" to "stale" without inventing any data.

## What it can do today

The product lets users watch one US stock at a time — in practice (simulated) mode, a real past session replayed at any speed, or a real live feed — and read the tape in plain language: buyer control, seller control, bid or ask absorption, or an unclear tape, each with a confidence score, live quote, running trades list, and observations. Users can search for a stock by name, choose the data source, and pick historical windows in their own local time using one-click US-session presets. A candlestick price chart appears in simulated and historical modes with colored tape-state markers and a bar-size selector. Users can pause and resume a running watch. Every Watch click gives immediate feedback — a "Connecting…" acknowledgement, a clear error on failure, or inline validation for invalid input. A connected stream with no data yet shows an honest "waiting" state; a background feed failure surfaces as an explicit error, never a frozen or blank screen.

_Last updated: 2026-06-07 after iteration 10 (CONTINUE)._
