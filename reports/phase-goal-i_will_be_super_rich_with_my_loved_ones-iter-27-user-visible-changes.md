# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-27 — User-Visible Changes

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-27
**Date:** 2026-06-13
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

None. This was a verification-only iteration. No new user capability was added. The product
surface as seen by the user is byte-identical to what was shipped in iteration 26.

---

## What Changed in the Visible UI

None. Zero frontend source files were changed. Every existing cockpit component (panel grid,
candlestick chart, recent-trades list, honest-state panels, error banner, stream-status dot,
feed-basis badge, replay-speed control, source selector, date input, time-window picker) is
unchanged in code and unchanged in behavior.

---

## What Old Behavior Changed

None. No existing feature works differently. The full backend test suite (848 passed, 1 skipped)
passes identically to the previous iteration. All cockpit projections still read from the same
canonical endpoints (`/history`, `/state`, `/features`, `/summary`) with no code changes.

---

## Not Visible Yet

None arising from this iteration. The surfaces listed below remain deferred from earlier
iterations pending live market hours (next US open: Monday 2026-06-15 14:30 UTC+01:00):

- **J-15** — live-feed-gap stale-to-recover state in the stream-status dot (requires live market hours).
- **J-67 live-IEX badge pixels** — the feed-basis badge rendered over a live IEX feed + the
  live-declared `iex`-stamped journal row (requires live market hours; J-67 remains `passing`
  on non-live evidence and was NOT re-opened).
