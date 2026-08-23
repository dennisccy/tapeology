# Phase goal-rapid-microscope-iter-28 — User-Visible Changes

**Phase:** goal-rapid-microscope-iter-28
**Date:** 2026-08-23
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Nothing new. This iteration adds zero new actions, zero new pages, and zero new navigation. It
  is a disclosure-only change to already-shipped copy.

---

## What Changed in the Visible UI

- On the `/desk` page, inside the already-shipped **Referee Registry** collapsible section →
  **Evidence Readiness** → **Strategy Family** block, a new one-line disclosure sentence now
  appears directly below the existing tick-gate statement and directly above the existing
  basis-caveats list:

  > "Legacy Referee readiness metric — seal-unaware in the Rapid Microscope era. It may include
  > withheld/unexposed Rapid-Microscope shards and must not be used as the canonical
  > Rapid-Microscope readiness count."

  It sits right beside the block's existing `Datasets` / `Train / Holdout` / `Trades` figures and
  the tick-gate statement, styled identically to the sibling caveat lines (`text-[11px]
  text-slate-500`) so it reads as part of the same disclosure family rather than a new visual
  unit. It is rendered under a brand-new `data-testid`
  (`referee-evidence-strategy-seal-unaware-caveat`) — no existing testid, heading, table, or
  figure changed.
- No other element on `/desk`, on the cockpit (`/`), or on `/structure` changed in any way.

---

## What Old Behavior Changed

- None. The `Datasets`, `Train / Holdout`, and `Trades` figures in the Strategy Family block still
  come from the exact same `GET /research/desk/referee/evidence` response, unchanged, and are
  still rendered as a straight pass-through with zero client-side arithmetic. The new sentence is
  static, hard-coded copy — it does not react to data, load, or error state, and it always renders
  whenever the parent Strategy Family block itself renders (no new loading/empty/error state was
  introduced).
- The Referee Registry section is still collapsed by default on page load (as it always was) and
  still requires clicking the "Referee Registry" header to expand and trigger its fetches — this
  iteration did not change that behavior.

---

## Not Visible Yet

- The actual test-infrastructure fix (durable on-disk caching for two backend test files that
  previously took 14–28 minutes each against the real 26 GB dataset archive) has zero user-facing
  surface — it is purely a developer/CI-facing speed improvement to `pytest` runs and is not
  observable from the running product in any way.
- The new `test_tc10_corrupted_dataset_surfaces_with_a_warm_durable_index_from_a_different_store`
  test (added this iteration) is a backend-only regression guard proving the new durable cache
  never masks a checksum failure; there is no UI surface for it — a corrupted dataset file's
  integrity error was already surfaced in the existing "No integrity errors." / integrity-errors
  list UI before this iteration, and that display is unchanged.
