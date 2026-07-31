# goal-desk-iter-29 Execution Plan

Era B "The Desk", goal-proposer journey **J-18**: every screen run (reused, cancelled, failed, or
freshly computed) leaves a durable, honest run record, and a duplicate Run Screen click on
unchanged inputs short-circuits to the already-recorded answer instead of paying for a ~101-symbol
recompute. Depth: **full** (structural — new store, new route, new shared-entry-point behavior
change, first-ever `[NEW]` demo walkthrough for this disclosure). This mirrors J-09's
`desk_topup_log.py` / J-10's reconcile-run-store discipline verbatim; it does not touch
`desk_screen.py`'s recorded snapshot/row/skip shapes, rank order, or five-pin key.

## What to Build

- **New module** `apps/backend/app/research/desk_screen_log.py` — mirror
  `desk_topup_log.py` verbatim: checksum-verified append-only run-record files (one JSON file per
  run, `file_checksum` + `record` shape), a `ScreenRunStore` class (`list()` → `(records, errors)`
  meta-only + full-detail split, `record()` the only mutation, no content-based dedup — every
  terminal run is its own genuinely distinct event), a single shared writer function
  `record_screen_run(...)`, and `resolve_desk_screen_log_dir(desk_universe_dir_resolved)` — a bare
  `TAPEOLOGY_DESK_SCREEN_LOG_DIR` env-var override else a sibling of the universe dir (the
  `resolve_desk_topup_log_dir` pattern). **No new `Config` field.**
- **Pre-check + single-writer wiring** inside `run_screen_and_record`
  (`desk_screen_compute.py:73`, the ONE shared entry point both `DeskScreenComputeManager`'s
  resolve path and the CLI's `main()` already call):
  - Resolve the five pins BEFORE the walk using ONLY existing accessors: `desk_screen.screen_as_of`,
    `UniverseStore.list()`'s latest record id, `Config.config_fingerprint()`,
    `desk_screen.compute_bar_store_signature` over `desk_coverage` — zero new derivation.
  - On a `ScreenStore.find_by_key` hit: short-circuit to the existing snapshot, `reused=True`,
    `members_attempted=0`, **zero `compute_tradability` calls**, no `BarStore` read beyond the
    index-only coverage read the pin resolution already makes.
  - On a miss: run the full walk exactly as today (zero behavior change to `compute_screen`).
  - At terminal state (done/cancelled/failed), call `record_screen_run` EXACTLY ONCE with: run id,
    `screen_date`, the five pins as resolved (each honestly `null` if the run failed before
    resolving it), started/finished UTC, terminal state, `reused`, `members_total`,
    `members_attempted`, ranked/skip-by-reason counts, `screen_id` (or `null`), and — on `failed` —
    the exception detail verbatim plus the member the walk was on. A process that dies before this
    call leaves NO record (structural, not policed).
- **New route** `GET /research/desk/screen/runs` in `desk_routes.py` — mirror
  `get_topup_runs`/`get_desk_index_reconcile_runs` exactly: honest-empty
  `{"runs": [], "latest": null}` at HTTP 200 before any run (never 404); `runs` = lightweight meta
  only (no ranked/skipped breakdown); `latest` = full record; `integrity_errors` in the same
  key/shape its three sibling desk GETs already use.
- **MCP / Config invariants** — zero MCP tool added (`get_endpoint`'s `/research/` allowlist
  already reaches the new path); confirm the suite still proves exactly 17 tools; zero new `Config`
  field; `Config().config_fingerprint()` stays `08e471b10130e1e2`.
- **Frontend** — new read-only "Screen Runs" section on `/desk`
  (`apps/frontend/app/desk/page.tsx`), beside the shipped Screen History / Top-up Runs / Index
  Reconciliation sections, built as a 4th instance of the exact same
  fetch-meta-list-plus-latest-detail component pattern (`TopupRunsSection`/reconcile-section
  precedent, ~page.tsx:977-1020 and :1180-1203): each run's date + id, terminal state, members
  attempted-of-total, ranked/skipped counts, its own recorded start→finish elapsed, produced
  snapshot id — or the honest "reused `<id>` — no walk was performed" / "nothing recorded" states —
  latest run's failure detail verbatim on failure, and the section's own `integrity_errors` line.
  Add the mirrored `DeskScreenRunRecord`/`DeskScreenRunsResult` types to `apps/frontend/lib/types.ts`
  (mirror the existing `DeskTopupRunRecord` shape). **No new ranked-table column, no change to the
  ranked table** (J-16's width contract + stored golden replay scripts stay untouched), **no new
  control** — copy is descriptive measurement only (no advice/imperative/urgency/prediction/
  efficiency-claim language); `tests/test_copy_discipline.py` must stay green unmodified.

## Agents Required

- developer: yes -- implement `desk_screen_log.py`, the `run_screen_and_record` pre-check +
  single-writer wiring, the new `GET /research/desk/screen/runs` route, the frontend Screen Runs
  section + types, and the backend tests (TC-1–TC-9, TC-14, TC-15) below. Do NOT edit the three
  named pre-existing tests
  (`test_second_run_with_identical_pins_reuses_the_existing_snapshot_no_second_file`,
  `test_cli_second_invocation_with_identical_pins_reuses_the_existing_snapshot`,
  `test_a_corrupted_snapshot_at_the_same_key_resolves_state_failed_never_a_silent_overwrite`) — if a
  genuine conflict surfaces (the J-17/`test_desk_topup_compute.py:1092` precedent), disclose it
  verbatim in the dev handoff rather than editing silently. Note: export
  `TMPDIR=/home/dennis-chan/.cache/iad/iad.goal-desk-iter-29.665075` (and `TMP`/`TEMP` the same)
  before running any test or command that writes temp files, per this run's isolation.

Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/research/desk_screen_log.py` -- NEW: `ScreenRunStore`, `record_screen_run`,
  `resolve_desk_screen_log_dir` (mirrors `desk_topup_log.py`).
- `apps/backend/app/research/desk_screen_compute.py` -- pre-check pin resolution + reuse
  short-circuit + terminal-state call to `record_screen_run` in `run_screen_and_record`; wire the
  same call in the CLI `main()`.
- `apps/backend/app/research/desk_routes.py` -- new `get_screen_run_store` dependency +
  `GET /research/desk/screen/runs` route (mirrors `get_topup_runs`/reconcile-runs routes).
- `apps/backend/tests/test_desk_screen_log.py` -- NEW: store/writer unit tests (mirrors
  `test_desk_topup_log.py`).
- `apps/backend/tests/test_desk_screen_compute.py` -- ADD TC-2..TC-9 coverage for the pre-check +
  writer wiring; do not edit the three named existing tests.
- `apps/backend/tests/test_mcp_server.py` -- confirm/assert 17-tool contract unaffected (no edit
  expected unless a count assertion needs the new path acknowledged as already-covered).
- `apps/frontend/app/desk/page.tsx` -- new "Screen Runs" section + fetch hook, mirroring the
  Top-up Runs / Index Reconciliation section pattern.
- `apps/frontend/lib/types.ts` -- add `DeskScreenRunRecord`/`DeskScreenRunsResult` types.
- `docs/handoffs/goal-desk-iter-29-dev.md` -- dev handoff (required by Definition of Done).

## UI Evolution

- New user-facing capability: the operator can see, for every screen run ever attempted --
  including reused/cancelled/failed ones -- a durable record of what happened and how long it took.
- New information displayed: per run -- date + id, terminal state, members attempted-of-total,
  ranked/skipped-by-reason counts, elapsed time, produced snapshot id (or honest reused/no-walk/
  nothing-recorded states), verbatim failure detail on failure, `integrity_errors` line.
- New user actions: none new (read-only section); the existing Run Screen button becomes cheaper on
  a duplicate-pin retrigger but is not a new control.
- UI surface changes: `/desk` gains a fourth ledger section, "Screen Runs", beside Screen History /
  Top-up Runs / Index Reconciliation. No new page, no nav-skeleton change.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the exact `Panel` + meta-list-plus-latest-detail component already
  shipped for Top-up Runs / Index Reconciliation (`page.tsx` ~:977-1020, :1180-1203) -- same table/
  detail layout, same Loading/Unavailable/Populated state handling, same `integrity_errors` line
  treatment. No new visual primitive.
- Layout: append as a fourth `<section>` after the existing "Index Reconciliation" section
  (~page.tsx:2046-2050), same dark/dense/terminal-grade house style, same 1440x900 no-horizontal-
  scroll constraint as its siblings.
- Key visual effects: none new -- match the existing sections' styling exactly (no new color, no
  new effect).
- States to handle: honest "nothing recorded" empty state (TC-10); populated state with a completed
  run (TC-11); a `reused` run's honest "no walk was performed" state (TC-12); latest run's failure
  detail rendered verbatim when `state == "failed"`.

## Key Test Scenarios

- TC-1: no screen run recorded -> `GET /research/desk/screen/runs` returns 200
  `{"runs": [], "latest": null}`.
- TC-2/TC-4: a pin-miss run walks every member, produces a golden-matching snapshot, and records
  `reused: false`, `members_attempted == members_total`, fields byte-identical to the snapshot.
- TC-3: an identical-pin retrigger records `reused: true`, `members_attempted: 0`, zero
  `compute_tradability` calls (test-asserted), same `screen_id`, no second file under `.data/screen`.
- TC-5: a cancelled run mid-walk records `state: "cancelled"`, `members_attempted < members_total`,
  `screen_id: null`, no snapshot file written.
- TC-6: a raising member records `state: "failed"` with verbatim exception detail + the raising
  member's name, no snapshot file written.
- TC-7: a writer never invoked (simulated process death) leaves the ledger with no entry for that
  run.
- TC-8: two sequential runs -- first run's file stays byte-identical (checksum unchanged) after the
  second is recorded; `runs` list carries both.
- TC-9: the three named pre-existing tests pass with zero edits to their assertions.
- TC-14: full backend suite green, fingerprint `08e471b10130e1e2` unchanged, zero new `Config`
  fields, MCP tool count exactly 17 (baseline 1,474 passed / 8 skipped or higher, exit 0).
- TC-15: before/after listing of the owner's real `apps/backend/.data` proves no file
  created/changed/removed except this journey's own new rebuildable log dir.
- TC-10/TC-11/TC-12 (browser, 1440x900, no horizontal scroll, after `rm -rf apps/frontend/.next`
  clean rebuild): empty "nothing recorded" state; populated completed-run state; a `reused` run's
  honest "no walk performed" state -- each its own screenshot.
- TC-13 (demo-narrator, `[NEW]`-flagged, first attempt): populated Screen Runs section captured over
  a fixture-scoped ledger with the scoped rig (backend + frontend) kept alive through the demo step
  and `$FRONTEND_URL` pointed at the scoped rig for the whole evidence phase (not the script's own
  `base_url` field, which the CLI overrides); distinct frame checksums verified via
  `md5sum reports/demo/goal-desk-iter-29/*.png`. If it fails for reasons outside product code,
  disclose honestly per methodology A.7 rather than block the verdict.
- Regression smoke (deterministic replay): J-03, J-04, J-05, J-06, J-07, J-09, J-10, J-12, J-16,
  J-17 all remain green; engine equivalence green; `test_copy_discipline.py` green unmodified.
