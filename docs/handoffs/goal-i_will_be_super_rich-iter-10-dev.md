# goal-i_will_be_super_rich-iter-10 Dev Handoff

**Phase:** goal-i_will_be_super_rich-iter-10
**Date:** 2026-06-07
**Agent:** developer
**Status:** complete

## What Was Built

Post-connect stream-lifecycle hardening (J-25 / J-26 / J-27): after a Watch is accepted and the
stream connects, the cockpit now ALWAYS resolves to an honest, non-idle terminal state — never a
mute/blank cockpit, never a confident `live` over an empty tape, never a swallowed feeder failure.
This closes the "No mute cockpit / no silent return to idle" critical anti-goal.

The change is **additive to the single existing canonical `stream_status`** (Data Contract row 6,
owned once by the engine/feeder). Two new engine-owned values were added — `waiting` and `failed` —
both already served verbatim by `/summary` + the WS `/stream`. No new endpoint, no second status
field/writer, no engine-math change, no client recomputation.

- **Engine `waiting` rung** (`tape_engine.py`): the canonical status now climbs
  `connecting` → `waiting` (stream open, no first event yet) → `live` (first event arrived). The
  first `process_event` promotes BOTH `connecting` and `waiting` to `live` (rung order holds; J-01
  / J-12 unchanged). `stale` / `paused` / `closed` / `failed` are owned by the feeder, not flipped
  in `process_event`. Status is delivery/lifecycle metadata only — it never enters `classify(...)`
  or any feature/score, so determinism is unaffected.
- **Feeders signal stream-open → `waiting`** (`watch_manager.py` `_feed` / `_feed_paced` /
  `_feed_live`): each feeder sets `stream_status = "waiting"` once the provider stream is open but
  before the first event is applied. A connected-but-quiet stream reads `waiting`, not a frozen
  `connecting` and never a confident `live`.
- **Feeders surface a failure → `failed`, logged not swallowed** (`watch_manager.py`): each
  feeder's stream loop now catches a non-`CancelledError` `Exception`, (a) **logs it server-side**
  via the stdlib `logging` module (a real, inspectable `logger.exception(...)` line naming the
  ticker) and (b) flips `stream_status` to `failed` before the task ends. `CancelledError` still
  means a clean stop/switch (→ `closed`, re-raised) — a cancel is NEVER reported as `failed`. For
  the live feeder, a provider exception raised inside the background puller is carried to the main
  loop via a `_Failure` sentinel (so it is surfaced, not lost in the puller task); the existing
  bounded `aclose()` teardown still runs (no synchronous unsubscribe in the failure branch — the
  iter-4 deadlock lesson).
- **`waiting` → `stale` bound** (`watch_manager.py` `_feed_live`): the live stale watchdog already
  flips to `stale` on a delivery-gap timeout; it now bounds a `waiting` that never received a first
  event (off-hours / quiet live feed) out to `stale`, reusing the already-registered
  `CONFIG.stale_gap_seconds` (no new timeout literal). The paced/sim feeders are finite, so their
  `waiting` resolves to `live`-or-`closed` by exhaustion — no new timer there.
- **Frontend honest treatments**: a new `WaitingState({ symbol, mode })` component (in
  `IdleState.tsx`) renders an explicit "Connected to `<SYMBOL>` (`<mode>`) — waiting for the first
  trade…" treatment in place of the blank panel grid; `Cockpit.tsx` guards against rendering the
  grid for a `waiting` snapshot; `app/page.tsx` routes a snapshot-borne `waiting` to `WaitingState`
  and a snapshot-borne `failed` (a post-connect feeder failure, distinct from iter-9's pre-snapshot
  `connStatus === "failed"`) to the existing `StreamFailedState` + error banner; an empty cold-start
  snapshot can no longer short-circuit into the full cockpit grid. `TopBar.tsx` `STREAM_DOT` gained
  `waiting` (amber + pulse, in-progress) and `failed` (rose). All read the engine status verbatim.

## Files Changed

- `apps/backend/app/engine/tape_engine.py` -- added the `waiting` rung (`connecting`/`waiting` →
  `live` on first event); documented `set_stream_status` valid values. No engine-math change.
- `apps/backend/app/watch_manager.py` -- `_feed` / `_feed_paced` / `_feed_live` set `waiting` on
  stream-open; catch non-`CancelledError` `Exception` → `logger.exception(...)` (names ticker) +
  flip `failed`; live `waiting`→`stale` bound via `stale_gap_seconds`; `_Failure` sentinel carries a
  live-puller exception to the main loop (and is re-queued, not discarded, if it arrives during
  pause); module-level `logging.getLogger(__name__)`. Bounded `aclose()` teardown unchanged.
- `apps/backend/app/engine/snapshot.py` -- extended the `stream_status` value-list comment with
  `waiting` / `failed` (doc only).
- `apps/backend/app/serializers.py` -- extended the module docstring with the full `stream_status`
  value set (doc only; the three pass-throughs are unchanged).
- `apps/backend/tests/test_stream_lifecycle.py` -- NEW: 9 unit tests (paced/sim AND live feeders).
- `apps/frontend/components/IdleState.tsx` -- NEW `WaitingState` component (amber pulsing dot, DOM
  text "Connected to `<SYMBOL>` (`<mode>`) — waiting for the first trade…").
- `apps/frontend/components/Cockpit.tsx` -- render `WaitingState` when `stream_status === "waiting"`
  instead of the blank panel grid (backstop guard).
- `apps/frontend/app/page.tsx` -- route snapshot-borne `waiting` → `WaitingState`, `failed` →
  `StreamFailedState` + banner, transient `connecting` snapshot → `ConnectingState`; chart hidden in
  all three; empty cold-start snapshot never renders the full grid.
- `apps/frontend/components/TopBar.tsx` -- `STREAM_DOT` gained `waiting` (amber pulse) + `failed`
  (rose).
- `apps/frontend/lib/types.ts` -- extended the `stream_status` doc comment with `waiting` / `failed`
  (still a free `string`; no shape change).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **198 passed, 1 skipped** (up from the baseline 189 passed; +9 new lifecycle tests, zero
failures, zero regressions).

The 9 new tests in `test_stream_lifecycle.py` assert, on BOTH the paced/sim and live feeders:
- a connected feeder with no first event sets `stream_status == "waiting"` (not `live`, not a frozen
  `connecting`), and for the live feeder bounds to `stale` after a tiny `stale_gap_seconds` override
  — fabricating NO trade during the wait (`event_count == 0`, recent-trades empty);
- the first real event flips `waiting` → `live` (rung order; J-01/J-12 unchanged);
- a feeder whose provider raises ends `stream_status == "failed"` AND emits a server-side log record
  naming the ticker (asserted via `caplog`) — engine not frozen at cold-start, not faked to `live`;
- a clean stop/switch (cancel) still ends `closed` (and the live socket is closed) — a cancel is NOT
  reported as `failed`.

Frontend: `cd apps/frontend && NEXT_DIST_DIR=.next-devcheck npm run build` — **compiled + type-checked
cleanly** (isolated dist dir; `tsconfig.json` / `next-env.d.ts` auto-edits reverted, isolated dir
removed, so no build-artifact noise is committed). The shared harness `:3650` `.next` was NOT
touched (iter-3/6/8 lesson).

## Live / Integration Verification

- Backend booted on an isolated port (`uvicorn main:app --port 8771`): `/health` = 200, no error
  log. `POST /watch/SIM-BUYER` → after warm-up `GET /summary` reads `stream_status=live`,
  `tape_state=buyer_control`, confidence ≈ 0.80 (J-01 not regressed). `DELETE /watch/SIM-BUYER` =
  200 (clean teardown). The backend was then killed; no server process left running.
- The `waiting` rung is transient for the dense SIM feed (it flips to `live` within the warm-up),
  exactly as designed — its deterministic proof is the unit tests (a no-event provider held in
  `waiting`, then bounded to `stale`).

## Known Issues

- **Live `waiting` / `stale` / `failed` over a REAL socket** is proven here only via the in-loop
  `FakeLiveProvider` / async-raising-provider doubles behind the provider seam (the hermetic J-12
  pattern). Real Alpaca-socket behavior off-hours remains the operator/gated credentialed check, as
  for J-12 / J-15. No real-socket regression is expected (the live feeder's event/teardown path is
  unchanged except for the additive status writes).
- **J-28 / J-29 / J-30 (vendor responsiveness — true call-level timeout, fast concurrent historical
  fetch / cached windows, warmed/cached fast symbol search) are explicitly OUT OF SCOPE this
  iteration** and were not touched. No J-28–J-30 defect was observed during this work. They share the
  word "timeout"/"vendor" with this lifecycle work but are a separate performance concern for the
  next iteration.
- **Pause is unchanged this iteration.** During the live `waiting` phase the Pause button is hidden
  (`pauseable` gates on `connecting`/`live`/`stale`, not `waiting`) — Stop is available; this avoids
  scope creep into pause behavior. A feeder failure that arrives while a watch is paused is re-queued
  (not discarded) so it still surfaces `failed` after resume — the no-swallow guarantee holds.
