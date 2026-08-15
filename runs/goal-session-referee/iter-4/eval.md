# Iteration 4 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The number problem found last time is really fixed. Last iteration the maths part could report a
result as more surprising than its own method allows; this iteration it cannot. I did not take
anyone's word for it. I ran the exact failing example myself and it now gives the correct answer
(2/7, not 1/7), and I wrote my own fresh test of 2,500 small cases — including the hard cases where
the two groups are far apart — and found zero bad answers, with 448 cases landing exactly on the
lowest allowed value. So J-03 "The statistics core" moves from half-done to done. Three smaller
things are still open and are written down below; none of them changes a verdict number today,
because nothing reads this code yet.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing (deferred — not re-tested) | reports/phase-goal-referee-iter-4-ui-test-results.md (Deferred table, UT-J-01 = DEFERRED-BUDGET); code change checked directly: `git diff -- apps/backend/tests/` has zero removed lines |
| J-02 The evidence contract | passing | passing (deferred — not re-tested) | reports/phase-goal-referee-iter-4-ui-test-results.md (Deferred table, UT-J-02 = DEFERRED-BUDGET); same zero-removed-lines check |
| J-03 The statistics core | partial | **passing** | docs/handoffs/goal-referee-iter-4-audit.md §1 (independent 7,035-case sweep, zero violations) + reports/qa/goal-referee-iter-4-test.log; evaluator's own run: exact repro p == 2/7, 2,500-case independent sweep with 0 violations / 448 at the floor, live attestation passes and rejects both a stale version and a tampered copy, full suite 2,513 collected / 2,505 passed / 8 skipped / 0 failed |
| J-04 Matched nulls | failing | failing (not targeted) | reports/phase-goal-referee-iter-0-ui-test-results.md#UT-J-04 |
| J-05 The registry | failing | failing (not targeted) | reports/phase-goal-referee-iter-0-ui-test-results.md#UT-J-05 |
| J-06 Estimand engines + adjudication | failing | failing (not targeted) | reports/phase-goal-referee-iter-0-ui-test-results.md#UT-J-06 |
| J-07 The starter family | failing | failing (not targeted) | reports/qa/goal-referee-iter-0-evidence/J-07-fail.png |
| J-08 Strategy family + promotion interlock | failing | failing (not targeted) | reports/phase-goal-referee-iter-0-ui-test-results.md#UT-J-08 |
| J-09 Referee on /desk + 22 MCP tools | failing | failing (not targeted) | reports/qa/goal-referee-iter-0-evidence/J-09-fail.png; evaluator parsed EXPECTED_TOOLS = 20 names, not 22 |
| J-10 The kept product stands | partial | partial (kept half re-verified) | reports/qa/goal-referee-iter-4-evidence/J-10-verify.png (replay PASS, fresh) + J-10-desk.png, J-10-cockpit.png, J-10-structure.png |

One FAIL row in the results file is NOT a regression: UT-07 is a supplementary check the browser
lane invented this iteration, expecting five Desk reference panels to open. Two of them
(`screenComparison`, `provenance`) only exist once a desk screen has been recorded, and the test
rig has none — the page shows the honest "Desk screen not computed yet." panel, exactly the state
recorded at iteration 0's baseline walk. I opened `J-10-desk.png` myself and confirmed it; the
auditor opened the same picture and reached the same conclusion (F1). The change this iteration
touched no page code at all.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets/credentials | OK | `iter-4/scan-report.md`: CLEAN, no secret findings; no config/env file in the diff (5 backend source files only) |
| Paid/external SaaS, new runtime dependency | OK | scan-report CLEAN; `requirements.txt`/`pyproject.toml` zero diff (`git diff --stat -- apps/backend` lists only the 5 referee source/test files); scipy still absent |
| License changes | OK | scan-report CLEAN; no LICENSE file in the diff |
| Fabricated/substituted data | OK | New data is synthetic test fixtures inside `tests/`, which the goal's Constraints sanction ("hermetic tests: keyless on committed fixtures... synthetic observation corpora with known truth"); no fixture appears in a production path; store-scope guard CLEAN, 11,274 protected files byte-identical |
| 1. No execution path, ever | OK | `test_no_execution_path` green inside my own full-suite run; diff contains no order/broker code |
| 2. No profit claims / no advice | OK | `test_copy_discipline` green in my run; the only new served text is the field name `stale_basis_dates` |
| 3. Frozen foundations | OK | `git diff --stat -- apps/backend` shows exactly 5 files, all `research/referee_*` + their tests; zero diff to `app/config.py`, `app/main.py`, `desk_playbook*.py`, `desk_forward.py`, `levels.py`, `tradability.py`, `setups.py`, `edge_report*.py`, `backtests.py`, `pnl_scan.py`, any route file; fingerprint printed by me = `08e471b10130e1e2` |
| 4. Hold-out-only promotion | OK | `pnl_scan.py` untouched (zero diff) |
| 5. No lookahead | OK | No measurement or bar-selection path changed; the diff is a summation-order fix plus one disclosure list |
| 6. Single source of truth | OK | The new `_is_stale_basis` predicate REPLACES two independent copies of the same check — duplication goes down, not up; coherence.md = COHERENCE-PASS |
| 7. Deterministic and seeded | OK | I called `permutation_test` twice on identical input and the full result dicts were byte-identical; the fixed branch uses no randomness at all (full enumeration) |
| 8. Read-only MCP | OK | MCP files untouched; I parsed `EXPECTED_TOOLS` myself = 20 tools |
| 9. Immutable data | OK | Store-scope guard CLEAN (`reports/qa/goal-referee-iter-4-store-scope-guard.md`): every protected path holds exactly the files it held before, byte-size and mtime unchanged |
| 10. Persistence stays scoped | OK | Nothing was recorded or fetched; no compute act exists yet |
| CI-inversion is never a p-value | OK | The fix strengthens the permutation p; no bootstrap quantity feeds it |
| Never shrink the BH denominator / no gate loosens mid-era | OK | No constant, floor, q, K or B changed; the only constant edited is the version label `STATS_CORE_VERSION` v1 → v2, which is the era's own "named revision" mechanism, and nothing has been recorded yet to re-key |
| The Referee never feeds back | OK | The import-ban guard from iteration 3 passes unmodified inside my full-suite run; no frozen module imports referee code |
| No confirmatory output without a verified attestation | OK | Strengthened: I ran the attestation live — it passes, and verification correctly refuses both a stale-version copy and a tampered copy |
| No annualized metrics | OK | The annualization guard is green in my own suite run |
| Enhancement loop stays in its box | OK | `docs/goal.md` untouched this iteration; all ten journey hashes recomputed and identical to the recorded ones |
| Host-guard caps are law | OK | I ran every heavy command under the declared CPU mask (`taskset -c 4-7,12-15`); no cap was widened or bypassed |

No violations, critical or minor.

## Next-Step Recommendation

Build J-04 "Matched nulls" next, on its own, at full depth. This is the part that gives every
signal a fair comparison: for each recorded signal it draws a set of comparison moments from the
same stock, at the same time of day, with the same amount of trading time left, and measures them
through exactly the same rail — so "better than chance" means better than a fair comparison, not
better than a straw man. Full depth is right because this iteration also mints permanent name-tags
for those comparison rules, and later registered questions will point at those tags forever, so a
mistake here cannot be quietly corrected later.

Three small things should ride along with it rather than becoming their own iteration:

1. Decide what "the smallest possible surprise value" means and serve the honest one. Today the
   maths core reports that the smallest reachable value is half of what its exact method can
   actually reach — I measured this myself on the same example the fix repaired. The written
   specification can be read both ways, so this needs your ruling: either serve the truly reachable
   value in exact mode, or rename the field to say it is a step size. Nothing reads it yet, so it
   is free to settle now and expensive to settle after the next four parts consume it.
2. Refuse unusable readings instead of silently mis-answering. If a reading arrives as "not a
   number" or "infinity", the guarantee we just proved quietly breaks and a meaningless answer
   comes out. J-04 builds the first thing that produces readings, so it should reject them at the
   door (counted as an exclusion, never as a zero).
3. Tighten one weak test: the check on the one-against-many shortcut currently accepts anything
   inside a wide statistical band, so a small, steady bias could slip through.

Two housekeeping items for a person, neither of which blocks the next build:

- This run's own paperwork stopped the automatic final check: `what-to-click.md` still contains a
  "fill in" placeholder, so the run finished as blocked and its five changed files are still
  sitting uncommitted in the working folder. They should be committed so the work is not lost.
- Still outstanding from iteration 2: the unrelated trendora backend on port 8255 was stopped by a
  pattern-based process kill and has not been restarted.

Approve "build the matched nulls next, at full depth, and settle the smallest-surprise-value
question while nothing depends on it yet."

## Halt Justification (if halting)

Not halting.
