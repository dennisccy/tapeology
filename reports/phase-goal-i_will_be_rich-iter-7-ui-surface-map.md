# Phase N — UI Surface Map

**Phase:** goal-i_will_be_rich-iter-7
**Date:** 2026-06-03
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `TopBar` — **Stop** button | New control | J-09 adds a deliberate "stop watching" action that issues `DELETE /watch/{ticker}` | Watch `SIM-BUYER`, confirm a **Stop** button appears beside the "Watching SIM-BUYER" label; on the idle screen (no ticker watched), confirm the Stop button is **absent** |
| `/` | `TopBar` → page body (`Cockpit` → `IdleState`) | Changed behavior | Clicking Stop calls `handleStop` → `setTicker(null)`, switching the body from cockpit to idle | While watching a live ticker, click **Stop**; confirm the main area replaces the populated cockpit with the idle state showing "No ticker watched" and **no stale numbers/frozen frame remain** |
| `/` | `TopBar` — status dot | Changed behavior | After Stop, `setTicker(null)` closes the WS client-side, so the dot returns to its pre-snapshot idle affordance | Click **Stop** while the dot reads **live**; confirm the dot returns to **idle** (grey) and no further snapshot updates arrive |
| `/` | `Cockpit` (re-watch path) | Changed behavior | Backend `stop()` removes the engine, so a later Watch builds a fresh cold engine | After stopping, re-enter the **same** ticker (`SIM-BUYER`) and click **Watch**; confirm the cockpit repopulates from cold (connecting → live → values), not a frozen/closed leftover |
| `/` | Error banner (`TopBar` error row) | Changed behavior | `handleStop` clears any error and returns to idle even if the DELETE call fails or returns 404 | Trigger Stop; confirm any prior error banner is cleared and the UI lands on idle regardless of backend response |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/watch_manager.py` — adds `WatchManager.stop(ticker) -> bool` (cancels feeder task, sets engine `stream_status` to `"closed"`, removes engine from registry). Drives behavior the user sees but has no direct UI surface of its own.
- `apps/backend/app/main.py` — adds `DELETE /watch/{ticker}` route (200 `{"status":"stopped"}` / 404 not-watched). Consumed by the frontend `stopTicker` call behind the Stop button — exercised via the UI, not directly visible.
- `apps/backend/tests/test_watch_manager.py` (new) and `apps/backend/tests/test_api.py` — unit/integration tests; no UI surface.
- `apps/frontend/lib/api.ts` — adds `stopTicker(ticker)` + `StopResult`; non-visual client wiring invoked by the Stop button (404 treated as effectively-stopped).

---

## Summary

- **Frontend surfaces changed:** 1 route (`/`), 3 components touched (`TopBar`, `page.tsx`, `lib/api.ts`)
- **New pages/routes:** 0
- **Modified components:** `TopBar` (new Stop button), `page.tsx` (new `handleStop`), `lib/api.ts` (new `stopTicker`)
- **Navigation changes:** no
- **Backend-only changes:** 4 (`watch_manager.py`, `main.py`, and 2 test files)
