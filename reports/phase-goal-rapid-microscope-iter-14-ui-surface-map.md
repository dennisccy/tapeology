# Phase goal-rapid-microscope-iter-14 — UI Surface Map

**Phase:** goal-rapid-microscope-iter-14
**Date:** 2026-08-19
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | Scout Ledger section (`data-testid="scout-ledger-section"`; expand control `data-testid="desk-section-expand-scoutLedger"`) | New section | Renders `GET /research/desk/micro/scout` verbatim — first-ever UI surface for the Scout ledger | Navigate to `http://localhost:3301/desk`, click the "Scout Ledger" header to expand it. Verify a "Ledger chain verification: ok" line appears, and either at least one family block (heading `"<family_id> — N variants tried"` followed by a 9-column table: Candidate / Feature / Horizon / Registered / Decision / Reason / Notes / Withheld excluded / Screen detail) or the empty state "No candidates ledgered." renders — the real backend has zero families today, so expect the empty state. |
| `/desk` | Scout Ledger "Run Screen" compute control (`scout-ledger-trigger`, `scout-ledger-progress`, `scout-ledger-cancel`) | New control | Lets an operator start/cancel a Scout screening run from the page instead of curl/CLI (TC-7) | With Scout Ledger expanded, click the "Run Screen" button. Within ~1 second verify the button's own label changes to "Screening…" and becomes disabled, a line reading "0 / 6 candidates" appears, and a "Cancel" button appears. Do NOT wait for completion in a smoke pass — this starts a real, 25+ minute computation against the live corpus (see `reports/phase-goal-rapid-microscope-iter-14-ui-test-plan.md` UT-06 for the long-running follow-through). |
| `/desk` | Scout Ledger Run History table (`scout-ledger-runs-table` / `scout-ledger-runs-empty`) | New table | Surfaces `GET /research/desk/micro/scout/runs` | With Scout Ledger expanded, verify a "Run History" sub-heading and either a 6-column table (Run / State / Started / Finished / Candidates / Error) or "No scout runs recorded yet." renders below the families block. |
| `/desk` | Walk-Forward section (`walk-forward-section`; expand control `desk-section-expand-walkForward`) | New section | Renders `GET /research/desk/micro/walkforward` verbatim — first-ever UI surface for the walk-forward ledger | Navigate to `http://localhost:3301/desk`, click "Walk-Forward" to expand. Verify a "Fold Specs" block with at least one `corpus_id` detail row, and at least one sequence block showing a "Sequence verdict:" line plus an 8-column fold table (Fold / Status / Effect / N / Sessions / Sign / Evidence class / Process label) and a "Recency —" summary line — the real backend has a non-empty Walk-Forward ledger today, so expect populated content, not the empty state. |
| `/desk` | Walk-Forward "Run Walk-Forward" compute control (`walk-forward-trigger`, `walk-forward-progress`, `walk-forward-cancel`) | New control | Lets an operator start/cancel a walk-forward diagnostic run from the page (TC-8) | With Walk-Forward expanded, click "Run Walk-Forward". Within ~1 second verify the label changes to "Running…" and becomes disabled, a line reading "0 / N steps" appears, and a "Cancel" button appears. Do NOT wait for completion in a smoke pass — this is a real, long-running computation. |
| `/desk` | Walk-Forward Run History table (`walk-forward-runs-table` / `walk-forward-runs-empty`) | New table | Surfaces `GET /research/desk/micro/walkforward/runs` | With Walk-Forward expanded, verify a "Run History" sub-heading and either a 7-column table (Run / State / Started / Finished / Steps / Folds evaluated / Error) or "No walk-forward runs recorded yet." renders. |
| `/desk` | Walk-Forward empty-sequences state (`walk-forward-sequences-empty`) | Copy bug (MINOR, code-review-flagged) | Reuses Scout's "No candidates ledgered." title instead of sequence-appropriate wording (`page.tsx:6431`) | Not independently exercisable live today — the real Walk-Forward ledger is non-empty, so this branch cannot render on the running app. Confirmed by reading the source: the `EmptyState` `title` prop for `walk-forward-sequences-empty` is still the literal string `"No candidates ledgered."` |
| `/desk` | Validation Vault section (`validation-vault-section`; expand control `desk-section-expand-validationVault`) | New section, read-only | Renders `GET /research/desk/micro/vault` verbatim; no compute/seal/assign/expose control anywhere by design | Navigate to `http://localhost:3301/desk`, click "Validation Vault" to expand. Verify "No shards recorded." and "No universes registered." both render (real vault store is empty today), plus two lines "Shard ledger chain verification: ok" and "Universe ledger chain verification: ok". Confirm no button of any kind exists anywhere inside `[data-testid="validation-vault-section"]`. |
| `/desk` | Scout family header omission of `family_root_id` (MINOR, code-review-flagged, `page.tsx:6197`) | Known gap | Phase spec's own "New information displayed" list names `family_root_id` for Scout rows; it is never rendered | Not independently exercisable live today — the real Scout ledger has zero families, so there is no family row to inspect. Confirmed by reading the source: the family header interpolates only `family.family_id` and `family.variants_tried`. |
| `/desk` | `toggleSection` fetch-on-first-expand wiring for all 3 new sections | Changed behavior (internal, additive) | Each section's GET fires exactly once, on first expand, guarded by a ref so re-collapsing/re-expanding never re-fetches | Expand "Scout Ledger", collapse it (click the header again), then expand it a third time. Verify the content reappears instantly with no new loading skeleton — confirms no duplicate fetch fires on re-expand. |
| `/desk` | Backend-unreachable path for all 3 new sections (`scout-ledger-unavailable`, `walk-forward-unavailable`, `validation-vault-unavailable`) | New error state | Typed "could not be loaded" message per TC-14, never a blank panel or stale table | Stop the backend process, reload `http://localhost:3301/desk`, expand each of the 3 new sections. Verify each shows an amber panel with the text "Backend unreachable — is the API running?" plus the fixed line "Nothing cached and nothing fabricated is shown in its place." |
| `/desk` | Microscope Readiness section (pre-existing, `micro-readiness-section`) | Regression (unchanged) | Sits directly above the 3 new sections on the same page | Expand "Microscope Readiness" and verify its totals table, `data-testid="micro-readiness-shards-table"`, and floors table still render as before. |
| `/desk` | Referee Registry / Referee Adjudications / Referee Runs sections (pre-existing) | Regression (unchanged) | Sit above Microscope Readiness on the same page; share the same `CollapsibleSection`/`toggleSection` machinery this phase extended | Expand each of the three "Referee …" headers in turn and verify each still renders its own table/content without an error panel. |
| `/desk` | Screen Runs / Top-up Runs / Index Reconciliation / Playbook Evidence sections, plus the always-visible Playbook signal table (`desk-playbook-signal-row`) and its "Compute" control (`desk-playbook-compute-button`) (pre-existing) | Regression (unchanged) | Share the page and the same collapsible/state machinery this phase extended | Verify the main Playbook signal rows still render above the fold without expansion, and that each of the 4 named collapsible sections still expands to show its own content. |
| `/structure` | Comparison dropdown (`data-testid="comparison-dataset-select"`) + Tradable Map | Regression (unchanged, different route) | Confirms the `/desk`-only change did not affect a sibling route | Navigate to `http://localhost:3301/structure`, verify the page loads and the comparison dropdown is present and selectable. |
| `/` (Cockpit) | Live tape + chart | Regression (unchanged, different route) | Confirms the `/desk`-only change did not affect the home route | Navigate to `http://localhost:3301/`, verify the chart renders. If it looks static in a headless capture, cross-check against the backend payload before calling it a failure — headless Chrome's `visibilityState: "hidden"` is known to freeze this specific chart. |
| All pages | `NavBar` (`data-testid="nav-link"`, `data-label` of "Cockpit" / "Structure" / "Desk") | Regression (unchanged) | Nav must still show exactly 3 links — no new route was registered in `app/meta.py` `UI_ROUTES` | From any page, verify the top navigation shows exactly 3 links labeled "Cockpit", "Structure", "Desk" and no fourth link. |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_desk_ui_guards.py` — widened the `_PRICE_ARITHMETIC_FIELDS` allow-list
  to cover every new numeric binding the three sections introduce (`variants_tried`,
  `withheld_excluded`, fold/decay fields, compute-progress counters, universe rule sizes). This is
  a CI guard test that constrains what the frontend is allowed to compute client-side — it has no
  UI surface of its own and renders nothing to a user; it only widens what the guard permits,
  never loosens an existing check.
- `vault.py`, `scout.py`, `scout_ledger.py`, `walkforward.py`, `walkforward_ledger.py`,
  `micro_routes.py` — **not touched this iteration.** All four GET endpoints and both compute
  triples this phase's UI reads were already shipped and already tested in earlier iterations;
  this phase's entire job was wiring an existing, unmodified backend surface to a screen for the
  first time. Confirmed via `git status`/`git diff` showing zero changes to any of these files.

---

## Summary

- **Frontend surfaces changed:** 3 new sections on 1 existing route (`/desk`), plus their 2
  compute controls and 2 run-history tables
- **New pages/routes:** 0
- **Modified components:** 3 frontend files — `apps/frontend/app/desk/page.tsx` (widened section
  type union, 3 new inline components, 3 new `CollapsibleSection` blocks, extended `toggleSection`
  and new trigger/cancel/poll handlers), `apps/frontend/lib/types.ts` (new response/row types),
  `apps/frontend/lib/api.ts` (11 new fetch/trigger/cancel functions)
- **Navigation changes:** no
- **Backend-only changes:** 1 (guard-test allow-list widening; zero product-code backend files
  touched)
