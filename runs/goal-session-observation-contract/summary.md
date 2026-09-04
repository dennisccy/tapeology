# Goal Session Summary — observation-contract

**Final verdict:** AWAITING_PUMP
**Total iterations:** 3
**Wall time (seconds):** 9
**Quota pauses:** 0
**Started:** 2026-09-02T20:56:28.458337Z
**Finished:** 2026-09-03T21:14:41.160344Z

## Branch

This session pushed iteration commits to `goal/observation-contract`. Open a PR with:

    gh pr create --base main --head goal/observation-contract \
      --title "feat: observation-contract — AWAITING_PUMP" \
      --body-file runs/goal-session-observation-contract/summary.md

## Final journey state

| Journey | Status | Last passing iter |
|---|---|---|
| J-01 | partial | - |
| J-02 | partial | - |
| J-03 | failing | - |
| J-04 | failing | - |
| J-05 | failing | - |
| J-06 | partial | - |

## Anti-goal violations

(none)

## Telemetry

See `runs/goal-session-observation-contract/telemetry.jsonl` for the structured event log.

## Iteration timing

```
== Wall-time report: session observation-contract
  goal-observation-contract-iter-0  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer              0.0m  calls=1  failures=1
  goal-observation-contract-iter-0  depth=lean  verdict=CONTINUE  wall=63.9m
      reviewer                    29.3m  calls=1
      browser-qa-agent            28.4m  calls=1
      goal-evaluator               5.0m  calls=1
      goal-decomposer              0.8m  calls=1
      browser-qa-replay            0.6m  calls=1
      developer                    0.3m  calls=1
      [engine] lean-pipeline      58.1m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  0.4m
      overlap saved              0.5m  (parallel steps)
  goal-observation-contract-iter-1  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)
      reviewer                    24.2m  calls=1
      developer                   23.0m  calls=1
      goal-decomposer              8.9m  calls=1
      iteration-summarizer         2.5m  calls=1
      coherence-auditor            2.1m  calls=1
      browser-qa-replay            0.6m  calls=1
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  2.5m
  goal-observation-contract-iter-1  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)
      browser-qa-replay            0.6m  calls=1
      coherence-auditor            0.0m  calls=1  failures=1
      browser-qa-agent             0.0m  calls=1  failures=1
      [engine] lean-pipeline       0.7m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer, developer, reviewer)
      pump-wait                  0.0m
  goal-observation-contract-iter-1  depth=lean  verdict=CONTINUE  wall=31.1m
      goal-evaluator              20.2m  calls=1
      coherence-auditor           10.8m  calls=1
      browser-qa-agent            10.3m  calls=1
      browser-qa-replay            0.5m  calls=1
      [engine] lean-pipeline      10.8m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer, developer, reviewer, coherence-auditor)
      pump-wait                  0.1m
      overlap saved             10.8m  (parallel steps)
  goal-observation-contract-iter-2  depth=lean  verdict=CONTINUE  wall=182.5m
      coherence-auditor           50.3m  calls=1
      developer                   46.7m  calls=1
      goal-evaluator              39.9m  calls=1
      browser-qa-agent            20.4m  calls=1
      reviewer                    20.1m  calls=1
      goal-decomposer             10.4m  calls=1
      demo-narrator               10.3m  calls=1
      iteration-summarizer        10.2m  calls=1
      browser-qa-replay            0.5m  calls=1
      [engine] lean-pipeline     117.1m  (contains agent time above)
      [engine] showcase-join      15.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  0.3m
      OVER BUDGET at browser-qa: 5540s > 3600s (mode=trim)
      overlap saved             26.2m  (parallel steps)
  goal-observation-contract-iter-3  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)
  goal-observation-contract-iter-3  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer            360.1m  calls=1  failures=1
      pump-wait                  0.0m
  goal-observation-contract-iter-3  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)
  goal-observation-contract-iter-3  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer              0.1m  calls=1  failures=1
      pump-wait                  0.1m
  session: 3 completed iteration(s), mean wall 92.5m
      total goal-decomposer            380.1m
      total reviewer                    73.6m
      total developer                   70.1m
      total goal-evaluator              65.0m
      total coherence-auditor           63.2m
      total browser-qa-agent            59.1m
      total iteration-summarizer        12.7m
      total demo-narrator               10.3m
      total browser-qa-replay            2.7m
      total AWAITING_PUMP paused gaps: 6.5m
      halts: AWAITING_PUMP, machine_reset, AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP
```
