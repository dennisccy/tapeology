# Goal Session Summary — rapid-microscope

**Final verdict:** AWAITING_PUMP
**Total iterations:** 17
**Wall time (seconds):** 8
**Quota pauses:** 0
**Started:** 2026-08-16T22:25:35.904129Z
**Finished:** 2026-08-20T08:10:27.501297Z

## Branch

This session pushed iteration commits to `goal/rapid-microscope`. Open a PR with:

    gh pr create --base main --head goal/rapid-microscope \
      --title "feat: rapid-microscope — AWAITING_PUMP" \
      --body-file runs/goal-session-rapid-microscope/summary.md

## Final journey state

| Journey | Status | Last passing iter |
|---|---|---|
| J-01 | passing | goal-rapid-microscope-iter-16 |
| J-02 | passing | goal-rapid-microscope-iter-16 |
| J-03 | passing | goal-rapid-microscope-iter-16 |
| J-04 | passing | goal-rapid-microscope-iter-16 |
| J-05 | passing | goal-rapid-microscope-iter-16 |
| J-06 | partial | - |
| J-07 | passing | goal-rapid-microscope-iter-16 |
| J-08 | passing | goal-rapid-microscope-iter-16 |
| J-09 | failing | - |
| J-10 | partial | - |

## Anti-goal violations

- [critical] No cross-unit liquidity arithmetic. No feature, screen, or study relates trade shares to displayed quote sizes unless the dataset's `quote_size_unit` is verified (spec §2.6); unverified or mixed units are a typed refusal. (critical) (iter goal-rapid-microscope-iter-2)
- [critical] No value is served before it exists. Every feature carries `anchor_at`/`observed_through`/`available_at`; a deferred construct is `unavailable` until its observations exist (TR-17). (critical) (iter goal-rapid-microscope-iter-2)
- [minor] No lookahead — every value computed as-of T uses only events/bars fully completed at T. (critical) (iter goal-rapid-microscope-iter-2)
- [critical] The denominator never shrinks. Every evaluated variant lands in the hash-chained ledger with a closed-vocabulary decision; kills are never deleted; the union-N across grid versions is served beside every family. (critical) (iter goal-rapid-microscope-iter-4)
- [critical] No threshold, grid, formula, embargo, or fold parameter is chosen or revised from validation, sealed, or holdout outcomes. (critical) (iter goal-rapid-microscope-iter-4)
- [critical] The denominator never shrinks ... kills are never deleted; the union-N across grid versions is served beside every family. (critical) (iter goal-rapid-microscope-iter-5)
- [critical] No threshold, grid, formula, embargo, or fold parameter is chosen or revised from validation, sealed, or holdout outcomes. Fitting rules are data functionals frozen before reveal. (critical) (iter goal-rapid-microscope-iter-5)
- [critical] The accessor is the only data door. No module but `micro_accessor.py` opens snapshot or vault event data; origin fences fail closed; import-ban and source-scan guards enforce it. (critical) (iter goal-rapid-microscope-iter-5)
- [minor] The 12 pre-existing tick symbol-days are permanently exploratory — never sealed, never `historical_oos`, never relabeled. (critical) (iter goal-rapid-microscope-iter-5)
- [minor] Trap T-7 · Insufficient is an answer. Floors never loosen; a below-floor fold serves `insufficient` with its arithmetic; the tick family's refusal at today's corpus is a FEATURE and is pinned by TR-15. (iter goal-rapid-microscope-iter-5)
- [minor] The 12 pre-existing tick symbol-days are permanently exploratory - never sealed, never `historical_oos`, never relabeled. (critical) (iter goal-rapid-microscope-iter-6)
- [minor] No exploratory read of a sealed shard / the 12 pre-existing tick symbol-days are permanently exploratory. (critical) (iter goal-rapid-microscope-iter-6)
- [critical] Immutable data — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. (critical) (iter goal-rapid-microscope-iter-7)
- [minor] No fold geometry change after fold 1 without a recorded voiding event that clears every survivor state of that corpus-era. (critical) (iter goal-rapid-microscope-iter-7)
- [minor] Rapid-validation spec §2.6: `quote_size_unit` is stamped from the dated vendor rule — "the recorder records the rule text + the verification note beside the stamp". (feeds the critical 'No cross-unit liquidity arithmetic' rail) (iter goal-rapid-microscope-iter-8)
- [minor] No exploratory read of a sealed shard. Event data and outcome aggregates of a `sealed` shard are refused everywhere (routes, MCP, accessor, readiness) until its recorded exposure; the refusal is typed, tested, and FAIL-CLOSED. (critical) (iter goal-rapid-microscope-iter-9)
- [minor] A recorded tranche is one opaque research pool until its shards are exposed ... no complete per-shard list of EITHER side while any pool member is unexposed. (critical — spec r5) (iter goal-rapid-microscope-iter-9)
- [minor] Frozen foundations — every `referee_*` module is byte-identical this era (SHA-256 listing recorded at iteration 0 and re-checked). (critical) — in collision with spec r4's "every corpus-wide enumerator EXCLUDES withheld shards". (iter goal-rapid-microscope-iter-9)
- [minor] Constraints — "The spec is canonical. Ambiguous or unimplementable => DROP the procedure from the iteration, record the drop, surface for an owner ruling — never improvise." (feeds the critical 'Sealed exposure is family-level and single-shot' and 'Evidence classes never mix' rails) (iter goal-rapid-microscope-iter-10)
- [minor] A recorded tranche is one opaque research pool until its shards are exposed ... Unexposed pool members stay mutually indistinguishable. (critical — spec r5/r7) (iter goal-rapid-microscope-iter-11)
- [minor] A recorded tranche is one opaque research pool until its shards are exposed ... Unexposed pool members stay mutually indistinguishable (critical - spec r5); and spec r6 section 7.8's governing invariant, 'unknown exposure history may never be read as never exposed'. (iter goal-rapid-microscope-iter-12)
- [minor] Sealed exposure is family-level and single-shot — never a second draw. No more than one evaluation per (family, shard) exists, ever ... *(critical)* / No exploratory read of a sealed shard *(critical)* — reached not through a product route but through the vault ledger's own on-disk representation. (iter goal-rapid-microscope-iter-13)
- [minor] T-10 - Evidence honesty. No screenshot => `unknown`, never `passing`; below-the-fold sections need element captures; operator acts are reported run-or-not-run. (iter goal-rapid-microscope-iter-14)
- [minor] A recorded tranche is one opaque research pool until its shards are exposed. ... The governing test is the TR-2 inference trap: given the registered universe plus every public artifact, no still-unexposed vault-eligible shard is identifiable with certainty. (critical - spec r5) (iter goal-rapid-microscope-iter-15)
- [minor] Constraints -- 'Guard tests are extended, never edited' / this era's own leakage-trap discipline: a guard that cannot be shown to fail proves nothing. (supporting the critical anti-goal 'Single source of truth' / 'no client-side arithmetic on a served numeric') (iter goal-rapid-microscope-iter-15)
- [minor] Constraints -- 'T-10 Evidence honesty. No screenshot => unknown, never passing; operator acts are reported run-or-not-run' (supporting the critical 'Deterministic and reproducible' / record-integrity rails) (iter goal-rapid-microscope-iter-16)
- [minor] Foundation invariants -- 'honest uncertainty' / no overclaiming of protection (supporting the critical 'The accessor is the only data door. ... origin fences fail closed') (iter goal-rapid-microscope-iter-16)

## Telemetry

See `runs/goal-session-rapid-microscope/telemetry.jsonl` for the structured event log.

## Iteration timing

```
== Wall-time report: session rapid-microscope
  goal-rapid-microscope-iter-0  depth=lean  verdict=CONTINUE  wall=48.6m
      developer                   14.1m  calls=1
      browser-qa-agent            11.3m  calls=1
      goal-decomposer              8.6m  calls=1
      reviewer                     8.0m  calls=1
      goal-evaluator               6.5m  calls=1
      browser-qa-replay            0.5m  calls=1
      [engine] lean-pipeline      33.6m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  0.5m
      overlap saved              0.4m  (parallel steps)
  goal-rapid-microscope-iter-1  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)
      developer                   49.0m  calls=1
      demo-narrator               16.8m  calls=1
      goal-decomposer             15.8m  calls=1
      iteration-summarizer         8.6m  calls=1
      readme-maintainer            1.3m  calls=1
      reviewer                     0.0m  calls=1  failures=1
      [engine] lean-pipeline      49.0m  (contains agent time above)
      [engine] showcase-join      11.0m  (contains agent time above)
      pump-wait                 16.1m
  goal-rapid-microscope-iter-1  depth=lean  verdict=ESCALATE  wall=44.0m
      browser-qa-agent            18.1m  calls=1
      reviewer                    13.3m  calls=1
      goal-evaluator              12.4m  calls=1
      coherence-auditor            6.6m  calls=1
      browser-qa-replay            0.5m  calls=1
      [engine] lean-pipeline      31.6m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer, developer, coherence-auditor)
      pump-wait                  0.3m
      overlap saved              7.0m  (parallel steps)
  goal-rapid-microscope-iter-2  depth=full  verdict=CONTINUE  wall=285.7m
      developer                  121.5m  calls=2
      auditor                     40.0m  calls=1
      browser-qa-agent            28.1m  calls=1
      reviewer                    24.0m  calls=2
      demo-narrator               22.9m  calls=2
      goal-decomposer             18.8m  calls=1
      goal-evaluator              15.6m  calls=1
      qa                          13.4m  calls=1
      ui-impact-analyst           10.4m  calls=1
      iteration-summarizer         7.2m  calls=1
      orchestrator                 6.0m  calls=1
      coherence-auditor            5.8m  calls=1
      readme-maintainer            1.9m  calls=1
      [engine] full-pipeline     234.0m  (contains agent time above)
      [engine] showcase-join      11.6m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                 32.4m
      OVER BUDGET at post-dev-fanout: 10921s > 3600s (mode=trim)
      overlap saved             30.0m  (parallel steps)
  goal-rapid-microscope-iter-3  depth=lean  verdict=ESCALATE  wall=112.3m
      developer                   49.7m  calls=1
      goal-evaluator              19.9m  calls=1
      goal-decomposer             18.4m  calls=1
      browser-qa-agent            13.2m  calls=1
      reviewer                    11.0m  calls=1
      iteration-summarizer         7.2m  calls=1
      coherence-auditor            5.8m  calls=1
      browser-qa-replay            0.5m  calls=1
      [engine] lean-pipeline      74.0m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  0.8m
      OVER BUDGET at browser-qa: 4747s > 3600s (mode=trim)
      overlap saved             13.4m  (parallel steps)
  goal-rapid-microscope-iter-4  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      reviewer                   248.5m  calls=1  failures=1
      developer                  111.5m  calls=1
      goal-decomposer             13.2m  calls=1
      iteration-summarizer         7.1m  calls=1
      orchestrator                 6.4m  calls=1
      [engine] full-pipeline     366.5m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                248.7m
  goal-rapid-microscope-iter-4  depth=full  verdict=ESCALATE  wall=117.3m
      auditor                     44.8m  calls=1
      reviewer                    31.9m  calls=1
      goal-evaluator              20.9m  calls=1
      qa                          14.8m  calls=1
      coherence-auditor            4.8m  calls=1
      [engine] full-pipeline      91.6m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
      pump-wait                  0.7m
      OVER BUDGET at coherence-auditor: 5496s > 3600s (mode=trim)
      unattributed (glue)        0.1m  (wall − agents(active) − quota)
  goal-rapid-microscope-iter-5  depth=full  verdict=ESCALATE  wall=188.3m
      developer                   72.3m  calls=1
      auditor                     37.4m  calls=1
      goal-evaluator              20.3m  calls=1
      goal-decomposer             17.9m  calls=1
      reviewer                    16.9m  calls=1
      qa                          13.0m  calls=1
      iteration-summarizer        10.2m  calls=1
      orchestrator                 5.2m  calls=1
      coherence-auditor            5.0m  calls=1
      [engine] full-pipeline     145.0m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  0.6m
      OVER BUDGET at post-dev-fanout: 6743s > 3600s (mode=trim)
      overlap saved             10.0m  (parallel steps)
  goal-rapid-microscope-iter-6  depth=full  verdict=ESCALATE  wall=149.7m
      developer                   31.8m  calls=1
      browser-qa-agent            26.7m  calls=1
      goal-evaluator              22.8m  calls=1
      qa                          21.3m  calls=1
      auditor                     20.9m  calls=1
      goal-decomposer             14.4m  calls=1
      reviewer                    12.7m  calls=1
      iteration-summarizer         9.3m  calls=1
      ui-impact-analyst            7.3m  calls=1
      orchestrator                 7.2m  calls=1
      coherence-auditor            3.5m  calls=1
      demo-narrator                1.8m  calls=1
      [engine] full-pipeline     109.0m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                 21.9m
      OVER BUDGET at post-dev-fanout: 3973s > 3600s (mode=trim)
      overlap saved             30.0m  (parallel steps)
  goal-rapid-microscope-iter-7  depth=full  verdict=CONTINUE  wall=164.9m
      developer                   34.2m  calls=1
      auditor                     25.4m  calls=1
      qa                          24.6m  calls=1
      browser-qa-agent            24.4m  calls=1
      goal-evaluator              23.6m  calls=1
      reviewer                    19.6m  calls=1
      goal-decomposer             17.3m  calls=1
      iteration-summarizer         8.8m  calls=1
      ui-impact-analyst            8.0m  calls=1
      orchestrator                 5.8m  calls=1
      coherence-auditor            4.1m  calls=1
      demo-narrator                1.7m  calls=1
      [engine] full-pipeline     119.9m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                 25.0m
      OVER BUDGET at post-dev-fanout: 4621s > 3600s (mode=trim)
      overlap saved             32.5m  (parallel steps)
  goal-rapid-microscope-iter-8  depth=lean  verdict=ESCALATE  wall=153.7m
      developer                   70.1m  calls=1
      goal-decomposer             30.4m  calls=1
      goal-evaluator              27.8m  calls=1
      reviewer                    17.9m  calls=1
      iteration-summarizer         9.5m  calls=1
      browser-qa-agent             7.2m  calls=1
      coherence-auditor            5.0m  calls=1
      browser-qa-replay            0.9m  calls=1
      [engine] lean-pipeline      95.3m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                 10.1m
      OVER BUDGET at browser-qa: 7115s > 3600s (mode=trim)
      overlap saved             15.2m  (parallel steps)
  goal-rapid-microscope-iter-9  depth=full  verdict=CONTINUE  wall=764.8m
      developer                  498.6m  calls=3
      auditor                     95.3m  calls=3
      reviewer                    46.5m  calls=3
      qa                          38.9m  calls=2
      browser-qa-agent            30.6m  calls=1
      coherence-auditor           24.3m  calls=1
      goal-evaluator              22.5m  calls=1
      goal-decomposer             15.3m  calls=1
      iteration-summarizer         7.9m  calls=1
      ui-impact-analyst            7.8m  calls=1
      orchestrator                 7.7m  calls=1
      demo-narrator                3.1m  calls=1
      [engine] full-pipeline     702.5m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                493.6m
      OVER BUDGET at post-dev-fanout: 5963s > 3600s (mode=trim)
      overlap saved             33.9m  (parallel steps)
  goal-rapid-microscope-iter-10  depth=lean  verdict=ESCALATE  wall=318.6m
      developer                  260.8m  calls=1
      goal-evaluator              18.1m  calls=1
      goal-decomposer             16.9m  calls=1
      reviewer                    13.3m  calls=1
      browser-qa-agent             9.3m  calls=1
      iteration-summarizer         8.1m  calls=1
      coherence-auditor            4.0m  calls=1
      browser-qa-replay            1.0m  calls=1
      [engine] lean-pipeline     283.4m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  7.3m
      OVER BUDGET at browser-qa: 17465s > 3600s (mode=trim)
      overlap saved             13.0m  (parallel steps)
  goal-rapid-microscope-iter-11  depth=full  verdict=CONTINUE  wall=621.2m
      coherence-auditor          349.1m  calls=1
      iteration-summarizer        98.7m  calls=1
      goal-decomposer             98.7m  calls=1
      developer                   58.1m  calls=1
      browser-qa-agent            27.1m  calls=1
      auditor                     26.0m  calls=1
      qa                          20.1m  calls=1
      goal-evaluator              19.9m  calls=1
      reviewer                    18.2m  calls=1
      ui-impact-analyst           10.7m  calls=1
      orchestrator                 9.3m  calls=1
      demo-narrator                2.8m  calls=1
      [engine] full-pipeline     153.3m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: test-plan, ui-test-design, ux-regression)
      pump-wait                 25.1m
      OVER BUDGET at post-dev-fanout: 11070s > 3600s (mode=trim)
      overlap saved            117.7m  (parallel steps)
  goal-rapid-microscope-iter-12  depth=lean  verdict=ESCALATE  wall=165.1m
      developer                   78.4m  calls=1
      reviewer                    30.3m  calls=1
      goal-evaluator              24.6m  calls=1
      goal-decomposer             19.7m  calls=1
      browser-qa-agent            12.0m  calls=1
      iteration-summarizer         7.9m  calls=1
      coherence-auditor            6.3m  calls=1
      browser-qa-replay            0.7m  calls=1
      [engine] lean-pipeline     120.8m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  0.3m
      OVER BUDGET at browser-qa: 7708s > 3600s (mode=trim)
      overlap saved             14.7m  (parallel steps)
  goal-rapid-microscope-iter-13  depth=full  verdict=ESCALATE  wall=351.7m
      developer                  168.1m  calls=2
      browser-qa-agent            54.0m  calls=1
      reviewer                    39.3m  calls=2
      auditor                     29.1m  calls=1
      qa                          22.6m  calls=1
      goal-evaluator              20.3m  calls=1
      goal-decomposer             19.4m  calls=1
      iteration-summarizer         9.2m  calls=1
      ui-impact-analyst            7.6m  calls=1
      orchestrator                 6.3m  calls=1
      coherence-auditor            5.0m  calls=1
      demo-narrator                1.6m  calls=1
      [engine] full-pipeline     306.9m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                 79.7m
      OVER BUDGET at post-dev-fanout: 14000s > 3600s (mode=trim)
      overlap saved             30.9m  (parallel steps)
  goal-rapid-microscope-iter-14  depth=full  verdict=ESCALATE  wall=215.3m
      developer                   55.8m  calls=1
      browser-qa-agent            38.1m  calls=1
      qa                          29.2m  calls=1
      auditor                     28.5m  calls=1
      goal-evaluator              25.2m  calls=1
      reviewer                    19.3m  calls=1
      goal-decomposer             15.3m  calls=1
      coherence-auditor           11.4m  calls=1
      ui-impact-analyst           10.6m  calls=1
      iteration-summarizer        10.2m  calls=1
      orchestrator                 8.1m  calls=1
      demo-narrator                2.4m  calls=1
      [engine] full-pipeline     163.3m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                 29.7m
      OVER BUDGET at post-dev-fanout: 5914s > 3600s (mode=trim)
      overlap saved             38.7m  (parallel steps)
  goal-rapid-microscope-iter-15  depth=full  verdict=ESCALATE  wall=228.4m
      browser-qa-agent            53.2m  calls=1
      auditor                     38.3m  calls=1
      developer                   35.3m  calls=1
      goal-decomposer             28.7m  calls=1
      goal-evaluator              27.0m  calls=1
      qa                          24.8m  calls=1
      reviewer                    19.8m  calls=1
      ui-impact-analyst           10.6m  calls=1
      iteration-summarizer        10.2m  calls=1
      coherence-auditor            6.3m  calls=1
      orchestrator                 6.2m  calls=1
      demo-narrator                1.7m  calls=1
      [engine] full-pipeline     166.3m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                 35.3m
      OVER BUDGET at post-dev-fanout: 5408s > 3600s (mode=trim)
      overlap saved             33.7m  (parallel steps)
  goal-rapid-microscope-iter-16  depth=full  verdict=ESCALATE  wall=229.8m
      developer                   66.2m  calls=1
      browser-qa-agent            28.9m  calls=1
      reviewer                    27.0m  calls=1
      goal-evaluator              25.1m  calls=1
      auditor                     24.6m  calls=1
      goal-decomposer             24.2m  calls=1
      qa                          22.2m  calls=1
      ui-impact-analyst           12.2m  calls=1
      orchestrator                 8.7m  calls=1
      coherence-auditor            7.3m  calls=1
      iteration-summarizer         7.0m  calls=1
      demo-narrator                4.9m  calls=1
      [engine] full-pipeline     173.0m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                 29.8m
      OVER BUDGET at post-dev-fanout: 7573s > 3600s (mode=trim)
      overlap saved             28.5m  (parallel steps)
  goal-rapid-microscope-iter-17  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      coherence-auditor           95.7m  calls=1
      developer                   54.1m  calls=1
      browser-qa-agent            31.8m  calls=1
      auditor                     30.9m  calls=1
      qa                          25.1m  calls=1
      reviewer                    25.0m  calls=1
      goal-decomposer             18.1m  calls=1
      ui-impact-analyst           11.9m  calls=1
      orchestrator                 8.3m  calls=1
      iteration-summarizer         7.1m  calls=1
      demo-narrator                2.7m  calls=1
      [engine] full-pipeline     165.8m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                121.2m
      OVER BUDGET at post-dev-fanout: 6342s > 3600s (mode=trim)
  goal-rapid-microscope-iter-17  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      ui-impact-analyst            0.1m  calls=1  failures=1
      [engine] full-pipeline       0.1m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
      pump-wait                  0.0m
  session: 17 completed iteration(s), mean wall 244.7m
      total developer                 1829.6m
      total reviewer                   642.9m
      total coherence-auditor          550.0m
      total auditor                    441.1m
      total browser-qa-agent           414.1m
      total goal-decomposer            411.1m
      total goal-evaluator             352.5m
      total qa                         270.0m
      total iteration-summarizer       234.3m
      total ui-impact-analyst           97.2m
      total orchestrator                85.2m
      total demo-narrator               62.3m
      total browser-qa-replay            4.0m
      total readme-maintainer            3.2m
      total AWAITING_PUMP paused gaps: 1.4m
      halts: AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP
```
