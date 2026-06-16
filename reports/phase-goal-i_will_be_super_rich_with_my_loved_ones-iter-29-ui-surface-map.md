# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-29 — UI Surface Map

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-29
**Date:** 2026-06-16
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

No UI source files were changed this iteration. The table below lists the surfaces exercised against a real live IEX feed to confirm existing behavior — change type is "Verified existing" for each.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | Live status indicator (status dot + label in cockpit status area) | Verified existing | J-15: confirmed `live → stale → live` flip on a real IEX feed lull | Enter a liquid symbol (e.g. `F` or `IBM`), start a live watch, observe status dot turns green with label `live`; wait for a genuine >10s feed lull and confirm the dot turns amber with label `stale` while the recent-trades count remains frozen; confirm the dot returns to green `live` on the next real market print |
| `/` | `FeedBasisBadge` (cockpit status area, adjacent to stream status) | Verified existing | J-67: confirmed badge renders "IEX (live)" with disclosure text on a real live IEX watch | Start a live watch on any symbol; confirm the badge reads "IEX (live)" and the disclosure line "live verdicts read the single-venue IEX feed; historical replay and studies use SIP — spreads and prints differ" is visible in the cockpit viewport |
| `/journal` | Journal table row — `data_feed` column | Verified existing | J-67: confirmed rows produced during a live IEX watch are stamped `data_feed = iex` with no SIP mixing | Declare a thesis during an active live IEX watch; navigate to `/journal`; confirm the resulting row shows `data_feed = iex` in the data-feed column and `bound_source` references the live symbol |

---

## Backend-Only Changes (No UI Impact)

- `reports/qa/goal-…-iter-29-evidence/ibm-live-summary.json` — captured live IBM REST snapshot (`stream_status: live`, `data_feed: iex`, real bid/ask); evidence artifact only, no UI surface affected.
- `reports/qa/goal-…-iter-29-evidence/j15-stale-sequence-rest.md` — log of the `live → stale → live` REST polling sequence with recent-trades-frozen proof; evidence artifact only, no UI surface affected.
- `reports/qa/goal-…-iter-29-evidence/journal-iex-row.json` — captured live-declared journal row stamped `data_feed = iex`; evidence artifact only, no UI surface affected.
- `reports/qa/goal-…-iter-29-evidence/taxonomy-feed-basis.json` — captured `feed_basis` block (IEX label + verbatim disclosure text); evidence artifact only, no UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 0 (application code); 4 evidence-only artifacts added under `reports/qa/`
