# Project story so far

Tapeology is a real-time "tape-reading" tool for US stocks: you point it at one ticker and it tells you, in plain language, what the order flow is doing right now — and how sure it is.

## How it has grown

An earlier run built the **practice mode** first, deliberately proving the hard ideas on a deterministic simulator before touching real market data. Over that work the single-ticker "cockpit" came to life — live bid/ask/spread/last, a running trade list, the core flow readouts, a confidence score, plain-language observations, and an event log — and it learned the product's defining habit of honesty: recognizing when heavy buying or selling is being *absorbed* (the price refuses to move) rather than mistaking that pressure for control.

This session opened with a **check-up, not a build**, confirming the practice cockpit still works end to end, then mapped the real work ahead: bringing in real US market data, live and historical, through the exact same engine, without ever inventing a number. The first stride added a **data-source selector** at the top — Live, Historical, or Simulated (practice) — each revealing just the controls it needs, plus an honest "real-data provider unavailable" message whenever no market-data account is connected, so the product can never quietly fall back to made-up prices. Behind the scenes a single isolated place took ownership of all vendor knowledge, and switching source or symbol began cleanly tearing down the previous watch.

The latest step is the big one: **real market data flows for the first time.** In Historical mode you can now enter a real US stock, pick a past date, a time window, and a replay speed, and watch that session's **real** trades and quotes replay through the unchanged engine — every panel filling with real values. You can **find a stock by typing part of its name or ticker** and pick from live suggestions. And when a symbol isn't tradable, or a window holds no data, the product shows a clear, specific honest message instead of a fabricated screen — it still never invents a tape.

Next, the product will follow a stock **live, in real time**, and show when the market is open or closed.

## What it can do today

The product lets users watch one US stock at a time — on built-in practice data or a real past session it replays from the market — and get a live, plain-language read of the tape: whether buyers or sellers are in control, whether heavy buying or selling is being absorbed while the price holds, or whether the tape is simply unclear, each with a confidence score, quote and trade readouts, observations, and an event log. Users can choose the data source, find a stock by search, replay a chosen historical window at a chosen speed, stop and restart cleanly, and always see an honest message rather than fabricated data when real data isn't available.

_Last updated: 2026-06-04 after iteration 2._
