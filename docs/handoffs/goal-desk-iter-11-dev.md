# goal-desk-iter-11 Dev Handoff

**Phase:** goal-desk-iter-11
**Date:** 2026-07-28
**Agent:** developer
**Status:** complete

## What Was Built

J-09 — a durable, append-only record of what every desk bar top-up run attempted, so a run's
outcome survives past the next run superseding the in-flight compute snapshot.

- New module `app/research/desk_topup_log.py`: `TopupRunStore` — a checksum-verified, append-only
  JSON-file store (one frozen file per completed top-up run), mirroring `UniverseStore`/
  `ScreenStore`'s load/checksum discipline. Unlike those two stores it performs **no content-keyed
  dedup** — every terminal run is its own distinct event, so `record()` always writes a brand-new
  file (no "already recorded" refusal path exists). `resolve_desk_topup_log_dir` mirrors
  `resolve_desk_screen_dir` exactly (`TAPEOLOGY_DESK_TOPUP_LOG_DIR` env override, else a sibling
  directory of the caller's own resolved universe dir — zero new `Config` field).
- `record_topup_run(...)` — the ONE shared writer function (a thin free function over
  `TopupRunStore.record`), called from exactly two places and nowhere else:
  - `DeskTopupComputeManager.trigger()`'s worker (`_work`), at BOTH its exit paths: the normal
    `"cancelled"`/`"done"` path (using `run_topup`'s own return value directly — proven
    byte-identical by a spy test) and the `except` branch for a whole-job `"failed"` (using a local
    `collected` list mirroring what `_publish` saw before the crash, independent of the shared
    `self._snapshot` to avoid any race with a superseding job).
  - The CLI's `main()`, once, after `run_topup(...)` returns successfully (the CLI has no cancel
    signal and always terminates `"done"`; an uncaught crash before this line is the correct
    interrupted-run case — zero record, never guarded against).
- `universe_snapshot_id` and `requested_window` (`{"start", "end"}`, one `_fetch_window_now()` call
  captured ONCE per run, before the walk starts) are threaded through as plain local/closure values
  in both callers — never added to `self._snapshot` (the manager's existing job-progress dict stays
  exactly its J-02 shape). `pairs_attempted` is derived from `len(outcomes)`, never a separately
  tracked counter.
- New route `GET /research/desk/topup/runs` in `desk_routes.py`: `{"runs": [...meta-only...],
  "latest": <full record>|null}`, honest-empty `{"runs": [], "latest": null}` HTTP 200 before any
  run, never a 404. `runs` entries carry every field except `outcomes` (mirrors the screen list's
  meta-only convention). A pure read — no new POST, no new compute manager; the log is written
  internally by the existing top-up trigger/CLI paths.
- `run_topup`/`_run_one_pair` (`desk_topup_compute.py:123-188`) are byte-unchanged — verified via
  `git diff` on those functions being empty and via a spy test proving the persisted record's
  `outcomes` are byte-identical to what `run_topup` itself returned.
- `app/mcp/__init__.py` needed zero code change: `/research/desk/topup/runs` is already reachable
  through the existing `ALLOWED_GET_PREFIXES` (`/research/`); `_STATIC_PATHS` count stayed exactly
  11, and `test_mcp_server.py`'s 17-tool contract (unmodified) still passes.
- Frontend: a new read-only "Top-up Runs" section on `/desk` — `TopupRunsTable` (meta-only, every
  recorded run: date, id, terminal state, attempted-of-total, universe snapshot) plus
  `LatestTopupRunDetail` (the latest run only — per-outcome counts, every failed pair's detail
  rendered verbatim and un-truncated, the honest unreached-pairs count). Fed by a 4th mount-time GET
  (`fetchDeskTopupRuns`) and re-fetched once when an in-flight top-up job reaches a terminal state
  (mirrors the screen compute poll's own "on terminal, refresh the durable list" precedent). No new
  interactive control — pure read-only disclosure, per this iteration's own OUT OF SCOPE text.

## Interpretation calls (logged in `runs/goal-session-desk/state/assumptions.md`, iter-11 entries)

1. **`requested_window` capture point** — captured once per run in the caller (`trigger()`/
   `main()`), not re-derived inside the writer or a second time inside `_run_one_pair` — the plan's
   own trap #3, implemented as written.
2. **Section placement** — rendered independent of whether a screen has ever been computed (a new
   top-level `<section aria-label="Top-up runs">` after the screen-state conditional, not nested
   inside `DeskPopulatedScreen`/beside Screen History as the plan's own non-binding suggestion
   read). A top-up run is a wholly separate operator act from a screen run; gating its disclosure
   behind "a screen must exist first" would hide real recorded history for no reason tied to what
   the data depends on, and would make TC-12's honest-empty screenshot only reachable after also
   running a screen it does not require.
3. **Per-outcome counts scope** — shown only for the latest run (the only record the backend's own
   meta-vs-full split ever gives `outcomes` for); historical `runs` rows show only what their meta
   actually carries (date, id, state, attempted-of-total, universe snapshot).

## Files Changed

Backend — new:
- `apps/backend/app/research/desk_topup_log.py` — `TopupRunStore`, `resolve_desk_topup_log_dir`,
  `record_topup_run`.
- `apps/backend/tests/test_desk_topup_log.py` — 15 tests: store discipline (checksum/append-only/
  no-dedup/no-update-method), corruption surfaced explicitly, interrupted-run-leaves-no-record,
  second-run-appends-without-touching-first, dir-resolution env override.

Backend — modified:
- `apps/backend/app/research/desk_topup_compute.py` — threads `universe_snapshot_id` +
  `requested_window` through `trigger()`/`main()`; calls `record_topup_run` at both `_work` exit
  paths and once in the CLI; `trigger()` gained a new required keyword-only-by-convention
  `topup_run_store: TopupRunStore` parameter (every existing call site updated).
- `apps/backend/app/research/desk_routes.py` — `get_topup_run_store` dependency, `GET
  /topup/runs` route, `trigger_desk_topup_compute` now injects `topup_run_store`.
- `apps/backend/tests/test_desk_topup_compute.py` — extended `manager_env`/`route_ctx` fixtures
  with the new store; added 6 new test functions (byte-identical-to-`run_topup`'s-return spy test,
  honest-empty + populated route tests, dir-resolution-under-`route_ctx` test, CLI shape-parity
  test, CLI no-universe-persists-nothing test) plus inline TC-4/TC-5/TC-6 assertions appended to 3
  existing scenario tests (cancelled run, failing pair, second run) — now 23 tests total (was 17).

Frontend — modified:
- `apps/frontend/lib/types.ts` — `DeskTopupRunMeta`, `DeskTopupRun`, `DeskTopupRunsListResult`
  (reuses the existing `DeskTopupOutcome` type verbatim for the `outcomes` array shape).
- `apps/frontend/lib/api.ts` — `fetchDeskTopupRuns()`, mirroring `fetchDeskScreen()`'s exact
  `{ok, data, error}` shape.
- `apps/frontend/app/desk/page.tsx` — `TopupRunsTable`/`TopupRunRow`/`LatestTopupRunDetail`/
  `TopupRunsSection` components (reusing `Panel`/`EmptyState`/`HEADER_CELL`/`LABEL_CELL`/
  `NUMERIC_CELL`); new `topupRunsResult` state; 4th mount-time GET; re-fetch on top-up-compute
  terminal transition; new top-level `<section aria-label="Top-up runs">`.

Not touched (verified via `git diff --stat`, empty): `tradability.py`, `levels.py`, `bars.py`,
`StructureChart.tsx`, `PriceChart.tsx`, the engine, `desk_coverage.py`, `desk_screen.py`,
`app/config.py`, `app/mcp/__init__.py`, `desk_universe.py`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1367 passed, 8 skipped, 0 failed** (floor was 1346 passed / 8 skipped — net +21 new tests,
0 regressions).

Also run individually during TDD: `test_desk_topup_log.py` (15/15), `test_desk_topup_compute.py`
(23/23), `test_mcp_server.py` + `test_copy_discipline.py` + `test_desk_universe.py` +
`test_desk_screen.py` + `test_desk_screen_compute.py` (re-run only, no code change expected — all
green, confirming zero regression to J-01/J-02/J-03/J-06/copy-lint).

Frontend: `npx tsc --noEmit` clean; `rm -rf .next && npm run build` — compiled successfully, `/desk`
prerendered (6.22 kB, up from its prior size, reflecting the new section), zero type errors, zero
lint errors.

Fingerprint / diff checks:
- `Config().config_fingerprint()` → `08e471b10130e1e2` (unchanged, as required).
- `git diff --stat` for `tradability.py`/`levels.py`/`bars.py`/`StructureChart.tsx` — empty.
- MCP: `_STATIC_PATHS` count unchanged at 11 (no new named tool); `test_mcp_server.py`'s
  `EXPECTED_TOOLS` (17) passes unmodified.

## Pre-handoff verification

- **Service startup**: `scripts/start-backend.sh` + `scripts/start-frontend.sh` on the project's
  deterministic ports (8301/3301) — clean startup with no errors, twice in a row (stop, then start
  again — no port conflicts). Live curl against the freshly-restarted backend confirmed
  `GET /research/desk/topup/runs` → `{"runs":[],"latest":null}` (honest empty against the ambient
  store, which has never run a J-09-aware top-up) and `GET /desk` on the frontend → HTTP 200 with
  "Top-up Runs" / the `desk-topup-runs-*` testids present in the server-rendered HTML. Both
  processes were stopped again before finishing this handoff (server-cleanup rule) — nothing was
  left running.
- **External integrations**: none new this iteration (no new adapter/vendor seam) — the top-up's
  existing Yahoo-adapter seam is unchanged; all TDD tests use `FakeAdapter`/monkeypatch, matching
  the existing J-02 pattern. A real ~100-symbol top-up run against the live vendor is explicitly OUT
  OF SCOPE this iteration (an operator-run act, not a suite gate).
- **Native dependencies**: none added.

## Known Issues

- No golden replay script (`journey-scripts/J-09.json`) or demo-narrator walkthrough was recorded —
  per this repo's pipeline division of labor, those are the browser-qa-agent's and demo-narrator's
  own steps (confirmed via `git log` on the existing `journey-scripts/J-08.json`, which was
  authored by an earlier iteration's browser-qa-agent commit, never a developer commit), not part of
  this dev dispatch.
- The historical `runs` list rows show only meta fields (date, id, state, attempted-of-total,
  universe snapshot) — no per-outcome (reused/fetched/failed) breakdown, since the backend's
  meta-only projection never carries `outcomes` for anything but the latest run (see interpretation
  call 3 above). If a future iteration wants a full breakdown on every historical row, the backend
  schema would need a new `outcome_counts` aggregate field (a non-fingerprint-affecting, Path-
  irrelevant addition derived from `outcomes`) — not built here since it is not what the current
  Data Contract shape specifies, and adding it would be a spec deviation, not a spec implementation.
- The Top-up Runs section is placed as its own top-level section after the screen conditional
  (visible regardless of screen state), not literally nested beside the Screen History table inside
  `DeskPopulatedScreen` as the plan's own (explicitly non-binding) suggested position read — see
  interpretation call 2. Functionally it still reads as adjacent to the screen content in the page's
  top-to-bottom flow.
- I did not attempt a real, credentialed ~100-symbol top-up run against the live Yahoo vendor (out
  of scope this iteration, per the phase spec's own OUT OF SCOPE list) — the mechanism is proven
  only against `FakeAdapter`/fixture-scoped inputs, as required.

## Addendum — auditor (2026-07-28), supersedes the suite counts above

The audit pass (`docs/handoffs/goal-desk-iter-11-audit.md`) added two missing spec'd tests; no
production code was changed. The counts recorded above were accurate for the developer's own run and
are left as written — the CURRENT numbers are:

- Full suite: **1369 passed, 8 skipped, 0 failed** (was 1367/8 at dev handoff time; +2 auditor tests).
- `tests/test_mcp_server.py`: **35 passed** (was 34) — `+ test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool`, closing TC-9's
  `get_endpoint("/research/desk/topup/runs")` byte-identity clause, which no lane had exercised.
- `tests/test_desk_topup_compute.py`: **24 passed** (was 23) — `+ test_a_walk_interrupted_before_the_terminal_write_leaves_zero_run_record`, replacing the
  vacuous store-level-only coverage of TC-7 with a walk that genuinely runs pairs and then dies
  before the terminal write.

`Config().config_fingerprint()` re-verified `08e471b10130e1e2`; `git diff --stat` for
`tradability.py`/`levels.py`/`bars.py`/`StructureChart.tsx`/`config.py`/`mcp/__init__.py`/
`test_copy_discipline.py` still empty.
