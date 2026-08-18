# Iteration State — rapid-microscope

**After iteration:** 7 · **Date:** 2026-08-18 · **Verdict:** CONTINUE

## Journeys

5 passing (J-01 J-02 J-03 J-04 J-05) · 2 partial (J-06 J-10) · 3 failing (J-07 J-08 J-09) — 10 total

## Active blockers

- **J-06 steps 2-5 (dev):** `app/research/tick_recorder.py` + `vault.py` absent; no tranche, no sealed shard, no universe registration.
  Step 1 shipped storage capability only — the §2.6 dated vendor rule (`ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE`) stays deferred, so nothing stamps a unit today.
- **J-10 trap half (dev):** TR-2/4/12/19/20/22 have no dedicated test; TR-2/4/12/20 are vault-owned.
- **Three dev minors, all due before the corpus grows:** `walkforward.py:1039` registers the tick fold spec BEFORE the floor check at `:1043`
  (freezes `DIAGNOSTIC_GEOMETRY` + today's 11-date manifest hash); frozen dataclasses + `conditions: list` ⇒ `hash(event)` raises on preserved
  tape (`providers/base.py:25`/`:52`); `_tick_dataset_session_dates` (`walkforward.py:995`) drops `DatasetStore.list()`'s `_errors` channel.
- **Two owner rulings (human):** the depletion `available_at` stamp one quote early (`micro_observer.py:636`/`:657`); and must J-01's readiness
  photo show the real 12-symbol-day corpus when the store-scoped rig can only seed 2 PG fixtures?
- **Harness (human, outside goal mode):** `merge_ui_test_results.py:64` reads a bold `**FAIL**` as no verdict; this run's replay/QA lanes cited
  ten screenshots that are not on disk.

## Last 2 verdicts

- iter 7: CONTINUE — J-05 finished (the `11 < 105` refusal now comes from a real CLI, re-run by the evaluator against the real store);
  J-06 step 1 landed; one critical checksum fault introduced and fixed in-run.
- iter 6: ESCALATE — J-05's tick-family clause was still test-only; the browser lane's real FAIL parsed as a pass by the merge script.

## Do not redo

- **J-05 is complete** — `run_tick_family_fold_request` (`walkforward.py:1005`) + CLI `--family tick_legacy`; evaluator re-ran it against the
  real store → `11 < 105`, exit 1. Do not rebuild.
- **Card-5.1 preservation fields landed + proven** in `providers/adapters/base.py`, `providers/base.py`, `providers/historical.py`,
  `providers/adapters/alpaca.py`, `research/datasets.py`; the split-freeze checksum fix (`_tape_identity_rows`, `datasets.py:233-254`) is done and
  guarded by `test_datasets.py::test_the_frozen_split_guard_still_refuses_one_tape_re_fetched_with_preservation_fields`.
- **No second unit vocabulary** — `micro_features.QUOTE_SIZE_UNITS` is the only one (AST guard test). Do not touch `micro_features.py` /
  `micro_observer.py`: it forces a whole-corpus snapshot rebuild.
- **Frozen foundations re-verified at iter 7** — fingerprint `08e471b10130e1e2`, six `referee_*.py` SHA-256 identical to iteration 0,
  suite 3045 pass / 8 skip / 0 fail. Do not re-derive the baseline.
- **J-01..J-04 served values re-derived live at iter 7** (readiness 12/18/3.0089; 18 snapshots / 3,815,933 rows; joinable 2 `{range_trade: 2}`;
  scout chain ok). Do not re-verify without a cause.
