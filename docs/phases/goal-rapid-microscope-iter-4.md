# Goal Iteration 4 — The Scout and the ledger: every trial on the record, honestly denominated

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 4
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — the iteration-3 evaluator verdict was ESCALATE, which grants full depth
  unconditionally regardless of the arbiter's other rungs (the iter-3 lesson: a mere depth
  recommendation is not enough — only a prior ESCALATE/REGRESSION/coherence-FAIL survives the
  arbiter's budget/cadence checks).
- **Frontend Present:** no
- **Target journeys:** J-04
- **Required-still-passing journeys:** J-01, J-02, J-03, J-10
- **Anti-goal reminders:**
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
    them, never a mutation of them. *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R,
    n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language,
    no imperative trading cues. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
    *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a recorded named seed via per-row
    streams; identical requests reproduce byte-identical results; no wall-clock, no unseeded
    randomness in any research artifact. *(critical)*
  - **The denominator never shrinks.** Every evaluated variant lands in the hash-chained ledger
    with a closed-vocabulary decision; kills are never deleted; the union-N across grid
    versions is served beside every family. *(critical)*
  - **No threshold, grid, formula, embargo, or fold parameter is chosen or revised from
    validation, sealed, or holdout outcomes.** Fitting rules are data functionals frozen before
    reveal; per-origin refits under an unchanged rule are provenance, never a new choice.
    *(critical)*
  - **Evidence classes never mix.** No `historical_exposed_diagnostic` output feeds a gate, a
    graduation transition, a certificate, a promotion, or a pooled statistic with
    `historical_oos` rows; nothing in this era emits `live_confirmatory`. *(critical)*
  - **No value is served before it exists.** Every feature carries
    `anchor_at`/`observed_through`/`available_at`; a deferred construct is `unavailable` until
    its observations exist; no outcome for a conditioned anchor begins before the conditioning
    set's maximum `available_at` (TR-17). *(critical)*
  - **No microstructure claim beyond what L1 supports.** `refill_consistent` is the strongest
    liquidity label; "iceberg", institutional-intent, and manipulation language are banned;
    every aggressor-derived quantity is served beside its `fallback_frac` and `unknown_frac`.
    *(critical)*
  - **No cross-unit liquidity arithmetic.** No feature, screen, or study relates trade shares to
    displayed quote sizes unless the dataset's `quote_size_unit` is verified (spec §2.6);
    unverified or mixed units are a typed refusal; unit normalization exists only as a recorded
    verification act, never silent arithmetic. *(critical)*

## GOAL

Give the Rapid Microscope its first falsification stage: a Scout that screens bounded,
pre-registered candidate mechanisms against the joinable corpus and permanently, honestly
ledgers every trial — including every kill — with its true across-grid-version denominator,
plus two small honesty fixes to the already-shipped corpus-readiness payload.

## BACKGROUND

The evaluator's iteration-3 verdict was ESCALATE, and its next-step recommendation is binding:
build J-04 next, and run it under the full pipeline so the independent auditor is in the loop,
because the auditor is the only step in this session that has caught a real honesty fault (twice,
in iteration 2) and J-04 is the journey that must never lose the record of a failed trial. That
verdict alone grants full depth unconditionally (Full trigger 3 — the iter-3 lesson names this as
the ONLY rung that survives the arbiter's budget/cadence checks; a mere depth recommendation would
not have been enough). J-04 carries four passenger items from iteration 3's eval: two are small,
in-scope honesty fixes to the already-shipped `joinable_corpus` field (the discarded playbook-store
error channel at `micro_join.py:381`, and the bare-`0` `band_touch_count`); the third — an owner
ruling on `micro_observer.py`'s one-quote-early depletion `available_at` stamp — is still due and
is a HUMAN decision this agent must not invent (T-1), so this iteration scopes around it by
excluding `quote_depletion`-conditioned candidates from J-04's registered grid (logged to the
assumption ledger) rather than blocking the whole journey or guessing a fix; the fourth
(re-photographing Microscope Readiness) is evidence-only and rides passively on this iteration's
required J-01/J-10 browser regression pass, per the no-evidence-only-iteration rule. Because the
prior verdict was ESCALATE, the regression set also widens to every currently non-failing journey
(J-01, J-02, J-03, J-10) rather than a narrow smoke set. Two lessons shape the IN SCOPE list
directly: iteration 2's streamed-artifact-completeness lesson (its own "Applies to" line names
J-04's screens) is met by giving the new `ScoutComputeManager` the same terminal-state-only
ledger-write discipline `MicroSnapshotComputeManager` already has; iteration 3's
`feature_source_hash`-rebuild lesson is inert here since this iteration's diff never touches
`micro_features.py`/`micro_observer.py`, but TC-18 verifies the 3,815,933-row snapshot total stays
unchanged anyway, the cheap check that lesson recommends.

## IN SCOPE

### Backend — J-04 (the Scout + exploratory candidate ledger)

- [ ] New `app/research/scout_ledger.py`: hash-chained append-only JSONL ledger per spec §5.2 —
  candidate spec fields (§5.1: `candidate_id`, `family_id`, `family_root_id` computed per the r2
  formula `sha256(canonical(feature_family_name, structure_context_kind,
  outcome_horizon_family))[:16]`, `feature`, `structure_context`, `outcome`, `fitting_rule?`,
  `econ_floor`, `corpus_manifest`, `grid_version`, `registered_at`, `spec_hash`); one permanent
  row per evaluated variant (`decision: survive|<KILL_REASONS>`, `reason`, `notes`, the family's
  running `variants_tried` union-N across grid versions); `superseded` rows point at their
  successor and are never deleted; chain-verification (TR-11).
- [ ] New `app/research/scout.py`: spec §5.3 screening (cluster unit = `session_date` for both
  families, frozen/corpus-size-invariant; within-session circular block permutation as the null,
  block length ≥ the longest evaluated horizon's label span; the banned plain row-shuffle kept
  ONLY as a counter-test fixture, never reachable from a production call path; non-overlapping
  anchor subsampling for clock-horizon effects), §5.4 mandatory disclosures (session/symbol
  concentration, ToD-bucket slices, fallback-tercile stratification for aggressor-derived
  features, the best-of-N expected-max-under-null disclosure, `evidence_class`), §5.5 economic
  relevance (`econ_interesting` served beside — never merged into — the statistical screen, with
  the frozen proxy sentence verbatim), the `SCOUT_MAX_VARIANTS_PER_FAMILY` (24) grid bound.
- [ ] A `ScoutComputeManager` mirroring `micro_snapshots.MicroSnapshotComputeManager`'s
  single-flight (`{"state": "refused", "reason": "already_running"}` on a concurrent trigger),
  pollable-progress, cooperative-cancel, terminal-state-only-ledger-write pattern; wire the three
  already-blueprinted routes (`GET /research/desk/micro/scout`, `POST/GET/POST-cancel
  .../scout/compute`, `GET .../scout/runs`) into the existing `micro_routes.py` alongside the
  readiness/snapshots routes (no new router file, no new store dependency provider).
- [ ] Register a bounded (≤ `SCOUT_MAX_VARIANTS_PER_FAMILY` per family) fixture grid — reusing the
  committed hermetic fixtures already wired for J-02/J-03 (`apps/backend/tests/fixtures/datasets/`
  and `apps/backend/tests/fixtures/datasets_j03/`) plus a purpose-built synthetic
  session-clustered fixture for TR-8's calibration — and run it end to end through both the
  manager and an embedded CLI `main()`/argparse entry point (the `micro_snapshots.py` precedent),
  killing and advancing per the recorded results (an all-`killed_insufficient_n` outcome on the
  tiny fixture corpus is an honest, acceptable result — this era's own Vision: "zero survivors is
  a passing grade").
- [ ] TR-8 (200-seed calibration on the autocorrelated known-null fixture, screen pass-rate ≤
  1.5 × `SCOUT_SCREEN_ALPHA` = 0.075, plus the banned-shuffle counter-test demonstrably failing
  that same ceiling), TR-9 (a candidate whose econ-floor inputs were read before `registered_at`
  is refused), TR-10 (adding 100 null candidates at an origin changes no prior candidate's fitted
  threshold or pass/fail), TR-11 (union-N spans grid versions; an in-place edit of row *k* breaks
  chain verification at *k*).
- [ ] This iteration's registered grid excludes any candidate whose conditioning `feature.name` is
  `quote_depletion` (see NOTES and the iter-4 assumption-ledger entry — the flagged one-quote-early
  `available_at` stamp on `micro_observer.py:636/657` stays unresolved and unrelied-upon; every
  other Wave-1 family — F-FLOW, F-RESPONSE, the rest of F-LIQUIDITY — stays eligible).

### Backend — passenger fixes (carried from iteration 3's next-step recommendation)

- [ ] `micro_join.py:381` (`joinable_corpus_counts`): read the playbook store's currently-discarded
  `_errors` return value and surface it — report the corruption beside the count (the same
  discipline dataset errors already get elsewhere in this module family) or refuse outright;
  never a silent undercount.
- [ ] `micro_join.py` / `micro_readiness.py` (`band_touch_count`): serve a typed "not enumerated"
  state that a reader cannot mistake for a real zero count — still owned by `micro_join.py`, still
  served by the existing `GET /research/desk/micro/readiness` (no new endpoint, no UI change,
  defining an actual touch stays J-09's job).

### Frontend

None. Frontend Present: no. J-04's Steps in `docs/goal.md` name no browser action; the Scout
Ledger section's UI rendering is J-08's scope (already the canonical home registered in
`blueprint.md`'s Information Architecture).

### New user-facing capability

None directly observable this iteration — J-04 is keyless/automated per goal.md's own framing.
The Scout Ledger is newly SERVED (queryable via its endpoints and the CLI) but not yet rendered;
that is the same accepted "served ahead of UI wiring" pattern the iter-2 coherence audit approved
for J-02's snapshot endpoints and iter-3's coherence audit re-confirmed for J-03's `joinable_corpus`
field.

### New information displayed

None in the UI this iteration.

### New user actions

None in the UI this iteration. An operator CAN trigger a Scout screening run via the CLI or
`POST /research/desk/micro/scout/compute` (a button lands in J-08).

### UI surface changes

None. Every shipped `/desk` section, including the Microscope Readiness panel, continues to
render exactly as shipped (J-01 Do-Not-Redo item).

### Product surface delta

No visible product surface change this iteration.

### Blueprint conformance

J-04's home is already registered in `blueprint.md`'s Information Architecture table ("Scout +
candidate ledger (J-04) | `/desk` → Scout Ledger | Desk") and its Data Contract row ("Scout
trials, kills, denominators, screens | new `app/research/scout_ledger.py` + `scout.py` |
`GET /research/desk/micro/scout`, ...") was written at baseline, anticipating this journey before
either module existed. Re-read this iteration and confirmed still accurate — no IA or Data
Contract edit needed. The two passenger fixes refine fields already inside the existing "Corpus
readiness truth ... joinable-corpus counts" row (same owner `micro_join.py`, same endpoint) — not
a new value, no edit needed there either. No nav-skeleton change; no
`blueprint.reapproval-requested` file written.

### Data-contract additions

None. The Scout Ledger row was already registered in `blueprint.md`'s Data Contract at baseline;
this iteration builds the module + endpoints that row already names, with no second computation
or second endpoint anywhere. The two passenger fixes change field HONESTY (never a bare `0`,
never a silently-discarded error) inside the existing `joinable_corpus` object, not its owner or
its endpoint.

## OUT OF SCOPE

- Any Scout candidate conditioned on `quote_depletion`, and any fix to `micro_observer.py`'s
  one-quote-early `available_at` stamp — the owner ruling is still due; not invented here (T-1).
- `micro_accessor.py` / `walkforward.py` (J-05) — J-04 continues reading through
  `micro_snapshots.read_snapshot_rows` / `micro_join.py`, the same plain-reader boundary iter-3
  already established; J-05 re-points it as part of its own scope.
- `tick_recorder.py` / `vault.py` (J-06), `micro_graduation.py` (J-07) — untouched.
- Any pilot-study-specific mechanism (range-wall failed aggression, delta divergence at level
  tests, capitulation exhaustion) — that is J-09; J-04 only builds the generic Scout + ledger
  machinery and runs it on a bounded FIXTURE grid, never a study-specific hypothesis.
- Rendering the Scout Ledger section on `/desk`, the `desk_scout` MCP tool, or the
  `EXPECTED_TOOLS` bump to 26 — J-08.
- The real ~150-symbol-day corpus or any operator-run recording act — J-06's scope; `docs/goal.md`
  names only "the fixture family's ledger" in J-04's own Acceptance text.
- Any change to `KILL_REASONS`, `SCOUT_*`, `ECON_FLOOR_SPREAD_MULTIPLE`, or any other spec §1
  constant — frozen; a change would be a named revision, never a tuning act.
- TR-1…TR-7, TR-12…TR-22 — owned by other journeys; only TR-8/9/10/11 land here per goal.md's own
  J-04 step 3.
- Completing the full TR-1…TR-22 trap suite or declaring J-10 fully "passing" — structurally
  spread across J-02…J-07 by goal.md's own design; this iteration adds 4 more traps (4 of 22 →
  8 of 22), J-10's overall verdict stays the evaluator's call.
- Any rewrite of `docs/rapid-validation-spec.md` — the spec is canonical; an unimplementable or
  ambiguous item is a drop + owner ruling, never an improvised change to the spec itself.

## DEFINITION OF DONE

- [ ] J-04: every variant in the registered bounded fixture grid lands in `scout_ledger.py` with a
  closed-vocabulary `decision`/`reason`, and the served `variants_tried` equals the union-N across
  grid versions (TC-1, TC-2)
- [ ] J-04: ledger tamper detection and `superseded` pointer semantics hold (TC-3, TC-4)
- [ ] J-04: TR-8 calibration and its banned-shuffle counter-test both pass (TC-5, TC-6)
- [ ] J-04: TR-9 registration-ordering refusal passes (TC-7)
- [ ] J-04: TR-10 pool invariance passes (TC-8)
- [ ] J-04: `SCOUT_MAX_VARIANTS_PER_FAMILY` bound is enforced (TC-9)
- [ ] J-04: the compute manager enforces single-flight and, together with the CLI, produces
  byte-identical ledger rows for the same grid (TC-10, TC-11)
- [ ] J-04: the served screen carries `evidence_class`, the best-of-N disclosure, and the economic
  column with the frozen proxy sentence verbatim (TC-12)
- [ ] J-04: zero registered candidates condition on `quote_depletion` this iteration (TC-13)
- [ ] Passenger fix: a corrupt playbook record surfaces honestly in `joinable_corpus`, never a
  silent undercount (TC-14)
- [ ] Passenger fix: `band_touch_count` serves a typed "not enumerated" state distinguishable from
  a real zero (TC-15)
- [ ] The real-corpus `joinable_corpus` enumerated arithmetic is unchanged by the passenger fixes
  (TC-16)
- [ ] Frozen-foundation re-checks pass: fingerprint `08e471b10130e1e2`, all 6 `referee_*` hashes
  match the iteration-0 listing, engine/`desk_playbook.py`/`desk_playbook_context.py` byte-freeze
  holds (TC-17)
- [ ] The 18 real-corpus snapshot files' row total is unchanged at 3,815,933 (TC-18)
- [ ] Full backend suite passes at a count ≥ 2,866 pass / 8 skip (iteration-3 baseline), 0 new
  failures (TC-19)
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-10 remain green (deterministic replay +
  LLM fallback); J-04 records an honest SKIP in the browser-qa pass, matching J-02/J-03's
  precedent (TC-20)
- [ ] No anti-goal violation introduced
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-4-dev.md`

## TESTING REQUIREMENTS

- Browser: J-01, J-02, J-03 (all currently SKIP or PASS with no dedicated UI surface beyond the
  already-shipped Microscope Readiness panel — re-verify unchanged); J-10's full kept-product
  sentinel script (`journey-scripts/J-10.json`), already repaired in iteration 3 — re-run
  unmodified, do not re-point it (Do-Not-Redo item). J-04 has no browser surface this iteration
  (Scout Ledger UI rendering is J-08's scope) — the browser-qa pass records an honest SKIP for
  J-04, the same precedent already established for J-02/J-03, not an `unknown`/evidence gap, since
  `docs/goal.md`'s own J-04 Acceptance text names no browser check.
- Unit/integration: new `tests/test_scout_ledger.py` (hash-chain integrity, `superseded`
  semantics, union-N across grid versions — TR-11) and `tests/test_scout.py` (screening procedure,
  disclosures, econ-floor column — TR-8/9/10); a dedicated TR-8 calibration test (200 seeds,
  autocorrelated null fixture, pass-rate ceiling, banned-shuffle counter-test); a manager/CLI
  parity test; `tests/test_micro_join.py` extended for the corrupt-record and `band_touch_count`
  fixes; `tests/test_micro_readiness.py` extended for the new `band_touch_count` shape; the
  existing `test_micro_snapshots.py` / `test_micro_observer.py` / `test_observer_equivalence.py` /
  `test_dense_replay_gate.py` / `test_micro_features.py` suites re-run unmodified; full suite
  re-run via `pytest tests/` (no extra `-q` — `pyproject.toml` already sets `addopts = "-q"`, the
  iter-0 lesson) to get the exact pass/skip count directly.
- Error cases: a candidate spec whose econ-floor inputs were read before `registered_at` is
  refused (TR-9), never silently ledgered; a ledger row edited in place breaks chain verification
  at that row (TR-11); a 25th variant submitted to a family already at
  `SCOUT_MAX_VARIANTS_PER_FAMILY` (24) is refused; a concurrent `trigger()` call while a screening
  run is already `"running"` returns `{"state": "refused", "reason": "already_running"}`, never a
  second run; a corrupt playbook record surfaces in `joinable_corpus`'s response rather than
  silently shrinking the count; the banned plain row-shuffle null demonstrably exceeds the TR-8
  pass-rate ceiling when substituted for the block-permutation null.

- TC-1: given a bounded fixture grid registered for one family (candidate specs frozen with
  `spec_hash`/`registered_at`/`econ_floor` inputs BEFORE any outcome is read), when
  `scout.py`'s screen runs it end to end via `ScoutComputeManager`, then `scout_ledger.py`'s JSONL
  contains exactly one permanent row per registered variant, each with `decision` in
  `{"survive"} | KILL_REASONS` (`killed_null`, `killed_direction`, `killed_insufficient_n`,
  `killed_concentration`, `killed_economic`, `killed_fragile`, `superseded`), a `reason` from that
  same closed vocabulary, and the family's running `variants_tried`.
- TC-2: given the same family already has grid_version 1 (N=40 candidates) ledgered, when
  grid_version 2 (25 more candidates) is registered and screened, then
  `GET /research/desk/micro/scout` serves `variants_tried: 65` for that family (the union across
  grid versions, TR-11).
- TC-3: given a ledger row *k* is edited in place on disk after being written, when the
  chain-verification check runs, then it reports a chain-verification failure at row *k*, and no
  code path silently accepts the tampered chain.
- TC-4: given a `superseded` row exists in the ledger, when the ledger is read, then the
  superseded row is still present (never deleted) and its successor pointer resolves to a later
  row in the same file.
- TC-5: given the TR-8 autocorrelated known-null fixture run across 200 seeds under the frozen
  `SCOUT_BLOCK_PERMUTATIONS = 2_000` / `SCOUT_SCREEN_ALPHA = 0.05`, when the within-session
  circular block-permutation screen runs for each seed, then the observed pass rate across the 200
  seeds is ≤ 1.5 × 0.05 = 0.075.
- TC-6: given the identical null fixture and seeds from TC-5, when the banned plain row-shuffle
  null is substituted for the block-permutation null (test-only code path), then its pass rate
  exceeds the 0.075 ceiling, demonstrating the anti-conservative failure the block design exists
  to fix.
- TC-7: given a candidate whose `econ_floor` inputs (`family_median_spread_bps`) were computed from
  data read AFTER that candidate's own `registered_at` timestamp, when it is submitted to the
  ledger, then registration is refused with a typed error and no ledger row is written for it
  (TR-9).
- TC-8: given a family with N candidates already screened at an origin, when 100 additional null
  (no true effect) candidates are registered and screened at that same origin, then every one of
  the original N candidates' fitted threshold and pass/fail decision, re-read from the ledger, is
  byte-identical to its value before the 100 additions (TR-10).
- TC-9: given a family already carrying `SCOUT_MAX_VARIANTS_PER_FAMILY` (24) variants across its
  grid versions, when a 25th variant is submitted for that same family, then registration is
  refused.
- TC-10: given a screening run already in `"running"` state, when `ScoutComputeManager.trigger()`
  is called a second time before the first resolves, then it returns
  `{"state": "refused", "reason": "already_running"}` and no second worker thread starts.
- TC-11: given the same bounded fixture grid, when it is run once via
  `POST /research/desk/micro/scout/compute` and once via the embedded CLI entry point, then the
  two runs' ledger rows carry identical `spec_hash`/`params_hash`/`decision`/`reason` values for
  every candidate — proving there is no second implementation of the screen.
- TC-12: given a screened candidate, when its served screen payload is read via
  `GET /research/desk/micro/scout`, then it carries `evidence_class` verbatim
  (`historical_exposed_diagnostic` on today's exposed fixture/legacy corpus), the best-of-N
  expected-max-under-null disclosure line, session/symbol concentration, ToD-bucket slices,
  fallback-tercile stratification for any aggressor-derived feature, and `econ_interesting` served
  beside — never merged into — the statistical screen, with the frozen proxy sentence ("quoted
  spread is a research cost proxy, not a full execution or tradability model") present verbatim.
- TC-13: given the bounded grid registered this iteration, when its candidate specs are
  enumerated, then none names `quote_depletion` as its conditioning `feature.name` (the scope
  decision in NOTES and the iter-4 assumption-ledger entry, deferred pending the owner ruling on
  `micro_observer.py`'s one-quote-early `available_at` stamp).
- TC-14: given a fixture playbook store whose `.list()` call returns a non-empty `_errors` value
  (a simulated corrupt record), when `micro_join.joinable_corpus_counts` runs against it, then the
  corruption is surfaced in the function's return value or the call raises — never silently
  dropped from `total`/`playbook_signal_count`/`by_setup_id`.
- TC-15: given no band-touch enumeration exists yet (J-09's future scope), when
  `GET /research/desk/micro/readiness` is called, then `band_touch_count`'s served state is a
  typed value a reader can distinguish from "we counted and found zero" — never a bare `0`.
- TC-16: given the real `.data/datasets` and playbook stores (a direct call against the real
  stores, not the browser rig), when `micro_join.joinable_corpus_counts` is called before and
  after this iteration's two passenger fixes, then `playbook_signal_count` stays `2` and
  `by_setup_id` stays `{"range_trade": 2}` — the fixes change only corruption-surfacing and the
  `band_touch_count`/`total` representation, never the enumerated arithmetic.
- TC-17: given the iteration-0 fingerprint and referee-hash baseline, when re-checked this
  iteration, then `Config().config_fingerprint()` still prints `08e471b10130e1e2`, all 6
  `referee_*.py` SHA-256 hashes match the iteration-0 listing, and `app/engine/`,
  `desk_playbook.py`, and `desk_playbook_context.py` show an empty diff.
- TC-18: given the 18 real-corpus snapshot files at their iteration-3 recorded row total
  (3,815,933), when this iteration's snapshot-identity tests re-verify them (no rebuild expected —
  `micro_features.py`/`micro_observer.py` bytes are unchanged by this iteration's diff), then the
  row total read straight off disk is still 3,815,933.
- TC-19: given the full backend suite after this iteration's changes, when `pytest tests/` runs
  (no extra `-q`), then the reported pass count is ≥ 2,866 with 8 skip and 0 new failures.
- TC-20: given the store-scoped browser rig, when browser-qa-agent re-runs J-01/J-02/J-03's checks
  and J-10's full sentinel script, then every previously-green step stays green (screenshots on
  record) and J-04 records an honest SKIP rather than an unscored gap.

## NOTES

- Evaluator's iteration-3 next-step recommendation (binding this iteration): build J-04 next under
  the full pipeline, because the auditor is the only step in this session that has caught a
  real honesty fault (iteration 2, twice), and J-04 is the journey that must never lose the
  record of a failed trial.
- Active blocker (human-owned, unresolved this iteration): the owner ruling on
  `micro_observer.py:636/657`'s one-quote-early depletion `available_at` stamp is due — this
  iteration does NOT invent a reading (T-1). Instead it scopes the Scout's registered grid to
  exclude every `quote_depletion`-conditioned candidate (logged to the assumption ledger). A later
  iteration may register such candidates once the ruling lands, as an ordinary new `grid_version`
  — no rework of this iteration's ledgered rows.
- Evidence-makeup passenger note (J-01's Microscope Readiness photograph, still citing iteration
  2's small-fixture-corpus capture): no dedicated task planned this iteration (the
  never-plan-evidence-only rule) — a fresh capture is expected to ride passively on this
  iteration's required J-01 browser regression check; if it does not, the evaluator carries the
  flag forward again, unchanged.
- Lesson applied (iteration 2, streamed-artifact completeness — "Applies to: ... J-04's screens"):
  `ScoutComputeManager` gets the SAME terminal-state-only ledger-write discipline
  `MicroSnapshotComputeManager` already has (a mid-run exception resolves the job to `"failed"`,
  never a silently-short ledger write) — see IN SCOPE.
- Lesson applied (iteration 2, J-10 test-rig pinning — "Applies to: every future iteration"): not
  reopened. Iteration 3's repair of `journey-scripts/J-10.json` is a Do-Not-Redo item; this
  iteration reuses it unmodified rather than re-deriving or re-pointing it.
- Lesson applied (iteration 3, the depth arbiter's ladder): this iteration's `Depth: full` rests on
  the unconditional ESCALATE rung (Full trigger 3), not merely on the evaluator's depth
  recommendation.
- Lesson applied (iteration 3, `feature_source_hash` rebuild risk): this iteration's diff stays
  inside `scout.py`/`scout_ledger.py`/`micro_join.py`/`micro_readiness.py` and never touches
  `micro_features.py`/`micro_observer.py`, so no whole-corpus snapshot rebuild is expected; TC-18
  verifies the row total anyway as the cheap proxy check the lesson recommends.
- Lesson applied (iteration 0, suite count): `pytest tests/ -q` swallows the summary line under
  this project's `addopts = "-q"`; run `pytest tests/` (no extra `-q`) or add `-v` to read the
  exact pass/skip count directly rather than reconstructing it.
- One interpretive call was logged to the assumption ledger this iteration (excluding
  `quote_depletion`-conditioned candidates from the registered grid pending the owner ruling) —
  flagged reversible.
- `blueprint.md` was re-read and confirmed already accurate for this iteration's scope (the Scout
  Ledger row was pre-registered at baseline); no edit made.
