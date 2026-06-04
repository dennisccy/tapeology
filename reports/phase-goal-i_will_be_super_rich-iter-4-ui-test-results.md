# Phase goal-i_will_be_super_rich-iter-4 — UI Test Results

**Phase:** goal-i_will_be_super_rich-iter-4
**Date:** 2026-06-04
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->

**Overall:** 9/11 tests passed, 0 failed, 2 skipped (gated/not-exercisable on the current backend state)

**All P1 tests passed** (UT-01, UT-02, UT-03, UT-07, UT-08, UT-10). The 2 SKIPs (UT-05, UT-06) are
P2 cases that cannot be exercised against *this* running backend (credentials present + market
open) and are covered hermetically by the functional suite — they are **not** failures.

The headline new behavior was directly observed on the **real Alpaca live socket** during open
market hours: a Live watch of **F** streamed real trades + quotes with the status reading **`live`**
(emerald) and the source label **`live F`** (J-12), and a quiet feed (ZZZQQ) honestly flipped to
**`stale`** (amber) while **fabricating zero trades** (J-15). The sim and historical regression
paths render unchanged.

---

## ⚠️ Test environment note — concurrent agent on a shared Chrome (read first)

This run executed against a **single shared headless Chrome** (`--remote-debugging-port=9222`,
profile `superpowers-chrome`) that a **second, concurrent QA agent for the same phase was actively
driving in real time**. Evidence this was happening, not a guess:

- A full **`live ZZZQQ`** watch cockpit appeared in the tab after I only reloaded → clicked *Live*
  → screenshotted (I never typed ZZZQQ or clicked Watch).
- Between my own `navigate` and my next action, the tab's mode flipped to **Historical** with
  foreign-set fields (symbol `F`, date `2030-01-05`, `10:00–10:02`). Switching mode requires a real
  React interaction — i.e. another driver, not browser autofill.
- The shared evidence directory contains **`TC-*` screenshots I did not author** (timestamps
  16:01–16:12, mid-run), produced by that concurrent same-phase QA agent.

**Mitigation applied so the results are trustworthy:** I worked in a **dedicated tab** and treated
the **authoritative backend on `:8650` (exclusively mine; the other session uses `:8835`) as the
source of truth** — every state-changing UI action was immediately cross-checked with a `curl`
against `:8650` (`/tape/<SYM>/summary`, `/watch/<SYM>/state`), and React inputs were set/cleared
with native setters to defeat stale foreign field values. Where a clean window was obtained, the
browser render and the backend agreed exactly (see evidence). I did **not** close the peer's tab or
restart the managed services (would sabotage the parallel run). The intermittent interference cost
extra attempts but did not prevent clean, corroborated verification of every P1 flow.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Home screen loads with mode controls | smoke | P1 | Page renders; TopBar + status dot + sim/historical/live selector; no error overlay | Idle home rendered: Tapeology TopBar, mode selector (Live/Historical/**Simulated**), Ticker input, grey **Idle** dot, "No ticker watched" body. No error overlay. | **PASS** | `UT-01-result.png` |
| UT-02 | Live watch mounts cockpit (live dot) | happy-path | P1 | Cockpit mounts; no error banner; dot **emerald** `live`; label `scenario: live F`; backend live | **Real Alpaca socket**: `stream_status=live`, `scenario="live F"`, real bid/ask **15.41/15.42**, live trades streaming (15.38×718 SELL…, count 0→13+). UI: Watching F, **emerald** dot (`bg-emerald-400`), label `scenario: live F`, cockpit mounted, no error banner. | **PASS** | `UT-02-live-F-emerald.png` |
| UT-03 | Live mode reveals search + market indicator | smoke | P1 | Symbol search input visible; `MarketStatusIndicator` renders a status; no error overlay | Live mode reveals **Symbol search** input + market indicator reading **`market open`** (title "The US market is open"). No error overlay. | **PASS** | `UT-03-11-live-controls-idle.png` |
| UT-04 | Symbol search filters & fills | happy-path | P2 | Matching symbols appear (e.g. AAPL); selecting fills the box; no crash on a valid prefix | Search returned real matches: `AAP*` → **AAPL — "Apple Inc. Common Stock"** (+ AAPB/AAPD/AAPU/AAPW…); `F` → **Ford Motor Company** (+ F.PRB/F.PRC…). Box filled with the picked ticker; watch proceeded. | **PASS** | `UT-08-historical-aapl.png` (AAPL dropdown), `UT-02-live-F-emerald.png` (F dropdown) |
| UT-05 | Live + no creds → provider unavailable | error | P2 | Cockpit not mounted; honest `provider_unavailable`; `POST` 503 | **Not exercisable:** this backend has Alpaca credentials configured (`/market/clock` → `available:true`). The no-credentials path cannot be produced without reconfiguring the harness-managed backend. Covered hermetically by the functional suite (`provider_unavailable` 503) and the `ProviderUnavailable` panel exists in `app/page.tsx`. | **SKIP** | n/a (env: creds present) |
| UT-06 | Live + market closed → market closed | error | P2 | Cockpit not mounted; honest `market_closed` + next open; `POST` 409 | **Not exercisable:** the US market is **open** now (`/market/clock` → `is_open:true`, next_close `2026-06-04T20:00:00Z`). The closed-market path cannot be produced live. Covered hermetically (`market_closed` 409 + `next_open`; iter-3 verified the gate with a `FakeAdapter`). | **SKIP** | n/a (env: market open) |
| UT-07 | Sim SIM-BUYER → buyer_control | regression | P1 | Cockpit mounts; tape state `buyer_control`; confidence bar populated | UI shows tape state **"Buyer Control"**, confidence **0.893** (full bar), populated QUOTE (103.03/103.05), FEATURES (aggr. buy ratio 0.963), RECENT TRADES (BUY prints), EVENT LOG "Tape state changed to buyer_control". Backend `/tape/SIM-BUYER/summary`: `buyer_control`, conf 0.87. | **PASS** | `UT-07-sim-buyer-control.png` |
| UT-08 | Historical AAPL replay populates | regression | P1 | Cockpit mounts; non-empty state/features; no error banner | Historical AAPL (2026-06-03 15:00–15:02) fetched real Alpaca data: scenario `historical AAPL 2026-06-03T15:00–2026-06-03T15:02`, bid/ask **311.67/313.30**, FEATURES populated (trade speed 2.17/s), RECENT TRADES streaming (311.70×320…), state **Unclear** (honest, wide IEX spread), no error banner. | **PASS** | `UT-08-historical-aapl.png` |
| UT-09 | Status dot live → stale → live | happy-path | P2 | Lull → dot **amber** `stale`; recent-trades count does NOT increase; resume → **emerald** `live` | **Stale leg + no-fabrication observed on the real path:** Live ZZZQQ (no prints on the prod IEX feed) → dot **amber** `stale` (`bg-amber-400`), sustained `stream_status=stale` for ~17s with **trades = 0** (QUOTE/FEATURES all empty/0.000, "No trades yet"). Live leg confirmed by UT-02; **stale→live recovery** is not browser-forceable on a non-streaming symbol and is covered by hermetic functional test TC-02. | **PASS** (stale + no-fabrication observed; recovery hermetic) | `UT-09-stale-amber.png` |
| UT-10 | Stop/switch tears down cleanly | happy-path | P1 | Cockpit clears; dot leaves live; subsequent `state` 404 — no orphan/leaked socket | Stop on a live (F) and a sim (SIM-BUYER) watch each cleared the cockpit to idle; backend dropped the watch entirely (`/tape/F/summary`, `/tape/SIM-BUYER/summary`, `/watch/*/state` all → **404**) — live Alpaca socket closed, no orphan/leak. (Dot returns to `idle`, the implementation's truthful no-watch state, rather than the plan's literal "closed".) | **PASS** | `UT-10-teardown-idle.png` |
| UT-11 | Live mode discoverable | ux | P3 | A clearly-labelled **Live** option; selecting it reveals the Live controls within 2 clicks | The 3-way selector (Live / Historical / Simulated) is on the home TopBar; one click on **Live** reveals symbol search + market indicator with no extra navigation. Labels unambiguous. | **PASS** | `UT-03-11-live-controls-idle.png` |

---

## Passed Tests

### UT-01 — Home screen loads with mode controls
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-4-evidence/UT-01-result.png`
- Navigated to `http://localhost:3650`; the page rendered the idle home with the Tapeology TopBar, the Live/Historical/Simulated segmented selector (Simulated active by default), the Ticker input + Watch button, and a grey **Idle** status dot. No blank screen, no error overlay. Reproduced cleanly on two separate navigations.

### UT-02 — Live watch of a real symbol mounts the cockpit (REAL Alpaca socket)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-4-evidence/UT-02-live-F-emerald.png`
- Selected **Live**, entered **F**, watched. Backend `:8650` (polled): `stream_status = live`, `scenario = "live F"`, real Ford quote **bid/ask 15.41 / 15.42** (penny spread), recent-trades count climbing 0 → 13+ (real prints: 15.38 ×718 SELL, ×600 SELL, 15.39 ×3300 SELL …).
- UI tab `:3650`: **Watching F**, status dot **emerald** (DOM class `bg-emerald-400`, label `live`), source label reads exactly **`scenario: live F`**, full cockpit mounted (TAPE STATE, QUOTE, FEATURES with volume 454/s and 11 large prints, RECENT TRADES streaming), **no** error banner.
- State read **Unclear / "Warming up"** at cold start — honest and correct (the engine does not manufacture a directional call from a cold/wide read; matches the iter-2 IEX lesson). This is genuine real-socket evidence for **J-12**, not a mock.

### UT-03 — Live mode reveals symbol search + market-status indicator
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-4-evidence/UT-03-11-live-controls-idle.png`
- Switching to **Live** reveals the `SymbolSearch` input and the `MarketStatusIndicator`, which polled `GET /market/clock` and rendered **`market open`** (emerald, title "The US market is open"). No error overlay from switching to Live.

### UT-04 — Symbol search filters and fills the symbol box
**Verdict:** PASS
**Evidence:** `UT-08-historical-aapl.png` (AAPL suggestions), `UT-02-live-F-emerald.png` (F suggestions)
- The debounced `GET /symbols/search` dropdown returned real verbatim matches: `AAP*` surfaced **AAPL — "Apple Inc. Common Stock"** at the top (plus AAPB/AAPD/AAPU/AAPW/AAPY/APLY); `F` surfaced **Ford Motor Company** (plus F.PRB/F.PRC/F.PRD…). Selecting a suggestion filled the symbol box and the subsequent watch used that ticker. No crash / empty list on a valid prefix.

### UT-07 — Sim SIM-BUYER still classifies (regression J-01/J-02)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-4-evidence/UT-07-sim-buyer-control.png`
- Simulated mode, watched **SIM-BUYER**. Backend `/tape/SIM-BUYER/summary`: `tape_state = buyer_control`, confidence ≈ **0.87**. UI: TAPE STATE **"Buyer Control"** (emerald) with a full confidence bar (0.893), populated QUOTE (Bid 103.03 / Ask 103.05), FEATURES (aggressive buy ratio 0.963, net aggressive volume 17300), RECENT TRADES (BUY prints), OBSERVATIONS ("Buyer aggression increasing"…), EVENT LOG ("Tape state changed to buyer_control"). Identical to pre-iteration behavior (sim path is a verified 0-line diff).

### UT-08 — Historical AAPL replay still populates (regression J-11)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-4-evidence/UT-08-historical-aapl.png`
- Historical mode, **AAPL**, window 2026-06-03 15:00–15:02 (1×). The backend fetched a real past window from Alpaca; `/tape/AAPL/summary`: scenario `historical AAPL 2026-06-03T15:00–2026-06-03T15:02`, bid/ask **311.67/313.30**. UI: cockpit mounted, QUOTE + FEATURES populated (trade speed 2.17/s, aggr. sell ratio 0.523), RECENT TRADES streaming as the replay advanced (311.70 ×320 …), state **Unclear** with observation "Mixed or weak evidence — no clear side in control" (honest, wide IEX spread), **no** error banner.

### UT-09 — Status dot stale on a quiet feed, with no fabricated trades (J-15 stale leg)
**Verdict:** PASS (stale flip + zero-fabrication observed on the real path; stale→live recovery covered by hermetic TC-02)
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-4-evidence/UT-09-stale-amber.png`
- Watched **ZZZQQ** (Alpaca's test symbol — it does not print on the production IEX feed) in Live mode. The stale watchdog flipped the canonical `stream_status` to **`stale`**: backend showed `stream_status = stale, trades = 0` sustained across 11 polls (~17s); UI dot **amber** (`bg-amber-400`, label `stale`), QUOTE all "—", FEATURES all 0.000, RECENT TRADES **"No trades yet"**, state honestly **Unclear**.
- This directly demonstrates the iteration's critical anti-goal guarantee: a feed lull surfaces **`stale`** and **no trades are fabricated** during the lull. The **stale→live recovery** leg cannot be browser-forced on a non-streaming symbol (and a liquid name like F never has a >10s gap during active hours), so it is covered by the hermetic deterministic functional test (TC-02), exactly as the test plan specifies. The live leg it builds on is confirmed by UT-02.

### UT-10 — Stop / switch tears down the watch cleanly (live + sim)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-4-evidence/UT-10-teardown-idle.png`
- Clicking **Stop** on the live **F** watch and on the sim **SIM-BUYER** watch each cleared the cockpit back to the idle "No ticker watched" state; the backend then returned **404** for `/tape/F/summary`, `/tape/SIM-BUYER/summary`, `/tape/ZZZQQ/summary`, and `/watch/<SYM>/state` — i.e. the watch (and, for live, the **vendor Alpaca socket**) was torn down with no orphan/leak. This validates the iter-0 socket-leak lesson at the UI level.
- Note: after Stop the status dot returns to **`idle`** (grey), the implementation's truthful no-watch state, rather than the literal `closed` the test plan/surface-map wording anticipated. The substantive teardown assertion (cockpit clears + backend watch removed, no orphan) is satisfied; the `idle` vs `closed` label is a benign wording nuance, not a defect.

### UT-11 — Live mode is discoverable
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-4-evidence/UT-03-11-live-controls-idle.png`
- The Live / Historical / Simulated segmented control sits on the home TopBar; a single click on the clearly-labelled **Live** chip reveals the Live controls (symbol search + market-status indicator) with no extra navigation. The three labels are unambiguous.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-05 — Live + missing credentials → provider unavailable
**Verdict:** SKIPPED
**Reason:** Not exercisable against this backend — Alpaca credentials **are** configured on `:8650`
(`GET /market/clock` → `available:true`). Producing the no-credentials path would require
reconfiguring/restarting the harness-managed backend (out of scope for browser QA, and would
disrupt the parallel run). The behavior is covered hermetically by the functional suite
(`provider_unavailable` → 503, no engine) and the `ProviderUnavailable` panel is present in the
frontend (`HONEST_REASONS` includes `provider_unavailable`).

### UT-06 — Live + market closed → market closed (next open)
**Verdict:** SKIPPED
**Reason:** Not exercisable now — the US market is **open** (`GET /market/clock` →
`is_open:true`, next_close `2026-06-04T20:00:00Z`). The closed-market refusal cannot be produced
during open hours. Covered hermetically (`market_closed` → 409 with `next_open`); iter-3 already
verified this gate with a `FakeAdapter`, and the closed-market panel renders the `next_open`.

*(Both UT-05 and UT-06 are the "honest non-cockpit" P2 cases the test plan flagged as the fallback
**when credentials are absent / the market is closed** — i.e. the opposite of today's state. Since
the live happy path WAS exercisable today, these complementary refusal paths are the ones that
could not be reproduced here. Neither is a failure; per the plan their substance is hermetic.)*

---

## Notes on verdict mapping

- **P1 result:** UT-01, UT-02, UT-03, UT-07, UT-08, UT-10 — **all PASS** ⇒ Browser QA Verdict **PASS**.
- No smoke, happy-path, or P1 test failed; there are **0 FAIL** results.
- The 3 SKIPs are gated/non-reproducible-state P2 cases, all hermetically covered — consistent with
  the test plan's own gated-path caveat (it anticipated EITHER the live path OR the refusal paths
  being exercisable in a given run, depending on creds + market hours).
- J-12 (real live read) and J-15 (honest `stale`, zero fabrication) were both **directly observed
  on the real Alpaca socket**, corroborated by authoritative backend reads on `:8650`.

---

## Environment

- **Frontend URL:** http://localhost:3650 (`NEXT_PUBLIC_API_URL=http://localhost:8650`)
- **Backend:** http://localhost:8650 — `/health` 200; `/market/clock` `available:true, is_open:true` (open) throughout
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (headless, shared profile `superpowers-chrome`, port 9222)
- **Market state at test time:** OPEN (creds configured) → live happy path exercisable; no-creds / market-closed refusal paths not reproducible
- **Concurrency caveat:** a second QA agent for the same phase was concurrently driving the shared Chrome tab and writing `TC-*` evidence to the same directory; mitigated via a dedicated tab + authoritative `:8650` backend cross-checks (see the test-environment note above)
- **Test Date:** 2026-06-04
- **Evidence directory:** `reports/qa/goal-i_will_be_super_rich-iter-4-evidence/` (own files prefixed `UT-`)
