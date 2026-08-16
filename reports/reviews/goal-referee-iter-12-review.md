**Verdict:** PASS

```yaml
phase: goal-referee-iter-12
date: 2026-08-16
reviewer: reviewer
summary: |
  Adds a corpus-honest accrual_basis block plus two per-candidate recorded-session fields
  to shortlist_response(), rendered beside (never replacing) the shipped calendar-day pair
  on /desk's Referee Registry section. Independently verified rather than trusting the
  handoff: accrual_rate_sessions_per_day/projected_days_to_target are computed by an
  unmodified code path (confirmed by direct source read + passing golden TC-6 test);
  n_sessions is reused verbatim (no fresh/differently-filtered recomputation) for both the
  S-1..S-3 and S-4..S-6 branches; pooled_sessions_at_current_basis matches
  playbook_occurrence_readiness()'s actual distinct_sessions/stale_basis_dates semantics.
  Ran full backend suite live (2695 collected, 0 failures/errors, 8 skipped, matches
  handoff); tsc --noEmit clean; Config().config_fingerprint() independently reproduced as
  08e471b10130e1e2; git diff on the five frozen files is empty; guard regex independently
  exercised against seeded violations and clean pass-throughs, both correct. Diff is
  tightly scoped (+73/-1 backend, +45/-0 frontend, -1 is a docstring extension not a logic
  deletion); zero new Config/referee_parameters entries (golden-hash pinned); docs/goal.md
  edit confined to the AUTO:journeys marker block. git status --porcelain shows only known
  harness/pipeline artifacts untracked, nothing unexpected.
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
