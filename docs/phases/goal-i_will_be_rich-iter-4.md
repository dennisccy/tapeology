# Goal Iteration 4 — Build the seller_control path; take J-03 (SIM-SELLER) green

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_rich
- **Iteration:** 4
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-03
- **Required-still-passing journeys:** J-01, J-02, J-08
- **Anti-goal reminders:**
  - **Price impact over raw aggression.** The classifier MUST distinguish absorption from control: a tape with high one-sided aggression but no corresponding price progress MUST resolve to the matching absorption state (bid_absorption / ask_absorption), never to seller_control / buyer_control. Keying on aggression ratios alone is a defect. *(critical)*
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*
  - **No fabricated data.** On a provider gap/failure the system MUST surface an explicit stale/no-data state and MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. *(critical)*
  - **Honest uncertainty.** When evidence is weak or mixed, the spread is wide, or there is no clean price impact, the state MUST be `unclear` with low confidence. The system MUST NOT manufacture a directional call to look decisive. *(critical)*
  - **No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code.
  - **Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine MUST produce identical features, state, and confidence; classification MUST NOT depend on wall-clock time or randomness. Each simulated scenario MUST have an automated test asserting the expected state is reached with reasonable confidence.

## GOAL

Watching `SIM-SELLER` settles the cockpit on **seller_control** — high `aggressive_sell_ratio`, **negative** `sell_price_impact` (real downward price progress, the mirror of the buyer guard), confidence ≥ the reasonable threshold, the tape-state panel and confidence bar render **rose**, and the event log shows "Tape state changed to seller_control" — promoting **J-03 from `failing` to `passing`** while the buyer cockpit (J-01, J-02) and single-source-of-truth (J-08) stay green.

## BACKGROUND

This is the first **new-scenario** journey since the iter-1 foundation. J-01/J-02 (buyer cockpit, now green-with-color) and J-08 (UI ≡ REST) are passing; six journeys (J-03–J-07, J-09) remain unbuilt.

**Premise correction (verified this planning pass — READ THIS).** The iter-3 evaluator recommended J-03 at **lean**, asserting the seller path is "already built and unit-proven … primarily a browser-verification." **Codebase inspection contradicts that** and the depth is therefore **full**:
- `apps/backend/app/engine/classifier.py` resolves **only** `buyer_control` and `unclear`. There is **no** `seller_control` gate, confidence, or observations (the docstring: "The structure extends to the other four states in later iterations"). Only `STATE_BUYER_CONTROL` / `STATE_UNCLEAR` exist.
- `apps/backend/app/providers/simulated.py` has only `_buyer_control_stream()`; `SimulatedProvider.stream()` drives **only** `SIM-BUYER`. `SIM-SELLER` is registered in `SIM_SCENARIOS` (so it is a *known* ticker — `POST /watch/SIM-SELLER` returns 200, not 400) but **emits zero events**, so today it would sit at an honest cold-start `unclear` forever.
- `apps/backend/app/config.py` has only buyer-side thresholds — no seller cutoffs.
- `apps/backend/tests/test_scenario.py`'s only SIM-SELLER test (`test_reserved_ticker_known_but_unresolved`) asserts SIM-SELLER is reserved-but-**unresolved** — the *opposite* of a seller_control proof.

So J-03 is **net-new backend work** (classifier state + config thresholds + simulator scenario + deterministic tests), centered on the **price-impact anti-goal's seller mirror** — the single most safety-critical surface in the product. That is why this runs at **full** depth (new classifier branch + new unit tests beyond browser smoke + a critical anti-goal guard), not lean.

**Good news — the frontend needs no code change (verified):** `apps/frontend/lib/format.ts` already maps `seller_control` → `text-rose-400` / `bg-rose-500`, `sideColor("sell")` → `text-rose-400`, and `impactColor(negative)` → `text-rose-400`; the iter-3 latent-class guard confirmed both rose base utilities resolve to real rules in the served bundle; the ticker input (`TopBar.tsx`) is free-text (accepts `SIM-SELLER`); and the transition emitter (`observations.py`) is state-generic (`"Tape state changed to {state}"`). Once the backend emits `seller_control`, the existing UI renders it. The browser pass **verifies** this; it does not require new frontend code.

**Lessons applied (mandatory reading for the developer/QA):**
- **iter-2 + iter-3 lesson — verify color by a BASE-selector stylesheet probe + `getComputedStyle`, never by eye or `grep`-substring.** J-03 is the **first on-screen render of the rose state path** via the dynamic `stateColor("seller_control")`. The probe MUST match the base selectors `.text-rose-400{` and `.bg-rose-500{` and explicitly EXCLUDE variant forms (`hover:`, `focus:`). (Note: `bg-rose-500` already appears statically in `TopBar.tsx` for the closed-dot, so it is certainly in-bundle; `text-rose-400` for the seller headline is the path to confirm on the live render.) Assert the seller headline computes rose `rgb(251, 113, 133)` and the confidence-bar fill computes rose `rgb(244, 63, 94)` (Tailwind v3 defaults, `theme.extend` empty) — and explicitly **not** the iter-2 colorless slate `rgb(226, 232, 240)`.
- **iter-1 lesson — an all-SKIPPED browser run is NOT verification.** Backend-PASS + clean build is not evidence the UI journey works. Precondition before driving the browser on this Next.js app: `rm -rf apps/frontend/.next`, restart the managed dev server with `NEXT_PUBLIC_API_URL` set, confirm HTTP 200. Do not let backend tests stand in for the browser gate.

## IN SCOPE

### Backend

- [ ] **`config.py` — add seller-side thresholds (no magic numbers), as the negative mirror of the buyer set.** Suggested values, mirroring the existing buyer gate exactly:
  - `min_aggressive_sell_ratio: float = 0.60` (mirror of `min_aggressive_buy_ratio`).
  - `max_sell_price_impact: float = -0.02` — the **negative** mirror of `min_buy_price_impact = +0.02`. `seller_control` requires `sell_price_impact <= max_sell_price_impact` (i.e. price actually fell). This negative cutoff is the keystone guard.
  - **Reuse** the side-neutral scales already in config (`ratio_scale`, `impact_scale`, `speed_scale`, `max_stable_spread`, `min_trade_speed`, `confidence_weights`, `reasonable_confidence`, `max_confidence`, `warmup_min_events`) — do NOT duplicate per-side copies; symmetric scoring must read the same scale numbers so buyer and seller confidence stay calibrated identically.
- [ ] **`classifier.py` — add the `seller_control` gate as the mirror of `buyer_control`.**
  - Add `STATE_SELLER_CONTROL = "seller_control"`.
  - Gate (over the primary window, ALL must hold): `aggressive_sell_ratio >= min_aggressive_sell_ratio` **AND** `sell_price_impact <= max_sell_price_impact` (negative — **price impact, not aggression**) **AND** `average_spread <= max_stable_spread` **AND** `trade_speed >= min_trade_speed`; emit `seller_control` only when the resulting confidence `>= reasonable_confidence`, else stay `unclear` (honest uncertainty).
  - Add `_seller_confidence(...)` mirroring `_buyer_confidence` — the impact component scores the **magnitude** of the negative impact past the negative cutoff (e.g. `(max_sell_price_impact - sell_price_impact) / impact_scale`, clamped), so a sharper drop earns higher confidence; reuse the same weights/scales.
  - Add `_seller_observations(...)`: e.g. `"Seller aggression increasing"`, `"Price falling on sell prints"` (only when impact is negative), `"Spread stable and narrow"`.
  - The buyer and seller gates are **mutually exclusive** in practice (the aggressive ratios are complementary shares of directional volume and cannot both reach 0.60), but make the control-flow precedence explicit and ensure neither branch can perturb the other; the existing buyer/unclear results MUST be unchanged.
- [ ] **`simulated.py` — add `_seller_control_stream()` (deterministic, seeded), the mirror of `_buyer_control_stream()`, and wire `SIM-SELLER` into `stream()`.**
  - Majority of prints are **aggressive sells** that hit the bid; a minority are aggressive buys. On an aggressive-sell tick (with the same probability the buyer stream uses to lift), the quote **drops one tick** (both bid and ask decrease) so `sell_price_impact` is genuinely **negative** (real downward price progress — this is what separates seller_control from bid_absorption). Hold the spread narrow/stable; reuse the buyer stream's quote size, sizes, and logical `dt`. All randomness from the seeded `random.Random` — same seed ⇒ identical stream.
  - Add `elif self.ticker == "SIM-SELLER": yield from self._seller_control_stream()` (the other three reserved sims still emit nothing this iteration).

### Frontend

- [ ] **None.** Verified already-generic and rose-ready (see BACKGROUND). Do **not** edit `format.ts`, `TapeStatePanel`, `TopBar`, or any component. The browser pass verifies the existing UI renders `seller_control` in rose; it adds no code.

### New user-facing capability
Watching `SIM-SELLER` now produces a real, resolved **seller_control** read (today it would hang at cold-start `unclear`). The user can confirm the system identifies the down-tape with the same fidelity as the up-tape, in the correct (rose) color language.

### New information displayed
No new *value type*. `seller_control` is an already-enumerated value of the existing **Tape state** contract (the tape-state panel already lists all five states); this iteration makes the engine actually emit it. The same per-snapshot `tape_state` / `confidence` / features render — now for a down-tape.

### New user actions
None. (The existing ticker input + Watch button drive it.)

### UI surface changes
None. The single `/` cockpit is structurally unchanged; only the *content* differs (rose seller read instead of green buyer read), via existing components.

### Product surface delta
The cockpit gains its second of five tape states. The product now honestly reads both directional controls (buyer ↔ seller) with consistent, measured color semantics — a visible step toward the five-state classifier.

### Blueprint conformance
**No new surfaces, no re-approval requested.** The single `/` cockpit (the only Information-Architecture home) and its tape-state panel already enumerate `seller_control`. The seller read is produced by the **same canonical owner** named in the Data Contract — `TapeStateClassifier` → engine snapshot → `GET /tape/{ticker}/state`, re-exposed read-only by `/summary` and `WS /stream`. `blueprint.md` is unchanged.

### Data-contract additions
**None.** No new displayed value, computing module, or endpoint. `seller_control` flows through the existing **Tape state + confidence** contract row (one producer: the classifier; one canonical endpoint: `/state`). Do NOT introduce a second producer or a parallel path for the seller state — read it from the same snapshot the buyer state uses.

## OUT OF SCOPE

- **No frontend code changes** — the UI is already generic and rose-ready; do not refactor `format.ts` or any component.
- **Do NOT touch or relax the `buyer_control` gate or its positive-`buy_price_impact` guard.** Add the seller branch alongside it; the existing buyer tests are the regression guard.
- **J-04 / J-05 (bid/ask absorption) are NOT started.** seller_control is *control* — high sell aggression **with** real downward price progress. Absorption is the opposite (high aggression, **no** price progress) and is the next, harder iteration. Building seller_control correctly (with the negative-impact guard) is the prerequisite that makes the absorption distinction meaningful.
- **Stream-status-dot consolidation stays DEFERRED.** Driving the top-bar dot from the engine's canonical `snapshot.stream_status` (instead of the client `connStatus`) is a no-data/teardown concern; it belongs to the J-04/J-05 (no-data) or J-09 (teardown) iteration. Not in scope here. **Not forgotten** — it MUST land before those journeys.
- **No DELETE /watch UI control (J-09), no new panels/routes/values, no other reserved sims driven** (SIM-BIDABS / SIM-ASKABS / SIM-CHOP stay reserved-and-silent).

## DEFINITION OF DONE

- [ ] **J-03 passes via browser-qa-agent** on `SIM-SELLER`: within the warm-up the tape-state panel settles on **seller_control** with confidence ≥ `reasonable_confidence` (0.60); `aggressive_sell_ratio` reads high; `sell_price_impact` reads **negative**; the seller headline state label and the confidence-bar fill compute **rose** (`text-rose-400` → `rgb(251,113,133)`, `bg-rose-500` → `rgb(244,63,94)`), measured by base-selector stylesheet probe + `getComputedStyle` (NOT by eye), explicitly not slate `rgb(226,232,240)`; the event log shows **"Tape state changed to seller_control"**; values update over the WebSocket without a page reload.
- [ ] **Required-still-passing remain green:** J-01 & J-02 (`SIM-BUYER` still settles on buyer_control @ ≥ threshold with the green color layer intact — the new seller branch must not perturb buyer classification) and J-08 (UI ≡ REST exact agreement for the watched ticker).
- [ ] **New deterministic backend tests pass:** SIM-SELLER → seller_control (confidence ≥ threshold, high aggressive_sell_ratio, negative sell_price_impact, "Tape state changed to seller_control" in the log) + determinism (same seed ⇒ identical snapshot) + the **critical seller price-impact guard** unit tests (below). The previously-green buyer/unclear tests still pass unchanged.
- [ ] **No anti-goal violation introduced** — seller_control requires negative sell_price_impact (price impact, not aggression); single source of truth holds (UI/REST/WS read one snapshot, no recomputation); no fabricated data (SIM-SELLER drives real events; unknown tickers still 400, not-watched reads still 404); deterministic (seeded); seller thresholds live in `config.py` (no magic numbers).
- [ ] Full backend suite green (`pytest tests/ -v` — currently 24/24; expect the new seller tests added on top, all passing); frontend `npm run build` clean.
- [ ] Coherence audit PASS (same producer/endpoint for the tape state; no new path for an existing contract value).
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_rich-iter-4-dev.md`.

## TESTING REQUIREMENTS

- **Unit / integration (this is why depth is full — new tests beyond browser smoke):**
  - **`tests/test_classifier.py` — the critical seller mirror guards (anti-goal: price impact, not aggression).** Mirror the existing buyer guards (`test_price_impact_guard_zero_impact_is_not_buyer_control`, `…_negative_impact_…`):
    - `test_seller_control_with_reasonable_confidence` — high `aggressive_sell_ratio` + sufficiently **negative** `sell_price_impact` + stable spread + elevated speed ⇒ `seller_control` @ confidence ≥ `reasonable_confidence`; pin the exact transparent confidence value (mirror of the buyer test's `pytest.approx`).
    - `test_price_impact_guard_zero_impact_is_not_seller_control` — high `aggressive_sell_ratio` but `sell_price_impact = 0.0` ⇒ **NOT** `seller_control` (this is the bid-absorption-in-spirit case: aggression without price progress must not read as control).
    - `test_price_impact_guard_positive_impact_is_not_seller_control` — `sell_price_impact = +0.05` (price actually rose) ⇒ **NOT** `seller_control`.
    - Confirm the existing buyer/unclear tests still pass (the seller branch must not change them — the default `_features()` has `aggressive_sell_ratio=0.10`, which must not trip the seller gate).
  - **`tests/test_scenario.py` — end-to-end through the real engine:**
    - `test_sim_seller_settles_on_seller_control` — run `SimulatedProvider("SIM-SELLER", "seller_control")` through `TapeEngine`; assert `tape_state == seller_control`, `confidence >= reasonable_confidence`, `aggressive_sell_ratio >= min_aggressive_sell_ratio`, `sell_price_impact < 0`, and `"Tape state changed to seller_control" in snapshot.event_log`.
    - `test_sim_seller_is_deterministic` — two runs ⇒ identical snapshot.
    - **Update** `test_reserved_ticker_known_but_unresolved` — SIM-SELLER is now driven, so this assertion must move to a still-reserved ticker (e.g. `SIM-BIDABS`) to keep proving "known sim ticker resolves a provider, and `build_provider('NOPE123') is None` never fabricates one." Do not leave a now-false test.
- **Browser (the real gate for J-03):**
  - **Precondition (iter-1 lesson):** `rm -rf apps/frontend/.next`; restart the managed dev server with `NEXT_PUBLIC_API_URL` set; confirm HTTP 200 before driving. An all-SKIPPED run does not count.
  - **J-03** on `SIM-SELLER`: type `SIM-SELLER`, Watch, wait for the stream to resolve; assert the tape-state panel reads "Seller Control" @ confidence ≥ threshold, `aggressive_sell_ratio` high, `sell_price_impact` negative, and the event log contains "Tape state changed to seller_control", with live WS updates (no reload).
  - **Color verification method (iter-2 + iter-3 lesson — measured, not eyeballed):** `getComputedStyle` on (a) the "Seller Control" headline state label and (b) the confidence-bar fill ⇒ assert rose (`rgb(251,113,133)` / `rgb(244,63,94)`), explicitly not slate `rgb(226,232,240)`; and a `document.styleSheets` **base-selector** probe asserting `.text-rose-400{` and `.bg-rose-500{` resolve to real rules (exclude `hover:`/`focus:` variants). Sanity-check the negative `sell_price_impact` cell computes rose via `impactColor`.
  - **Required-still-passing re-verify:** re-run J-01/J-02 on `SIM-BUYER` (still buyer_control, color layer still green) and J-08 (UI ≡ REST) for the watched ticker — proving the new seller branch did not regress the buyer read or the single-source-of-truth contract.
- **Error cases:** unknown ticker (e.g. `NOPE123`) ⇒ `POST /watch` returns 400 and the UI surfaces the error (no fabricated snapshot); a sell-heavy tape with no downward price progress ⇒ NOT seller_control (covered by the classifier guard tests above; the absorption states that own that case arrive in J-04/J-05).

## NOTES

- **Why full, overriding the iter-3 evaluator's "lean":** the lean recommendation assumed the seller path was already built and unit-proven. Direct codebase inspection (BACKGROUND) shows it is not — this iteration writes the seller classifier branch, its config thresholds, the seller simulator scenario, and the deterministic guard tests. The classifier's **seller price-impact guard is a critical anti-goal surface** (a seller scenario that classifies as seller_control on aggression alone, without negative price impact, is a defect and would also undermine the J-04 bid_absorption distinction), so it warrants full-depth rigor and unit tests beyond browser smoke. The journey **verdict** is unchanged (CONTINUE); only the factual premise behind the depth is corrected. Downstream agents and the next evaluator should note that journey-history/evaluator-log claims of "seller already built/unit-proven" were inaccurate.
- **Symmetry discipline:** implement seller_control as the strict mirror of buyer_control — same structure, same reused scales/weights, negated impact cutoff. This keeps confidence calibrated identically across sides and makes J-04/J-05 (absorption) a clean extension rather than a divergent code path. Avoid a parallel/forked classifier.
- **Forward value:** a correct seller_control with the negative-impact guard is the prerequisite for J-04 (bid_absorption: high sell aggression **without** the price drop ⇒ absorption, not seller_control) and pre-stages J-07 (this iteration produces a real non-buyer "Tape state changed to seller_control" transition).
- **Coherence:** no new value/endpoint/route/nav; `seller_control` rides the existing Tape-state contract row with its one producer (`TapeStateClassifier`) and one canonical endpoint (`/state`). No blueprint edit; no `blueprint.reapproval-requested` written.
