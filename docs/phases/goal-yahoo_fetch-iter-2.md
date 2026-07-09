# Goal Iteration 2 — J-02: the full timeframe set, incl. honestly-resampled 4h

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** yahoo_fetch
- **Iteration:** 2
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-02
- **Required-still-passing journeys:** J-01, J-06
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **`4h` is honestly derived.** It is a pure, deterministic resample of real `1h` bars, unit-tested for OHLC aggregation and bucket alignment, documented as derived; it is never presented as a vendor-native fetch and never fabricated. *(critical)*
  - **No fabricated bars, ever.** A symbol/window/timeframe Yahoo cannot serve (out of retention, unsupported interval, network failure) returns an explicit neutral error; the fetch never synthesizes, forward-fills across gaps, or pads a partial window to force a green journey. *(critical)*
  - **Yahoo default must not break the Alpaca path.** Making Yahoo the default bar vendor is additive: the Alpaca adapter, its credential gate, and its bar/tick/live paths stay byte-identical and selectable (opt-in). *(critical)*
  - **Dependency discipline.** `yfinance` is pinned in `requirements.txt` (confined to `adapters/yahoo.py`) and added to the install-security-policy allowlist; no unpinned/dynamic install, no other new runtime dependency. *(critical)*
  - **No new levels/PnL/strategy/champion computation.** This era feeds real bars to the existing era-4 owners and adds no second computation of levels, zones, PnL, aggregates, strategies, or the champion; the only new backend computation is the Yahoo fetch + `4h` resample confined to `adapters/yahoo.py` and the derived lookup index. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and archived-era behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact.
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*

## GOAL

The operator can fetch every era-5 Yahoo timeframe — `1w, 1d, 4h, 1h, 5m, 1m` — as real OHLCV bars, with `4h` deterministically resampled from real `1h` bars and honestly labelled as derived, and with out-of-retention windows and Yahoo-unsupported timeframes each returning an explicit, distinct neutral error that never fabricates a bar.

## BACKGROUND

J-01 landed the keyless Yahoo adapter but maps only `1d` (`_INTERVAL_MAP = {"1d": "1d"}`); every other timeframe currently returns an honest empty tuple → generic `EmptyBarWindowError` 422. J-02 is the next unblocker in the natural `J-01 → J-02 → J-03 → J-04 → J-05` chain: J-03 (store-first index) and J-04/J-05 (real levels/zones on real bars) all consume the multi-timeframe series this iteration produces. **Depth is `full`** (not lean) per two triggers in "Picking depth": (1) the iteration-1 evaluator explicitly recommended full for J-02, and (2) the `4h` resample is the era's *single named new backend computation* and carries its own critical anti-goal ("`4h` is honestly derived") plus the "no fabricated bars" and "no lookahead" rails — so the audit + coherence lanes must run to confirm the derived-`4h` value stays single-owner, deterministic, and honestly labelled. Only one risky change is bundled (the resampler); no second journey rides along.

Two lessons from prior iterations are carried in (see NOTES): the `feed="yahoo"` fixture-location rule (iter-1) and the "browser lane must actually run and emit evidence" rule (iter-0).

## IN SCOPE

### Backend
- [ ] Expand `_INTERVAL_MAP` in `apps/backend/app/providers/adapters/yahoo.py` to map the **five directly-fetched** era-5 timeframes to their real `yfinance` interval strings: `1w`, `1d`, `1h`, `5m`, `1m` (weekly is `yfinance`'s `1wk`; the developer confirms each exact interval string against the live vendor under the integration marker). `1d` mapping stays byte-identical to J-01.
- [ ] Implement the **deterministic `4h` resample-from-`1h`** *confined to `adapters/yahoo.py`* (the anti-goal-mandated single home for this computation). On a `4h` request the adapter fetches real `1h` bars and aggregates them into aligned 4-hour buckets: **open = first, high = max, low = min, close = last, volume = sum**, each bucket stamped `timeframe="4h"` with the bucket-open epoch. Buckets are **aligned to the session / regular-hours boundary** (not naive wall-clock modulo), and a **partial trailing bucket is handled honestly** (emitted from only the `1h` bars actually completed within it — never padded, never forward-filled, never using a future bar → satisfies the no-lookahead rail). The resample MUST be **byte-identical across identical requests** (pure function of the input `1h` bars; no wall-clock, no unseeded state).
- [ ] Make the honest error taxonomy **explicit and distinct** on the bar-fetch path (`POST /research/bars` → the Yahoo adapter): (a) a **Yahoo-unsupported timeframe** — a config-valid `bar_timeframes` entry that era-5 Yahoo does not offer (`8h`, `1mo`, `15m`) — returns an explicit neutral *unsupported-timeframe* error naming the timeframe as not served by Yahoo; (b) an **out-of-retention window** (e.g. `1m` two years ago) returns an explicit neutral *no-data-for-window* error (`NoDataForWindow` per the goal's naming); (c) **network failure** continues to surface the existing explicit `VendorTimeout` (504). Each is a distinct, honest state; **none** synthesizes, pads, or forward-fills a bar. The exact exception class is a developer decision, but the three states MUST be observably distinct (distinct detail messages / status) — not all collapsed into the generic empty-window 422.
- [ ] Pin/allowlist discipline: `yfinance` is **already** pinned (`requirements.txt`) and allowlisted (`config/install-security-policy.json`) from J-01 — J-02 adds **no** new runtime dependency. Verify this stays true (no unpinned/dynamic install introduced by the resampler).

### Frontend (if applicable)
- None. J-02 is a backend + provider-integration journey; the `/structure` fetch control and all UI provenance are **J-05** (out of scope here). No frontend file changes.

### New user-facing capability
Via `POST /research/bars` (REST) and the MCP `bars` proxy, an operator can now fetch real Yahoo bars at all six era-5 timeframes, including a genuinely-derived `4h`, and receives an explicit, distinct, honest error for windows/timeframes Yahoo cannot serve.

### New information displayed
None on-screen this iteration (no frontend change). New *API-observable* information: real bar series at five additional timeframes and the derived `4h` series, each served through the existing `GET /research/bars*` surface.

### New user actions
None (no UI change this iteration).

### UI surface changes
None.

### Product surface delta
The bar-fetch capability graduates from daily-only to the full era-5 timeframe set, feeding the multi-timeframe input that J-03/J-04/J-05 require. No visible product surface changes until J-05.

### Blueprint conformance
No new page, route, or nav element — J-02 lives entirely under the existing **Structure** home for the fetch capability (blueprint IA rows J-01/J-02, `/structure` → `GET /research/bars`). **Nav skeleton unchanged** (no re-approval request). The `4h` series flows through the existing bar-series value already registered in the Data Contract (row: "Bar series + double-sha256 checksums (candles)", owned by `BarStore` / `research/bars.py`, served by `GET /research/bars*` + MCP `bars`).

### Data-contract additions
**None.** J-02 introduces no new canonical *displayed* value. The six-timeframe series (including derived `4h`) are all instances of the existing BarStore-owned bar-series value, served by the existing `/research/bars*` endpoint; the provenance stamp `feed="yahoo"` is the era's single new owned value and was already registered in `blueprint.md` (Data Contract row 1) at J-01. The "`4h` derived-from-`1h`" honesty is enforced by **determinism + unit tests + adapter documentation**, not by a new canonical value. *If* the developer chooses to persist a `derived_from`/`resampled` provenance marker, it is an **additive field on the existing BarStore-owned series meta served by the existing `/research/bars*`** — no new owner, no new endpoint, no second computation. No blueprint edit is required this iteration.

## OUT OF SCOPE

- The derived **SQLite index / store-first coordinator** (`bar_index.py`) and the `?symbol=&timeframe=` filter — that is **J-03**.
- Real **S/R levels & confluence zones** on the new bars — **J-04** (owned by the untouched `research/levels.py`; J-02 adds no levels/zone computation).
- The `/structure` **fetch control**, the **"Yahoo Finance" provenance badge**, and the `taxonomy.FEED_BASIS_LABELS` label — **J-05**.
- Adding `15m` / `8h` / `1mo` as *fetchable* Yahoo timeframes — era-5 supports exactly the six enumerated in `docs/goal.md`; these three remain config-valid but Yahoo-unsupported (they exercise the unsupported-timeframe honest state). See assumption ledger iter-2.
- Any change to `config.py` (the six timeframes are already in `CONFIG.bar_timeframes`), `research/levels.py`, `research/backtests.py`, `research/strategies.py`, the engine, the JSON `BarStore`, or the Alpaca adapter — all stay byte-identical; `config_fingerprint` stays `4d665603569b9dbf`.
- Any tick-tape backfill, `/datasets` UI, brokerage/execution path, or champion movement.

## DEFINITION OF DONE

- [ ] `_INTERVAL_MAP` maps all five directly-fetched era-5 timeframes (`1w, 1d, 1h, 5m, 1m`) to real `yfinance` intervals; `1d` output is byte-identical to J-01.
- [ ] A `4h` request returns a series produced by resampling real `1h` bars (open=first / high=max / low=min / close=last / volume=sum, session-boundary-aligned), proven **byte-identical across two identical requests** by a unit test over a committed `1h` fixture, with an expected `4h` fixture asserted candle-for-candle.
- [ ] The partial trailing `4h` bucket is emitted from only the completed `1h` bars in it (asserted by test); no bar is synthesized, padded, or forward-filled anywhere in the fetch/resample path.
- [ ] A Yahoo-unsupported timeframe (`8h`/`1mo`/`15m`) returns an explicit unsupported-timeframe neutral error, **observably distinct** (detail/status) from the out-of-retention/empty-window error — asserted by a unit test.
- [ ] An out-of-retention window returns an explicit neutral no-data-for-window error with zero bars written — asserted by a unit test (keyless, via the injected fake/committed fixture path).
- [ ] Target journey **J-02** is scored `passing` by the goal-evaluator on unit + committed-fixture (keyless) evidence, plus the live six-timeframe + `4h`-matches-resampled-`1h` check under the `integration` marker (`TAPEOLOGY_LIVE_INTEGRATION=1`).
- [ ] Required-still-passing **J-01** remains green: a real `POST /research/bars` daily (or `1h`) fetch still returns HTTP 200 with `feed="yahoo"` and real bars (browser lane re-verifies and emits a screenshot).
- [ ] Required-still-passing **J-06** remains green: `config_fingerprint` stays `4d665603569b9dbf`, engine equivalence stays 22/22, the frozen `test_post_records_and_registers_a_bar_series` (Alpaca `feed=="sip"`) still passes, and `apps/backend/app/config.py` / `main.py` / `alpaca.py` show **zero diff**.
- [ ] No anti-goal violation introduced (scan-report 0 critical; coherence-auditor `COHERENCE-PASS` confirming the `4h` computation stays single-owner in `adapters/yahoo.py` and no second bar/levels computation appears).
- [ ] Full backend suite passes; no regressions. `yfinance` remains the only new runtime dependency (pinned + allowlisted); no new dependency added.
- [ ] Dev handoff written at `docs/handoffs/goal-yahoo_fetch-iter-2-dev.md`.

## TESTING REQUIREMENTS

- **Unit/integration (primary for J-02):**
  - Interval-mapping test: each of the six era-5 timeframes resolves (five direct + `4h` via the resample path); `8h`/`1mo`/`15m` do not resolve to a fetchable interval.
  - `4h` resampler tests over a **committed `1h` fixture** under `apps/backend/tests/fixtures/yahoo/` (NEVER `tests/fixtures/bars/` — see NOTES): assert OHLC aggregation exactly (open=first, high=max, low=min, close=last, volume=sum), bucket alignment to the session boundary, honest partial trailing bucket, and byte-identical output across two identical calls.
  - Error-taxonomy tests: unsupported-timeframe vs out-of-retention/empty-window are observably distinct; network failure → `VendorTimeout` (504); none writes or fabricates a bar.
  - Live `integration`-marked test (`TAPEOLOGY_LIVE_INTEGRATION=1`): fetch each of the six timeframes within its real retention window; confirm the live `4h` equals the deterministic resample of the live `1h`; confirm an out-of-retention `1m` and an unsupported `8h` each return the explicit neutral error.
- **Browser (regression re-verify — full pipeline runs the lane, which MUST emit evidence):** J-01 (`POST /research/bars` real Yahoo fetch renders real candles on `/structure`, `feed="yahoo"`) and J-06 (cockpit feed badge still "Simulated"; `/structure`, nav, and existing surfaces unbroken; zero unintended `yahoo` leakage beyond the already-Yahoo bar path).
- **Error cases (must be rejected/neutral, never fabricated):** unsupported timeframe (`8h`/`1mo`/`15m`), out-of-retention window (`1m` two years ago), empty/unknown-symbol window, network timeout, and `4h` requested with insufficient `1h` bars to fill a bucket (honest partial, not padded).

## NOTES

- **Lesson carried (iter-1 — fixture location):** a `feed="yahoo"` bar fixture MUST live under `apps/backend/tests/fixtures/yahoo/`, **never** `apps/backend/tests/fixtures/bars/` — the frozen `test_bars.py::test_committed_fixture_loads_through_the_real_store_path_keyless` runs `BarStore(FIXTURE_BAR_DIR).list()` over that whole dir and blanket-asserts `meta["feed"] == "sip"`, so a yahoo-feed file there breaks a frozen test. The existing `tests/fixtures/yahoo/AAPL_1d_20260601_20260604.json` is the precedent; add the new `1h`/`4h` fixtures beside it.
- **Lesson carried (iter-0 — browser lane must run):** any iteration claiming a browser-verifiable journey `passing` must confirm the browser-qa lane actually executed and emitted a screenshot; a "passing" without one is unevidenced. This is a full-depth iteration, so the 11-step pipeline runs browser-qa — ensure it emits evidence for the J-01/J-06 regression checks.
- **Confinement (anti-goal):** the `4h` computation is the era's single named new backend computation and MUST live only in `adapters/yahoo.py` — do not add a second resample path in `bars.py`, `levels.py`, or a route. The coherence-auditor will hard-fail a second owner.
- **Frozen invariants to re-prove:** `config.py` is untouched (all six timeframes already in `CONFIG.bar_timeframes`, which is fingerprint-protected) → `config_fingerprint` stays `4d665603569b9dbf`; `get_bar_fetch_adapter()` stays confined to `POST /research/bars` (never the shared `get_study_market_adapter()` / global `get_adapter()`), keeping the Alpaca cockpit/tick/live/search paths byte-identical.
- **Assumption logged:** era-5 Yahoo supports exactly the six enumerated timeframes; `15m` (config-valid + `yfinance`-native but not enumerated) is treated as Yahoo-unsupported this era — recorded in `runs/goal-session-yahoo_fetch/state/assumptions.md` (iter-2), reversible.
- **Reference:** iteration-1 evaluator next-step recommendation (`runs/goal-session-yahoo_fetch/iter-1/eval.md`) and coherence-auditor advisory (J-05 provenance-badge punch-list item deferred, unaffected by J-02).
