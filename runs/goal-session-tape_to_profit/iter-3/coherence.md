**Verdict:** COHERENCE-PASS

## Iteration 3 — Strategy grammar v1 + deterministic backtest engine (J-03)

**Session:** tape_to_profit
**Iteration index:** 3
**Snapshot SHA:** c1cf3bf7214cd81aafdd60bc618d5ca88a18c437

**Diff note:** `git diff c1cf3bf7214cd81aafdd60bc618d5ca88a18c437` covers the modified *tracked*
files (`apps/backend/app/config.py`, `apps/backend/app/main.py`, `apps/backend/app/mcp/__init__.py`,
`apps/backend/app/research/routes.py`, `apps/backend/app/research/store.py`,
`apps/backend/tests/test_journal_migration.py`, `apps/backend/tests/test_mcp_server.py`, plus the
append-only `runs/goal-session-tape_to_profit/telemetry.jsonl`); `git status`/`git diff HEAD` confirm
these are identical to the working tree (nothing additionally uncommitted beyond one extra
telemetry line). The iteration's new module and its tests are **untracked**, so they were audited
by direct read: `apps/backend/app/research/backtests.py` (new runner + job manager),
`apps/backend/tests/test_backtests.py`, `apps/backend/tests/test_backtests_api.py`,
`apps/backend/tests/test_no_execution_path.py`, `apps/backend/tests/fixtures/journal_v7_schema.sql`.
`Frontend Present: no` (lean, backend-only) — confirmed by `git diff c1cf3bf7...--stat --
apps/frontend` and `git status --porcelain -- apps/frontend` both returning empty, so no UI surface
map exists for this iteration (expected, per the no-map fallback) and IA surfaces were derived from
the diff/spec directly.

---

## Step 1 — Data Contract Check

No violations found.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Row 31 — Backtest reports | OK | Computed once in `BacktestRunner.run` (`apps/backend/app/research/backtests.py:194-253`), persisted via `JournalStore.insert_backtest`/`set_backtest_result` (`store.py:1113-1160`); served verbatim by `POST /research/backtests` (`routes.py:1507`), `GET /research/backtests` (`routes.py:1549`), `GET /research/backtests/{id}` (`routes.py:1558`), `POST /research/backtests/{id}/cancel` (`routes.py:1569`) — GET handlers do `record.payload` / `r.payload` only, no recomputation |
| Row 34 — Strategy definition v1 | OK | Single owner `Config.strategy_definition(STRATEGY_V1_ID)` (`config.py`, new); read once by the runner (`backtests.py:223`) and echoed verbatim into report provenance (`backtests.py:235 "strategy": strategy`) — no restated copy anywhere |
| Row 27 — R basis (prior era, reused) | OK | `backtests.py:80 from .marks import r_basis`, used at `backtests.py:396`; `grep -rn "def r_basis"` across `apps/backend/` returns exactly one definition (`app/research/marks.py:27`), shared with `studies.py:81`. No second R formula introduced |
| Row 30 — Dataset records (prior iter, reused) | OK | Runner reads datasets ONLY via `DatasetStore.get()` (`backtests.py:216`) and `DatasetStore.replay()` (`backtests.py:271`) — the public API. Enforced by a dedicated source-scan test, `test_runner_consumes_the_shared_r_helper_and_the_public_dataset_api` (`test_backtests.py:598-606`), which asserts `backtests.py` contains no `json.load`/`read_text`/`open(`/`_load(` |
| MCP `backtests` tool (row 31's machine surface) | OK | Declarative proxy map `_STATIC_PATHS["backtests"] = "/research/backtests"` (`app/mcp/__init__.py:87`, pre-existing, unchanged by this diff) dispatched generically by one `call_tool` handler (`__init__.py:300-310`) — no per-tool special-casing. This iteration's `__init__.py` diff is exactly the two tool description strings (`datasets`, `backtests`); confirmed no other hunks in `git diff c1cf3bf7... -- apps/backend/app/mcp`. New test `test_backtests_tool_byte_identical_on_a_non_empty_live_list` (`test_mcp_server.py`) asserts the tool's JSON equals `GET /research/backtests`'s bytes on a non-empty list |
| New sub-fields (per-trade `fees_usd`/`slippage_usd`, aggregates, seeded null baseline) | OK — not a new contract row | These are decomposition detail of the already-registered row 31 entity, explicitly called for by this iteration's own spec ("Report content:… gross/net R, gross/net $, fees, slippage" and "beside a seeded random-entry null baseline"), not an independently computed value with any risk of diverging across surfaces |

## Step 2 — Information Architecture Check

No violations found.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `POST/GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel` | OK | Added on the **existing** research router (`routes.py:81 router = APIRouter(prefix="/research", ...)`), not a new router. Blueprint IA table registers this journey verbatim as "J-03 strategy grammar + backtest engine \| API `/research/backtests*` + MCP `backtests` \| machine" — an explicit no-nav-home machine surface, so nav reachability does not apply |
| Nav / frontend | OK (untouched) | `apps/frontend/components/NavBar.tsx` has zero diff (absent from both `git diff --stat` and `git status`) — no dead link, no premature **Performance** entry (correctly still gated on J-05 per the blueprint's "ships together with the page" rule) |

- **No duplicate home, no parallel shell.** No second "backtests" surface was introduced; the only
  consumers are the four REST routes and the unchanged MCP proxy, both already the registered
  machine-surface homes.
- **No new UI surface at all.** Confirmed by the empty `apps/frontend` diff/status above, consistent
  with the iteration spec's own "UI surface changes: None" and "Blueprint conformance: No new UI
  surfaces… no blueprint edit, no reapproval request" sections.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None material. The implementation is unusually explicit about reuse at every choice point: entry
  arming reuses `_premise_state`/`_control_state`/`_synthetic_invalidation`/`_PathPoint`/status
  constants imported directly from `studies.py` (`backtests.py:87-99`) rather than copied; the
  migration (`store.py` v7→v8) is proven against a new committed old-schema fixture
  (`tests/fixtures/journal_v7_schema.sql`) following the exact precedent of the v6→v7 step. The dev
  handoff's own claims (single computing owner, public-API-only dataset access, MCP diff scoped to
  two strings) match what independent inspection of the diff and source shows.

## Summary

This iteration implements exactly Data Contract rows 31 (Backtest reports) and 34 (Strategy
definition v1), both pre-registered at baseline, with one computing owner each and zero second
computation/serving paths. R basis and dataset access are reused from their existing single owners
(`marks.r_basis`, `DatasetStore`'s public API) — enforced by a dedicated source-scan test, not just
asserted in prose. Exactly four routes land on the existing `/research` router at the blueprint's
pre-declared machine-surface home; the MCP `backtests` tool required (and received) zero handler
code changes, confirmed by an empty diff over the proxy/dispatch logic and a new byte-identity test.
No frontend file changed, no nav edit was made, and no dead **Performance** link was added ahead of
J-05. No Data Contract violation, no Information Architecture violation.
