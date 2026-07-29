# Phase goal-desk-iter-14 — User-Visible Changes

**Phase:** goal-desk-iter-14
**Date:** 2026-07-28
**Written by:** ui-impact-analyst

---

## Summary

Journey **J-10** ships on the existing `/desk` page: the operator can now trigger a reconciliation of
the app's internal bar-coverage index against the real, frozen price-bar files on disk, watch it
repair itself live, and read a permanent record of exactly what was wrong before and what got fixed.
No new page and no navigation change — this is one new button and one new read-only history panel
added to `/desk`, sitting beside the existing "Top-up Runs" panel.

---

## What Users Can Now Do

- Click a new **"Reconcile Index"** button on `/desk` to repair the app's internal lookup table
  (the "index") of which price-bar files it has stored for each stock and timeframe, rebuilt
  directly from the real files on disk.
- Watch live progress while a reconciliation runs — the button reads "Reconciling…" with a
  pulsing-dot phase indicator (classifying → reindexing → verifying) — and cancel it mid-run with a
  "Cancel" button.
- See a permanent **"Index Reconciliation"** history panel on `/desk` (immediately after the
  existing "Top-up runs" panel) listing every reconciliation run ever recorded: its date, a run id,
  whether it finished / was cancelled / failed, how many price-bar series exist on disk, and how
  many rows were in the index before vs. after that run.
- See, for the most recent run specifically, the full before/after detail: every affected
  stock+timeframe pair, sorted into three honest, plainly-labeled categories — "series on disk, no
  index row," "index row, no file on disk," and "index row, file on disk fails its checksum" — plus
  any corrupted-file errors, shown verbatim and never summarized.
- Retry after a failed reconciliation via a "Retry Reconcile Index" button that replaces the normal
  one, with the failure's own error text shown alongside it.
- Trust that the small colored "coverage" badges next to each ranked stock on `/desk` (already
  shipped) can now be independently checked and corrected instead of just trusted — a badge that was
  stuck showing "no data" for a stock that genuinely has data on disk can be relit by running
  Reconcile Index and then a new screen.
- See an honest **"No reconciliation run recorded yet."** message before the very first
  reconciliation on a given backend, instead of a blank or broken-looking panel.

---

## What Changed in the Visible UI

- A new, always-rendered `<section aria-label="Index Reconciliation">` is now the LAST section on
  `/desk`, placed immediately after "Top-up runs" — present regardless of whether a screen has ever
  been computed, the same "independent of screen state" placement the Top-up Runs panel already
  uses.
- The controls panel previously titled **"Run Screen / Top-up"** is now titled **"Run Screen / Top-up
  / Reconcile Index"** (its enclosing section's `aria-label` similarly grew from "Run Screen and
  Top-up controls" to "Run Screen, Top-up and Reconcile Index controls") and now holds a third
  button. The pre-screen "not computed yet" panel gained the same third button beside "Run Screen"
  and "Top-up".
- The new Index Reconciliation panel's table lists one row per recorded run: date, run id, state,
  "series on disk," and "rows indexed (before → after)".
- Below the table, the latest run gets its own detail block: a "state / series on disk / rows
  indexed" summary line, a labeled "Drift before (`N`)" list, a labeled "Drift after (`M`)" list
  (each entry names the affected pair and which of the three categories it belongs to), and — only
  when present — a "Store errors (`N`)" list naming each corrupted file and its error text verbatim.
- The reconcile button now shows four distinct visible states: idle ("Reconcile Index"); running
  ("Reconciling…" + a phase-progress line + a "Cancel" button); failed ("Retry Reconcile Index" +
  red error text); cancelled (an amber note reading "Index reconciliation cancelled — the index was
  not repaired this run.").
- The same auto-refresh pattern the Top-up panel already uses is mirrored here: once a
  reconciliation reaches a terminal state, the Index Reconciliation panel refreshes itself within one
  poll tick (~700ms) with no manual page reload.

---

## What Old Behavior Changed

- **Coverage badges** (the small colored tags next to each ranked stock on `/desk`, shipped in an
  earlier iteration) render with the exact same component, colors, and logic as before — zero code
  change to that badge itself. What changed is what a user can now DO about a wrong one: previously,
  if the internal index fell out of sync with the real stored files, a badge could stay dark ("no
  data") indefinitely even when the real data was sitting on disk, with no way to fix it from the
  product. Now: running "Reconcile Index" and then a new "Run Screen" can relight that same badge —
  the badge itself is unchanged, but it is no longer a dead end.
- The controls panel titled "Run Screen / Top-up" is renamed to "Run Screen / Top-up / Reconcile
  Index" (see above). The existing "Run Screen" and "Top-up" buttons keep their exact prior labels,
  states, and behavior — nothing about them changed beyond gaining a new sibling button.

---

## Not Visible Yet

- **No command-line tool exists for triggering a reconciliation.** Unlike "Top-up" — reachable both
  from a `/desk` button and a separate CLI script — "Reconcile Index" is UI/API-only; there is no
  script an operator can run instead of clicking the button. This is a deliberate scope decision
  (goal.md's J-10 text never asked for a CLI, unlike the earlier top-up/screen journeys), not a
  hidden backend capability — flagged here only so a tester or operator familiar with Top-up's CLI
  parity doesn't go looking for a reconcile equivalent that doesn't exist.
- No other gap: every new backend endpoint this iteration added (trigger, poll, cancel, durable
  list) has a corresponding visible element on `/desk` described above — there is no backend
  capability this iteration shipped without a UI access point.
