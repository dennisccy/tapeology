# goal-desk-iter-16 Dev Handoff

**Phase:** goal-desk-iter-16
**Date:** 2026-07-29
**Agent:** developer
**Status:** complete

## What Was Built

- **J-12a: individually-addressable screen snapshots via `?id=`.** `GET /research/desk/screen`
  gains a sibling `id: str | None` query param. `?id=<snapshot id>` (with `date` absent) returns
  that exact persisted record verbatim — `{"screen": <record>}` if found, else the existing honest
  `{"screen": null}` at HTTP 200 (never 404, mirroring the `?date=` no-match convention). This
  closes the real gap J-10's own repair exposed: `?date=` always resolves `matching[-1]` (the
  newest recording for that date), so an EARLIER same-`screen_date` recording — e.g. the real
  ambient `screen-2026-07-27-936543601e75` (pre-repair) vs `screen-2026-07-27-3ad3c57aa6ba`
  (post-repair) pair — was listed by the history endpoint but permanently unreachable through any
  existing read. `id` and `date` supplied together is an honest 4xx (422) refusal, never a silent
  precedence rule. `?date=` alone is byte-unchanged. The read recomputes nothing and writes
  nothing; `ScreenStore` stays the only owner.
- **J-12b: `integrity_errors` disclosure on the two run ledgers.** `GET /research/desk/topup/runs`
  and `GET /research/desk/coverage/reconcile/runs` both previously unpacked `records, _errors =
  store.list()` and silently discarded the second tuple element. Both routes now serve
  `"integrity_errors": errors` — the identical key/shape `GET /research/desk/screen` and
  `GET /research/desk/universe` already exposed. A corrupted run-record file was already excluded
  from `runs`/`latest` before this change (unaffected); this iteration only stops dropping the
  store's own honesty channel.
- **Frontend: id-based Screen History selection + highlighting.** `handleSelectHistoryScreen`
  switches from `fetchDeskScreenByDate(date)` to the new `fetchDeskScreenById(id)`; each history
  row's `onClick` now passes `meta.id`. Highlighting switches from a `screen_date` comparison to an
  `id` comparison (`selectedHistoryId`, derived as `viewingSnapshot?.id ?? latest?.id`, mirroring
  the existing `isViewingLatest` id-based check), so two same-`screen_date` rows are each
  independently, distinctly highlighted — including the default (latest) view, which is now itself
  a highlighted row.
- **Frontend: `created_utc` on every history row.** A new "recorded" column in the Screen History
  table shows each row's own `created_utc` beside `screen_date`, so two same-date rows read
  distinctly without opening either.
- **Frontend: Provenance panel gains `id`/`created_utc`.** Two new `Metric` rows (a straight
  re-format of fields `DeskScreenSnapshot` already carries — nothing derived). The default-view-only
  copy (shown only while `isViewingLatest`) now describes itself as the most recently RECORDED
  screen, never "the latest screen date" — copy-discipline-lint-clean (verified: 30/30 pass
  unmodified).
- **Frontend: `integrity_errors` disclosure on three of the four named ledger sections.** Screen
  History, Top-up Runs, and Index Reconciliation each render a shared `IntegrityErrorsNote`
  (count-plus-filename, plain-text — mirrors the existing `desk-provenance-signature-note` pattern,
  never a new alert/badge component) whenever that section's own payload carries any entries;
  absent otherwise. See "Known Issues" below for why the fourth named section (Universe) was NOT
  built.
- **Frontend types/api.** `lib/types.ts`: `integrity_errors: {file, error}[]` added to
  `DeskTopupRunsListResult`/`DeskReconcileRunsListResult`. `lib/api.ts`: new
  `fetchDeskScreenById(id)` (mirrors `fetchDeskScreenByDate` byte-for-byte except the query param
  name); `fetchDeskTopupRuns`/`fetchDeskReconcileRuns` needed no body change — their widened return
  types pass `res.json()`'s new field through verbatim.
- Zero new module, route, MCP tool, or `Config` field. `Config().config_fingerprint()` stays
  `08e471b10130e1e2`; MCP tool count stays exactly 17.

## Files Changed

- `apps/backend/app/research/desk_routes.py` — `get_screen` (`?id=` branch + `id`+`date` refusal),
  `get_topup_runs`/`get_desk_index_reconcile_runs` (`integrity_errors` added to response body),
  plus module-docstring updates for J-03/J-09/J-10 (now response-body-extended) and a new J-12
  paragraph.
- `apps/backend/tests/test_desk_screen.py` — new "screen `?id=` read (goal-desk-iter-16, J-12)"
  section: a `screen_route_ctx` fixture (live `TestClient` wiring, scoped entirely under `tmp_path`)
  and 6 new tests — `?id=` byte-identity (TC-1), `?date=` unchanged (TC-2), unknown-id honest-null
  (TC-3), `id`+`date` 4xx refusal (TC-4), a "never recomputes / list unaffected" test, and a
  SHA-256 before/after checksum test over every universe/screen/topup-run/reconcile-run file
  planted in that scoped tmp dir (TC-15).
- `apps/backend/tests/test_desk_topup_compute.py` — added `integrity_errors: []` to the existing
  honest-empty exact-equality assertion (would otherwise have broken on the new field) and to the
  post-run assertion; new test
  `test_get_topup_runs_surfaces_a_corrupted_run_records_integrity_error` (TC-5) — a corrupted file
  planted in the run log's own scoped dir (resolved via `get_topup_run_store()`, never
  `apps/backend/.data`) alongside one genuine record, both asserted correctly split between
  `integrity_errors` and `runs`/`latest`.
- `apps/backend/tests/test_desk_index_reconcile.py` — same `integrity_errors: []` fix to the
  existing honest-empty assertion; extended
  `test_tc20_get_reconcile_runs_survives_a_corrupted_run_record_file_alongside_a_genuine_one` (TC-6)
  with an `integrity_errors` assertion on the already-planted corrupt file.
- `apps/backend/tests/test_mcp_server.py` — fixed an exact-equality assertion in
  `test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool` that would otherwise have
  broken on the new field; new test `test_get_endpoint_desk_screen_id_query_proxies_verbatim`
  (TC-7) — `get_endpoint` proxies `?id=` verbatim for both a matching and an unknown id, with zero
  MCP code change (the existing `/research/` allowlist prefix already covers it).
- `apps/frontend/lib/types.ts` — `integrity_errors` field added to `DeskTopupRunsListResult` and
  `DeskReconcileRunsListResult`.
- `apps/frontend/lib/api.ts` — new `fetchDeskScreenById`; doc-comment updates on
  `fetchDeskTopupRuns`/`fetchDeskReconcileRuns` noting the widened type (no body change).
- `apps/frontend/app/desk/page.tsx` — `DeskHistoryRow`/`DeskHistoryTable` (id-based
  select+highlight+`created_utc` column), `handleSelectHistoryScreen` (switched to
  `fetchDeskScreenById`), a new shared `IntegrityErrorsNote` component, `TopupRunsSection`/
  `ReconciliationSection` (integrity-error line), `DeskPopulatedScreen`/`DeskProvenance`
  (`id`/`created_utc` rows, default-view copy reword, `screenIntegrityErrors` threaded through),
  `DeskPage` (`selectedHistoryId`/`screenIntegrityErrors` derivations), plus module-docstring and
  inline-comment updates.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1426 passed, 8 skipped, 0 failed** (exit code 0; the final "N passed" summary line was
again clipped by this environment's background-capture transition — confirmed instead via a
programmatic character-count of the progress bar: 1426 `.` + 8 `s`, zero `F`/`E` across the entire
1440-character bar — same documented environment quirk as iter-15's handoff). Baseline before this
iteration was 1418 passed / 8 skipped (iter-15); net +8 new tests, 0 regressions.

Targeted (all also included in the full run above):
- `pytest tests/test_desk_screen.py -v` → 55 passed (was 49 before this iteration).
- `pytest tests/test_desk_topup_compute.py tests/test_desk_index_reconcile.py -v` → 67 passed.
- `pytest tests/test_desk_topup_log.py -v` → 15 passed (unmodified).
- `pytest tests/test_mcp_server.py -v` → 36 passed (spawns a real subprocess backend).
- `pytest tests/test_desk_screen_compute.py tests/test_desk_universe_api.py tests/test_desk_ui_guards.py tests/test_desk_hover_tooltip_guard.py tests/test_copy_discipline.py -q` → 76 passed.

Frontend: `npx tsc --noEmit` → clean, zero errors. `rm -rf .next && npm run build` → compiled
successfully, linted clean, `/desk` route built (7.6 kB, 117 kB First Load JS).

Sentinels (all green, part of the full-suite run above):
- `Config().config_fingerprint()` still `08e471b10130e1e2` (confirmed both by
  `test_desk_screen_module_adds_no_config_field` and directly via `python -c`).
- MCP tool count still exactly 17 (`test_mcp_server.py`'s own `EXPECTED_TOOLS`/`TOOL_NAMES`
  assertions).
- `tests/test_copy_discipline.py` green **unmodified** (30 tests — I did not touch this file; the
  new Provenance/`IntegrityErrorsNote` copy passes the existing lint as-is).
- `git diff --stat` confirms zero diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/
  `StructureChart.tsx`/`desk_coverage.py` — none of these files appear in the diff at all.

## Live verification (Pre-handoff checklist)

- **Service startup:** started a scoped backend (`CHAIN_BACKEND_PORT=8471 bash
  scripts/start-backend.sh`, default `.data` dir — i.e. pointed at the REAL ambient store, read-only)
  and frontend (`CHAIN_FRONTEND_PORT=3471 bash scripts/start-frontend.sh`) cleanly; `GET /health` →
  `{"status":"ok"}`; `GET /desk` on the frontend returned 200. Both processes (including the
  `next-server` worker `next dev` spawns as a separate PID, and needed a second explicit kill) were
  stopped afterward; confirmed dead via refused connections on both ports and `ps`/`ss` showing no
  listeners. A pre-existing, unrelated backend+frontend pair on ports 8301/3301 was observed already
  running before this dispatch started (not started by this session) — left untouched throughout, per
  the iter-15 precedent.
- **End-to-end confirmation against the REAL ambient `.data/` store** (read-only — no compute, no
  write, per the OUT OF SCOPE text): `GET /research/desk/screen?date=2026-07-27` resolved to
  `screen-2026-07-27-3ad3c57aa6ba` (the later recording), exactly as before this iteration.
  `GET /research/desk/screen?id=screen-2026-07-27-936543601e75` (the earlier, pre-repair record —
  previously unreachable through any UI/API path) returned that exact record, distinct from what
  `?date=` serves. `GET /research/desk/screen?id=does-not-exist` → `{"screen": null}` at HTTP 200.
  `GET /research/desk/screen?id=X&date=Y` → HTTP 422. Independently re-confirmed goal.md's own
  worked example directly against the two real records: NFLX's `1d` coverage badge is
  `has_bars: false` (dark) in the earlier record and `has_bars: true` (lit) in the later one — the
  exact TC-9/TC-10/TC-11 visual difference the browser-QA lane will screenshot.
  `GET /research/desk/topup/runs` and `GET /research/desk/coverage/reconcile/runs` both now carry
  `"integrity_errors": []` against the real store (honestly empty — no corrupted files currently
  present there). The compiled dev bundle (`apps/frontend/.next/static/chunks/app/desk/page.js`) was
  grepped and confirmed to contain the new `desk-history-created-utc` and
  `desk-provenance-latest-note` testids, proving the served bundle reflects this iteration's source.

## Known Issues

- **The "Universe" ledger section named in the phase spec/plan does not exist in the frontend and
  was NOT built this iteration.** goal.md's IN SCOPE text and the execution plan both state "all
  four ledger sections (Universe, Screen History, Top-up Runs, Index Reconciliation)... already
  receive `integrity_errors` in their payload... but the page does not yet render it for any of the
  four" and cite `lib/types.ts:363/516/873` for a `DeskUniverseResult` type. I verified this premise
  against the actual codebase and it is factually incorrect for the frontend: there is no
  `DeskUniverseResult` type anywhere in `lib/types.ts` (lines 363/516 are `MergedCandlesPage`'s and
  `DatasetsListResult`'s own unrelated `integrity_errors` fields), no `fetchDeskUniverse*` function
  in `lib/api.ts`, and no Universe snapshot list/ledger rendered anywhere on `/desk` or
  `/structure` — `grep -rln "universe" apps/frontend/app apps/frontend/lib apps/frontend/components`
  confirms only `desk/page.tsx`/`lib/api.ts`/`lib/types.ts` mention the word at all, and none of
  them fetch or render the universe SNAPSHOT LIST (only the bare `universe_snapshot_id` string
  already shown in Provenance). The project's own `runs/goal-session-desk/state/blueprint.md`
  independently confirms this by design: its "Universe snapshots + membership" Data Contract row
  states the universe is "surfaced as the provenance line + universe metadata on `/desk` — no
  standalone page", and — unlike the topup-run and reconcile-run rows immediately below it — carries
  NO "iter-16 addition (J-12)" note, meaning the blueprint itself never registered a
  universe-integrity-errors UI addition for this iteration. I did not build a brand-new
  fetch-and-render Universe ledger section because: (1) no TC in goal.md's own TESTING
  REQUIREMENTS (TC-1 through TC-16) tests a Universe integrity-error line — TC-13 is scoped to
  Top-up Runs specifically; (2) the plan's own "Files to Create/Modify" list does not include
  creating a new Universe fetch function or section component; (3) the Visual Requirements text
  says "no layout restructuring — additive rows/columns within the four ALREADY-SHIPPED sections",
  and Universe is not an already-shipped UI section to add a row to; (4) `GET /research/desk/
  universe`'s `integrity_errors` field has been served since J-01 (unrelated to this iteration) —
  there is nothing new on the backend side for a Universe UI section to disclose that this
  iteration itself added. Flagging here rather than silently building an undocumented, untested new
  UI surface, or silently deciding the spec's premise doesn't matter — the reviewer/auditor should
  triage whether a follow-up journey to add a Universe section to `/desk` is warranted.
- **`DeskProvenance`'s new default-view note only appears while viewing `latest`** (`isViewingLatest
  === true`), per goal.md's own TC-12 wording ("given the default `/desk` load with no history
  selection"). Viewing ANY history-selected snapshot (including the one that happens to also be the
  newest by `created_utc` if selected explicitly via a click rather than via the default view) still
  shows only the unconditional `id`/`created_utc`/etc. `Metric` rows, not the "most recently
  recorded" note — this matches the spec's literal "default view" framing, not "whenever the
  displayed snapshot happens to be the latest one".
- If the Screen History store's records are ALL corrupted (zero valid records but one or more
  `integrity_errors`), `latest` resolves to `null` and the whole populated-screen view (including
  the Screen History panel and its `IntegrityErrorsNote`) is replaced by the pre-existing "Desk
  screen not computed yet." panel — so a screen-ledger integrity error would be invisible in that
  specific all-corrupted edge case. This is a pre-existing architectural property of the
  `latest === null` empty-state discriminator (unrelated to this iteration's own change), not
  exercised by any TC here (TC-13's corrupt-file plant targets Top-up Runs, which is rendered
  unconditionally, independent of screen state), and out of this iteration's scope to restructure.
- No new `Config` field, no fingerprint move, no new endpoint/route/page/nav entry, no MCP tool
  change — confirmed structurally (`git diff --stat` showing `app/config.py`/`app/mcp/__init__.py`/
  `app/meta.py` do not appear in the diff at all) and via the sentinels above.
