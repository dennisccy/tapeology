# Phase goal-i_will_be_rich-iter-1 — UI Surface Map

**Phase:** goal-i_will_be_rich-iter-1
**Date:** 2026-06-02
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

All surfaces are **new** — this is the greenfield first build of the `/` cockpit. The single route is `/`; the panels below are composed within it.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `IdleState` | New component | First build — empty cockpit before any ticker is watched | Load `/` without watching: confirm an empty/idle cockpit shows and **no** bid/ask/state/confidence numbers are rendered (no fabricated values) |
| `/` | `TopBar` (ticker input + **Watch** button) | New form / action | New user action: `POST /watch/{ticker}` on submit | Type `SIM-BUYER`, click **Watch**: confirm the watched-ticker label updates to `SIM-BUYER` and the stream-status dot moves from idle → connecting → live |
| `/` | `TopBar` (scenario indicator + stream-status dot) | New component | Show which scenario is replaying and live/idle/closed status | After watching `SIM-BUYER`, confirm the scenario indicator reads `scenario: buyer_control` and the status dot shows "live" |
| `/` | `TopBar` (watch error message) | New behavior | No-fabrication anti-goal — unknown ticker must error, not fake data | Type `NOPE` (a non-sim ticker), click **Watch**: confirm an explicit error message appears and **no** panels populate with numbers |
| `/` | `TapeStatePanel` | New component | Show classified tape state + confidence (J-02) | Watch `SIM-BUYER`, wait past warm-up: confirm the panel shows **Buyer Control** with a confidence ≥ the configured threshold and a confidence bar; confirm it is color-coded green |
| `/` | `TapeStatePanel` (warm-up note) | New behavior | Honest-uncertainty anti-goal — no premature directional call | Immediately after Watch, confirm the panel shows a "Warming up…" note / `unclear` low confidence before resolving (no instant directional call) |
| `/` | `QuotePanel` | New component | Show live bid / ask / spread / last (J-01) | Watch `SIM-BUYER`: confirm bid (green), ask (red), spread, and last are all numeric and that `spread == ask − bid` |
| `/` | `RecentTradesPanel` | New table | Show recent trades with aggressor side (J-01) | Watch `SIM-BUYER`: confirm the trade rows show price / size / side and are color-coded green (buy) / red (sell) / slate (unknown) |
| `/` | `FeaturesPanel` | New component | Show the nine named features (J-01) | Watch `SIM-BUYER`: confirm trade_speed, aggressive_buy_ratio, aggressive_sell_ratio, net_aggressive_volume, buy_price_impact, sell_price_impact each show a number; confirm `aggressive_buy_ratio` reads high and `buy_price_impact` reads positive |
| `/` | `FeaturesPanel` (window selector) | New control | Per-window structure for features | Click the 10s / 30s / 60s / 180s / 300s tabs: confirm the displayed feature values change with the selected window |
| `/` | `ObservationsPanel` | New component | Show human-readable evidence (J-01) | Watch `SIM-BUYER`: confirm ≥1 observation message appears (e.g. "Buyer aggression increasing") |
| `/` | `EventLogPanel` | New component | Show transition messages (J-02) | Watch `SIM-BUYER`: confirm the event log contains `"Tape state changed to buyer_control"` (newest first) |
| `/` | `Cockpit` (live WS updates) | New behavior | Live updates without reload (J-01) | Watch `SIM-BUYER` and wait: confirm panel values change over time **without** reloading the page |
| `/` | `Cockpit` (single source of truth) | New behavior | J-08 — UI must match REST verbatim | Compare the UI's state/confidence against `GET /tape/SIM-BUYER/state` and the feature readouts against `GET /tape/SIM-BUYER/features`: confirm they match exactly (one engine value per metric) |
| `/` | Footer disclaimer | New element | No trading-advice anti-goal | Confirm the footer reads "Descriptive only — not trading advice" |

---

## Backend-Only Changes (No UI Impact)

The bulk of this iteration is the engine that feeds the cockpit. These are consumed indirectly via the REST/WS endpoints the UI reads, but have no UI surface of their own:

- `app/providers/{base,simulated}.py` — provider interface + deterministic `SimulatedProvider` — no direct UI surface (drives the data the cockpit displays).
- `app/config.py` — single-source config for windows / thresholds / confidence boundaries (no-magic-numbers anti-goal) — no UI surface.
- `app/engine/{market_state,aggressor,features,classifier,snapshot,observations,tape_engine}.py` — the computation pipeline producing the one snapshot — no UI surface (values surface through the panels).
- `app/watch_manager.py` — per-ticker engine lifecycle — no UI surface.
- `app/serializers.py`, `app/main.py`, `main.py` — REST/WS endpoints (`POST /watch/{ticker}`, `GET /tape/{ticker}/{state,features,events,summary}`, `WS /tape/{ticker}/stream`, `GET /health`). These are **backend-api** changes the frontend *does* consume — their effect is visible through the cockpit panels above, but the endpoints themselves are not a UI surface.
- `apps/backend/tests/*` — test suite — no UI surface.
- Reserved-but-inert scenarios (`SIM-SELLER`, `SIM-BIDABS`, `SIM-ASKABS`, `SIM-CHOP`) — watchable but emit no events; they stay `unclear` and have no dedicated UI behavior yet.

---

## Summary

- **Frontend surfaces changed:** 14 (all new — one `/` route composing the app shell + six panels + idle/error states)
- **New pages/routes:** 1 (`/`)
- **Modified components:** 0 (all 10 frontend components + 5 lib modules are new; none pre-existed)
- **Navigation changes:** no — `/` is the single existing home per the approved blueprint (no reapproval)
- **Backend-only changes:** ~16 backend modules + the test suite (engine, providers, config, watch manager, serializers, API)
