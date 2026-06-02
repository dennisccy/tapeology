# goal-i_will_be_rich-iter-1 Dev Handoff

**Phase:** goal-i_will_be_rich-iter-1
**Date:** 2026-06-02
**Agent:** developer
**Mode:** INITIAL BUILD
**Status:** complete

## What Was Built

The full tape-cockpit walking skeleton, proven live on **SIM-BUYER** (targets **J-01, J-02, J-08**).

**Backend (`apps/backend/`, FastAPI + Python 3.12, in-memory):**
- **Provider interface** (`app/providers/base.py`) — frozen `TradeEvent` / `QuoteEvent` dataclasses, a `Side` enum, and a `Provider` Protocol yielding an ordered event stream. `BookLevelEvent` is reserved (commented) for a later iteration. The engine/API depend only on this interface.
- **Deterministic, seedable `SimulatedProvider`** (`app/providers/simulated.py`) — drives the `SIM-BUYER` scenario (aggressive buys lifting the offer, last price progressing higher, spread held at 0.02). Same seed ⇒ identical stream. Reserved tickers `SIM-SELLER / SIM-BIDABS / SIM-ASKABS / SIM-CHOP` are registered (known) but not driven to their states yet. `build_provider()` returns `None` for unknown tickers (no fabrication).
- **Config module** (`app/config.py`) — the single source for all window lengths {10,30,60,180,300}s, the large-print size, the buyer_control thresholds, the warm-up floor, and all confidence boundaries. No such literal appears inline in engine/classifier code.
- **`MarketState`** (`app/engine/market_state.py`) — derives bid / ask / spread / last once; `spread = ask − bid` computed in exactly one place.
- **Aggressor classifier** (`app/engine/aggressor.py`) — price ≥ ask ⇒ buy, ≤ bid ⇒ sell, strictly between ⇒ unknown, no quote ⇒ unknown, using the quote in effect at the trade timestamp.
- **`FeatureEngine`** (`app/engine/features.py`) — all five windows maintained concurrently, keyed on logical event timestamps. Computes `trade_speed, volume_speed, aggressive_buy_ratio, aggressive_sell_ratio, net_aggressive_volume, buy_price_impact, sell_price_impact, average_spread, large_print_count`. Price impact is the cumulative price change **on matching-side aggressor prints** — so high aggression with a flat price yields ~0 impact.
- **`TapeStateClassifier`** (`app/engine/classifier.py`) — transparent rule logic (no ML). `buyer_control` requires high `aggressive_buy_ratio` **AND positive `buy_price_impact`** AND stable spread AND elevated `trade_speed`, and only emits at confidence ≥ the reasonable bar; otherwise `unclear` (cold-start ⇒ very low confidence). Confidence is a config-weighted mean of four margin scores.
- **Single immutable snapshot** (`app/engine/snapshot.py`) + **observation/transition emitter** (`app/engine/observations.py`) + **engine wiring** (`app/engine/tape_engine.py`) — one `EngineSnapshot` per tick carrying quote/last, all features, state+confidence, observations, event log, recent trades (with side), scenario, and stream status. The emitter appends `"Tape state changed to buyer_control"` once, on the transition.
- **`WatchManager`** (`app/watch_manager.py`) — one engine per watched ticker, fed by an async background task that paces the provider stream on wall-clock (delivery pacing only). Unknown ticker ⇒ `UnknownTickerError`.
- **Pure serializers** (`app/serializers.py`) + **FastAPI app** (`app/main.py`, entrypoint shim `main.py`) — `POST /watch/{ticker}`, `GET /tape/{ticker}/{state,features,events,summary}`, `WS /tape/{ticker}/stream`, `GET /health`. Every read endpoint is a pure projection of the one snapshot; `/summary` and the WS stream re-expose it read-only (no recompute). Unknown ticker ⇒ 400; not-watched read ⇒ 404; cold-start ⇒ unclear/low confidence — no fabricated data.

**Frontend (`apps/frontend/`, Next.js 15 App Router + TypeScript + Tailwind):**
- The `/` tape cockpit: persistent app shell (app name, ticker input + **Watch**, watched-ticker label, scenario indicator, stream-status dot) and six panels (Quote, Recent-trades, Features with a per-window selector, Tape-state + confidence, Observations, Event-log), plus an idle/empty state and a "connecting" state. Initial paint via REST, live updates via the WebSocket. The UI renders engine values verbatim — it never recomputes spread, ratios, impacts, or confidence.

## Files Changed

All files are new (greenfield `apps/` tree). Key files:

**Backend** — `apps/backend/`: `requirements.txt`, `pyproject.toml`, `main.py` (ASGI shim);
`app/config.py`, `app/serializers.py`, `app/main.py`, `app/watch_manager.py`;
`app/providers/{base,simulated}.py`; `app/engine/{market_state,aggressor,features,classifier,snapshot,observations,tape_engine}.py`;
tests `tests/{conftest,test_aggressor,test_features,test_classifier,test_scenario,test_api}.py`.

**Frontend** — `apps/frontend/`: `package.json`, `tsconfig.json`, `next.config.mjs`, `postcss.config.mjs`, `tailwind.config.ts`, `.env.example`;
`app/{layout,page,globals.css}`; `components/{Panel,QuotePanel,RecentTradesPanel,FeaturesPanel,TapeStatePanel,ObservationsPanel,EventLogPanel,IdleState,TopBar,Cockpit}.tsx`;
`lib/{types,config,format,api,useTapeStream}.ts`.

**Project config** — `.claude/project-template.md` filled in with the real stack, test commands, service-start commands, and design tokens (this repo's vendored copy).

## Tests Run

**Backend:** `cd apps/backend && .venv/bin/python -m pytest tests/ -v` → **24 passed**.
Covers: aggressor boundaries (incl. the three edge cases), exact feature values + determinism + event-timestamp windowing, classifier buyer_control / cold-start, the **critical price-impact guard** (high buy ratio + zero/negative impact ⇒ NOT buyer_control), single-source-of-truth across serializers, a live SIM-BUYER watch over HTTP, and the error cases (unknown POST ⇒ 400, not-watched read ⇒ 404).

**Frontend:** `cd apps/frontend && npm run build` → compiled successfully (types check, static generation OK; Next 15.5.19).

**Live integration (verified, not mocked):** started both services via the framework `scripts/start-backend.sh` / `scripts/start-frontend.sh` (offset ports 8650 / 3650), watched `SIM-BUYER` in a real browser → cockpit resolved to **Buyer Control @ confidence ~0.88**, all panels populated with live values updating over the WebSocket (no reload), color semantics correct, event log a single clean `"Tape state changed to buyer_control"`, no browser console errors. Error cases returned 400 / 404 over curl. `/summary` headline features equal `/features` primary-window values exactly (single source). Both services were stopped afterward; ports 8650/3650 are free.

## Known Issues

- **Reserved scenarios are inert.** `SIM-SELLER / SIM-BIDABS / SIM-ASKABS / SIM-CHOP` are registered (watchable, return a real not-fabricated cold-start `unclear`) but emit no events yet, so they stay `unclear`. This is intentional and per spec (they are sequenced into later iterations). Their target states (seller_control, absorption pair, unclear-chop) are NOT yet implemented.
- **Five blueprint features are deferred.** `spread_change, absorption_score, bid_refresh_score, ask_refresh_score, liquidity_imbalance` are not computed this iteration (added additively when their owning journeys, J-04/J-05 etc., are built). The Features panel shows the nine implemented features.
- **No persistence / no Stop control / no L2.** In-memory only; `DELETE /watch` and the Stop control are deferred to the J-09 iteration; Level 2 / `BookLevelEvent` is later.
- **Warm-up floor = 40 trades.** SIM-BUYER shows an honest cold-start `unclear` for ~3–4s before resolving to buyer_control; this margin above the confidence bar deliberately prevents boundary chatter as the primary window fills.

## Suggested Next Phase

Implement **SIM-SELLER → seller_control (J-03)**: it is the direct mirror of buyer_control (high `aggressive_sell_ratio` AND negative `sell_price_impact` AND stable spread AND elevated trade_speed), reusing the existing engine/classifier structure and adding one scenario generator plus one classifier branch and its negative guard test. This keeps the iteration tight and extends the classifier symmetrically before tackling the price-impact-critical absorption pair (J-04/J-05).
