# Phase goal-desk-iter-16 — UI Surface Map

**Phase:** goal-desk-iter-16
**Date:** 2026-07-29
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | `DeskHistoryRow` / `DeskHistoryTable` (Screen History table, click handler `handleSelectHistoryScreen`) | Changed behavior | Row selection switched from `screen_date`-keyed fetch (`fetchDeskScreenByDate`) to `id`-keyed fetch (`fetchDeskScreenById`) so an earlier same-date recording is individually reachable | With the real ambient same-date pair (`screen-2026-07-27-936543601e75` earlier / `screen-2026-07-27-3ad3c57aa6ba` later) or an equivalent fixture: click the earlier row and verify only it highlights (`data-selected="true"` on that `tr`) and the ranked table's NFLX `1d` coverage badge renders dark (`has_bars: false`); then click the later row and verify only it highlights and NFLX `1d` renders lit (`has_bars: true`) |
| `/desk` | `DeskHistoryTable` header + `DeskHistoryRow` (new "recorded" column, `data-testid="desk-history-created-utc"`) | New column | Each row now shows its own `created_utc` so two same-date rows read distinctly without opening either | Open `/desk`, locate two rows whose "date" column values are identical, verify their "recorded" column values (the new column) differ |
| `/desk` | `DeskHistoryTable` (row highlighting, `selected` prop derived from `selectedHistoryId`) | Changed behavior | Highlight comparison switched from `meta.screen_date === selectedDate` to `meta.id === selectedId`, and the default (latest) view is now itself a highlighted row | Load `/desk` with no history row clicked, verify the row matching the currently-displayed `latest` snapshot's `id` is highlighted by default (not zero rows highlighted) |
| `/desk` | `DeskProvenance` (Provenance panel, `data-testid="desk-provenance"`) — new "Snapshot id" / "Recorded at" `Metric` rows | New data displayed | Names exactly which recording is on screen (its own `id` and `created_utc`), needed once two same-date recordings can exist | Click a Screen History row, verify the Provenance panel's "Snapshot id" value equals that row's `id` (matches `data-screen-id` on the clicked `tr`) and "Recorded at" equals the row's "recorded" column value |
| `/desk` | `DeskProvenance` — default-view note (`data-testid="desk-provenance-latest-note"`) | Changed copy (conditional element) | Reworded from an implicit "latest = latest date" framing to an explicit "most recently recorded, not necessarily latest date" statement, gated on `isViewingLatest` | Load `/desk` fresh (no row clicked): verify the note text reads "This is the most recently recorded screen (by recorded-at time), not necessarily the latest screen date...". Click a history row that is NOT the currently-latest snapshot: verify the note disappears. Click the row that IS the latest snapshot (or use "Show latest"): verify the note reappears |
| `/desk` | Screen History section — new `IntegrityErrorsNote` (`data-testid="desk-screen-history-integrity-errors"`) | New element (conditional) | Screen ledger's own `integrity_errors` (already returned by `GET /research/desk/screen`) is now rendered instead of being fetched-but-unused | With a corrupted screen record file planted in a scoped test store dir, reload `/desk` and verify a note reading "N file(s) failed an integrity check and is/are excluded: `<filename>`" appears beneath the Screen History table. With the real ambient store (currently zero corrupt files), verify no such note is rendered (no empty-array placeholder) |
| `/desk` | Top-up Runs section (`TopupRunsSection`) — new `IntegrityErrorsNote` (`data-testid="desk-topup-runs-integrity-errors"`) | New element (conditional) | `get_topup_runs` previously discarded `store.list()`'s `errors`; now serves and renders them | Plant a corrupted Top-up run record file in a scoped `TopupRunStore` dir (never `apps/backend/.data`), reload `/desk`, verify the integrity-error note is visible in the Top-up Runs section naming that file, and the corrupt record is absent from the runs table/latest-run detail |
| `/desk` | Index Reconciliation section (`ReconciliationSection`) — new `IntegrityErrorsNote` (`data-testid="desk-reconcile-runs-integrity-errors"`) | New element (conditional) | `get_desk_index_reconcile_runs` previously discarded `store.list()`'s `errors`; now serves and renders them | Plant a corrupted reconciliation run record file in a scoped `ReconcileRunStore` dir (never `apps/backend/.data`), reload `/desk`, verify the integrity-error note is visible in the Index Reconciliation section naming that file, and the corrupt record is absent from the runs table/latest-run detail |
| `/desk` | Universe ledger section | Not built (documented gap) | Spec/plan named a fourth "Universe" integrity-error line, but no Universe snapshot list/ledger section exists anywhere in the frontend — only a `universe_snapshot_id` string in Provenance | Confirm there is no Universe list/table anywhere on `/desk`; this is a documented known-gap, not a regression to test against — see the Not-Visible-Yet section of the user-visible-changes report |

<!-- Change Type options used above: Changed behavior | New column | New data displayed | New element (conditional) | Not built (documented gap) -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/desk_routes.py` `get_screen` — `id`+`date` supplied together now
  returns an honest HTTP 422 refusal (previously undefined/would have silently followed `date`'s
  branch since `id` support didn't exist). This is a request-shape/error-contract change with no
  dedicated UI surface of its own — the frontend never constructs a request supplying both params,
  so this refusal path is exercised only by direct API/MCP callers, not through any `/desk` click
  path. Covered by backend tests (`test_desk_screen.py` TC-4), not a browser-testable UI surface.

<!-- All other backend changes (the ?id= read and the two integrity_errors additions) ARE wired
     into a UI surface this same iteration and are listed in the Affected UI Surfaces table above. -->

---

## Summary

- **Frontend surfaces changed:** 7 (Screen History row selection/highlight, Screen History
  "recorded" column, Provenance `id`/`created_utc` rows, Provenance default-view note, Screen
  History integrity-error note, Top-up Runs integrity-error note, Index Reconciliation
  integrity-error note)
- **New pages/routes:** 0
- **Modified components:** `DeskHistoryRow`, `DeskHistoryTable`, `DeskProvenance`,
  `DeskPopulatedScreen`, `TopupRunsSection`, `ReconciliationSection`, `DeskPage` (plus one new
  shared component, `IntegrityErrorsNote`)
- **Navigation changes:** no
- **Backend-only changes:** 1 (the `id`+`date` 4xx refusal contract — not reachable through any
  existing `/desk` UI action)
