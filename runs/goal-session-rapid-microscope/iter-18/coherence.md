# Iteration 18 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-18
**Date:** 2026-08-20
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

This iteration touches exactly one already-registered Data Contract row — "Graduation states +
export bundles" (owner `app/research/micro_graduation.py` + `micro_sealed_evaluation.py` as sole
scientific owner of the sealed-shard verdict sub-computation, registered iter-17). Frontend Present
is "no" — no new page, no new endpoint, no new value name.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Graduation states + export bundles (`GET /research/desk/micro/graduation`) | OK | `apps/backend/app/research/micro_sealed_evaluation.py:79` (new module-owned `SEALED_MIN_OBSERVATIONS = 30`, never a `Config` field), `:130-146` (`_sealed_floors()` — fixed, zero-parameter, no caller/candidate input), `:158-164` (any `candidate_spec["floors"]` refused before any verdict is derived). Endpoint and owner unchanged; verified no other module references `SEALED_MIN_OBSERVATIONS`/`SEALED_BREADTH_NOT_APPLICABLE` (`grep -rn` across `apps/backend/app` and `apps/backend/tests` returns zero hits outside `micro_sealed_evaluation.py`/`test_micro_sealed_evaluation.py`) |
| Vault shards, universes, exposure ledger (`GET /research/desk/micro/vault`) | OK | Untouched this iteration. The new `apps/backend/scripts/seed_micro_graduation_iter18_fixture.py` *calls* the canonical `vault.seal_shard`/`assign_shard`/`expose_shard` (lines ~146-155) to stage a real shard for the QA seed — it does not modify `vault.py` or reimplement any part of it. `vault.py` has zero diff vs the snapshot SHA. The resulting non-empty "iter18-qa-universe" text now asserted in `J-08.json`/`J-10.json`'s Validation Vault step is a correct downstream reflection of the canonical vault ledger, not a second source |
| `floors_applied` sub-shape (breadth fields) | OK — in-place correction, not a new row | `micro_sealed_evaluation.py:198-202`; matches the blueprint's iter-18 note (`state/blueprint.md:256-275`) verbatim: same endpoint, same owner, corrected condition-1 rule per r9/TR-30 |

No new function/service duplicates the graduation verdict computation elsewhere; no new UI surface
fetches it from a non-canonical source (there is no new UI surface — Frontend Present: no).

## Information Architecture check

No new page, route, or nav change this iteration (confirmed: `Frontend Present: no` in the iter
spec, and the ui-surface-map report at
`reports/phase-goal-rapid-microscope-iter-18-ui-surface-map.md` states "Backend-only phase ...
No UI surfaces affected"). `app/meta.py`'s `UI_ROUTES` has zero diff vs the snapshot SHA.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new surface this iteration) | OK | `app/meta.py` unchanged; `reports/phase-goal-rapid-microscope-iter-18-ui-surface-map.md` |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The QA-only seed script (`apps/backend/scripts/seed_micro_graduation_iter18_fixture.py`) is a
  clean reuse of production functions (`DatasetStore.record`, `vault.seal_shard`/`assign_shard`/
  `expose_shard`, `evaluate_sealed_verdict`) scoped to a throwaway `TAPEOLOGY_DATASET_DIR` root via
  `qa_playbook_iter7_fixture_scoped_backend.sh` — no fallback to the unscoped default path, no
  hand-rolled JSON standing in for a real computation. This is the same pattern already accepted for
  every other seed script in that directory; nothing new to flag.
- The B3 (`is_exposed_before` equal-instant boundary) and B4 (`finalize()` trade-terminated session)
  coverage-gap fixtures named in the iteration-18 spec's IN SCOPE list are not present in this
  iteration's diff — `apps/backend/tests/test_micro_accessor.py` (equal-instant test around lines
  354-372) and `apps/backend/tests/test_micro_observer.py:273`
  (`test_gap_b4_a_trade_terminated_session_stamps_finalize_at_the_trades_own_timestamp`) already
  exist and are unchanged vs the iter-18 snapshot SHA — they predate this iteration. This is a
  Definition-of-Done/completeness question for the auditor/evaluator, not a coherence question: it
  creates no duplicate computation and no navigation/ownership drift, so it is noted here only for
  visibility and not scored as a violation.
