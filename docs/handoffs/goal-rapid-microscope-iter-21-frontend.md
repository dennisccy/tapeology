# goal-rapid-microscope-iter-21 Frontend Handoff

**Phase:** goal-rapid-microscope-iter-21
**Date:** 2026-08-20
**Agent:** developer
**Status:** complete

## What Was Built

A minimal, targeted fix to the already-shipped Scout Ledger section so it renders the two new
`structure_context.kind` values (`"band_touch"`, `"playbook_signal"`) J-09 wires on the backend —
no new section, page, heading, or shipped column (T-11).

- **Scout Ledger trial row, Feature cell** (`apps/frontend/app/desk/page.tsx`, the
  `family.trials.map(...)` block, ~line 6312-6353): now renders `structure_context.kind` inline,
  appended after the existing `feature.name / feature.transform` text, whenever the kind is not
  `"none"` — e.g. `divergence_at_level_bearish / threshold (band_touch)`. A `"none"`-kind row
  (every row the shipped J-04 default reference grid has ever produced, and the only kind that
  existed before this iteration) renders EXACTLY the text it always has — the addition is
  conditional and additive, never touching the `"none"` render path.
- **`lib/types.ts`** — `ScoutTrialRow.structure_context` widened from `{ kind: string }` to
  `{ kind: string; setup_id?: string }` (additive; matches the backend's new optional field on
  Study 3's own frozen spec, never served on any row this iteration actually screens).
- **Microscope Readiness — Sealed Tranche table gains one new row, "Joinable corpus — band
  touches"** (`apps/frontend/app/desk/page.tsx`, ~line 6005, the SAME table the existing
  "Joinable corpus — withheld (excluded)" row lives in): renders the real materialized int when
  `band_touch_count.status === "enumerated"`, else the honest `"not enumerated"` string — never a
  bare number a reader could mistake for a real zero. `lib/types.ts` already carried the correct
  `MicroReadinessJoinableCorpus.band_touch_count: { status: string; count: number | null }` type
  (its own comment named this "a future J-09 home" — this iteration IS that home); no type change
  needed, only the render. This closes the plan's own "New information displayed:
  `joinable_corpus.band_touch_count`'s real int in Microscope Readiness" item, which a first pass
  of this handoff incorrectly assumed was already covered by an existing render path — corrected
  after a direct grep of the live source found no `band_touch_count` render anywhere.

## Why this and nothing more

The plan's own scope for this iteration's frontend work was narrow: "verify the already-shipped
Scout Ledger section renders a `structure_context.kind="band_touch"` row generically... fix
minimally if a genuine gap is found — no new section/heading/column (T-11)." A source read of the
existing render path (before this fix) confirmed the table rendered `feature`/`outcome`/
`decision`/`reason`/`notes`/`withheld_excluded`/`screen_result` — but never `structure_context` at
all, anywhere, even inside the collapsed `screen_result` JSON detail (which is the SCREEN's own
computed disclosures, not the frozen candidate spec). This is the genuine gap TC-8 (browser-qa)
needs closed: "the candidate's row is visible and its `structure_context.kind` reads 'band_touch'
on screen." The fix adds it inline inside the EXISTING Feature cell rather than a new column,
honoring T-11's "no new column" instruction while still making the value genuinely visible.

No other UI change was needed or made:
- The Walk-Forward section's own UI reads `GET /research/desk/micro/walkforward`
  (`WalkForwardLedger`), a DIFFERENT store from the Scout ledger `register_screen_and_
  walkforward_check`'s own floor-check row is appended to (see the dev handoff's own reasoning for
  why the floor check lands in the SAME scout ledger as the screen, under the SAME
  `candidate_id`) — so the floor-check decision is visible in the Scout Ledger section (both the
  screen row and the floor-check row share one family's trial table), not a separate Walk-Forward
  section change. TC-8 itself only names the Scout Ledger section for browser verification, not
  Walk-Forward, which is consistent with this.
- No new button, control, or nav entry — the pilot grid stays CLI/manager-only this iteration
  (goal.md OUT OF SCOPE), matching the "operator act, not goal-mode act" framing.

## Files Changed

- `apps/frontend/app/desk/page.tsx` — Scout Ledger Feature cell, one conditional inline span; one
  new row in the Microscope Readiness Sealed Tranche table for `band_touch_count`.
- `apps/frontend/lib/types.ts` — `ScoutTrialRow.structure_context` type widened additively; a
  stale comment on `MicroReadinessJoinableCorpus` corrected (no type change needed there — the
  `band_touch_count` type was already correct).

## Verification

- `rm -rf apps/frontend/.next && npm run build` — clean build (`Compiled successfully`), type
  check passed, all three routes (`/`, `/desk`, `/structure`) prerendered successfully.
- Static source verification (grep) that both restored `J-10.json` golden-replay strings ("Built
  from signature:", "recorded signals, none hidden") and the `desk-section-expand-playbookEvidence`
  / `desk-playbook-date-input` testids are still present verbatim in the current frontend source.
- **A live, real-browser sanity check** (Chrome DevTools Protocol, `dev.sh` on :8301/:3301, the
  REAL production `.data/` corpus — not the formal QA fixture-scoped rig): navigated to `/desk`,
  expanded Microscope Readiness, confirmed the served HTML actually contains `<td
  data-testid="micro-readiness-band-touch-count">8247</td>` — a real, non-zero, live-computed
  count matching `GET /research/desk/micro/readiness`'s own JSON exactly (at least one of the 18
  real registered tick datasets' own symbol/date already has an operator-warmed tradability map).
  Also expanded Scout Ledger and confirmed the shipped `"No candidates ledgered."` empty state
  still renders correctly (the production ledger is genuinely empty — J-10's own expectation,
  unaffected by this iteration). This is a personal sanity check by the developer agent, not the
  formal QA evidence capture — the browser-qa-agent's own pass (against the fixture-scoped rig,
  with real screenshots) remains the DoD's actual evidence source for TC-8, the golden replay of
  the restored `J-10.json`, and the UT-10 element-capture re-take.

## Known Issues

- The walk-forward floor-check ledger row (no `feature`/`structure_context`/`outcome` fields of
  its own — see the dev handoff) renders as mostly em-dashes (`—`) in the Feature/Horizon columns
  and `null` in the collapsed `screen_result` detail. This is honest (never fabricated) but was not
  given its own dedicated rendering this iteration — a minor, deferrable UX polish item.
