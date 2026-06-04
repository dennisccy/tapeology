# goal-i_will_be_super_rich-iter-3 Execution Plan

> **Market clock + honest "market is closed".** Build the already-registered Data Contract
> **row 8** (`GET /market/clock`) and use it to (a) turn the Live **market-status indicator**
> from a hardcoded "unavailable" stub into a real open/closed + next-open readout, and (b) add a
> **market-closed pre-flight gate** to the live `POST /watch` branch so a Live watch while the
> market is closed surfaces the explicit **"market is closed (with next open)"** non-cockpit
> state — completing **J-14 (4/4)**. **No engine is ever created** on refusal; **no fabricated
> tape**. Live *streaming* itself stays honestly absent (`provider_not_implemented`) — the async
> socket is deliberately deferred to iter-4.
>
> **Targets J-14.** Advances J-12 only insofar as its Live market-status surface becomes real.
> Must NOT regress J-01–J-11, J-13. **No `blueprint.md` edit / no re-approval** — row 8, the IA
> market-status indicator, and the row-9 "market is closed" state are already registered in the
> approved blueprint. This is a purely additive build into the existing IA + Data Contract on a
> deliberately small, low-risk diff (engine/classifier/serializers/sim+historical providers
> untouched).

## Goal alignment (no drift)

The spec matches `docs/goal.md` exactly: `GET /market/clock` is an enumerated Phase-1 endpoint;
J-14 lists "market is closed (with the next open)" as a must-have honest edge case verifiable
**without a live feed** (a pre-flight clock check, not streaming). Singularity, no-fabricated-
data, no-execution (read-only clock call), provider-agnostic, and no-magic-numbers anti-goals
are all explicitly honored. **No scope creep flagged.** Live streaming (J-12) and the stale-on-gap
watchdog (J-15) are correctly OUT OF SCOPE this iteration.

## What to Build

**Backend** (vendor specifics stay confined to `providers/adapters/alpaca.py`)
- **`MarketClock` neutral record** in `providers/adapters/base.py`: at minimum `is_open: bool`,
  `next_open` / `next_close` as ISO-8601 **UTC** strings (`Z`). No vendor type. Add
  `get_market_clock()` to the `MarketDataAdapter` Protocol.
- **`AlpacaAdapter.get_market_clock()`** (`adapters/alpaca.py`) via `TradingClient.get_clock()`,
  translating the tz-aware vendor datetimes → `MarketClock` (serialize to ISO/`Z`). SDK import
  stays **lazy + inside the method** (the SDK-confinement tests must pass unchanged). Read-only
  reference call — places/echoes **no** order (no-execution holds).
- **`GET /market/clock`** in `main.py` (row 8, the one canonical serving endpoint). Reads the
  adapter via the existing `Depends(get_market_adapter)` seam; runs the blocking call **off the
  event loop** (`asyncio.to_thread`, matching `_watch_historical`/`symbols_search`). Responses:
  - creds present → `200 {"available": true, "is_open": <bool>, "next_open": <iso>, "next_close": <iso>}`
  - no creds (`adapter.is_available()` false) → `200 {"available": false, "is_open": null, "next_open": null, "next_close": null}`
  - adapter/network error → **degrade** to the same `available:false` nulls (benign, like
    `/symbols/search`). **Never** a fabricated open/closed.
- **Market-closed pre-flight gate** in the `live` branch of `POST /watch/{ticker}`, inserted
  **between** the existing no-creds check (line ~140) and the `provider_not_implemented` refusal
  (line ~142):
  1. `if not adapter.is_available()` → `provider_unavailable` (unchanged).
  2. **new:** read `adapter.get_market_clock()` (off-loop). **Only** when the clock
     **authoritatively** reports `is_open == False` → raise
     `RealDataError("market_closed", "market is closed", <status>, next_open=<iso>)`. **No
     engine created.** (Honesty guard — see Assumptions #2: a *degraded/unreachable* clock must
     **not** be reported as "closed".)
  3. market open (or clock indeterminate) → keep the existing `provider_not_implemented` refusal
     (streaming is iter-4 — honest, not a fabricated cockpit).
- **Extend `RealDataError`** to optionally carry `next_open`; the exception handler includes a
  `next_open` field in the JSON body **only when present**, so the existing three reasons' bodies
  stay **byte-for-byte** unchanged.
- **Config tunable** in `app/config.py` (no-magic-numbers): the market-closed HTTP **status code**
  (recommended **409** — request valid, conflicts with current market state; 503 acceptable). A
  clock cache TTL is **optional and not recommended** this iteration (keep the diff small).
- **Extend `FakeAdapter`** (`tests/fakes.py`) with a **configurable clock** (open / closed /
  unavailable) so the new live-branch behavior is driven hermetically via `dependency_overrides`.

**Frontend** (cockpit body unchanged; still exactly one screen `/`)
- **Replace the hardcoded "market unavailable" pill** in `components/TopBar.tsx` (lines ~153–162,
  shown when `mode === "live"`) with a real **market-status indicator** that fetches
  `GET /market/clock` and renders **open** (emerald, "market open") / **closed** (amber, "market
  closed — next open <time>") / **unavailable** (slate/amber, when `available:false`). Poll on
  mount **and on a config-driven interval only while `mode === "live"`**, and **clear the
  interval on unmount / mode-change** (iter-0 resource-leak lesson). The indicator **reads** row 8
  — it does **not** recompute open/closed.
- **`getMarketClock()`** reader in `lib/api.ts` (GET `/market/clock`, returns the row-8 shape; any
  failure → `available:false`, never a fabricated status).
- **`"market_closed"`** added to the `FailureReason` union (`lib/types.ts`), to `HONEST_REASONS`
  (`app/page.tsx`), and a **`market_closed`** case in `ProviderUnavailable.copyFor` rendering the
  distinct phrase **"market is closed"** + the **next open** time. Renders **in place of** the
  cockpit via the existing `Cockpit | ProviderUnavailable | IdleState` ternary.
- **Thread `next_open`** through `watchTicker`'s `WatchResult` (`lib/api.ts`) → the `failure` state
  (`page.tsx`) → the `market_closed` panel. Keep the existing three reasons' behavior unchanged.

## Agents Required
- backend-data: yes — `MarketClock` record + `get_market_clock()` (Protocol + Alpaca), the
  `GET /market/clock` endpoint, the live `POST /watch` market-closed pre-flight gate,
  `RealDataError.next_open`, the config status-code tunable, and the FakeAdapter clock.
- frontend-ux: yes — real market-status indicator (poll + cleanup), `getMarketClock()`, the
  `market_closed` honest panel, and `next_open` threading.
- developer: yes — single developer implements both, TDD, backend first then frontend.

Frontend Present: yes

## Files to Create/Modify

**Backend — modify**
- `apps/backend/app/providers/adapters/base.py` — add `MarketClock`; add `get_market_clock()` to the Protocol.
- `apps/backend/app/providers/adapters/alpaca.py` — implement `get_market_clock()` via `TradingClient.get_clock()` (lazy SDK import).
- `apps/backend/app/main.py` — add `GET /market/clock`; insert the live market-closed pre-flight gate; extend `RealDataError` + its handler with `next_open`.
- `apps/backend/app/config.py` — add the market-closed status-code tunable.
- `apps/backend/tests/fakes.py` — `FakeAdapter` gains a configurable clock (open/closed/unavailable) + `get_market_clock()`.
- `apps/backend/tests/test_real_data_gate.py` — reconcile the live+creds test (Assumptions #3); add live-branch market-closed / market-open gate tests + the 4-way distinct-reason assertion.

**Backend — create**
- `apps/backend/tests/test_market_clock.py` — `GET /market/clock` matrix (open / closed-with-next-open / no-creds nulls / adapter-error degrade).

**Frontend — modify**
- `apps/frontend/components/TopBar.tsx` — real market-status indicator (replaces the stub pill); poll + interval cleanup.
- `apps/frontend/lib/api.ts` — `getMarketClock()`; `next_open` on `WatchResult`.
- `apps/frontend/lib/types.ts` — `market_closed` in `FailureReason`; a `MarketClock` response type.
- `apps/frontend/app/page.tsx` — `market_closed` in `HONEST_REASONS`; thread `next_open` into `failure`.
- `apps/frontend/components/ProviderUnavailable.tsx` — `market_closed` copy case rendering "market is closed" + next open (accept a `nextOpen` prop).

## UI Evolution
- **New user-facing capability:** selecting **Live** shows the **real** market session status
  (open / closed + next open) instead of a static "unavailable" stub; Watching a real symbol Live
  while the market is **closed** yields an explicit honest **"market is closed (with next open)"**
  screen instead of a cockpit.
- **New information displayed:** the Live market-status indicator (row 8) and the next-open time
  in both the indicator and the closed-market non-cockpit panel.
- **New user actions:** none — the existing **Watch** (Live) now reaches the closed-market honest
  state; the indicator is informational. Data-source selector, symbol search, Stop unchanged.
- **UI surface changes:** confined to the persistent **TopBar** (the indicator) and the existing
  honest non-cockpit panel (`ProviderUnavailable`) gaining a `market_closed` variant. Still
  exactly one screen.
- **Navigation changes:** none.

## Visual Requirements
- **Component patterns:** reuse the existing `Panel` for the `market_closed` non-cockpit state
  (mirror the other three honest panels). The indicator reuses the established TopBar status-pill
  styling (the dot + label pattern already in `STREAM_DOT`).
- **Layout:** unchanged — persistent TopBar pill (replaces the current `mode==="live"` pill);
  centered amber `Panel` for the honest closed state, in place of the cockpit.
- **Key visual effects:** load-bearing color semantics — **emerald** = market open, **amber** =
  market closed / next-open / honest-fail, **slate/amber** = unavailable. `font-mono` for the
  next-open time. No new effects invented.
- **States to handle:** indicator = open / closed (+ next open) / unavailable / in-flight (before
  first fetch, reuse a calm placeholder, never a fabricated "open"). Panel = the `market_closed`
  honest state. Poll cleanup on unmount + mode-change.

## Key Test Scenarios
Hermetic via `FakeAdapter` + `dependency_overrides`; browser where wall-clock permits.
- **`GET /market/clock`:** open → `available:true,is_open:true`; closed → `is_open:false` with a
  **non-null `next_open`**; no creds → `available:false` with **null** fields; adapter raises →
  `available:false` (no fabrication).
- **`POST /watch` live, market closed** (FakeAdapter `is_open=False`) → distinct `market_closed`
  refusal at the chosen 4xx/503 with `next_open` in the body, **and `GET /tape/{ticker}/state` →
  404** (no engine).
- **`POST /watch` live, market open** (FakeAdapter `is_open=True`) → still `provider_not_implemented`
  (honest iter-4 boundary; no fabricated cockpit).
- **Four refusal reasons pairwise distinct:** `provider_unavailable`, `symbol_not_tradable`,
  `no_data_for_window`, `market_closed`.
- **Confinement stays green, unchanged:** `import alpaca` + `ALPACA_API_*` confined to
  `providers/adapters/alpaca.py`; engine/config/serializers/`providers/base.py`/`simulated.py`
  reference no vendor.
- **No regressions:** full backend suite passes (currently **110**); sim + historical paths
  behavior-identical (empty diff in engine/config/serializers/`providers/base.py`/`simulated.py`/
  `historical.py`). Frontend `npm run build` clean.
- **Browser (Chrome MCP), creds present:** select Live → indicator shows real session status; if
  closed at run time, Watch `AAPL` → "market is closed — next open …" panel renders in place of
  the cockpit (no quote/trades/state panels). If open at run time, document that and rely on the
  deterministic backend closed-branch test (note which branch was observed). Regression smoke:
  `SIM-BUYER` → buyer_control (J-01/J-02/J-10); Historical replay populates the cockpit (J-11);
  symbol search fills the box (J-13); Stop → idle (J-09).

## Assumptions & Risk Flags (documented per token policy — do not block on these)
1. **Status code = 409** for `market_closed` (config-driven `CONFIG.market_closed_status_code`).
   The frontend keys off `reason`, not the code, so this is safe; 503 is an acceptable alternative.
2. **Degraded-clock honesty (critical, no-fabricated-data):** the `POST /watch` pre-flight gate
   refuses with `market_closed` **only** when the clock is authoritative (`available:true` and
   `is_open == False`). A clock that is **unreachable/errored/`available:false`** (creds present
   but the vendor call failed) must **not** be reported as "closed" — that would fabricate a
   session state. In that case fall through to the existing `provider_not_implemented` refusal.
   (`is_open` is `None` on a degraded clock, so a naive `if not clock.is_open` is a defect — guard
   on `is_open is False`.)
3. **Reconcile the existing live+creds test.** `test_live_watch_with_creds_does_not_fabricate_a_cockpit`
   currently uses the **real** `AlpacaAdapter` with monkeypatched fake creds and expects
   `provider_not_implemented`. Once the gate calls `adapter.get_market_clock()`, that path must
   stay **hermetic** (no real network in the suite). Drive the live-branch clock cases via
   `fake_client` + the new FakeAdapter clock (per the spec's test matrix); keep a real-adapter
   variant only if it stays offline-honest (degraded clock → `provider_not_implemented` per #2).
4. **Singularity (coherence guardrail):** one computing owner (`adapter.get_market_clock()`), one
   serving endpoint (`GET /market/clock`). The **TopBar indicator reads the endpoint**; the
   **watch pre-flight reads `adapter.get_market_clock()` directly** (same owner — *not* a second
   endpoint, *not* a recomputation), mirroring how the availability gate reads
   `adapter.is_available()`. **No** second clock lookup, **no** client-side open/closed derivation.
5. **Tunable placement:** the backend status code (and any cache TTL) goes in `app/config.py`. The
   **frontend poll interval** is frontend-owned (the UI can't read `app/config.py`); define it as a
   **named constant** in the frontend (like the existing `REPLAY_SPEEDS`/`WS_PUSH_INTERVAL`), not
   an inline literal — the no-magic-numbers anti-goal targets engine/adapter/API numbers, not a UI
   poll cadence. Suggested default ~60s (session status changes slowly).
6. **Process note (from spec DoD):** run the **full** pipeline including the post-QA **audit**,
   **coherence-auditor**, and **closure** gates — iter-2 produced no audit handoff, and row 8
   transitions registered→built this iteration.
```
