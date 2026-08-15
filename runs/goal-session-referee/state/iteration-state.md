# Iteration State — referee

**After iteration:** 6 · **Date:** 2026-08-15 · **Verdict:** CONTINUE

## Journeys

5 passing (J-01..J-05) · 4 failing (J-06 J-07 J-08 J-09) · 1 partial (J-10 — kept half held on iter-5 evidence; era-end clauses wait on J-09) — 10 total

## Active blockers

- none blocking the build. J-06 is unblocked today (every dependency passing, keyless/fixture).
- process, MUST fix next round: the browser + replay lane never ran this iteration
  (`Frontend Present: no` self-skips it), so J-01/J-02/J-03 and J-10's kept half went unchecked;
  a second skipped round turns a safe carry-over into a real evidence hole.
- human, non-blocking, outside this project: trendora's backend on port 8255 is still down since
  iteration 2 and needs a person to restart it.

## Last 2 verdicts

- iter 6: CONTINUE — J-05 registry verified passing by the evaluator's own 27-check probe + full
  suite (2,587 passed / 0 failed, own run); the audit lane caught and fixed a critical
  backdate-the-boundary hole that review and QA had both cleared.
- iter 5: ESCALATE — J-04 matched nulls verified passing, but the next depth had to be full.

## Do not redo

- J-05 is DONE: `app/research/referee_registry.py` (4 append-only stores, registration act,
  withdrawal, accrual fold, CLI) + `GET /registry` and `POST /registry/hypotheses` in
  `referee_routes.py`. Do not rebuild or re-scope them.
- SETTLED, do not reopen: the registration instant is server-stamped — no POST field, no CLI flag
  may name it (audit B1); a duplicate hypothesis id writes no phantom family (B2); null records
  stay keyed by `(observation_id, null_spec_signature)`; `min_attainable_p` is `2/(draws_used+1)`
  exact, `1/(draws_used+1)` seeded. Rulings in `state/assumptions.md`.
- CLOSED this round: `backing_bucket_eligibility_rate` serves `None` (not `0.0`) when nothing is
  measurable; TC-15's 7-eligible fixture discriminates the seeded draw; TC-16 pins
  `window_overlap_fraction`.
- STILL OPEN: settle the J-02 `epoch_anchor or 0.0` lead before J-06 pools strategy trades;
  `registry_response()` hides all four stores' integrity_errors (B4); `WithdrawalStore.record()`
  mis-reports a corrupted file (B3); 3 dead imports (B5); TC-15's expectation is re-derived (T1).
- NOT done despite existing: the certificate store has SHAPE only (no mint path, unreachable from any route/CLI) — J-08's job.
