**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-hypothesis-foundry-iter-2
date: 2026-08-26
reviewer: reviewer
summary: |
  Ships exactly the spec'd scope: the QA-rig visibility fix (real-artifact copy into the scoped
  rig, matching resolve_foundry_dir's derivation, never writing to .data/) plus five new hermetic
  modules (foundry_interpreter/family/freeze/ledger/runner) implementing the generic interpreter,
  Scout-boundary adapter, family denominator/cap, freeze-set/manifest/first-read-lock, and
  hash-chained ledger with checkpoint/resume/single-flight. No existing frozen science-rail file
  (scout.py, micro_features.py, foundry_compiler.py, etc.) was touched. Full backend suite reran
  green (3825 passed / 8 skipped, exit 0) and no real epoch artifact exists under
  docs/hypothesis-foundry/. Tests use tight, exact-value assertions (byte-identical screen dict
  comparison in TC-4, exact set/count checks elsewhere).
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues:
  - severity: MINOR
    file: apps/backend/app/research/foundry_runner.py
    line: 89
    category: backend
    summary: >-
      run_one_candidate's already-terminal fast path returns the cached row without any identity
      check, despite its own docstring claiming "verify identity and return the existing row" —
      a caller resuming with a different manifest_hash/econ_floor/anchors for the same
      candidate_spec_hash gets the stale terminal row silently, with no ConflictingReplayRefused
      or mismatch signal (unlike the intent-without-terminal branch, which does check econ_floor).
      No test in test_foundry_runner.py exercises this path with mismatched inputs, and it isn't
      listed in the dev handoff's Known Issues.
    fix: >-
      Either compare the caller-supplied manifest_hash (and ideally econ_floor) against the
      existing terminal row's pinned values before returning it, raising
      fl.ConflictingReplayRefused/FoundryResumeIdentityMismatch on drift, or soften the docstring
      to state plainly that only candidate_spec_hash identity is checked (no manifest/econ-floor
      verification on the already-terminal path) and add that to Known Issues so J-06/J-07 close
      it before a real epoch relies on it.
standards:
  state_transitions_server_side: pass
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  architecture_principles: pass
```
