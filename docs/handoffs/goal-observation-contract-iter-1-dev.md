# goal-observation-contract-iter-1 Dev Handoff

**Phase:** goal-observation-contract-iter-1
**Date:** 2026-09-02
**Agent:** developer
**Status:** complete

## What Was Built

Binding Execution Order step 1 only (the constants, the pure builder, the two hash laws) --
lean, backend-only, zero served/UI surface, exactly per the iter spec's IN SCOPE list.

- `ENGINE_SEMANTICS_VERSION = "tape-engine-v1"` module constant added to
  `apps/backend/app/engine/tape_engine.py` (Constitution §6: bumped only by an owner act).
- New `apps/backend/app/observation_contract.py`, containing and only:
  - Schema constants `OBSERVATION_SCHEMA_VERSION = "tape-observation-v1"`, `PROVIDER = "tapeology"`.
  - The four-group field partition (`MACHINE_OBSERVATION_SEMANTIC_FIELDS`,
    `PROVENANCE_SOURCE_LIFECYCLE_METADATA_FIELDS`, `EXPLANATORY_METADATA_FIELDS`,
    `INTEGRITY_FIELDS`) enumerating all 45 Constitution §1 leaf paths exactly once, plus
    `field_partition_map()` for test iteration.
  - `canonical_encode(obj) -> bytes` using the repo's pinned encoding (matches
    `app/research/bars.py`'s idiom).
  - `compute_observation_hash` / `compute_artifact_hash` per the §6 hash laws.
  - `resolve_implementation_provenance()` -- process-memoized (module-level cache), returns
    `(engine_source_hash, source_revision, worktree_dirty)`. `engine_source_hash` is sha256 over
    the fixed, explicitly-ordered `ENGINE_SOURCE_MODULES` tuple (all 9 files under
    `app/engine/*.py`, verified equal to the sorted glob by a named test). `source_revision` /
    `worktree_dirty` come from two separate `git` subprocess calls (`rev-parse HEAD`;
    `status --porcelain --untracked-files=no -- apps/backend/app`, run with cwd at the repo
    root so the pathspec resolves correctly), each independently `None` on failure -- never
    invented. A `_reset_provenance_cache_for_tests()` test-only seam clears the memo.
  - `build_tape_observation(...)` -- the one pure builder. No clock read (every instant is
    either a verbatim caller input or `_iso_utc(epoch_anchor + timestamp)` for
    `observed_at_utc`), no git call, no import of `app.engine.classifier` or any
    feature-computation module. Computes the full v1 schema (including the pure-math
    `observed_at_utc` / `available_at_utc` / `availability_basis` projections) from
    already-resolved caller inputs; raises `ValueError` (the profile refusal) when
    `profile_id == "default"` but the caller's `config.config_fingerprint()` differs from the
    process `CONFIG` fingerprint.
- New `apps/backend/tests/test_tape_observation_projection.py` -- 38 tests, all named per the
  TC-1..TC-13 list in the iter spec, each guard/law test paired with a `test_counterexample_*`
  proving it can fail. Includes a doc-lint that parses `docs/observation-contract-spec.md`'s
  §4 field table and asserts it equals `field_partition_map()` with 0 differences, plus the
  `artifact_hash`-is-the-evidence-reference doc-lint assertion.

### Design decisions made without a stop-and-ask (documented for the reviewer)

1. **`source.scenario` is read from `snapshot.scenario`, not accepted as a second builder
   parameter.** The iter spec's prose lists "scenario" among the builder's "already-resolved
   inputs," but Constitution §1's binding field-owner table pins `source.scenario` to
   `EngineSnapshot.scenario`. Taking a separate `scenario` argument would risk a
   caller-supplied value diverging from the snapshot's own (a single-source-of-truth / Rail 6
   risk), so the builder reads it off the snapshot directly. No test needs a second parameter.
2. **`engine_identity.tape_state_vocabulary` is a literal duplicate tuple
   (`TAPE_STATE_VOCABULARY`) in `observation_contract.py`, not an import from
   `app.engine.classifier`.** The recompute guard (TC-2) explicitly forbids importing any name
   from `classifier.py`, but Constitution §1 requires this field to be "the classifier's closed
   state list." Resolved by hardcoding the five state-name strings (not logic, not a threshold)
   and adding `test_tape_state_vocabulary_matches_classifier_states`, which imports
   `classifier.py`'s own `STATE_*` constants from the TEST module (unrestricted) and asserts
   they match -- drift is caught by a test, never by the guarded module importing the
   classifier.
3. **`settled_at_utc` and `generated_at_utc` are accepted as already-formatted ISO strings**
   (verbatim pass-through), while `observed_at_utc` is computed inside the builder from the raw
   `epoch_anchor`/`timestamp` floats already on `EngineSnapshot`. This matches the iter spec's
   literal wording (these two are listed as accepted inputs, `observed_at_utc` is listed as
   something the builder "computes") and guarantees `available_at_utc == timing.settled_at_utc`
   on the live basis is a trivial verbatim-copy equality, not a re-formatting operation that
   could introduce drift.
4. **TC-9's "the underlying git subprocess was invoked at most once"** is implemented/tested as
   "zero additional `subprocess.run` calls across 4 repeated `resolve_implementation_provenance()`
   calls after the first resolution" -- proving memoization without asserting a specific total
   call count (the resolver legitimately issues two separate git commands per Constitution
   §7's two pinned, distinct commands).

## Files Changed

- `apps/backend/app/engine/tape_engine.py` -- added the `ENGINE_SEMANTICS_VERSION` module
  constant (8 lines; no other change).
- `apps/backend/app/observation_contract.py` -- new file (the builder module).
- `apps/backend/tests/test_tape_observation_projection.py` -- new file (38 tests).

No other file touched. `apps/backend/app/main.py`, `app/watch_manager.py`, and every frontend
file are unchanged (verified by `git status`).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_projection.py -v`
Result: 38 passed, 0 failed.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: 0 failed, exit code 0 (all dots, 8 `s` skip markers, matching the iter-0 baseline's skip
count). Tallied via `--collect-only -q` per-file counts (the venv's pytest 9.1.1 prints no final
"N passed" line, per the lessons-ledger note): total collected = 3976 = iter-0 baseline 3938
(3930 passed + 8 skipped) + 38 new tests in `test_tape_observation_projection.py`. So: **3968
passed / 8 skipped / 0 failed** -- no fewer than baseline, plus the new module, 0 failed.

Command: `cd apps/frontend && npx tsc --noEmit`
Result: 0 errors (unaffected -- no frontend file touched).

`Config.config_fingerprint()` verified unchanged: `08e471b10130e1e2`.

Manually verified the builder end-to-end (standalone script): built a `TapeObservation` dict
from a fixture `EngineSnapshot` + `resolve_implementation_provenance()`, confirmed
`schema_version`, `provider`, `config_fingerprint`, all top-level/nested keys, and both 64-hex
hashes are present and well-formed. `implementation_provenance.worktree_dirty` correctly read
`true` (honest -- there are genuinely uncommitted new files in this worktree right now).

### Pre-handoff verification (service startup)

Ran `scripts/dev.sh` (backend :8301 / frontend :3301): both started cleanly with no errors.
Confirmed `GET /openapi.json` -> 200, `GET /tape/SIM-BIDABS/observation` -> 404 (route not
built yet -- expected), frontend `/`, `/structure`, `/desk` -> 200. Stopped all processes
(verified via `ps`/`lsof` that ports 8301/3301 were fully released), then started `scripts/dev.sh`
again from clean -- identical clean startup on the same ports, no conflicts, same endpoint
checks passed. All backend/frontend processes killed before finishing (verified stopped).

No native-dependency or external-integration setup was introduced this iteration (pure
in-process Python + one local `git` subprocess call), so those two pre-handoff checklist items
are not applicable.

## Known Issues

- **J-01 remains not-fully-passing at the journey level** -- this is expected and called out
  explicitly in the iter spec's "Note on J-01's overall journey status": J-01's Acceptance
  requires the served JSON at `/tape/SIM-BIDABS/observation`, which needs the route (iteration
  5, Binding Execution Order step 5). `/tape/SIM-BIDABS/observation` still 404s, verified live
  against a running backend. The honest per-iteration signal is
  `test_tape_observation_projection.py` (38/38 passing) plus the full suite staying green.
- `docs/goal-session-observation-contract/state/blueprint.md` already carries an accurate
  "iter-1: builder module built in-process; not yet served" status note in its Data Contract
  table (rows for machine-observation-semantics and integrity) -- it appears to have been
  pre-written in anticipation of this iteration's scope and already matches what was actually
  built, so it was left untouched (out of my task scope; not a backend file).
- No new `git` dependency was introduced -- `subprocess`/`git` were already implicitly available
  in this environment (used by other repo tooling); `resolve_implementation_provenance()` fails
  closed (`None`/`None`) if `git` is ever unavailable, verified by a monkeypatched test case.
- The two-separate-git-subprocess-calls design (`rev-parse HEAD` + `status --porcelain`) is
  intentional per Constitution §7's two distinct, pinned command strings -- cannot be merged
  into a single git invocation without deviating from the binding exact command text.
