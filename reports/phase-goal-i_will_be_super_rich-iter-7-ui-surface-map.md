# Phase goal-i_will_be_super_rich-iter-7 — UI Surface Map

**Phase:** goal-i_will_be_super_rich-iter-7
**Date:** 2026-06-05
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `TopBar` — **Pause button** (amber, `px-2.5 py-1 text-xs font-semibold`) | New component | Pause/Resume control (J-19) added beside Stop | Watch SIM-BUYER, wait for `stream_status=live`, confirm an amber **Pause** button appears in the top bar beside Stop; confirm no Pause button appears before any watch is started |
| `/` | `TopBar` — **Resume button** (amber, replaces Pause when paused) | New component | Pause state must toggle the control to Resume | Click Pause on a live watch; confirm the Pause button is replaced by an amber **Resume** button; confirm no Stop is removed |
| `/` | `TopBar` — **PAUSED status dot** (amber, `bg-amber-400`, label "paused") | Changed behavior | New `paused` entry added to `STREAM_DOT` | While paused, confirm the top-right status dot shows an amber (non-pulsing) dot with the text "paused" — not "live", not "stale" |
| `/` | `TopBar` — **Pause/Resume button visibility logic** | Changed behavior | Buttons are hidden when stream is closed/idle | Stop a watch; confirm neither Pause nor Resume button appears in the "Watching …" cluster (the cluster itself disappears) |
| `/` | `Cockpit` — all panels (quote, recent trades, features, tape state) | Changed behavior | When paused, the engine emits no new snapshots so panels freeze | Click Pause on a live SIM-BUYER watch; confirm the trade count in Recent Trades does not increment for at least 5 seconds while the PAUSED indicator is shown |
| `/` | `PriceChart` — candlestick chart (Sim / Historical mode only) | Changed behavior | When paused, the engine appends no new candles so the chart freezes | Click Pause on a SIM-BUYER watch with candles visible; confirm the number of candles in the chart does not change for at least 5 seconds while paused |
| `/` | Full page — **Resume behavior: no fabricated data** | Changed behavior | On resume, counts must continue from the paused position, not jump | Click Pause, wait 3+ seconds, click Resume; confirm the Recent Trades count resumes incrementing from the exact count it had when Pause was clicked (no sudden large jump) |
| `/` | Full page — **Stop after Pause teardown** | Changed behavior | Stop must still fully close the session even when called on a paused watch | Pause a SIM-BUYER watch, then click Stop; confirm the cockpit returns to idle, the "Watching …" cluster disappears, and a fresh Watch call on SIM-BUYER succeeds (GET `/tape/SIM-BUYER/state` returns 404) |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/snapshot.py` — added `paused: bool = False` field and documented `"paused"` in the `stream_status` value set — flows to the UI via serializers; not an independent backend-only change (confirmed consumed).
- `apps/backend/app/engine/tape_engine.py` — `pause()`/`resume()` primitives; paused gate in `process_event` — internal engine mechanism powering the API routes (no direct UI coupling beyond what the routes expose).
- `apps/backend/app/watch_manager.py` — `pause(ticker)`/`resume(ticker)` + `_wait_while_paused`; feeder freeze logic — internal feeder mechanism (no direct UI coupling).
- `apps/backend/app/config.py` — `pause_poll_seconds: float = 0.02` — internal timing constant; no operator-visible effect.
- `apps/backend/tests/test_pause.py` — new engine + feeder pause/resume unit/integration tests — no UI surface affected.
- `apps/backend/tests/test_pause_api.py` — new `/pause` + `/resume` route tests — no UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 1 (the `/` home page, specifically the `TopBar` component and the existing cockpit/chart freeze behavior)
- **New pages/routes:** 0
- **Modified components:** `TopBar.tsx` (Pause/Resume buttons + PAUSED dot state); `page.tsx` (handlers); `lib/api.ts` (two new API call functions + `paused` on initial snapshot); `lib/types.ts` (`paused` field on `TapeSnapshot`)
- **Navigation changes:** no (no new routes, no new nav links)
- **Backend-only changes:** 6 (snapshot field + engine primitives + feeder freeze + config + 2 test files — all serve the wired-up UI feature)
