# goal-structure_ui-iter-3 Frontend Handoff

**Phase:** goal-structure_ui-iter-3
**Date:** 2026-07-07
**Agent:** developer
**Status:** complete

## What Was Built

The **Comparison** section — a third section on the existing `/structure` page, below the J-02
Registry section. It is the browser home for the honest `structure_tape`-vs-`v1` backtest
comparison: choose a registered dataset, run both strategies as an offline research job, and read
their aggregates + per-class A/B/C breakdown side by side, including the honest keyless outcome
(`structure_tape` a non-survivor with `n=0`, the champion unchanged at `v1`/`default`). This is the
app's first browser surface for this comparison — previously visible only via `curl`/MCP. With this
section, all four Must-have journeys (levels/zones, registry/champion, comparison, foundation
regression) are now browser-visible on one page.

## New user-facing capability

A person on `/structure` now sees, below the Registry section they already had:

- A dataset selector (populated from every registered dataset) and a "Run comparison" button. This
  starts an offline research job over already-recorded immutable data — it places nothing, and
  there is no cancel/promotion control on this button.
- Once both backtests finish, two side-by-side result cards (`v1` and `structure_tape`), each
  showing: trade count (`n`), net R, net $, `win_rate`, `max_drawdown_r` — with a nullable
  `win_rate`/`max_drawdown_r` shown as the honest `"no trades (n=0)"` rather than a misleading `0`
  — plus a per-class A/B/C table with an inline "insufficient sample" chip wherever a class's trade
  count is below the configured minimum.
- The always-visible "simulated — assumed fees/slippage — not indicative of live results" register,
  read from the payload on each side (never a frontend copy of the phrase).
- A read-only "Champion (moved never by this view)" panel and a "Founding baseline (PnL ledger)"
  panel sitting beside the comparison controls — confirming, on every load, that this view cannot
  and does not move the champion pointer.
- If either backtest hits `failed` or `cancelled`, its own card shows that outcome distinctly (a
  cancelled backtest explicitly says no result is shown — a partial simulated PnL is never served).
- If the backend is unreachable at any point — the dataset list, the "Run comparison" click, or a
  later poll — an explicit amber message appears; nothing is ever fabricated or silently frozen.

## Component/file map

- `apps/frontend/app/structure/page.tsx` — the Comparison section lives here: `BacktestClassTable`
  (the per-class A/B/C breakdown table — a sibling to J-02's `ClassMapTable`, not a reuse of it,
  since the per-class value here is a whole aggregate object, not a single number),
  `BacktestResultBlock` (one strategy's aggregates + class table + register),
  `BacktestPanel` (one side's full state machine — loading/in-progress/failed/cancelled/done), the
  dataset-select + Run form, the dual-backtest create handler, and the dual-backtest poll effect.
  The existing Levels & Zones and Registry sections above it are unchanged (beyond the header
  subtitle extension below).
- `apps/frontend/lib/api.ts` — `fetchDatasets()`, `createBacktest()`, `fetchBacktest()` (new),
  sitting beside the pre-existing `fetchPnlLedger()` this section also now calls from the page.
- `apps/frontend/lib/types.ts` — `Dataset`, `DatasetsListResult`, `BacktestAggregate`,
  `BacktestClassAggregate`, `BacktestResult`, `Backtest`, `CreateBacktestParams` (new).
  `BacktestResult` reuses the existing `Dataset`/`Strategy` types for its own `dataset`/`strategy`
  fields rather than declaring a second shape.

## Visual/UX states implemented

| State | Trigger | Copy (verbatim) | `data-testid` |
|---|---|---|---|
| Datasets loading | Page mount, fetch in flight | pulse-skeleton (reused `LoadingPanel`) | `comparison-datasets-loading` |
| Datasets unavailable | `GET /research/datasets` unreachable/non-200 | "Backend unreachable — is the API running?" | `comparison-datasets-unavailable` |
| No datasets registered | Dataset list is empty | "No datasets registered." + a recording hint | `comparison-no-datasets` |
| Idle | Datasets loaded, Run not yet clicked | "Choose a dataset, then Run comparison, to compare structure_tape against v1." | `comparison-idle` |
| Run failed to start | Either `POST /research/backtests` call fails | the backend's own error detail, verbatim | `comparison-run-error` |
| Poll-time unreachable | A poll tick can't reach a non-terminal backtest | "Backend unreachable while polling — showing the last known status." | `comparison-poll-error` |
| Per-side queued/running | A backtest is `queued`/`running` | "Queued…" / "Running…" (+ live events-processed count) | `comparison-v1-in-progress` / `comparison-structure-tape-in-progress` |
| Per-side failed | A backtest is `failed` | explicit error message + the backend's own error text | `comparison-v1-failed` / `comparison-structure-tape-failed` |
| Per-side cancelled | A backtest is `cancelled` | "cancelled before it finished… no result is shown" (NOT a partial-results state, unlike Studies) | `comparison-v1-cancelled` / `comparison-structure-tape-cancelled` |
| Per-side done | A backtest is `done` | aggregates + per-class table + register, all verbatim | `comparison-v1-*` / `comparison-structure-tape-*` |
| Founding baseline loading/unavailable/empty/populated | `GET /research/pnl/ledger` fetch states | mirrors `/performance`'s own ledger states | `comparison-founding-loading` / `-unavailable` / `-no-founding-row` / `-founding-row` |

Per-result testids (namespaced by side, e.g. `comparison-v1-*` / `comparison-structure-tape-*`):
`-n`, `-net-r`, `-net-usd`, `-win_rate`, `-max-drawdown-r`, `-class-table` (with
`comparison-class-row` / `comparison-insufficient-sample` inside), `-register`. The champion badge
uses `comparison-champion-strategy` / `comparison-champion-profile` — deliberately **distinct**
from the Registry section's `champion-strategy` / `champion-profile` testids, since (unlike
`/performance` vs `/structure`, which never co-render) Registry and Comparison are two sections of
the **same page** rendered simultaneously; reusing the identical strings would collide.

## Design system conformance

- Reused the file's existing local `Panel` container (titled "Comparison", matching the
  uppercase/tracking-wide title style already used for "Price chart — S/R levels", "Confluence
  zones", and "Registry") — no new visual language introduced.
- Reused `LoadingPanel`/`UnavailablePanel`/`EmptyState` and the `NUMERIC_CELL`/`HEADER_CELL`/
  `LABEL_CELL` constants exactly as J-01/J-02 established them — none were redefined.
- The per-class table is a **sibling** to J-02's `ClassMapTable`, not a forced reuse of it (per the
  plan's explicit visual-requirements note): `ClassMapTable` renders `Record<string, number>`;
  `aggregates_by_class`'s per-class value is a whole aggregate object, so a new small table was
  built rather than losing fields by force-fitting the existing one. Its class badge styling
  ("Class A/B/C") follows `ZoneRow`'s existing chip language.
- Layout: single column, appended below Registry inside the same `max-w-7xl` container; the two
  strategy result cards use a `grid md:grid-cols-2` two-column layout on desktop, stacking on
  narrow widths — the same precedent `StudyResultsView`'s setup-vs-null-baseline blocks already
  established.
- Dark instrument-panel style: font-mono numerics for every figure, amber
  (`border-amber-800/60 bg-amber-900/20 text-amber-300`) for the register line, the
  insufficient-sample chips, and every degraded/unavailable state — no new color introduced.
  Rose (`border-rose-700/70 bg-rose-900/30 text-rose-200`) for a failed backtest, matching
  `StudyResultsView`'s `results-failed` styling exactly.
- Every interactive element has hover/focus/active states: the dataset `<select>` reuses the
  existing `INPUT_CLASS` constant (focus ring included); the "Run comparison" button reuses the
  existing "Load" button's exact class string (hover/focus/active/disabled states all present).
- Loading, empty, and error states are all handled — see the state table above. No new chart was
  added (the spec calls for a tabular-only render here); the section does not touch or re-occlude
  the J-01 `StructureChart` canvas above it (confirmed live, screenshot below).
- Responsive: `sm:grid-cols-2` for the champion/founding-baseline row and `md:grid-cols-2` for the
  two strategy result cards, matching the file's/`StudyResultsView`'s existing breakpoint choices —
  no new breakpoint invented.

## Live browser verification performed

Ran the actual app (`bash scripts/dev.sh`) and drove it with the Chrome DevTools Protocol browser
tool end to end: selected a live registered dataset, clicked "Run comparison," and confirmed every
rendered value — `n`, net R, net $, `win_rate` (including the honest `structure_tape` `n=0` /
`"no trades (n=0)"` case), `max_drawdown_r`, all six per-class `insufficient_sample` chips, and both
sides' register text — matched a direct `curl` of `GET /research/backtests/{id}` byte-for-byte (see
the dev handoff for the full field-by-field values). Killed only the backend afterward and confirmed
the Comparison section's three fetch-dependent panels (datasets, founding-baseline, and — via the
Registry section's own state, reused here — the champion badge) each show the honest
backend-unreachable state, never fabricated or stale content. Reloaded `/performance` afterward to
confirm the Comparison section's distinct champion testids cause no cross-page interference with
Registry's or Performance's own `champion-strategy`/`champion-profile` elements. Screenshots were
taken for this developer's own sanity check but are not the formal QA evidence capture (that is the
browser-qa-agent's job, into `reports/qa/goal-structure_ui-iter-3-evidence/`).

## Known Issues / Limitations

- The per-side `failed` and `cancelled` states, the "no datasets registered" empty state, and the
  poll-time `comparison-poll-error` notice are code-complete (their render branches are structurally
  identical to the `queued`/`running`/`done`/dataset-unavailable paths already proven live) but were
  **not** individually exercised live this pass — see the dev handoff's "Known Issues" for why each
  needs either a timed cancel call or an isolated/empty-dataset-dir environment to reach honestly,
  matching iter-1's precedent for its own rarer states.
- `structure_tape` genuinely arms zero trades against the committed keyless reference dataset
  (confirmed live) — this is the expected, honest, non-fabricated outcome given no bar series is
  recorded for the reference symbol, not a defect in this section.
- No responsive breakpoint tuning beyond the page's existing `flex-wrap`/`overflow-x-auto`/
  `grid md:grid-cols-2` conventions, matching the precedent every prior page on this project
  (`/performance`, `/studies`, and this same page's J-01/J-02 sections) already set.
