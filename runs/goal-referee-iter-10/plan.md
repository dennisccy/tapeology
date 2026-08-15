# goal-referee-iter-10 Execution Plan

Era 6 "The Referee" closing round. Target journeys **J-09** (Referee on `/desk` + MCP contract
v5, 22 tools) and **J-10** (kept-product regression sentinel), full depth (mandatory — iter-9's
verdict was ESCALATE). J-01–J-08 are required-still-passing. This is the era's last planned
build round: after J-09/J-10 land, all 10 Must-have journeys are built and the era's remaining
work is the operator's own registration/evaluation acts, not new code.

No scope creep detected: every item below is either explicitly named in goal.md's Key
Capability 6 / Success Criterion 7 (the three `/desk` Referee sections + the 22-tool MCP
contract) or is a rider the iter-9 evaluator itself recommended riding into this round (closing
the open MINOR anti-goal gap, two docstring/test cleanups). All four riders stay inside
goal.md's Non-Goals — none touches `referee_stats.py` math, adds a Data Contract row, or wires
`certificate_mint` into a production route/CLI.

## What to Build

- **Referee Adjudications section** (`/desk`, below Referee Registry): verdict chips in the
  exact vocabulary (`registered` / `pending_forward_confirmation` / `insufficient_sample` /
  `fragile` / `no_evidence` / `corroborated` / `basis_retired`), `confirmatory_output_refused` +
  `refusal_reason` when refused, provenance (`evaluation_basis` hash, null/test-spec ids, seed
  identity, attestation pass/fail), and the served `REFEREE_REGISTER` disclosure text — all read
  verbatim from `GET /research/desk/referee/adjudications`, zero client-side derivation.
- **Referee Runs section** (below Adjudications): null-build and evaluation compute triggers
  with live `{done,total}` progress polling and cancel, plus both run ledgers (`run_id`, `state`,
  `started_at`, `finished_at`, `progress`, `error`) — reusing the page's existing compute-manager
  client pattern (single-flight slot, `handleTrigger*`/`handleCancel*`, poll-until-terminal).
- **MCP contract v5 (20 → 22 tools):** register `desk_referee` →
  `/research/desk/referee/adjudications` and `desk_referee_registry` →
  `/research/desk/referee/registry` as new `_STATIC_PATHS` entries — no selector args (both are
  already no-required-param GETs).
- **Rider 1 (closes iter-9's open MINOR anti-goal gap):** `_pool_strategy_trades` gains an
  optional `candidate: {"strategy_id", "profile"} | None` filter, matched at the journal-record
  level against `result["strategy_id"]`/`result["profile"]` (confirmed present on every record —
  `backtests.py:616-618`) — no new field, no second identity join. `run_evaluation_and_record`
  passes `certificate_mint["candidate"]` through it only when `certificate_mint` is supplied (the
  only path that can ever mint a certificate — still zero production callers this era);
  `certificate_mint=None` (every existing caller) stays whole-corpus/unfiltered, byte-identical.
  Design already logged at `runs/goal-session-referee/state/assumptions.md` ("iter-10 —
  goal-decomposer").
- **Rider 2:** drop the stale "unwired this iteration" language from `referee_adjudicate.py`'s
  module docstring (`:6`) and `authorize_promotion`'s section header/docstring (`:1720`,
  `:1731-1732`) — it has been wired into `pnl_scan._promote` since iter-9.
- **Rider 3:** replace `test_no_bypass_guard_can_fail_on_a_seeded_violation`'s hand-typed-string
  check (`test_pnl_scan.py:1239`) with a real exercise of the actual scan logic — refactor the
  scan into a shared helper both the production lint test and this can-fail test call, then run
  it against a seeded, mutated copy of the scanned source.
- **Rider 4:** delete the duplicate `S-5` assertion in `test_referee_registry.py` (~line 874:
  `assert by_id["S-5"][...]` repeats after the `S-6` assertion above it) — confirmed present,
  no other line in that test changes.
- **Guard-test growth (all "extend, never edit"):**
  - `test_mcp_server.py`: `EXPECTED_TOOLS` (currently a 20-tuple, `:56-77`) → 22-tuple; new
    byte-identity + honest-error tests for both new tools in empty AND populated fixture states.
  - `test_desk_ui_guards.py`: `_PRICE_ARITHMETIC_FIELDS` (`:215-259`) extended for every new
    referee numeric the two sections render (BH `k_star`/`m`, coverage counts, progress
    `{done,total}`, etc.) + seeded counter-tests, following the iter-7/8/9 precedent already in
    the file (e.g. the `hyp.discovery.*`/`hyp.accrual.*` entries).
  - `test_desk_refresh_chain_guard.py`: `_EXPECTED_EFFECT_COUNT` (currently `19`, `:160`) +
    `_EXPECTED_INTERVAL_COUNT`/`_EXPECTED_TIMEOUT_COUNT` (`:161-162`) re-derived exactly once
    with the mandatory rationale paragraph; the no-mount-trigger scan itself stays
    byte-unmodified.
  - `test_copy_discipline.py`: extend lexicon coverage only if the two sections' new copy
    requires it — no weakening of any existing check.
- **QA fixture seeding (fixture-scoped rig only, genuinely new — no prior iteration produced
  either state):** one hypothesis whose adjudication snapshot carries a populated
  `fragility_triggers` list (verdict `fragile`), and one whose stored attestation fails
  re-verification at fold time (`confirmatory_output_refused: true`) — needed so the populated
  screenshot shows both alongside the existing `pending_forward_confirmation`/`registered`
  states.
- **Full regression pass:** J-01–J-08 replay (deterministic golden + LLM fallback where no
  golden exists) green with zero regression; full backend suite green, collected-test count
  ≥ 2,678 (iter-9's own count); `Config().config_fingerprint()` prints `08e471b10130e1e2`; a
  real-browser kept-product walk (cockpit `/`, `/structure` pinned-AAPL Load, every shipped
  `/desk` section) plus the three Referee sections, screenshotted, after a T-9 clean rebuild
  (`rm -rf apps/frontend/.next` + restart).

## Agents Required

- backend-data: yes -- MCP `_STATIC_PATHS` registration, riders 1-4, all guard-test growth
  (`EXPECTED_TOOLS`, `_PRICE_ARITHMETIC_FIELDS`, `_EXPECTED_EFFECT_COUNT`, copy-discipline),
  fixture seeding for `fragile`/refused-attestation states, full backend suite + fingerprint
  verification.
- frontend-ux: yes -- the two new `CollapsibleSection`s on `/desk` (Adjudications, Runs), their
  `lib/api.ts` fetchers and `lib/types.ts` types, new `data-testid`s, static replay-script sweep.

Frontend Present: yes

## Files to Create/Modify

Backend:
- `apps/backend/app/mcp/__init__.py` -- add `desk_referee`/`desk_referee_registry` to
  `_STATIC_PATHS`
- `apps/backend/tests/test_mcp_server.py` -- `EXPECTED_TOOLS` → 22-tuple; byte-identity +
  honest-error tests for both new tools (empty + populated fixture states)
- `apps/backend/app/research/referee_adjudicate.py` -- rider 1 (`_pool_strategy_trades` @ `:521`
  gains `candidate` filter; call site @ `:1204` inside `run_evaluation_and_record` @ `:1121`
  passes `certificate_mint["candidate"]`); rider 2 (docstrings @ `:6`, `:1720`, `:1731-1732`)
- `apps/backend/tests/test_referee_adjudicate.py` -- new tests for the candidate filter
  (matched / unrelated / default-`None` cases; TC-13/14/15)
- `apps/backend/tests/test_pnl_scan.py` -- rider 3 (`test_no_bypass_guard_can_fail_on_a_seeded_violation`
  @ `:1239` refactored to exercise the real scan)
- `apps/backend/tests/test_referee_registry.py` -- rider 4 (delete duplicate `S-5` assertion
  ~`:874`)
- `apps/backend/tests/test_desk_ui_guards.py` -- `_PRICE_ARITHMETIC_FIELDS` extension + counter-tests
- `apps/backend/tests/test_desk_refresh_chain_guard.py` -- `_EXPECTED_EFFECT_COUNT` re-derivation
  + rationale paragraph
- `apps/backend/tests/test_copy_discipline.py` -- lexicon extension if new copy needs it

Frontend:
- `apps/frontend/app/desk/page.tsx` -- `RefereeAdjudicationsSection` + `RefereeRunsSection`
  components and their state/effects/handlers, mounted directly below the existing
  `RefereeRegistrySection` render (`:9590-9611`), following the established
  `sectionReadIssuedRef`/`toggleSection` deferred-fetch contract and the shipped
  `handleTrigger*`/`handleCancel*` single-flight compute pattern (precedent: `handleTriggerScreen`/
  `handleCancelScreen` @ `:8068`/`:8115`)
- `apps/frontend/lib/api.ts` -- new fetchers: `fetchRefereeAdjudications`,
  `fetchRefereeNullRuns`, `fetchRefereeEvaluateRuns`, `postRefereeNullsCompute` /
  `getRefereeNullsCompute` / `postRefereeNullsComputeCancel`, `postRefereeEvaluate` /
  `getRefereeEvaluate` / `postRefereeEvaluateCancel` (mirrors the existing `fetchRefereeRegistry`/
  `postRefereeRegistryHypothesis` style @ `:2068-2130`)
- `apps/frontend/lib/types.ts` -- adjudication entry/response types, null-run and evaluation-run
  ledger types, compute-progress types (mirrors the existing `RefereeRegistryResponse`/
  `RefereeHypothesis` style @ `:2120-2260`)

Handoff:
- `docs/handoffs/goal-referee-iter-10-dev.md` -- required dev handoff

## UI Evolution

- New user-facing capability: an operator can see every registered hypothesis's verdict (exact
  vocabulary chip, refusal reason when refused, full provenance) on `/desk`, and can trigger,
  watch live progress on, and cancel null-builds and evaluations with a visible run history —
  completing the Referee's three-panel on-screen presence this era promised.
- New information displayed: verdict chips (7-token vocabulary); `confirmatory_output_refused` +
  `refusal_reason`; `evaluation_basis` hash, null/test-spec ids, seed identity, attestation
  pass/fail per entry; the `REFEREE_REGISTER` disclosure text; null and evaluation run ledgers
  (`run_id`, `state`, `started_at`, `finished_at`, `progress {done,total}`, `error`).
- New user actions: expand/collapse the two new sections; trigger a null build for a
  hypothesis's null spec; trigger an evaluation for a hypothesis; cancel an in-flight null build
  or evaluation.
- UI surface changes: two new collapsible panels on `/desk`, directly below Referee Registry and
  below every shipped section (T-11 — no shipped `data-testid` or heading string reused). No
  other `/desk` section, column, or route changes.
- Navigation changes: none (`app/meta.py` `UI_ROUTES` untouched — nav stays exactly Cockpit `/` ·
  Structure `/structure` · Desk `/desk`).

## Visual Requirements

- Component patterns: reuse the shipped `CollapsibleSection` wrapper (title + `onToggle` +
  deferred fetch), the established table/row pattern with per-row `data-testid`s (precedent:
  `referee-hypotheses-row-${hypothesis_id}` in `RefereeHypothesesTable`), verdict chips as small
  text/pill tokens rendering the exact vocabulary string (no color implies advice — Design
  Direction rule), and the shipped compute-trigger button + progress readout + cancel-button
  pattern already used for screen/topup/reconcile/playbook computes.
- Layout: single-column stacked sections consistent with the rest of `/desk` (dense, dark-only,
  terminal-grade tables). Adjudications renders as one verdict/provenance table (one row per
  hypothesis). Runs renders as two sub-blocks — null-build controls+ledger, evaluation
  controls+ledger — mirroring the page's existing compute-section layout.
- Key visual effects: none new. House style stays dark-only, dense, professional, terminal-grade
  — no glow/gradient/color additions; this is a lab notebook, not a scorecard (Design Direction).
- States to handle: honest empty states verbatim (`"No hypotheses registered."`, the
  pending-accrual sentence, the attestation-refusal sentence, empty null/evaluation run
  ledgers); live in-flight progress (`{done,total}` polling, no reload); single-flight refusal
  when a second trigger fires while one is in-flight for the same hypothesis, visibly rendered;
  POST-failure error state.

## Key Test Scenarios

- TC-1/TC-5: zero registered hypotheses / zero recorded runs → honest empty-state text renders,
  no verdict chip, no ledger rows (screenshot).
- TC-2/TC-3: a seeded hypothesis with a failed attestation renders `insufficient_sample` +
  `confirmatory_output_refused: true` + the exact refusal sentence; a seeded hypothesis with
  non-empty `fragility_triggers` renders `fragile` — both in the same populated screenshot.
- TC-4: the populated panel also shows the exact `REFEREE_REGISTER` text plus per-entry
  `evaluation_basis` hash / spec ids / seed identity / attestation state, verbatim, zero
  client-side computation.
- TC-6/TC-7: clicking the null-build or evaluation compute trigger starts a run via
  `POST .../nulls/compute` or `POST .../evaluate`, panel polls live progress without reload, a
  completed run appears in the ledger with `state: "completed"`.
- TC-8: a second evaluation trigger for the same in-flight hypothesis is refused single-flight
  (no duplicate run record), refusal visibly rendered (screenshot).
- TC-9: ledger rows show `run_id`/`state`/`started_at`/`finished_at`/`error` read verbatim.
- TC-10: full kept-product browser walk (cockpit, `/structure` pinned-AAPL Load, every shipped
  `/desk` section) renders exactly as shipped in the same pass, screenshotted.
- TC-11/TC-12: MCP advertises exactly 22 tools; `desk_referee`/`desk_referee_registry` are
  byte-identical to their curl equivalents in both empty and populated fixture states.
- TC-13/TC-14/TC-15: the rider-1 candidate filter excludes unrelated trades and mints nothing
  for a mismatched candidate (TC-13), mints correctly for the matching candidate (TC-14), and
  leaves every `certificate_mint=None` caller's whole-corpus pooling byte-identical, including
  iter-9's own `insufficient_sample`-on-real-corpus result (TC-15).
- TC-16/TC-17/TC-18: no "unwired" string remains in `referee_adjudicate.py`; the no-bypass
  can-fail proof genuinely fails when the real scan logic is gutted; the duplicate `S-5`
  assertion is gone with every other assertion unchanged.
- TC-19: J-01–J-08 golden replay (+ LLM fallback where no golden exists) all still score
  `passing`.
- TC-20/TC-21: the `_PRICE_ARITHMETIC_FIELDS` counter-test catches a mutated new field path;
  `_EXPECTED_EFFECT_COUNT` asserts its re-derived value with the rationale paragraph present.
- TC-22: full backend suite green, fingerprint pin `08e471b10130e1e2`, collected-test count
  ≥ 2,678.

## Operational Notes

- T-9 applies: `rm -rf apps/frontend/.next` + rebuild + restart before any browser evidence.
- Host-guard CPU mask (`4-7,12-15`) applies to the Runs section's real compute triggers during
  browser QA exactly as it does to the desk's other computes (T-12) — these are heavy paths even
  against the small fixture-scoped corpus.
- No pattern-based process kills when starting/stopping backend/frontend servers for QA — this
  host is shared with other projects; stop servers by exact PID only.
- All QA/browser work targets the fixture-scoped rig (`:8301`/`:3301`), never the operator's real
  `.data/` store — no real registration/evaluation/null-build runs during this iteration's build
  or QA work.
