# goal-i_will_be_rich-iter-4 Execution Plan

**Goal:** Build the `seller_control` path so watching `SIM-SELLER` settles the cockpit on
**seller_control** (rose), promoting **J-03 failing → passing** while J-01/J-02 (buyer) and
J-08 (single source of truth) stay green. Net-new **backend** work; **no frontend code**.

**Depth: full** — new classifier branch + config thresholds + simulator scenario +
deterministic/guard unit tests (the seller price-impact guard is a critical anti-goal
surface). This overrides the iter-3 evaluator's "lean/already-built" note, which codebase
inspection disproves (classifier resolves only `buyer_control`/`unclear`; `SIM-SELLER`
emits zero events today). Alignment with `docs/goal.md` is clean — no drift, no scope creep.

## What to Build

- **`config.py`** — add seller-side thresholds as the negative mirror of the buyer set:
  - `min_aggressive_sell_ratio: float = 0.60` (mirror of `min_aggressive_buy_ratio`).
  - `max_sell_price_impact: float = -0.02` (the **negative** mirror of `min_buy_price_impact = +0.02`; the keystone guard — `seller_control` requires `sell_price_impact <= max_sell_price_impact`, i.e. price actually fell).
  - **Reuse** all side-neutral scales/weights already in config (`ratio_scale`, `impact_scale`, `speed_scale`, `max_stable_spread`, `min_trade_speed`, `confidence_weights`, `reasonable_confidence`, `max_confidence`, `warmup_min_events`). Do **not** duplicate per-side copies — symmetric scoring must read the same numbers so buyer/seller confidence stay calibrated identically.
- **`classifier.py`** — add `STATE_SELLER_CONTROL = "seller_control"` and a `seller_control` gate that is the strict mirror of `buyer_control`:
  - Gate (primary window, ALL must hold): `aggressive_sell_ratio >= min_aggressive_sell_ratio` **AND** `sell_price_impact <= max_sell_price_impact` (negative — **price impact, not aggression**) **AND** `average_spread <= max_stable_spread` **AND** `trade_speed >= min_trade_speed`; emit `seller_control` only when confidence `>= reasonable_confidence`, else stay `unclear`.
  - `_seller_confidence(...)` mirroring `_buyer_confidence`; impact component scores the **magnitude** past the negative cutoff: `(max_sell_price_impact - sell_price_impact) / impact_scale`, clamped — sharper drop ⇒ higher confidence. Reuse the same weights/scales.
  - `_seller_observations(...)`: `"Seller aggression increasing"`, `"Price falling on sell prints"` (only when impact is negative), `"Spread stable and narrow"`.
  - Make branch precedence explicit; the buyer/unclear results MUST be byte-identical to today (regression guard = existing buyer tests).
- **`simulated.py`** — add `_seller_control_stream()` (deterministic, seeded), the mirror of `_buyer_control_stream()`, and wire `elif self.ticker == "SIM-SELLER": yield from self._seller_control_stream()`. Majority aggressive **sells**, minority aggressive buys; on an aggressive-sell tick (same probability the buyer stream lifts) drop the quote **one tick** (bid and ask both down) so `sell_price_impact` is genuinely **negative**. Narrow/stable spread; reuse the buyer stream's quote size, trade sizes, and logical `dt`. All randomness from the seeded `random.Random`. The other three reserved sims still emit nothing.
- **Tests** — new deterministic + guard unit tests (see Key Test Scenarios); update the now-false reserved-ticker test.

## Agents Required

- **developer: yes** — implements the entire seller backend (config thresholds, classifier seller gate + confidence + observations, simulator seller stream, and all new/updated tests). Writes the dev handoff.
- **backend-data: yes** — config + classifier + simulator + pytest suite.
- **frontend-ux: no** — frontend is already generic and rose-ready (verified): `lib/format.ts` maps `seller_control`→`text-rose-400`/`bg-rose-500`, `sideColor("sell")`/`impactColor(negative)`→rose; `TopBar` input is free-text; the transition emitter is state-generic. **Do NOT edit `format.ts`, `TapeStatePanel`, `TopBar`, or any component** (spec OUT OF SCOPE). The browser pass *verifies* the existing UI; it adds no code.

## Frontend Present

Frontend Present: yes

(No frontend *code* changes, but J-03 is a user-facing journey whose acceptance is the
on-screen rose `seller_control` render — Chrome MCP browser QA is **required**, not optional.
This is the first on-screen render of the rose state path via dynamic `stateColor("seller_control")`.)

## Files to Create/Modify

- `apps/backend/app/config.py` — add `min_aggressive_sell_ratio` + `max_sell_price_impact` (negative); reuse existing side-neutral scales/weights.
- `apps/backend/app/engine/classifier.py` — add `STATE_SELLER_CONTROL`, the seller gate, `_seller_confidence`, `_seller_observations`; buyer/unclear paths unchanged.
- `apps/backend/app/providers/simulated.py` — add `_seller_control_stream()`; wire `SIM-SELLER` into `stream()`.
- `apps/backend/tests/test_classifier.py` — add the seller mirror guard tests.
- `apps/backend/tests/test_scenario.py` — add SIM-SELLER end-to-end + determinism tests; **move** `test_reserved_ticker_known_but_unresolved` to a still-reserved ticker (e.g. `SIM-BIDABS`) so it stays true.
- `docs/handoffs/goal-i_will_be_rich-iter-4-dev.md` — dev handoff (required by DoD).

## Critical Implementation Notes (read before coding)

- **Aggressor is classified by trade-price-vs-quote in the engine, NOT by the emitted `Side`.** The buyer stream emits trades with `Side.UNKNOWN` *at the ask* (engine tags them aggressive buys); the seller mirror MUST emit aggressive sells **at the bid** so the engine tags them `Side.SELL` and `sell_price_impact` (sum of `price − prev_price` over SELL trades in `features.py:72-94`) accumulates **negative**. Printing at the wrong side silently breaks the negative-impact signal. This is the single most error-prone detail.
- **Symmetry discipline:** implement seller_control as the strict mirror of buyer_control — same structure, same reused scales/weights, only the impact cutoff negated. By symmetry, a *symmetric* classifier input (sell-ratio 0.90, sell-impact −0.40, spread 0.02, speed 2.0) should compute the **same** confidence the buyer test pins (`≈0.8542`) — a strong transparent cross-check. Avoid a forked/parallel classifier; this keeps J-04/J-05 (absorption) a clean extension.
- **Mutual exclusivity:** buyer and seller gates cannot both fire (aggressive ratios are complementary shares of directional volume, neither can reach 0.60 simultaneously), but make precedence explicit and ensure neither branch perturbs the other.

## UI Evolution

- **New user-facing capability:** watching `SIM-SELLER` now produces a real, resolved **seller_control** read (today it hangs at cold-start `unclear`). The user sees the down-tape identified with the same fidelity as the up-tape, in the correct (rose) color language.
- **New information displayed:** no new *value type* — `seller_control` is an already-enumerated value of the existing Tape-state contract; this iteration makes the engine actually emit it. Same per-snapshot `tape_state`/`confidence`/features, now for a down-tape.
- **New user actions:** none (existing ticker input + Watch button drive it).
- **UI surface changes:** none — the single `/` cockpit is structurally unchanged; only the content differs (rose seller read vs green buyer read) via existing components.
- **Navigation changes:** none.

## Visual Requirements (verify, do not build)

- **Component patterns:** existing hand-built panels (`TapeStatePanel`, `FeaturesPanel`, `RecentTradesPanel`, event log) render the snapshot verbatim — unchanged.
- **Layout:** existing single-`/` cockpit grid — unchanged.
- **Color semantics (the load-bearing verification):** `seller_control` ⇒ headline state label rose `text-rose-400` → `rgb(251,113,133)`; confidence-bar fill rose `bg-rose-500` → `rgb(244,63,94)`; negative `sell_price_impact` cell rose via `impactColor`. Tailwind v3 defaults (`theme.extend` empty).
- **States to handle:** cold-start `unclear` → resolved `seller_control` transition; live WS updates with no reload. (Loading/empty/error treatments already exist; unchanged.)

## Key Test Scenarios (must pass for the phase to be complete)

**Backend unit/integration (`pytest tests/ -v` — currently 24/24; expect new seller tests on top, all green):**
- `test_classifier.py`:
  - `test_seller_control_with_reasonable_confidence` — high `aggressive_sell_ratio` + sufficiently **negative** `sell_price_impact` + stable spread + elevated speed ⇒ `seller_control` @ confidence ≥ `reasonable_confidence`; **pin the exact transparent confidence** (mirror of the buyer test's `pytest.approx`; by symmetry expect `≈0.8542` for a symmetric input).
  - `test_price_impact_guard_zero_impact_is_not_seller_control` — high `aggressive_sell_ratio` but `sell_price_impact = 0.0` ⇒ **NOT** `seller_control` (aggression without price progress ≠ control).
  - `test_price_impact_guard_positive_impact_is_not_seller_control` — `sell_price_impact = +0.05` (price rose) ⇒ **NOT** `seller_control`.
  - Existing buyer/unclear tests still pass unchanged (default `_features()` has `aggressive_sell_ratio=0.10` — must not trip the seller gate).
- `test_scenario.py`:
  - `test_sim_seller_settles_on_seller_control` — `SimulatedProvider("SIM-SELLER","seller_control")` through `TapeEngine` ⇒ `tape_state == seller_control`, `confidence >= reasonable_confidence`, `aggressive_sell_ratio >= min_aggressive_sell_ratio`, `sell_price_impact < 0`, and `"Tape state changed to seller_control" in snapshot.event_log`.
  - `test_sim_seller_is_deterministic` — two runs ⇒ identical snapshot.
  - **Update** `test_reserved_ticker_known_but_unresolved` to a still-reserved ticker (e.g. `SIM-BIDABS`); keep asserting `build_provider("NOPE123") is None`.

**Browser (the real gate for J-03 — `Frontend Present: yes`):**
- **Precondition (iter-1 lesson):** `rm -rf apps/frontend/.next`; restart the managed dev server with `NEXT_PUBLIC_API_URL` set; confirm `GET /` → HTTP 200 before driving. An all-SKIPPED run is **not** verification.
- **J-03:** type `SIM-SELLER`, Watch, wait for resolve ⇒ tape-state panel reads **"Seller Control"** @ confidence ≥ threshold; `aggressive_sell_ratio` high; `sell_price_impact` negative; event log contains **"Tape state changed to seller_control"**; values update over WS without reload.
- **Color = measured, not eyeballed (iter-2 + iter-3 lesson):** `getComputedStyle` on (a) the "Seller Control" headline label and (b) the confidence-bar fill ⇒ assert rose `rgb(251,113,133)` / `rgb(244,63,94)`, explicitly **not** slate `rgb(226,232,240)`; plus a `document.styleSheets` **base-selector** probe asserting `.text-rose-400{` and `.bg-rose-500{` resolve to real rules (exclude `hover:`/`focus:` variants). Sanity-check the negative `sell_price_impact` cell computes rose via `impactColor`.
- **Required-still-passing re-verify:** J-01/J-02 on `SIM-BUYER` (still `buyer_control` @ ≥ threshold, green color layer intact) and J-08 (UI ≡ REST exact agreement) — proving the new seller branch did not perturb the buyer read or single-source-of-truth.
- **Error case:** unknown ticker `NOPE123` ⇒ `POST /watch` 400 and the UI surfaces the error (no fabricated snapshot).

**Build:** `cd apps/frontend && npm run build` clean (no frontend code changed, but DoD requires a clean build).

## Anti-goal Guards (must hold)

- **Price impact, not aggression:** `seller_control` requires `sell_price_impact <= max_sell_price_impact` (negative); zero/positive impact ⇒ never `seller_control` (the absorption states own that case in J-04/J-05). *(critical)*
- **Single source of truth:** UI/REST/WS read one engine snapshot; no recomputation, no second producer or parallel path for the seller state — same canonical owner (`TapeStateClassifier` → snapshot → `GET /tape/{ticker}/state`). *(critical)*
- **No fabricated data:** `SIM-SELLER` drives real seeded events; unknown tickers still 400, not-watched reads still 404. *(critical)*
- **Honest uncertainty:** confidence below `reasonable_confidence` stays `unclear`. *(critical)*
- **No magic numbers:** seller thresholds live in `config.py`; no literals in engine/classifier. **Deterministic:** seeded `random.Random`, same seed ⇒ identical stream.
- **Coherence:** no new value/endpoint/route/nav; `seller_control` rides the existing Tape-state contract row (one producer, one canonical endpoint `/state`). No `blueprint.md` edit; no re-approval requested.

## Out of Scope (exclude — flag if requested)

- **No frontend code changes** (UI already rose-ready) — do not refactor `format.ts` or any component.
- **Do NOT touch or relax** the `buyer_control` gate or its positive-impact guard — add the seller branch alongside; existing buyer tests are the regression guard.
- **J-04/J-05 (bid/ask absorption) NOT started**; **stream-status-dot consolidation stays DEFERRED** (belongs to J-04/J-05/J-09 — not forgotten, must land before those); no `DELETE /watch` UI control (J-09); no new panels/routes/values; SIM-BIDABS / SIM-ASKABS / SIM-CHOP stay reserved-and-silent.

## Assumptions (documented per questioning policy — none blocking)

- The suggested config values (`min_aggressive_sell_ratio = 0.60`, `max_sell_price_impact = -0.02`) are adopted as the spec's negative mirror of the buyer gate; the developer may tune only if a deterministic test forces it, keeping symmetry with the buyer set.
- The seller stream mirrors the buyer stream's shape constants (`_P_SELL`/`_P_LIFT_ON_BUY` analogues, sizes, `dt`, quote size) so confidence lands with the same comfortable margin above `reasonable_confidence` as SIM-BUYER (~0.87) — the exact pinned scenario confidence is whatever the seeded stream deterministically yields; assert `>= reasonable_confidence`.
- The harness-managed dev server on :3650/:8650 is the browser target; QA clears `.next` and restarts it per the iter-1 precondition regardless.
