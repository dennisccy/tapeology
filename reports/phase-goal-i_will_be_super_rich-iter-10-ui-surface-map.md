# Phase goal-i_will_be_super_rich-iter-10 — UI Surface Map

**Phase:** goal-i_will_be_super_rich-iter-10
**Date:** 2026-06-07
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `WaitingState` (new, in `IdleState.tsx`) | New component | J-26: connected stream with no first trade must show an explicit named treatment instead of blank panels | Click Watch for a ticker whose snapshot arrives with `stream_status === "waiting"`; confirm the DOM contains the text "waiting for the first trade" and the ticker symbol, and that the full panel grid (Quote, Trades, Features, etc.) is NOT rendered |
| `/` | `Cockpit.tsx` — backstop guard | Changed behavior | J-26: prevent the Cockpit from ever rendering the full panel grid while `stream_status === "waiting"` | Pass a snapshot with `stream_status === "waiting"` into the Cockpit; confirm `WaitingState` is rendered and none of the six cockpit panels (TapeState, Quote, Features, RecentTrades, Observations, EventLog) appear |
| `/` | `app/page.tsx` — snapshot routing | Changed behavior | J-25/J-26/J-27: route `waiting`, snapshot-borne `failed`, and transient `connecting` snapshots to their explicit treatments; guard against empty cold-start snapshot rendering the full cockpit grid | With a snapshot whose `stream_status === "failed"`, confirm the `StreamFailedState` panel appears (data-testid="stream-failed-state") and the cockpit grid is absent; with `stream_status === "waiting"`, confirm `WaitingState` appears (data-testid="waiting-state") and the cockpit grid is absent |
| `/` | `app/page.tsx` — error banner (`bannerError`) | Changed behavior | J-27: error banner now also surfaces the message for a snapshot-borne `stream_status === "failed"` | While a snapshot reads `stream_status === "failed"`, confirm the TopBar error banner displays the text "The tape feed failed after connecting. No tape is shown." |
| `/` | `app/page.tsx` — price chart visibility | Changed behavior | Price chart must not render when the tape has no data (waiting or failed states); previously only suppressed during pre-snapshot failure | With a snapshot in `waiting` state (sim or historical mode), confirm the `PriceChart` component is not mounted in the DOM; confirm it reappears once `stream_status` advances to `live` |
| `/` | `TopBar.tsx` — `STREAM_DOT` `waiting` entry | New component state | J-26: status dot must read "waiting" (amber pulse) while stream is open but empty — never "live" | While `stream_status === "waiting"`, inspect the TopBar status dot label; confirm it reads "waiting" and has the amber pulsing style, not the green "live" style |
| `/` | `TopBar.tsx` — `STREAM_DOT` `failed` entry | New component state | J-27: status dot must read "failed" (rose) when snapshot's `stream_status === "failed"` — distinct from normal "closed" | With a snapshot carrying `stream_status === "failed"`, confirm the TopBar status dot reads the label "failed" and renders with rose colouring |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/tape_engine.py` — added the `waiting` rung to the `stream_status` state machine (`connecting`/`waiting` → `live` on first event); the rung is purely delivery/lifecycle metadata and never enters `classify(...)` or any feature/score. The UI reads this value verbatim via the existing `/summary` REST endpoint and the `/stream` WebSocket.
- `apps/backend/app/watch_manager.py` — feeders (`_feed`, `_feed_paced`, `_feed_live`) now set `stream_status = "waiting"` on stream-open, catch non-`CancelledError` exceptions and flip to `failed` (with a `logger.exception(...)` log line naming the ticker), and the live stale watchdog now bounds `waiting` → `stale` after `stale_gap_seconds`. Also adds a `_Failure` sentinel for carrying a live-puller exception to the main loop. These are engine/delivery mechanics; the UI surface impact is entirely through the existing `stream_status` field already routed above.
- `apps/backend/app/engine/snapshot.py` — extended the `stream_status` value-list doc comment with `waiting` / `failed`; doc change only, no serialiser or API shape change.
- `apps/backend/app/serializers.py` — extended the module docstring to list `waiting` / `failed` in the `stream_status` value set; pass-through logic unchanged, no API shape change.
- `apps/backend/tests/test_stream_lifecycle.py` — NEW: 9 unit tests covering the paced/sim and live feeders for the `waiting` rung, `waiting → stale` bound, feeder-raises → `failed` with log record, and cancel → `closed` (not `failed`). Test-only; no UI surface affected.
- `apps/frontend/lib/types.ts` — extended the `stream_status` doc comment with `waiting` / `failed`; TypeScript type is still a free `string`, no shape change, no UI behaviour change.

---

## Summary

- **Frontend surfaces changed:** 5 (WaitingState new component, Cockpit backstop guard, page.tsx snapshot routing, TopBar STREAM_DOT waiting entry, TopBar STREAM_DOT failed entry)
- **New pages/routes:** 0
- **Modified components:** 4 (IdleState.tsx adds WaitingState; Cockpit.tsx adds guard; app/page.tsx adds snapshot routing; TopBar.tsx adds two dot states)
- **Navigation changes:** no
- **Backend-only changes:** 5 (tape_engine.py, watch_manager.py, snapshot.py doc, serializers.py doc, test_stream_lifecycle.py)
