# Goal Session observation-contract — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-09-02T23:20:00Z

**Verdict:** CONTINUE
**Lesson:** Every one of J-01..J-05 asserts on the SAME served surface (`/tape/{ticker}/observation`),
but the goal's Binding Execution Order puts that route at step 5 — so several correctly-executed
build iterations will legitimately produce zero newly-passing journeys, and the journey table will
only unlock in a burst once the route lands. Do not read that flat stretch as a stall, and do not
reorder the route earlier to "show progress" (the order is mandatory); the honest per-iteration
signal in the meantime is the pytest module named in each journey's own steps.
**Applies to:** iterations 1-4 of this session (builder/hash laws, time law, descriptor/lifecycle,
path equivalence) — the decomposer and the evaluator both.

## iter-0 — 2026-09-02T23:21:00Z

**Verdict:** CONTINUE
**Lesson:** This venv's pytest (9.1.1) prints NO final "N passed, M skipped" summary line, and
`--collect-only -q` prints per-file counts (`tests/test_api.py: 15`) rather than test ids — so J-06's
required "record the `N passed` summary line" must be satisfied by tallying `-q` progress characters
(or summing the per-file collect counts: 3938 here), never by grepping for a summary line that never
appears. Also budget for it: the full suite runs longer than a browser-QA dispatch window (browser QA
had to record it `unknown` this iteration).
**Applies to:** any iteration recording backend suite counts, especially J-06 sentinel runs and any
browser-qa dispatch that tries to re-run the full suite itself.

## iter-1 — 2026-09-03T09:05:00Z

**Verdict:** CONTINUE
**Lesson:** The recompute guard forbids `observation_contract.py` from importing
`app.engine.classifier`, yet Constitution §1 requires the artifact to carry the classifier's closed
five-state name list. The resolution that survived review and the coherence audit: duplicate the
names as a literal tuple in the guarded module (`observation_contract.py:54-60`) and put the
single-source-of-truth check in the TEST module, which is unrestricted and CAN import the classifier
(`test_tape_state_vocabulary_matches_classifier_states`). Pattern: when a guard forbids an import
that a contract needs the value of, move the cross-check to the test side rather than weakening the
guard or importing anyway.
**Applies to:** any later iteration whose builder must expose an engine-owned vocabulary or enum it
is forbidden to import — iterations 2 and 3 (`availability_basis` values, lifecycle/feed-basis
vocabularies) most likely, and the iteration-6 guard module that will re-assert all of them.

## iter-2 — 2026-09-03T11:05:00Z

**Verdict:** CONTINUE
**Lesson:** The new settled-pair helper (`apps/backend/app/watch_manager.py:341`) keys its write off
`engine.snapshot().ticker` with no check that the engine is still the registered one, and the shipped
interleaving tests all use a SYNC no-feeder harness — so the one genuinely racy path (a live watch
switch, where the old task's cancellation branch settles after the new engine's cold reset) is
untested and the reviewer reproduced the clobber in a real async run. It self-heals only by accident
of loop ordering. Harden it with an identity check plus a real running-task switch test before the
route reads it at iteration 5.
**Applies to:** any iteration touching `watch_manager.py`'s feeder/cancellation paths, and iteration 5
(the route) which becomes the first production reader of `get_observation_source`.

## iter-2 — 2026-09-03T11:05:00Z

**Verdict:** CONTINUE
**Lesson:** `tests/test_tick_recorder.py::test_tr31_format_cli_progress_line_serves_only_the_whitelisted_aggregates`
is a genuinely time-dependent flake: it embeds a real elapsed-seconds value computed from a fixed past
date, and fails whenever those digits happen to contain one of its own fixture constants as a
substring (it hit "4253" for the developer today; my own full-suite run was clean). A single failure
in that one test is not a regression signal — re-run before treating it as one.
**Applies to:** any iteration that records a full backend suite count, especially J-06 sentinel runs.

## iter-3 — 2026-09-04T22:35:00Z

**Verdict:** CONTINUE
**Lesson:** A spec item phrased "all N values are pairwise distinguishable" invites a tautological
summary test: `test_seven_lifecycle_statuses_plus_watch_stopped_are_pairwise_distinguishable`
(`apps/backend/tests/test_tape_observation_lifecycle_feed.py:513`) asserts `len({...seven literals}) == 7`
and never touches `WatchManager` — the real proof lives entirely in the eight sibling tests above it.
The reviewer caught it; the suite would have stayed green forever without it meaning anything.
**Applies to:** any iteration writing "every one of N states/values is distinct" coverage — especially
iteration 6's `test_tape_observation_guards.py` (lexicon, compound-identifier ban, English-only,
external-system scan), whose whole value depends on the scan being non-vacuous over real inputs.

## iter-3 — 2026-09-04T22:35:00Z

**Verdict:** CONTINUE
**Lesson:** `runs/goal-observation-contract-iter-3/status.json` already read `current_step: dev_complete`
with the implementation and new test module fully present in the working tree, but no dev handoff file
existed — a prior developer session had finished the code and died before writing its artifact. The
second dev session correctly re-verified the tree against the spec instead of either trusting the status
flag or rebuilding from scratch; both shortcuts would have been wrong (double-build, or an unverified
"done").
**Applies to:** any resumed/re-dispatched iteration where `status.json` claims a step is complete but
that step's own output artifact (handoff, report) is missing — verify the working tree, do not redo and
do not assume.
