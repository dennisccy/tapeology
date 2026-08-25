# Session retro — rapid-microscope

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** rapid-microscope · **Terminal status:** GOAL_ACHIEVED · **Iterations:** 34

## Candidate items

### RETRO-1 · ESCALATE verdict pattern dominates 34-iter session
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Over half of the iterations ended ESCALATE rather than CONTINUE; many runs resolved CONTINUE only to be followed by ESCALATE, forcing re-evaluation and re-work. This prolongs sessions and delays goal convergence.
- **Evidence:** Verdict sequence — "iter 0: CONTINUE / iter 1: ESCALATE / iter 2: CONTINUE / iter 3: ESCALATE / iter 4: ESCALATE / iter 5: ESCALATE / iter 6: ESCALATE / iter 7: CONTINUE / iter 8: ESCALATE / iter 9: CONTINUE / iter 10: ESCALATE ... iter 20: ESCALATE / iter 21: ESCALATE / iter 22: STALLED / iter 23: ESCALATE / iter 24: CONTINUE / iter 25: ESCALATE / iter 26: CONTINUE / iter 27: ESCALATE / iter 28: STALLED / iter 29: STALLED / iter 30: GOAL_ACHIEVED"
- **Sketch:** Audit the ESCALATE gate logic in `.claude/workflow.md` verdict-dispatch rules. Check if the threshold for escalating vs. continuing is too tight, or if certain agent verdicts (reviewer, coherence-auditor, auditor) are weighted too heavily. Consider a "soft continue" mode for minor issues that don't warrant full re-evaluation.
- **Verify idea:** Next session should show ESCALATE/CONTINUE ratio trending away from 1:1, with fewer total iterations to GOAL_ACHIEVED (target <25 iters for similar scope).

### RETRO-2 · Per-pipeline-stage quotas exceeded in ≥15 iterations; budget misalignment
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The post-dev-fanout and browser-qa pipeline stages repeatedly exceeded their 3600s quota across 15+ iterations, forcing mode=trim or causing incomplete/interrupted attempts that lost work and required restart. The inconsistency suggests the budgets are misaligned with real workload.
- **Evidence:** Agent economics — wall-time report shows "OVER BUDGET at post-dev-fanout: 10921s > 3600s (mode=trim)" (iter 2), "14000s > 3600s (mode=trim)" (iter 13), "12315s > 3600s (mode=trim)" (iter 26); and "OVER BUDGET at browser-qa: 4747s > 3600s (mode=trim)" (iter 3), "17465s > 3600s (mode=trim)" (iter 10), recurring in iters 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 24, 26, 28, 30, 32, 33.
- **Sketch:** Instrument post-dev-fanout and browser-qa stages to categorize work (review rounds, capture, replay) and measure each separately. Rebase quotas on collected median + P95 latencies. Alternatively, allow adaptive quotas that scale with prior rounds (e.g., if iter-N hit 6000s, iter-N+1 gets 7200s).
- **Verify idea:** Next session shows no over-budget trims in browser-qa or post-dev-fanout stages, or trims occur <2 times per session.

### RETRO-3 · Browser-QA cannot coordinate rig restarts for fixture-scoped captures
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Journeys that require the shared `:8301`/`:3301` app to restart under a different `TAPEOLOGY_DATASET_DIR` cannot be satisfied by browser-QA (its rules forbid restarts). The gap is disclosed late (iter-31, iter-32), wasting iterations before falling back to manual restart approval.
- **Evidence:** Lessons tail — "A browser-QA dispatch cannot deliver a fixture-scoped capture that needs the shared `:8301`/`:3301` rig restarted under a different `TAPEOLOGY_DATASET_DIR` — that agent's own rules forbid restarting the app, so it disclosed the gap instead (as iter-31's did for J-11)."
- **Sketch:** Add a `requires_rig_restart: true` field to journey acceptance specs. In goal-decomposer, detect this flag and either reject the journey early, or issue an `AskUserQuestion` asking whether to restart the rig before the journey runs. Alternatively, extend browser-QA's permissions to explicitly allow rig restart for fixture-scoped captures if the spec declares it.
- **Verify idea:** Next journey requiring a rig restart either declares it in the spec (rig restarted proactively) or is rejected at decomposition time — no iteration wasted on discovery.

### RETRO-4 · Developer agent consumes 41% of wall-time; imbalance suggests missed instrumentation
- **Proposed:** P2 · Effort M · Risk LOW
- **Problem:** Developer consumed 2802.4m of 6772m total agent wall-time (41%), 3.3× the auditor and 1.6× goal-evaluator. No telemetry breaks down developer work by task type (search, implement, test, fix-loop round), so we cannot identify which tasks drive the imbalance or whether multiple fix-loop rounds compound the problem.
- **Evidence:** Agent economics — "total developer 2802.4m" vs "total auditor 749.5m" vs "total goal-evaluator 854.9m"; developer made 13 total invocations, averaging 215m per call.
- **Sketch:** Instrument each developer dispatch to tag the task type (search, implement, test-implement, fix-loop-round-N, retry-from-checkpoint). Log wall-time and token cost per tag. Analyze if fix-loops with N>3 dominate the cost, or if search/implement tasks are undersized and triggering many restarts.
- **Verify idea:** Next session's developer invocations are tagged in telemetry; wall-time distribution by task type is queryable; if fix-loops are the culprit, they average <4 rounds per invocation.

### RETRO-5 · STALLED verdicts led to recovery, not halt — gate enforcement unclear
- **Proposed:** P2 · Effort S · Risk LOW
- **Problem:** Three iterations declared STALLED (iters 22, 28, 29), which should be a hard halt per `.claude/workflow.md`, but the session recovered and reached GOAL_ACHIEVED (iters 30–33). The framework's STALLED gate is either unenforced or has undocumented recovery logic, making future STALLED→recovery cases hard to debug and reason about.
- **Evidence:** Verdict sequence — "iter 22: STALLED / iter 23: ESCALATE [session continues] ... iter 28: STALLED / iter 29: STALLED / iter 30: GOAL_ACHIEVED"; session.json shows "status: GOAL_ACHIEVED", not halted.
- **Sketch:** Audit goal-evaluator's STALLED gate (`.claude/workflow.md` verdict dispatch). Document the exact conditions that allow recovery (e.g., new evidence from auditor, user confirmation, or a time/round limit). If recovery is legitimate, rename STALLED to CHECKPOINT or add an explicit recovery substate; if STALLED should be final, fix the gate to enforce halt.
- **Verify idea:** Next session: if it emits STALLED, it halts immediately (no iter after STALLED); if it recovers from STALLED, the lessons log explicitly documents why (e.g., "auditor found new fixture; retrying").

