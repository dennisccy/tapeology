# goal-i_will_be_super_rich-iter-2 Execution Plan

> First **real provider behind the seam**: Historical replay (J-11) + symbol search (J-13),
> plus the unknown-symbol / no-data honest states (J-14, 2 of its 4 cases). The **same**
> `TapeEngine` and **same** canonical reads (`/state`, `/features`, `/summary`, `/events`,
> `WS /stream`) now render **real** Alpaca historical data — real data adds **no** parallel
> state/feature path. `alpaca-py` is the first real third-party dependency and the first real
> network I/O. Implements already-registered Data Contract **rows 7 + 9** and **feeds** rows
> 1–6 — **no `blueprint.md` edit, no re-approval** required. Targets **J-11, J-13**; advances
> **J-14**. Must NOT regress **J-01–J-10**.

## Verification-path decision (assumption — upfront question was dismissed)

Proceeding on the **safest autonomous default** = the spec's own escalation path:
- The developer **attempts a real Alpaca capture** via a committed operator script using the
  creds in `apps/backend/.env` (after the rename + loader below).
- **If capture succeeds** → commit the **real** fixture; the deterministic real-fixture replay
  test is the **in-loop J-11 evidence** (required-to-pass).
- **If capture is impossible** (invalid/expired creds, no network egress, no data entitlement)
  → **STOP and escalate in the dev handoff. Do NOT fabricate a fixture** (that is the
  *no-fabricated-data* anti-goal). J-11 in-loop evidence then rests on the provider seam +
  the historical controls + the honest states; the live/fixture capture is recorded as an
  **operator-gated** step. The DI fixture-replay **test scaffold is written either way**.

## What to Build

**Backend**
- **Fix the `.env` credential-name trap + add a loader (do this FIRST).** In the untracked
  operator `apps/backend/.env`, rename `ALPACA_SECRET_KEY` → **`ALPACA_API_SECRET`** (the
  adapter names are the contract — do **not** rename the adapter). Add a minimal **stdlib
  load-if-missing** loader (e.g. `app/env.py` imported at app startup and by `tests/conftest.py`)
  so both uvicorn and `pytest` see `apps/backend/.env`. **Loader rules:** never override an
  already-set env var (so `monkeypatch`/CI keep control and the existing gate tests stay
  hermetic); no new dependency. `.env` stays **untracked** — never commit it.
- **Add `alpaca-py` through the supply-chain gate.** Run
  `./scripts/automation/check-install.sh "pip install alpaca-py"` **first**; only on a pass add a
  **pinned** `alpaca-py==<resolved-version>` to `apps/backend/requirements.txt` and install into
  `apps/backend/.venv`.
- **Extend the Alpaca adapter — the ONE vendor module** (`app/providers/adapters/alpaca.py`,
  and nowhere else; the only place the SDK or the name "Alpaca" may appear):
  - `fetch_historical(symbol, start, end) -> list[raw trade/quote records]`
  - `search_symbols(query) -> list[{symbol, name}]`
  - **Translate vendor errors/empties into vendor-neutral outcomes at the seam** (e.g. neutral
    "not tradable" signal vs. empty list) so no Alpaca exception type leaks outward. Keep
    `is_available()` / `real_data_available()` as the single availability source. Run blocking
    fetches **off the event loop** (`asyncio.to_thread`) so the watch gate stays responsive.
- **`HistoricalProvider`** (new `app/providers/historical.py`) implementing the `Provider`
  Protocol (`ticker`, `scenario`, `stream()`):
  - Asks the adapter for the real window, then yields an **ordered** `TradeEvent`/`QuoteEvent`
    stream. Trades yielded as **`Side.UNKNOWN`** (the engine's aggressor classifier re-derives
    side from the interleaved quotes). **Preserve quote-before-trade at the same instant**
    (the engine relies on the in-effect quote — see `aggressor.py` / `tape_engine.py`).
  - Map real vendor timestamps → the engine's **logical** seconds (monotonic non-decreasing
    offsets from window start); **no wall-clock in events**.
  - `scenario` = the **`historical <SYM> <window>`** source label, so the row-6 watched-source
    descriptor renders from the canonical snapshot (no client recompute).
  - Define **neutral failure exceptions** (`SymbolNotTradable`, `NoDataForWindow`) in the
    provider/seam layer (not vendor types) for `main` to map → HTTP.
- **WatchManager: real-provider lifecycle.** Add `watch_with_provider(ticker, provider, ...)`
  that builds an engine fed by a given provider **without touching the sim registry**
  (`build_provider`). A **historical feeder** paces delivery by **inter-event logical gap ÷
  selected `speed`**, bounded by a **config cap** (a large gap never stalls the cockpit).
  Register its task in the existing `self._tasks` so `stop()` and a switch already cancel it —
  **no orphaned replay task** (iter-0 lesson). Engine math stays purely logical/deterministic;
  wall-clock only paces delivery.
- **`main.py` historical branch.** When `mode == "historical"` **and** `real_data_available()`:
  1. **Validate params → 422, no engine:** `start` < `end`, both parseable; `speed` ∈ the
     config-allowed bounded set.
  2. **Fetch the window** (off-loop). Map neutral failures → **explicit 4xx, no engine**:
     unknown/untradable symbol → `symbol_not_tradable` ("not a tradable symbol"); empty window
     → `no_data_for_window` ("no data for that window"). Missing creds → `503
     provider_unavailable` (unchanged). Each carries a distinct **`reason`** in the body.
  3. **On success** → build `HistoricalProvider` → `manager.watch_with_provider`.
  - **Replace** the historical use of the `provider_not_implemented` stub. **Live mode keeps its
    current behavior** (out of scope — still `provider_unavailable` / `provider_not_implemented`).
- **`GET /symbols/search?q=`** (row 7) — real tradable matches `[{symbol, name}, …]` via the
  adapter; **short/empty query → empty list** (not an error); result count capped by config.
  With no creds → empty list (graceful free-text degrade; never fabricated suggestions).
- **Config additions (no magic numbers, `app/config.py` only):** allowed replay-speed set +
  default; replay inter-event **pacing cap**; symbol-search **result limit**; symbol-search
  **min query length**. The allowed-speed set MUST be a **superset of the UI's {1,2,5,10}**.
- **Hermetic tests:** historical endpoint/provider tests **inject a fake adapter (DI / FastAPI
  dependency override)** returning the committed real fixture — a standard test seam, **never** a
  prod env-var backdoor and **never** a real network call in the suite.

**Frontend** (cockpit body stays identical across modes — no new cockpit, no mode-specific panels)
- **Cockpit on a successful historical watch** — a successful `POST /watch` (historical) drives
  the **existing** `Cockpit` exactly as sim (`page.tsx` `setTicker` → `useTapeStream` → REST/WS).
  The watched-source label reads `historical <SYM> <window>` from `snapshot.scenario` (row 6).
- **Symbol search box (J-13)** — in Live/Historical the symbol input offers **debounced**
  suggestions from `GET /symbols/search?q=` (symbol + name); selecting fills the symbol;
  **free-text entry still works**. No business logic — render adapter results verbatim.
- **Distinct honest non-cockpit states (J-14)** — `lib/api.ts` carries the distinct **`reason`**
  (not only `provider_unavailable`); `page.tsx` renders a **distinct amber panel per reason**:
  *provider unavailable (creds)* / *not a tradable symbol* / *no data for that window* —
  **in place of** the cockpit, never alongside fabricated panels. Generalize
  `ProviderUnavailable` (or add sibling panels).

## Agents Required
- **backend-data: yes** — `.env` rename + loader, `alpaca-py` (gated), adapter `fetch_historical`/
  `search_symbols`, `HistoricalProvider`, WatchManager historical lifecycle, `main.py` historical
  branch + `GET /symbols/search`, config additions, capture script + fixture, tests.
- **frontend-ux: yes** — debounced symbol-search dropdown, distinct honest non-cockpit panels,
  historical-success → cockpit wiring.
- developer: yes — implements both halves with TDD.

## Frontend Present
Frontend Present: yes

## Files to Create/Modify

**Create**
- `apps/backend/app/providers/historical.py` — `HistoricalProvider` + neutral failure exceptions + timestamp→logical mapping.
- `apps/backend/app/env.py` — minimal stdlib load-if-missing `.env` loader (no override).
- `apps/backend/scripts/capture_alpaca_fixture.py` — committed operator script: real creds → one fixed symbol+past-window → writes a **real** fixture.
- `apps/backend/tests/fixtures/alpaca/<sym>_<window>.json` — **REAL** captured fixture *(only if capture succeeds; never synthesized)*.
- `apps/backend/tests/test_historical_provider.py` — timestamp mapping + deterministic real-fixture replay.
- `apps/backend/tests/test_symbols_search.py` — search parsing/limit; short/empty → empty list.
- `apps/frontend/components/SymbolSearch.tsx` — debounced suggestions dropdown (or fold into TopBar).

**Modify**
- `apps/backend/app/providers/adapters/alpaca.py` — `fetch_historical` + `search_symbols` via `alpaca-py`; neutral error translation. *(sole vendor module)*
- `apps/backend/app/watch_manager.py` — `watch_with_provider` + cancellable per-event-paced historical feeder; `stop()`/switch teardown.
- `apps/backend/app/main.py` — historical branch (validate→422 / fetch→distinct 4xx no-engine / success→watch); `GET /symbols/search`; sibling error(s)+handler(s) carrying distinct `reason`.
- `apps/backend/app/config.py` — allowed speeds + default, replay pacing cap, search limit, search min-query-len.
- `apps/backend/requirements.txt` — pinned `alpaca-py==<ver>` (post-gate).
- `apps/backend/.env` — rename `ALPACA_SECRET_KEY` → `ALPACA_API_SECRET` *(untracked; not committed)*.
- `scripts/start-backend.sh` — ensure `.env` is loaded (loader module preferred over shell `source`, so pytest sees it too).
- `apps/backend/tests/test_real_data_gate.py` — allow the SDK import in the one adapter module; keep engine/config/serializers/`providers/base`/`providers/simulated` vendor-free (existing guards still pass); add distinct-`reason` + no-engine cases.
- `apps/backend/tests/conftest.py` — import the loader (no-override) so the suite stays hermetic.
- `apps/frontend/lib/api.ts` — `searchSymbols(q)`; `watchTicker` returns the distinct failure `reason`.
- `apps/frontend/lib/types.ts` — symbol-search result type; failure-reason type.
- `apps/frontend/components/TopBar.tsx` — wire `SymbolSearch` in live/historical (speeds already render).
- `apps/frontend/app/page.tsx` — generalize the failure state to render a distinct panel per reason; historical success → cockpit.
- `apps/frontend/components/ProviderUnavailable.tsx` — generalize / add siblings for the three reasons.

## UI Evolution
- **New user-facing capability:** watch a **real** US symbol over a chosen **past window**,
  replayed through the engine at a selectable speed; find a symbol by typing a partial
  name/symbol; honest distinct messages when a symbol is untradable or a window has no data.
- **New information displayed:** real bid/ask/spread/last, real recent trades, real feature
  readouts, real tape state + confidence, observations + event log for a replayed window (all
  **existing** cockpit values, now real-fed); live symbol-search suggestions; the
  `historical <SYM> <window>` source label; the two new honest states.
- **New user actions:** type a partial symbol → pick a suggestion; pick date + window + speed →
  Watch (controls already render from J-10; now they fetch real data).
- **UI surface changes:** **no new page or route** — the symbol input gains a suggestions
  dropdown and the non-cockpit area gains two new distinct messages; the cockpit is reused.
- **Navigation changes:** none (still exactly one screen `/`).

## Visual Requirements
- **Component patterns:** hand-built panels (no component library). Reuse the existing `Cockpit`
  panels verbatim for the real-data cockpit; honest states reuse the amber-bordered `Panel`
  pattern of `ProviderUnavailable`; suggestions = a slate dropdown list under the symbol input
  (existing `INPUT_CLASS` styling).
- **Layout:** persistent TopBar + responsive cockpit grid (unchanged); suggestions dropdown
  positioned under the symbol input.
- **Key visual effects (DESIGN SYSTEM tokens only):** amber = unavailable/unclear/honest-fail;
  emerald = active Watch; rose = stop/closed; **monospaced numerics** for all prices/sizes.
- **States to handle:** search empty/loading (no suggestions → no dropdown; free-text still
  works), the **three distinct** honest non-cockpit states, historical cockpit warm-up
  (connecting dot while fetch + replay populate), idle/empty after Stop.

## Key Test Scenarios
- **J-11 (deterministic, in-loop):** committed **real** fixture → `HistoricalProvider` + engine
  populates **every** cockpit value (bid/ask/spread/last, recent trades w/ price/size/side,
  feature readouts, tape state + confidence, observations, event log); a second identical run
  → **identical** state/confidence/features. *(If capture impossible: scaffold present +
  escalation documented — never a synthesized fixture.)*
- **J-11 (browser):** Historical mode → cockpit populates with real values; REST `/state` +
  `/features` match the UI (SSOT). (Operator-creds live fetch, or the fixture-backed watch.)
- **HistoricalProvider mapping:** timestamps logical, **monotonic non-decreasing**,
  **quote-before-trade preserved** at the same instant.
- **J-13:** `GET /symbols/search` returns real matches (symbol + name); short/empty query →
  empty list; typing a partial symbol shows suggestions; selecting fills the box; free-text works.
- **J-14:** unknown symbol → `symbol_not_tradable` ("not a tradable symbol"); no-data window →
  `no_data_for_window` ("no data for that window"); no-creds → `provider_unavailable`. Reasons
  are **distinct**, each creates **no engine** (subsequent `/state` → 404), and each shows **no
  cockpit** in the browser.
- **Validation:** `end ≤ start` / unparseable date-time / out-of-bounds `speed` → **422**;
  unknown `mode` → 422 (existing).
- **WatchManager historical lifecycle:** feeder cancellable; `stop()` **and** a switch tear it
  down (no orphaned replay task).
- **Adapter confinement:** `alpaca-py` import + the Alpaca name confined to
  `providers/adapters/alpaca.py`; engine/config/serializers/`providers/base`/`providers/simulated`
  reference no vendor (existing guard tests still pass, extended for the SDK import).
- **No regression:** existing **84** backend tests stay green; sim path byte-for-byte
  (no-body / `{}` / `mode:"sim"`); **browser** J-10 (selector + per-mode reveal), J-01/J-02
  (SIM-BUYER → buyer_control), J-09 (Stop → idle).

## Anti-goal guardrails (must hold)
- **Vendor seam singularity:** `alpaca-py` + "Alpaca" in **exactly one** module
  (`providers/adapters/alpaca.py`); engine/config/serializers/`providers/base`/
  `providers/simulated` stay vendor-free.
- **No secrets in source:** credentials env-only; `.env` stays untracked & uncommitted;
  `.env.example` keeps empty values.
- **No fabricated data:** every real-data failure = explicit distinct state, **no engine**, no
  sim fall-back; **never synthesize a fixture** (capture real or escalate).
- **Single source of truth:** rows 1–6 unchanged; historical feeds the **same** engine
  snapshot; no recompute in API/UI; **no new displayed value, no new contract row** (rows 7 & 9
  already registered).
- **Deterministic & reproducible:** engine math purely logical; wall-clock only paces delivery;
  rerun yields identical features/state/confidence.
- **Stay in scope / no execution path:** no broker/order/execution code; no
  scanner/news/charting/portfolio; **no engine/classifier/threshold/serializer/`providers.base`/
  `providers.simulated` change** beyond what the seam strictly requires.

## Out of scope (this iteration)
- **J-12 live socket + `GET /market/clock` (row 8)** and the live market-status pill wiring.
- **J-15** stale-gap → recover. **J-14 market-closed** case (needs Live → J-12).
- Level-2 book; persistence; predictive/backtest harness; extended tape states.

## Scope guard
If symbol search (J-13) proves harder than expected, **degrade gracefully to free-text entry**
(already working) so it cannot block J-11; flag any slip for the evaluator rather than expanding
scope.

## Documented assumptions
1. **Verification path** = the autonomous default above (attempt real capture; escalate on
   failure per spec NOTES; never fabricate). Upfront question was dismissed.
2. **`.env` loader** = tiny stdlib **load-if-missing** module (no override of existing env),
   imported at startup and by `conftest`; keeps the suite hermetic and `.env` untracked.
3. **Replay speeds:** backend allowed-speed config ⊇ the UI's `{1,2,5,10}`; keep `TopBar`
   `REPLAY_SPEEDS` in sync (no dynamic fetch — out of scope).
4. **`symbols/search` with no creds → empty list** (graceful free-text degrade); the unavailable
   state is surfaced at **Watch** (503), not in search.
5. **4xx mapping:** invalid params → 422; `symbol_not_tradable` / `no_data_for_window` → explicit
   4xx (e.g. 404) carrying a distinct body `reason`; the UI keys off `reason`. Each creates no
   engine.
6. **Blocking vendor fetch runs off the event loop** (`asyncio.to_thread`).

## Goal alignment / drift check
Aligned with `docs/goal.md` (Historical replay + symbol search + real-data honesty), the
approved **blueprint** (rows 7 + 9 already registered; rows 1–6 fed, not duplicated; single home
`/`), and the iter-1 eval recommendation. **No scope creep or goal drift detected.** Heeds both
prior lessons: the `.env` credential-name trap (fixed first) and orphaned-watch-on-switch
(historical feeder registered in `self._tasks` so `stop()`/switch cancel it).
