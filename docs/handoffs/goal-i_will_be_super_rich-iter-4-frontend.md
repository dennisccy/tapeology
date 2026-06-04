# goal-i_will_be_super_rich-iter-4 Frontend Handoff

**Phase:** goal-i_will_be_super_rich-iter-4
**Date:** 2026-06-04
**Agent:** developer
**Status:** complete — verification-only, **no frontend code changed**

## Summary

This iteration makes the **Live Watch action actually stream** (backend). The spec scoped the
frontend as verification-only: "the frontend needs no new code — once the backend live watch
creates an engine and flips the status, the cockpit and dot just work." I verified this end-to-end
and found **no gap**, so no frontend file was modified. Per the developer rules, any frontend
change must trace to the verification checkbox — none was needed.

## What Was Verified (no code change)

- **A successful Live watch renders the cockpit.** `lib/api.ts` `watchTicker` already treats any
  `2xx` (including the new live `{status:"watching"}`) as `result.ok`, capturing `scenario`.
  `app/page.tsx` `handleWatch` sets the ticker on `result.ok`, which mounts `<Cockpit>` and
  `useTapeStream` connects the WS. This path is mode-agnostic — it already worked for sim/historical
  and works identically for live. (Confirmed against a live `POST /watch/F` returning
  `{"ticker":"F","scenario":"live F","status":"watching"}`.)
- **The status dot reads the canonical live/stale status.** `components/TopBar.tsx` `STREAM_DOT`
  maps `live` → emerald (`bg-emerald-400`), `stale` → amber (`bg-amber-400`), `closed` → rose,
  reading `snapshot.stream_status` verbatim — no client recompute (single source of truth). So a
  live feed reads green and a feed lull reads amber with no UI change.
- **The watched-source label shows `live <SYM>`.** `TopBar.tsx` renders `snapshot.scenario`
  verbatim ("scenario: live F"); the backend now emits `live <SYM>` as the row-6 descriptor.
- **Live controls already render.** The Live mode reveals the `SymbolSearch` (J-13) and the
  `MarketStatusIndicator` (real `GET /market/clock`, J-14) — both unchanged from iter-3.
- **Lifecycle hardening already present (iter-0 lesson).** `page.tsx` `teardownActiveWatch`
  `DELETE`s the prior watch before a new Watch / mode switch, so switching live symbols closes the
  prior backend watch (and now its real vendor socket) — no orphaned watch / leaked socket.

## UI Surface / Navigation Changes

None. Still exactly one screen (`/`); the cockpit body is identical across sim / historical / live.
No new components, routes, actions, or displayed values. Row-6 `stream_status` now takes its
`live` / `stale` values from a real live feed (previously only `connecting` / `closed`).

## Browser QA Notes (for the browser-qa-agent)

- Re-verify the no-regression journeys: J-01, J-02 (SIM-BUYER → buyer_control), J-10 (mode
  selector reveal), J-11 (historical AAPL replay populates), J-13 (symbol search), J-14 (honest
  non-cockpit states).
- Confirm Live mode reveals the symbol search + market-status indicator, and that a successful
  live watch renders the cockpit with the dot reading **live** (emerald).
- **iter-3 caution (load-bearing):** build the frontend in an **isolated `.next`** (never the
  harness's shared one on `:3650`), and never `git checkout` a file carrying uncommitted iter edits.
- The live **feed itself** (J-12/J-15) is operator/gated — it was confirmed via the backend gated
  integration test against the real Alpaca socket during market hours (see the dev handoff), not via
  a browser-against-live-market test.
