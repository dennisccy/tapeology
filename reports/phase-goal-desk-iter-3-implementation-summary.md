# goal-desk-iter-3 — Implementation Summary

**Phase:** goal-desk-iter-3
**Date:** 2026-07-25
**Written by:** developer

---

## Features Implemented

- **The screen (backend + command line only, no page yet)**: the desk can now run a "screen" — one
  pass over the last registered list of S&P 100 names, as of a chosen date, that summarizes what
  the tradable-map wall calculation already says about each name (closest band, its grade, how far
  it sits from the last close, its score) into one ranked list. A name with no bars on file is
  reported as an honest "skipped" entry rather than guessed at. This is triggered by a command
  (`POST /research/desk/screen/compute` or the new command-line tool), not automatically.
- **The screen never repeats or overwrites itself**: every screen run is pinned to its exact inputs
  (the date, the universe list used, the app's setting fingerprint, and a summary of what bars were
  on file at the time). Running the identical request again returns the SAME saved result rather
  than writing a second copy — the record is permanent once written.
- **Live progress and cancel**: a screen run reports progress (how many of the ~100 names are done)
  and can be cancelled mid-run through the same command. Only one screen run can be in flight at a
  time.
- **Reading results back**: a new read endpoint lists past screen runs (lightweight summaries only,
  never the full ~100-row content for every past run in one response — that would be slow) and can
  fetch one specific date's full result, or the most recent one, exactly as it was recorded.

## Changed Behavior

- None. Every existing page, endpoint, and command from prior iterations works exactly as before —
  confirmed by re-running the full automated test suite (now 1297 checks, up from 1240, with zero
  failures) and by comparing the source code for every file that serves an existing page or
  endpoint (zero changes detected on any of them).

## Backend-Only Items

- **The screen itself** — `POST /research/desk/screen/compute` (run it), `GET
  /research/desk/screen` (read past runs), and a command-line tool
  (`python -m app.research.desk_screen_compute --date YYYY-MM-DD`) — has no page yet. An operator
  can run and read a screen today only through the command line or a direct API call (e.g. from
  Claude via the terminal, or `curl`). The `/desk` page that will show this on-screen, with a "Run
  Screen" button, comes in the next iteration.

## Incomplete Items

- **Nothing from this iteration's own scope is incomplete.** The whole capability described above
  (run a screen, read it back, cancel it, deterministic append-only records) is fully built and
  tested against real data (a real, live-fetched Microsoft bar history was added for testing
  purposes, alongside the Apple history already on file from a prior iteration).
- **A real, full ~100-name screen run over live market data has not been executed.** That is by
  design — this iteration proves the capability works correctly on realistic test data; running it
  for real over all ~100 names is a deliberate, separate operator action for later (the same way
  "fetch the real company list" and "download real bar history for every name" were separate
  operator actions in the two prior iterations). A short, safe live check against the real backend
  (start it, trigger a screen, watch it begin working on real names, then cancel) confirms the
  machinery is wired correctly end to end.

## Config and Environment Changes

- **No new settings that affect any stored result.** One new, optional environment variable,
  `TAPEOLOGY_DESK_SCREEN_DIR`, lets an operator choose where screen records are saved on disk (the
  same style as similar existing variables for bars and datasets); if unset, records are saved next
  to the existing universe-list folder. This variable has no effect on what any screen actually
  says — only where its files live.

## Known Limitations

- **The very first name checked in a real screen run can take several seconds** (this is normal
  "warming up" behavior already seen elsewhere in the app, e.g. when the Structure page loads for
  the first time after a restart, and is expected to warm the bar-file cache for every name at
  once, not just the first one — but this was not directly timed past the first name). A full real
  run over ~100 names has not been timed end to end; that measurement is left for the operator's
  own real run.
- **No filter to screen just one or a few names from the command line yet** — the command line tool
  always screens the full current list. Not needed for anything asked of this iteration; easy to
  add later if wanted.
- This iteration deliberately touches nothing about how bands, levels, or scores are calculated —
  it only reads those existing calculations and organizes them into a ranked list. Nothing about
  the trading-wall math itself changed.
