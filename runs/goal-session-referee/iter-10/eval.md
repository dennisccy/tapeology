# Iteration 10 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** evidence

## Summary

The last two Referee panels are real, and I checked them myself instead of reading the reports. On
the Desk page a person can now open "Referee Adjudications" and see each written-down question with
its plain verdict word, and open "Referee Runs" to start a job, watch it count up, cancel it, and
read the history of every run. The Claude connector now offers 22 read-only tools — I counted them
myself. The one weakness the previous round left open is genuinely closed: a certificate can no
longer be stamped with the name of a strategy whose trades were never part of the evidence. But
this round did not re-check 7 of the 8 older journeys — the clock ran out and their rows say
"deferred" — and the deterministic gate treats a deferred row exactly like a failure, so the era
cannot be declared finished yet. One promised picture is also missing: nobody photographed the
screen refusing a second job while the first is still running.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing (deferred — not re-tested) | reports/phase-goal-referee-iter-10-ui-test-results.md:49 (DEFERRED-BUDGET) |
| J-02 The evidence contract | passing | passing (deferred — not re-tested) | reports/phase-goal-referee-iter-10-ui-test-results.md:50 (DEFERRED-BUDGET) |
| J-03 The statistics core | passing | passing (row deferred; evaluator re-verified directly) | evaluator's own live `run_oracle_attestation()` → `passed: True`; zero diff to `referee_stats.py` |
| J-04 Matched nulls | passing | passing (deferred — not re-tested) | reports/phase-goal-referee-iter-10-ui-test-results.md:52 (DEFERRED-BUDGET) |
| J-05 The registry | passing | passing (deferred — not re-tested) | reports/phase-goal-referee-iter-10-ui-test-results.md:53; corroborated by reports/qa/goal-referee-iter-10-evidence/UT-02-result.png |
| J-06 Estimand engines + adjudication | passing | passing (row deferred; evaluator re-verified directly) | evaluator's own pooling probe (12 planted trades: unfiltered 12 / unrelated 0 / matched 12); reports/qa/goal-referee-iter-10-evidence/UT-04-result.png |
| J-07 The starter family | passing | passing | reports/phase-goal-referee-iter-10-regression-replay-results.md (1/1 PASS) + reports/qa/goal-referee-iter-10-evidence/J-07-verify.png |
| J-08 The strategy family + promotion interlock | passing | passing (row deferred; evaluator re-verified directly) | evaluator's own live probe: `authorize_promotion` on an empty store → `{"authorized": false, "refusal_class": "no_certificate"}` |
| J-09 The Referee on /desk + MCP v5 | failing | passing (capture defect: one required screenshot missing) | reports/qa/goal-referee-iter-10-evidence/UT-02-result.png, UT-04-result.png, UT-05-result.png, UT-09-result.png, UT-13-result.png; evaluator's own in-process MCP tool list = 22 |
| J-10 The kept product stands | partial | passing | reports/qa/goal-referee-iter-10-evidence/UT-14-cockpit-result.png, UT-14-structure-result.png, UT-13-result.png; evaluator's own suite run 2,688/2,680 passed/8 skipped/0 failed and pin `08e471b10130e1e2` |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | `runs/goal-session-referee/iter-10/scan-report.md` = CLEAN; the diff adds no config or env file (11 files: 1 MCP module, 1 research module, 6 backend test files, 3 frontend files) |
| Paid / external SaaS, new runtime dependency | OK | No manifest touched — `git diff --name-only bf6e3b9` matches no `package*.json`, `pyproject`, `requirements*`, or lockfile |
| License changes | OK | No LICENSE or license-field file appears in the diff |
| Fabricated / substituted data | OK | The `fragile` and refused-attestation entries are QA-seeded records on the fixture-scoped rig (ids `QA-FRAGILE-1`/`QA-REFUSED-1`), which the iteration spec explicitly sanctions; `apps/backend/.data/` contains no referee directory at all (evaluator checked), and reports/qa/goal-referee-iter-10-store-scope-guard.md is CLEAN with all 11,274 protected files unchanged |
| No execution path, ever | OK | No brokerage/order/trading code in the diff; `test_no_execution_path.py` green in the evaluator's own suite run |
| No profit claims / no advice | OK | Copy-discipline tests green; the rendered `REFEREE_REGISTER` disclosure states verdicts are "never a profit claim, never advice, never a prediction, and never annualized" (visible in UT-04-result.png) |
| Frozen foundations / no fingerprint movement | OK | `Config().config_fingerprint()` printed by the evaluator = `08e471b10130e1e2`; the era-cumulative product diff (`git diff --stat e875972`) touches zero lines of levels.py, tradability.py, setups.py, desk_forward.py, desk_playbook*.py, backtests.py, store.py or the engine; the `/desk` page diff is additive (10 hunks, one deleted line inside a union type) |
| Hold-out-only promotion / promotion is certificate-locked | OK — the open MINOR entry is now CLOSED | Rider 1 filters pooled evidence by the certificate's own candidate (`referee_adjudicate.py:533-596`, call site `:1266-1269`); evaluator's own probe: unrelated candidate pools 0 of 12 planted trades. `authorize_promotion` still refuses `no_certificate` on an empty store (evaluator's live probe) |
| No lookahead | OK | No measurement or bar-selection code changed |
| Single source of truth | OK | `runs/goal-session-referee/iter-10/coherence.md` = COHERENCE-PASS; every new panel renders served fields verbatim |
| Deterministic and seeded | OK | No RNG or seed-recipe code changed; `referee_stats.py` has zero diff |
| Read-only MCP | OK | Both new tools resolve through `_STATIC_PATHS` and `call_tool` only ever calls `_proxy_get`; evaluator listed 22 tools in-process, all read-only names |
| Immutable data / append-only stores | OK | No store format or writer changed; the rig's ledgers only ever appended (UT-09 shows completed and cancelled rows side by side, no rewrites) |
| Persistence stays scoped | OK — with one monitoring gap | Every write went to the fixture rig (`assert_scoped_qa_backend.py` run before the write tests). Audit finding T3 stands: the store-scope guard's protected-path list names 12 directories, none of them a referee store — nothing leaked (no referee dir exists in the real store) but the guard would not have noticed if it had |
| Referee-era rails (one checkpoint, exploratory atlas, CI-inversion, BH denominator, no gate loosening, no feedback, attestation refusal, no annualized metrics) | OK | Guard and oracle tests green in the evaluator's own suite run; UT-04 shows the refusal state served with its reason and `attestation: fail` rather than a confirmatory verdict |
| Enhancement loop stays in its box | OK | `docs/goal.md` is not in this iteration's diff |
| Host-guard caps are law | OK | `host-guard.env` released the CPU mask on 2026-07-30; no cap was disabled or widened; the rig's null builds are ~40 ms each |

## Next-Step Recommendation

Run one short verification round — no new building. Three things must happen in it.

1. Re-check the seven journeys this round skipped for time: J-01 "The era transition stands",
   J-02 "The evidence contract", J-03 "The statistics core", J-04 "Matched nulls", J-05 "The
   registry", J-06 "Estimand engines and adjudication" and J-08 "The strategy family and the
   promotion lock". Their rows say "deferred", and the automatic finish check treats a deferred row
   exactly like a failure, so the era cannot be declared done while they stand. Six of them have no
   stored click-by-click script (J-01's and J-02's are marked invalid), and most have no screen of
   their own, so re-checking them means running their own named backend acceptance tests and
   writing the result into the results table — not taking pictures of pages they do not have.
2. Take the one missing picture: the screen refusing a second job while the first is still running.
   Today the button greys out the moment it is clicked, so a second click never reaches the server
   and nothing is shown. To photograph the refusal, start a job one way (a second browser tab, or
   the command line) and then click the button in a freshly loaded page — the red line
   "Refused — a null build is already running for this spec." will appear. The behaviour itself is
   already proven three ways; only the picture is missing.
3. Fix the walk-through recorder: this round's recording was skipped because its script contains an
   action type ("scroll") the player does not understand.

Four small clean-ups are worth doing whenever a builder next touches this area; none of them blocks
the era: a certificate check that treats "both names unknown" as a match (unreachable today, but
worth refusing outright); the verdict page showing a plain dash when the second data request fails,
which looks the same as "this question honestly has no such value"; a stale comment on the Desk page
that still quotes the old counts 19/7/1; and adding the four Referee storage folders to the guard
that watches the owner's real data.

Two items for a person, neither blocking: this round's eleven changed files are not committed yet
(iterations 8 and 9 are already committed), and, from iteration 2 and outside this project, the
unrelated trendora backend on port 8255 has still not been restarted.

Approve one short verification round that re-checks the seven skipped journeys and takes the one
missing picture; nothing needs a human unblock to start it.
