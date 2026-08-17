# Iteration State — rapid-microscope

**After iteration:** 6 · **Date:** 2026-08-17 · **Verdict:** ESCALATE

## Journeys

4 passing (J-01 J-02 J-03 J-04) · 2 partial (J-05 J-10) · 4 failing (J-06 J-07 J-08 J-09) — 10 total

## Active blockers

- J-05 (dev, small): goal.md names "the tick-family fold request returns the typed floor-refusal naming
  `11 < 105`", but `app/` has ONE `build_folds` call site (`walkforward.py:1149`), always the playbook
  corpus, no corpus param anywhere — the string lives only in `test_walkforward.py:478` over synthetic
  dates. `_tick_dataset_session_dates` already resolves the real 11 dates.
- J-10 (blocked on J-06): traps TR-2/4/12/19/20 are J-06-owned per goal.md's own J-06 acceptance line.
- Pipeline (human/framework): `merge_ui_test_results.py:64` accepts only bare `PASS`/`FAIL` tokens, so a
  `**FAIL**` cell parsed as no verdict and a green headline reached `status.json` + closure. One line +
  one self-test row. Third consecutive iteration losing/corrupting browser evidence.
- J-01 (human ruling): the mandated rig seeds 2 PG fixtures by design, so the readiness panel can never
  show J-01's own 12/18/≈3.0 values. Seed the rig from the real corpus (its launcher forbids it) or
  amend J-01's acceptance. Do NOT schedule another retake.
- Owner rulings open: depletion stamp (`micro_observer.py:636/:657`); per-dataset "variants tried"; the percent-vs-bps unit pin (before J-09).
- New minor (J-06 scope): `_tick_dataset_session_dates` (`walkforward.py:995`) drops `list()`'s `_errors`
  channel (a corrupt shard is silently, permanently under-seeded) and the seed has no sealed filter — a
  sealed window could later be marked exposed forever. Seed by recorded legacy identity.

## Last 2 verdicts

- iter 6: ESCALATE — J-05's two gaps closed and proven live, J-10's sentinel green at last; but a P1
  browser FAIL was consumed as PASS by a parser defect, and J-06 step 1 touches frozen store/engine
  byte-compat, so the auditor must not be budget-demoted next run.
- iter 5: ESCALATE — walk-forward built, but two goal-named items unwired and the browser lane skipped.

## Do not redo

- J-05's TR-15 wiring (`walkforward.py:1148`) + CLI catch (`:1220-1228`) — DONE, re-proved live.
- Tick-corpus exposure seed (`TICK_LEGACY_CORPUS_ID`, `walkforward.py:1127-1130`) — DONE, 11 windows
  covering all 12 symbol-days, idempotent; readiness still serves `exploratory` for all 18 shards.
- The real 154-session diagnostic run (5 folds / 100 sessions) and J-01..J-04's machinery — verified.
- `Frontend Present: yes` WORKED — keep it. Blank `UT-02-microscope-readiness*.png` are dead; cite `UT-02-fail.png`.
