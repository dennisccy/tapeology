# Goal Iteration 16 — Leakage traps TR-3 / TR-22 / TR-26 plus three carried passengers

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 16
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict (iteration 15) was ESCALATE, the mandatory, no-exceptions
  grant of full depth this era's own precedent requires (iterations 8 and 12 both lost the
  independent auditor when full depth was requested only in evaluator prose, not the verdict
  line).
- Frontend Present: yes
- **Target journeys:** J-10
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-07, J-08 (full regression
  of every currently-passing journey — widened per this agent's own "after an ESCALATE, widen to
  a full regression" guidance, and independently required by J-10's own step-3 acceptance text,
  the kept-product sentinel, which this round must run anyway; J-06 stays excluded — no file
  under its module changes, matching iterations 14/15's own precedent for the identical reason)
- **Anti-goal reminders:**
  - "**No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
    *(critical)*"
  - "**The accessor is the only data door.** No module but `micro_accessor.py` opens snapshot or
    vault event data; origin fences fail closed; import-ban and source-scan guards enforce it.
    *(critical)*"
  - "**No value is served before it exists.** Every feature carries
    `anchor_at`/`observed_through`/`available_at`; a deferred construct is `unavailable` until
    its observations exist; no outcome for a conditioned anchor begins before the conditioning
    set's maximum `available_at` (TR-17). *(critical)*"
  - "**No exploratory read of a sealed shard.** Event data and outcome aggregates of a `sealed`
    shard are refused everywhere (routes, MCP, accessor, readiness) until its recorded exposure;
    the refusal is typed, tested, and fail-closed. *(critical)*"
  - "**A recorded tranche is one opaque research pool until its shards are exposed.** No served
    surface — readiness, recorder progress, datasets, backtests, PnL ledger, Scout, walk-forward,
    graduation, MCP, UI — may present a complete identity-labelled partition of "exploratory"
    versus "sealed", nor a complete per-shard list of EITHER side while any pool member is
    unexposed; the registered universe is public by construction, so a complete list of one side
    identifies the other by subtraction. Unexposed pool members stay mutually indistinguishable;
    identity becomes public only at real exposure or assignment. The governing test is the TR-2
    inference trap: given the registered universe plus every public artifact, no still-unexposed
    vault-eligible shard is identifiable with certainty. *(critical — spec r5)*"
  - "**Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*"
  - "**Deterministic and seeded** — every random draw uses a recorded named seed via per-row
    streams; identical requests reproduce byte-identical results; no wall-clock, no unseeded
    randomness in any research artifact. *(critical)*"
  - "**Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
    surface's behaviour stay byte-identical. New work is additive and versioned beside them,
    never a mutation of them. *(critical)*"

## GOAL

Land three of the five remaining leakage traps — TR-3 (accessor origin-fence + exact
corpus-aggregate boundary + import-ban), TR-22 (exposure-registry auto-classification + r2
initialization), and TR-26 (the `quote_depletion` revealing-quote availability fix, closing the
r6 timing item open since round 2) — each as an explicitly-labeled, non-vacuity-proven trap-suite
entry, plus three small carried passengers, moving J-10's trap count from 24/29 to 27/29.

## BACKGROUND

Iteration 15's verdict is ESCALATE, so full depth (with the independent auditor lane) is
mandatory this round regardless of any prose request (lessons iter-8, iter-12's process note;
Full trigger 3). The evaluator's own next-step recommendation names this exact split: round 16 =
TR-3 + TR-22 + TR-26; round 17 = TR-23 + TR-24, which "belong together" as graduation-adjacent
traps. TR-26 also closes the `quote_depletion` availability item open since round 2 (r6 §3 — the
"one quote early" bug); TR-22 is a named prerequisite for J-09 (the pilot studies stay explicitly
out of scope this round and the next, per every evaluator round since 13).

Direct code inspection (not assumed) shows the underlying MECHANISMS for TR-3 and TR-22 already
exist and are heavily unit-tested from the iterations that built them: `micro_accessor.py`'s
origin fence + `ExposureRegistry`, and `walkforward.py`'s `classify_evidence_class`. What J-10 is
missing is an explicitly-labeled, adversarially-framed TR-N trap-suite entry per §9's exact
acceptance bullet — matching this codebase's own established `test_vault.py`
`test_tr2_*`/`test_tr29_*` convention — so the "27 of 29" count stays auditable by name rather
than inferred from unlabeled TC-suite tests. TR-26 is a genuine, precisely-located bug, not a
gap: `tests/test_micro_observer.py::test_tc10_quote_depletion_resolves_at_a_price_change_
attached_to_the_next_trade_row` currently ASSERTS the pre-r6 (wrong) timestamp
(`observed_through == 2.0`, the last same-price quote) where the r6 owner ruling
(`docs/rapid-validation-spec.md` revision header, 2026-08-18) requires the REVEALING
price-changing quote (`3.0`) instead; the fix and its test correction are the same change, and
the bound-termination path is already correct (confirmed by direct trace of
`_advance_depletion_run`/`_resolve_depletion`) but has no dedicated test proving it today.

Iteration 15's own live demonstration — its own new TR-2 MCP sweep sealed a shard under an
UNREGISTERED universe, so the leak-detecting branch never executed, and it was caught only by
mutation-proof — is this round's binding design constraint (lesson iter-15): every trap test
below carries an explicit non-vacuity requirement, proven by deliberately reintroducing the exact
defect the trap guards against and showing the test fails, then restoring it. The iter-11 lesson
(widening one side of a paired mechanism re-opens the leak through the untouched twin) governs
TR-3/TR-22 specifically — both directions of each mechanism (refusal AND the boundary case one
step inside it; exposed-after AND exposed-before) get an explicit assertion, not just the one
path the existing TC-suite already covers. The iter-13 lesson (attack the crash/edge state, never
trust an in-code comment's "benign" claim) is why TR-26 is treated as a real diagnosed defect
rather than accepting the existing test's current assertion at face value.

Per the evaluator's own "carry three small passengers, never a round of their own" instruction,
and the standing budget-trimmer risk (iterations 8 and 12 lost the auditor to over-large rounds),
scope stays to exactly these three traps plus three named passengers. J-10 itself is EXPECTED to
remain `partial` at the end of this round (27/29, not 29/29) — that is the planned, correct
outcome (TR-23/TR-24 are round 17's), not a shortfall.

## IN SCOPE

### Backend

- [ ] `TR-3` (accessor fence): land an explicitly-labeled trap-suite entry (new or renamed test(s)
  in `apps/backend/tests/test_micro_accessor.py`, extended into `tests/test_walkforward.py` where
  the aggregate boundary is proven) covering all three §9 clauses — (a) the single-read origin
  fence (folding in / referencing the existing non-vacuous `test_tc1_*` coverage, not
  reimplementing it), (b) a NEW assertion that a multi-session AGGREGATE view built through the
  accessor at `origin=T` (the walk-forward origin-window/session-enumeration path, its one
  existing `origin=` consumer) contains EXACTLY the sessions with date `<= T`, boundary-exact at
  T and T+1, and (c) the import-ban (folding in / referencing the existing non-vacuous
  `test_tc3_*` coverage). Add the explicit non-vacuity mutation-proof for the origin-fence
  assertion specifically (the import-ban half already has one:
  `test_tc3_import_ban_guard_can_fail_on_a_seeded_violation`).
- [ ] `TR-22` (exposure registry): land an explicitly-labeled trap-suite entry
  (`apps/backend/tests/test_micro_accessor.py` and/or `tests/test_walkforward.py`, folding in /
  referencing the existing non-vacuous `test_tc13_*` pair which already proves both directions)
  covering all three §9 clauses — registered-after-exposure auto-classes
  `historical_exposed_diagnostic`, registered-before-any-exposure classes `historical_oos`, and
  the r2 initialization pre-marks every playbook-corpus and legacy-tick window exposed. Add the
  explicit non-vacuity mutation-proof on the `is_exposed_before`/`classify_evidence_class`
  comparison.
- [ ] `TR-26` (depletion revealing quote): fix the price-change-termination branch of
  `apps/backend/app/research/micro_observer.py`'s `_advance_depletion_run`/`_resolve_depletion` so
  a resolved run's `observed_through`/`available_at` stamp at the REVEALING (price-CHANGING)
  quote's own instant, never the prior same-price quote's — the depletion MAGNITUDE stays computed
  from the pre-change run data, unaffected (measurement end ≠ knowledge time, spec §3). The
  bound-termination branch (window closes by hitting `DEPLETION_WINDOW_QUOTES`) is already correct
  and stays unchanged. Correct the now-provably-wrong assertion in
  `tests/test_micro_observer.py::test_tc10_quote_depletion_resolves_at_a_price_change_attached_to_
  the_next_trade_row`; add a new bound-terminated fixture test; add a truncation-boundary test
  (truncate strictly before the revealing quote ⇒ the run stays unresolved/absent, never guessed;
  include it ⇒ deterministic resolution). Land the explicitly-labeled TR-26 trap-suite entry with
  its non-vacuity mutation-proof (revert the fix, show the corrected test fails).
- [ ] `apps/backend/tests/test_desk_ui_guards.py`: add the missing seeded-violation counter-test
  for the two iter-15-added `_PRICE_ARITHMETIC_FIELDS` clauses (`readiness.sealed_tranche.*`,
  `universeCounts.*`, `readiness.joinable_corpus.withheld_excluded`), mirroring the existing
  `test_desk_page_price_arithmetic_guard_catches_micro_readiness_field_arithmetic` shape exactly
  (closes iteration 15's open MINOR anti-goal item).
- [ ] No change to `vault.py`, `tick_recorder.py`, `micro_readiness.py`'s served computation,
  `scout.py`, `scout_ledger.py`, `walkforward_ledger.py`, `micro_routes.py`'s route shape, or
  `micro_chain_ledger.py` — this round's backend work is confined to `micro_accessor.py`'s and
  `walkforward.py`'s own test coverage (TR-3, TR-22) and `micro_observer.py`'s depletion-timing
  fix (TR-26).

### Frontend

- [ ] `apps/frontend/app/desk/page.tsx` `MicroReadinessSection` (~line 5886): wrap the loading and
  unavailable early returns in `data-testid="micro-readiness-section"`, mirroring
  `ValidationVaultSection`'s already-fixed pattern (page.tsx:6682-6699) exactly — closes
  iteration 15's COHERENCE-WARN.
- [ ] `apps/frontend/app/desk/page.tsx` Scout Ledger table (~lines 6315/6317): defend the two
  undefended reads (`trial.feature.name`/`.transform`, `trial.outcome.horizon_key`) with a safe
  fallback (e.g. optional chaining plus a placeholder glyph) so a malformed/tampered trial row
  degrades only that row's cell, never blanks the whole `/desk` page. Row-level defensive
  rendering only — NOT a page-wide React `ErrorBoundary` (see OUT OF SCOPE).

### New user-facing capability

None — this round hardens the leakage-trap suite and fixes an internal availability-timing bug;
no new feature.

### New information displayed

None new. The testid fix is a DOM/test-tooling attribute, not a displayed value; nothing served
changes shape.

### New user actions

None.

### UI surface changes

None structurally. The Scout table's malformed-row cells degrade gracefully instead of throwing
(a resilience change, not a new surface); `MicroReadinessSection`'s DOM wrapper gains the same
`data-testid` its three sibling sections already always carry.

### Product surface delta

No visible change to a healthy page. A previously-blank-page failure mode (one malformed Scout
row throwing during render) now degrades to a single bad cell instead.

### Blueprint conformance

No new surfaces. All three traps are backend-only test/correctness work with no UI home of their
own (J-10's kept-product-sentinel acceptance, not a nav entry). The two frontend passengers stay
inside the already-registered Microscope Readiness (J-01) and Scout Ledger (J-04) homes in
`blueprint.md`'s Information Architecture table — no nav-skeleton change, no reapproval file.

### Data-contract additions

None. TR-3/TR-22/TR-26 add no new served value: the accessor origin-fence and exposure registry
are backend-internal mechanisms never served through any endpoint or MCP tool, and the
`quote_depletion` timing correction fixes an existing, already-typed, never-served feature value's
TIMESTAMP — not its shape, owner, or endpoint (it is read only by `scout.py`/`walkforward.py`/
`micro_join.py` during compute, matching the already-registered "keyless/automated" J-02 IA row).
The three passengers touch DOM structure and test coverage only. `blueprint.md` gets a
documentation-only iter-16 note recording this (no table edit — nothing new to register).

## OUT OF SCOPE

- TR-23 (sealed-verdict ownership) and TR-24 (lineage boundary) — explicitly deferred to round 17
  per the evaluator's own two-way split ("belong together" as graduation-adjacent traps).
- J-09 "The pilot studies" — stays blocked; TR-22 landing this round is a named prerequisite, but
  starting J-09 itself was explicitly ruled out by every evaluator round since 13 and is not
  reopened here.
- J-06 real-tape recording and any operator-attended recorder/vault act — human-blocked,
  explicitly "do not record real tape this round" (carried instruction).
- Any change to `vault.py` itself, or intercepting `DatasetStore` to change vault/Referee
  behaviour indirectly — both explicitly rejected by the owner.
- Any change to `referee_*.py`, `micro_chain_ledger.py`, or any Playbook detector — frozen rails.
- J-10 step 2, the deterministic-rerun check (byte-identical snapshot/screen/fold outputs on a
  re-run over unchanged stores) — a real, named J-10 requirement, but not named for round 16 by
  the evaluator; deferred rather than silently folded in.
- Deepening J-02–J-05's byte-identical, single-step golden replay scripts — a real
  evaluator-recorded weakness ("worth strengthening if it fits without bloating the round"), but
  not a named round-16 requirement; deferred explicitly to avoid growing a round that must stay
  small enough to keep the independent auditor lane.
- A page-wide React `ErrorBoundary` component on `/desk` — the fix stays the narrow, row-level
  defensive read the evaluator specifically named ("make the Scout table survive a damaged row");
  a page-wide boundary is a larger structural change nobody asked for this round.
- Any new `Config` field, any fingerprint-affecting change, any new runtime dependency.

## DEFINITION OF DONE

- [ ] TR-3 lands as an explicitly-labeled, non-vacuity-proven trap-suite entry (TC-1..TC-4)
- [ ] TR-22 lands as an explicitly-labeled, non-vacuity-proven trap-suite entry (TC-5..TC-8)
- [ ] TR-26 lands: the price-change-termination availability bug is fixed, its previously-wrong
  test assertion corrected, bound-termination and truncation-boundary coverage added, non-vacuity
  proven (TC-9..TC-12)
- [ ] J-10's trap count is 27/29 (TR-3, TR-22, TR-26 newly present alongside the 24 already
  landed); TR-23/TR-24 explicitly remain open for round 17; J-10 itself stays `partial` — this is
  the planned outcome, not a shortfall
- [ ] `MicroReadinessSection` carries `data-testid="micro-readiness-section"` in all three render
  states, closing iteration 15's COHERENCE-WARN (TC-13)
- [ ] The Scout table survives a malformed/tampered trial row without blanking `/desk` (TC-14)
- [ ] The two iter-15 `_PRICE_ARITHMETIC_FIELDS` clauses have their seeded-violation counter-test
  (TC-15)
- [ ] Full backend suite green, 0 failures, passed count ≥ 3229 (iteration-15 baseline), frozen
  rails re-verified: fingerprint `08e471b10130e1e2`, six `referee_*.py` + `micro_chain_ledger.py`
  SHA-256 match iteration-0, zero new `Config` fields, `tsc --noEmit` clean (TC-16, TC-17)
- [ ] Target journey J-10 verified via the independent auditor + browser-qa-agent (traps green,
  kept-product sentinel screenshots on record per J-10's own acceptance text)
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-05, J-07, J-08 remain green with
  zero regressions (deterministic replay + LLM fallback for J-07 — mechanically verified) (TC-18)
- [ ] No anti-goal violation introduced — in particular no NEW lookahead (TR-26's fix must not
  stamp `available_at` EARLIER than the revealing quote either, only correct the "one quote
  early" direction) and the opaque-research-pool / sealed-shard rails stay intact at the
  fixture-proof level (production still has zero sealed shards)
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-16-dev.md`

## TESTING REQUIREMENTS

- Browser: J-10 (kept-product sentinel — cockpit `/` live tape + chart, `/structure` load +
  Tradable Map, every shipped `/desk` section including the three Referee sections and all four
  Rapid-Microscope sections, browser-verified via the store-scoped rig; J-10's own acceptance
  text names this explicitly); J-01, J-02, J-03, J-04, J-05, J-08 (deterministic replay); J-07
  (LLM fallback, direct-endpoint navigation to `GET /research/desk/micro/graduation` — no golden
  script exists for it by design, carried from iteration 15)
- Unit/integration: TC-1 through TC-15 below, each new trap assertion paired with its own
  non-vacuity mutation-proof (mirroring `tests/test_mcp_server.py`'s TR-2 non-vacuity fix,
  lines ~1292-1299 — copy the pattern, do not re-derive it)
- Error cases: TR-3's typed `MicroAccessorOriginFenceError` on a strictly-after-origin read
  (never an empty or truncated result); TR-26's `unavailable` (counted, never guessed) for a
  depletion run the session cuts short before either termination path fires; TR-22's diagnostic
  auto-classification is never silently promoted to `historical_oos`

Test-first contract:

- TC-1: given a `MicroAccessor` constructed with `origin=T` over a fixture with sessions
  S1 < T = S2 < S3, when `read_snapshot_rows` is called for S1's, S2's, and S3's datasets in
  turn, then S1 and S2 succeed and S3 raises `MicroAccessorOriginFenceError` (typed, never an
  empty list) — folding in the existing `test_tc1_*` coverage under the new TR-3 label.
- TC-2: given the same fixture, when an origin-fenced AGGREGATE view (the walk-forward
  origin-window/session-enumeration path) is built at `origin=S2`, then the returned session set
  is exactly `{S1, S2}`; rebuilt at `origin=S3`, the set is exactly `{S1, S2, S3}` — boundary-exact
  at T and T+1, neither off by one.
- TC-3: given the existing, already non-vacuous import-ban tests
  (`test_tc3_no_module_other_than_micro_accessor_imports_read_snapshot_rows`,
  `test_tc3_import_ban_guard_can_fail_on_a_seeded_violation`), when they are referenced/wired into
  the new explicitly-labeled TR-3 trap-suite entry, then the formal TR-3 entry is complete and
  auditable by name without re-implementing working coverage.
- TC-4: given the origin-fence comparison in `MicroAccessor.read_snapshot_rows` is temporarily
  weakened so it never refuses, when the new TR-3-labeled test suite runs against that weakened
  code, then it fails at the fence assertion; restoring the comparison makes it pass again.
- TC-5: given a freshly initialized `ExposureRegistry` with a logged exposure entry for session
  window W at instant `t0`, when a Mode-B spec is registered with `registered_at > t0` covering
  W, then `classify_evidence_class` returns `historical_exposed_diagnostic`.
- TC-6: given a freshly initialized `ExposureRegistry` for a NEW corpus_id with zero exposure
  entries, when a Mode-B spec is registered with `registered_at` before any exposure of its
  validation window, then `classify_evidence_class` returns `historical_oos`.
- TC-7: given `initialize_r2_exposure_registry` runs once for the playbook-corpus and legacy-tick
  corpus ids, when every one of their session-date windows is queried via `is_exposed_before` at
  any instant after `R2_REVISION_INSTANT`, then every query returns `True`.
- TC-8: given `is_exposed_before`'s strict `<` comparison is temporarily mutated to always return
  `False`, when the new TR-22-labeled test suite runs, then it fails at the auto-classification
  assertion; restoring the comparison makes it pass again.
- TC-9: given the existing `_depletion_events()` fixture (ask-side run at price 100.10 with
  updates at t=0/1/2, price change to 100.20 at t=3), when the observer resolves the run, then
  `observed_through` and `available_at` both equal `3.0` (the price-CHANGING/revealing quote's
  own instant — corrected from the current wrong `2.0`), while `value` stays `200.0`
  (500 − 300, unaffected by the timestamp fix).
- TC-10: given a NEW fixture reaching `DEPLETION_WINDOW_QUOTES` (20) same-price same-side quote
  updates with no price change, when the run resolves by hitting the update bound, then
  `observed_through` and `available_at` both equal the 20th (bound-hitting) quote's own instant.
- TC-11: given the corrected price-change-terminated run, when the dataset is truncated (TR-1
  prefix-style) strictly BEFORE the revealing quote's instant, then the depletion construct for
  that run does not appear as a resolved value (absent or `unavailable`, never guessed); when
  truncated at or after the revealing quote's instant, the same run resolves with its
  deterministic value and timestamp.
- TC-12: given the corrected `test_tc10_quote_depletion_resolves_at_a_price_change_...` assertion
  (`observed_through == 3.0`), when the price-change branch is reverted to stamp the pre-change
  run's own `observed_through` (the pre-fix behaviour), then this test fails — proving it is not
  vacuous with respect to the exact bug fixed.
- TC-13: given `/desk` with the readiness endpoint returning `ok: false`, still loading, and
  loaded, when `MicroReadinessSection` renders in each state, then
  `data-testid="micro-readiness-section"` is present in the DOM in all three.
- TC-14: given a Scout family whose `trials` array contains one row with a missing/malformed
  `feature.name` or `outcome.horizon_key`, when the Scout Ledger table renders, then the
  malformed row renders a defined fallback in that cell instead of throwing, and every other
  section of `/desk` continues to render normally.
- TC-15: given the two iter-15-added `_PRICE_ARITHMETIC_FIELDS` clauses, when a seeded
  client-side arithmetic snippet on each binding (e.g.
  `readiness.sealed_tranche.shard_count / readiness.sealed_tranche.symbol_days`,
  `universeCounts.shard_count + universeCounts.symbol_days`,
  `1 - readiness.joinable_corpus.withheld_excluded`) is checked against
  `_PRICE_ARITHMETIC_PATTERN`, then the pattern matches every seeded violation.
- TC-16: given the full backend test suite, when it is run after this iteration's changes, then
  it reports 0 failures with a passed count ≥ 3229 (the iteration-15 baseline), including all new
  TR-3/TR-22/TR-26/testid/defensive-read/guard tests.
- TC-17: given the kept-product sentinel (cockpit `/`, `/structure`, every shipped `/desk`
  section including the three Referee sections), when browser-verified via the store-scoped rig,
  then every section renders as shipped, `Config().config_fingerprint()` prints
  `08e471b10130e1e2`, and the six `referee_*.py` files + `micro_chain_ledger.py` SHA-256 match the
  iteration-0 baseline listing.
- TC-18: given J-01, J-02, J-03, J-04, J-05, J-08's stored golden replay scripts (and J-07's
  direct-endpoint LLM navigation), when the required-still-passing regression sweep runs, then
  all seven verify against the current build with zero regressions recorded.

## NOTES

- Build anchors (re-locate by symbol name, never line arithmetic — authored against `main` at
  iteration 15's own commit): `micro_accessor.py` — origin fence + sealed-shard check inside
  `MicroAccessor.read_snapshot_rows`, `ExposureRegistry.is_exposed_before`/`log_exposure`,
  `initialize_r2_exposure_registry`, `R2_REVISION_INSTANT`; `walkforward.py` —
  `classify_evidence_class`; `micro_observer.py` — `_advance_depletion_run` (the price-change
  branch that calls `self._resolve_depletion(side, run)` using the OLD run's own
  `observed_through` is the exact bug site — it needs the NEW quote's own `ts` instead),
  `_resolve_depletion`; `page.tsx` — `MicroReadinessSection`, `ValidationVaultSection`'s
  already-fixed wrapper pattern, the two undefended Scout-table reads; `test_desk_ui_guards.py`
  — `_PRICE_ARITHMETIC_FIELDS`, the existing counter-test pattern to mirror
  (`test_desk_page_price_arithmetic_guard_catches_micro_readiness_field_arithmetic`).
- Lessons applied (full text pre-trimmed in the dispatch prompt): iter-15 (every new trap needs a
  non-vacuity mutation-proof — this spec's TC-4/TC-8/TC-12 are exactly that, one per trap); iter-11
  (widening one side of a paired mechanism re-opens the leak through the untouched twin — TC-2's
  aggregate-boundary assertion and TC-6's before-registration direction exist specifically so
  neither TR-3 nor TR-22 ships with only one direction proven); iter-13 (attack the crash/edge
  state, never trust an in-code comment's "benign" claim — the reason TR-26 is treated as a
  diagnosed bug against the spec, not accepted as the existing test currently asserts it).
- Zero assumption-ledger entries this iteration. The scoping calls made (which module hosts the
  TR-3 aggregate-boundary proof; keeping the Scout-table fix row-level rather than a page-wide
  `ErrorBoundary`; deferring golden-script deepening and the deterministic-rerun check) are
  routine implementation/scope choices already directed by the evaluator's own specific language,
  not ambiguous goal-interpretation calls requiring an owner ruling.
- r6/r8 owner-ruling context for TR-26 and the halt-only vault recovery it sits beside:
  `docs/rapid-validation-spec.md`'s r6 (2026-08-18) and r8 (2026-08-19) revision-header notes, and
  `runs/goal-session-rapid-microscope/state/assumptions.md`'s 2026-08-18/2026-08-19 entries — read
  verbatim if the depletion fix's scope is unclear; it is explicitly ruled to be "an
  implementation bug against r2's existing availability law, not a methodology change."
