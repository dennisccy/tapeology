**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-referee-iter-7
date: 2026-08-15
reviewer: reviewer
summary: |
  Ships referee_adjudicate.py (J-06): estimand A/B/C pooling, evaluation as a recorded operator
  act, the append-only checkpoint + family BH fold, the read-side adjudication fold, and
  authorize_promotion, plus the 3 riders. Verified against docs/referee-statistical-spec.md and
  referee_stats.py directly: pooling/weighting, floor/eligibility gating, fragility triggers,
  attestation re-verification at fold time, and checkpoint immutability all match spec. TC-14/
  TC-17's BH-boundary math is independently hand-verified and correct. Full backend suite reran
  clean: 2642 collected / 2634 passed / 8 skipped / 0 failed (exceeds iter-6's 2595/2587/8
  baseline), config_fingerprint 08e471b10130e1e2 unchanged, MCP EXPECTED_TOOLS still 20 — all
  independently confirmed, not just taken from the dev handoff. Riders 1-3 correctly implemented
  and cross-reference the actual iter-6 audit findings (B4/B5/T1) accurately.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues:
  - severity: MINOR
    file: runs/goal-session-referee/state/blueprint.md
    line: 149
    category: standards
    summary: >-
      Rider 2 adds a 5th `integrity_errors` key to `GET /research/desk/referee/registry`'s
      response, but blueprint.md's "iter-6 note" Data Contract block still documents the old
      4-key shape (grep confirms zero `integrity_errors` mentions in the file, and it is absent
      from `git status`'s changed-file list) — directly contradicting the dev handoff's explicit
      claim that "the four-key GET shape pinned in state/blueprint.md is now five keys — updated
      as part of this fix."
    fix: Add `integrity_errors: [...]` to the GET /registry response shape documented in blueprint.md's registry note, or correct the handoff prose if this was intentionally deferred.
  - severity: NOTE
    file: apps/backend/app/research/referee_adjudicate.py
    line: 990
    category: code-quality
    summary: A BandMapResolver is constructed for estimand "C" (`if estimand in ("B", "C")`) but only estimand B's pooling path ever reads it — C routes through `_pool_against_null`, which takes no resolver.
    fix: 'Narrow the condition to `estimand == "B"` (harmless as-is: compute=False, no side effects).'
standards:
  state_transitions_server_side: pass
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: n/a
  architecture_principles: pass
```
