# Iteration 17 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-17
**Date:** 2026-08-20
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

This round's only Data-Contract-relevant change is the sealed-shard evaluation verdict sub-owner
move (TR-23) and the lineage-wide confirmation-boundary rewrite (TR-24), both sub-computations of
the already-registered "Graduation states + export bundles" row
(`runs/goal-session-rapid-microscope/state/blueprint.md:60`). I verified — by reading the diff, the
new module in full, and a repo-wide grep for competing definitions — that exactly one function
computes each value and exactly one endpoint serves it.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Sealed-shard evaluation verdict (PASS/FAIL/`insufficient`) | OK | Sole definition of `SEALED_PASS_RULE_V1` and the verdict-deriving function: `apps/backend/app/research/micro_sealed_evaluation.py:122` (`SEALED_PASS_RULE_V1 = ...`), `:260` (`def evaluate_sealed_verdict`), `:218` (`def _derive_verdict`). Repo-wide grep confirms these are the only definitions in `apps/backend/app/`. |
| `record_sealed_evaluation` (persistence of the verdict) | OK — no second computation | `apps/backend/app/research/micro_graduation.py:357` — retired the caller-supplied `passed: bool` parameter (old shape now raises `TypeError` at argument-binding, confirmed by diff + `TC-1`/`TC-15`); now only persists an already-computed `artifact: dict` and enforces single-shot idempotency. Grep confirms exactly ONE production call site, `micro_sealed_evaluation.py:411`, using the new `artifact=` shape — no lingering caller uses the old shape. |
| `GET /research/desk/micro/graduation` (serving endpoint) | OK — unchanged, single route | `apps/backend/app/research/micro_routes.py:572` (`@router.get("/graduation")`) — sole route definition; handler body (`:571-586`) calls only `list_graduation_families(ledger)`, a verbatim ledger read, no inline computation (T-8 "page-load GETs never compute" discipline, matching the `GET /scout`/`/walkforward`/`/vault` precedent). No new/second endpoint anywhere in the diff. |
| `proposed_confirmation_boundary` / `lineage_data_frontier` / `evidence_safe_boundary` (TR-24 rewrite) | OK | All new helpers (`_lineage_data_frontier` `micro_graduation.py:509`, `_embargo_for_lineage`, `_evidence_safe_boundary`, `_proposed_confirmation_boundary` `:605`, `final_confirmation_boundary` `:616`) live inside the SAME already-registered owner module and are each defined exactly once (grep-confirmed). `build_export_bundle` (the sole builder, unmoved) persists the full derivation as new sub-fields of the existing bundle — no new module, no new endpoint. |
| Non-canonical UI/MCP read of any of the above | OK — none exists | Zero `apps/frontend/**` diffs (git diff + `git status`); `reports/phase-goal-rapid-microscope-iter-17-ui-surface-map.md` states the graduation endpoint "is not fetched by any `/desk` section or MCP tool today (confirmed by grep... zero hits for 'graduation' in `page.tsx` or `app/mcp/*.py`)"; the independent audit's own Frontend Findings section (`docs/handoffs/goal-rapid-microscope-iter-17-audit.md:132-134`) independently confirms "None. Zero `apps/frontend/**` files changed." So there is no second surface that could ever show a different number for this value. |

No duplicate computation, no non-canonical source, no new unregistered displayed value (nothing new
is displayed at all this round — the bundle's new fields are internal sub-fields of an
already-registered, currently UI/MCP-unconsumed endpoint payload, consistent with this blueprint's
own established iter-3/iter-11/iter-16 precedent for in-place sub-owner/formula clarifications that
don't change a row's shape or serving path).

One thing intentionally left off this table: the r9 spec revision (`docs/rapid-validation-spec.md`,
2026-08-20) adds a new pinned constant `SEALED_MIN_OBSERVATIONS` and a rule that no sufficiency
floor may be caller-supplied. That revision is text-only this round — `micro_sealed_evaluation.py`'s
`_resolved_floors` (`:203-215`) still resolves floors from `candidate_spec.get("floors")`, disclosed
in the module's own docstring as "OWNER-OWED" pending exactly this ruling. Per the carried
instruction, r9 landed after this round's implementation and is explicitly next-round work, not a
defect in this round's diff — and it is not a coherence violation either way: there is still exactly
one function computing the verdict from whatever floors it is given, not a second competing
implementation.

## Information Architecture check

No new page, route, or feature this iteration. `apps/frontend/**` has zero diffs (verified via
`git diff 2485067...` and `git status`); `runs/goal-session-rapid-microscope/state/blueprint.md`'s
Information Architecture section (nav skeleton + feature-home table) is untouched by this iteration's
diff — only the Data Contract section's Graduation row changed. The ui-surface-map's own rows are all
labeled "Regression check (source unchanged)" or "no route — direct backend URL," confirming nothing
new was added to the nav.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new surface this iteration) | OK | `apps/frontend/**` 0 diffs; `runs/goal-session-rapid-microscope/state/blueprint.md` IA table unchanged; `reports/phase-goal-rapid-microscope-iter-17-ui-surface-map.md` Summary: "Frontend surfaces changed: 0 · New pages/routes: 0 · Modified components: 0 · Navigation changes: no" |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `final_confirmation_boundary` (`apps/backend/app/research/micro_graduation.py:616`) is a new
  exported utility not called by any production path this round — its own docstring discloses this
  plainly ("never called by `build_export_bundle` itself, since no real Referee registration happens
  this round"). Not a coherence issue (nothing is served or displayed through it yet, so there is no
  second value to disagree with anything), just noted for continuity: whichever future iteration
  wires real Referee registration should call this one function rather than re-deriving the
  `max(proposed, registration)` rule inline.
- The r9/TR-30 gap noted above under the Data Contract check (`SEALED_MIN_OBSERVATIONS` specified but
  not yet implemented) is not a coherence defect — flagging it here only so the next iteration's
  decomposer has it in one place alongside the rest of this round's coherence read.
