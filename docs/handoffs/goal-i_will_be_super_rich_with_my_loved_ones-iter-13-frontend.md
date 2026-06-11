# goal-i_will_be_super_rich_with_my_loved_ones-iter-13 Frontend Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-13
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

The `/journal/[id]` review-detail page (J-55) under the existing Journal home, rendered ENTIRELY
from the single `GET /research/journal/{id}` response + `GET /research/taxonomy` labels. The frontend
recomputes NOTHING — every value is a verbatim read of the persisted record (single source of truth).

### New route — `app/journal/[id]/page.tsx`
- Unwraps the Next 15 `params` Promise (`use`), fetches the detail + the taxonomy, and renders one
  of four states: a loading skeleton, an explicit **honest error / not-found** state (an unknown id
  → 404 → a styled alert + "Return to the journal", never a blank page), or the `JournalDetailView`.
- A "← Back to journal" link; the persistent NavBar already keeps **Journal** active on the nested
  `/journal/[id]` route (no nav change needed).

### `components/JournalDetailView.tsx`
Renders, all from the one response:
- **Thesis header** — ticker, setup + direction (taxonomy labels), status chip, invalidation/level
  (mono), declared date via the ONE shared `formatDateTimeDMY` (dd-MM-yyyy + local zone), bound
  source, feed, config fingerprint.
- **What you expected** — the frozen expected-behaviour statements (verbatim text); a note that the
  final status is read from the timeline (the canonical record).
- **Entry risk flags** — the frozen `risk_flags` as amber chips with their measured evidence
  verbatim. Honest omission: key ABSENT → "Not assessed — this thesis predates entry-risk
  assessment" (never an invented clean state); empty array → "Assessed at declaration — no entry risk
  flags fired".
- **What you did** — the action marks (price + true clock time + spread-at-mark); the realized move
  in **R** shown ONLY when both marks exist (no marks → no realized metric, never a dishonest zero) —
  labeled a journaled measurement, never P&L.
- **What the execution checks found** — one card per check with its enum status chip
  (`Flagged`/`Clean`/`Not applicable` — labels, never a numeric score) + the plain-language evidence
  verbatim. Below: the **suggested mistake-tag picker** — pre-selected with the backend's
  `suggested_mistake_tags`, toggleable, tag labels read ONLY from `taxonomy.mistake_tags`; a
  **disabled "Save review"** button with honest copy ("Saving a review is coming with the review
  flow") — mirrors the approved Studies-disabled no-dead-control pattern (the J-57 save flow lands
  next iteration). Honest omission: `execution_checks` absent → "Not assessed — execution checks are
  computed once a thesis is resolved, and this thesis predates that".
- **What the tape did** — the append-only verdict timeline at **true clock time** (persisted
  `wall_ts` via the shared formatter — never elapsed playback seconds, no client re-derivation); each
  row carries its verbatim evidence, last/state/confidence, and the `rule_first_true` price when
  present; gap/lifecycle rows (`expired`/`watch_restarted`/`paused`) get a distinct dashed muted
  treatment.
- The "Descriptive only — not trading advice" disclaimer (from the taxonomy) at the foot.

### `components/JournalTable.tsx`
- `/journal` rows are now **links** to `/journal/[id]` (the iter-12 "deliberately not links"
  placeholder resolves). The ticker cell carries a real `next/link` anchor (keyboard/SEO
  accessible); the whole row also navigates on click via `useRouter().push` (the anchor stops
  propagation so it doesn't double-fire).
- The empty-state `▤` (U+25A4) glyph was replaced with class-based muted rules (design-system tokens
  only; no icon library, no Unicode glyph) — the coherence fold-in.

### `lib/types.ts` / `lib/api.ts`
- New types: `JournalDetail`, `JournalDetailThesis`, `JournalTimelineRow`, `ExecutionCheck`,
  `MistakeTag`; `mistake_tags?` added to `ResearchTaxonomy`.
- `fetchJournalDetail(thesisId)` — GET `/research/journal/{id}`; resolves to `{ok, detail}` on 200,
  `{notFound: true}` on 404 (page shows the honest error state), or an explicit error on an
  unreachable backend (never a blank page).

## Design System Adherence
- Dark instrument-panel style; slate surfaces, restrained borders; mono for all prices/sizes/times.
- Color semantics reused, never repurposed: emerald = confirming/clean/long, rose =
  rejecting/invalidated/flagged/short, amber = risk-flag advisory + selected mistake tags, slate =
  pending/not-applicable/gap. Verdict + check-status COLORS are keyed off the id (a visual concern);
  every LABEL comes from the taxonomy (the frontend hardcodes none).
- Every interactive element (back link, row link, tag toggle, disabled Save) has hover/focus/active
  treatment; the disabled Save is visibly disabled with `aria-disabled` + a title.
- Loading / error / not-found / empty states all handled — not just the happy path.

## Tests Run
`cd apps/frontend && NEXT_DIST_DIR=.next-devbuild npx next build` → compiled + type-checked clean;
`/`, `/journal`, and the new `ƒ /journal/[id]` dynamic route all emitted. (Throwaway dist dir so the
QA harness's `.next` was untouched; the transient dir + the auto-edited `next-env.d.ts`/`tsconfig.json`
were reverted afterwards.)

## Known Issues
- Browser QA (the qa step) must capture the new below-the-fold `/journal/[id]` surface with
  scroll-into-view / full-page captures and open the PNGs — reuse of prior frames is only valid for
  re-rendered frozen data, never for this NEW detail surface. Test data-testids on the page:
  `journal-detail`, `detail-status-chip`, `detail-statements`, `detail-risk-flags` (+
  `risk-flags-not-assessed`), `detail-marks` (+ `detail-entry-mark`/`detail-exit-mark`/
  `detail-realized-r`), `detail-execution-checks` (+ `detail-execution-check` with `data-check` /
  `data-status`, `execution-checks-not-assessed`), `mistake-tag-picker` (+ `mistake-tag` with
  `data-tag`/`data-selected`), `save-review-disabled`, `detail-timeline` (+ `detail-timeline-row`
  with `data-verdict`, `detail-timeline-time`), `detail-error`. On `/journal`: `journal-row`
  (`data-href`), `journal-row-link`, `journal-empty-mark`.
