# goal-fast_wall-iter-4 — Implementation Summary

**Phase:** goal-fast_wall-iter-4
**Date:** 2026-07-17
**Written by:** developer

---

## Features Implemented

- **A "Compute edge report" button now exists on `/structure`.** Until this iteration, the page's
  Edge Report section could only ever say "not computed yet" — there was no way to actually run the
  full comparison from inside the app; the only way to warm it up was a developer running Python
  code by hand. Now there is a real button. Clicking it starts the full v1 / structure_tape /
  structure_tape_map comparison sweep as a background job, and the page watches it progress live —
  a small counter shows how many of the comparison's individual backtests have finished — until it
  either lands on the finished report or an honest failure message. The page never freezes and
  never needs a manual reload while this runs.
- **The compute only ever runs when someone explicitly asks for it.** Simply loading or refreshing
  `/structure` — or any other page, or any automated tool reading the data — still never starts the
  expensive sweep by itself. This was already true before this iteration (from the "Fast Wall"
  interlude's first piece of work) and stays true now; the button is the ONLY new way to start it,
  plus a matching command-line tool for running it unattended from a terminal (see below).
- **A companion command-line tool for running the sweep without the browser.** An operator can now
  run `python -m app.research.edge_report_compute` from a terminal to run the same compute directly
  — useful for kicking it off in the background and letting it run for a while, or for scripting.
  It prints its own progress as it goes and, once finished, the exact same warmed-up result is what
  the "Compute edge report" button and the page's report section will show — they share one
  computation, one storage location.
- **Only one compute can run at a time.** If someone clicks the button while a compute is already
  running (from an earlier click, or from the command-line tool), nothing new starts — the page
  simply keeps watching the ALREADY-running one. This prevents two overlapping runs from fighting
  over the machine's CPU.
- **A running compute can be told to stop, and stopping is clean.** If a compute is cancelled
  partway through, nothing half-finished is ever saved — the next time anyone looks at the report,
  it is still honestly "not computed yet," never a partial or misleading result.
- **A failure is never hidden or generic.** If something goes wrong mid-compute (for example, a
  corrupted data file), the page shows the actual error message from the backend, not a vague
  "something went wrong."

---

## Changed Behavior

- **The "not computed yet" panel on `/structure`'s Edge Report section**: previously a static
  message with nothing to click. Now the SAME message still appears exactly as before on a page
  that has never had a compute run, but a button now sits beneath it. Nothing about the existing
  message's wording changed.
- **The already-existing report display**: unchanged. Once a compute finishes, the same table/cell
  layout that already existed (from an earlier iteration) takes over — this iteration adds no new
  way of displaying the finished numbers, only a new way of REACHING them.

---

## Backend-Only Items

None — every backend piece added this iteration (the background-job manager, its three new web
addresses, and the command-line tool) has a corresponding, working piece on the `/structure` page:
the button, the live progress line, and the finished/failed outcomes.

One small piece exists but is not yet exposed as a button: the ability to CANCEL a running compute
has a working web address and was tested directly, but no cancel button was added to the page this
iteration — the plan for this iteration only called for a "start" button, not a "stop" button.

---

## Incomplete Items

None from this iteration's own scope — every piece the plan called for (the background-job
manager, the three new web addresses, the command-line tool, and the button/progress/failure
display on `/structure`) was built and automatically tested.

One verification gap, explained fully below under Known Limitations: this iteration's own visual,
click-through browser check could not be completed due to a technical problem with the browser
automation tool in this working session — the button was verified to work correctly through direct
web requests (the same requests the button itself makes), but not through an actual screenshot of
someone clicking it.

Reminder of what's intentionally still out of scope (planned for later iterations):
- Making the sweep resumable (so a stopped or interrupted run doesn't have to start over) and able
  to use multiple CPU cores at once, to make the FIRST real run — over the full recorded market
  data — finish in minutes instead of never finishing at all.
- A separate speed-up for the "which trading setups exist" scan (a different, unrelated slow spot).

---

## Config and Environment Changes

None. No new settings, no new environment variables, no database schema changes. The app's internal
"fingerprint" — the number that guarantees identical requests always produce identical results —
was directly checked before and after this work and confirmed unchanged. The command-line tool
accepts an optional `--workers` number (for a future speed-up not yet built) and an optional
`--force` flag (to recompute even when a saved result already exists) — neither requires any new
configuration.

---

## Known Limitations

- **This iteration's browser click-through could not be captured as a screenshot.** The automated
  browser-control tool used for visual verification repeatedly failed to start in this particular
  working session (a Chrome browser problem specific to this session's setup, not something wrong
  with the feature itself — a manually-started browser on the same machine worked fine). As a
  substitute, the developer verified the exact same sequence of web requests the button makes,
  directly, against a real running copy of the app (not a simulation) — start the compute, watch it
  progress, see it finish, see it fail on a deliberately broken test file, all producing the exact
  responses the page's code expects. This is strong evidence the feature works, but it is not the
  same as an actual screenshot of the button being clicked in a browser, and that gap should be
  closed by whoever runs the browser-based check next.
- **The demonstration data used for this iteration's live check has nothing to compare.** The one
  small practice dataset available in this scoped check doesn't happen to line up with any of the
  app's tracked price levels, so the compute finished almost instantly with an honest "nothing to
  report" result rather than visibly counting up through several backtests one by one. The
  counting-up behavior itself IS proven — just through the automated test suite's own practice
  data, not through this iteration's live browser-adjacent check.
- This project's shared configuration file (used to tell automated agents what commands to run) is
  currently in its blank, unfilled template state rather than carrying this project's actual values
  — a pre-existing gap unrelated to this iteration's work, already noted in prior iterations'
  summaries.
