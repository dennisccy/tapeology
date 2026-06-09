# Phase goal-i_will_be_super_rich-iter-13 — UI Test Results

**Phase:** goal-i_will_be_super_rich-iter-13
**Date:** 2026-06-09
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

**Overall:** 0/14 tests passed (14 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Home page loads without errors | smoke | P1 | Page renders without errors | Frontend not running | SKIP | none |
| UT-02 | Replay-speed dropdown visible and shows correct options | smoke | P1 | Dropdown visible with 1x/2x/5x/10x options | Frontend not running | SKIP | none |
| UT-03 | Mid-replay speed change accelerates cadence without restarting watch | happy-path | P1 | Speed change accelerates events, no watch restart | Frontend not running | SKIP | none |
| UT-04 | Pre-watch speed selection stages speed for next Watch | regression | P1 | Speed selection persists into next Watch start | Frontend not running | SKIP | none |
| UT-05 | Full RTH quick-pick loads tape data (no "very high-volume" error) | happy-path | P1 | Chart populates, no "very high-volume" error banner | Frontend not running | SKIP | none |
| UT-06 | Clear directional move on real sub-$100 stock resolves to control | happy-path | P1 | Tape-state shows buyer_control or seller_control | Frontend not running | SKIP | none |
| UT-07 | High aggression with no price progress stays unclear/absorption | validation | P2 | Tape-state shows unclear or absorption | Frontend not running | SKIP | none |
| UT-08 | SIM-BUYER/SIM-SELLER simulator baselines unchanged after J-33 re-tuning | regression | P1 | SIM-BUYER → buyer_control, SIM-SELLER → seller_control | Frontend not running | SKIP | none |
| UT-09 | Multi-hour window no longer triggers "shorter range" error | error | P1 | No "very high-volume" or "shorter range" error banner | Frontend not running | SKIP | none |
| UT-10 | Genuinely oversized window still shows actionable error banner | error | P2 | Actionable error banner with "shorter range" message | Frontend not running | SKIP | none |
| UT-11 | Historical window picker quick-picks unchanged after J-34 | regression | P1 | Quick-pick buttons visible, time range updates, chart populates | Frontend not running | SKIP | none |
| UT-12 | SIM-BUYER simulator chart renders correctly | regression | P1 | Chart renders candle data with buy-side markers | Frontend not running | SKIP | none |
| UT-13 | Speed dropdown reflects correct selected value while replay runs | ux | P2 | Dropdown shows updated speed immediately after selection | Frontend not running | SKIP | none |
| UT-14 | Speed dropdown present, labeled correctly, discoverable in Historical mode | ux | P2 | Dropdown visible, labeled with numeric multipliers 1x/2x/5x/10x | Frontend not running | SKIP | none |

---

## Passed Tests

None.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-01 — Home page loads without errors
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-02 — Replay-speed dropdown visible and shows correct options
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-03 — Mid-replay speed change accelerates cadence without restarting watch
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-04 — Pre-watch speed selection stages speed for next Watch
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-05 — Full RTH quick-pick loads tape data (no "very high-volume" error)
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-06 — Clear directional move on real sub-$100 stock resolves to control
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-07 — High aggression with no price progress stays unclear/absorption
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-08 — SIM-BUYER/SIM-SELLER simulator baselines unchanged after J-33 re-tuning
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-09 — Multi-hour window no longer triggers "shorter range" error
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-10 — Genuinely oversized window still shows actionable error banner
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-11 — Historical window picker quick-picks unchanged after J-34
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-12 — SIM-BUYER simulator chart renders correctly
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-13 — Speed dropdown reflects correct selected value while replay runs
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-14 — Speed dropdown present, labeled correctly, discoverable in Historical mode
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

---

## Environment

- **Frontend URL:** http://localhost:3650
- **Browser:** Chrome via MCP (not used — frontend unavailable)
- **Test Date:** 2026-06-09
- **Evidence directory:** `reports/qa/goal-i_will_be_super_rich-iter-13-evidence/`
