# Session retro — hypothesis-foundry

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** hypothesis-foundry · **Terminal status:** STALLED · **Iterations:** 9

## Candidate items

### RETRO-1 · Budget-trimming logic fails to cap runaway agent time
- **Proposed:** P0 · Effort M · Risk MED
- **Problem:** The 3600s time budget for qa-loop, post-dev-fanout, and browser-qa lanes is being ignored or ineffective. Seven of nine iterations overran (iters 1, 2, 3, 4, 5, 6, 7), with iters 5–6 reaching 11,000s (3× cap).
- **Evidence:** Agent economics — "OVER BUDGET at coherence-auditor: 3917s > 3600s", "OVER BUDGET at browser-qa: 7102s > 3600s", "OVER BUDGET at post-dev-fanout: 11083s > 3600s", "OVER BUDGET at qa-loop: 5106s > 3600s"
- **Sketch:** Audit the trim-mode budget enforcement in the pump and orchestrator. Check: (1) are kill signals firing? (2) is the time calculation accurate? (3) should earlier preemption thresholds (e.g., halt at 80% cap) be added? (4) can fanout be reduced proactively when approaching budget?
- **Verify idea:** Run a representative session and confirm no iteration exceeds its budget category by >5% margin.

### RETRO-2 · Claude token usage telemetry missing
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** Operators cannot observe token cost trends or audit cost per iteration because claude_usage events are not being recorded in the telemetry stream.
- **Evidence:** Agent economics — "none recorded (no claude_usage events in telemetry.jsonl — token telemetry may be off)"
- **Sketch:** Debug why the claude_usage event hook is silent. Check: (1) is the event source firing? (2) is the sink enabled in the telemetry config? (3) add a verification step to retro-collect that confirms the presence of claude_usage events and warns if missing.
- **Verify idea:** Run a session and confirm retro-collect emits at least one claude_usage event or prints a diagnostic line naming why it is absent.

### RETRO-3 · Audit-applied fixes invalidate earlier iteration screenshots
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** When the hard auditor applies a product fix (e.g., frontend code change) during its audit pass, all browser-QA screenshots captured earlier in the same iteration are now stale and no longer represent the final state. The system does not re-run demos or flag screenshots as invalid.
- **Evidence:** Lessons tail — "When the hard auditor APPLIES a product fix during its own pass, every screenshot the browser-QA lane already captured is stale by one change — here `apps/frontend/app/desk/page.tsx` moved at 16:25 while all evidence PNGs were taken at 16:08"
- **Sketch:** Implement a post-audit screenshot refresh: (1) detect when audit writes a product fix touching frontend or routes; (2) trigger an automatic demo-runner verification pass using the latest code; (3) re-file or supersede the stale evidence, or mark journey verdict as provisional pending re-run.
- **Verify idea:** Audit a journey with a product fix and verify the Final Summary includes fresh screenshots or an explicit "re-run after fix" placeholder.

### RETRO-4 · Demo recording selector validation insufficient
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** A demo recording can report success ("RECORDED_WITH_NOTES") and appear complete while its clicks silently fail (non-existent selectors in the current codebase), capturing wrong pages. The system trusts the recording without cross-checking selectors against the code.
- **Evidence:** Lessons tail — "A walkthrough recording can report `RECORDED_WITH_NOTES` and look complete while showing entirely the wrong page: this iteration's demo script clicked `desk-section-expand-*` testids that do not exist anywhere in `apps/frontend/app/desk/page.tsx`, all 7 clicks silently failed"
- **Sketch:** Add a selector validation gate before accepting a demo as journey evidence: (1) parse the demo script's click targets; (2) grep the codebase for matching test IDs; (3) if any selector is unresolved, mark the recording as NEEDS_REVIEW; (4) or auto-generate demo scripts from golden journey test IDs instead of free-form recording.
- **Verify idea:** Run demo-runner and verify it emits a warning if any click target does not exist in the current codebase.

### RETRO-5 · Escalate/Continue verdict churn without convergence
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** From iter 2 through iter 7, verdicts alternate between ESCALATE and CONTINUE without clear progress, ending in STALLED. This pattern suggests escalations are not effectively breaking feedback loops or changing the agent approach.
- **Evidence:** Verdict sequence — "iter 2: ESCALATE, iter 3: CONTINUE, iter 4: ESCALATE, iter 5: ESCALATE, iter 6: CONTINUE, iter 7: ESCALATE, iter 8: STALLED"
- **Sketch:** Add a convergence gate to the evaluator or orchestrator: (1) if ESCALATE verdicts occur in ≥4 of the last 6 iterations without a GOAL_ACHIEVED or clear product progress marker, halt with a distinct "escalation exhaustion" verdict instead of CONTINUE/ESCALATE; (2) review escalation criteria to ensure escalation meaningfully changes agent composition/tooling, not just re-runs the same path.
- **Verify idea:** Run a session with repeated escalations and verify it halts before iteration 8 if no progress signal appears.

