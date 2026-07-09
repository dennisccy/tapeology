# goal-yahoo_fetch-iter-3 — Implementation Summary

**Phase:** goal-yahoo_fetch-iter-3
**Date:** 2026-07-09
**Written by:** developer

---

## Features Implemented

- **Fetching the same data twice no longer re-downloads it from Yahoo Finance.** Before this
  iteration, every "fetch this symbol/timeframe/date range" request went out to Yahoo Finance over
  the network, even if the app had already fetched and saved that exact same data before. Now the
  app remembers what it already has, using a small, fast lookup index built specifically for this
  purpose. Asking for the same symbol, timeframe, and date range a second time comes back
  instantly — no network round-trip, no waiting on Yahoo Finance — because it's simply read back
  from what was already saved. Tested live against real, already-recorded data: a repeat request
  came back in 19 milliseconds.
- **Bar data can now be found by symbol and timeframe.** The app's data listing can now be narrowed
  down — for example, "show me only Apple's daily candles" — instead of always returning every
  single recorded series at once. Asking for a symbol or timeframe (or both together) that was
  never fetched simply returns nothing, cleanly, rather than an error.
- **The lookup index can rebuild itself from scratch at any time.** This lookup index is a
  convenience layer, not the real data. If it were ever lost, corrupted, or simply deleted, nothing
  about the actual saved market data is at risk — the app can regenerate the entire index by
  scanning what it has already saved. This was verified directly: the index was deleted and rebuilt
  successfully, reproducing the exact same lookups as before.

---

## Changed Behavior

- **Fetching the exact same symbol/timeframe/date-range window a second time**: Previously, this
  went out to Yahoo Finance again and — because the app refuses to save the exact same data
  twice — came back with a "this already exists" conflict message. Now the second request is
  recognized immediately as something already on file and is simply handed back, instantly, with no
  network call and no conflict message. (Two *different* requests that happen to fetch identical
  content are still refused as a conflict — that underlying protection has not changed at all, only
  the everyday case of "I asked for this again" now behaves sensibly.)
- **Listing recorded bar data**: Previously, the listing endpoint only supported "give me
  everything." It now optionally supports "give me only this symbol" and/or "give me only this
  timeframe," while "give me everything" continues to work byte-for-byte exactly as it did before —
  this was directly verified by comparing the two response paths.

---

## Backend-Only Items

- Both of the above are available today through the app's data API (and the same programmatic
  interface AI agents use) — there is still no on-screen control for any of it. Nobody can click a
  button in the app and see this speed-up or use the symbol/timeframe filter yet; that lands when a
  future iteration adds the fetch control to the Structure page. This was also true for the
  underlying fetch capability in the two prior iterations and remains true here.

---

## Incomplete Items

- None from this iteration's plan — the plan scoped this iteration to the instant-reuse lookup, the
  symbol/timeframe filter, and the rebuild-from-scratch safety net, and all three were completed and
  verified, including against real previously-recorded data on the live running app (not only
  simulated tests).

---

## Config and Environment Changes

- One new, entirely optional environment variable: `TAPEOLOGY_BAR_INDEX_DB`. Nobody needs to set
  this — by default, the app automatically places its new lookup index right next to where it
  already stores bar data. The variable exists only so an operator or a test can point the lookup
  index somewhere else if they ever specifically need to.
- No other settings changed. The project's central configuration file was left completely
  untouched by this iteration, and a built-in check re-confirmed that every research value the app
  computes elsewhere (support/resistance levels, backtests, and everything else) is still computed
  exactly as it was in the prior two iterations.

---

## Known Limitations

- **Data recorded before this iteration won't show up in the new symbol/timeframe search until it's
  re-indexed once.** The lookup index only learns about a piece of data at the moment it's freshly
  fetched from now on — it doesn't automatically go back and learn about everything fetched in the
  past. This is intentional (the feature is designed to update only when something new happens, not
  run background jobs), but it does mean that data already sitting in the app from earlier testing
  needed a one-time "learn what you already have" pass before the new search feature could find it.
  That one-time pass was already run as part of verifying this feature works, so the app's current
  real data is fully searchable right now — a future deployment that starts fresh, or that
  accumulates more fetches going forward, will index everything automatically without needing this
  step repeated.
- **The developer helper script that starts up the app for testing (`scripts/dev.sh`) doesn't always
  fully clean up every background process it starts when stopped.** This was noticed while
  double-checking the app starts up correctly, but it is a pre-existing quirk in that startup helper
  script itself — nothing this iteration's actual feature work touched or introduced. Worth a look
  in a future cleanup pass, but does not affect anything described above.
- There is still no on-screen way to try any of this — that remains planned for a future iteration
  that adds a fetch button to the Structure page, exactly as noted in the prior iteration's summary.
