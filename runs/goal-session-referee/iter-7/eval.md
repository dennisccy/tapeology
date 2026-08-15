# Iteration 7 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The judging machinery is real and it works. A written-down question can now be measured against
its fair comparison moments and come back with one permanent answer that no later run can change.
I checked this myself instead of believing the report: I ran the new test file (40 checks, all
pass), read the two main round-trip checks line by line — they build real price bars, real
recorded signals and real comparison records, then run the real code — and a made-up "there is
something here" case comes back "corroborated" while a made-up "there is nothing here" case comes
back "no evidence". The old product was walked in a real browser and held, with a fresh dated
picture — closing last round's evidence hole. The whole test suite is 2,642 collected / 2,634
passed / 8 skipped / 0 failed, run by me, and the settings pin still prints `08e471b10130e1e2`.
I am still raising the depth, for two reasons. First, this round was planned as the deep pass and
the engine cut it to the short one for time, so the most permanent part of the whole era shipped
without the hard audit. Second, my own poking found two things the short pass missed: if the
maths self-check fails, the system still writes the question's one-and-only permanent answer as
"corroborated" (what a person is shown is correctly refused, but the stored record is wrong
forever), and a damaged question file silently disappears from the answers page with no notice.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing (deferred; code re-checked) | reports/phase-goal-referee-iter-7-ui-test-results.md UT-J-01 `DEFERRED-BUDGET`; evaluator's own 157-test referee run (0 failures) |
| J-02 The evidence contract | passing | passing (deferred; module changed, re-checked) | UT-J-02 `DEFERRED-BUDGET`; runs/goal-session-referee/iter-7/iter-diff.md (referee_evidence.py Rider 1 hunk, read line by line); tests/test_referee_evidence.py green in evaluator's own run |
| J-03 The statistics core | passing | passing (deferred; module unchanged) | UT-J-03 `DEFERRED-BUDGET`; iter-diff.md file list — referee_stats.py absent (methodology A.6 durability); one definition site per stats function confirmed by grep |
| J-04 Matched nulls | passing | passing (deferred; module changed, re-checked) | UT-J-04 `DEFERRED-BUDGET`; additive `resolve_occurrence_backing_bucket` export only; tests/test_referee_null.py green in evaluator's own run |
| J-05 The registry | passing | passing (deferred; module changed, re-checked) | UT-J-05 `DEFERRED-BUDGET`; Riders 2+3 read in iter-diff.md; tests/test_referee_registry.py green in evaluator's own run |
| J-06 Estimand engines + adjudication | failing | **passing** | reports/phase-goal-referee-iter-7-ui-test-results.md UT-J-06 (SKIPPED — keyless, no browser surface); evaluator's own `tests/test_referee_adjudicate.py` run: 40 tests / 0 failures (own --junit-xml), DoD round-trip + TC-8 + TC-11/TC-23 + TC-22 assertions read directly; evaluator's own tampered-attestation probe |
| J-07 The starter family | failing | failing | Not targeted; zero `apps/frontend/` diff (`git status --porcelain`) |
| J-08 Strategy family + promotion interlock | failing | failing | Not targeted; `authorize_promotion` exists but `pnl_scan.py` is untouched (grep + git status) |
| J-09 Referee on /desk + MCP v5 | failing | failing | Not targeted; `test_mcp_server.py::EXPECTED_TOOLS` parses to exactly 20 names (evaluator's own parse) |
| J-10 The kept product stands | partial | partial (kept half green, fresh evidence) | reports/phase-goal-referee-iter-7-regression-replay-results.md UT-J-10 PASS; reports/qa/goal-referee-iter-7-evidence/J-10-verify.png (opened: /desk nav + shipped Playbook panels + honest empty state) |

Deferred note: UT-J-01..UT-J-05 carry `DEFERRED-BUDGET` rows (wall-clock trim rung 2 —
telemetry `iter_budget` budget=3600 / elapsed=6581, `iter_budget_trim` rung=replay-narrow). They
were NOT re-tested by the journey lane and keep their prior recorded status. Four of the five had
their own source modules changed this iteration, so the evaluator re-verified those directly
rather than leaning on durability.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials committed | OK | `iter-7/scan-report.md` = CLEAN (tracked + 2 untracked files scanned); no new config/env file in the diff file list |
| Paid / external SaaS dependency | OK | No manifest change — `pyproject.toml` absent from `git status --porcelain`; new module is stdlib + `random.Random` only |
| License changes | OK | No LICENSE/license-field file in the diff file list; scan-report reports no license finding |
| Fabricated / substituted data | OK | Fixtures live only in `tests/`; store-scope guard CLEAN — all 11,274 protected files byte-size and mtime unchanged (reports/qa/goal-referee-iter-7-store-scope-guard.md); the real registry is still empty, so no invented registration exists |
| No execution path, ever | OK | No broker/order code added; `tests/test_no_execution_path.py` green inside the evaluator's own full-suite run |
| No profit claims / no advice | OK | `REFEREE_REGISTER` text read in full: it states what a verdict does NOT mean (never a profit claim, never advice, never a prediction, never annualized). Gap noted, not a violation: the copy lint does not scan this surface yet — J-09 owns that extension |
| Frozen foundations / no lookahead | OK | `desk_forward.py`, `desk_playbook*.py`, `levels.py`, `tradability.py`, `pnl_scan.py`, `app/config.py` all untouched (git status); measurement is the imported rail, never a second implementation |
| Single source of truth | OK (advisory) | `iter-7/coherence.md` = COHERENCE-WARN, no blocking violation; one advisory: `blueprint.md`'s registry-response note still documents four keys after Rider 2 made it five, and the dev handoff falsely claims it was updated |
| Deterministic and seeded | OK | Every draw is keyed on `hypothesis_id` streams; TC-12 (identical evaluation basis + attestation) and TC-23 (byte-identical successive folds) green in the evaluator's own run |
| Immutable / append-only data | OK | Read directly: every new store's `record()` raises on a duplicate key AND refuses to overwrite an existing file; no update/delete/supersede method exists on any of the three new stores |
| No confirmatory claim outside the gauntlet | OK | Verdict is a pure function of recorded facts; exactly one checkpoint per hypothesis (snapshot count pinned at 1 after a later monitoring run) |
| Historical atlas is exploratory forever | OK | TC-8 verified by reading its assertions: an on-boundary date and a deep-backfilled old date (recorded after registration) both contribute zero to coverage and to T |
| CI-inversion is never a p-value | OK | The only p that reaches the BH fold comes from `referee_stats.permutation_test`; bootstrap CIs are recorded separately and never feed the verdict |
| Never shrink the BH denominator | OK | `_family_p_values` iterates the family's frozen candidate list and fills a literal `1.0` for any sibling without a checkpoint; TC-15/TC-16 green |
| No confirmatory output without a verified attestation | OK at the served surface; weakness recorded | The fold re-verifies at read time and refuses (`confirmatory_output_refused: true`, `insufficient_sample`) — proven by the evaluator's own probe with a deliberately broken attestation. BUT the same probe showed the permanent record is still written as `corroborated`. Interpretation call logged in `state/assumptions.md` |
| Referee never feeds back | OK | New import-topology guard test green; `pnl_scan.py` untouched; `authorize_promotion` is unwired |
| Promotion is certificate-locked | OK | `authorize_promotion` has no env override / bypass path (grepped its body); wiring is J-08's job |
| No annualized metrics | OK | Guard green inside the evaluator's own full-suite run |
| Enhancement loop stays in its box | OK | `docs/goal.md` unchanged this iteration (git status) |
| Host-guard caps | OK | No host-guard config touched; no widening anywhere in the diff |

## Next-Step Recommendation

Build J-07 "The starter family" next, on its own, at full depth. This is the first Referee screen
a person can actually use: the shortlist of candidate questions with live readiness numbers, a
pick-and-confirm step, and the real act of writing a question down — which stamps a start date
that can never be edited afterwards. Full depth because it is the first Referee page (so it needs
real browser pictures) and because the act it performs is permanent.

Three fixes must ride inside that round rather than becoming a round of their own, all found by
this evaluation rather than by the pipeline:

1. When the maths self-check fails, do not write the question's one permanent answer at all —
   record it as still pending, with an honest reason. Today the stored answer says "corroborated"
   even though what a person is shown correctly refuses to say so, and that stored answer can
   never be corrected.
2. A damaged question file must be reported on the answers page, not silently disappear — the
   same fix that was just applied to the registry page. Today a damaged file that already had a
   permanent answer vanishes without a word.
3. Correct the two paperwork slips this round left: the shared design note still describes the
   registry answer as having four parts when it now has five, and the builder's own write-up
   claims it was already updated when it was not.

For a person: approve building J-07 "The starter family" next, at full depth, with those three
fixes carried along. Nothing needs a human unblock to start. Still outstanding for a person and
outside this project, carried from iteration 2: the unrelated trendora backend on port 8255 has
not been restarted.
