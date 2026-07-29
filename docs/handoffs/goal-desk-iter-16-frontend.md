# goal-desk-iter-16 Frontend Handoff

**Phase:** goal-desk-iter-16
**Date:** 2026-07-29
**Agent:** developer
**Status:** complete

## What Was Built

- **Screen History: id-based selection + highlighting.** Clicking a history row now fetches that
  exact recording by its own `id` (`fetchDeskScreenById`, `GET /research/desk/screen?id=`) instead
  of by `screen_date` — the only way to reach an EARLIER same-`screen_date` recording once a later
  one exists (`?date=` always resolves the newest match). Highlighting is now id-based too
  (`selectedHistoryId`), so two same-date rows are each independently, distinctly highlighted, and
  the default (latest) view is itself a highlighted row in the table.
- **Screen History: `created_utc` column.** Each row now shows its own recorded-at timestamp beside
  `screen_date`, so two same-date rows read distinctly at a glance without opening either
  (`data-testid="desk-history-created-utc"`).
- **Provenance panel: `id` + `created_utc`.** Two new `Metric` rows name exactly which recording is
  on screen. The default-view-only note (visible only while viewing `latest`, not a history
  selection) now reads "This is the most recently recorded screen (by recorded-at time), not
  necessarily the latest screen date..." — replacing the prior implicit "latest = most recent"
  framing with an explicit, honest one (`data-testid="desk-provenance-latest-note"`).
- **Ledger integrity-error disclosure.** A new shared `IntegrityErrorsNote` component (plain-text,
  count-plus-filename, e.g. "1 file failed an integrity check and is excluded: reconcile-2026-01-01-
  deadbeef0000.json") renders in the Screen History, Top-up Runs
  (`data-testid="desk-topup-runs-integrity-errors"`), and Index Reconciliation
  (`data-testid="desk-reconcile-runs-integrity-errors"`) sections whenever that section's own
  payload carries any `integrity_errors` entries; absent otherwise (no empty-array placeholder).

## Files Changed

- `apps/frontend/app/desk/page.tsx` — see the dev handoff's "Files Changed" section for the full
  list of touched components (`DeskHistoryRow`, `DeskHistoryTable`, `IntegrityErrorsNote` (new),
  `TopupRunsSection`, `ReconciliationSection`, `DeskProvenance`, `DeskPopulatedScreen`, `DeskPage`).
- `apps/frontend/lib/types.ts` — `integrity_errors` added to `DeskTopupRunsListResult`/
  `DeskReconcileRunsListResult`.
- `apps/frontend/lib/api.ts` — new `fetchDeskScreenById`.

## Visual/UX notes for QA

- No new page, no new nav row — every change is additive rows/columns inside the four already-
  shipped sections (minus Universe — see Known Issues below), matching the design system's existing
  dark/dense/terminal-grade styling (`LABEL_CELL`/`NUMERIC_CELL`/`HEADER_CELL` classes, unchanged).
- The two real ambient same-`screen_date` recordings (`screen-2026-07-27-936543601e75` /
  `screen-2026-07-27-3ad3c57aa6ba`) are already present in `apps/backend/.data/screen/` and are the
  natural browser-QA/demo-narrator fixture — no seeding needed. Selecting the earlier one shows
  NFLX's `1d` coverage badge dark (`has_bars: false`); selecting the later one shows it lit
  (`has_bars: true`) — verified live against the real store (see dev handoff).
- The integrity-error note only appears when a ledger's `integrity_errors` array is non-empty;
  today the real ambient store has none, so a scoped-store test fixture (per goal.md's own
  discipline — a corrupt file planted OUTSIDE `apps/backend/.data`) is needed to browser-screenshot
  TC-13.

## Tests Run

Same commands/results as the dev handoff: `npx tsc --noEmit` clean; `rm -rf .next && npm run build`
compiled + linted clean; backend guard tests covering this page's source
(`test_desk_ui_guards.py`, `test_desk_hover_tooltip_guard.py`, `test_copy_discipline.py`) all green.

## Known Issues

- The phase spec/plan named "Universe" as a fourth ledger section needing an integrity-error line,
  but no such section exists in the frontend (confirmed by direct codebase inspection, not just the
  spec's own citations, which point at unrelated types). Not built this iteration — full rationale
  in the dev handoff's Known Issues section.
- See the dev handoff for the remaining known issues (the default-view-only Provenance note scope,
  and the all-screens-corrupted edge case where the Screen History integrity note would be hidden
  behind the pre-existing "not computed yet" empty state).
