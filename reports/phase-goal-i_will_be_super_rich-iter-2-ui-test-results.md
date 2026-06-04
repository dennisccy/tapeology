# Phase goal-i_will_be_super_rich-iter-2 — UI Test Results

**Phase:** goal-i_will_be_super_rich-iter-2
**Date:** 2026-06-04
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 14/15 tests passed (1 skipped — UT-10 not reachable; see note)

All reachable P1 tests passed. The one skipped test (UT-10, P1) is **not a failure**: it requires the
backend to run *without* Alpaca credentials, but this QA environment **has** working credentials, so the
no-credentials `provider_unavailable` state cannot be produced via the live backend. Its panel renders
through the **same** `ProviderUnavailable` component proven working by UT-08 and UT-09 (browser-verified).

---

## Environment notes (important — read first)

1. **Credentials ARE configured in this QA environment.** This *inverts* the test plan's default
   assumption. The operator-gated P1 tests (UT-02, UT-03, UT-06, UT-07, UT-08, UT-09) were therefore run
   against **real Alpaca data** and **PASS with real evidence** — `GET /symbols/search` returns real
   tradable matches, and a Historical watch of `F` over `2026-06-02T15:00–15:02Z` replays real Ford order
   flow. Conversely, UT-10 (no-creds panel) became *unreachable* and is recorded SKIPPED-not-reachable.

2. **Concurrent agent contention (resolved before the clean run).** During the first ~10 minutes the
   `qa` agent (PID 455243, same phase, QA-validation mode) was running its own required Chrome MCP browser
   checks against the **same** shared headless Chrome (port 9222) and the **same** backend (:8650). This
   intermittently stomped the shared tab (phantom `AAP` dropdown, a historical-`F` watch, mode flips I did
   not perform). I detected this via `ps`/backend-log analysis, **waited for the qa agent to exit**
   (confirmed: process gone + its report written), then **re-ran the entire suite cleanly** on a single
   driver. Every result below comes from that clean run and was **immediately re-verified via `eval` and
   cross-checked against the backend REST API**. The `TC-*` screenshots in the evidence directory are the
   qa agent's (shared dir), not mine; my evidence is the `UT-*` files.

3. **SSOT cross-checks.** For state-bearing tests I compared the rendered UI against `GET /tape/<t>/state`
   and `/summary` at a stable point (replay closed) — values matched, confirming the UI reads the canonical
   engine snapshot rather than recomputing.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Home loads, Simulated default | smoke | P1 | Wordmark, Live/Historical/Simulated (Simulated active), ticker input, Watch, idle "No ticker watched" | Exactly as expected; Idle dot; no error banner | PASS | `UT-01-home-simulated-default.png` |
| UT-02 | Search dropdown shows real matches | happy-path | P1 (gated→reachable) | Dropdown of SYMBOL + company rows for `AAP` | 12 real rows (AAP/ADVANCE AUTO PARTS, AAPB, AAPD, AAPG, …, AAPL/Apple Inc.); mono ticker + name; matches API exactly | PASS | `UT-02-symbol-search-dropdown-AAP.png` |
| UT-03 | Selecting a suggestion fills the box | happy-path | P1 (gated→reachable) | Box filled with AAPL, dropdown closes, no watch | Box = `AAPL`; dropdown closed on click; no watch started | PASS (minor nit) | `UT-03-suggestion-filled-AAPL.png` |
| UT-04 | Free-text Watch works | happy-path | P1 | Typed `F` (dropdown ignored) → watch starts for F | "Watching F" + cockpit populated; dropdown ignored/closed; scenario chip correct | PASS | `UT-04-freetext-F-watching.png` |
| UT-05 | Short/cleared query → no dropdown | validation | P2 | Empty/no-match query shows no dropdown, no stale rows | Empty → no listbox; `ZZQXNOMATCH9` (API `[]`) → 0 rows, no listbox | PASS | `UT-05-nomatch-no-dropdown.png` |
| UT-06 | Historical watch fills cockpit (real) | happy-path | P1 (gated→reachable) | Cockpit populates with real bid/ask/spread/last, trades, features, state+confidence, observations, event log | Full cockpit: Bid 16.59 / Ask 16.60 / Spread 0.01 / Last 16.59, tape state `Bid Absorption` (conf 0.950), 13 features, real trades table, observations, event log — matches REST (SSOT) | PASS | `UT-06-historical-F-cockpit.png` |
| UT-07 | Scenario chip `historical <SYM> <window>` | happy-path | P2 (gated→reachable) | Chip reads `historical F …` from snapshot | Chip = `historical F 2026-06-02T15:00–2026-06-02T15:02`; equals `scenario` field of `/tape/F/state` | PASS | `UT-06-historical-F-cockpit.png` (chip visible in header) |
| UT-08 | "Symbol not tradable" panel | error | P1 (gated→reachable) | Amber panel "Symbol not tradable" + phrase "not a tradable symbol"; no cockpit; no engine | Amber panel `SYMBOL NOT TRADABLE` + ⚠ + "not a tradable symbol" + no-fabrication help; no cockpit; no "Watching"; `/tape/ZZZZNOPE/state` → 404 | PASS | `UT-08-symbol-not-tradable.png` |
| UT-09 | "No data for that window" panel | error | P1 (gated→reachable) | Amber panel "No data for that window" + phrase; no cockpit | Amber panel `NO DATA FOR THAT WINDOW` + ⚠ + "no data for that window" + market-hours help; no cockpit; `/tape/F/state` → 404 (no engine) | PASS | `UT-09-no-data-for-window.png` |
| UT-10 | "Real-data provider unavailable" panel | error | P1 | No-creds → amber "Real-data provider unavailable" panel | **Not reachable**: this env HAS credentials, so `provider_unavailable` cannot be produced live. Same component/route proven by UT-08/09 + source. | SKIPPED-not-reachable | none (see Skipped) |
| UT-11 | Reason routing; cockpit never alongside | validation | P2 | Each reason → exactly one matching amber panel; cockpit absent | `symbol_not_tradable` (UT-08) and `no_data_for_window` (UT-09) each routed to exactly one matching panel, cockpit absent; 3rd reason unreachable but shares the identical route | PASS | `UT-08-…png`, `UT-09-…png` |
| UT-12 | Simulated keeps plain input | regression | P1 | Plain `Ticker e.g. SIM-BUYER` input; no dropdown; no historical controls | Plain input (no `SymbolSearch`); typing `SIM` shows no listbox; Date/Start/End/Speed not rendered in Simulated | PASS | `UT-12-sim-plain-input-no-dropdown.png` |
| UT-13 | SIM-BUYER classifies; Stop → idle | regression | P1 | Cockpit reaches `buyer_control`; Stop → idle | "Watching SIM-BUYER" + cockpit; UI `buyer_control` matches REST (conf 0.85); Stop → "No ticker watched", no error | PASS | `UT-13-sim-buyer-cockpit-buyer_control.png` |
| UT-14 | Source switch tears down watch | regression | P2 | Switching to Historical removes cockpit, shows historical controls, no orphaned watch | After SIM-BUYER active, click Historical → no "Watching", idle, historical controls shown; backend `/tape/SIM-BUYER/state` → 404 (no orphan) | PASS | `UT-14-source-switch-teardown.png` |
| UT-15 | Feature discoverable from `/` | ux | P3 | Source selector + all historical controls visible on one screen, no hidden nav | Live/Historical/Simulated + Symbol search + Date + Start + End + Replay speed + Watch all visible without scrolling (viewport 1100px) | PASS | `UT-15-historical-controls-discoverable.png` |

---

## Passed Tests

### UT-01 — Home page loads with default Simulated mode
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-2-evidence/UT-01-home-simulated-default.png`
- "Tapeology" wordmark, 3-way Live/Historical/Simulated control with **Simulated active**, ticker input
  (`Ticker e.g. SIM-BUYER`), green **Watch** button, and the idle "No ticker watched" main area all render.
  Idle status dot top-right; no error banner.

### UT-02 — Symbol search dropdown shows real matches (Historical)
**Verdict:** PASS
**Evidence:** `…/UT-02-symbol-search-dropdown-AAP.png`
- In Historical mode, typing `AAP` produced a `role="listbox"` ("Symbol suggestions") with **12 real rows**:
  `AAP` (ADVANCE AUTO PARTS INC), `AAPB`, `AAPD`, `AAPG`, `AAPL` (Apple Inc. Common Stock), … each row a
  monospaced ticker + lighter company name. The rows match `GET /symbols/search?q=AAP` byte-for-byte.

### UT-03 — Selecting a suggestion fills the box
**Verdict:** PASS (with a minor UX observation)
**Evidence:** `…/UT-03-suggestion-filled-AAPL.png`
- Clicking the `AAPL` row filled the symbol input with `AAPL`; the dropdown closed on the click; **no watch
  started** (idle remained). **Minor nit:** ~250 ms later the debounced lookup re-runs for the now-complete
  value `AAPL` and the dropdown briefly **re-opens** with AAPL-prefixed matches. Not a functional failure
  (symbol is correctly filled and free-text/watch still work), but a small polish item — selecting a
  suggestion arguably should suppress the immediate re-search.

### UT-04 — Free-text symbol Watch works without the dropdown
**Verdict:** PASS
**Evidence:** `…/UT-04-freetext-F-watching.png`
- Typed `F` with real keystrokes, **ignored** the open suggestions dropdown, and clicked **Watch**. The
  watch started for the typed text `F`: header showed "Watching F", the cockpit populated, scenario chip
  `historical F 2026-06-02T15:00–2026-06-02T15:02`. Backend `/tape/F/state` → 200. No silent no-op.

### UT-05 — Short / cleared query shows no dropdown
**Verdict:** PASS
**Evidence:** `…/UT-05-nomatch-no-dropdown.png`
- Emptying the field hides the dropdown (no stale rows). A no-match query `ZZQXNOMATCH9` (backend returns
  `[]`) leaves **0** option rows and no listbox.

### UT-06 — Historical watch populates the full cockpit with real values
**Verdict:** PASS
**Evidence:** `…/UT-06-historical-F-cockpit.png`
- Historical watch of `F` (2026-06-02 15:00–15:02, 10×) populated **every** cockpit value with real Ford
  data: **Quote** Bid 16.59 / Ask 16.60 / Spread 0.01 / Last 16.59; **Tape State** `Bid Absorption`,
  **Confidence** 0.950; **Features** (Trade speed 0.20/s, Aggressive sell ratio 1.000, Net aggressive
  volume −400, Absorption score 1.000, …); **Recent Trades** table with real price/size/side rows (incl.
  honest `UNKNOWN` sides where the aggressor classifier could not derive a side from quotes); **Observations**
  ("Heavy sell volume being absorbed", …); **Event Log** ("Bid refreshing at 16.59", "Tape state changed to
  bid_absorption", "Large buy print absorbed", …). UI values match `GET /tape/F/state` + `/summary` (SSOT).

### UT-07 — Source label reads `historical <SYM> <window>`
**Verdict:** PASS
**Evidence:** `…/UT-06-historical-F-cockpit.png` (chip in header)
- The `scenario:` chip reads `historical F 2026-06-02T15:00–2026-06-02T15:02`, identical to the `scenario`
  field returned by `GET /tape/F/state` (not a fabricated client string).

### UT-08 — Untradable symbol → "Symbol not tradable" honest panel
**Verdict:** PASS
**Evidence:** `…/UT-08-symbol-not-tradable.png`
- Historical watch of `ZZZZNOPE` rendered an amber-bordered panel titled `SYMBOL NOT TRADABLE`, a ⚠ icon,
  the emphasized phrase **"not a tradable symbol"**, and help text explicitly stating "No tape is shown —
  Tapeology never fabricates data to fill the gap." **No** cockpit, **no** "Watching" chip. Backend
  `/tape/ZZZZNOPE/state` → 404 — **no engine created** (no fabrication).

### UT-09 — Empty window → "No data for that window" honest panel
**Verdict:** PASS
**Evidence:** `…/UT-09-no-data-for-window.png`
- Historical watch of `F` over a past Sunday (2026-05-31, market closed) rendered the amber `NO DATA FOR
  THAT WINDOW` panel, ⚠ icon, phrase **"no data for that window"**, and "Try a different window during
  regular market hours" help. **No** cockpit. Backend `/tape/F/state` → 404 — **no engine created**.

### UT-11 — Each failure reason routes to its own panel; cockpit never alongside
**Verdict:** PASS
- Two of the three honest reasons were exercised back-to-back: `symbol_not_tradable` (UT-08) and
  `no_data_for_window` (UT-09). Each showed **exactly one** amber panel matching its reason with the
  cockpit **absent** (no panel-alongside-cockpit, no two panels at once). The third reason
  (`provider_unavailable`) is unreachable in this creds-present env (UT-10) but is routed through the
  **identical** `page.tsx` path (`HONEST_REASONS` includes all three → `ProviderUnavailable`).

### UT-12 — Simulated mode keeps the plain ticker input
**Verdict:** PASS
**Evidence:** `…/UT-12-sim-plain-input-no-dropdown.png`
- Simulated mode uses a plain `aria-label="Ticker"` input (placeholder `Ticker e.g. SIM-BUYER`). Typing
  `SIM` produced **no** suggestions dropdown (no `SymbolSearch`), and the Historical-only controls
  (Date / Start time / End time / Replay speed) are **not** rendered in Simulated mode.

### UT-13 — SIM-BUYER classifies; Stop returns to idle
**Verdict:** PASS
**Evidence:** `…/UT-13-sim-buyer-cockpit-buyer_control.png`
- Watching `SIM-BUYER` populated the cockpit and reached tape state **`buyer_control`** (UI matched
  `GET /tape/SIM-BUYER/state`: `buyer_control`, confidence ≈0.85, warm). Clicking **Stop** removed the
  cockpit and returned the main area to the idle "No ticker watched" state with no error banner.

### UT-14 — Switching data source tears down the active watch
**Verdict:** PASS
**Evidence:** `…/UT-14-source-switch-teardown.png`
- With `SIM-BUYER` actively watching, clicking **Historical** removed the "Watching SIM-BUYER" chip and the
  cockpit, returned to idle, and revealed the historical controls. Backend `/tape/SIM-BUYER/state` → 404,
  confirming the prior watch (and its feeder) was torn down — **no orphaned watch** (iter-0 lesson holds).

### UT-15 — Search box / honest panels discoverable from one screen
**Verdict:** PASS
**Evidence:** `…/UT-15-historical-controls-discoverable.png`
- The Live/Historical/Simulated control is visible without scrolling (one click to real data). In
  Historical mode the Symbol search, Date, Start time, End time, Replay speed, and Watch controls are all
  on-screen within the 1100px viewport — the entire J-11/J-13/J-14 feature set is reachable from `/` with
  no hidden navigation.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-10 — No credentials shows the "Real-data provider unavailable" honest panel
**Verdict:** SKIPPED-not-reachable
**Reason:** The test requires the backend to run **without** Alpaca credentials, but this QA environment
**has** working credentials (verified: `GET /symbols/search` returns real matches; Historical `F` fetch
succeeds). With credentials present, `adapter.is_available()` is true, so the `provider_unavailable`
reason cannot be produced through the live backend:
- Historical mode with creds proceeds to fetch (never `provider_unavailable`);
- Live mode with creds returns `provider_not_implemented` (503) — a different reason that is **not** in
  `HONEST_REASONS`, so it does not render this panel.

This is **not a FAIL** (no defect observed; the state is simply unreachable in this env). Confidence the
panel still works rests on convergent evidence:
1. The **same** `ProviderUnavailable` component renders all three reasons; its `symbol_not_tradable` and
   `no_data_for_window` branches were **browser-verified** (UT-08, UT-09) with identical structure
   (amber border, ⚠, emphasized phrase, no-fabrication help).
2. Source review (`components/ProviderUnavailable.tsx`, `app/page.tsx`): the `provider_unavailable`
   (default) branch maps to title "Real-data provider unavailable", phrase "real-data provider
   unavailable", and help mentioning the Alpaca key/secret or switching to Simulated; `page.tsx`
   `HONEST_REASONS` includes `provider_unavailable` and routes it to this component in place of the cockpit.
3. This was the J-14 slice that landed and was verified in iter-1 (no-credentials honest-unavailable state).

To browser-verify UT-10 directly, re-run browser QA against a backend started **without** `ALPACA_API_KEY`
/ `ALPACA_API_SECRET`.

---

## Minor observations (non-blocking)

- **UT-03 dropdown re-open:** after picking a suggestion, the debounced lookup re-runs for the completed
  symbol and the dropdown briefly re-opens. Polish item, not a failure.
- **Symbol value persists across a mode switch:** switching Simulated→Historical keeps the previously typed
  symbol in the box (single shared input state). Cosmetic; not covered by any test case and not a failure.
  (Encountered during setup; mentioned for transparency.)

---

## Environment

- **Frontend URL:** http://localhost:3650
- **Backend URL:** http://localhost:8650 (health 200; **Alpaca credentials present** in this env)
- **Browser:** Chrome (headless) via `mcp__plugin_superpowers-chrome_chrome__use_browser` (CDP :9222)
- **Test Date:** 2026-06-04
- **Evidence directory:** `reports/qa/goal-i_will_be_super_rich-iter-2-evidence/`
- **Concurrency:** a sibling `qa` agent shared this Chrome + backend early on; the clean suite was run
  after it exited (see "Environment notes" above). All `UT-*` evidence is from the clean single-driver run.
