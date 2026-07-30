# Session retro — desk

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** desk · **Terminal status:** STALLED · **Iterations:** 22

## Candidate items

### RETRO-1 · Instrument and cap goal-evaluator wall time per iteration
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** The goal-evaluator agent consumed 27 cumulative hours across 22 iterations, with a single failure in iter 7 taking over 18 hours before timing out. Teams planning future sessions have no visibility into when an evaluator is stalled or overconstrained.
- **Evidence:** Agent economics — "total goal-evaluator: 1621.7m" and Wall-time report iter 7 — "goal-evaluator: 1100.0m calls=1 failures=1"
- **Sketch:** Add a per-iteration wall-time circuit breaker to telemetry collection (e.g., alert if evaluator > 60m, fail if > 120m). Log cumulative evaluator minutes and frame-rate telemetry per journey to detect slow convergence early. Surface the threshold in session.json and loop documentation.
- **Verify idea:** Run a multi-iteration session and confirm that an evaluator timeout (or near-limit) logs a clear warning in telemetry.jsonl before the iteration halts.

### RETRO-2 · Require demo-walkthrough acceptance to include assertion source (not gallery presence alone)
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Demo-narrator verdicts report RECORDED success when the frame gallery is non-empty, even if the frames are byte-identical or scrolled off-screen, making the walkthrough unreliable as an acceptance criterion.
- **Evidence:** Lessons tail — "Demo Verdict: RECORDED with a non-empty gallery is NOT proof the film shows anything: this run's three frames are one byte-identical image (md5 `3b02db86…`)" and "Narration accuracy had to be proven a different way — by re-deriving every quoted number from the recorded snapshot on disk."
- **Sketch:** Change demo_runner.py to log frame-by-frame md5s and viewport position at each step. Modify the demo-narrator verdict logic to flag walkthrough conjuncts as REQUIRES_MANUAL if frame hashes repeat or if scrollable containers remain unseen. Reference `.claude/judgment-rubrics.md` evidence-floor rules when emitting the verdict.
- **Verify idea:** Run a demo walkthrough on a scrollable UI element; confirm the verdict either includes frame hashes or marks the conjunct as requiring manual verification.

### RETRO-3 · Instrument iteration-resumption overhead and pipeline re-entry cost
- **Proposed:** P2 · Effort M · Risk LOW
- **Problem:** Multiple iterations show incomplete attempts followed by resume-skipped phases (e.g., iter 7, 9, 10, 14, 19). The session loses wall time to re-entrant pipeline steps, but there is no metric tracking the cost of each resumption or root cause of the interruption.
- **Evidence:** Wall-time report — "goal-desk-iter-7 (incomplete/interrupted attempt)" followed by "(resume-skipped: goal-decomposer, coherence-auditor)" and similar patterns in iters 9, 10, 14, 19 with "failures=1" or no verdict recorded.
- **Sketch:** Add a resumption-tracker field to session.json (iter_id, original_verdict_attempt, skipped_agents, retry_count). Log the halt reason (timeout, out-of-quota, evaluator failure) in a new telemetry event class before resuming. Measure wall-time delta between first attempt and success.
- **Verify idea:** Complete a full goal-mode session and confirm session.json contains a resumption summary showing at least one resume event with the halt reason and wall-time cost.

### RETRO-4 · Reduce unattributed (glue) wall time in multi-phase iterations
- **Proposed:** P2 · Effort L · Risk LOW
- **Problem:** Full-pipeline iterations (depth=full) show 80–190m of unattributed (glue) time out of 150–230m total wall, suggesting serial bottlenecks between agent stages that are not logged.
- **Evidence:** Wall-time report iter 1 — "unattributed (glue): 83.5m" out of "wall=142.5m", iter 2 — "unattributed (glue): 96.0m" out of "wall=159.4m", iter 6 — "unattributed (glue): 192.5m" out of "wall=236.5m".
- **Sketch:** Decompose glue time by inserting telemetry checkpoints between agent dispatch and the next agent's start in the iteration orchestrator. Name the gap (e.g., "goal-decomposer→goal-evaluator delay", "artifact-write overhead"). Log to a new telemetry event class.
- **Verify idea:** Run a single full-pipeline iteration and confirm telemetry.jsonl includes one checkpoint event per named glue gap, totaling 80% of the reported unattributed time.

### RETRO-5 · Add deterministic halt-reason logging to session.json on STALLED verdict
- **Proposed:** P2 · Effort S · Risk LOW
- **Problem:** The session halted with STALLED status and parked_wip_sha, but session.json does not explain whether it halted due to hit-max-iterations, evaluator-unreachable, manual stop, or some other gate. Retro analysis cannot root-cause the halt without reading the lessons tail.
- **Evidence:** Halt context — "status: STALLED, last_verdict: STALLED" with no halt_reason field; Lessons tail — "STALLED on a human-owned unblock path, not CONTINUE" suggests human action was required.
- **Sketch:** Expand session.json to include halt_reason (string, one of: "max_iterations", "evaluator_unreachable", "manual_stop", "gate_blocked", "unknown") and halt_detail (human-readable explanation, e.g., "demo gallery frame hashes identical"). Emit halt_reason in the orchestrator's halt-decision log.
- **Verify idea:** Halt a goal-mode session and confirm session.json contains both halt_reason and halt_detail fields.

nothing recurred worth proposing beyond the five above (all friction counters are zero, verdict churn is documented in lessons, and the wall-time outlier in goal-evaluator has clear instrumentation gaps).
