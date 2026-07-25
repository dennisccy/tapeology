# goal-desk-iter-1 Execution Plan

Context: Era B "The Desk" (`docs/goal.md`), iteration 1, session `desk`, target journey **J-01
only**, depth **full**. Builds on the post-"Clean Slate" two-page product (Cockpit `/` +
`/structure`, pin `08e471b10130e1e2`, 15 MCP tools, suite 1169 pass/7 skip — all confirmed live at
iter-0 baseline with zero code diff). This iteration adds a backend-only, currently
UI-invisible universe subsystem that unblocks J-02–J-06; nothing on screen changes yet.

## What to Build

- **Universe vendor seam** — fetches the Wikipedia S&P 100 constituents page over HTTP via the
  already-pinned `httpx>=0.27` client; swappable via a `dependency_overrides` seam mirroring
  `get_bar_fetch_adapter`/`FakeAdapter` (`app/research/routes.py:471-496`) so tests inject fixture
  HTML with zero network calls.
- **Stdlib-only parser contract** — `html.parser.HTMLParser` (or targeted string/regex
  extraction) over the constituents table. **No `lxml`/`html5lib`/`beautifulsoup4`/
  `pandas.read_html()`** — none are declared dependencies (`bs4` is only yfinance's undeclared
  transitive import; importing it would itself be a dependency-drift violation). Validates ticker
  charset `[A-Z.-]{1,6}`, member count in `[90, 110]`, normalizes `BRK.B→BRK-B` / `BF.B→BF-B`
  (raw form retained in metadata), dedupes, sorts. Any validation failure raises a specific,
  honest error — never a partial or guessed list.
- **Three Path-A Config fields** — `desk_universe_source_url`, `desk_universe_min_members`
  (default `90`), `desk_universe_max_members` (default `110`), plus a storage-dir field/resolver
  if the store needs one (`TAPEOLOGY_*_DIR` env-override pattern, `dataset_dir_resolved`/
  `bar_dir_resolved` at `app/config.py:1298-1310`). Each field, **same commit**: exclusion-set
  entry with rationale comment (`app/config.py:1312` exclusion set — re-locate by grep, currently
  ends around `dataset_dir`/`bar_dir`/`bar_timeframes` entries), stability test, counter-test,
  and embedding of the value used-at-registration into the served payload (provenance duty).
- **Universe store** — one frozen JSON file per snapshot at
  `apps/backend/.data/universe/universe-<YYYY-MM-DD>-<checksum12>.json`, content-checksummed,
  structurally immutable (no update/delete function anywhere), mirroring `BarStore`
  (`app/research/bars.py:210`, `BarSeriesAlreadyRegistered`) / `DatasetStore`
  (`app/research/datasets.py:221`, `DatasetAlreadyRegistered`). Re-registering byte-identical
  content is a no-op/refusal, never a rewrite. Directory-scan listing is sufficient — no derived
  SQLite index needed this iteration (J-02 needs one; J-01 doesn't).
- **Two new routes under `/research`** — `POST /research/desk/universe/fetch` (operator act: fetch
  → parse → validate → register; honest 4xx naming the specific validation failure; 409-style
  refusal naming the existing snapshot on duplicate content) and `GET /research/desk/universe`
  (snapshot list + latest membership; explicit HTTP 200 empty payload before any registration —
  never 404).
- **Fixtures** under `apps/backend/tests/fixtures/universe/` (new dir, mirrors `bars/`/
  `datasets/`/`yahoo/`): valid constituents HTML (90–110 tickers, ≥1 dual-class ticker),
  corrupted variant (bad charset and/or out-of-bounds count), and the registered snapshot JSON
  produced by running the real registration path against the valid fixture once — this becomes
  "the fixture universe" J-02–J-05 will reference by that exact phrase.
- **Hermetic test wiring** — env-scoped universe directory (`TAPEOLOGY_DATASET_DIR`/
  `TAPEOLOGY_BAR_DIR` env-override pattern) so tests never touch the real `.data/universe/`.
- **Unit + route tests** covering the parser contract, store immutability, both routes' four
  states, Path-A stability/counter-tests, and a T-3 grep-based guard proving the universe module
  never imports `datasets.py`'s registration surface or `DatasetStore`.
- **One `@pytest.mark.integration` live-Wikipedia test** (network-enabled, outside the default
  suite) — run at least once this iteration; report the outcome honestly (success + member count,
  or the specific failure reason) in the dev handoff.
- **Pre/post kept-route baseline diff** — sha256 every existing `/research`, `/tape`, `/meta` GET
  response before and after the change; zero deltas expected (TC-11 / J-07 backend subset).

## Agents Required

- developer: yes -- implement the vendor seam, parser, Path-A Config fields, universe store,
  the two new routes, fixtures, hermetic test wiring, unit/route/integration tests, and the
  kept-route baseline diff described above. Single agent — this iteration is backend-only.
- backend-data: yes -- all of the above (vendor seam, parser, store, Config fields, routes,
  fixtures, tests).
- frontend-ux: no -- zero frontend files touched this iteration (no `/desk` page, no nav change,
  no `structure/page.tsx` edit). `/desk` ships in J-04; the `/structure` prefill ships in J-05.

## Frontend Present
no

## Files to Create/Modify

- `apps/backend/app/research/desk_universe.py` (new) -- vendor seam + stdlib HTML parser +
  validation/normalization + `UniverseStore` (frozen JSON, checksum, append-only), mirroring
  `bars.py`/`datasets.py`.
- `apps/backend/app/research/desk_routes.py` (new, preferred given `routes.py` is already ~74KB)
  -- `POST /research/desk/universe/fetch` + `GET /research/desk/universe` handlers; alternative is
  adding directly to `app/research/routes.py` (`router = APIRouter(prefix="/research", ...)` at
  :82) if the developer judges a new module unwarranted -- build discretion either way, but if a
  new module is created it must be mounted in `app/main.py` (`app.include_router(...)`, alongside
  the existing `research_router`/`meta_router` includes at :197/:201).
- `apps/backend/app/config.py` -- add the three `desk_universe_*` fields (+ optional storage-dir
  field/resolver), each in the `config_fingerprint()` exclusion set at :1312 with a rationale
  comment following the `dataset_dir`/`bar_dir` precedent.
- `apps/backend/app/main.py` -- mount the new desk router, only if `desk_routes.py` is created as
  a separate module.
- `apps/backend/tests/fixtures/universe/` (new dir) -- valid constituents HTML, corrupted HTML,
  registered snapshot JSON.
- `apps/backend/tests/test_desk_universe.py` (new) -- parser contract, store
  immutability/no-op-on-duplicate, Path-A stability + counter-tests, T-3 store-separation guard
  (naming mirrors `test_bars.py`/`test_datasets.py`).
- `apps/backend/tests/test_desk_universe_api.py` (new) -- both routes' four states (empty /
  registered / corrupted-input / duplicate-input), the `@pytest.mark.integration` live-Wikipedia
  test (naming mirrors `test_bars_api.py`/`test_datasets_api.py`).
- `docs/handoffs/goal-desk-iter-1-dev.md` (new) -- dev handoff, including the honest TC-14 live
  Wikipedia fetch outcome and the kept-route baseline diff result.

## Out of Scope (explicitly excluded this iteration)

- J-02 (coverage/top-up), J-03 (screen + ledger), J-04 (`/desk` page), J-05 (history +
  `/structure` prefill), J-06 (MCP `desk_universe`/`desk_screen` tools) -- all deferred to later
  iterations per `docs/goal.md`'s stated dependency order.
- Any change to `app/meta.py` `UI_ROUTES`, `NavBar.tsx`, or any frontend file.
- Any change to `tradability.py`, `levels.py`, `bar_index.py` schema, or
  `EdgeReportComputeManager` -- J-01's fetch is a single synchronous call, needs no compute
  manager.
- Any new runtime dependency (no `lxml`, `beautifulsoup4`, `html5lib`, `pandas.read_html()`).
- Writing universe data through `research/datasets.py`, or registering a screen as a dataset.
- A CLI wrapper for the universe fetch (not required until J-02/J-03).
- Any change to the fingerprint pin `08e471b10130e1e2` or its 13 existing assertion sites --
  Path A only.
- Re-shooting iter-0's kept-product browser-walk screenshots (already DONE, binding
  "do not redo" in `runs/goal-session-desk/state/iteration-state.md`).
- Fixing `journey-scripts/J-07.json` step 8's async-text assertion or warming the
  `/research/setups` scan cache -- carried forward to the next browser-QA iteration (expected
  around J-04); not actionable here since `Frontend Present: no` means no browser QA dispatches.

## Key Test Scenarios

- Empty state: fresh test-scoped universe dir, `GET /research/desk/universe` → HTTP 200, empty
  payload (no snapshots, no latest) -- never 404.
- Valid registration: fixture HTML (90–110 tickers, ≥1 dual-class) via injected fake vendor,
  `POST /research/desk/universe/fetch` → registers, returns 12-char checksum, member count in
  [90,110], normalized+sorted list (`BRK.B`→`BRK-B`, raw form preserved, no duplicates).
  `GET /research/desk/universe` then lists it and returns it as `latest`.
- Corrupted input: charset-violating ticker or out-of-bounds count → explicit 4xx naming the
  specific failure; store unchanged (no new snapshot); no partial/guessed registration.
- Duplicate content: re-fetching identical already-registered content → 409-style refusal naming
  the existing snapshot; on-disk file byte-unchanged (no rewrite).
- T-3 guard: grep/import check proves `desk_universe.py` never imports `research/datasets.py`'s
  registration surface or `DatasetStore` -- zero hits.
- Path-A fingerprint: `Config().config_fingerprint()` unchanged at `08e471b10130e1e2` after adding
  the three new fields (stability test); a counter-test (e.g. `desk_universe_min_members` raised
  above the fixture's actual count) proves the field live-wires into the NEW path's output while
  the fingerprint stays unaffected; the snapshot payload embeds the exact three field values used
  at registration (provenance).
- Kept-route regression (J-07 backend subset / TC-11): every existing `/research`, `/tape`,
  `/meta` GET response sha256-identical before vs. after this iteration's diff.
- Full suite: at least 1169 passed, exactly 7 skipped, 0 failed after the change; default
  (non-`integration`) run performs zero network calls.
- Integration (manual/`@pytest.mark.integration`, run at least once, outcome reported honestly in
  the dev handoff): a real fetch against the live Wikipedia constituents page.
