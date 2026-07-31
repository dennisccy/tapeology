# Phase goal-desk-iter-31 — User-Visible Changes

**Phase:** goal-desk-iter-31
**Date:** 2026-07-31
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

None new. This iteration adds no new capability, page, or control — it finishes two small
honesty/correctness fixes on the already-shipped `/desk` "Screen Runs" section that a prior
iteration's spec called for but whose developer step never ran, plus reverts two polluted build
files with no runtime effect.

---

## What Changed in the Visible UI

- On `/desk`, the "Screen Runs" panel's "Latest run" detail block no longer shows the amber
  "N members not reached" note or the "N ranked · N skipped (no bars) · N skipped (no basis)"
  counts line when the latest run is a **reused** run (`state: done`, `reused: true`). Only the
  plain outcome text ("reused `<screen id>` — no walk was performed") is shown for that run.
  Confirmed live against the running app: the current ambient latest run
  (`screenrun-2026-07-31-fe0829e64a0d`, reused, `members_attempted: 0` of 101) now renders with
  neither element present.
- (Edge case, not currently reproducible on the ambient store) When a screen run crashes before it
  has looked at any company at all, the "Latest run" failed-detail block now shows
  "(member not recorded)" as the named cause instead of the first company in the pinned universe —
  which the crash never actually reached.

---

## What Old Behavior Changed

- **Reused-run detail on `/desk`:** previously, a reused screen run's "Latest run" detail showed
  both the amber "N members not reached" warning and a "0 ranked · 0 skipped (no bars) · 0 skipped
  (no basis)" counts line right next to its own honest "reused, no walk was performed" text — the
  combination read like something had failed even though the run correctly did no new work. Now
  those two misleading elements are hidden specifically for `done && reused` runs. Every other run
  state (a genuine fresh walk, a cancelled run, a failed run) renders exactly as before — no visual
  change for those cases.
- **Crashed-run failure attribution (backend-driven display):** previously, if a screen run crashed
  before it ever started evaluating the first company on the list, the recorded failure named that
  first company as the cause. Now, in that specific case, the record honestly shows no company name.
  A run that crashes partway through, after genuinely reaching at least one company, still correctly
  names that company exactly as before — unchanged.

---

## Not Visible Yet

- The crash-before-any-attempt honesty fix (failure record no longer names an untouched company) has
  no live trigger to observe on the current ambient `/desk` store — no crashed-before-any-attempt run
  is currently recorded there. It is proven by two backend unit tests
  (`test_tc1_a_crash_before_any_member_is_attempted_records_failed_member_null` and the existing
  `test_tc6_a_raising_member_records_state_failed_with_verbatim_error_and_failed_member` regression
  guard in `apps/backend/tests/test_desk_screen_compute.py`) rather than by a screenshot this
  iteration.
