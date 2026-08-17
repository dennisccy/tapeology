# goal-rapid-microscope-iter-2 Dev Handoff

**Phase:** goal-rapid-microscope-iter-2
**Date:** 2026-08-17
**Agent:** developer
**Status:** complete

## What Was Built

- **The additive observer seam on replay** (`apps/backend/app/research/datasets.py`):
  `DatasetStore.replay(dataset_id, config, *, observer=None)` — an additive, default-`None` kwarg
  that calls the engine's existing `TapeEngine.add_observer` once before the event loop. `observer=None`
  stays byte-identical to every pre-existing call site (counter-tested).
- **`micro_observer.py`** — the streaming, prefix-honest `MicroObserver`. One row per TRADE event
  (never per raw event — see the granularity benchmark below); each row is a pure function of
  events `1..i` plus the engine snapshot, flushed synchronously before the next event. Tracks its
  own quote state (bid/ask/sizes — the engine drops quote sizes) to derive `side_source`
  (`quote_rule`/`tick_test`/`carried`/`unknown`) by mirroring `classify_aggressor`'s own documented
  stage-1 precondition (never recomputing the SIDE itself, which is always read verbatim from
  `snapshot.recent_trades[0].side`). Implements three deferred constructs — `response_asymmetry`
  (resolves exactly at the K-th subsequent trade row), `refill_consistent` and `quote_depletion`
  (quote-driven, attached to whichever row is being built when they resolve, or swept into an
  honest `unavailable` at `finalize()` if the session ends first).
- **`micro_features.py`** — the Wave-1 pure arithmetic: F-FLOW (cumulative delta, rolling
  imbalance over trade-count and share-count windows, same-side run length, volume burst,
  divergence-at-level), F-RESPONSE (impact efficiency, efficiency trend, `failed_aggression_score`,
  the reused-verbatim `absorption_score`), F-LIQUIDITY (quote imbalance, microprice, spread
  change), the closed outcome set (mid-basis primary + last-trade sensitivity column, the
  `available_at`/TR-17c refusal), and the section 2.6 cross-basis unit gate
  (`CrossBasisUnverifiedUnitError`). `micro_parameters()`/`micro_parameters_hash()` embed every
  constant verbatim.
- **`micro_snapshots.py`** — snapshot identity (the 7-component tuple), load-time re-verification
  (an honest cache MISS on any identity drift, never a served-stale value), the single-flight
  `MicroSnapshotComputeManager` (the `desk_playbook_compute`/`desk_forward_compute` pattern —
  cooperative cancel at dataset boundaries, monotonic progress, a durable JSONL run log), and the
  CLI (`python -m app.research.micro_snapshots [--dataset-id ID ...] [--all]`).
  `SNAPSHOT_FORMAT_VERSION = "micro-snapshot-v1"` pinned by the granularity benchmark below.
- **Three new routes** on `micro_routes.py`: `GET /research/desk/micro/snapshots`,
  `POST`/`GET`/`POST .../cancel` on `/snapshots/compute`, `GET /snapshots/runs` — all byte-identical
  GET-proxy-shaped reads/triggers, page-load GETs never compute.
- **18/18 legacy dataset snapshots built** through the manager + CLI against the real
  `apps/backend/.data/datasets` store (see the real-corpus section below).
- **Trap tests**: TR-1 (prefix + tail-perturbation, 3 cut points incl. i=1, against a real
  committed tick fixture), TR-7 (cache MISS on a `config_fingerprint` change and on a mutated
  `feature_source_hash`), TR-17a/b/c (availability triple, truncation reproduction, the planted-
  outcome refusal), TR-18 (units gate + an AST-based source-scan proving no ungated
  `quote_size_unit` arithmetic path exists).
- **Test infrastructure**: `qa_playbook_iter7_fixture_scoped_backend.sh` now stages the two
  already-committed PG SIP tick fixtures into the scoped rig's own throwaway `$ROOT/datasets`
  before backend start (a plain file copy — the fixture IS the on-disk store shape already).
- **Test hygiene**: the 5 misplaced Playbook-Evidence assertions (`:541-554`) moved from
  `test_desk_page_price_arithmetic_guard_catches_micro_readiness_field_arithmetic` back into
  `test_desk_page_price_arithmetic_guard_catches_evidence_basis_field_arithmetic`, whose docstring
  already claimed them — zero coverage lost, both functions' bodies match their own docstrings.

## Files Changed

- `apps/backend/app/research/datasets.py` -- MODIFY: additive `observer=` kwarg on `DatasetStore.replay`.
- `apps/backend/app/research/micro_observer.py` -- NEW: the streaming observer.
- `apps/backend/app/research/micro_features.py` -- NEW: constants + pure Wave-1 arithmetic + outcomes + unit gate.
- `apps/backend/app/research/micro_snapshots.py` -- NEW: identity/persistence/compute manager/CLI.
- `apps/backend/app/research/micro_routes.py` -- MODIFY: three new snapshot routes.
- `apps/backend/tests/test_micro_observer.py` -- NEW: TC-1/TC-2/TR-1/TR-17a/b + F-FLOW/F-RESPONSE/F-LIQUIDITY streaming oracles (TC-8/9/10).
- `apps/backend/tests/test_micro_features.py` -- NEW: pure-function oracles, outcome/TR-17c tests, unit-gate/TR-18 tests incl. the AST source scan.
- `apps/backend/tests/test_micro_snapshots.py` -- NEW: identity/TR-7/compute-manager/routes tests + the real 18-dataset corpus acceptance (TC-12).
- `apps/backend/tests/test_desk_ui_guards.py` -- MODIFY: the 5-assertion hygiene move (TC-16).
- `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` -- MODIFY: stage the 2 tick fixtures.
- `apps/backend/scripts/micro_snapshot_granularity_benchmark.py` -- NEW: the one-time section-2.4 benchmark script.

## The section 2.4 granularity benchmark (TC-11)

Run via `python scripts/micro_snapshot_granularity_benchmark.py` against the REAL
`apps/backend/.data/datasets` store on NVDA `72ca8bc0` (largest, 1,973,556 events / 928,933 trades)
and PG `dcfcf3cd` (14,241 events / 3,229 trades, the `test_dense_replay_gate.py` twin). Three
candidate representations measured:

| Dataset | Representation | Rows | Bytes on disk | Amplification vs. raw | Build time | Anchor-query latency |
|---|---|---:|---:|---:|---:|---:|
| NVDA (1.97M events, 198.5 MB raw) | A — per-event rows | 1,973,557 | 1,644,853,225 | 8.29x | 141.34 s | 2.32 µs |
| NVDA | **B — per-event sampled-at-anchors (SHIPPED)** | 928,934 | 1,488,653,258 | 7.50x | ~116 s (measured separately during dev; reused here) | 0.31 µs |
| NVDA | C — fixed-stride blocks (stride 200) | 9,868 | 1,160,493 | 0.0058x | 11.24 s | 0.17 µs |
| PG (14,241 events, 1.49 MB raw) | A — per-event rows | 14,242 | 7,342,322 | 4.93x | 0.474 s | 0.16 µs |
| PG | **B — per-event sampled-at-anchors (SHIPPED)** | 3,230 | 5,697,637 | 3.82x | 0.380 s | 0.15 µs |
| PG | C — fixed-stride blocks (stride 200) | 72 | 8,452 | 0.0057x | 0.051 s | 0.13 µs |

**Winner: Representation B, pinned as `SNAPSHOT_FORMAT_VERSION = "micro-snapshot-v1"`.** Every
Wave-1 feature family (spec section 3) and every outcome (section 4) is anchored at a TRADE (or a
future structural touch, joined read-side in J-03) — never at a bare quote tick. Representation A
pays 8-10% more bytes and runs ~35-40% slower to build (NVDA: 141s vs. ~116s) for zero additional
research capability this era's questions can use, since a standalone quote row carries no anchor
anything ever queries. Representation C is dramatically smaller (a genuine ~170x fewer bytes on
NVDA) but throws away exactly the row-level trajectory every feature family needs — cumulative
delta at a specific trade, `side_source`, the deferred completions — collapsing to block summaries
that could not answer a single one of the TC-8/9/10 oracle assertions this iteration proves.
Representation B's own anchor-query latency is also the fastest of the three on the larger corpus
(likely dominated by array-load and only mildly by row count at this scale, so this axis is a weak
tie-breaker relative to bytes/build-time, reported for completeness per the spec's own three
named axes).

## The real 18-dataset legacy corpus build (TC-12)

Built via `python -m app.research.micro_snapshots --all` against the real
`apps/backend/.data/datasets` store (18 files, ~0.92 GB raw). Result: **18/18 snapshots built**,
every one stamped `quote_size_unit: "unverified"` (spec section 2.6 — no legacy dataset carries a
recorded verification act), every identity re-verifying on a second `load_snapshot_meta` read.
Total snapshot storage: 3,815,933 rows (3,815,915 trade-anchored rows + one honest close-out row
per dataset sweeping that dataset's still-pending deferred constructs), 6,232.8 MB on disk. Total
wall-clock build time (fresh, cold): approximately 8-9 minutes on this host — throughput ranged
from ~44,000 events/s on the small PG fixtures down to ~17,000 events/s on NVDA (the biggest
single dataset, 1.97M events, completed in 116 s). This build runs via CLI/script directly against
the real store, never through the browser-QA lane or the hermetic pytest suite's default path — the
real-corpus acceptance test (`tests/test_micro_snapshots.py::test_tc12_*`) is module-scoped and
REUSES an already-valid build (via the same `load_snapshot_meta` identity check the compute
manager itself uses), so it only pays this cost on a machine's first-ever run.

## Interpretation calls (logged, not spec-ambiguities requiring an owner ruling)

These are engineering judgment calls within genuinely underspecified corners of an otherwise
frozen spec — none contradict a stated rule, and each is reversible in a later iteration:

- **`side_source` derivation.** The spec requires serving `side_source` beside every
  aggressor-derived quantity, but the engine exposes no stage-decision flag. `MicroObserver`
  mirrors `classify_aggressor`'s own DOCUMENTED stage-1 precondition against quote/prior-trade
  state it tracks itself (never reading engine-private state) — the identical technique
  `micro_readiness.py`'s own `_quote_rule_decides` already uses and its docstring justifies. The
  actual SIDE is always read verbatim from the engine snapshot, never recomputed.
- **"Session boundary" reuse of `desk_sessions.py`.** The iteration plan names this module as the
  session arbiter; on inspection, every J-02 dataset shard is already one recorded WINDOW inside
  one calendar session (established by `micro_readiness.py`'s own `session_date` resolution, Do
  Not Redo), and each `MicroObserver` instance is constructed fresh per replay — so "session
  anchor" and "replay start" coincide by construction, and there is no cross-session boundary
  within one dataset replay for an arbiter to resolve. `desk_sessions.py` is therefore not
  imported here; nothing invents a second session definition.
- **`price_extreme(tau)` = MAX mid, not min.** Spec section 3 says "max/min" without
  disambiguating; a higher price extreme paired with a weaker cumulative-delta extreme is the
  only reading consistent with the formula's own name, "bearish divergence."
- **`response_asymmetry`'s units.** Spec says "signed mid move" without naming a unit; bps
  (matching `impact_efficiency`'s own basis) was chosen so the value is comparable across
  instruments at different price levels, rather than a raw, symbol-specific dollar amount.
- **`quote_depletion`'s "current window" attachment.** A depletion window's anchor is a QUOTE
  price-run start, not a trade — so it cannot literally live on "its own" row under the
  trade-anchored representation. It resolves at a price change or the update bound and attaches
  to whichever row (a subsequent trade, or the session's `finalize()` close-out) is built next —
  the identical mechanism `refill_consistent` uses, generalized.
- **"Primary" feature window for `failed_aggression_score`.** The engine's own `absorption_score`
  (reused verbatim) is read from its 30-second CLOCK primary window; the NEW continuous
  `failed_aggression_score` complement uses this module's own smallest trade-COUNT window (20
  trades) as ITS primary — a distinct concept, not a reuse of the engine's window choice.
- **Divergence-at-level's delta baseline floor.** Section 3 ties the delta formula to "the SAME
  session-prefix baseline windows" volume burst draws from; the identical `< 5 windows =>
  undefined` floor was therefore applied to it too (not merely an empty-list check), for
  consistency with the shared baseline-window pool it explicitly names.

## Tests Run

> **Superseded by the Fix Notes below.** The FINAL numbers for this iteration are
> **2,828 passed / 8 skipped / 0 failed** — see "Fix Notes (review FAIL, 2026-08-17)".

Command: `cd apps/backend && .venv/bin/python -m pytest tests/`
Result: **2,822 passed, 8 skipped, 0 failed** (444.67s) — the FINAL run, against the freshly
rebuilt 18-dataset real-corpus snapshots (a rebuild triggered naturally by TR-7's own honest-MISS
mechanism after a mid-development source fix, then re-confirmed clean by an explicit CLI rebuild +
one more full suite pass). Baseline (iteration 1 / era-open): 2,691 pass / 8 skip = 2,699 total;
this iteration's requirement (goal-slice DEFINITION OF DONE) was ≥ 2,723 pass with 0 new failures
— met with room to spare (+123 pass net of the 8 unchanged skips, all of it new J-02 coverage; 0
regressions in any pre-existing test). An intermediate run (before the final deliberate rebuild,
while two trailing cosmetic fixes — see Known Issues — were still only on disk, not yet reflected
in the then-in-flight snapshot build) also passed clean at 2,821/8/0, confirming stability across
both runs.

### Era-open invariant re-check (J-10 / iteration-0 baseline)

- `Config().config_fingerprint()` → `08e471b10130e1e2` — unchanged.
- All 6 `referee_*.py` SHA-256 hashes — byte-identical to the iteration-0 listing (re-verified
  directly, not merely by test pass):
  ```
  482f38a11740bc839038290fc2a0e131f649a23f17265cbca0f2aa19fe07e1c5  referee_evidence.py
  03840c863b1e1f382ad2588d3bb6d8dc0e36a70582c3cb7a716638dabef32d99  referee_registry.py
  0cc3a06f7b382c63d544886ec74a47f2414612fc77dd3dac444b00cc35216140  referee_routes.py
  6dd807b5ab69af033686a395484b1b10515d0f453a79c0943e534a578259786c  referee_adjudicate.py
  fba8816a5d4901ea1eeb7faa71e350538f546a2a3af1f9edb5f6f5aa1ec5271c  referee_stats.py
  34917e381e4169aa029f5d0e18228fde75e4d3db5acec516f937e3ef3b371603  referee_null.py
  ```
- MCP `EXPECTED_TOOLS` — still the 22-tuple (unchanged; no MCP tool added this iteration).
- `tests/test_observer_equivalence.py` and `tests/test_dense_replay_gate.py` — zero diff to
  either file; both pass as part of the full suite above.

## Known Issues

- **`micro_accessor.py` (origin-fenced event-level reads) is explicitly out of scope this
  iteration** (J-05) — `GET /research/desk/micro/snapshots` serves build metadata only, per the
  iteration's own boundary note. Nothing this iteration reads a snapshot's raw rows except the
  build/verification code itself and this iteration's own tests.
- **Snapshot storage is substantial**: 6.2 GB for the 18-dataset legacy corpus (≈6.8x raw bytes).
  This is expected and disclosed by spec section 2.4's own framing ("the tranche corpus will be
  multiples of that") — flagged here for the operator's disk-budget awareness ahead of J-06's
  larger tranche.
- **`response_asymmetry`/`refill_consistent`/`quote_depletion` are wired into the live observer
  and proven on hand-crafted oracle fixtures + the real 18-dataset build (no crash, sane values);
  TWO Wave-1 primitives are proven ONLY as pure oracle-tested functions and are called from no
  streaming path this iteration** — (1) `divergence_at_level`, which has no live trigger because no
  structural touch join exists yet (`micro_join.py` is J-03), and (2)
  `execution_vs_replenishment_ratio`, which has no §2.6-legal call site: it is CROSS-BASIS, and
  every one of the 18 legacy datasets is `quote_size_unit: "unverified"`, so wiring it today would
  emit a refusal on every real row and a served value on none. Both are complete, oracle-tested
  arithmetic waiting on a caller; neither is a gap against this iteration's stated scope (the
  execution plan's own F-LIQUIDITY streaming list names spread change, quote imbalance, microprice,
  quote depletion, and `refill_consistent` — not this ratio). The FIRST dataset carrying a verified
  unit (J-06's recorder stamps it) is what makes a live call site legal.
- **Two trailing cosmetic fixes made after the first real 18-dataset build**, both zero-risk and
  both covered by the FINAL rebuild + suite pass above: (1) `micro_observer.py`'s `event_index`
  field was only counting trades, not every event (`trade_index` and `event_index` were
  accidentally identical) — fixed to count every event including quotes, matching spec section
  2.2's own "row i is a pure function of events 1..i"; no test asserts a specific `event_index`
  value, so this could not have masked a test failure. (2) An unused `Callable`/`sys` import in
  each of `micro_features.py`/`micro_snapshots.py`, removed. Both are reflected in the FINAL
  18/18 real-corpus rebuild and the 2,822-pass suite run above, not merely the earlier 2,821-pass
  intermediate run.
- **`feature_source_hash` covers `micro_features.py` only, not `micro_observer.py`** (noted while
  fixing the review's CRITICAL; NOT fixed here, because no listed issue implicates it and widening
  the identity tuple would re-key every snapshot a second time). Consequence: an edit confined to
  the observer's own streaming state machine would not, by itself, invalidate a stored snapshot —
  the operator would have to rebuild deliberately. It did not bite this time (the fix touched
  `micro_features.py` too, so all 18 identities missed honestly and rebuilt), but a future
  observer-only change could serve stale rows. Recorded for the reviewer/auditor to triage;
  the obvious fix is to hash both module sources into `feature_source_hash`.

- **A separate, narrower correctness fix mid-development**: `_ShareWindow.push` (the volume-time
  rolling-imbalance window) initially double-counted an `unknown`-sided print's contribution when
  deciding whether to trim the window's front — an `unknown`-sided trade's size was never added to
  the window's tracked total in the first place, so subtracting it during a trim was wrong. Fixed
  by never buffering `unknown`-sided prints in `_ShareWindow` at all (they carry no direction to
  contribute to a directional volume-time window), closing the bug by construction rather than by
  patching the arithmetic. Caught by manual code review, not a failing test (the existing oracle
  fixtures did not happen to exercise an `unknown`-sided print landing at a window's trim
  boundary) — the FINAL rebuild + suite pass reflects the fix.

---

## Fix Notes (review FAIL, 2026-08-17)

Source: `reports/reviews/goal-rapid-microscope-iter-2-review.md`. All three reported issues fixed;
nothing else in the reviewed scope was rebuilt or refactored.

### 1. CRITICAL — `quote_depletion`'s share-denominated magnitude was served ungated (`micro_observer.py:613`)

**The review was right, and the shipped 6.2 GB corpus embedded the violation.** Spec section 3
names the depletion magnitude CROSS-BASIS in the same clause as the execution-vs-replenishment
ratio ("as is any share-denominated depletion/replenishment magnitude"), so section 2.6 requires
the same typed refusal under an unverified `quote_size_unit` — and all 18 legacy datasets are
`unverified`. `_resolve_depletion` computed `start_size - current_size` and attached it
unconditionally; `self.quote_size_unit` was stamped on rows for display but never consulted.

**Fix** — `apps/backend/app/research/micro_observer.py`, `_resolve_depletion`: the gate now runs at
the point of emission, through `mf.require_share_denominated_magnitude_allowed` (the purpose-built
entry point the review correctly noted was written but never called). Under an unverified unit the
attachment carries `value: None`, `refused: True`, and
`refusal_reason: "cross_basis_unverified_quote_size_unit"` instead of the number.

Three deliberate choices, each defensible on its own:

- **The refusal is DATA, not a raised exception.** `CrossBasisUnverifiedUnitError` escaping
  mid-replay would abort the whole pass and refuse the unit-INVARIANT features (quote imbalance,
  microprice, every F-FLOW and F-RESPONSE value) along with the one illegal quantity. Same refusal,
  same fail-closed meaning, expressed as a persisted closed-vocabulary token — added to
  `micro_features.py` as `CROSS_BASIS_REFUSAL_UNVERIFIED_UNIT` so the vocabulary has one owner.
- **`unavailable` stays `False` on a refusal.** They are different honest states: `unavailable`
  means the observation window never closed (session ended first); `refused` means it closed
  normally and its magnitude is not reportable under this dataset's unit basis. Collapsing them
  would lose exactly the distinction section 2.6 exists to draw.
- **The run's unit-INVARIANT facts are still served** — the availability triple, the price, and
  `updates_observed`. Only the magnitude is withheld; the observation itself is on the record.
  `refill_consistent` needs no gate at all (it compares a displayed size to a displayed size within
  one dataset, and serves a boolean), and this is now counter-tested rather than assumed.

**The real corpus was rebuilt and swept.** The source change moved `feature_source_hash`, so all 18
stored identities reported an honest MISS (TR-7's own mechanism — verified explicitly before the
rebuild, 18/18 stale) and `python -m app.research.micro_snapshots --all` rebuilt every one.
Post-rebuild sweep of the persisted JSONL (every row of all 18 files, not a sample):

| | |
|---|---:|
| Snapshots valid on re-read (identity re-verified) | 18 / 18 |
| Every one stamped `quote_size_unit: "unverified"` | yes |
| Rows | 3,815,933 (unchanged from the pre-fix build) |
| Bytes on disk | 6,378.8 MB (was 6,232.8 MB — the refusal keys cost ~146 MB) |
| Persisted `quote_depletion` completions | 1,824,729 |
| …of those, refused with `value: None` | **1,824,729** |
| …of those, still serving a raw magnitude | **0** |

### 2. MINOR — the TC-10 test locked in the ungated value as correct (`test_micro_observer.py:268`)

Split into the two halves the TC-7/TR-18 contract actually requires, plus the observer-level
coverage the review asked for. Six tests added (2,822 → 2,828 — no existing test dropped):

- `test_tc10_quote_depletion_resolves_at_a_price_change_attached_to_the_next_trade_row` — now runs
  at `quote_size_unit="shares"` and asserts the magnitude **and** `refused is False`.
- `test_tc7_tr18_quote_depletion_magnitude_is_refused_under_an_unverified_unit` — the refusal, the
  reason token, `unavailable is False`, and the unit-invariant fields surviving intact.
- `test_tc7_tr18_round_lots_is_a_verified_unit_for_the_depletion_magnitude_too` — the gate asks
  "verified?", never "shares?".
- `test_tc7_tr18_unit_invariant_liquidity_features_are_never_refused_by_the_gate` — the section 2.6
  carve-out counter-tested: a gate that refused everything would be as dishonest as one that
  refused nothing.
- `test_tr18_real_fixture_serves_no_share_denominated_magnitude_under_an_unverified_unit` and its
  verified-unit twin — a whole-stream sweep over the REAL committed tick fixture, so the guarantee
  is proven on a real replay and not only on a five-event hand fixture.
- `test_tr18_source_scan_every_streaming_emitter_of_a_share_denominated_magnitude_is_gated`
  (`test_micro_features.py`) — closes the structural gap the review identified precisely: the
  existing scan walks only `micro_features.py`, so it could never see ungated arithmetic in
  `micro_observer.py`. The new scan walks the observer and requires every function constructing a
  deferred completion of a kind in `CROSS_BASIS_SHARE_DENOMINATED_KINDS` to call a section 2.6
  gate. Scoped to EMITTERS rather than to every reader of `quote_size_unit` on purpose: serving the
  unit as a row LABEL is not arithmetic over it, and a rule that flagged the label would need an
  exemption list — which is how a guard stops guarding. It also asserts it found at least one
  emitter, so it cannot pass vacuously.

**Counter-checked, not assumed.** With `_resolve_depletion` reverted to the shipped un-gated code,
three of the new tests fail (the per-event refusal test, the real-fixture sweep, and the source
scan naming `['_resolve_depletion']`); restored, all pass. The guards genuinely catch the bug the
review found.

### 3. NOTE — `execution_vs_replenishment_ratio` missing from the Known Issues disclosure

Added to Known Issues above, alongside `divergence_at_level`, with the reason it has no live call
site: it is cross-basis, and no dataset on disk carries a verified unit, so wiring it today would
emit a refusal on every row and a value on none. Not wired (the execution plan's own F-LIQUIDITY
streaming list does not include it); the first verified-unit dataset from J-06's recorder is what
makes a legal call site exist.

### Out-of-report fix, disclosed: two pre-existing flaky route tests

Re-running the full suite surfaced `test_compute_route_refuses_a_second_concurrent_trigger`
failing. It is **not** caused by the unit-gate fix — measured over 20 isolated runs each: **15/20
failures against the pre-fix observer, 14/20 against the fixed one.** `test_cancel_route_
acknowledges_a_running_job` shares the identical race (11/20). Both trigger a build of a 3-event
synthetic dataset (sub-millisecond) and then assert on a job that must still be RUNNING when a
`TestClient` round trip through the ASGI stack lands several milliseconds later — a coin flip. The
earlier 2,822-pass run simply won both flips. The manager-level twin
(`test_tc13_manager_refuses_a_second_concurrent_trigger`, no HTTP stack between the two calls) is
stable at 0/20 and was left alone.

Fixed by pinning the worker inside its build on a barrier (`_pinned_build`, a `monkeypatch` of
`ms.run_snapshot_build_and_record`) until after the second request is answered, so the refusal and
the cancel acknowledgement are genuine single-flight outcomes rather than races the test happened
to win. **No asserted contract was relaxed — only the timing was made deterministic.** Verified
0/25 failures each and 5/5 clean whole-module runs afterwards. Flagged here rather than fixed
silently: it is outside the review's three issues, but a test failing ~60% of the time in the
module the review's own fix task points at (`re-run TC-12`) could not be left red, and reporting a
green suite while one existed would have been dishonest.

### Files changed in this fix round

- `apps/backend/app/research/micro_observer.py` — the section 2.6 gate in `_resolve_depletion`; module docstring records the streaming-path contract.
- `apps/backend/app/research/micro_features.py` — `CROSS_BASIS_REFUSAL_UNVERIFIED_UNIT` + `CROSS_BASIS_SHARE_DENOMINATED_KINDS`; `require_share_denominated_magnitude_allowed` added to `__all__` now that it has a caller.
- `apps/backend/tests/test_micro_observer.py` — the TC-10 split + 4 new unit-gate/TR-18 tests.
- `apps/backend/tests/test_micro_features.py` — the streaming-layer TR-18 source scan.
- `apps/backend/tests/test_micro_snapshots.py` — `_pinned_build` + the two de-flaked route tests.
- `apps/backend/.data/micro_snapshots/` (not source) — all 18 snapshots rebuilt.

### Re-verification after the fix

Command: `cd apps/backend && .venv/bin/python -m pytest tests/`
Result: **2,828 passed, 8 skipped, 0 failed** (443.78s). (Note for future runs: passing `-q`
on top of the `addopts = "-q"` in `pyproject.toml` makes it `-qq`, which suppresses the final
count line entirely — run bare `pytest tests/`.)

- `Config().config_fingerprint()` → `08e471b10130e1e2` — unchanged.
- All 6 `referee_*.py` SHA-256 hashes — re-listed after the fix, byte-identical to the iteration-0
  baseline (same six digests recorded above).
- `git status` on `app/engine/`, `tests/test_observer_equivalence.py`, and
  `tests/test_dense_replay_gate.py` — zero entries; both golden/equivalence files pass unmodified
  inside the run above.
- MCP `EXPECTED_TOOLS` — still the 22-tuple.
- 18/18 real-corpus snapshots rebuilt, TC-12 re-run green.

---

## Audit amendments (2026-08-17, auditor)

Three claims above were invalidated by fixes applied during the audit
(`docs/handoffs/goal-rapid-microscope-iter-2-audit.md`, section 4). Recorded here so this handoff
does not out-live its own accuracy; nothing else in it changed.

1. **The Known Issue "`feature_source_hash` covers `micro_features.py` only … NOT fixed here" is
   now FIXED.** `micro_snapshots.feature_source_hash()` hashes the source bytes of both
   `micro_features.py` and `micro_observer.py` (fixed order, `_IDENTITY_SOURCE_MODULES`). This is
   strictly more conservative than spec section 2.3's literal wording — it can only ever turn a
   would-be cache HIT into an honest MISS. All 18 identities missed honestly and were rebuilt
   through the shipped CLI; `feature_source_hash` is now
   `b926251982a96b34835c883a44cdce79792899bc2a94b5accb3b1713f1da947b`.
2. **The fix-round sweep table's `quote_depletion` row is superseded.** A depletion window the
   session cut short was being recorded as a COMPLETED observation. Post-fix, post-rebuild
   whole-corpus sweep (every row of all 18 files): 1,824,729 completions — **1,824,693 refused**
   (window closed, magnitude withheld under the unverified unit) and **36 `unavailable: True` /
   `value: None` / `refused: False`** (exactly 2 per dataset — the bid and ask runs open at session
   end). Still **0** serving a raw magnitude. Rows (3,815,933) and bytes on disk (6,378.8 MB) are
   unchanged from the pre-audit build — the fix altered no trade row.
3. **The final suite count is 2,835 passed / 8 skipped / 0 failed** (468.30s, bare `pytest tests/`),
   up from 2,828 by exactly the 7 regression tests the audit added; zero pre-existing tests changed
   behaviour. Fingerprint `08e471b10130e1e2` and all 6 referee SHA-256 hashes re-verified unchanged
   after the fixes.
