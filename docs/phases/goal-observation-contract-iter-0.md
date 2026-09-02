# Goal Iteration 0 — Baseline: verify all six Observation Contract v1 journeys against current state

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** observation-contract
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06
- **Required-still-passing journeys:** None — first iteration of this session; `journey-history.json`
  has no recorded journeys yet.
- **Anti-goal reminders:**
  - *Immutable project rails (`docs/research-directions.md` §0.3, verbatim):*
    1. **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper
       trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the
       tier-1 guard; new research code adds matching guard tests, never weakens them.)
    2. **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n,
       fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no
       imperative trading cues.
    3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
       states and thresholds, and archived-era behavior stay byte-identical. New work is additive
       and versioned beside them, never a mutation of them.
    4. **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival
       through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins
       are labeled overfit. Never lower a minimum sample size, widen a gate, or pool across
       feeds/fingerprints to manufacture a survivor.
    5. **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
       (See the forming-bar rule in card 6.4.)
    6. **Single source of truth** — each shared value is computed once, owned by one canonical
       endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
       violations.
    7. **Deterministic and seeded** — every random draw uses a config-owned recorded seed;
       identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness
       in any research artifact.
    8. **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the
       MCP surface can change state.
    9. **Immutable data** — registered datasets and bar series are append-only, checksummed, never
       re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    10. **Persistence stays scoped** — no ambient recording of live streams; recording is an
        explicit, logged act.
  - *Source-authoring laws (`docs/research-directions.md` §0.8, verbatim; law 5 is not applicable to
    this era — an operator pivot outside the catalog that builds no research primitive):*
    1. **Hypothesis vs modifier.** A statement of the form "feature X adds confirm/veto
       information" is NOT a standalone directional hypothesis unless it explicitly names (a) the
       host setup / eligible population, (b) the relevant side or context, and (c) the directional
       return thesis. Otherwise it is a modifier / atlas / filter object. A future author may
       promote it ONLY through a new forward source revision that supplies all three. Never infer
       the missing host thesis.
    2. **Representation fidelity.** A source formula may be represented by implementation code only
       when the two are formula-equivalent under the ratified methodology, or when an explicit
       named forward supersession exists. Monotonic similarity, signed/unsigned convenience, and
       "it is the feature we happen to have built" are NOT implicit supersession.
    3. **Qualitative threshold fidelity.** There is no universal qualitative-word → quantile rule,
       and none may be invented. A load-bearing threshold is legal only if it is source-defined, an
       existing frozen constant, an exact frozen named construct, a true natural semantic boundary,
       or a newly owner-ratified value. Otherwise the source blocks. A generic quantile protocol is
       specifically forbidden: it would silently overwrite source-defined constants (Card 9.4's
       `z ≥ 4`, Card 9.5's `ratio ≥ 1.5`) while manufacturing values where the source states none
       (Study 1's "high", Study 3's "extreme").
    4. **Proxy lineage.** A historical partial proxy is immutable provenance. A fully specified
       mechanism is a NEW forward `source_id` with scoped supersession. Never "lift" a proxy into a
       full mechanism and never screen a proxy under the full mechanism's name.
    5. **Engineering on demand.** Do not build a research primitive because a blocked source might
       one day use it. Engineering is justified only when at least one forward source is otherwise
       scientifically complete AND that primitive is its remaining blocker. Corollary: a shared
       primitive serving several blocked sources is still not justified if every one of them is
       blocked on something else as well.
    6. **Prerequisite fidelity.** When a source names another card or spec as the provider of a
       load-bearing construct, that prerequisite must ACTUALLY define the construct referenced.
       Conceptual similarity, a matching baseline window, or a shared name is insufficient. If the
       named prerequisite does not define the referenced construct, **block** — never invent or
       extend it to fit.
  - *Era-specific anti-goals (checkable):*
    - No logic of the form `if tape_state == X: trade = True`; no field, token or copy that reads
      as a trading action, readiness or verdict (READY, NO_TRADE, NO_VERDICT, `trade_allowed`,
      PENDING_CONDITION or any equivalent) anywhere in the artifact, the module, its tests or the
      spec's served surface.
    - No candidate matching against an external screener, no external playbook logic, no position
      sizing, no stop calculation, no portfolio risk, no composite-policy promotion, no "validated
      edge" claim, no autonomous alert, no broker execution.
    - No second state engine, no second classifier, no change to the tape classifier, its
      thresholds, its five states, or the feature set; no new tape feature; no strategy mining; no
      change to any Foundry artifact or science.
    - No consumer-specific business logic; no import of, or path reference to, Workstation,
      Trendora or TenSteps under `apps/` or in `docs/observation-contract-spec.md`
      (guard-enforced; `docs/goal.md`, `docs/phases/`, `docs/goal-archive/` and
      `project-extensions/host-guard/` are excluded from the scan).
    - No non-English identifier, schema name, enum value, field name, test name or persisted value
      in the contract.
    - No recomputation of any tape feature, state, confidence, freshness or feed basis outside the
      engine and the one existing `data_feed_for_scenario`; no second scenario-prefix parser.
    - No `available_at_utc` that is not a manager-measured settled instant; no
      `observed_at + delivery_lag` reconstruction; no availability before the underlying event or
      state existed.
    - No latency modelling, no guessed vendor latency constant, no historical receive-time
      reconstruction.
    - No pooling, equating or silent conversion between `sim`, `iex` and `sip`.
    - No route that snapshots an engine for the observation; the atomic manager read is the only
      source.
    - No invented git provenance: `source_revision` and `worktree_dirty` are null when
      unavailable, never guessed; no git call per request.
    - No `content_hash` field; no `reason_codes[]`; no semantic-version inference automation.
    - No mandatory journey or test that requires Alpaca, the network, credentials or market hours.
    - No new UI page, panel, link, component or frontend file change; no new `Config` field; no
      named MCP tool; no CLI; no WebSocket embedding; no listing endpoint.
    - No weakening of any existing guard: `test_no_execution_path.py`, `test_feed_basis.py`,
      `test_copy_discipline.py`, `test_profile_equivalence.py`,
      `test_fingerprint_epoch_retirement.py`, `test_mcp_server.py`, `test_stream_lifecycle.py`,
      `test_observer_equivalence.py` and `test_epoch_anchor.py` stay green and unedited except for
      additive registrations.
  - *Goal-Mode / automation anti-goals:*
    - No Goal Mode workaround that edits, deletes, skips or xfails a guard merely to pass a
      journey.
    - No browser proof based on a fabricated state presented as real; fixture and real views must
      be visibly distinguished.
    - No weakening or bypass of `project-extensions/host-guard/host-guard.env`; Goal Mode pauses
      `AWAITING_HOST_GUARD` if confinement cannot be established.
    - No post-`GOAL_ACHIEVED` proposer or `AUTO:journeys` self-extension (the proposer is retired
      upstream).
    - Anti-goal violations use the existing Goal Mode violation state/disposition machinery; they
      are never dismissed in prose.

## GOAL

Establish the true starting state of every Must-have Observation Contract v1 journey (J-01..J-06)
against the current codebase, with zero code changes, so iteration 1 knows exactly which
era-transition paperwork is already done versus which entirely-unbuilt artifact/route/module each
journey depends on.

## BACKGROUND

This is iteration 0 of a brand-new, finite, six-journey era. Direct repository inspection at
baseline confirms two things already true before this session opened, and the entire scientific/
implementation surface entirely absent:

- **Already done (era-transition paperwork, not this era's build work):** `docs/goal-archive/
  goal-2026-09-02.md`, `docs/observation-contract-spec.md` (the frozen consumer-facing field table,
  361 lines) and a dated "Observation Contract v1" opening note in `docs/research-directions.md`
  all exist and are committed on `main` (HEAD `2f3d2b32 docs(observation-contract): open Observation
  Contract v1 era`). `config_fingerprint` reads `08e471b10130e1e2` and the MCP contract is at v8 /
  28 tools, matching the goal's pinned foundation values.
- **Entirely absent:** `apps/backend/app/observation_contract.py` does not exist; no
  `/tape/{ticker}/observation` route is registered in `apps/backend/app/main.py` (its `/tape/*`
  siblings `/state`, `/features`, `/events`, `/summary`, `/history` all exist; `/observation` does
  not); `WatchManager.get_observation_source` is not defined in `apps/backend/app/watch_manager.py`;
  and no `tests/test_tape_observation_*.py` module exists anywhere under `apps/backend/tests/`.
  `apps/frontend/app/{page.tsx,structure/page.tsx,desk/page.tsx}` all exist and are untouched, as
  the goal requires.

Given this, J-01 through J-05 are expected to fail outright (each depends on the still-unbuilt
builder, atomic manager read, or route), and J-06 is expected to be at best partial: its
era-transition sub-check (the three era-open artifacts existing, and `/`, `/structure`, `/desk`
rendering unchanged) already holds, but its guard-suite/regression-sentinel sub-check
(`tests/test_tape_observation_guards.py`) has no home yet — nothing has been built for it to guard.
Per this agent's baseline protocol, this iteration makes NO code changes — it only runs every
Must-have journey via browser-qa-agent against the current state and records exactly which of
`passing|failing|partial` each one is, so iteration 1 can target the true next chunk of work per the
goal's own Binding Execution Order (constants/builder/hash laws → time law/atomic read →
descriptor/lifecycle/provenance → ingestion-path equivalence → route/machine path →
guards/sentinel). `lessons.md` is empty (first iteration of this session) and there is no prior
evaluator verdict to react to; no assumption-ledger entry is needed (baseline verification requires
no ambiguous interpretive call — the goal's own field/owner table and binding order leave nothing to
interpret).

Depth is `lean` per the baseline protocol (the evaluator's own recommendation for this iteration),
and it is also the goal's own default (`docs/goal.md` Constraints: "Iteration depth: lean by
default with `Frontend Present: no`"). No full trigger applies — the developer agent is a no-op and
all value this iteration comes from the browser-qa verification pass.

## IN SCOPE

### Backend
(none — baseline is verify-only, no code changes)

### Frontend
(none — baseline is verify-only, no code changes; this era ships zero frontend file changes even
past baseline, per the goal's Product Shape)

### New user-facing capability
None. This iteration verifies existing state; it does not add capability.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — this iteration is pure assessment.

### Blueprint conformance
No new surfaces. `runs/goal-session-observation-contract/state/blueprint.md` was drafted this
iteration (Information Architecture: this era adds no page/panel/nav entry — its sole new surface
is the machine-only `GET /tape/{ticker}/observation` route, reached by URL, never a UI control;
Data Contract: every `TapeObservation` field is served by that one planned endpoint, condensed by
partition and pointing to Constitution §1 of `docs/goal.md` as the exact per-field authority). No
blueprint row is implemented yet — every row is `(planned)`; that begins at iteration 1+ per the
Binding Execution Order.

### Data-contract additions
None this iteration (verify-only). See `blueprint.md` for the full planned Data Contract this era
will register incrementally, in the order the goal's Binding Execution Order specifies.

## OUT OF SCOPE

- Any implementation of `ENGINE_SEMANTICS_VERSION`, the schema/partition constants,
  `build_tape_observation`, either hash law, `WatchManager.get_observation_source`, the
  source/session descriptor, the implementation-provenance resolver, the
  `/tape/{ticker}/observation` route, or any `tests/test_tape_observation_*.py` module — all
  deferred to future iterations per the Binding Execution Order.
- Any change to `app/engine/`, the tape classifier, its five states, thresholds, or feature set —
  illegal this era under both the goal's Constitution and the immutable project rails.
- Re-litigating or re-verifying Cockpit / Structure / Desk / Hypothesis Foundry journeys from prior
  eras beyond the J-06 "render unchanged, no new panel" spot-check — out of this session's
  Must-have scope; the existing regression suite covers their substance.

## DEFINITION OF DONE

- [ ] Every journey J-01..J-06 is exercised via browser-qa-agent against its `docs/goal.md`
      Acceptance criteria and recorded in `journey-history.json` as `passing`, `failing`, or
      `partial`, with the specific missing/present surface cited as evidence for each.
- [ ] No code, spec, or config file is modified by this iteration (backend, frontend, `docs/`
      outside this spec + blueprint, and `project-extensions/` all remain byte-identical to
      session start).
- [ ] No anti-goal violation is introduced (trivially true — no code changes).
- [ ] Existing backend full suite (`cd apps/backend && .venv/bin/python -m pytest tests/ -q`) and
      frontend compile (`cd apps/frontend && npx tsc --noEmit`) are run once and their current
      pass/skip/fail counts are recorded as this era's baseline reference; `config_fingerprint`
      (`08e471b10130e1e2`) and the MCP contract (v8 / 28 tools) are confirmed unchanged.
- [ ] Dev handoff written at `docs/handoffs/goal-observation-contract-iter-0-dev.md` noting the
      no-op nature of this iteration and the per-journey verification results.

## TESTING REQUIREMENTS

- Browser: J-01, J-02, J-03, J-04, J-05, J-06 (all Must-have journeys — baseline verifies the
  complete set, each via its Sim-mode served-JSON step).
- Unit/integration: none new; run `cd apps/backend && .venv/bin/python -m pytest tests/ -q` and
  `cd apps/frontend && npx tsc --noEmit` and record the current pass/skip/fail counts verbatim as
  this iteration's baseline reference.
- Error cases: N/A — no new input surface this iteration.

Test-first contract:

- TC-1: given `apps/backend/app/observation_contract.py` does not exist and no
  `/tape/{ticker}/observation` route is registered in `apps/backend/app/main.py`, when
  browser-qa-agent watches `SIM-BIDABS` from `/` (Simulated, `Watch`, wait for `live`) and then
  opens `/tape/SIM-BIDABS/observation`, then the response is a generic unmatched-route 404 rather
  than the required `"schema_version": "tape-observation-v1"` body, and
  `tests/test_tape_observation_projection.py` does not exist — record J-01 as failing.
- TC-2: given no `timing.settled_at_utc` / `available_at_utc` / `availability_basis` field is
  served anywhere and `tests/test_tape_observation_time.py` does not exist, when browser-qa-agent
  inspects the same `/tape/SIM-BIDABS/observation` 404 response and a repo search for the test
  module, then none of the three time concepts is observable and the module is absent — record
  J-02 as failing.
- TC-3: given `WatchManager.get_observation_source` is not defined and
  `tests/test_tape_observation_lifecycle_feed.py` does not exist, when browser-qa-agent exercises
  Watch → Pause watching → Resume watching → Stop watching → Watch again for `SIM-BIDABS` from `/`
  and reloads `/tape/SIM-BIDABS/observation` after each step, then every reload returns the same
  generic 404 with no `lifecycle.*` / `source.session_id` / `source.data_feed` field ever present to
  compare across steps — record J-03 as failing.
- TC-4: given `tests/test_tape_observation_path_equivalence.py` does not exist and no
  `observation_hash` is ever produced by any code path, when browser-qa-agent pauses `SIM-BIDABS`
  and reloads `/tape/SIM-BIDABS/observation` twice, then no `observation_hash` / `artifact_hash`
  pair exists in either response to compare — record J-04 as failing.
- TC-5: given no `/tape/{ticker}/observation` route exists on the FastAPI app and
  `tests/test_tape_observation_route.py` does not exist, when browser-qa-agent opens
  `/tape/SIM-BIDABS/observation` and `/tape/ZZZZ/observation`, then both return the same generic
  unmatched-route 404 rather than the required 200-with-schema / matched-404-parity distinction,
  and the MCP `get_endpoint` proxy has no new tool/path to proxy — record J-05 as failing.
- TC-6: given `docs/goal-archive/goal-2026-09-02.md`, the dated `docs/research-directions.md`
  opening note and `docs/observation-contract-spec.md` already exist and are committed (confirmed
  present at baseline), but `tests/test_tape_observation_guards.py` does not exist, when
  browser-qa-agent visits `/`, `/structure` and `/desk` (confirming each renders unchanged, 0 new
  panel/link/control) and the evaluator runs the full backend suite plus `tsc --noEmit`, then the
  three era-open artifacts are present and the three pages render unchanged, but the guard-suite
  module and its `test_counterexample_*` tests are entirely absent — record J-06 as partial
  (era-open paperwork already done; guard/regression-sentinel work entirely unbuilt).

## NOTES

- **Binding scientific/build ordering reminder for iteration 1+ planning:** per `docs/goal.md`'s
  "Binding Execution Order", constants/builder/hash laws (J-01) must land before the time
  law/atomic read (J-02), which must precede descriptor/lifecycle/provenance (J-03), which must
  precede ingestion-path equivalence (J-04), which must precede the route (J-05), which must
  precede guards/sentinel (J-06). A future decomposer that bundles route work ahead of the atomic
  read, or ingestion-path equivalence ahead of the descriptor, risks violating this binding partial
  order — follow the six-step sequence directly rather than parallelizing steps.
- **Deterministic-evidence discipline carried forward:** every future iteration's mandatory
  evidence must stay Sim-mode / committed-fixture / harness-based per the goal's
  Deterministic-evidence rule — no mandatory journey or test may depend on Alpaca, the network,
  credentials or market hours; a real-provider smoke test may exist only as an optional,
  environment-gated, non-blocking test.
- No `lessons.md` entries exist yet (first iteration of this session) and no assumption-ledger
  entry was needed this iteration — baseline verification required no ambiguous interpretive call.
