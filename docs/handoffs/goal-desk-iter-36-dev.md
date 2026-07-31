# goal-desk-iter-36 Dev Handoff

**Phase:** goal-desk-iter-36
**Date:** 2026-07-31
**Agent:** developer
**Status:** complete

## What Was Built

J-21 (screen-pin disclosure): before clicking Run Screen (or before reading a past screen's own
provenance), the operator can now see whether a run under the pins that would resolve right now
would reuse an already-recorded snapshot or walk the universe fresh.

- New backend module `app/research/desk_screen_pins.py` — `resolve_desk_screen_pins(screen_date,
  universe_store, bar_index, config, screen_store)`. Resolves the five pins for a caller-supplied
  `screen_date` through EXACTLY the same accessors `run_screen_and_record` already uses, in the
  same order: `desk_screen.screen_as_of` (`as_of`), `UniverseStore.list()`'s own latest record id +
  member count (`universe_snapshot_id`, `members_total`), `Config.config_fingerprint()`
  (`config_fingerprint`), and `desk_screen.compute_bar_store_signature` over
  `desk_coverage.get_desk_coverage`'s index-only read (`bar_store_signature`) — zero new
  derivation, no `BarStore` read of any kind. The recorded-or-not answer comes from
  `ScreenStore.find_by_key` on exactly those five pins — the same lookup J-18's pre-check already
  makes. Honest empty (`universe_snapshot_id`/`bar_store_signature`: `null`, `members_total: 0`,
  `recorded: null`) before any universe snapshot is registered, rather than hashing a signature
  over nothing.
- New endpoint `GET /research/desk/screen/pins` (`screen_date` REQUIRED query param, 422 if
  absent) wired into `desk_routes.py`. Takes only `UniverseStore`/`BarIndex`/`ScreenStore`
  dependencies — no `BarStore`/`DatasetStore`/compute-manager dependency at all, so it is
  structurally incapable of a `compute_tradability` call or a `BarStore` read. Writes nothing,
  triggers nothing, recomputes nothing. No new store, no new `Config` field, no new MCP tool (the
  existing `/research/` allowlist already reaches the new GET path).
- Frontend: `DeskProvenance` (`apps/frontend/app/desk/page.tsx`) gains a new
  `DeskProvenancePins` block rendering the pins resolved right now for the DISPLAYED snapshot's own
  `screen_date`, beside its already-shown recorded pins — the served `recorded`-or-`null` answer IS
  the match/differ statement (the page computes no equality of its own, per the J-20 rule and the
  logged interpretation call in `assumptions.md` iter-36 entry 1). A new `TodayScreenPinsNote`
  component renders one descriptive line inside the shared `ScreenComputeControl` (so it
  automatically appears beside the Run Screen button in BOTH the empty-state panel and the
  populated page's own control panel), querying the same endpoint for `todayUtcDate()` — the exact
  value the trigger already submits. Both fetches are page-load/selection-change GETs only — no
  timer, no polling loop; `todayPinsResult` additionally refreshes once on the screen-compute
  poll's own terminal tick (the same "refresh ledgers once on terminal" precedent the page already
  uses for Top-up Runs / Index Reconciliation / Screen Runs).

## Files Changed

- `apps/backend/app/research/desk_screen_pins.py` -- new module, the pin-resolution read (J-21's
  sole owner)
- `apps/backend/app/research/desk_routes.py` -- new `GET /research/desk/screen/pins` route +
  updated module docstring
- `apps/backend/tests/test_desk_screen_pins.py` -- new test file: TC-1/TC-2 (resolved pins name
  the exact snapshot a trigger reuses), TC-3/TC-4 (a planted bar-index row shifts the signature and
  a trigger then walks fresh, leaving the earlier file byte-identical), TC-5 (honest empty), TC-6
  (zero `compute_tradability`/`BarStore` calls, structurally proven by poisoning every `BarStore`
  method), TC-7 (byte-identical repeat), TC-8 (422 on missing `screen_date`), plus three route-level
  wiring tests
- `apps/frontend/lib/types.ts` -- new `DeskScreenPinsResult`/`DeskScreenPinsRecorded` types
- `apps/frontend/lib/api.ts` -- new `fetchDeskScreenPins(screenDate)` helper
- `apps/frontend/app/desk/page.tsx` -- `DeskProvenancePins`/`TodayScreenPinsNote` components,
  `pins`/`displayedPins` props threaded through `ScreenComputeControl`/`ScreenControlProps`/
  `DeskProvenance`/`DeskPopulatedScreen`, two new state hooks + two new effects (one mount fetch,
  one keyed on `displayedSnapshot`), one terminal-tick refresh added to the existing screen-compute
  poll effect

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: 1559 passed, 8 skipped, 0 failed (full suite; includes the 8 new tests in
`test_desk_screen_pins.py`, all passing)

Also ran: `cd apps/frontend && npx tsc --noEmit -p tsconfig.json` -- 0 errors.

Verified unchanged (per DoD):
- `Config().config_fingerprint()` == `08e471b10130e1e2` (zero new `Config` fields — this module
  takes no `Config` field of its own, only the process-wide singleton for `.config_fingerprint()`)
- Zero diff to `desk_screen.py`/`desk_screen_compute.py`/`desk_coverage.py`/`tradability.py`/
  `levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`

## Pre-handoff verification

- Ran `rm -rf apps/frontend/.next` then `bash scripts/dev.sh` (T-9 clean rebuild) -- backend
  (`:8301`) and frontend (`:3301`) both started cleanly (`{"status":"ok"}` from `/health`, HTTP 200
  from `/desk`). Stopped both, started again -- second start also came up clean with no port
  conflicts (`scripts/dev.sh`'s own port-based kill-before-start logic handled it; my own ad-hoc
  `pkill -f` cleanup commands during manual testing did NOT reliably reach the nested `next dev ->
  next-server` child process on the first try -- a reminder that PATTERN-based kills on this
  process tree are unreliable, but the SHIPPED `scripts/dev.sh` already uses a port-based
  `lsof`/`fuser` loop, which is robust and needed no change).
- Live-verified the new endpoint against the REAL ambient store: `GET
  /research/desk/screen/pins?screen_date=2026-07-31` returned
  `bar_store_signature: "2ce14e8f252966f7"`, `recorded: null` -- byte-identical to the exact
  "differ" scenario goal.md's own iter-36 rationale text describes (measured independently,
  read-only, before this build). Confirmed via Chrome MCP that `/desk` renders both the
  `DeskProvenance` differ line and the Run-Screen differ line correctly against this live ambient
  state, with zero console errors (only the benign React DevTools info log).
- All backend/frontend processes stopped and confirmed off both ports before finishing (no server
  left running).

## Known Issues

- The match state (recorded pins matching the displayed snapshot) and the honest empty state (no
  universe registered) are NOT exercised live in this handoff's own manual browser pass — per the
  iter spec's OUT OF SCOPE / lessons.md iter-32, those two states are meant to be captured on a
  FIXTURE-SCOPED rig by the browser-qa-agent, never by an ambient Run Screen click (which would
  invalidate sibling golden scripts pinned to the current ambient state). Both states ARE covered
  by backend unit tests (TC-1/TC-2 for match, TC-5 for empty) against planted, scoped stores.
- `journey-scripts/J-21.json` and the `[NEW]`-flagged demo-narrator walkthrough are NOT part of
  this handoff — per this codebase's own pipeline division of labor (confirmed against the
  goal-desk-iter-35 dev handoff's identical note), journey-scripts are authored by the browser-QA
  step and the walkthrough by the demo-narrator step, both after the code lands and is
  browser-verified.
- The interpretation call in `assumptions.md` iter-36 entry 1 (no separate `matches_displayed`
  boolean; the `recorded`-present-or-absent answer alone is treated as the match/differ statement)
  is implemented literally as logged. This is reversible per that entry's own note.
