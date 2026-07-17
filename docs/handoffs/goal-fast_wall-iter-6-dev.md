# goal-fast_wall-iter-6 Dev Handoff

**Phase:** goal-fast_wall-iter-6
**Date:** 2026-07-17
**Agent:** developer
**Status:** complete

## What Was Built

J-06 — "Restarts stop hurting: the durable setups scan cache" — the seventh and closing Must-have
journey of "The Fast Wall" interlude. `compute_setups`'s multi-minute full-panel touch-event scan
now survives a backend restart, and no longer relies on the fragile `id(config)` object-identity key.

- **New `apps/backend/app/research/setups_scan_cache.py`**: `SetupsScanCache` — a durable-only
  SQLite cache (mirrors `edge_report_backtest_cache.py`'s "no in-process hot slot of its own" shape,
  since `setups.py` already owns its own hot slot). `lookup(key: str) -> dict | None` /
  `publish(key: str, result: dict) -> None`; a fresh short-lived connection per call (WAL +
  `busy_timeout`); `sqlite3.Error` swallowed on both methods (a miss/no-op, never a crash). Result
  JSON stored WITHOUT `sort_keys` (the `EdgeReportCache._insert` byte-identity discipline).
  `scan_cache_key(*, config_content_hash, store_signature) -> str` — sha256 of canonical JSON, a
  pure function of two explicit named inputs (the `pair_cache_key` precedent). `resolve_scan_cache_db_path(bar_dir_resolved)`
  — env `TAPEOLOGY_SETUPS_CACHE_DB` if set, else `Path(bar_dir_resolved).parent / "setups_scan_cache.db"`
  (e.g. `.data/bars` -> `.data/setups_scan_cache.db`). No `reindex()`/bulk-rebuild method.
- **`apps/backend/app/research/setups.py`**: `compute_setups`'s key changed from
  `(id(config), _store_signature(store))` to `(_config_content_hash(config), _store_signature(store))`
  — `_config_content_hash` imported verbatim from `edge_report_cache.py` (never re-derived), the
  conservative whole-config content hash rather than `config.config_fingerprint()` alone (whose
  exclusion set drops exactly the `setups_*`/`tradability_*`/`sr_*` families this scan reads).
  `compute_setups` is now a three-tier lookup: in-process hot slot (unchanged atomic
  `(key, result)` single-rebind discipline) -> the new durable `SetupsScanCache` (self-resolved from
  the `store: BarStore` parameter already in scope — no FastAPI DI, no signature change, no call-site
  change) -> `_run_full_panel_scan`. A durable hit republishes to the hot slot; a full miss publishes
  to both layers (durable write before the hot-slot rebind) — both paths funnel through the SAME
  single `_SCAN_CACHE = (key, result)` rebind (the guard test's own requirement). Added
  `_reset_scan_cache_for_tests()` (mirrors `bars.py`/`datasets.py`'s identical precedent) — test-only,
  never called from production code. Refreshed the module docstring's B3 paragraph and the
  `_SCAN_CACHE` block comment to describe the new two-tier reality (content-hash keying, the durable
  sibling, why the OLD "PROCESS-LOCAL... never SQLite/disk-persisted" wording now needs the
  clarification that it describes the hot slot specifically). `_store_signature` is unchanged, reused
  as-is. `compute_setups`'s own signature and its 4 existing call sites are byte-unchanged.
- **`apps/backend/tests/conftest.py`**: the existing autouse `_reset_store_verified_caches` fixture
  now also calls `setups_module._reset_scan_cache_for_tests()` before every test (see "Judgment call"
  below for why this was necessary, not optional).
- **New `apps/backend/tests/test_setups_scan_cache.py`** (19 tests): `scan_cache_key`'s pure-function
  stability/key-busting-matrix, a call-counting-spy key-busting proof, lookup/publish mechanics,
  byte-identity/`sort_keys` discipline, durability across a simulated restart, deleting-the-DB-is-harmless,
  corrupted-DB tolerance (construction/lookup/publish never raise), thread concurrency, and
  `resolve_scan_cache_db_path`'s env-else-sibling policy (including a never-collides-with-siblings
  check against `resolve_cache_db_path`/`resolve_backtest_cache_db_path`).
- **`apps/backend/tests/test_setups.py`** (+7 tests, TC-1/2/3/4/5/6/8 — TC-7 needs no new test, see
  below): restart simulation (hot slot cleared, durable cache serves with zero rescans,
  byte-identical), identity-fragility-gone (a content-equal but distinct `Config` object is a cache
  hit), a `setups_*`-family field change busts the cache despite `config_fingerprint()` exclusion, a
  newly-recorded `"5m"` series busts the cache, deleting the durable DB file is harmless (one
  recompute, byte-identical), the non-vacuous mutation probe (a durable row pre-seeded with a
  DELIBERATELY WRONG payload is returned verbatim, proving the durable-hit path is genuinely read),
  and a corrupted durable DB never blocks `compute_setups` from serving the fresh scan.
- **`apps/backend/tests/test_setups_api.py`** (+1 test): TC-8's HTTP leg — a corrupted durable
  scan-cache DB file never blocks `GET /research/setups`, which still 200s with the freshly-scanned
  events list.

## Files Changed

- `apps/backend/app/research/setups_scan_cache.py` (NEW) — `SetupsScanCache`, `scan_cache_key`,
  `resolve_scan_cache_db_path`.
- `apps/backend/app/research/setups.py` — `compute_setups`'s three-tier rewrite; new
  `_reset_scan_cache_for_tests`; module docstring + `_SCAN_CACHE` block comment refreshed; two new
  imports (`edge_report_cache._config_content_hash`, `setups_scan_cache.{SetupsScanCache,
  resolve_scan_cache_db_path, scan_cache_key}`).
- `apps/backend/tests/conftest.py` — the existing autouse fixture also resets `setups.py`'s hot slot.
- `apps/backend/tests/test_setups_scan_cache.py` (NEW) — 19 tests, see above.
- `apps/backend/tests/test_setups.py` — +7 tests (TC-1/2/3/4/5/6/8) plus `import dataclasses`.
- `apps/backend/tests/test_setups_api.py` — +1 test (TC-8's HTTP leg).

**Zero diff** (git-confirmed via `git status --porcelain` / `git diff --stat`): `levels.py`,
`tradability.py`, `backtests.py`, `bars.py`, `datasets.py`, `dataset_index.py`, `edge_report.py`,
`edge_report_compute.py`, `edge_report_cache.py` (method bodies — only `_config_content_hash` is
imported elsewhere), `edge_report_backtest_cache.py`, `app/mcp/__init__.py`, `config.py`, `routes.py`,
and the entire `apps/frontend/` tree — exactly the plan's expected scope, nothing wider.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q` (`.claude/project-template.md` is
still the generic, unfilled vendored template — the same finding every prior iteration's dev handoff
has recorded; commands used here come from `pyproject.toml`, `README.md`'s "How to run" section, and
prior iterations' own handoffs).

Targeted runs (all green before the full run):
- `pytest tests/test_setups.py tests/test_setups_scan_cache.py -q` -> 60 passed (41 in
  `test_setups.py` = 34 pre-existing + 7 new; 19 in `test_setups_scan_cache.py`, all new).
- `pytest tests/test_setups_api.py tests/test_edge_report.py tests/test_edge_report_api.py tests/test_edge_report_cache.py tests/test_edge_report_compute.py tests/test_edge_report_backtest_cache.py tests/test_mcp_server.py tests/test_backtests.py tests/test_dataset_index.py -q`
  -> all green, 0 failures (downstream-sensitive files given `compute_setups` is called internally by
  `edge_report.py`'s `run_strategy_comparison_report`).

Full suite: **1544 passed, 7 skipped, 0 failed, 0 errors (1551 collected)** — up from the iter-5
baseline of 1517 passed / 7 skipped / 1524 collected by exactly **27 net-new tests** (19 + 7 + 1 = 27,
matching the collected-count delta exactly). Verified via raw dot-output character tallying (`.`/`s`/
`F`/`E`/`x`/`X`): 1544 dots, 7 `s`, zero `F`/`E`/`x`/`X` anywhere — this project's test harness does
not print the usual final pytest summary line (a pre-existing environment quirk every prior
iteration's handoff has also noted), so this counting method is the established verification
technique. Exit code 0.

`config.CONFIG.config_fingerprint()` confirmed still `4d665603569b9dbf` by direct computation (no
`Config` field added; the new module uses only stdlib `hashlib`/`json`/`os`/`sqlite3`).

Named guard tests re-run individually and confirmed passing, byte-unmodified source:
`test_setups.py::test_compute_setups_itself_never_touches_the_dataset_store`,
`test_setups.py::test_scan_cache_publish_is_a_single_atomic_rebind_never_two_separate_writes`,
`test_mcp_server.py::test_advertised_tool_set_is_exactly_capability_6` (confirmed still exactly 18
tools — no MCP tool was added).

TC-7's "frozen foundations" clause needs no NEW test: it is satisfied by the three guard tests above
(unmodified, still passing) plus the many existing `config_fingerprint()`-pinning tests scattered
across the suite (e.g. `test_setups_config_fields_are_excluded_from_config_fingerprint`).

## Live verification (beyond the automated suite)

Ran a SCOPED backend+frontend pair (ports 8391/3391) using the EXACT iter-4-established recipe
(`reports/phase-goal-fast_wall-iter-4-ui-test-plan.md`'s one-time setup: `TAPEOLOGY_DATASET_DIR` a
private copy of `tests/fixtures/datasets_j03`, `TAPEOLOGY_BAR_DIR` a fresh empty dir,
`TAPEOLOGY_JOURNAL_DB`, `TAPEOLOGY_EDGE_REPORT_CACHE_DB`), with this iteration's one new env var
(`TAPEOLOGY_SETUPS_CACHE_DB`) appended into the same scoped temp dir — never the default `.data/`
corpus or the project's own pinned default-port instance.

- **Service startup**: both `uvicorn` (backend) and `npx next dev` (frontend) started cleanly with
  zero errors against the new `setups.py`/`setups_scan_cache.py` code — confirms no import error, no
  startup crash. Both ports confirmed free after a clean teardown (`kill -9` + `fuser -k`), no stray
  process left running.
- **curl checks**: `GET /research/setups` returned `{"events":[]}` (honest empty — the scoped bar dir
  is intentionally empty) in 7ms on a warm call.
- **Chrome MCP browser pass succeeded this session**: navigated to `http://localhost:3391/structure`
  fresh, waited 10s, then mechanically queried the DOM via `eval` for every `[data-testid]` ending in
  `-loading` — **zero found** (`loadingTestids: []`). Confirmed by direct HTML inspection: Tradable
  Map renders its idle "Choose a symbol and an as-of time..." state (`tradable-map-idle` — correct,
  since no symbol was entered, not a loading state), Case Studies renders
  `case-studies-empty`/"No band-touch events scanned yet." (the scoped bar dir has zero registered
  series — the expected, honest outcome per the phase spec's own Visual Requirements), Edge Report
  renders the byte-identical frozen `edge-report-not-computed` panel ("Edge report not computed yet."
  + the exact J-01 detail text + "Compute edge report" button), Registry renders the full champion +
  three strategy cards (v1/structure_tape/structure_tape_map) with all their tables, Comparison
  renders its idle state with the one PG dataset option. Zero console errors (only the expected React
  DevTools info line). Full-page screenshot captured and visually confirmed no regression against the
  iter-5 baseline description. This satisfies TC-9 in full.
- **Real end-to-end durable-cache confirmation** (beyond what any pytest fixture proves): after the
  browser pass, `$SCOPED_DIR/setups_scan_cache.db` existed on disk (a real SQLite file, not a fixture)
  containing exactly one row — `result: {"events": []}`, a real ISO `created_utc` timestamp — proving
  the new three-tier lookup genuinely fired inside a REAL running backend process reached through a
  REAL page load, not merely inside isolated test fixtures. A second `GET /research/setups` against
  the same still-running process returned in 7ms (hot-slot or durable hit, either way not a rescan).

## Known Issues

- **Judgment call: `conftest.py`'s autouse fixture now also resets `setups.py`'s hot slot** — not
  explicitly listed in the plan's "Files to Create/Modify", but necessary for correctness, not
  optional polish. Switching `compute_setups`'s hot-slot key from `id(config)` to a CONTENT hash
  means two DIFFERENT tests using genuinely equal config content against a genuinely equal store
  signature (e.g. two separate tests both using an empty `BarStore` with `_syn_config()`'s default
  fields) could otherwise observe each other's leftover hot-slot entry across test-function
  boundaries within the same pytest process — a real, structural cross-test-contamination risk the
  OLD `id(config)`-based key did not have (a fresh Python object almost always gets a fresh `id()`
  within one process's lifetime). This mirrors exactly why `bars.py`/`datasets.py`'s own equivalent
  caches already needed (and got, at era-fast_wall J-02) this same autouse-reset treatment. The
  durable `SetupsScanCache` tier needs no such reset — its DB path is derived from each test's own
  `tmp_path`-scoped bar store root, so it is already naturally test-isolated by construction.
- **Judgment call: one HTTP-level test added to `test_setups_api.py`** (not explicitly in the plan's
  file list either) — TC-8's own acceptance wording explicitly names "a direct call to
  `GET /research/setups`" returning HTTP 200 despite a corrupted durable cache DB, not merely a
  direct `compute_setups` call. `test_setups.py`'s own TC-8 test already proves this at the module
  level; `routes.py`'s `list_setups`/`get_setup` wire through to `compute_setups` with zero additional
  error handling (confirmed by reading the route source), so the module-level proof structurally
  implies the route's 200 — but I added the one small HTTP-level test anyway for a genuine end-to-end
  confirmation rather than relying purely on that structural argument, given this project's repeated
  emphasis on non-vacuous, directly-observed proof over inference. Both judgment calls are
  purely-additive, low-risk, and scoped to test infrastructure only — no product file outside the
  plan's named list changed.
- **A minor, pre-existing doc staleness NOT touched**: `tests/test_edge_report_cache.py`'s own
  docstring (around its `test_unchanged_inputs_reuse_the_cache_across_a_fresh_config_object_with_equal_values`
  test) contains an aside describing `setups.py`'s `_SCAN_CACHE` as "in-process-only... `id(config)`-
  based" — accurate before this iteration, now slightly stale in that one parenthetical aside (the
  slot itself is still in-process/in-memory-only, but is no longer `id(config)`-keyed, and now has a
  durable sibling). Left untouched deliberately: it is prose commentary inside a DIFFERENT journey's
  (J-01's) frozen test file, outside this iteration's explicit scope (`edge_report_cache.py`'s own
  method bodies and tests are J-01-owned, listed as zero-diff-expected), the assertion it supports
  still passes and still proves what it claims about `EdgeReportCache`, and touching a file outside
  the plan's named list for a cosmetic comment fix seemed like exactly the kind of scope-drift the
  phase spec repeatedly warns against. Flagging for the reviewer/auditor to confirm this judgment.
- **`sqlite3` CLI is not installed in this environment** — durable-cache content during live
  verification was inspected via a one-off Python `sqlite3` module script instead of the `sqlite3`
  shell tool; no functional impact, noted only in case a future session expects the CLI to be present.
- **Bonus real-corpus items intentionally NOT attempted this iteration** (matching the phase spec's
  own explicit framing — never required for this iteration's Definition of Done): verifying the
  literal "restart + `/structure` ready within 10 seconds of navigation" figure against the real
  `.data/` corpus (`*(operator-verified on the real corpus)*` in goal.md) — the scoped/keyless
  verification above is what this iteration's Definition of Done actually requires.

## Suggested Next Phase

All 7 Must-have journeys of "The Fast Wall" interlude (J-01 through J-07) should now be `passing` if
J-06 lands cleanly — per this agent's own rules, the developer never marks journeys passing/failing;
that is the goal-evaluator's call next iteration, not predetermined here.
