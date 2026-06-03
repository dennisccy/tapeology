# goal-i_will_be_rich-iter-7 Dev Handoff

**Phase:** goal-i_will_be_rich-iter-7
**Date:** 2026-06-03
**Agent:** developer
**Status:** complete

## What Was Built

J-09 (Stop watching a ticker) — the ninth and final Must-have journey — completing the watch
lifecycle (start → read → **stop** → re-start) across the stack. Net-new this iteration:

**Backend**
- `WatchManager.stop(ticker) -> bool` (`apps/backend/app/watch_manager.py`): cancels the
  per-ticker feeder task and pops it from `_tasks`, sets the engine `stream_status` to `"closed"`
  (truthful status for any already-connected WS / in-flight read holding the engine reference),
  and **removes** the engine from `_engines`. Returns `True` if the ticker was being watched,
  `False` otherwise — idempotent, raises nothing on stop-of-not-watched. Removing the engine is
  what makes a later `watch()` build a fresh, cold engine ("re-watch = fresh read").
- `DELETE /watch/{ticker}` route (`apps/backend/app/main.py`): async, calls `manager.stop(ticker)`.
  `True` → HTTP 200 `{"ticker": ticker, "status": "stopped"}`; `False` → `HTTPException(404, …)`
  with the exact `_engine_or_404` detail string (honest "not being watched", never a fabricated
  success).
- No new code for post-stop reads — the existing semantics already hold: after `stop()`,
  `GET /tape/{ticker}/state|features|events|summary` → **404** (engine removed) and a fresh
  `WS /tape/{ticker}/stream` connect closes **4404** (`manager.get()` is `None`).

**Frontend**
- `stopTicker(ticker)` (`apps/frontend/lib/api.ts`): `DELETE ${API_BASE}/watch/{ticker}`,
  returning `{ ok, error? }` — mirrors `watchTicker`'s try/catch + "Backend unreachable" handling.
  A **404 counts as effectively-stopped** (the ticker is not watched either way).
- **Stop** button in `apps/frontend/components/TopBar.tsx`: rendered only when `watched` is set,
  beside the "Watching <TICKER>" label, wired to a new `onStop: () => void` prop. Static rose
  ghost `className` (no runtime-built class string — iter-2/iter-3 lesson) with hover/focus/active
  states.
- `handleStop` in `apps/frontend/app/page.tsx`: `await stopTicker(ticker)` then `setTicker(null)`
  + clear error, and passes `onStop={handleStop}` to `TopBar`. `setTicker(null)` returns the body
  to `<IdleState/>` **and** triggers `useTapeStream`'s effect cleanup, which closes the WS
  **client-side** — the "no further updates" mechanism (does not rely on the server closing the
  socket).

## Files Changed

- `apps/backend/app/watch_manager.py` — add `WatchManager.stop(ticker) -> bool` (cancel feeder, set closed, remove engine).
- `apps/backend/app/main.py` — add `DELETE /watch/{ticker}` route (200 stopped / 404 not-watched).
- `apps/backend/tests/test_watch_manager.py` — **new** — 5 unit tests: stop removes/closes, idempotent not-watched False, feeder cancellation (async), re-watch builds a fresh cold engine, determinism guard (no state leakage across the stop boundary).
- `apps/backend/tests/test_api.py` — add 2 route tests: full DELETE lifecycle (200 stopped → reads 404 → WS 4404 → re-watch 200) and not-watched → 404; plus `TestClient`/`WebSocketDisconnect` imports.
- `apps/frontend/lib/api.ts` — add `StopResult` + `stopTicker(ticker)` (DELETE; 404 = effectively-stopped).
- `apps/frontend/components/TopBar.tsx` — add Stop button (only when `watched`) + `onStop` prop; static rose ghost class.
- `apps/frontend/app/page.tsx` — add `handleStop` (stopTicker → `setTicker(null)` → clear error); pass `onStop`.

## Tests Run

**Backend** — Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **68 passed** (61 pre-existing + 7 new), 0 failed. Re-run twice — stable, no flakiness in
the async feeder-cancellation timing test.

**Frontend** — Command: `cd apps/frontend && npm run build`
Result: **passed** — compiled successfully, type-check clean, 4/4 static pages generated. Verified
the Stop button's new static rose classes (`rose-500/70`, `rose-500/10`, `rose-500/20`,
`text-rose-300`, `ring-rose-400`) are present in the emitted CSS bundle (not dropped).

**Live HTTP smoke test** (real uvicorn server, not ASGI transport): full J-09 lifecycle on
`SIM-BUYER` — POST→200, DELETE(watched)→200, GET state after stop→404, DELETE(not-watched)→404
(honest detail), re-POST→200, GET state re-watched→200, DELETE unknown ticker→404. All as expected.

## Pre-handoff verification

- **Service startup:** backend (`uvicorn main:app`) starts clean (`/health` → 200); frontend
  (`next dev`) starts clean (`GET /` → 200, compiled in ~4s). Both server processes were killed
  after verification; test ports confirmed clear. No external integrations in this iteration.
- **Red-flag guard (confirmed byte-untouched):** `apps/backend/app/engine/classifier.py`,
  `apps/backend/app/engine/features.py`, `apps/backend/app/config.py`, and
  `apps/backend/app/providers/` show **no** changes in `git status` — teardown is purely a
  `WatchManager` + API + frontend-control concern, as required.

## Known Issues

- **None blocking.** No new thresholds/config, no new Data-Contract value, no nav change — J-09
  realizes the already-registered `DELETE /watch/{ticker}` half of an existing blueprint row.
- **TestClient note (not a product issue):** in `test_api.py` the re-watched engine's
  `stream_status` reads `"closed"` under `fastapi.testclient.TestClient` because its per-request
  portal tears down the event loop after each call, cancelling the fresh feeder (whose
  `CancelledError` handler sets `"closed"`). So the API test asserts the timing-independent
  404→200 transition for "re-watch = fresh read"; the cold-start / no-state-leakage guarantee is
  proven directly (object identity, `event_count == 0`, determinism) in `test_watch_manager.py`.
- **Browser observation timing (handled, per iter-5/iter-6 lessons):** the live→idle teardown is
  most convincing while the stream is still live, but bounded sim streams (10,000 events) and WS
  pacing mean the dot may read `closed` if the click is late. The Stop handler drives idle
  **regardless** of server stream state (client-side WS close), so idle-return + re-watch-fresh
  hold either way; browser-qa MAY widen pacing via `TAPEOLOGY_FEED_PACE=0.12` (delivery pacing
  only — does not affect classification determinism) to make the live window easier to catch.

## Suggested Next Phase

With J-09 green, all nine Must-have journeys and the full watch lifecycle are complete. The next
step is evaluation (expected **GOAL_ACHIEVED**, subject to coherence remaining PASS and no
regression in J-01–J-08) rather than new feature work. If continuing, the goal doc's explicit
"later / nice-to-have" items (extended tape states, L2 `BookLevelEvent` + liquidity features,
persistence, the replay/backtest predictive-value harness) are the natural Phase-2 candidates —
none are MVP-required.
