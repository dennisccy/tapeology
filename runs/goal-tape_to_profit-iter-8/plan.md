# goal-tape_to_profit-iter-8 Execution Plan

## Context

J-01–J-08 are `passing`; iter-7 reached GOAL_ACHIEVED. `docs/goal.md` since gained a ninth
human-authored Must-have, **J-09**, making the operator's real-scale edge measurement a
first-class journey. J-09's headline mentions Alpaca credentials, but its CODE acceptance is
100% keyless: the record/backtest capabilities it depends on are already `passing` (J-02/J-03),
and the only NEW deliverable this iteration is the **baseline-edge report machinery** — a
read-only CLI that ranks the frozen champion's simulated hold-out edge per registered dataset.
Recording the real ≥3-symbol × ≥2-regime Alpaca library is the operator's own later action
(OUT OF SCOPE here — "only enlarges the data, changes no behavior," per goal.md's own words).

`runs/goal-session-tape_to_profit/state/blueprint.md` was already updated THIS iteration by the
goal-decomposer (Data Contract row 37 + the machine-surface CLI entry for
`python -m app.research.edge_report`) — no blueprint edit is needed from backend-data.

## What to Build

`apps/backend/app/research/edge_report.py` — `run_edge_report(store, dataset_store, config) ->
dict` + `python -m app.research.edge_report --out <path>` CLI. Modeled structurally on
`app/research/pnl_scan.py` (same disciplines: champion read, one `BacktestJobManager`
computation path, split separation, deterministic id/wall-clock-stripped render, `ScanError`
honest-failure pattern) but **strictly read-only** — it has no `_promote`, no ledger write, no
champion-pointer move. This is what makes "no train-only promotion" satisfied by construction:
there is nothing to promote.

- Read the CURRENT champion via `store.get_champion_pointer()` — never hardcode `v1`/`default`.
- For every registered dataset, train and hold-out kept in **separate, never-pooled** sections,
  backtest the champion through the EXISTING `BacktestJobManager.create` + `run_sync`, then read
  the persisted `aggregates` (`net_r`, `net_usd`, `n`) and `null_baseline.aggregates` **verbatim**
  — no second R/$/edge computation anywhere.
- Rank each split's own datasets by that dataset's measured champion edge (descending), tie-break
  by `dataset_id` ascending, so ordering is reproducible.
- Flag a dataset positive-edge ONLY when its **hold-out** `net_r > 0 AND net_usd > 0 AND n >=
  config.pnl_min_sample_size AND` it beats its own null baseline (see Design Notes #1 for the
  exact comparator). Emit an explicit `"no positive-edge dataset"` finding (exit 0) when none
  qualify — including the true-empty case (zero datasets registered at all).
- Attach the imported `REGISTER` string (from `backtests.py`) beside every $ figure — never
  re-declare it.
- Deterministic `--out`: sorted-key JSON, strip every per-run-random field (fresh backtest-report
  ids, wall-clock) before writing — the `pnl_scan._render_report` precedent, reused not forked.
- Honest failure states via a new `EdgeReportError` (the `ScanError` pattern): a dataset failing
  integrity verification, or a backtest ending non-`done`, aborts with an explicit error and
  NOTHING written.
- A dedicated grep-style guard (in the new test file) proving `edge_report.py`'s own source
  contains no broker/order/account/execution pattern and never calls `set_champion_pointer` or
  `append_validation_row`.

No frontend, no REST endpoint, no MCP tool, no `/performance` change — this is a pure
machine-surface CLI artifact (Data Contract row 37, already registered in blueprint.md).

## Agents Required

- backend-data: yes -- `edge_report.py`, `test_edge_report.py`, the dev handoff, and (optional,
  see Design Notes #5) one consistency line in `test_no_execution_path.py`. No other production
  file changes are expected.
- frontend-ux: no -- zero frontend files change (OUT OF SCOPE explicitly bars any page/panel/nav
  change; confirmed by the spec's own `**Frontend Present:** no` metadata line).

Frontend Present: no

## Files to Create/Modify

- `apps/backend/app/research/edge_report.py` (new) -- the report engine + `__main__` CLI entry.
- `apps/backend/tests/test_edge_report.py` (new) -- full test matrix (see Key Test Scenarios).
- `docs/handoffs/goal-tape_to_profit-iter-8-dev.md` (new) -- required dev handoff; document the
  two judgment calls in Design Notes #1 and #2 explicitly (matching this project's own precedent
  of naming flagged judgment calls in handoffs, e.g. iter-7's fingerprint-exclusion note).
- `apps/backend/tests/test_no_execution_path.py` (optional, recommended) -- add
  `"backend/app/research/edge_report.py"` to `test_scan_is_not_vacuous`'s explicit path-presence
  assertions, mirroring the precedent set for `pnl_scan.py` at iter-7. Not DoD-mandated (the
  repo-wide glob scan already covers the new file automatically with zero edits), so skip if
  time-constrained — do not let it block the iteration.

**Explicitly NOT touched** (confirm via `git diff` before handoff): `app/research/store.py`,
`app/research/pnl_scan.py`, `app/research/profiles.py`, `app/research/routes.py`,
`app/research/backtests.py`, `app/research/datasets.py`, `app/research/pnl_ledger.py`,
`app/config.py`, `app/mcp/*`, `apps/frontend/*`, `docs/goal.md`,
`runs/goal-session-tape_to_profit/state/blueprint.md` (already updated by the decomposer this
iteration).

## Design Notes (read before implementing — resolves the non-obvious judgment calls)

1. **"Beats its own null baseline" comparator is underspecified in the spec text.** Recommend
   requiring BOTH the champion's hold-out `net_r > null net_r` AND `net_usd > null net_usd`,
   matching this codebase's established "always gate on both R and $ jointly" convention (see
   `_is_positive()` in `pnl_scan.py`, and `train_positive`/`robust`/`survivor` all doing the
   same). Document the choice explicitly in the dev handoff — it is a genuine judgment call, not
   settled law.
2. **Config minimum-n field: reuse `Config.pnl_min_sample_size` (=5) verbatim.** The spec's own
   NOTES say this explicitly — the positive-edge flag is a *display/measurement* gate, not a
   *promotion* gate, so it takes the same semantic as the existing "insufficient sample" floor,
   not `promotion_min_sample_size`. Do NOT add a new config field. Since BOTH existing min-n
   fields are already excluded from `config_fingerprint()`, this iteration introduces **zero
   fingerprint risk** — no new `Config` field at all, unlike iter-7's `promotion_min_sample_size`
   addition. Confirm `test_default_fingerprint_is_pinned_and_unmoved_by_the_new_field`
   (`test_profile_equivalence.py:110`) still asserts `4d665603569b9dbf` — it will, since
   `config.py` is untouched.
3. **Per-split ranking key.** "Rank each split's datasets by hold-out edge" reads most naturally
   as: within each of the two sections (train, hold-out), order that section's own datasets by
   the champion's edge measured on that dataset (descending), tie-break `dataset_id` ascending.
   The positive-edge flag itself is explicitly hold-out-only per the acceptance text — train
   datasets are listed/ranked the same way but never flagged.
4. **Blueprint is already current.** Row 37 and the `python -m app.research.edge_report`
   machine-surface entry were added to `blueprint.md` by the goal-decomposer this iteration —
   backend-data must NOT edit it.
5. **Two distinct no-execution guards, not one.** (a) The NEW dedicated grep-style test asserting
   `edge_report.py`'s own source never calls `set_champion_pointer`/`append_validation_row` and
   carries no broker/order pattern — this is a DoD item, put it in `test_edge_report.py`. (b) The
   existing repo-wide `test_no_execution_path.py` (4 tests) — DoD only requires it "still 4/4"
   (automatic via its glob scan, zero edits needed); the optional path-assertion addition above is
   pure consistency polish, not a requirement.
6. **iter-7 carried-forward polish (B2: wrap `store.set_champion_pointer`'s call site in `_promote`
   in an explicit error type; T1: unused `import time` in `store.py:36`) is NOT triggered this
   iteration** — `store.py` and `pnl_scan.py` are not touched by `edge_report.py`. Confirmed out
   of scope per the spec's own NOTES.
7. **Missing-Alpaca-credentials path is a regression check, not new code.** `edge_report.py` never
   records datasets itself (it only reads already-registered ones), so the existing 503 "real-data
   provider unavailable" behavior (`routes.py`, already tested in `test_real_data_gate.py`) just
   needs to stay green — no new credentials-handling code belongs in `edge_report.py`.

## Key Test Scenarios

1. **Pure-render equality**: every displayed `net_r`/`net_usd`/`n` equals the stored
   `GET /research/backtests/{id}` aggregate byte-for-byte (no second computation path).
2. **Split separation**: train and hold-out are always two separate sections, never pooled or
   averaged together.
3. **Deterministic ranking**: stable `dataset_id` tie-break; re-runs preserve identical ordering.
4. **Fixture pair (non-regression baseline)**: committed train+holdout fixtures (n=1 per split <
   min 5) ⇒ explicit `"no positive-edge dataset"` finding, exit 0, per-dataset numbers still
   shown.
5. **Empty registry**: zero datasets registered at all ⇒ honest empty report, exit 0 (distinct
   from scenario 4 — no fabricated edge either way).
6. **Positive-edge flag proven BOTH ways**: a controlled scenario (test-local
   `dataclasses.replace`-lowered minimum or a constructed qualifying dataset — never by weakening
   the shipped default) ⇒ exactly one hold-out dataset flagged; the unflagged case is scenario 4.
7. **Determinism**: two independent fresh-state runs of an identical scenario produce
   byte-identical `--out` file bytes (per-run-random report ids / wall-clock stripped).
8. **`REGISTER` string** present beside every $ figure; null-baseline seed is the config-owned
   deterministic one.
9. **Default-frozen check**: engine byte-equivalence suite stays green; founding PnL row's
   `config_fingerprint` still reads `4d665603569b9dbf` (expected trivially true — no config field
   added, see Design Notes #2).
10. **Grep-style guard**: `edge_report.py` calls neither `set_champion_pointer` nor
    `append_validation_row`; contains no broker/order/account pattern.
11. **Honest failure states**: corrupt/integrity-failing dataset ⇒ explicit error, nothing
    written; a backtest ending non-`done` ⇒ explicit error, nothing written.
12. **Missing-credentials regression**: a real-feed record attempted without Alpaca credentials
    still surfaces the EXISTING 503 "real-data provider unavailable" (via `test_real_data_gate.py`
    staying green) — no synthesized data, no new code path.
13. **Full backend suite**: stays ≥ the ACTUAL current floor of **1025 passed / 1 skipped** (the
    real iter-7 final count per its dev handoff — the phase spec's own cited "1004" is the older
    iter-6 number; treat 1025/1 as the floor not to regress below), no test deletions,
    observer-equivalence 7/7.
14. **Required-still-passing journeys**: J-02/J-03/J-04/J-06/J-07 via the full backend suite +
    their existing test modules; J-01 via zero-diff `app/mcp/` + a proxied-endpoint spot check;
    J-05 via `test_profiles_api.py`'s real-HTTP-route test + zero-diff `/performance` page; J-08
    via observer-equivalence 7/7 + zero-diff `apps/frontend/`. Browser/replay lane is SKIPPED
    (backend-only, `Frontend Present: no`) — do not let QA claim golden replay that did not run
    (iter-2 + iter-7 lesson).
15. **Anti-goal zero-diff check**: `git diff` shows zero change under `apps/frontend/`,
    `apps/backend/app/mcp/`, and `docs/goal.md`.
16. **Environment**: before the large suite, check `du -sh /tmp/pytest-of-dennis-chan` against the
    per-user tmpfs quota; route pytest `--basetemp`/`TMPDIR` off tmpfs if pinned (iter-3 lesson).

## Out of Scope (per spec — do not implement)

Recording the real ≥3-symbol × ≥2-session-regime Alpaca library (operator action, requires real
credentials — deferred entirely); any new REST endpoint; any new MCP tool (MCP stays zero-diff);
any `/performance` page change or committed markdown render for the edge report; any mutation of
the champion pointer, PnL ledger, datasets, profiles, or engine defaults (edge_report is strictly
read-only beyond the standard row-31 backtest rows the existing runner already persists); any
change to the strategy grammar, fee/slippage/notional model, or thresholds; blueprint.md edits
(already done by the decomposer); the iter-7 carried-forward B2/T1 polish (not triggered — see
Design Notes #6); broker/order/account/execution code of any kind, anywhere.
