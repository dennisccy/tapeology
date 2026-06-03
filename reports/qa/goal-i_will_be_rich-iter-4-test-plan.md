# goal-i_will_be_rich-iter-4 Functional Test Plan

**Phase:** goal-i_will_be_rich-iter-4
**Date:** 2026-06-03
**Frontend Present:** yes

## Phase Goal

Build the `seller_control` classifier path so watching `SIM-SELLER` deterministically
settles the cockpit on **seller_control** (high `aggressive_sell_ratio`, **negative**
`sell_price_impact`, confidence ≥ `reasonable_confidence`, rose color render, and a
"Tape state changed to seller_control" log entry) — promoting **J-03 failing → passing**
while J-01/J-02 (buyer) and J-08 (single source of truth) stay green. Net-new backend
work only; no frontend code changes.

---

## Test Cases

### TC-01 — Seller-control classifier reaches reasonable confidence (anti-goal: price impact)

**Type:** api (pytest unit)
**Preconditions:** seller branch added to `classifier.py`; seller thresholds in `config.py`.

**Steps:**
1. Run `cd apps/backend && pytest tests/test_classifier.py::test_seller_control_with_reasonable_confidence -v`.
2. Feed features: high `aggressive_sell_ratio`, sufficiently **negative** `sell_price_impact`, stable spread, elevated `trade_speed`.

**Expected outcome:** Classifier returns `seller_control` with confidence ≥ `reasonable_confidence` (0.60), and a pinned transparent confidence value (mirror of the buyer test's `pytest.approx`; symmetric input ⇒ `≈0.8542`).
**Pass criteria:** Test passes; `state == "seller_control"`, confidence ≥ 0.60 and matches the pinned `pytest.approx` value.

---

### TC-02 — Seller price-impact guard: zero impact is NOT seller_control (critical anti-goal)

**Type:** api (pytest unit)
**Preconditions:** seller gate enforces `sell_price_impact <= max_sell_price_impact` (negative cutoff).

**Steps:**
1. Run `pytest tests/test_classifier.py::test_price_impact_guard_zero_impact_is_not_seller_control -v`.
2. Feed high `aggressive_sell_ratio` but `sell_price_impact = 0.0`.

**Expected outcome:** State is NOT `seller_control` (aggression without price progress must not read as control — this is the bid-absorption-in-spirit case).
**Pass criteria:** Test passes; returned state `!= "seller_control"` (stays `unclear`).

---

### TC-03 — Seller price-impact guard: positive impact is NOT seller_control (critical anti-goal)

**Type:** api (pytest unit)
**Preconditions:** as TC-02.

**Steps:**
1. Run `pytest tests/test_classifier.py::test_price_impact_guard_positive_impact_is_not_seller_control -v`.
2. Feed high `aggressive_sell_ratio` but `sell_price_impact = +0.05` (price actually rose).

**Expected outcome:** State is NOT `seller_control`.
**Pass criteria:** Test passes; returned state `!= "seller_control"`.

---

### TC-04 — Buyer/unclear classification unchanged (regression guard)

**Type:** api (pytest unit)
**Preconditions:** existing buyer tests present; default `_features()` has `aggressive_sell_ratio = 0.10`.

**Steps:**
1. Run `pytest tests/test_classifier.py -v` (full classifier suite).

**Expected outcome:** All pre-existing buyer_control and unclear tests pass unchanged; the new seller branch does not trip on default features and does not perturb buyer results.
**Pass criteria:** No previously-green classifier test regresses; full file passes.

---

### TC-05 — SIM-SELLER settles on seller_control end-to-end through the engine

**Type:** api (pytest integration)
**Preconditions:** `_seller_control_stream()` added; `SIM-SELLER` wired into `SimulatedProvider.stream()`.

**Steps:**
1. Run `pytest tests/test_scenario.py::test_sim_seller_settles_on_seller_control -v`.
2. Drive `SimulatedProvider("SIM-SELLER", "seller_control")` through `TapeEngine`.

**Expected outcome:** `tape_state == "seller_control"`; `confidence >= reasonable_confidence`; `aggressive_sell_ratio >= min_aggressive_sell_ratio`; `sell_price_impact < 0`; `"Tape state changed to seller_control" in snapshot.event_log`.
**Pass criteria:** Test passes asserting all five conditions above.

---

### TC-06 — SIM-SELLER stream is deterministic (anti-goal: deterministic & reproducible)

**Type:** api (pytest integration)
**Preconditions:** seller stream uses the seeded `random.Random` only.

**Steps:**
1. Run `pytest tests/test_scenario.py::test_sim_seller_is_deterministic -v`.
2. Run the SIM-SELLER scenario twice with the same seed; compare snapshots.

**Expected outcome:** Two runs produce identical features, state, and confidence.
**Pass criteria:** Test passes; snapshots are byte-identical across runs.

---

### TC-07 — Reserved-ticker test moved to a still-silent sim; no fabricated providers

**Type:** api (pytest integration)
**Preconditions:** `test_reserved_ticker_known_but_unresolved` updated (SIM-SELLER is now driven).

**Steps:**
1. Run `pytest tests/test_scenario.py -v`.
2. Confirm the reserved-but-unresolved assertion now targets a still-reserved sim (e.g. `SIM-BIDABS`) and that `build_provider("NOPE123") is None`.

**Expected outcome:** SIM-SELLER no longer asserted as unresolved; a still-silent sim proves the reserved-but-unresolved contract; unknown tickers never fabricate a provider.
**Pass criteria:** Test passes; no now-false assertion against SIM-SELLER remains; `build_provider("NOPE123") is None` holds.

---

### TC-08 — Full backend suite green

**Type:** api (pytest)
**Preconditions:** all backend changes complete.

**Steps:**
1. Run `cd apps/backend && pytest tests/ -v`.

**Expected outcome:** Previously 24/24; now 24 + new seller tests, all passing.
**Pass criteria:** Exit code 0; zero failures/errors; new seller tests counted in the pass total.

---

### TC-09 — Frontend build clean (no frontend code changed)

**Type:** artifact (build)
**Preconditions:** no frontend edits per OUT OF SCOPE.

**Steps:**
1. Run `cd apps/frontend && npm run build`.

**Expected outcome:** Build completes with no errors.
**Pass criteria:** Build exits 0; no compile/type errors.

---

### TC-10 — No magic numbers: seller thresholds live in config

**Type:** artifact
**Preconditions:** `config.py` updated.

**Steps:**
1. Verify `config.py` defines `min_aggressive_sell_ratio` (0.60) and `max_sell_price_impact` (negative, e.g. -0.02).
2. Verify `classifier.py` references these config fields and contains no inline threshold literals for the seller gate.
3. Verify side-neutral scales/weights are reused (no duplicated per-side copies).

**Expected outcome:** All seller cutoffs sourced from config; symmetric scales shared with the buyer gate.
**Pass criteria:** Config fields present; no seller-threshold literal in `classifier.py`/engine code; no duplicated scale constants.

---

### TC-11 — J-03 browser: SIM-SELLER renders seller_control with measured rose color (primary gate)

**Type:** browser
**Preconditions:** `rm -rf apps/frontend/.next`; managed dev server restarted with `NEXT_PUBLIC_API_URL` set; `GET /` (frontend, e.g. :3650) returns HTTP 200; backend (e.g. :8650) up. An all-SKIPPED run does NOT count.

**Steps:**
1. Navigate to `/`.
2. Type `SIM-SELLER` into the ticker input; click Watch.
3. Wait for the stream to connect and the warm-up to resolve.
4. Read the tape-state panel, confidence bar, `aggressive_sell_ratio`, `sell_price_impact`, and event log.
5. Run `getComputedStyle` on (a) the "Seller Control" headline state label and (b) the confidence-bar fill.
6. Run a `document.styleSheets` base-selector probe for `.text-rose-400{` and `.bg-rose-500{` (exclude `hover:`/`focus:` variants).

**Expected outcome:** Tape-state panel reads "Seller Control" @ confidence ≥ 0.60; `aggressive_sell_ratio` high; `sell_price_impact` negative; event log contains "Tape state changed to seller_control"; values update over WS without reload. Headline computes rose `rgb(251,113,133)`, confidence-bar fill computes rose `rgb(244,63,94)` — explicitly NOT slate `rgb(226,232,240)`; both base selectors resolve to real CSS rules.
**Pass criteria:** All read values match; both computed colors equal the rose RGBs (not slate); both base-selector probes find real rules; negative `sell_price_impact` cell computes rose via `impactColor`; live WS update observed with no page reload.

---

### TC-12 — J-01/J-02 re-verify: SIM-BUYER still buyer_control in green (regression)

**Type:** browser
**Preconditions:** as TC-11 (server up, .next cleared).

**Steps:**
1. Navigate to `/`; type `SIM-BUYER`; Watch.
2. Wait for resolve; read tape-state panel, confidence, `aggressive_buy_ratio`, `buy_price_impact`.
3. Measure headline + confidence-bar color via `getComputedStyle`.

**Expected outcome:** Settles on **buyer_control** @ confidence ≥ 0.60; `aggressive_buy_ratio` high; `buy_price_impact` positive; event log shows "Tape state changed to buyer_control"; color layer still green (not slate, not rose).
**Pass criteria:** State == buyer_control; values correct; computed colors are the buyer green (not perturbed by the seller branch).

---

### TC-13 — J-08 re-verify: UI ≡ REST exact agreement (single source of truth)

**Type:** api + browser
**Preconditions:** SIM-SELLER (or SIM-BUYER) watched and stabilized in the UI.

**Steps:**
1. With the ticker stabilized in the UI, note tape state, confidence, and key feature values shown.
2. `curl -s http://localhost:8650/tape/SIM-SELLER/state` and `curl -s http://localhost:8650/tape/SIM-SELLER/features`.
3. Compare REST values to the UI readouts.

**Expected outcome:** REST `state`/`confidence` exactly match the UI; `…/features` values exactly match the UI feature readouts — one engine value per metric, no recomputation/divergence.
**Pass criteria:** Every compared value is identical between REST and UI (exact match, not approximate).

---

### TC-14 — Error case: unknown ticker is rejected, no fabricated snapshot

**Type:** api + browser
**Preconditions:** server up.

**Steps:**
1. `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8650/watch/NOPE123` → expect 400.
2. In the UI, type `NOPE123`, click Watch.

**Expected outcome:** `POST /watch/NOPE123` returns 400; UI surfaces an error and does NOT render a fabricated tape state/snapshot.
**Pass criteria:** HTTP 400 from the API; UI shows an explicit error state with no synthesized state/confidence/features.

---

## Summary

Total test cases: 14
- API tests (pytest unit/integration + REST): 9 (TC-01–TC-08, plus REST portion of TC-13/TC-14)
- Browser tests: 4 (TC-11, TC-12, TC-13, TC-14 — UI portions)
- Artifact checks: 2 (TC-09 build, TC-10 config/no-magic-numbers)

**Critical anti-goal coverage:** TC-02 & TC-03 (price impact, not aggression — seller guard), TC-06 (deterministic), TC-07 & TC-14 (no fabricated data), TC-10 (no magic numbers), TC-13 (single source of truth), TC-01 (honest uncertainty via reasonable-confidence gate).
**Primary J-03 gate:** TC-11 (measured rose render). **Regression guards:** TC-04, TC-08, TC-12, TC-13.
