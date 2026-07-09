# Goal Session Summary — yahoo_fetch

**Final verdict:** AWAITING_PUMP
**Total iterations:** 1
**Wall time (seconds):** 26550
**Quota pauses:** 0
**Started:** 2026-07-08T23:31:20.432118Z
**Finished:** 2026-07-09T09:00:08.569691Z

## Branch

This session pushed iteration commits to `goal/yahoo_fetch`. Open a PR with:

    gh pr create --base main --head goal/yahoo_fetch \
      --title "feat: yahoo_fetch — AWAITING_PUMP" \
      --body-file runs/goal-session-yahoo_fetch/summary.md

## Final journey state

| Journey | Status | Last passing iter |
|---|---|---|
| J-01 | failing | - |
| J-02 | failing | - |
| J-03 | failing | - |
| J-04 | failing | - |
| J-05 | failing | - |
| J-06 | already_passing | goal-yahoo_fetch-iter-0 |

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
  session: 1 completed iteration(s), mean wall 26.5m
      total goal-evaluator             367.0m
      total goal-decomposer             19.9m
      total developer                   11.7m
      total readme-maintainer            8.8m
      total iteration-summarizer         5.2m
      total coherence-auditor            4.3m
      total reviewer                     2.0m
      total AWAITING_PUMP paused gaps: 4.1m
      halts: AWAITING_PUMP, AWAITING_PUMP
```
