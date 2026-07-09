# goal-yahoo_fetch-iter-3 Execution Plan

## Alignment check

J-03 ("Quick reuse — store-first fetch backed by a derived SQLite index") is next in the goal's
stated dependency chain `J-01 → J-02 → J-03 → J-04 → J-05`. J-01 (keyless Yahoo fetch) and J-02
(multi-timeframe + honest `4h` resample) are both done (audited PASS_WITH_GAPS, only a
non-blocking browser-evidence gap carried forward to J-05). No drift found between the phase spec
and `docs/goal.md`'s J-03 text — schema keys, `reindex()` semantics, the store-first coordinator
placement, and the additive filter all match verbatim. No scope creep to flag.

## What to Build

- A derived SQLite index (`apps/backend/app/research/bar_index.py`) mirroring `research/store.py`'s
  discipline (stdlib `sqlite3`, WAL, `busy_timeout`, hermetic dependency-injected DB path — the
  writer-thread-queue machinery in `store.py` is there for high-frequency verdict writes and is
  NOT required here; a direct connection is fine for this low-frequency metadata cache). Schema
  keyed by `(symbol, timeframe, window_start_utc, window_end_utc)` → `series_id`, `checksum`,
  `bar_count`. Stores metadata only; owns nothing.
- `reindex()` — drop + repopulate entirely from `BarStore.list()`'s **healthy** `records` (skip
  anything reported in that call's `errors` list — a corrupt file is not legitimately indexable
  data). Deleting the DB file and calling `reindex()` must reproduce identical lookups.
- A store-first coordinator inside `record_bar_series` (`research/routes.py`): index lookup
  **before** any adapter is touched; on a hit, return the stored series (checksum-verified via the
  existing `BarStore.get`) with **zero** adapter/network calls; on a miss, the existing fetch flow
  runs unchanged, then additively inserts into the index after `store.record` succeeds.
- Additive `?symbol=&timeframe=` filter on `GET /research/bars` (`list_bar_series`), served via the
  index; the no-param call stays **byte-identical** (still `store.list()` verbatim).
- A new `get_bar_index` DI provider (mirrors `get_bar_store`) at a config-derived, env-overridable
  path — **not** a new `Config` field, so `config.py` stays byte-identical (the preferred path the
  spec itself calls out; only fall back to a fingerprint-excluded field if the co-located path
  proves genuinely infeasible).
- Tests proving: no `fetch_bars` call on a cache hit, `reindex()` fidelity, the filter/no-param
  byte-identity, and `config_fingerprint` unchanged.

## Agents Required

- backend-data: yes -- implement `bar_index.py`, the store-first coordinator + additive filter in
  `research/routes.py`, the `get_bar_index` DI provider, and all associated tests (index unit
  tests, route-level store-first + filter tests, `reindex()` test, fingerprint-stability check).
- frontend-ux: no -- J-03 is backend-only (`Frontend Present: no` per the goal-mode metadata block
  and the phase spec's own IN SCOPE / TESTING REQUIREMENTS sections). The `/structure` fetch
  control is J-05; do not touch `apps/frontend/**` this iteration.

## Frontend Present
no

## Files to Create/Modify

- `apps/backend/app/research/bar_index.py` — NEW. `BarIndex` class constructed with an explicit DB
  path (hermetic/DI'd, like `BarStore`/`JournalStore`). Methods: `lookup(symbol, timeframe,
  window_start_utc, window_end_utc) -> hit | None` — match on the **raw ISO window strings**
  exactly as `BarStore.record` stores them (`body.start`/`body.end` verbatim, not parsed epochs —
  two epoch-equal-but-textually-different strings must NOT collide); `insert(...)` (called
  additively after a successful `store.record`, using values from the returned `meta` dict, not
  re-derived from the request body); `list(symbol=None, timeframe=None)` for the GET filter;
  `reindex()` as described above.
- `apps/backend/app/research/routes.py` — MODIFY.
  - New `get_bar_index()` DI provider mirroring `get_bar_store()` (~line 1537), overridable via
    `dependency_overrides` in tests exactly like `get_bar_store` is today.
  - `record_bar_series` (~line 1561): insert the index lookup **after** the existing 422
    validation block (ends ~line 1601) and **before** `adapter = get_bar_fetch_adapter()` (~line
    1603) — a cache hit must skip adapter resolution, `is_available()`, and `fetch_bars` entirely,
    not just skip the network call. On a hit, return `{"bar_series": store.get(hit.series_id)}`.
    **Move the `symbol = body.symbol.strip().upper()` normalization (currently at line 1616, done
    late) earlier so the lookup key matches exactly what later gets stored** — an unnormalized
    lookup key would silently never hit. On a miss, flow is unchanged through `store.record(...)`
    (~line 1643); add the additive `index.insert(...)` call right after that succeeds, before
    `return {"bar_series": meta}` (~line 1655).
  - `list_bar_series` (~line 1658): add optional `symbol`/`timeframe` query params served via the
    index; when both are absent, keep calling `store.list()` exactly as today — add a test that
    diffs the no-param response before/after to prove byte-identity.
- `apps/backend/tests/test_bar_index.py` — NEW. Insert-on-record; exact-key lookup hit/miss;
  `reindex()` rebuild from `BarStore.list()` reproduces identical lookups after the DB file is
  deleted; a missing/corrupt DB self-heals via `reindex()` without fabricating or losing a lookup.
- `apps/backend/tests/test_bars_api.py` — MODIFY (extend, do not weaken the 15 existing tests).
  - Store-first idempotence: two identical `POST /research/bars` calls; assert
    `adapter.fetch_bars_calls` (already exists on `FakeAdapter`, `tests/fakes.py:159` — no new fake
    needed) has exactly one entry after both calls, and the second response matches the first's
    `id`/`checksum`.
  - `?symbol=&timeframe=` filter test (returns only the matching series).
  - No-param `GET /research/bars` byte-identity assertion.
- `apps/backend/tests/test_bars.py` (or `test_config.py`) — MODIFY **only if** a `Config` field
  ends up added (fallback path): a fingerprint-stability test mirroring
  `test_bar_dir_is_excluded_from_config_fingerprint` (`test_bars.py:221`). Prefer skipping this
  file entirely by keeping `config.py` at zero diff.
- `docs/handoffs/goal-yahoo_fetch-iter-3-dev.md` — NEW. Dev handoff (DoD requirement).

## Out of Scope (explicitly excluded, per the phase spec's own boundaries)

- Any `apps/frontend/**` change, any `/structure` UI work — J-05.
- Overlap/subsumption caching (serving a sub-window from a larger stored window) — exact-tuple
  match only, a smarter cache is unrequested scope.
- Any background/ambient re-indexing or polling — the index updates only additively on an explicit
  store-first fetch.
- Any modification to `BarStore.record`, `research/bars.py`, `research/levels.py`,
  `research/strategies.py`, `research/backtests.py`, the tape engine, or the Alpaca adapter.
- The stale `README.md:72` sentence — a readme-maintainer concern, not this iteration's code.

## Key Test Scenarios

- First `POST /research/bars` stores + indexes; an identical second `POST` invokes the adapter's
  `fetch_bars` **zero** times and returns the stored series (store-first idempotence).
- `GET /research/bars?symbol=<S>&timeframe=<T>` returns only the matching series; no-param `GET
  /research/bars` is byte-identical to pre-iteration behavior.
- Deleting the index DB file and calling `reindex()` reproduces identical lookups.
- `config_fingerprint()` still equals `4d665603569b9dbf` regardless of which path (zero-diff or
  fingerprint-exclusion fallback) was taken.
- Edge case worth deliberate handling (not explicitly specced — flag for dev/QA judgment): an index
  entry pointing at a `series_id` the JSON store can no longer verify (deleted/corrupted file after
  indexing) must never fabricate or silently return partial data — treat it as a miss (fall through
  to a real fetch) or surface an explicit error, either is acceptable, silence is not.
- Full backend suite stays green with zero regressions (baseline from iter-2: 1189 collected / 1183
  passed / 6 skipped, 0 failed); engine equivalence suites stay 22/22 (J-06 guard).
- No browser/Chrome MCP checks required this iteration (`Frontend Present: no`); J-03's acceptance
  is index unit tests + the keyless store-first test per `docs/goal.md`.
