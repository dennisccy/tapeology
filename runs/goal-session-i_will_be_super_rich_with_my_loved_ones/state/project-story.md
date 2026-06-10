# Project story so far

Tapeology is a tape-reading tool that watches stock trades as they happen and tells you, in plain language, what the market is actually doing right now — whether buyers are in control, sellers are pressing, or the tape is unclear and choppy.

## How it has grown

The product started as a real-time tape cockpit. You type in a ticker, hit Watch, and the screen fills with live data: recent trades with their aggression side colour-coded, 14 calculated tape features, a tape-state verdict (buyer control, seller control, bid absorption, ask absorption, unclear), and a confidence score. The engine behind it is built to be honest: high one-sided aggression with no corresponding price move correctly reads as absorption rather than control; a weak or mixed tape reads as unclear at low confidence; the screen never invents data while waiting. You can also replay historical sessions from a chosen time window, stream a live ticker in real time, search for symbols, and view a price chart with tape-state markers on true clock-time candles. Pausing freezes the cockpit without tearing it down; resuming picks up where you left off.

Iteration 0 was a thorough health check with no code changes. Every existing journey was verified against the live codebase. The full backend test suite passed (283 tests, 1 operator-gated skip). All 23 core tape-reading journeys were confirmed working, including two committed real-data fixture tests that prove classification on real GME market data without needing live credentials. The research and journaling layer was confirmed entirely absent and ready to be built.

Iteration 1 laid the research layer's foundation. Two new simulation scenarios were added: "SIM-SHIFT", where buyers take control and then the tape honestly decays to choppy-unclear as price drifts back down, and "SIM-REVERSAL", where heavy selling is correctly read as absorption (not seller control) because the price never actually falls, and then buyers step in and price lifts above the absorbed level. Both are immediately watchable in the existing cockpit with no UI change. Under the hood the engine gained a proven-inert research attachment point — tested to be byte-identical whether or not it has anything attached, even if what is attached throws an error — that every future research feature will use safely. The backend suite grew to 292 tests with zero regressions, and all 12 targeted browser journeys passed.

## What it can do today

The product lets users watch any stock ticker in simulated or real mode and see a live tape cockpit that identifies buyer control, seller control, bid absorption, ask absorption, and unclear tape with confidence scores. Users can replay historical sessions, stream live tickers, search for symbols, pause and resume a watch without losing state, and view a price chart with tape-state markers on true clock-time candles. Two new simulation scenarios let users observe a tape that changes regime mid-stream: one where buyer control honestly decays to unclear, and one where absorbed selling resolves into buyer control with real upward price progress. Every verdict carries evidence; the product never fabricates data.

_Last updated: 2026-06-10 after iteration 1._
