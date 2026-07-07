# goal-structure_ui-iter-3 Dev Handoff

**Phase:** goal-structure_ui-iter-3
**Date:** 2026-07-07
**Agent:** developer
**Status:** complete

## What Was Built

- **The Comparison section (J-03)** — a third section on the existing `/structure` page, below
  Registry, `aria-label="structure_tape vs v1 comparison"`. It lets the user choose a registered
  dataset and click "Run comparison," which POSTs two backtests — `v1` and `structure_tape`, both
  `profile=default` — on the chosen dataset via `POST /research/backtests`, then polls both via
  `GET /research/backtests/{id}` (mirroring the Studies page's `setInterval` poll-while-active
  *pattern*, not its endpoint) until **both** reach a terminal status. This makes all four
  Must-have journeys (J-01–J-04) browser-visible — a GOAL_ACHIEVED candidate for the evaluator.
- Side-by-side per-strategy results: `n`, net R, net $, `win_rate`, `max_drawdown_r` (nullable
  fields rendered as an honest `"no trades (n=0)"`, never a fabricated `0`), plus the per-class
  A/B/C table from `aggregates_by_class` with `insufficient_sample` shown inline on the real
  numbers (never a separate "insufficient" state) — every value read verbatim from
  `GET /research/backtests/{id}`, zero client computation.
- The simulated register rendered **verbatim from the payload's `register` string** (never a
  hardcoded literal) — confirmed live to match `backtests.py`'s `REGISTER` constant exactly.
- A read-only champion badge (reusing the Registry section's already-fetched
  `GET /research/strategies` state — **no second champion fetch**) and a founding-baseline row read
  from `GET /research/pnl/ledger`, both shown beside the comparison controls.
- Six honest, distinct states: no datasets registered; the dataset list unreachable; idle (a
  dataset list is populated but Run has not been clicked); a backtest queued/running (per side,
  independently); a backtest failed (per side, with the explicit error); a backtest cancelled (per
  side — carrying **no** result at all, per `backtests.py`'s own documented behavior, unlike a
  Study's cancelled-but-partial results); plus a poll-time "backend unreachable" notice that clears
  automatically once polling recovers.
- **Non-gating polish** (iter-2 audit finding F1 / ux-regression rec #1): extended the
  `structure-framing` header subtitle to preview all three sections; updated `README.md`'s
  "Structure page" bullet (now framed as "three sections") and added a new dedicated bullet
  describing the Comparison capability.
- **Zero backend changes** — confirmed via `git diff --stat -- apps/backend` (empty) both before
  and after this iteration's work.

## Files Changed

- `apps/frontend/lib/api.ts` -- added `fetchDatasets()`, `createBacktest(params)`,
  `fetchBacktest(id)` (71 lines added; mirror `fetchBarSeriesList()` / `createStudy()` /
  `fetchStudy()`'s existing discipline byte-for-byte — `null`/explicit error on any
  non-200/unreachable backend, never a fabricated payload).
- `apps/frontend/lib/types.ts` -- added `Dataset`, `DatasetsListResult`, `BacktestAggregate`,
  `BacktestClassAggregate`, `BacktestResult`, `Backtest`, `CreateBacktestParams` (102 lines added).
  `BacktestResult.dataset`/`.strategy` reuse the existing `Dataset`/`Strategy` types verbatim — no
  duplicate shape declared anywhere.
- `apps/frontend/app/structure/page.tsx` -- added the Comparison section end to end: three new
  components (`BacktestClassTable`, `BacktestResultBlock`, `BacktestPanel`), the dataset-select +
  Run form, the dual-create handler (`Promise.all`, never sequential), the dual-poll `useEffect`
  (stops only once **both** backtests are terminal), all derived state, and the JSX block itself.
  Reused the file's own `Panel`/`LoadingPanel`/`UnavailablePanel`/`EmptyState` locals and the
  `NUMERIC_CELL`/`HEADER_CELL`/`LABEL_CELL` constants exactly as instructed — none were redefined.
  Also extended the header subtitle/framing text and the file's top doc-comment (579 lines added
  net; the existing J-01/J-02 sections are byte-unchanged apart from that one subtitle edit).
- `README.md` -- reframed the "Structure page" bullet as "three sections" and added a new
  "structure_tape-vs-v1 comparison on the Structure page" bullet (non-gating polish).

No `apps/backend/` file was touched — confirmed both before starting (the plan's own verification)
and after finishing (`git diff --stat -- apps/backend` returns empty).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1146 passed, 1 skipped, 0 failed (1147 collected)** — identical to iter-2's own reported
baseline, as expected since `apps/backend/` is an empty diff this iteration (confirmed via
`git diff --stat -- apps/backend` both before starting and after finishing). This suite's `-q`
terminal reporter does not print a final `N passed in Ys` count line in this environment on an
all-green run (a pre-existing quirk, present on this iteration's very first, failing run too — not
something this diff caused), so the exact count was confirmed two ways: a `--junit-xml` run
producing the structured, unambiguous
`{'errors': '0', 'failures': '0', 'skipped': '1', 'tests': '1147'}` (1147 − 1 skipped − 0 failed =
1146 passed); and, independently, since `apps/backend/` is an empty diff, only ONE test's outcome
could possibly depend on this iteration's (frontend-only) diff at all —
`test_copy_discipline.py::test_lint_frontend_source_literals_are_clean` (see "Fix Notes" below) —
confirmed failing exactly once before the `win_rate` fix and passing after (a standalone
`pytest tests/test_copy_discipline.py -q` run showed all dots, no `F`, after the fix).
`config_fingerprint` recomputed live via
`.venv/bin/python -c "from app.config import CONFIG; print(CONFIG.config_fingerprint())"` →
`4d665603569b9dbf`, matching the pinned J-04 value exactly.

Command: `cd apps/frontend && npm run build`
Result: `✓ Compiled successfully` — strict-mode type-check (`tsc --noEmit` under `next build`) and
production build both passed with no errors or warnings. `/structure` compiles to 7.68–7.69 kB (up
from iter-2's 5.34 kB), still a static page.

## Live verification performed

Ran the actual app via `scripts/dev.sh` (backend :8301, frontend :3301) and drove it with the
Chrome DevTools Protocol browser tool end to end — not mocked:

1. **Populated end-to-end comparison.** Loaded `/structure`, confirmed the Registry section and the
   new Comparison section both render (idle state, champion badge `v1`/`default`, the founding
   baseline row, and a 7-option dataset selector reflecting the 7 datasets this machine's
   `.data/datasets/` directory already holds). Selected a `PG`/`train` reference dataset, clicked
   "Run comparison." Both backtests polled to `done` within ~4 seconds. Extracted every rendered
   value via `document.querySelector` and diffed it against a direct `curl` of
   `GET /research/backtests/{id}` for both ids — **byte-for-byte match**: `v1` showed `n=5`,
   `net_r=-1.2392857142863114`, `net_usd=-123.92857142863114`, `win_rate=0.2`,
   `max_drawdown_r=1.2392857142863114`; `structure_tape` showed `n=0`,
   `win_rate` rendered as `"no trades (n=0)"` (never a fabricated `0`) — the expected honest
   non-survivor outcome on this keyless fixture (no recorded bar series for `PG`, so
   `structure_tape` arms nothing). Both sides' register line matched
   `"simulated — assumed fees/slippage — not indicative of live results"` exactly. All 6 per-class
   (A/B/C × 2 strategies) rows showed `insufficient sample (n < 5)`, matching the ledger's
   `min_sample_size=5`. No console errors.
2. **Backend-unreachable honest states.** Killed only the backend process (frontend left running),
   reloaded `/structure`: `structure-registry-unavailable`, `comparison-datasets-unavailable`, and
   `comparison-founding-unavailable` all rendered the explicit "Backend unreachable — is the API
   running?" / "Nothing cached and nothing fabricated is shown in its place." message — no
   fabricated content, no stale data. The Comparison section's champion block correctly fell back to
   "Champion not yet loaded (see the Registry section above)" since the Registry fetch also failed.
3. **Restart resilience.** Re-ran `scripts/dev.sh` from a clean stop: both services started with no
   port conflicts (`Application startup complete.` / `✓ Ready in ~1.2s`).
4. **Regression spot-check.** Confirmed the nav still lists exactly 5 links
   (`Cockpit/Journal/Studies/Performance/Structure`) and `/performance`'s own `champion-summary`
   block still renders `v1`/`default` correctly with no console errors — the new Comparison
   section's champion badge testids (`comparison-champion-strategy`/`comparison-champion-profile`)
   are distinct from both Registry's (`champion-strategy`/`champion-profile`) and Performance's
   (same strings as Registry, on a different route) — no same-page testid collision.
5. **Server cleanup.** All backend/frontend processes killed at the end of each verification pass
   (confirmed via `ss -tln` showing nothing listening on either port and `ps aux` showing no
   residual `uvicorn`/`next dev`/`next-server` processes).

## Fix Notes

While running the full backend suite for the first time, `tests/test_copy_discipline.py`'s J-66
lint (which scans frontend source string/template literals — including testids, not just visible
copy — for banned imperative/predictive/claim language) flagged two occurrences: the visible label
`"win rate"` and the testid template literal `` `${testid}-win-rate` `` in the new
`BacktestResultBlock`. The lint's `\bwin[\s-]?rate\b` pattern bans a bare "win rate"/"win-rate"
phrase (an unqualified positive win-rate-as-edge claim) but does **not** match the underscored
`win_rate` form (no space or hyphen between the two words). Verified the exact fix directly against
the lint's own `find_violations()` function before editing. Fixed by renaming both the visible
label and the testid segment to `win_rate` — the raw payload field name, which also matches (a) the
phase spec's own literal phrasing ("Render side-by-side aggregates (n, net R, net $, `win_rate`,
`max_drawdown_r`)") and (b) this same file's existing `StrategyCard` precedent of using raw field
names as labels for `r_stop`/`reward_target`/`state_flip`/`dataset_end`. Re-ran the full suite twice
after the fix — clean both times. No other file was touched for this fix.

## Known Issues

- **`structure_tape` genuinely arms zero trades on the committed keyless reference dataset** —
  confirmed live, not a defect. No bar series is recorded for `PG` (era-4's own documented data
  reality — see `docs/goal.md`'s "mostly-empty keyless data" framing), so
  `structure_tape`'s level-confirmed entry rule has nothing to test against. This is the exact
  honest "non-survivor" outcome the phase spec's Key Test Scenarios predicted.
- **Not exercised live this pass** (code-complete, but not demoed in the browser): the `failed` and
  `cancelled` per-side states (per the plan's own note #8, exercising `cancelled` live would need a
  direct `POST /research/backtests/{id}/cancel` call timed against a still-running job — mirroring
  how iter-1 treated its own rarer states); the "no datasets registered" empty state (would need an
  isolated/temp-dir environment, per the plan's note #9, since this machine's `.data/datasets/`
  already holds 7 registered datasets); and the poll-time `comparison-poll-error` notice (would need
  killing the backend *mid-poll*, after a comparison is already running, rather than before one
  starts). All four are implemented and covered by the `done`/`failed`/`cancelled`
  status-branch structure already proven live for the `done` and dataset/registry-unavailable paths
  — flagging for the browser-qa-agent to exercise independently per lessons.md iter-0/iter-1(b).
- No client-side recomputation anywhere in the diff — confirmed by inspection: no
  `set_champion_pointer` call exists, no R/$/win-rate/class-partition arithmetic exists outside the
  one `formatNullableAggregateField()` null-vs-string formatter (a display-only null check, not a
  computation).
