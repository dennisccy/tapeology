# Phase goal-referee-iter-8 — UI Surface Map

**Phase:** goal-referee-iter-8
**Date:** 2026-08-15
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|------------|------------|-------------|
| `/desk` | "Referee Registry" `CollapsibleSection` (`data-testid="desk-section-expand-refereeRegistry"`) | New section | First-ever Referee UI slice this era — the operator can now see and act on the Referee's registry from the browser instead of only via keyless backend tests | Navigate to `http://localhost:3301/desk`, scroll to the bottom, click the "Referee Registry" header; verify it expands (arrow glyph flips from "▸" to "▾") and sits directly below "Playbook Evidence" as the new last section |
| `/desk` | Shortlist table (`referee-shortlist-table`, rows `referee-shortlist-row-S-1`..`referee-shortlist-row-S-5`) | New table | Serves spec §7's five pinned candidates with LIVE sample-size readiness (TC-1) | With the section expanded, verify exactly 5 rows render with ids S-1 through S-5 in order, each showing a non-empty rationale sentence and numeric values in the n / Sessions / Accrual per day / Projected days columns |
| `/desk` | Zero-readiness shortlist rows S-4, S-5 (`range_trade:long`, `at_wall` context) | Changed behavior (edge case made visible) | Proves the divide-by-zero guard on `projected_days_to_target` (TC-2) renders honestly instead of crashing or showing garbage | Verify rows S-4 and S-5 show "0.00" in the "Accrual / day" column and an em dash "—" in the "Projected days" column — never blank, "NaN", or "Infinity" |
| `/desk` | "Select" button per shortlist row (`referee-shortlist-select-{candidate_id}`) | New control | Lets the operator begin the registration flow for one candidate | Click "Select" on the S-4 row; verify a confirmation panel appears below the table containing the exact text "Register S-4 (range_trade:long, Estimand B)?" |
| `/desk` | Confirmation panel (`referee-registration-confirm-panel`) with "Confirm Registration" / "Cancel" buttons | New panel | Explicit confirm-before-permanent-write gate — matches goal.md's own acceptance text for this journey | With the panel open, click "Cancel"; verify the panel disappears and the same row's button still reads "Select" (not "Registered") — confirms no write occurred |
| `/desk` | "Confirm Registration" button (`referee-registration-confirm-button`) → `POST /research/desk/referee/registry/hypotheses` | New write action | The core new capability this iteration ships: a real, permanent registration write producing a boundary-stamped hypothesis | Select an unregistered candidate, click "Confirm Registration"; verify the button briefly reads "Registering…", then a new row appears in the "Registered Hypotheses" table with that candidate's setup/side, a boundary date, and origin "historical-exploration" — this is an irreversible write against whichever registry store the running backend uses |
| `/desk` | "Registered Hypotheses" table (`referee-hypotheses-table`) and its empty state (`referee-hypotheses-empty`) | New table + empty state | Shows every permanently registered hypothesis, or the honest empty message when none exist | With zero hypotheses registered (the real live state as of this writing — verified via `GET /research/desk/referee/registry` returning `hypotheses: []`), verify the text "No hypotheses registered." renders in place of a table |
| `/desk` | Discovery cell (`referee-discovery-{hypothesis_id}`) inside the hypotheses table | New column | Distinguishes pre-registration ("discovery") evidence from post-registration ("accrual") evidence — makes the anti-goal rule "the historical atlas is exploratory forever" visible to the operator | After registering a candidate that already had matching historical signals (e.g. S-1, which currently shows `n=1` in the shortlist before registration), verify its row shows an "Accrual" count in a separate column from a "Discovery" count, with the italic label "discovery (exploratory)" beside the Discovery number |
| `/desk` | Inline registration error (`referee-registration-error`) | New error state | Backend refusals (422 malformed/duplicate, 409 conflict) must surface to the operator, never fail silently | Open Referee Registry in two browser tabs; in Tab A select a candidate and leave its confirm panel open; in Tab B select and confirm the SAME candidate (succeeds); back in Tab A click "Confirm Registration" on the now-stale panel; verify a red inline error line appears with the backend's own explanation text, and the page does not crash or blank out |
| `/desk` | "Playbook Evidence" section (pre-existing, now second-to-last) | Unchanged (regression surface) | A new section was inserted immediately below it — the surface most likely to show a layout regression if the insertion went wrong | Expand "Playbook Evidence" (the section directly above "Referee Registry"); verify it still renders its existing content exactly as before, with no visual shift or broken layout from the new section below it |
| `/desk` | Top navigation bar | Unchanged | No new route was added — confirmed live via `GET /meta/ui-routes` still returning exactly 3 entries | Verify the top nav still shows exactly "Cockpit", "Structure", "Desk" and no new link appeared |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/referee_adjudicate.py` — **Rider 1** (write-side attestation gate in
  `run_evaluation_and_record`): a failed oracle attestation now stores an evaluation's `role` as
  `"pending"` instead of `"checkpoint"`, so it never mints a hypothesis's one permanent
  adjudication snapshot. No UI surface exists yet (there is no Referee Adjudications
  page/section) where an operator could observe a `role` or `status` value — this is a
  backend-internal safety fix, verified only by the backend test suite (TC-7).
- `apps/backend/app/research/referee_adjudicate.py` — **Rider 2** (`integrity_errors` on
  `adjudications_response()`): `GET /research/desk/referee/adjudications` now discloses
  corrupted hypothesis files instead of silently dropping them. Confirmed by direct search: no
  frontend file calls this endpoint. Classified "not visible yet" per the diff-to-ui-impact
  skill's inference rule (new backend-api change, zero frontend consumption found) — this
  endpoint's UI is Journey J-09's scope.
- `apps/backend/tests/test_referee_registry.py`, `test_referee_adjudicate.py`,
  `test_desk_ui_guards.py` — test-only files; no UI surface.
- `runs/goal-session-referee/state/assumptions.md`, `telemetry.jsonl`, `trace/trace.jsonl` —
  pipeline process/bookkeeping files; no UI surface.

---

## Summary

- **Frontend surfaces changed:** 1 (the new "Referee Registry" section — containing 2 tables, 1
  confirmation panel, 3 distinct button behaviors, 1 empty state, 2 unavailable states, 1 loading
  state)
- **New pages/routes:** 0 (added to the existing `/desk` page; no new route)
- **Modified components:** `apps/frontend/app/desk/page.tsx` (2 new components:
  `RefereeRegistrySection`, `RefereeHypothesesTable`); `apps/frontend/lib/api.ts` (3 new
  functions: `fetchRefereeShortlist`, `fetchRefereeRegistry`, `postRefereeRegistryHypothesis`);
  `apps/frontend/lib/types.ts` (10 new types, the project's first-ever referee type bindings)
- **Navigation changes:** no
- **Backend-only changes:** 2 (Rider 1, Rider 2 — both in `referee_adjudicate.py`)
