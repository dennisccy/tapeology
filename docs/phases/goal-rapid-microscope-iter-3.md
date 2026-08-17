# Goal Iteration 3 — The structure × flow join, and an honest sentinel

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 3
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — `micro_join.py`'s correctness depends on cross-module interactions (a new
  snapshot-row reader, the unmodified `desk_playbook.py` signal timestamps, the unmodified
  `BandMapResolver` band basis, a new outcome/cost-proxy computation, and an additive
  readiness-endpoint field) around the CRITICAL no-lookahead rail — per-module unit tests do not
  cover that interaction, exactly the failure class iter-2's audit caught that review and QA both
  missed.
- **Frontend Present:** no
- **Target journeys:** J-03, J-10
- **Required-still-passing journeys:** J-01, J-02
- **Anti-goal reminders:**
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
    them, never a mutation of them. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
    *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a recorded named seed via per-row
    streams; identical requests reproduce byte-identical results; no wall-clock, no unseeded
    randomness in any research artifact. *(critical)*
  - **Immutable data** — registered datasets and bar series are append-only, checksummed,
    never re-tagged, never deleted, never content-perturbed. Splits are frozen at
    registration. *(critical)*
  - **No value is served before it exists.** Every feature carries
    `anchor_at`/`observed_through`/`available_at`; a deferred construct is `unavailable` until
    its observations exist; no outcome for a conditioned anchor begins before the conditioning
    set's maximum `available_at` (TR-17). *(critical)*
  - **No microstructure claim beyond what L1 supports.** `refill_consistent` is the strongest
    liquidity label; "iceberg", institutional-intent, and manipulation language are
    banned; every aggressor-derived quantity is served beside its `fallback_frac` and
    `unknown_frac`. *(critical)*
  - **No cross-unit liquidity arithmetic.** No feature, screen, or study relates trade shares to
    displayed quote sizes unless the dataset's `quote_size_unit` is verified (spec §2.6);
    unverified or mixed units are a typed refusal; unit normalization exists only as a recorded
    verification act, never silent arithmetic. *(critical)*
  - **Referee modules are byte-untouched this era** — `referee_handoff_ready` never implies
    current-Referee registrability of a flow predicate; that awaits a future named revision of
    the referee spec. *(critical)*
  - **Era-B/B2 anti-goals that remain binding:** membership is never a signal; snapshots and
    playbook records are append-only and pinned; every run is an explicit operator act; the
    briefing and the playbook describe, never advise; the demolition stays demolished; the
    ledger never holds orders; the suite stays keyless and hermetic; the fingerprint pin does
    not move; no threshold exists outside its spec and no code path sweeps one; the evidence
    pools one signature; no recorded playbook file is ever rewritten; no second implementation
    of the measurement rail. *(all critical)*

## GOAL

Make the corpus's structural signals and band-map wall touches joinable, for the first time, to
real lookahead-clean order-flow feature and outcome measurements already sitting in the snapshot
store (still invisible in the UI, staged for J-08), and repoint the kept-product sentinel's test
data so its Structure and Playbook Signals checks stop failing for reasons that have nothing to do
with the product.

## BACKGROUND

Iteration 2 shipped the micro observer and closed J-01's missing photograph. The evaluator's
next-step recommendation is binding this iteration: build J-03 next under the full pipeline,
specifically because iteration 2's own audit step caught two honesty defects (an ungated
share-denominated liquidity value, and a session-truncated stream persisted as if complete) that
review and QA both missed — and J-03 is the first place a genuine look-into-the-future bug would
actually bite (the critical no-lookahead rail). J-03 touches at least four modules whose
interactions matter — a new snapshot-row reader, the unmodified `desk_playbook.py`/
`BandMapResolver` readers, a new outcome/cost-proxy computation, and an additive readiness field —
without any single module's own test suite covering that interaction, which is Full trigger 1
(structural/cross-cutting). Two lessons apply directly: iter-2's "a snapshot's identity proves it
was produced by this code, not that it is complete" lesson names J-03's join explicitly as an area
that needs its own fail-closed completeness channel; and iter-2's "the J-10 sentinel keeps FAILING
for test-rig reasons" lesson is flagged "applies to every future iteration" until fixed, so this
iteration finally repoints it. J-10's trap-suite sub-criterion (TR-1…TR-22) cannot reach
"complete" until J-04 through J-07 land their own remaining traps (goal.md's own J-10 step 1 says
so explicitly, and frames J-10 as "guarding continuously," not a single-shot gate) — this iteration
only closes the rig-data-caused browser gap in J-10, not the whole journey.

## IN SCOPE

### Backend — J-03 (structure × flow join)

- [ ] New `app/research/micro_join.py`: for a playbook signal `(symbol, trigger_ts)` (read-only
  from `desk_playbook.py`'s recorded records) or a band-map wall touch (via
  `desk_playbook_context.BandMapResolver.resolve(symbol, as_of_epoch)`, `compute=False`), locate
  the covering snapshot and return the feature row(s) at-or-before the trigger plus the outcome
  row(s) after it.
- [ ] A plain snapshot-row reader added to `micro_snapshots.py` (co-located with the writer — see
  NOTES on the accessor boundary); `micro_join.py` calls this, never opens the JSONL files itself.
- [ ] Implement spec §4's closed outcome set for the outcome-after-trigger rows: mid-price move at
  the horizon(s) from spec §1; session-truncated with the truncation flagged and excluded from
  averages; a row lacking a quote mid at either end served as `unmeasured` (never measured off the
  last trade); the quoted spread at the outcome start (bps) served beside every outcome as its own
  cost-proxy column, never netted in silently.
- [ ] Outcome start = `anchor_at` (the trigger's own timestamp) for this journey's generic join
  (assumption-ledger entry — no per-candidate conditioning feature set exists before J-04); every
  feature family at the trigger row keeps its own `available_at`/`unavailable` flag undisturbed.
- [ ] Enumerate the joinable corpus (signals/touches falling inside recorded tick windows) and add
  a `joinable_corpus` field to `micro_readiness.py`'s served response (same endpoint) with `total`,
  `playbook_signal_count`, `band_touch_count`, and a `by_setup_id` breakdown, computed honestly
  from the real store.
- [ ] Lookahead-assertion test: a join at trigger T reads zero snapshot rows with event epoch > T.
- [ ] Detector/context byte-freeze guard test: `desk_playbook.py` and `desk_playbook_context.py`
  are byte-unchanged by this iteration's diff.
- [ ] Fixture-join test against the already-committed `apps/backend/tests/fixtures/datasets_j03/`
  PG SIP dataset (2026-06-09 17:02–17:03Z): build its snapshot via the existing J-02 pipeline, pair
  it with a fixture playbook-signal record and/or a fixture band-map cache entry at a known
  trigger, and assert the join's feature-at-trigger and outcome-after-trigger rows match
  hand-computed values.
- [ ] The joinable-corpus enumeration and the fixture-join build fail closed (refuse, never
  silently under-count or under-build) if any signal/touch lookup raises mid-loop — applying
  iter-2's streamed-artifact completeness lesson (audit B1/B2) to this journey's own loop.
- [ ] Record the already-flagged §3 window-mean `quote_imbalance`/`microprice` gap (iter-2 audit
  DISCLOSURE item) in this iteration's dev handoff Known Issues section — documentation only, not
  a new feature.

### Backend — J-10 (sentinel test-plan repointing; no product code change)

- [ ] Repair `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` step 9: replace the
  volatile per-instance signature-hash assertion (`b06e0bc289c54d77`, regenerated every restart)
  with the stable static label text that precedes it in `PlaybookEvidenceSection`
  (`apps/frontend/app/desk/page.tsx:10980`, the "Playbook Evidence" panel's
  `"Built from signature:"` label — not the hash span that follows it).
- [ ] Point this iteration's browser check for the Playbook Signals filter (the prior UT-07
  failure) at a symbol/session with recorded signals — reuse `AAPL` / `2026-06-22`, the same
  combination steps 5–7 of `journey-scripts/J-10.json` already use for Structure, already proven
  to render real content on the store-scoped rig.
- [ ] No change to any frontend source file, `desk_playbook.py`, `desk_playbook_context.py`, or
  the readiness/snapshot backend beyond what the J-03 items above already touch.

### Frontend

None. This iteration ships no new UI. The new `joinable_corpus` readiness field is backend-only
this iteration — the same accepted pattern iter-2's coherence audit approved for J-02's snapshot
endpoints: a value may be served ahead of its UI wiring when the wiring iteration is already named
in the blueprint's Information Architecture (here, J-08).

### New user-facing capability

None directly observable this iteration — J-03 is keyless/automated per goal.md's own framing
("the rest are keyless/automated with browser reveals landing in J-08"). J-10's fix restores
accurate sentinel signal on already-shipped surfaces (Structure/AAPL bands, the Playbook Signals
filter, the Playbook Evidence panel) — a truer report of an existing capability, not a new one.

### New information displayed

None in the UI this iteration. A new `joinable_corpus` object is newly SERVED (not yet rendered)
on `GET /research/desk/micro/readiness`.

### New user actions

None.

### UI surface changes

None. The Desk page's Microscope Readiness panel continues to render exactly as shipped (J-01
Do-Not-Redo item).

### Product surface delta

No visible product surface change this iteration.

### Blueprint conformance

J-03's home is already registered in `blueprint.md`'s Information Architecture table
("Structure × flow join (J-03) | keyless/automated; joinable-corpus count surfaces via Microscope
Readiness | Desk") — no IA edit needed. J-10's fix touches only a QA journey script, not a product
surface. No nav-skeleton change; no `blueprint.reapproval-requested` file written.

### Data-contract additions

`joinable_corpus` object added to the EXISTING "Corpus readiness truth" Data Contract row (same
owner `micro_readiness.py`, same endpoint `GET /research/desk/micro/readiness` — no new endpoint):
- `joinable_corpus.total: int >= 0`
- `joinable_corpus.playbook_signal_count: int >= 0`
- `joinable_corpus.band_touch_count: int >= 0`
- `joinable_corpus.by_setup_id: dict[str, int]` (keys = playbook `setup_id` values already
  recorded on signals)

Computed by the new `app/research/micro_join.py` (called from `micro_readiness.py`; never a second
computation elsewhere). `blueprint.md` already updated this iteration to register this addition.

## OUT OF SCOPE

- `micro_accessor.py` / `walkforward.py` (J-05) — not built early; J-03 reads snapshots via a
  plain reader, not the accessor (see assumption-ledger entry and NOTES).
- `scout.py` / `scout_ledger.py` (J-04), `tick_recorder.py` / `vault.py` (J-06),
  `micro_graduation.py` (J-07) — untouched.
- Any pilot-study-specific mechanism (range-wall failed aggression, delta divergence, capitulation
  exhaustion) — that is J-09; J-03 only builds the generic join primitive and its honest corpus
  count.
- Any new `/desk` UI section for Scout/Walk-Forward/Vault, or MCP tool additions — J-08.
- Resolving audit B5 (the `quote_depletion` `available_at` timing owner ruling) — still pending,
  still scoped to "before J-05," not this iteration.
- Re-photographing the Microscope Readiness panel with the real 12/18/~3.0 totals — deferred until
  a later iteration seeds the rig with more tick data (the standing J-01 evidence-makeup passenger
  note).
- The §3 window-mean `quote_imbalance`/`microprice` feature gap itself — disclosed in Known Issues
  this iteration, not built.
- Any change to `desk_playbook.py`, `desk_playbook_context.py`, or any playbook/band-context
  threshold constant.
- The advisory (non-blocking) shared-helper refactor between `micro_readiness._quote_rule_decides`
  and `micro_observer._side_source` noted in iter-2's coherence audit — neither function is
  touched by this iteration's work.
- Completing the full TR-1…TR-22 trap suite — structurally spread across J-02…J-07 by goal.md's
  own design; this iteration does not attempt to close that count.

## DEFINITION OF DONE

- [ ] J-03: the committed fixture join (`datasets_j03`) reproduces hand-computed feature-at-trigger
  and outcome-after-trigger values (TC-1, TC-2)
- [ ] J-03: the lookahead assertion and the detector/context byte-freeze guard both pass
  (TC-3, TC-4)
- [ ] J-03: `GET /research/desk/micro/readiness` serves the honest `joinable_corpus` breakdown,
  computed from the real store (TC-5)
- [ ] J-03: deferred-construct `unavailable` flags survive the join unperturbed (TC-6)
- [ ] J-10: `journey-scripts/J-10.json` step 9 passes on a fresh backend restart using the stable
  label assertion (TC-7)
- [ ] J-10: the Playbook Signals filter check passes using AAPL/2026-06-22 instead of the rig's
  empty default session (TC-8)
- [ ] Required-still-passing J-01, J-02 remain green (deterministic replay + LLM fallback)
- [ ] Full backend suite passes at a count ≥ 2,828 pass / 8 skip (iter-2 baseline), fingerprint
  prints `08e471b10130e1e2`, all 6 `referee_*` SHA-256 hashes match the iteration-0 listing (TC-9)
- [ ] No anti-goal violation introduced
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-3-dev.md`, including the §3
  window-mean gap disclosure in its Known Issues section

Note: this iteration does NOT claim "J-10 passes" wholesale — J-10's trap-suite sub-criterion
cannot close until later journeys land their remaining traps (see BACKGROUND and NOTES); its
overall verdict is the evaluator's call.

## TESTING REQUIREMENTS

- Browser: J-10's full journey script (`journey-scripts/J-10.json`, all steps including the
  repaired step 9); the Playbook Signals filter check via AAPL/2026-06-22 (the prior UT-07
  failure). J-03 has no dedicated browser check — it is keyless/automated per goal.md; its reveal
  lands in J-08.
- Unit/integration: `micro_join.py`'s fixture-join test; the lookahead-assertion test; the
  detector/context byte-freeze guard; the joinable-corpus readiness-field test; the
  deferred-construct-preservation test; the existing `test_micro_snapshots.py` /
  `test_micro_readiness.py` / `test_micro_observer.py` / `test_observer_equivalence.py` /
  `test_dense_replay_gate.py` suites re-run unmodified.
- Error cases: a trigger with no covering snapshot (outside the joinable corpus) is refused/
  excluded, never fabricated; a `BandMapResolver.resolve()` miss (`None`) is served as an honest
  absence, never a synthesized wall; a row lacking a quote mid at either end of the outcome window
  is `unmeasured`, never measured off the last trade.

- TC-1: given the committed PG SIP fixture
  (`apps/backend/tests/fixtures/datasets_j03/5232fa672b7b4077a5117d34b14c807d.json`,
  2026-06-09 17:02–17:03Z) built into a snapshot via the existing J-02 pipeline, and a fixture
  playbook-signal record `(symbol="PG", trigger_ts=<a timestamp inside the window>)`, when
  `micro_join.py`'s join function is called for that signal, then the returned feature-at-trigger
  row's values (cumulative_delta, spread, tape_state) equal the hand-computed values for the
  nearest at-or-before event, within floating-point tolerance.
- TC-2: given the same fixture snapshot and a fixture band-map cache entry for
  `(symbol, as_of_epoch)` resolved via `BandMapResolver.resolve(..., compute=False)`, when the
  join function is called for that touch, then it returns the matching feature/outcome rows when
  a map IS cached, and an honest absence (no fabricated wall) when `resolve()` returns `None`.
- TC-3: given a join call at trigger epoch T over the fixture snapshot, when the
  lookahead-assertion test runs, then every returned feature row's event epoch is <= T, and the
  test fails if any row has `event_epoch > T`.
- TC-4: given `desk_playbook.py` and `desk_playbook_context.py` as they exist before this
  iteration's diff, when the byte-freeze guard test runs after the diff, then both files hash
  identically to their pre-iteration SHA-256.
- TC-5: given the real `.data/datasets` store's 12 legacy symbol-day corpus and the real playbook
  store, when `GET /research/desk/micro/readiness` is called twice in a row, then both responses
  include an identical `joinable_corpus` object with `total`, `playbook_signal_count`,
  `band_touch_count` as non-negative integers and `by_setup_id` as a non-negative-integer-valued
  dict, computed from the real overlap, never hardcoded.
- TC-6: given a snapshot row still marked `unavailable` for a deferred construct at the trigger
  instant, when the join serves that feature-at-trigger row, then the `unavailable` flag is
  present verbatim in the response (never dropped or coerced to a number).
- TC-7: given a fresh backend restart (a new per-instance signature hash), when browser-qa-agent
  runs `journey-scripts/J-10.json` step 9 (expand the Playbook Evidence section), then the step's
  assertion matches the stable `"Built from signature:"` label text and passes regardless of the
  hash's current value.
- TC-8: given the store-scoped QA rig (`:8301`/`:3301`) with AAPL bars and recorded playbook
  signals for session `2026-06-22`, when browser-qa-agent exercises the Playbook Signals filter on
  `/desk` using `AAPL`/`2026-06-22` instead of the rig's empty default session, then the filtered
  table renders real signal rows, not an empty/honest-absence state caused by the wrong test
  input.
- TC-9: given the full backend suite after this iteration's changes, when `pytest tests/` runs (no
  extra `-q`, per the iter-0 lesson — `pyproject.toml` already sets `addopts = "-q"`), then the
  reported pass count is >= 2,828 with 0 new failures, `Config().config_fingerprint()` prints
  `08e471b10130e1e2`, and all 6 `referee_*.py` SHA-256 hashes match the iteration-0 listing.

## NOTES

- Evaluator's iter-2 next-step recommendation (binding this iteration): build J-03 next under the
  full pipeline, for the audit step's demonstrated value catching lookahead-honesty defects
  (rail 5 is critical).
- Lesson applied (iter-2, streamed-artifact completeness, audit B1/B2 — "Applies to: ...J-03's
  join"): any batch/loop construction of persisted or served rows needs an explicit fail-closed
  completeness channel beside its identity check, not just an identity/checksum proof. Applied to
  the joinable-corpus enumeration and the fixture-join build (see IN SCOPE).
- Lesson applied (iter-2, J-10 sentinel test-rig — "Applies to: every future iteration"): "pin the
  sentinel steps to data the rig actually holds." Applied by repointing the Playbook Signals
  filter check to AAPL/2026-06-22.
- Accessor boundary (assumption-ledger entry): `micro_accessor.py` and its TR-3 import-ban guard
  are J-05 deliverables; J-03 reads snapshots through a plain reader added to `micro_snapshots.py`
  on the still-fully-exploratory legacy corpus. Expect J-05 to re-point this read through the
  accessor as part of its own scope — do not build the accessor early to preempt this.
  `apps/backend/tests/fixtures/datasets_j03/` is already committed (git-tracked) and appears
  pre-staged for exactly this journey; reuse it rather than recording a new tick fixture.
- J-10's trap-suite sub-criterion (spec TR-1…TR-22) structurally cannot reach "complete" until
  J-04/J-05/J-06/J-07 land their own remaining traps (goal.md's own J-10 step 1: "whichever traps
  did not ship inside J-02…J-07 land here"); goal.md frames J-10 as "guarding continuously," not a
  single-shot gate. This iteration only closes the rig-data-caused browser gap — J-10's overall
  status is left to the evaluator.
- Open human-owned item (unchanged, not this iteration's responsibility): audit B5's
  `quote_depletion` `available_at` timing owner ruling, still scoped to "before J-05."
- Three interpretive calls were logged to the assumption ledger this iteration (the accessor/
  reader boundary before J-05; J-03's outcome-start basis; the joinable-corpus "per-study"
  breakdown granularity) — all flagged reversible.
