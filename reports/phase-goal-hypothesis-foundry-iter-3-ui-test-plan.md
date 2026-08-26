# Phase goal-hypothesis-foundry-iter-3 — UI Test Plan

**Status:** N/A — Backend-only phase. No UI tests required.

**Phase:** goal-hypothesis-foundry-iter-3
**Date:** 2026-08-26
**Written by:** ui-test-designer

## Basis

- `docs/phases/goal-hypothesis-foundry-iter-3.md` metadata: `**Frontend Present:** no`; its own
  `### Frontend` in-scope section reads "None."
- `runs/goal-hypothesis-foundry-iter-3/plan.md`: `## Frontend Present: no`; `frontend-ux: no` in
  Agents Required.
- `reports/phase-goal-hypothesis-foundry-iter-3-user-visible-changes.md`: "Status: N/A —
  Backend-only phase (Frontend Present: no)."
- `reports/phase-goal-hypothesis-foundry-iter-3-ui-surface-map.md`: "Status: N/A — Backend-only
  phase (Frontend Present: no)"; frontend surfaces changed: 0.

This iteration's substance (a hermetic oracle test suite proving the five `foundry_*.py` modules
together end-to-end, plus two internal data-integrity repairs — a resume-identity re-verification
check on `foundry_runner.py` and two new `SourceRecord` dataclass fields) is exercised only by the
pytest suite (`apps/backend/tests/test_foundry_hermetic_epoch.py` and related test files). None of
it is served through `GET /research/desk/micro/foundry` or any other route, and no UI route,
component, or served response shape changed. All Foundry UI stays deferred to the Binding
Execution Order step-5 consolidated read-surface iteration.

The only relevant browser check this iteration is a pure regression replay of the existing J-01
golden script (`runs/goal-session-hypothesis-foundry/journey-scripts/J-01.json`) against
already-shipped UI — that is functional/journey QA territory (TC-13 in the phase spec), not new
UI test-case design, since no new surface or interaction exists to design cases against.

No UI test cases are produced for this phase.
