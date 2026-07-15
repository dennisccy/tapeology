# goal-tradable_wall-iter-8 Frontend Handoff

**Phase:** goal-tradable_wall-iter-8
**Date:** 2026-07-15
**Agent:** developer
**Status:** complete

## What Was Built

**Cleanup A only** -- one bugfix inside the cockpit `PriceChart.tsx`'s existing tradable-band fetch
effect. No new component, no new page, no new visual element, no layout change. This closes the
iter-7 audit's F1 finding.

- **Before (iter-6/iter-7):** the tradability-fetch effect computed `as_of` as
  `history?.epoch_anchor != null ? new Date(history.epoch_anchor * 1000).toISOString() :
  new Date().toISOString()` -- i.e., it fell back to the browser's current wall-clock time whenever
  the watched session's own `epoch_anchor` had not yet resolved (the sub-second window before the
  first `…/history` poll response lands after a ticker/session change). During that window the
  effect would fire a request for **today's** morning-markup basis and could transiently draw the
  WRONG session's bands on the chart before the correct anchor-derived request superseded it a
  moment later.
- **After (this iteration):** the effect now checks `history?.epoch_anchor == null` FIRST and, if
  true, sets `phase: "loading"` and returns immediately -- no HTTP request is issued at all until a
  real anchor exists. The `: new Date().toISOString()` fallback branch is gone entirely; the only
  `as_of` computation left is `new Date(history.epoch_anchor * 1000).toISOString()`. The effect's
  dependency array is unchanged: `[ticker, history?.epoch_anchor]`.

This is a pure timing/correctness fix to an already-shipped effect -- nothing new is drawn, no new
state is introduced, no new prop or API call shape changed.

## Files Changed

- `apps/frontend/components/PriceChart.tsx` -- the tradability-fetch effect (previously ~L196-218)
  gained a 6-line early-return guard before its existing `let cancelled = false;` line; the `asOf`
  computation collapsed from a 4-line ternary to a single line (no fallback branch); the explanatory
  comment block immediately above the effect (previously ~L180-195) was rewritten to describe the
  new deferred-fetch, no-fallback behavior instead of documenting the old wall-clock fallback. No
  other line in the file changed -- the chart-creation effect, the candle/marker-drawing effect, the
  thesis-geometry effect, the band-drawing effect, the confluence-chip derivation, and all JSX are
  byte-identical to iter-7.

## Visual / Design Notes

No visual change. No new component, color, spacing, or effect. The band overlay and confluence chip
render exactly as iter-7 shipped them -- only the TIMING of when the underlying fetch is allowed to
fire changed (deferred instead of firing early against the wrong date).

## States Covered

- **Anchor not yet resolved** (first paint after a ticker/session change, before the first
  `…/history` response lands): previously issued a request against today's date; now issues NO
  request and stays in `phase: "loading"` -- confirmed this does not trip the ready-only
  `tradabilityEmpty`/confluence-chip logic (both gate on `phase === "ready"`, never on `"loading"`).
- **Anchor resolved:** unchanged -- fetches `GET /research/tradability` with the session's own
  `epoch_anchor`-derived `as_of`, exactly as iter-7.
- **SIM tickers:** unaffected -- confirmed via `apps/backend/app/providers/simulated.py:137`
  (`self.epoch_anchor = CONFIG.sim_session_anchor_epoch`, a fixed non-null value set at
  `SimulatedProvider.__init__`), so a SIM ticker's `epoch_anchor` is never null and this change is a
  structural no-op for the SIM path -- the honest "no tradable map" empty state still triggers the
  same way it always did (via the served `no_bar_series_for_symbol` field, not via this timing
  guard).
- **Live mode:** untouched -- `PriceChart` is not even mounted in live mode (the pre-existing gate in
  `page.tsx`, not touched this iteration).

## Tests

Same situation as every prior era-5B iteration: no frontend test runner exists in this repo
(`apps/frontend/package.json` has no `test` script, no `.test.ts(x)` file anywhere). Frontend
correctness was verified via:

1. `npx tsc --noEmit -p tsconfig.json` -- exit 0, zero type errors.
2. The 9 Python source-inspection tests in `apps/backend/tests/test_price_chart_confluence.py`
   (this repo's established precedent for testing frontend logic keylessly). Two were rewritten this
   iteration (module docstring, and
   `test_tradability_as_of_uses_the_watched_sessions_own_anchor_with_no_client_side_session_math`) to
   assert the new guard/no-fallback behavior; the other 7 are unmodified. All 9 pass. **Genuine
   red-then-green confirmed**: I stashed only the `.tsx` fix, reran the new test against the
   unmodified (iter-7) frontend, watched it fail with the exact expected message pinpointing the
   `new Date().toISOString()` fallback line, then restored the fix and reran to green -- see the dev
   handoff's "TDD Verification" section for the full transcript.
3. `test_copy_discipline.py` -- unaffected (no new copy was added; the chip text is unchanged).

No new browser verification was performed by me (developer) for this cleanup itself -- the plan
names browser re-verification of J-06/J-05/J-07 as a subsequent QA-stage activity, not a developer
pre-handoff step. I did, however, independently confirm via a live backend read (see the dev
handoff's "Live Verification" section) that the DATA this component will render once QA drives a
browser -- the pinned AAPL 2026-06-22 case's real tape timeline and band -- is now genuinely
populated on the operator's persisted store, which is the substantive product change this iteration
closes.

## Known Issues

See the dev handoff's "Known Issues" section (same list; the `GET /research/edge-report` timing
finding and the `scripts/dev.sh` process-cleanup finding are both relevant context for whoever runs
the next browser-QA pass against this iteration).
