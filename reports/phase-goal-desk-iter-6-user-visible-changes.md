# Phase goal-desk-iter-6 — User-Visible Changes

**Phase:** goal-desk-iter-6
**Date:** 2026-07-26
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now click any row in `/desk`'s "Screen History" panel and see that exact recorded
  date's own briefing (ranked rows, skipped members, and provenance line) replace what is
  currently on screen — no recompute, just a read-back of what was already saved.
- Users can now click a "Latest" button (shown whenever a past screen is on screen) to snap back
  instantly to the newest screen, with no network wait.
- Users can now click anywhere on a ranked briefing row (e.g. the AAPL row) on `/desk` to jump
  straight to `/structure` with that symbol and date already filled in and the tradable-map chart
  already loaded — no manual re-typing of the symbol or date.
- Users can now click anywhere on a **skipped** briefing row (a symbol with no bars or no basis
  session) to jump to `/structure` for that symbol too — `/structure` honestly shows its own
  empty/no-data state for it, which is expected, not an error.
- Users opening `/structure` directly via a link that carries `?symbol=...&asof=...` (as the new
  `/desk` drill-in links do) now see the page load automatically — fields filled in, chart drawn —
  with no click needed.

---

## What Changed in the Visible UI

- `/desk`'s "Screen History" table rows are no longer plain text — they are clickable, highlight
  on hover, and highlight with a solid background when the row currently being viewed is selected.
- A new banner appears above the Provenance panel on `/desk` whenever a non-latest screen is being
  viewed: "Viewing the recorded screen for `<date>` — not the latest." with a "Latest" button next
  to it.
- Every symbol in `/desk`'s Briefing table and Skipped Members table is now a clickable link (the
  whole row is the click target, not just the symbol text) that opens `/structure` for that symbol.
- A small amber inline note (`desk-history-fetch-error`) can now appear on `/desk` under the
  viewing banner if a history click fails or matches no recorded screen — the rest of the page
  stays exactly as it was before the click.
- `/structure`, when opened via a `/desk` drill-in link, now shows its Symbol and As-of fields
  already filled in and its tradable-map bands already drawn on first paint, instead of the usual
  blank form.

---

## What Old Behavior Changed

- `/desk`'s Screen History list: previously a read-only display (date, row/skip counts,
  provenance summary only, no interaction). Now selecting a row swaps the whole page's briefing
  display to that date's own snapshot.
- `/desk`'s Briefing and Skipped Members rows: previously plain text/data cells with no click
  behavior. Now every row (ranked or skipped) is a navigation link into `/structure`.
- `/structure`: previously always started blank regardless of how the page was reached, requiring
  a manual symbol/date entry and a Load click. Now, only when BOTH a `symbol` and `asof` query
  parameter are present in the URL, it fills those fields and loads automatically on mount. When
  opened with no query params, or with only one of the two present, it behaves exactly as before —
  empty fields, nothing loaded until Load is pressed.

---

## Not Visible Yet

None. This iteration's own stated scope was to wire two new interaction paths onto
already-registered backend data (the `GET /research/desk/screen?date=` endpoint, shipped and
backend-tested three iterations ago but never consumed by any frontend caller until now); no new
backend value, module, or route was introduced, so there is nothing left dangling behind an
unwired capability. (A handful of unrelated, previously-carried housekeeping items — a CLI
write-path guard, a per-series bar filter, one chart-guard-test re-tightening — remain
out-of-scope and untouched, as they were before this iteration; they were never UI-facing.)
