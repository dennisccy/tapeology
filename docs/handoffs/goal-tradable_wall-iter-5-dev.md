# goal-tradable_wall-iter-5 Dev Handoff

**Phase:** goal-tradable_wall-iter-5
**Date:** 2026-07-14
**Agent:** developer
**Status:** complete

## What Was Built

A backend-only enabler pass resolving the two blocking watch-items the iter-4 evaluator named
("audit B1", "audit B3") that must be fixed **before** J-05 renders `/structure` in iter-6. No
journey flips this iteration — J-05 stays `failing` by design. Both changes live entirely inside
`apps/backend/app/research/setups.py`; every caller (`routes.py`, `edge_report.py`) is untouched.

- **B1 — additive recency-boundary disclosure.** A touch event whose reaction horizon runs past
  the end of the store (`touch_index + horizons[0] >= len(all_bars)` — a touch inside the store's
  most-recent stored session) now additively carries two new fields on every event:
  `effective_reaction_horizon_bars` (the bar count the reaction close was actually read at —
  equal to the full configured `horizons[0]` whenever untruncated) and
  `reaction_boundary_truncated` (`true` exactly when the store ran out early). The `reaction`
  label itself is never mutated and the event is never excluded — the truncation is *disclosed*,
  not hidden or suppressed, matching the "additive disclosure" interpretation call logged in
  `runs/goal-session-tradable_wall/state/assumptions.md`. Implemented in
  `_reaction_and_forward_returns` (computes both new values from the same `reaction_index` the
  reaction close already reads) and threaded through `_event`.
- **B3 — a process-local memoized scan cache.** `compute_setups(store, config)` is now a thin,
  byte-identical memoizing wrapper: the real scan (unchanged algorithm, renamed
  `_run_full_panel_scan`) is only run when the store's content signature or the config object's
  identity changes since the last call; an unchanged store/config replays the identical cached
  result instead of re-running the full panel scan (measured live against the operator's real
  47-series store: **276.03s cold → 0.28s cached, ~985× faster** — see Tests Run). The signature is a sorted tuple of
  every healthy series' `(symbol, timeframe, id, checksum)` from `store.list()` (`bars.py` already
  exposes `checksum` per series). The cache is a single most-recent slot (module-level dict, two
  keys: `"key"`/`"result"`) — process-local, in-memory only, never SQLite/disk-persisted, mirroring
  the "rebuildable accelerator, never a source of truth" contract `bar_index.py` already lives
  under. `GET /research/setups`, `GET /research/setups/{id}`, and
  `edge_report.run_strategy_comparison_report` all call the SAME `compute_setups`, so all three
  now share the one cache transparently with **zero changes to `routes.py` or `edge_report.py`**.
- **Full re-verification of J-01/J-02/J-04/J-07** (frozen-foundation regression): confirmed
  `config_fingerprint() == "4d665603569b9dbf"` (existing tests, unchanged, still pass — no new
  `Config` field was needed for either B1 or B3), the strategy registry order stays `(v1,
  structure_tape, structure_tape_map)` (config.py/backtests.py untouched, zero diff), and
  `git diff --name-only -- apps/` touches exactly `apps/backend/app/research/setups.py` plus its
  two test files — `levels.py`, `tradability.py`, `engine/`, `strategies.py`, `bars.py`,
  `datasets.py`, `adapters/`, `edge_report.py`, and `backtests.py` are absent from the diff.

## Files Changed

- `apps/backend/app/research/setups.py` — B1: `_reaction_and_forward_returns` now returns a
  4-tuple (`reaction, forward_returns, effective_reaction_horizon_bars,
  reaction_boundary_truncated`); `_event` accepts and embeds the two new fields. B3: `compute_setups`
  is now a memoizing wrapper (`_SCAN_CACHE` module-level single-slot cache + `_store_signature`
  helper); the original scan body is renamed `_run_full_panel_scan` (algorithm byte-identical,
  only its call to `_event`/`_reaction_and_forward_returns` updated for the extra return values).
  Module docstring extended with B1/B3 sections.
- `apps/backend/tests/test_setups.py` — extended the pinned AAPL 2026-06-22 test with the two new
  non-boundary field assertions (`reaction_boundary_truncated is False`,
  `effective_reaction_horizon_bars == 78`); added a purpose-built `SYN-SETUPS-BOUNDARY` synthetic
  fixture (5 total 5m bars, so the store runs out of bars long before the real 78-bar horizon) plus
  two tests (boundary disclosure with exact values, determinism); added four B3 cache tests
  (cache-hit-vs-fresh-scan byte-identity, computed-once-via-spy, checksum-bust-via-spy,
  enriched-detail-never-leaks-into-shared-list using the real J-03 PG fixture); extended the
  `test_compute_setups_itself_never_touches_the_dataset_store` architecture guard to also inspect
  `_run_full_panel_scan` (the function that now actually contains the scan loop).
- `apps/backend/tests/test_setups_api.py` — added the two new field names to `_EVENT_FIELDS` (the
  route-level exact-field-set assertion); no other change — route code itself is untouched.

No changes to `test_setups_api.py` route bodies, `test_edge_report.py`, `test_edge_report_api.py`,
`routes.py`, `edge_report.py`, or any config/fixture file — all of those were re-run (unmodified)
to prove the change is transparent to every caller.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1337 passed, 7 skipped, 0 failed, 0 errors** (1344 collected). Iter-4's own full-suite
run (its dev handoff) reported **1331 passed, 7 skipped** (1338 collected) — this iteration adds
exactly **+6 passing tests** (2 B1 boundary tests + 4 B3 cache tests) with the identical 7 skips
(no new skip, no resolved skip — the skip set is the pre-existing `@pytest.mark.integration`
credentialed tests, unaffected by this change) and zero failures/errors: a clean, fully-accounted
delta with no regression.

Targeted re-runs during development (all green, run before the full suite as faster iteration
loops):
- `tests/test_setups.py`: **32 passed** (26 pre-existing + 6 new: 2 boundary, 4 cache).
- `tests/test_setups_api.py` + `tests/test_edge_report.py` + `tests/test_edge_report_api.py`
  (combined): **52 passed**.
- `config_fingerprint()` reconfirmed `4d665603569b9dbf` via the existing (unmodified)
  `test_setups_config_fields_are_excluded_from_config_fingerprint` and
  `test_recording_config_fields_are_excluded_from_config_fingerprint`.

**Live smoke test (pre-handoff verification):** started the real backend
(`.venv/bin/uvicorn main:app`) on an isolated port. First against a fresh, empty, isolated
`TAPEOLOGY_BAR_DIR`/`TAPEOLOGY_DATASET_DIR`/`TAPEOLOGY_JOURNAL_DB` — confirmed `/health` 200,
`GET /research/setups` returns `{"events": []}` in ~9ms (honest empty state), `GET
/research/edge-report` returns the honest empty-registry shape. Then restarted against the
**operator's real, already-populated `.data/bars/` (47 real series) and `.data/datasets/` (7 real
PG datasets)** — the literal scenario iter-4's handoff flagged as taking minutes — and measured all
four call sites in sequence:

| Call | Endpoint | Elapsed | Notes |
|---|---|---|---|
| 1 (cold) | `GET /research/setups` | **276.03 s** | uncached — matches iter-4's ~4m43s citation; returned **801 events** |
| 2 (cache hit) | `GET /research/setups` | **0.28 s** | byte-identical to call 1 (`diff` confirmed) — **~985× faster** |
| 3 (cache hit) | `GET /research/setups/{id}` | **0.32 s** | detail route shares the SAME cache |
| 4 (cache hit) | `GET /research/edge-report` | **0.40 s** | edge report shares the SAME cache (7 real datasets exist, so `run_strategy_comparison_report` genuinely calls `compute_setups` — a skipped call would prove nothing) |

This is real, concrete, cross-endpoint evidence — not just unit-test inference — that the single
in-process cache correctly serves `list_setups`, `get_setup`, AND
`run_strategy_comparison_report` off of ONE scan. It also independently reproduced the exact
**audit-B1 finding from iter-4's evaluator**: of the 801 real events, exactly **13** carry
`reaction_boundary_truncated: true` (iter-4's own eval.md cites "13/801 most-recent-session
events") — confirming B1 fires precisely on the real cases it was built for (sample: AAPL
2026-07-13, `effective_reaction_horizon_bars: 77`, `reaction: "chopped"`). The edge report's
`train`/`holdout`/`surviving_train_cells` are honestly empty — the 7 real datasets are all
symbol `PG`, which is not a panel symbol (the pre-existing, documented iter-4 Known Issue #6), so
no dataset resolves an owning event; this is expected, not a bug, and does not affect the cache
proof (the 0.40s response time IS the proof `compute_setups` was called and hit the cache — a
skipped call due to an empty registry would also have been fast, but for a different, unrelated
reason, which is why call 1's 276s cold scan matters as the baseline).

The server was stopped afterward (`pkill -f "uvicorn main:app"`), confirmed via `ps aux` (no
uvicorn process remains) and `ss -ltn` (port 8301 free).

## Known Issues

1. **Cache correctness relies on `id(config)` identity, not value equality.** `Config` is a frozen
   dataclass but carries plain `dict` fields (e.g. `tradability_quality_weights`), so it is not
   hashable and cannot be used as a dict key by value. Every production caller
   (`routes.py`/`edge_report.py`) shares the one imported `CONFIG` singleton, so `id(CONFIG)` is
   stable for the life of the process — this is the path that matters. Two *different* `Config(...)`
   objects constructed with identical field values (as some tests do) are treated as distinct cache
   entries — always a safe, conservative cache **miss** (extra recompute, never a wrong answer),
   never a correctness risk.
2. **Store-signature computation costs one `store.list()` call on every request, hit or miss** —
   `list()` re-verifies every registered series' checksum and embeds its full bar data, so it is
   not free. This is the plan's own explicit design (a deterministic signature over `store.list()`),
   and it is dramatically cheaper than the scan it guards: `_run_full_panel_scan`'s existing
   `_select_5m_series` already calls `store.list()` once **per panel symbol** (12 calls) before
   this change; a cache HIT now pays for exactly one `list()` call total instead of the full scan.
   Measured live against the operator's real 47-series store: a cache-hit `GET /research/setups`
   call (which pays this `list()` cost) completed in 0.28s — the signature cost is real but
   negligible next to the 276.03s it replaces. `_select_5m_series`'s own repeated-`list()` pattern
   was left untouched — out of this iteration's scope (only the cache layer was asked for).
3. **No thread-lock around the cache.** FastAPI can run sync route handlers in a thread pool, so
   two concurrent requests could theoretically both miss the cache and recompute simultaneously.
   Worst case is redundant work (both threads compute the same deterministic result and the last
   write wins) — never a torn or incorrect result, since the scan is a pure function of its inputs.
   Consistent with the "rebuildable accelerator, never a source of truth" framing; no locking was
   added since nothing here is unsafe, only occasionally-redundant.
4. **J-05 stays `failing` by design.** This iteration is a backend-only enabler per the goal-mode
   spec's own "Depth = full, target journeys: J-05" framing — no `/structure` UI change was made or
   attempted; iter-6 renders the UI on this now-recency-honest, now-bounded substrate.

**Nothing from the phase spec is incomplete.** All Definition-of-Done items are met by the tests
listed above. Out-of-scope items (the `/structure` render, cockpit changes, credentialed
recording, any frozen-file mutation, disk-persisting the cache, new MCP tools) were not touched.
