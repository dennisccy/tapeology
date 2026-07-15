# goal-tradable_wall-iter-9 Dev Handoff

**Phase:** goal-tradable_wall-iter-9
**Date:** 2026-07-15
**Agent:** developer
**Status:** complete

## What Was Built

J-08: a rebuildable, checksum-keyed result cache around `run_strategy_comparison_report`
(`edge_report.py`) so `GET /research/edge-report` (and its byte-identical MCP proxy) can serve the
3-way `v1` / `structure_tape` / `structure_tape_map` comparison within an interactive time budget
on a warm cache instead of the documented ~10+h / ~9.1M-tick sweep. Plus the keyless, agent-buildable
half of the PnL-history append machinery for the first real warm compute's eventual register.

- **`EdgeReportCache`** (new module `apps/backend/app/research/edge_report_cache.py`) — a two-layer
  rebuildable accelerator, never a second source of truth:
  - **Durable layer**: a persisted SQLite table (WAL + busy_timeout, hermetic DI'd path — mirrors
    `bar_index.py`), one row per cache key, surviving a backend restart.
  - **In-process fast path**: an instance-scoped atomic `(key, result)` tuple rebind (mirrors
    `setups.py`'s iter-6-hardened `_SCAN_CACHE`), so a concurrent cold-cache reader either observes
    a complete prior publish or safely (redundantly) recomputes — never a torn key/result pairing.
  - **Cache key** = dataset checksums (train+holdout together) + the strategy registry +
    `config_fingerprint()` + (judgment call, see "Deviation From Plan" below) a conservative
    whole-config-content hash, needed because `config_fingerprint()` deliberately excludes several
    field families (`pnl_min_sample_size`, the `sr_*`/`tradability_*`/`setups_*` families) that this
    report's own call graph (via `compute_setups` → `compute_tradability` → `compute_levels`)
    genuinely depends on.
  - A store-integrity failure (a corrupt dataset file) bypasses the cache entirely — `compute_fn` is
    called directly and raises the same `EdgeReportError` the uncached path always has; nothing is
    ever cached from a failed compute.
- **`edge_report.py`**: the former `run_strategy_comparison_report` body is renamed
  `_compute_strategy_comparison_report` (byte-identical, unrenamed callers unaffected). The public
  `run_strategy_comparison_report` is now a thin dispatcher: an optional `cache=` keyword arg
  (default `None` — the exact pre-J-08 behaviour, always recomputes) routes through
  `EdgeReportCache.get_or_compute` when supplied. No line inside the actual computation changed.
- **`routes.py`**: new `get_edge_report_cache()` FastAPI dependency (mirrors `get_bar_index()` —
  `TAPEOLOGY_EDGE_REPORT_CACHE_DB` env override, else a sibling of the dataset directory,
  `.data/edge_report_cache.db`). `get_edge_report` now depends on it and passes `cache=cache`
  through. Response shape is unchanged.
- **`pnl_ledger.py`**: new `append_strategy_comparison_row` (additive, beside the untouched
  `append_validation_row`) composes ONE ledger row from an already-completed 3-way comparison
  report — every cell copied verbatim (never recomputed), denormalized with its own `basis`
  (train/holdout), plus a row-level `assumptions` block (fees/slippage/dollars-per-R, read from
  config) and `register`. Never pools train/holdout or feeds. `render_history_markdown` gained one
  `if row.get("kind") == "strategy_comparison"` branch (a new discriminator field only new rows
  carry); the existing two-way row branch is untouched, byte-for-byte.
- **`pnl_history.py`**: new `append_strategy_comparison_and_render` (compose + regenerate in one
  step) and CLI additions `--append-report PATH --enhancement-id ID --title TITLE` plus a safety
  `--out PATH` override (mirrors `edge_report.py --out`). Omitting all three flags reproduces the
  pre-J-08 `main()` behaviour exactly. **The real append itself was NOT run** — building/testing the
  machinery only, per the operator-gated out-of-scope carry.

## Files Changed

- `apps/backend/app/research/edge_report_cache.py` (new) — the two-layer cache; see above.
- `apps/backend/app/research/edge_report.py` — `run_strategy_comparison_report` renamed to
  `_compute_strategy_comparison_report`; a new thin `run_strategy_comparison_report(..., cache=None)`
  dispatcher added above it. `run_edge_report`, `main`, and everything above the 3-way-report section
  comment (~line 250) untouched.
- `apps/backend/app/research/routes.py` — new `get_edge_report_cache()` dependency; `get_edge_report`
  gained one `cache: EdgeReportCache = Depends(get_edge_report_cache)` parameter and passes it
  through. No other route touched.
- `apps/backend/app/research/pnl_ledger.py` — new `_KIND_STRATEGY_COMPARISON` constant, `_ledger_cell`
  helper, `append_strategy_comparison_row`; `render_history_markdown` gained one branch (existing
  branch unchanged). `append_validation_row`/`ledger_projection` untouched.
- `apps/backend/app/research/pnl_history.py` — new `append_strategy_comparison_and_render`; `main()`
  gained `--append-report`/`--enhancement-id`/`--title`/`--out` flags, all optional; the no-flag path
  is byte-identical to before.
- `apps/backend/tests/test_edge_report_cache.py` (new, 16 tests) — `EdgeReportCache` unit tests
  against a cheap counting stub: cold miss, warm in-process hit, durability across a simulated
  restart, JSON round-trip byte/key-order preservation, six independent key-busting tests (dataset
  add/remove, strategy-registry-affecting field, config_fingerprint-affecting field, and — the two
  tests proving the 4th key component is load-bearing — `pnl_min_sample_size` and
  `tradability_band_cap_per_side`, both fingerprint-excluded yet output-affecting), a
  content-equal-but-distinct-object cache-hit proof, integrity-bypass, a 16-thread concurrency/
  torn-read test (mirrors `test_setups.py`), and a coherence import-scan guard.
- `apps/backend/tests/test_edge_report.py` (+7 tests) — cache-wiring integration tests using the
  REAL `_compute_strategy_comparison_report`: `cache=None` byte-identity, warm-vs-fresh byte-identity
  on a non-degenerate (3-cell) report shape, second-call-never-recomputes, a new dataset busting the
  wired cache, durability through the real public function, champion-pointer-untouched, and a
  coherence guard. All 28 pre-existing tests in this file are unmodified and still pass.
- `apps/backend/tests/test_edge_report_api.py` (+4 tests) — route-level DI wiring test, a real
  two-HTTP-request warm-cache-never-recomputes test (counts calls to
  `_compute_strategy_comparison_report`), a cold-vs-warm response byte-identity test, and a
  hermetic-cache-DB-location test. All 5 pre-existing tests unmodified.
- `apps/backend/tests/test_pnl_ledger.py` (+9 tests) — `append_strategy_comparison_row` composition
  (verbatim cells + `basis` added), no train/holdout pooling, no feed pooling, malformed-report
  refusal, duplicate-enhancement-id refusal, an honest all-empty append, `ledger_projection`
  passthrough, markdown byte-level-no-op, and the critical non-regression proof (an old two-way row's
  rendered section is byte-identical whether or not a new 3-way row follows it in the same ledger).
  All pre-existing tests unmodified.
- `apps/backend/tests/test_pnl_history.py` (new, 7 tests) — the CLI's new flags, all targeting
  `tmp_path`/`--out` overrides; never the committed file.
- `docs/handoffs/goal-tradable_wall-iter-9-dev.md` — this handoff.
- `docs/handoffs/goal-tradable_wall-iter-9-frontend.md` — frontend verify-only confirmation (no code
  changed).

**Not touched** (confirmed via `git status`): `research/levels.py`, `research/setups.py` (including
`_SCAN_CACHE`), `research/tradability.py`, `research/backtests.py`, `config.py`, any
`apps/frontend/**` file, `reports/pnl/pnl-history.md` (the committed file).

## A real bug found and fixed during implementation

The first cut of `EdgeReportCache._insert` serialized the stored result with `sort_keys=True` (for
consistency with the key-hashing helper). This broke response byte-identity: FastAPI/Starlette
serializes a route's returned dict in its **natural insertion order**, never alphabetically, so a
cold-miss response (declaration order) and a durable-cache-hit response (`json.loads` back from a
sorted-keys stored blob) would byte-DIFFER despite identical content. Caught for real by
`tests/test_mcp_server.py`'s existing `test_edge_report_tool_byte_identical_to_rest` /
`test_edge_report_tool_byte_identical_after_recording_a_real_dataset` (both compare raw wire bytes,
not parsed-JSON equality) — both failed immediately after wiring the cache into the route. Fixed by
serializing the stored result WITHOUT `sort_keys` (key order preserved verbatim through the round
trip); the sorted `_canonical()` helper is now used for hashing/keying only, documented explicitly
in both the module docstring and the method docstring so it is not reintroduced. Added a dedicated
regression test (`test_result_key_order_is_preserved_through_the_durable_round_trip_not_merely_content_equal`)
that would have caught this directly.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_edge_report_cache.py tests/test_edge_report.py tests/test_edge_report_api.py tests/test_pnl_ledger.py tests/test_pnl_history.py tests/test_mcp_server.py tests/test_bar_index.py -v`
Result: all green (16 + 35 + 9 + 31 + 7 + 28 + 10 = 136 tests, 0 failed).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **1392 passed, 7 skipped, 0 failed, 0 errors** in 433.86s. iter-8's baseline was 1348
passed / 7 skipped — the SAME 7 skips (the `integration`-marked live-Alpaca/live-Yahoo tests,
skipped by default), **44 net new passing tests, zero regressions.**

Command: `CONFIG.config_fingerprint()` (direct Python check)
Result: **`4d665603569b9dbf`** — unchanged (frozen-foundation invariant).

Command: `git status --porcelain reports/pnl/pnl-history.md`
Result: empty — the committed PnL history file is untouched by any test in this iteration.

## Live Verification

- **Service startup**: ran `scripts/dev.sh` end to end. Backend (`:8301`) reached "Application
  startup complete"; frontend (`:3301`) reached "Ready in 1246ms". Hit `GET /research/taxonomy` and
  `GET /research/strategies` (200) and the frontend `/` and `/structure` page shells (200, curl —
  server-rendered HTML only, never triggers the client-side `fetchEdgeReport()` call that only runs
  after browser hydration). **Deliberately did NOT hit `GET /research/edge-report` or open
  `/structure` in an actual browser** on this dev server, because it points at the REAL,
  un-overridden `.data/datasets/` directory — the 11 real credentialed datasets iter-8 confirmed are
  present on this machine — and hitting that endpoint here would trigger the real ~10+h sweep the
  dispatch instructions explicitly forbid triggering this turn.
- **Process cleanup**: confirmed and worked around the iter-8-documented gap live — `dev.sh`'s
  `trap "kill $BACKEND_PID $FRONTEND_PID"` only signals the direct child PIDs; the uvicorn
  `--reload` worker and the `next dev` → `next-server` grandchild survive a plain kill of the parent
  PIDs. Cleaned up by pattern (`pkill -9 -f "uvicorn main:app"`, `pkill -9 -f "next dev"`, plus one
  direct-PID kill for a `next-server` process pkill's pattern match missed on the first pass) and
  confirmed both ports free before restarting.
- **Restart**: `scripts/dev.sh` a second time after the above cleanup started cleanly on the SAME
  ports (`:8301`/`:3301`) with no "address already in use" conflict.
- **Cache mechanism, keylessly, against the committed fixtures** (per the dispatch instructions —
  never the real 11-dataset corpus): every `test_edge_report_cache.py`/`test_edge_report.py` cache
  test above runs the real `EdgeReportCache` and, for the wiring tests, the real
  `_compute_strategy_comparison_report` against small synthetic/fixture datasets — determinism,
  key-busting (dataset add/remove, strategy-registry field, config-fingerprint field, AND the two
  fingerprint-excluded-but-output-affecting fields), durability across a simulated restart
  (fresh `EdgeReportCache` object, same path, zero in-process state carried over), and a 16-thread
  concurrent-cold-cache torn-read guard are all exercised for real, not mocked.

## Frontend

Verify-only, per the plan — zero frontend files changed. See
`docs/handoffs/goal-tradable_wall-iter-9-frontend.md` for the full confirmation.

## Known Issues

- **The real ~10+h compute and its real PnL-history append were not run** — this is the explicit
  operator-gated carry (both the phase spec's OUT OF SCOPE section and the dispatch instructions for
  this turn forbid triggering it). The cache machinery, the append machinery, and every test around
  both are keyless and complete; when the operator eventually warms the cache for real (e.g. via a
  direct call to `GET /research/edge-report` against the real store, accepting the multi-hour first
  compute) and wants that result recorded to `reports/pnl/pnl-history.md`, the path is: fetch the
  warm JSON from the endpoint, then
  `python -m app.research.pnl_history --append-report <path-to-the-fetched-JSON> --enhancement-id <id> --title <title>`
  (omit `--out` to target the real committed file).
- **The cache key's 4th component (a conservative whole-config-content hash) is a genuine, tested,
  but undirected-by-the-plan addition** — see "Deviation From Plan" below. I judged this necessary
  for correctness rather than optional; a reviewer who disagrees with the reasoning should treat this
  as the single highest-priority item to re-examine.
- **`scripts/dev.sh`'s SIGTERM trap still does not clean up the full process tree** (the
  `next-server` grandchild survives a plain `kill` of the tracked PIDs) — pre-existing, first
  documented in the iter-8 dev handoff, out of this iteration's file scope (not touched). I worked
  around it during my own verification (see "Live Verification" above) but did not fix it.
- The PnL-history markdown's static intro paragraph (top of `render_history_markdown`'s output) was
  deliberately left untouched (still describes only the two-way row shape in general terms that
  happen to also hold for the new row shape) rather than adding a sentence about 3-way rows, to
  minimize the diff and avoid perturbing the committed file's header on the next real regeneration
  beyond what this iteration's own row-rendering logic requires.

## Deviation From Plan

**One judgment call, flagged explicitly per the codebase's own convention for such calls** (see
`edge_report_cache.py`'s module docstring, "Cache key — why it is FOUR parts, not the three the plan
names," for the full reasoning): the plan and phase spec both describe the cache key as "dataset
checksums + strategy registry + `config_fingerprint`" (three parts). I implemented those three
verbatim, but ADDITIONALLY fold in a fourth: a conservative hash over the config's ENTIRE field
content (no exclusion set), because `config_fingerprint()` is deliberately scoped to the tape/
backtest/PnL pipeline and excludes several field families (`pnl_min_sample_size`; the
`sr_*`/`tradability_*`/`setups_*` families) that this specific report's call graph reads directly
via `compute_setups` → `compute_tradability` → `compute_levels`, and via the `insufficient_sample`
gate. Without the 4th component I could construct a concrete, demonstrable staleness bug: change
`pnl_min_sample_size` (fingerprint-excluded) and the cache would silently keep serving cells labelled
against the OLD minimum. I judged serving a demonstrably-stale report to be a worse outcome than a
slightly wider "any config change busts the cache" net, and wrote two dedicated tests
(`test_pnl_min_sample_size_change_busts_the_cache_despite_fingerprint_exclusion` and
`test_tradability_field_change_busts_the_cache_despite_fingerprint_exclusion`) proving exactly this
gap and its fix. Nothing else deviates from the plan: no frozen file touched, no frontend code
changed, no real compute triggered, no champion promotion, no new nav/page/endpoint beyond the two
named (`get_edge_report_cache` dependency, `append_strategy_comparison_row`/
`append_strategy_comparison_and_render` functions).
