# goal-clean_slate-iter-5 Frontend Handoff

**Phase:** goal-clean_slate-iter-5
**Date:** 2026-07-24
**Agent:** developer
**Status:** complete

## What Was Built

Exactly one UI-visible capability change: the Case Studies panel on `/structure` becomes visible
and clickable again. Everything else this iteration is re-verification of the already-shipped,
two-page (Cockpit + Structure) product — no other frontend file changed.

- **Case Studies section un-hidden**: `SHOW_CASE_STUDIES` (`apps/frontend/app/structure/page.tsx:335`)
  flipped from `false` to `true`. The section (`<section aria-label="Case studies">`, `~line
  2339-2432`) reoccupies its pre-existing position between the Levels & Zones/raw-toggle area and
  the Edge Report section — no new component, no restyle, no new page. Its filter inputs (symbol,
  reaction), its four load/error/empty/no-match sub-states
  (`case-studies-loading`/`-unavailable`/`-empty`/`-no-match`), its populated table, and its
  row-click-to-drill-in handler were all already built and wired in era 5B/5C; this iteration only
  changed the render gate from off to on. No new state, no new handler, no new fetch call.
- **Framing paragraph restored**: the `data-testid="structure-framing"` paragraph now reads (in
  full): "Tradable Map is the default view, read verbatim from GET /research/tradability; toggle
  'Show raw levels' for the underlying S/R levels and confluence zones (off by default). **Case
  Studies lists every band-touch event with its reaction, forward returns, and — once recorded —
  its tape timeline;** Edge Report compares v1, structure_tape, and structure_tape_map over recorded
  windows, register included. Fetching bars below (Yahoo Finance, with Alpaca for history beyond
  Yahoo's limits) is this page's one explicit write action — everything else, including the
  strategy registry/champion and the structure_tape-vs-v1 comparison, is read-only. Every value on
  this page is read verbatim from its canonical endpoint — nothing here is recomputed in the
  browser." (bolded portion is the newly reinstated sentence, matching commit `e60f6a7`'s originally
  dropped text verbatim).
- **Both charts untouched this iteration**: `StructureChart.tsx` — zero diff, confirmed via
  `git diff` against the whole session's baseline. `PriceChart.tsx` — zero further edits (its one
  sanctioned thesis-geometry-overlay removal already landed in J-02/iter-2; nothing about it
  changed here).
- **No nav change**: `app/meta.py`'s `UI_ROUTES` (the single source the nav renders from) is
  unchanged — still exactly `/` (Cockpit) and `/structure` (Structure), 2 rows.

## Files Changed

- `apps/frontend/app/structure/page.tsx` -- the `SHOW_CASE_STUDIES` flip (line 335) + the one
  reinstated sentence in the framing paragraph (`~line 2031-2039`). **The only frontend file
  touched this iteration.**

## UI Verification Performed (non-Chrome smoke checks — see Known Issues for what's deferred)

- Clean rebuild: `rm -rf apps/frontend/.next`; `npm run build` compiled successfully with 0 type
  errors; route table shows exactly `/`, `/_not-found`, `/structure`.
- `.next` cleaned again post-build; both backend + frontend started fresh via `scripts/dev.sh`
  **twice** (stop, then start again) to confirm no port conflicts — both boots clean on ports
  8301/3301.
- `curl` checks on both boots: `/` → 200; `/structure` → 200; `/journal`, `/studies`,
  `/performance` → 404 (the app's own not-found rendering); `GET /meta/ui-routes` → the 2 kept
  routes verbatim.
- Fetched `/structure`'s served HTML directly: contains the literal string "Case Studies" (the
  section heading now renders) and the literal reinstated sentence "Case Studies lists every
  band-touch event..."; contains no "journal" or "performance" text anywhere on the page.
- Both dev processes stopped cleanly before finishing this task (no server left running).

## Known Issues / Deferred Work

**The full Chrome-driven browser walk with screenshot evidence is NOT part of this handoff** —
that is browser-qa-agent's stage in the pipeline (developer → reviewer → ui-impact-analyst →
ui-test-designer → browser-qa-agent → qa → …), running after this dev+review cycle. Specifically
still needing real-browser, screenshot-evidenced confirmation (per T-13 — no screenshot ⇒
`unknown`, never `passing`):

- TC-5–TC-8: sim cockpit (`SIM-BUYER` → "Buyer Control", PriceChart candles render, timeframe
  switch re-renders at a new bar width, live ticks move the rightmost bar with the band overlay
  staying anchored, "Stop" → "No ticker watched").
- TC-9: `/structure` Load of AAPL as-of `2026-06-22T21:00:00Z` renders the StructureChart with the
  ~300–302.4 wall band overlay visible.
- TC-10: clicking a Case Studies row (now un-hidden) opens the drill-in view (tape timeline or
  honest "not recorded").
- TC-11: the Edge Report panel's current honest state (populated cells or "Edge report not computed
  yet." + Compute button).

This developer's own verification (pytest suite, guard-suite isolation, grep/404/MCP sweeps, the
I-9 byte-comparison recapture, the diff-vs-inventory cross-check, the clean-rebuild + curl smoke
checks) covers everything backend-verifiable plus the one code change's compile-correctness and
basic page-reachability — it does not substitute for the browser-qa-agent's screenshot evidence,
and is not represented as such.
