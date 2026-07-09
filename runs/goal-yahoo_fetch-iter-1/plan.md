# goal-yahoo_fetch-iter-1 Execution Plan

Era 5 "The Library", iteration 1 — **J-01 only**: the keyless Yahoo Finance bar adapter and the
bar-fetch vendor seam. No new UI (J-05 owns the `/structure` fetch control). Depth: full (flagged
by the spec and the iter-0 evaluator as the highest-regression-risk change of the era — new runtime
dependency + a vendor selector that must NOT flip the live/tick/search path). No drift from
`docs/goal.md`: this is exactly Key Capability 1 / Must-have journey J-01, and every OUT-OF-SCOPE
boundary below is honored — no scope creep found.

## What to Build

- `YahooAdapter` (`apps/backend/app/providers/adapters/yahoo.py`): implements `MarketDataAdapter`
  (`name="yahoo"`, keyless `is_available()` always `True`), `fetch_bars(symbol, start, end,
  timeframe)` mapping the neutral **`1d` timeframe only** to `yfinance` (the full 6-timeframe table
  + `4h` resample is J-02 — do not build ahead). `volume` coerced to `int`. `fetch_historical`,
  `search_symbols`, `stream_live`, `get_market_clock`, `warm_symbol_universe` honestly raise / return
  empty (Yahoo is bars-only) — never fabricate.
- A **bar-fetch-only vendor default**: `POST /research/bars` (`record_bar_series`,
  `research/routes.py:1537`, adapter resolved at `:1568`) resolves Yahoo by default; Alpaca stays
  selectable/opt-in. `get_adapter()` (`providers/adapters/__init__.py:16`) and `get_market_adapter()`
  (`main.py:127`) — which back the live cockpit / tick / live / search / clock — are **not touched**.
- `feed="yahoo"` sourced from the **adapter** only when Yahoo serves the fetch (never a
  route/client-hardcoded literal); when Alpaca serves it, `feed` stays exactly
  `registry.config.historical_feed` ("sip") — byte-identical to today.
- Pin `yfinance==<version>` in `requirements.txt` (confined-to-adapter comment, mirroring the
  `alpaca-py`/`mcp` convention); add `"yfinance"` to `config/install-security-policy.json`'s
  `python.allowlist`.
- Tests: `yahoo.py` unit tests, a `FakeAdapter`-injected route test, a committed Yahoo fixture (no
  network in the default suite), a `pytest.mark.integration`-gated live daily fetch.

Explicitly **out of scope** (do not build ahead): the full timeframe set + `4h` resampler (J-02),
the SQLite store-first index (J-03), levels/zones on real bars (J-04 — `research/levels.py` needs no
change, it already computes on whatever bars exist), the `/structure` fetch control + provenance
badge (J-05), and any change to `config.py`, `research/levels.py`, `research/backtests.py`,
`research/strategies.py`, the engine, `research/bars.py` internals, or the Alpaca adapter.

## Agents Required
- developer: yes -- backend-only. This project's implementation agent handles both backend and
  frontend, but there is zero frontend/UI work this iteration: new adapter module, a
  `research/routes.py` seam change, `requirements.txt` + `install-security-policy.json`, and tests.
  (Maps to the generic "backend-data: yes, frontend-ux: no" ask — this pipeline has one unified
  `developer` agent, not separately named backend/frontend agents.)

Frontend Present: yes

No new UI is built this iteration. `Frontend Present` is `yes` anyway, by explicit direction of the
phase spec's Goal Mode Metadata and NOTES: iteration 0's browser-qa lane never ran (no evidence was
emitted). This iteration must actually exercise the browser lane as a **J-06 foundation regression
spot-check** — confirming the vendor-selector/backend change did not break existing rendered
surfaces. Do not skip browser QA by reasoning "no UI changed."

## Files to Create/Modify
- `apps/backend/app/providers/adapters/yahoo.py` -- NEW. `YahooAdapter` class per above.
- `apps/backend/app/research/routes.py` -- MODIFY. (1) add a bar-fetch-only adapter resolver used
  solely by `record_bar_series` (~line 1568), defaulting to `YahooAdapter()` — see Risk 1 below; (2)
  change the `feed=` argument passed to `store.record(...)` (~line 1594) to source from the resolved
  adapter for Yahoo while preserving `registry.config.historical_feed` for Alpaca — see Risk 3.
- `apps/backend/requirements.txt` -- MODIFY. Add pinned `yfinance==<version>` with the
  confined-to-adapter comment (mirror the `alpaca-py==0.43.4` block).
- `config/install-security-policy.json` -- MODIFY. Add `"yfinance"` to `python.allowlist` (currently
  `["anthropic"]`).
- `apps/backend/tests/test_yahoo_adapter.py` -- NEW. Unit tests: `name=="yahoo"`, keyless
  `is_available() is True`, the `1d`→yfinance interval mapping, `int` volume coercion, tick/live/search
  honest raise/empty. Mock the underlying `yfinance` call — no network in the default suite.
- `apps/backend/tests/test_bars_api.py` -- MODIFY (extend, never weaken). Add: Yahoo-is-default on
  `POST /research/bars`, `feed=="yahoo"` sourced-from-adapter, Alpaca-still-selectable/opt-in, and
  confirm all 12 existing tests keep passing with unchanged assertions (the byte-identical-Alpaca
  contract).
- `apps/backend/tests/fixtures/bars/` -- ADD one new committed Yahoo-shaped fixture file (a distinct
  filename from the 2 existing Alpaca-era fixtures already there — do not overwrite).
- `apps/backend/tests/test_live_integration.py` (extend) or a new sibling file -- gated
  `pytestmark = pytest.mark.integration`, skips unless `TAPEOLOGY_LIVE_INTEGRATION=1`; one real
  keyless Yahoo daily fetch.
- **Not modified** (frozen; confirm untouched in the diff): `config.py`, `research/levels.py`,
  `research/backtests.py`, `research/strategies.py`, `research/bars.py` (`BarStore` internals),
  `providers/adapters/alpaca.py`, `providers/adapters/__init__.py`, `providers/adapters/base.py`,
  `main.py`.

## Critical Implementation Risks (verified against the current code, not just the spec text)

1. **`get_study_market_adapter()` (`routes.py:1220`) is shared by 3 call sites — only 1 is bars.**
   It backs `create_study` SOURCE_HISTORICAL (line 1317, uses `fetch_historical`), historical dataset
   recording (line 1463, uses `fetch_historical`), AND `record_bar_series` (line 1568, uses
   `fetch_bars`). Yahoo has no `fetch_historical` (bars-only, honestly raises). **Do not** make
   `get_study_market_adapter()` itself default to Yahoo — that would silently break studies (J-60/61)
   and historical dataset recording, a real J-06 regression. Add a distinct resolver used only at the
   `record_bar_series` call site; leave `get_study_market_adapter()` itself untouched.
2. **Preserve the existing `FakeAdapter` test-injection pattern.** Every existing `test_bars_api.py`
   test injects via `app.dependency_overrides[get_market_adapter] = lambda: fake`. The new bar-fetch
   resolver should keep honoring an existing override on `get_market_adapter` (mirror
   `get_study_market_adapter`'s own `app.dependency_overrides.get(get_market_adapter,
   get_market_adapter)()` shape, just with a **different fallback default** — `YahooAdapter()` instead
   of `get_market_adapter()`) so none of the existing tests need rewriting to keep passing.
3. **`feed` sourcing is vendor-conditional, not `adapter.name` applied uniformly.**
   `AlpacaAdapter.name == "alpaca"`, not `"sip"` — the existing stamped value
   (`test_bars_api.py::test_post_records_and_registers_a_bar_series` asserts `meta["feed"] ==
   CONFIG.historical_feed`). Using `adapter.name` for **both** vendors would silently change Alpaca's
   stamp from `"sip"` to `"alpaca"` and break that existing frozen test. Only the Yahoo branch stamps
   `feed="yahoo"` (from the adapter); the Alpaca branch keeps stamping
   `registry.config.historical_feed` exactly as today.
4. **Reuse the existing honest-error paths — do not add new ones.** `BarStore.record()` already
   raises `EmptyBarWindowError` (→ existing 422) on an empty bar list and `BarSeriesAlreadyRegistered`
   (→ existing 409) on duplicate checksummed content (the checksum already includes `feed`, so Yahoo
   and Alpaca content never collide). `YahooAdapter.fetch_bars()` returning `()` for a genuinely
   unservable request is sufficient — no new exception type is needed this iteration.

## UI Evolution
- New user-facing capability: none — backend/operator-only. An operator or agent can POST a Yahoo
  daily fetch (no credentials) and read it back via REST/MCP; no on-screen control yet.
- New information displayed: none on-screen; `feed="yahoo"` becomes a real field on `GET
  /research/bars*` and the MCP `bars` proxy (no human-readable badge yet — that's J-05's taxonomy
  label work).
- New user actions: none.
- UI surface changes: none — existing surfaces (`/`, `/journal`, `/journal/[id]`, `/studies`,
  `/performance`, `/structure`) must render exactly as before.
- Navigation changes: none.

## Visual Requirements
N/A — no new UI this iteration. The browser-qa lane's only job is confirming existing dark-mode
Next.js/Tailwind pages still render without regression after the backend vendor-selector change (see
Key Test Scenarios).

## Key Test Scenarios
- Keyless daily Yahoo fetch: `POST /research/bars` with no credentials configured stores a series
  stamped `feed="yahoo"` through `BarStore` (append-only, checksum-verified); `GET
  /research/bars/{id}` and the MCP `bars` tool return it byte-for-byte.
- `feed` provenance: grep/coherence confirms `"yahoo"` has exactly one owner (the adapter) — no
  hardcoded route/client literal; `config.historical_feed` untouched.
- Vendor selector: a fetch with no override resolves Yahoo by default; overriding `get_market_adapter`
  (the existing test mechanism) still injects a fake/Alpaca adapter and reproduces pre-iteration
  behavior byte-for-byte (all 12 existing `test_bars_api.py` tests pass with unmodified assertions).
- Duplicate content -> existing `409` `BarSeriesAlreadyRegistered`; a genuinely unservable
  symbol/window -> existing `EmptyBarWindowError` 422 path (no fabricated/padded bars).
- `yfinance` pinned + allowlisted; the supply-chain install gate passes.
- Full backend suite green (regression baseline from iter-0: 1146 passed / 1 skipped / 1147
  collected); equivalence suites 22/22; `config_fingerprint` still `4d665603569b9dbf`.
- Live integration (gated): `TAPEOLOGY_LIVE_INTEGRATION=1` real keyless Yahoo daily fetch; the dev
  handoff states pass/fail explicitly either way (per `.claude/core.md` External Integration Testing).
- Browser regression spot-check (must actually run and emit `ui-test-results.md` + screenshots):
  Cockpit `/` (highest-risk surface — the live path through `get_adapter()`) and Structure
  `/structure` render unbroken; spot-check `/journal`, `/studies`, `/performance` too.
- Coherence audit runs and clears, producing `coherence.md` (did not happen on iter-0's zero-diff
  baseline; must happen now that `feed="yahoo"` is a real owned value) — no second bar store, no
  second `feed` source, no second levels/PnL computation.
