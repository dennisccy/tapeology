# Session retro — hypothesis-foundry

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** hypothesis-foundry · **Terminal status:** GOAL_ACHIEVED · **Iterations:** 10

## Candidate items

### RETRO-1 · Over-budget agent timeouts recur across 8 of 10 iterations
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The pipeline repeatedly hits agent-timeout budgets, forcing trim-mode recovery. Iters 1–9 (except 0) all show at least one agent exceeding its 3600s quota; iter-6 exceeds it by 3× (11083s). This churn slows feedback and may mask real failures.
- **Evidence:** Agent economics — "`OVER BUDGET at coherence-auditor: 3917s > 3600s`" (iter-1), "`OVER BUDGET at browser-qa: 3696s > 3600s`" (iter-2), "`OVER BUDGET at qa-loop: 4309s > 3600s`" (iter-3), "`OVER BUDGET at browser-qa: 7102s > 3600s`" (iter-4), "`OVER BUDGET at post-dev-fanout: 7322s > 3600s`" (iter-5), "`OVER BUDGET at post-dev-fanout: 11083s > 3600s`" (iter-6), "`OVER BUDGET at qa-loop: 5106s > 3600s`" (iter-7), "`OVER BUDGET at post-dev-fanout: 5283s > 3600s`" (iter-8).
- **Sketch:** Audit which agents consistently exceed budgets and why (genuine slow work, unforced parallelism, or budget calibration). Either increase budgets with evidence, reduce pipeline parallelism, or add per-agent fast-paths. Trim-mode should be an exception, not the default recovery.
- **Verify idea:** Rerun a similar session and confirm ≤2 over-budget events across all iterations, or zero on most iters.

### RETRO-2 · Verdict churn: 4 ESCALATE verdicts + 1 STALLED before final GOAL_ACHIEVED
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The verdict sequence shows repeated escalations (iters 2, 4, 5, 7) and one hard halt (iter 8 STALLED), suggesting either evaluation criteria are unclear, gates are flaky, or the pipeline lacks visibility into why verdicts are churning. This delays convergence and burns iterations.
- **Evidence:** Verdict sequence — "iter 2: ESCALATE", "iter 4: ESCALATE", "iter 5: ESCALATE", "iter 7: ESCALATE", "iter 8: STALLED", "iter 9: GOAL_ACHIEVED".
- **Sketch:** Correlate escalate/stalled verdicts with agent logs to identify whether they stem from product issues (handled by goal loop) or framework gaps (missing evidence, unclear stop-and-ask logic, or flaky deterministic gates). Add a post-iter summary linking verdict reasons to specific agent checks.
- **Verify idea:** A future session of similar complexity shows max 1–2 escalations and zero stalls before GOAL_ACHIEVED, with gate/stop-and-ask reasons clearly logged.

### RETRO-3 · Demo walkthrough script target-key shape mismatch deceives testid detection
- **Proposed:** P2 · Effort S · Risk LOW
- **Problem:** The demo walkthrough script at `demo_runner.py:117` uses wrong target-key shape (`{"data-testid": ...}` instead of `{"testid": ...}`), causing false negatives: testids that exist in the code are reported missing because the grep finds nothing. This misleads developers during debug.
- **Evidence:** Lessons tail — "`demo_runner.py:117` instead of the `{"testid": ...}` `demo_runner.py` resolves ... The testids exist and are generated dynamically at `apps/frontend/components/CollapsibleSection.tsx:45`, so grepping `app/desk/page.tsx` for them always returns 0 and always misleads."
- **Sketch:** Fix the resolver in `demo_runner.py:117` to use the correct shape (`{"testid": ...}`), or add a validation step that verifies the resolver's shape matches what `resolve_spec` expects. Document the shape contract in the demo_runner module docstring.
- **Verify idea:** Run a walkthrough script against a page with dynamically generated testids and confirm the resolver correctly finds them.

### RETRO-4 · Calendar-dependent time-bomb in test_tick_recorder flakes monthly
- **Proposed:** P2 · Effort S · Risk LOW
- **Problem:** A test in `test_tick_recorder.py::test_tr31_format_cli_progress_line_serves_only_the_whitelisted_aggregates` embeds a hardcoded date literal (2026-06-01) and asserts against real wall-clock elapsed seconds. As months pass, this test will flake harder because the elapsed-time span grows.
- **Evidence:** Lessons tail — "`tests/test_tick_recorder.py::test_tr31_format_cli_progress_line_serves_only_the_whitelisted_aggregates` asserts forbidden digit substrings against a string that embeds real wall-clock elapsed seconds measured from a fixed 2026-06-01 literal — a calendar-dependent time-bomb that will flake harder every month."
- **Sketch:** Replace the hardcoded date literal with a parameterizable `now` fixture or use only relative elapsed time, not absolute dates. Mock time in the test to control the reference epoch. Prevent future tests from hardcoding calendar dates in assertions.
- **Verify idea:** Run the test multiple times across different month boundaries and confirm it passes in all cases.

### RETRO-5 · Token telemetry unavailable — instrumentation gap
- **Proposed:** P2 · Effort S · Risk LOW
- **Problem:** The session produced no Claude token-usage data (`claude_usage` events missing from telemetry.jsonl), preventing cost/efficiency analysis for agent forecasting and optimization. The gap is unknown: telemetry may be off, or collection failed silently.
- **Evidence:** Agent economics — "none recorded (no claude_usage events in telemetry.jsonl — token telemetry may be off)".
- **Sketch:** Verify the telemetry collection (retro_collect.sh or the analyzer) is wired to capture `claude_usage` events. If telemetry is intentionally disabled, document that decision. If it should be on, fix the collection path and rerun.
- **Verify idea:** A subsequent session emits at least one `claude_usage` event per agent in telemetry.jsonl, with plausible token counts.
