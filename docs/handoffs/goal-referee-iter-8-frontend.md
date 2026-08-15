# goal-referee-iter-8 Frontend Handoff

**Phase:** goal-referee-iter-8
**Date:** 2026-08-15
**Agent:** developer
**Status:** complete

## What Was Built

The **first-ever Referee UI** on `/desk` — Era 6's machinery had been backend-only/keyless
through J-01–J-06; this iteration is the first time the operator can see and act on it in the
browser.

- **A new "Referee Registry" `CollapsibleSection`**, rendered directly below the shipped
  "Playbook Evidence" section (the previous last section on the page). Closed by default, like
  every other collapsed section on this page; its own read is deferred until first expand.
- **The shortlist table** (5 rows, always rendered — spec §7's five pinned candidates, S-1
  through S-5): candidate id, estimand, setup/side (with the context bucket in parentheses for
  B/C candidates), primary horizon, a plain-language rationale sentence, and four live readiness
  numbers (`n`, sessions, accrual rate per day, projected days to target) served verbatim by the
  backend — no client-side arithmetic anywhere on this page derives any of them.
- **The select → confirm → submit registration flow**: clicking "Select" on a shortlist row
  opens a distinct confirmation panel naming the candidate and stating that registration is
  permanent; "Confirm Registration" submits the real `POST .../registry/hypotheses` act with
  `confirm: true`; "Cancel" discards the selection. An in-flight submit disables both buttons and
  shows "Registering…"; a refused submission (422 malformed/duplicate spec id, 409 duplicate
  hypothesis/family id) surfaces the backend's own `detail` text inline, never a silent failure.
  On success, the registry is re-fetched so the new row renders complete with its
  status/accrual/discovery fold (which the POST response itself does not carry).
- **The registered-hypotheses table**: hypothesis id, setup/side, boundary
  (`confirmation_start_boundary`), origin, status, the accrual pair
  (`informative_post_boundary_sessions / target_sessions`), and the discovery pair
  (`n / n_sessions`) with its own served `"discovery (exploratory)"` label rendered as plain
  italic text beside it — visibly distinct from accrual, and never a colored badge (this
  section is a lab notebook, not a scorecard, per the Design Direction).
- **The honest `"No hypotheses registered."` empty state** when the registered-hypotheses table
  has zero rows (the shared `EmptyState` component, matching every other empty state on this
  page).
- **A shortlist row for an already-registered candidate** shows a disabled "Registered" button
  in place of "Select" — a client-side inference from the two already-fetched payloads (no new
  backend field), so a re-selection attempt cannot even reach the confirm panel; the backend's
  own 409 refusal still exists as the honest fallback if the client's view is stale.

## New user-facing capability

The operator can, for the first time, open `/desk`, expand "Referee Registry", see the Referee's
five pre-registered candidate research questions with live sample-size readiness and rationale,
and register one directly through an explicit confirm step — producing a permanent,
boundary-stamped hypothesis they can then see listed with its own accrual and discovery counts.

## New information displayed

- The five spec-pinned shortlist candidates: estimand, setup/side, primary measure/horizon,
  rationale sentence, live `n`/`n_sessions`/accrual-rate/projected-days-to-target.
- After registration: that hypothesis's boundary date, target session accrual, and
  `historical-exploration` origin.
- The `discovery (exploratory)` label on a registered hypothesis's pre-boundary historical
  numbers, visibly distinct from its post-boundary `accrual` numbers.

## New user actions

Select a shortlist candidate → review its live readiness → complete an explicit confirmation
step → submit the registration. Cancel is available at the confirmation step.

## UI surface changes

One new "Referee Registry" `CollapsibleSection` on `/desk`, rendered below every shipped
section. No existing section, column, or behavior changed anywhere else on the page — verified
by running the full guard-test suite (`test_desk_ui_guards.py`, `test_desk_refresh_chain_guard.py`)
green, and by a manual `curl` check that every previously-shipped route still returns 200.

## Navigation changes

None. Nav stays exactly Cockpit `/` / Structure `/structure` / Desk `/desk`; no new route.

## Component patterns used

- `Panel` + `CollapsibleSection` (`apps/frontend/components/CollapsibleSection.tsx`) — the exact
  wrapper every other `/desk` section already uses; no new wrapper component was written.
- Plain dense `<table>` markup (no `useTableSort`/`SortableHeader` framework) — the shortlist has
  a fixed 5 rows and the registered-hypotheses table is expected to stay small (2–3 rows this
  era), so sorting was judged unnecessary scope for this iteration; this matches the house
  style's own "tables and text, no dashboard cards/gauges" description.
- `PRIMARY_BUTTON_CLASS`/`CANCEL_BUTTON_CLASS` (the page's own existing Tailwind constants) for
  every button — Select, Confirm Registration, Cancel — no new button styling was invented.
- `LoadingPanel`/`UnavailablePanel`/`EmptyState` (the page's own existing shared components) for
  every degraded/empty state.

## States handled

- **Loading**: `LoadingPanel` (`referee-registry-loading`) while the two deferred fetches
  (shortlist + registry) are in flight.
- **Unavailable**: a dedicated `UnavailablePanel` for a failed shortlist fetch
  (`referee-shortlist-unavailable`) and, independently, for a failed registry fetch
  (`referee-hypotheses-unavailable`) — the two reads degrade independently rather than an
  all-or-nothing gate.
- **Empty**: `"No hypotheses registered."` when the registry has zero hypotheses (the shortlist
  itself is never empty — it always renders its 5 pinned rows, even against an all-zero-readiness
  corpus, since the candidate list is static and only the readiness numbers vary).
- **Selected / awaiting confirmation**: the distinct confirm panel, `data-testid=
  "referee-registration-confirm-panel"`, present only while `selectedCandidateId` is set.
- **Submitting**: both confirm-panel buttons disabled, label reads "Registering…".
- **Refused**: an inline red error line (`referee-registration-error`) carrying the backend's
  own refusal text verbatim (422 malformed/duplicate spec id, 409 duplicate id).

## data-testid inventory (all new, none reused — T-11)

`referee-registry-section`, `referee-registry-loading`, `referee-shortlist-unavailable`,
`referee-shortlist-table`, `referee-shortlist-row-{candidate_id}`,
`referee-shortlist-select-{candidate_id}`, `referee-registration-confirm-panel`,
`referee-registration-confirm-button`, `referee-registration-cancel-button`,
`referee-registration-error`, `referee-hypotheses-unavailable`, `referee-hypotheses-empty`,
`referee-hypotheses-table`, `referee-hypotheses-row-{hypothesis_id}`,
`referee-discovery-{hypothesis_id}`. The `CollapsibleSection` wrapper itself additionally
contributes `desk-section-expand-refereeRegistry`/`desk-section-body-refereeRegistry` (its own
existing, generic `id`-based naming — no collision with any shipped section's `id`).

## Verification performed

- `node_modules/.bin/tsc --noEmit -p tsconfig.json` — exit code 0, zero TypeScript errors.
- `tests/test_copy_discipline.py::test_lint_frontend_source_literals_are_clean` — green; every
  new string literal (rationale sentences, table headers, the confirm-step sentence, the empty
  state) is clean.
- `tests/test_desk_refresh_chain_guard.py` — green; effect count unchanged at 19 (zero new
  `useEffect` calls were introduced — the section's reads ride the existing `toggleSection`
  deferred-fetch handler, and registration is a plain async `onClick` handler).
- `tests/test_desk_ui_guards.py` — green, including the new counter-test proving the extended
  `_PRICE_ARITHMETIC_FIELDS` pattern genuinely fires on a seeded violation of every new field
  this section reads, and does not over-match the actual "X / Y" display idiom in use.
- Live smoke test against `scripts/dev.sh` (backend :8301, frontend :3301): `GET /desk` returns
  200; `GET /research/desk/referee/registry/shortlist` returns the 5 pinned candidates;
  `GET /research/desk/referee/registry` returns the honest empty state against the real
  (untouched) store.
- **Not performed by this agent**: a real Chrome-driven walkthrough of the select → confirm →
  submit flow, or the T-9 `rm -rf apps/frontend/.next` clean-rebuild browser pass — that is the
  browser-qa-agent's job (TC-3/TC-4/TC-5/TC-12) and is expected to run next in the pipeline.
