# Goal Iteration 3 — Market clock + honest "market is closed" (complete J-14); live market-status indicator (row 8)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich
- **Iteration:** 3
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-14
- **Advanced (not a target-pass this iter):** J-12 (only its *Live controls + market-status* surface becomes real; live streaming stays out of scope — iter-4)
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-13
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No fabricated data.** The system MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. Every real-data failure mode MUST surface an explicit, distinct state and never a cockpit: a provider gap/feed lull → `stale`; an unknown/untradable symbol → an explicit error; an empty historical window → explicit no-data; a live watch while the market is closed → explicit closed (with the next open); missing credentials → explicit "unavailable". Falling back to simulated or invented data to mask a real-data failure is a defect. *(critical)*
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*
  - **Provider-agnostic engine.** The engine and API MUST depend only on the provider interface … A concrete vendor SDK MUST appear in only one adapter module behind a vendor-neutral seam, so a second vendor is one new adapter; vendor specifics MUST NOT leak into the engine, providers, or API.
  - **No secrets in source.** Real-vendor API keys/tokens MUST come only from environment/config and MUST NOT be committed; with no keys the app runs simulator-only and real modes report an explicit "unavailable" rather than failing opaquely or fabricating data.
  - **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the tape. *(critical)*
  - **No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code.

## GOAL

Complete **J-14** (honest real-data edge cases, partial 3/4 → 4/4): a **Live** watch while the **market is closed** surfaces an explicit, distinct "market is closed (with the next open)" state — never a cockpit, never a fabricated tape, no engine created. To get there honestly, build the registered **market clock** (Data Contract **row 8**, `GET /market/clock`) and turn the Live **market-status indicator** from a hardcoded "unavailable" stub into a real open/closed + next-open readout.

## BACKGROUND

J-11 (historical replay), J-13 (symbol search), and 3/4 of J-14's honest edge cases landed in iter-2 with zero regressions; the only remaining real-data **failing** journeys are the **live-streaming half** — J-12 (real live WebSocket) and J-15 (stale-on-gap → recover) — plus J-14's 4th case (market closed). The iter-2 evaluator recommended building the entire live half at once. **This iteration deliberately takes only the market-clock slice** and defers the live socket to iter-4, because (a) the agent mandate is to stay tight (1–3 journeys, easy to score); (b) the live socket is a genuine architecture change — the `Provider` Protocol is today a *synchronous* `stream() -> Iterable[Event]`, while a live feed is async/unbounded — and bundling that refactor with the new honest-state UI would enlarge the blast radius against **11** currently-green journeys; and (c) J-12/J-15's real-socket behavior is **operator/gated** anyway (it cannot "pass" via browser QA), whereas the market clock is a *prerequisite* for both J-12's pre-flight open-check and J-14's closed case and is **fully hermetically + browser verifiable now**. So iter-3 completes a real journey (J-14) and builds a whole registered contract row (row 8) on a small, low-risk diff; iter-4 then does the live socket on top of it.

The market-closed refusal is a **pre-flight gate** (check the clock → refuse *before* any streaming), so it needs **no live socket** — exactly why goal.md lists the closed-market path as "verifiable without a live feed."

**Lessons applied (from `lessons.md`):**
- *iter-1 (env-name + dotenv):* RESOLVED — `app/env.py` (`load_env`) loads `apps/backend/.env` load-if-missing and is invoked by `app/main.py` and `tests/conftest.py`; the adapter reads `ALPACA_API_KEY`/`ALPACA_API_SECRET` (matching `.env.example`). The new clock method **reuses this same credential path** — do not introduce new env names.
- *iter-2 (capture-once fixture; IEX wide spread; naive-datetime→UTC):* The clock is tiny and time-varying, so a captured fixture is unnecessary — drive determinism with a **FakeAdapter** clock (open/closed/unavailable) via `dependency_overrides`, the established hermetic pattern. Alpaca returns **tz-aware** datetimes; serialize `next_open`/`next_close` as explicit ISO-8601 (UTC/`Z`) and render them with an explicit tz so an operator is never misled about "next open."
- *iter-0 (orphaned watch / leaked resource on switch):* No new feeder here, but the market-status **poll** must be cleaned up — clear its interval on unmount and on mode-change so switching away from Live leaks no timer.

**No new dependency / supply-chain gate:** `alpaca-py==0.43.4` is already pinned and allowlisted; the clock uses `TradingClient.get_clock()` from that same SDK — no new install.

## IN SCOPE

### Backend
- [ ] Add a vendor-neutral **`MarketClock`** record to `app/providers/adapters/base.py` — at minimum `is_open: bool`, `next_open` and `next_close` as ISO-8601 UTC strings (or tz-aware datetimes serialized to ISO at the endpoint). No vendor type leaks.
- [ ] Add **`get_market_clock()`** to the `MarketDataAdapter` Protocol (`adapters/base.py`) and implement it in **`AlpacaAdapter`** (`adapters/alpaca.py`) via `TradingClient.get_clock()`, translating the vendor response into `MarketClock`. The `alpaca` SDK import stays **lazy and confined to `alpaca.py`** (the existing confinement tests must keep passing unchanged). This is a read-only reference call — it places/echoes **no** order (no-execution anti-goal holds).
- [ ] Add **`GET /market/clock`** to `app/main.py` (Data Contract **row 8**, canonical serving endpoint). Reads the adapter via the existing `Depends(get_market_adapter)` seam (so tests can override it). Response shape:
  - creds present → `200 {"available": true, "is_open": <bool>, "next_open": <iso>, "next_close": <iso>}`
  - no creds (`adapter.is_available()` false) → `200 {"available": false, "is_open": null, "next_open": null, "next_close": null}` (explicit unavailable — never a fabricated open/closed)
  - adapter/network error → degrade to `available:false` (benign, like `GET /symbols/search`); never fabricate. Run the blocking vendor call off the event loop (`asyncio.to_thread`), matching `_watch_historical`/`symbols_search`.
- [ ] Add the **market-closed pre-flight gate** to the `live` branch of `POST /watch/{ticker}` (`main.py`), inserted **between** the existing no-creds check and the still-unimplemented streaming refusal:
  1. `if not adapter.is_available()` → `provider_unavailable` (unchanged).
  2. **new:** read `adapter.get_market_clock()` (off-loop); `if not clock.is_open` → raise `RealDataError("market_closed", "market is closed", <code>)` carrying the **next open** (include it in `detail` and as a structured `next_open` field in the JSON body). **No engine is created.**
  3. market open → keep the existing `provider_not_implemented` refusal (live streaming is iter-4 — this stays honest, not a fabricated cockpit).
  - Suggested status code **409** (request valid, conflicts with current market state); 503 acceptable. The frontend keys off `reason`, not the code.
- [ ] Extend the `RealDataError` JSON body so a `market_closed` refusal can carry `next_open` (e.g. add it to the handler payload when present), without changing the existing three reasons' bodies.
- [ ] Register any new tunable (e.g. a market-status **poll interval** if the backend owns one, or a clock cache TTL) in `app/config.py` — **no inline literal** in engine/adapter/API code (no-magic-numbers).

### Frontend
- [ ] Replace the **hardcoded "market unavailable" pill** in `components/TopBar.tsx` (currently shown when `mode === "live"`) with a real **market-status indicator** that fetches `GET /market/clock` and renders: **open** (emerald, "market open") / **closed** (amber, "market closed — next open <time>") / **unavailable** (slate/amber, when `available:false`). Poll on mount and on a config-driven interval **only while `mode === "live"`**, and **clear the interval** on unmount / mode-change (iter-0 resource-leak lesson). The indicator **reads** row 8 — it does not recompute open/closed.
- [ ] Add a new `getMarketClock()` reader to `lib/api.ts` (GET `/market/clock`, returns the row-8 shape; any failure → `available:false`, never a fabricated status).
- [ ] Add **`"market_closed"`** to the `FailureReason` union (`lib/types.ts`) and to `HONEST_REASONS` (`app/page.tsx`), and add a **`market_closed`** case to `ProviderUnavailable.copyFor` (`components/ProviderUnavailable.tsx`) rendering the distinct phrase **"market is closed"** plus the **next open** time. The honest panel renders **in place of** the cockpit (the existing mutually-exclusive `Cockpit | ProviderUnavailable | IdleState` ternary), never alongside fabricated panels.
- [ ] Surface the backend's `next_open` through `watchTicker`'s `WatchResult` (`lib/api.ts`) and thread it into the `failure` state (`page.tsx`) so the `market_closed` panel can display the next open. Keep the existing three reasons' behavior byte-for-byte.

### New user-facing capability
A user who selects **Live** sees the **real** market session status (open / closed + next open) instead of a static "unavailable" stub, and — when they try to Watch a real symbol live **while the market is closed** — gets an explicit, honest **"market is closed (with the next open)"** screen instead of a cockpit. No fabricated tape is ever shown for the closed market.

### New information displayed
- The live **market-status indicator**: market **open** / **closed** + **next open** (Data Contract row 8, read from `GET /market/clock`).
- The honest **"market is closed"** non-cockpit panel with the **next open** time (Data Contract row 9 — already-registered "market is closed" failure state).

### New user actions
None new — the existing **Watch** (Live mode) now reaches the market-closed honest state; the market-status indicator is informational (no new control/button). The data-source selector, symbol search, and Stop are unchanged.

### UI surface changes
Still **exactly one screen** (`/` — Watch — HOME). Changes are confined to the persistent **TopBar** (the Live market-status indicator) and the existing honest non-cockpit panel (`ProviderUnavailable`) gaining a `market_closed` variant. No new route, no new page.

### Product surface delta
The Live mode stops "lying small" (a permanent "unavailable" stub) and tells the truth about the session, and the last of J-14's honest edge cases is covered — so every real-data **failure** mode (no creds, untradable symbol, empty window, **market closed**) now surfaces its own distinct, explicit state with no fabricated cockpit. Live **streaming** itself is still honestly absent (`provider_not_implemented`) until iter-4.

### Blueprint conformance
**No blueprint edit and no re-approval needed** — every surface this iteration touches is **already registered** in the approved `blueprint.md`:
- **Information Architecture** already lists, in the Live app shell, the *"market-status indicator (open/closed, from `GET /market/clock`)"* and the canonical home **J-14 → the honest non-cockpit states**; everything stays on the single `/` HOME screen.
- **Data Contract row 8** *(Market clock — open/closed + next open/close · computing owner: vendor-agnostic adapter / market-clock module · serving endpoint: `GET /market/clock` · read by the live market-status indicator)* is already a registered (to-build) row — this iteration *builds* it exactly as specified.
- **Data Contract row 9** already enumerates *"market is closed"* as a registered honest failure state.
This is a purely **additive build into** the existing IA + Data Contract; the nav skeleton is unchanged, so no `blueprint.reapproval-requested` is written.

### Data-contract additions
**None new.** Row 8 and the row-9 `market is closed` state already exist in `blueprint.md`. Singularity rules this iteration MUST honor (coherence guardrails):
- The market clock has **one** computing owner (the vendor adapter's `get_market_clock()`) and **one** serving endpoint (`GET /market/clock`). The **TopBar indicator reads `GET /market/clock`**; the **`POST /watch` pre-flight gate reads `adapter.get_market_clock()` directly** (the same computing owner — *not* a second endpoint, *not* a recomputation), exactly mirroring how the row-9 availability gate already reads `adapter.is_available()`. Do **not** add a second clock lookup, a second endpoint, or any client-side open/closed derivation.
- Rows 1–6 (engine snapshot) are **untouched** — this iteration adds no state/feature/serving path. The sim and historical paths must stay behavior-identical (empty diff in engine, config-engine math, serializers, `providers/base.py`, `providers/simulated.py`, `providers/historical.py`).

## OUT OF SCOPE

- **J-12 live streaming (the real Alpaca WebSocket)** — the async provider interface, the live feeder, real-time trade/quote ingestion. Deferred to **iter-4**. A live watch with creds + open market intentionally still returns `provider_not_implemented` this iteration.
- **J-15 stale-on-gap → recover watchdog** — belongs with the live push feeder (iter-4); there is no live gap to detect without the socket. (The `stale` dot mapping already exists in `TopBar` and `set_stream_status` already accepts it — no work needed now.)
- Any change to the engine, classifier, feature math, serializers, or the simulated/historical providers.
- Market-local (ET) tz conversion is optional polish; explicit ISO/UTC is sufficient.
- A persistent/cached asset universe change, L2 book, or any new vendor.

## DEFINITION OF DONE

- [ ] **J-14 passes** (4/4): the no-creds, untradable-symbol, empty-window, **and market-closed** cases each surface an explicit, distinct honest state with **no engine created** (post-refusal `GET /tape/{ticker}/state` → 404) and no fabricated tape. Verified by browser-qa where the wall-clock permits, and authoritatively by the deterministic backend integration test (FakeAdapter clock=closed) — consistent with goal.md's "closed-market path is verifiable without a live feed."
- [ ] `GET /market/clock` (row 8) returns the open/closed + next-open/close shape with creds, `available:false` (nulls) without creds, and degrades to `available:false` on adapter error — never a fabricated status.
- [ ] The Live **market-status indicator** renders the real session status from `GET /market/clock` (open / closed + next open / unavailable) and cleans up its poll on unmount/mode-change.
- [ ] Required-still-passing journeys remain green: J-01–J-11 and J-13 (the sim cockpit, absorption pair, transitions, SSOT, stop/re-watch, data-source reveal, historical replay, symbol search). The sim + historical paths are behavior-identical (engine/config/serializers/`providers/base.py`/`providers/simulated.py`/`providers/historical.py` show an empty diff).
- [ ] No anti-goal violation introduced — independently checked via `git diff`: the `alpaca` SDK import + the vendor name stay confined to `providers/adapters/alpaca.py` (SDK-confinement + credential-confinement tests pass unchanged); no secret committed (`.env` untracked; `.env.example` values stay empty); no broker/order/execution code; the market clock is read-only.
- [ ] Unit/integration tests pass; no regressions in the full backend suite.
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich-iter-3-dev.md`. (Process note: iter-2 produced **no audit handoff** — this full-depth iteration should run the complete pipeline incl. the post-QA **audit**, **coherence-auditor**, and **closure** gates, since row 8 transitions from registered-to-built.)

## TESTING REQUIREMENTS

- **Browser (Chrome MCP):**
  - **J-14 (market closed):** with the env's real Alpaca creds, select **Live**, observe the **market-status indicator** showing the real session status; if the session is closed at run time, Watch a real symbol (e.g. `AAPL`) and confirm the honest **"market is closed — next open …"** panel renders **in place of** the cockpit (no quote/trades/state panels). If the market is open at run time, document that and rely on the deterministic backend test for the closed-refusal branch (note which branch was observed — the iter-2 creds-present convention).
  - **Regression smoke:** Simulated `SIM-BUYER` still resolves to **buyer_control** (J-01/J-02/J-10); a Historical replay still populates the cockpit (J-11); symbol search still fills the box (J-13); Stop returns to idle (J-09).
- **Unit/integration (pytest, hermetic via `FakeAdapter` + `dependency_overrides`):**
  - `GET /market/clock`: open → `available:true,is_open:true`; closed → `is_open:false` with a non-null `next_open`; no creds (`available=False`) → `available:false` with null fields; adapter raises → `available:false` (no fabrication).
  - `POST /watch` **live, market closed** (FakeAdapter `is_open=False`) → distinct `market_closed` refusal at the chosen 4xx/503 with `next_open` in the body, **and `GET /tape/{ticker}/state` → 404** (no engine).
  - `POST /watch` **live, market open** (FakeAdapter `is_open=True`, no streaming yet) → still `provider_not_implemented` (documents the honest iter-4 boundary; no fabricated cockpit).
  - **Distinctness:** the four real-data refusal reasons are pairwise distinct — `provider_unavailable`, `symbol_not_tradable`, `no_data_for_window`, `market_closed`.
  - **Confinement (must stay green, unchanged):** `import alpaca` and the `ALPACA_API_*` names remain confined to `providers/adapters/alpaca.py`; the engine/config/serializers/`providers/base.py`/`providers/simulated.py` reference no vendor. Extend `FakeAdapter` with a configurable clock (open/closed/unavailable).
- **Error cases that MUST be rejected / handled honestly:**
  - Live watch while market closed → explicit `market_closed` + next open, no engine (NOT a cockpit, NOT a fall-back to sim).
  - `GET /market/clock` with no creds → explicit `available:false`, never a guessed open/closed.
  - Live watch with creds + open market → honest `provider_not_implemented` (streaming is iter-4), never a fabricated cockpit.

## NOTES

- **Why one target journey at full depth:** J-14's completion is small in code but high in value (it closes the honest-edge-case set) and it builds an entire registered contract row (row 8) plus visible Live UI, while deliberately isolating the risky async-socket refactor to iter-4. This keeps the iteration tight and the evaluator's verdict crisp (a clean J-14 pass + row-8 build), rather than a muddy "J-14 passes / J-12+J-15 advance to partial" result.
- **Correcting an iter-2 forward-note:** the iter-2 evaluator expected row 8 to need *"a `blueprint.md` edit + re-approval."* It does **not** — row 8 (and the market-status indicator in the IA, and "market is closed" in row 9) were registered in the baseline blueprint, so this iteration builds into the approved structure with **no** re-approval pause.
- **iter-4 tee-up (for the next decomposer/developer):** the live half — J-12 (real Alpaca live WebSocket behind the seam; an **async** provider/feeder since the current `Provider.stream()` is synchronous) and J-15 (stale-on-gap → recover watchdog, fabricating no trades during the lull) — both **operator/gated** for real-socket behavior. The market clock built here is J-12's pre-flight "is the market open" check. Reuse the cancellable feeder/teardown so a live socket is never orphaned on switch/stop (iter-0 lesson); the `stale` dot + `set_stream_status` already exist.
- **No fabricated data is the throughline:** every branch added here that cannot serve real data returns an explicit, distinct state and creates no engine — verified by the `…/state` → 404 assertions and the distinct-reason test.
