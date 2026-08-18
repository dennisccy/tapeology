# Goal Iteration 7 — J-06's preservation prerequisite, the tick-family fold request made reachable, and the kept-product re-proof

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 7
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — Prior verdict was ESCALATE (iteration 6); mandatory full, no exceptions, per agent instructions.
- **Frontend Present:** yes (declared solely to force the browser-qa lane to dispatch the required-still-passing regression set and the J-10 sentinel — see NOTES; this iteration's own diff is backend/CLI-only, zero `.tsx`/`.ts` frontend files touched, no new page, no UI control)
- **Target journeys:** J-06, J-05, J-10
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04
- **Anti-goal reminders:**
  - "Frozen foundations — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them." *(critical)*
  - "Single source of truth — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations." *(critical)*
  - "Immutable data — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration." *(critical)*
  - "Deterministic and seeded — every random draw uses a recorded named seed via per-row streams; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact." *(critical)*
  - "The 12 pre-existing tick symbol-days are permanently exploratory — never sealed, never `historical_oos`, never relabeled." *(critical)*
  - "The denominator never shrinks. Every evaluated variant lands in the hash-chained ledger with a closed-vocabulary decision; kills are never deleted; the union-N across grid versions is served beside every family." *(critical)*
  - "No cross-unit liquidity arithmetic. No feature, screen, or study relates trade shares to displayed quote sizes unless the dataset's `quote_size_unit` is verified (spec §2.6); unverified or mixed units are a typed refusal; unit normalization exists only as a recorded verification act, never silent arithmetic." *(critical)*
  - "No fold geometry change after fold 1 without a recorded voiding event that clears every survivor state of that corpus-era." *(critical)*

## GOAL

Land J-06's first, hardest step — the Card-5.1 optional trade/quote preservation fields (spec
§7.1/§2.6) — with every legacy dataset and fixture proven byte-identical afterward, while making
J-05's still-outstanding "tick-family fold request" acceptance clause reachable through a real
production entry point for the first time.

## BACKGROUND

Iteration 6 (verdict ESCALATE, per the standing depth rule this makes Depth: full mandatory here,
no exceptions) closed two of J-05's three named gaps but left one open, confirmed independently by
the evaluator and re-confirmed by this decomposer against the running code: `app/` has exactly one
`build_folds` call site (`walkforward.py:1149`), always the playbook corpus, and neither of its two
callers (`micro_routes.py:323`, `walkforward.py:1221`) takes a corpus/family parameter — so goal.md
J-05's "the tick-family fold request returns the typed floor-refusal naming `11 < 105`" is satisfied
only by a synthetic-date unit test (`test_walkforward.py::test_tc20...`), never by a genuine caller.
The evaluator's own next-step recommendation was explicit: build J-06's first step "on its own,"
under the full pipeline, because it is "the era's most dangerous change" (every old recording and
fixture must still load byte-identically, and the price engine must still be byte-identical) — and
carry the small, already-understood J-05 gap as a passenger, since "the code that finds the 11 dates
already exists." This iteration does exactly that pairing, plus a J-10 re-proof pass, because the
J-06 change touches the shared event/record pipeline every dataset-reading journey depends on.

**Lessons applied:** (iter-3, second) editing `micro_features.py`/`micro_observer.py` forces a whole-
corpus snapshot rebuild — this iteration touches NEITHER file, by design (see OUT OF SCOPE). (iter-4/
iter-5, first) `Frontend Present: no` silently skips the WHOLE browser lane including the mandated
required-still-passing/sentinel set — this spec declares `Frontend Present: yes` for that reason
alone. (iter-2, second) pin J-10's sentinel steps to data the rig actually holds (AAPL as-of
2026-06-22, the existing 13-step `journey-scripts/J-10.json`) rather than inventing new coverage.
(iter-6, second) a guard wired into ONE production path is not the same claim as "the goal's named
input is reachable" — this iteration closes that exact gap for J-05, on a genuine call path, against
the real corpus, not just a synthetic fixture.

Two interpretation calls this iteration makes are logged in
`runs/goal-session-rapid-microscope/state/assumptions.md` (iter-7, both entries): (1) the §2.6
`schema_basis`/`quote_size_unit` work this iteration ships is storage CAPABILITY only — the dated
vendor RULE constant stays reserved for `tick_recorder.py` per that module's own docstring; (2) the
tick-family fold request is wired through the CLI only this iteration, not the shared
`POST /walkforward/compute` route, since no UI/MCP journey consumes it yet.

## IN SCOPE

### Backend

- [ ] **J-06 step 1 — Card-5.1 preservation prerequisite (spec §7.1 r2), the full pipeline
      end-to-end, all changes strictly additive/optional with an absent-key default:**
  - `app/providers/adapters/base.py` — `RawTrade` gains optional `conditions: list[str] | None`,
    `exchange: str | None`, and the other "immutable vendor identifiers the SDK response carries"
    spec §7.1 names by name (`tape`, `trade id`) as optional fields; `RawQuote` gains the vendor's
    quote-condition and bid/ask-exchange (venue) equivalents, where the Alpaca SDK response
    actually carries them (read the real SDK response shape directly — do not guess field names).
  - `app/providers/base.py` — `TradeEvent`/`QuoteEvent` gain the matching optional fields.
  - `app/providers/historical.py` — both existing `RawTrade`/`RawQuote` → `TradeEvent`/`QuoteEvent`
    construction sites (`HistoricalProvider.stream()` and `ProgressiveHistoricalProvider._emit()`)
    thread the new fields through when present.
  - `app/providers/adapters/alpaca.py` — both existing construction sites
    (`_fetch_one_subwindow`, `_fetch_trades_quotes`) populate the new `RawTrade`/`RawQuote` fields
    from the real Alpaca SDK trade/quote response objects when the SDK provides them.
  - `app/research/datasets.py` — `_event_to_row`/`_row_to_event` carry the new fields into/out of
    the stored JSON row ONLY when present (an event without them serializes to the exact same row
    shape as before this change — the `observer=`-kwarg precedent, never an emitted `null` for a
    key that used to be absent); `DatasetStore.record()`/`record_from_source()` gain optional
    `schema_basis: str | None = None` and `quote_size_unit: str | None = None` keyword parameters,
    stamped into `meta` only when supplied (omitted ⇒ manifest shape byte-unchanged for every
    existing call site). If a `quote_size_unit` value is supplied, validate it against the
    EXISTING `micro_features.QUOTE_SIZE_UNITS` tuple — do not define a second unit-vocabulary
    constant. Do NOT define `ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE` this iteration (assumption ledger
    iter-7, first entry) — that dated-rule constant stays reserved for `tick_recorder.py`.
  - Regression proof (not new test-writing, but must be explicitly re-run and reported): every one
    of the 18 real on-disk tick datasets, every committed fixture under
    `tests/fixtures/datasets/` and `tests/fixtures/alpaca/`, `tests/test_observer_equivalence.py`,
    and `tests/test_dense_replay_gate.py` (the golden trace) — all byte-unmodified, all green.

- [ ] **J-05 — make the tick-family fold request reachable from a genuine production entry point:**
  - `app/research/walkforward.py` — a new function (e.g. `run_tick_family_fold_request` or
    similar) that resolves REAL tick session dates via the EXISTING `_tick_dataset_session_dates`
    helper (no second inventory mechanism) against a `DatasetStore` pointed at
    `config.dataset_dir_resolved()`, then calls the ALREADY-WIRED
    `require_sufficient_sessions_for_folds(dates, DIAGNOSTIC_GEOMETRY)` — today this always raises
    `InsufficientSessionsForFoldsError` (11 real sessions < 105), which is the FEATURE (T-7 "
    Insufficient is an answer"). Consider mirroring the existing playbook path's ordering
    (register the fold spec under the existing `TICK_LEGACY_CORPUS_ID`, then check the floor) for
    ledger consistency with the rest of this module — developer's call, not mandated.
  - The CLI (`python -m app.research.walkforward`) gains a new flag alongside the existing
    `--diagnostic` (e.g. `--family tick_legacy`) that calls this function, printing the refusal
    and exiting non-zero exactly like the existing `InsufficientSessionsForFoldsError` catch block
    (mirror, do not duplicate the print/exit logic).
  - Route-level wiring of `POST /walkforward/compute` is explicitly deferred (OUT OF SCOPE below;
    assumption ledger iter-7, second entry).

### New user-facing capability

None this iteration. J-06 step 1 is a storage-schema change with no consumer yet (readiness's
completeness reporting of these fields is J-06 step 5); J-05's fix adds an operator-facing CLI
flag, not a UI control.

### New information displayed

None.

### New user actions

None (no UI buttons/forms this iteration; the new CLI flag is not a UI action).

### UI surface changes

None — zero `apps/frontend` files touched by this iteration's own diff.

### Product surface delta

None. This iteration is pure backend/CLI plumbing; the `/desk` Validation Vault section and the
Microscope Readiness completeness reporting for these new fields remain future J-06/J-08 work.

### Blueprint conformance

No new surfaces; no blueprint.md edit made this iteration. `datasets.py` remains the blueprint's
registered, unchanged owner of dataset/replay data — this iteration adds optional, unserved
storage capability to it (the same additive-kwarg shape already used for `replay(observer=...)`),
never a second owner or a second endpoint.

### Data-contract additions

None. No new value is served by any endpoint this iteration — `schema_basis`/`quote_size_unit`
are written to the dataset manifest only when a caller supplies them (no caller does yet), and
`micro_snapshots.quote_size_unit_for_dataset()` already defaults an absent key to `"unverified"`
(existing, unchanged code), so the served/consumed contract is untouched.

## OUT OF SCOPE

- J-06 steps 2–5: `tick_recorder.py` itself, `vault.py`, universe registration, the Tier-B
  resolution order, the real Alpaca starter-tranche recording, and readiness's completeness
  reporting of the new fields. This iteration is step 1 only, exactly as the iteration-6
  evaluator's recommendation scoped it.
- The `_tick_dataset_session_dates` corrupt-shard `_errors`-channel drop (`walkforward.py:995`)
  and "register tick days by recorded identity before sealed recordings exist" — both are tagged
  `iteration-state.md: "New minor (J-06 scope)"` against the VAULT/exposure-ledger steps (3–4),
  not step 1; folding them in here would dilute focus on the one genuinely dangerous change this
  run must not be shortened for. Carried forward to the iteration that builds `vault.py`.
- The `POST /walkforward/compute` route's family parameter (assumption ledger iter-7, second
  entry) — deferred until a UI/MCP consumer needs it.
- Any edit to `micro_features.py`, `micro_observer.py`, or `micro_snapshots.py` — all three
  already implement the `quote_size_unit` contract as spec section 2.6 requires (verified this
  iteration: `quote_size_unit_for_dataset()` already defaults absent to `"unverified"`; `QUOTE_SIZE_UNITS`,
  `require_verified_unit`, and the TR-18 cross-basis refusal are already shipped and tested by
  J-02). Touching either of the first two triggers a whole-corpus snapshot rebuild (iter-3 lesson)
  for zero benefit this iteration.
- A live credentialed Alpaca fetch proving real `conditions`/`exchange` values populate from a
  genuine SDK response is a nice-to-have hand-verification if time allows, never gating — the
  hermetic suite (mocked/fixture SDK responses) is what DEFINITION OF DONE requires.
- The framework bug that swallows a markdown `**FAIL**` browser-QA cell as no-verdict
  (`scripts/automation/merge_ui_test_results.py:64`, iter-6 finding) — needs a
  framework-maintenance session outside goal mode; flagged in NOTES for the operator, not fixed
  in this product iteration's diff.
- The two open owner rulings (the one-quote-early `micro_observer.py` depletion timing stamp; the
  real-vs-fixture-corpus J-01 readiness-photograph question) — neither blocks this iteration's
  scope; noted in NOTES, not resolved here (T-1: never invented silently).
- J-07, J-08, J-09 — untouched, still `failing`, no claim made about them.

## DEFINITION OF DONE

- [ ] J-06 step 1 ships and is proven via TC-1, TC-2, TC-3, TC-9 (all green); J-06's OVERALL
      journey status is not claimed complete — steps 2–5 remain outstanding.
- [ ] Engine byte-compat holds: TC-4 and TC-5 green; `Config().config_fingerprint()` still prints
      `08e471b10130e1e2`.
- [ ] J-05's remaining acceptance clause is met via a genuine production entry point: TC-6, TC-7,
      TC-8 all green (the evaluator determines whether this moves J-05 to `passing`).
- [ ] J-10's sentinel and TR-19's schema-provable half are re-proved: TC-10, TC-11 green (the
      evaluator determines J-10's resulting status; TR-2/4/12/20 remain outstanding, owned by
      later J-06 steps).
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04 remain green: TC-12.
- [ ] No anti-goal violation introduced (frozen foundations, immutable data, single source of
      truth, no cross-unit arithmetic, the 12-tick-day-permanently-exploratory rail — see
      Anti-goal reminders above).
- [ ] Full backend suite passes at a count ≥ the iteration-6 baseline, 0 failures, 0 regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-7-dev.md`.

## TESTING REQUIREMENTS

- Browser: the J-10 kept-product sentinel (`journey-scripts/J-10.json`, all 13 steps: cockpit `/`
  live tape + chart, `/structure` load + Tradable Map, every shipped `/desk` section including the
  three Referee sections) plus required-still-passing replay/LLM-fallback for J-01 (Microscope
  Readiness panel) and J-02/J-03/J-04 (deferred-budget carries acceptable only if this iteration's
  diff provably cannot reach their served values — otherwise re-verify live, per the iter-5/iter-6
  durability precedent). All via the store-scoped `:8301`/`:3301` rig; `rm -rf apps/frontend/.next`
  + rebuild first (T-9). Read the LLM lane's own `...-ui-test-results.llm.md` verdict line
  directly — never trust the merged headline alone (iter-6 lesson: a markdown `**FAIL**` cell can
  parse as no-verdict and flip the headline green).
- Unit/integration: dataset/provider round-trip and backward-compatibility tests (extend
  `test_datasets.py`); `test_observer_equivalence.py` and `test_dense_replay_gate.py` unmodified
  and green; `test_real_data_gate.py` (Alpaca confinement) green; the new CLI tick-family path
  covered in `test_walkforward.py` (extending the existing CLI-test block); the existing
  synthetic-date `test_tc20_...` test left unmodified and green.
- Error cases: a corrupt/tampered dataset file still raises `DatasetIntegrityError` exactly as
  before, unaffected by the new optional fields; `record()` called with a `quote_size_unit` value
  outside `micro_features.QUOTE_SIZE_UNITS` is rejected explicitly, never silently accepted; the
  tick-family CLI path against a below-floor directory prints the typed refusal and exits
  non-zero, never an unhandled traceback (mirroring the existing `--diagnostic` empty-store test).

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps
to at least one concrete scenario line below.

- TC-1: given the 18 real on-disk tick datasets and every committed dataset fixture
  (`tests/fixtures/datasets/*.json`, `tests/fixtures/alpaca/*.json`) recorded before this
  iteration, when each is loaded through `DatasetStore.list()`/`load_events()`/`replay()` after
  the schema change, then every file's stored `checksum` still verifies (no
  `DatasetIntegrityError`) and every yielded event/row is byte-identical to its pre-change value
  — no `conditions`/`exchange`/`schema_basis`/`quote_size_unit` key appears on any row or manifest
  that never had one.
- TC-2: given a freshly constructed `TradeEvent`/`QuoteEvent` carrying `conditions=["@","I"]`,
  `exchange="Q"` (trade) and the vendor quote-condition/venue equivalents (quote), when it is
  written through `DatasetStore.record()` and then reloaded via `load_events()`, then the
  reloaded event's `conditions`/`exchange` fields equal the original values exactly.
- TC-3: given `DatasetStore.record(..., schema_basis="v2_preservation", quote_size_unit="shares")`,
  when the dataset is reloaded via `list()`, then its manifest carries `schema_basis:
  "v2_preservation"` and `quote_size_unit: "shares"` verbatim; given `record()` is called WITHOUT
  those kwargs (every pre-existing call site), then the manifest carries neither key, matching the
  pre-change manifest shape exactly.
- TC-4: given `tests/test_observer_equivalence.py` and `tests/test_dense_replay_gate.py`
  unmodified by this iteration's diff, when the full suite runs after the schema change, then both
  pass byte-unchanged and `Config().config_fingerprint()` prints `08e471b10130e1e2`.
- TC-5: given the two Alpaca adapter construction sites now populate `conditions`/`exchange` (and
  quote equivalents) from the SDK response when present, when `test_real_data_gate.py`'s
  Alpaca-confinement guard runs, then it still passes and no test in the hermetic suite fetches
  the network.
- TC-6: given `python -m app.research.walkforward`'s new tick-family flag resolves session dates
  via `_tick_dataset_session_dates` against a hermetic `tmp_path` dataset directory (via the
  existing `TAPEOLOGY_DATASET_DIR` override) seeded with N < 105 tick-fixture files, when the flag
  is invoked, then the process prints a refusal containing the exact substrings "`{N} < 105`" and
  "TR-15", exits non-zero, and the ledger shows zero `ROW_KIND_FOLD_RESULT` rows.
- TC-7: given the SAME tick-family CLI path pointed at the operator's real `.data/datasets`
  directory (11 real distinct tick session dates), when the developer runs it by hand and pastes
  the output into the dev handoff, then the refusal names exactly "11 < 105" — the literal string
  goal.md J-05's acceptance requires — produced by a genuine production entry point, not a
  synthetic-date fixture alone; the evaluator independently re-runs this same command against the
  real store before crediting it.
- TC-8: given `test_walkforward.py::test_tc20_the_11_session_tick_corpus_returns_the_typed_floor_refusal_naming_11_lt_105`
  (the existing pure synthetic-date unit test) is left unmodified, when the full suite runs, then
  it still passes unchanged — the new production entry point is additive, never a replacement.
- TC-9: given `micro_features.QUOTE_SIZE_UNITS` is the sole unit-vocabulary tuple in the repo and
  `ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE` is undefined anywhere before this iteration, when this
  iteration's diff is grepped for a new `ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE` definition or a second
  `QUOTE_SIZE_UNITS`-shaped tuple, then none is found.
- TC-10: given the full backend suite after this iteration's diff, when it is run, then it passes
  at a count ≥ the iteration-6 baseline with 0 failures, the six `referee_*.py` module SHA-256
  hashes match the iteration-0 listing exactly, and two consecutive `DatasetStore.replay()` calls
  over one unchanged legacy dataset yield byte-identical snapshot sequences.
- TC-11: given a clean `apps/frontend/.next` rebuild and the store-scoped rig, when the J-10
  sentinel walkthrough runs (cockpit `/`, `/structure`, every shipped `/desk` section including
  the three Referee sections), then every step produces a screenshot (element capture for
  below-the-fold sections) and the LLM lane's own verdict file reads PASS for each step.
- TC-12: given the Microscope Readiness panel (J-01) and the Scout Ledger section (J-04) on
  `/desk`, when the required-still-passing check runs for J-01/J-02/J-03/J-04, then each renders
  its previously-recorded served values, OR — if this iteration's diff changed a shared producer —
  the newly re-derived value proven live against the real store, with a screenshot on record.

## NOTES

- **PUMP NOTE (standing, from the operator):** never use pattern-based process kills (`pkill -f` /
  `killall`) for uvicorn, next, node, chrome, or python — other projects share this host; kill
  only exact PIDs you started and recorded.
- **Iteration hygiene (goal.md Constraints, "the era-6 retro"):** keep browser acceptance narrow
  and default to the fixture-scoped backend for QA — this iteration already carries real risk in
  its backend diff; do not let QA scope creep add to the timeout risk that tripped 13 of 15 prior
  referee iterations.
- **Framework escalation (not this iteration's diff):** `scripts/automation/merge_ui_test_results.py:64`
  accepts only a bare `PASS`/`FAIL` token, so a markdown-emphasised `**FAIL**` browser-QA cell
  parses as no-verdict and a green headline can reach `status.json`/closure undetected (iter-6
  finding, caught only by the independent auditor). This needs a framework-maintenance session
  outside goal mode — the operator should action it separately; the standing mitigation inside
  this loop is reading the LLM lane's own verdict file directly (TC-11 above), not the merged
  headline.
- **Two open owner rulings, still non-blocking to this iteration's scope:** (1) the one-quote-early
  `micro_observer.py` depletion `available_at` timing stamp (`:636`/`:657`); (2) whether J-01's
  readiness photograph must show the real 12-symbol-day corpus when the store-scoped browser rig
  can only ever seed 2 PG fixtures (the rig's launcher structurally forbids pointing at the real
  `.data/datasets` store). Neither is touched by this iteration's scope.
- **Escalation flag:** this continues a multi-iteration ESCALATE chain — iterations 4, 5, and 6
  were each dispatched full following a prior ESCALATE, and each returned ESCALATE again — now on
  a change explicitly named by the evaluator as the era's most dangerous so far. Do not let the
  independent auditor step get budget-demoted (iteration-6's own note: "the auditor must not be
  budget-demoted next run") — if a time crunch forces a choice, cut J-10's sentinel
  re-verification depth before cutting the auditor's review of the byte-compat proof.
