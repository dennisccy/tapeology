# Goal Iteration 10 — The Referee's last two Desk panels, the 22-tool connector, and a closed certificate-evidence gap

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** referee
- **Iteration:** 10
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior iteration's verdict (iter-9) was ESCALATE, which mandates full
  depth with no exceptions; reinforced by trigger 1 in substance (this round changes two
  protective, re-derive-once-with-rationale guard counters — `_EXPECTED_EFFECT_COUNT` and
  `_PRICE_ARITHMETIC_FIELDS` — and needs real browser evidence for three new panels), but the
  binding reason is the mandatory ESCALATE rule.
- **Frontend Present:** yes
- **Target journeys:** J-09, J-10
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07, J-08
- **Anti-goal reminders:**
  - **Promotion is certificate-locked.** No champion promotion without a valid
    candidate-specific Referee certificate; no bypass flag, env override, or default-allow
    path exists (source-scan guard-tested); a Playbook certificate can never satisfy a
    strategy promotion. *(critical)*
  - **No confirmatory output without a verified oracle attestation.** The adjudication fold
    never serves a confirmatory verdict from an evaluation whose attestation is missing,
    mismatched, or version-stale — it serves the refusal state with its reason; descriptive
    output never masquerades as confirmatory. *(critical)*
  - **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on
    the MCP surface can change state. *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **The historical atlas is exploratory forever.** No historical observation is ever served,
    labeled, or counted as forward confirmation; discovery data renders only under its
    exploratory label. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
    them, never a mutation of them. *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R,
    n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language,
    no imperative trading cues. *(critical)*
  - **Host-guard caps are law.** This host (GEEKOM A7 Max mini-PC) hard-reset five times between
    2026-07-20 and 2026-07-28 under unconfined goal-mode load. When
    `project-extensions/host-guard/host-guard.env` declares ceilings (CPU mask `4-7,12-15` plus
    BLAS thread caps and memory/task bounds), every heavy path respects them. Never disable,
    widen, or bypass these caps to make a run faster or a pause go away. *(critical)*

## GOAL

An operator opens `/desk` and sees the Referee's last two panels — every registered
hypothesis's verdict with full provenance (Referee Adjudications), and live compute controls
with run history for null-builds and evaluations (Referee Runs) — while the Claude connector
gains read-only proxies of both as its 21st and 22nd tools; alongside this, a promotion
certificate can no longer honestly claim evidence it was not actually minted from.

## BACKGROUND

Iteration 9's verdict was ESCALATE, which this framework's own rule makes binding: this round
must run at full depth, no exceptions. It is also the evaluator's own explicit next-step
recommendation — J-09 is the one remaining build item (only the Referee Registry section of its
three exists today; `EXPECTED_TOOLS` is still the 20-tuple), and J-10's era-end clauses
(three Referee sections + 22 tools) are structurally gated on it, so both close together in the
same browser pass. Four small items ride inside this round exactly as the prior evaluator asked,
rather than becoming their own iterations: closing the still-open MINOR anti-goal entry (a
strategy-family certificate's declared candidate was never checked against the evidence it was
minted from — reproduced end-to-end by the iter-9 evaluator), the coherence-audit's stale
"unwired" docstring advisory, making the no-bypass scan's own can-fail proof exercise the real
scan instead of a hand-typed string, and deleting a duplicated test assertion. Lessons applied:
iter-9's own lesson ("a gate that compares PINS is not the same as a gate that validates
EVIDENCE") drives the rider-1 design below; iter-7's lesson (an append-only write side needs the
same gate as its read side) and iter-6's lesson (validate every input a derived value is derived
from, not just its name-alike field) both argue against leaving this open a second round now that
full-depth budget is available; iter-8's lesson (the fixture rig can structurally hide arithmetic
defects) is a reminder to hand-check any newly-rendered numeric, not just screenshot it. Target
selection follows the priority rubric without deviation: J-09 is the sole remaining failing
journey and the unblocker for J-10 (rule 3); J-10 rides as a co-target because the SAME full
browser pass this round requires for J-09 is also exactly J-10's own kept-product walk.

## IN SCOPE

### Backend

- [ ] `apps/backend/app/mcp/__init__.py`: add `desk_referee` → `/research/desk/referee/adjudications`
  and `desk_referee_registry` → `/research/desk/referee/registry` to `_STATIC_PATHS` (no
  selector arguments — both are already no-required-param GET endpoints, matching every other
  static-path tool's shape).
- [ ] `apps/backend/tests/test_mcp_server.py`: grow `EXPECTED_TOOLS` to the 22-tuple; byte-identity
  and honest-error tests for both new tools in empty AND populated fixture states.
- [ ] `apps/backend/app/research/referee_adjudicate.py` (rider 1 — closes the iter-9-recorded MINOR
  anti-goal entry): `_pool_strategy_trades` gains an optional `candidate: {"strategy_id", "profile"}
  | None` filter matched against the SAME `strategy_id`/`profile` fields `backtests.py`'s result
  block already stamps on every journal record (no new field, no second identity join, no change
  to the Δ_d formula/permutation frame/floors). `run_evaluation_and_record`'s strategy-family
  branch passes `certificate_mint["candidate"]` through it ONLY when `certificate_mint` is
  supplied (the only path that can ever mint a certificate — still zero production callers this
  era); `certificate_mint=None` (every existing route/CLI caller, every monitoring evaluation)
  keeps pooling whole-corpus and unfiltered, byte-identical to today. See
  `state/assumptions.md` iter-10 entry.
- [ ] `apps/backend/app/research/referee_adjudicate.py` (rider 2): update the module docstring
  (`:6`) and the `authorize_promotion` section header/docstring (`:1720`, `:1731-1732`) to drop
  "unwired this iteration" and state it is wired into `pnl_scan._promote` as of iteration 9.
- [ ] `apps/backend/tests/test_pnl_scan.py` (rider 3): replace
  `test_no_bypass_guard_can_fail_on_a_seeded_violation`'s hand-typed-string check (~line 1238)
  with a real exercise of the actual scan logic (refactor the scan into a reusable
  function/helper both the production lint test and this can-fail test call) against a seeded,
  mutated copy of the scanned source — so the test genuinely fails if the scan itself were
  gutted.
- [ ] `apps/backend/tests/test_referee_registry.py` (rider 4): delete the duplicate `S-5`
  assertion (~line 874, an exact repeat of the line above it); no behavior change.
- [ ] `apps/backend/tests/test_desk_ui_guards.py`: extend `_PRICE_ARITHMETIC_FIELDS` (+ seeded
  counter-tests) to cover every referee numeric newly rendered by the Adjudications and Runs
  sections (BH `k_star`/`m`, coverage counts, progress `{done,total}`, etc.), following the
  iter-7/iter-8/iter-9 precedent already in the file.
- [ ] `apps/backend/tests/test_desk_refresh_chain_guard.py`: re-derive `_EXPECTED_EFFECT_COUNT`
  (and re-check `_EXPECTED_INTERVAL_COUNT`/`_EXPECTED_TIMEOUT_COUNT`) exactly once, with the
  mandatory rationale paragraph, to match the two new sections' own deferred-fetch/compute-
  trigger effects; the no-mount-trigger scan itself stays byte-unmodified.
- [ ] `tests/test_copy_discipline.py`: extend lexicon coverage for the two new sections' copy if
  new strings require it (no weakening of any existing check).

### Frontend

- [ ] `apps/frontend/app/desk/page.tsx`: add the "Referee Adjudications" `CollapsibleSection`
  (verdict chips in the exact vocabulary tokens + provenance lines: evaluation basis hash, spec
  ids, seeds, attestation pass/fail; the served `REFEREE_REGISTER` disclosure rendered verbatim)
  directly below the existing Referee Registry section, following its established deferred-fetch
  contract (`sectionReadIssuedRef`/`toggleSection`).
- [ ] `apps/frontend/app/desk/page.tsx`: add the "Referee Runs" `CollapsibleSection` (null-build
  and evaluation compute controls with live progress + cancel, plus both run ledgers) below the
  Adjudications section, following the page's own shipped compute-manager client pattern
  (single-flight, poll, cancel) already used for the page's other computes.
- [ ] `apps/frontend/lib/api.ts` / `apps/frontend/lib/types.ts`: typed fetchers/types for
  `GET .../adjudications`, `GET .../nulls/runs`, `GET .../evaluate/runs`, and the
  `POST/GET/POST-cancel .../nulls/compute` + `.../evaluate` pairs — established style, zero
  client-side derivation of any verdict or number.
- [ ] New `data-testid`s only (T-11); static sweep of the two new sections against the stored
  golden replay scripts.
- [ ] QA fixture setup (fixture-scoped rig only, never the operator's real store): seed one
  hypothesis whose adjudication snapshot carries a populated `fragility_triggers` list
  (verdict `fragile`) and one whose stored attestation fails re-verification at fold time
  (`confirmatory_output_refused: true`), so the populated-state screenshot can show both
  required vocabulary states alongside the existing `pending_forward_confirmation`/`registered`
  ones.

### New user-facing capability

An operator can now see every registered hypothesis's verdict (with its exact vocabulary chip,
refusal reason when refused, and full provenance) on `/desk`, and can trigger, watch live
progress on, and cancel null-builds and evaluations with a visible run history — completing the
Referee's on-screen presence this era promised.

### New information displayed

Verdict chips (`registered` / `pending_forward_confirmation` / `insufficient_sample` /
`fragile` / `no_evidence` / `corroborated` / `basis_retired`); each entry's
`confirmatory_output_refused` state and `refusal_reason` when refused; `evaluation_basis` hash,
null/test-spec ids, seed identity, and attestation pass/fail per entry; the served
`REFEREE_REGISTER` disclosure text; null and evaluation run ledgers (`run_id`, `state`,
`started_at`, `finished_at`, `progress {done,total}`, `error`).

### New user actions

Expand/collapse the two new sections; trigger a null build for a hypothesis's null spec; trigger
an evaluation for a hypothesis; cancel an in-flight null build or evaluation.

### UI surface changes

Two new collapsible panels on `/desk`, rendered directly below the existing Referee Registry
panel and below every shipped section (T-11); no other `/desk` section, column, or route
changes.

### Product surface delta

`/desk` gains its final two Referee panels (Adjudications, Runs), completing the three-section
Referee surface this era's Product Shape names; the Claude MCP connector grows from 20 to 22
read-only tools.

### Blueprint conformance

Desk → **Referee Adjudications** (blueprint.md's pre-registered J-06 IA row) and Desk →
**Referee Runs** (blueprint.md's pre-registered J-04 IA row) — both homes already exist; no
nav-skeleton change, no `blueprint.reapproval-requested` needed.

### Data-contract additions

None. Every value this iteration renders (registry, adjudications, null/evaluation run ledgers)
is an ALREADY-REGISTERED Data Contract row (blueprint.md iter-0/4/5/6/7/8/9 notes); J-09 is
their first UI reader and MCP proxy, computing nothing new — zero client-side arithmetic or
verdict derivation. The rider-1 pooling fix changes which already-stored records are ELIGIBLE
INPUT to an existing computation at certificate-mint time; it adds no new served field, owner,
or endpoint.

## OUT OF SCOPE

- Wiring `journal_store`/`certificate_mint` into any production route or CLI flag — the mint
  stays reachable only by an explicit caller supplying both (unchanged from J-08); rider 1 only
  narrows what gets pooled when a caller already does that.
- Any change to `referee_stats.py`'s statistical math, the Δ_d formula, the permutation frame,
  BH, or any floor/constant (T-1) — rider 1 is an input-eligibility fix, not a procedure change.
- Any new backend Data-Contract row, computing module, or endpoint — all three sections and
  both new MCP tools proxy already-built J-04/J-05/J-06/J-08 endpoints verbatim.
- The Card 6.4 forming-bar fix (explicit goal.md Non-Goal, deferred to a future era).
- Any real operator registration/evaluation/null-build against the operator's actual
  `.data/` store — computes exercised during this iteration's own build/QA work run only
  against the fixture-scoped rig.
- Any fingerprint epoch movement or new `Config` field.
- Any change to a shipped `/desk` section, column, or behavior outside the two new sections
  landing below everything shipped.

## DEFINITION OF DONE

- [ ] J-09 passes via browser-qa-agent — three `/desk` Referee sections (Registry / Adjudications
  / Runs) render honest empty states after a clean rebuild (screenshot); a populated fixture
  state shows a verdict chip per vocabulary state including one `fragile` and one
  refused-attestation entry (screenshot); an in-flight second evaluation trigger is refused
  single-flight (screenshot); every shipped `/desk` section renders exactly as shipped in the
  same pass.
- [ ] MCP surface advertises exactly 22 tools; `desk_referee`/`desk_referee_registry` are
  byte-identical to their curl equivalents in both empty and populated fixture states.
- [ ] J-10 passes via browser-qa-agent — full kept-product browser walk (cockpit, structure,
  every shipped desk section) plus the three Referee sections, screenshotted; full backend
  suite green; `Config().config_fingerprint()` prints `08e471b10130e1e2`; collected-test count
  is at least iteration 9's own 2,678.
- [ ] Required-still-passing journeys J-01–J-08 remain green (deterministic replay + LLM
  fallback where no golden exists).
- [ ] No anti-goal violation introduced; the open MINOR "certificate evidence identity" entry
  (`journey-history.json`, recorded iter-9) is closed by the rider-1 fix and re-verified.
- [ ] Extended guard tests green: `_PRICE_ARITHMETIC_FIELDS`, `_EXPECTED_EFFECT_COUNT` (with its
  rationale paragraph present), `EXPECTED_TOOLS`, copy-discipline lexicon, and the no-bypass
  scan's own real can-fail proof.
- [ ] The coherence-audit advisory (stale "unwired" docstring on `authorize_promotion`) is
  closed.
- [ ] The duplicate assertion in `test_referee_registry.py` is removed.
- [ ] Unit tests pass; no regressions; full suite green.
- [ ] Dev handoff written at `docs/handoffs/goal-referee-iter-10-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-09 (all three `/desk` Referee sections, empty and populated fixture states, the
  single-flight refusal); J-10 (full kept-product walk: cockpit `/`, `/structure` pinned-AAPL
  Load, every shipped `/desk` section, plus the three Referee sections).
- Unit/integration: `_pool_strategy_trades`'s new candidate filter (matched / unrelated /
  default-`None` cases); `_mint_strategy_certificate`'s refusal path when pooled evidence does
  not match the named candidate; MCP `desk_referee`/`desk_referee_registry` byte-identity in
  both fixture states; `_PRICE_ARITHMETIC_FIELDS`/`_EXPECTED_EFFECT_COUNT`/`EXPECTED_TOOLS`/
  copy-discipline guard tests; the no-bypass can-fail proof exercising the real scan; run
  single-flight refusal.
- Error cases: a second evaluation-compute POST while one is already in flight for the same
  hypothesis is rejected with no duplicate run record created; a candidate-mismatched mint
  attempt (TC-13) mints nothing and raises no unhandled exception; a `desk_referee`/
  `desk_referee_registry` MCP call against a store containing an integrity-broken hypothesis
  file still returns the endpoint's own honest `integrity_errors` disclosure rather than
  erroring.

Test-first contract:

- TC-1: given a fixture-scoped backend with zero registered hypotheses and a clean `/desk`
  rebuild, when an operator expands "Referee Adjudications", then the panel renders the honest
  empty-state text `"No hypotheses registered."` and shows no verdict chip, captured in a
  screenshot.
- TC-2: given the fixture-scoped backend seeded with one hypothesis whose adjudication snapshot's
  stored attestation fails re-verification, when an operator expands "Referee Adjudications",
  then that entry's verdict chip reads `insufficient_sample`, `confirmatory_output_refused` is
  true, and the rendered refusal text contains "the checkpoint evaluation's oracle attestation is
  missing, mismatched, or version-stale -- confirmatory output is refused", captured in a
  screenshot.
- TC-3: given the fixture-scoped backend seeded with one hypothesis whose adjudication snapshot
  carries a non-empty `fragility_triggers` list, when an operator expands "Referee Adjudications",
  then that entry's verdict chip reads `fragile`, captured in the same populated screenshot as
  TC-2.
- TC-4: given the populated Adjudications panel from TC-2/TC-3, when it renders, then it also
  shows the exact `REFEREE_REGISTER` disclosure text served by `GET
  /research/desk/referee/adjudications` and, per entry, its `evaluation_basis` hash,
  `null_spec_id`/`test_spec_id`, seed identity, and attestation pass/fail state — every value
  read verbatim from the response body with zero client-side computation.
- TC-5: given a fixture-scoped backend with zero recorded null/evaluation runs, when an operator
  expands "Referee Runs", then the panel renders an honest empty run-ledger state for both null
  builds and evaluations, captured in a screenshot.
- TC-6: given the "Referee Runs" panel, when an operator clicks the null-build compute trigger
  for a registered hypothesis's null spec, then a `POST /research/desk/referee/nulls/compute`
  call starts a run, the panel polls and renders live `{done, total}` progress without a page
  reload, and a completed run appears in the null run ledger with `state: "completed"`.
- TC-7: given the "Referee Runs" panel, when an operator clicks the evaluation compute trigger
  for a registered hypothesis, then a `POST /research/desk/referee/evaluate` call starts a run
  and the panel polls and renders live progress.
- TC-8: given an evaluation run already in flight for a hypothesis, when the operator triggers a
  second evaluation for the SAME hypothesis before the first completes, then the second request
  is refused single-flight (no second run record is created) and the refusal is visibly
  rendered, captured in a screenshot.
- TC-9: given the populated Runs panel, when it renders a completed or cancelled run, then its
  ledger row shows `run_id`, `state`, `started_at`, `finished_at`, and `error` (when present)
  read verbatim from `GET .../nulls/runs` / `GET .../evaluate/runs`.
- TC-10: given the same browser session as TC-1–TC-9 after the T-9 clean rebuild, when the
  operator walks cockpit `/`, `/structure` (pinned-AAPL Load), and every shipped `/desk` section
  (screen history, forward returns, refresh chain, briefing, skipped, runs/pins/compare/
  provenance, all Playbook sections with context columns/filters/cohort views), then every one
  renders exactly as shipped, each captured in a screenshot.
- TC-11: given the running backend, when the MCP tool list is requested, then it advertises
  exactly 22 tools including `desk_referee` and `desk_referee_registry`, and
  `apps/backend/tests/test_mcp_server.py::EXPECTED_TOOLS` is a 22-tuple.
- TC-12: given the fixture-scoped backend in both its empty (TC-1/TC-5) and populated
  (TC-2/TC-3) states, when `desk_referee` is invoked, then its JSON is byte-identical to
  `curl GET /research/desk/referee/adjudications`'s own response in the same state; same for
  `desk_referee_registry` against `GET /research/desk/referee/registry`.
- TC-13: given 12 planted backtest trades all recorded under `strategy_id="v1", profile="default"`,
  when `run_evaluation_and_record` is called for a strategy-family hypothesis with
  `certificate_mint["candidate"] = {"strategy_id": "totally-unrelated-strategy", "profile":
  "totally-unrelated-profile"}`, then the pooled evidence for that evaluation contains zero of
  the planted trades and no certificate is minted naming the unrelated candidate — reproducing
  and closing the iter-9 evaluator's own probe.
- TC-14: given the SAME 12 planted `v1/default` trades, when `certificate_mint["candidate"] =
  {"strategy_id": "v1", "profile": "default"}` (the candidate the evidence actually belongs to)
  and the checkpoint's gates pass, then a certificate IS minted naming `v1/default`, proving the
  fix does not also break the honest-match path.
- TC-15: given `certificate_mint=None` (every existing route/CLI caller today), when a
  strategy-family evaluation runs, then `_pool_strategy_trades` pools the whole `JournalStore`
  exactly as before (unfiltered), and iter-9's own `insufficient_sample`-on-real-corpus
  acceptance (its TC-10) is unchanged.
- TC-16: given `apps/backend/app/research/referee_adjudicate.py` after this iteration, when its
  module docstring (`:6`) and `authorize_promotion`'s own section header/docstring (`:1720`,
  `:1731-1732`) are read, then neither contains the word "unwired".
- TC-17: given `apps/backend/tests/test_pnl_scan.py::test_no_bypass_guard_can_fail_on_a_seeded_violation`,
  when it runs against the real, unmodified scan logic, then it passes; when the SAME scan logic
  runs against a seeded copy of the source containing a banned bypass token, then the scan's own
  assertion genuinely fails (not a hand-typed string check).
- TC-18: given `apps/backend/tests/test_referee_registry.py` after this iteration, when the file
  is inspected, then the duplicate `S-5` assertion (formerly at line ~874) no longer appears and
  every other assertion in the file is unchanged.
- TC-19: given the stored golden replay scripts for J-01–J-08 (where they exist) plus an LLM
  browser-qa fallback for the keyless ones, when they run against this iteration's build, then
  all eight remain scored `passing` with zero regression.
- TC-20: given the newly-rendered Adjudications/Runs numerics, when `_PRICE_ARITHMETIC_FIELDS`'s
  seeded counter-test mutates one of the newly-added field paths to a client-derived value, then
  the guard test fails, proving the field is now genuinely covered (not just listed).
- TC-21: given the two new sections' deferred-fetch and compute-trigger effects, when
  `test_desk_refresh_chain_guard.py` runs after `_EXPECTED_EFFECT_COUNT` is re-derived, then it
  asserts the new count with the mandatory rationale paragraph present, and the no-mount-trigger
  scan itself stays green.
- TC-22: given the full backend suite, when it runs after this iteration, then it is green
  (0 failed), `Config().config_fingerprint()` prints `08e471b10130e1e2`, and the collected-test
  count is at least iteration 9's own 2,678.

## NOTES

- Process lesson (iter-9, second entry): a `next_depth: full` recommendation attached to a
  `CONTINUE` verdict was demoted to lean by the wall-clock budget in iterations 7 and 9 despite
  the spec pleading against it — `depth_full_granted` only fires on `reason:
  prior-verdict-ESCALATE`. This round's verdict genuinely IS ESCALATE, so the demotion condition
  does not apply here, but the pattern is worth flagging again given it has recurred three times
  this session: do not let a time trimmer cut this round back to the short pipeline.
- The QA fixture-seeding work for a `fragile` and a refused-attestation adjudication entry
  (TC-2/TC-3) is genuinely new setup, not a re-use of any existing fixture — no prior iteration
  has produced either verdict state on the fixture-scoped rig yet (the only seeded hypothesis to
  date, S-1, is same-day-registered with zero post-boundary accrual).
- Two items remain outstanding for a person, carried forward unchanged and non-blocking: this
  iteration's changed files plus iterations 8 and 9's should all be committed; and, from
  iteration 2 and outside this project, the unrelated trendora backend on port 8255 has not been
  restarted.
- The Runs section's compute triggers exercise real null-build/evaluation compute paths — heavy
  paths under T-12 — during browser-QA against the fixture-scoped rig's own small corpus; the
  host-guard CPU mask still applies to any such run exactly as it does to the desk's other
  computes.
