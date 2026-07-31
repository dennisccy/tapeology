# goal-desk-iter-34 Frontend Handoff

**Phase:** goal-desk-iter-34
**Date:** 2026-07-31
**Agent:** developer
**Status:** complete

## What Was Built

`/desk` → Top-up Runs → latest-run detail → "Pairs recorded earlier" block:

- **Grouping fix**: `topupLibraryReach` now derives one day-truncated key per outcome
  (`store_frozen_through_after.slice(0, 10)`) and uses that key for every grouping/comparison
  decision (finding the newest day, counting how many pairs reach it, partitioning "earlier").
  Previously it compared the raw microsecond-precision timestamp, so a pair recorded a few hours
  behind another pair on the SAME calendar day was wrongly shown under "Pairs recorded earlier"
  even though its own printed date (day-truncated at render time, unchanged) matched the "newest
  recorded reach" line's own printed date. That contradiction is now impossible.
- **Honest cap + disclosure**: the "Pairs recorded earlier" list renders at most 20 rows
  (`EARLIER_PAIRS_DISPLAY_CAP`). The heading's count is now the TRUE total (a new `earlierTotal`
  value), not the capped list's own length, so "Pairs recorded earlier (101)" stays accurate even
  though only 20 rows are shown. When the true total exceeds 20, one new plain sentence appears
  ("showing 20 of 101", new testid `desk-topup-run-latest-reach-earlier-cap`) between the heading
  and the row list. When the true total is ≤ 20, nothing new renders — behavior is unchanged from
  before this iteration.

No new section, control, or table column. Everything sits inside the already-registered
library-reach block between `desk-topup-run-latest-window-basis` and
`desk-topup-run-latest-failed` — J-16's measured table-width contract is untouched (this block is
outside the ranked table entirely).

## Files Changed

- `apps/frontend/app/desk/page.tsx` — `topupLibraryReach` (day-precision grouping, cap, true-total
  tracking) + `LatestTopupRunDetail`'s render (heading now reads `earlierTotal`; new conditional
  cap-disclosure paragraph).

## Visual / UX notes

- The new disclosure sentence reuses the existing muted descriptive-text style
  (`text-xs text-slate-400`), matching `WINDOW_BASIS_NOT_RECORDED`/`LIBRARY_REACH_NOT_RECORDED`'s
  own styling — no new color, badge, or emphasis introduced.
- Verified live (screenshot: `reports/qa/goal-desk-iter-34-evidence/UT-J-19-topup-reach-crop.png`,
  1440×900 viewport, T-9 clean rebuild) against the ambient `topup-2026-07-31-8fb5c9a1f737` run:
  "newest recorded reach 2026-07-30 · 303 pairs reach it", "Pairs recorded earlier (101)", "showing
  20 of 101", followed by 20 rows all printing `2026-07-27` — no row prints `2026-07-30`, and no
  horizontal scroll was introduced.
- States exercised: (1) true total > 20 → heading + disclosure + 20 capped rows (LIVE, confirmed
  above); (2) true total ≤ 20 → no disclosure (structural/unit only — the current ambient run's
  true total is 101, so this branch isn't exercised live this iteration; the conditional's own gate
  makes it structurally impossible to render the sentence when `earlierTotal <=
  EARLIER_PAIRS_DISPLAY_CAP`); (3) legacy run (no `store_frozen_through_after` anywhere) → unchanged
  `LIBRARY_REACH_NOT_RECORDED` fallback, this code path untouched by the diff; (4) all pairs share
  the same day → empty "earlier" list, section does not render at all (unchanged
  `earlierTotal > 0` gate, renamed from the prior `earlier.length > 0` gate but behaviorally
  identical since the cap never empties a non-empty true-total).

## Golden replay script

`runs/goal-session-desk/journey-scripts/J-19.json` repointed: no longer asserts any specific date,
count, or the bug's own contradictory row text (previously step 4 asserted `"AAPL 4h — 2026-07-30"`
as an EARLIER row — literally the bug this iteration fixes). New steps assert only stable
substrings ("reach it", "Pairs recorded earlier") and testid existence (a row renders; the
cap-disclosure renders — the latter documented as environment-dependent, since it depends on the
ambient run's true earlier-total staying above 20). Verified via `demo_runner.py --mode verify`
against the real ambient `:3301` frontend: PASS (6/6 including the five Required-still-passing
journeys J-04/J-07/J-09/J-16/J-17, unaffected).

## Known Issues

- The `[NEW]`-flagged demo-narrator walkthrough for this fix has not been recorded — that is a
  separate pipeline step, expected to run against the now-fixed page.
- TC-5 (the "true total ≤ 20 → no disclosure" branch) has no live screenshot this iteration; see the
  dev handoff's TC-1..TC-9 disclosure for the full breakdown of what was verified live vs.
  structurally.
