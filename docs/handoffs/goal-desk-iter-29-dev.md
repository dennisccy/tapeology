# goal-desk-iter-29 Dev Handoff

**Phase:** goal-desk-iter-29
**Date:** 2026-07-31
**Agent:** developer
**Status:** complete

## What Was Built

J-18 — every screen run (reused, cancelled, failed, or freshly computed) now leaves a durable,
honest run record, and a duplicate Run Screen click on unchanged inputs short-circuits to the
already-recorded answer instead of paying for a full ~101-symbol member walk.

- **New module `app/research/desk_screen_log.py`** — mirrors `desk_topup_log.py`/
  `desk_index_reconcile.py`'s discipline byte-for-byte: checksum-verified append-only run-record
  files (one JSON file per run), a `ScreenRunStore` class (`list()` -> `(records, errors)`,
  `record()` the only mutation, no update/delete path, no content-based dedup -- every terminal run
  is its own genuinely distinct event), the single shared writer `record_screen_run(...)`, and
  `resolve_desk_screen_log_dir(desk_universe_dir_resolved)` -- a bare
  `TAPEOLOGY_DESK_SCREEN_LOG_DIR` env-var override, else a sibling of the universe dir
  (`.data/screen_runs`). **No new `Config` field.**
- **Five-pin pre-check + reuse short-circuit + run-log wiring, all inside `run_screen_and_record`**
  (`desk_screen_compute.py`, the ONE shared entry point both `DeskScreenComputeManager`'s resolve
  path and the CLI's `main()` already call):
  - Resolves the run's five pins BEFORE any walk, using ONLY existing accessors:
    `desk_screen.screen_as_of`, `UniverseStore.list()`'s latest record id,
    `Config.config_fingerprint()`, `desk_screen.compute_bar_store_signature` over
    `desk_coverage` -- zero new pin derivation.
  - A `ScreenStore.find_by_key` hit on those five pins short-circuits IMMEDIATELY: the existing
    snapshot is returned with `reused=True`, `members_attempted=0`, and **zero**
    `compute_screen`/`compute_tradability` calls (live-verified below and asserted by a
    call-counting test, TC-3).
  - A miss runs the full walk exactly as before -- zero behavior change to `compute_screen` itself.
  - At the run's terminal outcome (done/cancelled/failed), `record_screen_run` is called EXACTLY
    ONCE with the five pins as resolved (each honestly `null` if the run failed before resolving
    it), started/finished UTC, terminal state, `reused`, `members_total`, `members_attempted`,
    `ranked_count`, `skipped_by_reason` ({`no_bars`, `no_basis`}), the resulting `screen_id` (or
    `null`), and -- on `failed` -- the exception detail verbatim plus the member the walk was on
    when it raised (`members[attempted]`, computed from the SAME `members` list the pin resolution
    already reads). `screen_run_store` is an OPTIONAL keyword-only parameter (default `None`) on
    both `run_screen_and_record` and `DeskScreenComputeManager.trigger` -- see "Design decision"
    below for why this differs from J-09/J-10's REQUIRED run-store parameter.
  - A process that ends before this call leaves NO record (structural, not policed) -- proven by
    TC-7.
- **New route `GET /research/desk/screen/runs`** in `desk_routes.py` -- mirrors
  `get_topup_runs`/`get_desk_index_reconcile_runs` exactly: honest-empty
  `{"runs": [], "latest": null, "integrity_errors": []}` at HTTP 200 before any run (never 404);
  `runs` = lightweight meta only (excludes `ranked_count`/`skipped_by_reason`/`error`/
  `failed_member`); `latest` = the full record; `integrity_errors` in the same key/shape its three
  sibling desk GETs already use.
- **CLI (`python -m app.research.desk_screen_compute --date ...`)** now constructs a
  `ScreenRunStore` and threads it through `run_screen_and_record` -- a run started from the CLI is
  durably logged exactly like one started from `/desk`'s Run Screen button.
- **Frontend** -- a new, read-only "Screen Runs" section on `/desk`, the fourth ledger section
  beside Screen History / Top-up Runs / Index Reconciliation, built as a fourth instance of the
  exact same table-plus-latest-detail component pattern. Each run's date + id, terminal state,
  members attempted-of-total, and what it produced (a screen id, the honest "reused `<id>` -- no
  walk was performed" note, or "nothing recorded" for a cancelled/failed run) render in the table;
  the latest run's own full detail adds elapsed time, ranked/skipped-by-reason counts, and (on
  `failed`) the raising member's name plus the verbatim error. No new ranked-table column, no
  change to the ranked table, no new control -- copy is descriptive measurement only.
- **Zero MCP tool added** -- `get_endpoint`'s existing `/research/` allowlist already reaches
  `/research/desk/screen/runs`; the suite still proves exactly 17 tools (a new reachability test
  added, mirroring the J-09/J-10 precedent).
- **Zero new `Config` field**; `Config().config_fingerprint()` still prints `08e471b10130e1e2`
  (verified below).
- **Zero diff** to `desk_screen.py`'s recorded snapshot/row/skip shapes, rank order, or five-pin
  key, and zero diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`desk_coverage.py`/
  `desk_topup_log.py`/`StructureChart.tsx`.

## Design Decision (disclosed per plan instructions)

J-09/J-10's `topup_run_store`/`reconcile_run_store` parameters on their own compute managers'
`trigger()` are REQUIRED (no default). The plan explicitly forbids editing the three named
pre-existing tests in `test_desk_screen_compute.py`
(`test_second_run_with_identical_pins_reuses_the_existing_snapshot_no_second_file`,
`test_cli_second_invocation_with_identical_pins_reuses_the_existing_snapshot`,
`test_a_corrupted_snapshot_at_the_same_key_resolves_state_failed_never_a_silent_overwrite`), all
three of which -- along with essentially every other pre-existing test in that file -- call
`run_screen_and_record`/`DeskScreenComputeManager.trigger()` positionally with NO run-store
argument. Making `screen_run_store` required would have forced editing every one of those call
sites, including the three protected ones. Instead, `screen_run_store` is OPTIONAL and
keyword-only (default `None`) on both `run_screen_and_record` and `trigger()`: when omitted, the
run-log write is a no-op, so every existing test keeps passing completely unmodified (verified:
full suite green, the three named tests pass with zero edits to their bodies or assertions). The
real HTTP route (`desk_routes.py`) and the CLI (`desk_screen_compute.py`'s `main()`) both always
supply a real `ScreenRunStore`, so every REAL run (button, CLI, or POST) is durably logged; only
test call sites that never asked for the log get to skip it. This is a design choice made to honor
the "do not edit the three named tests" instruction, not a test-assertion conflict -- no assertion
in any of the three tests was touched.

## Files Changed

- `apps/backend/app/research/desk_screen_log.py` -- NEW: `ScreenRunStore`, `record_screen_run`,
  `resolve_desk_screen_log_dir`, `ScreenRunIntegrityError`.
- `apps/backend/app/research/desk_screen_compute.py` -- five-pin pre-check + reuse short-circuit +
  terminal-state `record_screen_run` call inside `run_screen_and_record`; `screen_run_store`
  threaded through `DeskScreenComputeManager.trigger()` (optional kwarg) and the CLI's `main()`.
- `apps/backend/app/research/desk_routes.py` -- new `get_screen_run_store` dependency,
  `screen_run_store` wired into `trigger_desk_screen_compute`, new `GET /research/desk/screen/runs`
  route + `_screen_run_meta_only` projection.
- `apps/backend/tests/test_desk_screen_log.py` -- NEW: 17 store/writer unit tests.
- `apps/backend/tests/test_desk_screen_compute.py` -- 7 new tests (TC-1, TC-2/TC-4 combined, TC-3,
  TC-5, TC-6, TC-7, TC-8); zero edits to any pre-existing test, including the three named ones.
- `apps/backend/tests/test_mcp_server.py` -- 1 new reachability test proving
  `/research/desk/screen/runs` is reachable via `get_endpoint` with no new tool and the 17-tool
  count unaffected.
- `apps/frontend/lib/types.ts` -- new `DeskScreenRunMeta`/`DeskScreenRun`/
  `DeskScreenSkippedByReason`/`DeskScreenRunsListResult` types.
- `apps/frontend/lib/api.ts` -- new `fetchDeskScreenRuns()`.
- `apps/frontend/app/desk/page.tsx` -- new "Screen Runs" section (`ScreenRunRow`/`ScreenRunsTable`/
  `LatestScreenRunDetail`/`ScreenRunsSection`), new `screenRunsResult` state + mount-time fetch, the
  screen-compute poll's terminal tick now also refreshes the screen-run log, and the section
  rendered as a fourth `<section>` after Index Reconciliation.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: full suite green, exit 0 (1,533 collected in this run: ~1,525 passed / 8 skipped -- grew
from the iteration's own stated baseline of 1,474 passed / 8 skipped; zero regressions). Targeted
reruns of `test_desk_screen_log.py`, `test_desk_screen_compute.py`, `test_desk_screen.py`,
`test_mcp_server.py`, `test_copy_discipline.py`, `test_desk_ui_guards.py`,
`test_desk_hover_tooltip_guard.py` all green.

`Config().config_fingerprint()` verified via direct interpreter check: prints `08e471b10130e1e2`
(unchanged).

Frontend: `npx tsc --noEmit` over the whole project -- zero errors.

### Live, real (non-mocked) verification

Ran the new CLI + HTTP route against a scoped fixture dir (the full ~103-member fixture universe,
one seeded AAPL daily bar series -- never the ambient `.data/`):

```
first run:  103/103 members attempted, reused=false, screen_id=screen-2026-06-22-09cf660a4125
second run: 0/103 members attempted,   reused=true,  screen_id=screen-2026-06-22-09cf660a4125 (SAME id)
```

`GET /research/desk/screen/runs` against a live uvicorn instance served both records verbatim, with
the meta-only `runs` list correctly omitting `ranked_count`/`skipped_by_reason`/`error`/
`failed_member` and `latest` correctly including them.

### Service startup (pre-handoff checklist)

`bash scripts/dev.sh` was started and stopped TWICE in sequence (backend :8301, frontend :3301,
this project's deterministic per-project port offset). Both cycles started cleanly with no port
conflicts; `curl http://localhost:8301/research/desk/screen/runs` returned the honest-empty payload
against the REAL ambient store; `curl http://localhost:3301/desk` returned 200 and the SSR shell
contains the new "Screen Runs" panel title (the same pattern "Top-up Runs"/"Index Reconciliation"
already show -- the populated content itself is client-fetched after hydration, identical to its
two siblings). All spawned processes (uvicorn reloader + worker, `npm exec next dev` + its `sh`/
`node`/`next-server` children) were killed after each check; ports verified clear afterward.

### TC-15 (real `.data/` untouched)

Before this iteration's work, `apps/backend/.data/` held: 759 bar-series files, 1 universe record,
11 screen snapshots, 1 top-up run record, 2 index-reconcile run records, 18 dataset entries.
`.data/screen_runs` did not exist before this session and STILL does not exist after it (verified:
`ls .data/screen_runs` -> "No such file or directory") -- every test in this iteration used
`tmp_path`/env-var-scoped stores exclusively, and the one live verification above ran against a
separate scratch directory, never the ambient `.data/`. The new capability's storage directory will
only ever appear once an operator runs a real screen compute (button, CLI, or POST) against the
real store, per the journey's own design.

## Known Issues

- **`bar_store_signature` in the run-log record.** Per the Data Contract, this field is honestly
  `null` only when the run failed before it could be resolved. In practice, resolving it requires
  only an index-only `desk_coverage` read (no walk), so it resolves successfully in every scenario
  this iteration's tests exercise except the deliberately-simulated "process died before the writer
  call" case (TC-7), where by construction there is no record at all.
- **Elapsed-time display precision.** `formatScreenRunElapsed` in `page.tsx` renders whole seconds/
  minutes only (mirrors `/structure`'s own `formatComputeElapsed` precision) -- a sub-second run (as
  every fixture-scoped run in this iteration's own tests is) renders as "0s". This is a display
  rounding choice, not a data-loss issue: `started_utc`/`finished_utc` are both recorded with
  microsecond precision in the underlying record.
- **Browser verification (TC-10/TC-11/TC-12/TC-13) not performed by this agent.** Per the developer
  agent's scope, browser-driven acceptance (screenshots at 1440x900, the demo-narrator walkthrough)
  is the browser-qa-agent's/demo-narrator's responsibility. This handoff's own live checks (CLI +
  HTTP route + a curl-level SSR sanity check of `/desk`) confirm the backend contract and basic page
  availability; they are not a substitute for the browser acceptance this journey's DoD requires.
- **No genuine conflict with the three protected tests.** Unlike the J-17 precedent
  (`test_desk_topup_compute.py:1092`), no assertion in
  `test_second_run_with_identical_pins_reuses_the_existing_snapshot_no_second_file`,
  `test_cli_second_invocation_with_identical_pins_reuses_the_existing_snapshot`, or
  `test_a_corrupted_snapshot_at_the_same_key_resolves_state_failed_never_a_silent_overwrite` needed
  to change -- all three pass with the new pre-check/reuse-short-circuit logic exactly as written,
  because the reuse short-circuit's observable behavior (same `screen_id`, `reused: true`, no second
  file) is unchanged from what the OLD post-hoc `ScreenAlreadyRecorded` catch already produced; only
  the internal mechanism (a pre-check instead of a post-hoc catch) differs. See "Design Decision"
  above for the one deliberate, disclosed departure from the J-09/J-10 precedent (an optional rather
  than required `screen_run_store` parameter).
