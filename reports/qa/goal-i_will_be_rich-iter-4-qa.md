**Verdict:** PASS

# QA Report — goal-i_will_be_rich-iter-4 (seller_control / J-03)

**Phase:** goal-i_will_be_rich-iter-4
**Date:** 2026-06-03
**Agent:** qa (MODE 2 — validation)
**Frontend Present:** yes (Chrome MCP browser checks executed)
**Services:** backend :8650 (health 200), frontend :3650 (HTTP 200)

## Summary

J-03 verified green end-to-end. Watching `SIM-SELLER` settles the cockpit on
**seller_control** with high `aggressive_sell_ratio`, **negative** `sell_price_impact`,
confidence ≥ `reasonable_confidence`, and the rose color layer rendering by **measured**
`getComputedStyle` + base-selector stylesheet probe (not by eye). Required-still-passing
journeys hold: SIM-BUYER still settles on **buyer_control** in green (J-01/J-02), and
UI ≡ REST exact agreement holds (J-08). The full backend suite is green (31 passed,
+7 new seller tests). No frontend code was changed, as required.

---

## Step 1 — Artifact verification

| Artifact | Status |
|----------|--------|
| `docs/handoffs/goal-i_will_be_rich-iter-4-dev.md` | ✅ present |
| `reports/reviews/goal-i_will_be_rich-iter-4-review.md` | ✅ present, **PASS_WITH_NOTES** |
| `runs/goal-i_will_be_rich-iter-4/status.json` | ✅ present (`review_passed`) |
| `reports/qa/goal-i_will_be_rich-iter-4-test-plan.md` | ✅ present (14 cases, executed below) |

---

## Step 2 — Backend tests (exact output)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Log: `reports/qa/goal-i_will_be_rich-iter-4-test.log`

```
collected 31 items
tests/test_aggressor.py ......                                           [ 19%]
tests/test_api.py .......                                                [ 41%]
tests/test_classifier.py ..........                                      [ 74%]
tests/test_features.py ...                                               [ 83%]
tests/test_scenario.py .....                                             [100%]
============================== 31 passed in 4.32s ==============================
```

Exit code 0. Was 24/24 in iter-3; now **31 passed** (+7 new seller tests: 5 classifier
+ 2 scenario; the reserved-ticker test was *moved* to SIM-BIDABS, not added). All
previously-green buyer/unclear/aggressor/features/api tests pass unchanged.

New seller test functions confirmed present:
- `test_seller_control_with_reasonable_confidence`
- `test_price_impact_guard_zero_impact_is_not_seller_control`
- `test_price_impact_guard_positive_impact_is_not_seller_control`
- `test_wide_spread_blocks_seller_control`
- `test_default_buyer_features_do_not_trip_seller_gate`
- `test_sim_seller_settles_on_seller_control`
- `test_sim_seller_is_deterministic`
- `test_reserved_ticker_known_but_unresolved` — now targets still-reserved `SIM-BIDABS`,
  keeps `build_provider("NOPE123") is None`.

---

## Step 3 — Frontend build (TC-09)

Command: `cd apps/frontend && npm run build` → **exit 0**, `✓ Compiled successfully in 4.4s`,
type-check passed, 4 static pages generated. No frontend code changed (per OUT OF SCOPE).

---

## Step 3.5 / 4 — Functional test plan results

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | Seller-control reaches reasonable confidence | api(unit) | `seller_control` @ conf ≥ 0.60, pinned ≈0.8542 | `test_seller_control_with_reasonable_confidence` passed | **PASS** | part of 31-pass suite |
| TC-02 | Zero impact NOT seller_control (critical guard) | api(unit) | state ≠ seller_control | `test_price_impact_guard_zero_impact_is_not_seller_control` passed | **PASS** | price-impact-not-aggression guard |
| TC-03 | Positive impact NOT seller_control (critical guard) | api(unit) | state ≠ seller_control | `test_price_impact_guard_positive_impact_is_not_seller_control` passed | **PASS** | +0.05 impact rejected |
| TC-04 | Buyer/unclear unchanged (regression) | api(unit) | all buyer/unclear tests pass | full `test_classifier.py` (10) passed | **PASS** | default sell_ratio 0.10 does not trip seller gate (`test_default_buyer_features_do_not_trip_seller_gate`) |
| TC-05 | SIM-SELLER settles seller_control e2e | api(integration) | state/conf/ratio/impact<0/log all hold | `test_sim_seller_settles_on_seller_control` passed | **PASS** | through real TapeEngine |
| TC-06 | SIM-SELLER deterministic | api(integration) | identical snapshots | `test_sim_seller_is_deterministic` passed | **PASS** | seeded |
| TC-07 | Reserved-ticker moved; no fabricated providers | api(integration) | reserved assertion on SIM-BIDABS; NOPE123→None | `test_reserved_ticker_known_but_unresolved` (now SIM-BIDABS) passed | **PASS** | no now-false SIM-SELLER assertion remains |
| TC-08 | Full backend suite green | api | exit 0, 0 failures | 31 passed in 4.32s | **PASS** | |
| TC-09 | Frontend build clean | artifact | build exit 0 | exit 0, compiled, 4 pages | **PASS** | |
| TC-10 | No magic numbers: seller thresholds in config | artifact | config fields; classifier refs config | `min_aggressive_sell_ratio=0.60`, `max_sell_price_impact=-0.02` in config; classifier reads `c.min_aggressive_sell_ratio`/`c.max_sell_price_impact`/`c.ratio_scale`/`c.impact_scale`; no inline seller literals | **PASS** | side-neutral scales reused, not duplicated |
| TC-11 | J-03 browser: SIM-SELLER rose render (primary gate) | browser | seller_control, rose measured, neg impact, WS live | see below | **PASS** | primary gate |
| TC-12 | SIM-BUYER still buyer_control in green (regression) | browser | buyer_control, green, pos impact | see below | **PASS** | seller branch did not perturb buyer |
| TC-13 | UI ≡ REST exact agreement (J-08) | api+browser | identical state/conf | see below | **PASS** | single source of truth |
| TC-14 | Unknown ticker rejected, no fabricated snapshot | api+browser | 400 + UI error, no synth state | see below | **PASS** | |

**14/14 test cases passed.**

---

## Step 4 — Chrome MCP browser checks (executed, not faked)

Precondition met: frontend served HTTP 200 at :3650; backend 200 at :8650. Real Watch
flow driven via Chrome MCP (type ticker → click Watch → await stream resolve). Evidence
screenshots saved under `reports/qa/goal-i_will_be_rich-iter-4-evidence/`.

### TC-11 — SIM-SELLER → seller_control with measured rose (PRIMARY J-03 GATE) — PASS

Typed `SIM-SELLER`, clicked Watch, awaited "Seller Control". Measured readout:

- **Tape state:** "Seller Control"; **Confidence 0.875** (≥ 0.60). ✅
- **Aggressive sell ratio:** 0.933 (high); **Buy ratio:** 0.067. ✅
- **Sell price impact:** −0.380 (negative). ✅
- **Event log:** "Tape state changed to seller_control". ✅
- **Observations:** "Seller aggression increasing", "Price falling on sell prints",
  "Spread stable and narrow". ✅
- **Recent trades** dominated by SELL prints at descending prices (95.5x → 95.4x). ✅
- **Color (measured by `getComputedStyle`):**
  - Headline "Seller Control" → `rgb(251, 113, 133)` = rose-400 ✅ (explicitly **not** slate `rgb(226,232,240)`)
  - Confidence-bar fill (`h-2 ... bg-rose-500`) → `rgb(244, 63, 94)` = rose-500 ✅
  - Sell-price-impact value cell → `rgb(251, 113, 133)` = rose via `impactColor` ✅
- **Base-selector stylesheet probe:** `.text-rose-400` ✅ and `.bg-rose-500` ✅ both resolve
  to real CSS rules in the served bundle (exact selector match, hover/focus variants excluded).
- **Live WS update (no reload):** across captures on the same page, bid moved 95.49 → 94.88
  and sell_price_impact −0.380 → −0.420 → −0.500 with no navigation/reload. ✅

Evidence: `TC-11-sim-seller-seller-control.png`

### TC-12 — SIM-BUYER re-verify (J-01/J-02 regression) — PASS

Reloaded, typed `SIM-BUYER`, Watch, awaited "Buyer Control":

- **Tape state:** "Buyer Control"; **Confidence 0.883** (≥ 0.60). ✅
- **Aggressive buy ratio:** 0.946; **Buy price impact:** +0.400 (positive). ✅
- **Event log:** "Tape state changed to buyer_control". ✅
- **Color (measured):** headline → `rgb(52, 211, 153)` = emerald-400 (green); confidence-bar
  fill → `rgb(16, 185, 129)` = emerald-500. Base selectors `.text-emerald-400` and
  `.bg-emerald-500` resolve. ✅ Green layer intact — **not** perturbed to rose/slate by the
  new seller branch.

Evidence: `TC-12-sim-buyer-buyer-control.png`

### TC-13 — UI ≡ REST exact agreement (J-08) — PASS

With SIM-SELLER stabilized in the UI, compared UI readout to REST near-simultaneously:

- UI: state "Seller Control", **Confidence 0.848**.
- REST `GET /tape/SIM-SELLER/state`: `tape_state="seller_control"`, `confidence=0.8476259…`.
- State matches exactly; confidence matches to display precision (0.8476 → **0.848** @ 3dp).
  One engine value per metric; no recomputation/divergence. ✅

### TC-14 — Unknown ticker rejected, no fabricated snapshot — PASS

- API: `POST /watch/NOPE123` → **400** (verified via curl). Not-watched read
  `GET /tape/SIM-ASKABS/state` → **404** (no synthesized snapshot). ✅
- UI: watching an unknown ticker surfaced the explicit error
  *"'…' is not a known simulated ticker"* and rendered **"No ticker watched"** with **no**
  TAPE STATE / confidence / features — i.e. **no fabricated snapshot**. ✅

---

## Step 4b — UI Evolution Audit

1. **Did the UI evolve to reflect the new capability?** Yes — the existing cockpit now
   renders a real `seller_control` read (previously SIM-SELLER hung at cold-start `unclear`).
   No new code was required or added (spec mandated none); the already-generic, rose-ready
   components now display the engine's seller emission.
2. **Can the user see/understand/control it?** Yes — typing `SIM-SELLER` + Watch produces a
   correctly-colored (rose) "Seller Control" read with confidence, negative sell impact, the
   seller observations, and the transition in the event log, updating live over WS.
3. **Relying on old generic pages?** No — `seller_control` is an already-enumerated value of
   the existing Tape-state contract; it renders through the canonical tape-state panel.
4. **Technically complete but under-exposed?** No — the capability is fully visible and
   measured rose-rendered on the live surface.

**Verdict:** UI-PASS

---

## Anti-goal compliance

- **Price impact, not aggression:** seller_control requires `sell_price_impact ≤ −0.02`;
  zero/positive-impact guard tests (TC-02/TC-03) pass — aggression alone does not read as
  control. ✅
- **Single source of truth:** UI ≡ REST exact (TC-13); one producer/endpoint. ✅
- **No fabricated data:** unknown ticker → 400 + UI error, not-watched → 404, no synth
  snapshot (TC-14). ✅
- **Honest uncertainty:** seller gate emits `unclear` below `reasonable_confidence`. ✅
- **No magic numbers:** seller thresholds in `config.py`; classifier reads config (TC-10). ✅
- **Deterministic:** seeded stream determinism test passes (TC-06). ✅

---

## Blockers

None.

---

## Verdict

All 14 functional test cases pass; full backend suite green (31 passed); frontend build
clean; primary J-03 browser gate verified with measured rose color; required-still-passing
journeys (J-01/J-02 buyer-green, J-08 UI≡REST) re-verified green; UI-PASS; no anti-goal
violations.

**Verdict:** PASS
