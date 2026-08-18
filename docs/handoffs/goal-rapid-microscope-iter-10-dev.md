# goal-rapid-microscope-iter-10 Dev Handoff

**Phase:** goal-rapid-microscope-iter-10
**Date:** 2026-08-18
**Agent:** developer
**Status:** complete

## What Was Built

Implemented J-07 ("Graduation — provenance in, nothing laundered out") per
`docs/rapid-validation-spec.md` §8: the four-state stage vocabulary
(`exploratory -> walkforward_survivor -> sealed_survivor -> referee_handoff_ready`), a new
hash-chained graduation ledger, class-2-only advancement, single-shot sealed evaluation, and the
provenance-complete export bundle. Fixture-only, backend-only, zero new frontend surface, per the
iter spec.

- **New module `apps/backend/app/research/micro_graduation.py`.** No research computation of its
  own — a pure bookkeeping/state-machine layer over three sibling modules' already-ledgered
  evidence.
  - `GraduationLedger` — built on the shared `micro_chain_ledger.HashChainedLedger` primitive
    (never a hand-rolled chain, per the carried iter-4 lesson), the same "one global chain, N row
    kinds discriminated by `row_kind`" shape `walkforward_ledger.WalkForwardLedger` established.
    Two row kinds: `state_transition` and `sealed_evaluation`.
  - `evaluate_walkforward_survivor_transition` — reads a sequence's fold rows via `walkforward.
    fold_results_for_sequence` and its corpus's voiding state via `walkforward.
    is_corpus_era_voided` (both existing, read-only), and delegates the entire five-condition
    `WF_SURVIVOR_RULE_V1` predicate to `walkforward.sequence_verdict` (consulted, never
    reimplemented). `corpus_id`/`sidedness`/`econ_floor` are read off the ledgered fold rows
    themselves, never a second caller-supplied value that could drift.
  - `record_sealed_evaluation` — records a single-shot sealed-shard evaluation verdict. The
    pass/fail verdict itself is caller-supplied (a disclosed T-1 interpretation call — see "Known
    Issues / interpretation calls" below); this function's own job is confirming, via `vault.
    build_vault_state` (existing, unmodified), that the named shard genuinely reached `exposed`
    for this exact `family_root_id`, then recording the verdict permanently. A second call with an
    identical verdict is an idempotent replay; a second call with a *different* verdict for the
    same (family_root_id, dataset_id) is refused outright (never a second draw).
  - `evaluate_sealed_survivor_transition` — requires the family to already be
    `walkforward_survivor` (states are strictly ordered) and requires an already-recorded,
    *passing* sealed evaluation. A recorded failing verdict refuses the transition but the failed
    verdict itself stays permanently on record (TC-6).
  - `build_export_bundle` — buildable for ANY ledgered family at ANY current state, never gated to
    `sealed_survivor`+ (this is what lets a failed-sealed family's own failure be inspected). Pulls
    every ledgered scout trial for the family (including kills, via `scout_ledger.
    distinct_variant_count` — union-N), every fold with its `evidence_class`/`process_label`,
    every vault shard touched, the family's complete sealed-evaluation history, a derived
    "proposed confirmation boundary" (see interpretation calls below), and the sibling `family_id`
    list — plus the verbatim Referee-registration disclaimer sentence (TC-4).
  - `evaluate_referee_handoff_ready_transition` — requires `sealed_survivor`, builds the bundle,
    and requires it to validate (`bundle_validates`) before recording the final transition.
  - Every transition function is identity-keyed and replay-safe (`family_root_id` + target state),
    disclosing `"appended"` vs `"replayed"` per the iter-5 lesson named for this exact journey.
- **New route `GET /research/desk/micro/graduation`** on the existing `micro_routes.py` router,
  filling the reserved owner. Serves `list_graduation_families` (every family's current state,
  complete transition history, complete sealed-evaluation history) plus the ledger's own
  chain-verification verdict. Never 404/500 on an empty ledger — an explicit
  `"No candidates ledgered."` message (goal.md's own Design Direction example) at HTTP 200.
- **`docs/research-directions.md`** — J-07 step 3's "Record the Era-15 evidence line" turned out
  to be largely already done: the era-open "Amendment 2026-08-16, rapid-microscope opening"
  blockquote at the Era-15 header (line ~1744) already states, in full, that an L1 liquidity-family
  candidate reaching `walkforward_survivor` raises the Depth-purchase prior and becomes Card 15.3's
  comparison baseline, and that it dying at the Scout lowers it. (First pass at this task added a
  second, mostly-duplicate paragraph near "Era-15 kill test" — caught on review and reverted before
  finalizing, since restating an already-well-written amendment in different words is not what
  "record the evidence line" should mean.) What genuinely needed adding was a short, dated
  follow-up immediately after that amendment, closing the loop between its 2026-08-16 forward-
  looking promise and the fact that `micro_graduation.py` now actually implements the
  `walkforward_survivor`/`sealed_survivor` states it named in advance. Documentation-only, no
  code/threshold/purchase-decision change; `test_referee_guards.py`'s substring pins over this
  file (a different, pre-existing guard) re-verified passing after the edit.
- **`blueprint.md`'s three disclosure sub-field rows** (`withheld_excluded`, `sealed_withheld`,
  `sealed_tranche`) were already present — the decomposer applied this edit when authoring the
  iter spec (confirmed by reading `runs/goal-session-rapid-microscope/state/blueprint.md` directly
  before starting; no action needed from this agent).

## Files Changed

- `apps/backend/app/research/micro_graduation.py` -- new module, J-07's whole implementation (see above)
- `apps/backend/app/research/micro_routes.py` -- added `GET /research/desk/micro/graduation` + its
  directory-resolving dependency; updated the module docstring's route inventory
- `apps/backend/tests/test_micro_graduation.py` -- new test file, 19 tests covering TC-1 through
  TC-9 plus two extended guards (threshold-sweep ban, copy-discipline lint)
- `docs/research-directions.md` -- Era-15 section gained the J-07 step 3 evidence line (documentation only)
- `runs/goal-rapid-microscope-iter-10/status.json` -- pipeline status
- `docs/handoffs/goal-rapid-microscope-iter-10-dev.md` -- this handoff

No `Config` field added. No edit to `scout_ledger.py`, `walkforward.py`, `walkforward_ledger.py`,
`vault.py`, `micro_accessor.py`, or any `referee_*.py` file — J-07 reads the first four only
through their existing public functions, exactly as the iter spec's OUT OF SCOPE requires.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`

Result: **3,185 collected / 3,177 passed / 8 skipped / 0 failed** (0 errors). This is +19 over the
iter-9 baseline of 3,166 collected / 3,158 passed / 8 skipped (exactly the 19 new tests in
`test_micro_graduation.py`; zero pre-existing test changed behavior). Confirmed via `--junitxml`
report (`<testsuite errors="0" failures="0" skipped="8" tests="3185">`) since this environment's
pytest does not print its usual terminal "N passed in Ts" summary line — the JUnit report is the
authoritative source used here, worth flagging for whoever runs the suite next in this
environment.

`test_micro_graduation.py` alone: 19/19 passed. One test (TC-7's replay check) was verified
load-bearing directly: temporarily removing the "already recorded -> replayed" early-return from
`evaluate_walkforward_survivor_transition` and re-running that one test reproduced a real failure
(`AssertionError: assert 'appended' == 'replayed'`), then the change was reverted and the file
re-verified byte-identical to what was written (via `diff` against a pre-mutation backup) before
re-running the full suite green again.

**Frozen-foundation re-checks (developer-verified directly, not merely test-passing):**
- `Config().config_fingerprint()` -> `08e471b10130e1e2` (unchanged), confirmed via a direct
  `python -c` call.
- All six `referee_*.py` SHA-256 hashes, recomputed via `sha256sum`, match the iteration-0/iter-8
  baseline listing byte-for-byte: `referee_adjudicate.py` `6dd807b5...`, `referee_evidence.py`
  `482f38a1...`, `referee_null.py` `34917e38...`, `referee_registry.py` `03840c86...`,
  `referee_routes.py` `0cc3a06f...`, `referee_stats.py` `fba8816a...`.
- MCP surface: untouched (no MCP file edited); `test_mcp_server.py` passed unmodified, still 22
  tools.
- `git status --short`: only the files listed above (plus pipeline-generated
  `runs/goal-session-rapid-microscope/...` scaffolding this agent did not create) — no accidental
  drift into any KEPT surface.

**Service startup (pre-handoff checklist):**
- Backend: `bash scripts/start-backend.sh` — started cleanly (PID recorded), `GET /health` ->
  `{"status":"ok"}`, `GET /research/desk/micro/graduation` on a genuinely fresh ledger directory ->
  `{"families":[],"message":"No candidates ledgered.","chain_verification":{"ok":true,...}}` at
  HTTP 200. Stopped by exact PID.
- Frontend: `bash scripts/start-frontend.sh` — started cleanly ("✓ Ready in 1183ms", Next.js
  15.5.19), no errors. Stopping the launcher PID left one orphaned `node .../next dev` CHILD
  process still running (confirmed via `ps aux`) — killed it by its own exact PID (recorded from
  `ps`, never a pattern-based kill) and re-verified `ps aux | grep -E "next dev|uvicorn"` was
  empty afterward. Flagging this for whoever next runs `scripts/start-frontend.sh` standalone in
  this environment: the launcher's `exec` does not always prevent a webpack/child process from
  surviving a plain `kill` of the parent PID — worth a `pgrep -P <pid>` check after stopping it.

## Known Issues / disclosed interpretation calls (T-1 discipline)

Two genuine ambiguities in spec §8 were resolved with a disclosed, defensible reading rather than
dropped (dropping either would have made TC-2/TC-3/TC-6 impossible to satisfy) — both are
documented in the module's own docstrings and flagged here per the iter spec's own request for
"extra reviewer scrutiny" on this era's ledger-writer paths:

1. **The sealed-shard evaluation verdict (pass/fail) is caller-supplied, not computed by this
   module.** Spec §8 state 3 requires "passed its ... sealed-shard evaluation" as a *condition*
   but does not specify the statistical machinery that would produce a pass/fail verdict from a
   sealed shard's exposed event data — that machinery (a Mode-B-style evaluation run through the
   accessor against real vault data) does not exist anywhere in this codebase, no real sealed
   shard exists this era (J-06 step 4 is human-blocked), and building it would have reached into
   `micro_accessor.py`/TR-3 territory the iter spec explicitly reserves for a dedicated J-10
   hardening iteration. `record_sealed_evaluation` therefore accepts an already-computed `passed`
   boolean and is responsible for exactly what §8 *does* specify: confirming real vault exposure
   before ever recording a verdict, and recording it permanently and single-shot. This is fully
   fixture-provable (as TC-2/TC-6 do) and does not block a future iteration from wiring a real
   evaluator in front of this same function.
2. **"The proposed confirmation boundary" (a required bundle field, §8 point 4) has no formula in
   the spec.** Read here as the latest timestamp this family's own ledgered evidence has already
   consumed (`validation_revealed_at`/`registered_at` off the fold rows, `evaluated_at` off the
   sealed evaluations) — the earliest instant a genuinely fresh Referee registration could
   legitimately start counting from. Derived entirely from timestamps already on the ledgered
   rows; never a new, independently-tunable rule; honestly `None` when no evidence exists yet.

No other gaps. All 11 TC scenarios (TC-1 through TC-11) are covered — TC-10/TC-11 (the suite-count
and referee-hash re-check, and the golden-replay/fingerprint sweep) via the direct verification
above rather than a `test_micro_graduation.py` unit test, since they are cross-cutting sentinel
checks the iter spec itself frames as developer/reviewer-verified, not module-scoped TCs.

The golden-replay browser sweep for J-01..J-06/J-10 was not run by this agent (no browser tool
invoked) — this iteration made zero frontend changes and zero changes to any existing route's
behavior, so the regression risk is believed to be nil, but the actual replay execution is a
browser-QA-stage activity per the pipeline, not a developer-stage one.
