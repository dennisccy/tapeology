# goal-clean_slate-iter-4 — Implementation Summary

**Phase:** goal-clean_slate-iter-4
**Date:** 2026-07-24
**Written by:** developer

---

## Features Implemented

This iteration has no new user-visible feature — it is the "fingerprint epoch bump," a required
bookkeeping step that follows the demolition work of the previous three iterations. In plain
terms: earlier iterations deleted the manual-journal / studies / performance pages and their
backend plumbing. Those deleted features used to contribute to a hidden "fingerprint" number that
every measurement in the app carries (so measurements taken under different settings are never
mixed together). Now that those settings no longer exist, this iteration finishes the cleanup by:

- **Removing the now-unused settings** from the app's configuration file (23 settings that only
  the deleted pages ever used).
- **Minting a new fingerprint number** to reflect the smaller, cleaned-up configuration.
- **Adding one new "founding" measurement row** under the new fingerprint, so the app's
  measurement history honestly shows "here is where the old configuration's numbers end and the
  new configuration's numbers begin" — nothing from before this change is edited, deleted, or
  re-labeled.

## Changed Behavior

- **The fingerprint stamp every new measurement carries changed** from `4d665603569b9dbf` to
  `08e471b10130e1e2`. This stamp is invisible in normal use — it never appears as a headline
  number anywhere in the UI — but it is embedded in every measurement (levels, tradable-map bands,
  edge-report cells, PnL-ledger rows) so measurements from before and after this change can never
  be silently averaged together.
- **The PnL-history record now shows 2 entries instead of 1** on `GET /research/pnl/ledger` and in
  the committed `reports/pnl/pnl-history.md` file: the original "founding baseline" measurement
  (unchanged, still under the old fingerprint) and a new second "founding baseline (post-clean-
  slate epoch)" measurement under the new fingerprint. The actual profit/loss numbers in the new
  row are identical to the original row's numbers — nothing was re-measured differently, only
  re-stamped under the new, smaller configuration.
- **The backtest history list (an internal admin view, not a cockpit page) now shows its 2 newest
  entries as the two backtests this bookkeeping step itself ran** — this list has always shown
  only its 100 most recent entries; running any new backtest naturally pushes the oldest entry off
  that list. The 2 pushed-off entries are not deleted, just no longer on the first page.

## Backend-Only Items

- The fingerprint bump and the new PnL-ledger row are backend/config/report changes only. There is
  no new page, button, or on-screen indicator for this — it is invisible bookkeeping that keeps the
  app's honesty guarantees intact after the previous iterations' page removals. (The existing
  `/research/pnl/ledger` endpoint and the committed `reports/pnl/pnl-history.md` file, both already
  visible to an operator who looks for them, now simply show one more row than before.)

## Incomplete Items

None from this iteration's own scope. The next iteration (J-05, "the kept product stands") is a
separate, already-planned closing step that walks the surviving app end to end in a browser (both
charts, the Structure page, Case Studies, the Edge Report) to confirm nothing broke — that check
was intentionally NOT part of this iteration (this iteration's own acceptance criteria are all
backend/keyless by design, matching how the plan for this step was written).

## Config and Environment Changes

- No new environment variables or settings were added.
- 23 existing settings were REMOVED from the app's configuration (`apps/backend/app/config.py`) —
  all of them were leftover controls for the pages deleted in earlier iterations (verdict timing,
  hint timers, entry-checklist flags, and similar). None of the settings that control the surviving
  Cockpit/Structure pages, the levels/tradable-map computations, or the backtest engine were
  touched.
- Two existing settings — the "founding measurement" identifier and its display title — were given
  new values (not new settings, just new default text) so the required new measurement row could
  be added without colliding with the original one's identifier.

## Known Limitations

- The exact new fingerprint value (`08e471b10130e1e2`) and the new founding-row identifier
  (`founding-baseline-strategy-v1-default-clean-slate`) are recorded here and in the developer
  handoff for reference by whoever plans the next iteration — they do not need to be re-derived.
- One test file (`test_profile_equivalence.py`) contained an additional pinned fingerprint value
  the original plan for this iteration did not know about in advance (a second, related number
  that also had to move for the same reason as the main one). It was found, verified correct, and
  updated — documented in full in the developer handoff for transparency.
- A few code comments elsewhere in the codebase still mention some of the 23 removed settings by
  name, purely as historical "why we chose this number" notes attached to settings that ARE still
  in use. These comments are harmless (comments don't affect how the app runs) and were
  deliberately left alone to keep this iteration's changes narrowly scoped to exactly what was
  planned — flagged in the developer handoff for anyone doing a future documentation cleanup pass.
