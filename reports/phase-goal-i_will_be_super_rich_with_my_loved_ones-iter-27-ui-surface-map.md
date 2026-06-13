# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-27 — UI Surface Map

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-27
**Date:** 2026-06-13
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

No UI surfaces were changed in this iteration. The iteration was verification-only; backend and
frontend source files are byte-identical (J-68 sentinel holds — `git diff --stat HEAD --
apps/backend/ apps/frontend/` is empty at the end of the iteration).

The table below records the **existing** cockpit surfaces that browser-qa-agent must exercise
and capture as pixel evidence this iteration. These surfaces did not change in code; they are
listed so QA knows which DOM elements must visibly appear in each capture.

| Route / Page | Component / Element | Change Type | Why Listed | What to Test |
|-------------|---------------------|-------------|------------|--------------|
| `/` | Cockpit panel grid (bid / ask / spread / last, features, tape-state + confidence) | No change | J-11 / J-20 evidence capture required | Start a historical AAPL watch via `POST /watch/AAPL` with a real past RTH window; confirm bid, ask, spread, and last fields display non-zero numeric values within 30 s of the watch starting |
| `/` | Recent-trades list — side column | No change | J-16 evidence capture required | After the same historical AAPL watch, scroll the recent-trades list and confirm the side column shows "buy" or "sell" labels, with the count of "unknown" rows visibly lower than the total (target: unknown fraction < 1%) |
| `/` | Candlestick chart + tape-state markers + time-axis labels | No change | J-18 evidence capture required | After the historical AAPL watch, change the chart bar size; confirm candles render, at least one tape-state marker appears at a transition, and the time-axis labels show real market-clock times (e.g. "09:30") not Unix epoch integers |
| `/` | Time-window picker (local-zone label + quick-picks) | No change | J-18 / J-20 evidence capture required | Open the time-window picker; confirm the label shows the user's local timezone name and the quick-pick buttons (e.g. "Last 30 min", "Open 30") are visible and clickable |
| `/` | Busy-window load + re-watch button | No change | J-29 evidence capture required | Watch a busy symbol/window (AAPL full RTH); confirm the cockpit finishes loading within the configured bound (≤ 30 s); click re-watch and confirm it completes near-instantly (< 3 s, using the cached window) |
| `/` | Replay-speed control (1× / 2× / 5× / 10× selector) | No change | J-32 evidence capture required | During an in-progress historical replay at 1×, change the speed to 10×; confirm the replay continues from the current position without restarting the watch (no full re-fetch, no progress reset) |
| `/` | Closed-market honest panel | No change | J-14 (a) evidence capture required | Watch any symbol in live mode while the US market is closed; confirm the panel displays "market is closed" (or equivalent copy) and shows the next open time (2026-06-15 13:30 UTC / 14:30 BST) |
| `/` | Unknown-symbol honest panel | No change | J-14 (b) evidence capture required | Submit a made-up ticker (e.g. "ZZZZNOTREAL") as a watch target; confirm the UI renders a "not a tradable symbol" message (or equivalent) and does not show a populated cockpit |
| `/` | Empty-window honest panel | No change | J-14 (c) evidence capture required | Request a historical window with no trades (e.g. a pre-market or holiday window); confirm the UI renders a "no data for that window" message and does not fabricate candles or trades |
| `/` | Error banner | No change | J-22 evidence capture required | Simulate a slow/non-resolving vendor call (or let a real timeout elapse); confirm a distinct timeout or "unreachable" error message appears within the 12-second client-side bound (no infinite spinner past 12 s) |
| `/` | Failure panel / error banner | No change | J-23 evidence capture required | Start a historical watch then terminate the backend process mid-stream; confirm the UI displays "couldn't connect to the tape stream" (or equivalent) within the expected bound and does not show an infinite spinner |
| `/` | Stream-status dot (owned by `stream_status`) | No change | J-27 evidence capture required | Trigger a no-first-event or feeder-failure condition; confirm the stream-status dot shows an explicit `stale`, `closed`, or no-data state — it must never display `live` when no data is flowing and must not remain stuck on `connecting` |

---

## Backend-Only Changes (No UI Impact)

- Full backend test suite re-run (848 passed, 1 skipped, exit 0) — confirms existing
  behavior, no code change, no UI impact.
- Live credentialed Alpaca historical fetch probe (AAPL 2026-06-12 09:30–09:32 ET) — confirms
  `AlpacaAdapter.is_available()` returns `True` and the engine resolves sides on real SIP data;
  no code change, no UI impact.
- `get_market_clock()` live probe — confirms `is_open=False`, next open 2026-06-15T13:30:00Z;
  no code change, no UI impact.
- Unknown-symbol probe (`ZZZZNOTREAL`) — confirms `SymbolNotTradable` is raised and the honest
  state is reachable; no code change, no UI impact.

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages / routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 4 (all verification probes — no source modification)
