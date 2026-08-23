# goal-rapid-microscope-iter-26 Dev Handoff

**Phase:** goal-rapid-microscope-iter-26
**Date:** 2026-08-23
**Agent:** developer
**Status:** complete

## What Was Built

This iteration builds exactly the first two dev-owned, non-owner-blocked items the iter-25
evaluator named as safe to do now (item 4, referee disclosure, is explicitly deferred), plus
confirms the third (test-harness) item is already carried by the iteration's own metadata with
zero app-code change. Zero served value changes; zero frontend files change.

1. **A durable, composite-keyed band-touch count cache** (`MicroBandTouchCache`, new in
   `micro_readiness.py`), closing the "desk readiness ~22s-and-growing uncached band-touch walk"
   gap the iter-25 evaluator measured against the real store (the same code path backs the
   `desk_micro_readiness` MCP tool's ~13.5s warm / ~13min cold timing). It mirrors
   `MicroReadinessCache`'s existing `fallback_frac` table precedent byte-for-byte (own SQLite
   table, own env var `TAPEOLOGY_MICRO_BAND_TOUCH_CACHE_DB`, self-heal-on-corrupt contract, a miss
   that never computes on its own). It is keyed on the COMPOSITE
   `(dataset_meta["checksum"], resolver.map_key(symbol, window_start_epoch))` — never the checksum
   alone — so a re-warmed/changed band map (a new `map_key` under an unchanged dataset) is a
   genuine cache miss, never a stale hit under the old map.
   - Wired lookup-or-compute-and-publish into `micro_join.joinable_corpus_counts` (a new optional,
     keyword-only `band_touch_cache=None` parameter). Every existing caller that omits it (every
     pre-iteration call site and test) is byte-identical to before: the code falls through to the
     original uncached `enumerate_band_touches(...)` call.
   - `micro_readiness.build_readiness` gained the matching optional `band_touch_cache=None`
     parameter, threaded straight through to `joinable_corpus_counts`.
   - `micro_routes.py`'s `GET /research/desk/micro/readiness` route constructs the cache as a new
     FastAPI dependency (`get_micro_band_touch_cache`, mirroring the existing
     `get_micro_readiness_cache` pattern) and passes it into `build_readiness(...)`. The
     `desk_micro_readiness` MCP proxy is unaffected (it is a byte-identical GET proxy — no code
     there changes).
   - The served `band_touch_count` value is unchanged either way — only warm-path latency
     improves. No `Config` field, no fingerprint movement, no change to `micro_readiness.py`'s
     served response shape.

2. **Selector-table dedup in `micro_routes.py`.** `_BAND_TOUCH_PILOT_SELECTORS` /
   `_PLAYBOOK_SIGNAL_PILOT_SELECTORS` (two hand-written frozensets restating
   `scout._PILOT_GRID_SELECTORS`) are replaced by one derivation function,
   `_pilot_selectors_by_kind(kind, source=None)`, that filters the ONE canonical
   `scout._PILOT_GRID_SELECTORS` table by `kind` at CALL TIME (every use site in
   `trigger_scout_compute` now calls it directly — `_pilot_selectors_by_kind("band_touch")` /
   `_pilot_selectors_by_kind("playbook_signal")`), never as a module-level constant frozen once at
   import. This is deliberate: a frozen-at-import literal would only happen to equal today's
   values rather than genuinely track the source table, which is exactly what the genuine-
   derivation test (TC-6b) below proves is no longer possible. The three now-unused
   `GRID_SELECTOR_*` name imports were removed from `micro_routes.py`'s `from .scout import (...)`
   block (they had become docstring-only references); `_PILOT_GRID_SELECTORS` was added to that
   same import instead.

3. **Test-harness scope confirmed, no app-code change (TC-1).** The phase spec's own Goal Mode
   Metadata already widens `Required-still-passing` to the full remaining seven-golden set
   (J-02, J-03, J-04, J-05, J-06, J-09, J-10), so the deterministic replay lane driving all nine
   stored `journey-scripts/*.json` files (J-01, J-02, J-03, J-04, J-05, J-06, J-08, J-09, J-10;
   J-07 has no golden by design) in one recorded run is a pipeline/harness-level effect of that
   metadata widening, not something this dev pass needed to build. No source file under
   `runs/goal-session-rapid-microscope/journey-scripts/` was touched this iteration. The
   9/9-PASS report itself (`reports/phase-goal-rapid-microscope-iter-26-regression-replay-
   results.md`) is produced by the pipeline's replay-lane step, not by this dev pass.

## Files Changed

- `apps/backend/app/research/micro_readiness.py` — new `MicroBandTouchCache` class (composite-key
  SQLite cache: `checksum`, `map_key` → `touch_count`), `resolve_micro_band_touch_cache_db_path`
  helper, and a new optional `band_touch_cache` parameter on `build_readiness` threaded to
  `joinable_corpus_counts`.
- `apps/backend/app/research/micro_join.py` — `joinable_corpus_counts` gains an optional
  `band_touch_cache=None` keyword parameter; when given (and a `resolver` is also given), each
  record's band-touch count is looked up or computed-and-published per the composite key before
  falling back to `enumerate_band_touches` on a miss.
- `apps/backend/app/research/micro_routes.py` — (a) new `get_micro_band_touch_cache` FastAPI
  dependency, threaded into `GET /research/desk/micro/readiness`; (b) `_BAND_TOUCH_PILOT_SELECTORS`
  / `_PLAYBOOK_SIGNAL_PILOT_SELECTORS` replaced by the `_pilot_selectors_by_kind(kind, source=None)`
  derivation function, called at both use sites in `trigger_scout_compute`; unused
  `GRID_SELECTOR_*` imports removed, `_PILOT_GRID_SELECTORS` imported from `.scout` instead.
- `apps/backend/tests/test_micro_readiness.py` — new `MicroBandTouchCache` unit tests (cold-miss,
  publish/lookup round trip, composite-key-never-checksum-alone, corrupted-DB-survives-as-a-full-
  miss), `resolve_micro_band_touch_cache_db_path` default/env-override tests, a route-level
  corruption test (`GET /research/desk/micro/readiness` stays HTTP 200 with a corrupted band-touch
  cache DB); the `client` fixture now also overrides `get_micro_band_touch_cache` (tmp_path-scoped,
  matching the file's existing hermeticity discipline for every other store/cache dependency).
- `apps/backend/tests/test_micro_join.py` — new tests exercising the cache-wired path inside
  `joinable_corpus_counts`: a cold lookup that computes-and-publishes exactly one row for the
  composite key (verified via a raw SQLite row-count check), a `DatasetStore.load_events`
  call-count spy proving a warm second call never re-reads events, and a re-warmed-`map_key` test
  (two `BandMapResolver`s over genuinely different bar-store signatures) proving a new map identity
  is a genuine miss that never serves the old key's stale count.
- `apps/backend/tests/test_scout.py` — three new TC-6 tests: (a) the derived selector sets equal
  today's known sets; (b) a synthetic third entry added to a LOCAL COPY of
  `scout._PILOT_GRID_SELECTORS` (never the real module table) is reflected in the derived
  frozenset when passed explicitly as `source`, proving genuine runtime derivation; (c) a
  source-scan guard confirming `micro_routes.py` never hardcodes a second copy of any pilot
  selector's literal string value.
- `docs/handoffs/goal-rapid-microscope-iter-26-dev.md` — this file.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest -q` (full backend suite, plus targeted
full-file runs of the three touched test files individually beforehand)

Results:
- `tests/test_micro_join.py`: 47/47 passed
- `tests/test_micro_readiness.py`: 49/49 passed
- `tests/test_scout.py` (TC-6a/b/c subset, then full file via the full-suite run): all passed
- Full backend suite: **3,474 passed / 8 skipped / 0 failed / 0 errors** (3,482 collected — matches
  a clean, error-free collection of the whole suite; the 8-skip count matches the era-open baseline
  recorded in `docs/goal.md`'s Success Criteria #1, which states the skip count never grows)
- `Config().config_fingerprint()` == `08e471b10130e1e2` — unchanged, as required
- Zero `referee_*.py` files touched this iteration (`git status`/`git diff --stat` confirm no
  changes) — the SHA-256 byte-freeze is trivially intact
- `grep -rn MicroBandTouchCache app/ tests/` shows real production reach beyond its own
  definition file (`micro_routes.py`'s `get_micro_band_touch_cache` dependency and its use inside
  `GET /research/desk/micro/readiness`) — the iter-21 lesson's own reachability check, satisfied

## Pre-handoff service verification

- `bash scripts/dev.sh` started both backend (`:8301`) and frontend (`:3301`) cleanly; `GET /docs`
  and `GET /desk` both returned HTTP 200.
- Stopped both processes (port-scoped `fuser -k`, confirmed no lingering `uvicorn`/`next dev`
  processes or open sockets on either port), then restarted cleanly with no port conflicts — both
  came up healthy again on the same ports.
- No live/real-store manual hit of `GET /research/desk/micro/readiness` was made against the real
  ~26 GB ambient tick corpus during this verification pass (that corpus has grown far beyond the
  ~0.92 GB figure recorded at era authoring, so a cold call there is a multi-minute operation by
  design — exactly the cost this iteration's cache targets). The route's correctness against real
  data is proven indirectly: `apps/backend/tests/test_micro_readiness.py`'s real-corpus-backed
  module-scoped fixture tests (TC-1 through TC-5 in that file's own numbering) ran the ACTUAL
  committed dataset store and passed. QA's browser pass (TC-7/TC-8) is expected to run against the
  fixture-scoped rig per the era's own "keep browser acceptance narrow" iteration-hygiene rule, not
  the operator's real store.

## Known Issues

- None discovered inside this iteration's own scope. The referee disclosure item (deferred,
  out of scope this iteration per the phase spec) and the two owner-owned items (chain-ledger
  identity-commitment gap, sealed judge's `econ_floor`) remain open — unchanged by this iteration,
  as the phase spec instructs the evaluator to carry them forward without re-deriving.
- `_pilot_selectors_by_kind`'s `source` parameter type hint is a plain `dict[str, tuple[str, str]]
  | None` string annotation (matching the module's existing quoting convention for forward-
  referenced types elsewhere in this file) rather than importing `Mapping` from `typing` — a small
  interpretation call, logged here rather than in the assumption ledger since it has zero behavior
  or API-shape effect.
