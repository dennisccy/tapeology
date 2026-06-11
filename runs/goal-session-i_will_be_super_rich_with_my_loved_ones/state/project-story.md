# Project story so far

Tapeology is a tape-reading tool that watches stock trades as they happen and tells you, in plain language, what the market is actually doing right now — whether buyers are in control, sellers are pressing, or the tape is unclear — and lets you declare, track, mark, close, and now honestly assess entry risk for your own trading thesis against that live read.

## How it has grown

The product started as a real-time tape cockpit. Type in a ticker, hit Watch, and the screen fills with live data: recent trades colour-coded by side, 14 calculated tape features, a tape-state verdict with a confidence score, and a price chart with true clock-time candles. The engine is built to be honest: high aggression with no price move reads as absorption rather than control; a weak or mixed tape reads as unclear. Symbol search, historical replay, live streaming, and pause/resume all work without tearing down the cockpit.

Early iterations built the thesis layer — a "Declare a thesis" strip on the cockpit where you choose a setup type, direction, and required invalidation price. After resolving a correctness defect in statement evaluation, the verdict engine reached a reliable baseline: all five verdict states — confirming, rejecting, weakening, invalidated, and pending — render in real browser pixels with the underlying persistence layer proven against committed schema fixtures.

Iterations 6 and 7 completed the remaining verdict captures against canary-verified fresh servers, added user-facing thesis resolution ("Played out" and "Abandon" buttons save the outcome with timestamps), and finished the failed-move fade and absorption-reversal journeys. Iteration 8 fixed a subtle honesty gap in statement evaluation and introduced the journaling half of a trade: Mark entry and Mark exit controls record actual prices verbatim with spread-at-mark, showing the realized move in R units. Once an entry exists, the Abandon button disappears so an open position cannot be silently discarded.

Iteration 9 tackled a critical lifecycle gap: an entry-marked thesis now survives a watch interruption as "NOT EVALUATED," and re-watching the same source reattaches it with exactly one recorded gap event so the interrupted period is always visible in the timeline.

Iteration 10 brought the thesis onto the chart itself. The price chart now draws labeled invalidation and level price-lines at the exact prices declared, verdict-transition markers at the moments each state published, an entry marker at the recorded price and time, and a first-confirmation marker — all computed once on the server and drawn verbatim.

Iteration 11 completed the entry-risk assessment layer. When you declare a thesis, the product now instantly evaluates six risk conditions — whether you are chasing an extended move, setting an invalidation too tight relative to the spread, trading into a slow or illiquid tape, declaring before the classifier has warmed up, or going against the tape's own expected direction — and shows amber advisory chips for any that fire, each with the actual measured margin in plain language. A clean declare produces no chips and no false reassurance. These flags are frozen at the moment of declaration and never change as the tape moves.

## What it can do today

The product lets users watch any stock ticker (simulated, historical, or live) and see a real-time cockpit identifying buyer control, seller control, bid absorption, ask absorption, and unclear tape with confidence scores. Users can replay historical sessions, stream live tickers, search for symbols, pause and resume a watch without losing state, and view a price chart with tape-state markers on true clock-time candles. Users can declare a trading thesis, watch it judged live across all five verdict states with plain-language evidence, see the declared thesis geometry drawn on the chart, mark their actual entry and exit prices verbatim, see the realized move in R units, close a thesis as played out or abandoned, survive a watch interruption with the thesis intact, and now receive honest amber entry-risk chips at declaration showing exactly how far outside the safe zone each fired condition is.

_Last updated: 2026-06-11 after iteration 11._
