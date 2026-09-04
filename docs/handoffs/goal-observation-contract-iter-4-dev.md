# goal-observation-contract-iter-4 Dev Handoff

**Phase:** goal-observation-contract-iter-4
**Date:** 2026-09-04
**Agent:** developer
**Status:** complete

## What Was Built

- New test module `apps/backend/tests/test_tape_observation_path_equivalence.py` (6 tests, 0
  failed) -- the J-04 ingestion-path-equivalence proof (Binding Execution Order step 4). **Zero
  files under `apps/backend/app/` touched** -- the proof consumes only already-existing public
  surfaces (`WatchManager.watch_with_provider` / `watch_with_async_provider`,
  `TapeEngine.add_observer`, `build_tape_observation`).
  - TC-1/TC-2 -- `test_pg_sip_fixture_replay_and_live_legs_share_observation_hash_at_every_tick`:
    feeds the committed PG SIP fixture (`tests/fixtures/alpaca/PG_20260609_170000_171000_sip.json`,
    3,229 trades + 11,012 quotes = 14,241 records) as an identical valid ordered event stream into
    two freshly constructed engines -- one via the paced-replay entry point
    (`WatchManager(CONFIG, pace=0.0)`, `watch_with_provider(..., speed=float("inf"))` over
    `HistoricalProvider`), one via the live entry point (`watch_with_async_provider(...)` over
    `LiveProvider` fed the SAME records merged into arrival order). Per-tick capture on both via
    `TapeEngine.add_observer`. At every one of the 14,241 captured ticks AND at the end: asserts
    `observation_hash` and the full `MACHINE_OBSERVATION_SEMANTIC_FIELDS` set are equal, while
    `source.source_mode` (`historical` vs `live`), `source.data_feed` (`sip` vs `iex`),
    `source.session_id` and `source.session_started_at_utc` all differ. Runs in ~7.4s.
  - TC-3 -- `test_seeded_sim_scenario_replay_and_live_legs_share_observation_hash_at_every_tick`:
    the SAME proof over a SECOND, independent "valid ordered event stream" -- 60 ticks (120 events)
    of the fixed-seed `SIM-BIDABS` / `bid_absorption` scenario, materialised as vendor-neutral
    `RawQuote`/`RawTrade` records (`epoch = CONFIG.sim_session_anchor_epoch +` the sim's own
    logical timestamp, preserving the sim's quote-before-trade-at-equal-epoch order) and fed
    through the identical two entry points.
  - TC-4 -- `test_counterexample_mutated_semantic_field_makes_the_comparator_raise`: mutates one
    leg's `tape_state` in a real, freshly built `TapeObservation`, recomputes `observation_hash`,
    and proves the shared comparator (`_assert_semantic_equivalence`, the SAME helper TC-1/TC-3
    use) raises `AssertionError` -- the comparator is not vacuously true.
  - TC-5 -- `test_module_docstring_states_the_constitution_5_non_claim_verbatim`: the module
    docstring states Constitution §5's IEX-vs-SIP non-claim verbatim (whitespace-normalized
    substring match, robust to the docstring's own line-wrapping).
  - TC-6 -- `test_field_partition_groups_are_unchanged_from_iteration_1` (+ its own
    `test_counterexample_field_partition_drift_is_detected`): diffs `observation_contract`'s four
    field-partition-group constants against a frozen literal copy of the already-committed
    iteration-1 values; the diff is empty, proving no field was moved into a wider partition to
    manufacture TC-1/TC-3's equivalence.
- Fixup 1 (reviewer's carried-forward MINOR, `apps/backend/tests/test_tape_observation_lifecycle_feed.py`):
  **removed** `test_seven_lifecycle_statuses_plus_watch_stopped_are_pairwise_distinguishable`,
  which asserted only `len({seven hand-written literals}) == 7` and never called `WatchManager`.
  The nine tests directly above it (lines 370-510) already exercise every one of the seven
  `lifecycle.stream_status` values (plus the in-process `watch_stopped` case) non-vacuously from
  real `WatchManager`/`TapeEngine` calls, so the coverage this test wanted to represent already
  existed without a second literal-only copy. One test removed, not rewritten -- the iteration
  spec explicitly names this as an acceptable resolution.
- Fixup 2 (coherence-auditor's non-blocking advisory, `apps/backend/tests/test_tape_observation_time.py`):
  extended `test_watch_manager_iso_helper_matches_observation_contract_byte_for_byte` into a
  three-way check that also calls `app.main._iso_utc` (converting each representative epoch via
  `datetime.fromtimestamp(epoch, timezone.utc)` first, since its signature takes a `datetime`
  rather than the other two's `epoch: float`) and asserts byte-identical output against the other
  two `_iso_utc` copies. Extended the sibling `test_counterexample_iso_round_trip_detects_a_hand_formatted_string`
  so a hand-formatted string fails all three comparisons, not just one.

## Files Changed

- `apps/backend/tests/test_tape_observation_path_equivalence.py` (new, 408 lines, 6 tests) -- the
  J-04 equivalence proof.
- `apps/backend/tests/test_tape_observation_lifecycle_feed.py` (+10/-7 lines) -- removed the
  vacuous summary test, replaced with an explanatory NOTE.
- `apps/backend/tests/test_tape_observation_time.py` (+19/-4 lines) -- three-way ISO cross-check
  (imports `app.main`; two existing test bodies extended, no test added or removed).

No change to `apps/backend/app/observation_contract.py`, `apps/backend/app/watch_manager.py`,
`apps/backend/app/main.py`, `apps/backend/app/config.py`, or any frontend file -- all out of scope
per the iteration spec and confirmed untouched by `git status`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **4036 passed, 8 skipped, 0 failed** (4044 collected; exit code 0) -- exactly iter-3's
baseline (4031 passed / 8 skipped, per its dev handoff) plus this iteration's 6 new tests minus the
1 removed vacuous test (net +5), 0 regressions. The venv's pytest (9.1.1) prints no final "N
passed" summary line, so this was tallied by counting `-q` progress characters directly from the
captured output (`.`=4036, `s`=8, `F`=0, `E`=0), per the iter-0 lessons entry, and cross-checked
against an independent `--collect-only -q` per-file-count sum (181 files, 4044 collected) -- the
two tallies agree exactly.

Also run individually before the full-suite pass:
- `tests/test_tape_observation_path_equivalence.py` -- 6 passed, 0 failed, in ~7.4s total (the
  PG-fixture leg-pair alone -- a full ~14.2K-event replay-and-live double-run -- takes ~7.4s,
  comfortably inside the goal's "waits of at least 30 s" allowance).
- `tests/test_tape_observation_time.py` -- 33 passed, 0 failed (unchanged count from iter-3; only
  two existing test bodies' assertions were extended, no test added or removed).
- `tests/test_tape_observation_lifecycle_feed.py` -- 29 passed, 0 failed (30 -> 29, exactly the one
  intended removal).
- `Config.config_fingerprint()` -- confirmed `08e471b10130e1e2` (unchanged from the pinned value).
- `cd apps/frontend && npx tsc --noEmit` -- 0 errors (exit code 0; no frontend file touched, as
  expected).

## Manual verification (live backend)

Started the backend via `scripts/start-backend.sh` (bound port 8301, this repo's deterministic
per-path port offset), confirmed `GET /health` returns `{"status":"ok"}`. Stopped it
(`pkill -f "uvicorn main:app"`), confirmed no process remained, started it again to verify no port
conflicts on a clean restart -- `GET /health` responded correctly again. Stopped and confirmed
clean afterward (no uvicorn process remains).

Since this iteration touches **zero** files under `apps/backend/app/`, no backend code path could
have regressed, so this startup/restart check is a pure sanity confirmation, not a functional
regression test. The DoD's actual regression smoke check --
`/`, `/structure`, `/desk` render unchanged and Watch -> Pause -> Resume -> Stop transitions the
status dot through `live` -> `paused` -> `live` -> `closed`, plus confirming
`/tape/SIM-BIDABS/observation` still 404s across two reloads -- is the downstream browser-qa-agent
step per the iteration spec's own TESTING REQUIREMENTS section, not run by this developer pass.

## Self-check (anti-goal spot scan)

Grepped the three touched files for the era's actionability/external-system tokens
(`READY`, `NO_TRADE`, `NO_VERDICT`, `trade_allowed`, `PENDING_CONDITION`, `Workstation`,
`Trendora`, `TenSteps`, `composite_policy`, `should_trade`, `entry_price`, `stop_loss`,
`position_size`). The only two matches are both pre-existing, expected, and untouched by this
iteration: `ACTIONABILITY_TOKENS` (the copy-discipline guard's OWN lexicon constant, in
`test_tape_observation_lifecycle_feed.py`) and one deliberately-injected `"trade_allowed=true"`
string inside that same file's existing counter-example fixture proving the guard's scan is
non-vacuous. The new `test_tape_observation_path_equivalence.py` file has zero matches. The formal
goal-mode diff-scan step (TC-12) is a downstream pipeline stage, not run by this developer pass.

## Definition of Done -- verification against the spec

- [x] `test_tape_observation_path_equivalence.py` passes with 0 failures on both the PG-fixture
  leg-pair and the seeded-sim-scenario leg-pair, `test_counterexample_*` present and passing.
- [x] At every captured tick (all 14,241 for the PG fixture; all 120 for the sim scenario) and at
  the end of each leg-pair, `observation_hash` and the full semantic field set are identical
  between the replay leg and the live leg, while `source.source_mode`, `source.data_feed` (PG
  pair) and session metadata differ between the legs.
- [x] No semantic divergence hidden by a widened metadata partition -- `field_partition_map()`'s
  four groups are unchanged from iteration 1 (verified against a frozen literal copy, TC-6).
- [x] The new module's docstring states the Constitution §5 IEX-vs-SIP non-claim verbatim.
- [x] `test_tape_observation_lifecycle_feed.py`'s vacuous summary test no longer asserts solely
  over a hand-written literal disconnected from `WatchManager` (removed).
- [x] `test_tape_observation_time.py`'s ISO cross-check is a three-way comparison including
  `main._iso_utc`, with its counter-example still failing a hand-formatted string against all
  three.
- [x] Full backend suite still green -- 4036 passed / 8 skipped / 0 failed, net of this
  iteration's +6/-1 test additions, 0 regressions. `Config.config_fingerprint()` unchanged
  (`08e471b10130e1e2`).
- [x] `cd apps/frontend && npx tsc --noEmit` reports 0 errors (unaffected -- no frontend file
  touched).
- [ ] Browser-qa confirms zero visible product change -- downstream browser-qa-agent step (see
  Manual verification above for the backend-layer sanity check this developer pass performed).
- [ ] Anti-goal violation scan-report CLEAN; coherence verdict stays `COHERENCE-PASS` -- both are
  downstream pipeline steps; this pass's own self-check spot scan (above) came back clean.
- [x] Dev handoff written at this path.

## Known Issues

None found in the implementation. On direct inspection the new module and both fixups match the
iteration spec's IN SCOPE list, OUT OF SCOPE exclusions, and Test-first contract (TC-1 through
TC-6, TC-9) exactly -- no gaps, no workarounds, no production file touched.

One expected, non-defect note carried over from the spec's own text: this iteration cannot move
J-04 to `passing` on its own -- J-04's Acceptance requires two reloads of the served JSON at
`/tape/SIM-BIDABS/observation`, and that route does not exist until iteration 5. The evaluator is
expected to record J-04 as still `failing` or move it to `partial` on the strength of this
iteration's passing `test_tape_observation_path_equivalence.py` module, per the same convention
already applied to J-01/J-02/J-03 in prior iterations -- this is correct, not a regression.
