# goal-tradable_wall-iter-7 Execution Plan

Session: `tradable_wall` (Era 5B "The Tradable Wall"). Target journey: **J-06 — Cockpit confluence
(band overlay + descriptive chip)**. Pure-frontend iteration: no backend endpoint, config, or
computation changes; `config_fingerprint` stays `4d665603569b9dbf`. Required-still-passing (full
regression): J-01, J-02, J-04, J-05, J-07.

This plan aligns with `docs/goal.md` Key Capability 8 ("Cockpit confluence") and the session
blueprint (`runs/goal-session-tradable_wall/state/blueprint.md`), which already registers J-06's
home as `/` → `PriceChart` (sim/historical only) — no blueprint edit needed. No drift from the
phase spec detected; it is a faithful, already-well-scoped decomposition of the goal.

## What to Build

- **Tradable-band overlay on the cockpit `PriceChart`** (sim/historical modes only; live stays
  hidden, unchanged): fetch the watched symbol's bands from `GET /research/tradability` and draw
  one solid price line per band edge, colored by side (rose/resistance, emerald/support) — the
  verbatim precedent already shipped in `StructureChart.tsx` L97-120.
- **Honest "no tradable map" empty state** for SIM-*/no-bar-series symbols (`no_bar_series_for_symbol`
  or an empty served `bands[]`) — chart + tape markers keep working; no fabricated band, no chip.
- **Descriptive confluence chip**: visible only when the latest served price is inside a band AND
  the current served tape state matches the config-owned rejection/breakthrough mapping (read from
  `GET /research/strategies`, `structure_tape_map` entry) for that band's side. Descriptive copy
  only, citing the edge report as measured history — no imperative/prediction language.
- **Zero client recomputation**: band ranges/class/score, the confirmation mapping, and the tape
  state are all read verbatim from their owning endpoints; the component only does a display
  conjunction (is-price-in-range? does-state-match-served-mapping?).
- **Live mode untouched**: the existing `mode === "sim" || mode === "historical"` gate in
  `app/page.tsx` (L248-249) already fully unmounts `PriceChart` in live mode — do not touch that
  condition; this alone satisfies "live mode byte-identical."

## Agents Required

- **developer: yes** -- implement the band overlay + confluence chip end-to-end per this plan
  (frontend-only diff), then write `docs/handoffs/goal-tradable_wall-iter-7-dev.md`.
- backend-data: no -- no endpoint, config, or computation changes. Every frozen backend file
  (`config.py`, `strategies.py`, `tradability.py`, `levels.py`, `backtests.py`, `edge_report.py`,
  `setups.py`, `datasets.py`, the engine, the adapters) must stay absent from
  `git diff --name-only -- apps/backend/` — this is an explicit, independently-verifiable DoD item.
- frontend-ux: yes -- see Files to Create/Modify below.

## Frontend Present
Frontend Present: yes

## Files to Create/Modify

- `apps/frontend/components/PriceChart.tsx` -- main change. Add:
  - Two new self-contained data effects (this component already self-fetches its own data via
    `fetchHistory`, so keep that pattern rather than pushing fetches up into `page.tsx`):
    1. Fetch `fetchTradability(ticker, new Date().toISOString())` once per `ticker` change (NOT
       polled — the morning-markup basis is date-bounded and does not change intraday, unlike the
       1s `/tape/.../history` poll). Passing the CURRENT time verbatim as `as_of` and trusting the
       backend's existing `_resolve_basis` (`tradability.py`) to resolve "the prior completed
       session's close" is how `/structure`'s own Load form already works — zero client date-math,
       satisfies the no-lookahead test requirement.
    2. Fetch `fetchStrategies()` once on mount (ticker-independent config/registry data — both
       functions already exist byte-identical in `lib/api.ts`, added in iter-5/iter-6; **no new
       `api.ts` function is needed**).
  - Draw the band overlay in the existing chart-effect family: one **solid** (`lineStyle: 0`)
    price line per band edge via `series.createPriceLine`, colored rose (`#fb7185`)/resistance vs
    emerald (`#34d399`)/support — reuse `StructureChart.tsx` L97-120 verbatim as the pattern
    (title built from the served `side`/`class`/`quality_score`/`round_number`, single-price band
    draws one line not two). Solid keeps it visually distinct from this component's own existing
    DASHED thesis price-lines (`lineStyle: 2`).
  - Confluence chip logic: `lastPrice` = the latest entry of the already-fetched `history.bars[]`
    `.close` (per spec: "latest `GET /tape/{ticker}/history` bar close"); find the served band (if
    any) with `price_low <= lastPrice <= price_high`; map that band's `side` to a direction
    (`resistance` → `"short"`, `support` → `"long"` — this is a structural side→direction mapping
    named explicitly in the phase spec's Notes, NOT a restatement of tape-state vocabulary, so it
    is fine to inline); look up the `structure_tape_map` entry in the fetched strategies list;
    compare `currentTapeState` against `entries.rejection_states[direction]` and
    `entries.breakthrough_states[direction]` — **only these served strings**, never a hardcoded
    `"bid_absorption"`/`"ask_absorption"`/`"buyer_control"`/`"seller_control"` literal used for the
    matching decision. (The pre-existing `MARKER_COLORS`/`STATE_LABELS` dicts in this file already
    hardcode those four state names for marker COLOR/LABEL cosmetics — that is unrelated, pre-
    existing, allowed precedent; do not conflate it with the confirmation-mapping rule, and reusing
    `STATE_LABELS` to render the chip's human-readable state word is fine.) If multiple bands match
    (edge case; clustering should keep same-side bands non-overlapping) use the first match in
    served order — do not rank/score bands client-side.
  - New required prop: `tapeState: string | null` (see `page.tsx` change below) — the current
    tape state. **Do not** derive "current state" by scanning `history.markers` for the latest
    timestamp: `markers[]` only records transitions INTO the four named states and a silent
    transition into `unclear` is never marked, so the last marker can go stale/wrong. Use the WS
    snapshot's own `tape_state` field instead — it is the SAME engine-owned value, already read
    verbatim elsewhere in the cockpit (`Cockpit.tsx` reads `snapshot.tape_state` today), and
    reading a served field verbatim (vs. deriving one via a sort/max over a list) is the safer
    choice under the coherence-auditor's "no client recomputation" rule.
  - Chip copy: descriptive, e.g. the spec's own example — `"Inside R-band 300.4–302.1 (class A) ·
    tape: ask_absorption · measured history: edge report"`. Cite "edge report" as a **textual
    pointer**, not a fetched number — see Assumptions below. Must pass the existing
    `test_lint_frontend_source_literals_are_clean` copy-discipline lint (no imperative/predictive/
    certainty words; see `apps/backend/tests/test_copy_discipline.py`'s `_IMPERATIVE_PATTERNS`/
    `_PREDICTION_PATTERNS`).
  - Visual treatment: a neutral slate "factual stamp" chip, NOT the amber treatment this app
    reserves for degraded/empty/truncated states (established convention across `/structure` and
    `FeedBasisBadge.tsx`) — a confluence chip is a positive descriptive signal, not a warning.
    `FeedBasisBadge.tsx`'s `rounded bg-slate-800 px-2 py-1 text-xs text-slate-300` chip is the
    closest existing precedent to reuse/extend.
  - Honest empty overlay state: reuse the existing `EmptyHint` pattern (already imported) for the
    "no tradable map" message when bands are empty / `no_bar_series_for_symbol` is true.
  - The bands fetch is additive/non-blocking: if it fails or is still loading, candles + tape
    markers must keep rendering exactly as today (overlay/chip are a pure addition, never a
    dependency the rest of the chart waits on).

- `apps/frontend/app/page.tsx` -- ONE additive change: pass `tapeState={snapshot?.tape_state ??
  null}` into the existing `<PriceChart ticker={ticker} thesis={snapshot?.thesis ?? null} />` call
  at L249. Do NOT touch the surrounding `(mode === "sim" || mode === "historical")` gate
  (L248-249) — that is what keeps live mode byte-identical.

- `apps/frontend/lib/types.ts` -- widen `Strategy.entries` (currently `{ rule: string }`,
  L1075-1083) additively so TypeScript compiles when reading the `structure_tape_map`/
  `structure_tape` grammar (`config.py` `strategy_definition`, L1513-1544):
  ```ts
  export interface StrategyEntries {
    rule: string;
    proximity_band_bps?: number;
    rejection_states?: Record<"long" | "short", string>;
    breakthrough_states?: Record<"long" | "short", string>;
    arm_cooldown_seconds?: number;
    concurrency?: string;
  }
  ```
  and change `Strategy.entries: { rule: string }` to `Strategy.entries: StrategyEntries`. Purely
  additive/widening — no existing field removed, `v1`'s narrower shape still satisfies it.

- `apps/frontend/lib/api.ts` -- **no change expected**: `fetchTradability` (iter-5/6) and
  `fetchStrategies` (era-4) already exist with the exact signatures needed. Confirm during
  implementation rather than adding a duplicate.

- **Component-level keyless tests** (this repo has no frontend test runner — no `test` script, no
  `.test.ts(x)` files anywhere per every prior iteration's handoff, and goal.md's Constraints bar
  "no new runtime dependency" — the established precedent across iters 5-6 for testing frontend
  logic keyless is a **Python source-inspection test** in `apps/backend/tests/`, e.g. extending
  `test_copy_discipline.py` or a new `test_price_chart_confluence.py`, mirroring iter-6's B3
  structural-guard pattern). Cover: (a) the confirmation decision reads `entries.rejection_states`/
  `entries.breakthrough_states` off the fetched payload and contains no hardcoded
  `bid_absorption`/`ask_absorption`/`buyer_control`/`seller_control` literal in the matching branch
  (source-grep guard, scoped to exclude the pre-existing `MARKER_COLORS`/`STATE_LABELS` dicts);
  (b) band lines render only from served `bands[]` fields; (c) the `as_of` passed to
  `fetchTradability` is the current time, not a client-computed "prior session" date (no local
  date-math for session resolution).

- `docs/handoffs/goal-tradable_wall-iter-7-dev.md` -- required dev handoff (DoD item).

## UI Evolution

- **New user-facing capability**: the operator now sees the watched symbol's tradable bands drawn
  directly on the cockpit price chart, and — at a confluence moment — a descriptive chip stating
  the condition (band side/range/class + current tape state) with a pointer to the edge report.
  The tradable wall (previously `/structure`-only, J-05) is now visible where trades are watched.
- **New information displayed**: band overlay lines (verbatim from `/research/tradability`); the
  confluence chip (a display conjunction of served band × served last price × served tape state ×
  served mapping + an edge-report citation). No newly computed value anywhere.
- **New user actions**: none. Purely a display addition — no new button/form/control, no change to
  the Watch flow or bar-size selector.
- **UI surface changes**: `PriceChart` (cockpit `/`) gains the band overlay, the confluence chip,
  and the SIM/no-bars honest "no tradable map" empty state. No other surface changes; `/structure`
  is untouched (J-05 already shipped it there).
- **Navigation changes**: none (nav is frozen for Era 5B; no new page, no new nav entry).

## Visual Requirements

- **Component patterns**: reuse `Panel`/`EmptyHint` (already imported in `PriceChart.tsx`); reuse
  `StructureChart.tsx`'s solid-price-line-by-side-color pattern for bands; reuse
  `FeedBasisBadge.tsx`'s neutral slate chip styling (`rounded bg-slate-800 px-2 py-1 text-xs
  text-slate-300`) as the confluence chip's visual family.
  Do not use the amber palette (this app reserves it for degraded/empty/truncated states).
- **Layout**: no new panel/page. Bands render inside the existing "Price Chart — Tape-State
  Markers" `Panel`, on the same canvas as candles/markers. The chip sits as a small inline
  banner/badge near the top or bottom of that same panel — must not obscure the chart canvas.
- **Key visual effects**: none new; dark instrument-panel/terminal-grade look preserved (no
  marketing gloss, per DESIGN SYSTEM). Solid band lines vs. this component's existing dashed
  thesis price-lines is the one deliberate visual distinction (mirrors iter-6's solid-vs-dashed
  choice on `/structure`).
- **States to handle**: bands not yet fetched / fetch failed → chart+markers unaffected, no
  overlay, no chip (never block on the bands fetch); populated bands → overlay lines; empty bands
  or `no_bar_series_for_symbol` → explicit "no tradable map" `EmptyHint`, never a fabricated band;
  chip present only at the in-band + mapped-state conjunction, absent otherwise (outside all bands,
  or state `unclear`/unmapped); live mode → entire component unmounted (unchanged, verified via the
  existing parent gate).

## Assumptions (interpretation calls — documented, not escalated)

1. **`as_of` for the cockpit's tradability fetch = current wall-clock time**, verbatim, letting the
   backend's existing `_resolve_basis` own "which prior session." Matches `/structure`'s own Load
   flow and the phase spec's morning-markup test wording ("assert the frontend passes an `as_of`
   that resolves to the prior completed session").
2. **Current tape state source = `snapshot.tape_state`** (WS-pushed, passed as a new `PriceChart`
   prop from `page.tsx`), not a derivation from `/tape/{ticker}/history`'s `markers[]`. Rationale:
   `markers[]` cannot represent a silent transition into `unclear`, so scanning it for "the last
   state" can be stale/wrong, and doing so is itself a client-side derivation the coherence-auditor
   could flag. `snapshot.tape_state` is the same engine-owned value read verbatim, with existing
   precedent (`Cockpit.tsx`).
3. **Edge-report citation is a static textual pointer** ("measured history: edge report"), not a
   live-fetched number. The band/side/class the chip shows has no resolved `reaction` yet (that is
   a future outcome), so there is no single edge-report cell to honestly cite live; fabricating one
   (e.g., picking an arbitrary reaction) would be worse than a plain pointer phrase. If a
   reviewer/auditor wants a stronger citation, the safest additive option is fetching
   `GET /research/edge-report` (client already exists) and citing something verbatim and unrelated
   to the unresolved reaction (e.g., whether ANY `structure_tape_map` cell for this band's
   class/side exists across reactions) — left to developer judgment, not required for J-06 to pass.
4. Band-overlay refetch is keyed on `ticker` change only (not polled) — the map is date-bounded and
   does not change intraday, unlike the 1s tape-history poll.

## Out of Scope (per phase spec — do not implement)

Any backend/endpoint/config change; any live-mode change; the credentialed AAPL 06-22 recording
itself (J-03's separate operator-gated deliverable — J-06 only renders whatever is already served,
honestly empty/absent if J-03 hasn't populated it); any `/structure` change; client-side
recomputation of band ranges/classes/scores/reactions/tape states/PnL/provenance; a new nav entry
or page; the iter-6 non-blocking Case-Studies-filter-doesn't-auto-clear-drill-in nuance (unrelated
surface).

## Key Test Scenarios

- **Browser QA (J-06, primary)**: sim or historical mode, real symbol with bars — band overlay
  lines visible on the cockpit chart; at a moment where price is inside a band AND tape state
  matches the served mapping, the chip appears with descriptive copy; chip is absent when price is
  outside every band or state is `unclear`/unmapped. Anchor acceptance on this **structural**
  condition (chip present/absent correctly, overlay present), not a specific numeric band score
  (iter-6 lesson — scores drift on the live store). If a screenshot comes back blank/double-exposed
  at deep scroll, fall back to DOM `innerText` capture (a legitimate pass, per the iter-6 lesson).
- **SIM ticker**: chart + tape markers render; explicit "no tradable map" empty state shown; no
  fabricated band; no chip.
- **Live mode**: `PriceChart` (and therefore the overlay/chip) stays fully hidden — byte-identical
  to before this iteration.
- **Smoke re-verify**: `/structure` Tradable Map still defaults correctly (J-05) and nav is
  unchanged.
- **Mapping-driven, not hardcoded**: changing the served `/research/strategies` mapping changes
  chip visibility; no tape-state confirmation vocabulary is hardcoded in the matching branch.
- **No-lookahead**: the cockpit's tradability request/render uses an `as_of` resolving to the prior
  completed session — no forming-bar/session data enters the overlay or chip.
- **Full regression**: full backend suite green (no test deleted/weakened); `config_fingerprint`
  stays `4d665603569b9dbf`; `git diff --name-only -- apps/backend/` is EMPTY (independently
  verifies the "no backend change" constraint); J-01/J-02/J-04/J-05/J-07 remain passing.
- **Copy discipline**: `test_lint_frontend_source_literals_are_clean` (part of
  `test_copy_discipline.py`) stays green with the new chip copy included — no imperative/
  predictive/certainty language.
- **Type safety**: `npx tsc --noEmit -p tsconfig.json` exits 0.
- **Operator-gated (honest-blocked)**: the credentialed AAPL 2026-06-22 replay screenshot needs
  Alpaca creds configured; if absent, report it honestly as blocked/deferred — never simulate it or
  accept a handoff narration in place of a real screenshot + persisted artifact (iter-3 lesson).
  This does not block J-06's keyless core (overlay + chip logic + SIM empty state + live-unchanged)
  from passing.

**Environment note for the developer/QA**: this pipeline run isolates temp files — export
`TMPDIR`/`TMP`/`TEMP` to
`/tmp/iad.goal-tradable_wall-iter-7.2865738` before running the backend test suite or any command
that writes temp files.
