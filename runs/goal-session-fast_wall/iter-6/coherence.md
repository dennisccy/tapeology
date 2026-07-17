# Iteration 6 — Coherence Audit

**Iteration:** goal-fast_wall-iter-6
**Date:** 2026-07-17
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

This iteration (J-06) touches exactly one registered concept: the touch-event/case-study registry
("Unchanged existing owners" table, blueprint.md) owned by `setups.py` → `GET /research/setups` /
`GET /research/setups/{id}`. It adds a new accelerator, `setups_scan_cache.db`
(`app/research/setups_scan_cache.py`), already pre-registered at baseline in blueprint.md's
"Rebuildable accelerators" list and refined (additive detail only) this iteration.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Touch events / case registry (`compute_setups`) | OK — same sole computer, same two endpoints | `apps/backend/app/research/setups.py:184-203` (`compute_setups`); call sites unchanged at `routes.py:1945`, `routes.py:1967`, `edge_report.py:582`, `edge_report.py:932` (grep-confirmed, all still 2-arg `compute_setups(store, config)`) |
| `setups_scan_cache.db` (new accelerator) | OK — pure storage, not a second computer; no route/MCP tool reads it directly | `apps/backend/app/research/setups_scan_cache.py:108-176` (`SetupsScanCache.lookup`/`.publish` — no scan logic); `grep -rn "SetupsScanCache\|setups_scan_cache"` across `apps/backend/app` returns matches only inside `setups.py` and `setups_scan_cache.py` itself — no route, no MCP registration |
| Compute-job snapshot, not-computed edge-report payload (J-01/J-04/J-05's registered values) | OK — untouched | `edge_report.py`, `edge_report_compute.py`, `edge_report_cache.py` not in the diff except one reused import (`edge_report_cache._config_content_hash`); no method body changed |

**Duplicate-computation check:** `_run_full_panel_scan` (the sole computer, formerly/still the real
scan) is unchanged in body; `compute_setups` still calls it, and only it, on a genuine miss
(`setups.py:200`). `SetupsScanCache` never independently derives events — `lookup`/`publish` are pure
SQLite read/write with no scan logic (`setups_scan_cache.py:143-176`). No second implementation of the
scan exists anywhere in the diff.

**Non-canonical-source check:** zero new UI/REST/MCP surface reads `setups_scan_cache.db` — confirmed
by grep; only `compute_setups`'s own internals construct `SetupsScanCache`. The frontend is
byte-unchanged (0 files touched — confirmed by diff and by `reports/phase-goal-fast_wall-iter-6-ui-surface-map.md`'s own "Frontend surfaces changed (code): 0" summary), so no UI surface could even be fetching from a new source.

**Key-coverage sanity check (bears on "no divergent accelerator output," which the blueprint frames as
part of the single-source-of-truth data contract):** `edge_report_cache._config_content_hash`
(`edge_report_cache.py:150-156`) hashes `dataclasses.asdict(config)` with **no exclusion set** — unlike
`config_fingerprint()`, which the code and tests confirm drops the `setups_*`/`tradability_*`/`sr_*`
families (`Config` fields at `apps/backend/app/config.py:1110-1287`). `setups.py` imports this function
verbatim (`setups.py:52`) rather than re-deriving it — the same single key-derivation function
`edge_report_backtest_cache.py` already reuses. No second, divergent hash implementation exists.

**New displayed value check:** none. `compute_setups`'s served shape (`{"events": [...]}`) is
byte-unchanged; the spec's own "New information displayed: None new" self-attestation is accurate.

## Information Architecture check

Zero new pages/routes/features this iteration — confirmed by the diff (no frontend file touched) and
by the ui-surface-map ("New pages/routes: 0", "Navigation changes: no"). The blueprint's Navigation
skeleton and Feature/journey homes table are byte-unchanged (the only blueprint.md diff is the top
HTML-comment "iter-6 update" note and one accelerator-bullet detail line — verified directly with
`git diff a93fe40b... -- runs/goal-session-fast_wall/state/blueprint.md`, which is excluded from the
main noise-cut diff by pattern but was read in full separately). J-06's already-registered home
("no dedicated UI panel — accelerates `GET /research/setups`, backing Structure's Case Studies +
`/studies`") required no page/route, so there is nothing new to place or link.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| J-06 durable setups scan cache | OK — no UI panel needed per its own IA row; none added | blueprint.md IA table (unchanged this iteration); `structure/page.tsx` not in diff |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `README.md` was updated (by the pipeline's readme-maintainer step, not `setups.py`'s scope) to
  describe the live compute-progress counter's "reused from already-completed work" figure and the
  resumable/multi-worker sweep — capabilities the blueprint records as already shipped in iter-5
  (J-05), not new this iteration. This is stale-documentation catch-up, not a new claim; not a
  coherence violation (no code path, no nav element, no served value is affected).
- The blueprint's `setups_scan_cache.db` bullet update is additive-only, matching the pattern of the
  iter-4/iter-5 accelerator-bullet refinements: no new Data Contract row, no IA change, no
  `blueprint.reapproval-requested` file (confirmed: none exists in the session dir) — consistent with
  "additive detail only."
