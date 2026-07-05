# Iteration 8 — Coherence Audit

**Iteration:** goal-tape_to_profit-iter-8
**Date:** 2026-07-05
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration

Backend-only, machine-surface-only (`Frontend Present: no`). One new module,
`apps/backend/app/research/edge_report.py` (+ `apps/backend/tests/test_edge_report.py`, + one
additive guard line in `apps/backend/tests/test_no_execution_path.py`), delivering J-09's
`python -m app.research.edge_report --out <path>` CLI. Confirmed via
`git diff 54df8c6d4bb78dd8aad79d2ee993ecb803f175c3 --stat` (committed-since-snapshot: `.gitignore`,
`test_no_execution_path.py`, `blueprint.md`, `project-story.md`, telemetry/trace bookkeeping) plus
`git status` (uncommitted new files: `edge_report.py`, `test_edge_report.py`, reports/handoffs) that
`apps/frontend/`, `apps/backend/app/mcp/`, `apps/backend/app/routes.py`, `apps/backend/app/main.py`,
`project-extensions/mcp-servers.yaml`, `apps/backend/app/config.py`, `apps/backend/app/research/store.py`,
and `docs/goal.md` all show **zero diff** since the snapshot. `reports/phase-goal-tape_to_profit-iter-8-ui-surface-map.md`
exists and correctly states "N/A — Backend-only phase."

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Row 37 — Baseline-edge report (new, registered this iteration) | OK | `runs/goal-session-tape_to_profit/state/blueprint.md:80` (registered) ↔ `apps/backend/app/research/edge_report.py:178-219` (`run_edge_report`, sole computer) |
| Row 31 — Backtest aggregates (`net_r`/`net_usd`/`n`) | OK — read verbatim, no second computation | `edge_report.py:114-117` (`_measurement` copies `aggregates` fields verbatim) + `edge_report.py:89-111` (`_run_backtest` calls the one `BacktestJobManager.create`/`run_sync`, same import as `pnl_scan.py:91`) |
| Row 33 — Champion pointer | OK — read verbatim via `store.get_champion_pointer()`, never hardcoded | `edge_report.py:183`; proven by `test_edge_report.py:127-146` (`test_champion_is_read_verbatim_and_never_hardcoded`, moves the pointer and asserts the report + every backtest run reflect the move) |
| `REGISTER` string | OK — imported, not re-declared | `edge_report.py:57` (`from .backtests import BacktestJobManager, REGISTER, STATUS_DONE`); single definition remains `backtests.py:129` |
| `Config.pnl_min_sample_size` (min-n gate) | OK — reused existing field, no new config field | `edge_report.py:56,164` vs. `config.py:933`; zero diff to `config.py` confirmed by `git status`; NOTES in `docs/phases/goal-tape_to_profit-iter-8.md:124` explicitly justifies reuse over minting a third minimum, consistent with the existing dual-field precedent (`config.py:996-1019`) |
| Row 33 mutator (`set_champion_pointer`) / Row 32 mutator (`append_validation_row`) | OK — never called | Confirmed no match in `edge_report.py` (grep) + dedicated test `test_edge_report.py:425-436` + repo-wide guard `test_no_execution_path.py:117` (new additive line) |
| New concept: "positive-edge" flag (champion-alone measurement, hold-out only) | OK — genuinely new, not a duplicate of row 36 | Row 36 (`pnl_scan`) measures *candidate-vs-champion delta* for promotion; row 37 measures the *champion alone*, no comparison, no promotion — distinct concept, correctly registered as its own row rather than left unregistered |

No duplicate computation, no non-canonical source, no unregistered value. Every displayed number
traces to the one `BacktestJobManager` path and is asserted byte-identical to a fresh independent
re-run in `test_edge_report.py:304-333` (`test_every_displayed_value_matches_a_fresh_independent_backtest`).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `python -m app.research.edge_report --out <path>` (J-09 CLI) | OK — machine surface, no nav home required | `blueprint.md:43-45` places it under "**Machine surface** (no nav home — read-only, spawned on demand)" alongside the precedent `pnl_scan` CLI and the MCP server; confirmed zero diff to `apps/frontend/NavBar.tsx`/router (not present in `git status` or the diff) |

The blueprint's IA explicitly carves out a nav-exempt "Machine surface" category for exactly this
kind of read-only CLI artifact (already established for `pnl_scan`, the MCP server, and the
`pnl-history.md` render) — J-09's CLI is placed there, not invented as a new pattern. No page,
panel, or route was added, so there is no parallel-shell or hidden-feature risk in the UI sense.
No duplicate home: J-09 is conceptually distinct from J-07 (see Data Contract row above) and gets
its own new machine-surface line in the IA table (`blueprint.md:60`), not a second home for an
existing entity.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. The iteration is unusually disciplined for coherence purposes: zero frontend diff, zero
  diff to `config.py`/`store.py`/MCP/routes, single reused computation path, single reused
  `REGISTER` constant, single reused min-n config field (with an explicit justification note
  rather than silently minting a third one), and the new Data Contract row was registered in
  `blueprint.md` in the same iteration that introduced it (confirmed via
  `git diff 54df8c6d4bb78dd8aad79d2ee993ecb803f175c3 -- runs/goal-session-tape_to_profit/state/blueprint.md`),
  so there is no unregistered-value gap to flag.
