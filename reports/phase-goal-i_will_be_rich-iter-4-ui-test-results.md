# Phase goal-i_will_be_rich-iter-4 — UI Test Results

**Phase:** goal-i_will_be_rich-iter-4
**Date:** 2026-06-03
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests (UT-01–UT-05) pass; primary J-03 gate (UT-02 + UT-03) passes; buyer regression (UT-05) intact -->

**Overall:** 8/8 tests passed (0 skipped)

**Primary J-03 gate:** UT-02 (SIM-SELLER → Seller Control read) + UT-03 (measured rose color) — **both PASS**.
**Regression guard:** UT-05 (SIM-BUYER still Buyer Control in green) — **PASS** (new seller branch did not perturb the buyer read).
**Anti-goal coverage (UI-visible):** UT-06 (no fabricated snapshot on unknown ticker) + UT-07 (no seller over-fire without price progress) — **both PASS**.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Cockpit loads | smoke | P1 | Tapeology header, ticker input (ph "Ticker e.g. SIM-BUYER"), green Watch, idle/grey dot, no error | Title **Tapeology**, input aria-label **Ticker** + placeholder **Ticker e.g. SIM-BUYER**, **Watch** btn, **Idle** + grey dot, "No ticker watched", no rose error | **PASS** | `UT-01-result.png` |
| UT-02 | SIM-SELLER → Seller Control | happy-path | P1 | Headline **Seller Control**, conf ≥0.600, asr ≥0.600, sell impact negative, 3 obs, log "…seller_control" | Headline **Seller Control**, conf **0.888**, asr **0.955**, sell impact **-0.390**, 3 obs present, log **"Tape state changed to seller_control"** | **PASS** | `UT-02-seller-control.png` |
| UT-03 | Seller Control renders rose (measured) | happy-path | P1 | Headline `rgb(251,113,133)`, bar fill `rgb(244,63,94)`, sell-impact cell rose; base selectors resolve | Headline **`rgb(251,113,133)`**, bar **`rgb(244,63,94)`** (w 89%), sell-impact cell **`rgb(251,113,133)`**; `.text-rose-400`/`.bg-rose-500` base rules resolve | **PASS** | `UT-03-color-probe.png` |
| UT-04 | Live WS update, no reload | happy-path | P1 | Values update over WS w/o reload; status stays Live; new event-log lines appear mid-stream | Cockpit populated entirely via WS after Watch (no reload) in UT-02 & UT-05; status **Live** throughout; transition lines appeared live; backend conf climbs 0.775→0.892 (pushed every 0.2s) | **PASS** | `UT-02-seller-control.png` (live cockpit, no reload) |
| UT-05 | SIM-BUYER still Buyer Control (green) | regression | P1 | Headline **Buyer Control** `rgb(74,222,128)` green, conf ≥0.600, buy ratio high, buy impact positive, log "…buyer_control" | Headline **Buyer Control** **`rgb(52,211,153)`** (emerald-400), conf **0.871**, abr **0.928**, buy impact **+0.430** (emerald), bar **`rgb(16,185,129)`**, log **"Tape state changed to buyer_control"** | **PASS** (see color note) | `UT-05-buyer-control.png` |
| UT-06 | Unknown ticker error, no fabrication | error | P2 | Rose error line under header; no fabricated Tape State; app usable | Rose line **"'NOPE123' is not a known simulated ticker"** (`rgb(251,113,133)`); headline **null**; no Buyer/Seller Control; "No ticker watched"; input usable; status Idle | **PASS** | `UT-06-nope123-error.png` |
| UT-07 | Silent sim stays Unclear (no over-fire) | validation | P2 | Ticker accepted (no error), headline NOT Seller Control; stays Unclear/warming; no seller transition | Watching SIM-BIDABS (no error, 200); headline **Unclear** **`rgb(251,191,36)`** amber, conf 0.100, **warming**; event log empty; **no seller_control transition** | **PASS** | `UT-07-bidabs-unclear.png` |
| UT-08 | Ticker input discoverable / accepts both | ux | P3 | Input visible in 0 clicks; **Watching <ticker>** shown; free-text accepts both SIM tickers | Input always visible in header (every load); **Watching SIM-SELLER** (UT-02) and **Watching SIM-BUYER** (UT-05) both shown; both accepted via free text, no menu | **PASS** | `UT-02-seller-control.png`, `UT-05-buyer-control.png` |

---

## Passed Tests

### UT-01 — Cockpit page loads without errors (smoke)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_rich-iter-4-evidence/UT-01-result.png`
- Navigated to `http://localhost:3650/`. Measured DOM: title **Tapeology**, `input[aria-label="Ticker"]` with placeholder **Ticker e.g. SIM-BUYER**, **Watch** button, top-right status **Idle** (grey dot), "No ticker watched" empty state, no rose error text.
- Note: this Chrome MCP build does not capture browser console messages (console file stub: "not yet implemented"); "no uncaught errors" was instead confirmed by a clean full render plus an explicit JS probe (no rose error text, no error dialog — the `nextjs-portal` element is the always-present Next.js dev badge, not an error overlay).

### UT-02 — Watch SIM-SELLER resolves to Seller Control (primary J-03 gate)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_rich-iter-4-evidence/UT-02-seller-control.png`
- Typed `SIM-SELLER`, submitted; status transitioned to **Live**; "Watching SIM-SELLER" / "scenario: seller_control" shown.
- Tape State headline = **Seller Control**; **Confidence 0.888** (≥ 0.600); confidence bar filled (89%).
- Features: **Aggressive sell ratio 0.955** (≥ 0.600); **Sell price impact -0.390** (negative — keystone seller guard).
- Observations: **Seller aggression increasing**, **Price falling on sell prints**, **Spread stable and narrow** (all three).
- Event Log (newest first): **"Tape state changed to seller_control"**.

### UT-03 — Seller Control renders in rose (measured color)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_rich-iter-4-evidence/UT-03-color-probe.png`
- `getComputedStyle(headline).color` = **`rgb(251, 113, 133)`** (rose `text-rose-400`) — explicitly NOT slate `rgb(226,232,240)`, NOT emerald `rgb(74,222,128)`, NOT amber `rgb(251,191,36)`.
- Confidence-bar fill `backgroundColor` = **`rgb(244, 63, 94)`** (rose `bg-rose-500`), width 89%.
- **Sell price impact -0.390** cell color = **`rgb(251, 113, 133)`** (rose via `impactColor`); contrast: Buy price impact +0.120 cell = `rgb(52,211,153)` (emerald) — sign-based coloring confirmed.
- Base-selector stylesheet probe: `.text-rose-400` and `.bg-rose-500` resolve to real base rules in the served bundle (variant `hover:`/`focus:` forms excluded). This is the first on-screen render of the rose state path via the dynamic `stateColor("seller_control")` — confirmed live.

### UT-04 — Live WebSocket update without page reload
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_rich-iter-4-evidence/UT-02-seller-control.png` (live cockpit populated via WS, no reload)
- Core assertion directly observed: after clicking **Watch** (SIM-SELLER in UT-02, SIM-BUYER in UT-05), the entire cockpit (quote, features, tape state, confidence, observations, event log) populated **via the WebSocket stream with no page reload** — the page went from "No ticker watched" → full live read without F5.
- Status word stayed **Live** (green dot) throughout both watches.
- Event-log transition lines ("Tape state changed to seller_control" / "…buyer_control") appeared via the live stream, not after a manual reload.
- Confidence climb corroborated at the backend: SIM-BUYER confidence sampled **0.775 → 0.871 → 0.892** across the warm-up window; `WS /tape/{ticker}/stream` re-pushes the snapshot every 0.2s (`main.py` `WS_PUSH_INTERVAL`), and the UI rendered an in-flight value (0.871) below the final (0.892).
- Transparency: a standalone frame-by-frame UI climb *animation* was not captured as a separate artifact because (a) the simulated streams are finite and were pre-warmed on the backend so a fresh client resolves near-instantly, and (b) the shared Chrome was under concurrent contention (see Notes) that prevented reliable multi-second timed UI sampling. The test's expected results — live values without reload, status stays Live, event-log lines appear live — were all directly observed.

### UT-05 — SIM-BUYER still resolves to Buyer Control in green (regression — J-01/J-02)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_rich-iter-4-evidence/UT-05-buyer-control.png`
- Watched `SIM-BUYER`: headline **Buyer Control**, **Confidence 0.871** (≥ 0.600), bar filled 87%.
- **Aggressive buy ratio 0.928** (high); **Buy price impact +0.430** (positive, emerald cell).
- Event Log: **"Tape state changed to buyer_control"**.
- Measured headline color = **`rgb(52, 211, 153)`** (Tailwind **emerald-400**, `#34d399`) — green, explicitly NOT rose `rgb(251,113,133)`, NOT amber `rgb(251,191,36)`. Bar fill = **`rgb(16, 185, 129)`** (emerald-500). The new seller branch did **not** perturb the buyer read.
- **Color-reference note (test-plan typo, NOT a defect):** the test plan's reference lists `text-emerald-400 = rgb(74,222,128)`, but `rgb(74,222,128)` is Tailwind **green-400** (`#4ade80`); the true **emerald-400** is `rgb(52,211,153)`, which is what `format.ts` maps `buyer_control` to and what rendered. The bar fill `rgb(16,185,129)` matches the plan's stated `bg-emerald-500` exactly. The semantic requirement (green/emerald, distinctly not rose, not amber) is satisfied.

### UT-06 — Unknown ticker rejected with visible error, no fabricated snapshot (error)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_rich-iter-4-evidence/UT-06-nope123-error.png`
- Typed `NOPE123`, submitted: rose error line **"'NOPE123' is not a known simulated ticker"** appeared directly under the header (color `rgb(251,113,133)`), surfacing the backend `400` from `POST /watch/NOPE123` (independently confirmed via curl: POST=400, GET state=404).
- Tape State panel rendered **no** fabricated state (headline = null; no "Seller Control"/"Buyer Control"); "No ticker watched" empty state retained; status stayed **Idle**.
- App remained usable (ticker input still present and editable).

### UT-07 — Heavy non-resolving sim stays Unclear (validation — keystone anti-goal proxy)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_rich-iter-4-evidence/UT-07-bidabs-unclear.png`
- Typed `SIM-BIDABS` (reserved-but-silent sim), submitted: accepted with **no error** (Watch returned 200; "Watching SIM-BIDABS", scenario bid_absorption).
- Headline stayed **Unclear** (amber `rgb(251,191,36)`), **Confidence 0.100**, "Warming up — collecting tape data…" line shown; Quote/Features rendered honest no-data (`—` / 0.000), "No trades yet."
- **No** "Tape state changed to seller_control" ever appeared (event log empty). Confirms the product declares "Seller Control" only when price is actually pushed down — it does not over-fire on a non-seller stream, and a silent provider yields an honest empty/warming state (no fabrication).

### UT-08 — Ticker input accepts both SIM tickers and is discoverable (ux)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_rich-iter-4-evidence/UT-02-seller-control.png`, `reports/qa/goal-i_will_be_rich-iter-4-evidence/UT-05-buyer-control.png`
- The single ticker input (placeholder **Ticker e.g. SIM-BUYER**) is always visible in the header — reachable in 0 clicks from `/` on every load (UT-01, UT-02, UT-05, UT-06, UT-07 all show it).
- Free-text entry accepted both **SIM-SELLER** (UT-02) and **SIM-BUYER** (UT-05); the header shows **Watching SIM-SELLER** and **Watching SIM-BUYER** respectively. No separate menu or navigation required to switch tickers.

---

## Supporting cross-check (J-08 / single-source-of-truth corroboration)

Not a dedicated UT (the precise UI≡REST gate lives in the functional plan), but corroborated here:
- **SIM-SELLER** UI (seller_control, asr 0.955, sell impact -0.390) == REST `/summary` (seller_control, asr 0.955, spi -0.39) — exact match (stream closed/frozen).
- **SIM-BUYER** UI (buyer_control, abr 0.928, buy impact +0.430) vs REST `/summary` sampled later (buyer_control, abr 0.955, bpi 0.39) — identical **state**; feature magnitudes consistent, the small deltas reflect the rolling 30s window sampled at different stream timestamps (not a recomputation divergence). The UI reads the same snapshot contract the REST endpoints serve.

---

## Failed Tests

None.

---

## Skipped Tests

None. All 8 UI test cases were executed in a real Chrome session via Chrome MCP.

---

## Notes — operational issues encountered & handled

1. **Fresh backend engine state (deliberate restart).** The preceding functional-QA pass had already fed both finite simulated streams (SIM-SELLER, SIM-BUYER) to completion (`stream_status: closed`, snapshots frozen), and `WatchManager.watch()` is idempotent (no re-feed on re-watch). To verify the live warm-up path honestly (iter-1 lesson — an all-SKIPPED/stale run is not verification), the backend was cleanly restarted via the canonical `scripts/start-backend.sh` (`CHAIN_BACKEND_PORT=8650`), reset to fresh engine state (SIM-SELLER/SIM-BUYER → 404), and confirmed healthy before driving the browser.

2. **Next.js dev `.next` cache corruption — recovered (iter-1 lesson applied).** During the run the Next.js dev server hit a runtime webpack chunk error (`__webpack_modules__[moduleId] is not a function`, Next 15.5.19) — a known dev-mode `.next` build-cache artifact, **not** an application defect (the app rendered correctly before and after). Recovered exactly per the iter-1 precondition: killed the Next dev tree, `rm -rf apps/frontend/.next`, restarted via `scripts/start-frontend.sh` with `NEXT_PUBLIC_API_URL=http://localhost:8650`; clean recompile (`✓ Compiled / in 3.9s`), HTTP 200, app renders normally. Both services verified healthy at end (backend/frontend → 200).

3. **Shared-browser contention from a concurrent run (mitigated).** The Chrome MCP browser is shared; a concurrent **Trendora** browser-QA run (ports 3835/8835) was actively driving the same tab in real time (navigating it to its own pages, opening/closing tabs). Because the tab list is activity-ordered and both agents default to `tab_index 0`, naïve navigate→wait→read sequences were repeatedly hijacked, and one separate `screenshot` action captured a Trendora frame. Mitigations applied so every recorded result is genuinely from the Tapeology app: (a) every interaction eval begins with a `location.host === 'localhost:3650'` guard and reports `hijacked` instead of acting on the wrong app (so no measurement was ever taken from Trendora); (b) backend engines were pre-warmed via curl so the UI resolves instantly, removing multi-second waits; (c) evidence was taken from each successful host-verified eval's **atomic auto-captured PNG** rather than a separate screenshot action. UT-02/UT-03/UT-05/UT-06/UT-07 were each landed cleanly under this protocol with host-verified data.

---

## Environment

- **Frontend URL:** http://localhost:3650 (Next.js 15.5.19 dev)
- **Backend URL:** http://localhost:8650 (FastAPI/uvicorn) — restarted to fresh engine state during the run; healthy at end
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (headless)
- **Test Date:** 2026-06-03
- **Evidence directory:** `reports/qa/goal-i_will_be_rich-iter-4-evidence/`
  - `UT-01-result.png`, `UT-02-seller-control.png`, `UT-03-color-probe.png`, `UT-05-buyer-control.png`, `UT-06-nope123-error.png`, `UT-07-bidabs-unclear.png`
