# Phase goal-referee-iter-4 — UI Surface Map

**Phase:** goal-referee-iter-4
**Date:** 2026-08-14
**Written by:** ui-impact-analyst

---

## File Classification

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/backend/app/research/referee_stats.py` | backend-internal | none | Statistics core (`permutation_test` exact-enumeration fix, attestation re-pin, version bump). Imported by nothing outside its own test suite this iteration. |
| `apps/backend/app/research/referee_evidence.py` | backend-api | not visible yet | Adds `stale_basis_dates` to `playbook_occurrence_readiness()` (served at `GET /research/desk/referee/evidence`) and `playbook_observations()` (served by no route). Confirmed via frontend source search: neither the endpoint nor the new field is consumed anywhere in `apps/frontend/`. |
| `apps/backend/tests/test_referee_stats.py` | tests | none | New/extended pytest coverage only. |
| `apps/backend/tests/test_referee_oracles.py` | tests | none | New/extended pytest coverage only. |
| `apps/backend/tests/test_referee_evidence.py` | tests | none | New/extended pytest coverage only. |
| `docs/handoffs/goal-referee-iter-4-dev.md` | docs | none | Dev handoff document. |

---

## Affected UI Surfaces

No UI surface changed this iteration — zero frontend files were touched. `git status --porcelain`
shows only backend `.py` files and doc/report artifacts modified; `grep -rn "referee"
apps/frontend/app apps/frontend/components apps/frontend/lib` returns zero matches.

The three rows below are **not** new or changed surfaces. They are the pre-existing pages this
iteration's own execution plan (`runs/goal-referee-iter-4/plan.md`) and phase spec (TC-15) require
browser-qa to walk regardless — the project's binding rule has journey J-10 (the "kept product
stands" regression sentinel) ride every iteration, specifically so a backend-only diff like this
one can be proven not to have broken anything already shipped. Every step and expected-text value
below is taken verbatim from the project's own stored golden replay script,
`runs/goal-session-referee/journey-scripts/J-10.json`, which iterations 1–3 already used
successfully (iter-3's replay: PASS).

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` (Cockpit) | Ticker watch bar + `IdleState` | Regression check only (no code change) | J-10 sentinel re-walks this journey every iteration per the binding "rides every iteration" rule, independent of what this iteration's diff touched | Navigate to `http://localhost:3301/`, confirm the text "No ticker watched" is visible, type "SIM-BUYER" into the field labeled "Ticker", click the "Watch" button, confirm the text "Buyer Control" appears |
| `/structure` | Structure symbol input, `structure-as-of-input`, `structure-load-button` | Regression check only (no code change) | Same J-10 requirement; confirms the pinned-AAPL structure load still renders its previously-shipped output | Navigate to `http://localhost:3301/structure`, confirm the text "Structure" is visible, type "AAPL" into the field labeled "Structure symbol", type "2026-06-22 12:00:00" into the field with test id `structure-as-of-input`, click the button with test id `structure-load-button`, confirm the text "2026-06-18" appears |
| `/desk` | "Playbook Evidence" collapsible section (`CollapsibleSection` id `playbookEvidence`) | Regression check only (no code change) | Same J-10 requirement; confirms the one Desk section whose backing route (`GET /research/desk/referee/evidence`) just gained the unconsumed `stale_basis_dates` field still renders unchanged | Navigate to `http://localhost:3301/desk`, confirm the text "Playbook Signals" is visible, click the button with test id `desk-section-expand-playbookEvidence`, confirm its `aria-expanded` attribute becomes `"true"` and the text "Built from signature" appears |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/referee_stats.py` — fixes the exact-enumeration p-value floor bug in
  `permutation_test` (direct per-combination `math.fsum` accumulation, matching `_t_statistic`'s
  own method, plus a cross-session `math.fsum` combine that the developer found empirically
  necessary); re-pins `_ATTESTATION_EXPECTED`/`_ATTESTATION_TOLERANCE`; bumps
  `STATS_CORE_VERSION` to `"referee-stats-v2"`. Imported by nothing outside its own test suite —
  no UI surface affected.
- `apps/backend/app/research/referee_evidence.py` — additive-only: one shared
  `_is_stale_basis(...)` helper plus a new `stale_basis_dates` field on
  `playbook_occurrence_readiness()`'s and `playbook_observations()`'s response dicts. Zero change
  to any currently-served field's value. No UI surface affected (confirmed via frontend source
  search — see File Classification above).
- `apps/backend/tests/test_referee_stats.py`, `apps/backend/tests/test_referee_oracles.py`,
  `apps/backend/tests/test_referee_evidence.py` — new/extended pytest coverage (TC-1/2/5/6/7/8 in
  the first file, TC-3/4 in the second, TC-9/10 in the third) — no UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 5 (2 production modules + 3 test files)
