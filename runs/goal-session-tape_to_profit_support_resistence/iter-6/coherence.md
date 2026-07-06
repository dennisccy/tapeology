# Iteration 6 — Coherence Audit

**Iteration:** goal-tape_to_profit_support_resistence-iter-6
**Date:** 2026-07-06
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Scope of this iteration

Backend-only, machine-surface generalization of Data Contract row 43 (Named-strategy comparison
report). Files touched (per `git diff 0fb570480aa7c87e33e8bcbb38816d5d0dc1e6ee`, noise-excluded):
`apps/backend/app/research/pnl_scan.py`, `apps/backend/tests/test_no_execution_path.py`,
`apps/backend/tests/test_pnl_scan.py`, `README.md`. No frontend files touched (confirmed via diff
and via `reports/phase-goal-tape_to_profit_support_resistence-iter-6-ui-surface-map.md`, which
states "N/A — Backend-only phase"). No `runs/*`/`reports/*` churn outside harness bookkeeping; the
excluded-paths `--stat` shows only session-bookkeeping files (`goal-slice.md`, `snapshot-sha`,
`.steps/`, `telemetry.jsonl`, `trace.jsonl`, `project-story.md`) — no lockfile changed. `blueprint.md`
itself was not touched, matching the iter spec's "no blueprint.md edit this iteration" claim (row 43
was already registered at baseline).

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Row 43 — Named-strategy comparison report (`structure_tape` vs `v1`, per-split net R/net $/n/deltas, `survivor`/`overfit`/`robustness`) | OK | `apps/backend/app/research/pnl_scan.py:333-473` (`run_sweep`, generalized in place, same function — not a new module) |
| Row 43 — promotion (one ledger row + moved champion pointer) | OK | `pnl_scan.py:308-326` (`_promote`) calls the EXISTING single writer `append_validation_row` then the EXISTING single writer `store.set_champion_pointer`; verified only ONE call site of `set_champion_pointer` repo-wide (`apps/backend/app/research/store.py:1407` defines it, `apps/backend/app/research/pnl_scan.py:326` is its only caller) |
| Row 36 — profile-axis sweep (pre-existing, era-3) | OK | Unchanged behavior confirmed by reading the diff: `candidate_strategy_id=None` branch (`pnl_scan.py:366-372`) reproduces the exact pre-iteration call shape; `_promote`'s new `new_strategy_id`/`new_profile` params resolve to `(champion["strategy_id"], candidate_id)` for this axis — byte-identical to the prior hardcoded `store.set_champion_pointer(strategy_id=champion["strategy_id"], profile=candidate_id, ...)` |
| Net R / net $ / n measurement | OK — re-read, not recomputed | `_measurement()` (`pnl_scan.py:208-212`, untouched by this diff) still copies `result["aggregates"]` verbatim from the ONE `BacktestJobManager`/`BacktestRunner` computation (row 31); the new strategy axis reuses this same function for both champion and candidate — no second net R/$/edge computation path introduced |
| `provenance.assumptions` (audit-B1 disclosure string) | OK — not a new contract value | A static, config-independent caveat string (`BREAKTHROUGH_ANCHOR_CAVEAT`, `pnl_scan.py:143-150`) attached to the existing "provenance" field pattern already established for backtest reports (row 41: "echoed verbatim in each report's provenance"); disclosure prose, not a computed numeric value requiring its own owner/endpoint — matches DoD item "Audit B1 resolved... disclosed in the comparison report's provenance/assumptions" |
| Config (`promotion_min_sample_size`, `PROFILE_DEFAULT`, `STRATEGY_TAPE_ID`) | OK — reused, none added | `config.py` does not appear in the diff at all — confirms no new `Config` field was added (iter-1 lesson honored); `run_sweep`'s survivor gate (`pnl_scan.py:430-433`) reuses `config.promotion_min_sample_size` verbatim |

No duplicate computation, no non-canonical source, no unregistered value found.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route this iteration) | OK | Diff contains no `apps/frontend/*` changes; iter spec §"UI surface changes" states "None (no nav/page change...)"; `reports/phase-goal-tape_to_profit_support_resistence-iter-6-ui-surface-map.md` confirms "N/A — Backend-only phase" |

The `--strategy` CLI flag and the `provenance.assumptions` report field are machine-surface additions
to an existing CLI (`python -m app.research.pnl_scan`), which the blueprint IA already lists as a
"machine surface — no nav home." Nothing new needed a navigation path.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The README's new "Class-scaled risk, reward, and size..." bullet (README.md, capabilities list)
  documents a capability actually shipped in iter-5, not iter-6 — the iter-6 spec's own "Doc-parity
  rider" flags this as a deliberate catch-up of a missed iter-5 README edit, not new iter-6 scope.
  Noted for completeness; not a coherence defect (no code/computation/endpoint implication).
- None otherwise. This is a tightly-scoped, single-function generalization (`run_sweep`/`_promote`
  in the one row-36/43 owner module) with no new surfaces, no new config, and no new writers —
  the cleanest kind of iteration for this gate to audit.
