# goal-desk-iter-16 Execution Plan

## What to Build

Single journey **J-12**: (a) make every recorded screen snapshot individually addressable by its
own `id` (closing the "two same-`screen_date` recordings, only the newer one reachable" gap), and
(b) stop two ledger GETs from silently discarding their own store's `errors` — surface them as
`integrity_errors`, matching the convention `get_screen`/`get_universe` already use.

- **Backend — `?id=` read on the screen GET.** `desk_routes.py:314` `get_screen(date: str | None =
  None, ...)` gains a sibling `id: str | None = None` param. `id` given (no `date`): look up that
  exact record by `id` in `store.list()`'s records and return `{"screen": <verbatim record>}` or
  `{"screen": null}` (HTTP 200, never 404 — unknown-id is honest-null, same convention as `?date=`
  with no match). `id` **and** `date` both given: honest 4xx refusal (422, matching this router's
  existing FastAPI-validation convention — exact code not pinned by goal.md, logged as an
  assumption). `?date=` alone is byte-unchanged. Recomputes nothing, writes nothing; `ScreenStore`
  stays the only owner.
- **Backend — `integrity_errors` on the two run ledgers.** `desk_routes.py:271` `get_topup_runs`
  and `desk_routes.py:496` `get_desk_index_reconcile_runs` both currently do
  `records, _errors = store.list()` and discard the second tuple element. Stop discarding it: add
  `"integrity_errors": errors` to each response body, identical key/shape to `get_screen`'s
  (`{"file": str, "error": str}[]`) and `get_universe`'s existing usage. Zero change to
  `TopupRunStore.list()` / `ReconcileRunStore.list()` themselves (both already return
  `tuple[list[dict], list[dict]]` — `desk_topup_log.py:140`, `desk_index_reconcile.py:307`) — this
  is a pure response-shape change in the route layer.
- **Backend tests.** Extend `test_desk_screen.py` (TC-1..TC-4: `?id=` byte-identity against a
  planted same-`screen_date` two-record fixture, unknown-id → honest null, `id`+`date` → 4xx),
  `test_desk_topup_log.py` and `test_desk_index_reconcile.py` (TC-5/TC-6: a corrupt record file
  planted in a **scoped tmp store dir — never `apps/backend/.data`** → `integrity_errors` names it,
  record absent from `runs`/`latest`), `test_mcp_server.py` (TC-7/TC-8: `desk_screen` no-arg proxy
  unaffected, `get_endpoint` proxies `?id=` verbatim, `EXPECTED_TOOLS` count stays 17). Add one
  SHA-256 before/after checksum test over every universe/screen/topup-run/reconcile-run file on
  disk (TC-15) proving nothing was backfilled or rewritten by this iteration's changes.
- **Frontend — id-based history selection.** `page.tsx`:
  - `handleSelectHistoryScreen` (~:1553) switches from `fetchDeskScreenByDate(date)` to a new
    `fetchDeskScreenById(id)` API call (new function in `lib/api.ts`, mirrors
    `fetchDeskScreenByDate` byte-for-byte except the query param name).
  - `DeskHistoryRow` (~:479) / `DeskHistoryTable` (~:508) `onSelect` callback switches from
    `(date: string) => void` to `(id: string) => void`; the row's `onClick` passes `meta.id` instead
    of `meta.screen_date`.
  - Highlighting (currently `selected={meta.screen_date === selectedDate}` at ~:537) switches to
    an id-based comparison so two same-`screen_date` rows are each independently highlighted; thread
    a `selectedId` (derived from `viewingSnapshot?.id ?? latest?.id`, mirroring the existing
    `isViewingLatest` id-based check at ~:1614) down through the `DeskHistorySection`/
    `DeskHistoryTable` prop chain in place of `selectedDate`/`selectedHistoryDate`.
  - Each history row displays its own `created_utc` beside `screen_date` (currently `DeskHistoryRow`
    only renders `screen_date`, ~:498) so two same-date rows read distinctly without opening either.
  - `DeskProvenance` (`page.tsx:890`) gains two more `Metric` rows for the displayed snapshot's own
    `id` and `created_utc` (both already on `DeskScreenSnapshot`, `lib/types.ts:838` — a straight
    re-format of fields already fetched, nothing new to derive).
  - Default-view provenance copy (when `viewingSnapshot === null`, i.e. showing `latest`) is
    reworded to describe itself as the most recently **recorded** screen (`created_utc`-sorted
    `latest`), not "the latest screen date" — a copy-only change, still descriptive-measurement only
    per the copy-discipline lint.
  - All four ledger sections (Universe, Screen History, Top-up Runs, Index Reconciliation) render a
    count-plus-filename `integrity_errors` line whenever that section's own payload carries any
    entries — Universe and Screen History already receive `integrity_errors` in their payload
    (`DeskUniverseResult`/`DeskScreenListResult` per `lib/types.ts:363/516/873` already declare the
    field) but the page does not yet render it for any of the four; Top-up Runs and Index
    Reconciliation need the field threaded through their fetch results first (next bullet).
- **Frontend types/api.** `lib/types.ts`: add `integrity_errors: {file: string; error: string}[]`
  to `DeskTopupRunsListResult` (~:955) and to the reconcile-runs list result type (mirror of
  `DeskScreenListResult`'s existing field). `lib/api.ts`: no shape change needed to
  `fetchDeskTopupRuns`/`fetchDeskReconcileRuns` beyond the widened return type (`res.json()` already
  passes the field through verbatim); add `fetchDeskScreenById(id: string)` alongside the existing
  `fetchDeskScreenByDate` (~:957), same `{ok, data, error}` shape.
- **Demo-narrator.** A `[NEW]`-flagged walkthrough covering: opening the Screen History list →
  selecting the earlier of the two same-`screen_date` entries (rows + Provenance `id`/`created_utc`
  update, NFLX `1d` badge dark per goal.md's worked example) → selecting the later entry (rows +
  Provenance update, NFLX `1d` badge lit) → reading a ledger's integrity-error line. This clause is
  why the goal-decomposer set this iteration's depth to `full` (lean's demo-narrator lane runs after
  scoring — iter-11/iter-12 lesson).

## Out of scope (per goal.md, do not build)

- No new page or nav row; no change to the 5-pin snapshot key or any recorded row's stored content;
  no repair/rewrite/delete of a corrupt record — `integrity_errors` only ever *names* it; no CLI
  warmer for `?id=` (it's a GET, no compute involved); no write to `apps/backend/.data` for evidence
  capture (read the ambient store or a read-only `cp -a` copy); no new `Config` field, no new MCP
  tool, no new backend module/route beyond the additive param/field described above.

## Agents Required

- developer: yes — implement the backend `?id=`/`integrity_errors` changes + tests, and the
  frontend id-based selection/highlighting + Provenance/ledger rendering + type/api threading
  described above.

## Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/research/desk_routes.py` -- `get_screen` (~:314) gains `id` param + refusal
  branch; `get_topup_runs` (~:271) and `get_desk_index_reconcile_runs` (~:496) each add
  `"integrity_errors": errors` to their response body.
- `apps/backend/tests/test_desk_screen.py` -- `?id=` byte-identity, unknown-id honest-null,
  `id`+`date` 4xx refusal, same-`screen_date` two-record fixture.
- `apps/backend/tests/test_desk_topup_log.py` -- planted-corrupt-file → `integrity_errors` on
  `GET /research/desk/topup/runs` (scoped tmp dir only).
- `apps/backend/tests/test_desk_index_reconcile.py` -- same for
  `GET /research/desk/coverage/reconcile/runs`.
- `apps/backend/tests/test_mcp_server.py` -- `desk_screen` no-arg proxy unaffected, `get_endpoint`
  `?id=` verbatim proxy, `EXPECTED_TOOLS` stays 17.
- New/extended checksum test (in `test_desk_screen.py` or a shared desk test helper) -- SHA-256
  before/after listing of every universe/screen/topup-run/reconcile-run file on disk.
- `apps/frontend/lib/types.ts` -- `integrity_errors` field on the top-up-runs and reconcile-runs
  list result types.
- `apps/frontend/lib/api.ts` -- new `fetchDeskScreenById`; widened return types for
  `fetchDeskTopupRuns`/`fetchDeskReconcileRuns`.
- `apps/frontend/app/desk/page.tsx` -- `handleSelectHistoryScreen` (~:1553), `DeskHistoryRow`
  (~:479)/`DeskHistoryTable` (~:508) id-based select+highlight+`created_utc` display,
  `DeskProvenance` (~:890) `id`/`created_utc` rows + default-view copy reword, four ledger sections'
  `integrity_errors` line.
- `docs/handoffs/goal-desk-iter-16-dev.md` -- dev handoff (required by Definition of Done).

## UI Evolution

- New user-facing capability: any individually-recorded screen snapshot is openable from the
  history list by its own identity, including an earlier same-date recording previously
  unreachable once a later one existed; any of the four ledgers' own file-integrity problems is now
  visible on screen instead of silently dropped.
- New information displayed: displayed-snapshot `id` + `created_utc` in the Provenance panel;
  per-history-row `created_utc`; a count-plus-filename integrity-error line per ledger section when
  present.
- New user actions: click any history row (now keyed by `id`) to view that exact recording,
  including a same-date sibling.
- UI surface changes: Screen History list (id-based select/highlight + `created_utc` column),
  Provenance panel (+`id`, +`created_utc`, reworded default-view copy), all four ledger sections
  (+integrity-error line). No new page, no new nav row.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing `Metric` component for the two new Provenance rows; reuse
  the existing `EmptyState`/inline-note pattern (e.g. `desk-provenance-signature-note`) for the new
  integrity-error lines — plain text notes, not a new alert/badge component.
- Layout: no layout restructuring — additive rows/columns within the four already-shipped sections
  (Universe, Screen History, Top-up Runs, Index Reconciliation) and the Provenance panel.
- Key visual effects: none new — match the existing dark, dense, terminal-grade styling already on
  `/desk` (monospace-leaning label/numeric cell classes already in use, e.g. `LABEL_CELL`/
  `NUMERIC_CELL`/`HEADER_CELL`).
- States to handle: an integrity-error line renders only when that section's `integrity_errors`
  array is non-empty (absent otherwise, no empty-array placeholder); two same-`screen_date` history
  rows must each render distinctly selectable/highlighted (the TC-9 regression this iteration
  fixes); unknown-`id` selection leaves the currently-displayed snapshot unchanged with an error
  note (mirrors the existing unknown-`date` handling in `handleSelectHistoryScreen`).

## Key Test Scenarios

- `GET /research/desk/screen?id=<earlier same-date id>` returns that exact record byte-identical to
  its on-disk file, distinct from what `?date=` (which still resolves to the later recording) would
  return for the same date.
- `GET /research/desk/screen?id=does-not-exist` returns `{"screen": null}` at HTTP 200, never 404.
- `GET /research/desk/screen?id=X&date=Y` returns an honest 4xx.
- A corrupt record file planted in a **scoped** `TopupRunStore`/`ReconcileRunStore` dir (never
  `apps/backend/.data`) produces `integrity_errors: [{"file": ..., "error": ...}]` on the
  corresponding GET, with the corrupt record excluded from `runs`/`latest`.
- MCP `desk_screen` called with no args stays byte-identical to the no-param GET; `get_endpoint` on
  `/research/desk/screen?id=<id>` proxies verbatim; `EXPECTED_TOOLS` count is still 17.
- SHA-256 checksums of every universe/screen/topup-run/reconcile-run file on disk are identical
  before and after this iteration's test run (nothing backfilled or rewritten).
- Full backend suite green; `Config().config_fingerprint()` prints `08e471b10130e1e2`; zero diff to
  `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`/`desk_coverage.py`;
  `tests/test_copy_discipline.py` green unmodified.
- Browser (J-12, real backend carrying the real `screen-2026-07-27-*` same-date pair or an
  equivalent, after a clean `.next` rebuild — T-9): Screen History shows both same-date entries
  with distinct `created_utc` values; selecting the earlier one highlights only that row and shows
  its own rows (NFLX `1d` coverage badge dark) + its own `id`/`created_utc` in Provenance; selecting
  the later one highlights only that row and shows its own rows (NFLX `1d` badge lit) + updated
  Provenance; a planted corrupt run-record file's integrity-error line is visible and screenshotted
  in the Top-up Runs section; default-view Provenance copy reads as "most recently recorded", not
  "latest screen date".
- `[NEW]`-flagged demo-narrator walkthrough: `Demo Verdict: RECORDED` with a non-empty screenshot
  gallery covering the four steps above (history list → earlier entry → later entry →
  integrity-error line).
- Regression smoke green: J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11.

## Notes / Assumptions

- The exact HTTP status for the `id`+`date` refusal is not pinned by goal.md; 422 is the natural
  choice (matches this router's existing FastAPI-validation-refusal convention) — already logged as
  an assumption in `runs/goal-session-desk/state/assumptions.md` (`## iter-16`).
- This is a pure additive-read + disclosure iteration: no new module, route, MCP tool, or `Config`
  field. Every backend edit is confirmed against the current file (`desk_routes.py:271/314/496`
  read and verified against this plan); every frontend edit is confirmed against the current
  `page.tsx`/`lib/types.ts`/`lib/api.ts` (line anchors re-verified, not assumed from the spec).
- Environment: before running any command that writes temp files, `export
  TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-desk-iter-16.3302867"
  TMP="/home/dennis-chan/.cache/iad/iad.goal-desk-iter-16.3302867"
  TEMP="/home/dennis-chan/.cache/iad/iad.goal-desk-iter-16.3302867"`.
