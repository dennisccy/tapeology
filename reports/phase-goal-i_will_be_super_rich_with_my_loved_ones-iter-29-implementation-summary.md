# Iteration 29 — Implementation Summary

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-29
**Date:** 2026-06-16
**Written by:** developer

---

## Features Implemented

This iteration added **no new feature**. It was a verification + evidence-capture pass that
proves two market-hours-gated behaviours work on a REAL live stock feed — behaviours that already
existed in the product but could only be demonstrated when the US market is open and live
credentials are configured. The market was open (Tuesday, mid-afternoon New York time) and the
credentials were present, so both were proven for the first time on a real feed.

- **Live "feed went quiet" honesty proven on a real feed (J-15)**: When watching a real stock
  live, the status indicator correctly shows "live", then automatically switches to "stale" when
  the real exchange feed goes quiet for more than ten seconds, then switches back to "live" the
  moment new market data arrives. Crucially, while the feed is quiet the app invents NO trades and
  shows NO made-up prices — the recent-trades count and the last data time stay frozen until real
  data resumes. This was observed repeatedly on a real Ford/IBM feed.
- **Live "which data feed am I on" label proven on a real feed (J-67)**: The live cockpit shows a
  badge reading "IEX (live)" with a plain-language note explaining that live reads the
  single-venue IEX feed while historical replay and studies use the fuller SIP feed (so prices and
  spreads differ). A live-declared thesis was recorded in the journal stamped with the "iex" feed,
  confirming live (IEX) and historical (SIP) records are never mixed together.

---

## Changed Behavior

- **None.** No existing behaviour changed. The application code is byte-for-byte identical to
  before this iteration (verified with a live source check). The product behaves exactly as it
  did; this pass simply captured the proof on a live market feed.

---

## Backend-Only Items

- **None.** Every value verified here is already shown in the UI: the live/stale status indicator,
  the IEX feed badge and its note, and the journal row's feed stamp.

---

## Incomplete Items

- **Browser pixel screenshots** of the live "stale" indicator, the live IEX badge, and the "iex"
  journal row are the next (browser-QA) step. The binding proof — the live data feed actually
  flipping live→stale→live with no invented data, and a real Alpaca live-socket test passing — is
  already captured at the data level and via the credentialed live integration test.

---

## Config and Environment Changes

- **None.** No new environment variable, config key, or setting was added.
- Operational note (not a change): to watch a live symbol, the backend must be started with the
  Alpaca credentials present in its environment (loaded from `apps/backend/.env`); the live-data
  adapter reads credentials from the environment only.

---

## Known Limitations

- **The "stale" indicator is brief on busy stocks.** On a heavily traded stock the feed rarely
  goes quiet for a full ten seconds, so the "stale" state can clear within a second or two.
  Watching a quieter stock or an off-peak minute produces longer, easier-to-capture quiet
  periods; this was used to observe repeated multi-second "stale" spans on a real feed.
- **The free IEX live feed can show a wide spread.** Because the live feed is a single venue
  (IEX), some stocks show a wide bid/ask and the tape honestly reads "unclear". This is correct
  behaviour, not a fault — the live label and note exist precisely to make that limitation
  explicit to the user.
- **No application code changed.** If a genuine live-feed defect had been found it would have been
  fixed in place on the existing owner module; none was found, so the application is unchanged.
