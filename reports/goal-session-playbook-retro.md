# Session retro — playbook

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** playbook · **Terminal status:** STALLED · **Iterations:** 10

## Candidate items

### RETRO-1 · Post-dev-fanout budget overage and parallel-step starvation
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** The post-development parallel fanout (qa-loop, ui-test-design, auditor) is being trimmed before completion in most iterations, leaving acceptance verification incomplete. Developers and reviewers hit this repeatedly, and it masks whether downstream failures are real or time-starved.
- **Evidence:** Agent economics & wall-time report — "OVER BUDGET at post-dev-fanout: 6416s > 3600s (mode=trim)" (iter-1, line 84), "OVER BUDGET at post-dev-fanout: 4660s > 3600s (mode=trim)" (iter-6, line 188), "OVER BUDGET at post-dev-fanout: 4689s > 3600s (mode=trim)" (iter-8, line 222).
- **Sketch:** Analyze which post-dev tasks (qa-loop, auditor, ui-impact-analyst) are most critical for verdict confidence. Either (a) split developer scope into finer gates with separate budgets (core vs. test harness), (b) make post-dev-fanout budget depth-aware (larger for full, tighter for lean), or (c) implement a "post-dev checkpoint" that re-weights budget if developer alone used >50% of the fanout cap.
- **Verify idea:** Next sessions with large developer invocations show post-dev-fanout budget adequate for qa/auditor completion without trim, and downstream agent verdicts no longer cite "incomplete fanout due to trim".

### RETRO-2 · Browser-qa-agent wall-time and escalation correlation
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The browser-qa-agent consumed 486.8m of 1571m total session time (31%), and generated "OVER BUDGET at browser-qa" in iters 3, 7, 9 while the session verdict sequence shows ESCALATE at iters 3, 5, 7. This suggests retry loops without progress, but the session has no retry-count instrumentation.
- **Evidence:** Agent economics table — "browser-qa-agent | 9 | 486.8m" (line 241); wall-time report — "OVER BUDGET at browser-qa: 4658s > 3600s (mode=trim)" (iter-3, line 126), "OVER BUDGET at browser-qa: 4520s > 3600s (mode=trim)" (iter-7, line 203), "OVER BUDGET at browser-qa: 4198s > 3600s (mode=trim)" (iter-9, line 237); Verdict sequence — "iter 3: ESCALATE, iter 5: ESCALATE, iter 7: ESCALATE" (lines 22, 24, 26).
- **Sketch:** Add retry instrumentation to browser-qa-agent telemetry (per-journey retry count, step depth, time between retries). If a single journey hits >2 retries per iteration, log it as a framework signal. Optionally, implement a "replay-fast-path" mode that re-runs only the failing step (not full journey) to save time on subsequent attempts.
- **Verify idea:** Next sessions show browser-qa retry counts in telemetry; sessions with high retry counts flag via reports, and wall times for those journeys decrease after fast-path implementation.

### RETRO-3 · Escalation churn detection and human checkpoint
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** The verdict sequence shows ESCALATE at iters 3, 5, 7 with CONTINUE in between, ending in STALLED at iter-9. No mechanism detects this churn pattern or offers a human pause-and-replan checkpoint; the loop keeps trying without visibility into why escalations repeat.
- **Evidence:** Verdict sequence — "iter 3: ESCALATE, iter 4: CONTINUE, iter 5: ESCALATE, iter 6: CONTINUE, iter 7: ESCALATE, iter 8: CONTINUE, iter 9: STALLED" (lines 18–29); Halt context — "status: STALLED, parked_wip_sha: 05bf160" (lines 293–301).
- **Sketch:** Instrument goal-evaluator to track ESCALATE root causes (unfixable architecture, missing info, regression chains) in session.json. Implement an escalation counter; if counter ≥3 in a session, emit a structured "halt_suggestion: investigate_escalation" event and log the pattern for human review. Optionally, auto-trigger deeper goal-decomposer analysis of affected journeys or offer a checkpoint before iter-n+1.
- **Verify idea:** Next sessions show escalation counter in session.json; when ≥3, human gets a clear report of the pattern + root causes; fewer sessions enter STALLED after multiple escalations.

### RETRO-4 · Golden assertion rig-dependency in regression-test scripts
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** Regression-sentinel journeys are brittle when their assertions are rig-dependent (fixture-state, dynamic values). In iter-9, the browser lane used signature hash `9597251432bd9e75`, but the developer's capture 40 min earlier in the same iteration read `9803f6881e8f86b3`, proving the hash varies with runtime state. This breaks kept-product validation.
- **Evidence:** Lessons tail — "the browser lane replaced J-10's step 6 assertion 'Forward Returns' (a shipped Era-B section heading) with the literal signature hash `9597251432bd9e75`, so the era's kept-product sentinel now asserts nothing from any shipped section — and the hash is fixture-state dependent: the developer's own capture 40 minutes earlier in the SAME iteration read `9803f6881e8f86b3`" (lines 268–276).
- **Sketch:** Add a pre-browser-qa linter that scans journey-scripts/*.json for non-text assertions (hashes, timestamps, coordinates) and flags them as "rig-dependent". Provide an assertion-picker UI helper to guide toward static kept-surface strings (shipped page text, DOM IDs). Document in `.claude/judgment-rubrics.md` a "regression-test assertion safety" rule: never use computed or fixture-state values; always use shipped UI text.
- **Verify idea:** Next journey-script edits show zero signature-hash assertions in browser-qa reviews; assertion-safety linter blocks commits of dynamic assertions; browser-qa errors due to rig-dependent assertions disappear.

### RETRO-5 · Regression-sentinel verification gap at lean depth
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** When the browser-qa-agent declines to re-verify kept-route byte-identity (in writing) and the iteration depth downgrades to lean (no auditor scheduled), regression-sentinel acceptance clauses have no verifier. The evaluator is not equipped to replicate agent-level verification; acceptances float unconfirmed.
- **Evidence:** Lessons tail — "When the browser lane declines part of a journey's acceptance in writing ('kept-route byte-identity ... not independently re-verified by this agent') and the depth downgrade means no auditor ran either, that acceptance clause has NO verifier unless the evaluator becomes one" (lines 279–288).
- **Sketch:** In goal-evaluator or coherence-auditor: detect when a regression-sentinel journey has an "acceptance declined" annotation from browser-qa and depth=lean (auditor not scheduled). Either auto-promote depth to full for that iteration (accept budget overrun) or add a lightweight "acceptance validation" pass in the evaluator (git-diff confirm, screenshot equivalence). Document in `.claude/workflow.md` that regression-sentinels at lean depth require auditor run or evaluator acceptance-validation as a hard gate.
- **Verify idea:** Next sessions show no regression-sentinel acceptance gaps at lean depth; evaluator logs confirm acceptance-validation runs where browser-qa declined; audits unblock without depth promotion.

