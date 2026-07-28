# Phase goal-desk-iter-11 — User-Visible Changes

**Phase:** goal-desk-iter-11
**Date:** 2026-07-28
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- See a durable history of every top-up run on the `/desk` page, in a new **"Top-up Runs"** panel
  that stays at the bottom of the page no matter what the rest of the page is showing (loading, no
  screen computed yet, or a populated screen) — previously, a run's outcome vanished the instant the
  next run started or the page was reloaded after a long gap.
- See, for every recorded run, its date, a run id, whether it finished normally / was cancelled /
  failed, and how many symbol×timeframe pairs it attempted out of the total (e.g. `47 / 50`) — one
  row per run in a table.
- See, for the MOST RECENT top-up run specifically, a full breakdown: how many pairs were reused
  (already had data), freshly fetched, or failed (e.g. `"41 reused · 4 fetched · 2 failed"`), and —
  for every failed pair — the exact underlying error text, shown in full rather than summarized or
  cut short.
- See an honest count of how many pairs a cancelled or interrupted run never got to (e.g.
  `"3 pairs not reached"`), instead of that information being silently lost.
- Trust that after clicking the existing "Top-up" button and letting a run finish, the Top-up Runs
  panel updates itself with the new run automatically — no manual page reload required.
- Trust that when no top-up run has ever completed, the panel says so plainly ("No top-up runs
  recorded yet.") rather than appearing blank or broken.

---

## What Changed in the Visible UI

- The `/desk` page has a new **"Top-up Runs"** section (`aria-label="Top-up runs"`), rendered as the
  last section on the page — below Screen History and the Run Screen / Top-up controls when a screen
  exists, and below the "not computed yet" panel when it doesn't. It always renders, regardless of
  whether a screen has ever been run.
- The new panel's table lists one row per recorded run with five columns: date, run id, state
  (`done` / `cancelled` / `failed`), "attempted / total" pairs, and the universe snapshot id the run
  used.
- Below the table, for the latest run only, a "Latest run — `<date>` · `<id>`" detail block shows its
  state, "`N` of `M` pairs attempted", the per-outcome counts string, and — only when the run left
  pairs unreached — an amber "`N` pair(s) not reached" note.
- When the latest run had any failures, a "Failed pairs (`N`)" list appears beneath the counts,
  naming each failed symbol + timeframe and showing its raw error text verbatim (not truncated).
- The existing top-up progress poll (the one that already updates the live "Topping up…" progress
  line while a run is in flight) now also silently refreshes the Top-up Runs panel the moment that
  run reaches a terminal state — so a just-finished run's own record appears without the user doing
  anything extra.

---

## What Old Behavior Changed

None. The existing "Run Screen", "Top-up", and "Cancel" buttons, the live compute-progress lines,
Screen History, the Briefing/Skipped-Members tables, and every other element already on `/desk`
render and behave exactly as before — this iteration is a pure addition of one new read-only panel.
The one technical (not user-visible) side effect is that the top-up progress poll now performs one
extra background fetch when a run finishes, purely to populate the new panel — it changes no visible
label, button, or existing data.

---

## Not Visible Yet

- **Per-outcome / failure detail for older runs**: the panel's history table shows only summary
  fields (date, id, state, attempted/total, universe snapshot) for every run except the most recent
  one. The full pair-by-pair breakdown (which symbols were reused/fetched/failed, and the failure
  text) is only ever shown for the latest run — this is the current, intentional shape of what the
  backend's list endpoint serves (mirroring how the same page already shows full detail only for the
  currently selected screen, not every screen ever run), not a bug. Each older run's full detail is
  still saved to disk; there is simply no UI (or API endpoint) yet to browse into a specific past
  run's own detail.
- **A real, credentialed top-up run against the live Yahoo data vendor** has not been performed as
  part of this change — the panel and its data have been proven with simulated/fixture data only.
  The mechanism is fully wired, so the next time an operator runs a real Top-up from `/desk`, that
  run will be recorded and will appear in the panel like any other.
