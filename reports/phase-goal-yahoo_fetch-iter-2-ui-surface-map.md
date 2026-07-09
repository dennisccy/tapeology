# Phase goal-yahoo_fetch-iter-2 — UI Surface Map

**Phase:** goal-yahoo_fetch-iter-2
**Date:** 2026-07-09
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

No frontend source file changed this iteration (`git diff --stat -- apps/frontend/` is empty,
confirmed independently). The table below has exactly one row, and it is *not* a code change — it
documents a pre-existing, unmodified UI surface whose rendered content can now differ because the
backend data it reads has grown. See "Why Changed" for the precise mechanism; do not read this row
as "a component changed this iteration."

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/structure` | `StructureChart` (candles + level lines) and the Levels & Zones table, both fed by `pickRepresentativeSeries()` in `apps/frontend/app/structure/page.tsx` | Indirect data-surface expansion (zero source change) | This page's series-selection logic (`TIMEFRAME_ORDER`, shortest-timeframe-wins) and level-line labels (`${level.timeframe} ${level.type}`) already handled every era-5 timeframe generically, but until this iteration only `1d` bar series could ever exist (Yahoo could only fetch daily). Now that `1w`/`1h`/`5m`/`1m`/`4h` can be fetched (via direct API call, not a UI control), the very next `/structure` page load for a symbol with one of those series registered will render it instead of `1d`, with no frontend code change required. | 1. With the backend running, call `POST /research/bars` directly (curl or the MCP `bars` tool) with body `{"symbol":"AAPL","timeframe":"1h","start":"<a recent ISO start within Yahoo's ~730-day 1h retention>","end":"<a recent ISO end>"}`; confirm `HTTP 200` and `"feed":"yahoo"` in the response. 2. Open `/structure` in the browser, type `AAPL` into the symbol search, and click **Load**. 3. Expected result: the on-page summary text reads `"Candles: 1h series (... of ... recorded bars, as of the query time)"` (not `1d`), the candlestick chart renders visibly denser/shorter-interval candles than a daily series, and the Levels & Zones table contains at least one row whose Timeframe column reads `1h` — all without any frontend file having been touched by this iteration. |

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/providers/adapters/yahoo.py` (`_INTERVAL_MAP` expanded to 5 entries; new
  `_resample_4h()`; `fetch_bars()` now raises `UnsupportedTimeframe`/`NoDataForWindow` instead of
  silently returning an empty tuple) — the endpoint this powers, `POST /research/bars`, has **no UI
  caller anywhere**: `apps/frontend/lib/api.ts` defines only a `GET` wrapper for `/research/bars`
  (`fetchBarSeriesList`, plain `fetch()` with no method override, confirmed via grep) — there is no
  frontend function that POSTs to this endpoint. No UI surface affected for the fetch-trigger action
  itself.
- `apps/backend/app/providers/adapters/base.py` (new `UnsupportedTimeframe(Exception)` class beside
  `SymbolNotTradable`/`NoDataForWindow`/`VendorTimeout`) — pure exception-type definition, no UI
  caller, no HTTP surface of its own.
- `apps/backend/app/research/routes.py` (`record_bar_series` gains two new `except` clauses mapping
  `UnsupportedTimeframe` and `NoDataForWindow` to distinct `422` responses) — HTTP-mapping glue for
  the same UI-unreachable `POST /research/bars` endpoint above; the new error text is only
  observable by calling the API directly today (no UI element can trigger the request that would
  produce it).
- `apps/backend/tests/test_yahoo_adapter.py`, `apps/backend/tests/test_bars_api.py`,
  `apps/backend/tests/test_yahoo_live_integration.py` — test files, no UI surface.
- `apps/backend/tests/fixtures/yahoo/AAPL_1h_20260601_20260603.json` — new committed test fixture,
  no UI surface.

## Out of Scope for This Map (unrelated to the diff, not re-verified here)

- `/`, `/journal`, `/journal/[id]`, `/studies`, `/performance` — none of these pages read
  `GET /research/bars*` or `GET /research/levels*`, and none call the changed adapter/route code
  path, so they have no relationship to this iteration's diff. Full-app regression re-verification
  of these pages (per the plan's J-06 requirement) is the browser-QA lane's job, not a surface this
  diff touches — the dev handoff already records a manual smoke pass (`GET /`, `GET /structure` both
  200 against a live `bash scripts/dev.sh` run).

---

## Summary

- **Frontend surfaces changed:** 0 (zero `apps/frontend/**` files touched)
- **New pages/routes:** 0
- **Modified components:** 0 (one existing, unmodified component — `StructureChart` / the
  `/structure` page's series picker — becomes reachable with new data; see table above)
- **Navigation changes:** no
- **Backend-only changes:** 7 files (3 implementation: `yahoo.py`, `base.py`, `routes.py`; 3 test
  files; 1 new fixture) — none has a UI caller
