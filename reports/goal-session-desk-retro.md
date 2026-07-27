# Session retro — desk

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** desk · **Terminal status:** STALLED · **Iterations:** 8

## Candidate items

### RETRO-1 · Sentinel baseline capture must happen in iteration 0
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** When a goal.md sentinel journey asserts "kept responses are byte-identical to an era baseline," the pipeline has no guarantee the baseline was ever captured. In desk iter-0, the baseline artifact was not stored, so the sentinel clause sat unfalsifiable for seven iterations, then blocked closure at the end.
- **Evidence:** Lessons tail — "A sentinel journey that asserts 'kept responses are byte-identical to an era-open baseline' is unfalsifiable unless iteration 0 actually CAPTURES that baseline — this era never did, so the clause sat unchecked for seven iterations and then blocked closure at the gate."
- **Sketch:** Goal-mode iteration-0 must validate that any sentinel journey with a baseline-comparison clause has emitted the baseline artifact to `runs/goal-session-<sid>/state/` before the loop continues. Add a deterministic gate in the evaluator that greps for sentinel clauses mentioning "baseline" or "byte-identical," flags them, and forces evidence of the baseline file before CONTINUE. If missing, return STALLED with a diagnostic message naming the missing artifact.
- **Verify idea:** Run a test goal.md with a byte-identical sentinel; confirm iter-0 halts if no baseline was captured, resumes and passes once the baseline is manually placed.

### RETRO-2 · Frozen-file edits must immediately escalate to human
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** When a mid-era iteration repairs a file that goal.md declares frozen (e.g., bars.py), the repair silently breaks clauses in a sentinel journey without detection. The loop continued CONTINUE-ing through four more iterations because other work was productive, only to block at goal-close when the sentinel audit ran. This delays discovery of a human decision point.
- **Evidence:** Lessons tail — "the same era-close audit surfaced that a mid-era emergency repair to protected files (iter-4's price-less-bar fix in `bars.py` / `StructureChart.tsx` / a chart guard test) silently made THREE of that sentinel's clauses literally false; because each iteration had other productive work, the loop kept CONTINUE-ing past the one question only the owner could answer, four times."
- **Sketch:** Goal-mode developer (or any iteration-level edit tool) must detect writes to files named in goal.md's frozen-file list. On first touch, log an event and route a STALLED verdict immediately to the orchestrator with a message naming the file and asking the human to ratify the change. Do not allow CONTINUE until the human approves a new baseline or amends the frozen list.
- **Verify idea:** Edit a frozen file during a test goal run; confirm the next evaluator verdict is STALLED (not CONTINUE) and the human message surfaces the file name and the ratification question.

### RETRO-3 · Evaluator timeout and retry signal needs observatory instrumentation
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** Iter-7's goal-evaluator failed after 1100 minutes of wall time, then was retried. The long hang and failure are hard to diagnose from the telemetry alone; there is no clear log of why the evaluator consumed that time or when it decided to fail.
- **Evidence:** Agent economics / wall-time report — "goal-desk-iter-7  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt) goal-evaluator  1100.0m  calls=1  failures=1" followed by a successful retry.
- **Sketch:** Instrument goal-evaluator to emit periodic heartbeat logs (every 5–10 minutes of wall time) naming which journey/journey-step it is currently evaluating, how long that step has taken so far, and whether it has detected a hang or timeout. Emit the heartbeat to the session's telemetry.jsonl as a debug event. On timeout or failure, include a snapshot of the last heartbeat state.
- **Verify idea:** Run a long-running evaluator; confirm telemetry shows heartbeat events every 5–10 min and a failure snapshot on timeout, making it easy to see which step stalled.

### RETRO-4 · Friction counter coverage for evaluator hangs
- **Proposed:** P2 · Effort S · Risk LOW
- **Problem:** The friction counters omit any metric for evaluator timeouts or retries. Iter-7 had an evaluator failure that cost 1100 minutes of wall time, but the friction counters all read zero. Future sessions will have no early warning signal of this failure mode.
- **Evidence:** Friction counters — "Quota pauses: 0", "Attempt-1 review FAILs: 0", "Malformed-verdict rewrites: 0" (no evaluator timeout counter); Agent economics — goal-evaluator wall time in iter-7 failed attempt is 1100.0m.
- **Sketch:** Add a new friction counter: "Evaluator timeouts or retries (>30min per invocation)". Calculate it from telemetry claude_usage events where agent=goal-evaluator, wall_sec > 1800, and the next invocation has the same iteration and a success verdict. Emit the counter to retro-input.md.
- **Verify idea:** Generate a test telemetry with a 1100-min evaluator call followed by a retry; confirm retro-input.md shows the timeout counter as ≥1.

### RETRO-5 · Sentinel clause audit must run before iteration-final verdict
- **Proposed:** P2 · Effort M · Risk MED
- **Problem:** The goal-close audit that checks sentinel clauses ran only at the very end (iter-7 close), after the system had already committed to a CONTINUE series. If the audit had run earlier (e.g., at each iteration's close), the falsified baseline clauses would have been caught and flagged sooner.
- **Evidence:** Lessons tail — "Worse, the same era-close audit surfaced that a mid-era emergency repair to protected files (iter-4's price-less-bar fix in `bars.py` / `StructureChart.tsx` / a chart guard test) silently made THREE of that sentinel's clauses literally false; because each iteration had other productive work, the loop kept CONTINUE-ing past the one question only the owner could answer, four times."
- **Sketch:** Move the sentinel clause audit logic from goal-close into the evaluator's iteration-verdict logic. After each iteration's test results are in, run the audit on all sentinel journeys. If any clauses are now false (e.g., a baseline no longer matches), emit a STALLED verdict with a diagnostic naming which clauses failed and in which journey.
- **Verify idea:** Run a test goal where iter-4 breaks a sentinel clause; confirm the evaluator at iter-4's close returns STALLED with the broken clause named, not CONTINUE.
