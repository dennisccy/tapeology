# Goal Iteration 12 — True-clock chart axis + dd-MM-yyyy dates everywhere (J-31 / J-35)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich
- **Iteration:** 12
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-31, J-35
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10, J-11, J-12, J-13, J-14, J-15, J-16, J-17, J-18, J-19, J-20, J-21, J-22, J-23, J-24, J-25, J-26, J-27, J-28, J-29, J-30
- **Anti-goal reminders:**
  - **One focused chart, computed once.** OHLC bars and tape-state markers MUST be computed once in the engine history buffer and read identically by `…/history` and the chart; the UI MUST NOT recompute side, state, or price from raw data. An empty window MUST yield an **empty** chart, not invented candles. The chart is analysis-only — it MUST NOT add any order/execution affordance. The chart's **time axis shows true clock time** (real market time for historical; a synthetic session clock for simulated) via an **additive canonical epoch anchor** — the chart still recomputes no side/state/price, and the engine still bins on its deterministic logical timeline. *(critical)*
  - **Timezone-correct windows.** A historical window MUST be fetched for the exact instant the user selected in their local time — no silent UTC reinterpretation that shifts the window by the local offset; all market/session times shown to the user MUST carry an explicit zone label. *(critical)*
  - **Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*
  - **Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine MUST produce identical features, state, and confidence; classification MUST NOT depend on wall-clock time or randomness.
  - **No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config.
  - **No fabricated data.** The system MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey.

## GOAL

The price chart's time axis (and crosshair and markers) shows **true clock time** — real market time for historical replay, a synthetic session clock for simulated — formatted as `dd-MM-yyyy HH:mm:ss`, and **every date rendered anywhere in the UI** reads `dd-MM-yyyy` (24h times) from one shared formatter, with the native date picker replaced by a validated custom `dd-MM-yyyy` text input.

## BACKGROUND

The J-01–J-30 Must-have set reached GOAL_ACHIEVED at iter-11; `docs/goal.md` has since been extended with a refinement pass (J-31–J-35) that are now Must-have journeys not yet built (absent from journey-history; verified unbuilt by codebase probe — `PriceChart.tsx` renders `time: Math.round(b.time)`, i.e. elapsed/logical seconds, and there is no epoch/display anchor in the backend; the Historical picker still uses a native `<input type="date">` and `YYYY-MM-DD` plumbing in `lib/datetime.ts`). J-31 and J-35 are coupled — both center on time/date display, share the single shared date formatter, and J-35 explicitly names the J-31 chart axis as a place dates appear — so they are delivered together as one coherent "time display" outcome. Depth is **full**: J-31 introduces a NEW canonical data-contract value (an additive epoch/display anchor served by the engine/serializer), crosses the backend↔frontend boundary, and requires backend unit tests proving the anchor is exposed and that determinism is preserved — beyond a browser smoke test.

**Applied lessons (from `state/lessons.md`):**
- iter-6/7/8 (visual-journey verification): a chart/axis journey CANNOT be scored from backend tests + code inspection alone. Require a REAL rendered screenshot of the populated chart with the axis showing clock-time labels; poll the backend `/history` for real bars (>=5) BEFORE screenshotting; the shared harness `.next` on `:3650` has corrupted browser-qa repeatedly — build into an ISOLATED `NEXT_DIST_DIR` wired to the running backend if needed, and open the actual PNG bytes (a canvas element / PASS label alone is not proof; an idle "No ticker watched" shot is NO evidence).
- iter-2 (tz): the historical window picker historically sent NAIVE datetimes treated as UTC; row-12's resolver now resolves the exact tz-aware instant. J-35 MUST NOT regress that — the custom `dd-MM-yyyy` input still carries the explicit local zone label and resolves to the same tz-aware instant (no silent UTC shift); J-20 must stay green.
- iter-2 (symbol choice): IEX top-of-book is wide for high-priced names; do NOT assert a particular tape STATE for a real symbol in this iteration (TSLA honestly reads `unclear`). J-31/J-35 are about TIME/DATE display, not classification — assert axis timestamps and date format, never a state.

## IN SCOPE

### Backend
- [ ] Add an **additive canonical epoch/display anchor** to the engine snapshot: the real UTC epoch origin for historical/live (the first record's real epoch) and a synthetic session-start instant for simulated, preserved alongside the existing logical timeline. Computed ONCE in the engine/feeder; the engine still bins on its deterministic logical timeline (no wall-clock in classification).
- [ ] Expose the anchor read-only via the existing history projection so the chart can map each logical-binned bar/marker time to a true clock instant. Prefer extending the existing `GET /tape/{ticker}/history` projection (and the snapshot serializer) rather than adding a new endpoint; the chart reads it verbatim and recomputes no price/side/state.
- [ ] All new constants (e.g. the simulated synthetic-session-start anchor convention) live in `app/config.py` — no inline literals.

### Frontend
- [ ] Add ONE shared date/time formatter in `apps/frontend/lib/datetime.ts` (e.g. `formatDateDMY` / `formatDateTimeDMY`) producing `dd-MM-yyyy` and `dd-MM-yyyy HH:mm[:ss]` (24h) in the user's local zone with an explicit zone label where a date-time is shown. Route EVERY existing date/date-time render through it.
- [ ] `PriceChart.tsx`: replace the elapsed/logical `time: Math.round(b.time)` axis with **true clock time** derived from the engine's epoch anchor (real market time for historical; synthetic session clock for simulated). Axis ticks, crosshair, and marker timestamps read `dd-MM-yyyy HH:mm:ss` via the shared formatter. Switching bar size 10/30/60 s keeps the real-time axis. The chart still reads `/history` verbatim — it places no markers and recomputes no price/side/state itself.
- [ ] Replace the native `<input type="date">` in the Historical picker (`TopBar.tsx`) with a **custom validated `dd-MM-yyyy` text input`; the field still carries the explicit local zone label and resolves to the same tz-aware instant via the existing row-12 resolver (no silent UTC shift).
- [ ] Audit and convert every remaining UI date render to the shared formatter: market-status (live) times, the watched-source descriptor ("historical <SYM> <window>"), and recent-trade / event timestamps on real data — no `MM/DD/YYYY`, ISO `YYYY-MM-DD`, or "Jun 8"-style date remains visible anywhere.

### New user-facing capability
The user can read the price chart's time axis as real market clock time (historical) or a synthetic session clock (simulated) instead of a 0…600 s playback counter, and sees a single consistent `dd-MM-yyyy` date format across the entire UI, entering historical dates via a `dd-MM-yyyy` field.

### New information displayed
True clock-time stamps on the chart axis / crosshair / markers; `dd-MM-yyyy` (and `dd-MM-yyyy HH:mm:ss`) dates everywhere they were previously locale/ISO/elapsed-formatted.

### New user actions
A custom `dd-MM-yyyy` date text field (replacing the native date picker) in the Historical controls.

### UI surface changes
The existing price-chart pane (axis/crosshair/marker labels) and the existing Historical date/time picker, both on the single `/` HOME cockpit. No new pages, panels, or routes.

### Product surface delta
The one allowed chart becomes a genuinely interpretable decision aid (you can tell *when* a marked state occurred in real market time), and date display is unified and unambiguous (`dd-MM-yyyy`) across the product.

### Blueprint conformance
All work lives on the existing `/` HOME cockpit — the price-chart pane (J-17/J-18 home) and the Historical date/time picker (J-20 home). No nav-skeleton change, no new route. The chart still reads row-10 (`GET /tape/{ticker}/history`) verbatim; the window resolution still flows through row-12. Plans into the existing Information Architecture additively.

### Data-contract additions
- **NEW row 13 — Canonical display/epoch anchor** (the real UTC epoch origin for historical/live; a synthetic session-start instant for simulated). Single computing owner: the **engine/feeder** (preserved once alongside the logical timeline; the engine still bins on the deterministic logical timeline and reads no wall-clock for classification). Single serving endpoint: the existing **`GET /tape/{ticker}/history`** projection (and the snapshot serializer), read-only. Re-exposed by: `WS /stream` / `/summary` as applicable. The chart reads the anchor verbatim to render true clock time — it computes no price/side/state. This is additive; it does NOT introduce a second way to compute or serve any value already in rows 1–12 (the chart still reads OHLC/markers from row 10; the resolved historical window stays row 12). To be registered in `blueprint.md`.
- The shared `dd-MM-yyyy` formatter is **presentation only** (frontend) — not a new computed/served value; no contract row.

## OUT OF SCOPE

- J-32 (live replay-speed changes), J-33 (real-data classification calibration), J-34 (chunked long-window loading) — separate iterations.
- Any change to the engine's logical timeline, classification math, feature windows, or confidence — the anchor is **additive display metadata only**; J-01–J-09 classification and J-33 calibration are untouched here.
- Any change to the live-socket teardown / `stream_live` / feeder lifecycle (iter-4 deadlock lesson) beyond reading/preserving the epoch origin.
- Any new chart affordance (indicators, studies, drawing tools, pan/zoom behavior changes, order/execution controls) — anti-goal: one focused chart only.
- Changing the row-12 timezone resolution semantics — the custom date input must resolve to the SAME tz-aware instant as today (no silent UTC shift).

## DEFINITION OF DONE

- [ ] Target journeys J-31, J-35 pass via browser-qa-agent with REAL rendered evidence (see TESTING REQUIREMENTS).
- [ ] Required-still-passing journeys J-01–J-30 remain green (especially J-17/J-18 chart render, J-20 local-time window, J-08 single-source-of-truth, and all five sim classification scenarios J-01–J-09).
- [ ] No anti-goal violation introduced (chart still computes nothing; anchor is additive display metadata; determinism preserved; tz correctness preserved; no fabricated data).
- [ ] Backend unit tests pass (anchor exposed in the history projection for historical/sim; same ordered stream still yields identical features/state/confidence — anchor is additive and does not perturb classification); no regressions in the existing backend suite.
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich-iter-12-dev.md`.

## TESTING REQUIREMENTS

- **Browser:**
  - **J-31** — Historical replay of a real symbol over a known past intraday window: the chart axis / crosshair / markers show **real market clock time** (`dd-MM-yyyy HH:mm:ss`, local zone with explicit label), NOT a 0…600 s playback counter; switching bar size 10/30/60 s keeps the real-time axis. A `SIM-*` ticker shows a synthetic session-clock axis (a real clock face, not elapsed seconds). REQUIRES a real rendered screenshot of the populated chart with visible clock-time axis labels — poll backend `/history` for bars>=5 first; if the shared `:3650` `.next` is corrupted, build into an isolated `NEXT_DIST_DIR` wired to the running backend and open the PNG bytes (an idle/placeholder shot is NO evidence).
  - **J-35** — Every UI date reads `dd-MM-yyyy` (date-times `dd-MM-yyyy HH:mm[:ss]`, 24h): chart axis/crosshair (J-31), market-status times, watched-source descriptor, real-data trade/event timestamps, and the historical picker; no `MM/DD/YYYY`, ISO, or "Jun 8" remains. The native date picker is replaced by a working custom `dd-MM-yyyy` text field that still Watches a valid window.
- **Unit/integration:**
  - Backend: the engine/feeder preserves a correct epoch anchor (historical = first real record epoch; simulated = synthetic session-start) and the history projection exposes it; an additive-anchor assertion that the SAME ordered event stream still yields byte-identical features/state/confidence (determinism preserved — the anchor does not feed classification).
  - Frontend: the shared formatter renders `dd-MM-yyyy` / `dd-MM-yyyy HH:mm:ss` for representative instants; the custom date input parses/validates `dd-MM-yyyy` and resolves (via the existing row-12 resolver) to the SAME tz-aware instant as the prior native input for the same local date (no UTC shift) — guard against a J-20 regression.
- **Error cases:**
  - An invalid `dd-MM-yyyy` entry (e.g. `31-02-2026`, malformed text, empty) gives inline validation and never a silent no-op (J-24 stays green).
  - An empty historical window still yields an EMPTY chart (no invented candles) and the axis does not fabricate timestamps.

## NOTES

- This iteration resumes the session after a post-GOAL_ACHIEVED goal extension (J-31–J-35 added to `docs/goal.md`). It is NOT a regression — these are newly-introduced Must-have journeys. The evaluator should add J-31–J-35 to journey-history and score J-31/J-35 this iteration.
- The epoch anchor is the SAME concept the goal text calls the "additive canonical epoch anchor" / "display anchor" (Key Capabilities #1, #13; Canonical values "Price history & tape-state markers"). Implement it as additive metadata read verbatim by the chart — never as a second timeline the engine bins on.
- Reconciling evidence (iter-3/5/6/7/8/9 lessons): open the actual screenshot bytes; a `browser-qa SKIPPED` plus a working isolated-stack capture is acceptable; treat an idle/placeholder chart shot as NO evidence regardless of a PASS label; hash the evidence dir to detect byte-identical placeholders.
- Remaining after this iteration: J-32 (live speed), J-33 (calibration), J-34 (chunked long windows) — plan as subsequent tight iterations.
