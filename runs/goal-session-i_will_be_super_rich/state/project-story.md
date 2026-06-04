# Project story so far

Tapeology is a real-time "tape-reading" tool for US stocks: you point it at one ticker and it tells you, in plain language, what the order flow is doing right now — and how sure it is.

## How it has grown

An earlier run built the **practice mode** first, deliberately proving the hard ideas on a deterministic simulator before touching real market data. Over that work the single-ticker "cockpit" came to life — live bid/ask/spread/last, a running trade list, the core flow readouts, a confidence score, plain-language observations, and an event log — and it learned the product's defining habit of honesty: recognizing when heavy buying or selling is being *absorbed* (price refuses to move) instead of mistaking that pressure for control.

This session opened with a **check-up, not a build**: it confirmed the practice cockpit still works end to end across all nine practice journeys, then mapped the real work ahead — bringing in real US market data, both live and historical, through the exact same engine, without ever inventing a number.

The latest step took the first real stride toward that. The product now has a **data-source selector** at the top — Live, Historical, or Simulated (practice) — and each choice reveals just the controls it needs: a symbol box for real data, plus a date, a time window, and a replay-speed chooser for historical playback. Most importantly, it now answers honestly when no market-data account is connected: choosing Live or Historical and pressing Watch shows a clear "real-data provider unavailable" message instead of made-up prices — and it never quietly falls back to practice data. Under the hood, a single isolated place now owns all knowledge of the data vendor, the foundation that later lets real data flow through the unchanged engine; and switching source or symbol now cleanly tears down the previous watch, so nothing is left running in the background.

The practice cockpit remains the solid, now-protected floor, and the honest "unavailable" wall is in place so real data can never be faked. Next, the product will start replaying real past market sessions for a stock you choose, and let you find tickers by searching.

## What it can do today

The product lets users watch one ticker at a time on built-in practice data and get a live, plain-language read of the tape — whether buyers or sellers are in control, whether heavy buying or selling is being absorbed while the price holds, or whether the tape is simply unclear — each with a confidence score, live quote and trade readouts, observations, and an event log, with a clean stop-and-restart. It now also lets users choose a data source (practice, live, or historical) from a selector at the top, with an honest "real-data provider unavailable" message whenever no market-data account is connected.

_Last updated: 2026-06-04 after iteration 1._
