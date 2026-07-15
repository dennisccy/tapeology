# goal-tradable_wall-iter-8 — Implementation Summary

**Phase:** goal-tradable_wall-iter-8
**Date:** 2026-07-15
**Written by:** developer

---

## Features Implemented

- **No new feature.** This iteration is cleanup + verification only — it closes two small findings
  left over from iter-7's audit and confirms that your real recorded market data (the credentialed
  recordings you made) is now actually showing up correctly in the app, without needing to touch any
  of the app's core logic.

## Changed Behavior

- **The price chart no longer briefly flashes the wrong day's bands.** On the main `/` cockpit
  screen, when you switch which stock you're watching (or start a historical replay), there used to
  be a very brief moment — a fraction of a second — where the chart could ask the server for
  "today's" tradable bands instead of the bands for the actual day being replayed, before correcting
  itself. That brief wrong-day request no longer happens at all; the chart now waits until it
  genuinely knows which day it's showing before asking for bands.
- **Case Studies and Edge Report now have real data behind them.** Two sections of the `/structure`
  page — the "Case Studies" drill-in (which shows what the tape did at a specific price wall) and
  the "Edge Report" (which shows whether any strategy actually made money, measured honestly) — were
  previously empty or showed placeholder/synthetic data because no real recorded market data existed
  yet. Now that you've recorded real trade/quote data for 11 windows across 10 different stocks, I
  confirmed directly against the running server that:
  - The pinned example case (AAPL, June 22 2026, the ~$300 price wall) now shows the **real,
    second-by-second tape reading** during that window — 426 individual readings — instead of the
    "No recorded tape for this event" placeholder.
  - All 11 of your recorded windows are correctly matched up with the price-wall events they were
    recorded around, which means the Edge Report has real data to measure once it finishes
    computing (see "Known Limitations" below for why I couldn't watch it finish this session).

## Backend-Only Items

None. Every value involved was already being served by endpoints built in earlier iterations; this
iteration only fixed a timing bug in how the chart asks for data, and confirmed (without changing
any code) that those existing endpoints correctly serve your real recorded data.

## Incomplete Items

- **I did not personally watch the Edge Report finish computing.** See "Known Limitations" below —
  it is a real, working computation, but it is slow enough (likely several hours with your current
  amount of recorded data) that I could not wait for it to finish inside this one work session. I
  independently confirmed the pieces it depends on are correct and will produce real, non-empty
  results once it's given enough time to run — I just did not personally watch the finished report.

## Config and Environment Changes

None. No new environment variable, no config file change, no migration, no new dependency.

---

## Known Limitations

- **The Edge Report can take a very long time to compute — likely several hours — the first time it
  runs against your current amount of recorded data.** This is not a new problem I introduced; it was
  already flagged in two earlier iterations (iter-3 and iter-4) as a known slowness in how the app
  replays your recorded trade/quote data through its tape-reading logic. What's new is that I
  measured it concretely this time: reading through just ONE of your 11 recorded windows (the AAPL
  one, about 555,000 individual trades and quotes) took about 13 minutes by itself. The Edge Report
  has to do this same kind of reading for every one of your 11 windows, three separate times each
  (once per trading strategy being compared) — so a full run is realistically several hours, not
  seconds or minutes. This is not a bug — the computation is correct, just slow — and fixing the
  speed would require adding a "remember the answer" cache (similar to one that already speeds up a
  different part of this app), which is more work than this small cleanup iteration was scoped to do.
  **If you open `/structure` and the Edge Report section takes a very long time to show anything,
  that is expected right now, not something broken.**
- **A small housekeeping bug was found (and worked around, not fixed) in the app's own start/stop
  script.** When you stop the app with the normal Stop-both-servers action, one of the two servers
  (the one serving the web page) doesn't always fully shut down — a leftover process can keep running
  in the background. This doesn't cause visible problems day-to-day (starting the app again correctly
  clears out the leftover process automatically), but if you ever notice the app's port seeming
  "stuck," this is a known, pre-existing cause, unrelated to this iteration's changes.
- **The automated test plan document that was prepared ahead of this work contained two small factual
  mistakes** (it described the tape-reading states with made-up names that don't match what the app
  actually uses, and it referenced the wrong kind of ID in one example command). I did not edit that
  document myself since it isn't part of my job this iteration, but I've flagged the specific
  mistakes so whoever reviews the work next isn't confused by them.
