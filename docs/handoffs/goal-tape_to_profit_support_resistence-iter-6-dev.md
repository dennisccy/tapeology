# goal-tape_to_profit_support_resistence-iter-6 Dev Handoff

**Phase:** goal-tape_to_profit_support_resistence-iter-6
**Date:** 2026-07-06
**Agent:** developer
**Status:** complete

## IMPORTANT — Note on exact CLI usage and field naming (for QA/reviewer alignment)

`reports/qa/goal-tape_to_profit_support_resistence-iter-6-test-plan.md` was written before this
implementation existed and speculates a CLI invocation and JSON shape that differ from what was
actually built. The choices below were made because the phase spec/plan explicitly said to
**reuse the existing sweep's machinery verbatim** (`_dataset_rows` / `_split_summary` /
`_is_positive` / `_promote`) — inventing new field names or a new report shape for the strategy
axis would have violated that instruction. Please re-read the test plan against this section
before running it literally.

1. **Invocation is `python -m app.research.pnl_scan`, not a bare script path.** The module uses
   package-relative imports (`from ..config import ...`), exactly like every other module under
   `app/research/` — it has NEVER been runnable as `python apps/backend/app/research/pnl_scan.py`
   (that predates this iteration; running it that way raises `ImportError: attempted relative
   import with no known parent package` regardless of this change). The correct command (matching
   the module's own long-standing docstring):
   ```
   cd apps/backend && .venv/bin/python -m app.research.pnl_scan --strategy structure_tape --out /tmp/report.json
   ```
2. **There is no `--splits train` / `--splits hold_out` flag** (the test plan's TC-01/TC-02/TC-09
   assume one) — none was asked for by the phase spec, and adding one would have been scope creep.
   A single invocation ALWAYS reports both splits together (per-split, never pooled) — this is the
   SAME "one report, two split sections" shape the profile axis has always used, carried forward
   verbatim, per the iter-5 lesson recorded in this iteration's own plan ("the DoD's 'per
   train/hold-out split' is satisfied by dataset provenance... NOT a second split axis inside a
   single report — don't over-build a two-axis breakdown"). Passing `--splits` would be an
   `argparse` "unrecognized arguments" error, not a functional defect.
3. **The split key is `"holdout"` (no underscore)**, matching the existing `SPLIT_HOLDOUT`
   constant (`app/research/datasets.py`) — not `"hold_out"`.
4. **Per-dataset row field names reuse the EXISTING shape verbatim** (`_dataset_rows` /
   `_split_summary`, unchanged), not the test plan's speculated
   `strategy_tape_R`/`v1_R`/`delta_R`/`dataset` names. A real report's shape (confirmed via a live
   CLI run against the committed fixtures, not merely inferred):
   ```
   report = {
     "register": "...", "promotion_min_sample_size": 5,
     "champion_before": {"strategy_id": "v1", "profile": "default"},
     "champion_after": {...}, "promotion": null | {...},
     "provenance": {"assumptions": ["...B1 disclosure..."]},
     "candidates": [{
       "candidate_id": "structure_tape", "survivor": bool, "overfit": bool,
       "robustness": "robust" | "speculative",
       "train": {
         "aggregate": {"delta_net_r": ..., "delta_net_usd": ..., "candidate_n": ..., "champion_n": ...},
         "datasets": [{
           "dataset_id": ..., "dataset_checksum": ...,
           "champion": {"net_r": ..., "net_usd": ..., "n": ...},
           "candidate": {"net_r": ..., "net_usd": ..., "n": ...},
           "delta_net_r": ..., "delta_net_usd": ...
         }]
       },
       "holdout": { ...same shape as "train"... }
     }]
   }
   ```
   `"champion"` (not `"v1_*"`) is intentional: the champion's identity is data (read from
   `store.get_champion_pointer()`), never hardcoded to `v1` in the report shape, so the SAME shape
   stays correct if `v1` is ever displaced by a genuine promotion.
5. **The promoted enhancement id is `"structure_tape-over-v1-default"`** (test plan TC-06 example
   says `"structure_tape-over-v1"`, omitting the profile suffix) — this reuses the EXISTING
   `f"{candidate_id}-over-{champion['strategy_id']}-{champion['profile']}"` composition verbatim
   (unchanged from the profile axis), never a shortened id invented just for this axis.
6. **TC-03's expectation that a positive-but-below-min-n hold-out yields `overfit=false` does not
   match the EXISTING, REUSED-VERBATIM formula.** `overfit = train_positive and not survivor`, and
   `survivor` already folds in BOTH the sign check and the n-gate — there is no third state in the
   pre-existing (era-3, unmodified) formula that exempts "positive but insufficient n" from the
   `overfit` label. This is not a regression introduced by J-06: the PRE-EXISTING profile-axis test
   `test_min_n_gate_rejects_below_minimum_despite_positive_holdout` exercises the identical
   scenario shape and (correctly, deliberately) never asserts `overfit`'s value either, for exactly
   this reason. My new strategy-axis min-n tests follow the same deliberate omission. Changing this
   would mean modifying `_is_positive`/`overfit`'s formula, which the plan explicitly says to reuse
   verbatim — flagging for the auditor/evaluator to triage rather than silently reinterpreting it.

## What Was Built

- **A STRATEGY axis on the existing sweep** (`apps/backend/app/research/pnl_scan.py`,
  `run_sweep(..., candidate_strategy_id=None, bar_store=None)`) — an ADDITIVE branch beside the
  existing PROFILE axis, never a refactor of it:
  - CLI gains `--strategy STRATEGY_ID` (optional). Given, the sweep evaluates EXACTLY ONE
    candidate — backtest at `strategy_id=<given>`, `profile=default` — compared against the
    champion's CURRENT `strategy_id` (read verbatim from `store.get_champion_pointer()`, never
    hardcoded `"v1"`), also at `profile=default`.
  - Omitted (the default, `None`): the profile axis behaves **byte-identically** to before this
    iteration — proven by all 12 pre-existing `test_pnl_scan.py` tests passing completely
    unmodified.
- **`bar_store` (era-4 J-04's row-39 level source) threaded through every backtest call, on both
  axes** — `_run_backtest` now accepts and forwards it to `jobs.run_sync(...)`; `main()`
  unconditionally constructs `BarStore(config.bar_dir_resolved())` (the route's own precedent).
  `v1` ignores it entirely (byte-identical whether `None` or real), so this is a no-op for the
  profile axis; only a `structure_tape` backtest ever reads it, and honestly arms nothing without
  one.
- **`_promote` generalized** to accept explicit `new_strategy_id` / `new_profile` — the exact pair
  the winning candidate's own backtests ran at — instead of hardcoding the profile-axis assumption
  (`strategy_id=champion['strategy_id'], profile=candidate_id`). The profile axis's resulting
  pointer move is unchanged; a strategy-axis promotion moves the pointer to
  `{strategy_id: <candidate>, profile: "default"}`.
- **Audit item B1 disclosed, not re-armed**: every report (both axes) now carries a top-level
  `provenance.assumptions` list naming the `structure_tape` breakthrough arm's loose,
  sanctioned static-price-position anchor (a single at-event position test, not a fresh
  event-to-event level cross). A static, config-independent string (`BREAKTHROUGH_ANCHOR_CAVEAT`
  module constant) — present on every report regardless of axis, so it never perturbs the
  byte-identical-rerun guarantee.
- **`tests/test_no_execution_path.py`** — one new test
  (`test_named_strategy_comparison_and_promotion_code_carries_no_execution_vocabulary`) naming the
  new axis code explicitly (the iter-5 precedent for
  `test_class_scaled_sizing_and_reward_target_code_carries_no_execution_vocabulary`).
- **9 new tests in `tests/test_pnl_scan.py`** covering: comparison shape + fixture honesty on the
  committed PG dataset+bar fixtures (structure_tape trades 0 on train, 1 on hold-out — below the
  promotion minimum, the iter-3 lesson proven empirically); determinism of the `--strategy` CLI
  path; a genuine hold-out survivor promoting correctly (pointer move + exactly one ledger row +
  frozen-foundation fingerprint check); the same mid-promotion crash-safety guarantee as the
  profile axis; the min-n gate both ways; overfit labelling (positive train, failing hold-out,
  never promoted); >1-dataset-per-split honest promotion skip; and an unknown-strategy-id explicit
  refusal. Every asserted delta sign was verified empirically via a scratch probe against the real
  code before being written into an assertion — never hand-derived.
- **README.md doc-parity**: the existing "Candidate validation sweep" bullet now describes the
  named-strategy comparison capability and honestly states today's finding on the committed sample
  data (too few hold-out trades to trust a result yet — no promotion). The iter-5 doc-parity rider
  (the class-scaled-risk bullet) was already present — confirmed via `git blame`/reading, not
  duplicated.

## Files Changed

- `apps/backend/app/research/pnl_scan.py` -- added the `--strategy` CLI option, the
  `candidate_strategy_id`/`bar_store` params on `run_sweep`, the strategy-axis branch, generalized
  `_promote`'s pointer-move params, and the B1 disclosure constant + `provenance` report field.
- `apps/backend/tests/test_pnl_scan.py` -- 9 new tests for the strategy axis (see What Was Built);
  zero existing tests modified.
- `apps/backend/tests/test_no_execution_path.py` -- 1 new test naming the strategy-axis code
  explicitly.
- `README.md` -- doc-parity: the "Candidate validation sweep" bullet updated.
- `runs/goal-tape_to_profit_support_resistence-iter-6/status.json` -- `current_step: dev_complete`.

No changes to `apps/backend/app/config.py`, `app/research/store.py`, `app/research/pnl_ledger.py`,
or `app/research/edge_report.py` (all "expected no changes" per the plan; confirmed via
`git status`/`git diff --stat`). No changes anywhere under `apps/frontend/` (confirmed via
`git status --porcelain apps/frontend` returning empty — Frontend Present: no, per the plan).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`

Result (after this iteration's changes): **1146 passed, 1 skipped, 0 failed.**
Baseline (immediately before touching any code this iteration, same command): 1136 passed, 1
skipped, 0 failed. The 1 skip is pre-existing and unrelated to this iteration. Delta: +10 tests
(9 in `test_pnl_scan.py`, 1 in `test_no_execution_path.py`), **zero regressions**.

Narrower confirms also run:
- `pytest tests/test_pnl_scan.py -v` -- 21 passed (12 pre-existing unmodified + 9 new).
- `pytest tests/test_no_execution_path.py -v` -- 6 passed (5 pre-existing + 1 new).
- `pytest tests/test_profile_equivalence.py -v` -- all green (engine/`default`/`v1` byte-identity
  untouched; `config_fingerprint() == "4d665603569b9dbf"` still pinned, verified again inside the
  new survivor test after a real strategy-axis promotion).

Live (non-mocked) verification, beyond pytest:
- Ran the real CLI end-to-end against the committed fixtures via env vars
  (`TAPEOLOGY_DATASET_DIR=tests/fixtures/datasets`, `TAPEOLOGY_BAR_DIR=tests/fixtures/bars`):
  `python -m app.research.pnl_scan --strategy structure_tape --out <path>` -- exit 0, output
  matched the pytest-asserted numbers exactly (train candidate n=0, hold-out candidate n=1,
  `survivor=false`, champion unmoved, `provenance.assumptions` present).
  Also ran the backward-compatible no-flag path live -- exit 0.
- Service startup (`scripts/dev.sh`): started cleanly, stopped, and restarted a second time with no
  port conflicts -- backend `:8301` (`/health`) and frontend `:3301` (`/`) both returned HTTP 200
  both times. No startup errors from this iteration's changes (expected: no route or frontend code
  was touched).

## Known Issues

- **TC-03/QA-plan `overfit` expectation mismatch** -- see the "Note on exact CLI usage and field
  naming" section above. Not a regression; the reused-verbatim `overfit` formula has no third state
  for "positive train, hold-out positive-but-below-min-n" -- it reads `overfit=true` in that case,
  identically on both axes, and pre-dates this iteration.
- **`structure_tape` trades ZERO times on the committed PG TRAIN window**, not merely "few" -- the
  2-timeframe PG bar fixture's zones never fall inside that window's price path. The HOLD-OUT
  window does reach one class-C zone (n=1, still below the promotion minimum of 5). Both splits
  honestly fail the gate; the train delta reads *positive* only because champion `v1` itself lost
  money on that exact window (the era-3 finding, `docs/goal.md`) while `structure_tape` traded
  nothing there -- a real, non-fabricated mechanical consequence of the (unmodified) `overfit`
  formula, asserted directly in the new fixture test rather than concealed.
- **The genuine-survivor / overfit / min-n synthetic tests never touch the committed PG fixture**
  (per the iter-3 lesson, explicit in this iteration's plan) -- they reuse the existing synthetic
  three-timeframe confluence fixture (`test_levels._confluence_fixture`, imported directly rather
  than duplicated) paired with the canned `SIM-BUYER` scenario at varying window lengths. Every
  asserted delta sign was verified empirically via a scratch probe first.
- **`edge_report.py` was not touched** -- explicitly optional per the plan and not required for the
  DoD; it still evaluates only the champion strategy, unchanged from before this iteration.
- **Pre-existing operational finding, unrelated to this iteration's code** (surfaced only because
  the mandatory pre-handoff service-startup check runs `scripts/dev.sh` twice): a plain
  `pkill -f "next dev"` / `pkill -f "uvicorn main:app"` does not reliably reap every child process
  -- `next dev`'s spawned `next-server` (node) process, and uvicorn `--reload`'s multiprocessing
  worker (whose command line is a bare `python -c "from multiprocessing.spawn import
  spawn_main..."`, containing no `"uvicorn"` substring at all), can outlive a parent-only kill and
  keep holding the port. Had to kill by explicit PID during this iteration's verification.
  `scripts/dev.sh` is untouched (out of scope) -- flagging for operator awareness only.
