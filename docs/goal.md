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
analysis, not a general charting/technical-analysis platform, not an execution or portfolio system — those are separate
projects. Tapeology receives a ticker (from a user or an upstream system) and answers one
question: *what is the tape doing right now, and how confident are we?*

The **deterministic, seedable simulator** proved the engine's correctness first and remains the
default, offline, no-keys foundation. **Real US-equity market data is now in scope**, in two
modes that reuse the exact same engine: **live** (streaming real trades/quotes in real time) and
**historical replay** (fetching a chosen past date/time window and replaying it at a selectable
speed). Both sit behind the same **replaceable provider interface**; **Alpaca** is the first real
vendor (free **IEX** feed by default) behind a **vendor-agnostic adapter**, so another vendor
(Polygon, Databento, …) can be added without touching the engine or API. The five tape states —
**buyer_control, seller_control, bid_absorption, ask_absorption, unclear** — are surfaced one
ticker at a time in a simple Next.js UI, identically for simulated, live, or replayed real data.

To turn that read into something **testable**, Tapeology also plots the watched price as a
**candlestick chart** and overlays **markers at meaningful tape-state transitions** (for simulated
data and historical replay), so a user can see whether a state actually preceded the next move —
the one focused chart the product allows, not a general charting platform. A watched session can be
**paused and resumed** without losing what is on screen, and historical windows are chosen in the
user's **local time** with US-market-session quick-picks.

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
- **Replaceable data.** The simulator and the real providers sit behind one provider interface;
  swapping the source (or the vendor) changes neither the engine nor the API.
- **Live real data.** With vendor credentials configured, watching a real US symbol during market
  hours streams real trades + quotes through the same engine and classifies the live tape state —
  the identical pipeline the simulator uses.
- **Historical replay.** Watching a real symbol over a chosen past date/time window fetches its
  real trades + quotes and replays them through the engine at a selectable speed; the resulting
  read is reproducible for a fixed symbol + window.
- **Real-data honesty.** An unknown symbol, an empty window, a closed market, missing credentials,
  and a live-feed gap each surface an explicit error or `stale` state — never a fabricated tape.
- **Resolved aggressor side.** On real (historical and live) data the aggressor side is resolved
  for the vast majority of prints via the quote rule plus a tick-test fallback; only a genuinely
  undecidable print (no quote and no prior trade) remains `unknown`. Historical recent-trades is no
  longer dominated by `unknown`.
- **Tape-state prediction chart.** For simulated data and historical replay, the cockpit plots the
  price as candlesticks (selectable 10 / 30 / 60 s bars) and marks meaningful tape-state
  transitions, so a user can visually judge whether a state preceded the subsequent price move.
- **Pause / resume.** A watched session can be paused and resumed without tearing it down or
  clearing the UI; replay resumes deterministically and live resumes at current real data.
- **Local-time historical selection.** Historical windows are entered in the user's local timezone
  (with an explicit zone label and US-session quick-picks); the window fetched from the vendor
  matches the local window selected — no silent timezone shift.
- *(later)* **Predictive value, measured.** Beyond the visual chart read, an automated harness
  quantifies the directional edge of high-confidence tape states over the next 10 / 30 / 60 / 120
  seconds.

## Key Capabilities

1. **Provider abstraction** for the event stream, selected by a watch **mode** (`sim` |
   `live` | `historical`): a deterministic, seedable **SimulatedProvider** (default; no network,
   no keys); a **live provider** that streams real trades/quotes in real time; and a
   **historical-replay provider** that fetches a past window and replays it at a chosen speed.
   The real providers talk to the vendor only through a **vendor-agnostic adapter** (Alpaca
   first, free IEX feed; another vendor is one new adapter). The engine consumes provider events
   and never knows the source. Real timestamps are mapped to the engine's logical timeline
   (quote-before-trade preserved) so the engine stays unchanged and deterministic per stream.
2. **Core input events**: `TradeEvent` (ticker, timestamp, price, size, side ∈
   {buy, sell, unknown}); `QuoteEvent` (ticker, timestamp, bid, ask, bid_size, ask_size);
   and later `BookLevelEvent` (ticker, timestamp, side ∈ {bid, ask}, price, size, level).
3. **Trade aggressor classification (quote rule + tick-test fallback)**: trade price ≥ current
   ask ⇒ aggressive buy; price ≤ current bid ⇒ aggressive sell, using the quote in effect at the
   trade's timestamp. When no quote is in effect yet or the print is strictly between bid and ask,
   fall back to the **tick test** against the prior trade price (uptick ⇒ buy, downtick ⇒ sell,
   zero-tick ⇒ carry the last non-zero direction). Only a genuinely undecidable print — no quote
   **and** no prior trade — stays `unknown`. This rule is engine-level, so it sharpens **live** as
   well as historical; because far more prints get a side, real-data features and tape state read
   more truthfully than the quote-only rule did — an intended fidelity gain, not a regression.
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
8. **REST + WebSocket API**: `POST /watch/{ticker}` (optional body selects mode + historical
   params; empty body = sim), `DELETE /watch/{ticker}`, `GET /tape/{ticker}/state`,
   `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`,
   `WS /tape/{ticker}/stream`, plus real-data helpers `GET /symbols/search` (tradable-symbol
   lookup) and `GET /market/clock` (open/closed + next open/close).
9. **Simple single-ticker Next.js UI** showing the panels in Success Criteria, with a live
   event log and observations — not a complex trading platform. A **data-source selector**
   (Live / Historical / Simulated) drives a **symbol search** (real modes), a **date + time-window
   picker** and **replay-speed** control (historical), and a **market-status** indicator (live);
   the cockpit itself is identical across modes.
10. **Event-log / observation generation**: the engine emits discrete, human-readable
    messages on meaningful transitions, e.g. "Buyer aggression increasing", "Seller
    aggression increasing", "Large sell print absorbed", "Large buy print absorbed", "Ask
    refreshing at <price>", "Bid refreshing at <price>", "Tape state changed to
    buyer_control", "Tape state changed to unclear".
11. **Five simulated scenarios** that deterministically drive the engine toward each MVP
    state: buyer_control, seller_control, bid_absorption, ask_absorption, unclear_chop.
12. **Engine price + marker history buffer**: alongside the per-tick snapshot, the engine
    accumulates the watched price as **OHLC bars at 10 / 30 / 60 s** and a series of **meaningful
    tape-state-transition markers** (state + confidence + timestamp), using config-driven
    thresholds (no magic numbers). Computed once in the engine and served read-only.
13. **Tape-state prediction chart (UI)**: a **candlestick** chart of the watched price with a
    **bar-size selector** (10 / 30 / 60 s) and **markers at meaningful tape-state transitions**
    (green buyer_control, red seller_control, amber bid/ask_absorption; unclear unmarked), with
    pan/zoom. Shown for **simulated and historical** only, built on a lightweight client-side
    financial-charting library.
14. **Pause / resume a watch**: freeze and continue a watched session **without** tearing it down
    or clearing the UI. Replay (sim/historical) resumes exactly where it left off; live freezes the
    view and resumes at current real data (no fabricated backfill). The paused state is surfaced in
    the snapshot; Stop still fully tears the instance down.
15. **Historical window selection in local time**: the date/time picker defaults to the user's
    local timezone with an explicit **zone label** and **US-session quick-picks** ("Open 9:30 ET",
    "Close 16:00 ET", "Full RTH"), each annotated with the local equivalent; the fetched window
    equals the user's selected local window.
16. *(nice-to-have, later)* Optional extended states: `fake_breakout_risk`,
    `fake_breakdown_risk`, `liquidity_pull`, `liquidity_stack`, `exhaustion`.
17. *(nice-to-have, later)* Level 2 book ingestion (`BookLevelEvent`) and
    `liquidity_pull_score` / liquidity-stack features.
18. *(nice-to-have, later)* Persistence (PostgreSQL / Redis / Parquet / DuckDB) — only if a
    concrete need arises; Phase 1 is in-memory.
19. *(nice-to-have, later)* Replay/backtest harness measuring predictive value of
    high-confidence states over 10 / 30 / 60 / 120 s.

## Non-Goals

- No stock scanning or screening.
- No news, theme, or sentiment analysis.
- No chart-pattern scanning, technical-indicator studies, drawing tools, or multi-symbol /
  multi-pane charting. *(The one allowed chart is the focused price candlestick + tape-state-marker
  overlay for simulated/historical replay, used to evaluate whether a state predicts direction —
  not a general charting platform.)*
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
- **Frontend:** Next.js (App Router) + TypeScript; a simple single-ticker UI. The price chart uses
  a lightweight client-side financial-charting library — no server-side rendering and no new
  backend dependency.
- **Real-time transport:** WebSocket for live state/feature/event push; REST for
  request/response.
- **Data sources:** the deterministic, seedable **simulator** is the default/offline foundation
  (no keys); **real US-equity data** is selectable in two modes — **live** streaming and
  **historical replay** — from a real vendor (**Alpaca**, free IEX feed by default) behind a
  **vendor-agnostic adapter** so another vendor can be added without touching the engine/API.
- **Provider interface:** trades, quotes, and (later) L2 come from a replaceable provider
  selected by watch mode; the engine and API are provider-agnostic.
- **Credentials:** real-vendor API keys come only from environment/config (never committed). With
  no keys configured, the app runs simulator-only and the real modes report an explicit
  "provider unavailable" — they never fall back to fabricated data.
- **Local-time windows:** historical date/time windows are entered and displayed in the user's
  local timezone (with an explicit zone label) and resolved to the exact instant selected before
  the vendor fetch — no silent UTC reinterpretation of a naive value.
- **In-memory Phase 1:** rolling windows and state live in process memory; optional
  PostgreSQL/Redis/Parquet/DuckDB only if later needed.
- **No magic numbers:** every window length, threshold, large-print size, impact/absorption
  cutoff, and confidence boundary comes from config — no such literal in engine code.
- **Deterministic engine:** the same ordered event stream (and seed) yields identical
  features, state, and confidence — no wall-clock or randomness in classification.

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
- **Prediction chart:** one candlestick pane sized to the tape's short horizon (10 / 30 / 60 s
  bars), with tape-state markers in the same green/red/amber semantics — a focused decision aid,
  not a studies canvas.

## Product Shape

### Navigation / information architecture

- **Watch (`/`)** — the single-ticker tape cockpit and the app's home. A **data-source selector**
  (Live / Historical / Simulated) plus a ticker control (`POST /watch` on submit) and the live
  read for the watched ticker: bid / ask / spread / last, recent trades, the core feature
  readouts, the current **tape state** + **confidence**, the **observations** list, and the
  **event log**. Everything streams over `WS /tape/{ticker}/stream`. The source selector reveals
  mode-specific controls — a **symbol search** (real modes), a **date + time-window picker** and
  **replay-speed** control (historical), and a **market-status** indicator (live) — without
  changing the cockpit. It remains exactly one screen; a small indicator shows the source being
  watched (the sim scenario, "live AAPL", or "historical AAPL <window>"). Above the cockpit, a
  **price chart** — candlesticks with a bar-size selector and tape-state markers — is shown for
  **Simulated** and **Historical**. The watch controls include **Pause / Resume** (freeze and
  continue without clearing) beside Stop, with a **PAUSED** indicator when paused. The Historical
  **date/time-window picker** defaults to **local time** (with a zone label) and offers
  **US-session quick-picks** (Open 9:30 ET / Close 16:00 ET / Full RTH).

### API surface (Phase 1)

- `POST /watch/{ticker}` — begin watching; spins up an engine instance fed by the provider. An
  optional JSON body selects the mode and historical params (`{mode, start, end, speed}`, where
  `start`/`end` are timezone-aware instants for the selected local window); an empty body = a
  simulated watch (backward compatible).
- `DELETE /watch/{ticker}` — stop watching; tears the instance down (a live socket is closed).
- `GET /symbols/search?q=` — tradable-symbol suggestions for the search box (real modes).
- `GET /market/clock` — market open/closed + next open/close (live-mode status).
- `GET /tape/{ticker}/state` — current tape state + confidence (canonical).
- `GET /tape/{ticker}/features` — current per-window feature values (canonical).
- `GET /tape/{ticker}/events` — recent trade/quote events + emitted observations.
- `GET /tape/{ticker}/summary` — compact snapshot (quote, last, state, confidence, headline
  features).
- `WS /tape/{ticker}/stream` — live push of state, features, quote/last, and event-log
  messages.
- `GET /tape/{ticker}/history?bar=<10|30|60>` — engine-computed **OHLC bars + tape-state markers**
  for the price chart (simulated + historical); a pure projection of the engine history buffer.
- `POST /watch/{ticker}/pause` and `POST /watch/{ticker}/resume` — freeze/continue the feeder
  **without** tearing the instance down; the engine, its snapshot, and the history buffer survive.

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
- **Price history & tape-state markers** — OHLC bars (per selectable size) and meaningful-state
  markers are derived once in the engine's history buffer; `…/history` and the chart read the same
  series; the chart never recomputes side, state, or price.
- **Paused state** — owned once by the engine/feeder and surfaced in the snapshot; the UI reads it
  (no UI-side guess) to render the PAUSED indicator and toggle the control.
- **Stream status** (connecting | live | stale | paused | closed) — owned once by the engine/feeder;
  the UI's status indicator reads it. A live-feed gap flips it to **stale**; **pause** flips it to
  **paused** (without teardown) and resume restores the prior status; stop or stream exhaustion
  flips it to **closed** — never a fabricated "live".

## Must-have user journeys

Journeys **J-01 – J-09** are browser-verifiable against simulated data. A watched sim ticker is
bound to a known scenario (reserved sim tickers), so the expected tape state is deterministic;
simulated scenarios run on an accelerated clock, so each resolves within seconds (a browser
journey need not wait the full 60–300 s of real window time). These remain must-haves — the
real-data work MUST NOT regress them.

Journeys **J-10 – J-15** add real-vendor data and assume provider credentials are configured in
the environment for verification. **Historical replay** is reproducible for a fixed symbol +
past window (verifiable any time a key is present). **Live streaming** needs market hours, so its
real-socket behavior is confirmed by an operator/gated check (e.g. a credentialed integration
run), while its UI controls and honest-degradation states are browser-verifiable on their own.
With **no credentials**, the real modes MUST show an explicit "unavailable" — itself a verifiable
journey requiring no feed.

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

- **J-10: Choose a data source (Live / Historical / Simulated)**
  - Steps:
    1. Visit `/`
    2. Use the data-source selector to switch between Live, Historical, and Simulated
    3. Observe which controls appear for each mode; then watch `SIM-BUYER` in Simulated
  - Acceptance: the selector offers exactly the three modes; selecting **Live** reveals a symbol
    search + a market-status indicator; **Historical** reveals a symbol search + a date/time-window
    picker + a replay-speed control; **Simulated** reveals the ticker input. Choosing Simulated and
    watching `SIM-BUYER` still resolves to **buyer_control** exactly as J-01/J-02 (no regression).

- **J-11: Replay a real historical session**
  - Steps:
    1. Visit `/`, select **Historical**, enter a real symbol (e.g. `AAPL`), pick a past
       date/time window and a replay speed, and submit (Watch)
    2. Wait for the backend to fetch the window and the cockpit to populate
    3. Read the cockpit and let the replay run
  - Acceptance: the backend fetches that window's **real** trades + quotes from the vendor and
    replays them through the **same** engine; every cockpit panel populates with real values
    (bid/ask/spread/last, recent trades with price/size/side, the feature readouts, a tape state +
    confidence, observations, event log), updating over the WebSocket; REST and the UI agree
    (single source of truth). The read is reproducible for a fixed symbol + window.
    *(Verified with credentials configured.)*

- **J-12: Stream a real live ticker**
  - Steps:
    1. Visit `/`, select **Live**, enter/search a real symbol (e.g. `AAPL`), and submit (Watch)
    2. Observe the cockpit and the status indicator
  - Acceptance: during market hours with credentials configured, the cockpit streams **real-time**
    trades + quotes from the vendor and classifies the live tape state + confidence, updating over
    the WebSocket, with the status reading **live**. *(Real-socket behavior confirmed by an
    operator/gated credentialed run; the Live controls + status render without a feed.)*

- **J-13: Find a symbol by search**
  - Steps:
    1. Visit `/`, select **Live** or **Historical**
    2. Type a partial symbol or name into the search box
    3. Pick a suggestion
  - Acceptance: the search returns matching tradable symbols (symbol + name) from the vendor and
    selecting one fills the ticker for the watch. Free-text entry remains possible.
    *(Verified with credentials configured.)*

- **J-14: Real-data edge cases are handled honestly (no fabricated data)**
  - Steps:
    1. Attempt each: a Live/Historical watch with **no credentials** configured; an **unknown**
       symbol (real mode); a Historical window with **no data**; a **Live watch while the market is
       closed**
    2. Observe the result in each case
  - Acceptance: each surfaces an explicit, distinct state and **never a cockpit/tape**: no
    credentials → "real-data provider unavailable"; unknown symbol → "not a tradable symbol";
    empty window → "no data for that window"; market closed → "market is closed" (with the next
    open). No trades, quotes, prices, or tape state are synthesized to force a green result.
    *(The no-credentials / unknown-symbol / closed-market paths are verifiable without a live feed.)*

- **J-15: A live-feed gap shows `stale`, then recovers**
  - Steps:
    1. Watch a real symbol in **Live** mode
    2. Observe the status indicator across a lull in the feed and when data resumes
  - Acceptance: when no live event arrives within the configured window the status flips to
    **stale** (and the engine fabricates **no** trades during the gap); when events resume it
    returns to **live**. *(Confirmed by an operator/gated credentialed run.)*

Journeys **J-16 – J-20** cover the side-classification fix, the prediction chart, pause/resume, and
local-time window selection. **J-17 and J-19 run on simulated data and are browser-verifiable with
no credentials**; **J-16, J-18, and the correct-window-fetch half of J-20 assume vendor credentials
are configured**, while their UI/control surfaces remain browser-verifiable without a feed. These
additions MUST NOT regress J-01 – J-15.

- **J-16: Historical recent-trades show a resolved side (not `unknown`)**
  - Steps:
    1. Visit `/`, select **Historical**, enter a liquid symbol (e.g. `AAPL`) over a past
       regular-hours window, and Watch
    2. Let the window replay and read the **recent-trades** list
  - Acceptance: the large majority of trades show **buy** or **sell** (not `unknown`); where a quote
    is in effect, at/above-ask reads buy and at/below-bid reads sell, and mid-spread / pre-quote
    prints are resolved by the tick test; only a genuinely undecidable print may remain `unknown`;
    the `unknown` fraction is far lower than before. *(Verified with credentials configured.)*

- **J-17: Price chart with tape-state markers on simulated data**
  - Steps:
    1. Visit `/`, watch `SIM-BUYER`
    2. Observe the price chart above the cockpit; switch the **bar size** between 10 / 30 / 60 s
    3. Watch `SIM-SELLER`, then `SIM-BIDABS` / `SIM-ASKABS`
  - Acceptance: a **candlestick** chart of price renders and updates during replay; the bar-size
    selector re-renders the candles; **markers** appear at meaningful tape-state transitions in the
    correct colors (green for buyer_control, red for seller_control, amber for absorption; unclear
    unmarked). `SIM-BUYER` trends up with buyer markers, `SIM-SELLER` trends down with seller
    markers, and the absorption scenarios show amber markers with price held. *(No credentials;
    browser-verifiable.)*

- **J-18: Inspect tape-state prediction on a real historical chart**
  - Steps:
    1. Visit `/`, select **Historical**, watch a real symbol over a past window
    2. Read the candlestick chart; switch bar size 10 / 30 / 60 s; pan/zoom to a meaningful marker
       and inspect the price that follows it
  - Acceptance: candlesticks reflect the **real** replayed prices; the bars match the engine-served
    `…/history` data at each bar size; markers align with tape-state transitions; the user can
    visually assess whether a marked state preceded the subsequent move. *(Verified with credentials
    configured.)*

- **J-19: Pause and resume a watch without losing state**
  - Steps:
    1. Visit `/`, watch `SIM-BUYER` and let the cockpit populate
    2. Click **Pause**; observe the tape, chart, counters, and tape state
    3. Click **Resume**; then later click **Stop**
  - Acceptance: on **Pause**, the recent trades, chart, features, and tape state **freeze**, a
    **PAUSED** indicator shows, and the session is **not** cleared (no teardown); on **Resume**, the
    stream continues from where it left off; **Stop** still closes the stream and returns the cockpit
    to idle. *(No credentials; browser-verifiable.)*

- **J-20: Pick a historical window in local time with US-session quick-picks**
  - Steps:
    1. Visit `/`, select **Historical**
    2. Read the timezone label on the date/time picker and the **quick-picks** ("Open 9:30 ET",
       "Close 16:00 ET", "Full RTH")
    3. Choose a date and click a quick-pick (e.g. **Open**); then Watch
  - Acceptance: the picker defaults to the user's **local** time with an explicit zone label; each
    quick-pick is annotated with its local equivalent and fills a valid regular-hours start/end;
    with credentials, the window fetched from the vendor **matches the selected local window** (no
    UTC shift). *(The local-time labels + presets are browser-verifiable without a feed; the
    correct-window fetch is verified with credentials.)*

## Anti-goals

- **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and
  MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the
  tape. *(critical)*
- **Stay in scope.** No stock scanner/screener, no news/theme/sentiment analysis, no
  fundamental analysis, no chart-pattern or indicator charting, no portfolio/position
  management — these belong to separate projects and MUST NOT be built here. The one allowed chart
  is the focused price candlestick + tape-state-marker overlay (simulated/historical), which adds
  **no** indicators, studies, or drawing tools. *(critical)*
- **Price impact over raw aggression.** The classifier MUST distinguish absorption from
  control: a tape with high one-sided aggression but no corresponding price progress MUST
  resolve to the matching absorption state (bid_absorption / ask_absorption), never to
  seller_control / buyer_control. Keying on aggression ratios alone is a defect. *(critical)*
- **Honest uncertainty.** When evidence is weak or mixed, the spread is wide, or there is no
  clean price impact, the state MUST be `unclear` with low confidence. The system MUST NOT
  manufacture a directional call to look decisive. *(critical)*
- **No fabricated data.** The system MUST NOT synthesize trades, quotes, prices, or a tape state
  to force a green journey. Every real-data failure mode MUST surface an explicit, distinct state
  and never a cockpit: a provider gap/feed lull → `stale`; an unknown/untradable symbol → an
  explicit error; an empty historical window → explicit no-data; a live watch while the market is
  closed → explicit closed (with the next open); missing credentials → explicit "unavailable".
  Falling back to simulated or invented data to mask a real-data failure is a defect. *(critical)*
- **Single source of truth.** Tape state, confidence, and each feature MUST be computed
  exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and
  frontend MUST NOT recompute them. The same ticker MUST NOT show different values across
  views. *(critical)*
- **No magic numbers.** Every window length, threshold, large-print size, impact/absorption
  cutoff, and confidence boundary MUST come from config — no such literal in
  engine/classifier code.
- **Provider-agnostic engine.** The engine and API MUST depend only on the provider interface
  (TradeEvent / QuoteEvent / BookLevelEvent); swapping the simulator for a real feed — live or
  historical — MUST NOT require engine or API changes. A concrete vendor SDK MUST appear in only
  one adapter module behind a vendor-neutral seam, so a second vendor is one new adapter; vendor
  specifics MUST NOT leak into the engine, providers, or API.
- **No secrets in source.** Real-vendor API keys/tokens MUST come only from environment/config and
  MUST NOT be committed; with no keys the app runs simulator-only and real modes report an explicit
  "unavailable" rather than failing opaquely or fabricating data.
- **Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine
  MUST produce identical features, state, and confidence; classification MUST NOT depend on
  wall-clock time or randomness. Each simulated scenario MUST have an automated test asserting
  the expected state is reached with reasonable confidence.
- **No ML in v1.** The MVP classifier MUST be transparent rule/threshold logic over named
  features — no trained model in the first version.
- **No trade/profit claims.** The product MUST NOT claim profitability or present output as
  trading advice; tape state is descriptive, not prescriptive.
- **Honest side inference, not fabrication.** The aggressor side is a documented classification
  (quote rule, then a Lee-Ready **tick test** against the prior trade). This inference is legitimate
  and MUST be applied, but the engine MUST NOT force a guess when there is no quote **and** no prior
  trade — such a print stays `unknown`. Inferred side MUST NOT invent quotes or trades. *(critical)*
- **One focused chart, computed once.** OHLC bars and tape-state markers MUST be computed once in
  the engine history buffer and read identically by `…/history` and the chart; the UI MUST NOT
  recompute side, state, or price from raw data. An empty window MUST yield an **empty** chart, not
  invented candles. The chart is analysis-only — it MUST NOT add any order/execution affordance.
  *(critical)*
- **Honest pause.** Pause MUST freeze the displayed state without tearing the session down or
  fabricating data; while paused the UI MUST read as **paused**, never as live. On resume, **live**
  MUST rejoin current real data — the engine MUST NOT synthesize trades to "catch up" the gap.
  *(critical)*
- **Timezone-correct windows.** A historical window MUST be fetched for the exact instant the user
  selected in their local time — no silent UTC reinterpretation that shifts the window by the local
  offset; all market/session times shown to the user MUST carry an explicit zone label. *(critical)*
