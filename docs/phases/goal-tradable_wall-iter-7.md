# Goal Iteration 7 — Cockpit confluence: band overlay + descriptive chip (J-06)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** tradable_wall
- **Iteration:** 7
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-06
- **Required-still-passing journeys:** J-01, J-02, J-04, J-05, J-07 (full regression — every currently passing/already_passing journey; J-03 is `partial`/operator-gated and not in the protect-set)
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative trading cues. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **The tradable map is a lens, never a second levels engine.** `research/tradability.py` consumes `compute_levels` output verbatim (plus bars for scale context); it never re-detects pivots/extremes and never alters the frozen raw computation or its parameters. *(critical)*
  - **Morning-markup discipline.** Any session's map derives only from bars fully completed by the prior session's close; no forming-bar data enters a map, an event, or a chip. *(critical)*
  - **Descriptive, never imperative.** Chips, case studies, and reports state conditions and cite measured history — never "buy/sell/short now", no prediction or expected-return language, anywhere in UI copy. *(critical)*
  - **Feed honesty — never pool across feeds.** The `feed` stamp comes verbatim from the adapter/key tier; `iex`, `sip`, and Yahoo-bar lineages are never pooled in any analysis cell, report row, or claim; `iex` is never presented as the consolidated tape. *(critical)*
  - **Keys never committed, never logged.** Alpaca credentials live only in the operator's environment; no secret in source, fixtures, logs, artifacts, or reports. *(critical)*
  - **Live mode stays untouched.** The cockpit price chart remains hidden in live mode; no execution path, ever. *(critical)*
  - **No vocabulary drift.** No "paper trading", "shadow trading", "annualized", "expected profit", or advice/imperative phrasing anywhere in the UI copy; simulated PnL and simulated size always carry the visible "simulated — not indicative of live results" register.
  - **New strategy code is additive and registered — never a mutation.** `structure_tape_map` is a new config-owned registry entry beside frozen `v1`/`structure_tape`; no frozen definition, parameter, or output changes; the `config_fingerprint` stays `4d665603569b9dbf`. *(critical)*

## GOAL

In the cockpit `PriceChart` (sim + historical modes only; live stays hidden), overlay the watched symbol's tradable bands beside the existing tape-state markers and show a **descriptive confluence chip** when the last price is inside a band AND the current tape state matches the config-owned rejection/breakthrough mapping — surfacing the tradable wall where trades are actually watched, reading every value verbatim from its owning endpoint.

## BACKGROUND

J-06 is the **last agent-buildable journey** (J-01/J-02/J-04/J-05 passing; J-03 `partial`, its remaining credentialed ≥10-window recording operator-Alpaca-gated; J-07 sentinel). Priority rubric: nothing regressed; iter-6 coherence was `COHERENCE-PASS` (no consolidation owed); J-03's remaining work is human/operator-blocked (rule 6 — do not re-plan it); so J-06 is the correct and only agent-buildable target.

Every endpoint the overlay + chip need already exists server-side, so this is a **pure-frontend** iteration (no backend, no data-model, config untouched, `config_fingerprint` stays `4d665603569b9dbf`): bands from `GET /research/tradability` (J-01), the `structure_tape_map` rejection/breakthrough state mapping from `GET /research/strategies` (config.py:1357-1362, registered since J-04), the five-state timeline + last price from `GET /tape/{ticker}/history` (frozen foundation), and the edge-report citation from `GET /research/edge-report` (J-04). The band-line-by-side draw already exists as a verbatim precedent in `StructureChart.tsx` (L97-120) and `PriceChart.tsx` already draws price-lines via `series.createPriceLine`; the sim/historical-only render gate already exists in `page.tsx` (L248-249).

**Depth = full**, justified by the "Picking depth" triggers: (a) a new **coherence-relevant** cockpit UI surface on the primary `/` page — it must read the shared tradability/strategy/tape values *verbatim* and must not become a second home or a second computation for them; (b) **browser-verifiable**; (c) several **critical rails simultaneously load-bearing** — descriptive-never-imperative chip copy, mapping-read-from-`/research/strategies`-not-client-hardcoded (single-source-of-truth), morning-markup no-lookahead as-of, and live-mode byte-identical; (d) this is the **closing feature iteration**; and (e) the iter-6 evaluator explicitly recommended **full**. (The prior iteration was CONTINUE, not ESCALATE, so full is a judgment call on surface risk, not a forced escalation.)

**Lessons applied** (from `lessons.md`):
- **iter-6** (applies to any iter running browser-QA on this `/structure`/cockpit render family): deep-scroll Chrome-MCP screenshots can come back blank/double-exposed — fall back to DOM `innerText` capture (a legitimate pass, not a skip); and anchor acceptance on the goal's **structural** criterion (chip present with descriptive copy at the in-band + mapped-state condition; overlay present), NOT on a specific numeric band score, which drifts on the live, mutable store.
- **iter-3** (applies to any credentialed/operator-gated headline — especially J-06's credentialed AAPL cockpit replay): a credentialed headline is met only with a **persisted, re-openable artifact + a real screenshot of the named pinned case**, never a handoff narration or a QA "documents the outcome" check. J-06's credentialed AAPL 06-22 replay stays operator-gated — honestly blocked when keys are absent, never simulated.
- **iter-1** (applies to any iter reusing J-01's morning-markup as-of resolution — J-06 cockpit as-of): the bands overlaid must be as-of the **prior session close**; add an explicit no-lookahead check for the cockpit's as-of resolution so no forming-bar band enters the overlay/chip.

## IN SCOPE

### Backend
- [ ] **None.** No endpoint is added or modified; `config.py`, `strategies.py`, `tradability.py`, `levels.py`, `backtests.py`, `edge_report.py`, `setups.py`, `datasets.py`, the engine, and the adapters stay absent from the diff. `config_fingerprint` stays `4d665603569b9dbf`.

### Frontend
- [ ] **Band overlay in `apps/frontend/components/PriceChart.tsx`** — fetch the watched symbol's tradable bands from `GET /research/tradability` (symbol = watched ticker, `as_of` resolving to the prior completed session's close) and draw each band beside the existing tape-state markers, reusing the verbatim band-line-by-side precedent from `StructureChart.tsx` (solid line per band edge, rose = resistance / emerald = support, title from the served `side`/`class`/`quality_score`/`round_number`). The component clusters/scores/re-detects nothing — it only draws served fields.
- [ ] **Honest empty state** — a SIM-*/no-bars symbol (served band list empty / no bar series) shows the chart + tape markers + an explicit "no tradable map" empty state; never a fabricated band, never a chip.
- [ ] **Confluence chip** — visible only while the last served price (latest `GET /tape/{ticker}/history` bar close) is **inside a band** AND the current served tape state matches the **config-owned rejection/breakthrough mapping** for that band's side, read from `GET /research/strategies` (`structure_tape_map` → `entries.rejection_states` / `entries.breakthrough_states`). Chip copy is **descriptive** — it states the condition (side/range/class, tape state) and cites the edge report as measured history; it carries no imperative/prediction/expected-return language. The chip is **absent** when price is outside every band or the state is unmapped/`unclear`.
- [ ] **Preserve live-mode gating** — `PriceChart` continues to render only for `mode === "sim" || mode === "historical"` (`page.tsx` L248-249); live mode stays byte-identical (chart + overlay + chip all absent/hidden).
- [ ] **`apps/frontend/lib/api.ts` / `apps/frontend/lib/types.ts` (additive only)** — reuse the existing `fetchTradability` (J-05) and add a `fetchStrategies` client + the mapping/strategy types if not already present; no change to existing signatures' behavior.

### New user-facing capability
In the cockpit, the operator now sees the watched symbol's **tradable bands drawn on the price chart** and, at a confluence moment, a **descriptive chip** stating the condition (price inside R/S band, class, and the current tape state) with a pointer to the edge report — the tradable wall surfaced at the moment and place trades are watched, not only on `/structure`.

### New information displayed
The band overlay lines (verbatim from `/research/tradability`) on the cockpit chart, and the confluence chip — a **display conjunction** of served band range × served last price × served tape state × served mapping, plus the edge-report citation. No newly *computed* value.

### New user actions
None. The overlay and chip are display-only; the existing bar-size selector and Watch flow are unchanged. No new button/form/control is added — this is a descriptive surface, not an interactive one.

### UI surface changes
The cockpit `PriceChart` gains the tradable-band overlay + the confluence chip + the SIM/no-bars honest "no tradable map" empty state. No other surface changes.

### Product surface delta
The tradable map (previously visible only on `/structure`, J-05) is now surfaced in the **cockpit** at decision time, with tape-state confluence called out descriptively — closing the era's "surface it where trading happens" vision item for the cockpit.

### Blueprint conformance
J-06's canonical home is **already registered** in `blueprint.md` Information Architecture ("J-06 Cockpit confluence (band overlay + descriptive chip) → `/` → `PriceChart` (sim/historical only) → Cockpit"). No new page, no new nav entry (nav is frozen for Era 5B). **No blueprint edit is required this iteration** (verified: IA home present; Data Contract chip mapping/labels row + display-conjunction comment already present).

### Data-contract additions
**None.** The chip is a display conjunction of already-registered canonical values, each read verbatim from its single owning endpoint:
- band price range / side / class / `quality_score` / `round_number` — `research/tradability.py` → `GET /research/tradability`
- last price + current tape state (five-state) — frozen `TapeEngine` → `GET /tape/{ticker}/history`
- rejection/breakthrough state mapping — config → `strategies.py` → `GET /research/strategies`
- measured-history citation — `research/edge_report.py` → `GET /research/edge-report`

No new computing module, no new serving endpoint. (This exactly matches the existing `blueprint.md` note: "The chip's on-screen condition is a display conjunction of TWO canonical reads … mapping from `/research/strategies` — zero client recomputation.")

## OUT OF SCOPE

- **Any backend change** — no new/modified endpoint, no config change, `config_fingerprint` stays `4d665603569b9dbf`; every frozen backend file stays absent from the diff.
- **Any live-mode change** — the cockpit price chart stays hidden in live mode; no execution path, ever.
- **The credentialed recording itself** — J-06 *renders* whatever the endpoints serve; it does not record. The AAPL 06-22 tick recording is J-03's operator-Alpaca-gated deliverable.
- **Any change to `/structure`** (J-05 shipped) or to the setups / edge-report / tradability computations.
- **Client-side recomputation** of band ranges, classes, scores, reactions, tape states, PnL, provenance, or the confirmation mapping.
- **Client-hardcoded tape-state confirmation vocabulary or mapping** — the "which state confirms this side" decision must come from the served `/research/strategies` mapping.
- **New nav entry / new page** (nav is frozen).
- The iter-6 non-blocking `/structure` drill-in auto-clear UX nuance (review MINOR / audit F1) — a separate, unrelated surface.

## DEFINITION OF DONE

- [ ] **J-06 passes via browser-qa:** in sim/historical mode on a real symbol with bars, the band overlay is visible on the cockpit `PriceChart`; the confluence chip appears when the last price is inside a band AND the tape state is a mapped confirming state, with descriptive copy citing the edge report; the chip is absent when price is outside every band or the state is unmapped/`unclear`.
- [ ] A **SIM-*/no-bars ticker** shows the chart + tape markers + an honest "no tradable map" empty state (no fabricated band, no chip) — browser-verified.
- [ ] **Live mode is byte-identical** to before (PriceChart still hidden; no new element in the live cockpit) — browser-verified.
- [ ] The band overlay, chip mapping, chip state token, and last price are **all endpoint-read** — coherence-auditor confirms `COHERENCE-PASS` with zero client recomputation and no client-hardcoded confirmation vocabulary/mapping.
- [ ] **Required-still-passing** J-01, J-02, J-04, J-05, J-07 remain green (full regression).
- [ ] **`config_fingerprint` stays `4d665603569b9dbf`;** every frozen backend file is absent from the diff (backend untouched — independently verifiable via `git diff --name-only -- apps/backend/`).
- [ ] **No anti-goal violation:** chip copy is descriptive-only (no imperative/prediction/expected-return); bands are as-of the prior session close (no lookahead); no feed pooling; no credential in any file/log/artifact.
- [ ] Unit/component tests pass; full backend suite green; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-tradable_wall-iter-7-dev.md`.

## TESTING REQUIREMENTS

- **Browser (by ID):** **J-06** — (1) band overlay visible on the cockpit `PriceChart` in sim/historical on a real symbol; (2) chip appears at an in-band + mapped-state confluence moment with descriptive copy + edge-report citation, and is absent when price is outside all bands or the state is unmapped/`unclear`; (3) SIM ticker → chart + markers + honest "no tradable map" empty state; (4) live mode → chart/overlay/chip hidden (unchanged). Smoke re-verify **J-05** (`/structure` map default) and nav-unchanged.
  - *Per the iter-6 lesson:* this render family can yield blank/double-exposed screenshots at deep scroll — fall back to DOM `innerText` capture for any section that will not screenshot cleanly (a legitimate pass). Anchor chip/band acceptance on the **structural** criterion (chip present with descriptive copy at the in-band + mapped-state condition; overlay present), NOT on a specific numeric band score that drifts on the live store.
- **Unit/integration (component-level, keyless):**
  - The chip's "which state confirms this band's side" decision is driven by the **served `/research/strategies` mapping** (`structure_tape_map.entries.rejection_states` / `breakthrough_states`), not a client-hardcoded map — changing the served mapping changes chip visibility, and no tape-state confirmation vocabulary is hardcoded in the component.
  - The band overlay renders bands **verbatim** from `/research/tradability` (`side`/`price_low`/`price_high`/`class`/`quality_score`/`round_number`) and draws nothing (no bands, no chip) when the served band list is empty (SIM/no-bars honest empty state).
  - The chip is **absent** when the tape state is `unclear`/unmapped or the last price is outside every band.
- **Morning-markup / no-lookahead (iter-1 lesson):** a test that the cockpit's band overlay is requested and rendered **as-of the prior session close** — the endpoint enforces morning-markup server-side; assert the frontend passes an `as_of` that resolves to the prior completed session and renders only that served map, so no forming-bar band enters the overlay/chip.
- **Error/empty cases that must be handled:** SIM-*/no-bars symbol → honest empty state; tape state `unclear`/unmapped → no chip; price outside all bands → no chip; live mode → chart + chip hidden.
- **Operator-gated (honest-blocked, never simulated):** the credentialed **AAPL 2026-06-22 300-test replay** screenshot (bands + markers + chip during the test) requires Alpaca creds. When keys are absent it is honestly blocked/deferred — never simulated (iter-3 lesson: require a real screenshot of the named pinned case + a persisted artifact before the credentialed portion is called met; a handoff narration is not evidence). The **keyless** band-overlay + chip-logic + SIM-empty-state + live-unchanged portions are agent-buildable and browser-verifiable now and constitute J-06's passing core.

## NOTES

- **Interpretation logged** (`assumptions.md` iter-7): the goal's "mapping and **labels** read from `/research/strategies`, never hardcoded" is satisfied by reading the served rejection/breakthrough mapping and rendering the served tape-state token (cosmetic title-casing of a served token is an allowed re-format) — no new served label field is added, keeping J-06 pure-frontend and `config_fingerprint` frozen. Reversible.
- **Chip semantics reference** (for the developer): a resistance band defends a ceiling (short-direction reading) and a support band defends a floor (long-direction reading); the config maps `rejection_states = {long: bid_absorption, short: ask_absorption}` and `breakthrough_states = {long: buyer_control, short: seller_control}` (config.py:1357-1362). The chip must resolve this from the **served** `/research/strategies` payload, never from a restated client-side copy of these state strings.
- **Operator-gated carry (parallel — does NOT block J-06):** J-03's credentialed ≥10-window headline + a populated pinned-AAPL 06-22 tape timeline remains operator-Alpaca-gated. When it lands, the next browser-QA should screenshot the populated Edge Report cells + a real drill-in tape timeline + the cockpit chip during the real replay (closes audit T1).
- **After J-06 passes,** all six Must-have journeys are passing except **J-03** (`partial`, operator-gated) and **J-07** (sentinel, `already_passing`). The goal-evaluator decides whether that state is `GOAL_ACHIEVED` (with J-03's credentialed remainder recorded as an honest operator-gated carry) or `CONTINUE` — the decomposer does not pre-judge that call.
