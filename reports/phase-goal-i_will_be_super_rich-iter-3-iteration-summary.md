# Iteration Summary — goal-i_will_be_super_rich-iter-3

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-06-04
**Iteration:** 3

## In plain words

**What you can do now:** Watch one US stock at a time — on built-in practice data or a real past session replayed from the market — and get a live, plain-language read of the tape: whether buyers or sellers are in control, whether heavy buying or selling is being absorbed while the price holds, or whether the tape is simply unclear, each with a confidence score, quote and trade readouts, observations, and an event log. You can choose the data source, find a stock by typing part of its name or ticker, replay a chosen historical window at a chosen speed, stop and restart cleanly, and — when you pick Live — see whether the US market is open or closed with the time it next opens. You always get an honest message instead of a made-up screen when real data isn't available.

**What changed this time:** When you choose Live, the top bar now shows the real US market session — "market open", or "market closed" with the time it next opens — instead of a permanent "unavailable" label. And if you try to watch a real stock live while the market is closed, you now get a clear "Market is closed" screen that tells you when it next opens, instead of a fake or empty trading screen. No prices or trades are ever invented to fill the gap.

**What's next:** Next, the product will follow a stock live, in real time, and show when the feed briefly drops out ("stale") and then recovers.

## Headline

Completed J-14: honest "market is closed" screen + a real Live market-status indicator (market clock, contract row 8).

## Direction

**Signal:** improving
**Why:** This iter newly passed J-14 (honest real-data edge cases, 3/4 → 4/4) by building the market clock (`GET /market/clock`, Data Contract row 8) end-to-end and a live market-closed pre-flight gate that refuses with a distinct `market_closed` state and creates no engine. Zero regressions across the 12 required-still-passing journeys (engine/serializers/providers base+simulated+historical show a 0-line diff; 118 backend tests pass), COHERENCE-PASS, no anti-goal violations. The last two failing journeys are the live-streaming half (J-12, J-15), deliberately deferred to iter-4.

**Trend (last 4 iters):**
- Newly passing this iter: J-14
- Newly passing in last 4 iters total: J-10, J-11, J-13, J-14
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: none
- Iters with no journey state change: 1 of last 4 (iter-0 verify-only baseline; iters 1–3 each moved a journey forward)

**Latest evaluator reasoning:** Verified J-14 directly from TC-14 (honest "market is closed" panel + next open, "never fabricates data", no cockpit) and from the backend (`POST /watch/AAPL {mode:live}` → 409 `{reason:market_closed,next_open:…}`, then `GET /tape/AAPL/state` → 404 = no engine). Data Contract row 8 (`GET /market/clock`) built with exactly one computing owner + one serving endpoint; the pre-flight gate reads the same owner (not a 2nd lookup) — COHERENCE-PASS, no veto. Not GOAL_ACHIEVED because J-12 and J-15 (the live-streaming half) are still failing; CONTINUE on real progress (a full journey completed + a contract row built) with zero regressions and a tractable next slice.

## What was done

- Built the **market clock** end-to-end (Data Contract row 8): a vendor-neutral `MarketClock` record + `get_market_clock()` on the adapter Protocol, an `AlpacaAdapter` implementation via the read-only `TradingClient.get_clock()` (vendor SDK stays lazy and confined to `alpaca.py`), and the canonical `GET /market/clock` endpoint (creds → real status; no creds → `available:false` nulls; adapter error → benign degrade — never a fabricated open/closed).
- Added a **market-closed pre-flight gate** to the live branch of `POST /watch/{ticker}`: an authoritatively closed market → distinct `market_closed` refusal (409) carrying `next_open`, with **no engine created**; a degraded/unreachable clock is never reported closed (falls through to `provider_not_implemented`).
- Replaced the hardcoded "market unavailable" stub with a real **Live market-status indicator** (`MarketStatusIndicator`) — open / closed+next-open / unavailable — that reads `GET /market/clock`, polls every 60s only in Live mode, and tears down its interval on unmount/mode-change (iter-0 resource-leak lesson).
- Added the honest **"Market is closed"** panel variant (next-open time, "never fabricates data") rendering in place of the cockpit — **completing J-14 (4/4):** no-creds, untradable symbol, empty window, and now market-closed each surface a distinct honest state.
- Threaded `next_open` from the backend body → `WatchResult.nextOpen` → the `failure` state → the panel; added a shared `formatMarketTime()` so the next-open instant renders in the operator's local zone (never raw UTC).
- Verified zero regressions and clean anti-goals independently via `git diff`: engine/serializers/`providers/base.py`/`simulated.py`/`historical.py` 0-line diff; vendor + credential names confined to `alpaca.py`; `.env` untracked; read-only clock call (no order/account/position path); `CONFIG.market_closed_status_code` (no magic number). Review **PASS**, QA **PASS** (16/16 functional cases; 118 backend tests, exit 0).
- Browser QA (browser-qa-agent) recorded **SKIPPED** because the harness frontend (`:3650`) was down; the `qa` agent captured authoritative browser evidence (TC-13/TC-14/TC-16) on an isolated `:3651` instance, verifying the real indicator, the closed-market panel (no cockpit), poll cleanup, and no regression of SIM-BUYER / Historical replay / symbol search / Stop→idle.

## What's left

- Journey J-12 (Stream a real live ticker) **failing** — needs the real Alpaca live WebSocket behind an async provider/feeder seam (today's `Provider.stream()` is synchronous); its Live controls + market-status surface are now real, but streaming still returns `provider_not_implemented`.
- Journey J-15 (A live-feed gap shows stale, then recovers) **failing** — needs the live push feeder plus a stale-on-gap → recover watchdog (fabricating no trades during the lull).
- A Live watch with credentials while the market is **open** still honestly reports streaming as not-yet-built (the documented iter-4 boundary, not a regression).
- The backend's `next_close` from `GET /market/clock` is returned by the API but not yet surfaced anywhere in the UI (only `is_open` and `next_open` are displayed).
- Browser QA via the harness frontend (`:3650`) needs a re-run once the harness dev server is restarted — this iteration's UI verdicts came from an isolated instance after a self-inflicted, fully-remediated QA-process incident (shared `.next` corruption + a discarded-then-reconstructed `page.tsx`), not from the harness server.

## Next step

**iter-4 — the live-streaming half (J-12 + J-15), at `full` depth.** This is the genuine architecture change deliberately isolated out of iter-3: today's `Provider.stream() -> Iterable[Event]` is **synchronous**, while a live feed is **async/unbounded**, so iter-4 must introduce the async provider/feeder seam, wire the real Alpaca live WebSocket behind the existing vendor-neutral adapter, and add the **J-15** stale-on-gap → recover watchdog (fabricating no trades during the lull). Reuse iter-3's `get_market_clock()` as J-12's pre-flight open-check and the existing cancellable feeder teardown so a live socket is never orphaned on switch/stop (iter-0 lesson); the `stale` dot + `set_stream_status` already exist. Recommend **full** depth: high blast radius against **13** green journeys, real async I/O, and operator/gated real-socket verification (market hours + creds). Achieving J-12 + J-15 with no sim/historical regression closes the last two must-have journeys → goal completion.

## Quick verify

From `reports/phase-goal-i_will_be_super_rich-iter-3-what-to-click.md`:

1. Open `http://localhost:3650/` in your browser
2. Click the **Live** button in the data-source selector (top bar)
3. Wait ~3 seconds and read the "market" pill
4. Hover the pill (only matters if you have no creds)
5. (Market-closed branch only) Type `AAPL` into the "Symbol search" box, then click the green **Watch** button

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_will_be_super_rich-iter-3.md |
| Dev handoff | — | docs/handoffs/goal-i_will_be_super_rich-iter-3-dev.md |
| Review | PASS | reports/reviews/goal-i_will_be_super_rich-iter-3-review.md |
| Browser QA | SKIPPED | reports/phase-goal-i_will_be_super_rich-iter-3-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-i_will_be_super_rich-iter-3-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-i_will_be_super_rich-iter-3-user-visible-changes.md |
| What to click | — | reports/phase-goal-i_will_be_super_rich-iter-3-what-to-click.md |
| UI surface map | — | reports/phase-goal-i_will_be_super_rich-iter-3-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-i_will_be_super_rich-iter-3-ui-test-plan.md |
| QA | PASS | reports/qa/goal-i_will_be_super_rich-iter-3-qa.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_will_be_super_rich/iter-3/eval.md |
| Journey history | — | runs/goal-session-i_will_be_super_rich/state/journey-history.json |
