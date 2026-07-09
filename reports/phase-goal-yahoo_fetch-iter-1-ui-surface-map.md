# Phase goal-yahoo_fetch-iter-1 — UI Surface Map

**Phase:** goal-yahoo_fetch-iter-1
**Date:** 2026-07-09
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

Zero frontend files changed this iteration (`git status --short apps/frontend/` is empty — no
`.tsx`/`.ts`/`.css` diff anywhere under `apps/frontend/`). There is **no new page, component, form,
table, or navigation element**. Every row below exists because the phase spec mandates a **J-06
foundation regression spot-check** — the iter-0 evaluator required the browser-qa lane to actually
run and emit evidence this iteration, to confirm the new `yfinance` runtime dependency and the
backend vendor-selector change (`apps/backend/app/research/routes.py`) did not break any existing
rendered surface. `/structure` additionally has a real (if invisible) data-provenance link to the
changed endpoint; the other five routes have zero code relationship and are pure blast-radius
checks.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `Cockpit` (`apps/frontend/components/Cockpit.tsx`), `FeedBasisBadge`, `DataSourceSelector`, `MarketStatusIndicator` | No change — regression spot-check | Plan-flagged as the **highest-risk surface**: it depends on `get_adapter()` (`apps/backend/app/main.py:129`), which shares the same backend process/import graph as the modified `research/routes.py` (new `YahooAdapter` import + `get_bar_fetch_adapter()` resolver). The plan requires proving `get_adapter()` itself was not touched. | Load `/`, use the ticker search to watch an existing symbol, and confirm the live quote/tape panel populates with data and the feed-basis badge (`data-testid="feed-basis"`) still shows its pre-iteration `sim`/`iex`/`sip` label — not `"yahoo"` and not blank — with zero console/network errors. |
| `/structure` | `StructureChart` (`apps/frontend/components/StructureChart.tsx`) + the page's bar-series fetch (`apps/frontend/app/structure/page.tsx`, calls `GET /research/bars`) | Changed behavior (data-source only, no visual change) | This is the one existing surface that consumes the exact endpoint whose default vendor and `feed` stamp changed. Its `pickRepresentativeSeries` picker (unmodified) selects among whatever series exist for a symbol with no regard to `feed`. | Query a symbol that already has a pre-iteration (Alpaca-fed) registered bar series and confirm the candlestick chart, S/R level lines, and A/B/C confluence zone badges render exactly as before (same candle count, no blank chart, no error banner). Separately, confirm no element anywhere on the page renders the literal string `"yahoo"` or `"sip"` as visible text (no badge exists yet — this iteration must not have accidentally leaked the raw feed string into any label). |
| `/journal` | `JournalTable`, `JournalFilterBar`, `AnalyticsView`, `HintLog` | No change — regression spot-check | No code path in this iteration touches journal/trade data; included purely as a blast-radius check per the plan's "spot-check /journal, /studies, /performance too." | Load `/journal`, confirm the trade table populates with its existing rows and the filter bar's controls (date range / symbol filters) remain clickable, with zero console errors. |
| `/journal/[id]` | `JournalDetailView` | No change — regression spot-check | Same as above. | Open any existing journal entry's detail page (click a row from `/journal`) and confirm the thesis strip, evidence, and hint-log sections all render with no error state. |
| `/studies` | `StudyList`, `StudyCreateForm`, `StudyResultsView` | No change — regression spot-check | Same as above. Note: study creation's `SOURCE_HISTORICAL` path uses `get_study_market_adapter()`, which this iteration deliberately left untouched (plan Risk 1) — this row proves the page still renders, not that study creation was exercised. | Load `/studies`, confirm the existing studies list renders with its prior entries, and confirm the "new study" form opens and its fields are interactive (do not need to submit — submission exercises a code path this iteration explicitly did not change). |
| `/performance` | Performance/analytics page (`apps/frontend/app/performance/page.tsx`, no dedicated component — inline) | No change — regression spot-check | Same as above. | Load `/performance`, confirm the PnL ledger and profile analytics render with existing data (or the existing empty state if no data), with no error banner. |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/providers/adapters/yahoo.py` (NEW) — `YahooAdapter`: the concrete keyless
  Yahoo Finance adapter (`fetch_bars` for `"1d"` only; every other method honestly raises or
  returns empty). A provider module with no direct UI coupling — reachable only through the route
  below, and that route has no browser control pointed at it yet.
- `apps/backend/app/research/routes.py` (MODIFY) — new `get_bar_fetch_adapter()` resolver +
  conditional `feed` sourcing inside `record_bar_series` (`POST /research/bars`). This is a
  **backend-api** change (the frontend does consume `GET /research/bars`, per the `/structure` row
  above), but it changes a field's possible *value*, not the response *shape* — `feed: string` was
  already present in the frontend's `BarSeriesRecord` type before this iteration. No new request
  parameter exists to choose Yahoo vs. Alpaca from the API (confirmed in the dev handoff's "Known
  Issues"), so there is nothing for a future UI control to bind to yet beyond the default.
- `apps/backend/requirements.txt` (MODIFY) — pinned `yfinance==1.5.1`. Dependency manifest only,
  zero runtime UI behavior.
- `config/install-security-policy.json` / `incredible_auto_dev/config/install-security-policy.json`
  (MODIFY) — added `"yfinance"` to `python.allowlist`. Supply-chain install gate config, zero UI
  surface.
- `apps/backend/tests/test_yahoo_adapter.py` (NEW), `apps/backend/tests/test_bars_api.py`
  (MODIFY — extend only), `apps/backend/tests/test_yahoo_live_integration.py` (NEW),
  `apps/backend/tests/fixtures/yahoo/AAPL_1d_20260601_20260604.json` (NEW) — test code and a
  committed fixture. No UI surface.
- **Silent provenance note** (elaborated in the user-visible-changes report): `/structure`'s
  existing, unmodified series-picker can render Yahoo-sourced candles today if a Yahoo fetch is
  triggered via the API/MCP — there is no code change here, but it is the one path by which this
  iteration's new data can reach a real browser screen, and it does so with no visible label
  distinguishing it from Alpaca-sourced data.

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 8 files (`yahoo.py` new; `research/routes.py`, `requirements.txt`,
  `install-security-policy.json` modified; 3 new test files + 1 new fixture) — none with a UI
  surface of their own
- **Regression spot-check surfaces (no code change, evidence required by the plan):** 6
  (`/`, `/structure`, `/journal`, `/journal/[id]`, `/studies`, `/performance`)
