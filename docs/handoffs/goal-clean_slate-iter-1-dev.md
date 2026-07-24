# goal-clean_slate-iter-1 Dev Handoff

**Phase:** goal-clean_slate-iter-1 (J-01: "Backend demolition with byte-identical relocations")
**Date:** 2026-07-24
**Agent:** developer
**Status:** complete

## What Was Built

Nothing new — this is a demolition iteration. J-01 relocated two shared code families out of
soon-deleted modules, then deleted the 14 journal-era backend routes, the 11 journal-era modules,
`JournalStore`'s journal-era methods/dataclasses, and ~25 journal-era test files, while keeping
every other backend route byte-identical (verified by sha256 capture-and-diff, not just by test
pass/fail).

- **Relocated `r_basis`** from `marks.py` into `backtests.py` as a private helper (byte-identical
  math).
- **Relocated the dataset-source vocabulary** (`SOURCE_REFERENCE`, `SOURCE_HISTORICAL`,
  `REFERENCE_SOURCE_ID`, `_load_reference_window`) from `studies.py` into `datasets.py`
  (byte-identical).
- **Relocated the state-native arming family** (`STATUS_QUEUED/RUNNING/DONE/CANCELLED/FAILED`,
  `TERMINAL_STATUSES`, `_PROGRESS_EVERY`, `_PathPoint`, `_control_state`, `_premise_state`,
  `_synthetic_invalidation`, plus `_absorption_state` — a gap this plan's own gap-note missed, see
  Known Issues) from `studies.py` into `backtests.py` — the plan-flagged relocation, completed.
- **Relocated `get_study_market_adapter`/`_build_historical_fetch`** within `routes.py` itself, from
  beside the deleted `POST /research/studies` route to beside the kept `record_dataset` route — a
  second undocumented consumer this plan's own inventory missed (see Known Issues).
- **Deleted** 14 route handlers (`GET /research/analytics`, `/thesis/active`, `/hints/active`,
  `/hints`, `/journal`, `/journal/{id}`; `POST /thesis`, `/thesis/{id}/resolve`,
  `/thesis/{id}/action`, `/thesis/{id}/review`, `/studies`; `GET /studies`, `/studies/{id}`; `POST
  /studies/{id}/cancel`) plus their dead helpers `build_journal_detail`/`get_study_market_adapter`
  (the latter relocated, not deleted — see above).
- **SLIMMED `GET /research/taxonomy`** to just the `feed_basis` block (feeds + live disclosure) —
  every other label family (verdict/thesis-status/monitor-status/management-stance/checklist/
  chart-geometry/risk-flag/mistake-tag/grade/excursion/analytics/replay-study/hint/sound-cue/
  thesis-setup-catalog) removed. `taxonomy_payload()` no longer takes a `config` argument (nothing
  left uses it).
- **Slimmed `ResearchRegistry`**: lost `study_jobs`, `on_engine_created`, `startup_sweep`; kept
  `store`, `backtest_jobs`, `edge_report_compute`, `config`, `monitor_for`, `projection_for`,
  `hint_projection_for` — the last three are now permanent `None`-returning stubs (see Known Issues
  for why they could not simply be deleted this iteration).
- **Deleted 11 modules**: `journal_rows.py`, `monitor.py`, `hints.py`, `stance.py`, `verdict.py`,
  `grades.py`, `marks.py`, `excursions.py`, `execution_checks.py`, `analytics.py`, `studies.py`.
- **Deleted** `JournalStore`'s journal-era methods and the `ThesisRecord`/`ActionRecord`/
  `VerdictEventRecord` dataclasses (I-3's full DELETE list, plus `_encode_json_or_none` — see Known
  Issues). Migrations, schema version (v8), and every I-3 KEEP method are byte-untouched; the
  dormant tables (`theses`, `verdict_events`, `hints`, `actions`, `studies`, `study_occurrences`)
  still exist (verified by a kept test).
- **Deleted 25 journal-era test files** and updated 6 files beyond the two the plan explicitly named
  (`test_research_api.py`, `test_research_store.py`, `test_studies_reference.py`,
  `test_copy_discipline.py`, `conftest.py` — unchanged — plus 6 more files the plan's inventory
  missed: `test_backtests.py`, `test_observer_equivalence.py`, `test_setups_api.py`,
  `test_tradability_api.py`, `test_datasets_api.py`, `test_bars_api.py`, `test_levels_api.py`,
  `test_backtests_api.py` — see Known Issues for why each needed a forced, mechanical edit).
- **Removed `app/main.py`'s lifespan wiring** (`manager.set_on_engine_created(registry.
  on_engine_created)`, `registry.startup_sweep()`, the shutdown unset, and the now-orphaned
  `reg.study_jobs.join_all(...)` shutdown call). The WS `thesis`/`hint` frame merge
  (`_thesis_projection`/`_hint_projection`) is explicitly untouched — that is J-02's job.
- **`config.py` and all 13 fingerprint pin assertion lines are byte-untouched** — verified by grep
  (all 13 occurrences of `4d665603569b9dbf` still present) and `git diff fa76460 --
  apps/backend/app/config.py` (empty). `config_fingerprint()` still prints `4d665603569b9dbf`.

## Files Changed

Backend, `git diff fa76460 HEAD -- apps/backend/`: 57 files changed, 388 insertions(+), 18597
deletions(-). `git diff apps/frontend/` is empty (confirmed backend-only, as required).

- `apps/backend/app/research/routes.py` -- deleted 14 routes + 2 dead helpers; relocated
  `get_study_market_adapter`/`_build_historical_fetch`; slimmed imports, `ResearchRegistry`, and
  `get_taxonomy()` (1225 fewer lines)
- `apps/backend/app/research/taxonomy.py` -- slimmed to `feed_basis` only (1204 fewer lines)
- `apps/backend/app/research/backtests.py` -- gained `r_basis` + the state-native arming family
  (private helpers); docstring updated to drop "reused from studies" framing
- `apps/backend/app/research/datasets.py` -- gained `SOURCE_REFERENCE`/`SOURCE_HISTORICAL`/
  `REFERENCE_SOURCE_ID`/`_load_reference_window`; a few stale "studies" comment references fixed
- `apps/backend/app/research/pnl_baseline.py` -- import redirected from `.studies` to `.datasets`
- `apps/backend/app/research/edge_report.py` -- one comment updated (the `_aggregate` private-import
  precedent citation)
- `apps/backend/app/research/setups.py` -- one disambiguation comment updated (the tape-arming
  vocabulary now lives in `backtests.py`, not the deleted `studies.py`)
- `apps/backend/app/research/store.py` -- deleted journal-era methods + `ThesisRecord`/
  `ActionRecord`/`VerdictEventRecord` (+ `_encode_json_or_none`, verified zero kept callers);
  migrations/schema/KEEP methods byte-unchanged (1105 fewer lines)
- `apps/backend/app/main.py` -- lifespan wiring removal only (WS merge untouched)
- **Deleted:** `journal_rows.py`, `monitor.py`, `hints.py`, `stance.py`, `verdict.py`, `grades.py`,
  `marks.py`, `excursions.py`, `execution_checks.py`, `analytics.py`, `studies.py`
- **Deleted 25 test files:** `test_analytics.py`, `test_analytics_api.py`, `test_excursions.py`,
  `test_execution_checks.py`, `test_grades.py`, `test_journal_list.py`, `test_journal_migration.py`,
  `test_research_action.py`, `test_research_checklist.py`,
  `test_research_excursions_integration.py`, `test_research_execution_checks_api.py`,
  `test_research_freshness_integration.py`, `test_research_geometry.py`, `test_research_hints.py`,
  `test_research_hints_api.py`, `test_research_lifecycle.py`, `test_research_marks.py`,
  `test_research_monitor.py`, `test_research_resolve.py`, `test_research_review.py`,
  `test_research_risk_flags.py`, `test_research_stance.py`, `test_studies.py`,
  `test_studies_api.py`, `test_verdict_engine.py`
- `apps/backend/tests/test_research_api.py` -- rewritten to just the feed-basis canary (+1 new test
  asserting the payload's only key is `feed_basis`); the elaborate watch-wiring fixture simplified
  to a plain temp-path-injected client (nothing left in this file watches a ticker)
- `apps/backend/tests/test_research_store.py` -- rewritten to the generic store-infrastructure tests
  only (WAL, schema presence incl. dormant tables, writer-queue serialization, closed-store
  refusal, persistence-scope guard); the two infra tests that wrote through a thesis method now
  write through the kept `insert_backtest` instead
- `apps/backend/tests/test_studies_reference.py` -- rewritten to just the reference-fixture-load
  test (re-pointed at `datasets._load_reference_window`); the 3 tests pinning the (demolished)
  study-runner's occurrence-arming/excursion numbers are dropped, not reworked (see Known Issues)
- `apps/backend/tests/test_copy_discipline.py` -- dropped the "(b) representative served copy" leg
  (every symbol it sampled is deleted); fixture simplified (no more `on_engine_created` wiring);
  rail-2 lint rules and the "(a) taxonomy payload" + "(c)→(b) frontend literals" legs untouched
- `apps/backend/tests/test_backtests.py` -- 2 import lines repointed (`r_basis`, `_PathPoint`, now
  both from `.backtests`); 1 source-introspection guard assertion updated to check for the local
  `def r_basis(` instead of the now-gone `from .marks import r_basis` string; 2 comment fixes
- `apps/backend/tests/test_observer_equivalence.py` -- the file's last 2 tests (which attached a
  real `ResearchMonitor`, now deleted) removed; the 5 test-double-based equivalence tests (the
  file's original, still-sufficient J-68 proof) untouched
- `apps/backend/tests/test_setups_api.py`, `test_tradability_api.py`, `test_datasets_api.py`,
  `test_bars_api.py`, `test_levels_api.py`, `test_backtests_api.py` -- each file's `ctx` fixture had
  its own copy of the `manager.set_on_engine_created(registry.on_engine_created)` wiring (and, for
  `test_backtests_api.py`, a `registry.study_jobs.join_all(...)` teardown call); removed from all 6
- `runs/goal-session-clean_slate/iter-1/kept-route-baseline.txt` +
  `kept-route-after.txt` (+ two `.taxonomy-body.json` siblings) -- the I-9 byte-comparison capture
  (28 routes each; 27 byte-identical, `research.taxonomy` the one sanctioned diff)

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1165 passed, 1 failed, 0 errors, 7 skipped** (1173 collected; iter-0's baseline was 1665
passed / 7 skipped — a reduction of exactly the deleted/trimmed test content, no new tests silently
added beyond the one `test_taxonomy_payload_is_exactly_feed_basis` addition noted above).

The **1 failure** is `test_mcp_server.py::test_static_live_tools_json_byte_identical_to_rest`,
asserting `rest.status_code == 200` for the `journal`/`analytics`/`studies`/`taxonomy`/
`ui_route_map` MCP tools' REST equivalents. It fails on `journal` -> `GET /research/journal` -> now
404. **This is expected, not a defect** — the phase spec's own Out-of-Scope section names this
exact scenario: *"The three soon-dead MCP tools transiently proxy to now-404 routes via
`get_endpoint`'s existing honest-404 contract this iteration — expected, not a defect."*
`test_mcp_server.py` is untouched (MCP contract update is explicitly J-03's job); I did not edit it
to force this test green, since doing so would require either reverting the I-1 route deletions or
touching a file outside this iteration's scope. Every other test in that file (28 of 29) passes
unmodified.

Also verified directly (not just via pytest):
- All 14 deleted routes return exactly HTTP 404 (curled individually, correct verb each).
- `GET /research/taxonomy` returns the slimmed `{"feed_basis": {...}}` payload (304 bytes, was
  14021).
- I-9 byte-comparison: 27 of 28 captured KEPT routes are byte-identical sha256 before/after
  (`research.taxonomy` is the one sanctioned diff). Routes covered: `/meta/ui-routes`,
  `/research/{taxonomy, datasets×3, bars×5, candles×2, levels, tradability, setups×3, backtests×2,
  pnl/ledger, profiles, strategies, edge-report, edge-report/compute}`, `/tape/{state, features,
  events, summary, history}` (unwatched-ticker 404 shape).
- `config_fingerprint()` still prints `4d665603569b9dbf`; all 13 pinned assertion-literal
  occurrences still present (grep count matches exactly); `git diff fa76460 --
  apps/backend/app/config.py` is empty.
- T-12 grep for all 11 deleted module names, run against the **whole repo** (not just `apps/`,
  excluding `reports/**`/`runs/**`/`docs/goal-archive/**`): zero live hits.
- `scripts/start-backend.sh` starts cleanly on a fresh port and again after a stop (no port
  conflict); `GET /health` and `GET /research/taxonomy` respond correctly both times.

## Known Issues

**This section documents T-14 inventory corrections** — goal.md's own protocol for when in-era
reality contradicts its (very thorough, but not perfect) inventory: "STOP and surface it... the fix
is a documented inventory correction, never a silent improvisation." The plan (`runs/goal-clean_
slate-iter-1/plan.md`) had already flagged one such gap (the STATUS_*/`_PathPoint` family
studies.py→backtests.py relocation, missing from goal.md's own I-2 RELOCATE table). While
implementing that fix I found **four more**, all of the same shape (an unnamed second consumer, or
a forced mechanical test fix) and all resolved the same way the plan's own precedent recommends:
bounded, mechanical, documented — never a silent improvisation, never a bigger deletion than
planned.

1. **`get_study_market_adapter`/`_build_historical_fetch` (routes.py) had a second, undocumented
   caller.** goal.md's I-1 table lists `get_study_market_adapter` as a dead helper to delete
   alongside `create_study`. It is not dead: `record_dataset` (`POST /research/datasets`, an
   explicitly KEPT route) calls it too, for `SOURCE_HISTORICAL` recording — confirmed by the
   codebase's own docstring on the neighboring `get_bar_fetch_adapter`, which already documented
   "used by `create_study` SOURCE_HISTORICAL **and historical-dataset recording**". Fix: relocated
   both functions (byte-identical) from beside the deleted `create_study` to beside the kept
   `record_dataset`, with the two comments that named the now-deleted `create_study` updated for
   accuracy.

2. **`_premise_state`'s `absorption_reversal` branch needed `_absorption_state` too.** The plan's
   own STATUS_*/`_PathPoint` relocation list named `_control_state`/`_premise_state`/
   `_synthetic_invalidation` but not `_absorption_state` — a 3-line helper `_premise_state` calls
   internally. Confirmed live (not dead code) via `config.py`'s own `v1` strategy grammar, which
   registers `absorption_reversal` long/short as real entry setups. Missing this would have been a
   latent `NameError` triggered only when a real backtest run actually armed on that setup — never
   caught by a route smoke test. Relocated alongside the rest of the family.

3. **`main.py`'s shutdown block called `reg.study_jobs.join_all(...)` unconditionally.** Deleting
   `ResearchRegistry.study_jobs` (per I-2) without also removing this line would raise
   `AttributeError` on every backend shutdown — silently swallowed by the surrounding
   `contextlib.suppress(Exception)`, so it would never have failed a test, just silently skipped
   draining backtest-adjacent cleanup and left a dangling reference to the deleted `StudyJobManager`
   concept. Removed alongside the lifespan wiring.

4. **The WS `thesis`/`hint` merge (untouched, J-02's job) transitively needed store methods and a
   module this iteration deletes — the largest gap.** `app/main.py`'s `_thesis_projection`/
   `_hint_projection` (explicitly out of scope this iteration) call
   `registry.projection_for`/`.hint_projection_for` on every WS frame push. `hint_projection_for`
   degrades safely on its own (its `self._monitors` lookup is now permanently empty, since nothing
   populates it once `on_engine_created`'s wiring is cut — confirmed by grepping every
   `ResearchMonitor(` and `.add_observer(` call site in `app/`: exactly two, both in the two now-
   deleted call sites). But `_surviving_projection` — `projection_for`'s fallback — unconditionally
   called `JournalStore.get_active_thesis`/`has_entry_mark`/`get_actions`/`verdict_events` (all I-3
   DELETE-listed) and `monitor.build_projection` (monitor.py, wholesale deleted) — a live
   `AttributeError`/`ImportError` on **every WS frame for every watched ticker**, i.e. it would have
   broken the live cockpit tape stream entirely. Fix: `_surviving_projection` is now a documented
   stub returning `None` (its own already-established "normal state" per its docstring); it calls
   nothing. `hint_projection_for`/`projection_for`/`monitor_for` are kept on `ResearchRegistry` (NOT
   deleted this iteration, despite I-2 listing `hint_projection_for` for removal) because their
   still-live caller (the WS merge) is J-02's job, not this iteration's — deleting the method while
   its caller still exists would be the same class of bug as #3 above, just far more severe. I
   independently re-derived this exact fix and then cross-verified it against a dispatched research
   agent's independent trace of the same dependency chain from the opposite direction (main.py
   outward) — both arrived at the same root cause and the same three-part resolution (sever
   `on_engine_created`, delete `startup_sweep` with its caller, stub `_surviving_projection`). This
   is also what makes `hints.py`/`stance.py`/`verdict.py`/`grades.py`/`excursions.py`/
   `execution_checks.py` safely deletable exactly as I-2 specifies — none of them needed relocating,
   because nothing reaches them once the `ResearchMonitor` attachment path is severed.
   **J-02 should delete `hint_projection_for`/`projection_for`/`_surviving_projection`/`monitor_for`
   from `ResearchRegistry` in the SAME commit that removes the WS merge** — they will be genuinely
   dead at that point.

5. **`_encode_json_or_none` (store.py) — I-3's own text flagged this as conditional ("keep if any
   kept method uses it, else it may go with the pack") and it does not.** Grepped every call site
   (7 of them): all fall within `insert_thesis`, `insert_thesis_with_event`,
   `set_execution_checks`/`set_statement_final_statuses`/`set_grades`/`set_excursions`/`save_review`
   — all I-3 DELETE-listed methods. Deleted alongside them (not kept as I-3's own KEEP-method list
   literally enumerated it).

6. **Six more KEPT test files (not named in any I-8 row) had their own copy of the
   `on_engine_created` fixture wiring**, discovered via the first full-suite run after the route
   deletion (127 setup ERRORs, not failures — every test in these 6 files uses the SAME broken
   fixture): `test_setups_api.py`, `test_tradability_api.py`, `test_datasets_api.py`,
   `test_bars_api.py`, `test_levels_api.py`, `test_backtests_api.py` (the last also had a
   `registry.study_jobs.join_all(...)` teardown call, same as `main.py`'s #3 above). Each fixture
   copy had `manager.set_on_engine_created(registry.on_engine_created)` right after `set_registry`
   and the matching `manager.set_on_engine_created(None)` right before `set_registry(None)` — both
   lines removed, the generic ticker-stop teardown loop (unrelated to the hook) left untouched in
   each.

7. **`test_studies_reference.py`'s 3 `StudyJobManager`-dependent tests were dropped, not reworked,
   despite the plan's own note suggesting a rework.** The plan suggested "drive the reference/
   seeded-sim computation directly rather than through `StudyJobManager.create`/`run_sync`" — but
   the underlying computation (`StudyRunner`'s occurrence-arming + excursion-measurement +
   null-baseline aggregation) is not part of the STATUS_*/state-native-arming family relocated into
   `backtests.py`; it is `studies.py`-only logic serving no kept surface, confirmed via the same
   T-12 grep that cleared the rest of `studies.py` for deletion. Reworking these 3 tests would have
   meant reviving deleted computation just to keep pinned numbers green — the T-2 "never stub"
   spirit, applied to a computation rather than a module. The 4th test (the fixture-load path,
   which genuinely still guards `pnl_baseline.py`'s founding-baseline data path) is kept, re-pointed
   at `datasets._load_reference_window`.

**Config.py's two stale "studies.py" comment references were left untouched, on purpose.** Lines
~1238 and ~1343 reference the (now-relocated-to-backtests.py) tape-arming vocabulary as
"studies.py's own." Fixing them would touch `config.py`, which the plan explicitly reserves for
J-04 ("its config fields and schema-history comments are J-04's job... leave it alone"). Flagging
here so J-04 (or whoever next touches `config.py`) fixes the wording while already in the file.

**Nothing else known to be incomplete.** J-02 (frontend/WS), J-03 (MCP), J-04 (fingerprint epoch
bump) are unstarted, as scoped — `apps/frontend/` diff is empty, `app/mcp/__init__.py` is
byte-untouched, `config.py` is byte-untouched, all 13 fingerprint pins are byte-untouched.
