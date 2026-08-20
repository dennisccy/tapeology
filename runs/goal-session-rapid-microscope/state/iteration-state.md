# Iteration State — rapid-microscope

**After iteration:** 18 · **Date:** 2026-08-20 · **Verdict:** ESCALATE

## Journeys

7 passing (J-01 J-02 J-03 J-04 J-05 J-07 J-08) · 2 partial (J-06 J-10) · 1 failing (J-09) — 10 total

## Active blockers

- **J-09 gated on an owner decision (human).** The sealed judge still takes its ECONOMIC floor and
  evidence label from the caller (`micro_sealed_evaluation.py:316`, `:407-408`): `floor_bps=0.0`
  turns a 0.001 bps effect into a permanent "pass" — the same exploit class TR-30 just closed on
  condition 1. Needs a ruling on where a candidate's pre-registered floor/evidence class come from
  (the candidate-registration ledger deferred since iter-12). NOT a halt: zero production callers,
  no sealed row in the real store, champion still `v1`.
- **J-06 step 4 is operator-owned (human):** a real Alpaca recording to spec §7.6 minimums; the
  standing instruction still says do NOT record real tape.
- **J-10's only remaining gap (dev, unblocked):** its step-2 deterministic-rerun check.
- **Spec-metadata bug (decomposer):** `Frontend Present: no` while the DoD names `browser-qa-agent`
  disables the browser AND replay lanes at ANY depth. The next spec must say `Frontend Present: yes`.

## Last 2 verdicts

- iter 18: ESCALATE — TR-30 landed and is mutation-proved, but the UI lanes never ran, QA/review
  passed anyway, and only the auditor caught the round's own regression (10th such escape).
- iter 17: ESCALATE — audit proved by execution that condition 1 read caller floors; owner ruled r9.

## Do not redo

- **TR-30 is DONE and proved** — `SEALED_MIN_OBSERVATIONS=30` pinned (`micro_sealed_evaluation.py:131`),
  `_resolved_floors` deleted, `floors` key refused at `:332`, breadth = `not_applicable_single_shard`.
  Evaluator mutations: 30→1 = 6 tests red; refusal neutered = 3 tests red.
- **Trap suite is 30/30** (TR-1…TR-30; TR-17 appears as TR-17a/b/c). Do not re-count or re-add.
- **B3/B4 fixtures already exist** from iter-17 (`test_micro_accessor.py:357`,
  `test_micro_observer.py:273`) — do not duplicate.
- **J-08.json / J-10.json empty-state assertions already refreshed** to `iter18-qa-universe` by the
  iter-18 auditor under that spec's pre-authorised policy. Do not revert.
- **J-07 has no golden script by design** (`state/golden-gaps` = `J-07`); no origin fence in
  `micro_sealed_evaluation.py` (iter-17); `SEALED_PASS_RULE_V1` keeps its name/version 1 (spec r9).
