# Session retro — tradable_wall

> **PROPOSALS ONLY** — a human promotes candidates into docs/improvement-roadmap.md §16
> per EVO-1; nothing here is scheduled work.

**Session:** tradable_wall · **Terminal status:** STALLED · **Iterations:** 8

## Candidate items

### RETRO-1 · Unattributed wall-time visibility
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** Each iteration's wall-time breakdown shows 50–85% of total time labeled "unattributed (glue)" — making it impossible to understand where dispatch overhead, pump waits, network latency, or other cross-agent friction actually lives. This recurs across all 8 iterations.
- **Evidence:** Agent economics — "unattributed (glue)" hours in every iteration: iter-1 403.0m/442.3m, iter-2 123.2m/161.9m, iter-3 335.8m/379.8m, iter-4 181.0m/214.8m, iter-5 132.8m/178.8m, iter-6 195.6m/235.5m, iter-7 226.0m/290.7m.
- **Sketch:** Instrument analyze_telemetry.py's wall-time accounting to partition the "glue" bucket into named categories (pump-dispatch latency, inter-agent queue waits, network roundtrips, startup/GC). Add trace markers at pump dispatch boundaries and agent start/end to close the gap. Export per-category summaries in the wall-time report.
- **Verify idea:** A rerun of any goal-mode session shows zero or minimal "unattributed (glue)" time, with named latency sources summing to the original glue-bucket total.

### RETRO-2 · Missing token telemetry
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** Token usage and cost data are not being recorded despite Claude API calls in every iteration. The agent-economics section reports "no claude_usage events in telemetry.jsonl — token telemetry may be off", leaving every session without evidence of model costs or token-efficiency trends.
- **Evidence:** Agent economics — "none recorded (no claude_usage events in telemetry.jsonl — token telemetry may be off)"
- **Sketch:** Verify that claude_usage telemetry hooks are wired into the pump's dispatch client, and that dispatch.py logs token counts from every API response. Add a validation step (at session init or retro-collect time) that warns if claude_usage events are missing or sparse.
- **Verify idea:** A rerun of any goal-mode session exports per-agent and per-iteration claude_usage events with input/output token counts, and the retro report includes an Agent economics table with token totals and cost estimates.
