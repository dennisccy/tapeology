# Goal Iteration 14 — J-08 half 1: Scout Ledger, Walk-Forward, and Validation Vault render on /desk

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 14
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict (iteration 13) was ESCALATE, the mandatory, no-exceptions
  grant of full depth this era's own precedent requires (iterations 8 and 12 both lost the
  independent auditor when full depth was requested only in evaluator prose, not the verdict line).
- Frontend Present: yes
- **Target journeys:** J-08
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-07 (full regression — the
  prior verdict was ESCALATE, which this agent's own instructions say widens the regression set to
  every currently-passing journey rather than a rotating smoke subset)
- **Anti-goal reminders:**
  - "No exploratory read of a sealed shard. Event data and outcome aggregates of a `sealed` shard
    are refused everywhere (routes, MCP, accessor, readiness) until its recorded exposure; the
    refusal is typed, tested, and fail-closed. *(critical)*"
  - "Sealed exposure is family-level and single-shot — never a second draw. No more than one
    evaluation per (family, shard) exists, ever; a failed sealed verdict is permanent and travels
    in every later export bundle; no perturbed re-submission resets it. *(critical)*"
  - "A recorded tranche is one opaque research pool until its shards are exposed. No served
    surface — readiness, recorder progress, datasets, backtests, PnL ledger, Scout, walk-forward,
    graduation, MCP, UI — may present a complete identity-labelled partition of 'exploratory'
    versus 'sealed', nor a complete per-shard list of EITHER side while any pool member is
    unexposed; the registered universe is public by construction, so a complete list of one side
    identifies the other by subtraction. Unexposed pool members stay mutually indistinguishable;
    identity becomes public only at real exposure or assignment. The governing test is the TR-2
    inference trap: given the registered universe plus every public artifact, no still-unexposed
    vault-eligible shard is identifiable with certainty. *(critical — spec r5)*"
  - "Evidence classes never mix. No `historical_exposed_diagnostic` output feeds a gate, a
    graduation transition, a certificate, a promotion, or a pooled statistic with `historical_oos`
    rows; nothing in this era emits `live_confirmatory`. *(critical)*"
  - "Single source of truth — each shared value is computed once, owned by one canonical endpoint,
    and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations.
    *(critical)*"
  - "Read-only MCP — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP
    surface can change state. *(critical)*"
  - "Frozen foundations — the `v1` strategy, the `default` profile, the tape engine's five states
    and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
    surface's behaviour stay byte-identical. New work is additive and versioned beside them, never
    a mutation of them. *(critical)*"
  - "The vault secret never enters the repo, a log, a payload, or a screenshot — only its sha256
    commitment is ever recorded. *(critical)*"
  - "No microstructure claim beyond what L1 supports. `refill_consistent` is the strongest
    liquidity label; 'iceberg', institutional-intent, and manipulation language are banned; every
    aggressor-derived quantity is served beside its `fallback_frac` and `unknown_frac`. *(critical)*"

## GOAL

Render the Scout Ledger, Walk-Forward, and Validation Vault sections on `/desk` (directly below
the existing Microscope Readiness section), each reading its already-shipped backend endpoint
verbatim with operator compute controls where one exists, so the funnel from candidate trial
through fold sequence to vault shard state is visible on screen for the first time — without the
new page ever disclosing more of the vault's opaque pool than its own endpoint already does.

## BACKGROUND

Iteration 13's evaluator verdict is ESCALATE — this era's own hard-won, mechanically-binding way
to keep the independent auditor in the loop (iterations 8 and 12 both lost the auditor when full
depth was requested only in evaluator prose). The evaluator's next-step recommendation names this
iteration precisely: build J-08 as a full round with the auditor, split panels-first (this
iteration) from tools-plus-MCP-bump (iteration 15), because the panels render surfaces governed by
the critical "one opaque research pool" anti-goal that only the independent auditor has caught
failing in this session — five times (rounds 2, 4, 5, 7, 13), each time AFTER review and QA had
both already passed the same code (lessons iter-9, iter-9 second, iter-11). Direct codebase
inspection (not assumed from the goal text) confirms all four backend GET endpoints
(`/research/desk/micro/{readiness,scout,walkforward,vault}`) plus the Scout and Walk-Forward
compute triples already exist and are already tested, and that Microscope Readiness already
renders on `/desk` (shipped at iteration 1) while zero Scout/Walk-Forward/Vault frontend surface
exists yet (`grep` for `fetchDeskScout`/`fetchDeskVault`/`fetchDeskWalkforward` returns nothing).
This iteration is therefore genuinely frontend-heavy — three new below-the-fold sections plus
their compute controls — not a backend build, which is why `Frontend Present: yes` is load-bearing
this round for the first time in several iterations. J-06 steps 4-5 (the credentialed recording
tranche) and the r8-deferred vault identity-commitment revision stay explicit future work,
scheduled before the credentialed tranche but never bundled into this UI round (never design a
named spec revision ad hoc inside an unrelated fix; never bundle two risky items in one iteration).

## IN SCOPE

### Backend

- [ ] `apps/backend/tests/test_desk_ui_guards.py`: extend `_PRICE_ARITHMETIC_FIELDS` for every new
  numeric binding the three sections introduce (Scout family/trial fields incl. `variants_tried`;
  Walk-Forward fold/sequence/decay fields; Vault shard/universe fields) — the established
  allow-list-widening pattern, never a loosened check.
- [ ] No change to `vault.py`, `scout.py`, `scout_ledger.py`, `walkforward.py`,
  `walkforward_ledger.py`, or `micro_routes.py`'s served computation, serialization, or route
  shape — this iteration reads and renders the already-shipped endpoints verbatim (see OUT OF
  SCOPE). `test_copy_discipline.py`'s frontend-literal sweep is glob-based over
  `apps/frontend/app/**/*.tsx` already — no file edit needed there unless a banned phrase is used.

### Frontend

- [ ] `apps/frontend/lib/types.ts`: add response/row types for the Scout ledger body, the
  Walk-Forward ledger body, the Vault body, and the two new compute-manager snapshot/run-log
  shapes (Scout, Walk-Forward) — transcribed from the backend's own served shape (`list_scout_
  families`, `list_fold_specs`/`list_walkforward_sequences`, `build_vault_state`'s docstrings and
  return shapes) — no field invented, no field dropped.
- [ ] `apps/frontend/lib/api.ts`: add `fetchDeskScout`, `triggerDeskScoutCompute`,
  `fetchDeskScoutCompute`, `cancelDeskScoutCompute`, `fetchDeskScoutRuns`; the same five-function
  quintet for Walk-Forward; and `fetchDeskVault` — following the `fetchMicroReadiness` /
  Referee-Runs fetch-function precedent already in this file (same `API_BASE` usage, same
  `{ok, data, error}` envelope, same "Backend unreachable" fallback string).
- [ ] `apps/frontend/app/desk/page.tsx`: widen the `DeskCollapsibleSection` union with
  `"scoutLedger" | "walkForward" | "validationVault"`; add three `CollapsibleSection` blocks
  rendered directly below the existing Microscope Readiness section, in that order, each with its
  own lazy fetch-on-expand wiring (the pattern already used for `microReadiness`); add
  `ScoutLedgerSection`, `WalkForwardSection`, `ValidationVaultSection` components rendering their
  endpoint's fields verbatim — family/trial rows with denominators and kill reasons; fold-sequence
  rows with per-fold class labels and the decay line; shard/universe rows with one-way lifecycle
  states and the universe's two-stage reveal (`rule_commitment`-only pre-release,
  `symbol_rule`/`date_rule`/nonce post-release); surface both ledgers' `chain_verification`
  verdicts beside their data (the `GET /scout`/`GET /walkforward`/`GET /vault` precedent already
  documented in each route's own docstring).
- [ ] Wire Scout and Walk-Forward compute controls to their own `POST/GET/POST-cancel` triples
  using the shipped `RefereeComputeControlState` shape (one independent instance per section,
  never shared) — a "Run Screen" / "Run Walk-Forward" button, a progress readout, and a Cancel
  control, mirroring the Referee Runs section's own established pattern.
- [ ] The Validation Vault section is READ-ONLY this iteration — no button that seals, assigns,
  exposes, or starts a recorder run (see `state/assumptions.md`'s iter-14 entry for why).
- [ ] Each of the three new sections' fetch logic targets ONLY its own registered endpoint — the
  Validation Vault section in particular never fetches `/research/datasets` or re-reads Microscope
  Readiness's own aggregate to enrich or backfill its view; each section renders exactly the body
  its own endpoint returns and nothing computed client-side from a second source.

### New user-facing capability

An operator can now SEE, not just query via curl or pytest, the Scout's every candidate trial and
kill reason, the walk-forward engine's fold sequences and decay view, and the vault's shard/universe
lifecycle states, directly on `/desk` — and can start or cancel a Scout screening run or a
Walk-Forward compute run from the page instead of the CLI.

### New information displayed

Scout family/trial rows (`family_id`, `family_root_id`, `variants_tried`, per-trial `decision`/
`reason`/`notes`/`screen_result`); Walk-Forward fold-spec and sequence rows (`mode`, `fitting_rule`,
`rule_id`, per-fold results, evidence-class label, the decay view, the sequence verdict, `voided`);
Vault shard rows (opaque pre-exposure fields while `sealed`, full provenance from `assigned`
onward) and universe rows (`rule_commitment` pre-release, `symbol_rule`/`date_rule`/nonce
post-release); both ledgers' `chain_verification` verdicts.

### New user actions

"Run Screen" (Scout compute) button + progress + Cancel; "Run Walk-Forward" (Walk-Forward compute)
button + progress + Cancel; expand/collapse for each of the three new sections (the existing
`CollapsibleSection` control, reused unchanged).

### UI surface changes

`/desk` gains three new below-the-fold `<section>` blocks — Scout Ledger, Walk-Forward, Validation
Vault — rendered directly below the existing Microscope Readiness section and below every shipped
Referee section. No existing section's markup, `data-testid`, or heading changes.

### Product surface delta

`/desk` moves from showing only the corpus-readiness truth (J-01) to showing three more stages of
the funnel end-to-end (trial → fold → vault state) on screen, closing most of the "the funnel is
visible" gap J-08 exists to close. The fourth piece — the four new MCP proxy tools and the
`EXPECTED_TOOLS` bump to 26 — is explicitly deferred to iteration 15 per the evaluator's own split
recommendation.

### Blueprint conformance

Fulfills the ALREADY-REGISTERED Scout Ledger / Walk-Forward / Validation Vault homes in
`blueprint.md`'s Information Architecture table (present since era baseline; the J-08 row already
names "`/desk` → all four new sections above"). No nav-skeleton change. A short iter-14 note has
already been appended to `blueprint.md` for the record; no table content changed.

### Data-contract additions

None. All three sections render already-registered Data Contract rows (Scout ledger, Walk-Forward
ledger, Vault) verbatim from their already-registered endpoints and modules; no new field, no
second computation path, no new endpoint, no new owner.

## OUT OF SCOPE

- The four new MCP tools (`desk_micro_readiness`, `desk_scout`, `desk_walkforward`, `desk_vault`)
  and the `EXPECTED_TOOLS` bump to the 26-tuple — the evaluator's own split plan defers this to
  iteration 15 so this round's diff stays small enough for the auditor to fully cover.
- Any change to `vault.py`, `scout.py`, `scout_ledger.py`, `walkforward.py`,
  `walkforward_ledger.py`'s computation, serialization, or route shape, and any change to
  `docs/rapid-validation-spec.md`.
- J-06 steps 4-5 (the credentialed real-tape recording tranche) — stays shut; nothing in this
  iteration touches `tick_recorder.py`'s own compute UI or a universe-registration form.
- The r8-deferred vault identity-commitment revision (a FUTURE named spec revision per r8's own
  text: "not to be designed ad hoc inside this fix"). It remains scheduled before J-06 step 4, not
  before J-08's second half.
- J-09 (pilot studies) — its acceptance explicitly depends on J-08's sections existing to render
  through; out of reach until both J-08 halves land.
- J-10's remaining trap-suite items (TR-3, TR-22, TR-23, TR-24, TR-26) — a separate, unrelated body
  of backend work (a new `micro_sealed_evaluation.py` owner module, the lineage-boundary
  computation, the `quote_depletion` timing fix, accessor-fence/exposure-registry hardening); not
  bundled with this UI round (never bundle two risky items in one iteration).
- Any Recorder-progress panel — `tick_recorder.py`'s own `POST/GET/POST-cancel .../recorder/compute`
  triple is a separate Data Contract row from "Validation Vault" and is not one of J-08's four
  named sections; not built this iteration.

## DEFINITION OF DONE

- [ ] Scout Ledger and Walk-Forward sections render on `/desk`, verified via browser-qa-agent
      (element-captured; TC-1, TC-2, TC-7, TC-8, TC-9)
- [ ] Validation Vault section renders on `/desk`, read-only, and its opacity holds across BOTH
      shard lifecycle stages and BOTH universe release stages, verified via browser-qa-agent and
      the independent auditor's own probe (TC-3, TC-4, TC-5, TC-6, TC-15)
- [ ] J-08 as a whole is scored `partial` this iteration (panels done, the four MCP
      tools still pending iteration 15) — not claimed `passing` prematurely
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-05, J-07 remain green with REAL
      (not merely cited) evidence on disk (TC-13)
- [ ] No anti-goal violation introduced — the independent auditor specifically re-runs the TR-2 /
      TR-27 / TR-28 sweep methodology against the new `/desk` page, not only the raw JSON endpoints
      (TC-15; see NOTES)
- [ ] Zero client-side arithmetic on any newly-served numeric (TC-9)
- [ ] `EXPECTED_TOOLS` still asserts exactly 22; zero MCP file touched (TC-10)
- [ ] Frozen rails hold: fingerprint `08e471b10130e1e2`, the six `referee_*.py` SHA-256 hashes
      unchanged from the iteration-0 baseline, zero new `Config` fields (TC-11)
- [ ] Full backend suite plus the extended guard tests pass at a count ≥ 3228 collected, 0 failures
      (TC-10)
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-14-dev.md`

## TESTING REQUIREMENTS

- Browser: J-08 (Scout Ledger, Walk-Forward, Validation Vault sections; element-captured screenshots
  per section, per T-10); full regression sweep of J-01–J-05 and J-07 via the store-scoped rig,
  with every cited evidence path confirmed to exist on disk (not merely named in a results row).
- Unit/integration: extended `test_desk_ui_guards.py` (`_PRICE_ARITHMETIC_FIELDS`); `test_mcp_
  server.py` re-run unchanged (still 22); the existing `test_vault.py`/`test_scout.py`/
  `test_walkforward.py` TR-2/TR-27/TR-28 fixtures reused (not re-implemented) as the basis for the
  new frontend-layer sweep in TC-15.
- Error cases: backend-unreachable / non-200 responses for each of the three new fetches (TC-14);
  an empty scout ledger and an empty vault (TC-1, TC-3) beside a populated Walk-Forward ledger
  (TC-2) — the real `.data` store today has zero `micro_scout`/`micro_vault` directories but a
  non-empty `micro_walkforward` one, so this mixed empty/populated state is what the live backend
  will actually show, not a hypothetical.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps
to at least one concrete scenario line below.

- TC-1: given the real backend has zero registered scout families (no `micro_scout` ledger
  directory on disk), when an operator loads `/desk` and expands "Scout Ledger", then the section
  renders an honest empty-state treatment (matching the era's Design Direction copy convention, e.g.
  "No candidates ledgered.") with zero fabricated rows, plus `chain_verification.ok: true` for the
  empty ledger.
- TC-2: given the real backend's Walk-Forward ledger has at least one registered sequence
  (`micro_walkforward/walkforward_ledger.jsonl` is non-empty on disk today), when the operator
  expands "Walk-Forward", then the section renders at least one fold-sequence row whose evidence
  class label, sidedness, and decay-view values are byte-identical to the same fields in
  `GET /research/desk/micro/walkforward`'s JSON body.
- TC-3: given the real backend has zero registered vault universes (no `micro_vault` directory on
  disk), when the operator expands "Validation Vault", then the section renders an honest empty
  state for both `shards` and `universes` (e.g., "No universes registered.") plus both ledgers'
  `chain_verification.ok: true`, with zero fabricated shard or universe rows.
- TC-4: given a fixture vault state (the existing `test_vault.py` TR-2/TR-27 fixture shape, reused
  not reimplemented) with at least one `sealed` shard and a universe whose ORIGINAL registered pool
  is not yet fully released, when the Validation Vault section renders that state, then the sealed
  shard's row shows ONLY the surrogate `shard_id`, `universe_id`, coarse size bucket, salted
  commitment, `sealed_at`, and exposure state — no symbol, no date, no raw checksum, no exact event
  count anywhere in the rendered output — and that universe's row shows `rule_commitment`, never
  `symbol_rule`/`date_rule` or the nonce.
- TC-5: given that same fixture's universe reaches whole-ORIGINAL-pool release (every originally
  registered member exposed), when the Validation Vault section re-fetches, then the universe row
  now renders `symbol_rule`/`date_rule` and the nonce verbatim from the endpoint response — proving
  both the pre-release and post-release rendering paths are exercised, not only the happy path.
- TC-6: given the Validation Vault section's source code, when the independent auditor inspects its
  data flow, then it issues exactly one fetch (`GET /research/desk/micro/vault`) and performs no
  client-side join against any other endpoint's response (grep-verified: zero references to
  `/research/datasets` or the readiness response inside the section's component tree).
- TC-7: given the Scout Ledger section's compute control in an idle manager state, when the operator
  clicks "Run Screen", then the control shows a running/disabled state with a visible progress
  readout (`candidates_done`/`candidates_total`) and a Cancel control appears; clicking Cancel
  invokes `POST /scout/compute/cancel`, and the UI reaches a cancelled/idle terminal state without
  hanging.
- TC-8: given the Walk-Forward section's compute control in an idle manager state, when the operator
  clicks "Run Walk-Forward", then the same progress-readout-plus-Cancel behavior holds against
  `POST/GET/POST-cancel /research/desk/micro/walkforward/compute`.
- TC-9: given every numeric value newly rendered by the three sections (e.g., `variants_tried`, fold
  counts, decay percentages, size buckets), when `test_desk_ui_guards.py`'s widened
  `_PRICE_ARITHMETIC_FIELDS` sweep runs, then it reports zero client-side arithmetic operators
  applied to any of those bindings in `page.tsx`.
- TC-10: given the full backend test suite plus the extended guard tests, when the suite runs, then
  it passes at a count ≥ 3228 collected with 0 failures, and `tests/test_mcp_server.py` still
  asserts `EXPECTED_TOOLS` at exactly 22 (untouched).
- TC-11: given `Config().config_fingerprint()` and the six `referee_*.py` modules, when re-checked
  after this iteration's diff, then the fingerprint still prints `08e471b10130e1e2` and every
  `referee_*.py` SHA-256 hash is byte-identical to the iteration-0 baseline.
- TC-12: given a clean `rm -rf apps/frontend/.next` + rebuild (T-9) against the store-scoped
  browser-QA rig, when the browser pass visits `/desk` and element-captures Microscope Readiness
  (regression) plus the three new sections, then all four are visible below the shipped Referee
  sections in that exact order, each screenshot is written to disk at the path the results table
  cites, and no new `data-testid` or heading string collides with a shipped one (the T-11 static
  sweep against stored replay scripts passes).
- TC-13: given J-01 through J-05 and J-07's own already-registered acceptance, when the replay/
  browser-QA lane re-verifies them this iteration, then every cited evidence file for those six
  journeys actually exists on disk at the path the results table names (closing the
  `evidence_makeup` flag carried from iteration 13), and J-07's `/research/desk/micro/graduation`
  route is genuinely re-checked against the live backend (not recorded `DEFERRED-BUDGET` again).
- TC-14: given the backend is unreachable or returns a non-200 response, when any of the three new
  sections attempts its fetch, then it renders a typed "could not be loaded" error message (the
  `fetchMicroReadiness` precedent's `error` string) rather than a blank panel or a stale/fabricated
  table.
- TC-15: given the existing TR-2/TR-27/TR-28 pytest fixtures (a registered universe with a proper
  subset of shards exposed), when the independent auditor additionally sweeps the RENDERED `/desk`
  page (DOM output plus every network response the page issues) using the same inference-trap
  methodology TR-2 already applies to raw endpoints, then the same guarantee holds through the new
  UI layer: no still-unexposed vault-eligible shard is identifiable with certainty from the union
  of every value the page renders, and no complete identity-labelled exploratory/sealed partition
  is derivable from it by subtraction.

## NOTES

- **Auditor directive (why full + auditor is mandatory this round).** Probe the new Validation
  Vault section specifically against TR-2 (inference trap), TR-27 (nonced rule commitment,
  two-stage reveal), and TR-28 (coarse pre-release volume buckets) — confirm the FRONTEND adds no
  new inference surface beyond what `GET /research/desk/micro/vault` already discloses. This is the
  fault class the independent auditor alone has caught in this session, five times (rounds 2, 4, 5,
  7, 13), each time after review and QA had both already passed the same code (lessons iter-9,
  iter-9 second, iter-11). Attack the fix before writing it up (iter-9 lesson) rather than trusting
  a field-level review.
- **Design lesson (paired mechanisms, carried forward).** The Validation Vault section's universe
  rows have two release stages (pre-release `rule_commitment`-only vs. post-release
  `symbol_rule`/`date_rule`+nonce); treat both as first-class rendering paths, never one happy path
  with the other assumed — TC-4/TC-5 exist specifically to force both, per this era's own repeated
  lesson that widening one side of a paired mechanism while leaving its twin narrow is exactly how
  every leak this era closed originally opened.
- **Split plan.** This is half 1 of 2 of J-08 per iteration 13's evaluator recommendation. Half 2
  (the four MCP tools + `EXPECTED_TOOLS` 26-tuple bump) is the next full-depth iteration, scoped
  separately so this round's diff stays small enough for the auditor to fully cover — iteration 13
  itself ran over its clock and paid for it (a dropped journey re-check, a shed reviewer).
- **Evidence debt carried from iteration 13.** J-02–J-05 read `evidence_makeup: true` (cited
  screenshots that do not exist on disk); J-07 was `DEFERRED-BUDGET` (never re-checked this
  iteration). Both ride this iteration's Required-still-passing regression sweep rather than a
  dedicated round (per this agent's own rule against evidence-only iterations).
- **`state/golden-gaps` durability.** J-07's "no golden replay script, and here is why" disclosure
  has been auto-deleted by the replay lane three times this era. If it is found missing again this
  iteration, restore it verbatim (the reason is still valid: `demo_runner.normalize_url()` rewrites
  localhost URLs onto the frontend base, and no proxy exists for `/research/*`) rather than
  re-writing it from scratch — this is a harness durability gap for the framework maintainers, not
  a product gap for this iteration's developer.
- **Assumption ledger and blueprint.** This iteration's one interpretive call (why the Validation
  Vault section carries no compute button) is already appended to
  `runs/goal-session-rapid-microscope/state/assumptions.md` under `## iter-14 — goal-decomposer`,
  and a short confirming note is already appended to
  `runs/goal-session-rapid-microscope/state/blueprint.md` — both applied directly by the
  goal-decomposer before this spec was finalized; no further action needed on either file for this
  iteration's scope.
