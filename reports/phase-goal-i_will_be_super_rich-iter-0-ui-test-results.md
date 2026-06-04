# Goal iter-0 (baseline) — UI Test Results

**Phase:** goal-i_will_be_super_rich-iter-0 (baseline / verify-only)
**Date:** 2026-06-04
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!--
Rationale: Target journeys for this baseline are J-01 – J-15. The simulated half
(J-01 – J-09) all PASS. The real-data half (J-10 – J-15) are NOT IMPLEMENTED — the
must-have (P1) journeys do not pass, so by the verdict rule ("FAIL: any happy-path/P1
test fails") the overall verdict is FAIL. This is the EXPECTED baseline outcome, not a
regression: it records the green floor (9/15) and the work to build (6/15). The
goal-evaluator — not this report — assigns the per-journey already_passing / to-build
classification per the iter-0 spec.
-->

**Overall:** 9/15 journeys passed · 6/15 failed (not implemented) · 0 skipped

- **Simulated half (J-01 – J-09): 9/9 PASS** — the green floor the real-data work must not regress.
- **Real-data half (J-10 – J-15): 0/6** — surfaces not built (expected at baseline). Recorded as
  not-implemented / not-runnable, never as pass.

**Environment was fully testable:** frontend up (HTTP 200), backend up (`/health` 200), Chrome MCP available. Nothing was SKIPPED for environment reasons.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Watch a ticker & see the live cockpit | smoke / happy-path | P1 | All panels render live values; spread = ask−bid; features numeric; updates over WS | SIM-BUYER: bid 101.96 / ask 101.98 / spread 0.02 / last 101.98; trades w/ price·size·side; all features numeric; observations (3) + event log present; status dot **Live** (WS) | **PASS** | `UT-J-01-J-02-SIM-BUYER.png` |
| UT-J-02 | Buyer-control scenario identified | happy-path | P1 | State settles **buyer_control**, conf ≥ threshold; agg_buy_ratio high, buy_price_impact +; event-log transition | State **Buyer Control**, conf 0.883; agg_buy_ratio 0.946, buy_price_impact +0.430; "Tape state changed to buyer_control" | **PASS** | `UT-J-01-J-02-SIM-BUYER.png` |
| UT-J-03 | Seller-control scenario identified | happy-path | P1 | State settles **seller_control**, conf ≥ threshold; agg_sell_ratio high, sell_price_impact −; event-log transition | State **Seller Control**, conf 0.881; agg_sell_ratio 0.943, sell_price_impact −0.440, net_agg_vol −14000; "Tape state changed to seller_control" | **PASS** | `UT-J-03-SIM-SELLER.png` |
| UT-J-04 | Bid absorption detected (price impact, not aggression) | happy-path | P1 | High agg **sell** but price not lower → **bid_absorption** (not seller_control); absorption/bid_refresh elevated; absorption msg | agg_sell_ratio **1.000** yet last **flat 100.00**, sell_price_impact **0.000** → **Bid Absorption**, conf 0.917; absorption_score 1.000, bid_refresh_score 1.000; "Large sell print absorbed", "Bid refreshing at 100.00" | **PASS** | `UT-J-04-SIM-BIDABS.png` |
| UT-J-05 | Ask absorption detected (price impact, not aggression) | happy-path | P1 | High agg **buy** but price not higher → **ask_absorption** (not buyer_control); absorption/ask_refresh elevated; absorption msg | agg_buy_ratio **1.000** yet last **flat 100.02**, buy_price_impact **0.000** → **Ask Absorption**, conf 0.917; absorption_score 1.000, ask_refresh_score 1.000; "Large buy print absorbed", "Ask refreshing at 100.02" | **PASS** | `UT-J-05-SIM-ASKABS.png` |
| UT-J-06 | Choppy tape reported as unclear | happy-path | P1 | State **unclear**, low confidence; no directional call | State **Unclear**, conf **0.200**; agg_buy 0.500 / agg_sell 0.500, net_agg_vol 0, wide spread 0.18 (vs 0.02); "Mixed or weak evidence — no clear side in control" | **PASS** | `UT-J-06-SIM-CHOP.png` |
| UT-J-07 | Transitions announced in event log & observations | happy-path | P1 | Cold-start warm-up → resolved state logs "Tape state changed to …"; observations reflect evidence; appended over WS | Every scenario from cold start logged "Tape state changed to <state>"; observations are scenario-specific & live (e.g. "Buyer aggression increasing", "Large sell print absorbed", "Bid refreshing at 100.00") | **PASS** | event logs in `UT-J-01..05` PNGs |
| UT-J-08 | REST & live UI agree (single source of truth) | happy-path | P1 | REST state/confidence/features exactly match the UI for the same ticker | Same-tick capture: **ui_conf 0.855 == rest_conf 0.855**; UI "Buyer Control" == REST `buyer_control`; stream `live`; stable features (trade_speed 2.0, absorption 0.0, bid_refresh 1.0) match exactly | **PASS** | `UT-J-01-J-02-SIM-BUYER.png` + inline eval capture (below) |
| UT-J-09 | Stop watching a ticker | happy-path | P1 | Stop → stream closes, cockpit idle; re-watch starts fresh | Stop → "No ticker watched" / "Idle"; backend `GET /tape/SIM-CHOP/state` → **404** (torn down); re-watch repopulated a fresh cockpit | **PASS** | `UT-J-09-stopped-idle.png` |
| UT-J-10 | Choose a data source (Live / Historical / Simulated) | happy-path | P1 | Selector offers 3 modes, each revealing mode-specific controls | **Not implemented** — no selector. DOM: `select_count 0`, `radio_count 0`; only input = ticker text box, only button = Watch; no "Historical/Simulated/Source" text | **FAIL (not implemented)** | `UT-J-10-no-datasource-selector.png` |
| UT-J-11 | Replay a real historical session | happy-path | P1 | Historical mode fetches real window, replays through engine; cockpit populates with real values | **Not implemented** — no Historical mode, no date/time-window picker (`date_input_count 0`), no replay-speed control; backend ignores `{mode:historical,…}` body and returns 400; no historical provider | **FAIL (not implemented)** | `UT-J-10-…png` + backend probe (below) |
| UT-J-12 | Stream a real live ticker | happy-path (UI controls browser-checkable) | P1 | Live mode + market-status indicator render; (real socket = gated) | **Not implemented** — no Live mode selector, no market-status indicator; `GET /market/clock` → 404; backend ignores `{mode:live}` body (400). The green "Live" dot is the **sim** stream-status, not a live-vendor mode | **FAIL (not implemented)** | `UT-J-10-…png` + backend probe (below) |
| UT-J-13 | Find a symbol by search | happy-path | P1 | Search returns tradable symbols (symbol + name); selecting fills the ticker | **Not implemented** — no search box (only a plain ticker text input); `GET /symbols/search?q=AAPL` → **404** | **FAIL (not implemented)** | `UT-J-10-…png` + backend probe (below) |
| UT-J-14 | Real-data edge cases handled honestly (no fabricated data) | happy-path (no-cred / unknown / closed are browser-checkable) | P1 | Distinct explicit states: "provider unavailable" / "not a tradable symbol" / "no data for window" / "market closed" — never a cockpit | **Not implemented** as real-data honesty. Unknown symbol AAPL → sim-scoped **"'AAPL' is not a known simulated ticker"** (400); UI shows the error and **does NOT fabricate a cockpit** (anti-goal respected), but the four distinct real-data states do not exist; no `/market/clock` | **FAIL (not implemented)** | `UT-J-14-unknown-symbol-honest-error.png` + backend probe (below) |
| UT-J-15 | A live-feed gap shows `stale`, then recovers | gated / operator (UI status browser-checkable) | P1 | Live status flips to `stale` on a feed gap, back to `live` on resume; no fabricated trades in the gap | **Not implemented** — no Live mode / live provider / real socket to gap. Engine exposes a `stream_status` field (read `live` for the sim stream) but there is no live-vendor feed whose lull could be exercised | **FAIL (not implemented)** | n/a (no live surface to drive) |

---

## Passed Tests

### UT-J-01 — Watch a ticker and see the live tape cockpit
**Verdict:** PASS · **Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-0-evidence/UT-J-01-J-02-SIM-BUYER.png`
- Watched `SIM-BUYER` from the home `/` cockpit; stream connected (status dot → **Live**) and every panel populated live without a page reload.
- **Quote:** Bid 101.96 / Ask 101.98 / **Spread 0.02 (= ask − bid)** / Last 101.98 — all numeric.
- **Recent trades:** list of trades each with price · size · side (e.g. 101.98 / 300 / BUY).
- **Features (30s):** trade_speed 2.00/s, aggressive_buy_ratio 0.946, aggressive_sell_ratio 0.054, net_aggressive_volume 14900, buy_price_impact 0.430, sell_price_impact −0.140 — all show numbers.
- **Tape state** panel shows one of the five states with a **confidence** (0.883); **observations** (3) and **event log** each show ≥1 message.

### UT-J-02 — Buyer-control scenario is identified
**Verdict:** PASS · **Evidence:** `…/UT-J-01-J-02-SIM-BUYER.png`
- State settled on **Buyer Control** (`buyer_control`), confidence **0.883** (well above a "reasonable" threshold).
- aggressive_buy_ratio reads high (0.946); buy_price_impact reads positive (+0.430).
- Event log contains **"Tape state changed to buyer_control"**.

### UT-J-03 — Seller-control scenario is identified
**Verdict:** PASS · **Evidence:** `…/UT-J-03-SIM-SELLER.png`
- State settled on **Seller Control** (`seller_control`), confidence **0.881**.
- aggressive_sell_ratio high (0.943); sell_price_impact negative (−0.440); net_aggressive_volume −14000.
- Event log: **"Tape state changed to seller_control"**; observations: "Seller aggression increasing", "Price falling on sell prints".

### UT-J-04 — Bid absorption detected (the defining price-impact case)
**Verdict:** PASS · **Evidence:** `…/UT-J-04-SIM-BIDABS.png`
- Despite **maximum** aggressive-sell pressure (aggressive_sell_ratio **1.000**, net_aggressive_volume −17900), the **last price held flat at 100.00** (all recent trades at 100.00) and **sell_price_impact = 0.000**.
- Therefore classified **Bid Absorption** (NOT seller_control), confidence **0.917**.
- absorption_score **1.000**, bid_refresh_score **1.000**.
- Event log: **"Bid refreshing at 100.00"**, **"Large sell print absorbed"**, "Tape state changed to bid_absorption"; observations: "Heavy sell volume being absorbed", "Price holding despite sell prints".
- This directly validates the *price-impact-over-raw-aggression* anti-goal.

### UT-J-05 — Ask absorption detected (mirror price-impact case)
**Verdict:** PASS · **Evidence:** `…/UT-J-05-SIM-ASKABS.png`
- Despite **maximum** aggressive-buy pressure (aggressive_buy_ratio **1.000**, net_aggressive_volume +17400), the **last price stalled flat at 100.02** and **buy_price_impact = 0.000**.
- Therefore classified **Ask Absorption** (NOT buyer_control), confidence **0.917**.
- absorption_score **1.000**, ask_refresh_score **1.000**.
- Event log: **"Ask refreshing at 100.02"**, **"Large buy print absorbed"**, "Tape state changed to ask_absorption".

### UT-J-06 — Choppy tape reported as unclear
**Verdict:** PASS · **Evidence:** `…/UT-J-06-SIM-CHOP.png`
- State **Unclear** with **low confidence 0.200**.
- Mixed/weak evidence: aggressive_buy_ratio 0.500 / aggressive_sell_ratio 0.500, net_aggressive_volume 0, **wide spread 0.18** (vs 0.02 in clean scenarios), no clean price impact.
- Observation: "Mixed or weak evidence — no clear side in control". The UI does **not** assert buyer or seller control — honest uncertainty respected.

### UT-J-07 — Tape-state transitions are announced
**Verdict:** PASS · **Evidence:** event logs visible in `UT-J-01..05` PNGs
- Each scenario, watched from a cold start, recorded a **"Tape state changed to <state>"** line in the event log at the warm-up→resolved transition.
- The observations list carried scenario-specific, live evidence (e.g. "Buyer aggression increasing", "Seller aggression increasing", "Large sell print absorbed", "Bid refreshing at 100.00"), appended over the WebSocket.
- (For `SIM-CHOP`, no transition message appears — correct, because the tape never leaves `unclear`; the observation list still reflects the mixed-evidence read.)

### UT-J-08 — REST and the live UI agree (single source of truth)
**Verdict:** PASS · **Evidence:** `…/UT-J-01-J-02-SIM-BUYER.png` + same-tick eval capture
- A near-atomic capture from the page context (read the rendered DOM confidence and fetch `GET /tape/SIM-BUYER/state` in the same execution) produced:
  `ui_conf=0.855  ui_buyerlabel=true  rest_state=buyer_control  rest_conf=0.855  rest_stream=live`
  → **UI confidence 0.855 == REST confidence 0.855 exactly**, UI "Buyer Control" == REST `buyer_control`, stream `live`.
- A separate `…/features` read matched the UI on the stable metrics exactly (trade_speed 2.0, absorption_score 0.0, bid_refresh_score 1.0). The only differences in continuously-varying metrics across non-simultaneous reads were pure capture-latency drift on a live 2-trades/s stream — there is one engine value per metric, read identically by REST, WS, and the UI.

### UT-J-09 — Stop watching a ticker
**Verdict:** PASS · **Evidence:** `…/UT-J-09-stopped-idle.png`
- Clicking **Stop** returned the cockpit to the idle empty state ("No ticker watched", status "Idle") with no further updates.
- Backend teardown confirmed: `GET /tape/SIM-CHOP/state` → **404 "Ticker 'SIM-CHOP' is not being watched"** (this also exercises the honest not-watched 404 error path).
- Re-watching the same ticker started a fresh read (cockpit repopulated, Stop button returned).

---

## Failed Tests (real-data half — not implemented; expected at baseline)

> These six are the actual work of this session. Their surfaces do not exist in the
> current code, so they are recorded as **not implemented / not runnable** — never as
> pass and never as a regression. Credential gating is *not* the cause: the surfaces
> themselves are absent.

### UT-J-10 — Choose a data source (Live / Historical / Simulated)
**Verdict:** FAIL (not implemented)
**Failure:** No data-source selector exists. Structural DOM probe of the home screen: `select_count 0`, `radio_count 0`, `date_input_count 0`; the only `<input>` is the ticker text box (`"Ticker e.g. SIM-BUYER"`) and the only `<button>` is "Watch". No "Live / Historical / Simulated", "Source", "Market", or "replay/speed" text anywhere.
**Evidence:** `…/UT-J-10-no-datasource-selector.png`

### UT-J-11 — Replay a real historical session
**Verdict:** FAIL (not implemented)
**Failure:** No Historical mode, no date/time-window picker, no replay-speed control. Backend has no historical provider — `POST /watch/AAPL` with `{"mode":"historical","start":…,"end":…,"speed":10}` is treated as a sim watch and returns **400 "'AAPL' is not a known simulated ticker"** (the `mode` body is ignored).
**Evidence:** `…/UT-J-10-no-datasource-selector.png` + backend probe (below)

### UT-J-12 — Stream a real live ticker
**Verdict:** FAIL (not implemented)
**Failure:** No Live mode selector and no market-status indicator. `GET /market/clock` → **404**. `POST /watch/AAPL {"mode":"live"}` → **400** (mode ignored, no live provider). The green **"Live"** dot seen in J-01–J-08 is the *simulated* stream's status, not a real-vendor live mode.
**Evidence:** `…/UT-J-10-no-datasource-selector.png` + backend probe (below)

### UT-J-13 — Find a symbol by search
**Verdict:** FAIL (not implemented)
**Failure:** No symbol-search box (only a free-text ticker input). `GET /symbols/search?q=AAPL` → **404**.
**Evidence:** `…/UT-J-10-no-datasource-selector.png` + backend probe (below)

### UT-J-14 — Real-data edge cases handled honestly (no fabricated data)
**Verdict:** FAIL (not implemented)
**Failure:** The four distinct real-data honest states required by J-14 ("real-data provider unavailable", "not a tradable symbol", "no data for that window", "market is closed" + next open) do not exist, because the real modes are unbuilt. What exists today: an unknown symbol (AAPL) yields the **sim-scoped** error **"'AAPL' is not a known simulated ticker"** (HTTP 400), and the UI surfaces that error and stays at "No ticker watched".
**Important (anti-goal held):** the system does **NOT fabricate** a cockpit/tape for the unknown symbol — it errors honestly and renders no fake data. So the "no fabricated data" anti-goal is respected today; only the *specific real-data honesty states* are absent (to build).
**Evidence:** `…/UT-J-14-unknown-symbol-honest-error.png` + backend probe (below)

### UT-J-15 — A live-feed gap shows `stale`, then recovers
**Verdict:** FAIL (not implemented)
**Failure:** No Live mode / live provider / real socket exists, so a feed gap cannot be exercised. The engine does expose a `stream_status` field (observed `live` for the sim stream), which is the seam a future live feeder would flip to `stale`; but there is no real-vendor feed to lull/recover at baseline.
**Evidence:** n/a (no live surface to drive). Confirmed structurally via the absent Live mode (UT-J-10/J-12).

---

## Skipped Tests

None. The frontend and backend were both running and Chrome MCP was available; every target journey was exercised.

---

## Backend probe log (supporting evidence for J-10 – J-14)

```
# Available routes (OpenAPI) — simulated half only
GET     /health
GET     /tape/{ticker}/events
GET     /tape/{ticker}/features
GET     /tape/{ticker}/state
GET     /tape/{ticker}/summary
POST    /watch/{ticker}
DELETE  /watch/{ticker}
# Absent real-data endpoints
GET /symbols/search?q=AAPL   -> 404   (J-13)
GET /market/clock            -> 404   (J-12, J-14)

# mode body is not supported (no real providers) — J-11, J-12, J-14
POST /watch/AAPL  (empty body)                 -> 400 "'AAPL' is not a known simulated ticker"
POST /watch/AAPL  {"mode":"live"}              -> 400 "'AAPL' is not a known simulated ticker"
POST /watch/AAPL  {"mode":"historical",...}    -> 400 "'AAPL' is not a known simulated ticker"

# Honest error paths still hold (sim half)
GET /tape/SIM-CHOP/state  (after Stop / not watched) -> 404 "Ticker 'SIM-CHOP' is not being watched"
```

---

## Minor observations (non-blocking, not journey failures)

- **Switching tickers via Watch does not stop the previous backend watch.** After watching SIM-BUYER → SIM-SELLER → SIM-BIDABS → SIM-ASKABS by re-submitting in the UI, all four remained watched on the backend (each `…/state` → 200); only the explicit **Stop** button tore a watch down (SIM-CHOP → 404). The UI correctly shows one ticker at a time, so this does not affect any journey acceptance, but orphaned engine instances can accumulate when a user switches without stopping. Flagged for the team. (All test watches were cleaned up via `DELETE /watch/*` at the end of the run.)
- The same-tick J-08 verification was done via in-page `eval` because this Chrome-MCP build does not surface `eval` return values or `console.log` to the operator; the value was injected into the DOM and read back via `extract`. No impact on results.

---

## Environment

- **Frontend URL:** http://localhost:3650  (HTTP 200)
- **Backend URL:** http://localhost:8650  (`/health` 200; `NEXT_PUBLIC_API_URL=http://localhost:8650`)
- **Browser:** Chrome via superpowers-chrome MCP (`use_browser`)
- **Viewport:** 1440 × 1100
- **Test Date:** 2026-06-04
- **Evidence directory:** `reports/qa/goal-i_will_be_super_rich-iter-0-evidence/`
- **Reserved sim tickers exercised:** SIM-BUYER, SIM-SELLER, SIM-BIDABS, SIM-ASKABS, SIM-CHOP
