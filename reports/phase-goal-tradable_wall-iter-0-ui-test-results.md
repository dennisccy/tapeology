# Goal Iteration 0 (Era 5B "The Tradable Wall") — UI Test Results

**Phase:** goal-tradable_wall-iter-0
**Date:** 2026-07-14
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!--
This is a BASELINE assessment (Mode: baseline per docs/phases/goal-tradable_wall-iter-0.md), not a
feature-delivery QA pass. The developer step this iteration was a no-op by design; the codebase probe
in the iter spec explicitly EXPECTED J-01, J-02, J-04, J-05, J-06 to fail (their modules/endpoints are
absent) and J-03/J-06 to report `blocked` (no Alpaca credentials). The FAIL verdict below is the
literal, honest application of the browser-qa-agent's PASS/FAIL rule ("any happy-path test fails ->
FAIL") to that reality — it is NOT a regression and NOT a broken build. Only J-07 (foundation
regression sentinel) was expected to, and did, PASS. The goal-evaluator should read this as the
intended baseline signal: 6 journeys to build, 1 already holding.
-->

**Overall:** 1/7 tests passed (2 blocked/skipped, 4 failed — all as expected for baseline)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The tradable level map — from 1,800 levels to ≤10 bands | happy-path | P1 | `tradability.py` exists; `GET /research/tradability?symbol=AAPL&as_of=...` returns a ≤10-band map; MCP proxy `tradability` registered | `apps/backend/app/research/tradability.py` absent; `GET /research/tradability` → HTTP 404; no `tradability` MCP tool in the server's tool list; no UI control on `/structure` calls this endpoint | FAIL | none (no UI surface exists; verified via API probe + `/structure` DOM inspection) |
| UT-J-02 | The wide scan — a case-study registry across the 12-symbol panel | happy-path | P1 | `setups.py` exists; `GET /research/setups` returns ≥15 events across ≥8 symbols; `GET /research/setups/{id}` drill-in works; MCP proxy `setups` registered | `apps/backend/app/research/setups.py` absent; `GET /research/setups` → HTTP 404; no `setups` MCP tool; no "Case Studies" section anywhere on `/structure` | FAIL | none (no UI surface exists; verified via API probe + `/structure` DOM inspection) |
| UT-J-03 | Real tape at the wall — credentialed event-window recording | happy-path (credential-gated) | P1 | With operator Alpaca credentials, ≥10 event-window datasets recorded across ≥5 symbols (incl. pinned AAPL 2026-06-22); tape timeline joined to `GET /research/setups/{id}` | No Alpaca credentials found in the environment (`env \| grep -i alpaca` empty — checked before any test ran). `GET /research/datasets` shows only 7 pre-existing PG reference fixtures (all `data_feed: sip`, created 2026-07-03, era-3/4 provenance) — zero AAPL or event-window datasets. J-02's scan registry (a prerequisite for "top-ranked scan events") is also absent, so there is nothing to record around even independent of credentials. | SKIP (**BLOCKED** — credentials absent; not simulated, per iter-spec instruction) | none — env probe only, no artifact contains any credential |
| UT-J-04 | The edge report — what actually profits, under the existing gates | happy-path | P1 | `structure_tape_map` registered beside frozen `v1`/`structure_tape`; `GET /research/edge-report` returns the 3-way aggregated report; MCP proxy `edge_report` registered | `/structure` → Registry section renders only `v1` and `structure_tape` strategy cards (confirmed both via browser DOM and `GET /research/strategies` JSON) — no `structure_tape_map`; `GET /research/edge-report` → HTTP 404; no `edge_report` MCP tool. (The pre-existing `apps/backend/app/research/edge_report.py` era-3 champion-only CLI is a different artifact per the iter spec's own heads-up note — not this endpoint.) | FAIL | `reports/qa/goal-tradable_wall-iter-0-evidence/J-05-structure-baseline-raw-levels.png` (Registry section visible, only 2 strategy cards) |
| UT-J-05 | `/structure` decluttered — the map is the default, the noise is a toggle | happy-path | P1 | Default AAPL 2026-06-22 view shows ≤10 bands (incl. a ~300–302 resistance band) — not 1,800 lines; a "raw levels" toggle restores the old view; Case Studies + Edge Report sections present; era-5 fetch control + provenance badge still work | Loaded AAPL as-of 2026-06-22T15:00:00Z via the existing Load control (bars already store-first-cached from era 5, no re-fetch triggered): the ONLY rendered view is the raw levels/zones chart — 1,801 level DOM rows and 2,437 zone-related DOM nodes rendered, all on-screen simultaneously, no clustering/banding. No "Tradable Map", "Case Studies", or "Edge Report" text/section exists anywhere on the page (checked via full-page `innerHTML` substring search — all four came back `false`). No toggle exists (nothing to toggle — raw is the only view today). The era-5 fetch control and provenance badge (`data-testid="feed-basis-label"` = "Yahoo Finance") DO still render correctly. | FAIL | `reports/qa/goal-tradable_wall-iter-0-evidence/J-05-structure-baseline-raw-levels.png` |
| UT-J-06 | Cockpit confluence — bands + tape markers + a descriptive chip | happy-path (credential-gated) | P1 | During a credentialed AAPL 2026-06-22 historical replay, the band overlay is visible and a descriptive confluence chip appears at the 300-test; SIM tickers show an honest "no tradable map" state; live mode unchanged | No Alpaca credentials in the environment (same probe as J-03) — the credentialed AAPL 06-22 replay cannot be exercised; not simulated, per iter-spec instruction. Baseline check of the CURRENT cockpit `PriceChart`: watched SIM-BUYER (settled `buyer_control`) and SIM-SELLER (settled `seller_control`) in Simulated mode, and opened Historical mode (speed 1x/2x/5x/10x + session-window controls render correctly, pre-existing era-4 feature) — in every state, full-page text search found no "band", "confluence", or "chip" anywhere in the DOM. The overlay/chip feature does not exist yet, consistent with J-01 (bands) not being built. | SKIP (**BLOCKED** — credentials absent; not simulated, per iter-spec instruction) | `reports/qa/goal-tradable_wall-iter-0-evidence/J-07-sim-buyer-control.png`, `J-07-sim-seller-control.png`, `J-06-cockpit-historical-mode-baseline.png` |
| UT-J-07 | The foundation is unchanged (regression sentinel) | regression/smoke | P1 | Full backend suite green; `config_fingerprint` stays `4d665603569b9dbf`; era 1–5 surfaces (`/journal`, `/studies`, `/performance`, `/structure` fetch + provenance badge, `SIM-BUYER`/`SIM-SELLER` cockpit settlement) behave exactly as shipped; only the era-5B-named surfaces are additive | Nav bar unchanged: Cockpit / Journal / Studies / Performance / Structure, no new entry. `SIM-BUYER` watched → settled `buyer_control` (Event Log: "Tape state changed to buyer_control", Observations: "Buyer aggression increasing / Price lifting on buy prints / Spread stable and narrow"). `SIM-SELLER` watched → settled `seller_control` (Event Log: "Tape state changed to seller_control", Observations: "Seller aggression increasing / Price falling on sell prints"). `/journal` loads (heading "Journal"). `/studies` loads (heading "Replay studies"). `/performance` loads and shows `fingerprint 4d665603569b9dbf`, champion = `v1`/`default` — fingerprint confirmed unchanged. `/structure` fetch control renders; loading AAPL levels reused the already-fetched bars (no repeat network call — store-first flow intact) and the provenance badge correctly showed feed = "Yahoo Finance". `git diff --stat apps/` is empty — no source file was touched during this baseline pass. (Full backend pytest suite run is out of scope for this browser-only agent — a separate deterministic gate; not exercised here.) | PASS | `reports/qa/goal-tradable_wall-iter-0-evidence/J-07-cockpit-empty.png`, `J-07-sim-buyer-control.png`, `J-07-sim-seller-control.png`, `J-05-structure-baseline-raw-levels.png` |

---

## Passed Tests

### UT-J-07 — The foundation is unchanged (regression sentinel)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-0-evidence/J-07-sim-buyer-control.png`, `J-07-sim-seller-control.png`, `J-05-structure-baseline-raw-levels.png`
- Nav bar identical to shipped state (5 items, no new entry) — confirms the "no new nav entry" anti-goal holds at baseline.
- `SIM-BUYER` → `buyer_control` and `SIM-SELLER` → `seller_control` both settle correctly and are visible in the on-page Event Log.
- `/journal`, `/studies` ("Replay studies" h1), `/performance` (shows `config_fingerprint 4d665603569b9dbf`, champion `v1`/`default`) all render without error.
- `/structure` era-5 "Fetch from Yahoo Finance" control, the Load flow, store-first bar reuse, and the "Yahoo Finance" provenance badge (`data-testid="feed-basis-label"`) all still work byte-for-byte as shipped.
- `git diff --stat apps/` returned empty — verify-only invariant held (no source file modified during this QA pass).
- A golden replay script was written to `runs/goal-session-tradable_wall/journey-scripts/J-07.json` and passed `demo_runner.py --mode lint`.

---

## Failed Tests

### UT-J-01 — The tradable level map — from 1,800 levels to ≤10 bands
**Verdict:** FAIL (expected at baseline — module not yet built)
**Failure:** `apps/backend/app/research/tradability.py` does not exist; `GET /research/tradability?symbol=AAPL&as_of=2026-06-22T15:00:00Z` returns HTTP 404; no `tradability` MCP proxy tool is registered (absent from the live MCP tool list). No control on `/structure` calls this endpoint (confirmed by full-page HTML inspection — zero "Tradable Map" or band-related markup).
**Evidence:** none (no UI surface exists to screenshot)

**Steps taken:**
1. `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8301/research/tradability?symbol=AAPL&as_of=2026-06-22"` → `404`.
2. Loaded `/structure` in browser, inspected full DOM — no band/tradability UI element.

**Expected:** Module present, endpoint returns a ≤10-band AAPL map with the pinned resistance band ranking top-2.
**Actual:** Module and endpoint absent — HTTP 404.

---

### UT-J-02 — The wide scan — a case-study registry across the 12-symbol panel
**Verdict:** FAIL (expected at baseline — module not yet built)
**Failure:** `apps/backend/app/research/setups.py` does not exist; `GET /research/setups` returns HTTP 404; no `setups` MCP proxy tool registered; no "Case Studies" section anywhere on `/structure`.
**Evidence:** none (no UI surface exists to screenshot)

**Steps taken:**
1. `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8301/research/setups"` → `404`.
2. Loaded `/structure` in browser, full-page text search for "Case Studies" → not found.

**Expected:** Registry with ≥15 events across ≥8 symbols; AAPL 06-22 event present with reaction `rejected`.
**Actual:** Module and endpoint absent — HTTP 404.

---

### UT-J-04 — The edge report — what actually profits, under the existing gates
**Verdict:** FAIL (expected at baseline — module not yet built)
**Failure:** Strategy Registry on `/structure` (and `GET /research/strategies`) lists only `v1` and `structure_tape` — no `structure_tape_map` entry. `GET /research/edge-report` returns HTTP 404. No `edge_report` MCP proxy tool registered.
**Evidence:** `reports/qa/goal-tradable_wall-iter-0-evidence/J-05-structure-baseline-raw-levels.png`

**Steps taken:**
1. Loaded `/structure`, inspected Registry section — only two `[data-testid="strategy-card"]` elements (`v1`, `structure_tape`).
2. `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8301/research/edge-report"` → `404`.

**Expected:** Three-way `v1`/`structure_tape`/`structure_tape_map` edge report available via `GET /research/edge-report`.
**Actual:** Only 2 of 3 strategies registered; report endpoint absent.

---

## Skipped Tests

### UT-J-03 — Real tape at the wall — credentialed event-window recording
**Verdict:** SKIPPED
**Reason:** **BLOCKED** — no Alpaca credentials present in the environment (`env | grep -i alpaca` returned nothing, checked before any test action). Per the iteration spec's explicit instruction, this is recorded as `blocked`, not simulated or fabricated. Independently, the J-02 scan-event registry this journey depends on ("top-ranked scan events") is also absent, so the journey has no data to act on even setting credentials aside. `GET /research/datasets` confirms zero AAPL/event-window datasets exist — only 7 pre-existing PG reference fixtures from era 3/4.

### UT-J-06 — Cockpit confluence — bands + tape markers + a descriptive chip
**Verdict:** SKIPPED
**Reason:** **BLOCKED** — same credential absence as J-03; the credentialed AAPL 2026-06-22 historical-mode replay cannot be exercised. Not simulated, per the iteration spec's explicit instruction. Baseline current-state check was still performed (see Results Table / evidence) confirming no band overlay or confluence chip exists yet in the cockpit `PriceChart` under Simulated or Historical mode.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-14
- **Evidence directory:** `reports/qa/goal-tradable_wall-iter-0-evidence/`
- **Alpaca credentials:** absent from environment at test time (`env | grep -i alpaca` empty) — J-03 and J-06 correctly recorded as `blocked`, not simulated.
- **`config_fingerprint`:** confirmed `4d665603569b9dbf` (visible on `/performance`, matches the iter-spec anchor value).
- **Golden replay scripts written this iteration:** `runs/goal-session-tradable_wall/journey-scripts/J-07.json` (lints clean via `demo_runner.py --mode lint`). No script written for J-01–J-06 (all FAIL/SKIP this iteration — no passing flow to capture).
- **Verify-only invariant:** `git diff --stat apps/` returned empty at the end of this QA pass — no source file under `apps/` was modified.
