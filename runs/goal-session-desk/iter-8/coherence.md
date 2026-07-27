# Iteration 8 — Coherence Audit

**Iteration:** goal-desk-iter-8
**Date:** 2026-07-27
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration (why the checks below are short)

Iter-8 is a lean, pure-verification/hygiene iteration closing J-07. Per `docs/phases/goal-desk-iter-8.md`
("New user-facing capability: None", "UI surface changes: None", "Data-contract additions: None") and
confirmed against the actual diff (`git diff fe0a8e71c3f27a0569e03135df01b35f2ce53a02 -- .` with the
standard noise excludes, plus `git status`), the touched surface is exactly:

- `apps/backend/tests/test_mcp_server.py` — test-isolation fix (seeds its own `ScreenStore` fixture
  under a third, distinct date so `test_get_endpoint_desk_screen_date_query_proxies_verbatim` passes
  standalone). No production code changed.
- `apps/frontend/app/desk/page.tsx:204-214` — comment-only edit correcting a stale claim (iter-7's F2
  fix moved full-precision tooltip detail onto the row's drill-in anchor; the old comment still said
  "each cell's `title`"). Verified the surrounding JSX (`DeskRow`, lines 220-234) is byte-identical —
  same `href`, same `absolute inset-0`, same `data-testid="desk-row-drill-in"`.
- `apps/backend/scripts/goal-desk-iter8-baseline-diff.py` — new, untracked, one-off diagnostic script.
  Read in full (475 lines): it boots two throwaway `uvicorn` processes (a scratch worktree at
  `047c38e` and the current tree, each against a copied throwaway `.data/`), curls the existing kept
  routes on both, diffs response bodies, and writes `reports/goal-desk-iter-8-kept-route-baseline.md`.
  It is not imported by any app module, registers no route, and is not referenced from `app/main.py`
  (unchanged, confirmed via the snapshot diff below) — it is outside the served product entirely.
- `runs/goal-session-desk/journey-scripts/J-07.json` step 10 — golden-script target restored from
  `{"testid": "tradable-map-table"}` back to `{"testid": "tradable-map-chart-caption"}` (a golden
  replay asset, not app code).
- `runs/goal-session-desk/state/blueprint.md` — a "NOTED at iter-8" documentation-currency addendum
  only (lines 209-222); no Data Contract row added/changed, no nav-skeleton edit.
- `runs/goal-session-desk/state/assumptions.md` — one new logged assumption (route/input-set scope
  for the baseline-diff script); not a product decision.
- `docs/goal.md` — confirmed **unchanged** vs the snapshot SHA (`git diff <sha> -- docs/goal.md`
  produced no output), consistent with the iter spec's claim that the owner's R-1 ratification
  already landed before this iteration started and must not be re-worded here.

No new page, route, served value, or computation was introduced. No frontend fetch call changed.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Kept-route responses (`/research/*`, `/meta/ui-routes`) | OK | Read verbatim by the new diagnostic script via HTTP against the SAME existing endpoints on two separate processes (`apps/backend/scripts/goal-desk-iter8-baseline-diff.py:246-269` `_routes()`); it recomputes nothing — it is a byte-comparison harness, not a second source of any displayed value, and is never invoked by the running app. |
| Screen snapshot / rows (`desk_screen.py`) | OK | `test_mcp_server.py`'s fix calls the existing `ScreenStore(...).record(...)` (already the canonical write path) to seed test data — no new computation added. |
| Desk row tooltip content (drill-in anchor `title`) | OK | `apps/frontend/app/desk/page.tsx:204-214` is a comment-only change; the actual `title={deskRowDrillInTitle(row)}` (line 233) and the anchor markup are untouched — re-documentation of an existing value, not a re-fetch or recompute. |

No new displayed value was introduced this iteration, so there is nothing to register (A4/A5 do not apply).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| *(none — no new page/route/feature this iteration)* | OK | `apps/backend/app/meta.py` confirmed unchanged vs the snapshot SHA (not in the changed-file list); `UI_ROUTES` still 3 rows, no new nav entry to check. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The kept-route baseline report (`reports/goal-desk-iter-8-kept-route-baseline.md`) itself found two
  expected `DIFFERS` rows (merged-candles `integrity_errors`/`revised_timestamps` count, and
  `/meta/ui-routes` row count 2 vs 3) — both are pre-existing, already-blueprint-documented R-1 /
  iter-4 exemptions, not new drift introduced by this iteration. Noted for completeness, not a
  coherence issue.
- None otherwise. This iteration's tight scope (test fix + comment fix + a diagnostic script that
  never enters the served app + a golden-script restore) leaves no coherence surface to drift.
