# goal-clean_slate-iter-2 Frontend Handoff

**Phase:** goal-clean_slate-iter-2 (J-02: "Frontend + WS demolition — the two-page product")
**Date:** 2026-07-24
**Agent:** developer
**Status:** complete

## What Was Built

Subtractive only — no new UI capability, information, or action. The product's visible surface
shrinks from a 5-route, 5-link-nav app down to exactly the two-page instrument goal.md's Vision
names: **Cockpit `/` and Structure `/structure`, nothing else**. Every kept behavior on both
surviving pages — both charts, the provenance badge, levels/zones, tradable map, edge report,
strategy registry — was browser-verified to work exactly as before this iteration.

- **Nav shrinks from 5 links to 2** ("Cockpit", "Structure") — driven entirely by the backend's
  `GET /meta/ui-routes` (`app/meta.py`'s `UI_ROUTES` trim); `NavBar.tsx` itself needed no edit,
  confirmed by an empty `git diff` on that file (it already had "deliberately NO hardcoded route
  list here, not even as a fallback" per its own source comment).
- **`/journal`, `/journal/[id]`, `/studies`, `/performance` now render the app's real 404** — the
  existing dark, styled not-found treatment, not a blank screen, not a redirect, not a "coming
  soon" placeholder. Screenshot-verified for all four.
- **The manual thesis workflow is gone from the cockpit**: no thesis strip (declare/resolve/mark
  entry-exit/review), no hint dock (setup-forming hint declare affordance), no sound-cue toggle —
  anywhere. Verified by a full Watch → `buyer_control` → Stop cycle on `SIM-BUYER`: the cockpit
  panel grid (Tape State / Quote / Features / Recent Trades / Observations / Event Log) renders
  with nothing extra above or beside it, and Stop returns cleanly to the idle "No ticker watched"
  screen (no "surviving thesis" branch — that whole code path is deleted, not just hidden).
- **Both charts keep their full pre-iteration behavior** — the one sanctioned, closely-scoped edit
  (`PriceChart.tsx`'s thesis-geometry overlay removal) does not touch rendering:
  - Cockpit `PriceChart`: verified candles rendering (SIM-BUYER live tape + a real AAPL Historical
    replay), the Tape/History timeframe selector switching (10s/30s/60s and, for a recorded real
    symbol, 1m/5m/1h/4h/1d), the S/R tradable-band overlay rendering (a real AAPL 1h History view
    showed the resistance bands at 300.10–302.20 and several support bands below, each labeled
    with side/class/score/round-number exactly as before), and live tape bars moving as new trades
    arrived.
  - `/structure`'s `StructureChart` + Load flow: Loading the pinned AAPL as-of `2026-06-22T15:00:
    00Z` renders the SAME `300.11–302.2, Class A, score 171, 849 members, round number` resistance
    wall documented as this session's running pinned example. `StructureChart.tsx` itself has an
    empty `git diff` for the whole iteration — it was never opened for editing, let alone changed.
- **The feed-basis/provenance badge still renders** its label from the (already J-01-slimmed)
  `GET /research/taxonomy` `feed_basis` block — confirmed showing "Simulated" on the `SIM-BUYER`
  watch and "SIP (consolidated)" on the real AAPL Historical watch (two different feed labels,
  same taxonomy-driven lookup, proving the badge reads the served label rather than hardcoding
  one).
- **The WS frame carries no `thesis`/`hint` key.** Captured a live frame from
  `ws://localhost:8301/tape/SIM-BUYER/stream` directly (Python `websockets` client, not just a
  browser devtools glance): its 17 keys are exactly the engine projection (`ticker`,
  `stream_status`, `tape_state`, `confidence`, `data_feed`, `delivery_lag_seconds`, `event_log`,
  `features`, `headline_features`, `market`, `observations`, `paused`, `primary_window`,
  `recent_trades`, `scenario`, `timestamp`, `warm`) — no `thesis`, no `hint`. Saved at
  `runs/goal-session-clean_slate/iter-2/tc09-ws-frame-no-thesis-hint.json`.

## Changed Behavior

- **Top nav**: previously 5 links (Cockpit, Journal, Studies, Performance, Structure); now exactly
  2 (Cockpit, Structure).
- **Cockpit page**: previously showed a thesis strip between the chart and panel grid (idle
  declare line or an active projection) plus a hint dock under the tape-state panel and a
  sound-cue toggle; now shows neither — the panel grid renders directly, nothing added in their
  place (no empty-state placeholder — the capability itself is gone, not blanked).
- **`/journal`, `/studies`, `/performance`**: previously real pages; now each is the app's 404.

## Backend-Only Items

None — every backend change this iteration (the WS merge removal, the `ResearchRegistry` stub
cleanup, the `UI_ROUTES` trim) has an immediate, verified frontend-visible effect (the trimmed
nav, the vanished thesis/hint UI, the leaner WS frame). Nothing was built without a UI path.

## Incomplete Items

None from this iteration's own scope (J-02). Carried-forward, pre-existing, explicitly out of
scope here (documented in the phase spec's own Out-of-Scope list, re-confirmed unresolved):
`SHOW_CASE_STUDIES = false` on `/structure` (`apps/frontend/app/structure/page.tsx:335`) — still
suppresses the Case Studies section; not this journey's concern, flagged again for whoever plans
J-05.

## Config and Environment Changes

None. No new environment variable, no new config field, no build/tooling change. `rm -rf
apps/frontend/.next` + a fresh `next dev` start (T-9) was required before browser verification —
routine for any iteration that deletes pages, not a persistent config change.

## Known Limitations

- The chart-timeframe-button visual "selected" highlight on the cockpit `PriceChart`'s Tape
  10s/30s/60s group did not visibly update in one screenshot during manual testing even though the
  underlying view state DID change (the chart's caption text and rendered candle width both
  updated correctly). This is a **pre-existing** UI detail — `PriceChart.tsx`'s `segmentClass`/
  `view`-selection logic was not touched by this iteration's edit (confined entirely to the
  thesis-geometry removal), so it is not a regression introduced here and is out of this
  iteration's scope to investigate or fix (T-8 forbids any further edit to this file this era).
  Noted for whoever next has a legitimate reason to open `PriceChart.tsx`.
- `apps/frontend/app/structure/page.tsx:1305` carries a code comment with the bare word "Study"
  (contrasting backtests' behavior with the now-deleted replay-study runner's). Left untouched —
  not a TC-11 grep hit, not in this iteration's file list, and `/structure` is a high-stakes kept
  page with no mandate to touch this iteration.
