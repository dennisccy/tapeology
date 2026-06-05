# Phase goal-i_will_be_super_rich-iter-6 — UI Surface Map

**Phase:** goal-i_will_be_super_rich-iter-6
**Date:** 2026-06-05
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `PriceChart` panel ("Price Chart — Tape-State Markers") | New component | Iter-6 adds candlestick chart with tape-state markers for Sim/Historical watches (J-17/J-18) | Watch `SIM-BUYER`, wait ~4 s; confirm a panel titled "Price Chart — Tape-State Markers" appears above the cockpit and contains a candlestick canvas with at least one emerald (green) arrow marker labeled "Buyer Control" |
| `/` | Bar-size selector buttons (10s / 30s / 60s) inside `PriceChart` | New component | Users need to switch candle granularity | With `SIM-BUYER` active and candles visible, click "30s"; confirm the active button gains the `bg-slate-700` filled style and the chart redraws at coarser candles within ~1 s; repeat for "60s" |
| `/` | `PriceChart` empty/loading state overlay | New component | Honest empty treatment required before data arrives | Watch any ticker in Sim mode and observe the chart panel immediately after clicking Watch: confirm it shows "Loading price history…" text (not candles) before the first poll completes |
| `/` | `PriceChart` empty-window state | New component | Honest empty treatment required when no trades exist | Watch a ticker that has no trade history (e.g. immediately after the backend is restarted and before any trades arrive); confirm the chart shows "No price history for this window yet" and does NOT show placeholder candles |
| `/` | `PriceChart` — seller_control marker (rose) | New component | SIM-SELLER produces a downtrend + seller transition | Watch `SIM-SELLER`; confirm a rose (red, `#fb7185`) arrow marker labeled "Seller Control" appears on the chart at the transition point |
| `/` | `PriceChart` — absorption markers (amber) | New component | SIM-BIDABS / SIM-ASKABS produce absorption transitions | Watch `SIM-BIDABS`; confirm an amber (`#fbbf24`) arrow marker labeled "Bid Absorption" appears; repeat with `SIM-ASKABS` and confirm "Ask Absorption" marker |
| `/` | `PriceChart` visibility gate (Live mode hidden) | Updated layout | Chart must not appear in Live mode per blueprint IA | With `SIM-BUYER` watched and chart visible in Sim mode, click the "Live" data-source selector in the TopBar; confirm the entire "Price Chart — Tape-State Markers" panel disappears and only the cockpit area remains |
| `/` | `PriceChart` reappears on mode return | Updated layout | Chart visibility is gated on `mode === "sim" || mode === "historical"` | After hiding the chart by switching to Live, switch back to Sim mode and watch `SIM-BUYER` again; confirm the chart panel reappears above the cockpit |
| `/` | `page.tsx` layout — chart above cockpit | Updated layout | `PriceChart` is mounted above `<Cockpit>` in the page render tree | Watch `SIM-BUYER` in Sim mode; confirm the Price Chart panel is visually above (higher on screen than) the cockpit's quote/trade panels, with no panel displaced or obscured |
| `/` | `PriceChart` pan/zoom interaction | New component | Library-default interaction enabled | With candles visible on `SIM-BUYER` in Sim mode, drag the chart canvas left and right; confirm the time axis pans. Scroll the mouse wheel on the canvas; confirm the time axis zooms in/out |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/history.py` — new in-process OHLC buffer + marker list owned by `TapeEngine`; no UI surface — consumed only by the serializer and then the `/history` endpoint, which the chart reads.
- `apps/backend/app/engine/tape_engine.py` — feeds the history buffer in `process_event` and exposes `.history`; no UI surface beyond the data it supplies to the endpoint already listed.
- `apps/backend/app/config.py` — adds `history_bar_sizes`, `history_marker_states`, `history_max_bars`, `history_max_markers`; operator-invisible config constants.
- `apps/backend/app/serializers.py` — adds `serialize_history(history, bar)` pure projection; no UI surface directly — called only by the `/history` route handler.
- `apps/backend/tests/test_history.py` — new engine-buffer unit tests; no UI surface.
- `apps/backend/tests/test_history_api.py` — new history-endpoint integration tests; no UI surface.
- `apps/frontend/next.config.mjs` — adds env-gated `NEXT_DIST_DIR` build isolation; no runtime behavior change; unset by default, invisible to operators.
- `apps/frontend/lib/api.ts` — adds `fetchHistory(ticker, bar)`; not a UI surface directly — wired only into `PriceChart`.
- `apps/frontend/lib/types.ts` — adds `OhlcBar`, `TapeMarker`, `TapeHistory`, `HISTORY_BAR_SIZES`, `HistoryBarSize`; compile-time only.

---

## Summary

- **Frontend surfaces changed:** 1 (the `/` home screen)
- **New pages/routes:** 0 (chart lives on the existing `/` page)
- **Modified components:** 1 (`page.tsx` — mounts `PriceChart` above `<Cockpit>`)
- **New components:** 1 (`PriceChart` — candlestick chart + markers + bar-size selector)
- **Navigation changes:** no
- **Backend-only changes:** 9 files (engine buffer, serializer, config, API route, tests, type defs, build config)
