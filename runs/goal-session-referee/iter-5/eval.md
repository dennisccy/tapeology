# Iteration 5 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The matched-comparison machinery works. Every recorded trading signal can now be compared
against fair "what if nothing special happened" moments drawn from the same stock, at the same
time of day, with the same amount of trading time left, and measured through exactly the same
ruler — so J-04 "Matched nulls" moves from failing to passing. I did not take the builder's or
the reviewer's word for it: I re-ran the whole test suite myself (2,553 tests collected, 2,545
passed, 8 skipped, nothing failed), printed the settings pin myself, counted the Claude
connector's tools myself, and wrote my own extra test because the shipped tests never actually
checked the random picking. Nothing broke: the old product replayed green with a fresh picture,
and the guard over the owner's saved data reports all 11,274 files unchanged. I am asking for
the next round to run at full depth because this round was cut down to the short pipeline for
time reasons — its own plan asked for the long one — and it shipped records that can never be
edited later.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing (not re-tested — deferred for time) | reports/phase-goal-referee-iter-5-ui-test-results.md (Deferred table, DEFERRED-BUDGET); source unchanged this run (git status) |
| J-02 The evidence contract | passing | passing (not re-tested — deferred for time) | reports/phase-goal-referee-iter-5-ui-test-results.md (Deferred table, DEFERRED-BUDGET); source unchanged this run |
| J-03 The statistics core | passing | passing (row deferred; re-verified directly by the evaluator) | own full-suite run 2,545 passed / 8 skipped / 0 failed; `run_oracle_attestation()` live = passed True at `referee-stats-v2`; own 400-case floor sweep |
| J-04 Matched nulls | failing | **passing** | reports/phase-goal-referee-iter-5-ui-test-results.md#UT-J-04 (SKIP — no browser surface, "(Keyless; automated.)"); apps/backend/tests/test_referee_null.py 29 tests green in the evaluator's own suite run; evaluator's own subset-draw probe |
| J-05 The registry | failing | failing (not targeted) | carries iter-0 state; now unblocked |
| J-06 Estimand engines + adjudication | failing | failing (not targeted) | carries iter-0 state |
| J-07 The starter family | failing | failing (not targeted) | carries iter-0 state |
| J-08 Strategy family + promotion interlock | failing | failing (not targeted) | carries iter-0 state |
| J-09 Referee on /desk + 22 MCP tools | failing | failing (not targeted) | EXPECTED_TOOLS parses to 20 names; zero frontend files in the diff |
| J-10 The kept product stands | partial | partial (kept half green) | reports/qa/goal-referee-iter-5-evidence/J-10-verify.png (fresh, 2026-08-15 07:53); reports/phase-goal-referee-iter-5-regression-replay-results.md |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | runs/goal-session-referee/iter-5/scan-report.md = CLEAN (2 untracked files scanned); the six changed files are all `.py`, no config/env file touched |
| Paid or external SaaS / new dependency | OK | no manifest changed (`git status` on pyproject.toml / requirements / package.json = empty); referee_null.py imports only stdlib + in-repo modules |
| License change | OK | no LICENSE diff; scan-report reports no license finding |
| Fabricated or substituted data | OK | honest exclusions everywhere — zero eligible ⇒ `excluded: true` counted (TC-3), unresolvable band map excludes the whole occurrence instead of falling back (TC-5 second case), non-finite anchor excluded-and-counted (TC-13); no real-corpus null build was run and `GET /nulls` serves the empty state |
| 1. No execution path | OK | tests/test_no_execution_path.py green inside the evaluator's own full-suite run |
| 2. No profit claims / advice | OK | tests/test_copy_discipline.py green in the same run |
| 3. Frozen foundations | OK | `git status --porcelain` shows only referee_null.py (new), referee_stats.py, referee_routes.py + 3 test files — zero diff to desk_forward.py, desk_playbook*.py, levels.py, tradability.py, setups.py, edge_report*.py, backtests.py, pnl_scan.py, app/config.py, app/main.py; fingerprint printed live = `08e471b10130e1e2` |
| 4. Hold-out-only promotion | OK | pnl_scan.py untouched this iteration (interlock is J-08) |
| 5. No lookahead | OK | eligibility reads each candidate bar's own recorded epoch only (`_eligible_anchor_positions`, referee_null.py:329-353); TC-7 truncated-session test green; my own probe drew only from recorded bars |
| 6. Single source of truth | OK | coherence.md = COHERENCE-PASS; the rail, the leaf extractor and the band-context block are all imported, never re-implemented |
| 7. Deterministic and seeded | OK | **verified by me directly**: repeated builds of the same occurrence returned byte-identical anchors, and two different occurrences drew different subsets ([2,4,6,7] vs [1,3,5,6]) — the seeded stream is genuinely consulted; no wall-clock in any draw |
| 8. Read-only MCP | OK | EXPECTED_TOOLS parsed by AST = 20 names, unchanged; no MCP file touched |
| 9. Immutable data | OK | store exposes no update/delete/supersede method; duplicate key raises `NullAlreadyRecorded`; store-scope guard CLEAN, 11,274 protected files byte-identical |
| 10. Persistence stays scoped | OK | builds are explicit acts (POST + CLI); `GET /nulls` never computes (TC-17) |
| CI-inversion is never a p-value | OK | bootstrap functions unchanged except the new input guard; the p that feeds BH still comes from the permutation test |
| The Referee never feeds back | OK | the reverse-direction guard (detect/context never import referee) is byte-unchanged; the narrowing lets ONE referee module READ the context resolver, exactly as goal.md's Read-side law states, and every other referee module stays banned |
| No annualized metrics | OK | the annualization guard green inside the full-suite run |
| Enhancement loop stays in its box | OK | docs/goal.md unchanged this iteration |
| Host-guard caps are law | OK | no cap change; the developer used exact-PID service stops (no pattern-based kill this time) |

## Next-Step Recommendation

Build J-05 "The registry" next, alone, at **full depth**. This is the part that writes each
question down before its answer data exists, and stamps a date after which only new trading days
may count. Those records can never be edited later, so they must be right the first time — and
the deeper pipeline (hard audit, closure checks) is exactly what caught the fault this round just
fixed. Four small items should ride along instead of becoming their own round:

1. Add a test where more comparison moments are available than the four that get picked, so the
   random picking is actually checked. Today every test has four or fewer, so the picking cannot
   be wrong in any test. I verified the behaviour is correct by hand this round; the test gap is
   still there.
2. Gate the "how much do the two measurement windows overlap" number with a test — its formula
   was invented by the builder and no test checks its value.
3. Decide whether the comparison sets should be filed under a real question id once questions
   exist (today they borrow the comparison-rule's own name).
4. Serve "unknown" instead of "0" for the share of eligible moments when there is nothing to
   measure (the reviewer's NOTE at referee_null.py:533).

Also outstanding for a person, not blocking and outside this project: the unrelated trendora
backend on port 8255 has still not been restarted since iteration 2. For approval: "build the
question registry next, at full depth, with the four small clean-ups riding along."

## Halt Justification (if halting)

Not halting. ESCALATE only raises the next round's depth; the loop continues.
