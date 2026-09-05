# Phase goal-observation-contract-iter-6 — UI Surface Map

**Phase:** goal-observation-contract-iter-6
**Date:** 2026-09-05
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

No frontend file changed this iteration (confirmed empty `git status --porcelain` under
`apps/frontend/`). Every row below is a **re-verification** surface, not a modified one: this
iteration's own plan (`runs/goal-observation-contract-iter-6/plan.md`, "UI Evolution") states the
audit answer is fixed to "no user-facing capability introduced," and the rows exist because the
full-depth regression sentinel (J-06) and the J-02/J-04 evidence-closure work both require
actually re-exercising these surfaces, not just inspecting a diff.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `http://localhost:8301/tape/{ticker}/observation` (backend origin — machine-only JSON, not a Next.js page) | Served `TapeObservation` v1 JSON body | Re-verified only — zero code change, shipped in iteration 5 | Closes the J-04 evidence gap left open by iteration 5 (deterministic replay cannot reach a backend-only path) | Watch `SIM-BIDABS` to `live` on `/`, click the amber "Pause" button, then open `http://localhost:8301/tape/SIM-BIDABS/observation` and reload it once more while still paused. Verify `observation_hash` is byte-identical on both loads while `generated_at_utc` and `artifact_hash` each differ between the two |
| `http://localhost:8301/tape/{ticker}/observation` | Served JSON — the three time fields (`observed_at_utc`, `available_at_utc`, `availability_basis`) plus `timing.settled_at_utc`, `generated_at_utc` | Re-verified only — zero code change | Closes the J-02 evidence gap (iteration 5's evidence was borrowed from a screenshot filed under J-01's test id, not J-02's own numbered steps) | Watch `SIM-BIDABS` to `live`, open `http://localhost:8301/tape/SIM-BIDABS/observation`, and independently record and file (under J-02's own evidence, not J-01's) the values of `observed_at_utc`, `available_at_utc`, `availability_basis`, `timing.settled_at_utc`, `generated_at_utc`. Verify `observed_at_utc` starts with `2024-01-02T14:3`, `available_at_utc` is `null`, `availability_basis` reads `simulated_not_applicable`, and both `timing.settled_at_utc` and `generated_at_utc` carry today's real-world date |
| `http://localhost:8301/tape/ZZZZ/observation` | Served JSON — 404 error body | Re-verified only (regression, J-05) | Whole-product sentinel confirms the one-canonical-path guarantee still 404s for an unwatched ticker | Open `http://localhost:8301/tape/ZZZZ/observation` directly (no watch started for `ZZZZ`). Verify the response body reads `{"detail":"Ticker 'ZZZZ' is not being watched"}` — the same shape as `http://localhost:8301/tape/ZZZZ/state` — not a 200 response or a crash |
| `/` (Cockpit) | "Data source" control group, "Ticker" field, "Watch"/"Pause"/"Resume"/"Stop" buttons | Unchanged (regression only, J-06) | Whole-product regression sentinel requires confirming no new panel, link, or control was introduced anywhere on the existing pages | Navigate to `http://localhost:3301/`. Verify the header reads "Tapeology", the "Data source" group still shows exactly three options ("Live", "Historical", "Simulated"), and no new button, panel, or link appears anywhere on the page compared to iteration 5 |
| `/structure` | Structure page (`<h1 data-testid="structure-title">Structure</h1>`) | Unchanged (regression only, J-06) | Whole-product regression sentinel | Navigate to `http://localhost:3301/structure`. Verify the heading reads "Structure" and no new panel, link, or control has appeared |
| `/desk` | Desk page (`<h1 data-testid="desk-title">Desk</h1>`) | Unchanged (regression only, J-06) | Whole-product regression sentinel | Navigate to `http://localhost:3301/desk`. Verify the heading reads "Desk" and no new panel, link, or control has appeared |
| Persistent top nav (all pages) | `NavBar` (`data-testid="app-nav"`), links rendered from `GET /meta/ui-routes` | Unchanged (regression only) | Whole-product sentinel implies the new machine-only observation route must add zero nav entry | On any page, verify the top nav shows exactly three links — "Cockpit", "Structure", "Desk", in that order — and that none of them points to `/tape/*/observation` (the observation route has, and must keep, zero nav entry) |

<!-- Change Type key for this iteration: every affected surface is "Re-verified only" or
     "Unchanged (regression only)" — no row is a New page/component/form/table/modal, because
     this iteration's Anti-goal reminders explicitly forbid any such addition. -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_tape_observation_guards.py` (new, 649 lines, 21 tests, 0 failed) — five
  structural guard mechanisms (copy-discipline + compound-identifier ban, external-system
  reference guard, English-only guard, real-provider isolation guard, mutator-call-site guard),
  each shipping its own `test_counterexample_*` proof. Runs only inside the backend's automated
  pytest suite (`cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_guards.py -q`)
  — no endpoint, page, panel, or MCP tool exposes it; no UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 1 (new test module)
