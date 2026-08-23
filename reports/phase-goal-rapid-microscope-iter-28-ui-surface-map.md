# Phase goal-rapid-microscope-iter-28 — UI Surface Map

**Phase:** goal-rapid-microscope-iter-28
**Date:** 2026-08-23
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | `RefereeEvidenceReadinessSection` → Strategy Family block, new `<p data-testid="referee-evidence-strategy-seal-unaware-caveat">` | Updated layout (new static text element) | Owner ruling r5-point-7 (`docs/rapid-validation-spec.md` §10.7): the legacy `Datasets`/`Trades` counts are seal-unaware and must carry a verbatim disclosure since `referee_evidence.py` itself is frozen and cannot be edited to add the caveat server-side | Navigate to `/desk`, click the "Referee Registry" section header (`data-testid="desk-section-expand-refereeRegistry"`) to expand it, scroll to the "Strategy Family" sub-heading under "Evidence Readiness", and verify the exact sentence "Legacy Referee readiness metric — seal-unaware in the Rapid Microscope era. It may include withheld/unexposed Rapid-Microscope shards and must not be used as the canonical Rapid-Microscope readiness count." appears directly below the tick-gate line and directly above the basis-caveats bullet list |

<!-- Change Type options: New page | New component | Updated layout | Added navigation | Changed behavior | Removed element | New form | New table | New modal -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_micro_readiness.py` — `real_readiness`/`real_dataset_records` fixtures
  now use a persistent, gitignored `DatasetStore(index_db_path=...)` + `MicroReadinessCache` DB
  (the same production caching primitives `routes.py`'s `get_dataset_store()` already wires)
  instead of a fresh `tmp_path_factory` dir every run; plus a new test
  `test_tc10_corrupted_dataset_surfaces_with_a_warm_durable_index_from_a_different_store` — no UI
  surface affected (test-infra only, no served route or response shape changed).
- `apps/backend/tests/test_micro_join.py` — new `_real_corpus_dataset_store()` helper giving the
  same durable `index_db_path=` treatment to `test_tc16_real_corpus_joinable_corpus_arithmetic_is_
  unchanged_by_the_passenger_fixes` and `test_tc4_real_corpus_join_playbook_signal_is_unaffected_
  by_the_accessor_re_point` — no UI surface affected (test-infra only).
- `apps/backend/tests/test_micro_readiness_seal_unaware_caveat.py` — new file, 4 static-scan guard
  tests proving the frontend caveat constant is unique and character-for-character matches spec
  §10.7 — no UI surface affected (this is a test file that reads `page.tsx`'s source text; it does
  not run the app and does not itself change or serve anything to a user).
- No route handler, endpoint, response schema, or `referee_evidence.py`/`referee_routes.py`
  business logic changed anywhere this iteration (verified: all six `referee_*.py` files re-hash
  byte-identical to the iteration-0 SHA-256 baseline). `GET /research/desk/referee/evidence`'s
  response shape and values are completely unchanged — only the frontend's rendering of that
  already-served response gained one new static line.

---

## Summary

- **Frontend surfaces changed:** 1
- **New pages/routes:** 0
- **Modified components:** 1 (`RefereeEvidenceReadinessSection` in `apps/frontend/app/desk/page.tsx`)
- **Navigation changes:** no
- **Backend-only changes:** 3 (two test-infra fixture fixes + one new backend-only guard test file)
