# goal-i_will_be_super_rich-iter-4 Execution Plan

Frontend Present: yes

> **The live half — real-time streaming (J-12) + stale-on-gap → recover (J-15).** Close the
> **last two failing journeys**. Introduce an **async** streaming variant of the existing provider
> seam (today's `Provider.stream()` is synchronous/bounded; a live feed is async/unbounded), wire
> the real Alpaca live WebSocket behind the existing vendor-neutral adapter, and add the
> **stale watchdog** that owns the row-6 `stream_status` flip on a feed gap (fabricating no trades).
> The Live `POST /watch` branch stops refusing (`provider_not_implemented` 503) and starts streaming.
> **Engine, classifier, serializers, and the synchronous providers stay 0-diff**; the frontend needs
> **no new code** (the TopBar dot already renders `live`/`stale` from the canonical snapshot).

## Goal alignment (no drift)

Matches `docs/goal.md` exactly: J-12 ("Stream a real live ticker") and J-15 ("A live-feed gap shows
`stale`, then recovers") are the two remaining failing must-have journeys, both enumerated under the
**Live real data** and **Real-data honesty** success criteria. All critical anti-goals are explicitly
honored: no-execution (live socket subscribes to market data only — no order/account/position call),
no-fabricated-data (the watchdog synthesizes nothing during a lull; no sim fall-back on failure),
single-source-of-truth (live flows through the same rows 1–6; REST == WS), provider-agnostic
(vendor SDK confined to `alpaca.py`), no-magic-numbers (`stale_gap_seconds` in config), no-secrets.
Correctly OUT OF SCOPE: L2/`BookLevelEvent`, ML, persistence, multi-symbol live, auto-reconnect of a
dropped socket, any threshold loosening, any broker/order code. **No scope creep flagged.**

## What to Build

**Backend** (every vendor specific stays confined to `providers/adapters/alpaca.py`)

- **Async provider seam (additive — sync path 0-diff).** Add an async streaming Protocol
  (e.g. `LiveProvider`/`AsyncProvider` with `async def stream() -> AsyncIterator[Event]`) to
  `providers/base.py`. The existing synchronous `Provider`, `simulated.py`, and `historical.py`
  must show an **empty diff**. The engine still consumes via the unchanged `engine.process_event`.
- **`LiveProvider` (`providers/live.py`, NEW, vendor-neutral).** Consumes the adapter's async stream
  of neutral `RawTrade`/`RawQuote` and yields ordered `QuoteEvent`/`TradeEvent`, mapping each real
  UTC epoch onto the engine's **logical timeline** (quote-before-trade at equal instants, monotonic
  non-decreasing offsets — the same neutral→logical mapping `HistoricalProvider` does, but
  async/unbounded). Trades carry `Side.UNKNOWN` (engine re-derives the aggressor).
  `scenario = f"live {ticker}"`. Imports **no** vendor SDK.
- **Alpaca live method (`adapters/alpaca.py` ONLY — the single vendor module).** Add
  `async def stream_live(symbol)` (or a subscribe-bridge) using `alpaca.data.live.StockDataStream`
  (**lazy import**, the sole place the live SDK is named), subscribing to **trades + quotes for the
  one symbol** and emitting neutral `RawTrade`/`RawQuote`. On cancel/close it MUST **unsubscribe and
  close the socket** (no leak). It places/echoes **no order** and calls **no** trading/account/
  position API. Declare `stream_live` on the `MarketDataAdapter` Protocol in `adapters/base.py`.
- **Async live feeder + stale watchdog (`watch_manager.py`).** Add `watch_with_async_provider(ticker,
  provider)` + an async `_feed_live` that: (1) tears down any prior watch for the ticker first
  (iter-0 orphaned-watch lesson); (2) processes each event into the engine and **explicitly ensures
  the status reads `live`** — note the engine only auto-flips `connecting`→`live`, NOT `stale`→`live`,
  so the feeder owns the recovery flip; (3) if **no event arrives within `CONFIG.stale_gap_seconds`**
  (`asyncio.wait_for(next_event, stale_gap_seconds)`), sets `engine.set_stream_status("stale")` and
  **fabricates no trades** during the lull; (4) flips back to `live` on the next event; (5) on cancel
  (stop/switch/shutdown) cancels the task, **closes the vendor socket**, and sets `closed`.
- **`POST /watch/{ticker}` live branch (`main.py`).** Replace the `provider_not_implemented` (503)
  refusal with the real path: `adapter.is_available()` (else `provider_unavailable` 503) → the
  **existing** market-clock open pre-flight (`adapter.get_market_clock()` — the **same** computing
  owner; authoritative `is_open is False` → `market_closed` 409 with `next_open`, **no engine**; do
  **not** add a second clock) → build `LiveProvider` from `adapter.stream_live(...)` and start it via
  `watch_with_async_provider`. Return `{ticker, scenario: "live <SYM>", status: "watching"}`. No sim
  fall-back on any failure.
- **Config (`config.py`).** Add `stale_gap_seconds` (named field — no inline literal). Add any other
  live tunable only if actually used.

**Frontend — verification-only (no code change expected)**

- **Verify** the live happy path renders the existing cockpit: a successful Live watch sets the
  ticker → `Cockpit` renders + `useTapeStream` connects → the TopBar dot reads
  `snapshot.stream_status` and shows **live** (emerald) / **stale** (amber), and the watched-source
  label shows `live <SYM>`. (Confirmed already present: `TopBar.tsx` snapshot-driven status map maps
  `live`→emerald, `stale`→amber, `closed`→rose; `MarketStatusIndicator` + Live symbol-search render.)
- Make a **minimal** wiring fix **only if** a concrete gap is found; any frontend change must trace to
  this checkbox. Do not refactor or restyle.

## Agents Required

- **developer: yes** — implements the async seam, `LiveProvider`, the Alpaca live method, the async
  feeder + stale watchdog, the live `POST /watch` branch, the `stale_gap_seconds` config field, and
  all hermetic + gated tests; verifies (and only minimally wires) the frontend.
- **backend-data: yes**
- **frontend-ux: no** (verification-only; no frontend code change expected — browser QA re-verifies
  no-regression journeys and that the Live controls/cockpit/dot render)

## Files to Create/Modify

- `apps/backend/app/providers/base.py` — add the async `LiveProvider`/`AsyncProvider` Protocol +
  `AsyncIterator` import. **Sync `Provider` unchanged (0-diff).**
- `apps/backend/app/providers/live.py` — **NEW.** `LiveProvider` async neutral→logical mapping.
- `apps/backend/app/providers/adapters/base.py` — add `stream_live` to the `MarketDataAdapter` Protocol.
- `apps/backend/app/providers/adapters/alpaca.py` — add `stream_live()` (lazy `StockDataStream`,
  subscribe trades+quotes, neutral emit, **unsubscribe + close socket on cancel**). SOLE vendor module.
- `apps/backend/app/watch_manager.py` — add `watch_with_async_provider` + `_feed_live` + stale
  watchdog + socket-close-on-cancel.
- `apps/backend/app/main.py` — replace the live `provider_not_implemented` refusal with the real live
  path (reuse the existing clock pre-flight — **no second clock**).
- `apps/backend/app/config.py` — add `stale_gap_seconds`.
- `apps/backend/tests/fakes.py` — add an async `FakeLiveProvider` and extend `FakeAdapter` with an
  async `stream_live` that records close/unsubscribe. **Test-only — NEVER wired into the prod live path.**
- `apps/backend/tests/test_real_data_gate.py` — **UPDATE** the live+creds+**open-market** tests that
  currently assert `provider_not_implemented` (lines ~131–165) to assert a **started watch** via the
  fake async seam (the intended behavior change, not a regression). No-creds `provider_unavailable` +
  `market_closed` branches stay.
- `apps/backend/tests/test_live_provider.py` (and/or `test_watch_manager.py` additions) — **NEW**
  hermetic async tests (pipeline/SSOT, stale→recover, lifecycle/socket-close, vendor confinement).
- **Operator/gated integration check** — a `@pytest.mark.integration` test or a documented operator
  script that connects to the **real** Alpaca live WebSocket during market hours.
- `runs/goal-session-i_will_be_super_rich/state/blueprint.md` — **already carries** the additive
  async-seam clarification (sync vs async variant; the live feeder as the single row-6 `stream_status`
  owner that flips to `stale`). Additive, non-nav → **no re-approval; no further edit required.**

## UI Evolution (Frontend Present: yes)

- **New user-facing capability:** the Live **Watch** action now actually **streams** (was refused with
  `provider_not_implemented`). Select Live → search/enter a real symbol → Watch → the single-ticker
  cockpit streams real-time trades + quotes with status reading **live**; a feed lull shows **stale**
  (no invented trades); recovers to **live** when data resumes.
- **New information displayed:** no new *value*. Row-6 `stream_status` now takes its `live`/`stale`
  values from a **real live feed** (previously only `connecting`/`closed` from sim/historical). The
  watched-source label now includes the `live <SYM>` descriptor.
- **New user actions:** none beyond the existing selector → Live → search/enter → **Watch** / **Stop**.
- **UI surface changes:** none — still exactly one screen (`/`); cockpit body identical across modes.
- **Navigation changes:** none.

## Visual Requirements (Frontend Present: yes)

- **Component patterns:** existing hand-built cockpit panels; the TopBar **status dot** (snapshot-driven
  map already maps `live`→emerald, `stale`→amber, `closed`→rose). No new components.
- **Layout:** unchanged single-screen tape cockpit (panel grid; single-column → 2-col md → 3-col lg).
- **Key visual effects:** restrained, per DESIGN SYSTEM — status-dot color semantics (emerald = live,
  amber = stale/absorption/unclear), confidence bar. All already present.
- **States to handle:** `live` (streaming), `stale` (amber dot, no new trades), `closed` (after Stop),
  plus the existing honest non-cockpit states (`provider unavailable` / `market is closed`). All already
  rendered — **no new visual work expected.**

## Key Test Scenarios

- **J-15 (hermetic async, primary in-loop proof):** with `stale_gap_seconds` overridden small,
  live → (gap > timeout) → **`stale`** → (resume) → **`live`**, asserting the exact status transitions
  AND that the recent-trades count is **unchanged across the lull** (no fabricated trades).
- **J-12 (hermetic async):** a test-only async `FakeLiveProvider`/`FakeAdapter` behind the seam feeds
  real-shaped quotes+trades → snapshot populates, `stream_status == "live"`, tape state + confidence
  classify, and the **REST projection equals the WS/`summary` projection** (single source of truth).
- **Live lifecycle (socket-leak — load-bearing, iter-0):** `stop()` / a source-or-symbol switch cancels
  the live feeder **and** closes the fake vendor socket (assert close/unsubscribe invoked); `…/state`
  then 404s — no orphan, no leak.
- **Vendor confinement:** `import alpaca` / "Alpaca" / `StockDataStream` appear **only** in
  `adapters/alpaca.py` (git grep / test); engine + sync providers + serializers show a **0-line diff**.
- **Error cases:** live + no creds → `provider_unavailable` (503, no engine); live + market closed →
  `market_closed` (409 + `next_open`, no engine — reuse existing gate); feed gap → `stale` (nothing
  synthesized); stop/switch → socket closed.
- **External integration (operator/gated, out-of-loop):** the real Alpaca live socket during market
  hours → a real `live` read + classification. The handoff MUST state honestly whether this was run and
  the outcome (see Assumption #2).
- **Browser (no-regression + controls render):** J-01, J-02 (SIM-BUYER → buyer_control), J-10 (mode
  selector reveal), J-11 (historical AAPL replay populates), J-13 (symbol search fills box), J-14
  (honest non-cockpit states); Live mode reveals symbol search + market-status indicator and the
  cockpit/dot render on a successful watch.
- **Suite:** backend unit/integration green (iter-3 baseline 118 passed, exit 0) with the new tests
  added; no regressions. Frontend builds in an **isolated `.next`** (iter-3 QA caution).

## Assumptions & Flags (documented, not blocking — per `.claude/core.md`)

1. **No scope drift.** Spec ⇄ `docs/goal.md` align exactly; all critical anti-goals honored. No creep.
2. **Operator/gated real-socket run is out-of-loop and likely NOT executable this loop.** Creds are
   present in `apps/backend/.env` (per iter-3), but today (2026-06-04) the US market is **closed**
   (iter-3 observed `is_open=False`), so the real live read cannot be exercised in-loop. The **hermetic
   async fake is the in-loop proof** (the evaluator accepted the analogous hermetic `FakeAdapter` for
   J-14). Per core.md External Integration Testing, the mocked suite alone is NOT sufficient evidence the
   real integration works — so the runnable gated check MUST be real, and the handoff MUST document
   honestly that it was not run (off-hours/market closed) with the mechanism provided + verified.
3. **Engine auto-flips `connecting`→`live` only, NOT `stale`→`live`** (`tape_engine.py:69-70`). The live
   feeder must EXPLICITLY re-set `live` on the first event after a stale gap.
4. **`test_real_data_gate.py` live+open-market semantics change** from `provider_not_implemented` to a
   started watch (via the fake async seam) — intended, not a regression.
5. **Frontend genuinely needs no code.** `TopBar.tsx` already renders `live`/`stale`/`closed` from
   `snapshot.stream_status`; the scenario label flows through. `Frontend Present: yes` reflects that the
   user-facing Live capability becomes real and browser QA must re-verify — not that a frontend file
   changes (any change must trace to the verification checkbox).
6. **`blueprint.md` already carries the additive async-seam clarification** — additive, non-nav → no
   re-approval, no further edit required from the developer.
7. **Socket-close-on-cancel is first-class + tested** (iter-0): a leaked live socket is a real connection
   leak, unlike the in-memory sim.

## Done = the last two journeys close

Closing **J-12 + J-15** with **zero regressions** (engine/classifier/serializers/sync-providers 0-diff;
all 13 required-still-passing journeys green) clears the final two failing must-have journeys → the
evaluator can consider **GOAL_ACHIEVED**.
