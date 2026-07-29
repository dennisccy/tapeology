# goal-desk-iter-14 Execution Plan

Era B "The Desk", iteration 14 — builds the single goal-proposer-promoted journey **J-10**: the
operator can trigger a reconciliation of the derived `bar_index` against the frozen `BarStore`, watch
it repair itself through the existing `BarIndex.reindex()`, and see before/after drift on a durable,
append-only run record plus on the briefing's own coverage badges. Era closed `GOAL_ACHIEVED` +
`CONFIRM_ACHIEVED` at iter-13 (9/9 journeys passing, `iteration-state.md`). Required-still-passing:
J-01–J-09 (smoke-replay; J-06 by its 17-tool contract test, no browser surface). Depth = **full**
(already fixed by the phase spec's own metadata, not discretionary this iteration) — this is what
lets the demo-narrator lane run BEFORE evaluator scoring, closing TC-19 in this same pass.

No drift from `docs/goal.md`: J-10 lives in the `AUTO:journeys` block, both new Data-Contract rows are
already registered in `runs/goal-session-desk/state/blueprint.md` (see its "RESOLVED at iter-14"
trailer) and `assumptions.md`'s iter-14 entry, and the phase spec's IN/OUT-OF-SCOPE lists match both
verbatim. Nothing here is scope creep; nothing flagged for exclusion.

## Lessons this iteration is built around (from this session's own evaluator log — read before starting)

1. **One-way door (iter-12).** An append-only store's honest-EMPTY screenshot can never be re-created
   once a real run record exists. On ONE scoped rig: seed → boot BOTH backend + frontend → capture the
   empty Index-Reconciliation screenshot FIRST → only then trigger a reconciliation run.
2. **Lane ordering (iter-12/13).** Demo-narrator runs before the evaluator only at `full` depth — this
   iteration's depth is already locked `full`, so this is satisfied by construction; do not let a
   retry silently fall back to `lean`.
3. **Name the scoped rig everywhere (iter-9/11).** State the exact absolute scoped-root path in the
   dev handoff, the browser-QA dispatch, and the demo-narrator dispatch — all three, not just one.
4. **A golden script can be a write path (iter-4).** If `journey-scripts/J-10.json` is recorded, assert
   the ALREADY-POPULATED Reconciliation section's read-only text on replay — never click "Reconcile
   Index" or "Run Screen" inside the golden itself.
5. **Evidence compute vs. golden replay target collide (iter-10).** Any screen computed for THIS
   iteration's evidence must run on a fresh scoped copy of `.data/`, never the store J-01–J-09's own
   goldens replay against.

## What to Build

### Backend — drift classifier + repair (new module `apps/backend/app/research/desk_index_reconcile.py`)

- `classify_drift(store: BarStore, bar_index: BarIndex) -> tuple[dict, list[dict]]` — pure composition
  of `store.list(include_bars=False)` (→ `(healthy, errors)`) and `bar_index.list()` (unfiltered → all
  `BarIndexHit(series_id, checksum, bar_count)`, called with **no** symbol/timeframe filter). **Key
  implementation fact, verified in the current tree, that resolves the "zero new accessor" constraint**:
  `BarStore._path(series_id) == self._root / f"{series_id}.json"` (`bars.py:273-274`) — a file's name
  IS its series_id with `.json` stripped. So `{Path(e["file"]).stem for e in errors}` gives the set of
  series_ids whose file exists but is corrupted, with **zero new `bars.py` accessor**:
  - bucket (a) `unindexed_series`: healthy records whose `id` has no `bar_index.list()` hit →
    `{"series_id", "symbol", "timeframe"}` from that record's own meta.
  - bucket (b) `orphan_index_rows`: indexed `series_id`s not in healthy AND not in the corrupted-file
    stem set (no file at all, healthy or corrupt) → `{"series_id"}` alone (TC-2's explicit "no symbol
    or timeframe attached").
  - bucket (c) `stale_checksum_rows`: indexed `series_id`s that ARE in the corrupted-file stem set (a
    file exists on disk under that id but the store can no longer verify/report it) → `{"series_id"}`
    alone.
  - Since `store.list()` puts each file in `healthy` XOR `errors`, never both, buckets (b)/(c) are
    mutually exclusive by construction — no extra tie-breaking logic needed.
- `run_reconcile(store: BarStore, bar_index: BarIndex) -> dict` — the SOLE walker (mirrors
  `run_topup`): `drift_before = classify_drift(...)`; `rows_indexed_before = len(bar_index.list())`;
  `bar_index.reindex(store)` (`bar_index.py:198` — the ONLY repair path, never a second one);
  `drift_after = classify_drift(...)` (re-run identical comparison, expected empty for every pair this
  run repaired); `rows_indexed_after = len(bar_index.list())`; `series_on_disk = len(healthy)`;
  `store_errors` = the SAME `errors` list `classify_drift` already computed, passed through verbatim
  (never re-derived, never dropped). Returns everything the writer needs in one dict.
- `ReconcileRunStore` (mirrors `TopupRunStore` exactly — checksum-verified load, `record()` the only
  mutation, no update/delete, **no content-based dedup**, same defensive re-roll-on-path-collision) +
  `ReconcileRunIntegrityError` (mirrors `TopupRunIntegrityError`) + `resolve_desk_index_reconcile_dir
  (desk_universe_dir_resolved: str) -> str` (mirrors `resolve_desk_topup_log_dir` verbatim: env var
  `TAPEOLOGY_DESK_INDEX_RECONCILE_DIR` override, else a sibling dir of the universe dir, e.g.
  `index_reconcile_runs` — deliberately NOT a `Config` field).
- `record_reconcile_run(store, *, config_fingerprint, started_utc, finished_utc, state, series_on_disk,
  rows_indexed_before, rows_indexed_after, drift_before, drift_after, store_errors) -> dict` — the
  SINGLE shared writer, called exactly once at terminal state (mirrors `record_topup_run`).
- `DeskIndexReconcileComputeManager` (mirrors `DeskTopupComputeManager`'s shape: lock, `_snapshot`,
  cancel event, worker thread, `snapshot()`/`trigger()`/`cancel()`/`join_all()`). **Simpler dependency
  surface than top-up's**: `trigger(bar_store, bar_index, reconcile_run_store)` needs no
  `UniverseStore`/`ResearchRegistry` (reconcile never touches universe membership or
  `record_bar_series`) — so, unlike `DeskTopupComputeManager`, this module has **no** reason to import
  from `routes.py` and carries no circular-import constraint; still place it as a module-level
  singleton behind a FastAPI dependency in `desk_routes.py` for consistency with its two siblings.
  **No CLI warmer** (assumptions.md iter-14: goal.md's J-10 text never names one; the repair is a fast,
  local, no-network rebuild, so the POST route itself already serves the "real operator run" role).

### Backend — routes (add to the existing `apps/backend/app/research/desk_routes.py`, same router)

- `get_reconcile_run_store()` / `get_desk_reconcile_manager()` dependencies (mirror
  `get_topup_run_store` / `get_desk_topup_manager`, `desk_routes.py:179-192`).
- `POST /research/desk/coverage/reconcile/compute` — trigger (mirrors `trigger_desk_topup_compute`,
  `:195-211`, minus the `universe_store`/`registry` params).
- `GET /research/desk/coverage/reconcile/compute` — poll, plain read, never triggers (mirrors `:214-221`).
- `POST /research/desk/coverage/reconcile/compute/cancel` — 409 when idle/terminal (mirrors `:224-235`).
- `GET /research/desk/coverage/reconcile/runs` — honest `{"runs": [], "latest": null}` HTTP 200 before
  any run, lightweight meta-only list (mirrors `_topup_run_meta_only` / `get_topup_runs`, `:243-260` —
  meta list omits `drift_before`/`drift_after`/`store_errors`, `latest` carries them). No new router,
  no `main.py` change — `desk_routes.router` is already mounted (`main.py:42/202`).
- No new MCP tool — `get_endpoint`'s `/research/` allowlist already reaches the new GET path.

### Backend — tests

- New `apps/backend/tests/test_desk_index_reconcile.py` (models: `test_desk_topup_log.py`,
  `test_bar_index.py`, `test_desk_topup_compute.py`): TC-1/2/3 (the three drift buckets, isolated);
  TC-4/5 (repair-and-reverify incl. the corrupt-file case, store_errors verbatim); TC-6/7/20 (honest
  empty, append-only second-run, corrupted run-record file surfaced not fabricated — reuse
  `TopupRunStore`'s own corrupted-file test as the template); TC-8 (bar-store/universe/screen/top-up
  files byte-identical before/after, SHA-256 listing); TC-9/10/11 (idle-poll-never-triggers,
  single-flight, 409-cancel-when-idle). **Test-seam note**: the real repair (classify + `reindex()` +
  classify) is fast enough that a test asserting `"running"` state needs a deterministic slow-path
  seam — mirror `test_desk_topup_compute.py`'s monkeypatch/`threading.Event` handshake technique
  (patch `bar_index.reindex` or wrap it) rather than relying on real timing.
- New golden-scoped test proving TC-12 (post-repair screen = new snapshot under a new
  `bar_store_signature`) — **zero new production code needed for this**: `bar_store_signature` already
  checksums `desk_coverage`'s index-backed reads (blueprint), so once `reindex()` adds the missing row,
  the next screen naturally gets a new signature. This test only needs to prove the existing wiring,
  not add any.
- Sentinel re-checks: full suite ≥1369 passed/8 skipped/0 failed (TC-13); `test_mcp_server.py`
  `EXPECTED_TOOLS` still 17 (TC-14); `git diff --stat` empty on `bar_index.py`, `bars.py`,
  `tradability.py`, `levels.py`, `StructureChart.tsx` (TC-15, note `desk_coverage.py` too per IN
  SCOPE); `test_copy_discipline.py` green unmodified (TC-16).

### Frontend

**Types** (`apps/frontend/lib/types.ts`, add beside the `DeskTopup*` block ~:893-950):
`DeskReconcileUnindexedSeries {series_id, symbol, timeframe}`,
`DeskReconcileOrphanRow {series_id}`, `DeskReconcileStaleChecksumRow {series_id}`,
`DeskReconcileDrift {unindexed_series, orphan_index_rows, stale_checksum_rows}`,
`DeskReconcileStoreError {file, error}`,
`DeskReconcileRunMeta {id, config_fingerprint, started_utc, finished_utc, state, series_on_disk,
rows_indexed_before, rows_indexed_after}`,
`DeskReconcileRun extends DeskReconcileRunMeta {drift_before, drift_after, store_errors}`,
`DeskReconcileRunsListResult {runs: DeskReconcileRunMeta[], latest: DeskReconcileRun | null}`,
`DeskReconcileComputeProgress {...}`, `DeskReconcileComputeSnapshot {id, state, started_utc,
finished_utc, error, progress}`.

**API** (`apps/frontend/lib/api.ts`, mirror the `DeskTopup*` functions at `:1050-1130`):
`triggerDeskReconcileCompute()`, `fetchDeskReconcileCompute()`, `cancelDeskReconcileCompute()`,
`fetchDeskReconcileRuns()` against the four routes above.

**`apps/frontend/app/desk/page.tsx`**:
- `ReconcileIndexControl` component mirroring `TopupComputeControl` (`:788-865`ish) — button label
  states (idle/"Reconciling…"/retry-on-failed), live progress, cancel with the same
  cancelling-copy pattern, `data-testid="desk-reconcile-*"` mirroring `desk-topup-*`.
- `ReconciliationSection`/`IndexReconciliationTable` component mirroring `TopupRunsSection` — latest
  run's `series_on_disk`, `rows_indexed_before`/`after`, the affected pairs from `drift_before`, and
  `store_errors` verbatim; honest "no reconciliation run recorded yet" empty state.
- New `<section aria-label="Index Reconciliation" className="mt-6">` (Panel title "Index
  Reconciliation") placed immediately after the existing `<section aria-label="Top-up runs">`
  (`:1276-1280`) — same "always rendered, independent of screen state" placement precedent J-09
  established, not gated on the screen conditional above it.
- New state hooks (`reconcileCompute`, `reconcileTriggering`, `reconcileTriggerError`,
  `reconcileCancelRequested`, `reconcileCancelError`, `reconcileRunsResult`) mirroring the
  `topup*`/`topupRunsResult` hooks exactly.
- Mount-time effect (`:1061-1078`): add `fetchDeskReconcileCompute()` and `fetchDeskReconcileRuns()` to
  the existing GET batch → 6 GETs, still zero POSTs on load (T-4/5C).
  Poll effect (`:1111-1124` is the direct template): while `reconcileCompute?.state === "running"`,
  poll every 700ms; on terminal, refetch `fetchDeskReconcileRuns()` once, "keep last known state on a
  failed refetch" discipline preserved.
- **Build-discretion call, log the final choice**: place `ReconcileIndexControl` as a third control
  beside `ScreenComputeControl`/`TopupComputeControl` inside the existing "Run Screen and Top-up
  controls" panel (`:1006-1013`) — recommended, since goal.md step 5 says the trigger is "wired exactly
  like the existing Top-up button" and this keeps every trigger control in one place while the
  read-only history sections (Screen History / Top-up Runs / Index Reconciliation) stay grouped
  separately at the page's bottom. Not a hard requirement; disclose if a different placement is chosen.

### Golden replay, demo-narrator, handoff

- `runs/goal-session-desk/journey-scripts/J-10.json` (new, scoped backend) — per lesson 4 above, assert
  the ALREADY-POPULATED Reconciliation section's read-only text; a post-match liveness assertion
  (iter-4 lesson).
- `[NEW]`-flagged demo-narrator walkthrough (TC-19) — downstream lane, runs before evaluator at this
  iteration's locked `full` depth: empty state narrated first, populated state second, same rig.
- `docs/handoffs/goal-desk-iter-14-dev.md` — MUST name the exact absolute scoped-rig path (lesson 3).

## Agents Required

- developer: yes — implements the full stack in one TDD pass (backend module/store/manager/routes +
  frontend types/api/components/wiring); the two halves share one data shape and are tightly coupled.
- backend-data: yes — `desk_index_reconcile.py` (classifier, store, compute manager), the four new
  `desk_routes.py` routes, `test_desk_index_reconcile.py`, running the full suite + fingerprint +
  17-tool + copy-discipline sentinels, the scoped-rig seeding/drift-planting for evidence.
- frontend-ux: yes — `types.ts`/`api.ts` additions, `ReconcileIndexControl` +
  `ReconciliationSection` + page wiring in `desk/page.tsx`, the T-9 clean rebuild before any browser
  evidence.

## Frontend Present

Frontend Present: yes

## Files to Create/Modify

New:
- `apps/backend/app/research/desk_index_reconcile.py`
- `apps/backend/tests/test_desk_index_reconcile.py`
- `runs/goal-session-desk/journey-scripts/J-10.json`
- `docs/handoffs/goal-desk-iter-14-dev.md`

Modify:
- `apps/backend/app/research/desk_routes.py` — four new routes + two new dependencies (imports from
  `desk_index_reconcile.py`, same pattern as its `desk_topup_log`/`desk_topup_compute` imports).
- `apps/frontend/lib/types.ts` — the `DeskReconcile*` interfaces.
- `apps/frontend/lib/api.ts` — the four `*DeskReconcile*` functions.
- `apps/frontend/app/desk/page.tsx` — new components, new section, new state/effects, control
  placement (see build-discretion note above).

**Zero diff required (hard requirement, TC-15 + IN SCOPE)** — verify via `git diff --stat` in the dev
handoff: `apps/backend/app/research/bar_index.py`, `bars.py`, `tradability.py`, `levels.py`,
`desk_coverage.py`, `apps/frontend/components/StructureChart.tsx`, `PriceChart.tsx`, `config.py`,
`meta.py`, `app/mcp/__init__.py`. No new `Config` field anywhere.

## Evidence sequencing protocol (binding — one fresh scoped `.data/` copy, never ambient)

1. Seed a fresh scoped root (distinct name from every prior iteration's, e.g.
   `desk-iter14-scoped-qa`), via the existing `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh`.
2. Plant the TC-1 drift case (a bar series recorded with no matching `bar_index.db` row) and, if
   convenient, the TC-3 corrupt-file case, directly into the scoped copy.
3. Register a small scoped universe snapshot covering the affected symbol.
4. `rm -rf apps/frontend/.next` (T-9), boot BOTH scoped backend and frontend against that root.
5. Compute screen run #1 so the affected row exists with a dark coverage badge.
6. Capture TC-17 (honest empty Reconciliation state + the dark badge) NOW — this is the one-way door.
7. Trigger one reconciliation run (the real UI button or `POST`, on the scoped rig).
8. Compute screen run #2 (same universe/as-of) so the same row now shows a lit badge — this is a NEW
   append-only snapshot, never a rewrite of run #1's file.
9. Capture TC-18 (drift counts + the lit badge).
10. Record the `[NEW]`-flagged demo-narrator walkthrough (TC-19) against this same still-live rig,
    narrating steps 6 and 9's states in order.
11. Replay J-01–J-09 smoke set against the same scoped rig; checksum the ambient `.data/` tree
    before/after everything and prove zero write landed there.

State the scoped root's absolute path in the dev handoff, the browser-QA dispatch, AND the
demo-narrator dispatch (lesson 3) — not just one.

## UI Evolution

- New user-facing capability: the operator can trigger, from `/desk`, a reconciliation of the derived
  bar-coverage index against the frozen bar store, watch live progress with cancel, and read the
  latest run's before/after drift counts and affected pairs.
- New information displayed: series-on-disk count, rows-indexed before/after, affected symbol×timeframe
  pairs before/after repair, store errors verbatim; honest "no reconciliation run recorded yet" empty
  state.
- New user actions: "Reconcile Index" button (trigger); a cancel control while running (mirrors
  Top-up's cancel incl. 409-when-idle).
- UI surface changes: one new read-only section on the existing `/desk` page, beside Top-up Runs. No
  new page.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse `Panel`, `EmptyState`, `HEADER_CELL`/`LABEL_CELL`/`NUMERIC_CELL`,
  `PRIMARY_BUTTON_CLASS`/`CANCEL_BUTTON_CLASS` — zero new design tokens, matches Top-up Runs/
  Top-up button styling exactly.
- Layout: same stacked `<section aria-label="...">` single-column pattern; Index Reconciliation section
  immediately after Top-up Runs; trigger control recommended inside the existing Run Screen/Top-up
  controls panel (see build-discretion note).
- Key visual effects: none new — dense/terminal-grade table + button, no glow/gradient/animation beyond
  what Top-up already uses. Copy is descriptive measurement only (counts, pair names, dates) — no
  advice/urgency/prediction language (`test_copy_discipline.py` stays green unmodified).
- States to handle: honest empty state before any run; running state with live progress + cancel;
  populated state with drift counts + affected pairs + store errors, all legible in one screenshot
  (TC-18); the same coverage badge dark-before/lit-after on the ranked table (already-shipped J-02
  component, zero change — just a new data value flowing through it).

## Key Test Scenarios

Full contract is TC-1..TC-20 in `docs/phases/goal-desk-iter-14.md`; condensed:

- TC-1/2/3: the three drift buckets, isolated and exact (unindexed→symbol+timeframe; orphan→series_id
  alone; stale-checksum→series_id alone).
- TC-4/5: a reconciliation run flips `GET /research/desk/coverage`'s `has_bars` false→true for the
  drifted pair; a corrupt file's `store_errors` entry matches `BarStore.list()`'s own `errors` verbatim
  and the rebuilt index carries no row for it.
- TC-6/7/20: honest-empty before any run; second run appends without touching the first file
  (checksum unchanged); a corrupted run-record file is surfaced as a named error, never dropped/faked.
- TC-8: every `.data/bars/*.json` file and every previously recorded universe/screen/top-up file is
  byte-identical (SHA-256) before and after a reconciliation run.
- TC-9/10/11: idle GET never triggers a run; a second POST while running returns `started:false`
  unchanged; cancel while idle/terminal returns 409.
- TC-12: a post-repair NEW screen is a new append-only snapshot under a new `bar_store_signature`; the
  pre-repair screen file's checksum is unchanged.
- TC-13..16: full suite green, fingerprint `08e471b10130e1e2` unchanged, zero new Config field, MCP
  still 17 tools, zero diff on the five named files, copy-discipline lint green unmodified.
- TC-17/18 (browser, ONE scoped rig, in order): honest-empty Reconciliation section + dark badge
  screenshot, THEN drift-counts + lit-badge screenshot after one reconcile run + one new screen run.
- TC-19: `[NEW]`-flagged demo-narrator walkthrough, empty state before populated state, same rig.
- TC-20: covered under TC-6/7 above (corrupted run-record file honesty).

## Out of Scope

- CLI warmer for reconcile (goal.md's J-10 text never names one; logged in `assumptions.md` iter-14).
- Any new MCP tool (`get_endpoint`'s `/research/` allowlist already reaches the new GET route).
- Any change to `bar_index.py`/`bars.py` beyond their existing public reads — no new accessor, no
  schema change (the filename-stem insight above makes this achievable with zero new accessor).
- Any change to `desk_coverage.py`, `tradability.py`, `levels.py`, `StructureChart.tsx`.
- Repairing/rewriting a corrupt bar-series file itself — index-only repair; the file stays untouched,
  disclosed as a store error.
- A PnL-ledger append (goal.md's SSOT criterion substitutes for it explicitly).
- Any scheduler/auto-run/cron trigger — reconciliation stays an explicit operator act.
- Running the real ~88-pair ambient-store reconciliation as an automated gate — fixture-scoped drift
  only; the real run is a later, honestly-reported operator act.
- The two other backlogged proposer candidates (top-up-runs `integrity_errors` disclosure;
  coverage-freshness date-format consistency) — not promoted this cycle.
- Any nav-skeleton change — the section lives on the already-registered `/desk` home.
- Widening, disabling, or bypassing the host-guard CPU caps (`4-7,12-15`) for any process this
  iteration starts, even to make setup/evidence capture faster — `critical` anti-goal.

## Project alignment check

Directly advances Success Criteria #3/#4 (the screen's coverage badges become independently
checkable, not silently trusted) with zero new research math, zero fingerprint movement, and zero
touch to any frozen foundation. Builds on, not duplicates, existing architecture: reuses
`BarIndex.reindex()` (the only repair path, already exists, currently unreachable by any operator —
that gap is exactly what this iteration closes), mirrors `desk_topup_log.py`'s store discipline and
`DeskTopupComputeManager`'s compute-manager shape verbatim, and reuses the same scoped-rig script and
demo-narrator/browser-QA pipeline lanes prior iterations already proved out. If every clause above
holds, this returns the era to 10/10 journeys `passing`; whether that means `GOAL_ACHIEVED` is the
evaluator's call, not presumed here.
