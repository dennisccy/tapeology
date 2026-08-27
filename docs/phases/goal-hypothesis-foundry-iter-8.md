# Goal Iteration 8 — The final Foundry truth screen (J-08)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** hypothesis-foundry
- **Iteration:** 8
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior evaluator verdict (iter-7) was `ESCALATE`; per this agent's own binding
  rule an ESCALATE verdict forces full depth with no exceptions. (Trigger 1 also genuinely holds: this
  iteration's own DoD spans ≥3 modules whose interactions no single journey's tests already cover —
  `foundry_source_registry.py`/`micro_routes.py` read path, `foundry_runner.py`/`foundry_ledger.py`
  survivor accounting, `apps/frontend/app/desk/page.tsx`, and four separate guard-test files
  (`test_desk_ui_guards.py`, `test_vault.py`'s TR-2 sweep, `test_copy_discipline.py`,
  `test_run_hypothesis_foundry_real_exhaust.py`) — but trigger 3 alone is sufficient and mandatory.)
- **Frontend Present:** yes
- **Target journeys:** J-08
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-06, J-07 (all seven currently
  passing; every one reads through the same single canonical endpoint this iteration extends,
  `GET /research/desk/micro/foundry`, so all seven are relevant by the Data-Contract-sharing rule —
  this is also the era's closing iteration, matching six of the last seven verdicts' own full-regression
  practice)
- **Anti-goal reminders:**
  - Single source of truth. Every shared scientific value has one canonical backend owner; REST/UI/MCP
    never independently recompute it.
  - Persistence stays scoped. Fetching/recording/exposure is always an explicit operator act; page
    loads and Foundry reads never record market data. `GET /research/desk/micro/foundry` and every page-
    load GET are read-only and never compute/evaluate a candidate or trigger the exhaust runner.
  - No second real generation epoch.
  - No science-affecting code/spec/manifest change after the first-read lock.
  - No candidate invented after the real manifest freezes. No late variant insertion.
  - No automatic ranking/selection among diagnostic survivors for future protected evidence.
  - No claim that `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN` is OOS evidence or proof of edge.
  - The opaque unresolved research pool remains inference-resistant. The new Foundry REST/UI/optional
    MCP surface joins the existing TR-2-style inference sweep and may disclose only identity-safe
    aggregate safety facts, never enough to identify a still-unexposed member.
  - No profit claims and no advice. Any return/economic measurement is research evidence with its unit,
    n, assumptions, evidence class, and caveats; no imperative trading cue, price target, or prediction
    promise.
  - No browser proof based on fabricated fixture state when a journey claims to show real final state;
    fixture and real views must be visibly distinguished.
  - No Goal Mode workaround that edits/deletes/xfails a scientific guard merely to pass a journey.
  - Anti-goal violations use the existing Goal Mode anti-goal violation state/disposition machinery;
    they are not dismissed in prose.

## GOAL

The operator visiting `/desk` → Hypothesis Foundry sees one final, top-level summary of the real
epoch's complete truth — source dispositions, family/variant/survivor counts, freeze integrity, and
evidence class — plus a detail drill-in into at least one real blocked source's full canonical
provenance, closing the era's last remaining journey (J-08).

## BACKGROUND

Every other journey (J-01–J-07) has passed since iter-6/iter-7; J-08 has never been targeted in seven
consecutive evaluations because the goal's own Binding Execution Order sequences it last (confirmed by
two goal-evaluator assumption entries, iter-6 and iter-7, that this literal-match streak does not carry
rung C.4's intended meaning). The iter-7 evaluator's own next-step recommendation is unambiguous: build
J-08 now, at full depth, no sealed-file edits. This session's `Prior verdict: ESCALATE` independently
forces full depth per this agent's binding rule regardless of any recommendation.

Codebase inspection before writing this spec found the real gap precisely: the six existing Foundry
subsections (Sources/Compiler, Interpreter fixtures, Freeze/Integrity, Epoch/Manifest, Runner/
Checkpoint, Hermetic Oracles) already surface most J-08-required facts, but scattered — there is no
single top-level synthesis — and the REAL `epoch_manifest.source_dispositions[]` entries (read from the
committed `docs/hypothesis-foundry/epoch-manifest.json`) carry only `source_id`/`disposition`/
`lineage_refs`/`alias_refs`, never the full §1.4 canonical provenance (quoted spans, source hash,
mechanism statement, direction/comparator derivation, threshold provenance, audit note) that already
exists per-record in the separately committed `docs/hypothesis-foundry/source-registry.json` (verified
directly: 11 real source records, 0 `COMPILED`, disposition mix includes `ALIASED_PROXY_ONLY` ×2,
`BLOCKED_DIRECTION` ×4, `BLOCKED_SPEC_GAP` ×1, `ALIASED_VARIANT_VOCABULARY` ×1, `EXCLUDED_*` ×3 — ample
real material for J-08 step 2's "open at least one blocked source" requirement). `exhaust_progress` also
has no explicit survivor count field, only `frozen_ready_total`/`terminal_count`, both already `0`.

Applying prior lessons directly: (a) iter-1's lesson — the scoped QA rig must see the REAL committed
`docs/hypothesis-foundry/` artifacts (via the established `cp`-into-rig-root pattern), or every J-08
browser check honestly degrades to "not recorded yet"; (b) iter-6/iter-7's lesson — capture every Foundry
subsection screenshot through `demo_runner --mode verify`, never the Chrome-MCP deep-scroll path, which
has returned blank PNGs twice; (c) iter-6's lesson — never edit any of the 59 freeze-set-sealed files to
make a check pass (this iteration touches none of them: `micro_routes.py`, `foundry_source_registry.py`
read-path additions, `foundry_runner.py`'s `read_exhaust_progress()`, and
`apps/frontend/app/desk/page.tsx` are all non-sealed); (d) iter-7's lesson — the sealed-CLI/canonical-
helper equivalence test in `test_run_hypothesis_foundry_real_exhaust.py` is a tautology on this
permanently-empty manifest and must stop being described as drift protection in its own docstring —
the freeze-set hash pinning is what actually prevents divergence; (e) iter-7's lesson — replay this
iteration's own TARGET journey (J-08), not only the regression set, regardless of the frontend flag.

The two HUMAN-owned blocking anti-goal entries carried in `iteration-state.md` ("No second real
generation epoch" ratification; "Persistence stays scoped" page-load-GET-writes-a-lock-file fix, whose
only legal repair site is the sealed `foundry_runner.py`) are NOT this iteration's target and are not
attempted — both require an owner ruling this agent may not make, and the second requires editing a
sealed file this iteration must not touch. Per the priority rubric's "don't pick a human-blocked
journey" rule, J-08 (not human-blocked) is the correct and only target this iteration.

## IN SCOPE

### Backend
- [ ] Extend the real (non-fixture) source-disposition read path so `epoch_manifest.source_dispositions[]`
      entries additionally carry the full §1.4 canonical provenance already present per-record in the
      committed `docs/hypothesis-foundry/source-registry.json` (`quoted_spans`, `source_hash`,
      `mechanism_statement`, `operative_formula_refs`, `direction_derivation`, `comparator_derivation`,
      `threshold_provenance`, `superseded_fields`, `alternatives`, `audit_note`, `lineage_id`) — reading
      the already-tracked file directly (same convention `read_epoch_manifest_view()` already uses for
      `epoch-manifest.json`/`freeze-record.json`), never through a second compile pass and never through
      `resolve_foundry_dir()`.
- [ ] Add `exhaust_progress.diagnostic_survivor_count` to `read_exhaust_progress()` in
      `foundry_runner.py` — a genuine read of the real trial ledger's terminal rows whose `outcome ==
      "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"`, not a copy/re-derivation of `terminal_count`.
- [ ] Add a new top-level `final_summary` key to `GET /research/desk/micro/foundry`, computed once at
      module-import time (same GET-never-computes convention as every other Foundry view) as a PURE
      projection over already-computed values — `_EPOCH_MANIFEST_VIEW`'s `source_dispositions`/
      `families` and the real `exhaust_progress` result — with zero independent recomputation of any
      value already owned elsewhere (in particular, reuse the existing sole-owner
      `compute_frozen_ready_total` helper's already-computed result; do not add a second counting site).
- [ ] Correct the docstring/inline comment on the sealed-CLI/canonical-helper equivalence test in
      `apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py` (no assertion-logic change, no
      sealed-file change) to state plainly that the freeze-set hash pinning — not the equivalence
      assertion — is what prevents the two formulas from silently diverging, per the iter-7 finding.

### Frontend
- [ ] Add a new "Final Summary" subsection to the `/desk` → Hypothesis Foundry panel
      (`data-testid="foundry-final-summary"`), rendered immediately below the existing panel header
      (era identity/baseline) and above the six existing subsections, reading `final_summary` verbatim:
      source counts by disposition, family/variant counts, `diagnostic_survivor_count` with an explicit
      honest zero-survivor statement when it is `0`, `freeze_integrity_verdict`, evidence class,
      `protected_read_count`, and `exhaust_complete`. No client-side arithmetic on any of these fields.
- [ ] Add a per-source detail drill-in inside the Final Summary subsection using the same `<details>`
      convention already used elsewhere in the Foundry subsections — one `<details>` per real source
      record, expandable to show its `mechanism_statement`, `audit_note`, `direction_derivation`,
      `comparator_derivation`, `threshold_provenance`, `superseded_fields`, `alternatives`, and every
      `quoted_spans` entry's `text`/`location`, all read verbatim (no advisory copy, no recomputation).
- [ ] Reuse the single already-established `fetchDeskFoundry()` fetch — add no new `useEffect`,
      `setTimeout`, or `setInterval` (the page's pinned effect census must not move).

### New user-facing capability
The operator can see, in one place, the real epoch's complete final state (source/family/variant/
survivor/integrity/evidence summary) and drill into any individual real source record's full cited
provenance, without leaving `/desk`.

### New information displayed
`final_summary`'s seven fields (see Data-contract additions) plus, per real source record, its full
§1.4 provenance fields via the new detail drill-in.

### New user actions
Expand/collapse a source's detail `<details>` disclosure inside the new Final Summary subsection.

### UI surface changes
One new subsection (`foundry-final-summary`) inside the already-shipped `/desk` → Hypothesis Foundry
panel. No new page, no new nav entry.

### Product surface delta
`/desk` → Hypothesis Foundry now has a top-level "final truth" view synthesizing the six existing
subsections' real-epoch state, plus per-source detail drill-in — closing the panel's last planned gap.

### Blueprint conformance
Lives under the already-registered Information Architecture home: `/desk` → Hypothesis Foundry (Desk
nav section), specifically the row "J-08 Final Foundry truth ... | `/desk` → Hypothesis Foundry
(top-level summary + detail view) | Desk" already present in `state/blueprint.md` since baseline. No
nav-skeleton change; no `blueprint.reapproval-requested` needed.

### Data-contract additions
- `epoch_manifest.source_dispositions[].quoted_spans: list[{text: str, location: str}]` — computed by
  `app/research/foundry_source_registry.py`'s existing `SourceRecord`/serializer (reused), read via the
  existing `read_epoch_manifest_view()` path in `micro_routes.py`; served by
  `GET /research/desk/micro/foundry` (`epoch_manifest.source_dispositions[]`).
- `epoch_manifest.source_dispositions[].source_hash: str` (64-char lowercase hex sha256) — same module/
  endpoint as above.
- `epoch_manifest.source_dispositions[].mechanism_statement: str`,
  `.operative_formula_refs: list[str]`, `.direction_derivation: str`, `.comparator_derivation: str`,
  `.threshold_provenance: str | null`, `.superseded_fields: dict[str, str]`, `.alternatives: list[str]`,
  `.audit_note: str`, `.lineage_id: str | null` — same module/endpoint as above.
- `exhaust_progress.diagnostic_survivor_count: int >= 0` — computed by `app/research/foundry_runner.py`'s
  `read_exhaust_progress()` (reused function, additive field); served by
  `GET /research/desk/micro/foundry` (`exhaust_progress.diagnostic_survivor_count`).
- `final_summary.source_counts_by_disposition: dict[str, int]` (keys drawn from the closed §7.1
  disposition vocabulary; values sum to the total required-source-object count, 11 for the real epoch) —
  computed by a new pure-projection helper in `app/research/micro_routes.py` over the already-computed
  `_EPOCH_MANIFEST_VIEW` (no second read of `source-registry.json`/`epoch-manifest.json`); served by
  `GET /research/desk/micro/foundry` (`final_summary.source_counts_by_disposition`).
- `final_summary.family_count: int >= 0`, `.variant_count: int >= 0`,
  `.frozen_ready_total: int >= 0` (copied verbatim from the existing sole-owner
  `compute_frozen_ready_total` result, never recomputed), `.diagnostic_survivor_count: int >= 0`
  (copied verbatim from `exhaust_progress.diagnostic_survivor_count` above),
  `.freeze_integrity_verdict: str`, `.evidence_class: str` (constant
  `"historical_exposed_diagnostic"`), `.protected_read_count: int >= 0`, `.exhaust_complete: bool`,
  `.epoch_status: str` — same new helper/module/endpoint as the row above; every value is a projection
  of an already-canonically-owned field, never a second computation site.

## OUT OF SCOPE

- The optional read-only MCP proxy (`desk_micro_foundry`) — explicitly deferrable per `docs/goal.md`
  Product Shape ("MCP") and non-blocking for `GOAL_ACHIEVED`.
- Resolving either open HUMAN-owned blocking anti-goal entry ("No second real generation epoch"
  ratification; "Persistence stays scoped" page-load-GET-writes-a-lock-file fix) — both require an
  owner ruling this agent may not make, and the second's only legal repair site is a sealed file.
- Any edit to any of the 59 freeze-set-sealed files (verified byte-identical every iteration since
  iter-6) — none of this iteration's files are sealed, and none may become so.
- A second real generation epoch, any change to `source-registry.json`/`epoch-manifest.json`/
  `freeze-set.json`/`freeze-record.json` content, or re-running the exhaust CLI against the frozen
  real epoch.
- Re-verifying or re-building the internals of the six already-shipped fixture/real subsections
  (Sources/Compiler, Interpreter fixtures, Freeze/Integrity, Epoch/Manifest, Runner/Checkpoint,
  Hermetic Oracles) — only their continued regression-passing status is checked this iteration.
- Any new top-level page or nav entry.

## DEFINITION OF DONE

- [ ] J-08 passes via browser-qa-agent (TC-1 through TC-4)
- [ ] Required-still-passing journeys J-01–J-07 remain green via deterministic replay (LLM fallback for
      any journey lacking a stored golden) (TC-12)
- [ ] No anti-goal violation introduced: zero sealed-file byte changes, zero new page-load compute,
      zero client-side recomputation of any served numeric field
- [ ] Full backend suite passes, TypeScript compile is clean, zero regressions (TC-11)
- [ ] `final_summary` key present and correct on `GET /research/desk/micro/foundry` (TC-1)
- [ ] Source detail drill-in renders full §1.4 provenance for a real blocked source (TC-2, TC-3)
- [ ] REST body and rendered DOM values match byte-for-byte (TC-5)
- [ ] Numeric-field anti-recomputation guard extended to cover the Foundry final-summary surface (TC-6)
- [ ] Page effect/timer census unchanged (TC-7)
- [ ] TR-2 opaque-pool inference sweep still passes with the new fields present (TC-8)
- [ ] Copy-discipline lint still passes over the new JSX (TC-9)
- [ ] `test_run_hypothesis_foundry_real_exhaust.py` docstring corrected per the iter-7 finding (TC-10)
- [ ] Dev handoff written at `docs/handoffs/goal-hypothesis-foundry-iter-8-dev.md`

## TESTING REQUIREMENTS

- Browser: J-08 (target, all 5 steps); J-01–J-07 (regression set, deterministic replay + LLM fallback).
  Capture every Foundry subsection screenshot via `demo_runner --mode verify`, never the Chrome-MCP
  deep-scroll path (it has returned blank PNGs twice this session). Before the pass, ensure the scoped
  QA rig can see the real committed `docs/hypothesis-foundry/` artifacts (the established `cp`-into-
  rig-root pattern from iter-1/iter-2), or every real-epoch check will honestly (and wrongly, for this
  iteration's purposes) degrade to "not recorded yet."
- Unit/integration: `read_exhaust_progress()`'s new `diagnostic_survivor_count`; the new `final_summary`
  projection helper (unit test proving it reads, never recomputes, each underlying field); the extended
  `epoch_manifest.source_dispositions[]` provenance fields against the real committed source-registry
  content; the corrected test docstring in `test_run_hypothesis_foundry_real_exhaust.py`.
- Error cases: `final_summary` on a `not_yet_generated`/`generated_uncommitted` epoch status degrades
  honestly (no fabricated counts); a source record missing an optional provenance field (e.g.
  `threshold_provenance: null`) renders as an explicit absence, never a blank or a client-invented value.

Test-first contract:

- TC-1: given the real committed Foundry epoch (status `"committed"`, 11 source records, 0 compiled
  families), when a client calls `GET /research/desk/micro/foundry`, then the response body's
  `final_summary` object has `source_counts_by_disposition` values summing to 11, `family_count == 0`,
  `variant_count == 0`, `frozen_ready_total == 0`, `diagnostic_survivor_count == 0`,
  `freeze_integrity_verdict == "green"`, `protected_read_count == 0`, and `exhaust_complete == true`.
- TC-2: given that same response, when the operator visits `/desk` and expands the Hypothesis Foundry
  panel, then a subsection with `data-testid="foundry-final-summary"` renders those seven values
  verbatim, positioned below the era-identity header and above the six existing subsections.
- TC-3: given the real source registry's `pilot-study-1-range-wall-failed-aggression` record
  (disposition `ALIASED_PROXY_ONLY`), when the operator opens its detail `<details>` disclosure in the
  Final Summary source list, then the expanded element shows its `mechanism_statement`, `audit_note`,
  `direction_derivation`, `comparator_derivation`, and at least one `quoted_spans` entry's `text` and
  `location`, all read verbatim from `epoch_manifest.source_dispositions[]`.
- TC-4: given the real epoch has zero compiled families, when the operator inspects the Final Summary's
  survivor area, then it shows an explicit statement that zero diagnostic survivors exist for this
  epoch (`diagnostic_survivor_count == 0` rendered as text, not merely a bare `0`).
- TC-5: given the served `GET /research/desk/micro/foundry` JSON and the rendered `/desk` DOM captured
  in the same browser-qa pass, then every `final_summary` and source-detail value in the DOM equals the
  corresponding served JSON field (case-sensitive string/number equality).
- TC-6: given `test_desk_ui_guards.py`'s numeric-field anti-recomputation sweep, when the suite runs,
  then a new `test_desk_page_price_arithmetic_guard_catches_foundry_field_arithmetic` case exists,
  passes against the shipped page, and fails when a seeded client-side-arithmetic violation (e.g.
  `final_summary.family_count - 1`) is injected into the Foundry final-summary render path.
- TC-7: given the page's pinned effect/timer census (`test_table_sort_guards.py`/
  `test_desk_ui_guards.py`), when the suite runs after this iteration's frontend changes, then the
  pinned count is unchanged from its pre-iteration value.
- TC-8: given `test_vault.py`'s TR-2 adversarial join-resistance sweep (seals a shard, calls every
  registered GET route), when the suite runs, then it still passes with the new `final_summary`/
  source-detail fields present on `/research/desk/micro/foundry`.
- TC-9: given `test_copy_discipline.py`'s whole-frontend-source-literal lint, when the suite runs after
  `apps/frontend/app/desk/page.tsx` gains the new Final Summary JSX, then the lint reports zero
  banned-phrase matches.
- TC-10: given `test_run_hypothesis_foundry_real_exhaust.py`'s sealed-CLI/canonical-helper equivalence
  test, when its docstring/inline comment is read after this iteration, then it states that the
  freeze-set hash pinning — not the equivalence assertion — prevents the two formulas from silently
  diverging; the assertion logic and the sealed CLI file are byte-unchanged.
- TC-11: given the full backend test suite and `tsc` compile, when both run after this iteration's
  changes, then the backend suite passes with zero new failures and the TypeScript compile reports
  zero errors.
- TC-12: given journeys J-01 through J-07 (all currently passing), when the deterministic replay lane
  (with LLM fallback for any journey lacking a stored golden) re-runs them against this iteration's
  build, then all seven still pass with zero regressions.

## NOTES

- The two open HUMAN-owned blocking anti-goal entries (iter-5's "No second real generation epoch";
  iter-6's "Persistence stays scoped" lock-file write) remain unresolved after this iteration and may
  still block `GOAL_ACHIEVED` at the evaluator's discretion — that call belongs to the evaluator/owner,
  not to this spec.
- If the fresh-context reviewer/auditor finds the `final_summary` projection helper has drifted into
  independently recomputing any value (rather than reading an already-owned one), that is a coherence
  violation and must be fixed by pointing the field back at its single existing owner, never by adding
  a third computation site.
- Escalation flag carried from iter-4/iter-7: every iteration in this session has exceeded the 3600s
  wall-clock budget; a `CONTINUE` verdict this iteration would be mechanically demoted to lean by the
  engine's deterministic depth arbiter. This spec's `Depth: full` is justified independently by the
  prior `ESCALATE` verdict (trigger 3), so no operator action is required for depth — flagged only for
  visibility given this is the era's closing iteration.
