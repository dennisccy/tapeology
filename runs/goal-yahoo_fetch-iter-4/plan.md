# goal-yahoo_fetch-iter-4 Execution Plan

Target journey: **J-04** — "Real S/R levels and confluence zones on real Yahoo bars."
Required-still-passing: J-01, J-02, J-03, J-06 (foundation + eras 1-4 regression sentinel).

This is a **verify-and-lock** iteration, not a build. J-01-J-03 (Yahoo adapter, full timeframe set +
4h resample, SQLite store-first index) are already complete and audited (`PASS_WITH_GAPS`, both with
only documented, non-blocking GAP/OBSERVATION findings — see
`docs/handoffs/goal-yahoo_fetch-iter-3-audit.md`). `research/levels.py` is vendor-neutral by
construction (`compute_levels(store, symbol, as_of_epoch, config)` reads through the shared
`BarStore`, touching no vendor field) and `GET /research/levels` + the MCP `levels` tool already
serve it — so levels/zones simply populate once Yahoo bars exist for a symbol. **No production
source change is expected.** The deliverable is a committed real-Yahoo fixture plus tests proving
real levels+zones, REST==MCP agreement, no lookahead, and — the defining acceptance — that no
second levels/zone computation path was introduced anywhere.

## What to Build

- A committed real-Yahoo fixture under `apps/backend/tests/fixtures/yahoo/` that demonstrably
  yields, through `compute_levels` / `GET /research/levels`, non-empty `levels` AND at least one
  `confluence_zones` entry carrying an A/B/C `class` at a chosen `as_of`. **First verify** whether
  the two already-committed fixtures (`AAPL_1d_20260601_20260604.json`, 3 daily bars;
  `AAPL_1h_20260601_20260603.json`, 15 hourly bars) already cluster into a qualifying zone — see
  "Open Risk" below — and only add a richer real window if they don't.
- New test (`apps/backend/tests/test_levels_api.py`): **levels-on-Yahoo** — seed the committed
  Yahoo fixture(s) into a temp store, `GET /research/levels?symbol=<S>&as_of=<T>` →
  `no_bar_series_for_symbol: false`, non-empty `levels`, >=1 `confluence_zones` entry with an A/B/C
  `class`. Mirrors `test_get_levels_confluence_zones_exact_values_on_the_committed_pg_fixture`
  (same file, PG/`sip` fixture) but sourced from `tests/fixtures/yahoo/`.
- New test: **REST==MCP byte-for-byte** — the MCP `levels` proxy (`app/mcp/__init__.py`, tool name
  `"levels"`, proxies `GET /research/levels`) and the REST route return byte-identical JSON for the
  Yahoo-backed symbol at the same `symbol`/`as_of`.
- New test: **no-lookahead on Yahoo bars** — a level computed at `as_of` T is unchanged by a stored
  Yahoo bar timestamped after T (as-of truncation holds on the real Yahoo series, not just the PG
  fixture).
- **Coherence-lock confirmation** (read/diff check, not new code): `compute_levels` /
  `compute_confluence_zones` remain the sole owner in `research/levels.py`; both the REST route
  (`routes.py::get_levels`) and the MCP tool call it; no second levels/zone derivation exists
  anywhere (route, adapter, frontend, or a helper). This is what the downstream coherence-auditor
  step checks; the developer's job is to make sure nothing was added that would fail it.
- Confirm the existing honest-state tests still hold unmodified on the Yahoo path:
  `no_bar_series_for_symbol: true` for an unrecorded symbol; an `as_of` before the symbol's first
  Yahoo bar returns honest empty `levels` (not the no-series state); malformed/blank
  `symbol`/`as_of` stay 422.
- (Optional, integration-gated) an `integration`-marked live check under
  `TAPEOLOGY_LIVE_INTEGRATION=1`: fetch a real Yahoo window, then `GET /research/levels` returns
  real non-empty levels+zones live. Not required for the default hermetic suite.
- Dev handoff at `docs/handoffs/goal-yahoo_fetch-iter-4-dev.md`.

**If the developer finds a production change is genuinely required**, it MUST be additive and MUST
NOT alter `research/levels.py` (frozen byte-identical), its route, or the MCP layer.

## Agents Required

- backend-data: yes -- add/verify the committed Yahoo fixture(s) under
  `apps/backend/tests/fixtures/yahoo/`, write the three new hermetic tests in
  `test_levels_api.py` (levels-on-Yahoo populate, REST==MCP byte-identical, no-lookahead), confirm
  the coherence-lock, optionally add the `integration`-marked live check, run the full backend
  suite + equivalence tests, and write the dev handoff. No frontend, no production-logic change
  expected.
- frontend-ux: no -- J-04 is backend/API-verifiable only (keyless on the committed fixture); the
  `/structure` fetch control and "Yahoo Finance" provenance badge are **J-05**, explicitly out of
  scope this iteration.

## Frontend Present
no

## Files to Create/Modify

- `apps/backend/tests/fixtures/yahoo/` -- verify existing AAPL 1d+1h fixtures qualify (see Open
  Risk); add a richer real-Yahoo fixture file only if they don't (never synthesized data).
- `apps/backend/tests/test_levels_api.py` -- MODIFIED. Add the three new tests described above.
  Reference pattern already in this file:
  `test_get_levels_confluence_zones_exact_values_on_the_committed_pg_fixture` (line ~126).
- `docs/handoffs/goal-yahoo_fetch-iter-4-dev.md` -- NEW. Dev handoff.
- Expected **zero diff**: `apps/backend/app/research/levels.py`, `apps/backend/app/research/routes.py`
  (`get_levels`), `apps/backend/app/mcp/__init__.py`, `config.py` (fingerprint `4d665603569b9dbf`),
  `research/backtests.py`, `research/strategies.py`, the tape engine, the JSON `BarStore`, the
  Alpaca adapter. Any touch to these must be justified as additive-only in the dev handoff.

## Key Test Scenarios

- Seeded Yahoo fixture -> `GET /research/levels?symbol=<S>&as_of=<T>` returns
  `no_bar_series_for_symbol: false`, non-empty `levels`, >=1 `confluence_zones` entry with an A/B/C
  `class`.
- MCP `levels` tool and REST `GET /research/levels` return byte-identical JSON for the same
  Yahoo-backed `symbol`/`as_of`.
- A Yahoo bar stored with a timestamp after `as_of` T does not change levels computed at T
  (no-lookahead holds on real Yahoo data, not just synthetic/PG fixtures).
- Existing honest-state tests unmodified and passing: unrecorded symbol ->
  `no_bar_series_for_symbol: true`; `as_of` before the symbol's first bar -> empty `levels` with
  `no_bar_series_for_symbol: false`; malformed/blank `symbol`/`as_of` -> 422.
- Full backend suite green with zero regressions (iter-3 baseline: 1203 passed / 6 skipped / 0
  failed) plus the new tests, all passing.
- Engine equivalence suite 22/22 (`test_observer_equivalence.py` + `test_profile_equivalence.py`);
  `config_fingerprint` reproduces as `4d665603569b9dbf`.
- `git diff` shows no touch to `research/levels.py`, `research/backtests.py`,
  `research/strategies.py`, `config.py`, the tape engine, the JSON `BarStore`, or the Alpaca
  adapter (frozen-foundation check the developer should self-verify before handoff).

## Open Risk / First Verification Step

The phase spec itself flags this as unresolved: it is **not yet confirmed** that the two
already-committed Yahoo fixtures (3 daily + 15 hourly AAPL bars, prices roughly $305-$317) actually
cluster into a qualifying confluence zone. Read from `research/levels.py`: clustering pools levels
across every timeframe and groups them within `config.sr_confluence_band_bps` (20 bps = 0.20% of
the anchor price) of each other; **only clusters with >=2 members qualify** as a zone (a lone level
is honestly dropped, never a fabricated one-member zone). The developer's **first step** should be
to seed the two fixtures into a temp store and call `compute_levels`/hit the route directly to see
whether a qualifying zone actually forms at some `as_of`. If it does not, commit a richer real
Yahoo window (still real, never synthesized — e.g. a longer capture or an added
timeframe/symbol) that does, per the spec's explicit fallback instruction.

**Fixture-seeding mechanics note:** the two existing `tests/fixtures/yahoo/*.json` files are in
*raw-capture* format (`{symbol, timeframe, start, end, bars: [{epoch, open, high, low, close,
volume}]}`), not the `BarStore` per-record file format the PG fixture uses (which is
copied directly into the temp bar dir in `tests/fixtures/bars/`). `test_bars_api.py` already has a
proven helper chain for this exact format — `_load_yahoo_fixture()` / `_yahoo_fixture_dataframe()`
/ `_install_fake_yahoo_ticker(monkeypatch, df)` (around line 350-390) — which monkeypatches the
`yfinance.Ticker` boundary and POSTs through the real `/research/bars` route, exercising the real
`YahooAdapter`, `BarStore.record`, and `BarIndex.insert`. Reusing (or mirroring) that helper in
`test_levels_api.py` is the lowest-risk way to seed the temp store hermetically for the new tests,
rather than hand-building `BarStore`-format files for a vendor whose fixture format is already
established as raw-capture.

## Out of Scope (do not act on this iteration)

- Any modification to `research/levels.py`, `research/backtests.py`, `research/strategies.py`,
  `config.py`, the tape engine, the JSON `BarStore`, or the Alpaca adapter — all frozen
  byte-identical.
- The `/structure` fetch control, "Yahoo Finance" provenance badge, and
  `taxonomy.FEED_BASIS_LABELS["yahoo"]` — that is **J-05**.
- A feed-scoped `?feed=` filter or feed-segregated levels computation (the mixed-feed pooling edge
  cannot be closed without touching frozen `levels.py`; deferred per the assumption ledger).
- Champion promotion, PnL, strategies, backtests, datasets UI, tick-tape backfill.
- Audit carry-forwards **B2** (normalize blank `?symbol=`/`?timeframe=` to `None`) and **B3**
  (auto-index legacy series) — these are **J-05** pre-work, not J-04.
- Provisioning frontend `:3301`/backend `:8301` + Chrome MCP for the browser lane — a J-05 concern
  (forward-flagged in the spec's NOTES, not this iteration's job).

No drift from `docs/goal.md` detected: this phase spec is a direct, tightly-scoped implementation of
Key Capability 4 ("Real S/R levels & confluence zones on real bars ... no new computation, no
lookahead") and Must-have journey J-04, verbatim.
