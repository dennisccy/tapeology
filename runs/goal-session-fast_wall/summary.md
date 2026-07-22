# Goal Session Summary — fast_wall

**Final verdict:** GOAL_ACHIEVED
**Total iterations:** 7
**Wall time (seconds):** 82452
**Quota pauses:** 0
**Started:** 2026-07-16T23:29:02.432422Z
**Finished:** 2026-07-17T23:07:50.521411Z

## Branch

This session pushed iteration commits to `goal/fast_wall`. Open a PR with:

    gh pr create --base main --head goal/fast_wall \
      --title "feat: fast_wall — GOAL_ACHIEVED" \
      --body-file runs/goal-session-fast_wall/summary.md

## Final journey state

| Journey | Status | Last passing iter |
|---|---|---|
| J-01 | passing | goal-fast_wall-iter-6 |
| J-02 | passing | goal-fast_wall-iter-6 |
| J-03 | passing | goal-fast_wall-iter-6 |
| J-04 | passing | goal-fast_wall-iter-6 |
| J-05 | passing | goal-fast_wall-iter-6 |
| J-06 | passing | goal-fast_wall-iter-6 |
| J-07 | passing | goal-fast_wall-iter-6 |

## Anti-goal violations

(none)

## Telemetry

See `runs/goal-session-fast_wall/telemetry.jsonl` for the structured event log.

## Iteration timing

```
== Wall-time report: session fast_wall
  goal-fast_wall-iter-0  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)
      developer                   31.4m  calls=1
      goal-decomposer              9.6m  calls=1
      reviewer                     0.0m  calls=1  failures=1
      pump-wait                  0.7m
  goal-fast_wall-iter-0  depth=lean  verdict=CONTINUE  wall=41.5m
      browser-qa-agent            30.6m  calls=1
      goal-evaluator               7.0m  calls=1
      reviewer                     3.7m  calls=1
      (resume-skipped: goal-decomposer, developer)
      pump-wait                  0.3m
      unattributed (glue)        0.1m
  goal-fast_wall-iter-1  depth=full  verdict=CONTINUE  wall=247.6m
      goal-decomposer             14.7m  calls=1
      goal-evaluator               8.1m  calls=1
      coherence-auditor            4.1m  calls=1
      pump-wait                 17.9m
      unattributed (glue)      220.7m
  goal-fast_wall-iter-2  depth=full  verdict=CONTINUE  wall=196.3m
      goal-decomposer             12.9m  calls=1
      iteration-summarizer        12.9m  calls=1
      goal-evaluator              11.1m  calls=1
      readme-maintainer            4.4m  calls=1
      coherence-auditor            4.2m  calls=1
      pump-wait                  2.2m
      unattributed (glue)      150.9m
  goal-fast_wall-iter-3  depth=full  verdict=CONTINUE  wall=180.0m
      goal-decomposer             12.5m  calls=1
      iteration-summarizer        12.5m  calls=1
      goal-evaluator               9.6m  calls=1
      coherence-auditor            6.5m  calls=1
      readme-maintainer            3.8m  calls=1
      pump-wait                  0.7m
      unattributed (glue)      135.2m
  goal-fast_wall-iter-4  depth=full  verdict=CONTINUE  wall=236.8m
      goal-decomposer             18.0m  calls=1
      iteration-summarizer        18.0m  calls=1
      goal-evaluator              13.5m  calls=1
      coherence-auditor            6.8m  calls=1
      readme-maintainer            4.0m  calls=1
      pump-wait                  2.3m
      unattributed (glue)      176.5m
  goal-fast_wall-iter-5  depth=full  verdict=CONTINUE  wall=244.7m
      iteration-summarizer        30.4m  calls=1
      goal-decomposer             30.3m  calls=1
      goal-evaluator              11.4m  calls=1
      coherence-auditor            5.7m  calls=1
      readme-maintainer            3.4m  calls=1
      pump-wait                  8.1m
      unattributed (glue)      163.5m
  goal-fast_wall-iter-6  depth=full  verdict=GOAL_ACHIEVED  wall=219.3m
      iteration-summarizer        28.6m  calls=2
      goal-decomposer             20.5m  calls=1
      goal-evaluator              10.0m  calls=1
      readme-maintainer            7.0m  calls=2
      coherence-auditor            5.2m  calls=1
      pump-wait                  1.8m
      unattributed (glue)      147.9m
  session: 7 completed iteration(s), mean wall 195.2m
      total goal-decomposer            118.6m
      total iteration-summarizer       102.3m
      total goal-evaluator              70.7m
      total coherence-auditor           32.6m
      total developer                   31.4m
      total browser-qa-agent            30.6m
      total readme-maintainer           22.5m
      total reviewer                     3.7m
      total AWAITING_PUMP paused gaps: 3.5m
      halts: AWAITING_PUMP
```
