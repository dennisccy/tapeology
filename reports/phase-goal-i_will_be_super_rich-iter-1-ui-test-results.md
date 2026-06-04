# Phase goal-i_will_be_super_rich-iter-1 — UI Test Results

**Phase:** goal-i_will_be_super_rich-iter-1
**Date:** 2026-06-04
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 12/12 tests passed (0 failed, 0 skipped)

All P1 tests (UT-01..UT-09) passed. Both target journeys are demonstrated in the browser:
- **J-10** (data-source selector + per-mode control reveal + Simulated→SIM-BUYER→buyer_control no-regression) — verified.
- **J-14 no-credentials path** (Live/Historical Watch → honest "real-data provider unavailable" non-cockpit state, no fabricated data, no sim fall-back) — verified, with backend REST cross-checks (503 `provider_unavailable` + `/state` 404 proving no engine created).

The iter-0 lesson (orphaned watch on source/symbol switch) is confirmed fixed: switching the data source and clicking Stop both tear the prior watch down in the UI **and** at the backend (`GET /tape/SIM-BUYER/state` → 404 after teardown).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Home loads with selector | smoke | P1 | Title + 3-button selector (Live/Historical/Simulated), Simulated active by default, Ticker input + Watch, no errors | On a clean load: "Tapeology" title, selector shows exactly Live/Historical/Simulated with **Simulated** `aria-pressed="true"`, input placeholder `Ticker e.g. SIM-BUYER` (aria-label `Ticker`), green Watch, Idle dot, "No ticker watched" idle state. No error banner. | PASS | `UT-01-home-simulated-default.png` |
| UT-02 | Mode selection highlights one | happy-path | P1 | Exactly one mode active at all times; clicking sets only that one | Live→only Live pressed; Historical→only Historical; Simulated→only Simulated. Never zero/two active. | PASS | `UT-02-live-selected.png`, `UT-03-04-historical-controls.png` |
| UT-03 | Mode-aware symbol/ticker input | happy-path | P1 | Sim: `Ticker e.g. SIM-BUYER`/`Ticker`; Live & Historical: `Symbol e.g. AAPL`/`Symbol search`; typed text preserved across switch | Placeholders & aria-labels exactly as specified per mode. Typed value "SIM-BUYER" preserved across Simulated→Live→Historical (input not destroyed). | PASS | `UT-01-home-simulated-default.png`, `UT-03-04-historical-controls.png` |
| UT-04 | Historical replay controls reveal | happy-path | P1 | Historical reveals Date + Start time + en-dash + End time + Replay speed (1×/2×/5×/10×, default 1×); gone in Live/Sim; Watch always present | Historical reveals `input[type=date]` (Date), two `input[type=time]` (Start time/End time), `–` separator, `select` (Replay speed) with options exactly `1× 2× 5× 10×` default `1×`. Live & Simulated have only the symbol/ticker input (selectCount 0). Watch present in all modes. | PASS | `UT-03-04-historical-controls.png` |
| UT-05 | Live market-status indicator | happy-path | P1 | Live shows amber pill "market unavailable" with amber dot; never open/closed; gone outside Live | Live shows pill: amber dot + "market" + "unavailable", title "Live market status needs vendor credentials (not configured)", `text-amber-400`. Page never shows "open"/"closed". Pill absent in Historical and Simulated. | PASS | `UT-05-live-market-unavailable.png` |
| UT-06 | Live no-creds → unavailable panel | happy-path | P1 | Amber "Real-data provider unavailable" panel, ⚠ + lowercase phrase, mentions Alpaca creds / switch to Simulated, NO cockpit, no sim fall-back | Watch AAPL in Live → amber panel: title "Real-data provider unavailable" (CSS-uppercased), ⚠ icon, exact lowercase "real-data provider unavailable", body "Live data needs vendor API credentials… Set the Alpaca API key and secret… or switch to Simulated". No cockpit grid. Mode stays Live (no fall-back). Dot "idle". Backend POST /watch/AAPL {mode:live} → HTTP 503 `provider_unavailable`. | PASS | `UT-06-live-provider-unavailable.png` |
| UT-07 | Historical no-creds → unavailable panel | error | P1 | Same amber panel, body references Historical needing vendor credentials, NO cockpit, no fall-back | Watch MSFT in Historical (date 2026-06-03, 09:30–10:30, 1×) → amber panel with ⚠ + lowercase phrase, body "Historical data needs vendor API credentials…". No cockpit. No fall-back. | PASS | `UT-07-historical-provider-unavailable.png` |
| UT-08 | SIM-BUYER cockpit populates | regression | P1 | Cockpit populates over WS; "Watching SIM-BUYER" + Stop; tape state buyer_control; live (green) dot; no provider panel | Simulated + SIM-BUYER + Watch → cockpit grid (6 panels) populated; TAPE STATE "Buyer Control" (confidence 0.869); Quote/Features/Recent Trades/Observations/Event Log filled; "Watching SIM-BUYER" + Stop; status dot **live** (green); event log "Tape state changed to buyer_control". No provider-unavailable panel. | PASS | `UT-08-cockpit-buyer-control.png` |
| UT-09 | Switching source tears down prior watch | regression | P1 | "Watching" clears, dot → idle/connecting (not stuck live), cockpit gone; new Live watch → provider panel | While watching SIM-BUYER (backend /state=200), clicked Live → "Watching" cleared, Stop gone, cockpit gone (0 panels), dot **idle**, idle state shown, backend /tape/SIM-BUYER/state → **404** (engine torn down — no orphan). Then Watch AAPL in Live → provider-unavailable panel, no cockpit, no orphaned watch. | PASS | `UT-09a-switch-teardown-idle.png`, `UT-09b-new-live-unavailable.png` |
| UT-10 | Stop ends active watch | regression | P2 | "Watching"+Stop disappear, cockpit clears to idle, dot → idle/closed, no console errors | While watching SIM-BUYER (6 panels, live dot), clicked Stop → "Watching"+Stop gone, cockpit cleared (0 panels), "No ticker watched" idle state, dot **idle** (grey). Backend /tape/SIM-BUYER/state → **404**. No functional errors observed. | PASS | `UT-10-after-stop-idle.png` |
| UT-11 | Empty Live symbol no fabrication | validation | P2 | No fabricated cockpit; panel OR inline error OR watch simply doesn't start; stays on / no crash | Live + empty symbol + Watch → watch does not start; IdleState ("No ticker watched") remains; no active watch; no cockpit; still on `/`; no crash. | PASS | `UT-11-empty-live-no-cockpit.png` |
| UT-12 | Real-data feature discoverable | ux | P3 | Live/Historical/Simulated visible in first view (0 clicks, no scroll); labels clear; unavailable panel explains next action | Selector sits in the top bar, fully visible on first load without scrolling (0 clicks). Labels Live/Historical/Simulated are self-describing. Unavailable panel states next action in plain language (set Alpaca key/secret, or switch to Simulated). | PASS | `UT-01-home-simulated-default.png`, `UT-06-live-provider-unavailable.png` |

---

## Passed Tests

### UT-01 — Home screen loads with the data-source selector
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-1-evidence/UT-01-home-simulated-default.png`
- On a clean (warm) load the segmented control shows exactly `Live` / `Historical` / `Simulated` in order; `Simulated` is `aria-pressed="true"`, the other two `false`.
- Symbol input placeholder `Ticker e.g. SIM-BUYER` with aria-label `Ticker`; green `Watch` button present; far-right status dot reads `idle`.
- See **Notes** below regarding a transient stale-state observation on the very first cold-compile request and how it was resolved (source default is deterministically `sim`; confirmed across 3 clean reloads).

### UT-02 — Selecting a mode highlights only that mode
**Verdict:** PASS
- Clicking Live / Historical / Simulated in turn produced exactly one `aria-pressed="true"` button each time — never zero, never two.

### UT-03 — Symbol/ticker input is mode-aware
**Verdict:** PASS
- Simulated: placeholder `Ticker e.g. SIM-BUYER`, aria-label `Ticker`.
- Live & Historical: placeholder `Symbol e.g. AAPL`, aria-label `Symbol search`.
- Text preservation: a typed value `SIM-BUYER` survived Simulated→Live→Historical switches (the input is a single shared controlled field, not destroyed on mode change).

### UT-04 — Historical mode reveals the replay-window controls
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-1-evidence/UT-03-04-historical-controls.png`
- Historical reveals a date input (`Date`), a start-time input (`Start time`), an en-dash `–` separator, an end-time input (`End time`), and a `Replay speed` `select` with options exactly `1× / 2× / 5× / 10×` (default `1×`).
- These controls are absent in Live (only the symbol box) and in Simulated (only the ticker box; selectCount = 0). The `Watch` button remains in all three modes.

### UT-05 — Live mode shows the honest market-status indicator
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-1-evidence/UT-05-live-market-unavailable.png`
- Live shows a pill with an amber dot + the text `market` `unavailable` (`text-amber-400`), title "Live market status needs vendor credentials (not configured)".
- The page never renders `open` or `closed` market state. The pill is absent in Historical and Simulated (Live-only).

### UT-06 — Live watch with no credentials shows the provider-unavailable panel
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-1-evidence/UT-06-live-provider-unavailable.png`
- Live + `AAPL` + Watch renders the amber-bordered panel titled "Real-data provider unavailable" (visually uppercased by CSS), a ⚠ icon, and the exact lowercase phrase `real-data provider unavailable`.
- Body: "**Live** data needs vendor API credentials, which are not configured… Set the Alpaca API key and secret in the backend environment, or switch to **Simulated**…".
- No cockpit grid; mode remains Live (no silent fall-back to Simulated); status dot `idle`.
- Backend cross-check: `POST /watch/AAPL {"mode":"live"}` → **HTTP 503** `{"detail":"real-data provider unavailable","reason":"provider_unavailable"}`; subsequent `GET /tape/AAPL/state` → **404** (no engine created — no fabricated snapshot).

### UT-07 — Historical watch with no credentials shows the provider-unavailable panel
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-1-evidence/UT-07-historical-provider-unavailable.png`
- Historical + `MSFT` + date `2026-06-03` + `09:30`–`10:30` + speed `1×` + Watch renders the same amber panel with ⚠ and the lowercase phrase; body references "**Historical** data needs vendor API credentials".
- No cockpit; no fabricated data; no fall-back to Simulated.

### UT-08 — Simulated SIM-BUYER watch still populates the cockpit
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-1-evidence/UT-08-cockpit-buyer-control.png`
- Simulated + `SIM-BUYER` + Watch populates the full cockpit grid (6 panels). TAPE STATE resolves to **Buyer Control** (confidence 0.869); Quote (Bid 102.11 / Ask 102.13 / Spread 0.02 / Last 102.13), Features, Recent Trades, Observations, and Event Log ("Tape state changed to buyer_control") are all populated.
- TopBar shows "Watching SIM-BUYER" + red Stop; far-right status dot reads **live** (green). No provider-unavailable panel.

### UT-09 — Switching source/symbol tears down the prior watch
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-1-evidence/UT-09a-switch-teardown-idle.png`, `UT-09b-new-live-unavailable.png`
- With SIM-BUYER actively watched (backend `/tape/SIM-BUYER/state` = 200), clicking **Live** cleared the "Watching SIM-BUYER" indicator and Stop, removed the cockpit (0 panels), returned the status dot to **idle** (not stuck on the prior live stream), and showed the idle state.
- Backend cross-check: after the switch, `GET /tape/SIM-BUYER/state` → **404**, proving the prior watch's engine was torn down (the iter-0 orphaned-watch lesson is fixed — no leftover backend watch/socket).
- Watching `AAPL` in Live afterward produced a clean provider-unavailable panel (no cockpit, no orphaned prior watch).

### UT-10 — Stop button ends an active simulated watch
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-1-evidence/UT-10-after-stop-idle.png`
- With SIM-BUYER watched (6 panels, live dot), clicking **Stop** removed the "Watching" indicator + Stop, cleared the cockpit to the idle empty state, and returned the status dot to **idle** (grey).
- Backend cross-check: `GET /tape/SIM-BUYER/state` → **404** after Stop (engine ended). No functional errors observed.

### UT-11 — Empty symbol in Live mode does not fabricate a cockpit
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-1-evidence/UT-11-empty-live-no-cockpit.png`
- Live + empty symbol + Watch: the watch simply does not start (client guards an empty candidate). The IdleState ("No ticker watched") remains; no active watch; no cockpit; no fabricated tape data; the app stays on `/` with no crash. This matches the test's "watch simply does not start" acceptable outcome.

### UT-12 — Real-data feature is discoverable and clearly labeled
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich-iter-1-evidence/UT-01-home-simulated-default.png`, `UT-06-live-provider-unavailable.png`
- The `Live` / `Historical` / `Simulated` selector is in the top bar and fully visible in the first view (0 clicks, no scrolling). The labels make the data-source intent clear.
- When a real mode is chosen with no credentials, the unavailable panel explains the next action in plain language (set the Alpaca API key/secret, or switch to Simulated) — the user is not left guessing.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Notes & Observations

- **Initial cold-compile transient (UT-01) — investigated, not a defect.** On the very first navigation to `/` (a Next.js dev cold-compile), the data-source selector momentarily appeared with `Live` and then `Historical` active before settling. Investigation: (1) `localStorage` is empty (no persisted mode); (2) the source default is deterministic — `apps/frontend/app/page.tsx:14` uses `useState<DataSourceMode>("sim")` with no randomness; (3) a pre-existing Chrome tab held a prior session's Tapeology page, so the stale DOM was shown while the route compiled. After warm-up, **3/3 clean reloads** showed `Simulated` active by default (and the captured evidence screenshot confirms it). Treated as a transient artifact of the dev cold-compile + a stale pre-existing tab, not an application defect. A production build (no on-demand compile) would not exhibit this.
- **Console capture limitation.** The Chrome MCP console log file is a stub ("Console logging not yet implemented"), so console errors could not be programmatically asserted. No functional/visual errors were observed across all 12 tests; no blank screens, no crashes, no broken renders.
- **No-credentials precondition verified independently.** The backend is running with no Alpaca credentials: `POST /watch/<sym> {"mode":"live"|"historical"}` returns 503 `provider_unavailable`, and `GET /tape/<sym>/state` returns 404 afterward — confirming no engine/snapshot is created (no fabricated data), consistent with the "No fabricated data" and "No secrets in source" anti-goals.
- **Watch-lifecycle hardening confirmed at the backend, not just the UI.** Both the source-switch (UT-09) and the Stop button (UT-10) drive `GET /tape/SIM-BUYER/state` from 200 → 404, demonstrating the prior watch's engine is actually torn down (the explicit iter-0 lesson).

---

## Environment

- **Frontend URL:** http://localhost:3650
- **Backend URL:** http://localhost:8650 (health: `{"status":"ok"}`; no Alpaca credentials configured)
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser`
- **Test Date:** 2026-06-04
- **Evidence directory:** `reports/qa/goal-i_will_be_super_rich-iter-1-evidence/`
