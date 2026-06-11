# goal-i_will_be_super_rich_with_my_loved_ones-iter-14 Frontend Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-14
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

The `/journal/[id]` review-detail page becomes the fully usable review surface, and the `/journal`
list gains grade + reviewed columns. Every value is read VERBATIM from the single
`GET /research/journal/{id}` response (or the list rows + taxonomy labels) — the frontend recomputes
NOTHING. No new routes, no nav change.

### `/journal/[id]` (JournalDetailView)

- **Per-statement FINAL status badges (J-55).** Each frozen statement now renders its persisted final
  status as a colored chip — Met (emerald), Violated (rose), Not met / Not evaluated (slate) — read
  verbatim from `statement_final_statuses` (positionally keyed to `thesis.statements`). The iter-13
  "the final status is read from the timeline" deferral note is REMOVED. A pre-v6 resolution (key
  absent) renders the statements without badges plus an honest "final statuses were not recorded"
  line. `data-testid="detail-statement-final-status"` + `data-status` for QA.
- **Outcome × process quadrant (J-56).** A new `How it graded` section
  (`data-testid="detail-grades"`) shows two enum chips — Outcome (`data-testid="grade-outcome"`) and
  Process (`data-testid="grade-process"`) — with labels from the taxonomy (`outcome_grades` /
  `process_grades`) and the `process_evidence` line (`data-testid="grade-process-evidence"`) naming
  the checks/flags that drove the process grade. No numeric score anywhere. Pre-v6 rows show an
  honest "not graded" note. Colors: held/clean emerald, flagged amber, failed/violated rose,
  no_read slate.
- **Live Save review flow (J-57).** The iter-13 disabled `save-review-disabled` placeholder is
  REMOVED. The tag picker (`data-testid="mistake-tag-picker"`) seeds from the backend's SUGGESTED
  tags (each marked `·sug` and listed in a "suggested from the execution checks" line — visibly
  distinct from the user-confirmed set) and stays toggleable. Selecting `other` reveals a required
  note textarea (`data-testid="review-note-input"`) with inline validation
  (`data-testid="review-note-error"`); Save (`data-testid="save-review"`) is disabled until the note
  is present. Save posts to `POST /research/thesis/{id}/review`; on success the page re-reads the
  detail and renders the `Reviewed` chip (`data-testid="review-saved"`) + the confirmed tags
  (`data-testid="confirmed-tags"`) + note (`data-testid="confirmed-note"`). An already-reviewed
  thesis shows the saved selection read-only (the tags + Save are disabled). The backend's 4xx detail
  surfaces inline (`data-testid="save-review-error"`).

### `/journal` (JournalTable)

- New **Grade** column (`data-testid="journal-grade-cell"`): outcome + process enum chips
  (`journal-outcome-grade` / `journal-process-grade`), labels from the taxonomy. Pre-grade rows
  (active / pre-v6) show an em dash.
- New **Reviewed** column (`data-testid="journal-reviewed-cell"`): a `Reviewed` chip
  (`journal-reviewed-chip`) when `reviewed` is true, else an em dash.

## Files Changed

- `apps/frontend/lib/types.ts` -- `ThesisGrades`, `StatementFinalStatus`, `SavedReview`; extend
  `JournalRow` (grades?/reviewed), `JournalDetail` (statement_final_statuses?/grades?/reviewed/review?),
  `JournalDetailThesis`, `ResearchTaxonomy` (outcome_grades?/process_grades?).
- `apps/frontend/lib/api.ts` -- `saveReview(thesisId, mistakeTags, note)`.
- `apps/frontend/components/JournalDetailView.tsx` -- final-status badges, GradesQuadrant, the live
  ExecutionChecksSection Save flow.
- `apps/frontend/components/JournalTable.tsx` -- Grade + Reviewed columns + `gradeClass` helper.
- `apps/frontend/app/journal/[id]/page.tsx` -- `onSaved={load}` re-reads the detail after a save.

## Design System Conformance

- Dark instrument-panel style preserved; color semantics consistent (emerald = good/held/clean, amber
  = flagged advisory, rose = failed/violated, slate = neutral/no-read). Mono numerics retained.
- All labels come from the taxonomy (no hardcoded grade/tag/status copy). The "Descriptive only — not
  trading advice" footer discipline extends to the new blocks. Copy is past-tense and descriptive.
- Interactive elements (tag buttons, Save) carry hover/focus states and disabled treatments; loading
  ("Saving…"), empty (honest omission notes), and error (inline alert) states are handled.

## Tests Run

Command: `cd apps/frontend && NEXT_DIST_DIR=.next-qa npm run build`
Result: **PASS** — compiles + type-checks clean; `/journal` and `/journal/[id]` emitted.

## Known Issues

- Frontend behavior is browser-verified in the qa step. The build (type-check + compile) is the only
  frontend automated gate in this project; the J-55/J-56/J-57 acceptance is exercised by
  browser-qa-agent against the live backend.
