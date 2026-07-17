# goal-fast_wall-iter-2 — Implementation Summary

**Phase:** goal-fast_wall-iter-2
**Date:** 2026-07-17
**Written by:** developer

---

## Features Implemented

- **The app stops re-reading unchanged files on every request.** Two of the app's storage
  modules — the historical dataset store and the OHLC bar store — now remember, in memory, that a
  given file was already checked and found healthy, as long as that exact file hasn't changed on
  disk since. The next request for the same data is answered instantly instead of re-reading,
  re-parsing, and re-verifying the file from scratch.
- **That memory survives a server restart.** In addition to the in-memory shortcut, the dataset
  store now also keeps a small, durable side-file (`dataset_index.db`) recording which files it
  has already verified. If the backend process restarts (a deploy, a crash, a manual bounce), the
  very next request can still skip the expensive re-read — it doesn't have to start over.
- **Nothing about safety changed.** Every one of these shortcuts is a "remembered answer to a
  question already asked," never a new source of truth. If a file's content ever changes on disk —
  including a tampered or corrupted file — the app notices immediately (via the file's size and
  modification time) and re-checks it from scratch, exactly as before. A corrupted file is still
  reported as an error, never silently served as good data, and never silently cached as bad data
  either.
- **Measured on the real data on this machine**: the "list all datasets" request dropped from
  about **29 seconds** (cold, first request) to **effectively instant** (warm, and also
  instant again immediately after a real backend restart) — matching the interlude's stated goal
  of taking the ~31-second cold cost down to sub-second once warm, restart included.

---

## Changed Behavior

- **`GET /research/datasets`** (and every other place that reads dataset or bar-series metadata,
  including the `/structure` page's Edge Report lookup from last iteration): previously re-read
  and re-verified every file on every single call, no matter how many times in a row it was asked.
  Now, the first call after a file changes (or the first call ever) still does the full check; every
  subsequent call for unchanged content is served from memory (or from the durable side-file after
  a restart) with no file reading at all. The data returned is byte-for-byte identical either way —
  this is a speed change only, not a data or behavior change.
- No visible page, button, or screen changed. This iteration is entirely "under the hood."

---

## Backend-Only Items

- The stat-keyed in-memory caches and the new `dataset_index.db` durable index are backend
  plumbing only — there is nothing to click or see. Every existing page that already reads dataset
  or bar data (Structure, Studies) automatically gets faster once its underlying files are warm or
  the restart-surviving index is populated; no new UI wiring was needed or added.

---

## Incomplete Items

None from this iteration's scope. All items in the plan (the two in-memory caches, the durable
dataset index, the route wiring, and the test-only reset safety net) were completed and verified.

Reminder of what's intentionally still out of scope (per the plan, for later iterations):
- The "operator-run compute" button and background job on the `/structure` page (a later
  iteration).
- Making the backtests sweep itself resumable/parallel (a later iteration).
- The setups-scan durable cache (a later iteration — it depends on plumbing this iteration added,
  but was not itself built here).

---

## Config and Environment Changes

- `TAPEOLOGY_DATASET_INDEX_DB` — optional environment variable pointing at where the new durable
  dataset-metadata index file should live. If not set, it defaults to a file sitting next to the
  existing dataset folder (e.g. `.data/dataset_index.db`). This mirrors how the existing
  `TAPEOLOGY_BAR_INDEX_DB` variable already works for a similar existing feature.
- No database migration needed — this is a plain SQLite file that gets created automatically the
  first time it's needed, and rebuilds itself automatically (losing nothing) if it's ever deleted.
- No changes to any existing setting. The one internal fingerprint the app uses to guarantee
  research results never silently change (`config_fingerprint`) was verified unchanged before and
  after this work.

---

## Known Limitations

- This iteration's speed win is specific to the "list/read metadata" requests. It does not touch
  (and was explicitly told not to touch) the deeper verification the app does when it actually
  replays a dataset's full trade history for research — that always re-checks everything, every
  time, on purpose, so research results can never be silently served from a stale cache.
- The very first request after a fresh install (or after someone manually deletes the new
  `dataset_index.db` file) still pays the full, slower cost once — this is expected and intentional
  (the whole point is that nothing is a hidden shortcut that could serve wrong data; if in doubt,
  it always re-checks). Confirmed on this machine's real data: about 29 seconds for that one-time
  cost, then instant afterward, including across a real restart.
- This project's shared configuration file (used to tell automated agents what commands to run)
  is currently in its blank, unfilled template state rather than carrying this project's actual
  values — a pre-existing gap unrelated to this iteration's work, noted so it can be fixed later.
