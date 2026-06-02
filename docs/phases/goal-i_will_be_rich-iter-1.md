# Goal Iteration 1 — Tape-cockpit walking skeleton, proven on the buyer-control scenario

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_rich
- **Iteration:** 1
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-08
- **Required-still-passing journeys:** none (no journey is green yet — greenfield baseline; nothing to regress)
- **Anti-goal reminders** (verbatim from `docs/goal.md`):
  - **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the tape. *(critical)*
  - **Stay in scope.** No stock scanner/screener, no news/theme/sentiment analysis, no fundamental analysis, no chart-pattern or indicator charting, no portfolio/position management — these belong to separate projects and MUST NOT be built here. *(critical)*
  - **Price impact over raw aggression.** The classifier MUST distinguish absorption from control: a tape with high one-sided aggression but no corresponding price progress MUST resolve to the matching absorption state (bid_absorption / ask_absorption), never to seller_control / buyer_control. Keying on aggression ratios alone is a defect. *(critical)*
  - **Honest uncertainty.** When evidence is weak or mixed, the spread is wide, or there is no clean price impact, the state MUST be `unclear` with low confidence. The system MUST NOT manufacture a directional call to look decisive. *(critical)*
  - **No fabricated data.** On a provider gap/failure the system MUST surface an explicit stale/no-data state and MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. *(critical)*
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*
  - **No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code.
  - **Provider-agnostic engine.** The engine and API MUST depend only on the provider interface (TradeEvent / QuoteEvent / BookLevelEvent); swapping the simulator for a real feed MUST NOT require engine or API changes.
  - **Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine MUST produce identical features, state, and confidence; classification MUST NOT depend on wall-clock time or randomness. Each simulated scenario MUST have an automated test asserting the expected state is reached with reasonable confidence.
  - **No ML in v1.** The MVP classifier MUST be transparent rule/threshold logic over named features — no trained model in the first version.
  - **No trade/profit claims.** The product MUST NOT claim profitability or present output as trading advice; tape state is descriptive, not prescriptive.
  - **No secrets in source.** No API keys, tokens, or credentials committed; any future provider keys come from environment/config only.

## GOAL

Stand up the end-to-end tape-cockpit walking skeleton — deterministic `SimulatedProvider` → engine (market state, aggressor classifier, feature engine) → rule-based `TapeStateClassifier` → REST + WebSocket API → the `/` Next.js cockpit — and prove it live on the **buyer-control** scenario (`SIM-BUYER`), with REST and the live UI showing one identical engine value per metric.

## BACKGROUND

This is the first feature build after the verify-only baseline (iter 0, CONTINUE → full). The codebase is greenfield: no `apps/` tree, no product source, all nine journeys seeded `failing`. The iter-0 evaluator recommended a foundational build **sequenced so J-01 is verifiable first**, at full depth, because this iteration establishes the single-source-of-truth data contract, the price-impact classifier, and engine determinism — all critical anti-goals.

J-01's acceptance alone requires nearly the entire vertical slice (quote, trades, features, state+confidence, observations, event log, live WS), so the slice must be built now. To keep the iteration **scorable and tight** we prove that slice on **one** scenario (`SIM-BUYER`) and target exactly three mutually-reinforcing journeys: **J-01** (cockpit works end to end), **J-02** (classifier produces a correct, price-impact-keyed buyer_control read), and **J-08** (REST and UI agree — single source of truth). The remaining scenarios are deferred to dedicated iterations: seller_control (J-03), the price-impact-critical absorption pair (J-04/J-05), unclear-chop (J-06), transitions taxonomy (J-07), and stop/idle/re-watch (J-09). The `lessons.md` ledger is empty (no prior pitfalls to apply).

The two keystone anti-goals are locked in **now**, when it is cheapest: (a) single-source-of-truth — there is exactly one engine snapshot per tick and every view reads it; (b) price-impact-over-aggression — the very first classifier rule requires *positive buy_price_impact*, not just a high buy ratio, with a negative guard test, so the engine cannot later take an aggression-only shortcut that would misfire on `SIM-BIDABS`/`SIM-ASKABS`.

## IN SCOPE

### Backend
- [ ] **Provider interface** — typed `TradeEvent` (ticker, timestamp, price, size, side ∈ {buy, sell, unknown}) and `QuoteEvent` (ticker, timestamp, bid, ask, bid_size, ask_size); a provider yields an ordered event stream. The engine and API depend ONLY on this interface (provider-agnostic anti-goal). `BookLevelEvent` is not implemented this iteration but the interface must not preclude adding it later.
- [ ] **Deterministic, seedable `SimulatedProvider`** implementing the **`SIM-BUYER`** scenario: an ordered trade/quote stream that drives buyer_control — repeated aggressive buys lifting the offer, last price progressing higher, spread staying narrow/stable. Same seed ⇒ identical stream. Reserve the other sim-ticker names (`SIM-SELLER`, `SIM-BIDABS`, `SIM-ASKABS`, `SIM-CHOP`) in the registry, but they need NOT resolve to their target states this iteration.
- [ ] **Config module (no magic numbers)** — single source for: window lengths {10, 30, 60, 180, 300}s; large-print size; buyer_control thresholds (min aggressive_buy_ratio, min positive buy_price_impact, max spread for "stable", min trade_speed); confidence boundaries; warm-up minimum-events floor. No such literal may appear inline in engine/classifier code.
- [ ] **`MarketState` tracker** — maintains the latest quote + last trade and derives **bid / ask / spread / last** once, where `spread = ask − bid`.
- [ ] **Aggressor classifier** — trade price ≥ current ask ⇒ aggressive buy; ≤ current bid ⇒ aggressive sell; otherwise unknown — using the quote in effect at the trade's timestamp.
- [ ] **`FeatureEngine`** — rolling windows keyed on **event timestamps** (not wall-clock), maintained concurrently for all configured windows. Computes (this iteration) the features J-01 displays and the buyer_control rule needs: `trade_speed`, `volume_speed`, `aggressive_buy_ratio`, `aggressive_sell_ratio`, `net_aggressive_volume`, `buy_price_impact`, `sell_price_impact`, `average_spread`, `large_print_count`. It is the canonical feature producer; the remaining blueprint features (`spread_change`, `absorption_score`, `bid_refresh_score`, `ask_refresh_score`, `liquidity_imbalance`) are added **additively** in their owning iterations (J-04/J-05 etc.).
- [ ] **`TapeStateClassifier`** — transparent rule/threshold logic over named features, keyed on **price impact**. This iteration resolves: `SIM-BUYER` → **buyer_control** (requires high `aggressive_buy_ratio` AND positive `buy_price_impact` AND stable spread AND elevated `trade_speed`); cold-start / insufficient-evidence / mixed → **unclear** (low confidence). Produces state + confidence + human-readable observations. Structured to extend to the other four states later. All thresholds from config; no ML.
- [ ] **Single engine snapshot** — one immutable per-tick snapshot object carrying quote/last, the computed features, tape state + confidence, recent trades (with side), observations, event-log messages, scenario label, and stream status. This is the ONE producer all views read.
- [ ] **Observation / transition emitter** — emits `"Tape state changed to buyer_control"` on the transition into buyer_control plus ≥1 evidence observation (e.g. `"Buyer aggression increasing"`).
- [ ] **`WatchManager` + FastAPI app** — `POST /watch/{ticker}` spins up a per-ticker engine instance fed by the provider (in-memory). Reads: `GET /tape/{ticker}/state`, `/features`, `/events`, `/summary`. Live: `WS /tape/{ticker}/stream`. `/state` and `/features` are the canonical REST reads; `/summary` and `WS /stream` **re-expose the snapshot read-only — they MUST NOT recompute**. Unknown/non-sim ticker on `POST` ⇒ explicit error/no-data (never a fabricated stream). Reads for a not-watched ticker ⇒ explicit not-watched (e.g. 404), never fabricated. (`DELETE /watch` is deferred to the J-09 iteration.)

### Frontend
- [ ] **`/` tape-cockpit (Next.js App Router + TypeScript)** — app shell per blueprint: app name **Tapeology**, ticker input + **Watch** button (`POST /watch/{ticker}` on submit), watched-ticker label, scenario indicator, stream-status dot. (Stop control deferred to J-09.)
- [ ] **Panels:** Quote (bid / ask / spread / last), Recent-trades (price / size / **side**, color-coded), Features (the implemented named features for a primary window; per-window structure present), Tape-state (state + confidence, color-coded), Observations, Event-log.
- [ ] **Reads from the engine snapshot only** — initial paint via REST, live updates via `WS /stream`. The UI MUST NOT recompute `spread`, the aggressive ratios, price impacts, or confidence — it renders the engine's values verbatim (single source of truth).
- [ ] **Idle/empty state** before any ticker is watched: an empty cockpit with no fabricated or stale numbers.
- [ ] **Color semantics:** green = buy-side / positive impact; red = sell-side / negative impact; amber = absorption / unclear. No profitability claim and nothing presented as trading advice anywhere in the UI.

### New user-facing capability
A user can visit `/`, enter `SIM-BUYER`, click Watch, and see a live, honest single-ticker tape read that updates over WebSocket and settles on **buyer_control** with a confidence score.

### New information displayed
Live bid/ask/spread/last; recent trades with side; the named core features; the current tape state + confidence; observations; the event log; the replaying-scenario indicator and stream status.

### New user actions
Ticker input + **Watch** submit (issues `POST /watch/{ticker}`).

### UI surface changes
First build of the `/` cockpit and its six panels plus the persistent app shell. No other pages.

### Product surface delta
From nothing (greenfield) to a working single-ticker tape cockpit that reads and classifies the buyer-control scenario live.

### Blueprint conformance
All panels live under the **existing** `/` Watch home (the cockpit), the single Information-Architecture home in `blueprint.md`. No new IA home, no new top-level nav section, no nav-skeleton change ⇒ **no reapproval requested**.

### Data-contract additions
**None.** Every displayed value (tape state + confidence; the core features; bid/ask/spread/last; recent trades + side; observations + event-log; scenario label + stream status) is already registered in the blueprint Data Contract with its single canonical computing module and serving endpoint. This iteration is the first *implementation* of those already-registered values — each is read from its registered canonical source; no second computation or endpoint is introduced.

## OUT OF SCOPE

- `SIM-SELLER` / **seller_control** (J-03) — next iteration (symmetric to buyer_control).
- `SIM-BIDABS` / `SIM-ASKABS` / **absorption** detection and the `absorption_score` / `bid_refresh_score` / `ask_refresh_score` features (J-04/J-05) — the price-impact-critical pair, in a dedicated iteration.
- `SIM-CHOP` / **unclear-chop** scenario verification (J-06) — the `unclear` state exists for warm-up/mixed but the chop scenario is not driven or verified here.
- Full transition/observation taxonomy across scenarios (J-07) — only the buyer_control transition message is in scope.
- `DELETE /watch`, the Stop control, after-stop idle, and re-watch (J-09).
- Level 2 / `BookLevelEvent`, `liquidity_pull_score`, extended states (`fake_breakout_risk`, etc.) — later/nice-to-have.
- Persistence — Phase 1 is in-memory only.
- Any multi-ticker dashboard, watchlist grid, scanner, news, charting, fundamentals, portfolio, or execution/broker integration (anti-goals).

## DEFINITION OF DONE

- [ ] Target journeys **J-01, J-02, J-08** pass via browser-qa-agent on `SIM-BUYER`.
- [ ] Required-still-passing journeys: none (no journey was green) — no regression introduced.
- [ ] No anti-goal violation introduced — in particular: single-source-of-truth (one snapshot, no UI/API recompute), price-impact-keying (buyer_control requires positive `buy_price_impact`), honest-uncertainty (cold-start → unclear/low confidence), no-fabrication (unknown/not-watched ticker errors explicitly), determinism (same stream+seed → identical result), no-magic-numbers (all thresholds in config).
- [ ] Unit/integration tests pass; no regressions. Includes one automated `SIM-BUYER` scenario test asserting **buyer_control** at confidence ≥ the configured threshold (determinism anti-goal).
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_rich-iter-1-dev.md`.

## TESTING REQUIREMENTS

- **Browser (browser-qa-agent):**
  - **J-01** — visit `/`, watch `SIM-BUYER`; within warm-up every panel renders live values; bid/ask/spread/last are numeric and `spread = ask − bid`; recent-trades show price/size/side; `trade_speed`, `aggressive_buy_ratio`, `aggressive_sell_ratio`, `net_aggressive_volume`, `buy_price_impact`, `sell_price_impact` each show a number; the tape-state panel shows one of the five states with a confidence score; observations and event log each show ≥1 message; values update over WebSocket without a page reload.
  - **J-02** — `SIM-BUYER` settles on **buyer_control** with confidence ≥ the configured "reasonable" threshold; `aggressive_buy_ratio` reads high and `buy_price_impact` reads positive; the event log contains `"Tape state changed to buyer_control"`.
  - **J-08** — the tape state + confidence shown in the UI exactly match `GET /tape/SIM-BUYER/state`, and the UI's feature readouts match `GET /tape/SIM-BUYER/features` (one engine value per metric across REST, WS, and UI).
- **Unit/integration:**
  - Aggressor classifier: price ≥ ask ⇒ buy, ≤ bid ⇒ sell, strictly-between ⇒ unknown; uses the quote in effect at the trade timestamp; edge cases price == ask (buy), price == bid (sell), no prior quote (unknown).
  - `FeatureEngine`: feed a known ordered stream and assert exact feature values for at least one window; **determinism** — same stream (and seed) twice ⇒ identical snapshot; windowing keyed on event timestamps, not wall-clock.
  - `TapeStateClassifier`: `SIM-BUYER` stream ⇒ buyer_control at confidence ≥ threshold; cold-start / insufficient evidence ⇒ unclear at low confidence.
  - **Price-impact guard (critical):** a synthetic stream with high `aggressive_buy_ratio` but zero/negative `buy_price_impact` MUST NOT classify buyer_control — proving the rule keys on impact, not aggression.
  - **Single source of truth:** `/state`, `/summary`, and the WS payload serialize the same state/confidence from one snapshot (re-expose, not recompute); `/features` and `/summary`'s headline subset agree; `spread` is produced once in `MarketState`.
- **Error cases:**
  - `POST /watch/{ticker}` with an unknown/non-sim ticker ⇒ explicit error or no-data response; no fabricated trades/quotes/state.
  - `GET /tape/{ticker}/…` for a ticker that is not being watched ⇒ explicit not-watched (e.g. 404); no fabricated snapshot.
  - Cold start (before warm-up minimum events) ⇒ `unclear` with low confidence, never a fabricated directional call.

## NOTES

- **Determinism design (call out to developer):** the `SimulatedProvider` may use wall-clock only to *pace delivery* in live mode so the scenario resolves within seconds in the browser; every event still carries a logical timestamp, and the `FeatureEngine`/classifier compute purely from those logical timestamps (and the seed). The unit/scenario tests feed the ordered stream synchronously and assert an exact, wall-clock-independent result.
- **Single source of truth (call out):** there is exactly ONE engine snapshot per tick. `/state`, `/features`, `/events`, `/summary`, `WS /stream`, and the UI all read from it; the frontend renders `spread`, ratios, impacts, and confidence verbatim and never re-derives them. Locking this in now (J-08) is far cheaper than retrofitting it later.
- **Price impact, not aggression (call out):** even though absorption isn't built this iteration, the buyer_control rule requires positive `buy_price_impact` and is covered by a negative guard test — this prevents an aggression-only shortcut that would later misclassify `SIM-BIDABS`/`SIM-ASKABS` as control.
- **Stack (from `docs/goal.md` Constraints):** backend Python 3.12+ / FastAPI (uvicorn ASGI); frontend Next.js App Router + TypeScript; WebSocket for live push, REST for request/response; Phase-1 data simulated, deterministic, seedable; in-memory only.
- **Scope discipline:** this is a deliberately tight walking skeleton on one scenario. Do not build the other scenarios, absorption mechanics, stop/teardown, or any out-of-scope surface — they are sequenced into later iterations.
- **Reference:** iter-0 `eval.md` next-step recommendation (foundational sequence; J-01 first; full depth). `blueprint.md` is human-approved (`state/blueprint.approved` present) and in force from this iteration.
