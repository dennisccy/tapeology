# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-18 — Implementation Summary

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-18
**Date:** 2026-06-12
**Written by:** developer

---

## Features Implemented

- **Replay studies (the new Studies page)**: From a new, nav-enabled Studies page the user can run a
  "study" — a replay of the system's setup grammar over a chosen past window — and read how the setups
  would have played out, side-by-side with a fair "random-time baseline" over the same window.
- **Three ways to choose what to replay**: a one-click committed reference window (a real ~10-minute
  Procter & Gamble market capture that needs no credentials), any of the built-in simulated scenarios,
  or an arbitrary real symbol + past date/time window (needs market-data credentials).
- **Honest, side-by-side results**: for each study the page shows, per time horizon (10/30/60/120
  seconds), how often the setup's occurrences reached +1R first, −1R first, or neither — beside the same
  counts for the random-time baseline. Horizons cut short by the window end are counted separately as
  "truncated", never blended into the results.
- **Reproducible**: the same window + settings always produces the exact same numbers. The random
  baseline uses a recorded seed, so it reproduces exactly too. Re-running an identical study gives
  identical results.
- **Cancellable background jobs**: a study runs in the background (the live cockpit is never blocked) and
  shows a status of Queued → Running → Done. The user can Cancel a running study; it then shows as
  Cancelled with any partial results clearly marked partial. A study that can't run (no data, missing
  credentials) shows an explicit Failed with the reason — never a blank "success".
- **A committed reference study that reproduces in CI**: an automated test pins the exact numbers from
  the reference window (and a simulated scenario) so the result is verified on every build without
  credentials.

---

## Changed Behavior

- **The top navigation's "Studies" link is now enabled.** Previously it was a greyed-out "coming soon"
  item; now it opens the Studies page. Nothing else in the existing cockpit or journal changed.

---

## Backend-Only Items

- None. Every new backend capability (create / list / read / cancel a study) is wired to the new Studies
  page.

---

## Incomplete Items

- **Arbitrary real-symbol windows were not verified against the live vendor here** (no credentials in this
  environment). The committed reference window and the simulated scenarios are fully verified in CI
  without credentials; the arbitrary-window path reuses the exact same data-fetch the existing "watch a
  real symbol" flow already uses, and refuses explicitly (never fabricates data) when credentials are
  absent.

---

## Config and Environment Changes

- `study_null_arm_count` — how many random-time baseline points are drawn — default: `100`
- `study_arm_sustain_seconds` — how long a setup's pattern must hold before an occurrence is counted — default: `5.0`
- `study_arm_cooldown_seconds` — minimum spacing between counted occurrences — default: `180.0`
- `study_occurrence_r_spread_multiple` — sets the synthetic risk distance ("R") for an occurrence, as a multiple of the spread — default: `10.0`
- `study_occurrence_r_floor` — a minimum risk distance when there is no usable spread — default: `0.05`
- `study_null_baseline_seed` — the recorded seed that makes the random baseline reproducible — default: `1729`
- `study_list_max` — how many studies the list shows (display-only) — default: `100`
- No database migration: the existing study tables (present since the first version of the journal
  database) absorb the new records. No schema change.

---

## Known Limitations

- A study runs in this server process; if the server restarts mid-study, that study is lost and a study
  left "Running" by the old process is shown honestly as Running (not silently completed).
- Arbitrary real-symbol studies need valid market-data credentials configured in the environment; without
  them the create action returns an explicit "provider unavailable" message rather than substituting any
  data.
- Results are deliberately framed as journaled measurements with their sample size and the random-time
  baseline always shown — they are never presented as a profit, edge, or win-rate claim.
