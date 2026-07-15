# Phase goal-tradable_wall-iter-7 — UI Surface Map

**Phase:** goal-tradable_wall-iter-7
**Date:** 2026-07-15
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-------------|-------------|-------------|
| `/` (Cockpit) | PriceChart — tradable-band overlay (chart price lines) | New feature | Surfaces J-01's tradable bands (previously `/structure`-only) directly on the cockpit chart the operator is actually watching | In Historical mode, watch `AAPL` for the 2026-06-22 09:30–16:00 ET session (the project's pinned credentialed test window). Confirm the chart canvas shows solid (not dashed) horizontal price lines near the ~300 level, rose-colored (resistance), each showing an axis label of the form "R class {A/B/C} · score {N}[· round]" on hover/at the line. Confirm these lines are visually distinct (solid) from the pre-existing DASHED thesis price-lines already drawn on the same chart. |
| `/` (Cockpit) | PriceChart — band overlay `as_of` basis (correctness-critical fix made mid-build) | Changed behavior (bug found + fixed before handoff) | The overlay must resolve to the REPLAYED session's own prior close, not today's date, or the bands drawn during a Historical replay are meaningless relative to the price action shown | With the same `AAPL` 2026-06-22 Historical watch above, confirm the drawn bands reflect the 2026-06-18 prior-session basis specifically: a "R class A · score 153 · round" band near 300.17 and a second "R class A · score 77 · round" band nearby (the developer's own pinned verification numbers) — NOT bands computed from today's date. Cross-check via the browser Network tab: the `GET /research/tradability` request's `as_of` query parameter should correspond to the replayed session's own time (sourced from `history.epoch_anchor`), not a `new Date()` value at click time. |
| `/` (Cockpit) | PriceChart — confluence chip (`data-testid="confluence-chip"`) | New component | Descriptive display-conjunction of served band × served last price × served tape state × served `structure_tape_map` mapping, citing the edge report as measured history | Continue the `AAPL` 2026-06-22 replay (or any live/credentialed session) until the last traded price sits inside a drawn band AND the tape-state indicator elsewhere in the cockpit reads a state equal to that band's mapped rejection or breakthrough state (`bid_absorption`/`ask_absorption` for rejection, `buyer_control`/`seller_control` for breakthrough, depending on the band's side). Confirm a slate-gray chip (`data-testid="confluence-chip"`) appears below the chart reading "Inside {R\|S}-band {low}–{high} (class {X}) · tape: {State Label} ({rejection\|breakthrough}) · measured history: edge report." Then confirm the chip disappears once price exits the band or the tape state changes to `unclear` / an unmapped state. |
| `/` (Cockpit) | PriceChart — "no tradable map" empty hint (`data-testid="no-tradable-map"`) | New component (honest empty state) | SIM-\*/no-bar-series symbols must never show a fabricated band or a chip | Watch `SIM-BUYER` in Simulated mode. Confirm the chart and tape-state markers render normally, zero band lines are drawn, no confluence chip appears anywhere, and a hint (`data-testid="no-tradable-map"`) reading exactly "No tradable map for SIM-BUYER." appears below the chart. |
| `/` (Cockpit) | PriceChart props / `page.tsx` wiring (new `tapeState` prop) + Live-mode gate | Changed behavior (internal wiring; the gate condition itself is untouched) | `page.tsx` now threads the WS snapshot's own `tape_state` field into `PriceChart` so the chip has a current-state input; the pre-existing `(mode === "sim" \|\| mode === "historical")` gate must stay byte-identical so Live mode is unaffected | Watch a real symbol (e.g. `AAPL`) in Live mode. Confirm the entire "Price Chart — Tape-State Markers" panel is absent from the page — search the DOM for `data-testid="confluence-chip"` and `data-testid="no-tradable-map"` and confirm zero matches, identical to pre-iteration behavior. (If the real market happens to be closed at test time, confirm instead that the honest "Market is closed" panel renders in its place, and still no Price Chart panel appears.) |
| `/` (Cockpit) | `lib/types.ts` — new `StrategyEntries` interface, widened `Strategy.entries` | Type widening (supporting change, no visual surface of its own) | Lets `PriceChart.tsx` type-check reading `rejection_states`/`breakthrough_states` off the fetched `GET /research/strategies` payload; purely additive so `v1`'s narrower `{ rule }` shape still satisfies the widened type | Run `cd apps/frontend && npx tsc --noEmit -p tsconfig.json` and confirm exit code 0. Separately, open `/structure` (whose Registry section also reads `Strategy.entries.rule` for `v1`) and confirm the `v1` strategy row still renders identically to before — confirming the widened type didn't break the pre-existing narrower caller. |
| `/structure` | Tradable Map (unchanged — regression smoke check) | No change (verifies scope discipline) | This iteration touches no file under `apps/frontend/app/structure/`; J-05's Tradable Map must keep defaulting exactly as iter-6 left it | Navigate to `/structure`, submit the Load form for `AAPL` as-of `2026-06-22`, and confirm the Tradable Map section still defaults to the same ≤10-band table + `basis_as_of` stamp it showed at the end of iter-6 (no visual regression), and confirm the left-hand nav still carries no new entry. |

<!-- Change Type options used above: New feature | New component | New component (honest empty state) | Changed behavior | Type widening (supporting change) | No change (regression smoke check) -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_price_chart_confluence.py` — a new file of 9 keyless Python
  source-inspection tests that parse/grep `PriceChart.tsx`'s and `page.tsx`'s own source text (this
  repo's established precedent for testing frontend logic without a frontend test runner). They
  verify: no hardcoded tape-state literal in the chip's matching branch; the rejection/breakthrough
  mapping is read off the fetched `structure_tape_map` entry rather than restated as a local object;
  the correct registry entry is selected; the bands-fetch effect's dependency array is exactly
  `[ticker, history?.epoch_anchor]` (not polled); `as_of` sources from `history.epoch_anchor` with a
  wall-clock fallback and no local "which session" date-math; the strategies-fetch effect runs once
  (`[]` deps); the band overlay reads only served fields; the empty state exists and reuses
  `EmptyHint`; and `page.tsx` threads `tapeState` while preserving the live-mode gate. This is a test
  file, not product code — it has no UI surface of its own, though it guards the correctness of every
  cockpit surface listed above. Run via
  `cd apps/backend && .venv/bin/python -m pytest tests/test_price_chart_confluence.py -q` and confirm
  9 passed.

---

## Summary

- **Frontend surfaces changed:** 1 route (`/`) — the existing "Price Chart — Tape-State Markers"
  panel gains 3 new display elements (band overlay, confluence chip, "no tradable map" empty hint);
  1 supporting type file widened (non-visual).
- **New pages/routes:** 0
- **Modified components:** 2 — `apps/frontend/components/PriceChart.tsx` (substantive, +204/-4
  lines, verified via `git diff --stat`) and `apps/frontend/app/page.tsx` (one additive prop-thread
  line + a comment update, part of a combined 3-file, +229/-4-line diff) — plus 1 supporting library
  file (`apps/frontend/lib/types.ts`, additive interface widening, non-visual on its own).
- **Navigation changes:** no (nav is frozen for Era 5B; no new page, no new nav entry)
- **Backend-only changes:** 1 (`apps/backend/tests/test_price_chart_confluence.py` — new test file,
  no product code; `apps/backend/app/` itself carries zero diff this iteration)
