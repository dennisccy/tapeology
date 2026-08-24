# goal-rapid-microscope-iter-29 Execution Plan

## What to Build

This is a **re-verification-only** iteration — no production code, no new journey, no UI change.
The single job is to move J-07 "Graduation" off its stale iteration-24 stamp by actually running
its own acceptance suite through this iteration's dispatched pipeline (not citing the owner's
out-of-band manual maintenance report), and to independently confirm that report's own claims
rather than inherit them.

- Execute `apps/backend/tests/test_micro_graduation.py` (J-07's own acceptance suite, confirmed
  present and unchanged — TC-1 through TC-15) via the dispatched pipeline; record the exact pass
  count and wall-clock time in the dev handoff (TC-1).
- Independently re-derive — via a fresh `git diff`, not by citing
  `reports/qa/goal-rapid-microscope-maint-2026-08-24-verification.md` — that commits `f08f46ee`
  and `f2b292f4` changed zero files under `apps/backend/app/` and `apps/frontend/` relative to the
  iteration-28 snapshot SHA `d397ad4bdfcd3850870dfbb1ab7ad7a0c48273c6` (TC-3).
- Run the full backend suite (`cd apps/backend && PYTHONPATH=. .venv/bin/pytest tests/`, project's
  documented command — do not add a redundant `-q`, it suppresses the summary line per the iter-28
  handoff's own note) end to end once; record exit code, pass/skip/fail counts (expect ≥ 3,491
  passed / 8 skipped / 0 failed), and total wall-clock time (expect well inside budget, ~6-7 min)
  (TC-4).
- Before and after that full-suite run, record mtime + sha256 of the two live operator cache files
  (`apps/backend/.data/dataset_index.db`, `apps/backend/.data/micro_readiness_cache.db`) and
  confirm byte-identical — this exercises `test_real_corpus_cache_scope.py` as a live behavioral
  check, not just a passing-test citation (TC-7).
- Re-hash the six `referee_*.py` files (`referee_adjudicate.py`, `referee_evidence.py`,
  `referee_null.py`, `referee_registry.py`, `referee_routes.py`, `referee_stats.py`) against the
  era's iteration-0 frozen sha256 listing recorded in
  `docs/handoffs/goal-rapid-microscope-iter-0-dev.md` (TC-6).
- Run the deterministic replay harness (`demo_runner.py --mode verify`) against every stored
  golden script J-01 through J-10 excluding J-07 (`runs/goal-session-rapid-microscope/journey-
  scripts/J-01.json` .. `J-10.json`); every one must report PASS with zero diff (TC-5). J-07 has no
  stored golden (no screen, per an earlier binding ruling) — its own pytest suite is its
  acceptance mechanism this iteration, per the routed lesson.
- Write the dev handoff at `docs/handoffs/goal-rapid-microscope-iter-29-dev.md` capturing all of
  the above evidence (pass counts, timings, diff output, hash comparisons).

**No production code change is anticipated anywhere in `apps/backend/app/**` or
`apps/frontend/**`.** If the developer agent finds itself editing either tree, stop and flag —
that is out of this iteration's scope per the spec's explicit "no production code change
anticipated" line.

## Agents Required

- backend-data: yes — run/record `test_micro_graduation.py`, the full backend suite, the
  `git diff` re-derivation, the referee sha256 re-check, and the live-cache byte-identity check;
  write the dev handoff.
- frontend-ux: no — J-07 has no screen; no frontend file is expected to change; no browser
  acceptance is required for the target journey.

## Frontend Present: no

## Files to Create/Modify

- `docs/handoffs/goal-rapid-microscope-iter-29-dev.md` — new dev handoff recording TC-1..TC-7
  evidence (pass counts, timings, diff output, hash listings, live-cache byte-identity proof).
- No other file under `apps/backend/app/**` or `apps/frontend/**` is expected to change. (Test
  files, cache DBs, and other repo trees are not modified by this iteration — this is a read/run/
  record round, not an editing round.)

## Key Test Scenarios

- TC-1: `pytest apps/backend/tests/test_micro_graduation.py -v` — all tests PASS, 0 failed; pass
  count and wall-clock time recorded in the iter-29 dev handoff. This is the mechanism that moves
  J-07's stamp off iteration-24.
- TC-2 (evaluator-owned): given TC-1 lands green this iteration, the evaluator records J-07 with a
  fresh `last_passing=goal-rapid-microscope-iter-29` and clears the DEFERRED-BUDGET flag — not this
  plan's job to edit journey-history directly, but the dev/review/QA evidence must make this
  unambiguous.
- TC-3: `git diff d397ad4bdfcd3850870dfbb1ab7ad7a0c48273c6..HEAD -- apps/backend/app apps/frontend`
  produces empty output — zero production/frontend code changed since iteration 28. Must be run
  fresh this iteration, not cited from the owner's report.
- TC-4: `pytest apps/backend/tests/` end to end exits 0, 0 failed, pass count ≥ 3,491, completes
  well inside budget.
- TC-5: `demo_runner.py --mode verify` against every stored golden (J-01..J-10 excluding J-07)
  reports PASS with zero diff.
- TC-6: the six `referee_*.py` files re-hash byte-identical to the iteration-0 frozen sha256
  listing.
- TC-7: `apps/backend/.data/dataset_index.db` and `apps/backend/.data/micro_readiness_cache.db`
  have identical mtime and sha256 before and after the full-suite run (no test wrote to the live
  cache path).

## Out of Scope (per spec, do not re-plan)

- The three dev-chain framework findings (QA lane certifying unchecked work; closure gate never
  reading the browser lane's verdict; replay harness unable to run a round's own target goldens) —
  these live in `agents/**`/`scripts/automation/**`, outside a product round's authority per
  `.claude/maintenance-protocol.md` §1.
- The two owner-deferred items: chain-ledger identity (iter-13) and the sealed judge's money floor
  (iter-18).
- Any change to `micro_graduation.py`, `micro_sealed_evaluation.py`, `micro_accessor.py`, or any
  other `research/*` production module.
- Recording more real tape, revealing/assigning any sealed shard, running the three pilot studies
  against the real recorded corpus.
- Any new `Config` field or fingerprint movement (pin stays `08e471b10130e1e2`).
- Any UI/frontend change.

## Alignment Notes

- This iteration is a narrow, targeted re-verification round consistent with the goal's Success
  Criterion 1 ("nothing kept regresses... every `referee_*` module byte-identical to `main` at era
  open") and Criterion 8 (graduation provenance-complete, J-07's own domain) — it advances the era
  toward a clean GOAL_ACHIEVED state without adding scope, matching the priority rubric's
  "smallest spec wins ties."
- No drift from `docs/goal.md` detected. The spec's exclusions (three framework findings, two
  owner-deferred items) are correctly routed to human ownership and are not re-planned here.
- Host-guard caps remain in force for the full-suite run per the spec's carried-forward critical
  reminder; no override is authorized by this plan.
