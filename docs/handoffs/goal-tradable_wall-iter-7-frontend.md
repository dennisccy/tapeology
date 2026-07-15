# goal-tradable_wall-iter-7 Frontend Handoff

**Phase:** goal-tradable_wall-iter-7
**Date:** 2026-07-15
**Agent:** developer
**Status:** complete

## What Was Built

The cockpit `PriceChart` (the `/` page's price chart, shown for Simulated + Historical modes only —
Live stays hidden, unchanged) gains two additive surfaces layered on top of its existing candles +
tape-state markers + thesis geometry: a **tradable-band overlay** and a **descriptive confluence
chip**. No new page, no new route, no nav change — the tradable wall (previously visible only on
`/structure`, iter-6) is now also visible where trades are actually watched.

- **Band overlay.** One solid price line per band edge (rose = resistance, emerald = support —
  the same up/down palette the candle series itself uses), title built from the served
  `side`/`class`/`quality_score`/`round_number`. Bands come from `GET /research/tradability`, fetched
  for the watched symbol. Solid lines are visually distinct from this component's pre-existing
  DASHED thesis price-lines (the same solid-vs-dashed convention iter-6 established on `/structure`
  between bands and raw levels).
- **Confluence chip.** A small neutral slate "factual stamp" banner (NOT the amber treatment this
  app reserves for degraded/empty/truncated states — a confluence chip is a positive descriptive
  signal) that appears only when the last traded price is inside a band AND the current tape state
  matches that band's side in the served `structure_tape_map` state mapping. Example copy: "Inside
  R-band 300.05–300.17 (class A) · tape: Ask Absorption (rejection) · measured history: edge
  report." No imperative, no prediction — verified clean by the existing copy-discipline lint.
- **Honest "no tradable map" state.** A SIM ticker (or any symbol with no recorded bar series) shows
  the chart + tape markers exactly as before, plus a small "No tradable map for {ticker}." hint below
  the chart — never a fabricated band, never a chip. Visually confirmed in a real browser (see the
  dev handoff's Live Verification section) for `SIM-BUYER`.
- **Live mode: byte-identical.** The pre-existing `(mode === "sim" || mode === "historical")` render
  gate in `page.tsx` is completely untouched — confirmed in a real browser that watching AAPL in Live
  mode shows no "Price Chart" section at all (the honest "Market is closed" panel rendered instead,
  since the real market happened to be closed at test time).

## Files Changed

- `apps/frontend/components/PriceChart.tsx` -- the whole feature (+204/-4 lines). New required prop
  `tapeState: string | null`; two new fetch effects (tradable bands, keyed on
  `[ticker, history?.epoch_anchor]`; the strategy registry, fetched once on mount); one new drawing
  effect (band price lines, keyed on `[tradabilityState, history]`, mirroring the pre-existing thesis
  geometry effect's own self-healing dependency pattern); derived values for the confluence
  match (`lastPrice`, `matchedBand`, `direction`, `matchKind`, `confluence`, `tradabilityEmpty`); new
  JSX below the existing chart canvas for the chip and the empty hint.
- `apps/frontend/app/page.tsx` -- one additive line passing `tapeState={snapshot?.tape_state ??
  null}` into the existing `<PriceChart>` call; a short comment added to the pre-existing block
  comment above it. The render-gate condition itself is unchanged.
- `apps/frontend/lib/types.ts` -- new `StrategyEntries` interface (additive/widening); `Strategy.
  entries` narrowed-to-widened from `{ rule: string }` to `StrategyEntries` (existing narrower `v1`
  shape still satisfies it — no existing caller breaks).
- `apps/frontend/lib/api.ts` -- **no change.** `fetchTradability` (iter-5/6) and `fetchStrategies`
  (era-4) already existed with the exact signatures needed; confirmed during implementation rather
  than adding a duplicate, per the plan's own note.

## Visual / Design Notes

- No new visual effects — reuses this app's dark instrument-panel language throughout: the `Panel`/
  `EmptyHint` components already imported in this file, `FeedBasisBadge.tsx`'s neutral slate chip
  family (`rounded bg-slate-800 px-2 py-1 text-xs text-slate-300`) as the confluence chip's closest
  visual precedent, and `StructureChart.tsx`'s solid-band-line-by-side-color pattern reused
  byte-for-byte.
- Band overlay lines are SOLID (`lineStyle: 0`), matching iter-6's `/structure` convention, and
  visually distinct from this component's own pre-existing DASHED thesis price-lines (`lineStyle:
  2`) — so a viewer can tell "declared thesis reference" from "tradable-map band" at a glance even
  though both now share the same chart canvas.
- The chip and the empty hint sit below the chart canvas (inside the existing "Price Chart —
  Tape-State Markers" panel), never overlapping or obscuring the candles/markers above.
- Every new element is additive and non-blocking: while the bands fetch is idle/loading/failed, the
  chart and tape markers render exactly as they did before this iteration (verified — this is the
  same behavior across every state, confirmed live for the SIM/empty-state case and structurally
  guaranteed by the effect's own clear-then-redraw-only-on-resolved-data logic for the loading/error
  cases).

## States Covered

- **Band overlay:** not yet fetched / fetch failed -> no lines drawn (chart/markers unaffected,
  matches the "additive, non-blocking" DoD requirement); populated -> one solid line per band edge;
  empty (SIM/no-bar-series) -> no lines, explicit "no tradable map" hint instead.
- **Confluence chip:** present only at the in-band + mapped-state conjunction; absent when price is
  outside every band, or the tape state is `unclear`, or the tape state is a meaningful state that
  simply isn't the mapped one for that band's side.
- **Live mode:** the whole component (chart, overlay, chip, empty hint) stays fully unmounted —
  verified live, zero DOM presence.

## Tests

Same situation as every prior iteration: no frontend test runner exists in this repo
(`apps/frontend/package.json` has no `test` script, no `.test.ts(x)` files anywhere). Frontend
correctness was verified via:

1. `npx tsc --noEmit -p tsconfig.json` -- exit 0, zero type errors across all three changed files
   (re-confirmed after the `as_of` fix described in the dev handoff).
2. Nine new Python source-inspection tests in `apps/backend/tests/test_price_chart_confluence.py`
   (this repo's established precedent for testing frontend logic keylessly) — see the dev handoff
   for the full list. All 9 pass; they failed with clear, specific messages before the implementation
   existed (TDD confirmed).
3. `test_copy_discipline.py::test_lint_frontend_source_literals_are_clean` (part of the 31/31-passing
   copy-discipline suite) walks every `.tsx`/`.ts` file under `apps/frontend/components` and
   `apps/frontend/app` — including the new chip copy — for imperative/predictive/certainty-claim
   language. Clean.
4. **Extensive live browser verification** (Chrome MCP, console logging enabled throughout) — well
   beyond a typical smoke check, because this iteration's own testing is what surfaced and let me fix
   a real `as_of`-source bug (documented in detail in the dev handoff's "Deviation from Plan"
   section):
   - SIM-BUYER (Simulated mode): chart + markers render; "No tradable map for SIM-BUYER." renders
     correctly; zero console errors.
   - AAPL (Live mode): real market-closed panel rendered; the Price Chart section (and therefore the
     overlay/chip) is completely absent from the DOM; zero console errors.
   - AAPL (Historical mode, the credentialed pinned 2026-06-22 09:30-16:00 ET window, real Alpaca
     data, `feed: sip (consolidated)`): band overlay lines render correctly, including a `round`-
     flagged ~300 resistance band matching goal.md's own pinned rejection-cluster description; zero
     console errors on a fresh page load (one Fast-Refresh-only warning appeared mid-development
     during a hot-code-edit and was confirmed to be a dev-server artifact, not present on a clean
     reload).

**Not personally observed this session** (the credentialed, operator-gated portion of J-06's DoD,
explicitly separated from the dev-time "keyless core" by the plan): the confluence chip actually
firing live during the replay. I watched price approach the relevant band but did not happen to
observe the exact moment the tape state also matched the mapped confirming state within my
verification window. This is the named next step for browser-qa-agent / the credentialed operator
pass (potentially with a longer observation window or a targeted replay start time nearer the pinned
touch).

## Known Issues

See the dev handoff's "Known Issues" and "Deviation from Plan" sections (same list; all three items
there are frontend-relevant).
