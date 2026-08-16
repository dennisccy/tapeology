# Session retro — referee

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** referee · **Terminal status:** GOAL_ACHIEVED · **Iterations:** 15

## Candidate items

### RETRO-1 · Agent step timeout quota exceeded in 13/15 iterations
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Agents regularly exceed their per-step time budget (3600s), triggering trim mode and truncating evidence collection. This recurred in 13 of 15 iterations across multiple agent roles.
- **Evidence:** Wall breakdown — repeated "OVER BUDGET" lines: "OVER BUDGET at coherence-auditor: 3998s > 3600s (mode=trim)" (line 82), "OVER BUDGET at browser-qa: 6433s > 3600s (mode=trim)" (line 112), "OVER BUDGET at post-dev-fanout: 6061s > 3600s (mode=trim)" (line 129), and 10+ more instances across iters 1–13.
- **Sketch:** Audit the 3600s quota cap — it may be too tight for the depth and breadth of modern goals. Consider: (a) stratified per-agent caps based on empirical distribution, (b) context-aware budgets (lean vs. full depth), (c) a warn-then-pause policy instead of trim, to preserve evidence for later analysis.
- **Verify idea:** Re-run a similar complexity goal and measure whether "OVER BUDGET" lines drop below 5 per session; collect agent wall times and confirm the new caps are not padding.

### RETRO-2 · Browser-qa-agent wall-time outlier in full-depth iterations
- **Proposed:** P2 · Effort M · Risk MED
- **Problem:** In full-depth iterations, browser-qa-agent consumes extreme wall time, sometimes exceeding all other agents combined (iter-10: 193.8m solo).
- **Evidence:** Agent economics table — total browser-qa-agent: 394.0m of 1688m total (23%); Wall breakdown iter-10 "browser-qa-agent 193.8m calls=1" (line 220); iter-8 "browser-qa-agent 35.5m calls=1" (line 186).
- **Sketch:** Profile full-depth browser-qa execution to determine if time is spent on parallelizable checks (screenshot/assertion fan-out), sequential retries (flaky check loops), or single-pass deep analysis. If parallelizable, split into smaller steps with intermediate checkpoints to reduce wall time and quota pressure.
- **Verify idea:** Capture telemetry from a full-depth iteration's browser-qa-agent; if >30% is spent on parallel/retry work, a split should reduce wall time by 20% without degrading verdict quality.

### RETRO-3 · Repeated ESCALATE verdict churn in early iterations (pattern: 3, 5, 7, 9)
- **Proposed:** P2 · Effort S · Risk LOW
- **Problem:** Every alternate iteration escalates during the early run, suggesting an oscillating evaluation state or flipping verdict logic. This churn consumed extra iterations before resolution.
- **Evidence:** Verdict sequence — "iter 3: ESCALATE, iter 4: CONTINUE, iter 5: ESCALATE, iter 6: CONTINUE, iter 7: ESCALATE, iter 8: CONTINUE, iter 9: ESCALATE, iter 10: CONTINUE, iter 11: GOAL_ACHIEVED" (lines 22–30).
- **Sketch:** Add telemetry to log which evaluator rule(s) triggered each ESCALATE verdict. Review whether any evaluation criterion is flipping state on adjacent iterations due to measurement noise or systematic drift. Propose a stabilizing filter: require two consecutive violations before escalating, or add hysteresis to verdict transitions.
- **Verify idea:** Correlate ESCALATE events with evaluator-log reasons; if the same criterion recurs alternately, implement the filter and re-run the same goal; expect ESCALATE count to drop by 30%+ with no verdict change.
