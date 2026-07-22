# Session retro — fast_wall

> **PROPOSALS ONLY** — a human promotes candidates into docs/improvement-roadmap.md §16
> per EVO-1; nothing here is scheduled work.

**Session:** fast_wall · **Terminal status:** GOAL_ACHIEVED · **Iterations:** 7

## Candidate items

### RETRO-1 · Eliminate "unattributed (glue)" wall-time blind spot in telemetry
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** Every iteration reports large "unattributed (glue)" time segments (ranging 135–221 minutes per iteration), accounting for ~73% of total session wall time. These blind spots make it impossible to diagnose where wall time is actually spent; future sessions cannot tell whether it is legitimate pump/pipeline delays or instrumentation gaps.
- **Evidence:** Agent economics (wall breakdown) — "unattributed (glue)" spans: "220.7m" (iter-1), "150.9m" (iter-2), "135.2m" (iter-3), "176.5m" (iter-4), "163.5m" (iter-5), "147.9m" (iter-6); session mean 195.2m per iteration with ~73% unattributed.
- **Sketch:** Extend telemetry collection to track inter-agent wait states, subagent dispatch overhead, and pump-internal scheduling delays. Add named "wait/dispatch/scheduling" categories to the wall-time breakdown so implementers can distinguish legitimate queue time from true instrumentation gaps. Emit interim telemetry events (not just iter_end) to capture the full lifecycle.
- **Verify idea:** Run a goal-session and confirm that "unattributed (glue)" time shrinks to <10% of total, with new named categories accounting for the rest.

