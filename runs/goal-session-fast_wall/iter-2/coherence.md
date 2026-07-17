# Iteration 2 — Coherence Audit

**Iteration:** goal-fast_wall-iter-2
**Date:** 2026-07-17
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

This iteration (J-02) ships exactly the two accelerators the blueprint's "Rebuildable
accelerators" list pre-registered at baseline, and touches no canonical-value owner. Traced each
against both the registered source (`runs/goal-session-fast_wall/state/blueprint.md` lines 64-75)
and the diff.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Bar-series verified record (owner: `bars.py`, served by `GET /research/bars`) | OK | `apps/backend/app/research/bars.py:114-142` (`_cached_load`) wraps the existing `_load` verifier — no reimplementation. `_load_by_id` (line 149) and `list()` (line 179) still route through `_load` on any stat mismatch; only a stat-identical hit is served from cache. |
| Recorded-dataset metadata (owner: `datasets.py`, served by `GET /research/datasets`) | OK | `apps/backend/app/research/datasets.py:299-337` (`_cached_meta`) wraps the same `_load`; `get()`/`list()` (lines 341-373) unchanged shape, only fresh-copy `event_counts`. |
| `dataset_index.db` (new durable accelerator, pre-registered) | OK | `apps/backend/app/research/dataset_index.py` — `DatasetIndex.insert`/`lookup` store/return metadata the caller already verified; it computes nothing itself (no hashing, no parsing of dataset content). Consulted only from `datasets.py:323-329`, never exposed on any route or MCP tool directly. |
| `DatasetStore.load_events()` / `.replay()` (the paths that feed research values) | OK — trust boundary preserved | `datasets.py:289-297` (`_load_by_id`, used only by `load_events`/`replay`) is untouched and still calls `self._load(path)` unconditionally; mechanically proven by `test_load_events_and_replay_fully_reverify_even_when_the_metadata_cache_is_warm` (`apps/backend/tests/test_datasets.py:680-699`, TC-7). |
| `GET /research/datasets` (the ONE serving endpoint) | OK — still the only endpoint | `apps/backend/app/research/routes.py:379-397` (`get_dataset_store`) only changes internal DI wiring (`index_db_path=...`); no new route, no changed request/response shape. Byte-identity proven by `test_warm_cache_response_is_byte_identical_to_a_forced_fresh_verify` (`test_datasets_api.py:744-773`, TC-8 REST leg) and the MCP leg in `test_mcp_server.py:842-877`. |
| Durable-index-served metadata vs. fresh verify (no divergent accelerator output) | OK | `apps/backend/tests/test_dataset_index.py:91-134` (TC-9, restart simulation) and `:137-190` (TC-10, delete-and-repopulate) both assert `json.dumps(..., sort_keys=True)` equality between the index-served path and a from-scratch, index-free verify. |
| New displayed value / field | N/A — none added | Both `get()` methods return the identical response shape as before caching (`bars.py:161-163`, `datasets.py:352-353`); confirmed no new key anywhere in the diff. |

No new function anywhere in the diff independently recomputes a checksum, a bar/dataset record, or
any Data-Contract-registered research value (`levels.py`, `tradability.py`, `setups.py`,
`strategies.py`, `edge_report.py`, `edge_report_cache.py`, `backtests.py`, `pnl_ledger.py`,
`taxonomy.py` — none appear in the diff or the `--stat` summary). The only new module,
`dataset_index.py`, is a pure store/retrieve cache with a single caller (`datasets.py`) and no
route of its own — matching the blueprint's "owns nothing" framing verbatim.

## Information Architecture check

`Frontend Present: no` (iteration spec header) and confirmed by
`reports/phase-goal-fast_wall-iter-2-ui-surface-map.md` ("Backend-only phase... No UI surfaces
affected"). No frontend file appears anywhere in the diff or `git status`.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | OK — N/A | No nav/router file touched; `git diff --stat` and `git status` show zero files under any frontend path. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `README.md` gained a documentation-only edit (split one capability bullet into two: the existing
  "Edge report caching..." bullet plus a new "Safe-by-default Edge Report" bullet describing the
  not-computed panel). This describes J-01 (already shipped and coherence-PASS'd in iter-1), not
  new J-02 work — no new value, endpoint, or route is implied. README refresh is normal
  per-iteration housekeeping (`readme-maintainer`'s stated role in `CLAUDE.md`), not a coherence
  concern.
- The two new module-level caches and the durable index are exactly the items blueprint.md's
  "Rebuildable accelerators" list already named at baseline; the iteration spec correctly made no
  blueprint edit. Nothing for the next iteration to consolidate.
