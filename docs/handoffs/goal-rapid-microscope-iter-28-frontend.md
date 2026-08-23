# goal-rapid-microscope-iter-28 Frontend Handoff

**Phase:** goal-rapid-microscope-iter-28
**Date:** 2026-08-23
**Agent:** developer
**Status:** complete

## What Was Built

- **One new disclosure line on `/desk`, inside the already-shipped Referee Registry → Strategy
  Family block** (`referee-evidence-strategy-block`, part of `RefereeEvidenceReadinessSection`).
  Per the owner's 2026-08-18 r5-point-7 ruling (`docs/rapid-validation-spec.md` §10.7):
  `referee_evidence.strategy_trade_readiness`'s served counts (`Datasets`, `Train / Holdout`,
  `Trades`) count dataset FILES through the legacy Referee's own enumeration and may include
  withheld/unexposed Rapid-Microscope shards — a seal-unaware compatibility gap the spec requires
  disclosed verbatim wherever that metric is served. `referee_evidence.py`/`referee_routes.py`
  stay byte-frozen this whole era, so the caveat is served ONLY as static frontend copy, never a
  computed value and never a behavior change.
- No new page, no new nav entry, no new API call, no new user action. The block already fetched
  `GET /research/desk/referee/evidence` before this change; the new element renders a hard-coded
  string beside the response's existing `strategy_trade` figures.

## Files Changed

- `apps/frontend/app/desk/page.tsx`:
  - New module-level constant `REFEREE_EVIDENCE_SEAL_UNAWARE_CAVEAT` (defined once, just above
    `RefereeEvidenceReadinessSection`), holding the verbatim spec §10.7 sentence: *"Legacy Referee
    readiness metric — seal-unaware in the Rapid Microscope era. It may include withheld/unexposed
    Rapid-Microscope shards and must not be used as the canonical Rapid-Microscope readiness
    count."*
  - New `<p data-testid="referee-evidence-strategy-seal-unaware-caveat" className="mt-2 text-[11px]
    text-slate-500">{REFEREE_EVIDENCE_SEAL_UNAWARE_CAVEAT}</p>` inside
    `referee-evidence-strategy-block`, placed directly after the existing
    `referee-evidence-strategy-tick-gate` `<p>` and before the existing
    `referee-evidence-strategy-basis-caveats` `<ul>` — i.e. immediately beside the block's
    Datasets/Train-Holdout/Trades table.

## UI Evolution

- **New user-facing capability:** none — disclosure only, per spec (no new action, no new page).
- **New information displayed:** the verbatim seal-unaware caveat sentence, rendered beside the
  Referee Registry → Strategy Family block's existing Datasets/Trades/tick-gate figures on
  `/desk`.
- **New user actions:** none.
- **UI surface changes:** one new `<p>` element inside the already-shipped
  `referee-evidence-strategy-block`. No new section, no new page, no nav change.
- **Navigation changes:** none.

## Visual Requirements Applied

- Matches the existing block's style exactly — same `text-[11px] text-slate-500` treatment
  already used for `referee-evidence-strategy-basis-caveats`, so the new line reads as part of
  the same disclosure family rather than a new visual unit (the block's tick-gate line uses
  `text-slate-400`; the caveat uses `text-slate-500`, matching the more-muted basis-caveats
  styling directly below it since it is a secondary/compatibility note, not the primary served
  statement).
- Inline within the existing table/caveat stack — no new card, panel, or section was created.
- No new visual effects — static disclosure copy, not interactive; no color implies advice (Design
  Direction: class labels render verbatim, no color implies advice).
- No new loading/empty/error state — the text is static and always renders whenever the parent
  block itself renders (it is not computed, so it has no state of its own).

## Tests Run

- `npx tsc --noEmit -p tsconfig.json` from `apps/frontend/` — clean, zero type errors.
- Backend static-scan guard `apps/backend/tests/test_micro_readiness_seal_unaware_caveat.py`
  (4/4 pass) proves: the sentence is defined exactly once as a shared constant in
  `apps/frontend/app/desk/page.tsx`, the constant is actually rendered (not dead code), and its
  text matches `docs/rapid-validation-spec.md` §10.7 character-for-character.
- `apps/backend/tests/test_copy_discipline.py` (30/30 pass) — confirms the new frontend string
  and surrounding code comments trip none of the imperative/prediction/claim-language lint rules.

## Known Issues

- **No live browser render was captured by this dev pass.** The plan's own division of labor puts
  the live `/desk` element-scoped screenshot (spec TC-5: `rm -rf apps/frontend/.next` + rebuild
  per T-9, then an element capture of `referee-evidence-strategy-strategy-block` /
  the new `referee-evidence-strategy-seal-unaware-caveat` testid specifically, never a full-page
  stitch) on the downstream browser-qa-agent lane, which also needs to genuinely LLM-verify
  target journeys J-01/J-10 this round (the deterministic replay lane cannot execute a target
  journey's own golden in the round that touches it).
- The new `<p>` element's line-wrapping/visual spacing at real viewport widths has only been
  reasoned about from the existing sibling elements' classes, not visually confirmed — flag for
  the browser-qa pass to sanity-check wrapping doesn't collide with the following
  `basis_caveats` list.
