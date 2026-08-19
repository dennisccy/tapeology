# Goal Iteration 15 — J-08 half 2: MCP v6 (26 tools), the Microscope Readiness coherence fix, and J-07 re-verification

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 15
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict (iteration 14) was ESCALATE, the mandatory, no-exceptions
  grant of full depth this era's own precedent requires (iterations 8 and 12 both lost the
  independent auditor when full depth was requested only in evaluator prose, not the verdict line).
- Frontend Present: yes
- **Target journeys:** J-08, J-07
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-10 (rotating smoke set
  covering the sentinel + every journey whose UI home or shared endpoint this iteration touches;
  J-06 is intentionally excluded — its canonical Validation Vault home gets a testid-only fix with
  no change to its still-out-of-scope substantive recorder/tranche work, matching iteration 14's
  own precedent of not listing J-06 as required-still-passing for the identical reason)
- **Anti-goal reminders:**
  - "**No exploratory read of a sealed shard.** Event data and outcome aggregates of a `sealed`
    shard are refused everywhere (routes, MCP, accessor, readiness) until its recorded exposure;
    the refusal is typed, tested, and fail-closed. *(critical)*"
  - "**Sealed exposure is family-level and single-shot — never a second draw.** No more than one
    evaluation per (family, shard) exists, ever; a failed sealed verdict is permanent and travels
    in every later export bundle; no perturbed re-submission resets it. *(critical)*"
  - "**A recorded tranche is one opaque research pool until its shards are exposed.** No served
    surface — readiness, recorder progress, datasets, backtests, PnL ledger, Scout, walk-forward,
    graduation, MCP, UI — may present a complete identity-labelled partition of 'exploratory'
    versus 'sealed', nor a complete per-shard list of EITHER side while any pool member is
    unexposed; the registered universe is public by construction, so a complete list of one side
    identifies the other by subtraction. Unexposed pool members stay mutually indistinguishable;
    identity becomes public only at real exposure or assignment. The governing test is the TR-2
    inference trap: given the registered universe plus every public artifact, no still-unexposed
    vault-eligible shard is identifiable with certainty. *(critical — spec r5)*"
  - "**Evidence classes never mix.** No `historical_exposed_diagnostic` output feeds a gate, a
    graduation transition, a certificate, a promotion, or a pooled statistic with
    `historical_oos` rows; nothing in this era emits `live_confirmatory`. *(critical)*"
  - "**Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*"
  - "**Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on
    the MCP surface can change state. *(critical)*"
  - "**Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside them,
    never a mutation of them. *(critical)*"
  - "**The vault secret never enters the repo, a log, a payload, or a screenshot** — only its
    sha256 commitment is ever recorded. *(critical)*"

## GOAL

Ship the second half of J-08 — four new read-only MCP tools (`desk_micro_readiness`, `desk_scout`,
`desk_walkforward`, `desk_vault`) bringing the contract from 22 to 26 tools — fix Microscope
Readiness's coherence-WARN (it silently drops the `sealed_tranche` and `joinable_corpus.
withheld_excluded` aggregates its own endpoint already serves), fix the four small confirmed
defects from the last two rounds, and genuinely re-verify J-07, all under a full round the
independent auditor is guaranteed to run.

## BACKGROUND

Iteration 14's verdict is ESCALATE — in this session only the verdict line binds full depth
(lessons iter-8, iter-12 process note); the evaluator's own next-step recommendation names this
exact scope for iteration 15, split deliberately from iteration 14's panel-only half so each round
stays small enough for the auditor to fully cover. This round DOES put two opaque-pool-critical
surfaces in one diff — the four MCP proxies and the readiness-panel disclosure fix — which normally
this agent's own rubric would treat as "never bundle two risky items"; here that bundling is the
evaluator's own explicit, reasoned instruction (both pieces sit inside the SAME target journey,
J-08, not two separate journeys, and the auditor — the only lane that has caught this fault class,
six times now across iters 2, 4, 5, 7, 13, and 14's F1/F2 — is mandatory this round precisely
because both land together). The four tools are byte-identical GET proxies of already-registered,
already-audited endpoints (readiness/scout/walkforward/vault), so they carry no new computation
risk; the readiness fix wires two ALREADY-REGISTERED Data Contract sub-fields (blueprint.md's
iter-10 "Disclosure sub-fields" table) into their ALREADY-REGISTERED home, so it is a completeness
fix, not a new disclosure decision — the two widened surfaces are twins of each other (same backend
JSON, same two fields), not one widened while the other stays narrow (lesson iter-11). J-07 has
been `DEFERRED-BUDGET` two iterations running despite its own DoD forbidding a third, so its
re-verification is a first-class item here, not a passenger — it rides the LLM browser lane by
navigating directly to `GET /research/desk/micro/graduation` (no dedicated UI section exists for
it; state/assumptions.md's iter-15 second entry has the full reasoning). Lesson iter-14 (console
errors only surface after a section is expanded, not on first load) governs the HTML-nesting fix's
own acceptance test below.

## IN SCOPE

### Backend

- [ ] `apps/backend/app/mcp/__init__.py`: add four `_STATIC_PATHS` entries and four matching
  `types.Tool` entries — `desk_micro_readiness` → `/research/desk/micro/readiness`, `desk_scout` →
  `/research/desk/micro/scout`, `desk_walkforward` → `/research/desk/micro/walkforward`,
  `desk_vault` → `/research/desk/micro/vault` — inserted in the `TOOLS` tuple immediately after
  `desk_referee_registry` and before `pnl_ledger` (mirroring the file's own established
  no-required-param proxy shape and insertion convention: "each positioned right after its
  dependency-order sibling"). Update the module docstring's shipped-endpoint list in the same
  commit. No new HTTP verb, no new dependency, no change to `_request_path`'s dispatch shape.
- [ ] `apps/backend/tests/test_mcp_server.py`: extend `EXPECTED_TOOLS` from the 22-tuple to the
  ordered 26-tuple in the SAME commit as the tool additions (goal.md J-08 step 2's own explicit
  instruction); add honest-empty-state AND populated-state byte-identity tests for each of the
  four new tools, mirroring the `desk_referee`/`desk_referee_registry` precedent exactly. Populated
  states MUST be seeded via a DIRECT ledger/store write (e.g. the scout/walkforward/vault ledgers'
  own public append/record functions, the same rig `test_vault.py`'s TR-2 fixtures already use) —
  NEVER by triggering the live compute-manager screen/fold-run path, which the era's own evidence
  shows can run past 25 minutes against the real corpus and must not be relied on to finish inside
  a test or a browser-QA pass.
- [ ] Add a new test (reusing, not reimplementing, `test_vault.py`'s TR-2 rig — `_combined_fixture_
  store`, `_record_distinctive_dataset`, `_scope_everything_to`, `_scalars`) that calls all 26 MCP
  tools via `call_tool` against a backend with one sealed, globally-distinctive shard, and asserts
  the sealed shard's raw dataset id, checksum, symbol, window bounds, and exact trade/quote counts
  appear in ZERO tool response bodies — the MCP layer is a genuinely separate process
  (`python -m app.mcp` over stdio) the existing REST-only `app.openapi()`-driven TR-2 sweep never
  exercises today, so this closes that gap explicitly for the new MCP surface.
- [ ] No change to `micro_readiness.py`, `vault.py`, `scout.py`, `scout_ledger.py`, `walkforward.py`,
  `walkforward_ledger.py`, or `micro_routes.py`'s served computation, serialization, or route shape
  — every field this iteration surfaces (`sealed_tranche`, `joinable_corpus.withheld_excluded`) is
  already served by unchanged code; this iteration only adds readers.
- [ ] `apps/backend/tests/test_desk_ui_guards.py`: extend `_PRICE_ARITHMETIC_FIELDS` for the two
  newly-rendered numerics (`sealed_tranche.shard_count`/`symbol_days`/its `by_universe` counts,
  `joinable_corpus.withheld_excluded`) — the established allow-list-widening pattern.

### Frontend

- [ ] `apps/frontend/lib/types.ts`: extend `MicroReadinessResponse` (currently `totals`/`shards`/
  `study_floors`/`integrity_errors` only) with `joinable_corpus` (full shape, transcribed verbatim
  from `micro_readiness.py`'s `build_readiness` return statement: `total: number;
  playbook_signal_count: number; band_touch_count: { status: string; count: number | null };
  by_setup_id: Record<string, number>; playbook_integrity_errors: { file: string; error: string }[];
  withheld_excluded: number`) and `sealed_tranche: { shard_count: number; symbol_days: number;
  by_universe: Record<string, { shard_count: number; symbol_days: number }> }` — no field invented,
  none dropped.
- [ ] `MicroReadinessSection` (`page.tsx`): render `sealed_tranche.shard_count` and `sealed_tranche.
  symbol_days` as two new rows (or an adjoining small block — developer's choice of exact markup)
  in the existing Corpus Totals area, plus a small per-universe breakdown (`universe_id` →
  `shard_count`/`symbol_days` — the exact aggregate shape `micro_readiness.py`'s own docstring
  names as spec-approved, section 7.5 points 4/7); render `joinable_corpus.withheld_excluded` as
  one additional labeled count. AGGREGATE ONLY: no symbol, no session date, no dataset id, no raw
  checksum, no per-shard `exposure_state` for a withheld shard anywhere in the new markup — a
  per-shard list reopens the subtraction attack five prior rounds closed (lesson iter-9, both
  entries). `joinable_corpus.total`/`playbook_signal_count`/`band_touch_count`/`by_setup_id` stay
  fetched and typed but UNRENDERED this iteration (state/assumptions.md's iter-15 first entry).
- [ ] Fix the invalid HTML nesting at `apps/frontend/app/desk/page.tsx:6461-6472` (the Walk-Forward
  sequence verdict block): a `<details>`/`<pre>` block-level pair sits inside a `<p>`, which React
  reports as a hydration error (5 console errors the instant that block is expanded). Change the
  outer wrapper element so block content is legally nested (e.g. `<p>` → `<div>`), preserving the
  existing classes, text, and `<details>` content exactly. Confirmed by a whole-file scan to be the
  ONLY such site in the 12,000-line Desk page — no sibling occurrence needs the same fix.
- [ ] `ScoutLedgerSection`'s family header (`page.tsx`, ~6198-6203): render `family.family_root_id`
  beside the existing `family.family_id`/`variants_tried` text — the field is already on
  `ScoutFamily` and already fetched by the one canonical `GET /research/desk/micro/scout` call; no
  new fetch, no new type field.
- [ ] `WalkForwardSection`'s empty-sequences state (`page.tsx:6444`): change the `EmptyState` title
  from the reused "No candidates ledgered." (Scout's own copy) to sequence-appropriate wording
  (e.g. "No walk-forward sequences run.") — this section's own vocabulary is folds/sequences, never
  candidates.
- [ ] `ValidationVaultSection` (`page.tsx:6603-6621`): keep `data-testid="validation-vault-section"`
  present in the loading AND unavailable/error branches, matching `ScoutLedgerSection`'s and
  `WalkForwardSection`'s existing pattern (their section wrapper always renders, with the loading/
  unavailable ternary as a child of it); today Vault's two early returns skip the wrapper entirely,
  so the testid is genuinely absent from the DOM whenever the backend is unreachable.

### New user-facing capability

None new on screen — the operator's four already-shipped Rapid-Microscope panels become fully
honest (no silently-withheld disclosure numbers, no markup defect) and the product's machine
surface (Claude + MCP) grows from 22 to 26 read-only tools, making the readiness, scout, walk-
forward, and vault bodies newly readable from a conversation.

### New information displayed

On `/desk` → Microscope Readiness: the sealed-tranche aggregate (`shard_count`, `symbol_days`, a
per-universe breakdown) and the `withheld_excluded` count — both already served by the endpoint,
previously dropped by the frontend type. On Scout Ledger: each family's `family_root_id`.

### New user actions

None — all four new MCP tools are read-only proxies; no new button/control. Validation Vault stays
read-only (iteration 14's own assumption-ledger entry, unchanged).

### UI surface changes

Microscope Readiness gains two small aggregate additions (no new section); Scout Ledger's family
header gains one field; Walk-Forward's empty-sequences copy changes and its sequence-verdict block
changes tag (no visible layout change); Vault's loading/unavailable states gain a wrapper testid
(no visible change). No new page, no new section, no new nav entry.

### Product surface delta

The MCP contract moves from v5 (22 tools) to v6 (26 tools) — the readiness, scout, walk-forward,
and vault bodies are now reachable the same way the other 22 already are. J-08 as a whole (panels
+ MCP + the coherence fix + the four confirmed defects) is complete after this iteration, closing
the "the funnel is visible" gap end to end.

### Blueprint conformance

All work lands under the ALREADY-REGISTERED `/desk` → Rapid Microscope home (Microscope Readiness /
Scout Ledger / Walk-Forward / Validation Vault) in blueprint.md's Information Architecture table.
No new page, no nav-skeleton change. The four MCP tools are a machine-surface addition (goal.md's
"Target Users" bullet 2, Claude + MCP), not an IA nav entry. An iter-15 note has been appended to
`blueprint.md` for the record; no table content changed.

### Data-contract additions

None. `sealed_tranche` and `joinable_corpus.withheld_excluded` are ALREADY-registered Data
Contract sub-rows (blueprint.md's iter-10 "Disclosure sub-fields" table), owned by the
already-registered `micro_readiness.py`, served by the already-registered
`GET /research/desk/micro/readiness` — this iteration wires them into their already-registered UI
home, introducing no new field, no new owner, no new endpoint. The four new MCP tools are
byte-identical GET proxies of already-registered rows/endpoints (readiness/scout/walkforward/
vault) — per this codebase's own established convention (desk_playbook, desk_referee, etc. were
never given their own Data Contract row either), an MCP proxy of an already-registered endpoint is
a transport-layer addition, not a second computing module or a second serving path, and is
enforced by byte-identity tests rather than registration.

## OUT OF SCOPE

- J-06 steps 4-5 (the credentialed real-tape recording tranche) and the r8-deferred vault
  identity-commitment revision — both stay explicit future work, unbundled from this round exactly
  as iterations 13/14 kept them. Do NOT record real tape this iteration.
- J-09 (pilot studies) — still depends on J-08 being genuinely complete; not started this iteration.
- `joinable_corpus.total`/`playbook_signal_count`/`band_touch_count`/`by_setup_id` — typed and
  fetched but left unrendered (state/assumptions.md's iter-15 first entry); a plausible future home
  is J-09's own work, not this fix.
- A dedicated Graduation `/desk` UI section — goal.md's J-08 step 1 names exactly three sections
  (Scout Ledger, Walk-Forward, Validation Vault); J-07 stays keyless/automated and is verified this
  iteration via a direct-endpoint browser capture, not new UI (state/assumptions.md's iter-15
  second entry).
- J-10's remaining trap-suite items (TR-3, TR-22, TR-23, TR-24, TR-26) — a separate, unrelated body
  of backend work; not bundled with this round (never bundle a third risky item onto an already
  two-piece round).
- Any change to `docs/rapid-validation-spec.md`.
- The three older, already-decided minor items (quote-depletion timing stamp; referee-evidence
  freeze-and-disclose; the two spec §8 gaps the developer filled and disclosed at iteration 10) and
  the r8-deferred delete-both-files vault hole — all stay open, all already decided, none waiting
  on this iteration.
- The harness issues (the quality lane grading a not-run check as PASS; `state/golden-gaps` being
  auto-deleted a fourth time) — process/framework bugs, not product code; flagged for the framework
  side, not fixed by a product iteration spec.
- Any Recorder-progress panel (`tick_recorder.py`'s own compute triple) — a separate Data Contract
  row from "Validation Vault," not one of J-08's four named sections; not built this iteration.

## DEFINITION OF DONE

- [ ] The MCP contract carries exactly 26 tools in the documented order, `EXPECTED_TOOLS` and
      `TOOL_NAMES` both match, and the module docstring names all four new endpoints (TC-1)
- [ ] All four new MCP tools are byte-identical to their own GET route on both an honest-empty and
      a directly-seeded populated state (TC-2, TC-3)
- [ ] The extended TR-2 inference sweep passes against the full 26-tool MCP surface: a sealed
      shard's raw identity appears in zero tool results (TC-4)
- [ ] Microscope Readiness renders `sealed_tranche` and `joinable_corpus.withheld_excluded`
      verbatim, aggregate-only, with no per-shard identity anywhere in the new markup (TC-5, TC-6)
- [ ] The Walk-Forward HTML-nesting defect is fixed: zero new console/dev-overlay errors after
      expanding a sequence's verdict detail (TC-7)
- [ ] The three confirmed minor defects are fixed: Scout renders `family_root_id` (TC-8);
      Walk-Forward's empty-sequences copy is sequence-appropriate (TC-9); Vault's loading/
      unavailable states keep the `validation-vault-section` testid (TC-10)
- [ ] J-07 is genuinely re-verified this iteration via the browser lane against the live
      `GET /research/desk/micro/graduation` endpoint, plus a fresh `tests/test_micro_graduation.py`
      run — recorded as a real re-verification, not a third `DEFERRED-BUDGET` (TC-11)
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-05, J-10 remain green with REAL
      (not merely cited) evidence on disk (TC-13)
- [ ] No anti-goal violation introduced — the independent auditor specifically re-sweeps the new
      MCP surface AND the widened readiness panel against TR-2's inference-trap methodology, not
      only the raw JSON endpoints (TC-4, TC-6)
- [ ] Zero client-side arithmetic on any newly-rendered numeric (TC-12)
- [ ] Frozen rails hold: fingerprint `08e471b10130e1e2`, the six `referee_*.py` and
      `micro_chain_ledger.py` SHA-256 hashes unchanged from their respective baselines, zero new
      `Config` fields, Playbook detectors byte-untouched (TC-14)
- [ ] Full backend suite plus the extended guard tests pass at a count ≥ 3228 collected, 0
      failures; `tsc --noEmit` clean (TC-14, TC-15)
- [ ] The independent-auditor step genuinely runs this iteration (a dev handoff AND an audit
      report both exist on disk for `goal-rapid-microscope-iter-15`) — not trimmed for time (TC-16)
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-15-dev.md` (TC-16)

## TESTING REQUIREMENTS

- Browser: J-08's four sections re-verified on `/desk` after the fixes (element-captured, T-10),
  specifically Microscope Readiness (new aggregate rows) and Walk-Forward (expanded, console
  checked); J-07 verified by direct navigation to `GET /research/desk/micro/graduation` on the
  store-scoped rig with a screenshot of the JSON body; full regression sweep of J-01–J-05 and J-10
  via the store-scoped rig, with every cited evidence path confirmed to exist on disk (lesson
  iter-13).
- Unit/integration: `test_mcp_server.py` (26-tuple contract, per-tool byte-identity, empty +
  populated states for the four new tools); the new MCP-surface TR-2 sweep (reusing `test_vault.
  py`'s rig); extended `test_desk_ui_guards.py` (`_PRICE_ARITHMETIC_FIELDS`); `tests/test_micro_
  graduation.py` re-run fresh (not merely cited from a prior round).
- Error cases: backend-unreachable for `GET /research/desk/micro/vault` while loading/unavailable
  (TC-10); a sealed shard whose universe's original pool is not yet fully released, swept against
  all 26 tools (TC-4); an empty `sealed_tranche`/zero `withheld_excluded` state (the real `.data`
  store has zero registered vault universes today, so this all-zero case is what the live backend
  will actually show — TC-5 must also be exercised against a non-zero fixture state, not only the
  real store's current all-zero one, so the rendering path is proven, not merely inert).

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps
to at least one concrete scenario line below.

- TC-1: given the MCP module before this change (22 tools, ending
  `...,"desk_referee","desk_referee_registry","pnl_ledger","taxonomy","ui_route_map","get_endpoint"`),
  when the four new tools are added and `EXPECTED_TOOLS` is updated in the same commit, then
  `tuple(t.name for t in list_tools())` and `TOOL_NAMES` both equal the 26-entry ordered tuple with
  `desk_micro_readiness`, `desk_scout`, `desk_walkforward`, `desk_vault` inserted immediately after
  `desk_referee_registry` and before `pnl_ledger`.
- TC-2: given a running backend with no registered vault universes, no scout families, and no
  walk-forward sequences (the honest-empty state), when `call_tool("desk_micro_readiness", {})`,
  `call_tool("desk_scout", {})`, `call_tool("desk_walkforward", {})`, and `call_tool("desk_vault",
  {})` are each invoked, then each tool's `content[0].text` is byte-identical to a direct `GET` on
  its own registered path, with `isError` false.
- TC-3: given the same backend with each ledger seeded via a DIRECT store/ledger write (never a
  live compute run) to a non-empty state, when each of the four new tools is called again, then
  each tool's response is still byte-identical to its own GET route's response body.
- TC-4: given a distinctive sealed shard recorded under a registered universe whose original pool
  is not yet fully released (the existing TR-2 fixture rig), when all 26 MCP tools are called via
  `call_tool` against that backend, then the sealed shard's raw dataset id, checksum, symbol,
  window bounds, and exact trade/quote counts appear in ZERO tool response bodies.
- TC-5: given a fixture readiness store whose `sealed_tranche.shard_count`/`symbol_days`/
  `by_universe` and `joinable_corpus.withheld_excluded` are all non-zero, when `/desk` is loaded
  and Microscope Readiness is expanded, then the section displays those exact numbers on screen,
  byte-matching the fetched JSON (lesson iter-14: compare the on-screen value against the
  underlying response, not merely assert a value is present).
- TC-6: given that same fixture, when the rendered Microscope Readiness DOM is inspected, then it
  contains no symbol, session date, dataset id, or raw checksum belonging to any withheld shard,
  and no per-shard row for a withheld shard anywhere — aggregate counts only.
- TC-7: given `/desk` loaded with at least one recorded Walk-Forward sequence, when the sequence's
  "detail" `<details>` is expanded, then the browser console and the Next.js dev-overlay show zero
  new errors (no "Issues" badge appears where none appeared before expansion), and the rendered
  block passes HTML validation (no block-level element inside a `<p>`).
- TC-8: given a Scout family whose `family_root_id` differs from its `family_id`, when the Scout
  Ledger family header renders, then both `family_id` and `family_root_id` are visible in the
  header text.
- TC-9: given zero recorded Walk-Forward sequences, when the Walk-Forward section renders its
  empty state, then the displayed title is not "No candidates ledgered." and instead names
  sequences or folds explicitly (e.g. "No walk-forward sequences run.").
- TC-10: given the backend is unreachable (or returns non-2xx) for `GET /research/desk/micro/
  vault`, when the Validation Vault section renders (both the initial loading state and the
  settled-unavailable state), then the DOM contains an element with
  `data-testid="validation-vault-section"` wrapping the loading/error content in both states,
  matching Scout's and Walk-Forward's existing behavior in their own loading/unavailable states.
- TC-11: given `tests/test_micro_graduation.py`'s fixture walk
  (`exploratory → walkforward_survivor → sealed_survivor → referee_handoff_ready`), when the suite
  is re-run this iteration, then every case passes, and the browser-qa agent separately navigates
  to `GET /research/desk/micro/graduation` on the store-scoped rig and captures a screenshot
  showing HTTP 200 with the served stage vocabulary — recorded as this iteration's genuine J-07
  re-verification, not a `DEFERRED-BUDGET` row.
- TC-12: given every numeric value newly rendered this iteration (`sealed_tranche.shard_count`/
  `symbol_days`/its per-universe counts, `joinable_corpus.withheld_excluded`), when `test_desk_ui_
  guards.py`'s widened `_PRICE_ARITHMETIC_FIELDS` sweep runs, then it reports zero client-side
  arithmetic operators applied to any of those bindings in `page.tsx`.
- TC-13: given J-01 through J-05 and J-10's own already-registered acceptance, when the replay/
  browser-QA lane re-verifies them this iteration, then every cited evidence file for those
  journeys actually exists on disk at the path the results table names.
- TC-14: given the full backend test suite plus the extended guard tests and the six `referee_*.py`
  modules plus `micro_chain_ledger.py`, when run/re-checked after this iteration's diff, then the
  suite passes at a count ≥ 3228 collected with 0 failures, `Config().config_fingerprint()` still
  prints `08e471b10130e1e2`, and every one of those seven modules' SHA-256 hashes is byte-identical
  to its own era-open baseline.
- TC-15: given a clean `rm -rf apps/frontend/.next` + rebuild (T-9) against the store-scoped
  browser-QA rig, when `tsc --noEmit` runs across `apps/frontend` after the type additions, then it
  exits with 0 errors, including at every call site that constructs or reads a
  `MicroReadinessResponse` value.
- TC-16: given this iteration is dispatched at Depth: full per the binding ESCALATE-derived
  trigger (Full trigger 3), when the pipeline runs to completion, then both
  `docs/handoffs/goal-rapid-microscope-iter-15-dev.md` and an independent audit report for this
  iteration exist on disk — the round is not silently substituted with a lean/budget-trimmed run.

## NOTES

- **Auditor directive (why full + the auditor is mandatory this round).** Probe the four new MCP
  tools AND the widened Microscope Readiness panel specifically against TR-2 (inference trap) —
  confirm neither surface discloses more than its already-audited REST endpoint already does. This
  is the fault class the independent auditor alone has caught in this session, six times now
  (rounds 2, 4, 5, 7, 13, 14's F1/F2), each time after review and QA had both already passed the
  same code. Attack the fix before writing it up (lesson iter-9) rather than trusting a field-level
  review. Keep this round's diff to exactly the items listed above — no incidental extra scope —
  so the budget trimmer has no excuse to drop the auditor step (the carried, binding reason this
  round is full rather than lean).
- **Twin check (lesson iter-11).** The two pieces of this round widen the SAME underlying data
  (the readiness endpoint's `sealed_tranche`/`joinable_corpus` and the vault/scout/walkforward
  endpoints) through two transport layers (UI, MCP) that both read the SAME already-registered
  backend response verbatim — there is no narrow twin left behind, because neither new reader adds
  a byte of computation the endpoint didn't already produce. Confirm this holds at review/audit
  time rather than assuming it from this note.
- Process ask carried from the last two evaluators, restated for the record: this iteration's
  ESCALATE-forced full round must not be cut for time — if it is, the next evaluator should
  ESCALATE again rather than accept a lean substitute.
