# Phase goal-rapid-microscope-iter-6 — UI Surface Map

**Phase:** goal-rapid-microscope-iter-6
**Date:** 2026-08-17
**Written by:** ui-impact-analyst

---

**Reading this map:** this iteration's diff touches zero frontend files. Every row below is a
**pre-existing, unmodified surface** the browser-QA lane must re-verify only because
`Frontend Present: yes` finally unblocks it after two consecutive silent skips (iter-4, iter-5) —
not because this iteration changed any of them. There is no new UI surface to map; inventing one
would misrepresent the diff. Two groups of rows exist for two different reasons:

1. **J-01's overdue evidence** — the Microscope Readiness section on `/desk` has an open
   `evidence_makeup` flag (journey-history.json) because no real, non-fabricated screenshot has
   been captured in 2 iterations. This iteration's own DEFINITION OF DONE (TC-8) requires closing
   it.
2. **J-10's kept-product sentinel** — `journey-scripts/J-10.json`'s 13-step walk (cockpit →
   `/structure` → several `/desk` sections) has never completed a browser run this era. It is
   reused byte-unmodified this iteration; the rows below decompose its 13 steps by surface.

J-02, J-03, and J-04 (the other required-still-passing journeys) have **no dedicated UI element of
their own** — confirmed directly in `runs/goal-session-rapid-microscope/state/journey-history.json`:
J-02 is explicitly "No browser surface (keyless/automated journey)"; J-03's "Acceptance is
endpoint-side only (no browser element)"; J-04's own evidence path is a handoff document, never a
screenshot. Their only UI-visible overlap is that `/desk` as a whole must keep loading cleanly,
captured as a single row below rather than three invented per-journey rows.

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | Microscope Readiness section (`data-testid="micro-readiness-section"`, collapsible id `microReadiness`) | Regression check (unmodified this iteration) | J-01's `evidence_makeup` flag has been open for 2 iterations because the browser lane was silently skipped; this iteration declares `Frontend Present: yes` specifically to capture a fresh, real screenshot (TC-8) | Navigate to `/desk`, click the section header with `data-testid="desk-section-expand-microReadiness"` to expand it, and verify the "Corpus Totals" table (`data-testid="micro-readiness-totals-table"`) shows "Distinct symbol-days" = 12 and "Distinct datasets" = 18, and the "Legacy Tick Shards" table (`data-testid="micro-readiness-shards-table"`) lists 18 rows whose "Split provenance" column reads `hand_assigned` (the exact text `journey-scripts/J-01.json` step 2 asserts) and whose "Exposure state" column reads `exploratory` |
| `/desk` | Whole-page load (no dedicated element exists for J-02/J-03/J-04) | Regression check (unmodified this iteration) | J-02 ("micro observer"), J-03 ("structure × flow join"), and J-04 ("Scout and the ledger") are backend/CLI/endpoint-only journeys with no browser element of their own; their only UI-visible overlap is that `/desk` must keep loading cleanly since it renders data these journeys' backends touch | Navigate to `/desk` and verify the "Playbook Signals" heading renders, no error banner or broken/blank section appears anywhere on the page, and the browser console shows no unhandled exception |
| `/` (cockpit) | Ticker watch panel | Regression check (unmodified this iteration; J-10 steps 1–3) | Part of J-10's 13-step kept-product sentinel (`journey-scripts/J-10.json`, reused byte-unmodified), which has not completed a real browser run this era | Navigate to `/`, verify the text "No ticker watched" appears, type `SIM-BUYER` into the field labeled "Ticker", click the "Watch" button, and verify the text "Buyer Control" appears |
| `/structure` | Tradable Map load | Regression check (unmodified this iteration; J-10 steps 4–7) | Same J-10 sentinel | Navigate to `/structure`, verify the text "Tradable Map" appears, type `AAPL` into the field labeled "Structure symbol", type `2026-06-22 17:00:00` into the field with `data-testid="structure-as-of-input"`, click the element with `data-testid="structure-load-button"`, and verify the text "300.11–302.2" appears |
| `/desk` | Playbook Evidence section | Regression check (unmodified this iteration; J-10 steps 8–10) | Same J-10 sentinel | Navigate to `/desk`, verify the "Playbook Signals" heading appears, click `data-testid="desk-section-expand-playbookEvidence"`, verify the text "Built from signature:" appears, type `2026-06-22` into the field with `data-testid="desk-playbook-date-input"`, and verify the text "recorded signals, none hidden" appears |
| `/desk` | Referee Registry section | Regression check (unmodified this iteration; J-10 step 11) | Same J-10 sentinel | Click `data-testid="desk-section-expand-refereeRegistry"` and verify the text "config fingerprint 08e471b10130e1e2" appears (the same frozen fingerprint this iteration's own TC-10 re-checks in the backend suite) |
| `/desk` | Referee Adjudications section | Regression check (unmodified this iteration; J-10 step 12) | Same J-10 sentinel | Click `data-testid="desk-section-expand-refereeAdjudications"` and verify the text "No hypotheses registered" appears |
| `/desk` | Referee Runs section | Regression check (unmodified this iteration; J-10 step 13) | Same J-10 sentinel | Click `data-testid="desk-section-expand-refereeRuns"` and verify the text "No evaluation runs recorded yet." appears |

<!-- Change Type is "Regression check" throughout — no row above reflects a code change; every row exists because the browser lane is being genuinely exercised this iteration for the first time in three tries. -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/walkforward.py` — wires `require_sufficient_sessions_for_folds`
  (TR-15) into `run_diagnostic_walkforward`'s one fold-building call site (immediately before
  `build_folds`), adds a CLI `except InsufficientSessionsForFoldsError` catch in `main()`, and adds
  a new tick-corpus exposure-registry seeding call (new constant `TICK_LEGACY_CORPUS_ID`, new
  helper `_tick_dataset_session_dates`) — no UI surface affected. Confirmed by grep: zero
  references to "walkforward" or "walk-forward" anywhere under `apps/frontend/`.
- `apps/backend/tests/test_walkforward.py` — five new tests (TC-2, TC-3, TC-5, TC-6, TC-7) plus one
  rewritten CLI test (TC-4) — a test file; no UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 2
- **Pre-existing surfaces requiring regression re-verification this iteration:** 7 (Microscope
  Readiness section, `/desk` whole-page load, cockpit ticker watch, `/structure` Tradable Map,
  Playbook Evidence section, Referee Registry section, Referee Adjudications + Referee Runs
  sections)
