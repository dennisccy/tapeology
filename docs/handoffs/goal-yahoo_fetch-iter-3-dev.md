# goal-yahoo_fetch-iter-3 Dev Handoff

**Phase:** goal-yahoo_fetch-iter-3
**Date:** 2026-07-09
**Agent:** developer
**Status:** complete

## What Was Built

- **`BarIndex`** (`apps/backend/app/research/bar_index.py`, NEW) — a derived, rebuildable SQLite
  index over the canonical JSON `BarStore`. Stdlib `sqlite3` + WAL + `busy_timeout`, a hermetic
  dependency-injected DB path, no writer-thread-queue (a direct synchronous connection, per the
  plan's explicit "low-frequency metadata cache" call). Schema: one table `bar_index`, primary key
  `(symbol, timeframe, window_start_utc, window_end_utc)` -> `series_id, checksum, bar_count`.
  Methods: `lookup(...)` (exact-key, raw ISO strings, returns a `BarIndexHit` dataclass or `None`),
  `insert(meta)` (idempotent `INSERT OR REPLACE`, takes the `BarStore.record`-returned meta dict
  verbatim), `list(symbol=None, timeframe=None)` (independently combinable filters), `reindex(store)`
  (drop + repopulate from `store.list()`'s healthy `records`, skipping anything in that call's
  `errors`), and a `db_path` property for introspection/tests.
- **Store-first coordinator** in `record_bar_series` (`POST /research/bars`, `routes.py`): the
  `symbol = body.symbol.strip().upper()` normalization was moved earlier (right after the existing
  422 validation block) so the index lookup key matches exactly what a successful fetch later
  stores. An index hit returns the stored series via `store.get()` (checksum-verified) with **zero**
  adapter/network calls. A hit whose series the JSON store can no longer verify (deleted/corrupted
  since indexing) is treated as a miss — falls through to a real fetch, which additively overwrites
  the stale index row once it succeeds (self-heal; never fabricates or serves partial data). On a
  genuine miss, the existing fetch flow is unchanged; `index.insert(meta)` runs once
  `store.record(...)` succeeds, before the response is returned.
- **Additive `?symbol=&timeframe=` filter** on `GET /research/bars` (`list_bar_series`): both
  params optional and independently combinable, served via `BarIndex.list()` + `store.get()` per
  hit (checksum-verified). `symbol` is normalized (stripped + uppercased) so the filter is
  case-insensitive. With **neither** param present, the route is byte-identical to before — still
  `store.list()` verbatim, index never consulted on that path (proven by a dedicated test that
  diffs the route's response against a direct `store.list()` call).
- **`get_bar_index` DI provider** (`routes.py`, mirrors `get_bar_store`): resolves the index DB path
  from `TAPEOLOGY_BAR_INDEX_DB` if set, else a file co-located as a sibling of the config-owned bar
  directory (`bar_dir_resolved()`'s parent + `bar_index.db`, e.g. `.data/bars` -> `.data/bar_index.db`).
  **`config.py` has a zero diff** — no new `Config` field, no fingerprint-exclusion test needed;
  `config_fingerprint()` verified unchanged (`4d665603569b9dbf`, same as iter-2).

## Files Changed

- `apps/backend/app/research/bar_index.py` -- NEW. The `BarIndex` class (see above).
- `apps/backend/app/research/routes.py` -- MODIFIED. `get_bar_index()` DI provider added after
  `get_bar_store()`; `record_bar_series` gets the store-first coordinator + moved normalization +
  additive `index.insert(meta)`; `list_bar_series` gets the optional `symbol`/`timeframe` filter.
  `config.py`, `bars.py`, `store.py`, `levels.py`, `strategies.py`, `backtests.py`, the tape engine,
  and the Alpaca adapter were **not touched**.
- `apps/backend/tests/test_bar_index.py` -- NEW. 10 tests: exact-key lookup hit/miss (including a
  dedicated test proving two epoch-equal-but-textually-different ISO strings do NOT collide),
  insert-is-idempotent-and-overwrites, the symbol/timeframe filter, `reindex()` populating from
  `BarStore.list()`, `reindex()` skipping a corrupt file reported in `errors`, `reindex()` dropping a
  stale entry not reproduced by the current store (drop+repopulate, not an additive merge), and
  `reindex()` after deleting the DB file reproducing identical lookups.
- `apps/backend/tests/test_bars_api.py` -- MODIFIED (extended; the module docstring was updated to
  reflect the new store-first behavior).
  - `test_duplicate_content_is_refused_409` was **transformed** into
    `test_duplicate_window_post_is_served_store_first_no_second_fetch` — see "Changed test" note
    below.
  - Added `test_store_first_hit_pointing_at_a_corrupted_series_self_heals_via_a_refetch` (the
    plan's flagged edge case).
  - Added `test_symbol_and_timeframe_filter_returns_only_the_matching_series`.
  - Added `test_no_param_get_is_byte_identical_to_a_direct_store_list_call`.
  - Added `test_get_bar_index_resolves_to_a_sibling_of_the_bar_dir_by_default` (direct resolver
    proof, mirroring the existing `get_bar_fetch_adapter` resolver test).
  - All 12 pre-existing tests below the `# --- era-5 J-01/J-02` marker, plus the other originally
    passing tests, are otherwise unmodified and still pass.
- `docs/handoffs/goal-yahoo_fetch-iter-3-dev.md` -- NEW (this file).

## Changed test: why `test_duplicate_content_is_refused_409` could not stay as-is

The phase spec's own NOTES section said a repo grep found "no route-level test asserting 409 on a
duplicate-window `POST /research/bars`" — that grep missed one: `test_duplicate_content_is_refused_409`
posted the identical body twice and asserted the second call was a 409. J-03's entire point (stated
repeatedly in `docs/goal.md` and the phase spec's BACKGROUND) is to end exactly that "an identical
repeat POST re-hits Yahoo, then gets refused" behavior and replace it with "an identical repeat POST
is served from storage" — so that specific test's assertion became the literal behavior J-03 removes.
I transformed it in place (same two-POST shape, new assertions: 200/200, matching id+checksum, and
`fetch_bars_calls` length 1) rather than deleting it, and it now directly satisfies the plan's own
"store-first idempotence" test requirement — so no separate test needed to be added for that
scenario. The FROZEN store-level content-duplicate refusal (a **different** window whose fetched
content happens to match) is untouched — `store.record` was not modified — and stays covered by
`tests/test_bars.py::test_rerecording_identical_content_is_refused`, which still passes unmodified.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q --junit-xml=<path>`
Result: **1203 collected, 1203 passed (0 failed, 0 errors), 6 skipped** — the iter-2 baseline
(1189 collected / 1183 passed / 6 skipped / 0 failed) plus this iteration's 14 new tests (10 in
`test_bar_index.py`, 4 net-new in `test_bars_api.py`), zero regressions.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py tests/test_profile_equivalence.py -v`
Result: **22 passed** (J-06's "engine equivalence 22/22" guard).

Command: `cd apps/backend && .venv/bin/python -c "from app.config import CONFIG; print(CONFIG.config_fingerprint())"`
Result: `4d665603569b9dbf` (unchanged — `config.py` has a zero diff this iteration).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_bar_index.py tests/test_bars_api.py tests/test_bars.py -v`
Result: **48 passed** (fast targeted subset, run first for quick feedback before the full suite).

### Live verification against the real running app (not just tests)

J-03 adds no new external integration (no new adapter, no new vendor call) — the plan's own Testing
Requirements say a new live Yahoo test is not required this iteration, and the keyless `FakeAdapter`
+ committed fixture path is the specified acceptance route. I additionally ran the real app
(`bash scripts/dev.sh`, backend on `:8301`) against the **actual pre-existing production data** in
`apps/backend/.data/bars/` (8 real bar series recorded live in iter-1/iter-2, including real AAPL/MSFT
candles) to prove the feature end-to-end, not only against test fixtures:

- `POST /research/bars` with the exact body of an already-stored AAPL/1d series returned the
  identical `id` in **19ms**, with the backend process never touching the network (store-first hit
  on real data).
- `GET /research/bars` (no params) still returned all 8 real series with `integrity_errors: []`,
  byte-identical to before.
- `GET /research/bars?symbol=AAPL&timeframe=1d` initially returned an **empty** list against this
  pre-existing data (expected — see Known Issues below), then correctly returned the matching real
  series once I ran a one-off `BarIndex(...).reindex(store)` against the same live `.data/` directory
  the running server was using — proving `reindex()` and the filter both work correctly against real
  data, and that WAL-mode SQLite correctly hands off between a separate reindexing process and the
  live server process reading the same DB file.
- Restarted `scripts/dev.sh` (stop, then start again): both backend (`:8301`) and frontend (`:3301`,
  zero code changes but confirmed it still boots since the phase's checklist asks for both) came up
  cleanly on the same ports with no conflicts.
- All server processes (uvicorn, `next dev`, and — see Known Issues — the descendant `next-server`
  process the top-level PID capture misses) were killed before finishing this handoff; `lsof -ti
  :8301 :3301` and a process grep both confirm nothing tapeology-related is left running.

## Known Issues

- **Pre-existing bar series recorded before this iteration are not automatically indexed.** The
  index only updates additively on an explicit store-first `POST` (by design — "any
  background/ambient re-indexing or polling" is explicitly out of scope per the plan). The 8 real
  bar series already in `apps/backend/.data/bars/` from iter-1/iter-2 verification were invisible to
  the new `?symbol=&timeframe=` filter until I manually ran `BarIndex(...).reindex(store)` once (a
  three-line Python one-liner — see the live verification section above for the exact command). This
  is not a defect in scope for J-03 (no reindex-trigger endpoint or CLI was requested by the plan or
  DoD), but an operator upgrading a real deployment should run a one-time `reindex()` so
  already-stored data becomes filterable; I have left the real `.data/bar_index.db` in a
  freshly-reindexed, correct state as part of this verification, so nothing further is needed for
  the current environment.
- **`scripts/dev.sh` does not reliably kill the full frontend process tree on the SAME invocation's
  own `FRONTEND_PID` capture.** This is a pre-existing gap in that script (unrelated to this
  iteration's code — I did not modify `scripts/dev.sh`), but I hit it directly while verifying
  service startup: `next dev` spawns through `npm exec` -> `sh -c` -> `node .../next` -> a
  `next-server` child, and the script's `FRONTEND_PID=$!` only captures the outer subshell, so a
  `kill $FRONTEND_PID` (what the script's own Ctrl+C trap does) can leave the `next-server` process
  bound to the port. I did not fix this (out of scope — no frontend files were touched this
  iteration), but flagging it since a future iteration's QA/dev cycle could see a stale port
  occupied by an orphaned `next-server` from a prior run that only used the script's own Ctrl+C.
- **No admin/CLI surface for `reindex()`.** As scoped, `reindex()` is a library method exercised by
  tests and manual recovery, not a route or CLI command. If an operator's index DB is ever lost or
  corrupted in production, recovery is the same one-off Python snippet demonstrated in the live
  verification section above.
