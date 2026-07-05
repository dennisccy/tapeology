# goal-tape_to_profit_support_resistence-iter-0 Dev Handoff

**Phase:** goal-tape_to_profit_support_resistence-iter-0
**Date:** 2026-07-06
**Agent:** developer
**Status:** complete

## What Was Built

Nothing — by design. This is the era-4 (structure-and-tape) **verify-only baseline** (Mode:
baseline, Depth: lean). Zero code changes were made; the entire scope was executing the spec's
verification checklist against the current codebase and recording the evidence below.
`git status --short` shows **no tracked file modified and no file created under `apps/`** (the
product source tree). The only diffs present are pre-existing: era-3 closeout artifacts
(`reports/goal-session-tape_to_profit-*`, `runs/goal-session-tape_to_profit/*`) that were already
modified before this iteration started (era transition bookkeeping), plus two untracked pipeline
artifacts the goal-mode engine wrote before dev ran (`docs/phases/goal-tape_to_profit_support_resistence-iter-0.md`,
`runs/goal-session-tape_to_profit_support_resistence/`) — neither is product source.

## Baseline test counts (the era-4 anchor)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`

- **Collected: 1041 items. Result: 1040 passed, 1 skipped, 2 warnings in 364.95s (0:06:04). Exit 0.**
- The single skip is `tests/test_live_integration.py:37` — `"gated: set
  TAPEOLOGY_LIVE_INTEGRATION=1 to run the real live-socket check"`. This is an explicit two-stage
  opt-in gate (env var first, then credentials, then market-hours), not a credentials-missing
  failure — expected and honest for an autonomous, keyless run.
- This is up from era-3's own baseline (848 passed / 849 collected, recorded in
  `docs/handoffs/goal-tape_to_profit-iter-0-dev.md`), reflecting all growth added across era-3
  iterations 1–8. **The era-4 baseline is 1040 passing / 1041 collected.**

Engine equivalence test (byte-identical `default` outputs, J-07 guard):

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py -v`

- **7 passed in 0.11s.** The serialized-projection byte-identity guard over the observer seam is
  green — the frozen `default` behavior is intact and remains the pinned reference for era 4.

## Journey-by-journey verification evidence

The goal-evaluator assigns statuses; this section records what the codebase and a live backend
actually showed. Predictions from the spec (J-01–J-06 absent, J-07 intact) were **confirmed on
every point**.

### J-01 — multi-timeframe bar store + `GET /research/bars` (expected FAIL) — CONFIRMED ABSENT

- Live probe: `GET /research/bars` → **404** `{"detail":"Not Found"}`.
- `grep -rn "RawBar|fetch_bars|get_stock_bars|TimeFrame" app/` → zero matches anywhere in the
  backend.
- `app/providers/adapters/base.py`'s `MarketDataAdapter` Protocol exposes exactly
  `fetch_historical`, `search_symbols`, `get_market_clock`, `stream_live`,
  `warm_symbol_universe`, `is_available` — no `fetch_bars`. Existing dataclasses are `RawTrade`,
  `RawQuote`, `HistoricalWindow` — no `RawBar`.
- No bar-store module (`grep -rln "bar_store|BarStore"` → zero matches); no `/research/bars*`
  route registered (full route dump below).
- No `bars` tool in the MCP tool tuple (12 tools registered, enumerated below) — no MCP proxy
  exists either.

### J-02 — deterministic support/resistance levels (expected FAIL) — CONFIRMED ABSENT

- Live probe: `GET /research/levels` → **404** `{"detail":"Not Found"}`.
- `grep -in "pivot|confluence|swing|timeframe|proximity_band|class_threshold" app/config.py` →
  zero matches — no S/R config section exists.
- No S/R module anywhere in `app/research/` (module list below has no `levels.py` / `structure.py`
  equivalent).

### J-03 — confluence zones + A/B/C classes (expected FAIL) — CONFIRMED ABSENT

- Same `/research/levels` 404 as J-02 (confluence classes would be served from the same
  endpoint — there is nothing to serve).
- `grep -rln "confluence|support.*resistance|swing_pivot|SRLevel"` over `app/` → zero matches.

### J-04 — `structure_tape` as a registered strategy (expected FAIL) — CONFIRMED ABSENT

- Live probe: `GET /research/strategies` → **404** `{"detail":"Not Found"}` (no strategy-registry
  endpoint exists yet).
- Live probe: `POST /research/backtests` with `{"dataset_id":"nonexistent-probe",
  "strategy_id":"structure_tape","profile":"default"}` → **422**
  `{"detail":"unknown strategy_id 'structure_tape' — the registered strategy is 'v1'"}` — the
  strategy-id check in `app/research/routes.py:1522` fires before any dataset lookup, exactly the
  registry-of-one behaviour the spec expects.
- `app/config.py`: `STRATEGY_V1_ID = "v1"` is the only strategy id constant; no
  `StrategyRegistry` or `structure_tape` string exists anywhere in `app/`.

### J-05 — class-scaled stop/reward/simulated size (expected FAIL) — CONFIRMED ABSENT

- Since `structure_tape` itself is rejected at the registry check (J-04 above), no backtest under
  it can ever run, so no per-class report can exist.
- `grep -rln "per_class|class_breakdown|by_class|position_notional|simulated_notional"
  app/research/*.py app/config.py` → zero matches — no class-scaled risk/sizing machinery exists
  yet.

### J-06 — `structure_tape` vs `v1` on the measurement machine (expected FAIL) — CONFIRMED ABSENT (champion-only today)

- `app/research/pnl_scan.py` and `app/research/edge_report.py` both call `_run_backtest(...,
  strategy_id=champion["strategy_id"], ...)` throughout — every sweep/edge-report row varies only
  `profile`; there is no parameter path to evaluate an arbitrary named strategy. Today this always
  resolves to the champion's `v1`.
- `GET /research/profiles` → `200` — `"champion":{"strategy_id":"v1","profile":"default"}`,
  `"profiles":[{"id":"default","frozen":true,"is_default":true},
  {"id":"candidate-faster-warmup","frozen":false,"is_default":false,...}]`. This is the exact
  pre-iteration champion-pointer state that must stay untouched except by an honest hold-out
  promotion (J-07 guards this going forward).

### J-07 — the archived eras are unchanged (regression sentinel) — CONFIRMED INTACT

- Full suite green (1040/1041 above); equivalence suite green (7/7 above, byte-identical `default`
  projections — the pinned `config_fingerprint` guard).
- Champion pointer confirmed untouched: `v1` / `default` (above).
- Live backend (uvicorn `main:app`, loopback port 8000, scratch `TAPEOLOGY_JOURNAL_DB` so the real
  dev DB was never touched):
  - `GET /health` → 200.
  - `POST /watch/SIM-BUYER` → 200; polling `GET /tape/SIM-BUYER/state` every second: `unclear` /
    `warm:false` through t=3s, then settles at **t=4s** to `"tape_state":"buyer_control"`,
    `"warm":true`, confidence rising 0.86 → ~0.93+ and holding through t=12s. `DELETE
    /watch/SIM-BUYER` → 200.
  - `POST /watch/SIM-SELLER` → 200; same warm-up shape, settles at **t=4s** to
    `"tape_state":"seller_control"`, `"warm":true`, confidence 0.86 → ~0.94. `DELETE
    /watch/SIM-SELLER` → 200.
  - Archived research API intact: `GET /research/taxonomy`, `/research/journal`,
    `/research/studies`, `/research/datasets`, `/research/pnl/ledger` → all 200.
  - `GET /meta/ui-routes` → 200, exactly **4 nav entries** (Cockpit `/`, Journal `/journal`,
    Studies `/studies`, Performance `/performance`) plus the one non-nav `/journal/[id]` detail
    route — unchanged, no era-4 entry added.
- Live frontend (`next dev`, port 3000, `NEXT_PUBLIC_API_URL=http://localhost:8000`): `GET /` →
  200 (14831 bytes), `GET /journal` → 200, `GET /studies` → 200, `GET /performance` → 200.
- `apps/frontend/components/NavBar.tsx` inspected (read-only, unchanged): it is a client component
  that fetches `GET /meta/ui-routes` in a `useEffect` and renders only `nav: true` entries — no
  hardcoded route list, an explicit `nav-unavailable` degraded state on fetch failure. This
  confirms the nav's single source of truth is unchanged; a raw `curl` of the SSR shell shows an
  empty `<ul>` because the route-map fetch is client-side (expected — hydration/JS is required to
  populate it, which is why the full click-through nav check belongs to browser-qa, not this
  dev-level pass).
- Grep-guard (no execution/brokerage code): `grep -rIn "place_order|submit_order|brokerage|paper.
  trading|OrderTicket"` over `app/` → zero matches. `alpaca.trading.client.TradingClient` is
  imported in `app/providers/adapters/alpaca.py` but used **only** for `get_asset` (single-symbol
  tradability lookup) and `get_all_assets` (tradable-universe listing) — both read-only asset
  metadata calls, no order-placement call anywhere. Anti-goal holds.

### Backend route-table cross-check (authoritative absence evidence)

`app/research/routes.py` registers exactly: `/taxonomy`, `/analytics`, `/thesis/active`,
`/hints/active`, `/hints`, `/journal`, `/journal/{thesis_id}`, `/thesis`,
`/thesis/{thesis_id}/resolve`, `/thesis/{thesis_id}/action`, `/thesis/{thesis_id}/review`,
`/studies`, `/studies/{study_id}`, `/studies/{study_id}/cancel`, `/datasets`,
`/datasets/{dataset_id}`, `/backtests`, `/backtests/{backtest_id}`,
`/backtests/{backtest_id}/cancel`, `/pnl/ledger`, `/profiles` — the archived + era-3 surface
exactly. No `/bars`, `/levels`, or `/strategies` route exists.

MCP server (`app/mcp/__init__.py`) registers exactly 12 tools: `tape_state`, `tape_features`,
`tape_history`, `journal`, `analytics`, `studies`, `datasets`, `backtests`, `pnl_ledger`,
`taxonomy`, `ui_route_map`, `get_endpoint` — no `bars`, `levels`, or `strategies` tool exists.

`app/research/` module list: `analytics`, `backtests`, `datasets`, `edge_report`, `excursions`,
`execution_checks`, `feed_basis`, `grades`, `hints`, `journal_rows`, `marks`, `monitor`,
`pnl_baseline`, `pnl_history`, `pnl_ledger`, `pnl_scan`, `profiles`, `routes`, `stance`, `store`,
`studies`, `taxonomy`, `verdict` — the archived + era-3 modules only; no S/R, bar-store, or
strategy-registry module exists.

## Files Changed

- (none — verify-only baseline; zero source modifications)

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **1040 passed, 1 skipped** (1041 collected), 2 warnings, 364.95s, exit 0

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py -v`
Result: **7 passed** in 0.11s

## Service startup verification

- Backend `uvicorn main:app --app-dir apps/backend --host 127.0.0.1 --port 8000` (scratch
  `TAPEOLOGY_JOURNAL_DB`, never touching the real dev DB) started clean; `/health` → 200 within 1s.
- Frontend `npx next dev -p 3000` (Next.js 15.5.19) started clean (`Ready in 1347ms`); all four
  archived pages served 200.
- Both processes were stopped after verification; ports 8000 and 3000 confirmed free afterward
  (connection refused on both).

## Known Issues

- **Environment drift note (carried over from era-3):** the backend venv runs Python **3.14.4**
  while `.claude/project-template.md` states Python 3.12 (goal.md's Constraints section also says
  3.12). The full suite is green on 3.14.4 — a documentation/environment drift observation, not a
  failure. No action taken (out of scope for a verify-only iteration).
- **`.claude/project-template.md` is still the generic unfilled template** (placeholders like
  `<e.g., Python 3.12>` throughout, not project-specific values) — this developer used goal.md's
  "Constraints" section and the README's "How to run" section as the actual stack-configuration
  source of truth, matching what prior iterations evidently did too (documentation gap, not
  something this baseline iteration is scoped to fix).
- `tests/test_live_integration.py` skips on the explicit `TAPEOLOGY_LIVE_INTEGRATION=1` opt-in
  gate (expected — keyless, off-hours-safe by design; era-4 J-01's credentialed bar-fetch probe
  will be a separate, explicit operator action per the spec).
- Full browser-driven J-07 verification (SIM-BUYER/SIM-SELLER cockpit panels over WebSocket, the
  hydrated nav actually showing 4 clickable links, journal/studies/performance page content) is
  the browser-qa step per the spec's TESTING REQUIREMENTS; the API/SSR/code-inspection evidence
  above is the dev-level leg only. A plain `curl` cannot execute the nav's client-side
  `/meta/ui-routes` fetch, so its raw SSR HTML shows an empty nav `<ul>` — this is expected
  behaviour (confirmed by reading `NavBar.tsx`), not a defect.

## Suggested Next Phase

Per the spec's NOTES and goal.md's dependency order: iter-1 should build **J-01** (multi-timeframe
bar store + neutral `RawBar` on the adapter seam + `fetch_bars` + `GET /research/bars*`) — it is
the explicit unblocker, since J-02–J-06 all consume its bar series, and the spec itself flags it as
"a data-model + provider-seam change, i.e. a risky iteration to isolate on its own next."
