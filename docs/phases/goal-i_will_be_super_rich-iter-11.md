# Goal Iteration 11 — Vendor responsiveness: true call-level timeout, fast historical load, fast symbol search

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich
- **Iteration:** 11
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-28, J-29, J-30
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-15, J-16, J-17, J-18, J-19, J-20, J-21, J-22, J-23, J-24, J-25, J-26, J-27
- **Anti-goal reminders:**
  - **Bounded, honest, performant vendor calls.** Every vendor-gated Watch MUST be bounded by a **real call-level deadline** (an HTTP/SDK timeout), not only an async wrapper a blocking/large-response call can defeat, and the backend's bound MUST be **shorter than the frontend client timeout** so the user always sees the backend's honest error, never a client-side give-up. Interactive vendor paths MUST be **fast by design, not by lengthening timeouts**: a legitimate high-volume window MUST load within budget via an optimized fetch (concurrent trades/quotes, no needless pre-flight, cached/reused windows, prompt warm-up), and **symbol search MUST NOT re-fetch the whole asset universe per keystroke** (a warmed/cached universe, cancelled stale requests, a sensible min-query). Any timeout/oversize error MUST be **actionable for the real cause** (e.g. "shorten the window"), never a misleading "try again"; and every performance optimization MUST preserve correctness — **no fabricated or dropped trades/quotes, no recomputation outside the engine** (single source of truth holds). *(critical)*
  - **No fabricated data.** The system MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. Every real-data failure mode MUST surface an explicit, distinct state and never a cockpit. Falling back to simulated or invented data to mask a real-data failure is a defect. *(critical)*
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*
  - **No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code.
  - **Provider-agnostic engine.** The engine and API MUST depend only on the provider interface (TradeEvent / QuoteEvent / BookLevelEvent); swapping the simulator for a real feed MUST NOT require engine or API changes. A concrete vendor SDK MUST appear in only one adapter module behind a vendor-neutral seam; vendor specifics MUST NOT leak into the engine, providers, or API.
  - **No secrets in source.** Real-vendor API keys/tokens MUST come only from environment/config and MUST NOT be committed; with no keys the app runs simulator-only and real modes report an explicit "unavailable" rather than failing opaquely or fabricating data.
  - **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the tape. *(critical)*
  - **No silent dead-clicks.** Pressing Watch MUST always produce a visible UI change within ~1 second. The UI MUST NOT silently remain on the idle/previous screen, MUST NOT leave "Connecting…" running with no resolution, and MUST NOT swallow a failure. *(critical)*
  - **No mute cockpit, no silent return to idle.** A valid Watch MUST resolve to a non-idle terminal state. Connected-but-no-data MUST read as an explicit connecting/waiting or honest empty-state and MUST resolve, within a bounded configured time, to streaming data or an explicit honest state — owned once by the engine's `stream_status`. *(critical)*

## GOAL

Make every credential-gated vendor path responsive and honestly bounded: a vendor fetch is cut off by a real call-level deadline with an actionable message, a busy historical window loads fast by design (concurrent fetch + cached reuse + prompt warm-up), and symbol search is warmed and cancellable so it never stalls — closing the last three unbuilt Must-haves (J-28, J-29, J-30).

## BACKGROUND

J-01–J-27 all pass with concrete evidence; the only unbuilt Must-haves are the vendor-responsiveness cluster J-28/J-29/J-30, first scored failing at iter-10 (goal-expansion commit 533b6e2). The iter-10 evaluator recommends building them together at **full** depth because they share the Alpaca adapter / vendor-fetch path and reinforce one another, and they need new unit tests (a slow/large vendor double, fetch-concurrency timing, a cache hit, request cancellation, the backend<frontend ordering). Today the bound is only the iter-9 `asyncio.wait_for` **wrapper** around `to_thread(adapter.…)` (`main.py:191,243`) — which a blocking or CPU-bound large-response SDK call inside the worker thread can defeat (the thread keeps running; `wait_for` abandons it but the deadline is not enforced *at the vendor call*); `_fetch_trades_quotes` fetches trades then quotes **sequentially** with a needless `_require_tradable` pre-flight round-trip and no window cache; and `searchSymbols` (`api.ts:141`) has **no AbortController**, while `_asset_universe` warms lazily on first call (a cold first-search stall). Coherence for iter-10 was **COHERENCE-PASS** — no consolidation pass is owed, so this iteration may add the planned scope directly.

This is the GOAL_ACHIEVED-candidate slice: after J-28/J-29/J-30 pass with evidence and zero regressions, the full Must-have set J-01–J-30 is complete.

## IN SCOPE

### Backend

**J-28 — a true call-level vendor deadline, with backend<frontend ordering and an actionable message**
- [ ] Enforce a **real deadline at the vendor-call boundary** inside the one adapter module (`apps/backend/app/providers/adapters/alpaca.py`) — not only the existing `asyncio.wait_for` wrapper in `main.py`. Configure the Alpaca SDK / its underlying HTTP client (the `StockHistoricalDataClient` / `TradingClient` data calls — `get_stock_trades`, `get_stock_quotes`, `get_asset`, `get_all_assets`, `get_clock`) with an explicit per-request HTTP timeout so a slow/large response is cut off by the client itself, surfacing as a distinct timeout the adapter maps to the existing neutral `provider_timeout`. Keep the SDK confined to this one module (provider-agnostic anti-goal).
- [ ] Drive the call-level deadline from a **config constant** (extend the existing `vendor_call_timeout_seconds` block in `apps/backend/app/config.py`, or add a sibling for the HTTP-level deadline if the SDK needs a separate value — no inline literal anywhere). The backend-effective bound MUST remain **shorter than** the frontend `WATCH_REQUEST_TIMEOUT_MS` (currently 12000ms) so the backend's honest error always wins when the backend is reachable. Document the ordering invariant in config.
- [ ] Make the oversize/timeout failure **actionable for the real cause**: when a Historical window times out (or is detectable as oversized/very-high-volume), return a distinct, actionable message (e.g. "that window is very high-volume — try a shorter range") via the existing `RealDataError` → `POST /watch/{ticker}` failure path / the existing row-9 `provider_timeout` reason. Do NOT emit a misleading generic "please try again" for a deterministically-oversized window. No new endpoint — extend the existing failure path's message/reason mapping.

**J-29 — fast historical load by design (concurrent fetch, no needless pre-flight, cached window, prompt warm-up)**
- [ ] In `_fetch_trades_quotes` (`alpaca.py`), fetch **trades and quotes concurrently** (e.g. `asyncio.gather` over two `to_thread` calls, or a thread pool) instead of the current sequential `get_stock_trades` then `get_stock_quotes`. Preserve exact ordering/merge semantics into the engine's logical timeline (quote-before-trade) — concurrency is a fetch optimization only; it MUST NOT reorder, drop, or fabricate any trade/quote.
- [ ] Remove the **needless pre-flight round-trip**: today `fetch_historical` calls `_require_tradable` (a separate `get_asset` call) before the data fetch. Fold the tradable/unknown-symbol determination into the data fetch path (an unknown symbol still maps to the existing `symbol_not_tradable`; an empty result still maps to `no_data_for_window`) so a successful fetch costs one round-trip's latency, not two — without weakening J-14's honest unknown-symbol / no-data states.
- [ ] Add a **bounded in-process cache of fetched historical windows** keyed by (symbol, start, end, feed) so re-watching the same symbol + window is near-instant (a cache hit skips the vendor round-trip entirely). Cache the raw `HistoricalWindow` (real trades + quotes), never a fabricated one; bound the cache size/age via config (no magic numbers). A cache miss behaves exactly as today.
- [ ] Ensure the engine **warms promptly** on a historical replay: deliver the warm-up events (up to `warmup_min_events`) with minimal initial pacing / a bounded fast-forward, then resume normal replay pacing — so the cockpit shows a warm read quickly. The fast-forward is **delivery pacing only**; engine math stays purely logical and deterministic (the same ordered stream yields identical features/state/confidence). Any new pacing/fast-forward bound is a config constant.
- [ ] These speed-ups MUST NOT introduce a timeout or error on a legitimate busy window, MUST NOT fabricate or drop trades/quotes, and a genuinely slow path MUST still resolve to the honest bounded state (J-28). During the fetch the UI shows the existing waiting/progress treatment (row-6 `waiting`, J-26), never a blank/idle screen.

**J-30 — warmed/cached symbol universe + min-query (backend half)**
- [ ] **Warm the tradable-symbol universe at startup** (or first availability): trigger `_asset_universe()` from the existing FastAPI `lifespan` hook (`main.py:96`) in the background (non-blocking startup; if credentials are absent it is a no-op and search stays an empty list, never an error). Optionally refresh it in the background on a config-driven interval. Keep the existing module-level `_ASSET_UNIVERSE` cache as the single owner — do NOT add a second universe store.
- [ ] Keep `GET /symbols/search` serving from the warmed cache (it already reads `_asset_universe()`); confirm a vendor hiccup still yields an **empty list, never an error or a stuck spinner** (the existing `try/except → []` in `main.py:277` and `is_available()` guard stay). Enforce the existing `symbol_search_min_query` so an over-broad single-character scan is avoided server-side.
- [ ] Any new warm/refresh interval or persistence path is config-driven (no magic numbers). *(Persistence across restarts is nice-to-have per the journey wording — if implemented it must be a real cache file, never committed vendor data and never fabricated symbols; if not implemented, the startup warm alone satisfies "not a multi-second stall".)*

### Frontend

**J-30 — cancellable, debounced, min-query symbol search (frontend half)**
- [ ] Add **request cancellation** to `searchSymbols` (`apps/frontend/lib/api.ts:141`): use an `AbortController` so a newer keystroke cancels the prior in-flight request — no pile-up and no out-of-order overwrite where a slow earlier response clobbers a newer one. An aborted request resolves to "no result" (not an error).
- [ ] Wire `SymbolSearch.tsx` (`apps/frontend/components/SymbolSearch.tsx`) to abort the previous request on each new debounced lookup (the existing `active` flag drops late results but does not cancel — replace/augment it with real cancellation). Keep the existing 250ms debounce; enforce a sensible **minimum query length** on the client (mirroring the backend `symbol_search_min_query`) so a single character does not fire an over-broad search. The debounce-ms and min-query MUST be config constants (extend `apps/frontend/lib/config.ts`; no inline literal).
- [ ] Free-text watch entry MUST always remain possible (the user can ignore the dropdown and Watch whatever they typed) — unchanged from today. A vendor hiccup / empty list shows no suggestions, never an error banner or a stuck "Searching…" spinner.

### New user-facing capability

- A Historical watch of a real liquid symbol over a busy regular-hours window (including the market-open minute) populates the cockpit with real values **fast** — and re-watching the same symbol + window is near-instant.
- A genuinely oversized/high-volume window that exceeds the budget fails with a clear, **actionable** message ("try a shorter range") instead of a misleading generic retry — and the user always sees the backend's honest error, not a client-side give-up.
- Symbol search feels instant: the first search after a backend restart is not a multi-second stall, rapid typing does not pile up or show out-of-order results, and a vendor hiccup quietly yields no suggestions.

### New information displayed

- An **actionable oversize/timeout message** for a high-volume Historical window on the existing error/failure panel (a more specific variant of the already-registered row-9 `provider_timeout` reason — not a new displayed engine value).
- No new tape value, no new panel, no new chart series. Tape state, confidence, features, bid/ask/spread/last, recent trades, observations, event log, price history, paused state, and `stream_status` are all unchanged and remain single-source-of-truth (rows 1–12).

### New user actions

- None. Watch, Pause/Resume, Stop, the data-source selector, the symbol search box, the historical window picker, and the bar-size selector are all unchanged. This iteration changes the **responsiveness and honesty** of existing actions, not the action set.

### UI surface changes

- No new page, no new route, no nav change. The only visible surface delta is: (1) the symbol-search dropdown behaves crisply (cancellable, min-query, no stale overwrite); (2) an oversize-window Historical Watch shows a more actionable error on the existing failure panel. Both live on the single `/` HOME cockpit.

### Product surface delta

- The product becomes trustworthy under real vendor latency: fast where it can be (cached/concurrent fetch, warmed search), honestly bounded where it must be (a real call-level deadline with the backend's actionable error winning), and never fabricating or dropping data to look fast.

### Blueprint conformance

- All work lives on the single `/` — Watch (the tape cockpit) — HOME. No new page, no new route, no nav-skeleton change. The symbol search box, the Historical window picker/error panel, and the cockpit waiting/progress treatment are all already-registered surfaces on `/`. **No re-approval requested** (no top-level section added/renamed/moved). This is an **additive** behavioral hardening of already-built surfaces.

### Data-contract additions

- **No new displayed value and no new endpoint.** This iteration hardens the *performance and honesty* of existing contract rows without adding a row:
  - **Row 9** (`Real-data availability / failure state`) is clarified additively: its existing `provider_timeout` reason is now enforced by a **real call-level vendor deadline** (an HTTP/SDK timeout at the adapter boundary, not only the `asyncio.wait_for` wrapper), and an oversize-window timeout maps to an **actionable** message variant — still the same single `POST /watch/{ticker}` failure path, the same single owner (Live/Historical provider + adapter), no second endpoint.
  - **Row 7** (`Symbol search results`) keeps its single computing owner (the vendor-agnostic adapter behind the provider seam) and single endpoint (`GET /symbols/search?q=`); the warmed/cached universe and the client-side cancellation are **performance** properties of the same row, not a new value or a second lookup.
  - **Rows 10–12 and the historical fetch** keep their single owners; the concurrent fetch + window cache are a **fetch optimization** of the same Historical provider path — the engine still computes OHLC/markers/features once and serves them verbatim (single source of truth), and a cached window replays the **same real** trades/quotes (no fabrication).
- New config constants (call-level HTTP deadline, window-cache size/age, any warm/refresh interval or fast-forward bound, the frontend debounce-ms / min-query) are **config values, not displayed values** — they live in `apps/backend/app/config.py` / `apps/frontend/lib/config.ts` (no magic numbers), and are not registered as Data Contract rows.

## OUT OF SCOPE

- Any change to tape-state classification, the 14 features, confidence, OHLC/marker computation, the aggressor/tick-test rule, or the engine math (rows 1–5, 10). This iteration touches the **vendor fetch + search responsiveness**, not the engine.
- Adding a second vendor adapter, Level-2 / `BookLevelEvent`, the predictive-edge replay harness, or persistence beyond an optional symbol-universe cache file (all explicitly *later* in `docs/goal.md`).
- Any new endpoint, page, route, or nav element. Any new displayed engine value.
- Relaxing or lengthening timeouts to "fix" J-29 — the journey explicitly requires fast **by design**, not a longer deadline.
- Changing the mid-stream `stale_gap_seconds` delivery watchdog or the `waiting`/`failed`/`stale` lifecycle (J-25–J-27, already passing) — those are a separate, settled concern.
- Any order/execution/broker affordance (no-execution anti-goal).

## DEFINITION OF DONE

- [ ] Target journeys J-28, J-29, J-30 pass via browser-qa-agent and/or backend tests as appropriate (J-28 backend bound + ordering + message by unit test; J-29 fetch concurrency / cache hit / warm-up by unit test, plus the fast-load UX; J-30 search cancellation + warm/min-query by unit test, plus the crisp dropdown — verified with credentials where the journey requires a real vendor, browser-verifiable where it does not).
- [ ] Required-still-passing journeys J-01–J-27 remain green (engine/classifier/history/pause/lifecycle untouched or provably additive; re-verify the sim floor and the Watch-lifecycle states after the search/fetch edits).
- [ ] No anti-goal violation introduced — in particular: a real call-level deadline (not just the wrapper); backend timeout < frontend timeout; actionable oversize message; concurrent fetch preserves order and fabricates/drops nothing; cached window is real data; warmed universe; cancelled stale searches; engine math single-source-of-truth and deterministic; SDK confined to the one adapter; no secrets committed; no execution path.
- [ ] Unit tests pass; no regressions (backend suite was 198 passed / 1 skipped at iter-10 — keep it green and add the new tests below).
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich-iter-11-dev.md` (and a frontend handoff for the search-cancellation change).

## TESTING REQUIREMENTS

- **Browser:**
  - **J-29** — Historical, a liquid symbol (e.g. `TSLA`) + a busy window including the market-open minute (09:30–09:31 ET or its local equivalent): cockpit populates with real values within the configured bound (never a routine timeout); re-watch the same symbol + window is near-instant; the fetch wait shows the waiting/progress treatment, never a blank/idle screen. *(With credentials; the evaluator may need to close the render gap on an isolated stack per the standing visual-evidence lesson — see NOTES.)*
  - **J-30** — Live/Historical, type a few characters quickly (e.g. "TSL", backspace, "AAP"): suggestions appear within a small bounded time after the debounce; the **first search after a backend restart** is not a multi-second stall; rapid typing shows no pile-up / out-of-order overwrite; a vendor hiccup yields an empty list (no error, no stuck spinner); free-text watch still works.
  - **J-28** — an oversized/high-volume Historical window surfaces the actionable "shorten the window" error on the failure panel (not a generic retry), within the bound.
- **Unit/integration:**
  - **J-28** — a test with a **slow / large vendor double** proving the deadline is enforced at the vendor-call boundary (the call is cut off by the client, not merely abandoned by the wrapper); a test asserting the backend-effective bound is **strictly less than** the frontend `WATCH_REQUEST_TIMEOUT_MS`; a test asserting an oversize/timeout maps to the **actionable** message/reason (not a generic retry) and creates **no** engine (`/tape/{ticker}/state` → 404, no fabricated tape).
  - **J-29** — a test proving trades+quotes are fetched **concurrently** (e.g. the two vendor calls overlap / total time ≈ max not sum, via a timed double); a test proving the **needless pre-flight is gone** (a successful fetch makes one round-trip, and an unknown symbol still maps to `symbol_not_tradable`, an empty window to `no_data_for_window`); a **cache-hit** test (a second fetch of the same (symbol, start, end, feed) does NOT call the vendor and replays the same real records); a **warm-up timing** test (warm-up events delivered with the bounded fast-forward; the resulting features/state/confidence are **identical** to the un-fast-forwarded replay — determinism preserved).
  - **J-30** — a backend test that the universe is warmed (a search right after startup does not trigger a per-request universe fetch / is served from cache); a frontend/unit test (or a documented Playwright assertion) that a newer search **aborts** the prior in-flight request and a late response cannot overwrite a newer result; a test that a vendor error in the search path yields `[]` (never an exception); a min-query test (below `symbol_search_min_query` ⇒ `[]`, no vendor call).
- **Error cases:**
  - Oversized window ⇒ actionable timeout message, no engine, no fabricated tape.
  - Unknown symbol on the folded fetch path ⇒ `symbol_not_tradable` (J-14 unchanged).
  - Empty window ⇒ `no_data_for_window` (J-14 unchanged).
  - Vendor error during search ⇒ empty list, never an error or stuck spinner.
  - No credentials ⇒ search is an empty list and the startup warm is a no-op (J-14 `provider unavailable` for watch unchanged).
  - A cancelled (aborted) search ⇒ resolves to no result, not an error.

## NOTES

- **Heed the lessons (episodic memory):**
  - **iter-3/6/8/9/10 shared-`.next` corruption + visual-evidence lesson** (`lessons.md`): the harness frontend on `:3650` has repeatedly been left with a corrupted `.next` (HTTP 500 `Cannot find module './833.js'`), so browser-qa records SKIPPED and the evidence dir comes back empty. A **visual/UX journey must not be promoted on backend+code inference alone**. If browser-qa is skipped, the evaluator is expected to close the render gap on an **isolated stack** (isolated `NEXT_DIST_DIR` + isolated backend port + real Chromium via Playwright; grep the served chunks for the iter's new strings before trusting a running server; hash the evidence dir — `md5sum *.png | uniq -c -w32` — before trusting any PASS table). J-29's "fast load" and J-30's "crisp/instant search" are partly UX-timed; capture real rendered/timed evidence.
  - **iter-2 naive-UTC / penny-spread-symbol lesson:** real-data fixtures and demos must use a **penny-spread** symbol for a clean state (Ford reads clean `bid_absorption`; high-priced AAPL honestly reads `unclear` on the wide IEX top-of-book). For J-29's busy-window timing, a liquid symbol (TSLA/AAPL) is fine because the journey is about **load speed**, not the resolved state; do not assert a particular tape state for J-29.
  - **iter-0 orphaned-watch-on-switch lesson:** a new Watch / source-or-symbol switch does not implicitly Stop the prior watch — relevant only if the fetch/cache work touches the watch lifecycle; this iteration should not, but do not regress it.
  - **iter-4 live-socket-teardown deadlock lesson:** do NOT call the SDK's `unsubscribe_*()` from the live generator `finally` (it deadlocks on the event-loop thread). This iteration targets the **historical fetch + search** paths, not live-socket teardown — leave `stream_live`'s bounded graceful close untouched.
- **Credentialed verification:** J-28 (oversize timeout), J-29 (busy-window load + cache), and J-30 (real universe warm) are credential-gated for their real-vendor legs. Prefer the established **committed real-vendor fixture / hermetic double** pattern for the in-loop deterministic proofs (a slow/large vendor double for J-28; a timed concurrency double + a cache-hit assertion for J-29; a warm/abort assertion for J-30) — never synthesized market data. The against-live-vendor leg may remain operator-gated, as for J-11/J-12/J-16/J-18.
- **GOAL_ACHIEVED candidate:** these are the last three unbuilt Must-haves. After J-28/J-29/J-30 pass with concrete evidence and zero regressions across J-01–J-27 (and COHERENCE-PASS), the full Must-have set J-01–J-30 is complete and the evaluator may declare GOAL_ACHIEVED.
- **Process note (recurring):** no audit handoff was produced in several prior iterations (iter-2/3/5/10) — if the audit step runs, ensure `docs/handoffs/goal-i_will_be_super_rich-iter-11-audit.md` is written; otherwise the evaluator will perform the skeptical anti-goal verification directly via git-grep + a full local test run.
