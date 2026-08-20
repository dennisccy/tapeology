# Goal Iteration 21 — J-09 pilot studies: predeclare all three, screen the first one honestly

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 21
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — iteration-20 verdict was ESCALATE (mandatory, no exceptions). Independently
  also satisfies trigger 1 (structural/cross-cutting: `scout.py`'s core `extract_anchors` read
  path, a new `micro_join.py` band-touch enumerator, `walkforward.py`'s floor-check path, and
  frontend rendering of a never-before-seen `structure_context.kind` all change together, and no
  single journey's existing test suite covers their interaction) and trigger 4 (J-09 is a
  brand-new, never-attempted full-stack journey — its results render through J-08's shipped
  sections, closing real backend gaps `scout.py`'s own module docstring has named "J-09's scope"
  since era baseline).
- **Frontend Present:** yes
- **Target journeys:** J-09
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-10 (full
  regression widen — ESCALATE from iter-20 plus this iteration edits `scout.py`'s and
  `micro_join.py`'s shared core paths that every one of these journeys' machinery touches)
- **Anti-goal reminders:**
  - **No fabricated data** — the tape engine's five states and thresholds, the frozen structure
    computations, the JSON `BarStore`, and every KEPT surface's behaviour stay byte-identical. New
    work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a recorded named seed via per-row
    streams; identical requests reproduce byte-identical results; no wall-clock, no unseeded
    randomness in any research artifact. *(critical)*
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the
    MCP surface can change state. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*
  - **No exploratory read of a sealed shard.** Event data and outcome aggregates of a `sealed`
    shard are refused everywhere (routes, MCP, accessor, readiness) until its recorded exposure;
    the refusal is typed, tested, and fail-closed. *(critical)*
  - **A recorded tranche is one opaque research pool until its shards are exposed.** No served
    surface — readiness, recorder progress, datasets, backtests, PnL ledger, Scout, walk-forward,
    graduation, MCP, UI — may present a complete identity-labelled partition of "exploratory"
    versus "sealed", nor a complete per-shard list of EITHER side while any pool member is
    unexposed. *(critical — spec r5)*
  - **Evidence classes never mix.** No `historical_exposed_diagnostic` output feeds a gate, a
    graduation transition, a certificate, a promotion, or a pooled statistic with `historical_oos`
    rows; nothing in this era emits `live_confirmatory`. *(critical)*
  - **No threshold, grid, formula, embargo, or fold parameter is chosen or revised from
    validation, sealed, or holdout outcomes.** Fitting rules are data functionals frozen before
    reveal. *(critical)*
  - **The denominator never shrinks.** Every evaluated variant lands in the hash-chained ledger
    with a closed-vocabulary decision; kills are never deleted; the union-N across grid versions
    is served beside every family. *(critical)*
  - **The accessor is the only data door.** No module but `micro_accessor.py` opens snapshot or
    vault event data; origin fences fail closed; import-ban and source-scan guards enforce it.
    *(critical)*
  - **No microstructure claim beyond what L1 supports.** `refill_consistent` is the strongest
    liquidity label; "iceberg", institutional-intent, and manipulation language are banned; every
    aggressor-derived quantity is served beside its `fallback_frac` and `unknown_frac`.
    *(critical)*
  - **The 12 pre-existing tick symbol-days are permanently exploratory** — never sealed, never
    `historical_oos`, never relabeled. *(critical)*
  - **Referee modules are byte-untouched this era** — `referee_handoff_ready` never implies
    current-Referee registrability of a flow predicate. *(critical)*

## GOAL

Build J-09's shared foundation (structure-context-conditioned anchor extraction plus a real
band-touch enumerator) so all three predeclared pilot-study specs exist frozen in source before
any outcome is read, and take the first one (delta divergence at level tests) through a genuinely
discriminating Scout screen and walk-forward floor check to a recorded ledger decision, rendered
through J-08's already-shipped Desk sections.

## BACKGROUND

Iteration 20's evaluator re-tested and reversed the two-round-old "J-09 is human-blocked" claim
(sealed judge's econ-floor hole doesn't reach J-09 — see `iteration-state.md`'s Active blockers)
and ESCALATEd specifically so J-09, "the era's biggest new-code round," gets the independent audit
lane. Reading `scout.py` confirms the module's own docstring has named
`structure_context.kind in {"playbook_signal", "band_touch"}` as "J-09's scope" since era
baseline — `extract_anchors` structurally raises `ScoutUnsupportedStructureContextError` for both
today — and `micro_join.py`'s `joinable_corpus_counts` has carried a `band_touch_count:
{"status": "not_enumerated"}` placeholder since iteration 4 for the same reason: no wall-touch
enumerator exists yet. Both are genuinely unbuilt, not merely unwired.

Checking the spec (`docs/rapid-validation-spec.md` §1) shows every constant J-09's three studies
need is ALREADY pre-registered and frozen: `failed_aggression_score` already IS
"`dominant_side_volume_share × flatness`" (§1 `IMPACT_FLATNESS_SCALE_BPS`) — the exact
aggression-plus-collapsing-efficiency composite Study 1 names; `divergence_at_level()` (Card 9.1,
amended r2) is already fully coded in `micro_features.py` using the already-frozen
`DIVERGENCE_TRAILING_SECONDS`/`DIVERGENCE_DELTA_VOLUME_FRACTION`; `refill_consistent` and
`WF_FOLD_MIN_OBSERVATIONS`/`WF_TRAIN_MIN_SESSIONS`/`WF_FOLD_MIN_SIGNAL_SESSIONS` are likewise
already pinned. **No new threshold or formula needs inventing (T-1) — the remaining work is
wiring already-frozen primitives to a new anchor source, plus the enumerator itself.**

Success Criteria's own scope-pressure order explicitly permits deferring "up to two of the three
pilot studies" — this iteration predeclares all three (goal.md's stated priority order) but takes
only ONE (delta divergence at level tests — its formula is 100% pre-coded, the smallest remaining
glue) through a full screen-to-decision this iteration; the other two stay frozen-in-source,
undeferred in the sense that their frozen fields exist and are reviewable, but not yet passed
through the ledger. This is logged to the assumption ledger below.

Lessons applied: iter-17 (a rule module must never accept a caller-supplied threshold — J-09 reuses
only already-pinned §1 constants, never a new negotiable floor); iter-18 (a change to the shared QA
seeding rig requires re-running the FULL replay set the same round — if this iteration extends any
fixture the scoped QA backend reads, replay all 6 journeys before calling it done); iter-18(second)
(`Frontend Present: yes` is set explicitly, since DoD names browser-qa-agent); iter-16(second)
(check real `git status --porcelain`, not `status.json`, for any `journey-scripts/*.json` touch —
this iteration DOES touch `J-10.json`); iter-15 (any new trap-adjacent assertion needs a
non-vacuity check proving the state it sweeps is genuinely populated).

## IN SCOPE

### Backend
- [ ] `scout.py` `extract_anchors`: add read paths for `structure_context_kind in
      {"playbook_signal", "band_touch"}`, joining anchors via the already-registered
      `micro_join.join_playbook_signal`/`micro_join.join_band_touch` (no second join
      implementation), carrying the same per-window `side_source`/`fallback_frac`/`unknown_frac`
      disclosures the `"none"` path already serves. `ScoutUnsupportedStructureContextError`
      continues to guard any future, still-unsupported value.
- [ ] New band-touch enumerator in `micro_join.py` (e.g. `enumerate_band_touches`): walks a
      dataset's own trade timeline against the already-resolved `BandMapResolver` band map (no new
      wall detection, no new band-map computation — reads the resolver verbatim, read-only) and
      returns ordered per-wall touch instants (`{"symbol", "as_of_epoch", "band_id"}`-shaped),
      through the accessor discipline (no direct `open()`/`sqlite3.connect` outside
      `micro_accessor.py`/existing store readers — T-5).
- [ ] Materialize `joinable_corpus_counts`'s `band_touch_count` from the `not_enumerated` sentinel
      to the real enumerated int, now that the enumerator exists (same field, same owner
      `micro_readiness.py`, same endpoint — no shape change).
- [ ] A bounded, frozen-in-source pilot-study candidate grid (analogous to
      `default_fixture_grid()`) holding all THREE predeclared requests in goal.md's stated
      priority order — (1) range-wall failed aggression (`band_touch`, reusing
      `failed_aggression_score` + a `refill_consistent` co-occurrence disclosure), (2) delta
      divergence at level tests (`band_touch`, reusing `divergence_at_level()` verbatim), (3)
      capitulation exhaustion (`playbook_signal`, `setup_id="capitulation"`, reusing
      `failed_aggression_score`/efficiency-trend features) — each request's frozen fields
      (`feature`, `structure_context`, `outcome`, `econ_floor`) fully constructed and unit-tested
      for shape correctness, well under `SCOUT_MAX_VARIANTS_PER_FAMILY` (24).
- [ ] Take ONLY the delta-divergence-at-level-tests request through `register_and_screen_candidate`
      on a committed synthetic fixture with known band touches and a known divergence signature
      (hermetic, per the era's "known-effect oracle" discipline) — full §5.4 disclosures, §5.5
      economic column served beside the screen.
- [ ] A walk-forward floor check for the screened candidate against the corpus's `historical_oos`
      (class-2 / exposed-vault) session count, reusing the already-pinned `WF_TRAIN_MIN_SESSIONS`/
      `WF_FOLD_MIN_SIGNAL_SESSIONS`/`WF_FOLD_MIN_OBSERVATIONS` floors and the same
      typed-refusal-before-fold-spec pattern `run_tick_family_fold_request` (J-05) already
      establishes — never inventing a new floor, never calling `evaluate_mode_b_fold` on a corpus
      that cannot clear the floor. Record the resulting decision (`insufficient_n`, honestly, since
      today's real and fixture corpora carry zero exposed vault shards) in the scout ledger.
- [ ] `POST /research/desk/micro/scout/compute` gains an additive, default-omitted grid-selector
      parameter so the pilot grid is CLI/manager-runnable beside the unchanged default grid — no
      second endpoint, no behavior change when the parameter is omitted (byte-identical to today).
- [ ] New guard/source-scan test proving no `micro_*.py`/`scout*.py`/`walkforward*.py`/`vault.py`
      module imports or calls `strategy_trade_readiness` or `referee_evidence` (closes half of the
      iter-9-ordered r5 §10.7 item — see NOTES for the other half, dropped this iteration).
- [ ] Restore `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` steps 9-10 to their
      pre-iter-16 assertions (`desk-section-expand-playbookEvidence` → "Built from signature:";
      fill `desk-playbook-date-input` "2026-06-22" → "recorded signals, none hidden") — passenger,
      restoring the two data-bearing assertions iter-16 silently dropped for empty-state ones.

### Frontend
- [ ] Verify the already-shipped Scout Ledger / Walk-Forward sections render the new
      `structure_context.kind="band_touch"` candidate row generically (no hardcoded `"none"`
      assumption); fix minimally if a genuine gap is found — no new section, no new heading, no
      shipped column changed (T-11).
- [ ] Passenger: re-capture the `UT-10` backend-unavailable evidence via **element-capture** of
      `data-testid="scout-ledger-unavailable"` (not a full-page screenshot) so the picture shows
      the real panel text instead of iter-19's mostly-empty frame.

### New user-facing capability
None — J-09's results are read-only additions to the already-shipped Scout Ledger and
Walk-Forward sections; no new page, control, or nav entry.

### New information displayed
The delta-divergence pilot-study candidate's row (feature, `structure_context.kind="band_touch"`,
`evidence_class`, disclosures, decision) inside the already-shipped Scout Ledger section; its
floor-refusal (or fold result) inside the already-shipped Walk-Forward section; `joinable_corpus.
band_touch_count`'s real int inside the already-shipped Microscope Readiness section.

### New user actions
None new — the existing "Run Scout" / compute controls gain a grid-selector option usable via CLI
today; no new UI button this iteration (the pilot grid is not wired to a UI trigger yet — CLI/
manager only, consistent with keeping the real production Scout ledger untouched, see NOTES).

### UI surface changes
None — no new section, page, or shipped-heading change.

### Product surface delta
The Scout Ledger and Walk-Forward sections can now genuinely display a structure-conditioned
candidate (previously only `structure_context.kind="none"` rows ever existed); no visible change
against the real production store, which stays exactly as J-10's golden script already expects.

### Blueprint conformance
All rendered rows live under the already-registered Desk → Rapid Microscope → Scout Ledger /
Walk-Forward / Microscope Readiness homes (`blueprint.md` Information Architecture table,
unchanged this iteration). No nav-skeleton change.

### Data-contract additions
None — every value above is a NEW ROW inside an ALREADY-registered Data Contract entry (Scout
trials/screens → `scout.py`/`scout_ledger.py` → `GET /research/desk/micro/scout`; folds/decay →
`walkforward.py` → `GET /research/desk/micro/walkforward`; `joinable_corpus.band_touch_count` →
`micro_readiness.py`/`micro_join.py` → `GET /research/desk/micro/readiness`, materializing an
already-reserved placeholder). `blueprint.md` gets an additive iter-21 documentation note (below)
recording this — no owner, endpoint, or shape change.

## OUT OF SCOPE

- Range-wall failed aggression (Study 1) and capitulation exhaustion (Study 3): predeclared in
  frozen source form only this iteration, NOT passed through `register_and_screen_candidate` —
  explicitly deferred per Success Criteria's "up to two of three pilot studies are deferrable"
  scope-pressure order. Named, not silent.
- Running the pilot grid (or the existing default grid) against the REAL production `.data/` store.
  Consistent with J-04/J-05/J-06's own established precedent (production Scout ledger and fold
  ledger stay empty — J-10's own golden script still asserts "No candidates ledgered." — real runs
  are an explicit future operator act, never a goal-mode-agent act).
- The r5 §10.7 UI-caveat half (attaching the "seal-unaware" disclosure sentence to
  `strategy_trade_readiness`'s served value): `referee_evidence.py` is byte-frozen this era and no
  Rapid-Microscope surface currently consumes the value at all (confirmed: zero production
  callers outside `referee_evidence.py` itself), so there is no live UI/API surface this iteration
  can attach the caveat to without touching a frozen module or a shipped Referee section's
  behavior. DROPPED per T-1 ("ambiguous or unimplementable ⇒ drop, record, surface for an owner
  ruling") — logged to the assumption ledger; the guard/source-scan half (the part that IS
  buildable without touching anything frozen) stays in scope above.
- Any recorder/vault real-tape work (J-06 step 4, forbidden — operator-gated).
- Any `referee_*` module edit, any engine change, any threshold/constant not already pinned in
  spec §1.
- A UI trigger button for the pilot grid (CLI/manager-only this iteration, matching the "operator
  act, not goal-mode act" framing above).

## DEFINITION OF DONE

- [ ] `extract_anchors` supports `structure_context_kind in {"playbook_signal", "band_touch"}`
      without raising `ScoutUnsupportedStructureContextError`
- [ ] Band-touch enumerator built, unit-tested against a fixture band map with known touch instants
- [ ] All three pilot-study candidate requests exist frozen in source (feature/structure_context/
      outcome/econ_floor fully constructed), in goal.md's stated priority order
- [ ] Delta-divergence-at-level-tests candidate fully screened on a committed fixture: §5.4
      disclosures + §5.5 econ column served, walk-forward floor check run, decision recorded in
      the ledger
- [ ] Studies 1 and 3 explicitly named as deferred (not silently dropped) in the dev handoff
- [ ] `joinable_corpus.band_touch_count` serves a real int, not the `not_enumerated` sentinel
- [ ] Guard/source-scan proves zero Rapid-Microscope-module callers of `strategy_trade_readiness`/
      `referee_evidence`
- [ ] J-10 passenger: two dropped Playbook-Evidence assertions restored in `J-10.json`
- [ ] UT-10 passenger: element-capture re-taken, shows the real backend-unavailable panel
- [ ] J-09 passes as at least `partial` via browser-qa-agent (full pass requires Studies 1/3, out
      of scope this iteration); Required-still-passing journeys remain green (deterministic replay
      + LLM fallback)
- [ ] No anti-goal violation introduced
- [ ] Full backend suite green, pass count >= 3,281 (never shrinks), 0 failed, 0 errors
- [ ] `Config().config_fingerprint()` == `08e471b10130e1e2`; all six `referee_*` module SHAs
      byte-identical to the era-opening record
- [ ] TR-1 through TR-30 (incl. TR-17a/b/c) green
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-21-dev.md`

## TESTING REQUIREMENTS

- Browser: J-09 (Scout Ledger + Walk-Forward sections showing the new band_touch-conditioned row);
  J-10 (restored assertions, TR sentinel); J-08 (sections still render); smoke pass on J-01, J-02,
  J-03, J-04, J-05, J-06, J-07 via deterministic replay
- Unit/integration: `test_scout.py` (extract_anchors new paths + pilot grid shape), `test_micro_
  join.py` (band-touch enumerator oracle), `test_micro_readiness.py` (band_touch_count real int),
  `test_walkforward.py` (floor-check refusal path), a new guard test module or extension for the
  `strategy_trade_readiness` source scan
- Error cases: `ScoutUnsupportedStructureContextError` still raised for any genuinely unsupported
  `structure_context_kind`; band-touch enumerator returns an honest empty list (never a fabricated
  touch) when no band map resolves; walk-forward floor check never calls `evaluate_mode_b_fold`
  below floor

Test-first contract:

- TC-1: given `structure_context_kind="band_touch"` and a fixture dataset with a resolvable band
  map, when `extract_anchors` is called, then it returns anchor rows joined via
  `join_band_touch` instead of raising `ScoutUnsupportedStructureContextError`.
- TC-2: given `structure_context_kind="playbook_signal"` and a fixture recorded signal with
  `setup_id="capitulation"`, when `extract_anchors` is called, then it returns an anchor row
  joined via `join_playbook_signal` carrying `setup_id="capitulation"` verbatim.
- TC-3: given a fixture dataset with a known band map and a synthetic trade timeline crossing one
  registered wall at 3 known instants, when the band-touch enumerator runs, then it returns
  exactly 3 ordered touch records for that wall, matching the 3 known instants exactly (a
  hand-derived oracle fixture).
- TC-4: given the three pilot-study candidate-registration requests built in goal.md's stated
  priority order, when their frozen fields are inspected, then all three carry fully-constructed
  `feature`/`structure_context`/`outcome`/`econ_floor` fields and three DISTINCT `family_root_id`
  values (computed per the r2 `sha256(canonical(...))` rule).
- TC-5: given the delta-divergence-at-level-tests request is passed to
  `register_and_screen_candidate` against a committed fixture corpus, when the screen completes,
  then the returned row serves `evidence_class`, the §5.4 concentration/ToD/fallback-tercile
  disclosures, and the §5.5 `econ_interesting` column served BESIDE (never merged into) the
  statistical screen, with `registered_at` strictly before any outcome field is populated in the
  same row (TR-9).
- TC-6: given the delta-divergence candidate's screen has completed, when the walk-forward floor
  check runs against the corpus's `historical_oos`-class session count (zero, on both the real
  store and the fixture), then it serves a typed floor-refusal naming the exact shortfall against
  `WF_TRAIN_MIN_SESSIONS`/`WF_FOLD_MIN_SIGNAL_SESSIONS`, and that refusal is recorded as the
  study's ledger decision (`insufficient_n`) rather than silently omitted.
- TC-7: given the range-wall-failed-aggression and capitulation-exhaustion requests exist in the
  frozen pilot grid, when the grid module is inspected this iteration, then neither has been
  passed through `register_and_screen_candidate` (no partial ledger row for either), and the dev
  handoff names both as explicitly deferred.
- TC-8: given the delta-divergence candidate's screened row exists in a scoped QA fixture backend,
  when browser-qa navigates to `/desk` → Scout Ledger section, then the candidate's row is visible
  and its `structure_context.kind` reads "band_touch" on screen (no hardcoded-`"none"` rendering
  gap).
- TC-9: given a fixture with 3 known wall touches, when `GET /research/desk/micro/readiness` is
  called against that fixture, then `joinable_corpus.band_touch_count` serves the real int `3`,
  not `{"status": "not_enumerated", "count": None}`.
- TC-10: given a source scan of every `micro_*.py`/`scout*.py`/`walkforward*.py`/`vault.py` file,
  when the new guard test runs, then it asserts zero occurrences of `strategy_trade_readiness` or
  `referee_evidence` as an import or call target across those files.
- TC-11: given `J-10.json` steps 9-10 are restored to their pre-iter-16 assertions, when the golden
  replay runs against the scoped QA backend, then both steps pass with 0 failed steps.
- TC-12: given the Scout Ledger section's backend-unavailable state is triggered via the same
  `window.fetch`-override technique UT-10 already used, when
  `data-testid="scout-ledger-unavailable"` is captured directly (element-capture), then the
  screenshot visibly shows the panel's real text ("Backend unreachable — is the API running?" /
  the no-fabrication sentence).
- TC-13: given the full backend suite is run after this iteration's changes, when `pytest`
  completes, then the pass count is >= 3,281, 0 failed, 0 errors, and
  `Config().config_fingerprint()` prints `08e471b10130e1e2`.
- TC-14: given the six `referee_*` module files, when their SHA-256 hashes are recomputed, then
  all six match the era-opening record byte-identically.
- TC-15: given TR-1 through TR-30 (including the TR-17a/b/c triad), when the full trap suite runs,
  then every trap is green, with the new band-touch enumerator specifically checked against TR-3
  (accessor fence — no direct `open()`/`sqlite3.connect` outside `micro_accessor.py`/existing store
  readers) and TR-20 (root-family lineage, covered by TC-4's distinct `family_root_id`s).
- TC-16: given `desk_scout`/`desk_walkforward` MCP tools are invoked after this iteration's
  changes, when compared against their proxied REST GET responses, then they remain byte-identical,
  and `EXPECTED_TOOLS` stays at its already-26-tuple size.

## NOTES

- **Assumption logged:** whether "predeclare... in priority order" (goal.md J-09 step 1) binds the
  SCREENING order too, or only the order in which frozen specs appear in source. We chose: frozen
  specs are written in stated priority order (1, 2, 3), but only the study with the least
  invention risk (delta divergence — its formula is 100% pre-coded) is taken through a screen this
  iteration; the era's own Success Criteria explicitly permits deferring up to two of three.
  Reversible: yes — a later iteration can screen Studies 1/3 in either order without touching
  Study 2's already-recorded decision.
- **Assumption logged:** the r5 §10.7 "seal-unaware `strategy_trade_readiness` caveat, served
  wherever the metric appears" item is split — the guard/source-scan half is built (unambiguous,
  touches nothing frozen); the UI-caveat half is DROPPED this iteration because its only current
  serving surface is the byte-frozen `referee_evidence.py` behind the shipped, unchanged Referee
  Registry section, and no Rapid-Microscope surface consumes the value at all yet. Reversible: yes
  — if a future iteration wires `strategy_trade_readiness` into any NEW (non-frozen) surface, that
  surface carries the caveat from day one; if the owner rules the shipped Referee section may take
  additive disclosure text without breaching the "kept surfaces as shipped" invariant, that
  iteration builds it then.
- **Assumption logged:** "three ledgered study families EXIST with predeclared specs" (J-09
  acceptance) is read as satisfied by frozen, versioned, reviewable source-code specs — matching
  how `default_fixture_grid()`'s `DEFAULT_GRID_FEATURES`/`DEFAULT_GRID_THRESHOLDS` have always
  worked for J-04 — not as requiring a real production ledger write. This keeps J-10's own golden
  script assertion ("No candidates ledgered.") correct and un-touched.
- If extending the scoped QA seeding fixture is needed to make the delta-divergence screen
  genuinely discriminating (a fixture whose known effect is NOT saturated — iter-19's lesson),
  re-run the FULL 6-journey replay set before calling this iteration done (iter-18's lesson).
- Escalation condition carried from spec §10.7: if audit ever finds `strategy_trade_readiness`
  consumed by a live promotion or certificate decision, STOP and escalate immediately — not
  relevant this iteration (zero production callers confirmed), but the guard test above is exactly
  what would catch a future regression into that state.
