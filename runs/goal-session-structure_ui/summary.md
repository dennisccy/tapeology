# Goal Session Summary — structure_ui

**Final verdict:** GOAL_ACHIEVED
**Total iterations:** 5
**Wall time (seconds):** 39722
**Quota pauses:** 0
**Started:** 2026-07-06T23:02:41.903609Z
**Finished:** 2026-07-07T11:37:12.919720Z

## Branch

This session pushed iteration commits to `goal/structure_ui`. Open a PR with:

    gh pr create --base main --head goal/structure_ui \
      --title "feat: structure_ui — GOAL_ACHIEVED" \
      --body-file runs/goal-session-structure_ui/summary.md

## Final journey state

| Journey | Status | Last passing iter |
|---|---|---|
| J-01 | passing | goal-structure_ui-iter-4 |
| J-02 | passing | goal-structure_ui-iter-4 |
| J-03 | passing | goal-structure_ui-iter-4 |
| J-04 | already_passing | goal-structure_ui-iter-4 |

## Anti-goal violations

- [critical] Honest UI states only. No fabricated chart, level, zone, trade, fill, or PnL to force a green journey; every failure mode (no bar series, no levels, no zones, insufficient n, missing credentials, backend unreachable) surfaces an explicit, distinct state. (iter goal-structure_ui-iter-1)

## Telemetry

See `runs/goal-session-structure_ui/telemetry.jsonl` for the structured event log.

## Iteration timing

```
== Wall-time report: session structure_ui
  goal-structure_ui-iter-0  depth=lean  verdict=CONTINUE  wall=29.1m
      developer                   14.0m  calls=1
      goal-evaluator               6.8m  calls=1
      goal-decomposer              5.1m  calls=1
      reviewer                     3.2m  calls=1
      pump-wait                  0.4m
      unattributed (glue)        0.0m
  goal-structure_ui-iter-1  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer              6.7m  calls=1
      iteration-summarizer         6.5m  calls=1
      readme-maintainer            4.1m  calls=1
      pump-wait                  0.2m
  goal-structure_ui-iter-1  depth=full  verdict=CONTINUE  wall=134.3m
      goal-evaluator              11.0m  calls=1
      coherence-auditor            5.3m  calls=1
      (resume-skipped: goal-decomposer)
      pump-wait                  0.2m
      unattributed (glue)      118.0m
  goal-structure_ui-iter-2  depth=full  verdict=CONTINUE  wall=176.5m
      goal-decomposer              8.4m  calls=1
      goal-evaluator               8.3m  calls=1
      iteration-summarizer         8.2m  calls=1
      readme-maintainer            4.8m  calls=1
      coherence-auditor            4.0m  calls=1
      pump-wait                  0.4m
      unattributed (glue)      142.8m
  goal-structure_ui-iter-3  depth=full  verdict=CONTINUE  wall=173.3m
      goal-evaluator              11.5m  calls=1
      iteration-summarizer        10.2m  calls=1
      goal-decomposer             10.1m  calls=1
      readme-maintainer            8.0m  calls=1
      coherence-auditor            5.1m  calls=1
      pump-wait                  0.5m
      unattributed (glue)      128.5m
  goal-structure_ui-iter-4  depth=full  verdict=GOAL_ACHIEVED  wall=169.6m
      iteration-summarizer        16.3m  calls=2
      readme-maintainer            9.9m  calls=2
      goal-decomposer              8.8m  calls=1
      goal-evaluator               7.6m  calls=1
      coherence-auditor            2.7m  calls=1
      pump-wait                  0.4m
      unattributed (glue)      124.3m
  session: 5 completed iteration(s), mean wall 136.5m
      total goal-evaluator              45.2m
      total iteration-summarizer        41.1m
      total goal-decomposer             39.0m
      total readme-maintainer           26.8m
      total coherence-auditor           17.1m
      total developer                   14.0m
      total reviewer                     3.2m
      total AWAITING_PUMP paused gaps: 2.5m
      halts: AWAITING_PUMP
```
