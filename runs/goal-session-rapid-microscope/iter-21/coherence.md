# Iteration 21 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-21
**Date:** 2026-08-20
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

<!-- COHERENCE-WARN: only advisory issues; does NOT block GOAL_ACHIEVED -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `joinable_corpus.band_touch_count` (materialized from sentinel to real int) | OK | Owner unchanged: `apps/backend/app/research/micro_join.py:105` (new `enumerate_band_touches`) feeds the SAME `micro_readiness.py:296` `build_readiness` / `micro_readiness.py:475`+ (`joinable_corpus_counts` call site) that already owned this field; served only by `GET /research/desk/micro/readiness` (`apps/backend/app/research/micro_routes.py:97-114`). No second computation, no second serving endpoint. |
| Scout anchor extraction for `structure_context.kind="band_touch"`/`"playbook_signal"` | OK | `apps/backend/app/research/scout.py` new `_extract_band_touch_anchors`/`_extract_playbook_signal_anchors`/`_extract_divergence_anchors` all call the already-registered join primitives `mj.join_band_touch`/`mj.join_playbook_signal`/`mj.enumerate_band_touches`/`mj.outcome_row_at_single_horizon` (module `micro_join.py`) rather than reimplementing any join or outcome math — no duplicate computation. |
| Pilot-study candidate registration/screen (`register_and_screen_candidate`) | OK | `pilot_study_candidate_grid` (scout.py) builds kwargs dicts consumed by the SAME single production entry point every other grid already uses — no second screening implementation. |
| `divergence_at_level` / `failed_aggression_score` formulas | OK | Reused verbatim from `micro_features.py` (pre-existing, pre-frozen per spec §1) — no re-derivation found in the diff. |
| Scout-candidate walk-forward floor-check decision (`register_screen_and_walkforward_check`, `scout.py:1732`) | UNREGISTERED (WARN, not FAIL) | Computed by `walkforward.py`'s new `scout_candidate_walkforward_floor_check` (correct owner per the "Fold specs..." Data Contract row), but the resulting row is appended to the **Scout** ledger (`scout.py:1809-1826`, `"stage": "walkforward_floor_check"`) and served only via `GET /research/desk/micro/scout` — never via `GET /research/desk/micro/walkforward`. The phase spec's own "Data-contract additions" field (`docs/phases/goal-rapid-microscope-iter-21.md`) describes this row as "folds/decay → walkforward.py → GET /research/desk/micro/walkforward," which does not match what was actually built. There is only ONE serving path for this value (no duplicate computation, no non-canonical fetch), so this is not an objective FAIL — see Advisory notes. |
| `structure_context.setup_id` (additive, optional field) | OK | Additive-only widening of an already-registered row's shape (`apps/frontend/lib/types.ts` `ScoutTrialRow.structure_context`), verified byte-identical for every pre-J-09 candidate (no `setup_id` key when absent). |
| `POST /research/desk/micro/scout/compute` `grid` body param | OK | Request parameter, not a displayed value (matches the existing `observer=` kwarg precedent) — correctly carries no Data Contract row. |
| MCP `desk_scout` / `desk_walkforward` proxies | OK | No new MCP tool; both remain byte-identical GET proxies per goal.md TC-16 (not independently re-verified live in this audit, but no MCP-layer code changed in the diff). |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Scout Ledger — new `structure_context.kind` inline suffix + walk-forward floor-check row | OK | No new page/route/component. Renders inside the already-shipped `ScoutLedgerSection` in `apps/frontend/app/desk/page.tsx` (diff at line ~6333), under the already-registered Desk → Rapid Microscope → Scout Ledger home. |
| Microscope Readiness — new "band touches" row | OK | Renders inside the already-shipped `MicroReadinessSection` (`apps/frontend/app/desk/page.tsx` diff at line ~6011), already-registered Desk → Rapid Microscope → Microscope Readiness home. |
| Nav / layout | OK | `git diff --stat` against the iteration's snapshot SHA shows only `apps/frontend/app/desk/page.tsx` and `apps/frontend/lib/types.ts` touched on the frontend — no sidebar/nav/router file changed, confirming "No nav-skeleton change" as claimed by the iteration spec. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Undocumented serving endpoint for the walk-forward floor-check decision.** The scout-candidate
  walk-forward floor-check row (`scout.py:1809`, `"stage": "walkforward_floor_check"`) is computed
  by `walkforward.py` but persisted into and served exclusively through the **Scout** ledger/
  endpoint (`GET /research/desk/micro/scout`), never through `GET /research/desk/micro/walkforward`
  — it also does not appear in the Walk-Forward section's own UI (confirmed by
  `reports/phase-goal-rapid-microscope-iter-21-ui-surface-map.md`'s own "Backend-Only Changes"
  note: "it does NOT appear in the separate Walk-Forward section's own UI"). This is within the
  blueprint's IA allowance (`blueprint.md`'s J-09 row explicitly lists "Scout Ledger / Walk-Forward"
  as interchangeable homes for pilot-study results), and there is exactly one serving path for the
  value, so this is not a Data Contract violation. However, the phase spec's own "Data-contract
  additions" section mis-describes this row's endpoint as `GET /research/desk/micro/walkforward`.
  **Suggested fix (finite, for the next iteration's blueprint edit):** add an iter-21 documentation
  note to `runs/goal-session-rapid-microscope/state/blueprint.md`'s Data Contract clarifying that
  the scout-candidate walk-forward floor-check decision, though computed by `walkforward.py`, is a
  new sub-row of the ALREADY-registered "Scout trials, kills, denominators, screens" entry (owner
  `scout.py`+`scout_ledger.py`, served by `GET /research/desk/micro/scout`) — not a sub-row of the
  "Fold specs..." `walkforward.py` entry — since that is where it is actually persisted and
  rendered. No code change is required; this is a registration/documentation correction only.
- No other formatting drift, label inconsistency, or duplicate-home issue was found in this
  iteration's diff.
