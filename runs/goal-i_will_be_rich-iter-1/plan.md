# goal-i_will_be_rich-iter-1 Execution Plan

> Tape-cockpit walking skeleton, proven live on the **buyer-control** scenario (`SIM-BUYER`).
> Targets J-01, J-02, J-08. Greenfield build (no `apps/` tree yet). Blueprint is approved and in force.

## Alignment & Assumptions

- **Advances the goal:** stands up the first vertical slice (provider → engine → classifier → REST/WS → `/` cockpit) and locks the two keystone anti-goals (single source of truth, price-impact-over-aggression) at their cheapest point. Directly serves goal.md Success Criteria 1, 2, 4, 5.
- **Conforms to blueprint (no reapproval):** all six panels live under the existing `/` Watch home; no new IA home, no nav change. Data Contract additions: **none** — this is the first *implementation* of values already registered to their canonical owners/endpoints.
- **No spec drift / no scope creep:** spec stays inside goal.md scope. Out-of-scope items (other scenarios, absorption mechanics, Stop/teardown, L2, persistence, multi-ticker) are explicitly deferred — do **not** build them.
- **Assumptions (documented; `.claude/project-template.md` is the unfilled template):**
  - Layout `apps/backend/` (FastAPI, Python 3.12+, pytest, venv at `apps/backend/.venv/`) and `apps/frontend/` (Next.js App Router + TypeScript), per the template's test-command convention.
  - Backend `http://localhost:8000`, frontend `http://localhost:3000`; FastAPI CORS open to the frontend origin; frontend reads API base + WS URL from an env var (e.g. `NEXT_PUBLIC_API_BASE`).
  - Styling: Tailwind CSS (Next.js default) honoring goal.md Design Direction — calm dark surface, monospaced numerics, green=buy/positive, red=sell/negative, amber=absorption/unclear. No design-system config file exists, so follow goal.md Design Direction verbatim.
  - `SimulatedProvider` may use wall-clock **only** to pace live delivery so `SIM-BUYER` resolves within seconds in the browser; all computation keys on logical event timestamps + seed (determinism).

## What to Build

- **Provider interface** — typed `TradeEvent` (ticker, ts, price, size, side∈{buy,sell,unknown}) + `QuoteEvent` (ticker, ts, bid, ask, bid_size, ask_size); provider yields an ordered stream. Engine/API depend ONLY on this interface. Leave room for `BookLevelEvent` later (don't implement).
- **Deterministic seedable `SimulatedProvider`** — implements `SIM-BUYER` (aggressive buys lifting the offer, last price progressing higher, spread narrow/stable). Same seed ⇒ identical stream. Register `SIM-SELLER`/`SIM-BIDABS`/`SIM-ASKABS`/`SIM-CHOP` names only (need not resolve correctly yet).
- **Config module (no magic numbers)** — single source for window lengths {10,30,60,180,300}s, large-print size, buyer_control thresholds (min `aggressive_buy_ratio`, min positive `buy_price_impact`, max stable spread, min `trade_speed`), confidence boundaries, warm-up minimum-events floor.
- **`MarketState`** — latest quote + last trade ⇒ bid / ask / spread / last, computed once (`spread = ask − bid`).
- **Aggressor classifier** — price ≥ ask ⇒ buy; ≤ bid ⇒ sell; strictly between ⇒ unknown; uses the quote in effect at the trade's timestamp.
- **`FeatureEngine`** — concurrent rolling windows keyed on event timestamps. Computes this iteration: `trade_speed`, `volume_speed`, `aggressive_buy_ratio`, `aggressive_sell_ratio`, `net_aggressive_volume`, `buy_price_impact`, `sell_price_impact`, `average_spread`, `large_print_count`. (Remaining blueprint features added additively in later iterations.)
- **`TapeStateClassifier`** — transparent rule/threshold logic, **keyed on price impact**. `SIM-BUYER` ⇒ **buyer_control** (high `aggressive_buy_ratio` AND positive `buy_price_impact` AND stable spread AND elevated `trade_speed`); cold-start / insufficient / mixed ⇒ **unclear** (low confidence). State + confidence + observations. No ML.
- **Single engine snapshot** — one immutable per-tick object: quote/last, features, state+confidence, recent trades (with side), observations, event-log messages, scenario label, stream status. The ONE producer every view reads.
- **Observation / transition emitter** — emits `"Tape state changed to buyer_control"` on the transition + ≥1 evidence observation (e.g. `"Buyer aggression increasing"`).
- **`WatchManager` + FastAPI app** — `POST /watch/{ticker}` spins up an in-memory per-ticker engine. Canonical reads `GET /tape/{ticker}/state` and `/features`; `/events`; `/summary` and `WS /tape/{ticker}/stream` **re-expose the snapshot read-only — never recompute**. Unknown/non-sim ticker on POST ⇒ explicit error/no-data; read of a not-watched ticker ⇒ explicit not-watched (404). (No `DELETE /watch` this iteration.)
- **`/` tape-cockpit (Next.js)** — app shell (name **Tapeology**, ticker input + **Watch**, watched-ticker label, scenario indicator, stream-status dot) + six panels (Quote, Recent-trades, Features, Tape-state, Observations, Event-log) + idle/empty state. Initial paint via REST, live updates via WS. UI renders engine values **verbatim** — never recomputes spread/ratios/impacts/confidence. (No Stop control this iteration.)

## Agents Required

- **backend-data: yes** — provider interface, SimulatedProvider, config, MarketState, aggressor, FeatureEngine, classifier, snapshot, emitter, WatchManager, FastAPI REST+WS, all backend tests.
- **frontend-ux: yes** — `/` cockpit, app shell, six panels, idle state, REST client + WS hook, color semantics.
- developer: yes — single developer agent implements both backend and frontend with TDD.

Frontend Present: yes

## Files to Create/Modify

Concrete paths are at the developer's discretion (blueprint grants this), provided each canonical value keeps exactly one computing owner + one canonical endpoint. Suggested layout:

**Backend (`apps/backend/`)**
- `pyproject.toml` / `requirements.txt` — FastAPI, uvicorn, pytest, websockets/httpx.
- `app/config.py` — all windows/thresholds/large-print/confidence boundaries (no magic numbers).
- `app/providers/base.py` — `TradeEvent`, `QuoteEvent`, provider interface (BookLevelEvent reserved, not built).
- `app/providers/simulated.py` — `SimulatedProvider` + sim-ticker registry (`SIM-BUYER` live).
- `app/engine/market_state.py` — `MarketState` (bid/ask/spread/last).
- `app/engine/aggressor.py` — aggressor classifier.
- `app/engine/features.py` — `FeatureEngine` (rolling windows).
- `app/engine/classifier.py` — `TapeStateClassifier`.
- `app/engine/snapshot.py` — immutable engine snapshot.
- `app/engine/observations.py` — observation / transition emitter.
- `app/engine/tape_engine.py` — per-ticker engine wiring provider → state → snapshot.
- `app/watch_manager.py` — `WatchManager`.
- `app/main.py` — FastAPI: `POST /watch/{ticker}`, `GET /tape/{ticker}/{state,features,events,summary}`, `WS /tape/{ticker}/stream`; CORS.
- `tests/test_aggressor.py`, `tests/test_features.py`, `tests/test_classifier.py`, `tests/test_api.py`.

**Frontend (`apps/frontend/`)**
- `package.json`, `tsconfig.json`, `next.config.*`, Tailwind config, global styles.
- `app/layout.tsx` — app shell / top bar (ticker input + Watch, watched label, scenario indicator, stream dot).
- `app/page.tsx` — `/` cockpit composing the six panels + idle state.
- `components/{QuotePanel,RecentTradesPanel,FeaturesPanel,TapeStatePanel,ObservationsPanel,EventLogPanel,IdleState}.tsx`.
- `lib/api.ts` (REST client), `lib/useTapeStream.ts` (WS hook), `lib/types.ts` (snapshot types mirrored from backend).

**Project config**
- `.claude/project-template.md` — fill in stack/test/service-start sections (optional but recommended so later iterations don't re-derive). If filled, keep surgical.

## UI Evolution (Frontend Present: yes)

- **New user-facing capability:** visit `/`, enter `SIM-BUYER`, click **Watch**, and see a live, honest single-ticker tape read that updates over WebSocket and settles on **buyer_control** with a confidence score.
- **New information displayed:** live bid/ask/spread/last; recent trades with side; the implemented core features (per-window structure present); tape state + confidence; observations; event log; scenario indicator; stream status.
- **New user actions:** ticker input + **Watch** submit (issues `POST /watch/{ticker}`).
- **UI surface changes:** first build of the `/` cockpit, its persistent app shell, and six panels. No other pages.
- **Navigation changes:** none — `/` is the single existing home per the approved blueprint (no reapproval).

## Visual Requirements (Frontend Present: yes)

- **Component patterns:** panel/card per data group (Quote, Recent-trades, Features, Tape-state, Observations, Event-log); table/list rows for recent trades and event log; a labeled metric readout for each feature. Monospaced numerics for all prices/sizes/ratios. (No design-system component config exists — build clean, consistent panels.)
- **Layout:** dense single-screen instrument-panel grid — persistent top bar (app shell) + a panel grid below; full-width, responsive collapse on narrow widths.
- **Key visual effects:** restrained. Calm dark surface; color encodes side/impact consistently — green = buy-side / positive impact, red = sell-side / negative impact, amber = absorption / unclear; tape-state and trade rows color-coded accordingly. No clutter, no profitability claim, nothing presented as trading advice.
- **States to handle:** **idle/empty** (before any ticker watched — empty cockpit, no fabricated/stale numbers); **connecting/warm-up** (stream connecting, panels not yet populated); **live**; **stream stale/closed** (status dot reflects it); **error/no-data** (unknown ticker or not-watched read surfaces an explicit message, never fabricated values).

## Anti-goal guardrails (must hold — verified by coherence-auditor + QA)

- **Single source of truth:** exactly one snapshot per tick; `/state`, `/features`, `/events`, `/summary`, `WS /stream`, and the UI all read it; UI never re-derives spread/ratios/impacts/confidence.
- **Price impact, not aggression:** buyer_control rule requires positive `buy_price_impact`, covered by a negative guard test (high buy ratio + zero/negative impact ⇒ NOT buyer_control).
- **Honest uncertainty:** cold-start / insufficient / mixed ⇒ `unclear` at low confidence; never a manufactured directional call.
- **No fabricated data:** unknown/non-sim POST and not-watched reads return explicit errors — no synthesized trades/quotes/state.
- **Determinism:** same stream + seed ⇒ identical features/state/confidence; no wall-clock or randomness in classification.
- **No magic numbers:** every window/threshold/cutoff/boundary comes from config; none inline in engine/classifier code.
- **Provider-agnostic:** engine + API depend only on the provider interface.

## Key Test Scenarios

**Browser (browser-qa-agent, on `SIM-BUYER` — required):**
- **J-01:** watch `SIM-BUYER`; within warm-up every panel renders live values; bid/ask/spread/last numeric with `spread = ask − bid`; recent trades show price/size/side; `trade_speed`, `aggressive_buy_ratio`, `aggressive_sell_ratio`, `net_aggressive_volume`, `buy_price_impact`, `sell_price_impact` each show a number; tape-state panel shows one of five states + confidence; observations and event log each show ≥1 message; values update over WS without page reload.
- **J-02:** settles on **buyer_control** with confidence ≥ configured threshold; `aggressive_buy_ratio` high and `buy_price_impact` positive; event log contains `"Tape state changed to buyer_control"`.
- **J-08:** UI tape state + confidence exactly match `GET /tape/SIM-BUYER/state`; UI feature readouts match `GET /tape/SIM-BUYER/features` (one engine value per metric across REST, WS, UI).

**Unit / integration (must pass):**
- Aggressor: price≥ask⇒buy, ≤bid⇒sell, strictly-between⇒unknown; uses quote in effect at trade ts; edges price==ask (buy), price==bid (sell), no prior quote (unknown).
- FeatureEngine: feed a known ordered stream, assert exact feature values for ≥1 window; **determinism** — same stream+seed twice ⇒ identical snapshot; windowing on event timestamps, not wall-clock.
- Classifier: `SIM-BUYER` ⇒ buyer_control at confidence ≥ threshold; cold-start ⇒ unclear/low confidence.
- **Price-impact guard (critical):** synthetic stream with high `aggressive_buy_ratio` but zero/negative `buy_price_impact` MUST NOT classify buyer_control.
- **Single source of truth:** `/state`, `/summary`, WS payload serialize the same state/confidence from one snapshot; `/features` and `/summary` headline subset agree; `spread` produced once in `MarketState`.
- **Error cases:** unknown/non-sim POST ⇒ explicit error/no-data; read of a not-watched ticker ⇒ explicit not-watched (e.g. 404); cold start ⇒ `unclear` low confidence — all with no fabrication.

## Definition of Done (from spec)

- J-01, J-02, J-08 pass via browser-qa-agent on `SIM-BUYER`; no regressions (no journey was green).
- No anti-goal violation (guardrails above).
- Unit/integration tests pass, including the `SIM-BUYER` scenario test asserting buyer_control at confidence ≥ threshold.
- Dev handoff written to `docs/handoffs/goal-i_will_be_rich-iter-1-dev.md`.
