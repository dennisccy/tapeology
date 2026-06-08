# Phase goal-i_will_be_super_rich-iter-12 — UI Test Results

**Phase:** goal-i_will_be_super_rich-iter-12
**Date:** 2026-06-09
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

**Overall:** 0/16 tests passed (16 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Home cockpit loads without errors | smoke | P1 | Page renders with chart, controls, no errors | Frontend not running | SKIP | none |
| UT-02 | Simulated chart axis shows synthetic session-clock times | happy-path | P1 | Axis labels show dd-MM-yyyy HH:mm:ss | Frontend not running | SKIP | none |
| UT-03 | Historical chart axis shows real market clock times | happy-path | P1 | Axis labels show dd-MM-yyyy HH:mm:ss | Frontend not running | SKIP | none |
| UT-04 | Crosshair tooltip shows true clock time on hover | happy-path | P1 | Tooltip shows dd-MM-yyyy HH:mm:ss | Frontend not running | SKIP | none |
| UT-05 | Tape-state marker labels show true clock time | happy-path | P1 | Marker label shows dd-MM-yyyy HH:mm:ss | Frontend not running | SKIP | none |
| UT-06 | Bar-size switcher preserves real-clock time axis | happy-path | P1 | Axis labels remain dd-MM-yyyy HH:mm:ss after bar-size change | Frontend not running | SKIP | none |
| UT-07 | Historical date input accepts valid dd-MM-yyyy entry | happy-path | P1 | Field accepts 15-03-2024, Watch button enabled | Frontend not running | SKIP | none |
| UT-08 | Historical date input rejects impossible date | validation | P2 | Field shows amber border and error for 31-02-2026 | Frontend not running | SKIP | none |
| UT-09 | Historical date input rejects malformed entry | validation | P2 | Field shows amber border and error for ISO-format input | Frontend not running | SKIP | none |
| UT-10 | Market-status next-open time shows dd-MM-yyyy HH:mm UTC format | happy-path | P1 | Next-open shows dd-MM-yyyy HH:mm UTC+HH:MM | Frontend not running | SKIP | none |
| UT-11 | Watched-source descriptor shows dd-MM-yyyy dates | happy-path | P1 | Descriptor uses dd-MM-yyyy, not ISO instants | Frontend not running | SKIP | none |
| UT-12 | Empty historical window shows empty chart without fabricated timestamps | error | P2 | Empty chart with no-data message, no fabricated timestamps | Frontend not running | SKIP | none |
| UT-13 | Simulated chart classification still works | regression | P1 | buyer_control label appears with valid confidence score | Frontend not running | SKIP | none |
| UT-14 | Historical watch resolves correct date window, no UTC shift | regression | P1 | Leftmost bar at 08-01-2024 09:30, no UTC shift | Frontend not running | SKIP | none |
| UT-15 | Native date picker is NOT present | ux | P2 | Plain text input, no calendar popup | Frontend not running | SKIP | none |
| UT-16 | Simulated and historical chart date format is consistent | ux | P2 | Both charts use dd-MM-yyyy HH:mm:ss on time axis | Frontend not running | SKIP | none |

---

## Passed Tests

None.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-01 — Home cockpit loads without errors
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-02 — Simulated chart axis shows synthetic session-clock times
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-03 — Historical chart axis shows real market clock times
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-04 — Crosshair tooltip shows true clock time on hover
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-05 — Tape-state marker labels show true clock time
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-06 — Bar-size switcher preserves real-clock time axis
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-07 — Historical date input accepts valid dd-MM-yyyy entry
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-08 — Historical date input rejects impossible date with inline validation
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-09 — Historical date input rejects malformed entry with inline validation
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-10 — Market-status next-open time shows dd-MM-yyyy HH:mm UTC format
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-11 — Watched-source descriptor shows dd-MM-yyyy dates
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-12 — Empty historical window shows empty chart without fabricated timestamps
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-13 — Simulated chart classification still works
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-14 — Historical watch resolves correct date window, no UTC shift
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-15 — Native date picker is NOT present
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-16 — Simulated and historical chart date format is consistent
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

---

## Environment

- **Frontend URL:** http://localhost:3650
- **Browser:** Chrome via MCP (not used — frontend unavailable)
- **Test Date:** 2026-06-09
- **Evidence directory:** `reports/qa/goal-i_will_be_super_rich-iter-12-evidence/` (not created — no tests ran)
