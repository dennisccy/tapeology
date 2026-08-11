# Iteration 7 — Coherence Audit

**Iteration:** goal-playbook-iter-7
**Date:** 2026-08-11
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Back-scan plan (`backscan_plan`) | OK | Computed by `plan_backscan` in `apps/backend/app/research/desk_playbook_backscan.py:1136-1170` (new file); wired to its registered endpoint at `apps/backend/app/research/desk_routes.py:72-87` (`GET /research/desk/playbook/backscan/plan`), exactly matching the blueprint row (`runs/goal-session-playbook/state/blueprint.md:113`). |
| Back-scan progress + ledger (`backscan_compute` / `backscan_runs`) | OK | Computed by `DeskPlaybookBackscanComputeManager` + `BackscanRunStore`, same module (`desk_playbook_backscan.py:429-563`, `:225-401`); wired to the registered trio `POST/GET/POST-cancel /research/desk/playbook/backscan/compute` and `GET .../backscan/runs` (`desk_routes.py:99-157`), matching blueprint row `runs/goal-session-playbook/state/blueprint.md:114`. |
| Playbook records / measurement rail (unchanged owner) | OK — no re-implementation | `run_backscan` (`desk_playbook_backscan.py:1176-1219`) calls the ONE existing shared entry point `run_playbook_and_record` (imported from `.desk_playbook_compute` at `desk_playbook_backscan.py` top-of-file import, invoked `desk_routes.py` nowhere directly — only inside the walker) — no second detect/measure/record path. `plan_backscan` resolves the signature via the existing `compute_playbook_input_signature` (imported from `.desk_playbook`, `desk_playbook_backscan.py` imports block), never re-derived. Session honesty (`refuse_if_not_a_session`) is exercised only transitively inside `run_playbook_and_record`; `plan_backscan` deliberately never calls `desk_sessions.recorded_session_dates` (module docstring, `desk_playbook_backscan.py:944-957`), avoiding a second, cheaper-but-divergent session classifier. |
| `desk_playbook_detect.py` (range-trade fail-closed clause) | OK — zero source diff | Only `apps/backend/tests/test_desk_playbook_detect.py` gained a new test (`iter-diff.md:171-215`, the short-side mirror, TC-12); no change to `apps/backend/app/research/desk_playbook_detect.py` itself, matching the iteration's own "zero diff maintained" constraint. |
| Served numerics (`plan.total`/`missing`, `compute.planned_total`/`completed`, `outcomes.*`) | OK — reformat only | `apps/backend/tests/test_desk_ui_guards.py` extends `_PRICE_ARITHMETIC_FIELDS` to cover these new fields (`iter-diff.md:284-301`), mechanically guarding against client-side arithmetic; the new components (`BackscanOutcomeCounts`, `BackscanPlanPreview`, `BackscanControl` in `apps/frontend/app/desk/page.tsx`) only pass these fields through `fmt()` for display, no derivation. |

No new displayed value is missing from the Data Contract — every field rendered by the new panel (`plan.dates[].status`, `plan.total`, `plan.missing`, `compute.status/from/to/planned_total/completed/outcomes/current_date/error`, each `run.*` field) is an exact match to the two rows' documented shapes in `docs/phases/goal-playbook-iter-7.md`'s "Data-contract additions" section and the blueprint.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Backscan panel | OK | New `<section aria-label="Backscan">` added to the existing `/desk` route, directly below the shipped "Playbook Signals" section and inside the page's existing `<main>`/`Panel` shell (`apps/frontend/app/desk/page.tsx` diff, added lines ending `... </main>` per `git diff`-derived excerpt around the new section). No new route, no new top-level nav entry. Nav is data-driven from `app/meta.py` `UI_ROUTES` (blueprint.md:39) — that file is untouched in this diff (not among the 11 changed files), so the 3-row nav (Cockpit/Structure/Desk) is unchanged and the panel is reachable via the existing "Desk" nav link (1 click) + scroll — well within the ≤2-click bar. |
| No duplicate home | OK | The panel is not a second home for any existing entity — it is the pre-planned "Backscan" slot the blueprint's Information Architecture already reserved (`runs/goal-session-playbook/state/blueprint.md:59-60`), and the iteration spec's own "Blueprint conformance" field cites the exact same slot (`docs/phases/goal-playbook-iter-7.md:172-176`). |
| No parallel shell | OK | The section reuses the existing `Panel` component and page layout conventions (`<Panel title="Backscan">`, same button/table classes as `DeepBackfillControl`/`TopupRunsTable`) rather than introducing its own layout. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. (Minor stylistic note, not worth a WARN: the panel label is "Backscan" — one word, no hyphen — per the blueprint's own IA slot name, while prose elsewhere in the spec and module docstrings uses "back-scan" hyphenated. This is the decomposer's own established convention from earlier in the session, not new drift introduced by this iteration.)
