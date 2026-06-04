# Iteration Summary — goal-i_will_be_super_rich-iter-1

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-06-04
**Iteration:** 1

## In plain words

**What you can do now:** On the built-in practice data, you can watch one stock ticker at a time and get a plain-English read of what the order flow is doing — whether buyers or sellers are in control, whether heavy buying or selling is being absorbed while the price holds steady, or whether the tape is simply unclear — each with a confidence score, live quote and trade readouts, observations, and a running event log. You can stop a watch and start a new one cleanly. And you can now choose which data source to read from — practice, live, or historical — using a selector at the top of the screen.

**What changed this time:** You can now pick a data source at the top of the screen — Live, Historical, or Simulated (practice) — and each choice shows just the controls it needs (a symbol box for real data, plus a date, a time window, and a replay-speed chooser for historical playback). If you choose Live or Historical without a market-data account connected, the app now gives you a clear "real-data provider unavailable" message instead of ever inventing or guessing prices — and it never quietly falls back to practice data. Practice mode itself works exactly as before.

**What's next:** Next, the app will begin replaying real past market sessions for a stock you choose, and let you find tickers by searching for them.

## Headline

Added a Live/Historical/Simulated data-source selector with an honest "real-data unavailable" state.

## Direction

**Signal:** improving
**Why:** This iter flipped J-10 (choose a data source) failing → passing and advanced J-14 (honest real-data edge cases) failing → partial via the no-credentials 503 gate, with zero regressions and all five critical anti-goals independently verified clean against `git diff`. The engine and canonical reads (`/state`, `/features`, `/summary`, `/events`, `WS /stream`) have an empty diff, so J-01–J-09 hold. Next target is J-11 historical replay (plus J-13 symbol search) — the first real provider behind the new vendor-agnostic adapter seam.

**Trend (last 2 iters):**
- Newly passing this iter: J-10
- Newly passing in last 2 iters total: J-10
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: none
- Iters with no journey state change: 1 of last 2 (iter-0 baseline recorded inherited state)

**Latest evaluator reasoning:** The first real-data slice landed cleanly: J-10 flipped failing → passing (three-mode data-source selector + per-mode control reveal, Simulated → SIM-BUYER → buyer_control with no regression), and J-14 advanced failing → partial (the no-credentials path is now an honest "real-data provider unavailable" non-cockpit state, REST 503 `provider_unavailable` + `/state` 404 proving no engine is created). No required-still-passing journey regressed, all five critical anti-goals were independently verified clean, and `coherence.md` is COHERENCE-PASS (no structural veto).

## What was done

- Added a top-of-page data-source selector — Live / Historical / Simulated (Simulated default) — with per-mode controls (Simulated: ticker box; Live: symbol box + market-status indicator; Historical: symbol box + date, start/end time, replay-speed).
- Added an honest "real-data provider unavailable" state: a Live/Historical Watch with no credentials shows a non-cockpit panel — no fabricated data, no silent fall-back to the simulator (REST returns 503 `provider_unavailable`; `/state` → 404, proving no engine is created).
- Built a vendor-agnostic data seam: a `MarketDataAdapter` Protocol + a single `AlpacaAdapter` (env-only credential detection, no SDK imported) as the one module that knows the vendor; canonical `real_data_available()` defined once.
- Added an optional `{mode,start,end,speed}` body to `POST /watch/{ticker}`; the engine and all canonical reads (`/state`, `/features`, `/summary`, `/events`, `WS /stream`) are untouched (empty diff).
- Hardened the watch lifecycle: a new watch or a source/symbol switch tears down the prior watch first (fixes the iter-0 orphaned-watch lesson).
- Backend 84 tests pass (68 prior + 16 new gate tests); frontend type-check/build clean.
- Verified 2 target journeys pass browser QA — J-10 (selector + per-mode reveal + SIM-BUYER → buyer_control no-regression) and J-14's no-credentials path — with 12/12 browser tests and 15/15 functional cases passing.

## What's left

- Journey J-11 (Replay a real historical session) failing — first real provider not yet wired behind the seam.
- Journey J-12 (Stream a real live ticker) failing.
- Journey J-13 (Find a symbol by search) failing — the symbol box is free-text only, no vendor-backed suggestions.
- Journey J-14 (Real-data edge cases handled honestly) partial — only the no-credentials path is done; unknown-symbol, empty-window, and market-closed cases remain (need live vendor calls).
- Journey J-15 (A live-feed gap shows stale, then recovers) failing.
- Real Live/Historical data *serving* is not built — even with credentials present, a real-mode watch returns an explicit 503 `provider_not_implemented` rather than a cockpit.
- The Live market-status indicator is a static "unavailable" — it does not call a real market-clock endpoint yet.
- The Historical date/time/speed inputs are accepted but drive no real fetch yet (the watch is refused before they take effect).
- `.env` name trap: the stale local `apps/backend/.env` uses `ALPACA_SECRET_KEY`, but the adapter reads `ALPACA_API_SECRET` and there is no dotenv loader — real credentials must use the adapter's names (`ALPACA_API_KEY` / `ALPACA_API_SECRET`) plus a loader.

## Next step

Target **J-11 (replay a real historical session)** next — the safest first real-provider slice: reproducible for a fixed symbol + past window, needs no live market hours, and turns the creds-present `provider_not_implemented` branch into a populated cockpit through the **same** engine. Bundle **J-13 (`GET /symbols/search`)** so the real-mode symbol box gets vendor-backed suggestions. Decide two constraints up front: (1) **credentialed verification strategy** — plan either a gated/operator credentialed integration run or a recorded real-vendor (VCR-style) fixture built from real captured Alpaca data; never synthesized data, even in tests, or J-11 cannot be evidenced as passing; (2) **the `.env` credential-name trap** — real creds must use the adapter's `ALPACA_API_KEY` / `ALPACA_API_SECRET` names (with a dotenv loader) or `real_data_available()` will wrongly report "unavailable". **Full depth** is warranted: J-11 introduces the first real third-party dependency (`alpaca-py` via the supply-chain gate), real network I/O, and real-timestamp → logical-timeline mapping, and must not regress J-01–J-10.

## Quick verify

From `reports/phase-goal-i_will_be_super_rich-iter-1-what-to-click.md`:

1. Open `http://localhost:3650/` in your browser.
2. With `Simulated` still selected, type `SIM-BUYER` into the ticker box and click the green `Watch` button.
3. Click the `Live` button in the 3-way switch.
4. Type `AAPL` into the symbol box and click the green `Watch` button.
5. Click the `Historical` button.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_will_be_super_rich-iter-1.md |
| Dev handoff | — | docs/handoffs/goal-i_will_be_super_rich-iter-1-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-i_will_be_super_rich-iter-1-review.md |
| Browser QA | PASS | reports/phase-goal-i_will_be_super_rich-iter-1-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-i_will_be_super_rich-iter-1-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-i_will_be_super_rich-iter-1-user-visible-changes.md |
| What to click | — | reports/phase-goal-i_will_be_super_rich-iter-1-what-to-click.md |
| UI surface map | — | reports/phase-goal-i_will_be_super_rich-iter-1-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-i_will_be_super_rich-iter-1-ui-test-plan.md |
| QA | PASS | reports/qa/goal-i_will_be_super_rich-iter-1-qa.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_will_be_super_rich/iter-1/eval.md |
| Journey history | — | runs/goal-session-i_will_be_super_rich/state/journey-history.json |
