# Goal Iteration 4 — Live real-time streaming (J-12) + stale-on-gap → recover (J-15)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich
- **Iteration:** 4
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes (verification-focused — no frontend code change expected; see Frontend scope)
- **Target journeys:** J-12, J-15
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-13, J-14
- **Anti-goal reminders (verbatim from `docs/goal.md`; the *critical* ones for this iteration first):**
  - **No fabricated data.** The system MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. Every real-data failure mode MUST surface an explicit, distinct state and never a cockpit: a provider gap/feed lull → `stale`; an unknown/untradable symbol → an explicit error; an empty historical window → explicit no-data; a live watch while the market is closed → explicit closed (with the next open); missing credentials → explicit "unavailable". Falling back to simulated or invented data to mask a real-data failure is a defect. *(critical)*
  - **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the tape. *(critical)*
  - **Provider-agnostic engine.** The engine and API MUST depend only on the provider interface (TradeEvent / QuoteEvent / BookLevelEvent); swapping the simulator for a real feed — live or historical — MUST NOT require engine or API changes. A concrete vendor SDK MUST appear in only one adapter module behind a vendor-neutral seam, so a second vendor is one new adapter; vendor specifics MUST NOT leak into the engine, providers, or API.
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*
  - **Honest uncertainty.** When evidence is weak or mixed, the spread is wide, or there is no clean price impact, the state MUST be `unclear` with low confidence. The system MUST NOT manufacture a directional call to look decisive. *(critical)*
  - **Price impact over raw aggression.** The classifier MUST distinguish absorption from control: a tape with high one-sided aggression but no corresponding price progress MUST resolve to the matching absorption state (bid_absorption / ask_absorption), never to seller_control / buyer_control. *(critical)*
  - **No secrets in source.** Real-vendor API keys/tokens MUST come only from environment/config and MUST NOT be committed; with no keys the app runs simulator-only and real modes report an explicit "unavailable" rather than failing opaquely or fabricating data.
  - **Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine MUST produce identical features, state, and confidence; classification MUST NOT depend on wall-clock time or randomness.
  - **No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code.

## GOAL

Watching a real US symbol in **Live** mode (credentials configured, market open) streams the vendor's **real-time** trades + quotes through the **same** engine and classifies the live tape state + confidence with the status reading **live** (J-12); and when the live feed goes quiet beyond a configured window the status honestly flips to **stale** — fabricating no trades — then returns to **live** when events resume (J-15). These are the **last two failing journeys**; closing them with zero regressions completes the must-have set.

## BACKGROUND

iter-3 closed J-14 and built the market clock (Data Contract row 8), turning the Live market-status indicator real, but deliberately left the live-streaming half (J-12, J-15) for iter-4. The genuine architecture change isolated here: today's provider seam is **synchronous** (`Provider.stream() -> Iterable[Event]`), iterated eagerly by the `WatchManager` feeders — fine for the finite sim/historical streams, but a live feed is **async and unbounded**. So this iteration introduces an **async streaming variant of the provider seam** and wires the real Alpaca live WebSocket behind the existing vendor-neutral adapter, plus the **stale watchdog** that owns the row-6 `stream_status` flip on a feed gap.

Most of the surface already exists and must be reused, not rebuilt:
- `stream_status` is **already** Data Contract row 6 (`connecting | live | stale | closed`), owned by the engine/feeder; `engine.set_stream_status(...)` exists; the TopBar dot already renders `stale` as **amber** reading the canonical `snapshot.stream_status`; the Live controls + `MarketStatusIndicator` already render. So the **frontend needs no new code** — once the backend live watch creates an engine and flips the status, the cockpit and dot just work.
- `alpaca-py==0.43.4` is already a dependency and allowlisted (iter-2); `alpaca.data.live.StockDataStream` is the live socket client — **no new package install, no supply-chain gate this iteration**.
- `env.load_env()` is wired and the adapter reads `ALPACA_API_KEY` / `ALPACA_API_SECRET` (the iter-1 cred-name trap is resolved) — so the operator/gated credentialed run can load `.env`.
- iter-3's `adapter.get_market_clock()` is the live pre-flight open-check (reuse it — do **not** add a second clock); the cancellable feeder + `stop()`/`teardownActiveWatch` teardown already exist.

**Per `docs/goal.md`, J-12 and J-15 real-socket behavior is confirmed by an operator/gated credentialed run** (live data needs market hours + keys); the Live controls/status render without a feed, and the **honest-degradation + state-machine behavior is verifiable hermetically in-loop** (a test-only async fake behind the seam) — exactly how iter-3 verified the market-closed gate with a hermetic `FakeAdapter` and iter-2 used a committed real fixture. Decide this verification strategy up front (lesson iter-1).

**Lessons applied (from `lessons.md`):**
- **iter-0 (critical here):** switching/stopping a watch must tear down the prior watch — for a real socket this is a genuine **vendor WebSocket/connection leak**, not a harmless sim no-op. The live feeder MUST close the vendor socket on cancel (stop/switch/shutdown). Reuse the existing task-cancel teardown and add socket close.
- **iter-1:** env-var names align to `adapters/alpaca.py` and `load_env()` exists; the operator/gated run only needs `.env` filled. Plan the credentialed verification path before building (done — see Testing).
- **iter-2:** the free **IEX** top-of-book is wide for high-priced names, so a high-priced live symbol may honestly read **`unclear`** (correct — do not loosen the spread gate, it would regress J-01–J-09). For an operator clean-state live demo, prefer a **tight/penny-spread** name.
- **iter-3:** QA must build the frontend in an **isolated `.next`** (never the harness's shared one) and must never `git checkout` a file carrying uncommitted iter edits.

## IN SCOPE

### Backend

- [ ] **Async provider seam (additive — do not disturb the sync path).** Add an **async** streaming variant to the provider interface (e.g. an `AsyncProvider` / `LiveProvider` Protocol with `async def stream() -> AsyncIterator[Event]`) in `app/providers/base.py`, leaving the existing synchronous `Provider` Protocol and the simulated/historical providers **0-diff**. The engine consumes events through the unchanged `engine.process_event(event)` — no engine change.
- [ ] **`LiveProvider` (vendor-neutral, `app/providers/live.py`).** Consumes the adapter's live stream of vendor-neutral `RawTrade` / `RawQuote` records and yields ordered `QuoteEvent` / `TradeEvent`, mapping each real UTC epoch onto the engine's **logical timeline** (quote-before-trade preserved at equal instants, monotonic non-decreasing offsets) — the same neutral→logical mapping `HistoricalProvider` does, but async/unbounded. Trades carry `Side.UNKNOWN` (the engine re-derives the aggressor). `scenario = f"live {ticker}"` so the row-6 watched-source descriptor renders verbatim. Imports **no** vendor SDK.
- [ ] **Alpaca adapter live method (`app/providers/adapters/alpaca.py` ONLY — the single vendor module).** Add a live-stream method (e.g. `async def stream_live(symbol)` / a subscribe-bridge) that uses `alpaca.data.live.StockDataStream` (lazy import, the SOLE place the live SDK is named), subscribes to **trades + quotes for the one symbol**, and emits vendor-neutral `RawTrade` / `RawQuote`. On cancel/close it MUST unsubscribe and **close the socket** (no leak). It places/echoes **NO order** and calls **no** trading/account/position API (no-execution anti-goal). Declare the method on the `MarketDataAdapter` Protocol in `adapters/base.py`.
- [ ] **Async live feeder + stale watchdog (`app/watch_manager.py`).** Add `watch_with_async_provider(ticker, provider)` + an async `_feed_live` that: tears down any prior watch for the ticker first (iter-0 orphaned-watch lesson); processes each event into the engine and ensures the status reads **`live`**; if **no event arrives within `CONFIG.stale_gap_seconds`**, flips `engine.set_stream_status("stale")` and **fabricates no trades** during the lull; flips back to **`live`** on the next event; on cancel (stop/switch/shutdown) cancels the task, **closes the vendor socket**, and sets **`closed`**. The watchdog timeout MUST be config-driven (see Config) and the mechanism deterministic enough to test with a small override (e.g. `asyncio.wait_for(next_event, stale_gap_seconds)`).
- [ ] **`POST /watch/{ticker}` live branch (`app/main.py`).** Replace the `provider_not_implemented` (503) refusal with the real path: `adapter.is_available()` → the **existing** market-clock open pre-flight (`adapter.get_market_clock()`, the same computing owner — **no second clock**; authoritative `is_open is False` → `market_closed` 409 with next open, no engine) → build the `LiveProvider` from `adapter.stream_live(...)` and start it via `watch_with_async_provider`. Return `{ticker, scenario: "live <SYM>", status: "watching"}`. Missing creds stays `provider_unavailable` (503). No fabricated cockpit, no sim fall-back on any failure.
- [ ] **Config (`app/config.py`) — no magic numbers.** Add `stale_gap_seconds` (the live stale watchdog timeout the blueprint already anticipates). Add any other new live tunable (e.g. a reconnect/backoff bound) only if used — each as a named config field, never an inline literal.

### Frontend (verification-focused — no code change expected)

- [ ] **Verify** the live happy path renders the existing cockpit: a successful Live watch (`result.ok`) sets the ticker → `Cockpit` renders + `useTapeStream` connects the WS → the TopBar dot reads `snapshot.stream_status` and shows **live** (emerald) / **stale** (amber) verbatim, and the watched-source label shows **`live <SYM>`**. The `MarketStatusIndicator` and Live symbol-search controls already render.
- [ ] Only if a concrete gap is found during verification, make the **minimal** wiring fix (e.g. ensure the live `scenario` label flows through). Do not refactor or restyle. Any frontend change must trace to this checkbox.

### New user-facing capability

A user can select **Live**, search/enter a real symbol, press **Watch**, and — during market hours with credentials configured — see the single-ticker cockpit stream the vendor's real-time trades + quotes with the status reading **live**; if the feed goes quiet the status shows **stale** (no invented trades) and recovers to **live** when data resumes.

### New information displayed

No new displayed *value*. The already-registered row-6 `stream_status` now takes its `live` and `stale` values from a **real live feed** (previously only `connecting`/`closed` from sim/historical). The watched-source label now includes the `live <SYM>` descriptor.

### New user actions

None beyond the existing data-source selector → Live → search/enter symbol → **Watch** / **Stop** (all already present). This iteration makes the Live **Watch** action actually stream.

### UI surface changes

None. Still exactly one screen (`/`); the cockpit body is identical across sim/historical/live.

### Product surface delta

The Live mode transitions from "controls render but watching is refused (`provider_not_implemented`)" to a **working real-time tape read** with an honest live/stale status — completing the real-data half of the product.

### Blueprint conformance

All work lives on the existing **`/` — Watch (the tape cockpit) — HOME**; J-12 → Live controls + status → cockpit, J-15 → stream-status dot (live ⇄ stale) — both are already the registered canonical homes. No new route, no new page, no nav-skeleton change → **no blueprint re-approval required.** A single **additive architectural clarification** is added to `blueprint.md`'s provider-seam note (the async streaming variant is the same seam; the live feeder is the one owner that flips row-6 `stream_status` to `stale`) — additive, non-nav, no re-approval.

### Data-contract additions

**None.** `stream_status` (live/stale) is already **row 6** (owned by the engine/feeder). The live read flows through the **same** rows 1–6 — real live data adds **no** parallel state/feature/quote/trades path and **no** second `stream_status` owner. Symbol search (row 7), market clock (row 8), and the availability/failure state (row 9) are reused unchanged (the live pre-flight reads the row-8 owner directly — no second clock). The vendor live SDK is confined to the existing one adapter module (the architectural singularity, not a displayed value).

## OUT OF SCOPE

- Any change to the engine, classifier, feature windows, serializers, or the synchronous `Provider` / `SimulatedProvider` / `HistoricalProvider` (they must stay behavior-identical — 0-diff — so J-01–J-11 cannot regress).
- Level 2 / `BookLevelEvent`, `liquidity_pull_score`, extended states, ML, persistence, the predictive-edge harness (all explicitly *later* in `docs/goal.md`).
- A market-local / timezone window picker, multi-symbol live, or any new page/route/watchlist.
- Loosening any spread/impact/confidence threshold to make a high-priced live name read "control" (would regress J-01–J-09; a wide-IEX-spread name reading `unclear` is correct).
- Auto-reconnect of a *dropped* socket is **not** a hard requirement (a drop honestly shows `stale` until resume/stop); it may be added as operator-path robustness but must not expand scope or risk the green journeys.
- Any broker/order/execution/account/position code (anti-goal — never).

## DEFINITION OF DONE

- [ ] **J-15** verified in-loop: a hermetic async test (test-only fake provider/adapter behind the seam) drives **live → (gap > `stale_gap_seconds`) → `stale` → (resume) → live**, asserting the status transitions exactly and that **no trades are fabricated during the gap** (recent-trades count unchanged across the lull). Real-socket behavior additionally confirmed by the operator/gated credentialed run (mechanism provided; result documented honestly).
- [ ] **J-12** verified to the extent in-loop verifiable: a hermetic async test drives the full live pipeline (async feeder → engine → snapshot → REST/WS) so the cockpit values populate, `stream_status == "live"`, the tape state + confidence classify, and **REST == WS** (single source of truth); **and** the Live controls + market-status indicator render (browser). The **real Alpaca live socket** is confirmed by the operator/gated credentialed run during market hours — provided as a runnable, documented check; its result is stated honestly in the dev handoff (e.g. "not run in autonomous loop: off-hours / no creds — mechanism verified").
- [ ] All 13 required-still-passing journeys remain green. The engine, classifier, serializers, and the synchronous providers (`base.py` sync `Provider`, `simulated.py`, `historical.py`) show a **0-line diff**; the sim + historical paths are behavior-identical (re-verify J-01/J-02/J-10/J-11/J-13/J-14 by browser; J-03–J-08 carried on the empty-diff guarantee + green suite).
- [ ] No anti-goal violation: vendor live SDK + names confined to `alpaca.py` (`git grep` clean elsewhere — including the new live method); **no** order/account/position/trading call anywhere in the adapter; the stale watchdog fabricates nothing; the live path never falls back to sim; test fakes live under `tests/` and are **never** wired into the production live path; no secrets committed (`.env` untracked, `.env.example` empty values); SSOT preserved (live flows through rows 1–6).
- [ ] The live feeder closes the vendor socket on stop/switch/shutdown — no orphaned watch / leaked socket (asserted by a lifecycle test).
- [ ] Backend unit/integration suite passes (the iter-3 baseline was 118 passed, exit 0) with the new tests added; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich-iter-4-dev.md`, explicitly stating whether the operator/gated real-socket integration check was run and its result (honest, not minimized — per `.claude/core.md` External Integration Testing).

## TESTING REQUIREMENTS

- **Browser (no-regression + controls render):** re-verify J-01, J-02 (SIM-BUYER → buyer_control), J-10 (mode selector reveal), J-11 (historical AAPL replay populates), J-13 (symbol search fills box), J-14 (honest non-cockpit states); confirm Live mode reveals symbol search + market-status indicator and the cockpit/dot render on a successful watch. (J-12/J-15's *live feed* itself is operator/gated, not a browser-against-live-market test.)
- **Unit/integration (hermetic, deterministic — primary in-loop evidence):**
  - Async live pipeline: a **test-only** `FakeLiveProvider`/`FakeAdapter` (async, behind the seam) feeds real-shaped quotes+trades → engine snapshot populates, `stream_status == "live"`, state classifies, and the REST projection equals the WS/`summary` projection (SSOT).
  - Stale → recover state machine: with `stale_gap_seconds` overridden small, prove live → `stale` (on no-event-within-timeout, **no trades fabricated**) → `live` (on resume).
  - Live lifecycle: `stop()` / a source-or-symbol switch cancels the live feeder **and** closes the fake vendor socket (assert close/unsubscribe was invoked) — no leak; `…/state` then 404s.
  - Vendor confinement: assert (test or `git grep`) that `import alpaca` / "Alpaca" / `StockDataStream` appear only in `adapters/alpaca.py`; engine + sync providers unchanged.
- **External integration (operator/gated — out-of-loop):** at least one check (`@pytest.mark.integration` or a documented operator script) that connects to the **real** Alpaca live WebSocket during market hours with credentials and confirms a real `live` read + classification. Per `.claude/core.md`, the mocked/hermetic suite alone is **not** sufficient evidence the real integration works; the handoff must document whether this was run and the outcome.
- **Error cases:** live + no credentials → `provider_unavailable` (503, no engine); live + market closed → `market_closed` (409 with next open, no engine — reuse the existing gate); feed gap → `stale` (no synthesized trades); stop/switch → socket closed (no orphan).

## NOTES

- **Verification strategy decided up front (lesson iter-1):** the in-loop proof for J-12/J-15 is the **hermetic async fake** (a legitimate test double behind the provider seam — the same pattern as the simulator and iter-3's `FakeAdapter` clock; it is **not** production fabrication and must never be wired into the live production path). The genuine vendor socket is the **operator/gated** credentialed run per `docs/goal.md`. The evaluator decides whether this evidence marks J-12/J-15 passing (as it accepted the hermetic `FakeAdapter` for J-14) — the developer's job is to make both the hermetic and the gated mechanisms real and to document the gated result honestly.
- **iter-0 socket-leak lesson is load-bearing here:** unlike the in-memory sim, a leaked live socket is a real connection leak. Make socket-close-on-cancel a first-class, tested behavior.
- **iter-2 IEX reality:** for any operator clean-state live demo, choose a tight/penny-spread name; a high-priced name honestly reading `unclear` on the wide free IEX top-of-book is correct, not a bug — do not retune thresholds.
- **iter-3 QA caution:** build the frontend in an isolated `.next`; never `git checkout` a file with uncommitted iter edits.
- Closing J-12 + J-15 with zero regressions clears the last two failing journeys → the evaluator can consider **GOAL_ACHIEVED**.
