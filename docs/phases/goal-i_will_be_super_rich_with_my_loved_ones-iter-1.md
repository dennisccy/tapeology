# Goal Iteration 1 — Research foundation: engine observer seam (J-68 equivalence) + SIM-SHIFT / SIM-REVERSAL scenarios

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 1
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-68
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-17, J-19
- **Anti-goal reminders:**
  - "**The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested). An observer failure MUST surface explicitly and never kill the feed. *(critical)*"
  - "**Deterministic & reproducible.** Given the same ordered event stream (and seed), the engine MUST produce identical features, state, and confidence; classification MUST NOT depend on wall-clock time or randomness. Each simulated scenario MUST have an automated test asserting the expected state is reached with reasonable confidence."
  - "**Price impact over raw aggression.** The classifier MUST distinguish absorption from control: a tape with high one-sided aggression but no corresponding price progress MUST resolve to the matching absorption state (bid_absorption / ask_absorption), never to seller_control / buyer_control. Keying on aggression ratios alone is a defect. *(critical)*"
  - "**No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code."
  - "**Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass; …" — nothing cue-adjacent may appear this iteration.

## GOAL

Lay the research evolution's foundation: the engine exposes an exception-isolated snapshot-observer seam proven byte-identical-when-attached (the J-68 equivalence test), and two new deterministic sim scenarios — `SIM-SHIFT` and `SIM-REVERSAL` — become watchable in the existing cockpit.

## BACKGROUND

The iter-0 baseline confirmed all 31 research-evolution journeys (J-38–J-68) are unbuilt while J-01–J-37 are healthy. The iter-0 evaluator recommended exactly this scope at lean depth: capability 20 (the observer seam — the only sanctioned attachment point for everything research; its equivalence test is the automated core of J-68) and capability 21 (the two new provider-level scenarios that J-40, J-43, J-46, and J-53 will need once the verdict engine exists). Building the seam *before* any research feature means every later iteration attaches to a proven-inert hook instead of retro-fitting one. This is engine-adjacent but additive and narrow — one seam, two provider streams, no API or frontend change — so lean is sufficient.

Iter-0 lesson (applies here — this iteration's browser QA starts/stops the dev servers): absence/presence claims must be evidenced with the server demonstrably up (REST probes or file-tree inspection, never an ERR_CONNECTION_REFUSED screenshot); recount QA summary numbers from the results table; and kill the frontend dev server by port (`fuser -k`) — the `next dev` reloader child survives `pkill -f "next dev"`.

## IN SCOPE

### Backend

- [ ] **Observer seam on `TapeEngine`** (`apps/backend/app/engine/tape_engine.py`, capability 20):
  - A generic observer registration (e.g. `add_observer(...)`) holding a list of observer objects with two callbacks: `on_event(event, snapshot)` invoked at the END of every `process_event` (after the snapshot rebuild), and `on_status(status)` invoked on EVERY stream-status change. Status flips do not pass through events, so `on_status` MUST fire from every status writer: `set_stream_status`, `pause`, `resume`, and the internal `connecting/waiting → live` flip inside `process_event`.
  - **Exception isolation:** an observer raising MUST NOT propagate — the error is logged, the failing observer is marked failed (a per-observer failed state the future research monitor can read to surface `monitor_status: failed`; no research projection is built this iteration), and event processing/feeding continues unchanged.
  - **Engine stays research-agnostic:** no research imports, no research types in the engine; observers are opaque callables/objects against the seam. Nothing attaches an observer in production code this iteration — only tests attach.
- [ ] **J-68 equivalence test** (new `apps/backend/tests/test_observer_equivalence.py`): replay a fixed, seeded event stream (reuse the existing scenario streams per `test_scenario.py` conventions) through two engines — observers attached vs absent — and assert **byte-identical** outputs: serialized snapshot projections (state, confidence, features, quote/last, observations/event log) and the serialized history projection (OHLC bars + markers) compare equal at every assertion point, including final. One leg attaches a deliberately-throwing observer and asserts (a) processing completes, (b) outputs remain byte-identical to the no-observer run, (c) the failure is recorded/logged — never swallowed silently.
- [ ] **`SIM-SHIFT` scenario** (`apps/backend/app/providers/simulated.py`, capability 21): a sustained buyer-control phase, then an unclear/chop phase whose price band dips below the late-control price. Provider-level only (engine untouched), seeded and deterministic, registered in `SIM_SCENARIOS`, shape constants documented as scenario DATA in the existing style. Drives weakening-after-confirmation (J-43), stance decay (J-53), and clean-process invalidation deterministically in later iterations.
- [ ] **`SIM-REVERSAL` scenario** (same module): a bid-absorption phase at a held price, then a buyer-control phase that lifts price above the absorbed level. Same conventions. Drives the absorption-reversal happy path (J-40) and failed-move-fade confirmation (J-46) later.
- [ ] **Scenario tests** (extend `apps/backend/tests/test_scenario.py` patterns): for each new scenario, assert the deterministic phase **sequence** on the engine — SIM-SHIFT reaches `buyer_control` (confidence ≥ the configured reasonable threshold) then transitions to `unclear`, with the chop-phase price band dipping below the late-control price; SIM-REVERSAL reaches `bid_absorption` (not seller_control — the price-impact discipline) then `buyer_control` with last lifted above the absorbed price. Plus a determinism test per scenario (same seed ⇒ identical stream/state trace), mirroring the existing five.

### Frontend (if applicable)

None. The cockpit's free-text ticker input already watches any registered sim ticker; SIM-SHIFT and SIM-REVERSAL are immediately watchable with zero UI change. No thesis strip, no nav, no new page this iteration.

### New user-facing capability

The user can watch `SIM-SHIFT` and `SIM-REVERSAL` in the existing cockpit and observe, live, a tape that *changes regime*: SIM-SHIFT resolves to buyer_control then honestly decays to unclear; SIM-REVERSAL shows sellers being absorbed (bid_absorption, not seller_control) and then buyers taking control with real upward price progress.

### New information displayed

No new value types — the existing cockpit panels (state, confidence, features, observations, event log, chart) display the two new scenarios' regime transitions, e.g. "Tape state changed to buyer_control" followed later by "Tape state changed to unclear" (SIM-SHIFT).

### New user actions

None (existing Watch flow with two new valid sim tickers).

### UI surface changes

None.

### Product surface delta

The cockpit gains two new deterministic, watchable scenarios that exercise regime *transitions* (the first sims that deliberately change state mid-stream); under the hood the engine gains the inert, equivalence-proven research attachment seam that every subsequent research iteration will use.

### Blueprint conformance

No new surfaces. The new scenarios live in the existing **Cockpit (`/`)** home (J-01–J-37 row of the blueprint's feature-home table). The observer seam and both scenarios are already registered in the blueprint ("New for this session" governing principle and the "New sim scenarios" paragraph) — no blueprint edit required.

### Data-contract additions

None. No new displayed value: the new scenarios flow through existing rows 1–6 and 10 (state/confidence, features, quote/last, trades, observations, stream status, OHLC + markers). The observer seam exposes nothing to the UI this iteration. Row 14 (`delivery_lag_seconds`) is capability 22 — explicitly NOT this iteration.

## OUT OF SCOPE

- Any research feature proper: no thesis endpoints, no verdict engine, no taxonomy, no SQLite store, no `/journal` or `/studies`, no thesis strip, no nav bar (J-38+ come next iterations).
- No research monitor / research projection / `monitor_status` surface — only the engine-side per-observer failed state it will later read.
- No `delivery_lag_seconds`, no live-chart epoch-anchor work (capability 22).
- Nothing cue-adjacent (J-63–J-67) — binding build order: evidence (J-58–J-62) first.
- No changes to the classifier, features, config thresholds, existing five scenarios, API surface, or frontend.
- No fix attempts for the iter-0 partial journeys (J-11/J-14/J-16/J-18/J-20/J-22/J-23/J-27/J-28/J-29/J-32) — separate, later scope.

## DEFINITION OF DONE

- [ ] Target journey J-68's automated core passes: the observer-equivalence test asserts byte-identical snapshots + history with observers attached vs absent, including the throwing-observer leg (see NOTES on J-68's remaining thesis-strip clause).
- [ ] `SIM-SHIFT` and `SIM-REVERSAL` are registered, seeded, deterministic, and each has automated tests asserting its phase sequence and determinism; both are watchable in the cockpit via browser.
- [ ] Required-still-passing journeys remain green: browser re-verifies J-01/J-02 (SIM-BUYER cockpit), spot-checks J-17 (chart) and J-19 (pause/resume); the full backend suite (283 passing pre-iteration) still passes with zero regressions.
- [ ] No anti-goal violation introduced — in particular the engine remains research-agnostic and byte-identical with observers attached.
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-1-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-68 spot-flows — watch `SIM-BUYER` and confirm the J-01/J-02 cockpit is pixel-for-pixel behaviorally unchanged (panels, state buyer_control with confidence ≥ threshold, transition message); spot-check J-17 (chart renders candles + markers) and J-19 (pause/resume). Then watch `SIM-SHIFT` and capture the buyer_control read AND the later unclear read (two screenshots + event-log transition messages); watch `SIM-REVERSAL` and capture the bid_absorption read (high sell aggression, ~zero downward impact — absorption, NOT seller_control) AND the later buyer_control read with a lifted last price.
- Unit/integration: the observer-equivalence test (byte-identical serialized snapshot + history projections; assertion points during and at end of stream); observer exception-isolation (throwing observer → processing continues, outputs identical, failure recorded + logged); `on_status` fires for every status writer (`set_stream_status`, pause, resume, and the internal connecting→live flip); SIM-SHIFT and SIM-REVERSAL phase-sequence + determinism tests in the `test_scenario.py` style.
- Error cases: an observer raising in `on_event` AND in `on_status` must be isolated (logged + marked failed, feed alive, snapshots unchanged); an unknown sim ticker must still be rejected exactly as today (no accidental loosening while registering the two new tickers).

## NOTES

- **J-68 status honesty:** J-68's full acceptance also says "the thesis strip idles as a single declare affordance" — the strip does not exist yet (it ships with J-38). This iteration delivers J-68's automated equivalence test and the unchanged-cockpit browser legs; the strip-idle clause becomes verifiable once the strip exists. The evaluator owns the call on whether J-68 reads passing or partial until then; the spec claims only what is built.
- **Why the sims now:** SIM-SHIFT/SIM-REVERSAL flip no journey by themselves (J-40/J-43/J-46/J-53 need the verdict engine), but they are deterministic prerequisites and are independently browser-demonstrable as cockpit regime transitions — per the iter-0 evaluator's explicit recommendation.
- **Byte-identical meaning:** compare the serialized projections (the same serializer REST/WS uses, plus the history projection), not Python object identity — that is the form the anti-goal and J-68 specify and what later research attachment must preserve.
- **Critical guard (project-template note):** the buyer_control rule REQUIRES positive `buy_price_impact` and has a negative guard test — SIM-REVERSAL's control phase must earn confirmation through real price progress, never by relaxing the rule.
- **Harness lesson (iter-0):** kill the frontend dev server by port (`fuser -k`), not `pkill -f "next dev"`; never capture evidence against a downed server; recount QA results from the table, not the summary line.
- **Next up (for context, not scope):** thesis declaration + honest validation (J-38/J-39) with the taxonomy endpoint, then the verdict-engine journeys — the build order in `docs/goal.md` and the blueprint is binding.
