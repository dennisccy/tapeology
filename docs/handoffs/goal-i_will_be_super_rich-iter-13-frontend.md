# goal-i_will_be_super_rich-iter-13 Frontend Handoff

**Phase:** goal-i_will_be_super_rich-iter-13
**Date:** 2026-06-09
**Agent:** developer
**Status:** complete

## What Was Built

- **J-32 — live replay-speed control.** The existing Historical **replay-speed** `select` (the
  `1× / 2× / 5× / 10×` dropdown in the Historical mode-specific controls) now applies a speed change
  to a *running* replay immediately by calling `POST /watch/{ticker}/speed` — it is **not** a
  re-Watch. The cockpit and chart continue from their current position at the new cadence; nothing
  is re-fetched, no engine restart, no teardown. When no watch is running yet, the dropdown simply
  stages the speed the next Watch submits with (unchanged behavior).
- No new UI surface, component, page, or navigation. Only the speed control's behavior changed.
- J-33 and J-34 required **no** frontend work: the tape-state panel already renders the canonical
  state/confidence verbatim (J-33 only recalibrates that computation), and the Historical fetch wait
  + Full-RTH quick-pick already exist (J-34 only changes the backend fetch).

## Files Changed

- `apps/frontend/lib/api.ts` — added `setReplaySpeed(ticker, speed)`: `POST /watch/{ticker}/speed`
  with a JSON `{speed}` body; returns `{ok}` or `{ok:false, error}` (backend 422/404 surfaced).
- `apps/frontend/components/TopBar.tsx` — the replay-speed `select` `onChange` now also calls
  `onSpeedChange(next)` when a historical replay is running (`replayRunning`, derived from the
  canonical `snapshot.stream_status` being non-terminal in Historical mode — never a client guess).
  Added the `onSpeedChange` prop.
- `apps/frontend/app/page.tsx` — `handleSpeedChange` calls `setReplaySpeed(ticker, speed)` and
  surfaces any failure in the existing error banner; wired to `<TopBar onSpeedChange=… />`.

## How It Behaves

- **Out-of-set values** can't be chosen (only `1/2/5/10` are offered); the backend 422 is the
  authoritative guard if one ever reached it. The frontend offering is a courtesy.
- **A change while paused** is accepted by the backend and applies on resume (the speed cell is
  mutated regardless of pause state; pause only freezes *applying* events).
- **Determinism is preserved end-to-end:** speed is delivery-pacing only, so the canonical engine
  values (tape state, confidence, features) shown in the cockpit do not change when the speed
  changes — only the cadence of new candles/trades arriving.

## Tests Run

Command: `cd apps/frontend && npm run build`
Result: compiled + type-checked successfully.

Browser verification (J-32 cadence change, regression smoke on J-17/J-02/J-03/J-20) is for the
browser-QA stage. For the fast-resolving speed change, observe/hold the `POST .../speed` request and
assert the DOM/cadence rather than a bare PASS label (per the iter-12 reconciliation lesson).

## Known Issues

- The speed change is fire-and-forget from the UI's perspective: the new cadence is visible as new
  candles/trades arrive over the existing WS stream. There is no explicit "speed applied" toast —
  the change is silent on success (a failure surfaces in the error banner).
