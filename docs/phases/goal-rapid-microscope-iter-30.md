# Goal Iteration 30 — Re-verify the closed ledger; let the evaluator rule on GOAL_ACHIEVED

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 30
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** None — zero remaining failing/partial journeys (see BACKGROUND). This is
  the "all journeys passing" case in the goal-decomposer's own rules: do not manufacture work.
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10
  (full regression sweep — this is a closure-adjacent round, matching the guidance to widen to
  every passing journey periodically before a certification decision).
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
    - A recorded tranche is one opaque research pool until its shards are exposed. No served
      surface may present a complete identity-labelled partition of "exploratory" versus
      "sealed", nor a complete per-shard list of either side while any pool member is
      unexposed (TR-2 inference trap).
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
      displayed quote sizes unless the dataset's `quote_size_unit` is verified; unverified or
      mixed units are a typed refusal.
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
      human-authored journeys, the Anti-goals section, or any other part of that file.
  - *Host protection (carried verbatim — a physical constraint of the host, not product
    scope):* Host-guard caps are law. When `project-extensions/host-guard/host-guard.env`
    declares ceilings (CPU mask `4-7,12-15` plus BLAS thread caps and memory/task bounds),
    every heavy path respects them; the engine pauses `AWAITING_HOST_GUARD` (resumable) only
    when confinement cannot be established. Never disable, widen, or bypass these caps to make
    a run faster or a pause go away.

## GOAL

Re-verify, with zero code changes, that all ten Rapid-Microscope journeys remain green and that
the anti-goal ledger now carries zero unresolved *blocking* and zero unresolved *critical*
findings following the owner's out-of-band three-state disposition ruling — so the evaluator can
make an honest GOAL_ACHIEVED (or not) call on solid, freshly re-derived ground rather than
inherited state.

## BACKGROUND

Iteration 29 ended STALLED with 10/10 journeys green and exactly one class of blocker left: six
open anti-goal findings whose only remaining unblock path was an owner ruling on whether they
count against the era (two real, owner-deferred product items — r8 chain-ledger identity, r9
sealed-judge econ floor — plus four `T-10`/build-chain items the maintenance protocol places
outside a product round's authority). Since that verdict was written, the owner made exactly that
ruling **out of band** (commits `efb26351` "three-state anti-goal ledger" and `2551a139` "owner
dispositions for rapid-microscope's six open findings", both 2026-08-24, after iter-29). The new
ledger mechanism (`lib/anti_goal_disposition.py`) lets a `resolved: false` entry additionally carry
an owner-written `owner_disposition` (`deferred_named_revision` or `framework_backlog`,
`blocks_current_era: false`) without ever claiming it was fixed; the commit's own summary line
reports `total=52 resolved=46 unresolved_blocking=0 unresolved_non_blocking=6
unresolved_critical=0`. I independently read `runs/goal-session-rapid-microscope/state/journey-
history.json` this round rather than trusting the commit message: all six entries (indices 21, 29,
37, 44, 45, 48 in `anti_goal_violations`) now carry a well-formed `owner_disposition` with
`blocks_current_era: false`, `escalation_tripped: false` where an escalation condition is
recorded, and a non-blank `ruling`/`ruled_at`/reference — matching the module's fail-closed schema
(`lib/anti_goal_disposition.py`'s own test suite, `test-anti-goal-disposition.sh`, proves 10
malformed shapes still block). No product or science file changed in either commit
(`git show --stat` on both: `.claude/**`, `incredible_auto_dev/**`, and the one state JSON only).

This is squarely the goal-decomposer's own "zero remaining FAILING journeys" case
(`journey-history.json` shows all ten `passing`), now *additionally* cleared of the one thing that
was overriding that shortcut at iter-29 (a live, non-owner-owned blocker) — the owner-ruling
blocker iter-29 named is exactly the "human-owned" case the priority rubric's rule 6 says not to
re-plan. The one still-open item, "give J-05's stored check its own text and take close-up
captures for J-02/J-03", is explicitly recorded by the iter-29 evaluator as optional and
non-blocking ("It blocks nothing") — planning it as this iteration's deliverable would be exactly
the evidence-manufacturing rule 7 forbids, so it is named in OUT OF SCOPE instead and may ride
passenger only if the browser-qa pass below naturally produces it.

**Depth: this iteration deliberately writes `lean`, not the `full` the dispatch line recommends.**
That recommendation is iter-29's own "next depth" call, made *before* the owner's ruling landed —
it reflects a round that still had six live unblock questions, not the round that exists now. None
of the four full-depth triggers hold against this iteration's actual (zero-code) scope: no
structural/cross-cutting change, no data-model migration, the prior verdict was STALLED (not
ESCALATE/REGRESSION), and no hardening cadence is due (0 consecutive lean iterations, cadence
disabled per the dispatch header). This is not a new full-stack journey either — nothing is being
built. Per the engine's own arbiter, a full spec written outside those four conditions is demoted
to lean regardless of what is written here, so lean is both the honest and the mechanically
enforced choice; this deviation is logged to the assumption ledger.

**Lessons applied:** iter-25's first lesson ("re-check the GROUNDS of every carried-forward open
item, not just whether the code changed") and iter-29's two lessons ("a hard-audit finding is an
input to be re-derived, not a fact to inherit" and "check WHICH SECTION of `docs/goal.md` its cited
rule lives in before scoring an item as blocking") are why this spec re-reads the ledger directly
rather than trusting the commit message's summary line, and why TC-2/TC-3 below re-run the
disposition-summary CLI and re-test both live escalation conditions rather than copying last
round's numbers forward.

## IN SCOPE

### Backend
(none — zero production/test code changes; this round is verification only)

### Frontend
(none)

### New user-facing capability
None.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — this iteration re-confirms the existing product surface, it does not change it.

### Blueprint conformance
No new surfaces; no Information Architecture change.

### Data-contract additions
None.

## OUT OF SCOPE

- Any production or science code change — this iteration's own Definition of Done requires a
  literally empty `git status --porcelain apps/`.
- Re-opening or re-litigating the two owner-deferred product items (chain-ledger identity
  commitment r8; sealed-judge econ floor r9) — the owner's ruling already dispositioned both as
  `deferred_named_revision`, `blocks_current_era: false`; r8/r9 still forbid a build round from
  designing either fix ad hoc.
- The four `framework_backlog` items — their remedies live in `agents/**`/`skills/**`/
  `scripts/automation/**`, outside a product round's authority per
  `.claude/maintenance-protocol.md` §1.
- The optional, non-blocking dev job named in iter-29's next-step recommendation (giving J-05's
  golden its own assertion text; close-up captures for J-02/J-03) — not planned scope this
  round (rule 7); may ride passenger on the required-still-passing browser/replay pass below,
  never as a goal.
- Recording more real tape, revealing/assigning any sealed shard, or running the three pilot
  studies against the real recorded corpus (standing out-of-scope, unchanged).
- Any new Config field, threshold, grid, or fold-parameter change.

## DEFINITION OF DONE

- [ ] All ten Required-still-passing journeys (J-01..J-10) re-verified with zero regressions —
      deterministic replay for every journey carrying a stored golden, LLM browser-qa fallback
      for J-07 (no golden by binding design).
- [ ] The anti-goal disposition ledger re-confirmed: `unresolved_blocking=0`,
      `unresolved_critical=0`, both live escalation conditions (chain-ledger vault-writability;
      sealed-judge production caller) re-tested and still untripped.
- [ ] No anti-goal violation introduced.
- [ ] Zero product/science code diff: `git status --porcelain apps/` empty; all six `referee_*.py`
      files re-hash byte-identical to the iteration-0 listing; `docs/goal.md` diff empty against
      its iter-29 committed state.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-30-dev.md`, recording this
      as a zero-diff verification round with the re-derived evidence above (not a claim copied
      from the commit messages).

## TESTING REQUIREMENTS

- Browser: none of J-01..J-10 changed code this round, so no new capture is planned scope; the
  required-still-passing pass below uses deterministic replay first, LLM browser-qa fallback only
  for journeys without a stored golden (currently J-07 only).
- Unit/integration: `test_micro_graduation.py` (J-07's own suite); `lib/anti_goal_disposition.py`'s
  `summary` CLI against this session's `journey-history.json`.
- Error cases: none new — this round introduces no new code path.

Test-first contract:

- TC-1: given the stored golden scripts in `runs/goal-session-rapid-microscope/journey-scripts/`,
  when `demo_runner.py --mode verify` is run over every journey that has one (J-01..J-06,
  J-08..J-10 — nine of ten), then all nine pass with 0 failed steps and the run's exit summary
  reports 9/9 passing.
- TC-2: given J-07 has no stored golden by binding earlier decision, when
  `pytest apps/backend/tests/test_micro_graduation.py` is run, then all 23 tests pass and the
  wall-clock time is reported explicitly (regression check against the 1.49-1.56s times recorded
  at iter-29 by three independent runners).
- TC-3: given `lib/anti_goal_disposition.py`'s `summary` CLI is run against
  `runs/goal-session-rapid-microscope/state/journey-history.json`, when the command completes,
  then it reports `unresolved_blocking=0` and `unresolved_critical=0`, matching the count recorded
  in commit `2551a139` (`total=52 resolved=46 unresolved_blocking=0 unresolved_non_blocking=6
  unresolved_critical=0`).
- TC-4: given the chain-ledger identity escalation condition ("re-score CRITICAL the moment the
  vault directory becomes writable by anything the operator does not personally control, or the
  tranche datasets stop being directly readable outside the product"), when the vault directory's
  permission bits and the tranche datasets' readability are checked this round, then the
  directory is still operator-owned (not world/group-writable by anything else) and the tranche
  datasets are still directly readable outside the product — the condition remains untripped.
- TC-5: given the sealed-judge econ-floor escalation condition ("the moment any production caller
  is wired to `evaluate_sealed_verdict`, or any sealed-evaluation row appears outside a throwaway
  QA rig, this re-opens as CRITICAL immediately"), when `grep -rn evaluate_sealed_verdict
  apps/backend/app/` is run and `.data/` is checked for a `micro_graduation`/`micro_sealed_
  evaluation` directory, then grep returns zero production callers (docstrings/definition/error
  string only, unchanged from iter-29's re-test) and no such directory exists.
- TC-6: given the six `referee_*.py` files' iteration-0 SHA-256 listing
  (`docs/handoffs/goal-rapid-microscope-iter-0-dev.md:75-81`), when re-hashed at the end of this
  iteration, then all six hashes are byte-identical to that listing.
- TC-7: given `git status --porcelain apps/` and `git diff HEAD -- docs/goal.md`, when checked at
  the end of this iteration, then both are empty, confirming zero product/science code and zero
  goal-text change.

## NOTES

- This spec deliberately deviates from the dispatch line's `full` depth recommendation; see
  BACKGROUND's dedicated paragraph and the matching assumption-ledger entry for the full
  reasoning and the escape-condition check.
- If the evaluator disagrees with treating the owner's disposition ruling as clearing the STALLED
  blocker (e.g. reads a residual ambiguity in how `blocks_current_era` composes with an
  `escalation_tripped` re-test), that is exactly the kind of call the evaluator's own methodology
  §B.1/§C.2/§C.3 (added by commit `efb26351`) now governs directly — this spec does not attempt to
  pre-empt that reading, only to hand it fresh, independently re-derived evidence.
- The optional J-05/J-02/J-03 polish job remains available as a small, genuinely non-blocking
  follow-up if the evaluator does NOT declare GOAL_ACHIEVED this round; it is not built here.
