**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-tradable_wall-iter-5
date: 2026-07-14
reviewer: reviewer
summary: |
  Backend-only enabler pass, entirely inside app/research/setups.py + its two test files (git
  diff --stat confirms zero frozen-file touches). B1 additively discloses effective_reaction_horizon_bars
  + reaction_boundary_truncated with the exact spec'd boundary condition; verified by direct code
  trace and a purpose-built fixture that genuinely reaches the recency boundary. B3 memoizes
  compute_setups behind an id(config)+store-checksum-signature single-slot cache; traced routes.py
  and edge_report.py to confirm all three endpoints share one CONFIG singleton so the cache is
  genuinely cross-endpoint, matching the dev handoff's live-smoke evidence (276s cold vs 0.28-0.40s
  cached). Re-ran the full suite myself: dot-matrix shows exactly 1337 passed / 7 skipped / 0
  failed / 0 errors, matching the handoff's claim precisely. No scope creep.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues:
  - severity: MINOR
    file: apps/backend/app/research/setups.py
    line: 377
    category: backend
    summary: |
      compute_setups writes the cache as two separate, non-atomic dict-key assignments
      (_SCAN_CACHE["key"] = key then ["result"] = result). A concurrent reader landing in that gap
      sees the NEW key paired with the PREVIOUS (possibly None, on a cold process) result — a
      narrow torn-read Known Issue #3's "never a torn ... result" doesn't quite cover (it only
      analyzes the simultaneous-miss/redundant-recompute case). Low practical risk for this
      single-operator tool and self-heals next call, but the disclosure overclaims.
    fix: |
      Replace the two-key dict with a single atomic rebind (e.g. module-level
      `global _SCAN_CACHE; _SCAN_CACHE = (key, result)` — one name-store is atomic under the GIL),
      or wrap the read-check-write sequence in a threading.Lock.
  - severity: NOTE
    file: apps/backend/tests/test_setups.py
    line: 519
    category: tests
    summary: |
      Pre-existing "repeat scan determinism" tests (test_aapl_repeat_scan_determinism,
      test_repeat_scan_determinism, and the new test_boundary_regression_is_deterministic_across_repeat_scans)
      construct two BarStore instances over the same tmp_path while reusing one Config object, so
      B3 now serves the second call from cache (literally the same object) rather than truly
      re-scanning — diluting their original "two independent scans agree" intent. Coverage gap is
      closed elsewhere (test_cache_hit_is_byte_identical_to_a_fresh_uncached_scan calls
      _run_full_panel_scan directly), so this is observational only.
    fix: optional — note in a comment that these now exercise cache-consistency, not re-scan determinism.
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  ui_evolved_with_capability: n/a
  navigation_updated: n/a
  architecture_principles: pass
```
