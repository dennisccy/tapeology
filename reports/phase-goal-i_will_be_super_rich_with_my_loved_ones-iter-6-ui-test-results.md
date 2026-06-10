# Goal Mode Iter-6 — UI Test Results

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-6
**Date:** 2026-06-11
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

**Overall:** 13/16 tests passed (0 skipped, 3 failed)

Failures: J-46 (target — fmf confirms at buyer_control not bid_absorption due to inverted taxonomy in running server), J-41 (required-still-passing — direction-awareness stmt shows "met" on adverse SIM-SELLER tape), J-46-stmt (related to J-46 — stmt1 params `ask_absorption` instead of `bid_absorption` for long).

Root cause for all failures: uvicorn process started at 22:07 June 10; iter-6 code fixes written to disk at 23:15 without server restart. Old broken code runs in memory.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| J-40-A | Absorption-reversal: pending during bid_absorption | target | P1 | PENDING, tape=bid_absorption, stmt2=not_yet | PENDING, tape=Bid Absorption conf=0.950, stmt1=met/stmt2=not_yet, source=bid_absorption, Paused | PASS | UT-J-40-A-pending-bid-absorption.png |
| J-40-B | Absorption-reversal: confirming after buyer_control flip | target | P1 | CONFIRMING, tape=buyer_control, source=reversal_absorption_then_buyer | CONFIRMING, tape=Buyer Control conf=0.801, evidence "buyers took control with real upward impact (buy_price_impact +0.3700)", source=reversal_absorption_then_buyer, Paused | PASS | UT-J-40-B-confirming-paused.png |
| J-42 | trend_continuation/long on SIM-BUYER: confirming, no-flapping | target | P1 | CONFIRMING, both stmts met, tape=buyer_control | CONFIRMING, tape=Buyer Control conf=0.936, stmt1=met/stmt2=met, evidence "buyers keep pressing price up (buy_price_impact +0.4200)", Paused | PASS | UT-J-42-confirming-buyer-control.png |
| J-43 | SIM-SHIFT: confirming → weakening amber after chop shift | target | P1 | WEAKENING (amber chip), tape=unclear/chop | WEAKENING, tape=Unclear conf=0.200, evidence "control faded", stmt2=violated, amber chip rendered, Paused | PASS | UT-J-43-weakening-amber.png |
| J-45-A | level_break/long: pending pre-cross (Moment A) | target | P1 | PENDING pre-cross, last < level | PENDING, level=100.30, last=100.18 < level, tape=Buyer Control, Paused | PASS | UT-J-45-A-pending-pre-cross.png |
| J-45-B | level_break/long: confirming post-cross (Moment B) | target | P1 | CONFIRMING post-cross, last > level | CONFIRMING, level=100.30, last=100.33, evidence "Price broke above level at 100.30", Paused | PASS | UT-J-45-B-confirming-post-cross.png |
| J-46 | failed_move_fade/long on SIM-REVERSAL: confirming DURING bid_absorption | target | P1 | CONFIRMING while tape=bid_absorption (ts 19.5–60.5), stmt1=met (bid_absorption detected) | CONFIRMING fires at ts=82.5 tape=**buyer_control** (NOT bid_absorption). Journal: stmt1 params `states: ["ask_absorption"]` (inverted — should be `bid_absorption` for long). Server runs pre-iter-6 code. | FAIL | UT-J-46-fail-confirming-at-buyer-control.png |
| J-38 | Declare thesis: PENDING with statement display, REST=WS parity | required | P1 | ACTIVE thesis on SIM-BIDABS, PENDING, stmts rendered, no reload needed | PENDING, tape=Bid Absorption conf=0.950, stmt1=met/stmt2=not_yet, source=bid_absorption, Paused. REST /research/thesis/active?ticker=SIM-BIDABS returns verbatim thesis data matching WS frame | PASS | UT-J-38-pending-bid-absorption.png |
| J-39 | Thesis creation validation (no silent coercion) | required | P1 | unwatched→404, wrong-side→422, missing level→422, level on non-level→422, duplicate→409 | All 5 sub-cases verified via API: 404 "Ticker 'NOTREAL' is not being watched"; 422 "a long thesis's invalidation must be below the current last price"; 422 "setup 'level_break' requires a level_price"; 422 "setup 'absorption_reversal' does not take a level_price"; 409 "an active thesis already exists for 'SIM-BUYER'" | PASS | UT-J-39-thesis-active.png |
| J-41 | trend_continuation/long on SIM-SELLER: rejecting + direction-awareness | required | P1 | REJECTING, stmt "Price keeps making progress" shows **violated** (direction-aware: sell_price_impact negative = adverse for long) | REJECTING verdict correct; but stmt2 "Price keeps making progress in your direction rather than stalling" shows **met** (WRONG — old server evaluates `buy_price_impact > 0` direction-naively; buy_price_impact=+0.16 on SIM-SELLER triggers "met" even though sell_price_impact=-0.37) | FAIL | UT-J-41-rejecting-direction-defect.png |
| J-44 | Invalidation on hard trigger (SIM-SELLER) | required | P1 | thesis invalidated when price breaks below invalidation_price | INVALIDATED at ts=87.5. Evidence: "3 consecutive prints printed through your invalidation at 99.20 (last 99.20); the thesis is invalidated." Strip shows "THESIS INVALIDATED — RESOLVED" | PASS | UT-J-44-invalidated.png |
| J-01 | Watch a ticker and see the live tape cockpit | required | P1 | all panels render live values | Buyer Control cockpit: bid/ask/spread/last numeric, spread=ask-bid verified (0.02), recent trades price/size/side, trade_speed/aggressive_buy_ratio/sell_ratio/net_vol/buy_impact/sell_impact all numeric, tape-state Buyer Control conf=0.945, observations "Buyer aggression increasing", event log "Tape state changed to buyer_control" | PASS | UT-J01-J02-J07-J17-buyer-cockpit.png |
| J-02 | Buyer-control scenario identified | required | P1 | tape_state=buyer_control, high buy_ratio, positive buy_impact, event log "Tape state changed to buyer_control" | tape=Buyer Control conf=0.945, aggressive_buy_ratio=0.937, buy_price_impact=+0.440, event log "Tape state changed to buyer_control" | PASS | UT-J01-J02-J07-J17-buyer-cockpit.png |
| J-04 | Bid absorption detected (price-impact, not aggression) | required | P1 | tape=bid_absorption despite high aggressive_sell; absorption_score/bid_refresh elevated | tape=Bid Absorption conf=0.950, aggressive_sell_ratio=1.000 but sell_price_impact=0.000, absorption_score=1.000, bid_refresh_score=1.000, event log "Large sell print absorbed" + "Bid refreshing at 100.00" | PASS | UT-J04-bid-absorption.png |
| J-06 | Unclear/choppy tape reported as unclear | required | P1 | tape=unclear, low confidence, no directional assertion | tape=Unclear conf=0.200, aggressive_buy=0.500/sell=0.500, net_agg_vol=0, spread=0.12 (wide), observation "Mixed or weak evidence — no clear side in control" | PASS | UT-J06-unclear-chop.png |
| J-07 | Tape-state transitions announced in event log | required | P1 | event log shows "Tape state changed to …" on transition | Event log "Tape state changed to buyer_control" visible in J-02 cockpit screenshot | PASS | UT-J01-J02-J07-J17-buyer-cockpit.png |
| J-17 | Price chart with tape-state markers on simulated data | required | P1 | candlestick chart renders, bar-size selector re-renders candles, markers present | PRICE CHART section with 10s/30s/60s bar selector rendered; 30s selector clicked and chart re-rendered; SIM-BUYER trends up, event log confirms buyer_control markers | PASS | UT-J17-chart-30s-buyer.png |
| J-68 | Idle strip with no thesis = single declare affordance | required | P1 | single "Declare thesis" affordance, no duplicate buttons | "Declare thesis" button visible as sole affordance when no thesis active | PASS | UT-J-68-idle.png |

---

## Passed Tests

### J-40-A — Absorption-reversal: PENDING during bid_absorption
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-6-evidence/UT-J-40-A-pending-bid-absorption.png`
- SIM-REVERSAL paused during bid_absorption phase at ts=19.5
- Thesis declared via API with invalidation=99.0
- Strip shows: PENDING, tape=Bid Absorption conf=0.950, last=100.00, stmt1=met/stmt2=not_yet, source=bid_absorption

### J-40-B — Absorption-reversal: CONFIRMING after buyer_control flip
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-6-evidence/UT-J-40-B-confirming-paused.png`
- Streamed past bid_absorption into buyer_control phase; paused when verdict=confirming (ts=~82.5)
- Strip shows: CONFIRMING, tape=Buyer Control conf=0.801, both stmts met, evidence "buyers took control with real upward impact (buy_price_impact +0.3700)", source=reversal_absorption_then_buyer
- Verdict source descriptor correctly uses SIM-REVERSAL's two-phase identity

### J-42 — trend_continuation/long on SIM-BUYER: confirming, no-flapping
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-6-evidence/UT-J-42-confirming-buyer-control.png`
- Thesis declared on SIM-BUYER (already in buyer_control), paused when confirming
- Strip: CONFIRMING conf=0.936, stmt1=met/stmt2=met, evidence "buyers keep pressing price up (buy_price_impact +0.4200)"
- No flapping observed: verdict stayed CONFIRMING throughout buyer_control phase

### J-43 — SIM-SHIFT: confirming → weakening amber after chop shift
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-6-evidence/UT-J-43-weakening-amber.png`
- SIM-SHIFT streams buyer_control (stmt1=met/stmt2=met → CONFIRMING), then transitions to unclear/chop
- After chop phase: strip shows WEAKENING (amber chip), tape=Unclear conf=0.200, stmt2=violated, evidence "control faded"
- First test to render the amber WEAKENING chip

### J-45-A — level_break/long: PENDING pre-cross
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-6-evidence/UT-J-45-A-pending-pre-cross.png`
- SIM-REVERSAL paused at ts=20.0 (bid_absorption), level_break/long declared with level=100.30
- last=100.18 < level=100.30, tape=Buyer Control — strip shows PENDING

### J-45-B — level_break/long: CONFIRMING post-cross
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-6-evidence/UT-J-45-B-confirming-post-cross.png`
- Stream resumed; paused when verdict=confirming (ts=32.5)
- last=100.33 > level=100.30, evidence "Price broke above level at 100.30"
- Verdict latched to CONFIRMING at exact price-cross

### J-38 — Declare thesis: PENDING strip with REST/WS parity
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-6-evidence/UT-J-38-pending-bid-absorption.png`
- Thesis declared via API on SIM-BIDABS while stream paused in bid_absorption
- Browser cockpit shows PENDING strip with stmt1=met/stmt2=not_yet, source=bid_absorption
- REST GET /research/thesis/active?ticker=SIM-BIDABS returns verbatim thesis data
- No page reload required — thesis appeared over WebSocket

### J-39 — Thesis creation validated (no silent coercion)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-6-evidence/UT-J-39-thesis-active.png`
- All 5 validation sub-cases pass:
  1. Unwatched ticker (NOTREAL) → HTTP 404 "Ticker 'NOTREAL' is not being watched"
  2. Long thesis, invalidation above last (102.00 > 101.35) → HTTP 422 "a long thesis's invalidation must be below the current last price"
  3. level_break without level_price → HTTP 422 "setup 'level_break' requires a level_price"
  4. absorption_reversal with level_price → HTTP 422 "setup 'absorption_reversal' does not take a level_price"
  5. Second thesis on same ticker → HTTP 409 "an active thesis already exists for 'SIM-BUYER'"

### J-44 — Invalidation on hard trigger
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-6-evidence/UT-J-44-invalidated.png`
- trend_continuation/long declared on SIM-SELLER with invalidation=99.20 (below last=99.44)
- SIM-SELLER's downward price action drove last to 99.20; verdict → INVALIDATED at ts=87.5
- Strip: "INVALIDATED", evidence "3 consecutive prints printed through your invalidation at 99.20 (last 99.20); the thesis is invalidated."
- Status=invalidated, strip shows "THESIS INVALIDATED — RESOLVED" banner

### J-01, J-02, J-04, J-06, J-07, J-17, J-68 — Regression spot-checks
**Verdict:** PASS (all)
- J-01: Full cockpit with all panels live on SIM-BUYER (bid/ask/spread/last numeric, spread=ask-bid, trades, features, tape-state, observations, event log)
- J-02: tape=Buyer Control conf=0.945, aggressive_buy_ratio=0.937, buy_price_impact=+0.440
- J-04: tape=Bid Absorption conf=0.950 on SIM-BIDABS despite aggressive_sell=1.000; sell_price_impact=0.000; absorption_score=1.000
- J-06: tape=Unclear conf=0.200 on SIM-CHOP, buy/sell ratio=0.500, no directional assertion
- J-07: event log "Tape state changed to buyer_control" visible
- J-17: price chart with bar-size selector (10s/30s/60s) renders and re-renders candles on click
- J-68: single "Declare thesis" affordance on cockpit with no active thesis

---

## Failed Tests

### J-46 — failed_move_fade/long on SIM-REVERSAL: FAIL
**Verdict:** FAIL
**Failure:** Verdict fires CONFIRMING at tape=buyer_control (ts=82.5), not during bid_absorption as the spec requires. Statement 1 params in journal show `"states": ["ask_absorption"]` (inverted — should be `"bid_absorption"` for long direction). Statement 2 params show `"states": ["seller_control"]` (should be `"buyer_control"` for long).
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-6-evidence/UT-J-46-fail-confirming-at-buyer-control.png`

**Journal evidence (thesis bff5cff3c6154a65aee8332e9edeb866):**
```
ts=19.5: verdict=pending, tape=bid_absorption (correct declaration)
ts=82.5: verdict=confirming, tape=buyer_control (WRONG — spec requires confirming during bid_absorption)
```
Statement 1 stored params: `{"states": ["ask_absorption"]}` (old code — should be `bid_absorption` for long)
Statement 2 stored params: `{"states": ["seller_control"]}` (old code — should be `buyer_control` for long)

**Expected:** Thesis CONFIRMING while tape=bid_absorption, statement 1 "met" when bid_absorption is detected (i.e., the failed move is being absorbed at the bid), confirming the fade thesis
**Actual:** CONFIRMING fires only after tape transitions to buyer_control; statement 1 remains not_yet throughout bid_absorption because it checks for ask_absorption (wrong side for long)

**Root cause:** Server process (PID 323687) started at 22:07 June 10. Iter-6 fixes to `verdict.py` (line 340) and `taxonomy.py` (line 132) were written to disk at 23:15 but server was not restarted. Old code in memory has `fade_absorption = "ask_absorption"` for long (inverted).

---

### J-41 — trend_continuation/long on SIM-SELLER: direction-awareness FAIL
**Verdict:** FAIL
**Failure:** Verdict correctly shows REJECTING, but statement 2 "Price keeps making progress in your direction rather than stalling" shows **met** (should show **violated**). Old server code uses `buy_price_impact > 0` direction-naively; buy_price_impact=+0.16 on SIM-SELLER triggers "met" even though sell_price_impact=-0.37 (adverse for long). Iter-6 fix in `monitor.py` checks adverse side first (sell_impact <= max for long = violated) but that code is not running.
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-6-evidence/UT-J-41-rejecting-direction-defect.png`

**Steps taken:**
1. Started SIM-SELLER watch, waited for warm seller_control state
2. Declared trend_continuation/long with invalidation below current last
3. Polled for REJECTING verdict; paused and captured screenshot

**Expected:** verdict=REJECTING, stmt2 "Price keeps making progress in your direction rather than stalling" shows **violated** (direction-aware: sell_price_impact=-0.37 is adverse for long)
**Actual:** verdict=REJECTING (correct), but stmt2 shows **met** (direction-naive evaluation using buy_price_impact=+0.16 > 0 = "met")

**Root cause:** Same as J-46 — server not restarted after iter-6 code changes. `monitor.py` `_evaluate_statement` direction-awareness fix (lines 71-98) not in memory.

---

## Skipped Tests

None — all mandated journeys were executed.

---

## Journey Matrix Diff

Iter-6 spec mandated:
- **Target journeys (new):** J-40 ✓, J-42 ✓, J-43 ✓, J-45 ✓, J-46 FAIL, (J-46 includes two moments)
- **Required-still-passing:** J-38 ✓, J-39 ✓, J-41 FAIL, J-44 ✓, J-01 ✓, J-02 ✓, J-04 ✓, J-06 ✓, J-07 ✓, J-17 ✓, J-68 ✓

All 16 mandated test legs executed. No journeys silently dropped.

---

## Environment

- **Frontend URL:** http://localhost:3650
- **Backend URL:** http://localhost:8650
- **Browser:** Chrome via MCP (Chrome DevTools Protocol)
- **Test Date:** 2026-06-11
- **Evidence directory:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-6-evidence/`
- **Server note:** uvicorn process started 2026-06-10 22:07; iter-6 code patches applied to disk at 23:15 without server restart — old code runs in memory for all J-41/J-46 failures
