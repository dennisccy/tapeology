# Phase goal-yahoo_fetch-iter-5 — UI Surface Map

**Phase:** goal-yahoo_fetch-iter-5
**Date:** 2026-07-10
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

`apps/frontend/lib/api.ts` (new `recordBarSeries()` helper) and `apps/frontend/lib/types.ts` (new `RecordBarSeriesResult` interface) are non-visual client plumbing with no independent screen presence — they are exercised entirely through the Row 1/Row 2 form and behavior below, so they do not get their own row.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/structure` | "Fetch from Yahoo Finance" form — Symbol field, Timeframe `<select>` (`data-testid="fetch-timeframe-select"`), Start input (`data-testid="fetch-start-input"`), End input (`data-testid="fetch-end-input"`), submit button (`data-testid="fetch-yahoo-button"`) | New form | J-05: added the page's one new explicit write action — a UI control to fetch real Yahoo bars, previously only reachable via a backend-only path | With all four fields empty, confirm the "Fetch from Yahoo Finance" button is disabled (greyed out, not clickable). Then set Symbol=`AAPL`, Timeframe=`1d`, Start=`2026-06-01T00:00:00Z`, End=`2026-07-09T23:59:59Z` (a window already fetched/stored in a prior run) and confirm the button becomes enabled. |
| `/structure` | Fetch submit → Levels & Zones render (reused `StructureChart` + level lines + confluence-zone table) | Changed behavior | A successful fetch now auto-populates the pre-existing read-only chart/levels/zone-table render path by internally re-using the existing "Load" logic — no second click needed | Click "Fetch from Yahoo Finance" with the pre-seeded `(AAPL, 1d, 2026-06-01T00:00:00Z, 2026-07-09T23:59:59Z)` tuple. Confirm the button label briefly reads "Fetching…", then — without touching the separate "Load" button below — confirm the price chart renders real candles, at least one dashed level line appears on the chart, and the confluence-zone table shows rows (e.g. a class badge such as "A" with a numeric score). |
| `/structure` | Provenance badge (`FeedBasisBadge`, new placement directly above the price chart) | New feature | J-05 requires an honest, data-driven stamp of the displayed series' data source | After the fetch in the row above succeeds, confirm a badge reading "Yahoo Finance" appears directly above the chart. Then reload `/structure` fresh (do not fetch or load anything) and confirm no badge is rendered anywhere on the page while it is in its idle state. |
| `/structure` | Fetch-error panel (`data-testid="fetch-yahoo-error"`) | New feature (honest error state) | A failed fetch must surface the backend's own specific reason, never a generic message or a silent no-op | Submit the fetch form with a Start/End window that has no Yahoo data available for the chosen symbol/timeframe (e.g. an end date before the start date, or a clearly out-of-range future window) and confirm an amber-bordered panel appears below the form showing a specific error sentence (not "something went wrong") plus the note "Nothing cached and nothing fabricated is shown in its place." Confirm the Levels & Zones section below is left untouched — no chart clears or appears. |
| `/structure` | "No bar series recorded" empty state (`data-testid="structure-no-bar-series"`, pre-existing component from an earlier iteration) | Unchanged (regression check) | Not modified this iteration, but the phase's Definition of Done requires this state to remain reachable now that a new write action feeds the same page | In the pre-existing "Load" form (below the new fetch panel), type a symbol that has never had any bar series fetched or recorded (e.g. `ZZZQQQ`) and submit. Confirm the text "No bar series recorded for ZZZQQQ." with the line "Recording historical bars needs provider credentials." appears, and no chart, level line, or badge renders. |
| `/structure` | Page header paragraph + `structure-framing` caption (`data-testid="structure-framing"`) | Changed behavior (copy only) | The page description needed to acknowledge the one new write action instead of describing the whole page as read-only | Load `/structure` and confirm the paragraph under the "Structure" heading begins "Fetch real historical bars from Yahoo Finance (keyless), then see deterministic support/resistance levels…" and the caption below it (`data-testid="structure-framing"`) begins "One explicit write action — fetching bars from Yahoo Finance below — everything else on this page is read-only…". |
| `/` (home / cockpit, via shared `TopBar`) | `FeedBasisBadge` (pre-existing usage, unrelated route) | Updated component (type-only, non-visual) | The badge's `dataFeed` prop was widened from a fixed `"sim" \| "iex" \| "sip"` union to a general `string` so the same component could be reused on `/structure` for the `"yahoo"` feed; its rendering logic itself was not touched | Start a live or historical watch on the home page exactly as before this iteration, and confirm the feed badge in the top bar still renders its usual label (e.g. "SIP (consolidated)" or "IEX (live)") — a regression check confirming the shared-component type change did not alter its original behavior. |

<!-- Change Type options used above: New form | Changed behavior | New feature | Unchanged (regression check) -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/routes.py::list_bar_series` (B2 fix) — a blank `?symbol=` or `?timeframe=` query parameter now normalizes to "absent" before the no-param short-circuit check, so it returns byte-identical results to a true no-parameter request instead of silently using a narrower index-only lookup. No UI surface affected: `apps/frontend/lib/api.ts`'s `fetchBarSeriesList()` — the only frontend caller of `GET /research/bars` — always calls it with zero query parameters and never sends a blank symbol/timeframe value, so this fix has no reachable trigger anywhere in the current UI.
- `apps/backend/tests/test_research_api.py` — updated `test_taxonomy_serves_feed_basis_copy_canary` to assert the new `"yahoo"` label — a test-only change, no UI surface affected.
- `apps/backend/tests/test_bars_api.py` — new test proving the B2 fix (`test_blank_symbol_param_is_byte_identical_to_no_param_even_with_an_unindexed_series`) — a test-only change, no UI surface affected.

Note: `apps/backend/app/research/taxonomy.py` (the `"yahoo": "Yahoo Finance"` label addition) is **not** listed here — although it is a backend file, it is directly consumed by the existing `FeedBasisBadge` component and is what makes the "Yahoo Finance" badge (table row 3 above) show real text instead of a fallback. It is classified as UI-visible, not backend-only.

---

## Summary

- **Frontend surfaces changed:** 6 (5 new/changed on `/structure`, 1 type-only/non-visual change to a component also used on `/`)
- **New pages/routes:** 0
- **Modified components:** `apps/frontend/app/structure/page.tsx` (fetch form, submit wiring, badge insertion, copy), `apps/frontend/components/FeedBasisBadge.tsx` (prop type widened), `apps/frontend/lib/api.ts` (new `recordBarSeries()` helper), `apps/frontend/lib/types.ts` (new `RecordBarSeriesResult` interface)
- **Navigation changes:** no — `/structure` was already reachable from the top bar before this iteration
- **Backend-only changes:** 3 (`routes.py` B2 fix + 2 backend test files)
