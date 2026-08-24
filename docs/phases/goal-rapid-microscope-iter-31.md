# Goal Iteration 31 — J-11: Graduation gets a surface (desk section + MCP v7); J-07's golden gap closes

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 31
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-11
- **Required-still-passing journeys:** J-01, J-04, J-05, J-06, J-07, J-08, J-09, J-10 (every
  journey whose section renders on `/desk` — the page this iteration edits — plus J-08, the
  journey that owns the MCP tool-count contract this iteration bumps v6→v7, and J-10, the
  full-product sentinel. J-02/J-03 are excluded: keyless/automated, no `/desk` section of their
  own, unaffected by this iteration's surface.)
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
      surface — readiness, recorder progress, datasets, backtests, PnL ledger, Scout,
      walk-forward, graduation, MCP, UI — may present a complete identity-labelled partition
      of "exploratory" versus "sealed", nor a complete per-shard list of EITHER side while any
      pool member is unexposed. The governing test is the TR-2 inference trap.
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
      human-authored journeys, the Anti-goals section, or any other part of that file;
      proposed journeys MUST carry a single-source-of-truth acceptance criterion, keep the
      `default` profile and `v1` byte-identical, respect every rail above, and include a
      `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just to keep the loop
      alive is a failure.
  - *Host protection (carried verbatim — a physical constraint of the host, not product
    scope):* Host-guard caps are law. When `project-extensions/host-guard/host-guard.env`
    declares ceilings (CPU mask `4-7,12-15` plus BLAS thread caps and memory/task bounds),
    every heavy path respects them; the engine pauses `AWAITING_HOST_GUARD` (resumable) only
    when confinement cannot be established. Never disable, widen, or bypass these caps to make
    a run faster or a pause go away.

## GOAL

Ship J-11: a read-only **Graduation** section on `/desk` (directly below the shipped Validation
Vault section) that renders the already-computed `micro_graduation.py` ledger verbatim — per
family its stage token, transition history, and permanent sealed verdicts — plus a byte-identical
`desk_graduation` MCP proxy (contract v6→v7, 26→27 tools), so the funnel's terminal state stops
being invisible to both the operator and Claude+MCP, and J-07 finally gets a stored golden replay
script.

## BACKGROUND

Iteration 30 ended GOAL_ACHIEVED with all ten original journeys green. Between that verdict and
this dispatch, the goal-proposer appended **J-11** inside `docs/goal.md`'s `AUTO:journeys` marker
block — currently an UNCOMMITTED working-tree change (`git status --porcelain -- docs/goal.md`
shows ` M docs/goal.md`; confirmed by reading the diff directly), the only mechanism by which new
scope may legally enter this era per the "enhancement loop stays inside its box" anti-goal above.
J-11 is genuinely new: it is absent from `journey-history.json`'s 10-journey ledger, never
attempted. It closes two real, disclosed gaps this era has carried since baseline: (1)
`GET /research/desk/micro/graduation` — already built, already registered in the blueprint's Data
Contract, owner `micro_graduation.py`/`micro_sealed_evaluation.py` — has zero UI readers and zero
MCP tools; (2) J-07 "Graduation" has carried a disclosed golden-gap
(`runs/goal-session-rapid-microscope/state/golden-gaps` lists exactly `J-07`) since it has had no
browser surface a replay script could navigate to.

**This overrides the dispatch line's `evidence` depth recommendation.** That recommendation was
iter-30's own next-step call, computed before J-11 existed and while literally every Target
journey was already `passing` — rule 7 forbids planning an evidence-only iteration once real,
machine-buildable work exists, and J-11 is exactly that.

**Depth: lean, not full.** J-11 is full-stack (backend MCP tool + guard-test extensions, frontend
`/desk` section) but none of the four full-depth escape conditions holds: prior verdict was
GOAL_ACHIEVED (not ESCALATE/REGRESSION); iter-30's `coherence.md` was COHERENCE-PASS; consecutive
lean count is 1 of a cadence-6 threshold (not due); and trigger 4 ("brand-new full-stack journey
... with real Data-contract additions") does not fire because J-11's own Acceptance text
explicitly disclaims one: "no second computation path, no new endpoint, no Data Contract row
added". This is the depth rubric's own named lean example — "a new endpoint plus its UI use" —
here, new UI/MCP *readers* of an already-registered, unchanged endpoint. This deviation (from
`evidence`, not to `full`) is logged to the assumption ledger.

**Anchors verified in the tree today** (re-locate by symbol name, not line arithmetic — these may
drift): the MCP static-path table and `types.Tool` list live in
`apps/backend/app/mcp/__init__.py` (`_STATIC_PATHS["desk_vault"]`, the `desk_vault` `types.Tool`
entry — `desk_graduation` is the next sibling, immediately after both); `EXPECTED_TOOLS` and the
write-verb/arg-shape guards live in `apps/backend/tests/test_mcp_server.py`; the TR-2
join-resistance/inference sweep and the MCP-surface-closure structural test live in
`apps/backend/tests/test_vault.py`; `_PRICE_ARITHMETIC_FIELDS` lives in
`apps/backend/tests/test_desk_ui_guards.py`; the Validation Vault section (`ValidationVaultSection`,
its `<section aria-label="Validation Vault">` wrapper, and the `CollapsibleSection id="validationVault"`
pattern whose `desk-section-expand-validationVault` testid the J-06 golden already clicks) is the
last section in `apps/frontend/app/desk/page.tsx`, immediately before `</main>` — Graduation is the
next sibling, immediately below it (T-11).

**Lessons applied:** T-9 (clean rebuild before browser evidence), T-10 (evidence honesty — no
screenshot ⇒ `unknown`; element-capture for the new section), and T-11 (the new section renders
below shipped ones, reuses no shipped `data-testid`/heading string, is statically swept against
stored replay scripts) all govern this iteration directly, as does iter-25's "re-check the
GROUNDS of a carried-forward premise" (this spec independently confirms the golden-gap and the
zero-MCP-reader state via `state/golden-gaps` and a grep, not by trusting the goal-text claim) and
the blueprint's own iter-15 precedent (an MCP tool is a transport-layer proxy, never a second
Data Contract row).

## IN SCOPE

### Backend
- [ ] `apps/backend/app/mcp/__init__.py`: add `desk_graduation` to `_STATIC_PATHS` (value
      `/research/desk/micro/graduation`) and add its `types.Tool` entry, positioned immediately
      after `desk_vault` in both places (dependency-order sibling rule), matching the existing
      `desk_vault`/`desk_scout`/`desk_walkforward` no-required-param, byte-identical-GET-proxy
      shape exactly.
- [ ] `apps/backend/tests/test_mcp_server.py`: extend `EXPECTED_TOOLS` to the 27-tuple with
      `desk_graduation` immediately after `desk_vault` (guard tests are extended, never edited).
- [ ] `apps/backend/tests/test_desk_ui_guards.py`: extend `_PRICE_ARITHMETIC_FIELDS` with every
      served graduation numeric the new section renders, plus its seeded counter-test.
- [ ] `apps/backend/tests/test_vault.py`: confirm/extend the TR-2 join-resistance sweep and the
      MCP-surface-closure structural test (`test_tr2_the_mcp_surface_is_closed_structurally_not_route_by_route`)
      cover `/research/desk/micro/graduation` now that it has an MCP proxy.

### Frontend
- [ ] `apps/frontend/app/desk/page.tsx`: add a `GraduationSection` component + its
      `<section aria-label="Graduation">`/`<CollapsibleSection id="graduation">` wrapper, rendered
      as the next sibling directly below the Validation Vault `<section>`, fetched lazily on
      expand from `GET /research/desk/micro/graduation` (the same one-fetch-on-toggle pattern
      `ValidationVaultSection` already uses) and rendered verbatim: per family
      `family_root_id`, stage token, full `transitions` history, full `sealed_evaluations`
      history (including permanent failed verdicts), and the ledger's own `chain_verification`
      verdict — no client-side aggregate, derived count, re-ordering, or recomputation. Empty
      real ledger renders the served `message` verbatim (`"No candidates ledgered."`). Read-only:
      no compute button, no POST.

### New user-facing capability
The operator (and Claude via MCP) can now see the Rapid-Microscope funnel's terminal state —
which candidate families have graduated to which stage, their full transition history, and any
permanent sealed-evaluation failures — directly on `/desk`, without reading the ledger file by
hand.

### New information displayed
Per graduation family: `family_root_id`, current stage token
(`exploratory`/`walkforward_survivor`/`sealed_survivor`/`referee_handoff_ready`), full
`transitions` history, full `sealed_evaluations` history (including permanent failed verdicts),
and the ledger's `chain_verification` verdict — all already computed and stored by
`micro_graduation.py`, newly rendered.

### New user actions
None (read-only section; no compute/transition control — graduation transitions remain
non-UI acts per T-8).

### UI surface changes
`/desk` gains one new collapsible section, "Graduation", rendered directly below the shipped
Validation Vault section, in the same visual idiom (dark, dense, terminal-grade) as the other
Rapid Microscope sections.

### Product surface delta
The Rapid Microscope's four-section `/desk` block (Readiness, Scout Ledger, Walk-Forward,
Validation Vault) becomes five sections with Graduation appended at the bottom; the MCP surface
grows from 26 to 27 read-only tools.

### Blueprint conformance
Lives under the existing Information Architecture home `Desk (/desk) → Rapid Microscope` (see
`runs/goal-session-rapid-microscope/state/blueprint.md`), as the fifth section in that
already-registered group. Purely additive — no nav-skeleton change, no reapproval file needed.

### Data-contract additions
None. The "Graduation states + export bundles" row (owner `micro_graduation.py` /
`micro_sealed_evaluation.py`, endpoint `GET /research/desk/micro/graduation`) is already
registered in the blueprint's Data Contract since era baseline and stays completely unchanged —
this iteration adds new READERS (a UI section, an MCP proxy) of that one existing endpoint, never
a second computation path or a second serving route. The blueprint is updated only to register the
new UI/MCP readers under the existing row, matching the file's own iter-15 precedent for MCP-tool
additions.

## OUT OF SCOPE

- Any change to `micro_graduation.py`'s or `micro_sealed_evaluation.py`'s computation, the
  graduation stage vocabulary, or the sealed-pass rule (`SEALED_PASS_RULE_V1`) — this iteration
  is a surface-only wiring of an already-frozen ledger.
- A compute/transition control on the Graduation section — transitions stay non-UI acts (T-8).
- Any PnL ledger append, strategy/profile/candidate registration, or champion-pointer movement.
- Any `Config` field addition or fingerprint movement.
- The optional, non-blocking J-02/J-03 close-up captures and J-05's golden self-text fix named
  in iter-29/30's evaluator notes — unrelated to J-11, not planned this round (rule 5: never
  bundle unrelated work into a single-journey lean spec); may ride passenger only if the
  browser-qa pass below naturally produces them, never as a goal.
- Recording more real tape, revealing/assigning any sealed shard, or running the three pilot
  studies against the real recorded corpus (standing out-of-scope, unchanged).
- Re-opening the two owner-deferred anti-goal items (chain-ledger identity r8; sealed-judge econ
  floor r9) or the four `framework_backlog` items — settled, non-blocking, outside this
  iteration's scope.

## DEFINITION OF DONE

- [ ] J-11 passes via browser-qa-agent: the Graduation section renders below Validation Vault on
      the real store (`"No candidates ledgered."` + `chain_verification`) and, on a
      fixture-scoped rig seeded with one family per stage, renders all four stage tokens, a
      permanent failed sealed verdict, and the referee-spec-revision bundle copy — each with its
      own element screenshot on record.
- [ ] `desk_graduation` MCP tool ships, byte-identical to its GET route; `EXPECTED_TOOLS` is the
      27-tuple with `desk_graduation` immediately after `desk_vault`; the write-verb/arg-shape
      guards pass unweakened.
- [ ] `_PRICE_ARITHMETIC_FIELDS` covers every served graduation numeric with a passing seeded
      counter-test; the TR-2 sweep and the MCP-surface-closure structural test pass with
      `/research/desk/micro/graduation` included.
- [ ] J-07 has a stored golden replay script (`journey-scripts/J-07.json`) asserting a
      Graduation-section string unique to it; `state/golden-gaps` no longer lists `J-07`.
- [ ] No PnL number moves and none is invented: `GET /research/pnl/ledger` and
      `reports/pnl/pnl-history.md` byte-identical before/after, champion pointer still
      `v1`/`default`, both founding rows still `n = 1 < 5`.
- [ ] Required-still-passing journeys (J-01, J-04, J-05, J-06, J-07, J-08, J-09, J-10) remain
      green — deterministic replay for every journey with a stored golden, LLM browser-qa
      fallback for any without one that round.
- [ ] No anti-goal violation introduced; `config_fingerprint` still prints
      `08e471b10130e1e2`; all six `referee_*.py` files still hash byte-identical to the
      iteration-0 listing; every shipped `/`, `/structure`, `/desk` section still renders as
      shipped.
- [ ] Unit tests pass; full backend suite green at a count ≥ the iter-30 baseline (3,491 passed /
      8 skipped) with 0 failures.
- [ ] A `[NEW]`-flagged demo-narrator walkthrough step navigates `/desk` to the new Graduation
      section and shows the served state/empty-state copy on screen, with that step's own
      screenshot actually containing what the narration claims.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-31-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-11 (new — Graduation section, real-store empty state + fixture-scoped 4-stage
  render); J-07 (new golden replay, Graduation-section assertion); J-01, J-04, J-05, J-06, J-08,
  J-09, J-10 (regression, via stored goldens where they exist).
- Unit/integration: `apps/backend/tests/test_mcp_server.py` (EXPECTED_TOOLS 27-tuple, write-verb
  guard, arg-shape guard); `apps/backend/tests/test_desk_ui_guards.py`
  (`_PRICE_ARITHMETIC_FIELDS` extension + counter-test); `apps/backend/tests/test_vault.py`
  (TR-2 sweep, MCP-surface-closure structural test); `apps/backend/tests/test_micro_graduation.py`
  (unchanged, still green — this iteration touches no graduation computation).
- Error cases: the real-store empty ledger (`message: "No candidates ledgered."`) must render,
  never a fabricated row or a client-side placeholder; a malformed/missing graduation payload
  must not crash the section (matches the existing defensive-read pattern the other Rapid
  Microscope sections already use).

Test-first contract:

- TC-1: given the real store's empty graduation ledger, when the `/desk` Graduation section is
  expanded, then it renders the served `message` `"No candidates ledgered."` verbatim beside the
  served `chain_verification` verdict, with an element screenshot on record.
- TC-2: given a fixture-scoped rig seeded with one family per stage (`exploratory`,
  `walkforward_survivor`, `sealed_survivor`, `referee_handoff_ready`), when the Graduation
  section is expanded, then all four stage tokens are visible, a permanent failed sealed verdict
  is shown, and the bundle copy states current-Referee registration of a flow predicate awaits a
  named referee-spec revision.
- TC-3: given the new `desk_graduation` MCP tool is called, when its response is compared to
  `GET /research/desk/micro/graduation`'s own response body, then the two are byte-identical.
- TC-4: given `apps/backend/tests/test_mcp_server.py` is run, then `EXPECTED_TOOLS` is a 27-tuple
  with `desk_graduation` immediately after `desk_vault`, and the write-verb/arg-shape guards pass
  for the new tool.
- TC-5: given `apps/backend/tests/test_desk_ui_guards.py`'s seeded counter-test for the new
  graduation numeric fields in `_PRICE_ARITHMETIC_FIELDS`, when a deliberately-violating
  expression is injected, then the guard test fails as expected (proving it is live, not
  vacuous).
- TC-6: given `apps/backend/tests/test_vault.py`'s TR-2 sweep and
  `test_tr2_the_mcp_surface_is_closed_structurally_not_route_by_route`, when re-run after
  `desk_graduation` is added, then `/research/desk/micro/graduation` is present in
  `research_tool_paths` and `research_tool_paths <= swept` still holds.
- TC-7: given no stored golden exists for J-07 today, when this iteration ends, then
  `runs/goal-session-rapid-microscope/journey-scripts/J-07.json` exists, asserts a
  Graduation-section string unique to J-07, `demo_runner.py --mode verify` passes it, and
  `runs/goal-session-rapid-microscope/state/golden-gaps` no longer lists `J-07`.
- TC-8: given `GET /research/pnl/ledger` and `reports/pnl/pnl-history.md` captured before this
  iteration, when re-checked at the end, then both are byte-identical, the champion pointer is
  still `v1`/`default`, and both founding rows still carry `n = 1 < 5`.
- TC-9: given `Config().config_fingerprint()` and the six `referee_*.py` iteration-0 SHA-256
  listing, when re-checked at the end of this iteration, then the fingerprint prints
  `08e471b10130e1e2` and all six hashes match.
- TC-10: given the full backend suite, when run at the end of this iteration, then it passes at a
  count ≥ 3,491 (the iter-30 baseline) with 0 failures.
- TC-11: given the Required-still-passing journeys' stored goldens (J-01, J-04, J-05, J-06, J-08,
  J-09, J-10 — nine minus J-07/J-11's own fresh goldens), when `demo_runner.py --mode verify`
  runs, then all pass with 0 regressions.
- TC-12: given a `[NEW]`-flagged demo-narrator walkthrough step navigating `/desk` to the
  Graduation section, when its screenshot is captured, then the image actually contains the
  served state/empty-state copy the narration claims (T-10).

## NOTES

- This spec deliberately deviates from the dispatch line's `evidence` depth recommendation (to
  `lean`, not `full`); see BACKGROUND's dedicated paragraph and the matching assumption-ledger
  entry (`iter-31 — goal-decomposer`) for the full reasoning.
- `docs/goal.md`'s J-11 addition is currently an uncommitted working-tree change. This spec does
  not commit it; that stays whatever process (owner or engine) normally commits goal-text changes
  in this session.
- The six previously-open, owner-dispositioned anti-goal findings (r8, r9, four
  `framework_backlog` items) are unaffected by this iteration and are NOT re-litigated — per
  iteration-state's "Do not redo" list.
- If the evaluator judges J-11 was not a legitimate proposer addition (e.g., the "manufacturing a
  low-value journey" anti-goal fires), that is a call for the evaluator/owner, not pre-empted
  here — this spec only builds what J-11's own Acceptance text specifies.
