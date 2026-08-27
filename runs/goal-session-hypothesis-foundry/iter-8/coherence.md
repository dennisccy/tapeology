# Iteration 8 — Coherence Audit

**Iteration:** goal-hypothesis-foundry-iter-8
**Date:** 2026-08-27
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->
<!-- COHERENCE-WARN: only advisory issues; does NOT block GOAL_ACHIEVED -->
<!-- COHERENCE-FAIL: ≥1 objective violation; blocks GOAL_ACHIEVED, forces a consolidation iteration -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `final_summary` (new top-level key: `source_counts_by_disposition`, `family_count`, `variant_count`, `frozen_ready_total`, `diagnostic_survivor_count`, `freeze_integrity_verdict`, `evidence_class`, `protected_read_count`, `exhaust_complete`, `epoch_status`) | OK | `apps/backend/app/research/micro_routes.py:144-174` (`compute_foundry_final_summary`) — matches the blueprint's pre-registered row exactly: new module `micro_routes.py` (as registered), pure projection over `_EPOCH_MANIFEST_VIEW`/`compute_frozen_ready_total`'s already-canonical result/`exhaust_progress`, zero second counting site. Proven by `test_iter8_final_summary_copies_frozen_ready_total_verbatim_never_resums_families` (`test_foundry_route.py:484-511`). |
| `epoch_manifest.source_dispositions[].{quoted_spans,source_hash,mechanism_statement,operative_formula_refs,direction_derivation,comparator_derivation,threshold_provenance,superseded_fields,alternatives,audit_note,lineage_id}` | OK | `micro_routes.py:36-56,86-99` (`_enrich_source_dispositions_with_registry_provenance`) — pure merge of two already-parsed JSON payloads (`source-registry.json` records into `epoch-manifest.json` dispositions) via the existing single `read_epoch_manifest_view()` call; no second compile pass, no `resolve_foundry_dir()`. Matches the blueprint row verbatim. Independently cross-checked by `test_iter8_source_dispositions_carry_full_registry_provenance_verbatim` (`test_foundry_route.py:319-342`) and confirmed field-by-field by the human auditor (`docs/handoffs/goal-hypothesis-foundry-iter-8-audit.md` B1). |
| `exhaust_progress.diagnostic_survivor_count` | OK-BUT-SEE-ADVISORY | `micro_routes.py:120-127` (`_compute_diagnostic_survivor_count`), merged into the per-request `exhaust_progress` dict at `micro_routes.py:202-205`. Blueprint text (`state/blueprint.md` Data Contract row for `exhaust_progress`) names the owner as `foundry_runner.py`'s `read_exhaust_progress()`; the actual sole implementation lives in `micro_routes.py` instead. See Advisory notes below — judged NOT a duplicate-computation violation on the merits, but the blueprint text is now stale and should be corrected. |
| `/desk` nav / IA shell | OK | No route/nav file touched this iteration (`apps/frontend/components/NavBar.tsx` and `apps/backend/app/meta.py` both absent from the diff); nav renders from `GET /meta/ui-routes`, unaffected. |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| J-08 Final Summary subsection (`data-testid="foundry-final-summary"`) | OK | `apps/frontend/app/desk/page.tsx:8264-8274` — new `<CollapsibleSection id="foundry-final-summary-section">` nested inside the existing `HypothesisFoundrySection` component, reusing the same `openSubsections`/`toggleSubsection` state and the single already-fetched `foundry` payload. No new route (`git diff --name-status -- 'apps/frontend/**'` shows only `app/desk/page.tsx` and `lib/types.ts` touched — no new `page.tsx`, no new directory). No new nav link (`apps/frontend/components/NavBar.tsx` unchanged; nav renders from `GET /meta/ui-routes`, which `apps/backend/app/meta.py` — untouched — serves). Matches the blueprint's pre-registered IA row: "J-08 Final Foundry truth ... `/desk` → Hypothesis Foundry (top-level summary + detail view) | Desk". Reachable in the same ≤2-click path as every other Foundry subsection (Desk nav link → expand Hypothesis Foundry panel → expand Final Summary). |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Stale Data Contract module attribution for `exhaust_progress.diagnostic_survivor_count`.** The blueprint's Data Contract row states this field is "computed by `app/research/foundry_runner.py`'s `read_exhaust_progress()`". In practice `foundry_runner.py` is one of the 59 freeze-set-sealed files (verified directly: `docs/hypothesis-foundry/freeze-set.json` line 28, hash matches byte-identically before and after this iteration), so it cannot be edited — the dev correctly caught this (both the spec's IN SCOPE list and `plan.md` had wrongly pointed at the sealed file too, per the human auditor's B1 finding) and placed the SOLE implementation, `_compute_diagnostic_survivor_count()`, in the non-sealed `micro_routes.py` (`micro_routes.py:107-127`). I verified there is exactly one implementation of this concept in the codebase — no pre-existing computation of `diagnostic_survivor_count` exists anywhere else to duplicate (`grep -rn "diagnostic_survivor_count"` across `apps/` returns only this new function, its call site, its test file, the frontend type, and the frontend render — no second computation site). The function reuses the sealed module's own `SCOUT_TO_FOUNDRY_STATE["survive"]` constant (imported, never re-literalled) and the shared `FoundryLedger`/`ROW_KIND_TERMINAL` reader/constant (also imported, never reimplemented) — so even the filtering vocabulary has one source. This is the identical shape of deviation the blueprint itself already blessed at iter-7 for `exhaust_progress.frozen_ready_total` (row-split from `foundry_runner.py`/`foundry_ledger.py` to a named `micro_routes.py` helper, for the same "true owner is sealed" reason), which that iteration's own coherence-auditor treated as the correct resolution once consolidated into one named function. On the merits this is NOT a duplicate-computation FAIL: there is one computation site, forced there by an objective, independently-verified sealed-file constraint, following established precedent. It IS a documentation-accuracy gap: `state/blueprint.md`'s Data Contract table should be corrected next iteration (a row-split note, mirroring the iter-7 treatment of `frozen_ready_total`) to name `micro_routes.py` as the real owner, so future audits don't have to re-derive this from the diff.
- **Redundant (not divergent) ledger read.** `_compute_diagnostic_survivor_count` opens its own `FoundryLedger` and calls `all_rows()` a second time per request, in addition to the read `read_exhaust_progress()` already performs for `terminal_count` in the same request (`micro_routes.py:202-205`). Both reads hit the same on-disk ledger within one synchronous request with no interleaving writes, so there is no risk of the two counts disagreeing — this is a performance/IO redundancy, not a data-contract violation. Already logged and independently verified harmless by the human auditor (`docs/handoffs/goal-hypothesis-foundry-iter-8-audit.md` B2 — confirmed via mtime/size diffing that no ledger file was mutated across repeated GETs). Non-blocking; worth folding into the same future consolidation pass that corrects the blueprint attribution above, if/when `foundry_runner.py`'s seal is ever lifted or a wrapper is introduced.
- **`test_run_hypothesis_foundry_real_exhaust.py` docstring correction (TC-10)** — verified: the corrected text now states plainly that freeze-set hash pinning, not the equivalence assertion itself, is what prevents the two `frozen_ready_total` formulas from silently diverging (`test_run_hypothesis_foundry_real_exhaust.py:546-556`). No assertion-logic change; the sealed CLI file is untouched. Purely a documentation fix — no coherence impact, noted for completeness.
