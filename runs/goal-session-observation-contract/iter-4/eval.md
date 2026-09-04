# Iteration 4 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

This round proved, with tests only, that the tape engine sees the same thing whether the same
recorded events arrive by the replay path or by the live path. I re-ran the new test file myself:
6 checks, all pass, including the one that deliberately breaks a value and shows the comparison can
fail. I also re-ran the whole backend test set myself: 4036 pass, 8 skipped, 0 fail, and the
settings fingerprint still reads 08e471b10130e1e2. Nothing users can see changed, and the web
address `/tape/SIM-BIDABS/observation` still answers "404", which is correct for this round because
that address is only built next round. J-04 "Ingestion-path equivalence" therefore moves from
failing to partial, not to passing.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The artifact is a pure projection… | partial | partial (unchanged) | My own full-suite run (4036 pass / 8 skip / 0 fail, exit 0) re-covers `tests/test_tape_observation_projection.py`; served half still absent — `reports/qa/goal-observation-contract-iter-4-evidence/UT-J-04-result.png` (404) |
| J-02 Three distinct, honest instants… | partial | partial (unchanged) | Same full-suite run re-covers `tests/test_tape_observation_time.py` (now with the three-way ISO check); served half still absent — same screenshot |
| J-03 Lifecycle, feed basis and session identity… | partial | partial (unchanged) | Same full-suite run re-covers `tests/test_tape_observation_lifecycle_feed.py` (29 tests after the sanctioned removal); served half still absent — same screenshot |
| J-04 Ingestion-path equivalence… | failing | **partial** | My own run of `apps/backend/tests/test_tape_observation_path_equivalence.py` = 6 passed / 0 failed (steps 2 and 3 met); step 1 unmet — `reports/qa/goal-observation-contract-iter-4-evidence/UT-J-04-result.png` shows the route still returns 404; results row `UT-J-04` (PASS, regression-smoke scope) in `reports/phase-goal-observation-contract-iter-4-ui-test-results.md` |
| J-05 One read-only machine path | failing | failing (unchanged) | `apps/backend/tests/test_tape_observation_route.py` absent (my own `ls`); no `/observation` route in `apps/backend/app/main.py` (my own grep — only an unrelated `_iso_utc` docstring mention at line 268); same 404 screenshot |
| J-06 Guards and the regression sentinel | partial | partial (unchanged) | `apps/backend/tests/test_tape_observation_guards.py` still absent (my own `ls`); full suite green + fingerprint `08e471b10130e1e2` + `tsc --noEmit` 0 errors (all re-run by me); `/structure` and `/desk` render unchanged per the UT-J-04 DOM checks (prose, no separate screenshot); era-open docs present (`docs/observation-contract-spec.md`, `docs/goal-archive/goal-2026-09-02.md`) |

Notes on evidence quality:

- Only one screenshot exists for a nine-step browser sequence (the 404 page). The Watch → Pause →
  Resume → Stop transitions and the `/structure` / `/desk` spot-checks are recorded in prose and DOM
  queries only. I did NOT set `evidence_makeup`: J-04 is `partial` for a substantive reason (the
  route is absent), and the full browser evidence must be re-taken next round anyway once the served
  JSON becomes readable. Same call as iteration 3.
- No `journeys-changed.md` and no `browser-infra.json` this iteration. I recomputed every journey's
  `spec_hash` (`goal_gate.py hash-journeys`) — all six are unchanged from the recorded values, so no
  goal text drifted under a recorded status.
- Why this is not an escalation on J-05 "One read-only machine path" even though it has been
  recorded `failing` since iteration 0: it has never been attempted and then failed. The goal's own
  Binding Execution Order reserves the route for step 5, so J-05 was out of scope for iterations
  0-4 by instruction, not by inability. The review lane also passed (no fail-open), and no
  cross-cutting ambiguity surfaced this round. The next round is still recommended at full depth
  for the reason given below.
- Replay lane: no golden replay ran, correctly — zero journeys are recorded `passing`, so the
  Required-still-passing set is empty and there was nothing to re-verify mechanically. No
  `DEFERRED-BUDGET` row, no maintenance isolation.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials committed | OK | `iter-4/scan-report.md`: CLEAN, 0 findings (tracked + 1 untracked file). Diff is 3 test files only — no config, env or key file |
| Paid / external SaaS dependency | OK | No manifest touched (`git status -- apps/ docs/ scripts/` shows only the 3 test files); no new import of any vendor SDK in the new module |
| License change | OK | No LICENSE or license field in the diff (scan-report CLEAN) |
| Fabricated / substituted data presented as real | OK | Both legs consume the committed `tests/fixtures/alpaca/PG_20260609_170000_171000_sip.json` and the seeded `SIM-BIDABS` simulator; nothing is served, and no fixture path enters a production module (zero files under `apps/backend/app/`) |
| Rail 3 — frozen foundations byte-identical | OK | `apps/backend/app/observation_contract.py` is byte-identical to its iteration-1 commit (my own `diff` vs `2a8dd40e`); no engine, strategy or profile file in the diff; fingerprint `08e471b10130e1e2` re-checked by me |
| Rail 6 — single source of truth | OK | `iter-4/coherence.md` = COHERENCE-PASS; the new module calls `build_tape_observation`, `get_observation_source` and `compute_observation_hash` rather than reimplementing them |
| Rail 7 — deterministic and seeded | OK | Fixed fixture + fixed sim seed + fixed `generated_at_utc` placeholder; no wall-clock in any assertion |
| No pooling / equating / silent conversion between `sim`, `iex` and `sip` | OK | The two legs' feed bases stay distinct and honestly labelled (`sip` for the replay leg, `iex` for the live leg) and are excluded from the compared semantic set. The seeded-sim leg is fed through the same two feeders, which is what the goal's §5 itself prescribes; nothing is pooled and nothing is served (assumption logged) |
| No recomputation of tape feature / state / feed basis outside the engine | OK | The new module only reads `EngineSnapshot`s captured through `TapeEngine.add_observer`; no classifier or threshold reference (my own read of the module) |
| No semantic divergence hidden by widening the metadata partition (Binding Order — critical class) | OK | TC-6 compares the REAL `observation_contract` partition constants against a frozen literal copy and they match; independently, the whole module is unchanged since iteration 1 (my `diff`), so no widening was possible |
| No actionability field / token (READY, NO_TRADE, `trade_allowed`, …) | OK | My own grep over `test_tape_observation_path_equivalence.py`: zero matches |
| No external-system reference (Workstation / Trendora / TenSteps) | OK | Same grep: zero matches |
| No non-English identifier / schema name / field name / test name | OK | Non-ASCII characters appear only inside comments and the quoted Constitution §5 text (`§`, em dash) — no identifier, key or value |
| No weakening of any named guard file | OK | None of the nine protected guard files appears in the diff (`git status -- apps/`); full suite green |
| No new UI page/panel/component, no new `Config` field, no MCP tool, no CLI | OK | Zero frontend files and zero `apps/backend/app/` files in the diff; `tsc --noEmit` 0 errors (my own run) |
| No mandatory test requiring Alpaca / network / credentials / market hours | OK | Both legs run in-process over the committed fixture and the simulator; my own run needed no network and no server |
| Goal-Mode anti-goals (no guard skipped/xfailed to pass a journey; no fabricated browser proof) | OK | The one removed test was a tautology over literals, not a guard — the seven lifecycle statuses are still each asserted from real `WatchManager` calls (my own read of lines 370-510); the browser screenshot honestly shows the route's absence |

Ledger (`anti_goal_disposition.py summary`): total=0, resolved=0, unresolved_blocking=0,
unresolved_non_blocking=0, unresolved_critical=0.

Coherence: `iter-4/coherence.md` = **COHERENCE-PASS**, with the iteration-3 `_iso_utc` advisory now
closed by this iteration's three-way byte-identity test. Review: `PASS`, no issues — no fail-open.

## Next-Step Recommendation

Build the web address next: `GET /tape/{ticker}/observation` plus its test file
`tests/test_tape_observation_route.py`, which is J-05 "One read-only machine path" and step 5 of the
goal's required order. This is the round where five journeys finally become checkable in the
browser, so please note three things for it. First, the address must read the watch manager's single
atomic read and must never touch the engine directly — the goal calls that mistake a critical
violation. Second, three saved replay scripts still expect this address to be MISSING
(`journey-scripts/J-01.json` step 5 and `J-03.json` step 11 expect "Not Found";
`J-04.json` steps 8-9 expect "404"); they must be rewritten in the same round the address starts
working, or later automatic replays will report false failures. Third, one small test-quality
fixup: in `apps/backend/tests/test_tape_observation_path_equivalence.py` the check named
`test_counterexample_field_partition_drift_is_detected` compares two hand-written lists to each
other and never reads the real values, so it would still pass if the real list were deleted — it is
the same empty-check shape this round just removed elsewhere. In one sentence: next round should
build and serve the observation address, refresh the three replay scripts that assume it is absent,
and repair that one empty check.

