# Goal Iteration 14 — Clear J-01/J-02's deferred rows + J-12's owed strategy-block screenshot

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** referee
- **Iteration:** 14
- **Mode:** next
- **Depth:** evidence
- **Frontend Present:** no — zero code change; J-12's Strategy Family block is already shipped
  (iteration 13); only its screenshot evidence is incomplete.
- **Target journeys:** J-01, J-02, J-12
- **Required-still-passing journeys:** J-05, J-07, J-09, J-10, J-11
- **Anti-goal reminders:**
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
    them, never a mutation of them. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed,
    never re-tagged, never deleted, never content-perturbed. Splits are frozen at
    registration. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching
    is an explicit, logged act. *(critical)*
  - **Era-B/B2 anti-goals that remain binding:** membership is never a signal; snapshots and
    playbook records are append-only and pinned; every run is an explicit operator act; the
    briefing and the playbook describe, never advise; the demolition stays demolished; the ledger
    never holds orders; the suite stays keyless and hermetic; the fingerprint pin does not move;
    no threshold exists outside its spec and no code path sweeps one; the evidence pools one
    signature; no recorded playbook file is ever rewritten; no second implementation of the
    measurement rail. *(all critical)*
  - **No confirmatory output without a verified oracle attestation.** The adjudication fold
    never serves a confirmatory verdict from an evaluation whose attestation is missing,
    mismatched, or version-stale — it serves the refusal state with its reason; descriptive
    output never masquerades as confirmatory. *(critical)*
  - **Host-guard caps are law.** This host (GEEKOM A7 Max mini-PC) hard-reset five times between
    2026-07-20 and 2026-07-28 under unconfined goal-mode load — instant power/VRM transient
    trips with nothing in the journal; resets #3–#5 struck while tapeology's goal mode ran
    UNGUARDED beside trendora's. When `project-extensions/host-guard/host-guard.env` declares
    ceilings (CPU mask `4-7,12-15` — the complement of trendora's — plus BLAS thread caps and
    memory/task bounds), every heavy path respects them: headless engine runs self-wrap under
    the mask, and interactive pump sessions are auto-confined in place by the engine
    (`host-guard-adopt.sh`; `scripts/automation/host-guard-exec.sh claude` is the optional
    from-birth wrapper) — the engine pauses `AWAITING_HOST_GUARD` (resumable) only when
    confinement cannot be established. Never disable, widen, or bypass these caps to make a run
    faster or a pause go away; widening the mask follows the verification ladder in
    `trendora/project-extensions/host-guard/README.md`. *(critical)*

## GOAL

Replace J-01's and J-02's `DEFERRED-BUDGET` rows with real, live-run PASS results from their own
named backend test modules, and capture J-12's one owed screenshot — the Strategy Family block's
`tick_gate_statement` sentence and Card-6.4 forming-bar caveat, scoped to the
`referee-evidence-strategy-block` element rather than a full-page capture — with zero code change.

## BACKGROUND

Iteration 13's evaluator (`CONTINUE`) named exactly two remaining actions for a
no-new-building round: (1) run J-01's and J-02's own named backend test modules for real, since
`goal_gate.py` blocks `GOAL_ACHIEVED` while their rows still read `DEFERRED-BUDGET` no matter how
healthy every other journey is (`iteration-state.md` "Active blockers"); and (2) capture J-12's
Strategy Family block on its own — both existing captures (`J-12-seeded-rig-result.png`,
`J-12-empty-corpus-result.png`) truncate at the browser tool's 4,320px viewport cap while
`/desk`'s own `scrollHeight` is ~8,443px, cutting off exactly the `tick_gate_statement` and
Card-6.4 forming-bar caveat J-12 exists to surface (iter-13 lesson). Both asks are pure evidence
work on journeys already recorded `passing` — the narrow exception (rule 7) under which a
`Depth: evidence` spec is written — and the binding depth recommendation has no escape condition
to override anyway: the prior verdict was `CONTINUE` (not ESCALATE/REGRESSION), iter-13's own
`coherence.md` is `COHERENCE-PASS`, only 3 of the 6-iteration hardening cadence have elapsed, and
no brand-new full-stack journey is in play.

Lessons applied: iter-1 (a keyless journey — J-01/J-02 have no golden script,
`journey-scripts/J-0{1,2}.json.invalid` — re-verifies via its own pytest module, never a
screenshot of a page that doesn't exist); iter-12/iter-13 (a full-page capture can no longer
reach content this far down `/desk`; target the element itself, `referee-evidence-strategy-block`
at `apps/frontend/app/desk/page.tsx:5125`); iter-11 (`Depth: evidence` is enough to clear
`DEFERRED-BUDGET` rows but cannot fix tooling — the shared walk-through recorder still cannot
play a `scroll` step, so J-11's own owed walkthrough recording stays unaddressed this round, same
as last round). The pump note also flags a "watch, don't act" item carried from iter-13: the
Referee Registry panel now fires three server requests on expand (was two) and this is the second
consecutive round the golden script's wait needed raising (8s→12s at iter-13); if a future round
needs to raise it again, the slowness itself becomes the defect to fix, not the timeout to widen.
This iteration does not touch that code path, so it is recorded here for visibility only.

## IN SCOPE

### Backend
- none — `Depth: evidence`; no developer or reviewer is dispatched this iteration.

### Frontend
- none — J-12's Strategy Family block is already shipped; only one of its screenshots is
  missing.

### Evidence capture / re-verification (this iteration's actual deliverable)
- [ ] Run `apps/backend/tests/test_referee_guards.py` in full; record a real PASS/FAIL row for
  J-01 in this iteration's own results file, replacing the `DEFERRED-BUDGET` row (iter-13's own
  live count: 19 tests, 0 failures — reconfirm live, do not carry the stale number forward
  unverified).
- [ ] Run `apps/backend/tests/test_referee_evidence.py` in full; record J-02's real PASS/FAIL row
  (iter-13's own live count: 29 tests, 0 failures — reconfirm live; this same file's run also
  re-exercises the three J-01-labeled readiness-fold tests iteration 11 named
  (`test_playbook_readiness_pools_newest_per_date_at_the_current_basis`,
  `test_strategy_readiness_counts_datasets_splits_and_trades`,
  `test_strategy_readiness_names_the_unmet_tick_gate_and_the_forming_bar_caveat`), so no separate
  slice run is needed for J-01).
- [ ] Capture the `referee-evidence-strategy-block` element (`page.tsx:5125`) directly — an
  element-scoped screenshot, or the `/desk` sections above it collapsed first so it moves above
  the fold — on the same seeded fixture rig iteration 13 used for `J-12-seeded-rig-result.png`.
  A whole-page capture is not a technique that works on this page (iter-13 lesson): `/desk`'s
  `scrollHeight` (~8,443px) exceeds the capture tool's 4,320px cap. The target image must show
  both `referee-evidence-strategy-tick-gate` (`page.tsx:5167`) and
  `referee-evidence-strategy-basis-caveats` (`page.tsx:5173`) fully in-frame and legible.
  **This capture requires no write action** — the Strategy Family block renders
  `GET /research/desk/referee/evidence`'s already-computed fields verbatim; do not click Build
  Null / Evaluate / Register Hypothesis or any other Referee write control on `/desk` — those
  perform real, irreversible append-only writes and are categorically out of this iteration's
  scope (per dispatch guardrail).
- [ ] Confirm the new capture's checksum differs from the three iter-13 files it must not be
  confused with: `J-12-seeded-rig-result.png`, `J-12-empty-corpus-result.png`, and
  `J-05-result.png`.
- [ ] Replay the required-still-passing set on the same rig visit already open for the capture
  above: `journey-scripts/J-05.json`, `J-07.json`, `J-09.json`, `J-10.json`, `J-11.json`
  (deterministic replay) — a smoke pass piggybacked on the existing visit, not a fresh full
  re-shoot of sections this iteration does not touch.

### New user-facing capability
None — every capability under evidence already shipped; this iteration only strengthens its
evidence trail.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None — no `page.tsx` or component edit.

### Product surface delta
None. The product is unchanged by this iteration; only its evidence trail grows (two live-run
result rows, one corrected screenshot).

### Blueprint conformance
No new page, no nav-skeleton change, no new displayed value. Every journey this iteration
touches (J-01, J-02, J-12) already has its Feature/journey-home row in `blueprint.md`'s
Information Architecture table (J-01/J-12 both point at `/desk` → Referee Registry per the
iter-13 note; J-02 is a library-module row with no page of its own), and this iteration's
Data Contract rows change nothing in shape, owner, or endpoint — so `blueprint.md` is left
as-is, unedited.

### Data-contract additions
None — no new value, owner, or endpoint; this iteration reads exclusively from already-registered
rows and writes no new record anywhere.

## OUT OF SCOPE

- **Do not exercise any `/desk` Referee write control** (Build Null, Evaluate, Register
  Hypothesis, Withdraw, or any compute/cancel trigger) — these are real, irreversible
  append-only writes; this iteration's capture needs none of them (per dispatch guardrail).
- The stray two-line assertion at `apps/backend/tests/test_desk_ui_guards.py:371-372` (move it
  back into the test whose description it belongs to) — non-blocking; ride-along whenever a
  developer is next in this file, not this capture-only round.
- The four small clean-ups carried since iteration 10 (add the four Referee storage folders to
  the guard that watches the owner's real data; make a certificate with no name at all fail
  instead of matching; show a clear word instead of a plain dash when a second data request
  fails; correct the stale `19/7/1` comment) — same reason.
- Fixing the shared walk-through recorder's missing `scroll` action
  (`incredible_auto_dev/scripts/automation/lib/demo_runner.py`) — vendored framework tooling,
  out of a goal-decomposer's remit (established iter-11 precedent); J-11's own owed walkthrough
  recording stays unaddressed this round for the same reason.
- Any change to `referee_evidence.py`, `referee_stats.py`, `referee_null.py`,
  `referee_registry.py`, `referee_adjudicate.py`, `pnl_scan.py`, or any `/desk` component — this
  iteration only RUNS existing tests and captures existing, already-rendered UI.
- Investigating or further raising the Referee Registry panel's request count or replay wait
  timeout — a "watch, don't act" item this round (see BACKGROUND); a future iteration should
  treat the underlying slowness as the defect if the wait needs raising again, not silently widen
  it further.
- Committing this session's outstanding changed files (iterations 8–13) and restarting the
  unrelated trendora backend on port 8255 — both explicitly human/operator items carried since
  iteration 2 / iteration 11; neither is a chain deliverable.

## DEFINITION OF DONE

- [ ] J-01 carries a real PASS row (not `DEFERRED-BUDGET`) in this iteration's results table,
  backed by a live run of `test_referee_guards.py`.
- [ ] J-02 carries a real PASS row (not `DEFERRED-BUDGET`) in this iteration's results table,
  backed by a live run of `test_referee_evidence.py`.
- [ ] J-12 passes via browser-qa-agent with a fresh, checksum-distinct, in-frame capture of the
  `referee-evidence-strategy-block` element showing both the tick-gate sentence and every
  `basis_caveats` entry; its `evidence_makeup` flag clears.
- [ ] Required-still-passing journeys J-05, J-07, J-09, J-10, J-11 remain green (deterministic
  replay).
- [ ] No anti-goal violation introduced — zero production/test/config diff outside `docs/`,
  `reports/`, and `runs/`; no write reaches the operator's real Referee store.
- [ ] Full backend suite still green at or above iteration 13's floor (2,691 passed / 8 skipped,
  0 failed of 2,699 collected); `Config().config_fingerprint()` still `08e471b10130e1e2`.

No dev handoff accompanies this iteration — `Depth: evidence` dispatches no developer or
reviewer (see NOTES).

## TESTING REQUIREMENTS

- Browser: J-12 (element-scoped capture of `referee-evidence-strategy-block` only — its other
  clauses already carry evidence); J-05, J-07, J-09, J-10, J-11 (deterministic replay smoke pass
  on the same rig visit).
- Unit/integration: `apps/backend/tests/test_referee_guards.py` (J-01) and
  `apps/backend/tests/test_referee_evidence.py` (J-02), each run to completion and recorded as
  its own PASS/FAIL row; the full backend suite, run once, to confirm the floor holds.
- Error cases: N/A — no new code path; this iteration only re-proves existing, already-tested
  behaviour.

Test-first contract: every DEFINITION OF DONE checkbox maps to at least one concrete scenario
line below.

- TC-1: given `apps/backend/tests/test_referee_guards.py`, when run to completion, then all
  collected tests pass (expect 19, matching iteration 13's live run since zero backend code has
  changed since) and J-01's results-table row reads PASS, not `DEFERRED-BUDGET`.
- TC-2: given the full `apps/backend/tests/test_referee_evidence.py` suite, when run to
  completion, then all collected tests pass (expect 29, matching iteration 13's live run) and
  J-02's results-table row reads PASS, not `DEFERRED-BUDGET`.
- TC-3: given `/desk` with the Referee Registry section expanded on the same seeded fixture rig
  iteration 13 used, when the `referee-evidence-strategy-block` element is captured directly
  (not as part of a full-page screenshot), then the image shows the
  `referee-evidence-strategy-tick-gate` text and every `referee-evidence-strategy-basis-caveats`
  entry fully in-frame and legible.
- TC-4: given the new J-12 capture, when its checksum is compared against iteration 13's
  `J-12-seeded-rig-result.png`, `J-12-empty-corpus-result.png`, and `J-05-result.png`, then it
  differs from all three.
- TC-5: given `journey-scripts/J-05.json`, `J-07.json`, `J-09.json`, `J-10.json`, `J-11.json`,
  when replayed against the current build (zero product diff since iteration 13), then each
  reports PASS unmodified.
- TC-6: given the Referee Registry panel opened on the same rig visit and allowed its full
  12-second wait, when its three server requests resolve, then the S-1 row renders with the same
  fields iteration 13 recorded (`historical-exploration` origin, `2026-08-15` boundary, `active`
  status) — no regression from the previously raised wait.
- TC-7: given this iteration's file changes, when `git status`/`git diff` is inspected against
  the pre-iteration tree, then it shows changes only under `docs/`, `reports/`, and `runs/` —
  zero diff to `apps/backend/app/`, `apps/frontend/`, or any test file.
- TC-8: given the full backend suite, when run to completion, then it exits with a pass count at
  or above iteration 13's floor (2,691 passed, 8 skipped, 0 failed, 2,699 collected) and
  `Config().config_fingerprint()` reads `08e471b10130e1e2`.
- TC-9: given the operator's real Referee store directories and the store-scope guard, when this
  iteration completes, then the guard reports the same protected-file count as iteration 13
  (11,274 files) with zero new or modified files, and no POST was issued to any
  `/research/desk/referee/*/compute`, `.../evaluate`, or `.../registry/hypotheses` write
  endpoint.

## NOTES

- **No dev handoff accompanies this iteration** — `Depth: evidence` dispatches no developer or
  reviewer; the deliverables are two live-run results-table rows and one screenshot (mirrors this
  session's own iteration-11 precedent).
- **Do not redo** (binding, from `iteration-state.md`): J-12 is BUILT and verified except for one
  screenshot — `RefereeEvidenceReadinessSection` (`page.tsx:5004-5200`), backend byte-frozen since
  iteration 13 (`git diff -- apps/backend/app` EMPTY). J-05's replay timeout 8s→12s is by design
  (assertion text unchanged) — not a regression, and this iteration's TC-6 exists to confirm it
  still isn't one.
- **Framework item, not product scope:** the walk-through recorder's missing `scroll` action
  (`incredible_auto_dev/scripts/automation/lib/demo_runner.py`) still needs either a
  framework-side fix or a change to what the demo-narrator agent emits — flagged for a
  human/framework-maintenance pass, not planned as developer work (see OUT OF SCOPE). J-11's
  owed walkthrough recording is blocked on the same tooling gap and is not addressed this
  round.
- **Watch, don't act:** the Referee Registry panel's expand action now issues three server
  requests (was two), and iteration 13 was the second consecutive round whose golden-replay wait
  needed raising (8s→12s) to observe them all resolve. This iteration does not touch that code
  path; if a future round needs to raise the wait again, treat the slowness itself as the
  problem, not the timeout.
- **Keep total tool-time tight** (per dispatch note): reuse the existing seeded fixture rig
  rather than standing up a new one; do not re-run the full backend suite more than once; do not
  re-capture sections this iteration did not change (J-05/J-07/J-09/J-10/J-11 use the fast
  deterministic-replay lane, not fresh LLM-scored screenshots).
- **Carried human items, non-blocking:** this session's outstanding changed files from iterations
  8–13 are not yet committed; the unrelated trendora backend on port 8255 (outside this project)
  has been down since iteration 2.
- No blueprint edit accompanies this iteration — no new displayed value, no nav-skeleton change
  (see "Blueprint conformance" above).
- No new `assumptions.md` entry — this iteration's scope follows the prior evaluator's next-step
  recommendation and this session's own established iter-11 precedent (evidence depth clears
  deferred rows but cannot fix tooling) directly, with no fresh interpretive call to log.
