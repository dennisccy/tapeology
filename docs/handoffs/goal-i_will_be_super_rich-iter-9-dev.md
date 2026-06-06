# goal-i_will_be_super_rich-iter-9 Dev Handoff

**Phase:** goal-i_will_be_super_rich-iter-9
**Date:** 2026-06-06
**Agent:** developer
**Status:** complete

## What Was Built

Watch-lifecycle feedback hardening so every Watch click is acknowledged within ~1s and every
outcome resolves to a distinct, bounded, visible state — never a silent no-op, infinite spinner,
or swallowed failure. Targets J-21–J-24; no engine/classifier/feature-math change.

- **J-21 — Pending/connecting acknowledgement:** `app/page.tsx#handleWatch` now sets a synchronous
  `pending` state (the entered symbol) *before* the awaited teardown/watch round-trip, so the
  cockpit immediately leaves the idle screen and shows "Connecting to <SYMBOL>…" with the amber
  connecting dot, in all three modes. It is cleared/replaced when the watch resolves.
- **J-22 backend half — per-call vendor timeout:** new config constant
  `vendor_call_timeout_seconds` (`app/config.py`); the two Watch-gating vendor calls
  (`adapter.fetch_historical` in `_watch_historical`, `adapter.get_market_clock` in the `_watch_live`
  pre-flight) are wrapped in `asyncio.wait_for(..., timeout=CONFIG.vendor_call_timeout_seconds)`.
  On `asyncio.TimeoutError` the watch is refused with an explicit `RealDataError("provider_timeout",
  "market data provider timed out", 504)` and NO engine is created (no fabricated tape).
- **J-22 frontend half — client-side request-timeout backstop:** one config constant
  `WATCH_REQUEST_TIMEOUT_MS` (`lib/config.ts`) drives an `AbortController` in a new
  `fetchWithTimeout` helper applied to `watchTicker` and `fetchInitialSnapshot`. A client abort
  resolves `watchTicker` to a distinct `provider_timeout` error result ("Market data provider timed
  out…") rather than hanging forever.
- **J-23 — surfaced failed initial connection/stream:** `lib/useTapeStream.ts` no longer swallows
  the initial-snapshot failure (`.catch(() => {})` removed). `fetchInitialSnapshot` now THROWS on a
  hard transport failure/timeout (returns `null` only for a clean not-yet-ready response). The hook
  records an explicit `connStatus: "failed"` + `connError` message when the snapshot fetch throws or
  when the WS errors/early-closes BEFORE any frame arrives. `app/page.tsx` renders this via a new
  `StreamFailedState` cockpit treatment and the existing error banner within a bounded time.
- **J-24 — inline validation:** `components/TopBar.tsx` disables Watch and shows an inline message
  ("Enter a ticker symbol" / "Choose a valid time window") for an empty/whitespace symbol or a
  missing/invalid (`end <= start`) historical window; `handleWatch` also guards the empty-symbol
  case. The backend 422 remains the server-side backstop.

`provider_timeout` is an additive sibling of the existing row-9 reasons on the one `POST /watch`
failure path — no new endpoint, component, or status concept. The connecting dot
(`CONN_DOT.connecting`), the TopBar error banner, and `ProviderUnavailable` are reused.

## Files Changed

- `apps/backend/app/config.py` -- add `vendor_call_timeout_seconds` (`*_seconds` float, no-magic comment, distinct from `stale_gap_seconds`).
- `apps/backend/app/main.py` -- wrap `fetch_historical` + `get_market_clock` in `asyncio.wait_for`; explicit `provider_timeout` (504) on `TimeoutError`, no engine created.
- `apps/backend/tests/fakes.py` -- add `fetch_hang_seconds` / `clock_hang_seconds` flags to `FakeAdapter` to simulate a hung vendor.
- `apps/backend/tests/test_vendor_timeout.py` -- NEW: per-call timeout bound fires, `provider_timeout` returned, no engine registered, value is config-sourced.
- `apps/frontend/lib/config.ts` -- add `WATCH_REQUEST_TIMEOUT_MS` constant.
- `apps/frontend/lib/api.ts` -- `fetchWithTimeout` (AbortController) on `watchTicker` + `fetchInitialSnapshot`; `RequestTimeoutError`/`isTimeoutError`; distinct timeout error result; snapshot fetch now throws on hard failure.
- `apps/frontend/lib/useTapeStream.ts` -- stop swallowing snapshot failure; new `failed` status + `connError`; pre-snapshot WS error/close surfaced.
- `apps/frontend/lib/types.ts` -- add `"failed"` to `ConnStatus`.
- `apps/frontend/app/page.tsx` -- synchronous `pending` state; render `ConnectingState`/`StreamFailedState`; route connect-failure + timeout to the error banner; empty-symbol guard.
- `apps/frontend/components/IdleState.tsx` -- `ConnectingState` accepts a symbol; new `StreamFailedState`.
- `apps/frontend/components/TopBar.tsx` -- inline validation, disabled Watch when invalid, `failed` dot entry, validation cleared on input change.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: 189 passed, 1 skipped (the operator-gated live-integration test), 0 failed.

Frontend: `cd apps/frontend && npx tsc --noEmit` — exit 0 (no type errors). The project has no JS
unit-test runner (per `.claude/project-template.md`, user-facing behavior is covered by browser QA);
frontend behavior is verified by the browser-qa-agent.

## Known Issues

- **Browser verification pending (J-21–J-24 + J-01/J-09/J-10/J-14 regression):** these are browser-
  verifiable and must be run by the browser-qa-agent into an ISOLATED `NEXT_DIST_DIR` wired to an
  isolated backend — never `npm run build` against the shared `.next` on `:3650` (iter-3/6/7/8
  lesson). Capture real rendered screenshots of the pending, bounded-error, and inline-validation
  states; an idle/placeholder screenshot is NOT evidence.
- **Live vendor credentials ARE present in this environment's `apps/backend/.env`:** a live smoke
  test of `POST /watch/AAPL {mode:historical,...}` returned a real `200 watching` (not
  `provider_unavailable`). The backend timeout path is proven hermetically by the new unit tests
  (mocked slow adapter); it does not require a live credentialed run.
- **`WATCH_REQUEST_TIMEOUT_MS = 12000`** is set comfortably above the backend's
  `vendor_call_timeout_seconds = 8.0` so the backend's explicit error wins when the backend is
  reachable; the client timeout is the backstop only for an unreachable/hung backend that never
  responds. Both halves of J-22 are independently exercised.
