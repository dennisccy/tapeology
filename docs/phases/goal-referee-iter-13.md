# Goal Iteration 13 — the readiness fold gets a reader on the Desk page

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** referee
- **Iteration:** 13
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-12
- **Required-still-passing journeys:** J-01, J-02, J-05, J-07, J-09, J-10, J-11
- **Anti-goal reminders:**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an explicit, logged act. *(critical)*
  - **The Referee never feeds back.** No referee output gates, filters, ranks, or tunes any detector, context, screen, or strategy computation (import-ban + source-scan guard-tested); the frozen research vocabulary stays frozen. *(critical)*
  - **No annualized metrics anywhere** — the literal string is guard-tested out of research payloads. *(critical)*
  - **The enhancement loop stays inside its box.** The goal-proposer may append journeys ONLY inside the `AUTO:journeys` marker block above — it MUST NOT edit human-authored journeys, this Anti-goals section, or any other part of this file; proposed journeys MUST carry a single-source-of-truth acceptance criterion, keep the `default` profile and `v1` byte-identical, respect every rail above, and include a `[NEW]`-flagged walkthrough. Manufacturing a low-value journey just to keep the loop alive is a failure. *(critical)*

## GOAL

Give `GET /research/desk/referee/evidence` its first reader anywhere: inside the shipped
"Referee Registry" section on `/desk`, the operator can see WHY each evidence family —
Playbook occurrences and strategy backtest trades — is or isn't ready for confirmatory
statistics, including the honest tick-gate-unmet statement and the no-lookahead forming-bar
caveat, with zero backend change and zero new served value.

## BACKGROUND

Iteration 12 closed GOAL_ACHIEVED with all eleven journeys passing; its evaluator recommended
`Depth: evidence` for the next round because nothing remained but an owed walkthrough
recording. Before this round could dispatch, the goal-proposer appended a new Must-have
journey, J-12, inside `docs/goal.md`'s `AUTO:journeys` block. J-12 closes a real gap: the
Data Contract's canonical owner of per-family readiness (`app/research/referee_evidence.py` /
`GET /research/desk/referee/evidence`, registered since iteration 0) has never had a direct
reader — zero frontend grep hits beyond an unrelated type name, and it is not one of the
22 MCP tools (it stays reachable only through the generic `get_endpoint` `/research/`
allowlist). That means the entire `strategy_trade` block, the tick-gate statement, both
families' `integrity_errors`, and `REFEREE_FORMING_BAR_BASIS_CAVEAT` — the "can embed up to a
full bar-length of information from after the as-of instant" disclosure anti-goal 5 ("No
lookahead") leans on — are invisible in the browser today, visible only to `curl` and to tests.

**Depth: `evidence` does not fit this scope, so this iteration plans `lean` instead — no full
trigger holds.** J-12 requires real, never-before-built frontend code (a new
`fetchRefereeEvidence()`, new response types, two new rendered blocks, a widened arithmetic
guard, a new unowned-frontend-literal guard, a new golden replay script) — work an
`evidence`-depth round cannot perform (it dispatches capture + evaluation only, skipping
developer/reviewer), and my own agent instructions bar planning an evidence-only iteration
for anything but already-passing journeys; J-12 is brand new, not passing. Checking the four
`full` escape conditions in turn: prior verdict was `GOAL_ACHIEVED`, not `ESCALATE`; only 2 of
the 6-iteration hardening cadence have elapsed; this is not a data-model migration (goal.md's
own Step 1: "ZERO backend product diff... no new field, no new value, no new Data Contract
row, no new owner, and no new MCP tool"); and it is not a brand-new full-stack journey (that
trigger needs backend AND frontend work with real Data-Contract additions — J-12 is
frontend-only with explicitly none). None hold, so lean is not a shortfall, it is the correct
call — and it matches precedent: J-11, the most recent sibling journey (extend an
already-registered endpoint's reader inside this exact "Referee Registry" section), shipped
successfully at lean depth in iteration 12. This reasoning is also logged to
`runs/goal-session-referee/state/assumptions.md` (iter-13 entry).

Applicable carried lessons for this round: (iter-10) two clauses that demand DIFFERENT
on-screen states must not share one screenshot — checksum and open each one; this iteration
has exactly that shape (a seeded fixture-rig state and a separate empty-corpus state), so QA
needs two distinct captures, not one reused across both. (iter-12) a screenshot taken at a
deep scroll offset on `/desk` can come back blank even when the target is laid out and
visible — resize the viewport to the page's own `scrollHeight` before capturing. (T-11) new
sections/blocks render below shipped ones, reuse no shipped heading or `data-testid`, and are
statically swept against the stored golden replay scripts — `J-12.json` is new this round,
modeled on `J-11.json`'s shape. (iter-9 rider) a served disclosure string rendered from a
payload must never also exist as a hardcoded frontend literal — apply the same guard shape
used for `REFEREE_STARTER_FAMILY_ID`/`_Q` to `tick_gate_statement`/
`REFEREE_FORMING_BAR_BASIS_CAVEAT`.

## IN SCOPE

### Backend (tests only — zero production diff)

- [ ] `apps/backend/tests/test_desk_ui_guards.py`: widen `_PRICE_ARITHMETIC_FIELDS` with every
  new served `referee_evidence` numeric this component reads (`records`, `distinct_sessions`,
  `signals_at_current_basis`, `dataset_count`, `per_split_counts.train`/`.holdout`,
  `trade_count`) plus a seeded counter-test proving the widened pattern actually fails on
  injected client-side arithmetic over these fields — same "counts, not prices" convention as
  the iter-8/iter-12 additions already in that file.
- [ ] New guard test (place in whichever of `test_referee_evidence.py` /
  `test_referee_registry.py` already owns this shape) asserting the `tick_gate_statement` text
  and `REFEREE_FORMING_BAR_BASIS_CAVEAT` text appear in NO `apps/frontend/**/*.ts`/`*.tsx`
  source file — mirrors the iteration-9 `REFEREE_STARTER_FAMILY_ID`/`_Q` unowned-literal guard
  (`test_referee_registry.py:695-698`).
- [ ] A byte-identity check (golden fixture or direct comparison) proving `referee_evidence()`'s
  served body is unchanged by this iteration's diff.
- [ ] Confirm, do not edit: `test_desk_refresh_chain_guard.py::_EXPECTED_EFFECT_COUNT` stays
  `21`; `test_copy_discipline.py` stays green with the newly-rendered copy included (it already
  globs `app/**/*.tsx`).

### Frontend

- [ ] `apps/frontend/lib/api.ts`: add `fetchRefereeEvidence()` returning
  `{ok: boolean, data: RefereeEvidenceResponse | null, error?: string}`, `GET
  ${API_BASE}/research/desk/referee/evidence` — follow `fetchRefereeShortlist`/
  `fetchRefereeRegistry`'s exact established shape (`lib/api.ts:2073-2119`) verbatim, including
  the same `res.json().detail` error-message fallback and the same
  `"Backend unreachable — is the API running?"` catch-branch message.
- [ ] `apps/frontend/lib/types.ts`: add `RefereeEvidenceResponse` and its two nested block
  types, matching `referee_evidence()`'s exact served shape field-for-field (see Data-contract
  additions below for the full shape — this iteration reads it, adds no field).
- [ ] `apps/frontend/app/desk/page.tsx`: new `refereeEvidenceResult` state, mirroring the
  existing `refereeRegistryResult`/`refereeShortlistResult` declarations (~line 8413-8422).
  Extend the ALREADY-EXISTING `toggleSection`'s `"refereeRegistry"` branch (~line 8499-8501)
  with a third call, `fetchRefereeEvidence().then(setRefereeEvidenceResult)` — no new branch,
  no new `useEffect`, so the page's pinned effect census is untouched.
- [ ] `RefereeRegistrySection` component: new `evidenceResult` prop, passed from the call site
  at `page.tsx:10534-10546`. Render two new dense blocks (tables/text, no cards/gauges) BELOW
  the shipped registered-hypotheses table, reusing the shipped `EmptyState` component
  (`page.tsx:4932` convention) for every honest-absence sentence: **playbook family** —
  `records`, `distinct_sessions`, `signals_at_current_basis`, the `detector_basis` +
  `config_fingerprint` identity, and `stale_basis_dates` rendered verbatim in served order (an
  empty list renders its own `EmptyState`-style sentence, never a blank); **strategy family** —
  `dataset_count`, `per_split_counts.train`/`.holdout`, `trade_count`, the
  `tick_gate_statement` verbatim, and every `basis_caveats` entry verbatim; plus each block's
  own `integrity_errors` disclosure row (empty ⇒ its own honest "no integrity errors"
  sentence). New `data-testid`s and heading strings only — none reused from any shipped
  section.
- [ ] Author a `[NEW]`-flagged demo-narrator walkthrough step list for J-12, modeled on
  `runs/goal-session-referee/journey-scripts/J-11.json`'s shape (`goto /desk` → `click` the
  `desk-section-expand-refereeRegistry` testid → `expect` the strategy family's tick-gate
  sentence and the forming-bar caveat), using only `goto`/`click`/`fill`/`expect`/`wait_for` —
  never `scroll`.
- [ ] Add `runs/goal-session-referee/journey-scripts/J-12.json`, same schema as the existing
  journey scripts, for future deterministic regression replay.

### New user-facing capability

Inside the already-expandable "Referee Registry" section on `/desk`, the operator can now see,
without `curl` or MCP, exactly how much Playbook and strategy evidence exists for the Referee
to reason about, and the two honest caveats that gate confirmatory use of the strategy family
(the tick-gate-unmet statement and the no-lookahead forming-bar disclosure).

### New information displayed

Playbook family: records, distinct sessions, signals pooled at the current detector basis, the
detector-basis + config-fingerprint identity, and any stale-basis dates (or an honest "none"
line). Strategy family: dataset count, per-split (train/holdout) counts, trade count, the
tick-gate statement, and every basis caveat (today, the Card-6.4 forming-bar lookahead
disclosure). Both blocks: an integrity-errors disclosure row (or an honest "none" line).

### New user actions

None. This is a pure additional read inside a section that is already expandable; no new
button, form, or control is added.

### UI surface changes

Two new dense text/table blocks appended below the shipped registered-hypotheses table, inside
the existing "Referee Registry" `CollapsibleSection` on `/desk`. No new page, no new nav entry;
no shipped row, column, heading, or `data-testid` moves.

### Product surface delta

The forming-bar no-lookahead caveat and the tick-gate-unmet statement — already computed and
served since earlier iterations, but visible only to `curl`/tests until now — become visible
to a human operator in the browser for the first time.

### Blueprint conformance

`/desk` → **Referee Registry** — the existing Information Architecture row already shared by
J-05/J-07/J-11; no new page, no new nav section. `runs/goal-session-referee/state/blueprint.md`
is updated this iteration (additive edit): the J-01 row's "Canonical home" cell now reads
`/desk → **Referee Registry**` instead of the bare endpoint, reflecting that the endpoint gains
its first direct UI reader. This is not a nav-skeleton change, so no
`blueprint.reapproval-requested` file is written.

### Data-contract additions

None. This iteration reads the ALREADY-registered Data Contract row "Referee evidence coverage
+ per-family readiness" (owner `app/research/referee_evidence.py`, endpoint `GET
/research/desk/referee/evidence`) verbatim — zero new field, zero new value, zero new owner,
zero new endpoint, zero new MCP tool. For the developer's exact field shape to bind
client-side (already served, confirmed by reading the live source this iteration):

```
GET /research/desk/referee/evidence ->
{
  playbook_occurrence: {
    detector_basis: string,
    config_fingerprint: string,
    records: int >= 0,
    distinct_sessions: int >= 0,
    signals_at_current_basis: int >= 0,
    per_setup_side: [{setup: string, side: string, n: int, n_sessions: int}, ...],
    stale_basis_dates: [{session_date: string, record_detector_basis: string}, ...],
    integrity_errors: [string, ...]
  },
  strategy_trade: {
    dataset_count: int >= 0,
    per_split_counts: {train: int >= 0, holdout: int >= 0},
    trade_count: int >= 0,
    tick_gate_met: boolean,
    tick_gate_statement: string,
    basis_caveats: [string, ...],
    integrity_errors: [string, ...]
  }
}
```

`referee_evidence()`'s served body (`apps/backend/app/research/referee_evidence.py:358-372`)
must stay byte-identical before and after this iteration's diff (golden-diffed).

## OUT OF SCOPE

- Any change to `app/research/referee_evidence.py` or any other `app/research/referee_*.py`
  production module — byte-identical, proven by `git diff`.
- Any new Data Contract row, new served field, or new MCP tool (stays exactly 22 —
  `get_endpoint`'s existing generic `/research/` allowlist already reaches this endpoint).
- The shipped shortlist table and the shipped registered-hypotheses table already inside
  "Referee Registry" — neither is touched.
- Referee Adjudications and Referee Runs sections — untouched this iteration.
- Walkthrough CAPTURE. Lean depth dispatches no demo step; the script is authored (see
  Frontend scope) but the recording itself rides `evidence_makeup`, exactly as J-11's did in
  iteration 12 — this is not a product gap.
- Fixing the shared demo-narrator recorder's inability to play a `scroll` action
  (`incredible_auto_dev/.../demo_runner.py`) — vendored framework tooling, a human/
  finalization item, not this project's product code.
- The four small carried hardening items from prior evaluator recommendations (adding the four
  Referee storage folders to the store-scope guard; a certificate with no name at all matching
  instead of failing; a plain dash instead of a clear word on a failed second fetch; a stale
  `19/7/1` comment) — unrelated surfaces to J-12; carried forward, not bundled in here.
- Committing changed files — human-owned.
- Exercising any Referee write button/control (null-build trigger, evaluate trigger, hypothesis
  registration) during development or QA — those perform real irreversible append-only writes;
  this journey is a pure read and QA must stay on read-only navigation.

## DEFINITION OF DONE

- [ ] J-12 passes via browser-qa-agent — both the seeded fixture-rig state and a separate
  empty-corpus state, each with its own screenshot
- [ ] Required-still-passing journeys (J-01, J-02, J-05, J-07, J-09, J-10, J-11) remain green —
  deterministic replay + LLM fallback, mechanically verified
- [ ] No anti-goal violation introduced — zero backend diff, fingerprint
  `08e471b10130e1e2` unchanged, 22-tool MCP contract unchanged, zero client-side arithmetic on
  any new served numeric, no profit/advice/prediction phrasing in the new copy
- [ ] Unit tests pass; no regressions — full backend suite green, at least 2,695 collected (the
  iteration-12 baseline), 0 failed, no test removed or weakened
- [ ] Dev handoff written at `docs/handoffs/goal-referee-iter-13-dev.md`

## TESTING REQUIREMENTS

- Browser: J-12 on two distinct backend states — (1) the standard seeded fixture rig (already
  used for J-05/J-07/J-09/J-11), proving the hand-computed non-empty counts and the
  string-for-string `tick_gate_statement`/`basis_caveats` match; (2) a clean/empty-corpus rig
  (zero playbook records, zero datasets/backtests), proving the honest all-zero/absent state —
  do NOT reuse one screenshot for both (iter-10 lesson). Resize the viewport to the page's own
  `scrollHeight` before capturing (iter-12 lesson) rather than scrolling. In the SAME pass as
  capture (1), sweep every other shipped `/desk` section (including the shipped shortlist and
  registered-hypotheses tables, Referee Adjudications, Referee Runs, and every Playbook
  section) to confirm nothing shipped moved. Run `assert_scoped_qa_backend.py` first, as
  established in this session, and never click a Referee write control.
- Deterministic replay: J-01, J-02, J-05, J-07, J-09, J-10, J-11 against their stored golden
  scripts (or their own named backend test module for the keyless/backend-only ones); new
  `journey-scripts/J-12.json` added this iteration for future rounds.
- Unit/integration: full backend suite (baseline 2,695 collected / 2,687 passed / 8 skipped,
  must not shrink); the two new/widened guard tests named in Backend scope; a byte-identity
  check on `referee_evidence()`'s served body; `test_copy_discipline.py`;
  `test_desk_refresh_chain_guard.py`'s `_EXPECTED_EFFECT_COUNT == 21` assertion stays passing
  unedited; `test_mcp_server.py::EXPECTED_TOOLS` stays exactly 22 names.
- Error cases: backend unreachable during the fetch shows the shipped
  `"Backend unreachable — is the API running?"` message (mirrors every sibling fetch helper); a
  non-200 response from `/evidence` shows the shipped `res.json().detail`-or-fallback error
  string, never a blank panel or an unhandled exception.

Test-first contract — TC- scenarios:

- TC-1: given the seeded fixture rig's non-empty playbook corpus, when the operator expands
  "Referee Registry" on `/desk`, then the playbook family block shows `records`,
  `distinct_sessions`, and `signals_at_current_basis` each numerically equal to the same
  request's own `GET /research/desk/referee/evidence` response body.
- TC-2: given that same rig, when the playbook family block renders, then its `detector_basis`
  and `config_fingerprint` identity line matches the endpoint's own served values exactly.
- TC-3: given a fixture whose playbook corpus contains at least one stale-basis session date,
  when the playbook family block renders, then every `stale_basis_dates` entry
  (`session_date` + `record_detector_basis`) renders verbatim, matching the endpoint's own list.
- TC-4: given a fixture whose playbook corpus contains zero stale-basis dates, when the
  playbook family block renders, then it shows its own honest "no stale basis dates" sentence
  rather than a blank area.
- TC-5: given the seeded fixture rig's dataset/journal stores, when the strategy family block
  renders, then `dataset_count`, `per_split_counts.train`, `per_split_counts.holdout`, and
  `trade_count` each equal the endpoint's own served integers.
- TC-6: given that same rig, when the strategy family block renders, then the on-screen
  `tick_gate_statement` text is byte-identical to that same request's own
  `GET /research/desk/referee/evidence` response string (compared string-for-string in the
  test, never against a re-typed literal).
- TC-7: given that same rig, when the strategy family block renders, then every
  `basis_caveats` entry (today exactly the Card-6.4 forming-bar caveat) renders byte-identical
  to the endpoint's own served string.
- TC-8: given a fixture whose playbook store or dataset store carries a corrupt/unreadable
  record, when either family block renders, then its own `integrity_errors` row lists the
  error(s) verbatim; given zero integrity errors, then the row shows its own honest "no
  integrity errors" sentence instead of being blank.
- TC-9: given a SEPARATE clean/empty-corpus backend (zero playbook records, zero datasets,
  zero backtests), when the Referee Registry section is expanded, then both family blocks
  render an honest all-zero/absent state (explicit zero counts + the tick-gate-unmet sentence)
  rather than a blank area, a spinner, or a 404/error path — captured as its OWN distinct
  screenshot, not reused from TC-1..TC-7's rig.
- TC-10: given the `/desk` page already loaded and idle, when the operator opens "Referee
  Registry" for the first time, then exactly one `GET /research/desk/referee/evidence` request
  fires (from the existing `toggleSection("refereeRegistry")` branch), and
  `test_desk_refresh_chain_guard.py::_EXPECTED_EFFECT_COUNT` stays `21` — page load itself
  issues zero requests and computes nothing.
- TC-11: given the shipped source tree, when a guard test greps every
  `apps/frontend/**/*.ts`/`*.tsx` file, then neither the `tick_gate_statement` sentence's
  distinctive text nor `REFEREE_FORMING_BAR_BASIS_CAVEAT`'s distinctive text appears in any
  frontend source file — both reach the DOM only from the runtime payload.
- TC-12: given a seeded counter-fixture that injects client-side arithmetic over any of the new
  served numerics (e.g. `records + distinct_sessions` computed in a rendered expression), when
  the widened `_PRICE_ARITHMETIC_FIELDS` regexp runs against it, then the counter-test fails
  the build (proving the guard actually catches the injected arithmetic, not just that it
  passes on unmodified source).
- TC-13: given `apps/frontend/.next` freshly rebuilt (T-9) and the backend running on the
  seeded fixture rig, when the browser navigates to `/desk` and expands "Referee Registry",
  then a screenshot shows both new blocks with every value matching that backend's own served
  `/research/desk/referee/evidence` body exactly, AND every other shipped `/desk` section
  (screen history, forward returns, refresh chain, briefing, skipped, runs/pins/compare/
  provenance, every Playbook section, the shipped shortlist + registered-hypotheses tables,
  Referee Adjudications, Referee Runs) renders exactly as shipped in the same pass.
- TC-14: given the backend running before and after this iteration's frontend-only diff, when
  `Config().config_fingerprint()` is printed, then it reads `08e471b10130e1e2` both times, and
  `git diff` over every `app/research/referee_*.py` module, `desk_playbook*.py`,
  `desk_forward.py`, `levels.py`, `tradability.py`, and `pnl_scan.py` is empty.
- TC-15: given the PnL ledger and champion pointer files before this iteration, when they are
  SHA-256 hashed again after, then both hashes are byte-identical (no new ledger row appended),
  and the `default`-profile equivalence test passes.
- TC-16: given the full backend test suite, when it runs after this iteration, then it collects
  at least 2,695 tests (iteration-12 baseline), no previously-passing test fails, and no test
  is removed or weakened.
- TC-17: given a stored regression-replay golden script for J-12
  (`journey-scripts/J-12.json`: `goto /desk` → `click`
  `desk-section-expand-refereeRegistry` → `expect` a new, non-shipped heading/testid unique to
  this iteration), when the deterministic replay runs, then it matches first-visible text with
  zero collision against any shipped `data-testid` or heading string.
- TC-18: given `apps/backend/tests/test_mcp_server.py`, when `EXPECTED_TOOLS` is parsed after
  this iteration, then it still names exactly 22 tools — no new tool added.

## NOTES

- Assumption logged: `runs/goal-session-referee/state/assumptions.md` (iter-13 entry) records
  the depth-recommendation reasoning above (`evidence` recommended → `lean` planned) in full,
  for the evaluator's benefit.
- `runs/goal-session-referee/state/blueprint.md` is updated this iteration (additive-only): the
  J-01 Information Architecture row's home cell now names `/desk → **Referee Registry**`
  instead of the bare endpoint, plus a trailing iter-13 note explaining the zero-Data-Contract-
  change reasoning. No `blueprint.reapproval-requested` file is written (not a nav-skeleton
  change).
- Human-owned, non-blocking, carried forward unchanged from iteration 12: this session's prior
  rounds are already committed (working tree was clean at this iteration's start); the shared
  demo-narrator recorder still cannot play `scroll`, so the era's video walkthrough remains
  outstanding pending a framework-level fix outside this project; the four small carried
  hardening items listed under Out of Scope; and, from iteration 2 and outside this project,
  the unrelated trendora backend on port 8255 has still not been restarted.
- Time-budget context: this session's evaluator has flagged wall-clock budget pressure in
  multiple prior rounds (iterations 7, 9, and again per iteration 12's own budget-breached
  flag). Keeping this iteration to a single, narrow, frontend-only journey at lean depth is
  deliberate — it should complete well inside budget and leaves nothing ambiguous to cut.
