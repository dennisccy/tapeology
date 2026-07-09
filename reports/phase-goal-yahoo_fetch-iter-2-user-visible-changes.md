# Phase goal-yahoo_fetch-iter-2 — User-Visible Changes

**Phase:** goal-yahoo_fetch-iter-2
**Date:** 2026-07-09
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- **Nothing new by clicking anywhere in the browser app.** This iteration shipped zero frontend
  source changes (`git diff --stat -- apps/frontend/` is empty) and added no button, page, field,
  or link. A person browsing the web app cannot trigger any of this iteration's new capability.
- **For an operator/developer calling the API directly** (curl, a script, or the MCP `bars` proxy —
  not the web browser), `POST /research/bars` can now successfully fetch real weekly (`1w`), hourly
  (`1h`), 5-minute (`5m`), and 1-minute (`1m`) Yahoo Finance bars. Previously only daily (`1d`)
  worked; every other timeframe failed with one generic "no bars" error regardless of cause.
- **That same operator can now also fetch a 4-hour (`4h`) series** — not a native Yahoo interval,
  but real hourly bars combined into 4-hour blocks by the backend itself (open/high/low/close/volume
  aggregated honestly, the trailing partial block left short rather than padded). This did not exist
  in any form before this iteration.
- **When a fetch request can't be served, the operator now gets a specific reason** instead of one
  generic message: requesting a timeframe Yahoo doesn't offer this era (`8h`, `1mo`, `15m`) returns
  `"timeframe '<tf>' is not served by Yahoo Finance"`; requesting a real supported timeframe whose
  specific symbol/date window has no data returns a distinct `"no data for <symbol> <timeframe> in
  the requested window"` message. Both are still HTTP 422, and neither ever returns fake bars.

## What Changed in the Visible UI

- **No page, component, label, button, or navigation element changed.** `/`, `/journal`,
  `/journal/[id]`, `/studies`, `/performance`, and `/structure` are byte-identical in source to
  before this iteration.
- **Latent effect worth knowing about (existing code, not new this iteration):** the `/structure`
  page already contains generic, timeframe-agnostic display logic that predates this iteration —
  `pickRepresentativeSeries()` in `apps/frontend/app/structure/page.tsx` already ranks every
  registered bar series for a symbol using a `TIMEFRAME_ORDER` list that already spans
  `1m, 5m, 15m, 1h, 4h, 8h, 1d, 1w, 1mo` (shortest-available wins), and `StructureChart.tsx` already
  labels every S/R level line with `${level.timeframe} ${level.type}` verbatim, for any timeframe
  string. Because that generic logic already existed, the FIRST TIME a `1h`/`1w`/`5m`/`1m`/`4h`
  series is ever registered for a symbol (only possible via a direct API call today, not a UI
  action), `/structure` will automatically start rendering that series' candles and level labels
  instead of daily — with zero frontend code change. Before this iteration, that logic never had
  anything but `1d` to choose from, since Yahoo could only fetch `1d`. This is not a new feature
  shipped this iteration — it is pre-existing frontend behavior that this iteration's backend change
  makes reachable, but only through a channel (direct API/MCP fetch) outside the product's own UI.

## What Old Behavior Changed

- **Fetching a daily (`1d`) bar series** via `POST /research/bars` continues to work exactly as
  before — output is byte-identical to last iteration.
- **Fetching an hourly, weekly, 5-minute, or 1-minute series** via `POST /research/bars`: previously
  every one of these requests always failed with a generic 422 "no bars in the requested window,"
  even though the request itself was perfectly valid. Now these requests succeed and return real
  bars, the same way daily fetching already did.
- **Error responses from `POST /research/bars` for a request Yahoo can't serve**: previously every
  failure case (unknown symbol, out-of-range window, unsupported timeframe) returned the identical
  generic message. Now the message differs depending on the cause (see above). Any script or
  integration that pattern-matches the old generic error text should be re-checked — the HTTP status
  code (422) is unchanged in both new cases, but the message text is not.

## Not Visible Yet

- **There is still no on-screen control anywhere in the app to fetch bars from Yahoo Finance, at any
  timeframe** — this was already true after last iteration and remains true here; a person cannot
  click a button to fetch `1w`/`1h`/`5m`/`1m`/`4h` (or even `1d`) bars. That fetch-trigger UI on the
  `/structure` page is explicitly deferred to a future iteration ("J-05" per `docs/goal.md`).
- **The derived `4h` timeframe has no on-screen provenance indicator** distinguishing it as
  "combined from real hourly bars" versus a directly-fetched series — that labeling (the "Yahoo
  Finance" provenance badge / `taxonomy.FEED_BASIS_LABELS`) is also part of the deferred J-05 work.
- **The new, more specific error messages are only observable by calling the API directly** (or via
  a future UI that surfaces them) — no part of the current web app can trigger a fetch, so no part
  of the current web app can currently display one of these new error messages to a browsing user.
- **The Cockpit's feed indicator remains "Simulated"** and is unaffected by any of this — the
  Yahoo/live-bar work in this era stays confined to the Structure/research bar-fetch path, never
  the live tape shown on the home page.
