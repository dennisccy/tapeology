**Verdict:** PASS

```yaml
phase: goal-referee-iter-4
date: 2026-08-14
reviewer: reviewer
summary: |
  Fixes the exact-enumeration p-value floor bug in permutation_test (direct complement
  accumulation + cross-session math.fsum, matching _t_statistic's own method), proven via
  TC-1 (hand-verified independently: p=2/7), a 3,000-case property test, and a paired oracle
  calibration case + anti-conservative mutant. Lead-1 stale_basis_dates disclosure and both
  reviewer-flagged test gaps (TC-7/TC-8) are correctly implemented, additive-only. Full suite
  independently re-run: 2504 pass/8 skip/0 fail (JUnit XML), matching the handoff; fingerprint
  08e471b10130e1e2, EXPECTED_TOOLS=20, and zero diff to every named frozen file all confirmed.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues: []
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  architecture_principles: pass
```
