# Iteration 31 — Coherence Audit

**Iteration:** goal-desk-iter-31
**Date:** 2026-07-31
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

This iteration touches exactly one already-registered Data-Contract row ("Screen run records
(per-run outcome ledger)" — J-18, owner `desk_screen_log.py`/`desk_screen_compute.py`, served by
`GET /research/desk/screen/runs`) and makes zero new value/endpoint/module/owner. Both fixes are
corrections to the derivation/rendering of already-recorded fields on that row, not new
computation.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `failed_member` (screen-run record, terminal `"failed"` state) | OK — same owner, corrected derivation only | `apps/backend/app/research/desk_screen_compute.py:277` — `members[attempted] if attempted < len(members) else None` → `members[attempted] if 0 < attempted < len(members) else None`; still the ONE writer (`run_screen_and_record`), still the ONE record shape, no new field |
| `run.state` / `run.reused` / `run.ranked_count` / `run.skipped_by_reason` (rendered on `/desk`'s "Latest run" block) | OK — client-side conditional suppression of an existing display, not a recomputation | `apps/frontend/app/desk/page.tsx:1328-1340` (`LatestScreenRunDetail`) — added `&& !(run.state === "done" && run.reused)` / `&& !run.reused` guards around already-rendered elements; the underlying `run` object is still the same prop, still sourced (up the component tree) from `GET /research/desk/screen/runs` verbatim — this is a "re-format for display" case (Part A rule 3), not a violation |

No new displayed value/entity was introduced this iteration (confirmed against the diff and the
iteration spec's own "New information displayed: None" / "Data-contract additions: None" fields),
so Part A rules 4/5 (duplicate-of-existing / unregistered-new) do not apply.

Checked for a second computation path or non-canonical fetch and found none: `grep`-ing the diff
for `fetch(`, a second `failed_member` assignment, or any new endpoint/module touching screen-run
records turns up only the single `file:line` pair above in each case.

## Information Architecture check

No new page, route, section, or control. The change lives entirely inside the already-registered
`/desk` → "Screen Runs" section's "Latest run" detail block (blueprint.md's J-18 Feature/journey
home row, shipped iter-29). Confirmed against `app/meta.py`'s `UI_ROUTES` (unchanged this
iteration — not present in the diff) and the ui-surface-map, which independently reports
"Navigation changes: no" / "New pages/routes: 0".

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` "Screen Runs" → "Latest run" detail | OK — existing home, no new surface | `app/meta.py` `UI_ROUTES` unchanged (not in diff); `apps/frontend/app/desk/page.tsx` diff is confined to `LatestScreenRunDetail`'s existing JSX, no new component/route/import |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The two tracked build-plumbing files (`apps/frontend/next-env.d.ts`, `apps/frontend/tsconfig.json`)
  are reverted to their pre-iteration-30 content in this diff (dropping the dangling absolute
  scratchpad path). This is repo hygiene, not a product/data-contract/IA concern — noted only for
  completeness, no action needed from this gate.
- The blueprint's own "NOTED at iter-30" entry was corrected (outside this diff's excluded
  `runs/*` scope, confirmed by direct read of `runs/goal-session-desk/state/blueprint.md`) to stop
  claiming these two fixes had already shipped, and a new "NOTED at iter-31" entry registers this
  iteration's real scope before the build — consistent with the session's own
  never-claim-shipped-before-landing lesson. This is documentation currency, not a coherence
  defect.
