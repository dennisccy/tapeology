# Iteration 2 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The work asked for this round is real and done. Every recorded trading signal and every
recorded test trade can now be read as one single kind of record, with the same fields for
both, so the later parts of the Referee have one shared foundation instead of two. I did not
take the builder's word for it: I ran the tests myself, and I read the new test file line by
line to check the numbers in it are written out by hand rather than copied from the code they
are meant to check. The old product still works, the settings pin has not moved, and nothing
was written into the owner's saved data. One thing outside this project needs a person:
while cleaning up its test servers, the builder also stopped an unrelated project's server,
and that server is still stopped.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing | `reports/phase-goal-referee-iter-2-ui-test-results.md` row UT-J-01 (PASS) + `reports/qa/goal-referee-iter-2-evidence/UT-J-01-result.png`; evaluator re-ran `tests/test_referee_evidence.py` (17) unmodified and printed `current_playbook_detector_basis() == 02bebbe17e7b8769` matching the screenshot |
| J-02 The evidence contract | failing | **passing** | Acceptance lane (goal.md `(Keyless; automated.)`): evaluator's own run of `tests/test_referee_evidence.py` + `tests/test_referee_guards.py` = 28 passed; test bodies read at `apps/backend/tests/test_referee_evidence.py:410-483` (hand-typed golden, full-dict equality), `:489-511` (cold/warm/deleted parity), `:517-577` (pool/split), `:583-619` (dedup + coverage-shrink), `:625-690` (net_r, ET crossing, caveat identity, paired nulls), `:715-743` (SHA-256 before/after). Live-endpoint regression row UT-J-02 (PASS) + `reports/qa/goal-referee-iter-2-evidence/UT-J-02-result.png` |
| J-03 The statistics core | failing | failing (not targeted) | carried; `referee_stats.py` does not exist |
| J-04 Matched nulls | failing | failing (not targeted) | carried |
| J-05 The registry | failing | failing (not targeted) | carried |
| J-06 Estimand engines + adjudication | failing | failing (not targeted) | carried |
| J-07 The starter family | failing | failing (not targeted) | carried |
| J-08 Strategy family + promotion interlock | failing | failing (not targeted) | carried |
| J-09 Referee on /desk + 22 MCP tools | failing | failing (not targeted) | carried |
| J-10 The kept product stands | partial | partial | Golden replay PASS (`reports/phase-goal-referee-iter-2-regression-replay-results.md`) + freshly captured `reports/qa/goal-referee-iter-2-evidence/J-10-verify.png` (sha256 `dc791441…`, differs from iter-1's). Stays partial: the three Referee `/desk` sections do not exist and MCP still advertises 20 tools, not 22 — both land with J-09 |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | `iter-2/scan-report.md`: CLEAN on added lines. Diff is 3 Python files only — no new config/env file |
| Paid / external SaaS, new runtime dependency | OK | `requirements.txt`/`pyproject.toml` absent from `git diff --name-only` vs `7d52450`. New code uses stdlib `sqlite3`/`hashlib` only |
| License changes | OK | No LICENSE path in the diff (checked by name grep) |
| Fabricated / substituted data | OK | Unmeasurable leaves are EXCLUDED, never filled: `test_...excludes_unmeasurable_leaves` asserts the 3 `1m` keys are absent and `excluded_leaves == 3`; `test_strategy_observations_skips_a_report_with_no_dataset_block` returns `{[], []}` rather than a made-up identity |
| 1. No execution path | OK | `test_no_execution_path.py` green inside my 2446-pass run; no order/broker code in the diff |
| 2. No profit claims / no advice | OK | `test_copy_discipline.py` green; `test_forming_bar_basis_caveat_passes_copy_discipline` pins the one new served sentence |
| 3. Frozen foundations | OK | ZERO diff to `desk_playbook*.py`, `desk_forward.py`, `levels.py`, `tradability.py`, `setups.py`, `pnl_scan.py`, `app/config.py`, `app/main.py`, `referee_routes.py` (verified by me). `Config().config_fingerprint()` printed `08e471b10130e1e2`. Diff is additive: 1144 insertions / 1 deletion |
| 4. Hold-out-only promotion | OK | n/a this iteration — `pnl_scan.py` untouched; the interlock is J-08 |
| 5. No lookahead | OK | Both adapters only re-shape values already recorded in each signal's own `forward` block; no re-measurement (coherence audit confirms the same) |
| 6. Single source of truth | OK | `iter-2/coherence.md` = **COHERENCE-PASS**; no duplicate computation, no new endpoint, no new Data-Contract row |
| 7. Deterministic and seeded | OK | No randomness added. The cache is stat-keyed and content-neutral — cold/warm/deleted parity asserted |
| 8. Read-only MCP | OK | Zero MCP diff; `test_mcp_server.py` 20-tool pin green |
| 9. Immutable data | OK | TC-9 SHA-256 listing unchanged at unit level; `reports/qa/goal-referee-iter-2-store-scope-guard.md` CLEAN — 11,274 protected files byte-identical |
| 10. Persistence stays scoped | OK | Only new persistence is the derived, rebuildable observation cache (`TAPEOLOGY_REFEREE_OBS_CACHE_DB`), which owns nothing |
| Referee never feeds back | OK | Actively proven, not assumed: bidirectional AST import-ban tests green (`test_no_referee_module_imports_the_detect_or_context_modules`, `test_the_detect_and_context_modules_import_no_referee_module`, plus a seeded can-fail counter-test) |
| Evidence pools one signature | OK | `detector_basis` pooling proven by TC-3/TC-4 |
| No annualized metrics | OK | Guard green in the full suite |
| Confirmatory-claim / BH / attestation rails | OK | n/a — no statistics, registry, or verdicts exist yet |
| Enhancement loop stays in its box | OK | `docs/goal.md` unchanged — all 10 journey spec hashes identical to iteration 1's record |
| Host-guard caps | OK | Not touched; heaviest path this iteration was a 164s test suite |
| **Out-of-scope host action (NOT a goal.md anti-goal — recorded for visibility)** | **NOTE** | The developer's first cleanup used a pattern-based `pkill -f "uvicorn main:app"` and also killed an unrelated project's backend (trendora, port 8255). I confirmed nothing is listening on 8255 now, so it is still down. Honestly self-disclosed in `docs/handoffs/goal-referee-iter-2-dev.md`. Not a listed anti-goal and not a product defect — but it needs a person to restart it, and the pattern must never be used again |

## Next-Step Recommendation

Build **J-03 "The statistics core"** next, on its own, and run it at **full depth**. This is the
part that decides whether a result is real or just noise, so it deserves the extra review
lanes: a wrong sum here would still pass its own tests and would quietly poison every verdict
the Referee later prints. Its own acceptance says the proof suite IS the deliverable, which is
exactly when an independent check of the checker is worth the time.

Three small leftovers from this round should ride along with it, not become an iteration of
their own: (1) add tests for the "was this trading day complete" helper, which today has none
and is a rough estimate that cannot see gaps in the price data — the later adjudication step
will rely on it; (2) add a test for the cache file-path helper, which is written but never
called; (3) settle one wording question in `docs/referee-statistical-spec.md`: the written spec
says every record must carry a detector name, but a strategy trade has no detector, so the code
leaves it empty — the owner should confirm that is correct before the adjudication step depends
on it.

Separately, and outside this project: please restart trendora's backend on port 8255. The exact
command is written down in `docs/handoffs/goal-referee-iter-2-dev.md`. Approve building J-03
next at full depth; nothing inside this project is blocked.
