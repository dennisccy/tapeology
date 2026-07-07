# goal-structure_ui-iter-3 Execution Plan

Scope check against `docs/goal.md`: **aligned, no drift.** This is J-03 ("`structure_tape` is
compared to `v1` on screen, honestly"), the sole remaining `failing` Must-have journey; J-01/J-02
are green (iter-1/iter-2, both audited PASS) and J-04 guards continuously. Verified directly against
the running code (not just the spec prose) that this is genuinely **frontend-only**: `POST
/research/backtests`, `GET /research/backtests/{id}`, `GET /research/datasets`, and `GET
/research/pnl/ledger` all already exist and already serve every field J-03 needs — `apps/backend/`
MUST stay an empty diff. The phase spec's one refinement over `docs/goal.md`'s own prose — rendering
the fuller served `register` string instead of the goal doc's abbreviated paraphrase — is not drift;
it is the doc's own single-source-of-truth rail applied correctly (render the payload, never a
literal copy of it). Depth **full** is justified: J-03 is the single riskiest journey in this
session (dual POST + dual poll, simulated-PnL rendering, insufficient-sample labelling, and the
no-promotion rail all at once), and this is a GOAL_ACHIEVED candidate iteration.

## What to Build

- A third **Comparison** section on `apps/frontend/app/structure/page.tsx` (below the existing
  Registry section), `aria-label="structure_tape vs v1 comparison"`: a dataset selector
  (`GET /research/datasets`), a "Run comparison" button that POSTs two backtests (`v1` and
  `structure_tape`, both `profile=default`, same chosen `dataset_id`) and polls both to a terminal
  status, reusing the Studies page's poll *pattern* (not its endpoint).
- Side-by-side aggregates (`n`, net R, net $, `win_rate`, `max_drawdown_r`) plus the per-class A/B/C
  table from `aggregates_by_class` (with `insufficient_sample` verbatim), all read from
  `GET /research/backtests/{id}` — zero client computation.
- The simulated register rendered **verbatim from the payload's `register` string** (never a
  hardcoded literal — see "Critical grounding" below for the exact served text).
- The champion pointer (read-only, `v1`/`default`) and the founding baseline row from
  `GET /research/pnl/ledger`, shown beside the comparison.
- Honest, distinct states: no datasets registered; a backtest `queued`/`running`; `failed`;
  `cancelled`; `done`-but-insufficient-n; backend unreachable.
- **Non-gating polish** (fold in, does not block J-03): extend the `structure-framing` header
  subtitle to preview all three sections (carry-forward from iter-2 audit finding F1); update
  `README.md`'s stale J-01-only "Structure page" bullet.
- **Zero backend changes.** No edit to `config.py`, `research/levels.py`, `research/backtests.py`,
  `research/strategies.py`, the engine, or `config_fingerprint` (`4d665603569b9dbf`).

## Agents Required

- developer: yes -- implement the Comparison section end-to-end (three new `api.ts` helpers, new
  `types.ts` types modeling the REAL nested payload shape below, the `page.tsx` section with the
  dual-backtest run/poll loop and all six honest states), run the backend suite + frontend build,
  do the non-gating polish, write the dev handoff.
  - backend-data: no -- `POST /research/backtests`, `GET /research/backtests/{backtest_id}`,
    `GET /research/datasets`, and `GET /research/pnl/ledger` already exist and already serve every
    field this journey needs (confirmed by reading `apps/backend/app/research/routes.py:1499-1791`,
    `backtests.py:272-433`, and `pnl_ledger.py` directly, not from the spec's prose alone). A
    backend diff this iteration is a defect against the "no new backend computation or endpoint"
    anti-goal.
  - frontend-ux: yes -- the new Comparison section, its supporting `api.ts`/`types.ts` additions,
    and the two non-gating polish edits.

Frontend Present: yes

## Files to Create/Modify

- `apps/frontend/lib/api.ts` -- add `fetchDatasets()` (mirrors `fetchStudies()`'s
  `{ok, datasets, error?}` shape reading `GET /research/datasets`'s `{datasets, integrity_errors}`
  body), `createBacktest({dataset_id, strategy_id, profile})` (mirrors `createStudy()`'s
  `{ok, backtest?, status?, error?}` shape, POSTing to `/research/backtests` — **exactly these
  three body fields**, confirmed against `BacktestRequest` in `routes.py:160-171`; no
  `null_baseline_seed` field exists on this request, unlike `CreateStudyParams`), and
  `fetchBacktest(id)` (mirrors `fetchStudy()`, `GET /research/backtests/{id}`, returns the backtest
  or `null`). Do **not** add a new PnL-ledger helper — `fetchPnlLedger()` already exists (used by
  `/performance`) and is exactly what the founding-baseline row needs; reuse it.
- `apps/frontend/lib/types.ts` -- add `Dataset`/`DatasetsListResult` (mirror the `BarSeriesRecord`/
  `BarSeriesListResult` pair's shape: `id`, `symbol`, `window_start_utc`, `window_end_utc`,
  `data_feed`, `event_counts: {trades, quotes, total}`, `checksum`, `split`, `source`,
  `source_kind`, `source_id`, `epoch_anchor`, `created_utc`); `BacktestAggregate` (`n`, `gross_r`,
  `net_r`, `gross_usd`, `net_usd`, `win_rate: number | null`, `max_drawdown_r: number | null`);
  `BacktestClassAggregate` (`BacktestAggregate` fields **plus** `insufficient_sample: boolean`);
  `Backtest` typed to the REAL nested shape in "Critical grounding" below (`status`, top-level
  `error?`, and a `result?` object holding `register`, `aggregates`, `aggregates_by_class`,
  `dataset`, `strategy`, `config_fingerprint`, `null_baseline`). Model `win_rate`/`max_drawdown_r`
  as nullable — `n=0` genuinely serves `null`, never `0` (confirmed in `_aggregate()`).
- `apps/frontend/app/structure/page.tsx` -- add the Comparison section: dataset-select control,
  "Run comparison" button, a poll effect tracking BOTH backtest ids (see "Critical grounding"), the
  aggregates + per-class tables, the register render, the champion/founding-baseline block, and the
  six honest states. Reuse this file's own already-defined `Panel`/`LoadingPanel`/
  `UnavailablePanel`/`EmptyState` locals and the `NUMERIC_CELL`/`HEADER_CELL`/`LABEL_CELL`
  constants — do not redefine them (the J-02 precedent).
- `README.md` -- update the "Structure page" bullet to describe all three shipped sections
  (non-gating).
- `docs/handoffs/goal-structure_ui-iter-3-dev.md` -- dev handoff (DoD requirement).
- **No `apps/backend/` files.**

### Critical grounding (read from the actual backend source, not inferred from the spec prose)

1. **The result is NESTED one level under `result`, not flat on `backtest`.** `BacktestRunner.run`
   builds a `result` dict (`register`, `dataset`, `strategy_id`, `strategy`, `profile`,
   `config_fingerprint`, `trades`, `aggregates`, `aggregates_by_class`, `null_baseline`) and
   `_persist_terminal` does `final["result"] = result` (`backtests.py:399-426`, `:841-848`). So
   `GET /research/backtests/{id}` returns `{"backtest": {"id", "status", "dataset_id",
   "strategy_id", "profile", ..., "result": {...only once status is "done"/"cancelled"...},
   "error": "...only if status is failed..."}}`. Read `backtest.result.aggregates`,
   `backtest.result.aggregates_by_class`, and `backtest.result.register` -- **not**
   `backtest.aggregates` / `backtest.register`. Getting this nesting wrong silently breaks every
   render (undefined property reads), so type `Backtest.result` as optional and gate every render
   on `backtest.status === "done"` (mirrors `StudyResultsView`'s `terminalWithResults` gate).
2. **`insufficient_sample` exists ONLY inside `aggregates_by_class`'s per-class entries, never on
   the top-level `aggregates`.** `_aggregate()` (the top-level computer, `backtests.py:272-305`)
   returns no such key; only `_aggregate_by_class()` (`:308-330`) adds
   `agg["insufficient_sample"] = agg["n"] < config.pnl_min_sample_size` per class (A/B/C, always
   all three, even when empty). Render the per-class flag verbatim; do **not** compute or fabricate
   an overall/derived "insufficient" or "non-survivor" boolean anywhere in the frontend — that would
   be an uncanonical second computation (trap T10). The doc's "`structure_tape` a non-survivor"
   framing is prose for humans reading `docs/goal.md`, not a literal field the UI must produce.
3. **The served register is the fuller string, not the goal doc's paraphrase.** `REGISTER =
   "simulated — assumed fees/slippage — not indicative of live results"` (`backtests.py:142`,
   re-exported by `pnl_ledger.py`). Render `backtest.result.register` / `ledger.register` verbatim
   — never type the goal doc's abbreviated "simulated — not indicative of live results" into the UI.
4. **The champion is already in scope on this page — do not re-fetch it.** `page.tsx`'s existing
   J-02 `useEffect` already calls `fetchStrategies()` on mount and holds `registry.champion` in
   component state. The Comparison section's champion badge must reuse that SAME state (zero new
   `/research/strategies` call) — never a second fetch, which risks a second "view" of the champion
   drifting from the first. **However**, the Registry section already renders this exact champion
   using `data-testid="champion-summary"`/`"champion-strategy"`/`"champion-profile"` — and unlike
   `/performance` vs `/structure` (different routes, safely never co-rendered, per the iter-2 audit's
   finding T2), Registry and Comparison are **two sections of the SAME page rendered
   simultaneously**. Reusing the identical testid strings a second time on this one page would
   collide (two DOM nodes, one testid — the exact risk the iter-2 audit's T2 note flagged as a
   "future test-hygiene item"). If the Comparison section re-renders the champion, give it its own
   distinct testids (e.g. `comparison-champion-strategy`/`comparison-champion-profile`) while
   reading the identical `registry.champion` values — same source, distinct DOM identity.
5. **The founding baseline row** is `ledger.rows.find(r => r.founding)` from the newly-added
   `fetchPnlLedger()` mount call (an honest absence if the ledger is empty — no founding row yet).
   `PnlLedgerRow`/`PnlSplitPair`/`PnlSplitMeasurement` types already exist in `types.ts` — reuse
   them; render the founding row's `candidate` split(s) beside the live comparison, per the spec's
   "beside the champion pointer and the founding baseline row."
6. **The poll loop tracks TWO ids, not one.** Unlike Studies (one list, poll while any row is
   active), J-03 creates exactly two backtests (`v1` id + `structure_tape` id) via
   `Promise.all([createBacktest(v1Params), createBacktest(structureTapeParams)])`, then an interval
   (mirror `studies/page.tsx`'s `setInterval(loadStudies, 700)`) re-fetches both ids via
   `fetchBacktest(id)` and stops once **both** reach a terminal status (`done`/`cancelled`/
   `failed`) — not after either one alone.
7. **`BacktestRequest` accepts exactly `dataset_id`/`strategy_id`/`profile`** (`routes.py:160-171`)
   — no `null_baseline_seed` field; the backend's own `BacktestJobManager.create()` always falls
   back to the config-owned default seed since the route never forwards one. `createBacktest()`
   needs no fourth parameter.
8. **A cancel control is not required.** The spec's "New user actions" names only the dataset
   selector + "Run comparison" button — no cancel button. The `cancelled` honest state still needs
   to render correctly (code-complete), but exercising it live may require a direct
   `POST /research/backtests/{id}/cancel` call during QA (curl, or the browser tool's own fetch)
   rather than a UI control — mirroring how iter-1 exercised its rarer states.
9. **Datasets already exist live.** The running `.data/datasets/` directory currently holds 7
   registered datasets, so `GET /research/datasets` returns a non-empty list today — the populated
   dataset-selector path is trivially reachable. The "no datasets registered" empty state is still
   required in code but may need an isolated/temp-dir environment to exercise live (the iter-1
   fixture-seeding precedent).

## UI Evolution

- New user-facing capability: choose a registered dataset, run `structure_tape` and `v1` as an
  offline research job over it, and read both strategies' aggregates + per-class A/B/C breakdown
  side by side — including the honest keyless outcome (`structure_tape` insufficient-n, champion
  unchanged) — inside the app rather than only via `curl`/MCP.
- New information displayed: side-by-side backtest aggregates (`n`, net R, net $, `win_rate`,
  `max_drawdown_r`) for `v1` and `structure_tape`; the per-class A/B/C `aggregates_by_class` table
  with `insufficient_sample`; the founding baseline ledger row; the champion pointer; the simulated
  register string — all read verbatim from their canonical payloads.
- New user actions: a dataset selector and a "Run comparison" button (an offline research job over
  already-recorded immutable data; places nothing; no promotion control; no order/execution
  control).
- UI surface changes: one new Comparison section on the existing `/structure` page, below Registry.
  No new route.
- Navigation changes: none — `/structure` already ships (iter-1); no nav change this iteration.

## Visual Requirements

- Component patterns: reuse this file's local `Panel`, `LoadingPanel`, `UnavailablePanel`,
  `EmptyState` wrappers and the `NUMERIC_CELL`/`HEADER_CELL`/`LABEL_CELL` constants exactly as J-02
  did; the per-class A/B/C table can follow `ZoneRow`'s class-badge visual language (`Class A/B/C`
  chip) rather than inventing a new badge style. `ClassMapTable` (J-02) is typed
  `Record<string, number>` and is NOT a direct fit for `aggregates_by_class` (whose per-class value
  is an object with `n`/`net_r`/`net_usd`/`win_rate`/`max_drawdown_r`/`insufficient_sample`, not a
  single number) — build a small sibling table for this shape rather than force-fitting
  `ClassMapTable`.
- Layout: single column, appended below the Registry section, same `max-w-7xl` container as the
  rest of the page. A simple two-column (or two-card) side-by-side layout for `v1` vs
  `structure_tape` aggregates reads well on desktop; stack on narrow widths (matches
  `StudyResultsView`'s `grid md:grid-cols-2` precedent for its setup-vs-null-baseline blocks).
- Key visual effects: dark instrument-panel style, amber for the honest-empty/degraded/insufficient
  states (existing `UnavailablePanel`/insufficient-sample chip conventions), font-mono numerics. No
  new chart — this section is tabular only (explicitly out of scope per the spec).
- States to handle: idle (before Run is clicked / no dataset chosen), no datasets registered
  (empty), `queued`/`running` (poll in progress — an amber/slate in-progress panel, mirroring
  `results-status-absence`), `failed` (mirror `results-failed`), `cancelled` (mirror
  `results-cancelled`), `done` (render aggregates; per-class insufficient-sample chips shown inline
  with the real numbers, never as a separate state), backend-unreachable at any step (dataset list
  fetch, POST, or poll).

## Key Test Scenarios

- End-to-end populated comparison: choose a dataset, click Run, both backtests poll to `done`;
  every rendered aggregate/per-class value/`insufficient_sample`/`register` byte-matches
  `GET /research/backtests/{id}` for both `v1` and `structure_tape`; champion still `v1`/`default`
  (matches Registry section + `GET /research/profiles`); founding baseline row renders from the
  ledger. On the keyless reference dataset, expect `structure_tape` to arm zero (or very few)
  trades (no recorded bar series -> no levels to enter against), so its `aggregates.win_rate`/
  `max_drawdown_r` render as an honest `null` (never `0`) and all three `aggregates_by_class`
  entries show `insufficient_sample: true`.
- Register text matches `backtests.py`'s `REGISTER` constant exactly (the fuller string, not
  `docs/goal.md`'s abbreviated paraphrase).
- Honest states, each distinct with a screenshot: no datasets registered; `running`/`queued`
  in-progress; `failed`; `cancelled`; `done`-but-insufficient-n; backend unreachable (dataset fetch,
  POST, and poll each).
- No promotion: confirm no `set_champion_pointer` call exists anywhere in the new diff; champion
  badge is read-only with no button/control that could move it.
- J-01 re-verify: levels/zones chart + zones table still render correctly; the new section does not
  re-occlude `StructureChart`'s overlay (confirm z-index intact — low risk since this section is
  tabular, per the phase spec's own lesson iter-1(a)).
- J-02 re-verify: Registry + champion still render correctly; if the Comparison section re-renders
  a champion badge, confirm its testids are distinct from Registry's (no same-page collision).
- J-04 regression sentinel: `git diff --stat -- apps/backend` is empty; full backend suite green
  (baseline 1146 passed / 1 skipped per iter-2's handoff); `config_fingerprint` recomputes live to
  `4d665603569b9dbf`; 5-link nav intact; `/performance` unaffected.
- Coherence: every new `api.ts` helper returns `null`/an explicit error on failure (never a
  fabricated payload); no client-side recomputation of R/$/win-rate/class partition/champion
  anywhere in the diff.
- **Evidence discipline (lessons.md iter-0):** every scenario above needs a screenshot in
  `reports/qa/goal-structure_ui-iter-3-evidence/` — "renders correctly" on prose alone is `unknown`,
  not `passing`. Per lessons.md iter-1(b): if the auditor fixes any browser-QA FAIL in place, J-03
  stays `partial` until an *independent* browser-QA re-run confirms.

## Out of Scope (confirmed — no drift from docs/goal.md or the phase spec)

- Any backend edit of any kind; any change to `config.py`, `research/levels.py`,
  `research/backtests.py`, `research/strategies.py`, the engine, or `config_fingerprint`.
- Any champion promotion, `set_champion_pointer` call, or PnL-ledger write from the UI.
- Any client-side recomputation of R, $, win-rate, the class partition, or the champion.
- A `/datasets` library-inventory page (roadmap Card 5.9).
- A new `lightweight-charts` chart for the comparison (tabular render only); any change to J-01's
  chart or J-02's registry behavior beyond what's needed to avoid the testid-collision note above.
- New vocabulary ("paper trading" / "annualized" / "expected profit" / advice or imperative
  phrasing); the register text comes from the payload, never a frontend literal.
