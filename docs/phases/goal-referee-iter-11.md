# Goal Iteration 11 — Clear the deferred re-verification backlog + J-09's owed screenshot

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** referee
- **Iteration:** 11
- **Mode:** next
- **Depth:** evidence
- **Frontend Present:** no — zero code change; J-09's UI is already shipped, only its evidence is
  incomplete.
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-08, J-09
- **Required-still-passing journeys:** J-07, J-10
- **Anti-goal reminders:**
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
    them, never a mutation of them. *(critical)*
  - **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out
    survival through the sweep gate PLUS a valid Referee certificate (this era makes the
    "era-6 statistical gates" clause real). Train-only wins are labeled overfit. Never lower a
    minimum sample size, widen a gate, or pool across feeds/fingerprints to manufacture a
    survivor. *(critical)*
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
  - **Promotion is certificate-locked.** No champion promotion without a valid
    candidate-specific Referee certificate; no bypass flag, env override, or default-allow
    path exists (source-scan guard-tested); a Playbook certificate can never satisfy a
    strategy promotion. *(critical)*
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

Replace the seven `DEFERRED-BUDGET` rows iteration 10's wall-clock budget left behind — J-01
through J-06 and J-08 — with real, live-run PASS/FAIL results, and capture the one screenshot J-09
still owes (the null-build single-flight refusal) — with zero code change.

## BACKGROUND

Iteration 10 shipped J-09 and J-10 for real (Referee Adjudications + Runs panels rendered on
`/desk`, MCP grown 20→22 tools) but ran out of budget before re-checking 7 of the 8 older
journeys; their rows in `reports/phase-goal-referee-iter-10-ui-test-results.md` read
`DEFERRED-BUDGET`, and `goal_gate.py:448` blocks `GOAL_ACHIEVED` while any deferred row stands
(`iteration-state.md`). J-01/J-02 have no golden replay script at all (`journey-scripts/J-01.json.invalid`,
`J-02.json.invalid`); J-03–J-06 and J-08 never had one either — none is a dedicated page, their UI
reveals land inside J-09's own Referee sections (`goal.md`: "the rest are keyless/automated with
browser reveals landing in J-09"). Per this session's own iter-1 lesson, re-verifying them means
running each one's own named pytest module and recording a real PASS/FAIL row — never a screenshot
of a page that does not exist. J-09 itself is `passing` but carries `evidence_makeup: true` for one
clause: the "second in-flight trigger refused" screenshot is byte-identical (md5
`d3065788c71ecfcc5623b7704ad6de73`) to two unrelated screenshots (iter-10's own finding) — the
underlying refusal is already proven three ways (unit test, a 5-concurrent-POST probe, and the
reachable UI refusal path), so only the picture is owed.

This is not the "zero remaining FAILING journeys, nothing left to do" case — `journey-history`'s
`passing` status on all ten journeys predates the deferral, and `goal_gate.py`'s deterministic gate
additionally requires zero outstanding deferred rows before it will even consider
`GOAL_ACHIEVED`, which is exactly what this iteration clears; the evaluator's own iter-10 verdict
was `CONTINUE` with an explicit "one short verification round" next step, not a declaration that
nothing remains.

The evaluator's binding depth recommendation for this iteration is `evidence`. No escape condition
holds: the prior verdict was `CONTINUE` (not ESCALATE/REGRESSION), the prior coherence verdict was
`COHERENCE-PASS` (iter-10's Anti-goal Check table cites `runs/goal-session-referee/iter-10/coherence.md`),
the hardening cadence is explicitly disabled this session ("0 = disabled" per the dispatch prompt),
and there is no brand-new full-stack journey in play. Iteration 10's own next-step recommendation
named three things: (1) re-check the seven skipped journeys via their own backend acceptance
tests, (2) capture J-09's owed screenshot, and (3) "fix the walk-through recorder, whose script
still contains an action type ('scroll') the player does not understand." Item (3) is a code fix
to `incredible_auto_dev/scripts/automation/lib/demo_runner.py` (`_VALID_ACTIONS = {"goto", "click",
"fill", "expect", "wait_for"}` — "scroll" is not a member), which is vendored FRAMEWORK tooling
that authors this project's demo-narrator script, not Tapeology product code — the same class of
item the desk session's own `goal-desk-iter-25.md` named explicitly "out of a goal-decomposer's
remit." It rides in NOTES/OUT OF SCOPE for a human or framework-maintenance pass, not as an IN
SCOPE item here, so that this spec's only real ask (re-verify + capture) matches rule 7's
evidence-depth exception exactly (see `assumptions.md` iter-11 entry for the full reasoning).

Lessons applied: iter-1 (keyless journeys re-verify via their own pytest module, never a
screenshot of a nonexistent page); iter-2 (a screenshot of a static JSON body proves rendering,
not a live re-check — every re-verification below runs a live pytest module or live probe); iter-10
(checksum evidence images whenever a clause demands a distinct on-screen state — TC-8 below checks
the new screenshot's hash against the old shared one); and a sibling session's own recorded lesson
(`goal-playbook-iter-12.md` BACKGROUND, citing that session's `lessons.md` iter-11): "A
`Depth: evidence` micro-path silently deletes planned code work... Never plan code work under it"
— confirming the recorder fix cannot be an IN SCOPE item here.

## IN SCOPE

### Backend
- none — `Depth: evidence`; no developer or reviewer is dispatched this iteration.

### Frontend
- none — J-09's Referee Runs panel is already shipped; only one of its screenshots is missing.

### Evidence capture / re-verification (this iteration's actual deliverable)
- [ ] Run `apps/backend/tests/test_referee_guards.py` (catalog reconciliation + zero-lens-diff
  guards) plus the J-01 readiness-fold slice of `apps/backend/tests/test_referee_evidence.py`
  (`test_playbook_readiness_pools_newest_per_date_at_the_current_basis`,
  `test_strategy_readiness_counts_datasets_splits_and_trades`,
  `test_strategy_readiness_names_the_unmet_tick_gate_and_the_forming_bar_caveat`); record a real
  PASS/FAIL row for J-01 in this iteration's own results file, replacing UT-J-01's
  `DEFERRED-BUDGET` row.
- [ ] Run the full `apps/backend/tests/test_referee_evidence.py` (26 tests: observation contract,
  both adapters, the derived-observation cache cold/warm/deleted, the dedup/coverage-shrink
  disclosure); record J-02's row.
- [ ] Run `apps/backend/tests/test_referee_stats.py` (48 tests) and
  `apps/backend/tests/test_referee_oracles.py` (11 tests — goal.md: "the oracle suite is green and
  IS the acceptance"), within `REFEREE_ORACLE_BUDGET_SECONDS`; record J-03's row.
- [ ] Run `apps/backend/tests/test_referee_null.py` (36 tests); record J-04's row.
- [ ] Run `apps/backend/tests/test_referee_registry.py` (47 tests); record J-05's row.
- [ ] Run `apps/backend/tests/test_referee_adjudicate.py` (57 tests); record J-06's row.
- [ ] Run `apps/backend/tests/test_pnl_scan.py` (30 tests — the whole file now encodes the J-08
  certificate/promotion-interlock behavior, including `test_no_bypass_path_exists_for_authorize_promotion`,
  `test_no_bypass_guard_can_fail_on_a_seeded_violation`, and the `test_tc3`.."test_tc7"` refusal-class
  set); record J-08's row.
- [ ] Capture J-09's owed screenshot: on the scoped fixture rig, start a null build for
  `referee-null-tod-v1` from a second channel (a second browser tab, or a direct
  `POST /research/desk/referee/nulls/compute` / the `referee_null.py` CLI) while it is still
  running, then on a freshly loaded `/desk` in the primary tab expand Referee Runs and click
  "Build Null" for the same spec — capture the resulting `triggerError` line, exact text
  "Refused — a null build is already running for this spec." Confirm via
  `assert_scoped_qa_backend.py` (run immediately before the write) that the target is the scoped
  rig, never the operator's real store, and confirm the new screenshot's checksum differs from
  `UT-07-result.png`/`UT-09-result.png`/`UT-10-result.png`'s shared hash
  (`d3065788c71ecfcc5623b7704ad6de73`, iter-10's own finding).
- [ ] Replay the required-still-passing set: `journey-scripts/J-07.json` (deterministic replay);
  a light smoke pass on J-10 (`/`, `/structure`, `/desk` each load without a console error),
  piggybacked on the same rig visit already needed for the J-09 capture above — not a full
  fresh re-shoot of every `/desk` section (iter-10 already screenshot-verified all of them one
  iteration ago, and zero product code has changed since).

### New user-facing capability
None — every capability under test already shipped; this iteration only strengthens its evidence.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None — no `page.tsx` or component edit.

### Product surface delta
None. The product is unchanged by this iteration; only its evidence trail grows (seven live-run
result rows, one corrected screenshot).

### Blueprint conformance
No new page, no nav-skeleton change. Every journey this iteration touches (J-01–J-09) already has
its Feature/journey-home row in `blueprint.md`'s Information Architecture table, and none of this
iteration's Data Contract rows changes shape, owner, or endpoint — so per the desk session's own
`goal-desk-iter-25.md` precedent ("No blueprint edit accompanies this iteration — no new displayed
value, no nav-skeleton change"), `blueprint.md` is left as-is.

### Data-contract additions
None — no new value, owner, or endpoint; this iteration reads exclusively from already-registered
rows.

## OUT OF SCOPE

- Fixing `incredible_auto_dev/scripts/automation/lib/demo_runner.py`'s `_VALID_ACTIONS` set (or
  changing what the demo-narrator agent emits so it never proposes a "scroll" step) — vendored
  framework tooling, not this era's product surface; out of a goal-decomposer's remit
  (`goal-desk-iter-25.md` precedent). Flagged for a human or framework-maintenance pass, not
  planned as developer work.
- The four small clean-ups iteration 10's evaluator listed as non-blocking: a certificate check
  that treats "both names unknown" as a match; a plain dash on a second-data-request failure that
  looks like an honest "no value"; a stale `19/7/1` comment; adding the four Referee storage
  folders to the store-scope guard. Explicitly "worth doing whenever a builder is next in this
  area," not this capture-only round.
- Any change to `referee_evidence.py`, `referee_stats.py`, `referee_null.py`,
  `referee_registry.py`, `referee_adjudicate.py`, `pnl_scan.py`, or any `/desk` component — this
  iteration only RUNS existing tests/probes; it edits none of them.
- Committing the outstanding changed files from iterations 8–10, and restarting the unrelated
  trendora backend on port 8255 — both explicitly human/operator items the evaluator has carried
  since iteration 2 and iteration 10; neither is a chain deliverable.

## DEFINITION OF DONE

- [ ] J-01 through J-06 and J-08 each carry a real PASS/FAIL row (not `DEFERRED-BUDGET`) in this
  iteration's own results file, backed by their own named pytest module's actual run output.
- [ ] J-09 passes via browser-qa-agent with all three acceptance screenshots present, including a
  freshly captured, checksum-DISTINCT single-flight-refusal image (`evidence_makeup` cleared).
- [ ] Required-still-passing journeys J-07 (deterministic replay) and J-10 (live smoke pass)
  remain green.
- [ ] No anti-goal violation introduced — zero production/test/config diff (`git diff` against the
  pre-iteration tree empty outside `docs/`, `reports/`, `runs/`); every write this iteration lands
  on the scoped fixture rig only, confirmed via `assert_scoped_qa_backend.py` before the write and
  the store-scope guard after.
- [ ] Full backend suite still green at or above iteration 10's floor (2,680 passed / 8 skipped, 0
  failed of 2,688 collected), `Config().config_fingerprint()` still `08e471b10130e1e2`.

## TESTING REQUIREMENTS

- Browser: J-09 (single-flight-refusal screenshot only — its other clauses already carry
  evidence); J-07 (deterministic replay); J-10 (light smoke: `/`, `/structure`, `/desk` load
  without console error).
- Unit/integration: the seven named pytest modules below, each run to completion and recorded as
  its own PASS/FAIL row; the full backend suite, run once, to confirm the floor holds.
- Error cases: N/A — no new code path; this iteration proves existing refusal/failure paths still
  behave as recorded (the null-build single-flight refusal; `pnl_scan`'s no-certificate/
  wrong-candidate/stale/mismatched/failed-gates/malformed refusal classes — already covered by the
  named pytest modules below).

Test-first contract: every DEFINITION OF DONE checkbox maps to at least one concrete scenario line
below.

- TC-1: given `apps/backend/tests/test_referee_guards.py` and the J-01 readiness-fold tests in
  `test_referee_evidence.py`, when run to completion, then all pass and J-01's results-table row
  reads PASS (not `DEFERRED-BUDGET`).
- TC-2: given the full `apps/backend/tests/test_referee_evidence.py` suite (26 tests), when run to
  completion, then all pass and J-02's results-table row reads PASS.
- TC-3: given `apps/backend/tests/test_referee_stats.py` (48 tests) and
  `apps/backend/tests/test_referee_oracles.py` (11 tests), when run to completion within
  `REFEREE_ORACLE_BUDGET_SECONDS`, then all pass and J-03's results-table row reads PASS.
- TC-4: given `apps/backend/tests/test_referee_null.py` (36 tests), when run to completion, then
  all pass and J-04's results-table row reads PASS.
- TC-5: given `apps/backend/tests/test_referee_registry.py` (47 tests), when run to completion,
  then all pass and J-05's results-table row reads PASS.
- TC-6: given `apps/backend/tests/test_referee_adjudicate.py` (57 tests), when run to completion,
  then all pass and J-06's results-table row reads PASS.
- TC-7: given `apps/backend/tests/test_pnl_scan.py` (30 tests, including
  `test_no_bypass_path_exists_for_authorize_promotion` and the `test_tc3`.."test_tc7"` refusal-class
  set), when run to completion, then all pass and J-08's results-table row reads PASS.
- TC-8: given a null build started for `referee-null-tod-v1` against the scoped fixture rig from a
  second channel while it is still running, when `/desk`'s Referee Runs "Build Null" control for
  the same spec is clicked on a freshly loaded page, then the page renders the exact line
  "Refused — a null build is already running for this spec." and the captured screenshot's
  checksum differs from `UT-07-result.png`/`UT-09-result.png`/`UT-10-result.png`'s shared md5
  `d3065788c71ecfcc5623b7704ad6de73`.
- TC-9: given `journey-scripts/J-07.json`, when replayed against the post-iteration build, then it
  reports PASS unmodified.
- TC-10: given the same rig visit already open for TC-8, when `/`, `/structure`, and `/desk` are
  each loaded, then all three render without a console error and without visual regression versus
  iteration 10's own screenshots (a light smoke check, not a full re-shoot).
- TC-11: given this iteration's file changes, when `git status`/`git diff` is inspected against
  the pre-iteration tree, then it shows changes only under `docs/`, `reports/`, and `runs/` — zero
  diff to `apps/backend/app/`, `apps/frontend/`, or any test file.
- TC-12: given the full backend suite, when run to completion, then it exits with a pass count at
  or above 2,680 (8 skipped, 0 failed, 2,688 collected) and `Config().config_fingerprint()` reads
  `08e471b10130e1e2`.
- TC-13: given every write this iteration performs (the TC-8 null build), when
  `assert_scoped_qa_backend.py` runs immediately before it and the store-scope guard runs after,
  then both report clean — the scoped rig confirmed as the target, and all protected files under
  the operator's real store unchanged.

## NOTES

- **No dev handoff accompanies this iteration** — `Depth: evidence` dispatches no developer or
  reviewer; the deliverables are the seven results-table rows and the one screenshot (mirrors
  `goal-desk-iter-25.md`'s own NOTES precedent: "there is no `docs/handoffs/...-dev.md` to
  write").
- **Do not redo** (binding, from `iteration-state.md`): J-09 is BUILT and verified (Adjudications +
  Runs on `/desk`, MCP 20→22) — only the one owed screenshot is this iteration's business. The
  iter-9 MINOR anti-goal closure, Riders 2–4, the re-derived guard counters, and the
  era-cumulative-diff inventory check are all CLOSED — none is re-opened or re-tested here.
- **Framework item, not product scope:** the walk-through recorder's "scroll" validation failure
  (`incredible_auto_dev/scripts/automation/lib/demo_runner.py:87`, `_VALID_ACTIONS` has no "scroll"
  entry) needs either a framework-side fix to that file or a change to what the demo-narrator agent
  emits — flagged here for a human/framework-maintenance pass, not planned as developer work (see
  OUT OF SCOPE and the `assumptions.md` iter-11 entry for the full reasoning).
- **Carried human items, non-blocking:** this session's outstanding changed files from iterations
  8–10 are not yet committed; the unrelated trendora backend on port 8255 (outside this project)
  has been down since iteration 2. Neither blocks this iteration's own deliverables.
- Assumption-ledger entry written: `runs/goal-session-referee/state/assumptions.md` iter-11 — why
  the recorder fix is read as out-of-scope for a `Depth: evidence` iteration rather than as grounds
  to deviate from the binding depth recommendation.
- No blueprint edit accompanies this iteration — no new displayed value, no nav-skeleton change
  (see "Blueprint conformance" above).
