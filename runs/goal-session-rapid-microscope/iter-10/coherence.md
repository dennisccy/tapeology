# Iteration 10 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-10
**Date:** 2026-08-18
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Graduation states + export bundles | OK | New owner `apps/backend/app/research/micro_graduation.py` (665 lines, untracked/new file — confirmed via `git status`); served solely by `GET /research/desk/micro/graduation`, added at `apps/backend/app/research/micro_routes.py:562-581` (per bounded diff). Matches the ALREADY-RESERVED row in `runs/goal-session-rapid-microscope/state/blueprint.md:60` verbatim — no second owner, no second endpoint. |
| `WF_SURVIVOR_RULE_V1` verdict (walk-forward's own canonical value, `walkforward.py`) | OK — consulted, not duplicated | `micro_graduation.py:306` calls `wf.sequence_verdict(fold_results, sidedness=sidedness, econ_floor=econ_floor, voided=voided)` and only branches on `verdict["refused"]` / `verdict["verdict"]`. No re-implementation of the five-condition rule anywhere in the new file (confirmed by full read — the rule's conditions appear nowhere as literal comparisons in `micro_graduation.py`). |
| Shard exposure state (vault's own canonical value, `vault.py`) | OK — consulted, not duplicated | `micro_graduation.py:379` calls `vault.build_vault_state(vault_shard_ledger, vault_universe_ledger)` (existing, unmodified) and only reads `shard_entry["exposure_state"]`/`shard_entry["family_root_id"]` back. No new vault-state-machine logic. |
| Scout union-N variant count (`scout_ledger.py`'s own canonical value) | OK — consulted, not duplicated | `micro_graduation.py:527` calls `scout_ledger.distinct_variant_count(scout_trials)` on trials filtered to the family — reuses the existing counting function verbatim. |
| Voiding state (`walkforward.py`'s own canonical value) | OK — consulted, not duplicated | `micro_graduation.py:304` calls `wf.is_corpus_era_voided(wf_ledger, corpus_id)` — no second voiding mechanism, matching the spec's own IN-SCOPE requirement. |
| Ledger chain integrity (hash-chain primitive) | OK — reused, not hand-rolled | `GraduationLedger.__init__` (`micro_graduation.py:210-211`) wraps `micro_chain_ledger.HashChainedLedger` directly — the required shared primitive (iter-4 lesson), not a fourth independent chain implementation. Verified by `test_tc8_a_truncated_tail_is_caught_by_the_durable_head_anchor` in `test_micro_graduation.py:413-423`, which exercises the SAME tail-anchor discipline the shared primitive provides. |
| `withheld_excluded` / `sealed_withheld` / `sealed_tranche` (disclosure sub-fields, closing iter-9's coherence WARN) | OK — documentation catch-up, no code change this iteration | `blueprint.md:62-70` now carries explicit rows for all three, each attributed to its single already-registered owner module (or, for `withheld_excluded`, the one shared predicate `vault.withheld_dataset_ids()` → `micro_snapshots.exclude_withheld()` consumed identically by every serving endpoint). `git status` confirms none of `scout.py`, `walkforward.py`, `micro_join.py`, `edge_report.py`, `edge_report_cache.py`, `pnl_scan.py`, `desk_screen.py`, `micro_snapshots.py`, `datasets.py`, or `micro_readiness.py` changed this iteration — the WARN is closed by registration only, as intended. |
| Sealed-shard evaluation pass/fail verdict (new sub-concept inside the graduation bundle) | OK — genuinely new, but scoped inside the already-registered "Graduation states + export bundles" row, not a duplicate of any existing concept | `micro_graduation.py`'s own docstring (lines 31-48) explicitly notes `vault.py` "carries no pass/fail concept at all — only shard LIFECYCLE state", so this is additive, not a re-derivation of an existing value. Served only via the one graduation endpoint; no second surface. |
| `proposed_confirmation_boundary`, `union_n_variants_tried`, `family_multiplicity`, `sealed_evaluations`, `fold_results`, `shards_touched` (export-bundle sub-fields, spec §8 point 4) | OK — sub-fields of the one already-registered bundle, served through the one canonical endpoint/module; no separate blueprint row needed (unlike the disclosure sub-fields, these are never served from any endpoint but this one) | `micro_graduation.py:494-555` (`build_export_bundle`), served only via `GET /research/desk/micro/graduation`. |

No new UI-displayed value this iteration (frontend change: none, per the iteration spec's own "New information displayed: None"), so Data Contract step 4/5 (new displayed value not yet registered) does not apply.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `GET /research/desk/micro/graduation` (J-07, backend-only, no UI this iteration) | OK — no violation; the blueprint's own IA already designates this feature "keyless/automated," inert until J-08 wires it in | `blueprint.md:41` ("Graduation states (J-07) \| keyless/automated; states surface via the Scout Ledger / Walk-Forward / Vault rows they attach to \| Desk") plus the standing precedent recorded at `blueprint.md:87-90` (iter-3's identical pattern for J-03's joinable-corpus field, "the wiring iteration (J-08) is already named in the Information Architecture table above, so this is not an orphan feature"). No nav/sidebar/router file changed this iteration (`git status` shows zero frontend files touched), so there is nothing new to check for reachability — the route has deliberately zero UI surface yet, exactly as planned and as the blueprint already sanctions. |

No new page, route with a UI surface, or nav change exists in this iteration's diff — Part B has nothing else to evaluate.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `docs/goal.md` and `docs/rapid-validation-spec.md` carry this same day's r5 owner-ruling edits (the opaque-research-pool rule for the vault/recorder surfaces). Per the carried context for this audit, r5 governs J-06 territory, not J-07's graduation work, and it touches neither `blueprint.md`'s Information Architecture nor its Data Contract — confirmed no coherence-relevant fallout from r5 in this iteration's diff.
- The iter-9 coherence WARN ("`withheld_excluded`, `sealed_withheld`, `sealed_tranche` served across roughly nine endpoints but not yet rows in this table") is now closed by `blueprint.md`'s new "Disclosure sub-fields" table — verified above. No re-raise.
