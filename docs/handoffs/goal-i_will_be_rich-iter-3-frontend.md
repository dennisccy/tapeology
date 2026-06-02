# goal-i_will_be_rich-iter-3 Frontend Handoff

**Phase:** goal-i_will_be_rich-iter-3
**Date:** 2026-06-02
**Agent:** developer
**Status:** complete

## UI Change

The cockpit's color language now actually renders. No structural, layout, copy, or
component change — the single `/` cockpit is unchanged in shape. Only the **color
presentation** of existing elements is corrected:

- "Buyer Control" headline state label → emerald (was slate)
- Confidence-bar fill → emerald (was transparent)
- BUY trade-side cells → emerald; SELL → rose; unknown → slate (as designed)
- Positive `buy_price_impact` → emerald; negative → rose; zero → slate

These all read their classes from `lib/format.ts`; the fix makes those classes exist in the
served bundle. The amber (absorption/unclear) and rose (seller) base utilities are now in the
bundle as well, so the upcoming J-03/04/05/06 journeys won't hit the same latent breakage.

## How It Was Fixed

`apps/frontend/tailwind.config.ts` — added `./lib/**/*.{ts,tsx}` to the `content` globs so
Tailwind scans `lib/format.ts`, where all 8 color classes appear as literal return strings.
No component was edited; `format.ts` was left as-is per spec.

## Files Changed

- `apps/frontend/tailwind.config.ts` — `content` now includes `./lib/**/*.{ts,tsx}`.

## Verification

- `npm run build` clean; built CSS contains all 8 base utilities with correct emerald/amber/
  rose RGB values (measured via stylesheet-rule probe, not by eye).
- Dev server (`next dev`, HTTP 200): all 8 base utilities present in the dev-served stylesheet.
- See the main dev handoff (`goal-i_will_be_rich-iter-3-dev.md`) for the full red→green
  measurement table and the exact elements/RGB values QA should `getComputedStyle`-assert.

## States Handled

Presentation-only change — no new loading/empty/error states. Existing idle/connecting/
warming-up states are unaffected (their colors, e.g. `text-amber-400` warming-up hint and the
TopBar status dot, were already static and remain correct).
