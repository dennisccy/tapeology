# Iteration 5 — Coherence Audit

**Iteration:** goal-referee-iter-5
**Date:** 2026-08-15
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

This iteration is backend-only (J-04, matched nulls). It fills in the field-level shape of two rows
already registered in `runs/goal-session-referee/state/blueprint.md` at baseline (owner/endpoint
unchanged) plus one internal library-function fix that the blueprint itself explicitly excludes from
the Data Contract.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Matched-null records (`referee-null-tod-v1` / `referee-null-context-v1`) | OK | Owner `apps/backend/app/research/referee_null.py::build_null_record` (new file, L429-600); served only by `GET /research/desk/referee/nulls` in `apps/backend/app/research/referee_routes.py:96-107`. Matches blueprint row exactly — same module, same endpoint, no second path. |
| Null compute progress + runs | OK | Owner `referee_null.py::RefereeNullComputeManager`/`RefereeNullRunStore` (L718-1054); served by `POST/GET /research/desk/referee/nulls/compute`, `POST /nulls/compute/cancel`, `GET /nulls/runs` in `referee_routes.py:109-193`. Single compute-manager singleton (`referee_routes.py:66`), single run-store. |
| Anchor measurement value | OK (reuse, not duplication) | `referee_null.py:417` calls the imported `desk_forward._measure_from` directly; `referee_null.py:418` calls the imported `referee_evidence._resolve_leaf` for horizon/MDD extraction — zero local reimplementation of either. Confirmed zero diff to `desk_forward.py` (file not in the changed-file list). |
| Backing-bucket / band membership | OK (reuse, not duplication) | `referee_null.py:538-539` calls the imported `desk_playbook_context.band_context_block` over the resolver's recorded map; zero diff to `desk_playbook_context.py` (file not in the changed-file list; import-only addition per `referee_routes.py`'s own docstring). |
| Anchor draw (`_draw_anchor_indices`) | OK (reuse, not a second rail) | `referee_null.py:553` calls the imported `desk_forward._draw_anchor_indices`. `referee_stats.py`'s own separate `_draw_indices_without_replacement` is pre-existing (iteration 3), unchanged this iteration, and is a deliberately import-decoupled copy documented in the iter spec's own NOTES (stats core carries a stricter, estimand-agnostic import ban) — not a new duplicate-computation introduced by this diff. |
| `permutation_test`'s `min_attainable_p` | OK — not a Data Contract value | `apps/backend/app/research/referee_stats.py:558-570` (the fix: `2.0 if use_enumeration else 1.0) / (draws_used + 1)`). Internal field of a library function with no route of its own; the blueprint's own iter-5 note explicitly states this is not a Data-contract addition. No second implementation exists anywhere else. |
| Non-finite guard (`_require_finite_values`/`_require_finite_session_groups`) | OK | New helpers in `referee_stats.py:293-323`, called once at each public entry point (`_t_statistic`, `bootstrap_ci_occurrence`, `bootstrap_ci_cluster`) — a validation guard, not a value computation; no duplication risk. |

Field-shape check against the blueprint's iter-5 note (`state/blueprint.md:88-105`): every field the
note lists for the null record (`null_record_id`, `null_spec_id`, `null_spec_signature`,
`observation_id`, `symbol`, `session_date`, `side`, `tod_bucket`, `k_requested`, `k_drawn`,
`eligible_count`, `excluded`, `anchors[]` with its five sub-fields, `mean_window_overlap`,
`non_finite_excluded_count`, `backing_bucket_eligibility_rate`, `context_algorithm_version`,
`provenance`) is present verbatim in `build_null_record`'s two return shapes
(`referee_null.py:475-494` and `:581-600`). No extra, unregistered top-level field found.

No new displayed value was introduced outside the two already-registered rows. No new UI surface
exists this iteration to check for a non-canonical fetch (frontend diff is empty — see IA check
below).

## Information Architecture check

The iter spec (`docs/phases/goal-referee-iter-5.md` — Frontend section, "New user-facing capability,"
"New information displayed," "New user actions," "UI surface changes" all say "None") and the actual
diff agree: zero frontend files changed. Verified directly:

```
$ git status --porcelain | grep -iE "frontend|\.tsx|\.jsx|apps/web"
no frontend files touched
```

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `GET/POST /research/desk/referee/nulls*` (new backend endpoints) | OK — not yet a UI-facing feature | No page consumes these routes this iteration (by design). Blueprint's own IA row for J-04 (`state/blueprint.md:36`) names its canonical home as `/desk` → **Referee Runs**, explicitly landing in J-09, not this iteration. The iter spec's "Blueprint conformance" section confirms: "The Referee Runs section itself renders in J-09; this iteration only builds what J-09 will read." Nothing to navigate to yet — not a hidden-feature violation, since there is no new user-reachable surface to hide. |

No nav/sidebar/router file was touched (none of `app/meta.py`'s `UI_ROUTES`, any `Sidebar`/`Nav`
component, or frontend route config appear in the diff). No parallel shell, no duplicate home, no
new page was introduced.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- Minor enum-vs-implementation nuance in the blueprint's own iter-5 note (`state/blueprint.md:98-100`):
  the note documents the run-ledger record's `state` field as
  `"running"|"completed"|"failed"|"cancelled"`, but `RefereeNullRunStore.record()`
  (`referee_null.py:783-812`) enforces `_TERMINAL_STATES = ("completed", "failed", "cancelled")` and
  raises on anything else — the persisted ledger record can never actually carry `"running"` (writes
  are terminal-state-only, matching every other shipped compute-manager log in this codebase). The
  in-flight indicator lives in a differently-named `status` field on `RefereeNullComputeManager`'s
  own snapshot (values `idle`/`running`/`cancelling`/`done`/`error`), served by the separate
  `GET /nulls/compute` endpoint. This is not a coherence violation — there is exactly one writer and
  one shape for each of the two values, and the two fields are named differently so they cannot be
  confused with each other — just a documentation enum broader than what the code can produce. Worth
  a one-line correction to the blueprint note next time it's touched; does not block this iteration.
