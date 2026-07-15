# Iteration diff (bounded)

Files changed: 5. Shown in full: 5.

```diff
diff --git a/README.md b/README.md
index 8a3c105..6edec2d 100644
--- a/README.md
+++ b/README.md
@@ -74,15 +74,15 @@ Current capabilities:
 - **Support/resistance levels and confluence zones (research API)** — from any recorded bar series, compute the horizontal price levels where a symbol has structurally turned: swing pivots (a bar's high or low that is the extreme among its surrounding neighbours) and prior-period extremes (the prior day/week/month's high, low, or close), each stamped with its timeframe, how it was derived, its touch count, and an overall strength score that weights longer timeframes and more touches higher. Levels that sit close together in price across different timeframes are grouped into a confluence zone carrying a combined strength score and an honest A/B/C conviction class: A when several distinct timeframes agree and at least one is longer-term (daily/weekly/monthly), B when two distinct timeframes agree, and C when the zone only ever shows up within a single timeframe — a grade is never inflated to look more convincing than the evidence supports. Every one of those parameters — pivot lookback, confluence tolerance, and the class thresholds — comes from one central config; nothing is hard-coded, fitted, or invented on the fly. Levels and zones computed "as of" a given time use only bars recorded at or before that moment; a bar recorded later can never change an earlier answer — proven directly by comparing the same query against a store with and without the later bars physically removed, for both levels and zones. Identical requests always return byte-identical results. A symbol with no bar history at all gets an explicitly different message than a symbol that has history but no notable levels or zones yet — the "nothing to show" cases are never conflated. These levels and zones are now visualized on the Structure page in the browser, and remain reachable through the research API and the matching machine-readable tool.
 - **Strategy registry and a tape-confirmed structure strategy (research API)** — a named list of the trading strategies a backtest can be run under: the original `v1` strategy, plus an additive second one, `structure_tape`, that only opens a simulated trade where price sits at (or has just moved through) one of the support/resistance levels above AND the live tape agrees — either the tape shows that level being defended (a fade back the other way) or shows real, sustained price impact carrying straight through it (a follow-through in that direction). Every simulated entry records exactly which level — its price, timeframe, and A/B/C conviction class — triggered it, reported with the same simulated return-in-R-and-dollars figures beside the same random-entry comparison every backtest already shows. Registering `structure_tape` never changes the frozen `v1` strategy or any of its past results, and `structure_tape` only ever becomes the shown "champion" strategy through the same honest hold-out comparison every candidate goes through — never automatically. The current registry and today's champion strategy are reachable through the research API and the matching machine-readable tool.
 - **Class-scaled risk, reward, and size for structure_tape, with a per-class PnL breakdown (research API)** — every `structure_tape` simulated trade sets its stop distance, take-profit target, and simulated position size from the A/B/C conviction class of the level it entered at: an A-class level (the strongest cross-timeframe agreement) gets a tight stop (about 1 basis point beyond the level) and the largest simulated size, while B and C levels get progressively wider stops and smaller size. The take-profit target is a class-scaled multiple of the trade's own risk, capped at the next already-detected opposing level rather than an arbitrary distance. Every stop distance, target multiple, and size factor is a named configuration value, never a number buried in code. Backtest reports for any registered strategy show, alongside the existing blended total, a per-class A/B/C breakdown of trade count and net return in both R-multiples and dollars — a strategy that does not use support/resistance levels (such as `v1`) honestly shows all three classes empty rather than omitting the section.
-- **Fetch real bars from Yahoo Finance, right on the Structure page** — a fetch control above the Levels & Zones section lets you pick a symbol, a timeframe (1w / 1d / 4h / 1h / 5m / 1m), and a start/end date range, then click "Fetch from Yahoo Finance" — no account, API key, or cost required. The button stays disabled until every field has a value, and its label changes to "Fetching…" while a request is in flight. On success, the candlestick chart, the support/resistance level lines, and the confluence-zone table populate automatically — no separate "Load" step — and a "Yahoo Finance" badge appears above the chart confirming the data's provenance, its label read from the same central taxonomy used elsewhere in the product. Asking again for a symbol/timeframe/window you already fetched is served back instantly from local storage instead of contacting Yahoo Finance again, with no duplicate-data error. When a fetch cannot be completed, a distinctly-styled panel explains the specific reason — an unsupported timeframe, no data for the requested window, or the fetch service being unreachable — instead of a generic error, and states plainly that nothing cached or fabricated is shown in its place.
-- **Structure page** — a fifth top-level page (reachable from the top navigation bar on every page), with an explicit fetch action (the bullet above) plus three read-only sections. The first read-only section lets you pick a symbol and an as-of date/time, then shows that symbol's computed support/resistance levels as dashed reference lines on a price candlestick chart — each line labelled with its timeframe and level type — plus a confluence-zones table beneath the chart listing each zone's A/B/C strength grade, its numeric score, and its member levels. Every value is read verbatim from the same levels computation used elsewhere in the product — nothing is recomputed in the browser. Four distinct honest states cover every case where nothing can be shown: no price history has ever been recorded for the symbol, history is recorded but nothing is derivable yet at that as-of time, levels exist but none cluster into a qualifying zone, and the backend is unreachable or the entered date/time is invalid — each with its own explicit wording, never a blank or guessed screen. When a symbol has price history recorded at more than one timeframe, the chart draws candles from only the shortest recorded timeframe while still drawing a reference line for levels from every timeframe — a disclosed, deliberate limitation rather than a gap. The second and third sections (the strategy registry/champion panel and the structure_tape-vs-v1 comparison) are described in the next two bullets.
-- **Strategy registry and champion panel on the Structure page** — beneath the confluence-zones table, a Registry section shows the two trading strategies the system knows about, `v1` and `structure_tape`, each as a card listing its entry rule and its exit rules — stop distance, a reward target where the strategy defines one (only `structure_tape` does), the tape-state-flip exit, the time horizon, and the dataset-end exit. The `structure_tape` card additionally shows three small tables — stop distance, reward target, and simulated position size — each broken out by A/B/C confluence class. A Champion panel above the two cards names the strategy/profile pair currently favored (today `v1` on the `default` profile) and a caption confirms this agrees with the same champion shown on the Performance page. The section loads automatically as soon as the Structure page opens — no symbol or as-of time is required — every value is read verbatim from the backend with nothing calculated in the browser, and an explicit "registry unavailable" message replaces the whole section, with no guessed fallback, if the backend can't be reached.
+- **Fetch real bars from Yahoo Finance, right on the Structure page** — a fetch control lets you pick a symbol, a timeframe (1w / 1d / 4h / 1h / 5m / 1m), and a start/end date range, then click "Fetch from Yahoo Finance" — no account, API key, or cost required. The button stays disabled until every field has a value, and its label changes to "Fetching…" while a request is in flight. On success, the candlestick chart and the Tradable Map populate automatically — no separate "Load" step — with the raw support/resistance level lines and confluence-zone table available a click away via "Show raw levels"; a "Yahoo Finance" badge appears above the chart confirming the data's provenance, its label read from the same central taxonomy used elsewhere in the product. Asking again for a symbol/timeframe/window you already fetched is served back instantly from local storage instead of contacting Yahoo Finance again, with no duplicate-data error. When a fetch cannot be completed, a distinctly-styled panel explains the specific reason — an unsupported timeframe, no data for the requested window, or the fetch service being unreachable — instead of a generic error, and states plainly that nothing cached or fabricated is shown in its place.
+- **Structure page** — a fifth top-level page (reachable from the top navigation bar on every page). Picking a symbol and an as-of date/time now shows, by default, the **Tradable Map**: bands drawn as solid, color-coded reference lines on the price candlestick chart (rose for resistance, emerald for support) plus a table of each band's side, price range, quality score, member count, round-number flag, and inherited A/B/C class. A "Show raw levels" toggle, off by default, reveals the page's original view unchanged — dashed reference lines for every individual raw level, plus a confluence-zones table beneath the chart listing each zone's A/B/C strength grade, numeric score, and member levels — and can be switched back off. Below the toggle, two sections are new to the page: **Case Studies**, a filterable registry of historical band-touch events with a per-event drill-in, and **Edge Report**, an honest three-strategy profit comparison over recorded event windows. Further down, the existing "Fetch from Yahoo Finance" control and its provenance badge, the strategy **Registry**/champion panel, and the `structure_tape`-vs-`v1` **Comparison** tool are all still present and work exactly as before — the next two bullets describe the Registry and Comparison sections. Every value on the page is read verbatim from its owning endpoint — nothing is recomputed in the browser — and each section has its own explicit empty/error state rather than a blank or guessed screen: no price history ever recorded for the symbol, history recorded but nothing derivable yet at that as-of time, levels with no qualifying zone, or the backend unreachable/date-time invalid. When a symbol has price history recorded at more than one timeframe, the chart draws candles from only the shortest recorded timeframe while still drawing reference lines for levels from every timeframe — a disclosed, deliberate limitation rather than a gap.
+- **Strategy registry and champion panel on the Structure page** — further down the page (below the Tradable Map, Case Studies, and Edge Report sections), a Registry section shows the three trading strategies the system knows about — `v1`, `structure_tape`, and `structure_tape_map` — each as a card listing its entry rule and its exit rules: stop distance, a reward target where the strategy defines one (`structure_tape` and `structure_tape_map` both do; `v1` does not), the tape-state-flip exit, the time horizon, and the dataset-end exit. The `structure_tape` and `structure_tape_map` cards additionally show three small tables — stop distance, reward target, and simulated position size — each broken out by A/B/C confluence class. A Champion panel above the cards names the strategy/profile pair currently favored (today `v1` on the `default` profile) and a caption confirms this agrees with the same champion shown on the Performance page. The section loads automatically as soon as the Structure page opens — no symbol or as-of time is required — every value is read verbatim from the backend with nothing calculated in the browser, and an explicit "registry unavailable" message replaces the whole section, with no guessed fallback, if the backend can't be reached.
 - **structure_tape-vs-v1 comparison on the Structure page** — beneath the Registry section, a Comparison section lets you choose a registered dataset and run both `structure_tape` and the champion strategy `v1` over it as an offline research job (it places nothing and never touches an order path); each side's progress is shown independently as it moves from Queued to Running (with a live count of events processed) to Done, and the two result cards populate automatically once both finish, with no manual refresh. It then shows both strategies' results side by side: trade count, net return in R and dollars, win rate, and maximum drawdown — a strategy that took zero trades shows an honest "no trades (n=0)" instead of a misleading zero — plus a per-class A/B/C breakdown of the same figures with an explicit "insufficient sample" label wherever a class has too few trades to trust. The always-visible "simulated — assumed fees/slippage — not indicative of live results" register is shown exactly as the backend serves it, never a rephrased copy. A read-only Champion panel beside the results confirms the champion is unaffected — this comparison never promotes a strategy or writes to the PnL ledger, no matter what it finds — and a Founding baseline panel shows the ledger's first recorded row for reference. Every number is read verbatim from the same backtest report the research API and command-line tool already serve. On the committed keyless sample data this honestly shows `structure_tape` arming too few (or zero) trades to trust a result, exactly the "not enough evidence yet" finding the underlying research tool already reports — the champion stays `v1` on `default`. No datasets registered, a comparison still running, a failed or cancelled run, and the backend being unreachable each show their own distinct, explicit message rather than a blank or guessed result.
-- **Tradable level map (research API)** — distills a symbol's raw support/resistance levels (which can number in the thousands for a heavily traded stock) down to at most 10 price "bands" total — the handful of price zones actually worth marking on a chart. Each band carries its price range, whether it is support or resistance, a quality score, how many underlying levels back it up, whether it sits on a psychologically "round" price, and an inherited A/B/C conviction class where one applies. The map for any given day is built using only data fully available before that trading day started — mirroring how a trader marks up charts before the open — with weekends and market holidays handled automatically by falling back to whichever trading day actually closed last. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
-- **Touch-event scanner and case-study registry (research API)** — walks every stored trading session in a 12-symbol panel's recorded price history and checks each session's actual price action against that session's own tradable level map, built strictly from data available before the session opened, so a later session's data can never change an earlier one's already-recorded result. Every genuine touch of a band is logged with its outcome — rejected and turned away, broken straight through, or chopped near the wall with no clear outcome — together with how far price moved by two later checkpoints; a touch too recent to have built up the usual follow-up window is honestly labeled with exactly how much less time its verdict is based on, rather than being shown as an ordinary result. Run against real, freshly fetched price history for the full panel, the registry already holds several hundred touch events across all 12 symbols, a healthy mix of breakouts, rejections, and chops, with identical requests always returning byte-identical results; because scanning the full panel is expensive, the scan result is remembered after the first request, so repeat lookups return in a fraction of a second instead of re-scanning every time. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
-- **Real tape recorded and joined at wall-touch events (command-line research tool + research API)** — with market-data vendor credentials configured, a dedicated recording tool captures a real trade-by-trade market-data window (an hour before through 90 minutes after) around the best-scoring touch events from the case-study registry, spreading its picks across as many different stocks as possible and always including the project's pinned reference example. Once a touch event has a matching real recording, opening that event's detail view replays the frozen tape-reading engine over the recording and attaches a timeline of what buyers and sellers were actually doing around the touch — for example, sellers absorbing at the ask right before a rejection, or buyers in control through a break. Events with no matching recording show an honestly empty timeline rather than an invented one. A committed real-data sample keeps this timeline check running with no credentials required. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
-- **A third registered strategy, `structure_tape_map` (research API)** — the app now has three registered ways of simulating trades against historical data: the original `v1`, the frozen `structure_tape` (which trades off the raw list of thousands of individual price levels), and this new one, which trades off the same small handful of tradable bands the level map produces instead. It reuses the exact same class-scaled stop/target/position-sizing rules as `structure_tape` — only which levels it watches differs. Registering it changes nothing about `v1`, `structure_tape`, or their past results. It is runnable through the existing backtest API; today it is only exercised automatically as part of the 3-way edge report below, and there is no button yet to pick it directly in the browser.
-- **The 3-way profit edge report (research API)** — a new endpoint runs `v1`, `structure_tape`, and `structure_tape_map` over every recorded practice-tape window and reports, honestly, how each one actually did — broken down by price-level quality (A/B/C), which side of the market it traded (support or resistance), how price reacted at the touch (rejected, broke, or chopped), and which data feed the window came from. Every dollar figure carries its sample size, a comparison against a random-entry baseline, and the same "simulated — not indicative of live results" register used everywhere else in the app. With only the small practice dataset available today the report is honestly empty — no strategy yet has enough recorded real-world touches to report a result — rather than a manufactured one; once real trading windows are recorded it will start showing real, if still small-sample, numbers. The same comparison is available to AI tools through the machine-readable connection, byte-for-byte identical to what a person sees calling the endpoint directly. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
+- **Tradable level map (research API)** — distills a symbol's raw support/resistance levels (which can number in the thousands for a heavily traded stock) down to at most 10 price "bands" total — the handful of price zones actually worth marking on a chart. Each band carries its price range, whether it is support or resistance, a quality score, how many underlying levels back it up, whether it sits on a psychologically "round" price, and an inherited A/B/C conviction class where one applies. The map for any given day is built using only data fully available before that trading day started — mirroring how a trader marks up charts before the open — with weekends and market holidays handled automatically by falling back to whichever trading day actually closed last. On the operator's real AAPL price history, for example, the strongest band in the map is the ~300–302 resistance zone — the exact level where price was rejected six times before a sharp drop — ranking first out of all ten bands, ahead of every other zone. This map is now the default view on the Structure page in the browser, and remains reachable through the research API and the matching machine-readable tool.
+- **Touch-event scanner and case-study registry (research API)** — walks every stored trading session in a 12-symbol panel's recorded price history and checks each session's actual price action against that session's own tradable level map, built strictly from data available before the session opened, so a later session's data can never change an earlier one's already-recorded result. Every genuine touch of a band is logged with its outcome — rejected and turned away, broken straight through, or chopped near the wall with no clear outcome — together with how far price moved by two later checkpoints; a touch too recent to have built up the usual follow-up window is honestly labeled with exactly how much less time its verdict is based on, rather than being shown as an ordinary result. Run against real, freshly fetched price history for the full panel, the registry already holds several hundred touch events across all 12 symbols, a healthy mix of breakouts, rejections, and chops, with identical requests always returning byte-identical results; because scanning the full panel is expensive, the scan result is remembered after the first request, so repeat lookups return in a fraction of a second instead of re-scanning every time. This registry is now browsable on the Structure page in the browser as Case Studies — filterable by symbol and by reaction outcome, with a per-event drill-in — and remains reachable through the research API and the matching machine-readable tool.
+- **Real tape recorded and joined at wall-touch events (command-line research tool + research API)** — with market-data vendor credentials configured, a dedicated recording tool captures a real trade-by-trade market-data window (an hour before through 90 minutes after) around the best-scoring touch events from the case-study registry, spreading its picks across as many different stocks as possible and always including the project's pinned reference example. Once a touch event has a matching real recording, opening that event's detail view replays the frozen tape-reading engine over the recording and attaches a timeline of what buyers and sellers were actually doing around the touch — for example, sellers absorbing at the ask right before a rejection, or buyers in control through a break. Events with no matching recording show an honestly empty timeline rather than an invented one. A committed real-data sample keeps this timeline check running with no credentials required. This timeline is now visible in the browser inside each event's Case Studies drill-in on the Structure page, and remains reachable through the research API and the matching machine-readable tool.
+- **A third registered strategy, `structure_tape_map` (research API)** — the app now has three registered ways of simulating trades against historical data: the original `v1`, the frozen `structure_tape` (which trades off the raw list of thousands of individual price levels), and this new one, which trades off the same small handful of tradable bands the level map produces instead. It reuses the exact same class-scaled stop/target/position-sizing rules as `structure_tape` — only which levels it watches differs. Registering it changes nothing about `v1`, `structure_tape`, or their past results. It appears as its own card in the Structure page's strategy Registry section and is exercised automatically as part of the 3-way edge report below (now also visible on the Structure page); it is runnable through the existing backtest API, but there is no button yet to pick it directly for a standalone ad hoc backtest in the browser.
+- **The 3-way profit edge report (research API)** — a new endpoint runs `v1`, `structure_tape`, and `structure_tape_map` over every recorded practice-tape window and reports, honestly, how each one actually did — broken down by price-level quality (A/B/C), which side of the market it traded (support or resistance), how price reacted at the touch (rejected, broke, or chopped), and which data feed the window came from. Every dollar figure carries its sample size, a comparison against a random-entry baseline, and the same "simulated — not indicative of live results" register used everywhere else in the app. With only the small practice dataset available today the report is honestly empty — no strategy yet has enough recorded real-world touches to report a result — rather than a manufactured one; once real trading windows are recorded it will start showing real, if still small-sample, numbers. The same comparison is available to AI tools through the machine-readable connection, byte-for-byte identical to what a person sees calling the endpoint directly. This report is now visible on the Structure page in the browser as the Edge Report, and remains reachable through the research API and the matching machine-readable tool.
 - **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `POST /research/thesis`, `GET /research/thesis/active`, `GET /research/taxonomy`, `GET /research/analytics`, `GET /research/journal`, `GET /research/journal/{id}`, `POST /research/thesis/{id}/action`, `GET /research/studies`, `POST /research/studies`, `POST /research/studies/{id}/cancel`, `GET /research/hints/active`, `GET /research/hints`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/levels`, `GET /research/tradability`, `GET /research/setups`, `GET /research/setups/{id}`, `GET /research/edge-report`, `GET /meta/ui-routes`.
 - **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, journal, studies, datasets, backtests, strategy registry, PnL ledger, bar series, support/resistance levels, tradable level maps, touch-event case studies, profit edge reports, and navigation data a person sees. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
 <!-- /AUTO:capabilities -->
diff --git a/apps/frontend/app/page.tsx b/apps/frontend/app/page.tsx
index 9aee5ec..dcf72c5 100644
--- a/apps/frontend/app/page.tsx
+++ b/apps/frontend/app/page.tsx
@@ -239,14 +239,21 @@ export default function Page() {
         {/* Tape-state prediction chart — above the cockpit, for Simulated + Historical only
             (hidden for Live, per the blueprint IA). Hidden while the stream has failed (pre- or
             post-connect) or is still waiting for its first event — there is nothing to chart yet,
-            and the chart must never invent candles. Reads GET …/history verbatim. */}
+            and the chart must never invent candles. Reads GET …/history verbatim.
+            era-5B J-06 (additive): also passes the WS snapshot's own `tape_state` so the chart can
+            draw its tradable-band overlay + confluence chip — this render gate is UNCHANGED, so
+            live mode stays byte-identical (the chart, overlay, and chip all stay hidden there). */}
         {ticker &&
           !streamFailed &&
           !snapshotFailed &&
           !snapshotWaiting &&
           !snapshotConnecting &&
           (mode === "sim" || mode === "historical") && (
-            <PriceChart ticker={ticker} thesis={snapshot?.thesis ?? null} />
+            <PriceChart
+              ticker={ticker}
+              thesis={snapshot?.thesis ?? null}
+              tapeState={snapshot?.tape_state ?? null}
+            />
           )}
         {pending && !ticker ? (
           // J-21: pending acknowledgement — shown the instant Watch is clicked, before any data.
diff --git a/apps/frontend/components/PriceChart.tsx b/apps/frontend/components/PriceChart.tsx
index 4d65477..d9f2d6a 100644
--- a/apps/frontend/components/PriceChart.tsx
+++ b/apps/frontend/components/PriceChart.tsx
@@ -14,17 +14,29 @@
 // affordance (Stay-in-scope / No-execution anti-goals).
 
 import { useEffect, useRef, useState } from "react";
-import { fetchHistory } from "@/lib/api";
+import { fetchHistory, fetchStrategies, fetchTradability } from "@/lib/api";
 import { formatDateTimeDMY } from "@/lib/datetime";
 import {
   HISTORY_BAR_SIZES,
   type HistoryBarSize,
+  type StrategiesPayload,
   type TapeHistory,
   type ThesisGeometry,
   type ThesisProjection,
+  type TradabilityResponse,
 } from "@/lib/types";
 import { Panel, EmptyHint } from "./Panel";
 
+// era-5B J-06 (additive): the cockpit gains a tradable-band overlay + a descriptive confluence
+// chip beside the existing candles/tape-state markers/thesis geometry above — sim/historical modes
+// only (the parent's existing mode gate in app/page.tsx already fully unmounts this component in
+// live mode; untouched by this addition). Bands come from GET /research/tradability (era-5B J-01);
+// the chip's rejection/breakthrough state mapping comes from GET /research/strategies's
+// `structure_tape_map` entry (era-5B J-04). Both are read VERBATIM — this component computes no
+// score, cluster, class, or mapping of its own; it only draws served fields and evaluates a display
+// conjunction (is the last price inside a served band AND does the served tape state match the
+// served mapping for that band's side).
+
 // How often we re-pull `…/history` while a ticker is watched — matches the cockpit's WS push
 // cadence so the chart accrues new candles in step with the rest of the cockpit (no 2nd socket).
 const POLL_INTERVAL_MS = 1000;
@@ -68,20 +80,45 @@ const PRICE_LINE_COLORS: Record<string, string> = {
 // Entry/exit marks render in their own slate-200 treatment, distinct from the verdict palette.
 const MARK_COLOR = "#e2e8f0"; // slate-200
 
+// The registered structure_tape_map strategy id (era-5B J-04) — mirrors app/structure/page.tsx's
+// OWN `STRATEGY_TAPE_ID = "structure_tape"` constant precedent byte-for-byte: this is a
+// REGISTRY-LOOKUP key (which entry to read off the fetched strategies list), never tape-state
+// confirmation vocabulary. The confirmation mapping itself is read off that entry's OWN
+// `rejection_states`/`breakthrough_states` fields below — never restated as a literal here.
+const STRATEGY_TAPE_MAP_ID = "structure_tape_map";
+
 export function PriceChart({
   ticker,
   thesis,
+  tapeState,
 }: {
   ticker: string | null;
   // The live thesis projection (WS `thesis` key) or null. Read VERBATIM for its `geometry`; the
   // chart derives nothing. `null` (no/cleared/resolved-non-invalidated thesis) => no overlay.
   thesis?: ThesisProjection | null;
+  // The engine-owned CURRENT tape state (era-5B J-06), read VERBATIM off the WS snapshot's own
+  // `tape_state` field — page.tsx passes `snapshot?.tape_state ?? null`, the SAME value
+  // Cockpit.tsx already renders. Drives the confluence chip's matching decision below; NEVER
+  // derived from `history.markers` here — a silent transition into `unclear` is never marked, so
+  // scanning markers for "the latest state" can go stale/wrong.
+  tapeState: string | null;
 }) {
   const [barSize, setBarSize] = useState<HistoryBarSize>(HISTORY_BAR_SIZES[0]);
   const [history, setHistory] = useState<TapeHistory | null>(null);
   // `loaded` distinguishes "haven't fetched yet" (connecting) from "fetched, genuinely empty"
   // (an empty window) so the empty treatment reads honestly in both cases.
   const [loaded, setLoaded] = useState(false);
+  // The watched symbol's tradable bands (era-5B J-06) — `phase` distinguishes "not fetched yet"
+  // from "fetched, genuinely empty" (SIM-*/no-bar-series), mirroring `loaded` above so the empty
+  // treatment is honest in both cases. Additive/non-blocking: `idle`/`loading`/`error` render
+  // nothing extra — the chart + tape markers never wait on this fetch.
+  const [tradabilityState, setTradabilityState] = useState<{
+    phase: "idle" | "loading" | "ready" | "error";
+    data: TradabilityResponse | null;
+  }>({ phase: "idle", data: null });
+  // The strategy registry (era-5B J-06) — ticker-independent config/registry data, fetched once.
+  // Supplies the confluence chip's rejection/breakthrough state mapping.
+  const [strategies, setStrategies] = useState<StrategiesPayload | null>(null);
 
   const containerRef = useRef<HTMLDivElement | null>(null);
   // Library object handles kept across renders; typed loosely because the module is loaded
@@ -94,6 +131,9 @@ export function PriceChart({
   // update REMOVES the prior lines before adding the new ones (no stale/duplicate lines) and so a
   // cleared/resolved thesis removes them entirely.
   const priceLinesRef = useRef<any[]>([]);
+  // The tradable-band price-line handles (era-5B J-06) — tracked SEPARATELY from `priceLinesRef`
+  // (the thesis geometry's own dashed lines) so redrawing one family never clobbers the other.
+  const bandPriceLinesRef = useRef<any[]>([]);
   // The latest tape-state markers (engine-owned) and thesis markers (research-owned). They share the
   // ONE series-marker primitive, so both effects funnel through `setCombinedMarkers` which sets the
   // union in a single call (lightweight-charts' setMarkers replaces the whole set).
@@ -135,6 +175,62 @@ export function PriceChart({
     };
   }, [ticker, barSize]);
 
+  // --- Fetch the watched symbol's tradable bands (era-5B J-06) -------------------------------
+  // Keyed on `[ticker, history?.epoch_anchor]` (not `barSize`, not polled every second): the
+  // morning-markup basis is date-bounded and does not move intraday, unlike the 1s `…/history`
+  // poll above — `epoch_anchor` itself is a STABLE per-watch value (the engine sets it once at
+  // watch-start; it never changes while the SAME ticker stays watched), so this still fetches at
+  // most once per watch, not on every poll tick.
+  //
+  // `as_of` is the WATCHED SESSION's own current moment, verbatim: `history.epoch_anchor` (Data
+  // Contract row 13, ALREADY fetched by the poll above — no new fetch) is "the real UTC epoch a
+  // watched session's logical time 0 maps to" — a real market epoch for a historical replay, so
+  // during e.g. the 2026-06-22 replay this correctly resolves THAT session's own prior-close basis
+  // (2026-06-18) rather than today's. Falls back to the current wall-clock time only before the
+  // first `history` response lands (first paint) or for a SIM ticker (whose synthetic anchor is
+  // moot anyway — SIM-* symbols resolve `no_bar_series_for_symbol` regardless of `as_of`). This is
+  // STILL zero client "which session" math (no-lookahead): `_resolve_basis` (tradability.py) alone
+  // decides the prior session server-side; converting an epoch-seconds field to an ISO string is
+  // the SAME pure unit/format conversion this file already does for candle timestamps above
+  // (`toClock`), never a date computation of "which session."
+  useEffect(() => {
+    if (!ticker) {
+      setTradabilityState({ phase: "idle", data: null });
+      return;
+    }
+    let cancelled = false;
+    setTradabilityState({ phase: "loading", data: null });
+    const asOf =
+      history?.epoch_anchor != null
+        ? new Date(history.epoch_anchor * 1000).toISOString()
+        : new Date().toISOString();
+    fetchTradability(ticker, asOf).then((res) => {
+      if (cancelled) return;
+      if (res.ok && res.data) {
+        setTradabilityState({ phase: "ready", data: res.data });
+      } else {
+        setTradabilityState({ phase: "error", data: null });
+      }
+    });
+    return () => {
+      cancelled = true;
+    };
+  }, [ticker, history?.epoch_anchor]);
+
+  // --- Fetch the strategy registry ONCE (era-5B J-06) -----------------------------------------
+  // Ticker-independent config/registry data (the SAME GET /research/strategies read `/structure`'s
+  // Registry section already established). Supplies the confluence chip's rejection/breakthrough
+  // state mapping — read verbatim below, never restated as a client-side literal.
+  useEffect(() => {
+    let cancelled = false;
+    fetchStrategies().then((res) => {
+      if (!cancelled && res.ok) setStrategies(res.strategies);
+    });
+    return () => {
+      cancelled = true;
+    };
+  }, []);
+
   // --- Create the chart once (client-only dynamic import, never at SSR) ---------------------
   useEffect(() => {
     if (!ticker) return;
@@ -325,10 +421,93 @@ export function PriceChart({
     setCombinedMarkers();
   }, [thesis, history]);
 
+  // --- Draw the tradable-band overlay VERBATIM (era-5B J-06) ---------------------------------
+  // One SOLID price line per band edge, colored by side — reuses StructureChart.tsx's L97-120
+  // pattern byte-for-byte. Bands are read off the served prop only; this component performs no
+  // scoring or clustering of its own. Keyed on `[tradabilityState, history]` rather than just
+  // `tradabilityState`: `history` polls every second (see POLL_INTERVAL_MS above), so if the chart
+  // series is not yet created the very first time bands resolve, the next poll tick re-runs this
+  // effect and draws them — the SAME self-healing dependency the thesis-geometry effect just above
+  // already relies on for the identical series-not-ready race.
+  useEffect(() => {
+    const series = seriesRef.current;
+    if (!series) return;
+
+    // Always clear prior band lines first (mirrors the thesis-geometry effect's own clear-then-
+    // redraw pattern) so a re-fetch or ticker change never leaves a stale/duplicate line.
+    for (const line of bandPriceLinesRef.current) {
+      try {
+        series.removePriceLine(line);
+      } catch {
+        // The series may have been disposed between renders — ignore (it is being torn down).
+      }
+    }
+    bandPriceLinesRef.current = [];
+
+    const bands = tradabilityState.data?.bands ?? [];
+    for (const band of bands) {
+      const color = band.side === "resistance" ? "#fb7185" : "#34d399"; // rose-400 / emerald-400
+      const sideLabel = band.side === "resistance" ? "R" : "S";
+      const classLabel = band.class ? ` class ${band.class}` : "";
+      const title = `${sideLabel}${classLabel} · score ${band.quality_score}${band.round_number ? " · round" : ""}`;
+      const edges =
+        band.price_low === band.price_high ? [band.price_low] : [band.price_low, band.price_high];
+      for (const price of edges) {
+        const handle = series.createPriceLine({
+          price,
+          color,
+          lineWidth: 2,
+          lineStyle: 0, // LineStyle.Solid — distinct from this component's own DASHED thesis lines
+          axisLabelVisible: true,
+          title,
+        });
+        bandPriceLinesRef.current.push(handle);
+      }
+    }
+  }, [tradabilityState, history]);
+
   if (!ticker) return null;
 
   const hasBars = !!history && history.bars.length > 0;
 
+  // --- Confluence chip (era-5B J-06) ----------------------------------------------------------
+  // A pure DISPLAY CONJUNCTION over already-fetched/served values — price-in-band × served tape
+  // state × the served rejection/breakthrough mapping. No scoring, no clustering, no client-side
+  // mapping literal: `rejectionState`/`breakthroughState` are read off the FETCHED
+  // structure_tape_map entry, never restated (the only place this file hardcodes the four tape-
+  // state names is the pre-existing MARKER_COLORS/STATE_LABELS cosmetic dicts above, unrelated to
+  // this decision).
+  const lastPrice =
+    history && history.bars.length > 0 ? history.bars[history.bars.length - 1].close : null;
+  const bands = tradabilityState.data?.bands ?? [];
+  const matchedBand =
+    lastPrice != null
+      ? bands.find((b) => lastPrice >= b.price_low && lastPrice <= b.price_high) ?? null
+      : null;
+  // Structural side->direction reading (named explicitly in the phase spec's Notes — NOT tape-state
+  // vocabulary): a resistance band defends a ceiling (a short-direction reading); a support band
+  // defends a floor (a long-direction reading).
+  const direction: "long" | "short" | null =
+    matchedBand == null ? null : matchedBand.side === "resistance" ? "short" : "long";
+  const mapEntry = strategies?.strategies.find((s) => s.strategy_id === STRATEGY_TAPE_MAP_ID)?.entries;
+  const rejectionState = direction ? mapEntry?.rejection_states?.[direction] : undefined;
+  const breakthroughState = direction ? mapEntry?.breakthrough_states?.[direction] : undefined;
+  const matchKind: "rejection" | "breakthrough" | null =
+    tapeState != null && tapeState === rejectionState
+      ? "rejection"
+      : tapeState != null && tapeState === breakthroughState
+        ? "breakthrough"
+        : null;
+  const confluence = matchedBand && matchKind ? { band: matchedBand, kind: matchKind } : null;
+
+  // Honest "no tradable map" state (SIM-*/no-bar-series symbols) — shown ONLY once the bands fetch
+  // genuinely resolved empty, never while still loading/failed (the overlay/chip are a pure
+  // ADDITION that never blocks or degrades the chart/markers above).
+  const tradabilityEmpty =
+    tradabilityState.phase === "ready" &&
+    !!tradabilityState.data &&
+    (tradabilityState.data.no_bar_series_for_symbol || tradabilityState.data.bands.length === 0);
+
   return (
     <Panel title="Price Chart — Tape-State Markers" className="mb-4">
       <div className="mb-3 flex items-center gap-2">
@@ -368,6 +547,29 @@ export function PriceChart({
           </div>
         )}
       </div>
+
+      {/* era-5B J-06: the tradable-band overlay's companion strip. Additive/non-blocking — while
+          the bands fetch is idle/loading/failed this renders nothing, so the chart + tape markers
+          above never wait on it. Neutral slate "factual stamp" styling (mirrors
+          FeedBasisBadge.tsx's chip family) — this app reserves amber for degraded/empty/truncated
+          states; a confluence chip is a positive descriptive signal, not a warning. */}
+      {confluence && (
+        <div
+          data-testid="confluence-chip"
+          className="mt-3 rounded bg-slate-800 px-2.5 py-1.5 text-xs text-slate-300"
+        >
+          Inside {confluence.band.side === "resistance" ? "R" : "S"}-band{" "}
+          {confluence.band.price_low.toFixed(2)}–{confluence.band.price_high.toFixed(2)}
+          {confluence.band.class ? ` (class ${confluence.band.class})` : ""} · tape:{" "}
+          {STATE_LABELS[tapeState ?? ""] ?? tapeState} ({confluence.kind}) · measured history:{" "}
+          edge report
+        </div>
+      )}
+      {tradabilityEmpty && (
+        <div className="mt-3" data-testid="no-tradable-map">
+          <EmptyHint>No tradable map for {ticker}.</EmptyHint>
+        </div>
+      )}
     </Panel>
   );
 }
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index b1faf36..3b13410 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -1069,12 +1069,28 @@ export interface StrategyExits {
   dataset_end: { rule: string };
 }
 
+// One strategy's `entries` block (GET /research/strategies). `rule` is the one field every
+// strategy shares; the rest are present ONLY where the backend's OWN grammar carries them
+// (`structure_tape` / `structure_tape_map`'s `structure_level_tape_confirmation` rule —
+// config.py:1516-1523) — v1's `entries` carries only `rule` (an honest field omission, never a
+// fabricated value for v1). `rejection_states`/`breakthrough_states` are the era-5B J-06 cockpit
+// confluence chip's OWN mapping source (Record<direction, tape-state-name>) — read verbatim by
+// PriceChart.tsx, never restated as a client-side literal.
+export interface StrategyEntries {
+  rule: string;
+  proximity_band_bps?: number;
+  rejection_states?: Record<"long" | "short", string>;
+  breakthrough_states?: Record<"long" | "short", string>;
+  arm_cooldown_seconds?: number;
+  concurrency?: string;
+}
+
 // One registered strategy (GET /research/strategies — Data Contract row 40/41). `size_multiple_by_class`
 // is present ONLY on structure_tape (v1 has no class-scaled simulated size) — an honest field
 // omission, never a fabricated map for v1.
 export interface Strategy {
   strategy_id: string;
-  entries: { rule: string };
+  entries: StrategyEntries;
   exits: StrategyExits;
   fees: { per_share: number; min_per_trade: number };
   slippage: { spread_fraction: number };
diff --git a/apps/backend/tests/test_price_chart_confluence.py b/apps/backend/tests/test_price_chart_confluence.py
new file mode 100644
index 0000000..1f304e0
--- /dev/null
+++ b/apps/backend/tests/test_price_chart_confluence.py
@@ -0,0 +1,218 @@
+"""Structural guards for the cockpit tradable-band overlay + confluence chip (era-5B J-06).
+
+PriceChart.tsx has no frontend test runner behind it (no `test` npm script, no `.test.ts(x)` file
+anywhere in this repo — see every prior era-5B iteration's dev handoff); this repo's established
+precedent for testing frontend LOGIC keylessly is a Python source-inspection test that reads the
+`.tsx` source directly (test_profile_equivalence.py's `test_performance_page_offers_no_profile_
+selection_control`, test_strategies_api.py's `test_strategies_module_carries_no_second_copy_of_
+the_id_strings`, and this module's own sibling test_copy_discipline.py's frontend-literal scan).
+This module extends that precedent to J-06's two hardest-to-verify-by-inspection invariants:
+
+  1. the confluence chip's "which tape state confirms this band's side" decision reads the SERVED
+     `/research/strategies` `structure_tape_map` mapping — never a client-hardcoded literal of one
+     of the four tape-state names (single-source-of-truth / no-client-recomputation);
+  2. the band overlay's fetch is keyed on `ticker` alone and passes the CURRENT wall-clock time as
+     `as_of` (no client-side "which is the prior session" date arithmetic — the no-lookahead
+     resolution is entirely server-side, in `tradability.py`'s own `_resolve_basis`).
+
+Copy-discipline coverage (imperative/prediction/claim language in the new chip text) is NOT
+duplicated here: `test_copy_discipline.py::test_lint_frontend_source_literals_are_clean` already
+walks every `.tsx` string literal under `apps/frontend/components/**` and `apps/frontend/app/**`,
+so it automatically covers PriceChart.tsx's new chip copy.
+"""
+
+from __future__ import annotations
+
+import re
+from pathlib import Path
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+FRONTEND_DIR = BACKEND_DIR.parent / "frontend"
+PRICE_CHART = FRONTEND_DIR / "components" / "PriceChart.tsx"
+PAGE_TSX = FRONTEND_DIR / "app" / "page.tsx"
+
+# The four tape-state names the confirmation MAPPING may name. Legitimate ONLY inside the
+# pre-existing MARKER_COLORS / STATE_LABELS cosmetic marker color/label dicts (unrelated to the
+# confluence-matching decision) — every other occurrence would be a hardcoded restatement of the
+# server-owned `rejection_states` / `breakthrough_states` mapping.
+_TAPE_STATE_NAMES = ("bid_absorption", "ask_absorption", "buyer_control", "seller_control")
+_STATE_LITERAL = re.compile(r'["\'](' + "|".join(_TAPE_STATE_NAMES) + r')["\']')
+
+
+def _source() -> str:
+    assert PRICE_CHART.exists(), f"expected {PRICE_CHART} to exist"
+    return PRICE_CHART.read_text()
+
+
+def _excluded_literal_lines(lines: list[str]) -> set[int]:
+    """Line indices (0-based) inside the pre-existing MARKER_COLORS / STATE_LABELS object-literal
+    blocks — the ONE allowed place a bare tape-state-name string literal may appear (cosmetic
+    marker color/label lookups, unrelated to the chip's confirmation decision)."""
+    excluded: set[int] = set()
+    in_block = False
+    for i, line in enumerate(lines):
+        if re.search(r"const (MARKER_COLORS|STATE_LABELS)\s*:", line):
+            in_block = True
+        if in_block:
+            excluded.add(i)
+        if in_block and line.strip().startswith("};"):
+            in_block = False
+    return excluded
+
+
+def test_confluence_matching_has_no_hardcoded_tape_state_literal():
+    """The chip's "does the tape confirm this band's side" decision must compare the served
+    `tapeState` prop against the FETCHED `structure_tape_map` entry's `rejection_states` /
+    `breakthrough_states` fields — never a client-hardcoded copy of one of the four state names.
+    Scoped to exclude the pre-existing MARKER_COLORS/STATE_LABELS dicts (cosmetic marker
+    color/label lookups that already hardcode all four names for an unrelated purpose)."""
+    lines = _source().splitlines()
+    excluded = _excluded_literal_lines(lines)
+    offenders = [
+        (i + 1, line.strip())
+        for i, line in enumerate(lines)
+        if i not in excluded and _STATE_LITERAL.search(line)
+    ]
+    assert not offenders, (
+        "hardcoded tape-state-name literal found outside the allowed MARKER_COLORS/STATE_LABELS "
+        f"dicts (must instead read off the served /research/strategies mapping): {offenders}"
+    )
+
+
+def test_confluence_matching_reads_rejection_and_breakthrough_off_the_served_entry():
+    """`rejection_states` / `breakthrough_states` must appear as PROPERTY READS (`.rejection_states`
+    / `.breakthrough_states` — reading a field off the fetched strategies payload) — never as
+    object-literal KEYS (`rejection_states:` / `breakthrough_states:`), which would mean the
+    component declared its OWN restated copy of the mapping shape instead of reading the served
+    one."""
+    source = _source()
+    assert ".rejection_states" in source, "expected a read of the served entry's rejection_states field"
+    assert ".breakthrough_states" in source, "expected a read of the served entry's breakthrough_states field"
+    assert "rejection_states:" not in source, (
+        "found an object-literal `rejection_states:` KEY — the mapping must be READ off the served "
+        "payload, never restated as a local object literal"
+    )
+    assert "breakthrough_states:" not in source, (
+        "found an object-literal `breakthrough_states:` KEY — the mapping must be READ off the "
+        "served payload, never restated as a local object literal"
+    )
+
+
+def test_confluence_selects_structure_tape_map_strategy_entry():
+    """The chip must look up the `structure_tape_map` entry specifically (the registered strategy
+    this era's rejection/breakthrough mapping lives on) — mirrors app/structure/page.tsx's OWN
+    `STRATEGY_TAPE_ID = "structure_tape"` constant precedent (a registry-lookup key literal is
+    legitimate; it is not tape-state confirmation vocabulary)."""
+    source = _source()
+    assert "structure_tape_map" in source
+    assert "fetchStrategies" in source
+
+
+def test_tradability_bands_fetch_is_keyed_on_ticker_and_stable_session_anchor_not_polled():
+    """The bands fetch must be keyed on `[ticker, history?.epoch_anchor]` — NOT on `barSize`, and
+    NOT folded into the existing 1s `setInterval` history poll. `epoch_anchor` is a STABLE per-watch
+    value (the engine sets it once at watch-start and it never changes while the same ticker stays
+    watched), so keying on it still fetches at most once or twice per watch (not every poll tick) —
+    the tradable map is date-bounded and does not move intraday, unlike the tape-history poll."""
+    source = _source()
+    idx = source.index("fetchTradability(")
+    tail = source[idx : idx + 900]
+    m = re.search(r"\},\s*\[([^\]]*)\]\s*\)\s*;", tail)
+    assert m, "could not find the enclosing effect's dependency array after the fetchTradability( call"
+    deps = m.group(1).strip()
+    assert deps == "ticker, history?.epoch_anchor", (
+        f"expected the bands effect to be keyed on [ticker, history?.epoch_anchor], found deps={deps!r}"
+    )
+
+
+def test_tradability_as_of_uses_the_watched_sessions_own_anchor_with_no_client_side_session_math():
+    """`as_of` must be the WATCHED SESSION's own current moment: `history.epoch_anchor` (Data
+    Contract row 13, already fetched by the existing history poll — no new fetch) converted to an
+    ISO string, falling back to the current wall-clock time only before the first `history`
+    response lands. This is what makes a HISTORICAL replay of a PAST session (e.g. 2026-06-22)
+    resolve THAT session's own prior-close basis (2026-06-18) — using the browser's wall-clock
+    "now" instead would resolve TODAY's basis, which is unrelated to whatever price action is being
+    replayed (verified empirically: a live AAPL 2026-06-22 replay showed no band anywhere near the
+    replayed price when as_of was wall-clock "now"). No-lookahead guard: the frontend must contain
+    no local "prior session" date arithmetic — `_resolve_basis` (tradability.py) alone decides the
+    prior session server-side; this only supplies WHICH moment to resolve from."""
+    source = _source()
+    idx = source.index("fetchTradability(")
+    call_site = source[idx : idx + 60]
+    assert "asOf" in call_site, "expected fetchTradability to be called with a computed `asOf` variable"
+    # The `asOf` computation itself, just above the call site.
+    as_of_computation = source[max(0, idx - 400) : idx]
+    assert "history?.epoch_anchor" in as_of_computation or "history.epoch_anchor" in as_of_computation, (
+        "expected the as_of computation to read history's epoch_anchor field"
+    )
+    assert "epoch_anchor * 1000" in as_of_computation, (
+        "expected epoch_anchor (seconds) to be converted to ms the SAME way this file already does "
+        "for candle timestamps (toClock), not a fresh unit convention"
+    )
+    assert "new Date().toISOString()" in as_of_computation, (
+        "expected a current-wall-clock-time fallback for before the first history response lands"
+    )
+    banned_session_math = [
+        "getPreviousTradingDay",
+        "priorSession",
+        "previousSession",
+        "subtractDays",
+        "setDate(",
+        "getDay()",
+    ]
+    offenders = [b for b in banned_session_math if b in source]
+    assert not offenders, f"found apparent client-side prior-session date arithmetic: {offenders}"
+
+
+def test_strategies_fetched_once_on_mount_not_per_ticker():
+    """`fetchStrategies()` is ticker-independent config/registry data — it must be fetched in an
+    effect with an EMPTY dependency array (mount-only), not re-fetched per ticker/tick."""
+    source = _source()
+    idx = source.index("fetchStrategies(")
+    tail = source[idx : idx + 500]
+    m = re.search(r"\},\s*\[([^\]]*)\]\s*\)\s*;", tail)
+    assert m, "could not find the enclosing effect's dependency array after the fetchStrategies() call"
+    deps = m.group(1).strip()
+    assert deps == "", f"expected the strategies effect to be mount-only ([]), found deps={deps!r}"
+
+
+def test_band_overlay_reads_only_served_band_fields():
+    """The band overlay must draw ONLY served `TradabilityBand` fields (verbatim, reusing
+    StructureChart.tsx's L97-120 pattern) — no local scoring/clustering. Checks for the exact
+    property-access substrings the served shape provides."""
+    source = _source()
+    for field in (
+        "band.side",
+        "band.price_low",
+        "band.price_high",
+        "band.class",
+        "band.quality_score",
+        "band.round_number",
+    ):
+        assert field in source, f"expected the band overlay to read {field} verbatim"
+    assert "createPriceLine" in source
+
+
+def test_no_tradable_map_empty_state_present():
+    """A SIM-*/no-bar-series symbol must show an explicit, honest 'no tradable map' state — never a
+    fabricated band. Reuses the pre-existing `EmptyHint` component (already imported)."""
+    source = _source()
+    assert "no_bar_series_for_symbol" in source
+    assert re.search(r"no tradable map", source, re.IGNORECASE)
+    assert source.count("<EmptyHint") >= 2, (
+        "expected a SECOND EmptyHint usage beyond the pre-existing 'no price history' one"
+    )
+
+
+def test_page_threads_tape_state_prop_and_preserves_live_mode_gate():
+    """`page.tsx` must pass the WS-snapshot's own `tape_state` field into `PriceChart` as the new
+    `tapeState` prop, WITHOUT touching the pre-existing sim/historical-only render gate (the gate
+    alone is what keeps live mode byte-identical — the iter-7 plan's explicit "do not touch"
+    instruction)."""
+    source = PAGE_TSX.read_text()
+    assert "tapeState={snapshot?.tape_state ?? null}" in source, (
+        "expected page.tsx to pass tapeState={snapshot?.tape_state ?? null} into PriceChart"
+    )
+    assert '(mode === "sim" || mode === "historical")' in source, (
+        "the live-mode gate must be present and unchanged"
+    )
```
