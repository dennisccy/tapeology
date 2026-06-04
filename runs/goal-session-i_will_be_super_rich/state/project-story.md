# Project story so far

Tapeology is a real-time "tape-reading" tool for US stocks: you point it at one ticker and it tells you, in plain language, what the order flow is doing right now — and how sure it is.

## How it has grown

An earlier run built the **practice mode** first, proving the hard ideas on a deterministic simulator before touching real market data: the single-ticker "cockpit" came to life — a live quote, a running trade list, the core flow readouts, a confidence score, plain-language observations, and an event log — along with the product's defining habit of honesty, recognizing when heavy buying or selling is being *absorbed* (the price refuses to move) rather than mistaking that pressure for control.

This session opened with a **check-up**, confirming the practice cockpit still works end to end, then set out to bring in real US market data through the exact same engine without ever inventing a number. The first stride added a **data-source selector** — Live, Historical, or Simulated — each revealing just the controls it needs, plus an honest "real-data provider unavailable" message whenever no market-data account is connected. Then **real market data flowed for the first time**: in Historical mode you can enter a real US stock, pick a past date, a time window, and a replay speed, and watch that session's real trades and quotes replay through the unchanged engine; you can find a stock by typing part of its name or ticker; and an untradable symbol or an empty window shows a clear, specific honest message instead of a fabricated screen.

The latest step **finishes the honesty promise and gets the product ready to go live.** Choosing **Live** now shows the real US market session in the top bar — "market open", or "market closed" with the time it next opens — instead of a permanent "unavailable" label. And trying to watch a real stock live while the market is closed brings up a clear **"Market is closed"** screen with the next open time, never a fake or empty cockpit. With that, every real-data dead end — no account connected, an unknown stock, an empty window, a closed market — now tells the truth in its own words.

Next, the product will follow a stock **live, in real time**, and show when the feed briefly drops out and then recovers.

## What it can do today

The product lets users watch one US stock at a time — on built-in practice data or a real past session it replays from the market — and get a live, plain-language read of the tape: whether buyers or sellers are in control, whether heavy buying or selling is being absorbed while the price holds, or whether the tape is simply unclear, each with a confidence score, quote and trade readouts, observations, and an event log. Users can choose the data source, find a stock by search, replay a chosen historical window at a chosen speed, see whether the live market is open or closed with its next open time, stop and restart cleanly, and always see an honest message rather than fabricated data when real data isn't available.

_Last updated: 2026-06-04 after iteration 3._
