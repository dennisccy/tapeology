# goal-rapid-microscope-iter-2 Execution Plan

## Context (for the dispatched agents, not part of the spec)

Session `rapid-microscope`, iteration 2, target journeys **J-02** (new) with **J-01** closed out
and **J-10 widened to the FULL kept-product sentinel** (mandatory because iter-1 returned
`ESCALATE`). Iter-1 already shipped and real-corpus-verified `micro_readiness.py` +
`GET /research/desk/micro/readiness` + the `/desk` Microscope Readiness panel — **Do Not Redo**.
Iter-1's only gap was evidentiary: the mandated store-scoped browser rig (`:8301`/`:3301`) points
`TAPEOLOGY_DATASET_DIR` at a fixture dir with zero tick datasets, so the shipped panel could only
be proven via API/text-extract, never a real screenshot. This iteration's job is (a) build J-02
(the observer/snapshot/feature machinery, byte-honest per spec) and (b) seed two already-committed
tick fixtures into the QA rig so J-01's panel finally photographs non-empty. The canonical spec is
`docs/rapid-validation-spec.md` (§0–§4 govern this iteration; implement verbatim, never re-derive —
an ambiguity is a drop + owner ruling, not an invention). The full acceptance contract (TC-1
through TC-19) is spelled out in `docs/phases/goal-rapid-microscope-iter-2.md` — developer and
reviewer should read that file directly; this plan is a routing guide, not a spec substitute.

No scope-creep or CLAUDE.md contradiction found: the iteration spec is unusually disciplined,
already fences off J-03–J-07 work, UI rendering, new MCP tools, wider QA-rig seeding, and any new
`Config` field in its own OUT OF SCOPE section, and is squarely the next dependency-ordered journey
Key Capability 2 / Success Criteria #1–#2 call for. Nothing here needs trimming.

## What to Build

- Additive `observer=` kwarg on `DatasetStore.replay` — default `None`, byte-identical to today
  (counter-tested); wires `TapeEngine.add_observer` once before the event loop starts. No second
  replay implementation.
- `micro_observer.py` — the streaming, prefix-honest observer (spec §2.2): snapshot row *i* is a
  pure function of events `1..i` + the engine snapshot after event *i*; flush before the next
  event; deferred constructs (e.g. `refill_consistent`, response-over-K) written at their
  `observed_through` row, referencing `anchor_at`, never attached retroactively.
- `micro_snapshots.py` — snapshot identity + load-time verification (spec §2.3: `dataset_id` +
  `dataset_checksum` + `MICRO_ALGO_VERSION` + `SNAPSHOT_FORMAT_VERSION` + `feature_source_hash` +
  `config_fingerprint` + `params_hash`, re-verified on every read, `DatasetIntegrityError`
  discipline reused); single-flight compute-manager + CLI mirroring
  `desk_forward_compute.DeskForwardComputeManager` / `desk_playbook_compute.py` (no new pattern);
  the §2.4 granularity benchmark routine.
- `micro_features.py` — F-FLOW / F-RESPONSE / F-LIQUIDITY Wave-1 primitives (spec §3): cumulative
  delta, rolling imbalance, run length, volume burst, divergence-at-level; impact efficiency +
  trend, `failed_aggression_score`, response asymmetry; spread change, quote imbalance,
  microprice, quote depletion, `refill_consistent`. Every value carries
  `anchor_at`/`observed_through`/`available_at`, per-row `side_source`, per-window
  `fallback_frac`/`unknown_frac`; §2.6 cross-basis unit gating on share-denominated
  liquidity features; §4 mid-only primary outcome set + separately named last-trade sensitivity
  column. `micro_parameters()` embeds every module constant verbatim, keyed on hash
  (monkeypatch-counter-tested). Reuses `desk_sessions.py` for session boundaries — never a second
  definition. Engine-derived values (aggressor side, five-window features, tape state,
  bid/ask/spread/last) are read from the snapshot verbatim, never recomputed.
- The §2.4 granularity benchmark on ≥2 real datasets incl. NVDA `72ca8bc0` (1.97M events, 3
  candidate representations); pin the winner as `SNAPSHOT_FORMAT_VERSION = "micro-snapshot-v1"`;
  record the measured table in the dev handoff. Runs via CLI/script directly against the real
  `.data/datasets` store — never through the browser-QA lane.
- Build snapshots for all 18 legacy datasets through the manager + CLI; every one stamped
  `quote_size_unit: "unverified"` (no legacy dataset has a recorded verification act).
- Hand-derived, committed oracle fixtures for each feature family (F-FLOW/F-RESPONSE/F-LIQUIDITY)
  — feature-level TR-16 vectors only; the full Scout/walk-forward end-to-end oracle is J-05's.
- Trap tests landing this iteration: TR-1 (prefix + tail-perturbation, 3 cut points incl. i=1),
  TR-7 (cache MISS on changed `config_fingerprint` or mutated feature-module byte), TR-17a/b/c
  (availability law, truncation reproduction, conditioned-outcome refusal), TR-18 (units gate,
  incl. a source-scan proving no silent normalization path exists).
- Extend `apps/backend/app/research/micro_routes.py` with three new byte-identical GET-proxy
  routes: `GET /snapshots`, `POST`/`GET`/`POST .../cancel` on `/snapshots/compute`,
  `GET /snapshots/runs` — page-load GETs never compute.
- Test infra (not product code): extend `qa_playbook_iter7_fixture_scoped_backend.sh` to stage the
  two already-committed tick fixtures (`tests/fixtures/datasets/6c9bf2c7…json`,
  `d9f9dbe0…json`) into the scoped rig's own throwaway `$ROOT/datasets`, mirroring how it already
  stages bars/universe/playbook fixtures — read-only reuse, never a pointer at the real store.
- Test hygiene: in `test_desk_ui_guards.py`, move the 5 misplaced Playbook-Evidence assertions
  (currently inside the iter-1-authored micro-readiness counter-test, ~:541-554) into
  `test_desk_page_price_arithmetic_guard_catches_evidence_basis_field_arithmetic` (:510), whose
  docstring already claims them — zero assertion coverage lost, both functions' bodies match their
  own docstrings again.
- Full regression close-out: backend suite ≥ 2,723 pass / 8 skip / 0 new failures; fingerprint
  stays `08e471b10130e1e2`; all 6 `referee_*.py` SHA-256 hashes match the iteration-0 baseline;
  `tests/test_observer_equivalence.py` and the golden feature trace
  (`test_dense_replay_gate.py`) pass byte-unmodified.

**Do Not Redo / touch:** `micro_readiness.py`, `GET /research/desk/micro/readiness`, the existing
`/desk` Microscope Readiness section render (all iter-1, verified). **Do not build this
iteration:** `micro_join.py` (J-03), `scout.py`/`scout_ledger.py` (J-04), `micro_accessor.py`/
`walkforward.py` (J-05), `tick_recorder.py`/`vault.py` (J-06), `micro_graduation.py` (J-07), any
`.tsx` rendering of snapshot data or a "Build Snapshots" button (J-08), any new MCP tool (stays at
22), any new `Config` field, or a wider QA-rig seed than the 2 named fixtures.

## Agents Required

- backend-data: yes -- implement the observer wiring (`datasets.py`), `micro_observer.py`,
  `micro_snapshots.py` (identity + compute-manager + CLI + benchmark), `micro_features.py`, the
  3 new `micro_routes.py` routes, the 18-dataset snapshot build, the oracle fixtures, traps
  TR-1/TR-7/TR-17/TR-18, the QA-rig fixture-seeding script extension, and the
  `test_desk_ui_guards.py` hygiene fix.
- frontend-ux: no -- zero `.tsx` files are edited this iteration; the already-shipped Microscope
  Readiness panel is reused unchanged. It is simply fed real (if small) fixture data through the
  QA rig instead of an empty store — a test-infrastructure change, not application code.

## Frontend Present
Frontend Present: yes

(No new UI ships — browser-qa-agent still runs because this iteration must (1) prove, via
element-screenshot through the extended store-scoped rig, that the already-shipped J-01 panel now
renders a non-empty, real shard table instead of the empty corpus iter-1 could only show via
API/text-extract, and (2) re-verify the WIDENED J-10 kept-product sentinel — cockpit `/`,
`/structure` load + Tradable Map, and every shipped `/desk` section including all three Referee
sections — mandatory this iteration because iter-1 returned `ESCALATE`.)

## Files to Create/Modify

- `apps/backend/app/research/datasets.py` -- MODIFY: additive `observer: object | None = None`
  kwarg on `DatasetStore.replay` (:376); every existing call site stays byte-identical.
- `apps/backend/app/research/micro_observer.py` -- NEW: the prefix-honest streaming observer.
- `apps/backend/app/research/micro_snapshots.py` -- NEW: snapshot identity/verification,
  single-flight compute-manager + CLI, the §2.4 benchmark routine.
- `apps/backend/app/research/micro_features.py` -- NEW: F-FLOW/F-RESPONSE/F-LIQUIDITY primitives
  + `micro_parameters()`.
- `apps/backend/app/research/micro_routes.py` -- MODIFY: extend with the 3 new snapshot routes
  (currently only `GET /readiness`).
- New test modules (naming at developer's discretion, mirroring `test_micro_readiness.py`'s
  precedent) covering TC-1/2 (observer wiring + TR-1), TC-3 (TR-7), TC-4/5/6 (TR-17a/b/c), TC-7
  (TR-18), TC-8/9/10 (feature-family oracles), TC-11 (benchmark), TC-12 (18/18 build + identity),
  TC-13 (single-flight/cancel/progress).
- `apps/backend/tests/test_desk_ui_guards.py` -- MODIFY: extend `_PRICE_ARITHMETIC_FIELDS` for any
  new served snapshot-metadata numeric; TC-16 hygiene fix (move the 5 misplaced assertions to
  their docstring-claimed function).
- `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` -- MODIFY (extend, never
  rewrite): stage the 2 committed tick fixtures into the scoped rig's `$ROOT/datasets`.
- `docs/handoffs/goal-rapid-microscope-iter-2-dev.md` -- NEW: dev handoff with the benchmark
  table, 18/18 build result, and suite/fingerprint/referee-hash re-check.

## UI Evolution (Frontend Present: yes, but no new capability this iteration)

- New user-facing capability: none. The already-shipped Microscope Readiness panel (J-01) is
  reused verbatim.
- New information displayed: none — `GET /research/desk/micro/snapshots` and its compute/run
  siblings are new SERVED endpoints this iteration but nothing renders them yet (that is J-08).
- New user actions: none — no compute/build button exists in the UI yet (J-08's scope).
- UI surface changes: none — `/desk`'s DOM is byte-unchanged; only the QA rig's underlying
  fixture data changes (2 seeded tick datasets), not the page or any `data-testid`/heading string.
- Navigation changes: none.

## Visual Requirements (Frontend Present: yes)

- No new rendering. Reuse the exact shipped Microscope Readiness panel and every existing
  `/structure`/`/desk` section's current visual treatment, unchanged.
- QA must confirm the panel's existing empty-state copy (e.g. no shards) no longer renders now
  that the rig serves 2 real fixture shards, and that the shard table / totals line / floors
  table render those same values verbatim from the API (element-capture, per T-10 — no screenshot
  ⇒ `unknown`, never `passing`).
- Full `rm -rf apps/frontend/.next` + rebuild before any browser pass (T-9).

## Key Test Scenarios

- TC-1: every existing `DatasetStore.replay` call site (no `observer` arg) stays byte-identical; a
  new probe observer's `on_event` fires once per event in stored order.
- TC-2 (TR-1): a dataset's snapshot truncated at 3 cut points (incl. i=1) reproduces
  byte-identical retained rows; one extra tail event changes no prior row.
- TC-3 (TR-7): a snapshot re-load after a `config_fingerprint` change, or a one-byte
  `micro_features.py` change, reports a cache MISS and rebuilds rather than serving stale.
- TC-4/5/6 (TR-17a/b/c): a deferred construct's `available_at` equals exactly its
  `observed_through` instant; truncating at T reproduces byte-identically exactly the rows with
  `available_at` ≤ T; an outcome starting before its conditioning set's max `available_at` is
  refused with a typed error.
- TC-7 (TR-18): an `unverified`-unit fixture refuses every cross-basis feature with a typed error;
  the verified twin serves them; a pooled request spanning both is refused outright.
- TC-8/9/10: hand-derived F-FLOW/F-RESPONSE/F-LIQUIDITY oracle fixtures match committed expected
  values exactly; response asymmetry reads `unavailable` (never guessed) when the session ends
  first; zero "iceberg"/institutional-intent language appears anywhere.
- TC-11: the §2.4 benchmark runs on ≥2 real datasets incl. NVDA `72ca8bc0`; bytes-amplification /
  build-time / query-latency recorded for all 3 candidate representations;
  `SNAPSHOT_FORMAT_VERSION = "micro-snapshot-v1"` pinned; table lands in the dev handoff.
- TC-12: all 18 legacy datasets get built snapshots; `GET /research/desk/micro/snapshots` lists 18
  entries, every one `quote_size_unit: "unverified"`, identity re-verifies on a second read.
- TC-13: the compute manager refuses a second concurrent build (single-flight);
  `GET .../compute` reports `datasets_done` increasing monotonically to `state == "done"`.
- TC-14: `test_observer_equivalence.py` and the golden feature trace
  (`test_dense_replay_gate.py`) pass byte-unmodified — zero diff to either file.
- TC-15: through the extended store-scoped rig, `GET /research/desk/micro/readiness` returns a
  non-empty shard table (the 2 seeded fixtures), and the `/desk` Microscope Readiness panel,
  element-screenshotted, renders that same non-empty data verbatim — closing the iter-1 ESCALATE
  gap.
- TC-16: `test_desk_ui_guards.py`'s two counter-test functions each contain exactly their own
  docstring-claimed assertions after the move; both still pass.
- TC-17: full backend suite ≥ 2,723 pass / 8 skip / 0 new failures; fingerprint unchanged
  (`08e471b10130e1e2`); all 6 referee-module SHA-256 hashes match the iteration-0 baseline exactly.
- TC-18 (widened J-10 sentinel, mandatory post-ESCALATE): cockpit `/` live tape + chart,
  `/structure` load + Tradable Map, every shipped `/desk` section (Playbook Evidence, Band
  Context, Cohorts, Referee Registry/Adjudications/Runs) render exactly as shipped, zero
  `data-testid`/copy change anywhere outside the QA-rig fixture seeding.
- TC-19: `docs/handoffs/goal-rapid-microscope-iter-2-dev.md` exists and records the benchmark
  table, the 18/18 snapshot build result, and the suite/fingerprint/referee-hash re-check.
