# Iteration 8 — Coherence Audit

**Iteration:** goal-playbook-iter-8
**Date:** 2026-08-11
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Evidence aggregates (`cells`/`invalidation_breached`/`other_signatures`/`parameters`/`register`) | OK | Computed by new `fold_evidence`/`inspect_signature` in `apps/backend/app/research/desk_playbook_evidence.py:383-433`; wired to the registered `GET /research/desk/playbook/evidence` (optional `?signature=`) at `apps/backend/app/research/desk_routes.py:1320-1349` — exact match to the blueprint's reserved row (`runs/goal-session-playbook/state/blueprint.md:116`) and the iter-8 spec's "Data-contract additions" shape (`docs/phases/goal-playbook-iter-8.md:147-166`). Response shape (`signature`, `cells[]`, `invalidation_breached[]`, `other_signatures[]`, `parameters`, `register`) matches `apps/frontend/lib/types.ts:841-887`'s `DeskPlaybookEvidence*` types field-for-field. |
| Measurement rail (unchanged owner, `desk_forward.py`) | OK — no re-implementation | `desk_playbook_evidence.py:63` imports `DESK_FORWARD_HORIZONS_MINUTES`/`_collect_measures` from `.desk_forward` verbatim and never imports or calls `_measure_from`; the module's own docstring (`desk_playbook_evidence.py:8-18`) states the only genuinely new math is the quartile fold (`_quartile_stats`, `:254-268`), which the rail's own `_avg_cell`/`_collect_measures` never produced (no p25/p75 there) — this is new EVIDENCE math the blueprint's own "Ships at" note for this row explicitly anticipates (`blueprint.md:116`), not a duplicate of a registered value. A source-scan/behavioral guard confirms the rail import stays zero-diff (`apps/backend/tests/test_desk_playbook_guards.py:453-466`, updated this iteration to a LIVE enforcement now that the evidence module exists). |
| Playbook records / store (unchanged owner, `desk_playbook.py`) | OK — no re-implementation | `desk_playbook_evidence.py:64-71,241,427` reads exclusively through `PlaybookStore.get` (the store's own verified reader); `_projections_by_signature` (`:217-248`) never opens a record file directly. `compute_playbook_input_signature`/`playbook_parameters` are imported verbatim (`:69-70`), never re-derived. |
| Single-signature pooling (hard anti-goal) | OK — guard-tested | `fold_evidence` (`desk_playbook_evidence.py:398-405`) partitions projections by `playbook_input_signature == default_signature` before folding; only `default_projections` ever reaches `_fold_cells`/`_fold_invalidation_breached`, everything else is listed via `_fold_other_signatures` (`:359-380`), never pooled. Enforced by a dedicated test (`apps/backend/tests/test_desk_playbook_evidence.py:375`, TC-5) plus the guard-test cross-reference in `test_desk_playbook_guards.py:435-441`. |
| Evidence projection cache — no update/delete method | OK — guard-tested | `PlaybookEvidenceCache` (`desk_playbook_evidence.py:119-174`) exposes only `lookup`/`insert` (idempotent `INSERT OR REPLACE`), no `update`/`delete`; asserted by `test_desk_playbook_evidence.py:471` (`test_playbook_evidence_cache_has_no_update_or_delete_method`). |
| Back-scan plan (unchanged owner, `desk_playbook_backscan.py`) | OK — fix stays in the canonical owner | The malformed-date honesty fix (`_planned_dates`, `desk_playbook_backscan.py:41-58`) and the new `malformed_days` helper (`:210-215`) both live in the ALREADY-registered owning module for this row (`blueprint.md:114`); `desk_routes.py:1234` (the trigger route) only calls that owner's function, it does not reimplement date-parsing itself. No new endpoint, no second date-validity rule. |
| Served numerics on the new section (`cell.signal.*`/`cell.baseline.*`/`breach.*`) | OK — reformat only | `apps/frontend/app/desk/page.tsx:556-731` (`PlaybookEvidenceCellRow`/`PlaybookEvidenceBreachRow`) passes every field through `fmt()` with no arithmetic; the client-side-arithmetic guard is extended to cover exactly these bindings (`apps/backend/tests/test_desk_ui_guards.py:491-494`) with a counter-test proving it fires on seeded violations (`:501-515`). `fetchDeskPlaybookEvidence` (`apps/frontend/lib/api.ts:806-827`) fetches only the one registered endpoint — no second fetch path for this value anywhere in the diff. |

No new displayed value in this iteration is missing from the Data Contract — every field the new Playbook Evidence section renders (`cells[].signal/baseline/below_min_n`, `invalidation_breached[]`, `other_signatures[]`, `register`) is an exact match to the iter-8 spec's "Data-contract additions" section and the blueprint's pre-registered row.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Playbook Evidence section | OK | New `<section aria-label="Playbook Evidence">` added to the existing `/desk` route, rendered directly below the shipped Backscan panel inside the page's existing `<main>`/`Panel` shell (`apps/frontend/app/desk/page.tsx:777-781`). No new route. `apps/backend/app/meta.py` (`UI_ROUTES`, the nav's single data source per `blueprint.md:40`) and `apps/frontend/components/NavBar.tsx` are both untouched this iteration (`git diff 5a4cae42f... -- apps/backend/app/meta.py apps/frontend/components` returns empty) — the 3-row nav (Cockpit/Structure/Desk) is unchanged, so the section is reachable via the existing "Desk" nav link (1 click) + scroll, well within the ≤2-click bar. |
| No duplicate home | OK | This is the blueprint's own pre-reserved "Playbook Evidence" IA slot (`blueprint.md:63-64`), and the iteration spec's "Blueprint conformance" field cites the identical slot (`docs/phases/goal-playbook-iter-8.md:140-144`) — not a second home for any existing entity. |
| No parallel shell | OK | The section reuses the existing `Panel` component and the page's established table/badge styling (same `ROW_NUMERIC_CELL`/`LoadingPanel`/`UnavailablePanel`/`EmptyState` primitives every other `/desk` section uses — `apps/frontend/app/desk/page.tsx:707-731`), not a bespoke layout. |
| Back-scan trigger refusal (422 on malformed date) | OK — behavior change, not a new surface | Same registered endpoint (`POST /research/desk/playbook/backscan/compute`), no new route or panel; the existing Backscan panel's own error-display convention handles the response (per `reports/phase-goal-playbook-iter-8-ui-surface-map.md`'s row on the From-input behavior change). |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The iteration also touches framework/harness files outside the product blueprint's scope (`incredible_auto_dev/scripts/automation/{browser-qa-phase.sh,goal-iter-lean.sh,lib/replay-lane.sh,run-evals.sh}`, plus new `project-extensions/store-scope/` and `incredible_auto_dev/scripts/automation/store-scope/`) — a new store-scope guard for the golden-replay lane. This is pipeline/QA infrastructure, not an app-level displayed value or route, so it is outside the Data Contract/IA rules this gate enforces; noted for completeness only.
- `EVIDENCE_REGISTER` (`desk_playbook_evidence.py:98-113`) is long and dense compared to the shorter `PLAYBOOK_REGISTER`/`FORWARD_REGISTER` strings it says it follows the pattern of. Not a coherence violation (single string, single owner, no banned-language hits observed), just a readability note for the decomposer to consider if a future iteration touches this copy.
