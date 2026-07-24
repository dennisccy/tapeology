# Phase goal-clean_slate-iter-2 — UI Test Results

**Phase:** goal-clean_slate-iter-2 (J-02: "Frontend + WS demolition — the two-page product")
**Date:** 2026-07-24
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 18/18 tests passed (0 failed, 0 skipped) — 16 UI test-plan cases (UT-01–UT-16) plus 2
goal-mode regression lanes (UT-J-01, UT-J-05).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Cockpit loads without errors | smoke | P1 | Nav = Cockpit+Structure; header controls; "No ticker watched" idle state; no thesis/hint/sound UI | Rendered exactly as expected; Watch disabled with amber "Enter a ticker symbol" | PASS | UT-01-cockpit-idle.png |
| UT-02 | Structure loads without errors | smoke | P1 | Heading "Structure"; Symbol/As-of/Today/Load form; empty-state Tradable Map prompt | Rendered exactly as expected, no chart/spinner/crash | PASS | UT-02-structure-idle.png |
| UT-03 | Top nav shows exactly two links | regression | P1 | Nav = "Cockpit","Structure" only, on both `/` and `/structure`; no "unavailable" banner | Confirmed via DOM (`nav a` = ["Cockpit","Structure"]) on both pages | PASS | UT-01-cockpit-idle.png, UT-15-nav-structure-active.png |
| UT-04 | `/journal` renders not-found | regression | P1 | "404" heading + "This page could not be found."; nav intact | Confirmed; DOM shows 0 buttons/inputs (no leftover journal table) | PASS | UT-04-journal-404.png |
| UT-05 | `/studies` renders not-found | regression | P1 | Same 404 treatment; no Create Study form/results list | Confirmed; 0 buttons/inputs | PASS | UT-05-studies-404.png |
| UT-06 | `/performance` renders not-found | regression | P1 | Same 404 treatment; no analytics chart/table | Confirmed; 0 buttons/inputs | PASS | UT-06-performance-404.png |
| UT-07 | `/journal/<id>` fails gracefully | error | P2 | Same 404 treatment; no crash/blank shell/stack trace | Confirmed clean 404 | PASS | UT-07-journal-id-404.png |
| UT-08 | Sim cockpit flow, no thesis/hint/sound | happy-path | P1 | 6-panel grid + chart; "Buyer Control" reached; no thesis strip/hint dock/sound toggle | Confirmed on 2 independent Watch cycles; 0 SVG circle markers; no thesis/hint/sound text anywhere | PASS | UT-08-sim-buyer-buyer-control.png |
| UT-09 | Stop returns to plain idle screen | regression | P1 | Returns directly to "No ticker watched"; no surviving-thesis panel | Confirmed via DOM (`bodyHasNoTicker:true`, `bodyHasWatching:false`, 0 Stop buttons) | PASS | UT-09-stop-returns-idle.png |
| UT-10 | PriceChart candles/timeframe/live bars | happy-path | P1 | Candles visible; 30s/60s timeframe switch selects correctly; bars keep moving; no thesis circle/up-arrow markers or dashed price lines | Confirmed via `aria-pressed` on Tape buttons + before/after price move (100.88→103.08 over 15s, x-axis window shifted) + 0 SVG circles | PASS | UT-10-pricechart-60s-live-t1.png, UT-10-pricechart-60s-live-t2-moved.png |
| UT-11 | Historical AAPL band overlay + provenance badge | regression | P1 | S/R band overlay renders on 1h History; feed chip = "SIP (consolidated)"; no thesis markers | Confirmed: pink resistance band "R A · 171 · round" at 300.10, feed chip exact text "SIP (consolidated)", 0 circle markers | PASS | UT-11-aapl-historical-band-overlay-1h.png |
| UT-12 | `/structure` wall band unchanged | regression | P1 | Resistance band ~300–302.4, Class A, round-number flag; same band on chart | Confirmed exact match: table row "300.11–302.2 \| Class A \| 171 \| 849 \| round number"; chart labels "300.10" and "302.20" on price axis | PASS | UT-12-structure-aapl-wall-band.png |
| UT-13 | WS frame has no thesis/hint key | regression | P1 | Captured frame JSON has no `thesis`/`hint` key; other keys present | Independently captured 3595 real frames via injected WebSocket monkey-patch on the app's own connection: 0 frames with `thesis` key, 0 with `hint` key; all other expected keys present | PASS | UT-13-ws-frame-capture.json |
| UT-14 | Empty-ticker Watch validation | validation | P2 | Watch disabled + amber message when empty; enabled once a char is typed | Confirmed via `button.disabled` true→false and message text present→absent | PASS | UT-14-watch-enabled-after-typing.png |
| UT-15 | Nav discoverability | ux | P2 | "Structure" visible in one glance; click navigates + highlights; no disabled/coming-soon labels | Confirmed: clicked nav link from Cockpit, arrived at `/structure` with "Structure" highlighted | PASS | UT-15-nav-structure-active.png |
| UT-16 | No dead references anywhere | ux | P3 | No "Journal/Studies/Performance/Declare thesis/Hint/Prefill" text on either kept page | Confirmed via full-body text scan on `/` and `/structure`: 0 forbidden-word hits on both | PASS | (DOM scan, no separate screenshot) |
| UT-J-01 | Backend demolition with byte-identical relocations (regression) | regression | P1 | All 14 I-1 routes 404; kept routes byte-identical except sanctioned `meta.ui-routes`; fingerprint unchanged | All 14 routes independently curled → 404; 5 kept routes spot-checked → 200; fingerprint = `4d665603569b9dbf` (matches); dev's I-9 re-capture shows only the 1 sanctioned + 2 explained non-regression diffs | PASS | (curl output, this report) |
| UT-J-05 | The kept product stands — regression sentinel (scoped subset) | regression | P1 | Sim cockpit settles Buyer Control w/ both-chart proof; `/structure` Load renders pinned AAPL wall band | Both re-verified live via the same evidence as UT-08/UT-10/UT-12 (this iteration's own diff surface); Case Studies / full-suite-under-new-pin / diff-vs-inventory correctly out of scope this iteration per phase spec NOTES | PASS | UT-08-sim-buyer-buyer-control.png, UT-12-structure-aapl-wall-band.png |

---

## Passed Tests

### UT-01 — Cockpit loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-clean_slate-iter-2-evidence/UT-01-cockpit-idle.png`
- Navigated to `/`. Nav bar shows "Tapeology" wordmark + exactly two links, "Cockpit" (highlighted) and "Structure". Header shows the 3-way source selector (Live/Historical/Simulated, Simulated default-highlighted), ticker field (placeholder "Ticker e.g. SIM-BUYER"), Watch button (disabled), amber "Enter a ticker symbol". Main area shows "No ticker watched" heading, the descriptive body text, and "Try: SIM-BUYER". No thesis strip, hint panel, or sound toggle anywhere.

### UT-02 — Structure loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-clean_slate-iter-2-evidence/UT-02-structure-idle.png`
- Navigated to `/structure`. Heading "Structure" renders. Nav shows "Structure" highlighted as active. Form shows Symbol (placeholder "e.g. PG"), As-of (placeholder "2026-06-09T21:00:00Z"), Today, Load. Tradable Map panel shows the exact empty-state prompt "Choose a symbol and an as-of time, then Load, to see its tradable level map." — no chart, no crash, no spinner.

### UT-03 — Top nav shows exactly two links on every kept page
**Verdict:** PASS
**Evidence:** `reports/qa/goal-clean_slate-iter-2-evidence/UT-01-cockpit-idle.png`, `UT-15-nav-structure-active.png`
- Verified programmatically via `Array.from(document.querySelectorAll('nav a')).map(a => a.textContent.trim())` on both `/` and `/structure`: returns exactly `["Cockpit","Structure"]` on each. "Cockpit" highlighted on `/`, "Structure" highlighted on `/structure`. No "navigation unavailable" banner on either page (backend reachable throughout).

### UT-04 — `/journal` renders the app's not-found page
**Verdict:** PASS
**Evidence:** `reports/qa/goal-clean_slate-iter-2-evidence/UT-04-journal-404.png`
- Navigated to `/journal`. Renders "404" heading + "This page could not be found." Nav bar intact above it, showing Cockpit/Structure. DOM has 0 buttons and 0 inputs (no leftover `JournalTable`/`JournalFilterBar` controls). Not blank, not a redirect, not a browser network-error page.

### UT-05 — `/studies` renders the app's not-found page
**Verdict:** PASS
**Evidence:** `reports/qa/goal-clean_slate-iter-2-evidence/UT-05-studies-404.png`
- Navigated to `/studies`. Same 404 treatment as UT-04. DOM has 0 buttons/0 inputs — no "Create Study" form, no study-results list, no "Replay studies" heading anywhere.

### UT-06 — `/performance` renders the app's not-found page
**Verdict:** PASS
**Evidence:** `reports/qa/goal-clean_slate-iter-2-evidence/UT-06-performance-404.png`
- Navigated to `/performance`. Same 404 treatment. DOM has 0 buttons/0 inputs — no analytics chart or table.

### UT-07 — `/journal/<id>` (nonexistent id) fails gracefully
**Verdict:** PASS
**Evidence:** `reports/qa/goal-clean_slate-iter-2-evidence/UT-07-journal-id-404.png`
- Navigated to `/journal/1`. Same clean 404 treatment — no crash, no blank detail shell, no raw JS stack trace in the page body.

### UT-08 — Sim cockpit flow settles Buyer Control with no thesis/hint/sound UI
**Verdict:** PASS
**Evidence:** `reports/qa/goal-clean_slate-iter-2-evidence/UT-08-sim-buyer-buyer-control.png`
- Typed `SIM-BUYER`, clicked Watch. Confirmed end to end on two independent Watch cycles (one that resolved/closed almost immediately, one that stayed genuinely live for the full observation window — both are legitimate simulated-scenario behaviors, unrelated to this iteration's diff). The 6-panel grid (Tape State, Quote, Features, Recent Trades, Observations, Event Log) appeared above a live price-chart panel. "Tape State" heading reached "Buyer Control" in bold green with a Confidence readout and progress bar. Verified programmatically at every checkpoint: 0 `<circle>` SVG elements (no thesis-verdict markers), body text contains none of "Declare thesis / Prefill / SETUP FORMING / verdict / stance", and no sound/mute icon visible in any screenshot.
- Note: the brief "Connecting to SIM-BUYER…" transient (step 4) resolved faster than this tool's screenshot round-trip could reliably catch for the SIM-BUYER scenario specifically; the equivalent transient WAS caught cleanly for the AAPL Historical watch (see UT-11), confirming the app's connecting-state UI works correctly — this is a tooling/timing observation, not a functional gap.

### UT-09 — Stop always returns to the plain idle screen
**Verdict:** PASS
**Evidence:** `reports/qa/goal-clean_slate-iter-2-evidence/UT-09-stop-returns-idle.png`
- From the Buyer Control state, clicked Stop. Verified via DOM (`bodyHasNoTicker:true`, `bodyHasWatching:false`, 0 remaining "Stop" buttons) and screenshot: returns directly to the same idle screen as UT-01 ("No ticker watched" / body text / "Try: SIM-BUYER"). No intermediate "surviving thesis" panel, banner, or card appeared at any point.

### UT-10 — Cockpit PriceChart: candles, timeframe switch, live bars, no thesis markers
**Verdict:** PASS
**Evidence:** `reports/qa/goal-clean_slate-iter-2-evidence/UT-10-pricechart-60s-live-t1.png`, `UT-10-pricechart-60s-live-t2-moved.png`
- Candlesticks confirmed visible (solid green bar bodies, not a blank chart). Clicked the Tape group's "30s" button — verified via `aria-pressed="true"` + distinct CSS classes (not just visual guess, since the page also has an unrelated Features-panel button group with the same "30s"/"60s" labels). Clicked "60s" — same `aria-pressed` verification. Captured two screenshots 15 seconds apart during a genuinely live watch: Bid/Ask/Last moved from 100.87/100.89/100.88 to 103.06/103.08/103.08, the chart's x-axis time window shifted forward (14:30–14:31 → 14:34–14:35), and the Recent Trades list fully refreshed — conclusive proof the chart is actively live, not frozen. No circle/up-arrow thesis markers and no dashed horizontal reference lines at any point (`svgCircleCount: 0`); only the expected down-arrow tape-state markers (e.g. green "Buyer Control", red "Seller Control") appear above bars.

### UT-11 — Historical AAPL replay: S/R band overlay + provenance badge
**Verdict:** PASS
**Evidence:** `reports/qa/goal-clean_slate-iter-2-evidence/UT-11-aapl-historical-band-overlay-1h.png`, `UT-11-aapl-historical-tape-markers.png`
- Switched to Historical, filled Symbol=AAPL, Date=22-06-2026, clicked "Open 9:30 ET" quick-pick (filled 02:30 PM–02:31 PM Europe/London), set Replay speed to 10×, clicked Watch. Caught the "Connecting to AAPL…" transient cleanly. Cockpit loaded normally (no real-data-unavailable panel). Clicked the History group's "1h" button: a shaded resistance band rendered directly on the chart, labeled "R A · 171 · round" at price 300.10, behind the candles. The "feed" chip read exactly "SIP (consolidated)" (not "Simulated") — verified via DOM text match. No thesis circle/up-arrow markers (`circleMarkerCount: 0`) and no "Declare thesis"/"Prefill"/"SETUP FORMING"/"verdict:" text anywhere.

### UT-12 — `/structure` Load still renders the unchanged 300–302-class wall band
**Verdict:** PASS
**Evidence:** `reports/qa/goal-clean_slate-iter-2-evidence/UT-12-structure-aapl-wall-band.png`, `UT-12-structure-loaded-fullpage.png`
- Filled Symbol=AAPL, As-of=2026-06-22T21:00:00Z, clicked Load. Tradable Map table's top resistance row reads exactly `resistance | 300.11–302.2 | Class A | 171 | 849 | round number` — falls within the expected ~300–302.4 range, Class A, round-number flag present. The same band is drawn on the candle chart below with explicit price-axis labels "300.10" and "302.20" next to the "R A · 171 · round" annotation — an exact match to the expected price-line labels near 300.1 and 302.2. No console errors observed; chart is not blank.

### UT-13 — Captured WS frame has no `thesis`/`hint` key
**Verdict:** PASS
**Evidence:** `reports/qa/goal-clean_slate-iter-2-evidence/UT-13-ws-frame-capture.json`
- Chrome MCP's `use_browser` tool has no built-in Network/WS-frame inspector action (confirmed via `action=help`), so this was verified with an equivalent, arguably stronger technique: a `window.WebSocket` monkey-patch was injected into the live page (before any Watch click) that transparently wraps the real constructor and records every message the app's own WS connection receives, without altering any behavior. Across two independent Watch cycles on `ws://localhost:8301/tape/SIM-BUYER/stream`, **3595 real frames** were captured. Result: **0 frames contain a `thesis` key, 0 frames contain a `hint` key**. The full key set on the last frame: `ticker, scenario, stream_status, paused, data_feed, delivery_lag_seconds, warm, timestamp, market, tape_state, confidence, primary_window, features, headline_features, observations, event_log, recent_trades` — every key the test plan calls out (`ticker`, `stream_status`, `tape_state`, `features`, `recent_trades`, `market`, `confidence`, `event_log`, `data_feed`) is present, with no `thesis`/`hint` anywhere.

### UT-14 — Watch button disables and explains itself on an empty ticker
**Verdict:** PASS
**Evidence:** `reports/qa/goal-clean_slate-iter-2-evidence/UT-14-watch-enabled-after-typing.png`
- On a fresh `/` load with an empty ticker field, verified via DOM: Watch button `disabled: true`, amber "Enter a ticker symbol" text present — before any click was attempted. After typing a single character (`A`), verified: `disabled: false`, warning text no longer present in the page body.

### UT-15 — Structure is reachable from Cockpit in one click; nav labels are unambiguous
**Verdict:** PASS
**Evidence:** `reports/qa/goal-clean_slate-iter-2-evidence/UT-15-nav-structure-active.png`
- From `/`, "Structure" is visible in the nav bar with no menu or scrolling required. Clicked the nav link (`//nav//a[text()="Structure"]`); the app navigated client-side to `/structure` (confirmed via `window.location.pathname === "/structure"`), and "Structure" now shows highlighted as the active link. No greyed-out/disabled/"coming soon" label for Journal, Studies, or Performance anywhere near the nav.

### UT-16 — No dead references to deleted pages/features anywhere in the kept UI
**Verdict:** PASS
- Scanned full `document.body.textContent` on both `/` and `/structure` for the strings "Journal", "Studies", "Performance", "Declare thesis", "Hint", "Prefill": **zero hits on either page**. (The dev handoff separately notes a bare word "Study" surviving inside one HTML source **comment** in `structure/page.tsx:1305` — comments are not part of rendered DOM text and were correctly not picked up by this rendered-text scan; not a UT-16 violation since UT-16 is scoped to what a user actually sees.) The only two navigable destinations referenced anywhere in either page's UI are "Cockpit" and "Structure".

### UT-J-01 — Backend demolition with byte-identical relocations (goal-mode regression lane, Required-still-passing)
**Verdict:** PASS
**Evidence:** curl output captured in this session (see Environment/Notes below); `runs/goal-session-clean_slate/iter-2/kept-route-after.txt` (dev's I-9 re-capture, cross-referenced)
- J-01's own acceptance is explicitly **keyless/automated** with no browser component (goal.md: *"(Keyless; automated.)"*; this iteration's own phase-spec NOTES confirm: *"J-01 has no browser component... its regression check this iteration is the I-9 byte-comparison re-capture... plus the full suite, not a browser replay."*). This lane was therefore executed as an HTTP/config-level check rather than a Chrome MCP click-path:
  1. **All 14 I-1 deleted routes independently curled → 404**: `GET /research/analytics`, `GET /research/thesis/active`, `GET /research/hints/active`, `GET /research/hints`, `GET /research/journal`, `GET /research/journal/1`, `POST /research/thesis`, `POST /research/thesis/1/resolve`, `POST /research/thesis/1/action`, `POST /research/thesis/1/review`, `POST /research/studies`, `GET /research/studies`, `GET /research/studies/1`, `POST /research/studies/1/cancel` — every one returned `404`.
  2. **5 kept routes spot-checked → 200**: `/research/taxonomy`, `/research/datasets`, `/research/strategies`, `/research/profiles`, `/research/pnl/ledger`.
  3. **Config fingerprint unchanged**: `python -c "from app.config import Config; print(Config().config_fingerprint())"` → `4d665603569b9dbf` (matches the pinned value).
  4. **`GET /meta/ui-routes`** returns exactly `{"routes": [{"path": "/", "label": "Cockpit", "nav": true}, {"path": "/structure", "label": "Structure", "nav": true}]}`.
  5. Cross-referenced the dev's own `runs/goal-session-clean_slate/iter-2/kept-route-after.txt` I-9 re-capture (28 kept routes vs. iter-1's baseline): 25/28 byte-identical, 1 sanctioned diff (`meta.ui-routes`, this iteration's own documented change), and 2 diffs (`research.backtests.list`, `research.pnl_ledger`) documented at length in that file's own header as a launch-cwd artifact (dev-server cwd reading a different, real, full-history `tapeology_journal.db` than iter-1's capture did), with byte-for-byte proof that pointing at the SAME db file reproduces iter-1's exact hashes — not a code regression. This browser-qa pass did not independently re-derive that SHA-256 proof (it is a backend data-path argument, not a UI-observable behavior) but the reasoning is sound and the affected routes are unrelated to any file this iteration touched (confirmed empty `git diff` on `backtests.py`/`pnl_ledger.py`/`store.py`/`config.py`, per the dev handoff).
  - Full pytest suite re-run was not repeated in this browser-qa pass (outside this agent's browser-testing mandate and duplicative of the dev/reviewer stage); the dev handoff reports 1162 passed / 1 pre-authorized failure (`test_mcp_server.py::test_static_live_tools_json_byte_identical_to_rest`, J-03's to close) / 7 skipped, matching iter-1's baseline minus the 3 sanctioned test-function deletions.

### UT-J-05 — The kept product stands — regression sentinel (goal-mode regression lane, scoped subset)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-clean_slate-iter-2-evidence/UT-08-sim-buyer-buyer-control.png`, `UT-10-pricechart-60s-live-t2-moved.png`, `UT-12-structure-aapl-wall-band.png`
- Per this iteration's own phase-spec NOTES: *"J-05's regression check this iteration is the browser walk in TC-5 through TC-8, covering exactly the kept surfaces this iteration's own diff touches (both charts, provenance badge, sim cockpit); J-05's OTHER acceptance clauses (Case Studies, full-suite-under-new-pin, cumulative diff-vs-inventory) are out of scope until J-04/J-05's own iteration."* This lane was scoped accordingly, not marked FAIL/SKIP for the intentionally-out-of-scope clauses:
  - **Sim cockpit settles Buyer Control with both-chart proof**: re-verified live via the same Watch→Buyer Control→Stop flow as UT-08, with the PriceChart candle/timeframe/live-bar proof from UT-10.
  - **`/structure` Load for the pinned AAPL as-of 2026-06-22 renders the 300–302.4 wall band**: re-verified live via the same Load flow as UT-12 — table row `300.11–302.2 | Class A | 171 | 849 | round number`, chart labels 300.10/302.20.
  - **Provenance badge**: re-verified via UT-11 (feed chip = "SIP (consolidated)" on the AAPL historical watch) and the Simulated-source runs (feed = "Simulated").
  - Case Studies drill-in, full-suite-under-the-new-pin, and the cumulative diff-vs-inventory cross-check are correctly NOT exercised here — they depend on J-04 (fingerprint epoch bump), which has not run yet this session, exactly as the phase spec's Out-of-Scope section states.

---

## Failed Tests

None. All 18 executed tests (16 UI test-plan cases + 2 goal-mode regression lanes) passed.

---

## Skipped Tests

None. Frontend, backend, and Chrome MCP were all available throughout the run.

---

## Methodology notes

- **Console-error capture**: Chrome MCP's `enable_console_logging`/`get_console_messages` and the per-action `*-console.txt` auto-capture consistently returned a placeholder (`# TODO: Console logging not yet implemented`) throughout this session — a tool-side limitation, not a claim of zero messages. Absence of console errors is inferred from the absence of any crash overlay, error boundary, or broken render across ~40 interactions and 20+ screenshots, not from captured console text. Noted here rather than silently assumed.
- **Race conditions in the tool's auto-captured screenshot**: on two occasions (the "Stop" click during UT-09/UT-10, and the "Structure" nav-link click during UT-15) the tool's own auto-captured screenshot was stale (taken before React finished re-rendering after a client-side state/route change). Both were caught and corrected by re-checking actual DOM/`window.location` state and taking a fresh screenshot — flagged here so the evidence PNGs are understood as the corrected, verified state, not the first raw capture.
- **SIM-BUYER scenario timing varies run to run**: one Watch cycle resolved to `buyer_control` and reported `stream_status: "closed"` (a settled/concluded simulated session) within the first delivered WS frame; a second cycle stayed genuinely `"live"` for the full observation window with continuously moving prices. Both are legitimate pre-existing simulated-scenario behaviors (verified unrelated to this iteration's WS-merge-removal diff, since the captured frames from the "closed" run show the exact same key set, no `thesis`/`hint`, as the "live" run) — not treated as a defect.
- **Golden replay scripts written**: `runs/goal-session-clean_slate/journey-scripts/J-02.json` and `.../J-05.json`, both lint-clean (`demo_runner.py --mode lint`). No script was written for J-01 — its acceptance is entirely keyless/HTTP-level (goal.md marks it `(Keyless; automated.)`), with no goto/click/fill browser flow to meaningfully replay; per the "best-effort, skip if you can't produce a clean one" rule, it is skipped rather than forced.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser`
- **Test Date:** 2026-07-24
- **Evidence directory:** `reports/qa/goal-clean_slate-iter-2-evidence/`
