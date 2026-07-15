# goal-tradable_wall-iter-9 Execution Plan

**Alignment check:** J-08 was appended by the goal-proposer strictly inside `docs/goal.md`'s
`<!-- AUTO:journeys -->` marker block (goal.md:369-415) — the sanctioned mechanism; no
human-authored journey or the Anti-goals section was touched. It closes the one real gap the
iter-8 audit (B1/B2) and evaluator independently flagged: `GET /research/edge-report` is a
~10+h/~9.1M-tick uncached sweep, so the era's headline "what actually profits" answer has never
been observed end-to-end. This iteration is purely additive (a cache layer + an append-path),
touches no frozen computation, and does not contradict or drift from docs/goal.md.

## What to Build
- A rebuildable, checksum-keyed result **cache** around `run_strategy_comparison_report`
  (`apps/backend/app/research/edge_report.py:426`) so `GET /research/edge-report` (and its
  byte-identical MCP proxy) serve the 3-way `v1`/`structure_tape`/`structure_tape_map` report
  within an interactive budget on a warm cache instead of the current ~10+h sweep.
- Cache key = `DatasetStore` per-dataset checksums (train+holdout together, append-only/immutable)
  + the strategy registry + `config_fingerprint` (`4d665603569b9dbf`). ANY change to the dataset
  set, registry, or config busts the key and forces a byte-identical recompute. The cache is
  **never** a source of truth — `edge_report.py` stays the sole computer; a miss recomputes
  byte-identically.
- **Durable across backend restart**: a persisted, rebuildable derived artifact (mirror the
  `bar_index.py` SQLite precedent — hermetic DI'd path, WAL + busy_timeout pragmas), layered with
  an in-process atomic `(key, result)` publish for the hot path (mirror `setups.py`'s
  `_SCAN_CACHE`, lines 357-408: single tuple rebind, read-local-reference-before-inspect) so a
  concurrent cold-cache reader never observes a torn/half-written result.
- Explicitly **do NOT** touch `compute_setups`/`_SCAN_CACHE` (`setups.py`) — that scan cost is
  already memoized and is explicitly NOT what this iteration caches; the cost being cached is the
  `BacktestJobManager` sweep inside `_split_cells`/`run_strategy_comparison_report` only.
- Wire the **PnL-history append path** (code + keyless unit tests only) through the existing
  owner `pnl_ledger.py` (writer) / `pnl_history.py` (CLI): given a completed 3-way comparison
  report, append `v1` (null/baseline) vs `structure_tape` vs `structure_tape_map` per split
  (train/holdout never pooled, feeds never pooled), each cell carrying net R, net $, n,
  fee/slippage assumptions, basis, null baseline, and the "simulated — not indicative of live
  results" register; n<5 → `insufficient_sample`. This is NEW, additive code beside the existing
  2-way `append_validation_row` — do not modify that function. The actual real-corpus append to
  the committed `reports/pnl/pnl-history.md` is OUT OF SCOPE this iteration (operator-gated
  carry) — no test should write to the committed file.
- New tests: determinism/byte-identity, key-busting, durability-across-restart,
  concurrency/torn-read, PnL-history append format (full list under Key Test Scenarios).
- Frontend: **verify-only**. `/structure`'s existing Edge Report section already reads
  `GET /research/edge-report` verbatim (era-5 J-05) — confirm it renders the warm-cache
  report/empty-state correctly. Add a frontend change ONLY if browser-QA finds the warm render
  needs a minor observable-state/timeout tweak; do not touch any other `/structure` or cockpit
  surface.
- Dev handoff at `docs/handoffs/goal-tradable_wall-iter-9-dev.md`.

## Agents Required
- backend-data: yes -- the cache module/logic wrapping `run_strategy_comparison_report`, the
  route/DI wiring, the PnL-history append path, and all new tests (determinism/concurrency/
  durability/key-busting/append-format).
- frontend-ux: no -- verify-only per spec, no code change expected. browser-qa-agent must still
  exercise `/structure`'s Edge Report render (see Frontend Present below); a developer frontend
  edit is authorized ONLY if that check finds the warm render needs an observable-state/timeout
  adjustment.

Frontend Present: yes

## Files to Create/Modify
- `apps/backend/app/research/edge_report.py` -- add a cache-aware entry point wrapping
  `run_strategy_comparison_report` (rename the current pure-compute body to a private
  `_compute_...`, mirroring `setups.py`'s `_run_full_panel_scan` rename, so existing callers of
  the public name stay byte-compatible). No change to `run_edge_report`, any helper above the "3-
  way strategy-comparison report" section comment (~line 250), or the computation itself.
- `apps/backend/app/research/edge_report_cache.py` (new module; name at developer's discretion)
  -- the persisted SQLite durable cache: mirror `bar_index.py`'s `BarIndex` class shape (hermetic
  DI'd path, WAL + busy_timeout pragmas, one row keyed on the dataset-checksums+registry+
  fingerprint signature, a JSON-blob result column written in one atomic transaction) plus the
  in-process atomic tuple-rebind fast path (mirror `setups.py:357-408`).
- `apps/backend/app/research/routes.py` -- `get_edge_report` (line 2076) wires through the new
  cache the same DI-overridable way `get_bar_index()` (line 1549, env var
  `TAPEOLOGY_BAR_INDEX_DB`, sibling-of-config-dir default, NOT part of `config_fingerprint`)
  already wires `BarIndex` -- add an analogous `get_edge_report_cache()` dependency. Route
  response shape stays identical.
- `apps/backend/app/research/pnl_ledger.py` -- new ADDITIVE function (beside the untouched
  `append_validation_row`) composing+appending the 3-way comparison rows from a completed
  `run_strategy_comparison_report` output via the same `store.append_pnl_ledger_row` writer;
  `render_history_markdown` gains a rendering branch for the new row shape (existing 2-way rows
  render unchanged).
- `apps/backend/app/research/pnl_history.py` -- gains the append entry point (CLI flag or
  function) the operator invokes after a real warm compute; the existing
  `write_history_markdown`-only `main()` behavior stays available/unchanged.
- `apps/backend/app/mcp/__init__.py` -- likely **no code change**: the `edge_report` tool is a
  pure `httpx` GET proxy against the running backend (`mcp/__init__.py:395` `_proxy_get`), so it
  reflects the cached route automatically. Confirm via the existing MCP byte-identity test rather
  than editing.
- `apps/backend/tests/test_edge_report.py` and/or new `apps/backend/tests/test_edge_report_cache.py`
  -- determinism, key-busting, durability, concurrency tests.
- `apps/backend/tests/test_edge_report_api.py` -- route/DI wiring test for the new cache
  dependency (mirror `test_edge_report_route_wired_through_the_existing_get_bar_store_seam`, line
  114); MCP byte-identity test stays green.
- `apps/backend/tests/test_pnl_ledger.py` -- keyless unit tests for the new append function (full
  register, no pooling, `insufficient_sample` gating, byte-level-no-op re-render).
- `docs/handoffs/goal-tradable_wall-iter-9-dev.md` -- required dev handoff.
- **NOT expected to change**: `reports/pnl/pnl-history.md` (committed file — the real append is
  operator-gated, out of scope this iteration), `research/levels.py`, `research/setups.py`
  (including `_SCAN_CACHE`), `research/tradability.py`, `research/backtests.py`'s strategy math,
  any `config.py` fingerprinted field, `apps/frontend/**` (unless QA finds the conditional gap
  above).

## UI Evolution
- New user-facing capability: none new in kind -- the SAME `/structure` Edge Report section
  becomes usable within seconds instead of a ~10+h wait, once the operator has warmed the cache.
  No new button, form, control, page, or nav entry (nav frozen for Era 5B).
- New information displayed: none new -- identical edge-report cells, now observably renderable.
- New user actions: none.
- UI surface changes: none structural. A conditional, narrowly-scoped observable-state/timeout
  tweak to the existing Edge Report section is authorized ONLY if browser-QA reports the warm
  render needs one.
- Navigation changes: none.

## Visual Requirements
- No new component patterns, layout, or visual effects -- this iteration does not add or restyle
  any UI surface. If a conditional tweak proves necessary, reuse the existing Edge Report
  section's established loading/empty/populated state treatments (dark-only, dense,
  terminal-grade per the Design Direction) rather than introducing new ones.

## Key Test Scenarios
1. **Determinism/byte-identity**: a warm-cache `run_strategy_comparison_report`/
   `GET /research/edge-report` result is byte-identical to a fresh cache-cleared compute over the
   SAME store, verified on a NON-degenerate report shape (real datasets, or the
   `test_synthetic_scan_join_produces_real_cells_all_insufficient_sample` panel-override pattern
   already in `test_edge_report.py:579`) -- not merely an empty `cells: []` (iter-4 lesson).
2. **Key-busting**: changing a dataset's checksum (add/remove/replace a registered dataset), the
   strategy registry, or `config_fingerprint` each independently forces a recompute rather than
   serving a stale cached result.
3. **Durability**: constructing a fresh cache instance against the SAME persisted path
   (simulating a backend restart, no in-process state carried over) serves the prior warm result
   without recomputation.
4. **Concurrency/torn-read**: a cold-cache concurrent read (mirror `test_setups.py:1020`'s
   threading pattern) never observes a torn/half-written result -- every concurrent reader either
   sees a complete prior publish or triggers its own full (redundant but harmless) recompute.
5. **Cache is never a source of truth**: `edge_report.py` remains the sole computer; a miss
   recomputes byte-identically; no second computation path exists anywhere (coherence-auditor's
   named focus this iteration).
6. **Route/DI wiring**: `GET /research/edge-report` wires through the new cache dependency the
   same overridable way `get_bar_index()` does (test mirrors
   `test_edge_report_route_wired_through_the_existing_get_bar_store_seam`).
7. **MCP byte-identity**: the `edge_report` MCP proxy response equals the REST route's response
   verbatim (existing test stays green; expect no code change needed since the proxy is a pure
   HTTP passthrough).
8. **Frozen-foundation equivalence**: `config_fingerprint() == "4d665603569b9dbf"`; `levels.py`,
   `setups.py` (incl. `_SCAN_CACHE`, untouched), `tradability.py`, `v1`, `structure_tape`,
   `structure_tape_map`, `default` profile all byte-identical; champion pointer untouched after a
   cached report run.
9. **PnL-history append**: keyless unit test (`tmp_path`, never the committed file) that, given a
   completed comparison report, the new append composes a row with train/holdout separate, feeds
   never pooled, n<5 → `insufficient_sample`, null baseline present, and the "simulated — not
   indicative of live results" register; regenerating markdown from unchanged rows is a
   byte-level no-op. Confirm `reports/pnl/pnl-history.md` (committed) is untouched by this
   iteration's tests.
10. **Full backend suite green**, zero regressions, zero deleted/weakened tests (iter-8 baseline:
    1348 passed / 7 skipped); `test_no_credential_in_artifacts.py` stays green.
11. **Browser (J-08, browser-qa-agent)**: `/structure` Edge Report section renders the warm-cache
    report (or honest all-`insufficient_sample`/empty state) verbatim within an interactive
    budget -- open the screenshot; fall back to `innerText`/DOM-text extraction for deep-scroll
    sections (iter-6 lesson). Re-verify J-05 page shell (Tradable Map default + off-by-default
    raw toggle + Case Studies) and J-06 cockpit chip/overlay unregressed. Use the REAL tape-state
    vocabulary `{buyer_control, seller_control, bid_absorption, ask_absorption, unclear}` and the
    pinned EVENT id `13e24a2f185b1299` (16 hex) -- NOT the 32-hex dataset id, which 404s against
    `/research/setups/{id}` -- per the iter-8 audit's T3 correction to the QA test-plan.
12. **Out-of-scope guardrails** (do not implement): the real ~10+h compute + its real
    pnl-history append (operator-gated); any change to `edge_report.py`'s computation itself,
    `levels.py`, `setups.py`, `tradability.py`, `v1`, `structure_tape`, `structure_tape_map`,
    `default`, or `config_fingerprint`; any champion promotion; any new dataset recording; any
    era-6 statistical machinery, `/datasets` UI, or nav entry.
