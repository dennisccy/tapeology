# goal-rapid-microscope-iter-33 Dev Handoff

**Phase:** goal-rapid-microscope-iter-33
**Date:** 2026-08-24
**Agent:** developer
**Status:** complete

## What Was Built

J-12: a read-only **Feature Snapshots** section on `/desk` (directly below the shipped Graduation
section), plus two new honest disclosure counts on `GET /research/desk/micro/snapshots`, plus a
byte-identical `desk_micro_snapshots` MCP proxy (contract v7→v8, 27→28 tools), plus J-02's owed
golden extension.

- **Backend**
  - `micro_snapshots.py`: new `snapshot_meta_report(root_dir, dataset_store, config) -> dict`
    performs the ONE meta-directory walk and returns
    `{"snapshots": [...], "withheld_excluded": int, "stale_excluded": int}`.
    `withheld_excluded` is **pool-derived** — computed via the module's own shared
    `_unresolved_pool_ids` choke point over the store's FULL `dataset_store.list()` record set
    (the SAME predicate `withheld_dataset_ids_for_store`/`exclude_withheld` already share) — never
    a count of which withheld ids happen to have a `*.meta.json` file present on disk.
    `stale_excluded` is computed AFTER the withheld filter, over the meta files actually on disk:
    a meta file whose `load_snapshot_meta` re-verification misses counts once, never carrying its
    stale value. `list_snapshot_meta` (existing, exported) now delegates to
    `snapshot_meta_report(...)["snapshots"]` — unchanged list-only shape for its existing (only)
    caller.
  - `micro_routes.py`: `GET /research/desk/micro/snapshots` now returns
    `snapshot_meta_report(...)` verbatim (existing `snapshots` key byte-identical; no new
    endpoint, no second computation path).
  - `app/mcp/__init__.py`: added `desk_micro_snapshots` to `_STATIC_PATHS`
    (`/research/desk/micro/snapshots`) and its `types.Tool` entry, positioned immediately after
    `desk_micro_readiness` and before `desk_scout` (dependency-order sibling rule). MCP contract
    bumped to v8 (27 → 28 tools) in the module docstring and inline comments.
  - `tests/test_mcp_server.py`: `EXPECTED_TOOLS` grown to the 28-tuple with
    `desk_micro_snapshots` immediately after `desk_micro_readiness`; two new byte-identity tests
    (`test_desk_micro_snapshots_tool_byte_identical_on_the_honest_empty_state` /
    `..._on_a_populated_state`, the latter seeding a real snapshot through
    `run_snapshot_build_and_record` against a live backend's env-scoped dataset dir, never a live
    `POST /snapshots/compute` run); three previously-hardcoded `len(TOOL_NAMES) == 27` assertions
    bumped to `28`.
  - `tests/test_desk_ui_guards.py`: `_PRICE_ARITHMETIC_FIELDS` extended with
    `snapshot.(row_count|bytes_on_disk)` and `report.(withheld_excluded|stale_excluded)`, plus a
    seeded counter-test proving the guard is live
    (`test_desk_page_price_arithmetic_guard_catches_feature_snapshots_arithmetic`).
  - `tests/test_vault.py`: extended the TR-2 join-resistance sweep (explicit
    `swept["/research/desk/micro/snapshots"] == 200` sanity assertion) and the MCP-surface-closure
    structural test (`"/research/desk/micro/snapshots" in research_tool_paths`); added a new
    counter-test proving `withheld_excluded` is pool-derived, not snapshot-file-derived — TC-7
    (`test_tc7_micro_snapshots_withheld_excluded_is_pool_derived_not_snapshot_file_derived`):
    registers a universe whose rule matches one real dataset's own `(symbol, session_date)`,
    never sealing it and never building any snapshot at all, and asserts the served
    `withheld_excluded == 1` while `snapshots == []` — proving the count cannot be file-derived
    (a withheld shard's snapshot build never runs).
  - `tests/test_micro_snapshots.py`: fixed the one pre-existing exact-equality assertion
    (`test_get_snapshots_is_an_honest_empty_list_on_a_fresh_store`) to the new additive response
    shape; added `withheld_excluded`/`stale_excluded` assertions to
    `test_snapshots_route_lists_a_built_snapshot` and `test_tc12_real_corpus_listed_via_the_route`
    (the latter asserts presence/non-negativity only — the real `.data` store's actual
    `withheld_excluded` reflects whatever vault universes the operator has genuinely registered
    across later eras, not this fixture's concern); two new unit tests for
    `snapshot_meta_report` directly (`test_snapshot_meta_report_counts_a_present_but_no_longer_
    identity_matching_meta_as_stale`, `test_snapshot_meta_report_withheld_excluded_is_pool_
    derived_over_the_full_registered_corpus`).
  - New fixture-scoped seed script `apps/backend/scripts/seed_micro_snapshots_iter33_disclosure_
    fixture.py`: plants one valid snapshot (real build), one stale meta (real build, then its
    OWN persisted `dataset_checksum` mutated — the only faithful way to construct a "built, then
    invalidated" fixture without changing the running code's own bytes), and one withheld pool
    member (a registered universe whose rule matches its `(symbol, session_date)`, never sealed,
    never snapshotted) — self-checks its own three-way split before exiting. Regression-tested by
    the new `tests/test_seed_micro_snapshots_iter33_disclosure_fixture.py`.

- **Frontend**
  - `lib/types.ts`: `SnapshotMeta`, `DeskMicroSnapshotsResponse`, `DeskMicroSnapshotRunLogEntry`,
    `DeskMicroSnapshotRunsResponse`.
  - `lib/api.ts`: `fetchDeskMicroSnapshots()` / `fetchDeskMicroSnapshotsRuns()`.
  - `app/desk/page.tsx`: `"featureSnapshots"` added to `DeskCollapsibleSection`; two new
    fetch-on-expand state slices (`snapshotsResult`, `snapshotsRunsResult`); a new
    `FeatureSnapshotsSection` component (testid family `micro-snapshots-*`, T-11) rendering the
    snapshot table (dataset id, snapshot format version, algo version, config fingerprint,
    feature source hash, params hash, quote size unit, row count, bytes on disk, built at) plus
    the `withheld_excluded`/`stale_excluded` disclosure line plus the build-run history table
    (newest-first, exactly as served) — no client-side aggregate, derived count, re-ordering, or
    recomputation. Read-only: no build button, `/snapshots/compute` stays UI-unreachable. Wired as
    a new `<section aria-label="Feature Snapshots">`/`<CollapsibleSection id="featureSnapshots">`,
    the sixth Rapid-Microscope section, directly below Graduation and immediately before
    `</main>`.

- **Journey golden**: `runs/goal-session-rapid-microscope/journey-scripts/J-02.json` gained step 3
  — clicks `desk-section-expand-featureSnapshots`, asserts the statically-rendered
  `"Withheld (excluded):"` label (the section's own always-present shell text, never an
  async-loaded row or table cell) — this doubles as J-02's owed element close-up per the spec.

## Files Changed

- `apps/backend/app/research/micro_snapshots.py` — `snapshot_meta_report` + `list_snapshot_meta` delegation
- `apps/backend/app/research/micro_routes.py` — `GET /snapshots` returns the new report shape
- `apps/backend/app/mcp/__init__.py` — `desk_micro_snapshots` tool, contract v7→v8
- `apps/backend/tests/test_mcp_server.py` — 28-tuple + two new byte-identity tests + count bumps
- `apps/backend/tests/test_desk_ui_guards.py` — guard field extension + counter-test
- `apps/backend/tests/test_vault.py` — TR-2/structural extensions + TC-7 counter-test
- `apps/backend/tests/test_micro_snapshots.py` — fixed exact-equality test + new unit tests
- `apps/backend/scripts/seed_micro_snapshots_iter33_disclosure_fixture.py` — new fixture seed script
- `apps/backend/tests/test_seed_micro_snapshots_iter33_disclosure_fixture.py` — new regression test
- `apps/frontend/lib/types.ts` — new snapshot/run response types
- `apps/frontend/lib/api.ts` — two new fetch functions
- `apps/frontend/app/desk/page.tsx` — `FeatureSnapshotsSection` + wiring
- `runs/goal-session-rapid-microscope/journey-scripts/J-02.json` — step 3 added

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q -rA`
Result: **3512 passed, 8 skipped, 0 failed** (iter-32 baseline: 3503 passed / 8 skipped — net +9;
exit code 0; verified via `-rA` per-test PASSED lines since this pytest install does not print its
usual final summary line, the same iter-32/iter-31 environment quirk). Targeted files also run
individually and green: `test_micro_snapshots.py` (39), `test_vault.py` (95), `test_mcp_server.py`
(69), `test_desk_ui_guards.py` (86), `test_desk_forward_ui_guard.py` +
`test_meta_routes.py` + `test_copy_discipline.py` (57), `test_seed_micro_snapshots_iter33_
disclosure_fixture.py` (3).

Frontend: `npx tsc --noEmit` — clean, zero errors.

Seed script (`apps/backend/scripts/seed_micro_snapshots_iter33_disclosure_fixture.py`), run
standalone against a throwaway root: exit 0, self-check `ok: 1 valid served, 1 stale excluded,
1 withheld excluded`.

`docs/phases/goal-rapid-microscope-iter-33.md`'s `demo_runner.py --mode lint --scripts-dir
runs/goal-session-rapid-microscope/journey-scripts --journeys J-02` (pure JSON/schema validation,
no browser/playwright needed): `J-02 ok`. Playwright is not installed in this backend venv, so
`--mode verify` (the actual browser replay) is left to the downstream browser-qa-agent stage —
see Known Issues.

Frozen-foundation re-checks: `Config().config_fingerprint()` still prints `08e471b10130e1e2`;
`git status --porcelain` shows zero diff under any `referee_*.py` file; `GET /research/pnl/ledger`
unaffected (this iteration touches no PnL/ledger/strategy/profile code at all).

## Pre-handoff verification

- **Service startup works**: `rm -rf apps/frontend/.next` (T-9), then `bash scripts/dev.sh`
  started backend (`:8301`) and frontend (`:3301`) cleanly (`Application startup complete`,
  Next.js `✓ Ready`, `✓ Compiled /desk in 3.2s`, zero compile errors in the dev log). Live checks:
  `GET /health` → 200; `GET /research/desk/micro/snapshots` → 200 with the real store's 18
  snapshots plus `"withheld_excluded":80,"stale_excluded":0` (the 80 reflects the operator's own
  real vault universe registrations across later eras — genuinely unrelated to this iteration);
  `GET /desk` → 200 and its initial HTML already contains `aria-label="Feature Snapshots"` and
  `data-testid="desk-section-expand-featureSnapshots"` (the section mounts correctly). **Per the
  pump's operational note, both processes were left RUNNING (not killed) for the downstream
  browser-QA stage** — this deviates from the agent instructions' normal "kill servers before
  finishing" rule, which the dispatch prompt explicitly overrides for this pipeline run.
- **External integrations**: N/A — this iteration adds no adapter, scraper, or external API call.
- **Native dependency binaries**: N/A — no new dependency added.

## Known Issues

- **Browser evidence (TC-1 real-store capture, TC-2 fixture-scoped valid/stale/withheld capture,
  the `[NEW]`-flagged demo-narrator walkthrough step, and `demo_runner.py --mode verify` for
  J-02's new step 3) is NOT part of this dev pass** — per the standard goal-mode pipeline division
  of labor (the same split iter-32's own handoff used) and because this environment's backend venv
  has no `playwright` package installed (`ModuleNotFoundError: No module named 'playwright'`), so
  the actual browser replay cannot run from this agent. This handoff hands the browser-qa stage
  everything it needs:
  - **TC-1 (real store)**: the persistent `:8301`/`:3301` rig already serves the real 18-snapshot
    inventory plus both disclosure counts (verified live above) — navigate to `/desk`, expand
    "Feature Snapshots", element-capture the section.
  - **TC-2 (fixture-scoped)**: run the seed script against a fresh, never-seeded root, e.g.
    `TAPEOLOGY_DATASET_DIR=apps/backend/.data/qa-fixtures/goal-rapid-microscope-iter33-disclosure/datasets
    apps/backend/.venv/bin/python scripts/seed_micro_snapshots_iter33_disclosure_fixture.py
    apps/backend/.data/qa-fixtures/goal-rapid-microscope-iter33-disclosure` (self-checks and
    prints `ok: 1 valid served, 1 stale excluded, 1 withheld excluded` on success), then restart
    the backend with that SAME `TAPEOLOGY_DATASET_DIR` (the snapshots dir resolves as a sibling of
    it automatically — no separate `TAPEOLOGY_MICRO_SNAPSHOTS_DIR` needed) and browser-verify the
    three states: the valid snapshot (symbol `PGSNAPOK`) renders every identity field; the stale
    meta (symbol `PGSNAPST`) appears nowhere as a row; the withheld member (symbol `PGSNAPWH`)
    appears nowhere by id/symbol/session-date/checksum/row-count/bytes — both counts read `1`.
  - `demo_runner.py --mode verify` for J-02's new step 3, and the `[NEW]`-flagged demo-narrator
    walkthrough step, are likewise this later stage's responsibility.
- **J-03's owed element close-up and J-05's golden wording fix stay owed** — explicitly out of
  scope this iteration (spec's own OUT OF SCOPE list); not touched.
- **`withheld_excluded: 80` on the real persistent rig** is a genuinely large, real number
  reflecting the operator's actual accumulated vault-universe registrations from prior real-data
  eras (tradable_wall / fast_wall / etc.) — not a bug and not something this iteration's tests
  hardcode against (`test_tc12_real_corpus_listed_via_the_route` only asserts presence/
  non-negativity of the real-store counts for exactly this reason; the pool-derived-vs-file-derived
  proof lives on hermetic throwaway stores in `test_vault.py`/`test_micro_snapshots.py`).
