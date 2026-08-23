# Phase goal-rapid-microscope-iter-24 — UI Surface Map

**Phase:** goal-rapid-microscope-iter-24
**Date:** 2026-08-23
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | `ValidationVaultSection` — "Sealed at" column, `validation-vault-shards-table` (behind `desk-section-expand-validationVault`) | **Changed behavior (regression — verified)** | Backend `_serialize_shard` (`vault.py:1497`) now serves `sealed_at` as a bare `YYYY-MM-DD` string instead of a full ISO timestamp; the frontend's unchanged `formatDateTimeET` call still converts every value through the `America/New_York` timezone, so a date-only input parses as UTC midnight and displays as the PREVIOUS calendar day plus a spurious time (e.g. served `"2026-06-09"` renders `"2026-06-08 20:00 ET"`) | Navigate to `http://localhost:3301/desk`, click the element with `data-testid="desk-section-expand-validationVault"`, locate the shards table (`data-testid="validation-vault-shards-table"`), and read the "Sealed at" cell for any row (e.g. the `iter18-qa-universe` shard from J-08/J-10). Record the exact displayed string. **Pass condition the operator likely expects:** a bare date like `2026-06-09` with no time or `ET` suffix. **Actual verified behavior:** a shifted date plus a time like `2026-06-08 20:00 ET` — flag as a defect if reproduced live. |
| `/desk` | `ValidationVaultSection` — "Assigned at" / "Exposed at" columns | Unchanged | These fields were NOT touched by this iteration's `_coarsen_sealed_at_to_date` (only `opaque["sealed_at"]` is coarsened) | For a non-sealed (assigned/exposed) shard row, confirm "Assigned at" still shows a normal full date-time like `2026-06-09 14:32 ET` (no regression here — contrast against the broken "Sealed at" cell in the same row) |
| `/desk` | `ValidationVaultSection` — sealed-row opacity (`Dataset`/`Family root`/`Symbol`/`Session date`/`Assigned at`/`Exposed at`/`Content checksum` cells) | Unchanged (pre-existing invariant, re-verify) | Anti-goal r5 requires no still-sealed shard discloses symbol/date; this iteration must not have weakened it | For a shard row whose "State" column reads `sealed`, confirm the 7 cells to its right each read exactly `sealed — opaque`, never a real symbol or date |
| `/desk` | `ScoutLedgerSection` (behind `desk-section-expand-scoutLedger`) | New QA-fixture data (scoped rig only, not the ordinary backend) | New seeder `seed_micro_scout_iter24_j09_fixture.py` plants a real `capitulation_exhaustion_pilot` family via `scout.register_screen_and_walkforward_check`, giving J-09 non-empty content to assert on | Against the scoped QA rig (`bash apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh`), navigate to `/desk`, click `desk-section-expand-scoutLedger`, confirm the text `failed_aggression_score__playbook_signal__trades_20` is visible in the ledger table, alongside a decision in the closed vocabulary (dev handoff reports `killed_insufficient_n`) |
| `/desk` | `ScoutLedgerSection` empty-state text (`data-testid="scout-ledger-families-empty"`, "No candidates ledgered.") | No product code change — only two stored QA-replay JSON scripts' assertions changed | J-08.json step 3 and J-10.json step 12 now assert the always-present "Ledger chain verification:" heading instead of the empty-state text, because the SAME scoped rig now has a non-empty ledger after the J-09 seed runs | Against the ORDINARY backend (a fresh `.data/` store with zero Scout candidates, NOT the QA rig), confirm the Scout Ledger section still shows "No candidates ledgered." exactly as before — proves the empty-state message itself is unchanged in production code |
| `/desk` (Graduation, via Scout Ledger / Walk-Forward / Vault sections; J-07) | No component changed | Re-verification only — zero diff to `micro_graduation.py` / `micro_sealed_evaluation.py` this iteration (grep-confirmed by dev) | Run the standard scoped QA rig, walk through the Graduation-relevant sections, and capture a screenshot dated 2026-08-23 (or later) — a carried-forward iter-22 screenshot is explicitly not acceptable this iteration per the phase DoD |
| `/desk` | Full page shell, `data-testid` structure, section order | Unchanged | No frontend file in `git diff` touches `apps/frontend/` (confirmed: only `tsconfig.json`, no app code) | Confirm the six `/desk` sections (Microscope Readiness, Scout Ledger, Walk-Forward, Validation Vault, plus Referee Registry/Adjudications/Runs) still appear in the same order with the same headings as before this iteration |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/scripts/j06_operator.py` — widened `stage_tr2()` with a run-aware third check
  (`residual_pool_uncertainty_by_run_time_bucket`), consulted only by the operator CLI
  (`j06_operator.py verify`/`tr2`) — no web route, no UI surface.
- `apps/backend/scripts/seed_micro_scout_iter24_j09_fixture.py` — new QA-fixture seeder script,
  run only by the scoped test rig launcher — not part of any user-facing flow.
- `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` — QA rig launcher extension
  (invokes the new seeder) — test infrastructure only.
- `apps/backend/tests/test_vault.py`, `apps/backend/tests/test_j06_operator.py` — new/extended
  unit tests — no runtime UI surface.
- `runs/goal-session-rapid-microscope/journey-scripts/J-09.json` (new),
  `J-08.json`/`J-10.json` (assertion text swap) — stored golden-replay test assets, not
  application code; they encode assertions ABOUT the Scout Ledger UI surface (see table above)
  but do not themselves render anything.
- `runs/goal-session-rapid-microscope/state/assumptions.md`, `blueprint.md` — process/doc
  artifacts, no UI surface.
- The independent full-file read of `j06_operator.py`/`tick_recorder.py` — no code change beyond
  what's already listed above; a review activity, not a UI-affecting change.

---

## Summary

- **Frontend surfaces changed:** 0 files edited, but **1 UI surface behaves differently** as a
  direct downstream effect of a backend-only change (the Validation Vault "Sealed at" column) —
  and that surface now exhibits a verified display regression (wrong date + spurious time) rather
  than the intended clean date-only display.
- **New pages/routes:** 0
- **Modified components:** 0 (zero `apps/frontend/` files in the diff)
- **Navigation changes:** no
- **Backend-only changes:** 7 files/scripts with no UI impact (listed above)
