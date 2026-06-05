# Iteration Summary — goal-i_will_be_super_rich-iter-6

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-06-05
**Iteration:** 6

## In plain words

**What you can do now:** Watch a US stock in practice or historical replay mode and read the tape in plain language — buyer control, seller control, bid or ask absorption, or unclear — with a confidence score, live quote, running trades list, and observations. You can search for a stock by name, choose from Live, Historical, or Simulated data sources, replay a past session at speed, or follow a live market with an honest live/stale signal. The recent-trades list labels most real-market prints as buy or sell (not "unknown"). A candlestick price chart now appears above the cockpit when you are watching a simulated or replayed stock, letting you see the watched price drawn as candles, with colored markers at each moment the tape state shifted to something meaningful — green for buyer control, red for seller control, amber for absorption.

**What changed this time:** A price chart was added above the cockpit for Simulated and Historical watches. You can see candle bars representing the watched price over time, and colored markers show exactly where the tape state changed to something significant. A small bar-size selector lets you switch between 10-second, 30-second, and 60-second candles. The chart shows an honest "no price history yet" message before data arrives, and disappears automatically when you switch to Live mode. The underlying data pipeline is fully proven correct, but the chart's on-screen rendering has not yet been captured in a browser screenshot — that confirmation is the top priority for the next round.

**What's next:** Next we'll re-run the browser checks against a clean build to confirm the candlestick chart actually renders on screen, then build the ability to pause and resume a watch without losing state.

## Headline

Engine history buffer (OHLC 10/30/60 s + markers) + `/history` endpoint + PriceChart component built; backend data path proven; browser render unverified (J-17/J-18 partial).

## Direction

**Signal:** improving
**Why:** J-17 and J-18 advanced from `failing` to `partial` this iteration — the full backend data pipeline is independently proven correct (live `/history` probe, 18 new tests, 141→159 suite count, no regressions, COHERENCE-PASS), the frontend component exists and builds cleanly, and the source of the browser-QA failure is root-caused to stale infra (corrupted `.next`), not a code defect. No previously-passing journey regressed. The path to full `passing` status for J-17/J-18 is unambiguous: rebuild the shared `.next` and re-run browser checks.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-16 (iter-5)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5 (iter-6 advanced J-17/J-18 from failing to partial; iter-5 passed J-16; iters 2/3/4 each passed journeys)

**Latest evaluator reasoning:** "The backend data path is independently proven correct for all five sim scenarios and over the wire (404/422/empty contract), the suite rose 141→159 with no regressions, the source builds clean (`/` static-prerendered, no SSR), and coherence is PASS. However, J-17/J-18 lack their defining visual evidence: browser-qa SKIPPED all 15 UT tests because the shared `:3650` dev server returns HTTP 500 (corrupted `.next` — the iter-3 failure mode recurring), and the one `qa` chart screenshot is blank. The chart-renders claim is therefore unconfirmed at the pixel level — `partial`, not passing."

## What was done

- Built `app/engine/history.py`: new engine history buffer accumulating OHLC candles at 10/30/60 s (binned by logical timestamp) and meaningful-transition markers (`buyer_control`, `seller_control`, `bid_absorption`, `ask_absorption`); markers reuse the engine snapshot's own `tape_state`/`confidence` — no second classification
- Wired the buffer into `tape_engine.py` (feed in `process_event` only; exposed as a read-only `TapeEngine.history` property); added config keys (`history_bar_sizes`, `history_marker_states`, `history_max_bars`, `history_max_markers`) — no magic numbers in engine code
- Added `GET /tape/{ticker}/history?bar=<10|30|60>` in `main.py` with a pure `serialize_history` projection: 404 for unwatched ticker, 422 for out-of-range `bar`, 200 + empty lists for a ticker with no trades yet — never invented candles
- Added `PriceChart.tsx` (client-only, `"use client"`, dynamic import in effect to avoid SSR): renders OHLC candlesticks + emerald/rose/amber markers; 10/30/60 s bar-size selector; pan/zoom; honest empty state; polls `/history` at 1 s cadence
- Mounted `<PriceChart>` above `<Cockpit>` in `page.tsx` for `mode === "sim" || mode === "historical"` only (hidden for `live`); added `fetchHistory` to `api.ts` and `OhlcBar`/`TapeMarker`/`TapeHistory` types to `types.ts`
- Added `NEXT_DIST_DIR` env-gated override to `next.config.mjs` so a one-off isolated build never clobbers the running dev server's `.next`
- Backend data path independently verified by evaluator: live SIM-BUYER/SELLER/BIDABS/ASKABS/CHOP probed → correct candles, correct marker colors, 0 markers for `unclear`; 404/422/empty over the wire confirmed
- Suite rose from 141 to 159 (18 new tests in `test_history.py` + `test_history_api.py`); isolated frontend build (`NEXT_DIST_DIR=.next-iter6-build`) compiled clean with `/` static-prerendered (no SSR violation); 0 browser QA tests run (shared `:3650` HTTP 500 from corrupted `.next`)

## What's left

- Journey J-17 (Price chart with tape-state markers on simulated data) — `partial`; browser render not yet pixel-verified due to corrupted shared `.next`; top priority for iter-7
- Journey J-18 (Inspect tape-state prediction on a real historical chart) — `partial`; real-historical in-browser render unverified; backend correctness already proven
- Journey J-19 (Pause and resume a watch without losing state) — `failing`; not built (deferred per iter-6 spec)
- Journey J-20 (Pick a historical window in local time with US-session quick-picks) — `failing`; not built (deferred per iter-6 spec)
- Corrupted shared `.next` at `:3650` must be rebuilt before any browser-qa run (`Cannot find module './833.js'`); prerequisite for closing J-17/J-18

## Next step

iter-7 at full depth, two deliverables: (1) Close the J-17/J-18 visual-evidence gap (highest priority) — run browser-qa against a clean isolated frontend build (`NEXT_DIST_DIR` set, `NEXT_PUBLIC_API_URL` pointing to an isolated backend, never the shared `:3650`/`.next`) and capture real screenshots showing: candlesticks rendered for SIM-BUYER, the emerald buyer_control marker, rose for SIM-SELLER, amber for SIM-BIDABS/SIM-ASKABS, the 10→30→60 s selector re-rendering candles, and the chart hidden in Live mode. The shared `:3650` `.next` is corrupted and must be rebuilt or bypassed before any browser run — this is a prerequisite, not optional. Once those screenshots exist, J-17 → passing and J-18's surface → passing (real-fetch correctness already stands on the backend test and the evaluator's live `/history` proof). (2) Build J-19 (pause/resume) — `POST /watch/{ticker}/pause|resume`, engine/feeder owns the paused state in the snapshot, UI Pause/Resume beside Stop with a PAUSED indicator; freeze without teardown, live resumes at current real data (no fabricated backfill), Stop still tears down. Then J-20 (local-time picker + US-session quick-picks) as its own slice.

## Quick verify

From `reports/phase-goal-i_will_be_super_rich-iter-6-what-to-click.md`:

1. Open `http://localhost:3650` in your browser — expect the page loads with a TopBar, ticker input, and mode selector showing "Simulated"; no chart panel yet (confirms chart only appears when watching).
2. Type `SIM-BUYER` into the ticker input field and click the "Watch" button — expect a panel titled "Price Chart — Tape-State Markers" appears above the cockpit within 1–2 seconds, with a "Loading price history…" overlay and a bar-size selector ("10s", "30s", "60s").
3. Wait 15–20 seconds and observe the chart canvas — expect at least 3 candlestick bars on the dark canvas and an emerald (bright green) arrow marker at the `buyer_control` transition; cockpit "Tape State" panel simultaneously shows `buyer_control`.
4. Click the "30s" button in the bar-size selector — expect the chart redraws within 1 second with fewer, wider bars; "30s" button gains an active/filled style.
5. Click the "Live" button in the TopBar — expect the "Price Chart — Tape-State Markers" panel disappears immediately; no empty gap or ghost box where the chart was.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_will_be_super_rich-iter-6.md |
| Dev handoff | — | docs/handoffs/goal-i_will_be_super_rich-iter-6-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-i_will_be_super_rich-iter-6-review.md |
| Browser QA | SKIPPED | reports/phase-goal-i_will_be_super_rich-iter-6-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-i_will_be_super_rich-iter-6-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-i_will_be_super_rich-iter-6-user-visible-changes.md |
| What to click | — | reports/phase-goal-i_will_be_super_rich-iter-6-what-to-click.md |
| QA | PASS | reports/qa/goal-i_will_be_super_rich-iter-6-qa.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_will_be_super_rich/iter-6/eval.md |
| Journey history | — | runs/goal-session-i_will_be_super_rich/state/journey-history.json |
