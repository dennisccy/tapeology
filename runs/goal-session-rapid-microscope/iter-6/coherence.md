# Iteration 6 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-6
**Date:** 2026-08-17
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Summary

This iteration is backend-only: two files changed against snapshot `562c1ae1cb2d8e06664c35d1114bb84a4c41c6df`
— `apps/backend/app/research/walkforward.py` (+79/-14) and `apps/backend/tests/test_walkforward.py`
(+260 new/rewritten test lines). `git diff --stat` against the full noise-excluded tree confirms
these are the *only* two non-harness files touched (`runs/*`/`reports/*` churn is harness
bookkeeping). Zero frontend files touched — confirmed independently by `grep -ril
"walkforward|walk-forward" apps/frontend/` returning nothing, matching the ui-surface-map's own
"Confirmed by grep" line and the iter spec's "Frontend: None" / "UI surface changes: None"
declarations. `Frontend Present: yes` was declared solely to force the browser-qa lane to
dispatch (a framework workaround named explicitly in the spec), not because any UI changed.

## Data Contract check

The touched module (`walkforward.py`) is the blueprint's own registered owner for "Fold specs,
folds, sequences, decay view" (served by `GET /research/desk/micro/walkforward` and its
compute/runs siblings). Both changes land inside that canonical module and reuse pre-existing
canonical functions rather than forking new ones:

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Fold-building floor guard (TR-15) | OK — `require_sufficient_sessions_for_folds`/`InsufficientSessionsForFoldsError` are pre-existing (defined `apps/backend/app/research/walkforward.py:332,338`, outside every diff hunk); iter-6 only adds the call site at `walkforward.py:1148`, immediately before the existing `build_folds` call. No second implementation created. | `apps/backend/app/research/walkforward.py:1148` |
| §6.7 exposure registry (tick-corpus seed) | OK — reuses the exact pre-existing `has_any_exposure_entries` / `initialize_r2_exposure_registry` functions (imported at `walkforward.py:67-68`, unchanged by this diff) that the playbook seed already uses one block above; only a new `corpus_id` (`TICK_LEGACY_CORPUS_ID`) and window list are parameterized in. Not a duplicate computation of a registered value — it is the canonical writer, called a second time for a second corpus. | `apps/backend/app/research/walkforward.py:1127-1130` |
| Tick dataset inventory | OK — resolved via `config.dataset_dir_resolved()` + the canonical `DatasetStore` class from `datasets.py` (the blueprint's registered, unchanged datasets/replay owner) — matches the iter spec's explicit "no second inventory mechanism" requirement. | `apps/backend/app/research/walkforward.py:1128` (`from .datasets import DatasetStore` at `:59`) |
| `micro_readiness.py`'s served `exposure_state` (vault vocabulary) | OK — untouched. `test_walkforward.py`'s new TC-7 test imports and calls the canonical `build_readiness` from `micro_readiness.py` directly (not a re-derivation) and asserts every shard still reads `exploratory`, proving the walk-forward-internal registry and the readiness-served value stay the two separate mechanisms the blueprint's Data Contract note requires, never conflated. | `apps/backend/tests/test_walkforward.py:177-211` |
| `GET /research/desk/micro/walkforward` response shape | OK — no route file touched (`git diff --stat` against `routes.py`/`micro_readiness.py` is empty); serialized shape unchanged, matching the iter spec's "Data-contract additions: None." | n/a (no route diff) |

No duplicate computation, no non-canonical serving path, no new displayed value. Nothing to
register in the Data Contract this iteration.

## Information Architecture check

Zero new pages/routes/features — nothing to audit under Part B. The ui-surface-map's own summary
(`Frontend surfaces changed: 0`, `New pages/routes: 0`, `Navigation changes: no`) is consistent
with the diff, and the blueprint required no edit (re-confirmed by reading it: the IA table's
existing "Desk → Walk-Forward (J-05)" and "Desk → Microscope Readiness (J-01)" rows already cover
the surfaces this iteration's browser pass re-verifies; nothing new needs a home).

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new feature this iteration) | OK | n/a |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `walkforward.py`'s new private helper `_tick_dataset_session_dates` (`walkforward.py:983-999`)
  mirrors — by its own docstring's admission, "mirrored, not imported" — the same
  window_start_utc-to-ET-session-date conversion idiom that already exists privately in
  `micro_readiness.py`'s `_et_datetime` and `micro_accessor.py`'s `_session_date_for_dataset`.
  This is a third private copy of the same small utility transform. It is **not** a Data Contract
  violation: none of the three implementations feeds a registered/displayed value independently
  (this one only seeds an internal, non-served exposure-registry row list, and TC-7 proves the
  one value that *is* served — `micro_readiness.py`'s `exposure_state` — is computed exactly once,
  by its own canonical function). Flagging only as a DRY-style housekeeping note for a future
  iteration to consider factoring into one shared helper — general code deduplication is outside
  this gate's mandate (Data Contract coherence, not code review), so it does not affect this
  verdict.
