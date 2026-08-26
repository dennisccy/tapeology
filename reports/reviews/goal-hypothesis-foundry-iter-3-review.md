**Verdict:** PASS

```yaml
phase: goal-hypothesis-foundry-iter-3
date: 2026-08-26
reviewer: reviewer
summary: |
  Ships the composite hermetic "complete factory" oracle suite (TC-1..TC-8, 9 tests in a new
  test_foundry_hermetic_epoch.py) driving the real compiler->interpreter->family->ledger->runner
  path with no mocks, plus the two carried repairs: foundry_runner's already-terminal fast path
  now re-verifies manifest_hash/econ_floor_bps (TC-9), and SourceRecord gains source_hash
  (sha256(source_excerpt), init=False) and alternatives (TC-10/TC-11). Every kill-type fixture is
  a traced translation of an already-proven test_scout.py fixture; assertions are exact-value
  (state, reason, hash order, disclosure n) not loose. Verified production wiring by direct read
  (foundry_ledger row schema, scout.screen_candidate return shape, EVIDENCE_CLASS constant) and by
  running the full backend suite locally (exit 0; targeted -v run of the four touched Foundry test
  files: 57/57 passed). No anti-goal violation found: scout.py untouched (only monkeypatched inside
  a scoped monkeypatch.context()), no second decision rail, evidence_class fixed to the real
  historical_exposed_diagnostic constant, docs/hypothesis-foundry/ real-epoch artifacts absent.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues: []
standards:
  state_transitions_server_side: pass
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  architecture_principles: pass
```
