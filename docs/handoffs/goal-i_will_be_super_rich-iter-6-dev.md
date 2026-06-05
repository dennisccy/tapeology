# goal-i_will_be_super_rich-iter-6 Dev Handoff

**Phase:** goal-i_will_be_super_rich-iter-6
**Date:** 2026-06-05
**Agent:** developer
**Status:** complete

## What Was Built

Tape-state prediction chart (J-17 + J-18) — candlestick price chart + tape-state-transition
markers, with a 10/30/60 s bar-size selector, shown above the cockpit for **Simulated and
Historical** only. Implements the already-registered Data Contract **row 10** on the existing `/`
HOME. No new nav section, no new page, no blueprint edit.

Backend:
- **Engine history buffer** (`app/engine/history.py`, owned by `TapeEngine`): accumulates the
  watched **trade price into OHLC candles at three concurrent bin sizes (10 / 30 / 60 s)**,
  bucketed by the engine's **logical timestamp** (never wall-clock), and appends a
  **tape-state-transition marker** `{timestamp, state, confidence}` whenever the classified
  `tape_state` changes **to a meaningful state** (`buyer_control` / `seller_control` /
  `bid_absorption` / `ask_absorption`). A transition **to** `unclear` is not marked. Markers reuse
  the engine snapshot's **own** `tape_state` / `confidence` for that tick — no second
  classification. Candles bin the same price the snapshot exposes as `last` — no second price
  source. Accrual happens **only** in `process_event` (per real events), never in
  `set_stream_status` or construction, so a status flip cannot mutate the series.
- **Read-only exposure**: `TapeEngine.history` property returns the buffer; `serialize_history`
  is a pure projection.
- **New route** `GET /tape/{ticker}/history?bar=<10|30|60>`: returns the selected bar size's OHLC
  series + the marker series. 404 for a not-watched ticker; **422** for an out-of-set `bar` (never
  silently coerced); empty buffer ⇒ `{bar, bars: [], markers: []}` at HTTP 200 (no invented
  candles). Works for simulated + historical (the backend does not special-case mode).
- **Config keys** (no magic numbers): `history_bar_sizes = (10, 30, 60)`,
  `history_marker_states` (the four meaningful states), `history_max_bars`, `history_max_markers`.

Frontend:
- Added **`lightweight-charts` v5.2.0** (candlestick-native, client-only, tiny, supports series
  markers) to `apps/frontend/package.json`.
- **`PriceChart` component** (`apps/frontend/components/PriceChart.tsx`): renders the OHLC
  candlesticks plus colored markers (emerald = buyer_control, rose = seller_control, amber =
  absorption), with a 10/30/60 s bar-size selector and library-default pan/zoom. Reads **only**
  from `GET /tape/{ticker}/history` (polled on a 1 s cadence — matches the WS push interval; no
  second WebSocket). Recomputes no price/side/state. Empty/idle treatment ("Loading…" /
  "No price history for this window yet") — never placeholder candles. The chart library is
  imported **dynamically inside an effect**, so it never runs during server render (no SSR).
- **Mounted above `<Cockpit>`** in `apps/frontend/app/page.tsx`, rendered only when
  `mode === "sim" || mode === "historical"` (hidden for `live`).

## Files Changed

- `apps/backend/app/engine/history.py` -- NEW: the engine history buffer (OHLC accumulators per
  bar size + meaningful-transition markers); `OhlcBar` / `TapeMarker` frozen dataclasses.
- `apps/backend/app/engine/tape_engine.py` -- construct the buffer; feed each trade price in
  `process_event`; note the state transition (using the snapshot's own state/confidence) after the
  snapshot is built; expose `TapeEngine.history` read-only.
- `apps/backend/app/config.py` -- add `history_bar_sizes`, `history_marker_states`,
  `history_max_bars`, `history_max_markers`.
- `apps/backend/app/serializers.py` -- add `serialize_history(history, bar)` (pure projection:
  OHLC list + marker list).
- `apps/backend/app/main.py` -- add `GET /tape/{ticker}/history` (404 / 422 / empty-200 contract).
- `apps/backend/tests/test_history.py` -- NEW: engine-buffer tests.
- `apps/backend/tests/test_history_api.py` -- NEW: `…/history` projection + error-case tests.
- `apps/frontend/package.json` / `package-lock.json` -- add `lightweight-charts ^5.2.0`.
- `apps/frontend/components/PriceChart.tsx` -- NEW: candlestick chart + markers + bar-size
  selector; client-only; reads `…/history`; empty-state treatment.
- `apps/frontend/lib/api.ts` -- add `fetchHistory(ticker, bar)`.
- `apps/frontend/lib/types.ts` -- add `OhlcBar`, `TapeMarker`, `TapeHistory`, `HISTORY_BAR_SIZES`,
  `HistoryBarSize`.
- `apps/frontend/app/page.tsx` -- mount `<PriceChart>` above `<Cockpit>` for sim/historical only.
- `apps/frontend/next.config.mjs` -- add an **env-gated** `distDir` override (`NEXT_DIST_DIR`),
  unset by default — used so a one-off build never clobbers the running dev server's shared
  `.next`. Normal `npm run dev` / `npm run build` behaviour is unchanged.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **159 passed, 1 skipped** (up from 141 passed / 1 skipped at iter-5 — 18 new tests, no
regressions; the count rose as required by the plan's no-regression cross-check).

Frontend type-check: `cd apps/frontend && npx tsc --noEmit` → clean (exit 0).
Frontend build: `cd apps/frontend && NEXT_DIST_DIR=.next-iter6-build npm run build` → compiled
successfully; `/` prerendered as static content (confirms no SSR violation from the chart). The
isolated dist dir was removed afterward; the shared `.next` and `next-env.d.ts` / `tsconfig.json`
were left untouched (the build's auto-edits to those two files were reverted).

Live backend verification (uvicorn on an isolated port 8777, then torn down):
- `POST /watch/SIM-BUYER` → resolves to `buyer_control`; `GET …/history?bar=10` returns real
  candles (price climbing 100.03 → 100.19) + exactly **1** `buyer_control` marker carrying the
  engine's own confidence (0.723). `bar=30` / `bar=60` collapse to 1 coarser bar each; the marker
  count is shared across bar sizes.
- Error cases live: not-watched → **404**; `bar=7` and `bar=abc` → **422** (`detail: "bar must be
  one of: 10, 30, 60"`); no `?bar=` → **200** with the default bar.

## Known Issues

- **J-18 real-fetch correctness is not exercised live here** (no vendor credentials were used in
  this dev pass). The backend correctness guarantee for J-18 is the `…/history`-agrees-with-engine
  test (`test_history_api.py`) plus the determinism/binning tests, exactly as the plan specifies;
  the chart **surface** (candles render, bar-size switches, empty/honest behaviour) is
  browser-verifiable on simulated data without a feed. With credentials present, a Historical watch
  of a penny-spread name (e.g. Ford) over a past RTH window will populate real candles through the
  same engine + endpoint path verified above on sim data. No code path special-cases the mode.
- **Bar-size switch re-fetches** (the poll effect re-runs on `barSize` change) and the candle data
  is re-`setData` into the existing series — there is a brief moment before the first re-fetch lands
  where the prior bar size's candles remain; this is cosmetic and resolves within the 1 s poll.
- The history buffer is **in-memory and bounded** (`history_max_bars` / `history_max_markers`,
  Phase-1 — no persistence), so a very long replay retains only the most recent candles/markers.
