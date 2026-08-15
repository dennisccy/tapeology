# Iteration 6 — Coherence Audit

**Iteration:** goal-referee-iter-6
**Date:** 2026-08-15
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Registry (families, hypotheses, withdrawals, certificates) — owner `referee_registry.py`, `GET/POST /research/desk/referee/registry[/hypotheses]` | OK | `apps/backend/app/research/referee_registry.py` (new file, whole module); wired at `apps/backend/app/research/referee_routes.py:214-321` (new `GET`/`POST` handlers). Field-level shape matches the blueprint's iter-6 note exactly: Family fields (`referee_registry.py:687-693`), Hypothesis fields (`:708-728`), Withdrawal fields (`:757-761`), `GET` response shape `{families, hypotheses, withdrawals, certificates}` (`:851-856`), `accrual` sub-shape (`:811-816`) — all field-for-field identical to `runs/goal-session-referee/state/blueprint.md`'s iter-6 note. |
| Per-hypothesis `accrual` fold (new field, registered same-iteration) | OK — reuses shared primitives, not a duplicate computation | `referee_registry.py:99-106` imports `_epoch_from_iso`, `_et_session_date`, `_is_stale_basis`, `_newest_per_session_date`, `_record_detector_basis`, `current_playbook_detector_basis` from `referee_evidence.py` rather than reimplementing any of them (confirmed these six names are defined exactly once, in `referee_evidence.py:199-306`, and nowhere else in `apps/backend/app/research/*.py`). `_hypothesis_accrual` (`referee_registry.py:771-816`) composes them into a genuinely new, boundary-filtered fold (distinct from `playbook_occurrence_readiness()`'s unfiltered `per_setup_side`, `referee_evidence.py:255-305`) — one `PlaybookStore.list()` scan per `GET`, shared across every hypothesis (`registry_response`, `referee_registry.py:840-841`), not a second store scan per hypothesis. |
| ET-calendar boundary conversion (`confirmation_start_boundary`) | OK — reused, not re-derived | `referee_registry.py:603` calls the imported `_et_session_date(_epoch_from_iso(...))`; no second DST-aware implementation exists in the new module. |
| `PLAYBOOK_CONTEXT_BACKING_BUCKETS` vocabulary (Estimand-C structural check) | OK — single source, transitively imported | Defined once at `desk_playbook_context.py:162`; `referee_registry.py:109` imports it from `referee_null.py` (which itself imports, not hand-copies, the same tuple) rather than declaring a second vocabulary tuple. Guard-tested: `referee_registry.py` imports neither `desk_playbook_detect` nor `desk_playbook_context` directly (`apps/backend/tests/test_referee_guards.py`, new `test_referee_registry_module_imports_neither_the_detect_nor_the_context_module`). |
| `backing_bucket_eligibility_rate` (already-registered field on the Matched-null-records row, owner `referee_null.py`) | OK — bug fix within the same owner/endpoint, not a new value or source | `apps/backend/app/research/referee_null.py:529-537`: one-line change (`backing_rate = None` unconditionally when `tod_eligible_count == 0`) inside the module that already owns this field; no new endpoint, no second implementation elsewhere. |
| Registry storage directory resolution | OK — matches the established sibling-dir pattern | `referee_registry.py:177-185` (`resolve_referee_registry_dir`) mirrors `referee_null.py:153-160`'s (`resolve_referee_null_dir`) exact env-var-or-sibling pattern; no new `Config` field (confirmed `apps/backend/app/config.py` untouched per `git status`). |

No new UI surface was added this iteration (`Frontend Present: no`; `reports/phase-goal-referee-iter-6-ui-surface-map.md` confirms "No UI surfaces affected"), so there is no new fetch path to check for a non-canonical source — nothing renders the registry yet, exactly as the blueprint's IA table plans (J-09 is its first UI/MCP consumer). No MCP tool was added (`git status` shows no MCP-server files touched; `EXPECTED_TOOLS` stays at 20 per the dev/audit handoffs), so there is no second read-path into the registry via MCP either.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `GET/POST /research/desk/referee/registry[/hypotheses]` | OK — no nav change needed, none made | Not a UI-facing route this iteration (backend-only; no page renders it). The blueprint's `app/meta.py` `UI_ROUTES` nav skeleton (`runs/goal-session-referee/state/blueprint.md:15-27`) already lists exactly 3 routes and the J-05 row already names `/desk` → "Referee Registry" as this feature's canonical home at baseline. `git status --porcelain` confirms no frontend files changed. Nothing to FAIL: there is no new page to be hidden, undiscoverable, duplicated, or wrapped in a parallel shell. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- This iteration's own dispatched hard-audit (`docs/handoffs/goal-referee-iter-6-audit.md`) already found and fixed a critical defect (B1: the boundary was caller-choosable via a `registered_at` field on the POST body / a `--registered-at` CLI flag) and an important one (B2: a duplicate-`hypothesis_id` retry under a new `family_id` wrote a phantom FAMILY record before refusing). Both fixes are present in the diff I reviewed (`RefereeHypothesisRegistrationRequest` in `referee_routes.py` carries no `registered_at` field; the CLI `register` subparser in `referee_registry.py` carries no `--registered-at` flag; the duplicate-hypothesis check now runs before the family write at `referee_registry.py:683-684`). Neither finding is a Data-Contract or Information-Architecture violation under this audit's mandate (no value was computed twice or served from a non-canonical source, no nav/page was affected) — noted here only so the record is complete; they do not change this verdict.
- The same audit report also lists open, explicitly-deferred gaps (B3: `WithdrawalStore.record()` misreports a corrupted file as "already withdrawn"; B4: `registry_response()` discards all four stores' per-list `integrity_errors` instead of disclosing them the way `stale_basis_dates` does elsewhere; B5/B6: dead imports and a string-comparison edge case). These are correctness/completeness matters already tracked with a recommended next step for J-06 in that report — none of them is a scattered-navigation or duplicate-computation issue, so none is a coherence WARN either; flagged here only for visibility, not as new findings.
- No label/formatting inconsistency to note: nothing from this iteration is displayed anywhere yet.
