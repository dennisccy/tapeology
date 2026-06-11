# goal-i_will_be_super_rich_with_my_loved_ones-iter-14 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-14
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

The review pillar (goal.md pillar 4) is now fully usable: declare → judge → resolve → **review**
closes the loop. Three gaps from iter-13 are closed, all riding the same proven
terminal-resolution / persist-once seam plus one new review endpoint.

### Backend

- **Per-statement FINAL statuses (J-55).** New `compute_final_statement_statuses` (pure) +
  `compute_and_persist_final_statuses` (persist-once) in `monitor.py`. At every terminal resolution
  (the same four call sites as execution checks) each frozen statement's final status is persisted
  ONCE on an additive `theses.statement_final_statuses` JSON column — the frozen `statements` JSON is
  NEVER mutated. Live-monitored paths (user resolve while watched, system invalidation, stream-end
  expiry) record the at-terminal-moment evaluation from the SAME `_evaluate_statement` the live
  projection uses (one owner — no second rule). The restart-expiry sweep has no live context, so it
  records the explicit honest `not_evaluated` enum (added to `STATEMENT_STATUSES`). Pre-v6 resolved
  theses carry the key ABSENT (the detail then renders statements without a badge). Served verbatim
  only by `GET /research/journal/{id}`.
- **Outcome × process grades (J-56).** New `app/research/grades.py` — the SINGLE owner. Outcome
  (`thesis_held | thesis_failed | no_read`) is 1:1 from the resolution via the config-owned
  `process_outcome_grade_map`. Process (`clean | flagged | violated`) is a config-owned rule over the
  named, evidence-backed checks (frozen entry risk flags + persisted execution checks): a FAILED
  execution check violates; else a fired risk flag flags; else clean. **Being invalidated is never by
  itself a process failure** (an invalidated, no-flag, clean-checks thesis grades `clean`). Both axes
  are ENUM labels with plain-language `process_evidence` naming which checks/flags drove the grade —
  NEVER a numeric score. Computed ONCE at the same terminal-resolution seam, AFTER the execution
  checks persist (the process rule weighs them), and persisted to an additive `theses.grades` JSON
  column. Served verbatim by `GET /research/journal/{id}` and as an additive `grades` key on
  `GET /research/journal` rows. Grade display copy is owned by the taxonomy (`outcome_grades` /
  `process_grades`); the frontend hardcodes none.
- **Review save flow (J-57).** New `POST /research/thesis/{id}/review` with body
  `{mistake_tags, note?}`: validation matrix — 404 unknown id; 422 unknown tag; 422 `other` without a
  (non-blank) note; 409 unless resolved; 409 if already reviewed (conservative immutability default,
  see below). On success persists the confirmed tags + note verbatim and flips `reviewed=1` via
  `store.save_review`. The append-only `verdict_events` write surface is UNTOUCHED. The saved review +
  `reviewed` status are served by `GET /research/journal/{id}`; `reviewed` is a pre-registered
  additive key on `GET /research/journal` rows (ALWAYS present as a boolean fact — `False` until
  saved — never absent).
- **Schema v5 → v6 versioned migration (ONE bump)** covering all five additive columns
  (`statement_final_statuses`, `grades`, `review_tags`, `review_note`, `reviewed`): in-place `ALTER`
  in one `BEGIN IMMEDIATE` writer transaction, idempotent `PRAGMA table_info` guards, never
  backfilled. `reviewed` is added with `DEFAULT 0` (the honest "no review exists" fact, NOT a
  backfilled computed value). Proven against a committed `tests/fixtures/journal_v5_schema.sql` plus
  the persistent-DB + fresh-DB-at-current-version checks.

### Frontend

- `/journal/[id]`: each frozen statement now renders its persisted FINAL status badge
  (met/violated/not met/not evaluated), verbatim from `statement_final_statuses` — the iter-13 "see
  timeline" deferral note is removed; pre-v6 rows render an honest "final statuses not recorded" note.
- `/journal/[id]`: new **outcome × process quadrant** block (`How it graded`) — two enum chips
  (labels from the taxonomy) + the `process_evidence` line naming the checks that drove the process
  grade. Pre-v6 rows show an honest "not graded" note.
- `/journal/[id]`: the **Save review** flow is live (the iter-13 disabled placeholder is removed).
  Tags seed from the suggestions and stay toggleable; suggested tags are visibly marked (`·sug`) and
  distinct from the user-confirmed set; selecting `other` reveals a required note with inline
  validation; Save calls the new endpoint; on success the page re-reads the detail and renders the
  saved tags + note + a `Reviewed` chip (an already-reviewed thesis shows the saved selection
  read-only).
- `/journal` list: additive **Grade** (outcome + process chips) and **Reviewed** columns; pre-grade /
  unreviewed rows show an honest em dash.

## Files Changed

- `apps/backend/app/config.py` -- bump `journal_schema_version` 5→6 (+ migration doc); add the
  config-owned grade rule (`process_outcome_grade_map`, `process_violated_min_failed_checks`,
  `process_flagged_min_risk_flags`).
- `apps/backend/app/research/store.py` -- v6 schema columns + ThesisRecord fields + v5→v6 migration
  step + `set_grades` / `set_statement_final_statuses` / `save_review` setters + row decode.
- `apps/backend/app/research/grades.py` -- NEW: the single-owner outcome × process grade functions.
- `apps/backend/app/research/monitor.py` -- final-statuses compute/persist helpers; wire grades +
  final statuses into the invalidation and expiry terminal paths.
- `apps/backend/app/research/routes.py` -- wire grades + final statuses into the user-resolve path and
  the startup sweep; new `POST /research/thesis/{id}/review` endpoint; serve final statuses / grades /
  review (+ always-present `reviewed`) on the journal detail.
- `apps/backend/app/research/journal_rows.py` -- additive `grades` (post-resolution) + always-present
  `reviewed` row keys.
- `apps/backend/app/research/taxonomy.py` -- `OUTCOME_GRADES` / `PROCESS_GRADES` enums + display copy;
  `not_evaluated` added to `STATEMENT_STATUSES`; both grade catalogs in the taxonomy payload.
- `apps/backend/tests/fixtures/journal_v5_schema.sql` -- NEW committed v5 fixture for the migration.
- `apps/backend/tests/test_grades.py` -- NEW: grade-computation unit matrix.
- `apps/backend/tests/test_research_review.py` -- NEW: review endpoint matrix + grades + final
  statuses end-to-end, both J-56 quadrants.
- `apps/backend/tests/test_journal_migration.py` -- v5→v6 migration tests + updated chained-version
  assertions.
- `apps/backend/tests/test_journal_list.py` -- updated row contract (grades omitted pre-resolution;
  `reviewed` always present).
- `apps/frontend/lib/types.ts` -- `ThesisGrades`, `StatementFinalStatus`, `SavedReview`; extend
  `JournalRow` / `JournalDetail` / `JournalDetailThesis` / `ResearchTaxonomy`.
- `apps/frontend/lib/api.ts` -- `saveReview()`.
- `apps/frontend/components/JournalDetailView.tsx` -- final-status badges, the grades quadrant, the
  live Save flow.
- `apps/frontend/components/JournalTable.tsx` -- Grade + Reviewed columns.
- `apps/frontend/app/journal/[id]/page.tsx` -- pass `onSaved={load}` so a save re-reads the detail.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **554 passed, 1 skipped** (the 1 skip is a pre-existing credential-gated live test).

Command: `cd apps/frontend && NEXT_DIST_DIR=.next-qa npm run build`
Result: **PASS** — compiles + type-checks clean; `/`, `/journal`, and `/journal/[id]` all emitted.
(Used `NEXT_DIST_DIR=.next-qa` per the spec — never the live dev server's `.next`.)

## Known Issues

- **Browser QA is deferred to the qa step** (as designed). Dev verified J-55/J-56/J-57 end-to-end via
  unit/integration tests + a live backend startup canary (uvicorn `/health` ok; taxonomy serves
  `outcome_grades`/`process_grades`; a fresh journal DB migrates to schema 6). The J-56 SIM-SHIFT
  clean-process leg depends on the chop dip printing at 100.00 below an invalidation placed at 100.05
  (between the chop center and the warmed late-control last); the test asserts the flag-free
  precondition and the invalidation actually firing, so it is self-validating.
- **409-on-already-reviewed is a conservative default** chosen because goal.md is silent on
  re-review. It keeps review records immutable in the spirit of journal integrity (a re-review would
  need its own honest, tested path and must never touch the append-only timeline). The frontend
  renders an already-reviewed thesis's tags read-only rather than offering a second Save.
- **No engine/classifier/provider/chart change** (J-68 sentinel): all work is observer-side /
  research-store-side. The observer-equivalence test stays green (engine outputs byte-identical).
- The two new config grade-rule values DO enter `config_fingerprint` (they affect a persisted grade) —
  intentional, so grades are never silently pooled across different grade rules.
