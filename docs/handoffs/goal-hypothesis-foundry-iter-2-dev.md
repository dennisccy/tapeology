# goal-hypothesis-foundry-iter-2 Dev Handoff

**Phase:** goal-hypothesis-foundry-iter-2
**Date:** 2026-08-26
**Agent:** developer
**Status:** complete

## What Was Built

- **QA-rig visibility fix (J-01 step 5, TC-1/TC-2/TC-3).** `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh`
  now copies the real, already-recorded `apps/backend/.data/foundry/era_open_baseline.json` artifact
  (read-only source, never written to) into the scoped rig's own throwaway `$ROOT/foundry/` before
  backend start — the same "plain file copy of an already-recorded real artifact" pattern the script
  already used for the two PG tick-dataset fixtures. `foundry_source_registry.resolve_foundry_dir()`'s
  `TAPEOLOGY_FOUNDRY_DIR` override already existed from iter-1; the gap was purely that nothing wired the
  rig to see the real directory. Live-verified: launched the rig on a throwaway port, confirmed
  `GET /research/desk/micro/foundry` now serves the genuine recorded values (suite counts
  `passed=3787/skipped=8/failed=0`, `config_fingerprint`, all six Referee-module SHA-256 hashes) instead of
  `era_open_baseline: null`, and confirmed the real `.data/foundry/era_open_baseline.json` is byte-identical
  (md5sum) before and after the rig ran — the store-scope guard's own invariant, verified directly since
  `.data/` is gitignored (no `git status` diff to check).
- **`app/research/foundry_interpreter.py`** (J-03): the generic candidate interpreter. `resolve_population`
  implements spec §4.1 exactly — resolves every conditioning component via its own
  `ComponentResolution.resolved`/`available_at`/`corner_satisfied`; excludes+counts an anchor with any
  unresolved component from BOTH cells under a typed reason; computes
  `candidate_available_at`/`outcome_start` by calling the EXISTING timing helper
  (`micro_features.resolve_outcome_start`) directly, never a second hand-written `max()`; evaluates the
  frozen membership corner as a closed dispatch over `relation.kind`
  (`direct_scalar_membership`/`conjunction`) — never a parsed/`eval()`'d expression, since
  `threshold_corner_predicate` stays descriptive-text-only exactly like `foundry_compiler.py`'s own
  precedent. `project_boolean_membership` turns every eligible anchor into a Scout-canonical dict with
  `feature_value = 1.0/0.0` (raw coordinate values never reach the Scout boundary). `read_model` serves the
  §4.1 total/eligible/unavailable-by-reason/candidate/comparator/usable-sessions read model.
  `interpret_candidate` is the full pipeline, calling `scout.screen_candidate` DIRECTLY (never the
  registration/ledger path) with the fixed orchestration label `foundry_boolean_membership`
  (never a member of `scout.AGGRESSOR_DERIVED_FEATURES`) and transform `threshold` / predicate
  `feature_value >= 1.0`. An unsupported `relation.kind` (the ordered-lag form) raises
  `UnsupportedRelationBlocked` with `.disposition == "BLOCKED_UNSUPPORTED_RELATION"` — no guessed window.
- **`app/research/foundry_family.py`** (J-04): `build_family_registry` freezes each family's complete
  variant denominator; a family whose count exceeds `scout.SCOUT_MAX_VARIANTS_PER_FAMILY` (imported, never
  redefined) is `blocked=True` WHOLE, never a subset. `attempt_late_insertion` always refuses — there is no
  mutation API on the frozen `FoundryFamily` dataclass at all. `n_variants_tried_for` reads only the frozen
  `variant_count`, never an execution-progress counter.
- **`app/research/foundry_freeze.py`** (J-04): `generate_or_verify_manifest` — identical generation inputs
  replayed against an already-generated epoch slot verify/no-op; changed inputs raise
  `ManifestDriftRefused` (never a second `epoch_2`). `generate_freeze_set` — the deterministic enumerated
  path+sha256 manifest generator: starts from `FREEZE_SET_REQUIRED_MODULES` (the ten §8.4-named modules)
  and transitively walks each covered file's own same-directory (`level == 1`) relative imports via `ast`,
  raising `FreezeSetDependencyUnproven` the instant any required or discovered dependency is missing on
  disk. `build_freeze_record`/`FreezeRecord` pin every §8.4 hash. `verify_commit_is_ancestor` is a real
  `git merge-base --is-ancestor` wrapper (tested against this repo's own HEAD). `verify_freeze_set_unchanged`
  recomputes sha256 over ONLY the enumerated freeze-set paths and raises `FreezeIntegrityHalt` on any
  mismatch/missing file — it structurally cannot false-refuse on a Goal Mode session file or a
  non-scientific UI-only file, since neither was ever added to `entries`.
- **`app/research/foundry_ledger.py`** (J-04): `FoundryLedger`, built on the existing shared
  `micro_chain_ledger.HashChainedLedger` primitive (the same one `micro_accessor.ExposureRegistry`/
  `walkforward_ledger.WalkForwardLedger` already use — never a fourth hand-rolled hash chain).
  `record_intent`/`record_terminal` implement the §6/§9.2 intent-then-terminal lifecycle; an exact-duplicate
  terminal replay is idempotent (returns the existing row); a content-differing replay for the same
  `candidate_spec_hash` raises `ConflictingReplayRefused`. `deterministic_rule_id` implements
  `"foundry:" + epoch_id + ":" + candidate_spec_hash`. `prospective_root_status` records the candidate's
  own `foundry_family_id` for a one-coordinate `direct_scalar_membership` candidate (the one mechanically
  defined case this era can support without inventing a real Scout root mapping), else the literal
  `root_deferred_composite` sentinel — never a synthetic root. This module never imports `scout_ledger`, so
  no Foundry trial can ever land on the Scout ledger from here.
- **`app/research/foundry_runner.py`** (J-03/J-04 integration): `map_scout_decision` — the closed,
  exhaustive Scout-decision → Foundry-state table (`killed_insufficient_n` → `EVALUATED_INSUFFICIENT`;
  every other kill → `EVALUATED_KILLED`; `survive` → `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN`).
  `run_one_candidate` — the full resume-aware lifecycle: already-terminal → verify+skip;
  intent-without-terminal (crash) → verify the pinned econ-floor identity (`FoundryResumeIdentityMismatch`
  on drift), then deterministically re-execute and append exactly one terminal row; neither → record intent
  first, then execute. `run_family` — a plain ordered for-loop over the caller's own manifest-order
  sequence, structurally invariant to effect/p-value/verdict (no sort/filter/rank anywhere in it).
  `SingleFlightLock` — a real `fcntl.flock(LOCK_EX|LOCK_NB)` wrapper; a concurrent second acquire raises
  `ConcurrentRunnerRefused`; a sequential (already-released) second acquire succeeds.
- **Tests**: `test_foundry_interpreter.py` (6, TC-4..TC-8 + a relation-dispatch closure check),
  `test_foundry_family.py` (8, TC-9/TC-10), `test_foundry_freeze.py` (11, TC-11/TC-12/TC-13),
  `test_foundry_ledger.py` (7, TC-14/TC-18/TC-19), `test_foundry_runner.py` (7, TC-14/TC-15/TC-16/TC-17,
  plus TC-51's resume econ-floor-identity check) — 39 new tests, all hermetic (no dataset/network I/O).

## Files Changed

- `apps/backend/app/research/foundry_interpreter.py` -- new: generic interpreter + Scout-boundary adapter
- `apps/backend/app/research/foundry_family.py` -- new: Foundry family denominator + cap + late-insertion refusal
- `apps/backend/app/research/foundry_freeze.py` -- new: manifest generation/replay, freeze-set generator, freeze record, first-read-lock drift check
- `apps/backend/app/research/foundry_ledger.py` -- new: hash-chained append-only Foundry trial ledger
- `apps/backend/app/research/foundry_runner.py` -- new: canonical-order runner, verdict mapping, single-flight lock
- `apps/backend/tests/test_foundry_interpreter.py` -- new
- `apps/backend/tests/test_foundry_family.py` -- new
- `apps/backend/tests/test_foundry_freeze.py` -- new
- `apps/backend/tests/test_foundry_ledger.py` -- new
- `apps/backend/tests/test_foundry_runner.py` -- new
- `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` -- copies the real recorded
  `era_open_baseline.json` into the scoped rig's own `$ROOT/foundry/` before backend start

No edit was needed to `runs/goal-session-hypothesis-foundry/state/blueprint.md`: the goal-decomposer had
already pre-authored its "Iteration note (iter-2)" describing exactly this module split, and it matches
what was actually built.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **3825 passed, 8 skipped, 0 failed** (exit code 0; verified via the real shell exit code, not a
piped/truncated log). This includes all 39 new Foundry tests plus the full pre-existing suite (iter-1
baseline was 3787 passed/8 skipped) — no regressions.

Command: `cd apps/frontend && ./node_modules/.bin/tsc --noEmit`
Result: **0 errors** (no frontend files changed this iteration; gate re-verified anyway per DEFINITION OF
DONE TC-20).

Service startup verified via `scripts/dev.sh`: started (backend :8301, frontend :3301, both healthy within
1s), confirmed `GET /research/desk/micro/foundry` serves live real data on the actual dev backend, stopped
both (ports confirmed free, no lingering `uvicorn`/`next dev`/`next-server` child processes), started again
— no port conflicts on the restart. Both server processes killed before finishing this handoff.

## Known Issues

- **`generate_freeze_set`'s transitive scan only follows same-directory (`level == 1`) relative imports.**
  A deeper relative import (e.g. `micro_join.py`'s own `from ..providers.base import TradeEvent`, which
  reaches outside `app/research/` into a sibling top-level package) is not discovered/enumerated by this
  scanner. This is disclosed, not silently hidden: `_local_sibling_imports`'s own docstring explains why,
  and every module §8.4 explicitly names (`scout.py`, `micro_features.py`, `micro_observer.py`,
  `micro_join.py`, every `foundry_*.py`) lives flat inside `app/research/`, so the required-modules
  coverage TC-12 asks for is still fully proven. If a real J-06/J-07 freeze-set needs to prove coverage of
  a cross-package dependency (e.g. `app/providers/base.py`), the scanner's package-resolution needs
  widening first — flagged here for the reviewer/auditor to weigh whether that widening belongs in this
  era's scope or a later one.
- **Resume-identity verification (TC-15/TC-51) is intentionally partial this iteration.** `run_one_candidate`
  verifies only the intent row's pinned economic-floor identity on resume (the one identity this era's
  hermetic runner has something real to check against, since there is no real freeze/manifest/eligible-
  corpus wiring yet). Full freeze-hash + eligible-corpus-hash resume verification
  (`foundry_freeze.verify_freeze_set_unchanged` called from inside the runner) is real-epoch territory —
  deferred to J-06/J-07 when an actual freeze record and corpus manifest exist to verify against. This
  matches the iteration's own NOTES: the five `foundry_*.py` modules "operate on hermetic fixture epoch ids
  only this iteration."
  Real economic-floor materialization (a numeric `econ_floor_bps` from a real corpus) also stays J-07
  territory per OUT OF SCOPE — every test here passes a caller-supplied hermetic `econ_floor` dict.
- **§4.4's optional descriptive seam (aggressor-derived fallback-tercile disclosure for a composite Foundry
  trial) was not built.** The spec frames it as "implementation MAY add" one only if a composite candidate
  genuinely needs it, subject to strict byte-identical-by-default constraints; no TC in this iteration
  requires it, and building it now would be speculative (the simplicity bar: no abstraction before it is
  actually needed). Every Foundry trial's `fallback_tercile` disclosure currently renders `None` regardless
  of whether an underlying coordinate is `aggressor_derived=True`, since the fixed orchestration label
  `foundry_boolean_membership` is never in `scout.AGGRESSOR_DERIVED_FEATURES` by design (§4.2's own "must
  not pretend this synthetic membership is an existing scientific feature").
- **No CLI entry point for `foundry_runner.py` yet.** Spec §9 eventually wants this "implemented as a
  resumable manager/CLI operator act." This iteration built and hermetically proved the library functions
  (`run_one_candidate`/`run_family`/`SingleFlightLock`) that such a CLI would call; no TC this iteration
  requires an actual command-line wrapper, and one is naturally deferred to whichever iteration first wires
  real-epoch orchestration (J-06/J-07).
- No anti-goal violation was introduced: no real Foundry candidate outcome is read anywhere in this
  iteration's code or tests; no Scout-rail behavior changed (`scout.py` itself was not touched); no Foundry
  trial is ever written to the existing Scout ledger (`foundry_ledger.py` never imports `scout_ledger`); no
  guard was weakened; `docs/hypothesis-foundry/source-registry.json`, `epoch-manifest.json`,
  `freeze-set.json`, and `freeze-record.json` remain absent from the tree (confirmed via `find` before
  writing this handoff).
