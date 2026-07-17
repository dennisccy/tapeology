# Goal Iteration 5 — Implementation Summary

**Phase:** goal-fast_wall-iter-5
**Date:** 2026-07-17
**Written by:** developer

---

## Features Implemented

- **A durable "already computed" memory for individual backtests**: the edge-report sweep (the
  compute behind the "Compute edge report" button on `/structure`, and the `python -m
  app.research.edge_report_compute` command-line warmer) now remembers each individual
  (dataset, strategy) result it has already computed, in a small database file on disk. If the
  sweep is stopped partway through and started again, it skips everything it already finished and
  only computes what's left — instead of starting over from zero every time.
- **A genuinely faster command-line warmer**: the command-line warmer can now spread its work
  across multiple CPU cores at once (`--workers N`), which actually runs the backtests in
  parallel rather than accepting the flag and silently ignoring it (as it did last iteration).
  This only applies to the command-line tool — the on-page button still runs one thing at a time,
  by design (see Known Limitations).
- **A verified browser walkthrough of last iteration's button**: last iteration built the
  "Compute edge report" button, the progress line, and the failure/retry states, but a technical
  problem with the testing tool meant nobody had actually watched it work in a browser yet. This
  iteration that problem was resolved, and the full click-through was watched and screenshotted
  end to end: clicking the button, watching the live progress counter, seeing the finished result
  appear, and seeing a failure message render correctly when something goes wrong.

---

## Changed Behavior

- **The command-line warmer's `--workers` flag**: Previously accepted the flag but always ran
  every backtest one at a time regardless of what number you gave it. Now a value greater than 1
  genuinely splits the work across that many separate worker processes.
- **Interrupting and re-running the compute (button or command line)**: Previously, if the sweep
  was interrupted (killed, crashed, or the server restarted mid-sweep), re-running it recomputed
  everything from scratch, including work that had already finished. Now it picks up where it
  left off, skipping already-finished work.

---

## Backend-Only Items

- The "run this in parallel across N processes" capability is available ONLY through the
  command-line warmer, not through the on-page button. This was a deliberate choice (documented
  in the plan) to keep multi-process work out of the always-running web server — it's the kind of
  thing that's easy to add safely to a one-shot command-line tool but risky to add to a server
  that's also serving other pages at the same time. A future iteration could extend it to the
  button if genuinely needed.

---

## Incomplete Items

None from this iteration's plan — every item in the plan's scope was completed and verified
(automated tests plus a live browser walkthrough).

Two items were explicitly OUT OF SCOPE for this iteration per the plan, not incomplete:
- Running the command-line warmer against the full real trading-data corpus (as opposed to small
  test fixtures) to produce the very first complete real edge report — this remains an
  operator-run action for whenever there's a good moment for a multi-CPU sweep to run.
- Wiring the multi-process speedup into the on-page button — deliberately deferred (see
  Backend-Only Items above).

---

## Config and Environment Changes

- `TAPEOLOGY_EDGE_SWEEP_CACHE_DB` — where the new "remember which backtests are already done"
  database file lives. Default: a file named `edge_report_backtests.db` sitting next to wherever
  the dataset folder already lives — no setup needed unless you want to point it somewhere custom.
- `TAPEOLOGY_EDGE_SWEEP_WORKERS` — how many worker processes the command-line warmer uses by
  default when `--workers` isn't explicitly passed. Default: 4 if not set.
- No database migrations — the new memory file is created automatically the first time it's
  needed, and deleting it is always safe (the next run just recomputes and rebuilds it).

---

## Known Limitations

- The multi-process speedup is command-line-only this iteration (see Backend-Only Items) — the
  button-triggered compute still runs one backtest at a time, just with the new "don't redo
  finished work" memory.
- The full real-data run (the one that would actually take the sweep from "essentially never
  finishes" to "minutes") was not run as part of this iteration's work — it's still an
  operator-run action, same as before. This iteration makes that eventual run faster and safer to
  interrupt/retry; it doesn't run it.
- While testing the failure-message screen, it became clear that a permanently broken data file
  produces a slightly different (and equally correct) error screen than a temporarily-broken one
  that gets fixed before the page is viewed again. Both are honest, both show the real problem —
  this is just a note for whoever writes the next round of click-through test instructions, so
  they arrange the right one on purpose.
