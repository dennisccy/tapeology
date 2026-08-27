# Phase goal-hypothesis-foundry-iter-7 — User-Visible Changes

**Status:** N/A — Backend-only phase (Frontend Present: no)

No user-visible changes. All changes are internal backend implementation.

## Verification note

Confirmed against the actual diff (not just plan.md's declaration):
- `apps/backend/app/research/micro_routes.py` — the inline `_FOUNDRY_FROZEN_READY_TOTAL` expression
  (previously ~line 901) was extracted into a new named function `compute_frozen_ready_total()`,
  still called once at module import time. The formula is byte-identical
  (`sum(f["variant_count"] for f in epoch_manifest_view.get("families", []))`); only its location
  changed. Served value of `GET /research/desk/micro/foundry`'s `exhaust_progress.frozen_ready_total`
  field is unchanged (`0`), verified live against `:8301` per the dev handoff.
- `apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py` — one new equivalence-pinning
  unit test added (`test_frozen_ready_total_sealed_cli_formula_agrees_with_the_canonical_helper`).
  Test-only file; no UI coupling.
- `git status` confirms zero files under `apps/frontend/**` were touched.

Since the rendered `/desk` → Hypothesis Foundry → Runner/Checkpoint subsection already displays
`frozen_ready_total` verbatim from this same endpoint (built in a prior iteration), and the served
value is provably unchanged, there is nothing new, removed, or differently-behaving for a user to
observe in this iteration.
