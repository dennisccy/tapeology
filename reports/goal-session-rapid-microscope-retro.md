# Session retro — rapid-microscope

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** rapid-microscope · **Terminal status:** STALLED · **Iterations:** 29

## Candidate items

### RETRO-1 · goal_gate blocking on DEFERRED-BUDGET for no-golden Required journeys
- **Proposed:** P0 · Effort M · Risk LOW
- **Problem:** When a Required-still-passing journey has no stored golden, the budget trim marks it DEFERRED-BUDGET. The goal_gate then counts this cell as blocking GOAL_ACHIEVED, making it mechanically impossible to achieve even when every journey is passing.
- **Evidence:** Lessons tail — "A SPEED-15 rung-2 budget trim that sheds a no-golden Required-still-passing journey writes a `DEFERRED-BUDGET` row, and `goal_gate.py` counts that cell as blocking — so an ordinary wall-clock overrun can silently make GOAL_ACHIEVED mechanically impossible even when every journey is green. Iter-28 shed J-07 (no stored golden by an earlier binding decision, so replay structurally cannot cover it)"
- **Sketch:** Modify goal_gate.py to not count DEFERRED-BUDGET rows as blocking for GOAL_ACHIEVED, since they represent deliberate budget trims, not failures. Alternatively, enforce that any journey on Required-still-passing must have a golden before the round runs.
- **Verify idea:** Next goal session with a no-golden Required journey will reach GOAL_ACHIEVED (or GOAL_FAILED) on substance, not stuck on DEFERRED-BUDGET.

### RETRO-2 · Repeated OVER BUDGET markers and adaptive work shedding
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Nearly every iteration hits OVER BUDGET at post-dev-fanout, browser-qa, or coherence-auditor, triggering mode=trim to shed work. The same stages (ui-test-design, ux-regression) are repeatedly shed and reappear, suggesting the 3600s stage budgets are too tight.
- **Evidence:** Agent economics — "iter-2: OVER BUDGET at post-dev-fanout: 10921s > 3600s (mode=trim)", "iter-9: OVER BUDGET at post-dev-fanout: 5963s > 3600s (mode=trim)", "iter-26: OVER BUDGET at post-dev-fanout: 12315s > 3600s (mode=trim)", and 17 similar OVER BUDGET lines across iters 3, 5–8, 10, 12–17, 19–21, 24.
- **Sketch:** Increase post-dev-fanout, browser-qa, and coherence-auditor stage budgets based on historical utilization; or improve cost prediction before dispatch to adjust batch sizes preemptively.
- **Verify idea:** Future goal sessions show fewer OVER BUDGET markers and less work shedding; trim mode is a safety fallback, not the common path.

### RETRO-3 · Pump/dispatch failures causing incomplete iteration attempts
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** Four iterations (1, 4, 17, 28) entered the pipeline but never produced a final verdict, showing "verdict=?" and "incomplete/interrupted attempt". Each was followed by a resume that re-ran downstream stages, leaving the session ambiguous.
- **Evidence:** Agent economics — "goal-rapid-microscope-iter-1  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)", "goal-rapid-microscope-iter-4  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)", "goal-rapid-microscope-iter-17  depth=full  verdict=?  (incomplete/interrupted attempt)", "goal-rapid-microscope-iter-28  depth=full  verdict=?  (incomplete/interrupted attempt)"
- **Sketch:** Add explicit health checks at iteration boundaries; fail fast if dispatch doesn't complete within a timeout; improve error recovery so incomplete iterations roll back cleanly instead of requiring manual resume.
- **Verify idea:** Future goal sessions have no "?" verdicts; all iterations either complete with a final verdict or halt with a clear error message.

### RETRO-4 · Extended ESCALATE/STALL sequences without convergence
- **Proposed:** P1 · Effort L · Risk MED
- **Problem:** This session produced 17 ESCALATE verdicts, 2 STALLED verdicts, and only 5 CONTINUE out of 29 iterations. The verdict loop never broke (iters 1–6 mostly ESCALATE, 20–28 mostly ESCALATE/STALLED), suggesting the framework lacked instrumentation to detect and halt when looping on the same issue.
- **Evidence:** Verdict sequence — "iter 1: ESCALATE, iter 2: CONTINUE, iter 3-6: ESCALATE/ESCALATE/ESCALATE/ESCALATE, ... iter 20-21: ESCALATE/ESCALATE, iter 22: STALLED, iter 23: ESCALATE, iter 24: CONTINUE, iter 25: ESCALATE, iter 26: CONTINUE, iter 27: ESCALATE, iter 28: STALLED"
- **Sketch:** Add heuristics to detect repeated escalations on the same root cause and halt with "looping detected" instead of continuing; or implement a max-consecutive-escalates threshold (e.g., halt after 5 consecutive ESCALATE without a CONTINUE).
- **Verify idea:** Future goal sessions that would produce 15+ iterations either achieve GOAL_ACHIEVED or halt on a "looping" / "infeasible" signal within ~8 iterations.
