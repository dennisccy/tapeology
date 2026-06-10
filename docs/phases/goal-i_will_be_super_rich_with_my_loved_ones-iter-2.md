# Goal Iteration 2 — Thesis declaration with honest validation (J-38 + J-39)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 2
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-38, J-39
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-17, J-19, J-21, J-24
- **Anti-goal reminders:**
  - "**The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested). An observer failure MUST surface explicitly and never kill the feed. *(critical)*"
  - "**Journal integrity.** Verdict timelines are append-only: never edited, backfilled, fabricated, or recomputed at read time; nothing is recorded before declaration; gaps (pause, watch restart, stale spans) are explicit events; data-end resolves to an explicit `expired`, never a fabricated outcome; action marks are recorded exactly as the user stated them — never inferred fills. Abandoned theses remain visible in every denominator (no survivorship pruning), and an entry-marked thesis can never be abandoned. *(critical)*"
  - "**Source, feed, and config honesty.** Every research record MUST be stamped with its bound source, its `data_feed`, and a `config_fingerprint` over the entire frozen config; a thesis MUST never be evaluated against a different source than it was declared on; analytics and studies MUST NOT pool across feeds or fingerprints; and SIP-derived research MUST NOT be presented as validating IEX-live behaviour without the explicit basis label. *(critical)*"
  - "**No naked outputs.** Every published verdict, stance, hint, risk flag, execution check, and grade MUST carry plain-language evidence derived from canonical engine values. A verdict without evidence is a defect. *(critical)*"
  - "**No prediction language.** A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do. *(critical)*"
  - "**Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass; every hint MUST cite the user's study baseline for its setup/feed or state exactly that none exists. Shipping a buy/sell-adjacent cue with no evidence layer behind it is a defect. *(critical)*"
  - "**No execution path.** Tapeology MUST NOT place, route, simulate, or recommend orders, and MUST NOT integrate any broker/brokerage or trading API. It only reads and classifies the tape. *(critical)*"
  - "**Persistence stays scoped to research records.** SQLite holds theses, verdict events, hints, actions, reviews, and study results only — no trades, quotes, candles, or feature series are persisted (committed test fixtures excepted)."
  - "**Single source of truth.** Tape state, confidence, and each feature MUST be computed exactly once in the engine and read identically by REST, WebSocket, and the UI; the API and frontend MUST NOT recompute them. The same ticker MUST NOT show different values across views. *(critical)*"
  - "**No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code." (extends to research code per the *Research config defaults* constraint)

## GOAL

A user watching a ticker can declare a thesis (setup × direction × required invalidation) in the new cockpit thesis strip and see it live — frozen expected-behaviour statements with honest statuses and a `pending` verdict — with every incoherent input rejected explicitly (404/409/422), never silently coerced.

## BACKGROUND

This is the keystone research iteration per the evaluator's iter-1 recommendation and the binding build order in `docs/goal.md`: first new API namespace (`/research/*`), first persistence (journal-scoped SQLite), and first frontend research surface (the thesis strip on the cockpit). It builds capability 23 plus the supporting subset of capabilities 28 (store foundation) and the taxonomy endpoint, attaching via the iter-1 observer seam — the verdict ENGINE (transitions, dwell publishing, J-40–J-46) is the NEXT iteration; here the verdict stays honestly `pending`. FULL depth is warranted: cross-cutting backend+frontend+persistence change, UX-regression risk to the cockpit layout (J-01–J-09), and a new data contract that everything later builds on (thesis projection must read verbatim-identical across REST, the WS key, and the strip).

Lessons applied (from `lessons.md`): J-38's browser leg uses `SIM-BIDABS`, whose absorption state is persistent (not a transient phase), so state-panel screenshots are safe; still prefer REST-probe + event-log evidence for sequence/absence claims, capture failure-path evidence (422/409 responses + inline messages) with the server demonstrably up, and have the QA harness kill the frontend dev server by port (`fuser -k`), not by `pkill -f "next dev"`.

## IN SCOPE

### Backend

- [ ] **Research config defaults** in `apps/backend/app/config.py`: env-configured journal DB path (tests inject a temp path via the existing dependency-override pattern) and a `config_fingerprint` function hashed over the ENTIRE frozen config (classifier + research values). No research literal outside config.
- [ ] **Taxonomy module + `GET /research/taxonomy`** — the single backend owner of every research label: setup catalog (`absorption_reversal`, `trend_continuation`, `level_break`, `failed_move_fade`) with per-setup parameter requirements (level REQUIRED for the two level setups, FORBIDDEN otherwise) and expected-behaviour statement templates; direction and verdict enums with display copy. The frontend hardcodes none of these.
- [ ] **Journal store foundation (SQLite, scoped)** — stdlib `sqlite3` only: WAL, `busy_timeout`, `BEGIN IMMEDIATE`, a single writer queue (never written from event processing or the WS serialization path). Create the full versioned schema now (theses, verdict_events, hints, actions, studies, study_occurrences, schema_version); only `theses` + `verdict_events` are written this iteration. The repository exposes NO update/delete on `verdict_events` (append-only at the repository level). No tape data persisted.
- [ ] **`POST /research/thesis`** — `{ticker, setup_type, direction, invalidation_price, level_price?}`. Honest validation, never silent coercion: 404 not-watched; 409 if an active thesis exists on the ticker; 422 for wrong-side invalidation (long ⇒ invalidation below current last; short ⇒ above), missing level for a level setup, level supplied to a non-level setup, unknown enums. On success: freezes the **entry context** (state, confidence, last, spread, primary-window features) and the derived **expected-behaviour statements** at creation; binds the thesis to the **source identity** (the snapshot's scenario descriptor — sim scenario / exact historical window / live SYMBOL, never the bare ticker string); stamps bound source + `data_feed` (`sim | sip | iex`) + `config_fingerprint`; records the initial `pending` verdict event (append-only timeline starts here — nothing recorded before declaration); returns the full thesis projection.
- [ ] **`GET /research/thesis/active?ticker=`** — the canonical REST read of the thesis projection (`thesis: null` is a normal state, not an error). MUST equal the WS frame's `thesis` key verbatim (blueprint row 15).
- [ ] **Research monitor** attached via the iter-1 observer seam (`on_event` / `on_status`), exception-isolated: holds the active thesis per ticker, evaluates the frozen statements' live statuses (met / not-yet / violated) from EXISTING engine states/features only, and serves the projection (thesis fields, statement statuses, verdict — fixed at `pending` this iteration — and `monitor_status`). Read-only over the engine; no engine/classifier/feature/config-threshold change.
- [ ] **Additive WS `thesis` key** on `WS /tape/{ticker}/stream` — same projection as `…/thesis/active`, `null` when none; engine snapshot fields untouched byte-for-byte.
- [ ] **Minimal lifecycle honesty (subset of capability 24, so QA and users are never deadlocked):** stop / stream end / feeder failure auto-resolves an active thesis `expired(reason)` with a final timeline event; a startup sweep resolves any thesis left `active` in the DB to `expired` (no entry marks exist yet, so the survives-with-entry-mark exception is moot and NOT built). Full lifecycle/re-attach (J-47, J-50) is later.
- [ ] **Equivalence re-proof:** extend/re-run `test_observer_equivalence.py` with the REAL research monitor attached (no thesis declared) — engine `serialize_stream`/`serialize_history` projections byte-identical.

### Frontend

- [ ] **Thesis strip** between the price chart and the panel grid on `/` (its blueprint home): idle = a single one-line declare affordance (J-68's strip-idle clause); the declare form is taxonomy-driven (setups, directions, and the level field's presence come from `GET /research/taxonomy` — no hardcoded labels), invalidation price required, with inline validation messages surfaced from backend 422/409/404 responses (nothing created on rejection, no silent coercion or auto-correction).
- [ ] **Active-thesis display**: setup, direction, invalidation in mono, the frozen expected-behaviour statements each with a live status (met / not-yet / violated), the verdict badge (`pending` in slate per the design direction), bound source + `data_feed` stamp, and `monitor_status: failed` surfaced honestly if an observer error occurs. All values read verbatim from the WS `thesis` key / REST projection — the frontend derives nothing.
- [ ] **Copy discipline** (J-66 register, applied from day one): thesis-attributed, present-tense, descriptive strings; no imperative buy/sell/enter/exit, no prediction, no certainty language; the cockpit's "Descriptive only — not trading advice" discipline extends to the strip.

### New user-facing capability
Declare a thesis on the watched ticker and watch the tape get judged against it honestly (starting at `pending`); incoherent declarations are explicitly rejected with on-screen reasons.

### New information displayed
The active thesis (setup, direction, invalidation), frozen expected-behaviour statements with live met/not-yet/violated statuses, the `pending` verdict, bound source + data-feed stamp, monitor status.

### New user actions
Declare-thesis affordance + form (setup select, direction select, invalidation price input, level price input when the taxonomy requires it, submit).

### UI surface changes
One new strip on the cockpit page (`/`), between the chart and the panel grid. No new pages, no nav change — Journal/Studies nav arrives with their pages in later iterations.

### Product surface delta
The cockpit evolves from a pure tape reader into the first decision-support surface: the user's own idea is now a first-class, validated, journaled object judged against the live tape.

### Blueprint conformance
All surfaces live under the existing **Cockpit (`/`)** home — exactly the blueprint's thesis-strip placement (IA row "J-38–J-46, J-49, J-50, J-52, J-53 → `/` thesis strip"). No nav-skeleton change; no reapproval needed.

### Data-contract additions
None — this iteration ACTIVATES already-registered rows: **15** (thesis projection — research monitor → `GET /research/thesis/active`, WS `thesis` key verbatim-equal), **16** (verdict timeline — initial `pending` + `expired` events only this iteration), **24** (taxonomies → `GET /research/taxonomy`), **26** (source / data_feed / config_fingerprint stamps). Row 17 (entry risk flags) is NOT built yet (J-49). Never compute or fetch any registered value via a second path — the strip reads row 15 only.

## OUT OF SCOPE

- Verdict transition engine (confirming/weakening/rejecting/invalidated), per-setup dwell, `rule_first_true` — next iteration (J-40–J-46); the verdict stays `pending` here.
- Entry risk flags (J-49): omit the computation AND the projection field entirely until J-49 builds it — an always-empty `risk_flags: []` would dishonestly read as "no risks found".
- Resolve/abandon endpoints and strip controls (J-50), action marks (J-52), management stance (J-53).
- Thesis geometry on the chart (J-48 — invalidation/level price-lines, verdict marks).
- `/journal` and `/studies` pages, top-bar nav links, hint dock, analytics, excursions, studies, checklist/stance (cues are LAST, after J-58–J-62).
- Restart persistence/re-attach journeys (J-51, J-47) — the store persists by nature, but those journeys are verified later; the startup sweep above is the only restart behavior built now.
- Any engine, classifier, feature, or existing-config-threshold change; any new market indicator.

## DEFINITION OF DONE

- [ ] Target journeys J-38, J-39 pass via browser-qa-agent
- [ ] Required-still-passing journeys (J-01–J-09, J-17, J-19, J-21, J-24) remain green; thesis strip idles as a single declare affordance with nothing else moved (J-68 strip-idle clause — re-evaluate J-68)
- [ ] No anti-goal violation introduced (equivalence test with the real monitor attached passes byte-identical)
- [ ] Unit tests pass; no regressions (backend suite ≥ iter-1's 292 passed / 1 skipped, plus this iteration's new tests)
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-2-dev.md`

## TESTING REQUIREMENTS

- Browser:
  - **J-38** — watch `SIM-BIDABS`, declare absorption_reversal / long / invalidation below last via the strip; assert ACTIVE thesis with setup/direction/invalidation (mono), statements each showing a live status, verdict `pending`, no page reload; assert `GET /research/thesis/active?ticker=SIM-BIDABS` equals the WS frame's `thesis` key verbatim (REST probe, server demonstrably up).
  - **J-39** — unwatched ticker → 404; wrong-side invalidation → inline message + 422 and nothing created; `level_break` without level → 422; `absorption_reversal` with level → 422; valid declare then second declare → 409 with explicit message. Capture response evidence, not only screenshots.
  - **J-68 strip-idle leg** — with no thesis declared, the cockpit (J-01 flow) renders identically except the one-line declare affordance; spot-check J-17 (chart) and J-19 (pause/resume).
  - Required-still-passing spot checks: J-01–J-09, J-17, J-19, J-21, J-24.
- Unit/integration:
  - Full validation matrix for `POST /research/thesis` (404 / 409 / each 422 case, both directions for wrong-side invalidation); nothing persisted on rejection.
  - Frozen entry context + statements (a config change after creation never rewrites them); source binding (scenario descriptor, not bare ticker); `data_feed` + `config_fingerprint` stamps (fingerprint stable across runs, changes when any config value changes).
  - Journal store: WAL + writer-queue discipline, temp-path injection, schema_version present, repository exposes no update/delete on `verdict_events`.
  - Initial `pending` event recorded at creation; stop/stream-end → `expired(reason)` final event; startup sweep resolves stale actives.
  - WS `thesis` key == `…/thesis/active` projection verbatim; snapshot keys unchanged with the monitor attached (extended equivalence test, benign + real monitor + throwing observer).
- Error cases: wrong-side invalidation (long above / short below), missing level for level setups, forbidden level for non-level setups, unknown setup/direction enums, unwatched ticker, duplicate active thesis, observer exception → `monitor_status: failed` with feed alive.

## NOTES

- Evaluator iter-1 explicitly recommended this scope at FULL depth (`runs/goal-session-i_will_be_super_rich_with_my_loved_ones/iter-1/eval.md`, Next-Step Recommendation); coherence was PASS, no consolidation debt.
- J-68 cannot fully pass this iteration (its "J-01–J-37 all green" clause awaits 11 still-partial journeys) — the deliverable here is its strip-idle clause; the evaluator decides its status.
- The statement-status evaluator composes EXISTING engine states/features only (no new indicators, no auto-tuning); statuses are projection-level (in-memory, recomputed per event by the monitor) — only the thesis row and timeline events are persisted.
- Writer-queue discipline matters because the monitor runs inside the engine's observer callbacks: persistence writes MUST be queued off the event-processing path, never block the feeder, and an SQLite failure must surface as `monitor_status: failed` — never kill the feed, never silently drop a record.
- QA harness: budget for SIM-BIDABS warm-up before declaring (the strip needs a populated cockpit); kill the dev frontend by port per the iter-0 lesson.
