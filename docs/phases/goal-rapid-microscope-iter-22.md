# Goal Iteration 22 — Finish J-09: screen Studies 1 and 3 through an operator-reachable path

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 22
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — Prior-iteration verdict was ESCALATE (mandatory, no exceptions; also
  matches trigger 1 in substance: the new grid-selector wiring touches `scout.py`'s manager, CLI,
  and route bodies together, and iter-21's audit already showed that class of change is reachable
  by nothing but a unit test unless every entry point is exercised)
- **Frontend Present:** yes
- **Target journeys:** J-09, J-07
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-08, J-10
- **Anti-goal reminders:**
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **No threshold, grid, formula, embargo, or fold parameter is chosen or revised from
    validation, sealed, or holdout outcomes.** Fitting rules are data functionals frozen before
    reveal; per-origin refits under an unchanged rule are provenance, never a new choice.
    *(critical)*
  - **The denominator never shrinks.** Every evaluated variant lands in the hash-chained ledger
    with a closed-vocabulary decision; kills are never deleted; the union-N across grid
    versions is served beside every family. *(critical)*
  - **Evidence classes never mix.** No `historical_exposed_diagnostic` output feeds a gate, a
    graduation transition, a certificate, a promotion, or a pooled statistic with
    `historical_oos` rows; nothing in this era emits `live_confirmatory`. *(critical)*
  - **No microstructure claim beyond what L1 supports.** `refill_consistent` is the strongest
    liquidity label; "iceberg", institutional-intent, and manipulation language are banned;
    every aggressor-derived quantity is served beside its `fallback_frac` and `unknown_frac`.
    *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
    them, never a mutation of them. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed,
    never re-tagged, never deleted, never content-perturbed. Splits are frozen at
    registration. *(critical)*

## GOAL

Screen Studies 1 (range-wall failed aggression) and 3 (capitulation exhaustion) — the two
pilot-study candidates that have existed frozen-in-source since iter-21 but were never reachable
outside a unit test — through the Scout on the same committed hermetic fixtures Study 2 used,
each to a recorded, closed-vocabulary ledger decision plus a walk-forward floor-check row,
reachable via the CLI/compute-manager path exactly like Study 2 already is; re-photograph the
walk-forward eligibility line iter-21's independent auditor fixed but nobody has yet seen on
screen; and take a fresh, dated re-verification screenshot of J-07 Graduation, which the prior
round's clock cut.

## BACKGROUND

Iter-21 (ESCALATE, full) built and screened Study 2 (delta divergence) end to end and moved J-09
from `failing` to `partial`; its own next-step recommendation named finishing Studies 1 and 3 as
"the only thing standing between the project and nine of ten journeys green," re-photographing the
walk-forward eligibility line as still owed (only the auditor's own fix has checked itself), and
re-checking J-07 because the round's wall-clock cut it before anyone looked. The prior verdict is
ESCALATE, so this iteration is full depth by the binding rule with no exceptions to weigh.

Two lessons from this session's own record shape this iteration's scope. First (iter-21 lesson):
"A spec'd flow can pass review AND QA while being reachable by NOTHING but a unit test" — Study 2's
own walk-forward floor-check row was exactly this trap until iter-21's audit forced it into the
route/CLI path; Studies 1 and 3 must ship reachable the same way from day one, not added to a test
file only. Second (iter-17 lesson, restated because Study 1 touches a threshold-shaped argument
again): a new rule/threshold module must not let a caller or a convenient fixture narrow a
spec-pinned constant. Study 1's frozen request already deliberately stays single-feature
(`failed_aggression_score >= 0.5`) rather than inventing the two-feature `refill_consistent`
co-occurrence goal.md's own prose describes — that machinery is genuinely unbuilt (T-1), and this
iteration does not invent it; Study 1's honest screen answer this round is on the single-feature
signature alone, exactly as iter-21 froze it and exactly as `docs/rapid-validation-spec.md`'s own
"ambiguous or unimplementable ⇒ drop, never improvise" rule requires. This is logged to the
assumption ledger below.

The 22.3-second Microscope Readiness latency fix the auditor scoped (B2) is explicitly excluded
this round — the evaluator's own next-step recommendation named it "shed THIS first if the clock
bites," and this session's own iteration-hygiene note records step timeouts in 13 of 15 referee-era
iterations, so keeping this round small is a deliberate priority-1 choice, not an oversight.

## IN SCOPE

### Backend

- [ ] Add two additive `grid` selector values to `POST /research/desk/micro/scout/compute`'s
      request body (mirroring `GRID_SELECTOR_DELTA_DIVERGENCE_PILOT`'s existing shape exactly —
      one-element grid, required resolver/playbook_store wiring, required `exposure_registry` so
      the walk-forward floor-check stage records via the SAME operator-reachable path, never only
      a unit test): one selecting `PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION`, one selecting
      `PILOT_STUDY_CAPITULATION_EXHAUSTION`. Wire both into `ScoutComputeManager.trigger` AND the
      `python -m app.research.scout --grid ...` CLI, exactly as `delta_divergence_pilot` already
      is in both places — no third, differently-wired path.
- [ ] Run Study 1 (`PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION`) through
      `register_screen_and_walkforward_check` against the same committed hermetic band-touch
      fixture family Study 2's TC-5/TC-6 tests already use, using the frozen single-feature
      request exactly as iter-21 froze it (`failed_aggression_score`, `op: "ge", value: 0.5`,
      `structure_context_kind: "band_touch"`) — no new feature, no co-occurrence term added.
- [ ] Run Study 3 (`PILOT_STUDY_CAPITULATION_EXHAUSTION`) through the same function against a
      hermetic `PlaybookStore` fixture carrying one `setup_id="capitulation"` signal, reusing the
      established `pg_snapshot_store`-style fixture pattern iter-21's own TC-1/TC-2 tests already
      built for `playbook_signal` anchor extraction — no second implementation of that fixture
      shape.
- [ ] Rewrite `test_tc7_range_wall_and_capitulation_are_frozen_but_never_screened` (now false) into
      an assertion that both studies WERE screened this iteration with recorded, closed-vocabulary
      decisions and non-empty ledger rows — the negative proof it made is retired, not silently
      deleted (state why in the dev handoff).
- [ ] No change to the default reference grid's behaviour, the delta-divergence pilot path, any
      `referee_*` module, the engine, or `Config().config_fingerprint()`.

### Frontend

- [ ] No new component or section — the Scout Ledger / Walk-Forward sections already render any
      family/trial generically (feature name, `structure_context.kind`, decision, reason,
      withheld_excluded, `screen_result`); Studies 1 and 3 render through the SAME existing
      generic table with zero UI code change (T-11: new sections stay below shipped ones; this
      adds rows to an already-shipped section, not a new section).

### New user-facing capability

The operator can trigger Study 1 or Study 3's screen (CLI or, once wired, the same compute-manager
path Study 2 uses) and see its recorded decision — including its walk-forward floor-check row — on
the already-shipped `/desk` Scout Ledger and Walk-Forward sections, exactly as Study 2's decision
already renders.

### New information displayed

No new field. Three pilot-study families (not one) now appear in the same already-shipped Scout
Ledger table, each carrying the same already-registered per-trial fields.

### New user actions

None new — the existing "Run Screen" trigger surface is unchanged; only the CLI/manager's internal
grid-selector vocabulary grows by two additive values (a request parameter, not a UI control).

### UI surface changes

None. Same sections, same table, same columns — more rows.

### Product surface delta

`/desk`'s Scout Ledger and Walk-Forward sections now show all three predeclared J-09 studies with
recorded decisions instead of one; no other surface changes.

### Blueprint conformance

All work lands under the already-registered Information Architecture home "`/desk` → Scout Ledger
/ Walk-Forward (J-09 pilot-study results render here too)" — no new page, no nav-skeleton change.

### Data-contract additions

None. Studies 1 and 3 are new ROWS inside the already-registered "Scout trials, kills,
denominators, screens" and "Fold specs, folds, sequences, decay view" Data Contract rows
(`scout.py`/`scout_ledger.py`/`walkforward.py`, `GET /research/desk/micro/scout`,
`GET /research/desk/micro/walkforward`) — exactly the precedent `blueprint.md`'s iter-21 note
already recorded for Study 2. The two new `POST /scout/compute` grid-selector values are additive
request parameters, not displayed values (matching the existing `observer=` kwarg precedent), so
they carry no Data Contract row of their own.

## OUT OF SCOPE

- The two-feature `failed_aggression_score` × `refill_consistent` co-occurrence machinery for
  Study 1 — genuinely unbuilt (T-1); Study 1 screens on its already-frozen single-feature request
  this round, honestly disclosed as such in the dev handoff.
- The 22.3-second Microscope Readiness page-load latency fix (auditor B2) — explicitly the
  evaluator's own "shed first" item; deferred, not dropped silently.
- Real production Scout/fold runs against the live `.data/` store — still forbidden (quadratic
  divergence anchor extraction, uncancellable mid-candidate, auditor B3).
- Recording real market tape for J-06 — still an unauthorized operator act.
- The sealed judge's economic-floor / evidence-label sourcing ruling — still awaiting the owner;
  J-09 does not depend on it (iter-20's re-derived finding, unchanged).
- Turning an unknown `grid` selector name into a polite error instead of a raised `ValueError` —
  explicitly named by the iter-21 evaluator as NOT this round's work.
- The one-line blueprint documentation correction of which address serves the eligibility row —
  explicitly named by the iter-21 evaluator as NOT this round's work.
- Making the divergence search fast enough to run against the real tape — explicitly named by the
  iter-21 evaluator as NOT this round's work.
- The stale Referee-readiness-count disclosure/guard named in round 9 — not carried forward by the
  iter-21 evaluator's own next-step list; left for a future round to re-surface explicitly rather
  than folded in here unannounced.

## DEFINITION OF DONE

- [ ] Study 1 screens to a recorded, closed-vocabulary ledger decision plus a walk-forward
      floor-check row, reachable via the CLI (and/or compute-manager route) — not only a pytest
      fixture.
- [ ] Study 3 screens to a recorded, closed-vocabulary ledger decision plus a walk-forward
      floor-check row, reachable the same way.
- [ ] The default reference grid still writes exactly one row per candidate (no floor-check stage
      row anywhere in its output) — unchanged regression proof.
- [ ] J-09 re-evaluated by browser-qa-agent with all three pilot-study families visible on
      `/desk`'s Scout Ledger / Walk-Forward sections, each with a recorded decision.
- [ ] The walk-forward eligibility line (the `stage: "walkforward_floor_check"` row) for Study 2
      is freshly photographed on screen this iteration — no reused iter-21 asset.
- [ ] J-07 re-verified via a fresh, dated browser-qa-agent screenshot this iteration (no code
      change expected; the earlier proof stands per iter-21's own durability finding, but the
      finish line stays blocked without a fresh look).
- [ ] Required-still-passing journeys (J-01, J-02, J-03, J-04, J-05, J-08, J-10) remain green via
      deterministic replay + LLM fallback.
- [ ] No anti-goal violation introduced (see restated rails above); no new `Config` field; no
      referee-module diff; fingerprint stays `08e471b10130e1e2`.
- [ ] Unit tests pass; full backend suite count is ≥ the iter-21 baseline (3,316 pass / 8 skip),
      0 failures, 0 errors.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-22-dev.md`, explicitly
      naming Study 1's single-feature-only scope as a disclosed, deliberate T-1 deferral (not an
      oversight).

## TESTING REQUIREMENTS

- Browser: J-09 (Scout Ledger + Walk-Forward sections showing all three study families and the
  Study-2 walk-forward floor-check row), J-07 (Graduation address, fresh capture).
- Unit/integration: the new grid-selector wiring in `ScoutComputeManager.trigger` and the CLI
  `main()`; `register_screen_and_walkforward_check` exercised for both new studies; the rewritten
  `test_tc7_...` assertion; the unchanged-default-grid regression test.
- Error cases: the default grid's screen-only output shape is unchanged (no floor-check row);
  Study 1's request fields stay byte-identical to iter-21's frozen values (no invented
  co-occurrence field or threshold).

Test-first contract:

- TC-1: given the frozen Study-1 request (`PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION`,
  `feature_name="failed_aggression_score"`, `structure_context_kind="band_touch"`) and the same
  committed hermetic band-touch fixture Study 2's tests use, when the new `range_wall_...`
  grid-selector value is posted to `POST /research/desk/micro/scout/compute`, then the response
  reaches `state: "done"` and `GET /research/desk/micro/scout` shows one new family with a
  screen-stage trial row carrying a closed-vocabulary `decision` and
  `structure_context.kind == "band_touch"`.
- TC-2: given the Study-1 run in TC-1 with an `exposure_registry` holding zero `historical_oos`
  sessions, when the run completes, then a second ledger row under the same `candidate_id` has
  `stage == "walkforward_floor_check"`, `decision == "killed_insufficient_n"`, and
  `walkforward_floor_check.status == "insufficient_n"`.
- TC-3: given a hermetic `PlaybookStore` fixture carrying one `setup_id="capitulation"` signal and
  the frozen Study-3 request (`structure_context_kind="playbook_signal"`, `setup_id="capitulation"`),
  when the new `capitulation_...` grid-selector value is posted to
  `POST /research/desk/micro/scout/compute`, then the response reaches `state: "done"` and the
  ledger shows one new family with `structure_context == {"kind": "playbook_signal",
  "setup_id": "capitulation"}` and a closed-vocabulary `decision`.
- TC-4: given the Study-3 run in TC-3 with zero `historical_oos` sessions, when the run completes,
  then a second ledger row under the same `candidate_id` has `stage == "walkforward_floor_check"`
  and `decision == "killed_insufficient_n"`.
- TC-5: given the default reference grid (`grid` omitted or `"default"`), when
  `POST /research/desk/micro/scout/compute` is called, then the ledger writes exactly one row per
  candidate — no row anywhere has `stage == "walkforward_floor_check"`.
- TC-6: given Study 1's request object as returned by `pilot_study_candidate_grid()`, when its
  fields are inspected, then `feature_name == "failed_aggression_score"` and
  `params == {"op": "ge", "value": 0.5}` remain byte-identical to the iter-21-frozen values — no
  new co-occurrence field added.
- TC-7: given `python -m app.research.scout --grid range_wall_failed_aggression_pilot` (or the
  equivalent new CLI choice) run against the committed fixture, when it completes, then stdout
  reports `1 candidate(s) processed` and the on-disk ledger contains the two rows from TC-1/TC-2 —
  proving the CLI path, not only a unit test, produces them.
- TC-8: given a fresh `rm -rf apps/frontend/.next` + rebuild and the scoped QA backend seeded with
  the TC-1..TC-4 runs, when browser-qa navigates to `/desk` and expands Scout Ledger, then a
  screenshot shows three families (range-wall, delta-divergence, capitulation) each with ≥2 trial
  rows, and the delta-divergence family's `walkforward_floor_check` row is visible on screen.
- TC-9: given the scoped QA backend, when browser-qa re-navigates to the J-07 graduation address
  (the `GET /research/desk/micro/graduation` surface reached the same way iter-20's capture
  reached it), then a fresh, iter-22-dated screenshot shows the graduation answer's full body
  (family, sealed reading, verdict, observation count) — not a reused iter-20 asset.
- TC-10: given the rewritten `test_tc7_...` assertion and the rest of the suite, when the full
  backend test suite runs, then it exits with 0 failures, 0 errors, and a pass count ≥ 3,316
  (the iter-21 baseline).
- TC-11: given the Required-still-passing journeys (J-01, J-02, J-03, J-04, J-05, J-08, J-10),
  when the deterministic golden-replay set is run against this iteration's build, then every
  journey with a stored script (`journey-scripts/J-0{1..5}.json`, `J-08.json`, `J-10.json`)
  reports 0 failed steps, and each is confirmed by an opened, non-corrupt screenshot.
- TC-12: given the finished build, when `Config().config_fingerprint()` is evaluated and
  `git status --porcelain` is read directly, then the fingerprint prints `08e471b10130e1e2` and
  no `referee_*.py` module appears in the changed-file list.

## NOTES

- Rig-mutation sequencing: this iteration's browser pass POSTs to `/research/desk/micro/scout/compute`
  against the scoped QA rig, which — per the binding "Do not redo" rig rule already on record —
  invalidates `J-08.json` step 3 / `J-10.json` step 12's "No candidates ledgered." assertion for any
  LATER lane in the same run. Sequence rig-mutating browser tests (TC-8) after the golden-replay
  lane, or confirm those two scripts are order-independent, before calling this iteration clean.
- `Frontend Present: yes` is set because the Definition of Done names `browser-qa-agent` for J-09
  and J-07 (iter-18 lesson: `Frontend Present: no` self-cancels the whole UI chain even at full
  depth).
- The evaluator's own honesty finding from iter-20 stands unchanged: J-09 has never been, and is
  not by this spec, human-blocked — nothing in this iteration's scope needs the owner's sealed-judge
  ruling.
