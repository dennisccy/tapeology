# Project story so far

Tapeology is a tape-reading tool that watches stock trades as they happen and tells you, in plain language, what the market is actually doing right now — whether buyers are in control, sellers are pressing, or the tape is unclear and choppy.

## How it has grown

The product started as a real-time tape cockpit. You type in a ticker, hit Watch, and the screen fills with live data: recent trades with their aggression side colour-coded, 14 calculated tape features, a tape-state verdict (buyer control, seller control, bid absorption, ask absorption, unclear), and a confidence score. The engine behind it is built to be honest: high one-sided aggression with no corresponding price move correctly reads as absorption rather than control; a weak or mixed tape reads as unclear at low confidence; the screen never invents data while waiting. You can also replay historical sessions from a chosen time window, stream a live ticker in real time, search for symbols, and view a price chart with tape-state markers on true clock-time candles. Pausing freezes the cockpit without tearing it down; resuming picks up where you left off. Dates are entered and displayed in dd-MM-yyyy with local-time quick-picks.

The latest step — iteration 0 of this session — was a thorough health check with no code changes made. Every existing journey was verified against the live codebase. The full backend test suite passed (283 tests, 1 operator-gated skip). The result: all 23 of the core tape-reading journeys are confirmed working, including live real-data streaming, historical replay, and two committed real-data fixture tests that prove classification on real GME market data without needing live credentials. Eleven further journeys are partially verified (backend logic solid; some browser legs require live market hours). The research and journaling layer — the next major chapter — is confirmed entirely absent and ready to be built.

## What it can do today

The product lets users watch any stock ticker in simulated or real mode and see a live tape cockpit that identifies buyer control, seller control, bid absorption, ask absorption, and unclear tape with confidence scores. Users can replay historical sessions, stream live tickers, search for symbols, pause and resume a watch without losing state, and view a price chart with tape-state markers on true clock-time candles. Every verdict carries evidence; the product never fabricates data.

_Last updated: 2026-06-10 after iteration 0._
