# goal-referee-iter-10 Dev Handoff

**Phase:** goal-referee-iter-10
**Date:** 2026-08-15
**Agent:** developer
**Status:** complete

## What Was Built

### J-09: The Referee on `/desk` + MCP contract v5 (20 -> 22 tools)

- **Referee Adjudications section** (`apps/frontend/app/desk/page.tsx`): a new `CollapsibleSection`
  rendered directly below the shipped Referee Registry section. On first expand it fetches
  `GET /research/desk/referee/adjudications` (and, to cross-reference each entry's own
  `null_spec_id`/`test_spec_id`, `GET /research/desk/referee/registry`) and renders, per registered
  hypothesis: the verdict chip in the exact 7-token vocabulary, `confirmatory_output_refused` +
  `refusal_reason` when refused (or the live pre-checkpoint accrual `{post_boundary_sessions,
  target_sessions}` when no checkpoint exists yet), a provenance block (`evaluation_basis` hash,
  null/test spec ids, seed identity -- rendered as the hypothesis_id, see Known Issues --
  attestation pass/fail, and the recorded Benjamini-Hochberg fold `k_star/m (q=...)`), and
  `fragility_triggers`. The served `REFEREE_REGISTER` disclosure text is rendered verbatim above
  the table. Honest empty state: `"No hypotheses registered."` (TC-1). Zero client-side arithmetic
  or verdict derivation -- every value is read straight off the response body.
- **Referee Runs section**: a second new `CollapsibleSection` below Adjudications -- the era's LAST
  section. Hosts two independent, single-flight-PER-KEY compute controls (unlike every other desk
  compute control on this page, which is a page-wide singleton): null-build triggers keyed by
  `null_spec_id` (derived from the distinct non-null `null_spec_id`s actually present across the
  registry's own hypotheses -- never a hand-typed constant list) and evaluation triggers keyed by
  `hypothesis_id` (one control per registered hypothesis). Each control shows a trigger button,
  live `{done,total}` progress while running, a cancel button, and an inline refusal message when a
  second trigger for the SAME key fires while one is already running (TC-8, mirroring the
  backend-authoritative `started: false` refusal `handleRunBackscanClick` already established).
  Below both control blocks, the durable null-build and evaluation run ledgers render as sortable
  tables (`run_id`, spec/hypothesis id, `state`, `progress`, `started_at`, `finished_at`, `error`),
  each with its own honest empty state.
- **MCP contract v5**: `desk_referee` -> `/research/desk/referee/adjudications` and
  `desk_referee_registry` -> `/research/desk/referee/registry` registered in `_STATIC_PATHS`
  (`apps/backend/app/mcp/__init__.py`) -- no selector arguments, matching every other no-arg static
  tool. `EXPECTED_TOOLS` grown to the 22-tuple with both new names positioned right after
  `desk_playbook_evidence`.

### Rider 1 -- closes the iter-9-recorded MINOR anti-goal entry (candidate-evidence identity)

`_pool_strategy_trades` (`apps/backend/app/research/referee_adjudicate.py`) gains an optional
`candidate: {"strategy_id", "profile"} | None` keyword filter. When supplied, both the candidate
trades AND the recorded `random_null` trades are narrowed to observations whose OWN backtest
report (resolved via `_strategy_backtest_id`/`JournalStore.get_backtest`, memoized) was recorded
under that EXACT `(strategy_id, profile)` -- no new field on the observation shape, no second
identity join, reusing `strategy_observations()` unmodified. `run_evaluation_and_record` passes
`certificate_mint["candidate"]` through it ONLY when `certificate_mint` is supplied (the only path
that can ever mint a certificate -- still zero production callers this era). `certificate_mint=None`
(every existing route/CLI caller) keeps pooling whole-corpus and unfiltered, byte-identical to
before this rider. This closes the exploit the iter-9 evaluator reproduced: a certificate could
previously be minted for an unrelated candidate name using evidence that never belonged to it.

### Riders 2-4 (small cleanups the iter-9 evaluator asked to ride into this round)

- **Rider 2**: dropped the stale "unwired this iteration" language from `referee_adjudicate.py`'s
  module docstring and `authorize_promotion`'s section header/docstring -- it has been wired into
  `pnl_scan._promote` since iteration 9 (verified: `pnl_scan.py` imports and calls
  `authorize_promotion` at `_promote`, before `append_validation_row`).
- **Rider 3**: `test_pnl_scan.py::test_no_bypass_guard_can_fail_on_a_seeded_violation` now exercises
  the REAL scan logic (`_assert_no_bypass_tokens`, factored out of
  `test_no_bypass_path_exists_for_authorize_promotion` so both tests call the identical helper)
  against a seeded, mutated copy of the actual `pnl_scan.py` source, instead of a hand-typed string
  check that never touched the production scan at all.
- **Rider 4**: removed the duplicate `S-5` assertion in `test_referee_registry.py`
  (`test_shortlist_s4_s5_s6_readiness_reflects_the_at_wall_context_resolve`), an exact repeat of the
  line above it. No other assertion in that test changed.

### Guard-test growth

- `test_mcp_server.py`: `EXPECTED_TOOLS` -> 22-tuple; 6 new tests (byte-identity + honest
  integrity-error-surfacing for both new tools, empty AND populated fixture states -- the populated
  state registers ONE real hypothesis through the actual POST route, never a hand-crafted file).
  Also fixed two PRE-EXISTING tests (`test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool`,
  `test_get_endpoint_desk_screen_runs_byte_identical_with_no_new_tool`) whose own hardcoded
  `len(TOOL_NAMES) == 20` needed re-deriving to `22` -- their own "no new tool for this path" claim
  is unaffected.
- `test_desk_ui_guards.py`: `_PRICE_ARITHMETIC_FIELDS` extended for every referee numeric the two
  new sections actually render (`entry.live_coverage.*`, `snapshot.bh.{k_star,m,q}`,
  `compute.{done,total}`, `run.progress.{done,total}` -- `\??` added to cover the optional-chaining
  forms the JSX genuinely uses) + one new seeded counter-test proving each path is genuinely caught,
  not just listed, with a "does not over-match" check against the real page's own pass-through
  idioms.
- `test_desk_refresh_chain_guard.py`: `_EXPECTED_EFFECT_COUNT` 19 -> 21, `_EXPECTED_INTERVAL_COUNT`
  7 -> 9 (`_EXPECTED_TIMEOUT_COUNT` unchanged at 1), re-derived exactly once with the mandatory
  rationale paragraph. Both new compute managers are single-flight PER KEY, so each gets exactly
  ONE poll effect (never one per key) that polls every currently-running key from a single
  `setInterval` -- +2 effects/+2 intervals total, not +4/+2 as a naive per-key design would need.
  The section's own deferred reads add NO effect (`toggleSection` is a plain event handler, never
  an effect). Also extended `_TRIGGER_CALLS` with the four new handler/client identifiers
  (`handleTriggerRefereeNullBuild`/`triggerRefereeNullsCompute`/`handleTriggerRefereeEvaluate`/
  `triggerRefereeEvaluate`) so the no-mount-trigger scan covers them too.
- `test_copy_discipline.py`: verified (via `find_violations` run directly against every new copy
  string, plus the full suite run) that no lexicon extension was needed -- every new string
  (honest-empty texts, refusal messages, verdict tokens, run-state words) is already clean.

### New tests for the rider-1 fix (`test_referee_adjudicate.py`)

Three new tests (`test_iter10_tc13_...`, `test_iter10_tc14_...`, `test_iter10_tc15_...`, distinctly
named from the file's own pre-existing iter-9 `test_tc13`/`test_tc14` to avoid any collision):
TC-13 reproduces the iter-9 evaluator's own probe (12 planted `v1/default` trades, mint attempted
for an unrelated candidate) and proves zero evidence pools and no certificate mints; TC-14 proves
the SAME 12 trades mint correctly when the candidate matches; TC-15 proves `candidate=None` (every
existing caller) pools byte-identical to the pre-rider shape.

**A necessary side-effect fix**: implementing rider 1 correctly REVEALED that two pre-existing
tests (`test_tc12_a_strategy_checkpoint_mints_exactly_one_certificate_through_the_real_rail`,
`test_tc13_a_failed_attestation_never_mints_a_strategy_certificate_role_stays_pending` in
`test_referee_adjudicate.py`, plus three tests in `test_pnl_scan.py` built on the shared
`_mint_matching_certificate_through_the_real_rail` helper) had ALWAYS planted evidence under
`STRATEGY_V1_ID`/`PROFILE_DEFAULT` while declaring a DIFFERENT candidate identity in the
certificate mint (e.g. `"structure_tape"`, or `PROFILE_CANDIDATE_FASTER_WARMUP`) -- a mismatch that
was harmless before this rider (pooling was unfiltered) and is now a genuine test-fixture bug the
rider correctly surfaces. Fixed by making the test fixtures internally consistent: the two
`test_referee_adjudicate.py` tests' own `candidate` literal now names `STRATEGY_V1_ID` (matching
what they actually plant); `test_pnl_scan.py`'s `_plant_strategy_backtest` gained
`strategy_id`/`profile` parameters (defaulting to the old hardcoded values for safety) that
`_mint_matching_certificate_through_the_real_rail` now passes through from its own `candidate`
argument, so every one of its callers' planted evidence matches its own declared candidate. No
production code changed for this fix -- test fixtures only.

## Files Changed

- `apps/backend/app/mcp/__init__.py` -- `desk_referee`/`desk_referee_registry` added to
  `_STATIC_PATHS` + `TOOLS` (20 -> 22 tools); module docstring's endpoint list updated.
- `apps/backend/app/research/referee_adjudicate.py` -- rider 1 (`_pool_strategy_trades` candidate
  filter + `_strategy_backtest_id`/`_candidate_matches_observation` helpers; the
  `run_evaluation_and_record` call site); rider 2 (docstring "unwired" cleanup).
- `apps/backend/tests/test_mcp_server.py` -- `EXPECTED_TOOLS` 22-tuple; 6 new
  `desk_referee`/`desk_referee_registry` tests; 2 pre-existing tool-count assertions re-derived.
- `apps/backend/tests/test_referee_adjudicate.py` -- 3 new TC-13/14/15 tests for rider 1; TC-12/
  TC-13 (iter-9) candidate literal fix.
- `apps/backend/tests/test_pnl_scan.py` -- rider 3 (`_assert_no_bypass_tokens` helper +
  refactored can-fail test; also removed a stray leftover assertion line from the original test
  body my first edit did not fully replace); `_plant_strategy_backtest` gained
  `strategy_id`/`profile` params, threaded through `_mint_matching_certificate_through_the_real_rail`.
- `apps/backend/tests/test_referee_registry.py` -- rider 4 (duplicate `S-5` assertion removed).
- `apps/backend/tests/test_desk_ui_guards.py` -- `_PRICE_ARITHMETIC_FIELDS` extended + 1 new
  counter-test.
- `apps/backend/tests/test_desk_refresh_chain_guard.py` -- `_EXPECTED_EFFECT_COUNT`/
  `_EXPECTED_INTERVAL_COUNT` re-derived + rationale paragraph; `_TRIGGER_CALLS` extended.
- `apps/frontend/app/desk/page.tsx` -- `RefereeAdjudicationsSection`/`RefereeRunsSection` (+
  sub-components), new state, `toggleSection` branches, trigger/cancel handlers, 2 new polling
  effects, mount site. See `docs/handoffs/goal-referee-iter-10-frontend.md` for the frontend-side
  detail.
- `apps/frontend/lib/api.ts` -- 9 new fetchers (`fetchRefereeAdjudications`, `fetchRefereeNullRuns`,
  `fetchRefereeEvaluateRuns`, the `nulls/compute` + `evaluate` trigger/get/cancel triplets).
- `apps/frontend/lib/types.ts` -- corresponding response/snapshot/run-ledger types.
- `runs/goal-session-referee/state/assumptions.md` -- 3 new "iter-10 -- developer" entries (the
  "seed identity" rendering interpretation; the redundant-registry-fetch cross-section design; the
  QA-fixture-setup scope note).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ --junit-xml=<path>` (foreground;
`pyproject.toml`'s `addopts = "-q"` suppresses the summary line, verified via junit-xml + exit code).

Result: **2688 collected, 2680 passed, 8 skipped, 0 failed**, exit code 0 (>= iteration 9's own
2,678 floor). `Config().config_fingerprint()` prints `08e471b10130e1e2` (verified live, unchanged).

Also individually verified green before the full run (so failures were isolated and attributable):
`test_desk_ui_guards.py` (77 passed), `test_desk_refresh_chain_guard.py` (29 passed),
`test_mcp_server.py` (52 passed, real uvicorn subprocess), `test_copy_discipline.py` (30 passed),
and the combined referee+pnl_scan batch (`test_referee_adjudicate.py`, `test_referee_registry.py`,
`test_pnl_scan.py`, `test_referee_guards.py`, `test_referee_evidence.py`, `test_referee_null.py`,
`test_referee_stats.py`, `test_referee_oracles.py` -- 274 passed).

Frontend: `npm run build` (Next.js production build, TypeScript strict mode) with an isolated
`NEXT_DIST_DIR` so the check never touched any running dev server's `.next` -- compiled cleanly,
zero TypeScript errors, `/desk` route built at 42.8 kB. (The isolated build auto-appends its temp
dist path to `tsconfig.json`'s `include` list; reverted via `git checkout` immediately after, so
`tsconfig.json` carries no diff.)

**Live service verification** (not just fixtures): `rm -rf apps/frontend/.next`, then started a
real backend (`scripts/start-backend.sh`, port 8301) and frontend (`scripts/start-frontend.sh`,
port 3301) against this repo's own deterministic QA-rig ports. `GET /health` -> `200`. `GET /desk`
-> `200`, compiled cleanly (624 modules), and the served HTML contains all three Referee section
headings ("Referee Registry", "Referee Adjudications", "Referee Runs"). Curled the four new/changed
read routes directly -- `GET /research/desk/referee/registry`, `/adjudications`, `/nulls/runs`,
`/evaluate/runs` -- all returned the correct honest-empty JSON shown above. Ran the live MCP module
(`app.mcp.list_tools`/`call_tool`) against this running backend: 22 tools advertised,
`desk_referee`/`desk_referee_registry` both present and returning byte-identical bodies. Stopped
both servers by their exact PIDs (backend: single `kill <pid>`; frontend: `kill -- -<pgid>` against
the whole `npm exec next dev` process-group tree, verified via `pstree` that every worker thread
shared the one PGID) -- no pattern-based kill, per this iteration's pump note. Made ZERO writes
against the operator's real default store during this verification -- every call was a GET; no
registration/compute POST was ever sent to this non-fixture-scoped instance.

## Known Issues

- **"Seed identity" is rendered as the hypothesis_id, not a raw seed value.** No endpoint serves the
  literal `REFEREE_SEED` constant (271828) as JSON this era -- it is a single global module
  constant, never per-record. Logged as a T-1 interpretation in `state/assumptions.md` (iter-10,
  developer): the Adjudications provenance block labels the entry's own `hypothesis_id` as "seed
  identity" (the one per-hypothesis component of the spec's pinned seed recipe
  `f"{REFEREE_SEED}:{hypothesis_id}:{purpose}..."`), rather than fabricate or hardcode a value
  client-side.
- **BH `k_star`/`m`/`q` are rendered even though goal.md's own acceptance text does not explicitly
  name them** (it lists evaluation_basis/spec ids/seed/attestation). Added anyway because the
  phase spec's IN SCOPE bullet names them as an anticipated example of "every referee numeric newly
  rendered," and they make a `fragile`/`corroborated`/`no_evidence` verdict's own derivation
  auditable (Design Direction: "verdicts with their provenance... a lab notebook, not a
  scorecard"). If a future reviewer judges this out of scope, it is a one-line JSX removal plus a
  guard-regex trim -- no data-contract or store impact either way.
- **QA fixture seeding (the `fragile` and refused-attestation adjudication states) is NOT built by
  this handoff.** Following the iter-9 precedent (the developer verifies already-shipped read
  paths against a live server; browser-specific fixture construction is the browser-qa-agent's own
  preparatory step), this is left for QA. The exact mechanics are already demonstrated in this
  repo's own tests and can be followed verbatim against the fixture-scoped rig's OWN
  `TAPEOLOGY_DESK_REFEREE_EVAL_DIR` (or the universe-dir sibling default):
  - **`fragile` verdict**: register a hypothesis, then call `run_evaluation_and_record(...,
    journal_store=<planted evidence producing a BH pass with a triggered fragility condition>)`
    directly (or via a small Python one-off), OR write an `AdjudicationSnapshotStore.record(...)`
    entry by hand with `"verdict": "fragile"` and a non-empty `fragility_triggers` list, matching
    `_build_and_record_snapshot`'s own schema (`referee_adjudicate.py`, the `snapshot_fields` dict)
    -- the ONLY constraint the fold enforces at read time is that `attestation.passed` re-verifies
    (`verify_oracle_attestation`), so the planted `attestation` block must be a real, passing one
    (e.g. `referee_stats.run_oracle_attestation()`'s own return value, embedded verbatim).
  - **Refused-attestation state**: the SAME snapshot shape, but with `attestation` mutated after
    minting (e.g. `passed: False`, or a `stats_core_version` mismatch) so
    `verify_oracle_attestation` fails at FOLD time -- `test_a_corrupted_snapshot_file_refuses_
    rather_than_silently_reverting_to_live` and `test_tc13_a_failed_attestation_never_mints_a_
    strategy_certificate_role_stays_pending` (`test_referee_adjudicate.py`) both demonstrate this
    exact construction (monkeypatching `run_oracle_attestation` to force `passed: False` before
    calling `run_evaluation_and_record`, or writing a snapshot file directly with a failing
    `attestation` block). The rendered refusal text is `entry.refusal_reason`, served verbatim by
    `_snapshot_fold`'s own literal string -- TC-2's required text is exact and does not need to be
    reproduced by the fixture; it is already hardcoded in the backend.
  - Both fixture states must be constructed ONLY against the fixture-scoped rig (never the
    operator's real `.data/` store) -- per this iteration's own pump note, `POST
    /research/desk/referee/registry/hypotheses` is a real, irreversible append-only write.
- **The Runs section's trigger controls have no mount-time seed.** Unlike every other compute
  manager on this page, a null-build/evaluation job started before this page load (e.g. from a
  different browser tab, or a page refresh mid-run) will render as idle until the operator
  re-triggers it or the section is re-expanded -- there is no proactive "is anything already
  running for this key" fetch on first expand. This was a deliberate simplicity-bar call (nothing
  in TC-6/7/8 requires resuming an in-flight job from a stale page load) and is reversible: adding
  a mount-time snapshot fetch per discovered key is additive, not a redesign.
