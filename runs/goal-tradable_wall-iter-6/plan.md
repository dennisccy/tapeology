# goal-tradable_wall-iter-6 Execution Plan

Target journey: **J-05** (`/structure` decluttered — Tradable Map default + Case Studies + Edge
Report). Required-still-passing: J-01, J-02, J-03 (keyless substrate), J-04, J-07. This is a
pure-frontend render iteration over three backend read surfaces that iters 1–5 already built and
stabilized (`tradability.py`, `setups.py`, `edge_report.py`) — the single backend touch is the
iter-5-evaluator-recommended atomic hardening of the B3 scan cache write, closing a torn-read
window before this iteration becomes the first caller to fire `/setups` + `/setups/{id}` +
`/edge-report` concurrently from one page load.

## What to Build

- Harden the existing B3 scan-cache write in `setups.py` (`compute_setups`, lines ~373–379) so the
  check-and-set is atomic against concurrent callers — no other backend behavior changes.
- Add frontend API client functions + types for the three not-yet-wired endpoints:
  `GET /research/tradability`, `GET /research/setups` (+ optional filters), `GET
  /research/setups/{id}`, `GET /research/edge-report`.
- Make **Tradable Map** the new default view on `/structure`: chart candles + ≤10 band overlays +
  a bands table (range, side, quality score, inherited class, member count, round-number flag,
  `basis_as_of`) — read verbatim from `GET /research/tradability`.
- Move the current raw levels + confluence-zones panels behind an explicit **"raw levels" toggle**,
  off by default; on, they render byte-identically to today (era-5 behavior preserved).
- Add a **Case Studies** section: registry table from `GET /research/setups` (symbol/reaction
  filters) + a row drill-in from `GET /research/setups/{id}` (band, reaction, forward returns,
  `tape_timeline` or an honest empty state, honest recency-boundary disclosure via
  `reaction_boundary_truncated` + `effective_reaction_horizon_bars`).
- Add an **Edge Report** section rendering `GET /research/edge-report` verbatim (per-cell n/R/$ +
  register + null baseline; an empty/all-`insufficient_sample` report is a valid, first-class
  render, never hidden or fabricated).
- Keep the era-5 **Fetch from Yahoo Finance** control, **provenance badge**, **Registry**, and
  **Comparison** sections intact, repositioned below the three new sections.

## Agents Required

- backend-data: yes — the single atomic-rebind/Lock hardening in
  `apps/backend/app/research/setups.py` (`_SCAN_CACHE` check-and-set only) + one new concurrency
  test. No other backend file is in scope.
- frontend-ux: yes — new API client fns/types + the `/structure` page's three new sections + the
  raw-levels toggle + the Case Studies drill-in.

Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/research/setups.py` — replace the two non-atomic dict-key writes
  (`_SCAN_CACHE["key"]=key` then `["result"]=result`) with a single atomic publish: either rebind
  one immutable `(key, result)` tuple (read once — atomic under the GIL, no new import) or wrap the
  check-and-set in a `threading.Lock`. `compute_setups`'s signature, the scan body
  (`_run_full_panel_scan`), its output, and every caller (`routes.py`, `edge_report.py`) stay
  byte-identical — this is the ONLY backend change this iteration.
- `apps/backend/tests/test_setups.py` — new concurrency test proving two threads racing a cold
  cache never observe a torn key/result pair (no key paired with a stale/`None` result, no 500);
  the existing B1/B3 tests (`test_cache_hit_is_byte_identical_to_a_fresh_uncached_scan`,
  computed-once spy, checksum-bust spy, enriched-detail-never-leaks, pinned AAPL 2026-06-22
  non-boundary assertions) must stay green unmodified in behavior.
- `apps/frontend/lib/types.ts` — add types mirroring the backend JSON verbatim: a tradability band
  (`side`, `price_low`, `price_high`, `class`, `quality_score`, `round_number`, `member_count`,
  `members[]` — reuse the existing `SrLevel`-shaped member entry), the tradability response
  (`symbol`, `as_of`, `bands[]`, `no_bar_series_for_symbol`, `basis_as_of`); a setup event (`id`,
  `symbol`, `session_date`, `band`, `touch_ts/open/high/low/close/volume`, `reaction`,
  `forward_returns[]`, `effective_reaction_horizon_bars`, `reaction_boundary_truncated`,
  `tape_timeline[]`) and the list/detail wrapper shapes; an edge-report cell (`strategy_id`,
  `band_class`, `band_side`, `reaction`, `feed`, `dataset_ids[]`, `measurement`, `null_baseline`,
  `insufficient_sample`) and the report wrapper (`register`, `pnl_min_sample_size`, `train.cells[]`,
  `holdout.cells[]`, `surviving_train_cells[]`).
- `apps/frontend/lib/api.ts` — add `fetchTradability(symbol, asOf)`, `fetchSetups(filters?:
  {symbol?, reaction?, band_class?})`, `fetchSetupDetail(id)`, `fetchEdgeReport()`, each returning
  the file's established `{ok, data, error}` (or named-field equivalent) shape and surfacing the
  backend's `detail` verbatim on non-200 (see `fetchLevels`/`fetchStrategies` immediately above for
  the exact pattern to copy).
- `apps/frontend/app/structure/page.tsx` — the main change: Tradable Map becomes the default view
  (replaces "Price chart — S/R levels" + "Confluence zones" as the landing render — those two move
  under a new "Show raw levels" toggle, off by default, unchanged when on); new Case Studies section
  (table + filters + drill-in); new Edge Report section; existing Fetch control / Registry /
  Comparison sections retained, moved below the new sections.
- `apps/frontend/components/StructureChart.tsx` (extend) or a new sibling component — draw band
  price-areas/lines alongside the existing candle + level-line rendering, reusing the
  `lightweight-charts` primitives (`createPriceLine`, etc.) already established in this file.
  Prefer additive props over rewriting existing behavior — the raw-levels toggle's "on" state must
  keep rendering byte-identically to today.
- New small presentational components as needed for the bands table / case registry table /
  drill-in / edge-report table, following this page's existing `Panel` / `EmptyState` /
  `UnavailablePanel` / `LoadingPanel` conventions — no new visual system.

## UI Evolution

- **New user-facing capability:** loading a symbol as-of a session now shows at most ~10
  quality-scored tradable bands by default (not 1,800 raw level lines); the operator can browse
  every historical band-touch case with its reaction, forward returns, and (when recorded) tape
  timeline, and read a 3-way strategy edge report — all on `/structure`.
- **New information displayed:** tradable bands (range, side, quality score, A/B/C class, member
  count, round-number flag, morning-markup `basis_as_of`); the case registry (symbol, session date,
  band, reaction, forward returns, recency-boundary honesty fields); per-event tape timelines;
  edge-report cells (strategy × class × side × reaction × feed, n/R/$ + full register, null
  baseline).
- **New user actions:** a "raw levels" toggle (off by default); Case Studies symbol + reaction
  filters; clicking a Case Studies row opens its drill-in.
- **UI surface changes:** `/structure` gains three sections — Tradable Map (new default), Case
  Studies (+ drill-in), Edge Report — plus the raw-levels toggle; the era-5 Fetch control,
  provenance badge, Registry, and Comparison sections remain, repositioned below.
- **Navigation changes:** none — no new nav entry, nav skeleton is frozen for this era (goal.md
  anti-goal "No new nav entry").

## Visual Requirements

- **Component patterns:** reuse the page's existing `Panel` wrapper per new section;
  `EmptyState` / `UnavailablePanel` / `LoadingPanel` for honest states (each new section gets its
  own distinct testid + copy, never shared, per this page's established precedent); plain
  `border-collapse` tables (matching `ZoneRow` / `BacktestClassTable`'s font-mono numeric styling)
  for the bands table, case registry, and edge-report cells; a toggle control matching the
  existing button/select visual language (`border-slate-600` / `bg-slate-800` family).
- **Layout:** Tradable Map keeps the chart-above-table layout the current Levels & Zones section
  already uses; Case Studies is a filterable table with a row-click drill-in (reuse `Panel` for the
  drill-in rather than introducing a new modal system, unless a modal is materially simpler); Edge
  Report is a data table grouped/sorted by strategy, in `BacktestClassTable`'s per-class breakdown
  style.
- **Key visual effects:** none new — stay inside the page's existing dark instrument-panel style
  (slate surfaces, restrained borders, font-mono numerics, amber for honest-empty/degraded states).
  No glassmorphism/glow additions; this is a data-density page, not a marketing surface.
- **States to handle per new section:** loading; honest empty (`no_bar_series_for_symbol`, zero
  bands, zero events, empty/all-`insufficient_sample` edge report); degraded/unreachable
  (`UnavailablePanel` with the backend's `detail` verbatim, including a malformed-`as_of` 422); and
  populated. The drill-in additionally needs its own distinct truncated-horizon disclosure state
  (`reaction_boundary_truncated: true`) and its own distinct "no recorded tape for this event"
  state (`tape_timeline: []`) — never presented as a full-horizon reaction or a silently-missing
  timeline.

## Key Test Scenarios

- **Backend:** existing B1/B3 `setups.py` tests stay green (cache byte-identity, computed-once
  spy, checksum-bust spy, enriched-detail-never-leaks, pinned AAPL 2026-06-22 non-boundary
  assertions). NEW: a concurrency test proving two threads racing a cold cache never observe a
  torn key/result pair (no key paired with a stale/`None` result, no 500).
- **Frontend unit:** the four new API client fns return the `{ok, …, error}` shape and surface the
  backend `detail` verbatim on non-200 (422 malformed `as_of`, unreachable backend); the
  raw-levels toggle defaults off and its "on" render is unchanged from before this iteration;
  boundary-event rendering keys off `reaction_boundary_truncated` (never rendered as a
  full-horizon reaction).
- **Browser (J-05, primary — against the operator's already-populated 12-symbol panel store, the
  same store J-01/J-02/J-04 were verified against):** load AAPL as-of the pinned 2026-06-22
  session — (1) Tradable Map renders by default, ≤10 bands total, including a resistance band
  spanning the ~300.48–302.07 rejection cluster with `round_number` flagged, ranking top-2 by
  `quality_score`; (2) toggling "raw levels" on renders the pre-existing all-levels view
  unchanged, off returns to the map; (3) Case Studies lists events with working filters, and the
  pinned AAPL 06-22 ~300 row's drill-in shows `reaction: rejected` with negative forward returns
  and its honest `tape_timeline` state; (4) Edge Report renders `GET /research/edge-report`
  verbatim, including the expected empty/all-`insufficient_sample` state on the keyless
  PG-only-dataset fixture; (5) the era-5 Fetch-from-Yahoo control and `FeedBasisBadge` still work.
  Screenshot every state.
- **Recency-boundary disclosure (separate from the pinned case):** the pinned AAPL 2026-06-22 event
  is a fully-formed historical reaction, NOT a boundary case. Per the iter-5 dev handoff's live
  smoke test, boundary events (`reaction_boundary_truncated: true`) sit near each symbol's
  *most-recent* stored session (13/801 real events on the operator's store, e.g. an AAPL event
  around 2026-07-13). Verify the drill-in for one such event (found via the unfiltered or
  symbol-filtered Case Studies list) shows the truncated-horizon disclosure honestly.
- **Regression:** J-01/J-02/J-04/J-07 stay green; `config_fingerprint` stays `4d665603569b9dbf`;
  `git diff --name-only -- apps/` touches only the files listed above (no `tradability.py` /
  `edge_report.py` / `levels.py` / `strategies.py` / `backtests.py` / `config.py` / `datasets.py`
  / engine / adapters edits beyond the one `setups.py` cache hardening); the frontend
  copy-discipline lint (`test_copy_discipline.py`, which walks `apps/frontend/components` +
  `apps/frontend/app` automatically) stays green over all new page copy — no imperative/prediction
  language, no "win rate"/"profit"/"paper trading"/"annualized" vocabulary, simulated $ figures
  keep the "simulated — not indicative of live results" register.

## Notes / Assumptions

- This iteration touches **zero** frozen research modules besides the scoped `setups.py` cache
  hardening — `tradability.py`, `edge_report.py`, `levels.py`, `strategies.py`, `backtests.py`,
  `config.py`, `datasets.py`, the engine, and the adapters are all out of scope, per both the phase
  spec and `docs/goal.md`'s frozen-foundation anti-goal invariants; the tuple-rebind vs.
  `threading.Lock` choice for the cache fix is an implementation detail left to the developer.
- Out of scope (explicitly deferred per the phase spec): J-06 cockpit confluence (band overlay +
  chip on `PriceChart`) — queued for iter-7; any change to raw levels/zones rendering itself; any
  restructuring/removal of the era-5 Fetch control, provenance badge, Registry, or Comparison
  sections; the credentialed J-03 ≥10-window recording headline (operator-gated, parallel carry —
  the drill-in shows `tape_timeline` when a recorded dataset exists and an honest empty state
  otherwise); re-keying `_SCAN_CACHE` off something other than `id(config)` (a test-only flakiness
  concern per iter-5's coherence review, not a correctness issue — leave alone unless the atomic
  fix changes it for free).
- Zero client recomputation is the central rail here (this is what the coherence-auditor
  hard-fails): every band score/class/range, reaction, forward return, tape state, and edge-report
  cell must be `String(value)`-verbatim from its owning endpoint, matching this page's own
  established precedent (`zone.score`, `zone.class`, etc.) — never re-derived in the browser.
- No drift from `docs/goal.md` detected — this plan implements exactly J-05's steps and acceptance
  criteria as specified in `docs/phases/goal-tradable_wall-iter-6.md`, layered on the already-shipped
  J-01/J-02/J-04 backend surfaces with no duplication of prior work.
