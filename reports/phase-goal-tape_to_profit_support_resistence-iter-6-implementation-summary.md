# Goal Iteration 6 (J-06) — Implementation Summary

**Phase:** goal-tape_to_profit_support_resistence-iter-6
**Date:** 2026-07-06
**Written by:** developer

---

## Features Implemented

- **Named-strategy comparison, run from the command line**: the existing "candidate check" tool
  (which already compared alternate settings against the current champion) can now instead compare
  a whole alternate trading strategy — specifically `structure_tape`, the tape-plus-structure
  strategy built in earlier iterations — against the current champion strategy (`v1`). Ask for it
  by adding `--strategy structure_tape` when running the tool; leave it off and the tool behaves
  exactly as it always has, checking alternate settings instead.
- **Same honesty rules, applied to a whole strategy**: the comparison shows, separately for the
  training data and for data the strategy has never seen (the "held-out" data — never mixed
  together), how many simulated trades each side made and what the combined simulated result was,
  in both "R" (risk-multiple) and dollar terms. A strategy is only promoted to be the new champion
  if it genuinely beats the current champion on the held-out data, with enough trades to trust the
  result — a win on the training data alone is honestly labeled "overfit" and is never promoted.
- **A disclosed measurement caveat**: every comparison report now plainly states a known limitation
  of how `structure_tape` currently recognizes a "follow-through" (a price break through a level) —
  it is a slightly looser check than watching for the exact moment of the break, which can make the
  strategy look like it trades a bit more often than a stricter check would show. This is disclosed
  in the report rather than silently left for a reader to discover, and it was not changed this
  iteration (changing it risked disturbing already-tested, tape-confirmed behaviour from earlier
  iterations).
- **Honest result on today's sample data**: run against the one small sample dataset currently
  committed to the project, the comparison honestly reports that `structure_tape` has not yet
  produced enough held-out trades to trust a result either way — so nothing is promoted, and the
  champion strategy stays `v1`. This is the correct, honest outcome for a small sample, not a
  failure of the tool.

## Changed Behavior

- **The candidate-check command-line tool**: previously it could only compare alternate
  "settings profiles" against the champion (holding the strategy fixed). It now ALSO supports
  comparing an alternate strategy (holding the settings profile fixed), selected with the new
  `--strategy` option. Nothing about the existing settings-profile comparison changed — every
  pre-existing check for that behavior still passes unmodified, proving it is identical to before.
- **The promotion record ("champion" pointer)**: previously, a promotion could only ever change
  which settings profile was in use. It can now also change which STRATEGY is in use (if one
  genuinely earns it via the same held-out test) — but only through this same one honest gate;
  nothing else about how a promotion is recorded changed.

## Backend-Only Items

- This is entirely a command-line/machine-readable capability, matching how the era-3 measurement
  tools already worked — there is no new screen or button, and none was planned for this
  iteration. The result is visible today by reading the tool's output file, or (only if a genuine
  promotion happens) via the existing Performance page and the existing "who's the champion"
  API/machine-readable connection, exactly as any other promotion already surfaces.

## Incomplete Items

- None from this iteration's assigned scope. A full, credentialed real-world comparison (using a
  larger, multi-symbol history rather than the one small committed sample) is a future operator
  action once real market-data credentials and a bigger recorded history are available — this
  iteration proves the comparison tool itself works honestly, not that `structure_tape` is (or
  isn't) actually a better strategy in the real world.

## Config and Environment Changes

- No new environment variables and no new configuration settings were added — the iteration
  reused every existing setting (the same "enough trades to trust it" threshold, the same
  default settings profile) rather than inventing new ones, exactly as the plan required.
- No database migration was needed.

## Known Limitations

- On the one small sample dataset already committed to the project, `structure_tape` makes zero
  simulated trades on the training slice and exactly one on the held-out slice — both honestly
  below the "enough trades to trust" floor. This is a known consequence of that sample being short
  and covering only two price timeframes, carried over from an earlier iteration's finding, not a
  new issue. A bigger, more realistic comparison needs a bigger recorded history.
- The scenarios proving a genuine promotion actually works (and the "positive on training data but
  fails on held-out data" honest-overfit case) were verified using small, purpose-built practice
  data, not the single real sample already in the project — the same disclosed testing technique
  used in earlier iterations. It does not change how the tool behaves on real data, only how the
  behaviour was checked before shipping.
- The disclosed "follow-through" measurement caveat (see Features Implemented) is a carried-over,
  pre-existing simplification, not something introduced this iteration — it is now written down
  plainly in every comparison report rather than left undocumented.
