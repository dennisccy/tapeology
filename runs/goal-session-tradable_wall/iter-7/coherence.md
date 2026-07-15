# Iteration 7 — Coherence Audit

**Iteration:** goal-tradable_wall-iter-7
**Date:** 2026-07-15
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Scope of this iteration

Pure-frontend, additive-only (per spec: "None" backend). 4 files touched:
`apps/frontend/app/page.tsx` (+11/-4, prop-thread only), `apps/frontend/components/PriceChart.tsx`
(+204/-4, the substantive change — band overlay + confluence chip), `apps/frontend/lib/types.ts`
(+18/0, additive type widening), `README.md` (docs catch-up for prior-era bullets, out of coherence
scope — no application code, no routing, no computed value). No file under `apps/backend/app/`
appears in the diff; `config_fingerprint` claim independently plausible since no config/backend file
changed. One new backend test file (`apps/backend/tests/test_price_chart_confluence.py`) — test code,
not a served value or nav surface, out of Data Contract / IA scope.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Tradable band map (side/price_low/price_high/class/quality_score/round_number) | OK | Fetched via `fetchTradability(ticker, asOf)` → `GET /research/tradability` (`apps/frontend/lib/api.ts:1056-1071`, unchanged, canonical per blueprint row). Drawn verbatim in `apps/frontend/components/PriceChart.tsx:447-464` — reads `band.side`, `band.price_low`, `band.price_high`, `band.class`, `band.quality_score`, `band.round_number` only; no scoring/clustering. Byte-identical pattern to the pre-existing `StructureChart.tsx:97-120` precedent it explicitly reuses. |
| Current tape state (five-state) | OK | Threaded as `tapeState={snapshot?.tape_state ?? null}` (`apps/frontend/app/page.tsx:255`) — reuses the SAME WS snapshot field other cockpit surfaces already render; not a new fetch, not a second source. Chip compares it against the served mapping at `PriceChart.tsx:495-499`, never recomputes it. |
| Rejection/breakthrough state mapping (`structure_tape_map.entries.rejection_states` / `.breakthrough_states`) | OK | Fetched via `fetchStrategies()` → `GET /research/strategies` (`apps/frontend/lib/api.ts:868-882`, unchanged, canonical). Looked up by registry id at `PriceChart.tsx:492` (`STRATEGY_TAPE_MAP_ID = "structure_tape_map"`, `PriceChart.tsx:88` — a lookup KEY, not confirmation vocabulary, mirroring `app/structure/page.tsx:190`'s `STRATEGY_TAPE_ID` precedent byte-for-byte) and read as property accesses at `PriceChart.tsx:493-494` (`.rejection_states`, `.breakthrough_states`) — never restated as an object-literal mapping. Confirmed independently by the new backend source-inspection tests (`test_price_chart_confluence.py::test_confluence_matching_has_no_hardcoded_tape_state_literal`, `::test_confluence_matching_reads_rejection_and_breakthrough_off_the_served_entry`), which I re-verified by reading the actual grep targets in the diff myself rather than trusting the test's own claim. |
| Price-in-band × tape-state-matches-mapping ("confluence") | OK — pre-authorized display conjunction | `matchedBand` (`PriceChart.tsx:483-485`) and `matchKind`/`confluence` (`PriceChart.tsx:495-501`) are boolean membership/equality checks over already-served values (last price from the existing `/tape/{ticker}/history` poll, band range from `/research/tradability`, state names from `/research/strategies`). This is exactly the case the blueprint pre-registers verbatim: "the chip's on-screen condition is a display conjunction of TWO canonical reads … zero client recomputation of scores, classes, reactions, PnL, or provenance" (`blueprint.md:70-72`). Not a new computed value. |
| Side→direction reading (`resistance→short`, `support→long`) | OK — structural convention, not a value | `PriceChart.tsx:490-491`. Explicitly specified by the iteration spec's own Notes ("Chip semantics reference") as the intended developer guidance, not a re-derivation of any registered metric; used only to pick which already-served mapping key (`long`/`short`) to read. |
| Measured-history / edge-report citation | OK, with a note | The chip's "measured history: edge report" text (`PriceChart.tsx:562-565`) is a static string, not a fetch of `GET /research/edge-report` — no numeric edge-report value (n, R, $) is displayed, so there is no duplicated computation or non-canonical source of any Data Contract figure. See advisory note below; not a violation because no value is at stake. |
| `Strategy.entries` type widening (`rule` → `StrategyEntries` with optional `rejection_states`/`breakthrough_states`/etc.) | OK | `apps/frontend/lib/types.ts:1079-1096`. Purely additive/optional-field widening of the existing `GET /research/strategies` response type — no new fetch, no behavior change for `/structure`'s existing `entries.rule` reads (untouched file). Widens, does not fork, the canonical shape. |

No duplicate computation and no non-canonical source found for any registered value this iteration
touches.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Cockpit band overlay + confluence chip (`/`) | OK | No new route/page/nav file in the diff (only `page.tsx`, `PriceChart.tsx`, `types.ts` changed — no `Sidebar`/`Nav`/`TopBar`/router file touched). The overlay + chip render inside the pre-existing `/` cockpit page's existing "Price Chart — Tape-State Markers" `Panel` (`PriceChart.tsx`'s existing `<Panel title="Price Chart — Tape-State Markers">` wrapper, unchanged), which is the blueprint's own registered canonical home: "J-06 Cockpit confluence (band overlay + descriptive chip) → `/` → `PriceChart` (sim/historical only) → Cockpit" (`blueprint.md:37`). `/` is the nav's first top-level entry (`blueprint.md:21`) — 0/1-click reachable, well within the ≤2-click rule. No parallel shell (reuses the existing `Panel` component); no duplicate home (this is a distinct, blueprint-registered surface from `/structure`'s Tradable Map — same canonical data, two intentionally different UI contexts, which the Data Contract explicitly allows as re-formatting for display). |
| Live-mode gate | OK — verified unchanged | `apps/frontend/app/page.tsx:251`: `(mode === "sim" || mode === "historical")` — textually identical before/after (diff only adds a comment above it and the additive `tapeState` prop inside the JSX call). Confirms live mode stays byte-identical, per DoD. |

No new page, no new nav entry (nav is frozen for Era 5B, honored), no hidden feature, no duplicate
home, no parallel shell.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The confluence chip's "measured history: edge report" copy is a fixed string, not a value read from
  `GET /research/edge-report` — no $ /R/n figure is displayed, so this is not a Data Contract
  violation (nothing is duplicated or mis-sourced), just narrower than a literal reading of the
  iteration spec's "cites the edge report as measured history" might suggest. If a future iteration
  wants the chip to surface an actual edge-report figure, it must be fetched from
  `GET /research/edge-report` verbatim (never recomputed) — a note for the decomposer, not a defect
  today.
- `README.md`'s `AUTO:capabilities` block was refreshed to catch up documentation for several
  already-shipped prior-era surfaces (Tradable Map default, Case Studies, Edge Report, `structure_tape_map`
  registry card) but does not mention this iteration's new cockpit band overlay / confluence chip
  anywhere. Documentation-only, no application code or data source — outside this gate's Data
  Contract / IA scope (README is not a UI surface or nav path), so not scored here; flagged only as
  color for whichever agent owns README completeness.
