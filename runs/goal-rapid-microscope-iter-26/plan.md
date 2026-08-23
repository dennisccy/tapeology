# goal-rapid-microscope-iter-26 Execution Plan

## Context (do not re-derive)

Iter-25 verdict was ESCALATE (all 10 journeys `passing`, era not certifiable on 8 open minor
anti-goal items). The iter-25 evaluator's own ordered next-step list names three dev-owned,
non-owner-blocked items as safe to do now; this iteration builds exactly the first three and
explicitly defers the fourth (referee disclosure). No journey is FAILING/PARTIAL — J-01/J-08 are
Target only because they are the two browser-verifiable surfaces this iteration's code touches
(regression proof, not a new capability). Full depth is mandatory per rail (prior verdict
ESCALATE), independent of either change's own size.

## What to Build

- **Durable band-touch cache** (closes "desk readiness ~22s on the real store"): a new SQLite
  cache, mirroring `MicroReadinessCache`'s `fallback_frac` table precedent
  (`app/research/micro_readiness.py:226-289`), keyed on the COMPOSITE
  `(dataset checksum, resolver.map_key(symbol, window_start_epoch))` — never the checksum alone,
  so a re-warmed/changed band map (a new `map_key`) is a genuine miss, never a stale hit under
  the old map. Wired lookup-or-compute-and-publish inside `joinable_corpus_counts`
  (`app/research/micro_join.py:586-656`), which currently sums
  `enumerate_band_touches(meta, dataset_store, resolver)` over every record with NO caching
  (`micro_join.py:639-641`) — this is the ~22s-and-growing uncached per-dataset
  `DatasetStore.load_events` cost the iter-25 evaluator measured against the real store (also
  backs the `desk_micro_readiness` MCP tool's ~13.5s warm / ~13min cold timing). Publishes ONLY a
  resolved count, never a placeholder; a corrupted/unreadable cache DB is a full miss, never a
  crash (mirror the existing self-heal contract). `GET /research/desk/micro/readiness` and the
  `desk_micro_readiness` MCP proxy keep serving byte-identical values — only warm-path latency
  changes. New cache needs its OWN env var in the `TAPEOLOGY_MICRO_*` family (existing sibling
  caches each get their own — e.g. `TAPEOLOGY_MICRO_READINESS_CACHE_DB`; do not reuse that one).
  Callers that pass no cache (every existing pre-iteration call site/test) must keep today's
  behavior byte-identical (uncached compute) — treat the new cache param as optional, defaulted,
  the same shape as `resolver=None` already works in `joinable_corpus_counts`.

- **Selector-table dedup** (closes "duplicated pilot-selector table"): `micro_routes.py:284-287`
  currently hand-restates `scout._PILOT_GRID_SELECTORS`
  (`app/research/scout.py:1684-1689`, a `dict[str, tuple[study_id, kind]]`) as two separate
  hand-written frozensets, `_BAND_TOUCH_PILOT_SELECTORS` (`kind == "band_touch"`) and
  `_PLAYBOOK_SIGNAL_PILOT_SELECTORS` (`kind == "playbook_signal"`). Replace both with a
  filter-derivation over `scout._PILOT_GRID_SELECTORS` so there is exactly ONE canonical
  selector→kind source. **Design constraint from TC-6(b):** the derivation must be a genuine
  runtime computation from the source dict, not a frozen-at-import constant that only happens to
  equal today's values — TC-6(b) monkeypatches a LOCAL COPY of `scout._PILOT_GRID_SELECTORS`
  with a synthetic third `kind="band_touch"` entry and expects the route-level frozenset to grow
  to include it. Write this as a small derivation function callable with an explicit source dict
  (defaulting to `scout._PILOT_GRID_SELECTORS` for the real route path), not a bare module-level
  literal computed once at import.

- **Test-harness scope only, no app-code change:** confirm the deterministic replay lane drives
  all nine stored `journey-scripts/*.json` files in one recorded run this iteration (J-01, J-02,
  J-03, J-04, J-05, J-06, J-08, J-09, J-10 — J-07 has no golden by design). The iteration spec's
  own metadata already widens `Required-still-passing` to the full remaining seven-golden set
  (`docs/phases/goal-rapid-microscope-iter-26.md` line 13), so this should already be honored by
  the pipeline's existing replay-lane logic without a code change; verify
  `reports/phase-goal-rapid-microscope-iter-26-regression-replay-results.md` shows 9/9 PASS rows
  including a PASS for `J-06.json`'s own Validation Vault assertion (TC-1) — do not treat this as
  a dev deliverable requiring new source files.

## Out of scope (per phase spec — do not build)

- Referee disclosure + guard for `strategy_trade_readiness`'s stale count (deferred, owner-safe
  per iter-25 evaluator's own "drop 4 and 5, never 1" ordering).
- Chain-ledger identity-commitment gap, sealed judge's `econ_floor` — both owner-owned.
- No real tape recording, no sealed-shard exposure/assignment, no running J-09 on the real
  corpus.
- No change to any `referee_*.py` module (byte-freeze) and no change to
  `micro_readiness.py`'s served response SHAPE — the cache is a purely internal layer.
- No `Config` field, no fingerprint movement, no `blueprint.md` edit (no new displayed value, no
  new page).

## Agents Required

- backend-data: yes -- implement the band-touch SQLite cache (`micro_readiness.py`/`micro_join.py`
  wiring) and the selector-derivation dedup in `micro_routes.py`, plus their co-located unit
  tests (cache cold/warm/invalidation/corruption; selector equality + genuine-derivation +
  source-scan guard). All work is Python backend; no frontend code changes this iteration.
- frontend-ux: no -- zero frontend files change (goal.md/phase-spec both confirm: served values
  and rendered UI are byte-unchanged; only warm-path latency of an existing endpoint changes).

## Frontend Present: yes

Note on this line: the phase spec's own Goal Mode Metadata header says "Frontend Present: no"
(that field classifies whether FRONTEND CODE changes this iteration — it does not). But the
Definition of Done and Testing Requirements explicitly mandate fresh browser-qa-agent evidence
for both Target journeys: TC-7 (J-01 "Microscope Readiness" section, element screenshot, values
byte-identical pre/post-cache) and TC-8 (J-08 "Scout Ledger" section, element screenshot,
pilot-study rows and `variants_tried` unchanged pre/post-dedup). This line is set to `yes`
specifically so qa-phase.sh runs the Chrome MCP browser checks needed to produce that evidence —
setting it to `no` would risk TC-7/TC-8 going unverified. No new UI surface, no new user action;
this is a regression-proof browser pass, not a feature browser pass.

## Files to Create/Modify

- `apps/backend/app/research/micro_readiness.py` -- new durable SQLite cache class for band-touch
  counts (mirrors `MicroReadinessCache` at :226-289; own env var, own table, self-heal-on-corrupt
  contract) and/or its resolution-path helper; `build_readiness` gains a way to pass it through
  to `joinable_corpus_counts` (optional param, default preserves today's uncached behavior).
- `apps/backend/app/research/micro_join.py` -- `joinable_corpus_counts` (:586-656) does
  lookup-or-compute-and-publish per dataset record via the new cache before/instead of calling
  `enumerate_band_touches` (:517-568) unconditionally; keys on
  `(dataset_meta["checksum"], resolver.map_key(symbol, window_start_epoch))` per record.
- `apps/backend/app/research/micro_routes.py` -- (a) construct the new cache as a FastAPI
  dependency (mirror `get_micro_readiness_cache` pattern just above `@router.get("/readiness")`)
  and thread it into `build_readiness(...)` in `get_micro_readiness`; (b) replace the
  hand-written `_BAND_TOUCH_PILOT_SELECTORS`/`_PLAYBOOK_SIGNAL_PILOT_SELECTORS` literals (:284-287)
  with a derivation over `scout._PILOT_GRID_SELECTORS` (needs a new import of that name from
  `.scout`, alongside the existing `GRID_SELECTOR_*` imports at the top of the file).
- `apps/backend/tests/test_micro_readiness.py` -- co-locate new cache cold/warm/invalidation/
  corruption tests beside the existing `MicroReadinessCache` tests (:243-260-ish, see
  `test_cache_lookup_is_none_on_a_genuine_miss` / `test_cache_publish_then_lookup_round_trips` /
  `test_cache_survives_a_corrupted_db_file_as_a_full_miss` for the pattern to mirror) — TC-2,
  TC-3, TC-4, TC-5.
- `apps/backend/tests/test_micro_join.py` -- extend the existing `joinable_corpus_counts`
  coverage (many call sites already at :513-970) to exercise the cache-wired path: a
  `DatasetStore.load_events` call-count spy proving a warm second call skips re-reading events
  (TC-3), and a re-warmed-map-key genuine-miss test (TC-4).
- `apps/backend/tests/test_scout.py` (or a new `apps/backend/tests/test_micro_routes.py` if the
  developer judges the route-level derivation logic doesn't belong in `test_scout.py` — no
  existing `test_micro_routes.py` file exists today; `test_scout.py` already imports symbols from
  `micro_routes.py`, e.g. `get_scout_compute_manager`, `get_scout_ledger_dir` at its top, and is
  today's closest precedent for route-level micro_routes coverage) -- new selector-derivation
  equality test (`{RANGE_WALL_PILOT, DELTA_DIVERGENCE_PILOT}` /
  `{CAPITULATION_PILOT}`), the genuine-derivation test (extend a LOCAL copy of
  `scout._PILOT_GRID_SELECTORS` with a synthetic `kind="band_touch"` entry, observe growth), and
  a source-scan/grep guard confirming `micro_routes.py` has no second hand-written selector→kind
  literal — TC-6.
- `docs/handoffs/goal-rapid-microscope-iter-26-dev.md` -- dev handoff documenting the cache's
  composite-key design, the selector-derivation change, and (briefly) that the
  Required-still-passing widening was a harness/spec change already carried by the iteration
  metadata, not new app code (TC-10).

## UI Evolution

None — no new user-facing capability, no new information displayed, no new user actions, no UI
surface changes, no navigation changes. This section is browser-regression-only; see the "Frontend
Present" note above.

## Visual Requirements

N/A — no rendering, styling, or layout change of any kind. The browser pass exists solely to
prove the existing "Microscope Readiness" and "Scout Ledger" `/desk` sections render
byte-identical values after the cache/dedup change (TC-7, TC-8). No new component patterns, no
new states to handle.

## Key Test Scenarios

- TC-1: deterministic replay lane runs all 9 stored goldens in one recorded run; 9/9 PASS
  including `J-06.json`'s Validation Vault "Sealed at" assertion (harness/spec-level, not new
  app code — verify the regression-replay-results report, don't rebuild the harness).
- TC-2/TC-3/TC-4/TC-5: new band-touch cache — first-hit computes and stores exactly one row
  keyed on `(checksum, map_key)`; warm second call skips `DatasetStore.load_events` (call-count
  spy) and returns the unchanged count; a genuinely new `map_key` (re-warmed band map) is a
  fresh miss, never a stale serve; a corrupted/unreadable cache DB degrades to a full miss and
  HTTP 200 with a freshly computed value, never a 500.
- TC-6: `_BAND_TOUCH_PILOT_SELECTORS`/`_PLAYBOOK_SIGNAL_PILOT_SELECTORS` equal today's known sets;
  a synthetic third entry added to a LOCAL copy of `scout._PILOT_GRID_SELECTORS` is reflected in
  the derived frozenset (proves genuine derivation); a grep/source-scan guard confirms no second
  hand-written selector→kind literal remains in `micro_routes.py`.
- TC-7: browser-qa-agent screenshot of `/desk` Microscope Readiness section — totals/per-shard/
  floors byte-identical to J-01's registered pre-iteration values.
- TC-8: browser-qa-agent screenshot of `/desk` Scout Ledger section — pilot-study family rows and
  `variants_tried` line unchanged from pre-iteration render.
- TC-9: reviewer/auditor re-hash all six `referee_*.py` modules against the iteration-0 SHA-256
  listing (byte-identical) and diff the `GET /research/desk/micro/readiness` response schema
  (unchanged — the cache is purely internal).
- Full backend suite green, zero regressions, `Config().config_fingerprint()` still
  `08e471b10130e1e2`.
- Lesson-driven check (iter-21): the new cache class must be reachable from `app/` (its real
  call site inside `joinable_corpus_counts`/the readiness route), not only from its own unit
  test — `grep -rn <new_cache_class_name> app/ tests/` should show at least one hit under `app/`
  beyond its own definition file.
