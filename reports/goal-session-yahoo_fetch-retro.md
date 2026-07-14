# Session retro — yahoo_fetch

> **PROPOSALS ONLY** — a human promotes candidates into docs/improvement-roadmap.md §16
> per EVO-1; nothing here is scheduled work.

**Session:** yahoo_fetch · **Terminal status:** GOAL_ACHIEVED · **Iterations:** 9

## Candidate items

### RETRO-1 · Pump coordination stalls recur across iterations
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The pump halted 6 times during this session, accumulating 1507.3m of AWAITING_PUMP paused time. Iterations 2–6 also show 134–151m of "unattributed (glue)" wall time, indicating inter-agent coordination gaps. This recurs in multi-iteration sessions and delays user feedback.
- **Evidence:** Agent economics — "halts: AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP" and "total AWAITING_PUMP paused gaps: 1507.3m"
- **Sketch:** Add pump-side telemetry (why it pauses — blocked subagent, dispatch queue backlog, heartbeat miss) and goal-mode dispatch logic to detect hangs. Audit whether coherence-auditor resume-skips or dev/evaluator rework chains cause step sequencing delays. Consider parallel dispatch for independence-checking steps.
- **Verify idea:** A future multi-iteration goal-mode session should show ≤300m of AWAITING_PUMP gaps and ≤50m of unattributed glue time per iteration.

### RETRO-2 · Goal-evaluator inflight timeout not counted in friction
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** Goal-evaluator hung for 360.1m with a failure flag twice (iter-1 and iter-7), suggesting an inflight timeout or heartbeat miss. These failures are not captured in the friction counters, making them invisible to framework analysis.
- **Evidence:** Agent economics — "goal-evaluator 360.1m calls=1 failures=1" in iter-1 and iter-7 incomplete attempts; Friction counters — "Quota pauses: 0" (no pause instrumentation for timeouts)
- **Sketch:** Add a friction counter for "Agent inflight timeouts" (distinct from quota pauses); export CHAIN_DISPATCH_INFLIGHT_TIMEOUT + CHAIN_PUMP_HEARTBEAT_TIMEOUT to telemetry so hangs are visible. Include timeout-caused failure in the attempt-N retry logic.
- **Verify idea:** Future sessions with evaluator hangs will show a nonzero "Inflight timeouts" counter in the friction section of the retro digest.

### RETRO-3 · Secret scanner self-recursion structural risk remains
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The scan-recursion bug (scanner re-scanning its own generated diff artifacts, causing CRITICAL count to compound) was fixed mid-session by PATH-based exclusion in `CHAIN_SCAN_BOOKKEEPING_EXCLUDES`. Without a hardening gate, future sessions may revert to value-based allowlists that don't work, or miss the PATH-based config.
- **Evidence:** Lessons tail — "scan-recursion CRITICAL that blocked this session for two iterations was cured ONLY by the PATH-based fix (`CHAIN_SCAN_BOOKKEEPING_EXCLUDES` excluding `runs reports docs/handoffs docs/phases` from both the tracked diff and the untracked enumeration)"
- **Sketch:** Bake `CHAIN_SCAN_BOOKKEEPING_EXCLUDES` defaults into the goal-mode environment or config (not a manual export). Document in `.claude/core.md` or a scan-policy file that PATH exclusion is the only durable fix for self-recursion. Add a pre-gate sanity check: if the scan-report changes between two consecutive runs with identical source, flag it as a recursion symptom.
- **Verify idea:** A follow-up goal-mode session whose diff includes only product code (no scanner edits) passes the scan gate on first attempt without CRITICAL compounding.

### RETRO-4 · Regression sentinel false-negatives on async/select content
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The deterministic regression replay (demo_runner.py text-matcher) fails on content inside `<select><option>` and async-loaded rows, even when evaluator screenshots prove the content is rendered. This blocks the goal-achieved gate despite genuine passage, requiring manual screenshot override — a brittle decision tree.
- **Evidence:** Lessons tail — "regression-sentinel golden scripts must assert on STATICALLY-rendered, always-present headings/labels (not `<option>` text or async rows); the evaluator MUST open the failing-step screenshot before honoring a replay FAIL — the screenshot outranks the replay verdict"
- **Sketch:** Harden the golden-script validator: reject `expect.text` targeting `<option>` or async-list content at build time, with a clear error message. Alternatively, enhance demo_runner.py's text-matcher to wait for async load and inspect shadow DOM / aria-label. Update the goal-achieved gate to require screenshot inspection when replay FAIL occurs, not just check the ui-test-results.md cell.
- **Verify idea:** Next UI-journey that uses dropdowns or async lists will pass the gate without needing manual screenshot adjudication.

### RETRO-5 · Token telemetry instrumentation gap
- **Proposed:** P2 · Effort S · Risk LOW
- **Problem:** The Agent economics section reports "none recorded (no claude_usage events in telemetry.jsonl — token telemetry may be off)". Without token data, framework cost analysis is blind to model pricing, inflight quota, or per-agent efficiency — making it impossible to detect regressions in LLM economics.
- **Evidence:** Agent economics — "none recorded (no claude_usage events in telemetry.jsonl — token telemetry may be off)"
- **Sketch:** Check if telemetry emission for claude_usage is disabled in the goal-mode pump or analyze_telemetry.py. If disabled, re-enable it. If the backend API is not emitting tokens, add token-counting to the pump's subagent dispatch (input + output tokens per call). Ensure telemetry.jsonl has a claude_usage event per agent call.
- **Verify idea:** The next retro digest will show a non-empty Agent economics section with token counts per agent and total session cost in the wall-time report.
