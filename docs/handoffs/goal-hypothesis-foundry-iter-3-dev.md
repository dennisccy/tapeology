# goal-hypothesis-foundry-iter-3 Dev Handoff

**Phase:** goal-hypothesis-foundry-iter-3
**Date:** 2026-08-26
**Agent:** developer
**Status:** complete

## What Was Built

- **New hermetic "complete factory" oracle suite** (`apps/backend/tests/test_foundry_hermetic_epoch.py`,
  9 tests / TC-1 through TC-8): drives the REAL production
  `foundry_compiler` -> `foundry_interpreter` -> `foundry_family` -> `foundry_ledger` -> `foundry_runner`
  path together (no mock of any of the five modules) over one composite epoch:
  - **TC-1/TC-2** (one combined test): one `BLOCKED_SPEC_GAP` source, one `EXCLUDED_PREVIOUSLY_KILLED`
    source, one `ALIASED_VARIANT_VOCABULARY` source, plus seven `FROZEN_READY` variants in one Foundry
    family, terminating `EVALUATED_INSUFFICIENT` (`killed_insufficient_n`), `EVALUATED_KILLED` via each
    of `killed_null`/`killed_direction`/`killed_concentration`/`killed_economic`/`killed_fragile`, and one
    correctly-signed `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN`. Asserts canonical manifest-order visiting
    (ledger row order == input order, ordinal 0..6) is unaffected by any kill/survivor, every terminal
    row's family denominator/best-of-N disclosure equals the pre-frozen manifest value (`7`), and every
    non-compiled source keeps its declared disposition.
  - **TC-3**: an all-`BLOCKED_*`/`EXCLUDED_*`/`ALIASED_*` epoch (zero `FROZEN_READY` variants) — the
    compiler produces zero `CandidateSpec`s and an empty family registry; the read model over zero
    anchors is an honest all-zero summary, not an error.
  - **TC-4**: an all-killed epoch (six variants covering every kill/insufficient reason) completes
    validly with zero `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN` rows.
  - **TC-5**: a multi-survivor epoch (two independently-surviving candidates with a kill in between)
    preserves every survivor; no ranking/selection/demotion of one over another.
  - **TC-6**: a large synthetic fixture spanning 4 families x 5 variants = 20 candidates, with a
    simulated mid-epoch crash (12 candidates processed, then every in-memory object including the ledger
    instance is discarded). Resume opens a BRAND NEW `FoundryLedger` on the same on-disk directory and
    deliberately re-visits the FULL 20-candidate sequence from ordinal 0 (never trusting an assumed
    "resume from candidate 12" position) — proves position is reconstructed from the ledger's own
    already-terminal rows: the first 12 are verified+skipped byte-identically (zero duplicate rows), the
    remaining 8 execute fresh, canonical order and hash-chain integrity (`verify_chain()["ok"]`) hold
    across the crash boundary.
  - **TC-7** (parametrized x2 + one no-new-abstraction test): a hermetic population source (a lazy
    generator standing in for a future real extraction step) that raises the EXISTING
    `micro_accessor.MicroAccessorSealedShardError`/`MicroAccessorOriginFenceError` partway through
    `foundry_interpreter.resolve_population`'s own anchor iteration. The Foundry side fails closed: the
    exception propagates uncaught out of `run_one_candidate`, no terminal `EVALUATED_*`/survivor row is
    ever written (only the pre-outcome intent row may exist), and a source-identity check confirms the
    reused exception types ARE the real `micro_accessor` ones (no Foundry-local subclass/wrapper).
  - **TC-8**: across a fresh 7-outcome-type sweep, every terminal row's
    `screen_result.screen_result.evidence_class` is the fixed literal `historical_exposed_diagnostic`
    (`scout.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC`) — never `historical_oos`/`live_confirmatory`.
  - Every per-kill-type anchor fixture (null/direction/concentration/economic/insufficient/fragile/
    survive) is a direct translation of an ALREADY hermetically-proven `test_scout.py` fixture into the
    Foundry's `PopulationAnchor`/`ComponentResolution` shape — never invented from scratch. `killed_fragile`
    needed the same `scout._two_sided_p` monkeypatch `test_scout.py`'s own fragile test uses (scoped per-
    candidate via `monkeypatch.context()`, never applied to the whole composite run, so it cannot mask
    the other six candidates' own real p-values).
- **`foundry_runner.py` resume-identity gap closed** (`run_one_candidate`, TC-9): the already-terminal
  fast path now re-verifies `manifest_hash` (read off the stored terminal row itself) and `econ_floor_bps`
  (read off that candidate's own pinned intent row) against the current invocation's inputs, raising the
  existing `FoundryResumeIdentityMismatch` on either drift — mirroring the intent-without-terminal
  branch's own econ-floor check three lines below it. Matching inputs still return the existing row
  unchanged (no behavior change for the common case; `test_tc14_already_terminal_candidate_is_verified_
  and_skipped_not_re_executed` and the new TC-9 match case both still pass).
- **`foundry_source_registry.py`: `SourceRecord` gains two §1.4 fields**:
  - `source_hash: str` — `init=False`, computed as `sha256(source_excerpt)` inside `__post_init__`, so it
    can never be caller-supplied and therefore can never drift from `source_excerpt` (mirrors the module's
    existing "always recomputed, never cached" `source_registry_hash` discipline one level up). Deliberately
    excluded from `source_registry_hash`'s own canonical projection (it is a pure derivation of
    `source_excerpt`, which is already included there — the same reason `CandidateSpec._canonical_fields`
    excludes `candidate_spec_hash` from its own hash input).
  - `alternatives: tuple[str, ...] = ()` — a per-record disclosure naming the `source_id`(s) of the sibling
    representation(s) this record legally alternates with, additive alongside (never a replacement for)
    `foundry_family_key` membership. Empty when no ratified alternative exists. Included in
    `source_registry_hash`'s canonical projection (real disclosure content, unlike the derived `source_hash`).
  - Extended the existing "two explicitly-frozen legal variants" fixture pair (`_variant_record` in
    `test_foundry_compiler.py`, the fixture `J-02` step 2 / iter-1 TC-4 already uses) with an `alternatives`
    parameter and a new test (`test_tc11_two_legal_variants_name_each_other_as_their_alternative`) proving
    each variant names the other; `test_foundry_source_registry.py` gained `source_hash` correctness tests
    (`test_tc10_*`, 3 tests) plus an empty-default test and a registry-hash-sensitivity test for
    `alternatives` (2 tests).
- **`docs/hypothesis-foundry-spec.md` §1.4**: added the `alternatives` field-table row, documentation-only.

## Files Changed

- `apps/backend/tests/test_foundry_hermetic_epoch.py` -- new: composite/all-blocked/all-killed/
  multi-survivor/checkpoint-resume/protected-data-trip hermetic oracle suite (TC-1..TC-8, 9 tests)
- `apps/backend/app/research/foundry_runner.py` -- `run_one_candidate`'s already-terminal fast path now
  re-verifies `manifest_hash`/`econ_floor_bps` before returning a cached row (TC-9)
- `apps/backend/app/research/foundry_source_registry.py` -- `SourceRecord` gains `source_hash`
  (`init=False`, `sha256(source_excerpt)`) and `alternatives` (`tuple[str, ...]`, default empty);
  `_canonical_source_record` includes `alternatives` in `source_registry_hash`
- `apps/backend/tests/test_foundry_source_registry.py` -- 5 new tests: `source_hash` correctness/
  non-constructibility (TC-10), `alternatives` default-empty and registry-hash sensitivity
- `apps/backend/tests/test_foundry_compiler.py` -- `_variant_record` gains an `alternatives` parameter;
  1 new test (TC-11) extends the existing two-legal-variant fixture pair
- `apps/backend/tests/test_foundry_runner.py` -- 2 new tests (TC-9): already-terminal fast path raises
  `FoundryResumeIdentityMismatch` on `manifest_hash` drift and on `econ_floor_bps` drift
- `docs/hypothesis-foundry-spec.md` -- §1.4 field table gains the `alternatives` row

No edit was needed to `runs/goal-session-hypothesis-foundry/state/blueprint.md`: its pre-authored
"Iteration note (iter-3)" already described exactly this scope and matches what shipped; no Data Contract
row was added or re-homed.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **3842 passed, 8 skipped, 0 failed** (exit code 0). iter-2's baseline was 3825 passed / 8 skipped;
this iteration adds exactly 17 new test items (16 new test functions; `test_tc7_a_protected_data_trip_
during_anchor_resolution_fails_closed` is parametrized over the two exception types, collecting as 2 items)
with zero regressions. Skip count unchanged at 8.

Command: `cd apps/frontend && ./node_modules/.bin/tsc --noEmit`
Result: **0 errors** (no frontend files changed this iteration).

Confirmed via `find`: `docs/hypothesis-foundry/source-registry.json`/`epoch-manifest.json`/
`freeze-set.json`/`freeze-record.json` remain absent from the tree — no real Foundry epoch artifact was
created anywhere in this iteration's code, tests, or manual verification steps.

Service startup verified via `scripts/dev.sh`: started (backend :8301, frontend :3301, both healthy),
confirmed `GET /research/desk/micro/foundry` serves live real data on the actual dev backend (era
identity + era-open baseline, unchanged shape from iter-2), stopped both, started again — no port
conflicts on the restart, no lingering `uvicorn`/`next dev`/`next-server` child processes (verified via
`ps`/`lsof` after each stop). Both server processes killed before finishing this handoff.

## Known Issues

- **`generate_freeze_set`'s transitive scan is still same-directory-only (`level == 1`)** — carried
  unchanged from iter-2 (real J-06/J-07 territory; this iteration did not touch `foundry_freeze.py`).
- **Resume-identity verification is still intentionally partial for the freeze/eligible-corpus hashes** —
  this iteration closed the `manifest_hash`/`econ_floor_bps` gap on the already-terminal fast path (TC-9),
  but the full post-first-read-lock science-hash verification (`foundry_freeze.verify_freeze_set_unchanged`
  called from inside the runner) still awaits a real freeze record to verify against — deferred to
  J-06/J-07, matching the module's own scope note.
- **§4.4's optional descriptive seam and a CLI entry point for `foundry_runner.py` are still not built** —
  neither TC-1..TC-13 in this iteration nor any prior iteration requires them; both remain naturally
  deferred to whichever iteration first wires real-epoch orchestration.
- **TC-7's protected-data-trip proof is intentionally hermetic-only** — it reuses the real
  `MicroAccessorSealedShardError`/`MicroAccessorOriginFenceError` exception types via a hermetic
  generator stand-in for a future real extraction step; it does not wire the real
  `micro_accessor.MicroAccessor` into the Foundry runner's real-corpus resolution path, per this
  iteration's own scoping (`state/assumptions.md` iter-3) and `docs/hypothesis-foundry-spec.md` §10's
  "future work, meaning fixed here" framing — that wiring is J-07 territory.
- No anti-goal violation was introduced: no real Foundry candidate outcome is read anywhere in this
  iteration's code or tests; `scout.py` itself was not modified (only monkeypatched inside a test's
  narrowly-scoped `monkeypatch.context()`, restored immediately after); no Foundry trial is ever written
  to the Scout ledger; no guard was weakened, xfail'd, or deleted; every fixture's `evidence_class` stayed
  `historical_exposed_diagnostic` (TC-8); no `docs/hypothesis-foundry/` real-epoch artifact was created
  (confirmed via `find` before writing this handoff).
