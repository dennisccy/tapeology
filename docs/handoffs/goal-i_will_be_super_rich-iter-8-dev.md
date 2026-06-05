# goal-i_will_be_super_rich-iter-8 Dev Handoff

**Phase:** goal-i_will_be_super_rich-iter-8
**Date:** 2026-06-05
**Agent:** developer
**Status:** complete

## What Was Built

- **Timezone-correct historical window resolution (J-20).** The Historical date/time picker now
  resolves the user's selected **local** date + start/end times to explicit **tz-aware UTC ISO-8601
  instants** (`…Z`) once, in the frontend, before the `POST /watch` body is built. This replaces the
  naive `` `${date}T${startTime}` `` construction (the iter-2 load-bearing bug, where the picker sent
  a naive value the backend then treated as UTC, forcing operators to hand-convert ET→UTC).
- **Local timezone label** on the Historical picker — the operator's IANA zone (e.g.
  `Asia/Hong_Kong`), derived from `Intl.DateTimeFormat().resolvedOptions().timeZone`, shown so the
  user sees which zone their entry is interpreted in.
- **US-session quick-picks** beside the Historical controls: **Open 9:30 ET**, **Close 16:00 ET**,
  **Full RTH 9:30–16:00 ET**. Each is annotated with its **local equivalent** for the chosen date,
  and one click fills a valid regular-hours start/end. The 9:30 / 16:00 ET anchors are **named
  constants**; the ET→local/UTC mapping is computed via the IANA `America/New_York` zone, so it is
  **DST-correct** (no hardcoded ±4/±5 offset).
- **Backend source-of-truth verification tests** (not a behavior change): assert the historical
  watch path fetches the **exact** UTC instant for an **offset-bearing** input (e.g.
  `…T09:30:00-04:00` → `13:30Z`, and `…-05:00` in winter → `14:30Z`), and that a **naive** input is
  still treated as UTC (no regression of the existing `_parse_window_dt` fallback).

No engine, classifier, provider, or endpoint logic changed. J-18 (real-historical chart render) is
left to browser-QA to evidence with a populated screenshot — no code change to the chart pipeline.

## Files Changed

- `apps/frontend/lib/datetime.ts` — ADDED the row-12 resolution module: `resolveLocalWindowInstant`
  (local date+time → tz-aware UTC ISO, once), named ET session anchors `ET_SESSION_OPEN` /
  `ET_SESSION_CLOSE`, `etWallTimeToUtc` (DST-correct ET→UTC via `America/New_York`),
  `resolveSessionPreset` (quick-pick local fills + local-equivalent annotations), `localZoneLabel` /
  `localOffsetLabel` (zone label), and `utcToLocalTimeInput`. The existing display-only
  `formatMarketTime` is unchanged.
- `apps/frontend/components/TopBar.tsx` — REPLACED the naive datetime build in `handleSubmit` with
  the resolver; ADDED the local zone label and the US-session quick-pick row inside the existing
  `mode === "historical"` reveal; ADDED a `presetWindow` state so a quick-pick submits its
  already-resolved tz-aware instants verbatim (correct even when the session spans two local
  calendar dates), with manual edits to date/start/end clearing it.
- `apps/backend/tests/test_window_resolution.py` — NEW focused test module: 6 tests covering the
  offset-bearing-instant resolution (summer EDT + winter EST), the `Z`-suffix case, the naive→UTC
  no-regression case, and two HTTP integration tests asserting the exact UTC instant reaches
  `adapter.fetch_historical`.

No blueprint edit was made: `runs/goal-session-i_will_be_super_rich/state/blueprint.md` row 12
**already** names `lib/datetime.ts` as the resolution owner, documents the DST-correct
`America/New_York` mapping + named ET preset constants, and is marked "built at iter-8" (line 92 /
line 77). The implementation matches that registered contract exactly; an additional edit would be
redundant.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **184 passed, 1 skipped** (the 1 skip is the pre-existing operator-gated live-integration
test). Named required modules green: `test_history_api.py`, `test_historical_provider.py`,
`test_watch_manager.py`, `test_real_data_gate.py`, plus the new `test_window_resolution.py` (68
passed across those modules together).

Frontend type-check + compile: `cd apps/frontend && npx next build` (run with an isolated
`NEXT_DIST_DIR`, then the dir + the build's tsconfig/next-env edits were reverted so only the two
intended source files remain modified) — **compiled successfully, all types valid, 4/4 static pages
generated**.

DST-correctness verification (no TS unit runner exists — see Known Issues): a Node check of the
resolver math under fixed `TZ` confirmed:
- `etWallTimeToUtc("2026-06-02", 9, 30)` → `2026-06-02T13:30:00.000Z` (summer EDT, −04:00)
- `etWallTimeToUtc("2026-01-05", 9, 30)` → `2026-01-05T14:30:00.000Z` (winter EST, −05:00) — the
  **different** offset proves it is zone-driven, not a fixed offset.
- Under `TZ=Asia/Hong_Kong` (UTC+8), the same ET anchor still resolves to `13:30Z`, the quick-pick
  fills the **local** input as `21:30`, and re-resolving that local fill round-trips back to `13:30Z`.

## Known Issues

- **No frontend unit-test runner exists.** `apps/frontend/package.json` has only `dev`/`build`/
  `start`, and project-template states "Frontend tests: N/A (covered by browser QA)". The frontend
  resolver's DST-correctness is therefore evidenced by (a) the in-scope **backend** offset-bearing
  test (under pytest), (b) the documented **Node** check above, and (c) **browser-QA network
  inspection** of the POST body's `start`/`end`. Adding jest/vitest was treated as out-of-scope (new
  dependency + infra beyond this slice).
- **Local-midnight span across far-east zones.** The US RTH session can fall on two **local**
  calendar dates (e.g. 16:00 ET = 04:00 next-day in Hong Kong). A quick-pick handles this correctly
  because it submits its pre-resolved tz-aware instants verbatim (the `presetWindow` override) rather
  than re-resolving local `HH:MM` against the single `<input type="date">`. Note for QA: in such a
  zone the quick-pick's filled `end` time input may read earlier than `start` (it belongs to the next
  local day) — this is expected; the **submitted** window is still a valid `start < end` UTC range.
  A purely **manual** entry in such a zone is still bound to the one selected date, which is the
  documented manual-entry behavior (the quick-picks exist precisely to make the common RTH case
  one-click-correct).
- **J-18 is render-verification only.** No code in the chart pipeline changed this iteration; the
  populated real-historical screenshot must come from browser-QA watching the committed Ford fixture
  window (`F`, 2026-06-02 15:00–15:02) against a clean isolated `.next` + isolated backend port. A
  placeholder/idle screenshot or a SKIPPED browser run is not evidence (iter-6/iter-7 lesson).
- **Shared `.next` hazard.** Per the iter-3/iter-6 lesson and the project MEMORY note, do not build
  against the live harness `:3650 .next`; the QA harness already has running servers on `:3650`/
  `:8650`/`:3651`. The browser run must use an isolated dist dir + isolated backend port.
