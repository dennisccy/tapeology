# Phase goal-desk-iter-34 — UI Surface Map

**Phase:** goal-desk-iter-34
**Date:** 2026-07-31
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | `LatestTopupRunDetail` — "Pairs recorded earlier" heading + row list (`data-testid="desk-topup-run-latest-reach-earlier"`, rows `data-testid="desk-topup-run-latest-reach-earlier-row"`), just below the reach line (`data-testid="desk-topup-run-latest-reach"`) | Changed behavior | Grouping bug fixed: pairs are now grouped/compared at calendar-day precision (matching what is printed), so a pair dated the same day as "newest recorded reach" can no longer appear under "earlier"; the list is also now capped at 20 rows instead of unbounded | Navigate to `http://localhost:3301/desk`, scroll to the "Top-up Runs" panel's latest-run detail, read the calendar day printed in the "newest recorded reach `<date>` · `<N>` pairs reach it" line, then check every row under "Pairs recorded earlier" — confirm none of their printed dates equal that same day, and confirm no more than 20 rows are rendered |
| `/desk` | New conditional disclosure paragraph `data-testid="desk-topup-run-latest-reach-earlier-cap"`, sitting between the "Pairs recorded earlier (N)" heading and its row list | New element (conditional) | Discloses the true earlier-pairs count when the rendered list has been capped, so truncation is never silent | Navigate to `http://localhost:3301/desk`; if the "Pairs recorded earlier (N)" heading's `N` is greater than 20, confirm the text "showing 20 of `N`" appears directly below the heading and above the first row; if `N` is 20 or fewer, confirm this sentence is absent entirely |
| `/desk` | "Pairs recorded earlier (N)" heading text itself (inside the same `desk-topup-run-latest-reach-earlier` block) | Changed behavior | The heading's count `N` now reflects the TRUE total of earlier pairs (`earlierTotal`), not the length of the (now-capped) rendered list — so the heading stays honest even when the list below it shows fewer rows | Navigate to `http://localhost:3301/desk`, count the rendered `desk-topup-run-latest-reach-earlier-row` elements and compare to the number in parentheses in the "Pairs recorded earlier (N)" heading — if a cap-disclosure sentence is present, `N` (the heading) must be strictly greater than the number of rendered rows (at most 20); if no cap-disclosure is present, `N` must equal the number of rendered rows |

<!-- Change Type key used above: Changed behavior | New element (conditional) -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_desk_topup_library_reach_guard.py` — extended with source-introspection
  guard assertions (day-truncation grouping, 20-row cap + true-total preservation, render-wiring)
  and their seeded-violation counterparts — test-only code that guards the frontend logic above; no
  UI surface of its own.
- `runs/goal-session-desk/journey-scripts/J-19.json` — golden replay/regression-test script
  repointed to stable substrings and testid-existence checks instead of exact dates/counts/the old
  buggy row text — a QA automation asset, not a rendered UI surface.
- `runs/goal-session-desk/state/blueprint.md` — internal state-tracking document flipping an
  "IN BUILD" note to "RESOLVED at iter-34" — project bookkeeping, not user-facing.

---

## Summary

- **Frontend surfaces changed:** 1 (`/desk` Top-up Runs latest-run detail block)
- **New pages/routes:** 0
- **Modified components:** 1 (`LatestTopupRunDetail` / its `topupLibraryReach` helper in
  `apps/frontend/app/desk/page.tsx`)
- **Navigation changes:** no
- **Backend-only changes:** 3 (test guard file, golden replay script, blueprint state doc)
