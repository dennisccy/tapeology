# Goal Iteration 6 — The registry: pre-registration with an immutable boundary

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** referee
- **Iteration:** 6
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — the last evaluator verdict was ESCALATE (mandatory, no exceptions); the
  evaluator's own next-step also asked for full depth on this exact journey because it mints
  permanent, never-editable records.
- **Frontend Present:** no
- **Target journeys:** J-05
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-10 (kept-product half only —
  its era-end clauses stay gated on J-09)
- **Anti-goal reminders:**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper
    trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is
    the tier-1 guard; new research code adds matching guard tests, never weakens them.)
    *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R,
    n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language,
    no imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
    them, never a mutation of them. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a recorded named seed via per-row
    streams; identical requests reproduce byte-identical results; no wall-clock, no unseeded
    randomness in any research artifact. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed,
    never re-tagged, never deleted, never content-perturbed. Splits are frozen at
    registration. *(critical)*
  - **No confirmatory claim outside the gauntlet.** A confirmatory verdict exists only for a
    registered hypothesis with an immutable pre-data boundary, a calibrated randomization p, a
    family BH pass at the registered q, session-clustered robustness, and floors met — and
    exactly ONE confirmatory checkpoint per hypothesis, recorded as an append-only snapshot
    that later evaluations can never change (a replication is a new registered hypothesis).
    *(critical)*
  - **The historical atlas is exploratory forever.** No historical observation is ever served,
    labeled, or counted as forward confirmation; discovery data renders only under its
    exploratory label. *(critical)*
  - **Never shrink the BH denominator.** No BH pass may run with m smaller than the family's
    registered planned count; no candidate joins a family retroactively; no unevaluated or
    late-withdrawn candidate is dropped from m — they fold as p=1, never disappear; no family's
    q changes after registration. *(critical)*
  - **No gate loosens mid-era.** q, floors, targets, K, B, and every eligibility rule are fixed
    at registration; `insufficient_sample` is an answer, never a reason to widen anything.
    *(critical)*

## GOAL

An operator (or a fixture standing in for one) can write a hypothesis question down — its
setup, side, estimand, primary measure, and null design — through a real registration act
BEFORE any confirmation data exists, get back an immutable boundary date derived honestly from
the registration instant, and see it and its live readiness on `GET /research/desk/referee/registry`;
nothing about a registered question can ever be edited, and a withdrawal is refused once a
post-boundary evaluation already exists.

## BACKGROUND

Iteration 5 shipped J-04 (matched nulls) but the engine's arbiter demoted its full-depth request
to lean for time (`depth_demoted`, `reason: full-cap`) — the evaluator's own ESCALATE verdict
says permanent, never-editable machinery shipped without the hard-audit pipeline that caught
iteration 3's real statistical bug, and asks for J-05 next at full depth for exactly that
reason: the registry is even more permanent than J-04 (append-only identity records that every
later evaluation, BH computation, and certificate points at forever). Per this project's own
rule, a prior ESCALATE verdict makes full depth mandatory this iteration regardless of any
other signal (trigger 3) — reinforced, not overridden, by the evaluator's own stated reasoning.
Because iterations 3 AND 5 both asked for full and both got demoted on time/budget, this
iteration deliberately targets ONE journey only (not bundled with J-06) and folds in only the
four SMALL riders iteration 5's own eval explicitly asked to carry along, all of them
same-file/test-only except one one-field bug fix — matching this project's "smallest spec wins
ties" discipline and reducing a third demotion's odds without shrinking the scope ESCALATE
actually calls for.

Lessons applied: iter-5's lesson says a "hand-verified draw" test is vacuous unless the
candidate pool strictly exceeds the number drawn — this iteration's rider closes exactly that
gap for `referee_null.py`'s seeded subset draw (still open per the current "Do not redo" list).
iter-3's and iter-4's lessons (dual-computation-path bit-identity; a boundary/floor test must
sample the regime where the boundary is actually reached) apply directly to this iteration's
own new dual-path logic — the ET-midnight boundary conversion has exactly one regime where a
naive implementation drifts a calendar date, so its test fixture is chosen to land IN that
regime (23:30 ET), not merely "some date". iter-1's lesson (no golden replay exists for a
backend-only journey) applies again: J-05 is "(Keyless; automated.)" per its own acceptance —
plan verification as pytest, not a browser pass. iter-2's lesson (pattern-based `pkill` hits
other projects on this shared host) applies to any dev-server restart this iteration performs.

## IN SCOPE

### Backend

- [ ] New `app/research/referee_registry.py`: append-only FAMILY, HYPOTHESIS, and WITHDRAWAL
  stores per `docs/referee-statistical-spec.md` §5 — no update/delete method on any store;
  duplicate identity raises. Registration validation refuses, each with a distinct honest
  error and no record written: malformed (including required-field gaps, `target_sessions` <
  `REFEREE_MIN_SESSIONS`, `min_occurrences` < `REFEREE_MIN_OCCURRENCES`, and an Estimand-C
  context predicate `desk_playbook_context.BandMapResolver` cannot evaluate — spec §3.3's own
  refusal clause), duplicate `hypothesis_id`/`family_id`, retroactive-boundary (an explicitly
  supplied boundary at or before `registered_at`'s own ET calendar date), and unknown-spec-id
  (`null_spec_id`/`test_spec_id` outside the pinned set in spec §1).
- [ ] `confirmation_start_boundary` computation reuses `referee_evidence.py`'s existing
  epoch→ET-calendar-date conversion (the same helper `_et_session_date` already uses) rather
  than a second DST-aware conversion implementation.
- [ ] Withdrawal: refuses once a post-boundary evaluation exists for the hypothesis (accept an
  injectable/caller-supplied evaluation-existence signal for this iteration — no evaluation
  store exists until J-06; a fixture supplies both `True`/`False` states so the refusal rule
  itself is provably correct today, and J-06 wires the real evaluation store to the same
  signal when it lands); an accepted withdrawal appends a WITHDRAWAL record and changes nothing
  else about the (immutable) hypothesis record.
- [ ] New `app/research/referee_registry.py` CERTIFICATE store (append-only; SHAPE per spec §8
  only — no writer/mint path this iteration; see OUT OF SCOPE).
- [ ] Per-hypothesis `accrual` fold on `GET .../registry`: count distinct post-boundary
  `session_date`s carrying ≥1 observation in the hypothesis's own `(setup_id, side)` cell,
  reusing `referee_evidence.playbook_occurrence_readiness()`'s existing per-cell pooling
  (never a second `PlaybookStore` scan or a second detector-basis/session-date loop) — served
  labeled `is_proxy: true` (see `state/assumptions.md` iter-6 entry) and disclosing
  `basis_current: bool` when a hypothesis's pinned `detector_basis` no longer matches the
  corpus's live value (the T-6 disclosure pattern, not a silent mismatch).
- [ ] `POST /research/desk/referee/registry/hypotheses` (explicit confirmation required before
  any write) and `GET /research/desk/referee/registry` (serves `families`, `hypotheses` folded
  with `status` + `accrual`, `withdrawals`, `certificates`) added to `referee_routes.py`.
- [ ] CLI entry point for registration and withdrawal, matching `referee_null.py`'s
  `argparse`/`main()` convention.
- [ ] Storage directory follows the established env-var-or-sibling-default family (alongside
  `TAPEOLOGY_DESK_REFEREE_DIR`'s existing `_NULL_DIR`/`_EVAL_DIR`/`_LOG_DIR` siblings) — not a
  new `Config` field.
- [ ] Import-topology guard (`tests/test_referee_guards.py`) extended so `referee_registry.py`
  sits inside the same Read-side-law boundary as the other referee modules (may import the
  rail / `BandMapResolver` / `referee_evidence`; `desk_playbook_detect`/`desk_playbook_context`
  never import it back).
- [ ] Rider (referee_null.py:533, reviewer NOTE carried from iteration 5): serve
  `backing_bucket_eligibility_rate: None` — not `0.0` — when nothing is measurable; the field
  is already typed `float|None` in the shipped contract, so this corrects an implementation
  bug inside an already-registered type, not a new field.
- [ ] Rider (test-only, `tests/test_referee_null.py`, carried from iteration 5's eval): one
  fixture offering more than `REFEREE_NULL_ANCHORS_PER_OCCURRENCE` (= 4) eligible anchors, so
  the seeded subset draw is actually discriminated by a test for the first time; one
  hand-computed `window_overlap_fraction` assertion.

### Frontend

None — J-05 is "(Keyless; automated.)" per its own acceptance; no page renders this
iteration's work (J-09 remains its first UI reveal, per the blueprint's Information
Architecture).

### New user-facing capability

None visible in the app this iteration. A new operator-facing capability exists at the
CLI/API layer (writing a hypothesis question down before its answer data exists) for J-07 to
build a UI onto next.

### New information displayed

None (no UI surface renders this iteration).

### New user actions

None via the UI. A new CLI command and a new confirmed `POST` act exist (registration,
withdrawal) but are not reachable from any page yet.

### UI surface changes

None.

### Product surface delta

None visible to a person browsing `/desk` today. The product now has a real, immutable
pre-registration mechanism that J-06 (adjudication), J-07 (the registration UI + the operator's
actual approvals), and J-08 (the certificate contract) all build on.

### Blueprint conformance

`/desk` → **Referee Registry** — already registered in `state/blueprint.md`'s Information
Architecture table at baseline (the J-05 row). No nav-skeleton change this iteration.

### Data-contract additions

The "Registry" row (owner `referee_registry.py`; `GET /research/desk/referee/registry`,
`POST .../registry/hypotheses`) is already registered in `state/blueprint.md`'s Data Contract
table since baseline (owner/endpoint unchanged). This iteration fills in its field-level shape
for the first time (full detail appended to `state/blueprint.md`'s iter-6 note; summarized
here):

- **Family record** (immutable, append-only): `family_id: str`, `q: float` (0 < q ≤ 1),
  `candidate_hypothesis_ids: list[str]` (the complete planned list = BH denominator m,
  forever), `registered_at: str` (ISO-8601 UTC).
- **Hypothesis record** (immutable, append-only): `hypothesis_id: str`, `family_id: str`,
  `registered_at: str`, `evidence_family: "playbook"|"strategy"`, `estimand: "A"|"B"|"C"`,
  `setup_id: str`, `side: "long"|"short"`, `context_predicate: dict|None` (B/C only),
  `primary_measure_key: str`, `primary_horizon: str`,
  `sidedness: "greater"|"less"|"two-sided"`, `null_spec_id: str|None` (None for
  `evidence_family="strategy"`), `test_spec_id: str`, `detector_basis: str|None` (None for
  strategy), `context_algorithm_version: str|None` (B/C only),
  `confirmation_start_boundary: str` (`"YYYY-MM-DD"` ET), `target_sessions: int`
  (≥ `REFEREE_MIN_SESSIONS`), `min_occurrences: int` (≥ `REFEREE_MIN_OCCURRENCES`),
  `origin: "historical-exploration"`. Fold-only additions on `GET`:
  `status: "active"|"withdrawn"`, `accrual: {informative_post_boundary_sessions: int,
  target_sessions: int, is_proxy: true, basis_current: bool}`.
- **Withdrawal record** (immutable, append-only): `hypothesis_id: str`,
  `withdrawn_at: str` (ISO-8601 UTC), `reason: str|None`.
- **Certificate record** (immutable, append-only store; shape only, per spec §8 — no writer
  until J-08): `candidate: {strategy_id: str, profile: str}`,
  `champion_identity_at_scan_time: dict`, `train_dataset: {id: str, checksum: str, split:
  str}`, `holdout_dataset: {id: str, checksum: str, split: str}`, `config_fingerprint: str`,
  `gate_version: str`, `referee_parameters_hash: str`, `family_id: str`, `hypothesis_id: str`,
  `gate_results: {calibrated_p: float, bh_pass: bool, ci: [float, float], floors_met: bool}`.
- **`GET /research/desk/referee/registry` response:** `{families: [...], hypotheses: [...],
  withdrawals: [...], certificates: []}` (certificates empty this iteration).

No second computation of any already-registered Data Contract value is introduced —
`playbook_occurrence_readiness()` (J-01), the ET-date helper (J-02/evidence), and
`BandMapResolver` (J-04/context) are imported, not re-implemented.

## OUT OF SCOPE

- J-06: estimand engines (A/B/C), the permutation test run, BH computation, verdict vocabulary,
  the confirmatory checkpoint. The registry stores hypothesis IDENTITY only — no statistical
  test runs inside this iteration's code.
- J-07: the shortlist UI, the registration-flow UI, and the operator's REAL registration of
  the 2–3 starter hypotheses. This iteration only builds the mechanism, exercised on fixtures.
- J-08: certificate MINTING, `authorize_promotion`, and the `pnl_scan` interlock. J-05 defines
  only the certificate record's append-only shape/store; nothing writes to it this iteration.
- The carried J-02 `epoch_anchor or 0.0` lead (iteration 4's decomposer note: must be settled
  before J-06, not before J-05) — no strategy-family code is touched this iteration.
- Any change to `desk_forward.py`, `desk_playbook*.py`, `levels.py`, `tradability.py`,
  `referee_stats.py`'s statistical procedures, or `pnl_scan.py` — read-only imports at most.
- New MCP tools (stays at 20), new `Config` fields, any fingerprint movement.
- Restarting trendora's backend on port 8255 (outside this project; still outstanding for a
  person since iteration 2 — not a build task).

## DEFINITION OF DONE

- [ ] J-05 passes: append-only proven across all four record kinds (no update/delete method;
  duplicate raises); malformed/duplicate/retroactive-boundary/unknown-spec-id each refused
  distinctly; a withdrawal after a post-boundary evaluation exists is refused; the ET-midnight
  boundary case lands on the correct session date — verified via `browser-qa-agent`'s
  keyless/automated lane (no screenshot required; J-05 carries no browser acceptance).
- [ ] Required-still-passing journeys (J-01, J-02, J-03, J-04; J-10's kept-product half) remain
  green — deterministic replay + LLM fallback.
- [ ] No anti-goal violation introduced — particularly immutable data, single source of truth,
  deterministic/seeded, never-shrink-the-BH-denominator, and no-gate-loosens-mid-era.
- [ ] Unit tests pass; no regressions — full suite count ≥ the iter-5 baseline (2,553
  collected / 2,545 passed / 8 skipped), zero failed.
- [ ] `Config().config_fingerprint()` prints `08e471b10130e1e2`; `EXPECTED_TOOLS` still parses
  to exactly 20 names.
- [ ] Store-scope guard over the owner's real `.data/` directory: all previously-recorded files
  (11,274 at the last recorded count) remain byte-identical.
- [ ] Dev handoff written at `docs/handoffs/goal-referee-iter-6-dev.md`.

## TESTING REQUIREMENTS

- Browser: none. J-05 is "(Keyless; automated.)" per its own acceptance (lesson iter-1: no
  golden replay script can exist for a backend-only journey). J-10's kept-product half is
  re-verified through the standard regression replay + a fresh screenshot — no new browser
  scenario is authored by this iteration.
- Unit/integration: new `tests/test_referee_registry.py` covering the scenarios below; riders
  in `tests/test_referee_null.py`; the import-topology extension in `tests/test_referee_guards.py`.
- Error cases: malformed registration payloads (missing required field, `target_sessions`/`min_occurrences`
  below floor, an unevaluable Estimand-C context predicate); duplicate `hypothesis_id`/`family_id`;
  a retroactive boundary; an unknown `null_spec_id`/`test_spec_id`; a withdrawal blocked by a
  post-boundary evaluation.

Test-first contract — TC- scenarios (each maps to a Definition-of-Done checkbox or a
Data-contract addition above):

- TC-1: given a fresh FamilyRecord store, when the same `family_id` is registered twice, then
  the second call raises and the store contains exactly one record for that id.
- TC-2: given a fixture Estimand-A registration (`capitulation`, `long`, primary `5m`,
  `null_spec_id="referee-null-tod-v1"`) submitted with explicit confirmation, then it returns a
  `hypothesis_id`, the stored record's `confirmation_start_boundary` equals the ET calendar
  date of its `registered_at`, and no update/delete method exists on the Hypothesis store class.
- TC-3: given a registration payload missing a required field (e.g. `primary_horizon`), when it
  is submitted, then the request is refused with a distinct "malformed" error and no record is
  written.
- TC-4: given a registration payload whose `confirmation_start_boundary` is explicitly supplied
  at or before `registered_at`'s own ET calendar date, when it is submitted, then it is refused
  with a distinct "retroactive boundary" error and no record is written.
- TC-5: given a registration payload naming `null_spec_id="referee-null-made-up-v9"`, when it is
  submitted, then it is refused with a distinct "unknown spec id" error and no record is
  written.
- TC-6: given an Estimand-C registration whose `context_predicate` names a band-context cell
  `BandMapResolver` cannot evaluate, when it is submitted, then it is refused as malformed and
  no record is written.
- TC-7: given a registration with `target_sessions` below `REFEREE_MIN_SESSIONS` (12), when it
  is submitted, then it is refused as malformed and no record is written.
- TC-8: given a registration at a UTC instant equal to 23:30 America/New_York on a hand-picked
  date, when it is submitted, then the stored `confirmation_start_boundary` equals that same ET
  calendar date — not the UTC calendar date and not the following ET date.
- TC-9: given a registered hypothesis with no post-boundary evaluation on record, when it is
  withdrawn, then the withdrawal succeeds, a WITHDRAWAL record is appended, and the
  hypothesis's folded `status` on `GET .../registry` reads `withdrawn`.
- TC-10: given a registered hypothesis with a fixture-injected post-boundary-evaluation signal
  set `True`, when a withdrawal is attempted, then it is refused, no WITHDRAWAL record is
  written, and the hypothesis's folded `status` stays `active`.
- TC-11: given a populated fixture registry (≥2 hypotheses spanning ≥2 distinct `(setup_id,
  side)` cells with known observation counts and known post-boundary session dates), when
  `GET /research/desk/referee/registry` is called, then each hypothesis's
  `accrual.informative_post_boundary_sessions` matches a hand-counted value from the fixture
  corpus, `accrual.is_proxy` is `true`, and `accrual.target_sessions` equals the value pinned
  at registration.
- TC-12: given the Certificate store seeded with one hand-built fixture certificate dict (no
  production minting call), when the same `certificate_id` is inserted twice, then the second
  call raises and no update/delete method exists on the store class.
- TC-13: given the CLI registration command and the equivalent `POST` body for the same fixture
  Estimand-A candidate, when both are run, then they produce byte-identical stored Hypothesis
  records.
- TC-14: given the five starter-family candidate definitions (spec §7, S-1..S-5), when each is
  submitted in turn as a fixture registration, then all five are accepted with zero refusals
  and produce five distinct `hypothesis_id`s carrying the estimand/null-spec/primary pairing
  spec §7's table names.
- TC-15: given a `referee_null.py` fixture offering 7 eligible anchor candidates with
  `REFEREE_NULL_ANCHORS_PER_OCCURRENCE = 4`, when the seeded draw runs twice on the same
  observation key, then both runs return the identical, hand-verified, non-trivial 4-element
  subset, and a second observation key returns a different subset.
- TC-16: given a hand-computed pair of measurement windows with a known overlap fraction, when
  `window_overlap_fraction` computes it, then the returned value equals the hand-computed
  fraction to within float tolerance.
- TC-17: given a context-variant null build where zero anchors are ever measurable for an
  occurrence, when `build_null_record` runs, then `backing_bucket_eligibility_rate` is `None`,
  never `0.0`.
- TC-18: given the full backend test suite, when it runs after this iteration's changes, then
  it collects at least the iter-5 baseline count, ≥2,545 tests pass, 0 fail, and
  `Config().config_fingerprint()` prints `08e471b10130e1e2`.
- TC-19: given `apps/backend/tests/test_mcp_server.py::EXPECTED_TOOLS`, when parsed after this
  iteration, then it still contains exactly 20 tool names.
- TC-20: given the store-scope guard over the owner's real `.data/` directory, when it runs
  after this iteration's test suite, then every previously-recorded file remains byte-identical
  to the last recorded baseline.

## NOTES

- **Naming caution:** the codebase already has an unrelated `ResearchRegistry` class
  (`app/research/routes.py`, a dependency-injection container for stores). The new
  `referee_registry.py`'s FAMILY/HYPOTHESIS/WITHDRAWAL/CERTIFICATE registry is a completely
  different concept sharing only the English word "registry" — keep the two nowhere near each
  other in imports/naming to avoid a reviewer false-positive.
- **Two interpretation calls logged this iteration** (`state/assumptions.md`, both reversible,
  both zero-consumer today): (1) the registry's `accrual` field is a disclosed readiness PROXY,
  not spec §3.1's exact informative-session count — J-06 supersedes it; (2) null records stay
  filed by null-spec id, never re-keyed under `hypothesis_id`, closing iteration 5's carried
  open question now that hypothesis ids exist to file under.
- **Certificate scope is deliberately thin.** Step 1 of J-05 assigns the certificate record's
  shape to `referee_registry.py`; its mint path is explicitly J-08's job per both goal.md
  ("mintable only through the real evaluation rail") and spec §8. Building the shape/store now
  (fixture-tested for append-only-ness only) means J-08 does not have to also design store
  mechanics under its own time pressure.
- **Outstanding for a person, unchanged since iteration 2, outside this project:** trendora's
  backend on port 8255 has still not been restarted.
- **Host protection, not a verbatim anti-goal quote but binding per goal.md's "Host protection"
  clause:** keep this iteration's own tool-time tight — an earlier iteration this session
  already hit a wall-clock cap mid-step, and host-guard CPU/memory ceilings apply to every
  heavy path. Use exact-PID process stops for any dev-server restart, never a pattern-based
  `pkill` (iter-2 lesson: a pattern match hit an unrelated project's backend on this shared
  host).
