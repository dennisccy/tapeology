# Project story so far

Tapeology is a tape-reading tool that watches stock trades as they happen and tells you, in plain language, what the market is actually doing right now — whether buyers are in control, sellers are pressing, or the tape is unclear and choppy — and lets you declare and track your own trading thesis against that live read.

## How it has grown

The product started as a real-time tape cockpit. You type in a ticker, hit Watch, and the screen fills with live data: recent trades colour-coded by aggression side, 14 calculated tape features, a tape-state verdict (buyer control, seller control, bid absorption, ask absorption, unclear), and a confidence score. The engine is built to be honest: high one-sided aggression with no corresponding price move reads as absorption rather than control; a weak or mixed tape reads as unclear at low confidence; the screen never invents data while waiting. You can also replay historical sessions, stream a live ticker, search for symbols, and view a price chart with tape-state markers on true clock-time candles. Pausing freezes the cockpit without tearing it down; resuming picks up where you left off.

Iteration 1 laid the research layer's foundation. Two new simulation scenarios were added — one where buyer control decays to choppy-unclear as price drifts back, and one where heavy selling correctly reads as absorption before buyers lift price above the absorbed level. Under the hood, the engine gained a proven-inert research attachment point tested to be byte-identical whether or not anything is attached.

Iteration 2 delivered the thesis strip. While watching a ticker, a "Declare a thesis" bar appears between the price chart and the feature panels. You fill in your trade idea — setup type, direction, and a required invalidation price — and click Declare. The strip expands to show your thesis with expected-behaviour statements that update live as "met", "not yet", or "violated", a "Pending" verdict badge, and an honesty stamp showing the data source and feed. Incoherent declarations are refused with a clear on-screen message and nothing is recorded. The full backend was verified (332 passing tests); browser confirmation was blocked by a build-tooling conflict.

Iteration 3 fixed that tooling conflict and ran browser tests end-to-end: the thesis declaration flow and the full error-rejection matrix were both exercised in a real browser with REST cross-checks, and all 13 required smoke journeys re-verified green. Progress was real — but the screenshots of the thesis strip itself were captured at the wrong scroll position (only the price chart frame was visible; the strip sat just below it). Formally closing out the thesis-strip journeys requires a screenshot that actually shows the strip, so those journeys stay open and the next round is required to run at full depth with a stricter evidence rule.

## What it can do today

The product lets users watch any stock ticker in simulated or real mode and see a live tape cockpit that identifies buyer control, seller control, bid absorption, ask absorption, and unclear tape with confidence scores. Users can replay historical sessions, stream live tickers, search for symbols, pause and resume a watch without losing state, and view a price chart with tape-state markers on true clock-time candles. Users can also declare a trade thesis on a watched ticker — choosing a setup type, direction, and invalidation price — and watch the tape judged against it with live expected-behaviour statuses. Incoherent inputs are refused with plain-language reasons and nothing is created on rejection. Every verdict carries evidence; the product never fabricates data.

_Last updated: 2026-06-10 after iteration 3._
