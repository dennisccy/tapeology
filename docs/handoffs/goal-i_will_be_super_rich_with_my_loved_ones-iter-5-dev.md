# goal-i_will_be_super_rich_with_my_loved_ones-iter-5 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-5
**Date:** 2026-06-10
**Agent:** developer
**Status:** complete

## What Was Built

This is the evaluator-mandated consolidation/fix iteration — NO new feature scope. The iter-4
verdict engine (J-40–J-46) was already built and unit-proven, but every browser journey was blocked
by one persistence defect. This iteration fixes persistence and proves it against the REAL dev DB.

- **Versioned SQLite migration v1 → v2 (the blocker).** `journal_schema_version` bumped `1 → 2`.
  On store open, `JournalStore._migrate()` reads the stored `schema_version` and, when it is older
  than 2, runs `ALTER TABLE verdict_events ADD COLUMN rule_first_true_ts REAL` and
  `... rule_first_true_price REAL`, then `UPDATE schema_version SET version = 2` — all inside ONE
  `BEGIN IMMEDIATE` writer transaction. A `PRAGMA table_info` guard makes each ALTER idempotent (a
  DB that already has the columns but a stale version row just bumps the version, never crashes).
  The migration NEVER backfills `rule_first_true_*` on pre-existing rows — old verdict events keep
  `NULL` (the timeline is append-only). `journal_schema_version` stays excluded from
  `config_fingerprint`, so a migration does not change the fingerprint.
- **Atomic declaration.** New `JournalStore.insert_thesis_with_event(thesis, event)` inserts the
  thesis row AND the initial `pending` verdict event in ONE writer transaction. The declare route
  now calls this single method instead of two separate `insert_thesis` + `append_verdict_event`
  calls. Any failure rolls back BOTH — a thesis row without its initial event can no longer exist
  (the iter-4 orphan defect).
- **Orphan cleanup verified (no code change needed).** The existing startup sweep
  (`store.expire_stale_actives` → `routes.ResearchRegistry.startup_sweep` → `main.lifespan`) selects
  `WHERE status = 'active'` regardless of verdict-event count, so it already resolves zero-event
  active orphans to `expired` and appends a final `expired` timeline row. Verified against an exact
  replica of the defective dev DB (both orphans `4beae280…` SIM-BUYER and `c4e37534…` SIM-SELLER
  swept; rows retained, never deleted). No sweep extension and no routes.py change were required.
- **Old-schema regression test.** New `apps/backend/tests/test_journal_migration.py` builds a temp
  DB from the committed v1-schema fixture (`tests/fixtures/journal_v1_schema.sql` — research records
  ONLY, no tape data) and asserts: migration to v2 (columns added, version row = 2), pre-existing
  rows intact with `NULL` rule_first_true (no backfill), declare succeeds end-to-end, idempotent v2
  reopen, stale-version-row-with-columns-present does not crash, fresh temp DB created at v2
  directly, atomic-rollback on forced event-insert failure, and the zero-event-orphan sweep.
- **Atomicity regression test (store + API).** Fault-injects a failure on the initial
  verdict-event INSERT via a connection proxy (`sqlite3.Connection` is an immutable C type that
  cannot be monkeypatched). Asserts NO thesis row persists at the store level, and that the API
  surfaces a 503 with nothing partially saved (a clean re-declare then returns 200 — no orphan 409).
- **Docstring fix (iter-4 review NOTE).** Corrected the `store.py` module docstring: writes are
  enqueued onto and executed by the dedicated writer worker; the enqueuing caller is
  synchronous-but-fast (it waits only for the worker's result handoff, not for reader/WS
  contention), and a write failure is raised so the monitor flips `monitor_status: failed`.
- **Frontend (one line).** Added `data-testid="thesis-strip"` to the shared `StripShell`
  `<section>` in `ThesisStrip.tsx` — covers every state (idle declare affordance, loading, error,
  active thesis) since all branches render through `StripShell`. No visual change.
- **Blueprint note (additive).** One sentence in the session blueprint's Persistence paragraph:
  schema evolution ships a versioned migration proven against a committed old-schema fixture. No
  new surfaces, owners, endpoints, or computations.

## Files Changed

- `apps/backend/app/config.py` -- `journal_schema_version: 1 → 2`; replaced the stale
  "migration is out of scope" comment with the migration contract; fingerprint exclusion untouched.
- `apps/backend/app/research/store.py` -- added `_migrate()` (v1→v2 in one `BEGIN IMMEDIATE`,
  idempotent via `_column_exists`), `insert_thesis_with_event()` (atomic declare), `_create_schema`
  now calls `_migrate`; corrected the module docstring.
- `apps/backend/app/research/routes.py` -- `declare_thesis` now persists via the single atomic
  `insert_thesis_with_event` call (was two transactions). No other change.
- `apps/backend/tests/fixtures/journal_v1_schema.sql` -- NEW committed v1-schema fixture (research
  records only; deliberately lacks the v2 columns).
- `apps/backend/tests/test_journal_migration.py` -- NEW: migration, idempotency, stale-version-row,
  atomic-rollback, and zero-event-orphan-sweep tests.
- `apps/backend/tests/test_research_api.py` -- NEW route-level atomicity test (503 + nothing saved).
- `apps/frontend/components/ThesisStrip.tsx` -- added `data-testid="thesis-strip"` to `StripShell`.
- `runs/goal-session-i_will_be_super_rich_with_my_loved_ones/state/blueprint.md` -- one additive
  persistence-discipline sentence.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **364 passed, 1 skipped** (the skip is the credentialed live-integration test that needs
Alpaca keys — unchanged from prior iterations). Up from the iter-4 baseline of 353 passed; the +11
are the 10 new migration tests + 1 new route-level atomicity test. Zero regressions, observer
equivalence still green.

Frontend build: `cd apps/frontend && NEXT_DIST_DIR=.next-iter5-verify npm run build` — succeeded
(type-check + compile clean). The temp dist dir was removed and the build-touched `tsconfig.json` /
`next-env.d.ts` reverted to their committed state so nothing leaks into the diff and the live QA
frontend's shared `.next-qa` is untouched.

## Real-Dev-DB Proof (the deliverable)

The defining requirement — `POST /research/thesis` returns **200** against the **persistent** dev DB
migrated in place — is proven two ways:

1. **In-place v1 → v2 migration + orphan sweep**, against an exact reconstruction of the original
   defective dev DB (schema v1, missing the two columns, carrying the two zero-event active orphans
   `4beae280…` / `c4e37534…`). Opening a real `JournalStore` against it migrated it to v2 in place
   (columns added, version row = 2); the real `startup_sweep` resolved both orphans to `expired`
   (rows retained, final `expired` timeline event appended); a fresh SIM-BUYER declaration then
   succeeded (no 409).

2. **Live HTTP 200** against the actual persistent dev DB (`apps/backend/tapeology_journal.db`).
   Started the real uvicorn backend (port 8777, default `TAPEOLOGY_JOURNAL_DB`), watched
   SIM-BIDABS to `bid_absorption`, and `POST /research/thesis`
   (`absorption_reversal`/`long`, invalidation 99.0) returned **HTTP 200** with the full active-thesis
   projection (verdict `pending`, evidence-backed statements, `monitor_status: ok`,
   `bound_source: bid_absorption`, `data_feed: sim`). `GET /research/thesis/active` matched the
   declared thesis, and `GET /research/journal/{id}` showed the persisted timeline beginning with
   the initial `pending` event (`rule_first_true_ts: null`, correctly not backfilled). `DELETE
   /watch/SIM-BIDABS` then expired the thesis on teardown — the persistent DB ended at schema v2
   with zero lingering active theses. The backend process was killed after the proof.

The persistent dev DB is now at schema v2 with all prior orphans swept — the in-place migration of
the dev DB IS the deliverable, and it is done.

## Known Issues

- None functionally. The persistent dev DB (`apps/backend/tapeology_journal.db`) is gitignored
  (`*.db`) and is NOT committed — only the human-readable `journal_v1_schema.sql` fixture is
  committed (the project's `*.db` rule would otherwise block a binary fixture; SQL keeps it
  inspectable and reproducible). The migration test materializes the binary v1 DB from that SQL at
  test time.
- The live-integration test remains skipped without Alpaca credentials (pre-existing; out of scope).
- Browser QA (the full 12-test matrix on the persistent dev stack) is the next pipeline step — the
  backend + frontend changes that unblock it are complete and verified above; the verdict UI now
  renders against real persisted data for the first time.
