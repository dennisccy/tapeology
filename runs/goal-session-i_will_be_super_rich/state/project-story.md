# Project story so far

Tapeology is a real-time tape-reading tool for US stocks: you point it at one ticker and it tells you, in plain language, what the order flow is doing right now — and how sure it is.

## How it has grown

An earlier run built the **practice mode** first, proving the hard ideas on a deterministic simulator before touching real market data. The single-ticker cockpit came to life — a live quote, a running trade list, the core flow readouts, a confidence score, plain-language observations, and an event log. The product's defining habit of honesty was established early: it recognizes when heavy buying or selling is being *absorbed* (the price refuses to move) rather than mistaking that pressure for control.

This session then set out to bring in real US market data through that same engine without ever inventing a number. Real data arrived in stages. First came a **data-source selector** (Live, Historical, or Simulated), each revealing only the controls it needs. Then **real historical replays**: enter a US stock, pick a past date and window, and watch that session's real trades and quotes flow through the unchanged engine — including honest error messages for every dead end (unknown symbol, empty window, closed market). After wiring symbol search and market-clock awareness, the session **completed the live promise**: the cockpit can stream a real ticker live, showing a green "live" light during market hours and an amber "stale" light during any quiet gap — inventing no trades during the lull, and recovering cleanly when real data resumes. These sixteen journeys reached a completed milestone at iteration 4.

With every original must-have verified, the goal was expanded. Iteration 5 tackled the **directional accuracy of real-data prints**. The trades list had been showing "unknown" for roughly one in five real-market trades — those that landed between the bid and ask, or arrived before any quote was in effect. A two-stage **aggressor classifier** now closes that gap. It first applies the published quote (a trade at or above the ask is a buy; at or below the bid is a sell), and when that can't decide it falls back to the classic tick test: compare to the prior trade price and carry the last clear direction. On the committed real Ford data window, unknown trades dropped from 20% to zero. Only a genuinely undecidable print — no quote and no prior trade — still honestly reads "unknown." All fifteen previously-passing journeys were re-verified clean with no regressions.

## What it can do today

The product lets users watch one US stock at a time — in practice mode, a real past session replayed at a chosen speed, or a real live feed — and read the tape in plain language: buyer control, seller control, bid or ask absorption, or an unclear tape, each with a confidence score, live quote, running trades list, and observations. Users can search for a stock, choose the data source, replay history at any speed, follow a live market with an honest live/stale signal, stop and restart cleanly, and always see a truthful message when real data is unavailable. The recent-trades list now labels most real-market prints as buy or sell (not "unknown"), making the directional read and the aggression-ratio features materially more accurate on real data.

_Last updated: 2026-06-05 after iteration 5._
