# goal-fast_wall-iter-2 Dev Handoff

**Phase:** goal-fast_wall-iter-2
**Date:** 2026-07-17
**Agent:** developer
**Status:** complete

## What Was Built

Target journey **J-02** ("The stores stop re-reading — verified-content caches + durable dataset
index"). Backend-only, zero frontend files touched (`Frontend Present: no`, confirmed by diff).

- **`bars.py`**: a module-level, stat-keyed `(path, st_size, st_mtime_ns)` verified-record cache
  (`_VERIFIED_CACHE`), mirroring `setups.py`'s `_SCAN_CACHE` atomic-publish discipline. A stat
  match serves the cached `_LoadedBarSeries` with zero I/O; any mismatch re-runs the full existing
  `_load` verifier unchanged; `BarSeriesIntegrityError` is never cached; a ~2s racy-write guard
  refuses to publish a just-written file. `get`/`list` now route through the cache (via
  `_load_by_id`/`list`'s loop calling the new `_cached_load`) and return fresh per-row dict copies
  every call, so a caller mutating the returned structure can never poison a later cached read.
  `load_bars` is unchanged in code but now benefits transitively (it already built fresh `RawBar`s
  from the loaded rows). Added a public, read-only `BarStore.root` property and a test-only
  `_reset_verified_cache_for_tests()` helper.
- **`datasets.py`**: the same stat-keyed cache shape, scoped to **metadata only**
  (`_VERIFIED_META_CACHE`), consulted exclusively by `get()`/`list()` via a new `_cached_meta`
  method. `load_events()`/`replay()` are untouched — they still call `_load_by_id`/`_load` directly
  and unconditionally on every call (the verification trust boundary). `event_counts` (the one
  nested mutable field in a dataset's metadata) is copied fresh per call for the same
  mutation-isolation reason as `bars.py`'s per-row copies — not itself a numbered test case, but
  the identical caching-introduced hazard, so I fixed it defensively and added a test for it
  (`test_get_and_list_return_event_counts_copies_a_caller_mutation_never_poisons_the_cache`).
  `DatasetStore.__init__` gained a keyword-only `index_db_path: str | None = None` (default
  preserves today's exact in-process-only behavior for every existing caller — none pass it
  today); when set, `get`/`list` consult the durable index (lazily constructed, so construction
  itself stays I/O-free) after the in-process cache and before a full verify, and publish
  newly-verified metadata into it.
- **New `dataset_index.py`**: a durable sibling SQLite metadata index —
  `dataset_index(path PRIMARY KEY, size, mtime_ns, meta_json, created_utc)`, `meta_json` stored via
  plain `json.dumps` WITHOUT `sort_keys` (the byte-identity precedent). Mirrors `bar_index.py`'s
  hermetic-DI'd-path / WAL + busy_timeout / "derived, rebuildable, owns nothing" shape (one
  long-lived connection, not `edge_report_cache.py`'s per-call-fresh-connection shape — this module
  doesn't need to survive that module's own many-threads-one-instance concurrency test). No
  `reindex()` method — unlike `bar_index.py`, repopulation happens organically through
  `DatasetStore.list()`'s own per-file traversal on a cold/deleted index, so a dedicated bulk
  rebuild method isn't needed by anything.
- **`routes.py`**: `get_dataset_store()` grew the exact `get_bar_index()` env-else-sibling shape:
  `TAPEOLOGY_DATASET_INDEX_DB` env var if set, else `.data/dataset_index.db` (a sibling of the
  resolved dataset directory), passed as `DatasetStore(..., index_db_path=...)`. Zero change to any
  route's request/response body or `Depends` signature.
  `EdgeReportCache` — this speedup reaches `GET /research/edge-report` (and its MCP proxy) as a
  transparent side effect through the now-cached `dataset_store.list()`, with zero code change to
  `edge_report.py`, `edge_report_cache.py`, or `structure/page.tsx`, exactly as scoped.
- **`tests/conftest.py`**: the file's first autouse fixture, resetting both new module-level caches
  before every test (via each module's own test-only reset helper) — prevents unbounded cache
  growth across a long suite run and guarantees no cross-test leakage (TC-12).

## Files Changed

- `apps/backend/app/research/bars.py` — stat-keyed verified-record cache, `BarStore.root`
  property, test-only reset helper; `get`/`list`/`load_bars` routed through the cache.
- `apps/backend/app/research/datasets.py` — metadata-only stat-keyed cache, `index_db_path`
  constructor arg + lazy durable-index wiring, test-only reset helper; `get`/`list` routed through
  the cache; `load_events`/`replay` deliberately untouched.
- `apps/backend/app/research/dataset_index.py` (new) — the durable sibling SQLite metadata index.
- `apps/backend/app/research/routes.py` — `get_dataset_store()` grows the env-else-sibling
  resolver for `TAPEOLOGY_DATASET_INDEX_DB`.
- `apps/backend/tests/conftest.py` — first autouse fixture, resets both new caches per test.
- `apps/backend/tests/test_bars.py` — 7 new tests (TC-1, TC-2, TC-3, TC-5 bars leg, TC-6, TC-11,
  TC-12).
- `apps/backend/tests/test_datasets.py` — 4 new tests (TC-4, TC-5 datasets leg, TC-7, plus the
  `event_counts` copy-isolation test).
- `apps/backend/tests/test_dataset_index.py` (new) — 7 tests: direct `DatasetIndex` lookup/insert
  contract tests, plus TC-9 and TC-10 through `DatasetStore`.
- `apps/backend/tests/test_datasets_api.py` — 1 new test: TC-8's REST leg (warm response
  byte-identical to a response forced through both cache layers being cold).
- `apps/backend/tests/test_edge_report_api.py` — 1 new test: TC-14 (the existing integrity-error
  500 path survives a prior warm `GET /research/datasets` read on the same file).
- `apps/backend/tests/test_mcp_server.py` — extended
  `test_datasets_tool_byte_identical_on_a_non_empty_live_list` (TC-8's MCP leg) to age every
  recorded dataset file's mtime past the racy-write window before the comparison, so the test
  actually exercises the warm-cache path instead of always hitting cold-by-freshness; run both
  standalone and inside the full module per the iter-1-applied lesson.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q` (from `.claude/project-template.md`'s
inferred convention — see Known Issues for a note on this file's actual state).

Result: **1427 passed, 7 skipped, 0 failed** (1434 collected total) in 435.78s. Zero new failures,
zero newly-skipped or deleted tests. `config.config_fingerprint()` confirmed still
`4d665603569b9dbf` (no `Config` field added — `index_db_path` is a plain constructor keyword, not
a config field).

Targeted runs during development (all green, included in the full-suite number above):
- `test_bars.py` + `test_datasets.py` + `test_dataset_index.py`: 48 passed.
- `test_datasets_api.py` + `test_edge_report_api.py`: 30 passed.
- `test_mcp_server.py::test_datasets_tool_byte_identical_on_a_non_empty_live_list` standalone:
  1 passed.
- `test_mcp_server.py` full module (28 tests): all passed (the iter-1-applied "order-coupling"
  lesson — checked deliberately, since this file's byte-identity tests share module-scoped
  backend state).

## Real-corpus verification (operator-verified, TC-15 — non-blocking, recorded anyway)

The real operator corpus was present in this environment (`.data/datasets/`, 882MB, 18 datasets,
0 integrity errors) with no pre-existing `dataset_index.db`, giving a genuinely cold baseline.
Started the real backend via `scripts/dev.sh` (port 8301) with no `TAPEOLOGY_DATASET_DIR` override
(the real default corpus):

- Cold `GET /research/datasets` (first call, no durable index yet): **29.37s**, HTTP 200, 18
  datasets, 0 errors — closely matches goal.md's documented 31.4s baseline (same cost profile,
  measurement variance expected).
- Warm `GET /research/datasets` (same process, in-process cache populated): **0.00s**, byte-identical
  to the cold response (`diff` confirmed).
- **Restart simulation**: killed and restarted the real backend (a genuine new process, in-process
  cache cold), then timed the first post-restart call: **0.00s**, byte-identical to the original
  cold response — proving the durable `dataset_index.db` survives a restart and the backend never
  re-pays the ~30s cost, exactly Success Criterion #3's claim.
- Spot-checked `GET /research/edge-report` against the real corpus: correctly returns the
  J-01 `status: "not_computed"` honest payload (cold cache key, non-empty registry) — confirms
  the now-cached `dataset_store.list()` reaches `peek_strategy_comparison_report`'s
  `_verified_records` call as the transparent speedup the plan promised, with zero code change to
  `edge_report.py`.
- Frontend `/` and `/structure` both returned HTTP 200 against the real backend.

## Pre-handoff verification

- **Service startup**: `scripts/dev.sh` started both backend (:8301) and frontend (:3301) cleanly,
  no errors in either log. Stopped both, confirmed ports fully freed (note: killing `next dev`
  cleanly requires targeting the actual port-holder, not just a top-level PID — its process chain
  is `npm exec` → `sh -c` → `node`; `dev.sh`'s own pre-start cleanup already does this correctly
  via `lsof -ti :$PORT` + `fuser -k -9`, which target whoever holds the socket rather than assuming
  a specific parent PID). Started again — healthy in 2s, no port conflicts.
- **External integrations**: N/A — this iteration adds no adapter/scraper/external API surface
  (pure in-process + durable-cache accelerator over the existing file-based stores).
- **Native dependency binaries**: N/A — stdlib `sqlite3` only, no new runtime dependency (matches
  the anti-goal).
- Killed all server processes started for verification before finishing (confirmed via `ss`/`lsof`
  showing both ports fully freed, no lingering tapeology processes).

## Known Issues

- `.claude/project-template.md` resolves (via the `.claude` → `incredible_auto_dev/.claude`
  symlink) to the framework's generic, unfilled template — it does not carry this project's actual
  stack/test-command values. I inferred the real values from `docs/goal.md`'s Constraints section,
  `apps/backend/pyproject.toml`, and `scripts/start-backend.sh`/`scripts/dev.sh` instead (Python
  3.12+/FastAPI backend, `apps/backend/.venv/bin/python -m pytest tests/ -q`, Next.js 15 frontend).
  Not a gap introduced by this iteration — pre-existing project setup — but worth an operator fix
  at some point so future agents don't need to re-derive it from source.
- The defensive `except OSError: return self._load(path)` (or `.meta`) branch in both stores'
  new caching wrappers, guarding a file vanishing between a directory scan/existence check and the
  cache's own `path.stat()` call, is intentionally uncovered by a dedicated test — it is a
  vanishingly rare TOCTOU race preserving pre-existing `list()` behavior (a file that disappears
  mid-scan was always converted to a caught `*IntegrityError`/skipped, never an uncaught crash;
  this branch keeps that true now that a `stat()` call sits in front of the loader). Flagging for
  the reviewer/auditor rather than silently omitting the reasoning.
- Per the plan's own explicit note, the choice of exactly WHEN the durable index gets written
  (opportunistically on every full-verify miss, which is what I implemented) vs. only via a
  separate explicit publish step was called out as ordinary developer-level scoping, not a
  goal-interpretation ambiguity — both shapes satisfy TC-9/TC-10 identically. No open question left
  here.
