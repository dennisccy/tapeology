# Goal Iteration 10 — Thesis geometry is drawn on the price chart (J-48)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 10
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-48
- **Required-still-passing journeys:** J-01, J-02, J-17, J-31, J-38, J-42, J-45, J-50, J-52, J-68
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - **One focused chart, computed once.** OHLC bars and tape-state markers MUST be computed once in the engine history buffer and read identically by `…/history` and the chart; the UI MUST NOT recompute side, state, or price from raw data. An empty window MUST yield an **empty** chart, not invented candles. The chart is analysis-only — it MUST NOT add any order/execution affordance. The chart's **time axis shows true clock time** (real market time for historical; a synthetic session clock for simulated) via an **additive canonical epoch anchor** — the chart still recomputes no side/state/price, and the engine still bins on its deterministic logical timeline. *(critical)*
  - **Stay in scope.** No stock scanner/screener, no news/theme/sentiment analysis, no fundamental analysis, no chart-pattern or indicator charting, no portfolio/position management — these belong to separate projects and MUST NOT be built here. The one allowed chart is the focused price candlestick + tape-state-marker overlay (simulated/historical), which adds **no** indicators, studies, or drawing tools. *(critical)*
  - **No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the tape. *(critical)*
  - **The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested). An observer failure MUST surface explicitly and never kill the feed. *(critical)*
  - **Journal integrity.** Verdict timelines are append-only: never edited, backfilled, fabricated, or recomputed at read time; nothing is recorded before declaration; gaps (pause, watch restart, stale spans) are explicit events; data-end resolves to an explicit `expired`, never a fabricated outcome; action marks are recorded exactly as the user stated them — never inferred fills. Abandoned theses remain visible in every denominator (no survivorship pruning), and an entry-marked thesis can never be abandoned. *(critical)*
  - **No prediction language.** A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do. *(critical)*
  - **Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass; every hint MUST cite the user's study baseline for its setup/feed or state exactly that none exists. Shipping a buy/sell-adjacent cue with no evidence layer behind it is a defect. *(critical)*
  - (Geometry is capability 25 — declared-thesis visualization, not a cue. It draws what the user already declared and what the timeline already published; it adds no checklist, stance, or hint.)

## GOAL

A declared thesis becomes visible on the price chart: labeled invalidation and level price-lines at the declared prices, with verdict-transition, entry/exit, and first-confirmation markers at their times — all computed once server-side in the existing single thesis-projection builder and drawn verbatim by the chart.

## BACKGROUND

The iter-9 evaluator's primary recommendation is **J-48**: its dependencies are now complete (J-52 action marks passing, J-47 interruption-safe lifecycle passing), and it owes the explicitly deferred chart clauses of **J-45** (the level price-line for `level_break` theses) and **J-52** (entry/exit marks drawn on the chart). goal.md capability 25 defines the shape exactly: "the declared invalidation and level render as labeled price-lines; published verdict transitions, entry/exit marks, and the first-confirmation mark render as markers visually distinct from tape-state markers — in every mode, computed once server-side and drawn verbatim." Everything geometry needs already exists in canonical owners: thesis prices on the row-15 projection (`build_projection`, `apps/backend/app/research/monitor.py:137` — the SINGLE builder, coherence-confirmed in iter-9), the append-only verdict timeline with `logical_ts`/`wall_ts`/`last` (row 16), and verbatim marks with `logical_ts` (row 18, `marks_projection`). The chart (`apps/frontend/components/PriceChart.tsx`) already maps logical time to the true-clock axis via the canonical epoch anchor (`epoch_anchor + logical_ts`, row 13 — the established J-31 additive display offset) and already supports series markers; no engine or history-buffer change is needed or allowed.

**Binding lessons surfaced for this iteration (state/lessons.md):**
- **The chart is a below-the-fold visual surface**: browser-qa MUST scroll it into view (or capture full-page) before every chart assertion, and the evaluator opens the PNGs — a viewport-cropped capture of an empty header is not evidence.
- **Pre-capture server-freshness canary**: restart the QA backend after dev changes; assert server start time > newest patched-file mtime (or a content canary) before any capture.
- **Capture geometry states at the asserted moment before sim teardown**: SIM-BUYER is a bounded stream — capture the pre-cross (pending, lines only) and post-confirmation (markers) moments while the watch is live, not after it closes.
- **The chart reads geometry verbatim from its single owner — derive nothing new client-side**; the new served value (the `geometry` key) is registered in the blueprint Data Contract with one owner (done alongside this spec).
- **Diff the executed browser-test list against this spec's journey matrix** before writing results.
- **Never `npm run build` against the live dev server's shared `.next`** — use `NEXT_DIST_DIR=.next-qa`.
- **No schema change is expected** (geometry is a pure projection of already-persisted rows). If one becomes unavoidable, it MUST ship as a versioned migration proven against a committed old-schema fixture — otherwise stop and flag.
- The FULL-pipeline harness defect (engine halts at `qa_complete`) remains open — depth stays **lean** per the evaluator.

## IN SCOPE

### Backend

- [ ] **Additive `geometry` key on the row-15 thesis projection** (`apps/backend/app/research/monitor.py::build_projection` — the ONE builder; never a second path): when a thesis projection is built, it also carries a chart-ready `geometry` object computed from canonical values only:
  - **`price_lines`** — the invalidation line (always; the declared `invalidation_price` verbatim) and the level line (ONLY when `level_price` is set; declared price verbatim), each with a backend-owned plain-language label (display copy lives with the taxonomy module per Data Contract row 24 — the frontend hardcodes no research strings).
  - **`markers`** — (a) one marker per **published verdict transition** from the thesis's append-only timeline (row 16): verdict, `logical_ts`, `wall_ts` (a pure projection of the appended rows — never recomputed, never edited); (b) the **entry** and **exit** marks (row 18) at their recorded `logical_ts` with their verbatim prices — present ONLY when the marks exist (no marks ⇒ no mark markers, no fabricated placement); (c) the **first-confirmation mark** — the first timeline event whose verdict is `confirming` — identified once server-side.
  - **Honest segment rule (computed server-side):** geometry markers include only events placeable on the **current watch's logical timeline** — i.e. events at/after the latest `watch_restarted` gap event when one exists (a re-attached thesis's pre-gap events belong to a previous watch's timeline and MUST be omitted from the chart rather than misplaced; they remain fully visible in the journal timeline). Price-lines are time-independent and always served.
- [ ] **WS parity for free:** the WS `thesis` key already re-exposes the same projection — extend the existing REST-equals-WS-verbatim equivalence test to cover `geometry`. No new endpoint; `GET /research/thesis/active?ticker=` remains the single serving endpoint.
- [ ] **Timeline access stays canonical:** the verdict-transition rows handed to `build_projection` come from the thesis's canonical append-only record (the journal store / the monitor's own appended rows — the same single-writer data, one shape for the live and survivor paths). If a cap is needed for very long timelines, reuse the existing config-owned timeline cap — no new magic numbers.

### Frontend

- [ ] **Chart renders the geometry verbatim** (`apps/frontend/components/PriceChart.tsx` + wiring in `apps/frontend/app/page.tsx`): the page already holds the live thesis projection (WS `thesis` key); pass it (or its `geometry`) into the chart.
  - Price-lines render via the charting library's price-line facility at the served prices with the served labels — invalidation and (when present) level, visually distinct from each other.
  - Thesis markers render through the existing series-marker mechanism, **visually distinct from tape-state markers** (different shape/position), using the established verdict semantics: `confirming` emerald, `weakening` amber, `rejecting`/`invalidated` rose, `pending` slate; entry/exit marks in their own distinct treatment with mono prices.
  - Marker x-placement uses the SAME canonical epoch anchor the candles already use (`epoch_anchor + logical_ts` — row 13); the chart computes no state, side, price, or time basis of its own.
  - **No thesis ⇒ no geometry**: with `thesis: null` the chart renders exactly as today (J-68/J-17 regression bar); geometry clears when the thesis resolves or is cleared.
  - The same one component serves all modes (sim/historical/live) — no mode-specific geometry code path.

### New user-facing capability
The user sees their declared thesis ON the chart: where the idea is invalidated, where the level is, when each verdict published, when they entered/exited, and when the tape first confirmed — in the same pane as price and tape-state markers.

### New information displayed
Labeled invalidation/level price-lines at the declared prices; verdict-transition markers; entry/exit mark markers with verbatim prices; the first-confirmation marker.

### New user actions
None — this iteration is pure visualization of already-declared/recorded facts. No new buttons, forms, or controls; the chart gains no interaction affordance.

### UI surface changes
The existing `/` cockpit chart pane only (price-lines + a thesis marker layer). No new pages, no nav change, no new panels.

### Product surface delta
The chart becomes the thesis canvas goal.md promises — closing the deferred chart clauses of J-45 (level line) and J-52 (marks on chart) and completing the declared-thesis visual loop before the journal/review surfaces (J-55+) are built.

### Blueprint conformance
No new surfaces. J-48's registered home is already `/` chart pane (Cockpit) in `blueprint.md`. The chart pane is on the home route (0 clicks).

### Data-contract additions
No new contract rows. One **additive note** registered in `blueprint.md` row 15 (done by the decomposer alongside this spec): the thesis projection gains a `geometry` key — computed ONLY inside the same single `build_projection` as a pure projection of the declared thesis prices + the row-16 append-only timeline + row-18 marks (current-segment events only), served by the same endpoint + WS `thesis` key, drawn verbatim by the chart on the row-13 epoch anchor. Never a second computation path, never client-side derivation, never a second endpoint.

## OUT OF SCOPE

- Entry risk flags (J-49) — the evaluator's named alternative; next candidate, not this iteration.
- The `/journal` page, journal list endpoint, review flow, grades, mistake tags (J-51, J-55–J-57).
- Management stance, distance-to-invalidation, open R (J-53); execution checks (J-54); excursions/analytics/studies (J-58–J-62); the entire cue layer (J-63–J-67 — binding build order: cues strictly after evidence J-58–J-62 passes).
- Any engine/classifier/feature/provider/history-buffer file change. The geometry owner is the research projection; `GET /tape/{t}/history` and the engine history buffer are NOT touched (tape-state markers stay engine-owned, thesis geometry stays research-owned — two registered owners, one chart). If a lifecycle/status value turns out to be needed, read it from its existing canonical owner — do not blanket-avoid by duplicating it.
- Schema changes (geometry is a read-time projection of persisted rows — the timeline itself is never recomputed, the projection merely re-exposes the appended rows verbatim). If unavoidable, versioned-migration rule applies (stop and flag first).
- Chart pan/zoom/tooltip enhancements, marker click interactions, drawing tools, or any chart capability beyond the geometry overlay.
- Re-rendering pre-gap (previous-watch) markers on a re-attached thesis's chart — omitted honestly per the segment rule; the journal timeline remains their record.

## DEFINITION OF DONE

- [ ] Target journey J-48 passes via browser-qa-agent on the sim leg (the live-mode render leg is credentials/market-hours operator-gated per goal.md — the same single component renders it; note it explicitly in results rather than skipping silently)
- [ ] J-45's deferred level-line clause and J-52's deferred chart-marks clause are evidenced in the J-48 captures
- [ ] Required-still-passing journeys remain green — especially J-17/J-31 (tape-state markers + true-clock axis unchanged) and J-68 (no-thesis chart renders exactly as before)
- [ ] No anti-goal violation introduced (no indicators/drawing tools/execution affordances; chart computes nothing; timeline never recomputed at read)
- [ ] Unit tests pass (geometry projection + WS/REST parity + segment rule + no-marks honesty); full backend suite green; observer-equivalence suite green; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-10-dev.md`

## TESTING REQUIREMENTS

- Browser (J-48, per goal.md steps — SCROLL THE CHART INTO VIEW for every capture; run the server-freshness canary first; capture at the asserted moment before the bounded sim ends; use `NEXT_DIST_DIR=.next-qa` for any build):
  1. Watch `SIM-BUYER`; declare **level_break / long** with a level above the current last (inside the scenario's deterministic rise) and an invalidation below. Capture: BOTH labeled price-lines visible at the declared prices while the verdict is still `pending` (pre-cross) — this is also J-45's deferred level-line clause.
  2. Mark an entry (prefilled last). Capture: the entry marker on the chart at its time with its verbatim price — J-52's deferred chart clause.
  3. After last crosses the level and confirmation publishes: capture the `confirming` state with the verdict-transition marker(s) and the first-confirmation marker visible, **visually distinct from the tape-state markers in the same frame**.
  4. Regression frame (J-68/J-17/J-31): a watch with NO thesis shows candles + tape-state markers + true-clock axis only — no lines, no thesis markers.
  - Diff the executed test list against this matrix before writing results; the evaluator opens the PNGs.
- Unit/integration (`apps/backend/tests/`):
  - `build_projection` geometry: level_break thesis ⇒ invalidation + level price-lines with the declared prices and backend-owned labels; non-level setup ⇒ NO level line; entry/exit marks present ⇒ markers with verbatim price + `logical_ts`; no marks ⇒ no mark markers; first-confirmation marker = first `confirming` timeline event; verdict-transition markers equal the appended timeline rows exactly (projection, not recomputation).
  - Segment rule: a thesis with a `watch_restarted` gap event serves only post-gap markers in geometry (price-lines still present).
  - WS `thesis` frame equals REST `GET /research/thesis/active` projection verbatim INCLUDING `geometry` (extend the existing parity test).
  - Observer-equivalence suite stays green (engine outputs byte-identical — nothing in this diff touches the engine).
- Error cases: thesis with `thesis: null` ⇒ no geometry anywhere (no empty-but-present lines); resolved thesis clears geometry from the chart; a survivor (not-evaluated) projection still serves geometry from persisted records via the same builder without error.

## NOTES

- Evaluator mandate (iter-9 eval.md): primary J-48, depth lean ("the FULL-pipeline harness defect (engine halts at qa_complete) remains open, and lean iterations 6–9 have produced complete, verifiable evidence").
- Documented assumption: the sim browser leg is one continuous watch, so the segment rule is exercised by unit test (re-attach pixels were iter-9's scope); goal.md J-48 marks the live-mode chart render as credentials/market-hours operator-verifiable — the sim leg plus the single shared component is the browser evidence this iteration owes.
- Marker copy discipline: any marker label text is backend-served or a verbatim enum label — present-tense, descriptive, never imperative or predictive ("Descriptive only — not trading advice" register extends to the chart).
- Iter-9 lesson (recorded in lessons.md): when an iteration needs a value the OUT OF SCOPE section would forbid touching, name the canonical owner up front instead of duplicating it — this spec names the row-15 builder, row-16 timeline, row-18 marks, and row-13 anchor as the only sources geometry may read.
