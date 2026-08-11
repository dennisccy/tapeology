# goal-playbook-iter-4 Frontend Handoff

**Phase:** goal-playbook-iter-4
**Date:** 2026-08-10
**Agent:** developer
**Status:** complete

## What Was Built

- **No new section, no new route.** The already-shipped `/desk` Playbook Signals section (from
  J-03) now renders three additional setup types when they fire on a recorded session:
  jump-base-explosion (`jbe`), drop-base-implosion (`dbi`), and cup-and-handle (`cup_handle`).
- `playbookSetupLabel` (`apps/frontend/app/desk/page.tsx`) gains three labels: `"jbe"` → "Jump-Base
  Explosion", `"dbi"` → "Drop-Base Implosion", `"cup_handle"` → "Cup and Handle" — rendered in the
  same chip (`CHIP_CLASS`) the shipped opening-range-break setups already use.
- `PlaybookSignalDetail` (the expandable per-signal detail panel) branches on `signal.setup_id` to
  render each new setup's own geometry disclosure line, verbatim from the served payload:
  - **jbe/dbi**: base width (MBR) and bar count, jump size (MBR), the trigger slot, flatline/
    ascending-base flags, and the ladder-step ratio when a second firing exists.
  - **cup_handle**: cup bar count and depth (MBR), handle retrace fraction and duration fraction,
    the trigger slot, optimal/desirable-duration flags, and the three RVOL medians (cup middle
    third, cup outer thirds, handle).
  - The already-shipped opening-range-break line, forward-measurement table, invalidation-breach
    note, and baseline-pool note are all UNCHANGED and now render behind their own `setup_id`
    check (or unconditionally, where they were always setup-agnostic).

## Files Changed

- `apps/frontend/lib/types.ts` -- `DeskPlaybookGeometry` gains the JBE/DBI and cup-and-handle
  fields as OPTIONAL properties (the shape now genuinely varies by `setup_id`; the opening-range
  fields also became optional for the same reason). `slots_to_break` is the one field every setup
  serves and stays required.
- `apps/frontend/app/desk/page.tsx` -- `playbookSetupLabel` (three new labels);
  `PlaybookSignalDetail` (three new conditional geometry-line branches, `data-testid`s
  `desk-playbook-signal-continuation-geometry` and `desk-playbook-signal-cup-handle-geometry`).

## New user-facing capability

On the same Playbook Signals table (session-date input + Run Playbook trigger/poll/cancel, all
unchanged), the operator now sees three additional setup types fire alongside opening-range
breaks, each with its own geometry disclosure line in the expandable signal-detail panel. No new
user action.

## Tests Run

Command: `cd apps/frontend && npx tsc --noEmit && npm run build`
Result: clean type-check; production build succeeds (6/6 static pages,
`/desk` bundle 27.5 kB / 139 kB first load).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_desk_ui_guards.py -q`
Result: 34 passed (includes the extended `_PRICE_ARITHMETIC_FIELDS` guard + its new counter-test
proving every new geometry field is caught if ever combined with client-side arithmetic).

Service startup verified via `scripts/dev.sh` — frontend on :3301, `/desk` returns 200 both on
initial start and after a stop/restart cycle.

## Known Issues

- No real browser screenshot pass was taken by this agent — that is the browser-qa-agent's job.
  The three new render branches were verified against the ACTUAL served field shapes (via a direct
  backend probe script during development, not committed) and pass `tsc`/`next build` cleanly, but
  visual legibility on the fixture rig (TC-1/TC-2/TC-3 of J-04's acceptance) is unverified by this
  handoff.
- No new `data-testid` introduced by this iteration collides with any of the 20 stored
  `goal-session-desk` golden replay scripts or `J-10.json` (grepped by hand — the two new testids,
  `desk-playbook-signal-continuation-geometry` and `desk-playbook-signal-cup-handle-geometry`, are
  new strings not referenced anywhere else in the frontend or in `runs/goal-session-playbook/
  journey-scripts/`).
