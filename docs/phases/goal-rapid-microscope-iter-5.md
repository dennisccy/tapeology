# Goal Iteration 5 — The walk-forward engine: chronology, fences, and one honest diagnostic run

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 5
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — the iteration-4 evaluator verdict was ESCALATE, which grants full depth
  unconditionally regardless of the arbiter's other rungs (the iteration-3 lesson: a plain depth
  *recommendation* is not enough — only a prior ESCALATE/REGRESSION/coherence-FAIL survives the
  arbiter's budget/cadence checks; iteration 3's own full-typed spec was demoted to lean for
  exactly this reason).
- **Frontend Present:** no
- **Target journeys:** J-05
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-10
- **Anti-goal reminders:**
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
    them, never a mutation of them. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
    *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a recorded named seed via per-row
    streams; identical requests reproduce byte-identical results; no wall-clock, no unseeded
    randomness in any research artifact. *(critical)*
  - **No fold geometry change after fold 1** without a recorded voiding event that clears every
    survivor state of that corpus-era. *(critical)*
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
  - **The accessor is the only data door.** No module but `micro_accessor.py` opens snapshot or
    vault event data; origin fences fail closed; import-ban and source-scan guards enforce it.
    *(critical)*
  - **No value is served before it exists.** Every feature carries
    `anchor_at`/`observed_through`/`available_at`; a deferred construct is `unavailable` until
    its observations exist; no outcome for a conditioned anchor begins before the conditioning
    set's maximum `available_at` (TR-17). *(critical)*
  - **The 12 pre-existing tick symbol-days are permanently exploratory** — never sealed, never
    `historical_oos`, never relabeled. *(critical)*
  - **Referee modules are byte-untouched this era** — `referee_handoff_ready` never implies
    current-Referee registrability of a flow predicate; that awaits a future named revision of
    the referee spec. *(critical)*

## GOAL

Give the Rapid Microscope its chronological validation stage: an origin-fenced accessor that
becomes the sole legal door onto snapshot data, a walk-forward engine that proves its own
leakage discipline on synthetic oracles before anything real is measured through it, and one
real diagnostic fold sequence over the 155-session playbook corpus — delivered and served,
worth zero graduation credit by design.

## BACKGROUND

The iteration-4 evaluator verdict was ESCALATE, which grants this iteration full depth
unconditionally (Full trigger 3) and makes its next-step recommendation binding: build J-05
next, because it is the journey that decides which results are ever allowed to count, and the
independent auditor is the only step in this session that has caught a real integrity fault
(twice in iteration 2, four more times in iteration 4). J-05 is also the natural next step in
`docs/goal.md`'s own dependency order (J-01→J-02→J-03→J-04→**J-05**→...) and the largest
unblocker on the board: J-07 (graduation) and J-09 (the pilot studies) both need a working
walk-forward engine before they can do anything.

Two lessons apply directly and are binding on this iteration's shape. First, iteration-4's
lesson (logged twice) that a `Frontend Present: no` spec must not let the browser-qa step skip
the required-still-passing regression set — its own "Applies to" line names "every iteration of
J-05/J-06/J-07/J-09 in this era" verbatim. Iteration 4 made exactly this mistake (zero
screenshots, the whole browser lane SKIPPED); this iteration's TESTING REQUIREMENTS are written
to make that failure structurally harder to repeat. Second, iteration-4's hash-chained-ledger
lesson — "every future hash-chained ledger in this era (`walkforward.py`'s fold ledger...)" —
names this iteration's own new ledger by module name; its tail-anchor pattern (a
separately-persisted `{row_count, head_hash}` written AFTER the row it commits to) is copied in
directly rather than re-deriving the pre-audit chain-only design iteration 4 had to fix twice.
Third, iteration-2's streamed-artifact-completeness lesson names "J-05's fold outputs" in its own
"Applies to" line — the walk-forward compute manager gets the same terminal-state-only
ledger-write discipline `MicroSnapshotComputeManager`/`ScoutComputeManager` already have.

A codebase check (not carried from any prior assumption) also corrects the iteration-3
assumption-ledger's scope prediction: `micro_join.py` is not the only existing direct reader of
`micro_snapshots.read_snapshot_rows` — `scout.py:343` calls it directly too, for its own
candidate-cell construction. Both re-points are in scope this iteration so the TR-3 import-ban
source-scan actually passes against the real tree, not just against the one call site the
iteration-3 note anticipated.

Two owner rulings remain open (the `micro_observer.py` one-quote-early `available_at` stamp;
whether Scout's "variants tried" should also count per data-set) and stay open this iteration —
both are human decisions this agent must not invent (T-1), and neither is a dependency of J-05's
own surface: the diagnostic run reads the playbook corpus's already-computed forward/MDD outcome
statistics (Era B2 reuse), never a `quote_depletion`-conditioned micro feature, and
walk-forward's own ledger has its own provenance fields, untouched by Scout's counting question.
They are carried forward, due before J-06. Two more iteration-4 passenger items (the
"approximately None bps" copy fix; the `_PRICE_ARITHMETIC_FIELDS`/copy-discipline additions for
new micro numerics) are explicitly J-08-scoped ("before any of this is put on screen") and stay
out of scope here.

Because the prior verdict was ESCALATE, the required-still-passing set widens to every currently
non-failing journey (J-01, J-02, J-03, J-04, J-10) rather than a narrow smoke set — which,
usefully, is the whole non-failing board right now, so this is also the natural point to refresh
it fully. The diagnostic run's own corpus (155 sessions of playbook bar data, materially larger
than the 18-file tick corpus J-04 screened) triggers the Constraints' "iteration hygiene" note
(step timeouts tripped in 13 of 15 referee-era iterations) and iteration-4's own "watch the
running time" flag — it is scoped as an explicit compute-manager/CLI act, never a blocking
pytest recomputation, per the shipped desk pattern.

## IN SCOPE

### Backend — J-05 (the chronological walk-forward engine)

- [ ] New `app/research/micro_accessor.py`: an origin-fenced accessor (constructed with an
  `origin` session date) that becomes the sole legal reader of snapshot and ledger-input data
  (spec §6.1); refuses any read beyond `origin` with a typed error, never an empty result;
  treats a sealed shard as invisible except as §7.5 opaque metadata (the vault itself does not
  exist until J-06 — the accessor's vault-event-reading path is written generically so J-06 can
  extend it without re-deriving the origin-fence/import-ban discipline); every outcome-data read
  it serves appends an entry to the §6.7 exposure registry (surface, window, timestamp), so
  there is no unlogged read path.
- [ ] Re-point BOTH existing direct callers of `micro_snapshots.read_snapshot_rows` through the
  new accessor — verified via codebase check to be `micro_join.py:416` (as the iteration-3
  assumption anticipated) AND `scout.py:343` (its own candidate-cell construction, not
  previously anticipated); both callers' served/ledgered values stay byte-identical after
  re-pointing (TC-4, TC-5).
- [ ] A source-scan import-ban guard test (the `test_referee_guards.py` ast-based bidirectional
  import-ban precedent, TR-3) proving no module other than `micro_accessor.py` imports or calls
  the raw snapshot-row reader.
- [ ] New `app/research/walkforward.py` + its own hash-chained append-only fold/sequence ledger
  (the `desk_playbook_log.py`/`scout_ledger.py` pattern) per spec §6.2–§6.8:
  - Fold spec `{corpus_id, corpus_manifest_hash, geometry, clustering_unit, floors,
    registered_at, geometry_hash}`, frozen at registration; `clustering_unit` is always
    `session_date`, never corpus-size-dependent; fold boundaries fall only on session-date
    boundaries; `step_sessions ≥ test_sessions` or registration is refused; a second geometry on
    the same corpus without a recorded voiding event is refused (TR-13), and a voiding event
    clears every survivor state of that corpus-era.
  - Purge by construction from session-truncated labels (TR-6); per-fold-spec derived embargo
    with its derivation recorded (`E=0` legitimate when no cross-boundary dependency is
    identified; the diagnostic run pins its own predeclared `E=5` per `DIAGNOSTIC_GEOMETRY`,
    never treated as a universal default).
  - Mode A: rolling-origin discovery where the frozen fitting RULE (never a realized numeric
    value) is the sequence identity (TR-14); realized fitted values recorded as fold provenance;
    the validation window is revealed only after the spec hash is recorded, with freeze order
    visible in the fold ledger.
  - Mode B: a human-authored spec registered (ledger row, spec hash, timestamp) FIRST, evaluated
    on later windows; evaluation against a window already exposed before `registered_at`
    auto-classes `historical_exposed_diagnostic` (TR-22) — since every window in play this era
    (playbook corpus + 12 legacy tick days) is r2-pre-marked exposed, Mode B structurally cannot
    yet produce `historical_oos` output until J-06 lands genuinely unexposed sealed shards; this
    is the expected, honest state this iteration, not a defect.
  - §6.7 exposure registry: corpus-scoped, hash-chained, r2-initialized with every window of the
    155-session playbook corpus and every one of the 12 legacy tick symbol-days pre-marked
    exposed.
  - §6.8 process labels: `rule_process` vs `operator_process`; a post-reveal operator selection
    labels its sequence `operator_process`, refused at `walkforward_survivor` (TR-21); a
    pre-reveal registered shortlist keeps `rule_process`.
  - §6.6 decay view: per constant-rule sequence, per-fold effect/n/sessions/sign/ToD-regime
    slices/symbol breadth/recent-vs-older consistency; pooling across sequences refused; every
    fold/sequence carries `evidence_class`; class-mixing refused (TR-5); below-floor folds serve
    `insufficient` with their arithmetic; sequences below `WF_MIN_SUFFICIENT_FOLDS` (3) refuse a
    sequence-level verdict; the tick family refuses fold construction outright, naming the
    failed minima (TR-15, `11 < 105`).
  - The explicit `WF_SURVIVOR_RULE_V1` predicate (spec §6.6, all five conditions verbatim)
    implemented with no discretionary override.
- [ ] A `WalkForwardComputeManager` mirroring the shipped single-flight / pollable-progress /
  cancel / CLI-runnable pattern (`MicroSnapshotComputeManager`/`ScoutComputeManager`), plus two
  lessons applied: (iteration-2) terminal-state-only ledger writes — a mid-run exception resolves
  the run to `"failed"`, never a silently-short ledger write; (iteration-4) a separately-persisted
  tail anchor (`{row_count, head_hash}`, written AFTER the row it commits to) beside the hash
  chain, so tail truncation is caught, not only in-place edits. Wire the already-blueprinted
  routes (`GET /research/desk/micro/walkforward`, `POST/GET/POST-cancel .../walkforward/compute`,
  `GET .../walkforward/runs`) into the existing `micro_routes.py`, following the readiness →
  snapshots → scout wiring pattern already there (no new router file).
- [ ] Build synthetic TR-16 oracle fixtures (small, keyless, committed): a known-null corpus
  (zero true effect) and a planted-effect corpus (a registered sign/magnitude); prove both end to
  end through Scout screening + walk-forward folds, plus a byte-identical rerun.
- [ ] TR-3, TR-5, TR-6, TR-13, TR-14, TR-15, TR-16, TR-21, TR-22 (nine traps). Verified via
  codebase check that TR-1, TR-7, TR-8, TR-9, TR-10, TR-11, TR-17, TR-18 are the 8 already
  landed (J-02/J-03/J-04), so this iteration brings the trap suite from 8/22 to 17/22, leaving
  TR-2/TR-4/TR-12/TR-19/TR-20 (5 traps, all vault/recorder-scoped) for J-06/J-07.
- [ ] The diagnostic acceptance run: predeclare (ledgered, before any outcome read) a small
  frozen set of already-shipped playbook setup definitions as the run's candidate rule(s) — the
  specific subset is an implementation choice logged at registration time, never invented from
  outcomes; run the real 155-session playbook bar corpus (2025-06 orphan excluded, disclosed)
  under `DIAGNOSTIC_GEOMETRY` via the compute manager or CLI (not a blocking pytest
  recomputation — budgeted as an explicit, potentially multi-minute operator/CLI act per the
  Constraints' compute-manager-reuse pattern and the iteration-4 "watch the running time" note);
  read the playbook corpus's already-computed forward/MDD outcome statistics (Era B2 reuse) as
  each setup occurrence's effect input, never a recomputation of the detector output itself;
  produces 5 folds / 100 validation sessions, every fold/sequence labeled
  `historical_exposed_diagnostic`.
- [ ] Counter-tests proving diagnostic-class results and `operator_process` sequences award zero
  graduation-relevant (survivor) credit under `WF_SURVIVOR_RULE_V1`, regardless of statistical
  outcome.

### Frontend

None. `Frontend Present: no`. J-05's Steps in `docs/goal.md` name no browser action; the
Walk-Forward section's UI rendering is J-08's scope (already the canonical home registered in
`blueprint.md`'s Information Architecture).

### New user-facing capability

None directly observable this iteration — J-05 is keyless/automated per goal.md's own framing.
The walk-forward engine and its fold/sequence ledger are newly SERVED (queryable via their
endpoints and CLI) but not yet rendered — the same accepted "served ahead of UI wiring" pattern
the coherence audit has approved every iteration since J-02.

### New information displayed

None in the UI this iteration.

### New user actions

None in the UI this iteration. An operator can trigger the diagnostic walk-forward run via the
CLI or `POST /research/desk/micro/walkforward/compute` (a button lands in J-08).

### UI surface changes

None. Every shipped `/desk` section, including the Microscope Readiness panel, continues to
render exactly as shipped (J-01 Do-Not-Redo item).

### Product surface delta

No visible product surface change this iteration.

### Blueprint conformance

J-05's home is already registered in `blueprint.md`'s Information Architecture table
("Walk-forward engine + diagnostic run (J-05) | `/desk` → Walk-Forward | Desk") and its Data
Contract row ("Fold specs, folds, sequences, decay view | new `app/research/walkforward.py` +
its ledger | `GET /research/desk/micro/walkforward`, ...") was written at baseline, anticipating
this journey before the module existed — the same "served ahead of UI wiring" pattern the
coherence audit has approved every iteration since J-02 (iter-2 footnote, `blueprint.md:77-80`).
Re-read this iteration and confirmed still accurate — no IA or Data Contract edit needed; no
nav-skeleton change; no `blueprint.reapproval-requested` file written.

### Data-contract additions

None. The Walk-Forward row was already registered in `blueprint.md`'s Data Contract at baseline;
this iteration builds the module, ledger, and endpoints that row already names. The §6.7
exposure registry and §6.8 process labels are integrity mechanisms that feed that row's own
`evidence_class`/decay-view fields — sub-components of the one already-registered value, not a
second computation or a second endpoint, the same "sub-field of the registered row" reasoning
the coherence audit already applied to J-04's `chain_verification` field
(`runs/goal-session-rapid-microscope/iter-4/coherence.md`).

## OUT OF SCOPE

- `vault.py`, `tick_recorder.py` (J-06) — untouched; the accessor's vault-event-reading path is
  written generically (spec §6.1's "vault event data" clause) but has nothing to read until J-06
  creates sealed shards.
- `micro_graduation.py` (J-07) — untouched; only the native `WF_SURVIVOR_RULE_V1` predicate
  lands (walk-forward's own rule, spec §6.6), never the four-state graduation machine or its
  export bundle.
- Rendering the Walk-Forward section on `/desk`, the `desk_walkforward` MCP tool, or the
  `EXPECTED_TOOLS` bump to 26 — J-08.
- Any pilot-study-specific mechanism (range-wall failed aggression, delta divergence at level
  tests, capitulation exhaustion) — J-09; this iteration's only candidate rules are the
  predeclared playbook-setup diagnostic set and the TR-16 synthetic oracle fixtures, never a
  real microstructure hypothesis.
- TR-1/2/4/7/8/9/10/11/12/17/18/19/20 — owned by other journeys (8 already landed per
  J-02/J-03/J-04; TR-2/4/12/19/20 are vault/recorder-scoped, J-06/J-07); only
  TR-3/5/6/13/14/15/16/21/22 land here.
- Resolving either open owner ruling (the `micro_observer.py` one-quote-early `available_at`
  stamp; whether Scout's "variants tried" should also count per data-set) — both remain
  human-owned and due before J-06, not invented here (T-1); neither is a dependency of J-05's
  own surface (see BACKGROUND).
- The "approximately None bps" kill-message copy fix and the
  `_PRICE_ARITHMETIC_FIELDS`/copy-discipline guard-list additions for new micro numerics —
  explicitly deferred to "before J-08 renders" per iteration-4's own next-step item 4.
- Any change to spec §1 constants (`WF_TRAIN_MIN_SESSIONS`, `WF_SURVIVOR_SIGN_CONSISTENCY`,
  `DIAGNOSTIC_GEOMETRY`, etc.) — frozen; a change is a named revision, never a tuning act.
- Real Alpaca recording, sealed vault shards, or any operator-run tranche act — J-06.
- Any change to Scout's own screening logic, ledger schema, or decisions (J-04 stays a
  Do-Not-Redo item) beyond the single re-pointed internal data-access call proven byte-identical
  by TC-5.
- Any rewrite of `docs/rapid-validation-spec.md` — canonical; an unimplementable or ambiguous
  item is a drop + owner ruling, never an improvised spec change.

## DEFINITION OF DONE

- [ ] J-05: `micro_accessor.py` enforces the origin fence (typed refusal, never empty) and
  sealed-shard invisibility (TC-1, TC-2)
- [ ] J-05: the TR-3 import-ban source-scan passes; `micro_join.py` and `scout.py` are
  re-pointed through the accessor with byte-identical served/ledgered values (TC-3, TC-4, TC-5)
- [ ] J-05: fold-spec registration is frozen (geometry, corpus-size-invariant `session_date`
  clustering, `step ≥ test`) (TC-6, TC-7)
- [ ] J-05: purge is exact by construction and asserted (TR-6); embargo derivation is recorded,
  with `E=0` legitimate when justified (TC-8, TC-9)
- [ ] J-05: geometry freeze (TR-13) and Mode A rule-identity freeze/reveal (TR-14) both hold
  (TC-10, TC-11, TC-12)
- [ ] J-05: Mode B registration-first discipline holds; the exposure registry's r2
  initialization and its mechanical `historical_oos`/diagnostic classing rule (TR-22) both hold
  (TC-13, TC-14)
- [ ] J-05: `WF_SURVIVOR_RULE_V1` is implemented as a discretion-free predicate over all five
  conditions (TC-15)
- [ ] J-05: below-floor folds and below-`WF_MIN_SUFFICIENT_FOLDS` sequences both refuse honestly
  rather than fabricating a verdict (TC-16, TC-17)
- [ ] J-05: class-mixing refusal (TR-5) and process-label discipline (TR-21) both hold (TC-18,
  TC-19)
- [ ] J-05: the tick-family typed floor-refusal (TR-15) names `11 < 105` (TC-20)
- [ ] J-05: TR-16's known-null and planted-effect end-to-end oracles both pass, byte-identical on
  rerun (TC-21, TC-22)
- [ ] J-05: the diagnostic acceptance run completes against the real 155-session playbook corpus
  at the pinned geometry, producing 5 folds / 100 validation sessions, all
  `historical_exposed_diagnostic` (TC-23)
- [ ] J-05: diagnostic-class and `operator_process` sequences are counter-tested to award zero
  graduation-relevant (survivor) credit (TC-24)
- [ ] J-05: the walk-forward compute manager applies the iteration-2 streamed-artifact-
  completeness lesson (terminal-state-only ledger writes) and the iteration-4 tail-truncation
  lesson (a separately-persisted tail anchor) (TC-25, TC-26)
- [ ] Frozen-foundation re-checks pass: fingerprint `08e471b10130e1e2`, all 6 `referee_*` hashes
  match the iteration-0 listing, `app/engine/`/`desk_playbook.py`/`desk_playbook_context.py`
  byte-freeze holds, the 18 real-corpus snapshot files' row total is unchanged at 3,815,933
  (TC-27)
- [ ] Full backend suite passes at a count ≥ 2,949 pass / 8 skip (iteration-4 baseline), 0 new
  failures (TC-28)
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-10 remain green — browser-qa-agent
  ACTUALLY runs this regression set this iteration (screenshots on record), regardless of
  `Frontend Present: no` (TC-29)
- [ ] No anti-goal violation introduced
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-5-dev.md`

## TESTING REQUIREMENTS

- Browser: J-01 (Microscope Readiness panel, screenshot on record); J-02, J-03, J-04 (no
  dedicated UI surface of their own — re-verified via the same shared-panel check J-01 already
  covers, the iteration-2/3/4 precedent; an honest SKIP is recorded for their own acceptance,
  never an unscored gap); J-10's full `journey-scripts/J-10.json` 13-step sentinel (screenshots
  on record), already repaired in iteration 3 — re-run unmodified, do not re-point it
  (Do-Not-Redo item). **BINDING:** this is a `Frontend Present: no` iteration, but per the
  iteration-4 lesson (logged twice — "a `Frontend Present: no` iteration spec makes the
  browser-qa step skip the WHOLE pass" and "a regression set is not a frontend-delta question —
  whenever a spec names required-still-passing journeys, the browser lane must run them
  regardless of `Frontend Present`") — the browser-qa-agent step MUST execute this iteration's
  required-still-passing set exactly as if this were a frontend-touching iteration. A blanket
  SKIP across J-01/J-02/J-03/J-04/J-10 is not an acceptable outcome of this spec; it is the exact
  failure iteration 4 already made once. J-05 alone (no dedicated UI surface, per its own
  Acceptance text) records an honest SKIP for itself.
- Unit/integration: new `tests/test_micro_accessor.py` (origin fence, sealed-shard invisibility,
  import-ban source-scan — TR-3); new `tests/test_walkforward.py` (fold-spec registration,
  purge/embargo, Mode A/B, `WF_SURVIVOR_RULE_V1`, decay view, class labels, process labels — TR-5,
  TR-6, TR-13, TR-14, TR-15, TR-21, TR-22); a dedicated TR-16 oracle test module plus its two
  synthetic fixture corpora; extended `tests/test_scout.py` / `tests/test_scout_ledger.py` and
  `tests/test_micro_join.py` proving the accessor re-point is byte-identical (TC-4, TC-5); the
  diagnostic-run proof invoked via CLI or a dedicated slow/marked test reading the real 155-session
  playbook corpus; existing `test_micro_snapshots.py` / `test_micro_observer.py` /
  `test_observer_equivalence.py` / `test_dense_replay_gate.py` / `test_micro_features.py` /
  `test_micro_readiness.py` / `test_referee_guards.py` re-run unmodified; full suite re-run via
  `pytest tests/` (no extra `-q` — `pyproject.toml`'s `addopts = "-q"` swallows the summary line,
  the iteration-0 lesson) to read the exact pass/skip count directly.
- Error cases: an origin-T accessor read beyond T raises a typed error, never an empty result; a
  read attempt against a sealed fixture shard outside §7.5 metadata is refused; an import of
  `read_snapshot_rows` from anywhere but `micro_accessor.py` fails the source-scan; a second,
  different geometry registered on an already-fold-1'd corpus without a voiding event is refused;
  a fold below its floors serves `insufficient` rather than a fabricated pass/fail; a sequence
  with a post-reveal operator selection is refused at `walkforward_survivor` even if it would
  otherwise qualify; a fold request against the 11-session tick corpus returns the typed
  floor-refusal, never an empty report; a truncated walk-forward ledger (newest row(s) deleted
  directly from disk) is caught by the tail anchor even when the remaining chain still verifies.

- TC-1: given an accessor constructed with `origin = T` over a fixture snapshot spanning sessions
  before and after T, when a read is requested for a row/window dated after T, then the accessor
  raises a typed error (never an empty list or a silently-truncated result).
- TC-2: given a fixture shard flagged `sealed` in the accessor's view, when the accessor is
  queried for that shard's event data or outcome aggregates, then it returns only §7.5 opaque
  metadata (or a typed refusal) — never the underlying rows.
- TC-3: given the full backend source tree, when the TR-3 import-ban source-scan (ast-based, the
  `test_referee_guards.py` precedent) runs, then no module other than `micro_accessor.py`
  contains an import of `read_snapshot_rows` (or any other raw snapshot/vault-event opener).
- TC-4: given `micro_join.py`'s snapshot-row read call is re-pointed from
  `micro_snapshots.read_snapshot_rows` to the new accessor, when `joinable_corpus_counts` is
  called against the real `.data/datasets` and playbook stores before and after the re-point,
  then `playbook_signal_count` stays `2` and `by_setup_id` stays `{"range_trade": 2}` — the
  re-point changes only the internal read path, never the served arithmetic.
- TC-5: given `scout.py`'s direct `read_snapshot_rows` call at its candidate-cell construction
  site is re-pointed through the same accessor, when the iteration-4 bounded fixture grid is
  re-run through `ScoutComputeManager`, then every candidate's `spec_hash`/`decision`/`reason` in
  `scout_ledger.py` is byte-identical to its pre-re-point value.
- TC-6: given a fold spec is registered with `geometry`, `clustering_unit`, and `floors` fields,
  when the spec is re-read after registration, then all fields are frozen exactly as registered,
  and `clustering_unit` reads `session_date` regardless of whether the corpus is the 155-session
  playbook corpus or the 11-session tick corpus.
- TC-7: given a fold-spec registration where `step_sessions` < `test_sessions`, when registration
  is attempted, then it is refused (pooled statistics over overlapping validation windows are
  never constructed).
- TC-8: given a synthetic fixture with a label planted to cross a fold's session-date boundary,
  when the fold build runs, then it fails with a purge-exactness error naming the crossing label,
  and session-truncation is asserted (not merely assumed) for every fold in the run.
- TC-9: given a fold spec whose session-truncated labels and prefix-only features leave no
  identified cross-boundary dependency, when embargo is derived, then `embargo_sessions = 0` is
  accepted with its derivation recorded as legitimate; separately, the diagnostic run's own fold
  spec records `embargo_sessions = 5` as its predeclared choice, not as a value implied by any
  universal rule.
- TC-10: given a fold spec already registered for a corpus with fold 1 completed, when a second,
  different geometry is registered for that same `corpus_id` without a voiding event, then
  registration is refused; when a voiding event IS recorded, then every existing survivor state
  for that corpus-era reads as void afterward.
- TC-11: given a sequence at multiple origins under the fitting rule `training_quantile(0.90)`,
  when each origin's refit runs, then all origins stay in the SAME sequence; when the rule string
  is then changed (e.g. to `training_quantile(0.95)`), then a NEW sequence starts rather than
  extending the prior one.
- TC-12: given a Mode A origin's candidate generation and fitting have completed, when the spec
  hash is recorded, then the validation window's outcome is not readable through the accessor
  until AFTER that recording — the fold ledger's freeze-order timestamps show spec-hash-then-
  reveal, never the reverse.
- TC-13: given a Mode B spec is registered with `registered_at` AFTER a logged exposure-registry
  entry for its validation window, when it is evaluated, then it is auto-classed
  `historical_exposed_diagnostic`.
- TC-14: given a freshly initialized exposure registry, when any window of the 155-session
  playbook corpus or any of the 12 legacy tick symbol-days is queried for its exposure state,
  then it reads already-exposed from r2 initialization, before any explicit serving act in this
  run.
- TC-15: given five synthetic sufficient folds — all class `historical_oos` and `rule_process`,
  sign-agreement ≥ `WF_SURVIVOR_SIGN_CONSISTENCY` (0.7), pooled effect in the registered direction
  ≥ the family's econ floor, no sufficient fold in the opposite direction, and zero voiding
  events — when `WF_SURVIVOR_RULE_V1` evaluates the sequence, then it returns
  `walkforward_survivor`; when any ONE of the five conditions is individually violated in an
  otherwise-identical fixture, then it does not.
- TC-16: given a fold with fewer than `WF_FOLD_MIN_OBSERVATIONS` (30) observations, or fewer than
  `WF_FOLD_MIN_SIGNAL_SESSIONS` (8) signal-carrying sessions, or fewer than `WF_FOLD_MIN_SYMBOLS`
  (2) symbols, when that fold is served, then its status reads `insufficient` with the specific
  failed-minimum arithmetic attached, never a fabricated numeric result.
- TC-17: given a sequence with fewer than `WF_MIN_SUFFICIENT_FOLDS` (3) sufficient folds, when a
  sequence-level verdict is requested, then the response is a refusal naming the shortfall, never
  a computed verdict.
- TC-18: given one `historical_exposed_diagnostic` fold and one `historical_oos` fold from the
  same family, when a pooled statistic across both is attempted, then it is refused; and the
  diagnostic fold is independently confirmed to contribute nothing to any survivor/graduation-
  relevant tally.
- TC-19: given a sequence where a human or proposer selection is logged AFTER a fold reveal
  (choosing among Mode-A outputs), when `walkforward_survivor` is evaluated for it, then it is
  refused regardless of its statistics and labeled `operator_process`; given an otherwise-
  identical sequence whose selection was logged BEFORE any reveal (a registered shortlist), then
  it keeps `rule_process` and is eligible.
- TC-20: given a fold request pointed at the 18-dataset/11-session tick corpus, when the request
  is made, then the response is a typed floor-refusal naming `11 < 105`, never an empty fold
  report.
- TC-21: given the synthetic TR-16 known-null corpus (no true effect), when it is run end to end
  through Scout screening and walk-forward folds, then no sequence reaches
  `walkforward_survivor`; a byte-identical rerun over the unchanged fixture reproduces the same
  result.
- TC-22: given the synthetic TR-16 planted-effect corpus (a registered sign and magnitude), when
  it is run end to end through the same pipeline, then the recovered sequence's sign matches the
  planted sign and its magnitude falls within the fixture's stated tolerance of the planted value
  (mid-basis outcome primary); a byte-identical rerun reproduces the same recovered values.
- TC-23: given the real 155-session playbook bar corpus with the 2025-06 orphan session excluded
  and disclosed, when the diagnostic acceptance run executes under `DIAGNOSTIC_GEOMETRY`
  (train=40, embargo=5, test=20, step=20) via the compute manager or CLI, then it produces
  exactly 5 folds spanning 100 validation sessions, and every served fold and sequence carries
  `evidence_class: historical_exposed_diagnostic`.
- TC-24: given the diagnostic run's completed folds/sequences (all `historical_exposed_
  diagnostic`) and a synthetic `operator_process`-labeled sequence, when each is evaluated under
  `WF_SURVIVOR_RULE_V1`, then every one returns not-a-survivor, regardless of its own statistical
  sign or magnitude.
- TC-25: given a walk-forward compute run already in `"running"` state, when
  `WalkForwardComputeManager.trigger()` is called a second time before the first resolves, then
  it returns `{"state": "refused", "reason": "already_running"}` and no second worker starts;
  given a mid-run exception in either the diagnostic run or a fixture run, then the run resolves
  to a terminal `"failed"` run-log entry rather than leaving a partially-written fold/sequence
  row.
- TC-26: given the walk-forward ledger's newest committed row(s) are deleted directly from the
  JSONL file after being written (simulating tail truncation), when the ledger's integrity check
  reads the separately-persisted tail anchor (`row_count`/`head_hash`) against the file's actual
  tail, then the mismatch is detected and reported — not just an in-place edit's chain-
  verification break.
- TC-27: given the iteration-0 fingerprint and referee-hash baseline and the iteration-3 snapshot
  row-total baseline, when re-checked this iteration, then `Config().config_fingerprint()` still
  prints `08e471b10130e1e2`, all 6 `referee_*.py` SHA-256 hashes match the iteration-0 listing,
  `app/engine/`/`desk_playbook.py`/`desk_playbook_context.py` show an empty diff, and the 18
  real-corpus snapshot files' row total read straight off disk is still 3,815,933.
- TC-28: given the full backend suite after this iteration's changes, when `pytest tests/` runs
  (no extra `-q`), then the reported pass count is ≥ 2,949 with 8 skip and 0 new failures.
- TC-29: given the store-scoped browser rig, when browser-qa-agent runs J-01/J-02/J-03/J-04's
  checks and J-10's full sentinel script, then every previously-green step stays green
  (screenshots on record for J-01 and J-10) and J-05 records an honest SKIP rather than an
  unscored gap — and the pass is NOT recorded as a blanket SKIP across the whole
  required-still-passing set.

## NOTES

- Evaluator's iteration-4 next-step recommendation (binding this iteration): build J-05 next
  under the full pipeline, because it decides which results are allowed to count and the
  independent auditor is the only step in this session that has ever caught that class of
  mistake.
- Lesson applied (iteration 4, logged twice — browser lane vs. `Frontend Present: no`): this
  iteration's TESTING REQUIREMENTS state, in bold, that the browser-qa-agent step must run the
  full required-still-passing set regardless of the frontend flag. This is the primary process
  fix this iteration carries forward from the ESCALATE verdict.
- Lesson applied (iteration 4, hash-chained ledger tail truncation — "Applies to: ...
  `walkforward.py`'s fold ledger"): the new ledger gets a separately-persisted tail anchor from
  day one (TC-26), not the pre-audit chain-only design that needed two later fixes for
  `scout_ledger.py`.
- Lesson applied (iteration 2, streamed-artifact completeness — "Applies to: ... J-05's fold
  outputs"): `WalkForwardComputeManager` gets the same terminal-state-only ledger-write
  discipline the shipped managers already have (TC-25).
- Lesson applied (iteration 3, `feature_source_hash` rebuild risk): this iteration's diff does
  not touch `micro_features.py`/`micro_observer.py`, so no whole-corpus snapshot rebuild is
  expected; TC-27 verifies the row total anyway as the cheap proxy check the lesson recommends.
- Lesson applied (iteration 0, suite count): run `pytest tests/` (no extra `-q`) or add `-v` to
  read the exact pass/skip count directly rather than reconstructing it from dot-grid characters.
- Lesson applied (iteration 2, J-10 test-rig pinning): not reopened. Iteration 3's repair of
  `journey-scripts/J-10.json` is a Do-Not-Redo item; reused unmodified.
- Active blockers (human-owned, unresolved this iteration, carried forward due before J-06): (a)
  the owner ruling on `micro_observer.py:636/657`'s one-quote-early depletion `available_at`
  stamp; (b) whether Scout's "variants tried" bucket should also be counted per data-set. Neither
  invented here (T-1); neither is a dependency of J-05's own surface (see BACKGROUND).
- Two more iteration-4 passenger items (the "approximately None bps" kill-message copy fix; the
  `_PRICE_ARITHMETIC_FIELDS`/copy-discipline additions for new micro numerics) are explicitly
  J-08-scoped ("before J-08 renders") and are not this iteration's job.
- Running-time caution (iteration-4's own note, and the Constraints' iteration-hygiene rail):
  the diagnostic run's 155-session real playbook corpus is materially larger than the 18-file
  tick corpus J-04 screened. Run it as an explicit compute-manager/CLI act (resumable,
  progress-pollable, cancelable), never inline inside a blocking pytest run, and keep hermetic CI
  tests on small synthetic/fixture corpora — mirroring exactly how J-02's snapshot builds and
  J-04's fixture-grid screen already separate "prove the mechanics on fixtures" from "run the
  real, possibly slow, corpus act."
- No interpretive call was logged to the assumption ledger this iteration — the scope questions
  encountered (which playbook setups to predeclare for the diagnostic run; the exact orphan
  session date) are implementation choices disclosed at build time, not goal ambiguities
  requiring an interpretation.
- `blueprint.md` was re-read and confirmed already accurate for this iteration's scope (the
  Walk-Forward row was pre-registered at baseline); no edit made.
