# goal-tape_to_profit-iter-8 Audit Report

**Date:** 2026-07-05
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

J-09's baseline-edge report machinery (`python -m app.research.edge_report --out <path>`) is
implemented exactly to spec: strictly read-only, single-computation-path, honest in every failure
and empty state, and default-frozen. I independently re-ran the load-bearing tests, exercised the
real CLI end-to-end (byte-identical re-runs confirmed by SHA256), re-pinned the config fingerprint,
and source-scanned the module for forbidden execution/promotion calls — all clean. Every DEFINITION
OF DONE item is genuinely met, not merely claimed. No critical or important issues found; no fixes
required.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (no_change_needed): pure-render-equality test reads the store, not a literal HTTP GET**
`test_edge_report.py:304` (`test_every_displayed_value_matches_a_fresh_independent_backtest`)
compares each displayed `net_r`/`net_usd`/`n` against `store.get_backtest(id).payload["result"]
["aggregates"]` rather than an HTTP `GET /research/backtests/{id}` as the DoD wording literally
says. I read the route (`routes.py:1561-1569`): it is `return {"backtest": record.payload}` — a
verbatim pass-through with zero transformation, so `store.get_backtest(id).payload` is byte-identical
to what the endpoint serves under `["backtest"]`. The test is in fact *stronger* on the load-bearing
axis (it runs a FRESH independent backtest and asserts identical numbers, proving there is no second
computation path), and only weaker on literal-surface fidelity. Already flagged by the reviewer as a
NOTE. Not a functional gap; no fix warranted.

**B2 — OBSERVATION (no_change_needed): dedicated guard test checks only the two promotion-API calls**
`test_edge_report_source_calls_no_promotion_api` (`test_edge_report.py:425`) asserts only that
`edge_report.py` never calls `.set_champion_pointer(` or `append_validation_row(`, not the
broker/order/account clause. The dev handoff explains why: embedding those literal pattern strings
as forbidden-data in the test would itself trip the repo-wide `test_no_execution_path.py` scanner.
I verified the broker/order clause IS genuinely enforced for the new module: `edge_report.py` is
NOT in `TIER1_ALLOWED`/`TIER2_ALLOWED`, so `test_no_order_account_or_broker_execution_code_anywhere`
scans it, and `test_scan_is_not_vacuous` now explicitly asserts `edge_report.py` is in the scanned
set (`test_no_execution_path.py:117`, the one additive line this iteration). I also grepped the
module directly for every Tier-1/Tier-2 pattern plus the two promotion calls: zero matches. Net DoD
coverage is identical, split across two files. Reasonable call; no fix.

**B3 — OBSERVATION (no_change_needed): `_beats_null` checks both R and $ though they are proportional**
`_beats_null` (`edge_report.py:145`) gates on `net_r > null net_r` AND `net_usd > null net_usd`.
Under the fixed `$-per-R` notional these are always proportional, so the second clause is currently
redundant. The dev flagged this honestly and kept it to match the codebase's established "gate on
both R and $ jointly" convention (`pnl_scan._is_positive`). Defensive, not a defect.

### Frontend Findings

None. `Frontend Present: no`. I confirmed zero changes under `apps/frontend/` (`git status
--porcelain apps/frontend/` → 0) — no page, panel, nav, or `/meta/ui-routes` change, exactly as
scoped.

### Test Findings

**T1 — OBSERVATION (no_change_needed): `dataset_id` tie-break tested as a pure function**
`test_rank_orders_by_net_r_descending_with_dataset_id_tiebreak` (`test_edge_report.py:287`) calls
`edge_report._rank()` directly with representative measurement dicts rather than engineering a real
float tie between two recorded datasets (impractical to arrange deterministically). This tests pure
JSON sort/shape logic — no tape/PnL data is fabricated — and every other test in the suite uses
real recorded datasets. Honestly disclosed; acceptable.

### Anti-goal note (not a finding): `docs/goal.md` shows a git diff

The DoD line 98 asks for "zero change under `docs/goal.md`." A literal `git diff` DOES show goal.md
changed — but the diff is the **human-authored J-09 journey** added ABOVE the (still-empty)
`<!-- AUTO:journeys -->` marker, in the human Must-have region; the Anti-goals section and every
existing J-01–J-08 journey are untouched. This is the *premise* of the iteration (the spec's own
BACKGROUND calls J-09 "human-authored … absent from journey-history.json"), not a dev or
goal-proposer edit: the dev's `changed_files` lists only the 3 backend files, and the proposer
"dry-stopped" per the archived memory. The DoD's intent — the enhancement loop / dev must not mutate
goal.md — is satisfied. Not a violation.

---

## 3. Domain Assessment

The core domain logic is correct and honest across all four critical anti-goals this iteration
touches:

- **Single source of truth.** The report reads row-31 `aggregates` and `null_baseline.aggregates`
  VERBATIM via `_measurement` (`edge_report.py:114-117,141`); the positive-edge flag is a set of
  boolean comparisons on those already-persisted numbers (`_is_positive_edge`, `_beats_null`) — no
  arithmetic re-derives R/$ anywhere. Every backtest goes through the one `BacktestJobManager.create`
  + `run_sync` path. I ran the real CLI and confirmed the displayed numbers (holdout net_r
  `0.3334000000001356`, null net_r `5.101632142856395`, etc.) are the raw measured aggregates, and
  the test assertions match those exact floats — empirically grounded, not hand-typed.
- **No profit claims / no advice.** `REGISTER` ("simulated — assumed fees/slippage — not indicative
  of live results") sits at report top level; every `$` figure appears beside its R, its n, and its
  null baseline; "positive-edge" is a disclosed-threshold measurement, never a live-results or
  edge claim. Live output confirms.
- **No train-only promotion — satisfied by construction.** The module promotes/appends NOTHING: no
  `_promote`, no ledger write, no pointer move. My source scan found zero mutation calls other than
  the benign `store.close()`; the only persisted writes are the allowed row-31 backtest rows. Train
  rows carry NO `positive_edge` key at all (honest omission), confirmed in live output — only
  hold-out rows are flagged.
- **No fabricated data — honest failure states.** Integrity failure aborts at `_split_datasets`
  before any backtest (`EdgeReportError`, nothing written, `store.list_backtests() == []` asserted);
  a non-`done` backtest raises explicitly; empty registry and zero qualifiers both yield the exact
  literal `"no positive-edge dataset"` at exit 0 (verified live). Missing Alpaca credentials are
  correctly out-of-module — `edge_report` never records, so the existing 503 gate
  (`test_real_data_gate.py`, re-run green) is the surfaced state, no new credential code.
- **Default frozen.** No `Config` field added; `config.config_fingerprint()` independently re-computed
  to `4d665603569b9dbf`; `test_profile_equivalence.py` green.

The champion is read verbatim from the pointer (`get_champion_pointer` → `{strategy_id, profile}`)
and both the report echo AND every backtest run use it — proven by the pointer-move test. Ranking is
deterministic (net R descending, `dataset_id` tie-break), and two independent fresh-state CLI runs
produced byte-identical output (identical SHA256 `092e865b…`).

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | None. No CRITICAL or IMPORTANT issues found; all findings are OBSERVATION-level, honestly disclosed. |

---

## 5. Recommended Next Step

**Proceed.** J-09's report machinery meets every DEFINITION OF DONE item on keyless evidence I
independently verified (targeted suites green, CLI observed end-to-end, fingerprint pinned, source
scanned read-only, zero diff to frontend/mcp/config/store/pnl_scan). Hand to the goal-evaluator to
mark J-09 `passing`; per the spec this closes the era (J-01–J-09) and is a GOAL_ACHIEVED candidate.
The real ≥3-symbol × ≥2-regime library recording remains the operator's credentialed action, out of
scope here as specified. The three OBSERVATIONs need no follow-up; the two carried-forward iter-7
polish items (store.py B2/T1) were correctly not triggered this iteration.
