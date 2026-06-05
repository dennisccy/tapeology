# goal-i_will_be_super_rich-iter-5 Functional Test Plan

**Phase:** goal-i_will_be_super_rich-iter-5  
**Date:** 2026-06-05  
**Frontend Present:** no

## Phase Goal

Extend the aggressor classification in the tape engine to apply a **two-stage rule**: (1) quote rule unchanged and taking precedence, then (2) Lee-Ready tick-test fallback when no quote is in effect or the print lands strictly mid-spread; resolve the large majority of prints to buy/sell on real data while preserving the one honest-undecidable case (no quote **and** no prior trade) as `unknown`.

## Test Cases

### TC-01 — Quote rule at-or-through: price >= ask resolves to BUY

**Type:** api  
**Preconditions:** Aggressor classifier with two-stage rule implemented; test fixture with a trade at price 100.50 when quote has ask=100.50.

**Steps:**
1. Prepare a trade at price=100.50 with quote bid=100.00, ask=100.50 in effect at the trade timestamp
2. Call `classify_aggressor(trade, quote, prior_trade_price=None, last_tick_dir=None)`

**Expected outcome:** Returns `Side.BUY` — quote rule fires because price is at-or-above the ask.  
**Pass criteria:** Function returns `Side.BUY` for the trade; no fallback to tick test is needed.

---

### TC-02 — Quote rule at-or-through: price <= bid resolves to SELL

**Type:** api  
**Preconditions:** Aggressor classifier with two-stage rule; test fixture with trade at price 99.50 when bid=99.50.

**Steps:**
1. Prepare a trade at price=99.50 with quote bid=99.50, ask=100.00 in effect
2. Call `classify_aggressor(trade, quote, prior_trade_price=None, last_tick_dir=None)`

**Expected outcome:** Returns `Side.SELL` — quote rule fires because price is at-or-below the bid.  
**Pass criteria:** Function returns `Side.SELL` for the trade.

---

### TC-03 — No quote, uptick: tick test resolves to BUY

**Type:** api  
**Preconditions:** Aggressor classifier with tick-test fallback; trade arrives with no quote in effect; prior trade price available.

**Steps:**
1. Prepare a trade at price=100.25 with quote=None (no quote in effect)
2. Set prior_trade_price=100.00 (uptick case: 100.25 > 100.00)
3. Call `classify_aggressor(trade, quote=None, prior_trade_price=100.00, last_tick_dir=None)`

**Expected outcome:** Tick test fires and returns `Side.BUY` for the uptick.  
**Pass criteria:** Function returns `Side.BUY`; classification did not rely on a quote.

---

### TC-04 — No quote, downtick: tick test resolves to SELL

**Type:** api  
**Preconditions:** Aggressor classifier with tick-test fallback; no quote in effect; prior trade price available.

**Steps:**
1. Prepare a trade at price=99.75 with quote=None
2. Set prior_trade_price=100.00 (downtick case: 99.75 < 100.00)
3. Call `classify_aggressor(trade, quote=None, prior_trade_price=100.00, last_tick_dir=None)`

**Expected outcome:** Tick test fires and returns `Side.SELL` for the downtick.  
**Pass criteria:** Function returns `Side.SELL`; classification did not rely on a quote.

---

### TC-05 — No quote, zero-tick, last direction BUY: carries direction

**Type:** api  
**Preconditions:** Aggressor classifier; zero-tick scenario; a prior non-zero tick direction has been carried.

**Steps:**
1. Prepare a trade at price=100.00 with quote=None
2. Set prior_trade_price=100.00 (zero-tick: same price)
3. Set last_tick_dir=Side.BUY (the engine has carried a BUY direction from earlier)
4. Call `classify_aggressor(trade, quote=None, prior_trade_price=100.00, last_tick_dir=Side.BUY)`

**Expected outcome:** Tick test fires, zero-tick condition matches, and carried direction `Side.BUY` is returned.  
**Pass criteria:** Function returns `Side.BUY` via the carried direction.

---

### TC-06 — Strictly mid-spread + uptick: tick-test fallback resolves to BUY

**Type:** api  
**Preconditions:** Aggressor classifier; quote is in effect but trade is strictly between bid and ask; tick test applies.

**Steps:**
1. Prepare a trade at price=100.25 with quote bid=100.00, ask=100.50 (mid-spread: 100.00 < 100.25 < 100.50)
2. Set prior_trade_price=100.00 (uptick: 100.25 > 100.00)
3. Call `classify_aggressor(trade, quote, prior_trade_price=100.00, last_tick_dir=None)`

**Expected outcome:** Quote rule does not decide (price is strictly between bid/ask); tick test fires on uptick and returns `Side.BUY`.  
**Pass criteria:** Function returns `Side.BUY` via the tick-test fallback.

---

### TC-07 — Strictly mid-spread + downtick: tick-test fallback resolves to SELL

**Type:** api  
**Preconditions:** Aggressor classifier; quote in effect; trade strictly mid-spread; prior trade price shows downtick.

**Steps:**
1. Prepare a trade at price=100.25 with quote bid=100.00, ask=100.50 (mid-spread)
2. Set prior_trade_price=100.50 (downtick: 100.25 < 100.50)
3. Call `classify_aggressor(trade, quote, prior_trade_price=100.50, last_tick_dir=None)`

**Expected outcome:** Tick test fires on downtick and returns `Side.SELL`.  
**Pass criteria:** Function returns `Side.SELL` via the tick-test fallback.

---

### TC-08 — No quote AND no prior trade: honest UNKNOWN (fabrication guard)

**Type:** api  
**Preconditions:** Aggressor classifier; neither a quote in effect nor a prior trade exists.

**Steps:**
1. Prepare a trade at price=100.50 with quote=None
2. Set prior_trade_price=None (no prior trade exists)
3. Call `classify_aggressor(trade, quote=None, prior_trade_price=None, last_tick_dir=None)`

**Expected outcome:** Both quote rule and tick test cannot decide; returns `Side.UNKNOWN` — the one honest-undecidable case.  
**Pass criteria:** Function returns `Side.UNKNOWN`; no guess or fabrication occurs.

---

### TC-09 — Zero-tick before any non-zero direction exists: UNKNOWN

**Type:** api  
**Preconditions:** Aggressor classifier; zero-tick print; no prior trade exists; no carried direction (fresh watch).

**Steps:**
1. Prepare a trade at price=100.50 with quote=None
2. Set prior_trade_price=100.50 (zero-tick: same price)
3. Set last_tick_dir=None (no direction carried yet; fresh watch)
4. Call `classify_aggressor(trade, quote=None, prior_trade_price=100.50, last_tick_dir=None)`

**Expected outcome:** Zero-tick with no direction to carry returns `Side.UNKNOWN`.  
**Pass criteria:** Function returns `Side.UNKNOWN`; the first print in a fresh watch that matches price stays undecidable.

---

### TC-10 — Quote rule precedence: quote-rule classification is not overridden by tick test

**Type:** api  
**Preconditions:** Aggressor classifier; both quote rule and tick test are applicable, but quote rule wins.

**Steps:**
1. Prepare a trade at price=100.50 with quote bid=100.00, ask=100.50 (at ask)
2. Set prior_trade_price=99.50 (which would be an uptick, suggesting BUY via tick test)
3. Call `classify_aggressor(trade, quote, prior_trade_price=99.50, last_tick_dir=None)`

**Expected outcome:** Quote rule fires first (price >= ask) and returns `Side.BUY`; tick test does not override.  
**Pass criteria:** Function returns `Side.BUY` via quote rule; quote-rule precedence is enforced.

---

### TC-11 — Recent-trades side matches FeatureEngine side: single source of truth

**Type:** artifact  
**Preconditions:** Engine processes a trade through both the classifier and FeatureEngine; both store the computed side.

**Steps:**
1. Replay a fixture (or run a simulated scenario) through the engine
2. Collect all trades from `recent_trades` snapshot
3. Collect the count of aggressive buys and sells recorded by `FeatureEngine.add_trade()`
4. For each trade, verify its `side` in `recent_trades` matches the side counted by FeatureEngine

**Expected outcome:** Every trade's displayed side in `recent_trades` equals the side recorded in the feature engine count.  
**Pass criteria:** Zero mismatches between `recent_trades` side and FeatureEngine-counted side for all trades in the replay.

---

### TC-12 — Real-data fidelity: Ford fixture unknown fraction is below stated bound and strictly lower than quote-only rule

**Type:** api  
**Preconditions:** Committed Ford fixture (`F_20260602_150000_20260602_150200.json`) with 65 trades and 1772 quotes; both quote-only and two-stage classifiers available.

**Steps:**
1. Replay the Ford fixture through the engine with the two-stage classifier (quote rule + tick test)
2. Count the number of trades classified as `UNKNOWN`
3. Compute the `unknown_fraction = unknown_count / total_trades`
4. Replay the same fixture with a quote-only classifier (no tick test)
5. Compute the quote-only `unknown_fraction_baseline`
6. Compare the two fractions

**Expected outcome:** Two-stage `unknown_fraction` is strictly lower than `unknown_fraction_baseline` and below a stated bound (e.g., ≤ 0.15 for a liquid symbol).  
**Pass criteria:** `unknown_fraction < unknown_fraction_baseline` AND `unknown_fraction <= 0.15`.

---

### TC-13 — Determinism: identical event stream yields identical sides and features

**Type:** api  
**Preconditions:** A fixture or ordered event stream that can be replayed twice.

**Steps:**
1. Replay the same event stream through the engine a first time
2. Collect the `recent_trades` list and extract all sides; compute `aggressive_buy_ratio`, `aggressive_sell_ratio`, `net_aggressive_volume` at the final window snapshot
3. Reset the engine to a clean state
4. Replay the same event stream a second time
5. Collect the `recent_trades` list and features again
6. Compare both runs

**Expected outcome:** Sides for each trade are identical in both runs; `aggressive_buy_ratio`, `aggressive_sell_ratio`, and `net_aggressive_volume` are numerically identical.  
**Pass criteria:** Zero divergence in `recent_trades` sides; features match exactly (no floating-point noise) across replays.

---

### TC-14 — No fabricated data: empty stream produces no fabricated sides

**Type:** api  
**Preconditions:** A watch is started but no events are sent to the engine.

**Steps:**
1. Create an engine instance for a ticker
2. Do not feed any TradeEvent or QuoteEvent
3. Query the `recent_trades` snapshot

**Expected outcome:** `recent_trades` is empty; no fabricated trades appear.  
**Pass criteria:** `recent_trades` list is empty (length == 0).

---

### TC-15 — Quote rule precedence regression: SIM-BUYER → buyer_control still resolves at threshold confidence

**Type:** api  
**Preconditions:** Aggressor classifier two-stage rule implemented; SIM-BUYER simulated scenario fixture.

**Steps:**
1. Replay the SIM-BUYER scenario through the engine with the two-stage classifier
2. Let the tape stabilize within the warm-up window
3. Read the final tape state and confidence score

**Expected outcome:** Tape state is `buyer_control` with confidence >= configured threshold (e.g., 0.60).  
**Pass criteria:** State == `buyer_control` AND confidence >= threshold; no regression from the quote-rule-only implementation.

---

### TC-16 — Quote rule precedence regression: SIM-BIDABS → bid_absorption still protects absorption detection

**Type:** api  
**Preconditions:** Aggressor classifier; SIM-BIDABS scenario fixture.

**Steps:**
1. Replay the SIM-BIDABS scenario through the engine with the two-stage classifier
2. Let the tape stabilize
3. Read the final tape state and absorption_score / bid_refresh_score

**Expected outcome:** Tape state is `bid_absorption` (not `seller_control`), confidence >= threshold; absorption_score and bid_refresh_score are elevated.  
**Pass criteria:** State == `bid_absorption` AND confidence >= threshold; price-impact distinction is preserved.

---

### TC-17 — REST endpoint returns resolved side in recent-trades events

**Type:** api  
**Preconditions:** Engine populated with trades; backend running; recent-trades endpoint live.

**Steps:**
1. Start the backend server
2. Begin watching a ticker (SIM-BUYER or a real fixture via test harness)
3. Allow the engine to process several trades
4. Query `GET /tape/{ticker}/events` over REST
5. Inspect the response JSON for the `recent_trades` array

**Expected outcome:** Each trade in the JSON array has a `side` field set to `BUY`, `SELL`, or `UNKNOWN` (not null or missing).  
**Pass criteria:** All trades have a `side` field; the field value is one of the three valid sides.

---

### TC-18 — WebSocket stream delivers resolved sides

**Type:** api  
**Preconditions:** Backend running; WebSocket stream connected; trades being processed.

**Steps:**
1. Start the backend server and begin watching a ticker
2. Connect a WebSocket client to `WS /tape/{ticker}/stream`
3. Allow the engine to process several trades over the stream
4. Capture the JSON messages for recent-trades updates

**Expected outcome:** Each recent-trades message in the WebSocket stream includes trades with `side` field populated.  
**Pass criteria:** All streamed trades have a non-null `side` field; values match the REST endpoint for the same window.

---

### TC-19 — Backend suite: test count strictly increases

**Type:** artifact  
**Preconditions:** Full backend test suite run before and after the implementation.

**Steps:**
1. Run the backend test suite: `pytest apps/backend/tests/ -v --tb=short` (before implementation baseline)
2. Implement the two-stage classifier and new tests (TC-01 through TC-14 above)
3. Run the full suite again
4. Compare test counts

**Expected outcome:** Test count after implementation is strictly higher than baseline; all existing tests pass; no tests are deleted.  
**Pass criteria:** `new_test_count > baseline_test_count` AND exit code == 0.

---

### TC-20 — Backend suite: all tests green, exit 0

**Type:** api  
**Preconditions:** Implementation complete; all test cases and existing suite ready.

**Steps:**
1. Run the full backend test suite: `pytest apps/backend/tests/ -v --tb=short 2>&1`
2. Capture the exit code and final line (e.g. "128 passed, 1 skipped in 10.23s")

**Expected outcome:** Exit code is 0; summary line shows all tests passed (no failures, no errors).  
**Pass criteria:** Exit code == 0 AND summary includes "passed" with no "failed" or "error".

---

## Summary

**Total test cases:** 20  
**API tests:** 17 (TC-01 through TC-10, TC-12, TC-13, TC-14, TC-17, TC-18, TC-20)  
**Artifact checks:** 3 (TC-11, TC-19, and overall suite health)  

**Coverage:**
- Quote rule precedence (TC-01, TC-02, TC-10)
- Tick-test fallback: no quote (TC-03, TC-04, TC-05), mid-spread (TC-06, TC-07)
- Honest undecidable cases: no quote + no prior trade (TC-08), zero-tick before direction (TC-09)
- Real-data fidelity: Ford fixture unknown reduction (TC-12), determinism (TC-13), no fabrication (TC-14)
- Single source of truth: recent_trades ↔ FeatureEngine agreement (TC-11)
- Regression protection: SIM-BUYER / SIM-BIDABS absorption preservation (TC-15, TC-16)
- REST + WebSocket delivery (TC-17, TC-18)
- Suite health: test count strictly increases, all green (TC-19, TC-20)
