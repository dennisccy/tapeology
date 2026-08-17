# Goal Iteration 2 — The micro observer streams prefix-honest snapshots; the QA rig finally shows real tick data

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 2
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict was `ESCALATE` (`runs/goal-session-rapid-microscope/iter-1/eval.md`), which the agent instructions make mandatory and exception-free for this iteration's depth; independently reinforced by trigger 1 (this iteration edits the two files the era promises to keep byte-identical — the tape engine's observer hook and `DatasetStore.replay`).
- **Frontend Present:** yes (browser-qa verifies J-01's panel and the full J-10 sentinel this iteration; no `.tsx` source is edited)
- **Target journeys:** J-01, J-02
- **Required-still-passing journeys:** J-10 — widened to the FULL kept-product sentinel this
  iteration (cockpit `/`, `/structure` load + Tradable Map, every shipped `/desk` section incl.
  all three Referee sections, full backend suite, fingerprint check, referee SHA-256 listing),
  per the rule that a prior `ESCALATE` verdict widens the regression set; J-10's own canonical
  home already covers exactly this scope, so no other journey needs separate listing.
- **Anti-goal reminders (selected; full text governs — see `docs/goal.md` §Anti-goals):**
  - *Immutable rail 3 — Frozen foundations:* "the `v1` strategy, the `default` profile, the tape
    engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`,
    and every KEPT surface's behaviour stay byte-identical. New work is additive and versioned
    beside them, never a mutation of them. *(critical)*"
  - *Immutable rail 5 — No lookahead:* "every value computed as-of T uses only events/bars fully
    completed at T. *(critical)*"
  - *Immutable rail 7 — Deterministic and seeded:* "every random draw uses a recorded named seed
    via per-row streams; identical requests reproduce byte-identical results; no wall-clock, no
    unseeded randomness in any research artifact. *(critical)*"
  - *Immutable rail 9 — Immutable data:* "registered datasets and bar series are append-only,
    checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at
    registration. *(critical)*"
  - *Rapid-Microscope anti-goal:* "No value is served before it exists. Every feature carries
    `anchor_at`/`observed_through`/`available_at`; a deferred construct is `unavailable` until
    its observations exist; no outcome for a conditioned anchor begins before the conditioning
    set's maximum `available_at` (TR-17). *(critical)*"
  - *Rapid-Microscope anti-goal:* "No cross-unit liquidity arithmetic. No feature, screen, or
    study relates trade shares to displayed quote sizes unless the dataset's `quote_size_unit` is
    verified (spec §2.6); unverified or mixed units are a typed refusal; unit normalization
    exists only as a recorded verification act, never silent arithmetic. *(critical)*"
  - *Rapid-Microscope anti-goal:* "No microstructure claim beyond what L1 supports.
    `refill_consistent` is the strongest liquidity label; 'iceberg', institutional-intent, and
    manipulation language are banned; every aggressor-derived quantity is served beside its
    `fallback_frac` and `unknown_frac`. *(critical)*"

## GOAL

Wire the additive observer seam onto dataset replay and ship `micro_observer.py` /
`micro_snapshots.py` / `micro_features.py` so every one of the 18 legacy tick datasets gets a
prefix-honest, benchmarked, identity-verified flow/response/liquidity feature snapshot — and
close out J-01's last open half by giving the mandated store-scoped QA rig a real, non-empty
tick corpus to photograph.

## BACKGROUND

Iteration 1 shipped J-01's readiness endpoint and `/desk` panel; the evaluator (iter-1/eval.md)
verified the backend half directly against the real 18-dataset corpus (12 symbol-days, 18
shards, 3.0089 session-equivalents, all three floors `floor_unmet`) — that work is Do Not Redo.
That same evaluator returned `ESCALATE` and recommended building J-02 next "under the full
pipeline... because it also touches the two files this era promises to keep byte-for-byte
identical" (`DatasetStore.replay` and the tape engine's observer hook). Per the agent
instructions a prior `ESCALATE` makes full depth mandatory regardless (Full trigger 3); the
evaluator's own restated depth recommendation for this iteration agrees. `coherence.md` (iter-1)
returned `COHERENCE-PASS`, so rule 2's consolidation trigger does not fire — this iteration
proceeds straight to new scope. Per the priority rubric, J-02 is simultaneously the natural
dependency-order successor (J-01 → J-02 → J-03 → ...) and the unblocker every remaining journey
(J-03 through J-09) needs (rule 3); nothing regressed (rule 1 moot).

Alongside J-02, this iteration carries the evaluator's two named clean-up items — NOT as a
second risky journey (rule 5), but as low-risk test-infrastructure work that stays entirely
outside frozen product code: (1) seed the store-scoped QA rig with real, already-committed tick
fixtures so J-01's browser half can finally be photographed non-empty, directly closing the gap
`lessons.md` iter-1 flagged ("any acceptance naming real-corpus values is structurally
unprovable through the browser lane... Applies to: any iteration whose browser acceptance reads
the tick corpus — J-06's vault states, J-08's four `/desk` micro sections, and J-09's study
results all hit this same wall"); (2) move 5 misplaced counter-test assertions in
`test_desk_ui_guards.py` back to their own function (the MINOR item in iteration-state's active
blockers). Literally reproducing J-01's exact real-corpus totals (12 symbol-days / 18 shards /
~3.0 session-equivalents) through the mandated rig would require either fabricating data or
pointing the rig's `TAPEOLOGY_DATASET_DIR` at the real `.data/datasets` store — the latter is
riskier than it looks this iteration specifically, because J-02 also adds the FIRST write-capable
route under that same directory family (the snapshot-compute manager), whose derived-cache
storage dir defaults to a sibling of wherever `TAPEOLOGY_DATASET_DIR` points; pointing that at the
real store could let a stray compute leave derived files beside the operator's real tree instead
of inside the throwaway scoped root. So this iteration seeds only the two already-committed PG
fixture datasets into the rig's own throwaway root instead — real, non-fabricated, but small.
This interpretation call is logged to `runs/goal-session-rapid-microscope/state/assumptions.md`
(iter-2 — goal-decomposer).

## IN SCOPE

### Backend

- [ ] `apps/backend/app/research/datasets.py`: additive `observer: object | None = None` kwarg on
      `DatasetStore.replay` (spec §2.1), calling `engine.add_observer(observer)` once, before the
      event loop starts, only when not `None`. `add_observer`/`_notify_event` already exist
      unmodified on `TapeEngine` (`app/engine/tape_engine.py:123`/`:144`) — this iteration is
      purely the wiring at the ONE replay entry point (`datasets.py:376`); no second replay
      implementation. Counter-tested: every existing call site (no `observer` argument) stays
      byte-identical.
- [ ] New `apps/backend/app/research/micro_observer.py`: the streaming `on_event(event, snapshot)`
      observer implementing the prefix law (spec §2.2) — row *i* is a pure function of events
      `1..i` plus the engine snapshot after event *i*; flush before consuming event *i+1*; no
      whole-dataset normalizer, baseline, calibration, or end-of-session statistic anywhere.
      Deferred constructs (§0 availability law) are written at their `observed_through` row,
      referencing their `anchor_at`, never attached retroactively.
- [ ] New `apps/backend/app/research/micro_snapshots.py`: snapshot identity + load-time
      verification (spec §2.3 — key = `(dataset_id, dataset_checksum, MICRO_ALGO_VERSION,
      SNAPSHOT_FORMAT_VERSION, feature_source_hash, config_fingerprint, params_hash)`; the loader
      re-verifies all three checksums/hashes on every read and refuses on mismatch, the
      `DatasetIntegrityError` discipline reused, not reinvented). Persistence + build orchestration
      follow the shipped desk compute-manager pattern (single-flight, snapshot-pollable progress,
      cancel, CLI-runnable, one shared writer, terminal-state-only ledger writes — the precedent
      already used by `desk_forward_compute.py`/`desk_playbook_compute.py`/`edge_report_compute.py`;
      no new pattern invented). Adds the three pre-registered routes (blueprint.md's
      `micro_snapshots.py` Data Contract row): `GET /research/desk/micro/snapshots`,
      `POST/GET/POST-cancel /research/desk/micro/snapshots/compute`,
      `GET /research/desk/micro/snapshots/runs`.
- [ ] New `apps/backend/app/research/micro_features.py`: F-FLOW / F-RESPONSE / F-LIQUIDITY per
      spec §3 (cumulative delta, rolling imbalance, same-side run length, volume burst,
      divergence-at-level; impact efficiency + trend, `failed_aggression_score`, response
      asymmetry; spread change, quote imbalance, microprice, quote depletion,
      `refill_consistent`), each carrying the `anchor_at`/`observed_through`/`available_at`
      triple, per-row `side_source`, per-window `fallback_frac`/`unknown_frac`, and the §2.6
      size-unit gating on cross-basis liquidity features (execution-vs-replenishment ratio, any
      share-denominated depletion/replenishment magnitude). The spec §4 mid-only primary outcome
      set (last-trade basis as a separately named sensitivity column) lands here too, with
      outcome start = the conditioning feature set's max `available_at`. Reuses engine-snapshot
      values verbatim per §2.5 (aggressor side + `side_source`, the five-window features, tape
      state, bid/ask/spread/last) — never recomputes them. Constants (`MICRO_SEED`,
      `MICRO_ALGO_VERSION`, `REFILL_M_QUOTES`, `RESPONSE_K_TRADES`,
      `BURST_BASELINE_TRAILING_WINDOWS`, `DEPLETION_WINDOW_QUOTES`, `IMPACT_FLATNESS_SCALE_BPS`,
      `DIVERGENCE_TRAILING_SECONDS`, `DIVERGENCE_DELTA_VOLUME_FRACTION`, etc. — spec §1 table) are
      module constants, never `Config` fields; a `micro_parameters()` helper (the desk pattern)
      embeds every constant used verbatim into each persisted record, keyed on their hash — a
      monkeypatched constant must move both the parameters hash and the result identity
      (counter-tested). Session boundaries reuse the existing session-honesty module
      (`desk_sessions.py`, spec §0's named arbiter) — never a second definition.
- [ ] The §2.4 granularity benchmark: run on ≥2 real datasets including the largest, NVDA
      `72ca8bc0` (1.97M events, confirmed on disk), measuring bytes-on-disk amplification vs. the
      raw dataset, one-pass build time, and anchor-query latency for the 3 candidate
      representations (per-event rows; per-event sampled-at-anchors; fixed-stride event blocks).
      The winner is pinned as `SNAPSHOT_FORMAT_VERSION = "micro-snapshot-v1"`; the measured table
      is recorded in the iteration handoff. This benchmark and the 18-dataset build below run
      directly against the real `apps/backend/.data/datasets` store via CLI/script — never through
      the browser-QA lane, so the store-scope guard (which gates browser lanes only) does not
      apply here.
- [ ] Build snapshots for all 18 legacy datasets through the manager + CLI; every one carries
      `quote_size_unit: "unverified"` (spec §2.6 — no legacy dataset has a recorded verification
      act; this is a per-dataset property `micro_readiness.py` does not compute or duplicate).
- [ ] Hand-derived oracle fixtures (committed, hermetic) for each feature family — F-FLOW,
      F-RESPONSE, F-LIQUIDITY — feature-level TR-16 vectors (the full Scout/walk-forward
      end-to-end synthetic-corpus oracle is J-05's, out of scope here).
- [ ] Trap tests landing this iteration: **TR-1** (prefix + tail-perturbation, 3 cut points incl.
      i=1); **TR-7** (snapshot cache MISSES on a changed `config_fingerprint`-relevant field and
      on a mutated feature-module byte); **TR-17** (a/b/c — the `available_at` law, truncation
      reproduction, conditioned-outcome refusal); **TR-18** (units gate — unverified-unit fixture
      refuses every cross-basis feature with a typed error; verified twin serves them; mixed-unit
      pooling refused; source-scan proves no silent normalization path exists).
- [ ] **Boundary note (not a build item, a scope fence):** `GET /research/desk/micro/snapshots`
      serves BUILD METADATA only (the identity tuple, `row_count`, `quote_size_unit`, timestamps)
      — never raw per-event feature rows. T-5/the Constraints' accessor-only-door rule governs
      origin-fenced, event-level snapshot READS, which land with `micro_accessor.py` in J-05; do
      not build that module or an event-level read path early.
- [ ] **Test infrastructure (not product code):** extend
      `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` (the ONE mandatory
      launcher — "extended forward, never rewritten," per its own docstring) to place the two
      already-committed tick-dataset fixtures at `apps/backend/tests/fixtures/datasets/*.json`
      into the scoped rig's own throwaway `$ROOT/datasets` directory before backend start,
      mirroring how the script already stages bars/universe/playbook fixtures. Read-only reuse of
      already-committed test fixtures; never a copy of, or pointer into, the real
      `.data/datasets` store.
- [ ] **Test hygiene:** in `apps/backend/tests/test_desk_ui_guards.py`, move the 5 misplaced
      Playbook-Evidence assertions currently living at `:541-554` (inside the iter-1-authored
      `test_desk_page_price_arithmetic_guard_catches_micro_readiness_field_arithmetic`) back into
      `test_desk_page_price_arithmetic_guard_catches_evidence_basis_field_arithmetic` (`:510`),
      whose own docstring already claims them. Every assertion keeps running; only its home
      function changes, so both functions' bodies match their docstrings again.

### Frontend

None — J-02 ships no browser-visible surface (the snapshot compute button and its rendered
progress land in J-08). The QA-rig fixture seeding and the test-hygiene move above are backend
test-infrastructure changes, not application frontend code; zero `.tsx` files are edited.

### New user-facing capability

None new this iteration — the goal's own framing already says J-02 is "keyless/automated with
browser reveals landing in J-08." The one user-visible delta is evidentiary, not capability: the
already-shipped Microscope Readiness panel (J-01) now photographs with a real, non-empty tick
corpus through the mandated QA rig, closing out its last unproven half. The 12/18/~3.0 real-corpus
totals themselves were already provable — and proven — against the operator's actual store in
iteration 1; this iteration does not change what the product can do, only what the browser lane
can now show.

### New information displayed

None — no new UI rendering ships this iteration. `GET /research/desk/micro/snapshots` and its
compute/run siblings are new SERVED endpoints (pinning the Data Contract's already-registered
row), but nothing renders them in `/desk` yet; that is J-08.

### New user actions

None — no compute button exists in the UI yet (Key Capability 2: "the single-flight manager +
CLI"; the UI button is explicitly J-08's scope, listed in OUT OF SCOPE below).

### UI surface changes

None. `/desk`'s DOM is byte-unchanged this iteration (only the QA rig's underlying fixture data
changes, not the page itself or any `data-testid`/heading string).

### Product surface delta

No product surface delta this iteration — J-02 is backend-only research infrastructure. The only
observable delta is evidentiary: the store-scoped QA rig can now serve a real (if small) tick
shard, so J-01's browser half can finally be captured, and the next iterations that need
non-empty tick data through the same rig (J-06, J-08, J-09, per `lessons.md` iter-1) are
unblocked from hitting the identical empty-corpus wall.

### Blueprint conformance

No new page; no nav-skeleton change. The Data Contract row for J-02's three artifacts (new
`app/research/micro_snapshots.py` + its `GET`/`POST`/`POST`-cancel routes) is already
pre-registered in `runs/goal-session-rapid-microscope/state/blueprint.md`'s Data Contract table
(added at baseline, transcribed verbatim from `docs/goal.md` §Product Shape). This iteration is
that row's first concrete elaboration — the exact response shape below — not a new row, so no
`blueprint.md` edit is needed (the same reasoning iteration 1 applied to `micro_readiness.py`).

### Data-contract additions

Elaborates the already-registered `app/research/micro_snapshots.py` row (see Blueprint
conformance) — every field newly served this iteration:

```
GET /research/desk/micro/snapshots ->
{
  "snapshots": [
    {
      "dataset_id": str, "dataset_checksum": str,
      "micro_algo_version": int,                    // MICRO_ALGO_VERSION, 1 today
      "snapshot_format_version": str,                // "micro-snapshot-v1", pinned by the §2.4 benchmark
      "feature_source_hash": str,                    // sha256 over the feature-module bytes
      "config_fingerprint": str,                     // "08e471b10130e1e2" today
      "params_hash": str,                            // sha256 of micro_parameters()
      "quote_size_unit": "unverified" | "shares" | "round_lots",  // "unverified" for every legacy dataset
      "row_count": int >= 0, "bytes_on_disk": int >= 0,
      "built_utc": str (ISO instant)
    }, ...                                           // 18 entries after this iteration's build
  ]
}

POST /research/desk/micro/snapshots/compute ->
  {"state": "running", "run_id": str} | {"state": "refused", "reason": "already_running"}

GET /research/desk/micro/snapshots/compute ->
{
  "state": "idle" | "running" | "done" | "failed" | "cancelled",
  "progress": {"datasets_total": int, "datasets_done": int, "current_dataset_id": str | null},
  "started_utc": str | null, "finished_utc": str | null, "error": str | null
}

POST /research/desk/micro/snapshots/compute/cancel -> {"state": "cancelled"}

GET /research/desk/micro/snapshots/runs ->
  {"runs": [ {"run_id": str, "state": str, "started_utc": str, "finished_utc": str | null,
              "datasets_done": int, "datasets_total": int, "error": str | null}, ... ]}
```

No value here is computed a second time anywhere else: `config_fingerprint` is read verbatim
from `Config().config_fingerprint()`; the engine-derived features reused per §2.5 are read from
the engine snapshot, never recomputed; `quote_size_unit` is the per-dataset manifest stamp
(§2.6), not re-derived. Nothing is added to `blueprint.md` since the module+endpoint row already
exists there.

## OUT OF SCOPE

- `micro_join.py` and the joinable-corpus count (J-03); `scout.py`/`scout_ledger.py` (J-04);
  `micro_accessor.py`/`walkforward.py` (J-05); `tick_recorder.py`/`vault.py` (J-06);
  `micro_graduation.py` (J-07) — all later iterations.
- Any UI rendering of snapshot data, or a "Build Snapshots" button on `/desk` — J-08.
- Any new MCP tool — the surface stays at 22 tools; `desk_micro_readiness`/`desk_scout`/
  `desk_walkforward`/`desk_vault` land in J-08.
- Seeding the QA rig with the full 18-dataset/12-symbol-day corpus — only the two already-committed
  fixture files land this iteration (rubric rule 4, smallest fix that unblocks J-01 now); a wider
  seed is deferred to whichever later iteration needs it (J-06/J-08/J-09).
- Any change to `micro_readiness.py` / `GET /research/desk/micro/readiness` — already built and
  verified correct on the real corpus (Do Not Redo).
- Any new `Config` field or engine change beyond the additive `observer=` kwarg; the fingerprint
  stays `08e471b10130e1e2`.
- Recomputing anything the engine snapshot already owns (aggressor side, the five-window
  features, tape state) — spec §2.5's reuse table is read-only.
- TR-2/3/4/5/6/8/9/10/11/12/13/14/15/16(the full Scout/walk-forward end-to-end form)/19/20/21/22
  — belong to J-03 through J-07/J-10, not this iteration.
- `micro_accessor.py` or any origin-fenced event-level snapshot READ path (see the Boundary note
  above) — J-05's exclusive door.

## DEFINITION OF DONE

- [ ] J-02 passes via unit/integration evidence (no browser surface this iteration): TR-1/TR-7/
      TR-17/TR-18 green; every feature-family oracle fixture (F-FLOW/F-RESPONSE/F-LIQUIDITY)
      green; the §2.4 benchmark table recorded and `SNAPSHOT_FORMAT_VERSION` pinned; 18/18 legacy
      snapshots built with verified identities and `quote_size_unit: "unverified"`;
      `tests/test_observer_equivalence.py` and the golden feature trace pass byte-unmodified.
- [ ] J-01 passes via browser-qa-agent: the `/desk` Microscope Readiness panel, screenshotted
      through the extended store-scoped rig, renders a non-empty, real (fixture-sourced) shard
      table verbatim from `GET /research/desk/micro/readiness` — closing the browser gap
      iteration 1 left open (the literal real-corpus totals stay proven by iteration 1's own
      endpoint-side evidence; Do Not Redo).
- [ ] Required-still-passing J-10's FULL kept-product sentinel remains green (widened regression
      per the prior-`ESCALATE` rule): cockpit `/`, `/structure` load + Tradable Map, every shipped
      `/desk` section.
- [ ] No anti-goal violation introduced (rails 3/5/7/9 and the three cited Rapid-Microscope rails
      re-checked via the same trap tests; full anti-goal table re-verified by the evaluator).
- [ ] Unit tests pass; no regressions — backend suite ≥ 2,723 pass / 8 skip (iteration 1's count),
      fingerprint stays `08e471b10130e1e2`, all 6 `referee_*.py` SHA-256 hashes match iteration
      0's listing.
- [ ] The `test_desk_ui_guards.py` test-hygiene fix lands: both counter-test functions' bodies
      match their own docstrings again, zero assertion coverage lost.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-2-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-01 (Microscope Readiness panel — expand, element-capture per T-10, now showing the
  2 seeded fixture shards) and J-10's FULL kept-product sentinel (cockpit `/` live tape + chart,
  `/structure` load + Tradable Map, every shipped `/desk` section: Playbook Evidence, Band
  Context, Cohorts, Referee Registry/Adjudications/Runs), all via the store-scoped rig
  (`:8301`/`:3301`), clean rebuild first (`rm -rf apps/frontend/.next`, T-9).
- Unit/integration: `micro_observer.py`/`micro_snapshots.py`/`micro_features.py` against hermetic
  hand-derived oracle fixtures (no network) AND against the 18 real legacy datasets for the
  build/identity acceptance (mirrors iteration 1's precedent — a fixture cannot substitute for the
  real-corpus build); TR-1/TR-7/TR-17/TR-18; the granularity benchmark script; the `observer=None`
  default counter-test on `DatasetStore.replay`; the single-flight/cancel/progress behavior of the
  snapshot compute manager; the full backend suite re-run.
- Error cases: an `observer.on_event` that raises stays exception-isolated (the existing
  `_notify_event` discipline, counter-tested, never re-derived) — engine output is unaffected
  either way; a cross-basis feature request against an `unverified`-unit dataset raises the typed
  refusal, never silently normalizes or 500s; a planted outcome starting before its conditioning
  set's max `available_at` is refused by the outcome join, never silently measured early; a
  snapshot read whose `dataset_checksum`/`config_fingerprint`/`feature_source_hash` no longer
  match is refused (the `DatasetIntegrityError` discipline), never served stale or partial.

Test-first contract:

- TC-1: given every existing call site of `DatasetStore.replay` (no `observer` argument) and one
  NEW call with `observer=<probe>`, when the full backend suite runs, then (a) the no-observer
  path stays byte-identical (zero diff to any existing test) and (b) `<probe>.on_event` fires
  once per event in stored order, observing the same snapshot values the no-observer stream
  produces.
- TC-2: given the 18 legacy datasets each replayed once with the micro observer attached, when
  one dataset's snapshot rows are truncated at 3 cut points (incl. i=1), then every retained row
  is byte-identical to its value in the full run, and appending one additional tail event changes
  no prior row's stored value (TR-1).
- TC-3: given a built snapshot for one dataset, when it is re-loaded after (a) `config_fingerprint`
  changes or (b) one byte of `micro_features.py` changes, then the load reports a cache MISS and
  rebuilds rather than serving the stale snapshot (TR-7).
- TC-4: given a feature row whose `observed_through` occurs after its `anchor_at` (e.g. a
  `refill_consistent` deferred construct), when the row is read, then `available_at` equals
  exactly the `observed_through` instant — never `anchor_at`, never any other value (TR-17a).
- TC-5: given a dataset truncated at instant T, when its snapshot is rebuilt from the truncated
  stream, then it contains byte-identically exactly the rows whose full-run `available_at` ≤ T,
  and zero rows with `available_at` > T (TR-17b).
- TC-6: given a planted outcome whose start precedes its conditioning feature set's maximum
  `available_at`, when the outcome join runs, then it is refused with a typed error rather than
  silently measured early (TR-17c).
- TC-7: given a fixture dataset stamped `quote_size_unit: "unverified"`, when any cross-basis
  feature (execution-vs-replenishment ratio, any share-denominated depletion/replenishment
  magnitude) is requested, then it is refused with a typed error; given the verified twin
  fixture, the same feature is served; given a pooled request spanning both, then it is refused
  outright (TR-18).
- TC-8: given the hand-derived F-FLOW oracle fixture (a short synthetic trade sequence with known
  sides), when cumulative delta, rolling imbalance, same-side run length, volume burst, and
  divergence-at-level are computed, then every value matches the fixture's committed expected
  values exactly, with `unknown`-side prints excluded from cumulative delta and counted.
- TC-9: given the hand-derived F-RESPONSE oracle fixture, when impact efficiency, efficiency
  trend, `failed_aggression_score`, and response asymmetry are computed, then every value matches
  the fixture's expected values, and response asymmetry reads `unavailable` (never a guessed
  number) when the session ends before `RESPONSE_K_TRADES` subsequent trades exist.
- TC-10: given the hand-derived F-LIQUIDITY oracle fixture, when spread change, quote imbalance,
  microprice, quote depletion, and `refill_consistent` are computed, then every value matches the
  fixture's expected values, and no "iceberg"/institutional-intent string appears anywhere in the
  output.
- TC-11: given ≥2 real datasets including NVDA `72ca8bc0` (1.97M events), when the §2.4
  granularity benchmark runs the 3 candidate representations, then bytes-on-disk amplification,
  one-pass build time, and anchor-query latency are recorded for each, the chosen representation
  is pinned as `SNAPSHOT_FORMAT_VERSION = "micro-snapshot-v1"`, and the table appears in
  `docs/handoffs/goal-rapid-microscope-iter-2-dev.md`.
- TC-12: given all 18 legacy datasets, when snapshots are built through the manager + CLI, then
  `GET /research/desk/micro/snapshots` lists 18 entries, every one carrying
  `quote_size_unit: "unverified"` and a `(dataset_id, dataset_checksum, config_fingerprint,
  feature_source_hash, params_hash)` identity that re-verifies on a second read.
- TC-13: given the snapshot-build manager is already running, when a second build is requested
  concurrently, then it is refused per the single-flight pattern (never two concurrent builds),
  and `GET /research/desk/micro/snapshots/compute` reports `datasets_done` increasing
  monotonically until `state == "done"`.
- TC-14: given `tests/test_observer_equivalence.py` and the golden feature trace
  (`test_dense_replay_gate.py`), when they run this iteration, then both pass byte-unmodified
  (zero diff to either file).
- TC-15: given the store-scoped QA rig freshly started via the extended launcher, when `GET
  /research/desk/micro/readiness` is called through it, then `totals.distinct_symbol_days >= 1`
  and `shards` is non-empty (the two seeded fixture datasets), and the `/desk` Microscope
  Readiness panel — expanded and element-screenshotted — renders that same non-empty,
  non-fabricated shard data verbatim.
- TC-16: given `test_desk_ui_guards.py`'s two adjacent counter-test functions, when the 5
  misplaced Playbook-Evidence assertions are moved from
  `..._catches_micro_readiness_field_arithmetic` into
  `..._catches_evidence_basis_field_arithmetic`, then the destination function's body contains
  all 5 of its docstring-claimed assertions, the source function's body contains only its own
  Microscope-Readiness assertions, and both functions still pass.
- TC-17: given the full backend suite and iteration 1's baseline (2,723 pass / 8 skip, fingerprint
  `08e471b10130e1e2`, the 6 referee-module SHA-256 listing from iteration 0), when re-run this
  iteration, then the suite count is ≥ 2,723 pass with 0 new failures, the fingerprint is
  unchanged, and all 6 referee SHA-256 hashes match iteration 0's listing exactly.
- TC-18: given the shipped `/`, `/structure`, and every shipped `/desk` section, when
  browser-qa-agent re-verifies them this iteration (widened regression per the prior-`ESCALATE`
  rule), then every one renders exactly as previously shipped, with zero `data-testid` or copy
  change anywhere outside the QA-rig fixture seeding.
- TC-19: given the iteration completes, when the developer writes the handoff, then
  `docs/handoffs/goal-rapid-microscope-iter-2-dev.md` exists and records the granularity-benchmark
  table, the 18/18 snapshot build result, and the suite/fingerprint/referee-hash re-check results.

## NOTES

- Interpretation call logged to `runs/goal-session-rapid-microscope/state/assumptions.md` as
  `iter-2 — goal-decomposer`: the browser evidence for J-01 shows a small, real (not fabricated)
  2-shard/1-symbol corpus proving the rendering path, not a literal reproduction of the specific
  12/18/~3.0 real-corpus totals — those stay proven by iteration 1's endpoint-side evidence
  against the operator's real store. Reversible: a later iteration may instead scope the
  readiness cache to read the real corpus read-only once the snapshot-compute route's storage dir
  is confirmed fully isolated from `TAPEOLOGY_DATASET_DIR`'s sibling-default resolution.
- Applying `lessons.md` iter-1 directly: this iteration is the fix for the flagged gap
  ("seed them (or scope the readiness cache and let the rig read the real corpus read-only)
  BEFORE a browser acceptance depends on non-empty tick data... Applies to... J-06's vault
  states, J-08's four `/desk` micro sections, and J-09's study results"). Applying `lessons.md`
  iter-0: the backend suite must be invoked as `pytest tests/` with no added `-q`, and
  `status.json`'s `browser_checks_run` flag is stale — trust
  `reports/phase-*-ui-test-results.md` and the evidence directory instead.
- Do Not Redo (iteration-state, binding): `micro_readiness.py` +
  `GET /research/desk/micro/readiness` (built, verified correct on the real store, 31/31 unit
  tests green); the `/desk` Microscope Readiness section's existing render; the era-open
  invariants (fingerprint, 6/6 referee SHA-256, MCP 22-tuple, store-scope guard). None of these
  are rebuilt or re-derived this iteration. `WF_TRAIN_MIN_SESSIONS`/`WF_TEST_MIN_SESSIONS` stay
  solely in `micro_readiness.py` — J-02 does not touch them (that reconciliation is J-05's).
- Depth is `full` per the binding evaluator recommendation and the mandatory prior-`ESCALATE`
  rule (Full trigger 3); no full trigger needed to be independently argued, though trigger 1
  (structural/cross-cutting — this iteration touches the two byte-frozen replay/observer files)
  independently applies too.
- The `_PRICE_ARITHMETIC_FIELDS` frontend guard does NOT need extension this iteration — no new
  numeric is rendered in any `.tsx` file (J-02 has no UI surface; the QA-rig fixture seeding only
  changes what data the ALREADY-shipped J-01 panel reads, not what it renders).
