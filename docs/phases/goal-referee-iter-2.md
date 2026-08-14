# Goal Iteration 2 — J-02: the evidence contract (two families, one typed observation)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** referee
- **Iteration:** 2
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes (no frontend code changes this iteration — J-02 is backend-only per
  goal.md's `(Keyless; automated.)` marker; browser-qa still runs the J-10 regression sentinel:
  cockpit `/`, `/structure`'s AAPL Load, and every shipped `/desk` section, per the "rides every
  iteration" binding note in `iteration-state.md`)
- **Target journeys:** J-02
- **Required-still-passing journeys:** J-01, J-10
- **Anti-goal reminders:** (verbatim from `docs/goal.md`; the subset this iteration's build
  surface actually touches — see full list under § Anti-goals for the rest)
  - 3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
    them, never a mutation of them. *(critical)*
  - 5. **No lookahead** — every value computed as-of T uses only events/bars fully completed at
    T. *(critical)*
  - 6. **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - 9. **Immutable data** — registered datasets and bar series are append-only, checksummed,
    never re-tagged, never deleted, never content-perturbed. Splits are frozen at
    registration. *(critical)*
  - **No threshold or definition tuning, anywhere, ever.** Detector constants, band-context
    constants (`70 bps`, `(1R, 2R)` edges), and cohort vocabulary are frozen; `room_r`,
    backing, headroom never become detector gates; no code path iterates any threshold against
    outcomes (source-scan guard-tested). A genuine bug fix is a named revision that re-keys,
    never an edit of recorded meaning.
  - **No fingerprint epoch movement.** Zero new Config fields expected; Path A if one is
    unavoidable; the pin `08e471b10130e1e2` does not move.
  - **The Referee never feeds back.** No referee output gates, filters, ranks, or tunes any
    detector, context, screen, or strategy computation (import-ban + source-scan
    guard-tested); the frozen research vocabulary stays frozen. *(critical)*

## GOAL

Backend-only: every recorded Playbook occurrence and every recorded strategy trade becomes
available as one typed observation record — `{evidence_family, observation_id, symbol,
session_date, anchor_ts, side, measure_key, value, cluster_key, provenance{...}}` — through two
per-family adapters plus a small rebuildable cache in `referee_evidence.py`, so J-04 (nulls),
J-05 (registry), and J-06 (adjudication) have exactly one shared, non-reimplementable layer to
build on.

## BACKGROUND

Iteration 1's evaluator recorded J-01 passing and explicitly recommended building **J-02 alone,
at lean depth, next** — the next step in goal.md's own dependency order
(J-01 → J-02 → … → J-09), and the one every remaining Referee journey imports rather than
re-derives. Iteration 1's `coherence.md` was `COHERENCE-PASS` (not FAIL), so rubric rule 2
(consolidation before features) does not apply and no violations need fixing first. No journey
regressed (rule 1 n/a). J-02 is the smallest available unblocker (rule 3): J-04, J-05, and J-06
each name "consuming the contract (J-02)" as a direct dependency in goal.md's own Key
Capabilities text, and nothing else in the backlog is smaller or more blocking (rule 4). One
journey only, so rule 5 (never bundle two risky journeys) does not arise. It is not
human-blocked — the iteration-state's "Active blockers" is explicitly "none" and calls J-02
"buildable today: keyless, backend-only, no new dependency" (rule 6 n/a). Real code lands this
iteration, so rule 7 (no evidence-only iterations) does not apply.

Depth is **lean**, matching the evaluator's binding recommendation; none of the four full
triggers hold: this is a single self-contained extension of one already-owned module
(`referee_evidence.py`) plus one new derived cache, under the Referee's own read-side/import-ban
law — not a refactor of shared architecture and not ≥3 interacting modules (trigger 1); it is
purely ADDITIVE (a new observation contract and a new cache table for a never-before-served
shape) and changes neither the computing module nor the serving endpoint of any
ALREADY-REGISTERED Data-Contract value — J-01's own `GET /research/desk/referee/evidence` body
stays byte-identical (trigger 2 does not apply); the prior verdict was `CONTINUE`, not `ESCALATE`
(trigger 3 n/a); consecutive lean iterations sits at 1 of the 6-iteration hardening cadence
(trigger 4 not due); and it carries zero frontend work and zero new Data-Contract row of its own
(the blueprint's IA table already lists J-02 as "library modules, no page of their own" —
`n/a — consumed by J-04–J-09`), so it is not a brand-new full-stack journey either.

Per the binding "Do not redo" list, this iteration extends `referee_evidence.py` — it never
rebuilds it, never re-verifies J-01's already-proven counts fold, and never re-drafts
`blueprint.md` (the correct row is already there). It also carries the one open rider from
iteration 1's eval and coherence advisory: fold the two already-served `integrity_errors` fields
into this endpoint's documented response shape, and reuse `REFEREE_FORMING_BAR_BASIS_CAVEAT`
verbatim rather than minting a second caveat string. Per `lessons.md`'s iter-1 entry, J-02 is a
backend-only journey and no golden replay script can exist for it (`demo_runner.py` is
single-base-url); expect it to land in `state/golden-gaps` — that is by design, not a defect, and
its primary verification lane is the hermetic pytest fixture suite, not a browser walk.

## IN SCOPE

### Backend
- [ ] Extend `app/research/referee_evidence.py` (never rebuild — binding "Do not redo") with the
      typed observation contract per `docs/referee-statistical-spec.md` §2 and goal.md Key
      Capability 1 / J-02's steps verbatim: `evidence_family`, `observation_id` (a pure function
      of `source_record_id` + signal/trade index), `symbol`, `session_date`, `anchor_ts`
      (ISO-8601 UTC), `side`, `measure_key`, `value`, `cluster_key`, and
      `provenance{detector_basis, config_fingerprint, context_algorithm_version, source_record_id,
      basis_caveats}` — units (% side-signed returns) and the side→MDD binding
      (`long → mdd_long_*`) stated once, here.
- [ ] Playbook adapter: **reuse, never reimplement**, J-01's own
      `current_playbook_detector_basis()` and `_newest_per_session_date()` for the
      `(detector_basis, config_fingerprint)` pooling/dedup identity; walk each newest-per-date
      record's signals into observations; carry the completeness predicate (finest-series reach
      of the RTH close window, `docs/referee-statistical-spec.md` §2's completed-session rule);
      count a truncated/unmeasurable leaf as an exclusion, never a value; carry per-date coverage
      counts; disclose when a newest record covers fewer symbols than the superseded record it
      replaces.
- [ ] Strategy adapter: join each recorded backtest report's trades to
      `{dataset(id, checksum, split, symbol, epoch_anchor, data_feed), strategy_id, profile,
      config_fingerprint}` (`store.py`/`datasets.py`, `backtests.py` result block); `cluster_key
      = dataset id`; real UTC `anchor_ts` from `epoch_anchor + logical_ts`; adapt the recorded
      `random_null` trades (`backtests.py::_null_trades` :1010) as the family's paired null
      observation set, kept separate and labeled — never merged indistinguishably into the
      primary trades; `provenance.basis_caveats` reuses the existing
      `REFEREE_FORMING_BAR_BASIS_CAVEAT` constant verbatim (the iter-1 rider — no second string).
- [ ] A derived observation cache (new module, or an extension inside `referee_evidence.py` —
      developer's choice of file organization) following the established derived/rebuildable
      cache contract (`desk_meta_cache.py` / `bar_index.py` / `dataset_index.py` precedent):
      stat-keyed sqlite at `TAPEOLOGY_REFEREE_OBS_CACHE_DB`, owns nothing, deleting it changes
      latency only, never the served content.
- [ ] Documentation rider (iter-1 eval + coherence advisory): fold the two already-served
      `integrity_errors` fields (`playbook_occurrence.integrity_errors`,
      `strategy_trade.integrity_errors`) into this endpoint's pinned response-shape
      documentation (module docstring / test comment) — behavior is unchanged; this closes the
      documentation gap only.
- [ ] Extend `tests/test_referee_evidence.py` with hermetic fixture golden tests: hand-computed
      observation sets for both families; cold/warm/deleted-cache parity; the
      two-signatures-same-parameters pooling fixture; the monkeypatched-constant-splits-the-pool
      fixture; the same-date dedup/newest-selection fixture with a coverage-shrink disclosure;
      a truncated/unmeasurable exclusion fixture; the `random_null`-adapted-null fixture.
- [ ] Extend `tests/test_referee_guards.py`'s import-ban check to be bidirectional over this
      iteration's new code paths: no `referee_*.py` module imports `desk_playbook_detect` or
      `desk_playbook_context`, and neither of those modules imports any `referee_*` module.
- [ ] Zero new `Config` fields; zero diff to `desk_playbook*.py`, `desk_forward.py`, `levels.py`,
      `tradability.py`, `setups.py`, `pnl_scan.py`.

### Frontend
- (none — J-02 is backend-only; goal.md marks it `(Keyless; automated.)`)

### New user-facing capability
None directly user-facing yet — this is a backend-only library layer. It becomes
operator-visible only later, when J-04/J-05/J-06 consume it and J-07/J-09 render results on
`/desk`.

### New information displayed
None (no UI change this iteration).

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None visible in the UI. `referee_evidence.py` gains a typed, per-observation contract and a
small rebuildable cache — internal plumbing every later Referee journey imports, not a new
served surface of its own.

### Blueprint conformance
Already covered by the existing blueprint IA row: "J-02 evidence contract, J-03 stats core
(library modules, no page of their own) | n/a — consumed by J-04–J-09 | —". No edit needed —
this iteration builds into that row exactly as drafted.

### Data-contract additions
None. The typed observation contract is an internal library shape consumed by later journeys'
own endpoints (nulls, registry, evaluations, adjudications — each already has its own Data
Contract row in `blueprint.md`), not a new displayed value or a new serving endpoint of its own
this iteration. J-01's existing Data-Contract row (`GET /research/desk/referee/evidence` →
`referee_evidence.py`) is unchanged: same owner, same endpoint, same served body.

## OUT OF SCOPE

- J-03's statistics core, oracle suite, seeded draws, CIs, p-values, and attestation — no
  randomization or bootstrap work this iteration.
- J-04's matched nulls, null store, or compute manager.
- J-05's registry.
- J-06's estimand engines and adjudication.
- J-07's and J-09's `/desk` UI surfacing and the two new MCP tools — zero frontend, zero MCP
  changes this iteration.
- J-08's promotion interlock / `authorize_promotion` — untouched; `pnl_scan.py` stays
  byte-identical.
- Any new REST route — J-02's own acceptance is entirely fixture-only/keyless; no endpoint
  serves individual observations this iteration.
- Any change to J-01's already-served response shape or behavior — the aggregate readiness
  counts stay byte-identical; only this endpoint's documentation gains the two already-served
  `integrity_errors` rider fields.
- Any real registration/evaluation/null-build operator act — none of that machinery exists yet.
- Re-verifying or re-scoring J-01 or J-10 as target journeys — both ride along only as
  Required-still-passing.

## DEFINITION OF DONE

- [ ] Target journey J-02 passes: the hermetic pytest fixture-golden suite reproduces
      hand-computed observation sets byte-identically for both families, including the
      cold/warm/deleted-cache parity, pooling/split, dedup, exclusion, and paired-null fixtures
      — the primary evidence lane per goal.md's own `(Keyless; automated.)` tag; browser-qa-agent
      confirms no live-endpoint regression (J-02 adds no new route to smoke).
- [ ] Required-still-passing journey J-01 remains green: `GET /research/desk/referee/evidence`
      serves the SAME byte-identical response shape as iteration 1 (`tests/test_referee_evidence.py`
      + `tests/test_referee_guards.py` re-run — pytest re-run, not golden replay, per the
      `lessons.md` iter-1 entry: no replay script can exist for this backend-only route).
- [ ] Required-still-passing journey J-10 remains green (deterministic replay of the stored
      9-step golden `runs/goal-session-referee/journey-scripts/J-10.json` where it applies, else
      the LLM browser-qa fallback — cockpit, `/structure` AAPL Load, every shipped `/desk`
      section).
- [ ] No anti-goal violation introduced: zero diff to `desk_playbook*.py`, `desk_forward.py`,
      `levels.py`, `tradability.py`, `setups.py`, `pnl_scan.py`; zero new `Config` fields;
      `Config().config_fingerprint()` still `08e471b10130e1e2`; bidirectional import-ban guard
      green; zero writes to any pre-existing store file (SHA-256 listing unchanged).
- [ ] Unit tests pass; full backend suite ≥ 2,433 pass / 8 skip (iteration 1's recorded floor);
      no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-referee-iter-2-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-10 only (regression sentinel — cockpit `/`, `/structure` AAPL Load, every shipped
  `/desk` section). J-02 itself needs no browser check — goal.md marks it
  `(Keyless; automated.)` and its acceptance runs entirely against committed pytest fixtures.
- Unit/integration: extended `tests/test_referee_evidence.py` (golden observation fixtures for
  both families, cache cold/warm/deleted parity, pooling/dedup/exclusion/paired-null fixtures)
  and extended `tests/test_referee_guards.py` (bidirectional import-ban) must exist and pass;
  the full existing suite must stay green at ≥ 2,433 pass / 8 skip.
- Error cases: a corrupted/unparseable Playbook or dataset record must propagate as a served
  `integrity_errors` entry (existing behavior, now documented), never crash the adapter or be
  silently dropped; a fully truncated/unmeasurable leaf, or an occurrence with zero measurable
  data, must be counted as an exclusion — never a fabricated or fallback `value`.

Test-first contract:

- TC-1: given a committed hermetic fixture Playbook corpus (multiple `session_date` values,
  multiple `(setup, side)` cells, at least one truncated/unmeasurable leaf), when the playbook
  adapter builds observations with the cache cold, then the returned list matches a
  hand-computed golden fixture byte-for-byte on every field (`evidence_family`,
  `observation_id`, `symbol`, `session_date`, `anchor_ts`, `side`, `measure_key`, `value`,
  `cluster_key`, and every `provenance` key).
- TC-2: given the identical fixture corpus, when the same adapter call runs a second time with
  the cache now warm, and a third time immediately after the cache DB file is deleted, then all
  three runs return byte-identical observation lists.
- TC-3: given two recorded Playbook records with different `playbook_input_signature` values but
  byte-identical `parameters`, when observations are built, then every observation from both
  records carries the same `provenance.detector_basis` string.
- TC-4: given the same two-record fixture, when a `PLAYBOOK_*` detector constant is monkeypatched
  before the second record's `parameters` are captured, then the two records' observations carry
  two different `provenance.detector_basis` values.
- TC-5: given two recorded Playbook records for the same `session_date` and the same
  `detector_basis` (a same-day re-recording), when observations are built, then only the newest
  record's (by `(recorded_at, id)`) signals appear as that date's observations, and when the
  newest record's symbol coverage is smaller than the superseded record's, a served disclosure
  names the difference.
- TC-6: given a Playbook signal whose forward measurement is truncated/unmeasurable (`reason`
  non-null) at the primary horizon, when observations are built, then no observation is emitted
  for that leaf and it is counted in a served exclusion field instead.
- TC-7: given a committed hermetic fixture backtest report with recorded `trades` (including at
  least one `random_null`-labeled trade) for a known `(dataset_id, checksum, split)`, when the
  strategy adapter builds observations, then each non-null trade yields one observation with
  `cluster_key` equal to the dataset id, `measure_key == "net_r"`, `value` equal to that trade's
  own recorded `net_r`, and `provenance.basis_caveats == [REFEREE_FORMING_BAR_BASIS_CAVEAT]`
  (the exact existing constant, verified by identity/equality — not a re-typed string).
- TC-8: given the same fixture report, when the strategy adapter processes the recorded
  `random_null` trades, then they are returned as a separately labeled paired-null observation
  set, never merged indistinguishably into the primary trade observations.
- TC-9: given the full fixture corpus for both families, when a SHA-256 listing of every
  pre-existing store file (playbook, dataset, journal) is taken before and after the adapter
  calls, then the two listings are byte-identical.
- TC-10: given this iteration's change, when `tests/test_referee_guards.py`'s import-ban check
  runs, then it finds zero imports of `desk_playbook_detect` or `desk_playbook_context` inside
  any `referee_*.py` module, and zero imports of any `referee_*` module inside
  `desk_playbook_detect.py` or `desk_playbook_context.py`.
- TC-11: given `GET /research/desk/referee/evidence` unchanged by this iteration, when
  `tests/test_referee_evidence.py`'s existing J-01 fixture assertions are re-run, then the
  response body is byte-identical to iteration 1's recorded shape, and the module's own
  documentation now explicitly lists `playbook_occurrence.integrity_errors` and
  `strategy_trade.integrity_errors` as part of the pinned response shape.
- TC-12: given the full backend suite, when `pytest` completes, then it reports pass and skip
  counts each ≥ 2,433 pass / 8 skip with zero errors, and `Config().config_fingerprint()` still
  prints `08e471b10130e1e2`.

## NOTES

- **Two riders folded into this same file, per iteration 1's eval + coherence advisory:** (1)
  document the two already-served `integrity_errors` fields as part of the pinned response
  shape; (2) the strategy adapter's `basis_caveats` must reuse
  `REFEREE_FORMING_BAR_BASIS_CAVEAT` verbatim — it is now the single source of truth J-06 and
  J-08 must also read back rather than re-wording (TC-7 pins this).
- Per `lessons.md`'s iter-1 entry, expect J-02 to land in `state/golden-gaps` — no golden replay
  script can exist for a backend-only route (`demo_runner.py` resolves every step against the
  single frontend origin). This is by design, not a defect; do not chase it.
- `runs/goal-session-referee/state/blueprint.md` is unchanged this iteration: the IA row this
  journey fulfills ("library modules, no page of their own") was already drafted correctly at
  baseline. No nav change, so no `blueprint.reapproval-requested` file either.
- No entry added to `runs/goal-session-referee/state/assumptions.md` this iteration. The one
  open implementation choice — whether the playbook adapter fans a signal out to one observation
  per applicable `measure_key` up front, or builds observations lazily per requested
  `measure_key` — is a normal, reversible engineering decision inside the pinned per-observation
  SHAPE (`docs/referee-statistical-spec.md` §2 fixes the record's fields, not the adapter's
  call signature); it is not a goal ambiguity requiring an owner ruling.
- Traps most relevant this iteration (`docs/goal.md` § Build anchors & weak-model traps): **T-1**
  (the spec is law — implement §2's contract verbatim; a developer who finds a clause
  unimplementable drops it and surfaces it rather than improvising) and **T-6** (the corpus moves
  daily — pool on `detector_basis` + newest-complete-record-per-date; a newest record covering
  fewer symbols than a superseded one is a served disclosure, never a silent shrink; TC-5 pins
  this).
- Anchors to re-locate by symbol name (grep), never by line arithmetic: `playbook_parameters()`
  :246, `compute_playbook_input_signature` :345, `PlaybookStore.newest_for_date` :956 in
  `desk_playbook.py`; `DESK_FORWARD_MEASURE_KEYS` :146, `_measure_from` :451 in
  `desk_forward.py`; `_close_trade` :1137, `_null_trades` :1010, result block :608–634 in
  `backtests.py`; `current_playbook_detector_basis`, `_newest_per_session_date`,
  `REFEREE_FORMING_BAR_BASIS_CAVEAT` in `apps/backend/app/research/referee_evidence.py` (this
  iteration's own extension target — reuse these, do not reimplement).
