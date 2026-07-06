# Goal Iteration 1 — J-01 multi-timeframe bar store (the bar data foundation)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tape_to_profit_support_resistence
- **Iteration:** 1
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-01
- **Required-still-passing journeys:** J-07
- **Anti-goal reminders (verbatim — the six that bear directly on J-01):**
  - **No live execution path.** Tapeology MUST NOT place, route, or transmit orders anywhere — no brokerage integration, no trading API, **no paper-trading API**, no order tickets. The ONLY permitted "fill" is the offline backtester's simulated fill against recorded historical tape, clearly labelled simulated and sent nowhere; "position size" is a simulated notional, never a real order. *(critical)*
  - **The tape engine, `default` profile, and `v1` strategy are frozen.** Structure work is additive and versioned only: new bars/levels/classes and the `structure_tape` strategy may be added, but the `default` profile's outputs stay byte-identical (equivalence-tested), the live cockpit uses `default` only, `v1` stays byte-identical, and no enhancement may mutate an archived-era behaviour to pass. *(critical)*
  - **No fabricated data — honest failure states.** No synthesized bars, levels, trades, fills, or PnL to force a green journey; every failure mode (backend down, corrupt file, empty window, missing credentials, rate-limited, no levels found, insufficient n) surfaces an explicit, distinct state. *(critical)*
  - **Single source of truth.** Every canonical value — bar series, levels, confluence classes, backtest aggregates, PnL rows — is computed once and read verbatim by every surface (REST, WebSocket, UI, MCP, reports). A second computation path or a diverging number across surfaces is a defect. *(critical)*
  - **MCP is read-only.** The MCP server exposes no mutating tools, proxies only the canonical GET surface (plus the allowlisted `get_endpoint`), and MUST NOT become a second implementation of any computation. *(critical)*
  - **Persistence stays scoped.** SQLite holds research records; the bar and dataset stores hold explicitly recorded historical bars and tape for research replay. The live cockpit's tape remains unpersisted; no ambient recording. *(critical)*
  - *(The remaining critical anti-goals — no-lookahead, no-train-only-promotion, no-ML, no-profit-claims, no-capital/portfolio-management, enhancement-loop-in-its-box — govern levels/strategy/PnL work in J-02–J-06 and are not exercised by J-01's bar-data foundation; they still apply to any code J-01 touches and MUST NOT be violated.)*

## GOAL

A recorded multi-timeframe OHLC bar series can be ingested, persisted immutably (checksummed), and read back byte-identically via `GET /research/bars` / `GET /research/bars/{id}` and the MCP `bars` proxy — proven **keyless on a committed fixture** in CI — while the `default` profile and `v1` stay byte-identical.

## BACKGROUND

The iter-0 baseline recorded J-01–J-06 as honestly absent (404/422 + route-table inspection) and J-07 (eras 1–3 sentinel) as already-passing; the evaluator's explicit next-step recommendation is **"Build J-01 in iter-1, run it full."** J-01 is the era's designated unblocker — the natural dependency order is J-01 → J-02 → J-03 → J-04 → J-05 → J-06, and every downstream journey consumes the stored bar series (Data-Contract row 38), so nothing else can proceed until bars exist. **Depth = full** is justified by two "Picking depth" triggers: this is a **data-model change** (a new immutable checksummed store) **and a provider-seam integration** (a new `RawBar` + `fetch_bars` on the frozen `MarketDataAdapter` seam, wired to Alpaca `get_stock_bars`) — plus the prior evaluator's explicit `full` recommendation. It is deliberately **one risky journey isolated on its own** (rubric rule 5).

Two pitfalls carried into scope: (1) **`config_fingerprint` stability** — adding a `bar_dir` config field must NOT move the `default` fingerprint (mirror how `dataset_dir` is in the `excluded` set at `config.py`), or the J-07 equivalence suite breaks; a fingerprint-stability test pins this. (2) **lessons.md (iter-0):** the lean baseline never ran browser-qa; because J-01 changes **zero** `apps/frontend/` code, J-07's cockpit leg is guarded this iteration by the **engine equivalence suite (byte-identical `default`) + a verified zero-frontend-diff**, not by screenshots — and this iteration DOES change backend code, so the equivalence suite must be run for real (not asserted from a zero-diff shortcut).

## IN SCOPE

### Backend
- [ ] **Adapter seam** (`apps/backend/app/providers/adapters/base.py`): add a neutral `RawBar` dataclass (symbol, timeframe, UTC bar-open time, open/high/low/close, volume — a vendor-agnostic OHLC candle beside `RawTrade`/`RawQuote`) and add `fetch_bars(symbol, start, end, timeframe)` to the `MarketDataAdapter` Protocol. No vendor types cross the seam.
- [ ] **Alpaca adapter** (`apps/backend/app/providers/adapters/alpaca.py`): implement `fetch_bars` via the lazily-imported `StockHistoricalDataClient.get_stock_bars` with `StockBarsRequest` + `TimeFrame` (Minute/Hour/Day/Week/Month; 4h/8h expressed as Hour×amount). Stamp the feed via the existing `historical_feed()` (SIP|IEX). **Missing credentials → the EXISTING explicit unavailable state** (mirror `research/routes.py:1444` — `503 "real-data provider unavailable — a historical record needs credentials"`), NEVER fabricated bars. Free-tier discipline: throttle to the rate limit and **never fetch the most-recent (~15-min-delayed) bar**.
- [ ] **Bar store** — NEW module `apps/backend/app/research/bars.py`, mirroring `research/datasets.py`: a `BarStore` persisting immutable, checksummed bar-series files under a new `config.bar_dir`. Each entry stamps symbol, timeframe, UTC window, feed, **bar count**, and a **content checksum**. The ONLY mutation is `record`, which **refuses re-recording already-registered content** (mirror `DatasetAlreadyRegistered` → `BarSeriesAlreadyRegistered`). Both checksums (content + whole-file) are **recomputed and verified on EVERY load**. Honest failure states mirror datasets: `BarSeriesNotFound` (unknown id), `BarSeriesIntegrityError` (corrupt/tampered file), explicit empty-window refusal.
- [ ] **Config** (`apps/backend/app/config.py`): add `bar_dir` (package-anchored default `.data/bars`, mirroring `dataset_dir`) + `bar_dir_resolved` reading `TAPEOLOGY_BAR_DIR`; add a config-owned **`bar_timeframes`** enumeration (the valid `?timeframe=` set — distinct from the existing intra-second `history_bar_sizes`), plus any rate-throttle / recency-delay-guard parameters — **no magic numbers, no literals inline**. **Add `bar_dir` to the `config_fingerprint` `excluded` set** (same storage-location discipline as `dataset_dir`) so the `default` fingerprint stays byte-identical.
- [ ] **Routes** (`apps/backend/app/research/routes.py`, `/research`-prefixed router already mounted at `main.py:203`): add `POST /research/bars` (the explicit credentialed record/register action; missing creds → the 503 explicit-unavailable state above), `GET /research/bars` (list stored series), `GET /research/bars/{id}` (one series). Values are computed once by the store and served verbatim. An out-of-set `timeframe` is a **422 (never silently coerced)**, mirroring the `?bar=` validation precedent.
- [ ] **MCP** (`apps/backend/app/mcp/__init__.py`): add a `bars` tool — extend `STATIC_TOOLS` with `"bars": "/research/bars"` and add its `types.Tool(...)` entry; a thin, byte-identical `response.text` proxy (mirror `datasets`). Backend-down → an explicit tool error naming the base URL. **No mutating tool is added.**
- [ ] **Capability probe:** a one-symbol probe (daily/weekly/monthly/hourly) recording the plan's honest finding — feed (SIP|IEX), lookback range, and observed rate behaviour — into the dev handoff. Recorded honestly; never fabricated when credentials are absent (probe reports the missing-credentials state).
- [ ] **Committed keyless fixture:** a miniature multi-timeframe bar fixture proving ingest→persist→read in CI **without credentials**, mirroring the dataset store's committed-source-fixture mechanism (raw fixture under version control in `tests/fixtures/` + a generator/loader, OR a tracked bar-store entry). Invariant to satisfy: the fixture is committed AND keyless AND exercised by the test suite.

### Frontend (if applicable)
- None. J-01 is a machine surface only (REST + MCP). The nav skeleton (Cockpit · Journal · Studies · Performance) is unchanged; a levels/bars view is explicitly out of the data-foundation scope.

### New user-facing capability
An operator (or an MCP client) can record a multi-timeframe OHLC bar series and read it back — the first time the engine has ever had a bar, a timeframe, or historical structure data. Keyless on the committed fixture; a real Alpaca recording is an optional credentialed operator action that only enlarges the data.

### New information displayed
Bar-series metadata and OHLC candles via `GET /research/bars` / `GET /research/bars/{id}` and MCP `bars`: symbol, timeframe, UTC window, feed (SIP|IEX), bar count, content checksum, and the ordered OHLC candle list.

### New user actions
`POST /research/bars` (record/register a bar series — the explicit credentialed research action). No UI controls (machine surface).

### UI surface changes
None. No page, panel, or nav change.

### Product surface delta
The product gains a machine-readable historical-bar foundation under the existing Performance/research data model; the live cockpit and all four nav surfaces are untouched. Nothing user-visible changes in the browser.

### Blueprint conformance
No new surfaces. J-01's endpoints (`/research/bars*`) and MCP `bars` tool are machine surfaces already homed in the blueprint Information-Architecture table (row *"J-01 multi-timeframe bar store | API `/research/bars*` + MCP `bars` | machine"*). The nav skeleton is unchanged — no `blueprint.reapproval-requested` is written.

### Data-contract additions
**None new.** J-01 *realizes* the already-registered Data-Contract **row 38** (Bar series: symbol, timeframe, UTC window, feed, bar count, checksum) — single owner = the NEW bar-store module (`research/bars.py`) fed by `RawBar` + `fetch_bars` on the adapter seam; single serving endpoint = `POST/GET /research/bars*` + MCP `bars`. No blueprint edit is required and **no second computation or serving path for bars is introduced**. (Row 38 was drafted for the whole era at baseline; this iteration is its first real implementation.)

## OUT OF SCOPE

- **J-02** deterministic support/resistance level detection, and any `GET /research/levels` endpoint — next iteration.
- **J-03** confluence zones / A/B/C classes.
- **J-04** the `structure_tape` strategy and `GET /research/strategies`.
- **J-05** class-scaled stop/reward/simulated-size PnL.
- **J-06** the named-strategy comparison / generalized edge-report path.
- Any frontend or levels/bars **view** (explicitly out of the data-foundation scope per Product Shape).
- Any **real credentialed** bar recording as a *gating* requirement — the CI gate is keyless-on-fixture; real Alpaca bars are an optional credentialed operator action.
- Any change to the `default` profile, the `v1` strategy, the champion pointer, or any engine default.

## DEFINITION OF DONE

- [ ] **J-01 passes:** on the committed keyless fixture, ingest→persist→read works with **no credentials**; `GET /research/bars` and `GET /research/bars/{id}` return the stored series (symbol, timeframe, UTC window, feed, bar count, checksum + OHLC candles); a re-read is **byte-identical** — asserted by tests.
- [ ] Bar-store immutability + integrity proven by unit tests: byte-identical re-record→re-read; both checksums verified on load; corrupt file → explicit `BarSeriesIntegrityError`; re-record identical content → `BarSeriesAlreadyRegistered`; empty window → explicit refusal; unknown id → `BarSeriesNotFound`.
- [ ] `POST /research/bars` with missing credentials returns the **EXISTING explicit unavailable (503)** state — never fabricated bars — asserted by a test; an out-of-set `timeframe` returns **422**.
- [ ] MCP `bars` tool JSON is **byte-identical** to `GET /research/bars` (test); backend-down → an explicit tool error.
- [ ] **`config_fingerprint` for `default` is UNCHANGED** (`bar_dir` is fingerprint-excluded): the fingerprint-stability test passes and its counter-test still shows a real threshold moves the fingerprint; the **engine equivalence suite is 7/7 byte-identical `default`** (`tests/test_profile_equivalence.py`, `tests/test_observer_equivalence.py`) — this is J-07's guard.
- [ ] `v1`, `default`, and the champion pointer are untouched, and `git diff -- apps/frontend/` is **empty** (J-07 cockpit leg guarded by equivalence + zero-frontend-diff, per lessons.md).
- [ ] The capability-probe finding (feed SIP|IEX, lookback range, rate behaviour) is recorded honestly in the dev handoff.
- [ ] Full backend suite passes; no regressions (J-07 remains green).
- [ ] Dev handoff written at `docs/handoffs/goal-tape_to_profit_support_resistence-iter-1-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** none — `Frontend Present: no`. J-01 changes no `apps/frontend/` code, so J-07's cockpit leg is guarded this iteration by the **engine equivalence suite (byte-identical `default`) + a verified empty `apps/frontend/` diff** (per lessons.md, zero-frontend-diff makes the equivalence suite — not screenshots — J-07's evidence). Browser-QA stages (5, 6, 8) auto-skip with N/A stubs; the executor MUST still verify the frontend diff is empty and run the equivalence suite for real.
- **Unit/integration:** new `tests/test_bars.py` (store: record/load, byte-identical re-runs, double-checksum verify-on-load, immutability/`BarSeriesAlreadyRegistered`, `BarSeriesIntegrityError`, `BarSeriesNotFound`, empty-window refusal, stamp presence); new `tests/test_bars_api.py` (keyless-on-fixture `GET /research/bars` + `/{id}` happy path, missing-cred `POST` → 503, out-of-set timeframe → 422, unknown id → 404/explicit); extend `tests/test_mcp_server.py` (`bars` byte-identity + backend-down error); a **config-fingerprint-stability test** proving `bar_dir` does NOT move `config_fingerprint` plus the counter-test that a real threshold STILL does (mirror `tests/test_datasets.py`).
- **Error cases (must be rejected/surfaced explicitly):** corrupt bar file → `BarSeriesIntegrityError`; re-record identical content → `BarSeriesAlreadyRegistered`; empty window → explicit refusal; missing credentials on `POST /research/bars` → 503 explicit-unavailable; unknown id → explicit not-found; out-of-set `timeframe` → 422 (never silently coerced).

## NOTES

- **Depth = full** per the "data-model change" + "provider-seam integration" triggers and the iter-0 evaluator's explicit `full` recommendation. This is one risky journey isolated alone (rubric rule 5); J-02–J-06 wait for their own iterations.
- **Config-fingerprint pitfall (do not miss):** `bar_dir` MUST join the `excluded` set in `config.config_fingerprint` (same discipline as `dataset_dir`) or the `default` fingerprint moves and J-07 equivalence fails. The fingerprint-stability test is a DoD item, not optional.
- **lessons.md (iter-0) applied:** this iteration changes backend code, so the equivalence suite must be run for real to ground J-07 (the zero-diff shortcut no longer covers a code-changing iter). Because there is zero frontend diff, the browser-qa screenshot is correctly not required — but the empty `apps/frontend/` diff must be verified, not assumed.
- **Required-still-passing = J-07 only** because it is the *only* passing journey and is itself the aggregate eras-1–3 regression sentinel (engine equivalence + all archived surfaces + the full backend suite); J-01–J-06 are all failing and cannot be regression anchors. There is no additional passing journey to widen the set with.
- **Mirror, don't reinvent:** `research/datasets.py` (store + double checksum + immutable `record` + honest failure taxonomy), `research/routes.py:1444` (missing-cred 503), and the `datasets` MCP tool are the exact precedents to copy; matching them keeps the single-source-of-truth and honest-failure-state anti-goals satisfied by construction.
