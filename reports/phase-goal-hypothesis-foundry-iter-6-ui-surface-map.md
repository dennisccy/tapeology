# Phase goal-hypothesis-foundry-iter-6 — UI Surface Map

**Phase:** goal-hypothesis-foundry-iter-6
**Date:** 2026-08-27
**Written by:** ui-impact-analyst

---

## File Classification

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/frontend/app/desk/page.tsx` | frontend-direct | direct | New `RunnerCheckpointSubsection` component + new `CollapsibleSection` entry inside `HypothesisFoundrySection`. |
| `apps/frontend/lib/types.ts` | frontend-direct | direct | New `FoundryExhaustProgress` type; `DeskFoundryResponse` grows `exhaust_progress`. Feeds the above component's props — no visual change on its own but load-bearing for it. |
| `apps/backend/app/research/micro_routes.py` | backend-api / full-stack | direct | `GET /research/desk/micro/foundry` grows the `exhaust_progress` key. Frontend already consumes this same endpoint (confirmed: `foundryResult` fetch feeding `HypothesisFoundrySection`) and was extended in the same iteration to render the new key — full-stack pairing. |
| `apps/backend/app/research/foundry_runner.py` | backend-api | indirect | New `read_exhaust_progress()` function computes exactly the `exhaust_progress` payload the route serves and the UI renders verbatim. No UI file itself, but the sole source of the new UI surface's data. |
| `apps/backend/app/research/foundry_ledger.py` | backend-internal | indirect | New `record_epoch_open`/`epoch_open_row` row-kind. Not called from any route directly, but `read_exhaust_progress()` reads `ledger.epoch_open_row()` — the presence/timestamp of this row is what flips the UI from the empty state to the populated state. |
| `apps/backend/app/research/foundry_freeze.py` | backend-internal | none | Repo-relative freeze-set keys, new `era_open_evidence_class_contract` field. Feeds `freeze-record.json`/`freeze-set.json` integrity checks the exhaust CLI performs before running; not rendered in any UI field this iteration (confirmed: no `era_open_evidence_class_contract` reference in `page.tsx`/`types.ts`). |
| `apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py` | backend-internal / config | none | Operator CLI script (freeze-set/freeze-record regeneration, TC-7 refusal, `--advance-freeze-commit` flag). Run outside the app; no route or page reads this script directly. |
| `apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py` | backend-internal / config | none | New operator CLI script — the real exhaust runner. Its *output* (the ledger row) is what the UI surface reflects, but the script itself is never invoked from the app and has no route. |
| `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` | config | none | QA-rig provisioning script (copies the real ledger into the scoped `:8301` root). Test/ops infrastructure, not user-visible product code. |
| `docs/hypothesis-foundry/freeze-set.json`, `docs/hypothesis-foundry/freeze-record.json` | config | indirect | Regenerated data files (relative paths, expanded coverage, new field, advanced `freeze_commit`). Their content is what the exhaust CLI verifies before it runs and writes the ledger row the UI later displays; not fetched or rendered by any route/page directly. |
| `apps/backend/tests/test_foundry_ledger.py`, `test_foundry_freeze.py`, `test_foundry_real_epoch_artifacts.py`, `test_foundry_route.py`, `test_run_hypothesis_foundry_real_exhaust.py` | backend-internal | none | Test files. No UI impact. |

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | `RunnerCheckpointSubsection` (new, inside `HypothesisFoundrySection` → "Hypothesis Foundry" panel) | New component | Surfaces the real exhaust pass's checkpoint/completion state (`exhaust_progress`) so an operator can confirm the era's second irreversible act happened, honestly, with zero protected reads. | Navigate to `http://localhost:3301/desk`, click the "Hypothesis Foundry" section header (`data-testid="desk-section-expand-hypothesisFoundry"`), then click the "Runner / Checkpoint" section header (`data-testid="desk-section-expand-foundry-runner-checkpoint-section"`). Verify the element with `data-testid="foundry-runner-checkpoint"` becomes visible and contains the text "Runner lock: Idle — lock free". |
| `/desk` | `foundry-runner-checkpoint-real-banner` (green "Real Epoch — not a fixture" banner) | New element | Distinguishes this real runtime data from the four hermetic-fixture subsections above it. | After expanding "Runner / Checkpoint", verify an element with `data-testid="foundry-runner-checkpoint-real-banner"` is visible and its text reads "Real Epoch — not a fixture". |
| `/desk` | `foundry-runner-first-read-lock` (first-read-lock timestamp line) | New element | Proves the exhaust pass's first-read lock was written, with a real timestamp. | Verify the element with `data-testid="foundry-runner-first-read-lock"` contains the text "First-read lock recorded at:" followed by the ISO timestamp `2026-08-27T06:55:51.071173Z`. |
| `/desk` | `foundry-runner-eligible-corpus-hash` (eligible-corpus manifest hash line) | New element | Shows the fingerprint of exactly which dataset members were in scope, with sealed/withheld data already excluded. | Verify the element with `data-testid="foundry-runner-eligible-corpus-hash"` contains the text "Eligible-corpus manifest hash:" followed by the hash `da7488f8609c801f7a6f7c27c736e8a2a713e98f53b2d7006956c355df5c3260`. |
| `/desk` | `foundry-runner-checkpoint-ordinal` (checkpoint "N of M" line) | New element | Shows how many frozen candidates reached a terminal state out of the total frozen-ready count. | Verify the element with `data-testid="foundry-runner-checkpoint-ordinal"` contains the text "Checkpoint:" followed by "0 of 0". |
| `/desk` | `foundry-runner-protected-read-count` (protected/withheld/sealed reads line) | New element | Proves zero protected/withheld/sealed data was read during the pass — the anti-goal-compliance evidence. | Verify the element with `data-testid="foundry-runner-protected-read-count"` contains "Protected/withheld/sealed reads:" followed by "0", rendered in the emerald/green color class (not the rose/red one). |
| `/desk` | `foundry-runner-single-flight-status` (runner lock status line) | New element | Shows whether the exhaust runner is idle, currently running, or was refused due to a concurrent invocation. | Verify the element with `data-testid="foundry-runner-single-flight-status"` contains the text "Runner lock:" followed by "Idle — lock free". |
| `/desk` | `foundry-runner-freeze-integrity-verdict` (freeze integrity verdict line) | New element | Shows whether the freeze-set/freeze-record integrity check passed ("green") before the exhaust pass ran. | Verify the element with `data-testid="foundry-runner-freeze-integrity-verdict"` contains the text "Freeze integrity:" followed by "green" in the emerald/green color class. |
| `/desk` | `foundry-runner-exhaust-complete` (completion message) | New element | Honest plain-language statement that the exhaust pass reached completion, and specifically that this era's frozen manifest carried zero `FROZEN_READY` variants. | Verify the element with `data-testid="foundry-runner-exhaust-complete"` is visible (not `foundry-runner-exhaust-incomplete`) and its text contains "Exhaust complete" and "zero FROZEN_READY variants this epoch — an honest, vacuous completion". |
| `/desk` | `foundry-runner-checkpoint-empty` (`EmptyState`, pre-lock render path) | New element (conditional) | Honest pre-first-read-lock state — must render correctly if `exhaust_progress.first_read_lock_recorded` is `false` (not expected against the real, already-run epoch, but must still render honestly rather than fabricate a value). | Not exercisable against the real, already-run epoch on `:8301`/`:3301` (the lock is permanently recorded). Confirmed instead via the backend test suite: `apps/backend/tests/test_foundry_route.py` covers the pre-lock degrade shape server-side. If ever manually exercised (e.g., against a freshly seeded rig with no ledger), verify the element `data-testid="foundry-runner-checkpoint-empty"` shows the text "The real exhaust pass has not been run yet — the first-read lock has not been recorded." |
| `/desk` | `HypothesisFoundrySection` (outer "Hypothesis Foundry" panel — pre-existing, unmodified subsections) | Regression surface | Backend response for `GET /research/desk/micro/foundry` grew one additive top-level key; every pre-existing key (`era`, `era_open_baseline`, `sources_compiler`, `interpreter_fixtures`, `freeze_integrity`, `hermetic_oracles`, `epoch_manifest`) is unchanged. | Expand each of the five pre-existing subsections ("Sources / Compiler", "Interpreter Fixtures", "Freeze / Integrity", "Hermetic Oracles", "Epoch / Manifest") and confirm each still renders its previously-shipped content with no missing or altered text (see golden-replay expected strings in the Regression section of the test plan). |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/foundry_freeze.py`'s repo-relative freeze-set key format and the new
  `era_open_evidence_class_contract` field on `FreezeRecord` — internal audit-trail/integrity
  bookkeeping consumed by the exhaust CLI's own pre-run verification, never rendered in any UI
  field.
- `apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py`'s `_load_existing_manifest_store`
  typed-refusal fix (TC-7), write-ordering change, and `--advance-freeze-commit` flag — an operator
  CLI script with no route or page consuming it.
- `apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py` (the new real exhaust CLI itself) —
  an operator/CLI-only act, by design never triggered from the app; only its *result* (the ledger
  row) is surfaced, via the separate `exhaust_progress` route key.
- `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh`'s new `cp` block provisioning
  the scoped `:8301` rig with the real ledger — QA/test infrastructure, not product code.
- `docs/hypothesis-foundry/freeze-set.json` / `freeze-record.json` regeneration — data files read by
  backend integrity checks, not fetched or rendered directly by any route or page.
- All new/changed backend test files (`test_foundry_ledger.py`, `test_foundry_freeze.py`,
  `test_foundry_real_epoch_artifacts.py`, `test_foundry_route.py`,
  `test_run_hypothesis_foundry_real_exhaust.py`) — test-only, no UI impact.

---

## Summary

- **Frontend surfaces changed:** 1 (the "Runner / Checkpoint" subsection and its 9 child elements,
  all within the existing `/desk` page).
- **New pages/routes:** 0.
- **Modified components:** 1 new component (`RunnerCheckpointSubsection`); 1 existing component
  extended to include it (`HypothesisFoundrySection`).
- **Navigation changes:** no.
- **Backend-only changes:** 6 (see above).
