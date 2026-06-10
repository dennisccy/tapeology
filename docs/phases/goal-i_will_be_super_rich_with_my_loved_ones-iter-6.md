# Goal Iteration 6 — Verdict-transition evidence completion + statement direction-correctness

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_will_be_super_rich_with_my_loved_ones
- **Iteration:** 6
- **Mode:** normal
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-40, J-42, J-43, J-45, J-46
- **Required-still-passing journeys:** J-38, J-39, J-41, J-44, J-01, J-02, J-04, J-06, J-07, J-17, J-68 (idle-strip clause)
- **Anti-goal reminders (verbatim from docs/goal.md; all others still hold):**
  - "**No naked outputs.** Every published verdict, stance, hint, risk flag, execution check, and grade MUST carry plain-language evidence derived from canonical engine values. A verdict without evidence is a defect. *(critical)*"
  - "**No prediction language.** A verdict or stance describes what the tape is doing **now** relative to the declared thesis — never a forecast of what price will do. *(critical)*"
  - "**Journal integrity.** Verdict timelines are append-only: never edited, backfilled, fabricated, or recomputed at read time; nothing is recorded before declaration; gaps (pause, watch restart, stale spans) are explicit events; data-end resolves to an explicit `expired`, never a fabricated outcome; …" *(critical — the statement-template fixes in this iteration MUST NOT rewrite the frozen statements already stored on existing theses in the persistent dev DB)*
  - "**The research layer is read-only over the engine.** It MUST NOT mutate engine, classifier, or feature state or outputs: the same event stream yields **byte-identical** tape state/confidence/features/history with or without an active thesis or attached observers (equivalence-tested). …" *(critical)*
  - "**No new indicators, no auto-tuning.** Confirmation rules, stances, hints, and studies MUST be composed from the EXISTING engine features and states only; research thresholds are config-owned research defaults …" *(critical — the direction-awareness fix composes the EXISTING `buy_price_impact` / `sell_price_impact` primary-window values only; any threshold goes in config)*
  - "**Evidence before cues.** The entry checklist/stance and setup-forming hints MUST NOT be built before the journal, excursion outcomes, and replay studies exist and their journeys (J-58 – J-62) pass; …" *(critical — nothing cue-shaped is built this iteration)*

## GOAL

Flip the five PARTIAL verdict-transition journeys (J-40, J-42, J-43, J-45, J-46) to passing by capturing each transition in the browser AT the asserted moment, after first fixing the two direction-correctness defects that currently make those pixels impossible or dishonest.

## BACKGROUND

The iter-5 evaluator (CONTINUE, lean recommended) mandated a LEAN evidence-completion iteration with NO new feature scope: the verdict engine and persistence are proven, but the executed browser matrix silently dropped four of the spec's journeys and captured UT-04 after the thesis had expired (capture-narrative mismatch). Five journeys therefore sit at PARTIAL purely for missing moment-correct pixels. Targeting all five at once deviates from the usual 1–3 cap deliberately: they are one flow shape (declare → wait for the scenario's deterministic phase → screenshot the thesis strip), and the evaluator named all five as one batch.

Planning-time code reading found **two real defects that must be fixed BEFORE the captures**, both inside already-registered canonical owners (blueprint Data Contract rows 15/16):

1. **Statement-status direction-awareness (evaluator observation 1, visible in shipped iter-5 pixels).** `_evaluate_statement` in `apps/backend/app/research/monitor.py` (lines 68–85, `directional_impact` kind) reads only the thesis-side impact — for a LONG thesis, `buy_price_impact > 0` ⇒ `met`. On SIM-SELLER's falling tape, an incidentally positive buy impact made "Price keeps making progress in your direction rather than stalling." read **met** on a LONG thesis while sellers pressed price down (UT-10/UT-14 pixels). The status must be direction-aware against the adverse side.
2. **`failed_move_fade` side mapping is INVERTED vs J-46.** `_raw_failed_move_fade` in `apps/backend/app/research/verdict.py` (line 334) sets `fade_absorption = "ask_absorption"` for LONG; goal.md J-46 mandates a LONG fade declared during SIM-REVERSAL's **bid-absorption** phase reads **confirming** ("the downside break is being absorbed"). Under current code that thesis stays `pending` through the whole absorption phase — the J-46 browser leg would fail as specified. The same inversion is frozen into the `failed_move_fade` statement templates in `apps/backend/app/research/taxonomy.py` (lines 119–136): statement 1 has `states_long=["ask_absorption"]`, and statement 2 has `states_long=["seller_control"]` — the latter contradicting even the verdict engine's own control branch (`_control_state()` = buyer_control for long). The unit tests at `apps/backend/tests/test_verdict_engine.py:336-369` encode the inversion and must be rewritten to goal.md's semantics, not preserved.

Lessons applied (binding, from `state/lessons.md`): capture verdict-state screenshots AT the asserted moment BEFORE sim scenario teardown (theses auto-expire at stream end); diff the executed browser matrix against this spec's full journey matrix BEFORE execution — iter-5 silently dropped 4 legs; scroll-into-view or full-page on every below-the-fold capture — the evaluator opens the PNGs and an idle strip where a chip was claimed is the named FAIL condition; never `npm run build` against the live dev server's shared `.next` (use `NEXT_DIST_DIR=.next-qa`); no `store.py` schema change is in scope, so no migration is needed — and none may be smuggled in.

## IN SCOPE

### Backend
- [ ] **Fix `directional_impact` statement evaluation** (`apps/backend/app/research/monitor.py`, `_evaluate_statement`): for a LONG thesis, the statement must NOT read `met` while the adverse side is materially pressing price down (and symmetrically for SHORT). Use ONLY the existing primary-window `buy_price_impact` / `sell_price_impact` values read verbatim from the snapshot; a tape with material adverse impact reads `violated`, genuinely flat/no-evidence reads `not_yet`. Any new threshold (e.g. an adverse-impact dominance test) is a config-owned research default — no magic number in research code. Do NOT touch `verdict.py`'s `_has_directional_impact` (verdict rules gate on the matching control tape_state first; they are correct and browser-proven for J-41/J-44).
- [ ] **Fix the `failed_move_fade` side mapping to goal.md J-46 semantics**: in `verdict.py` `_raw_failed_move_fade`, LONG fades a failed DOWNSIDE break ⇒ `fade_absorption = "bid_absorption"` (SHORT ⇒ `ask_absorption`), with the evidence wording mirrored ("The push lower failed …" for long); in `taxonomy.py` the `failed_move_fade` templates become statement 1 `states_long=["bid_absorption"], states_short=["ask_absorption"]` and statement 2 `states_long=["buyer_control"], states_short=["seller_control"]`. Frozen statements already persisted on existing theses MUST remain untouched (journal integrity — templates change in code only; no DB rewrite, no migration).
- [ ] **Rewrite the unit tests that encoded the inversion** (`apps/backend/tests/test_verdict_engine.py:336-369`): a LONG failed_move_fade on SIM-REVERSAL confirms DURING the bid-absorption phase (the deliberate J-40 asymmetry) and stays confirming through the buyer-control reclaim; add the SHORT mirror (ask_absorption); add four-quadrant direction-awareness tests for the `directional_impact` statement (long/short × favorable/adverse tape).

### Frontend (if applicable)
- None. The thesis strip renders backend projection values verbatim; no component, page, or fetch changes.

### New user-facing capability
None new — this iteration completes the proof (and honesty) of the already-shipped verdict-transition engine. After it, every one of the five verdict states (pending, confirming, weakening, rejecting, invalidated) has been seen in real pixels, and statement statuses read direction-honestly.

### New information displayed
None new. The WEAKENING (amber) chip renders in the browser for the first time, but it is existing, registered row-15 projection output.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
Statement statuses on the thesis strip become direction-honest (no more "making progress in your direction" reading met on an adverse tape); a long failed-move fade now confirms on the absorbed downside break as the catalog promises.

### Blueprint conformance
No new surfaces. All work lives inside the registered canonical owners of Data Contract rows 15 (thesis projection — research monitor → `GET /research/thesis/active`) and 16 (published verdict timeline — verdict engine → journal repository). Nav untouched.

### Data-contract additions
None. No new value, endpoint, or computation path; both fixes correct computation INSIDE the registered single owners. No blueprint edit required.

## OUT OF SCOPE

- J-48 thesis geometry on the chart (the J-45 "level line visible on the chart" clause stays explicitly deferred to J-48, as established in iter-5).
- J-50 user-facing resolve controls, J-52 action marks, J-47 re-attach, the `/journal` page, analytics, studies, and the entire cue layer (Evidence-before-cues).
- Any `store.py` schema change or migration (none is needed; none is permitted here).
- Any engine/classifier/provider change (`apps/backend/app/engine/`, `providers/` untouched; SIM-SHIFT/SIM-REVERSAL scenario data stays as calibrated).
- Any frontend change.
- Fixing the full-pipeline `qa_complete` halt (harness-level; this iteration runs the lean cycle which does not contain those steps — see NOTES).

## DEFINITION OF DONE

- [ ] Target journeys J-40, J-42, J-43, J-45, J-46 pass via browser-qa-agent with moment-correct captures per the matrix below — every claimed verdict chip visibly present in its PNG (scroll-into-view or full-page; an idle strip under a chip claim is a FAIL).
- [ ] The executed browser matrix is diffed against the TESTING REQUIREMENTS matrix below BEFORE execution and covers every leg — no silently dropped journey (the iter-5 failure mode).
- [ ] Required-still-passing journeys remain green; J-41's re-capture additionally shows the progress statement no longer reading met on the adverse tape (the direction-awareness fix in pixels).
- [ ] No anti-goal violation introduced; observer-equivalence test still green; no schema change in the diff.
- [ ] Unit tests pass, including the rewritten J-46-semantics tests and the four-quadrant statement tests; no regressions (backend suite fully green bar the known credential-gated skip).
- [ ] Browser-qa artifacts exist: `reports/phase-goal-i_will_be_super_rich_with_my_loved_ones-iter-6-ui-test-results.md` + `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-6-evidence/` PNGs (the lean pipeline must run to completion — see NOTES).
- [ ] Dev handoff written at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-6-dev.md`.

## TESTING REQUIREMENTS

- **Browser (the core deliverable — five independent watch sessions, one thesis each; one active thesis per ticker, so J-40 and J-46 need separate SIM-REVERSAL watches):**

  | Leg | Scenario / declare | Capture moment A | Capture moment B |
  |---|---|---|---|
  | **J-40** | Watch `SIM-REVERSAL`; once the state reads Bid Absorption, declare **absorption_reversal / long**, invalidation below the absorbed price (e.g. 99.00) | PENDING chip during sustained bid_absorption — premise statement met, trigger statement not-yet | CONFIRMING chip after the flip to buyer_control, **same thesis** (strip shows the SIM-REVERSAL source descriptor — iter-5's UT-12 was bound to SIM-BUYER and did not count), evidence citing the flip |
  | **J-42** | Watch `SIM-BUYER`; declare **trend_continuation / long**, invalidation below (e.g. 99.00) | CONFIRMING chip after the ~3s-logical dwell, evidence citing buyer control + positive impact; statements read met | (no-flapping: a second capture ≥10s later still CONFIRMING, or the published timeline via `GET /research/journal/{id}` showing a single confirm transition) |
  | **J-43** | Watch `SIM-SHIFT`; during the buyer-control phase declare **trend_continuation / long**, invalidation FAR below the chop band — the chop centers on the scenario start price 100.00, so use e.g. 95.00 (never invalidated) | CONFIRMING chip during the control phase | **WEAKENING amber chip** after the shift to chop — the first time this chip has ever rendered; distinct "supporting evidence faded"-register evidence; never a silent return to pending |
  | **J-45** | Watch `SIM-BUYER`; declare **level_break / long** with the level a few cents ABOVE the current last (inside the deterministic rise, e.g. last + 0.30), invalidation below | PENDING chip pre-cross with the cross statement not-yet (the latch unset despite strong control) | CONFIRMING chip after last crosses the level, evidence citing the cross + control. Chart level-line clause deferred to J-48 |
  | **J-46** | Fresh watch of `SIM-REVERSAL`; during the bid-absorption phase declare **failed_move_fade / long** with the level just above the absorbed price (e.g. 100.05) and invalidation below | **CONFIRMING chip DURING the absorption phase** ("the downside break is being absorbed" — the deliberate asymmetry with J-40, only possible after the side-mapping fix) | still CONFIRMING after buyers take control and price reclaims the level (never rejecting) |

  **Timing budget (binding):** sim phases are 60s logical (SIM-SHIFT control, SIM-REVERSAL absorption) / 72s logical (SIM-SHIFT chop) / 120s logical (SIM-REVERSAL control); the feeder paces phase 2 at roughly real time after the fast-forwarded warm-up — budget **~60s+ of wall-clock waiting per phase shift** and poll the strip so moment B is captured promptly when the chip changes, **before the stream ends and the thesis auto-expires**. Declare as soon as the declared phase's state settles, never near a phase boundary. Every capture must contain the thesis strip (scroll-into-view or full-page).

  **Plus:** one J-41 re-capture (SIM-SELLER, trend_continuation/long, far invalidation): REJECTING chip with evidence AND the "Price keeps making progress in your direction…" statement now reading violated/not-met — the direction-awareness fix verified in pixels. One idle-cockpit capture re-confirming the J-68 idle-strip clause (no thesis ⇒ single declare affordance, cockpit unchanged).

- **Unit/integration:** rewritten `test_j46_*` tests asserting LONG fmf confirms during SIM-REVERSAL's bid_absorption phase + stays confirming through the reclaim + SHORT mirror; four-quadrant `directional_impact` statement tests (long/short × favorable/adverse); full backend suite green; observer-equivalence test green.
- **Error cases:** no new input surface. Re-assert (suite-level, already covered) that the fmf/statement fixes change no validation behaviour: level still REQUIRED for failed_move_fade (422 when missing), wrong-side invalidation still 422.

## NOTES

- **Evaluator mandate (iter-5 eval.md):** lean evidence-completion, no new feature scope. The two code fixes are the targeted-defect allowance: item (2) of the mandate names the statement direction-awareness defect, and the fmf inversion is a planning-time discovery that would otherwise fail the mandated J-46 leg mid-iteration. Nothing else may be built.
- **The fmf rewrite is goal-corrective, not test-appeasing:** `test_verdict_engine.py:336-369` currently asserts the inverted semantics with a comment claiming "a long failed_move_fade expects a failed UP push absorbed at the ask" — goal.md J-46 says the opposite in plain words ("declare failed_move_fade / long … during the absorption phase the verdict reads confirming ('the downside break is being absorbed')"). goal.md wins. The reviewer should treat any attempt to keep the old mapping and instead bend the browser plan as a spec violation.
- **Journal integrity caveat for the developer:** statements are frozen onto each thesis at declaration. Fix the TEMPLATES (taxonomy.py) and the LIVE status evaluation (monitor.py) only; existing rows in the persistent dev DB keep their stored statements verbatim — no UPDATE, no backfill, no migration (`journal_schema_version` stays 2, and it remains excluded from `config_fingerprint`).
- **Verdict-engine blast radius is nil by construction:** `verdict.py` contains no reference to statements (verified by grep), and `_has_directional_impact` is untouched, so J-38/J-39/J-41/J-44's proven behaviour is unaffected except for the intended fmf correction.
- **Pipeline-halt watch item:** the full pipeline halted at `qa_complete` (status `complete` / `next_action: audit`) in both prior full iterations — audit/ux-regression/closure never ran. This lean iteration's cycle (developer → reviewer → browser-qa → coherence → evaluator) does not contain those steps, so it sidesteps the defect, but the halt remains OPEN and must be fixed in the harness before the next FULL iteration is dispatched; the evaluator should keep treating closure-auditor claims as absent until then. Relatedly, the QA-validation habit of relabeling unit evidence as "browser PASS" was called out twice — the browser-qa report is the only honest browser record.
- **Harness cautions:** use `NEXT_DIST_DIR=.next-qa` for any frontend build (never against the live dev server's shared `.next`); QA harness uses the deterministic offset ports per `.claude/project-template.md`.
- **After this iteration:** the evaluator-suggested next feature targets are J-48 (thesis geometry on the chart) or J-50 (user-facing resolve) — not part of this spec.
