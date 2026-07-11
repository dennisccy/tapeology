# Phase goal-yahoo_fetch-iter-6 — UI Test Results

**Phase:** goal-yahoo_fetch-iter-6
**Date:** 2026-07-11
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 8/8 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/structure` loads without errors | smoke | P1 | Heading, framing copy, fetch panel, load form, idle prompt all visible; no blank page/errors | All elements rendered exactly as specified; console shows only the standard React DevTools info line, no errors | PASS | `reports/qa/goal-yahoo_fetch-iter-6-evidence/UT-01-result.png` |
| UT-02 | Fetching a Yahoo bar series renders chart, S/R levels, confluence zones | happy-path | P1 | Button reverts from "Fetching…" within ~1s; real candlestick chart with ≥2 level lines; confluence zones with class badges; caption with X of Y bars | Button read "Fetch from Yahoo Finance" (reverted); chart rendered with multiple dashed level lines; 16 confluence zones (Class A/B/C) with scores; caption read "Candles: 5m series (234 of 2028 recorded bars, as of the query time). Level lines span every recorded timeframe." | PASS | `reports/qa/goal-yahoo_fetch-iter-6-evidence/UT-02-result.png` |
| UT-03 | Clean, unoccluded "Yahoo Finance" provenance badge | ux | P1 | Outside click on "Structure" heading closes the SymbolSearch dropdown; badge "feed Yahoo Finance" fully legible with no overlap | Dropdown fully closed after clicking the heading; chip "feed **Yahoo Finance**" fully visible directly above the chart with zero overlapping elements | PASS | `reports/qa/goal-yahoo_fetch-iter-6-evidence/UT-03-result.png` |
| UT-04 | Fetch button disabled until all four fields filled | validation | P2 | Button faded/disabled through steps with 0-3 fields filled; fully enabled only once all 4 are filled | Verified via computed style at each step: 0 fields → `disabled:true, opacity:0.4, cursor:not-allowed`; +Symbol → same; +Timeframe → same; +Start → same; +End (all 4) → `disabled:false, opacity:1, cursor:pointer` | PASS | `reports/qa/goal-yahoo_fetch-iter-6-evidence/UT-04-empty.png`, `UT-04-enabled.png` |
| UT-05 | Invalid date range shows an honest error | error | P2 | Amber panel with "end must be after start"; "Nothing cached and nothing fabricated..." below it; no chart appears/changes | Amber-bordered panel appeared with exact text "end must be after start" and "Nothing cached and nothing fabricated is shown in its place." directly below; Levels & Zones section stayed on its unchanged idle prompt | PASS | `reports/qa/goal-yahoo_fetch-iter-6-evidence/UT-05-result.png` |
| UT-06 | Honest empty state for a symbol with zero stored bars (TSLA) | error | P1 | "No bar series recorded for TSLA." + "Recording historical bars needs provider credentials."; no chart/badge/zones; neutral background | Both lines rendered exactly as specified on a plain neutral panel (visibly distinct from the UT-05 amber panel); no chart, candle, level line, badge, or zone table anywhere on the page (confirmed via full-page text extraction) | PASS | `reports/qa/goal-yahoo_fetch-iter-6-evidence/UT-06-result.png` |
| UT-07 | Pre-existing "Load" workflow still works for an already-recorded symbol | regression | P1 | Real candlestick chart + level lines + confluence zones panel render for AAPL via the Load form | Chart rendered with dashed level lines; "Confluence zones" panel rendered below with Class A/B/C entries — confirms the Load form works normally for valid input (positive control for UT-06) | PASS | `reports/qa/goal-yahoo_fetch-iter-6-evidence/UT-07-result.png` |
| UT-08 | Repeating an already-fetched window re-serves instantly | regression | P2 | Button reverts from "Fetching…" quickly (well under 1s); chart/zones remain correct; no "409"/"conflict"/"duplicate"/"already exists" text anywhere | Button already read "Fetch from Yahoo Finance" by the time of the very next tool call (confirming near-instant store-first resolve); identical chart + all 16 confluence zones re-rendered correctly; full-page text extraction confirmed zero occurrences of "409", "conflict", "duplicate", or "already exists" | PASS | `reports/qa/goal-yahoo_fetch-iter-6-evidence/UT-08-result.png` |

---

## Passed Tests

### UT-01 — `/structure` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-6-evidence/UT-01-result.png`
- Navigated to `http://localhost:3301/structure`. Heading "Structure" visible; framing sentence "Fetch real historical bars from Yahoo Finance (keyless)…" and the smaller "One explicit write action — fetching bars from Yahoo Finance below — everything else on this page is read-only…" line both present. "Fetch from Yahoo Finance" panel visible with Symbol / Timeframe ("Choose…") / Start / End fields and the submit button. Second form (Symbol / As-of / Load) visible below it, followed by the idle prompt "Choose a symbol and an as-of time, then Load, to see its S/R levels and confluence zones." No blank page, no error banner. Enabled console logging and re-loaded the page separately — only a standard React DevTools info-level message logged, zero errors/warnings.

### UT-02 — Fetching a Yahoo bar series renders chart, S/R levels, and confluence zones
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-6-evidence/UT-02-result.png`
- Typed `AAPL` into Symbol, selected `1d` in the timeframe dropdown, typed `2026-06-01T00:00:00Z` / `2026-06-04T00:00:00Z` into Start/End, clicked "Fetch from Yahoo Finance". Full-page text extraction confirmed: heading "PRICE CHART — S/R LEVELS", a "feed Yahoo Finance" badge, a caption reading "Candles: 5m series (234 of 2028 recorded bars, as of the query time). Level lines span every recorded timeframe.", and a "CONFLUENCE ZONES" section with 16 zone entries carrying Class A/B/C badges and numeric scores (e.g. "Class A / zone 1 · score 12"). No amber error panel appeared. Button text had already reverted to "Fetch from Yahoo Finance" by the time of the confirming screenshot.

### UT-03 — Clean, unoccluded "Yahoo Finance" provenance badge
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-6-evidence/UT-03-result.png`
- Immediately following UT-02's fetch, the second form's Symbol field had auto-filled "AAPL" with its suggestions dropdown open, visually overlapping the area above the chart (confirmed pre-existing/expected behavior per the test's preconditions). Clicked the "Structure" `<h1>` heading (outside any field's own box). The dropdown fully closed — no floating list box remained anywhere on the page. The small dark chip reading "feed" and, in bold monospace, "**Yahoo Finance**" was fully visible directly above the candlestick chart with no dropdown, list, or any other element overlapping any part of it. This is the defining evidence item for this iteration (J-05's provenance badge, previously occluded in every iter-5 screenshot per defect F1).

### UT-04 — "Fetch from Yahoo Finance" button stays disabled until all four fields are filled
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-6-evidence/UT-04-empty.png`, `reports/qa/goal-yahoo_fetch-iter-6-evidence/UT-04-enabled.png`
- Reloaded `/structure` fresh. Verified button computed state at each incremental fill step via the button's `disabled` property and computed `opacity`/`cursor` style:
  - 0 fields filled: `disabled=true`, `opacity=0.4`, `cursor=not-allowed` (screenshot: `UT-04-empty.png`)
  - +Symbol (`AAPL`) only: `disabled=true`, `opacity=0.4`
  - +Timeframe (`1d`): `disabled=true`, `opacity=0.4`
  - +Start (`2026-06-01T00:00:00Z`): `disabled=true`, `opacity=0.4`
  - +End (`2026-06-04T00:00:00Z`, all 4 fields filled): `disabled=false`, `opacity=1`, `cursor=pointer` (screenshot: `UT-04-enabled.png`)
- Matches the expected result exactly: faded/disabled through partial fill, fully opaque/clickable only once complete.

### UT-05 — Invalid date range shows an honest error, nothing fabricated
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-6-evidence/UT-05-result.png`
- Reloaded `/structure` fresh. Filled Symbol=`AAPL`, Timeframe=`1d`, Start=`2026-06-04T00:00:00Z` (later date, deliberately in Start), End=`2026-06-01T00:00:00Z` (earlier date, deliberately in End), clicked "Fetch from Yahoo Finance". An amber/orange-bordered panel appeared showing the exact text "end must be after start", with the fixed line "Nothing cached and nothing fabricated is shown in its place." directly below it. The Levels & Zones section below remained on its unchanged idle prompt ("∅ Choose a symbol and an as-of time, then Load…") — no chart, candle, or level line appeared or changed as a result of the click.

### UT-06 — Honest empty state for a symbol with zero stored bars
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-6-evidence/UT-06-result.png`
- Independently confirmed via `curl http://localhost:8301/research/bars?symbol=TSLA` → `{"bar_series":[],"integrity_errors":[]}` before starting (zero recorded series for TSLA in this environment). Reloaded `/structure` fresh. In the second ("Load") form, typed `TSLA` into Symbol, `2026-06-05T00:00:00Z` into As-of, clicked "Load". The text "No bar series recorded for TSLA." appeared, with "Recording historical bars needs provider credentials." directly below it. Full-page text extraction confirmed no chart, no candles, no level line, no "Yahoo Finance" badge, and no confluence zone table rendered anywhere on the page. The panel renders on the same plain neutral background used by the idle prompt — visibly distinct from the loading state and from the amber error panel seen in UT-05. This is the second defining evidence item for this iteration (browser-captured TC-11, previously unit-only).

### UT-07 — Pre-existing "Load" workflow still works for an already-recorded symbol
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-6-evidence/UT-07-result.png`
- In the same session (immediately following UT-06), cleared the Symbol field and typed `AAPL` (a symbol with recorded bars from UT-02's fetch), set As-of=`2026-06-05T00:00:00Z`, clicked "Load". A real candlestick chart rendered in the "Price chart — S/R levels" panel with dashed level lines, and the "Confluence zones" panel rendered below with populated Class A/B/C zone entries — the same read-only Load workflow that pre-dates this iteration's fetch-panel work, confirmed unaffected. This serves as the positive control ruling out "the form itself is broken" as an explanation for UT-06's empty result.

### UT-08 — Repeating an already-fetched window re-serves instantly, not a duplicate-conflict error
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-6-evidence/UT-08-result.png`
- Note on precondition: the test plan's stated precondition ("UT-02 completed earlier in this same browser session, without an intervening page refresh") was not literally preserved, because UT-04/UT-05/UT-06 each intentionally reloaded the page to establish clean starting states for their own checks. To still exercise the exact behavior under test — repeating an identical, already-recorded fetch tuple — the Symbol/Timeframe/Start/End fields were refilled with the identical `AAPL` / `1d` / `2026-06-01T00:00:00Z` / `2026-06-04T00:00:00Z` tuple from UT-02 and "Fetch from Yahoo Finance" was clicked again. This is a superset of the original scenario (it re-confirms store-first serve survives a full page reload, not only a same-session repeat click) and directly validates the same server-side contract (repeat window POST → 200 store-first, no 409).
- Result: the button already read "Fetch from Yahoo Finance" (not stuck on "Fetching…") by the very next tool call, confirming a near-instant resolve. The chart and all 16 confluence zones re-rendered identically to UT-02's result. Full-page text extraction confirmed zero occurrences of "409", "conflict", "duplicate", or "already exists" anywhere on the page.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-11
- **Evidence directory:** `reports/qa/goal-yahoo_fetch-iter-6-evidence/`
- **Preconditions confirmed before testing:** frontend returned HTTP 200 at `/structure`; backend returned HTTP 200 at `/health`; `GET /research/bars?symbol=TSLA` confirmed `bar_series: []` (zero-data fixture for UT-06 valid).
