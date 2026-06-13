# Iteration 27 — Implementation Summary

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-27
**Date:** 2026-06-13
**Written by:** developer

---

## Features Implemented

- **None — this was a verification iteration, not a feature iteration.** No new capability was
  added to the product. The work was to *prove with real data* that the real-data flows already
  built in earlier iterations actually behave correctly, and to capture that proof as evidence.
  The product code is unchanged (byte-for-byte identical) at the end of this iteration.

---

## Changed Behavior

- **None.** No existing functionality works differently. The full backend test suite still passes
  identically (848 passing, 1 skipped, which is the same skip as before — a test that only runs
  while the live US market is open).

---

## Backend-Only Items

- **None.** Nothing new was added in the backend. The only backend activity was running the
  existing test suite and running the existing real-data fetch against the live data vendor
  (Alpaca) to confirm it still returns real, correct data.

---

## What we proved (the actual deliverable of this iteration)

This iteration's "output" is confidence, captured as evidence:

- **The real-data credentials now work.** Earlier the data-vendor secret key was missing, which
  would have blocked all real-data verification. The operator has since added it, so the system
  can now pull real US-stock market data on demand. We confirmed this end-to-end.
- **Real historical replay returns real data.** We pulled a real past trading window for Apple
  (AAPL) — Friday 2026-06-12, the first two minutes of the trading day — and got 24,619 real
  trades and 21,034 real quotes back from the vendor. No fabricated or placeholder data.
- **Buy/sell sides are correctly resolved on real data.** Out of those 24,619 real trades, the
  engine correctly labelled 14,091 as buys and 10,527 as sells, with only **1** left as "unknown".
  This is the headline real-data quality goal: the recent-trades list is no longer dominated by
  "unknown" — it shows real buy/sell direction.
- **The "market is closed" message is real and correct.** Because today is Saturday, the live
  market clock honestly reports the market as closed and points to the next open: **Monday
  15-06-2026 at 14:30 (UK time / UTC+01:00).** The system does not pretend the market is open.
- **A fake ticker is honestly rejected.** Asking for a made-up symbol returns a clear
  "not a tradable symbol" result instead of inventing fake trades.

---

## Incomplete Items

- **Browser-screenshot captures** of the above (the actual on-screen pixels showing real values
  in the cockpit, the chart, the recent-trades side column, and the honest error panels) are
  produced by the separate browser-QA step of this same iteration, not by this development step.
  This development step proved the underlying data is real and correct so those screenshots will
  show real content, not empty panels.
- **Three live-market-only checks are intentionally deferred to a Monday iteration** (this is
  scheduled, not a failure):
  - J-15 — recovering from a gap in a *live* streaming feed (needs the live market open).
  - J-67's live "IEX" data-source badge shown over a *live* feed (off-hours the screen correctly
    shows "market is closed" instead, so the badge genuinely cannot appear yet).
  - Any live re-confirmation of journeys J-12 / J-25 / J-26 (already passing on non-live evidence).
  - Next US market open for all of these: **Monday 15-06-2026 14:30 UTC+01:00.**

---

## Config and Environment Changes

- **No code or config changes.**
- **Environment note (operator action already taken):** `apps/backend/.env` now contains both
  `ALPACA_API_KEY` and `ALPACA_API_SECRET`. Both are required for real-data modes to work. With
  both present, the system pulls real market data; with either missing, the real modes honestly
  report "provider unavailable" and never fabricate data. (Secrets are never committed to git.)

---

## Known Limitations

- Real historical data is the free SIP consolidated feed, which is available for data older than
  ~15 minutes — perfectly fine for replaying past windows (what this iteration verified), but the
  live-streaming and live-badge checks still need to be run during real US market hours on Monday.
- All real-data side-resolution measurements this iteration came from a single real Apple window;
  a second symbol (e.g. TSLA) or a second window can be checked the same way if more samples are
  wanted — the path is identical and already proven.
