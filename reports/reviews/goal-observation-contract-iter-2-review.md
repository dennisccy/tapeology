**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-observation-contract-iter-2
date: 2026-09-03
reviewer: reviewer
summary: |
  WatchManager's per-ticker atomic settled pair (_settle) and get_observation_source(ticker)
  are implemented exactly per the IN SCOPE list, threaded through all five feeder paths and
  pause()/resume(). The new test_tape_observation_time.py (33 tests incl. every required
  test_counterexample_* pair) passes 33/33; guard-list files, the fingerprint (08e471b10130e1e2)
  and tsc --noEmit (0 errors) all independently re-verified green; observation_contract.py,
  main.py, app/engine/, config.py and every frontend file are untouched. Documented cold-reset
  design decision is sound and tested. One MINOR gap found via direct reproduction: _settle
  writes keyed only by ticker string with no identity check against the currently-registered
  engine, so a stale feeder's deferred cancellation cleanup can transiently clobber a freshly
  re-watched ticker's settled pair during a live switch — not exercised by the shipped tests
  (which use the sync no-task harness) and currently inert (no route reads
  get_observation_source yet), but must be hardened before iteration 5 wires it to a route.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues:
  - severity: MINOR
    file: apps/backend/app/watch_manager.py
    line: 341
    category: backend
    summary: "_settle(engine, ...) derives the dict key from engine.snapshot().ticker with no check that `engine` is still self._engines.get(ticker); on a live switch (watch_with_provider/_progressive_historical/_async_provider, which call stop() then immediately create a fresh engine+task), the OLD task's deferred CancelledError-branch settle call can write into the SAME ticker key after the fresh cold-reset, using the old engine's stale snapshot. Reproduced directly: in a real async run it does fire (traced), and self-heals only because the new engine's own first waiting-flip settle happens to run immediately after in the same loop turn — an ordering the code does not guarantee. No current caller is affected (get_observation_source has zero production readers this iteration) and TC-1..TC-4's interleaving tests only use the synchronous no-task harness, so this path is untested."
    fix: "Guard the write with an identity check, e.g. `if self._engines.get(ticker) is engine: self._settled[ticker] = (...)` inside _settle, mirroring the existing no-fabricated-engine idiom; add a regression test that switches watch_with_async_provider on the same ticker while the old feeder task is genuinely running and asserts get_observation_source never returns the old engine's snapshot at any await point."
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  architecture_principles: pass
```
