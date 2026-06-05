# Goal Iteration 6 — Tape-state prediction chart (candlesticks + markers) for Simulated & Historical

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich
- **Iteration:** 6
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-17, J-18
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-15, J-16
- **Anti-goal reminders:**
  - **Stay in scope.** No stock scanner/screener, no news/theme/sentiment analysis, no fundamental analysis, no chart-pattern or indicator charting, no portfolio/position management — these belong to separate projects and MUST NOT be built here. The one allowed chart is the focused price candlestick + tape-state-marker overlay (simulated/historical), which adds **no** indicators, studies, or drawing tools. *(critical)*
  - **One focused chart, computed once.** OHLC bars and tape-state markers MUST be computed once in the engine history buffer and read identically by `…/history` and the chart; the UI MUST NOT recompute side, state, or price from raw data. An empty window MUST yield an **empty** chart, not invented candles. The chart is analysis-only — it MUST NOT add any order/execution affordance. *(critical)*
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*
  - **No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code.
  - **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the tape. *(critical)*
  - **Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine MUST produce identical features, state, and confidence; classification MUST NOT depend on wall-clock time or randomness.
  - **Provider-agnostic engine.** The engine and API MUST depend only on the provider interface (TradeEvent / QuoteEvent / BookLevelEvent); a concrete vendor SDK MUST appear in only one adapter module.
  - **No fabricated data.** The system MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. An empty historical window → explicit no-data / empty chart, never invented candles.

## GOAL

A user watching `SIM-BUYER` / `SIM-SELLER` / `SIM-BIDABS` / `SIM-ASKABS` (and a real symbol over a past Historical window) sees a live **candlestick price chart above the cockpit** with a **10 / 30 / 60 s bar-size selector** and **markers at meaningful tape-state transitions** (green buyer_control, red seller_control, amber absorption; unclear unmarked) — so they can visually judge whether a marked state preceded the subsequent price move.

## BACKGROUND

J-16 (resolved aggressor side) landed in iter-5 and was independently re-verified; J-01–J-16 are all `passing`, leaving J-17, J-18, J-19, J-20 as the only `failing` journeys (per `journey-history.json`). The iter-5 evaluator (`CONTINUE`, depth `full`) recommended building **J-17 + J-18 together** — they share one mechanism: the engine **history buffer** (OHLC bars + transition markers, computed once) projected by `GET /tape/{ticker}/history?bar=<10|30|60>` and rendered by one candlestick chart component (J-17 = simulated data, J-18 = real historical replay). These were pre-registered additively as **Data Contract row 10** in the approved `blueprint.md` at iter-5, on the existing `/` HOME — so this iteration introduces **no nav-skeleton change and needs no blueprint re-approval**. This is the first **frontend** change of the J-16–J-20 extension, crosses backend (new engine state + new endpoint) and frontend (new chart + charting library), and carries the load-bearing *"One focused chart, computed once"* critical anti-goal — hence **full** depth. J-19 (pause/resume) and J-20 (local-time picker) are deliberately deferred to their own later slices to keep this iteration scorable. The `coherence.md` for iter-5 was `COHERENCE-PASS`, so no consolidation pass is owed.

## IN SCOPE

### Backend
- [ ] Add an **engine history buffer** to the single engine (logical owner: the engine; concrete file is the developer's choice, e.g. a new `app/engine/history.py` owned by `TapeEngine`). As each event is processed in `apps/backend/app/engine/tape_engine.py::process_event`, the buffer accumulates the watched **price** into **OHLC bars binned at 10 / 30 / 60 s** (three concurrent bin sizes, bucketed by the engine's **logical timestamp** — never wall-clock) and appends a **tape-state-transition marker** `{timestamp, state, confidence}` whenever the classified `tape_state` changes to a **meaningful** state (`buyer_control`, `seller_control`, `bid_absorption`, `ask_absorption`; a transition **to** `unclear` is NOT marked). Computed **once**, alongside the existing snapshot — the chart never re-bins or re-classifies.
- [ ] Surface the history buffer read-only. Either attach the bars+markers to `EngineSnapshot` (frozen) or expose a read accessor on `TapeEngine`; do not introduce a second classifier or a second price source. Markers MUST reuse the **same** `tape_state` / `confidence` values already produced by `TapeStateClassifier` (Data Contract rows 1) — no recomputation.
- [ ] Add **config keys** for the bar sizes and any marker-significance / OHLC binning parameter to `apps/backend/app/config.py` (the single `Config` frozen dataclass). No bar-size or threshold literal may appear inline in engine code (No-magic-numbers anti-goal). The allowed bar sizes (10/30/60) come from config; an out-of-range `bar` value is rejected (see error cases).
- [ ] Add route `GET /tape/{ticker}/history?bar=<10|30|60>` in `apps/backend/app/main.py`, served by a new pure projection in `apps/backend/app/serializers.py` (mirror the existing `serialize_*` pattern). Response = the selected bar size's OHLC series + the marker series for the watched ticker. Reads of a **not-watched** ticker return **404** (consistent with `/state`, `/features`). An **empty** history (no trades yet, or an empty historical window) returns an **empty bars list + empty markers list** (HTTP 200) — never invented candles.
- [ ] The endpoint is meaningful for **simulated + historical** watches. (Live is intentionally hidden in the UI; the backend need not special-case the mode — it simply serves whatever the engine has accumulated.)

### Frontend
- [ ] Add **one** charting dependency to `apps/frontend/package.json` — a **lightweight client-side financial-charting library** (recommended: `lightweight-charts`, which is candlestick-native). Hard constraints: **client-side only (no SSR** — render inside a `"use client"` component, dynamically imported / mounted in an effect so it never runs during server render), **no new backend dependency**, and it must support candlesticks + custom series markers. Do not add a general TA/indicator library.
- [ ] Add a **`PriceChart` component** (`apps/frontend/components/PriceChart.tsx`) that renders a **candlestick** chart of the OHLC series plus **markers** at the transition timestamps, colored by the marker's state: **emerald** = buyer_control, **rose** = seller_control, **amber** = bid/ask_absorption (per the DESIGN SYSTEM tokens; unclear is unmarked). Include a **bar-size selector** (10 / 30 / 60 s) that re-fetches/re-renders the candles. Support pan/zoom (library default is sufficient). It reads its data **only** from `GET /tape/{ticker}/history` (add the fetch to `apps/frontend/lib/api.ts` and the response types to `apps/frontend/lib/types.ts`); it MUST NOT recompute price, side, or state, and MUST NOT bucket candles or place markers from raw trades.
- [ ] Mount `PriceChart` **above** the cockpit in `apps/frontend/app/page.tsx` (above `<Cockpit>`), rendered **only when `mode === "sim"` or `mode === "historical"`** and **hidden when `mode === "live"`** (matches the blueprint IA: "Price chart (Simulated + Historical only) … Hidden for Live"). Keep the page exactly one screen.
- [ ] Empty/idle handling: before data arrives, or for an empty historical window, the chart shows an **empty** chart / "no price history yet" treatment — never placeholder candles. The chart refreshes as new bars accrue during replay (poll `…/history` on the existing stream cadence or on snapshot tick; do not open a second WebSocket).

### New user-facing capability
The user can see the watched price as a candlestick chart with tape-state-transition markers and switch the bar size between 10 / 30 / 60 seconds, for Simulated and Historical watches.

### New information displayed
OHLC price candles (at the selected 10/30/60 s bar size) and colored markers at meaningful tape-state transitions, positioned above the existing cockpit.

### New user actions
A bar-size selector (10 s / 30 s / 60 s) on the chart; pan/zoom on the chart canvas.

### UI surface changes
A new `PriceChart` panel above the cockpit on `/`, shown for Simulated and Historical modes only (hidden for Live). No new page or route.

### Product surface delta
The cockpit gains a visual price-and-prediction pane: a user can now correlate a marked tape-state transition with the subsequent candle movement on the same screen, turning the textual read into a testable visual one — the single focused chart the product allows.

### Blueprint conformance
All new UI lives on the existing **`/` — Watch (the tape cockpit) — HOME**, in the already-described **"Price chart (Simulated + Historical only)"** pane **above the cockpit** (Information Architecture, `blueprint.md`). J-17 and J-18 are already mapped to "price-chart pane above the cockpit (sim / historical)". **No new nav section, no moved home, no nav-skeleton change → no re-approval requested.**

### Data-contract additions
**None new.** This iteration **implements** the already-registered **Data Contract row 10** — *Price history: OHLC bars (per 10/30/60 s) + tape-state-transition markers (state + confidence + ts)* — canonical computing module **Engine history buffer**, canonical serving endpoint **`GET /tape/{ticker}/history?bar=<10|30|60>`**, re-exposed read-only by the chart, which **never recomputes price/side/state** (sim + historical only). Markers reuse rows 1 (tape state + confidence) verbatim; candles bin the same price the engine already derives from quotes/trades. No second computation or second endpoint for any existing contract value is introduced.

## OUT OF SCOPE

- **J-19 (pause/resume)** and **J-20 (local-time window picker + US-session quick-picks)** — separate later slices; do not start them here.
- Any technical indicators, overlays, studies, drawing tools, multi-pane/multi-symbol charting, volume sub-panes, or a second chart (No-scope / one-focused-chart anti-goals).
- Any order/buy/sell/execution affordance, button, or annotation on or near the chart (No-execution anti-goal).
- Showing the chart in **Live** mode (it is hidden for Live by design this iteration).
- Changing the engine's classification, feature, side, or confidence logic, or the existing cockpit panels — the chart is purely additive and read-only.
- Persisting the history buffer (Phase 1 stays in-memory).

## DEFINITION OF DONE

- [ ] Target journeys J-17 and J-18 pass via browser-qa-agent (J-17 fully browser-verifiable on sim with no credentials; J-18's chart/bar-size/marker UI is browser-verifiable, and the bars-match-`…/history` correctness is asserted by a backend test — real-fetch correctness is verified when credentials are present, otherwise the gated/fixture path stands in, per the J-16–J-20 verification note in `docs/goal.md`).
- [ ] Required-still-passing journeys J-01–J-16 remain green (no regression to the cockpit, classification, side resolution, or real-data honesty).
- [ ] No anti-goal violation introduced — in particular: the chart reads `…/history` and recomputes nothing; an empty window yields an empty chart; no order/execution affordance is added; no magic bar-size/threshold literal in engine code; markers reuse the engine's own state/confidence.
- [ ] Unit/integration tests pass; no regressions (existing suite was 141 passed / 1 skipped at iter-5 — must not drop).
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich-iter-6-dev.md`.

## TESTING REQUIREMENTS

- **Browser (named, by ID):**
  - **J-17** — Watch `SIM-BUYER`: candlestick chart renders and updates during replay; toggle bar size 10 → 30 → 60 s and confirm the candles re-render; confirm an **emerald** buyer_control marker appears. Then watch `SIM-SELLER` (down trend + **rose** seller marker) and `SIM-BIDABS` / `SIM-ASKABS` (**amber** absorption markers with price held). Confirm the chart is shown for Simulated and **hidden when the data source is switched to Live**.
  - **J-18** — Select **Historical**, watch a real symbol over a past regular-hours window (use a **penny-spread** liquid name for a clean read, e.g. Ford — see NOTES): candlesticks reflect the replayed real prices, the bar-size selector switches 10/30/60 s, and markers align with tape-state transitions. (Where credentials are absent in the QA environment, verify the chart surface + bar-size + empty/honest behavior in the browser and rely on the backend correctness test below for the bars-match-`…/history` guarantee.)
- **Unit/integration (code paths that MUST have tests):**
  - Engine history buffer: feeding a known ordered event stream produces the expected OHLC bars at each of 10/30/60 s and a marker **only** at meaningful state transitions (assert exact bar boundaries by **logical** timestamp and exact marker timestamps/states). Determinism: replaying the same stream yields identical bars + markers.
  - Single source of truth: the marker `state`/`confidence` equal the engine snapshot's `tape_state`/`confidence` at that transition (no independent classification); candle prices derive from the same price the snapshot exposes.
  - `GET /tape/{ticker}/history` projection: for a watched sim ticker, the served bars/markers equal the engine buffer's content for the requested `bar` size (the `/history`-agrees-with-engine analogue of the existing single-source API tests in `test_api.py`).
- **Error cases (must be rejected / handled honestly):**
  - `GET /tape/{ticker}/history` for a **not-watched** ticker → **404** (not a fabricated empty 200 for an unknown engine).
  - An **out-of-range / invalid `bar`** value (not in the configured {10,30,60}) → rejected with a 4xx (not silently coerced).
  - A watched ticker with **no trades yet** (or an empty historical window) → **empty** bars + **empty** markers (200), and the UI renders an **empty** chart — no invented candles (No-fabricated-data / one-focused-chart anti-goals).

## NOTES

- **Coherence:** iter-5 was `COHERENCE-PASS`; this iteration implements pre-registered Data Contract **row 10** on the existing HOME with **no** nav change, so no `blueprint.md` edit and **no** `blueprint.reapproval-requested` are needed. The coherence-auditor will check that the chart reads row 10 and recomputes nothing, and that no second price/state/side computation or second endpoint was introduced.
- **Lesson (iter-3, frontend QA) — applies directly, this is a frontend iteration:** QA/build MUST happen in an **isolated `.next`**, never against the harness's shared `.next` (`npm run build` against the shared dir corrupted the `:3650` dev server), and QA MUST NOT `git checkout` any file carrying uncommitted iteration edits (it previously discarded the developer's `page.tsx`). Adding a charting dependency means `npm install` will run — ensure it does not clobber the running harness server.
- **Lesson (iter-5, evidence) — applies to the evaluator:** the authoritative `…-ui-test-results.md` has twice been a **stale pre-build verify-only re-baseline** (self-labelled "no code changes", old test count, pre-fix screenshot). For this iteration the chart's existence is browser-verifiable, but the **bars-match-`…/history`** correctness is the backend test — cross-check both, and confirm the test count rose from the iter-5 baseline (141 passed) rather than trusting a screenshot alone.
- **Lesson (iter-2, real-data demo) — applies to J-18:** the free **IEX** top-of-book is wide for high-priced names (AAPL reads `unclear`); for a clean Historical chart read pick a **penny-spread** symbol (Ford) and reuse the **capture-once committed real fixture** pattern so J-18's chart is deterministic and offline-reproducible without depending on live creds at QA time. Never synthesize trades to fill the chart.
- **Charting library:** `lightweight-charts` is the recommended fit (candlestick-native, ~tiny, client-side, supports series markers). The developer may choose another **lightweight client-side financial-charting** library so long as it is client-only (no SSR), adds no backend dependency, and supports candlesticks + markers. It must NOT be a general TA/indicator/drawing library (Stay-in-scope anti-goal).
- **Bucketing:** bin OHLC by the engine's **logical timestamp**, consistent with the deterministic-engine rule (wall-clock only paces delivery, never classification or binning). Reserved sim tickers run on an accelerated clock, so the chart populates within the journey's seconds-long warm-up.
- **References:** iter-5 eval recommendation (`runs/goal-session-i_will_be_super_rich/iter-5/eval.md`), approved blueprint Data Contract row 10 + IA "Price chart (Simulated + Historical only)" (`runs/goal-session-i_will_be_super_rich/state/blueprint.md`), goal Key Capabilities #12 (history buffer) and #13 (prediction chart) and Product Shape API line `GET /tape/{ticker}/history` (`docs/goal.md`).
