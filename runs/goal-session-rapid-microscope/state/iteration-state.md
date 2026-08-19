# Iteration State — rapid-microscope

**After iteration:** 11 · **Date:** 2026-08-19 · **Verdict:** CONTINUE

## Journeys

6 passing (J-01..J-05, J-07 — J-07 CARRIED `DEFERRED-BUDGET`, not re-run) · 2 partial (J-06 3-of-5
steps, J-10 traps 20-of-28 + sentinel green) · 2 failing (J-08, J-09 — never targeted) — 10 total

## Active blockers

- **Nothing is owner-owed — a first this session.** r6 (08-18) settled the sealed-verdict owner,
  lineage boundary, corrupted-ledger fail-closed, depletion revealing quote; r7 (08-19) the nonced
  commitment + coarse volume buckets. All 6 open anti-goal items are DESIGNED-BUT-UNBUILT, 0 critical.
- **Hard gate (dev):** J-06 step 4 (credentialed tranche) waits on all four of r6 §7.8 verify_chain,
  r7 nonced commitment, r7 coarse buckets, symbol/date normalization.
- **Dev cleanups:** iter-11's phase spec OUT OF SCOPE still calls the corrupted-ledger question "an
  open owner question" (ruled a day earlier — do not inherit); and `state/golden-gaps` (`J-07`) was
  deleted with no `J-07.json` golden written, silently dropping J-07's regression cover.

## Last 2 verdicts

- iter 11: CONTINUE — the r5 opaque-pool fix is BUILT and survived attack (auditor drove the real
  `run_tick_recording` path; evaluator re-verified real-store inertness); suite 3192/3184/8/0, 0 regressions.
- iter 10: ESCALATE — J-07 newly passing, but r5's design was wholly unbuilt and the developer
  improvised two undefined spec procedures instead of stopping.

## Do not redo

- **Withhold predicate DONE + sole choke point** — `vault.unresolved_pool_universe_by_dataset_id`, read
  by `micro_snapshots.exclude_withheld`/`withheld_dataset_ids_for_store` (8 enumerators inherit it),
  `micro_readiness.build_readiness`, `routes.py:get_withheld_dataset_ids`. Never add a second one; the
  beyond-plan `routes.py` delegation is load-bearing — keep it.
- **Recorder progress DONE (aggregate-only)** — `tick_recorder._progress_view`'s 10-field whitelist on
  GET + POST echo, no bypass (TC-7). Never re-add `progress.outcomes`; only exactness is open.
- **TR-2 DONE as a real inference trap** — `test_vault.py` TC-8/TC-9 + the pre-fix counter-test; only
  widen its forbidden substrings to symbol + session date (audit T1).
- **Frozen rails re-verified at iter 11** — fingerprint `08e471b10130e1e2`, six `referee_*.py` = iter 0,
  MCP 22-tuple, 0 `.tsx`/`.ts` diffs, real `.data` untouched (18 datasets, no `micro_vault` dir).
- **Evidence re-takes are PASSENGER work** — UT-04 wrong panel, UT-09 blank; both carry `evidence_makeup: true`.
