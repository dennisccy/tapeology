# Goal Session Summary — observation-contract

**Final verdict:** AWAITING_PUMP
**Total iterations:** 1
**Wall time (seconds):** 49
**Quota pauses:** 0
**Started:** 2026-09-02T20:56:28.458337Z
**Finished:** 2026-09-03T06:48:39.202135Z

## Branch

This session pushed iteration commits to `goal/observation-contract`. Open a PR with:

    gh pr create --base main --head goal/observation-contract \
      --title "feat: observation-contract — AWAITING_PUMP" \
      --body-file runs/goal-session-observation-contract/summary.md

## Final journey state

| Journey | Status | Last passing iter |
|---|---|---|
| J-01 | failing | - |
| J-02 | failing | - |
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
  session: 1 completed iteration(s), mean wall 63.9m
      total reviewer                    53.5m
      total browser-qa-agent            28.4m
      total developer                   23.4m
      total goal-decomposer              9.7m
      total goal-evaluator               5.0m
      total iteration-summarizer         2.5m
      total coherence-auditor            2.1m
      total browser-qa-replay            1.7m
      total AWAITING_PUMP paused gaps: 5.0m
      halts: AWAITING_PUMP, machine_reset, AWAITING_PUMP
```
