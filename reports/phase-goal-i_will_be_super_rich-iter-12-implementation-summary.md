# Phase iter-12 — Implementation Summary

**Phase:** goal-i_will_be_super_rich-iter-12
**Date:** 2026-06-08
**Written by:** developer

---

## Features Implemented

- **Real clock time on the price chart**: The price chart's time axis, the crosshair you hover, and
  the tape-state markers now show the actual clock time of each candle — formatted as
  `dd-MM-yyyy HH:mm:ss` in your local time zone — instead of a counter that just climbed from 0 to
  600 seconds. For a replayed real session it shows the real market time; for a simulated scenario it
  shows a synthetic session clock starting at 09:30 (US market open). Switching the bar size between
  10, 30, and 60 seconds keeps the real-time axis.
- **One consistent date format across the whole app**: Every date the app displays now reads
  `dd-MM-yyyy` (dates) or `dd-MM-yyyy HH:mm` / `HH:mm:ss` (date-times), produced by a single shared
  formatter. This covers the chart axis, the live market-status "next open" time, the closed-market
  panel, and the "what am I watching" descriptor at the top.
- **A `dd-MM-yyyy` date field for historical replay**: The historical date picker now uses a typed
  `dd-MM-yyyy` field instead of the browser's built-in date picker (whose format varied by locale).
  If you type an impossible or malformed date (for example 31-02-2026), the app shows an inline
  message and outlines the field — it never quietly ignores the click.

---

## Changed Behavior

- **Price-chart time axis**: Previously labeled with elapsed playback seconds (0…600). Now labeled
  with true clock time (`dd-MM-yyyy HH:mm:ss`, local zone).
- **Date display in the market-status and closed-market panels**: Previously showed a "Jun 8"-style
  locale date. Now shows `dd-MM-yyyy HH:mm` with the local UTC-offset label.
- **Watched-source descriptor**: For a historical watch it previously showed raw machine timestamps
  (e.g. `2024-05-14T13:30:00.000Z`). Now shows the friendly `14-05-2024 13:30` form.
- **Historical date entry**: Previously the native browser date picker. Now a typed `dd-MM-yyyy`
  field — but it resolves to exactly the same point in time as before (no time-zone shift), so a
  window you pick is still fetched for the exact local instant you chose.

---

## Backend-Only Items

- A new read-only value, the **display/epoch anchor**, is now included in the chart's history
  response (`GET /tape/{ticker}/history`). It is the real clock time that the chart's internal
  timeline starts from. It is fully wired to the chart UI — there is no un-surfaced backend work.

---

## Incomplete Items

- None deferred from this iteration's scope. (The separate refinement journeys J-32 live replay-speed
  changes, J-33 real-data classification calibration, and J-34 chunked long-window loading remain for
  later iterations, as planned.)

---

## Config and Environment Changes

- `sim_session_anchor_epoch` (backend config) — the fixed synthetic session-start used as the chart's
  clock anchor for simulated data. Default: `1704205800.0` (2024-01-02 09:30 US Eastern). No
  environment variable; no new credential; no database change.

---

## Known Limitations

- **Confirming the real-market historical axis on screen needs vendor credentials.** Replaying a real
  symbol over a past window (to see real market times on the axis) requires Alpaca API credentials.
  Without them, the simulated session-clock axis is fully checkable, and the real-historical anchor is
  proven by an automated backend test against a recorded data fixture.
- **The chart's on-screen time labels should be confirmed with a real screenshot.** The clock-time
  axis is produced by the charting library using formatter callbacks that the build type-checks and
  that backend data confirms; per the project's visual-journey practice, a real rendered screenshot of
  the populated chart should still be captured during browser QA to confirm the labels visually.
- **Trade/event rows show no date column today**, so there was no non-conforming date to convert there.
  If a future iteration adds a timestamp to those rows, it must use the same shared `dd-MM-yyyy`
  formatter.
