# Goal Iteration 4 — Verdict-transition engine (J-40–J-46) + thesis-strip visual-evidence debt (J-38/J-39)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 4
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-38, J-39, J-40, J-41, J-42, J-43, J-44, J-45, J-46
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-17, J-19, J-21, J-24
- **Anti-goal reminders:**
  - "**No prediction language.** A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do. *(critical)*"
  - "**No naked outputs.** Every published verdict, stance, hint, risk flag, execution check, and grade MUST carry plain-language evidence derived from canonical engine values. A verdict without evidence is a defect. *(critical)*"
  - "**Journal integrity.** Verdict timelines are append-only: never edited, backfilled, fabricated, or recomputed at read time; nothing is recorded before declaration; gaps (pause, watch restart, stale spans) are explicit events; data-end resolves to an explicit `expired`, never a fabricated outcome; action marks are recorded exactly as the user stated them — never inferred fills. Abandoned theses remain visible in every denominator (no survivorship pruning), and an entry-marked thesis can never be abandoned. *(critical)*"
  - "**The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested). An observer failure MUST surface explicitly and never kill the feed. *(critical)*"
  - "**No new indicators, no auto-tuning.** Confirmation rules, stances, hints, and studies MUST be composed from the EXISTING engine features and states only; research thresholds are config-owned research defaults calibrated against the sims/fixtures; no parameter optimizer, grid search, or automatic threshold fitting of any kind. *(critical)*"
  - "**Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass; every hint MUST cite the user's study baseline for its setup/feed or state exactly that none exists. Shipping a buy/sell-adjacent cue with no evidence layer behind it is a defect. *(critical)*"
  - "**No magic numbers.** Every window length, threshold, large-print size, impact/absorption cutoff, and confidence boundary MUST come from config — no such literal in engine/classifier code." (extends verbatim to every research value per the Research-config-defaults constraint)

## GOAL

The declared thesis is judged live by the tape: the verdict engine publishes `pending → confirming / weakening / rejecting / invalidated` with plain-language evidence, an append-only timeline, dwell-honest timing, and a hard robust invalidation trigger — visible on the thesis strip with screenshot evidence that finally, provably contains the strip.

## BACKGROUND

Iter-3's evaluator returned **ESCALATE**, mandating this exact scope at FULL depth: (1) the verdict-transition engine — all prerequisites are in place (SIM-SHIFT/SIM-REVERSAL from iter-1; thesis declaration, statements, monitor observer seam, SQLite store with append-only `verdict_events` from iter-2; backend suite green at 332/1) — and (2) the visual-evidence debt: across three iterations not one screenshot has actually contained the thesis strip (all viewport-top captures with the strip below the fold), so J-38/J-39 and the J-68 strip-idle clause sit `partial` on DOM-read-only claims. Nine target journeys exceed the usual 1–3, but J-40–J-46 are facets of ONE module (a per-setup rule table over existing engine values) and J-38/J-39 need zero new code — only correctly-framed captures of surfaces this iteration renders on anyway. The full pipeline's audit/closure gates are precisely what the lean loop lacked when it twice passed evidence that showed nothing.

**Lessons in force** (from session lessons.md): SIM-SHIFT/SIM-REVERSAL pace phase 2 ~60s logical — browser QA must budget for the phase shift and capture event-log/timeline records for sequence claims, since a transient phase can be missed by a single screenshot (iter-1). Isolate any frontend build from the live dev server's `.next` (`NEXT_DIST_DIR=.next-qa`); an all-SKIP browser run means "frontend unverified" and a dead frontend is a FAIL, not a SKIP (iter-2). **Binding evidence rule (iter-3): every thesis-strip assertion must be backed by a capture that visibly contains the strip — scroll the asserted element into view or take a full-page screenshot before every capture.** Recount QA results from the table, not the summary line; distrust step self-reports of "Frontend Present: no" — this spec says yes.

## IN SCOPE

### Backend

- [ ] **Verdict-transition engine** (new module under `apps/backend/app/research/`): a pure per-event evaluator invoked from the existing `ResearchMonitor.on_event` seam, mapping each engine snapshot to a raw verdict via **config-owned, per-setup rule tables** composed ONLY of existing tape states/features. Per-setup semantics:
  - **absorption_reversal** — confirms on the REVERSAL (flip to matching control with real price impact), never on sustained absorption alone (premise statements read met; trigger reads not-yet) — J-40.
  - **trend_continuation** — confirms while matching control + impact hold; an opposing control tape publishes **rejecting** with evidence citing the opposing control/impact; rejecting is a judgement, not a resolution (thesis stays active) — J-41/J-42.
  - **level_break** — a latch: no confirmation however strong control is until last crosses the declared level; once latched + control holds, confirming citing cross + control — J-45.
  - **failed_move_fade** — the deliberate asymmetry with J-40: the absorption of the break IS the expected behaviour and reads confirming; the reclaim keeps it confirming; rejecting requires real opposite follow-through — J-46.
- [ ] **Dwell + timing record**: per-setup **logical-time** dwell (restarting at thesis creation, so confirmation requires post-declaration evidence by construction); every published transition records **`rule_first_true`** (first logical instant + price the raw rule held) and **`published_at`**; the published verdict never flaps per tick.
- [ ] **Confirmed → weakening rule**: once confirmed, fading evidence (tape going neutral/unclear) publishes **weakening** after its dwell — never a silent return to `pending` — with distinct "supporting evidence faded" register — J-43.
- [ ] **Invalidation trigger (dwell-exempt, robust, system-owned)**: a print beyond the declared invalidation by ≥ the configured spread-multiple ε, OR k consecutive prints beyond it (a lone bad print inside the guard does NOT invalidate), flips the verdict to **invalidated** immediately and **auto-resolves** the thesis `invalidated` via the existing store path, with the offending print price + logical timestamp recorded as evidence — J-44. (This is internal monitor logic — NOT the user-facing resolve endpoint, which stays out of scope.)
- [ ] **Append-only timeline**: each published transition is appended to `verdict_events` via the existing single-writer repository (`logical_ts, wall_ts, verdict, evidence, tape_state, confidence, last, rule_first_true`); a config-owned timeline cap; never recomputed at read time.
- [ ] **Minimal `GET /research/journal/{id}`** — the blueprint row-16 registered serving endpoint: returns the thesis record + its persisted verdict timeline verbatim (404 unknown id). Minimal projection only — no list endpoint, no analytics, no review fields.
- [ ] **Config (research defaults, documented)**: per-setup verdict dwell, invalidation ε spread-multiple, k-consecutive count, timeline cap — all in `app/config.py` (they enter the existing `config_fingerprint` automatically since it hashes the entire frozen config); no literals in research code.
- [ ] **Evidence strings**: present-tense, descriptive, thesis-attributed, derived from canonical snapshot values (e.g. "buyers took control with real upward impact (buy_price_impact +0.0042)") — no imperative/predictive/certainty language.

### Frontend (if applicable)

- [ ] **ThesisStrip verdict rendering**: render the live verdict with its evidence line using the established semantics — `confirming` emerald, `weakening` amber, `rejecting` rose, `invalidated` rose with a terminal treatment, `pending` slate — labels/display copy from `GET /research/taxonomy` (row 24; hardcode none). The strip already reads the projection via the WS `thesis` key — no new read path.
- [ ] **Terminal invalidated state**: when the thesis auto-resolves `invalidated`, the strip shows the terminal treatment (resolved, with the offending evidence) rather than silently reverting to the idle declare affordance.
- [ ] No new pages, no chart changes (thesis geometry is J-48, a later iteration).

### New user-facing capability
The user's declared thesis is now continuously judged against the live tape: they can watch the verdict move from pending to confirming/weakening/rejecting, see plain-language evidence for every transition, and have a print through their invalidation hard-resolve the thesis — all on the existing thesis strip.

### New information displayed
Live verdict state + evidence sentence on the thesis strip; terminal invalidated treatment with the offending print; the full append-only verdict timeline via `GET /research/journal/{id}`.

### New user actions
None (declaration already exists; verdicts are system-published; the resolve/mark controls are J-50/J-52, later).

### UI surface changes
Thesis strip only: verdict chip/section gains the four non-pending states with the extended color semantics and evidence line; terminal treatment on invalidation. Cockpit otherwise unchanged.

### Product surface delta
The thesis strip stops being a static record and becomes the live confirmation readout — the core of pillar 2 (tape confirmation). The product can now answer "is the tape confirming, weakening, or rejecting my thesis right now, and where is it invalidated?" on deterministic sims, identically wired for real data.

### Blueprint conformance
No new surfaces. Everything renders on the existing Cockpit home (`/` thesis strip), the registered home for J-38–J-46 in `blueprint.md`. The timeline is served by the row-16 registered endpoint `GET /research/journal/{id}`.

### Data-contract additions
**None.** All values this iteration produces are already registered: thesis projection incl. verdict + evidence = row 15 (read via WS `thesis` key / `GET /research/thesis/active` — the strip keeps its single existing read path); published verdict timeline = row 16 (this iteration implements its registered owner — verdict engine → journal repository — and its registered endpoint); verdict display copy = row 24 (`/research/taxonomy`); stamps = row 26. Do NOT introduce any second computation or serving path for any of these.

## OUT OF SCOPE

- J-48 thesis geometry on the chart (level/invalidation price-lines, verdict marks) — next iteration. Note: J-45's parenthetical "level line visible on the chart" clause is explicitly deferred with it; J-45 is targeted on its latch/verdict acceptance.
- J-49 entry risk flags; J-50 resolve endpoint + strip resolve controls (`played_out`/`abandoned`); J-52 action marks; J-53 management stance.
- `/journal` page, review, grading, mistake tags (J-51, J-54–J-57); excursions/analytics/studies (J-58–J-62).
- ALL cue surfaces — entry checklist, stance, hints, sounds (J-63–J-67): hard-gated behind J-58–J-62 by the Evidence-before-cues anti-goal.
- Gap events for pause/stale spans on the timeline beyond what the existing monitor status handling already records — the full gap-event vocabulary belongs to J-47/J-51.
- Any engine/classifier/feature/provider change. The engine is untouched; the verdict engine composes existing snapshot values only.

## DEFINITION OF DONE

- [ ] Target journeys J-40, J-41, J-42, J-43, J-44, J-45, J-46 pass via browser-qa-agent on their named sim scenarios (J-45 on its latch/verdict acceptance; chart-line clause deferred to J-48).
- [ ] J-38 and J-39 flip: their flows re-run with **screenshots that visibly contain the thesis strip** (active-thesis render for J-38; inline 422 message + preserved form values for J-39). The J-68 strip-idle declare affordance is likewise captured visibly.
- [ ] **Binding evidence rule honored on every capture:** the asserted element is scrolled into view (or the capture is full-page) — a viewport-top capture of a below-the-fold surface is a FAIL of the evidence requirement, not a soft note.
- [ ] Required-still-passing journeys (J-01–J-09, J-17, J-19, J-21, J-24) remain green.
- [ ] Observer-equivalence tests still pass: engine outputs byte-identical with an active thesis being verdict-evaluated vs no research layer.
- [ ] No anti-goal violation introduced (no prediction/imperative copy anywhere in evidence strings; no naked verdicts; timeline append-only; no magic numbers).
- [ ] Unit tests pass; no regressions in the existing backend suite.
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-4-dev.md`.

## TESTING REQUIREMENTS

- Browser (Chrome MCP, no credentials needed — all deterministic seeded sims; **stop the watch between journeys** so the active thesis auto-expires and re-declaration never 409s; budget ~60s logical for SIM-SHIFT/SIM-REVERSAL phase 2, and prefer event-log/timeline assertions for transient phase-sequence claims):
  - **J-40**: SIM-REVERSAL, declare absorption_reversal/long during absorption → verdict stays pending with premise met / trigger not-yet through sustained absorption; confirming (with flip-citing evidence) only after buyer_control phase; timeline holds `rule_first_true` + `published_at`.
  - **J-41**: SIM-SELLER, trend_continuation/long, far invalidation → rejecting with seller-control evidence; thesis stays active.
  - **J-42**: SIM-BUYER, trend_continuation/long → confirming after dwell; stays confirming (no flapping).
  - **J-43**: SIM-SHIFT, trend_continuation/long during control → confirming, then weakening after the shift (post-dwell), never a silent return to pending; both transitions on the timeline.
  - **J-44**: SIM-SELLER, any long with invalidation just below last → invalidated immediately on the qualifying print, thesis auto-resolved, terminal strip treatment, offending print + logical ts in the final timeline entry.
  - **J-45**: SIM-BUYER, level_break/long with level above current last → pending pre-cross (cross statement not-yet) despite control; confirming after latch + control.
  - **J-46**: SIM-REVERSAL, failed_move_fade/long during absorption → confirming DURING the absorption; remains confirming through the reclaim.
  - **J-38/J-39 re-run** with correctly framed captures (strip visible in pixels); REST `…/thesis/active` cross-checks as before.
- Unit/integration (pytest, deterministic unpaced replays through engine + monitor):
  - One test per setup type asserting the J-40/J-42/J-45/J-46 verdict sequences on the seeded scenario streams, including the J-40 trap (sustained absorption alone NEVER confirms absorption_reversal) and the J-45 latch (no confirm pre-cross).
  - Confirmed→weakening (J-43) and rejecting (J-41) sequences with their evidence registers.
  - **Invalidation robustness with a synthetic outlier print**: a lone print inside the ε·spread guard does NOT invalidate; ≥ε single print and k-consecutive both do; auto-resolution recorded; dwell-exemption asserted.
  - Dwell: a rule that holds pre-declaration does not confirm until it holds post-declaration through the dwell; `rule_first_true` ≠ `published_at` recorded correctly.
  - Repository: timeline rows append-only (no update/delete path), cap enforced, `GET /research/journal/{id}` serves persisted rows verbatim + 404 unknown id.
  - Observer equivalence re-asserted with verdict evaluation active.
- Error cases: unknown journal id → 404; all existing declaration validation (404/422/409 matrix) unchanged and re-asserted; no verdict event ever recorded before declaration.

## NOTES

- **Escalation context:** prior verdict ESCALATE ⇒ full depth is mandatory. The phase-closure-auditor must verify that evidence PNGs actually show the asserted UI states — the gate the lean loop missed twice. QA/browser reports: recount pass/fail from the result table, not the summary line.
- This spec declares **Frontend Present: yes** (metadata above) — iter-3's demo step skipped on a false "Frontend Present: no"; downstream steps must not repeat that.
- The verdict engine is pure and observer-side: it reads frozen snapshots and writes only through the journal repository's single writer queue (never from the WS serialization path). An evaluator exception must surface as `monitor_status: failed` per the existing isolation contract, never kill the feeder.
- Scope-creep flag: nothing here requires capabilities outside goal.md Key Capabilities 24 (verdict engine) + the row-16 serving slice of the journal API; the full journal/review surface is deliberately excluded.
- Evidence-string copy register: present-tense, descriptive, thesis-attributed ("the tape confirmed your thesis"), per the goal.md Copy register; the existing "Descriptive only — not trading advice" line stays.
