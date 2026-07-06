# goal-tape_to_profit_support_resistence-iter-1 Execution Plan

Goal alignment: this iteration builds **J-01** (the multi-timeframe bar store), the explicit
designated unblocker per `docs/goal.md`'s Era 4 dependency order (J-01 → J-02 → ... → J-06) and
per the iter-0 dev handoff's own "Suggested Next Phase." It is additive-only, backend-only, and
protects the frozen `default` profile / `v1` strategy via a fingerprint-exclusion + the engine
equivalence suite. No drift from the goal or scope creep detected — the spec's IN SCOPE/OUT OF
SCOPE sections cleanly isolate J-01 from J-02–J-06 and from any frontend surface.

## What to Build

- Neutral `RawBar` dataclass + `fetch_bars(symbol, start, end, timeframe)` added to the
  `MarketDataAdapter` Protocol (adapter seam), beside the existing `RawTrade`/`RawQuote`/
  `HistoricalWindow`.
- Alpaca `fetch_bars` implementation via `StockHistoricalDataClient.get_stock_bars` +
  `StockBarsRequest` + `TimeFrame` (Minute/Hour/Day/Week/Month; 4h/8h expressed as Hour×amount);
  stamps the feed via the existing `historical_feed()` (SIP|IEX); throttles to the rate limit and
  never fetches the most-recent (~15-min-delayed) bar.
- New `BarStore` module mirroring `research/datasets.py`: immutable, double-checksummed
  (content + whole-file) bar-series files under a new config-owned `bar_dir`. `record()` is the
  only mutation and refuses re-registering identical content (`BarSeriesAlreadyRegistered`);
  honest failure states `BarSeriesNotFound`, `BarSeriesIntegrityError`, explicit empty-window
  refusal — verified on every load.
- Config additions: `bar_dir` (package-anchored default, `TAPEOLOGY_BAR_DIR` override) +
  `bar_dir_resolved()`; a `bar_timeframes` enumeration (the valid `?timeframe=` set); rate-throttle
  / recency-delay-guard parameters — no magic numbers. `bar_dir` joins the `config_fingerprint`
  `excluded` set so the `default` fingerprint stays byte-identical.
- Routes under `/research`: `POST /research/bars` (explicit credentialed record action),
  `GET /research/bars` (list), `GET /research/bars/{id}` (detail) — serving the store's metadata
  verbatim. Out-of-set `timeframe` → 422 (never silently coerced).
- MCP `bars` tool: a byte-identical read-only proxy of `GET /research/bars`, added to the existing
  static-tool registry; backend-down → an explicit tool error naming the base URL.
- A one-symbol capability probe (daily/weekly/monthly/hourly) recording the real, honest finding
  (feed, lookback range, rate behaviour) into the dev handoff — or the honest missing-credentials
  state if Alpaca creds are absent in this environment (never fabricated).
- A committed, keyless, miniature multi-timeframe bar fixture proving ingest→persist→read in CI
  with no credentials.
- A `config_fingerprint`-stability test (`bar_dir` excluded) plus its counter-test that a real
  threshold still moves the fingerprint.

## Agents Required

- developer: yes -- implement the full backend slice above end to end (adapter seam, Alpaca
  `fetch_bars`, `BarStore`, config, routes, MCP tool, capability probe, fixture, and the full test
  suite). Explicitly **mirror** `research/datasets.py`, the `/datasets` route trio
  (`routes.py:1374-1496`), and the `datasets` MCP tool throughout — this is the spec's own
  directive and keeps the single-source-of-truth / honest-failure-state anti-goals satisfied by
  construction. No frontend-ux work is required or in scope.
- backend-data: yes
- frontend-ux: no

Frontend Present: no

## Files to Create/Modify

- `apps/backend/app/providers/adapters/base.py` -- add `RawBar` dataclass + `fetch_bars` to the
  `MarketDataAdapter` Protocol
- `apps/backend/app/providers/adapters/alpaca.py` -- implement `fetch_bars`
  (`get_stock_bars`/`StockBarsRequest`/`TimeFrame`), rate-throttle, never-fetch-most-recent-bar
  guard, feed stamping via existing `historical_feed()`
- `apps/backend/app/research/bars.py` -- NEW module: `BarStore` (mirrors `research/datasets.py`
  end to end: double checksum, verified-on-every-load, `record()` as the only mutation,
  `BarSeriesNotFound`/`BarSeriesIntegrityError`/`BarSeriesAlreadyRegistered`, empty-window refusal)
- `apps/backend/app/config.py` -- `bar_dir` + `bar_dir_resolved()` (mirror `dataset_dir` /
  `dataset_dir_resolved()` at ~line 1143), `bar_timeframes` enum (see naming note below),
  rate-throttle/recency-delay params, `bar_dir` added to the `config_fingerprint` `excluded` set
  (mirror the `dataset_dir` entry at ~line 1192)
- `apps/backend/app/research/routes.py` -- `get_bar_store()` dependency + `POST /research/bars`,
  `GET /research/bars`, `GET /research/bars/{id}` (mirror the `/datasets` trio at lines 1374-1496)
- `apps/backend/app/mcp/__init__.py` -- `"bars": "/research/bars"` in `STATIC_TOOLS` (mirror line
  87) + a `types.Tool(...)` entry (mirror the `datasets` tool at lines 162-170)
- `apps/backend/tests/fixtures/bars/` (or an equivalent tracked bar-store entry -- developer's
  choice per spec) -- NEW committed keyless multi-timeframe bar fixture, mirroring
  `tests/fixtures/datasets/*.json`
- `apps/backend/tests/test_bars.py` -- NEW: store unit tests (mirror `test_datasets.py`'s scenario
  coverage and naming style)
- `apps/backend/tests/test_bars_api.py` -- NEW: route tests (mirror `test_datasets_api.py`'s
  scenario coverage and naming style)
- `apps/backend/tests/test_mcp_server.py` -- extend: `bars` byte-identity test + backend-down error
  test
- `docs/handoffs/goal-tape_to_profit_support_resistence-iter-1-dev.md` -- dev handoff, including
  the capability-probe finding and confirmation of zero `apps/frontend/` diff

## Key Test Scenarios

- Record → reload is byte-identical; both checksums (content + whole-file) are recomputed and
  verified on every load.
- Corrupt bar file -> `BarSeriesIntegrityError`; re-recording identical content ->
  `BarSeriesAlreadyRegistered`; empty window -> explicit refusal; unknown id -> `BarSeriesNotFound`.
- `GET /research/bars` / `/{id}` serve the stored series verbatim (symbol, timeframe, UTC window,
  feed, bar count, checksum, ordered OHLC candles) -- keyless on the committed fixture, in CI, with
  no credentials.
- `POST /research/bars` with missing credentials -> explicit unavailable response (see status-code
  note below); an out-of-set `timeframe` -> 422, never silently coerced.
- MCP `bars` tool JSON is byte-identical to `GET /research/bars`; backend-down -> an explicit tool
  error naming the base URL.
- `bar_dir` is excluded from `config_fingerprint`: the stability test passes, and its counter-test
  (a real threshold still moves the fingerprint) also passes.
- Full engine equivalence suite (`test_profile_equivalence.py` + `test_observer_equivalence.py`)
  stays green -- byte-identical `default` state/confidence/features/history, pinned fingerprint.
- `git diff -- apps/frontend/` is empty; full backend suite passes with zero regressions (J-07
  stays green); `v1`, `default`, and the champion pointer are untouched.

## Assumptions & Spec Clarifications

These are resolved here (not asked as questions) per the token/questioning policy -- each is a
low-ambiguity call grounded in direct inspection of the current codebase.

1. **Missing-credentials status code: spec cites a 503 precedent that is actually 422 in the
   current code -- resolve as 503, per the explicit, repeated DEFINITION OF DONE / TESTING
   REQUIREMENTS text.** The spec says three times that `POST /research/bars` with missing
   credentials must return **503** ("the EXISTING explicit unavailable (503) state"), citing
   `research/routes.py:1444` as the precedent. Direct inspection shows that line (and the
   analogous historical-study path at `routes.py:1294-1300`) both actually raise **422**, not 503
   -- confirmed further by the existing test `test_historical_without_credentials_is_an_explicit_422`
   (`test_datasets_api.py:221`). There is no existing 503-for-missing-credentials precedent
   anywhere in `routes.py` (the file's other 503s are generic internal-failure cases, e.g.
   `DatasetRecordError` at line 1464, or "could not persist/resolve/save" at lines 351/797/923/1176
   -- unrelated to credentials). Since the DoD and Testing Requirements are the graded acceptance
   criteria and state 503 unambiguously and repeatedly, implement **503** for this case -- reusing
   the existing message *style* ("real-data provider unavailable -- a historical bar recording
   needs credentials") and the "never fabricate" discipline, but at `status_code=503` rather than
   copying the 422 literally from the cited line. Write the DoD-required test asserting 503.
2. **`bar_timeframes` vs. the existing `history_bar_sizes` (config.py:211).** These are unrelated
   concepts: `history_bar_sizes` is the tape engine's existing intra-second rolling-window sizing
   (10/30/60s), unrelated to OHLC candle timeframes. Keep the new enum's name and any config keys
   clearly distinct (`bar_timeframes` as specified) so nothing conflates the two or collides.
3. **Capability probe outcome is not gated.** This environment's Alpaca credential state is
   unknown to this plan; the developer should run the probe honestly and record whatever the real
   environment shows -- a missing-credentials finding is an acceptable, expected, non-blocking
   outcome per the spec ("recorded honestly; never fabricated when credentials are absent").
4. **Fixture mechanism: recommend mirroring `tests/fixtures/datasets/*.json` directly.** The
   simplest path satisfying "committed AND keyless AND exercised by the test suite" is to commit
   1-2 small bar-store JSON files (covering at least two timeframes) in the exact `BarStore`
   on-disk format under a new fixture directory, then point a test's `BarStore` at that directory
   and assert a byte-identical load -- mirroring
   `test_committed_fixture_pair_loads_through_the_real_store_path_and_replays_keyless`
   (`test_datasets.py:292`). No `.env.example` change is needed (no new credential name; `bar_dir`'s
   override follows the same undocumented-storage-path convention as `TAPEOLOGY_DATASET_DIR`).
