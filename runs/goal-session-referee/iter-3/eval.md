# Iteration 3 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This iteration built the statistics engine that decides whether a trading pattern is real or just
noise. Most of it is genuinely good, and I checked it myself rather than trusting the report: the
proof suite runs green in 81 seconds, the whole test suite is 2,495 pass / 8 skip with nothing
broken, the settings pin still prints `08e471b10130e1e2`, and the tamper checks really do refuse a
hand-edited proof record. But I found a real fault the developer, the reviewer and the coherence
check all missed. In one of the two ways the engine can compute a "how surprising is this result"
number, the answer can come out SMALLER than the smallest value that method is mathematically able
to produce — which makes a result look more convincing than it is. I reproduced this on 60,000
fresh test cases: it happens on about 1.7% of small ones, and always on the most extreme results,
which are exactly the ones a person would act on. Nothing is shown to any user yet, so nothing is
misleading anyone today, but the next four journeys all plan to use this engine for their real
numbers.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing (not re-tested — budget) | `reports/phase-goal-referee-iter-3-ui-test-results.md` UT-J-01 row = `DEFERRED-BUDGET`; prior evidence `reports/qa/goal-referee-iter-2-evidence/UT-J-01-result.png` re-opened and still matches; its source file has zero diff this iteration |
| J-02 The evidence contract | passing | passing (not re-tested — budget) | same results file, UT-J-02 row = `DEFERRED-BUDGET`; acceptance lane `tests/test_referee_evidence.py` re-run green by the evaluator |
| J-03 The statistics core | failing | **partial** | `reports/phase-goal-referee-iter-3-ui-test-results.md` UT-J-03 row (SKIP — backend-only, no browser surface); acceptance re-run by the evaluator: 77 referee tests green in 80.8s, full suite 2,495 pass / 8 skip; blocked by an evaluator-reproduced defect at `apps/backend/app/research/referee_stats.py:424` |
| J-04 – J-09 | failing | failing (not targeted) | carried; no work this iteration |
| J-10 The kept product stands | partial | partial (kept half re-verified) | `reports/phase-goal-referee-iter-3-regression-replay-results.md` UT-J-10 PASS + screenshot `reports/qa/goal-referee-iter-3-evidence/J-10-verify.png` |

### The blocking defect in J-03, in plain terms

The engine has two ways to work out a p-value (the "how surprising is this?" number). When the
number of possible re-shufflings is small, it lists every single one exactly. In that exact mode,
the code works out the second group's total by subtracting the first group's total from the
overall total (`referee_stats.py:424`), while the reference figure it compares against was built by
adding the second group's numbers up directly (`referee_stats.py:454`). Those two routes disagree
in the last decimal place. The result is that the real, observed arrangement of the data narrowly
fails its own "is this extreme?" test (`referee_stats.py:430`) and is not counted — so the p-value
comes out at half of the smallest value the exact method can legitimately produce.

Reproduced by the evaluator on fresh fixtures (not from any report):

| Fixture shape | Cases below the exact floor | Rate | Served / correct floor |
|---|---|---|---|
| 1 session, 2 vs 2, N(0,1) | 343 / 20,000 | 1.72% | 1/7 served where 2/7 is the floor |
| 1 session, 1 vs 4, N(0,1) | 171 / 20,000 | 0.86% | 1/6 served where 2/6 is the floor |
| 2 sessions, 2 vs 2, N(0,1) | 49 / 20,000 | 0.25% | 1/37 served where 2/37 is the floor |

Minimal reproduction:

```python
from app.research.referee_stats import permutation_test
g1 = [0.9571299431380904, 0.23675146939940733]
g2 = [-0.2015364333714562, -0.47887435876092443]
permutation_test({"s0": (g1, g2)}, "probe", sidedness="greater")["p"]  # -> 0.1428... (1/7), floor is 2/7
```

Two things make this hard to see and worth recording:

- **The proof suite never runs the exact mode.** Every oracle generator uses 10–40 sessions, so the
  number of re-shufflings is astronomically above the 8,192 cut-off and the seeded mode runs
  instead. The seeded mode is not affected, because its formula adds the observed result in as the
  "+1" on top rather than looking for it among the draws.
- **The one exact-mode test cannot fail this way.** `test_referee_stats.py:258` uses the values
  5.0, 1.0 and 2.0, which computers store exactly, so the last-decimal-place disagreement never
  appears. The deliberately-broken "mutant" test is also one-directional by construction (it always
  returns the least surprising answer possible), so it can only prove the suite catches an
  over-cautious mistake, never an over-confident one.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | `iter-3/scan-report.md` CLEAN on added lines; no new config or env file in the changed-file list |
| Paid / external SaaS, new runtime dependency | OK | `requirements.txt` and `pyproject.toml` have zero diff vs snapshot `f2e1e43` (evaluator's own `git diff`); the new module imports only `itertools`, `math`, `random`, `statistics` |
| License changes | OK | scan-report CLEAN; no LICENSE file in the diff |
| Fabricated / substituted data | OK | the new module reads no store and ingests no vendor data; the simulated data generators live inside the test file and are labelled as test infrastructure |
| 1. No execution path | OK | no trading/broker code added; `test_no_execution_path.py` green inside the evaluator's own full-suite run |
| 2. No profit claims / no advice | OK | the module serves no copy to any surface; `test_copy_discipline.py` green |
| 3. Frozen foundations | OK | evaluator ran `git status --porcelain -- apps/backend/app/ apps/frontend/`: the only entry is the new untracked `referee_stats.py`. Zero diff to the tape engine, `desk_*`, `levels`, `tradability`, `setups`, `pnl_scan`, `config.py`, `main.py`, every route file, and the whole frontend. `Config().config_fingerprint()` printed `08e471b10130e1e2` by the evaluator |
| 4. Hold-out-only promotion | OK | `pnl_scan.py` untouched; no promotion path changed |
| 5. No lookahead | OK | the module reads no bars or tape at all — it only consumes number arrays a caller passes in |
| 6. Single source of truth | OK | `iter-3/coherence.md` = **COHERENCE-PASS**; the combined statistic is implemented once in `_t_statistic` and shared by both callers |
| 7. Deterministic and seeded | OK | evaluator re-ran the p-value, both confidence intervals and the attestation twice each — byte-identical every time. (The defect above is a correctness fault, not a determinism fault: it is reproducibly wrong, not randomly wrong) |
| 8. Read-only MCP | OK | MCP server untouched; evaluator parsed `EXPECTED_TOOLS` = 20 tools |
| 9. Immutable data | OK | store-scope guard CLEAN — all 11,274 protected files byte-identical; the new module writes nothing anywhere |
| 10. Persistence stays scoped | OK | no recording or fetching path added |
| Referee: no confirmatory claim outside the gauntlet | OK | no verdict is served; the module is imported by nothing |
| Referee: historical atlas exploratory forever | OK | nothing served this iteration |
| Referee: CI-inversion is never a p-value | OK | evaluator read the returned shapes: neither confidence-interval function returns a p at all; the only p producers are the primary test and the named robustness disclosure |
| Referee: never shrink the BH denominator | OK | `benjamini_hochberg` sets `m = len(p_values)` and drops nothing; the "unevaluated folds in as 1" case is tested |
| Referee: no gate loosens mid-era | OK | constants match the spec values named in the iteration spec; no gate exists yet to loosen |
| Referee: the Referee never feeds back | OK | new import-ban guard plus its can-fail counter-test, both re-run green by the evaluator |
| Referee: no confirmatory output without a verified attestation | OK | evaluator executed all four refusal cases — tampered result (with the `passed` flag still claiming true), stale version, tampered expectation, non-dict input — every one refused |
| Referee: no annualized metrics | OK | the literal string appears in none of the three new files; the guard test is green |
| Referee: enhancement loop stays in its box | OK | `docs/goal.md` is untouched; only `docs/referee-statistical-spec.md` gained one clarifying sentence |
| Host-guard caps | OK | no widening or bypass observed in the diff |

**Result: no anti-goal violated, critical or minor.** The defect above is a correctness fault in
this iteration's own new code, not a breach of any rail.

## Next-Step Recommendation

Iteration 4 should fix the statistics engine's exact-mode p-value and prove the fix, at **full**
depth, before anything else is built on top of it. Three things belong in that iteration:

1. **Fix the floor.** Make the exact mode add up the second group directly, the same way the
   reference figure does, so the observed arrangement always counts as one of the extreme ones. The
   property to guarantee and to test is simple: in exact mode the answer can never be smaller than
   2/(number of arrangements + 1).
2. **Prove it with a real check, not a lucky example.** Add an oracle case that actually runs the
   exact mode — small session counts and awkward decimal values, not round numbers — and add a
   deliberately-broken variant that errs in the over-confident direction, since today's "mutant"
   test can only catch the over-cautious kind.
3. **Re-pin the stored proof record and bump the engine's version label** from
   `referee-stats-v1`, because the fix changes numbers the record pins. Doing it now is free —
   nothing has been recorded yet.

Two smaller riders should ride along rather than becoming their own iteration: the unused draw
helper and the untested one-anchor shortcut the reviewer flagged, and a check of two leads I could
not resolve in this pass, both in older, unchanged code — a date whose newest record sits at a
different detector version can silently blank that date's evidence, and a dataset with no time
anchor is turned into a 1969 date, which would lump unrelated trades into one group. Both would
matter to J-06.

For a person deciding: approve iteration 4 as "fix and prove the p-value floor in the statistics
engine, at full depth, then continue to matched nulls (J-04)". Nothing here needs a human to unblock
it. One older item is still outstanding and does need a person: the unrelated trendora backend on
port 8255 that iteration 2's cleanup stopped has still not been restarted.

## Why ESCALATE rather than CONTINUE

The decomposer wrote this iteration's spec at **full** depth with an explicit written reason: this
module is shared architecture that four later journeys will import, and "a subtle implementation bug
here would pass its own isolated unit tests while silently invalidating every later verdict". The
engine then demoted the run to **lean** for wall-clock budget reasons
(`telemetry.jsonl`: `depth_demoted`, `reason: budget-breach`), so the deeper audit and closure
lanes never ran — and the same budget cut also skipped J-01 and J-02's re-checks. The exact failure
the decomposer predicted then happened: a subtle statistical bug that passes every one of its own
tests, that the review lane examined and declared correct, and that only an independent
reproduction caught. That is cross-cutting complexity warranting the full pipeline. An `ESCALATE`
verdict is also the only signal that mechanically guarantees the next iteration runs full — it is
the first rung of the engine's own depth ladder and outranks the budget-breach demotion.

This is not a halt. Nothing regressed, no anti-goal was violated, the coherence audit passed, and
the fix is small and fully within the team's control.
