# Phase goal-i_will_be_super_rich-iter-6 — UI Test Results

**Phase:** goal-i_will_be_super_rich-iter-6
**Date:** 2026-06-05
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

**Overall:** 0/15 tests passed (15 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Home page loads with chart panel when SIM-BUYER is watched | smoke | P1 | Page renders with chart panel visible | Frontend not running | SKIP | none |
| UT-02 | SIM-BUYER watch shows loading overlay then populates candlesticks | happy-path | P1 | Loading overlay then candlesticks appear | Frontend not running | SKIP | none |
| UT-03 | Emerald marker appears for buyer_control on SIM-BUYER chart | happy-path | P1 | Emerald arrow marker on chart at buyer_control transition | Frontend not running | SKIP | none |
| UT-04 | Rose marker appears for seller_control on SIM-SELLER chart | happy-path | P1 | Rose/red arrow marker on chart at seller_control transition | Frontend not running | SKIP | none |
| UT-05 | Amber markers appear for SIM-BIDABS and SIM-ASKABS | happy-path | P1 | Amber arrow markers on chart at absorption transitions | Frontend not running | SKIP | none |
| UT-06 | Bar-size selector switches granularity 10s / 30s / 60s | happy-path | P1 | Chart redraws with fewer/more bars when bar size changes | Frontend not running | SKIP | none |
| UT-07 | Chart is hidden when mode switches to Live | validation | P1 | Chart panel disappears after switching to Live mode | Frontend not running | SKIP | none |
| UT-08 | Chart reappears when switching back from Live to Simulated | regression | P1 | Chart panel reappears after switching back to Simulated | Frontend not running | SKIP | none |
| UT-09 | Chart shows loading overlay immediately after watch starts | validation | P2 | "Loading price history…" text visible within 2 seconds | Frontend not running | SKIP | none |
| UT-10 | Chart shows empty-state message when no price data exists | validation | P2 | "No price history for this window yet" shown on empty data | Frontend not running | SKIP | none |
| UT-11 | Chart is above cockpit, no cockpit panel displaced or obscured | regression | P1 | TopBar → chart panel → cockpit grid layout preserved | Frontend not running | SKIP | none |
| UT-12 | Pan and zoom interaction works on the chart canvas | happy-path | P2 | Time axis shifts on drag; zoom changes on scroll | Frontend not running | SKIP | none |
| UT-13 | Cockpit panels still receive live updates during Sim watch | regression | P1 | Quote/trades/tape-state panels update while chart is shown | Frontend not running | SKIP | none |
| UT-14 | Chart styling matches the cockpit dark instrument-panel theme | ux | P2 | Chart canvas dark background matching cockpit theme | Frontend not running | SKIP | none |
| UT-15 | Bar-size selector selected state is visually distinct | ux | P2 | Active bar-size button has visually distinct filled style | Frontend not running | SKIP | none |

---

## Passed Tests

None.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-01 — Home page loads with chart panel when SIM-BUYER is watched
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-02 — SIM-BUYER watch shows loading overlay then populates candlesticks
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-03 — Emerald marker appears for buyer_control on SIM-BUYER chart
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-04 — Rose marker appears for seller_control on SIM-SELLER chart
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-05 — Amber markers appear for SIM-BIDABS and SIM-ASKABS
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-06 — Bar-size selector switches granularity 10s / 30s / 60s
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-07 — Chart is hidden when mode switches to Live
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-08 — Chart reappears when switching back from Live to Simulated
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-09 — Chart shows loading overlay immediately after watch starts
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-10 — Chart shows empty-state message when no price data exists
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-11 — Chart is above cockpit, no cockpit panel displaced or obscured
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-12 — Pan and zoom interaction works on the chart canvas
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-13 — Cockpit panels still receive live updates during Sim watch
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-14 — Chart styling matches the cockpit dark instrument-panel theme
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-15 — Bar-size selector selected state is visually distinct
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

---

## Environment

- **Frontend URL:** http://localhost:3650
- **Browser:** Chrome via MCP (not used — frontend unavailable)
- **Test Date:** 2026-06-05
- **Evidence directory:** `reports/qa/goal-i_will_be_super_rich-iter-6-evidence/` (not created — no tests executed)
