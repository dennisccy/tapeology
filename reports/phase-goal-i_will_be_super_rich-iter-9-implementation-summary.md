# Iteration 9 — Implementation Summary

**Phase:** goal-i_will_be_super_rich-iter-9
**Date:** 2026-06-06
**Written by:** developer

---

## Features Implemented

- **Immediate Watch acknowledgement**: The moment you click Watch — in Simulated, Live, or
  Historical mode — the screen leaves the idle state and shows "Connecting to <SYMBOL>…" with a
  pulsing amber status dot, so a click is never silently ignored.
- **Bounded waits with a clear timeout message**: If the data provider or the backend is slow or
  unreachable, the wait now ends within a fixed time and shows an explicit "Market data provider
  timed out" message instead of spinning forever. This is enforced in two independent places — the
  backend caps each outbound vendor request, and the browser caps each Watch request — so a hang
  anywhere still resolves to a visible error.
- **Honest connection-failure message**: If the connection to the live tape stream fails right after
  Watch (for example, the backend stops), the screen now shows an explicit "Couldn't connect to the
  tape stream" message instead of leaving "Connecting…" stuck on screen.
- **Inline input checks**: An empty ticker, or a Historical date/time window that is missing or
  ends before it starts, now disables the Watch button and shows an inline hint ("Enter a ticker
  symbol" / "Choose a valid time window") immediately — clicking Watch is never a silent no-op.

---

## Changed Behavior

- **Clicking Watch**: Previously the screen stayed on the idle view until the backend replied, with
  no client-side timeout. Now it shows an immediate "Connecting to <SYMBOL>…" acknowledgement and is
  guaranteed to resolve to a cockpit, an honest non-cockpit panel, an explicit error, or an inline
  validation message within a bounded time.
- **A slow/hung provider request**: Previously a slow vendor call could block a Watch request with
  no upper bound. Now each Watch-gating vendor call (historical fetch, live market-clock pre-flight)
  is capped; on timeout the watch is refused with a distinct "market data provider timed out" result
  and no tape is created.
- **A failed initial connection**: Previously the initial data fetch failure was silently ignored.
  Now it is surfaced as an explicit connection-failure state.

---

## Backend-Only Items

- None. The new backend timeout produces a `provider_timeout` failure reason that the frontend
  surfaces (via the existing error banner). There is no backend capability left unwired.

---

## Incomplete Items

- **Browser verification of the four target journeys (J-21–J-24)** and the regression re-checks
  (J-01, J-09, J-10, J-14) are performed by the separate browser-QA step, not in this implementation
  pass. The code is in place; the visual proof (real screenshots of the connecting, timeout, and
  validation states) is captured there.

---

## Config and Environment Changes

- `vendor_call_timeout_seconds` (backend config, `app/config.py`) — the maximum time a single
  outbound vendor request that gates a Watch may take before the Watch is refused — default: `8.0`
  seconds. This is separate from the existing mid-stream `stale_gap_seconds` watchdog.
- `WATCH_REQUEST_TIMEOUT_MS` (frontend config, `lib/config.ts`) — the browser-side cap on each Watch
  request — default: `12000` ms (set above the backend cap so the backend's explicit error wins when
  the backend is reachable).
- No environment variables, secrets, or schema changes.

---

## Known Limitations

- The frontend has no automated unit-test runner in this project; frontend behavior is validated by
  the browser-QA step. Backend behavior (including the new per-call timeout) is covered by automated
  unit tests (189 passing).
- This environment has live vendor credentials configured, so a Historical/Live watch reaches the
  real provider; the timeout behavior is still proven hermetically by unit tests using a simulated
  slow provider, independent of any live call.
- The browser-side timeout (12s) only acts as a backstop for an unreachable/unresponsive backend;
  when the backend is reachable it returns its own explicit timeout error first (8s).
