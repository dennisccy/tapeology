# goal-tradable_wall-iter-9 — Implementation Summary

**Phase:** goal-tradable_wall-iter-9
**Date:** 2026-07-15
**Written by:** developer

---

## Features Implemented

- **A "remember the answer" cache for the Edge Report.** The Edge Report (the section of the
  `/structure` page that tells you whether any of the three trading strategies actually made money,
  measured honestly, over your recorded market data) has always been correct but very slow to
  compute — realistically several hours the first time it runs against your current recorded data
  (the same slowness flagged in the last two check-ins). This iteration adds machinery so that,
  **once you've waited for it to finish computing one time**, the app remembers the answer and
  serves it back instantly on every future visit to `/structure` or every future request — even
  after you restart the app entirely. Nothing about WHAT the report measures or HOW it's calculated
  changed; this only changes whether the app has to redo hours of work every single time someone
  looks at the page.
- **The report-remembering machinery is built and thoroughly tested, but has not yet been "warmed
  up" with your real data.** I deliberately did not trigger the real, several-hours-long computation
  this session (see "Incomplete Items" below) — that first real run is something you or a future
  session needs to kick off deliberately, once, when you're ready to let it run in the background.
  After that, every subsequent look at the Edge Report should be fast.
- **A way to permanently record the Edge Report's findings once they exist.** Added a one-command
  way (for a future session or for you directly) to take a finished Edge Report and permanently save
  its findings into the app's honesty ledger (the running record of "which strategy actually
  profited, measured honestly" that lives in `reports/pnl/pnl-history.md`). This machinery is built
  and tested, but — like the cache above — has not been used for real yet, because there's no
  finished real report to record.

## Changed Behavior

- **None visible today.** The `/structure` page's Edge Report section looks and behaves exactly the
  same as before. The only difference is what happens BEHIND the scenes the second time (and every
  time after that) someone requests it: instead of recomputing from scratch, the app now checks
  whether it already knows the answer first.

## Backend-Only Items

- **The "remember the answer" cache itself** — a piece of server-side plumbing with no visible UI of
  its own. You will never see or interact with it directly; you'll only notice its effect (a fast
  Edge Report instead of a slow one, once it's been warmed up once).
- **The one-command "save the findings permanently" tool** — this is a command-line tool for
  operator/technical use, not something reachable through the app's web pages.

## Incomplete Items

- **The real, several-hours-long first computation was intentionally NOT run this session.** I was
  specifically instructed not to trigger it (running it here risked tying up this entire work
  session for 10+ hours with no way to safely stop partway through and keep the progress). Instead,
  I built and thoroughly tested the "remembering" machinery itself using small practice data, proving
  it correctly remembers, correctly forgets and redoes the work if anything relevant changes, and
  never loses or corrupts an answer even if multiple requests arrive at the same busy moment. **The
  actual first real run — and the permanent recording of its findings — is the next deliberate
  action for you or a future session to take**, once you're ready to let the computation run in the
  background for however long it takes.

## Config and Environment Changes

- No new environment variable is required. One optional, technical override exists
  (`TAPEOLOGY_EDGE_REPORT_CACHE_DB`) for redirecting where the "remembered answer" file is stored on
  disk — you will not need to touch this under normal use; it defaults to sitting alongside the
  app's other internal data files.
- No database migration, no new external service, no new paid dependency.

---

## Known Limitations

- **The Edge Report is still slow the very first time someone waits for it to finish** — this
  iteration does not make the underlying computation itself any faster; it only makes sure that
  slowness only ever has to be paid once. If you (or anyone) open `/structure` before that first real
  run has ever completed, the Edge Report section will still show its honest "still loading" state
  for a long time, exactly as before.
- **The permanent record-keeping step (saving the finished report's findings into
  `reports/pnl/pnl-history.md`) has not happened yet**, because there is no finished real report to
  save yet. The committed record-keeping file itself is completely untouched by this iteration —
  every test I wrote specifically avoided it, writing only to disposable practice locations.
- **A small housekeeping bug in the app's own start/stop script, first noticed in the previous
  check-in, is still present** (one of the two servers doesn't always fully stop when you use the
  normal stop action — starting the app again automatically clears it out). This is unrelated to
  this iteration's work and outside what I was asked to fix this time.
