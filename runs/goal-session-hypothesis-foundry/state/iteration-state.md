# Iteration State — hypothesis-foundry

**After iteration:** 2 · **Date:** 2026-08-26 · **Verdict:** ESCALATE

## Journeys

1 passing (J-01) · 3 partial (J-02 J-03 J-04) · 4 failing (J-05 J-06 J-07 J-08) — 8 total; first journey of the era is green (`reports/qa/goal-hypothesis-foundry-iter-2-evidence/J-01-result.png`).

## Active blockers

- **NEXT ITERATION MUST RUN FULL DEPTH.** The iter-2 spec declared `Depth: full` (cross-cutting trigger) and the deterministic arbiter demoted it to lean for `budget-breach` (engine.log 21:47:43), so the interpreter/freeze/ledger/runner machinery has had NO auditor pass. J-05's oracle suite is exactly the audit-grade stage.
- **Resume identity hole (owner: dev)** — `apps/backend/app/research/foundry_runner.py:89`: the already-terminal fast path returns the cached ledger row without re-verifying `manifest_hash`/`econ_floor`, so a resumed candidate with drifted inputs silently gets a stale result instead of a refusal. Reviewer MINOR + seconded by the coherence auditor. Close before J-06/J-07.
- **`SourceRecord` missing §1.4 `alternatives` + `source_hash`** (`foundry_source_registry.py:159`) — carried from iter-1; J-02 step 3 requires `alternatives`; hard prerequisite before J-06 authors real sources (owner: dev).
- Lesser carried items: freeze-set scanner follows only same-directory imports; `BLOCKED_UNIT_CONTRACT` unreachable from declared fields; no CLI entry point for `foundry_runner.py`.
- Operator decision (not agent-fixable): `session.json` caps iterations at 60; `docs/goal.md` recommends `--max-iter 80`.

## Last 2 verdicts

- iter 2: ESCALATE — J-01 passed and J-03/J-04 reached partial, but the era's linchpin machinery shipped without an auditor because the budget rule downgraded a spec-declared full iteration.
- iter 1: CONTINUE — browser lane repaired honestly; Foundry panel + compiler machinery landed, but J-01's baseline block and J-02's whole UI were still unproven on screen.

## Do not redo

- **J-01 COMPLETE + verified (all 5 steps)** — panel shows era boundary AND the real era-open baseline; evaluator recomputed all six Referee hashes and matched the served values. Golden script `journey-scripts/J-01.json` lint-passes. Do not rebuild or re-record.
- **QA-rig visibility fix DONE the honest way** — `qa_playbook_iter7_fixture_scoped_backend.sh` copies the real `.data/foundry/era_open_baseline.json` into the rig's throwaway root with an honest `null` fallback. Never plant invented rig values.
- **Binding Execution Order step 3 SHIPPED** — `foundry_interpreter.py`, `foundry_family.py`, `foundry_freeze.py`, `foundry_ledger.py`, `foundry_runner.py` + 39 hermetic tests (TC-4..TC-19), evaluator re-ran 71 Foundry tests exit 0. Next legal stage = step 4 (J-05 oracles).
- **All Foundry read surfaces stay deferred** to the single consolidated step-5 read-surface iteration — settled in `state/assumptions.md` iter-1. J-02/J-03/J-04 cannot reach `passing` before it.
- **Suite/rails baseline** — 3825 passed / 8 skipped / 0 failed, tsc 0, `config_fingerprint 08e471b10130e1e2` (pinned, unmoved), store-scope guard CLEAN. Frozen rails (`scout.py`, `micro_features.py`, `micro_routes.py`) untouched — keep it that way.
- Steps 6-8 (real generation, freeze commit, exhaust) remain ILLEGAL until steps 4-5 are proven.
