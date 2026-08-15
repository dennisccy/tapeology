# goal-referee-iter-4 — Implementation Summary

**Phase:** goal-referee-iter-4
**Date:** 2026-08-14
**Written by:** developer

---

## Features Implemented

This iteration has no new user-visible feature. It fixes a real correctness bug the previous
iteration's reviewer found in the statistics engine that Era 6 ("The Referee") is building —
before that engine gets wired into anything a person or the app actually reads.

In plain terms: Tapeology is building a new "referee" system whose whole job is to say, honestly,
whether a pattern the app noticed is real evidence or just noise. Part of that system is a
statistics calculator that produces a number called a p-value — roughly, "how surprising would
this result be if there were actually nothing going on." The previous iteration's reviewer found
that in one specific, narrow situation, this calculator could report a p-value that was
mathematically impossible — smaller (more "impressive-looking") than the calculation method
itself is capable of legitimately producing. This iteration fixes that calculation so it can never
again report an impossible number, and adds new proof (both hand-checked examples and large
randomized checks) that the fix actually works in both directions — it doesn't just stop being
"too confident," it also isn't now "not confident enough."

- **Fixed the miscalculation.** The bug was a subtle floating-point arithmetic mistake: one number
  was computed two different ways in two different places, and the two ways could disagree by a
  tiny sliver in rare cases — just enough, in those rare cases, to throw off the final result.
  Fixed so both computations always agree.
- **Added new proof the fix works, in both directions.** One new automated test reproduces the
  reviewer's exact example and confirms the correct answer comes back. A second test tries
  thousands of randomly generated situations and confirms none of them produce an impossible
  answer. A third and fourth test extend the calculator's own "self-check" suite (which runs
  thousands of simulated trials to prove the statistics are correctly calibrated) to specifically
  cover the exact kind of situation where this bug could occur — a gap the previous iteration's
  self-check suite didn't cover — and to prove the self-check suite would have caught this exact
  bug if it had existed when that suite was written.
- **Re-verified and re-labeled the engine's own "proof of health" stamp.** The statistics engine
  carries a small stamp recording which version of its own logic produced a result (so nothing
  downstream can ever mistake results from before this fix for results from after it). That stamp
  was updated and the underlying proof re-run from scratch against the fixed code.
- **Added one small honesty improvement to an already-shipped feature.** A part of the system that
  counts how much trading evidence exists in the archive already correctly ignores evidence from
  before a rule change — but it did so silently. It now explicitly lists which dates it ignored
  and why, instead of just quietly not counting them. This has no visible effect today (no rule
  change has actually happened yet), but it means a future rule change will be reported honestly
  instead of just causing numbers to quietly shrink with no explanation.

## Changed Behavior

- **The statistics calculator's most extreme-looking results are now capped correctly.** Before
  this fix, in one narrow situation, the calculator could report a result as slightly more
  significant than its own method allows. This has never been visible to anyone — this
  statistics engine isn't connected to any screen or report yet — but it's fixed before it gets
  connected to anything.
- **One archive-summary feature gained a new, currently-always-empty detail field**
  (`stale_basis_dates`) that will only ever contain anything after a future detector-rule change
  — which hasn't happened yet. Every number this feature already reported is unchanged.

## Backend-Only Items

- Everything in this iteration is backend-only. The statistics calculator and the archive-summary
  feature it touches are not yet connected to any page, button, or report a person can see — that
  connection is planned for a later step in this same project chapter (several iterations away).

## Incomplete Items

None from this iteration's own scope. The full walk-through of the existing app (cockpit, the
Structure page, the Desk page and all its sections) that confirms nothing else broke is handled by
a separate QA step later in the pipeline, not by this development step — this iteration's own work
was entirely backend calculation code with no visible screen to check.

## Config and Environment Changes

None. No new settings, no new environment variables, no new external service or library.

## Known Limitations

- The fix actually needed to be slightly broader than the original plan described. The plan called
  for fixing one specific calculation step; testing showed that fixing only that step still left a
  real (if rare — about 7 times in 100) chance of the same impossible-number bug showing up in
  situations spanning several trading sessions at once. A second, closely related fix (making sure
  numbers are combined the same careful way in a second spot) closes that gap completely, verified
  against over 20,000 randomly generated test situations with zero remaining problems. Full
  reasoning is in the developer handoff.
- The "proof of health" stamp mentioned above happened to come out with the exact same numeric
  values as before the fix, for the one small example it's built from — the fix genuinely changed
  the underlying code, but this particular example's specific numbers didn't happen to trigger the
  bug. The fix itself is proven correct by three other, dedicated tests, not by this stamp.
