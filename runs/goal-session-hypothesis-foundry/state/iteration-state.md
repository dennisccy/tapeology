# Iteration State — hypothesis-foundry

**After iteration:** 1 · **Date:** 2026-08-26 · **Verdict:** CONTINUE

## Journeys

0 passing · 2 partial (J-01 J-02) · 6 failing (J-03 J-04 J-05 J-06 J-07 J-08) — 8 total; first real screenshots of the session exist (`reports/qa/goal-hypothesis-foundry-iter-1-evidence/`).

## Active blockers

- **Era-open baseline invisible to the scoped QA rig → J-01 step 5 cannot be photographed (owner: dev).** `foundry_source_registry.resolve_foundry_dir()` derives the foundry dir from `TAPEOLOGY_DATASET_DIR`, which the rig points at a throwaway root, so `GET /research/desk/micro/foundry` returns `era_open_baseline: null`. The real file `apps/backend/.data/foundry/era_open_baseline.json` is genuine (evaluator recomputed all six Referee hashes — matched). Fix = give the rig the REAL artifact (copy it in, or set `TAPEOLOGY_FOUNDRY_DIR`); planting invented rig numbers is an anti-goal.
- **`SourceRecord` missing §1.4 `source_hash` + `alternatives`** (`foundry_source_registry.py:159`) while the new spec claims the list is mirrored verbatim — J-02 step 3 needs `alternatives`; must land before J-06 authors real sources (owner: dev).
- Operator decision (not agent-fixable): `session.json` caps iterations at 60; `docs/goal.md` recommends `--max-iter 80`.

## Last 2 verdicts

- iter 1: CONTINUE — browser lane repaired honestly; Foundry panel + compiler machinery landed, but J-01's baseline block and J-02's whole UI are still unproven on screen.
- iter 0: CONTINUE — baseline; era paperwork done, all Foundry machinery unbuilt, browser lane refused by the store-scope guard.

## Do not redo

- **QA-rig fixture bug FIXED + verified** — `seed_micro_graduation_iter18_fixture.py::_observation()` declares `value_unit=wf.WF_OBSERVATION_UNIT`; `walkforward.py` untouched, no test silenced; the :8301 rig boots and browser QA drove a live Chrome pass. Do not revisit the guard.
- **J-01 steps 1-4 DONE + verified** — panel names rapid-microscope (closed) / hypothesis-foundry (active) on screen; archive, dated note, untouched prior-era run dir, dead proposer opt-in re-confirmed. Only step 5 (baseline render) remains.
- **Era-open baseline recorded once** — 3787 passed / 8 skipped / 0 failed, tsc 0, `config_fingerprint 08e471b10130e1e2` (pinned), six Referee hashes. Do not re-record.
- **Binding Execution Order step 2 machinery SHIPPED** — `docs/hypothesis-foundry-spec.md`, `foundry_source_registry.py`, `foundry_compiler.py`, `GET /research/desk/micro/foundry`, 40 tests (TC-1..TC-15) re-run by the reviewer. Next = step 3 (interpreter/Scout adapter, family, freeze).
- **Sources/Compiler + all other Foundry read surfaces stay deferred** to the single consolidated read-surface iteration (step 5) — settled in `state/assumptions.md` iter-1.
- Steps 6-8 (real generation, freeze commit, exhaust) remain ILLEGAL until steps 2-5 are proven.
