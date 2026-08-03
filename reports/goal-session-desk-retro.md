# Session retro — desk

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** desk · **Terminal status:** GOAL_ACHIEVED · **Iterations:** 37

## Candidate items

### RETRO-1 · Goal-evaluator wall-time outlier — rebalance agent economics
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The goal-evaluator agent consumed 1894 minutes over 37 iterations while developer consumed 682 minutes — nearly 2.8× more wall time. This imbalance starves other agents and creates bottleneck risk.
- **Evidence:** Agent economics — "total goal-evaluator 1893.6m" vs "total developer 682.1m" (lines 653–654). Iter 7 alone shows goal-evaluator 1100.0m with failures=1 (line 158).
- **Sketch:** Analyze goal-evaluator dispatch: identify overlapping work with auditor/coherence-auditor, or excessive retry loops within verdict logic. Consider splitting verdict logic into fast binary path vs. deep analysis, or deferring non-blocking checks to post-verdict hooks.
- **Verify idea:** Run same session headless; if goal-evaluator wall time drops below 2× developer time while maintaining verdict accuracy, rebalance is working.

### RETRO-2 · Incomplete/interrupted attempts accumulate without deterministic cleanup
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** At least 12 partial attempts across the session (lines 88, 123, 128, 157, 183, 184, 193, 199, 250, 256, 355, 367, 442, 474, 483) are marked "incomplete/interrupted" with no recorded halt reason. Resume logic skips agents silently, making root-cause diagnosis impossible for future optimization.
- **Evidence:** Wall-time report — lines 86–672 show multiple "goal-desk-iter-<n> depth=<d> verdict=? wall=? (incomplete/interrupted attempt)" entries with no halt_reason logged.
- **Sketch:** Add halt_reason field to session.json + telemetry event at every incomplete attempt, naming the trigger (heartbeat timeout, quota pause, engine reset, developer timeout). Aggregate halt reasons in retro-input.md so patterns become visible per-session.
- **Verify idea:** Next session's retro report includes a "Halt reasons" counter section; review to find most common incomplete-attempt cause.

### RETRO-3 · Resume-skipped agents suppress evidence without audit trail
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** When iterations resume, agents marked "resume-skipped" are discarded silently. Coherence-auditor is resume-skipped in 12+ iterations; unknown whether skipped work was redundant, critical, or observable. This opacity makes verdicts unverifiable if critical evidence was skipped.
- **Evidence:** Wall-time report — "(resume-skipped: coherence-auditor)" appears in lines 134, 146, 168, 190, 203, 215, 237, 260, 274, 394, 405, 419, 438, 471, 487, 510, 522, 540, 553, 573, 587, 598, 618, 633, 648.
- **Sketch:** Before skipping an agent on resume, emit a checkpoint record naming the agent, iteration, depth, and incomplete state. Tag verdicts with critical-agent skips as "evidence incomplete." Human reviews whether tag correlates with rework in next iteration.
- **Verify idea:** Retro report flags CONTINUE/GOAL_ACHIEVED with "critical agent(s) skipped"; human confirms no verdict accuracy loss correlates with the tag.

### RETRO-4 · OVER BUDGET annotations lack halt mechanism — silent trim risks incomplete evaluation
- **Proposed:** P2 · Effort L · Risk MED
- **Problem:** Eleven OVER BUDGET instances (lines 440, 460, 482, 500, 542, 575, 589, 620, 635, 650) show agents exceeding 3600s inflight timeout in trim mode. These print as warnings but do NOT prevent the verdict, risking silent data loss or incomplete audit.
- **Evidence:** Wall-time report — lines 440, 460, 482, 500, 542, 575, 589, 620, 635, 650 show "OVER BUDGET at <step>: <seconds>s > 3600s (mode=trim)".
- **Sketch:** Convert OVER BUDGET in critical agents (auditor, goal-evaluator, coherence-auditor) to STALLED rather than CONTINUE. For non-critical agents, emit telemetry event counted as friction signal in retro. Tune trim timeout or parallelize overbudget agent work.
- **Verify idea:** Next session records zero OVER BUDGET in critical agents, or OVER BUDGET halts execution for manual intervention (no silent trim).

### RETRO-5 · Depth demotion (full→lean) breaks spec clause guarantees — breaks acceptance criteria
- **Proposed:** P2 · Effort M · Risk LOW
- **Problem:** Engine demoted depth from full to lean on four consecutive iterations (32, 33, 35, 36), preventing demo-narrator from running. Two journeys owe unmet `[NEW]`-flagged walkthroughs. Journey specs that depend on demo-narrator have no fallback, so engine depth decisions can silently break acceptance criteria.
- **Evidence:** Lessons tail — "The engine has now demoted a `Depth: full` spec to `lean` on four consecutive iterations (32, 33, 35, 36), so the demo-narrator step has not run since iter-34 and TWO journeys (J-20, J-21) now owe a `[NEW]`-flagged walkthrough" (lines 698–704).
- **Sketch:** Tag demo-narrator walkthroughs as `evidence`-depth passengers in goal.md, not acceptance requirements. Or: add hard gate preventing full→lean demotion if unmet `[NEW]` walkthroughs exist; require human approval to demotion.
- **Verify idea:** No future journey accumulates an unmet `[NEW]`-flagged walkthrough over 5+ verdicts; all satisfied before halt, or session escalates before demotion.
