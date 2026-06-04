# Project story so far

Tapeology is a real-time "tape-reading" tool for US stocks: you point it at one ticker and it tells you, in plain language, what the order flow is doing right now — and how sure it is.

## How it has grown

An earlier run built the **practice mode** first, proving the hard ideas on a deterministic simulator before touching real money data: the single-ticker "cockpit" came to life — a live quote, a running trade list, the core flow readouts, a confidence score, plain-language observations, and an event log — along with the product's defining habit of honesty, recognizing when heavy buying or selling is being *absorbed* (the price refuses to move) rather than mistaking that pressure for control. This session opened with a **check-up** that the practice cockpit still works end to end, then set out to bring in real US market data through that very same engine without ever inventing a number.

It arrived in stages. First came a **data-source selector** — Live, Historical, or Simulated — each revealing just the controls it needs. Then **real market data flowed**: in Historical mode you can enter a real US stock, pick a past date, a time window and a replay speed, and watch that session's real trades and quotes replay through the unchanged engine; you can find a stock by typing part of its name or ticker; and every real-data dead end — no account connected, an unknown stock, an empty window, a closed market (shown with the time it next opens) — now tells the truth in its own words instead of faking a screen.

The latest step **finished the promise**: the product now follows a stock **live, in real time**. Choose Live, enter a real ticker, press Watch, and during market hours the cockpit streams the market's real trades and quotes through the same engine, with a green "live" light. If the feed goes quiet, the app honestly shows an amber "stale" light and invents **no** trades during the lull, then returns to live the moment real data resumes; stopping or switching closes the live connection cleanly. With that, **every must-have is done** — the real-market half now runs on the very same engine as the practice simulator, completing the product's defining promise.

## What it can do today

The product lets users watch one US stock at a time — on built-in practice data, a real past session it replays from the market, or a real live feed — and read the tape in plain language: whether buyers or sellers are in control, whether heavy buying or selling is being absorbed while the price holds, or whether the tape is simply unclear, each with a confidence score, quote and trade readouts, observations, and an event log. Users can choose the data source, search for a stock, replay a chosen historical window at a chosen speed, follow a live market in real time with an honest live/stale signal, see whether the market is open or closed with its next open time, stop and restart cleanly, and always see an honest message rather than fabricated data when real data isn't available.

_Last updated: 2026-06-04 after iteration 4._
