# Goal Iteration 22 — Stance freshness: never a frozen green over a dead tape (J-64)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 22
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-64
- **Required-still-passing journeys:** J-63, J-53, J-47, J-50, J-19, J-08, J-02, J-01, J-68 (idle/no-thesis sentinel + byte-identity clause)
- **Anti-goal reminders:**
  - "**No fabricated data.** The system MUST NOT synthesize trades, quotes, prices, or a tape state to force a green journey. Every real-data failure mode MUST surface an explicit, distinct state and never a cockpit: a provider gap/feed lull → `stale`; … Falling back to simulated or invented data to mask a real-data failure is a defect. *(critical)*" — a served `feed_live: "status live" PASS` over a paused stream is exactly this class of dishonesty.
  - "**Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*" — the fix is a READ of the canonical row-6 `stream_status` / row-14 `delivery_lag_seconds`, never a second computation.
  - "**The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested). An observer failure MUST surface explicitly and never kill the feed. *(critical)*"
  - "**No naked outputs.** Every published verdict, stance, hint, risk flag, execution check, and grade MUST carry plain-language evidence derived from canonical engine values. A verdict without evidence is a defect. *(critical)*"
  - "**No prediction language.** A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do. *(critical)*"
  - "**No unsolicited or unconditional trade commands.** Every actionable cue MUST be gated on a user-declared thesis with an invalidation, rendered as named checks with margins and evidence, in present-tense descriptive language. *(critical)*"

## GOAL

When the watched tape stops being live — paused, stale, closed, or failed — the entry checklist degrades **immediately and visibly** to `no_fresh_tape` (the named `feed_live` / `tape_lag_ok` checks failing with their real margins), a previously green `conditions_met` never persists over non-live data, resume restores honest evaluation, and the canonical `delivery_lag_seconds` readout is visible in the cockpit.

## BACKGROUND

The iter-21 evaluator (CONTINUE, recommend lean) mandated J-64 with a **confirmed live defect** to close: its own REST probe showed that after `POST /watch/SIM-BUYER/pause`, `/summary` reads `stream_status: paused` while `GET /research/thesis/active` still serves `feed_live: "status live" PASS`, `tape_lag_ok PASS`, stance `conditions_met` — a frozen green over a paused tape. Root cause is wiring, not logic: `monitor.py` advances the checklist ONLY in `on_event` and serves `build_checklist` from `_last_snapshot` (captured at the last event); status flips travel via `on_status`, which today handles only the terminal `closed`/`failed` paths and never refreshes the checklist — exactly the seam goal.md capability 20 warns about ("status flips do not pass through events, so stale/closed/failed handling REQUIRES this hook"). The pure evaluator in `stance.py` is already correct (`no_fresh_tape` whenever `feed_live`/`tape_lag_ok` fail, **dwell-exempt** — unit-proven including from a previously-green met); only its inputs/advancement are broken. Depth stays **lean**: the full-pipeline `qa_complete` harness halt remains open (iter-5 lesson); restore full the moment it is fixed.

Lessons that bind this iteration (from `state/lessons.md`):
- **iter-21 (the freshness-wiring lesson, written for exactly this iteration):** freshness/degradation claims need a **feeder-level integration test across an actual status flip** (pause/stale → REST projection re-read) — never evaluator units alone; and QA stance/freshness claims about paused streams must be cross-checked against whether the capture itself was taken paused.
- **iter-20:** absence/freshness states (`no_fresh_tape`, the post-resume read, the post-close removal) MUST each be captured on their **exact** precondition, not a look-alike; derived numerics in captures must be recomputable from in-frame anchors.
- **iter-11:** sim-calibrated thresholds sit razor-thin against the scenarios that must demo them — browser QA should poll REST to TIME the Pause click while `conditions_met` is actually showing (on SIM-BUYER the chase check fails shortly after confirmation as price keeps running; SIM-REVERSAL's post-reversal green is the proven `conditions_met` substrate from iter-21).
- **iter-9:** before declaring engine files out of scope, check whether the canonical status owner must carry anything new — here it does NOT: `stream_status` and `delivery_lag_seconds` already live on the snapshot/feeder; this iteration only READS them at the right moments. Reading current engine state inside `on_status` is the established iter-9 precedent (`engine.end_reason`).
- **iter-18:** never `npm run build` against the live dev server's shared `.next`; browser QA must canary-probe code identity after dev before capturing.

## IN SCOPE

### Backend

- [ ] **Fix the freshness wiring in `app/research/monitor.py`** (the single row-25 owner — no new module, no new endpoint). The served checklist (REST `…/thesis/active` == WS `thesis` key verbatim, via the one `build_projection`) MUST agree with the CURRENT canonical row-6 `stream_status` and row-14 `delivery_lag_seconds` at all times, including across status flips that carry no events:
  - On every `on_status` flip — including the non-terminal `paused` and `stale`, and the restore back to the prior status on resume — the monitor advances the checklist evaluator against current canonical values, so the dwell-exempt `no_fresh_tape` publishes **immediately** (the pure `stance.py` logic is correct and must not be re-derived; fix the call sites/inputs).
  - The served per-check rows (`feed_live`, `tape_lag_ok`) MUST read the current canonical status/lag — not the stale `_last_snapshot` captured at the last event. Acceptable mechanisms (developer's choice, may combine): (a) `on_status` refreshes the monitor's snapshot reference from the engine's current snapshot (the engine/feeder is the canonical row-6/row-14 owner; this is a READ, the iter-9 precedent) and advances the checklist; (b) projection-time `build_checklist` reads the engine's current status/lag. Either way: **no second computation of any contract value, no new serving path.**
  - `on_status` stays exception-isolated (a failure surfaces `monitor_status: failed`, never kills the feeder).
  - **Resume restores honest evaluation:** after `POST …/resume`, `no_fresh_tape` clears and the stance reflects live post-resume evidence; a green `conditions_met` re-publishes ONLY through its existing dwell on fresh evidence — never an instant restoration of the pre-pause green.
  - **Terminal paths unchanged:** `closed`/`failed` keep their existing honest-by-removal behavior (unmarked thesis → `expired(reason)` with the projection cleared; entry-marked → detached not-evaluated with no checklist keys). `_expire_active` / `_detach_not_evaluated` semantics MUST NOT change (J-47/J-50 stay green). The management stance (J-53) is untouched — its enum has no freshness state and pauses are already recorded as row-16 gap events.
  - **Engine, classifier, features, providers untouched.** Observer-equivalence stays byte-identical with **zero re-pins**. No engine metadata is expected this iteration; if a genuine seam need emerges, apply the iter-9 rule (name the canonical owner, additive lifecycle metadata only, never read by classification) rather than working around it.
- [ ] **Feeder-level integration test** (the iter-21 lesson made binding — through the REAL app/WatchManager/status seam, not evaluator units), reproducing the evaluator's probe: watch `SIM-BUYER` → declare `trend_continuation`/`long` → poll the served projection until stance `conditions_met` → `POST /watch/SIM-BUYER/pause` → `GET /research/thesis/active` MUST read stance `no_fresh_tape` with `feed_live` failing and its margin naming the paused status — immediately, no dwell hold → `POST …/resume` → the projection returns to live evaluation (`no_fresh_tape` clears; any green arrives only via the dwell on fresh evidence).
- [ ] **Stale-flip variant** on the same seam: flip the engine's stream status to `stale` via its canonical setter (J-15's real live-lull leg remains operator-gated; this exercises the identical monitor seam) → the served projection degrades to `no_fresh_tape` the same way.
- [ ] **REST == WS verbatim across the flip:** the WS frame at/after the pause flip carries the same degraded checklist as REST (extend the existing verbatim-equality coverage to a status-flip moment).
- [ ] **Closed-leg coverage:** assert (or confirm existing tests assert) that at stream end with an unmarked thesis carrying a green checklist, the thesis expires and the projection clears — no green of any kind persists; the entry-marked variant detaches not-evaluated with no checklist keys.

### Frontend

- [ ] **Visible `delivery_lag_seconds` readout** (row 14 build-out — the readout is pre-registered in the Data Contract): render the served snapshot value in the cockpit's stream-status area (next to the existing status indicator/PAUSED treatment), mono numerics, display rounding only (e.g. "lag 0.1s"). It reads the SAME served value the `tape_lag_ok` check reads (summary/WS snapshot field) — **zero client-side computation, no wall-clock arithmetic in the UI**. Honest absence when the field is null/absent (e.g. before the first record): omit or show an explicit placeholder, never a fabricated 0.
- [ ] **No new strip work expected:** ThesisStrip already renders the `no_fresh_tape` stance (amber) with row-24 taxonomy copy from iter-21 — verify it renders the degraded stance + the failing `feed_live`/`tape_lag_ok` margins verbatim when served. Fix only if a rendering gap surfaces; no client-side derivation may be added.

### New user-facing capability
The moment the tape stops being live, the moment-of-decision read says so: pausing (or a stale feed) flips the checklist to an explicit NO FRESH TAPE with the failing freshness checks named, instead of a frozen green; resuming restores a live, honest read.

### New information displayed
The canonical `delivery_lag_seconds` value, visible in the cockpit beside the stream status; the `feed_live` / `tape_lag_ok` check margins now always reflect the CURRENT stream status and lag, including while paused/stale.

### New user actions
None — Pause/Resume already exist (J-19); this iteration makes the research projection honest across them.

### UI surface changes
The `/` cockpit status area gains the small lag readout. No new pages, no new routes, no nav change.

### Product surface delta
The cue layer's freshness guarantee becomes real end-to-end: the entry checklist can now be trusted at the moment of decision because it provably degrades the instant the tape is not live — closing the gap between the unit-proven evaluator and the served projection.

### Blueprint conformance
No new surfaces. The freshness fix lands in the row-25 owner serving the `/` thesis strip (pre-registered home: "J-63, J-64 (entry checklist / stance + freshness) — built LAST → `/` thesis strip", Cockpit section). The lag readout lands on the `/` cockpit, pre-registered in row 14's notes ("UI lag readout AND the `tape_lag_ok` check read this same value"). Iter-22 build-out notes added to `blueprint.md` (additive — no skeleton change, no re-approval needed).

### Data-contract additions
None. No new value, no new computation, no new endpoint: the iteration READS the registered row-6 `stream_status` and row-14 `delivery_lag_seconds` at the correct moments and ships row 14's already-registered UI readout. Rows 14 and 25 gain additive iter-22 build-out notes in `blueprint.md`.

## OUT OF SCOPE

- J-65 (hint dock), J-66 (cue-discipline sweep), J-67 (live feed badge) — each lands with its own iteration; one cue surface per iteration holds.
- The J-64 **stale leg in a real live browser session** — operator-gated per J-15's pattern (goal.md says so explicitly); covered here by the feeder-level stale-flip integration test, documented as gated (never silently skipped).
- Any change to the pure check/stance evaluator logic in `stance.py` (it is correct and unit-proven) beyond what the wiring fix strictly requires at its call sites.
- Any engine/classifier/feature/provider change; any new config key (the lag bound `delivery_lag_ok_bound_seconds` and the checklist dwell already exist); any schema change (stays v7); any persistence of checklist state.
- The J-68 "J-01–J-37 all green" backlog (J-11/J-14/J-16/J-18/J-20/J-22/J-23/J-27/J-28/J-29/J-32/J-15) — a separate, later effort.

## DEFINITION OF DONE

- [ ] J-64 passes via browser-qa-agent: paused leg (green `conditions_met` → Pause → explicit `no_fresh_tape` with `feed_live` failing, captured while actually paused), resume leg (honest evaluation restored), closed leg (stream end → no green persists), visible lag readout — plus the feeder-level integration tests for the pause, resume, and stale flips.
- [ ] Required-still-passing journeys remain green: J-63 (the checklist's live behavior is unregressed), J-53, J-47, J-50, J-19, J-08, J-02, J-01, J-68 (byte-identity: observer-equivalence green, zero re-pins).
- [ ] No anti-goal violation introduced; no second computation or serving path for any contract value.
- [ ] Full backend suite passes; frontend builds (without touching the live dev server's `.next` — iter-18 lesson).
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-22-dev.md`.

## TESTING REQUIREMENTS

- Browser (J-64):
  1. **Paused leg:** watch a sim that reaches `conditions_met` (SIM-REVERSAL post-reversal is the proven substrate; QA should poll `GET /research/thesis/active` to time the click — iter-11 lesson), capture the green checklist on its exact precondition, click **Pause**, capture the PAUSED cockpit showing the checklist at **NO FRESH TAPE** with the `feed_live` check failing and its margin naming the paused status. The degraded capture MUST itself be taken while paused (iter-21 lesson).
  2. **Resume leg:** click **Resume**, capture the checklist back on live evaluation (a re-green is dwell-gated — accept `conditions_not_met`/`conditions_met` per live evidence; assert `no_fresh_tape` cleared).
  3. **Closed leg:** with an unmarked thesis carrying a green (or any) checklist, let the bounded sim stream end; capture that the thesis reads expired and no checklist/green persists.
  4. **Lag readout:** capture the visible lag value in the cockpit and cross-check it equals the REST `/summary` `delivery_lag_seconds` at the same moment (recomputable-from-anchors discipline, iter-20 lesson).
- Unit/integration:
  - Feeder-level integration test for pause → `no_fresh_tape` (immediate) → resume → honest evaluation (REST projection reads, through the real app/WatchManager seam).
  - Stale-flip variant on the same seam.
  - REST == WS verbatim at/after a status flip.
  - Closed/failed terminal paths unregressed (expire/detach exactly as before — existing tests stay green).
  - Observer-equivalence suite green, zero re-pins (byte-identity clause).
- Error cases:
  - `on_status` failure inside the new wiring surfaces `monitor_status: failed` (exception-isolated, feeder alive).
  - Lag readout with a null/absent `delivery_lag_seconds` renders an honest absence, never `0`.
  - Pause with NO active thesis: no checklist keys appear (presence rules unchanged).

## NOTES

- **Evaluator mandate (iter-21 eval.md):** this scope is verbatim the evaluator's next-step recommendation, including the named reproduction probe and the feeder-level-test requirement. The evaluator listed J-67 as an optional companion; it is deliberately excluded to keep the iteration scoreable on the freshness guarantee alone — freshness is the cue layer's core honesty promise and deserves an undiluted verdict.
- **The pure evaluator is correct — do not rewrite it.** `stance.py` already maps paused/stale/closed/failed/waiting → `no_fresh_tape` dwell-exempt, including from a previously-green met (parametrized unit tests green). The defect is exclusively that `monitor.py` neither advances the checklist on `on_status` nor serves current status/lag at projection time. Keep the fix surgical (core.md: surgical changes).
- **Open harness halt:** the full-pipeline `qa_complete` halt remains open — depth stays lean; restore full when fixed.
- **J-64 verdict basis:** with the stale browser leg operator-gated by goal.md itself, the journey's pass rests on the paused/resume/closed browser legs + the lag readout + the feeder-level integration tests (pause + stale). The evaluator should weigh the integration tests as primary evidence for the stale clause, per the journey's own "*(Pause/closed legs: no credentials, browser-verifiable; the stale leg follows J-15's gated pattern)*" annotation.
