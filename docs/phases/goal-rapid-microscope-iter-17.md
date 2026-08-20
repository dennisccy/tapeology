# Goal Iteration 17 — The sealed verdict gets a real owner: TR-23 and TR-24 close the trap suite at 29/29

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 17
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict (iteration 16) was ESCALATE, the mandatory, no-exceptions
  grant of full depth this era's own precedent requires (iterations 8 and 12 both lost the
  independent auditor when full depth was requested only in evaluator prose, not the verdict
  line). Independently reinforced by trigger 2: this round moves the sealed-verdict
  sub-computation of the ALREADY-registered "Graduation states + export bundles" Data-Contract row
  to a new owner module, `micro_sealed_evaluation.py`, per the r6 owner ruling itself (the serving
  endpoint and row shape are unchanged — see Data-contract additions below).
- Frontend Present: yes
- **Target journeys:** J-10
- **Required-still-passing journeys:** J-01, J-04, J-05, J-07, J-08 (relevance-scoped, not a full
  10-journey sweep — see BACKGROUND for why this differs from iteration 16's own full-regression
  choice)
- **Anti-goal reminders:**
  - "**Sealed exposure is family-level and single-shot — never a second draw.** No more than one
    evaluation per (family, shard) exists, ever; a failed sealed verdict is permanent and travels
    in every later export bundle; no perturbed re-submission resets it. *(critical)*"
  - "**No exploratory read of a sealed shard.** Event data and outcome aggregates of a `sealed`
    shard are refused everywhere (routes, MCP, accessor, readiness) until its recorded exposure;
    the refusal is typed, tested, and fail-closed. *(critical)*"
  - "**Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival
    through the sweep gate PLUS a valid Referee certificate. Train-only wins are labeled overfit.
    Never lower a minimum sample size, widen a gate, or pool across feeds/fingerprints to
    manufacture a survivor. *(critical)*"
  - "**No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
    *(critical)*"
  - "**The accessor is the only data door.** No module but `micro_accessor.py` opens snapshot or
    vault event data; origin fences fail closed; import-ban and source-scan guards enforce it.
    *(critical)*"
  - "**Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*"
  - "**Deterministic and seeded** — every random draw uses a recorded named seed via per-row
    streams; identical requests reproduce byte-identical results; no wall-clock, no unseeded
    randomness in any research artifact. *(critical)*"
  - "**Referee modules are byte-untouched this era** — `referee_handoff_ready` never implies
    current-Referee registrability of a flow predicate; that awaits a future named revision of the
    referee spec. *(critical)*"

## GOAL

Close the TR-1…TR-29 leakage-trap suite at 29/29 by building TR-23 (a new, sole-owner sealed-verdict
evaluator that recomputes and refuses a caller-asserted pass/fail) and TR-24 (the lineage-wide,
no-backdating confirmation-boundary formula) — each proven by deliberately breaking production
source and by a fixture built so the correct and corrupted paths can never coincide — plus four
small named passengers: J-10's own replay script genuinely run for the first time this era, two
stale module docstrings corrected, and two GAP-closing discriminating fixtures.

## BACKGROUND

Iteration 16's verdict is ESCALATE, so full depth with the independent auditor is mandatory this
round (Full trigger 3). The evaluator's own next-step recommendation names this exact scope: "the
last two safety tests… TR-23… TR-24… which belong together," explicitly finishing "the whole of
what remains in J-10… apart from the repeat-run check" — J-10 step 2 (the byte-identical
deterministic-rerun check) is therefore deliberately OUT OF SCOPE this round, not an oversight; J-10
stays `partial` even after this round lands, by design.

Direct code inspection (not assumed) confirms both traps are genuinely unbuilt, and materially more
than "add a trap test": `micro_sealed_evaluation.py` does not exist. `micro_graduation.py`'s
`record_sealed_evaluation` (lines 338-346) still takes `passed: bool` straight from the caller — its
own module docstring (lines 31-48) discloses this was "a disclosed T-1 interpretation call" made
because "the statistical MACHINERY… does not exist anywhere in this codebase yet." The r6 owner
ruling (2026-08-18, `assumptions.md` lines 757-814) closes exactly that gap: it defines
`SEALED_PASS_RULE_V1` FIRST (reusing the already-pinned §1 floors `WF_FOLD_MIN_OBSERVATIONS` / `_
SIGNAL_SESSIONS` / `_SYMBOLS`, no new constant) and names the new owner module explicitly.
`_proposed_confirmation_boundary` (lines 475-491) is equally naive today — it reads only
`validation_revealed_at`/`registered_at`/`evaluated_at` off the ONE `sequence_id` a caller supplies,
applies no embargo, and is explicitly the formula the owner ruling REJECTS ("the dev's 'latest
timestamp on surviving evidence rows' is REJECTED"). Neither `vault.py` nor `micro_chain_ledger.py`
needs to change: `vault.py` already carries no pass/fail concept (lifecycle only, unmodified `build_
vault_state` stays the read path); the new evaluation artifact persists through the ALREADY-EXISTING
`GraduationLedger`/`ROW_KIND_SEALED_EVALUATION` row-kind machinery (built on `HashChainedLedger`,
per this module's own established "one global chain, N row kinds" convention) — no new hand-rolled
chain, no touch to the frozen `micro_chain_ledger.py`.

The governing design constraint carried into this round: two consecutive prior rounds shipped a
brand-new trap that was structurally unable to fail, each caught only by the independent auditor —
iteration 15's opaque-pool sweep (sealed under an unregistered universe, so the leak branch never
ran) and iteration 16's TR-26 magnitude clause (a fixture whose revealing quote coincidentally
carried the same size the run already held, surviving a genuine dev TDD proof AND a reviewer
mutation). Acceptance below is written to require BOTH halves for TR-23 and TR-24: mutation evidence
(deliberately break production, show the specific named failure, restore byte-identical) AND fixture
discrimination (the correct and corrupted computed values must be numerically DIFFERENT, never
coincidental) — this is iteration 16's own named lesson, applied here before it can recur a third
time.

Required-still-passing is scoped narrower than iteration 16's own full 7-journey regression. That
was the right call for THAT round (its traps touched the accessor and exposure registry broadly
across the whole corpus). This round's surface is `micro_graduation.py` plus one new sibling module
plus two test-file fixture additions plus two docstrings — J-02 (observer) and J-03 (structure×flow)
share no changed module with this round the way J-01 (readiness aggregates), J-04 (Scout
`family_root_id` — read by the lineage scan), J-05 (walk-forward fold data — read by both traps),
J-07 (graduation itself, the journey whose owner module is rewritten), and J-08 (the `/desk`
sentinel surface J-10's own script walks) do, so the tighter 5-journey set stays fully relevant
without diluting the round's budget. J-06 stays excluded from Required-still-passing: it is
currently `partial`, not passing, and no file under `vault.py` changes this round (matching
iterations 14/15/16's own precedent for the identical reason).

`micro_accessor.py`'s docstring (lines 34-37) decision, per the carried instruction to decide and
say which: **CORRECT THE DOCSTRING, do not wire the fence.** TR-23's shard read is a POST-exposure,
whole-shard outcome recomputation, not a rolling-origin walk-forward fold — architecturally it is
the SAME `origin=None` UNFENCED pattern `micro_join.py`/`scout.py` already use for whole-corpus
reads, so it becomes a THIRD unfenced caller, not the walkforward.py-style fenced one the stale
docstring claims exists. Wiring a live fence into `walkforward.py` for its own sake, unasked, would
be exactly the "silent, unrequested behavior change smuggled into" an unrelated round that this
module's own docstring already warns against (T-1 discipline). Logged to the assumption ledger.

Lessons applied (pre-trimmed tail): iter-15 (every new trap needs a non-vacuity mutation-proof — TC
-8/TC-13 below); iter-16 (fixture discrimination is a SEPARATE, additional requirement from
mutation-proof — TC-9/TC-14, this round's central design constraint); iter-13 (attack the crash/edge
state, never trust an in-code "benign" comment — directly shapes B3/B4's exact-boundary fixtures,
TC-16/TC-17).

## IN SCOPE

### Backend

- [ ] New module `apps/backend/app/research/micro_sealed_evaluation.py` (spec §8.1): the sole
  scientific owner of the sealed-shard evaluation verdict. Implements the 7-step mandatory sequence
  verbatim — (1) require an ASSIGNED shard + a candidate spec frozen BEFORE that assignment;
  (2) verify `spec_hash`/`family_root_id`/outcome basis/sidedness/economic floor/sample+breadth
  floors against the candidate's own already-registered Scout spec; (3) obtain the shard ONLY
  through `micro_accessor.MicroAccessor` (unfenced `origin=None` — see BACKGROUND) plus
  `vault.build_vault_state` (existing, unmodified) to confirm genuine `exposed` binding to this
  EXACT `family_root_id`; (4) RECOMPUTE the outcome from canonical snapshot/outcome machinery —
  reuse `walkforward.py`'s existing statistical core (e.g. `summarize_fold_observations` or
  equivalent already-consulted function), never a second, independently-valued implementation, and
  never trust a caller-computed effect; (5) derive the verdict deterministically from
  `SEALED_PASS_RULE_V1`'s five conditions; (6) persist an immutable, hash-addressed evaluation
  artifact through the ALREADY-EXISTING `GraduationLedger`/`ROW_KIND_SEALED_EVALUATION` machinery;
  (7) return only that artifact's id+hash for the transition to consume.
- [ ] The evaluation artifact (spec §8.1, transcribed): candidate + spec identity and hashes ·
  `family_root_id` · shard identity and checksum AFTER lawful assignment · evidence class · process
  label · outcome basis · n / sessions / symbol breadth · effect and economic-floor inputs ·
  registered direction · rule id/version/hash · the deterministic verdict · the closed-vocabulary
  failure reason when not a pass. The verdict is **tri-state** — PASS / FAIL / `insufficient` (spec
  §8.1 point 1: "neither a pass nor a fail") — `insufficient` and FAIL must both refuse the
  `sealed_survivor` transition but stay distinguishable in the persisted artifact and in every later
  export bundle, never silently coerced to one boolean. Suggested (not mandatory) closed vocabulary:
  one reason per `SEALED_PASS_RULE_V1` condition, mirroring `scout.py`'s own `KILL_REASONS`
  convention — never a free-text message.
- [ ] `micro_graduation.py`: retire `record_sealed_evaluation`'s caller-supplied `passed: bool`
  parameter — the function (or its replacement call site) must call into the new owner module's
  computed verdict instead of accepting one. `evaluate_sealed_survivor_transition` and
  `build_export_bundle` updated to read the new artifact shape. Rewrite the module's own now-stale
  "disclosed T-1 interpretation call" docstring paragraph (lines 31-48) to describe the shipped,
  non-caller-supplied behavior — leaving it as-is would misdescribe the code exactly like the
  `micro_accessor.py` defect this round already targets.
- [ ] `micro_graduation.py`: rewrite `_proposed_confirmation_boundary` into the r6 §8.2 lineage-wide
  formula — `lineage_data_frontier` = max of each evidence item's own already-recorded timestamp
  field (never a newly-invented `observed_through` — no ledger row anywhere is named that; each row
  type already carries its own instant: scout trial rows carry `registered_at`, fold rows carry
  `validation_revealed_at`/`registered_at`, the new evaluation artifact carries its own recomputed
  outcome's timing) across EVERY evidence item the `family_root_id` lineage ever touched — survivors,
  killed/superseded Scout siblings (`build_export_bundle` already computes `scout_trials` filtered to
  this exact `family_root_id`, kills included — thread it into the new function, no new ledger join
  needed), folds of any verdict/class/process-label (not just `_eligible_folds`), and sealed
  evaluations of any verdict including FAIL/`insufficient`; then `evidence_safe_boundary` = frontier
  + the applicable embargo in session/market semantics; then `proposed_confirmation_boundary` = the
  first eligible boundary strictly after `max(evidence_safe_boundary, handoff_created_at)`. Rewrite
  the function's own stale "disclosed T-1 interpretation call" docstring to describe the new formula.
  If any evidence-item type genuinely has no usable own-timestamp field to stand in for "evidence
  consumed" (T-1: "an unspecified constant or rule is a drop… never an invention"), drop that item's
  inclusion, name the exact gap in the dev handoff, and flag it for an owner ruling rather than
  fabricating a value.
- [ ] `build_export_bundle`: persist the full derivation per spec §8.2 — `lineage_data_frontier`,
  the evidence ids contributing to the max, `frontier_observed_through`, the embargo rule id+value,
  `evidence_safe_boundary`, `handoff_created_at`, and `proposed_confirmation_boundary`.
- [ ] `apps/backend/app/research/micro_accessor.py`: correct the module docstring (lines 34-37) to
  state plainly that no current production caller constructs an origin-fenced read — no behavior
  change (decision above).
- [ ] `apps/backend/tests/test_micro_accessor.py`: a discriminating fixture closing GAP B3 — a
  viewing/exposure entry logged at EXACTLY the same instant a validation window is registered
  (`logged_at == instant`); asserts `is_exposed_before`'s strict `<` semantics (an exactly-simultaneous
  logging does NOT count as "before"), locking down the boundary the iteration-16 audit's `<`→`<=`
  mutation could otherwise silently drift.
- [ ] `apps/backend/tests/test_micro_observer.py`: a discriminating fixture closing GAP B4 — a
  session whose LAST event is a TRADE, not a quote; asserts `finalize()`'s `unavailable_at`/
  session-end stamp equals the trade's own timestamp and is numerically DIFFERENT from what the
  fixture's own `observed_through` would be if the session had ended on a quote instead — so the two
  values can never coincide and the assertion cannot pass for the wrong reason.
- [ ] New test file `apps/backend/tests/test_micro_sealed_evaluation.py` (TR-23) and additions to
  `apps/backend/tests/test_micro_graduation.py` (TR-24), each an explicitly-labeled, non-vacuity- AND
  discrimination-proven trap-suite entry (see TESTING REQUIREMENTS).
- [ ] `runs/goal-session-rapid-microscope/journey-scripts/J-10.json`: run it through the deterministic
  replay harness for the first time this era. If it passes, restore the two Playbook Evidence
  data-bearing assertions dropped in iteration 16 and re-run to confirm still green; if it does not
  pass, record the finding in the dev handoff rather than silently dropping anything further.
- [ ] No change to `vault.py`, `micro_chain_ledger.py`, `walkforward_ledger.py`'s persisted row shape
  (no new `family_root_id` field on fold rows — the module's own established "two identity spaces
  this era has never joined" precedent stays), `scout.py`, `scout_ledger.py`, `micro_readiness.py`,
  `tick_recorder.py`, `micro_routes.py`'s route shape, any `referee_*.py`, or any Playbook detector.

### Frontend

- None. This round is backend-only (a new module, a rewrite of one existing module's two
  sub-computations, two test-file fixture additions, two docstring corrections, one replay-script
  re-run). No `apps/frontend/**` source file changes. Frontend Present is still `yes` because
  browser-qa-agent must run this round regardless — J-10's own acceptance requires a browser-verified
  kept-product sentinel, and the required-still-passing set needs its replay/LLM checks dispatched.

### New user-facing capability

None this iteration — this round hardens the trap suite and consolidates ownership of an internal
verdict computation; the product surface is unchanged.

### New information displayed

None new. `GET /research/desk/micro/graduation`'s served shape gains fields inside its EXISTING
`sealed_evaluations`/export-bundle payload (verdict tri-state, the artifact's provenance fields, the
lineage-boundary derivation) — the endpoint is not fetched by any `/desk` section or MCP tool today
(confirmed by grep: zero hits for "graduation" in `page.tsx` or `app/mcp/*.py`), so nothing rendered
changes.

### New user actions

None.

### UI surface changes

None. No `/desk` section is touched.

### Product surface delta

No visible change to any page. The graduation endpoint's internal correctness improves; its shape
and route stay exactly as registered.

### Blueprint conformance

No new surfaces. TR-23/TR-24 are backend-only, living entirely under the ALREADY-registered
"Graduation states (J-07) | keyless/automated; states surface via the Scout Ledger / Walk-Forward /
Vault rows they attach to" home in `blueprint.md`'s Information Architecture table — no nav-skeleton
change, no reapproval file.

### Data-contract additions

None new. This round moves the sealed-verdict sub-computation of the ALREADY-registered "Graduation
states + export bundles" row to a new internal owner module (`micro_sealed_evaluation.py`) per the r6
ruling itself — `micro_graduation.py` stays the persistence/transition layer and the ONE serving
endpoint stays exactly `GET /research/desk/micro/graduation`; no second endpoint, no shape
duplication, single source of truth preserved. `blueprint.md`'s Data Contract table is updated to
name the new sub-owner (an additive, in-place edit — no new row, matching this file's own
iter-3/iter-16 note precedent for sub-owner clarifications); an iter-17 note is added recording it.

## OUT OF SCOPE

- J-10 step 2, the byte-identical deterministic-rerun check — explicitly carved out by iteration
  16's own next-step language ("the whole of what remains… apart from the repeat-run check");
  deferred to a future round, not silently folded in. J-10 stays `partial` at 29/29 traps — the
  planned outcome, not a shortfall.
- J-09 "The pilot studies" — TR-22 (its named prerequisite) already landed, but starting J-09 itself
  stays explicitly deferred by every evaluator round since 13 and is not reopened here; this round's
  capacity is fully committed to TR-23/TR-24 plus passengers.
- J-06 real-tape recording and any operator-attended recorder/vault act — human-blocked; standing
  "do NOT record real tape" instruction stays in force.
- Any change to `vault.py` itself, or intercepting `DatasetStore` to change vault/Referee behaviour
  indirectly — both explicitly rejected by the owner in an earlier round.
- Any change to `referee_*.py`, `micro_chain_ledger.py`, the engine, `Config`, or any Playbook
  detector — frozen rails.
- Wiring `micro_accessor.py`'s origin fence into a live production caller — the alternative to the
  docstring fix, explicitly NOT chosen this round (see BACKGROUND and the assumption ledger).
- Any change to `walkforward_ledger.py`'s persisted fold-row shape (e.g. adding a `family_root_id`
  field) — the lineage scan threads already-computed `scout_trials`/`fold_results` through the new
  boundary function instead; no new join column.
- The 3 other, older open minor anti-goal items not named by iteration 16's next-step recommendation
  — left undisturbed; none are owner-owed.
- The framework-level ask "make the harness count replay scripts among a round's changed files" —
  outside this session's product scope (a tool problem for the framework maintainers, matching how
  this session has treated identical harness-behavior asks in every prior round).
- Widening Required-still-passing to a full regression of all 7-10 currently-passing journeys — this
  round's touched surface does not warrant it (see BACKGROUND); J-02/J-03 are excluded.
- Any new MCP tool, any new `/desk` section, any nav-skeleton change, any new `Config` field, any
  fingerprint-affecting change, any new runtime dependency.

## DEFINITION OF DONE

- [ ] TR-23 lands as an explicitly-labeled, non-vacuity- and discrimination-proven trap-suite entry
  in `test_micro_sealed_evaluation.py`; `micro_sealed_evaluation.py` is the sole scientific owner;
  `record_sealed_evaluation`'s caller-supplied `passed: bool` is retired (TC-1..TC-9)
- [ ] TR-24 lands as an explicitly-labeled, non-vacuity- and discrimination-proven trap-suite entry;
  `_proposed_confirmation_boundary` is rewritten to the lineage-wide r6 §8.2 formula; `build_export_
  bundle` persists the full derivation (TC-10..TC-14)
- [ ] Both traps' acceptance fixtures are verified DISCRIMINATING — correct and corrupted computed
  values are numerically different, never coincidental (TC-9, TC-14, explicitly)
- [ ] `micro_accessor.py`'s and `micro_graduation.py`'s stale docstrings are corrected to describe
  shipped behavior, documentation-only, no test regression (TC-15)
- [ ] The two GAP-closing discriminating fixtures (B3 exact-instant boundary, B4 trade-terminated
  session) land (TC-16, TC-17)
- [ ] J-10's stored replay script is genuinely run for the first time this era; if it passes, the
  two dropped Playbook Evidence assertions are restored and it is re-run green (TC-18)
- [ ] J-10's trap count reaches 29/29 (TR-1 through TR-29 all present); J-10 itself stays `partial`
  (step 2 remains explicitly out of scope) — the planned outcome (TC-19)
- [ ] Full backend suite green, 0 failures, passed count ≥ 3238 (iteration-16 baseline); frozen
  rails re-verified: fingerprint `08e471b10130e1e2`, six `referee_*.py` + `micro_chain_ledger.py`
  SHA-256 match iteration-0, MCP tool count = 26, zero new `Config` fields, `tsc --noEmit` clean
  (TC-20)
- [ ] Target journey J-10 verified via the independent auditor + browser-qa-agent
- [ ] Required-still-passing journeys J-01, J-04, J-05, J-07, J-08 remain green with zero
  regressions (deterministic replay + LLM fallback for J-07 — mechanically verified) (TC-21)
- [ ] No anti-goal violation introduced — no real tape recorded, J-09 untouched, `vault.py` /
  `referee_*.py` / `micro_chain_ledger.py` / `walkforward_ledger.py`'s row shape byte-unchanged, MCP
  stays at 26 tools, no nav-skeleton or UI change
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-17-dev.md`

## TESTING REQUIREMENTS

- Browser: J-10 (kept-product sentinel — cockpit `/` live tape + chart, `/structure` load + Tradable
  Map, every shipped `/desk` section including the three Referee sections and all four
  Rapid-Microscope sections, browser-verified via the store-scoped rig; J-10's own acceptance text
  names this explicitly); J-01, J-04, J-05, J-08 (deterministic replay); J-07 (LLM fallback,
  direct-endpoint navigation to `GET /research/desk/micro/graduation` — no golden script exists for
  it by design, carried from iteration 15)
- Unit/integration: TC-1 through TC-19 below, each new trap assertion paired with its own
  non-vacuity mutation-proof AND its own discrimination check (mirroring `test_mcp_server.py`'s TR-2
  fix and `test_micro_observer.py`'s TR-26 twin-fixture fix — copy the established pattern, do not
  re-derive it)
- Error cases: TR-23's typed refusal on a rule changed after assignment (never a pass, never a
  silent skip); TR-23's tri-state `insufficient` never silently coerced to FAIL or PASS; TR-24's
  boundary never computed earlier than either the proposed or the Referee registration boundary
  (never backdated)

Test-first contract:

- TC-1: given the OLD `record_sealed_evaluation` call shape (a caller-supplied `passed: bool`),
  when it is attempted against the new evaluator's contract, then it is impossible/refused — the
  parameter no longer accepts a caller-asserted verdict.
- TC-2: given a registered candidate spec (sidedness, economic floor, `family_root_id`, frozen
  before assignment) and a fixture vault shard assigned then exposed to that exact family, when the
  new `micro_sealed_evaluation.py` owner function runs the full mandatory sequence, then it returns
  a deterministic verdict derived from `SEALED_PASS_RULE_V1`'s five conditions and persists an
  immutable artifact carrying candidate/spec identity+hashes, `family_root_id`, shard identity+
  checksum, evidence class, process label, outcome basis, n/sessions/symbol breadth, effect+floor
  inputs, registered direction, and rule id/version/hash.
- TC-3: given a fixture whose registered rule is changed AFTER shard assignment, when the evaluator
  runs, then it fails closed with a closed-vocabulary reason naming the rule-identity mismatch —
  never a pass.
- TC-4: given identical inputs (same candidate spec, same assigned/exposed shard), when the
  evaluator runs twice, then the second run returns a byte-identical artifact and verdict to the
  first.
- TC-5: given a `(family_root_id, dataset_id)` pair with an already-recorded sealed evaluation, when
  a second evaluation attempt for the SAME pair is made, then it is refused (or idempotently
  replayed if genuinely identical inputs) — never a second, different draw.
- TC-6: given a fixture below `WF_FOLD_MIN_OBSERVATIONS`/`_SIGNAL_SESSIONS`/`_SYMBOLS`, when
  evaluated, then the verdict is `insufficient` — distinct from both PASS and FAIL — and the single
  evaluation shot is still consumed (no second attempt permitted) because the shard was genuinely
  exposed.
- TC-7: given a family whose sealed evaluation FAILED, when `build_export_bundle` is called for
  that family at any later graduation state, then the failed verdict is present in the bundle's
  `sealed_evaluations`, permanently.
- TC-8 (mutation evidence): given production source with `SEALED_PASS_RULE_V1`'s floor/direction/
  magnitude/rule-identity check deliberately weakened, when the TR-23-labeled test suite runs
  against that weakened code, then it FAILS naming the specific wrong verdict the corrupted code
  produced; restoring the code byte-identically makes it pass again.
- TC-9 (fixture discrimination): given a fixture pair where the correctly recomputed effect and a
  deliberately corrupted computed effect are DIFFERENT numeric values (never coincidentally equal),
  when both are run through `SEALED_PASS_RULE_V1`, then the correct and the corrupted paths produce
  DIFFERENT verdicts — the assertion cannot pass for the wrong reason.
- TC-10: given a family_root_id lineage containing a surviving candidate and a KILLED Scout sibling
  (same family, different variant) whose own evidence's recorded timestamp is LATER than the
  survivor's own frontier, when `proposed_confirmation_boundary` is computed for the export bundle,
  then it is pushed to strictly after the killed sibling's timestamp plus the applicable embargo —
  not merely the survivor's own evidence.
- TC-11: given a deferred feature whose `anchor_at < observed_through` inside the lineage's evidence
  set, when the lineage frontier is computed, then it moves to that feature's `observed_through`,
  never its earlier `anchor_at`.
- TC-12: given a `proposed_confirmation_boundary` and an independent, LATER Referee
  registration-time boundary, when the final confirmation boundary is derived, then it equals
  `next_eligible(max(proposed, registration))` — never earlier than either input.
- TC-13 (mutation evidence): given production source with the lineage scan deliberately narrowed
  back to "only the survivor's own sequence" (the rejected naive form), when the TR-24-labeled test
  suite runs, then it FAILS at the killed-sibling assertion naming the wrong (too-early) boundary it
  produced; restoring the lineage-wide scan makes it pass again.
- TC-14 (fixture discrimination): given the killed sibling's own timestamp and the survivor's own
  frontier set to DELIBERATELY DIFFERENT calendar instants (never coincidentally equal), when the
  boundary is computed under the correct rule versus the naive single-sequence rule, then the two
  rules produce OBSERVABLY DIFFERENT boundary dates.
- TC-15: given the corrected `micro_accessor.py` module docstring, when grepped against every
  production construction site of `MicroAccessor(`, then the docstring's claim matches the actual
  call sites exactly (zero origin-fenced production callers); given `micro_graduation.py`'s
  rewritten docstrings, when read against the shipped code, then neither describes the retired
  caller-supplied-verdict or single-sequence-boundary behavior.
- TC-16 (GAP B3): given a viewing/exposure entry logged at EXACTLY the same instant a validation
  window is registered (`logged_at == instant`), when `is_exposed_before` is queried at that exact
  instant, then it returns the boundary-correct result under strict `<` (an exactly-simultaneous
  logging does not count as "before").
- TC-17 (GAP B4): given a session fixture whose LAST event is a TRADE, not a quote, when `finalize
  ()` stamps the session-end value, then it equals the trade's own timestamp and is numerically
  DIFFERENT from what the fixture's `observed_through` would be had the session ended on a quote.
- TC-18: given `runs/goal-session-rapid-microscope/journey-scripts/J-10.json`, when it is run
  through the deterministic replay harness for the first time this era, then a pass/fail result is
  recorded; if it passes, the two Playbook Evidence data-bearing assertions removed in iteration 16
  are restored and the script re-run reports green a second time.
- TC-19: given `apps/backend/tests/` after this iteration, when every `TR-` label is swept and
  deduplicated (TR-17's a/b/c sub-parts counted once), then exactly 29 distinct trap ids (TR-1
  through TR-29) are present, including TR-23 and TR-24 by name.
- TC-20: given the full backend test suite, when it is run after this iteration's changes, then it
  reports 0 failures with a passed count ≥ 3238 (the iteration-16 baseline); `Config().config_
  fingerprint()` prints `08e471b10130e1e2`; the six `referee_*.py` files + `micro_chain_ledger.py`
  SHA-256 match the iteration-0 baseline; the MCP tool list is unchanged at 26; `tsc --noEmit` is
  clean.
- TC-21: given J-01, J-04, J-05, J-08's stored golden replay scripts (and J-07's direct-endpoint LLM
  navigation), when the required-still-passing regression sweep runs, then all five verify against
  the current build with zero regressions recorded.

## NOTES

- Build anchors (re-locate by symbol name, never line arithmetic — authored against the iteration-16
  commit): `micro_graduation.py` — module docstring "disclosed T-1 interpretation call" paragraph
  (lines 31-48), `record_sealed_evaluation` (338-403), `evaluate_sealed_survivor_transition`
  (406-464), `_latest_timestamp`/`_proposed_confirmation_boundary` (470-491), `build_export_bundle`
  (494-555), `_REQUIRED_BUNDLE_FIELDS`/`bundle_validates` (558-570), `ROW_KIND_SEALED_EVALUATION`
  (already in `__all__`, reuse — do not add a new row kind). `micro_accessor.py` — module docstring
  "Two callers, two disciplines" paragraph (lines 25-37, the claim to correct), `MicroAccessor.
  read_snapshot_rows`, `is_exposed_before` (line 158). `micro_observer.py` — `finalize()` (line
  714). `walkforward.py` — `evaluate_mode_b_fold` (581, the Mode-B evaluation shape TR-23's
  recomputation most closely resembles), `summarize_fold_observations` (the reuse candidate for the
  statistical core — "consulted, never reimplemented," this codebase's own established convention
  for `sequence_verdict`), `WF_FOLD_MIN_OBSERVATIONS`/`_SIGNAL_SESSIONS`/`_SYMBOLS` (167-169),
  `classify_evidence_class` (439). `vault.py` — `build_vault_state`, `STATE_EXPOSED` (read-only,
  unmodified). `scout.py`/`scout_ledger.py` — trial rows carry `registered_at` (confirmed by grep;
  no row anywhere in this codebase is named `observed_through` literally — see the IN SCOPE note on
  deriving the lineage frontier from each row's own existing timestamp field).
- Spec sections to implement verbatim: `docs/rapid-validation-spec.md` §8.1 (TR-23, lines 796-840),
  §8.2 (TR-24, lines 842-870), §9's TR-23/TR-24 table rows (899-900). Owner-ruling rationale:
  `runs/goal-session-rapid-microscope/state/assumptions.md` lines 757-814 (2026-08-18, "OWNER
  RULINGS (4) → spec revision r6 'the sealed verdict has an owner'") — read verbatim before
  designing the artifact shape or the boundary formula; it directly rejects at least one plausible
  naive implementation ("latest timestamp on surviving evidence rows") that this round must not
  reintroduce.
- Lessons applied (full text pre-trimmed in the dispatch prompt): iter-15 (every new trap needs a
  non-vacuity mutation-proof — TC-8/TC-13 are exactly that); iter-16 (a mutation-proof alone is
  insufficient — the fixture itself must be built so it can DISCRIMINATE the right answer from the
  wrong one, never coincide — TC-9/TC-14 are this round's answer to that exact lesson, the reason
  this spec calls it out as its own acceptance clause rather than folding it into the mutation-proof
  bullet); iter-13 (attack the crash/edge state, never trust an in-code "benign" comment — B3/B4's
  exact-boundary fixtures, TC-16/TC-17); iter-11 (widening one side of a paired mechanism re-opens
  the leak through the untouched twin — informs why TC-6's tri-state `insufficient` must stay
  distinguishable rather than collapsing into a boolean, and why the lineage scan must cover folds
  "of any verdict," not just eligible ones).
- Two assumption-ledger entries logged this iteration: the `micro_accessor.py` docstring
  correct-vs-wire decision, and the lineage-frontier `observed_through`-derivation/drop-if-impossible
  discipline. See `runs/goal-session-rapid-microscope/state/assumptions.md`.
- `blueprint.md` updated: the Data Contract table's Graduation row now names `micro_sealed_
  evaluation.py` as the sealed-verdict sub-owner (additive, no new row, no endpoint change); an
  iter-17 note records the reasoning, matching this file's own iter-3/iter-11/iter-16 note
  precedent for sub-owner clarifications that don't change a row's shape or serving path.
