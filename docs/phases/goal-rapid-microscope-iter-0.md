# Goal Iteration 0 — Baseline: verify all ten Rapid-Microscope journeys against current state

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10
- **Required-still-passing journeys:** None — first iteration of this session; no journey has
  been verified yet in `journey-history.json`.
- **Anti-goal reminders:**
  - *Immutable rails (critical; "only ever grow more specific, never weaker"):*
    1. No execution path, ever — no brokerage/trading API, no order tickets, no live OR paper
       trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py`
       is the tier-1 guard; new research code adds matching guard tests, never weakens them.)
    2. No profit claims and no advice — every $ figure is a simulated measurement carrying R,
       n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction
       language, no imperative trading cues.
    3. Frozen foundations — the `v1` strategy, the `default` profile, the tape engine's five
       states and thresholds, the frozen structure computations, the JSON `BarStore`, and
       every KEPT surface's behaviour stay byte-identical. New work is additive and versioned
       beside them, never a mutation of them.
    4. Hold-out-only promotion — the champion pointer moves only on a genuine hold-out
       survival through the sweep gate PLUS a valid Referee certificate. Train-only wins are
       labeled overfit. Never lower a minimum sample size, widen a gate, or pool across
       feeds/fingerprints to manufacture a survivor.
    5. No lookahead — every value computed as-of T uses only events/bars fully completed at T.
    6. Single source of truth — each shared value is computed once, owned by one canonical
       endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor
       hard-fails violations.
    7. Deterministic and seeded — every random draw uses a recorded named seed via per-row
       streams; identical requests reproduce byte-identical results; no wall-clock, no
       unseeded randomness in any research artifact.
    8. Read-only MCP — MCP tools remain byte-identical proxies of GET endpoints; nothing on
       the MCP surface can change state.
    9. Immutable data — registered datasets and bar series are append-only, checksummed,
       never re-tagged, never deleted, never content-perturbed. Splits are frozen at
       registration.
    10. Persistence stays scoped — no ambient recording of live streams; recording/fetching
        is an explicit, logged act.
  - *Era-B/B2 anti-goals (still binding):* membership is never a signal; snapshots and
    playbook records are append-only and pinned; every run is an explicit operator act; the
    briefing and the playbook describe, never advise; the demolition stays demolished; the
    ledger never holds orders; the suite stays keyless and hermetic; the fingerprint pin does
    not move; no threshold exists outside its spec and no code path sweeps one; the evidence
    pools one signature; no recorded playbook file is ever rewritten; no second implementation
    of the measurement rail.
  - *Referee-era anti-goals (still binding):* no confirmatory claim outside the gauntlet; the
    historical atlas is exploratory forever; CI-inversion is never a p-value; never shrink the
    BH denominator; no gate loosens mid-era; the Referee never feeds back; promotion is
    certificate-locked with no bypass; no confirmatory output without a verified oracle
    attestation; no annualized metrics anywhere.
  - *Rapid-Microscope anti-goals (added, not weakening any rail above):*
    - No exploratory read of a sealed shard. Event data and outcome aggregates of a `sealed`
      shard are refused everywhere (routes, MCP, accessor, readiness) until its recorded
      exposure; the refusal is typed, tested, and fail-closed.
    - Sealed exposure is family-level and single-shot — never a second draw. No more than one
      evaluation per (family, shard) exists, ever; a failed sealed verdict is permanent and
      travels in every later export bundle; no perturbed re-submission resets it.
    - Evidence classes never mix. No `historical_exposed_diagnostic` output feeds a gate, a
      graduation transition, a certificate, a promotion, or a pooled statistic with
      `historical_oos` rows; nothing in this era emits `live_confirmatory`.
    - No fold geometry change after fold 1 without a recorded voiding event that clears every
      survivor state of that corpus-era.
    - No threshold, grid, formula, embargo, or fold parameter is chosen or revised from
      validation, sealed, or holdout outcomes. Fitting rules are data functionals frozen
      before reveal; per-origin refits under an unchanged rule are provenance, never a new
      choice.
    - The denominator never shrinks. Every evaluated variant lands in the hash-chained ledger
      with a closed-vocabulary decision; kills are never deleted; the union-N across grid
      versions is served beside every family.
    - The accessor is the only data door. No module but `micro_accessor.py` opens snapshot or
      vault event data; origin fences fail closed; import-ban and source-scan guards enforce
      it.
    - No microstructure claim beyond what L1 supports. `refill_consistent` is the strongest
      liquidity label; "iceberg", institutional-intent, and manipulation language are banned;
      every aggressor-derived quantity is served beside its `fallback_frac` and
      `unknown_frac`.
    - No sub-second outcome horizon and no latency-sensitive mechanism, per DO-NOT #1.
    - No cross-unit liquidity arithmetic. No feature, screen, or study relates trade shares to
      displayed quote sizes unless the dataset's `quote_size_unit` is verified (spec §2.6);
      unverified or mixed units are a typed refusal; unit normalization exists only as a
      recorded verification act, never silent arithmetic.
    - No value is served before it exists. Every feature carries
      `anchor_at`/`observed_through`/`available_at`; a deferred construct is `unavailable`
      until its observations exist; no outcome for a conditioned anchor begins before the
      conditioning set's maximum `available_at` (TR-17).
    - The 12 pre-existing tick symbol-days are permanently exploratory — never sealed, never
      `historical_oos`, never relabeled.
    - The ~150-symbol-day research-readiness gate is never lowered or silently satisfied; any
      claim whose predeclared floor is unmet fails closed with the floor arithmetic served.
    - Referee modules are byte-untouched this era — `referee_handoff_ready` never implies
      current-Referee registrability of a flow predicate; that awaits a future named revision
      of the referee spec.
    - The vault secret never enters the repo, a log, a payload, or a screenshot — only its
      sha256 commitment is ever recorded.
    - The enhancement loop stays inside its box. The goal-proposer may append journeys ONLY
      inside the `AUTO:journeys` marker block of `docs/goal.md` — it MUST NOT edit
      human-authored journeys, the Anti-goals section, or any other part of that file;
      proposed journeys MUST carry a single-source-of-truth acceptance criterion, keep the
      `default` profile and `v1` byte-identical, respect every rail above, and include a
      `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just to keep the loop
      alive is a failure.
  - *Host protection (carried verbatim — a physical constraint of the host, not product
    scope):* Host-guard caps are law. This host (GEEKOM A7 Max mini-PC) hard-reset five times
    between 2026-07-20 and 2026-07-28 under unconfined goal-mode load. When
    `project-extensions/host-guard/host-guard.env` declares ceilings (CPU mask `4-7,12-15`
    plus BLAS thread caps and memory/task bounds), every heavy path respects them; the engine
    pauses `AWAITING_HOST_GUARD` (resumable) only when confinement cannot be established.
    Never disable, widen, or bypass these caps to make a run faster or a pause go away.

## GOAL

Establish the honest baseline for the newly opened "Rapid Microscope" era: verify, with zero
code changes, the current pass/partial/failing state of all ten Must-have journeys (J-01–J-10)
against the existing codebase and running product, and record the era-open reference metrics
(backend suite count, fingerprint, referee-module SHA-256 listing), so every later iteration
builds on a truthful starting point.

## BACKGROUND

This is iteration 0 of the newly opened `rapid-microscope` session, dispatched immediately
after Era 6 "The Referee" reached `GOAL_ACHIEVED` (2026-08-16). A codebase scan for this
baseline confirms the era-transition documents already exist on `main`
(`docs/goal-archive/goal-2026-08-16.md`, `docs/rapid-validation-spec.md`, the
`docs/research-directions.md` rapid-microscope amendments, and the
`project-extensions/proposer-guidance.md` §5.3 amendments) — so J-01's transition-artifact
sub-check is expected to verify true. However, none of this era's core deliverable modules
(`micro_readiness.py`, `micro_observer.py`, `micro_snapshots.py`, `micro_features.py`,
`micro_join.py`, `scout.py`/`scout_ledger.py`, `micro_accessor.py`/`walkforward.py`,
`tick_recorder.py`/`vault.py`, `micro_graduation.py`) exist anywhere under
`apps/backend/app/` yet, so J-01's readiness endpoint/UI sub-checks and all of J-02 through
J-09 are expected to register FAILING at this snapshot. J-10's "kept product stands" sentinel
targets EXISTING shipped surfaces (cockpit `/`, `/structure`, and `/desk`'s Playbook /
band-context / cohort / Referee Registry-Adjudications-Runs sections) that have not changed
since Era 6 closed, so its sentinel component should largely verify true — but J-10's full
acceptance also needs the NEW TR-1…TR-22 trap suite and the deterministic-rerun check, neither
of which exists yet, so its overall verdict is expected to land PARTIAL at best. No
`lessons.md` or `assumptions.md` entries exist yet (this is genuinely the first iteration) and
there is no prior evaluator verdict to react to. Depth is `lean` per both the mandatory
baseline-mode rule and the evaluator's binding recommendation; no full trigger applies because
this iteration touches zero source files. Target-selection rule 1-7 of the priority rubric do
not apply in baseline mode — ALL Must-have journeys are targeted per the explicit Baseline mode
override in the agent instructions, not a rubric pick.

## IN SCOPE

### Backend
- None — verify-only baseline iteration; no code changes.

### Frontend
- None — verify-only baseline iteration; no code changes.

### New user-facing capability
None — this iteration only observes and records existing state; it delivers no new capability.

### New information displayed
None — no UI changes. (The blueprint at
`runs/goal-session-rapid-microscope/state/blueprint.md`, drafted this iteration, records where
this era's future NEW values will eventually be displayed — see Blueprint conformance below.)

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — the product surface is unchanged by this iteration. Its only artifacts are: (1) this
spec, (2) the coherence blueprint, (3) recorded journey verdicts in `journey-history.json`
(written by the evaluator, not this iteration), and (4) the iteration-0 dev handoff carrying
the recorded baseline metrics.

### Blueprint conformance
This iteration DRAFTS the blueprint itself
(`runs/goal-session-rapid-microscope/state/blueprint.md`) rather than conforming to a
pre-existing one — there is no prior blueprint for this session. The drafted blueprint carries
forward the unchanged nav/IA from prior eras (Cockpit `/` · Structure `/structure` · Desk
`/desk`) and registers this era's seven planned NEW Data-Contract rows (verbatim from
`docs/goal.md` §Product Shape) as the target contract for J-01–J-08's future builds. No page
is built this iteration, so there is no conformance check to perform yet.

### Data-contract additions
None this iteration — no code is written, so no new displayed value exists yet. The seven
values this era will eventually add (corpus readiness truth, snapshot metadata, scout ledger,
walk-forward ledger, vault ledger, recorder runs, graduation states) are pre-registered in the
blueprint's Data Contract table so future iterations build directly into that contract rather
than inventing a competing shape.

## OUT OF SCOPE

- Any implementation of `micro_readiness.py`, `micro_observer.py`, `micro_snapshots.py`,
  `micro_features.py`, `micro_join.py`, `scout.py`, `scout_ledger.py`, `micro_accessor.py`,
  `walkforward.py`, `tick_recorder.py`, `vault.py`, or `micro_graduation.py`, or any of the
  seven new `/research/desk/micro/*` endpoints — that is J-01 through J-09's work in later
  iterations.
- The additive `observer=` kwarg on `DatasetStore.replay`, or any `TapeEngine.add_observer`
  wiring (J-02's work).
- The Card-5.1 preservation-field prerequisite (`conditions`/`exchange` on
  `RawTrade`/`RawQuote`/`TradeEvent`/`QuoteEvent`) (J-06 step 1's work).
- Any operator-gated act: universe registration, real-Alpaca recorder runs, vault sealing or
  exposure (J-06's work — explicitly an operator act inside a later iteration, never this one).
- New `/desk` sections or MCP tool additions (J-08's work) — the MCP surface stays at its
  current 22 tools this iteration.
- The three pilot studies (J-09) and the graduation fixture walk (J-07).
- The TR-1…TR-22 leakage-trap suite and the deterministic-rerun check (J-10's remaining work
  beyond this iteration's sentinel-only verification).
- Any fix to a discovered gap, failing test, or missing module. Baseline only RECORDS current
  state; it never remediates.
- Any edit to `docs/goal.md`, `docs/rapid-validation-spec.md`, or
  `project-extensions/proposer-guidance.md`.

## DEFINITION OF DONE

- [ ] J-01 verified against the current repo/backend/UI; a verdict (passing/partial/failing) is
      recorded with cited sub-check evidence (transition artifacts; `GET
      /research/desk/micro/readiness`; the `/desk` Microscope Readiness section).
- [ ] J-02 verified; verdict recorded citing presence/absence of the `observer=` seam,
      `micro_observer.py`/`micro_snapshots.py`/`micro_features.py`, and the snapshots endpoint.
- [ ] J-03 verified; verdict recorded citing presence/absence of `micro_join.py` and any
      joinable-corpus count reporting.
- [ ] J-04 verified; verdict recorded citing presence/absence of `scout.py`/`scout_ledger.py`
      and the scout endpoint.
- [ ] J-05 verified; verdict recorded citing presence/absence of
      `micro_accessor.py`/`walkforward.py` and the walkforward endpoint.
- [ ] J-06 verified; verdict recorded citing presence/absence of `tick_recorder.py`/`vault.py`
      and the vault endpoint.
- [ ] J-07 verified; verdict recorded citing presence/absence of `micro_graduation.py`.
- [ ] J-08 verified; verdict recorded citing which of the four new `/desk` sections exist and
      the current MCP tool count (22 vs. the target 26).
- [ ] J-09 verified; verdict recorded citing presence/absence of any ledgered pilot-study
      specs.
- [ ] J-10 verified; verdict recorded citing the backend suite pass/skip count, the fingerprint
      value, and screenshot/element-capture evidence for cockpit/structure/desk kept surfaces.
- [ ] Era-open backend suite pass/skip count, `Config().config_fingerprint()` value, and the
      SHA-256 listing of every `apps/backend/app/research/referee_*.py` file are recorded as
      the iteration-0 reference baseline (goal.md Success Criteria #1; J-01 step 2).
- [ ] Zero source files under `apps/backend/` or `apps/frontend/` are modified; no anti-goal
      violation is introduced.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-0-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-01 (era transition artifacts + `/desk` Microscope Readiness section, expected
  absent), J-08 and J-10 (`/`, `/structure`, `/desk` — every existing shipped section: Playbook,
  band context, cohorts, Referee Registry/Adjudications/Runs — plus a check for the four NEW
  Rapid-Microscope sections, expected absent), all via the store-scoped rig (`:8301`/`:3301`)
  per the Constraints' browser-evidence rule (`rm -rf apps/frontend/.next` + rebuild before
  capture, T-9). A screenshot or element capture is recorded for every kept surface checked
  (T-10 — no screenshot means `unknown`, never `passing`).
- Unit/integration: `cd apps/backend && .venv/bin/pytest -q` is run to completion and its
  pass/skip/fail counts are recorded verbatim as the era-open baseline;
  `Config().config_fingerprint()` is checked and recorded (expected `08e471b10130e1e2`); the
  SHA-256 listing of every `apps/backend/app/research/referee_*.py` file is recorded as the
  iteration-0 reference listing for every later re-check (J-10 acceptance).
- Error cases: not applicable this iteration (no new code paths exist to reject invalid input).
  Any endpoint that 404s or errors when probed (e.g. `GET /research/desk/micro/readiness`
  before it exists) is recorded as evidence supporting that journey's FAILING verdict, not
  treated as a bug to fix.

Test-first contract — TC- scenarios seeding the functional-test plan:

- TC-1: given the current `main` branch, when the browser-qa-agent checks for
  `docs/goal-archive/goal-2026-08-16.md`, `docs/rapid-validation-spec.md`, the
  `docs/research-directions.md` rapid-microscope amendments, and the
  `project-extensions/proposer-guidance.md` §5.3 amendments, and calls `GET
  /research/desk/micro/readiness` and loads `/desk` looking for a Microscope Readiness
  section, then a J-01 verdict (passing/partial/failing) is recorded in
  `journey-history.json` citing which sub-checks passed and which did not.
- TC-2: given the current codebase, when the browser-qa-agent inspects
  `apps/backend/app/research/datasets.py` for an `observer=` kwarg on `DatasetStore.replay`,
  searches `apps/backend/app/` for `micro_observer.py`/`micro_snapshots.py`/`micro_features.py`,
  and calls `GET /research/desk/micro/snapshots`, then a J-02 verdict is recorded citing
  presence/absence of each artifact.
- TC-3: given the current codebase, when the browser-qa-agent searches for `micro_join.py` and
  any joinable-corpus count served on the readiness endpoint, then a J-03 verdict is recorded
  citing presence/absence.
- TC-4: given the current codebase, when the browser-qa-agent searches for
  `scout_ledger.py`/`scout.py` and calls `GET /research/desk/micro/scout`, then a J-04 verdict
  is recorded citing presence/absence.
- TC-5: given the current codebase, when the browser-qa-agent searches for
  `micro_accessor.py`/`walkforward.py` and calls `GET /research/desk/micro/walkforward`, then a
  J-05 verdict is recorded citing presence/absence.
- TC-6: given the current codebase, when the browser-qa-agent searches for
  `tick_recorder.py`/`vault.py` and calls `GET /research/desk/micro/vault`, then a J-06 verdict
  is recorded citing presence/absence.
- TC-7: given the current codebase, when the browser-qa-agent searches for
  `micro_graduation.py`, then a J-07 verdict is recorded citing presence/absence.
- TC-8: given the current codebase, when the browser-qa-agent loads `/desk` and looks for
  Scout Ledger / Walk-Forward / Validation Vault sections below the shipped Referee sections,
  and checks the MCP tool count against `desk_micro_readiness`/`desk_scout`/
  `desk_walkforward`/`desk_vault`, then a J-08 verdict is recorded citing which sections/tools
  exist and the tool count (22 vs. 26).
- TC-9: given the current codebase, when the browser-qa-agent searches the (non-existent)
  scout ledger for any ledgered pilot-study specs (range-wall failed aggression, delta
  divergence at level tests, capitulation exhaustion), then a J-09 verdict is recorded citing
  presence/absence.
- TC-10: given the current codebase and the running backend, when the browser-qa-agent runs
  `cd apps/backend && .venv/bin/pytest -q`, checks `Config().config_fingerprint()` prints
  `08e471b10130e1e2`, and loads `/`, `/structure`, `/desk` (Playbook / band-context / cohorts
  / Referee sections) with a screenshot or element capture of each, then a J-10 verdict is
  recorded citing the suite pass/skip count, the fingerprint value, and the screenshot
  evidence for each kept surface.
- TC-11: given the current `apps/backend/app/research/referee_*.py` files, when the developer
  computes their SHA-256 listing and records the current backend suite pass/skip count, then
  both values are written verbatim into
  `docs/handoffs/goal-rapid-microscope-iter-0-dev.md` as the frozen era-open baseline for
  every later re-check (Success Criteria #1; J-10 acceptance).
- TC-12: given the iteration executes with zero intended source edits, when the reviewer
  inspects the iteration's `git diff`, then the diff touches only files under
  `runs/goal-session-rapid-microscope/`, `docs/phases/goal-rapid-microscope-iter-0.md`, and
  `docs/handoffs/goal-rapid-microscope-iter-0-dev.md` — no file under `apps/backend/app/` or
  `apps/frontend/` is modified.
- TC-13: given the iteration completes, when the developer writes the handoff, then
  `docs/handoffs/goal-rapid-microscope-iter-0-dev.md` exists and lists, for each of J-01
  through J-10, its recorded verdict and the evidence citation used to reach it.

## NOTES

- First iteration of this session: `lessons.md` and `assumptions.md` are both empty by design
  — nothing to apply or log yet.
- This era is unusually large for a single session (10 journeys, ~40 anti-goal bullets, one
  operator-gated real-data recording act inside J-06, and later heavy-compute paths governed
  by host-guard caps). Future iterations should follow the natural dependency order goal.md
  itself states — J-01 → J-02 → J-03 → J-04 → J-05 → J-06 → J-07 → J-08 → J-09, with J-10
  guarding continuously — and honor the goal's own "Iteration hygiene" note: step timeouts
  tripped in 13 of 15 Era-6 iterations, so keep per-iteration scope lean, browser acceptance
  narrow, and the fixture-scoped backend the default for QA.
- The blueprint drafted this iteration deliberately carries forward only the unchanged nav/IA
  from prior eras plus this era's seven NEW Data-Contract rows (verbatim from `docs/goal.md`
  §Product Shape); it does not re-enumerate every value shipped by earlier eras — that full
  history lives in `docs/goal-archive/goal-2026-08-16.md`.
- This dispatch did not pass `--require-blueprint-approval`, so the blueprint auto-approves
  and the loop is expected to proceed directly into iteration 1 without a human pause.
- Per the priority rubric, target selection this iteration follows the explicit Baseline mode
  override (all Must-have journeys targeted), not the regressed/unblocker/smallest-spec rubric
  — there is no prior journey state for that rubric to operate on yet.
