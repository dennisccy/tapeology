# Iteration 8 — Coherence Audit

**Iteration:** goal-tradable_wall-iter-8
**Date:** 2026-07-15
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Scope of this iteration

Two files in the diff (`git diff 2ddac049...`), both matching the iter spec's declared scope exactly
— no more, no less:

- `apps/frontend/components/PriceChart.tsx` (+16/-8) — Cleanup A (iter-7 audit finding F1): the
  tradable-band fetch effect (era-5B J-06 confluence overlay) now early-returns and stays in
  `phase: "loading"` while `history?.epoch_anchor == null`, instead of falling back to
  `new Date().toISOString()` (browser wall-clock). Effect dependency array changed from
  `[ticker, history?.epoch_anchor]`-adjacent to explicitly `[ticker, history?.epoch_anchor]`
  (unchanged deps, just the guard moved inside).
- `apps/backend/tests/test_price_chart_confluence.py` (docstring + 2 assertion blocks) — Cleanup
  B / T1: realigns the module docstring and
  `test_tradability_as_of_uses_the_watched_sessions_own_anchor_with_no_client_side_session_math`'s
  assertions to the new deferred-fetch behavior (asserts no `new Date().toISOString()` anywhere in
  source, asserts the `epoch_anchor == null` guard exists, asserts `phase: "loading"` appears ≥2
  times). Test-only — not a served value, not a UI surface.

No backend production or frozen file appears in the diff (`levels.py`, `tradability.py`, `config.py`,
`strategies.py`, `backtests.py`, `engine/`, `adapters/`, `bars.py`, `datasets.py` — none touched),
consistent with the iter spec's "No production backend change" / frozen-file exclusion list. The
data-driven Case Studies drill-in and Edge Report content described in the ui-surface-map come from
the operator's out-of-band recorded datasets flowing through pre-existing, unmodified read paths —
zero code diff for those two surfaces, so nothing to audit there beyond confirming (below) that no new
fetch path was introduced.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Tradable level map / bands (blueprint row: `tradability.py` → `GET /research/tradability?symbol=&as_of=`) | OK | Call site unchanged: `fetchTradability(ticker, asOf)` at `apps/frontend/components/PriceChart.tsx:217`, which still resolves to `GET /research/tradability?symbol=&as_of=` in `apps/frontend/lib/api.ts:1054-1071` (byte-identical to iter-7, not in this diff). The only change is (a) *when* the fetch fires — gated behind `if (history?.epoch_anchor == null) { …; return; }` (`PriceChart.tsx:207-213`) instead of firing unconditionally, and (b) the `asOf` expression itself, now `new Date(history.epoch_anchor * 1000).toISOString()` (`PriceChart.tsx:216`) with the `new Date().toISOString()` wall-clock branch deleted. `epoch_anchor` is a field of `history`, which is fetched by the pre-existing `/tape/{ticker}/history` poll (unchanged, outside this diff) — not a new fetch. Converting an already-fetched epoch-seconds field to an ISO string is the same pure unit conversion this file already applies to candle timestamps (`toClock`); it computes no part of the tradable-band value itself (side/price_low/price_high/class/quality_score stay server-computed, read verbatim at the unchanged render site below the diff). This is a re-format/timing fix per skill Part A.3, not a duplicate computation and not a non-canonical source. |
| Tape five-state timeline / `epoch_anchor` (blueprint row: frozen `TapeEngine` → `GET /tape/{ticker}/history`) | OK — untouched | `history` and `history?.epoch_anchor` are read, never computed, at `PriceChart.tsx:207,216,228`. No new fetch, no client-side "which session" arithmetic added — the deleted branch removed a wall-clock fallback, it did not add session-math; confirmed by the test's own `banned_session_math` list (`test_price_chart_confluence.py`, unchanged list content) still asserting no `getPreviousTradingDay`-style helpers exist. |

No new displayed value or entity is introduced by this iteration (iter spec's own "Data-contract
additions: None" — confirmed against the diff: no new UI text, no new field read, no new endpoint
call). No duplicate computation, no non-canonical source.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Cockpit band overlay / confluence chip fetch timing (`/`) | OK | No route, page, nav, sidebar, or router file appears in the diff (only `PriceChart.tsx`, a component, and a backend test file). The change is confined to the existing effect inside the already-registered canonical home: `blueprint.md:37` — "J-06 Cockpit confluence (band overlay + descriptive chip) → `/` → `PriceChart` (sim/historical only) → Cockpit." `/` is the nav's first top-level entry (`blueprint.md:21`), 0/1-click reachable. No parallel shell, no duplicate home, no new surface — confirmed independently by `reports/phase-goal-tradable_wall-iter-8-ui-surface-map.md`: "New pages/routes: 0", "Navigation changes: no". |

Nav stays frozen for Era 5B as required (Cockpit · Journal · Studies · Performance · Structure,
unchanged) — no top-level entry added or removed, matching the iter spec's own "Blueprint
conformance: No new surfaces... No blueprint nav-skeleton change."

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The deferred-fetch guard sets `phase: "loading"` (not `"idle"`) whenever `history?.epoch_anchor`
  is unresolved, which is a functional/UX behavior (does the loading state ever get stuck) rather
  than a coherence concern — no duplicate value, no orphaned surface. That behavior is browser-QA's
  domain (per the ui-surface-map's test guidance for the `/` cockpit row), not this gate's; nothing
  to flag here.
- No new-but-unregistered value appeared this iteration, so there is nothing for the decomposer to
  add to the Data Contract next iteration.
