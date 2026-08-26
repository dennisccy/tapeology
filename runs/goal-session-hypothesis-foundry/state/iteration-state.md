# Iteration State — hypothesis-foundry

**After iteration:** 3 · **Date:** 2026-08-27 · **Verdict:** CONTINUE

## Journeys

1 passing (J-01) · 4 partial (J-02 J-03 J-04 J-05) · 3 failing (J-06 J-07 J-08) — 8 total. J-05 moved failing → partial; every partial is blocked on the SAME missing thing: the step-5 read surface.

## Active blockers

- **THE ONE BLOCKER: no Foundry read surface exists.** J-02/J-03/J-04/J-05 have 22 on-screen acceptance steps between them and ZERO have ever been photographed. Binding Execution Order step 5 (fixture states visible, real epoch still unopened) is now the only legal next stage and the only work that can turn four journeys green at once. Owner: dev. Homes already named in `state/blueprint.md` (Sources/Compiler · Interpreter · Freeze/Integrity · Hermetic Oracles, all under `/desk` → Hypothesis Foundry).
- `SourceRecord.alternatives` has no fail-closed validation (auditor B7) — no check that a named sibling id exists, is a family member, or is not itself. Add a batch lint BEFORE J-06 authors the real 11 records (owner: dev, `foundry_source_registry.py:189-199`).
- Crash-path resume still verifies `econ_floor_bps` only, never `manifest_hash` (auditor B4, `foundry_runner.py:112-119`) — narrower sibling of the hole just closed; carry into J-06/J-07.
- QA report keeps mis-describing the J-01 browser replay as covered by the backend test run (auditor T5). It is covered by `reports/phase-...-regression-replay-results.md`; cite that, not pytest.
- Lesser carried: freeze not exercised by the composite oracle (B3); no checkpoint file exists so "never trusts a stale checkpoint" is unfalsifiable (T1); large-N performance fixture not delivered, O(n²) ledger measured but harmless at the 24-variant cap (B5); freeze-set scanner follows same-directory imports only; `BLOCKED_UNIT_CONTRACT` unreachable from declared fields; no CLI entry point for `foundry_runner.py`.
- Operator decision (not agent-fixable): `session.json` caps iterations at 60; `docs/goal.md` recommends `--max-iter 80`.

## Last 2 verdicts

- iter 3: CONTINUE — the hermetic factory suite is real and evaluator-re-run (10 tests), the full pipeline paid off by catching two untested seams, but nothing shipped that an operator can see, so J-05 stopped at partial.
- iter 2: ESCALATE — J-01 passed and J-03/J-04 reached partial, but the era's linchpin machinery shipped without an auditor because the budget rule downgraded a spec-declared full iteration.

## Do not redo

- **Binding Execution Order step 4 IS COMPLETE** — `tests/test_foundry_hermetic_epoch.py` (10 tests): composite all-outcome-types epoch, all-blocked, all-killed, multi-survivor, 20-candidate crash/resume, protected-data trip, evidence-class immutability, plus the auditor-added real-compiler→real-runner seam test. Evaluator re-ran: 10 passed. Do not rebuild it — extend it only if a NEW gap is named.
- **Both iter-2 carried blockers are CLOSED** — `foundry_runner.py:94-110` already-terminal fast path now raises `FoundryResumeIdentityMismatch` on `manifest_hash`/`econ_floor_bps` drift (TC-9); `SourceRecord` now has `alternatives` + `source_hash` (`init=False`, `sha256(source_excerpt)`) with §1.4 documented (TC-10/TC-11). Do not re-open either.
- **J-01 COMPLETE + re-verified by replay** (`iter-3-evidence/J-01-verify.png`, UT-J-01 PASS). Golden script `journey-scripts/J-01.json` works. Do not rebuild or re-record.
- **Steps 1-4 all shipped** (era transition, methodology+registry+CandidateSpec, interpreter/family/freeze/ledger/runner, hermetic oracles). Steps 6-8 (real generation, freeze commit, exhaust) stay ILLEGAL until step 5 ships.
- **Never plant invented values in the QA rig** — `qa_playbook_iter7_fixture_scoped_backend.sh` copies the REAL `.data/foundry/era_open_baseline.json` in, with an honest `null` fallback. Settled in iter-2.
- **Suite/rails baseline** — 3842 passed / 8 skipped / 0 failed, tsc 0, `config_fingerprint 08e471b10130e1e2` (evaluator-recomputed, unmoved), `scout.py`/`micro_features.py`/`referee_*.py` untouched. Keep it that way.
