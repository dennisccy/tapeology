# goal-i_will_be_super_rich_with_my_loved_ones-iter-5 Execution Plan

Consolidation/fix iteration (evaluator-mandated, depth full, NO new feature scope). The
iter-4 verdict engine (J-40–J-46) is built and unit-proven (353 passed / 1 skipped) but
every browser journey is blocked by one persistence defect: `verdict_events` gained
`rule_first_true_ts`/`rule_first_true_price` only in the `CREATE TABLE IF NOT EXISTS` DDL
with no versioned migration, so `_create_schema` no-ops on the persistent dev DB
(`apps/backend/tapeology_journal.db`) and every `POST /research/thesis` 503s. A secondary
defect (thesis insert + initial verdict event as two transactions) left orphaned active
thesis `4beae280…` that 409-blocks SIM-BUYER. This iteration fixes persistence, proves it
against the REAL dev DB, and re-runs the full 12-test browser matrix.

## What to Build

- **Versioned SQLite migration v1→v2 (the blocker).** Bump `journal_schema_version` to `2`
  in `apps/backend/app/config.py:362` and fix its stale "migration is out of scope" comment.
  In `store.py`, on open: read the stored `schema_version`; if < 2, run the two
  `ALTER TABLE verdict_events ADD COLUMN rule_first_true_{ts,price} REAL` statements and
  update the version row — ALL inside one `BEGIN IMMEDIATE` writer transaction. A
  `PRAGMA table_info` guard is acceptable belt-and-braces (columns already present + stale
  version row must not crash). NEVER backfill `rule_first_true_*` on pre-existing rows
  (append-only timeline — old events keep `NULL`). `journal_schema_version` stays excluded
  from `config_fingerprint` (config.py:437) — the migration must not change the fingerprint.
- **Atomic declaration.** `insert_thesis` + the initial `pending` verdict event execute in
  ONE writer transaction; any failure rolls back both. A thesis row without its initial
  event can no longer exist.
- **Orphan cleanup via the startup sweep.** Verify the existing sweep (`store.py:342`,
  `routes.py:86 startup_sweep`) resolves zero-event active thesis `4beae280…` to `expired`
  on backend start; extend it only if the zero-event case is not handled. Do NOT delete the
  row (no survivorship pruning). After the sweep, SIM-BUYER must accept a new declaration.
- **Old-schema regression test.** Commit a small v1-schema journal DB fixture under
  `apps/backend/tests/fixtures/` (research records ONLY — explicitly allowed by the
  persistence anti-goal; no tape data). Test copies it to a temp path, opens the store,
  asserts migration to v2 (columns present, version row = 2, old rows intact with `NULL`
  rule_first_true) and declares a thesis end-to-end. Also: idempotent open on an
  already-v2 DB; stale-version-row-with-columns-present does not crash.
- **Atomicity regression test.** Fault-inject a failure on the initial verdict-event
  insert; assert NO thesis row persists and the API surfaces the error honestly.
- **Minor:** fix the store.py docstring note flagged by the iter-4 reviewer.
- **Frontend (one line):** add `data-testid="thesis-strip"` to the ThesisStrip root
  element. No other frontend change.
- **Blueprint note (additive):** one sentence in the session blueprint's Persistence
  paragraph — versioned migrations proven against a committed old-schema fixture. No new
  surfaces, owners, endpoints, or computations; no reapproval needed.
- **Dev-handoff proof against the REAL dev DB:** `POST /research/thesis` returns 200
  against `apps/backend/tapeology_journal.db` migrated in place — not a temp DB.

## Agents Required

- developer: yes -- all backend work (migration, atomic declaration, sweep verification,
  v1 fixture + migration/atomicity/idempotency tests, docstring fix, blueprint persistence
  note) plus the single-attribute frontend change and the dev handoff with real-dev-DB proof.
- backend-data: yes (the iteration IS the persistence fix)
- frontend-ux: yes (minimal — one `data-testid` attribute on ThesisStrip; no visual change)

## Frontend Present
yes

(Yes despite the tiny code delta: the iter-4 verdict UI becomes browser-provable for the
first time, and the spec mandates the full 12-test browser matrix against the persistent
dev stack.)

## Files to Create/Modify

- `apps/backend/app/config.py` -- `journal_schema_version: 1 → 2`; update the stale
  "migration is out of scope" comment; keep the fingerprint exclusion untouched.
- `apps/backend/app/research/store.py` -- versioned on-open migration (one `BEGIN
  IMMEDIATE`); atomic `insert_thesis` + initial verdict event; sweep extension ONLY if the
  zero-event active case is unhandled; reviewer-flagged docstring fix.
- `apps/backend/app/research/routes.py` -- only if the startup sweep needs the zero-event
  extension wired; otherwise untouched.
- `apps/backend/tests/fixtures/<v1-journal>.db` -- NEW committed iter-2-schema fixture
  (research records only).
- `apps/backend/tests/test_research_store.py` (or a new `test_journal_migration.py`) --
  migration-from-fixture, idempotent v2 open, stale-version-row guard, atomic-rollback,
  zero-event-orphan sweep tests.
- `apps/frontend/components/ThesisStrip.tsx` -- add `data-testid="thesis-strip"` to root.
- `runs/goal-session-i_will_be_super_rich_with_my_loved_ones/state/blueprint.md` -- one
  additive sentence in the Persistence paragraph.
- `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-5-dev.md` -- dev handoff
  incl. the 200-declare-against-the-real-dev-DB evidence and the orphan-sweep result.

## UI Evolution

- New user-facing capability: declaring a thesis now WORKS on the real, persistent
  installation — the declare flow returns the active thesis instead of a 503, and the
  verdict engine's live judgements (pending → confirming / weakening / rejecting /
  invalidated, each with evidence) become visible in the browser for the first time.
- New information displayed: none new — the iter-4 verdict chip, evidence line, statement
  statuses, and terminal invalidated treatment finally render against real persisted data.
- New user actions: none new — the existing declare form simply stops failing.
- UI surface changes: none beyond the `data-testid` attribute.
- Navigation changes: none. All target journeys live at their registered blueprint home —
  the `/` thesis strip (Cockpit). Top bar untouched.

## Visual Requirements

- Component patterns: existing hand-built ThesisStrip only — no new components.
- Layout: unchanged — strip between chart and panel grid on the one-screen cockpit.
- Key visual effects: existing verdict semantics (confirming emerald, weakening amber,
  rejecting/invalidated rose with terminal treatment, pending slate); mono numerics.
- States to handle: already built in iter-4 — idle declare affordance (J-68), active thesis
  with live verdict + evidence, inline 422 error visible in pixels (J-39), terminal
  invalidated treatment (J-44). This iteration only makes them reachable.

## Key Test Scenarios

- `POST /research/thesis` returns 200 against the PERSISTENT dev DB (migrated in place to
  v2) — proven in the dev handoff with the actual dev DB, not a temp DB.
- Orphan `4beae280…` resolved to `expired` by the startup sweep (row retained); a fresh
  SIM-BUYER declaration succeeds (no 409).
- Migration-from-committed-v1-fixture test passes: columns added, version row = 2, old rows
  intact with `NULL` rule_first_true, declare succeeds end-to-end; idempotent v2 reopen;
  stale version row + present columns does not crash.
- Atomicity: forced failure on the initial event insert leaves NO thesis row and surfaces
  an explicit API error.
- Full backend suite green (≥353 passed, incl. observer equivalence), zero regressions.
- Browser QA, full 12-test matrix on the persistent dev stack: J-38 (declare on SIM-BIDABS;
  REST `…/thesis/active` == WS `thesis` verbatim, no reload), J-39 (404/422×3/409 matrix
  with the inline 422 IN PIXELS), J-40 (SIM-REVERSAL pending-through-absorption →
  confirming on the flip, `rule_first_true` + published on the timeline), J-41 (rejecting,
  thesis stays active), J-42 (confirming after dwell, no flapping), J-43 (confirming →
  weakening, both on the timeline, never silent pending), J-44 (dwell-exempt invalidated +
  auto-resolve + terminal treatment + offending print), J-45 (level_break latch), J-46
  (failed_move_fade confirms DURING absorption), J-68 (idle strip locatable via
  `data-testid="thesis-strip"`; capture must match narrative).
- Binding evidence rule (violated four iterations running): EVERY browser capture has the
  asserted element in pixels via scroll-into-view or full-page screenshot; the closure
  auditor opens the PNGs — mis-framed/un-opened PNGs are CLOSURE-FAIL material.
- QA preconditions: verify the dev backend + frontend under test first; never
  `npm run build` against the live dev server's shared `.next` (use `NEXT_DIST_DIR=.next-qa`);
  recount pass/fail from result tables, not prose.
- Required-still-passing: J-01–J-09, J-17, J-19, J-21, J-24 remain green.

## Scope Guards (reviewer should reject drift)

- NO new feature scope (evaluator mandate): no chart thesis geometry (J-48), no entry risk
  flags (J-49), no resolve controls (J-50), no `/journal` page, no action marks, no
  analytics/studies/cues. No engine/classifier/feature/provider changes. No verdict-rule
  changes. No ORM — stdlib `sqlite3` only. No backfill of `rule_first_true_*`.

## Assumptions (documented, not asked)

- Migrating `apps/backend/tapeology_journal.db` in place during dev verification is
  intended — the in-place migration of the persistent dev DB IS the deliverable.
- The v1 fixture is small and handcrafted/generated from the iter-2 DDL (theses +
  verdict_events rows sufficient to prove non-backfill), committed as binary or built by a
  test helper from committed SQL — developer's choice, fixture committed either way.
- The startup sweep likely already covers zero-event active theses via the generic
  "active → expired" sweep; the developer verifies before extending (verify-first, per spec).
