# Phase goal-i_will_be_super_rich-iter-13 — UI Surface Map

**Phase:** goal-i_will_be_super_rich-iter-13
**Date:** 2026-06-09
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|---------------------|-------------|-------------|--------------|
| `/` | `TopBar` — Historical replay-speed `select` (1× / 2× / 5× / 10×) | Changed behavior | J-32: speed dropdown now calls `POST /watch/{ticker}/speed` on a running replay instead of staging for the next Watch | While a historical replay is actively running, change the speed from 1× to 10× — verify the cadence of incoming candles/trades visibly accelerates within ~1 second and the cockpit does not reload or lose its current chart position |
| `/` | `TopBar` — replay-speed `select` when no watch is running | Unchanged behavior confirmed | J-32: verify pre-watch staging path was not broken | With no watch running, select 5× from the speed dropdown, then start a new Historical Watch — verify the replay starts at 5× cadence, not at the default 1× |
| `/` | Tape-state panel (row 1) — state label + confidence bar | Changed behavior | J-33: classifier now uses relative spread (bps) and relative price impact (return) rather than absolute dollar constants | Load a Historical replay for a real sub-$100 ticker that made a clear directional move (e.g. a session with strong one-sided price progress); verify the state label reads `seller_control` or `buyer_control` (red or green) and confidence is above the display threshold, not stuck on `unclear` (amber) |
| `/` | Tape-state panel (row 1) — state label | Changed behavior | J-33: a tape with high one-sided aggression but no proportionate price progress must still read `unclear` or absorption | Load a Historical replay for a tape with heavy selling aggression but negligible price change; verify the state panel shows `unclear` or `ask_absorption` (amber), not `seller_control` |
| `/` | Historical quick-pick row — "Full RTH 9:30–16:00" button | Changed behavior | J-34: long windows now load via chunked parallel sub-window fetches instead of being refused | With Alpaca credentials configured, click the Full RTH quick-pick for a liquid symbol (e.g. SPY); verify the watch starts and the chart populates with tape data rather than displaying the "very high-volume — try a shorter range" error banner |
| `/` | Historical window loading — error banner | Changed behavior | J-34: "very high-volume" error is now a true backstop for genuinely oversized windows, not the routine outcome for multi-hour windows | Confirm that a normal multi-hour window (e.g. 2-hour pick for a liquid symbol) no longer triggers the "shorter range" error banner during loading; also confirm that a window large enough to genuinely exceed the budget still shows the actionable "shorter range" error banner |
| `/` | Error banner (top of page) | Unchanged — existing path now also handles speed-change failures | J-32: a failed `setReplaySpeed` call (e.g. 404 on a non-running replay) surfaces here | Simulate a speed change against a stopped replay (if reachable) and verify the error banner appears with a message; confirm no error banner appears on a successful mid-replay speed change |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/watch_manager.py` — added per-ticker mutable speed cell (`set_speed`, `stop` cleanup, `_feed_paced` reads current speed each iteration) — no directly rendered value; behavior is mediated through the new `POST /watch/{ticker}/speed` endpoint which the frontend already consumes.
- `apps/backend/app/config.py` — new relative classifier gate constants (`max_stable_spread_bps`, `min_buy_price_impact_return`, `max_sell_price_impact_return`, `absorption_flat_band_return`, `impact_return_scale`) and chunked-fetch bounds (`historical_chunk_seconds`, `historical_chunk_max_concurrency`) — these are internal tuning constants; they alter computed outputs already shown in the UI but are not surfaced as displayed values.
- `apps/backend/app/engine/features.py` — new `reference_price` feature (in-window mid/last price) — appears in raw `/features` JSON output and the WebSocket `features` payload; not rendered as a new cockpit readout.
- `apps/backend/app/engine/classifier.py` — relative spread/impact gates with absolute fallback — recalibrates the tape-state value already shown in the tape-state panel; no new displayed field.
- `apps/backend/app/providers/adapters/alpaca.py` — `_split_window` helper + chunked, bounded-concurrency, epoch-stitched `_fetch_trades_quotes` — changes how data is fetched; the resulting window data is rendered by the existing chart and tape panels.
- `apps/backend/tests/test_speed_api.py` — new test file — no UI surface.
- `apps/backend/tests/test_classifier_relative.py` — new test file — no UI surface.
- `apps/backend/tests/test_chunked_fetch.py` — new test file — no UI surface.

---

## Summary

- **Frontend surfaces changed:** 3 (TopBar.tsx, lib/api.ts, app/page.tsx)
- **New pages/routes:** 0
- **Modified components:** 1 (TopBar replay-speed dropdown behavior)
- **Navigation changes:** no
- **Backend-only changes:** 8 (watch_manager, config, features, classifier, alpaca adapter, 3 new test files)
