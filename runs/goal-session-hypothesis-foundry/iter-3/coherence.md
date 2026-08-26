# Iteration 3 — Coherence Audit

**Iteration:** goal-hypothesis-foundry-iter-3
**Date:** 2026-08-27
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration (confirmed from diff + spec)

`git diff dd432557` (noise-excluded) touches only:
`apps/backend/app/research/foundry_runner.py`, `apps/backend/app/research/foundry_source_registry.py`,
three existing `test_foundry_*.py` files, one new test file
`apps/backend/tests/test_foundry_hermetic_epoch.py`, and one line added to
`docs/hypothesis-foundry-spec.md` §1.4. `git status` confirms zero `apps/frontend` changes and no new
route/endpoint file. The excluded-path `--stat` shows only harness bookkeeping (`runs/`, `reports/`,
`telemetry.jsonl`, `trace.jsonl`) plus `state/blueprint.md`'s own iter-3 note — no lockfile changed.
This matches the iter spec's "Frontend Present: no" / "New user-facing capability: None" / "Data-contract
additions: None" declarations, and `reports/phase-goal-hypothesis-foundry-iter-3-ui-surface-map.md`
independently confirms 0 frontend surfaces changed.

## Data Contract check

All five blueprint Data Contract rows this iteration touches remain served by exactly the same single
module they were already registered to; nothing new is exposed through
`GET /research/desk/micro/foundry` (its route file is untouched — confirmed absent from both the main
diff and the excluded-path stat).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Source dispositions + lineage/alias refs (row 2, owner `foundry_source_registry.py`) | OK | `apps/backend/app/research/foundry_source_registry.py:189-199` adds `alternatives`/`source_hash` fields to the existing `SourceRecord` dataclass in its already-registered module; `source_hash` is `init=False` and derived in the existing `__post_init__` (mirrors `source_registry_hash`'s determinism pattern) — no second computation path, no new endpoint reads it |
| Runner checkpoint / resume identity (rows 7-8, owner `foundry_runner.py` / `foundry_ledger.py`) | OK | `apps/backend/app/research/foundry_runner.py:96-109` extends the *existing* `run_one_candidate`'s already-terminal branch in place — same function, same module, same call sites (`test_foundry_runner.py`, the new hermetic suite). No parallel resume-verification path was added |
| Hermetic oracle proof of compiler→interpreter→family→freeze/ledger→runner (J-05) | OK | `apps/backend/tests/test_foundry_hermetic_epoch.py` calls only the already-registered production functions (`fc.compile_sources`, `fi.resolve_population`/`read_model`, `ff.build_family_registry`, `fl.FoundryLedger`, `fr.run_one_candidate`/`run_family`) — no new production module, no reimplementation of any registered computation |

No new displayed value is introduced (the two new `SourceRecord` fields are not yet served anywhere —
confirmed: the route module is unchanged and `_canonical_source_record`'s projection change is only
consumed by the existing hash/test code, not by any endpoint response). Consistent with the iter spec's
own "Data-contract additions: None" and the blueprint's iter-3 note, which describes exactly this as an
internal-schema deepening of already-registered rows.

## Information Architecture check

No new page, route, or feature ships this iteration (`Frontend Present: no`; 0 frontend files changed).
The `/desk` → Hypothesis Foundry panel and its nav path are unchanged.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new UI surface this iteration) | OK | `apps/frontend/` diff is empty; `reports/phase-goal-hypothesis-foundry-iter-3-ui-surface-map.md` confirms 0 new pages/routes/nav changes |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- Not a coherence issue but worth flagging for the record: the iteration's own audit
  (`docs/handoffs/goal-hypothesis-foundry-iter-3-audit.md`, finding B7) notes `SourceRecord.alternatives`
  has no fail-closed validation that named sibling ids exist/are real family members. This is a
  correctness/completeness concern (auditor's domain, already tracked as PASS_WITH_GAPS), not a Data
  Contract violation — the field is a disclosure, not a second source of family membership (family-key
  membership remains the sole mechanism, per the field's own docstring at
  `foundry_source_registry.py:189-195`), and it is not yet read by any UI/endpoint. No action needed from
  this gate.
- This iteration is hermetic-backend-only by design (matching the J-02/J-03/J-04 precedent of shipping
  machinery before the consolidated read-surface iteration). Nothing here changes the IA or Data
  Contract shape the blueprint already committed to at iter-1/iter-2; the iter-3 blueprint note (already
  written by the decomposer) accurately describes the delta.
