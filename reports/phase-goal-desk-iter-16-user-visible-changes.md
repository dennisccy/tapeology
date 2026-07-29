# Phase goal-desk-iter-16 — User-Visible Changes

**Phase:** goal-desk-iter-16
**Date:** 2026-07-29
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now open **every** individually-recorded screen snapshot from the `/desk` Screen History
  list — including an earlier recording that shares a `screen_date` with a later one. Previously,
  clicking either of two same-date rows always displayed the same (newer) snapshot; the older one
  was listed but permanently unreachable. Now clicking any row opens that exact recording.
- Users can now tell two same-date Screen History rows apart at a glance: each row shows its own
  "recorded" timestamp (`created_utc`) in a new column next to the trading date.
- Users can now see exactly which snapshot is on screen: the Provenance panel gains a "Snapshot id"
  row and a "Recorded at" row naming the displayed recording's own identity and timestamp.
- Users can now see file-integrity problems that were previously silently swallowed: if a Top-up Run
  record file or an Index Reconciliation run record file on disk fails its own integrity check, a
  plain-text note naming the failed file(s) now appears in that section on `/desk`. (The Screen
  History section already had this internally and now renders it too.)

---

## What Changed in the Visible UI

- `/desk` Screen History table: a new "recorded" column shows each row's `created_utc` beside its
  `screen_date`.
- `/desk` Screen History table: row highlighting now tracks the exact snapshot `id`, not the date —
  two rows sharing a date are each independently, distinctly highlightable, and the default (latest)
  view is itself shown as a highlighted row.
- `/desk` Provenance panel: two new rows, "Snapshot id" and "Recorded at", appear above the existing
  "Universe snapshot" row.
- `/desk` Provenance panel: the descriptive note shown when no history row is selected (viewing the
  default/latest snapshot) was reworded from implying "the latest screen date" to explicitly stating
  "the most recently recorded screen (by recorded-at time), not necessarily the latest screen date —
  an earlier same-date recording can still exist and be opened from Screen History below."
- `/desk` Screen History section: a new integrity-error note appears beneath the history table
  whenever the screen ledger's own payload reports any (count-plus-filename, e.g. "1 file failed an
  integrity check and is excluded: screen-2026-01-01-deadbeef.json").
- `/desk` Top-up Runs section: same new integrity-error note, beneath the run table/latest-run
  detail.
- `/desk` Index Reconciliation section: same new integrity-error note, beneath the run table/latest
  run detail.

---

## What Old Behavior Changed

- **Screen History row click**: previously fetched the row's snapshot by `screen_date`
  (`GET /research/desk/screen?date=`), which always resolved to the newest recording for that date.
  Now fetches by the row's own `id` (`GET /research/desk/screen?id=`), so a same-date pair each
  resolves to its own distinct recording. Single-recording dates behave identically to before.
- **Screen History row highlighting**: previously compared the displayed snapshot's `screen_date`
  against the clicked row's date; now compares `id`. No visible difference for dates with only one
  recording; for a same-date pair, previously both rows could appear to represent "the selected"
  state ambiguously — now exactly one row highlights at a time, matching what's actually displayed.
- **Provenance panel default-view copy**: reworded (see above) — an existing panel's descriptive text
  changed, not its data.
- `GET /research/desk/screen?date=` itself (used internally, not by the history click-through
  anymore) is byte-unchanged — same resolution-to-newest-match behavior as before.

---

## Not Visible Yet

- The phase spec and execution plan both named a fourth "Universe" ledger section that should also
  gain an integrity-error line, alongside Screen History, Top-up Runs, and Index Reconciliation.
  On inspection this section does not exist anywhere in the frontend — `/desk` has never rendered a
  list of registered universe snapshots, only a single `universe_snapshot_id` string inside the
  Provenance panel. This was not built this iteration (the dev handoff documents why the spec's
  premise did not match the actual codebase). `GET /research/desk/universe`'s own `integrity_errors`
  field has existed since an earlier iteration (J-01) but still has no UI rendering path anywhere in
  the app.
- If every recorded screen snapshot were simultaneously corrupted (an edge case that does not
  currently exist in the real data), the entire Screen History panel — including its new
  integrity-error note — would not render at all, because the page falls back to its pre-existing
  "Desk screen not computed yet." empty state in that specific case. This is a pre-existing property
  of the page's empty-state logic, unchanged by this iteration, but worth knowing when testing.
