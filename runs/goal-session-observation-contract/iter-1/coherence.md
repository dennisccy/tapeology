# Iteration 1 — Coherence Audit

**Iteration:** goal-observation-contract-iter-1
**Date:** 2026-09-03
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

Iteration touches only the future `GET /tape/{ticker}/observation` row group (blueprint
`state/blueprint.md` §Data Contract). No value from that row group — or any other Cockpit /
Structure / Desk value — is served anywhere this iteration; the diff adds no route, no UI fetch,
and no new endpoint. `apps/backend/app/observation_contract.py` is exactly the module the
blueprint names as the future canonical computing module for these rows (blueprint lines 68, 71:
`build_tape_observation` in `apps/backend/app/observation_contract.py`).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `tape_state`, `confidence`, `warm`, `primary_window`, `features` | OK — verbatim echo, no recomputation | `apps/backend/app/observation_contract.py:351-355` reads straight from `snapshot.*`; guarded by an AST test (`test_recompute_guard_no_classifier_or_feature_import_or_threshold_literal`, `apps/backend/tests/test_tape_observation_projection.py:160-163`) that fails if the module ever imports `app.engine.classifier`/`app.engine.features` or embeds a classifier threshold literal, with a `test_counterexample_*` proving the guard is not vacuous |
| `trade_event_count` | OK — verbatim `snapshot.event_count`, no re-count | `observation_contract.py:356`; `test_source_scan_builder_has_no_loop_over_trade_data` (`test_tape_observation_projection.py:195-208`) AST-asserts no `for`/`while` in the builder |
| `engine_identity.engine_semantics_version` | OK — single new module constant, read verbatim | `apps/backend/app/engine/tape_engine.py:32-39` (`ENGINE_SEMANTICS_VERSION`), read once by `observation_contract.py:43,387` — no second copy |
| `engine_identity.windows`, `engine_identity.warmup_min_events` | OK — pre-existing `Config` fields/methods, unchanged | `observation_contract.py:391-392` calls `config.window_label(...)` / `config.warmup_min_events`, both pre-existing in `apps/backend/app/config.py` (confirmed unmodified by this diff) |
| `observation_hash`, `artifact_hash` | OK — one hash law each, computed once | `observation_contract.py:160-172`; not served or duplicated anywhere else in the diff |
| `implementation_provenance.*` (`engine_source_hash`, `source_revision`, `worktree_dirty`) | OK — one resolver, memoized once per process | `observation_contract.py:218-244`; `test_provenance_resolver_memoized_across_repeated_calls` (`test_tape_observation_projection.py:359-379`) proves at most one git subprocess call |
| `engine_identity.tape_state_vocabulary` (new field, not yet in blueprint's per-field table) | OK, with an advisory note — see below | `observation_contract.py:54-60` (`TAPE_STATE_VOCABULARY`) |

No new UI surface was added, so Part A.2 (non-canonical source) does not apply — there is nothing
to fetch this from yet. No value outside the registered `TapeObservation` group was touched.

## Information Architecture check

No new page, route, panel, link or component. `apps/backend/app/main.py` is byte-unchanged
(`git diff <snapshot-sha> -- apps/backend/app/main.py` empty) — the `/tape/{ticker}/observation`
route is still absent, exactly as the blueprint and iter spec require ("route lands iter-5").
Every `apps/frontend/**` file is byte-unchanged (`git diff <snapshot-sha> -- apps/frontend/`
empty). Inspected `apps/backend/app/main.py` directly to confirm no router registration was
added.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `GET /tape/{ticker}/observation` | OK — correctly NOT built yet, matches blueprint's "(planned — route lands iter-5)" | `apps/backend/app/main.py` (unchanged) |
| Cockpit `/`, `/structure`, `/desk` | OK — unchanged | no frontend file in the diff |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Unregistered value: `engine_identity.tape_state_vocabulary`.** This is a new field (the
  closed 5-state name list) that is not itemized as its own row in the blueprint's Data Contract
  table (it currently falls under the umbrella "`engine_identity.*`" wildcard in blueprint line
  68, so it is arguably already covered, but the field-level detail lives only in
  `docs/observation-contract-spec.md` / `docs/goal.md`'s Constitution §1, not in the blueprint
  itself). Not a duplicate-computation FAIL: `TAPE_STATE_VOCABULARY` in
  `apps/backend/app/observation_contract.py:54-60` is a literal name-list constant (not logic,
  not a threshold), required by the module's own recompute guard (it cannot import
  `app.engine.classifier`), and is cross-checked every test run against `classifier.py`'s own
  `STATE_*` constants by `test_tape_state_vocabulary_matches_classifier_states`
  (`test_tape_observation_projection.py:176-184`), so drift would be caught immediately rather
  than silently diverging. No action required; noted for the decomposer's awareness only.
- This iteration is backend-only with zero served/UI surface (per spec, "no visible product
  change"), so most of Part B does not apply — recorded here as a deliberate no-op consistent
  with the skill's "pure infra iteration" case, not skipped.
