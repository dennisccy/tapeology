# Phase goal-fast_wall-iter-5 — User-Visible Changes

**Phase:** goal-fast_wall-iter-5
**Date:** 2026-07-17
**Written by:** ui-impact-analyst

---

## Context

This iteration made **zero changes to any frontend file** — `git status`/`git diff` on
`apps/frontend/` is empty, confirming `apps/frontend/app/structure/page.tsx` is byte-identical to
iter-4's shipped version. Two things happened instead:

1. The already-shipped "Compute edge report" button, live progress line, and failed-state render —
   built in iter-4 but never actually watched in a browser because Chrome MCP failed to start —
   were finally driven end-to-end in a live Chrome session and screenshotted (click → running →
   terminal state, plus the failed-state render). This closes a **verification** gap iter-4's own
   report flagged ("this iteration's actual browser click-through was not captured with a
   screenshot... a verification gap to close, not a known product gap"), not a product gap. No
   pixel changed; what changed is the evidence behind an already-claimed capability.
2. The compute engine behind that same button became resumable, and — from the command line only —
   parallel. This changes **how fast** a re-triggered compute finishes and makes one number that was
   already being displayed (the "(N from cache)" annotation on the progress line) genuinely
   non-zero for the first time, without adding, removing, or relabeling a single on-page element.

---

## What Users Can Now Do

- **None new this iteration.** Every action available on `/structure` — loading the page, clicking
  "Compute edge report" / "Retry compute," watching the progress line, reading the finished report
  — already existed since iter-4. This iteration adds no new button, page, form, or navigation
  entry anywhere in the browser UI; the plan's own scope statement is explicit: "New user actions:
  none — the existing 'Compute edge report' button is byte-unchanged."

---

## What Changed in the Visible UI

- **Nothing rendered differently.** No label, layout, color, or component changed on `/structure`
  or anywhere else in the frontend — the page is git-confirmed byte-identical to iter-4.
- The one thing that changed is evidentiary, not visual: the exact same not-computed panel / button
  / progress line / failed-state render that iter-4 built was, for the first time, actually
  exercised through a live browser session (scoped backend, cold cache) and screenshotted for TC-1
  (click → "Computing…" + live "0 / 0 backtests" progress → terminal render, zero full-page
  reload), TC-2 (the not-computed panel's exact pre-click text, plus every other `/structure`
  section — Tradable Map, Case Studies, Fetch from Yahoo Finance, Registry, Comparison — confirmed
  rendering exactly as before), and TC-3 (a `state: "failed"` snapshot rendering the backend's
  `EdgeReportError` message verbatim, with the button relabeled "Retry compute"). A user looking at
  the page would see no difference from iter-4; a reviewer looking at whether the claimed iter-4
  capability actually works in a real browser now has photographic proof where before there was
  none.

---

## What Old Behavior Changed

- **Re-triggering an interrupted compute now finishes faster.** Previously, if a compute job was
  killed, crashed, or the server restarted mid-sweep, clicking "Compute edge report" / "Retry
  compute" again (or re-running the command-line warmer) recomputed every single (dataset,
  strategy) pair from scratch — including pairs that had already finished. It now skips every pair
  already durably recorded and computes only what is left, so a resumed run can complete far
  faster than a fresh one. One direct, visible consequence: the progress line's existing
  "(N from cache)" annotation — present in the code since iter-4 but permanently dead (N was always
  `0`, because nothing was ever cached) — can now genuinely show a non-zero N while a resumed
  compute is running. On a first-time, cold-cache click — the scenario this iteration's own
  screenshots capture — there is nothing yet to resume from, so that specific click looks and
  behaves exactly as it did in iter-4 (the annotation stays absent).
- **The command-line warmer's `--workers N` flag now does what it says.** Previously
  `python -m app.research.edge_report_compute --workers N` accepted any number but silently ran
  every backtest one at a time regardless of the value. A value greater than 1 now genuinely splits
  the sweep across that many separate worker processes. This is a terminal-only change — the
  `/structure` page's button still runs its compute on a single process, by design (see "Not
  Visible Yet" below).

---

## Not Visible Yet

- **Multi-process parallelism is command-line-only.** The on-page "Compute edge report" / "Retry
  compute" button still runs its sweep single-threaded — a deliberate, logged, reversible scope
  decision to keep multi-process work out of the always-on web server this iteration, not a defect.
  Only `python -m app.research.edge_report_compute --workers N` gets the speedup.
- **The new per-pair backtest cache has no UI or API surface, and is not meant to get one.** The
  new `EdgeReportBacktestCache` (a SQLite file, typically `edge_report_backtests.db`) is a pure
  internal accelerator behind the sweep — nothing on `/structure`, the REST API, or MCP reads it
  directly, and deleting it is always safe (the next compute silently rebuilds it).
- **Cancelling a running compute still has no button** — unchanged since iter-4. The backend route
  exists (`POST /research/edge-report/compute/cancel`) but no element on `/structure` calls it.
- **Forcing a fresh recompute over an already-warm report still has no UI control** — unchanged
  since iter-4. The page's button always sends `force: false`.
- **The first complete real edge report — the one run against the actual trading-data corpus rather
  than small test fixtures — still has not been produced.** This iteration makes that eventual run
  faster and safely interruptible; it does not run it. It remains an explicit, operator-gated
  action for a future session (the CLI warmer, now genuinely parallel and resumable, is the tool
  that would run it).
