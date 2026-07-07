# Phase goal-structure_ui-iter-3 — UI Test Results

**Phase:** goal-structure_ui-iter-3
**Date:** 2026-07-07
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 0/26 tests passed (26 skipped)

**Reason for SKIPPED verdict:** The frontend was not available at the dispatched test URL
(`http://localhost:3301`) at the time this QA run started, and the dispatch instructions explicitly
stated "Frontend available: no ... Do NOT attempt to run browser tests." A precondition curl check
confirmed both services unreachable before any test execution was attempted (see Environment section
below). No browser automation of any kind was performed; all 26 test cases from
`reports/phase-goal-structure_ui-iter-3-ui-test-plan.md` are recorded as SKIPPED with this single
root cause.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Structure page loads with 3 sections | smoke | P1 | Page renders Levels & Zones, Registry, Comparison panels in order; no error/blank | Not executed — frontend not running | SKIP | none |
| UT-02 | Comparison section static elements render | smoke | P1 | Comparison panel shows disclaimer, Champion/Founding boxes, dataset dropdown, disabled Run button | Not executed — frontend not running | SKIP | none |
| UT-03 | Dataset selector populates | smoke | P1 | Dropdown shows placeholder + one option per registered dataset, formatted `symbol · split · id-prefix` | Not executed — frontend not running | SKIP | none |
| UT-04 | Full comparison run end to end | happy-path | P1 | Run button becomes "Running…", both result cards appear and resolve from Queued/Running to a finished state | Not executed — frontend not running | SKIP | none |
| UT-05 | Side-by-side aggregates render | happy-path | P1 | Both finished cards show all 5 fields (n, net R, net $, win_rate, max drawdown) with real or honest-null values | Not executed — frontend not running | SKIP | none |
| UT-06 | Per-class A/B/C table renders | happy-path | P1 | Each card shows a 3-row Class A/B/C table with n/net R/net $/sample columns | Not executed — frontend not running | SKIP | none |
| UT-07 | Register line renders | happy-path | P1 | Both cards show the exact verbatim register string (fuller phrase, not the shorter paraphrase) | Not executed — frontend not running | SKIP | none |
| UT-08 | Founding baseline row renders | happy-path | P1 | Founding-baseline box shows either a populated row or the exact "No founding row yet" text | Not executed — frontend not running | SKIP | none |
| UT-09 | Champion panel read-only v1/default | happy-path | P1 | Champion box shows "v1"/"default", matches Registry badge, no interactive control | Not executed — frontend not running | SKIP | none |
| UT-10 | Reference dataset honest non-survivor outcome | happy-path | P1 | structure_tape card shows insufficient-sample chip on all 3 classes and "no trades (n=0)"; champion unchanged | Not executed — frontend not running | SKIP | none |
| UT-11 | Run button disabled until dataset chosen | validation | P2 | Button inert with placeholder selected; clickable and starts run once a real dataset is chosen | Not executed — frontend not running | SKIP | none |
| UT-12 | No datasets registered empty state | error | P2 | Exact "No datasets registered." text plus hint; no dropdown/button rendered | Not executed — frontend not running | SKIP | none |
| UT-13 | Backend unreachable at page load | error | P2 | Dataset area shows unreachable message; Champion box shows "Champion not yet loaded..." | Not executed — frontend not running | SKIP | none |
| UT-14 | Backend failure on POST (run-error) | error | P2 | Amber panel with message ending "...could not be started."; no result/in-progress card | Not executed — frontend not running | SKIP | none |
| UT-15 | Backend unreachable mid-poll | error | P2 | "Backend unreachable while polling..." notice within ~700ms; last-known state stays visible; auto-recovers | Not executed — frontend not running | SKIP | none |
| UT-16 | Failed backtest distinct card | error | P2 | Rose-bordered card with "This backtest could not produce a result..." + backend error text; other side unaffected | Not executed — frontend not running | SKIP | none |
| UT-17 | Cancelled backtest distinct card | error | P2 | Card shows exact cancelled message; no aggregates/table/register for that side | Not executed — frontend not running | SKIP | none |
| UT-18 | J-01 Levels & Zones still works | regression | P1 | Chart with candles + dashed levels, zones table below, unaffected by new section | Not executed — frontend not running | SKIP | none |
| UT-19 | J-01 chart not occluded | regression | P1 | Chart stays interactive; no overlay/tooltip hidden; no visual overlap with Comparison section | Not executed — frontend not running | SKIP | none |
| UT-20 | J-02 Registry/champion still renders | regression | P1 | Two strategy cards (v1, structure_tape) + champion badge "v1"/"default", unchanged from pre-iter-3 | Not executed — frontend not running | SKIP | none |
| UT-21 | No champion testid collision | regression | P1 | Exactly one `champion-strategy` node and one `comparison-champion-strategy` node, both reading "v1" | Not executed — frontend not running | SKIP | none |
| UT-22 | 5-link nav intact | regression | P1 | Exactly 5 nav links: Cockpit, Journal, Studies, Performance, Structure | Not executed — frontend not running | SKIP | none |
| UT-23 | /performance unaffected | regression | P1 | Page loads normally with v1/default champion summary; no console errors | Not executed — frontend not running | SKIP | none |
| UT-24 | Header subtitle previews 3 sections | ux | P3 | Intro paragraph and disclaimer both name all three sections, not just Levels/Zones | Not executed — frontend not running | SKIP | none |
| UT-25 | Insufficient-sample chip clear | ux | P3 | Chip reads exact "insufficient sample (n < 5)" text, amber, next to real numbers | Not executed — frontend not running | SKIP | none |
| UT-26 | Comparison reachable in 1 click | ux | P3 | 1 click from home to /structure; Comparison section reachable by scroll alone, no hidden controls | Not executed — frontend not running | SKIP | none |

---

## Passed Tests

None — the frontend was unavailable for the entire QA window, so no test case reached execution.

---

## Failed Tests

None recorded. Per the browser-qa-agent rules, unavailability of the frontend is recorded as SKIPPED, never as FAIL.

---

## Skipped Tests

All 26 test cases below share the identical root cause and were not executed for any other reason.

### UT-01 — Structure page loads with 3 sections
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-02 — Comparison section static elements render
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-03 — Dataset selector populates
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-04 — Full comparison run end to end
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-05 — Side-by-side aggregates render
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-06 — Per-class A/B/C table renders
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-07 — Register line renders
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-08 — Founding baseline row renders
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-09 — Champion panel read-only v1/default
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-10 — Reference dataset honest non-survivor outcome
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-11 — Run button disabled until dataset chosen
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-12 — No datasets registered empty state
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-13 — Backend unreachable at page load
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-14 — Backend failure on POST (run-error)
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-15 — Backend unreachable mid-poll
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-16 — Failed backtest distinct card
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-17 — Cancelled backtest distinct card
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-18 — J-01 Levels & Zones still works
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-19 — J-01 chart not occluded
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-20 — J-02 Registry/champion still renders
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-21 — No champion testid collision
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-22 — 5-link nav intact
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-23 — /performance unaffected
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-24 — Header subtitle previews 3 sections
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-25 — Insufficient-sample chip clear
**Verdict:** SKIPPED
**Reason:** frontend not running

### UT-26 — Comparison reachable in 1 click
**Verdict:** SKIPPED
**Reason:** frontend not running

---

## Environment

- **Frontend URL:** http://localhost:3301 (dispatched target; unreachable — `curl -o /dev/null -w "%{http_code}"` returned no HTTP response / connection failed at precondition check)
- **Backend URL:** http://localhost:8301/health (also unreachable at precondition check, same connection failure)
- **Precondition check performed:** yes — `curl` against both URLs before any test execution; both failed to connect. Per dispatch instructions ("Frontend available: no ... Do NOT attempt to run browser tests"), no Chrome MCP session was opened and no browser automation was attempted.
- **Browser:** Chrome via MCP (not invoked this run)
- **Test Date:** 2026-07-07
- **Evidence directory:** `reports/qa/goal-structure_ui-iter-3-evidence/` (no new screenshots captured this run; the directory pre-existed with unrelated artifacts from a prior session and was not used as evidence for this report's verdict)
