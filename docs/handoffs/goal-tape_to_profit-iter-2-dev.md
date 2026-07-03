# goal-tape_to_profit-iter-2 Dev Handoff

**Phase:** goal-tape_to_profit-iter-2
**Date:** 03-07-2026
**Agent:** developer
**Status:** complete

## What Was Built

Target journey **J-02** — the historical tape dataset store with the frozen train/hold-out
registry — plus the iter-1 evaluator's must-fix (Playwright for the harness replay lane).

- **Config knob** — `dataset_dir` in `app/config.py` with the `TAPEOLOGY_DATASET_DIR` env
  override (`dataset_dir_resolved()`, mirroring the `TAPEOLOGY_JOURNAL_DB` pattern). Default is
  package-anchored `apps/backend/.data/datasets/` (covered by the existing `.data/` gitignore
  entry). **Excluded from `config_fingerprint`** with the `journal_db_path` rationale (a storage
  location touches no persisted research value; the absolute default would otherwise mint a
  per-machine fingerprint) — pinned by a fingerprint-stability test + the real-threshold
  counter-test.
- **Dataset store module** — new `app/research/datasets.py`, the ONE reader/writer of dataset
  files (Data Contract row 30). One JSON file per dataset holding provider-neutral
  TradeEvent/QuoteEvent rows (never vendor payloads) + metadata: id, symbol, UTC window,
  `data_feed` (via the one `feed_basis` mapping), event counts, content checksum, immutable
  split tag, source descriptor/kind/id, epoch anchor, created timestamp.
- **Record/register** — `record_from_source(...)`: an explicit research action resolving the
  source exactly like studies (`reference` = the committed keyless PG SIP fixture via studies'
  one loader, optionally sliced to a `[start, end)` UTC sub-window; `historical` = the existing
  neutral adapter fetch seam via an injected fetch callable). Synchronous (no job manager, per
  spec). Checksum computed at registration; the split tag is assigned at registration and frozen.
- **Split immutability, structurally** — no update/re-tag/delete function exists anywhere in the
  module and no PATCH/PUT/DELETE route exists. The 409-style refusal: dataset identity is its
  CONTENT checksum, so re-recording already-registered content under a different split (the
  re-tag attempt) — or the same split — raises `DatasetAlreadyRegistered`, mapped to HTTP 409
  naming the existing id and its frozen tag. Additionally the split lives INSIDE the
  checksum-verified region, so hand-editing the tag in the file is caught as an integrity error.
- **Integrity on every load** — two sha256 checks recomputed on EVERY load (no bypassable path):
  a whole-record file checksum (catches any tamper, split included) and the content checksum
  (symbol + feed + anchor + ordered events). Failures raise the distinct `DatasetIntegrityError`
  (detail → explicit HTTP 500; the list surfaces corrupt files in `integrity_errors` while
  healthy rows still serve — never silent, never fabricated). Unknown id → 404; invalid record
  request (unknown source/split, missing/malformed/inverted window, empty window) → 422.
- **Replay** — `DatasetStore.replay(dataset_id, config)`: verified load, then an unpaced replay
  through a FRESH `TapeEngine` (the studies-runner pattern) yielding every per-event snapshot.
  Byte-identical to replaying the original source stream (full frozen-snapshot equality at every
  tick + byte-identical serialized history at every bar size) and deterministic across re-runs.
  No REST replay endpoint (Product Shape lists none) — consumed by tests now, J-03's backtester
  next.
- **Routes** — exactly three, on the existing research router: `POST /research/datasets`
  (record/register), `GET /research/datasets` (list; `{"datasets": [...], "integrity_errors":
  [...]}`), `GET /research/datasets/{id}` (detail). `sim` is explicitly NOT a source kind
  (datasets are historical tape; a seeded sim reproduces on demand) → 422.
- **Committed miniature fixture pair** — `apps/backend/tests/fixtures/datasets/` (260 KB total):
  train = PG SIP 17:00:00–17:01:00Z (376 trades + 945 quotes), holdout = PG SIP
  17:05:00–17:05:45Z (228 trades + 930 quotes). Disjoint windows. Generated ONCE through the
  real record path by the committed `apps/backend/scripts/generate_dataset_fixtures.py` (which
  refuses regeneration while the pair exists) — never hand-crafted JSON. CI loads them through
  the real store path (checksum verification included) and replays them keyless.
- **No ambient recording** — nothing in the watch/stream path imports the dataset module;
  test-locked by an end-to-end SIM-BUYER watch asserting zero dataset files.
- **MCP: zero code changes** — `git diff app/mcp/ app/meta.py` is empty. The `datasets` tool
  flipped from honest 404 to live 200 automatically. The MCP test suite was extended minimally
  (spec-authorized): `datasets` moved out of the honest-404 premise set, a new test asserts
  tool-vs-curl **byte-identity on a non-empty 200 list**, the stdio end-to-end honest-404
  example switched to `backtests`, and the subprocess backend fixture now sets
  `TAPEOLOGY_DATASET_DIR` to a temp dir.
- **Playwright for the harness python3 (evaluator must-fix)** — install gate run first
  (`check-install.sh`), one-entry policy allowlist diff (the `mcp` precedent; see Notes),
  `playwright==1.61.0` installed to the user site, `python3 -m playwright install chromium` run.
  Verified: `python3 -c "import playwright"` exits 0, `python3 -m playwright --version` prints
  `Version 1.61.0`, a real headless chromium launch renders a page, and demo_runner.py's exact
  availability probe (`import playwright.sync_api`) passes — the replay lane will produce real
  result rows for J-01/J-08 instead of the iter-1 silent no-op. NOT added to
  `apps/backend/requirements.txt` (harness tooling, not a product dependency — requirements.txt
  is untouched).

### Design decisions (documented, not silent)

- **Content-addressed identity powers the 409.** With no mutation route besides POST, "attempt
  to re-tag" is expressed as re-recording the same content: the content checksum (symbol + feed
  + anchor + events) identifies a dataset, so one content = one dataset = one frozen split. The
  live-recorded train slice reproduces the committed fixture's checksum exactly
  (`dcf14dbd…`), demonstrating the determinism.
- **Window metadata**: the stored `window_start_utc`/`window_end_utc` are the REQUESTED bounds
  when given (they define the recording action); a reference record with no bounds stores the
  actual first/last event epochs. Machine records use ISO-8601 UTC (the MarketClock precedent);
  dd-MM-yyyy remains a UI-display rule and no UI changed.
- **List keeps serving through corruption**: one corrupt file must not take down the whole
  machine surface (MCP `datasets` proxies the list), so the list serves healthy rows and
  surfaces each corrupt file explicitly in `integrity_errors` — non-silent, non-fabricated.
- **Source vocabulary reused, not duplicated**: `SOURCE_REFERENCE`/`SOURCE_HISTORICAL` and the
  committed-reference loader are imported from `studies.py` (one owner per literal/loader).

## Files Changed

- `apps/backend/app/config.py` — `dataset_dir` knob + `dataset_dir_resolved()` env override +
  fingerprint exclusion (with rationale); `pathlib.Path` import
- `apps/backend/app/research/datasets.py` — NEW: the dataset store module (single owner of
  dataset files: record/register, verified loads, list/get/load_events/replay)
- `apps/backend/app/research/routes.py` — the three dataset routes + `DatasetRecordRequest`
  model + `get_dataset_store` dependency; imports for the datasets module + neutral adapter
  errors
- `apps/backend/scripts/generate_dataset_fixtures.py` — NEW: one-shot fixture-pair generator
  through the real record path (refuses regeneration)
- `apps/backend/tests/fixtures/datasets/6c9bf2c700d749e0993efd92c5807de3.json` — NEW: committed
  train fixture dataset (PG SIP 60 s)
- `apps/backend/tests/fixtures/datasets/d9f9dbe04fb24a7caccc53f0c6805412.json` — NEW: committed
  holdout fixture dataset (PG SIP 45 s)
- `apps/backend/tests/test_datasets.py` — NEW: 14 store-level tests (metadata, split
  immutability + reload, byte-identical replay vs source, corruption matrix, fixture pair,
  fingerprint exclusion)
- `apps/backend/tests/test_datasets_api.py` — NEW: 18 REST tests (record happy paths incl. the
  adapter seam, full 422 matrix, 409 re-tag, 404, corrupt-file 500 + `integrity_errors`, no
  ambient recording)
- `apps/backend/tests/test_mcp_server.py` — surgical: `datasets` out of the honest-404 premise;
  new non-empty byte-identity test; stdio honest-404 example → `backtests`; dataset-dir env in
  the backend fixture
- `incredible_auto_dev/config/install-security-policy.json` (repo-root `config/` symlink) —
  exactly ONE allowlist entry added: `"playwright"` (the `mcp` precedent from iter-1)

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/`
Result: **901 passed, 1 skipped** (the pre-existing credentialed live-integration skip), 0 failed
— all ≥868 archived-era tests intact plus 33 new (14 + 18 + 1); no test deleted or weakened.

Also run:
- Engine equivalence suite: `tests/test_observer_equivalence.py` → **7/7 passed** (default
  outputs untouched — no engine file changed, by construction)
- New tests confirmed FAILING first (TDD): module-missing / fixture-missing failures before
  implementation and generation
- Frontend build: `cd apps/frontend && npm run build` → passes (frontend untouched)
- Live service verification (real uvicorn via `scripts/start-backend.sh`, port 8650):
  `GET /research/datasets` **200** `{"datasets":[],"integrity_errors":[]}` (baseline was 404) →
  POST reference record 200 → re-tag attempt **409** with the frozen-tag message → unknown id
  **404** → list shows the row. MCP `datasets` tool against the live backend: byte-identical to
  curl on non-empty data, `isError` false. Frontend started (200 on `/`), both stopped, backend
  restarted with no port conflict, then all servers killed (ports 8650/3650 confirmed free).
- Playwright verification: import ok, `Version 1.61.0`, real headless chromium page render ok,
  demo_runner availability probe passes.

## Known Issues

- **PEP 668**: this Debian-based system blocks `pip install --user`, so the Playwright install
  used `python3 -m pip install --user --break-system-packages playwright==1.61.0` exactly as the
  spec anticipated (the package still lands in `~/.local`, not system site-packages). The
  chromium download landed at `~/.cache/ms-playwright/chromium_headless_shell-1228` and a real
  launch was verified.
- **Install-gate policy diff**: the gate required an allowlist entry even for a pinned version;
  the diff is exactly the one `"playwright"` entry (reviewer: please confirm it is exactly that
  one entry, per the spec's instruction).
- The MCP `datasets` tool DESCRIPTION string still says "404 until J-02 ships the dataset
  store" — now moot but accurate as written ("until"); left untouched because `app/mcp/` edits
  are explicitly out of scope this iteration.
- No real-credential Alpaca recording was exercised (J-02 is keyless by design; the historical
  source path is covered through the injected adapter seam with the committed real F-window
  fixture). Real-scale recording remains a later operator action through the same seam.
- Replay is exercised by tests and consumed next by J-03; there is deliberately NO REST replay
  endpoint (Product Shape lists none).

## Suggested Next Phase

J-03 per the spec's own pointer: strategy grammar v1 + the deterministic backtest engine over
these datasets (entries from the existing setup/state arming rules; exits by R-stop / horizon /
state-flip; config-owned fee/slippage models and $-per-R notional), producing persisted PnL
reports in R AND $ beside a seeded random-entry null baseline — `POST/GET /research/backtests`
flips the MCP `backtests` tool from honest 404 exactly the way `datasets` flipped this
iteration, and the committed train/holdout fixture pair gives it a keyless CI substrate.
