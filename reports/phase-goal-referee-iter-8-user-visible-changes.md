# Phase goal-referee-iter-8 — User-Visible Changes

**Phase:** goal-referee-iter-8
**Date:** 2026-08-15
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Open `http://localhost:3301/desk`, scroll to the bottom, and click "Referee Registry" to expand
  a brand-new section listing the Referee's five pre-registered candidate research questions
  (S-1 through S-5) — the first Referee-era capability the operator can see or act on in the
  browser (previously this machinery was backend-only/keyless).
- See, for each of the five candidates, a plain-English rationale sentence plus four live
  readiness numbers — occurrence count (`n`), session count, accrual rate per day, and projected
  days until enough evidence has accrued — computed fresh from the real data store on every page
  load, never hardcoded. Verified live as of this writing: S-1/S-2/S-3 currently show `n=1`,
  `n_sessions=1`, an accrual rate of 0.02/day, and 517 projected days; S-4/S-5 currently show all
  zeros with "—" for projected days (a real zero-corpus case, not a placeholder).
- Select one of the five candidates (click "Select"), review an explicit confirmation panel
  naming the candidate and stating the action is permanent, then click "Confirm Registration" to
  submit a real, permanent write that boundary-stamps the hypothesis as of that moment.
- Cancel a pending selection before submitting by clicking "Cancel" in the confirmation panel —
  discards the selection with no write performed.
- View every registered hypothesis in a new "Registered Hypotheses" table showing its boundary
  date, origin (`historical-exploration`), status, its accrual progress (post-registration
  sessions / target), and — new this iteration — a separate "discovery (exploratory)" count of
  matching evidence that already existed *before* registration, rendered distinctly from accrual.
- See the honest message "No hypotheses registered." when nothing has been registered yet — which
  is the real, current state of the live app as of this writing (verified directly:
  `GET /research/desk/referee/registry` currently returns `"hypotheses": []`).

---

## What Changed in the Visible UI

- `/desk` gains one new collapsible section, "Referee Registry" — positioned as the new *last*
  section on the page, directly below the existing "Playbook Evidence" section. It is closed by
  default, like every other collapsible section on the page, and its data is not fetched until
  first expanded.
- Inside it, a new 5-row shortlist table (columns: Candidate, Estimand, Setup / Side, Primary,
  Rationale, n, Sessions, Accrual / day, Projected days, Action) always renders all five
  candidates, even the two (S-4, S-5) that currently have zero recorded evidence — those rows
  show "0.00" and "—" rather than a blank cell, "NaN", or a crash.
- A new confirmation panel appears below the shortlist when a candidate is selected (and
  disappears on Cancel or after a successful submit), and a new "Registered Hypotheses" table (or
  its "No hypotheses registered." empty state) renders below that.
- A registered hypothesis's row now shows two distinct evidence counts side by side — "Accrual"
  and "Discovery" — with the discovery count carrying the plain italic label
  "discovery (exploratory)", rendered as ordinary text, never a colored badge (this section reads
  as a lab notebook, not a scorecard).
- No existing page — Cockpit (`/`), Structure (`/structure`), or any of the other ten existing
  `/desk` sections — has any visible change; the top navigation bar is unchanged (still exactly
  "Cockpit" / "Structure" / "Desk", confirmed live via `GET /meta/ui-routes`).

---

## What Old Behavior Changed

None. This iteration is purely additive, confirmed both by the developer's own claim and by
direct inspection of the `apps/frontend/app/desk/page.tsx` diff: every change is a new import, a
new member on the `DeskCollapsibleSection` union, new module constants, new state hooks, one new
branch inside the existing deferred-fetch `toggleSection` handler, one new async handler function,
and one new `<section>` block appended after the page's previous last section. No pre-existing
line of rendered output, prop, label, or handler was modified.

---

## Not Visible Yet

- Two of the six readiness numbers the shortlist endpoint serves — `target_sessions` and
  `min_occurrences` — are present in the live API response for all 5 candidates (confirmed via
  direct query) but are not shown as their own columns anywhere in the UI. This was a deliberate
  scope-minimization call per the dev handoff, not an oversight; the numbers remain available in
  the served JSON for a future UI to surface.
- Rider 2's new `integrity_errors` key on `GET /research/desk/referee/adjudications` has no UI
  consumer this iteration — no page fetches `/adjudications` at all yet (that endpoint's UI is
  Journey J-09's scope, explicitly out of scope this iteration).
- Rider 1's write-side fix (a failed oracle attestation now stores an evaluation's `role` as
  `"pending"` instead of `"checkpoint"`, so it can never mint a hypothesis's one permanent
  adjudication snapshot) has no observable UI surface at all — there is no Referee Adjudications
  page/section yet where an operator could see an evaluation's role or status. This is a
  backend-only safety fix, verifiable only through the backend test suite.
