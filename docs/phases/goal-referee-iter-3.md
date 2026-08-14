# Goal Iteration 3 — J-03: the statistics core (calibrated, seeded, oracle-proven, fail-closed)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** referee
- **Iteration:** 3
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — `referee_stats.py` becomes new shared statistical architecture that
  J-04–J-08 (five future journeys) will all import for their actual verdict math; a subtle
  implementation bug here would pass its own isolated unit tests while silently invalidating
  every later confirmatory/exploratory verdict the Referee ever prints — the cross-module
  blast-radius trigger 1 targets, matching the evaluator's own iter-2 reasoning verbatim ("a
  wrong sum there would pass its own tests while quietly spoiling every later verdict").
- **Frontend Present:** yes (no frontend code changes this iteration — J-03 is backend-only per
  goal.md's `(Keyless; automated.)` marker; browser-qa still runs the J-10 regression sentinel:
  cockpit `/`, `/structure`'s AAPL Load, and every shipped `/desk` section, per the "rides every
  iteration" binding note in `iteration-state.md`)
- **Target journeys:** J-03
- **Required-still-passing journeys:** J-01, J-02, J-10
- **Anti-goal reminders:** (verbatim from `docs/goal.md`; the subset this iteration's build
  surface actually touches — see full list under § Anti-goals for the rest)
  - 3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
    them, never a mutation of them. *(critical)*
  - 6. **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - 7. **Deterministic and seeded** — every random draw uses a recorded named seed via per-row
    streams; identical requests reproduce byte-identical results; no wall-clock, no unseeded
    randomness in any research artifact. *(critical)*
  - **CI-inversion is never a p-value.** Ordinary bootstrap quantities are uncertainty
    intervals; every p that feeds BH comes from a spec-named null-calibrated randomization
    procedure; the oracle suite guards the distinction. *(critical)*
  - **No confirmatory output without a verified oracle attestation.** The adjudication fold
    never serves a confirmatory verdict from an evaluation whose attestation is missing,
    mismatched, or version-stale — it serves the refusal state with its reason; descriptive
    output never masquerades as confirmatory. *(critical)*
  - **No gate loosens mid-era.** q, floors, targets, K, B, and every eligibility rule are fixed
    at registration; `insufficient_sample` is an answer, never a reason to widen anything.
    *(critical)*
  - **The Referee never feeds back.** No referee output gates, filters, ranks, or tunes any
    detector, context, screen, or strategy computation (import-ban + source-scan guard-tested);
    the frozen research vocabulary stays frozen. *(critical)*

## GOAL

Backend-only: the calibrated statistics engine — seeded per-row streams, percentile bootstrap
confidence intervals at two clustering levels, the within-session group-label permutation test
that is the primary confirmatory procedure, sign-flip/equal-weight robustness disclosures,
Benjamini–Hochberg with Benjamini–Yekutieli disclosure, and a fail-closed oracle attestation —
exists as a proven, independently-oracle-verified library (`referee_stats.py`) that every later
Referee journey (J-04 through J-08) will import for its real p/CI/BH math, with the seeded
oracle suite itself serving as this iteration's acceptance rather than a fixture-only test.

## BACKGROUND

Priority rubric: no journey regressed at iteration 2 (rule 1 n/a). Iteration 2's `coherence.md`
was `COHERENCE-PASS`, not FAIL, so rule 2 (consolidation before features) does not apply. J-03 is
the next unblocker in goal.md's own stated dependency order (J-01 → J-02 → J-03 → …) and is a
named, direct dependency of J-06's estimand evaluators ("each computing... consuming the
contract (J-02), nulls (J-04), and stats core (J-03)") — rule 3 is satisfied and nothing else in
the backlog unblocks more (rule 4 n/a, single obvious next target). Exactly one journey is
targeted, and it is deliberately the ONLY risky journey in this iteration rather than bundled
with another (rule 5): J-04 (nulls) and J-08 (promotion interlock) are both separately risky and
explicitly left for later iterations. It is not human-blocked: `iteration-state.md`'s Active
blockers section states J-03 is "buildable today: keyless, backend-only, no new dependency"
(rule 6 n/a); the only human-owned blocker on file (trendora's `:8255` restart) is outside this
project and does not gate tapeology. Real code and a real proof suite land this iteration, so
rule 7 (no evidence-only iterations) does not apply. This exactly matches the iter-2 evaluator's
own explicit next-step recommendation: "Build J-03 ... next, alone, ... at full depth."

**Depth is full, trigger 1.** Checking the other three triggers explicitly, none independently
holds: the prior verdict was `CONTINUE` with zero regressions, not `ESCALATE`/`REGRESSION`
(trigger 3 n/a); iteration 2's `coherence.md` is `COHERENCE-PASS`, not FAIL (trigger 2 n/a — and
separately, J-03 adds no new/changed Data-Contract value at all, so the data-model-migration
trigger could not apply regardless); consecutive lean iterations sits at 2 of the 6-iteration
hardening cadence, not due (trigger 4 n/a); and J-03 carries zero frontend work, so it is not a
brand-new full-stack journey either (that specific trigger-4 variant n/a). Trigger 1 is what
applies: `referee_stats.py` is new SHARED statistical architecture — the one module J-04's
test-spec consumption, J-06's three estimand evaluators, and J-08's strategy-family gate will all
import for their real verdict math — and its own isolated oracle suite can prove internal
calibration correctness but cannot exercise the eventual multi-module integration J-06 will
require. A wrong sum, a mis-seeded stream, or a CI-that-is-secretly-a-p-value substitution here
would pass this iteration's own tests while quietly invalidating every confirmatory/exploratory
verdict the Referee ever prints later — precisely the blast-radius trigger 1 targets, and
precisely why the evaluator asked for the extra full-pipeline review lanes (planner,
functional-test-plan, audit, closure) on top of the developer/reviewer pair a lean cycle would
give it.

**Lessons applied.** Per `lessons.md`'s iter-1 entry, no golden replay script exists for a
backend-only route, and the recommended fallback lane is "pytest + an LLM browser-qa
live-endpoint smoke pass" — but that fallback itself does not apply to J-03: unlike J-01/J-02, J-03
serves no HTTP endpoint at all (it is a library module plus a proof suite, unconsumed by any
route this iteration), so there is no live endpoint to smoke and the ENTIRE verification lane is
the pytest oracle suite. Per iter-2's lesson, any dev-server cleanup must use exact-PID
process-tree kills only, never `pkill -f` (which killed an unrelated project's backend last
iteration and is still down) — restated in OUT OF SCOPE.

**Riders carried, per the binding "Do not redo" list and iteration 2's eval.** Three small
leftovers ride along with J-03 rather than becoming their own iteration: (1) test
`_signal_reaches_session_complete` in `referee_evidence.py` (currently zero assertions, a
gap-blind estimate J-06's confirmatory-eligibility fold will lean on); (2) test
`resolve_referee_obs_cache_db_path` (exported, never called); (3) close the `detector_basis`
wording rider. On (3): iteration 2's eval asked for "an owner ruling ... before J-06 assumes the
field is populated," but goal mode is headless and no human ruling is available before this
iteration closes. Per this agent's "decide from evidence, do not ask" instruction, this
iteration ratifies iter-2's already-accepted, already-reversible convention
(`detector_basis: None` for strategy observations, mirroring `context_algorithm_version`'s
existing "None when inapplicable" pattern) as standing for this era via one documentation-only
sentence in the spec — logged as a fresh entry in `state/assumptions.md` (see NOTES). None of
the three riders touches `referee_evidence.py`'s own source, only its test file and one spec
sentence — so J-01/J-02's served response shape is unaffected (still Required-still-passing, not
re-targeted).

## IN SCOPE

### Backend

- [ ] Build `apps/backend/app/research/referee_stats.py` implementing
  `docs/referee-statistical-spec.md` §1's constants that THIS module directly consumes as module
  constants (never `Config` fields), read at call time: `REFEREE_SEED = 271828`,
  `REFEREE_STREAM_RECIPE`, `REFEREE_B = 10_000`, `REFEREE_ENUMERATION_THRESHOLD = 8_192`,
  `REFEREE_CI_LEVEL = 0.95`, `REFEREE_MIN_CLUSTERS_FOR_CI = 8`, `REFEREE_ORACLE_B = 2_000`,
  `REFEREE_ORACLE_REPLICATIONS = 400`, `REFEREE_ORACLE_BUDGET_SECONDS = 120`,
  `REFEREE_ORACLE_SIZE_TOLERANCE` (the `[0.5·α, 1.5·α]` band at α = 0.05, i.e. `[0.025, 0.075]`).
  §1's OTHER constants (`REFEREE_MIN_SESSIONS`, `REFEREE_MIN_OCCURRENCES`,
  `REFEREE_NULL_ANCHORS_PER_OCCURRENCE`, `REFEREE_TOD_BUCKETS`, `REFEREE_GATE_VERSION`,
  `REFEREE_DEFAULT_Q`) belong to J-04/J-05/J-06/J-08's own consuming modules, not this one —
  whether the developer pre-declares them here for later reuse or defers them to their consuming
  journey is an open, non-blocking file-organization choice, not a spec ambiguity.
  `REFEREE_SESSION_COMPLETE_ET` already lives in `referee_evidence.py` (J-01) — reused, never
  redefined, if this module ever needs it.
- [ ] The seeded per-row stream constructor implementing the pinned recipe verbatim:
  `f"{REFEREE_SEED}:{hypothesis_id}:{purpose}[:{session_date}[:{i}]]"`
  (`purpose ∈ {"null-draw","perm","flip","boot-occ","boot-cluster"}`). Every draw goes through
  `random.Random(stream)` with the hand-coded Fisher–Yates idiom
  (`desk_forward._draw_anchor_indices`'s discipline, reused or matched exactly) — never
  `random.sample`, never a shared/global `random.Random()` instance, never numpy's RNG for any
  seeded draw (numpy is already an idiomatic dependency elsewhere, e.g. `levels.py`, but must
  never be the source of a seeded draw here — it would break the hand-coded discipline and the
  byte-identical reproducibility requirement in a way that would not show up as an obvious bug).
- [ ] Percentile bootstrap CI at `REFEREE_CI_LEVEL`, BOTH clustering levels always computed side
  by side: occurrence-level (`purpose="boot-occ"`, resample paired per-occurrence differences
  with replacement) and session-clustered (`purpose="boot-cluster"`, resample informative
  sessions with replacement — a drawn session carries ALL its observations, the statistic is T).
  Below `REFEREE_MIN_CLUSTERS_FOR_CI` informative sessions, the clustered-CI call returns the
  literal `insufficient_sample` state, never a fabricated interval. MDE (`≈ z_{1−α}·sd*(T)`) is
  served from the clustered resamples as the power disclosure.
- [ ] The within-session group-label permutation engine (`referee-test-perm-v1`'s ALGORITHM —
  see OUT OF SCOPE on the id/signature itself): the combined statistic
  `T = Σ_s w_s·Δ_s / Σ_s w_s` with the two pre-registered weight forms (A/C harmonic
  `n_s·K_s/(n_s+K_s)`; B `n1_s·n2_s/(n1_s+n2_s)`); independent per-session seeded sub-streams
  (`purpose="perm"`) that preserve group sizes; full enumeration when the total permutation
  space is ≤ `REFEREE_ENUMERATION_THRESHOLD`, else exactly `REFEREE_B` seeded draws;
  `p = (1 + #{T* ≥ T}) / (B + 1)` for registered sidedness "greater" (mirrored for "less";
  `|T*| ≥ |T|` for "two-sided"); the minimum-attainable p (granularity) served beside every p.
- [ ] Session-level sign-flip (`purpose="flip"`) and equal-session-weight (`w_s = 1`) robustness
  variants — computed and served alongside every confirmatory result, feeding ONLY the future
  `fragile` verdict rule (J-06 builds the verdict fold); NEVER substituted for the primary
  permutation p anywhere in this module.
- [ ] Benjamini–Hochberg (caller-supplied registered `q`, caller-supplied `m` = the family's
  planned count — an unevaluated or withdrawn-after-checkpoint candidate folds as `p = 1`, never
  dropped from `m`) with Benjamini–Yekutieli served beside it as a non-deciding
  dependence-robustness disclosure, per spec §5's BH rule.
- [ ] `run_oracle_attestation()`: executes a pinned known-answer subset (fixed seeds, fixed tiny
  fixture datasets, exact expected p/CI digests with stated tolerances) and returns
  `{expected, actual, tolerance, passed, stats_core_version}`; round-trips on the pinned subset;
  a corrupted/mismatched attestation (one changed byte/field) is DETECTED by the verifier, never
  silently accepted as passing.
- [ ] Build `apps/backend/tests/test_referee_oracles.py` — the seeded oracle suite per spec §6,
  ALL SIX cases (null calibration iid-skewed; null calibration heavy-tailed; the two DEMONSTRATED
  failures — the unclustered foil over-rejecting and the sign-flip mis-sizing; power at S=40;
  the 20-null+1-positive BH sweep; CI coverage at S=40 and the S=6 `insufficient_sample` case)
  plus a deliberately mis-implemented test-statistic mutation fixture that must fail calibration
  — the whole suite completing within `REFEREE_ORACLE_BUDGET_SECONDS`.
- [ ] Carried rider 1 (non-blocking, ride along): extend
  `apps/backend/tests/test_referee_evidence.py` with real assertions for
  `_signal_reaches_session_complete` (currently zero coverage) at and around the
  `REFEREE_SESSION_COMPLETE_ET` boundary, including its disclosed bar-gap-blind limitation as an
  asserted behavior, not a silently-passing one.
- [ ] Carried rider 2 (non-blocking, ride along): extend the same test file with real assertions
  for `resolve_referee_obs_cache_db_path` (exported, never called) — the env-var-override path
  and the sibling-of-playbook-dir default path.
- [ ] Carried rider 3 (non-blocking, ride along; see NOTES + the new `state/assumptions.md`
  iter-3 entry): add ONE clarifying sentence to `docs/referee-statistical-spec.md` §2 documenting
  that `provenance.detector_basis` is `None` for every strategy-family observation by design. A
  documentation-only closure — zero `.py` diff for this specific rider, not a named spec revision
  (no constant, weight, eligibility rule, or test procedure changes).
- [ ] Extend `apps/backend/tests/test_referee_guards.py` (or a companion) with a
  `referee_stats.py`-scoped guard, matching the existing bidirectional AST import-ban pattern:
  `referee_stats.py` imports none of `desk_playbook_detect`, `desk_playbook_context`,
  `desk_forward`, `levels`, `tradability` (the stats core is estimand-agnostic — it consumes
  plain numeric/session arrays a future caller passes in, never rail/detector/context data
  directly) — with a seeded can-fail counter-test proving the guard actually detects a violation.
- [ ] Zero new `Config` fields; zero diff to `desk_playbook*.py`, `desk_forward.py`, `levels.py`,
  `tradability.py`, `setups.py`, `pnl_scan.py`, `app/config.py`, `app/main.py`, any route file,
  and `apps/backend/app/research/referee_evidence.py`'s own SOURCE (only its test file gains the
  two rider test functions).

### Frontend

- (none — J-03 is backend-only; goal.md marks it `(Keyless; automated.)`)

### New user-facing capability

None yet. `referee_stats.py` is unconsumed by any route, page, or MCP tool this iteration.

### New information displayed

None (no UI change this iteration).

### New user actions

None.

### UI surface changes

None.

### Product surface delta

None visible in the UI this iteration. `referee_stats.py` becomes a new, oracle-proven internal
library — the calibrated statistics engine every later Referee journey (J-04's test-spec
consumption, J-06's estimand evaluators, J-08's strategy-family gate) will call for its actual
p/CI/BH math — but it is not wired into any caller, route, or page yet.

### Blueprint conformance

Already covered by the existing blueprint IA row: "J-02 evidence contract, J-03 stats core
(library modules, no page of their own) | n/a — consumed by J-04–J-09 | —". No edit needed —
`state/blueprint.md` is unchanged this iteration.

### Data-contract additions

None. `referee_stats.py` serves no HTTP endpoint and displays no value this iteration; it is a
pure computation library consumed by later journeys' own already-listed Data-Contract rows
(nulls, registry, evaluations, adjudications), not a new served surface of its own.

## OUT OF SCOPE

- J-04's matched nulls, the null store, compute manager, or CLI — including MINTING the
  `referee-null-tod-v1`, `referee-null-context-v1`, and `referee-test-perm-v1` signature-bearing
  spec ids, which is explicitly J-04's own Step 3 deliverable. J-03 builds the permutation-test
  ALGORITHM only, never its stored identity.
- J-05's registry.
- J-06's estimand engines (A/B/C) or adjudication fold — `referee_stats.py` ships unconsumed
  this iteration; no caller wires it into an actual estimand computation.
- J-07's shortlist/registration UI, J-09's `/desk` sections and the two new MCP tools — zero
  frontend, zero MCP diff (`EXPECTED_TOOLS` stays the existing 20-tuple).
- J-08's promotion interlock / `authorize_promotion` — `pnl_scan.py` stays byte-identical.
- Any change to `referee_evidence.py`'s SOURCE code (only its test file gains rider coverage);
  no change to the served `GET /research/desk/referee/evidence` body.
- Any new REST route, any new `Config` field, any new runtime dependency — `requirements.txt`/
  `pyproject.toml` stay unchanged; numpy (already present, used in `levels.py`) is confined to
  non-random numeric aggregation only if used at all — never for a seeded draw; `scipy` stays
  absent, per goal.md's Non-Goals.
- Any statistical constant, weight, eligibility rule, or test procedure not pinned in
  `docs/referee-statistical-spec.md` §1/§3.4–§3.6/§6 — an ambiguous or unimplementable clause is
  DROPPED and surfaced for an owner ruling, never improvised (T-1), with the one exception of the
  already-ratified, documentation-only `detector_basis` rider (IN SCOPE item above).
- Real registration, evaluation, or null-build operator acts — none of that machinery exists yet.
- Pattern-based process kills of any kind (`pkill -f` or similar) for dev-server cleanup —
  exact-PID process-tree kill only (iter-2 lesson: a pattern-based kill took down an unrelated
  project's backend and it is still down). No action on trendora's `:8255` restart — human-owned,
  outside this project, does not block this iteration.
- Re-verifying or re-scoring J-01, J-02, or J-10 as target journeys — all three ride along only
  as Required-still-passing.

## DEFINITION OF DONE

- [ ] Target journey J-03 passes: the seeded oracle suite (`tests/test_referee_oracles.py`) is
  green, completes within `REFEREE_ORACLE_BUDGET_SECONDS`, and is reproduced independently (not
  taken on the developer's report) — reviewer and evaluator each re-run the suite themselves and
  read the mutation-fixture and demonstrated-failure test bodies line by line to confirm expected
  values are hand-derived, not copied from the implementation under test.
- [ ] Required-still-passing journeys J-01 and J-02 remain green: `GET
  /research/desk/referee/evidence` serves the SAME byte-identical response shape as iteration 2
  (pytest re-run of `tests/test_referee_evidence.py` + `tests/test_referee_guards.py`, not golden
  replay — no replay script can exist for this backend-only route, per `lessons.md`'s iter-1
  entry).
- [ ] Required-still-passing journey J-10 remains green (deterministic replay of the stored
  golden where it applies, else the LLM browser-qa fallback — cockpit, `/structure` AAPL Load,
  every shipped `/desk` section).
- [ ] No anti-goal violation introduced: `Config().config_fingerprint()` still prints
  `08e471b10130e1e2`; zero diff to the named frozen modules; zero new `Config` fields; zero new
  runtime dependency; MCP still advertises exactly 20 tools; the new `referee_stats.py`
  import-ban/read-side guard is green; zero writes to any pre-existing store file (SHA-256
  listing unchanged — this iteration's new module writes to no store at all, seeded or
  otherwise).
- [ ] Unit tests pass; full backend suite ≥ 2,446 pass / 8 skip (iteration 2's recorded floor);
  no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-referee-iter-3-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-10 only (regression sentinel — cockpit `/`, `/structure` AAPL Load, every shipped
  `/desk` section). J-03 itself needs no browser check and has no live endpoint to smoke — goal.md
  marks it `(Keyless; automated.)` and its entire acceptance runs against the seeded oracle suite;
  unlike J-01/J-02, J-03 serves nothing over HTTP this iteration, so not even an endpoint smoke
  pass applies to it.
- Unit/integration: `tests/test_referee_oracles.py` (new) must exist and pass all 6 oracle cases
  plus the mutation-fixture calibration-failure case, within budget; `tests/test_referee_evidence.py`
  gains the two rider test functions; `tests/test_referee_guards.py` gains the `referee_stats.py`
  import-ban check with its own can-fail counter-test; the full existing suite stays green at
  ≥ 2,446 pass / 8 skip.
- Error cases: a corrupted/mismatched oracle attestation must be DETECTED, never silently accepted
  as passing; a clustered-CI request below `REFEREE_MIN_CLUSTERS_FOR_CI` must return the literal
  `insufficient_sample` state, never a fabricated interval; the deliberately wrong test-statistic
  mutation fixture must FAIL calibration, never pass by coincidence.

Test-first contract:

- TC-1: given the pinned stream recipe with a fixed `(hypothesis_id, purpose, session_date, i)`
  tuple, when the stream constructor is called twice with identical inputs, then both calls
  produce byte-identical `random.Random` draw sequences, and no code path in the module calls
  `random.sample` or constructs an un-seeded/global `random.Random()` instance.
- TC-2: given a small fixture set of paired per-occurrence differences, when the occurrence-level
  percentile bootstrap CI runs at `REFEREE_CI_LEVEL` with a seeded stream, then two independent
  runs with identical inputs produce byte-identical CI bounds, and the bounds match a
  hand-computed percentile expectation on the tiny fixture.
- TC-3: given a fixture with fewer than `REFEREE_MIN_CLUSTERS_FOR_CI` (8) informative sessions,
  when the session-clustered CI is requested, then the result is the literal `insufficient_sample`
  state, never a fabricated interval; given a fixture with ≥ 8 informative sessions, the same call
  instead returns a real interval plus an MDE disclosure.
- TC-4: given a fixture whose total within-session label-permutation space is ≤
  `REFEREE_ENUMERATION_THRESHOLD` (8,192), when the permutation p-value is computed, then it
  enumerates every permutation exactly (deterministic, no seeded sampling) and matches a
  hand-computed p-value on a tiny known fixture.
- TC-5: given a fixture whose permutation space exceeds `REFEREE_ENUMERATION_THRESHOLD`, when the
  p-value is computed, then exactly `REFEREE_B` (10,000) seeded draws are used,
  `p = (1 + #{T* ≥ T}) / (B + 1)` for "greater" sidedness, and two runs with identical seeds and
  inputs return byte-identical p.
- TC-6: given a fixture where the sign-flip and equal-weight robustness variants disagree with the
  primary permutation result, when both are computed, then both values are returned/served
  alongside the primary p, and the primary p returned to the caller is unchanged by that
  disagreement (the variants never substitute for the primary decision).
- TC-7: given a fixture family of checkpoint p-values with a known planned count `m` and a
  registered `q`, when BH is applied, then the corroboration boundary `k*` matches a
  hand-computed `max{k : p_(k) ≤ (k/m)·q}`; given one candidate marked unevaluated/withdrawn, its
  p folds as the literal value `1` and stays inside `m` rather than being dropped; the
  Benjamini–Yekutieli-adjusted values are returned as a separate, non-deciding field.
- TC-8: given the lognormal-shifted-to-zero-mean generator at n_s=1/K=4 (spec §6 case 1), when the
  seeded oracle simulation runs `REFEREE_ORACLE_REPLICATIONS` (400) replications at α = 0.05, then
  the empirical rejection rate falls inside `REFEREE_ORACLE_SIZE_TOLERANCE`'s band (`[0.025,
  0.075]`).
- TC-9: given the Student-t(3) heavy-tailed generator (spec §6 case 2), when the same simulation
  runs, then the empirical rejection rate again falls inside the `[0.025, 0.075]` band.
- TC-10: given the session-clustered-with-regime generator, when an UNCLUSTERED pooled-label
  permutation foil (a deliberately wrong procedure) is run against it, then its empirical
  rejection rate falls ABOVE the tolerance band's ceiling (0.075) — it must over-reject, proving
  the primary within-session test is necessary.
- TC-11: given the skewed n_s=1/K=3 one-sided fixture, when the session-level sign-flip variant is
  run as if it were the decision rule, then its empirical rejection rate falls outside the
  `[0.025, 0.075]` band (mis-sized), while the true within-session label permutation computed on
  the SAME fixture in the same test run holds size (inside the band).
- TC-12: given the +0.5·sd location-shift fixture at S = 40 informative sessions (spec §6 case 4),
  when the seeded power simulation runs, then the reported rejection rate matches a pinned golden
  value within its stated tolerance.
- TC-13: given 20 known-null candidates plus 1 known-positive candidate (m = 21, spec §6 case 5),
  when BH at q = 0.10 is applied to each of a seeded set of replications' checkpoint p-values,
  then the false-admission rate across replications stays within its binomial tolerance band, and
  the known-positive is admitted in the large majority of replications, matching the pinned
  golden.
- TC-14: given S = 40 sessions with a known true session-mean effect (spec §6 case 6), when the
  clustered percentile CI is computed across replications, then its empirical coverage is ≈ 95%
  within tolerance; given S = 6 sessions (below `REFEREE_MIN_CLUSTERS_FOR_CI`), the identical call
  instead returns the literal `insufficient_sample` state.
- TC-15: given a deliberately mis-implemented test statistic (the mutation fixture — e.g. one that
  ignores session clustering or applies a wrong sign/weight), when it is substituted into the
  oracle suite's calibration case, then that mutant's empirical rejection rate falls OUTSIDE the
  `[0.025, 0.075]` tolerance band — the mutant fails calibration, proving the suite would catch a
  wrong implementation.
- TC-16: given identical seeds and identical fixture inputs, when the full CI+p+BH computation
  runs twice as separate calls, then every returned p value and every CI bound is byte-identical
  between the two runs.
- TC-17: given the pinned known-answer subset, when `run_oracle_attestation()` runs, then it
  returns `{expected, actual, tolerance, passed=True, stats_core_version}` with `actual` matching
  `expected` within `tolerance`; given one field of a serialized attestation record altered before
  it is handed to the fold-time verifier, then the verifier reports the mismatch (`passed=False`
  or an explicit corruption signal), never silently accepting it.
- TC-18: given the full oracle suite (`tests/test_referee_oracles.py`), when it is run end-to-end,
  then it completes within `REFEREE_ORACLE_BUDGET_SECONDS` (120 seconds).
- TC-19: given this iteration's complete diff, when `requirements.txt`/`pyproject.toml` are
  inspected, then neither file changed; when `referee_stats.py`'s imports are inspected, then it
  imports only stdlib (`statistics`, `random`, `math`, etc.), never `scipy`, and never numpy for
  any seeded draw.
- TC-20: given a fixture signal engineered so its computed `last_bar_epoch` lands exactly at, one
  second before, and one second after `_session_complete_epoch(session_date)`
  (`REFEREE_SESSION_COMPLETE_ET = "15:55"` ET), when `_signal_reaches_session_complete` is called
  on each, then it returns `True` at and after the boundary and `False` strictly before it.
- TC-21: given `TAPEOLOGY_REFEREE_OBS_CACHE_DB` unset, when
  `resolve_referee_obs_cache_db_path(desk_universe_dir_resolved)` is called, then it returns a
  path that is a sibling of the resolved playbook directory named `referee_obs_cache.db`; given
  the env var set to an explicit path, when the same function is called, then it returns that
  exact override path verbatim.
- TC-22: given `docs/referee-statistical-spec.md` §2 after this iteration's one added sentence,
  when the section is read, then it explicitly states `detector_basis` is `None` for
  strategy-family observations by design; when the full diff for this rider is inspected, then it
  touches zero `.py` files (documentation-only).
- TC-23: given `referee_stats.py`, when the extended `tests/test_referee_guards.py` import-ban
  scan runs, then it finds zero imports of `desk_playbook_detect`, `desk_playbook_context`,
  `desk_forward`, `levels`, or `tradability` inside `referee_stats.py`, and the guard's own
  seeded counter-test (a deliberately inserted violation) causes the guard to fail, proving it can
  actually catch a violation.
- TC-24: given the complete iteration diff, when the full backend suite runs, then it reports pass
  and skip counts each ≥ 2,446 pass / 8 skip with zero errors, and `Config().config_fingerprint()`
  still prints `08e471b10130e1e2`.
- TC-25: given `GET /research/desk/referee/evidence` unchanged by this iteration, when
  `tests/test_referee_evidence.py`'s existing J-01 and J-02 fixture assertions (the readiness
  fold plus both adapters' golden fixtures) are re-run, then every assertion passes unmodified
  and the response body matches iteration 2's recorded shape byte-for-byte.
- TC-26: given this iteration's complete diff, when `tests/test_mcp_server.py::EXPECTED_TOOLS` is
  inspected and a SHA-256 listing of every pre-existing playbook/dataset/journal store file is
  taken before and after the diff, then `EXPECTED_TOOLS` still has exactly 20 entries and the two
  listings are byte-identical.
- TC-27: given the T-9 clean rebuild (`rm -rf apps/frontend/.next`, rebuild, restart), when J-10's
  regression walk runs (deterministic replay of the stored golden where it applies, else the LLM
  browser-qa fallback), then the cockpit sim tape/chart, `/structure`'s pinned-AAPL Load, and
  every shipped `/desk` section render exactly as shipped, each evidenced by a screenshot.

## NOTES

- **The "test-spec id" split.** `referee-test-perm-v1` names the permutation ALGORITHM this
  iteration builds, but MINTING it as a stored, signature-bearing spec id is explicitly J-04's own
  Step 3 deliverable ("Mint the null-spec and test-spec ids... that J-05 hypothesis records will
  reference immutably"). Do not mint or hash a `referee-test-perm-v1` identity record this
  iteration — build the function, leave the id-minting to J-04.
- **§1 constants split.** This spec deliberately scopes `referee_stats.py`'s OWN constants to
  only what its own functions consume (streams, CI, permutation, oracle budget/tolerance). The
  remaining §1 constants (`REFEREE_MIN_SESSIONS`, `REFEREE_MIN_OCCURRENCES`,
  `REFEREE_NULL_ANCHORS_PER_OCCURRENCE`, `REFEREE_TOD_BUCKETS`, `REFEREE_GATE_VERSION`,
  `REFEREE_DEFAULT_Q`) belong to their consuming journeys (J-04/J-05/J-06/J-08); whether the
  developer pre-declares them here now or defers them is a normal, reversible file-organization
  choice — not a T-1 spec ambiguity requiring a drop-and-surface.
- **`referee_parameters()` (the desk-pattern aggregator).** Not required to exist as a
  full-era aggregator this iteration — J-03's own constants may simply live as plain module
  constants for now, with the full `referee_parameters()` embedding-and-hashing pattern arriving
  once a record-writing journey (J-04) actually needs to hash parameters into a stored identity.
  Building a stub now that only covers this iteration's constants is fine; do not block on it.
- **Assumption ledger entry added this iteration** (`state/assumptions.md`, `## iter-3 —
  goal-decomposer`): ratifies iter-2's accepted `detector_basis: None` convention as standing for
  this era, since no human owner ruling is available in headless goal mode. Reversible — a future
  explicit owner ruling can still override the one added sentence.
- Per the binding "Do not redo" list: backend-only journeys get a `not_yet` golden stub (see
  `journey-scripts/J-01.json`, `J-02.json`) — expect J-03 to land the same way during execution;
  this is infrastructure the pipeline creates, not something to author here.
- Traps most relevant this iteration (`docs/goal.md` § Build anchors & weak-model traps): **T-1**
  (the spec is law — an ambiguous/unimplementable clause is dropped and surfaced, never
  improvised); **T-3** (CI-inversion is not a p-value — the ordinary bootstrap is NEVER the null
  distribution; only the within-session permutation feeds BH; TC-10/TC-11's demonstrated-failure
  cases exist to prove this distinction mechanically); **T-8** (fail closed — the attestation is
  verified, never trusted; TC-17 pins the corruption-detection half).
- Anchors to re-locate by symbol name (grep), never by line arithmetic: `_draw_anchor_indices`
  :428 and `_measure_from` :451 in `desk_forward.py` (the Fisher–Yates/measurement idiom this
  module's stream discipline must match, though `referee_stats.py` itself does not import
  `desk_forward` — see the import-ban guard); `REFEREE_SESSION_COMPLETE_ET`,
  `_signal_reaches_session_complete`, `resolve_referee_obs_cache_db_path`, and the bidirectional
  import-ban pattern in `test_no_referee_module_imports_the_detect_or_context_modules` /
  `test_the_detect_and_context_modules_import_no_referee_module` in `test_referee_guards.py` (the
  pattern this iteration's new guard extends).
