# Phase goal-hypothesis-foundry-iter-3 — What to Click

**Status:** N/A — Backend-only phase. No UI verification steps.

**Phase:** goal-hypothesis-foundry-iter-3
**Date:** 2026-08-26
**Written by:** ui-test-designer

## Basis

- `docs/phases/goal-hypothesis-foundry-iter-3.md`: `**Frontend Present:** no`; "New user-facing
  capability: None"; "New user actions: None"; "UI surface changes: None"; "Product surface delta:
  None visible to the operator this iteration."
- `runs/goal-hypothesis-foundry-iter-3/plan.md`: `## Frontend Present: no`.
- `reports/phase-goal-hypothesis-foundry-iter-3-user-visible-changes.md`: "There is no new screen
  or button for an operator to click, and nothing new is shown on `/desk` this iteration."
- `reports/phase-goal-hypothesis-foundry-iter-3-ui-surface-map.md`: navigation changes: no; the
  existing `/desk` "Hypothesis Foundry" panel and its `GET /research/desk/micro/foundry` endpoint
  are unchanged this iteration (byte-identical served response shape).

There is nothing new for an operator to click, load, or observe in the browser this iteration. The
work is a hermetic backend test suite (composite/all-blocked/all-killed/multi-survivor/
checkpoint-resume/protected-data-trip fixture epochs run through the real
compiler → interpreter → family → freeze/ledger → runner pipeline) plus two internal integrity
repairs, none of which is reachable from any UI route or served endpoint. All Foundry UI remains
deferred to a future consolidated read-surface iteration.

No operator verification guide is produced for this phase.
