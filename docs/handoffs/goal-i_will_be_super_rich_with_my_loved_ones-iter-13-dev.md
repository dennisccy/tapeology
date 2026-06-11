# goal-i_will_be_super_rich_with_my_loved_ones-iter-13 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-13
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

J-54 (machine-derived execution checks computed once at resolution) + J-55 (the `/journal/[id]`
review-detail page), the lean pair the iter-12 evaluator mandated. Strictly additive — research
stays observer-only; no engine/classifier/provider/chart change; `verdict_events` write semantics
untouched (still append-only, no update/delete added).

### Backend
- **Single-owner execution-checks function** — new module `apps/backend/app/research/execution_checks.py`.
  `compute_execution_checks(thesis, *, actions, timeline, config)` is a PURE function computing the
  four named checks from the persisted action marks + the append-only verdict timeline + frozen
  thesis fields ONLY:
  - `entered_before_confirmation` — entry's logical_ts precedes the first published `confirming`
    event (or no `confirming` was ever published while entry-marked → failed);
  - `chased_entry` — entry price beyond the recorded `rule_first_true_price` × (1 ± `chase_return_threshold`),
    direction-aware. **Anchored at the recorded `rule_first_true` price, never the post-dwell
    publish** (per Constraints); reuses the existing `chase_return_threshold` config seam — no new
    magic number. No anchor recorded ⇒ `not_applicable` (never a fabricated pass/fail);
  - `exited_beyond_invalidation` — exit recorded at/beyond the declared invalidation in the adverse
    direction (held through the stop);
  - `cut_confirming_early` — exit recorded while the latest published verdict at the exit instant was
    `confirming`.
  Each check yields an **enum status** (`failed | passed | not_applicable` — labels, never numeric
  scores) + plain-language evidence quoting the measured values. No marks ⇒ the mark-dependent checks
  read `not_applicable`. `compute_and_persist_execution_checks(store, thesis_id, config)` is the one
  entry point every terminal-resolution path calls (idempotent: never recomputes if already set).
- **Suggested mistake tags** — derived once with the checks from the backend-owned
  `taxonomy.CHECK_SUGGESTED_TAG` mapping (`entered_before_confirmation` → `entered_before_confirmation`,
  `chased_entry` → `chased`, `exited_beyond_invalidation` → `ignored_rejection`). The system SUGGESTS
  only; it never records a confirmed tag. `cut_confirming_early` has no clean catalog tag, so it maps
  to nothing (the user adds `other` + a note in the J-57 flow).
- **Computed once at every terminal-resolution path, persisted (schema v5):**
  - user `POST /research/thesis/{id}/resolve` (routes.py);
  - system invalidation auto-resolve (`monitor._evaluate_verdict`);
  - stream-end / stop expiry (`monitor._expire_active`);
  - restart-expiry sweep (`ResearchRegistry.startup_sweep`).
  Each calls the SAME single function once, right after the status flip, and persists the result on
  the thesis row via the new `store.set_execution_checks`.
- **Schema v5 versioned migration** — `journal_schema_version` bumped 4 → 5; `theses` gains an
  `execution_checks TEXT` column added by an in-place `ALTER TABLE` inside one `BEGIN IMMEDIATE`
  writer transaction, idempotent (`PRAGMA table_info` guard), **never backfilled**. Pre-v5 resolved
  theses keep the key **ABSENT** (NULL → `None` → the journal detail OMITS the key — the established
  honest-omission pattern, like pre-v4 `risk_flags`). Proven against the new committed v4 fixture.
- **Mistake-tag catalog in the taxonomy** — `taxonomy.MISTAKE_TAGS` (the full goal.md capability-29
  catalog: `chased`, `entered_before_confirmation`, `ignored_rejection`, `ignored_risk_flags`,
  `moved_invalidation` *(self-assessed)*, `no_clear_setup`, `wrong_setup_type`, `overstayed`,
  `other`) with display copy + a `requires_note` flag (`other` → true), served additively by
  `GET /research/taxonomy`. The review SAVE flow (`POST …/review`) is NOT built (J-57, iter-14).
- **`GET /research/journal/{id}` gains additive keys** — `execution_checks` (the four-check list)
  and `suggested_mistake_tags`, served VERBATIM from the persisted record via the new
  `build_journal_detail` helper. Present only post-resolution; absent pre-resolution / pre-migration.
  Nothing recomputed at read; the existing timeline-row shape is unchanged (additive-only).

### Frontend
See the companion frontend handoff for detail; in brief: the new `/journal/[id]` route + the
`JournalDetailView` component render the single `GET /research/journal/{id}` response + taxonomy
labels verbatim; `/journal` rows became links; the JournalTable empty-state `▤` glyph was replaced
with class-based styling.

## Files Changed
- `apps/backend/app/config.py` -- `journal_schema_version` 4 → 5 + the v4→v5 migration doc.
- `apps/backend/app/research/store.py` -- v5 schema column, `ThesisRecord.execution_checks`, v4→v5 migration step, `set_execution_checks`, encode/decode preserving ABSENT-vs-computed.
- `apps/backend/app/research/execution_checks.py` -- NEW: the single-owner pure function + the compute-and-persist helper.
- `apps/backend/app/research/monitor.py` -- compute+persist checks on the invalidation and expiry resolution paths.
- `apps/backend/app/research/routes.py` -- compute+persist on user resolve + the startup sweep; `build_journal_detail` helper serving the additive keys verbatim.
- `apps/backend/app/research/taxonomy.py` -- mistake-tag catalog + check→tag mapping + payload exposure.
- `apps/backend/tests/fixtures/journal_v4_schema.sql` -- NEW: committed v4 fixture (resolved thesis, no execution_checks column) for the migration regression test.
- `apps/backend/tests/test_execution_checks.py` -- NEW: 16 pure unit tests over the four checks (failed/passed/not_applicable + evidence + chase anchored at rule_first_true + suggested-tag mapping + determinism).
- `apps/backend/tests/test_research_execution_checks_api.py` -- NEW: end-to-end resolution-path + serving tests (compute-once / byte-identical re-read / absent pre-resolution / not_applicable without marks / 404 / additive-only timeline).
- `apps/backend/tests/test_journal_migration.py` -- v4→v5 migration tests + v4 fixture loader; updated the chained-migration assertions (v3 fixture now chains to current).
- `apps/backend/tests/test_research_api.py` -- mistake-tag catalog taxonomy tests + check→tag-targets-exist test.
- `apps/backend/tests/test_research_store.py` -- de-pinned one stale `== 4` schema assertion to `== CONFIG.journal_schema_version`.
- `apps/frontend/app/journal/[id]/page.tsx` -- NEW: the review-detail route (loading / error / not-found / detail states).
- `apps/frontend/components/JournalDetailView.tsx` -- NEW: renders statements, timeline (true clock time), risk flags, marks, execution checks + the suggested-tag picker (disabled Save).
- `apps/frontend/components/JournalTable.tsx` -- rows became links to `/journal/[id]`; `▤` empty-state glyph replaced with class-based rules.
- `apps/frontend/lib/types.ts` -- `JournalDetail`/`JournalTimelineRow`/`ExecutionCheck`/`MistakeTag` types + `mistake_tags` on `ResearchTaxonomy`.
- `apps/frontend/lib/api.ts` -- `fetchJournalDetail` (200 / 404-notFound / error).

## Tests Run
Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **525 passed, 1 skipped, 0 failed** (full suite; includes the new execution-checks unit +
API tests and the v4→v5 migration tests).

Frontend: `cd apps/frontend && NEXT_DIST_DIR=.next-devbuild npx next build` → compiled + type-checked
clean; `/`, `/journal`, and the new dynamic `/journal/[id]` route all emitted. (Built into a throwaway
dist dir so the QA harness's shared `.next` was never clobbered; the transient dir + the auto-edited
`next-env.d.ts`/`tsconfig.json` were reverted to keep the diff clean.)

## Known Issues
- **Live REST content canary (passed):** a real uvicorn backend (separate temp journal DB) ran the
  full flow — watch SIM-BUYER → declare trend_continuation/long → mark entry while PENDING → let it
  confirm → mark exit → resolve `played_out` → `GET /research/journal/{id}` returned `status:
  played_out` with `execution_checks` present: `entered_before_confirmation` **failed** (entry 21.5s
  < first confirming publish 25.0s) with `suggested_mistake_tags: ["entered_before_confirmation"]`,
  `chased_entry` passed (anchored at the recorded `rule_first_true` 100.20, NOT the publish last),
  `exited_beyond_invalidation` passed, `cut_confirming_early` failed; a second GET returned
  byte-identical `execution_checks`; `GET /research/taxonomy` served the full `mistake_tags` catalog
  (`other.requires_note: true`); an unknown id returned 404; no numeric score anywhere. The backend
  was stopped and all temp files removed; no stray uvicorn/next-dev processes remain.
- **Browser QA deferred to the qa step.** `/journal/[id]` is a new below-the-fold surface — the qa
  agent must capture it with scroll-into-view / full-page captures and open the PNGs; reuse of prior
  risk-flag/verdict frames is only valid for re-rendered frozen data, never for the NEW detail
  surface.
- **Schema change ⇒ DB migration.** Any existing journal DB on disk migrates v→5 automatically on
  first open (idempotent, never backfilled). The committed v4 fixture proves the v4→v5 step; the
  chained v1/v2/v3 fixtures prove the path migrates all the way to v5.
- **Out of scope this iteration (honestly absent):** J-56 grades (grade keys absent from rows +
  detail), J-57 review SAVE flow (the detail's Save button is present but DISABLED with honest copy —
  the no-dead-control pattern), excursions (J-58), analytics (J-59), studies (J-60–62), all cues, and
  the "re-watch this window" affordance.
- **Blueprint conformance:** the iter-13 additive notes already present in
  `runs/.../state/blueprint.md` rows 19 (execution-checks half + schema v5) and 24 (mistake-tag
  catalog) match what shipped exactly; `/journal/[id]` lives at its already-approved home under the
  Journal nav (no skeleton change, no reapproval).
