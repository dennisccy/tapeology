# goal-yahoo_fetch-iter-1 Dev Handoff

**Phase:** goal-yahoo_fetch-iter-1
**Date:** 2026-07-09
**Agent:** developer
**Status:** complete

## What Was Built

- `YahooAdapter` (`apps/backend/app/providers/adapters/yahoo.py`, NEW) — the second concrete
  `MarketDataAdapter`: `name="yahoo"`, keyless `is_available()` (always `True`), and
  `fetch_bars(symbol, start, end, timeframe)` mapping ONLY the neutral `"1d"` timeframe to
  yfinance's `"1d"` interval this iteration (the full 6-timeframe table + `4h` resample is J-02,
  deliberately not built ahead — `_INTERVAL_MAP == {"1d": "1d"}`). `volume` is coerced to `int`.
  `fetch_historical` / `get_market_clock` / `stream_live` honestly raise `NotImplementedError`
  (Yahoo is bars-only, never fabricated); `search_symbols` honestly returns `[]`;
  `warm_symbol_universe` is a no-op (never raises, per the base seam's own contract). An unmapped
  timeframe or an empty vendor response (unknown/delisted symbol, or genuinely no data) both
  return an honest empty tuple `()` — no new exception type.
- A **bar-fetch-only vendor default** (`apps/backend/app/research/routes.py`): a new
  `get_bar_fetch_adapter()` resolver, used ONLY by `POST /research/bars` (`record_bar_series`),
  defaults to `YahooAdapter()` while still honoring any existing `dependency_overrides` on
  `get_market_adapter` — the exact mechanism every pre-iteration `test_bars_api.py` test already
  uses, so all 12 existing tests keep passing byte-for-byte unmodified. `get_study_market_adapter()`
  (used by `create_study` SOURCE_HISTORICAL and historical-dataset recording — both need
  `fetch_historical`, which Yahoo does not have) is left **untouched** — a deliberate, code-verified
  risk mitigation (plan Risk 1). The global live/tick/search accessor `get_adapter()` (`main.py`)
  is **untouched**.
- **`feed` provenance sourced from the adapter** — `record_bar_series` now stamps
  `feed = adapter.name if isinstance(adapter, YahooAdapter) else registry.config.historical_feed`:
  a Yahoo-served fetch stamps `"yahoo"` (single owner: the adapter); an Alpaca/fake-served fetch
  keeps the byte-identical pre-iteration `CONFIG.historical_feed` ("sip") stamp — NOT
  `adapter.name` applied uniformly (which would have silently renamed Alpaca's stamp from `"sip"`
  to `"alpaca"` and broken the frozen `test_post_records_and_registers_a_bar_series` assertion).
- `yfinance==1.5.1` pinned in `apps/backend/requirements.txt` (confined-to-adapter comment,
  mirroring the `alpaca-py`/`mcp` convention) and added to `python.allowlist` in
  `config/install-security-policy.json`. Verified via
  `scripts/automation/check-install.sh "pip install yfinance==1.5.1"` → `ALLOW` ("All packages
  are in the allowlist").

## Files Changed

- `apps/backend/app/providers/adapters/yahoo.py` -- NEW. `YahooAdapter`.
- `apps/backend/app/research/routes.py` -- MODIFY. New `get_bar_fetch_adapter()` resolver;
  `record_bar_series` uses it instead of `get_study_market_adapter()`; `feed` sourced
  conditionally from the resolved adapter; docstrings on `BarRecordRequest` and
  `record_bar_series` updated to describe the Yahoo-default reality (no behavior change from the
  docstring edits themselves; `get_study_market_adapter()` itself is untouched).
- `apps/backend/requirements.txt` -- MODIFY. Added pinned `yfinance==1.5.1`.
- `config/install-security-policy.json` -- MODIFY. Added `"yfinance"` to `python.allowlist`
  (this path is a symlink into `incredible_auto_dev/config/install-security-policy.json`, the
  correct "neutral asset source" location per CLAUDE.md's routing table).
- `apps/backend/tests/test_yahoo_adapter.py` -- NEW. 14 unit tests: identity, keyless
  availability, `MarketDataAdapter` protocol conformance, `fetch_bars` daily mapping + volume-`int`
  coercion + ascending-order + symbol normalization (mocked `yfinance.Ticker`, driven by the
  committed fixture), the explicit `_INTERVAL_MAP == {"1d": "1d"}` scope-boundary proof,
  empty-tuple honesty for an unmapped timeframe (asserting zero vendor calls) and an empty vendor
  response, and the five honestly-bars-only methods.
- `apps/backend/tests/test_bars_api.py` -- MODIFY (extend only; all 12 pre-existing tests
  unmodified and still passing with unmodified assertions). Added 3 tests: Yahoo-is-default
  end-to-end through the real route (mocked `yfinance.Ticker`, `feed=="yahoo"`, byte-for-byte
  `GET .../{id}`), a direct hermetic proof that `get_bar_fetch_adapter()` resolves to
  `YahooAdapter` with no override, and a Yahoo-empty-response 422 test proving the existing
  `EmptyBarWindowError` path is reused (no new exception type).
- `apps/backend/tests/fixtures/yahoo/AAPL_1d_20260601_20260604.json` -- NEW. A REAL, live-captured
  Yahoo daily AAPL 3-bar window (fetched live during implementation, then frozen), used to drive
  the mocked `yfinance.Ticker.history()` response in both test files above — see "Known Issues"
  for why this lives at `tests/fixtures/yahoo/` rather than the existing `tests/fixtures/bars/`.
- `apps/backend/tests/test_yahoo_live_integration.py` -- NEW. `pytest.mark.integration`, gated on
  `TAPEOLOGY_LIVE_INTEGRATION=1`: one real keyless Yahoo daily fetch for AAPL. **Run live during
  this session — PASSED** (see Tests Run below).
- **Not modified** (frozen; confirmed untouched in the diff): `config.py` (`config_fingerprint`
  independently re-verified as still `4d665603569b9dbf`), `research/levels.py`,
  `research/backtests.py`, `research/strategies.py`, `research/bars.py` (`BarStore` internals),
  `providers/adapters/alpaca.py`, `providers/adapters/__init__.py`, `providers/adapters/base.py`,
  `main.py`, `apps/frontend/**` (zero frontend diff — confirmed via `git status --short
  apps/frontend/`).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q --junit-xml=<path>`
Result: **1165 collected, 1163 passed, 2 skipped, 0 failed, 0 errors** (exit code 0). Baseline
from iter-0 was 1146 passed / 1 skipped / 1147 collected; this iteration adds exactly 18 new tests
(14 in `test_yahoo_adapter.py`, +3 net in `test_bars_api.py`, 1 in
`test_yahoo_live_integration.py`) and 1 new skip (the new gated live-integration test, skipped by
default) — 1147 + 18 = 1165 collected, 1 + 1 = 2 skipped, both match exactly. Confirmed via
JUnit XML (`<testsuite errors="0" failures="0" skipped="2" tests="1165">`) after the plain-text
`-q` run's final summary line was intermittently absent from piped/redirected output in this
environment (a capture quirk, not a test-outcome issue — the dot-progress markers were
consistently all `.`/`s` with zero `E`/`F` across every run, and JUNit XML gives the
unambiguous ground truth).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_bars_api.py tests/test_yahoo_adapter.py tests/test_observer_equivalence.py tests/test_profile_equivalence.py -v`
Result: **51 passed**, 0 failed (15 in `test_bars_api.py` [12 pre-existing + 3 new] + 14 in
`test_yahoo_adapter.py` + 7 in `test_observer_equivalence.py` + 15 in
`test_profile_equivalence.py`). The two equivalence suites total 22/22 passed, proving
byte-identical `default`-profile engine output — matches the plan's regression baseline exactly.

Command: `cd apps/backend && .venv/bin/python -c "from app.config import CONFIG; print(CONFIG.config_fingerprint())"`
Result: `4d665603569b9dbf` — unchanged, as required.

Command: `cd apps/backend && TAPEOLOGY_LIVE_INTEGRATION=1 .venv/bin/python -m pytest tests/test_yahoo_live_integration.py -v -s`
Result: **1 passed** — a real, live, keyless Yahoo Finance daily fetch for AAPL succeeded: no
credentials, real network call, real OHLCV data parsed correctly into `RawBar`s, ascending epoch
order confirmed. External integration confirmed working live, not mocks-only.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_yahoo_live_integration.py -v` (no env var)
Result: **1 skipped** — confirmed the gate correctly no-ops by default (no accidental network
call in the standard suite).

Service startup verified: `bash scripts/dev.sh` — backend (uvicorn, port 8301 this run) and
frontend (Next.js, port 3301 this run) both started cleanly with no errors; `GET
/research/taxonomy` against the live backend returned 200; both processes were killed cleanly
afterward and re-verified to leave no lingering process or bound port.

Supply-chain install gate: `./scripts/automation/check-install.sh "pip install yfinance==1.5.1"`
→ `Decision: ALLOW` / `Reason: All packages are in the allowlist.`

## Known Issues

- **Committed Yahoo fixture location deviates from the plan's literal path.** The plan said to add
  the fixture under `apps/backend/tests/fixtures/bars/`. I verified against the actual code that
  dropping a `feed="yahoo"` file into that flat, shared directory would break the EXISTING, frozen
  `tests/test_bars.py::test_committed_fixture_loads_through_the_real_store_path_keyless`, which
  does `store.list()` over the WHOLE directory and blanket-asserts `meta["feed"] ==
  CONFIG.historical_feed` for every record found there (that same directory also seeds
  `test_mcp_server.py`'s bars/levels byte-identity proofs and `test_levels.py`/`test_pnl_scan.py`
  fixture reads, though those are feed-agnostic / symbol-filtered and would not have broken).
  Rather than weaken or touch that frozen test (forbidden — J-06 requires "no test deleted or
  weakened to make new work pass"), I put the new fixture at
  `apps/backend/tests/fixtures/yahoo/AAPL_1d_20260601_20260604.json` instead — mirroring the
  EXISTING precedent of `tests/fixtures/alpaca/` (a raw vendor-capture-shaped fixture, sibling to
  the BarStore-native-shaped `tests/fixtures/bars/`). It is real, live-captured data (not
  synthetic), and is consumed by both new test files to drive a mocked
  `yfinance.Ticker.history()` response, exercising the adapter's real parsing code end to end with
  no network in the default suite. Flagging this explicitly as a deliberate, code-verified
  deviation from the plan's literal text, not an oversight.
- **The MCP `bars` tool is not re-tested specifically for a Yahoo-stamped series.** The DoD
  mentions "`GET /research/bars/{id}` and the MCP `bars` proxy return it byte-for-byte." I proved
  the REST half directly (byte-for-byte `GET .../{id}` in the new `test_bars_api.py` test). The
  MCP `bars` tool has zero feed-awareness — it is architecturally a byte-identical proxy of `GET
  /research/bars` (`app/mcp/__init__.py`: `"bars": "/research/bars"`), with no code path that
  could differentiate by `feed` value, and this is ALREADY proven byte-identical against live
  bar-store content by the existing, unmodified
  `test_mcp_server.py::test_bars_tool_byte_identical_on_a_non_empty_live_list` (which spins up a
  real uvicorn subprocess). I judged a Yahoo-specific duplicate of that proof to be redundant
  scope creep rather than added coverage, since nothing in the MCP layer branches on `feed`.
  Flagging so the reviewer can independently judge whether this reasoning is sufficient.
- **No REST-level vendor-selection parameter exists** (e.g. no `adapter_name` field on
  `BarRecordRequest`). The QA agent's test plan
  (`reports/qa/goal-yahoo_fetch-iter-1-test-plan.md`, written before this implementation existed,
  derived from the phase-spec text alone per its own trace log) speculates about a request
  parameter like `adapter_name="alpaca"` for selecting the vendor per-request (its TC-05/06/10/11).
  No such parameter is specified anywhere in `docs/goal.md`, the phase spec, or — critically — the
  execution plan (`runs/goal-yahoo_fetch-iter-1/plan.md`), which explicitly verified against the
  actual code and directed "Alpaca stays selectable" to mean via the EXISTING
  `dependency_overrides`-on-`get_market_adapter` test-injection mechanism (plan Risks 1 and 2, and
  the plan's own Key Test Scenarios wording: "overriding `get_market_adapter` (the existing test
  mechanism) still injects a fake/Alpaca adapter"). I followed the execution plan, which did the
  deeper, code-verified analysis; I did not add a speculative request parameter that isn't
  specified anywhere and would be scope creep relative to the plan's "Files to Create/Modify"
  list. In production (no test process, no `dependency_overrides` populated), the bar-fetch path
  will always resolve to Yahoo — there is currently no operator-facing way to force an Alpaca bar
  fetch through this endpoint; this matches the plan's explicit scope (era-5's
  Alpaca-bar-fetch-opt-in story is not elaborated beyond the test seam this iteration) but is
  worth the reviewer/QA agent confirming reads correctly when QA validates against the actual
  implementation rather than its own pre-implementation speculative plan.
- **`YahooAdapter.fetch_bars` maps only `"1d"` this iteration (by design, not a bug).** A request
  for any other config-registered timeframe (e.g. `"1h"`) through the Yahoo-default path returns
  an empty tuple → the existing `EmptyBarWindowError` 422 ("no bars in the requested window")
  rather than a timeframe-specific error message — this is the plan's own explicitly sanctioned
  Risk-4 behavior ("`YahooAdapter.fetch_bars()` returning `()` for a genuinely unservable request
  is sufficient — no new exception type is needed this iteration"). The full interval table plus
  the honest unsupported-timeframe/out-of-retention error taxonomy is J-02's job.
- **`yfinance` prints noisy diagnostic text to stdout/stderr on an unknown symbol** (e.g.
  `"$ZZZZZ...: possibly delisted; no timezone found"`) — cosmetic vendor-library log noise, not a
  functional issue; it does not affect the returned (empty) DataFrame or any assertion.
- Python in `apps/backend/.venv` is actually 3.14.4, not the 3.12 documented in README's
  Prerequisites — a pre-existing environment fact unrelated to this iteration, noted only because
  I observed it while verifying the venv; not something I changed or need to fix.
- `.claude/project-template.md` is still the unfilled generic template (a pre-existing gap noted
  in README.md's own `<!-- TODO -->` comment, predating this iteration) — I derived the real
  test/start commands from `README.md`, `apps/backend/pyproject.toml`, and `scripts/dev.sh` /
  `scripts/start-backend.sh` / `scripts/start-frontend.sh` directly, per that TODO's own
  instruction. Not fixed here (out of scope for this iteration).
- In this sandboxed environment, a pytest run's final one-line `-q` summary ("N passed... in
  X.XXs") intermittently did not appear in piped/redirected stdout even though the dot-progress
  markers and exit code were correct — a tool/capture artifact I worked around with
  `--junit-xml`. Noting it in case it affects a downstream QA/reviewer agent's own test capture.
