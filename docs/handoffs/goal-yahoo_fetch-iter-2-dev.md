# goal-yahoo_fetch-iter-2 Dev Handoff

**Phase:** goal-yahoo_fetch-iter-2
**Date:** 2026-07-09
**Agent:** developer
**Status:** complete

## What Was Built

- **`_INTERVAL_MAP` expanded to the five directly-fetched era-5 timeframes**
  (`apps/backend/app/providers/adapters/yahoo.py`): `1d -> "1d"` (byte-identical to J-01),
  `1w -> "1wk"`, `1h -> "1h"`, `5m -> "5m"`, `1m -> "1m"`. Each exact interval string was verified
  against the LIVE vendor during implementation (not assumed from docs) — see "Tests Run" below.
- **The deterministic `4h`-from-`1h` resample** (`_resample_4h`, confined entirely to
  `yahoo.py` — the era's one named new backend computation): `fetch_bars` special-cases
  `timeframe == "4h"` by fetching real `1h` bars and aggregating them into buckets
  (open=first/high=max/low=min/close=last/volume=sum). Buckets reset at the start of each trading
  SESSION rather than a naive wall-clock `epoch % 14400` grid: a gap of more than 2 hours between
  two consecutive `1h` bars marks a new session (the overnight/weekend/holiday gap is always far
  larger than the ~1-hour intraday spacing), so a bucket always starts at a real session-open time
  the vendor itself returned — no hardcoded exchange hours or timezone conversion needed. A
  session whose bar count isn't a multiple of four (a 6.5h regular session yields 7 real `1h`
  bars: 4+3) naturally ends in a shorter trailing bucket built from only the bars that exist —
  never padded/forward-filled. Pure function of its `1h` input: two identical requests produce
  byte-identical `4h` output (unit-tested and live-tested). **Empirically cross-checked against
  yfinance's own native `"4h"` interval on a live 5-day AAPL window during implementation: my
  resample was bucket-for-bucket byte-identical to the vendor's own native series** — high
  confidence in correctness, even though (see Known Issues) this implementation deliberately never
  uses that native interval.
- **A three-way, observably-distinct honest-error taxonomy** on the Yahoo bar-fetch path:
  1. `UnsupportedTimeframe` (NEW exception, `providers/adapters/base.py`) — a config-valid
     `bar_timeframes` entry Yahoo does not serve this era (`8h`/`1mo`/`15m`). Raised BEFORE any
     vendor call (statically knowable from the timeframe string alone) — `research/routes.py`
     maps it to `422` with a detail naming the timeframe (e.g. `"timeframe '8h' is not served by
     Yahoo Finance"`).
  2. `NoDataForWindow` (EXISTING exception, reused per the goal's own naming) — a
     mapped/servable timeframe whose specific symbol/window genuinely returns nothing from the
     vendor (an unknown symbol OR a real window outside that timeframe's retention — yfinance
     answers both with an empty DataFrame, never an exception; there is no way to distinguish the
     two from the adapter's side, exactly as `fetch_bars`'s own protocol docstring already
     allowed). Mapped to `422` with a detail containing "no data" / "window".
  3. `VendorTimeout` (unchanged) — a real network timeout still maps to `504`.
  None of the three ever writes, pads, forward-fills, or fabricates a bar — verified by tests
  asserting zero files land in the bar store after each failure. A non-Yahoo adapter (FakeAdapter/
  Alpaca, injected via the existing `get_market_adapter` override) that still returns an empty
  tuple directly continues to hit the pre-existing, byte-identical `EmptyBarWindowError` 422 path —
  this taxonomy is additive to the Yahoo-specific path, not a replacement of the generic one.
- **`record_bar_series` (`research/routes.py`) gains two new `except` clauses** mapping
  `UnsupportedTimeframe` and `NoDataForWindow` to their distinct `422` responses, placed alongside
  the existing `VendorTimeout -> 504` clause around the same `adapter.fetch_bars(...)` call. HTTP-
  mapping glue only — the timeframe-classification and resample logic stay confined to `yahoo.py`.
- **Dependency discipline verified, not re-touched**: `yfinance==1.5.1` (pinned in
  `requirements.txt`, allowlisted in `config/install-security-policy.json`) is still the only new
  runtime dependency — J-02 needed no additional package; confirmed via `git diff --stat` showing
  zero changes to either file.

## Files Changed

- `apps/backend/app/providers/adapters/yahoo.py` -- MODIFY. `_INTERVAL_MAP` expanded to 5 entries;
  new module-level `_resample_4h` + its two tunables (`_FOUR_HOUR_BUCKET_SIZE`,
  `_SESSION_GAP_SECONDS`); `fetch_bars` special-cases `"4h"`, raises `UnsupportedTimeframe` for an
  unmapped timeframe (zero vendor call) and `NoDataForWindow` for a genuinely empty vendor
  response (previously both silently returned `()`); module + method docstrings updated for the
  new three-way taxonomy.
- `apps/backend/app/providers/adapters/base.py` -- MODIFY. New `UnsupportedTimeframe(Exception)`
  beside the existing `SymbolNotTradable`/`NoDataForWindow`/`VendorTimeout` trio.
- `apps/backend/app/research/routes.py` -- MODIFY. Import `UnsupportedTimeframe`; `record_bar_series`
  gains two new `except` clauses (`UnsupportedTimeframe`, `NoDataForWindow` -> both `422`, distinct
  detail text); docstring updated to describe the era-5 J-02 taxonomy.
- `apps/backend/tests/fixtures/yahoo/AAPL_1h_20260601_20260603.json` -- NEW. A REAL, live-captured
  AAPL `1h` series (15 bars: two full 6.5h trading sessions — 7 real bars each, naturally 4+3 — plus
  a third session truncated to its first bar only, giving a genuine partial-window trailing
  bucket). Lives under `tests/fixtures/yahoo/` per the iter-1 lesson (never `tests/fixtures/bars/`,
  which the frozen `test_bars.py::test_committed_fixture_loads_through_the_real_store_path_keyless`
  blanket-asserts `feed == "sip"` over).
- `apps/backend/tests/test_yahoo_adapter.py` -- MODIFY (extend + evolve). Two J-01 scope-boundary
  tests updated as the plan explicitly directed (`_INTERVAL_MAP` now asserts all 5 entries; the
  "unmapped timeframe" test repurposed to the 3 genuinely-Yahoo-unsupported ones, parametrized).
  One additional J-01 test evolved beyond what the plan explicitly flagged (see Known Issues):
  `test_fetch_bars_returns_empty_tuple_for_an_empty_vendor_response` -> now asserts
  `NoDataForWindow` is raised. Added: parametrized interval-mapping tests for `1w`/`1h`/`5m`/`1m`; a
  real-shaped-data `1h` parsing test off the new fixture; 9 `_resample_4h`/`fetch_bars(...,"4h")`
  tests (OHLC-exact on a full bucket, candle-for-candle vs. independently-computed expected values,
  session-boundary alignment — not a naive wall-clock grid, honest partial trailing bucket, the
  every-day natural 4+3 split, pure-function determinism across two calls, empty-input handling,
  end-to-end route-facing 4h fetch, `NoDataForWindow` propagation through the 4h path). 31 tests
  total in this file (was 14).
- `apps/backend/tests/test_bars_api.py` -- MODIFY (extend). The 12 pre-existing FakeAdapter-injected
  tests are UNTOUCHED and pass unmodified (byte-identical assertions). One J-01 Yahoo-path test
  evolved beyond what the plan explicitly flagged (see Known Issues):
  `test_yahoo_empty_vendor_response_is_the_existing_422_no_new_exception_type` -> renamed
  `test_yahoo_out_of_retention_or_unknown_symbol_is_422_no_data_for_window`, now asserting the
  `NoDataForWindow`-sourced detail text instead of the old `EmptyBarWindowError` text. Added 3 new
  route-level tests: an unsupported-timeframe request is `422` with zero vendor calls; the
  unsupported-timeframe and no-data-for-window responses are observably distinct (different detail
  text, diffed directly); `1mo`/`15m` hit the same case-1 taxonomy as `8h`. 18 tests total in this
  file (was 15).
- `apps/backend/tests/test_yahoo_live_integration.py` -- MODIFY (extend; stays
  `pytest.mark.integration`, gated on `TAPEOLOGY_LIVE_INTEGRATION=1`). Added: all six era-5
  timeframes fetch real bars within real retention; the live `4h` fetch equals `_resample_4h` of
  the live `1h` fetch; a real ~2-year-back `1m` window raises `NoDataForWindow`; a real `8h`
  request raises `UnsupportedTimeframe`. **Run live this session — all 5 tests PASSED** (see Tests
  Run below).
- **Not modified** (frozen; confirmed byte-identical in the diff): `apps/backend/app/config.py`
  (`config_fingerprint` independently re-verified as still `4d665603569b9dbf`), `research/levels.py`,
  `research/backtests.py`, `research/strategies.py`, `research/bars.py` (`BarStore` class itself),
  `providers/adapters/alpaca.py`, `providers/adapters/__init__.py`, `main.py`, `requirements.txt`,
  `config/install-security-policy.json`, and **all** of `apps/frontend/**` (`git diff --stat --
  apps/frontend/` returns empty — zero frontend files touched this iteration, per the plan's
  explicit "Frontend Present: yes is a pipeline-gating mechanism only" framing).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q --junit-xml=<path>`
Result: **1189 collected, 1183 passed, 6 skipped, 0 failed, 0 errors** (exit code 0). Baseline from
iter-1 was 1165 collected / 1163 passed / 2 skipped; this iteration adds exactly 24 new tests (17
net in `test_yahoo_adapter.py`, 3 net in `test_bars_api.py`, 4 net in
`test_yahoo_live_integration.py`) and 4 new default-skips (the expanded gated live-integration file
now has 5 tests, up from 1) — 1165 + 24 = 1189 collected, 2 + 4 = 6 skipped, both match exactly.
Confirmed via JUnit XML (`errors="0" failures="0" skipped="6" tests="1189"`).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_yahoo_adapter.py tests/test_bars_api.py tests/test_yahoo_live_integration.py -v`
Result: **49 passed, 5 skipped**, 0 failed (31 in `test_yahoo_adapter.py` + 18 in `test_bars_api.py`
+ 0 passed/5 skipped in `test_yahoo_live_integration.py`, correctly gated off by default).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py tests/test_profile_equivalence.py -q`
Result: **22 passed**, 0 failed — the two equivalence suites stay 22/22, proving byte-identical
`default`-profile engine output (no regression).

Command: `cd apps/backend && .venv/bin/python -c "from app.config import CONFIG; print(CONFIG.config_fingerprint())"`
Result: `4d665603569b9dbf` — unchanged, as required.

Command: `cd apps/backend && TAPEOLOGY_LIVE_INTEGRATION=1 .venv/bin/python -m pytest tests/test_yahoo_live_integration.py -v -s`
Result: **5 passed** (0.XXs) — ALL live, real, keyless Yahoo Finance checks succeeded, no mocks:
  - `test_real_yahoo_keyless_daily_fetch_returns_real_bars` (J-01 regression) — PASSED.
  - `test_real_yahoo_all_six_era5_timeframes_fetch_within_real_retention` — PASSED: real
    `1w`/`1d`/`4h`/`1h`/`5m`/`1m` AAPL bars fetched live, each with correct OHLC ordering,
    ascending timestamps, real volumes.
  - `test_real_yahoo_4h_equals_the_deterministic_resample_of_real_1h` — PASSED: a live `4h` fetch
    equals `_resample_4h` applied to a live `1h` fetch over the same window, byte-for-byte.
  - `test_real_yahoo_out_of_retention_1m_window_raises_no_data_for_window` — PASSED: a real `1m`
    request ~2 years back raised `NoDataForWindow` against the live vendor.
  - `test_real_yahoo_unsupported_8h_timeframe_raises_unsupported_timeframe` — PASSED.
  External integration confirmed working live, not mocks-only, per `.claude/core.md`.

Command (extra, beyond the plan's asks — full end-to-end proof through the actual HTTP server, not
just the adapter/pytest layer): with `bash scripts/dev.sh` running live, `curl -X POST
http://localhost:8301/research/bars -d '{"symbol":"MSFT","timeframe":"4h","start":"...","end":"..."}'`
Result: **HTTP 200**, `feed="yahoo"`, `bar_count=20`, real MSFT OHLCV `4h` candles, ascending
timestamps; `GET /research/bars/{id}` read it back byte-for-byte. A second POST with
`timeframe="8h"` (same window) returned **HTTP 422**, `detail: "timeframe '8h' is not served by
Yahoo Finance"`, through the real running route (not a unit test double).

Regression/coherence checks:
- `git diff --stat -- apps/frontend/` -> empty.
- `git diff --stat -- config.py main.py alpaca.py providers/adapters/__init__.py research/levels.py research/backtests.py research/strategies.py research/bars.py` -> empty (all byte-identical).
- `git diff --stat -- requirements.txt config/install-security-policy.json` -> empty (yfinance
  pin/allowlist unchanged from J-01, no new dependency).
- `grep -rn "resample\|_FOUR_HOUR\|_SESSION_GAP" apps/backend/app --include="*.py"` (excluding
  `yahoo.py`) -> no matches: the `4h` computation has exactly one owner, confirmed.

Service startup verified: `bash scripts/dev.sh` — backend (uvicorn, port 8301 this run) and
frontend (Next.js, port 3301 this run) both started cleanly with no errors; `GET
/research/taxonomy` (200), `GET /` (200), and `GET /structure` (200) all confirmed against the
live backend/frontend; both processes were killed cleanly afterward (`next-server`'s child process
required a direct `kill -9` beyond the `pkill` pattern match — noted below) and re-verified to
leave no lingering process or bound port on 8301/3301.

## Known Issues

- **Two additional J-01-era tests were evolved beyond what the plan's file list explicitly
  flagged**, applying the SAME "intended evolution of a scope-boundary test, not the forbidden
  weakening a frozen test" principle the plan explicitly sanctioned for two OTHER tests in
  `test_yahoo_adapter.py`. The plan's own framing of the error taxonomy ("Today
  `YahooAdapter.fetch_bars()` collapses two different situations into one empty tuple ... J-02 must
  split this into three observably distinct states") only makes sense if the mapped-timeframe/
  empty-vendor-response case (case 2) becomes an explicit raise rather than staying a silent empty
  tuple — and `docs/goal.md`'s own J-02 acceptance text literally names the mechanism ("an
  out-of-retention ... request returns an explicit neutral error (`NoDataForWindow` /
  unsupported-timeframe)"), and the QA agent's independently-written test plan
  (`reports/qa/goal-yahoo_fetch-iter-2-test-plan.md`, TC-08) independently arrived at the same
  expectation ("uses `NoDataForWindow` exception or equivalent"). Since Yahoo cannot distinguish
  "unknown symbol" from "out-of-retention window" (both give an empty DataFrame — a fact already
  frozen from J-01), there is no way to make ONLY a new "out-of-retention" test hit the new
  `NoDataForWindow` path while leaving the OLD "unknown symbol" test on the old `EmptyBarWindowError`
  path — they are the exact same code path. I evolved both tests (renamed, reasserted) rather than
  leaving them contradicting the new implementation. Flagging explicitly so the reviewer can verify
  this reasoning independently — the underlying BEHAVIORAL GUARANTEE (a genuinely unservable
  request is an explicit, honest 422, zero bars written, nothing fabricated) is preserved in both
  cases; only the exception type and detail text changed.
- **This adapter deliberately never uses `yfinance`'s own native `"4h"` interval, even though one
  exists.** During implementation I discovered (live, against the pinned `yfinance==1.5.1`) that
  the vendor now accepts `interval="4h"` directly and returns real session-aligned 4-hour bars.
  This is NOT used anywhere in this implementation: `docs/goal.md`'s anti-goal is explicit that
  `4h` must be "honestly derived" and "never presented as a vendor-native fetch," so `_INTERVAL_MAP`
  deliberately excludes `"4h"` and `fetch_bars` always resamples locally from real `1h` bars
  instead. I verified live that my local resample is bucket-for-bucket byte-identical to the
  vendor's own native `4h` series on the same window — strong independent confidence the algorithm
  is correct — but the implementation intentionally does not take the (arguably simpler) native-
  fetch shortcut, per the goal's explicit policy. Flagging for the reviewer/auditor's awareness
  since this is a deliberate policy choice, not an oversight, and could look at first glance like a
  missed simplification.
- **The session-boundary detector is a data-driven heuristic (a >2-hour gap between consecutive
  `1h` bars marks a new trading session), not an exchange-calendar lookup.** This was a deliberate
  choice to avoid adding any new dependency (an exchange-calendar library would violate the
  "yfinance is the only new runtime dependency" anti-goal) and to avoid hardcoding a specific
  exchange's regular-hours (e.g. `9:30 ET`) into the adapter. It is verified correct against real
  AAPL data (both the committed fixture and a live 5-day cross-check against yfinance's own native
  `4h` bars) and is robust to standard overnight/weekend/holiday gaps (always far larger than the
  ~1-hour intraday spacing), but it has not been tested against an exotic case such as a
  same-session multi-hour trading halt that happens to leave an exactly-2-hour data gap — an edge
  case I judged out of scope for this iteration's real-data test coverage.
- **`get_bar_fetch_adapter()` and `get_study_market_adapter()` remain deliberately distinct**
  (unchanged from J-01) — this iteration's new error taxonomy applies ONLY to the bar-fetch path
  (`POST /research/bars`); it does not touch `create_study`'s `SOURCE_HISTORICAL` path or any other
  caller of `get_study_market_adapter()`. Confirmed no diff to that resolver or its callers.
- The `next-server` (Next.js) worker process was not killed by the `pkill -f "next dev -p 3301"`
  pattern used during the pre-handoff service-startup check — it runs as a separate child process
  whose own command line is `next-server (v15.5.19)`, not `next dev ...`. I killed it directly by
  PID and re-verified no lingering process/port afterward. Noting this in case a future session's
  cleanup script relies on the same pattern-match — `scripts/dev.sh` itself is unchanged by this
  iteration (backend-only phase), so this is pre-existing environment behavior, not something this
  iteration introduced or fixed.
- No new REST-level vendor-selection parameter was added (same carried-over gap as iter-1's dev
  handoff already documented) — out of scope for J-02, which is confined to the interval map, the
  `4h` resample, and the error taxonomy.
