# Iteration 1 — Coherence Audit

**Iteration:** goal-yahoo_fetch-iter-1
**Date:** 2026-07-09
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Bar-series provenance `feed="yahoo"` (blueprint row 1) | OK | Sole hardcoded `"yahoo"` literal is `YahooAdapter.name` at `apps/backend/app/providers/adapters/yahoo.py:58`. The route reads it off the adapter object — `feed = adapter.name if isinstance(adapter, YahooAdapter) else registry.config.historical_feed` at `apps/backend/app/research/routes.py:1616` — never a route- or client-hardcoded `"yahoo"` string. Non-Yahoo path is byte-identical to pre-iteration (`registry.config.historical_feed`, unchanged). Stored through the unmodified canonical `BarStore.record(...)` (`research/bars.py` not touched by this diff) and served back through the existing, unmodified `GET /research/bars` / `GET /research/bars/{id}` handlers — single source, single serving endpoint confirmed. |
| Bar series + checksums, S/R levels, A/B/C zones, strategies/champion, backtests aggregates, PnL ledger, datasets, UI route map, "Yahoo Finance" taxonomy label (all other blueprint rows) | OK — not touched | None of their owning modules (`research/bars.py` internals, `research/levels.py`, `research/backtests.py`, `research/strategies.py`, `research/pnl_ledger.py`, `research/datasets`, `app/meta.py`, `research/taxonomy.py`) appear anywhere in the diff (`git diff 7ebb15b8...` full listing checked). Zero risk of duplicate computation this iteration. |
| New displayed value this iteration | N/A — none | Iteration spec ("New information displayed: None on-screen this iteration") and the ui-surface-map both confirm zero frontend changes; `feed="yahoo"` is a REST/MCP-only field this iteration, already registered in the blueprint (row 1) before this iteration started — nothing new to register. |

**Accessor-discipline check (supporting evidence for single-owner `feed`):** the iteration's own named crux risk — that a bar-fetch vendor default could leak into the live/tick/search accessor — is cleanly avoided. `apps/backend/app/main.py` has **zero diff** against the snapshot SHA (confirmed via `git diff 7ebb15b8... --stat -- apps/backend/app/main.py`, empty output), so `get_adapter()` / `get_market_adapter()` (used by cockpit `/`, tick, live, search, clock at `main.py:243,401,428,168`) is untouched. The new `get_bar_fetch_adapter()` (`research/routes.py:1539-1551`) is a distinct resolver confined to `POST /research/bars`, defaulting to `YahooAdapter` while reusing the same `get_market_adapter` dependency-override key so existing `FakeAdapter`-injecting tests still pass unmodified. `get_study_market_adapter()` (`research/routes.py:1222-1225`, the historical-dataset/study path) is untouched and still falls through to `get_market_adapter()` → Alpaca/simulated. Two vendor resolvers, cleanly separated, zero cross-contamination — this is the mechanism that keeps the Data Contract's "adapter is the sole source of the feed stamp" true.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | OK — N/A | Blueprint: "Nav skeleton is UNCHANGED this era." Iteration spec: "No new UI this iteration" / "No new surfaces and no nav-skeleton change." `reports/phase-goal-yahoo_fetch-iter-1-ui-surface-map.md` confirms 0 frontend files changed, 0 new pages/routes, 0 modified components, 0 navigation changes — all six listed rows are regression spot-checks of pre-existing surfaces, not new features. Nothing to check reachability for. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The ui-surface-map's "Silent provenance note" is worth carrying forward: `/structure`'s existing, unmodified series-picker can now render Yahoo-sourced candles (if a Yahoo fetch is triggered via the API/MCP) with no visible badge distinguishing them from Alpaca-sourced ones — the "Yahoo Finance" human-readable label (blueprint Data Contract row 2, `taxonomy.FEED_BASIS_LABELS`) is explicitly deferred to J-05. This is intentional, in-scope, and matches the blueprint's own IA table (J-05 row), not a violation — flagging only so the decomposer keeps it on the J-05 punch list rather than treating current silence as done.
