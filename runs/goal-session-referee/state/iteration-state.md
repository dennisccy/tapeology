# Iteration State — referee

**After iteration:** 12 · **Date:** 2026-08-16 · **Verdict:** GOAL_ACHIEVED

## Journeys

11 passing (J-01..J-11) · 0 failing · 0 unknown · 0 deferred — 11 total (J-11 new this iter,
added by the proposer inside the AUTO:journeys block; it carries `evidence_makeup` for an owed
walkthrough recording only)

## Active blockers

- none for the product. Human-owned, non-blocking: (a) this iteration's 6 changed product files
  + prior evidence files are uncommitted; (b) the shared recorder `demo_runner.py` has no
  `scroll` action, so the era has no walkthrough recording (framework tooling, not Tapeology
  code); (c) from iter-2 and outside this project, trendora's backend on :8255 is still down.

## Last 2 verdicts

- iter 12: GOAL_ACHIEVED — J-11 verified in the browser (basis line + new "Projected sessions"
  column, shipped 0.02 / 564 pair unmoved), all 11 journeys hold current evidence, coherence
  PASS, no open anti-goal, evaluator's own suite 2,695 collected / 2,687 passed / 0 failed.
- iter 11: GOAL_ACHIEVED — evidence-only round cleared every deferred row and the owed J-09
  capture; zero product diff.

## Do not redo

- J-11 shipped and verified: `accrual_basis` + the two per-candidate fields in
  `referee_registry.py::shortlist_response()`, one basis line + one "Projected sessions"
  column in `page.tsx::RefereeRegistrySection`, §9 addendum in `referee-statistical-spec.md`.
- The shipped calendar-day pair (`accrual_rate_sessions_per_day` / `projected_days_to_target`)
  is deliberately unchanged and must stay so — the recorded-session basis sits BESIDE it.
- `informative_sessions_per_pooled_session` is API-only by decision (assumptions.md iter-12);
  do not "fix" it by adding a second column unless the owner asks.
- Do not plan an iteration whose only content is the J-11 walkthrough recording — a capture
  item for finalization/a human, blocked on the shared recorder, not on the product.
- Four carried hardening items, none blocking: 4 Referee dirs into the store-scope guard;
  both-names-unknown certificate match (`referee_adjudicate.py:550`); dash-vs-unknown on a
  failed second fetch; stale `19/7/1` comment.
- Anti-goal entries from iters 6, 8 and 9 are all closed and re-confirmed — do not re-litigate.
