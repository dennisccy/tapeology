# Phase goal-i_will_be_super_rich-iter-9 — UI Surface Map

**Phase:** goal-i_will_be_super_rich-iter-9
**Date:** 2026-06-06
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|---|---|---|---|---|
| `/` | `ConnectingState` (in cockpit area) | New component | J-21: Watch click must leave the idle screen immediately with a named acknowledgement | Type "SIM-BUYER" and click Watch; within ~1s the cockpit area must show the amber pulsing dot and text "Connecting to SIM-BUYER…" — the idle "No ticker watched" view must no longer be visible |
| `/` | `StreamFailedState` (in cockpit area) | New component | J-23: Failed initial tape connection must surface a distinct error state, not a frozen spinner | Start a Watch for a valid ticker, then stop the backend immediately after; within a bounded time the cockpit area must show the rose ⚠ icon and heading "Couldn't connect to the tape stream" |
| `/` | TopBar status dot (`CONN_DOT.failed`) | Changed behavior | J-23: New `failed` status must have a distinct dot color/label, not remain on "connecting" | After a tape stream connection failure, confirm the status dot in the top-right corner shows a rose-colored dot with the label "failed" (not "connecting" or "closed") |
| `/` | TopBar error banner | Changed behavior | J-22/J-23: Timeout and stream-failure errors must appear in the error banner | Simulate an unreachable backend (or wait for the client timeout), then confirm a rose-colored error message appears below the TopBar header — message must include "timed out" or "Couldn't connect" rather than remaining blank |
| `/` | Watch button (inline validation) | Changed behavior | J-24: Empty symbol must never be a silent no-op — Watch must be disabled with an inline message | Clear the symbol field entirely; confirm the Watch button turns gray/disabled and the amber text "Enter a ticker symbol" appears immediately beside it without clicking Watch |
| `/` | Historical window inline validation | Changed behavior | J-24: Missing or invalid Historical time window must show an inline message and disable Watch | Switch to Historical mode, enter a symbol but leave the date/time fields blank; confirm the Watch button is disabled and "Choose a valid time window" appears in amber beside it |
| `/` | Historical inline validation clears on edit | Changed behavior | J-24: Validation message must clear as the user corrects their input, not persist stale | In Historical mode, click Watch without a symbol to trigger "Enter a ticker symbol", then type a single character in the symbol field; confirm the amber validation message disappears immediately |
| `/` | `app/page.tsx` `handleWatch` — pending state | Changed behavior | J-21: `pending` state set synchronously before awaited teardown so idle screen exits immediately | In Simulated mode, with no ticker currently watched, click Watch on a valid symbol; confirm the cockpit area changes away from idle before the backend responds (within ~1s) |
| `/` | `app/page.tsx` mode change clears pending | Changed behavior | Mode switch while connecting must not leave a stale connecting state visible | Click Watch to enter the connecting state, then immediately click a different mode tab; confirm the cockpit area returns to idle (no "Connecting to…" leftover) |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/config.py` — adds `vendor_call_timeout_seconds = 8.0` constant; the value is consumed by `main.py` and its effect surfaces in the UI as the `provider_timeout` error banner — no isolated backend-only surface.
- `apps/backend/app/main.py` — wraps `fetch_historical` and `get_market_clock` in `asyncio.wait_for`; on timeout raises `RealDataError("provider_timeout", …, 504)` — effect is UI-visible via the error banner.
- `apps/backend/tests/fakes.py` — adds `fetch_hang_seconds` / `clock_hang_seconds` to `FakeAdapter`; test-only, no UI surface.
- `apps/backend/tests/test_vendor_timeout.py` — new backend unit test; test-only, no UI surface.
- `apps/frontend/lib/config.ts` — adds `WATCH_REQUEST_TIMEOUT_MS = 12000` constant; consumed by `api.ts` to drive the `AbortController` — no isolated UI surface (effect is the timeout error banner).
- `apps/frontend/lib/api.ts` — adds `fetchWithTimeout` / `RequestTimeoutError` / `isTimeoutError`; effect is UI-visible via the timeout error result surfaced in `page.tsx`.
- `apps/frontend/lib/useTapeStream.ts` — removes `.catch(() => {})` swallow, adds `failed` status + `connError`; effect is UI-visible via `StreamFailedState` and the error banner.
- `apps/frontend/lib/types.ts` — adds `"failed"` to `ConnStatus` union; type-level change, effect is UI-visible via the `failed` dot and `StreamFailedState`.

---

## Summary

- **Frontend surfaces changed:** 1 (all changes are on `/`)
- **New pages/routes:** 0
- **Modified components:** 4 (`IdleState.tsx` — adds `ConnectingState` + `StreamFailedState`; `TopBar.tsx` — adds inline validation + `failed` dot; `app/page.tsx` — adds `pending` state logic and new render branches)
- **Navigation changes:** no
- **Backend-only changes:** 4 (`config.py`, `main.py`, `fakes.py`, `test_vendor_timeout.py`) — all backend effects are wired to visible UI states
