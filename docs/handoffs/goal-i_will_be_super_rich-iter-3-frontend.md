# goal-i_will_be_super_rich-iter-3 Frontend Handoff

**Phase:** goal-i_will_be_super_rich-iter-3
**Date:** 2026-06-04
**Agent:** developer
**Status:** complete

## What Was Built (UI)

- **Live market-status indicator (real, replacing a stub).** In the persistent TopBar, selecting **Live** previously showed a permanently hardcoded "market unavailable" pill. It now shows the **real** session status read from `GET /market/clock` (Data Contract row 8):
  - **market open** — emerald dot + "open"
  - **market closed** — amber dot + "closed — next open <local time, explicit zone>"
  - **unavailable** — amber dot + "unavailable" (no credentials, or the clock could not be reached)
  - **in-flight** — a calm slate "…" placeholder before the first fetch resolves (never a fabricated "open")
- **Honest "market is closed" panel (completes the J-14 set).** Watching a real symbol in **Live** mode while the market is closed now renders a distinct amber **"Market is closed"** non-cockpit panel — in place of the cockpit — showing the phrase "market is closed" and the **next open** time. No quote/trades/state panels, no fabricated tape.

## How It Works (data flow, no business logic in the UI)

- `MarketStatusIndicator` calls `getMarketClock()` (`lib/api.ts` → `GET /market/clock`) on mount and every 60s **while mounted**. It is mounted only when `mode === "live"` (conditional render in `TopBar`), so switching away from Live unmounts it and its `useEffect` cleanup clears the interval and ignores any in-flight response (iter-0 resource-leak lesson). It **reads** open/closed verbatim — it never recomputes the session.
- On a refused Live watch, `watchTicker` surfaces `reason` + `nextOpen` (parsed from the backend's `reason` / `next_open`). `page.tsx` routes `market_closed` (now in `HONEST_REASONS`) to `ProviderUnavailable` with `nextOpen`, which renders the closed-market copy. The existing three reasons are unchanged.
- The next-open instant (ISO-8601 UTC from the backend) is rendered via `formatMarketTime()` (`lib/datetime.ts`) in the operator's local zone with an explicit zone label, so UTC is never mis-read as local.

## Files Changed

- `apps/frontend/components/MarketStatusIndicator.tsx` — **new**; the Live market-status indicator (poll on mount + 60s interval, cleanup on unmount/mode-change).
- `apps/frontend/lib/datetime.ts` — **new**; `formatMarketTime()` shared formatter (local zone + explicit zone label; raw-string fallback if unparseable).
- `apps/frontend/components/TopBar.tsx` — replaced the hardcoded "market unavailable" pill with `{mode === "live" && <MarketStatusIndicator />}`.
- `apps/frontend/components/ProviderUnavailable.tsx` — added the `market_closed` copy case (title "Market is closed", phrase "market is closed", next-open help) + a `nextOpen` prop.
- `apps/frontend/app/page.tsx` — added `market_closed` to `HONEST_REASONS`; threaded `nextOpen` through the `failure` state into `ProviderUnavailable`.
- `apps/frontend/lib/api.ts` — added `getMarketClock()`; added `nextOpen` to `WatchResult` (parsed from `next_open`).
- `apps/frontend/lib/types.ts` — added `"market_closed"` to `FailureReason`; added the `MarketClock` response interface.

## Design System Conformance

- **Color semantics (load-bearing):** emerald = open, amber = closed / next-open / unavailable / honest-fail, slate = pre-fetch placeholder — consistent with the existing palette. No new colors or effects invented.
- **Component reuse:** the closed-market panel reuses the existing `Panel` (mirrors the other three honest non-cockpit panels). The indicator reuses the established TopBar status-pill styling (dot + label, `font-mono` for the time/value).
- **One screen:** still exactly one route (`/`). No new page, no navigation change. Changes confined to the persistent TopBar and the existing `ProviderUnavailable` panel.

## Tests Run

Command: `cd apps/frontend && npm run build`
Result: **Compiled successfully** — TypeScript types valid, lint clean, 4/4 static pages generated.

Frontend has no unit-test suite (per `.claude/project-template.md`); user-facing behavior is covered by browser QA. Build (type-check) is the frontend gate.

## Known Issues

- The closed-market **panel** and the indicator's "open"/"closed" states are wall-clock dependent for live browser QA. At handoff time the US market is closed, so both are verifiable now. If QA runs during market hours, the indicator shows "open" and a Live watch returns the honest `provider_not_implemented` (no panel) — the closed branch is then covered by the deterministic backend test.
- `formatMarketTime()` renders in the **browser's** local timezone (correct for an operator); the underlying value is the backend's authoritative ISO-8601 UTC, so there is no recomputation — only presentation.
