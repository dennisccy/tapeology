# Goal Session Summary — tradable_wall

**Final verdict:** STALLED
**Total iterations:** 8
**Wall time (seconds):** 117498
**Quota pauses:** 0
**Started:** 2026-07-14T00:14:12.002869Z
**Finished:** 2026-07-15T08:52:31.549372Z

## Branch

This session pushed iteration commits to `goal/tradable_wall`. Open a PR with:

    gh pr create --base main --head goal/tradable_wall \
      --title "feat: tradable_wall — STALLED" \
      --body-file runs/goal-session-tradable_wall/summary.md

## Final journey state

| Journey | Status | Last passing iter |
|---|---|---|
| J-01 | passing | goal-tradable_wall-iter-7 |
| J-02 | passing | goal-tradable_wall-iter-7 |
| J-03 | partial | - |
| J-04 | passing | goal-tradable_wall-iter-7 |
| J-05 | passing | goal-tradable_wall-iter-7 |
| J-06 | passing | goal-tradable_wall-iter-7 |
| J-07 | already_passing | goal-tradable_wall-iter-7 |

## Anti-goal violations

(none)

## Telemetry

See `runs/goal-session-tradable_wall/telemetry.jsonl` for the structured event log.

## Iteration timing

```
== Wall-time report: session tradable_wall
  goal-tradable_wall-iter-0  depth=lean  verdict=CONTINUE  wall=54.1m
      developer                   18.8m  calls=1
      browser-qa-agent            15.0m  calls=1
      goal-evaluator               8.4m  calls=1
      goal-decomposer              6.7m  calls=1
      reviewer                     5.0m  calls=1
      pump-wait                  2.0m
      unattributed (glue)        0.1m
  goal-tradable_wall-iter-1  depth=full  verdict=CONTINUE  wall=442.3m
      goal-decomposer             13.6m  calls=1
      goal-evaluator              10.8m  calls=1
      iteration-summarizer         6.5m  calls=1
      coherence-auditor            4.8m  calls=1
      readme-maintainer            3.7m  calls=1
      pump-wait                  2.3m
      unattributed (glue)      403.0m
  goal-tradable_wall-iter-2  depth=full  verdict=CONTINUE  wall=161.9m
      goal-evaluator              12.6m  calls=1
      iteration-summarizer         8.9m  calls=1
      goal-decomposer              8.9m  calls=1
      coherence-auditor            4.4m  calls=1
      readme-maintainer            3.9m  calls=1
      pump-wait                  0.3m
      unattributed (glue)      123.2m
  goal-tradable_wall-iter-3  depth=full  verdict=CONTINUE  wall=379.8m
      goal-decomposer             12.1m  calls=1
      iteration-summarizer        12.0m  calls=1
      goal-evaluator              10.6m  calls=1
      coherence-auditor            4.9m  calls=1
      readme-maintainer            4.4m  calls=1
      pump-wait                  0.4m
      unattributed (glue)      335.8m
  goal-tradable_wall-iter-4  depth=full  verdict=CONTINUE  wall=214.8m
      goal-evaluator              10.2m  calls=1
      goal-decomposer              8.2m  calls=1
      iteration-summarizer         7.7m  calls=1
      coherence-auditor            3.9m  calls=1
      readme-maintainer            3.8m  calls=1
      pump-wait                  0.7m
      unattributed (glue)      181.0m
  goal-tradable_wall-iter-5  depth=full  verdict=CONTINUE  wall=178.8m
      goal-evaluator              13.5m  calls=1
      goal-decomposer             11.9m  calls=1
      iteration-summarizer         7.9m  calls=1
      readme-maintainer            7.3m  calls=1
      coherence-auditor            5.3m  calls=1
      pump-wait                  4.2m
      unattributed (glue)      132.8m
  goal-tradable_wall-iter-6  depth=full  verdict=CONTINUE  wall=235.5m
      goal-evaluator              10.4m  calls=1
      goal-decomposer              9.8m  calls=1
      coherence-auditor            7.1m  calls=1
      readme-maintainer            6.6m  calls=1
      iteration-summarizer         6.0m  calls=1
      pump-wait                  4.0m
      unattributed (glue)      195.6m
  goal-tradable_wall-iter-7  depth=full  verdict=STALLED  wall=290.7m
      iteration-summarizer        17.6m  calls=2
      readme-maintainer           16.3m  calls=2
      goal-evaluator              13.2m  calls=1
      goal-decomposer             11.5m  calls=1
      coherence-auditor            6.1m  calls=1
      pump-wait                  3.7m
      unattributed (glue)      226.0m
  session: 8 completed iteration(s), mean wall 244.7m
      total goal-evaluator              89.7m
      total goal-decomposer             82.6m
      total iteration-summarizer        66.7m
      total readme-maintainer           45.9m
      total coherence-auditor           36.6m
      total developer                   18.8m
      total browser-qa-agent            15.0m
      total reviewer                     5.0m
      halts: STALLED
```
