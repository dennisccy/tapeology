# Goal Iteration 0 — Baseline verification of Era 6 "The Referee"

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** referee
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** yes (no frontend code changes this iteration; browser-qa still loads
  `/desk`, `/`, `/structure` to verify current state per T-9/T-10 — J-07 and J-09 are the
  browser-verifiable targets)
- **Target journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10
- **Required-still-passing journeys:** (none — iteration 0 has no prior recorded journey state)
- **Anti-goal reminders:** (verbatim from `docs/goal.md` § Anti-goals)
  - 1. No execution path, ever — no brokerage/trading API, no order tickets, no live OR paper
    trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is
    the tier-1 guard; new research code adds matching guard tests, never weakens them.)
    *(critical)*
  - 2. No profit claims and no advice — every $ figure is a simulated measurement carrying R,
    n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language,
    no imperative trading cues. *(critical)*
  - 3. Frozen foundations — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
    them, never a mutation of them. *(critical)*
  - 4. Hold-out-only promotion — the champion pointer moves only on a genuine hold-out
    survival through the sweep gate PLUS a valid Referee certificate (this era makes the
    "era-6 statistical gates" clause real). Train-only wins are labeled overfit. Never lower a
    minimum sample size, widen a gate, or pool across feeds/fingerprints to manufacture a
    survivor. *(critical)*
  - 5. No lookahead — every value computed as-of T uses only events/bars fully completed at T.
    *(critical)*
  - 6. Single source of truth — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - 7. Deterministic and seeded — every random draw uses a recorded named seed via per-row
    streams; identical requests reproduce byte-identical results; no wall-clock, no unseeded
    randomness in any research artifact. *(critical)*
  - 8. Read-only MCP — MCP tools remain byte-identical proxies of GET endpoints; nothing on
    the MCP surface can change state. *(critical)*
  - 9. Immutable data — registered datasets and bar series are append-only, checksummed,
    never re-tagged, never deleted, never content-perturbed. Splits are frozen at
    registration. *(critical)*
  - 10. Persistence stays scoped — no ambient recording of live streams; recording/fetching
    is an explicit, logged act. *(critical)*
  - Era-B/B2 anti-goals that remain binding: membership is never a signal; snapshots and
    playbook records are append-only and pinned; every run is an explicit operator act; the
    briefing and the playbook describe, never advise; the demolition stays demolished; the
    ledger never holds orders; the suite stays keyless and hermetic; the fingerprint pin does
    not move; no threshold exists outside its spec and no code path sweeps one; the evidence
    pools one signature; no recorded playbook file is ever rewritten; no second implementation
    of the measurement rail. *(all critical)*
  - Referee-era anti-goals (added, not weakening any rail above):
    - No confirmatory claim outside the gauntlet. A confirmatory verdict exists only for a
      registered hypothesis with an immutable pre-data boundary, a calibrated randomization p,
      a family BH pass at the registered q, session-clustered robustness, and floors met — and
      exactly ONE confirmatory checkpoint per hypothesis, recorded as an append-only snapshot
      that later evaluations can never change (a replication is a new registered hypothesis).
      *(critical)*
    - The historical atlas is exploratory forever. No historical observation is ever served,
      labeled, or counted as forward confirmation; discovery data renders only under its
      exploratory label. *(critical)*
    - CI-inversion is never a p-value. Ordinary bootstrap quantities are uncertainty
      intervals; every p that feeds BH comes from a spec-named null-calibrated randomization
      procedure; the oracle suite guards the distinction. *(critical)*
    - Never shrink the BH denominator. No BH pass may run with m smaller than the family's
      registered planned count; no candidate joins a family retroactively; no unevaluated or
      late-withdrawn candidate is dropped from m — they fold as p=1, never disappear; no
      family's q changes after registration. *(critical)*
    - No gate loosens mid-era. q, floors, targets, K, B, and every eligibility rule are fixed
      at registration; `insufficient_sample` is an answer, never a reason to widen anything.
      *(critical)*
    - The Referee never feeds back. No referee output gates, filters, ranks, or tunes any
      detector, context, screen, or strategy computation (import-ban + source-scan
      guard-tested); the frozen research vocabulary stays frozen. *(critical)*
    - Promotion is certificate-locked. No champion promotion without a valid
      candidate-specific Referee certificate; no bypass flag, env override, or default-allow
      path exists (source-scan guard-tested); a Playbook certificate can never satisfy a
      strategy promotion. *(critical)*
    - No confirmatory output without a verified oracle attestation. The adjudication fold
      never serves a confirmatory verdict from an evaluation whose attestation is missing,
      mismatched, or version-stale — it serves the refusal state with its reason; descriptive
      output never masquerades as confirmatory. *(critical)*
    - No annualized metrics anywhere — the literal string is guard-tested out of research
      payloads. *(critical)*
    - The enhancement loop stays inside its box. The goal-proposer may append journeys ONLY
      inside the `AUTO:journeys` marker block in `docs/goal.md` — it MUST NOT edit
      human-authored journeys, the Anti-goals section, or any other part of that file;
      proposed journeys MUST carry a single-source-of-truth acceptance criterion, keep the
      `default` profile and `v1` byte-identical, respect every rail above, and include a
      `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just to keep the loop
      alive is a failure. *(critical)*
  - Host protection (a physical constraint of the host, not product scope): Host-guard caps
    are law. This host (GEEKOM A7 Max mini-PC) hard-reset five times between 2026-07-20 and
    2026-07-28 under unconfined goal-mode load — instant power/VRM transient trips with
    nothing in the journal; resets #3–#5 struck while tapeology's goal mode ran UNGUARDED
    beside trendora's. When `project-extensions/host-guard/host-guard.env` declares ceilings
    (CPU mask `4-7,12-15` plus BLAS thread caps and memory/task bounds), every heavy path
    respects them: headless engine runs self-wrap under the mask, and interactive pump
    sessions are auto-confined in place by the engine — the engine pauses
    `AWAITING_HOST_GUARD` (resumable) only when confinement cannot be established. Never
    disable, widen, or bypass these caps to make a run faster or a pause go away. *(critical)*

## GOAL

Establish the Era 6 "The Referee" baseline by attempting all ten Must-have journeys
(J-01–J-10) against the current, entirely-unbuilt referee surface and recording each verdict
with concrete evidence, so every later iteration knows exactly what already works (the kept
product, J-10) versus what remains to build (J-01–J-09) instead of assuming it from
`docs/goal.md`'s prose.

## BACKGROUND

This is iteration 0 of a brand-new era opened on `main` at `e875972` today (2026-08-14).
Direct inspection (Glob/Grep, not assumed from prose) confirms: `app/research/` has zero
`referee_*.py` files; `apps/backend/tests/test_mcp_server.py::EXPECTED_TOOLS` has exactly 20
entries (no `desk_referee`/`desk_referee_registry`); `Config().config_fingerprint()`'s pinned
literal `08e471b10130e1e2` is already the value used throughout the existing test suite; no
frontend file references "Referee"; and `docs/referee-statistical-spec.md` (371 lines) exists
as the canonical spec but nothing implements it yet. So J-01 through J-09 are expected to fail
every acceptance check, while J-10 (the kept-product regression sentinel) is the one journey
with real existing content to verify, since Era B2 shipped the kept product (`/`, `/structure`,
`/desk`) GOAL_ACHIEVED on 2026-08-11. Depth is `lean` per the evaluator's binding
recommendation and per baseline mode's own rule — no full trigger applies (zero code changes
this iteration, so no cross-cutting blast radius exists); the iteration's entire value is the
browser-qa step's per-journey verification, not any full-cycle machinery. Target-journey
selection follows the baseline-mode rule (ALL Must-have journeys targeted), not the
`--next`-mode priority rubric, since iteration 0 has no prior journey state to rank against.
`lessons.md` and `assumptions.md` are both empty for this session (first iteration) — nothing
to carry forward yet.

## IN SCOPE

### Backend
- (none — baseline verification only; no code changes this iteration)

### Frontend
- (none — baseline verification only; no code changes this iteration)

### Verification tasks (read-only; this iteration's actual scope)
- [ ] Attempt J-01's acceptance check: `GET /research/desk/referee/evidence` against the
      current backend (expect route absent — `app/research/referee_evidence.py` does not
      exist).
- [ ] Attempt J-02's acceptance check: import `app/research/referee_evidence.py` and look for
      its fixture goldens (expect module absent).
- [ ] Attempt J-03's acceptance check: look for `app/research/referee_stats.py` and
      `tests/test_referee_oracles.py` and run the oracle suite if present (expect both absent).
- [ ] Attempt J-04's acceptance check: `GET /research/desk/referee/nulls` (expect route
      absent — `referee_null.py` does not exist).
- [ ] Attempt J-05's acceptance check: `GET /research/desk/referee/registry` and
      `POST /research/desk/referee/registry/hypotheses` (expect both absent —
      `referee_registry.py` does not exist).
- [ ] Attempt J-06's acceptance check: `GET /research/desk/referee/adjudications` (expect
      route absent — `referee_adjudicate.py` does not exist).
- [ ] Attempt J-07's acceptance check in a real browser: load `/desk` after a clean rebuild
      (`rm -rf apps/frontend/.next`, T-9) and look for a shortlist/registration flow (expect
      absent — screenshot required as evidence per T-10, even for a failing verdict).
- [ ] Attempt J-08's acceptance check: drive a fixture candidate through `pnl_scan._promote`
      and look for `authorize_promotion` anywhere in `app/research/` (expect absent — the
      pre-Era-6 promotion gate is the only one that runs today).
- [ ] Attempt J-09's acceptance check in the same browser pass as J-07: look for the three new
      `/desk` sections (Referee Registry / Referee Adjudications / Referee Runs) and read
      `EXPECTED_TOOLS`'s length (expect 0 of 3 sections present, 20 tools not 22).
- [ ] Attempt J-10's acceptance check: run the full backend suite + engine equivalence, walk
      every kept surface (`/`, `/structure`, every shipped `/desk` section) in a real browser
      after the same clean rebuild, and confirm the fingerprint pin — record the exact
      pass/skip count as the era-open floor future iterations must never fall below.
- [ ] Record each journey's verdict (`passing` / `failing` / `partial`) into
      `journey-history.json` with the concrete evidence (response code, absent-file path, test
      output, or screenshot path) backing each verdict — a verdict without an attempted check
      does not satisfy this.

### New user-facing capability
None — baseline verification only; the product is unchanged.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None. This iteration only records ground truth against the current, unmodified product.

### Blueprint conformance
No new surfaces this iteration. `runs/goal-session-referee/state/blueprint.md` is drafted
this iteration (Information Architecture: Cockpit/Structure/Desk nav unchanged, three new
Desk sections mapped for J-04/J-05/J-06/J-07/J-09; Data Contract: the 7 Era-6 rows mirrored
verbatim from `docs/goal.md` § Product Shape) for iterations 1+ to build into — it is not
consumed by any code this iteration.

### Data-contract additions
None this iteration. The Data Contract for Era 6 (referee evidence, matched-null records,
null-compute/runs, registry, evaluation records/runs, adjudications, promotion-authorization
verdict — see `blueprint.md` § Data Contract) is pre-registered for J-01–J-09 to implement in
later iterations; none of it is built or served yet.

## OUT OF SCOPE

- Any implementation of `referee_evidence.py`, `referee_stats.py`, `referee_null.py`,
  `referee_registry.py`, `referee_adjudicate.py`, or any `/research/desk/referee/*` route —
  all of J-01–J-09's real backend work starts at iteration 1.
- Any change to `desk_playbook*.py`, `desk_forward.py`, `levels.py`, `tradability.py`,
  `pnl_scan.py`, or any other frozen/kept module.
- Any new `Config` field or fingerprint movement.
- Any real hypothesis registration or evaluation run (J-07's operator act) — not yet possible,
  since no registry exists.
- Reading `docs/referee-statistical-spec.md`'s procedure-level detail — that is iteration 1+'s
  J-03 developer work; this iteration only confirms the spec file exists as the canonical
  source.

## DEFINITION OF DONE

- [ ] J-01 through J-10 each attempted against the current codebase and recorded with a
      verdict + evidence in `journey-history.json`.
- [ ] J-07 and J-09 attempted in a real browser after a clean rebuild (T-9); each verdict
      backed by a screenshot per T-10, including the failing verdicts.
- [ ] Full backend suite run once; exact pass/skip count recorded as the era-open floor
      (`docs/goal.md`'s Success Criterion 1 states 2,418 pass / 8 skip at authoring — this
      iteration confirms the live figure).
- [ ] `Config().config_fingerprint()` confirmed == `08e471b10130e1e2`.
- [ ] `apps/backend/tests/test_mcp_server.py::EXPECTED_TOOLS` confirmed at exactly 20 tool
      names.
- [ ] No anti-goal violation introduced.
- [ ] `runs/goal-session-referee/state/blueprint.md` drafted with the Era 6 Information
      Architecture + Data Contract.
- [ ] Dev handoff written at `docs/handoffs/goal-referee-iter-0-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-07 (shortlist/registration flow — expect absent), J-09 (three Referee `/desk`
  sections + MCP tool count — expect absent/20), J-10 (kept-surface walk across `/`,
  `/structure`, every shipped `/desk` section).
- Unit/integration: run the existing full backend suite
  (`cd apps/backend && .venv/bin/python -m pytest tests/`) once and record the exact pass/skip
  totals; no new tests are written this iteration (there is no new code to test).
- Error cases: N/A — no new code paths this iteration; the "error case" being verified is the
  expected 404/absent-module state for J-01–J-06 and J-08's acceptance checks.

Test-first contract:

- TC-1: given the current codebase has no `app/research/referee_evidence.py`, when it is
  imported and `GET /research/desk/referee/evidence` is requested, then both the import fails
  (module not found) and the route returns 404, and J-01 and J-02 are each recorded `failing`
  in `journey-history.json` with that evidence.
- TC-2: given the current codebase has no `app/research/referee_stats.py` or
  `tests/test_referee_oracles.py`, when the oracle suite is looked for, then neither file
  exists and J-03 is recorded `failing` with that absence as evidence.
- TC-3: given the current codebase has no `referee_null.py`, `referee_registry.py`, or
  `referee_adjudicate.py`, when `GET /research/desk/referee/nulls`,
  `GET /research/desk/referee/registry`, and `GET /research/desk/referee/adjudications` are
  each requested, then each returns 404 and J-04, J-05, and J-06 are each recorded `failing`
  with that evidence.
- TC-4: given the current codebase has no `authorize_promotion` function anywhere under
  `app/research/`, when a fixture candidate is driven through `pnl_scan._promote`, then
  promotion proceeds under the pre-Era-6 gate only (no certificate check exists) and J-08 is
  recorded `failing` with that absence as evidence.
- TC-5: given a clean-rebuilt frontend (`rm -rf apps/frontend/.next` then rebuild) and a
  browser navigated to `/desk`, when the page fully loads, then no element with a heading or
  `data-testid` referencing "Referee Registry", "Referee Adjudications", or "Referee Runs" is
  present, a screenshot is captured as evidence, and both J-07 and J-09 are recorded `failing`.
- TC-6: given the same browser pass as TC-5, when the kept surfaces (`/`, `/structure`, every
  shipped `/desk` section) are walked and compared against their Era B2 shipped behavior, then
  each surface's screenshot is captured as evidence and its match/mismatch is recorded in
  `journey-history.json` for J-10 (zero code changed this iteration, so a match is expected —
  but the walk must actually run, never be assumed).
- TC-7: given the current codebase, when `apps/backend/tests/test_mcp_server.py`'s
  `EXPECTED_TOOLS` tuple is read, then it contains exactly 20 entries and neither
  `desk_referee` nor `desk_referee_registry` is present.
- TC-8: given the current codebase, when `Config().config_fingerprint()` is evaluated, then it
  returns exactly `08e471b10130e1e2`.
- TC-9: given the current codebase, when the full backend test suite is run to completion,
  then it reports a fixed pass count and skip count with zero errors, and that exact pair is
  recorded in `iteration-state.md` as the era-open floor J-10 must never fall below in any
  later iteration.
- TC-10: given zero Backend/Frontend code changes are made this iteration, when
  `git diff --stat` is checked against the pre-iteration commit, then it shows no changes
  outside `docs/phases/goal-referee-iter-0.md`, `runs/goal-session-referee/state/blueprint.md`,
  and the goal-mode state/handoff artifacts, and zero anti-goal violations are recorded.
- TC-11: given this iteration's planning step, when
  `runs/goal-session-referee/state/blueprint.md` is read, then it contains an "Information
  Architecture" section with the 3-route nav skeleton and a "Data Contract" section listing
  the 7 Era-6 rows from `docs/goal.md` § Product Shape.
- TC-12: given this iteration has zero Backend/Frontend in-scope items, when the developer
  step runs, then it writes `docs/handoffs/goal-referee-iter-0-dev.md` stating no code changes
  were made and pointing to the journey-verification results as this iteration's deliverable.

## NOTES

- Confirmed independently this iteration (not assumed from `docs/goal.md`'s prose): (a)
  `app/research/` contains zero `referee_*.py` files; (b) `EXPECTED_TOOLS` in
  `test_mcp_server.py` has exactly 20 entries with no referee tools; (c) the fingerprint
  literal `08e471b10130e1e2` is already the pinned value used across existing tests; (d) no
  frontend file references "Referee"; (e) the backend suite collects without error. This
  grounds the expectation that J-01–J-09 will verify `failing` and J-10 will verify at-or-near
  `passing` — but the actual verdicts are the evaluator's call after browser-qa/orchestrator
  execute this spec, not asserted here.
- `docs/referee-statistical-spec.md` (371 lines) is confirmed present and is the binding
  source for J-03–J-06's real implementation starting iteration 1+; this iteration does not
  need its procedure-level content, only confirmation that it exists as the canonical spec.
- Host-guard config confirmed present at `project-extensions/host-guard/host-guard.env`; the
  full backend suite run this iteration is the pre-existing, already-hermetic suite (no new
  heavy compute), so no special host-guard handling beyond the standard wrap is expected —
  flagging per `docs/goal.md`'s Host protection anti-goal for downstream awareness.
- Because this is iteration 0 of a 10-journey natural dependency chain
  (J-01 → J-02 → J-03 → J-04 → J-05 → J-06 → J-07 → J-08 → J-09, with J-10 continuous),
  iteration 1 will very likely target J-01 (and possibly J-02, the two backend-only, no-UI
  journeys that unblock everything downstream) at lean depth — but that choice belongs to
  iteration 1's goal-decomposer dispatch, informed by this iteration's recorded verdicts.
- No entry was added to `runs/goal-session-referee/state/assumptions.md` this iteration — the
  baseline-mode rule set (verify only, target all Must-have journeys) required no ambiguous
  interpretation of `docs/goal.md`.
