# Iteration State — rapid-microscope

**After iteration:** 3 · **Date:** 2026-08-17 · **Verdict:** ESCALATE

## Journeys

3 passing (J-01 J-02 J-03) · 6 failing (J-04..J-09) · 1 partial (J-10) — 10 total

## Active blockers

- **Owner ruling due (human):** a depletion measurement's `available_at` is stamped one quote early
  (`app/research/micro_observer.py:636/:657`, locked by `tests/test_micro_observer.py:291`).
  Harmless today; J-04 is the first journey that conditions a result on it. Do not invent a reading (T-1).
- **Dev, next iter:** `app/research/micro_join.py:381` discards the playbook store's error channel —
  a corrupt record is silently dropped from `joinable_corpus` while the docstring claims fail-closed.
- **Dev, next iter:** `joinable_corpus.band_touch_count` is a bare `0` a reader cannot tell apart from
  a real count of none — serve a "not enumerated" state (defining a touch is J-09's work).
- **Evidence make-up (passenger, never a goal):** J-01's readiness photo — this iteration's capture
  came out blank; the good one still shows the small rig corpus, not the real 12/18/~3.0.

## Last 2 verdicts

- iter 3: ESCALATE — J-03's join landed and verified (74 tests, real-store count = 2 signals, suite
  2866/8/0), but the engine demoted this full-typed iteration to lean (`budget-breach`), so the
  auditor never ran; J-04's trial ledger needs it.
- iter 2: CONTINUE — J-02 built, J-01's photo closed; the audit step caught two critical honesty
  defects review and QA both missed.

## Do not redo

- J-03's join is DONE: `micro_join.py` (+ `read_snapshot_rows`, `spread_bps`, the `joinable_corpus`
  readiness field). Only the two honesty fixes above are open.
- J-10's sentinel script is REPAIRED and green: `journey-scripts/J-10.json` steps 9-10 (static
  "Built from signature:" label; Playbook Signals on 2026-06-22). Do not re-point it again.
- Frozen-foundation re-checks PASSED (fingerprint `08e471b10130e1e2`, 6 `referee_*` hashes vs iter 0,
  engine + both playbook/context modules byte-unchanged, store guard clean). Re-check, never re-derive.
- `micro_accessor.py` stays OUT until J-05 owns it; J-03's plain reader is deliberate — J-05
  re-points that read. Do not build the accessor early.
- The 18 real-corpus snapshots were rebuilt (row total unchanged at 3,815,933) — no rebuild needed
  unless `micro_features.py`/`micro_observer.py` bytes change again.
