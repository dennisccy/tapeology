# Iteration 19 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-19
**Date:** 2026-08-20
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Scope of this iteration's diff

Diffed `dfbf9340...` → working tree, noise-excluded, per the invocation prompt. Confirmed via
`git diff --stat -- apps/backend/app/ apps/frontend/` (empty output) that **zero files under either
production tree changed** relative to the snapshot SHA. The full changed-file set for this iteration
is:

- `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` — extended in place (adds a
  `_TAPEOLOGY_SCOPED_VARS` array reused by both the existing stderr echo and a new durable
  `reports/qa-scoped-backend-store-manifest.md` write). Dev/QA tooling, not a product module.
- `runs/goal-session-rapid-microscope/journey-scripts/J-02.json`, `J-03.json`, `J-04.json`,
  `J-05.json` — each gets a new step 2 (click an already-existing `desk-section-expand-*` control,
  assert an already-served literal string) and, for J-02/J-03/J-04, a corrected step-1 assertion
  text. Golden-replay fixtures, not product code.
- `apps/backend/tests/test_micro_deterministic_rerun.py` (new) — pytest module only.
- `runs/goal-session-rapid-microscope/state/blueprint.md` — one appended iter-19 documentation
  note (verified via diff: pure addition, no row edits).
- `docs/phases/goal-rapid-microscope-iter-19.md` — the iteration spec itself (new file).

(`docs/goal.md`, `docs/rapid-validation-spec.md`, `micro_accessor.py`, `micro_graduation.py`,
`micro_sealed_evaluation.py`, and their test files show as locally modified in `git status`, but
`git diff <snapshot-sha> -- <those paths>` returns empty — they were already at their current
content when the snapshot was captured, i.e. pre-existing uncommitted state from before this
iteration, not part of iter-19's diff. Out of scope for this audit.)

This matches the iter spec's own framing exactly: "no `.tsx` file changes," "no Data Contract or
Information Architecture change," test/harness-only.

## Data Contract check

The four deepened golden scripts assert literal strings that are all pre-existing, already-registered
Data Contract fields, read from their already-registered endpoints — no new fetch path, no
client-side recomputation:

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Per-shard `fallback_frac` ("Fallback frac" header) | OK — pre-existing, era-baseline readiness row, `GET /research/desk/micro/readiness` | `runs/.../journey-scripts/J-02.json` step 2 asserts text only; no fetch code touched |
| `joinable_corpus.withheld_excluded` ("Joinable corpus — withheld (excluded)") | OK — iter-10 Disclosure sub-fields row, same endpoint | `runs/.../journey-scripts/J-03.json` step 2 |
| Scout `chain_verification` ("Ledger chain verification:") | OK — era-baseline scout row, `GET /research/desk/micro/scout` | `runs/.../journey-scripts/J-04.json` step 2 |
| Walk-forward `chain_verification` ("Ledger chain verification:") | OK — era-baseline walkforward row, `GET /research/desk/micro/walkforward` | `runs/.../journey-scripts/J-05.json` step 2 |

The new `test_micro_deterministic_rerun.py` module calls only the already-registered canonical
functions to prove rerun-determinism — `ms.build_snapshot_rows` / `ms.run_snapshot_build_and_record`
(`apps/backend/tests/test_micro_deterministic_rerun.py:193,212`), `scout.screen_candidate` /
`scout.register_and_screen_candidate` (`:235,314`), `wf.evaluate_mode_b_fold`
(`:162`/`_evaluate_mode_b_in_a_fresh_ledger`). It introduces no second implementation of any
registered value — it is a test harness asserting the canonical modules' own determinism, not a
parallel computation path. No new displayed value is introduced.

The QA-launcher's new `reports/qa-scoped-backend-store-manifest.md` write is a dev-tooling artifact
(which env vars a QA launch bound to), not a value served to any product client — matches the
blueprint's own "internal tooling, not a served product value" framing (`state/blueprint.md` iter-19
note).

## Information Architecture check

Zero new pages, routes, or nav-visible features this iteration (confirmed: no `.tsx` diff at all).
The golden-script steps click only already-existing `desk-section-expand-microReadiness` /
`-scoutLedger` / `-walkForward` controls, already reachable via the established `/desk` nav skeleton.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new feature/route this iteration) | OK | n/a |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `runs/goal-session-rapid-microscope/state/golden-gaps` (a one-line harness state file recording
  "J-07" as the sole journey with no golden script, per the standing precedent that J-07's LLM lane
  covers it) was deleted in this iteration's working tree. It is pure engine bookkeeping, not part
  of the blueprint's IA or Data Contract, so it carries no coherence verdict weight — noting it only
  so the deletion doesn't go unremarked if it was unintentional.
- No unregistered-but-new values and no formatting drift observed — the iteration's own framing
  ("test/harness-only, zero product behavior change") is accurate against the diff.
