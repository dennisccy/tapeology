# Session retro — tradable_wall

> **PROPOSALS ONLY** — a human promotes candidates into docs/improvement-roadmap.md §16
> per EVO-1; nothing here is scheduled work.

**Session:** tradable_wall · **Terminal status:** GOAL_ACHIEVED · **Iterations:** 11

## Candidate items

### RETRO-1 · Add scoped-keyless backend fixture for replay/observability iterations
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Golden-replay and observability iterations false-fail when the `/structure` journey runs against the unscoped real-corpus backend; edge-report compute (10h+) starves the page render, so the replay's expected band string never appears and screenshots show only the loading skeleton. This recurred in iters 6, 8, 9, and 10, forcing manual verdict repair and obscuring real regressions.
- **Evidence:** Lessons tail — "the replay lane must be pointed at the scoped-keyless backend (`TAPEOLOGY_DATASET_DIR` fixture + pre-warmed `TAPEOLOGY_EDGE_REPORT_CACHE_DB`), not the pipeline's default real-corpus backend, or its `/structure` steps will false-fail on backend saturation." and "browser-QA runs against the shared pipeline backend pointed at the REAL corpus, where a genuine cold ~10h edge-report compute keeps the cache empty the whole session, so the warm render is unreachable by design."
- **Sketch:** Introduce a `TAPEOLOGY_BACKEND_MODE=scoped-keyless` environment variable for iteration replay and observability lanes. When active, point the backend to a pre-provisioned keyless dataset directory and pre-warmed edge-report cache instead of the real corpus. Document the fixture setup in the iteration harness and ensure browser-QA and golden-replay both check this mode before dispatching.
- **Verify idea:** Run three consecutive observability iterations against the scoped backend and confirm `/structure` screenshots render the band values within 30s, not timeout.

### RETRO-2 · Audit lane must check browser-qa-agent result directly before down-scoring
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** The coherence-auditor reads only its own QA report and ignores separately-dispatched browser-qa-agent output. When the audit lane's Chrome launch fails, the auditor scores a journey as `partial` or `unknown`, even though the browser-qa-agent may have succeeded in a parallel lane and delivered the real evidence. This forces manual intervention to discover the missing evidence and re-score.
- **Evidence:** Lessons tail — "the audit lane can be STALE relative to the browser-qa lane. Here the QA agent failed to launch Chrome and SKIPPED all browser tests; the auditor (reading that QA report) wrote PASS_WITH_GAPS... But the separate browser-qa-agent then ran successfully... The evaluator must open `reports/phase-<iter>-ui-test-results.md` (the browser-qa-agent's own file) directly and not let the audit's characterization of a Chrome-down QA run stand in for it."
- **Sketch:** Before scoring any journey, have coherence-auditor check if `reports/phase-<iter>-ui-test-results.md` exists and contains positive evidence (screenshots, pass marks) that supersede the audit lane's own QA attempt. Emit a note in the audit report when this cross-check finds the parallel lane's evidence and upgrades the score.
- **Verify idea:** Run an iteration where the audit lane's Chrome fails but the parallel browser-qa-agent succeeds; verify the audit report now cites the parallel evidence and the final journey score reflects the pass, not the partial.

### RETRO-3 · Expose token telemetry for claude_usage events
- **Proposed:** P2 · Effort S · Risk LOW
- **Problem:** Token telemetry is unavailable in sessions ("no claude_usage events in telemetry.jsonl — token telemetry may be off"), making it impossible to profile cost/efficiency across agents or iterations. Only wall-time is visible, which obscures model-tier spend and token budgets.
- **Evidence:** Agent economics — "none recorded (no claude_usage events in telemetry.jsonl — token telemetry may be off)"
- **Sketch:** Ensure the telemetry collection pipeline (_on both Claude Code and OpenAI backends_) captures claude_usage events for every agent dispatch. Add a check in retro_collect.sh to warn if the ratio of dispatches to claude_usage events drops below 90%. Update `.claude/workflow.md` to document which agents must emit token telemetry.
- **Verify idea:** Run one full goal session and verify that `analyze_telemetry.py --json --token-profile` produces a per-agent and per-iteration token report matching the claude_usage event count.

### RETRO-4 · Reduce unattributed (glue) wall-time drift in full-depth iterations
- **Proposed:** P2 · Effort M · Risk MED
- **Problem:** Full-depth iterations show large unattributed wall-time blocks (403m in iter-1, 335m in iter-3, 226m in iter-7, 290m in iter-8), often exceeding the sum of named agents. These periods are opaque and prevent identifying where time is truly being spent or where infrastructure bottlenecks lie, especially when backend compute (edge-report, etc.) is involved.
- **Evidence:** Agent economics — "goal-tradable_wall-iter-1  depth=full  verdict=CONTINUE  wall=442.3m ... unattributed (glue)      403.0m" and iters 3, 6, 7, 8 also show 226m–335m unattributed blocks.
- **Sketch:** Instrument the iteration harness and goal-mode pump to emit sub-second telemetry events for pump_wait, inter-agent coordination delays, and backend-query blocks. Add a telemetry sink for "unattributed" periods that logs which agent(s) are inflight and what resource (network, compute, dispatch queue) they are blocked on. Update retro_collect.sh to report a breakdown of unattributed time.
- **Verify idea:** Re-run a full-depth iteration and verify that unattributed time is now ≤10% of total wall-time and each unattributed block is tagged with the blocking agent and resource type.

### RETRO-5 · Persist credentialed journeys' output artifacts in canonical store, not /tmp
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** Operator-credentialed journeys (e.g., Alpaca recording, edge-report compute) write their output to `/tmp`, which is garbage-collected between iterations. A lesson-tail entry describes this: credentials' headline reads as "met" in memory, but the actual artifacts are gone, forcing re-runs and masking whether a credentialed step actually succeeded.
- **Evidence:** Lessons tail — "verify credentialed-headline durability against the artifact, never memory — `ls apps/backend/.data/datasets/` showed the same 7 Jul-3 PG datasets with no AAPL/panel-symbol, contradicting the ambient 'J-03 headline MET (15 windows)' note (those datasets went to /tmp and were GC'd)."
- **Sketch:** Define a canonical output directory (`apps/backend/.data/credentialed-sessions/<session-id>/<journey-id>/`) for each operator-gated journey. Update the developer dispatch template to pass `TAPEOLOGY_CREDENTIALED_OUTPUT_DIR` to each credentialed builder. Add a post-build check in the evaluator to verify that the canonical directory contains the expected artifacts before scoring the journey as passing.
- **Verify idea:** Run an iteration with an Alpaca credentialed recording; verify that `ls apps/backend/.data/credentialed-sessions/tradable_wall/j-03/ | wc -l` shows 15+ dataset files after the iteration halts, and the evaluator cites the directory path in its evidence.
