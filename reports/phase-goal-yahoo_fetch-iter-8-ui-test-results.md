# UI Test Results (merged)

**Date:** 2026-07-12
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 6/6 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-04 | Real S/R levels and confluence zones on real Yahoo bars | regression | P1 | Journey replays end-to-end via the deterministic script; all expects hold | **Not browser-driven by this agent** (per dispatch: verified separately). `runs/goal-session-yahoo_fetch/journey-scripts/J-04.json` replayed by `demo_runner.py` (`reports/phase-goal-yahoo_fetch-iter-8-regression-replay-results.md`, dated 2026-07-12): navigated `/structure` (expect "Fetch from Yahoo Finance"), filled Symbol=AAPL + As-of=2026-06-05T00:00:00Z, clicked Load, expect "Confluence zones" — all held | PASS | `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-04-verify.png` |
| UT-J-05 | Fetch from the app — the Structure page fetch control with "Yahoo Finance" provenance | regression | P1 | Journey replays end-to-end via the deterministic script; all expects hold | **Not browser-driven by this agent** (per dispatch: verified separately). `runs/goal-session-yahoo_fetch/journey-scripts/J-05.json` replayed by `demo_runner.py` (same replay report): navigated `/structure`, filled Symbol=AAPL, filled Start=2026-06-05T00:00:00Z, clicked Load, expect the `feed-basis-label` testid present — all held | PASS | `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-05-verify.png` |
| UT-J-01 | Fetch real historical bars from Yahoo Finance, keyless | regression | P1 | A stored `feed="yahoo"` series is fetchable/readable with no credentials; provenance singly-owned and visible; no fabricated data | Filled Fetch panel (Symbol=AAPL, Timeframe=1d, Start=2026-06-01T00:00:00Z, End=2026-06-04T00:00:00Z), clicked "Fetch from Yahoo Finance". Page rendered a "feed / **Yahoo Finance**" badge, a real candlestick "PRICE CHART — S/R LEVELS" section, and caption "Candles: 5m series (234 of 2028 recorded bars, as of the query time)." No fabricated/placeholder text, no error. `GET /research/bars` before/after confirms the served series (`89a829f7c3b9`) was NOT newly created — `created_utc` unchanged at `2026-07-10T14:27:41.881667Z`, AAPL/1d count unchanged at 4 | PASS | `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-01-result.png` |
| UT-J-02 | The full timeframe set, including honestly-resampled 4h | regression | P1 | All six timeframes (1w,1d,4h,1h,5m,1m) real and offered; 4h present, never fabricated, and actively used in real structure output | Live-read the `<select data-testid="fetch-timeframe-select">`: options exactly `Choose…, 1w, 1d, 4h, 1h, 5m, 1m` — the full real timeframe set, no more no less. The rendered 16-zone confluence table cited real entries from four different stored timeframes together: `1d` (`prior-period-extreme`), `1h`/`4h`/`5m` (`swing-pivot`) — e.g. zone 6 (price 308.85, `4h swing-pivot`) and zone 16 (price 316.94, `4h swing-pivot`) — proving `4h` is genuinely stored and actively feeding real structure, not merely an offered-but-unused option | PASS | `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-01-result.png` |
| UT-J-03 | Quick reuse — store-first fetch backed by a derived SQLite index | regression | P1 | A repeat fetch of an already-stored window is served from storage with no network call, no duplicate/conflict error, and creates no new record | Clicked "Fetch from Yahoo Finance" again with identical AAPL/1d/2026-06-01→2026-06-04 fields unchanged. Button transiently read "Fetching…" (disabled) then reverted to idle ("Fetch from Yahoo Finance", enabled) by the next check; word-boundary regex scan of `document.body.innerText` for the words conflict, duplicate, "already exists", failed, and error found zero matches; full chart + all 16 zones re-rendered correctly. `GET /research/bars?symbol=AAPL&timeframe=1d` before/after both clicks: still exactly 4 series, target series `created_utc` timestamp byte-identical — proves no new write occurred either time | PASS | `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-03-result.png` |
| UT-J-06 | The foundation is unchanged (regression sentinel) | regression | P1 | Cockpit/Journal/Studies/Performance render as before; the fixed `/studies` assertion target is genuinely static; pinned `config_fingerprint` visible | Navigated `/` → "No ticker watched" found. Navigated `/journal` → "SIM-BUYER" found. Navigated `/studies` → "Replay studies" found, AND confirmed present as `<h1 data-testid="studies-title">Replay studies</h1>` in the raw HTML captured immediately after `navigate` (before any explicit wait) — proving it is a genuinely static, always-present target, not an async-timing gamble. Navigated `/performance` → "4d665603569b9dbf" found | PASS | `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-06-studies.png`, `reports/qa/goal-yahoo_fetch-iter-8-evidence/J-06-performance.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-12

