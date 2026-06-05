# goal-i_will_be_super_rich-iter-6 Execution Plan

Tape-state prediction chart: candlestick price chart + tape-state-transition markers, with a
10/30/60 s bar-size selector, shown above the cockpit for **Simulated and Historical** only.
Targets J-17 + J-18 (built together — they share one mechanism). Full depth, first frontend
change of the J-16–J-20 extension. Required-still-passing: J-01–J-16.

This iteration **implements** the already-registered Data Contract **row 10** on the existing
`/` HOME. No new nav section, no new page, no blueprint edit, no re-approval. (Confirmed against
`blueprint.md` IA "Price chart (Simulated + Historical only)" and the iter-5 eval recommendation.)

## What to Build

- **Engine history buffer (computed once).** As each event is processed in
  `TapeEngine.process_event`, accumulate the watched **price into OHLC bars at three concurrent
  bin sizes (10 / 30 / 60 s)**, bucketed by the engine's **logical timestamp** (never wall-clock),
  and append a **tape-state-transition marker** `{timestamp, state, confidence}` whenever the
  classified `tape_state` changes **to a meaningful state** (`buyer_control`, `seller_control`,
  `bid_absorption`, `ask_absorption`). A transition **to** `unclear` is NOT marked. The marker's
  `state` and `confidence` MUST be the **same** values the classifier already produced for that
  tick (reuse `EngineSnapshot.tape_state` / `confidence` — Data Contract row 1); no second
  classification. Candles bin the same trade `price` the engine already derives (the value the
  snapshot exposes as `last`); no second price source.
- **Read-only exposure.** Surface the buffer either as a frozen field on `EngineSnapshot` or via a
  read accessor on `TapeEngine`. No second classifier, no second price source.
- **Config keys (no magic numbers).** Add the allowed bar sizes `(10, 30, 60)` and any
  marker-significance / OHLC-binning parameter to the single `Config` dataclass in
  `apps/backend/app/config.py`. No bar-size or threshold literal inline in engine code. The set of
  valid `bar` values comes from config.
- **New route `GET /tape/{ticker}/history?bar=<10|30|60>`** in `apps/backend/app/main.py`, served
  by a new pure projection in `apps/backend/app/serializers.py` (mirror the `serialize_*` pattern):
  returns the selected bar size's OHLC series + the marker series for the watched ticker. Works for
  **simulated + historical** (backend does not special-case mode; it serves whatever the engine
  accumulated — Live is hidden in the UI only).
- **Charting dependency.** Add **one** lightweight client-side financial-charting library to
  `apps/frontend/package.json` — recommended `lightweight-charts` (candlestick-native, tiny,
  supports custom series markers). Hard constraints: client-side only (no SSR), no new backend
  dependency, candlesticks + markers. NOT a general TA/indicator/drawing library.
- **`PriceChart` component** (`apps/frontend/components/PriceChart.tsx`): renders the OHLC
  candlesticks plus colored markers, with a 10/30/60 s bar-size selector and pan/zoom (library
  default). Reads **only** from `GET /tape/{ticker}/history`. It MUST NOT recompute price, side, or
  state, and MUST NOT bin candles or place markers from raw trades.
- **Mount above the cockpit** in `apps/frontend/app/page.tsx` (above `<Cockpit>`), rendered **only
  when `mode === "sim"` or `mode === "historical"`** and **hidden when `mode === "live"`**. Keep
  the page exactly one screen.
- **Empty/idle handling.** Before data arrives or for an empty historical window, show an **empty**
  chart / "no price history yet" treatment — never placeholder candles. Refresh as bars accrue
  during replay by polling `…/history` on the existing stream cadence; do **not** open a second
  WebSocket.

## Agents Required

- developer: yes -- backend (engine history buffer + config keys + `…/history` route + serializer
  projection) and frontend (charting dep + `PriceChart` + page mount + `api.ts`/`types.ts` types),
  with the unit/integration tests below. Single developer agent covers both backend and frontend.

## Frontend Present

yes

## Files to Create/Modify

- `apps/backend/app/engine/history.py` -- NEW (developer's choice of path): the engine history
  buffer — accumulates OHLC bars at 10/30/60 s by logical timestamp + meaningful-transition
  markers; computed once, owned by `TapeEngine`.
- `apps/backend/app/engine/tape_engine.py` -- in `process_event`, feed each trade price + the
  classified state/confidence into the buffer; expose the buffer read-only (snapshot field or
  accessor). Accrue **only on event processing** (see Assumptions) — not in `set_stream_status`.
- `apps/backend/app/engine/snapshot.py` -- if attaching to the snapshot: add a frozen field for the
  OHLC bars + markers (frozen/immutable, consistent with the existing dataclass).
- `apps/backend/app/config.py` -- add `history_bar_sizes = (10, 30, 60)` (or equivalent) and any
  marker-significance / binning parameter; one source of truth for the numbers.
- `apps/backend/app/serializers.py` -- add `serialize_history(snap, bar)` (pure projection of the
  buffer for the requested bar size: OHLC list + marker list).
- `apps/backend/app/main.py` -- add `GET /tape/{ticker}/history`: 404 for a not-watched ticker
  (reuse `_engine_or_404`); reject an out-of-range `bar` (not in config set) with a 4xx; empty
  buffer ⇒ `{bars: [], markers: []}` at HTTP 200 (no invented candles).
- `apps/backend/tests/test_history.py` -- NEW: engine-buffer tests (exact OHLC boundaries by
  logical ts at each of 10/30/60 s; markers only at meaningful transitions; determinism on replay;
  marker state/confidence == snapshot values; candle prices derive from the same price).
- `apps/backend/tests/test_api.py` (or a new `test_history_api.py`) -- `…/history` projection
  matches the engine buffer for a watched sim ticker; 404 not-watched; 4xx invalid `bar`; empty ⇒
  empty 200.
- `apps/frontend/package.json` -- add the one charting dependency.
- `apps/frontend/components/PriceChart.tsx` -- NEW: candlestick chart + markers + bar-size
  selector; client-only; reads `…/history`; empty-state treatment.
- `apps/frontend/lib/api.ts` -- add `fetchHistory(ticker, bar)` calling `GET /tape/{ticker}/history`.
- `apps/frontend/lib/types.ts` -- add `OhlcBar`, `TapeMarker`, and the `…/history` response type.
- `apps/frontend/app/page.tsx` -- mount `<PriceChart ticker mode .../>` above `<Cockpit>`, only for
  `sim`/`historical`, hidden for `live`.

## UI Evolution

- New user-facing capability: the user can see the watched price as a **candlestick chart with
  tape-state-transition markers** and switch the bar size between 10 / 30 / 60 s, for Simulated and
  Historical watches — turning the textual tape read into a testable visual one on the same screen.
- New information displayed: OHLC price candles (at the selected 10/30/60 s bar size) and colored
  markers at meaningful tape-state transitions, positioned above the existing cockpit.
- New user actions: a bar-size selector (10 s / 30 s / 60 s) on the chart; pan/zoom on the chart
  canvas.
- UI surface changes: a new `PriceChart` panel **above the cockpit on `/`**, shown for Simulated
  and Historical modes only (hidden for Live). No new page or route.
- Navigation changes: none. (All new UI lives on the existing `/` HOME; the chart pane was already
  described in the approved blueprint IA — no nav-skeleton change, no re-approval.)

## Visual Requirements

- Component patterns: a single `Panel`-framed chart pane (reuse the existing `components/Panel.tsx`
  wrapper so the chart matches the cockpit panels) containing the candlestick canvas; a small inline
  segmented bar-size selector (10 / 30 / 60 s) as plain buttons styled to match the cockpit (no new
  component library — DESIGN SYSTEM is hand-built panels).
- Layout: full-width chart pane spanning the top of the main content area, directly **above** the
  cockpit panel grid; the page remains exactly one screen.
- Key visual effects (from DESIGN SYSTEM, dark instrument-panel): calm dark surface
  (slate-950 / slate-900 panel, slate-800 border); restrained styling, no chrome. Marker colors
  carry the load-bearing semantics: **emerald** = `buyer_control`, **rose** = `seller_control`,
  **amber** = `bid_absorption` / `ask_absorption`; `unclear` is **unmarked**. Use the
  emerald/rose/amber tokens already defined in the DESIGN SYSTEM — do not invent ad-hoc hex.
  Configure the chart's own background/grid/text to the slate palette so it does not read as a
  bright third-party widget. Monospaced numerics on any price axis labels.
- States to handle: **loading/idle** — empty chart with a "no price history yet" message before
  data arrives; **empty window** (historical with no data) — same empty treatment, never invented
  candles; **active** — candles render and update as bars accrue during replay; the active bar-size
  button is visually distinct (selected state). No error state beyond the empty treatment (the
  cockpit-level honest non-cockpit panels already own real-data failures; for Live the chart is
  simply hidden).

## Key Test Scenarios

- **J-17 (browser, no credentials):** Watch `SIM-BUYER` → a candlestick chart renders and updates
  during replay; toggle bar size 10 → 30 → 60 s and confirm the candles re-render; confirm an
  **emerald** buyer_control marker appears. Then `SIM-SELLER` (down trend + **rose** seller marker)
  and `SIM-BIDABS` / `SIM-ASKABS` (**amber** absorption markers with price held). Confirm the chart
  is shown for Simulated and **hidden when the data source is switched to Live**.
- **J-18 (browser surface + backend correctness):** Historical watch of a real penny-spread symbol
  (e.g. Ford) over a past RTH window → candlesticks reflect the replayed real prices; the bar-size
  selector switches 10/30/60 s; markers align with tape-state transitions. Where QA has no
  credentials, verify the chart surface + bar-size + empty/honest behavior in the browser and rely
  on the backend bars-match-`…/history` test for the correctness guarantee.
- **Backend — engine buffer:** a known ordered event stream produces the expected OHLC bars at each
  of 10/30/60 s (assert exact bar boundaries by **logical** timestamp) and a marker **only** at
  meaningful state transitions (exact marker timestamps/states). Replaying the same stream yields
  identical bars + markers (determinism).
- **Backend — single source of truth:** marker `state`/`confidence` equal the engine snapshot's
  `tape_state`/`confidence` at that transition (no independent classification); candle prices derive
  from the same price the snapshot exposes.
- **Backend — projection + error cases:** for a watched sim ticker, `…/history` bars/markers equal
  the engine buffer for the requested `bar`; not-watched ⇒ **404**; out-of-range `bar` ⇒ **4xx**
  (not silently coerced); watched with no trades / empty window ⇒ **empty** bars + **empty** markers
  (200) and an empty chart in the UI.
- **No regression:** J-01–J-16 stay green; existing suite was **141 passed / 1 skipped** at iter-5
  and must not drop — the new tests must make the count **rise** (cross-check, do not trust a
  screenshot — iter-5 stale-evidence lesson). Dev handoff written at
  `docs/handoffs/goal-i_will_be_super_rich-iter-6-dev.md`.

## Assumptions (documented, not asked)

1. **Library:** use `lightweight-charts` (recommended in the spec) unless the developer hits a
   concrete SSR/packaging blocker, in which case any client-only candlestick+marker library that
   adds no backend dependency is acceptable. Mount it inside a `"use client"` component, imported
   dynamically / in an effect so it never runs during server render.
2. **Buffer accrual point:** candles + markers accrue in `process_event` (per real events only),
   keyed by logical timestamp. `_build_snapshot` also runs on `set_stream_status` and at
   construction — accrual must NOT happen there, or a status flip would mutate the series. The
   previous-state tracking for marker emission lives in the engine and reuses the classifier output
   already computed for the snapshot (no second classify call).
3. **Candles are driven by trade prices** (the watched price the engine derives, exposed as
   snapshot `last`); quotes do not create candles. An OHLC bar is emitted only for bins that contain
   at least one trade — empty bins are not invented.
4. **Chart data source in the UI:** `PriceChart` lives in `page.tsx` (which already holds `ticker`
   and `mode`); it polls `…/history` on a short interval (matching the WS push cadence) while a
   ticker is watched and mode is sim/historical. It does not consume the WS stream and does not open
   a second socket. (`useTapeStream` does not expose `ticker`/`mode`, so the chart reads them from
   page state.)
5. **Marker confidence display:** the marker carries `confidence` for completeness/tooltip use; the
   acceptance only requires the colored marker at the transition — confidence rendering is optional
   polish, not a gate.

## Scope Guard (excluded — flag if attempted)

- **J-19 (pause/resume)** and **J-20 (local-time window picker)** — deferred to later slices; do NOT
  start them here (rows 11–12 stay unimplemented).
- No technical indicators, overlays, studies, drawing tools, multi-pane/multi-symbol charts, volume
  sub-panes, or a second chart (Stay-in-scope / one-focused-chart anti-goals).
- No order/buy/sell/execution affordance, button, or annotation on or near the chart (No-execution
  anti-goal — critical).
- Do NOT show the chart in Live mode (hidden by design this iteration).
- Do NOT change the engine's classification, feature, side, or confidence logic, or the existing
  cockpit panels — the chart is purely additive and read-only.
- Do NOT persist the buffer (Phase 1 stays in-memory).

## Build/QA Caution (carried lessons — load-bearing this iteration)

- Adding a charting dependency runs `npm install`. QA/build MUST happen in an **isolated `.next`**,
  never against the harness's shared `.next` (`npm run build` against the shared dir corrupted the
  `:3650` dev server in iter-3). `npm install` must not clobber the running harness server.
- QA MUST NOT `git checkout` any file carrying uncommitted iteration edits (it previously discarded
  the developer's `page.tsx`).
- Authoritative correctness for J-18 is the **backend** bars-match-`…/history` test plus the test
  count rising from 141 — cross-check both; do not trust a pre-build screenshot or a stale
  verify-only re-baseline (iter-5 evidence lesson).
