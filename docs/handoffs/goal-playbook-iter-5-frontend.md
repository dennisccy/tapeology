# goal-playbook-iter-5 Frontend Handoff

**Phase:** goal-playbook-iter-5
**Date:** 2026-08-11
**Agent:** developer
**Status:** complete

## What Was Built

- **No new section, no new route.** The already-shipped `/desk` Playbook Signals section (from
  J-03) now renders a fifth setup type when it fires on a recorded session: capitulation entry
  after a vertical decline reverses.
- `playbookSetupLabel` (`apps/frontend/app/desk/page.tsx`) gains one label: `"capitulation"` ->
  "Capitulation" -- rendered in the same chip (`CHIP_CLASS`) every other shipped setup uses.
- `PlaybookSignalDetail` (the expandable per-signal detail panel) gains a `capitulation` geometry
  branch, rendered verbatim from the served payload: `decline_mbr` (the vertical decline's
  magnitude in MBR units), `decline_bars` (how many bars the decline leg spanned, including any
  re-anchoring), `climax_rvol` (the possibly-re-anchored climax bar's own RVOL), and
  `bars_from_climax_to_trigger` (how many bars after the climax the first-strength reversal
  fired) -- new `data-testid="desk-playbook-signal-capitulation-geometry"`, checked against every
  stored golden replay script (this session's own J-01/J-02/J-03/J-10 and all 20 `goal-session-desk`
  scripts) with zero collisions.
- The `euphoria_recent`/`capitulation_recent` decoration chips (already wired since a prior
  iteration, at the `PlaybookSignalDetail` disclosures line) render for the FIRST time with real
  firing data this iteration -- no code change was needed there, only a real marker/signal pair to
  prove them.
- The two `/desk` copy spots widened to name every shipped setup family: the empty-state sentence
  ("Run Playbook detects and measures the opening-range-break, jump-base-explosion,
  drop-base-implosion, cup-and-handle, and capitulation families on...") and the populated-section
  blurb ("The book's opening-range-break, jump-base-explosion, drop-base-implosion, cup-and-handle,
  and capitulation signals, detected on...") -- closing the OPEN minor anti-goal violation carried
  from iter-4 (this same widening lands on the backend's `PLAYBOOK_REGISTER`, pinned exactly by a
  new backend test).

## Files Changed

- `apps/frontend/lib/types.ts` -- `DeskPlaybookGeometry` gains four OPTIONAL capitulation-only
  fields (`decline_mbr`, `decline_bars`, `climax_rvol`, `bars_from_climax_to_trigger`).
- `apps/frontend/app/desk/page.tsx` -- `playbookSetupLabel` (one new label); `PlaybookSignalDetail`
  (one new conditional geometry-line branch); the empty-state and populated-section copy strings.

## New user-facing capability

On the same Playbook Signals table (session-date input + Run Playbook trigger/poll/cancel, all
unchanged), the operator now sees a fifth setup type -- capitulation -- alongside opening-range
breaks, JBE, DBI, and cup-and-handle, each with its own geometry disclosure line in the expandable
signal-detail panel. For the first time across ANY setup type, a signal row can also carry a live
"euphoria recent" / "capitulation recent" decoration note (rendered in the disclosures line,
already-shipped markup, now proven with real data). No new user action.

## Tests Run

Command: `cd apps/frontend && npx tsc --noEmit`
Result: clean type-check, zero errors.

Command: `cd apps/frontend && rm -rf .next && npm run build`
Result: clean production build, 6/6 static pages, `/desk` bundle 27.7 kB / 139 kB first load
(T-9 discipline: `.next` removed and rebuilt before this verification pass).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_desk_ui_guards.py`
Result: all guard tests pass, including the extended `_PRICE_ARITHMETIC_FIELDS` guard covering
`geometry.decline_mbr`/`climax_rvol`/`bars_from_climax_to_trigger` plus its new counter-test.

Service startup verified via `scripts/dev.sh` -- frontend on `:3301`, `/desk` returns 200 on
initial start and after a stop/restart cycle (see the dev handoff for the full startup log).

## Known Issues

- No real browser screenshot pass was taken by this agent -- that is the browser-qa-agent's job.
  The new capitulation branch and the (now-real) decoration chips were verified against the ACTUAL
  served field shapes via backend `compute_playbook` fixtures during development and pass
  `tsc`/`next build` cleanly, but visual legibility on the fixture rig (TC-1/TC-2/TC-3) and the
  carried DBI screenshot re-take (TC-18, from iter-4) are unverified by this handoff -- both need a
  T-9 clean-rebuilt real browser pass in the same session.
- No new `data-testid`/heading string introduced this iteration collides with any stored golden
  replay script (grepped explicitly, zero hits) -- see the dev handoff for the exact check.
