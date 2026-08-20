# goal-rapid-microscope-iter-16 Dev Handoff

**Phase:** goal-rapid-microscope-iter-16
**Date:** 2026-08-20
**Agent:** developer
**Status:** complete

## What Was Built

Three leakage-trap-suite entries (TR-3, TR-22, TR-26) plus three small carried passengers, per the
plan. J-10 moves 24/29 -> 27/29 traps and stays `partial` at the end of this round — planned
(TR-23/TR-24 are round 17's), not a shortfall.

### TR-3 — accessor origin-fence (`docs/rapid-validation-spec.md` section 9)

An explicitly-labeled trap-suite entry covering all three clauses, split across the two files the
plan directed:

- **(a) single-read fence** — `apps/backend/tests/test_micro_accessor.py`'s existing, non-vacuous
  `test_tc1_a_read_at_or_before_origin_succeeds` / `test_tc1_a_read_strictly_after_origin_raises_a_
  typed_error_never_empty` / `test_tc1_origin_equal_to_the_dataset_session_date_is_visible_the_
  fence_is_inclusive` — folded in by reference (a new `# === TR-3 ===` header block names every
  clause and its proving test by exact name), not reimplemented.
- **(b) the multi-session AGGREGATE-boundary proof** — a genuinely NEW test,
  `test_tr3_an_origin_fenced_loop_over_several_sessions_returns_exactly_the_set_le_origin` in
  `test_walkforward.py`. Direct code inspection (not assumed) confirmed the plan's own resolution
  of the spec's TC-2 framing ambiguity: no production call site anywhere constructs
  `MicroAccessor(origin=...)` today — `micro_join.py:434` and `scout.py:353` both pass
  `origin=None` (the disclosed unfenced mode), and `walkforward.py`'s `build_folds` is a pure
  function over `session_dates: list[str]` that never touches the accessor. So this is a NEW test
  proving the accessor's own aggregate behaviour directly (three planted sessions S1 < T=S2 < S3;
  at `origin=S2` the accepted set is exactly `{S1, S2}`, at `origin=S3` exactly `{S1, S2, S3}` —
  boundary-exact both directions, the iter-11 lesson: never prove only the refusal side). No
  production edit to `micro_accessor.py` or `walkforward.py`; reuses
  `test_micro_accessor.py`'s own `_plant_dataset_and_snapshot` verbatim (imported cross-file, the
  codebase's own established precedent — `test_micro_accessor.py` itself already imports
  `_events_for_store` from `test_micro_observer.py` the same way).
- **(c) import-ban** — `test_micro_accessor.py`'s existing, non-vacuous
  `test_tc3_no_module_other_than_micro_accessor_imports_read_snapshot_rows` /
  `test_tc3_the_guard_also_catches_a_module_qualified_call_that_imports_no_banned_name` /
  `test_tc3_micro_join_and_scout_no_longer_import_read_snapshot_rows_directly` /
  `test_tc3_import_ban_guard_can_fail_on_a_seeded_violation` (its own non-vacuity proof already
  existed) — folded in by reference, unchanged.
- **Non-vacuity for the fence clause** —
  `test_tr3_weakening_the_origin_fence_comparison_makes_the_guarding_assertion_fail_restoring_it_
  passes` (`test_micro_accessor.py`). See "Non-vacuity proofs" below.

### TR-22 — exposure-registry auto-classification (spec section 9 / 6.7)

An explicitly-labeled trap-suite entry in `test_walkforward.py`, all three clauses satisfied by
folding in existing, already non-vacuous coverage:

- **(a)/(b) both classification directions** — the existing `test_tc13_a_mode_b_spec_registered_
  after_a_logged_exposure_is_auto_classed_diagnostic` / `test_tc13_a_mode_b_spec_registered_
  before_any_exposure_of_its_window_classes_historical_oos` pair already proves registered-after
  -> `historical_exposed_diagnostic` and registered-before -> `historical_oos`.
- **(c) r2 initialization** — the existing `test_tc14_freshly_initialized_registry_reads_every_
  named_window_exposed_before_any_serving_act` (this file) and `test_tc14_r2_initialization_pre_
  marks_every_named_window_exposed_before_any_serving_act` (`test_micro_accessor.py`).
- **Non-vacuity** — a NEW test,
  `test_tr22_mutating_is_exposed_before_to_always_return_false_makes_the_auto_classification_
  assertion_fail_restoring_it_passes`. See "Non-vacuity proofs" below, including a genuine
  construction-time discovery: the obvious way to write this test (call `wf.evaluate_mode_b_fold`
  twice, once mutated once restored) is itself SILENTLY VACUOUS, because `append_fold_result` is
  idempotent on `(sequence_id, fold_index, spec_hash)` — a second call with the identical spec/fold
  returns the FIRST (mutated, wrong) cached row rather than re-running the classification. The test
  instead calls `wf.classify_evidence_class` directly (the pure function under test), sidestepping
  the ledger entirely.

### TR-26 — `quote_depletion` revealing-quote availability (spec section 3, r6 owner ruling
2026-08-18) — the one genuine production fix this round, closing an item open since round 2

**Headline, stated plainly for later lanes: the TR-26 assertion flip (`observed_through`/
`available_at` `2.0` -> `3.0`) is the SPECIFIED BEHAVIOUR FIX, not a regression.** It implements
the owner's r6 ruling that availability is stamped at the REVEALING quote, not the last
same-price one ("measurement end != knowledge time") — closing a `quote_depletion` timing item
that has been open since round 2 of this era.

`apps/backend/app/research/micro_observer.py`'s `_advance_depletion_run`, price-change-termination
branch: previously called `self._resolve_depletion(side, run)` using the OLD run's own stale
`observed_through` (the LAST same-price quote, one instant too early). Per the r6 owner ruling
("measurement end != knowledge time"), the completion's `observed_through`/`available_at` must
stamp the REVEALING price-CHANGING quote's own instant instead — the point at which the observer
actually learns the run has ended. Fix is one line (`run["observed_through"] = ts`) inserted
immediately before the existing `self._resolve_depletion(side, run)` call in that branch. The
depletion MAGNITUDE (`start_size - current_size`) is computed from the pre-change run's own
`start_size`/`current_size`, untouched by this change. The bound-termination branch (closes by
hitting `DEPLETION_WINDOW_QUOTES`) was already correct and is unchanged — a new dedicated test now
proves it, where none existed before.

**This assertion change is the specified behaviour fix, not a regression**:
`test_micro_observer.py::test_tc10_quote_depletion_resolves_at_a_price_change_attached_to_the_
next_trade_row`'s `observed_through`/`available_at` assertions changed from `2.0` to `3.0`
(`value` stays `200.0`, unaffected). **A second, previously-undiscovered test needed the identical
correction**: `test_tc7_tr18_quote_depletion_magnitude_is_refused_under_an_unverified_unit` asserts
the SAME timing fact (from the SAME `_depletion_events()` fixture) under the unit-refusal path —
this was not named in the plan's file list but is mechanically the same value from the same fixture
and method, so leaving it uncorrected would have reintroduced the exact bug as a regression in a
different test. Both are now `3.0`, documented as the specified fix in both docstrings.

New coverage added:
- `test_tc10_bound_terminated_depletion_resolves_at_the_bound_hitting_quotes_own_instant` — a NEW
  20-same-price-update fixture (`DEPLETION_WINDOW_QUOTES`), proving the ALREADY-correct
  bound-termination path for the first time with a dedicated test.
- `test_tc11_truncating_strictly_before_the_revealing_quote_leaves_the_run_unresolved` /
  `test_tc11_truncating_at_the_revealing_quote_resolves_the_run_deterministically` — the
  TR-1-style truncation-boundary pair: truncating strictly before the revealing quote leaves the
  run `unavailable` (swept by `finalize()`, never guessed); truncating at/after it resolves
  deterministically at that exact instant, even with no trade afterward to carry the completion
  (the close-out row attaches it).
- `test_tc12_tr26_reverting_the_fix_makes_the_corrected_assertion_fail_restoring_it_passes` — the
  non-vacuity mutation-proof. See below.

### Passenger 1 — `MicroReadinessSection` testid (closes iteration 15's COHERENCE-WARN)

`apps/frontend/app/desk/page.tsx`'s `MicroReadinessSection` loading and unavailable early returns
now wrap their content in `data-testid="micro-readiness-section"`, mirroring
`ValidationVaultSection`'s already-fixed pattern (`page.tsx:6684-6699`) exactly. The loaded-state
return already carried the testid; it is now present in all three render states.

### Passenger 2 — Scout Ledger table survives a malformed/tampered trial row

`apps/frontend/app/desk/page.tsx`'s Scout Ledger table: the two previously-undefended reads
(`trial.feature.name`/`trial.feature.transform`, `trial.outcome.horizon_key`) now use optional
chaining with a `"—"` fallback glyph, so a malformed row degrades only its own cell(s) instead of
throwing during render (which — per the carried context, `grep -c "ErrorBoundary\|
componentDidCatch\|getDerivedStateFromError"` on the whole page returns 0 — would otherwise blank
the entire `/desk` page). Row-level defensive rendering only, exactly as scoped — no page-wide
`ErrorBoundary` was added (explicitly out of scope).

Reachability was proven with a one-off manual script against the real, unmodified `ScoutLedger`/
`list_scout_families` public API (scout.py/scout_ledger.py are frozen this round — no new
committed test touches them; see "Manual reachability proof" below): a row appended via
`ScoutLedger.append_row()` with the exact sparse field set `test_desk_scout_tool_byte_identical_on_
a_populated_state` (`test_mcp_server.py`) already uses (`family_id`, `family_root_id`,
`candidate_id`, `decision`, `reason` — no `feature`/`outcome` key at all) is served completely
verbatim by `list_scout_families` (`scout.py:1273`, docstring: "every row verbatim"). This
confirms the malformed shape the frontend now defends against is genuinely reachable through the
real backend contract, not hypothetical.

### Passenger 3 — `_PRICE_ARITHMETIC_FIELDS` seeded-violation counter-test

`apps/backend/tests/test_desk_ui_guards.py` gains
`test_desk_page_price_arithmetic_guard_catches_sealed_tranche_and_universe_counts_and_withheld_
excluded_arithmetic`, mirroring the existing `test_desk_page_price_arithmetic_guard_catches_micro_
readiness_field_arithmetic` shape exactly — proving the two iteration-15-added clauses
(`readiness.sealed_tranche.*`, `universeCounts.*`, `readiness.joinable_corpus.withheld_excluded`)
actually catch seeded client-side arithmetic (division, addition, subtraction), plus a negative
control confirming no over-match on a non-arithmetic template-literal render of the same fields.

## Non-vacuity proofs

Per this round's binding governing rule (iteration 15's own opaque-pool regression test was
structurally unable to fail because it sealed its shard under an unregistered universe, so the leak
path it was written for never executed — caught only by the auditor's mutation-proof, not by
review or QA): for each of TR-3, TR-22, TR-26, the defect the trap guards against was deliberately
reintroduced, shown to make the guarding assertion FAIL with the exact leaked/incorrect value
named, then the code was restored and shown to pass again.

**TR-26 (the strongest form — the REAL bug in the REAL file, not a simulation):**

The bug already existed in production before this iteration's fix. The correction to `test_tc10_
quote_depletion_resolves_at_a_price_change_attached_to_the_next_trade_row`'s assertion (`2.0` ->
`3.0`) was written and run BEFORE the production fix was applied — a genuine TDD red step, not a
monkeypatch simulation:

```
$ .venv/bin/python -m pytest tests/test_micro_observer.py -v
FAILED tests/test_micro_observer.py::test_tc10_quote_depletion_resolves_at_a_price_change_attached_to_the_next_trade_row
FAILED tests/test_micro_observer.py::test_tc7_tr18_quote_depletion_magnitude_is_refused_under_an_unverified_unit
FAILED tests/test_micro_observer.py::test_tc11_truncating_at_the_revealing_quote_resolves_the_run_deterministically
FAILED tests/test_micro_observer.py::test_tc12_tr26_reverting_the_fix_makes_the_corrected_assertion_fail_restoring_it_passes
========================= 4 failed, 31 passed in 0.39s =========================
```
All four failures were exactly the fix-dependent ones (TC-10 bound-termination and TC-11's
strictly-before case, both independent of the bug, correctly passed already). The single-line fix
(`micro_observer.py`) was then applied; re-running the same file:
```
$ .venv/bin/python -m pytest tests/test_micro_observer.py -q
...................................                                      [100%]
```
35/35 pass (31 original + 4 new). `test_tc12_tr26_...` additionally provides a PERMANENT regression
guard: it monkeypatches in the exact pre-fix `_advance_depletion_run` body, asserts the leaked
value is `2.0` (`!= 3.0`), then `monkeypatch.undo()`s and re-asserts `3.0` — proven, before the
production fix existed, to correctly FAIL at its own final assertion (see the RED-step transcript
above, where this test is one of the four failures — its "restore" phase genuinely depended on the
real fix being present, not merely on monkeypatch mechanics).

**TR-3 (self-contained mutation-proof test,
`test_tr3_weakening_the_origin_fence_comparison_makes_the_guarding_assertion_fail_restoring_it_
passes`):** monkeypatches `micro_accessor._session_date_for_dataset` (the fence's own date
resolver) to always report `"2000-01-01"` — the exact effect of a comparison that never refuses.
Under the sanity check (unpatched), reading a strictly-after-origin dataset raises
`MicroAccessorOriginFenceError` as required. Under the weakened patch, the SAME read leaks the
rows (`assert leaked_rows` — non-empty, the exact leaked value the defect would produce, proving
the guard TC-1 requires would fail against this weakened code). `monkeypatch.undo()`, then the
identical read raises `MicroAccessorOriginFenceError` again — byte-identical restoration
(guaranteed by pytest's own monkeypatch teardown mechanics, stronger than a manual file edit).

**TR-22 (self-contained mutation-proof test,
`test_tr22_mutating_is_exposed_before_to_always_return_false_makes_the_auto_classification_
assertion_fail_restoring_it_passes`):** monkeypatches `ExposureRegistry.is_exposed_before` to
always return `False` (the exact defect: prior exposure silently undetected). Against a registry
with a real logged exposure entry BEFORE the spec's `registered_at`, `classify_evidence_class`
under the mutation wrongly returns `historical_oos` (`assert leaked ==
wf.EVIDENCE_CLASS_HISTORICAL_OOS` — the exact incorrect value; genuinely-exposed evidence silently
promoted to fake out-of-sample, the precise class-mixing anti-goal TR-22 exists to prevent).
`monkeypatch.undo()`, then the identical call correctly returns
`EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC` again.

All 7 of the above (the 3 new mutation-proofs plus the 4 TR-26-adjacent new tests) were re-verified
individually by exact node id immediately before writing this handoff:
```
tests/test_micro_accessor.py::test_tr3_weakening_the_origin_fence_comparison_makes_the_guarding_assertion_fail_restoring_it_passes PASSED
tests/test_walkforward.py::test_tr3_an_origin_fenced_loop_over_several_sessions_returns_exactly_the_set_le_origin PASSED
tests/test_walkforward.py::test_tr22_mutating_is_exposed_before_to_always_return_false_makes_the_auto_classification_assertion_fail_restoring_it_passes PASSED
tests/test_micro_observer.py::test_tc12_tr26_reverting_the_fix_makes_the_corrected_assertion_fail_restoring_it_passes PASSED
tests/test_micro_observer.py::test_tc10_bound_terminated_depletion_resolves_at_the_bound_hitting_quotes_own_instant PASSED
tests/test_micro_observer.py::test_tc11_truncating_strictly_before_the_revealing_quote_leaves_the_run_unresolved PASSED
tests/test_micro_observer.py::test_tc11_truncating_at_the_revealing_quote_resolves_the_run_deterministically PASSED
7 passed in 0.32s
```

## A naming discipline note (self-caught during construction)

This codebase's per-file `TC-N` numbering is historically overloaded across iterations — e.g.
`test_micro_accessor.py`'s own "TC-2" already names sealed-shard invisibility (unrelated to the
origin fence), and `walkforward.py`'s module docstring names `test_micro_join.py`'s own "TC-4" as
the micro_join re-point proof. Naming a brand-new iter-16 test `test_tc2_tr3_...` or
`test_tc4_tr3_...` would have silently collided with those established, DIFFERENT meanings. Every
new test this round therefore carries only the globally-unambiguous `tr3`/`tr22`/`tr26` spec-trap
tag (never a reused bare `tcN` prefix) — except in `test_micro_observer.py`, where the file's own
pre-existing "TC-10" section already IS quote_depletion (so `tc10`/`tc11`/`tc12` genuinely
harmonize there, not collide).

## Files Changed

- `apps/backend/app/research/micro_observer.py` — the one production edit: `_advance_depletion_
  run`'s price-change branch now stamps `run["observed_through"] = ts` (the revealing quote's own
  instant) before resolving. 7 lines added (comment + fix), 0 removed.
- `apps/backend/tests/test_micro_observer.py` — 2 existing assertions corrected (`2.0` -> `3.0`,
  both documented as the specified fix); 4 new tests (bound-termination, 2x truncation-boundary,
  non-vacuity mutation-proof) plus a `# === TR-26 ===` section header.
- `apps/backend/tests/test_micro_accessor.py` — 1 new non-vacuity test plus a `# === TR-3 ===`
  section header cross-referencing every existing test that proves the other two clauses.
- `apps/backend/tests/test_walkforward.py` — imports extended (`CONFIG`, `MicroAccessor`,
  `MicroAccessorOriginFenceError`, `resolve_micro_snapshots_dir`, cross-file `_plant_dataset_and_
  snapshot`); 1 new TR-3 aggregate-boundary test + header; 1 new TR-22 non-vacuity test + header;
  module docstring note added.
- `apps/backend/tests/test_desk_ui_guards.py` — 1 new seeded-violation counter-test for the two
  iteration-15 `_PRICE_ARITHMETIC_FIELDS` clauses.
- `apps/frontend/app/desk/page.tsx` — `MicroReadinessSection`'s two early returns wrapped in the
  `micro-readiness-section` testid; Scout Ledger table's two undefended reads made
  optional-chained with a `"—"` fallback.

No change to `vault.py`, `tick_recorder.py`, `micro_readiness.py`, `scout.py`, `scout_ledger.py`,
`walkforward_ledger.py`, `micro_routes.py`, `micro_chain_ledger.py`, any `referee_*.py`, any
Playbook detector, or `Config` — confirmed via `git diff --stat` (only the 6 files above show
modified) and via an explicit zero-diff check on the full "should stay untouched" list
(`vault.py`, `scout.py`, `scout_ledger.py`, `walkforward.py`, `micro_accessor.py`,
`micro_routes.py`, `micro_readiness.py`, `micro_chain_ledger.py`, `config.py`) plus the SHA-256
re-check below. `micro_accessor.py` and `walkforward.py` themselves received ZERO production
edits this round — test-file-only, exactly as scoped.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ --junitxml=<path>`

- `tests/test_micro_observer.py`: 35 passed, 0 failed (see the RED->GREEN transcript above for the
  TR-26 proof sequence).
- `tests/test_micro_accessor.py`: 18 passed, 0 failed.
- `tests/test_walkforward.py`: all passed, 0 failed (68 collected in this file).
- `tests/test_desk_ui_guards.py`: all passed, 0 failed (81 collected in this file).
- The 7 new/mutation-proof tests individually re-confirmed by exact node id immediately before
  writing this handoff (transcript above).
- Frontend: `npx tsc --noEmit` (apps/frontend) — 0 errors, including the two optional-chained Scout
  table reads and the unchanged `MicroReadinessSection` props.
- Manual reachability proof (not a committed test — `scout.py`/`scout_ledger.py` frozen this
  round): `ScoutLedger.append_row()` with the sparse field set, read back via `list_scout_families`
  — confirmed `feature`/`outcome` keys genuinely absent from the served row (script + output in
  "Passenger 2" above).
- `Config().config_fingerprint()` -> `08e471b10130e1e2` (unchanged, matches the era pin).
- SHA-256 re-check, six `referee_*.py` + `micro_chain_ledger.py`, byte-identical to the
  iteration-0 baseline (`docs/handoffs/goal-rapid-microscope-iter-0-dev.md`, re-confirmed against
  iteration 15's own re-check):
  ```
  6dd807b5ab69af033686a395484b1b10515d0f453a79c0943e534a578259786c  referee_adjudicate.py
  482f38a11740bc839038290fc2a0e131f649a23f17265cbca0f2aa19fe07e1c5  referee_evidence.py
  34917e381e4169aa029f5d0e18228fde75e4d3db5acec516f937e3ef3b371603  referee_null.py
  03840c863b1e1f382ad2588d3bb6d8dc0e36a70582c3cb7a716638dabef32d99  referee_registry.py
  0cc3a06f7b382c63d544886ec74a47f2414612fc77dd3dac444b00cc35216140  referee_routes.py
  fba8816a5d4901ea1eeb7faa71e350538f546a2a3af1f9edb5f6f5aa1ec5271c  referee_stats.py
  c8e86991ba229dadad4b76342bd97c5ead1fe62d6373e5db94fdf053ccaebaff  micro_chain_ledger.py
  ```
- **Full backend suite (authoritative, read from `--junitxml`, not the redirected stdout stream —
  this session's own known pytest-version gotcha, which has caused five miscounts before this
  round)**: **3245 collected / 3237 passed / 8 skipped / 0 failed / 0 errors**, in a clean run with
  nothing else competing for CPU. Baseline (iteration 15): 3237 collected / 3229 passed / 8 skipped
  / 0 failed. **Delta: +8 collected / +8 passed / 0 skipped-count change / 0 failed** — exactly the
  8 new tests this round adds (4 in `test_micro_observer.py`, 1 in `test_micro_accessor.py`, 2 in
  `test_walkforward.py`, 1 in `test_desk_ui_guards.py`), nothing removed, zero regressions.

### A transient failure this dev pass investigated and did not reproduce in the clean run

Two earlier runs during this dev pass each showed exactly 2 failures —
`test_micro_join.py::test_tc4_real_corpus_join_playbook_signal_is_unaffected_by_the_accessor_re_
point` (`AssertionError: assert 'no_covering_snapshot' == 'joined'`) and
`test_micro_snapshots.py::test_tc12_real_corpus_identity_re_verifies_on_a_second_read`
(`built_utc` differed between two reads of the same real dataset's snapshot metadata, ~50s apart).
The first of those two runs had a real, self-inflicted confound (I started `scripts/dev.sh` for the
service-startup check WHILE that suite was running — competing CPU load I introduced myself); the
second run was intended to be clean but still showed the identical 2 failures, which is why this
was investigated further rather than dismissed as contention. Direct code reading built a specific,
well-supported hypothesis, but **it was not proven to full certainty and was not reproduced in the
authoritative clean run**, so it is recorded here as a hypothesis, not a settled diagnosis:
`micro_snapshots.py`'s `feature_source_hash()` deliberately hashes `_IDENTITY_SOURCE_MODULES =
(mf, mo)` — `micro_features` AND `micro_observer` — specifically so an observer-only source edit
(exactly this round's TR-26 fix) invalidates every real on-disk snapshot's cached identity at
once (the function's own docstring: "an observer-only edit CHANGES every stored row's values while
every stored identity still verifies... hashing both... can only ever turn a would-be hit into an
honest MISS, never the reverse"). Multiple, independent, PRE-EXISTING test files each carry their
own fixture that calls `run_snapshot_build_and_record` against the SAME real, shared
`CONFIG.dataset_dir` corpus (`test_micro_join.py:58`, `test_micro_snapshots.py:487`,
`test_scout.py`, `test_scout_ledger.py` — none of these fixtures are new or touched this round).
The hypothesis is that the first time all of these independently notice the corpus is stale (a
one-time event, since nothing has changed `micro_observer.py`'s source in any run before this one
per every prior iteration's handoff), their rebuilds can race over the same shared files. A direct
check of the real corpus's current on-disk state after these runs found all 18 real snapshots
already fresh and mutually consistent (`built_utc` clustered within ~100ms of each other), and
re-running `test_tc4_real_corpus_join_playbook_signal_is_unaffected_by_the_accessor_re_point` in
isolation 3 times in a row passed 3/3 — consistent with, but not full proof of, a one-time
transient settling now over. `test_tc12_real_corpus_identity_re_verifies_on_a_second_read` was not
independently re-isolated before the authoritative clean full-suite run (performed independently,
described above) reported 0 failures, which supersedes and resolves the question for this round.
**If either test fails again in a future run with the real corpus already settled, that would be
new evidence against this hypothesis and should be investigated fresh, not assumed away.**

## Pre-handoff verification

- **Service startup**: `bash scripts/dev.sh` — backend `:8301` and frontend `:3301`, both came up
  clean (`GET /health` -> 200, `GET /` -> 200 on both). Stopped both via `lsof`/`fuser` on both
  ports (matching `dev.sh`'s own cleanup technique) plus a `pkill` sweep for `uvicorn`/`next dev`
  child processes; re-checked both ports fully released before finishing.
- **External integrations**: none added this iteration — no new adapter/vendor call; the one
  production edit is a pure timestamp-stamping correction inside the existing observer, no new I/O.
- **Native dependency binaries**: none added.
- **Real-store hygiene**: every NEW proof this iteration adds (the mutation-proof tests, the
  manual Scout reachability script) runs against a `tmp_path`-scoped or
  `tempfile.TemporaryDirectory()`-scoped fixture store — none of this round's own additions ever
  touch the real `.data` store. Running the pre-existing full suite DOES legitimately rebuild the
  real snapshot corpus's cached files this round specifically (see the transient-failure
  investigation above) — that is pre-existing, already-shipped test behavior this round did not
  add or change, and the correct, designed response to a genuine `micro_observer.py` source edit;
  the real corpus's underlying recorded datasets (the append-only, checksummed source-of-truth
  files) are never written to, only the derived, rebuildable snapshot cache.

## Known Issues

- **The full backend suite passed clean at 3245/3237/8/0 (see "Tests Run" above), but getting
  there took two earlier runs that each showed the same 2 failures in `test_micro_join.py`/
  `test_micro_snapshots.py`'s "real corpus" tests, investigated and written up above.** The
  authoritative clean run resolves the question for THIS round, but the underlying condition —
  several independent, pre-existing test fixtures each rebuilding the SAME real, shared snapshot
  corpus whenever `micro_observer.py`'s source changes — is a genuine, real (if rare) source of
  test interference that predates this round and was simply never triggered before (every prior
  iteration's handoff records zero changes to `micro_observer.py`; this is the first). It is not
  something this round's scope authorizes fixing (no production edit to `micro_join.py`/
  `micro_snapshots.py`/`scout.py`/`scout_ledger.py` is in scope), but it is worth a future round
  flagging to the test-suite's own maintainers: multiple independent fixtures writing to one
  shared, real, mutable directory is fragile exactly when it is least convenient — the first run
  after a genuine source change.
- **Browser confirmation of the two frontend passengers (TC-13/TC-14: `MicroReadinessSection`
  testid in the "unavailable" state live; Scout table degrading gracefully on a real seeded
  malformed row in a live DOM) was not performed by this dev pass.** The DOM structure change and
  the optional-chaining fix are both `tsc`-clean and traced by hand against the exact JSX; the
  malformed-row shape is proven reachable through the real backend contract (Passenger 2 above).
  Per this pipeline's own division of labor (iteration 15's dev handoff makes the identical call
  for its own non-zero-fixture render), live browser confirmation against a seeded fixture-scoped
  rig is the QA/browser-qa lane's job, not reproduced here.
- **J-10's own kept-product sentinel (full browser pass over cockpit/`/structure`/every shipped
  `/desk` section) was not run by this dev pass** — it is J-10's own acceptance requirement,
  explicitly the downstream QA/browser-qa-agent's + independent auditor's job this round (this
  round's carried context: "the independent auditor runs after you").
- TR-23 and TR-24 remain open, explicitly deferred to round 17 per the evaluator's own two-way
  split — not attempted here, not a gap in this round's scope.
