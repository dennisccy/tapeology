# goal-i_will_be_rich-iter-5 Execution Plan

Absorption pair — **bid_absorption (J-04)** & **ask_absorption (J-05)**: the product's
defining "price impact, not raw aggression" case. Same high one-sided aggression as
control, but with **flat** price impact + a refreshing quote ⇒ *absorption*, never
*control*. Plus the thrice-deferred **stream-status-dot** coherence consolidation.

Goal/blueprint alignment verified by direct code inspection (not forward-carried notes):
`classifier.py` has only buyer/seller/unclear; `features.py` `FEATURE_NAMES` has 9 of 14
(absorption triplet absent) and `_Window` stores only `(ts, spread)` — no bid/ask series;
`config.py` has no absorption thresholds; `simulated.py` registers SIM-BIDABS/SIM-ASKABS
but their streams emit **zero** events. `format.ts` already maps both absorption states →
amber labels; `TapeSnapshot.stream_status` already exists and is serialized. **No scope
drift, no anti-goal conflict** — additive values on existing contract rows; one producer /
one endpoint each; no new route; the dot change *removes* a parallel client source.

## What to Build

**Backend (net-new):**
- Three features in `FeatureEngine`, computed additively (existing 9 stay byte-identical):
  - `bid_refresh_score` — among aggressive-**sell** prints in the window, fraction after
    which the **bid did not fall** (held/refreshed). High when bid holds under selling
    (SIM-BIDABS); low when bid walks down (SIM-SELLER). Pure, deterministic.
  - `ask_refresh_score` — strict mirror over aggressive-**buy** prints (ask did not rise).
  - `absorption_score` — summary: high dominant aggressive ratio **and** that side's price
    impact flat (near zero). Deterministic; scales/cutoffs from config.
  - To compute refresh scores, thread the **bid/ask price series** into `_Window`
    (currently only `(ts, spread)`) additively via `FeatureEngine.add_quote(...)` and the
    `TapeEngine.process_event` quote branch. Do **not** change how `average_spread` or any
    existing feature is computed.
- Two classifier states `bid_absorption` / `ask_absorption` with gates inserted **after**
  the buyer/seller-control gates and **before** the `unclear` fallback (control precedence):
  - **bid_absorption:** `aggressive_sell_ratio >= min_aggressive_sell_ratio` AND
    `sell_price_impact > max_sell_price_impact` (no real drop — complement of seller-control's
    impact condition) AND `bid_refresh_score >= min_bid_refresh_score` AND stable spread;
    emit only at confidence `>= reasonable_confidence`, else stay `unclear`.
  - **ask_absorption:** the buy/ask mirror (`aggressive_buy_ratio` high,
    `buy_price_impact < min_buy_price_impact`, `ask_refresh_score >= min_ask_refresh_score`,
    stable spread).
  - **Keystone precedence (critical anti-goal):** high sell aggression **with** real negative
    impact ⇒ `seller_control`; high sell aggression with **flat** impact + bid refresh ⇒
    `bid_absorption` (never `seller_control`, never silently `unclear`). Symmetric for buy/ask.
    Gates are mutually exclusive on the impact condition.
  - Absorption confidence function(s) (reward flat impact — cannot reuse the directional
    impact component unchanged) + per-tick observations (e.g. "Heavy sell volume being
    absorbed", "Bid refreshing at <price>", "Price holding despite sell prints").
- Absorption **event-log message** generated **once** in the engine emitter (single source):
  e.g. "Large sell print absorbed" / "Bid refreshing at <price>" (bid) and "Large buy print
  absorbed" / "Ask refreshing at <price>" (ask). Keep the existing "Tape state changed to
  bid_absorption / …ask_absorption" transition line working. Message must reflect **real**
  in-window evidence (no fabrication) — the emitter needs the evidence threaded to it.
- Config-only thresholds (no-magic-numbers): `min_bid_refresh_score`,
  `min_ask_refresh_score` (and `min_absorption_score` if the gate uses it); any flat-impact
  band / near-zero ceiling only if the design needs one; absorption confidence scales/weights.
  Reuse side-neutral existing values (`max_stable_spread`, `min_trade_speed`, ratio floors,
  `reasonable_confidence`, `max_confidence`, `warmup_min_events`) — add per-side only where
  semantics genuinely differ.
- Two deterministic, seedable simulated streams wired into `SimulatedProvider.stream()`
  (currently SIM-BIDABS/SIM-ASKABS emit nothing); emit only `QuoteEvent`/`TradeEvent` with
  `Side.UNKNOWN` (aggressor classification stays in the engine):
  - `_bid_absorption_stream()` (SIM-BIDABS): majority aggressive **sells** print at the bid
    but the **bid holds** (refreshes, does NOT drop) ⇒ `aggressive_sell_ratio` high,
    `sell_price_impact ≈ 0` (above the −cutoff), `bid_refresh_score` high, large prints
    present. Contrast SIM-SELLER (bid walks down ⇒ strongly negative impact).
  - `_ask_absorption_stream()` (SIM-ASKABS): the buy/ask mirror.

**Frontend:**
- `FeaturesPanel.tsx`: add three rows to the fixed `FEATURE_ROWS` (`absorption_score`,
  `bid_refresh_score`, `ask_refresh_score`; sensible labels, 3 decimals, not color-by-sign).
  Existing 9 rows unchanged.
- Tape-state rendering: `bid_absorption`/`ask_absorption` already resolve to amber via
  `stateColor`/`stateBarColor`/`stateLabel` — **verify** (do not assume) the first on-screen
  amber render of a *resolved* absorption state computes amber (see Key Test Scenarios).
- Stream-status dot (`TopBar.tsx`): drive the dot from the canonical `snapshot.stream_status`
  (map connecting/live/stale/closed → color/label) when a snapshot is present, falling back to
  the client `connStatus` only for the pre-snapshot idle/connecting affordance. `page.tsx`
  already passes `snapshot` to `TopBar`, so the data is threaded — the change is inside
  `TopBar` (add a `stream_status`→dot map alongside the existing `connStatus` `DOT_COLOR`).
  Must NOT destabilize the live dot on J-01/J-02/J-03.

## Agents Required
- developer: yes -- backend (features + bid/ask threading, classifier states/gates,
  config thresholds, emitter absorption message, two sim streams) and frontend (3 feature
  rows, stream-status-dot consolidation); plus the unit/integration tests below. TDD —
  write the keystone classifier guard tests first.

## Frontend Present
yes

## Files to Create/Modify

**Backend**
- `apps/backend/app/engine/features.py` -- add the 3 features to `FEATURE_NAMES`; thread
  bid/ask into `_Window` + `FeatureEngine.add_quote(...)`; compute refresh/absorption scores
  in `_Window.compute()`. Existing 9 features unchanged (additive only).
- `apps/backend/app/config.py` -- add absorption thresholds + confidence scales/weights;
  reuse side-neutral existing values.
- `apps/backend/app/engine/classifier.py` -- add `STATE_BID_ABSORPTION` /
  `STATE_ASK_ABSORPTION`; insert the two gates (after control, before unclear); absorption
  confidence fns + observations. Buyer/seller/unclear paths behaviourally unchanged.
- `apps/backend/app/engine/observations.py` -- emit the absorption event-log message once,
  from real in-window evidence (extend `on_tick(...)` to receive the evidence it needs);
  keep the transition line working.
- `apps/backend/app/engine/tape_engine.py` -- thread `bid`/`ask` into the `add_quote(...)`
  call (quote branch); pass evidence to the emitter so the absorption message is generated
  once here (single source). No recompute of any displayed value.
- `apps/backend/app/providers/simulated.py` -- add `_bid_absorption_stream()` /
  `_ask_absorption_stream()`; wire `SIM-BIDABS` / `SIM-ASKABS` into `stream()`.

**Frontend**
- `apps/frontend/components/FeaturesPanel.tsx` -- add the 3 absorption rows.
- `apps/frontend/components/TopBar.tsx` -- dot reads `snapshot.stream_status` (with a
  connecting/live/stale/closed map) and falls back to `connStatus` pre-snapshot.

**Tests**
- `apps/backend/tests/test_classifier.py` -- keystone guard tests (see Key Test Scenarios).
- `apps/backend/tests/test_features.py` -- refresh/absorption feature behavior + assert the
  existing 9 feature values are unchanged by the bid/ask `add_quote` threading.
- `apps/backend/tests/test_scenario.py` -- SIM-BIDABS→bid_absorption, SIM-ASKABS→
  ask_absorption (conf ≥ `reasonable_confidence`), per-scenario determinism, and SIM-BUYER
  still buyer_control / SIM-SELLER still seller_control (no misroute/regression).
- `apps/backend/tests/test_api.py` -- `/state` `/features` `/summary` `WS /stream` agree on
  tape_state/confidence + the absorption feature values for a watched absorption ticker.

## UI Evolution (Frontend Present: yes)
- **New user-facing capability:** Watch SIM-BIDABS → **Bid Absorption** (heavy selling
  absorbed, price holding) and SIM-ASKABS → **Ask Absorption** (heavy buying absorbed, price
  stalling) — each with confidence, absorption/refresh readouts, amber coloring, observations,
  and an absorption event-log message, live over WS. The top-bar dot now tells the truth about
  whether the engine's stream is live or closed.
- **New information displayed:** three feature rows (`absorption_score`, `bid_refresh_score`,
  `ask_refresh_score`); two newly reachable amber tape states (Bid/Ask Absorption) with
  confidence; absorption observations + an absorption event-log line.
- **New user actions:** none (no new controls; ticker input + Watch already reach both
  scenarios — Stop/`DELETE /watch` UI stays J-09, out of scope).
- **UI surface changes:** no new page/route — all within the existing `/` cockpit (Features
  panel +3 rows; Tape-state panel renders two already-styled amber states; Observations +
  Event-log show absorption messages; top-bar dot reads canonical stream status).
- **Navigation changes:** none.

## Visual Requirements (Frontend Present: yes)
- **Component patterns:** reuse existing hand-built panels (`Panel`/`Metric` rows in
  `FeaturesPanel`, `TapeStatePanel`, `EventLogPanel`, `ObservationsPanel`, `TopBar` dot). No
  new component types; match the established row/label/value pattern exactly.
- **Layout:** unchanged — the existing 1/2/3-col responsive cockpit grid; absorption rows
  append to the Features panel; absorption states render in the existing Tape-state panel.
- **Key visual effects:** amber semantics for absorption (`text-amber-400` headline,
  `bg-amber-500` confidence-bar fill) per DESIGN SYSTEM — green = buy/positive,
  red = sell/negative, amber = absorption/unclear. Restrained borders + status dot; no new
  effects invented. Monospaced numerics for the new feature readouts (3 decimals).
- **States to handle:** live (resolved absorption render), warm-up/cold-start (honest
  `unclear` before evidence), and the stream-status dot states (connecting/live/stale/closed).
  The new feature rows show "—" when a value is absent (existing `Metric` null treatment).

## Key Test Scenarios
- **J-04 (browser, the real gate):** SIM-BIDABS settles on **bid_absorption** (NOT
  seller_control, NOT unclear) at confidence ≥ `reasonable_confidence`; `aggressive_sell_ratio`
  high while last price does **not** move meaningfully lower; `absorption_score` /
  `bid_refresh_score` elevated; event log shows an absorption message; rendered live in amber
  over WS without reload.
- **J-05 (browser):** SIM-ASKABS → **ask_absorption** (NOT buyer_control/unclear), mirror
  assertions (`aggressive_buy_ratio` high, last price flat, `absorption_score`/
  `ask_refresh_score` elevated, absorption event-log message, live amber render).
- **Keystone classifier guard tests (`test_classifier.py`):** high `aggressive_sell_ratio` +
  `sell_price_impact ≈ 0`/above the −cutoff + high `bid_refresh_score` + stable spread ⇒
  bid_absorption (assert NOT seller_control AND NOT unclear); high `aggressive_sell_ratio` +
  real **negative** `sell_price_impact` ⇒ seller_control (assert NOT bid_absorption — control
  precedence); the buy/ask mirror pair; wide spread blocks absorption (stays unclear).
- **Feature tests:** `bid_refresh_score` high when bid holds / low when it walks down;
  `ask_refresh_score` mirror; `absorption_score` high on high-ratio-flat-impact, low on
  real-impact; existing 9 values unchanged by the add_quote bid/ask threading.
- **Amber render confirmation (not eyeballed, not grep-substring):** the first on-screen amber
  render of a *resolved* absorption state confirmed by `getComputedStyle` **and** a
  base-selector stylesheet probe (`.text-amber-400{` / `.bg-amber-500{`, excluding
  `:hover`/variant forms) — headline `text-amber-400`, confidence-bar `bg-amber-500`.
- **Stream-status dot:** reflects the canonical `snapshot.stream_status` (matches
  `GET /tape/{ticker}/summary`'s `stream_status`); live dot on the directional scenarios
  unaffected.
- **Regression guards (must stay green):** J-01 (six panels live on SIM-BUYER), J-02
  (SIM-BUYER still buyer_control, NOT ask_absorption), J-03 (SIM-SELLER still seller_control,
  NOT bid_absorption), J-08 (UI ≡ REST, including ≥1 absorption feature e.g. `bid_refresh_score`
  and tape_state/confidence). Backend baseline (31 tests) + new absorption tests all pass.
- **Error/no-fabrication paths:** unknown ticker ⇒ 400; not-watched read ⇒ 404; a silent/cold
  provider (no refresh evidence) stays honest `unclear` (the absorption gate requires real
  `*_refresh_score` evidence, not mere absence of impact).

## Assumptions / Notes
- **Browser is the real gate.** If browser-qa SKIPS due to a frontend HTTP 500 (corrupted
  `.next` cache), treat it as a verification-closure signal, NOT a pass: `rm -rf
  apps/frontend/.next`, restart the dev server with `NEXT_PUBLIC_API_URL` set, re-run. A
  backend PASS does not substitute for browser verification of J-04/J-05 (lesson iter-1).
- `page.tsx` already passes `snapshot` to `TopBar`; `TapeSnapshot.stream_status` is already
  typed and serialized (`/state` `/summary` `/stream`). No backend change is needed for the
  dot — `stream_status` already transitions connecting→live→closed (engine + watch_manager).
  `"stale"` is enumerated in the snapshot type but has no current setter; the dot map should
  still handle it defensively.
- **Coherence:** expect COHERENCE-PASS — additive values on existing contract rows, one
  producer / one endpoint each, no new route or parallel shell; the dot change removes a
  parallel client source rather than adding one. `blueprint.md` already carries the additive
  realization note (no new row, no reapproval).
- **Out of scope (do not build):** J-06 (active SIM-CHOP), J-07 (full transition taxonomy),
  J-09 (Stop/`DELETE /watch` UI control), the un-built `spread_change`/`liquidity_imbalance`
  features, L2/persistence/replay, and all permanent anti-goals (execution, scanning, news,
  charting, portfolio).
