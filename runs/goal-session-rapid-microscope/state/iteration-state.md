# Iteration State — rapid-microscope

**After iteration:** 1 · **Date:** 2026-08-17 · **Verdict:** ESCALATE

## Journeys

0 passing · 2 partial (J-01 J-10) · 8 failing (J-02 J-03 J-04 J-05 J-06 J-07 J-08 J-09) — 10 total

## Active blockers

- **Empty tick corpus on the browser QA rig (owner: dev).** The forced store-scoped backend
  (`:8301`, from `apps/backend/scripts/start_scoped_qa_backend.sh`) points `TAPEOLOGY_DATASET_DIR`
  at a fixture dir with 0 tick files, so `/desk`'s Microscope Readiness panel photographs as
  0/0/[]. This is the ONLY reason J-01 is not passing, and it will block J-06/J-08/J-09 the same
  way. Usable fixtures already exist at `apps/backend/tests/fixtures/datasets/`.
- **MINOR (owner: dev).** `apps/backend/tests/test_desk_ui_guards.py:510-559` — 5 checks sit in the
  wrong test function; both function names now misdescribe their bodies.

## Last 2 verdicts

- iter 1: ESCALATE — the readiness endpoint is genuinely correct on the real corpus (evaluator
  re-computed 12 / 18 / 3.0089 / all floors unmet), but the browser lane cannot see any tick data,
  and J-02 next touches the two byte-frozen files; both warrant the full pipeline.
- iter 0: CONTINUE — verify-only baseline; era-open numbers recorded, nothing built yet.

## Do not redo

- `micro_readiness.py` + `GET /research/desk/micro/readiness` are built and verified correct on the
  real store (12 symbol-days / 18 shards / 3.0089 session-equivalents / 3 floors `floor_unmet` /
  `integrity_errors: []`); `tests/test_micro_readiness.py` 31/31 green. Only its browser screenshot
  is missing — do not rebuild or re-derive the module.
- The `/desk` "Microscope Readiness" section exists below "Referee Runs", renders the served body
  verbatim with zero client-side arithmetic, non-colliding testids; coherence.md = COHERENCE-PASS.
- Era-open invariants re-verified by the evaluator: fingerprint `08e471b10130e1e2`, 6/6
  `referee_*.py` SHA-256 match iter-0, observer-equivalence + golden trace green, MCP still a
  22-tuple, store-scope guard CLEAN. No need to re-baseline them.
- `REFEREE_TICK_GATE_SYMBOL_DAYS` (150) is imported from `referee_evidence.py`, never duplicated.
- `WF_TRAIN_MIN_SESSIONS`=40 / `WF_TEST_MIN_SESSIONS`=20 already live in `micro_readiness.py`
  (~line 580); J-05's `walkforward.py` must import or supersede them, never re-declare a value.
