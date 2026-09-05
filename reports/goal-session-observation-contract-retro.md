# Session retro — observation-contract

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** observation-contract · **Terminal status:** GOAL_ACHIEVED · **Iterations:** 8

## Candidate items

### RETRO-1 · Goal-decomposer catastrophic timeout and dominance
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The goal-decomposer agent dominates session wall time (465.9 min of ~1,300 min total) and suffered a catastrophic timeout in iter-3, taking 360 minutes in a single failed call before retrying and failing again at 0.1 minutes. This pattern wastes compute and delays convergence.
- **Evidence:** Agent economics — "goal-observation-contract-iter-3  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt) goal-decomposer 360.1m calls=1 failures=1" and immediately after "goal-observation-contract-iter-3  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt) goal-decomposer 0.1m calls=1 failures=1"
- **Sketch:** Add decomposer-specific timeout instrumentation and log decomposed slices with time-per-slice to identify pathological goal expansions early. Consider streaming decomposition results or chunking the goal to detect failures within minutes, not hours. Emit a circuit-breaker error if a single decompose call exceeds 30 minutes.
- **Verify idea:** Re-run a future session and confirm goal-decomposer never exceeds 20 minutes per call, or fails fast (<1 min) with an explicit error instead of a timeout wall.

### RETRO-2 · Recurring agent budget overruns (5 of 8 iterations)
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** Five out of eight iterations exceeded their 3600-second agent-execution budgets and were trimmed mid-execution. Trimming loses evidence and may mask real failures, making the verdict unreliable when agents are routinely cut off.
- **Evidence:** Agent economics — "OVER BUDGET at browser-qa: 5540s > 3600s (mode=trim)" (iter-2), "OVER BUDGET at coherence-auditor: 4603s > 3600s (mode=trim)" (iter-4), "OVER BUDGET at browser-qa: 5072s > 3600s (mode=trim)" (iter-5), "OVER BUDGET at post-dev-fanout: 4160s > 3600s (mode=trim)" (iter-6), "OVER BUDGET at coherence-auditor: 3655s > 3600s (mode=trim)" (iter-7)
- **Sketch:** Analyze which agents repeatedly exceed their budgets (browser-qa 2 times, coherence-auditor 2 times). Raise their individual budgets to accommodate real work, or parallelize their tasks (e.g., split browser-qa across independent journeys). Add a pre-dispatch timeout hint so a launcher can warn or adjust budget if prior iterations show consistent overruns.
- **Verify idea:** Increase browser-qa and coherence-auditor budgets to 5400 seconds in a future session and confirm no OVER_BUDGET trims occur, or reduce them to <2 per session.

### RETRO-3 · Token telemetry instrumentation gap
- **Proposed:** P2 · Effort S · Risk LOW
- **Problem:** Agent economics recorded zero claude_usage events, blocking visibility into token consumption (model usage, cost, tier distribution) across the session. Without this, it is impossible to validate whether a model-tier upgrade or agent-rebalancing change actually reduces cost or latency.
- **Evidence:** Agent economics — "none recorded (no claude_usage events in telemetry.jsonl — token telemetry may be off)"
- **Sketch:** Enable claude_usage event logging in the dispatch wrapper or pump. Record model_id, input_tokens, output_tokens, and cache_read_tokens for every agent call. Aggregate by agent role to surface which agents consume the most tokens and which models are used most.
- **Verify idea:** Run a future session and confirm telemetry.jsonl contains ≥1 claude_usage event per agent dispatch with non-zero token counts recorded.

### RETRO-4 · Pump coordination halts block iteration completion (5 halts, 3 incomplete attempts)
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The session halted on AWAITING_PUMP five times and accumulated three iterations (0, 1, 3) with incomplete or interrupted attempts. Iter-3 in particular retried four times before converging, wasting ~390 minutes of the decomposer. This pattern suggests pump availability or dispatch coordination issues break the iteration loop.
- **Evidence:** Halt context — "halts: AWAITING_PUMP, machine_reset, AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP" and Agent economics — iter-0 "incomplete/interrupted attempt" (line 39), iter-1 "incomplete/interrupted attempt" (lines 52, 61), iter-3 "incomplete/interrupted attempt" (lines 95–107)
- **Sketch:** Add dispatch retry limits to avoid cascading retries on transient pump unavailability. Log pump readiness state transitions (online/offline) at every dispatch attempt. If AWAITING_PUMP is hit >2 times in a session, emit an operator alert and pause the iteration loop pending manual intervention rather than auto-retrying.
- **Verify idea:** Confirm future sessions with pre-dispatch pump health checks have ≤1 AWAITING_PUMP halt per session and zero incomplete attempts on the first iteration.
