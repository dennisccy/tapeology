# Goal Iteration 21 — Entry checklist with live margins (J-63)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 21
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-63
- **Required-still-passing journeys:** J-53, J-44, J-43, J-42, J-38, J-08, J-02, J-01, J-68 (idle/no-thesis sentinel + byte-identity clause)
- **Anti-goal reminders:**
  - "**No unsolicited or unconditional trade commands.** Every actionable cue MUST be gated on a user-declared thesis with an invalidation, rendered as named checks with margins and evidence, in present-tense descriptive language. No imperative buy/sell/enter/exit wording, no price targets, no certainty language — anywhere. A hint is a logged description of a forming pattern, never a command and never a thesis by itself. *(critical)*"
  - "**No prediction language.** A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do. *(critical)*"
  - "**No naked outputs.** Every published verdict, stance, hint, risk flag, execution check, and grade MUST carry plain-language evidence derived from canonical engine values. A verdict without evidence is a defect. *(critical)*"
  - "**The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested). An observer failure MUST surface explicitly and never kill the feed. *(critical)*"
  - "**No new indicators, no auto-tuning.** Confirmation rules, stances, hints, and studies MUST be composed from the EXISTING engine features and states only; research thresholds are config-owned research defaults calibrated against the sims/fixtures; no parameter optimizer, grid search, or automatic threshold fitting of any kind. *(critical)*"
  - "**Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*"
  - "**Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass… *(critical)*" — **satisfied:** J-58–J-62 all read `passing` in journey-history; the gate is open.

## GOAL

A user with an active, evaluated, not-yet-entry-marked thesis sees the **entry checklist** in the `/` thesis strip: eight named checks each rendering its **live measured margin in its own units** (never a bare boolean), an aggregate stance (`conditions_met | conditions_not_met | tape_against | no_fresh_tape`) publishing through its own dwell, and a **nearest-counterevidence** line — all computed once server-side.

## BACKGROUND

The iter-20 evaluator (CONTINUE, recommend lean) named J-63 the next target: the cue layer is underway (J-53 shipped iter-20 after the evidence gate opened iter-19), and the established rule is **one cue surface per iteration**. J-63 carries the goal's heaviest honesty machinery — blueprint row 25's checklist half plus row 14's `delivery_lag_seconds`, which is registered in the Data Contract but **not yet built** (no occurrence anywhere in `apps/backend` or `apps/frontend`); the `tape_lag_ok` check cannot exist without it, so row 14 ships here as its prerequisite. Depth stays **lean** because the full-pipeline `qa_complete` harness halt remains open (iter-5 lesson); restore full the moment it is fixed.

Lessons that bind this iteration (from `state/lessons.md`):
- **iter-20:** absence/precondition legs MUST be captured on their **exact** precondition, not a look-alike (the "active thesis, no entry mark" leg was substituted with a no-thesis cockpit); derived numerics in captures must be recomputable from in-frame anchors.
- **iter-19:** the **backend stays the validation authority** — no client-side "courtesy disable" may pre-empt a backend 4xx on cue-layer forms; transient states need a designated REST/DOM fallback as primary evidence up front.
- **iter-7/iter-8:** direction-aware rule logic needs **four-quadrant proof** (favorable + adverse tape × long + short), and named numeric truth anchors must appear in the actual test parameters, not just the handoff.
- **iter-9:** when lifecycle/status metadata is needed, name the engine/feeder seam as the legitimate owner **up front** — this spec does (row 14 is feeder-owned in `watch_manager.py`, additive snapshot metadata like iter-9's `end_reason`).
- **iter-6 / iter-2 / iter-18:** browser QA must restart the backend after dev and canary-probe code identity (`GET /research/taxonomy` must serve the new checklist copy); never `npm run build` against the live dev server's shared `.next`.
- **iter-1:** SIM-REVERSAL's phase 2 arrives in ~real time (~60 s logical) — browser QA must budget for it and prefer event-log/timeline assertions for sequence claims.

## IN SCOPE

### Backend

- [ ] **Row 14 — `delivery_lag_seconds` ships (prerequisite for `tape_lag_ok`).** Feeder-owned (`app/watch_manager.py`), surfaced as **additive** snapshot/projection metadata (the iter-9 `end_reason` precedent: engine files may carry it as lifecycle/display metadata only), served by `GET /tape/{ticker}/summary` and the WS frame. Never read by classification — determinism and the observer-equivalence suite stay green with **zero re-pins**. Per-mode honest semantics, documented in the handoff: **live** = latest record's epoch vs wall clock (the goal.md canonical definition); **paced replay (sim/historical)** = the feeder's processing backlog against its own pacing schedule (a replay deliberately hours behind wall clock is NOT "lagging"; a healthy sim reads ≈0). The lag bound is a new config key (e.g. `delivery_lag_ok_bound_seconds`) — a documented research default, no magic number.
- [ ] **Entry-checklist evaluator (row 25 checklist half)** in `app/research/stance.py` — the single row-25 owner module, driven by the research monitor (observer-only; engine untouched). Eight named checks, each composed ONLY of existing canonical values, each carrying pass/fail + its **live measured margin in its own units**:
  1. **verdict confirming** — the current published row-16 verdict (margin = the verdict itself);
  2. **warm** — events processed vs the classifier's own `warmup_min_events` floor (no new threshold);
  3. **feed_live** — the canonical `stream_status` must be `live` (margin = the actual status);
  4. **tape_lag_ok** — row 14's `delivery_lag_seconds` vs the config bound (seconds) — reads the SAME value the future UI lag readout reads (row 14 note);
  5. **spread within the stability domain** — reusing the classifier's own stability gates, in bps (capability-26 precedent: no new threshold);
  6. **trade speed ≥ floor** — reusing the classifier's own gate (events/s);
  7. **invalidation distance ≥ spread multiple** — distance from current last to declared invalidation in spread-multiples vs `invalidation_too_tight_spread_multiple`;
  8. **not chasing** — return from the recorded **`rule_first_true`** price vs `chase_return_threshold` (anchored at `rule_first_true`, never the post-dwell publish).
- [ ] **Aggregate stance** `conditions_met | conditions_not_met | tape_against | no_fresh_tape`: `conditions_met` only when every check passes after confirmation; `conditions_not_met` with the **blocker list** while any check fails (incl. verdict pending); `tape_against` when the published verdict is rejecting; `no_fresh_tape` whenever `feed_live`/`tape_lag_ok` fail (paused/closed/stale/failed) — a previous green MUST NOT persist over non-live data (the full J-64 freshness journey is verified next iteration, but the honest degradation behavior MUST exist now; never ship a frozen green as an intermediate state). Publishes through its **own** config-owned logical-time dwell (new key, documented research default) — no per-tick flapping.
- [ ] **Nearest-counterevidence line** — computed once server-side: names the closest condition that would flip the current read (e.g. the check nearest its boundary when `conditions_met`; the nearest-to-passing blocker when not), with its margin.
- [ ] **Presence rules** (mutually exclusive with the J-53 management stance): active + monitor-evaluating + **no entry mark** → entry checklist; entry-marked + unresolved → management stance (existing, unchanged); no thesis / not-evaluated survivor → NEITHER, each with its distinct honest-absence rendering (no checklist keys served at all on those paths).
- [ ] **Serving:** additive keys on row 15's single `build_projection` (REST `…/thesis/active` == WS `thesis` key **verbatim**). NEVER persisted — schema stays v7, `verdict_events` untouched; no new endpoint, no new route.
- [ ] **Taxonomy (row 24, additive):** check labels + per-check margin captions, the four stance labels + factual evidence templates ("6/8 checks pass" register — present-tense, never imperative or predictive), the nearest-counterevidence template, and the checklist honest-absence copy — all served by `GET /research/taxonomy`; the frontend hardcodes none.
- [ ] **Config + fingerprint discipline:** new keys (checklist stance dwell; delivery-lag bound) are documented research defaults. Default stance: a new key goes **IN** `config_fingerprint`; exclusion is allowed ONLY if genuinely serving-only (the checklist is never persisted — the `management_stance_dwell_seconds` precedent) and MUST follow the codified pattern: documented rationale comment + fingerprint-stability test + counter-test that a real threshold still moves the fingerprint.

### Frontend

- [ ] **ThesisStrip entry-checklist block** (`apps/frontend/components/ThesisStrip.tsx`): shown only on the checklist presence path; renders the stance chip (existing palette semantics: `conditions_met` emerald, `conditions_not_met` slate, `tape_against` rose, `no_fresh_tape` amber), the eight named checks each with pass/fail and its live margin in **mono**, the blocker list when not met, and the nearest-counterevidence line. **Zero client-side arithmetic and zero stance derivation** — margins render verbatim with display rounding only (iter-19/20 discipline); all labels/copy from `GET /research/taxonomy`.
- [ ] **No client-side pre-emption of backend validation** anywhere this block adds interactivity (iter-19 lesson) — the backend stays the validation authority.
- [ ] **Carry-along (evaluator-mandated):** consolidate the three hardcoded `journaled measurement, R = |entry − invalidation|` caption literals at `ThesisStrip.tsx:220/345/633` to read `taxonomy.stance_readout_caption` (already served and typed) — closes the iter-20 coherence advisory.

### New user-facing capability
At the moment of decision — an active thesis being evaluated, before any entry is marked — the user sees whether the tape currently meets the entry conditions, **check by check with live measured margins**, instead of a naked signal.

### New information displayed
Eight named checks with live margins in their own units (verdict, events vs warm-up floor, stream status, lag seconds vs bound, spread bps vs stability cap, trade speed vs floor, invalidation distance in spread-multiples, chase return vs threshold); the aggregate stance with factual "N/8 checks pass" copy; the blocker list; the nearest-counterevidence line; the (server-computed) `delivery_lag_seconds` value now exists in the summary/WS payload.

### New user actions
None — the checklist is display-only (advisory, never blocking; no new buttons or forms).

### UI surface changes
The `/` thesis strip gains the entry-checklist block on the pre-entry-mark path. No new pages, no nav change.

### Product surface delta
The cue layer's second surface: the thesis strip now covers BOTH cue moments — entry (checklist, this iteration) and holding (management stance, iter-20) — each honest, evidence-carrying, and absent on the wrong preconditions.

### Blueprint conformance
J-63's canonical home is pre-registered in the approved IA: `/` thesis strip, nav section Cockpit ("J-63, J-64 (entry checklist / stance + freshness) — built LAST → `/` thesis strip"). No new surfaces, no nav-skeleton change.

### Data-contract additions
No new rows. Build-outs of registered rows (blueprint updated additively this iteration): **row 14** (`delivery_lag_seconds` — feeder owner, served via `/summary` + WS) ships; **row 25** checklist half (checks + margins + stance + nearest-counterevidence — owner `app/research/stance.py`, served via row 15's single `build_projection`) ships; **row 24** gains checklist display copy. The checks read ONLY registered canonical values (row 1 state/verdicts via row 16, row 2 features, row 3 spread/last, row 6 stream status, row 14 lag, row 18 marks, thesis fields) — never a second computation of any contract value.

## OUT OF SCOPE

- **J-64 as a verified journey** — the paused/closed/stale forcing legs, the visible `delivery_lag_seconds` UI readout clause, and the live-lull gated leg are next iteration's journey (the honest `no_fresh_tape` degradation behavior itself IS in scope above; only its dedicated journey verification is deferred).
- J-65 (hint dock / hint log), J-66 (cue-discipline sweep + sound toggle), J-67 (live feed badge) — later cue iterations.
- The long-tail J-01–J-37 partials gating J-68 (J-11/J-14/J-16/J-18/J-20/J-22/J-23/J-27/J-28/J-29/J-32, J-15) — a separate, later effort.
- Any schema change (stays v7), any persistence of checklist/stance values, any engine/classifier rule or threshold change, any new endpoint or route, any sound cue.

## DEFINITION OF DONE

- [ ] Target journey J-63 passes via browser-qa-agent: on SIM-REVERSAL, an absorption_reversal/long thesis declared during the absorption phase shows `conditions_not_met` + blocker list + live margins while pending; flips to `conditions_met` ("8/8 checks pass" register) only after confirmation with every margin rendered; `tape_against` is shown for a rejecting thesis (e.g. trend_continuation/long on SIM-SELLER); the nearest-counterevidence line is present; no per-tick flapping (dwell).
- [ ] Required-still-passing journeys remain green — in particular J-53 (the management stance still renders on the entry-marked path, mutually exclusive with the checklist) and J-68's pixel sentinel (idle + no-thesis cockpit unchanged; observer-equivalence suite green, zero re-pins).
- [ ] No anti-goal violation introduced (copy-lint green over all new strings; no imperative/predictive language; every stance carries evidence; engine byte-identity holds).
- [ ] Unit tests pass; full backend suite green (no regressions); frontend builds.
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-21-dev.md`, documenting the per-mode `delivery_lag_seconds` semantics and the fingerprint decision (in vs excluded, with the pattern evidence) for each new config key.

## TESTING REQUIREMENTS

- **Browser (J-63):**
  - Capture each stance state on its **exact precondition** (iter-20 lesson — no look-alikes): (a) pending/`conditions_not_met` during SIM-REVERSAL's absorption phase, (b) `conditions_met` after the reversal confirms (budget ~60 s real time for phase 2 — iter-1 lesson), (c) `tape_against` on a rejecting thesis, (d) the absence legs: entry-marked thesis shows the management stance and NO checklist; no-thesis cockpit shows neither.
  - Every capture scroll-into-view/full-page with the asserted element visibly in frame (iter-3/4 lessons); margins in captures must be recomputable from in-frame anchors (iter-20 lesson).
  - Restart the backend after dev and canary-probe `GET /research/taxonomy` for the new checklist copy before any capture (iter-6 lesson); do not run `npm run build` against the live dev server's `.next` (iter-2/18 lessons).
  - REST cross-check: `GET /research/thesis/active` checklist keys equal the WS `thesis` key verbatim, and equal what the pixels show.
- **Unit/integration:**
  - Per-check margin computation against **exact numeric anchors stated in the test parameters** (iter-8 lesson), including boundary cases on both sides of each reused gate (warm-up floor, stability spread cap, trade-speed floor, `invalidation_too_tight_spread_multiple`, `chase_return_threshold`, lag bound).
  - **Four-quadrant proof** for the direction-sensitive checks (not-chasing and invalidation-distance: long + short × favorable + adverse), per the iter-7 lesson.
  - Stance aggregation map (every check-combination class → stance), dwell publish/no-flap/lone-flicker, `tape_against` on rejecting, `no_fresh_tape` forced on each non-live status (paused/closed/stale/failed) including from a previously-green `conditions_met`.
  - Presence rules: keys ABSENT with no thesis, on the entry-marked path (management stance present instead), and on the not-evaluated survivor path.
  - REST==WS verbatim test for the new keys (extend the J-08 pattern).
  - Observer-equivalence suite green unchanged (zero re-pins); fingerprint stability + counter test for any excluded serving-only key; copy-lint over all new taxonomy strings.
  - `delivery_lag_seconds`: unit coverage of the per-mode semantics (healthy sim ≈0; a stalled/backlogged feeder reads > 0) without introducing wall-clock into classification.
- **Error cases:** no new write endpoints, so no new 4xx surface — but verify the checklist never renders for an unwatched/404 ticker and that an observer/evaluator exception surfaces as `monitor_status: failed` (never a dead feeder, never a silently-frozen stance).

## NOTES

- **Depth rationale:** lean per the iter-20 evaluator recommendation — the full-pipeline `qa_complete` harness halt (iter-5 lesson) is still open; restore full depth (audit + ux-regression scrutiny for the cue layer) the moment it is fixed.
- **Engine-seam authorization (explicit, iter-9 precedent):** `app/watch_manager.py`, `app/engine/snapshot.py`/`tape_engine.py`, and `app/serializers.py` MAY carry the additive `delivery_lag_seconds` metadata as feeder-owned lifecycle/display data. Classification, features, history, and the observer signature MUST be untouched; the equivalence suite is the proof. No other engine change is authorized.
- **Honesty constraint carried from the invocation:** live margins are computed once server-side; the UI does no arithmetic; the backend stays the validation authority; distinct absence copies per path; config-owned thresholds default INTO the fingerprint unless serving-only with rationale + stability + counter test.
- **Known sweep debt left for J-66 (do not expand scope):** after the caption consolidation above, any remaining hardcoded research copy is J-66 fodder, not this iteration's.
- Blueprint updated additively this iteration (rows 14/24/25 build-out notes + iter-21 IA note + config note); no nav-skeleton change, so no re-approval needed.
