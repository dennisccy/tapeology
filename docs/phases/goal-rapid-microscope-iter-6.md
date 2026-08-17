# Goal Iteration 6 — Close J-05's two wiring gaps; unblock the browser lane for J-01/J-10 evidence

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 6
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict was ESCALATE (mandatory, no exceptions)
- **Frontend Present:** yes
- **Target journeys:** J-05, J-10
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04
- **Anti-goal reminders:**
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **The 12 pre-existing tick symbol-days are permanently exploratory** — never sealed, never `historical_oos`, never relabeled. *(critical)*
  - **No threshold, grid, formula, embargo, or fold parameter is chosen or revised from validation, sealed, or holdout outcomes.** Fitting rules are data functionals frozen before reveal; per-origin refits under an unchanged rule are provenance, never a new choice. *(critical)*

## GOAL

Close J-05's two remaining production-wiring gaps — the exposure registry never marks the 12
legacy tick days exposed, and the typed "insufficient sessions" refusal has zero call sites in
`app/` — and, by declaring `Frontend Present: yes`, finally let the browser-qa lane actually
dispatch so J-01's overdue Microscope Readiness photograph gets taken and J-10's whole-product
sentinel walk runs for the first time this era.

## BACKGROUND

Iteration 5 built and re-verified the real walk-forward engine (5 folds / 100 validation
sessions, honestly refused) but left two items the goal names word for word unwired — the §6.7
exposure registry never marks the 12 legacy tick days exposed, and
`require_sufficient_sessions_for_folds` (TR-15) has zero call sites in `app/` — so J-05 stayed
`partial`. The iter-5 evaluator also root-caused why browser evidence has been missing for two
iterations running: `scripts/automation/browser-qa-phase.sh:52` writes N/A stubs and exits
before `browser-qa-agent` is ever dispatched whenever a plan says `Frontend Present: no`, and the
`CHAIN_GOAL_TARGET_JOURNEYS` safeguard meant to prevent exactly this has zero readers — so this
iteration declares `Frontend Present: yes` even though it carries zero frontend changes, per the
dispatch prompt's explicit operator instruction (this is the one remedy fully inside this loop's
control; the durable script fix is framework-maintenance work outside `docs/goal.md`'s Key
Capabilities and outside this agent's authority). J-10 rides alongside J-05 because its own
acceptance requires exactly the sentinel walk this fix finally unblocks, and because its
remaining trap work (TR-2/4/12/19/20) is entirely J-06-owned per goal.md's own J-06 acceptance
line, not reachable before J-06 ships. Coherence was `COHERENCE-PASS` last iteration (no
consolidation forced), and the prior `ESCALATE` verdict makes `Depth: full` mandatory regardless
of the arbiter's usual budget/cadence rungs (iter-3's lesson: only a prior ESCALATE/REGRESSION/
COHERENCE-FAIL grants full unconditionally).

## IN SCOPE

### Backend
- [ ] Wire `require_sufficient_sessions_for_folds` (TR-15) into `run_diagnostic_walkforward`'s
      existing fold-building call site (`apps/backend/app/research/walkforward.py`, immediately
      before its one `build_folds` call), so the typed `InsufficientSessionsForFoldsError` is
      genuinely reachable through the compute route and the CLI, not merely test-covered. Today's
      real playbook corpus (155 sessions) stays well above the 105-session floor, so this is a
      defensive, forward-looking guard on the ONE production path that ever builds folds — it
      does not change today's served result, and it is what J-09 will rely on once walk-forward
      runs against smaller corpora.
- [ ] Give the CLI's `main()` a clean, non-crashing catch for `InsufficientSessionsForFoldsError`
      — print the typed refusal message and exit non-zero, never an unhandled traceback.
      `WalkForwardComputeManager.trigger`'s existing generic exception handler already resolves a
      raised exception from the compute route's worker to `{"state": "failed", "error": str(exc)}`
      — verify this already covers the route side; do not re-plumb it.
- [ ] Seed the §6.7 exposure registry for the legacy tick corpus: register a `corpus_id` distinct
      from `playbook_setups_diagnostic_v1` and mark every session window of the
      currently-registered tick datasets exposed, guarded against duplicate re-seeding the exact
      way the playbook seeding already is (`has_any_exposure_entries`). Resolve the tick dataset
      list the same way `micro_readiness.py` already does (via `config.dataset_dir_resolved()`)
      — no second inventory mechanism, no hardcoded date list (J-06 has not landed yet, so "every
      tick dataset currently registered" and "the 12 legacy symbol-days" are, today, the exact
      same set — seeding now is what makes that equivalence safe).
- [ ] Trigger the seeding above from the SAME operator-act entry point the playbook seeding
      already uses inside `run_diagnostic_walkforward` (never from a GET route — page-load GETs
      never compute, per the era's Non-Goals: "No scheduling").
- [ ] Extend `apps/backend/tests/test_walkforward.py` with the production-reachability and
      idempotent-seeding tests named in TESTING REQUIREMENTS below.

### Frontend
- None. Zero frontend code changes this iteration. `Frontend Present: yes` is declared solely to
  force the browser-qa lane to actually dispatch (root cause above, confirmed independently by
  the iter-4 and iter-5 evaluators). The durable fix — making `detect_frontend_in_plan`
  (`lib/common.sh:1502`) or the browser-qa skip branch actually read the already-exported
  `CHAIN_GOAL_TARGET_JOURNEYS` — is framework-maintenance work outside this agent's authority and
  outside `docs/goal.md`'s Key Capabilities; flagged again here, not scheduled as iteration scope.

### New user-facing capability
None. No new served value, no new page, no new button. This iteration closes two backend
production-wiring gaps in the already-shipped walk-forward engine and, by finally letting the
browser lane run, captures overdue evidence (J-01's Microscope Readiness photograph) and executes
J-10's whole-product sentinel walk for the first time this era.

### New information displayed
None. `GET /research/desk/micro/walkforward`'s response shape is unchanged; a below-floor fold
request now fails closed with a typed message instead of silently returning an empty result, but
no new field is added and no currently-served value changes.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None visible. This is a correctness-and-evidence iteration, not a feature iteration.

### Blueprint conformance
No new surfaces. Reuses the existing Desk → Microscope Readiness (J-01) and Desk → Walk-Forward
(J-05; UI wiring still deferred to J-08 per `blueprint.md`'s Information Architecture table)
homes, both already registered. No nav-skeleton change; `blueprint.md` needs no edit this
iteration (re-read and confirmed accurate — no new displayed value, no new page).

### Data-contract additions
None. The served shape of `GET /research/desk/micro/walkforward` is unchanged. TC-7 below
additionally proves `micro_readiness.py`'s served `exposure_state` per shard is untouched by this
change — the walk-forward-internal §6.7 exposure registry (used only to classify a future
spec/window pair `historical_oos` vs `historical_exposed_diagnostic`) and the readiness-served
vault `exposure_state` (`exploratory`/`hand_assigned`) remain two separate mechanisms, never
conflated, per the "12 tick days stay permanently exploratory" rail restated above.

## OUT OF SCOPE

- J-06 "The recorder and the Vault" — a new, larger, credentialed pillar. Starting it now would
  bundle a second risky journey onto this iteration's targeted fix (never bundle two risky
  journeys). The iter-5 evaluator's own next-step names it as the FOLLOWING iteration's target,
  after J-05 closes "in one short, focused pass."
- J-07 (blocked on J-06) and J-09 (renders through J-08's sections, and needs the percent/bps
  unit pin below) — not reachable yet.
- J-08's new `/desk` sections (Scout Ledger / Walk-Forward / Validation Vault rendering) — a
  separate, larger UI journey; not this iteration.
- The two human-owned rulings (the one-quote-early `micro_observer.py:636/:657` timing stamp;
  whether "variants tried" is counted per-dataset) — still awaiting the owner; not re-litigated
  or worked around here (T-1: vagueness is a drop, never an invention).
- The J-09 percent-vs-bps unit pin (`playbook_observations`'s `value` field vs `econ_floor`,
  `walkforward.py:970` vs `:676`) — explicitly "due before J-09" per iteration-state, not J-05/
  J-10.
- The J-08-parked items (the "approximately None bps" copy fix, the
  `_PRICE_ARITHMETIC_FIELDS`/copy-discipline additions, disclosing which denominator
  `sign_agreement`/decay use) — explicitly parked for J-08 per iteration-state.
- Rebuilding, re-running, or re-deriving any of J-01..J-04's or J-05's ALREADY-verified machinery
  (`micro_accessor.py`, `walkforward*.py`, `micro_chain_ledger.py`, the manager, the CLI, the real
  diagnostic run, the three iter-5 in-run audit fixes) — binding per iteration-state's
  "Do not redo."
- The `browser-qa-phase.sh` / `detect_frontend_in_plan` framework fix — outside this agent's
  authority; the loop-internal workaround (`Frontend Present: yes`) is used instead.
- J-10's remaining 5 traps (TR-2/4/12/19/20) — all explicitly J-06-owned per goal.md's own J-06
  acceptance line; not reachable before J-06 ships.

## DEFINITION OF DONE

- [ ] J-05 "The walk-forward engine" passes: `require_sufficient_sessions_for_folds` has ≥1 real
      call site in `app/` (TC-1/TC-2), the compute route and CLI both surface the typed refusal
      without crashing (TC-3/TC-4), and the exposure registry holds tick-corpus entries (TC-5/
      TC-6) — with every one of J-05's previously-met acceptance items (the 5-fold/100-session
      diagnostic run, TR-3/5/6/13/14/15/16/21/22) re-verified, not carried.
- [ ] J-10 "The kept product stands" advances: the 13-step sentinel (`journey-scripts/J-10.json`,
      unmodified) actually executes via browser-qa-agent and is green (TC-9); the full backend
      suite passes at ≥ iteration-5's 3033-pass baseline with 0 regressions; the fingerprint and
      referee-SHA-256 checks pass (TC-10).
- [ ] Browser-qa-agent is genuinely dispatched this iteration (not N/A-stubbed) — verified via a
      real, non-SKIPPED verdict in `reports/phase-goal-rapid-microscope-iter-6-ui-test-results.md`
      and a populated evidence directory.
- [ ] J-01's `evidence_makeup` flag closes with a fresh Microscope Readiness element screenshot
      (TC-8).
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04 remain green (TC-11 — deterministic
      replay + LLM fallback, mechanically verified under `Frontend Present: yes`, so the lane
      cannot skip them this time).
- [ ] No anti-goal violation introduced; both OPEN minor items this iteration targets (TR-15
      unreachable; tick-day exposure registry unseeded) close, each proven live on the running
      program, not merely test-covered.
- [ ] Unit tests pass; no regressions (TC-10).
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-6-dev.md` (TC-12).

## TESTING REQUIREMENTS

- Browser: J-01 (Microscope Readiness element capture, closing `evidence_makeup`), J-10 (the
  13-step kept-product sentinel, `journey-scripts/J-10.json`, re-run unmodified) — both via
  browser-qa-agent under `Frontend Present: yes` against the store-scoped rig, after a clean
  `rm -rf apps/frontend/.next` rebuild (T-9).
- Unit/integration: `test_walkforward.py` gains a production-reachability test proving
  `run_diagnostic_walkforward` ITSELF raises `InsufficientSessionsForFoldsError` on a below-floor
  session list (not just the standalone function TC-20 already covers) and a tick-corpus
  exposure-seeding test pair (first-seed + idempotent-reseed); full backend suite (invoke
  `pytest tests/` WITHOUT a redundant `-q`, per the iter-0 lesson, so the pass/skip/fail summary
  line stays legible); fingerprint check; referee SHA-256 listing check against the iteration-0
  baseline; engine equivalence + golden-trace tests pass byte-unmodified.
- Error cases: a below-floor session list reaching the production fold-building call site must
  raise the typed `InsufficientSessionsForFoldsError` (never an empty fold report standing in for
  it); the CLI must catch it and exit non-zero with the typed message (never an unhandled
  traceback); a duplicate exposure-registry seeding trigger must not duplicate rows.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract
addition above maps to at least one concrete scenario line, numbered
sequentially, of exactly this shape:

- TC-1: given the real playbook diagnostic corpus (155 sessions, already above the 105-session
  floor), when `POST /research/desk/micro/walkforward/compute` (or
  `python -m app.research.walkforward --diagnostic`) runs after this iteration's change, then
  `require_sufficient_sessions_for_folds` is called before `build_folds` and passes silently, and
  the served result is byte-identical to iteration 5's recorded values (5 folds, 100 validation
  sessions, verdict refused "2 < 3").
- TC-2: given a fake session list shorter than `minimum_sessions_for_sufficient_folds
  (DIAGNOSTIC_GEOMETRY)` (105) fed through the SAME production call path `run_diagnostic_
  walkforward` uses (a new backend test using the existing `_FakePlaybookStore`/
  `_FakeUniverseStore` doubles), when that path runs, then it raises
  `InsufficientSessionsForFoldsError` naming the exact shortfall, and never returns a success
  dict with an empty `rows` list.
- TC-3: given `WalkForwardComputeManager.trigger`'s existing generic exception handling, when the
  compute route's worker raises `InsufficientSessionsForFoldsError` (TC-2's scenario wired
  through the manager), then `GET /research/desk/micro/walkforward/compute` reports
  `{"state": "failed", "error": "<the exact shortfall message>"}` — never an unhandled 500, never
  a silently-empty success.
- TC-4: given the CLI (`python -m app.research.walkforward --diagnostic`) run against a
  below-floor corpus (an integration test against a scoped fixture store), when `main()` runs,
  then it prints the typed refusal message and returns a non-zero exit code — never an unhandled
  Python traceback.
- TC-5: given the exposure registry has never held a tick-corpus entry, when the diagnostic
  walk-forward operator act runs (CLI or compute route) against the real (or a scoped copy of
  the) tick `DatasetStore`, then `exposure_registry.jsonl` gains one exposure entry per session
  window of every currently-registered tick dataset, under a `corpus_id` distinct from
  `playbook_setups_diagnostic_v1`.
- TC-6: given the tick-corpus exposure entries already exist from a prior run, when the same
  operator act runs a second time, then the registry's tick-corpus row count is unchanged
  (idempotent, mirroring the existing `has_any_exposure_entries` playbook guard).
- TC-7: given this iteration's exposure-registry change, when `micro_readiness.py`'s served
  `exposure_state` per shard is read again (real store), then all 18 shards still read
  `exploratory` — proving the walk-forward-internal `historical_oos` classification registry and
  the readiness-served vault `exposure_state` stay two separate mechanisms, never conflated.
- TC-8: given a clean rebuild (`rm -rf apps/frontend/.next`, rebuild, restart — T-9), when
  browser-qa-agent runs against the store-scoped rig with `Frontend Present: yes` forcing real
  dispatch, then the Microscope Readiness section's element screenshot shows a real
  non-fabricated tick corpus (checksums, coverage gaps, fallback fractions, floor-unmet states)
  and `reports/phase-goal-rapid-microscope-iter-6-ui-test-results.md` records a real verdict (not
  SKIPPED) — closing J-01's `evidence_makeup` flag.
- TC-9: given the same browser pass, when `journey-scripts/J-10.json`'s 13-step sentinel runs
  UNMODIFIED, then every step's screenshot renders the same real data prior iterations recorded
  (cockpit `/` live tape + chart, `/structure` load + Tradable Map, every shipped `/desk` section
  including the 3 Referee sections), producing a green sentinel result for the first time this
  era.
- TC-10: given the full backend suite, when `pytest tests/` runs (no redundant `-q`), then the
  pass count is ≥ 3033 with 0 fail, `Config().config_fingerprint()` prints `08e471b10130e1e2`,
  and the six `referee_*.py` SHA-256 hashes match the iteration-0 baseline listing exactly.
- TC-11: given J-01/J-02/J-03/J-04's existing golden replay scripts, when the deterministic-replay
  executor runs them this iteration (now genuinely reachable, since `Frontend Present: yes`
  prevents the browser lane from skipping), then all four replay green with no LLM fallback
  needed, or — for any journey without a golden on file — the LLM browser-qa lane covers it in
  the same pass.
- TC-12: given this iteration's dev work completes, when the developer agent finishes, then
  `docs/handoffs/goal-rapid-microscope-iter-6-dev.md` exists and names both wiring fixes (TR-15
  reachability, tick-corpus exposure seeding) with their exact file:line locations.

## NOTES

- **Lessons applied this iteration:** iter-0 (invoke `pytest tests/` without a redundant `-q` so
  the pass/skip/fail summary is legible — TC-10); iter-1/iter-2-second (the tick-corpus browser
  panel and the J-10 sentinel are already pinned to data the store-scoped rig actually holds —
  `journey-scripts/J-10.json` is repaired and must run UNMODIFIED, never re-pointed); iter-4-first
  and iter-5-first (`Frontend Present: no` silently skips the WHOLE browser pass including the
  required-still-passing set — the direct driver of this iteration's `Frontend Present: yes`);
  iter-5-second (an idempotent write path must key on the identity of one evaluation/seeding act,
  never merely be "idempotent everywhere else" — applied to the new tick-corpus seeding via TC-6,
  mirroring the exact guard the playbook seeding already uses).
- **Iteration hygiene:** per goal.md's own Constraints ("step timeouts tripped in 13 of 15 referee
  iterations"), verify against a scoped/throwaway copy of the real store first (the pattern the
  iter-4/iter-5 evaluator already used for its own re-derivation), and use the fixture-scoped
  `:8301`/`:3301` backend as the default for QA — do not point the browser rig at the real
  `.data/datasets` store (iter-1's lesson: the seeder never populates it with tick datasets, and
  the snapshot-compute manager's derived-cache storage dir defaults to a sibling of it).
- **Passenger items carried forward (not this iteration's scope, tracked for later):** the two
  owner rulings (the one-quote-early timing stamp; per-dataset "variants tried" counting); the
  percent-vs-bps unit pin before J-09; the J-08-parked copy/guard-list additions.
- **Escalation flag:** if the browser lane still fails to dispatch despite `Frontend Present:
  yes` (a different mechanical failure than the one this iteration works around), that is a 3rd
  consecutive miss and should be escalated to a human/framework-maintenance session rather than
  retried a 4th time with the same workaround.
- Depth is `full` because the prior verdict was `ESCALATE` (mandatory, no exceptions, per this
  session's own iter-3 lesson that only ESCALATE/REGRESSION/COHERENCE-FAIL grants full
  unconditionally against the arbiter's usual budget/cadence rungs).
