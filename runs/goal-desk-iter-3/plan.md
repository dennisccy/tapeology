# goal-desk-iter-3 Execution Plan

Context: Era B "The Desk" (`docs/goal.md`), iteration 3, session `desk`, target journey **J-03
only**, depth **full** (a brand-new persisted append-only data kind — the screen-snapshot store —
plus a second compute manager spanning `tradability.py`/`bar_index.py`/`desk_coverage.py`/
`datasets.py`). Required-still-passing: **J-01** (`GET /research/desk/universe`, unperturbed),
**J-02** (`GET /research/desk/coverage` + top-up compute, reused verbatim), **J-07**'s backend/
keyless subset (suite floor, fingerprint pin; no browser pass, `Frontend Present: no`). Builds
directly on iter-1's `desk_universe.py`/`UniverseStore` discipline and iter-2's compute-manager
precedent (`desk_topup_compute.py`) and its dedicated-endpoint precedent (`desk_routes.py`) —
both confirmed live in the current tree. iter-2's audit explicitly recommended proceeding to J-03
next; this spec carries forward its recommendations verbatim (T-6 as-of-never-`now()`, per-
`(symbol,timeframe)` coverage truth, bar-store-signature via index-only reads). No scope creep
against `docs/goal.md` found: every IN SCOPE item traces to Key Capability 3 / J-03's steps, and
OUT OF SCOPE correctly fences off J-04–J-06, the frozen research owners, and the fingerprint pin.
This iteration is backend/CLI-only — `/desk` does not exist until J-04, so nothing on screen
changes.

Environment note for the developer/reviewer/QA steps that follow: this pipeline run isolates temp
files — export `TMPDIR`/`TMP`/`TEMP` to
`/home/dennis-chan/.cache/iad/iad.goal-desk-iter-3.14200` before running pytest or any
temp-file-writing command.

## What to Build

- **`desk_screen.py`** (new): a `ScreenStore` mirroring `desk_universe.UniverseStore`'s discipline
  exactly (checksum-verified load on every read, `record()` the only mutation, refuses/returns-
  the-existing-snapshot on an identical 5-pin key `(screen_date, as_of, universe_snapshot_id,
  config_fingerprint, bar_store_signature)`, no update/delete function anywhere) plus the row-
  computation function.
- **Row computation**: walk the LATEST universe snapshot's members through `compute_tradability`
  (`tradability.py:381`, byte-for-byte reuse — confirmed signature
  `compute_tradability(store: BarStore, symbol: str, as_of_epoch: float, config: Config) -> dict`),
  `desk_coverage.get_desk_coverage` (verbatim reuse for the coverage badge), and
  `DatasetStore.list()` (`datasets.py:353`, presence-only, for the tick-evidence badge).
- **Best-band selection + `distance_bps`** (per `assumptions.md` iter-3 entry 1): apply
  `(class rank A=3/B=2/C=1/null=0 desc, distance_bps asc, quality_score desc)` twice — first
  WITHIN a symbol's own band list to pick its "best" band, then ACROSS symbols (+`symbol asc`) for
  the final row order.
- **Reference close price** (`assumptions.md` iter-3 entry 2, TC-19): resolve via
  `BarStore.merged_bars(symbol, "1d")` (confirmed: the exact accessor `tradability.py`'s own
  `_select_daily_series` calls internally) and read the ONE bar dated at `basis_as_of`
  (`compute_tradability` already returns this) — never re-deriving which bar is the basis, never
  touching `tradability.py`'s or `levels.py`'s return shape. `git diff` on both must stay empty.
- **`bar_store_signature`** (T-4, TC-15): a checksum over sorted `(symbol, timeframe,
  latest_window_end_utc)` tuples sourced entirely from `desk_coverage.get_desk_coverage`'s own
  reads — zero `BarStore.list`/`.get` calls, instrumented and asserted.
- **Screen dir resolution — zero new `Config` field**: a bare module-level function mirroring
  `resolve_cache_db_path(dataset_dir_resolved: str)` (`edge_report_cache.py:188` — confirmed:
  checks `os.environ.get(...)` first, else a sibling path derived from the CALLER's own already-
  resolved dir string; never imports `config.py`'s singleton). `desk_screen.py`'s version takes
  `CONFIG.desk_universe_dir_resolved()`'s return value as a plain string and checks
  `TAPEOLOGY_DESK_SCREEN_DIR` first, else a sibling `.data/screen/` dir. Do **not** touch
  `config.py` — no new field, no exclusion-set entry.
- **Compute manager** (new module `desk_screen_compute.py`, or folded into `desk_screen.py` —
  developer's call): mirrors `EdgeReportComputeManager` (`edge_report_compute.py:108` — confirmed
  shape: no-arg `__init__`, `threading.Lock` + `threading.Event`, `snapshot()` returns a deep,
  caller-safe copy, `trigger()` takes all deps per-call and returns `{"started": bool, "compute":
  <snapshot>}` unchanged if already running, background worker thread, stale-job-guarded publish).
  Triggered per a REQUIRED `screen_date`; an identical-pin trigger over an already-recorded
  snapshot returns it without recomputing or rewriting.
- **Placement — see "Notes / Known Traps" below: use a module-singleton-behind-a-FastAPI-
  dependency, the `desk_topup_compute.py` pattern, NOT a `ResearchRegistry` property.** This
  resolves a real tension in the spec's own NOTES vs. its OUT OF SCOPE section.
- **Extend `desk_routes.py`** (same file, same already-mounted router — no `main.py` change
  needed) with `GET /research/desk/screen` (latest + `?date=` + lightweight snapshot list — meta
  only, never full `rows`/`skipped` in the list), `POST /research/desk/screen/compute` (422 if
  `screen_date` missing), `GET /research/desk/screen/compute` (poll), `POST
  /research/desk/screen/compute/cancel` (409 when idle) — mirrors the existing `/topup/compute*`
  trio exactly (confirmed live at `desk_routes.py:163-200`).
- **CLI warmer** (e.g. `python -m app.research.desk_screen_compute`, mirrors
  `desk_topup_compute.py`'s `main()`): REQUIRED `--date`, never defaults to today's wall-clock
  date; exits non-zero on a missing arg.
- **Tests**: the store (append-only refusal, checksum verification, corrupt-file honesty — the
  `UniverseIntegrityError` precedent), the row computation (rank order, both skip reasons
  `"no_bars"`/`"no_basis"`, byte-for-byte cross-check vs `GET /research/tradability` on the REAL
  committed AAPL fixture), the compute manager (single-flight, cancel, GET-never-computes,
  identical-pin no-rewrite), the routes (honest-empty `{"screens": [], "latest": null}`, `?date=`,
  422 on missing `screen_date`), the CLI (`--date` required). See the fixture-gap note below
  before assuming any AMD/MSFT bar fixture already exists.

## Agents Required

- developer: yes -- implement `desk_screen.py` (store + row computation + best-band selection +
  reference-close resolution + bar-store-signature + dir resolver), the compute manager, the four
  new `desk_routes.py` endpoints, the CLI warmer, the new MSFT partial-coverage bar fixture, and
  all unit/integration tests described above. Single agent — this iteration is backend-only.
- backend-data: yes -- all of the above (new append-only store, compute manager, routes, CLI,
  fixtures, tests).
- frontend-ux: no -- zero frontend files touched this iteration. No `/desk` page, no
  `structure/page.tsx` edit, no `UI_ROUTES` change. `blueprint.md`'s Feature/journey-homes table
  states J-03 is "backend POST/CLI compute; served to `/desk`" with no standalone page — J-04's
  job.

## Frontend Present
no

## Files to Create/Modify

- `apps/backend/app/research/desk_screen.py` (new) -- `ScreenStore`, the row-computation function,
  best-band selection, reference-close resolution, `bar_store_signature`, the screen-dir resolver.
- `apps/backend/app/research/desk_screen_compute.py` (new, or folded into `desk_screen.py`) -- the
  compute-manager class, the per-member work function, the CLI `main()`.
- `apps/backend/app/research/desk_routes.py` -- add the four `/research/desk/screen*` handlers
  (imports from the two files above); existing `fetch_universe`/`get_universe`/`get_coverage`/
  `trigger_desk_topup_compute`/etc. handler bodies must stay byte-unchanged.
- `apps/backend/tests/test_desk_screen.py` (new) -- store discipline, row computation, best-band
  selection, skip reasons, `bar_store_signature` index-only instrumentation, byte-for-byte
  cross-check vs `GET /research/tradability` on the real AAPL fixture.
- `apps/backend/tests/test_desk_screen_compute.py` (new) -- single-flight, cancel, GET-never-
  computes, identical-pin no-rewrite, CLI `--date` required/rejection.
- `apps/backend/tests/fixtures/` -- **new**: a committed MSFT bar-fixture pair covering exactly
  `1h`+`1d` (never `4h`/`1w`) for TC-2, mirroring either the PG pattern (`tests/fixtures/bars/`,
  `BarStore`-record-format, seeded by copying into a temp bar dir — `test_levels_api.py:120-145`)
  or the AAPL raw-capture pattern (`tests/fixtures/yahoo/*.json`, loaded via `_load_yahoo_fixture`
  then `BarStore.record()` — `test_tradability.py:464-492`). Reuse the existing committed AAPL
  fixture for TC-1/TC-19 (already used by `test_tradability.py`'s pinned 2026-06-22 golden — do
  NOT create a second one). No AMD bar fixture is required (see fixture-gap note below).
- No changes to: `config.py`, `main.py`, `meta.py`, `mcp/__init__.py`, `tradability.py`,
  `levels.py`, `bars.py`, `bar_index.py`, `desk_universe.py`, `desk_coverage.py`,
  `desk_topup_compute.py` — all reused verbatim; `git diff` on each must be empty (TC-16, TC-17,
  TC-19 all key off this).
- `docs/handoffs/goal-desk-iter-3-dev.md` (new) -- dev handoff.

## Out of Scope (mirrors the phase spec's OUT OF SCOPE verbatim)

- J-04 (`/desk` page), J-05 (history + `/structure` drill-in), J-06 (MCP v3) -- later iterations;
  J-06 is unbuildable until this one ships.
- A `desk_screen_dir` `Config` field -- explicitly rejected; use the bare env-var/sibling resolver.
- Any change to `tradability.py`, `levels.py`, `bars.py`'s/`bar_index.py`'s existing methods,
  `desk_universe.py`, `desk_coverage.py`, `routes.py`, `config.py`, `main.py`, `meta.py`,
  `mcp/__init__.py` -- zero diff expected on every one of these (a hard DoD/TC-19 requirement, not
  just a preference -- see the placement note below).
- A real ~100-symbol screen over real bar data -- an explicit future operator-run act; this
  iteration ships the capability, verified keyless against the committed fixtures.
- The optional `UniverseStore.latest()` DRY cleanup (iter-2 audit B3) -- still optional.
- Repaying `desk_topup_compute.py`'s carried-forward test-net debt (CLI `main()` tests, populated
  route-level coverage assertion, composite cancel/resume test) -- carried forward again.
- Warming `_config_content_hash`-stranded caches, re-pointing `J-07.json` step 8 -- both deferred
  to whichever iteration runs J-04's browser pass (no new `Config` field this iteration either, so
  the stranding does not worsen).

## Notes / Known Traps for the Developer

- **Compute-manager placement is more constrained than the spec's NOTES section suggests.** The
  NOTES section says "either placement is acceptable" (module-singleton vs. a `ResearchRegistry`
  property, the `EdgeReportComputeManager` precedent) — but the DoD and OUT OF SCOPE both require
  **zero diff on `routes.py`**, and `ResearchRegistry` (the class that would own the property)
  lives IN `routes.py` (confirmed: `class ResearchRegistry` at `routes.py:152`, `__init__` already
  constructs `self._edge_report_compute = EdgeReportComputeManager()` there). Adding a screen-
  compute property necessarily edits that file. Use the `desk_topup_compute.py` pattern instead
  (confirmed live at `desk_routes.py:54,155-160`): a module-level singleton constructed at import
  time, exposed only through a `get_desk_screen_compute_manager()` FastAPI dependency, fully
  test-overridable via `app.dependency_overrides`. `desk_screen_compute.py` needs nothing from
  `routes.py` anyway (no `record_bar_series` reuse, unlike the top-up), so there is no functional
  reason to prefer the registry — only the zero-diff constraint needs stating explicitly so no
  effort is spent on the registry path and then reverted.
- **No committed AMD or MSFT bar fixture exists today** — searched thoroughly
  (`grep -rliE "\bAMD\b|\bMSFT\b"` across `tests/`, filename search, `test_mcp_server.py` in full):
  zero hits. The phase spec's TESTING REQUIREMENTS prose ("the real AAPL/AMD/MSFT bar fixtures
  already used by `test_tradability.py`/`test_mcp_server.py`") overstates what's committed —
  `test_tradability.py`'s only real committed bar-fixture golden is **AAPL** (`tests/fixtures/
  yahoo/AAPL_*.json`, TC-1/TC-19's basis). AAPL/AMD/MSFT bars DO exist, but only in the operator's
  ambient `apps/backend/.data/bars/` (gitignored, era-open production state, not available on a
  fresh checkout or in CI) — never read that dir from a test (the iter-1/iter-2 established rule).
  **TC-2 needs a NEW committed MSFT fixture** shaped `1h`+`1d` present, `4h`+`1w` absent (mirror
  the PG or AAPL fixture-creation pattern above). **No TC literally requires AMD bars** — TC-13's
  AMD reference is a `DatasetStore` tick-evidence presence check only (dataset registration, not
  bars), satisfiable with a lightweight synthetic `DatasetStore.record()` stub per symbol name (all
  11 symbols) in a temp store — no real tick-data fixture needed for any of them.
- Tests must use their OWN temp-scoped universe/bar/screen dirs (the
  `TAPEOLOGY_DESK_UNIVERSE_DIR`/`TAPEOLOGY_BAR_DIR`/`TAPEOLOGY_DESK_SCREEN_DIR` env-override
  pattern) — never the ambient real `.data/` tree.
- Suite floor is 1240 passed / 8 skipped non-decreasing (iter-2's own floor); pin
  `08e471b10130e1e2` must print unchanged before AND after (TC-16).
- The DoD's "J-01, J-02, J-07 remain green ... kept-route byte-identity" line has no dedicated TC
  number this iteration (iter-1/iter-2 had TC-11/TC-13 for this) — low risk since `desk_screen*`
  are pure additions and `desk_routes.py`'s existing handler bodies are untouched, but re-running
  the iter-2 24-template kept-route capture (`runs/goal-desk-iter-2/kept-route-*-24.txt`'s method)
  against a populated dir is still worth doing to substantiate the claim in the dev handoff.
- `GET /research/tradability` is confirmed live at `routes.py:935-936`
  (`get_tradability(symbol, as_of, store)`) — TC-1's cross-check target.

## Key Test Scenarios

- TC-1/TC-19: AAPL screen row on the pinned 2026-06-22 session is byte-identical to
  `GET /research/tradability?symbol=AAPL&as_of=<derived>` for the selected "best" band; the
  reference close is the real fixture bar's own recorded close at `basis_as_of`; `git diff` on
  `tradability.py`/`levels.py` is empty.
- TC-2: MSFT (real symbol, new fixture: `1h`/`1d` only) resolves a ranked row, never mis-skipped
  for partial coverage; its `coverage` field is honest per-timeframe.
- TC-3/TC-11: zero-bar members → `skipped: "no_bars"`; a daily series with no resolvable session →
  `skipped: "no_basis"` (distinct, never conflated); skip-row `coverage` still honest.
- TC-4/TC-10: identical `screen_date`+pins re-triggered → same snapshot `id`, no second file, no
  recompute; two fresh-process row computations are byte-identical (no wall-clock/randomness).
- TC-5/TC-6: no screen ever computed → `GET /research/desk/screen` returns 200
  `{"screens": [], "latest": null}`; `?date=D` returns the exact persisted snapshot verbatim, never
  recomputed on GET.
- TC-7/TC-8/TC-9: concurrent trigger while running → `started: false`, same job; cancel mid-flight
  → `"cancelled"` with fewer than `members_total` done; idle cancel → 409; empty-body trigger →
  422, never defaults to today.
- TC-12: every row/skip's `coverage` is byte-identical to `desk_coverage.get_desk_coverage`'s own
  per-member block for the same universe snapshot (proving reuse).
- TC-13: the 11 named dataset-store symbols → `tick_evidence: true`; every other member → `false`.
- TC-14: `rows` sorted by `(band_class rank A>B>C>null desc, distance_bps asc, band_score desc,
  symbol asc)`.
- TC-15: `bar_store_signature` derivation issues zero `BarStore.list`/`.get` calls (instrumented).
- TC-16/TC-17: `Config().config_fingerprint()` unchanged at `08e471b10130e1e2`; full suite ≥1240
  passed / ≥8 skipped / 0 failed; every guard test (`test_no_execution_path.py`,
  `test_no_credential_in_artifacts.py`, the 13 fingerprint pin assertions) passes byte-unmodified.
- TC-18: CLI with no `--date` → non-zero exit, explicit usage error; `--date 2026-06-22` against a
  scoped test dir → completes, prints a ranked/skipped summary count.
