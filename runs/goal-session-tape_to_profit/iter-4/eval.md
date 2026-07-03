**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

# Iteration 4 Evaluation

## Summary

J-04 is newly passing: the append-only PnL ledger shipped with the founding baseline row (strategy v1 on profile `default`, fixture train + hold-out), served identically over `GET /research/pnl/ledger`, the committed `reports/pnl/pnl-history.md`, and the MCP `pnl_ledger` tool — the last registered tool to leave the honest-404 state. All four required-still-passing journeys (J-01, J-02, J-03, J-08) re-verified with explicit result rows and screenshot evidence; full backend suite 983 passed / 1 skipped (up from 952 collected, one sanctioned vacuous-test removal replaced by a stronger live test), engine equivalence 7/7, COHERENCE-PASS. Remaining: J-05, J-06, J-07.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing (deterministic replay, all expects held; nav 3 links from route map, honest not-found end state per golden script) | reports/qa/goal-tape_to_profit-iter-4-evidence/J-01-verify.png |
| J-02 | passing | passing (5 datasets listed w/ checksums + frozen splits, `integrity_errors: []`; re-tag → 409; detail verbatim; unknown id → 404) | reports/qa/goal-tape_to_profit-iter-4-evidence/UT-J-02-datasets-list-200.png (+2) |
| J-03 | passing | passing (identical POST re-run: new ids, byte-identical aggregates AND null baseline, seed 1729, register + full provenance) | reports/qa/goal-tape_to_profit-iter-4-evidence/UT-J-03-backtest-rerun-byte-identical.png |
| J-04 | failing | **passing** (iter-0 404 → 200 flip; founding row honest: `baseline: null`, candidate net R+$ per split, n=1 both splits labeled insufficient sample, full provenance, register verbatim; POST/DELETE → 405) | reports/qa/goal-tape_to_profit-iter-4-evidence/UT-J-04-research-pnl-ledger-200-flip.png, UT-J-04-founding-row-honesty.png, UT-J-04-write-405-refusal.png |
| J-05 | failing | failing (fresh negative evidence: nav still 3 links, no `/performance` — correct per the blueprint no-dead-link rule) | reports/qa/goal-tape_to_profit-iter-4-evidence/J-01-verify.png |
| J-06 | failing | failing (fresh negative evidence: `test_mcp_server.py` stdio honest-404 leg now exercises `/research/profiles`) | reports/qa/goal-tape_to_profit-iter-0-evidence/UT-J-06-research-profiles-404.png |
| J-07 | failing | failing (untouched; no sweep harness exists) | reports/phase-goal-tape_to_profit-iter-0-ui-test-results.md |
| J-08 | passing | passing (deterministic replay: SIM-BUYER → Buyer Control and SIM-SELLER → Seller Control asserted by script expects; journal + studies render) | reports/qa/goal-tape_to_profit-iter-4-evidence/J-08-verify.png |

**Cross-surface verification performed by the evaluator (not trusted from handoffs):** the founding row's train aggregates (`net_r -0.16000000000001136`, `net_usd -16.000000000001137`, `n 1`) in the J-04 screenshots equal the independent J-03 backtest-re-run capture EXACTLY; both dataset ids + checksums in the row's provenance appear verbatim in the J-02 datasets-list capture; the committed `reports/pnl/pnl-history.md` carries the same values, ids, checksums, dd-MM-yyyy date (03-07-2026), register string, and insufficient-sample labels. The verbatim-copy / single-source-of-truth contract is proven across three independent evidence captures plus the committed render.

Note on `UT-J-04-founding-row-honesty.png`: the `all_honesty_checks_true: false` aggregate is a naive every-true fold artifact — `row_count: 1` is non-boolean and `train_pooled_with_holdout: false` is the *desired* false; every individual check holds its desired value. The PASS verdict on individual checks is correct.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No live execution path (critical) | OK | Grep of new modules (`pnl_ledger.py`, `pnl_baseline.py`, `pnl_history.py`) clean; `test_no_execution_path.py` green; ledger has no REST write surface (405 screenshot) |
| No profit claims / no advice (critical) | OK | Register verbatim on REST + markdown; every $ beside R and n; both splits labeled insufficient sample (n=1 < 5); honest negative train figure preserved; markdown states "not a profitability claim" |
| Default engine outputs frozen (critical) | OK | Zero diff to `app/engine/`, `backtests.py`, `datasets.py` (verified via `git diff --stat` against snapshot 5f7bb266); equivalence 7/7 |
| No train-only promotion (critical) | OK | No promotion logic exists; founding row is a measurement with explicit `baseline: null`; train/hold-out never pooled (payload + markdown) |
| No ML / online tuning | OK | None introduced |
| No fabricated data (critical) | OK | Founding baseline side explicit null (never zeros); values verbatim copies of persisted row-31 aggregates (equality tested + evidence-cross-checked); duplicate id → `DuplicateEnhancementError`; corrupt/missing report → `LedgerCompositionError`, nothing appended |
| Single source of truth (critical) | OK | One writer (`append_validation_row`), one serving read (`ledger_projection`) consumed by route, markdown, and MCP proxy; MCP byte-identity tested; REST-vs-markdown values identical (evaluator-verified) |
| MCP read-only (critical) | OK | Evaluator inspected the exact diff: two documentation-string hunks only in `app/mcp/__init__.py`, zero proxy/handler logic |
| Persistence stays scoped (critical) | OK | Ledger in journal SQLite via versioned v8→v9 migration (committed v8 fixture); seeding is an explicit CLI action; cockpit tape unpersisted, untouched |
| Enhancement loop stays inside its box (critical) | OK | `docs/goal.md` unmodified; AUTO:journeys block empty |

The only UPDATE statement in the store diff is `UPDATE schema_version SET version = 9` — migration bookkeeping, explicitly sanctioned by the spec; no UPDATE/DELETE targets `pnl_ledger`.

## Coherence

`runs/goal-session-tape_to_profit/iter-4/coherence.md`: **COHERENCE-PASS** — no Data Contract violation (row 32 implemented with one writer + one serving read; register imported from the single `REGISTER` constant), no IA violation (machine-surface home exactly as the blueprint's J-04 row declares; no dead Performance link ahead of J-05).

## Next-Step Recommendation

**Target J-05** (the `/performance` page) at **lean** depth — the first frontend iteration of the era, per the dev handoff's suggestion and the J-02 → J-03 → J-04 → **J-05** chain. All data it needs is now live. Scope: fourth top-level page rendering `GET /research/pnl/ledger` rows verbatim (no client-side recomputation; every $ beside its R and n; register visible; train/hold-out separate; insufficient-sample labels — the founding row is n=1 on both splits, so the page's insufficient-sample rendering is exercised by real data), champion summary per the blueprint, Performance nav entry rendered from `/meta/ui-routes` (adding `/performance` to the route map — this changes the J-01 nav assertion and likely requires updating the stored golden expectations for the 3-link nav), dark cockpit design language. Browser lane must verify the nav on every page and the page-value-equals-API-value acceptance. After J-05: J-06 (profiles), then J-07 (sweep).

Heads-up for J-07 planning (recorded in lessons.md): the fixture windows arm exactly n=1 trade per split, below the configured minimum of 5 — the sweep's promotion gate semantics on the fixture pair need deliberate test design (config-controlled minimum), since no candidate can reach n ≥ 5 on the current fixtures.
