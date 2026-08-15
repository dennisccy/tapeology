# Goal Iteration 4 — J-03: fix the exact-mode p-value floor, prove it both directions, close one evaluator-flagged evidence gap

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** referee
- **Iteration:** 4
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — the prior iteration's verdict was `ESCALATE`, which mandates full depth
  this iteration with no exceptions. (Trigger 1 independently also holds, unchanged from
  iteration 3's own justification: `referee_stats.py` is shared statistical architecture that
  J-04–J-08 will all import for their real verdict math, so a subtle correctness bug here would
  pass isolated unit tests while silently invalidating every later verdict — exactly what
  happened last iteration and exactly why the deeper audit/closure lanes matter this time.)
- **Frontend Present:** yes (no frontend code changes this iteration — every target/rider item
  is backend/statistics; browser-qa still runs J-10's regression sentinel every iteration per
  the binding "rides every iteration" note in `iteration-state.md`, matching iter-3's own
  precedent)
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

Fix the statistics engine's exact-enumeration p-value so it can never report a result as more
significant than its own method mathematically allows, prove the fix with new oracle evidence in
BOTH the over-cautious and over-confident directions, re-pin and version the fail-closed
attestation accordingly, and — riding along — close two same-file test gaps the reviewer flagged
plus one evaluator-flagged silent-evidence-drop in the already-shipped readiness fold, so every
later Referee journey (J-04–J-08) builds on a statistics core that is actually proven correct.

## BACKGROUND

**Priority rubric.** Rule 1 (regressed journeys first): nothing regressed at iteration 3 — J-03
moved `failing → partial`, not backwards. Rule 2 (consolidation before features): iteration 3's
`coherence.md` was `COHERENCE-PASS`, not FAIL, so this is not a mandated consolidation pass —
but the evaluator's own `ESCALATE` plays the same forcing role here: fix the found defect before
building anything else on top of it. Rule 3 (unblockers next): J-03 is still the direct,
named dependency every later journey (J-04's test-spec consumption, J-06's three estimand
evaluators, J-08's strategy gate) needs correct, and it is the ONLY thing standing between
`partial` and `passing` — closing it unblocks the rest of the era's dependency chain
(J-01 → J-02 → J-03 → J-04 → …). Rule 4 (smallest spec wins ties): n/a, no tie — J-03 is the
sole, evaluator-named next step. Rule 5 (never bundle two risky journeys): only J-03 is a
**target** journey this iteration; the one evidence-gap rider (below) touches J-01/J-02's
already-shipped surface but is deliberately additive-only and does not re-target either journey.
Rule 6 (don't pick a human-blocked journey): n/a — J-03's fix is buildable today, keyless,
backend-only; the only human-owned item on file (trendora's `:8255` restart) is outside this
project and does not gate it. Rule 7 (no evidence-only iterations): real code and real proof
land this iteration.

**Depth is full, trigger 3 (mandatory).** Per this agent's own binding rule, a prior `ESCALATE`
verdict requires full depth with no exceptions — the evaluator's own depth recommendation for
this iteration is `full`, matching. Checking the other triggers for completeness: trigger 1 also
independently holds (unchanged reasoning from iteration 3 — see metadata above); trigger 2
(data-model migration) does not apply — every change this iteration is additive (new fields,
never a changed computing module or serving endpoint for an already-registered Data-Contract
value); trigger 4 (hardening cadence) is not due on its own (3 of 6 consecutive lean iterations
— though moot here since trigger 3 already mandates full).

**What exactly happened last iteration, and what this iteration must prove.** The evaluator
reproduced a real, provable defect in `permutation_test`'s exact-enumeration branch
(`apps/backend/app/research/referee_stats.py`): the second group's sum is computed by
subtracting the first group's sum from a separately-accumulated session total
(`g2_sum = total - g1_sum`), while `_t_statistic` (the function that computes the OBSERVED
statistic every draw is compared against) sums the same group directly via `math.fsum(group2)`.
The two paths disagree in their last representable digit for non-round decimal inputs, so the
TRUE observed grouping — which must always legitimately count as "at least as extreme as
itself" in exact-enumeration mode — can fail that self-comparison and get silently dropped from
the extreme count. The result: the returned p can fall to HALF of what exact enumeration's own
`p = (1 + #{T* extreme}) / (draws + 1)` formula can legitimately produce (the floor is always
`2 / (draws_used + 1)`, since the observed grouping is one guaranteed member of the enumerated
space). The evaluator reproduced this on 60,000 fresh cases at rates up to 1.72%, always on the
most extreme results — exactly the ones a reader would act on. Nothing is served to any user
yet, so nothing is misleading anyone today, but this module is imported by nothing precisely
because it ships unconsumed — the whole point of fixing it now, before J-04 wires it into real
computation.

**Lessons applied (`lessons.md` iter-3 entry, "Applies to: any iteration touching
`referee_stats.py`").** All three of its rules drive this iteration's scope directly: (1) the
fix makes the OBSERVED/identity case bit-identical between the two summation paths, not merely
"close"; (2) the new oracle-suite case is chosen specifically so it ENTERS the enumeration
branch (small S, decimal fixtures) — closing the exact coverage hole the lesson names ("every
oracle generator uses S≥10 sessions... the enumeration branch is NEVER exercised"); (3) the
existing mutation fixture is paired with a new ANTI-conservative mutant (the pre-fix subtraction
code, which OVER-states significance) alongside the existing over-cautious-only one.

**Riders carried, per iteration 3's own next-step recommendation and the binding "Do not redo"
list.** Two same-file reviewer flags ride along (zero extra blast radius — same file, same
review pass): `_draw_indices_without_replacement` (dead code today) is KEPT, not deleted — its
own docstring already frames it as the canonical without-replacement primitive
(`desk_forward._draw_anchor_indices`'s matched idiom) J-04's real anchor draws are the most
likely future caller of, so deleting it now would just mean re-adding it next iteration — and it
gains the direct test coverage the reviewer asked for instead. The untested `n1>1, n2==1` seeded
fast path (a realistic future shape per spec Sec4.1's anchor-shortfall disclosure) gains a
from-scratch reference test, mirroring the existing `n1==1` case the reviewer already
hand-verified.

**The "two leads" rider — one closed, one deliberately dropped.** Iteration 3's evaluator also
asked for "a check of two leads in older unchanged code... both would matter to J-06," phrased
as something that should "ride along... rather than becoming its own iteration." Both were
traced to a concrete root cause this iteration (not left as vague leads):

- **Lead 1 (closed this iteration).** `playbook_occurrence_readiness()` (J-01's own function,
  served today at `GET /research/desk/referee/evidence`) and `playbook_observations()` (J-02's
  adapter) each independently implement the SAME check — a date whose newest Playbook record's
  `(detector_basis, config_fingerprint)` does not match the LIVE values contributes zero to that
  date's counted/served evidence — with no disclosure of which date, or why. On today's real
  corpus this never fires (no detector revision has happened this era — the frozen research
  vocabulary is unchanged), so this is a forward-looking safety net, free to add now while
  nothing consumes it, exactly like iteration 3's own "re-pin now, it's free" reasoning for the
  attestation. Fixed additively: a new `stale_basis_dates` disclosure, built by ONE shared helper
  both functions call (reducing, not adding to, the pre-existing duplication of this check —
  serves anti-goal 6 directly).
- **Lead 2 (dropped, per T-1 — "an ambiguous or unimplementable clause is DROPPED and surfaced
  for an owner ruling, never improvised").** `_strategy_observation()`'s
  `epoch_anchor = dataset.get("epoch_anchor") or 0.0` was investigated as a candidate "missing
  time anchor fabricates a ~1969 date" fix. It is real, but far more entangled than a small
  check: the IDENTICAL `or 0.0` pattern is already-shipped, FROZEN behavior in
  `edge_report.py:489` (this era must not touch it — Foundation invariant #2 names
  `edge_report*.py` byte-identical), and the shared test fixture `_plant_dataset` (used across
  every `strategy_observations()` test) deliberately sets `epoch_anchor=0.0` as a real,
  hand-verified value — `test_strategy_observations_emits_net_r_with_the_forming_bar_caveat`'s
  own comment proves the resulting `"1969-12-31"` `session_date` is an INTENTIONAL, checked
  assertion (proving accurate ET day-boundary conversion), not a bug demonstration. A correct
  fix must distinguish a genuinely-missing/`None` anchor from an explicitly-present `0.0` one
  (the current `or` truthy check conflates them) — see NOTES for the full investigation and the
  fresh `state/assumptions.md` entry. Not attempted this iteration; surfaced for whoever next
  touches `referee_evidence.py`'s strategy adapter (naturally, J-06, its first real caller).

## IN SCOPE

### Backend

- [ ] Fix `permutation_test`'s exact-enumeration branch (`referee_stats.py`, the
  `g2_sum = total - g1_sum` step) so the returned `p` can never fall below the exact mode's own
  mathematical floor `2 / (draws_used + 1)`: compute each enumerated combination's group-2 sum
  the SAME way `_t_statistic` computes it for the observed grouping — a direct accumulation over
  that combination's own complement values — never by subtracting from a separately-accumulated
  session total. Zero change to the seeded (non-enumeration) `b`-draws branch — see OUT OF SCOPE
  for why it does not share this defect.
- [ ] Add the regression + property proof, in `apps/backend/tests/test_referee_stats.py`:
  - The evaluator's exact minimal reproduction (`g1=[0.9571299431380904,
    0.23675146939940733]`, `g2=[-0.2015364333714562, -0.47887435876092443]`, one session,
    `sidedness="greater"`) now returns the correct floor value, not the previously-served
    under-floor one.
  - A property test across many freshly seeded-generated small enumeration-mode fixtures
    (2-vs-2 and 1-vs-4 shapes, matching the evaluator's own reproduction shapes) asserting `p`
    never falls below `2 / (draws_used + 1)` across all three `sidedness` values, for a
    generated set at least as large as the evaluator's own reproduction (thousands of cases).
- [ ] Extend `apps/backend/tests/test_referee_oracles.py` so the oracle suite itself — the thing
  J-03's acceptance names as "IS the acceptance" — genuinely exercises the enumeration branch
  (closing the exact coverage hole `lessons.md`'s iter-3 entry names): a calibration case with S
  small enough that its permutation space stays at or under `REFEREE_ENUMERATION_THRESHOLD`
  (8,192), built from non-round decimal values (not integers, not values like `5.0`/`1.0`/`2.0`
  that float arithmetic stores exactly), checked for both the floor property AND empirical
  calibration within `REFEREE_ORACLE_SIZE_TOLERANCE`. Extend the existing mutation-fixture
  test with a SECOND, paired mutant that reproduces the PRE-FIX subtraction-based computation —
  proving the suite catches an over-confident (anti-conservative) implementation bug, not only
  the existing over-cautious one.
- [ ] Re-capture `_ATTESTATION_EXPECTED`/`_ATTESTATION_TOLERANCE` by running
  `run_oracle_attestation()` against the FIXED code and hardcoding the fresh result (the
  currently-pinned values were captured against the buggy build and may no longer match); bump
  `STATS_CORE_VERSION` from `"referee-stats-v1"` to `"referee-stats-v2"` — the module's own
  docstring already frames this exact scenario ("bumped only on a genuine algorithmic revision
  to this file... a named revision, never silently"). Add a test asserting
  `verify_oracle_attestation()` rejects an attestation whose `stats_core_version` reads the OLD
  `"referee-stats-v1"` string as version-stale, even when every other field matches the new pin.
- [ ] Close the two reviewer-flagged gaps in the same file (`test_referee_stats.py`): direct
  test coverage for `_draw_indices_without_replacement` (KEEP the function — do not delete; it
  is the documented without-replacement primitive J-04's anchor draws are expected to reuse) —
  deterministic under identical seeded streams, returns `k` distinct sorted indices in
  `range(population)`; and a fixture with `n1 > 1, n2 == 1` inside `permutation_test`'s seeded
  branch, asserted against a from-scratch general-algorithm reference (mirroring the existing
  `n1 == 1` case the reviewer already hand-verified).
- [ ] Close Lead 1 in `apps/backend/app/research/referee_evidence.py`, additive-only, zero
  change to any currently-served field's VALUE: one shared helper (called by both
  `playbook_occurrence_readiness()` and `playbook_observations()`, replacing their two
  independent copies of the SAME `(detector_basis, config_fingerprint)` match check) discloses
  `stale_basis_dates: [{"session_date": str, "record_detector_basis": str}]` for any date whose
  newest record does not match the live values, instead of the record silently contributing
  nothing. Extend the EXISTING fixture in
  `test_playbook_readiness_pools_newest_per_date_at_the_current_basis` (its "Date D3: a
  STALE-basis record" case already constructs exactly this scenario) with the new assertion, and
  add one sibling test for `playbook_observations()` alongside
  `test_playbook_observations_dedup_selects_newest_and_discloses_coverage_shrink`.
- [ ] Zero new `Config` fields; zero diff to `desk_playbook*.py`, `desk_forward.py`, `levels.py`,
  `tradability.py`, `setups.py`, `edge_report*.py`, `backtests.py`, `pnl_scan.py`,
  `app/config.py`, `app/main.py`, any route file, and `docs/referee-statistical-spec.md` (this
  fix makes the implementation match the spec's already-stated formula-level definition — it
  does not reinterpret or re-derive anything the spec defines, so no spec text changes).

### Frontend

- (none — every item this iteration is backend-only; J-03 is `(Keyless; automated.)` and Lead 1's
  fix touches a route J-09, several iterations away, first surfaces)

### New user-facing capability

None yet. `referee_stats.py` remains unconsumed by any route, page, or MCP tool. Lead 1's new
field is served but rendered nowhere.

### New information displayed

None (no UI change this iteration).

### New user actions

None.

### UI surface changes

None.

### Product surface delta

None visible in the UI this iteration. `referee_stats.py`'s primary confirmatory test becomes
provably floor-safe in exact mode, with oracle evidence in both directions; `referee_evidence.py`
gains one honest disclosure field on its already-shipped readiness fold and observation adapter.

### Blueprint conformance

No new page. `state/blueprint.md`'s existing IA row ("J-01 per-family readiness fold... | `GET
/research/desk/referee/evidence` | Desk" and "J-02 evidence contract, J-03 stats core (library
modules, no page of their own) | n/a — consumed by J-04–J-09 | —") already covers every module
this iteration touches; unchanged. The Data Contract row for "Referee evidence coverage +
per-family readiness" gains a documentation note for the one new additive field (see
Data-contract additions below) — edited into `blueprint.md` this iteration, purely additive, no
re-approval needed (no nav-skeleton change).

### Data-contract additions

One new served (not yet UI-displayed — J-09 is the first UI consumer, several iterations away)
field on the ALREADY-registered "Referee evidence coverage + per-family readiness" row, owned by
`app/research/referee_evidence.py`:

- `stale_basis_dates: list[{"session_date": str, "record_detector_basis": str}]` — every date
  whose newest Playbook record's own `(detector_basis, config_fingerprint)` does not match the
  live values, disclosed instead of silently contributing zero. Served on BOTH
  `playbook_occurrence_readiness()`'s response (live today at `GET
  /research/desk/referee/evidence`'s `playbook_occurrence` block, J-01) and
  `playbook_observations()`'s response (unconsumed by any route this iteration, J-02), computed
  by one shared helper both call.

This field does not change the value of any field already served today; it is empty (`[]`) on
every fixture — including the real production store — that has no stale-basis record (which
today's real corpus is expected to be, since no detector revision has happened this era).

## OUT OF SCOPE

- J-04's matched nulls, J-05's registry, J-06's estimand engines/adjudication, J-07's
  shortlist/registration UI, J-08's promotion interlock, J-09's `/desk` sections and the two new
  MCP tools — `referee_stats.py`/`referee_evidence.py`'s outputs get no caller this iteration;
  zero frontend, zero MCP diff (`EXPECTED_TOOLS` stays the existing 20-tuple).
- The seeded (non-enumeration) `b`-draws branch's own `g2_sum = total - g1_sum` step. It is
  mathematically benign at Monte-Carlo scale: its floating-point disagreement (~1 ULP per draw)
  is many orders of magnitude below the sampling error of `REFEREE_B` (10,000) seeded random
  draws, and — unlike the enumeration branch — it never needs the observed grouping to
  bit-match itself (the `p = (1 + extreme) / (b + 1)` formula's "+1" already accounts for the
  observed result unconditionally, regardless of whether it is ever drawn). The evaluator's
  finding and fix are scoped to the exact-enumeration branch only.
- **Lead 2 — the strategy adapter's `epoch_anchor` fallback.** Explicitly dropped this iteration
  per T-1 (see BACKGROUND and the fresh `state/assumptions.md` entry). Do not touch
  `_strategy_observation()`, `strategy_observations()`, or `edge_report.py` (frozen, out of
  inventory regardless).
- Rewriting `referee_stats.py` or re-deriving any of its already-shipped constants from the
  spec — the binding "Do not redo" list is explicit: fix the enumeration branch and its oracle
  gap, nothing else.
- Any change to `docs/referee-statistical-spec.md` — the fix is implementation-fidelity, not a
  spec reinterpretation.
- Redesigning or re-keying `playbook_occurrence_readiness()`/`playbook_observations()` beyond the
  one named additive field — no change to any currently-served field's computation or value; the
  shared helper factors out existing duplicated logic, it does not change what that logic
  decides.
- Any real registration, evaluation, or null-build operator act — none of that machinery exists
  yet.
- Pattern-based process kills (`pkill -f` or similar) for dev-server cleanup — exact-PID
  process-tree kill only (iter-2 lesson: a pattern-based kill took down an unrelated project's
  backend and it is still down). No action on trendora's `:8255` restart — human-owned, outside
  this project, does not block this iteration.
- Re-verifying or re-scoring J-01 or J-02 as TARGET journeys — only J-03 is targeted. Both ride
  along as Required-still-passing precisely because Lead 1 touches their already-shipped
  functions; every currently-served field/value on both must stay byte-identical except the one
  new additive field, matching the exact "extend, never mutate" discipline iteration 1's
  `integrity_errors` rider and iteration 3's own two `referee_evidence.py`-test riders already
  established for this pair of journeys.

## DEFINITION OF DONE

- [ ] Target journey J-03 passes: the exact-enumeration floor guarantee is proven on the
  evaluator's own minimal repro AND a broad generated property set (TC-1, TC-2); the oracle
  suite gains a case that genuinely enters the enumeration branch and a paired
  anti-conservative mutant, both green (TC-3, TC-4); the attestation is re-pinned and
  version-bumped, round-trips, and rejects the old version string as version-stale (TC-5, TC-6); the
  two reviewer-flagged same-file gaps are closed (TC-7, TC-8). Reviewer and evaluator each
  independently re-run the suite and hand-check the new fixtures' expected values are
  independently derived, not copied from the implementation under test.
- [ ] Lead 1 is closed additively, verified on both call sites (TC-9, TC-10); Lead 2 is
  explicitly NOT touched (confirmed by zero diff to `_strategy_observation`/
  `strategy_observations`/`edge_report.py`).
- [ ] Required-still-passing journeys J-01 and J-02 remain green: every existing fixture
  assertion in `tests/test_referee_evidence.py` still passes, unmodified except the one named
  extension and one new sibling test (TC-13); the response shapes are byte-identical to
  iteration 3's recorded shape plus exactly the one new additive field at its empty-list default
  on every fixture that triggers no exclusion.
- [ ] Required-still-passing journey J-10 remains green (TC-15).
- [ ] No anti-goal violation introduced: `Config().config_fingerprint()` still prints
  `08e471b10130e1e2`; zero diff to every named frozen module; zero new `Config` fields; zero new
  runtime dependency; MCP still advertises exactly 20 tools; the `referee_stats.py` import-ban
  guard (from iteration 3) still passes unmodified (TC-14); zero writes to any pre-existing store
  file (SHA-256 listing unchanged — this iteration's changes still write to no store at all).
- [ ] Unit tests pass; full backend suite ≥ 2,495 pass / 8 skip (iteration 3's recorded floor);
  no regressions (TC-11, TC-12).
- [ ] Dev handoff written at `docs/handoffs/goal-referee-iter-4-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-10 only (regression sentinel — cockpit `/`, `/structure` AAPL Load, every shipped
  `/desk` section). Neither J-03 nor Lead 1 has a live endpoint to smoke beyond the existing
  pytest-covered `GET /research/desk/referee/evidence` route (J-01, already keyless/automated
  per `lessons.md`'s iter-1 entry — no golden replay script can exist for it).
- Unit/integration: `tests/test_referee_stats.py` gains the minimal-repro regression test, the
  floor-guarantee property test, and the two reviewer-flagged-gap tests; `tests/test_referee_oracles.py`
  gains one enumeration-branch calibration case and one paired anti-conservative mutant, whole
  suite still completing within `REFEREE_ORACLE_BUDGET_SECONDS` (120s); `tests/test_referee_evidence.py`
  gains the `stale_basis_dates` assertion on its existing D3 fixture plus one new sibling test for
  `playbook_observations()`; the full existing suite stays green at ≥ 2,495 pass / 8 skip.
- Error cases: an attestation record whose `stats_core_version` is stale (the old
  `"referee-stats-v1"` string) must be DETECTED and rejected, never silently accepted; the
  anti-conservative mutant fixture must be DETECTED as miscalibrated/floor-violating, never pass
  by coincidence; the floor-guarantee property test must find ZERO violations across its full
  generated set.

Test-first contract:

- TC-1: given the evaluator's exact minimal-reproduction fixture (`g1=[0.9571299431380904,
  0.23675146939940733]`, `g2=[-0.2015364333714562, -0.47887435876092443]`, one session,
  `hypothesis_id="probe"`, `sidedness="greater"`), when `permutation_test` runs post-fix, then
  `result["p"] == 2/7` (`0.2857142857142857`), not the previously-served `1/7`.
- TC-2: given a freshly seeded-generated set of at least several thousand small enumeration-mode
  fixtures spanning 2-vs-2 and 1-vs-4 group-size shapes (matching the evaluator's own
  reproduction shapes) across `"greater"`, `"less"`, and `"two-sided"` sidedness, when
  `permutation_test` runs on each, then every returned `p >= 2 / (draws_used + 1)` — zero
  violations across the entire generated set.
- TC-3: given a new oracle-suite calibration case whose total within-session permutation space
  is at or under `REFEREE_ENUMERATION_THRESHOLD` (8,192) and whose fixture values are non-round
  decimals, when the seeded simulation runs, then `permutation_test["enumeration"] is True` for
  every replication, the empirical rejection rate falls inside `REFEREE_ORACLE_SIZE_TOLERANCE`,
  and no single replication's `p` falls below its own `2 / (draws_used + 1)` floor.
- TC-4: given a second, paired mutant of the mutation-fixture test that reproduces the PRE-FIX
  subtraction-based group-2 sum (the anti-conservative direction), when it is run against the
  same calibration case, then it is DETECTED — either its empirical rejection rate falls outside
  `REFEREE_ORACLE_SIZE_TOLERANCE` or it produces at least one `p` below the exact floor on the
  TC-1/TC-2 style fixtures — proving the suite catches an over-confident implementation bug, not
  only an over-cautious one.
- TC-5: given the fixed code, when `run_oracle_attestation()` runs, then it returns
  `{expected, actual, tolerance, passed=True, stats_core_version="referee-stats-v2"}` with
  `expected`/`tolerance` freshly re-captured from the fixed build (not the pre-fix values); given
  two independent calls, both return byte-identical `actual` values.
- TC-6: given an attestation record identical to the new pin except `stats_core_version` reads
  the OLD string `"referee-stats-v1"`, when `verify_oracle_attestation()` checks it, then it
  returns `False` (version-stale rejection).
- TC-7: given a seeded stream and `population=7, k=3`, when `_draw_indices_without_replacement`
  is called twice with two independently-constructed but identically-seeded `random.Random`
  instances, then both calls return the same sorted 3-element list of distinct indices in
  `range(7)`; given `k == population`, the same function returns every index exactly once.
- TC-8: given a fixture with `n1 = 3, n2 = 1` inside `permutation_test`'s seeded (non-enumeration)
  branch, when the `elif n2 == 1` fast path executes, then its result matches a from-scratch
  general-algorithm reference computed independently in the test.
- TC-9: given `test_playbook_readiness_pools_newest_per_date_at_the_current_basis`'s existing
  Date-D3 stale-basis fixture (`session_date="2026-06-10"`, `stale_parameters`), when `GET
  /research/desk/referee/evidence` is called, then `occurrence["stale_basis_dates"]` contains
  exactly one entry for `"2026-06-10"` with its own `record_detector_basis`, while every
  currently-asserted field in that same test (`records == 4`, `distinct_sessions == 3`,
  `signals_at_current_basis == 5`, `per_setup_side`) keeps its existing value unchanged.
- TC-10: given an equivalent fixture (one live-basis date, one stale-basis date) passed to
  `playbook_observations()`, when it runs, then `result["stale_basis_dates"]` discloses the
  stale date with zero change to `observations`, `coverage_by_date`,
  `coverage_shrink_disclosures`, or `session_completeness`.
- TC-11: given the complete iteration diff, when the full backend suite runs, then it reports
  pass/skip counts each ≥ 2,495 pass / 8 skip with zero errors, and
  `Config().config_fingerprint()` still prints `08e471b10130e1e2`.
- TC-12: given this iteration's complete diff, when `tests/test_mcp_server.py::EXPECTED_TOOLS` is
  inspected and a SHA-256 listing of every pre-existing playbook/dataset/journal store file is
  taken before and after the diff, then `EXPECTED_TOOLS` still has exactly 20 entries and the two
  listings are byte-identical.
- TC-13: given `tests/test_referee_evidence.py`'s full existing test file, when it is re-run
  after this iteration's diff, then every pre-existing test passes with its ORIGINAL assertions
  unchanged, except the single named extension in TC-9 and the single new sibling test in TC-10.
- TC-14: given `referee_stats.py` after this iteration's diff, when the existing
  `test_referee_stats_module_imports_none_of_the_banned_rail_detector_context_modules` guard (and
  its own can-fail counter-test) from iteration 3 runs, then both still pass unmodified.
- TC-15: given the T-9 clean rebuild (`rm -rf apps/frontend/.next`, rebuild, restart), when J-10's
  regression walk runs (deterministic replay of the stored golden where it applies, else the LLM
  browser-qa fallback), then the cockpit sim tape/chart, `/structure`'s pinned-AAPL Load, and
  every shipped `/desk` section render exactly as shipped, each evidenced by a screenshot.

## NOTES

- **Anchors, re-located by symbol name (never line arithmetic — per this project's own build-anchor
  discipline; iteration 3's eval.md cited `:424`/`:454` and this iteration's own investigation
  found the live file's `_t_statistic` fsum(group2) at a DIFFERENT line, `:239`, confirming line
  numbers drift and must not be trusted verbatim):** `permutation_test`'s exact-enumeration
  branch — the `g1_sum = math.fsum(...)` / `g2_sum = total - g1_sum` pair inside the
  `if use_enumeration:` block; `_t_statistic`'s own `math.fsum(group1) / n1 - math.fsum(group2) /
  n2`; `_is_extreme`; `_ATTESTATION_EXPECTED`/`_ATTESTATION_TOLERANCE`/`_ATTESTATION_SESSION_GROUPS`;
  `STATS_CORE_VERSION`; `verify_oracle_attestation`; `_draw_indices_without_replacement`. In
  `referee_evidence.py`: `playbook_occurrence_readiness`, `playbook_observations`,
  `_newest_per_session_date`, `_record_detector_basis`, `current_playbook_detector_basis`.
- **Lead 2, full investigation record (for whoever next touches the strategy adapter — likely
  J-06, its first real caller).** `_strategy_observation()`'s
  `epoch_anchor = dataset.get("epoch_anchor") or 0.0` conflates "genuinely missing/`None`" with
  "explicitly `0.0`" because `or` treats both as falsy. `DatasetStore.record()`
  (`apps/backend/app/research/datasets.py`) requires `epoch_anchor: float | None` as a
  mandatory keyword — the key is therefore ALWAYS present on a real registered dataset, but its
  value legitimately can be `None` (`providers/historical.py`'s `min(epochs) if epochs else
  None`; `providers/live.py`'s `None` until the first record). The identical `or 0.0` pattern is
  already-shipped in `edge_report.py:489`, which this era's Foundation invariants list as frozen
  and byte-identical — it is NOT a target for this era regardless. Its consequence there is
  low (a sort-key perturbation within one `(strategy_id, band_class, band_side, reaction, feed)`
  pool, never a cross-pool grouping), which is plausibly why it was never flagged before; the
  Referee's copy is higher-consequence because it feeds `session_date`, which directly
  participates in `permutation_test`'s within-session exchangeability grouping. The widely-reused
  test fixture `_plant_dataset` sets `epoch_anchor=0.0` deliberately, and
  `test_strategy_observations_emits_net_r_with_the_forming_bar_caveat`'s own comment
  hand-verifies the resulting `session_date == "1969-12-31"` as a REAL, checked assertion (proof
  the ET conversion crosses a day boundary rather than a UTC passthrough) — not a bug
  demonstration. A future
  fix must check `"epoch_anchor" in dataset and dataset["epoch_anchor"] is not None` (or
  equivalent), never a truthy `or`, so `0.0` keeps being honored as a legitimate explicit value
  while `None`/missing gets excluded and counted instead of defaulted. Whether
  `referee_evidence.py` should match or intentionally diverge from `edge_report.py`'s convention
  is a project-wide consistency question, not a Referee-only one — flagged, not decided, here.
- **Assumption ledger entry added this iteration** (`state/assumptions.md`, `## iter-4 —
  goal-decomposer`): records the "ride along vs. investigate only" reading of iteration 3's
  next-step recommendation, and the Lead 2 drop with its full reasoning. Reversible.
- Per the binding "Do not redo" list: `referee_stats.py` "exists and mostly works — fix the
  enumeration branch + its oracle gap; do NOT rewrite the module or re-derive its constants from
  the spec." This iteration's scope is exactly that fix plus the oracle gap it names, plus the
  two same-file riders and Lead 1 the evaluator explicitly asked to carry alongside it.
- Traps most relevant this iteration (`docs/goal.md` § Build anchors & weak-model traps): **T-1**
  (the spec is law — Lead 2 is dropped and surfaced per this exact rule, not improvised); **T-3**
  (CI-inversion is not a p-value — unaffected by this fix, restated for salience since this
  iteration touches the ONE function that produces the confirmatory p); **T-6** (the corpus moves
  daily — Lead 1's disclosure is the mechanism that will make a future detector revision's effect
  on readiness counts honest instead of silent); **T-8** (fail closed — TC-6 extends the
  version-stale half of this discipline the version bump newly makes real).
