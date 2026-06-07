# goal-i_will_be_super_rich-iter-11 Execution Plan

Vendor responsiveness — the last three unbuilt Must-haves (J-28, J-29, J-30). Make every
credential-gated vendor path **honestly bounded** (a real call-level deadline whose error beats
the client) and **fast by design** (concurrent historical fetch + folded pre-flight + window
cache + prompt warm-up; warmed/cancellable symbol search). This is the GOAL_ACHIEVED-candidate
slice: after J-28–J-30 pass with evidence and zero regression across J-01–J-27, the full
Must-have set J-01–J-30 is complete.

**Additive hardening only.** No new endpoint, route, page, nav element, displayed engine value,
or second `stream_status`/contract writer. The engine math (rows 1–5, 10), the classifier, the
chart, the side/tick rule, and the J-25–J-27 lifecycle are untouched. The only behavioral deltas
are: row-9 timeout now enforced at the vendor-call boundary with an actionable oversize message;
row-7 search served from a warmed cache with client-side cancellation; the historical fetch path
optimized (concurrency + folded pre-flight + cache + warm-up) while replaying the **same real**
records. COHERENCE-PASS for iter-10 — no consolidation owed; add this scope directly.

## What to Build

**J-28 — a true call-level vendor deadline, backend<frontend ordering, actionable message**
- Enforce a real HTTP-level deadline at the vendor-call boundary inside the one adapter
  (`alpaca.py`) — not only the existing `asyncio.wait_for` wrapper in `main.py`. The pinned
  `alpaca-py==0.43.4` client constructors expose **no** `timeout` kwarg (verified — see SDK Seam
  below); set a default request timeout on the SDK client's underlying `requests.Session` so a
  slow/large response is cut off by the client itself, surfacing as a distinct timeout the adapter
  maps to the existing neutral failure → row-9 `provider_timeout`. SDK stays confined to `alpaca.py`.
- Drive the HTTP deadline from a **config constant** (extend the `vendor_call_timeout_seconds`
  block in `config.py`; add a sibling HTTP-level constant since the SDK needs its own value — no
  inline literal). The HTTP deadline MUST be ≤ the existing `wait_for` wrapper bound, and the
  backend-effective bound MUST stay strictly **shorter than** the frontend `WATCH_REQUEST_TIMEOUT_MS`
  (12000ms) so the backend's honest error always wins. Document the ordering invariant in config.
- Make the oversize/timeout failure **actionable**: a Historical window that times out (or is
  detectably oversized/high-volume) returns a distinct, actionable message (e.g. "that window is
  very high-volume — try a shorter range") via the existing `RealDataError` → `POST /watch/{ticker}`
  row-9 `provider_timeout` path. No generic "please try again" for a deterministically-oversized
  window. No new endpoint — extend the existing failure path's message/reason mapping only.

**J-29 — fast historical load by design**
- In `_fetch_trades_quotes` (`alpaca.py`), fetch **trades and quotes concurrently** (two
  `to_thread` calls under `asyncio.gather`, or a thread pool) instead of sequential
  `get_stock_trades` then `get_stock_quotes`. Preserve exact merge/ordering into the engine's
  logical timeline (quote-before-trade) — concurrency is a fetch optimization only; it MUST NOT
  reorder, drop, or fabricate any trade/quote. (Note: `_fetch_trades_quotes` is currently sync; the
  concurrency belongs at the async boundary — see Sharp Edges.)
- Remove the **needless pre-flight round-trip**: `fetch_historical` today calls `_require_tradable`
  (`get_asset`) before the data fetch. Fold the tradable/unknown-symbol determination into the data
  fetch (an unknown symbol still → `SymbolNotTradable`/`symbol_not_tradable`; an empty result still
  → `NoDataForWindow`/`no_data_for_window`) so a successful fetch costs one round-trip's latency,
  not two — without weakening J-14's honest states.
- Add a **bounded in-process cache of fetched historical windows** keyed by (symbol, start, end,
  feed); a cache hit skips the vendor round-trip and replays the **same real** `HistoricalWindow`
  (never fabricated). Bound size/age via config (no magic numbers). A cache miss behaves as today.
- Ensure the engine **warms promptly** on a historical replay: deliver the first up-to-
  `warmup_min_events` warm-up events with minimal initial pacing / a bounded fast-forward, then
  resume normal `_feed_paced` pacing — so the cockpit shows a warm read quickly. Fast-forward is
  **delivery pacing only**; engine math stays purely logical/deterministic (same ordered stream ⇒
  identical features/state/confidence). Any new fast-forward bound is a config constant.
- These speed-ups MUST NOT introduce a timeout/error on a legitimate busy window, MUST NOT
  fabricate/drop trades/quotes, and a genuinely slow path still resolves to the honest bounded
  state (J-28). During the fetch the UI shows the existing row-6 `waiting` treatment (J-26).

**J-30 — warmed/cached symbol universe + cancellable client search**
- Backend: **warm the tradable-symbol universe at startup** — trigger the universe load from the
  FastAPI `lifespan` startup (currently `lifespan` only `yield`s then shuts down) in the
  background (non-blocking startup; no creds ⇒ a no-op, search stays `[]`, never an error). Keep the
  existing module-level `_ASSET_UNIVERSE` cache as the **single** owner — do NOT add a second store.
  Route the warm through the neutral adapter seam, not by naming the SDK in `main.py` (see Sharp
  Edges). Optional config-driven background refresh interval. `GET /symbols/search` keeps serving
  from the warmed cache (its existing `try/except → []` + `is_available()` guard + the
  `symbol_search_min_query` enforcement stay).
- Frontend: add **request cancellation** to `searchSymbols` (`api.ts`) via an `AbortController` so a
  newer keystroke cancels the prior in-flight request — no pile-up, no out-of-order overwrite. An
  aborted request resolves to "no result" (`[]`), not an error. Wire `SymbolSearch.tsx` to abort the
  previous request on each new debounced lookup (replace/augment the existing `active`-flag late-drop
  with real cancellation). Keep the 250ms debounce but move it (and a client min-query mirroring the
  backend `symbol_search_min_query`) into `config.ts` — no inline literal. Free-text watch entry
  stays possible; a vendor hiccup/empty list shows no suggestions, never an error banner or stuck
  "Searching…".

## Agents Required

- developer: yes -- one cross-cutting change. **Backend:** the HTTP-level vendor deadline + the
  actionable oversize message + concurrent fetch + folded pre-flight + the bounded window cache +
  the warm-up fast-forward + the startup universe warm, all behind the existing seams, plus new
  config constants and the new unit tests below. **Frontend:** `AbortController` cancellation in
  `searchSymbols`, `SymbolSearch.tsx` real cancellation, and the `config.ts` debounce/min-query
  constants. Single owner (the change is tightly coupled along the vendor-fetch + search path).

## Frontend Present
yes

## Files to Create/Modify

- `apps/backend/app/providers/adapters/alpaca.py` -- set an HTTP request timeout on the SDK
  client `requests.Session` (see SDK Seam); concurrent trades+quotes fetch; fold `_require_tradable`
  into the data fetch (drop the separate pre-flight); bounded (symbol,start,end,feed) window cache;
  a neutral universe-warm entry the API can call; map an HTTP timeout → the neutral timeout outcome.
- `apps/backend/app/providers/adapters/base.py` -- if the universe warm needs a neutral method on
  the `MarketDataAdapter` protocol (e.g. `warm_symbol_universe()`), add it here (doc only — keep the
  seam vendor-free). Only if `main.py` cannot warm via an existing neutral call.
- `apps/backend/app/config.py` -- add the HTTP-level vendor-deadline constant (sibling of
  `vendor_call_timeout_seconds`, documenting the HTTP-deadline ≤ wrapper < frontend ordering); the
  window-cache size/age; the warm-up fast-forward bound; any universe-refresh interval. No magic
  numbers; document the backend<frontend invariant.
- `apps/backend/app/main.py` -- fire the background universe warm from the `lifespan` startup
  (before the `yield`); extend the historical `provider_timeout` path to carry the actionable
  oversize message/reason. No new endpoint; the `asyncio.wait_for` wrapper stays as the backstop.
- `apps/backend/app/watch_manager.py` -- in `_feed_paced` (the historical replay feeder), deliver
  the first up-to-`warmup_min_events` events with the bounded fast-forward, then resume normal
  pacing. Delivery-pacing only — determinism preserved. (Touch ONLY `_feed_paced`; leave `_feed`,
  `_feed_live`, pause, and the stale watchdog untouched — J-19/J-25–J-27 are settled.)
- `apps/backend/tests/fakes.py` -- extend `FakeAdapter` with a slow/large vendor double, a
  fetch-concurrency timing lever, a cache-hit probe, and a universe-warm/search-count hook (reuse
  the existing seam doubles; never the prod path / synthesized market data).
- `apps/backend/tests/test_vendor_responsiveness.py` -- NEW: the J-28/J-29/J-30 unit tests below.
- `apps/frontend/lib/api.ts` -- `searchSymbols` gains an `AbortController` (per-call signal); an
  aborted request resolves to `[]` (not an error); keep the empty/short-query guard.
- `apps/frontend/lib/config.ts` -- add `SYMBOL_SEARCH_DEBOUNCE_MS` and `SYMBOL_SEARCH_MIN_QUERY`
  constants (no inline literal in the component).
- `apps/frontend/components/SymbolSearch.tsx` -- abort the prior in-flight request on each new
  debounced lookup (real cancellation, replacing the late-drop `active` flag); read debounce-ms +
  min-query from `config.ts`; enforce the client min-query; free-text entry unchanged.
- `docs/handoffs/goal-i_will_be_super_rich-iter-11-dev.md` -- dev handoff (required).
- `docs/handoffs/goal-i_will_be_super_rich-iter-11-frontend.md` -- frontend handoff for the
  search-cancellation change (spec asks for it explicitly).

## UI Evolution

- **New user-facing capability:** a busy real Historical window (incl. the market-open minute)
  populates the cockpit with real values **fast**, and re-watching the same symbol+window is
  near-instant; a genuinely oversized window fails with a clear, **actionable** "try a shorter
  range" message (not a misleading generic retry), and the user always sees the backend's honest
  error rather than a client-side give-up; symbol search feels instant — the first search after a
  backend restart is not a multi-second stall, rapid typing does not pile up or show out-of-order
  results, and a vendor hiccup quietly yields no suggestions.
- **New information displayed:** an **actionable oversize/timeout message** on the existing
  error/failure panel (a more specific variant of the already-registered row-9 `provider_timeout`
  reason — NOT a new displayed engine value). No new tape value, panel, or chart series; rows 1–12
  are unchanged and remain single-source-of-truth.
- **New user actions:** none. Watch, Pause/Resume, Stop, the data-source selector, the symbol
  search box, the historical window picker, and the bar-size selector are all unchanged. This
  iteration changes the **responsiveness and honesty** of existing actions, not the action set.
- **UI surface changes:** no new page/route/nav. The only visible deltas: (1) the symbol-search
  dropdown behaves crisply (cancellable, min-query, no stale overwrite); (2) an oversize-window
  Historical Watch shows a more actionable error on the existing failure panel. Both on the single
  `/` HOME cockpit.
- **Navigation changes:** none.

## Visual Requirements

- **Component patterns:** reuse the existing failure/error panel and TopBar error banner for the
  actionable oversize message (a more specific `provider_timeout` variant — no new component). Reuse
  the existing `SymbolSearch` dropdown idiom and the existing row-6 `waiting` treatment (J-26) for
  the fetch wait. No new component library, no raw-div soup.
- **Layout:** unchanged — the single `/` tape-cockpit. The search dropdown, the historical
  window/error panel, and the cockpit waiting/progress treatment are all already-registered surfaces.
- **Key visual effects:** restrained per DESIGN SYSTEM. No new effects invented; the oversize error
  reuses the existing rose/error treatment, the waiting state the existing amber-pulse `waiting` dot.
- **States to handle:** the fetch-wait progress state (existing row-6 `waiting`, J-26 — never a
  blank/idle screen); the actionable oversize/timeout error on the failure panel; the empty/short/
  hiccup search dropdown (no suggestions, no error, no stuck spinner); an in-flight search cancelled
  by a newer keystroke (resolves to no result, no flicker of stale matches).

## SDK Seam (load-bearing — verified against installed alpaca-py 0.43.4)

The pinned SDK exposes **no per-request `timeout`**:
- `StockHistoricalDataClient.__init__` and `TradingClient.__init__` have NO `timeout` parameter
  (verified via `inspect.signature`).
- The base `RESTClient` (`alpaca/common/rest.py`) builds `self._session = Session()` (line 69) and
  calls `self._session.request(method, url, **opts)` (line 195); the `opts` dict (lines 113–125)
  carries `headers`/`allow_redirects`/`params`/`json` but **no `timeout`**.
- Therefore a real HTTP deadline must be applied at the `requests.Session` layer of the
  constructed client — e.g. wrap the client's `_session.request` to inject a default `timeout`, or
  mount a timeout-bearing `HTTPAdapter`. This stays inside `alpaca.py` (the SDK-confinement
  anti-goal holds). The developer must confirm the exact session attribute on the live SDK before
  relying on it; if the SDK internals differ, fall back to a session-level `requests` timeout
  wrapper — do NOT guess a non-existent constructor kwarg, and do NOT drop down to raw HTTP
  (that would re-implement vendor specifics outside the SDK).

This HTTP deadline is the **real call-level bound** J-28 requires; the existing
`asyncio.wait_for(...)` wrapper in `main.py` stays as the outer backstop (it abandons the thread;
the HTTP timeout is what actually stops the call).

## Sharp Edges (call out to dev)

1. **Backend < frontend ordering (J-28):** `WATCH_REQUEST_TIMEOUT_MS = 12000` (config.ts) and
   `vendor_call_timeout_seconds = 8.0`. The NEW HTTP deadline ≤ the `wait_for` wrapper bound, and
   the backend-effective bound MUST stay strictly < 12000ms. A unit test MUST assert
   backend-effective-bound < frontend bound from config (not hardcoded).
2. **Concurrency at the async boundary (J-29):** `_fetch_trades_quotes` is a sync method called via
   one `to_thread` in `main.py`. To overlap the two vendor calls, run trades and quotes each in its
   own `to_thread` under `asyncio.gather` — keep the merge/order into the engine timeline identical.
   The timing test must prove total ≈ max(t_trades, t_quotes), not the sum.
3. **Single source of truth / no fabrication:** the window cache stores the **real**
   `HistoricalWindow` only; a cache hit replays the same real trades/quotes. The engine still
   computes OHLC/markers/features/state/confidence ONCE and serves them verbatim — no recomputation
   outside the engine, no synthesized records. (coherence-auditor hard-fails a contract value
   recomputed/served via a new path or a fabricated record.)
4. **Determinism (J-29 warm-up):** the warm-up fast-forward is delivery pacing ONLY — it must never
   enter `classify(...)` or any feature/score. A test MUST assert the fast-forwarded replay yields
   **identical** features/state/confidence to the un-fast-forwarded replay.
5. **Folded pre-flight must not weaken J-14:** after dropping the `get_asset` pre-flight, an unknown
   symbol MUST still map to `symbol_not_tradable` and an empty window to `no_data_for_window` — both
   from the folded fetch path. Existing J-14 tests must stay green.
6. **Universe warm without SDK leak (J-30):** the `lifespan` startup warm must go through the neutral
   adapter seam (e.g. a neutral `warm_symbol_universe()` on the adapter, or call the existing
   adapter accessor) — `main.py` must NOT name the SDK or `_asset_universe` directly. No-creds ⇒
   no-op, search stays `[]`. Keep `_ASSET_UNIVERSE` the single owner (no second store).
7. **iter-4 deadlock lesson:** this iteration touches the **historical fetch + search** paths, NOT
   live-socket teardown. Do NOT call the SDK's `unsubscribe_*()` from any `finally`; leave
   `stream_live`'s bounded graceful close and `_feed_live` untouched.
8. **No relaxing/lengthening timeouts to "fix" J-29:** the journey requires fast **by design**
   (concurrency + folded pre-flight + cache + warm-up), NOT a longer deadline. Do not raise
   `vendor_call_timeout_seconds` or `WATCH_REQUEST_TIMEOUT_MS` to pass J-29.

## Key Test Scenarios

Backend unit/integration (`apps/backend/tests/test_vendor_responsiveness.py`, using the seam
doubles in `tests/fakes.py` — never the prod path, never synthesized market data):

- **J-28:** a **slow/large vendor double** proves the deadline is enforced at the vendor-call
  boundary (the call is cut off by the client/HTTP timeout, not merely abandoned by the wrapper); a
  test asserts the backend-effective bound is **strictly less than** the frontend
  `WATCH_REQUEST_TIMEOUT_MS`; a test asserts an oversize/timeout maps to the **actionable**
  message/reason (not a generic retry) and creates **no** engine (`/tape/{ticker}/state` → 404, no
  fabricated tape).
- **J-29:** trades+quotes fetched **concurrently** (total ≈ max not sum, via a timed double); the
  **pre-flight is gone** (a successful fetch makes one round-trip; an unknown symbol still →
  `symbol_not_tradable`, an empty window → `no_data_for_window`); a **cache-hit** test (a second
  fetch of the same (symbol,start,end,feed) does NOT call the vendor and replays the same real
  records); a **warm-up timing** test (warm-up events delivered with the bounded fast-forward; the
  resulting features/state/confidence are **identical** to the un-fast-forwarded replay).
- **J-30:** the universe is **warmed** (a search right after startup does not trigger a per-request
  universe fetch / is served from cache); a vendor error in the search path yields `[]` (never an
  exception); a **min-query** test (below `symbol_search_min_query` ⇒ `[]`, no vendor call).
  Frontend cancellation proven by a frontend/unit assertion or a documented Playwright assertion
  (a newer search aborts the prior in-flight request; a late response cannot overwrite a newer
  result).
- **Error cases:** oversized window ⇒ actionable timeout message, no engine, no fabricated tape;
  unknown symbol on the folded path ⇒ `symbol_not_tradable`; empty window ⇒ `no_data_for_window`;
  vendor error during search ⇒ `[]`; no credentials ⇒ search `[]` and the startup warm is a no-op
  (J-14 `provider unavailable` for watch unchanged); a cancelled (aborted) search ⇒ no result.
- **Full suite green:** `cd apps/backend && .venv/bin/python -m pytest tests/ -v` — keep the iter-10
  floor (198 passed / 1 skipped), add the new tests, zero regressions across J-01–J-27 (re-verify
  the sim floor and the Watch-lifecycle states after the search/fetch edits).

Browser (browser-qa, by journey ID) — run against a **CLEAN isolated frontend**
(`NEXT_DIST_DIR` + `NEXT_PUBLIC_API_URL` → an isolated backend), NEVER the shared `:3650` `.next`
(iter-3/6/8/10 lesson). **Grep the served chunks for this iteration's new strings** before trusting
a running server; **hash the evidence dir (`md5sum *.png | uniq -c -w32`)** before trusting any PASS
table; assert on DOM text/timing, not just pixels (iter-9 placeholder-screenshot lesson). J-29's
"fast load" and J-30's "crisp/instant search" are partly UX-timed — capture real rendered/**timed**
evidence:

- **J-29** (with credentials) — Historical, a liquid symbol (e.g. `TSLA`) + a busy window including
  the market-open minute: the cockpit populates with real values within the configured bound (never
  a routine timeout); re-watch the same symbol+window is near-instant; the fetch wait shows the
  row-6 `waiting`/progress treatment, never a blank/idle screen. Do NOT assert a particular tape
  state for J-29 (it is about load speed — iter-2 penny-spread lesson; a liquid symbol is fine).
- **J-30** — type a few characters quickly ("TSL", backspace, "AAP"): suggestions appear within a
  small bounded time after the debounce; the **first search after a backend restart** is not a
  multi-second stall; rapid typing shows no pile-up / out-of-order overwrite; a vendor hiccup yields
  an empty list (no error, no stuck spinner); free-text watch still works.
- **J-28** — an oversized/high-volume Historical window surfaces the actionable "shorten the window"
  error on the failure panel (not a generic retry), within the bound.
- **Regression smoke:** J-01 (SIM-BUYER full cockpit + Buyer Control), J-10 (3-mode controls), J-13
  (symbol search returns matches), J-17 (sim chart), J-21 (synchronous connecting), J-24 (inline
  validation), J-26 (waiting treatment) re-verified on the same isolated stack — no Watch-flow or
  search regression.

## Out of Scope (excluded — do NOT build here)

- Any change to tape-state classification, the 14 features, confidence, OHLC/marker computation, the
  aggressor/tick rule, or engine math (rows 1–5, 10). This iteration touches the vendor fetch +
  search responsiveness, not the engine.
- A second vendor adapter, Level-2 / `BookLevelEvent`, the predictive-edge replay harness, or
  persistence beyond an **optional** symbol-universe cache file (all explicitly *later* in
  `docs/goal.md`). The startup warm alone satisfies "not a multi-second stall"; a persisted
  universe cache file is nice-to-have only and, if built, MUST be a real cache (never committed
  vendor data, never fabricated symbols).
- Any new endpoint, page, route, nav element, displayed engine value, or a SECOND
  `stream_status`/contract writer (the coherence-auditor hard-fails that drift).
- Relaxing/lengthening `vendor_call_timeout_seconds` or `WATCH_REQUEST_TIMEOUT_MS` to "fix" J-29
  (fast by design, not a longer deadline).
- Changing the mid-stream `stale_gap_seconds` watchdog or the `waiting`/`failed`/`stale`/`closed`
  lifecycle (J-25–J-27, settled); the live-socket teardown / `_feed_live` (iter-4 deadlock); pause
  behavior (J-19).
- Any order/execution/broker affordance (no-execution anti-goal).

## Goal Alignment & Risk Notes

- **Advances the goal:** closes the final "Bounded, honest, performant vendor calls" critical
  anti-goal and the last three Must-have journeys (J-28–J-30). After this iteration the full
  Must-have set J-01–J-30 is complete — the GOAL_ACHIEVED candidate.
- **Builds on existing architecture:** the `RealDataError` → row-9 `provider_timeout` path, the
  `asyncio.wait_for` wrapper, the `_ASSET_UNIVERSE` cache, the `FakeAdapter` seam doubles, the
  `SymbolSearch` debounce, and the row-6 `waiting` treatment all already exist — this change is
  additive to them, not a rebuild.
- **Credentialed verification:** J-28 (oversize timeout), J-29 (busy-window load + cache), J-30
  (real universe warm) are credential-gated for their real-vendor legs; creds are present in this
  environment's `apps/backend/.env` (per the iter-9 handoff). Prefer the established committed
  real-vendor fixture / hermetic double for the in-loop deterministic proofs; the against-live-vendor
  leg may remain operator-gated, as for J-11/J-12/J-16/J-18.
- **Process note:** if the audit step runs, ensure
  `docs/handoffs/goal-i_will_be_super_rich-iter-11-audit.md` is written; otherwise the evaluator
  performs the skeptical anti-goal verification directly via git-grep + a full local test run.
- **No spec/goal contradiction or scope creep detected.** The spec is precise, code-grounded, and
  self-disciplines scope (engine/lifecycle explicitly excluded). The one non-obvious risk is the
  SDK timeout seam (no constructor kwarg in alpaca-py 0.43.4) — flagged above with the verified line
  references so the developer applies a real session-level deadline rather than a non-existent kwarg.
