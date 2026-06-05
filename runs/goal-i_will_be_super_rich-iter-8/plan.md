# goal-i_will_be_super_rich-iter-8 Execution Plan

Final build slice toward GOAL_ACHIEVED. After iter-7, 18/20 must-have journeys pass; this
iteration closes **J-20** (local-time historical window picker + US-session quick-picks, with a
timezone-correct fetch) and promotes **J-18** (real-historical candlestick chart) from `partial`
to `passing` via a rendered screenshot. No new page, no new route, no nav change — additive only.

## What to Build
- **Frontend datetime resolution module** (Data Contract row 12 owner). Extend
  `apps/frontend/lib/datetime.ts` with a **pure** function that takes the user's selected local
  date + start/end times and returns explicit **tz-aware ISO-8601 UTC instants** (offset or `Z`),
  resolved **once**, before the `POST /watch` body is built. This replaces the naive
  `` `${date}T${startTime}` `` construction at `TopBar.tsx:83-84` (the iter-2 load-bearing bug:
  the picker sends a naive value the backend treats as UTC, forcing operators to hand-convert ET→UTC).
- **Local timezone label** on the Historical picker — derived from
  `Intl.DateTimeFormat().resolvedOptions().timeZone` / the local offset — so the user sees which
  zone their entry is interpreted in (satisfies "all market/session times shown carry a zone label").
- **US-session quick-picks** beside the Historical date/time controls: **Open 9:30 ET**,
  **Close 16:00 ET**, **Full RTH (9:30–16:00 ET)**. Each annotated with its **local equivalent**
  for the selected date; clicking one fills a valid regular-hours start/end that then resolves
  through the same row-12 function to tz-aware UTC. The 9:30/16:00 ET anchors are **named preset
  constants**, and the ET→local/UTC mapping is computed via the IANA `America/New_York` zone so it
  is **DST-correct** (no hardcoded ±4/±5 offset).
- **Honest watched-source label** — the Historical descriptor shown must reflect the actual
  resolved window; do not display a window different from the one fetched (backend already builds
  the row-6 descriptor from the submitted `body.start`/`body.end`).
- **Backend source-of-truth verification test** (not a behavior change): assert the historical
  watch path / `_parse_window_dt` fetches the **exact** UTC instant for an **offset-bearing** input
  (e.g. `…T09:30:00-04:00`), and that a **naive** input remains treated as UTC (no regression of
  existing behavior). This proves the contract the corrected frontend now relies on.
- **J-18 render verification** (no code change to the chart pipeline): browser-QA watches the
  committed real Ford fixture window in Historical mode against a clean isolated build and captures
  a **populated** candlestick screenshot with tape-state markers, plus a 10→30→60 s bar re-render.

## Agents Required
- developer: yes -- extend `lib/datetime.ts` with the resolution function + named ET anchors; wire
  it + the zone label + quick-pick row into `TopBar.tsx` (replacing the naive datetime build); add
  the backend offset-bearing-instant unit test. No engine/classifier/provider/endpoint logic.

## Frontend Present
yes

## Files to Create/Modify
- `apps/frontend/lib/datetime.ts` -- ADD pure resolution fn (local date+time → tz-aware UTC ISO
  instants, once, before POST) + named ET session-anchor constants (9:30 / 16:00) + ET→local/UTC
  mapping via `America/New_York`; keep the existing display-only `formatMarketTime`.
- `apps/frontend/components/TopBar.tsx` -- replace naive `` `${date}T${startTime}` `` at lines
  83-84 with the row-12 resolver; render the **local zone label** and the **US-session quick-pick**
  row (Open / Close / Full RTH, each annotated with the local equivalent) inside the existing
  `mode === "historical"` reveal.
- `apps/backend/tests/test_history_api.py` (or a focused new test module) -- ADD a unit test:
  offset-bearing `start`/`end` are fetched for that exact UTC instant; naive value unchanged.
- `docs/handoffs/goal-i_will_be_super_rich-iter-8-dev.md` -- dev handoff (required by DoD).
- `runs/goal-session-i_will_be_super_rich/state/blueprint.md` -- additive row-12 clarification only
  (name `lib/datetime.ts` as the resolution owner; mark built this iteration). **No nav-skeleton
  change; no re-approval requested.** (Coherence-auditor / summarizer territory — surgical edit.)

## UI Evolution
- New user-facing capability: a Historical user picks a date/time window in their **own local
  timezone** (clearly labeled), or one-clicks a **US-session preset** (Open / Close / Full RTH)
  shown in both ET and their local time, and trusts the fetched window **matches** their local
  selection — no mental UTC conversion, no silent shift.
- New information displayed: an explicit **local timezone label** on the Historical picker; three
  **quick-pick** controls each annotated with the local-time equivalent for the chosen date; and
  the **populated real-historical candlestick chart** (real replayed Ford prices + tape-state
  markers) made visible/verified (J-18 — newly evidenced, not new UI).
- New user actions: click a **US-session quick-pick** to fill the start/end window. (Unchanged:
  enter date/start/end/speed and Watch — now resolved to a tz-aware instant.)
- UI surface changes: the existing Historical controls in `TopBar.tsx` gain a zone label and a
  quick-pick row. No new page, no new route, no new panel.
- Navigation changes: none. All work stays on `/`, inline with the existing Historical reveal.

## Visual Requirements
- Component patterns: hand-built panels (DESIGN SYSTEM = no component library). Reuse the existing
  `INPUT_CLASS` and the established small-button styling already in `TopBar.tsx` for the quick-pick
  buttons; keep the date/time/speed inputs as-is. Monospaced numerics (`font-mono`) for any
  time/offset display.
- Layout: quick-pick buttons sit in the same flex row as the Historical date/time/speed controls
  (wraps on narrow); the zone label is a small muted text element adjacent to the date/time inputs.
- Key visual effects: restrained per DESIGN SYSTEM — subtle slate borders, hover/focus/active on
  buttons. No new colors; the picker is neutral chrome (no buy/sell semantics here). The chart's
  existing emerald/rose/amber marker semantics are unchanged.
- States to handle: zone label always shown in Historical mode; quick-picks disabled or no-op when
  no date is chosen (a quick-pick must produce a **valid** start < end, never a malformed/empty
  window); the chart's existing empty/loading treatment is unchanged (an empty window ⇒ empty
  chart, never fabricated candles).

## Key Test Scenarios
- **J-20 (browser, no creds):** in Historical mode the picker shows an explicit **local zone
  label**; the three quick-picks (Open 9:30 ET / Close 16:00 ET / Full RTH) render with
  **local-equivalent** annotations; clicking one (e.g. Open) fills a **valid RTH** start/end.
  Screenshot each.
- **J-20 timezone-correct fetch (browser network inspection + backend test):** submitting the
  window sends a **tz-aware** `start`/`end` (offset or `Z`) **equal to the selected local instant**
  — not a naive string, not UTC-shifted; AND the backend unit test confirms an offset-bearing
  instant is fetched for that exact UTC instant (naive still treated as UTC, unchanged).
- **J-18 (browser, no creds — REQUIRES PIXELS):** watch the committed Ford fixture window
  (`F`, 2026-06-02 15:00–15:02) in Historical mode against a **clean isolated `.next`** + isolated
  backend port; capture a **populated** candlestick screenshot with real replayed prices + markers;
  switch bar size 10→30→60 s and screenshot the re-render. An idle/placeholder screenshot, a
  `PASS_SURFACE`, or a `browser-qa SKIPPED` is **NOT** a pass.
- **Error cases (no regression):** end ≤ start rejected (existing 422); out-of-set replay speed
  rejected (existing 422); a quick-pick always yields start < end; an empty historical window still
  yields the honest `no_data_for_window` state and an **empty** chart (J-14 / one-focused-chart
  anti-goal intact).
- **Required-still-passing:** J-11 / J-16 (historical replay + resolved side — this iteration
  touches the historical watch path), J-17 (sim chart still renders), J-19 (pause/resume), and the
  full backend suite green incl. `test_history_api.py`, `test_historical_provider.py`,
  `test_watch_manager.py`.

## Assumptions & Notes (documented per token policy)
- **No frontend unit-test runner exists.** `apps/frontend/package.json` has only `dev`/`build`/
  `start`; project-template states "Frontend tests: N/A (covered by browser QA)" and the frontend
  test command is `npm run build` (type-check only). The spec's frontend-resolution-unit-test bullet
  is therefore satisfied by **two existing, runnable checks** rather than a new TS test harness:
  (a) the **backend** offset-bearing-instant unit test (in scope, runs under pytest), and (b)
  **browser-QA network inspection** asserting the POST body's `start`/`end` are tz-aware and equal
  to the selected local instant (explicit in the DoD). Adding jest/vitest is treated as
  **out-of-scope** (new dependency + infra beyond this slice); if the reviewer judges a TS unit test
  necessary for the DST math, that is a separate decision. The DST-correctness still MUST be
  demonstrated — pick the row-12 implementation so a DST-affected date resolves correctly via
  `America/New_York` (verifiable by network inspection on such a date and/or a manual node check
  documented in the handoff).
- **Prefer the frontend fix over a backend change.** `_parse_window_dt` already honors a tz-aware
  offset and only falls back to UTC for a naive value — leave that fallback intact. The durable fix
  is that the frontend stops sending naive values. Touch the backend fallback **only** if a reviewer
  proves it unsafe AND no historical test regresses (per OUT OF SCOPE).
- **Clean-state walkthroughs use a penny-spread name (Ford).** The free IEX top-of-book is wide for
  high-priced names (AAPL reads `unclear`, which is correct and out of scope); the committed Ford
  fixture is the offline-reproducible real-historical source for J-18.
- **Shared `.next` is a known hazard** (corrupted browser-QA twice with a `./833.js` 500). The
  browser run MUST use an isolated `NEXT_DIST_DIR` + isolated backend port, and MUST NOT
  `git checkout` any file carrying uncommitted iter edits (iter-3/iter-6 lessons).
- **Goal alignment:** this slice maps 1:1 to goal.md Key Capability 15 (historical window selection
  in local time) and Capability 13 (the one focused chart, now real-data render-verified). It
  introduces **no** new Data Contract value (row 12 already registered; J-18 reads row-10 verbatim),
  stays inside the single `/` HOME, and respects every cited critical anti-goal
  (timezone-correct-windows, one-focused-chart, no-fabricated-data, single-source-of-truth,
  no-execution-path). No scope creep detected; no general/arbitrary-timezone picker (only local +
  ET presets) and no live-mode change.
- **Path to GOAL_ACHIEVED:** once J-20 passes with a timezone-correct fetch and J-18 has a populated
  real-historical screenshot, all 20 must-have journeys pass — a GOAL_ACHIEVED **candidate** for the
  evaluator (the evaluator, not this plan, makes that call). J-18's against-the-live-vendor leg
  remains operator-gated (like J-12/J-15); the offline fixture render satisfies the in-loop bar.
