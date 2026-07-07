# Iteration 3 — Coherence Audit

**Iteration:** goal-structure_ui-iter-3
**Date:** 2026-07-07
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration

Diff vs snapshot `7b1d40b6a16a3e9d8e06c81bc9310c19eda3f0b6` touches exactly 4 substantive files:
`README.md`, `apps/frontend/app/structure/page.tsx` (+565/-14), `apps/frontend/lib/api.ts` (+71),
`apps/frontend/lib/types.ts` (+102). `apps/backend/` diff is empty (confirmed directly via
`git diff --stat -- apps/backend`), matching the spec's "no backend edit" requirement. This adds
one new Comparison section (J-03) to the existing `/structure` page — no new route, no nav change.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Backtest aggregates (n, net R, net $, win_rate, max_drawdown_r) | OK | `apps/frontend/app/structure/page.tsx` `BacktestResultBlock` renders `String(agg.n)` / `String(agg.net_r)` / `String(agg.net_usd)` / `formatNullableAggregateField(agg.win_rate)` / `formatNullableAggregateField(agg.max_drawdown_r)` — all read from `result.aggregates` returned by `GET /research/backtests/{id}`; zero arithmetic. |
| Per-class A/B/C breakdown + `insufficient_sample` | OK | `BacktestClassTable` renders `Object.entries(result.aggregates_by_class)` verbatim (`agg.n`/`agg.net_r`/`agg.net_usd`/`agg.insufficient_sample`) — no client-side threshold recomputation; `insufficient_sample` is the payload's own boolean, only the label text ("insufficient sample (n < N)") is added. |
| PnL-ledger rows + founding baseline | OK | `fetchPnlLedger()` / `PnlLedger` type are untouched this iteration (`git diff` shows zero hunks touching either) — the Comparison section reuses the pre-existing fetch and locates the row via `ledger.rows.find(r => r.founding)`, a lookup on already-fetched data, not a new computation or endpoint. |
| Simulated-honesty register string | OK | Rendered as `{result.register}` (`page.tsx` `BacktestResultBlock`); `grep -n "simulated —"` over the whole diff returns zero hardcoded occurrences. Proactively registered as the one Data Contract addition this iteration (`runs/goal-session-structure_ui/state/blueprint.md` diff, +1 line, single-owner `REGISTER` constant) — correctly scoped, not an unregistered-value gap. |
| Champion pointer (in the Comparison section) | OK | Reuses `registry.champion` — the SAME state already fetched via `fetchStrategies()` for the J-02 Registry section (`page.tsx:~1045-1065`); no second champion fetch, no second source. |
| Datasets (dataset selector) | OK | `fetchDatasets()` (`apps/frontend/lib/api.ts`, new) is a thin wrapper around `GET /research/datasets` returning the payload verbatim (`{ok, data, error}` shape mirroring `fetchBarSeriesList`); the dataset `<option>` label (`{d.symbol} · {d.split} · {d.id.slice(0,8)}`) is display formatting, not a new computed value. |
| `min_sample_size` (used in the insufficient-sample label) | OK | Read from the pre-existing `PnlLedger.min_sample_size` field (`ledger?.min_sample_size ?? null`) — not derived client-side. |
| UI route map / nav | OK (untouched) | `apps/backend/app/meta.py` and `apps/frontend/components/NavBar.tsx` both show an empty diff — confirmed via `git diff --stat` against both paths. |

No duplicate computation, no non-canonical source, no client-side recomputation of any registered
value found anywhere in the diff.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/structure` Comparison section (J-03) | OK | Built inside the existing `/structure` page at exactly the home `blueprint.md`'s IA table pre-assigns it ("`/structure` (Comparison section) · Structure"). `apps/backend/app/meta.py` (`UI_ROUTES`, the nav owner) and `apps/frontend/components/NavBar.tsx` both empty-diff — no new route, no nav change. Reachable in the same 1 click as the existing `/structure` top-bar link (scroll to a lower section on the same page, not a new click/route). |
| Duplicate-home check | OK | The ui-surface-map's own "Backend-Only Changes" note confirms `GET /research/backtests` (plural) is called by no other frontend code and there is no other in-app way to browse backtest runs — this is the first and only UI surface for the backtest-run entity. It polls `/research/backtests/{id}`, distinct from the Studies page's `/research/studies` sweep-job entity — the pattern (poll loop) is reused, the endpoint is not. |
| Parallel-shell check | OK | `grep -n "^function LoadingPanel\|^function UnavailablePanel\|^function EmptyState\|^function ClassMapTable"` on the post-iteration file shows exactly one definition each — reused via the new `BacktestPanel`/`BacktestResultBlock`, not redefined. `BacktestClassTable` is a genuinely distinct component from the pre-existing `ClassMapTable` (per-class *backtest-result* aggregate object vs. per-class *strategy-config* single number) — not a duplicate UI surface for the same value. |
| Testid-collision check | OK | Registry's `champion-strategy`/`champion-profile` (page.tsx:988/997) and Comparison's `comparison-champion-strategy`/`comparison-champion-profile` (page.tsx:1051/1060) are confirmed distinct strings — no DOM collision between the two same-page testid pairs. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None. Checked specifically for label/format drift on the newly-introduced null-`win_rate` handling
("no trades (n=0)") against any pre-existing convention — `StudyResultsView`'s aggregate shape
(`StudyPopulationAggregate`) has no `win_rate`/`max_drawdown_r` field at all, and `/performance`
renders no win_rate either, so there is no pre-existing sibling display this diverges from; this is
a first-of-its-kind honest-null pattern, clearly labeled, not a coherence issue.
