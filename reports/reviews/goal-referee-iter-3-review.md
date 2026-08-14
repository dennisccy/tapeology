**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-referee-iter-3
date: 2026-08-14
reviewer: reviewer
summary: |
  Ships referee_stats.py (seeded streams, occurrence/cluster percentile bootstrap CIs, the
  primary within-session permutation test, sign-flip/equal-weight robustness disclosures,
  BH+BY, a fail-closed oracle attestation) plus the 6-case + mutation-fixture oracle suite and
  both carried-rider tests, matching docs/referee-statistical-spec.md Sec1/Sec3/Sec5/Sec6
  verbatim. Note: the diff packet only shows 3 tracked-file edits; the primary deliverable
  (referee_stats.py, test_referee_oracles.py, test_referee_stats.py) was untracked/new and
  read directly since git diff HEAD omits unstaged new files. Independently re-ran: oracle
  suite 9/9 passed in 78.1s (budget 120s), full backend suite 2495 pass/8 skip/0 fail/0 error
  (matches dev report exactly), config_fingerprint 08e471b10130e1e2 and MCP 20-tool count both
  reconfirmed by direct execution. Hand-verified math: the A/C-vs-B weight-form equivalence,
  BH k*/BY formulas, TC-4/TC-7 hand derivations, enumeration-branch correctness, and the
  n1==1 seeded fast path (proven byte-identical to the general Fisher-Yates loop).
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues:
  - severity: MINOR
    file: apps/backend/app/research/referee_stats.py
    line: 164
    category: code-quality
    summary: "_draw_indices_without_replacement is dead code: defined but never invoked by any production path or any test. permutation_test's own without-replacement draws are hand-inlined separately (a documented perf choice), never routed through this helper."
    fix: remove the unused function, or if it is meant as a primitive for J-04's future anchor draws, add a direct unit test exercising it now.
  - severity: MINOR
    file: apps/backend/app/research/referee_stats.py
    line: 456
    category: tests
    summary: "permutation_test's seeded-draw fast path has an untested branch: elif n2 == 1 (a session with >1 occurrences and exactly 1 matched anchor -- a realistic future shape per spec Sec4.1's anchor-shortfall disclosure). No fixture in either test file constructs n1>1 with n2==1, so this branch has zero automated coverage. I independently re-derived it and confirmed it is mathematically correct (uniform choice of the single excluded index == uniform choice of the n-1-sized complement), but it ships unverified by the suite in code explicitly built for high-blast-radius reuse."
    fix: add a fixture to test_referee_stats.py with n1>1, n2==1 asserting the fast path matches a from-scratch general-algorithm reference, before J-04 starts feeding real anchor-shortfall data through it.
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: fail
  no_hardcoded_localhost: n/a
  architecture_principles: pass
```
