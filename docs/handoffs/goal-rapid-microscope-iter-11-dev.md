# goal-rapid-microscope-iter-11 Dev Handoff

**Phase:** goal-rapid-microscope-iter-11
**Date:** 2026-08-19
**Agent:** developer
**Status:** complete

## What Was Built

Closes the r5 "opaque research pool" hole (`docs/rapid-validation-spec.md` §7.5 point 7): a
registered-but-unresolved vault universe's pool members now stay withheld **regardless of whether
anything ever explicitly sealed them** — the structural gap named in the phase spec's BACKGROUND
(a repo-wide grep found zero production call sites of `seal_shard`/`assign_shard`/`expose_shard`,
so a real recording finalized under a registered universe would previously have been fully
identifiable everywhere, since the old predicate only recognized an explicit ledger row).

- **`vault.py`** — one new shared predicate, `unresolved_pool_universe_by_dataset_id` (+ its
  `unresolved_pool_dataset_ids` key-set convenience form), plus a new `universe_ledger_for_dataset_dir`
  resolver mirroring `shard_ledger_for_dataset_dir`. The predicate is the UNION of (a) today's
  ledger-row check (`withheld_universe_by_dataset_id`, byte-unchanged) and (b) a NEW
  universe-RULE membership check (`expected_recording_pairs()` × `created_utc >= registered_at`)
  that applies **only** to a dataset the shard ledger has never recorded a row for at all — a
  `ledger_tracked_ids` guard found and fixed during TDD (an already-`exposed` shard has no row in
  test (a)'s result, so a naive "not already withheld" check let test (b) re-catch it forever;
  fixed by excluding any dataset the ledger has ANY row for, in ANY state, from test (b)).
- **`micro_snapshots.py`** — `withheld_dataset_ids_for_store`/`exclude_withheld` now route
  through the new predicate via one private choke point (`_unresolved_pool_ids`); a new
  `_pool_records`/`_et_session_date` helper converts store records into the
  `(dataset_id, symbol, session_date, created_utc)` tuples the predicate needs. Zero call-site
  changes in any of its 8 downstream consumers (scout.py, walkforward.py, micro_join.py ×2,
  edge_report.py, edge_report_cache.py ×2, pnl_scan.py, desk_screen.py, setups.py).
- **`micro_readiness.py`** — `build_readiness`'s per-shard loop switches to the new predicate;
  `sealed_tranche`'s field names/shape are unchanged, only which datasets populate it broadens.
  The withhold check still runs before `store.load_events` (TC-10).
- **`tick_recorder.py`** — the live `progress` body (`GET .../recorder/compute`, and the `POST`'s
  own immediate echo) is now aggregate-only at every point during a run: `chunks_total`,
  `chunks_done`, `chunks_fetched`, `chunks_reused`, `chunks_unchanged`, `chunks_failed`,
  `trades_total`, `quotes_total`, `percent_complete`, `elapsed_seconds`. No symbol, date, dataset
  id, or other per-chunk field ever appears. The manager's internal `outcomes` list is kept
  **only** as private in-process state (never served) so the pre-existing exception-fallback path
  in `_resolve_terminal` (a failure outside any single chunk, e.g. TR-19) still builds an accurate
  terminal run-log row unchanged; the served projection (`_progress_view`) is an explicit
  whitelist, never a spread, so that internal field can never leak by accident. `GET
  .../recorder/runs` (already aggregate-only) is untouched.
- **`micro_routes.py`** — `GET /recorder/compute`'s docstring updated to state the new
  aggregate-only contract; no code change (it already forwards `manager.snapshot()`'s `progress`
  verbatim, and that method now returns the aggregate shape automatically).
- **`routes.py`** (found during implementation, **not** in the plan's original file list — see
  "Beyond the plan" below) — `get_withheld_dataset_ids` (the dependency behind `GET
  /research/datasets`, `GET /research/datasets/{id}`, and `POST /research/backtests`) now
  delegates to `micro_snapshots.withheld_dataset_ids_for_store` instead of calling
  `vault.withheld_dataset_ids` directly.
- **Tests**: `test_vault.py` gains one comprehensive TC-8/TC-9 test — the r5 deterministic
  inference-trap rewrite, run against a fixture pool with mixed provenance (1 legitimately
  exposed, 1 ledger-tracked sealed, 2 untracked), with the operator compute acts (snapshot build,
  Scout run, edge report, PnL sweep) run first, then every registered route swept, proving no
  still-unexposed member's (symbol, date) identity is derivable — plus the TC-9 counter-test
  proving the pre-fix predicate *would* have isolated the sealed-but-untracked dataset uniquely.
  `test_micro_readiness.py` gains TC-1/TC-3/TC-4/TC-10 (predicate mechanics, the `created_utc`
  timing guard, the load-order guard). `test_tick_recorder.py` gains TC-6/TC-7 (aggregate-only
  progress mid-run and at terminal state; no bypass parameter/header exists) plus one existing
  assertion updated (`test_tc7_a_cancelled_run_finishes_its_in_flight_chunk_and_stops_before_the_next`
  asserted on `progress["outcomes"]`'s length, which no longer exists in the served shape — swapped
  for the equivalent `chunks_done` count, which was always numerically identical).

## Beyond the plan: a third call site the plan's file list missed

The plan/phase-spec's own "Files to Create/Modify" list named `vault.py`, `micro_snapshots.py`,
`micro_readiness.py`, `tick_recorder.py`, and `micro_routes.py` as the backend surface. Writing
the TC-8/TC-9 inference-trap test surfaced a real, load-bearing gap that list omitted:
`app/research/routes.py`'s `get_withheld_dataset_ids` — the dependency behind `GET
/research/datasets` itself — called `vault.withheld_dataset_ids` **directly**, bypassing
`micro_snapshots.py` entirely. Without fixing this, the single most public dataset-listing
surface in the product would still have fully exposed an untracked pool member, defeating the
iteration's own goal. The phase spec's own BACKGROUND section names this exact surface
("`GET /research/datasets`") as one of the two the fix must close, and TC-9's own test scenario is
built around it — so this was a decomposition oversight, not an ambiguity requiring an owner
ruling (T-1 doesn't apply: the *what* was already unambiguous in the phase spec's prose, only the
file list was incomplete). Fixed with the same one-line delegation pattern used everywhere else
(`micro_snapshots.withheld_dataset_ids_for_store(store)`), reusing the identical choke point — no
second predicate anywhere. A repo-wide grep after the fix (`grep -rn
"vault\.withheld_dataset_ids\|vault\.withheld_universe_by_dataset_id" app/`) finds zero remaining
direct callers outside `vault.py`'s own internals and this docstring's own description of the old
behavior.

## Files Changed

- `apps/backend/app/research/vault.py` -- new `universe_ledger_for_dataset_dir`,
  `unresolved_pool_universe_by_dataset_id`, `unresolved_pool_dataset_ids` (+ two small private
  helpers, `_latest_universes`/`_universe_pair_index`); module docstring extended.
- `apps/backend/app/research/micro_snapshots.py` -- `withheld_dataset_ids_for_store`/
  `exclude_withheld` route through the new predicate via a shared private helper; new
  `_et_session_date`/`_pool_records` helpers.
- `apps/backend/app/research/micro_readiness.py` -- `build_readiness`'s per-shard loop uses the
  new predicate; `window_start_utc` ET-conversion precomputed once per record and reused.
- `apps/backend/app/research/tick_recorder.py` -- `TickRecorderComputeManager`'s live progress
  is aggregate-only (`_progress_view`/`_elapsed_seconds`/`_outcome_type_counts` added;
  `_chunk_entry` gains optional `trade_count`/`quote_count`; `_publish` accumulates
  `trades_total`/`quotes_total`; `_copy_recorder_snapshot` rewritten as an explicit whitelist
  projection); `_run_log_entry` refactored to share `_outcome_type_counts` (byte-identical output).
- `apps/backend/app/research/micro_routes.py` -- `GET /recorder/compute` docstring updated;
  no logic change.
- `apps/backend/app/research/routes.py` -- `get_withheld_dataset_ids` delegates to
  `micro_snapshots.withheld_dataset_ids_for_store` (see "Beyond the plan" above).
- `apps/backend/tests/test_vault.py` -- new TC-8/TC-9 inference-trap test + a new
  `_record_pool_dataset` fixture helper.
- `apps/backend/tests/test_micro_readiness.py` -- new TC-1/TC-3/TC-4/TC-10 tests + `_pool_fixture`/
  `_plant_pool_dataset` fixture helpers.
- `apps/backend/tests/test_tick_recorder.py` -- new TC-6/TC-7 tests + one existing assertion
  updated (see above); module docstring's numbered list extended.

## Pre-Handoff Verification

- **Service startup**: `bash scripts/start-backend.sh` started uvicorn cleanly on its pinned port
  8301 ("Application startup complete", no import/route-registration errors) — confirming the new
  `from . import micro_snapshots` import in `routes.py` and every other change import cleanly in a
  real process, not just under pytest. Live-curled against the running server (the REAL `.data`
  store, zero registered vault universes):
  - `GET /research/desk/micro/recorder/compute` → `{"state":"idle","progress":{"chunks_total":0,
    "chunks_done":0,"chunks_fetched":0,"chunks_reused":0,"chunks_unchanged":0,"chunks_failed":0,
    "trades_total":0,"quotes_total":0,"percent_complete":0.0,"elapsed_seconds":0.0},
    "started_utc":null,"finished_utc":null,"error":null}` — exactly the 10 aggregate fields, no
    `outcomes`.
  - `GET /research/datasets` → the real 18-dataset corpus, starting with the PG fixtures, byte-
    identical to before this iteration (confirms `get_withheld_dataset_ids`'s new implementation
    is inert against the real store, live, not just in a test double).
  - Stopped by its own PID (no pattern-based kill, per the standing operator rule); confirmed zero
    leftover processes afterward.
  - Frontend was not started — zero `.tsx`/`.ts` files changed this iteration, so there is nothing
    new for it to exercise; the browser-QA lane (a later pipeline stage) covers the
    required-still-passing journeys against the real UI.
- **External integrations**: N/A — this iteration adds no new adapter, scraper, or external API
  call. `tick_recorder.py`'s existing Alpaca-backed recorder is unchanged in its vendor-facing
  behavior (only its progress-reporting SHAPE changed); no live vendor call was made or needed to
  verify that.
- **Native dependencies**: N/A — no new dependency was added.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **3192 collected / 3184 passed / 8 skipped / 0 failed / 0 errors** (exit code 0). This
terminal doesn't print pytest's usual "N passed in Ts" summary line (a pre-existing environment
quirk, also documented in the iter-10 dev handoff); the exact count above was derived
programmatically from the dot-progress output (`.`=pass, `s`=skip, `F`=fail, `E`=error — zero of
the latter two). This is EXACTLY the carried baseline (3,185 collected / 3,177 passed / 8 skipped)
plus this iteration's 7 new tests, all passing, with the skip count unchanged — zero regressions
anywhere in the suite, including the real-corpus tests, the referee guards, the MCP contract test,
and every one of `micro_snapshots.exclude_withheld`'s 8 downstream consumer files.

Targeted runs during development (all green before the full-suite run):
- `pytest tests/test_tick_recorder.py -q` -- 39 passed (37 existing + 2 new TC-6/TC-7).
- `pytest tests/test_micro_readiness.py tests/test_vault.py tests/test_micro_snapshots.py
  tests/test_scout.py tests/test_edge_report.py tests/test_pnl_scan.py tests/test_desk_screen.py
  tests/test_micro_join.py tests/test_edge_report_cache.py tests/test_setups.py
  tests/test_walkforward.py -q` -- all passed (every one of `micro_snapshots.exclude_withheld`'s
  8 downstream consumer files, plus the three directly-edited test files) -- confirms zero
  call-site changes were needed and nothing regressed.
- `pytest tests/test_vault.py -q -k tc8_tc9` -- 1 passed (after two real bugs found and fixed
  during TDD: the `ledger_tracked_ids` guard in `vault.py`, and the `routes.py` gap above).
- `pytest tests/test_micro_readiness.py -q -k "tc1_ or tc3_ or tc4_ or tc10_"` -- all passed.

Frozen-constraint spot checks (all confirmed against the working tree):
- `Config().config_fingerprint()` prints `08e471b10130e1e2` -- unchanged.
- `git diff --stat` for all six `referee_*.py` modules is empty -- byte-untouched. SHA-256 hashes
  recorded for the auditor's convenience:
  - `referee_adjudicate.py` `6dd807b5ab69af033686a395484b1b10515d0f453a79c0943e534a578259786c`
  - `referee_evidence.py` `482f38a11740bc839038290fc2a0e131f649a23f17265cbca0f2aa19fe07e1c5`
  - `referee_null.py` `34917e381e4169aa029f5d0e18228fde75e4d3db5acec516f937e3ef3b371603`
  - `referee_registry.py` `03840c863b1e1f382ad2588d3bb6d8dc0e36a70582c3cb7a716638dabef32d99`
  - `referee_routes.py` `0cc3a06f7b382c63d544886ec74a47f2414612fc77dd3dac444b00cc35216140`
  - `referee_stats.py` `fba8816a5d4901ea1eeb7faa71e350538f546a2a3af1f9edb5f6f5aa1ec5271c`
- `git diff --stat -- app/mcp/` is empty -- MCP surface untouched, `EXPECTED_TOOLS` untouched
  (still the 22-tuple at `test_mcp_server.py:60`).
- `git diff --stat` shows zero `.tsx`/`.ts` files touched, zero `app/config.py` touch (no new
  `Config` field), zero `docs/rapid-validation-spec.md`/`docs/goal.md` edits by this agent (those
  were already modified by the decomposer/pump before dispatch, per the carried context).
- **TC-5 (real-store inertness).** No file/command in this session ever wrote to
  `apps/backend/.data/` -- every test uses a `tmp_path`-scoped store, and the only reads of the
  real corpus are the pre-existing `real_readiness`/`real_dataset_records` fixtures in
  `test_micro_readiness.py` (`DatasetStore.list()`, read-only, checksum-verified). Independent
  corroboration: `find apps/backend/.data -type d` lists no `micro_vault` directory at all --
  since `HashChainedLedger.append_row` is the only code path that ever creates one (a lazy
  `mkdir` on first write), its total absence proves no vault operation (`register_universe`/
  `seal_shard`/etc.) has EVER run against the real store, confirming the "zero registered vault
  universes today" premise directly rather than assuming it. Post-implementation reference hash
  (`find .data -type f -exec sha256sum {} \; | sort | sha256sum`, for the auditor to re-run and
  diff against a fresh capture if desired): `9fab9194cb1ec63c3d961a46c755a244fc32c459e1bb4d7a18f08972123ef1c5`.

## Known Issues

- **`_PRICE_ARITHMETIC_FIELDS` (`test_desk_ui_guards.py`) was deliberately NOT extended.** The
  new `progress.chunks_fetched`/`trades_total`/`quotes_total`/`percent_complete`/`elapsed_seconds`
  fields are backend-only this iteration (confirmed: zero `.tsx` files reference `progress.*` at
  all) -- that guard exists to catch client-side arithmetic on fields a `.tsx` file actually
  binds, and there is nothing to bind yet. J-08 (a future iteration) will need to add these when
  it builds the actual Recorder-progress UI panel.
- **A minor, deliberate inefficiency**: `unresolved_pool_universe_by_dataset_id` scans the shard
  ledger twice per call (once inside `withheld_universe_by_dataset_id`, once for the new
  `ledger_tracked_ids` guard) rather than one shared scan. Left as is -- the shard ledger is tiny
  today (no real recording has ever run against the operator's store), and computing `result` via
  a hand-inlined copy of `withheld_universe_by_dataset_id`'s own filter to share one scan would
  itself be the "second, divergent implementation" the DEFINITION OF DONE explicitly forbids.
  Worth revisiting only if the shard ledger ever grows large enough for this to matter.
- **The exploratory-track exposure mechanism remains a genuine open design gap** (unchanged from
  the phase spec's own NOTES -- not addressed this iteration, not this iteration's job). A
  registered-but-unresolved pool member simply stays withheld indefinitely today, which is
  conservative and safe, but no section of the spec yet says how a non-sealed member is ever
  deliberately released to exploratory use.
- **Wiring `tick_recorder.py` to call `vault.seal_shard` at record time** remains unbuilt, exactly
  as the phase spec's OUT OF SCOPE list requires. This iteration's fix is safe without it (the
  universe-rule predicate is safe the instant `register_universe` runs), but it means a real
  recording today still produces zero vault ledger rows -- every real future pool member will be
  in the "untracked" case my TC-8/TC-9 test specifically covers, not the "sealed" case.
- No `desk_micro_readiness`/`desk_scout`/`desk_walkforward`/`desk_vault` MCP tool was added (J-08's
  scope, correctly deferred); MCP surface stays at 22 tools.
