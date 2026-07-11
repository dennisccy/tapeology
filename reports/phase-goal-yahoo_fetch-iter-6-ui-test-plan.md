# Phase goal-yahoo_fetch-iter-6 — UI Test Plan

**Phase:** goal-yahoo_fetch-iter-6
**Date:** 2026-07-11
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301

---

## Context: this is a re-evidencing pass, not new UI

Per `reports/phase-goal-yahoo_fetch-iter-6-ui-surface-map.md`, **zero product source changed this
iteration** (`git diff --stat HEAD -- apps/` is empty). Every surface below already shipped in iter-5
and is byte-identical today. This plan exists to drive the same already-built `/structure` fetch
control end-to-end and land the two pieces of browser evidence J-05 was still missing:

1. A **clean, unoccluded** "Yahoo Finance" provenance badge (UT-03).
2. A **browser-captured honest empty state** for a symbol with zero stored bars (UT-06).

All test data below — symbol `AAPL`, timeframe `1d`, window `2026-06-01T00:00:00Z`–
`2026-06-04T00:00:00Z`, and the no-data symbol `TSLA` — is the exact combination already confirmed
present/absent in this environment by the dev handoff (`docs/handoffs/goal-yahoo_fetch-iter-6-dev.md`)
and the prior QA pass (`reports/qa/goal-yahoo_fetch-iter-6-qa.md`, which screenshot-captured this same
flow successfully). No data seeding is required to execute this plan.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/structure` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend is running at http://localhost:3301
- Backend is running at http://localhost:8301
- No login is required — this app has no authentication gate

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Structure" is visible near the top of the page
- Below it, a sentence beginning "Fetch real historical bars from Yahoo Finance (keyless)…" is visible
- Below that, a smaller line of text beginning "One explicit write action — fetching bars from Yahoo
  Finance below — everything else on this page is read-only…" is visible
- A panel titled "Fetch from Yahoo Finance" is visible, containing: a "Symbol" field, a "Timeframe"
  dropdown showing "Choose…", a "Start (UTC, ISO-8601)" field, an "End (UTC, ISO-8601)" field, and a
  "Fetch from Yahoo Finance" button
- Below that panel, a second, separate form is visible containing: a "Symbol" field, an "As-of (UTC,
  ISO-8601)" field, and a "Load" button
- Below that, the text "Choose a symbol and an as-of time, then Load, to see its S/R levels and
  confluence zones." is visible
- No blank/white page, no red error banner, no browser console errors

---

### UT-02 — Fetching a Yahoo bar series renders chart, S/R levels, and confluence zones (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- UT-01 passed
- A bar series for symbol `AAPL`, timeframe `1d`, covering at least `2026-06-01T00:00:00Z`–
  `2026-06-04T00:00:00Z` is already recorded and indexed in this environment (confirmed by the dev
  handoff and QA pass — no seeding action needed)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. In the "Fetch from Yahoo Finance" panel, type `AAPL` into the "Symbol" field
3. Select `1d` from the "Timeframe" dropdown
4. Type `2026-06-01T00:00:00Z` into the "Start (UTC, ISO-8601)" field — this matches the field's own
   grey placeholder text, but you must actually type it; the placeholder alone is not a submitted
   value
5. Type `2026-06-04T00:00:00Z` into the "End (UTC, ISO-8601)" field — same note, type it rather than
   trusting the placeholder
6. Click the "Fetch from Yahoo Finance" button

**Expected Result:**
- The button briefly reads "Fetching…" then returns to reading "Fetch from Yahoo Finance" within
  about 1 second (this is a store-first serve from local storage, not a live network round-trip to
  Yahoo)
- No amber error panel appears below the form
- A "Price chart — S/R levels" panel appears showing a real candlestick chart (visible candle bodies
  and wicks, at least 3 candles) with at least two dashed horizontal level lines drawn across it
- Directly below it, a "Confluence zones" panel appears showing at least one zone entry with a badge
  reading "Class A", "Class B", or "Class C" next to text reading "zone 1 · score" followed by a
  number
- A caption below the chart reads "Candles: `<timeframe>` series (X of Y recorded bars, as of the
  query time). Level lines span every recorded timeframe." (`<timeframe>` will be one of
  `1w`/`1d`/`4h`/`1h`/`5m`/`1m` — the exact series the app picks to represent the symbol; any of
  these is correct as long as the sentence pattern and numbers X/Y are present)

---

### UT-03 — Clean, unoccluded "Yahoo Finance" provenance badge (ux) — defining evidence for this iteration

**Type:** ux
**Priority:** P1 *(elevated from the usual P2/P3 for ux tests — this is the specific evidence gap this
iteration exists to close; see the phase spec's Definition of Done)*
**Surface:** `/structure`

**Preconditions:**
- UT-02 passed (chart is currently rendered for `AAPL`)
- Immediately after the fetch in UT-02, the SECOND form's "Symbol" field (the one next to the "Load"
  button — not the "Fetch from Yahoo Finance" field you just typed into) auto-fills with "AAPL" and its
  suggestions dropdown may pop open on its own. This is expected, pre-existing behavior — dismissing it
  is exactly what this test does.

**Steps:**
1. Look at the second form below the "Fetch from Yahoo Finance" panel — if a dropdown list of symbol
   suggestions is currently open beneath its "Symbol" field, note that it visually overlaps the area
   directly above the chart
2. Click the page heading text "Structure" at the very top of the page (this is outside every symbol
   field's own box, so it safely closes any open suggestion dropdown without changing any field's
   value)
3. Look at the small chip directly above the candlestick chart

**Expected Result:**
- Any suggestion dropdown that had been open is now fully closed — no floating list box remains
  visible anywhere on the page
- A small dark chip reading "feed" followed by "Yahoo Finance" in bold monospace text is fully visible
  directly above the chart
- No dropdown, list, or any other element overlaps or covers any part of this chip — every letter of
  "Yahoo Finance" is legible

---

### UT-04 — "Fetch from Yahoo Finance" button stays disabled until all four fields are filled (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- A fresh, unmodified load of `/structure` (reload the page first if fields already have values from a
  prior test)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Look at the "Fetch from Yahoo Finance" button without touching any field
3. Type `AAPL` into the "Symbol" field, then look at the button again
4. Select `1d` from the "Timeframe" dropdown, then look at the button again
5. Type `2026-06-01T00:00:00Z` into the "Start (UTC, ISO-8601)" field, then look at the button again
6. Type `2026-06-04T00:00:00Z` into the "End (UTC, ISO-8601)" field, then look at the button again

**Expected Result:**
- At step 2: the button appears faded/dimmed (reduced opacity) and clicking it does nothing — no
  "Fetching…" state, no chart change
- At steps 3, 4, and 5: the button still appears faded/dimmed — it stays disabled as long as any one
  of the four fields is empty
- At step 6 (all four fields now filled): the button becomes fully opaque/solid, and clicking it now
  triggers the "Fetching…" state described in UT-02

---

### UT-05 — Invalid date range shows an honest error, nothing fabricated (error)

**Type:** error
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- `/structure` is loaded

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type `AAPL` into the "Symbol" field of the "Fetch from Yahoo Finance" panel
3. Select `1d` from the "Timeframe" dropdown
4. Type `2026-06-04T00:00:00Z` into the "Start (UTC, ISO-8601)" field (the LATER date, deliberately
   placed in Start)
5. Type `2026-06-01T00:00:00Z` into the "End (UTC, ISO-8601)" field (the EARLIER date, deliberately
   placed in End)
6. Click the "Fetch from Yahoo Finance" button

**Expected Result:**
- An amber-colored panel appears below the form showing the exact text "end must be after start"
- Directly below that line, the fixed text "Nothing cached and nothing fabricated is shown in its
  place." appears
- No chart, candle, or level line appears or changes anywhere on the page as a result of this click
- Whatever the Levels & Zones section below was showing before this click (e.g., the idle prompt, or a
  previously loaded chart) remains unchanged

---

### UT-06 — Honest empty state for a symbol with zero stored bars (error) — defining evidence for this iteration

**Type:** error
**Priority:** P1 *(elevated — the second piece of browser evidence this iteration exists to land)*
**Surface:** `/structure`

**Preconditions:**
- Symbol `TSLA` has zero recorded bar series in this environment (confirmed via the dev handoff:
  `GET /research/bars?symbol=TSLA` returns an empty list). Optionally verify yourself by opening
  `http://localhost:8301/research/bars?symbol=TSLA` in a new browser tab and confirming the JSON shows
  `"bar_series":[]`. If a future environment reset has caused TSLA to have data, substitute any other
  symbol confirmed empty by the same check.

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. In the SECOND form (the one with the "Load" button — NOT the "Fetch from Yahoo Finance" panel above
   it), type `TSLA` into the "Symbol" field
3. Type `2026-06-05T00:00:00Z` into the "As-of (UTC, ISO-8601)" field
4. Click the "Load" button

**Expected Result:**
- The text "No bar series recorded for TSLA." appears in the Levels & Zones section
- Directly below it, the text "Recording historical bars needs provider credentials." appears
- No chart, no candles, no level line, no "Yahoo Finance" badge, and no confluence zone table appear
  anywhere on the page
- This message renders on a plain neutral background — visibly distinct from a loading spinner and
  from the amber error panel seen in UT-05

---

### UT-07 — Pre-existing "Load" workflow still works for an already-recorded symbol (regression)

**Type:** regression
**Priority:** P1 *(this is the positive control for UT-06 — confirming the Load form works normally
for valid input rules out "the form itself is broken" as an alternative explanation for UT-06's empty
result)*
**Surface:** `/structure`

**Preconditions:**
- Symbol `AAPL` has at least one recorded bar series (true after UT-02, and true independently of this
  iteration regardless)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. In the SECOND form (the one with the "Load" button), type `AAPL` into the "Symbol" field
3. Type `2026-06-05T00:00:00Z` into the "As-of (UTC, ISO-8601)" field
4. Click the "Load" button

**Expected Result:**
- A real candlestick chart renders in a "Price chart — S/R levels" panel, with at least two dashed
  level lines
- A "Confluence zones" panel renders below it with at least one zone entry
- This is the same read-only Load workflow that existed before the "Fetch from Yahoo Finance" panel
  was added — it is unaffected by this iteration's evidence-capture work

---

### UT-08 — Repeating an already-fetched window re-serves instantly, not a duplicate-conflict error (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- UT-02 already completed earlier in this same browser session, without an intervening page refresh
  (the "Fetch from Yahoo Finance" form still shows `AAPL` / `1d` / `2026-06-01T00:00:00Z` /
  `2026-06-04T00:00:00Z`)

**Steps:**
1. Without changing any field, click the "Fetch from Yahoo Finance" button a second time

**Expected Result:**
- The button briefly reads "Fetching…" then returns to reading "Fetch from Yahoo Finance", just as
  quickly as the first time (well under 1 second — still a store-first serve, not a live network call)
- The chart, level lines, and confluence zones from UT-02 remain visible and correct
- No error panel appears — specifically, no text mentioning "409", "conflict", "duplicate", or
  "already exists" appears anywhere on the page

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Page loads cleanly | smoke | P1 | `/structure` |
| UT-02 | Fetch renders chart/levels/zones | happy-path | P1 | `/structure` |
| UT-03 | Clean unoccluded "Yahoo Finance" badge | ux | P1 | `/structure` |
| UT-04 | Fetch button disabled until all fields filled | validation | P2 | `/structure` |
| UT-05 | Invalid date range shows honest error | error | P2 | `/structure` |
| UT-06 | Honest empty state for TSLA (zero bars) | error | P1 | `/structure` |
| UT-07 | Pre-existing Load workflow still works | regression | P1 | `/structure` |
| UT-08 | Repeat fetch re-serves instantly, no duplicate error | regression | P2 | `/structure` |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-03 and UT-06 are the two tests this
iteration exists to land — if either cannot be captured cleanly, J-05 cannot flip to `passing`
regardless of the other six tests' results.
