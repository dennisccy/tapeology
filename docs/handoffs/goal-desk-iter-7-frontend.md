# goal-desk-iter-7 Frontend Handoff

**Phase:** goal-desk-iter-7
**Date:** 2026-07-26
**Agent:** developer
**Status:** complete

## What Was Built

No new page, panel, button, or nav change. The ONLY frontend edit this iteration is the F2
hover-honesty fix on the already-shipped `/desk` page — moving where the full-precision detail
some per-cell hover tooltips used to carry is now reachable from, without changing anything visible
at rest and without changing the row's click/navigation geometry.

### The regression (iter-6 audit finding F2)

Each `/desk` briefing row is a "stretched link": the `<tr>` is `position: relative`, and one
`<Link data-testid="desk-row-drill-in">` (or `desk-skip-row-drill-in` on a skipped row) is
`absolute inset-0` inside it — a single real `next/link` anchor that makes the whole row clickable,
landing on `/structure?symbol=<sym>&asof=<iso>`. That anchor paints ABOVE every cell in the row,
including the per-cell `title` attributes at `desk-row-distance`/`desk-row-score` (full-precision
`distance_bps`/`band_score`, displayed rounded to 2 decimals per audit F3) and each coverage badge's
own `title` ("window last requested: ..."). Once the anchor covers the whole row, a mouse hovering
over those cells never actually reaches their `title` — the browser only sees the anchor, so none of
that full-precision/freshness detail was reachable by hovering anywhere on the page.

### The fix

Rather than touch the anchor's own geometry (any of `href`, `absolute inset-0`, or `data-testid`
risks breaking J-05's already-passing whole-row click, which is exactly why that path was rejected
in the phase spec), the lost detail is now composed directly onto the anchor's OWN `title` — the one
element that is already reachable everywhere in the row:

- `deskRowDrillInTitle(row)` (new, `apps/frontend/app/desk/page.tsx`): returns
  `"distance <row.distance_bps> bps · score <row.band_score> · <timeframe> window last requested:
  <value|never> · ..."` — one line per coverage entry the row actually has (never a hardcoded
  timeframe list).
- `deskSkipDrillInTitle(skip)` (new): returns ONLY the coverage-freshness lines — a skipped member
  has no `distance_bps`/`band_score`, so the tooltip never fabricates one.
- Both are wired via `title={...}` on the existing anchors — no other JSX attribute on either anchor
  changed.

### What did NOT change

- The anchors' `href`, `className="absolute inset-0"`, and `data-testid` are byte-identical to
  iteration 6.
- The rounded 2-decimal cell DISPLAY (audit F3's own fix) is unchanged — `desk-row-distance`/
  `desk-row-score` still render `fmt(row.distance_bps)`/`fmt(row.band_score)`; their own (now
  unreachable) per-cell `title`s were left in place as harmless dead markup rather than removed,
  since removing them was explicitly not required and touching more than necessary risked scope
  creep on a fix whose whole point was minimal blast radius.
- No layout, spacing, color, or at-rest visual change anywhere on the page — the fix is invisible
  until a pointer actually hovers a row.
- Nav, routes, empty states, Run Screen/Top-up buttons, screen history — all untouched.

## Files Changed

- `apps/frontend/app/desk/page.tsx` — added `deskRowDrillInTitle`/`deskSkipDrillInTitle`; added
  `title={...}` to `desk-row-drill-in` and `desk-skip-row-drill-in`. That is the entire diff.

## Tests Run

- `cd apps/frontend && rm -rf .next && npm run build` — compiles successfully, TypeScript
  strict-mode typecheck passes with zero errors, `/desk` still registers as a static route
  alongside `/` and `/structure`, bundle size for `/desk` essentially unchanged (5.43 kB).
- Backend guard: `apps/backend/tests/test_desk_hover_tooltip_guard.py` (new, 3 tests, all passing)
  source-inspects `page.tsx` to prove the composite tooltip is actually built from
  `row.distance_bps`/`row.band_score`/`latest_window_end_utc` (ranked rows) and only
  `latest_window_end_utc` (skip rows) — see the dev handoff for detail.
- Backend guard: existing `apps/backend/tests/test_desk_ui_guards.py` and
  `apps/backend/tests/test_copy_discipline.py` re-run unmodified and still pass (5 + 30 tests) —
  the F2 fix did not introduce a second compute path or any copy-discipline violation.

## Known Issues

- **No browser screenshot was captured by me** confirming the composite tooltip is actually visible
  on hover (TC-8/TC-9/TC-10 in the phase spec). This iteration's frontend change is verified by
  (a) TypeScript build success, (b) the new source-introspection guard test proving the tooltip
  content is correctly composed, and (c) manual reasoning about the DOM (the anchor is the topmost
  element at every point in the row, so its `title` is reachable everywhere) — but an actual
  hover-and-screenshot pass is the browser-qa-agent's job this iteration (J-07's regression walk),
  not mine. If that pass finds the tooltip does not render as expected in a real browser, that is
  the next thing to investigate.
- The per-cell `title`s at `desk-row-distance`/`desk-row-score` and each coverage badge remain in
  the markup as unreachable dead code (deliberately left, per the phase spec's own "developer's
  call" on this point) — a future cleanup could remove them, but doing so this iteration would have
  been an unrequested extra edit to a page whose F2 fix was chosen specifically to minimize blast
  radius.
