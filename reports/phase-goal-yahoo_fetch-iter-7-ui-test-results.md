# UI Test Results (merged)

**Date:** 2026-07-12
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 5/6 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-04 | Real S/R levels and confluence zones on real Yahoo bars | regression | P1 | Journey replays end-to-end via the deterministic script; all expects hold | **Not browser-driven by this agent** (per dispatch: verified separately). `runs/goal-session-yahoo_fetch/journey-scripts/J-04.json` was replayed by `demo_runner.py` (dated 2026-07-12): navigated to `/structure` (expect "Fetch from Yahoo Finance"), filled Symbol=AAPL + As-of=2026-06-05T00:00:00Z on the read-only Load form, clicked Load, expect "Confluence zones" — all held | PASS | `reports/qa/goal-yahoo_fetch-iter-7-evidence/J-04-verify.png` (see `reports/phase-goal-yahoo_fetch-iter-7-regression-replay-results.md`) |
| UT-J-05 | Fetch from the app — the Structure page fetch control with "Yahoo Finance" provenance | regression | P1 | Journey replays end-to-end via the deterministic script; all expects hold | **Not browser-driven by this agent** (per dispatch: verified separately). `runs/goal-session-yahoo_fetch/journey-scripts/J-05.json` replayed by `demo_runner.py` (dated 2026-07-12): navigated to `/structure`, filled Symbol=AAPL, filled Start(as-of)=2026-06-05T00:00:00Z, clicked Load, expect the `feed-basis-label` testid present — all held | PASS | `reports/qa/goal-yahoo_fetch-iter-7-evidence/J-05-verify.png` (see `reports/phase-goal-yahoo_fetch-iter-7-regression-replay-results.md`) |
| UT-J-06 | The foundation is unchanged (regression sentinel) | regression | P1 | Journey replays end-to-end via the deterministic script; all expects hold (Cockpit/Journal/Studies/Performance render as before; pinned `config_fingerprint` visible) | **Not browser-driven by this agent** (per dispatch: verified separately). `runs/goal-session-yahoo_fetch/journey-scripts/J-06.json` replayed by `demo_runner.py` (dated 2026-07-12): step 3 (`goto /studies`, expect "Absorption reversal") **FAILED** — "did not appear". See Failed Tests section below for this row's diagnostic note | FAIL | `reports/qa/goal-yahoo_fetch-iter-7-evidence/J-06-verify.png` (see `reports/phase-goal-yahoo_fetch-iter-7-regression-replay-results.md`) |
| UT-J-01 | Fetch real historical bars from Yahoo Finance, keyless | regression | P1 | A stored `feed="yahoo"` series is fetchable/readable with no credentials; provenance singly-owned and visible; no fabricated data | Filled Fetch panel (Symbol=AAPL, Timeframe=1d, Start=2026-06-01T00:00:00Z, End=2026-06-04T00:00:00Z) and clicked "Fetch from Yahoo Finance"; page rendered a "feed / **Yahoo Finance**" badge, a real candlestick "PRICE CHART — S/R LEVELS" section, and caption "Candles: 5m series (234 of 2028 recorded bars, as of the query time)." No fabricated/placeholder text, no error | PASS | `reports/qa/goal-yahoo_fetch-iter-7-evidence/UT-J-01-result.png` |
| UT-J-02 | The full timeframe set, including honestly-resampled 4h | regression | P1 | All six timeframes (1w,1d,4h,1h,5m,1m) real and fetchable; 4h present, never fabricated, and actively used | Timeframe `<select data-testid="fetch-timeframe-select">` confirmed exactly `Choose…,1w,1d,4h,1h,5m,1m` (verified both from static HTML and a live `element.value` eval read to rule out an attribute/property false-negative); the rendered 16-zone confluence table cited real `1d`/`1h`/`4h`/`5m` entries together in the same computation — e.g. zone 6 (price 308.85, `4h swing-pivot`) and zone 16 (price 316.94, `4h swing-pivot`) — proving `4h` data is genuinely stored and actively feeding real structure, not merely offered | PASS | `reports/qa/goal-yahoo_fetch-iter-7-evidence/UT-J-01-result.png` |
| UT-J-03 | Quick reuse — store-first fetch backed by a derived SQLite index | regression | P1 | A repeat fetch of an already-stored window is served from storage with no network call and no duplicate-conflict error | Clicked "Fetch from Yahoo Finance" again with the identical AAPL/1d/2026-06-01→2026-06-04 fields unchanged; button transiently read "Fetching…" then had already reverted to idle with the full chart + all 16 zones re-rendered by the very next tool call; a precise regex scan of `document.body.innerText` for the standalone words "conflict"/"duplicate"/"already exists"/"failed" found zero matches (a naive raw "409" substring search was a false positive traced to the decimal price `312.3514099121094`, confirmed by inspecting the exact surrounding text — not an HTTP 409) | PASS | `reports/qa/goal-yahoo_fetch-iter-7-evidence/UT-J-03-result.png` |

## Failed Tests

### UT-J-06 — The foundation is unchanged (regression sentinel)

**Verdict:** FAIL
**Failure:** **Not browser-driven by this agent** (per dispatch: verified separately). `runs/goal-session-yahoo_fetch/journey-scripts/J-06.json` replayed by `demo_runner.py` (dated 2026-07-12): step 3 (`goto /studies`, expect "Absorption reversal") **FAILED** — "did not appear". See Failed Tests section below for this row's diagnostic note
**Evidence:** ``reports/qa/goal-yahoo_fetch-iter-7-evidence/J-06-verify.png` (see `reports/phase-goal-yahoo_fetch-iter-7-regression-replay-results.md`)`

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-12

