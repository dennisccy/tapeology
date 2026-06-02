# Project Goal

## Vision

Tapeology is a **standalone, real-time tape-reading system for US stocks**. It does one
thing well: given a single ticker, it watches live order flow — trades, quotes, and
(later) the Level 2 book — and classifies the **current tape state**.

Its defining principle is **price impact, not raw aggression**. The question is never
just "are buyers buying?" but "when buyers buy aggressively, does price actually move
higher — or are they being absorbed?" — and symmetrically for sellers. A tape where
aggressive sell volume is high yet price refuses to fall is **bid absorption**, not
seller control, and Tapeology must say so.

Tapeology is deliberately narrow. It is **not** a scanner, not news/theme/fundamental
analysis, not charting, not an execution or portfolio system — those are separate
projects. Tapeology receives a ticker (from a user or an upstream system) and answers one
question: *what is the tape doing right now, and how confident are we?*

Phase 1 runs entirely on **simulated market data** with a small set of hand-crafted
scenarios, so the engine's correctness is proven deterministically before any real feed
is attached. The data source sits behind a **replaceable provider interface**; real
trades/quotes/L2 drop in later without touching the engine. The MVP recognizes five tape
states — **buyer_control, seller_control, bid_absorption, ask_absorption, unclear** —
surfaced one ticker at a time in a simple Next.js UI alongside the live features that
justify them.

## Target Users

- A discretionary US-equity trader who already knows *which* ticker to watch and wants a
  fast, honest read on whether the current tape favors buyers, favors sellers, or is
  absorbing aggression.
- An upstream system (scanner, alerting, or another project) that pushes a ticker to
  Tapeology and consumes the resulting tape state over REST/WebSocket.
- The developer/operator validating the engine against known simulated scenarios.

## Success Criteria

The first success metric is **not** profit. In priority order:

- **Classifies known simulated scenarios.** For each of the five MVP scenarios
  (buyer_control, seller_control, bid_absorption, ask_absorption, unclear_chop) the engine
  reaches the expected tape state with reasonable confidence within a bounded warm-up,
  proven by an automated test per scenario.
- **Surfaces the read in the UI.** Watching a ticker shows, for that one ticker, live
  bid/ask/spread/last, recent trades, the core features, the current tape state, a
  confidence score, plain-language observations, and an event log — all driven by the
  engine and updating live over WebSocket.
- **Price impact, not aggression.** Absorption is detected specifically: high aggressive
  volume on one side with little/no price progress resolves to the matching absorption
  state rather than "control".
- **Single source of truth.** Tape state, features, and confidence for a ticker are
  computed exactly once in the engine and read identically by REST, WebSocket, and the UI.
- **Replaceable data.** The Phase-1 simulator and any future live provider sit behind one
  provider interface; swapping the source changes neither the engine nor the API.
- *(later)* **Predictive value.** On historical/replay data, high-confidence tape states
  show measurable directional edge over the next 10 / 30 / 60 / 120 seconds.

## Key Capabilities

1. **Provider abstraction** for the live event stream: a deterministic, seedable
   **SimulatedProvider** (default; no network, no keys) and a swappable real provider
   (trades, quotes, L2) selected by config. The engine consumes provider events and never
   knows the source.
2. **Core input events**: `TradeEvent` (ticker, timestamp, price, size, side ∈
   {buy, sell, unknown}); `QuoteEvent` (ticker, timestamp, bid, ask, bid_size, ask_size);
   and later `BookLevelEvent` (ticker, timestamp, side ∈ {bid, ask}, price, size, level).
3. **Trade aggressor classification**: trade price ≥ current ask ⇒ aggressive buy; price ≤
   current bid ⇒ aggressive sell; otherwise unknown — using the quote in effect at the
   trade's timestamp.
4. **Rolling feature windows** maintained concurrently at **10s, 30s, 60s, 180s, 300s**.
5. **Core features** per window: `trade_speed`, `volume_speed`, `aggressive_buy_ratio`,
   `aggressive_sell_ratio`, `net_aggressive_volume`, `large_print_count`,
   `average_spread`, `spread_change`, `buy_price_impact`, `sell_price_impact`,
   `absorption_score`, `bid_refresh_score`, `ask_refresh_score`, `liquidity_imbalance`.
   *(later)* `liquidity_pull_score`.
6. **Tape-state classifier** mapping features → one MVP state + a confidence score + a
   short list of human-readable observations:
   - **buyer_control** — high aggressive_buy_ratio, positive buy_price_impact, stable
     spread, elevated trade_speed.
   - **seller_control** — high aggressive_sell_ratio, negative sell_price_impact, stable
     spread, elevated trade_speed.
   - **bid_absorption** — high aggressive sell volume, price does not move meaningfully
     lower, bid appears to refresh, seller impact weakens.
   - **ask_absorption** — high aggressive buy volume, price does not move meaningfully
     higher, ask appears to refresh, buyer impact weakens.
   - **unclear** — mixed signals, weak evidence, wide spread, low trade_speed, or no clean
     price impact.
7. **Watch lifecycle**: start/stop watching a ticker; each watched ticker has an
   independent engine instance fed by the provider.
8. **REST + WebSocket API**: `POST /watch/{ticker}`, `DELETE /watch/{ticker}`,
   `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`,
   `GET /tape/{ticker}/summary`, `WS /tape/{ticker}/stream`.
9. **Simple single-ticker Next.js UI** showing the panels in Success Criteria, with a live
   event log and observations — not a complex trading platform.
10. **Event-log / observation generation**: the engine emits discrete, human-readable
    messages on meaningful transitions, e.g. "Buyer aggression increasing", "Seller
    aggression increasing", "Large sell print absorbed", "Large buy print absorbed", "Ask
    refreshing at <price>", "Bid refreshing at <price>", "Tape state changed to
    buyer_control", "Tape state changed to unclear".
11. **Five simulated scenarios** that deterministically drive the engine toward each MVP
    state: buyer_control, seller_control, bid_absorption, ask_absorption, unclear_chop.
12. *(nice-to-have, later)* Optional extended states: `fake_breakout_risk`,
    `fake_breakdown_risk`, `liquidity_pull`, `liquidity_stack`, `exhaustion`.
13. *(nice-to-have, later)* Level 2 book ingestion (`BookLevelEvent`) and
    `liquidity_pull_score` / liquidity-stack features.
14. *(nice-to-have, later)* Persistence (PostgreSQL / Redis / Parquet / DuckDB) — only if a
    concrete need arises; Phase 1 is in-memory.
15. *(nice-to-have, later)* Replay/backtest harness measuring predictive value of
    high-confidence states over 10 / 30 / 60 / 120 s.

## Non-Goals

- No stock scanning or screening.
- No news, theme, or sentiment analysis.
- No chart-pattern scanning or technical-indicator charting.
- No fundamental analysis.
- No trade execution, order placement, or broker/brokerage integration.
- No portfolio or position management.
- No machine learning in the first version — the MVP classifier is rule/threshold-based.
- No multi-ticker dashboard or watchlist grid — the UI shows one ticker at a time.
- No persistence in Phase 1 (in-memory only); a datastore is added later only if needed.
- No claim or implication that the system is profitable, and nothing presented as trading
  advice.

## Constraints

- **Backend:** Python 3.12+, FastAPI (uvicorn ASGI). Python is the implementation language
  — explicitly not Rust.
- **Frontend:** Next.js (App Router) + TypeScript; a simple single-ticker UI.
- **Real-time transport:** WebSocket for live state/feature/event push; REST for
  request/response.
- **Phase-1 data:** simulated only, deterministic and seedable for reproducible tests.
- **Provider interface:** trades, quotes, and (later) L2 come from a replaceable provider;
  the engine and API are provider-agnostic.
- **In-memory Phase 1:** rolling windows and state live in process memory; optional
  PostgreSQL/Redis/Parquet/DuckDB only if later needed.
- **No magic numbers:** every window length, threshold, large-print size, impact/absorption
  cutoff, and confidence boundary comes from config — no such literal in engine code.
- **Deterministic engine:** the same ordered event stream (and seed) yields identical
  features, state, and confidence — no wall-clock or randomness in classification.
- **No secrets in source:** any future provider API keys come from environment/config,
  never committed.

## Design Direction

- **Visual style:** clean, dense, instrument-panel feel — a single-ticker "tape cockpit".
  Monospaced numerics for prices/sizes; calm dark surface, restrained color.
- **Color semantics:** green = buy-side aggression / positive impact; red = sell-side
  aggression / negative impact; neutral/amber = absorption or unclear. Color encodes side
  and impact consistently everywhere.
- **Mood:** fast, honest, legible at a glance; no clutter, no chrome that isn't
  information.
- **Reference:** the trade blotter / Level-2 montage of a pro trading terminal, distilled
  to one ticker and one verdict.

## Product Shape

### Navigation / information architecture

- **Watch (`/`)** — the single-ticker tape cockpit and the app's home. A ticker input
  (`POST /watch` on submit) plus the live read for the watched ticker: bid / ask / spread /
  last, recent trades, the core feature readouts, the current **tape state** +
  **confidence**, the **observations** list, and the **event log**. Everything streams over
  `WS /tape/{ticker}/stream`. Phase 1 is exactly one screen; a small indicator shows which
  simulated scenario the watched ticker is replaying.

### API surface (Phase 1)

- `POST /watch/{ticker}` — begin watching; spins up an engine instance fed by the provider.
- `DELETE /watch/{ticker}` — stop watching; tears the instance down.
- `GET /tape/{ticker}/state` — current tape state + confidence (canonical).
- `GET /tape/{ticker}/features` — current per-window feature values (canonical).
- `GET /tape/{ticker}/events` — recent trade/quote events + emitted observations.
- `GET /tape/{ticker}/summary` — compact snapshot (quote, last, state, confidence, headline
  features).
- `WS /tape/{ticker}/stream` — live push of state, features, quote/last, and event-log
  messages.

### Canonical values (single source of truth — computed once in the engine, displayed identically everywhere)

- **Tape state** (buyer_control | seller_control | bid_absorption | ask_absorption |
  unclear) — classified once per engine tick; REST, the WS stream, and the UI show the same
  value.
- **Confidence score** — produced once with the state by the classifier; never recomputed
  in the API or UI.
- **Core features** (the 14 MVP features, per window) — computed once in the feature
  engine; `…/features`, the stream, and the UI read the same numbers.
- **Current bid / ask / spread / last** — derived once from the latest quote/trade;
  identical across REST, WS, and UI (spread = ask − bid).
- **Observations & event-log messages** — generated once by the engine on transitions; the
  stream and UI render the same messages (no UI-side re-derivation).

## Must-have user journeys

Each journey is browser-verifiable against Phase-1 simulated data. A watched ticker is
bound to a known simulated scenario (reserved sim tickers), so the expected tape state is
deterministic. Simulated scenarios run on an accelerated clock, so each resolves within
seconds (a browser journey need not wait the full 60–300 s of real window time).

- **J-01: Watch a ticker and see the live tape cockpit**
  - Steps:
    1. Visit `/`
    2. Enter the buyer-control sim ticker (`SIM-BUYER`) and submit (Watch)
    3. Wait for the stream to connect and the panels to populate
    4. Read the bid/ask/spread/last panel; the recent-trades list; the feature readouts;
       the tape-state panel; the confidence score; the observations list; the event log
  - Acceptance: within the scenario's warm-up, every panel renders live values —
    bid/ask/spread/last are numeric and spread = ask − bid; the recent-trades list shows
    trades with price/size/side; trade_speed, aggressive_buy_ratio, aggressive_sell_ratio,
    net_aggressive_volume, buy_price_impact, and sell_price_impact each show a number; the
    tape-state panel shows one of the five states with a confidence score; the observations
    list and event log each show at least one message; and values update over the WebSocket
    without a page reload.

- **J-02: Buyer-control scenario is identified**
  - Steps:
    1. Visit `/`, watch `SIM-BUYER`
    2. Let the scenario stream until the tape state stabilizes
    3. Read the tape-state panel, confidence, and the buy/sell price-impact readouts
  - Acceptance: the tape state settles on **buyer_control** with confidence ≥ the configured
    "reasonable" threshold; aggressive_buy_ratio reads high and buy_price_impact reads
    positive; the event log contains "Tape state changed to buyer_control".

- **J-03: Seller-control scenario is identified**
  - Steps:
    1. Visit `/`, watch `SIM-SELLER`
    2. Let it stream until the state stabilizes
    3. Read the tape-state panel, confidence, and price-impact readouts
  - Acceptance: the tape state settles on **seller_control** with confidence ≥ threshold;
    aggressive_sell_ratio reads high and sell_price_impact reads negative; the event log
    shows "Tape state changed to seller_control".

- **J-04: Bid absorption is detected (price impact, not aggression)**
  - Steps:
    1. Visit `/`, watch `SIM-BIDABS`
    2. Let it stream until the state stabilizes
    3. Read the tape state, the aggressive-sell readout, the last-price movement, and the
       absorption / bid-refresh readouts
  - Acceptance: although aggressive **sell** volume is high, the last price does **not** move
    meaningfully lower; the tape state settles on **bid_absorption** (not seller_control)
    with confidence ≥ threshold; absorption_score / bid_refresh_score read elevated and the
    event log shows an absorption message (e.g. "Large sell print absorbed" / "Bid
    refreshing at <price>"). This is the defining price-impact case: high aggression + no
    price progress ⇒ absorption.

- **J-05: Ask absorption is detected (price impact, not aggression)**
  - Steps:
    1. Visit `/`, watch `SIM-ASKABS`
    2. Let it stream until the state stabilizes
    3. Read the tape state, the aggressive-buy readout, the last-price movement, and the
       absorption / ask-refresh readouts
  - Acceptance: although aggressive **buy** volume is high, the last price does **not** move
    meaningfully higher; the tape state settles on **ask_absorption** (not buyer_control)
    with confidence ≥ threshold; absorption_score / ask_refresh_score read elevated and the
    event log shows an absorption message (e.g. "Large buy print absorbed" / "Ask refreshing
    at <price>").

- **J-06: Unclear / choppy tape is reported as unclear**
  - Steps:
    1. Visit `/`, watch `SIM-CHOP`
    2. Let it stream
    3. Read the tape-state panel and confidence
  - Acceptance: the tape state reads **unclear** (mixed signals / wide spread / low
    trade_speed / no clean price impact) with low confidence; the UI does not assert buyer
    or seller control. The system honestly says "unclear" rather than forcing a directional
    call.

- **J-07: Tape-state transitions are announced in the event log and observations**
  - Steps:
    1. Visit `/`, watch a scenario ticker from a cold start
    2. Watch the event log and observations as the engine warms up and the state resolves
    3. Note the messages emitted as the state changes
  - Acceptance: as the engine moves from its initial unclear read to the scenario's resolved
    state, the event log records a "Tape state changed to …" message at the transition and
    the observations list reflects current evidence (e.g. "Buyer aggression increasing",
    "Large sell print absorbed", "Ask refreshing at <price>"). Messages append live over the
    WebSocket.

- **J-08: REST and the live UI agree (single source of truth)**
  - Steps:
    1. Visit `/`, watch a scenario ticker and let the state stabilize
    2. Read the tape state, confidence, and key features shown in the UI
    3. In a new tab, open `GET /tape/{ticker}/state` and `GET /tape/{ticker}/features` for
       the same ticker
  - Acceptance: the tape state and confidence from the REST endpoint exactly match the UI for
    that ticker, and the feature values from `…/features` match the UI's feature readouts —
    one engine value per metric, read identically by REST, the WS stream, and the UI (no
    divergence between views).

- **J-09: Stop watching a ticker**
  - Steps:
    1. Visit `/`, watch a scenario ticker
    2. Use the UI control that issues `DELETE /watch/{ticker}`
    3. Observe the UI
  - Acceptance: after stopping, the live stream for that ticker closes and the cockpit
    returns to an idle/empty state with no further updates; re-watching the same ticker
    starts a fresh read.

## Anti-goals

- **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and
  MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the
  tape. *(critical)*
- **Stay in scope.** No stock scanner/screener, no news/theme/sentiment analysis, no
  fundamental analysis, no chart-pattern or indicator charting, no portfolio/position
  management — these belong to separate projects and MUST NOT be built here. *(critical)*
- **Price impact over raw aggression.** The classifier MUST distinguish absorption from
  control: a tape with high one-sided aggression but no corresponding price progress MUST
  resolve to the matching absorption state (bid_absorption / ask_absorption), never to
  seller_control / buyer_control. Keying on aggression ratios alone is a defect. *(critical)*
- **Honest uncertainty.** When evidence is weak or mixed, the spread is wide, or there is no
  clean price impact, the state MUST be `unclear` with low confidence. The system MUST NOT
  manufacture a directional call to look decisive. *(critical)*
- **No fabricated data.** On a provider gap/failure the system MUST surface an explicit
  stale/no-data state and MUST NOT synthesize trades, quotes, prices, or a tape state to
  force a green journey. *(critical)*
- **Single source of truth.** Tape state, confidence, and each feature MUST be computed
  exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and
  frontend MUST NOT recompute them. The same ticker MUST NOT show different values across
  views. *(critical)*
- **No magic numbers.** Every window length, threshold, large-print size, impact/absorption
  cutoff, and confidence boundary MUST come from config — no such literal in
  engine/classifier code.
- **Provider-agnostic engine.** The engine and API MUST depend only on the provider interface
  (TradeEvent / QuoteEvent / BookLevelEvent); swapping the simulator for a real feed MUST NOT
  require engine or API changes.
- **Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine
  MUST produce identical features, state, and confidence; classification MUST NOT depend on
  wall-clock time or randomness. Each simulated scenario MUST have an automated test asserting
  the expected state is reached with reasonable confidence.
- **No ML in v1.** The MVP classifier MUST be transparent rule/threshold logic over named
  features — no trained model in the first version.
- **No trade/profit claims.** The product MUST NOT claim profitability or present output as
  trading advice; tape state is descriptive, not prescriptive.
- **No secrets in source.** No API keys, tokens, or credentials committed; any future provider
  keys come from environment/config only.
