# goal-i_will_be_rich-iter-1 Functional Test Plan

**Phase:** goal-i_will_be_rich-iter-1
**Date:** 2026-06-02
**Frontend Present:** yes

## Phase Goal

Stand up the end-to-end tape-cockpit walking skeleton (SimulatedProvider → engine → rule-based classifier → REST + WebSocket API → `/` Next.js cockpit) and prove it live on the **`SIM-BUYER`** scenario, with REST, WS, and the UI all showing one identical engine value per metric (single source of truth), keyed on price impact, not raw aggression.

## Test Cases

### TC-01 — Cockpit renders all panels live on SIM-BUYER (J-01)

**Type:** browser
**Preconditions:** Backend running on `:8000`, frontend on `:3000`.

**Steps:**
1. Navigate to `http://localhost:3000/`.
2. Enter `SIM-BUYER` in the ticker input and click **Watch**.
3. Wait through warm-up for the stream to populate panels.

**Expected outcome:** Within warm-up, all six panels render live values: Quote (bid/ask/spread/last numeric), Recent-trades (price/size/side), Features, Tape-state (state + confidence), Observations (≥1 message), Event-log (≥1 message).
**Pass criteria:** Every panel shows non-empty numeric/text data; `spread == ask − bid` exactly; Recent-trades rows each show a side; features `trade_speed`, `aggressive_buy_ratio`, `aggressive_sell_ratio`, `net_aggressive_volume`, `buy_price_impact`, `sell_price_impact` each show a number; Tape-state shows one of the five states + a confidence score; Observations and Event-log each ≥1 message.

### TC-02 — Live updates over WebSocket without page reload (J-01)

**Type:** browser
**Preconditions:** TC-01 watch active.

**Steps:**
1. With `SIM-BUYER` watched, observe Recent-trades / Features / Event-log over several seconds without reloading.
2. Confirm no full-page reload occurs (no navigation).

**Expected outcome:** Panel values change/append as the simulated stream advances, pushed via `WS /tape/SIM-BUYER/stream`.
**Pass criteria:** At least one panel's values visibly change between two observations with no page reload; stream-status dot indicates a live/connected state.

### TC-03 — SIM-BUYER settles on buyer_control with positive impact (J-02)

**Type:** browser
**Preconditions:** TC-01 watch active and warmed up.

**Steps:**
1. Watch `SIM-BUYER` and let the tape resolve past warm-up.
2. Read the Tape-state panel, the `aggressive_buy_ratio` and `buy_price_impact` readouts, and the Event-log.

**Expected outcome:** State settles on **buyer_control** at confidence ≥ configured threshold; `aggressive_buy_ratio` reads high and `buy_price_impact` reads positive; Event-log contains `"Tape state changed to buyer_control"`.
**Pass criteria:** Tape-state == `buyer_control`; confidence ≥ configured "reasonable" threshold; `buy_price_impact` > 0; `aggressive_buy_ratio` high; Event-log line `"Tape state changed to buyer_control"` present.

### TC-04 — UI matches REST and WS, single source of truth (J-08)

**Type:** browser
**Preconditions:** TC-01 watch active and warmed up.

**Steps:**
1. With `SIM-BUYER` warmed up, read tape state + confidence and feature readouts from the UI.
2. In parallel call `curl http://localhost:8000/tape/SIM-BUYER/state` and `curl http://localhost:8000/tape/SIM-BUYER/features`.
3. Compare UI values against the REST responses for the same snapshot.

**Expected outcome:** UI state + confidence exactly match `/tape/SIM-BUYER/state`; UI feature readouts match `/tape/SIM-BUYER/features` — one engine value per metric across REST, WS, and UI.
**Pass criteria:** State, confidence, and each compared feature are identical (UI does not recompute); no divergence in `spread`, ratios, impacts, or confidence.

### TC-05 — Idle/empty cockpit before any ticker is watched

**Type:** browser
**Preconditions:** Frontend running; no ticker watched (fresh load).

**Steps:**
1. Navigate to `http://localhost:3000/` without watching anything.

**Expected outcome:** Empty cockpit with no fabricated or stale numbers; an idle/empty state is shown.
**Pass criteria:** No numeric tape data displayed; idle/empty messaging present; no profitability claim or trading-advice language anywhere.

### TC-06 — Canonical REST reads return the engine snapshot (J-08)

**Type:** api
**Preconditions:** Backend running; `POST /watch/SIM-BUYER` already issued and warmed up.

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/watch/SIM-BUYER`
2. `curl -s http://localhost:8000/tape/SIM-BUYER/state`
3. `curl -s http://localhost:8000/tape/SIM-BUYER/features`
4. `curl -s http://localhost:8000/tape/SIM-BUYER/events`
5. `curl -s http://localhost:8000/tape/SIM-BUYER/summary`

**Expected outcome:** POST returns 2xx; `/state` returns state + confidence; `/features` returns the named features; `/events` returns event-log messages; `/summary` re-exposes the snapshot headline subset without recomputing.
**Pass criteria:** All return 200; `/summary` state/confidence equal `/state`; `/summary` headline feature subset equals the matching `/features` values; `spread == ask − bid` in the payload (produced once in MarketState).

### TC-07 — Unknown / non-sim ticker on POST errors, no fabrication

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/watch/NOPE123`

**Expected outcome:** Explicit error / no-data response; no engine spun up, no synthesized trades/quotes/state.
**Pass criteria:** Non-2xx (e.g. 400/404) with an explicit error body; subsequent `GET /tape/NOPE123/state` does not return a fabricated snapshot.

### TC-08 — Read of a not-watched ticker returns explicit not-watched

**Type:** api
**Preconditions:** Backend running; `SIM-SELLER` registered but never watched.

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/tape/SIM-SELLER/state`

**Expected outcome:** Explicit not-watched response (e.g. 404); no fabricated snapshot.
**Pass criteria:** HTTP 404 (or documented not-watched code); body contains no tape state/feature values.

### TC-09 — Backend unit/integration suite passes

**Type:** artifact
**Preconditions:** Backend tests present under `apps/backend/tests/`.

**Steps:**
1. Run the backend test suite (pytest from `apps/backend/`).

**Expected outcome:** All unit/integration tests pass, covering aggressor classification, FeatureEngine values + determinism, classifier outcomes, the price-impact guard, single-source-of-truth, and error cases.
**Pass criteria:** Exit code 0; 0 failures; includes a `SIM-BUYER` scenario test asserting buyer_control at confidence ≥ threshold.

### TC-10 — Aggressor classifier boundary cases

**Type:** artifact
**Preconditions:** `tests/test_aggressor.py` exists.

**Steps:**
1. Inspect/run the aggressor tests.

**Expected outcome:** price ≥ ask ⇒ buy; ≤ bid ⇒ sell; strictly between ⇒ unknown; uses the quote in effect at the trade timestamp; edges price==ask ⇒ buy, price==bid ⇒ sell, no prior quote ⇒ unknown.
**Pass criteria:** All listed cases (including the three edge cases) have asserting tests and pass.

### TC-11 — FeatureEngine determinism and event-timestamp windowing

**Type:** artifact
**Preconditions:** `tests/test_features.py` exists.

**Steps:**
1. Inspect/run the FeatureEngine tests.

**Expected outcome:** Feeding a known ordered stream asserts exact feature values for ≥1 window; same stream + seed twice ⇒ identical snapshot; windows keyed on event timestamps, not wall-clock.
**Pass criteria:** Exact-value assertions present; a determinism (run-twice-identical) assertion present and passing; no wall-clock dependence.

### TC-12 — Price-impact guard: aggression without impact ≠ buyer_control (critical)

**Type:** artifact
**Preconditions:** `tests/test_classifier.py` exists.

**Steps:**
1. Inspect/run the classifier guard test.

**Expected outcome:** A synthetic stream with high `aggressive_buy_ratio` but zero/negative `buy_price_impact` does NOT classify as buyer_control — proving the rule keys on impact, not aggression.
**Pass criteria:** Test exists and passes; resulting state is not `buyer_control` for the no-impact stream.

### TC-13 — Cold-start / insufficient evidence ⇒ unclear at low confidence

**Type:** artifact
**Preconditions:** Classifier tests exist.

**Steps:**
1. Inspect/run the cold-start classifier test (and/or watch `SIM-BUYER` and read state during the first sub-warm-up tick).

**Expected outcome:** Before the warm-up minimum-events floor, state is `unclear` with low confidence — never a fabricated directional call.
**Pass criteria:** Cold-start assertion yields `unclear` + low confidence; no directional state manufactured pre-warm-up.

### TC-14 — No magic numbers: thresholds sourced from config

**Type:** artifact
**Preconditions:** `app/config.py` and engine/classifier modules present.

**Steps:**
1. Inspect `app/config.py` for window lengths {10,30,60,180,300}s, large-print size, buyer_control thresholds (min `aggressive_buy_ratio`, min positive `buy_price_impact`, max stable spread, min `trade_speed`), confidence boundaries, warm-up floor.
2. Grep engine/classifier code for inline numeric literals of those quantities.

**Expected outcome:** All such constants live in config; none appear inline in engine/classifier code.
**Pass criteria:** Each threshold/window/cutoff/boundary present in config; no corresponding magic-number literal inline in engine/classifier modules.

### TC-15 — Provider-agnostic engine boundary

**Type:** artifact
**Preconditions:** `app/providers/base.py` and engine modules present.

**Steps:**
1. Inspect engine and API imports/dependencies.

**Expected outcome:** Engine and API depend only on the provider interface (`TradeEvent` / `QuoteEvent`); no direct dependency on `SimulatedProvider` internals; `BookLevelEvent` reserved but not implemented in a way that precludes later addition.
**Pass criteria:** No engine/API code imports simulator-specific internals; provider interface is the only coupling point.

### TC-16 — Color semantics and no trading-advice language

**Type:** browser
**Preconditions:** TC-01/TC-03 watch active.

**Steps:**
1. With `SIM-BUYER` in buyer_control, inspect color coding of trade rows and the tape-state panel.
2. Scan all visible UI text.

**Expected outcome:** green = buy-side / positive impact, red = sell-side / negative impact, amber = absorption / unclear; no profitability claim and nothing presented as trading advice.
**Pass criteria:** Buy-side / positive readouts render green, sell-side / negative red, unclear/absorption amber; no profitability or advice language anywhere in the UI.

### TC-17 — Dev handoff artifact exists

**Type:** artifact
**Preconditions:** Phase implementation complete.

**Steps:**
1. Check `docs/handoffs/goal-i_will_be_rich-iter-1-dev.md` exists and is non-empty.

**Expected outcome:** Dev handoff is present per Definition of Done.
**Pass criteria:** File exists and documents what was built.

## Summary

Total test cases: 17
- Browser tests: 6 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-16)
- API tests: 3 (TC-06, TC-07, TC-08)
- Artifact checks: 8 (TC-09, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15, TC-17)

Coverage maps to: J-01 (TC-01, TC-02), J-02 (TC-03), J-08 (TC-04, TC-06); anti-goals — single source of truth (TC-04, TC-06), price-impact-over-aggression (TC-12), honest uncertainty (TC-13), no fabrication (TC-05, TC-07, TC-08), determinism (TC-11), no magic numbers (TC-14), provider-agnostic (TC-15).
