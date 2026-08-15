**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-referee-iter-9
date: 2026-08-15
reviewer: reviewer
summary: |
  Wires authorize_promotion into pnl_scan._promote/run_sweep BEFORE append_validation_row (fail
  closed, certificate_store now a required kwarg, no bypass token found in source or on the
  scan's own logic). Adds the strategy-family Sec3.7 pooling branch (verified byte-identical
  shape to _pool_against_null, zero new referee_stats.py code) and the certificate's real mint
  site, gated on evidence_family=="strategy" + fresh checkpoint + re-verified attestation. Riders
  (accrual/discovery context fix, S-6 short-side candidate, family_id/family_q backend-owned
  field, UI guard extension) all verified present and correctly wired. Full backend suite
  re-run: 2678 collected, 0 failed, 8 skipped (>= 2657 floor); fingerprint confirmed
  08e471b10130e1e2; frontend tsc --noEmit clean.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues:
  - severity: MINOR
    file: apps/backend/tests/test_referee_registry.py
    line: 874
    category: tests
    summary: duplicate assertion — line 874 is byte-identical to line 872 (both assert S-5's readiness), an apparent copy-paste leftover from adding the S-6 line between them
    fix: delete the redundant line 874
  - severity: MINOR
    file: apps/backend/tests/test_pnl_scan.py
    line: 1239
    category: tests
    summary: test_no_bypass_guard_can_fail_on_a_seeded_violation checks a substring in a hand-typed string rather than exercising the real banned_tokens/file-scan loop, so it would not catch a future regression that silently guts the actual scan
    fix: seed the violation into a temp file and run the SAME scan logic the primary guard test uses (or factor the scan into a helper both tests call)
  - severity: NOTE
    file: apps/backend/app/research/referee_adjudicate.py
    line: 521
    category: backend
    summary: _pool_strategy_trades/strategy_observations pools every recorded backtest trade unconditionally, unfiltered by strategy_id/profile — a certificate's evidence isn't scoped to the specific candidate named in certificate_mint. Honestly logged as T-1 in state/assumptions.md and confirmed unreachable from any production route this era (grepped every run_evaluation_and_record call site — none supply journal_store/certificate_mint)
    fix: revisit before wiring journal_store/certificate_mint into the /evaluate route in a future era
standards:
  state_transitions_server_side: pass
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: pass
  architecture_principles: pass
```
