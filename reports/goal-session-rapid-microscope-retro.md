# Session retro — rapid-microscope

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** rapid-microscope · **Terminal status:** STALLED · **Iterations:** 30

## Candidate items

### RETRO-1 · ESCALATE churn dominates verdict sequence, ending in STALLED
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The session produced 22 ESCALATE verdicts out of 30 iterations and never converged, ending STALLED. This heavy recycle pattern suggests either the evaluator's gates are too strict, escalation resolution is broken, or the goals are unachievable with this toolchain. Developers see repeated work rejection with no clear path to success.
- **Evidence:** Verdict sequence — "iter 0: CONTINUE, iter 1: ESCALATE, iter 2: CONTINUE, iter 3: ESCALATE, iter 4: ESCALATE, iter 5: ESCALATE, iter 6: ESCALATE, iter 7: CONTINUE, iter 8: ESCALATE, iter 9: CONTINUE, iter 10: ESCALATE, iter 11: CONTINUE, iter 12: ESCALATE, iter 13: ESCALATE, iter 14: ESCALATE, iter 15: ESCALATE, iter 16: ESCALATE, iter 17: ESCALATE, iter 18: ESCALATE, iter 19: CONTINUE, iter 20: ESCALATE, iter 21: ESCALATE, iter 22: STALLED, iter 23: ESCALATE, iter 24: CONTINUE, iter 25: ESCALATE, iter 26: CONTINUE, iter 27: ESCALATE, iter 28: STALLED, iter 29: STALLED"
- **Sketch:** Instrument the evaluator to categorize why ESCALATEs occur (e.g., test failure, regression, anti-goal violation, evidence gap). Add a max-escalate-per-journey counter; if a single journey escalates >4 times, escalate to human review rather than retry. Alternatively, add a convergence detector that flags when ESCALATE/CONTINUE cycles are not making progress over 5+ iterations.
- **Verify idea:** Run a follow-up session on the same goal; if ESCALATE count drops to <30% of iterations or to <15 total, the fix is working.

### RETRO-2 · Developer agent dominates wall time; 42% of session spent in one agent
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Developer consumed 2700.5m out of 6404.3m total wall time—nearly 3.5x more than any other agent (reviewer 768.4m, auditor 749.5m). This serialization bottleneck suggests developer tasks are over-scoped, work is not parallelized, or the pipeline queues dispatches inefficiently.
- **Evidence:** Agent economics — "developer | 13 | 43259 | ...", and session wall-time summary "total developer 2700.5m" vs "total reviewer 768.4m" and "total auditor 749.5m" and "total goal-evaluator 756.4m"
- **Sketch:** Profile developer's task scope in high-wall iterations (e.g., iter-9 and iter-13, where developer made multiple calls). Identify whether developer is calling itself recursively, blocking on external resources, or doing work that could be delegated to specialized agents. Implement per-iteration developer time cap (e.g., 1 call maximum, or <60m per iteration).
- **Verify idea:** In next session, measure developer call count and wall time per iteration; target ratio to other agents <2x instead of 3.5x.

### RETRO-3 · Iteration budget overruns; 15+ iterations exceed post-dev-fanout cap
- **Proposed:** P2 · Effort S · Risk LOW
- **Problem:** Sixteen iterations reported "OVER BUDGET" with some wildly exceeding the 3600s post-dev-fanout cap (iter-2: 10921s, iter-13: 14000s, iter-26: 12315s, iter-28: 11738s). Trim mode silently skips downstream agents, degrading observability and potentially masking regressions.
- **Evidence:** Wall-time breakdown — "goal-rapid-microscope-iter-2 [...] OVER BUDGET at post-dev-fanout: 10921s > 3600s (mode=trim)", "goal-rapid-microscope-iter-13 [...] OVER BUDGET at post-dev-fanout: 14000s > 3600s (mode=trim)", "goal-rapid-microscope-iter-26 [...] OVER BUDGET at post-dev-fanout: 12315s > 3600s (mode=trim)"
- **Sketch:** Increase post-dev-fanout budget to 7200s–10800s for full-pipeline iterations, or add a pre-flight budget estimate that warns developers upfront of their time window. Alternatively, reduce developer scope (RETRO-2) to keep within tighter caps.
- **Verify idea:** Rerun this session; if OVER BUDGET warnings appear in <10% of iterations, the fix is working.

### RETRO-4 · Multiple incomplete/resume attempts within single iteration; pump instability
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Iter-1, iter-4, iter-17, iter-28 each show multiple incomplete attempts within one iteration, including failed agent calls (iter-17 ui-impact-analyst failure, iter-28 auditor failure). This suggests pump inflight timeouts are too short or the pump is crashing mid-dispatch, forcing expensive restarts.
- **Evidence:** Wall-time breakdown — "goal-rapid-microscope-iter-1  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)" followed by "goal-rapid-microscope-iter-1  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)" then final attempt; similar pattern for iter-4, iter-17 (with "failures=1"), and iter-28 (with "auditor [...] failures=1")
- **Sketch:** Audit CHAIN_DISPATCH_INFLIGHT_TIMEOUT (current likely 3600s) and per-agent inflight caps. Raise them to 14400s or 21600s for lengthy iterations. Add early-warning telemetry 10% before timeout. Implement a pump-crash recovery log to detect if the pump is restarting mid-dispatch.
- **Verify idea:** In next session, measure count of incomplete-attempt repeats; should be zero or <3% of iterations (i.e., <1 per session).

### RETRO-5 · Single-agent wall-time outliers obscure queue vs. compute bottleneck
- **Proposed:** P2 · Effort M · Risk MED
- **Problem:** Individual agent calls show extreme wall times (coherence-auditor 349.1m in iter-11, developer 498.6m with 3 calls in iter-9, goal-evaluator 51.4m in iter-19) that dwarf others' effort. Without instrumentation separating true agent-execution time from pump-queue delay, the pipeline cannot distinguish genuine algorithmic bottlenecks from queue stalls.
- **Evidence:** Wall-time breakdown — "goal-rapid-microscope-iter-11 [...] coherence-auditor 349.1m calls=1", "goal-rapid-microscope-iter-9 [...] developer 498.6m calls=3 [...] pump-wait 493.6m", "goal-rapid-microscope-iter-19 [...] goal-evaluator 51.4m calls=1"
- **Sketch:** Add telemetry breakdown in the analyzer: emit (agent-name, wall-time, queue-time-estimated, active-agent-time). Use this to separate pump overhead from true work. Flag outliers where queue-time > 50% of wall-time as pump-tuning candidates, and outliers where active-time is extreme as agent-logic candidates.
- **Verify idea:** Rerun one high-outlier iteration (e.g., a developer-heavy iter); if queue-time is >50% of wall-time, pump tuning (RETRO-4) is the fix. If <30%, agent logic needs profiling.
