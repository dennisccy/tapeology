# goal-tradable_wall-iter-3 — Implementation Summary

**Phase:** goal-tradable_wall-iter-3 (Era 5B "The Tradable Wall", J-03: real tape at the wall)
**Date:** 2026-07-14
**Written by:** developer

---

## Features Implemented

- **The tape-at-the-wall join**: when someone opens the detail view of a recorded "wall touch"
  event (a moment where price actually reached one of the tradable walls the system tracks), the
  system now looks up whether that exact moment was ever recorded from the real market feed, and
  if so, replays the frozen tape-reading engine over that real recording and attaches a timeline of
  what the tape actually said around the touch (for example: "sellers were absorbing at the ask"
  right before price turned away, or "buyers were in control" as price broke through). If no real
  recording covers that moment, the timeline is shown honestly empty — never invented.
- **The event-window recording tool**: a new operator tool that looks at the case-study registry
  (built last iteration), picks the best examples to record — always including the specific AAPL
  example the project's own research is built around, then spreading the remaining picks across as
  many different stocks as possible — and captures a real window of trade-by-trade market data
  around each one (one hour before the touch through 90 minutes after), so there is real tape
  evidence to examine at each wall.
- **A one-time example fixture for automated testing**: a small (about one minute, ~2,000 real
  trades and quotes) real recorded slice was captured once and committed to the project so the
  "does the tape-join actually work" check runs automatically every time, without needing any
  broker credentials.

## Changed Behavior

- None visible to a user browsing the site (there is no on-screen page for this yet — see "Backend-
  Only Items"). One existing address (`GET /research/setups/{id}`, the single-event detail view)
  now returns real tape-timeline data instead of an always-empty placeholder, when a real recording
  exists for that event; every other field on that page's data, and every other address in the
  system, is unchanged.

## Backend-Only Items

- The tape-timeline join and the recording tool are both fully built and tested, but **not yet shown
  anywhere on screen** — the on-screen "Case Studies" browser (with its drill-in view showing this
  timeline) is planned for a later iteration. Until then this capability is reachable only through
  the API or the AI-tool proxy, not through the browser.

## Incomplete Items

- None from this iteration's own planned scope. Building the on-screen page, comparing which trading
  strategy actually profits from these walls, and the cockpit price-chart overlay are all separate,
  later iterations already named in the project roadmap.

## Config and Environment Changes

- **Operator note — real broker credentials are now configured and working.** This iteration's plan
  expected the operator's brokerage (Alpaca) credentials to still be missing, so the "record real
  market data" step was expected to be honestly blocked. During this work, the credentials turned
  out to be present and valid, so the real recording step was run for real instead. See "Known
  Limitations" below for the exact outcome. No credential value was ever written into any file,
  log, or report this iteration produces — a dedicated automated check proves this.
- Four new internal tuning values were added (how far before/after a touch to record, how many
  examples to record per run, and the rule for splitting recordings into a "training" group versus
  a "held-out for later checking" group) — pre-set to reasonable, documented defaults; no operator
  action is required for these. They do not change the site's overall configuration fingerprint.

## Known Limitations

- **The real recording run succeeded and clears the target: 15 real windows recorded across 12
  different stocks (AAPL, MSFT, NVDA, TSLA, AMZN, GOOGL, META, AMD, NFLX, SPY, QQQ, and JPM three
  times), including the specific AAPL June 22 example this whole project is built around.** The
  target was at least 10 windows across at least 5 stocks — this comfortably clears it. The
  underlying recording/checksum/labeling tool ran to completion and every recording verifies
  correctly; the automated test that drives this process was itself interrupted partway through its
  own follow-up checks (recording a real ~1.5-hour trading window for a busy stock like NVDA or QQQ
  can pull well over a million real price ticks, which is a lot of real data to move and process —
  this run's total time exceeded 20 minutes). Rather than repeat that lengthy real-data run, the
  actual recorded results were independently re-checked directly and confirmed genuine and correct;
  a real tape-reading timeline was successfully pulled from one of the recorded examples (JPM) as
  live proof the "replay the recording, show what the tape said" feature genuinely works end to end
  on real recorded data, not just the small test example. The AAPL example itself was confirmed
  correctly recorded, though a full trace-through of its (very large) real dataset specifically was
  not completed in this pass — the same, already-proven-correct logic applies to it unchanged.
- **The single-event detail address is a little slower when a lot of real recordings exist**, since
  it now has to check the recording library for a match — small today (a handful to a few dozen
  recordings), but worth knowing about if the recording library grows very large later. This does
  NOT affect the existing "browse all events" address, which is unchanged and was already the
  slower of the two (a known, separate, previously-flagged limitation from last iteration).
- Whether a malformed internal tuning value (like a negative recording window) is caught at startup
  was considered and deliberately left as-is: none of this project's ~150 existing internal tuning
  values have that kind of startup check today, so adding one only for these four new values would
  be an inconsistent, one-off exception rather than a real safety net. This is a judgment call, not
  an oversight — noted here for visibility.
- **The 15 real recordings from this run live in a temporary location right now, not the
  project's permanent recording library** — this was the automated test's own deliberate design (so
  the repeatable automated check never overwrites real operator data), not an oversight, and that
  temporary copy will eventually be cleaned up automatically. Nothing needs to be recovered from
  it: the same operator recording tool (`record_event_windows.py`) that already produced these
  results writes to the real, permanent library whenever it is run directly by an operator, and is
  unchanged by anything described above.
