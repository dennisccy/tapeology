# Phase goal-rapid-microscope-iter-22 — User-Visible Changes

**Phase:** goal-rapid-microscope-iter-22
**Date:** 2026-08-20
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- An operator can now run **Study 1 (range-wall failed aggression)** — one of the three
  predeclared J-09 pilot studies that previously existed only in source code and unit tests — by
  either running `python -m app.research.scout --grid range_wall_failed_aggression_pilot` from a
  terminal, or sending `{"grid": "range_wall_failed_aggression_pilot"}` to the existing
  `POST /research/desk/micro/scout/compute` action (the same trigger door Study 2 used since
  iter-21). The run's answer (survive/kill, with a stated reason) then appears as a new family in
  the already-shipped Scout Ledger table on `/desk`.
- An operator can now run **Study 3 (capitulation exhaustion)** the same way, using
  `--grid capitulation_exhaustion_pilot` or `{"grid": "capitulation_exhaustion_pilot"}`. Its
  result also appears as a new family in the same Scout Ledger table.
- For both new studies, the operator can now see a second, honest row recording **"is there
  enough independently-verified evidence yet"** — today it reports `killed_insufficient_n`
  (the product has zero confirmed-independent trading sessions recorded so far) rather than
  silently skipping that check, exactly as Study 2's floor-check row already did.
- Nothing changed about how an operator reaches these studies — there is still no dropdown, radio
  button, or new field on `/desk` to pick a study family. The shipped "Run Screen" button keeps
  running only the original default grid; the two new study names are request-parameter values
  reachable via the CLI or the API, not a new on-screen control.

---

## What Changed in the Visible UI

- The Scout Ledger table on `/desk` (`Scout Ledger` section, expand via the "Scout Ledger" header)
  can now show up to **three** predeclared study families instead of one, once all three have been
  triggered: `failed_aggression_score__band_touch__trades_20` (Study 1, range-wall), the
  already-shipped `divergence_at_level_bearish__band_touch__trades_20` (Study 2, delta-divergence),
  and `failed_aggression_score__playbook_signal__trades_20` (Study 3, capitulation) — each its own
  family block with its own trial-row table, no new column or new section.
- Study 1's Feature cell reads `failed_aggression_score / threshold (band_touch)`; Study 3's
  Feature cell reads `failed_aggression_score / threshold (playbook_signal)` — same feature name,
  disambiguated only by the `(band_touch)` vs `(playbook_signal)` suffix already shipped in iter-21
  and by the different family header each study lands under.
- Both new families gain a second ledger row under the same candidate ID: Feature and Horizon show
  `—` (em-dash), and the Decision column reads `killed_insufficient_n` — the walk-forward
  floor-check verdict, rendered through the exact same generic row shape Study 2's floor-check row
  already used.
- No new page, section, heading, button, form field, or navigation entry was added anywhere on
  `/desk`. No column was added to the Scout Ledger table.

---

## What Old Behavior Changed

- None. The default reference grid (what the shipped "Run Screen" button actually triggers) still
  produces exactly one row per candidate, with no `killed_insufficient_n` floor-check row — this is
  explicitly regression-tested this round. The delta-divergence pilot study (Study 2) and its
  existing walk-forward floor-check row are unchanged; this iteration only re-photographs that row,
  it does not alter it.

---

## Not Visible Yet

- Study 1's real research question is still screened in a simplified, single-signal form. The full
  question goal.md describes asks whether aggressive buying/selling into a price wall, TOGETHER
  WITH a specific opposite-side liquidity signature, predicts a rejection. Only the first half (the
  aggression signal alone, `failed_aggression_score >= 0.5`) is screened this round — the
  liquidity co-occurrence half is machinery that has never been built, and this round does not
  build it. This was already disclosed as deliberately deferred in iter-21 and remains disclosed,
  not silently narrowed.
- There is still no on-screen control (dropdown, button, or form field) on `/desk` to pick which
  study family to run — an operator must already know the CLI flag or the API's `grid` request
  value to reach Study 1 or Study 3. Wiring a UI control for this was not in scope this round.
- An operator who submits an unrecognized `grid` value still gets a raw HTTP 500 rather than a
  friendly validation message — a pre-existing, disclosed, and explicitly out-of-scope rough edge,
  unchanged this round.
- Running either new study against the operator's full real recorded history (rather than small
  test fixtures) remains known to be slow — fixing that speed issue was explicitly excluded from
  this round's scope.
