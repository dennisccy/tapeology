# goal-rapid-microscope-iter-32 Dev Handoff

**Phase:** goal-rapid-microscope-iter-32
**Date:** 2026-08-24
**Agent:** developer
**Status:** complete

## What Was Built

A QA-only fixture-seeding script plus its own pytest coverage -- **zero production code changed**
(no route, MCP tool, or `/desk` component touched; `micro_graduation.py`,
`micro_sealed_evaluation.py`, `micro_routes.py`, `vault.py`, `scout_ledger.py`, `walkforward.py`,
`datasets.py` are all byte-identical to iter-31). This is purely the evidence-generation
infrastructure J-11 needs for its two still-missing browser captures (empty-ledger + four-stage
fixture rig); the actual browser passes, the demo-narrator `[NEW]` walkthrough step, and J-07's
stored golden are later pipeline stages, out of this dev pass's scope.

- **`apps/backend/scripts/seed_micro_graduation_iter32_fourstage_fixture.py`** -- seeds FOUR
  families into one throwaway scoped root (`<root>/datasets`, sibling `micro_snapshots`/
  `micro_vault`/`micro_graduation`/`walkforward`/`scout` directories), each produced by calling
  the REAL, unmodified production functions (never a hand-set `passed`/`state` field):
  - **Family A -- `exploratory`.** Disclosed interpretation call: `list_graduation_families`
    only lists a family with >=1 graduation-ledger row of either kind, and `"exploratory"` is
    never itself an appendable `to_state`. Since `evaluate_sealed_verdict`/
    `record_sealed_evaluation` carry no `walkforward_survivor` precondition of their own (only
    `evaluate_sealed_survivor_transition` enforces state ordering -- confirmed by direct source
    read), Family A's sole ledger footprint is one REAL, `insufficient` sealed evaluation (29
    observations, one short of `SEALED_MIN_OBSERVATIONS`=30) via the real
    `evaluate_sealed_verdict` -- `evaluate_walkforward_survivor_transition` is NEVER called for
    this family, exactly as the iteration spec's own words scope it ("no walk-forward survivor
    transition attempted").
  - **Family B -- `walkforward_survivor`, carrying one PERMANENT FAILED sealed evaluation.**
    Three real, already-sufficient fold rows (`walkforward_ledger.append_fold_result`) advance it
    via the real `evaluate_walkforward_survivor_transition`; the real `evaluate_sealed_verdict`
    is then called with 30 real observations whose recomputed effect (mean 1.0, positive
    direction) is below the family's 5.0 bps econ floor -- a genuine `verdict="fail"`,
    `failure_reason="below_economic_floor"`. `evaluate_sealed_survivor_transition` is
    deliberately never called, so the state stays permanently `walkforward_survivor`.
  - **Family C -- `sealed_survivor`.** Same walk-forward setup (own corpus/sequence), a genuine
    PASSING sealed evaluation on its OWN distinct vault shard (different `dataset_id`/checksum
    from Family B), then the real `evaluate_sealed_survivor_transition`.
  - **Family D -- `referee_handoff_ready`.** Identical to Family C, then the real
    `evaluate_referee_handoff_ready_transition` (builds + validates the export bundle), whose
    `referee_registration_note` carries `REFEREE_FUTURE_REVISION_SENTENCE` verbatim -- the same
    string the frontend's `GRADUATION_REFEREE_HANDOFF_NOTE` constant already quotes byte-for-byte
    (iter-31).
  - **Idempotent-replay-safe.** `micro_graduation.py`'s own state-advancing functions already
    check-first (unchanged, reused as-is). `DatasetStore.record`/`vault.seal_shard`/
    `assign_shard`/`expose_shard` carry NO such branch of their own (each refuses outright on a
    second call against content/a shard already on record); the script supplies that discipline
    AT THE CALL SITE (`_plant_dataset_and_snapshot`'s `except DatasetAlreadyRegistered` reuse,
    `_idempotent_seal_assign_expose`'s three `except ShardLifecycleOrderError: pass` guards) --
    verified live: a second run against the same root appends zero new rows anywhere (graduation
    ledger stayed at 10 rows, walk-forward ledger stayed at 9 rows, chain still verifies).
  - Prints each family's `family_root_id` + resulting state/verdict to stderr with an explicit
    `MISMATCH`/`ok` tag per family, and a final `ERROR` line if any diverged; exits 0 only when
    all four land in their target state (and Family A's/B's own verdicts read
    `insufficient`/`fail`).
- **`apps/backend/tests/test_seed_micro_graduation_iter32_fourstage_fixture.py`** -- 8 new tests:
  all four target states land correctly; Family A's exploratory-via-insufficient-sealed-eval
  shape (zero transitions, one `insufficient` row); Family B's `fail` verdict is genuinely
  recomputed (`n=30`, `effect≈1.0`, `sign="positive"`, `failure_reason="below_economic_floor"`,
  state never advances past `walkforward_survivor`) -- read back from the ledger, not the
  script's stdout; Family C's shard is distinct from Family B's; Family D's bundle transition
  carries a `bundle_hash`; a second run against the same root appends no duplicate row (content-
  identical rows, chain still verifies) in BOTH the graduation ledger and the upstream
  walk-forward fold ledger; and a monkeypatch-driven error-path test confirming `main()` returns
  1 and prints `MISMATCH`/`ERROR` when a family's target diverges.

## Files Changed

- `apps/backend/scripts/seed_micro_graduation_iter32_fourstage_fixture.py` -- new QA-only fixture
  seed script (no production import site outside this script and its own test file).
- `apps/backend/tests/test_seed_micro_graduation_iter32_fourstage_fixture.py` -- new regression
  coverage for the seed script's own fixture shape and idempotency.

No other file was touched. `runs/goal-session-rapid-microscope/state/blueprint.md`'s iter-32 note
was already present (written by the decomposer) confirming "no Data Contract or Information
Architecture change... adds no module, no route, no MCP tool, and touches no line of
`micro_graduation.py`, `micro_sealed_evaluation.py`, `micro_routes.py`, or the `/desk` Graduation
section component" -- verified true by `git status --porcelain`, which shows only the two new
files above (plus this handoff and `runs/goal-rapid-microscope-iter-32/status.json`).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **3,504 passed, 8 skipped, 0 failed** (iter-31 baseline: 3,495 passed / 8 skipped -- net
+9: the 8 new tests in this iteration's own file, plus one pre-existing test the iter-31 handoff's
recorded baseline undercounted; either way this comfortably satisfies the DoD's "≥ 3,495 passed, 8
skipped, 0 failed" floor). No `F`/`E`/`x`/`X` marks anywhere in the run (verified by parsing the
raw dot-progress output directly, since this environment's pytest 9.1.1 install does not print its
usual final "N passed in Ys" summary line -- a local quirk, not a suite failure: `-rA` confirms
every collected test is individually listed `PASSED`, zero `FAILED`/`ERROR`).

The new test file alone: `.venv/bin/python -m pytest tests/test_seed_micro_graduation_iter32_fourstage_fixture.py -v`
-> 8 passed.

The seed script itself, run directly against a scratch root: exit 0, all four `[ok]` tags, verified
via a follow-up Python snippet that `GraduationLedger.verify_chain()` reads `{"ok": True, ...}`
and each family's served shape (`state`, `sealed_evaluations`, `transitions`) matches the target
exactly (Family A `exploratory`/`insufficient`/n=29; Family B `walkforward_survivor`/`fail`/n=30;
Family C `sealed_survivor`/`pass`/n=30; Family D `referee_handoff_ready`/`pass`/n=30, transitions
`[walkforward_survivor, sealed_survivor, referee_handoff_ready]` with `bundle_hash` present). A
second run against the identical root reproduced identical output and zero row growth (10
graduation rows, 9 walk-forward fold rows, both unchanged).

Frozen-foundation re-checks: `Config().config_fingerprint()` still prints `08e471b10130e1e2`;
`git status --porcelain` shows zero diff under any `referee_*.py` file.

## Pre-handoff verification

- **Service startup**: `scripts/dev.sh` started backend (`:8301`) and frontend (`:3301`) cleanly
  (`Application startup complete`, `Ready in 1251ms`). Live checks: `GET /health` -> 200,
  `GET /research/desk/micro/graduation` -> 200 (the default/unscoped ledger, untouched by this
  iteration), `GET /desk` -> 200. Both processes (and their child `next-server`/reloader
  processes) were killed afterward; `lsof -ti :8301 :3301` confirmed both ports free and `ps aux`
  confirmed no stray `uvicorn`/`next` processes remained.
- **External integrations**: N/A -- this iteration adds no adapter, scraper, or external API
  call. The seed script's own "REAL production functions" are all in-process/on-disk (dataset
  store, snapshot builder, vault ledger, walk-forward ledger, graduation ledger) -- no network
  call of any kind.
- **Native dependency binaries**: N/A -- no new dependency was added.

## Known Issues

- **Browser evidence (Capture 1 "empty", Capture 2 "four-stage") is NOT part of this dev pass.**
  Per the iter-32 spec's own scoping and the standard goal-mode pipeline division of labor, the
  actual backend restarts against `TAPEOLOGY_MICRO_GRADUATION_DIR` and the browser-qa-agent
  element-capture passes (TC-1..TC-4) are a later pipeline stage. This handoff hands that stage
  everything it needs: run the seed script once against a fresh scoped root (e.g.
  `apps/backend/.venv/bin/python scripts/seed_micro_graduation_iter32_fourstage_fixture.py
  apps/backend/.data/qa-fixtures/goal-rapid-microscope-iter32-fourstage`) to produce the
  four-family fixture, and point Capture 1 at ANY fresh, never-seeded root's `micro_graduation`
  subdirectory (e.g. `apps/backend/.data/qa-fixtures/goal-rapid-microscope-iter32-empty/
  graduation`, left un-seeded) for the empty-ledger render. In both cases only
  `TAPEOLOGY_MICRO_GRADUATION_DIR` needs to change on backend restart -- verified live above that
  the persistent rig's DEFAULT (unscoped) graduation directory is completely untouched by seeding
  into a scoped root, so J-07's existing golden is unaffected.
  - Concretely, for Capture 2 the env var should be
    `TAPEOLOGY_MICRO_GRADUATION_DIR=$(pwd)/apps/backend/.data/qa-fixtures/goal-rapid-microscope-iter32-fourstage/micro_graduation`
    (the sibling directory `resolve_micro_graduation_dir` computes under the root the script
    was invoked with).
- **The `[NEW]`-flagged demo-narrator walkthrough step and J-07's stored golden replay script**
  are likewise out of this dev pass's scope (spec's own Browser evidence / demo-narrator
  concerns) -- unaffected by anything in this handoff.
- **Family A's "exploratory" construction is a disclosed interpretation call**, not literally
  spelled out in the iteration spec's own bullet text (which only says "no walk-forward survivor
  transition attempted"). Given `list_graduation_families` structurally requires >=1 ledger row
  to appear in the served list at all, and "exploratory" is never an appendable `to_state`, the
  only code-legal way to make a family visibly `exploratory` is via a `sealed_evaluation` row
  with zero `state_transition` rows -- confirmed safe by direct source read of
  `evaluate_sealed_verdict`/`record_sealed_evaluation` (neither has a `walkforward_survivor`
  precondition of its own). If a reviewer/auditor judges this reading incorrect, the fix is
  narrow: swap Family A's `_insufficient_observations` sealed-eval call for a different real call
  that still lands it in the ledger without a `state_transition` row -- no other family is
  affected.
