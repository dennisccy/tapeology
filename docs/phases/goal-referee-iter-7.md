# Goal Iteration 7 — Estimand engines and adjudication (J-06)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** referee
- **Iteration:** 7
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — `referee_adjudicate.py` integrates `referee_stats.py` (J-03),
  `referee_null.py` (J-04), and `referee_registry.py` (J-05) into one new compute-manager +
  append-only snapshot store; the cross-module INTEGRATION correctness is not covered by any
  single existing journey's own test suite.
- **Frontend Present:** no
- **Target journeys:** J-06
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-10
- **Anti-goal reminders:**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative trading cues. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a recorded named seed via per-row streams; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **No confirmatory claim outside the gauntlet.** A confirmatory verdict exists only for a registered hypothesis with an immutable pre-data boundary, a calibrated randomization p, a family BH pass at the registered q, session-clustered robustness, and floors met — and exactly ONE confirmatory checkpoint per hypothesis, recorded as an append-only snapshot that later evaluations can never change (a replication is a new registered hypothesis). *(critical)*
  - **The historical atlas is exploratory forever.** No historical observation is ever served, labeled, or counted as forward confirmation; discovery data renders only under its exploratory label. *(critical)*
  - **CI-inversion is never a p-value.** Ordinary bootstrap quantities are uncertainty intervals; every p that feeds BH comes from a spec-named null-calibrated randomization procedure; the oracle suite guards the distinction. *(critical)*
  - **Never shrink the BH denominator.** No BH pass may run with m smaller than the family's registered planned count; no candidate joins a family retroactively; no unevaluated or late-withdrawn candidate is dropped from m — they fold as p=1, never disappear; no family's q changes after registration. *(critical)*
  - **No gate loosens mid-era.** q, floors, targets, K, B, and every eligibility rule are fixed at registration; `insufficient_sample` is an answer, never a reason to widen anything. *(critical)*
  - **The Referee never feeds back.** No referee output gates, filters, ranks, or tunes any detector, context, screen, or strategy computation (import-ban + source-scan guard-tested); the frozen research vocabulary stays frozen. *(critical)*
  - **Promotion is certificate-locked.** No champion promotion without a valid candidate-specific Referee certificate; no bypass flag, env override, or default-allow path exists (source-scan guard-tested); a Playbook certificate can never satisfy a strategy promotion. *(critical)*
  - **No confirmatory output without a verified oracle attestation.** The adjudication fold never serves a confirmatory verdict from an evaluation whose attestation is missing, mismatched, or version-stale — it serves the refusal state with its reason; descriptive output never masquerades as confirmatory. *(critical)*

## GOAL

Build `referee_adjudicate.py`: the estimand evaluators (A/B/C), evaluation as a recorded
operator act, the single append-only confirmatory checkpoint with its family BH fold, and the
read-side verdict fold — so a registered hypothesis can be evaluated against its fixture
evidence and come back with one honest, permanent, pure-function-of-recorded-facts verdict.

## BACKGROUND

Iteration 6 shipped the registry (J-05) and its own dispatched hard-audit caught a critical
backdateable-boundary hole review and QA had both missed — the evaluator's own next-step
explicitly asked for J-06 at **full** depth, citing exactly that pattern ("the deeper checking
lane has now caught a serious fault twice in this session that the lighter checks missed"). That
recommendation is BINDING by default per this project's rubric, and on the merits it is also
independently correct: J-06 satisfies full-depth trigger 1 (structural/cross-cutting) —
`referee_adjudicate.py` integrates `referee_stats.py` (J-03), `referee_null.py` (J-04), and
`referee_registry.py` (J-05) into one new compute-manager + append-only snapshot store, and none
of those three journeys' own test suites cover that INTEGRATION — only a journey built across
all three can. None of the four named escape conditions (prior ESCALATE/REGRESSION, prior
coherence FAIL, cadence due, brand-new full-stack journey) applies here to justify deviating
DOWN from the recommendation, so this spec plans **full**, cites trigger 1, and leaves depth
enforcement to the engine's own independent arbiter rather than second-guessing it.

Transparency note for the evaluator: iteration 6 itself tripped this session's wall-clock
ceiling (`runs/goal-session-referee/iter-6/budget-breached`) while still landing a `CONTINUE`
verdict. Reading `scripts/automation/run-goal.sh`'s depth arbiter directly shows that combination
(a budget breach on an ordinary `CONTINUE`) triggers a mandatory one-iteration lean-recovery
demotion independent of any `Full trigger:` line — expect a `depth_demoted`
(`reason: budget-breach`) telemetry event and an actual `developer → reviewer → browser-qa` lean
dispatch even though this spec plans full. That is the engine's own safety net, not a defect in
this plan: the four escape conditions I check are my rubric, not the engine's complete rule set,
and I should not pre-empt its enforcement by writing a depth this spec's own merits do not
support. Because I know the effective dispatch is very likely lean, every DEFINITION OF DONE item
and TESTING REQUIREMENTS scenario below is written to be independently satisfiable by a lean
cycle (nothing here depends on a dedicated audit-report artifact existing) and compensates with
an unusually thorough TC- set built directly from four accumulated lessons on this exact
codebase: float-accumulation asymmetry between two computation routes for the same quantity
(iter-3), boundary/floor property tests needing a generator that actually reaches the boundary
(iter-4), seeded-draw tests needing a candidate pool strictly larger than the draw (iter-5), and
validating a derived value's SIBLING inputs, not just its own name-alike field (iter-6). J-06 is
the era's biggest single append-only surface yet (permanent verdict snapshots, never
correctable), so these lessons matter more here than anywhere prior. The evaluator should keep
applying its own independent re-verification discipline regardless of dispatched depth (already
shown throughout this session) and may ESCALATE if it judges a lean-shaped pass inadequate for
machinery this permanent — exactly the same call it made at iteration 5, which would sanction an
unconditional full pass for iteration 8.

Target selection: J-06 is the only defensible pick. It is failing, it unblocks J-07 (the
starter-family registration flow gains real meaning once evaluation exists), J-08
(`authorize_promotion` is J-06's own deliverable), and J-09 (the Adjudications section has
nothing to render without it); every other failing journey (J-07, J-08, J-09) is explicitly
sequenced after it in goal.md's own dependency order. No regressed journey exists (rule 1 n/a);
the last coherence verdict was PASS, not FAIL (rule 2 n/a); rule 6 (never bundle two risky
journeys) is satisfied trivially — J-06 is the only journey in scope.

Two spec ambiguities required an interpretation call and are logged to
`runs/goal-session-referee/state/assumptions.md`: (1) the `killed` verdict names no registered
kill-condition mechanism anywhere in the spec or the Hypothesis record schema, so no code path
this iteration computes or emits it (T-1: vagueness is a drop, never an improvisation); (2) the
spec's "refuses confirmatory output... with honest copy" on attestation failure names no
distinct verdict token among the 9 listed, so this iteration represents it as a dedicated
`confirmatory_output_refused`/`refusal_reason` pair that forces the served `verdict` to the most
conservative non-claim state (`insufficient_sample`) rather than inventing a tenth token.

## IN SCOPE

### Backend

- [ ] New module `app/research/referee_adjudicate.py`: Estimand A/B/C pooling per spec §3.1–§3.3
      over the evidence contract (J-02) + matched nulls (J-04); the primary within-session
      group-label permutation test (§3.4, `referee_stats.permutation_test`) with its
      pre-registered weights; both CI levels (`bootstrap_ci_occurrence`/`bootstrap_ci_cluster`)
      and the three robustness disclosures (§3.5: `sign_flip_result`, `equal_weight_t`, the
      entry-basis re-measure sensitivity per §4.3) — `insufficient_sample` below
      `REFEREE_MIN_CLUSTERS_FOR_CI` (`referee_stats.py:98`) or under either registered floor
      (`target_sessions`/`min_occurrences` on the Hypothesis record).
- [ ] Estimand B's informative-session rule is distinct from A/C (§3.2): only sessions carrying
      BOTH the context cell AND its complement pool into `T`; one-group sessions are counted out
      loud in a served `one_group_sessions_excluded` field, never silently dropped.
- [ ] Estimand C reads `referee_null.py`'s own already-served `backing_bucket_eligibility_rate`
      disclosure (closed at iter-6: `None` when nothing is measurable) rather than
      re-implementing context-anchor evaluability — single source of truth for that check.
- [ ] Evaluation store + its run-ledger store, mirroring `RefereeNullStore`/`RefereeNullRunStore`'s
      file-record + env-var-or-sibling-dir shape exactly (`TAPEOLOGY_DESK_REFEREE_EVAL_DIR` /
      `TAPEOLOGY_DESK_REFEREE_EVAL_LOG_DIR`, per goal.md's own named `_EVAL_DIR`/`_LOG_DIR`
      families — deliberately NOT `Config` fields). One evaluation record per evaluation act,
      embedding `evaluation_basis` (content hash of the dedup record-id set + coverage counts,
      null record ids, null/test-spec ids, seeds, B, `STATS_CORE_VERSION`) and the live
      `referee_stats.run_oracle_attestation()` output.
- [ ] Evaluation compute manager, mirroring `RefereeNullComputeManager`
      (`referee_null.py:939`) exactly: single-flight PER `hypothesis_id`, snapshot-pollable
      progress, cooperative cancel checked before each unit of work, terminal-state-only
      run-ledger writes, one `run_evaluation_and_record` walker + one shared
      `record_evaluation_run` writer (the `record_null_run` precedent) + a CLI subcommand
      mirroring `referee_null.py`'s `main()`.
- [ ] Accrual gating (§5): confirmatory eligibility = post-boundary informative sessions
      (recomputed HERE, for real, per spec §3.1's "eligible occurrence with eligible anchor"
      definition — never inherited from the registry's own `is_proxy: true` estimate) ≥
      `target_sessions` on completed-session records only. Below target: record `role: "pending"`
      with NO confirmatory `permutation_p`. The FIRST qualifying evaluation per hypothesis is its
      checkpoint (`role: "checkpoint"`); every later evaluation is `role: "monitoring"`.
- [ ] Adjudication snapshot store (append-only; written ONLY at the checkpoint evaluation):
      the family BH fold at the registered q (`referee_stats.benjamini_hochberg`, `m` = the
      family's frozen planned count) over the family's checkpoint p-values, plus the BY
      disclosure, fragility triggers, and the frozen `evaluation_basis`/attestation copied
      verbatim from the checkpoint evaluation.
- [ ] Read-side adjudication fold (`adjudications_response()`): for every hypothesis in the
      registry, serves its recorded snapshot verbatim if one exists, else a LIVE pure-function
      fold over recorded facts only — `exploratory`/`registered`/`pending_forward_confirmation`/
      `basis_retired` (via the existing `_is_stale_basis`-style comparison against
      `current_playbook_detector_basis()`, imported not re-derived). Attestation is
      RE-VERIFIED at fold time (not trusted from evaluation time); a missing/mismatched/
      version-stale attestation sets `confirmatory_output_refused: true` with a `refusal_reason`
      and forces `insufficient_sample` rather than any confirmatory token. `REFEREE_REGISTER`
      (the served disclosure text) is defined here and included on every response.
- [ ] `authorize_promotion(candidate, certificate_store, live_scan_context)`: a pure function
      reading the (still-empty) `CertificateStore` and returning
      `{authorized, refusal_class, reason}`. Implements all 6 named refusal classes (§8:
      `no_certificate`, `stale`, `wrong_candidate`, `mismatched_datasets`, `failed_gates`,
      `malformed_unverifiable`) — NOT wired into `pnl_scan._promote` this iteration (J-08's job,
      per goal.md's explicit sequencing and the "NOT done despite existing" note on the
      certificate store's mint path).
- [ ] New module constant `REFEREE_GATE_VERSION` (parameters-discipline: embedded in
      certificate gate results / hashed like every other referee constant, never a `Config`
      field).
- [ ] Mount `GET /research/desk/referee/evaluations` (`?hypothesis_id=`),
      `POST/GET/POST-cancel /research/desk/referee/evaluate`, `GET
      /research/desk/referee/evaluate/runs`, `GET /research/desk/referee/adjudications` on the
      existing `referee_routes.py` router (already included in `main.py` since J-01 — no new
      router registration). Mirror the null-compute route shapes at `referee_routes.py:112-213`
      exactly (`{"records": [...], "integrity_errors": [...]}` on GET-list;
      `{"record": ...|None}` on GET-by-id; `started: bool` semantics on trigger; `409` on
      cancel-when-idle).
- [ ] New import-topology guard test extending `test_referee_guards.py`'s existing pattern:
      `referee_adjudicate.py` imports neither `desk_playbook_detect` nor
      `desk_playbook_context` directly.
- [ ] Rider 1 (bug fix, already-owned module): `referee_evidence.py:798`'s
      `epoch_anchor = dataset.get("epoch_anchor") or 0.0` silently anchors a trade at the Unix
      epoch when the dataset carries no `epoch_anchor`, corrupting its derived `session_date`
      and pooling it into a bogus cluster (the "1969 date" bug; J-06 is its first real reader).
      Fix: a missing/falsy `epoch_anchor` excludes that dataset's trades as an honest, counted
      exclusion (T-5 discipline: "unmeasurable = counted exclusion, never zero"), never a
      silent epoch-0 anchor.
- [ ] Rider 2 (bug fix, already-owned module, audit gap B4): `referee_registry.py`'s
      `registry_response()` (`:819`) currently discards all four stores' `integrity_errors`
      instead of disclosing them. Fix: surface them the same way `get_referee_nulls`/
      `get_referee_nulls_runs` already do (`referee_routes.py:112-213`) — reuse the pattern, do
      not invent a second disclosure shape.
- [ ] Rider 3 (cleanup, audit gaps B5/T1): remove the three reviewer-flagged dead imports in
      `referee_registry.py`; re-pin `test_referee_registry.py`'s seeded random-draw test to a
      hand-computed literal expected value instead of deriving the expectation from the code
      under test.
- [ ] Zero `Config` field additions; zero new runtime dependencies (stdlib + `random.Random`
      streams only, matching every prior referee module).

### Frontend

None. J-06 is backend/CLI-only — `referee_adjudicate.py` has no page of its own; its eventual
render target (the Referee Adjudications section) is J-09's job. `Frontend Present: no` is
accurate here (unlike a `Frontend Present: no` iteration whose real scope quietly touches the UI
— it does not).

### New user-facing capability

None this iteration. The operator can run an evaluation via CLI (`python -m
app.research.referee_adjudicate evaluate --hypothesis-id ...`) or `curl` the new endpoints
directly; no page renders anything new yet.

### New information displayed

None (no UI consumer exists yet — J-09 is the first).

### New user actions

None (no UI this iteration).

### UI surface changes

None.

### Product surface delta

None visible in the browser. The real product-facing delta is the new keyless capability
itself: a registered hypothesis can now be evaluated end-to-end and come back with a permanent,
recorded verdict — visible today only via direct API/CLI/test evidence, exactly as J-04 and J-05
shipped before their own UI (J-09) existed.

### Blueprint conformance

No new UI surface. `runs/goal-session-referee/state/blueprint.md`'s Information Architecture
already registers J-06's canonical home at baseline: `/desk` → **Referee Adjudications** (J-09
remains its first UI consumer) — unchanged this iteration.

### Data-contract additions

All four rows below already exist as owner+endpoint STUBS in `blueprint.md`'s Data Contract
since baseline (`referee_adjudicate.py` / the four `/research/desk/referee/evaluat*` +
`/adjudications` endpoints) — this iteration gives them their FIRST field-level shape (the
iter-4/5/6 precedent), owner and endpoint unchanged:

- **Evaluation record** (append-only): `evaluation_id: str`, `hypothesis_id: str`,
  `family_id: str`, `evaluated_at: str` (ISO-8601 UTC), `evidence_family:
  "playbook"|"strategy"`, `estimand: "A"|"B"|"C"`, `evaluation_basis: str` (sha256[:16]),
  `coverage: {post_boundary_informative_sessions: int, target_sessions: int, min_occurrences:
  int, occurrences_pooled: int, one_group_sessions_excluded: int}`, `confirmatory_eligible:
  bool`, `role: "pending"|"checkpoint"|"monitoring"`, `T: float|None`, `permutation_p:
  float|None`, `permutation_enumeration: bool|None`, `min_attainable_p: float|None`,
  `ci_occurrence: [float, float]|"insufficient_sample"|None`, `ci_cluster: [float,
  float]|"insufficient_sample"|None`, `sign_flip_p: float|None`, `equal_weight_T: float|None`,
  `entry_basis_T: float|None`, `entry_basis_sign_flip: bool|None`, `attestation: {passed: bool,
  expected: dict, actual: dict, tolerance: dict, stats_core_version: str}`, `provenance:
  {config_fingerprint: str, computed_at: str}`.
- **Adjudication snapshot record** (append-only, exactly one per hypothesis, written only at
  its checkpoint evaluation): `snapshot_id: str`, `hypothesis_id: str`, `family_id: str`,
  `checkpoint_evaluation_id: str`, `snapshot_at: str` (ISO-8601 UTC), `bh: {q: float, m: int,
  k_star: int, bh_pass: bool, by_adjusted_p: float, by_pass: bool}`, `fragility_triggers:
  list[str]` (any of `"by_fail"`, `"sign_flip"`, `"entry_basis_sign_flip"`,
  `"cluster_ci_includes_zero"`), `verdict:
  "no_evidence"|"insufficient_sample"|"fragile"|"corroborated"`, `evaluation_basis: str`
  (frozen copy), `attestation: dict` (frozen copy).
- **Evaluation run-ledger record**: `run_id: str`, `hypothesis_id: str`, `state:
  "running"|"completed"|"failed"|"cancelled"`, `started_at: str`, `finished_at: str|None`,
  `progress: {done: int, total: int}`, `error: str|None` — mirrors the null run-ledger shape
  exactly.
- **`GET /research/desk/referee/adjudications` response**: `{entries: [{hypothesis_id: str,
  verdict: "exploratory"|"registered"|"pending_forward_confirmation"|"insufficient_sample"|
  "fragile"|"no_evidence"|"corroborated"|"basis_retired", confirmatory_output_refused: bool,
  refusal_reason: str|None, snapshot: SnapshotRecord|None, live_coverage: {...}|None}...],
  register: REFEREE_REGISTER}`. `killed` is a documented but never-emitted enum member this
  iteration (see NOTES) — no code path returns it.
- **`authorize_promotion` return shape** (not yet a served HTTP value — J-08 surfaces it inside
  `pnl_scan`'s report): `{authorized: bool, refusal_class:
  "no_certificate"|"stale"|"wrong_candidate"|"mismatched_datasets"|"failed_gates"|
  "malformed_unverifiable"|None, reason: str|None}`.

Reused verbatim, never re-derived: `referee_stats.permutation_test`/`benjamini_hochberg`/
`bootstrap_ci_occurrence`/`bootstrap_ci_cluster`/`sign_flip_result`/`equal_weight_t`/
`run_oracle_attestation`/`verify_oracle_attestation` (J-03); `referee_null.py`'s null records
and `backing_bucket_eligibility_rate` disclosure (J-04); `referee_registry.py`'s Family/
Hypothesis/Withdrawal/CertificateStore records, `_epoch_from_iso`/`_et_session_date`/
`_is_stale_basis`/`current_playbook_detector_basis` (J-05/J-02).

## OUT OF SCOPE

- J-07's `/desk` registration UI/browser flow and the real starter-family registration act
  (explicit operator act, gated on the J-07 UI existing — not this iteration's job to trigger).
- J-08's certificate MINT path and its `pnl_scan._promote` wiring — `authorize_promotion` is
  built as a pure, unwired function only; fixture-by-fixture testing of all 6 refusal classes
  is J-08's own Acceptance clause ("each refusal class is separately fixture-tested").
- J-09's three `/desk` sections, new `data-testid`s, the 21st/22nd MCP tools, referee-copy
  additions to the copy lint.
- Any strategy-family END-TO-END adjudication run or test (Non-Goal: "No strategy-family
  statistics buildout beyond the adapter") — the epoch_anchor fix is a defensive fix inside the
  shared J-02 adapter, not a strategy-family adjudication build-out.
- The `killed` verdict (no registered kill-condition mechanism exists anywhere in the spec or
  schema — dropped per T-1; logged to `state/assumptions.md`).
- `WithdrawalStore.record()`'s corrupted-file misreport (audit gap B3) — explicitly deferred,
  not required by iteration 6's next-step recommendation; carried forward, not silently dropped.
- Any `Config` field addition, any new runtime dependency (scipy stays out), any threshold or
  eligibility-rule tuning.
- Widening Required-still-passing to a full regression sweep of all 5 passing journeys plus
  J-10 in full — not due this iteration (no ESCALATE/coherence-FAIL/cadence trigger); the
  6-journey set above is scoped to what this iteration's diff can actually affect plus the
  mandatory kept-product walk.

## DEFINITION OF DONE

- [ ] J-06 fixture round-trip, end-to-end through the real code path: a synthetic known-positive
      family (registration → null build → evaluation → checkpoint) adjudicates `corroborated`;
      a synthetic known-null family adjudicates `no_evidence`.
- [ ] Pre-boundary / deep-backfilled counter-test: no record with `session_date` on-or-before a
      hypothesis's `confirmation_start_boundary` ever contributes to `coverage` or `T`, including
      one deep-backfilled record recorded (`recorded_at`) AFTER registration.
- [ ] Checkpoint immutability: a later `"monitoring"` evaluation changes nothing served by
      `GET .../adjudications` for that hypothesis; the fold is byte-identical across two
      successive calls against an unchanged store.
- [ ] Tampered-attestation refusal: a stored evaluation record whose attestation is mismatched
      folds to `confirmatory_output_refused: true` with a non-empty `refusal_reason`, never a
      confirmatory verdict token.
- [ ] `authorize_promotion` is directly fixture-tested for `no_certificate`, `stale`, and the
      success path; the remaining 4 refusal classes are implemented with matching honest reasons
      (full fixture coverage rides with J-08).
- [ ] The three riders land: epoch_anchor exclusion, registry `integrity_errors` disclosure,
      dead-import + test-pin cleanups.
- [ ] Required-still-passing journeys (J-01, J-02, J-03, J-04, J-05, J-10) remain green —
      deterministic replay + LLM fallback; J-10's kept-product browser walk produces a FRESH
      dated screenshot this iteration (it did not run at all in iteration 6 — a second skipped
      round would turn a safe carry-over into a real evidence hole).
- [ ] No anti-goal violation introduced; zero new `Config` fields; MCP tool count stays exactly
      `20` (`test_mcp_server.py::EXPECTED_TOOLS`, `:56`); `Config().config_fingerprint()` prints
      `08e471b10130e1e2`.
- [ ] Unit tests pass; full suite count grows past iteration 6's own-verified baseline (2,595
      collected / 2,587 passed / 8 skipped) with nothing newly failing.
- [ ] Dev handoff written at `docs/handoffs/goal-referee-iter-7-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-10's kept-product walk only (cockpit sim tape + chart, `/structure` pinned-AAPL
  Load, every shipped `/desk` section including all Playbook sections) — deterministic replay
  first, LLM fallback on drift/no-golden, screenshot-evidenced. J-06 itself carries no browser
  acceptance (*(Keyless; automated.)* per goal.md).
- Unit/integration: estimand A/B/C pooling against hand-computed fixture corpora (not just
  "runs without error" — assert the actual `T`/`p`/CI numbers against independently
  hand-computed expectations, the iter-6 lesson about validating derived values for real); the
  evaluation compute manager's single-flight/cancel/resume semantics (mirroring
  `referee_null.py`'s own resumable-reuse and cancel-leaves-no-partial-record precedent, cited
  there as TC-8 and TC-20 — this spec's own TC- numbers below are a separate, self-contained
  list); the BH fold at a real rank boundary
  (not just an obviously-positive and an obviously-negative case — the iter-4 lesson: a
  boundary/floor test only proves anything if the fixture is constructed to actually land ON the
  boundary); the full read-side verdict vocabulary; the two rider bug fixes; the new
  import-topology guard.
- Error cases: malformed/unknown `hypothesis_id` on `POST .../evaluate` (422, no job started);
  an evaluate-trigger payload that ALSO supplies a field aimed at the informative-session count
  or an evaluation timestamp is ignored — the server always recomputes coverage itself (the
  iter-6 lesson: validate every input a derived value could be reached through, not just its own
  name-alike field); a corrupted evaluation/snapshot file is surfaced in `integrity_errors`,
  never a 500 and never a silent drop from the list.

Test-first contract — TC- scenarios:

**Estimand computation (A/B/C)**

- TC-1: given a fixture Estimand-A hypothesis (sidedness "greater") with 14 informative sessions
  where every occurrence value exceeds its session's matched-null anchor mean by a fixed positive
  margin, when the evaluator runs a full evaluation through the real estimand-A pooling code,
  then the returned `permutation_p` is below `0.05` and `T`'s sign matches "greater".
- TC-2: given a fixture Estimand-B hypothesis with 10 sessions containing BOTH the context cell
  and its complement and 4 sessions containing only one group, when the evaluator pools
  informative sessions, then only the 10 dual-group sessions enter `T` and the response's
  `coverage.one_group_sessions_excluded` equals `4`.
- TC-3: given a fixture Estimand-C hypothesis whose registered backing bucket has zero eligible
  context-matched-null anchors for every occurrence (`referee_null.py`'s own
  `backing_bucket_eligibility_rate: None` disclosure), when an evaluation runs, then
  `coverage.post_boundary_informative_sessions` counts zero sessions from that cell and `role`
  is `"pending"` with no `permutation_p` served — never a fabricated p from zero anchors.
- TC-4: given a fixture hypothesis below `REFEREE_MIN_CLUSTERS_FOR_CI` informative sessions,
  when the clustered CI is computed, then `ci_cluster` equals the literal string
  `"insufficient_sample"`, never a numeric interval.
- TC-5: given a fixture Estimand-A hypothesis whose entry-basis close-anchored re-measurement
  flips `T`'s sign relative to the primary measurement, when the fold computes the verdict at an
  otherwise-BH-passing checkpoint, then `fragility_triggers` includes
  `"entry_basis_sign_flip"` and `verdict` is `"fragile"`.
- TC-6: given a fixture Estimand-A hypothesis whose clustered CI includes `0` at an
  otherwise-BH-passing checkpoint, when the fold computes the verdict, then `fragility_triggers`
  includes `"cluster_ci_includes_zero"` and `verdict` is `"fragile"`.

**Evaluation as an operator act, and the pre-boundary counter-test**

- TC-7: given a hypothesis with `0` post-boundary informative sessions, when `POST
  /research/desk/referee/evaluate` runs with `{"hypothesis_id": "<id>"}`, then the recorded
  evaluation record's `role` is `"pending"`, `confirmatory_eligible` is `false`, and no
  `permutation_p` field is served.
- TC-8: given a playbook record whose `session_date` is on or before a hypothesis's
  `confirmation_start_boundary`, including one instance whose OWN `recorded_at` is AFTER
  registration (a deep-backfilled record), when an evaluation runs, then neither record
  contributes to `coverage.post_boundary_informative_sessions` nor to the pooled `T`.
- TC-9: given a hypothesis with post-boundary informative sessions strictly below its registered
  `target_sessions`, when an evaluation runs, then `coverage.post_boundary_informative_sessions`
  reports the real recomputed count (never the registry's own `is_proxy: true` estimate) and
  `role` is `"pending"`.
- TC-10: given a hypothesis with post-boundary informative sessions ≥ `target_sessions` on
  completed-session records only, when the FIRST such evaluation runs, then `role` is
  `"checkpoint"`, exactly one adjudication snapshot record is appended, and
  `confirmatory_eligible` is `true`.
- TC-11: given an already-checkpointed hypothesis with more sessions accrued since, when a
  further evaluation runs, then the new record's `role` is `"monitoring"` and the snapshot
  store's record count for that `hypothesis_id` stays at exactly `1`.
- TC-12: given two evaluation acts run back-to-back against an unchanged store, when both
  complete, then their `evaluation_basis` values are byte-identical and their live
  `run_oracle_attestation()` outputs are byte-identical.
- TC-13: given a `POST .../evaluate` body that additionally carries
  `{"hypothesis_id": "...", "post_boundary_informative_sessions": 999}`, when the evaluation
  runs, then the extra field is ignored — the recorded `coverage.post_boundary_informative_sessions`
  reflects only the server's own recount, never the caller-supplied value.

**Checkpoint, snapshot, family BH fold**

- TC-14: given a family of 21 fixture hypotheses (20 known-null + 1 known-positive) all reaching
  checkpoint under `q=0.10`, when the family BH fold runs, then its computed `k_star` equals the
  hand-computed rank from `p_(k) ≤ (k/m)·q` with `m=21`, and the known-positive hypothesis's rank
  is inside the corroborated set while all 20 known-null ranks are not — including the boundary
  case where the known-positive's own p sits exactly at the `(k*/m)·q` threshold.
- TC-15: given a family whose planned candidate list includes one hypothesis still `"registered"`
  (never evaluated) when its 3 siblings checkpoint, when the family BH fold runs, then `m` still
  equals the family's full planned count (not `3`) and the unevaluated candidate folds as `p=1`
  in the BH input.
- TC-16: given a hypothesis withdrawn after a post-boundary evaluation already exists (refused
  per J-05), when the family BH fold runs regardless, then that hypothesis's frozen checkpoint
  p-value still counts toward `m`.
- TC-17: given a checkpointed hypothesis whose BH passes but whose Benjamini–Yekutieli-adjusted p
  fails at the same q, when the fold computes the verdict, then `fragility_triggers` includes
  `"by_fail"` and `verdict` is `"fragile"`, never `"corroborated"`.
- TC-18: given a checkpointed hypothesis meeting BH, no fragility trigger, and both registered
  floors, when the fold computes the verdict, then `verdict` is `"corroborated"`.
- TC-19: given a checkpointed hypothesis whose BH fold rejects the null (rank outside `k_star`),
  when the fold computes the verdict, then `verdict` is `"no_evidence"`.

**Read-side fold and verdict vocabulary**

- TC-20: given a hypothesis with zero post-boundary sessions of any kind, when `GET
  /research/desk/referee/adjudications` runs, then that hypothesis's entry serves `verdict`
  `"registered"`.
- TC-21: given a hypothesis whose pinned `detector_basis` no longer equals
  `current_playbook_detector_basis()`, when the fold runs, then `verdict` is `"basis_retired"`
  regardless of any other computed state.
- TC-22: given an evaluation record whose stored `attestation.actual` is test-mutated to no
  longer match `attestation.expected`, when `GET .../adjudications` folds that hypothesis, then
  `confirmatory_output_refused` is `true` with a non-empty `refusal_reason`, and `verdict` is
  never `"corroborated"`, `"no_evidence"`, or `"fragile"`.
- TC-23: given two successive `GET /research/desk/referee/adjudications` calls with no store
  mutation between them, when both responses are compared byte-for-byte, then they are
  identical.
- TC-24: given at least one registered hypothesis, when `GET .../adjudications` runs, then the
  response's `register` field equals the `REFEREE_REGISTER` text verbatim on every call.
- TC-25: given zero hypotheses registered anywhere (today's real store), when `GET
  /research/desk/referee/registry` and `GET /research/desk/referee/adjudications` both run
  against it, then both return HTTP `200` with empty lists — never `404`/`500`.

**`authorize_promotion`**

- TC-26: given no certificate exists for a candidate `(strategy_id, profile)`, when
  `authorize_promotion` runs, then it returns `authorized: false`, `refusal_class:
  "no_certificate"`.
- TC-27: given a fixture certificate whose `config_fingerprint` differs from the live scan's own
  fingerprint, when `authorize_promotion` runs, then it returns `authorized: false`,
  `refusal_class: "stale"`.
- TC-28: given a fixture certificate whose every pin (candidate, champion identity, datasets,
  fingerprint, gate results) matches the live scan context exactly and whose `gate_results.
  bh_pass` is `true`, when `authorize_promotion` runs, then it returns `authorized: true`.

**Riders**

- TC-29: given a strategy dataset record with no `epoch_anchor` field, when
  `strategy_observations()` runs, then that dataset's trades are excluded from the returned
  observations and counted in a served exclusion disclosure — never anchored at the Unix epoch.
- TC-30: given a corrupted family/hypothesis/withdrawal/certificate record file on disk, when
  `GET /research/desk/referee/registry` runs, then the response's `integrity_errors` list names
  the corrupted file — never a silent drop, never a `500`.
- TC-31: given `test_referee_registry.py`'s seeded random-draw test, when it runs against the
  shipped selection code, then its assertion compares against a hand-computed literal value
  written directly in the test file, not a value derived by calling the code under test.

**Compute manager and CLI**

- TC-32: given an evaluation already `"running"` for hypothesis `H`, when a second `POST
  .../evaluate` for the same `H` is issued, then the response reports `started: false` while a
  concurrent trigger for a DIFFERENT hypothesis `H2` starts normally (single-flight per
  hypothesis, not process-global).
- TC-33: given an in-flight evaluation for hypothesis `H`, when `POST .../evaluate/cancel` is
  issued for `H`, then the run-ledger records exactly one terminal `"cancelled"` row and no
  partial evaluation record is written for `H`.
- TC-34: given the CLI's evaluate subcommand run twice in a row against an unchanged store, when
  both runs complete, then the second run reuses (never re-computes) any already-recorded
  evaluation whose exact key already exists.

**Required-still-passing / kept product**

- TC-35: given the deployed `/`, `/structure`, and `/desk` pages unchanged by this iteration,
  when the deterministic replay lane (or its LLM fallback on drift/no-golden) runs against J-01,
  J-02, J-03, J-04, J-05, and J-10's kept-product clauses, then every one reports green and
  J-10's kept-product walk produces a freshly dated screenshot for THIS iteration.
- TC-36: given the full backend suite, when it runs after this iteration's changes, then the
  collected/passed count is at or above `2,595 collected / 2,587 passed / 8 skipped` with zero
  new failures, and `Config().config_fingerprint()` prints `08e471b10130e1e2`.
- TC-37: given `apps/backend/tests/test_mcp_server.py::EXPECTED_TOOLS`, when the suite runs,
  then it still parses to exactly `20` tool names.

## NOTES

- **This spec plans full; the actual dispatch will very likely run lean, and that is expected.**
  See BACKGROUND — iteration 6 tripped the wall-clock budget marker while still landing
  `CONTINUE`, and the engine's own arbiter treats that combination as a mandatory one-iteration
  lean recovery pass, independent of this spec's `Full trigger:` line. This spec still plans full
  because trigger 1 genuinely holds and none of the four named escape conditions license
  deviating from the evaluator's binding recommendation — enforcement is the engine's job, not
  mine to pre-empt. If the evaluator judges a lean-shaped pass inadequate for machinery this
  permanent, ESCALATE is the correct lever (as at iteration 5), which sanctions an unconditional
  full pass for iteration 8.
- **`killed` is dropped, not deferred silently** — logged to `state/assumptions.md` (iter-7,
  goal-decomposer). No Hypothesis-record field or spec clause names a kill-condition trigger; the
  verdict vocabulary function may include the literal string as a documented future enum member,
  but no code path this iteration computes or returns it.
- **Attestation-refusal representation is an interpretation call** — logged to
  `state/assumptions.md` (iter-7, goal-decomposer): a dedicated `confirmatory_output_refused` +
  `refusal_reason` pair, forcing `verdict` to `insufficient_sample`, rather than a tenth verdict
  token the spec's §5 list does not name.
- Mirror, do not reinvent: every new store/manager/route shape in this iteration has a
  byte-for-byte precedent already shipped in `referee_null.py`/`referee_routes.py` (J-04) —
  deviating from those shapes without a stated reason is itself a coherence risk.
- Host protection: evaluation compute (like null builds) must respect
  `project-extensions/host-guard/host-guard.env`'s CPU/memory ceilings; never widen or bypass
  them to finish faster.
- Still outstanding for a person, carried from iteration 2 and outside this project: the
  unrelated trendora backend on port 8255 has not been restarted. Non-blocking.
