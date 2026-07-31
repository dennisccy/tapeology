# Phase goal-desk-iter-29 — User-Visible Changes

**Phase:** goal-desk-iter-29
**Date:** 2026-07-31
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see a durable history of every screen run ever attempted — including runs that
  reused an already-recorded result, were cancelled partway, or failed — by scrolling to the new
  "Screen Runs" panel on the `/desk` page (below the existing "Index Reconciliation" panel).
- For each recorded run, users can now see: the date it ran, its run id, its terminal outcome
  (`done` / `cancelled` / `failed`), how many of the universe's members it actually checked versus
  the total, and what it produced (a screen id, an honest "reused `<id>` — no walk was performed"
  note, or "nothing recorded" for a cancelled/failed run).
- For the most recent run specifically, users can now see additional detail: elapsed time
  (start→finish), the ranked count and skipped-by-reason counts (no bars / no basis) on a completed
  walk, an "N members not reached" note if the run stopped early, and — if that run failed — the
  exact member name it was working on plus the underlying error message, verbatim.
- Clicking "Run Screen" a second time for the same day (unchanged inputs) is now noticeably faster:
  the system checks first and, if nothing changed, returns the already-recorded answer immediately
  instead of re-walking all ~101 universe members. This is not a new control — it is the existing
  "Run Screen" button becoming cheaper on a duplicate click — but it is now visible in the new
  ledger via the `reused: true` outcome text.

---

## What Changed in the Visible UI

- `/desk` gains a fourth ledger section, "Screen Runs", placed immediately after the existing
  "Index Reconciliation" section — same dark/dense styling, same table-plus-latest-detail layout
  as its three siblings (Screen History, Top-up Runs, Index Reconciliation).
- The new section's table has five columns: date, run, state, attempted / total, produced.
- The new section's "Latest run" detail block shows: state, "N of M members attempted", elapsed
  time, produced outcome, an amber "N member(s) not reached" note when applicable, ranked/skipped
  counts (only when `state === "done"`), and the raising member + verbatim error text (only when
  `state === "failed"`).
- The new section reuses the exact same empty-state text pattern as its siblings: "No screen runs
  recorded yet." when nothing has been recorded.
- The new section carries its own "integrity errors" note line, identical in shape to the one
  already shown on Screen History / Top-up Runs / Index Reconciliation.

---

## What Old Behavior Changed

- **Run Screen (duplicate click on an unchanged day).** Previously: clicking "Run Screen" a second
  time for the same day always re-walked all ~101 universe members before landing on the same
  result (visibly slower, with the members-progress counter climbing from 0 again). Now: an
  identical repeat click resolves immediately via the built-in check, and the button's own
  "Reused the snapshot already recorded for this key — `<id>`" message (already shown before this
  iteration) now corresponds to a genuinely instant response rather than a full recompute that
  happened to reuse the result at the end. No visible text or button changed — only the speed and,
  now, the new ledger's own record of that reuse.
- No change to the ranked table, its columns, its row content, or its click-through behavior — the
  briefing itself computes and displays identically to before.

---

## Not Visible Yet

None. The new backend capability (the screen-run log, served at
`GET /research/desk/screen/runs`) has a corresponding UI surface in this same iteration — the new
"Screen Runs" panel on `/desk`.
