# Iteration 7 — Coherence Audit

**Iteration:** goal-hypothesis-foundry-iter-7
**Date:** 2026-08-27
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

---

## Reading applied (per the pump's explicit request to state this plainly)

Two readings were available for `exhaust_progress.frozen_ready_total`:

- **Strict/mechanical reading:** "no second computation of this value may exist anywhere in the
  repository, ever." Under this reading the row is unfixable by policy — the sealed
  `run_hypothesis_foundry_real_exhaust.py:225` still contains an independent formula and cannot be
  edited (it is entry 46/59 of the byte-identical `docs/hypothesis-foundry/freeze-set.json`,
  reverified: `git diff <snapshot> -- apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py`
  is empty). A gate that can never be satisfied once tripped is not a gate, it's a permanent veto,
  and the skill I follow is explicit that the FAIL bar is meant to be narrow and objective, not a
  source of infinite loops.
- **Applied reading (this audit):** the Data Contract check asks whether *this iteration's diff*
  introduces a *new* duplicate computation, or whether ownership within the code the diff is
  legally free to change has been genuinely consolidated to one canonical function, with any
  legally-frozen residual disclosed and permanently pinned against future drift. I apply this
  reading because (a) my own agent instructions phrase the check as "any **new** function... that
  computes that value independently" — the sealed CLI's formula is not new, it was already found
  and FAILED at iter-6; (b) the CLI is an operator-run offline script, not one of the app's
  REST/UI/MCP product surfaces the Data Contract governs (`GET /research/desk/micro/foundry` is);
  and (c) the manifest this value is computed over (`docs/hypothesis-foundry/epoch-manifest.json`,
  `families: []`) is itself sealed and the era's anti-goals forbid a second real generation epoch —
  so the two formulas cannot practically diverge for the life of this frozen epoch, even though the
  auditor's own report correctly shows they are not structurally equivalent in the abstract.

Under the applied reading, this iteration's diff introduces **no new** duplicate computation and
does the maximum legally available consolidation. I record the residual as an advisory WARN, not a
FAIL, per the below.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `exhaust_progress.frozen_ready_total` | OK (consolidated; residual advisory) | `apps/backend/app/research/micro_routes.py:901-923` — sole non-sealed definition (`compute_frozen_ready_total`), called once at module scope, consumed by `read_exhaust_progress` (`foundry_runner.py:229/262/276/282`) which takes it as a parameter and never re-derives it. Repo-wide grep for `frozen_ready_total` outside `apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py` (sealed) finds no other independent computation; `apps/frontend/app/desk/page.tsx:7869/7889/7895` only renders the value verbatim. |
| `exhaust_progress.frozen_ready_total` (residual) | ADVISORY — see notes | `apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py:225,268,274,297` — pre-existing (iter-6), unedited this iteration (diff empty), sealed by `freeze-set.json`; still independently computes and logs the value to its own stdout when an operator runs the CLI directly (not a REST/UI/MCP surface). |
| Other `exhaust_progress` sub-fields (`terminal_count`, `checkpoint_ordinal`, `exhaust_complete`) | OK, unchanged this iteration | `foundry_runner.py:271-282` unchanged; not touched by this diff; carried structurally-analogous two-computing-site pattern already flagged in `docs/handoffs/goal-hypothesis-foundry-iter-7-audit.md` finding B3 as non-blocking/deferred, out of this iteration's scope per spec |
| No other Data Contract row touched | OK | Diff is exactly 2 files (`micro_routes.py`, `test_run_hypothesis_foundry_real_exhaust.py`), +60/-1; `git diff <snapshot> --stat -- apps/ docs/` confirms nothing else changed |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| No new page/route/feature this iteration ("Frontend Present: no"; blueprint note: "no IA/nav change") | OK — not applicable | `apps/frontend/**` has zero diff lines against the snapshot SHA; `/desk` → Hypothesis Foundry → Runner/Checkpoint remains the sole, already-registered home for this row; nothing new to place |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Residual duplicate is real and permanent, not a new defect.** `run_hypothesis_foundry_real_exhaust.py:225` still independently computes `frozen_ready_total` and prints it to stdout (`:297`) when the sealed CLI is run directly. It cannot be removed or redirected without breaking the era's first-read lock. This is disclosed plainly in `docs/handoffs/goal-hypothesis-foundry-iter-7-dev.md` ("Coherence-Auditor Outcome"), in `state/blueprint.md`'s split `exhaust_progress.frozen_ready_total` row, and in the audit report (`docs/handoffs/goal-hypothesis-foundry-iter-7-audit.md`, B2). Recommend the era's closing record carry this as a permanently-accepted, test-pinned exception rather than something a future iteration should keep trying to "fully" resolve — there is no more legal to give.
- **The equivalence-pinning test is documentary, not a general drift detector.** The post-dev audit (B1, appended to the dev handoff as "AUDITOR NOTE") correctly shows `compute_frozen_ready_total` (`f["variant_count"]`, hard subscript) and the sealed CLI's formula (`len(fm.get("variants", []))`, tolerant `.get`) are not equivalent for a non-empty `families` list — the test only reads `0 == 0` because the frozen manifest's `families` is permanently `[]`. What actually prevents divergence is that both the manifest and the CLI are sha256-pinned freeze-set entries, not the test's assertion logic. This nuance is already correctly recorded in the dev handoff and audit report; no further action needed, but future eras should not describe this pattern as "the test guards against drift" without that caveat.
- **Structurally analogous unregistered risk (B3, out of scope this iteration).** `exhaust_complete` and `terminal_count`/`checkpoint_ordinal` have the same two-computing-site shape (`foundry_runner.py` vs. the sealed CLI) as the row this iteration fixed. The spec explicitly deferred these as non-blocking; flagging here only so the era's closing record doesn't lose track of it if a future consolidation pass is ever authorized.

## Summary

This iteration's diff (`apps/backend/app/research/micro_routes.py`, `apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py`) introduces no new duplicate computation, no non-canonical serving path, and no IA/navigation change. It consolidates `exhaust_progress.frozen_ready_total` to a single named owner within the entire non-sealed codebase and permanently pins the sealed CLI's transcribed formula against it, verified via `git diff <snapshot-sha> -- apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py` returning empty (seal intact) and a repo-wide grep finding no other non-sealed computation. Iter-6's `COHERENCE-FAIL` on this row is retired. The one remaining structural fact — a legally-frozen, disclosed, pinned duplicate inside a sealed operator CLI that is not a product surface — is recorded as an advisory WARN, not a blocking FAIL, under the reading explained above. `GOAL_ACHIEVED` is not blocked by this verdict.
