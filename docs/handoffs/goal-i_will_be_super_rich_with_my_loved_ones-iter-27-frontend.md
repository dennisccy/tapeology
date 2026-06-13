# goal-i_will_be_super_rich_with_my_loved_ones-iter-27 Frontend Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-27
**Date:** 2026-06-13
**Agent:** developer
**Status:** complete
**Iteration type:** VERIFICATION / EVIDENCE-CAPTURE ONLY

---

## What Was Built (frontend)
- **Nothing.** No new component, no new surface, no new copy, no new action. Frontend source is
  **byte-identical** at the end of this iteration (`git diff --stat HEAD -- apps/frontend/` is
  empty). No genuine UI defect surfaced during verification, so no in-place fix was needed.

## Files Changed
- **None.**

---

## Existing surfaces exercised as evidence (no code change)
These already-shipped cockpit surfaces are the targets for browser-qa-agent's pixel captures.
They are listed here so QA knows exactly which DOM elements must visibly appear in each capture
(lesson iter-3 line 33 — every capture must contain the asserted element):

| Journey | Surface (existing) | Asserted element in the capture |
|---------|--------------------|---------------------------------|
| J-11/J-20 | `/` Cockpit panel grid (bid/ask/spread/last, features, tape-state + confidence) | real numeric values populate; spread = ask − bid |
| J-16 | Recent-trades list — **side column** | resolved buy/sell sides; `unknown` fraction far lower than the quote-only baseline |
| J-18 | Candlestick chart + tape-state markers + **true-clock time axis** | chart matches `…/history` at each bar size; markers at transitions; real market-clock labels |
| J-29 | Busy-window load + re-watch | loads within the configured bound; re-watch near-instant (window cache) |
| J-32 | Replay-speed control | in-progress 1×→10× change continues from current position (no re-Watch / re-fetch) |
| J-14 (a) | Closed-market honest panel | "market is closed" + next open 15-06-2026 14:30 UTC+01:00 |
| J-14 (b) | Unknown-symbol honest panel | "not a tradable symbol" |
| J-14 (c) | Empty-window honest panel | "no data for that window" |
| J-22 | Error banner | distinct timeout/unreachable error within the client-side bound (12s) |
| J-23 | Failure panel / error banner | "couldn't connect to the tape stream" (no infinite spinner) |
| J-27 | Stream-status dot owned by `stream_status` | explicit `stale`/`closed`/no-data state (never fabricated `live`, never stuck `connecting`) |

All read the registered canonical endpoints verbatim (`…/history`, `…/state`, `…/features`,
`…/summary`) — no UI-side recomputation of side/state/price/time. The cockpit is the single `/`
home, unchanged, one ticker at a time.

## Design-system conformance
Unchanged — existing dark instrument-panel palette (green = buy/positive, red = sell/negative,
amber = absorption/unclear; mono numerics). No new effect, no new token usage.

## Backend data path confirmed live (dev step) so these captures are populated, not empty
- Live credentialed Alpaca historical fetch returns real AAPL trades/quotes (24,619 / 21,034 for
  a 2-min window).
- The engine resolves the aggressor side on real data with unknown ≈ 0.004% (J-16 side column
  will show resolved buy/sell, not a wall of `unknown`).
- `get_market_clock()` returns `is_open=False`, next_open 2026-06-15T13:30:00Z (the J-14
  closed-market panel will show the real Monday open).
- Unknown symbol raises `SymbolNotTradable` (the J-14 unknown-symbol panel is reachable).

See the dev handoff (`...-iter-27-dev.md`) for the full per-leg evidence and the deferred
live-only legs (J-15, J-67 live-IEX pixels) with their Monday gating.

## Known Issues (frontend)
- Pixel capture is owned by the browser-qa-agent pipeline step, not the dev step.
- Pre-capture hygiene (lessons line 51/123/27): browser-qa-agent must confirm the frontend dev
  server is live and serving a fresh bundle (content canary) before any capture; a dead frontend
  is a hard-flag, not a soft-skip. Per the QA frontend-build-caution memory, do NOT
  `npm run build` against the live harness dev server's shared `.next`; use `npx tsc --noEmit`
  if a type-check is needed.
