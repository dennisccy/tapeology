**Verdict:** PASS

```yaml
phase: goal-desk-iter-19
date: 2026-07-29
reviewer: reviewer
summary: |
  One-key selection-rule fix: _select_opposite_band now uses its own local distance-first
  tie-break tuple (distance_bps asc, class rank desc via _CLASS_RANK, quality_score desc)
  instead of delegating to _select_best_band's class-first tuple, matching goal.md J-14 step 1
  verbatim. Verified _select_best_band and _row_rank_key are byte-unchanged (diff packet shows
  only the two hunks in desk_screen.py touching the new key() closure + docstrings). TC-1 test
  correctly flipped; all other opposite-band tests confirmed unmodified since their fixtures
  each carry exactly one opposite-side band per symbol, so the two rules cannot diverge there.
  Independently re-ran the full backend suite: 1456 tests, 0 failed, 0 errors, 8 skipped;
  fingerprint 08e471b10130e1e2 unchanged; git diff --stat against all nine named frozen paths
  (tradability.py, levels.py, bars.py, bar_index.py, StructureChart.tsx, desk_coverage.py,
  config.py, desk/page.tsx, lib/types.ts) confirmed empty.
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
