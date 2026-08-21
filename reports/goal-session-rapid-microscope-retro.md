# Session retro — rapid-microscope

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** rapid-microscope · **Terminal status:** STALLED · **Iterations:** 23

## Candidate items

### RETRO-1 · Post-dev-fanout budget quota overflow
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Every full-depth iteration's post-dev-fanout step exceeds its 3600s quota, forcing work to be discarded in trim mode instead of queued.
- **Evidence:** Agent economics — "OVER BUDGET at post-dev-fanout: 10921s > 3600s (mode=trim)" (iter-2), "OVER BUDGET at post-dev-fanout: 6743s > 3600s (mode=trim)" (iter-5), and 12 more occurrences (iters 6, 7, 9, 13, 14, 15, 16, 17, 18, 19, 21, 22).
- **Sketch:** Measure actual post-dev-fanout load (reviewer + goal-evaluator + coherence-auditor + qa in parallel). If 5400s+ is typical, raise quota to 7200s. If load is legitimate, defer lower-priority audits to a post-showcase hook. Profile a mid-session iteration.
- **Verify idea:** Re-run with adjusted quota; confirm zero OVER BUDGET messages and work is queued instead of trimmed.

### RETRO-2 · Developer agent time concentration
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** Developer agent consumed 2052.1m wall-time (34% of session total), averaging 158m per call, dominating every iteration and suggesting inefficient task structure or tool redundancy.
- **Evidence:** Agent economics — "total developer 2052.1m" vs reviewer 705.7m, coherence-auditor 586.7m, goal-evaluator 584.4m; session mean 224.4m per iteration with 13 developer calls.
- **Sketch:** Log developer subagent calls and task descriptions for 2–3 representative iterations. Identify repeated or long-running work (e.g., test generation, code review loops). Create targeted skill or split developer into narrower roles (code-implementer, integration-tester).
- **Verify idea:** Measure per-developer-call wall-time on similar goal; target <120m/call.

### RETRO-3 · Showcase walkthrough lane cannot capture backend research pages
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Demo-narrator's showcase walkthrough rewrites all URLs to frontend port (:3301), which has no backend pass-through, breaking screenshot capture for `/research/...` pages.
- **Evidence:** Lessons tail (iter-22) — "The showcase walkthrough lane cannot photograph a backend research address at all: it rewrites every URL onto the frontend port (`:3301`), which has no pass-through, so `reports/demo/goal-rapid-microscope-iter-22/step-07.png` is a Next.js 404 for the graduation surface."
- **Sketch:** Add backend proxy pass-through to showcase launcher (forward `/research/*` and `/api/*` to backend host). Or add demo-config option to skip backend-only steps with documented limitation.
- **Verify idea:** Run demo step targeting `/research/...` URL; confirm screenshot captures full research page (not 404).

### RETRO-4 · Browser-QA budget overflow in lean iterations
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** Lean-iteration browser-QA consistently exceeds its 3600s quota (reaching 17465s in iter-10), forcing trim mode and incomplete evidence collection.
- **Evidence:** Agent economics — iter-3: "OVER BUDGET at browser-qa: 4747s > 3600s", iter-8: "7115s > 3600s", iter-10: "17465s > 3600s", iter-12: "7708s > 3600s".
- **Sketch:** Investigate whether lean-iteration browser-QA should be deferred (post-verdict gate) rather than inline, or raise quota to 7200s. Profile iter-10 to confirm browser-QA is bottleneck and not a test harness hang.
- **Verify idea:** Lean iterations no longer trigger OVER BUDGET at browser-qa; QA completes within 6000s or properly defers.

### RETRO-5 · Coherence-auditor evaluation cycles unsustainably long
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** Coherence-auditor consumes 586.7m total wall-time; iter-11 alone shows 349.1m for a single call, suggesting evaluation logic is inefficient or over-instrumented.
- **Evidence:** Agent economics — "total coherence-auditor 586.7m"; iter-11: "coherence-auditor 349.1m calls=1".
- **Sketch:** Profile a long-running coherence-auditor call (e.g., iter-11) to identify bottlenecks (file I/O, artifact loading, verdict tree traversal). Cache frequently-recomputed values (lessons index, verdict history). Consider splitting into fast-path (verdict only) and slow-path (full audit) with gate-based routing.
- **Verify idea:** Coherence-auditor wall-time in similar session drops 40%+ or latency becomes predictable (<60m for lean iterations).
