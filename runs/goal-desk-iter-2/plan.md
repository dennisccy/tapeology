# goal-desk-iter-2 Execution Plan

Context: Era B "The Desk" (`docs/goal.md`), iteration 2, session `desk`, target journey **J-02
only**, depth **full** (structural: first desk compute manager outside `edge_report_compute.py`;
data-model: resolves two `blueprint.md`-registered-but-placeholder Data-Contract rows).
Required-still-passing: **J-01** (`GET /research/desk/universe` byte-identical to iter-1's
baseline — J-02's own top-up reads J-01's latest snapshot) and **J-07**'s backend/keyless subset
(suite floor, fingerprint pin, widened kept-route capture). Builds on iter-1's shipped universe
subsystem (`desk_universe.py`, `desk_routes.py`, the fixture universe
`tests/fixtures/universe/universe-2026-07-25-817cc184bbb3.json`) — confirmed live against the
current tree. This iteration is backend/CLI-only; `/desk` does not exist until J-04, so nothing on
screen changes. No scope creep found against `docs/goal.md`: every IN SCOPE item traces to Key
Capability 2, and OUT OF SCOPE explicitly fences off J-03–J-06, the frozen research owners, and the
fingerprint pin.

Environment note for the developer/reviewer/QA steps that follow: this pipeline run isolates temp
files — export `TMPDIR`/`TMP`/`TEMP` to
`/home/dennis-chan/.cache/iad/iad.goal-desk-iter-2.14200` before running pytest or any
temp-file-writing command.

## What to Build

- **Pinned top-up timeframe set** as a plain structural constant (NOT a `Config` field —
  mirrors the `PRIOR_PERIOD_TIMEFRAMES` precedent, `levels.py:106`): `{"1h", "4h", "1d", "1w"}`.
  Re-confirm quickly (already verified live for this spec) against `config.py`'s `bar_timeframes`/
  `sr_timeframe_weights`, `levels.py:106`, and `yahoo.py`'s `_INTERVAL_MAP` (`4h` is the local
  `_resample_4h` from `1h`; `8h`/`15m`/`1mo` are out of `_INTERVAL_MAP` and excluded; `5m`/`1m`
  excluded per the desk anti-goal text).
- **New desk-coverage module** — a pure read function over the latest universe snapshot's members
  × the pinned timeframe set, reporting `has_bars` and `latest_window_end_utc` per `(symbol,
  timeframe)`. Reads `bar_index` only — never re-hashes/walks the JSON `BarStore` (T-4, the 5C
  31.4s mistake).
- **Additive `bar_index.py` read-API extension** — confirmed live: `BarIndexHit`
  (`bar_index.py:66`) currently carries only `series_id`/`checksum`/`bar_count`; `window_end_utc`
  IS already a `_SCHEMA` column (`bar_index.py:49`) but is not exposed on any read return today.
  Add a field to `BarIndexHit` (or an equivalent new accessor) that surfaces it — no DB schema
  change, `.lookup()`/`.insert()`'s existing contract and all current callers (the `POST
  /research/bars` store-first coordinator) stay byte-unmodified. Logged as an interpretation call
  in `assumptions.md` per the spec's own NOTES.
- **`GET /research/desk/coverage`** (new, dedicated endpoint — this iteration's build-time
  decision, already reflected in `runs/goal-session-desk/state/blueprint.md`'s Data Contract):
  honest empty payload (`universe_snapshot_id: null`, `members: []`, HTTP 200, never 404) before
  any universe snapshot exists.
- **Desk top-up compute manager** mirroring `EdgeReportComputeManager` (`edge_report_compute.py:108`,
  confirmed live: `trigger`/`cancel`/`main()` at :130/:218/:267) verbatim in shape — one in-flight
  job slot, in-memory process-scoped snapshot (`id`/`state`/`started_utc`/`finished_utc`/`error`/
  `progress`), cooperative cancel, atomic snapshot publish under a lock.
- **Top-up work function** — walks the latest universe snapshot's members × the pinned timeframe
  set; for each pair, calls the SAME existing bar-fetch-and-record logic `POST /research/bars`
  already uses (`routes.py` ~:519, confirmed store-first) **in-process** — never a second
  fetch-and-record implementation. Records one honest outcome per pair: `"reused"` /
  `"fetched"` / `"failed"` (detail preserved, never swallowed) into `progress.outcomes`.
- **Three routes**, mirroring `routes.py:1268/1293/1302` exactly (confirmed live: identical
  trigger/poll/cancel-409 shape already exists for edge-report compute): `POST
  /research/desk/topup/compute` (single-flight trigger, `{"started": bool, "compute": <snapshot>}`),
  `GET /research/desk/topup/compute` (poll; snapshot or `null`), `POST
  /research/desk/topup/compute/cancel` (409 when idle).
- **CLI warmer** (e.g. `python -m app.research.desk_topup_compute`, mirrors
  `edge_report_compute.py`'s `main()`): runs the top-up to completion synchronously for the
  operator's real ~100-symbol run; one progress line per completed pair.
- **Conditional Config field** — only IF a genuinely new semantic knob is needed (e.g. a
  per-timeframe fetch-window/lookback for the top-up's vendor calls): Path A in the SAME commit
  (exclusion-set entry, stability test, counter-test, payload provenance), mirroring the four
  shipped `desk_universe_*` fields (`config.py:1118-1134`, exclusion set at :1567-1570, confirmed
  live). Prefer reuse over inventing a new field. Operational knobs (worker/concurrency cap, if
  any) are env vars, never `Config` fields (the `TAPEOLOGY_EDGE_SWEEP_WORKERS` precedent).
- **Widen the kept-route byte-comparison capture** from iter-1's 14 probed templates to all 24
  kept GET route templates (audit finding T2 — unprobed last time: `/research/levels`,
  `/research/tradability`, `/research/bars/{id}`, `/research/bars/{id}/candles`,
  `/research/datasets/{id}`, `/research/setups/{id}`, and the four `/tape/{ticker}/...` routes),
  captured before/after this iteration's diff against a data dir populated by this iteration's own
  fixture top-up run (not near-empty, so the capture can actually observe cache-warmth-class
  regressions).
- **Tests**: coverage truth-table (incl. honest-empty), top-up resumability + store-first-reuse +
  single-flight + cancel, GET-never-computes on both new GET routes, the pinned-timeframe-set
  assertion against `levels.py`'s live constants, the `bar_index.py` extension proven additive
  (existing `test_bar_index.py` assertions byte-unmodified), honest failure-taxonomy handling
  (`NoDataForWindow`/`VendorTimeout`/`UnsupportedTimeframe`), and Path-A tests if a new Config
  field is added.

## Agents Required

- developer: yes -- implement the desk-coverage module, the additive `bar_index.py` extension, the
  coverage route, the top-up compute manager + work function + 3 routes + CLI warmer, the
  conditional Config field (Path A, only if needed), the widened 24-template kept-route capture,
  and all unit/integration tests described above. Single agent — this iteration is backend-only.
- backend-data: yes -- all of the above (coverage read, bar_index extension, compute manager,
  routes, CLI, tests, fixtures).
- frontend-ux: no -- zero frontend files touched this iteration. No `/desk` page, no nav change, no
  `structure/page.tsx` edit. `blueprint.md`'s Feature/journey-homes table states J-02 has "no
  standalone page" — its badges surface on `/desk` only once J-04 ships.

## Frontend Present
no

## Files to Create/Modify

- `apps/backend/app/research/desk_coverage.py` (new, name at build discretion) -- pinned
  timeframe-set constant + the pure coverage-read function over `bar_index`.
- `apps/backend/app/research/bar_index.py` -- additive-only: new `BarIndexHit` field (or
  accessor) exposing `window_end_utc`; `.lookup()`/`.insert()` signatures and all current callers
  unchanged.
- `apps/backend/app/research/desk_topup_compute.py` (new, name at build discretion, mirrors
  `edge_report_compute.py`) -- the compute-manager class, the top-up work function (reusing `POST
  /research/bars`'s fetch-and-record logic in-process), and the CLI `main()`.
- `apps/backend/app/research/desk_routes.py` -- add `GET /research/desk/coverage` and the three
  `/research/desk/topup/compute*` handlers to the existing `/research/desk` router (already
  mounted in `app/main.py:202`); a new routes submodule is also acceptable if the developer judges
  `desk_routes.py` too large, but must still mount under the same router/prefix.
- `apps/backend/app/config.py` -- ONLY if a new semantic knob is genuinely needed for the top-up's
  vendor calls: add it with Path A in the same commit (exclusion set at :1567-1570, stability +
  counter-test, provenance in the payload it shapes).
- `apps/backend/tests/test_desk_coverage.py` (new) -- truth-table incl. honest-empty, per-member
  per-timeframe assertions, `latest_window_end_utc` exactness, index-read-only call-counting guard
  (T-4), pinned-timeframe-set assertion against `levels.py`'s live constants.
- `apps/backend/tests/test_desk_topup_compute.py` (new) -- `pairs_total == N*4`, resumability
  (cancel-then-resume skips completed pairs), store-first-reuse (second run = all-reused, zero
  vendor calls), single-flight (concurrent trigger returns the same job id), cancel-409-when-idle,
  GET-never-computes, honest failure outcome + run-continues-after-one-failure.
- `apps/backend/tests/test_bar_index.py` -- add assertions proving the extension is additive;
  existing assertions must stay byte-unmodified and passing.
- `apps/backend/tests/fixtures/` -- reuse the existing fixture universe
  (`fixtures/universe/universe-2026-07-25-817cc184bbb3.json`); add/extend a bar-store fixture with
  bars recorded across all 4 pinned timeframes for exactly 2 of a 5-member fixture universe (TC-3/
  TC-4's per-member truth-table), plus an instrumented vendor-fetch seam for call-counting
  (TC-7/TC-10).
- `runs/goal-desk-iter-2/kept-route-baseline-24.txt` / `kept-route-after-24.txt` (new) -- the
  widened TC-13 capture, all 24 kept GET route templates, against a data dir populated by this
  iteration's own fixture top-up run.
- `docs/handoffs/goal-desk-iter-2-dev.md` (new) -- dev handoff, including the honest per-pair
  outcome mix from any real/fixture top-up run and the TC-13 diff result.

## Out of Scope (explicitly excluded this iteration)

- J-03 (screen compute + ledger), J-04 (`/desk` page — `UI_ROUTES` stays 2 rows), J-05 (history +
  `/structure` prefill), J-06 (MCP `desk_universe`/`desk_screen` — suite stays 15 tools) -- all
  deferred per `docs/goal.md`'s stated dependency order.
- Tick-evidence badges -- J-03's screen-row concern, not J-02's coverage payload.
- A `is_fresh`/staleness boolean -- coverage serves raw `latest_window_end_utc` only; J-04's
  display-layer concern.
- Fixing `edge_report_cache._config_content_hash`'s missing exclusion set -- accepted, documented
  latency-only gap (iter-1 audit B1 / lesson); do not edit that frozen, shared mechanism this
  iteration (would bundle a second cross-cutting change into an already-full J-02).
- J-01 hardening (parser `skipped_rows` count; loud B3 corrupt-file replacement) -- binding "do not
  redo," J-01 is DONE per `iteration-state.md`.
- The real ~100-symbol Yahoo top-up run itself -- an operator-run act reported honestly, never a CI
  gate.
- Re-pointing `journey-scripts/J-07.json` step 8, or warming the real-data `/research/setups`
  cache -- no browser QA dispatches this iteration (`Frontend Present: no`); carried forward again
  for J-04.
- Any change to `tradability.py`, `levels.py`, `bars.py`'s store format, or
  `EdgeReportComputeManager` itself -- read/reuse verbatim, single source of truth.
- Any `bar_index.py` DB schema change or change to `.lookup()`/`.insert()`'s existing semantics --
  only the one sanctioned additive read-accessor.
- Any change to the fingerprint pin `08e471b10130e1e2` or its 13 assertion sites -- Path A only.
- Re-probing J-01 acceptance clauses or re-shooting prior screenshots -- already DONE, binding "do
  not redo."

## Notes / Known Traps for the Developer

- Tests must use their OWN temp-scoped universe + bar dirs (`TAPEOLOGY_DESK_UNIVERSE_DIR`/
  `TAPEOLOGY_BAR_DIR` env-override pattern) -- `apps/backend/.data/universe/` already holds a real
  registered snapshot from iter-1 QA; never touch the ambient real dir from a test.
  `apps/backend/.data/setups_scan_cache.db` is currently cold (iter-1 audit B1) -- irrelevant to
  this iteration's hermetic tests, only matters for the next browser-QA pass (J-04).
  Similarly, a real live POST to `/research/desk/universe/fetch` with identical Wikipedia content
  now returns 409 (the prod dir is pre-populated) -- expected, not a bug, if an operator run is
  exercised.
- Skip-count floor is 8 non-decreasing (iter-1 grew it from 7); suite pass floor is 1210
  non-decreasing, per this iteration's own DEFINITION OF DONE.
- `bar_index` reads must be proven index-only (no `BarStore.list()`/full-store-hash call) via an
  instrumented call-counter, not just asserted by inspection (T-4 / TC-5).

## Key Test Scenarios

- Honest empty: no universe snapshot ever registered → `GET /research/desk/coverage` returns 200,
  `universe_snapshot_id: null`, `members: []` (TC-1).
- Truth-table: fixture universe with bars recorded for exactly 2 of 5 members across all 4 pinned
  timeframes → those 2 report `has_bars == true` on all 4, the other 3 report `false` on all 4,
  asserted per-member (TC-2/TC-3); `latest_window_end_utc` matches the exact recorded `bar_index`
  value, never fabricated/rounded (TC-4).
- Index-only latency: `GET /research/desk/coverage` issues zero `BarStore.list()`/full-hash calls
  (TC-5).
- Top-up mechanics: `pairs_total == N*4`; polling shows `state` reaching `"done"` with exactly one
  outcome per pair, each in `{"fetched","reused","failed"}` (TC-6); a second run over the same
  snapshot reports all-`"reused"` with zero vendor calls (TC-7, store-first proven); a run
  cancelled after M of N*4 pairs, then resumed, reuses those M pairs and only attempts the rest
  (TC-8); a concurrent second trigger while one is running returns `started: false` and the SAME
  job id (TC-9, single-flight).
- GET-never-computes: neither new GET route starts a fetch/compute as a side effect, proven via a
  call-counting fixture (TC-10).
- Regression floor: full suite ≥1210 passed / ≥8 skipped after this diff; `Config().config_fingerprint()`
  still `08e471b10130e1e2`, including under any new Config field's non-default override (TC-11);
  `GET /research/desk/universe` byte-identical to iter-1's baseline (TC-12, J-01 stays passing); all
  24 kept GET route templates byte-identical pre/post-diff against a populated data dir (TC-13).
- Honest failure handling: a pair whose vendor call raises `NoDataForWindow`/`VendorTimeout`/
  `UnsupportedTimeframe` reports `outcome == "failed"` with the detail preserved verbatim, and the
  run continues to the remaining pairs rather than aborting (TC-14).
- Idle cancel: `POST /research/desk/topup/compute/cancel` with no job ever run, or the last job
  terminal, returns 409 (TC-15).
