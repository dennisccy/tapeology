# Goal Session Summary — yahoo_fetch

**Final verdict:** AWAITING_PUMP
**Total iterations:** 5
**Wall time (seconds):** 17414
**Quota pauses:** 0
**Started:** 2026-07-08T23:31:20.432118Z
**Finished:** 2026-07-10T18:18:40.203465Z

## Branch

This session pushed iteration commits to `goal/yahoo_fetch`. Open a PR with:

    gh pr create --base main --head goal/yahoo_fetch \
      --title "feat: yahoo_fetch — AWAITING_PUMP" \
      --body-file runs/goal-session-yahoo_fetch/summary.md

## Final journey state

| Journey | Status | Last passing iter |
|---|---|---|
| J-01 | passing | goal-yahoo_fetch-iter-4 |
| J-02 | passing | goal-yahoo_fetch-iter-4 |
| J-03 | passing | goal-yahoo_fetch-iter-4 |
| J-04 | passing | goal-yahoo_fetch-iter-4 |
| J-05 | failing | - |
| J-06 | passing | goal-yahoo_fetch-iter-4 |

## Anti-goal violations

(none)

## Telemetry

See `runs/goal-session-yahoo_fetch/telemetry.jsonl` for the structured event log.

## Iteration timing

```
== Wall-time report: session yahoo_fetch
  goal-yahoo_fetch-iter-0  depth=lean  verdict=CONTINUE  wall=26.5m
      developer                   11.7m  calls=1
      goal-evaluator               6.9m  calls=1
      goal-decomposer              5.9m  calls=1
      reviewer                     2.0m  calls=1
      pump-wait                  0.4m
      unattributed (glue)        0.1m
  goal-yahoo_fetch-iter-1  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             14.0m  calls=1
      readme-maintainer            8.8m  calls=1
      iteration-summarizer         5.2m  calls=1
      pump-wait                  5.2m
  goal-yahoo_fetch-iter-1  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-evaluator             360.1m  calls=1  failures=1
      coherence-auditor            4.3m  calls=1
      (resume-skipped: goal-decomposer)
      pump-wait                  0.2m
  goal-yahoo_fetch-iter-1  depth=full  verdict=CONTINUE  wall=18.4m
      goal-evaluator              10.7m  calls=1
      (resume-skipped: goal-decomposer, coherence-auditor)
      pump-wait                  0.1m
      unattributed (glue)        7.7m
  goal-yahoo_fetch-iter-2  depth=full  verdict=CONTINUE  wall=173.7m
      goal-evaluator              10.9m  calls=1
      iteration-summarizer         8.7m  calls=1
      goal-decomposer              8.7m  calls=1
      coherence-auditor            6.5m  calls=1
      readme-maintainer            4.7m  calls=1
      pump-wait                  0.6m
      unattributed (glue)      134.2m
  goal-yahoo_fetch-iter-3  depth=full  verdict=CONTINUE  wall=179.6m
      goal-evaluator              11.0m  calls=1
      iteration-summarizer         9.3m  calls=1
      goal-decomposer              9.3m  calls=1
      coherence-auditor            3.7m  calls=1
      readme-maintainer            3.2m  calls=1
      pump-wait                  0.4m
      unattributed (glue)      143.0m
  goal-yahoo_fetch-iter-4  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      iteration-summarizer         7.9m  calls=1
      goal-decomposer              7.9m  calls=1
      readme-maintainer            4.5m  calls=1
      pump-wait                  0.5m
  goal-yahoo_fetch-iter-4  depth=full  verdict=CONTINUE  wall=99.2m
      goal-evaluator               8.4m  calls=1
      coherence-auditor            3.4m  calls=1
      (resume-skipped: goal-decomposer)
      pump-wait                  0.1m
      unattributed (glue)       87.4m
  goal-yahoo_fetch-iter-5  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer            231.6m  calls=1  failures=1
      iteration-summarizer       231.6m  calls=1  failures=1
      pump-wait                463.1m
  goal-yahoo_fetch-iter-5  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer              9.4m  calls=1
      pump-wait                  0.1m
  goal-yahoo_fetch-iter-5  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      (resume-skipped: goal-decomposer)
  session: 5 completed iteration(s), mean wall 99.5m
      total goal-evaluator             408.1m
      total goal-decomposer            286.8m
      total iteration-summarizer       262.6m
      total readme-maintainer           21.3m
      total coherence-auditor           18.0m
      total developer                   11.7m
      total reviewer                     2.0m
      total AWAITING_PUMP paused gaps: 548.8m
      halts: AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP
```
