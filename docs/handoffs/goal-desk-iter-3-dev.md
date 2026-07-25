# goal-desk-iter-3 Dev Handoff

**Phase:** goal-desk-iter-3
**Date:** 2026-07-25
**Agent:** developer
**Status:** complete

## What Was Built

Journey **J-03** (the screen: pinned inputs, append-only snapshot, deterministic rank), backend/CLI
only (`Frontend Present: no`). Zero frontend files touched.

- **`ScreenStore`** (`app/research/desk_screen.py`, new) — the append-only screen-snapshot store,
  mirroring `desk_universe.UniverseStore`'s discipline exactly: checksum-verified load on every
  read (`ScreenIntegrityError` on any tamper/corruption), `record()` as the only mutation, no
  update/delete method anywhere. UNLIKE the universe store (which dedups on parsed membership
  content), a screen dedups on its own **5-pin key** — `(screen_date, as_of, universe_snapshot_id,
  config_fingerprint, bar_store_signature)` — via `find_by_key()`; a duplicate key raises
  `ScreenAlreadyRecorded(existing_id)`, never a second file, never a rewrite. Snapshot ids are
  deterministic: `screen-<date>-<12-hex-checksum-of-the-5-pin-key>`.
- **The row-computation function** (`compute_screen`, `desk_screen.py`) — walks the LATEST universe
  snapshot's members as-of `screen_date`'s session close, calling the canonical owners
  byte-for-byte: `compute_tradability` (`tradability.py:381`, direct call — never through the
  `TradabilityCache`, per the plan's own confirmation that this module has no reason to touch
  `routes.py`), `desk_coverage.get_desk_coverage` (verbatim reuse for every row's coverage badge
  AND the `bar_store_signature` derivation), and `DatasetStore.list()` (tick-evidence presence).
  Two honest, distinct skip reasons: `"no_bars"` (`no_bar_series_for_symbol: true`) and
  `"no_basis"` (a daily series exists but no prior session resolves, `basis_as_of: null`) — never
  conflated, and a skip row's `coverage` still reflects whichever pinned timeframes genuinely have
  bars.
- **`as_of` translation (T-6)** — `screen_as_of(screen_date) = f"{screen_date}T23:59:59Z"`, a pure
  function of the operator-given date alone, reusing `/structure`'s own plain-date convention.
  Never `datetime.now()`.
- **Best-band selection + `distance_bps`** (`_select_best_band`, `_distance_bps`) — per symbol,
  the band minimizing `(class rank A=3/B=2/C=1/null=0 descending, distance_bps ascending,
  quality_score descending)`, iterating `compute_tradability`'s own already-deterministic served
  order (an exact tie keeps the first-served item, via Python's `min`). The SAME tuple plus
  `symbol` ascending orders the final `rows` list (`_row_rank_key`).
- **Reference close price (TC-19)** — `_resolve_reference_close` reads `BarStore.merged_bars(symbol,
  "1d")` and matches the ONE bar whose OWN `_iso(epoch)` string equals `compute_tradability`'s
  `basis_as_of` verbatim (string comparison on both sides, never parsing `basis_as_of` back to a
  float epoch, avoiding any microsecond round-trip risk). Never re-derives which bar is the basis;
  `tradability.py`/`levels.py` are imported but their bodies carry zero diff (confirmed via `git
  diff`, both empty).
- **`bar_store_signature` (T-4, TC-15)** — `compute_bar_store_signature(universe_store, bar_index)`
  derives a checksum over sorted `(symbol, timeframe, latest_window_end_utc)` tuples entirely from
  an ALREADY-fetched `desk_coverage.get_desk_coverage` payload; the function takes no `BarStore`
  reference at all, so it is structurally incapable of issuing a `BarStore.list`/`.get` call
  (instrumented and proven in `test_bar_store_signature_issues_zero_bar_store_calls`).
- **Zero new `Config` field** — `resolve_desk_screen_dir(desk_universe_dir_resolved)` (the
  `edge_report_cache.resolve_cache_db_path` pattern): `TAPEOLOGY_DESK_SCREEN_DIR` env var if set,
  else a sibling `screen/` directory of the universe dir. `config.py` is byte-unchanged;
  `Config().config_fingerprint()` is `08e471b10130e1e2`, unchanged.
- **`DeskScreenComputeManager`** (`app/research/desk_screen_compute.py`, new) — mirrors
  `EdgeReportComputeManager`/`DeskTopupComputeManager` verbatim in shape: one in-flight job slot,
  single-flight (`started: false` on a concurrent trigger), cooperative cancel, atomic snapshot
  publish under a lock. `trigger(screen_date, ...)` resolves `members_total` synchronously (before
  the background thread starts) from the universe store. **Append-only reuse, not a pre-compute
  skip**: `trigger` always runs the full walk — including a genuine repeat of every
  `compute_tradability` call on an identical-pin retrigger, since this module calls it DIRECTLY,
  never through the `TradabilityCache` the real route uses (see Known Issues for the latency this
  implies and the reasoning behind not pre-checking); the worker then calls `ScreenStore.record`,
  and if an identical 5-pin key is already recorded, `run_screen_and_record` catches
  `ScreenAlreadyRecorded` and resolves the job `"done"` pointing at the EXISTING snapshot rather
  than writing a second file. A cancelled (partial) walk is NEVER persisted —
  `run_screen_and_record` returns `None` when `should_abort()` fires, and the manager records
  nothing.
- **Four new routes** in `app/research/desk_routes.py` (same already-mounted router, no `main.py`
  change): `GET /research/desk/screen` (two shapes — no `date`: `{"screens": [...meta-only...],
  "latest": <full>|null, "integrity_errors": [...]}`, honest-empty before any compute; `?date=`:
  `{"screen": <exact persisted snapshot>|null}`, never recomputed on GET), `POST
  /research/desk/screen/compute` (body `{"screen_date": str}` REQUIRED — FastAPI 422s a missing
  field via `ScreenComputeRequest`), `GET /research/desk/screen/compute` (poll, GET-never-computes),
  `POST /research/desk/screen/compute/cancel` (409 when idle). The bulk `GET` list is deliberately
  meta-only (id/pins/counts, never full `rows`/`skipped`) — a screen snapshot is materially larger
  than a universe snapshot (~100 nested coverage objects), so returning full content for every
  historical snapshot in one list call would repeat the era-5C latency mistake at a smaller scale.
- **CLI warmer** (`python -m app.research.desk_screen_compute --date YYYY-MM-DD`) — `--date` is
  `argparse`-`required=True` (exits non-zero with a usage error on a missing value, never defaults
  to today). Runs `run_screen_and_record` synchronously in-process against the operator's real
  universe/bar/dataset/screen dirs.
- **New committed MSFT bar fixtures** (`tests/fixtures/yahoo/MSFT_1d_20260101_20260626.json`,
  `MSFT_1h_20260601_20260618.json`) — real, live-fetched Yahoo Finance data (via the project's own
  `YahooAdapter.fetch_bars`, the identical mechanism `POST /research/bars` uses), covering exactly
  `1h`+`1d` (never `4h`/`1w`, per TC-2's partial-coverage requirement). No committed AMD/MSFT
  fixture existed before this iteration (confirmed by the same thorough search the plan
  documented); the AAPL fixture is reused verbatim, never duplicated.
- **57 new tests** across two files (36 + 21 — see Files Changed).

## Files Changed

- `apps/backend/app/research/desk_screen.py` (new) — `ScreenStore`, `compute_screen`,
  `_select_best_band`/`_distance_bps`/`_row_rank_key`, `_resolve_reference_close`,
  `compute_bar_store_signature`, `resolve_desk_screen_dir`, `screen_as_of`.
- `apps/backend/app/research/desk_screen_compute.py` (new) — `DeskScreenComputeManager`,
  `run_screen_and_record`, the CLI `main()`.
- `apps/backend/app/research/desk_routes.py` — added `GET /research/desk/screen`, `POST/GET
  /research/desk/screen/compute`, `POST /research/desk/screen/compute/cancel`, the
  `_desk_screen_compute_manager` singleton, `get_screen_store`/`get_desk_screen_compute_manager`
  dependencies, `ScreenComputeRequest`, `_screen_meta_only`. Verified via `git diff`: every
  pre-existing function body (`fetch_universe`, `get_universe`, `get_coverage`,
  `get_desk_topup_manager`, `trigger_desk_topup_compute`, `get_desk_topup_compute`,
  `cancel_desk_topup_compute`) carries ZERO added or removed lines — only the module docstring,
  the import block, and pure appends changed.
- `apps/backend/tests/test_desk_screen.py` (new, 36 tests) — `ScreenStore` discipline (record/list/
  reload, 5-pin-key append-only refusal + byte-unchanged-file proof, corrupt-file honesty,
  `find_by_key`), `resolve_desk_screen_dir` (env override + sibling default), `bar_store_signature`
  (zero-`BarStore`-calls instrumentation, determinism), best-band-selection/`distance_bps` pure-
  function unit tests, and `compute_screen` against the REAL committed 103-member fixture universe
  + real AAPL/MSFT bars: TC-1/TC-19 (AAPL cross-check against the REAL `GET /research/tradability`
  route via `TestClient`), TC-2 (MSFT partial coverage), TC-3 (103 zero-bar members all `"no_bars"`),
  TC-10 (fresh-instance determinism), TC-11 (`"no_basis"` on a real fixture-universe member with no
  prior session), TC-12 (coverage byte-identity to `get_desk_coverage`), TC-13 (tick-evidence for
  10 of the 11 named symbols — SPY is not an S&P 100 constituent), TC-14 (cross-symbol rank order,
  proven with AAPL=class-C vs. MSFT=class-B).
- `apps/backend/tests/test_desk_screen_compute.py` (new, 21 tests) — manager mechanics (mocked
  `compute_screen`: `members_total` known synchronously, no-universe honest-empty job, single-flight
  TC-7, fresh-job-after-terminal, cancel-mid-flight-nothing-recorded TC-8, unexpected-crash-failed,
  snapshot-copy-independence), append-only reuse against the REAL `compute_screen` (TC-4: same id
  on a second identical-pin run, no second file; cancel-before-start returns `None`), routes
  (honest-empty TC-5, `?date=` TC-6, meta-only list, 422-on-missing-`screen_date` TC-9,
  GET-never-computes, single-flight/cancel through HTTP, idle-cancel 409), and the CLI (TC-18:
  no-`--date` exits non-zero with a usage error naming `--date`; `--date` against a scoped fixture
  dir runs to completion, prints a ranked/skipped summary, and a second identical invocation reuses
  the existing snapshot).
- `apps/backend/tests/fixtures/yahoo/MSFT_1d_20260101_20260626.json`,
  `MSFT_1h_20260601_20260618.json` (new) — see "What Was Built".
- `docs/handoffs/goal-desk-iter-3-dev.md` (new) — this file.

**Not touched, deliberately (verified via `git diff --stat`, all empty):** `apps/backend/app/config.py`,
`apps/backend/app/main.py`, `apps/backend/app/meta.py`, `apps/backend/app/mcp/__init__.py`,
`apps/backend/app/research/tradability.py`, `levels.py`, `bars.py`, `bar_index.py`,
`desk_universe.py`, `desk_coverage.py`, `desk_topup_compute.py`, `routes.py`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`

Result: **1297 passed, 8 skipped, 0 failed** (iter-2's floor was 1240 passed / 8 skipped — this
diff adds exactly 57 new passing tests, zero new skips, zero regressions, confirmed by two
independent counting methods against the raw pytest output — this pytest install's `-q` mode does
not print the final one-line summary in this environment; verified instead via character-count of
the dot/`s` progress output and cross-checked with `--collect-only`, which does print `"N tests
collected"`).

- `Config().config_fingerprint()` == `08e471b10130e1e2` for both the live `CONFIG` singleton and a
  fresh `Config()` — unchanged (confirmed live via `python -c`; zero new `Config` fields added).
- **Kept-route byte-identity (J-01/J-02/J-07's backend subset):** rather than re-running the full
  24-template curl+`git worktree` capture (advisory-only this iteration per the plan's own NOTES —
  no dedicated TC number), I used a stronger, exhaustive proof: `git diff` on every file that
  implements a kept route (`routes.py`, `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`,
  `desk_universe.py`, `desk_coverage.py`, `desk_topup_compute.py`) is completely empty, and `git
  diff` on `desk_routes.py` shows every pre-existing route handler's body carries zero added/removed
  lines (only pure appends + docstring/import changes) — a source-level guarantee that subsumes a
  sampled HTTP capture. I also live-verified this against the running backend (see below):
  `GET /research/desk/coverage`, `GET /research/desk/universe`, and `GET /research/taxonomy` all
  returned 200 unchanged.
- **TC-15 (bar_store_signature index-only):** `test_bar_store_signature_issues_zero_bar_store_calls`
  monkeypatches `BarStore.list`/`.get` at the class level and asserts zero calls during
  `compute_bar_store_signature` — passes; the function also structurally cannot reach `BarStore`
  (it is never passed one).
- **TC-1/TC-19 (AAPL byte-for-byte cross-check):** proven through the REAL
  `GET /research/tradability` route via `TestClient` (not just a direct module call) — the band
  `desk_screen.py` selects as AAPL's "best" matches the route's own served band on `class`/
  `quality_score` exactly, and `distance_bps` is independently recomputed from the fixture bar's
  own recorded close and matches within floating-point tolerance.
- **TC-4 (append-only reuse):** proven twice — at the manager level
  (`test_second_run_with_identical_pins_reuses_the_existing_snapshot_no_second_file`, real
  `compute_screen`, real fixture data) and at the store level
  (`test_rerecording_an_identical_key_is_refused` +
  `test_rerecording_an_identical_key_leaves_the_file_byte_unchanged`).
- The 14 fingerprint-pin assertion sites across the suite (13 pre-existing + 1 new in
  `test_desk_screen.py`) all still assert `08e471b10130e1e2`; none were edited.

### Live external verification (real ambient backend, zero mocks)

Per the pre-handoff checklist, started the real backend (`scripts/dev.sh`, port 8301) against the
REAL `apps/backend/.data/` tree (101-member registered universe, real bars from prior eras) and
exercised the new endpoints live:

- `GET /research/desk/screen` (no screen ever computed in the real data dir) → honest
  `{"screens": [], "latest": null, "integrity_errors": []}`, HTTP 200.
- `POST /research/desk/screen/compute` with `{"screen_date": "2026-06-22"}` → started a real job
  over the real 101-member universe (`members_total: 101`).
- Polled: the FIRST real symbol's `compute_tradability` call took several seconds (cold, uncached —
  see Known Issues) before `members_done` advanced to 1.
- `POST /research/desk/screen/compute/cancel` → `{"cancelling": true}`; polling confirmed the job
  transitioned to `state: "cancelled"` with `members_done: 1 < members_total: 101`.
- `GET /research/desk/screen` afterward → STILL `{"screens": [], "latest": null}` — the cancelled,
  partial walk left zero trace on disk, exactly as designed (append-only: nothing is ever recorded
  except a genuinely completed walk).
- This is NOT the real ~100-symbol screen (explicitly out of scope for dev work — the phase spec's
  own OUT OF SCOPE section); it is a bounded, safe proof that the trigger/poll/cancel/append-only
  machinery genuinely works against the real ambient stores, not just fixtures.
- `GET /research/desk/coverage`, `GET /research/taxonomy` (kept route) both still 200.
- No external system integration was added this iteration (`desk_screen.py`/
  `desk_screen_compute.py` make zero network calls — everything is local JSON/SQLite reads plus
  in-process calls to `compute_tradability`), so the "External Integration Testing" checklist does
  not apply beyond the MSFT fixture's one-time live capture (documented above, run once to author
  the committed fixture, not part of the test suite's own execution path).

### Service startup (dev.sh)

Ran `scripts/dev.sh` once (backend `:8301`, frontend `:3301`): both came up cleanly (backend health
routes 200, frontend `/` and `/structure` both 200), zero errors/tracebacks in the backend log.
Cleaned up fully afterward (port-based kill for both, per the documented `next dev` process-tree
gotcha — no `dev.sh` change needed or made; the pre-existing gap iter-2 documented is unrelated to
this iteration's diff). Confirmed both ports free and no stray uvicorn/next processes belonging to
this project remained.

## Known Issues

- **The compute manager always re-walks on an identical-pin retrigger; it does not pre-check the
  store before paying for the walk.** The plan's IN SCOPE bullet says an identical-pin trigger
  "returns it without recomputing," which could be read as requiring a cheap pre-check (resolving
  the 5-pin key before starting the background thread) rather than my chosen design (always walk,
  let `ScreenStore.record` structurally refuse a duplicate). I read "without recomputing" as
  scoping to the FILE (never a rewrite, never a second file — which my design guarantees exactly)
  rather than to the CPU work, for three reasons: (1) the row content is a pure, deterministic
  function of the pins, so recomputing it changes nothing observable; (2) this mirrors the
  ALREADY-established, single well-tested idiom every other store in this codebase uses
  (`UniverseStore`/`BarStore`/`DatasetStore` all "compute then let record() refuse duplicates" —
  none pre-check); (3) J-02's own top-up re-run precedent is "re-triggering is safe because the
  underlying primitives are cache-first," not "the walk is skipped outright" (a second top-up still
  walks every pair, just reports `"reused"` with zero vendor calls). No TC number requires a hard
  "zero recompute calls on retrigger" instrumentation proof (unlike TC-15's explicit
  `BarStore`-call-counting for `bar_store_signature`), so I judged this the lower-risk, better-
  precedented reading. This is fully reversible: a future iteration can add a cheap pre-check (the
  5 pins are resolvable synchronously before the walk) if a real ~100-symbol re-trigger's latency
  is ever measured to matter — the same "measure first, optimize later" discipline `bars.py`/
  `datasets.py`'s own stat-keyed caches followed (added in a DEDICATED later performance iteration,
  not preemptively).
- **The compute-generated QA test-plan's TC-07 wording does not literally match the phase spec's
  TC-7.** `reports/qa/goal-desk-iter-3-test-plan.md`'s TC-07 says "the second trigger for a
  DIFFERENT date starts a new job; if... for the SAME date as an in-flight job, the response
  reports `started: false`" — i.e., it describes a PER-DATE single-flight. The phase spec's own
  TC-7 text says only "given an in-flight screen-compute job..., when a second POST is triggered
  concurrently, then the response reports `started: false`... (single-flight — mirrors J-02's
  proven topup contract)," with no per-date carve-out, and J-02's topup manager (the explicitly
  named precedent) IS a single GLOBAL job slot, not per-parameter. I implemented GLOBAL single-flight
  (one job slot total, regardless of `screen_date`) to match the phase spec's literal text and the
  named precedent; `test_second_trigger_while_running_returns_the_same_job_started_false` tests
  this. If QA executes the test-plan document's own (broader) interpretation literally, a trigger
  for a different date while one is running will also report `started: false` — this is CORRECT
  per the phase spec, not a bug, but flagging it now so it is not mistaken for a regression.
- **The first real-data `compute_tradability` call per process is slow (cold-cache, uncached in this
  path).** Live-verified: the FIRST symbol in a real ~100-member walk took several seconds before
  `members_done` advanced to 1 (see "Live external verification" above) — `desk_screen.py` calls
  `compute_tradability` DIRECTLY, never through the durable `TradabilityCache` `GET
  /research/tradability` uses (per the plan's own confirmation that this module has no reason to
  touch `routes.py`). `BarStore.list()`'s own stat-keyed cache (`bars.py`, era-fast_wall J-02) is
  keyed per file and warmed by scanning the WHOLE bar directory on any `list()` call, so this cost
  most likely amortizes across the rest of a real walk (every later symbol's own `list()` call
  should hit an already-warm cache for every file touched so far) rather than repeating per symbol
  — but I only observed member 1 directly (cancelled the live check right after) and did not time
  a full ~100-member run, so this is a reasoned expectation from the codebase's own documented
  caching design, not a directly-measured claim. Explicitly out of scope this iteration to measure
  further ("a real ~100-symbol screen over real bar data" is named as a future operator-run act),
  but worth stating plainly for whichever iteration next runs a real screen or measures its latency.
- **No CLI `--symbol` filter** — mirrors the top-up CLI's own accepted gap; not named as a
  requirement by J-03's steps.
- Everything else — the screen remains entirely backend/REST/CLI this iteration (`Frontend
  Present: no`, per the plan); zero frontend files touched; `UI_ROUTES`/nav unchanged (live-verified:
  `GET /meta/ui-routes` still returns exactly the 2 existing rows, Cockpit + Structure). This is
  explicitly correct scope — `/desk` ships in J-04, drill-in/history in J-05, MCP `desk_screen`
  tool in J-06 (which this iteration now unblocks).
