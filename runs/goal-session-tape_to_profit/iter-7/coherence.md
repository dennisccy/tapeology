# Iteration 7 — Coherence Audit

**Iteration:** goal-tape_to_profit-iter-7
**Date:** 2026-07-03
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Summary

J-07 (candidate-sweep harness, `python -m app.research.pnl_scan`) is a backend/CLI-only
iteration: `git diff 0bb67ad728cd80ba4296c3736f0ce5b293f816e9` touches only
`apps/backend/app/{config.py,research/{profiles.py,routes.py,store.py}}`, three backend test
files, one new fixture, two new backend files (`pnl_scan.py`, `test_pnl_scan.py`), and the
session's own state files (`blueprint.md`, `project-story.md`, telemetry/trace). Zero diff under
`apps/frontend/` and zero diff under `apps/backend/app/mcp/`, confirmed directly
(`git diff <sha> -- apps/frontend/` and `-- apps/backend/app/mcp/` both empty), matching the spec's
"Frontend Present: no" / "UI surface changes: None" and the anti-goal "MCP stays zero-diff."
`reports/phase-goal-tape_to_profit-iter-7-ui-surface-map.md` independently confirms "No UI surfaces
affected."

## Data Contract check

The iteration's one live coherence risk (per its own NOTES: "confirm exactly one champion source
and one ledger-append writer") is the champion pointer moving from a hardcoded constant
(`app/config.py`'s `STRATEGY_V1_ID`/`PROFILE_DEFAULT`) to a persisted, movable store row — this was
verified directly against the diff and the surrounding code, not just asserted by the spec:

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Row 33 champion pointer (read side) | OK | `apps/backend/app/research/profiles.py:52-58` — `profiles_projection(store, config)` returns `store.get_champion_pointer()` verbatim, no id-literal fallback (the retired `STRATEGY_V1_ID`/`PROFILE_DEFAULT` import was removed from this file). Route wiring: `apps/backend/app/research/routes.py:1614-1621` passes `registry.store` through. `get_champion_pointer` has exactly two production/reader call sites (`profiles.py:58`, `apps/backend/app/research/pnl_scan.py:271,366`) — grep-verified, no third reader. |
| Row 33 champion pointer (write side) | OK | `apps/backend/app/research/store.py:1407` (`JournalStore.set_champion_pointer`) is the ONE mutation method; its ONE production caller is `apps/backend/app/research/pnl_scan.py:256` (grep-verified: `apps/backend/app/research/routes.py`, `apps/backend/app/mcp/*`, and `apps/frontend/*` contain zero calls). The iteration additionally ships its own source-scan guard test enforcing this: `apps/backend/tests/test_pnl_scan.py:383-395` (`test_champion_pointer_setter_is_called_from_exactly_one_source_file`) asserts `callers == ["research/pnl_scan.py"]` over every file under `app/`. |
| Row 31 backtest computation (reused by the sweep) | OK | `apps/backend/app/research/pnl_scan.py:108-130` (`_run_backtest`) calls the existing `BacktestJobManager.create` + `run_sync` (`app/research/backtests.py`, zero-diff this iteration) and reads `store.get_backtest(id).payload["result"]["aggregates"]` verbatim — no second backtest/PnL arithmetic. `apps/backend/app/research/backtests.py` and `apps/backend/app/research/pnl_ledger.py` both show zero diff vs the snapshot (`git diff <sha> -- <path>` empty for both), confirming they were reused, not reimplemented. |
| Row 32 PnL-ledger append (promotion path) | OK | `apps/backend/app/research/pnl_scan.py:93,238-246` calls the EXISTING single writer `pnl_ledger.append_validation_row` (module unmodified). No new append/insert path into `pnl_ledger` appears anywhere in the diff. |
| Row 36 scan reports (new owner) | OK | `apps/backend/app/research/pnl_scan.py` is a new file matching its pre-registered owner exactly ("`app.research.pnl_scan` — computed once per run, written to the `--out` path", blueprint row 36). Report shape (`run_sweep`, `pnl_scan.py:362-369` + `_split_summary`, `:183-197`) — per candidate: train/holdout net R+$ deltas, n per split, per-dataset breakdown, `survivor`, `robustness`, `overfit` — matches row 36's registered definition field-for-field; no field invents a new un-registered concept. |
| Row 34 strategy/fee/notional config | OK | Read by the reused backtest runner only (`pnl_scan.py` never touches engine/trade arithmetic directly) — no second grammar. |
| `promotion_min_sample_size` (new config field) | OK — not a Data Contract entity | A config-owned threshold echoed into the row-36 report for provenance (`pnl_scan.py:364`), the same pattern row 31 already uses for `config_fingerprint` provenance. It is a gate parameter, not an independently displayed/computed value, so it needs no Data Contract row of its own. Its `config_fingerprint` exclusion (`apps/backend/app/config.py:990-1017,1268-1275`) is a single, self-documented design decision on the ONE existing fingerprint computation — not a second computation path. |

No new UI surface was added (see IA check below), so there is no "new UI surface fetching from a
non-canonical endpoint" to check — the only new reader of row 33/31/32 values is backend/CLI code
in the same trust tier as their existing owning modules, which is the established pattern
(`pnl_baseline.py` already reads `JournalStore` methods directly the same way).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| J-07 candidate sweep (`python -m app.research.pnl_scan`) | OK | No route/page/nav entry exists or is claimed. `apps/frontend/components/NavBar.tsx`: zero diff vs snapshot (`git diff <sha> -- apps/frontend/` empty). Blueprint IA table lists J-07's canonical home as "machine surface... CLI `python -m app.research.pnl_scan`" with no nav section — the iteration matches this exactly (spec: "UI surface changes: None. No new pages, panels, or nav entries."). |
| `/performance` champion display (unchanged surface, new underlying source) | OK | `/performance` continues to read `GET /research/profiles` (unchanged route path, unchanged response shape: `{"profiles": [...], "champion": {"strategy_id", "profile"}}`). No parallel page was created to show the champion; the existing home is reused. |

No new page, panel, or nav entry was introduced, so there is nothing to check for duplicate
homes or parallel shells beyond the above.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None specific to coherence. (For the record: the post-QA auditor's independent report,
  `docs/handoffs/goal-tape_to_profit-iter-7-audit.md`, flags one gap, B2 — the champion-pointer
  write in `_promote` is not wrapped in the same retry/lock discipline as some other writes — but
  that is a write-durability/robustness concern, not a single-source-of-truth or navigation
  violation: it still goes exclusively through the one `set_champion_pointer` mutation path, so it
  does not fall under this gate's Data Contract or IA rules and is left to that report.)
- `runs/goal-session-tape_to_profit/state/blueprint.md`'s row-33 Notes were extended additively
  this iteration to record the champion-pointer owner-model change (constant → persisted pointer).
  This is exactly the kind of contract upkeep this gate wants to see, not drift.
