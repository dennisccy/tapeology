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

## iter-4 — 2026-09-04T22:58:00Z

**Verdict:** CONTINUE
**Lesson:** Three stored golden replay scripts now assert that `/tape/SIM-BIDABS/observation` is
ABSENT — `journey-scripts/J-01.json` step 5 and `J-03.json` step 11 expect `"Not Found"`, and the
new `J-04.json` steps 8-9 expect `"404"`. The moment iteration 5 registers the route, every one of
those replays will fail for the wrong reason (the assertion encodes the temporary absence, not the
journey). Whoever ships the route must rewrite those three scripts in the SAME iteration.
**Applies to:** any iteration that makes a previously-404 route real, and generally any golden
script written while a journey's target surface does not exist yet.

## iter-4 — 2026-09-04T22:58:00Z

**Verdict:** CONTINUE
**Lesson:** The tautological-summary-test failure mode reappeared in the very iteration that removed
it. `test_tape_observation_path_equivalence.py::test_counterexample_field_partition_drift_is_detected`
builds `widened = _FROZEN_SEMANTIC_FIELDS + ("source.session_id",)` and asserts it differs from
`_FROZEN_SEMANTIC_FIELDS` — two hand-written literals; it would still pass if
`observation_contract.MACHINE_OBSERVATION_SEMANTIC_FIELDS` were deleted. The primary TC-6 test IS
non-vacuous (real constants vs frozen literal), so nothing is unproven — but a counter-example that
never touches the real subject proves nothing about the guard.
**Applies to:** any `test_counterexample_*` written for a "constant X has not drifted" guard — the
counter-example must perturb (or stand in for) the REAL constant, not a second copy of the literal.

## iter-5 — 2026-09-05T02:40:00Z

**Verdict:** ESCALATE
**Lesson:** The deterministic replay lane cannot reach a backend-only URL. `replay-lane.sh` always
calls `demo_runner.py --base-url "$FRONTEND_URL"`, and `normalize_url()` rewrites even an ABSOLUTE
`localhost:8301` URL onto that single origin — so every golden `goto` to `/tape/{ticker}/observation`
renders Next.js's own 404 page and false-FAILs. Proof this iteration: `J-01-verify.png`,
`J-03-verify.png` and `J-04-verify.png` are byte-identical (md5 `cdcf05e2748…`) captures of that one
error screen. Journeys asserting on machine-JSON paths must be routed to the LLM browser-qa lane
(which navigates the backend origin directly), and a golden script for such a journey is worse than
none.
**Applies to:** any iteration whose journeys assert on a backend-served path (`/tape/*`,
`/research/*`, `/meta/*`) rather than a rendered page; anyone regenerating
`runs/goal-session-observation-contract/journey-scripts/` (J-01, J-03, J-04 are queued in
`state/goldens-regen-pending`, J-05 in `state/golden-gaps`).

## iter-5 — 2026-09-05T02:41:00Z

**Verdict:** ESCALATE
**Lesson:** Two browser-qa dispatches in one iteration silently destroy each other's evidence. The
canary dispatch wrote `reports/phase-…-iter-5-ui-test-results.llm.md` with J-01/J-03 **PASS**; a
second, J-05-only dispatch then OVERWROTE that same `llm.md`; the merge at the end therefore produced
a `ui-test-results.md` showing J-01 and J-03 as SKIP. The real PASS rows survive only in
`…-ui-test-results.canary.md`. An evaluator reading only the merged file would have under-scored two
journeys that were fully verified — always check for a `.canary.md` sibling when the replay lane's
FAILs were voided.
**Applies to:** any iteration where `regression-replay-results.md` carries a VOIDED / mass-false-FAIL
breaker footer, or where more than one browser-qa dispatch runs.

## iter-6 — 2026-09-05T05:45:00Z

**Verdict:** CONTINUE
**Lesson:** In a would-be closing iteration, the wall-clock budget trim is expensive in a way that
is easy to miss: J-05's substance was fully exercised this round under other row ids (UT-04 served
JSON, UT-07 404 body, `test_tape_observation_route.py` green), but its OWN row was shed as
`DEFERRED-BUDGET`, and `goal_gate.py results` blocks GOAL_ACHIEVED on the ROW, not on the substance
(verified: `results_rc=1` while `journeys` returns 6/6 passing). Run the cheap already-passing
journey rows FIRST in any closing round — a skipped row costs an entire extra iteration.
**Applies to:** any iteration expected to be the last one of an era; any iteration where
`reports/phase-*-ui-test-results.md` ends with a "Deferred (iteration budget)" section.

## iter-6 — 2026-09-05T05:45:00Z

**Verdict:** CONTINUE
**Lesson:** A guard can be honestly named, honestly described, green — and still not check the
invariant its specification names. The shipped mutator-call-site guard admitted ANY `WatchManager`
method (location), while `docs/goal.md` J-06 step 3 says "methods **that re-settle**"; `WatchManager.stop`
mutates without re-settling and sailed through. The auditor's fix derives the allowed set from the
scanned file's own AST (`self._settle(...)` call sites) with one documented carve-out. Read a guard's
predicate against the spec's verb, not its test name. (Related: the deterministic replay lane can
produce a false PASS as well as false FAILs — `journey-scripts/J-02.json` never opens the address it
claims to verify.)
**Applies to:** any iteration shipping an AST/structural guard; anyone regenerating the golden
journey scripts.

## iter-7 — 2026-09-05T07:05:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** A seeded Sim watch CLOSES on its own once the scenario's event stream is exhausted, and
the Cockpit then honestly drops the `Pause watching` control (only `Stop` remains) — so the demo
recorder's `Locator.wait_for: Timeout 4000ms` on demo steps 06/07 (`reports/demo/goal-observation-contract-iter-7/step-06.png`
shows `Watching SIM-BIDABS [Stop]`, lag 34.2s, red dot `Closed`) is a recorder-pacing artifact
against CORRECT behaviour, not a broken Pause button. The browser-qa lane clicked Pause fine minutes
earlier (`UT-J-04-reload-1.png` shows `"stream_status":"paused","paused":true`). Never read a demo
locator timeout on a Sim watch as a product regression without checking `lifecycle.stream_status` in
the same frame.
**Applies to:** any iteration whose demo/walkthrough lane drives a Sim-mode Watch → Pause → Resume
sequence, and any evaluator scoring `RECORDED_WITH_NOTES` demo results.
