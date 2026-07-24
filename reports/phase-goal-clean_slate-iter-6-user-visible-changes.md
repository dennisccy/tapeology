# Phase goal-clean_slate-iter-6 — User-Visible Changes

**Phase:** goal-clean_slate-iter-6 (J-05: "The kept product stands — regression sentinel")
**Date:** 2026-07-24
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

**None.** This is a dead-code-removal + test-hardening + re-certification iteration, not a
feature iteration. Goal.md states it explicitly: "New user-facing capability: None." The dev
handoff confirms nothing new was added — no new page, button, form, data view, filter, or
affordance exists after this iteration that didn't already exist before it. Every change is
either a deletion of already-unreachable backend code or a new automated test; neither is
something a user can navigate to, click, or otherwise perceive.

---

## What Changed in the Visible UI

**None.** Zero frontend files changed this iteration — confirmed directly (`git status` /
`git diff --stat` show no path under `apps/frontend/` touched; the only modified file anywhere
is `apps/backend/app/research/routes.py`, plus one new backend test file and one new evidence
report). The top navigation, the Cockpit page (`/`), the Structure page (`/structure`), both
charts (candles, timeframe switching, live tape moving bars, the S/R band overlay), the Case
Studies panel/table/filters/drill-in, and the Edge Report panel all render pixel- and
behavior-identical to iter-5's shipped state.

---

## What Old Behavior Changed

None — no existing feature behaves differently after this iteration.

One thing worth flagging to testers so the mandatory re-walk isn't mistaken for busywork: this
iteration IS the interlude's closing regression sentinel (target journey J-05, "the kept product
stands"). Even though nothing changed, the full kept-product surface — cockpit ticker watch/stop,
chart timeframe switching, `/structure`'s Load-by-symbol-and-date flow and its resulting wall-band
value, the Case Studies row-click drill-in, the Edge Report's honest current state, and the
2-item top nav — must be walked one more time as evidence that this iteration's backend file edit
(`routes.py`, which also serves several of `/structure`'s live routes even though no live handler
in it was touched) didn't disturb anything. That walk is expected to show everything unchanged,
not different.

---

## Not Visible Yet

- The 5 deleted Pydantic request-body classes (`ThesisRequest`, `ResolveRequest`,
  `ActionRequest`, `StudyRequest`, `ReviewRequest`) were never visible to begin with — each had
  exactly one occurrence in `routes.py` (its own class definition) and zero live route-parameter
  references, confirmed both by the developer's grep sweep and by the new guard test's own
  AST-based check. There is no "before" UI state to compare against: deleting them changes
  nothing on screen, now or ever — they were dead the moment the routes that used to accept them
  were deleted several iterations ago.
- The new structural guard test (`apps/backend/tests/test_routes_no_orphaned_request_models.py`)
  is a backend-only automated check. It runs inside `pytest`, never renders anywhere a user or
  operator would see it, and has no UI surface planned for it, ever. Its only observable effect is
  making the test suite fail loudly if a future change repeats this exact mistake (a route
  deleted, its request-body class left behind) — the opposite of what happened this time, when it
  sat unnoticed for several iterations.
