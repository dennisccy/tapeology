**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-desk-iter-26
date: 2026-07-30
reviewer: reviewer
summary: |
  J-17's per-pair window derivation (_pair_window: tail vs full_lookback vs nothing-frozen), the
  new "unchanged" 409 classification, the four additive per-pair Data-Contract fields, and the
  /desk disclosure lines (counts + tail-vs-lookback line + per-failed-pair requested_window +
  legacy-run honest fallback) are implemented correctly and match goal.md's three window cases,
  TC-1..TC-8. This is a re-review after a prior FAIL: the dev applied exactly the fix_task from
  that review (extended, not weakened, the one blocking assertion to the 8-key schema, documented
  as a carve-out per the fix_task's own accepted alternative) and the full backend suite is now
  green (independently re-run here: exit 0, zero failures). Zero-diff constraints re-verified
  empty for bars.py/bar_index.py/desk_coverage.py/desk_screen.py/tradability.py/levels.py/
  StructureChart.tsx/PriceChart.tsx/config.py/desk_topup_log.py; fingerprint unchanged
  (08e471b10130e1e2); the 409 raised for BarSeriesAlreadyRegistered is the sole 409 in
  record_bar_series's path, so the unchanged-vs-failed classification cannot misfire on an
  unrelated conflict.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues:
  - severity: NOTE
    file: apps/backend/app/research/desk_topup_compute.py
    line: 172
    category: code-quality
    summary: run_topup calls _pair_window twice per pair (provenance capture, then again inside _run_one_pair) — one extra merged_bars read per pair.
    fix: optional — dev declined intentionally to avoid changing _run_one_pair's monkeypatched signature; leave as is unless profiling shows it matters.
  - severity: NOTE
    file: apps/backend/tests/test_desk_topup_compute.py
    line: 1092
    category: spec
    summary: the carve-out to the "existing assertions pass unmodified" rule is recorded by the dev as "awaiting ratification" rather than pre-approved; this review ratifies it (it is the documented-carve-out alternative my own prior fix_task named, the assertion was extended not relaxed, and the full suite is green).
    fix: none required from dev; if product/spec ownership wants to record this formally elsewhere (e.g. amend goal.md's OUT-OF-SCOPE text), that is a process follow-up, not a code fix.
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  architecture_principles: pass
```
