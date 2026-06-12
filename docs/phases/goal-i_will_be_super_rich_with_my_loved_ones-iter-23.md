# Goal Iteration 23 — Setup-forming hints: descriptive, gated, logged (J-65)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 23
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-65
- **Required-still-passing journeys:** J-01, J-04, J-06, J-38, J-51, J-59, J-63, J-64, J-68 (byte-identity clause)
- **Anti-goal reminders:**
  - "**No unsolicited or unconditional trade commands.** Every actionable cue MUST be gated on a user-declared thesis with an invalidation, rendered as named checks with margins and evidence, in present-tense descriptive language. No imperative buy/sell/enter/exit wording, no price targets, no certainty language — anywhere. A hint is a logged description of a forming pattern, never a command and never a thesis by itself. *(critical)*"
  - "**Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass; every hint MUST cite the user's study baseline for its setup/feed or state exactly that none exists. Shipping a buy/sell-adjacent cue with no evidence layer behind it is a defect. *(critical)*" — satisfied: J-58–J-62 are all passing in journey history.
  - "**No naked outputs.** Every published verdict, stance, hint, risk flag, execution check, and grade MUST carry plain-language evidence derived from canonical engine values. A verdict without evidence is a defect. *(critical)*"
  - "**No prediction language.** A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do. *(critical)*"
  - "**No scanning, no execution — still.** Theses and hints exist only on the one watched ticker; studies run only over explicitly chosen windows; there is no background or multi-symbol setup detection, and (re-affirming the first anti-goal) no order placement, routing, simulation of fills, or broker integration."
  - "**The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested). An observer failure MUST surface explicitly and never kill the feed. *(critical)*"
  - "**Source, feed, and config honesty.** Every research record MUST be stamped with its bound source, its `data_feed`, and a `config_fingerprint` over the entire frozen config; a thesis MUST never be evaluated against a different source than it was declared on; analytics and studies MUST NOT pool across feeds or fingerprints; and SIP-derived research MUST NOT be presented as validating IEX-live behaviour without the explicit basis label. *(critical)*"
  - "**No new indicators, no auto-tuning.** Confirmation rules, stances, hints, and studies MUST be composed from the EXISTING engine features and states only; research thresholds are config-owned research defaults calibrated against the sims/fixtures; no parameter optimizer, grid search, or automatic threshold fitting of any kind. *(critical)*"

## GOAL

The cockpit's hint dock shows a descriptive, dwell-gated "setup forming" card on the watched ticker — citing the user's own study baseline or exactly "no studied baseline — unvalidated pattern", prefilling (never creating) a declaration on click — and every shown hint is logged and visible in the journal's hint log.

## BACKGROUND

J-65 is the last unbuilt cue surface (iter-22's evaluator recommendation: one cue surface per iteration has held; J-67 feed badge and the J-66 copy sweep follow). The evidence layer (J-58–J-62) passes, so the "evidence before cues" gate is satisfied. Depth stays **lean** because the iteration adds one observer-driven evaluator + two read endpoints + one dock component + one in-page journal view — and the full-pipeline `qa_complete` harness halt remains open (restore full the moment it is fixed). The `hints` table already exists in schema v7 as a placeholder (`id, ticker, payload, created_wall_ts`); the research monitor attaches per watched ticker at engine creation regardless of thesis, so hints can fire with no thesis declared — exactly what J-65 step 1 requires.

Honesty constraints binding this iteration (from the evaluator's recommendation and goal.md capability 33): hints are descriptive/observational only — never imperative, never a prediction or edge claim; computed once server-side from canonical values; distinct absence copies; config-owned thresholds IN the fingerprint unless genuinely serving-only (then the codified rationale + stability-test + counter-test pattern applies).

## IN SCOPE

### Backend

- [ ] **Hint engine, single owner** — new module `apps/backend/app/research/hints.py` (blueprint row-22 build-out), a pure, deterministic, logical-time evaluator driven by the existing `ResearchMonitor` `on_event` / `on_status` seam (observer-only; NO engine/classifier/feature file touched; runs inside the monitor's existing exception isolation so a hint failure surfaces as `monitor_status: failed`, never a dead feeder).
- [ ] **Patterns — state-native, watched-ticker-only**, composed ONLY of the existing canonical tape state (row 1) + logical time:
  - sustained `bid_absorption` → setup context **absorption_reversal / long**
  - sustained `ask_absorption` → **absorption_reversal / short**
  - sustained `buyer_control` → **trend_continuation / long**
  - sustained `seller_control` → **trend_continuation / short**
  - `unclear` never produces a hint; level setups never produce hints (they have no state-native arming).
- [ ] **Sustain dwell + cooldown, config-owned**: `hint_sustain_dwell_seconds` and `hint_cooldown_seconds` (names final per existing convention) — logical-time, deterministic, documented research defaults, **IN `config_fingerprint`** (they shape persisted hint records — the study-arming-threshold precedent). Calibrate the dwell so SIM-BIDABS fires within a browser-verifiable wait and SIM-CHOP's flapping NEVER sustains past it.
- [ ] **Fire-once record**: when a pattern sustains past the dwell, produce the hint record ONCE — pattern id, plain-language evidence with measured values (e.g. "bid absorption sustained 45 s — sellers being absorbed at the bid"), setup-type context + direction, baseline citation, bound source, `data_feed`, `config_fingerprint`, logical + wall timestamps — and persist it to the existing `hints` table via the single writer queue (schema stays **v7**; the JSON `payload` carries the fields; never written from event processing or the WS serialization path — the established enqueue pattern).
- [ ] **Baseline citation, produced once at fire**: read the user's PERSISTED completed (`done`) studies matching that setup_type + `data_feed` + `config_fingerprint` (excluding `hindsight_level` studies); cite the STORED aggregates verbatim (e.g. n occurrences + ternary outcome vs the seeded null baseline) — never recomputed at read; when none exists the citation is exactly **"no studied baseline — unvalidated pattern"**.
- [ ] **Active-hint lifecycle**: the hint stays active while its pattern's state persists; it clears when the state leaves the pattern, when the watch stops, and on any non-live status flip (paused / stale / closed / failed) — present-tense "is forming" copy must never sit over a non-live tape (the iter-22 J-64 freshness lesson). Clearing never touches the persisted log record. The cooldown gates re-fires of the same pattern on the same ticker.
- [ ] **Serving** (computed once server-side, rendered verbatim):
  - `GET /research/hints/active?ticker=` — the active-hint projection; `hint: null` is a normal state, not an error.
  - The WS frame gains one **additive `hint` key** that MUST equal the REST active-hint projection verbatim (the row-15 `thesis`-key precedent); engine snapshot fields untouched.
  - `GET /research/hints?ticker=&limit=&offset=` — the persisted hint log, rows verbatim (newest first); pagination via the existing journal serving-only page-size config keys or the same codified serving-only pattern.
- [ ] **Declared-from linkage**: `POST /research/thesis` gains an optional additive `declared_from_hint_id`; when present and valid, the created thesis records the link and the hint record is marked declared-from (via the writer queue; the hints table is not append-only-mandated). Unknown/invalid hint id → **422**. The link is recorded only when the user completes a declaration — one click never creates a thesis.
- [ ] **Taxonomy (row 24, additive)**: hint display copy ships via `GET /research/taxonomy` — pattern labels, present-tense evidence templates, the exact "no studied baseline — unvalidated pattern" string, the baseline-citation template, the dock title + "Descriptive only — not trading advice" register line, the declared-from label, hint-log column labels, and the hint-log honest empty-state copy. The frontend hardcodes none of them.

### Frontend

- [ ] **`HintDock` component** on `/` under the tape-state panel (its pre-registered blueprint home): renders the served active hint VERBATIM — pattern + evidence, setup-type context, baseline citation, declare affordance — visible only when a hint is active (no empty-state chrome; the dock simply absent otherwise). Amber/neutral styling per the design system; no sound cue this iteration.
- [ ] **Declare affordance** prefills the thesis strip's declare form (ticker, setup type, direction); `invalidation_price` stays EMPTY and required — the user must type it. Submitting the prefilled form passes `declared_from_hint_id`. The affordance is hidden/disabled while a thesis is already active on the ticker (no dead control producing a 409 — the iter-13 no-dead-control pattern).
- [ ] **`/journal` hint log**: a third in-page view (theses | analytics | hints) — NO new route, NO nav change: rows rendered verbatim (time via the one shared dd-MM-yyyy formatter, ticker, pattern, evidence, baseline citation, declared-from), labels + empty-state copy from taxonomy.

### New user-facing capability
While watching a ticker with a sustained absorption or control tape, the user sees a descriptive "setup forming" card naming the matching setup type with measured evidence and the honest study-baseline context, and can one-click prefill a thesis declaration (still typing the invalidation themselves). Every hint ever shown is reviewable in the journal's hint log.

### New information displayed
The active hint card (pattern, evidence, setup context, baseline citation) in the cockpit's hint dock; the hint log view in `/journal` (time, ticker, pattern, evidence, citation, declared-from).

### New user actions
The hint card's declare affordance (prefills the declare form); the `/journal` view switcher gains a "Hints" option.

### UI surface changes
`/` gains the hint dock under the tape-state panel (visible only when a hint is active); `/journal` gains the hint log in-page view. No new routes, no nav change.

### Product surface delta
The cue layer completes its last unbuilt surface: the cockpit now describes forming tape-native patterns honestly (logged, baseline-cited, never imperative), closing the loop between live observation and the journal/studies evidence layer.

### Blueprint conformance
Both surfaces land at homes pre-registered in the approved IA since baseline: "hint dock (under the tape-state panel)" on `/` (Cockpit) and the "`hint log`" within `/journal` (Journal) — see the J-65 row of the feature-homes table. No new routes, no nav-skeleton change.

### Data-contract additions
Row 22 (Hints) is built out, not added: single computing owner = the hint engine (`app/research/hints.py`, driven by the research monitor); serving = `GET /research/hints/active?ticker=` (== WS `hint` key verbatim) for the dock and `GET /research/hints` for the log — registered in `blueprint.md` this iteration. Row 24 gains hint display copy (same single taxonomy endpoint). No value already in the contract gains a second computation or serving path: tape state is READ from the snapshot the monitor already receives; study baselines are READ from persisted row-23 results; stamps follow row 26.

## OUT OF SCOPE

- The **optional sound cue** (defaults OFF, transition-only, cooldown) — it is part of J-66's acceptance and ships with the J-66 cue-discipline sweep, not here.
- J-66 (copy/anti-imperative sweep + copy-lint test) and J-67 (live feed badge) — their own iterations.
- The J-68 "J-01–J-37 all green" re-verification backlog (only the byte-identity clause is re-verified here).
- Any engine, classifier, feature, provider, or history-buffer change (byte-identity must hold; zero re-pins).
- Any schema migration (stay v7 — the existing `hints` table + JSON payload suffice).
- Hints on unwatched tickers, multi-symbol or background detection, hint push/alerting of any kind.
- Any new chart geometry, any analytics change beyond none (the hint log is its own view; analytics is untouched).

## DEFINITION OF DONE

- [ ] J-65 passes via browser-qa-agent: SIM-BIDABS with no thesis shows the hint card past the dwell (state-descriptive copy, absorption_reversal context, NO imperative and NO direction command, exactly "no studied baseline — unvalidated pattern" on a fresh DB); the declare affordance prefills ticker/setup/direction with invalidation still required and NO thesis created by the click; SIM-CHOP watched at least as long produces NO hint; the shown hint appears in `/journal`'s hint log with its declared-from flag.
- [ ] Required-still-passing journeys remain green (J-01, J-04, J-06, J-38, J-51, J-59, J-63, J-64; J-68 byte-identity clause via the observer-equivalence suite, zero re-pins).
- [ ] No anti-goal violation introduced (in particular: no imperative/prediction language anywhere in the new copy; every hint carries plain-language evidence; stamps on every record).
- [ ] Unit tests pass; full backend suite green; frontend build clean; no regressions.
- [ ] `blueprint.md` row-22/row-24/IA registrations match what shipped.
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-23-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** J-65 (all four acceptance legs: hint shown + copy discipline + citation absence string; prefill-never-creates; SIM-CHOP negative leg; hint log visibility). Re-verify J-01/J-04/J-06 cockpit basics, J-38 declare flow (unprefilled path unchanged), J-51/J-59 journal views, J-63/J-64 checklist surfaces (a hint must coexist correctly with the thesis strip lifecycle).
- **Unit/integration:**
  - Dwell fires deterministically on a sustained matching state at exactly the configured logical-time dwell; flapping/unclear streams NEVER fire; cooldown suppresses a re-fire of the same pattern within the window.
  - Pattern→setup/direction mapping for all four sustained states; `unclear` produces nothing.
  - Citation logic: with a matching persisted `done` study (same setup + feed + fingerprint) the stored aggregates are cited verbatim; with no study / feed mismatch / fingerprint mismatch / `hindsight_level`-only studies the citation is exactly "no studied baseline — unvalidated pattern".
  - Persistence: hint rows written via the single writer queue with bound source + `data_feed` + `config_fingerprint` stamps; the record is created once (no duplicate on continued sustain).
  - REST `GET /research/hints/active` == WS `hint` key verbatim (including `hint: null`); the hint log endpoint paginates and filters by ticker.
  - Declared-from: valid id links thesis and flips the hint record; the prefill path alone creates nothing.
  - Freshness: paused/stale/closed/failed status flips clear the active hint immediately; the log record survives.
  - Observer-equivalence suite green with the hint engine attached (byte-identical snapshots, zero re-pins); hint-engine exception → `monitor_status: failed`, feeder alive.
- **Error cases:** unknown `declared_from_hint_id` → 422; active-hint read on a not-watched ticker → `hint: null` (normal, not an error); malformed pagination params rejected per the existing journal endpoint convention.

## NOTES

- **Lesson applied (iter-22, evidence bookkeeping):** browser-qa MUST checksum the evidence directory and verify each cited capture actually shows the claimed state — iter-22 shipped 5 byte-identical idle frames mis-cited as pass evidence. The React-controlled-input automation failure documented there also applies: drive the ticker input via the documented workaround and verify the cockpit actually populated before capturing.
- **Depth rationale:** evaluator recommended lean; the full-pipeline `qa_complete` harness halt remains open — restore full depth the moment it is fixed.
- **Determinism:** dwell + cooldown are logical-time (the verdict-dwell precedent), so sim journeys are deterministic; no wall-clock in hint decisions (wall ts is a record stamp only).
- **Fingerprint note:** adding the two hint config keys changes `config_fingerprint` by construction (it hashes the entire frozen config) — this correctly segregates new analytics/study records from old ones; it is the designed behavior, not a defect. They stay IN the fingerprint (persisted-record-shaping, the study-arming precedent); no exclusion is requested.
- **Build order honored:** J-58–J-62 pass in journey history, so the "evidence before cues" gate for hints is satisfied; this is the last cue surface, after which only J-66 (sweep), J-67 (badge), and the J-68 backlog remain.
