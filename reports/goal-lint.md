# goal-lint report — docs/goal.md

Run: 2026-07-30 · deterministic exit: 0 · semantic findings: 3

Scope note (honesty): the deterministic pass covers the whole file. The semantic pass read
Success Criteria → Product Shape (145–320), the build anchors/traps T-1…T-10a (308–375), **J-14
verbatim** (965–1073, the journey edited today), and the full Anti-goals section (1077–1160).
J-01…J-13 were consulted through the session's journey digests and their evaluator history, not
re-read verbatim this run — findings below are confined to what was actually read.

## Deterministic lint (goal_lint.py)
clean (exit 0, no output)

## Semantic findings

### Overloaded term — "rig" now means two different things in one acceptance line — line 1028
> Acceptance: on the fixture-scoped rig a NEW screen run — for a screen date not already recorded under

- **Problem:** today's owner ratification (T-10a) adds a second, unrelated "rig" to the same
  acceptance sentence — the **headed capture rig** (`project-extensions/qa-rig/`, a browser/display
  harness) now sits ~20 lines below the **fixture-scoped rig** (a data-scoping condition about
  which store the backend serves). A browser-qa or evaluator agent reading "the rig" has two
  referents and no disambiguator; iterations 19–21 already showed this lane mis-resolving rig
  language six times running.
- **Suggested rewrite:** rename the first occurrence so the two never collide —
  `Acceptance: on the fixture-scoped DATA rig (a scoped copy of the store, per T-2) a NEW screen run — for a screen date not already recorded under`
  and keep the T-10a reference spelled "headed capture rig" wherever it appears.

### Acceptance clause the runs never satisfy — "on the fixture-scoped rig" — line 1028
> Acceptance: on the fixture-scoped rig a NEW screen run — for a screen date not already recorded under

- **Problem:** every evidence lane in iterations 16, 19, 20 and 21 served the **ambient**
  `apps/backend/.data` instead of a scoped copy, and each evaluator disclosed it as a deviation
  rather than a failure — a criterion that is stated, breached, and waived six times in a row is
  training the loop to treat acceptance text as advisory. Iteration 19's lane also wrote into the
  owner's real store (390 bar series, 4 screens) while nominally on "the fixture-scoped rig".
  Either the clause is enforceable or it should not be in the contract.
- **Suggested rewrite:** make it mechanically checkable instead of aspirational —
  `Acceptance: on a scoped data rig — the serving backend started with the desk store env override pointing at a copy, proven by the evaluator reading /proc/<uvicorn pid>/environ and reporting the path it found — a NEW screen run ...`
  (If scoping is not actually wanted for evidence lanes, drop the clause and state plainly that
  evidence runs may append to the real store, so nothing is silently waived.)

### Unobservable as specified — the `[NEW]`-flagged walkthrough — line 1049
> **`[NEW]`-flagged demo-narrator walkthrough** covers the briefing's opposite-wall disclosure end to

- **Problem:** the demo runner's action set is `{goto, click, fill, expect, wait_for}` with no
  scroll primitive, and every ranked row is one stretched `next/link` anchor — so a click inside a
  row navigates to `/structure` instead of revealing anything. The `opposite` column sits past the
  table's horizontal overflow edge, which is why iteration 21's film "passed" with three
  byte-identical frames that do not show the column at all. As written, the clause cannot be met
  by the tool it names, yet it reports success.
- **Suggested rewrite:** state what the frames must actually contain, and let the runner prove it
  by assertion rather than by pixels it cannot reach —
  `a [NEW]-flagged demo-narrator walkthrough over POPULATED ranked rows whose steps assert (expect) the "opposite" column header and at least one row's rendered opposite-wall text, with each recorded frame distinct (no two frames byte-identical) — and if the column is to be VISIBLE in a frame, the runner first gains a scroll action (lean, zero product change) driving the table container's scrollLeft.`

## Summary

Structurally clean, and today's T-10a ratification is well-formed: it keeps the screenshot bar
intact while naming a capture path that can actually satisfy it. The highest-impact fix is the
second finding — six consecutive waivers of "on the fixture-scoped rig" mean the contract is
teaching the loop that acceptance text is negotiable; make it a checkable environment assertion or
remove it. The other two are one-line disambiguations that prevent a repeat of the J-14 stall.
