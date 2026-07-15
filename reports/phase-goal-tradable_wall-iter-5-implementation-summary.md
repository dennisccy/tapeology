# goal-tradable_wall-iter-5 — Implementation Summary

**Phase:** goal-tradable_wall-iter-5
**Date:** 2026-07-14
**Written by:** developer

---

## Features Implemented

This is a "make the plumbing honest and fast" iteration — nothing new appears on any page yet.
It fixes two problems the previous iteration's reviewer flagged as things that must be fixed
*before* the case-study browser can go on screen (planned for next iteration).

- **Honest labeling for very recent price touches**: the case-study scanner looks at where price
  touched a trading band and then reports what happened next ("rejected", "broke", or "chopped"),
  measured about 6.5 hours of trading later. For touches that happened very recently — so recently
  that 6.5 hours of trading data hasn't accumulated yet — the scanner was still giving a definite
  verdict while quietly reporting "no data" for the follow-up numbers, with nothing telling the
  reader *why*. Now every such case honestly says "this verdict was based on less time than usual,
  and here's exactly how much." Tested against the operator's own real price history: out of 801
  touch events found, exactly 13 recent ones now carry this honest label (matching the number the
  previous iteration's review had already spotted and flagged for fixing). Nothing about which
  touches get scored, or what verdict they get, has changed — this only adds an honest label where
  one was missing.
- **A much faster case-study/comparison report**: scanning the entire 12-symbol watchlist's price
  history for every touch event is slow. Three different pages/features all needed to run that
  same slow scan every single time someone asked for the data — meaning one visit to the future
  "case studies" page could have triggered it up to three times in a row. Now the app remembers
  the last scan result and only redoes the work when the underlying price history actually
  changes. Tested against the operator's own real, already-fetched price history (47 stored price
  series, 801 touch events found): the first request took **4 minutes 36 seconds**; every request
  after that — for the case-study list, for a single case's details, and for the profit
  comparison report — came back in **under half a second**, returning the exact same numbers
  every time. Nothing about the numbers themselves changed — only how often they're recomputed.

---

## Changed Behavior

- **None visible.** No page looks or behaves differently. The scanner's calculations, the profit
  comparison report, and every existing screen work exactly as before — verified by re-running the
  full automated test suite. The only difference is two new, honest, additional data fields
  attached to each recent-touch record (used internally / by the API), and the multi-minute scan
  now runs once instead of repeatedly.

---

## Backend-Only Items

- **The two new "how much data was this verdict based on" fields** — available today through the
  API and the AI-assistant read tool, but not shown on any page. The next iteration is expected to
  surface them when it builds the case-study browser.
- **The speed fix** — invisible by design; there is no "cache" toggle or setting. It simply makes
  the existing API faster on repeat requests.

---

## Incomplete Items

None — every requirement for this iteration was completed. Explicitly **out of scope** (planned
for later iterations):

- Actually putting any of this on a page (the `/structure` case-study browser) — next iteration.
- Any change to the cockpit chart — the iteration after that.
- Recording more real historical trading data with the operator's own market-data credentials —
  a separate, operator-run action, unaffected by this iteration.

---

## Config and Environment Changes

None. No new environment variables, no new settings, no database migration, no change to the
internal fingerprint the app uses to guarantee "these results were computed under the same
rules" (double-checked and confirmed unchanged).

---

## Known Limitations

- **The very first request after the app starts (or after new price history is fetched) is still
  slow** — the app has to actually do the scan at least once before it has anything to remember.
  This iteration makes repeat requests fast; it does not make the first one faster.
- **The memory of the last scan lives only in the running app process** — it is not saved to disk.
  If the backend restarts, the next request pays the slow scan once again, then goes back to being
  fast. This is deliberate: the previous iteration's implementation summary itself flagged this as
  the right kind of cache to add ("a future iteration should consider caching that scan"), and a
  disk-persisted cache would risk quietly serving stale results if it were ever forgotten about —
  an in-memory, auto-refreshing cache cannot get stuck stale.
