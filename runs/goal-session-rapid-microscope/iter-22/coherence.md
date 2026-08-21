# Iteration 22 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-22
**Date:** 2026-08-21
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

Registered Data Contract row touched this iteration: "Scout trials, kills, denominators, screens" /
"Fold specs, folds, sequences, decay view" (owner `scout.py` + `scout_ledger.py` + `walkforward.py`,
served by `GET /research/desk/micro/scout` / `GET /research/desk/micro/walkforward`,
`blueprint.md` lines 56-57). This iteration adds Studies 1 (range-wall failed aggression) and 3
(capitulation exhaustion) as new families/rows inside that already-registered row, exactly the
precedent the blueprint's own iter-21 note recorded for Study 2 (blueprint.md lines 299-326,
iter-22 note lines 328-342).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Scout screen decision (Study 1, `failed_aggression_score`/`band_touch`) | OK | `apps/backend/app/research/scout.py:174-188` (`pilot_study_candidate_grid`, `_PILOT_GRID_SELECTORS`) feeds the SAME `register_and_screen_candidate`/`register_screen_and_walkforward_check` functions Study 2 already uses (unchanged this iteration; called from `apps/backend/tests/test_scout.py:487-495`) |
| Scout screen decision (Study 3, `failed_aggression_score`/`playbook_signal`/`capitulation`) | OK | Same functions, same call path — `apps/backend/tests/test_scout.py:536-545` |
| Walk-forward floor-check row (both new studies) | OK | `ScoutComputeManager.trigger` (`apps/backend/app/research/scout.py:1921-2000`) and CLI `main()` (`apps/backend/app/research/scout.py:2126-2153`) both funnel into the SAME `run_scout_grid_and_record` (unchanged this iteration, called at `scout.py:2020-2024` from the manager's `_work()` and at `scout.py:2151-2153` from the CLI) — one canonical execution path regardless of entry point (route vs. CLI) |
| Grid-selector routing table (`selector -> (study_id, structure_context.kind)`) | OK (advisory, see notes) | `apps/backend/app/research/scout.py:184-188` (`_PILOT_GRID_SELECTORS`, canonical) vs. `apps/backend/app/research/micro_routes.py:41-44` (`_BAND_TOUCH_PILOT_SELECTORS`/`_PLAYBOOK_SIGNAL_PILOT_SELECTORS`, a second hand-maintained encoding of the same classification — not a displayed value, so not a Data Contract violation; see Advisory notes) |
| PlaybookStore construction in `trigger_scout_compute` | OK | `apps/backend/app/research/micro_routes.py:297` reuses the pre-existing `desk_routes.get_playbook_store` dependency (imported since before this iteration, `micro_routes.py:47`, already used by the readiness/walk-forward routes) — not a second, independently-constructed store |

No new displayed field was introduced (iter spec's own "New information displayed: No new field"
claim, confirmed against the diff — only new ledger *rows* under already-registered fields). No new
endpoint was added; `POST /research/desk/micro/scout/compute`'s `grid` parameter gained two
additive string values, matching the already-approved `GRID_SELECTOR_DELTA_DIVERGENCE_PILOT`
precedent and the `observer=` kwarg precedent the blueprint cites for non-displayed request
parameters.

## Information Architecture check

Zero frontend files changed this iteration (`git diff --stat` against the snapshot SHA shows only
`apps/backend/app/research/micro_routes.py`, `apps/backend/app/research/scout.py`, and
`apps/backend/tests/test_scout.py` — confirmed against `reports/phase-goal-rapid-microscope-iter-22-ui-surface-map.md`'s
own "Frontend surfaces changed: 0 files" line). The blueprint's IA table already names the canonical
home for this feature: "Pilot studies (J-09) | `/desk` → Scout Ledger / Walk-Forward (results
render through J-08's sections, no new page) | Desk" (blueprint.md line 43). Studies 1 and 3 render
through that same already-shipped generic table with no UI code change, exactly as the iter spec's
"Frontend: No new component or section" states.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Study 1 / Study 3 pilot results on `/desk` Scout Ledger + Walk-Forward | OK | No nav file change needed — feature lands in its pre-existing IA home (blueprint.md line 43); zero component diff confirmed via `git diff --stat` |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `apps/backend/app/research/micro_routes.py:41-44` defines `_BAND_TOUCH_PILOT_SELECTORS` /
  `_PLAYBOOK_SIGNAL_PILOT_SELECTORS` as literal frozensets that duplicate the
  `selector -> structure_context.kind` classification already encoded in
  `apps/backend/app/research/scout.py:184-188`'s `_PILOT_GRID_SELECTORS` dict, rather than deriving
  the split programmatically from that one table. This is not a Data Contract violation (it routes
  which dependency to construct, not a displayed value, and a future mismatch would raise a loud
  `ValueError` in `ScoutComputeManager.trigger`, not silently diverge two numbers) — but it is a
  second hand-maintained encoding of the same fact, worth collapsing into one lookup (e.g. derive
  the route's two frozensets from `scout._PILOT_GRID_SELECTORS` by filtering on `kind`) the next
  time this table changes, so a fourth pilot study can't be added to one table and forgotten in the
  other.
