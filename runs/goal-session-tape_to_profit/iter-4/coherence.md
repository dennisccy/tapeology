**Verdict:** COHERENCE-PASS

## Iteration 4 — Append-only PnL ledger with the founding baseline row (J-04)

**Session:** tape_to_profit
**Iteration index:** 4
**Snapshot SHA:** 5f7bb2661accd91a401da322498103cce8ea4e2e

**Diff note:** `git diff 5f7bb2661accd91a401da322498103cce8ea4e2e --stat` shows 7 modified *tracked*
files (`apps/backend/app/config.py`, `apps/backend/app/mcp/__init__.py`,
`apps/backend/app/research/routes.py`, `apps/backend/app/research/store.py`,
`apps/backend/tests/test_journal_migration.py`, `apps/backend/tests/test_mcp_server.py`, plus the
append-only `runs/goal-session-tape_to_profit/telemetry.jsonl`); `git status`/`git diff HEAD` confirm
these match the working tree exactly (no drift). The iteration's new modules and tests are
**untracked**, so they were audited by direct read: `apps/backend/app/research/pnl_ledger.py` (the
row-32 writer + serving projection + markdown render), `apps/backend/app/research/pnl_baseline.py`
(founding-baseline seeding CLI), `apps/backend/app/research/pnl_history.py` (markdown regen CLI),
`apps/backend/tests/test_pnl_ledger.py`, `apps/backend/tests/test_pnl_ledger_api.py`,
`apps/backend/tests/fixtures/journal_v8_schema.sql`, and the committed render output
`reports/pnl/pnl-history.md`. `Frontend Present: no` (lean, backend-only) — confirmed by
`git diff 5f7bb266...--stat -- apps/frontend` and `git status --short -- apps/frontend` both
returning empty, so no UI surface map exists for this iteration (expected, per the no-map fallback)
and IA surfaces were derived from the diff/spec directly.

---

## Step 1 — Data Contract Check

No violations found.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Row 32 — PnL-ledger rows | OK | Single writer `append_validation_row` (`apps/backend/app/research/pnl_ledger.py:133`) composes the row by copying `net_r`/`net_usd`/`n` **verbatim** from the persisted row-31 backtest payload's `result.aggregates` via `_split_measurement` (`pnl_ledger.py:110-118`) — grepped for `net_r`/`net_usd` across the new modules + routes + MCP and every hit is a read of the stored aggregates or a display-string interpolation, never a second formula. Persisted via the append-only `JournalStore.append_pnl_ledger_row` (`store.py:1256`) |
| Row 32 — single serving read | OK | `ledger_projection` (`pnl_ledger.py:196`) is the ONE read; `GET /research/pnl/ledger` calls it directly (`routes.py:1599 return ledger_projection(...)`), `render_history_markdown` calls the SAME function (`pnl_ledger.py:227,232`), and the MCP `pnl_ledger` tool is the pre-existing generic proxy dispatch (`app/mcp/__init__.py:83-89,251-252`, unchanged by this diff) that fetches the REST route — so REST, markdown, and MCP structurally cannot diverge. Cross-surface equality is asserted directly in tests: `test_pnl_ledger_tool_byte_identical_on_a_non_empty_200` (`test_mcp_server.py`) and the REST-vs-markdown check in the QA evidence (`reports/phase-goal-tape_to_profit-iter-4-ui-test-results.md:22`) |
| Row 32 — register string | OK | Imported from the single existing constant — `from .backtests import REGISTER, STATUS_DONE` (`pnl_ledger.py:52`); `backtests.py:121` remains the one definition. No second copy of the register string introduced |
| Row 32 — append-only repository | OK | `JournalStore` gains `append_pnl_ledger_row` / `get_pnl_ledger_row` / `list_pnl_ledger` (`store.py:1256,1281,1298`) and no update/delete method for the table; a duplicate enhancement id raises `DuplicateEnhancementError` (`store.py:336`) from a SQL `IntegrityError`, never an overwrite — mirrored by a source-scan test per the dev handoff ("no UPDATE/DELETE SQL targets the table anywhere") |
| Row 31 — Backtest reports (prior iter, reused) | OK | The founding-baseline CLI and the ledger writer read backtest reports only through `store.get_backtest()` (`pnl_ledger.py:78`) and run new backtests only through the existing `BacktestJobManager.create`/`run_sync` public API (`pnl_baseline.py:69-75`) — confirmed zero diff to `apps/backend/app/research/backtests.py` (`git diff --stat` empty) |
| Row 30 — Dataset records (prior iter, reused) | OK | The seeding CLI obtains datasets only via the public `record_from_source` path (`pnl_baseline.py:38-56`), reusing an already-registered dataset on `DatasetAlreadyRegistered` rather than re-recording — confirmed zero diff to `apps/backend/app/research/datasets.py` |
| MCP `pnl_ledger` tool | OK | `git diff 5f7bb266... -- apps/backend/app/mcp/__init__.py` is exactly two hunks: the module-docstring sentence and the tool's `description` string (`__init__.py:14-22`, `179-186`) — no proxy/dispatch/handler logic touched. The pre-existing `_STATIC_PATHS["pnl_ledger"]` mapping (`__init__.py:89`) and the generic dispatcher (`__init__.py:251-252`) are unchanged lines, not part of this diff |
| Config additions (`pnl_min_sample_size`, `pnl_founding_enhancement_id`/`_title`, the two founding windows, `pnl_history_md_path`) | OK — not new contract rows | All are config-owned knobs for row 32 (label threshold, founding-row identity, render path), not independently computed values; fingerprint-exclusion vs. inclusion is argued per-field in `config.py:1120-1139` and pinned both ways per the dev handoff. This is decomposition detail of the already-registered row 32 entity |

## Step 2 — Information Architecture Check

No violations found.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `GET /research/pnl/ledger` | OK | Added on the **existing** research router (`routes.py:1598-1599`, same `router` used by rows 30/31), not a new router or shell. Blueprint IA table registers this journey verbatim: "J-04 PnL ledger (append-only) \| API `/research/pnl/ledger` + `reports/pnl/pnl-history.md` + MCP `pnl_ledger` \| machine" — an explicit no-nav-home machine surface, so click-count reachability does not apply |
| `reports/pnl/pnl-history.md` | OK | Already named in the blueprint's machine-surface list ("`reports/pnl/pnl-history.md` — pure render of the stored PnL-ledger rows") and in the IA table's J-04 row; the committed file exists at exactly that path with the founding row rendered |
| Nav / frontend | OK (untouched) | `apps/frontend/components/NavBar.tsx` and all of `apps/frontend/` have zero diff and zero uncommitted changes (`git diff --stat -- apps/frontend` and `git status --short -- apps/frontend` both empty) — no dead **Performance** link added ahead of J-05, consistent with the blueprint's "ships together with the page" no-dead-link rule. `GET /meta/ui-routes` / `app/meta.py` also show zero diff, matching the spec's explicit scope boundary |

- **No duplicate home, no parallel shell.** No second "PnL ledger" surface was introduced; the three
  consumers (REST route, markdown render, MCP proxy) are all pre-declared machine-surface homes for
  row 32, sharing one read.
- **No new UI surface at all.** Confirmed by the empty `apps/frontend` diff/status above, consistent
  with the iteration spec's own "UI surface changes: None" and "Blueprint conformance: No new UI
  surfaces… No blueprint edit, no reapproval request" sections.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None material. The implementation is unusually explicit about single-ownership at every choice
  point: the writer only ever reads `result.aggregates` off a `STATUS_DONE` report (refusing
  non-terminal/corrupt/wrong-split reports via `LedgerCompositionError` rather than tolerating a
  divergent read), the markdown render and the REST route are proven to call the identical
  `ledger_projection` function rather than merely "the same shape," and the founding row's baseline
  side is stored as an explicit `null` rather than a zero that could be mistaken for a second
  measured value. The dev handoff's claims (one writer, one serving read, doc-strings-only MCP diff,
  zero engine/backtests/datasets/meta.py diff) match what independent inspection of the diff and
  source shows, and the reviewer's independent pass corroborates the same zero-diff and append-only
  findings.

## Summary

This iteration implements exactly Data Contract row 32 (PnL-ledger rows), pre-registered at
baseline, with one computing/composing owner (`append_validation_row`) and one serving read
(`ledger_projection`) consumed identically by REST, the committed markdown, and the MCP proxy — no
second computation or query path exists, and cross-surface byte-identity is asserted in tests, not
just claimed. The register string is the one existing `REGISTER` constant; backtests and datasets
are touched only through their existing public APIs, with zero diff to the compute modules
themselves. The one new route lands on the blueprint's pre-declared machine-surface home for J-04
with no nav-reachability requirement; the MCP tool's diff is documentation strings only, confirmed by
inspecting the exact hunks. No frontend file changed, no nav edit was made, and no dead
**Performance** link was added ahead of J-05. No Data Contract violation, no Information Architecture
violation.
