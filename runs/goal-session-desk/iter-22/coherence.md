# Iteration goal-desk-iter-22 — Coherence Audit

**Iteration:** goal-desk-iter-22
**Date:** 2026-07-30
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Summary

This is a `Depth: evidence`, capture-only iteration (spec: `docs/phases/goal-desk-iter-22.md`).
Confirmed via `git diff 363203d41980496475ba8e286063b470d74deeff --stat -- apps/` returning
**empty** — zero diff to `apps/backend/` or `apps/frontend/` (also zero untracked files under
`apps/`). The only new files are entirely outside the app: `project-extensions/qa-rig/README.md`,
`project-extensions/qa-rig/capture-native-tooltip.py`, `project-extensions/qa-rig/xrig.sh` (new,
owner-approved headed-capture QA tooling), plus doc/report/runs bookkeeping
(`docs/handoffs/goal-desk-iter-22-dev.md`, `docs/phases/goal-desk-iter-22.md`,
`reports/reviews/goal-desk-iter-22-review.md`, `reports/qa/goal-desk-iter-22-evidence/*`,
`runs/goal-session-desk/iter-22/*`) and a documentation-only `NOTED at iter-22` entry appended to
`runs/goal-session-desk/state/blueprint.md` (lines 537-551) naming T-10a and the qa-rig — the entry
itself states "no new Data-Contract row, no nav-skeleton change" and I verified that claim against
the diff rather than taking it on faith.

The `deskRowDrillInTitle`/`data-testid="desk-row-drill-in"` composite tooltip
(`apps/frontend/app/desk/page.tsx:278-346`) that the new qa-rig photographs was already present,
byte-unchanged, before this iteration (confirmed by grep against the working tree — the lines match
the blueprint's own iter-18/19 description verbatim). The qa-rig is a screenshot tool for an
already-registered, already-rendered value; it computes nothing, serves nothing, and is not itself a
UI surface of the product (it lives under `project-extensions/`, alongside `host-guard/`, not under
`apps/frontend/app/`).

## Data Contract check

No registered value's computation or serving path changed this iteration. `bands_by_class` /
`opposite_band` (the "Screen snapshots, rank rows, skip rows" row, owner `desk_screen.py`, endpoint
`GET /research/desk/screen`) were already fully shipped/registered at iter-18/19; this iteration
reads and photographs the already-rendered tooltip, it does not recompute or re-serve the value.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `bands_by_class` (ranked row) | OK — unchanged, zero diff to `desk_screen.py` | `apps/backend/app/research/desk_screen.py` (no diff this iter) |
| Ranked-row `title`/tooltip render | OK — unchanged, zero diff to `page.tsx` | `apps/frontend/app/desk/page.tsx:278-346` (no diff this iter) |

## Information Architecture check

No new page, route, or nav entry this iteration. `project-extensions/qa-rig/` is dev/QA tooling
(analogous to `project-extensions/host-guard/`), not an app page or feature — it has no navigation
concern.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` (unchanged) | OK — no route/page change | `apps/backend/app/meta.py` `UI_ROUTES` (no diff this iter) |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. This is a pure evidence-capture iteration with zero product diff; nothing to note beyond
  the summary above.
