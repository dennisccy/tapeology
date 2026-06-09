# goal-i_will_be_super_rich-iter-13 Dev Handoff

**Phase:** goal-i_will_be_super_rich-iter-13
**Date:** 2026-06-09
**Agent:** developer
**Status:** complete

## What Was Built

- **J-32 — mutable replay speed.** New `POST /watch/{ticker}/speed` endpoint lets a user change the
  replay speed of a *running* historical replay and have it apply within ~1s — no re-fetch, no
  engine restart, no teardown. `WatchManager` now owns a per-ticker mutable speed cell that
  `_feed_paced` reads each loop iteration; `set_speed(ticker, speed)` mutates it. Out-of-set speed ⇒
  422 (validated against `CONFIG.allowed_replay_speeds`, backend-authoritative); not-watched ⇒ 404.
  Speed is delivery-pacing only — the engine processes the same ordered events with the same logical
  timestamps, so features/state/confidence are byte-identical at any speed (determinism preserved).
- **J-33 — relative spread/impact classifier gates.** The directional/absorption gates now judge
  "wide spread" and "clean price impact" *relative to the instrument's price level* — spread in
  basis points, impact as a return — instead of via absolute dollar constants tuned for the ~$100
  simulator. A new canonical `reference_price` feature (the in-window mid/last price) is computed
  once in the `FeatureEngine` and read by the classifier. When a price basis is present the relative
  cutoffs apply; when absent (legacy unit-test fixtures, or a cold/empty window) the classifier
  falls back to the absolute constants byte-identically. Result: a real ~$30–50 name with a
  proportionate (even absolute-$-wide) spread and a strong negative impact resolves to
  `seller_control` (mirror: `buyer_control`) instead of perpetual `unclear`; a genuinely wide
  *relative* spread or high aggression with no proportionate progress still reads `unclear` /
  absorption. The absorption gates remain the exact complement of the control impact condition.
- **J-34 — chunked long-window fetch.** The historical fetch path splits a long window (above
  `CONFIG.historical_chunk_seconds`, default 15 min) into bounded contiguous sub-windows fetched
  with bounded concurrency (`CONFIG.historical_chunk_max_concurrency`, default 4) and stitches them
  back in epoch order into one real window. The advertised Full-RTH quick-pick (and any multi-hour
  window) now loads for a liquid symbol instead of returning the "very high-volume" error. No
  fabricated/dropped/reordered/de-duplicated prints; a short window still makes a single call; the
  window cache makes a re-watch near-instant. This is fast by design (parallelized pagination), not
  a longer timeout — the backend bound stays shorter than the frontend client timeout, and the
  "shorter range" message remains a true backstop (J-28).
- **Frontend J-32 wiring.** The existing Historical replay-speed control now issues
  `POST /watch/{ticker}/speed` (not a re-Watch) when a historical replay is already running; the
  cockpit/chart continue from their current position at the new cadence. `setReplaySpeed` was added
  to `lib/api.ts` and a `handleSpeedChange` handler to the page.

## Files Changed

- `apps/backend/app/main.py` — added `SpeedRequest` model + `POST /watch/{ticker}/speed` route (422 out-of-set, 404 not-watched, mutate speed, return canonical summary).
- `apps/backend/app/watch_manager.py` — per-ticker mutable speed cell, `set_speed()`, `stop()` clears the cell, `_feed_paced` reads the current speed each iteration (accepts a cell or a bare float).
- `apps/backend/app/config.py` — new relative gate constants (`max_stable_spread_bps`, `min_buy_price_impact_return`, `max_sell_price_impact_return`, `absorption_flat_band_return`, `impact_return_scale`) and chunk bounds (`historical_chunk_seconds`, `historical_chunk_max_concurrency`).
- `apps/backend/app/engine/features.py` — new `reference_price` feature (in-window mid/last price level).
- `apps/backend/app/engine/classifier.py` — relative spread/impact gates + relative confidence components, with an absolute fallback when no `reference_price` basis is present.
- `apps/backend/app/providers/adapters/alpaca.py` — pure `_split_window` helper + chunked, bounded-concurrency, epoch-stitched `_fetch_trades_quotes`.
- `apps/backend/tests/test_speed_api.py` — NEW: J-32 route (422/404/live-apply/no-teardown) + determinism (same window at 1× and 10× ⇒ identical output; speed-change-mid-replay).
- `apps/backend/tests/test_classifier_relative.py` — NEW: J-33 regression fixture (relative seller/buyer control on a ~$40 shape) + negative guards (wide relative spread ⇒ unclear; no-progress ⇒ absorption; complement/keystone; absolute-fallback unchanged).
- `apps/backend/tests/test_chunked_fetch.py` — NEW: J-34 `_split_window` partition + chunked fetch split/in-order-stitch with no fabricate/drop/reorder/de-dup; config-sourced bounds.
- `apps/frontend/lib/api.ts` — added `setReplaySpeed(ticker, speed)`.
- `apps/frontend/components/TopBar.tsx` — speed control issues a live speed change when a historical replay is running (`replayRunning` derived from the canonical snapshot); new `onSpeedChange` prop.
- `apps/frontend/app/page.tsx` — `handleSpeedChange` wired to the TopBar.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: 259 passed, 1 skipped (the skipped test is the credential-gated live integration test).

Command (frontend): `cd apps/frontend && npm run build`
Result: compiled + type-checked successfully (no unit suite; user-facing behavior covered by browser QA).

## Known Issues

- **Credential-gated legs are not live-verified here.** J-33's real-GME confirmation (14-05-2024
  14:30–14:40 London) and J-34's real Full-RTH liquid-symbol load require Alpaca credentials, which
  are not configured in this environment. They are gated by the deterministic classifier regression
  fixture (J-33) and the chunk-split + in-order-stitch unit tests (J-34), both of which run with no
  keys and pass. The live external-data path (`fetch_historical`/chunked stitch) was therefore not
  exercised against the real vendor — only against the fake SDK and the committed real fixture.
- **`reference_price` is now serialized in `/features.windows` and the WS `features`.** It is a
  feature value (not a new "displayed" headline), so it appears in the per-window feature maps. The
  frontend reads only the named headline features, so nothing new renders; but a reviewer scanning
  the raw `/features` payload will see the extra key. This is intentional (single source of truth:
  the classifier reads the same canonical value).
- **`set_speed` on a non-paced watch (sim or live) returns 404.** Sim watches use the unpaced
  `_feed` and live watches use `_feed_live`; neither has a speed cell, so there is nothing to
  re-pace. This is correct (speed is a historical-replay concept), and the frontend only offers the
  speed control in Historical mode.
