# Iteration 4 — Coherence Audit

**Iteration:** goal-clean_slate-iter-4
**Date:** 2026-07-24
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Summary

J-04 (the §0.4 Path B fingerprint epoch bump) is a backend/config/reports-only iteration: zero
`apps/frontend/` files touched, zero new pages/routes/endpoints, zero new displayed-value types.
Every file in the diff (`apps/backend/app/config.py`, 8 backend test files updating a pinned
literal, one new grep-based retirement-guard test, `reports/pnl/pnl-history.md`) is either (a) a
deletion of orphaned `Config` fields + a pruning of the matching fingerprint exclusion-set entries,
both edited **in place** inside the one existing canonical `Config.config_fingerprint()` method, or
(b) a test/report file consuming that same canonical method's output. No new function, module, or
endpoint that independently computes any Data-Contract value was introduced anywhere in the diff.
`README.md`'s diff (Case-Studies wording) predates this iteration's snapshot boundary — it is
iter-3's own `e224583` showcase/README-maintainer commit sitting between the WIP snapshot and HEAD,
not an iter-4 edit; it is prose, not code, and not evaluated as this iteration's change.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `config_fingerprint` | OK | `apps/backend/app/config.py` — same method, same class, same file; only its field list (23 deletions) and its `excluded` set (8 prunes) shrank in place. Live re-computation independently confirms `Config().config_fingerprint() == "08e471b10130e1e2"`, matching all 13 updated test-pin sites (`test_timeframe_history_api.py:194`, `test_levels.py:718`, `test_tradability.py:370`, `test_backtests.py:416,1485`, `test_profile_equivalence.py:121`, `test_pnl_scan.py:193,266,569,646`, `test_edge_report.py:213`, `test_setups.py:409,779`) plus a 14th site the diff also corrects (`test_profile_equivalence.py`'s `test_candidate_resolved_fingerprint_is_distinct_from_default`, a *derived* resolved-profile fingerprint that necessarily moves in lockstep with the base config — same canonical function, different input, not a second source). Independent `grep -rn "4d665603569b9dbf" apps/` (excluding the new retirement test's own literal) returns zero hits. |
| PnL ledger rows | OK | `reports/pnl/pnl-history.md` diff shows only an appended section 2 (new-epoch founding row) — section 1 is byte-unchanged. The new row is a new *instance* of the existing entity, produced by the same unmodified `pnl_ledger.py` writer / `GET /research/pnl/ledger` endpoint (neither file appears in the diff). Cross-checked against `runs/goal-session-clean_slate/iter-4/kept-route-after.txt`: only 2 of 28 kept routes differ from iter-3's baseline (`research.pnl_ledger`, `research.backtests.list`), and both differences are fully attributed in the capture's own header to this iteration's sanctioned actions (the appended row; the pre-existing page-size cap rolling 2 old backtest reports off a "100 most recent" window) — not a value recomputed elsewhere. |
| Every other Data-Contract row (bands, touch events, edge cells, bars, levels, strategy registry, datasets, backtests, profiles, taxonomy, route/nav inventory) | OK | Zero touch — none of `tradability.py`, `setups.py`, `edge_report.py`, `bars.py`, `levels.py`, `strategies.py`, `datasets.py`, `backtests.py`, `profiles.py`, `taxonomy.py`, `app/meta.py` appear in the diff. 26 of 28 kept routes in the I-9 recapture are byte-identical to iter-3's capture, corroborating "unchanged." |

No new displayed value/entity was introduced this iteration (the spec's own "Data-contract
additions: None" is accurate — the second ledger row is the existing entity, not a new one).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| *(none — no new page/route/feature this iteration)* | OK | `blueprint.md`'s IA already lists J-04's home as "backend/config + reports/pnl/pnl-history.md; no page — —"; the diff confirms zero `apps/frontend/` files changed, so there is nothing to check for nav reachability. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The dev handoff transparently logs a genuine gap in the iter-spec's own inventory: the 13
  enumerated I-9 pin-assertion sites missed a 14th literal (`test_profile_equivalence.py`'s
  candidate-resolved-profile fingerprint), caught only because the suite failed without it. This is
  not a coherence defect — it's the same single canonical `config_fingerprint()` function, invoked
  on a resolved-profile variant exactly as it always was — but it's worth the next iteration's
  planner noting that "13 pin sites" should read "14" if this file is ever re-audited or the pin
  moves again.
- Two stray prose references to now-deleted field names survive in comments/docstrings
  (`config.py`'s `backtest_list_max` exclusion comment, `backtests.py`/`test_backtests.py`
  precedent comments naming `study_null_baseline_seed`/`excursion_horizons_seconds`) — cosmetic
  only, no functional or Data-Contract impact, already flagged by the developer as out-of-scope
  under this iteration's surgical "touch only these lines" discipline.
